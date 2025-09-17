# LangGraph Voice Interview System Documentation

## Architecture Overview

This document outlines a LangGraph-based voice interview system that uses dual ASR models, real-time conversation management, and background validation. The system follows LangGraph best practices with state management, parallel processing, and structured validation.

## System Flow

```mermaid
flowchart TD
    %% Main Conversation Flow
    START["`**START**
    Incoming call`"]
    
    INIT["`**initialize_session**
    Load questions & conversation state`"]
    
    ASK["`**ask_question**
    Present question via TTS`"]
    
    LISTEN["`**active_listening**
    VAD + Real-time ASR`"]
    
    CONV_CHECK{"`**conversation_agent**
    Speech finished? Info complete?`"}
    
    RT_VALIDATE["`**realtime_validate**
    Quick field validation`"]
    
    RT_DECIDE{"`**realtime_decision**
    Basic validation passed?`"}
    
    CLARIFY["`**ask_clarification**
    'Could you repeat?' / 'Anything else?'`"]
    
    ACCEPT["`**accept_response**
    'Got it, moving on...'`"]
    
    QUEUE_ASR["`**queue_for_processing**
    Send audio to background ASR`"]
    
    NEXT_Q{"`**check_questions**
    More questions?`"}
    
    REVIEW["`**send_review**
    Generate review link`"]
    
    END["`**END**
    Session complete`"]
    
    %% Background Processing & Validation
    BG_ASR["`**background_asr**
    High-quality transcription`"]
    
    BG_VALIDATE["`**validate_content**
    Deep content validation`"]
    
    BG_DECIDE{"`**validation_check**
    Content acceptable?`"}
    
    BG_STORE["`**store_validated**
    Save final answer`"]
    
    %% Validation Feedback Loop
    PUSH_BACK["`**push_back_to_user**
    'Let me ask that again...'`"]
    
    RETRY_COUNT{"`**retry_limit**
    Attempts < threshold?`"}
    
    %% Human Review UI Flow
    CLICK_LINK["`**user_clicks_link**
    Access review interface`"]
    
    VALIDATE_UI["`**validate_content_ui**
    Review & edit answers`"]
    
    FINAL_END["`**FINAL_END**
    Process complete`"]

    %% Main Flow
    START --> INIT
    INIT --> ASK
    ASK --> LISTEN
    LISTEN --> CONV_CHECK
    
    CONV_CHECK -->|"still speaking"| LISTEN
    CONV_CHECK -->|"needs clarification"| CLARIFY
    CONV_CHECK -->|"response complete"| RT_VALIDATE
    
    RT_VALIDATE --> RT_DECIDE
    RT_DECIDE -->|"validation failed"| CLARIFY
    RT_DECIDE -->|"validation passed"| ACCEPT
    
    CLARIFY --> LISTEN
    ACCEPT --> QUEUE_ASR
    QUEUE_ASR --> NEXT_Q
    
    NEXT_Q -->|"yes"| ASK
    NEXT_Q -->|"no"| REVIEW
    
    REVIEW --> END

    %% Background Validation Flow
    QUEUE_ASR -.->|"async"| BG_ASR
    BG_ASR --> BG_VALIDATE
    BG_VALIDATE --> BG_DECIDE
    
    %% Validation Decision Paths
    BG_DECIDE -->|"good quality"| BG_STORE
    BG_DECIDE -->|"poor quality/noise"| PUSH_BACK
    
    %% Retry Logic
    PUSH_BACK --> RETRY_COUNT
    RETRY_COUNT -->|"can retry"| ASK
    RETRY_COUNT -->|"max attempts"| REVIEW
    
    %% Final States
    BG_STORE -.->|"validated content"| NEXT_Q
    
    %% Human Review Flow
    END --> CLICK_LINK
    CLICK_LINK --> VALIDATE_UI
    VALIDATE_UI --> FINAL_END

    %% Styling
    classDef conversationNode fill:#e8f5e8,stroke:#2e7d32,stroke-width:2px
    classDef backgroundNode fill:#e3f2fd,stroke:#1565c0,stroke-width:2px
    classDef validationNode fill:#ffebee,stroke:#c62828,stroke-width:2px
    classDef decisionNode fill:#fff8e1,stroke:#ef6c00,stroke-width:2px
    classDef systemNode fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px
    classDef uiNode fill:#e8f5e8,stroke:#388e3c,stroke-width:2px
    classDef realtimeNode fill:#fff3e0,stroke:#f57c00,stroke-width:2px
    
    class INIT,ASK,LISTEN,CLARIFY,ACCEPT,QUEUE_ASR,REVIEW conversationNode
    class BG_ASR,BG_VALIDATE,BG_STORE backgroundNode
    class PUSH_BACK validationNode
    class CONV_CHECK,NEXT_Q,BG_DECIDE,RETRY_COUNT,RT_DECIDE decisionNode
    class START,END,FINAL_END systemNode
    class CLICK_LINK,VALIDATE_UI uiNode
    class RT_VALIDATE realtimeNode
```

