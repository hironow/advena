import pytest

from src.keyword import generate_canonical, parse_keywords, tokenize_keywords


@pytest.mark.parametrize(
    "input_str, expected_tokens",
    [
        # "がない場合はスペースで区切る
        ("AI LLM エンジニア", ["AI", "LLM", "エンジニア"]),
        ('"AI" LLM エンジニア', ["AI", "LLM", "エンジニア"]),
        # "で囲むと完全一致扱い
        ('"AI LLM エンジニア"', ["AI LLM エンジニア"]),
        # ダブルクオートで囲まれた単語の場合は、クオートを外して通常のトークンにする
        ('"AI" "LLM" エンジニア', ["AI", "LLM", "エンジニア"]),
        # 複数語が囲まれている場合はそのまま1トークンとして扱う
        ('"AI LLM" エンジニア', ["AI LLM", "エンジニア"]),
        # 余計な空白が入っている場合のテスト
        ('  "AI"   LLM   エンジニア  ', ["AI", "LLM", "エンジニア"]),
        # シングルクオートのみは特別扱いしないので、そのままトークンに含まれる
        ("'AI' LLM エンジニア", ["'AI'", "LLM", "エンジニア"]),
        # アポストロフィを含む単語もそのまま扱う
        ("AI LLM own's エンジニア", ["AI", "LLM", "own's", "エンジニア"]),
        # ダブルクオートによるグルーピングは有効。シングルクオートはそのまま
        ("\"own's\" LLM owns' エンジニア", ["own's", "LLM", "owns'", "エンジニア"]),
        # ダブルクオートとシングルクオートが混在するケース
        ("\"AI\" 'LLM' エンジニア", ["AI", "'LLM'", "エンジニア"]),
        # ケースセンシティブのテスト: 大文字小文字がそのまま残る
        ("AI ai Ai", ["AI", "ai", "Ai"]),
    ],
)
def test_tokenize_keywords(input_str, expected_tokens):
    tokens = tokenize_keywords(input_str)
    assert tokens == expected_tokens


@pytest.mark.parametrize(
    "tokens, expected_canonical",
    [
        (["AI", "LLM", "エンジニア"], "AI|LLM|エンジニア"),
        (["LLM", "AI", "エンジニア"], "AI|LLM|エンジニア"),
        (["LLM", "エンジニア", "AI"], "AI|LLM|エンジニア"),
        (["エンジニア", "AI", "LLM"], "AI|LLM|エンジニア"),
        # シングルクオート
        (["'AI'", "LLM", "エンジニア"], "'AI'|LLM|エンジニア"),
        (["own's", "owns'", "AI"], "AI|own's|owns'"),
        # ケースセンシティブのテスト: "AI", "ai", "Ai" の順序は Unicode コードポイント順となる
        (["AI", "ai", "Ai"], "AI|Ai|ai"),
    ],
)
def test_generate_canonical(tokens, expected_canonical):
    canonical = generate_canonical(tokens)
    assert canonical == expected_canonical


@pytest.mark.parametrize(
    "raw_keywords, expected",
    [
        (
            '"AI" LLM エンジニア',
            {
                "rawKeywords": '"AI" LLM エンジニア',
                "keywordsExact": ["AI", "LLM", "エンジニア"],
                "canonical": "AI|LLM|エンジニア",
            },
        ),
        (
            "AI LLM エンジニア",
            {
                "rawKeywords": "AI LLM エンジニア",
                "keywordsExact": ["AI", "LLM", "エンジニア"],
                "canonical": "AI|LLM|エンジニア",
            },
        ),
        (
            '"AI LLM エンジニア"',
            {
                "rawKeywords": '"AI LLM エンジニア"',
                "keywordsExact": ["AI LLM エンジニア"],
                "canonical": "AI LLM エンジニア",
            },
        ),
        (
            '"AI LLM" エンジニア',
            {
                "rawKeywords": '"AI LLM" エンジニア',
                "keywordsExact": ["AI LLM", "エンジニア"],
                "canonical": "AI LLM|エンジニア",
            },
        ),
        (
            '  "AI"   LLM   エンジニア  ',
            {
                "rawKeywords": '  "AI"   LLM   エンジニア  ',
                "keywordsExact": ["AI", "LLM", "エンジニア"],
                "canonical": "AI|LLM|エンジニア",
            },
        ),
    ],
)
def test_parse_keywords(raw_keywords, expected):
    result = parse_keywords(raw_keywords)
    assert result == expected
