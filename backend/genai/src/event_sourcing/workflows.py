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
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

import feedparser  # type: ignore
from pydantic import BaseModel, RootModel

from src.blob.storage import (
    ISBN_DIR,
    JP_E_CODE_DIR,
    XML_LATEST_ALL_DIR_BASE,
    get_closest_cached_oai_pmh_file,
    get_closest_cached_rss_file,
    put_oai_pmh_json,
    put_rss_xml_file,
)
from src.book.book import latest_all, thumbnail
from src.book.feed import convert_to_entry_item, fetch_rss, parse_rss
from src.book.oai_pmh import get_metadata_by_isbn, get_metadata_by_jp_e_code
from src.logger import logger
from src.utils import get_now

JST = ZoneInfo("Asia/Tokyo")


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
    target_url: str, prefix_dir: str, suffix_dir: str
) -> None:
    """RSSを取得してGCSにアップロードする"""
    utcnow = get_now()
    cached_xml = get_closest_cached_rss_file(utcnow, prefix_dir, suffix_dir)

    feed: feedparser.FeedParserDict
    if cached_xml is None:
        # キャッシュが見つからなかった場合は、リクエストを送信する
        raw_xml: str = fetch_rss(url=target_url)

        feed, last_build_date = parse_rss(raw_xml)
        if last_build_date is None:
            raise ValueError("RSS フィードの更新日時が取得できませんでした。")

        # UTC -> JST
        last_build_date = last_build_date.astimezone(ZoneInfo("Asia/Tokyo"))
        cache_signature = f"{last_build_date.strftime('%Y%m%d_%H%M%S_0900')}"
        # cache upload
        bs_xml = io.BytesIO(raw_xml.encode("utf-8"))
        result_url = put_rss_xml_file(
            signature=cache_signature,
            prefix_dir=XML_LATEST_ALL_DIR_BASE,
            file=bs_xml,
            suffix_dir=suffix_dir,
        )
        logger.info(f"RSSフィードを '{result_url}' にキャッシュしました。")
    else:
        raw_xml = cached_xml.read().decode("utf-8")
        feed, last_build_date = parse_rss(raw_xml)
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
                put_oai_pmh_json(
                    item.isbn,
                    ISBN_DIR,
                    metadata_json_str,
                )
                logger.info("isbn metadata をキャッシュしました")
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
                put_oai_pmh_json(
                    item.jp_e_code,
                    JP_E_CODE_DIR,
                    metadata_json_str,
                )
                logger.info("jp_e_code metadata をキャッシュしました")
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
    # 作成したcombined masterdataをGCSにアップロードする
    # entityMapをまずはそのままjsonにしてみる
    mst_books = MstBooks(mst_map)
    # mst_books_json = mst_books.model_dump_json(indent=2)
    # 適当なファイルへ
    # with open("./combined_masterdata.json", "w", encoding="utf-8") as f:
    #     f.write(mst_books_json)
    #     logger.info("combined_masterdata.json に書き込みました。")

    # 読み込みテスト
    # with open("./combined_masterdata.json", "r", encoding="utf-8") as f:
    #     json_data = f.read()
    #     mst_books_loaded = MstBooks.model_validate_json(json_data)
    #     # logger.info(f"mst_books_loaded: {mst_books_loaded}")

    #     dumped_mst_books = mst_books_loaded.model_dump()
    #     # 件数を表示したい
    #     logger.info(f"mst_books_loaded: {len(dumped_mst_books.keys())} 件")

    # JSTの2月6日のdatetime
    target_datetime = datetime(2025, 2, 6, 9, 0, 0, tzinfo=JST)

    past, current, future = split_books(mst_map, target_datetime)

    # 件数を表示したい
    logger.info(f"past: {len(past)} 件")
    logger.info(f"current: {len(current)} 件")
    logger.info(f"future: {len(future)} 件")

    # currentだけをjsonにしてみる
    mst_books_current = MstBooks(current)
    mst_books_current_json = mst_books_current.model_dump_json(indent=2)
    # 適当なファイルへ
    with open("./combined_masterdata_current.json", "w", encoding="utf-8") as f:
        f.write(mst_books_current_json)
        logger.info("combined_masterdata_current.json に書き込みました。")

    # LLMに渡すやつ
    llm_input = "current_text.txt"
    i = ""
    for _, mst_book in current.items():
        book_prompt = convert_to_book_prompt(mst_book)
        logger.info(f"{book_prompt}")
        logger.info("---")

        i += book_prompt + "\n"
        i += "---\n"

    with open(llm_input, "w", encoding="utf-8") as f:
        f.write(i)
        logger.info("current_text.txt に書き込みました。")


def convert_to_book_prompt(mst_book: MstBook) -> str:
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
        if key in ["bibRecordCategory", "publicationPlace"]:
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
                metadata_str += f"* {key}: {', '.join([str(d) for d in mdata])}\n"
            case dict():
                metadata_str += (
                    f"* {key}: {','.join([f'{k}:{v}' for k, v in mdata.items()])}\n"
                )
            case _:
                logger.warning(f"metadata に未対応の型が含まれています: {mdata}")

    return f"title:{title}\nsummary:{summary}\nmetadata:\n{metadata_str}"


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
    if target_datetime.tzinfo != ZoneInfo("Asia/Tokyo"):
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
    url = latest_all(size=1000)
    print(url)
    exec_fetch_rss_and_oai_pmh_workflow(url, "latest_all", "1000")
