// advena の番組制作: 現行コードと、その修正の提案
//
// 現行コード (スイッチがすべて false) は、状態を変える書き込みと読み取りごとに 1 つの action を持つ。
//   collect      収集実行 (main.py の /async_task → workflows.exec_fetch_rss_and_oai_pmh_workflow → radio_show.new)
//   deliver      Pub/Sub が文書作成イベントを /add_radio_show に push する (scripts/bind-eventarc-invoke.sh)
//   check        /add_radio_show が status を読み、番組対象日の項目を選ぶ (main.py:124-140, workflows.py:247-258)
//   writeScript  LLM で台本を作り public/radio_show_script/{id}.txt に保存する (workflows.py:283-293)
//   writeAudio   TTS で音声を作り public/radio_show_audio/{id}.mp3 に保存する (workflows.py:296-302)
//   publish      radio_show.publish が status=created にする。何も確かめない (radio_show.py:251-273)
//   depFails     Gemini / TTS / GCS が失敗し、例外で 500 を返す (main.py:146-148)
//   ackTimeout   ack 期限 (300 秒) までに応答がなく、Pub/Sub が失敗とみなす。実行そのものは続く
//   kill         Cloud Run のインスタンスが落ち、実行が消える
//   midnight     JST の日付が変わる
//
// 前提 (コードからは確かめられないもの):
//   - 2 つの実行が同じ番組を並行に扱うには、再配信を別のインスタンスが受ける必要がある。
//     backend は uvicorn の 1 プロセスで、制作中はイベントループを止めるので、同じインスタンスに届いた
//     再配信は前の実行の後に回る (Dockerfile.prd, main.py:136)。Cloud Run の台数の設定はリポジトリにない。
//   - 再配信の上限はモデルでは 2 回 (Pub/Sub の既定値はもっと多い)。
//
// 提案のスイッチ:
//   FIX_DAY   作成時に JST の番組対象日を決めて保存し、文書の ID をその日から作る (同じ日の文書は 1 つだけ作れる)
//   FENCE     status の確認をトランザクションにし、制作権を世代番号つきで取る。台本と音声は世代ごとのパスに書き、
//             公開はその世代がまだ制作権を持つときだけ成功する。制作権には期限 (リース) がある
//   TERMINAL  該当なしの番組を skipped にする
//   SWEEP     未完了 (creating / producing) で、配信待ちも有効なリースも、その番組を扱う実行もない番組を
//             failed にする回収処理。実際には「作成から、再配信の窓と Cloud Run のリクエストタイムアウトより
//             長く経った」で判定し、Cloud Scheduler で定期的に動かす想定。
module radio {
  const FIX_DAY: bool
  const FENCE: bool
  const TERMINAL: bool
  const SWEEP: bool
  const SHOWS: Set[str]
  const RUNS: Set[str]

  pure val LAST_DAY = 2
  pure val DAYS = 1.to(LAST_DAY)
  pure val MAX_ATTEMPTS = 2
  pure val SLOTS = 0.to(MAX_ATTEMPTS)
  pure val ACTIVE = Set("started", "selected", "scripted", "voiced")
  pure val PRODUCING_PCS = Set("selected", "scripted", "voiced")
  pure val TERMINALS = Set("created", "skipped", "failed")
  pure val UNFINISHED = Set("creating", "producing")

  // 番組文書と、その文書作成イベントの配信状況
  type Doc = {
    status: str,       // "none" | "creating" | "producing" | "created" | "skipped" | "failed"
    createdOn: int,    // 収集実行が文書を作った日 (0 = 未作成)
    storedDay: int,    // 文書に保存された broadcasted_at の日付 (0 = 指定なし)
    items: Set[int],   // 結合マスタデータに項目がある日付 (項目日時の JST 日付)
    pending: bool,     // Pub/Sub が配信を控えている
    attempts: int,     // 配信した回数
    dead: bool,        // 配信打ち切り (dead letter)
    gen: int,          // FENCE: 制作権の世代
    lease: bool,       // FENCE: 制作権の期限がまだ切れていない
    pubSlot: int,      // 公開した台本と音声のパスの世代 (現行コードでは常に 0)
    pubScript: str,    // 公開した時点で台本のパスにあった内容を書いた実行
    pubAudio: str,     // 公開した時点で音声のパスにあった内容を書いた実行
    pubDay: int,       // 公開した番組の broadcasted_at
    checkedNoItems: bool, // 制作実行が status を確かめ、番組対象日の項目が 0 件だと分かった
  }

