"""
Job Search Agent React Tools
Provides all tools for React agent interaction using simple_rag.py
"""
from typing import Dict, Any, List, Optional
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage
from langgraph.store.base import BaseStore
from langgraph.graph.state import StateGraph
from pydantic import BaseModel, Field

from .simple_rag import SimpleRAG
from .agentic_rag import create_agentic_cv_rag
from .state import JobSearchState
import os
from .prompt import (
    PROFILE_STATUS_QUERY, CONTACT_INFO_QUERY,
    LOCATION_QUERY, LANGUAGES_QUERY, PROFESSIONAL_TITLE_QUERY,
    CV_REQUIREMENT_MATCHING_PROMPT, CV_PERSONAL_INFO_EXTRACTION_PROMPT,
    CV_STRUCTURED_ANALYSIS_PROMPT
)
from .response_schemas import (
    StandardResponse, DocumentStatusResponse, PersonalInfoResponse,
    CoverLetterResponse, SearchResponse, UploadResponse, JobRequirementsResponse
)
from .pydantic_models import JobAnalysis, CVAnalysis, PersonalInfo

# =============================================================================
# PYDANTIC SCHEMAS FOR TOOL VALIDATION (LANGGRAPH BEST PRACTICE)
# =============================================================================

class CVUploadInput(BaseModel):
    """Input schema for CV upload tool with proper validation"""
    file_path: Optional[str] = Field(
        default=None,
        description="Full path to the CV file (PDF, DOC, DOCX, TXT, MD). Example: '/Users/john/documents/resume.pdf'"
    )
    content: Optional[str] = Field(
        default=None,
        description="Raw text content of the CV if providing content directly instead of file path"
    )
    thread_id: str = Field(
        default="default",
        description="Thread identifier for document storage (usually keep as 'default')"
    )

# Try to import PDF loader
try:
    from langchain_community.document_loaders import PyPDFLoader
    PDF_LOADER_AVAILABLE = True
except ImportError:
    PDF_LOADER_AVAILABLE = False




# Initialize SimpleRAG components using the dedicated simple_rag.py file
# Initialize SimpleRAG - will automatically load persistent CV data if available
simple_rag = SimpleRAG()

# Initialize Agentic RAG - will use the same SimpleRAG instance
agentic_cv_rag = create_agentic_cv_rag(simple_rag)

def get_job_search_tools() -> List:
    """Return list of all job search tools for React agent - LangGraph best practices"""
    return [
        upload_cv,  # Now supports both text and PDF content
        upload_job_posting,
        get_document_status,
        clear_documents,
        validate_workflow_state,
        analyze_job_requirements,
        analyze_cv_match,
        generate_cover_letter,
        search_cv_details,  # Now uses agentic RAG by default
        extract_personal_info,
        suggest_next_actions,
    ]

# =============================================================================
# DOCUMENT MANAGEMENT TOOLS
# =============================================================================