## Technology Stack

### Models
- **OpenAI Whisper Large v3 Turbo**: Real-time ASR (809M params)
- **OpenAI Whisper Large v3**: Background ASR (1550M params)
- **GPT-4o mini**: Real-time conversation management & quick validation
- **GPT-4o**: Deep content validation
- **OpenAI TTS-1**: Speech synthesis (streaming)(choice for voice)

### Storage
- **PostgreSQL**: Session data, questions, answers
- **Redis**: Queue management, session state
- **No Vector Store Required**: Fixed question set

## Data Models (Pydantic)

```python
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Union
from enum import Enum

class QuestionType(str, Enum):
    TEXT = "text"
    BOOLEAN = "boolean"
    NUMBER = "number"
    POLICY_NUMBER = "policy_number"
    EMAIL = "email"
    PHONE = "phone"
    DATE = "date"

class ValidationLevel(str, Enum):
    REALTIME = "realtime"
    BACKGROUND = "background"

class QuestionValidationRules(BaseModel):
    field_type: QuestionType
    required: bool = True
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    pattern: Optional[str] = None
    realtime_validation: bool = True
    background_validation: bool = True

class Question(BaseModel):
    id: str
    text: str
    validation_rules: QuestionValidationRules
    realtime_prompt: str  # For GPT-4o mini
    background_prompt: str  # For GPT-4o
    max_retries: int = 3

class RealtimeValidationResult(BaseModel):
    is_valid: bool
    extracted_value: Optional[str] = None
    confidence: float
    reason: Optional[str] = None

class BackgroundValidationResult(BaseModel):
    is_valid: bool
    extracted_value: Optional[str] = None
    quality_score: float
    completeness_score: float
    confidence: float
    issues: List[str] = []

class ConversationState(BaseModel):
    session_id: str
    current_question_index: int = 0
    answers: dict = {}
    retry_counts: dict = {}
    conversation_context: List[dict] = []
    audio_buffer: Optional[bytes] = None
    real_time_transcription: str = ""
```

## Node Specifications

### 1. System Nodes

#### `START`
- **Type**: Entry Point
- **Function**: Initialize call session
- **State Updates**: Creates session_id, initializes conversation_state
- **Tools**: Call handler, session generator

```python
def start_node(state: ConversationState) -> ConversationState:
    return {
        "session_id": generate_session_id(),
        "call_started": True,
        "timestamp": datetime.now()
    }
```

#### `initialize_session`
- **Type**: Tool Node
- **Function**: Load questions and initialize conversation state
- **Tools**: Database query, state initializer
- **State Updates**: `questions`, `current_question_index`, `conversation_state`

```python
def initialize_session_node(state: ConversationState) -> ConversationState:
    questions = load_questions_from_db()
    return {
        **state,
        "questions": questions,
        "current_question_index": 0,
        "answers": {},
        "retry_counts": {}
    }
```

### 2. Conversation Flow Nodes

