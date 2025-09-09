# Userflows

## 🎯 USER FLOW 1: HAPPY PATH - SIMPLE COVER LETTER GENERATION
````mermaid
flowchart LR
%% Legend 
    subgraph LEGEND["Legend"]
    LEGEND_UA["👤 User Action"] 
    LEGEND_RA["🏢 Recruiter Action"]
    LEGEND_SN["🤖 System Node"]
    LEGEND_DP["🔀 Decision Point"] 
    LEGEND_EP["🎯 End Point"]
    LEGEND_RD["🔄 Redirect"]
    end
    
    %% Title 
    subgraph TITLE["🎯 USER FLOW 1: HAPPY PATH - SIMPLE COVER LETTER GENERATION"]
    end
    
    %% Styling
    classDef userAction fill:#e8f5e8,stroke:#2e7d32,stroke-width:2px
    classDef recruiterAction fill:#fff3e0,stroke:#f57c00,stroke-width:2px
    classDef systemNode fill:#e3f2fd,stroke:#1976d2,stroke-width:2px
    classDef decision fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px
    classDef endpoint fill:#ffebee,stroke:#d32f2f,stroke-width:3px
    classDef clarification fill:#f1f8e9,stroke:#689f38,stroke-width:2px
    classDef ragProcess fill:#fff8e1,stroke:#f57f17,stroke-width:2px
    classDef validation fill:#e8eaf6,stroke:#3f51b5,stroke-width:2px
    classDef title fill:#f5f5f5,stroke:#666666,stroke-width:3px
    classDef phase fill:#f9f9f9,stroke:#888888,stroke-width:1px
    class TITLE title
   
    
    %% Apply colors to legend items
    class LEGEND_UA userAction
    class LEGEND_RA recruiterAction
    class LEGEND_SN systemNode
    class LEGEND_DP decision
    class LEGEND_EP endpoint
    class LEGEND_CL clarification
    class LEGEND_RG ragProcess
    class LEGEND_VL validation
````
````mermaid
flowchart LR
    
    %% Main Flow
    subgraph FLOW
       direction LR
    A[👤 User Opens App] --> B{🤖 Session Already Initialized?<br/>📍 session_manager}
    B -->|✅ Yes| C[👤 User: 'Generate cover letter']
    B -->|❌ No| D[🔄 Redirect to Setup Flow]
    
    C --> E[🤖 Analyze Intent<br/>📍 user_input_analyzer_llm]
    E --> F[🤖 Route Decision<br/>📍 orchestrator_llm]
    F --> G[🤖 Generate Cover Letter<br/>📍 cover_letter_generator]
    G --> H[🤖 Quality Review<br/>📍 quality_reviewer]
    
    H --> I{🤖 Quality Score ≥ 8?<br/>📍 quality_reviewer}
    I -->|✅ Yes| J[🤖 Present Cover Letter<br/>📍 response_formatter]
    I -->|❌ No| K[🤖 Auto-Improve<br/>📍 auto_improver]
    K -.-> G
    
    J --> L[👤 User Reviews Result]
    L --> M{👤 User Satisfied?}
    M -->|✅ Yes| N[👤 User: Download/Copy<br/>📍 export_handler]
    M -->|❌ No| O[👤 User: Request Changes]
    
    O -.-> P[🤖 Analyze Feedback<br/>📍 feedback_analyzer]
    P -.-> Q[🤖 Regenerate with Feedback<br/>📍 cover_letter_generator]
    Q -.-> H
    
    N --> R[🎯 Success: Cover Letter Complete]
    D -.-> S[🔄 Redirect to Flow 2]
   end
    
   
    
    %% Styling
    classDef userAction fill:#e8f5e8,stroke:#2e7d32,stroke-width:2px
    classDef recruiterAction fill:#fff3e0,stroke:#f57c00,stroke-width:2px
    classDef systemNode fill:#e3f2fd,stroke:#1976d2,stroke-width:2px
    classDef decision fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px
    classDef endpoint fill:#ffebee,stroke:#d32f2f,stroke-width:3px
    classDef redirect fill:#e8eaf6,stroke:#3f51b5,stroke-width:2px
    classDef title fill:#f5f5f5,stroke:#666666,stroke-width:3px
    
    class A,C,L,N,O userAction
    class E,F,G,H,J,K,P,Q systemNode
    class B,I,M decision
    class R endpoint
    class D,S redirect
    class TITLE title
    
    %% Apply colors to legend items
    class LEGEND_UA userAction
    class LEGEND_RA recruiterAction
    class LEGEND_SN systemNode
    class LEGEND_DP decision
    class LEGEND_EP endpoint
    class LEGEND_RD redirect