@tool(args_schema=CVUploadInput)
def upload_cv(file_path: Optional[str] = None, content: Optional[str] = None, thread_id: str = "default") -> str:
    """Upload and analyze a CV/resume file for job applications.

    Use this tool when a user wants to upload their CV, resume, or curriculum vitae.
    The CV can be provided either as a file path or as text content.

    Args:
        file_path: Path to the CV file (PDF, DOC, DOCX, or TXT). Use this for file uploads.
        content: Raw text content of the CV. Use this if the CV content is provided directly.
        thread_id: Internal identifier for document storage (usually keep as default)

    Returns:
        Detailed analysis of the uploaded CV including professional profile and skills

    Examples:
        - upload_cv(file_path="/path/to/resume.pdf")
        - upload_cv(content="John Doe\nSoftware Engineer\n...")
    """
    try:
        # Input validation - must provide either file_path or content
        if not file_path and not content:
            return "❌ Please provide either a file_path to your CV file or the content directly."

        if file_path and content:
            return "❌ Please provide either file_path OR content, not both."

        final_text_content = ""

        # Handle file path input (most common use case)
        if file_path:
            try:
                import os

                # Validate file exists
                if not os.path.exists(file_path):
                    return f"❌ File not found: {file_path}\nPlease check the file path and try again."

                # Handle different file types based on extension
                file_extension = file_path.lower().split('.')[-1]

                if file_extension == 'pdf':
                    # Handle PDF files
                    if not PDF_LOADER_AVAILABLE:
                        return "❌ PDF processing not available. Please install required packages: pip install langchain-community pypdf"

                    from langchain_community.document_loaders import PyPDFLoader
                    loader = PyPDFLoader(file_path)
                    docs = loader.load()

                    if not docs:
                        return f"❌ Could not extract text from PDF: {file_path}\nThe PDF might be image-based or corrupted."

                    final_text_content = "\n".join([doc.page_content for doc in docs])
                    print(f"📄 PDF processed: {len(docs)} pages, {len(final_text_content)} characters")

                elif file_extension in ['doc', 'docx']:
                    # Handle Word documents
                    try:
                        from langchain_community.document_loaders import UnstructuredWordDocumentLoader
                        loader = UnstructuredWordDocumentLoader(file_path)
                        docs = loader.load()
                        final_text_content = "\n".join([doc.page_content for doc in docs])
                        print(f"📄 Word document processed: {len(final_text_content)} characters")
                    except ImportError:
                        return "❌ Word document processing not available. Please install: pip install unstructured[docx]"

                elif file_extension in ['txt', 'md']:
                    # Handle plain text files
                    with open(file_path, 'r', encoding='utf-8') as f:
                        final_text_content = f.read()
                    print(f"📄 Text file processed: {len(final_text_content)} characters")

                else:
                    return f"❌ Unsupported file type: .{file_extension}\nSupported formats: PDF, DOC, DOCX, TXT, MD"

            except Exception as file_error:
                return f"❌ Error processing file {file_path}: {str(file_error)}"

        # Handle direct content input
        elif content:
            final_text_content = content
            print(f"📝 Processing provided content: {len(final_text_content)} characters")

        # Validate content
        if len(final_text_content.strip()) < 50:
            return "❌ CV content too short. Please provide a more complete CV."

        # Enhanced content processing - keep more content but intelligently truncate
        if len(final_text_content) > 15000:  # Increased from 5000
            # Smart truncation: preserve beginning and key sections
            lines = final_text_content.split('\n')
            # Keep first 80% of content to preserve structure
            truncate_point = int(len(final_text_content) * 0.8)
            limited_content = final_text_content[:truncate_point]
            print(f"📝 Content truncated from {len(final_text_content)} to {len(limited_content)} chars (preserved 80%)")
        else:
            limited_content = final_text_content
            print(f"📝 Processing full content: {len(limited_content)} characters")

        # Force re-indexing with new optimized chunking strategy
        print("🔄 Re-indexing CV with LangGraph-optimized chunking...")
        success = simple_rag.replace_cv_content(limited_content)
        if not success:
            return "❌ Failed to index CV content with optimized RAG"

        # Enhanced analysis using multiple targeted queries (leveraging optimized retrieval)
        analysis_components = []

        try:
            # Professional profile analysis
            profile_result = simple_rag.query_cv(
                "What is this person's current professional title, main expertise, and overall career focus? Provide a concise professional summary.",
                f"{thread_id}_profile"
            )
            if profile_result and profile_result.get('answer'):
                analysis_components.append(f"**Professional Profile:** {profile_result['answer']}")

            # Key skills analysis
            skills_result = simple_rag.query_cv(
                "List the most important technical skills, tools, and competencies mentioned in this CV. Focus on the most relevant and current ones.",
                f"{thread_id}_skills"
            )
            if skills_result and skills_result.get('answer'):
                analysis_components.append(f"**Key Skills:** {skills_result['answer']}")

            # Recent experience analysis
            experience_result = simple_rag.query_cv(
                "Describe the most recent and significant work experience, including achievements and responsibilities. What makes this person stand out?",
                f"{thread_id}_experience"
            )
            if experience_result and experience_result.get('answer'):
                analysis_components.append(f"**Recent Experience:** {experience_result['answer']}")

            # Combine all analysis components
            if analysis_components:
                analysis_result = "\n\n".join(analysis_components)
            else:
                analysis_result = "CV uploaded and indexed successfully. Analysis available for job matching."

        except Exception as e:
            analysis_result = f"CV uploaded and indexed with optimized RAG. Analysis temporarily unavailable: {str(e)}"

        # Determine processing method for metadata
        processing_method = "file" if file_path else "content"
        file_type = ""
        if file_path:
            file_type = file_path.lower().split('.')[-1]

        # Enhanced response with more detailed metadata
        return UploadResponse.create(
            document_type=f"cv_{processing_method}" + (f"_{file_type}" if file_type else ""),
            content_length=len(limited_content),
            analysis_result=analysis_result,
            metadata={
                "processing_method": "LangGraph-optimized RAG with enhanced retrieval",
                "chunk_strategy": "500 tokens with 100 token overlap",
                "input_method": f"{'File path: ' + file_path if file_path else 'Direct content'}",
                "file_type": file_type or "text",
                "truncated": len(final_text_content) > len(limited_content),
                "original_length": len(final_text_content) if len(final_text_content) > len(limited_content) else None,
                "next_steps": ["Upload job posting for tailored analysis", "Generate targeted cover letter", "Ask specific questions about your background"]
            }
        )

    except Exception as e:
        return f"❌ Error uploading CV: {str(e)}"


# PDF functionality has been integrated into upload_cv tool