#### `ask_question`
- **Type**: Tool Node
- **Function**: Present current question via TTS
- **Tools**: OpenAI TTS-1 (streaming)
- **State Updates**: `question_asked`, `audio_played`

```python
async def ask_question_node(state: ConversationState) -> ConversationState:
    current_q = state["questions"][state["current_question_index"]]
    
    audio_stream = await openai_tts_stream(
        model="tts-1",
        voice="alloy",
        text=current_q.text,
        format="pcm"
    )
    
    await play_audio_stream(audio_stream)
    
    return {
        **state,
        "question_asked": current_q.text,
        "question_timestamp": datetime.now()
    }
```

#### `active_listening`
- **Type**: Tool Node
- **Function**: VAD + Real-time ASR for conversation flow
- **Tools**: VAD, OpenAI Whisper Large v3 Turbo, Audio buffer
- **State Updates**: `real_time_transcription`, `audio_buffer`, `speech_ended`

```python
async def active_listening_node(state: ConversationState) -> ConversationState:
    # VAD detection
    speech_detected = await detect_voice_activity()
    
    if speech_detected:
        audio_chunk = await capture_audio_chunk()
        
        # Real-time transcription with Whisper Turbo
        transcription = await whisper_turbo_transcribe(audio_chunk)
        
        return {
            **state,
            "real_time_transcription": state.get("real_time_transcription", "") + transcription,
            "audio_buffer": state.get("audio_buffer", b"") + audio_chunk,
            "speech_detected": True
        }
    
    return {
        **state,
        "speech_ended": True
    }
```

#### `conversation_agent`
- **Type**: LLM Agent Node
- **Function**: Determine conversation state using real-time transcription
- **Model**: GPT-4o mini
- **State Updates**: Route decision
- **LangGraph Pattern**: Conditional Edge

```python
async def conversation_agent(state: ConversationState) -> str:
    current_question = state["questions"][state["current_question_index"]]
    
    response = await gpt4o_mini.chat([
        {"role": "system", "content": """
        Analyze the conversation state. Return one of:
        - "still_speaking": User is mid-sentence or pausing
        - "needs_clarification": User seems confused or asking questions
        - "response_complete": User has finished their answer
        """},
        {"role": "user", "content": f"""
        Question: {current_question.text}
        User speech: {state['real_time_transcription']}
        Speech ended: {state.get('speech_ended', False)}
        """}
    ])
    
    return response.content.strip()
```

#### `realtime_validate` 
- **Type**: LLM Agent Node
- **Function**: Quick field validation using real-time transcription
- **Model**: GPT-4o mini
- **State Updates**: `realtime_validation_result`

```python
async def realtime_validate_node(state: ConversationState) -> ConversationState:
    current_question = state["questions"][state["current_question_index"]]
    validation_rules = current_question.validation_rules
    
    response = await gpt4o_mini.chat([
        {"role": "system", "content": current_question.realtime_prompt},
        {"role": "user", "content": f"""
        Expected field type: {validation_rules.field_type}
        User response: {state['real_time_transcription']}
        
        Extract and validate the response. Return JSON with:
        {{
            "is_valid": boolean,
            "extracted_value": "extracted value or null",
            "confidence": 0.0-1.0,
            "reason": "reason if invalid"
        }}
        """}
    ])
    
    validation_result = RealtimeValidationResult.parse_raw(response.content)
    
    return {
        **state,
        "realtime_validation_result": validation_result
    }
```

#### `realtime_decision` 
- **Type**: Decision Node
- **Function**: Route based on real-time validation
- **Logic**: Check validation result
- **LangGraph Pattern**: Conditional Edge

```python
def realtime_decision(state: ConversationState) -> str:
    validation_result = state["realtime_validation_result"]
    
    if validation_result.is_valid and validation_result.confidence > 0.7:
        return "validation_passed"
    else:
        return "validation_failed"
```

#### `ask_clarification`
- **Type**: Chain Node
- **Function**: Request clarification based on validation failure
- **Tools**: OpenAI TTS-1, Template engine
- **State Updates**: `clarification_sent`

