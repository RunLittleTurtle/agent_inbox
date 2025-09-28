# Prompt Management Guide

Complete guide for managing system prompts in the React Agent MCP template with config UI integration.

## Overview

The template uses a centralized prompt management system with:
- `prompt.py` - Define prompts following LangGraph best practices
- Config UI integration - Edit prompts through web interface
- Dynamic placeholder replacement - Context-aware prompts
- Modular prompt structure - Separate sections for easy maintenance

## Prompt Architecture

### File Structure

```
src/your_agent/
├── prompt.py          # Main prompt definitions
├── config.py          # Agent configuration and context
├── ui_config.py       # Config UI prompt field definitions
└── x_agent_orchestrator.py  # Prompt integration
```

### Core Components

1. **System Prompt**: Main agent instructions and behavior
2. **Role Prompt**: Agent role and responsibilities
3. **Guidelines Prompt**: Operational guidelines and constraints
4. **Context Integration**: Dynamic time/timezone information

## Prompt Definition (`prompt.py`)

### Main System Prompt

```python
"""
System prompts for the React Agent MCP Template
Following LangGraph best practices - all prompts are defined here
These prompts are editable through the configuration UI
"""

# Main system prompt for the agent - editable through config UI
AGENT_SYSTEM_PROMPT = """You are a helpful {AGENT_DISPLAY_NAME} assistant specialized in {AGENT_DESCRIPTION}.

## Your Role:
- Help users efficiently with {AGENT_DISPLAY_NAME} operations
- Use available tools to complete tasks
- Provide clear, direct responses
- Handle errors gracefully and explain issues

## Guidelines:
- Be concise and actionable
- Use tools when appropriate for the request
- Explain what you're doing when using tools
- If tools fail, suggest alternatives or explain limitations
- When you complete a task, simply END - don't try to transfer back
- Don't use handoff tools - let the supervisor manage routing
- Focus on providing complete answers to questions

You are part of a multi-agent system. Focus on {AGENT_DISPLAY_NAME} tasks and let other agents handle their domains."""
```

### Modular Prompts

```python
# Role description prompt - editable section
AGENT_ROLE_PROMPT = """## Your Role:
- Help users efficiently with operations
- Use available tools to complete tasks
- Provide clear, direct responses
- Handle errors gracefully and explain issues"""

# Guidelines prompt - editable section
AGENT_GUIDELINES_PROMPT = """## Guidelines:
- Be concise and actionable
- Use tools when appropriate for the request
- Explain what you're doing when using tools
- If tools fail, suggest alternatives or explain limitations
- When you complete a task, simply END - don't try to transfer back
- Don't use handoff tools - let the supervisor manage routing
- Focus on providing complete answers to questions"""

# Legacy prompt for backwards compatibility
AGENT_PROMPT = """You are a helpful AI assistant specialized in {AGENT_DESCRIPTION}.
Use the available tools to help users efficiently."""
```

### Prompt Formatting Function

```python
def get_formatted_prompt(agent_display_name: str, agent_description: str) -> str:
    """
    Get the formatted system prompt with placeholder replacements
    Used by the agent at runtime
    """
    return AGENT_SYSTEM_PROMPT.replace(
        "{AGENT_DISPLAY_NAME}", agent_display_name
    ).replace(
        "{AGENT_DESCRIPTION}", agent_description
    )
```

## Config UI Integration

### UI Configuration Schema (`ui_config.py`)

Add prompt editing capability to your configuration UI:

```python
CONFIG_SECTIONS = [
    # ... other sections ...
    {
        'key': 'prompt_templates',
        'label': 'System Prompts',
        'description': 'Customize agent behavior through system prompts',
        'fields': [
            {
                'key': 'agent_system_prompt',
                'label': 'Main System Prompt',
                'type': 'textarea',
                'description': 'Main system prompt that defines agent behavior',
                'placeholder': 'You are a helpful assistant...',
                'required': True,
                'rows': 15,
                'note': 'Use {AGENT_DISPLAY_NAME} and {AGENT_DESCRIPTION} as placeholders'
            },
            {
                'key': 'agent_role_prompt',
                'label': 'Role Description',
                'type': 'textarea',
                'description': 'Define the agent\'s role and responsibilities',
                'rows': 8,
                'placeholder': '## Your Role:\n- Help users with...'
            },
            {
                'key': 'agent_guidelines_prompt',
                'label': 'Operational Guidelines',
                'type': 'textarea',
                'description': 'Guidelines for agent behavior and responses',
                'rows': 10,
                'placeholder': '## Guidelines:\n- Be concise and actionable...'
            }
        ]
    }
]
```

### Reading Prompt Values (Config API)

In `config-app/src/app/api/config/values/route.ts`, add prompt reading:

