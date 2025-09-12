# LangGraph Job Application Assistant - Node Specifications

```mermaid

graph TD
linkStyle default interpolate basis
    %% INITIALIZATION PHASE (One-time)
    subgraph INIT["🚀 INITIALIZATION PHASE (One-time)"]
        A[START] --> B[document_loader]
        B --> C[job_posting_analyzer]
        C --> D[cv_analyzer]
        D --> E[cv_vectorizer]
        E --> F[INITIALIZATION_COMPLETE]
    end
    
    %% CONVERSATION PHASE (Repeated)
    subgraph CONV["💬 CONVERSATION PHASE (Repeated)"]
        G[USER_INPUT] --> H[user_input_analyzer_llm]
        H --> I{orchestrator_llm}
        
        %% Main routing paths
        I -->|Generate Cover Letter| J[cover_letter_generator]
        I -->|Answer Questions| K[question_router_llm]
        I -->|Update Documents| L[document_updater]
        I -->|General Chat| K
        
        %% RAG Decision Sub-flow
        subgraph RAG["🔍 SMART RAG SUB-FLOW"]
            K --> M{rag_decision_llm}
            M -->|Needs Specific Details| N[cv_retriever]
            M -->|Analysis Sufficient| O[analysis_responder]
            
            N --> P[context_combiner]
            P --> Q[enhanced_responder]
        end
        
        %% Quality review path
        J --> R[quality_reviewer]
        O --> R
        Q --> R
        
        R --> S{Quality Check router}
        S -->|Approved| T[CONVERSATION_END]
        S -->|Needs Revision| I
        
        %% Special flows
        L --> U[TRIGGER_REINIT]
    end
    
    %% Phase connections
    F -.->|Ready for conversations| G
    U -.->|Re-run initialization| A
    T -.->|New user input| G
    
    %% Styling
    classDef initPhase fill:#e3f2fd,stroke:#1976d2,stroke-width:3px
    classDef convPhase fill:#f3e5f5,stroke:#7b1fa2,stroke-width:3px
    classDef ragPhase fill:#fff8e1,stroke:#f57f17,stroke-width:3px
    classDef startEnd fill:#e8f5e8,stroke:#388e3c,stroke-width:3px
    classDef processor fill:#fff3e0,stroke:#f57c00,stroke-width:2px
    classDef llmDecision fill:#ffebee,stroke:#d32f2f,stroke-width:3px
    classDef ragNode fill:#fff8e1,stroke:#f57f17,stroke-width:2px
    classDef vectorizer fill:#e8eaf6,stroke:#3f51b5,stroke-width:2px
    classDef trigger fill:#fce4ec,stroke:#c2185b,stroke-width:2px,stroke-dasharray: 5 5
    
    class A,F,G,T startEnd
    class B,C,D,J,R processor
    class H,I,K,M,S llmDecision
    class N,P,Q,O ragNode
    class E vectorizer
    class L,U trigger


```



# 

## State Structure

```python
class JobSearchState(MessagesState):
    job_posting: str              # Raw job posting content
    cv_content: str              # Loaded CV markdown content
    job_analysis_report: str     # Structured analysis of job requirements
    cv_analysis_report: str      # Gap analysis between CV and job
    cover_letter: str           # Generated cover letter
    qa_response: str            # Response to specific questions
    quality_review: str         # Quality assessment and feedback
    current_task: str           # Current operation: "analyze_job", "generate_cover", "answer_question"
    templates: dict             # Cover letter templates and configurations
    user_preferences: dict      # User styling and format preferences
```

## Node Specifications

### 1. Document Loader

**Purpose**: Initial data loading and validation node

**Responsibilities**:

- Load CV markdown from designated folder
- Validate job posting input from user
- Load cover letter templates and configurations
- Perform initial format validation

**Inputs**:

- User-provided job posting
- CV file path configuration

**Outputs**:

- Populated `cv_content` and `job_posting` in state
- Loaded `templates` dictionary

