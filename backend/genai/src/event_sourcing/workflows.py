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
from datetime import datetime
from zoneinfo import ZoneInfo

import httpx

from src.blob.storage import put_rss_xml_file
from src.book.book import FeedItem, latest_all
from src.book.feed import parse_rss
from src.logger import logger
from src.utils import get_now


def exec_rss_workflow(target_url: str, suffix: str) -> None:
    """RSSを取得してGCSにアップロードする"""
    # TODO: 対象のURLがキャッシュされている可能性があり、本日時点のRSSがあるかを確認する

    utcnow = get_now()
    jstnow = utcnow.astimezone(ZoneInfo("Asia/Tokyo"))
    target_signature = f"{jstnow.strftime('%Y%m%d_%H%M%S_0900')}_{suffix}.xml"
    logger.info(f"RSSフィードを '{target_signature}' あたりから取得します。")

    response = httpx.get(target_url)
    response.raise_for_status()
    raw_xml = response.text

    # feedのlastBuildDateをcacheの識別に利用する
    feed, last_build_date = parse_rss(raw_xml)
    if last_build_date is None:
        raise ValueError("RSS フィードの更新日時が取得できませんでした。")
    # UTC -> JST
    last_build_date = last_build_date.astimezone(ZoneInfo("Asia/Tokyo"))
    cache_signature = (
        f"{last_build_date.strftime('%Y%m%d_%H%M%S_0900')}_{suffix}.xml"
    )
    # GCSにアップロード
    bs_xml = io.BytesIO(raw_xml.encode("utf-8"))
    logger.info(f"RSSフィードを '{cache_signature}' にアップロードします。")
    result_url = put_rss_xml_file(cache_signature, bs_xml)
    logger.info(f"RSSフィードを '{result_url}' にキャッシュしました。")

    # feed parseにより結果を型付け
    # FeedParserDictから取り出していく
    # for entry in feed.entries:
    #     feed_item = FeedItem(
    #         title=entry.title,
    #         link=entry.link,
    #         description=entry.description,
    #         guid_url=entry.guid,
    #         guid_isPermaLink=entry.guidisPermaLink,
    #         guid=entry.guid,
    #         category=entry.category,
    #         pubDate=datetime(*entry.published_parsed[:6], tzinfo=ZoneInfo("UTC")),
    #     )
    #     logger.info(feed_item)


if __name__ == "__main__":
    # RSSを取得してGCSにアップロードする
    url = latest_all(10)
    print(url)
    exec_rss_workflow(url, "latest_all")