@tool
def upload_job_posting(content: str, thread_id: str = "default") -> str:
    """
    Store job posting content for later analysis. REQUIRED FIRST STEP before analyzing job requirements.

    Args:
        content: The job posting text content
        thread_id: Thread identifier for document storage

    Returns:
        Storage confirmation
    """
    try:
        # Limit content length to prevent API errors (max ~2000 chars)
        limited_content = content[:2000] if len(content) > 2000 else content

        # CRITICAL: Always clear ALL old job data before storing new posting
        print(f"🧹 Clearing all old job data for thread_id: {thread_id}")
        simple_rag.clear_thread_data(thread_id)  # Remove ALL old data

        # Store new job posting using SimpleRAG
        success = simple_rag.store_job_posting(thread_id, limited_content)
        if not success:
            return "❌ Failed to store job posting"

        # Verify immediate storage
        verification = simple_rag.get_job_posting(thread_id)
        if not verification or verification != limited_content:
            return "❌ Failed to verify job posting storage"

        print(f"✅ New job posting stored and verified for thread_id: {thread_id}")
        print(f"📄 Content preview: {limited_content[:100]}...")

        # Simple storage confirmation
        analysis_result = "Job posting stored successfully. Ready for analysis with analyze_job_requirements tool."

        return UploadResponse.create(
            document_type="job_posting",
            content_length=len(limited_content),
            analysis_result=analysis_result,
            metadata={
                "stored_in_thread": thread_id,
                "ready_for": ["Cover letter generation", "Job requirement analysis"]
            }
        )

    except Exception as e:
        return f"❌ Error uploading job posting: {str(e)}"


@tool
def get_document_status(thread_id: str = "default") -> str:
    """
    Check status of uploaded documents using simple_rag.py

    Args:
        thread_id: Thread identifier

    Returns:
        Document status summary
    """
    try:
        # Check CV status (always available from default)
        cv_status = "✅ Uploaded"

        # Check job posting status
        job_status = "✅ Uploaded" if simple_rag.has_job_posting(thread_id) else "❌ Missing"

        # Check if CV is indexed in SimpleRAG and get sample content
        try:
            test_result = simple_rag.vector_store.similarity_search("test", k=1)
            index_status = "✅ Indexed"

            # Get current CV content sample - show comprehensive overview
            cv_sample_result = simple_rag.query_cv("Provide a comprehensive overview including: my name, current role, key technical skills (especially AI/ML), recent work experience, and main achievements. Show the diversity of my background.", thread_id)
            cv_sample = cv_sample_result.get('answer', 'No content found') if cv_sample_result else 'No content found'

        except Exception as e:
            index_status = "❌ Not indexed"
            cv_sample = f"Error accessing CV: {str(e)}"

        # Generate suggestions
        suggestions = []
        if job_status != "✅ Uploaded":
            suggestions.append("Upload a job posting to generate tailored cover letter")
        else:
            suggestions.extend([
                "Generate cover letter",
                "Ask questions about the job",
                "Get interview preparation tips"
            ])

        return DocumentStatusResponse.create(
            cv_status=cv_status,
            job_posting_status=job_status,
            index_status=index_status,
            cv_sample=cv_sample,
            thread_id=thread_id,
            suggestions=suggestions
        )

    except Exception as e:
        return f"❌ Error checking document status: {str(e)}"


@tool
def clear_documents(thread_id: str = "default") -> str:
    """
    Clear all documents for current thread.

    Args:
        thread_id: Thread identifier

    Returns:
        Cleanup confirmation
    """
    try:
        # Clear thread-specific documents using SimpleRAG (keep CV indexed)
        success = simple_rag.clear_thread_data(thread_id)
        if not success:
            return f"❌ Error clearing documents for thread: {thread_id}"

        return f"✅ All documents cleared for thread: {thread_id}\n\nYou can now upload new documents to start fresh."

    except Exception as e:
        return f"❌ Error clearing documents: {str(e)}"


# =============================================================================
# GENERATION TOOLS
# =============================================================================

