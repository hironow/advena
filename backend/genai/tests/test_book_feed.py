from datetime import datetime

import httpx
import pytest

from src.book.feed import (
    _fetch_rss,
    _generate_filename_from_date,
    _parse_rss_from_file,
    fetch_and_cache_rss,
    parse_rss,
)

# テストで利用するダミーの Atom 形式の RSS フィード XML
dummy_atom_xml = """<?xml version="1.0" encoding="utf-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <title>Dummy Feed</title>
  <updated>2025-02-08T15:45:00Z</updated>
  <entry>
    <title>Test Entry</title>
    <id>urn:uuid:60a76c80-d399-11d9-b93C-0003939e0af6</id>
    <updated>2025-02-08T15:45:00Z</updated>
    <summary>Test Summary</summary>
  </entry>
</feed>
"""


# httpx.get の呼び出しを差し替えるためのダミーのレスポンスクラス
class DummyResponse:
    def __init__(self, text: str):
        self.text = text

    def raise_for_status(self):
        pass


# ダミーの httpx.get 関数
def dummy_get(url: str, **kwargs):
    return DummyResponse(dummy_atom_xml)


def test_generate_filename_from_date():
    dt = datetime(2025, 2, 8, 15, 45, 0)
    filename = _generate_filename_from_date(dt)
    # 生成されるファイル名は "YYYYMMDD_HHMMSS.xml" 形式
    assert filename == "20250208_154500.xml"


def test_parse_rss():
    # parse_rss は生の XML を渡すので、dummy_atom_xml を利用
    feed, last_build_date = parse_rss(dummy_atom_xml)
    # Atom フィードの場合、feedparser は feed.title に値をセットします
    assert feed.feed.title == "Dummy Feed"
    expected_dt = datetime(2025, 2, 8, 15, 45, 0)
    assert last_build_date == expected_dt


def test_fetch_rss(monkeypatch):
    # httpx.get をダミーの関数に差し替え
    monkeypatch.setattr(httpx, "get", dummy_get)
    result = _fetch_rss("http://example.com/feed")
    # fetch_rss は取得した生 XML をそのまま返すので、dummy_atom_xml と一致するはずです
    assert result == dummy_atom_xml


def test_fetch_and_cache_rss(monkeypatch, tmp_path):
    # テスト時のカレントディレクトリを一時ディレクトリに変更
    monkeypatch.chdir(tmp_path)
    # httpx.get をダミーの関数に差し替え
    monkeypatch.setattr(httpx, "get", dummy_get)

    fetch_and_cache_rss("http://example.com/feed")

    # ダミーの RSS から抽出される更新日時により、ファイル名は以下となるはずです
    expected_filename = "20250208_154500.xml"
    file_path = tmp_path / expected_filename
    assert file_path.exists()

    # 保存された内容がダミーの XML と一致するか検証
    content = file_path.read_text(encoding="utf-8")
    assert content == dummy_atom_xml


def test_parse_rss_from_file(tmp_path):
    # 一時ファイルにダミーの XML を書き込み、parse_rss_from_file でパースできるか検証
    file = tmp_path / "dummy.xml"
    file.write_text(dummy_atom_xml, encoding="utf-8")

    feed = _parse_rss_from_file(str(file))
    assert feed.feed.title == "Dummy Feed"