  // 制作実行 (1 回の配信を受けた /add_radio_show の処理)
  type Exec = {
    pc: str,           // "idle" | "started" | "selected" | "scripted" | "voiced"
    doc: str,
    day: int,          // 選んだ番組対象日
    gen: int,          // FENCE: 取った制作権の世代
    orphan: bool,      // ack 期限を過ぎた。この実行の応答を Pub/Sub はもう見ない
  }

  pure val noDoc: Doc = {
    status: "none", createdOn: 0, storedDay: 0, items: Set(), pending: false, attempts: 0,
    dead: false, gen: 0, lease: false, pubSlot: 0, pubScript: "", pubAudio: "", pubDay: 0,
    checkedNoItems: false,
  }
  pure val idleExec: Exec = { pc: "idle", doc: "", day: 0, gen: 0, orphan: false }

  var today: int
  var docs: str -> Doc
  var runs: str -> Exec
  var scriptBlob: (str, int) -> str   // (番組, パスの世代) → その内容を書いた実行
  var audioBlob: (str, int) -> str

  val vars = (today, docs, runs, scriptBlob, audioBlob)

  action init = all {
    today' = 1,
    docs' = SHOWS.mapBy(s => noDoc),
    runs' = RUNS.mapBy(r => idleExec),
    scriptBlob' = tuples(SHOWS, SLOTS).mapBy(k => ""),
    audioBlob' = tuples(SHOWS, SLOTS).mapBy(k => ""),
  }

  // 制作実行が応答を返したときの配信の状態。成功 (2xx) なら ack。
  // 失敗なら、回数が残っていれば再配信、残っていなければ配信打ち切り。
  // ack 期限を過ぎた実行の応答は Pub/Sub が見ないので、何も変えない。
  pure def respond(d: Doc, orphaned: bool, ok: bool): Doc =
    if (orphaned or ok) d
    else if (d.attempts < MAX_ATTEMPTS) { ...d, pending: true }
    else { ...d, dead: true }

  // 番組対象日: 保存された日があればその日、無ければ制作実行を始めた日 (workflows.py の exec_date_jst)
  pure def targetOf(d: Doc, t: int): int = if (d.storedDay == 0) t else d.storedDay

  // その番組が本来紹介するはずの日: 保存された日、無ければ収集した日
  pure def intendedDay(d: Doc): int = if (d.storedDay == 0) d.createdOn else d.storedDay

  pure def dayFor(arg: int, t: int): int = if (arg == 0) t else arg

  pure def slotOf(e: Exec): int = if (FENCE) e.gen else 0

  // status の確認 (main.py:124-131) と項目の選択 (workflows.py:247-258) の後の、文書と実行の状態
  pure def afterCheck(d: Doc, e: Exec, t: int): (Doc, Exec) =
    if (TERMINALS.contains(d.status))
      (respond(d, e.orphan, true), idleExec)
    else if (FENCE and d.status == "producing" and d.lease)
      (respond(d, e.orphan, false), idleExec)
    else if (not(d.items.contains(targetOf(d, t))))
      (respond({ ...d, status: if (TERMINAL) "skipped" else d.status, lease: false, checkedNoItems: true },
               e.orphan, true), idleExec)
    else if (FENCE)
      ({ ...d, status: "producing", gen: d.gen + 1, lease: true },
       { ...e, pc: "selected", day: targetOf(d, t), gen: d.gen + 1 })
    else
      (d, { ...e, pc: "selected", day: targetOf(d, t) })

  // 公開してよいか。現行コードは何も確かめない
  pure def mayPublish(d: Doc, e: Exec): bool =
    not(FENCE) or (d.status == "producing" and d.gen == e.gen)

  def dayTaken(day: int): bool =
    SHOWS.exists(s => docs.get(s).status != "none" and docs.get(s).storedDay == day)

  // 結合マスタデータに項目がある日付: 収集した日 (itemsToday) と翌日 (itemsTomorrow) のどちらにあるか
  pure def itemDays(t: int, itemsToday: bool, itemsTomorrow: bool): Set[int] =
    Set(t, t + 1).filter(d => (d == t and itemsToday) or (d == t + 1 and itemsTomorrow))

