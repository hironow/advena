# Public workflow and Internal workflow with context
# 実装するworkflowはビジネスプロセスのこと
#
# * RSS -> GCS
# * GCS -> GCS
# * GCS -> LLM
# * GCS -> Firestore
# * Firestore -> GCS
# * Firestore -> LLM
#
# GCSのバケット以下のフォルダを定義する:
# * rss (raw): lastBuildDateと検索キーワードを末尾に含めたファイル (更新される可能性がないので、削除しない)     : /rss/{lastBuildDate}_{keyword}.xml
# * oai_pmh (raw): 1書籍ごとのデータ (更新されている可能性があるので、古いものから除去して良い)                : /oai_pmh/{book_id}.xml
# * combined masterdata (edited): rssとoai_pmhを結合して、ラジオ番組作成が可能な形式に変換したファイル      : /combined_masterdata/{lastBuildDate}_{keyword}.json
# * radio audio data (edited): ラジオ番組の音声データ                                               : /radio_audio_data/{lastBuildDate}_{keyword}.mp3
# * radio script data (edited): ラジオ番組の音声データに対応するスクリプトデータ                        : /radio_script_data/{lastBuildDate}_{keyword}.json
#
# 要件:
# RSSを取得すれば、combined masterdataを作成できる
# combined masterdataを取得すれば、ラジオ番組を作成できる(スクリプト段階)
# ラジオ番組(スクリプト)を作成すれば、音声データを作成できる


import io
import json
from datetime import UTC, datetime
from typing import Any

import feedparser  # type: ignore
from pydantic import BaseModel, RootModel

from src.blob.storage import (
    ISBN_DIR,
    JP_E_CODE_DIR,
    XML_LATEST_ALL_DIR_BASE,
    get_closest_cached_oai_pmh_file,
    get_closest_cached_rss_file,
    get_json_file,
    put_combined_json_file,
    put_oai_pmh_json,
    put_rss_xml_file,
    put_tts_audio_file,
    put_tts_script_file,
)
from src.book.book import latest_all, thumbnail
from src.book.feed import convert_to_entry_item, fetch_rss, parse_rss
from src.book.oai_pmh import get_metadata_by_isbn, get_metadata_by_jp_e_code
from src.event_sourcing.entity import radio_show as entity_radio_show
from src.llm import agent, ng_word
from src.logger import logger
from src.tts import google as tts_google
from src.utils import JST, get_now


class MstBook(BaseModel):
    title: str
    summary: str
    isbn: str
    jp_e_code: str
    link: str
    thumbnail_link: str
    published: datetime
    metadata: dict[str, Any] = {}


class MstBooks(RootModel[dict[str, MstBook]]):
    def __getitem__(self, key: str) -> MstBook:
        return self.root[key]

    def __iter__(self):
        return iter(self.root)

    def __len__(self) -> int:
        return len(self.root)