@tool
def generate_cover_letter(thread_id: str = "default", preferences: Optional[Dict[str, str]] = None) -> str:
    """
    Generate a tailored cover letter using analysis results from analyze_job_requirements and analyze_cv_match

    Args:
        thread_id: Thread identifier
        preferences: User preferences for generation (tone, length, etc.)

    Returns:
        Generated cover letter or error message
    """
    try:
        # Check if job posting is available
        if not simple_rag.has_job_posting(thread_id):
            return StandardResponse.error(
                "generate_cover_letter",
                "Job posting is required. Please upload a job posting first.",
                "MISSING_JOB_POSTING"
            )

        # Check if analysis results are available
        job_analysis = simple_rag.get_job_analysis(thread_id)
        cv_analysis = simple_rag.get_cv_analysis(thread_id)

        if not job_analysis:
            return StandardResponse.error(
                "generate_cover_letter",
                "Job analysis not found. Please run analyze_job_requirements first.",
                "MISSING_JOB_ANALYSIS"
            )

        if not cv_analysis:
            return StandardResponse.error(
                "generate_cover_letter",
                "CV analysis not found. Please run analyze_cv_match first.",
                "MISSING_CV_ANALYSIS"
            )

        # Extract personal information using the dedicated extract_personal_info tool
        print(f"📞 Extracting personal information using extract_personal_info tool...")
        try:
            personal_info_result = extract_personal_info.invoke({"thread_id": thread_id})

            # Parse the JSON response from extract_personal_info
            import json
            if isinstance(personal_info_result, str) and personal_info_result.startswith('{'):
                personal_data = json.loads(personal_info_result)
                if personal_data.get("status") == "success":
                    extracted_info = personal_data.get("data", {})
                    contact_info = extracted_info.get("contact_information", "")
                    location_info = extracted_info.get("location", "")
                    professional_title = extracted_info.get("professional_title", "")
                else:
                    return StandardResponse.error("generate_cover_letter", f"Failed to extract personal info: {personal_data.get('error', {}).get('message', 'Unknown error')}")
            else:
                return StandardResponse.error("generate_cover_letter", "Invalid response from extract_personal_info tool")

        except Exception as e:
            return StandardResponse.error("generate_cover_letter", f"Error calling extract_personal_info: {str(e)}")

        # Build cover letter using analysis results
        from datetime import datetime
        current_date = datetime.now().strftime("%B %d, %Y")

        # Parse extracted personal information
        name = "Name not found"
        email = ""
        location = ""

        # Extract name from contact_info
        if "Name:" in contact_info:
            try:
                name = contact_info.split("Name:")[1].split("\n")[0].strip()
            except:
                pass

        # Extract email from contact_info
        if "Email:" in contact_info:
            try:
                email_line = contact_info.split("Email:")[1].split("\n")[0].strip()
                if email_line and email_line != "Not specified":
                    email = email_line
            except:
                pass

        # Use location from extract_personal_info
        if location_info and location_info != "Location not specified":
            location = location_info.strip()

        # Extract company name from job analysis
        company_name = job_analysis.get("company_culture", "your organization")
        if "company" in company_name.lower():
            company_name = company_name.split("company")[0].strip() or "your organization"

        # Build cover letter header with extracted personal info (NO HARDCODING!)
        header_lines = []
        if name and name != "Name not found":
            header_lines.append(name)
        if email:
            header_lines.append(email)
        if location:
            header_lines.append(location)
        header_lines.append("")

        header_lines.extend([
            current_date,
            "",
            "Dear Hiring Manager,",
            ""
        ])

        # Build narrative-driven cover letter content
        top_requirements = job_analysis.get("top_requirements", [])
        cv_matches = cv_analysis.get("cv_job_matches", [])
        talking_points = cv_analysis.get("compelling_talking_points", [])
        overall_fit = cv_analysis.get("overall_fit_score", 0)

        # Extract company insights for compelling opener
        role_focus = job_analysis.get('role_focus', 'this position')
        company_culture = job_analysis.get('company_culture', company_name)

        # Build compelling opening hook with company insight + immediate value
        strongest_talking_point = talking_points[0] if talking_points else None
        if overall_fit > 0.7 and strongest_talking_point:
            opening_hook = f"What motivated me to explore {company_name}'s focus on {role_focus}, I knew my experience in {strongest_talking_point['point'].lower()} would be exactly what your team needs."
        elif company_culture and company_culture != company_name:
            opening_hook = f"Your emphasis on {company_culture} resonates with my approach to {role_focus} - I thrive in environments that value innovation and user-centric solutions."
        else:
            opening_hook = f"Having spent years mastering {role_focus}, I'm drawn to {company_name}'s commitment to creating exceptional user experiences."

        # Create flowing experience narrative (weave all 3 requirements naturally)
        narrative_sentences = []
        transition_words = ["Recently", "Building on this experience", "Additionally"]

        for i, req in enumerate(top_requirements):
            if i >= 3:  # Limit to 3 requirements max
                break

            req_name = req.get("requirement", f"Requirement {i+1}")

            # Find matching CV experience
            matching_experience = ""
            for match in cv_matches:
                if match.get("requirement") == req_name:
                    matching_experience = match.get("matching_experience", "")
                    break

            if matching_experience:
                # Create narrative sentence (not bullet point)
                transition = transition_words[i] if i < len(transition_words) else "Moreover"
                # Truncate and make conversational
                experience_snippet = matching_experience[:100].strip()
                if len(matching_experience) > 100:
                    experience_snippet = experience_snippet.rsplit(' ', 1)[0] + "..."

                narrative_sentences.append(f"{transition}, I {experience_snippet.lower()}")

        experience_narrative = " ".join(narrative_sentences) + " This diverse experience positions me to tackle complex challenges while maintaining focus on user satisfaction."

        # Forward-looking contribution statement
        confidence_level = "confident" if overall_fit > 0.6 else "excited"
        contribution_close = f"I'm {confidence_level} that my proven track record in {role_focus} can help {company_name} achieve its next level of growth. I'd welcome the opportunity to discuss how my experience can contribute to your team's continued success."

        # Assemble narrative content (3 paragraphs max, no bullets)
        content_lines = [
            opening_hook,
            "",
            experience_narrative,
            "",
            contribution_close,
            "",
            "Best regards,",
            name
        ]

        # Combine header and content
        all_lines = header_lines + content_lines
        cover_letter_content = "\n".join(all_lines)

        # Return standardized JSON response with cover letter and metadata
        return CoverLetterResponse.create(
            cover_letter_content=cover_letter_content,
            personal_info_used={
                "contact_details": contact_info[:100] + "..." if len(contact_info) > 100 else contact_info,
                "location_details": location_info[:100] + "..." if len(location_info) > 100 else location_info
            },
            job_info_used={
                "narrative_format": "Storytelling approach with integrated requirements",
                "requirements_woven": len(top_requirements),
                "talking_points_integrated": len(talking_points),
                "overall_fit_score": f"{overall_fit:.1%}" if overall_fit else "Analysis-based",
                "word_count_target": "150-200 words (professional and concise)"
            }
        )

    except Exception as e:
        return StandardResponse.error("generate_cover_letter", str(e))


