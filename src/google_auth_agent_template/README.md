# Google OAuth Agent Template

**Generic template for building LangGraph agents with Google Workspace OAuth authentication.**

This template provides a production-ready architecture for creating agents that interact with Google APIs (Calendar, Contacts, Gmail, Drive, etc.) using OAuth 2.0 authentication.

---

## 🎯 What This Template Provides

- ✅ **Google OAuth 2.0 Integration**: Fetch refresh tokens from Supabase, use shared client credentials
- ✅ **LangGraph 2025 Patterns**: Uses `create_react_agent` prebuilt for tool-calling
- ✅ **Graceful Degradation**: Falls back to "connect your account" message when OAuth missing
- ✅ **Tool Wrapper Pattern**: Closure-based LangChain tools for clean API access
- ✅ **Config UI Integration**: Full configuration schema for config-app
- ✅ **User-Editable Prompts**: Load custom prompts from Supabase
- ✅ **State Management**: Pydantic v2 with custom reducers

---

## 📁 Template Structure

```
google_auth_agent_template/
├── __init__.py                    # Module exports
├── config.py                      # Agent configuration (LLM, timezone, OAuth scopes)
├── agent_orchestrator.py          # Main agent workflow (LangGraph)
├── state.py                       # State schema with Pydantic v2
├── prompt.py                      # System prompts (customizable)
├── executor_factory.py            # OAuth credential loading (100% reusable)
├── google_workspace_executor.py   # Google API client wrapper
├── google_workspace_tools.py      # LangChain tools for agent
├── ui_config.py                   # Configuration UI schema
└── README.md                      # This file
```

---

## 🚀 How to Use This Template

### Step 1: Copy and Rename

```bash
# Copy template to new agent folder
cp -r src/google_auth_agent_template src/contacts_agent

# Navigate to new agent
cd src/contacts_agent
```

### Step 2: Global Find & Replace

Replace the following placeholders throughout all files:

| Placeholder | Replace With | Example |
|-------------|--------------|---------|
| `{DOMAIN}` | Your agent domain (lowercase) | `contacts`, `email`, `calendar` |
| `{Domain}` | Your agent domain (capitalized) | `Contacts`, `Email`, `Calendar` |
| `{SERVICE_NAME}` | Google API service name | `People`, `Gmail`, `Calendar` |
| `{API_VERSION}` | Google API version | `v1`, `v3` |
| `GoogleAuthAgent` | Your agent class name | `ContactsAgent`, `EmailAgent` |
| `create_google_auth_agent` | Your factory function | `create_contacts_agent` |

**Quick Find & Replace (macOS/Linux):**
```bash
# Replace {DOMAIN} with contacts
find . -type f -name "*.py" -exec sed -i '' 's/{DOMAIN}/contacts/g' {} +

# Replace {Domain} with Contacts
find . -type f -name "*.py" -exec sed -i '' 's/{Domain}/Contacts/g' {} +

# Replace {SERVICE_NAME} with People
find . -type f -name "*.py" -exec sed -i '' 's/{SERVICE_NAME}/People/g' {} +

# Replace {API_VERSION} with v1
find . -type f -name "*.py" -exec sed -i '' 's/{API_VERSION}/v1/g' {} +

# Replace class/function names
find . -type f -name "*.py" -exec sed -i '' 's/GoogleAuthAgent/ContactsAgent/g' {} +
find . -type f -name "*.py" -exec sed -i '' 's/create_google_auth_agent/create_contacts_agent/g' {} +
```

### Step 3: Customize Files

#### 3.1 `config.py` - Update OAuth Scopes

```python
# Replace with your required scopes
GOOGLE_OAUTH_SCOPES = [
    "https://www.googleapis.com/auth/contacts.readonly",
    "https://www.googleapis.com/auth/contacts",
]
```

**Scope Reference:**
- **Calendar**: `calendar`, `calendar.events`
- **Contacts**: `contacts`, `contacts.readonly`
- **Gmail**: `gmail.readonly`, `gmail.modify`, `gmail.send`
- **Drive**: `drive`, `drive.file`, `drive.readonly`

See full list: https://developers.google.com/identity/protocols/oauth2/scopes

#### 3.2 `google_workspace_executor.py` - Implement API Methods

