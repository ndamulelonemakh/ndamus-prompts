"""
Simple tool selector to prevent overwhelming LLMs with too many tools at once.
Dynamically selects the most relevant tools based on user queries and conversation context.

Installation:
    pip install agno loguru google-genai

Basic Usage:
    ```python
    from simple_tool_selector import SimpleToolSelector
    
    # Initialize with your Google API key
    selector = SimpleToolSelector(api_key="your-google-api-key")
    
    # Select relevant tools for a query
    selected_tools = selector.select_relevant_tools(
        user_message="Help me analyze this CSV data",
        history=conversation_history,
        available_tools=your_agent_tools,
        max_tools=10
    )
    ```

Environment Setup:
    Set your Google API key as an environment variable:
    ```bash
    export GOOGLE_API_KEY=your_actual_api_key
    ```

Potential Improvements:
    - Support for custom scoring functions and selection criteria
    - Integration with vector databases for large tool collections
    - Use LiteLLM for multi-provider support (OpenAI, Anthropic, etc.)
"""

import inspect
import os
import traceback
from textwrap import dedent
from typing import Any, Callable, Dict, List, Optional

from agno.agent import Agent
from agno.tools import Toolkit, Function
from agno.tools.mcp import MultiMCPTools
from google import genai
from google.genai import types
from loguru import logger
from pydantic import BaseModel, Field

class ToolSelection(BaseModel):
    name: str = Field(..., description="The name of the tool/function")
    toolkit: str = Field("default", description="The toolkit to which the tool/function belongs")
    relevance: int = Field(..., ge=0, le=10,
                           description="A score indicating the relevance of the tool/function out of 10")


class SelectedTools(BaseModel):
    tools: List[ToolSelection] = Field(..., description="The list of selected tools/functions")