@tool
def search_cv_details(query: str, thread_id: str = "default") -> str:
    """
    Advanced CV search using agentic RAG with intelligent query rewriting and quality assessment

    This tool uses LangGraph's agentic RAG pattern to:
    - Intelligently route queries (retrieval vs direct response)
    - Automatically rewrite vague or foreign queries
    - Iteratively improve search quality
    - Prevent hallucination with grounded responses

    Best for: Vague queries, foreign language terms, complex questions

    Args:
        query: Search query for CV content (can be vague or in any language)
        thread_id: Thread identifier

    Returns:
        Comprehensive CV search results with automatic query improvement
    """
    try:
        print(f"🤖 Agentic RAG search for: '{query}'")

        # Use agentic RAG for intelligent search
        result = agentic_cv_rag.search(query, thread_id)

        # Extract results
        answer = result.get("answer", "No answer generated")
        retrieval_attempts = result.get("retrieval_attempts", 0)
        final_query = result.get("final_query", query)

        # Determine if query was rewritten
        query_rewritten = query != final_query

        return SearchResponse.create(
            query=query,
            answer=answer,
            context_count=retrieval_attempts,
            relevant_sections=[
                f"Query rewritten: {query_rewritten}",
                f"Final query: {final_query}",
                f"Retrieval attempts: {retrieval_attempts}"
            ]
        )

    except Exception as e:
        # Fallback to basic search on error
        print(f"⚠️ Agentic RAG failed: {e}, falling back to basic search")
        return search_cv_details_basic.invoke({"query": query, "thread_id": thread_id})


@tool
def search_cv_details_basic(query: str, thread_id: str = "default") -> str:
    """
    BACKUP: Basic CV search with anti-hallucination controls (fallback only)

    Args:
        query: Search query for CV content
        thread_id: Thread identifier

    Returns:
        Relevant CV details matching the query, grounded strictly in actual CV content
    """
    try:
        # Limit query length to prevent token issues
        limited_query = query[:1500] if len(query) > 1500 else query

        # Step 1: Document Grading - Check if retrieved documents are relevant (LangGraph best practice)
        # Use unique thread ID to avoid caching issues (following analyze_cv_match pattern)
        unique_thread_id = f"{thread_id}_search_{hash(limited_query[:50])}"

        # Get raw chunks for document relevance grading first
        retrieved_chunks = simple_rag.get_raw_cv_chunks(limited_query, k=8)

        if not retrieved_chunks or len(retrieved_chunks) == 0:
            return SearchResponse.create(
                query=query,
                answer="I cannot find any relevant information in your CV for this query. Please verify your CV contains this information or try rephrasing your question.",
                context_count=0
            )

        # Step 2: Document Relevance Grading (LangGraph CRAG pattern)
        docs_context = "\n\n".join(retrieved_chunks[:5])  # Limit context for grading

        grade_prompt = f"""You are a grader assessing relevance of retrieved CV content to a user question.

Here is the retrieved CV content:
{docs_context}

Here is the user question: {limited_query}

If the CV content contains keywords or semantic meaning related to the user question, grade it as relevant.
Give a binary score 'relevant' or 'not_relevant' to indicate whether the CV content can answer the question.

CRITICAL: Only grade as 'relevant' if the CV content actually contains information that can answer the question.

Score:"""

        from langchain_openai import ChatOpenAI
        from .config import LLM_CONFIG

        # Document grading with structured output (LangGraph best practice)
        class DocumentGrade(BaseModel):
            """Binary score for document relevance check"""
            score: str = Field(description="Document relevance score: 'relevant' or 'not_relevant'")

        grading_llm = ChatOpenAI(**LLM_CONFIG).with_structured_output(DocumentGrade)
        grade_result = grading_llm.invoke(grade_prompt)

        if grade_result.score == "not_relevant":
            return SearchResponse.create(
                query=query,
                answer=f"The retrieved CV content is not relevant to your question about '{limited_query}'. Please try a different search term or verify this information exists in your CV.",
                context_count=len(retrieved_chunks)
            )

        # Step 3: Enhanced RAG Query with strict grounding prompt (following CV_REQUIREMENT_MATCHING_PROMPT pattern)
        enhanced_query = f"""CRITICAL ANTI-HALLUCINATION INSTRUCTIONS:
- ONLY use information explicitly stated in my CV
- NEVER invent, estimate, or assume any details not in the CV
- NEVER mention companies, projects, or achievements not explicitly written in the CV
- If the information is not clearly stated, respond: "This information is not specified in the CV"
- Quote or reference actual CV content when possible

From my CV, find information about: {limited_query}

STRICT REQUIREMENT: Base your response ONLY on explicit CV content. Do not extrapolate or fill gaps."""

        # Use enhanced retrieval with unique thread ID
        result = simple_rag.query_cv(enhanced_query, unique_thread_id)

        if not result or not result.get('answer'):
            return SearchResponse.create(
                query=query,
                answer="I cannot find specific information about this topic in your CV.",
                context_count=0
            )

        # Step 4: Hallucination Check (LangGraph Self-RAG pattern)
        answer = result['answer']
        context_chunks = retrieved_chunks[:5]  # Use original chunks for verification

        hallucination_prompt = f"""You are a grader assessing whether an answer is grounded in/supported by CV facts.

CV Facts:
{docs_context}

Generated Answer:
{answer}

Is the answer grounded in/supported by the CV facts? Give a binary score 'grounded' or 'hallucinated'.
Look for:
- Invented company names not in CV
- Fabricated metrics not in CV
- Made-up projects not in CV
- Assumed skills not explicitly mentioned

Score:"""

        class HallucinationGrade(BaseModel):
            """Binary score for hallucination grading"""
            score: str = Field(description="Hallucination score: 'grounded' or 'hallucinated'")

        hallucination_llm = ChatOpenAI(**LLM_CONFIG).with_structured_output(HallucinationGrade)
        hallucination_result = hallucination_llm.invoke(hallucination_prompt)

        if hallucination_result.score == "hallucinated":
            return SearchResponse.create(
                query=query,
                answer=f"I cannot provide reliable information about '{limited_query}' based on your CV content. Please verify this information exists in your CV or rephrase your question.",
                context_count=len(result.get('context', []))
            )

        # Step 5: Return verified, grounded response
        context_count = len(result.get('context', []))

        return SearchResponse.create(
            query=query,
            answer=answer,
            context_count=context_count
        )

    except Exception as e:
        # Handle OpenAI API errors gracefully
        if "server had an error" in str(e) or "APIError" in str(e):
            return SearchResponse.create(
                query=query,
                answer="❌ Temporary API issue. Please try again in a moment.",
                context_count=0
            )
        else:
            return SearchResponse.create(
                query=query,
                answer=f"❌ Error searching CV: {str(e)}",
                context_count=0
            )


