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


def parse_oai_pmh(url: str):
    """OAI-PMHをパース"""
    pass


if __name__ == "__main__":
    rss_url = "https://ndlsearch.ndl.go.jp/rss/ndls/bib.xml?cs=bib&display=panel&from=0&size=10&sort=published:desc&f-ht=ndl&f-ht=library&f-repository=R100000137&f-doc_style=digital&f-doc_style=paper&f-mt=dtbook&f-mt=dbook"
    parse_rss(rss_url)