```python
async def ask_clarification_node(state: ConversationState) -> ConversationState:
    validation_result = state.get("realtime_validation_result")
    
    if validation_result and validation_result.reason:
        clarification = f"I need to clarify: {validation_result.reason}"
    else:
        clarification = "Could you repeat that or provide more details?"
    
    await speak_text(clarification)
    
    return {
        **state,
        "clarification_sent": clarification,
        "real_time_transcription": ""  # Reset for new response
    }
```

#### `accept_response`
- **Type**: Chain Node
- **Function**: Acknowledge response and move forward
- **Tools**: OpenAI TTS-1, Template engine
- **State Updates**: `response_accepted`

```python
async def accept_response_node(state: ConversationState) -> ConversationState:
    acknowledgment = "Got it, moving on to the next question..."
    await speak_text(acknowledgment)
    
    return {
        **state,
        "response_accepted": True,
        "acceptance_timestamp": datetime.now()
    }
```

#### `queue_for_processing`
- **Type**: Tool Node
- **Function**: Queue audio for background ASR processing
- **Tools**: Redis Queue, Audio preprocessor
- **State Updates**: `queued_for_background`

```python
async def queue_for_processing_node(state: ConversationState) -> ConversationState:
    queue_item = {
        "session_id": state["session_id"],
        "question_id": state["current_question_index"],
        "audio_buffer": state["audio_buffer"],
        "real_time_transcription": state["real_time_transcription"]
    }
    
    await redis_queue.enqueue("background_asr", queue_item)
    
    return {
        **state,
        "queued_for_background": True,
        "current_question_index": state["current_question_index"] + 1
    }
```

### 3. Background Processing Nodes

#### `background_asr`
- **Type**: Tool Node (Async)
- **Function**: High-quality transcription
- **Model**: OpenAI Whisper Large v3
- **State Updates**: Background processing state

```python
async def background_asr_node(queue_item: dict) -> dict:
    high_quality_transcription = await whisper_large_v3_transcribe(
        audio=queue_item["audio_buffer"],
        model="whisper-large-v3",
        language="en"
    )
    
    return {
        **queue_item,
        "background_transcription": high_quality_transcription,
        "transcription_confidence": high_quality_transcription.confidence
    }
```

#### `validate_content` (UPDATED)
- **Type**: LLM Agent Node
- **Function**: Deep content validation with background transcription
- **Model**: GPT-4o
- **State Updates**: `background_validation_result`

```python
async def validate_content_node(queue_item: dict) -> dict:
    question = load_question_by_index(queue_item["question_id"])
    
    response = await gpt4o.chat([
        {"role": "system", "content": question.background_prompt},
        {"role": "user", "content": f"""
        Question: {question.text}
        High-quality transcription: {queue_item['background_transcription']}
        Real-time transcription: {queue_item['real_time_transcription']}
        
        Perform deep validation and return JSON with:
        {{
            "is_valid": boolean,
            "extracted_value": "final extracted value",
            "quality_score": 0.0-1.0,
            "completeness_score": 0.0-1.0,
            "confidence": 0.0-1.0,
            "issues": ["list of any issues found"]
        }}
        """}
    ])
    
    validation_result = BackgroundValidationResult.parse_raw(response.content)
    
    return {
        **queue_item,
        "background_validation_result": validation_result
    }
```

#### `validation_check`
- **Type**: Decision Node
- **Function**: Route based on background validation quality
- **Logic**: Multi-factor validation check

```python
def validation_check(queue_item: dict) -> str:
    result = queue_item["background_validation_result"]
    
    if (result.is_valid and 
        result.quality_score > 0.8 and 
        result.completeness_score > 0.7 and 
        result.confidence > 0.8):
        return "good_quality"
    else:
        return "poor_quality"
```

#### `store_validated`
- **Type**: Tool Node
- **Function**: Save validated answer to database
- **Tools**: Database connector
- **State Updates**: Database state

