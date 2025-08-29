#!/usr/bin/env python3
"""
Ambient Email Agent CLI
A command-line interface for the Agent Inbox email workflow system.
"""

import asyncio
import subprocess
import sys
import os
import time
import webbrowser
import signal
import psutil
from pathlib import Path
from typing import Optional, List
from datetime import datetime

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.syntax import Syntax
import httpx

app = typer.Typer(
    name="ambient-email",
    help="🤖 Ambient Email Agent - Human-in-the-loop email workflow system",
    rich_markup_mode="rich"
)

console = Console()

# Configuration
PROJECT_ROOT = Path(__file__).parent.parent.absolute()
VENV_PATH = PROJECT_ROOT / ".venv"
AGENT_INBOX_PATH = PROJECT_ROOT / "agent-inbox"
AGENT_CHAT_UI_PATH = PROJECT_ROOT / "agent-chat-ui"
LANGGRAPH_API = "http://127.0.0.1:2024"
AGENT_INBOX_UI = "http://localhost:3000"
AGENT_CHAT_UI = "http://localhost:3001"
LANGSMITH_STUDIO = "https://smith.langchain.com"


def ensure_venv():
    """Ensure virtual environment exists and is activated."""
    if not VENV_PATH.exists():
        console.print("[red]❌ Virtual environment not found![/red]")
        console.print(f"Expected: {VENV_PATH}")
        raise typer.Exit(1)
    
    # Check if we're in a virtual environment (multiple ways to detect)
    in_venv = (
        hasattr(sys, 'real_prefix') or  # older virtualenv
        (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix) or  # venv/virtualenv
        os.environ.get('VIRTUAL_ENV') is not None  # environment variable
    )
    
    if not in_venv:
        console.print("[yellow]⚠️  Not running in virtual environment![/yellow]")
        console.print(f"Please activate: [bold]source {VENV_PATH}/bin/activate[/bold]")
        raise typer.Exit(1)


def check_service(url: str, service_name: str) -> bool:
    """Check if a service is running."""
    try:
        import requests
        response = requests.get(url, timeout=2)
        return response.status_code in [200, 404]  # 404 is fine for API root
    except:
        return False


def find_processes_on_port(port: int) -> List[psutil.Process]:
    """Find processes running on a specific port."""
    processes = []
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            # Get connections separately to avoid attr access issues
            connections = proc.connections()
            for conn in connections:
                if hasattr(conn, 'laddr') and conn.laddr.port == port:
                    processes.append(proc)
                    break
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess, AttributeError):
            # Some processes don't have network connections or we don't have permission
            pass
    return processes


def kill_processes_on_port(port: int, service_name: str) -> bool:
    """Kill all processes running on a specific port."""
    processes = find_processes_on_port(port)
    
    if not processes:
        return False
    
    console.print(f"[yellow]⚠️  Found {len(processes)} process(es) running on port {port}[/yellow]")
    
    killed_any = False
    for proc in processes:
        try:
            console.print(f"[yellow]🔄 Killing {service_name} process {proc.pid} ({proc.name()})[/yellow]")
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except psutil.TimeoutExpired:
                console.print(f"[red]💀 Force killing process {proc.pid}[/red]")
                proc.kill()
                proc.wait()
            killed_any = True
            console.print(f"[green]✅ Successfully stopped process {proc.pid}[/green]")
        except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
            console.print(f"[yellow]⚠️  Could not kill process {proc.pid}: {e}[/yellow]")
    
    if killed_any:
        time.sleep(2)  # Give processes time to fully stop
    
    return killed_any


