from datetime import datetime
from typing import Any, Callable

import feedparser


def parse_rss(url: str):
    """RSSフィードをパース"""
    feed = feedparser.parse(url)

    # チャンネル情報を表示
    print("Feed Title:", feed.feed.get("title"))
    print("Feed Link:", feed.feed.get("link"))
    print("Feed Last Build Date:", feed.feed.get("lastbuilddate"))
    print()

    # 各アイテムを処理
    for entry in feed.entries:
        title = entry.get("title")
        link = entry.get("link")
        description = entry.get("description")
        published = entry.get("published")

        print(f"Title: {title}")
        print(f"Link: {link}")
        print(f"Description: {description}")
        print(f"Published: {published}")
        print("-" * 40)


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
    rss_url = "https://ndlsearch.ndl.go.jp/rss/ndls/bib.xml?cs=bib&display=panel&from=0&size=10&sort=published:desc&f-ht=ndl&f-ht=library&f-repository=R100000137&f-doc_style=digital&f-doc_style=paper&f-mt=dtbook&f-mt=dbook"
    parse_rss(rss_url)