````
## 🎯 USER FLOW 2: FIRST-TIME USER - COMPLETE SETUP FLOW
````mermaid
flowchart LR
%% Legend 
    subgraph LEGEND["Legend"]
    LEGEND_UA["👤 User Action"] 
    LEGEND_RA["🏢 Recruiter Action"]
    LEGEND_SN["🤖 System Node"]
    LEGEND_DP["🔀 Decision Point"] 
    LEGEND_EP["🎯 End Point"]
    LEGEND_ER["⚠️ Error State"]
    LEGEND_UI["📝 User Input"]
    end
    
    %% Title 
    subgraph TITLE["🎯 USER FLOW 2: FIRST-TIME USER - COMPLETE SETUP FLOW"]
    end
    
    %% Styling
    classDef userAction fill:#e8f5e8,stroke:#2e7d32,stroke-width:2px
    classDef recruiterAction fill:#fff3e0,stroke:#f57c00,stroke-width:2px
    classDef systemNode fill:#e3f2fd,stroke:#1976d2,stroke-width:2px
    classDef decision fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px
    classDef endpoint fill:#ffebee,stroke:#d32f2f,stroke-width:3px
    classDef clarification fill:#f1f8e9,stroke:#689f38,stroke-width:2px
    classDef ragProcess fill:#fff8e1,stroke:#f57f17,stroke-width:2px
    classDef validation fill:#e8eaf6,stroke:#3f51b5,stroke-width:2px
    classDef title fill:#f5f5f5,stroke:#666666,stroke-width:3px
    classDef phase fill:#f9f9f9,stroke:#888888,stroke-width:1px
    class TITLE title
   
    
    %% Apply colors to legend items
    class LEGEND_UA userAction
    class LEGEND_RA recruiterAction
    class LEGEND_SN systemNode
    class LEGEND_DP decision
    class LEGEND_EP endpoint
    class LEGEND_CL clarification
    class LEGEND_RG ragProcess
    class LEGEND_VL validation
````
````mermaid
flowchart LR
    
    %% Main Flow - line 1
    subgraph FLOW - line 1
       direction LR
    A[👤 New User Opens App] --> B[🤖 Welcome Screen<br/>📍 onboarding_controller]
    B --> C[👤 User: Upload CV<br/>📍 file_upload_handler]
    C --> D{🤖 CV Valid?<br/>📍 document_validator}
    D -->|❌ No| E[⚠️ Show Error + Tips<br/>📍 error_handler]
    E -.-> C
    D -->|✅ Yes| F[👤 User: Paste Job Posting<br/>🏢 From Recruiter/Job Board]
    
    F --> G{🤖 Job Posting Valid?<br/>📍 job_posting_validator}
    G -->|❌ No| H[⚠️ Show Error + Examples<br/>📍 error_handler]
    H -.-> F
    G -->|✅ Yes| I[👤 User: Set Preferences<br/>📍 preference_manager]
    
    I --> J[📝 Cover Letter Length?<br/>📍 preference_collector]
    J --> K[📝 Tone Preference?<br/>📍 preference_collector]
    K --> L[📝 Language Choice?<br/>📍 preference_collector]
    L --> M[👤 User: Start Analysis]
    end
    
   
    
    %% Styling
    classDef userAction fill:#e8f5e8,stroke:#2e7d32,stroke-width:2px
    classDef recruiterAction fill:#fff3e0,stroke:#f57c00,stroke-width:2px
    classDef systemNode fill:#e3f2fd,stroke:#1976d2,stroke-width:2px
    classDef decision fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px
    classDef endpoint fill:#ffebee,stroke:#d32f2f,stroke-width:3px
    classDef errorState fill:#ffcdd2,stroke:#c62828,stroke-width:2px
    classDef userInput fill:#f1f8e9,stroke:#689f38,stroke-width:2px
    classDef title fill:#f5f5f5,stroke:#666666,stroke-width:3px
    
    class A,C,I,M,W,U userAction
    class F recruiterAction
    class B,N,O,P,Q,R,V,X,Y systemNode
    class D,G,S decision
    class Z endpoint
    class E,H,T errorState
    class J,K,L userInput
    class TITLE title
    
    %% Apply colors to legend items
    class LEGEND_UA userAction
    class LEGEND_RA recruiterAction
    class LEGEND_SN systemNode
    class LEGEND_DP decision
    class LEGEND_EP endpoint
    class LEGEND_ER errorState
    class LEGEND_UI userInput
