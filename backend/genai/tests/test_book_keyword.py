# tests/test_keyword.py

import pytest

from src.book.keyword import parse_keywords


@pytest.mark.parametrize(
    "token_list, expected",
    [
        (
            ["AI LLM", "エンジニア"],
            {
                "keywordsExact": ["AI LLM", "エンジニア"],
                "canonical": "AI LLM|エンジニア",
            },
        ),
        (
            ["AI LLM エンジニア"],
            {"keywordsExact": ["AI LLM エンジニア"], "canonical": "AI LLM エンジニア"},
        ),
        (
            ["AI", "エンジニア", "LLM"],
            {
                "keywordsExact": ["AI", "エンジニア", "LLM"],
                "canonical": "AI|LLM|エンジニア",
            },
        ),
        (
            ["LLM", "AI", "エンジニア"],
            {
                "keywordsExact": ["LLM", "AI", "エンジニア"],
                "canonical": "AI|LLM|エンジニア",
            },
        ),
        (
            ["AI", "ai", "Ai"],
            {"keywordsExact": ["AI", "ai", "Ai"], "canonical": "AI|Ai|ai"},
        ),
        (
            ["  AI  ", "LLM", " エンジニア "],
            {
                "keywordsExact": ["AI", "LLM", "エンジニア"],
                "canonical": "AI|LLM|エンジニア",
            },
        ),
    ],
)
def test_parse_keywords(token_list, expected):
    result = parse_keywords(token_list)
    assert result == expected
