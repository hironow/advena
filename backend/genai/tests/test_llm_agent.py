import pytest

from src.llm import agent


# 外部依存する LiteLLMModel のダミー実装
class DummyLiteLLMModel:
    def __init__(self, model_id, temperature, config):
        self.model_id = model_id
        self.temperature = temperature
        self.config = config


# 外部依存する ToolCallingAgent のダミー実装
class DummyToolCallingAgent:
    def __init__(self, tools, model, prompt_templates, max_steps):
        self.tools = tools
        self.model = model
        self.prompt_templates = prompt_templates
        self.max_steps = max_steps

    def run(self, task: str, stream: bool) -> str:
        # 常に <think> タグを含む文字列を返すことでテスト通過させる
        return "<think>dummy response</think>"


def test_call_agent(monkeypatch):
    """
    call_agent 関数が、エージェントの run メソッドを呼び出して正しく結果を返すか検証するテスト
    """
    # agent モジュール内の LiteLLMModel, ToolCallingAgent, INSTRUCTION_PROMPT をダミーに置き換える
    monkeypatch.setattr(agent, "LiteLLMModel", DummyLiteLLMModel)
    monkeypatch.setattr(agent, "ToolCallingAgent", DummyToolCallingAgent)
    monkeypatch.setattr(agent, "INSTRUCTION_PROMPT", "dummy prompt")

    # テスト用の文字列を用意して call_agent を呼び出す
    test_text = "test message"
    result = agent.call_agent_with_dataset(test_text)

    # DummyToolCallingAgent.runと同じ
    assert result == "<think>dummy response</think>"


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
    expected = "\nconsole.log('Hello World');\n"
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
    # 最初の <script> ブロックの中身が抽出されるはず
    expected = "\nconsole.log('First');\n"
    result = agent.extract_script_block(text)
    assert result is not None
    assert result.strip() == expected.strip()