@tool
def extract_personal_info(thread_id: str = "default") -> str:
    """
    Extract comprehensive personal information from CV using structured output

    Args:
        thread_id: Thread identifier

    Returns:
        Structured personal information from CV
    """
    try:
        # Use centralized extraction prompt from prompt.py - LangGraph best practice
        extraction_prompt = CV_PERSONAL_INFO_EXTRACTION_PROMPT

        from langchain_openai import ChatOpenAI
        from .config import LLM_CONFIG
        llm = ChatOpenAI(**LLM_CONFIG)

        # Use structured output with Pydantic model
        structured_llm = llm.with_structured_output(PersonalInfo)

        try:
            # Get raw CV chunks directly from vector store (bypasses LLM filtering)
            contact_chunks = simple_rag.get_raw_cv_chunks("contact information email phone address name header", k=12)

            # Combine raw chunks to preserve all contact details
            cv_context = "\n\n".join(contact_chunks)

            # Extract personal info using structured output
            full_prompt = f"{extraction_prompt}\n\nRaw CV Content:\n{cv_context}"
            personal_info = structured_llm.invoke(full_prompt)

            # Convert to response format
            return PersonalInfoResponse.create(
                contact_info=f"Name: {personal_info.full_name}\nEmail: {personal_info.email or 'Not specified'}\nPhone: {personal_info.phone or 'Not specified'}",
                location=personal_info.location or "Location not specified",
                languages=", ".join(personal_info.languages) if personal_info.languages else "Languages not specified",
                professional_title=f"{personal_info.current_title or 'Title not specified'}" + (f" at {personal_info.current_company}" if personal_info.current_company else "")
            )

        except Exception as e:
            # Fallback to original query method if structured output fails
            queries = {
                "contact_info": CONTACT_INFO_QUERY,
                "location": LOCATION_QUERY,
                "languages": LANGUAGES_QUERY,
                "basic_profile": PROFESSIONAL_TITLE_QUERY
            }

            extracted_info = {}
            for info_type, query in queries.items():
                try:
                    result = simple_rag.query_cv(query, thread_id)
                    if result and result.get('answer'):
                        extracted_info[info_type] = result['answer']
                except Exception:
                    extracted_info[info_type] = f"Could not extract {info_type}"

            return PersonalInfoResponse.create(
                contact_info=extracted_info.get('contact_info', 'Not found'),
                location=extracted_info.get('location', 'Not found'),
                languages=extracted_info.get('languages', 'Not found'),
                professional_title=extracted_info.get('basic_profile', 'Not found')
            )

    except Exception as e:
        return f"❌ Error extracting personal information: {str(e)}"


# =============================================================================
# UTILITY TOOLS (Simplified versions)
# =============================================================================




