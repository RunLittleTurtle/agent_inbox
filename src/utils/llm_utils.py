"""
Centralized LLM utilities for cross-provider compatibility.

This module provides standardized functions for:
- Creating LLM instances (Anthropic or OpenAI)
- Formatting tool_choice parameters correctly per provider
- Binding tools with proper provider-specific parameters
"""

from typing import List, Optional, Union, Any
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_core.language_models import BaseChatModel


def get_llm(model_name: str, temperature: float = 0, **kwargs) -> BaseChatModel:
    """
    Get the appropriate LLM instance based on model name.

    Args:
        model_name: Name of the model (e.g., 'claude-3-5-sonnet', 'gpt-4o')
        temperature: Model temperature (0-1)
        **kwargs: Additional provider-specific parameters

    Returns:
        Configured LLM instance (ChatAnthropic or ChatOpenAI)

    Note:
        Provider-specific parameters like parallel_tool_calls should NOT be passed here.
        Use bind_tools_with_choice() instead for proper tool binding.

        Reasoning models (gpt-5, gpt-5-mini, o3) do NOT support the temperature parameter.
        Temperature will be automatically excluded for these models.
    """
    # OpenAI reasoning models that don't support temperature parameter
    # Synced with config/model_constants.json REASONING_MODELS_NO_TEMPERATURE
    # To add new reasoning model: update the list in model_constants.json
    reasoning_models = ['gpt-5', 'gpt-5-mini', 'o3']
    is_reasoning_model = any(rm in model_name.lower() for rm in reasoning_models)

    if model_name.startswith('claude') or model_name.startswith('opus'):
        return ChatAnthropic(model=model_name, temperature=temperature, **kwargs)
    else:  # OpenAI models (gpt-*, o3)
        # Don't pass temperature for reasoning models
        if is_reasoning_model:
            print(f" Model {model_name} is a reasoning model - excluding temperature parameter")
            return ChatOpenAI(model=model_name, **kwargs)
        else:
            return ChatOpenAI(model=model_name, temperature=temperature, **kwargs)


def get_tool_choice(model_name: str, tool_name: Optional[str] = None) -> Union[dict, str]:
    """
    Get the correct tool_choice format based on model provider.

    Args:
        model_name: Name of the model (e.g., 'claude-3-5-sonnet', 'gpt-4o')
        tool_name: Name of specific tool to invoke (if None, requires any tool)

    Returns:
        Properly formatted tool_choice for the provider:
        - Anthropic: {"type": "tool", "name": "ToolName"} for specific tool
        - Anthropic: {"type": "any"} to require any tool
        - OpenAI: {"type": "function", "function": {"name": "ToolName"}} for specific tool
        - OpenAI: "required" to require any tool
    """
    if model_name.startswith('claude') or model_name.startswith('opus'):
        # Anthropic format
        if tool_name:
            return {"type": "tool", "name": tool_name}
        else:
            return {"type": "any"}
    else:
        # OpenAI format
        if tool_name:
            return {"type": "function", "function": {"name": tool_name}}
        else:
            return "required"


def bind_tools_with_choice(
    llm: BaseChatModel,
    model_name: str,
    tools: List[Any],
    tool_name: Optional[str] = None,
    parallel_tool_calls: bool = False
) -> BaseChatModel:
    """
    Bind tools to LLM with proper provider-specific parameters.

    Args:
        llm: LLM instance from get_llm()
        model_name: Name of the model (needed to determine provider)
        tools: List of tool schemas or classes to bind
        tool_name: Optional specific tool name to force (if None, any tool allowed)
        parallel_tool_calls: Whether to allow parallel tool calls (OpenAI only)

    Returns:
        LLM instance with tools bound and proper tool_choice set

    Example:
        >>> llm = get_llm("claude-sonnet-4-20250514", temperature=0.2)
        >>> tools = [MyTool1, MyTool2, MyTool3]
        >>> # Require any tool to be called:
        >>> bound = bind_tools_with_choice(llm, "claude-sonnet-4-20250514", tools)
        >>> # Force specific tool:
        >>> bound = bind_tools_with_choice(llm, "claude-sonnet-4-20250514", tools, tool_name="MyTool1")
    """
    tool_choice = get_tool_choice(model_name, tool_name)

    if model_name.startswith('claude') or model_name.startswith('opus'):
        # Anthropic: only tool_choice parameter
        return llm.bind_tools(tools, tool_choice=tool_choice)
    else:
        # OpenAI: tool_choice + parallel_tool_calls
        return llm.bind_tools(
            tools,
            tool_choice=tool_choice,
            parallel_tool_calls=parallel_tool_calls
        )


def is_anthropic_model(model_name: str) -> bool:
    """Check if model name is for Anthropic provider."""
    return model_name.startswith('claude') or model_name.startswith('opus')


def is_openai_model(model_name: str) -> bool:
    """Check if model name is for OpenAI provider."""
    return not is_anthropic_model(model_name)