```typescript
if (agentId === 'your_agent') {
  const projectRoot = path.join(process.cwd(), '..');
  const promptPath = path.join(projectRoot, 'src/your_agent/prompt.py');

  if (fs.existsSync(promptPath)) {
    const content = fs.readFileSync(promptPath, 'utf8');

    // Extract prompts using regex patterns
    const systemPromptMatch = content.match(
      /AGENT_SYSTEM_PROMPT\s*=\s*"""([\s\S]*?)"""/
    );
    const rolePromptMatch = content.match(
      /AGENT_ROLE_PROMPT\s*=\s*"""([\s\S]*?)"""/
    );
    const guidelinesPromptMatch = content.match(
      /AGENT_GUIDELINES_PROMPT\s*=\s*"""([\s\S]*?)"""/
    );

    return {
      // ... other config sections ...
      prompt_templates: {
        agent_system_prompt: systemPromptMatch?.[1] || '',
        agent_role_prompt: rolePromptMatch?.[1] || '',
        agent_guidelines_prompt: guidelinesPromptMatch?.[1] || ''
      }
    };
  }
}
```

### Writing Prompt Values (Config API)

In `config-app/src/app/api/config/update/route.ts`, add prompt writing:

```typescript
if (configPath.includes('your_agent') && sectionKey === 'prompt_templates') {
  const promptPyPath = fullPath.replace('ui_config.py', 'prompt.py');

  if (!fs.existsSync(promptPyPath)) {
    console.error(`Prompt file not found: ${promptPyPath}`);
    return false;
  }

  let promptContent = fs.readFileSync(promptPyPath, 'utf8');

  if (fieldKey === 'agent_system_prompt') {
    promptContent = promptContent.replace(
      /(AGENT_SYSTEM_PROMPT\s*=\s*""")[\s\S]*?(""")/,
      `$1${value}$2`
    );
  } else if (fieldKey === 'agent_role_prompt') {
    promptContent = promptContent.replace(
      /(AGENT_ROLE_PROMPT\s*=\s*""")[\s\S]*?(""")/,
      `$1${value}$2`
    );
  } else if (fieldKey === 'agent_guidelines_prompt') {
    promptContent = promptContent.replace(
      /(AGENT_GUIDELINES_PROMPT\s*=\s*""")[\s\S]*?(""")/,
      `$1${value}$2`
    );
  }

  fs.writeFileSync(promptPyPath, promptContent, 'utf8');
  console.log(`Updated ${fieldKey} in ${promptPyPath}`);
  return true;
}
```

## Context Integration

### Dynamic Context Enhancement

The template automatically adds context to prompts:

```python
# In x_agent_orchestrator.py
def _build_workflow(self):
    """Build React agent with enhanced context"""
    context = get_current_context()

    enhanced_prompt = f"""{AGENT_SYSTEM_PROMPT}

**CURRENT CONTEXT:**
- Now: {context['current_time']}
- Timezone: {context['timezone_name']}
- Today: {context['today']}
- Current Time: {context['time_str']}

Use available tools efficiently and provide clear feedback."""

    return create_react_agent(
        model=self.llm,
        tools=self.tools,
        prompt=enhanced_prompt,
        name=f"{AGENT_NAME}_agent"
    )
```

### Context Information Available

From `config.py`, the context includes:

```python
def get_current_context() -> Dict[str, str]:
    """Get current time and timezone context"""
    timezone_zone = ZoneInfo(USER_TIMEZONE)
    current_time = datetime.now(timezone_zone)
    tomorrow = current_time + timedelta(days=1)

    return {
        "current_time": current_time.isoformat(),
        "timezone": str(timezone_zone),
        "timezone_name": USER_TIMEZONE,
        "today": f"{current_time.strftime('%Y-%m-%d')} ({current_time.strftime('%A')})",
        "tomorrow": f"{tomorrow.strftime('%Y-%m-%d')} ({tomorrow.strftime('%A')})",
        "time_str": current_time.strftime('%I:%M %p %Z')
    }
```

## Prompt Customization Patterns

### Service-Specific Examples

**Gmail Agent Prompt:**
```python
AGENT_SYSTEM_PROMPT = """You are a helpful Gmail assistant specialized in email management and organization.

## Your Role:
- Help users efficiently manage their Gmail inbox
- Send, search, organize, and archive emails
- Manage labels and email organization
- Provide email insights and summaries

## Available Email Operations:
- Send emails with proper formatting
- Search emails by sender, subject, date, or content
- Create and manage email labels
- Archive, delete, or organize emails
- Extract important information from emails

## Guidelines:
- Always confirm before sending emails
- Use clear, professional email formatting
- Respect email privacy and security
- Provide email summaries when searching
- When sending emails, ask for confirmation of recipients and content
- Handle attachments and email threads appropriately

You focus on Gmail operations. For calendar, documents, or other services, let the supervisor route to appropriate agents."""
```