def exec_fetch_rss_and_oai_pmh_workflow(
    target_url: str,
    prefix_dir: str,
    suffix_dir: str,
    broadcasted_at: datetime | None = None,
) -> None:
    """RSS、API系をcallしてGCSにキャッシュ、ラジオ番組作成が可能な最終1ファイルをGCSにアップロードする。ラジオ番組が作成開始される。"""
    logger.info("start exec_run_agent_and_tts_workflow ...")
    logger.info(
        f"target_url: {target_url}, prefix_dir: {prefix_dir}, suffix_dir: {suffix_dir}, broadcasted_at: {broadcasted_at}"
    )
    if target_url == "":
        raise ValueError("target_url is empty.")
    if prefix_dir == "" or suffix_dir == "":
        raise ValueError("prefix_dir or suffix_dir is empty.")
    if broadcasted_at is not None:
        # must timezone-aware
        if broadcasted_at.tzinfo is None:
            raise ValueError("broadcasted_at must be timezone-aware.")

    utcnow = get_now()
    cached_xml = get_closest_cached_rss_file(utcnow, prefix_dir, suffix_dir)

    feed: feedparser.FeedParserDict
    if cached_xml is None:
        # キャッシュが見つからなかった場合は、リクエストを送信する
        raw_xml: str = fetch_rss(url=target_url)
        feed, last_build_date = parse_rss(raw_xml)
        if last_build_date is None:
            raise ValueError("RSS フィードの更新日時が取得できませんでした。")

        # JST
        last_build_date = last_build_date.astimezone(JST)
        # cache upload
        bs_xml = io.BytesIO(raw_xml.encode("utf-8"))
        cached_url = put_rss_xml_file(
            last_build_date=last_build_date,
            prefix_dir=XML_LATEST_ALL_DIR_BASE,
            file=bs_xml,
            suffix_dir=suffix_dir,
        ).public_url
        logger.info(f"RSSフィードを '{cached_url}' にキャッシュしました。")
    else:
        raw_xml = cached_xml.read().decode("utf-8")
        feed, last_build_date = parse_rss(raw_xml)
        if last_build_date is None:
            raise ValueError("RSS フィードの更新日時が取得できませんでした。")

        # JST
        last_build_date = last_build_date.astimezone(JST)
        logger.info("キャッシュからRSSフィードを取得しました。")

    # keyはlink
    mst_map: dict[str, MstBook] = {}
    for entry in feed.get("entries", []):  # type: ignore
        if entry is None:
            continue

        item = convert_to_entry_item(entry)
        logger.info(f"item: {item}")

        # oai_pmh から書誌情報を取得する
        metadata: dict[str, Any] = {}
        thumbnail_link: str = ""
        if item.isbn != "":
            thumbnail_link = thumbnail(item.isbn)
            cached_metadata = get_closest_cached_oai_pmh_file(item.isbn, ISBN_DIR)
            if cached_metadata is None:
                metadata = get_metadata_by_isbn(item.isbn)
                # cacheする
                metadata_json_str = json.dumps(metadata, ensure_ascii=False, indent=2)
                cashed_url = put_oai_pmh_json(
                    item.isbn,
                    ISBN_DIR,
                    metadata_json_str,
                ).public_url
                logger.info(f"isbn metadata を {cashed_url} にキャッシュしました")
            else:
                metadata = json.loads(cached_metadata.read().decode("utf-8"))
                logger.info("キャッシュからisbn metadataを取得しました。")
        elif item.jp_e_code != "":
            thumbnail_link = thumbnail(item.jp_e_code)
            cached_metadata = get_closest_cached_oai_pmh_file(
                item.jp_e_code, JP_E_CODE_DIR
            )
            if cached_metadata is None:
                metadata = get_metadata_by_jp_e_code(item.jp_e_code)
                # cacheする
                metadata_json_str = json.dumps(metadata, ensure_ascii=False, indent=2)
                cached_url = put_oai_pmh_json(
                    item.jp_e_code,
                    JP_E_CODE_DIR,
                    metadata_json_str,
                ).public_url
                logger.info(f"jp_e_code metadata {cached_url} にキャッシュしました")
            else:
                metadata = json.loads(cached_metadata.read().decode("utf-8"))
                logger.info("キャッシュからjp_e_code metadataを取得しました。")
        else:
            logger.error(f"isbn または jp_e_code が取得できませんでした。: {item}")

        # mapに格納
        mst_map[item.link] = MstBook(
            title=item.title,
            summary=item.summary,
            isbn=item.isbn,
            jp_e_code=item.jp_e_code,
            link=item.link,
            thumbnail_link=thumbnail_link,
            published=item.published or utcnow,
            metadata=metadata,
        )

    # ここで、entryMapを使って、combined masterdataを作成する
    rss_sig = last_build_date.strftime("%Y%m%d_%H%M%S_0900")
    # 作成したcombined masterdataをGCSにアップロードする
    # entityMapをまずはそのままjsonにしてみる
    mst_books = MstBooks(mst_map)
    mst_books_json_str = mst_books.model_dump_json(indent=2)
    result_blob = put_combined_json_file(rss_sig, mst_books_json_str)
    logger.info(f"combined masterdata を '{result_blob.name}' にアップロードしました。")
    if result_blob is None:
        raise ValueError("combined masterdata がアップロードできませんでした。")

    # Firestore recordをここで creating で作成する
    creating = entity_radio_show.new(result_blob.name, broadcasted_at)
    logger.info(f"[COMMAND] radio_show.new creating: {creating}")

    # 後続処理はeventarcが行う

    return


def exec_run_agent_and_tts_workflow(
    radio_show_id: str,
    masterdata_blob_path: str,
    exec_date: datetime | None = None,
) -> None:
    logger.info("start exec_run_agent_and_tts_workflow ...")
    logger.info(
        f"radio_show_id: {radio_show_id}, masterdata_blob_path: {masterdata_blob_path}, exec_date: {exec_date}"
    )
    if masterdata_blob_path == "":
        raise ValueError("masterdata_blob_path is empty.")
    if exec_date is not None:
        # must timezone-aware
        if exec_date.tzinfo is None:
            raise ValueError("broadcasted_at must be timezone-aware.")

    # load masterdata
    mst_json = get_json_file(masterdata_blob_path)
    mst_books_loaded = MstBooks.model_validate_json(mst_json)
    logger.info("Success to load masterdata json.")

    # 以降はJSTでの処理
    exec_date_jst = datetime.now(JST)
    if exec_date is not None:
        # 実行対象の日時を上書き
        exec_date_jst = exec_date.astimezone(JST)
    mst_map = mst_books_loaded.root
    past, current, future = split_books(mst_map, exec_date_jst)
    logger.info("Success to split books.")
    logger.info(f"past: {len(past)}, current: {len(current)}, future: {len(future)}")

    # agent: prompting
    # 与えるcontextの順番を一律にするために、keyでソートする
    save_books: list[entity_radio_show.RadioShowBook] = []
    llm_context = ""
    mst_keys = current.keys()
    sorted_mst_keys = sorted(mst_keys)
    for idx, mst_key in enumerate(sorted_mst_keys):
        mst_book = current[mst_key]
        save_books.append(
            entity_radio_show.RadioShowBook(
                title=mst_book.title,
                url=mst_key,
                thumbnail_url=mst_book.thumbnail_link,
                isbn=mst_book.isbn,
                jp_e_code=mst_book.jp_e_code,
            )
        )
        book_prompt = convert_to_book_prompt(mst_book, idx + 1)
        llm_context += book_prompt + "\n"
    logger.info(f"llm_context: {llm_context}")

    # agent: llm -> script
    logger.info("start agent call ...")
    result = agent.call_agent_with_dataset(llm_context)
    logger.info(f"agent call result: {result}")
    # parse script
    script = agent.extract_script_block(result)
    if script is None:
        raise ValueError("script が取得できませんでした。")
    logger.info(f"radio show script: {script}")

    # upload: script
    script_blob = put_tts_script_file(radio_show_id, script)
    script_public_url = script_blob.public_url

    # start: script -> audio
    recorded = tts_google.synthesize(script)
    if recorded is None:
        raise ValueError("recorded が取得できませんでした。")

    bs = io.BytesIO(recorded.audio_content)
    audio_blob = put_tts_audio_file(radio_show_id, bs)
    audio_public_url = audio_blob.public_url

    # created に更新

    entity_radio_show.publish(
        radio_show_id,
        audio_public_url,
        script_public_url,
        save_books,
        broadcasted_at=exec_date_jst,
    )

    return