@tool
def analyze_job_requirements(thread_id: str = "default") -> str:
    """
    Analyze PREVIOUSLY UPLOADED job posting to extract the 3 most important requirements for cover letter targeting.
    Requires upload_job_posting to be called first.

    Args:
        thread_id: Thread identifier

    Returns:
        JSON with top 3 job requirements and analysis
    """
    try:
        # Check if job posting is available
        print(f"🔍 analyze_job_requirements: Checking for job posting, thread_id: {thread_id}")
        job_posting = simple_rag.get_job_posting(thread_id)

        if not job_posting:
            return StandardResponse.error(
                "analyze_job_requirements",
                "No job posting found. You must call upload_job_posting first with the job posting content.",
                "MISSING_JOB_POSTING"
            )

        # CRITICAL: Check if we have BOTH job_posting AND job_analysis (indicates stale data)
        existing_analysis = simple_rag.get_job_analysis(thread_id)
        if existing_analysis:
            print(f"⚠️ WARNING: Found existing job analysis - this may be stale data!")
            print(f"📄 Job posting preview: {job_posting[:100]}...")
            # Clear old analysis to force fresh analysis
            thread_data = simple_rag._load_thread_data(thread_id)
            if "job_analysis" in thread_data:
                del thread_data["job_analysis"]
                simple_rag._save_thread_data(thread_id, thread_data)
                print(f"🧹 Cleared old job analysis to ensure fresh analysis")

        print(f"📋 Processing job posting: {job_posting[:100]}...")

        # Use LLM with structured output to analyze job requirements
        analysis_prompt = f"""You are a job analysis expert. Analyze this job posting and extract the 3 MOST IMPORTANT requirements that a candidate must demonstrate in their cover letter to be compelling.

Job Posting:
{job_posting}

For each requirement, provide:
1. The specific requirement/skill from the job posting
2. Why it's critical for this specific role
3. 3-5 relevant keywords from the job posting

Also analyze the company culture and role focus."""

        from langchain_openai import ChatOpenAI
        from .config import LLM_CONFIG
        llm = ChatOpenAI(**LLM_CONFIG)

        # Use structured output with Pydantic v2
        structured_llm = llm.with_structured_output(JobAnalysis)

        try:
            analysis_result = structured_llm.invoke(analysis_prompt)
            # Convert Pydantic model to dict for storage
            analysis_data = analysis_result.model_dump()
        except Exception as e:
            # Fallback to basic analysis if structured output fails
            return StandardResponse.error(
                "analyze_job_requirements",
                f"Failed to analyze job requirements: {str(e)}"
            )

        # Store analysis results for cover letter generation
        success = simple_rag.store_job_analysis(thread_id, analysis_data)
        if not success:
            return StandardResponse.error("analyze_job_requirements", "Failed to store job analysis")

        # Verify storage immediately for debugging
        verification = simple_rag.get_job_analysis(thread_id)
        if not verification:
            print(f"⚠️ WARNING: Job analysis stored but not retrievable for thread_id: {thread_id}")
        else:
            print(f"✅ Job analysis stored and verified for thread_id: {thread_id}")

        return JobRequirementsResponse.create(
            top_requirements=analysis_data.get('top_requirements', []),
            company_culture=analysis_data.get('company_culture', ''),
            role_focus=analysis_data.get('role_focus', '')
        )

    except Exception as e:
        return StandardResponse.error("analyze_job_requirements", str(e))


@tool
def analyze_cv_match(thread_id: str = "default") -> str:
    """
    Analyze CV to find relevant experience matching job requirements

    Args:
        thread_id: Thread identifier

    Returns:
        JSON with matching experience and compelling talking points
    """
    try:
        # Check if job analysis is available (with retry for execution context issues)
        job_analysis = simple_rag.get_job_analysis(thread_id)

        # If not found, try to reload thread data explicitly
        if not job_analysis:
            # Force reload of thread data in case of execution context issues
            import time
            time.sleep(0.1)  # Brief pause for file system consistency
            thread_data = simple_rag._load_thread_data(thread_id)
            job_analysis = thread_data.get("job_analysis")

        if not job_analysis:
            return StandardResponse.error(
                "analyze_cv_match",
                "Job analysis not found. Please run analyze_job_requirements first.",
                "MISSING_JOB_ANALYSIS"
            )
        top_requirements = job_analysis.get("top_requirements", [])

        # Build comprehensive CV matching analysis
        cv_matches = []

        for i, req in enumerate(top_requirements, 1):
            # Handle numbered format from JobRequirementsResponse
            requirement = req.get(f"requirement {i}", "") or req.get("requirement", "")
            importance = req.get(f"importance {i}", "") or req.get("importance", "")
            keywords = req.get(f"keywords {i}", []) or req.get("keywords", [])

            # Use centralized prompt from prompt.py - LangGraph best practice
            matching_query = CV_REQUIREMENT_MATCHING_PROMPT.format(
                requirement=requirement,
                importance=importance,
                keywords=', '.join(keywords)
            )

            # Query CV for matching experience with unique thread ID to avoid caching issues
            unique_thread_id = f"{thread_id}_req_{i}_{hash(requirement[:50])}"
            match_result = simple_rag.query_cv(matching_query, unique_thread_id)

            if match_result and match_result.get('answer'):
                cv_matches.append({
                    "requirement": requirement,
                    "matching_experience": match_result['answer'],
                    "keywords_addressed": keywords,
                    "strength_score": "high" if len(match_result['answer']) > 100 else "medium"
                })

        # CRITICAL FIX: Use the cv_matches data that was carefully built through individual RAG queries
        # Build cv_matches summary for structured aggregation
        cv_matches_summary = "\n\n".join([
            f"REQUIREMENT {i+1}: {match.get(f'requirement {i+1}', match.get('requirement', 'Unknown requirement'))}\n"
            f"CV EXPERIENCE FOUND: {match.get('matching_experience', 'No experience found')}\n"
            f"KEYWORDS ADDRESSED: {', '.join(match.get('keywords_addressed', []))}\n"
            f"MATCH STRENGTH: {match.get('strength_score', 'unknown')}"
            for i, match in enumerate(cv_matches)
        ])

        # Use centralized structured analysis prompt from prompt.py
        cv_analysis_prompt = CV_STRUCTURED_ANALYSIS_PROMPT.format(
            cv_matches_summary=cv_matches_summary
        )

        try:
            # Use structured output for consistent CV analysis aggregation
            structured_llm = simple_rag.llm.with_structured_output(CVAnalysis)
            cv_analysis_result = structured_llm.invoke(cv_analysis_prompt)
            analysis_results = cv_analysis_result.model_dump()
        except Exception as e:
            # NO SILENT FALLBACK - Return explicit error for debugging visibility
            return StandardResponse.error(
                "analyze_cv_match",
                f"Structured LLM analysis failed during aggregation: {str(e)}. Raw cv_matches were successfully generated but could not be aggregated into final format.",
                "STRUCTURED_OUTPUT_FAILURE"
            )

        # Store for cover letter generation
        success = simple_rag.store_cv_analysis(thread_id, analysis_results)
        if not success:
            return StandardResponse.error("analyze_cv_match", "Failed to store CV analysis")

        # Extract talking points count from results for message
        talking_points_count = len(analysis_results.get("compelling_talking_points", []))

        return StandardResponse.success(
            "analyze_cv_match",
            analysis_results,
            f"Found {talking_points_count} compelling talking points"
        )

    except Exception as e:
        return StandardResponse.error("analyze_cv_match", str(e))