````
````mermaid

flowchart LR
%% Main Flow - line 2
    subgraph FLOW - line 2
       direction LR
    M[👤 User: Start Analysis] --> N[🤖 Initialize Session<br/>📍 session_initializer]
    N --> O[🤖 Load Documents<br/>📍 document_loader]
    O --> P[🤖 Analyze Job Posting<br/>📍 job_posting_analyzer]
    P --> Q[🤖 Analyze CV Fit<br/>📍 cv_analyzer]
    Q --> R[🤖 Create Vector Index<br/>📍 cv_vectorizer]
    
    R --> S{🤖 Analysis Successful?<br/>📍 initialization_validator}
    S -->|❌ No| T[⚠️ Show Error + Support<br/>📍 error_handler]
    T --> U[👤 User: Retry or Contact Support]
    U -.-> M
    S -->|✅ Yes| V[🤖 Show Setup Complete<br/>📍 success_notifier]
    
    V --> W[👤 User: Generate First Cover Letter]
    W --> X[🤖 Generate Cover Letter<br/>📍 cover_letter_generator]
    X --> Y[🤖 Present Results<br/>📍 response_formatter]
    Y --> Z[🎯 Success: Ready for Conversations]
    end
    
   
    
    %% Styling
    classDef userAction fill:#e8f5e8,stroke:#2e7d32,stroke-width:2px
    classDef recruiterAction fill:#fff3e0,stroke:#f57c00,stroke-width:2px
    classDef systemNode fill:#e3f2fd,stroke:#1976d2,stroke-width:2px
    classDef decision fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px
    classDef endpoint fill:#ffebee,stroke:#d32f2f,stroke-width:3px
    classDef errorState fill:#ffcdd2,stroke:#c62828,stroke-width:2px
    classDef userInput fill:#f1f8e9,stroke:#689f38,stroke-width:2px
    classDef title fill:#f5f5f5,stroke:#666666,stroke-width:3px
    
    class A,C,I,M,W,U userAction
    class F recruiterAction
    class B,N,O,P,Q,R,V,X,Y systemNode
    class D,G,S decision
    class Z endpoint
    class E,H,T errorState
    class J,K,L userInput
    class TITLE title
    
    %% Apply colors to legend items
    class LEGEND_UA userAction
    class LEGEND_RA recruiterAction
    class LEGEND_SN systemNode
    class LEGEND_DP decision
    class LEGEND_EP endpoint
    class LEGEND_ER errorState
    class LEGEND_UI userInput
````
## 🎯 USER FLOW 3: ITERATIVE REFINEMENT - COVER LETTER MODIFICATIONS