**Error Handling**:

- Missing CV file
- Invalid job posting format
- Template loading failures

------

### 2. Job Posting Analyzer

**Purpose**: Extract and structure job requirements

**Responsibilities**:

- Parse job requirements, skills, and qualifications
- Identify company culture and values
- Extract key responsibilities and expectations
- Determine application format requirements
- Analyze industry and role context

**Inputs**:

- `job_posting` from state

**Outputs**:

- Structured `job_analysis_report` containing:
  - Required skills (technical/soft)
  - Company information
  - Role responsibilities
  - Application requirements
  - Industry context

**LLM Prompt Focus**:

- Systematic requirement extraction
- Priority ranking of skills
- Cultural fit indicators

------

### 3. CV Analyzer

**Purpose**: Perform gap analysis between CV and job requirements

**Responsibilities**:

- Compare CV skills against job requirements
- Identify strengths and matching points
- Highlight gaps and potential concerns
- Suggest positioning strategies
- Extract relevant experience for emphasis

**Inputs**:

- `cv_content` and `job_analysis_report` from state

**Outputs**:

- Comprehensive `cv_analysis_report` containing:
  - Skills match percentage
  - Key selling points
  - Gap analysis
  - Recommended positioning
  - Experience relevance mapping

**Analysis Framework**:

- Technical skill alignment
- Experience relevance scoring
- Cultural fit assessment
- Growth potential indicators

------

### 4. Orchestrator

**Purpose**: Central coordination and task routing

**Responsibilities**:

- Determine next action based on user input
- Route to appropriate generator node
- Manage workflow state transitions
- Handle user interaction and commands
- Coordinate revision cycles

**Decision Logic**:

- **Cover Letter Generation**: Route to `cover_letter_generator`
- **Question Answering**: Route to `question_responder`
- **Analysis Update**: Loop back to analyzers
- **Quality Issues**: Coordinate revisions

**Inputs**:

- All state data
- User commands and preferences

**Outputs**:

- Updated `current_task`
- Routing decisions

------

### 5. Cover Letter Generator

**Purpose**: Create tailored cover letters

**Responsibilities**:

- Generate personalized cover letter content
- Integrate job-specific requirements
- Highlight relevant CV experiences
- Apply appropriate tone and formatting
- Customize based on company culture

**Inputs**:

- `job_analysis_report`
- `cv_analysis_report`
- `templates`
- `user_preferences`

**Outputs**:

- Complete `cover_letter` with:
  - Personalized introduction
  - Relevant experience highlights
  - Company-specific motivation
  - Professional closing
  - Proper formatting

**Generation Strategy**:

- Template-based customization
- Dynamic content insertion
- Tone adaptation
- Length optimization

------

### 6. Question Responder

**Purpose**: Handle specific application questions

**Responsibilities**:

- Process user questions about the application
- Provide specific, contextual answers
- Reference CV and job analysis
- Offer strategic advice
- Generate interview preparation content

**Inputs**:

- User question
- All analysis reports
- CV content

**Outputs**:

- Detailed `qa_response` with:
  - Direct answer to question
  - Supporting reasoning
  - Relevant examples from CV
  - Strategic recommendations

**Question Categories**:

- Salary negotiation guidance
- Interview preparation
- Application strategy
- Skill development advice

------

### 7. Quality Reviewer

**Purpose**: Final quality assurance and improvement

**Responsibilities**:

- Review all generated content for quality
- Check for consistency and accuracy
- Verify requirement alignment
- Assess professional tone and formatting
- Provide improvement recommendations

**Inputs**:

- Generated content (`cover_letter` or `qa_response`)
- All analysis reports
- Original requirements

**Outputs**:

- `quality_review` containing:
  - Quality score (1-10)
  - Specific feedback points
  - Improvement suggestions
  - Approval/revision recommendation

**Quality Criteria**:

- Content accuracy and relevance
- Professional tone and language
- Requirement coverage
- Formatting and structure
- Personalization level