@app.command()
def inbox(
    port: int = typer.Option(3000, "--port", "-p", help="Port to run Agent Inbox on"),
    dev: bool = typer.Option(True, "--dev/--prod", help="Run in development mode"),
    restart: bool = typer.Option(True, "--restart/--no-restart", help="Kill existing processes and restart")
):
    """
    🚀 Launch the Agent Inbox UI
    
    Opens the React-based Agent Inbox interface for human-in-the-loop email workflow management.
    Automatically kills any existing processes on the port and restarts them.
    """
    console.print(Panel.fit(
        "🚀 [bold blue]Agent Inbox Launcher[/bold blue]",
        subtitle="Human-in-the-loop Email Workflow UI"
    ))
    
    ensure_venv()
    
    if not AGENT_INBOX_PATH.exists():
        console.print(f"[red]❌ Agent Inbox directory not found: {AGENT_INBOX_PATH}[/red]")
        raise typer.Exit(1)
    
    # Kill existing processes on the port if restart is enabled
    if restart:
        console.print(f"[blue]🔍 Checking for existing processes on port {port}...[/blue]")
        killed = kill_processes_on_port(port, "Agent Inbox")
        if not killed:
            console.print(f"[green]✅ No existing processes found on port {port}[/green]")
    
    # Check if LangGraph dev server is running
    if not check_service(LANGGRAPH_API, "LangGraph"):
        console.print(f"[yellow]⚠️  LangGraph dev server not detected at {LANGGRAPH_API}[/yellow]")
        console.print("   Agent Inbox needs the LangGraph dev server to function properly.")
        console.print("   Start it with: [bold]python cli.py langgraph[/bold]")
    
    console.print(f"📂 Working directory: {AGENT_INBOX_PATH}")
    console.print(f"🌐 Agent Inbox UI will be at: [link]http://localhost:{port}[/link]")
    console.print(f"🔗 Connects to LangGraph API: [link]{LANGGRAPH_API}[/link]")
    console.print()
    
    try:
        # Change to agent-inbox directory and run yarn dev
        os.chdir(AGENT_INBOX_PATH)
        
        if dev:
            console.print("[green]🔄 Starting development server...[/green]")
            
            # Start yarn dev with custom port in the background
            env = os.environ.copy()
            env['PORT'] = str(port)
            process = subprocess.Popen(["yarn", "dev"], env=env)
            
            # Wait a moment for server to start, then open browser
            console.print("[blue]💭 Waiting for server to start...[/blue]")
            time.sleep(5)
            
            # Open browser
            browser_url = f"http://localhost:{port}"
            console.print(f"[green]🌎 Opening {browser_url} in your browser...[/green]")
            webbrowser.open(browser_url)
            
            # Wait for the process to complete (user will Ctrl+C to stop)
            try:
                process.wait()
            except KeyboardInterrupt:
                console.print("\n[yellow]📱 Stopping Agent Inbox...[/yellow]")
                process.terminate()
                process.wait()
        else:
            console.print("[green]🏗️  Building production version...[/green]")
            env = os.environ.copy()
            env['PORT'] = str(port)
            subprocess.run(["yarn", "build"], check=True, env=env)
            subprocess.run(["yarn", "start"], check=True, env=env)
            
    except subprocess.CalledProcessError as e:
        console.print(f"[red]❌ Failed to start Agent Inbox: {e}[/red]")
        raise typer.Exit(1)
    except KeyboardInterrupt:
        console.print("\n[yellow]📱 Agent Inbox stopped[/yellow]")


@app.command()
def langgraph(
    port: int = typer.Option(2024, "--port", "-p", help="Port to run LangGraph on"),
    studio: bool = typer.Option(True, "--studio/--no-studio", help="Open LangSmith Studio"),
    restart: bool = typer.Option(True, "--restart/--no-restart", help="Kill existing processes and restart")
):
    """
    🚀 Launch the LangGraph development server
    
    Starts the LangGraph API server for the email workflow engine.
    Automatically kills any existing processes on the port and restarts them.
    """
    console.print(Panel.fit(
        "🚀 [bold green]LangGraph Dev Server[/bold green]",
        subtitle="Email Workflow Engine"
    ))
    
    ensure_venv()
    
    # Kill existing processes on the port if restart is enabled
    if restart:
        console.print(f"[blue]🔍 Checking for existing processes on port {port}...[/blue]")
        killed = kill_processes_on_port(port, "LangGraph")
        if not killed:
            console.print(f"[green]✅ No existing processes found on port {port}[/green]")
    
    langgraph_url = f"http://127.0.0.1:{port}"
    console.print(f"🌐 LangGraph API will be at: [link]{langgraph_url}[/link]")
    if studio:
        console.print("🎨 LangSmith Studio will open automatically")
    console.print()
    
    try:
        os.chdir(PROJECT_ROOT)
        console.print("[green]🔄 Starting LangGraph development server...[/green]")
        subprocess.run(["langgraph", "dev", "--port", str(port)], check=True)
        
    except subprocess.CalledProcessError as e:
        console.print(f"[red]❌ Failed to start LangGraph: {e}[/red]")
        raise typer.Exit(1)
    except KeyboardInterrupt:
        console.print("\n[yellow]🤖 LangGraph server stopped[/yellow]")