````mermaid
flowchart LR
%% Legend 
    subgraph LEGEND["Legend"]
    LEGEND_UA["👤 User Action"] 
    LEGEND_RA["🏢 Recruiter Feedback"]
    LEGEND_SN["🤖 System Node"]
    LEGEND_DP["🔀 Decision Point"] 
    LEGEND_EP["🎯 End Point"]
    LEGEND_RG["🔍 RAG Process"]
    LEGEND_VS["📊 Version Control"]
    LEGEND_FT["📝 Feedback Type"]
    end
    
    %% Title 
    subgraph TITLE["🎯 USER FLOW 3: ITERATIVE REFINEMENT - COVER LETTER MODIFICATIONS"]
    end
    
    %% Styling
    classDef userAction fill:#e8f5e8,stroke:#2e7d32,stroke-width:2px
    classDef recruiterAction fill:#fff3e0,stroke:#f57c00,stroke-width:2px
    classDef systemNode fill:#e3f2fd,stroke:#1976d2,stroke-width:2px
    classDef decision fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px
    classDef endpoint fill:#ffebee,stroke:#d32f2f,stroke-width:3px
    classDef clarification fill:#f1f8e9,stroke:#689f38,stroke-width:2px
    classDef ragProcess fill:#fff8e1,stroke:#f57f17,stroke-width:2px
    classDef validation fill:#e8eaf6,stroke:#3f51b5,stroke-width:2px
    classDef title fill:#f5f5f5,stroke:#666666,stroke-width:3px
    classDef phase fill:#f9f9f9,stroke:#888888,stroke-width:1px
    class TITLE title
   
    
    %% Apply colors to legend items
    class LEGEND_UA userAction
    class LEGEND_RA recruiterAction
    class LEGEND_SN systemNode
    class LEGEND_DP decision
    class LEGEND_EP endpoint
    class LEGEND_CL clarification
    class LEGEND_RG ragProcess
    class LEGEND_VL validation
````

````mermaid
flowchart TD

    %% Main Flow - line 1
    subgraph FLOW - line 1
       direction LR
    A[👤 User Has Initial Cover Letter] --> B[👤 User Reviews Content]
    B --> C{👤 Satisfied with Result?}
    C -->|✅ Yes| D[👤 User: Download/Use<br/>📍 export_handler]
    C -->|❌ No| E[👤 User: Provide Feedback<br/>🏢 May Include Recruiter Input]
    
    E --> F[🤖 Classify Feedback Type<br/>📍 feedback_classifier]
    F --> G[📝 Make it Shorter<br/>📍 length_optimizer]
    F --> H[📝 Change Tone<br/>📍 tone_adjuster]
    F --> I[📝 Add Specific Details<br/>📍 detail_enhancer]
    F --> J[📝 Different Focus<br/>📍 focus_shifter]
    F --> K[📝 Other Changes<br/>📍 custom_modifier]
    
    G --> L[🤖 Analyze Request<br/>📍 request_analyzer]
    H --> L
    I --> L
    J --> L
    K --> L
    
    L --> M[🤖 Check if RAG Needed<br/>📍 rag_decision_llm]
    M --> N{🔍 Need Specific CV Details?<br/>📍 rag_decision_llm}
    N -->|✅ Yes| O[🔍 RAG Retrieval<br/>📍 cv_retriever]
    N -->|❌ No| P[🤖 Use Analysis Only<br/>📍 analysis_responder]
    O --> Q[🔍 Enhanced Response<br/>📍 enhanced_responder]
    P --> Q
    end
    
    %% Main Flow - line 2
    subgraph FLOW - line 2
       direction LR
    Q --> R[🤖 Regenerate Content<br/>📍 cover_letter_generator]
    R --> S[🤖 Quality Review<br/>📍 quality_reviewer]
    S --> T{🤖 Quality Acceptable?<br/>📍 quality_validator}
    T -->|❌ No| U[🤖 Auto-Improve<br/>📍 auto_improver]
    U -.-> R
    T -->|✅ Yes| V[🤖 Present Revised Version<br/>📍 response_formatter]
    
    V --> W[👤 User: Compare Versions<br/>📍 version_comparator]
    W --> X{👤 Prefer New Version?}
    X -->|✅ Yes| Y[📊 Save as Current<br/>📍 version_manager]
    X -->|❌ No| Z[📊 Keep Previous<br/>📍 version_manager]
    X -->|🤝 Both| AA[📊 Save Both Versions<br/>📍 version_manager]
    
    Y --> BB{👤 Want More Changes?}
    Z --> BB
    AA --> BB
    BB -->|✅ Yes| CC[👤 Provide More Feedback]
    CC -.-> E
    BB -->|❌ No| DD[👤 User: Finalize Choice<br/>📍 finalization_handler]
    DD --> EE[🎯 Success: Cover Letter Refined]
    D --> EE
    end
  
    
    %% Styling
    classDef userAction fill:#e8f5e8,stroke:#2e7d32,stroke-width:2px
    classDef recruiterAction fill:#fff3e0,stroke:#f57c00,stroke-width:2px
    classDef systemNode fill:#e3f2fd,stroke:#1976d2,stroke-width:2px
    classDef decision fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px
    classDef endpoint fill:#ffebee,stroke:#d32f2f,stroke-width:3px
    classDef ragProcess fill:#fff8e1,stroke:#f57f17,stroke-width:2px
    classDef versionControl fill:#e8eaf6,stroke:#3f51b5,stroke-width:2px
    classDef feedbackType fill:#f1f8e9,stroke:#689f38,stroke-width:2px
    classDef title fill:#f5f5f5,stroke:#666666,stroke-width:3px
    
    class A,B,W,DD,D,CC userAction
    class E recruiterAction
    class F,L,M,R,S,U,V systemNode
    class C,N,T,X,BB decision
    class EE endpoint
    class O,Q ragProcess
    class Y,Z,AA versionControl
    class G,H,I,J,K feedbackType
    class TITLE title
    
    %% Apply colors to legend items
    class LEGEND_UA userAction
    class LEGEND_RA recruiterAction
    class LEGEND_SN systemNode
    class LEGEND_DP decision
    class LEGEND_EP endpoint
    class LEGEND_RG ragProcess
    class LEGEND_VS versionControl
    class LEGEND_FT feedbackType