------

## Error Handling & Edge Cases

### Common Error Scenarios

- **Missing Documents**: Graceful fallback to manual input
- **Invalid Job Postings**: Request clarification or reformatting
- **Analysis Failures**: Retry with simplified prompts
- **Quality Issues**: Automatic revision loop with user feedback

### Performance Considerations

- **Caching**: Store analysis results for reuse
- **Parallel Processing**: Run independent analyses concurrently
- **Token Management**: Optimize prompt lengths for cost efficiency
- **Rate Limiting**: Handle API limitations gracefully

## Configuration Options

### User Preferences

```python
user_preferences = {
    "cover_letter_length": "medium",  # short, medium, long
    "tone": "professional",           # casual, professional, enthusiastic
    "format": "traditional",          # modern, traditional, creative
    "language": "french",            # english, french, bilingual
    "export_format": "markdown"      # markdown, pdf, docx
}
```

### Template System

- Multiple cover letter templates
- Industry-specific variations
- Customizable sections and blocks
- Dynamic content placeholders







````mermaid
flowchart LR
    %% Color Legend
     subgraph LEGEND
    LEGEND_RA["🤖 React Agent (Central Hub)"] 
    LEGEND_PN["⚙️ Processing Node"]
    LEGEND_LD["🧠 LLM Decision Point"]
    LEGEND_SO["💾 Storage Operation"]
    LEGEND_EP["🎯 End Point"]
    LEGEND_SN["🔍 Specialized Node"]
    end
    
    %% Title
    subgraph TITLE["🎯 COMPLETE JOB SEARCH AGENT - LANGGRAPH ARCHITECTURE"]
    end
    
     %% Styling
    
    classDef reactAgent fill:#e8f5e8,stroke:#2e7d32,stroke-width:3px
    classDef processingNode fill:#e3f2fd,stroke:#1976d2,stroke-width:2px
    classDef llmDecision fill:#fff3e0,stroke:#f57c00,stroke-width:3px
    classDef storageOp fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px
    classDef endPoint fill:#ffebee,stroke:#d32f2f,stroke-width:3px
    classDef specializedNode fill:#f1f8e9,stroke:#689f38,stroke-width:1px,stroke-dasharray: 3 3
    classDef title fill:#f5f5f5,stroke:#666666,stroke-width:3px
    
    class AGENT reactAgent
    class DOCPROC,RAGINDEX,QUALITY processingNode
    class ROUTE1,ROUTE2,ROUTE3,ROUTE4 llmDecision
    class STORE storageOp
    class START,END1,END2,END3 endPoint
    class TITLE title
    
    %% Apply colors to legend
    class LEGEND_RA reactAgent
    class LEGEND_PN processingNode
    class LEGEND_LD llmDecision
    class LEGEND_SO storageOp
    class LEGEND_EP endPoint
    class LEGEND_SN specializedNode
````