```python
class ContactsExecutor(GoogleWorkspaceExecutor):
    SERVICE_NAME = "people"  # Google People API
    API_VERSION = "v1"

    SCOPES = [
        "https://www.googleapis.com/auth/contacts.readonly",
    ]

    def list_contacts(self, page_size: int = 50):
        """List contacts from Google Contacts"""
        results = self.service.people().connections().list(
            resourceName='people/me',
            pageSize=page_size,
            personFields='names,emailAddresses,phoneNumbers'
        ).execute()
        return results.get('connections', [])

    def get_contact(self, resource_name: str):
        """Get contact details"""
        person = self.service.people().get(
            resourceName=resource_name,
            personFields='names,emailAddresses,phoneNumbers,addresses'
        ).execute()
        return person
```

**API Documentation:**
- Calendar: https://developers.google.com/calendar/api/v3/reference
- People (Contacts): https://developers.google.com/people/api/rest
- Gmail: https://developers.google.com/gmail/api/reference/rest
- Drive: https://developers.google.com/drive/api/v3/reference

#### 3.3 `google_workspace_tools.py` - Create LangChain Tools

```python
def create_google_workspace_tools(executor: ContactsExecutor) -> List[BaseTool]:
    """Create tools for Contacts agent"""

    @tool
    def list_contacts(page_size: int = 50) -> str:
        """List contacts from Google Contacts"""
        try:
            contacts = executor.list_contacts(page_size)
            return json.dumps(contacts, indent=2)
        except Exception as e:
            logger.error(f"Error listing contacts: {e}")
            return f"Error: {str(e)}"

    @tool
    def get_contact(resource_name: str) -> str:
        """Get contact details by resource name"""
        try:
            contact = executor.get_contact(resource_name)
            return json.dumps(contact, indent=2)
        except Exception as e:
            logger.error(f"Error getting contact: {e}")
            return f"Error: {str(e)}"

    return [list_contacts, get_contact]
```

#### 3.4 `prompt.py` - Customize Agent Instructions

Update `AGENT_SYSTEM_PROMPT` with domain-specific instructions:

```python
AGENT_SYSTEM_PROMPT = """
You are a Contacts assistant with access to Google Contacts API.

ROLE:
Help users search, view, and manage their Google Contacts.

CAPABILITIES:
- List contacts with pagination
- Get detailed contact information
- Search contacts by name or email

INSTRUCTIONS:
1. When listing contacts, show: name, email, phone
2. Format contact information clearly
3. Respect user privacy - only show requested data
4. Ask before performing any modifications
"""
```

#### 3.5 `state.py` - Add Domain-Specific Fields

```python
class ContactsAgentState(MessagesState):
    """State for Contacts agent"""

    user_id: str = ""

    # Domain-specific fields
    current_contacts: Annotated[List[Dict], merge_dict_lists] = Field(
        default_factory=list,
        description="List of contacts currently being discussed"
    )

    search_query: Optional[str] = Field(
        default=None,
        description="Current search query"
    )

    selected_contact: Optional[Dict] = Field(
        default=None,
        description="Currently selected contact"
    )
```

#### 3.6 `ui_config.py` - Add Configuration Fields

```python
{
    "section_id": "google_integration",
    "section_title": "Google Contacts Integration",
    "fields": [
        {
            "field_id": "max_contacts",
            "field_type": "number",
            "label": "Max Contacts to Fetch",
            "default_value": 50,
            "min": 1,
            "max": 200,
        },
        {
            "field_id": "default_contact_group",
            "field_type": "text",
            "label": "Default Contact Group",
            "default_value": "myContacts",
        },
    ]
}
```

### Step 4: Test Locally

```bash
# Activate virtual environment
source .venv/bin/activate

# Test agent initialization
python -c "
import asyncio
from contacts_agent import ContactsAgent

async def test():
    agent = ContactsAgent(user_id='user_test_123')
    await agent.initialize()
    print('Agent initialized successfully!')

asyncio.run(test())
"
```

### Step 5: Integrate with Supervisor

Update `src/graph.py` to add your new agent:

```python
from contacts_agent import create_contacts_agent

async def contacts_agent_node(state: State, config: RunnableConfig) -> Dict:
    """Contacts agent node"""
    user_id = config["configurable"].get("user_id")
    model = get_llm(...)

    contacts_agent = await create_contacts_agent(
        model=model,
        user_id=user_id
    )

    result = await contacts_agent.ainvoke({"messages": state["messages"]})
    return {"messages": result["messages"]}

# Add to supervisor graph
workflow.add_node("contacts_agent", contacts_agent_node)
```

---

## 🔐 OAuth Setup

### Required Environment Variables

Add to `.env`:

```bash
# Google OAuth App Credentials (shared across all users)
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret

# Agent-specific config
CONTACTS_LLM_MODEL=claude-3-5-sonnet-20241022
CONTACTS_LLM_TEMPERATURE=0.1
```