````
## 🎯 USER FLOW 4: COMPLEX REQUIREMENTS - CLARIFICATION & CUSTOM GENERATION

````mermaid
flowchart LR
%% Legend
    subgraph LEGEND["🎨 COLOR LEGEND"]
        LEGEND_UA["👤 User Action"] 
        LEGEND_RA["🏢 Recruiter Requirements"]
        LEGEND_SN["🤖 System Node"]
        LEGEND_DP["🔀 Decision Point"] 
        LEGEND_EP["🎯 End Point"]
        LEGEND_CL["💭 Clarification Process"]
        LEGEND_RG["🔍 RAG Enhancement"]
        LEGEND_VL["✅ Validation Process"]
    end
    
    %% Title 
    subgraph TITLE["🎯 USER FLOW 4: COMPLEX REQUIREMENTS - CLARIFICATION & CUSTOM GENERATION"]
    end
    
    %% Styling
    classDef userAction fill:#e8f5e8,stroke:#2e7d32,stroke-width:2px
    classDef recruiterAction fill:#fff3e0,stroke:#f57c00,stroke-width:2px
    classDef systemNode fill:#e3f2fd,stroke:#1976d2,stroke-width:2px
    classDef decision fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px
    classDef endpoint fill:#ffebee,stroke:#d32f2f,stroke-width:3px
    classDef clarification fill:#f1f8e9,stroke:#689f38,stroke-width:2px
    classDef ragProcess fill:#fff8e1,stroke:#f57f17,stroke-width:2px
    classDef validation fill:#e8eaf6,stroke:#3f51b5,stroke-width:2px
    classDef title fill:#f5f5f5,stroke:#666666,stroke-width:3px
    classDef phase fill:#f9f9f9,stroke:#888888,stroke-width:1px
    class TITLE title
   
    
    %% Apply colors to legend items
    class LEGEND_UA userAction
    class LEGEND_RA recruiterAction
    class LEGEND_SN systemNode
    class LEGEND_DP decision
    class LEGEND_EP endpoint
    class LEGEND_CL clarification
    class LEGEND_RG ragProcess
    class LEGEND_VL validation
````