@app.command()
def email(
    sender: str = typer.Option("test@example.com", help="Email sender address"),
    subject: str = typer.Option("Test Email", help="Email subject"),
    body: str = typer.Option("Hi there, please help me write a professional email response.", help="Email body"),
    wait: bool = typer.Option(True, "--wait/--no-wait", help="Wait for workflow to reach interrupt")
):
    """
    📧 Create and run a test email workflow
    
    Creates a dummy email and runs it through the adaptive email workflow,
    creating a thread that will appear in Agent Inbox for human review.
    """
    console.print(Panel.fit(
        "📧 [bold blue]Adaptive Email Workflow Test[/bold blue]",
        subtitle="Create test email and workflow thread"
    ))
    
    ensure_venv()
    
    # Check if LangGraph is running
    if not check_service(LANGGRAPH_API, "LangGraph"):
        console.print(f"[red]❌ LangGraph dev server not running at {LANGGRAPH_API}[/red]")
        console.print("   Please start it first with: [bold]ambient-email langgraph[/bold]")
        raise typer.Exit(1)
    
    asyncio.run(_run_email_workflow(sender, subject, body, wait))


async def _run_email_workflow(sender: str, subject: str, body: str, wait: bool):
    """Run the email workflow asynchronously."""
    from datetime import datetime
    
    # Create test email
    test_email = {
        "id": f"test_email_{int(datetime.now().timestamp())}",
        "subject": subject,
        "body": body,
        "sender": sender,
        "recipients": ["me@company.com"],
        "timestamp": datetime.now().isoformat(),
        "attachments": [],
        "thread_id": None
    }
    
    console.print("📧 [bold]Test Email Created:[/bold]")
    email_table = Table(show_header=False, box=None)
    email_table.add_row("From:", f"[blue]{test_email['sender']}[/blue]")
    email_table.add_row("Subject:", f"[green]{test_email['subject']}[/green]")
    email_table.add_row("Body:", f"{test_email['body'][:80]}..." if len(test_email['body']) > 80 else test_email['body'])
    console.print(email_table)
    console.print()
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            # Create thread
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task("Creating workflow thread...", total=None)
                
                thread_response = await client.post(f"{LANGGRAPH_API}/threads", json={})
                
                if thread_response.status_code != 200:
                    console.print(f"[red]❌ Failed to create thread: {thread_response.status_code}[/red]")
                    console.print(f"Response: {thread_response.text}")
                    return
                    
                thread_data = thread_response.json()
                thread_id = thread_data["thread_id"]
                progress.update(task, description=f"Created thread: {thread_id}")
                
                # Start workflow
                progress.update(task, description="Starting email workflow...")
                
                run_response = await client.post(
                    f"{LANGGRAPH_API}/threads/{thread_id}/runs",
                    json={
                        "assistant_id": "agent",
                        "input": {
                            "email": test_email,
                            "messages": []
                        }
                    }
                )
                
                if run_response.status_code != 200:
                    console.print(f"[red]❌ Failed to start workflow: {run_response.status_code}[/red]")
                    console.print(f"Response: {run_response.text}")
                    return
                    
                run_data = run_response.json()
                run_id = run_data["run_id"]
                progress.update(task, description=f"Started workflow: {run_id}")
            
            console.print(f"✅ [green]Workflow started successfully![/green]")
            console.print(f"   Thread ID: [bold]{thread_id}[/bold]")
            console.print(f"   Run ID: [bold]{run_id}[/bold]")
            console.print()
            
            if wait:
                console.print("⏳ Waiting for workflow to reach human review interrupt...")
                
                for attempt in range(12):  # Wait up to 36 seconds
                    await asyncio.sleep(3)
                    
                    status_response = await client.get(f"{LANGGRAPH_API}/threads/{thread_id}")
                    
                    if status_response.status_code == 200:
                        status_data = status_response.json()
                        thread_status = status_data.get("status", "unknown")
                        
                        console.print(f"   📊 Status check {attempt + 1}: {thread_status}")
                        
                        if thread_status == "interrupted":
                            console.print(f"   ✅ [green]Thread interrupted! Ready for human review.[/green]")
                            break
                            
                        if thread_status in ["success", "error"]:
                            console.print(f"   ⚠️  Workflow completed without interrupt: {thread_status}")
                            break
                else:
                    console.print("   ⏰ Timeout waiting for interrupt (workflow may still be running)")
            
            console.print()
            console.print("🎯 [bold blue]Next Steps:[/bold blue]")
            console.print(f"1. Open Agent Inbox: [link]{AGENT_INBOX_UI}[/link]")
            console.print(f"2. Look for Thread ID: [bold]{thread_id}[/bold]")
            console.print("3. Test the human-in-the-loop workflow:")
            console.print("   • Click 'Accept' to approve the draft")
            console.print("   • Click 'Respond to assistant' to provide feedback")
            console.print("   • Test the feedback refinement loop")
            
        except Exception as e:
            console.print(f"[red]❌ Error running workflow: {e}[/red]")