### Google Cloud Console Setup

1. Go to https://console.cloud.google.com/apis/credentials
2. Create OAuth 2.0 Client ID (Web application)
3. Add authorized redirect URI: `https://your-config-app.vercel.app/api/oauth/google/contacts_agent/callback`
4. Enable required APIs:
   - **Contacts**: Google People API
   - **Email**: Gmail API
   - **Calendar**: Google Calendar API
   - **Drive**: Google Drive API

### Supabase Schema

User refresh tokens are stored in `user_secrets` table:

```sql
-- Table structure (already exists)
CREATE TABLE user_secrets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL,
    google_refresh_token TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

---

## 📚 LangGraph 2025 Patterns Used

### 1. Prebuilt create_react_agent

```python
# Simple tool-calling agent (recommended)
agent = create_react_agent(
    model=self.model,
    tools=self.tools,
    prompt=agent_prompt
)
# Returns compiled graph - ready to use!
```

### 2. Graceful OAuth Fallback

```python
# No credentials? Show user how to connect
if not self.tools:
    agent = create_react_agent(
        model=self.model,
        tools=[],
        prompt=get_no_tools_prompt()
    )
```

### 3. Closure Pattern for Tools

```python
def create_tools(executor):
    @tool
    def my_tool(param: str) -> str:
        # Executor captured in closure
        return executor.call_api(param)
    return [my_tool]
```

---

## 🎨 Advanced: Human-in-the-Loop

If your agent performs WRITE operations (send emails, create events), add approval workflow:

### 1. Create Approval Node

```python
def approval_node(state: State, config: RunnableConfig):
    """Request human approval before executing"""
    from langgraph.checkpoint.base import interrupt

    # Show user what will happen
    draft = state.get("draft_action")
    approval = interrupt(f"Approve this action? {draft}")

    return {"approval_granted": approval}
```

### 2. Add Conditional Routing

```python
workflow = StateGraph(ContactsAgentState)
workflow.add_node("agent", agent)
workflow.add_node("approval", approval_node)

def should_approve(state):
    if state.get("requires_approval"):
        return "approval"
    return END

workflow.add_conditional_edges("agent", should_approve, {
    "approval": "approval",
    END: END
})
```

---

## 🐛 Troubleshooting

### Agent shows "No tools available"

**Cause**: Google OAuth credentials not found in Supabase

**Fix**:
1. Check user has connected Google account in config-app
2. Verify `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` in `.env`
3. Check Supabase `user_secrets` table has `google_refresh_token` for user

### "deleted_client" OAuth Error

**Cause**: Using wrong `GOOGLE_CLIENT_ID` (from deleted OAuth app)

**Fix**:
1. Go to Google Cloud Console
2. Verify OAuth client is **Active**
3. Copy correct Client ID (long alphanumeric string)
4. Update `.env` and LangGraph Cloud environment variables

### ImportError for google_workspace_tools

**Cause**: Module not properly initialized

**Fix**:
1. Check `__init__.py` exists and imports are correct
2. Verify no syntax errors in `google_workspace_tools.py`
3. Ensure `executor_factory.py` imports the right function name

---

## 📖 Additional Resources

- **LangGraph Docs**: https://langchain-ai.github.io/langgraph/
- **Google OAuth Scopes**: https://developers.google.com/identity/protocols/oauth2/scopes
- **Google API Explorer**: https://developers.google.com/apis-explorer
- **Calendar API Ref**: https://developers.google.com/calendar/api/v3/reference
- **People API Ref**: https://developers.google.com/people/api/rest
- **Gmail API Ref**: https://developers.google.com/gmail/api/reference/rest

---

## ✅ Checklist for New Agent

- [ ] Copy template to `src/{your_agent}/`
- [ ] Global find & replace for all placeholders
- [ ] Update OAuth scopes in `config.py`
- [ ] Implement executor methods in `google_workspace_executor.py`
- [ ] Create LangChain tools in `google_workspace_tools.py`
- [ ] Customize prompts in `prompt.py`
- [ ] Add state fields in `state.py`
- [ ] Update UI config in `ui_config.py`
- [ ] Test locally with `python -c "..."`
- [ ] Enable Google API in Cloud Console
- [ ] Add to supervisor in `src/graph.py`
- [ ] Deploy and test with real user

---

**Happy Building! 🎉**

This template saves you ~80% of boilerplate code. Focus on your domain-specific logic and let the OAuth architecture handle the rest.