  // 収集実行。arg は broadcasted_at (0 = 指定なし)
  action collect(s: str, arg: int, itemsToday: bool, itemsTomorrow: bool): bool = all {
    // 引数の範囲 (step が選ぶ範囲と同じ。直接呼ぶ scripted run もこの範囲に限る)
    arg == 0 or (1 <= arg and arg <= today),
    not(itemsTomorrow) or today < LAST_DAY,
    docs.get(s).status == "none",
    not(FIX_DAY) or not(dayTaken(dayFor(arg, today))),
    docs' = docs.set(s, { ...noDoc, status: "creating", createdOn: today,
      storedDay: if (FIX_DAY) dayFor(arg, today) else arg,
      items: itemDays(today, itemsToday, itemsTomorrow), pending: true }),
    today' = today, runs' = runs, scriptBlob' = scriptBlob, audioBlob' = audioBlob,
  }

  action deliver(s: str, r: str): bool = all {
    docs.get(s).pending,
    runs.get(r).pc == "idle",
    docs' = docs.set(s, { ...docs.get(s), pending: false, attempts: docs.get(s).attempts + 1 }),
    runs' = runs.set(r, { ...idleExec, pc: "started", doc: s }),
    today' = today, scriptBlob' = scriptBlob, audioBlob' = audioBlob,
  }

  action checkDoc(r: str, s: str): bool = all {
    runs.get(r).pc == "started",
    runs.get(r).doc == s,
    docs' = docs.set(s, afterCheck(docs.get(s), runs.get(r), today)._1),
    runs' = runs.set(r, afterCheck(docs.get(s), runs.get(r), today)._2),
    today' = today, scriptBlob' = scriptBlob, audioBlob' = audioBlob,
  }

  action check(r: str): bool = checkDoc(r, runs.get(r).doc)

  action writeScript(r: str): bool = all {
    runs.get(r).pc == "selected",
    scriptBlob' = scriptBlob.set((runs.get(r).doc, slotOf(runs.get(r))), r),
    runs' = runs.set(r, { ...runs.get(r), pc: "scripted" }),
    today' = today, docs' = docs, audioBlob' = audioBlob,
  }

  action writeAudio(r: str): bool = all {
    runs.get(r).pc == "scripted",
    audioBlob' = audioBlob.set((runs.get(r).doc, slotOf(runs.get(r))), r),
    runs' = runs.set(r, { ...runs.get(r), pc: "voiced" }),
    today' = today, docs' = docs, scriptBlob' = scriptBlob,
  }

  action publishDoc(r: str, s: str): bool = all {
    runs.get(r).pc == "voiced",
    runs.get(r).doc == s,
    docs' = if (mayPublish(docs.get(s), runs.get(r)))
        docs.set(s, { ...docs.get(s), status: "created", lease: false,
          pubSlot: slotOf(runs.get(r)),
          pubScript: scriptBlob.get((s, slotOf(runs.get(r)))),
          pubAudio: audioBlob.get((s, slotOf(runs.get(r)))),
          pubDay: runs.get(r).day })
      else docs,
    runs' = runs.set(r, idleExec),
    today' = today, scriptBlob' = scriptBlob, audioBlob' = audioBlob,
  }

  action publish(r: str): bool = publishDoc(r, runs.get(r).doc)

  // 依存先の失敗で例外になり 500 を返す。FENCE では自分の制作権を手放す
  action depFailsDoc(r: str, s: str): bool = all {
    Set("selected", "scripted").contains(runs.get(r).pc),
    runs.get(r).doc == s,
    docs' = docs.set(s, respond(
      { ...docs.get(s), lease: if (FENCE and docs.get(s).gen == runs.get(r).gen) false else docs.get(s).lease },
      runs.get(r).orphan, false)),
    runs' = runs.set(r, idleExec),
    today' = today, scriptBlob' = scriptBlob, audioBlob' = audioBlob,
  }

  action depFails(r: str): bool = depFailsDoc(r, runs.get(r).doc)

  action ackTimeoutDoc(r: str, s: str): bool = all {
    ACTIVE.contains(runs.get(r).pc),
    runs.get(r).doc == s,
    not(runs.get(r).orphan),
    docs' = docs.set(s, respond(docs.get(s), false, false)),
    runs' = runs.set(r, { ...runs.get(r), orphan: true }),
    today' = today, scriptBlob' = scriptBlob, audioBlob' = audioBlob,
  }

  action ackTimeout(r: str): bool = ackTimeoutDoc(r, runs.get(r).doc)

  action killDoc(r: str, s: str): bool = all {
    ACTIVE.contains(runs.get(r).pc),
    runs.get(r).doc == s,
    docs' = docs.set(s, respond(docs.get(s), runs.get(r).orphan, false)),
    runs' = runs.set(r, idleExec),
    today' = today, scriptBlob' = scriptBlob, audioBlob' = audioBlob,
  }

  action kill(r: str): bool = killDoc(r, runs.get(r).doc)

  action leaseExpires(s: str): bool = all {
    FENCE,
    docs.get(s).lease,
    docs' = docs.set(s, { ...docs.get(s), lease: false }),
    today' = today, runs' = runs, scriptBlob' = scriptBlob, audioBlob' = audioBlob,
  }

  action sweep(s: str): bool = all {
    SWEEP,
    UNFINISHED.contains(docs.get(s).status),
    not(docs.get(s).pending),
    not(docs.get(s).lease),
    RUNS.forall(r => runs.get(r).pc == "idle" or runs.get(r).doc != s),
    docs' = docs.set(s, { ...docs.get(s), status: "failed" }),
    today' = today, runs' = runs, scriptBlob' = scriptBlob, audioBlob' = audioBlob,
  }

  action midnight = all {
    today < LAST_DAY,
    today' = today + 1,
    docs' = docs, runs' = runs, scriptBlob' = scriptBlob, audioBlob' = audioBlob,
  }

  // 何も起きない。すべてが終わった状態でも次の状態があるようにする (TLC の deadlock を避ける)
  action stutter = all {
    today' = today, docs' = docs, runs' = runs, scriptBlob' = scriptBlob, audioBlob' = audioBlob,
  }

  // 公平性の対象: 番組を終わりに向けて進める操作。止める操作 (depFails, ackTimeout, kill)、
  // 新しい収集、日付の変化は含めない
  action progress = {
    nondet s = SHOWS.oneOf()
    nondet r = RUNS.oneOf()
    any { deliver(s, r), check(r), writeScript(r), writeAudio(r), publish(r), leaseExpires(s), sweep(s) }
  }

  action step = any {
    nondet s = SHOWS.oneOf()
    nondet r = RUNS.oneOf()
    nondet arg = Set(0).union(1.to(today)).oneOf()
    nondet itemsToday = Set(true, false).oneOf()
    nondet itemsTomorrow = Set(true, false).oneOf()
    any {
      collect(s, arg, itemsToday, itemsTomorrow), deliver(s, r), check(r), writeScript(r), writeAudio(r), publish(r),
      depFails(r), ackTimeout(r), kill(r), leaseExpires(s), sweep(s),
    },
    midnight,
    stutter,
  }

  // 1 つの番組対象日に公開済み番組は高々 1 本 (放送枠)
  val onePerDay = DAYS.forall(day =>
    SHOWS.filter(s => docs.get(s).status == "created" and docs.get(s).pubDay == day).size() <= 1)

  // 公開済み番組の台本と音声 (公開 URL の先にある内容) は、同じ制作実行が書いたもの
  val sameRun = SHOWS.forall(s => docs.get(s).status == "created" implies
    scriptBlob.get((s, docs.get(s).pubSlot)) == audioBlob.get((s, docs.get(s).pubSlot)))

  // 公開した後、公開 URL の先の台本と音声は変わらない
  val unchangedAfterPublish = SHOWS.forall(s => docs.get(s).status == "created" implies and {
    scriptBlob.get((s, docs.get(s).pubSlot)) == docs.get(s).pubScript,
    audioBlob.get((s, docs.get(s).pubSlot)) == docs.get(s).pubAudio,
  })

  // 公開済み番組は、本来紹介するはずの日 (保存された日、無ければ収集した日) の番組である
  val dayAsIntended = SHOWS.forall(s => docs.get(s).status == "created" implies
    docs.get(s).pubDay == intendedDay(docs.get(s)))

  // 同じ番組を制作している (LLM や TTS を呼びうる) 実行は、同時に高々 1 つ
  val oneProducerAtATime = SHOWS.forall(s =>
    RUNS.filter(r => PRODUCING_PCS.contains(runs.get(r).pc) and runs.get(r).doc == s).size() <= 1)

  // 該当なしと確かめられた番組は failed にならない (failed は「公開できなかった」の意味だけに使う)
  val noItemsNotFailed = SHOWS.forall(s => docs.get(s).checkedNoItems implies docs.get(s).status != "failed")

  // 作成された番組は、いずれ終わる (公開、skipped、failed のどれか)
  temporal eventuallyTerminal = SHOWS.forall(s =>
    always(UNFINISHED.contains(docs.get(s).status) implies eventually(TERMINALS.contains(docs.get(s).status))))

  temporal fairness = weakFair(progress, vars)

  // 進める操作が公平に実行されるなら、作成された番組はいずれ終わる。止める操作は何度起きてもよい
  temporal Liveness = fairness implies eventuallyTerminal
}

