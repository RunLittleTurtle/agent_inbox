# Supervisor Connection Snippet

## Code to add to `src/graph.py`

Copy this function to `src/graph.py` and replace placeholders with your agent details:


```python
async def create_{AGENT_NAME}_agent():
    """Create {AGENT_DISPLAY_NAME} agent with MCP integration for {AGENT_DESCRIPTION}"""
    try:
        from src.{AGENT_NAME}_agent.x_agent_orchestrator import create_{AGENT_NAME}_agent as create_{AGENT_NAME}_orchestrator

        # Use proper {AGENT_NAME} agent orchestrator (returns compiled workflow)
        {AGENT_NAME}_agent_workflow = create_{AGENT_NAME}_orchestrator()

        logger.info("{AGENT_DISPLAY_NAME} agent with MCP integration initialized successfully")
        return {AGENT_NAME}_agent_workflow

    except Exception as e:
        logger.error(f"Failed to create {AGENT_NAME} agent with MCP: {e}")
        logger.info("Creating fallback {AGENT_NAME} agent without MCP tools")

        # Fallback: basic {AGENT_NAME} agent without MCP tools
        {AGENT_NAME}_model = ChatAnthropic(
            model="claude-sonnet-4-20250514",
            temperature=0,
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
            streaming=False
        )

        fallback_prompt = """You are a {AGENT_DISPLAY_NAME} assistant.
        I apologize, but I cannot directly access {AGENT_DISPLAY_NAME} at the moment due to a technical issue.
        I can provide general {AGENT_DESCRIPTION} assistance and planning, but cannot perform actual operations.
        Please let me know how I can assist you with {AGENT_DESCRIPTION} planning."""

        return create_react_agent(
            model={AGENT_NAME}_model,
            tools=[],
            name="{AGENT_NAME}_agent_fallback",
            prompt=fallback_prompt
        )
```





## Example: Gmail Agent (for reference)

```python
async def create_gmail_agent():
    """Create Gmail agent with MCP integration for email management"""
    try:
        from src.gmail_agent.x_agent_orchestrator import create_gmail_agent as create_gmail_orchestrator

        # Use proper gmail agent orchestrator (returns compiled workflow)
        gmail_agent_workflow = create_gmail_orchestrator()

        logger.info("Gmail agent with MCP integration initialized successfully")
        return gmail_agent_workflow

    except Exception as e:
        logger.error(f"Failed to create gmail agent with MCP: {e}")
        logger.info("Creating fallback gmail agent without MCP tools")

        # Fallback: basic gmail agent without MCP tools
        gmail_model = ChatAnthropic(
            model="claude-sonnet-4-20250514",
            temperature=0,
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
            streaming=False
        )

        fallback_prompt = """You are a Gmail assistant.
        I apologize, but I cannot directly access Gmail at the moment due to a technical issue.
        I can provide general email management assistance and planning, but cannot perform actual operations.
        Please let me know how I can assist you with email management planning."""

        return create_react_agent(
            model=gmail_model,
            tools=[],
            name="gmail_agent_fallback",
            prompt=fallback_prompt
        )
```

## Add to supervisor agents list

In `create_supervisor_graph()` function:

```python
async def create_supervisor_graph():
    # ... existing code ...

    # Add your agent
    {AGENT_NAME}_agent = await create_{AGENT_NAME}_agent()

    # Add to supervisor
    workflow = create_supervisor(
        agents=[
            calendar_agent,
            email_agent,
            drive_agent,
            job_search_agent,
            {AGENT_NAME}_agent,  # Add your agent here
        ],
        model=supervisor_model,
        prompt=supervisor_prompt,
        # ... rest of config
    )
```

## Add to supervisor prompt

In the `supervisor_prompt` string in `src/graph.py`:

```python
supervisor_prompt = f"""You are a team supervisor dispatching requests and managing specialized agents.

AGENT CAPABILITIES:
- calendar_agent: All calendar operations
- email_agent: Email management and composition
- job_search_agent: CV, job search, career advice
- drive_agent: File management, Google Drive integration
- {AGENT_NAME}_agent: {AGENT_DISPLAY_NAME} {AGENT_DESCRIPTION}

ROUTING RULES:
- Calendar/scheduling → calendar_agent
- Email tasks → email_agent
- Job search/career → job_search_agent
- File management → drive_agent
- {AGENT_DISPLAY_NAME} operations → {AGENT_NAME}_agent

Route quickly and decisively to the appropriate agent."""
```
