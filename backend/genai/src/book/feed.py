from datetime import datetime
from typing import Any, Callable

import feedparser  # type: ignore
import httpx


def _fetch_rss(url: str) -> str:
    response = httpx.get(url)
    response.raise_for_status()  # ステータスコードが 200 以外の場合は例外を発生
    return response.text


def parse_rss(raw_xml: str):
    """
    生の XML 文字列から feedparser を使って RSS フィードをパースし、
    更新日時（updated_parsed または published_parsed）を取得する関数。

    戻り値は、パース結果の feedparser オブジェクトと、更新日時を表す datetime オブジェクト（存在する場合）。
    """
    feed = feedparser.parse(raw_xml)
    # updated_parsed がなければ published_parsed を使用
    last_build_date_struct = feed.feed.get(
        "updated_parsed", feed.feed.get("published_parsed")
    )
    if last_build_date_struct:
        # time.struct_time（9要素）の先頭6要素 (year, month, day, hour, minute, second) から datetime を生成
        last_build_date = datetime(*last_build_date_struct[:6])
        print("Raw lastBuildDate:", last_build_date_struct)
        print("Datetime lastBuildDate:", last_build_date)
    else:
        print("更新日時が見つかりませんでした。")
        last_build_date = None
    return feed, last_build_date


def _generate_filename_from_date(dt: datetime) -> str:
    """datetime オブジェクトから、ファイル名として使用可能なフォーマット（YYYYMMDD_HHMMSS.xml）を生成する関数。"""
    return dt.strftime("%Y%m%d_%H%M%S.xml")


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

    filename = _generate_filename_from_date(last_build_date)

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
