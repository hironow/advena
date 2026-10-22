"""Text-only smolagents adapter using Google's SDK directly."""

from typing import Any
from uuid import uuid4

from google import genai
from google.genai import types
from smolagents import Tool
from smolagents.models import (
    ChatMessage,
    ChatMessageToolCall,
    ChatMessageToolCallFunction,
    MessageRole,
    Model,
    get_clean_message_list,
    get_tool_json_schema,
    tool_role_conversions,
)
from smolagents.monitoring import TokenUsage


class GeminiModel(Model):
    def __init__(
        self,
        model_id: str,
        temperature: float,
        config: dict[str, Any],
    ) -> None:
        super().__init__(model_id=model_id)
        self.temperature = temperature
        self.safety_settings = config.get("safety_settings", [])

    def generate(
        self,
        messages: list[ChatMessage | dict[str, Any]],
        stop_sequences: list[str] | None = None,
        response_format: dict[str, str] | None = None,
        tools_to_call_from: list[Tool] | None = None,
        **kwargs: Any,
    ) -> ChatMessage:
        if response_format is not None:
            raise ValueError(
                "GeminiModel does not support response_format; use tool schemas"
            )
        unknown = set(kwargs) - {"tool_choice"}
        if unknown:
            raise TypeError(f"Unsupported generation options: {sorted(unknown)}")
        tool_choice = kwargs.get("tool_choice", "required")
        modes = {"required": "ANY", "auto": "AUTO", "none": "NONE"}
        if not isinstance(tool_choice, str) or tool_choice not in modes:
            raise ValueError(f"Unsupported tool_choice: {tool_choice}")
        normalized = []
        for message in messages:
            role = message["role"] if isinstance(message, dict) else message.role
            content = (
                message.get("content") if isinstance(message, dict) else message.content
            )
            if isinstance(content, str):
                content = [{"type": "text", "text": content}]
            if not isinstance(content, list) or any(
                not isinstance(part, dict) or part.get("type") != "text"
                for part in content
            ):
                raise ValueError("GeminiModel supports text-only messages")
            normalized.append({"role": role, "content": content})
        cleaned = get_clean_message_list(
            normalized, role_conversions=tool_role_conversions
        )
        contents = []
        instructions = []
        for message in cleaned:
            content = message["content"]
            if isinstance(content, str):
                text = content
            else:
                if any(part.get("type") != "text" for part in content):
                    raise ValueError("GeminiModel supports text-only messages")
                text = "\n".join(part["text"] for part in content)
            role = message["role"]
            if role == "system":
                instructions.append(text)
            elif role in ("user", "assistant"):
                contents.append(
                    types.Content(
                        role="model" if role == "assistant" else "user",
                        parts=[types.Part(text=text)],
                    )
                )
            else:
                raise ValueError(f"Unsupported message role: {role}")
        config = types.GenerateContentConfig(
            temperature=self.temperature,
            safety_settings=self.safety_settings,
            stop_sequences=stop_sequences,
            system_instruction="\n".join(instructions) if instructions else None,
            automatic_function_calling=types.AutomaticFunctionCallingConfig(
                disable=True
            ),
        )
        if tools_to_call_from:
            declarations = []
            for tool in tools_to_call_from:
                schema = get_tool_json_schema(tool)["function"]
                declarations.append(
                    types.FunctionDeclaration(
                        name=schema["name"],
                        description=schema.get("description"),
                        parameters_json_schema=schema["parameters"],
                    )
                )
            config.tools = [types.Tool(function_declarations=declarations)]
            config.tool_config = types.ToolConfig(
                function_calling_config=types.FunctionCallingConfig(
                    mode=modes[tool_choice]
                )
            )
        with genai.Client() as client:
            response = client.models.generate_content(
                model=self.model_id, contents=contents, config=config
            )
        if not response.candidates or not response.candidates[0].content:
            raise RuntimeError(
                "Gemini returned no candidate content (possibly blocked)"
            )
        parts = response.candidates[0].content.parts or []
        text = "".join(part.text for part in parts if part.text and not part.thought)
        calls = [
            ChatMessageToolCall(
                id=part.function_call.id or uuid4().hex,
                type="function",
                function=ChatMessageToolCallFunction(
                    name=part.function_call.name,
                    arguments=part.function_call.args or {},
                ),
            )
            for part in parts
            if part.function_call is not None
        ]
        if not text and not calls:
            raise RuntimeError("Gemini returned no text or function calls")
        usage = response.usage_metadata
        return ChatMessage(
            role=MessageRole.ASSISTANT,
            content=text or None,
            tool_calls=calls or None,
            raw=response,
            token_usage=TokenUsage(
                input_tokens=usage.prompt_token_count or 0,
                output_tokens=(usage.candidates_token_count or 0)
                + (usage.thoughts_token_count or 0),
            )
            if usage
            else None,
        )