**Google Sheets Agent Prompt:**
```python
AGENT_SYSTEM_PROMPT = """You are a helpful Google Sheets assistant specialized in spreadsheet operations and data management.

## Your Role:
- Help users create, read, and modify spreadsheets
- Perform data analysis and calculations
- Format and organize spreadsheet data
- Create charts and visualizations

## Available Spreadsheet Operations:
- Create new spreadsheets and worksheets
- Read and write cell values and ranges
- Format cells, rows, and columns
- Create formulas and calculations
- Generate charts and graphs
- Manage sheet permissions and sharing

## Guidelines:
- Always specify exact cell ranges when working with data
- Preserve existing data unless explicitly asked to overwrite
- Use proper spreadsheet formulas and functions
- Maintain data consistency and formatting
- Provide clear explanations of data changes
- Handle large datasets efficiently

You focus on spreadsheet operations. For email, documents, or other services, let the supervisor route to appropriate agents."""
```

### Placeholder Usage

Use these placeholders in your prompts:

- `{AGENT_DISPLAY_NAME}` - Human-readable agent name
- `{AGENT_DESCRIPTION}` - Agent capability description

Example with placeholders:
```python
AGENT_SYSTEM_PROMPT = """You are a helpful {AGENT_DISPLAY_NAME} assistant specialized in {AGENT_DESCRIPTION}.

Your primary focus is {AGENT_DESCRIPTION}. When users need help with other services, guide them to use the appropriate agent through the supervisor system.

Available {AGENT_DISPLAY_NAME} capabilities:
- [List your agent's specific capabilities]
- [Based on your MCP tools and functionality]
"""
```

## Prompt Testing and Validation

### Testing Prompts in Development

```python
# Test prompt formatting
from prompt import get_formatted_prompt
from config import AGENT_DISPLAY_NAME, AGENT_DESCRIPTION

formatted_prompt = get_formatted_prompt(AGENT_DISPLAY_NAME, AGENT_DESCRIPTION)
print("=== Formatted Prompt ===")
print(formatted_prompt)
```

### Validate Prompt Integration

```python
# Test complete workflow creation
from x_agent_orchestrator import create_default_orchestrator

try:
    workflow = create_default_orchestrator()
    print("✅ Workflow created successfully with prompt")
except Exception as e:
    print(f"❌ Prompt integration error: {e}")
```

### Testing with Config UI

1. Start config server: `npm run dev:config`
2. Navigate to `http://localhost:3004/config`
3. Edit prompt in "System Prompts" section
4. Save changes
5. Restart agent to test new prompt

## Best Practices

### Prompt Structure

1. **Clear Role Definition**: Start with what the agent is and does
2. **Capability Overview**: List available operations
3. **Behavioral Guidelines**: Define how the agent should respond
4. **Context Awareness**: Include relevant system context
5. **Boundary Setting**: Define what the agent should/shouldn't do

### Writing Effective Prompts

1. **Be Specific**: Clear, unambiguous instructions
2. **Use Examples**: Provide examples for complex operations
3. **Set Expectations**: Define response format and style
4. **Handle Errors**: Include error handling guidance
5. **Stay Focused**: Keep prompts focused on the agent's domain

### Multi-Agent Considerations

1. **Domain Boundaries**: Clearly define agent responsibilities
2. **Handoff Guidance**: When to let supervisor handle routing
3. **Avoid Overlap**: Prevent conflicting agent behaviors
4. **Consistent Style**: Maintain consistent interaction patterns

### Maintenance

1. **Version Control**: Track prompt changes in git
2. **Testing**: Test prompts with real scenarios
3. **User Feedback**: Incorporate user experience feedback
4. **Iterative Improvement**: Refine prompts based on performance

## Common Prompt Patterns

### Error Handling

```python
## Error Handling:
- If a tool fails, explain what went wrong clearly
- Suggest alternative approaches when possible
- Never make up information if tools aren't available
- Ask for clarification when requests are ambiguous
```

### Tool Usage Guidance

```python
## Tool Usage:
- Always use tools when they're available for the task
- Explain what you're doing when using tools
- Provide summaries of tool results
- Chain tools logically for complex operations
```

### Response Formatting

```python
## Response Format:
- Provide clear, actionable responses
- Use bullet points for lists and steps
- Include relevant details without overwhelming
- End responses definitively - don't transfer back to supervisor
```

### Security and Privacy

```python
## Security Guidelines:
- Never log or expose sensitive information
- Confirm before performing destructive operations
- Respect user privacy and data protection
- Handle authentication securely
```

This prompt management system provides flexible, maintainable, and user-friendly prompt customization while maintaining the technical robustness required for production deployment.