````mermaid
flowchart LR
    
    
    %% First Line - Request Analysis & Validation
    subgraph LINE1["📋 PHASE 1: REQUEST ANALYSIS & VALIDATION"]
        direction LR
        A[👤 User: Complex Cover Letter Request<br/>🏢 May Include Recruiter Specs] --> B[🤖 Analyze Request<br/>📍 user_input_analyzer_llm]
        B --> C{🤖 Request Clear & Complete?<br/>📍 request_validator}
        C -->|✅ Yes| D[🤖 Route to Generation<br/>📍 orchestrator_llm]
        C -->|❌ No| E[🤖 Identify Missing Info<br/>📍 gap_analyzer]
        
        E --> F[💭 Ask Clarifying Questions<br/>📍 clarification_generator]
        F --> G[👤 User: Provide Additional Info<br/>🏢 May Consult Recruiter]
        G --> H[🤖 Validate Requirements<br/>📍 requirement_validator]
        H --> I{🤖 All Requirements Clear?<br/>📍 requirement_validator}
        I -->|❌ No| J[💭 Ask Follow-up Questions<br/>📍 clarification_generator]
        J -.-> G
        I -->|✅ Yes| K[✅ Validate Feasibility<br/>📍 feasibility_checker]
        
        K --> L{🤖 Requirements Achievable?<br/>📍 feasibility_validator}
        L -->|❌ No| M[🤖 Suggest Alternatives<br/>📍 alternative_generator]
        M --> N[👤 User: Accept or Modify<br/>🏢 May Need Recruiter Approval]
        N --> O{👤 User Decision?}
        O -->|🔄 Modify| P[👤 User: Adjust Requirements]
        P -.-> K
        O -->|✅ Accept| Q[🤖 Proceed with Alternative<br/>📍 requirement_adapter]
        
        L -->|✅ Yes| R[🤖 Check Special Needs<br/>📍 requirement_analyzer]
        Q --> R
        D --> R
        R --> CONNECTOR[⬇️ PROCEED TO GENERATION]
        
    end
 
  
    
    %% Styling
    classDef userAction fill:#e8f5e8,stroke:#2e7d32,stroke-width:2px
    classDef recruiterAction fill:#fff3e0,stroke:#f57c00,stroke-width:2px
    classDef systemNode fill:#e3f2fd,stroke:#1976d2,stroke-width:2px
    classDef decision fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px
    classDef endpoint fill:#ffebee,stroke:#d32f2f,stroke-width:3px
    classDef clarification fill:#f1f8e9,stroke:#689f38,stroke-width:2px
    classDef ragProcess fill:#fff8e1,stroke:#f57f17,stroke-width:2px
    classDef validation fill:#e8eaf6,stroke:#3f51b5,stroke-width:2px
    classDef title fill:#f5f5f5,stroke:#666666,stroke-width:3px
    classDef connector fill:#e1f5fe,stroke:#01579b,stroke-width:3px
    classDef phase fill:#f9f9f9,stroke:#888888,stroke-width:1px
    
    class G,N,P,DD,FF,HH,JJ userAction
    class A recruiterAction
    class B,E,H,M,Q,R,U,X,AA,BB,CC,GG,II systemNode
    class C,I,L,O,S,Z,EE decision
    class KK endpoint
    class F,J clarification
    class T,V,W ragProcess
    class K,Y validation
    class TITLE title
    class CONNECTOR connector
    class LINE1,LINE2 phase
    
    %% Apply colors to legend items
    class LEGEND_UA userAction
    class LEGEND_RA recruiterAction
    class LEGEND_SN systemNode
    class LEGEND_DP decision
    class LEGEND_EP endpoint
    class LEGEND_CL clarification
    class LEGEND_RG ragProcess
    class LEGEND_VL validation
