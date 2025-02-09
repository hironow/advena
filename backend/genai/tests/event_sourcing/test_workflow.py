from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from src.event_sourcing.workflows import MstBook, convert_to_book_prompt, split_books


def test_split_books_classification():
    """
    各書籍が target_datetime に対して、過去日、当日、未来日それぞれに分類されるかテストする。
    ※ target_datetime は JST で与える（例：ZoneInfo("Asia/Tokyo")）
    ※ MstBook.published は UTC で与える
    """
    # 基準日時：2025-02-11 12:00:00 JST
    target_datetime = datetime(2025, 2, 11, 12, 0, 0, tzinfo=ZoneInfo("Asia/Tokyo"))

    books = {
        "book_past": MstBook(
            title="Past Book",
            summary="summary1",
            isbn="isbn1",
            jp_e_code="jp_e_code1",
            link="link1",
            thumbnail_link="thumb1",
            published=datetime(
                2025, 2, 10, 10, 0, 0, tzinfo=ZoneInfo("UTC")
            ),  # JST: 19:00 (2/10)
        ),
        "book_current": MstBook(
            title="Current Book",
            summary="summary1",
            isbn="isbn1",
            jp_e_code="jp_e_code1",
            link="link2",
            thumbnail_link="thumb2",
            # 2025-02-11 03:00 UTC → JST: 12:00 (2/11)
            published=datetime(2025, 2, 11, 3, 0, 0, tzinfo=ZoneInfo("UTC")),
        ),
        "book_future": MstBook(
            title="Future Book",
            summary="summary1",
            isbn="isbn1",
            jp_e_code="jp_e_code1",
            link="link3",
            thumbnail_link="thumb3",
            # 2025-02-12 01:00 UTC → JST: 10:00 (2/12)
            published=datetime(2025, 2, 12, 1, 0, 0, tzinfo=ZoneInfo("UTC")),
        ),
    }

    past, current, future = split_books(books, target_datetime)

    assert "book_past" in past, "過去日と判定されるべき書籍が past に含まれていません。"
    assert "book_current" in current, (
        "当日と判定されるべき書籍が current に含まれていません。"
    )
    assert "book_future" in future, (
        "未来日と判定される書籍が future に含まれていません。"
    )