@app.command()
def gmail(
    count: int = typer.Option(1, "--count", "-c", help="Number of emails to fetch"),
    process: bool = typer.Option(True, "--process/--no-process", help="Send email to workflow for processing"),
    show_body: bool = typer.Option(True, "--show-body/--no-body", help="Display email body content")
):
    """
    📧 Fetch latest Gmail email(s) and trigger workflow
    
    Retrieves the most recent email(s) from your Gmail inbox and automatically sends them to the
    LangGraph workflow for processing. The processed email will appear in Agent Inbox for review.
    """
    console.print(Panel.fit(
        "📧 [bold blue]Gmail Email Fetcher[/bold blue]",
        subtitle="Retrieve latest emails from Gmail"
    ))
    
    ensure_venv()
    
    try:
        # Import Gmail utilities
        from src.utils.google_auth import GoogleAuthHelper
        from googleapiclient.discovery import build
        
        console.print("🔐 Authenticating with Gmail...")
        
        # Gmail API scopes
        scopes = [
            'https://www.googleapis.com/auth/gmail.readonly',
            'https://www.googleapis.com/auth/gmail.send'
        ]
        
        # Try different token files
        token_files = ['fresh_token.pickle', 'token.pickle']
        gmail_service = None
        
        for token_file in token_files:
            if os.path.exists(token_file):
                creds = GoogleAuthHelper.get_credentials(scopes, token_file)
                if creds:
                    gmail_service = build('gmail', 'v1', credentials=creds)
                    console.print(f"✅ Authenticated using {token_file}")
                    break
        
        if not gmail_service:
            console.print("[red]❌ Could not authenticate with Gmail[/red]")
            console.print("💡 Make sure you have run OAuth setup: [bold]python simple_oauth_setup.py[/bold]")
            raise typer.Exit(1)
        
        console.print(f"📬 Fetching {count} latest email(s)...")
        
        # Fetch emails
        results = gmail_service.users().messages().list(
            userId='me',
            maxResults=count,
            q='in:inbox'
        ).execute()
        
        messages = results.get('messages', [])
        
        if not messages:
            console.print("[yellow]📭 No emails found in inbox[/yellow]")
            return
        
        console.print(f"📨 Found {len(messages)} email(s)\n")
        
        fetched_emails = []
        
        for i, message in enumerate(messages, 1):
            # Get full message details
            msg = gmail_service.users().messages().get(
                userId='me', 
                id=message['id'],
                format='full'
            ).execute()
            
            # Extract email headers
            headers = {h['name']: h['value'] for h in msg['payload']['headers']}
            
            sender = headers.get('From', 'Unknown')
            subject = headers.get('Subject', 'No Subject')
            date_str = headers.get('Date', '')
            message_id = headers.get('Message-ID', None)  # Extract Gmail Message-ID for threading
            thread_id = msg.get('threadId', None)  # Extract Gmail thread ID for proper threading
            
            # Extract recipients (To, Cc, Bcc)
            recipients = []
            to_header = headers.get('To', '')
            cc_header = headers.get('Cc', '')
            bcc_header = headers.get('Bcc', '')
            
            # Parse To field
            if to_header:
                recipients.extend([addr.strip() for addr in to_header.split(',')])
            # Parse Cc field  
            if cc_header:
                recipients.extend([addr.strip() for addr in cc_header.split(',')])
            # Parse Bcc field
            if bcc_header:
                recipients.extend([addr.strip() for addr in bcc_header.split(',')])
            
            # If no recipients found, use a default (this email was sent to your inbox)
            if not recipients:
                recipients = ['info@800m.ca']  # Default to your email address
            
            # Extract body
            body = ""
            if 'parts' in msg['payload']:
                for part in msg['payload']['parts']:
                    if part['mimeType'] == 'text/plain' and 'data' in part['body']:
                        import base64
                        body_data = part['body']['data']
                        body = base64.urlsafe_b64decode(body_data).decode('utf-8')
                        break
            elif msg['payload']['mimeType'] == 'text/plain' and 'data' in msg['payload']['body']:
                import base64
                body_data = msg['payload']['body']['data']
                body = base64.urlsafe_b64decode(body_data).decode('utf-8')
            
            # Create email object (matching EmailMessage model from state.py)
            email_data = {
                'id': message['id'],
                'subject': subject,
                'body': body,
                'sender': sender,
                'recipients': recipients,  # Required field
                'timestamp': datetime.now().isoformat(),
                'attachments': [],  # Empty list for now
                'thread_id': thread_id,  # Gmail thread ID for proper threading
                'message_id': message_id,  # Gmail Message-ID for threading
            }
            
            fetched_emails.append(email_data)
            
            # Display email info
            console.print(Panel(
                f"[bold]Email #{i}[/bold]\n"
                f"📤 From: [cyan]{sender}[/cyan]\n"
                f"📋 Subject: [yellow]{subject}[/yellow]\n"
                f"📅 Date: {date_str}\n"
                f"🆔 ID: [dim]{message['id']}[/dim]",
                title=f"📧 Email {i}/{len(messages)}",
                border_style="blue"
            ))
            
            if show_body and body:
                # Show body preview (first 300 chars)
                body_preview = body[:300] + "..." if len(body) > 300 else body
                console.print(Panel(
                    Syntax(body_preview, "text", theme="monokai", line_numbers=False),
                    title="📝 Body Preview",
                    border_style="green"
                ))
            
            console.print()  # Empty line between emails
        
        # Optional: Send to workflow
        if process and fetched_emails:
            console.print("🔄 Sending latest email to workflow for processing...")
            
            latest_email = fetched_emails[0]  # Get the first (latest) email
            
            # Send to LangGraph API
            asyncio.run(_send_email_to_workflow(latest_email))
        
        # Update CLI commands file
        _update_cli_commands_with_gmail()
        
    except ImportError as e:
        console.print(f"[red]❌ Missing dependencies: {e}[/red]")
        console.print("💡 Install Google API dependencies: [bold]pip install -r requirements.txt[/bold]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]❌ Error fetching Gmail: {e}[/red]")
        raise typer.Exit(1)