````
````mermaid

    flowchart LR
    %% Second Line - RAG & Generation
    subgraph LINE2["🚀 PHASE 2: RAG PROCESSING & GENERATION"]
        direction LR
        CONNECTOR[⬇️ PROCEED TO GENERATION] --> S[🤖 Needs RAG Retrieval?<br/>📍 rag_decision_llm]
        S -->|✅ Yes| T[🔍 Perform RAG Search<br/>📍 cv_retriever]
        S -->|❌ No| U[🤖 Use Analysis Only<br/>📍 analysis_responder]
        T --> V[🔍 Extract Specific Details<br/>📍 detail_extractor]
        V --> W[🔍 Combine with Requirements<br/>📍 context_combiner]
        U --> W
        
        W --> X[🤖 Generate Custom Cover Letter<br/>📍 cover_letter_generator]
        X --> Y[✅ Enhanced Quality Review<br/>📍 quality_reviewer]
        Y --> Z{🤖 Meets All Requirements?<br/>📍 requirement_checker}
        Z -->|❌ No| AA[🤖 Identify Gaps<br/>📍 gap_analyzer]
        AA --> BB[🤖 Re-generate with Fixes<br/>📍 cover_letter_generator]
        BB -.-> Y
        
        Z -->|✅ Yes| CC[🤖 Present Custom Result<br/>📍 response_formatter]
        CC --> DD[👤 User: Review Against Requirements<br/>🏢 May Share with Recruiter]
        DD --> EE{👤 Meets Expectations?}
        EE -->|❌ No| FF[👤 User: Specify Issues<br/>🏢 Recruiter Feedback]
        FF --> GG[🤖 Targeted Improvements<br/>📍 improvement_analyzer]
        GG -.-> X
        
        EE -->|🤔 Partially| HH[👤 User: Request Adjustments<br/>🏢 Specific Recruiter Notes]
        HH --> II[🤖 Make Incremental Changes<br/>📍 incremental_modifier]
        II -.-> CC
        
        EE -->|✅ Yes| JJ[👤 User: Approve Final Version<br/>🏢 Recruiter Sign-off]
        JJ --> KK[🎯 Success: Custom Cover Letter Complete]
    end
    
     %% Styling
    classDef userAction fill:#e8f5e8,stroke:#2e7d32,stroke-width:2px
    classDef recruiterAction fill:#fff3e0,stroke:#f57c00,stroke-width:2px
    classDef systemNode fill:#e3f2fd,stroke:#1976d2,stroke-width:2px
    classDef decision fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px
    classDef endpoint fill:#ffebee,stroke:#d32f2f,stroke-width:3px
    classDef clarification fill:#f1f8e9,stroke:#689f38,stroke-width:2px
    classDef ragProcess fill:#fff8e1,stroke:#f57f17,stroke-width:2px
    classDef validation fill:#e8eaf6,stroke:#3f51b5,stroke-width:2px
    classDef title fill:#f5f5f5,stroke:#666666,stroke-width:3px
    classDef connector fill:#e1f5fe,stroke:#01579b,stroke-width:3px
    classDef phase fill:#f9f9f9,stroke:#888888,stroke-width:1px
    
    class G,N,P,DD,FF,HH,JJ userAction
    class A recruiterAction
    class B,E,H,M,Q,R,U,X,AA,BB,CC,GG,II systemNode
    class C,I,L,O,S,Z,EE decision
    class KK endpoint
    class F,J clarification
    class T,V,W ragProcess
    class K,Y validation
    class TITLE title
    class CONNECTOR connector
    class LINE1,LINE2 phase
    
    %% Apply colors to legend items
    class LEGEND_UA userAction
    class LEGEND_RA recruiterAction
    class LEGEND_SN systemNode
    class LEGEND_DP decision
    class LEGEND_EP endpoint
    class LEGEND_CL clarification
    class LEGEND_RG ragProcess
    class LEGEND_VL validation
````

## USER FLOW 5: 🎯 USER FLOW: RETURNING USER - QUICK COVER LETTER GENERATION

````mermaid
flowchart LR
  subgraph LEGEND["🎨 COLOR LEGEND"]
    LEGEND_UA["👤 User Action"]
    LEGEND_RA["🤖 React Agent"]
    LEGEND_SN["🤖 System Node"]
    LEGEND_DP["🔀 Decision Point"]
    LEGEND_EP["🎯 End Point"]
    LEGEND_TS["🧵 Thread State"]
  end
  subgraph TITLE["🎯 USER FLOW: RETURNING USER - QUICK COVER LETTER GENERATION"]
  end
  %% styles
  classDef userAction fill:#e8f5e8,stroke:#2e7d32,stroke-width:2px;
  classDef reactAgent fill:#f1f8e9,stroke:#689f38,stroke-width:2px;
  classDef systemNode fill:#e3f2fd,stroke:#1976d2,stroke-width:2px;
  classDef decision fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px;
  classDef endpoint fill:#ffebee,stroke:#d32f2f,stroke-width:3px;
  classDef threadState fill:#fff8e1,stroke:#f57f17,stroke-width:2px;
  classDef title fill:#f5f5f5,stroke:#666666,stroke-width:3px;
  classDef connector fill:#e1f5fe,stroke:#01579b,stroke-width:3px;
  classDef phase fill:#f9f9f9,stroke:#888888,stroke-width:1px;
  class LEGEND_UA userAction
  class LEGEND_RA reactAgent
  class LEGEND_SN systemNode
  class LEGEND_DP decision
  class LEGEND_EP endpoint
  class LEGEND_TS threadState

