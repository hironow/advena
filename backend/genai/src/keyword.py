from typing import Any


def _generate_canonical(tokens: list[str]) -> str:
    """
    トリム済みのトークンのリストから、順序に依存しない canonical 表現を生成する。
    canonical 表現は、各トークン（ケースセンシティブ）の Unicode 順にソートし、
    パイプ ("|") で連結した文字列です。

    例:
        ["AI", "LLM", "エンジニア"]  -> "AI|LLM|エンジニア"
        ["LLM", "AI", "エンジニア"]  -> "AI|LLM|エンジニア"

    Args:
        tokens (list[str]): 各フォームから入力されたトークン（すでにトリム済み）。

    Returns:
        str: canonical 表現。
    """
    sorted_tokens = sorted(tokens)
    return "|".join(sorted_tokens)


def parse_keywords(token_list: list[str]) -> dict[str, Any]:
    """
    フォームから受け取ったキーワード入力値のリストをパースして、以下の情報を返します:
      - keywordsExact: 各入力値の左右の空白をトリムした結果のリスト
      - canonical: トリム済みトークンをソートして "|" で連結した canonical 表現

    仕様:
      - 各フォームに入力された値は、前後の空白を除去して扱います。
      - 入力値そのものの中の内部の空白は変更しません。
      - canonical 表現は入力順序に依存せず、ソートした結果で生成します。

    Args:
        token_list (list[str]): 各フォームの入力値のリスト。

    Returns:
        dict[str, Any]: {
            "keywordsExact": トリム済みの入力値リスト,
            "canonical":  ソートして "|" で連結した canonical 表現
        }

    例:
        入力: ["  AI  ", "LLM", " エンジニア "]
        出力: {
          "keywordsExact": ["AI", "LLM", "エンジニア"],
          "canonical": "AI|LLM|エンジニア"
        }
    """
    trimmed_tokens = [token.strip() for token in token_list]
    canonical = _generate_canonical(trimmed_tokens)
    return {"keywordsExact": trimmed_tokens, "canonical": canonical}
