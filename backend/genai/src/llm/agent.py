import os
import re

import litellm
import weave
from lmnr import Laminar as L  # type: ignore
from lmnr import observe  # type: ignore
from smolagents import LiteLLMModel, ToolCallingAgent  # type: ignore

from src.llm.config import INSTRUCTION_PROMPT

# LLM settings
MODEL_ID = "gemini-2.0-flash-001"
# 微調整対象のパラメータ
TEMPERATURE = 0.08
SEED = 42

# 正規表現パターン
SCRIPT_PATTERN = re.compile(r"(<script>.*?</script>)", re.DOTALL)


if os.getenv("CI") == "true":
    # CI 環境では weave と Laminar を初期化しない
    # LiteLLM のデバッグログを有効化
    litellm._turn_on_debug()
else:
    weave.init(project_name=os.getenv("WEAVE_PROJECT_NAME", ""))
    L.initialize(project_api_key=os.getenv("LMNR_PROJECT_API_KEY"))


def get_agent() -> ToolCallingAgent:
    # use smolagents as llm agent
    # see: https://cloud.google.com/vertex-ai/generative-ai/docs/learn/models#gemini-models
    model = LiteLLMModel(
        MODEL_ID,
        temperature=TEMPERATURE,
        seed=SEED,
    )
    agent = ToolCallingAgent(
        tools=[],
        model=model,
        prompt_templates={
            "system_prompt": INSTRUCTION_PROMPT,
        },
        max_steps=5,
    )
    return agent


def call_agent(agent: ToolCallingAgent, text: str) -> str:
    return agent.run(task=text, stream=False)


def extract_script_block(text: str) -> str | None:
    """
    指定の文字列から最初に見つかった <script> タグブロックを抽出して返します。

    タグ自体 (<script> および </script>) も含めた文字列を返します。
    もし <script> ブロックが見つからなかった場合は None を返します。

    Args:
        text (str): 対象の文字列

    Returns:
        Optional[str]: 抽出した <script> ブロック、もしくは None
    """
    match = SCRIPT_PATTERN.search(text)
    if match:
        return match.group(1)
    return None


if __name__ == "__main__":
    agent = get_agent()
    dataset = """
None
"""
    text = "dataset: " + dataset
    result = call_agent(agent, text)
    print(result)