````
````mermaid
flowchart LR
  subgraph LINE1["📋 PHASE 1: REQUEST ANALYSIS & JOB POSTING PROCESSING"]
    direction LR
    A[👤 User: Cover letter please<br/>and this is the job offer:<br/>pasted content]
    A --> B[🤖 React Agent Receives Message<br/>📍 create_react_agent]
    B --> C[🤖 Agent Analyzes Message<br/>📍 LLM reasoning]
    C --> D{🔀 Detects Job Offer<br/>in Message?<br/>📍 content_detection}
    D -->|✅ Yes| E[🤖 Agent Calls Tool<br/>📍 upload_job_posting content]
    D -->|❌ No| F[🤖 Agent Asks for Clarification]
    F -.-> A
    E --> G[🧵 Store Job Posting in Thread<br/>📍 document_store.store_job_posting]
    G --> CONNECTOR1[⬇️ PROCEED TO CV CHECK PHASE]
  end
  %% styles
  classDef userAction fill:#e8f5e8,stroke:#2e7d32,stroke-width:2px;
  classDef reactAgent fill:#f1f8e9,stroke:#689f38,stroke-width:2px;
  classDef systemNode fill:#e3f2fd,stroke:#1976d2,stroke-width:2px;
  classDef decision fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px;
  classDef endpoint fill:#ffebee,stroke:#d32f2f,stroke-width:3px;
  classDef threadState fill:#fff8e1,stroke:#f57f17,stroke-width:2px;
  classDef title fill:#f5f5f5,stroke:#666666,stroke-width:3px;
  classDef connector fill:#e1f5fe,stroke:#01579b,stroke-width:3px;
  classDef phase fill:#f9f9f9,stroke:#888888,stroke-width:1px;
  class A userAction
  class B,C,E,F systemNode
  class D decision
  class G threadState
  class CONNECTOR1 connector
  class LINE1 phase

````

````mermaid
flowchart LR
  subgraph LINE2["🔍 PHASE 2: CV VALIDATION & DOCUMENT LOADING"]
    direction LR
    CONNECTOR1[⬇️ PROCEED TO CV CHECK PHASE] --> H[🧵 Check Thread State<br/>📍 JobSearchState.cv_content]
    H --> I{🔀 CV Already Exists?<br/>📍 state.cv_content}
    I -->|❌ No| J[🤖 Agent: Please upload<br/>your CV first]
    I -->|✅ Yes| K[🤖 Agent Calls Tool<br/>📍 generate_cover_letter]
    K --> L[🤖 Load Documents from Thread<br/>📍 document_store.get_documents]
    J -.-> V[🔄 Redirect to Upload Flow]
    L --> CONNECTOR2[⬇️ PROCEED TO ANALYSIS PHASE]
  end
 %% styles
  classDef userAction fill:#e8f5e8,stroke:#2e7d32,stroke-width:2px;
  classDef reactAgent fill:#f1f8e9,stroke:#689f38,stroke-width:2px;
  classDef systemNode fill:#e3f2fd,stroke:#1976d2,stroke-width:2px;
  classDef decision fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px;
  classDef endpoint fill:#ffebee,stroke:#d32f2f,stroke-width:3px;
  classDef threadState fill:#fff8e1,stroke:#f57f17,stroke-width:2px;
  classDef title fill:#f5f5f5,stroke:#666666,stroke-width:3px;
  classDef connector fill:#e1f5fe,stroke:#01579b,stroke-width:3px;
  classDef phase fill:#f9f9f9,stroke:#888888,stroke-width:1px;
````

````mermaid

````