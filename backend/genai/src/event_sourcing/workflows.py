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
from typing import Any
from zoneinfo import ZoneInfo

import feedparser
import httpx

from src.blob.storage import (
    ISBN_DIR,
    JP_E_CODE_DIR,
    get_closest_cached_oai_pmh_file,
    get_closest_cached_rss_file,
    put_oai_pmh_json,
    put_rss_xml_file,
)
from src.book.book import latest_all
from src.book.feed import convert_to_entry_item, parse_rss
from src.book.oai_pmh import get_metadata_by_isbn, get_metadata_by_jp_e_code
from src.logger import logger
from src.utils import get_now


def exec_rss_workflow(target_url: str, prefix_dir: str) -> None:
    """RSSを取得してGCSにアップロードする"""
    utcnow = get_now()
    jstnow = utcnow.astimezone(ZoneInfo("Asia/Tokyo"))
    target_signature = f"{jstnow.strftime('%Y%m%d_%H%M%S_0900')}.xml"
    logger.info(f"RSSフィードを '{target_signature}' あたりから取得します。")

    cached_xml = get_closest_cached_rss_file(utcnow, prefix_dir)

    feed: feedparser.FeedParserDict
    if cached_xml is None:
        # キャッシュが見つからなかった場合は、リクエストを送信する
        response = httpx.get(target_url)
        response.raise_for_status()
        raw_xml = response.text

        feed, last_build_date = parse_rss(raw_xml)
        if last_build_date is None:
            raise ValueError("RSS フィードの更新日時が取得できませんでした。")

        # UTC -> JST
        last_build_date = last_build_date.astimezone(ZoneInfo("Asia/Tokyo"))
        cache_signature = f"{last_build_date.strftime('%Y%m%d_%H%M%S_0900')}.xml"
        # cache upload
        bs_xml = io.BytesIO(raw_xml.encode("utf-8"))
        logger.info(f"RSSフィードを '{cache_signature}' にアップロードします。")
        result_url = put_rss_xml_file(cache_signature, "latest_all", bs_xml)
        logger.info(f"RSSフィードを '{result_url}' にキャッシュしました。")
    else:
        logger.info("キャッシュからRSSフィードを取得します。")
        raw_xml = cached_xml.read().decode("utf-8")
        feed, last_build_date = parse_rss(raw_xml)
        logger.info("キャッシュからRSSフィードを取得しました。")

    for entry in feed.get("entries", []):
        if entry is None:
            continue

        item = convert_to_entry_item(entry)
        logger.info(f"item: {item}")

        # oai_pmh から書誌情報を取得する

        metadata: dict[str, Any] = {}
        if item.isbn:
            cached_metadata = get_closest_cached_oai_pmh_file(item.isbn, ISBN_DIR)
            if cached_metadata is None:
                metadata = get_metadata_by_isbn(item.isbn)
                # cacheする
                logger.info("isbn metadata をキャッシュします")
                metadata_json_str = json.dumps(metadata, ensure_ascii=False, indent=2)
                put_oai_pmh_json(
                    item.isbn,
                    ISBN_DIR,
                    metadata_json_str,
                )
                logger.info("isbn metadata をキャッシュしました")
            else:
                logger.info(f"cached isbn data found: {item.isbn}")
                metadata = json.loads(cached_metadata.read().decode("utf-8"))
        elif item.jp_e_code:
            cached_metadata = get_closest_cached_oai_pmh_file(
                item.jp_e_code, JP_E_CODE_DIR
            )
            if cached_metadata is None:
                metadata = get_metadata_by_jp_e_code(item.jp_e_code)
                # cacheする
                logger.info("jp_e_code metadata をキャッシュします")
                metadata_json_str = json.dumps(metadata, ensure_ascii=False, indent=2)
                put_oai_pmh_json(
                    item.isbn,
                    JP_E_CODE_DIR,
                    metadata_json_str,
                )
                logger.info("jp_e_code metadata をキャッシュしました")
            else:
                logger.info(f"cached jp_e_code data found: {item.isbn}")
                metadata = json.loads(cached_metadata.read().decode("utf-8"))

        logger.info(f"metadata: {metadata}")

        # metadataをjsonにする
        # metadata_json = json.dumps(metadata, ensure_ascii=False)
        # logger.info(f"metadata: {metadata_json}")

        break


if __name__ == "__main__":
    # RSSを取得してOAI-PMHを取得して、GCSにアップロードする
    url = latest_all(10)
    print(url)
    exec_rss_workflow(url, "latest_all")