class SimpleToolSelector:
    def __init__(self, api_key: Optional[str] = os.getenv("GOOGLE_API_KEY"), model: str = "gemini-2.5-flash-lite"):
        """
        Initialize the tool selector.

        Args:
            api_key: Google API key for Gemini
            model: Gemini model to use for tool selection. Future iterations may use LiteLLM to enable more
            freedom in model choice.
        """
        assert api_key, "API key must be provided or set in environment variables"
        self.client = genai.Client(api_key=api_key)
        self.model = model
        self._tool_cache: Dict[str, List[Dict[str, Any]]] = {}

    @staticmethod
    def _get_function_metadata(func: Callable) -> Dict[str, Any]:
        name = func.__name__
        docstring = inspect.getdoc(func)
        signature = inspect.signature(func)
        parameters = []

        for param_name, param in signature.parameters.items():
            param_info = {
                'name': param_name,
                'annotation': param.annotation if param.annotation != inspect.Parameter.empty else None,
                'default': param.default if param.default != inspect.Parameter.empty else None,
                'kind': param.kind.name
            }
            parameters.append(param_info)

        return {
            'name': name,
            'docstring': docstring,
            'parameters': parameters,
            'signature': str(signature),
            'full_signature': f"{name}{signature}"
        }

    def extract_tools_metadata(self, agent: Agent) -> List[Dict[str, Any]]:
        cache_key = f"agent_{id(agent)}"
        if cache_key in self._tool_cache:
            return self._tool_cache[cache_key]

        metadata = []
        for tool in agent.tools:
            if isinstance(tool, MultiMCPTools):
                for name, fn in tool.functions.items():
                    logger.debug(f"Processing MCP function: {name}")
                    metadata.append(
                        fn.to_dict() | {"toolkit": "MCP"}
                    )
            elif isinstance(tool, Toolkit):
                toolkit_name = tool.name
                for fn in tool.tools:
                    function_metadata = self._get_function_metadata(fn)
                    metadata.append(function_metadata | {"toolkit": toolkit_name})
            elif isinstance(tool, Function):
                function_metadata = tool.to_dict()
                metadata.append(function_metadata | {"toolkit": "default"})
            elif isinstance(tool, Callable):
                function_metadata = self._get_function_metadata(tool)
                metadata.append(function_metadata | {"toolkit": "default"})
            else:
                logger.warning(f"Unknown tool type: {type(tool)}")

        self._tool_cache[cache_key] = metadata
        return metadata

    def clear_cache(self):
        self._tool_cache.clear()

    @staticmethod
    def _fallback_selection(
            user_message: str,
            available_tools: List[Dict[str, Any]],
            max_tools: int
    ) -> List[ToolSelection]:
        """Fallback tool selection based on simple keyword matching. (These could also use cosine similarity or RAG"""
        logger.warning("Using fallback tool selection...")
        message_words = set(user_message.lower().split())
        scored_tools = []

        for tool in available_tools:
            score = 0
            tool_text = f"{tool.get('name', '')} {tool.get('docstring', '')}".lower()

            for word in message_words:
                if word in tool_text:
                    score += 1

            scored_tools.append((tool, score))

        # Sort by score and take top tools
        scored_tools.sort(key=lambda x: x[1], reverse=True)
        selected = scored_tools[:max_tools]

        return [
            ToolSelection(
                name=tool.get('name', 'unknown'),
                toolkit=tool.get('toolkit', 'default'),
                relevance=min(score * 2, 10)  # Scale score to 0-10
            )
            for tool, score in selected
        ]

    def _select_with_llm(self, prompt: str, system: Optional[str] = None) -> list[ToolSelection]:
        contents = [
            types.Content(
                role="user",
                parts=[types.Part.from_text(text=prompt)],
            )
        ]

        generate_content_config = types.GenerateContentConfig(
            thinking_config=types.ThinkingConfig(
                include_thoughts=False,
                thinking_budget=1024,
            ),
            temperature=0,
            system_instruction=[
                types.Part.from_text(text=system or "You are a helpful assistant"),
            ],
            response_mime_type="application/json",
            response_schema=list[ToolSelection],
        )

        result = self.client.models.generate_content(
            model=self.model,
            contents=contents,
            config=generate_content_config,
        )

        return result.parsed

    def select_relevant_tools(
            self,
            user_message: str,
            history: List[Dict[str, Any]],
            available_tools: List[Dict[str, Any]],
            max_tools: int = 50,
            min_tools: int = 3
    ) -> List[ToolSelection]:
        system_prompt = """You are the Chief AI engineer responsible for optimising an intelligent AI chat \
        assistant which uses a variety of tools"""
        prompt = dedent(f"""Given the following user query, conversation history and tool descriptions, \
        select the most relevant tools/functions that will be useful
        to get additional context or perform the necessary actions to achieve the users goals:

        ###Latest user message:
        {user_message}

        ###Conversation history:
        {history}

        ###Available tools:
        {available_tools}

        ---
        Instructions:
         - Your goal is to select a minimum of {min_tools} up to a maximum of {max_tools} relevant tools/functions \
         ranked by their relevance to the user query and context.
         - You should format your response as a JSON array where each object has the following keys: 
           - `name`: The name of the tool/function
           - `toolkit`: The toolkit to which the tool/function belongs if available, else use "default"
           - `relevance`: A score indicating the relevance of the tool/function out of 10
        """)

        try:
            response = self._select_with_llm(prompt, system_prompt)
            return response
        except Exception as e:
            logger.error(f"Error selecting tools: {e}\n{traceback.format_exc()}")
            return self._fallback_selection(user_message, available_tools, max_tools)

    def filter_agent_tools(
            self,
            agent: Agent,
            user_message: str,
            history: List[Dict[str, Any]] = None,
            max_tools: int = 50
    ) -> List[ToolSelection]:
        """
        High-level method to filter agent tools based on relevance.

        Args:
            agent: The agent to filter tools for
            user_message: The user's message
            history: Conversation history (optional)
            max_tools: Maximum number of tools to select

        Returns:
            List of selected tools
        """
        if history is None:
            history = []

        available_tools = self.extract_tools_metadata(agent)
        return self.select_relevant_tools(
            user_message=user_message,
            history=history,
            available_tools=available_tools,
            max_tools=max_tools
        )


def select_tools_for_query(
        agent: Agent,
        user_message: str,
        history: List[Dict[str, Any]] = None,
        max_tools: int = 50,
        model: str = "gemini-2.5-flash-lite"
) -> List[ToolSelection]:
    selector = SimpleToolSelector(model=model)
    return selector.filter_agent_tools(agent, user_message, history, max_tools)