def test_split_books_skip_none():
    """
    published に None が設定されている場合、その項目がスキップされることをテストする。
    """
    target_datetime = datetime(2025, 2, 11, 12, 0, 0, tzinfo=ZoneInfo("Asia/Tokyo"))

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
        summary="summary1",
        isbn="isbn1",
        jp_e_code="jp_e_code1",
        link="link_valid",
        thumbnail_link="thumb_valid",
        # 2025-02-11 03:00 UTC → JST: 12:00 (2/11)
        published=datetime(2025, 2, 11, 3, 0, 0, tzinfo=ZoneInfo("UTC")),
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
    MstBook.published は UTC で、target_datetime は JST で与える場合に、
    日付の比較が正しく行われるかテストする。

    例：
      - 2025-02-11 00:00:00 UTC は JST では 2025-02-11 09:00:00 となり、日付は 2025-02-11
      - 2025-02-11 14:30:00 UTC は JST では 2025-02-11 23:30:00 となる
    """
    # target_datetime: 2025-02-11 09:00:00 JST
    target_datetime = datetime(2025, 2, 11, 9, 0, 0, tzinfo=ZoneInfo("Asia/Tokyo"))

    # 過去に分類させるには、published を JST で 2025-02-10 23:00 以前になるように設定
    # 例: 2025-02-10 14:00:00 UTC → JST: 2025-02-10 23:00:00
    book_utc_past = MstBook(
        title="UTC Past Book",
        summary="summary1",
        isbn="isbn1",
        jp_e_code="jp_e_code1",
        link="utc_past",
        thumbnail_link="thumb_utc_past",
        published=datetime(2025, 2, 10, 14, 0, 0, tzinfo=ZoneInfo("UTC")),
    )
    # 当日と分類する例：
    # 2025-02-11 00:00:00 UTC → JST: 2025-02-11 09:00:00
    book_utc_current = MstBook(
        title="UTC Current Book",
        summary="summary1",
        isbn="isbn1",
        jp_e_code="jp_e_code1",
        link="utc_current",
        thumbnail_link="thumb_utc_current",
        published=datetime(2025, 2, 11, 0, 0, 0, tzinfo=ZoneInfo("UTC")),
    )
    # 2025-02-11 14:30:00 UTC → JST: 2025-02-11 23:30:00
    book_utc_current2 = MstBook(
        title="UTC Current Book 2",
        summary="summary1",
        isbn="isbn1",
        jp_e_code="jp_e_code1",
        link="utc_current2",
        thumbnail_link="thumb_utc_current2",
        published=datetime(2025, 2, 11, 14, 30, 0, tzinfo=ZoneInfo("UTC")),
    )
    # 2025-02-12 00:30:00 UTC → JST: 2025-02-12 09:30:00
    book_utc_future = MstBook(
        title="UTC Future Book",
        summary="summary1",
        isbn="isbn1",
        jp_e_code="jp_e_code1",
        link="utc_future",
        thumbnail_link="thumb_utc_future",
        published=datetime(2025, 2, 12, 0, 30, 0, tzinfo=ZoneInfo("UTC")),
    )

    books = {
        "utc_past": book_utc_past,
        "utc_current": book_utc_current,
        "utc_current2": book_utc_current2,
        "utc_future": book_utc_future,
    }

    past, current, future = split_books(books, target_datetime)

    assert "utc_past" in past, "UTC Past Book は過去日として分類されるべきです。"
    assert "utc_current" in current, "UTC Current Book は当日として分類されるべきです。"
    assert "utc_current2" in current, (
        "UTC Current Book 2 は当日として分類されるべきです。"
    )
    assert "utc_future" in future, "UTC Future Book は未来日として分類されるべきです。"


def test_split_books_target_timezone_error():
    """
    target_datetime が JST 以外の場合、エラーが発生することをテストする。
    """
    # target_datetime を UTC として指定（JST ではない）
    target_datetime = datetime(2025, 2, 11, 12, 0, 0, tzinfo=ZoneInfo("UTC"))
    books = {}
    with pytest.raises(ValueError, match="target_datetime must be in JST timezone"):
        split_books(books, target_datetime)


def test_no_metadata():
    book = MstBook(
        title="Test Book",
        summary="A book for testing.",
        isbn="1234567890",
        jp_e_code="jp_test",
        link="http://example.com",
        thumbnail_link="http://example.com/thumbnail",
        published=datetime(2020, 1, 1, 12, 0, 0),
        metadata={},
    )
    expected = "title:Test Book\nsummary:A book for testing.\nmetadata:\n"
    result = convert_to_book_prompt(book)
    assert result == expected


def test_metadata_string():
    book = MstBook(
        title="String Test",
        summary="Testing string metadata",
        isbn="111",
        jp_e_code="code",
        link="http://example.com",
        thumbnail_link="http://example.com/thumbnail",
        published=datetime(2020, 1, 1, 0, 0, 0),
        metadata={"author": "John Doe"},
    )
    expected = "title:String Test\nsummary:Testing string metadata\nmetadata:\n* author: John Doe\n"
    result = convert_to_book_prompt(book)
    assert result == expected


def test_metadata_string_empty():
    book = MstBook(
        title="Empty String Test",
        summary="Testing empty string metadata",
        isbn="222",
        jp_e_code="code",
        link="http://example.com",
        thumbnail_link="http://example.com/thumbnail",
        published=datetime(2020, 1, 1, 0, 0, 0),
        metadata={"author": ""},
    )
    expected = (
        "title:Empty String Test\nsummary:Testing empty string metadata\nmetadata:\n"
    )
    result = convert_to_book_prompt(book)
    assert result == expected


def test_metadata_list():
    book = MstBook(
        title="List Test",
        summary="Testing list metadata",
        isbn="333",
        jp_e_code="code",
        link="http://example.com",
        thumbnail_link="http://example.com/thumbnail",
        published=datetime(2020, 1, 1, 0, 0, 0),
        metadata={"tags": ["fiction", "novel"]},
    )
    expected = "title:List Test\nsummary:Testing list metadata\nmetadata:\n* tags: fiction, novel\n"
    result = convert_to_book_prompt(book)
    assert result == expected


def test_metadata_list_empty():
    book = MstBook(
        title="Empty List Test",
        summary="Testing empty list metadata",
        isbn="444",
        jp_e_code="code",
        link="http://example.com",
        thumbnail_link="http://example.com/thumbnail",
        published=datetime(2020, 1, 1, 0, 0, 0),
        metadata={"tags": []},
    )
    expected = "title:Empty List Test\nsummary:Testing empty list metadata\nmetadata:\n"
    result = convert_to_book_prompt(book)
    assert result == expected


def test_metadata_list_all_none():
    book = MstBook(
        title="List All None",
        summary="Testing list with all None values",
        isbn="555",
        jp_e_code="code",
        link="http://example.com",
        thumbnail_link="http://example.com/thumbnail",
        published=datetime(2020, 1, 1, 0, 0, 0),
        metadata={"tags": [None, None]},
    )
    expected = (
        "title:List All None\nsummary:Testing list with all None values\nmetadata:\n"
    )
    result = convert_to_book_prompt(book)
    assert result == expected


def test_metadata_dict():
    book = MstBook(
        title="Dict Test",
        summary="Testing dict metadata",
        isbn="666",
        jp_e_code="code",
        link="http://example.com",
        thumbnail_link="http://example.com/thumbnail",
        published=datetime(2020, 1, 1, 0, 0, 0),
        metadata={"info": {"pages": 300, "publisher": "XYZ"}},
    )
    # dict の出力は {k:v} の順序が定義された順序で出力されるため、ここではリテラルで定義した順序を前提としています。
    expected = "title:Dict Test\nsummary:Testing dict metadata\nmetadata:\n* info: pages:300,publisher:XYZ\n"
    result = convert_to_book_prompt(book)
    assert result == expected


def test_metadata_dict_empty():
    book = MstBook(
        title="Empty Dict Test",
        summary="Testing empty dict metadata",
        isbn="777",
        jp_e_code="code",
        link="http://example.com",
        thumbnail_link="http://example.com/thumbnail",
        published=datetime(2020, 1, 1, 0, 0, 0),
        metadata={"info": {}},
    )
    expected = "title:Empty Dict Test\nsummary:Testing empty dict metadata\nmetadata:\n"
    result = convert_to_book_prompt(book)
    assert result == expected


def test_skipped_keys():
    book = MstBook(
        title="Skipped Keys Test",
        summary="Testing skipped keys in metadata",
        isbn="888",
        jp_e_code="code",
        link="http://example.com",
        thumbnail_link="http://example.com/thumbnail",
        published=datetime(2020, 1, 1, 0, 0, 0),
        metadata={
            "bibRecordCategory": "Some Category",
            "publicationPlace": "Tokyo",
            "genre": "Science Fiction",
        },
    )
    # "bibRecordCategory" と "publicationPlace" はスキップされ、"genre" のみ出力される
    expected = "title:Skipped Keys Test\nsummary:Testing skipped keys in metadata\nmetadata:\n* genre: Science Fiction\n"
    result = convert_to_book_prompt(book)
    assert result == expected


def test_multiple_metadata_keys_sorted():
    book = MstBook(
        title="Multiple Metadata Test",
        summary="Testing multiple metadata keys sorted",
        isbn="999",
        jp_e_code="code",
        link="http://example.com",
        thumbnail_link="http://example.com/thumbnail",
        published=datetime(2020, 1, 1, 0, 0, 0),
        metadata={
            "year": "2020",
            "author": "Alice",
            "tags": ["Fiction", "Drama"],
        },
    )
    # キーは "author", "tags", "year" の順にソートされる
    expected = (
        "title:Multiple Metadata Test\n"
        "summary:Testing multiple metadata keys sorted\n"
        "metadata:\n"
        "* author: Alice\n"
        "* tags: Fiction, Drama\n"
        "* year: 2020\n"
    )
    result = convert_to_book_prompt(book)
    assert result == expected


def test_metadata_with_none_value():
    book = MstBook(
        title="None Value Test",
        summary="Testing metadata with None value",
        isbn="1010",
        jp_e_code="code",
        link="http://example.com",
        thumbnail_link="http://example.com/thumbnail",
        published=datetime(2020, 1, 1, 0, 0, 0),
        metadata={"rating": None, "review": "Good book"},
    )
    # "rating" は None なのでスキップされ、"review" のみ出力される
    expected = "title:None Value Test\nsummary:Testing metadata with None value\nmetadata:\n* review: Good book\n"
    result = convert_to_book_prompt(book)
    assert result == expected


def test_metadata_unsupported_type(caplog):
    book = MstBook(
        title="Unsupported Type Test",
        summary="Testing unsupported metadata type",
        isbn="1111",
        jp_e_code="code",
        link="http://example.com",
        thumbnail_link="http://example.com/thumbnail",
        published=datetime(2020, 1, 1, 0, 0, 0),
        metadata={"pages": 300},  # int 型は対応外
    )
    expected = "title:Unsupported Type Test\nsummary:Testing unsupported metadata type\nmetadata:\n"
    result = convert_to_book_prompt(book)
    assert result == expected
    # ログに「metadata に未対応の型が含まれています: 300」が記録されていることを確認
    assert any(
        "metadata に未対応の型が含まれています: 300" in record.message
        for record in caplog.records
    )