async def _send_email_to_workflow(email_data):
    """Send email to LangGraph workflow for processing"""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Create thread
            thread_response = await client.post(
                f"{LANGGRAPH_API}/threads",
                json={"metadata": {"source": "gmail_cli"}}
            )
            
            if thread_response.status_code != 200:
                console.print(f"[red]❌ Failed to create thread: {thread_response.status_code}[/red]")
                console.print(f"Response: {thread_response.text}")
                return
            
            thread_data = thread_response.json()
            thread_id = thread_data["thread_id"]
            
            # Create initial state matching our AgentState structure
            initial_state = {
                "email": email_data,
                "messages": [],
                "output": [],
                "dynamic_context": {
                    "insights": [],
                    "execution_metadata": {},
                    "context_updates": {}
                },
                "long_term_memory": None,
                "status": "processing",
                "intent": None,
                "extracted_context": None,
                "draft_response": None,
                "response_metadata": {},
                "error_messages": [],
                "calendar_data": None,
                "document_data": None,
                "contact_data": None,
                "created_at": datetime.now().isoformat()
            }
            
            # Start workflow with proper state structure
            run_response = await client.post(
                f"{LANGGRAPH_API}/threads/{thread_id}/runs",
                json={
                    "assistant_id": "agent",
                    "input": initial_state,
                    "stream_mode": "values"
                }
            )
            
            if run_response.status_code != 200:
                console.print(f"[red]❌ Failed to start workflow: {run_response.status_code}[/red]")
                console.print(f"Response: {run_response.text}")
                return
            
            run_data = run_response.json()
            console.print(f"✅ Email sent to workflow!")
            console.print(f"   Thread ID: [bold]{thread_id}[/bold]")
            console.print(f"   Run ID: [bold]{run_data['run_id']}[/bold]")
            console.print(f"🎯 Check Agent Inbox at: [link]{AGENT_INBOX_UI}[/link]")
            
    except Exception as e:
        console.print(f"[red]❌ Error sending email to workflow: {e}[/red]")
        import traceback
        console.print(f"[dim]{traceback.format_exc()}[/dim]")