```python
async def store_validated_node(queue_item: dict) -> dict:
    result = queue_item["background_validation_result"]
    
    await database.store_answer(
        session_id=queue_item["session_id"],
        question_id=queue_item["question_id"],
        answer=result.extracted_value,
        transcription=queue_item["background_transcription"],
        validation_result=result,
        timestamp=datetime.now()
    )
    
    return {
        **queue_item,
        "stored_successfully": True
    }
```

### 4. LangGraph Configuration

```python
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.postgres import PostgresCheckpointer

# Initialize checkpointer for state persistence
checkpointer = PostgresCheckpointer(
    connection_string="postgresql://user:pass@localhost/langgraph"
)

# Create the graph
workflow = StateGraph(ConversationState)

# Add nodes
workflow.add_node("start", start_node)
workflow.add_node("initialize_session", initialize_session_node)
workflow.add_node("ask_question", ask_question_node)
workflow.add_node("active_listening", active_listening_node)
workflow.add_node("conversation_agent", conversation_agent)
workflow.add_node("realtime_validate", realtime_validate_node)
workflow.add_node("ask_clarification", ask_clarification_node)
workflow.add_node("accept_response", accept_response_node)
workflow.add_node("queue_for_processing", queue_for_processing_node)

# Add conditional edges
workflow.add_conditional_edges(
    "conversation_agent",
    lambda state: conversation_agent(state),
    {
        "still_speaking": "active_listening",
        "needs_clarification": "ask_clarification", 
        "response_complete": "realtime_validate"
    }
)

workflow.add_conditional_edges(
    "realtime_decision",
    realtime_decision,
    {
        "validation_passed": "accept_response",
        "validation_failed": "ask_clarification"
    }
)

# Set entry point
workflow.set_entry_point("start")

# Compile the graph
app = workflow.compile(checkpointer=checkpointer)
```

## Question Configuration Examples

```python
# Example question configurations
questions = [
    Question(
        id="full_name",
        text="What is your full name?",
        validation_rules=QuestionValidationRules(
            field_type=QuestionType.TEXT,
            required=True,
            min_length=2,
            max_length=100,
            realtime_validation=True,
            background_validation=True
        ),
        realtime_prompt="""
        Extract a person's full name from the speech.
        Look for first and last name at minimum.
        Return invalid if only first name given.
        """,
        background_prompt="""
        Validate the full name with high accuracy.
        Check for proper capitalization, common name patterns.
        Ensure both first and last names are present.
        """,
        max_retries=3
    ),
    
    Question(
        id="policy_number", 
        text="What is your policy number?",
        validation_rules=QuestionValidationRules(
            field_type=QuestionType.POLICY_NUMBER,
            required=True,
            pattern=r"^[A-Z]{2}\d{6,10}$",
            realtime_validation=True,
            background_validation=True
        ),
        realtime_prompt="""
        Extract a policy number that should be 2 letters followed by 6-10 digits.
        Example: AB1234567
        Return invalid if format doesn't match.
        """,
        background_prompt="""
        Validate policy number format precisely.
        Must be exactly 2 uppercase letters followed by 6-10 digits.
        Check against common policy number patterns.
        """
    ),
    
    Question(
        id="has_dependents",
        text="Do you have any dependents on your policy?",
        validation_rules=QuestionValidationRules(
            field_type=QuestionType.BOOLEAN,
            required=True,
            realtime_validation=True,
            background_validation=False  # Simple boolean doesn't need deep validation
        ),
        realtime_prompt="""
        Extract a yes/no answer about having dependents.
        Accept variations like "yes", "no", "yeah", "nope", etc.
        Return boolean true/false.
        """,
        background_prompt=""  # Not used for simple boolean
    )
]
```

This architecture follows LangGraph best practices with:
- **State management** using Pydantic models
- **Checkpointing** for fault tolerance
- **Conditional edges** for complex routing
- **Parallel processing** with background validation
- **Structured validation** with clear separation of concerns
- **Modular design** with focused single-responsibility nodes