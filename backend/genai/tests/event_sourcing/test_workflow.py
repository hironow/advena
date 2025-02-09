from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from src.event_sourcing.workflows import MstBook, split_books


def test_split_books_classification():
    """
    各書籍が target_datetime に対して、過去日、当日、未来日それぞれに分類されるかテストする。
    """
    # 基準日時を 2025-02-11 12:00:00（ローカルタイム、タイムゾーン無し）とする
    target_datetime = datetime(2025, 2, 11, 12, 0, 0)

    books = {
        "book_past": MstBook(
            title="Past Book",
            link="link1",
            thumbnail_link="thumb1",
            published=datetime(2025, 2, 10, 10, 0, 0),
        ),
        "book_current": MstBook(
            title="Current Book",
            link="link2",
            thumbnail_link="thumb2",
            published=datetime(2025, 2, 11, 9, 30, 0),
        ),
        "book_future": MstBook(
            title="Future Book",
            link="link3",
            thumbnail_link="thumb3",
            published=datetime(2025, 2, 12, 15, 0, 0),
        ),
    }

    past, current, future = split_books(books, target_datetime)

    assert "book_past" in past, "過去日と判定されるべき書籍が past に含まれていません。"
    assert "book_current" in current, (
        "当日と判定されるべき書籍が current に含まれていません。"
    )
    assert "book_future" in future, (
        "未来日と判定されるべき書籍が future に含まれていません。"
    )


def test_split_books_skip_none():
    """
    published に None が設定されている場合、その項目がスキップされることをテストする。
    """
    target_datetime = datetime(2025, 2, 11, 12, 0, 0)

    # pydantic のバリデーションを回避するため、.construct() を利用して published に None を設定
    book_invalid = MstBook.construct(
        title="Invalid Book",
        link="link_invalid",
        thumbnail_link="thumb_invalid",
        published=None,
        metadata={},
    )
    book_valid = MstBook(
        title="Valid Book",
        link="link_valid",
        thumbnail_link="thumb_valid",
        published=datetime(2025, 2, 11, 12, 0, 0),
    )

    books = {
        "book_invalid": book_invalid,
        "book_valid": book_valid,
    }
    past, current, future = split_books(books, target_datetime)

    # published が None の書籍は全ての分類から除外されるはず
    assert "book_invalid" not in past
    assert "book_invalid" not in current
    assert "book_invalid" not in future
    # book_valid は当日なので、current に分類される
    assert "book_valid" in current


def test_split_books_timezone_consistency():
    """
    JSTとUTCなどタイムゾーンが異なる日時同士で、日付の比較が正しく行われるかテストする。
    例として、JST で 2025-02-11 09:00 は UTC では 2025-02-11 00:00 に相当するため、
    両者の .date() は 2025-02-11 となり、当日として分類されるはず。
    """
    # target_datetime を UTCタイムゾーンで指定
    target_datetime = datetime(2025, 2, 11, 0, 0, 0, tzinfo=ZoneInfo("UTC"))

    # 書籍データをタイムゾーン付きで作成
    book_utc_past = MstBook(
        title="UTC Past Book",
        link="utc_past",
        thumbnail_link="thumb_utc_past",
        published=datetime(2025, 2, 10, 23, 0, 0, tzinfo=ZoneInfo("UTC")),
    )
    # JSTで 2025-02-11 09:00:00 (これは UTCでは 2025-02-11 00:00:00 相当)
    book_jst_current = MstBook(
        title="JST Current Book",
        link="jst_current",
        thumbnail_link="thumb_jst_current",
        published=datetime(2025, 2, 11, 9, 0, 0, tzinfo=ZoneInfo("Asia/Tokyo")),
    )
    # JSTで 2025-02-11 23:30:00（UTCでは 2025-02-11 14:30:00 相当）→ 日付は 2025-02-11 のまま
    book_jst_current2 = MstBook(
        title="JST Current Book 2",
        link="jst_current2",
        thumbnail_link="thumb_jst_current2",
        published=datetime(2025, 2, 11, 23, 30, 0, tzinfo=ZoneInfo("Asia/Tokyo")),
    )
    # UTCで未来の日時
    book_utc_future = MstBook(
        title="UTC Future Book",
        link="utc_future",
        thumbnail_link="thumb_utc_future",
        published=datetime(2025, 2, 12, 0, 30, 0, tzinfo=ZoneInfo("UTC")),
    )

    books = {
        "utc_past": book_utc_past,
        "jst_current": book_jst_current,
        "jst_current2": book_jst_current2,
        "utc_future": book_utc_future,
    }

    past, current, future = split_books(books, target_datetime)

    assert "utc_past" in past, "UTC Past Book は過去日として分類されるべきです。"
    assert "jst_current" in current, "JST Current Book は当日として分類されるべきです。"
    assert "jst_current2" in current, (
        "JST Current Book 2 は当日として分類されるべきです。"
    )
    assert "utc_future" in future, "UTC Future Book は未来日として分類されるべきです。"
