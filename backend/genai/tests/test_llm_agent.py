import pytest

from src.llm import agent


# --- ダミークラスの定義 ---
# 外部依存する LiteLLMModel のダミー実装
class DummyLiteLLMModel:
    def __init__(self, model_id, temperature, seed):
        self.model_id = model_id
        self.temperature = temperature
        self.seed = seed


# 外部依存する ToolCallingAgent のダミー実装
class DummyToolCallingAgent:
    def __init__(self, tools, model, prompt_templates, max_steps):
        self.tools = tools
        self.model = model
        self.prompt_templates = prompt_templates
        self.max_steps = max_steps

    def run(self, task: str, stream: bool) -> str:
        # 単純に引数 task を返すようにする（実際には LLM へ問い合わせを行うはず）
        return f"dummy response: {task}"


# --- テストコード ---


def test_call_agent(monkeypatch):
    """
    call_agent 関数が、エージェントの run メソッドを呼び出して正しく結果を返すか検証するテスト
    """
    # agent モジュール内の LiteLLMModel, ToolCallingAgent, INSTRUCTION_PROMPT をダミーに置き換える
    monkeypatch.setattr(agent, "LiteLLMModel", DummyLiteLLMModel)
    monkeypatch.setattr(agent, "ToolCallingAgent", DummyToolCallingAgent)
    monkeypatch.setattr(agent, "INSTRUCTION_PROMPT", "dummy prompt")

    # _get_agent でエージェントを生成
    dummy_agent = agent._get_agent()

    # テスト用の文字列を用意して call_agent を呼び出す
    test_text = "test message"
    result = agent.call_agent(dummy_agent, test_text)

    # DummyToolCallingAgent.run は f"dummy response: {task}" を返すので、
    # 期待される結果は "dummy response: test message" となる
    assert result == f"dummy response: {test_text}"


def test_get_agent(monkeypatch):
    """
    _get_agent 関数が、正しく ToolCallingAgent インスタンスを生成しているか検証するテスト
    """
    # LiteLLMModel, ToolCallingAgent, INSTRUCTION_PROMPT をダミーに置き換える
    monkeypatch.setattr(agent, "LiteLLMModel", DummyLiteLLMModel)
    monkeypatch.setattr(agent, "ToolCallingAgent", DummyToolCallingAgent)
    monkeypatch.setattr(agent, "INSTRUCTION_PROMPT", "dummy prompt")

    dummy_agent = agent._get_agent()

    # エージェントがダミーの ToolCallingAgent であることを確認
    assert isinstance(dummy_agent, DummyToolCallingAgent)
    # ツールリストは空で、max_steps が 5 になっていることを確認
    assert dummy_agent.tools == []
    assert dummy_agent.max_steps == 5
    # プロンプトテンプレートが正しくセットされていることを確認
    assert dummy_agent.prompt_templates == {"system_prompt": "dummy prompt"}
    # モデルの初期化が正しく行われ、モデル ID が "gemini-2.0-flash-001" であることを確認
    assert dummy_agent.model.model_id == "gemini-2.0-flash-001"


def test_extract_script_block_found():
    text = """
<html>
<head>
<script>
console.log('Hello World');
</script>
</head>
<body>
<p>Some text</p>
</body>
</html>
"""
    expected = "<script>\nconsole.log('Hello World');\n</script>"
    result = agent.extract_script_block(text)
    assert result is not None
    # 前後の余分な空白を除いて比較
    assert result.strip() == expected.strip()


def test_extract_script_block_not_found():
    text = "<html><body><p>No script here</p></body></html>"
    result = agent.extract_script_block(text)
    assert result is None


def test_extract_script_block_multiple():
    text = """
<script>
console.log('First');
</script>
<script>
console.log('Second');
</script>
"""
    # 最初の <script> ブロックのみが抽出されるはず
    expected = "<script>\nconsole.log('First');\n</script>"
    result = agent.extract_script_block(text)
    assert result is not None
    assert result.strip() == expected.strip()