// 現行コード、番組 1 つ、実行枠 2 つ
module code1 {
  import radio(FIX_DAY = false, FENCE = false, TERMINAL = false, SWEEP = false,
               SHOWS = Set("s1"), RUNS = Set("r1", "r2")).*

  // ack 期限を過ぎた r1 が動き続けるうちに、再配信を受けた r2 が同じパスに台本を書く。
  // r1 が公開すると、公開 URL の先の台本は r2、音声は r1 のもの
  run mixedScriptAndAudioTest =
    init.then(collect("s1", 0, true, false)).then(deliver("s1", "r1")).then(check("r1"))
      .then(writeScript("r1")).then(ackTimeout("r1"))
      .then(deliver("s1", "r2")).then(check("r2")).then(writeScript("r2"))
      .then(writeAudio("r1")).then(publish("r1"))
      .expect(docs.get("s1").status == "created" and not(sameRun))

  // 該当なしで 204 を返すと、配信は終わり、番組は creating のまま残る
  run noItemsLeavesCreatingTest =
    init.then(collect("s1", 0, false, false)).then(deliver("s1", "r1")).then(check("r1"))
      .expect(and {
        docs.get("s1").status == "creating",
        not(docs.get("s1").pending), not(docs.get("s1").dead),
        RUNS.forall(r => runs.get(r).pc == "idle"),
      })