````mermaid
flowchart TD
    linkStyle default interpolate basis
     %% Main Graph Flow
    START[🚀 START] --> AGENT[🤖 React Agent<br/>📍 agent_node<br/>Tools: upload_cv, upload_job_posting,<br/>generate_cover_letter, search_cv_details]
    
    AGENT --> ROUTE1{🧠 route_after_agent<br/>📍 router.py<br/>LLM Decision}
    
    ROUTE1 -->|Documents Need Processing| DOCPROC[⚙️ Document Processor<br/>📍 document_processor_node<br/>🧠 LLM: Analyze CV + Job Posting]
    ROUTE1 -->|User Request Ready| ROUTE2{🧠 assess_user_intent<br/>📍 router.py<br/>LLM Decision}
    ROUTE1 -->|Conversation Complete| END1[🎯 END]
    
    DOCPROC --> ROUTE3{🧠 should_trigger_rag<br/>📍 router.py<br/>LLM Decision}
    
    ROUTE3 -->|CV Needs Indexing| RAGINDEX[💾 RAG Indexer<br/>📍 rag_indexer_node<br/>Create Vector Store]
    ROUTE3 -->|Skip Indexing| AGENT
    
    RAGINDEX --> STORE[💾 Storage Update<br/>📍 storage.py<br/>Save Index Status]
    STORE --> AGENT
    
    %% Intent-based routing to specialized processing
    ROUTE2 -->|Generate Cover Letter| COVERGEN[🔍 Cover Letter Generator<br/>📍 cover_letter_generator_node<br/>🧠 LLM: Generate Tailored Content]
    ROUTE2 -->|Answer Question| QROUTE{🧠 should_trigger_rag<br/>📍 router.py<br/>LLM: Needs Specific Details?}
    ROUTE2 -->|Improve Content| IMPROVE[🔍 Content Improver<br/>📍 content_improver_node<br/>🧠 LLM: Apply Feedback]
    ROUTE2 -->|Continue Chat| AGENT
    
    %% Question Answering Flow
    QROUTE -->|Needs RAG| RAGSEARCH[🔍 RAG Search<br/>📍 rag_search_node<br/>Semantic CV Search]
    QROUTE -->|Use Analysis Only| QANSWER[🔍 Question Answerer<br/>📍 question_answerer_node<br/>🧠 LLM: Strategic Response]
    
    RAGSEARCH --> RAGCOMBINE[🔍 RAG Context Combiner<br/>📍 rag_combiner_node<br/>🧠 LLM: Combine Details + Analysis]
    RAGCOMBINE --> QANSWER
    
    %% All specialized nodes go to quality review
    COVERGEN --> QUALITY[⚙️ Quality Reviewer<br/>📍 quality_reviewer_node<br/>🧠 LLM: Contextual Quality Check]
    QANSWER --> QUALITY
    IMPROVE --> QUALITY
    
    QUALITY --> ROUTE4{🧠 validate_completion_readiness<br/>📍 router.py<br/>LLM Decision}
    
    ROUTE4 -->|Quality Approved| END2[🎯 SUCCESS:<br/>Task Complete]
    ROUTE4 -->|Needs Improvement| AGENT
    ROUTE4 -->|User Feedback| AGENT
    
    %% User Flow Support Indicators
    AGENT -.->|Flow 1: Happy Path| ROUTE2
    AGENT -.->|Flow 2: First-Time Setup| ROUTE1
    AGENT -.->|Flow 3: Iterative| IMPROVE
    AGENT -.->|Flow 4: Complex Requirements| QROUTE
    AGENT -.->|Flow 5: Returning User| COVERGEN
    
    %% Styling
    classDef reactAgent fill:#e8f5e8,stroke:#2e7d32,stroke-width:3px
    classDef processingNode fill:#e3f2fd,stroke:#1976d2,stroke-width:2px
    classDef llmDecision fill:#fff3e0,stroke:#f57c00,stroke-width:3px
    classDef specializedNode fill:#f1f8e9,stroke:#689f38,stroke-width:1px,stroke-dasharray: 3 3
    classDef storageOp fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px
    classDef endPoint fill:#ffebee,stroke:#d32f2f,stroke-width:3px
    classDef title fill:#f5f5f5,stroke:#666666,stroke-width:3px
    
    class AGENT reactAgent
    class DOCPROC,RAGINDEX,QUALITY processingNode
    class ROUTE1,ROUTE2,ROUTE3,ROUTE4,QROUTE llmDecision
    class COVERGEN,QANSWER,IMPROVE,RAGSEARCH,RAGCOMBINE specializedNode
    class STORE storageOp
    class START,END1,END2 endPoint
    class TITLE title
    
    %% Apply colors to legend
    class LEGEND_RA reactAgent
    class LEGEND_PN processingNode
    class LEGEND_LD llmDecision
    class LEGEND_SN specializedNode
    class LEGEND_SO storageOp
    class LEGEND_EP endPoint
````