@tool
def validate_workflow_state(thread_id: str = "default") -> str:
    """
    Validate current workflow state and guide next steps. Call this when unsure about workflow.

    Args:
        thread_id: Thread identifier

    Returns:
        Workflow validation and next step guidance
    """
    try:
        print(f"🔍 Validating workflow state for thread_id: {thread_id}")

        # Check current state
        has_cv = True  # CV is always available
        has_job_posting = simple_rag.has_job_posting(thread_id)
        has_job_analysis = bool(simple_rag.get_job_analysis(thread_id))
        has_cv_analysis = bool(simple_rag.get_cv_analysis(thread_id))

        print(f"📊 Current state: CV={has_cv}, Job={has_job_posting}, JobAnalysis={has_job_analysis}, CVAnalysis={has_cv_analysis}")

        # Determine workflow status and next steps
        workflow_status = []
        next_actions = []

        if not has_job_posting:
            workflow_status.append("❌ No job posting stored")
            next_actions.append("🚨 CRITICAL: Call upload_job_posting with job posting content FIRST")

        elif has_job_posting and not has_job_analysis:
            workflow_status.append("✅ Job posting stored")
            workflow_status.append("❌ Job analysis missing")
            next_actions.append("📋 Call analyze_job_requirements to extract key requirements")

        elif has_job_analysis and not has_cv_analysis:
            workflow_status.append("✅ Job posting and analysis ready")
            workflow_status.append("❌ CV analysis missing")
            next_actions.append("🎯 Call analyze_cv_match to find relevant CV experience")

        elif has_job_analysis and has_cv_analysis:
            workflow_status.append("✅ Complete analysis workflow ready")
            next_actions.append("✍️ Ready for generate_cover_letter or extract_personal_info")

        # Create response
        status_text = "\n".join(workflow_status)
        actions_text = "\n".join(next_actions)

        return StandardResponse.success(
            "validate_workflow_state",
            {
                "thread_id": thread_id,
                "workflow_complete": has_job_posting and has_job_analysis and has_cv_analysis,
                "current_status": workflow_status,
                "next_actions": next_actions,
                "workflow_stage": "complete" if (has_job_analysis and has_cv_analysis) else "incomplete"
            },
            f"Workflow validation complete. Status: {status_text}"
        )

    except Exception as e:
        return StandardResponse.error("validate_workflow_state", str(e))


@tool
def suggest_next_actions(thread_id: str = "default") -> str:
    """Suggest helpful next actions based on current state."""
    try:
        has_cv = True  # CV is always available from default
        has_job = simple_rag.has_job_posting(thread_id)

        # Generate suggestions inline
        suggestions = []
        if not has_cv:
            suggestions.append("📄 Upload your CV/resume to begin")
        if not has_job:
            suggestions.append("💼 Upload a job posting for tailored assistance")
        if has_cv and has_job:
            suggestions.extend([
                "✍️ Generate a tailored cover letter",
                "❓ Ask questions about job fit",
                "🎯 Get interview preparation tips"
            ])

        return StandardResponse.success(
            "suggest_next_actions",
            {
                "current_status": {
                    "cv_available": has_cv,
                    "job_posting_available": has_job
                },
                "suggested_actions": suggestions,
                "thread_id": thread_id
            },
            "Next action suggestions generated"
        )
    except Exception as e:
        return f"❌ Error generating suggestions: {str(e)}"





# =============================================================================
# CORE TOOL REGISTRY
# =============================================================================
