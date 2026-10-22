from pathlib import Path

import pytest
from google import genai
from google.genai import types
from google.genai.models import Models
from smolagents import ToolCallingAgent
from smolagents.models import ChatMessage, MessageRole

from src.llm.gemini_model import GeminiModel


@pytest.fixture(autouse=True)
def isolated_provider_environment(monkeypatch):
    # Never select the developer's account or provider configuration.
    for key in (
        "GOOGLE_API_KEY",
        "GEMINI_API_KEY",
        "GOOGLE_GENAI_USE_VERTEXAI",
        "GOOGLE_GENAI_USE_ENTERPRISE",
        "GOOGLE_CLOUD_PROJECT",
        "GOOGLE_CLOUD_LOCATION",
        "GOOGLE_APPLICATION_CREDENTIALS",
    ):
        monkeypatch.delenv(key, raising=False)


@pytest.mark.parametrize("environment", [".env", ".env.dev", ".env.prd"])
def test_supplied_environments_select_adc(environment):
    # Inspect only the public selector, never include other env values in assertions.
    path = Path(__file__).resolve().parents[1] / environment
    selectors = [
        line.strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.startswith("GOOGLE_GENAI_USE_ENTERPRISE=")
    ]
    assert selectors == ["GOOGLE_GENAI_USE_ENTERPRISE=true"]


def test_generate_preserves_prompt_temperature_and_safety(monkeypatch):
    monkeypatch.setenv("GOOGLE_API_KEY", "test-key-not-a-credential")
    monkeypatch.delenv("GOOGLE_GENAI_USE_VERTEXAI", raising=False)
    captured = {}

    def generate_content(self, **kwargs):
        captured.update(kwargs)
        return types.GenerateContentResponse(
            candidates=[
                types.Candidate(
                    content=types.Content(
                        role="model", parts=[types.Part(text="<script>answer</script>")]
                    )
                )
            ]
        )

    monkeypatch.setattr(Models, "generate_content", generate_content)
    safety = [{"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"}]
    model = GeminiModel(
        "test-model", temperature=0.08, config={"safety_settings": safety}
    )
    result = model.generate(
        [
            ChatMessage(role=MessageRole.SYSTEM, content="system instructions"),
            ChatMessage(
                role=MessageRole.USER, content=[{"type": "text", "text": "dataset"}]
            ),
        ],
        stop_sequences=["STOP"],
    )

    assert captured["model"] == "test-model"
    assert captured["contents"] == [
        types.Content(role="user", parts=[types.Part(text="dataset")])
    ]
    config = captured["config"]
    assert config.system_instruction == "system instructions"
    assert config.temperature == 0.08
    assert config.stop_sequences == ["STOP"]
    assert config.safety_settings == [types.SafetySetting(**safety[0])]
    assert result.role == MessageRole.ASSISTANT
    assert result.content == "<script>answer</script>"


def test_real_agent_returns_native_final_answer(monkeypatch):
    monkeypatch.setenv("GOOGLE_API_KEY", "test-key-not-a-credential")
    monkeypatch.delenv("GOOGLE_GENAI_USE_VERTEXAI", raising=False)

    def generate_content(self, **kwargs):
        config = kwargs["config"]
        declaration = config.tools[0].function_declarations[0]
        assert declaration.name == "final_answer"
        schema = declaration.parameters_json_schema
        assert schema["properties"]["answer"]["type"] == "string"
        assert schema["required"] == ["answer"]
        assert config.tool_config.function_calling_config.mode == "ANY"
        assert config.automatic_function_calling.disable is True
        return types.GenerateContentResponse(
            candidates=[
                types.Candidate(
                    content=types.Content(
                        role="model",
                        parts=[
                            types.Part(
                                function_call=types.FunctionCall(
                                    name="final_answer",
                                    args={"answer": "<script>done</script>"},
                                )
                            )
                        ],
                    )
                )
            ]
        )

    monkeypatch.setattr(Models, "generate_content", generate_content)
    model = GeminiModel("test-model", temperature=0.08, config={})
    agent = ToolCallingAgent(tools=[], model=model, max_steps=2, verbosity_level=0)

    assert agent.run("dataset", stream=False) == "<script>done</script>"


def test_real_agent_recovers_from_invalid_tool_arguments(monkeypatch):
    monkeypatch.setenv("GOOGLE_API_KEY", "test-key-not-a-credential")
    monkeypatch.delenv("GOOGLE_GENAI_USE_VERTEXAI", raising=False)
    requests = []

    def generate_content(self, **kwargs):
        requests.append(kwargs)
        args = (
            {"wrong_parameter": "bad"}
            if len(requests) == 1
            else {"answer": "recovered"}
        )
        return types.GenerateContentResponse(
            candidates=[
                types.Candidate(
                    content=types.Content(
                        role="model",
                        parts=[
                            types.Part(
                                function_call=types.FunctionCall(
                                    name="final_answer", args=args
                                )
                            )
                        ],
                    )
                )
            ]
        )

    monkeypatch.setattr(Models, "generate_content", generate_content)
    agent = ToolCallingAgent(
        tools=[],
        model=GeminiModel("test-model", temperature=0.08, config={}),
        max_steps=3,
        verbosity_level=0,
    )

    assert agent.run("dataset", stream=False) == "recovered"
    assert len(requests) == 2
    assert all(content.role in ("user", "model") for content in requests[1]["contents"])
    assert any(
        "wrong_parameter" in (part.text or "")
        for content in requests[1]["contents"]
        for part in content.parts
    )


