from datetime import UTC, datetime
from typing import Any

import feedparser  # type: ignore
import httpx
from pydantic import BaseModel
from ratelimit import limits, sleep_and_retry  # type: ignore
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from src.logger import logger

# レート制限の設定（例: 1分間に最大60回＝1秒あたり1回）
CALLS_PER_MINUTE = 60  # 回
ONE_MINUTE = 60  # 秒


def fetch_rss(url: str) -> str:
    """httpx を使って RSS フィードを取得する関数。"""
    try:
        response = httpx.get(url, timeout=300)  # タイムアウトは 300 秒 = 5 分
        response.raise_for_status()
        raw_xml = response.text
        return raw_xml
    except httpx.HTTPError as exc:
        logger.error(f"HTTP Exception for {exc.request.url} - {exc}")
        return ""


def parse_rss(raw_xml: str) -> tuple[feedparser.FeedParserDict, datetime | None]:
    """
    生の XML 文字列から feedparser を使って RSS フィードをパースし、
    更新日時（updated_parsed または published_parsed）を取得する関数。
    返り値の時刻は必ずUTCとして扱う。

    戻り値は、パース結果の feedparser オブジェクトと、更新日時を表す datetime オブジェクト（存在する場合）。
    """
    feed = feedparser.parse(raw_xml)  # type: ignore
    # updated_parsed がなければ published_parsed を使用
    last_build_date_struct = feed.feed.get(  # type: ignore
        "updated_parsed",
        feed.feed.get("published_parsed"),  # type: ignore
    )
    if last_build_date_struct:
        # time.struct_time（9要素）の先頭6要素 (year, month, day, hour, minute, second) から datetime を生成
        last_build_date = datetime(*last_build_date_struct[:6], tzinfo=UTC)  # type: ignore
    else:
        logger.warning("RSS フィードの更新日時が取得できませんでした。")
        last_build_date = None
    return feed, last_build_date


class FeedEntry(BaseModel):
    title: str = ""
    title_detail: dict[str, Any] = {}
    links: list[dict[str, Any]] = []
    link: str = ""
    summary: str = ""
    summary_detail: dict[str, Any] = {}
    id: str = ""
    guidislink: bool = False
    tags: list[dict[str, Any]] = []
    published: datetime | None = None
    # このデータ用の追加フィールド
    repo: str = ""
    isbn: str = ""
    jp_e_code: str = ""

    class Config:
        # feedparser のデータは想定外のキーも持つので許容する
        extra = "allow"


def convert_to_entry_item(feed: feedparser.FeedParserDict) -> FeedEntry:
    """feedparser.FeedParserDict を FeedEntry に変換する関数。"""
    # published_parseを使ってutc datetimeに変換
    published_date = None
    published_parsed = feed.get("published_parsed")
    published_date = datetime(*published_parsed[:6], tzinfo=UTC)

    # linkの末尾を取り出し `https://ndlsearch.ndl.go.jp/books/R100000137-I9784798073972`
    # `R100000137-I9784798073972` のように 13桁をISBN
    # `R100000137-I09D154490010d0000000` のように 20桁をJP-eコード
    # として取り出す I が先頭についているので取り除くことに注意
    link_id: str = feed.get("id", "")
    repo = ""
    isbn = ""
    jp_e_code = ""
    if link_id != "":
        last_part = link_id.split("/")[-1]
        parts = last_part.split("-")
        if len(parts) == 2:
            parts[1] = parts[1]
            repo = parts[0]
            signature = parts[1][1:]  # 先頭の1文字(I)を取り除く
            if len(signature) == 13:  # ISBN
                isbn = signature
            elif len(signature) == 20:  # JP-eコード
                jp_e_code = signature

    data: dict[str, Any] = {
        "title": feed.get("title", ""),
        "title_detail": feed.get("title_detail", {}),
        "links": feed.get("links", []),
        "link": feed.get("link", ""),
        "summary": feed.get("summary", ""),
        "summary_detail": feed.get("summary_detail", {}),
        "id": feed.get("id", ""),
        "guidislink": feed.get("guidislink", False),
        "tags": feed.get("tags", []),
        "published": published_date,
        "repo": repo,
        "isbn": isbn,
        "jp_e_code": jp_e_code,
    }

    # NOTE: 厳密にすると今後の変更に追随できないので `construct` でゆるい型チェックにする
    return FeedEntry.construct(**data)
