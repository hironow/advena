// advena の利用者文書: サインイン時の作成と、/add_user による created への更新
//
// 現行コードの写し:
//   readUsers   addUserAdmin のトランザクションが users を firebase_uid で検索する
//               (frontend/web/lib/firestore/admin-db.ts: tx.get(...where("firebase_uid", "==", firebase_uid).limit(1)))
//   commit      該当がなければ status=creating, version 0 の文書を新しい UUID で作り、コミットする
//   markCreated /add_user (main.py) が creating を created にする。Python 側の読み出し時の移行も同じ変更をする
//
// 同じ人 (同じ firebase_uid) が 2 つの端末からほぼ同時にサインインする場面だけを見る。
//
// スイッチ:
//   ABSENCE_GUARDED  トランザクションの中で「該当なし」と読んだ結果も守られ、その後に別のトランザクションが
//                    該当する文書を作ると、こちらのコミットが失敗して再試行になる。
//                    Firestore のサーバー用ライブラリがこれを保証するかは、コードからは決まらない
module account {
  const ABSENCE_GUARDED: bool

  pure val LOGINS = Set("a", "b")
  // ログイン a は u1 を、b は u2 を作ろうとする (randomUUID は毎回違う)
  pure def newIdOf(l: str): str = if (l == "a") "u1" else "u2"
  pure val IDS = Set("u1", "u2")

  var userStatus: str -> str   // "none" | "creating" | "created"
  var phase: str -> str        // "idle" | "read" | "done"
  var sawNone: str -> bool     // 検索で該当なしと読んだ
  var stale: str -> bool       // 読んだ後に、別のトランザクションが該当する文書を作った

  action init = all {
    userStatus' = IDS.mapBy(i => "none"),
    phase' = LOGINS.mapBy(l => "idle"),
    sawNone' = LOGINS.mapBy(l => false),
    stale' = LOGINS.mapBy(l => false),
  }

  def anyUser: bool = IDS.exists(i => userStatus.get(i) != "none")

  action readUsers(l: str): bool = all {
    phase.get(l) == "idle",
    phase' = phase.set(l, "read"),
    sawNone' = sawNone.set(l, not(anyUser)),
    stale' = stale.set(l, false),
    userStatus' = userStatus,
  }

  // コミット。該当なしと読んでいれば作る。ABSENCE_GUARDED なら、読んだ後に作られた文書と衝突して失敗し、読み直す
  action commit(l: str): bool = all {
    phase.get(l) == "read",
    if (ABSENCE_GUARDED and sawNone.get(l) and stale.get(l)) all {
      phase' = phase.set(l, "idle"),
      userStatus' = userStatus,
      sawNone' = sawNone,
      stale' = stale,
    } else all {
      phase' = phase.set(l, "done"),
      userStatus' = if (sawNone.get(l)) userStatus.set(newIdOf(l), "creating") else userStatus,
      sawNone' = sawNone,
      // この作成は、読んだ後でまだコミットしていない他のログインから見ると、読んだ結果を古くする
      stale' = if (sawNone.get(l)) LOGINS.mapBy(o => stale.get(o) or (o != l and phase.get(o) == "read")) else stale,
    },
  }

  action markCreated(i: str): bool = all {
    userStatus.get(i) == "creating",
    userStatus' = userStatus.set(i, "created"),
    phase' = phase, sawNone' = sawNone, stale' = stale,
  }

  action stutter = all {
    userStatus' = userStatus, phase' = phase, sawNone' = sawNone, stale' = stale,
  }

  action step = any {
    nondet l = LOGINS.oneOf()
    nondet i = IDS.oneOf()
    any { readUsers(l), commit(l), markCreated(i) },
    stutter,
  }

  // 1 つの firebase_uid に利用者文書は高々 1 つ
  val oneUserPerUid = IDS.filter(i => userStatus.get(i) != "none").size() <= 1
}

// 「該当なし」が守られない場合
module accountUnguarded {
  import account(ABSENCE_GUARDED = false).*

  // 2 つのログインがどちらも該当なしと読み、どちらも作る
  run duplicateUserTest =
    init.then(readUsers("a")).then(readUsers("b")).then(commit("a")).then(commit("b"))
      .expect(not(oneUserPerUid))
}

// 「該当なし」が守られる場合
module accountGuarded {
  import account(ABSENCE_GUARDED = true).*

  // 修正が働く場面: b のコミットは失敗し、読み直すと a の文書が見えるので作らない
  run secondLoginRetriesTest =
    init.then(readUsers("a")).then(readUsers("b")).then(commit("a")).then(commit("b"))
      .then(readUsers("b")).then(commit("b"))
      .expect(oneUserPerUid and phase.get("b") == "done" and userStatus.get("u2") == "none")
}