@pytest.mark.parametrize(
    "selector", ["GOOGLE_GENAI_USE_VERTEXAI", "GOOGLE_GENAI_USE_ENTERPRISE"]
)
@pytest.mark.parametrize("vertex", [False, True])
def test_real_sdk_selects_auth_from_isolated_environment(monkeypatch, vertex, selector):
    for key in (
        "GOOGLE_API_KEY",
        "GEMINI_API_KEY",
        "GOOGLE_GENAI_USE_VERTEXAI",
        "GOOGLE_CLOUD_PROJECT",
        "GOOGLE_CLOUD_LOCATION",
    ):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv(selector, "true" if vertex else "false")
    if vertex:
        monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", "test-project")
        monkeypatch.setenv("GOOGLE_CLOUD_LOCATION", "global")
    else:
        monkeypatch.setenv("GOOGLE_API_KEY", "test-key-not-a-credential")

    with genai.Client() as client:
        assert bool(client.vertexai) is vertex


def test_generate_reports_token_usage(monkeypatch):
    monkeypatch.setenv("GOOGLE_API_KEY", "test-key-not-a-credential")
    monkeypatch.delenv("GOOGLE_GENAI_USE_VERTEXAI", raising=False)

    def generate_content(self, **kwargs):
        return types.GenerateContentResponse(
            candidates=[
                types.Candidate(
                    content=types.Content(
                        role="model", parts=[types.Part(text="answer")]
                    )
                )
            ],
            usage_metadata=types.GenerateContentResponseUsageMetadata(
                prompt_token_count=7,
                candidates_token_count=3,
                thoughts_token_count=2,
            ),
        )

    monkeypatch.setattr(Models, "generate_content", generate_content)
    result = GeminiModel("test-model", temperature=0.08, config={}).generate(
        [ChatMessage(role=MessageRole.USER, content="dataset")]
    )

    assert result.token_usage.input_tokens == 7
    assert result.token_usage.output_tokens == 5


@pytest.mark.parametrize(
    "parts", [None, [], [types.Part(text="private reasoning", thought=True)]]
)
def test_empty_or_thought_only_response_fails_loudly(monkeypatch, parts):
    monkeypatch.setenv("GOOGLE_API_KEY", "test-key-not-a-credential")
    monkeypatch.delenv("GOOGLE_GENAI_USE_VERTEXAI", raising=False)

    def generate_content(self, **kwargs):
        return types.GenerateContentResponse(
            candidates=[]
            if parts is None
            else [types.Candidate(content=types.Content(role="model", parts=parts))]
        )

    monkeypatch.setattr(Models, "generate_content", generate_content)
    with pytest.raises(RuntimeError, match="Gemini returned no"):
        GeminiModel("test-model", temperature=0.08, config={}).generate(
            [ChatMessage(role=MessageRole.USER, content="dataset")]
        )


def test_sdk_client_is_closed_on_request_failure(monkeypatch):
    monkeypatch.setenv("GOOGLE_API_KEY", "test-key-not-a-credential")
    monkeypatch.delenv("GOOGLE_GENAI_USE_VERTEXAI", raising=False)
    closed = []
    original_close = genai.Client.close

    def close(self):
        closed.append(True)
        original_close(self)

    def generate_content(self, **kwargs):
        raise RuntimeError("provider unavailable")

    monkeypatch.setattr(genai.Client, "close", close)
    monkeypatch.setattr(Models, "generate_content", generate_content)
    with pytest.raises(RuntimeError, match="provider unavailable"):
        GeminiModel("test-model", temperature=0.08, config={}).generate(
            [ChatMessage(role=MessageRole.USER, content="dataset")]
        )
    # SDK finalizers may call close again; resource cleanup must still happen.
    assert closed


def test_consecutive_text_messages_are_preserved(monkeypatch):
    monkeypatch.setenv("GOOGLE_API_KEY", "test-key-not-a-credential")
    captured = []

    def generate_content(self, **kwargs):
        captured.extend(kwargs["contents"])
        return types.GenerateContentResponse(
            candidates=[
                types.Candidate(
                    content=types.Content(
                        role="model", parts=[types.Part(text="answer")]
                    )
                )
            ]
        )

    monkeypatch.setattr(Models, "generate_content", generate_content)
    GeminiModel("test-model", temperature=0.08, config={}).generate(
        [
            ChatMessage(role=MessageRole.USER, content="first"),
            ChatMessage(role=MessageRole.USER, content="second"),
        ]
    )
    assert captured == [
        types.Content(role="user", parts=[types.Part(text="first\nsecond")])
    ]


def test_multimodal_input_is_rejected_before_sdk_construction():
    with pytest.raises(ValueError, match="text-only"):
        GeminiModel("test-model", temperature=0.08, config={}).generate(
            [
                ChatMessage(
                    role=MessageRole.USER,
                    content=[{"type": "image", "image": object()}],
                )
            ]
        )


def test_unsupported_response_format_is_not_silently_ignored():
    with pytest.raises(ValueError, match="response_format"):
        GeminiModel("test-model", temperature=0.08, config={}).generate(
            [ChatMessage(role=MessageRole.USER, content="dataset")],
            response_format={"type": "unsupported"},
        )
