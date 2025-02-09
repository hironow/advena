from datetime import UTC, datetime
from typing import Any, Callable

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
CALLS_PER_MINUTE = 60
ONE_MINUTE = 60  # 秒


@sleep_and_retry
@limits(calls=CALLS_PER_MINUTE, period=ONE_MINUTE)
@retry(
    wait=wait_exponential(multiplier=1, min=2, max=60),  # 最初は2秒、最大60秒まで待機
    stop=stop_after_attempt(5),  # 最大5回の試行
    retry=retry_if_exception_type(
        httpx.HTTPStatusError
    ),  # 任意の例外が発生したらリトライ
)
def fetch_rss(url: str) -> str:
    """httpx を使って RSS フィードを取得する関数。"""
    response = httpx.get(url, timeout=30)  # タイムアウトは 30 秒
    response.raise_for_status()
    raw_xml = response.text
    return raw_xml


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

    # 厳密にすると今後の変更に追随できないので `construct` でゆるい型チェックにする
    return FeedEntry.construct(**data)


def generate_filename_from_date(dt: datetime) -> str:
    """datetime オブジェクトから、ファイル名として使用可能なフォーマット（YYYYMMDD_HHMMSS.xml）を生成する関数。この時刻ファイル名なので、JST時刻を使用する。"""
    dt = dt.astimezone(timezone("Asia/Tokyo"))
    return dt.strftime("%Y%m%d_%H%M%S_0900.xml")


def fetch_and_cache_rss(url: str) -> None:
    """
    httpx で RSS フィードを取得し、feedparser でパースした後、
    更新日時を用いて安全なファイル名を生成し、生の XML をキャッシュとして保存する関数。

    ※更新日時が取得できない場合は、現在日時を使用してファイル名を作成します。
    """
    # URL から生 XML を取得
    raw_xml = _fetch_rss(url)

    # 生 XML から feedparser でパースし、更新日時を取得
    feed, last_build_date = parse_rss(raw_xml)

    # 更新日時が取得できなかった場合は、現在日時を利用
    if last_build_date is None:
        last_build_date = datetime.now()

    filename = generate_filename_from_date(last_build_date)

    # XML をファイルに保存（UTF-8 エンコード推奨）
    with open(filename, "w", encoding="utf-8") as f:
        f.write(raw_xml)

    print(f"RSSフィードを '{filename}' にキャッシュしました。")


def _parse_rss_from_file(file_path: str):
    """キャッシュ済みの XML ファイルから RSS フィードをパースする関数。"""
    with open(file_path, "r", encoding="utf-8") as f:
        raw_xml = f.read()
    feed, _ = parse_rss(raw_xml)
    return feed


# TODO: feed item の型をpydanticで定義後に対応する
def split_by_date(
    feed_items: list[dict[str, Any]], date_picker: Callable[[dict[str, Any]], str]
):
    """日付でフィードアイテムを分割する。過去のもの、今日のもの、未来のものの3つにする
    date_pickerは、feed_itemの1つであるdictを受け取り内部のdateの対象となる文字列を返す関数
    """
    today = date_picker({})
    past_items = []
    today_items = []
    future_items = []

    for item in feed_items:
        date = date_picker(item)
        if date < today:
            past_items.append(item)
        elif date == today:
            today_items.append(item)
        else:
            future_items.append(item)

    return past_items, today_items, future_items


if __name__ == "__main__":
    rss_url = "https://ndlsearch.ndl.go.jp/rss/ndls/bib.xml?cs=bib&display=panel&from=0&size=1000&sort=published%3Adesc&f-ht=ndl&f-ht=library&f-repository=R100000137&f-doc_style=digital&f-doc_style=paper&f-mt=dtbook&f-mt=dbook"
    fetch_and_cache_rss(rss_url)