  // 依存先の失敗が再配信の上限まで続くと、配信は打ち切られ、番組は creating のまま残る
  run haltUntilDeadLetterTest =
    init.then(collect("s1", 0, true, false)).then(deliver("s1", "r1")).then(check("r1"))
      .then(writeScript("r1")).then(depFails("r1"))
      .then(deliver("s1", "r1")).then(check("r1")).then(depFails("r1"))
      .expect(docs.get("s1").dead and docs.get("s1").status == "creating")

  // 制作が中断し、再配信が JST の 0 時をまたぐと、番組対象日が翌日になる。
  // 結合マスタデータに翌日の日付の項目があれば、翌日の番組として公開される
  run lateProductionTest =
    init.then(collect("s1", 0, true, true)).then(deliver("s1", "r1")).then(check("r1"))
      .then(depFails("r1")).then(midnight)
      .then(deliver("s1", "r1")).then(check("r1")).then(writeScript("r1")).then(writeAudio("r1"))
      .then(publish("r1"))
      .expect(docs.get("s1").pubDay == 2 and not(dayAsIntended))
}

// 現行コード、番組 2 つ、実行枠 1 つ (1 日 1 本を見る)
module code2 {
  import radio(FIX_DAY = false, FENCE = false, TERMINAL = false, SWEEP = false,
               SHOWS = Set("s1", "s2"), RUNS = Set("r1")).*

  // 同じ日に収集実行が 2 回動く (スケジューラの再試行、運用者の再実行)。どちらも公開される
  run twoShowsOneDayTest =
    init.then(collect("s1", 0, true, false)).then(collect("s2", 0, true, false))
      .then(deliver("s1", "r1")).then(check("r1")).then(writeScript("r1")).then(writeAudio("r1")).then(publish("r1"))
      .then(deliver("s2", "r1")).then(check("r1")).then(writeScript("r1")).then(writeAudio("r1")).then(publish("r1"))
      .expect(not(onePerDay))
}

