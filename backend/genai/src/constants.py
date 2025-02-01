from urllib.parse import urlencode

# 国立国会図書館サーチの RSS フィード
RSS_URL_BASE = "https://ndlsearch.ndl.go.jp/rss/ndls/bib.xml"

# 書影API
# see: https://ndlsearch.ndl.go.jp/help/api/thumbnail
THUMBNAIL_URL_BASE = "https://ndlsearch.ndl.go.jp/thumbnail/"

# OAI-PMH
# 詳細データを取る用 metadataPrefix は dcndl (DC-NDL(RDF)) の方が詳細情報が多い
# 例: https://ndlsearch.ndl.go.jp/api/oaipmh?verb=GetRecord&metadataPrefix=oai_dc&identifier=oai:ndlsearch.ndl.go.jp:R100000137-I9784621310328
# 例: https://ndlsearch.ndl.go.jp/api/oaipmh?verb=GetRecord&metadataPrefix=dcndl&identifier=oai:ndlsearch.ndl.go.jp:R100000137-I9784621310328
# see: https://ndlsearch.ndl.go.jp/help/api/oai_pmh
OAI_PMH_URL_BASE = "https://ndlsearch.ndl.go.jp/api/oaipmh"

# 出版情報登録センター (JPRO)
# see: https://ndlsearch.ndl.go.jp/help/api/provider
JPRO_REPOSITORY = "R100000137"


def thumbnail(isbn: str) -> str:
    """書影画像を取得するための URL を生成する
    例: https://ndlsearch.ndl.go.jp/thumbnail/9784422311074.jpg
    """
    # ハイフンがあれば取り除く
    isbn = isbn.replace("-", "")
    # ISBN は 13 桁でハイフン区切りなし。NOTE: JP-eコードは 20 桁で区切りなしだが、ここでは ISBN のみを想定する
    if len(isbn) != 13:
        raise ValueError("ISBN should be 13 digits")

    return f"{THUMBNAIL_URL_BASE}{isbn}.jpg"


def latest_all(size: int = 1000) -> str:
    """最新の全ての資料を取得するための URL を生成する
    期待する URL query string は:
    ?cs=bib&display=panel&from=0&size=1000&sort=published%3Adesc&f-ht=ndl&f-ht=library&f-repository=R100000137&f-doc_style=digital&f-doc_style=paper&f-mt=dtbook&f-mt=dbook

    item の例:
    <title>はじめての　シールえほん　ぺたぺた　ミッフィー / ディック・ブルーナ イラストほか</title>
    <link>https://ndlsearch.ndl.go.jp/books/R100000137-I9784065386859</link>
    <description>ディック・ブルーナ イラスト; 講談社 編集. はじめての　シールえほん　ぺたぺた　ミッフィー. 講談社. ISBN:9784065386859</description>
    <guid isPermaLink="true">https://ndlsearch.ndl.go.jp/books/R100000137-I9784065386859</guid>
    <category>図書</category>
    <pubDate>Sat, 21 Dec 2024 18:46:00 +0900</pubDate>
    """
    if size > 1000:
        size = 1000
    if size < 1:
        size = 1

    params: dict[str, str | list[str]] = {
        "cs": "bib",
        "display": "panel",
        "from": "0",
        "size": str(size),
        "sort": "published:desc",  # ':' は自動的にエスケープされるので、'%3A' と明示する必要はない
        "f-ht": ["ndl", "library"],  # 複数の f-ht パラメータをリストで指定
        "f-repository": JPRO_REPOSITORY,
        "f-doc_style": ["digital", "paper"],  # 複数指定の場合
        "f-mt": ["dtbook", "dbook"],
    }
    # doseq=True を指定することで、リストの各要素が個別のパラメータとしてエンコードされる
    query_string = urlencode(params, doseq=True)
    return f"{RSS_URL_BASE}?{query_string}"


def latest_with_keywords(keywords: list[str], size: int = 100) -> str:
    """最新の資料をキーワードで検索するための URL を生成する
    期待する URL query string は:
    ?cs=bib&display=panel&from=0&size=20&keyword=AI%20LLM%20%E3%82%A8%E3%83%B3%E3%82%B8%E3%83%8B%E3%82%A2&f-ht=ndl&f-ht=library

    NOTE: keywordの順序で返り値は変わらないことを期待する
    """
    if size > 100:
        size = 100
    if size < 1:
        size = 1

    params: dict[str, str | list[str]] = {
        "cs": "bib",
        "display": "panel",
        "from": "0",
        "size": str(size),
        "sort": "published:desc",
        "f-ht": ["ndl", "library"],
        "f-repository": JPRO_REPOSITORY,
        "f-doc_style": ["digital", "paper"],
        "f-mt": ["dtbook", "dbook"],
        "keyword": keywords,  # リストをそのまま指定
    }
    query_string = urlencode(params, doseq=True)
    return f"{RSS_URL_BASE}?{query_string}"


if __name__ == "__main__":
    url = latest_all()
    print(url)

    url = latest_with_keywords(["AI", "LLM", "エンジニア"])
    print(url)
