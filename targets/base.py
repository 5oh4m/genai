"""
Abstract base class for all PayShield target agents.
Handles Gemini client initialization, tool registration, and conversation management.
"""

import os
import json
import logging
from abc import ABC, abstractmethod
from typing import Any, Optional
from dataclasses import dataclass, field

from openai import AsyncOpenAI
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)


@dataclass
class ToolCall:
    """Record of a tool invocation by the target agent."""
    tool_name: str
    arguments: dict
    result: dict


@dataclass
class ConversationTurn:
    """A single turn in the conversation."""
    role: str  # "user" | "assistant" | "system" | "tool"
    content: str
    tool_calls: list[ToolCall] = field(default_factory=list)

    def to_dict(self) -> dict:
        d = {"role": self.role, "content": self.content}
        if self.tool_calls:
            d["tool_calls"] = [
                {"tool": tc.tool_name, "args": tc.arguments, "result": tc.result}
                for tc in self.tool_calls
            ]
        return d


class BaseTarget(ABC):
    """
    Abstract base for LLM-backed PayShield target services.
    Each target has a system prompt, registered tools, and conversation state.
    """

    def __init__(self):
        api_key = os.getenv("OPENROUTER_API_KEY", "")
        if not api_key:
            raise EnvironmentError(
                "OPENROUTER_API_KEY not set. Copy .env.example to .env and add your key.\n"
                "Get one at https://openrouter.ai/keys"
            )

        self.client = AsyncOpenAI(base_url="https://openrouter.ai/api/v1", api_key=api_key)
        self.model_name = os.getenv("OPENROUTER_MODEL", "stealth/ox-alpha")
        self.conversation_history: list[ConversationTurn] = []
        self.tool_calls_log: list[ToolCall] = []

        # Subclasses must define these
        self._system_prompt: str = ""
        self._tools: dict[str, callable] = {}
        self._tool_descriptions: list[dict] = []

    @property
    @abstractmethod
    def name(self) -> str:
        """Short identifier for this target (e.g., 'support_chatbot')."""
        ...

    @property
    @abstractmethod
    def display_name(self) -> str:
        """Human-readable name (e.g., 'PayShield Customer Support')."""
        ...

    @abstractmethod
    def _setup(self) -> None:
        """Subclass hook to set system prompt, register tools, etc."""
        ...

    def register_tool(self, name: str, func: callable, description: str, parameters: dict) -> None:
        """Register a callable tool the target agent can invoke."""
        self._tools[name] = func
        self._tool_descriptions.append({
            "name": name,
            "description": description,
            "parameters": parameters,
        })

    def reset_conversation(self) -> None:
        """Clear conversation history for a fresh session."""
        self.conversation_history = []
        self.tool_calls_log = []

    def get_last_action(self) -> str:
        """Return the most recent tool call name, or 'none' if no tools were called."""
        if self.tool_calls_log:
            return self.tool_calls_log[-1].tool_name
        return "none"

    def get_transcript(self) -> list[dict]:
        """Return the full conversation as a list of dicts."""
        return [turn.to_dict() for turn in self.conversation_history]

    async def process_message(self, user_message: str) -> str:
        """
        Process an incoming user message:
        1. Add to conversation history
        2. Call Gemini with system prompt + history
        3. If the model wants to call a tool, execute it and feed result back
        4. Return the final assistant response

        Returns:
            The assistant's text response.
        """
        self.conversation_history.append(
            ConversationTurn(role="user", content=user_message)
        )

        # Build the messages for the OpenAI call
        contents = self._build_contents()

        try:
            # We inject the system prompt as the first message
            # But the user mentioned `stealth/ox-alpha` might prefer it in user turn.
            # We will use the system role, which OpenRouter supports.
            messages = [{"role": "system", "content": self._system_prompt}] + contents

            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=0.7,
                max_tokens=1024,
            )

            assistant_text = response.choices[0].message.content or ""

            # Check if the response contains tool call patterns
            # We use a convention: if the model outputs JSON with a "tool_call" key,
            # we parse and execute it
            tool_calls_this_turn = []
            extracted_calls = self._extract_tool_calls(assistant_text)

            for call_info in extracted_calls:
                tool_name = call_info.get("tool_name", "")
                tool_args = call_info.get("arguments", {})

                if tool_name in self._tools:
                    result = self._tools[tool_name](**tool_args)
                    tc = ToolCall(tool_name=tool_name, arguments=tool_args, result=result)
                    tool_calls_this_turn.append(tc)
                    self.tool_calls_log.append(tc)
                    logger.info(f"[{self.name}] Tool called: {tool_name}({tool_args}) → {result}")

            self.conversation_history.append(
                ConversationTurn(
                    role="assistant",
                    content=assistant_text,
                    tool_calls=tool_calls_this_turn,
                )
            )

            return assistant_text

        except Exception as e:
            error_msg = f"[{self.name}] API error: {e}"
            logger.error(error_msg)
            self.conversation_history.append(
                ConversationTurn(role="assistant", content=error_msg)
            )
            return error_msg

    def _build_contents(self) -> list[dict]:
        """Build the messages list for the OpenAI API call."""
        contents = []
        for turn in self.conversation_history:
            role = turn.role if turn.role in ["user", "assistant"] else "assistant"
            contents.append({"role": role, "content": turn.content})
        return contents

    def _extract_tool_calls(self, text: str) -> list[dict]:
        """
        Extract tool call intentions from the model's response.
        Convention: model outputs ```tool_call\n{JSON}\n``` blocks.
        """
        calls = []
        marker = "```tool_call"
        parts = text.split(marker)
        for part in parts[1:]:
            end = part.find("```")
            if end != -1:
                json_str = part[:end].strip()
                try:
                    call_data = json.loads(json_str)
                    calls.append(call_data)
                except json.JSONDecodeError:
                    pass
        return calls