def _update_cli_commands_with_gmail():
    """Update CLI commands file with Gmail command examples"""
    cli_commands_path = PROJECT_ROOT / "CLI" / "cli_commands"
    
    gmail_commands = "\n# Fetch latest Gmail emails\n"
    gmail_commands += "python cli.py gmail                     # Fetch 1 latest email\n"
    gmail_commands += "python cli.py gmail --count 5           # Fetch 5 latest emails\n"
    gmail_commands += "python cli.py gmail --process           # Fetch and send to workflow\n"
    gmail_commands += "python cli.py gmail --no-body           # Fetch without showing body\n"
    
    try:
        with open(cli_commands_path, 'r') as f:
            current_content = f.read()
        
        if "# Fetch latest Gmail emails" not in current_content:
            with open(cli_commands_path, 'a') as f:
                f.write(gmail_commands)
    except Exception as e:
        console.print(f"[yellow]⚠️  Could not update CLI commands file: {e}[/yellow]")


@app.command()
def start(
    langgraph_port: int = typer.Option(2024, "--langgraph-port", help="Port for LangGraph server"),
    inbox_port: int = typer.Option(3000, "--inbox-port", help="Port for Agent Inbox UI"),
    chat_port: int = typer.Option(3001, "--chat-port", help="Port for Agent Chat UI"),
    studio: bool = typer.Option(True, "--studio/--no-studio", help="Open LangSmith Studio")
):
    """
    🚀 Start complete AI agent stack with all UIs
    
    Launches LangGraph server, Agent Inbox, Agent Chat UI, and LangSmith Studio.
    This is the one-command solution to get everything running.
    """
    console.print(Panel.fit(
        "🚀 [bold green]Starting Complete AI Agent Stack[/bold green]",
        subtitle="LangGraph + Agent Inbox + Agent Chat + LangSmith Studio"
    ))
    
    ensure_venv()
    
    try:
        # Step 1: Start LangGraph server in background
        console.print("[blue]📋 Step 1: Starting LangGraph server...[/blue]")
        
        # Kill existing LangGraph processes
        killed_langgraph = kill_processes_on_port(langgraph_port, "LangGraph")
        if not killed_langgraph:
            console.print(f"[green]✅ No existing LangGraph processes found on port {langgraph_port}[/green]")
        
        # Start LangGraph in background
        langgraph_env = os.environ.copy()
        os.chdir(PROJECT_ROOT)
        langgraph_cmd = str(VENV_PATH / "bin" / "langgraph")
        langgraph_process = subprocess.Popen(
            [langgraph_cmd, "dev", "--port", str(langgraph_port)],
            env=langgraph_env
        )
        
        console.print(f"[green]✅ LangGraph server starting on port {langgraph_port}[/green]")
        console.print("[blue]💭 Waiting for LangGraph to initialize...[/blue]")
        time.sleep(5)  # Give LangGraph time to start
        
        # Step 2: Start Agent Inbox UI
        console.print("[blue]📋 Step 2: Starting Agent Inbox UI...[/blue]")
        
        if not AGENT_INBOX_PATH.exists():
            console.print(f"[red]❌ Agent Inbox directory not found: {AGENT_INBOX_PATH}[/red]")
            langgraph_process.terminate()
            raise typer.Exit(1)
        
        # Kill existing Agent Inbox processes
        killed_inbox = kill_processes_on_port(inbox_port, "Agent Inbox")
        if not killed_inbox:
            console.print(f"[green]✅ No existing Agent Inbox processes found on port {inbox_port}[/green]")
        
        # Start Agent Inbox
        os.chdir(AGENT_INBOX_PATH)
        inbox_env = os.environ.copy()
        inbox_env['PORT'] = str(inbox_port)
        inbox_process = subprocess.Popen(["yarn", "dev"], env=inbox_env)
        
        console.print(f"[green]✅ Agent Inbox UI starting on port {inbox_port}[/green]")
        
        # Step 3: Start Agent Chat UI
        console.print("[blue]📋 Step 3: Starting Agent Chat UI...[/blue]")
        
        if not AGENT_CHAT_UI_PATH.exists():
            console.print(f"[red]❌ Agent Chat UI directory not found: {AGENT_CHAT_UI_PATH}[/red]")
            langgraph_process.terminate()
            inbox_process.terminate()
            raise typer.Exit(1)
        
        # Kill existing Agent Chat processes
        killed_chat = kill_processes_on_port(chat_port, "Agent Chat UI")
        if not killed_chat:
            console.print(f"[green]✅ No existing Agent Chat processes found on port {chat_port}[/green]")
        
        # Start Agent Chat UI
        os.chdir(AGENT_CHAT_UI_PATH)
        chat_env = os.environ.copy()
        chat_env['PORT'] = str(chat_port)
        chat_process = subprocess.Popen(["npm", "run", "dev"], env=chat_env)
        
        console.print(f"[green]✅ Agent Chat UI starting on port {chat_port}[/green]")
        console.print("[blue]💭 Waiting for all UIs to initialize...[/blue]")
        time.sleep(8)  # Give all services time to start
        
        # Step 4: Open all browser interfaces
        console.print("[blue]📋 Step 4: Opening all browser interfaces...[/blue]")
        
        langgraph_url = f"http://127.0.0.1:{langgraph_port}"
        inbox_url = f"http://localhost:{inbox_port}"
        chat_url = f"http://localhost:{chat_port}"
        
        # Open LangSmith Studio first
        if studio:
            console.print(f"[green]🎨 Opening LangSmith Studio...[/green]")
            webbrowser.open(LANGSMITH_STUDIO)
            time.sleep(1)  # Small delay between browser opens
        
        # Open Agent Chat UI
        console.print(f"[green]💬 Opening Agent Chat UI at {chat_url}[/green]")
        webbrowser.open(chat_url)
        time.sleep(1)
        
        # Open Agent Inbox UI
        console.print(f"[green]📧 Opening Agent Inbox at {inbox_url}[/green]")
        webbrowser.open(inbox_url)
        
        # Success summary
        console.print()
        console.print(Panel(
            f"[bold green]🎉 Complete AI Agent Stack Started Successfully![/bold green]\n\n"
            f"🤖 LangGraph Server: [link]{langgraph_url}[/link]\n"
            f"📧 Agent Inbox UI: [link]{inbox_url}[/link]\n"
            f"💬 Agent Chat UI: [link]{chat_url}[/link]\n"
            f"🎨 LangSmith Studio: [link]{LANGSMITH_STUDIO}[/link]\n\n"
            f"[dim]Press Ctrl+C to stop all services[/dim]",
            title="✅ All Services Running",
            border_style="green"
        ))
        
        # Wait for all processes (user will Ctrl+C to stop)
        try:
            while True:
                # Check if any process has died
                if langgraph_process.poll() is not None:
                    console.print("[red]❌ LangGraph server stopped unexpectedly[/red]")
                    break
                if inbox_process.poll() is not None:
                    console.print("[red]❌ Agent Inbox stopped unexpectedly[/red]")
                    break
                if chat_process.poll() is not None:
                    console.print("[red]❌ Agent Chat UI stopped unexpectedly[/red]")
                    break
                time.sleep(1)
        except KeyboardInterrupt:
            console.print("\n[yellow]📱 Stopping all services...[/yellow]")
            
            # Stop all processes gracefully
            langgraph_process.terminate()
            inbox_process.terminate()
            chat_process.terminate()
            
            # Wait for them to stop
            try:
                langgraph_process.wait(timeout=5)
                inbox_process.wait(timeout=5)
                chat_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                console.print("[yellow]💀 Force killing remaining processes...[/yellow]")
                langgraph_process.kill()
                inbox_process.kill()
                chat_process.kill()
            
            console.print("[green]✅ All services stopped[/green]")
        
    except subprocess.CalledProcessError as e:
        console.print(f"[red]❌ Failed to start services: {e}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]❌ Unexpected error: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def setup_oauth():
    """
    🔐 Setup Gmail OAuth authentication
    
    Runs the OAuth setup process to authenticate with Gmail.
    """
    console.print(Panel.fit(
        "🔐 [bold green]Gmail OAuth Setup[/bold green]",
        subtitle="Authenticate with Google Gmail"
    ))
    
    ensure_venv()
    
    try:
        oauth_script = PROJECT_ROOT / "simple_oauth_setup.py"
        if not oauth_script.exists():
            console.print("[red]❌ OAuth setup script not found![/red]")
            console.print(f"Expected: {oauth_script}")
            raise typer.Exit(1)
        
        console.print("🚀 Starting OAuth setup process...")
        console.print("💡 A browser window will open for Google authentication")
        console.print()
        
        # Run the OAuth setup script
        result = subprocess.run([
            sys.executable, str(oauth_script)
        ], cwd=PROJECT_ROOT, capture_output=False, text=True)
        
        if result.returncode == 0:
            console.print("\n[green]✅ OAuth setup completed successfully![/green]")
            console.print("💡 You can now run: [bold]python cli.py gmail[/bold]")
        else:
            console.print(f"\n[red]❌ OAuth setup failed with exit code: {result.returncode}[/red]")
            console.print("💡 Please check the error messages above")
            raise typer.Exit(1)
            
    except Exception as e:
        console.print(f"[red]❌ Error during OAuth setup: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def status():
    """
    📊 Check status of all services
    
    Shows the current status of LangGraph API and Agent Inbox UI.
    """
    console.print(Panel.fit(
        "📊 [bold yellow]Service Status[/bold yellow]",
        subtitle="Check running services"
    ))
    
    status_table = Table(show_header=True, header_style="bold magenta")
    status_table.add_column("Service", style="cyan", no_wrap=True)
    status_table.add_column("URL", style="blue")
    status_table.add_column("Status", justify="center")
    
    # Check LangGraph
    langgraph_status = "🟢 Running" if check_service(LANGGRAPH_API, "LangGraph") else "🔴 Stopped"
    status_table.add_row("LangGraph API", LANGGRAPH_API, langgraph_status)
    
    # Check Agent Inbox
    inbox_status = "🟢 Running" if check_service(AGENT_INBOX_UI, "Agent Inbox") else "🔴 Stopped"
    status_table.add_row("Agent Inbox UI", AGENT_INBOX_UI, inbox_status)
    
    console.print(status_table)
    console.print()
    
    if not check_service(LANGGRAPH_API, "LangGraph"):
        console.print("💡 Start everything: [bold]python cli.py start[/bold]")
    
    if not check_service(AGENT_INBOX_UI, "Agent Inbox"):
        console.print("💡 Start everything: [bold]python cli.py start[/bold]")


if __name__ == "__main__":
    app()
