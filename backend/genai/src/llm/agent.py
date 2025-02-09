import os
import re

import litellm
import tenacity
import weave
from lmnr import Laminar as L  # type: ignore
from lmnr import observe  # type: ignore
from smolagents import LiteLLMModel, ToolCallingAgent  # type: ignore
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from src.llm.config import INSTRUCTION_PROMPT
from src.logger import logger

# 必要に応じて最小文字数（またはトークン数）の閾値を設定
MIN_RESPONSE_LENGTH = 100

# LLM settings
MODEL_ID = "gemini-2.0-flash-001"
# 微調整対象のパラメータ
INITIAL_TEMPERATURE = 0.08


# safety_settingsを設定
safety_settings = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
]


# 正規表現パターン
SCRIPT_PATTERN = re.compile(r"<script\b[^>]*>(.*?)</script>", re.DOTALL)

if os.getenv("CI") == "true":
    # CI 環境では weave と Laminar を初期化しない
    # LiteLLM のデバッグログを有効化
    # litellm._turn_on_debug()
    pass
else:
    weave.init(project_name=os.getenv("WEAVE_PROJECT_NAME", ""))
    L.initialize(project_api_key=os.getenv("LMNR_PROJECT_API_KEY"))


class TemperatureHolder:
    def __init__(self, temperature: float):
        self.temperature = temperature


temp_holder = TemperatureHolder(INITIAL_TEMPERATURE)


def adjust_temperature(retry_state: tenacity.RetryCallState) -> None:
    """リトライ前に微調整するコールバック"""
    temp_holder.temperature += 0.03
    logger.info(
        f"retry count: {retry_state.attempt_number}, updated temperature: {temp_holder.temperature}"
    )


@observe(name="call_agent_with_dataset")
@retry(
    retry=retry_if_exception_type(ValueError),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=240),
    before_sleep=adjust_temperature,
)
def call_agent_with_dataset(dataset: str) -> str:
    """あまりに短い応答が返ってきた場合は再試行する関数
    リトライ設定は、最大3回、指数バックオフで最大240秒まで待機する。
    """
    # use smolagents as llm agent
    # see: https://cloud.google.com/vertex-ai/generative-ai/docs/learn/models#gemini-models
    model = LiteLLMModel(
        MODEL_ID,
        temperature=temp_holder.temperature,
        config={"safety_settings": safety_settings},
    )
    my_agent = ToolCallingAgent(
        tools=[],
        model=model,
        prompt_templates={
            "system_prompt": INSTRUCTION_PROMPT,
        },
        max_steps=5,
    )

    text = "### dataset: \n" + dataset
    result = my_agent.run(task=text, stream=False)

    # thinkタグもscriptタグもない場合は再試行
    if isinstance(result, str) and "<think>" not in result and "<script>" not in result:
        raise ValueError("No <think> or <script> tag found in the response.")

    return result


def extract_script_block(text: str) -> str | None:
    """
    指定の文字列から最初に見つかった <script> タグブロック内の内容を抽出して返します。

    タグ自身 (<script> および </script>) は返り値に含みません。
    もし <script> ブロックが見つからなかった場合は None を返します。

    Args:
        text (str): 対象の文字列

    Returns:
        Optional[str]: 抽出した <script> ブロック内の内容、もしくは None
    """
    match = SCRIPT_PATTERN.search(text)
    if match:
        return match.group(1)
    return None


if __name__ == "__main__":
    #     agent = get_agent()
    #     dataset = """
    # None
    # """
    #     text = "dataset: " + dataset
    #     result = call_agent(agent, text)
    #     print(result)

    sample_text = "<script>hoge</script>"
    extracted_content = extract_script_block(sample_text)
    print(extracted_content)  # 出力: hoge