// 提案 (4 つのスイッチすべて)、番組 1 つ、実行枠 2 つ
module proposal1 {
  import radio(FIX_DAY = true, FENCE = true, TERMINAL = true, SWEEP = true,
               SHOWS = Set("s1"), RUNS = Set("r1", "r2")).*

  // 修正が働く場面: リースが切れた後の古い実行 r1 の公開は拒まれ、公開されるのは r2 の台本と音声
  run staleRunIsFencedTest =
    init.then(collect("s1", 0, true, false)).then(deliver("s1", "r1")).then(check("r1"))
      .then(writeScript("r1")).then(ackTimeout("r1")).then(leaseExpires("s1"))
      .then(deliver("s1", "r2")).then(check("r2")).then(writeScript("r2")).then(writeAudio("r2")).then(publish("r2"))
      .then(writeAudio("r1")).then(publish("r1"))
      .expect(and {
        docs.get("s1").status == "created", docs.get("s1").pubSlot == 2,
        scriptBlob.get(("s1", 2)) == "r2", audioBlob.get(("s1", 2)) == "r2",
        sameRun, unchangedAfterPublish,
      })

  // 修正が働く場面: 配信打ち切りの後、回収処理が番組を failed にする
  run sweeperClosesDeadLetterTest =
    init.then(collect("s1", 0, true, false)).then(deliver("s1", "r1")).then(check("r1")).then(depFails("r1"))
      .then(deliver("s1", "r1")).then(check("r1")).then(depFails("r1"))
      .then(sweep("s1"))
      .expect(docs.get("s1").dead and docs.get("s1").status == "failed")

  // 修正が働く場面: 該当なしは skipped
  run noItemsIsSkippedTest =
    init.then(collect("s1", 0, false, false)).then(deliver("s1", "r1")).then(check("r1"))
      .expect(docs.get("s1").status == "skipped")
}

// 提案、番組 2 つ、実行枠 1 つ
module proposal2 {
  import radio(FIX_DAY = true, FENCE = true, TERMINAL = true, SWEEP = true,
               SHOWS = Set("s1", "s2"), RUNS = Set("r1")).*

  // 修正が働く場面: 同じ日の 2 回目の収集は文書を作れない。翌日の収集は作れる
  run secondCollectSameDayRefusedTest =
    init.then(collect("s1", 0, true, false)).then(collect("s2", 0, true, false)).fail()

  run nextDayCollectAllowedTest =
    init.then(collect("s1", 0, true, true)).then(midnight).then(collect("s2", 0, true, false))
      .expect(docs.get("s1").storedDay == 1 and docs.get("s2").storedDay == 2)
}

// 提案から 1 点だけを除いたもの (方針案の各条項が要ることを見る)

// 回収処理を除く
module noSweep1 {
  import radio(FIX_DAY = true, FENCE = true, TERMINAL = true, SWEEP = false,
               SHOWS = Set("s1"), RUNS = Set("r1", "r2")).*
}

// 作成時の日付の固定を除く
module noFixDay2 {
  import radio(FIX_DAY = false, FENCE = true, TERMINAL = true, SWEEP = true,
               SHOWS = Set("s1", "s2"), RUNS = Set("r1")).*
}

module noFixDay1 {
  import radio(FIX_DAY = false, FENCE = true, TERMINAL = true, SWEEP = true,
               SHOWS = Set("s1"), RUNS = Set("r1", "r2")).*
}

// 世代つきの制作権を除く
module noFence1 {
  import radio(FIX_DAY = true, FENCE = false, TERMINAL = true, SWEEP = true,
               SHOWS = Set("s1"), RUNS = Set("r1", "r2")).*
}

// skipped を除く
module noTerminal1 {
  import radio(FIX_DAY = true, FENCE = true, TERMINAL = false, SWEEP = true,
               SHOWS = Set("s1"), RUNS = Set("r1", "r2")).*

  // 該当なしの番組が creating のまま残り、回収処理が failed にする
  run noItemsBecomesFailedTest =
    init.then(collect("s1", 0, false, false)).then(deliver("s1", "r1")).then(check("r1")).then(sweep("s1"))
      .expect(docs.get("s1").checkedNoItems and docs.get("s1").status == "failed" and not(noItemsNotFailed))
}
