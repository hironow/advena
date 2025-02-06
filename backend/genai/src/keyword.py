import re
from typing import Any


def tokenize_keywords(raw_keywords: str) -> list[str]:
    """
    ユーザー入力のキーワード文字列をトークンに分割します。

    ルール:
    - ダブルクオート (") で囲まれた部分は 1 つのトークンとして扱います。
    - クオート外の部分は半角空白で分割します。
    - 各トークンの前後の余分な空白は除去します。

    Args:
        raw_keywords (str): ユーザーが入力したキーワード文字列。

    Returns:
        list[str]: トークンのリスト。

    Examples:
        >>> tokenize_keywords('"AI LLM エンジニア"')
        ['AI LLM エンジニア']

        >>> tokenize_keywords('AI LLM エンジニア')
        ['AI', 'LLM', 'エンジニア']

        >>> tokenize_keywords('"AI" LLM エンジニア')
        ['AI', 'LLM', 'エンジニア']
    """
    # ダブルクオートで囲まれた部分を抽出するパターン
    pattern = r'"([^"]+)"'
    quoted_tokens = re.findall(pattern, raw_keywords)
    # 抽出済みの部分は削除して、残りを空白で分割
    raw_without_quotes = re.sub(pattern, "", raw_keywords)
    unquoted_tokens = raw_without_quotes.split()

    # quoted_tokens と unquoted_tokens を結合
    tokens = quoted_tokens + unquoted_tokens
    # 空文字や余計な空白を除去
    tokens = [token.strip() for token in tokens if token.strip()]

    return tokens


def generate_canonical(tokens: list[str]) -> str:
    """
    トークンのリストから canonical 表現を生成します。

    canonical 表現は、ケースセンシティブのまま各トークンを一貫した（例: Unicodeコードポイント順）
    順序でソートし、区切り文字（ここでは "|"）で連結した文字列です。これにより、入力順序に依存しない比較が可能になります。

    Args:
        tokens (list[str]): トークンのリスト。

    Returns:
        str: canonical 表現。

    Examples:
        >>> generate_canonical(["AI", "LLM", "エンジニア"])
        'AI|LLM|エンジニア'

        >>> generate_canonical(["LLM", "AI", "エンジニア"])
        'AI|LLM|エンジニア'
    """
    sorted_tokens = sorted(tokens)
    return "|".join(sorted_tokens)


def parse_keywords(raw_keywords: str) -> dict[str, Any]:
    """
    ユーザー入力のキーワード文字列をパースし、以下の情報を含む辞書を返します。

      - rawKeywords: ユーザーが入力した元の文字列
      - keywordsExact: クオートの有無を反映したトークンのリスト
      - canonical: トークンの集合としての canonical 表現（順序に依存しない）

    例:
        >>> parse_keywords('"AI" LLM エンジニア')
        {
            "rawKeywords": '"AI" LLM エンジニア',
            "keywordsExact": ["AI", "LLM", "エンジニア"],
            "canonical": "AI|LLM|エンジニア"
        }

    Args:
        raw_keywords (str): ユーザー入力のキーワード文字列。

    Returns:
        dict[str, Any]: パース結果を含む辞書。
    """
    tokens = tokenize_keywords(raw_keywords)
    canonical = generate_canonical(tokens)
    return {
        "rawKeywords": raw_keywords,
        "keywordsExact": tokens,
        "canonical": canonical,
    }
