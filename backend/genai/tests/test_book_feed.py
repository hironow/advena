import time
from datetime import UTC, datetime

import feedparser
import httpx
import pytest
import tenacity

from src.book.feed import convert_to_entry_item, fetch_rss, parse_rss
from src.logger import logger


# FakeResponse の定義（すでに定義済みの場合はそのまま利用）
class FakeResponse:
    def __init__(
        self, text: str, status_code: int = 200, raise_exception: bool = False
    ):
        self.text = text
        self.status_code = status_code
        self.raise_exception = raise_exception

    def raise_for_status(self):
        if self.raise_exception:
            # httpx.HTTPStatusError は request, response を受け取るので、ここではダミーとして None を渡す
            raise httpx.HTTPStatusError("Dummy error", request=None, response=self)


def test_fetch_rss_success(monkeypatch):
    """正常系: httpx.get で取得した RSS XML が返る"""
    dummy_xml = "<rss><channel><title>Test Feed</title></channel></rss>"

    def fake_get(url, timeout):
        return FakeResponse(dummy_xml, status_code=200)

    # httpx.get を差し替え
    monkeypatch.setattr(httpx, "get", fake_get)

    result = fetch_rss("http://dummy.url/rss")
    assert result == dummy_xml


@pytest.mark.skip("adhoc")
def test_fetch_rss_retry_failure(monkeypatch):
    """失敗系: HTTPStatusError を毎回発生させ、最終的にリトライ上限に達して RetryError が上がること、
    かつリトライ回数が 5 回であることを検証"""

    call_count = {"count": 0}

    def fake_get(url, timeout):
        call_count["count"] += 1
        return FakeResponse("", status_code=500, raise_exception=True)

    # テスト中の待ち時間をゼロにするため、time.sleep を no-op に置き換え
    monkeypatch.setattr(time, "sleep", lambda seconds: None)
    monkeypatch.setattr(httpx, "get", fake_get)

    with pytest.raises(tenacity.RetryError) as exc_info:
        fetch_rss("http://dummy.url/rss")

    # リトライ上限は 5 回（初回含めて計 5 回）なので
    assert call_count["count"] == 5

    # 内部の最後の例外が HTTPStatusError であることを確認
    assert isinstance(exc_info.value.last_attempt.exception(), httpx.HTTPStatusError)


def test_parse_rss_with_updated(monkeypatch):
    """feed に updated_parsed が存在する場合、正しい日時が得られること"""
    dummy_struct = (2025, 2, 9, 10, 20, 30, 0, 0, 0)

    def fake_parse(xml):
        return feedparser.FeedParserDict({"feed": {"updated_parsed": dummy_struct}})

    monkeypatch.setattr(feedparser, "parse", fake_parse)
    raw_xml = "<dummy>ignored</dummy>"
    feed, last_build_date = parse_rss(raw_xml)
    expected_date = datetime(2025, 2, 9, 10, 20, 30, tzinfo=UTC)
    assert last_build_date == expected_date
    # feed は fake_parse が返すオブジェクトであること
    assert feed.get("feed", {}).get("updated_parsed") == dummy_struct


def test_parse_rss_with_published(monkeypatch):
    """updated_parsed が無い場合、published_parsed を使って日時が取得できること"""
    dummy_struct = (2025, 2, 9, 10, 20, 30, 0, 0, 0)

    def fake_parse(xml):
        return feedparser.FeedParserDict({"feed": {"published_parsed": dummy_struct}})

    monkeypatch.setattr(feedparser, "parse", fake_parse)
    raw_xml = "<dummy>ignored</dummy>"
    feed, last_build_date = parse_rss(raw_xml)
    expected_date = datetime(2025, 2, 9, 10, 20, 30, tzinfo=UTC)
    assert last_build_date == expected_date


def test_parse_rss_no_date(monkeypatch):
    """更新日時が取得できない場合、None が返され、警告ログが出力されること"""

    def fake_parse(xml):
        return feedparser.FeedParserDict(
            {
                "feed": {
                    # どちらのフィールドも存在しない
                }
            }
        )

    monkeypatch.setattr(feedparser, "parse", fake_parse)

    # logger.warning の呼び出しを記録するための仕掛け
    warning_messages = []

    def fake_warning(msg):
        warning_messages.append(msg)

    monkeypatch.setattr(logger, "warning", fake_warning)

    raw_xml = "<dummy>ignored</dummy>"
    feed, last_build_date = parse_rss(raw_xml)
    assert last_build_date is None
    assert any("更新日時が取得できませんでした" in msg for msg in warning_messages)


def dummy_published_parsed():
    # published_parsed として利用する tuple。最初6要素で日時を構成する
    return (2025, 2, 9, 10, 20, 30, 0, 0, 0)


def test_convert_to_entry_item_isbn():
    """id により ISBN が抽出されるケース"""
    dummy_feed = feedparser.FeedParserDict(
        {
            "title": "Test Title",
            "title_detail": {"type": "text"},
            "links": [{"href": "http://example.com"}],
            "link": "http://example.com",
            "summary": "Test summary",
            "summary_detail": {"type": "html"},
            "id": "https://ndlsearch.ndl.go.jp/books/R100000137-I9784798073972",
            "guidislink": True,
            "tags": [{"term": "test"}],
            "published_parsed": dummy_published_parsed(),
        }
    )
    entry = convert_to_entry_item(dummy_feed)
    expected_date = datetime(2025, 2, 9, 10, 20, 30, tzinfo=UTC)
    assert entry.title == "Test Title"
    assert entry.published == expected_date
    assert entry.repo == "R100000137"
    assert entry.isbn == "9784798073972"
    assert entry.jp_e_code == ""


def test_convert_to_entry_item_jpe():
    """id により JP-eコード が抽出されるケース"""
    # JP-eコードは signature の長さが20文字の場合に抽出される
    dummy_feed = feedparser.FeedParserDict(
        {
            "title": "Test Title",
            "title_detail": {"type": "text"},
            "links": [{"href": "http://example.com"}],
            "link": "http://example.com",
            "summary": "Test summary",
            "summary_detail": {"type": "html"},
            "id": "https://ndlsearch.ndl.go.jp/books/R100000137-I01234567890123456789",
            "guidislink": True,
            "tags": [{"term": "test"}],
            "published_parsed": dummy_published_parsed(),
        }
    )
    entry = convert_to_entry_item(dummy_feed)
    assert entry.repo == "R100000137"
    assert entry.isbn == ""
    assert entry.jp_e_code == "01234567890123456789"


def test_convert_to_entry_item_empty_id():
    """id が空文字の場合、repo, isbn, jp_e_code は空文字のままであること"""
    dummy_feed = feedparser.FeedParserDict(
        {
            "title": "Test Title",
            "published_parsed": dummy_published_parsed(),
        }
    )
    entry = convert_to_entry_item(dummy_feed)
    assert entry.repo == ""
    assert entry.isbn == ""
    assert entry.jp_e_code == ""