def convert_to_book_prompt(mst_book: MstBook, number: int) -> str:
    """MstBookをLLMに渡すだけの情報にする"""
    # linkはいらない
    # metadataのnullばっかりの項目はいらない
    # publishedはJSTに変換する
    # thumbnail_linkもいらない

    title = mst_book.title
    summary = mst_book.summary

    # metadataは全ての項目が null の場合はkeyを表示しない
    # 1つでもnullでない場合は表示する(nullは None と表記)
    metadata_str = ""
    keys = mst_book.metadata.keys()
    sorted_keys = sorted(keys)
    for key in sorted_keys:
        # skipして良いkey
        if key in [
            "bibRecordCategory",
            "publicationPlace",
            "title",
            "identifier",
            "price",
            "language",
            "extent",
        ]:
            continue

        mdata = mst_book.metadata[key]
        if mdata is None:
            continue
        # skipパターン
        match mdata:
            case str() if mdata == "":
                continue
            case list() if len(mdata) == 0 or all(x is None for x in mdata):
                continue
            case dict() if len(mdata) == 0 or all(x is None for x in mdata.values()):
                continue
        # displayパターン
        match mdata:
            case str():
                metadata_str += f"* {key}: {mdata}\n"
            case list():
                # tagのようなものにsensitiveが入りやすい。全体に影響を与えるので割愛
                if key in ["value"]:
                    if any(ng_word.is_ng_word(str(d)) for d in mdata):
                        continue

                metadata_str += f"* {key}: {', '.join([str(d) for d in mdata])}\n"

            case dict():
                metadata_str += (
                    f"* {key}: {','.join([f'{k}:{v}' for k, v in mdata.items()])}\n"
                )
            case _:
                logger.warning(f"metadata に未対応の型が含まれています: {mdata}")

    return f"{number}冊目 title:{title}\nsummary:{summary}\nmetadata:\n{metadata_str}"


def split_books(
    mst_books: dict[str, MstBook], target_datetime: datetime
) -> tuple[dict[str, MstBook], dict[str, MstBook], dict[str, MstBook]]:
    """mst_books の各項目の published (UTC) を JST に変換し、
    target_datetime (JST) の日付と比較して、
    過去日、当日、未来日に分類して返す。

    ※ target_datetime は JST タイムゾーンでなければ ValueError を発生させる。
    ※ published が None の場合は、その項目はスキップする。"""
    # target_datetime が timezone-aware かつ JST であるかをチェック
    if target_datetime.tzinfo is None:
        raise ValueError("target_datetime must be timezone-aware and in JST timezone.")
    if target_datetime.tzinfo != JST:
        raise ValueError("target_datetime must be in JST timezone.")

    target_datetime = target_datetime or datetime.now(JST)
    target_date = target_datetime.astimezone(JST).date()

    past: dict[str, MstBook] = {}
    current: dict[str, MstBook] = {}
    future: dict[str, MstBook] = {}

    for link, mst_book in mst_books.items():
        if mst_book.published is None:
            continue

        published_date = mst_book.published.astimezone(JST).date()
        if published_date < target_date:
            past[link] = mst_book
        elif published_date == target_date:
            current[link] = mst_book
        else:
            future[link] = mst_book

    return past, current, future


if __name__ == "__main__":
    # RSSを取得してOAI-PMHを取得して、GCSにアップロードする
    size = 1000
    url = latest_all(size=size)
    print(url)
    jst_date = datetime(2025, 2, 5, 9, 0, 0, tzinfo=JST)
    exec_fetch_rss_and_oai_pmh_workflow(url, "latest_all", str(size), jst_date)
