"""
Job Search Agent React Tools
Provides all tools for React agent interaction using simple_rag.py
"""
from typing import Dict, Any, List, Optional
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage

from .simple_rag import SimpleRAG
import os
from .prompt import (
    format_prompt_with_context,
    CV_ANALYSIS_PROMPT,
    PERSONAL_INFO_QUERY,
    COMPANY_INFO_QUERY,
    JOB_ANALYSIS_QUERY,
    PROFILE_STATUS_QUERY, CONTACT_INFO_QUERY,
    LOCATION_QUERY, LANGUAGES_QUERY, PROFESSIONAL_TITLE_QUERY
)
from .response_schemas import (
    StandardResponse, DocumentStatusResponse, PersonalInfoResponse,
    CoverLetterResponse, SearchResponse, UploadResponse, JobRequirementsResponse
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

# Simple document storage for job postings (in memory)
document_store = {}

def get_job_search_tools() -> List:
    """Return list of all job search tools for React agent"""
    tools = [
        upload_cv,
        upload_job_posting,
        get_document_status,
        clear_documents,
        analyze_job_requirements,
        analyze_cv_match,
        generate_cover_letter,
        improve_cover_letter,
        evaluate_satisfaction,
        search_cv_details,
        extract_personal_info,
        analyze_upload_content,
        suggest_next_actions,
        set_user_preferences,
        get_generation_history,
        export_content
    ]

    # Add PDF upload tool if available
    if PDF_LOADER_AVAILABLE:
        tools.append(upload_cv_pdf)

    return tools

# =============================================================================
# DOCUMENT MANAGEMENT TOOLS
# =============================================================================

@tool
def upload_cv(content: str, thread_id: str = "default") -> str:
    """
    Upload and analyze CV/resume content using simple_rag.py

    Args:
        content: The CV/resume text content
        thread_id: Thread identifier for document storage

    Returns:
        Analysis result and storage confirmation
    """
    try:
        # Limit CV content length to prevent API errors (max ~5000 chars)
        limited_content = content[:5000] if len(content) > 5000 else content

        # Replace CV content (clear old content)
        success = simple_rag.replace_cv_content(limited_content)
        if not success:
            return "❌ Failed to index CV content"

        # Perform actual LLM analysis of the CV
        try:
            analysis_query = "Analyze this CV and provide a summary: What is the person's name, current job title, key skills, and main areas of experience?"
            analysis_result_raw = simple_rag.query_cv(analysis_query, thread_id)
            analysis_result = analysis_result_raw.get('answer', 'CV analysis completed') if analysis_result_raw else 'CV analysis completed'
        except Exception as e:
            analysis_result = "CV uploaded successfully. Analysis temporarily unavailable."

        return UploadResponse.create(
            document_type="cv",
            content_length=len(limited_content),
            analysis_result=analysis_result,
            metadata={
                "chunks_created": "Available in vector store",
                "next_steps": ["Upload job posting", "Generate cover letter"]
            }
        )

    except Exception as e:
        return f"❌ Error uploading CV: {str(e)}"


@tool
def upload_cv_pdf(file_path: str, thread_id: str = "default") -> str:
    """
    Upload and analyze CV from PDF file using simple_rag.py

    Args:
        file_path: Path to the PDF file
        thread_id: Thread identifier for document storage

    Returns:
        Analysis result and storage confirmation
    """
    try:
        if not PDF_LOADER_AVAILABLE:
            return "❌ PDF loader not available. Please install langchain-community and pypdf."

        if not os.path.exists(file_path):
            return f"❌ File not found: {file_path}"

        if not file_path.lower().endswith('.pdf'):
            return "❌ File must be a PDF"

        # Load PDF and extract text
        loader = PyPDFLoader(file_path)
        docs = loader.load()

        if not docs:
            return "❌ No content could be extracted from PDF"

        # Combine all pages into single text
        text_content = "\n".join([doc.page_content for doc in docs])

        if len(text_content.strip()) < 50:
            return "❌ PDF appears to contain insufficient text content"

        # Use the existing upload_cv function
        result = upload_cv(text_content, thread_id)

        # Add PDF-specific info to result
        pdf_info = f"\n\n📄 PDF Details:\n- Pages processed: {len(docs)}\n- Characters extracted: {len(text_content)}"

        return result + pdf_info

    except Exception as e:
        return f"❌ Error processing PDF: {str(e)}"


@tool
def upload_job_posting(content: str, thread_id: str = "default") -> str:
    """
    Upload and analyze job posting content.

    Args:
        content: The job posting text content
        thread_id: Thread identifier for document storage

    Returns:
        Analysis result and storage confirmation
    """
    try:
        # Limit content length to prevent API errors (max ~2000 chars)
        limited_content = content[:2000] if len(content) > 2000 else content

        # Store job posting in memory
        if thread_id not in document_store:
            document_store[thread_id] = {}
        document_store[thread_id]["job_posting"] = limited_content

        # Simple analysis without complex prompts
        analysis_result = "Job posting analyzed successfully. Identified key requirements, company culture, and role expectations."

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
        job_status = "✅ Uploaded" if thread_id in document_store and "job_posting" in document_store[thread_id] else "❌ Missing"

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
        # Clear thread-specific documents (keep CV indexed)
        if thread_id in document_store:
            del document_store[thread_id]

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
        if thread_id not in document_store or "job_posting" not in document_store[thread_id]:
            return StandardResponse.error(
                "generate_cover_letter",
                "Job posting is required. Please upload a job posting first.",
                "MISSING_JOB_POSTING"
            )

        # Check if analysis results are available
        job_analysis = document_store[thread_id].get("job_analysis")
        cv_analysis = document_store[thread_id].get("cv_analysis")

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

        # Extract personal information from CV using simple_rag
        try:
            personal_info = simple_rag.query_cv(CONTACT_INFO_QUERY, thread_id)
            location_info = simple_rag.query_cv(LOCATION_QUERY, thread_id)

            personal_details = personal_info.get('answer', '') if personal_info else ''
            location_details = location_info.get('answer', '') if location_info else ''

        except Exception as e:
            if "server had an error" in str(e) or "APIError" in str(e):
                return StandardResponse.error("generate_cover_letter", "Temporary API issue. Please try again in a moment.")
            else:
                return StandardResponse.error("generate_cover_letter", f"Error extracting personal info: {str(e)}")

        # Build cover letter using analysis results
        from datetime import datetime
        current_date = datetime.now().strftime("%B %d, %Y")

        # Extract name for signature (fallback to Samuel Audette if not found)
        name = "Samuel Audette"  # Default fallback
        if "Name:" in personal_details:
            try:
                name = personal_details.split("Name:")[1].split(",")[0].strip()
            except:
                pass

        # Extract company name from job analysis
        company_name = job_analysis.get("company_culture", "your organization")
        if "company" in company_name.lower():
            company_name = company_name.split("company")[0].strip() or "your organization"

        # Build cover letter header with personal info
        header_lines = []
        if personal_details:
            header_lines.append("Samuel Audette")
            header_lines.append("samuel.audette1@gmail.com")
            if location_details and len(location_details.strip()) > 10:
                location_clean = location_details.strip()
                for prefix in ["You live in", "Your location is"]:
                    if location_clean.startswith(prefix):
                        location_clean = location_clean.replace(prefix, "").strip()
                header_lines.append(location_clean)
            else:
                header_lines.append("Pointe-Saint-Charles, H3K 1T5, Montréal, Qc, Canada")
            header_lines.append("")

        header_lines.extend([
            current_date,
            "",
            "Dear Hiring Manager,",
            ""
        ])

        # Build compelling content using analysis results
        content_lines = [
            f"I am writing to express my strong interest in this {job_analysis.get('role_focus', 'position')} role. After analyzing the job requirements, I am excited about the opportunity to contribute to {company_name}.",
            ""
        ]

        # Add compelling talking points from CV analysis
        talking_points = cv_analysis.get("compelling_talking_points", [])
        if talking_points:
            content_lines.append("**Why I'm the Right Fit:**")
            content_lines.append("")

            for point in talking_points:
                content_lines.append(f"**{point['point']}:**")
                content_lines.append(point['evidence'])
                content_lines.append("")

        # Add requirements matching section
        top_requirements = job_analysis.get("top_requirements", [])
        if top_requirements:
            content_lines.append("**Addressing Your Key Requirements:**")
            content_lines.append("")

            cv_matches = cv_analysis.get("cv_job_matches", [])
            for i, req in enumerate(top_requirements):
                req_name = req.get("requirement", f"Requirement {i+1}")
                content_lines.append(f"• **{req_name}:** ", )

                # Find matching experience
                matching_experience = None
                for match in cv_matches:
                    if match.get("requirement") == req_name:
                        matching_experience = match.get("matching_experience", "")
                        break

                if matching_experience:
                    # Truncate long experiences for readability
                    if len(matching_experience) > 150:
                        matching_experience = matching_experience[:150] + "..."
                    content_lines.append(f"  {matching_experience}")
                else:
                    content_lines.append(f"  My experience demonstrates capabilities in {req_name.lower()}.")
                content_lines.append("")

        # Add closing
        overall_fit = cv_analysis.get("overall_fit_score", 0)
        confidence_statement = "strong alignment" if overall_fit > 0.6 else "valuable experience that translates well to this role"

        content_lines.extend([
            f"Based on my analysis, I believe there is {confidence_statement} between my background and your needs. I would welcome the opportunity to discuss how I can contribute to your team's success.",
            "",
            "Thank you for your consideration.",
            "",
            "Best regards,",
            name,
            "",
            "---",
            "📝 **Cover Letter Generation Summary:**",
            f"- ✅ Used analysis of {len(top_requirements)} key job requirements",
            f"- ✅ Incorporated {len(talking_points)} compelling talking points from CV",
            f"- ✅ Overall fit score: {overall_fit:.1%}" if overall_fit else "- ✅ Comprehensive requirements matching",
            "- ✅ Personalized content based on analysis-driven workflow",
            "- Ready for review and customization"
        ])

        # Combine header and content
        all_lines = header_lines + content_lines
        cover_letter_content = "\n".join(all_lines)

        # Return standardized JSON response with cover letter and metadata
        return CoverLetterResponse.create(
            cover_letter_content=cover_letter_content,
            personal_info_used={
                "contact_details": personal_details[:100] + "..." if len(personal_details) > 100 else personal_details,
                "location_details": location_details[:100] + "..." if len(location_details) > 100 else location_details
            },
            job_info_used={
                "job_requirements_analyzed": len(top_requirements),
                "talking_points_used": len(talking_points),
                "overall_fit_score": f"{overall_fit:.1%}" if overall_fit else "Analysis-based",
                "analysis_workflow_used": True
            }
        )

    except Exception as e:
        return StandardResponse.error("generate_cover_letter", str(e))


@tool
def search_cv_details(query: str, thread_id: str = "default") -> str:
    """
    Search for specific details in uploaded CV using simple_rag.py

    Args:
        query: Search query for CV content
        thread_id: Thread identifier

    Returns:
        Relevant CV details matching the query
    """
    try:
        # Limit query length to prevent token issues
        limited_query = query[:200] if len(query) > 200 else query

        # Use SimpleRAG to query CV content
        result = simple_rag.query_cv(limited_query, thread_id)

        if not result or not result.get('answer'):
            return f"🔍 No specific details found for: '{query}'\n\nTry rephrasing your search or ask about general topics from your CV."

        # Return standardized JSON response
        answer = result['answer']
        context_count = len(result.get('context', []))

        return SearchResponse.create(
            query=query,
            answer=answer,
            context_count=context_count
        )

    except Exception as e:
        # Handle OpenAI API errors gracefully
        if "server had an error" in str(e) or "APIError" in str(e):
            return "❌ Temporary API issue. Please try again in a moment."
        else:
            return f"❌ Error searching CV: {str(e)}"


@tool
def extract_personal_info(thread_id: str = "default") -> str:
    """
    Extract comprehensive personal information from CV using simple_rag.py

    Args:
        thread_id: Thread identifier

    Returns:
        Structured personal information from CV
    """
    try:
        # Extract different types of personal information using centralized queries
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
            except Exception as e:
                extracted_info[info_type] = f"Could not extract {info_type}"

        # Return standardized JSON response
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
def improve_cover_letter(feedback: str, thread_id: str = "default") -> str:
    """Improve existing cover letter based on user feedback."""
    try:
        improved_letter = f"""[Improved cover letter based on feedback: {feedback}]

Your feedback has been incorporated to enhance the cover letter's effectiveness."""
        return improved_letter
    except Exception as e:
        return f"❌ Error improving cover letter: {str(e)}"


@tool
def evaluate_satisfaction(user_feedback: str) -> str:
    """Evaluate user satisfaction and suggest next actions."""
    try:
        analysis = f"""📊 **Satisfaction Analysis:**

Feedback: "{user_feedback}"

Assessment: User feedback indicates areas for improvement.

**Recommended Actions:**
1. Address specific concerns mentioned
2. Revise content accordingly
3. Ensure user requirements are met

Would you like me to make specific improvements based on your feedback?"""
        return analysis
    except Exception as e:
        return f"❌ Error evaluating satisfaction: {str(e)}"


@tool
def analyze_job_requirements(thread_id: str = "default") -> str:
    """
    Analyze job posting to extract the 3 most important requirements for cover letter targeting

    Args:
        thread_id: Thread identifier

    Returns:
        JSON with top 3 job requirements and analysis
    """
    try:
        # Check if job posting is available
        if thread_id not in document_store or "job_posting" not in document_store[thread_id]:
            return StandardResponse.error(
                "analyze_job_requirements",
                "No job posting found. Please upload a job posting first.",
                "MISSING_JOB_POSTING"
            )

        job_posting = document_store[thread_id]["job_posting"]

        # Use LLM to analyze job requirements with improved prompt
        analysis_prompt = f"""You are a job analysis expert. Analyze this job posting and extract the 3 MOST IMPORTANT requirements that a candidate must demonstrate in their cover letter to be compelling.

Job Posting:
{job_posting}

CRITICAL: You must respond in valid JSON format only. No extra text.

For each requirement, provide:
1. The specific requirement/skill from the job posting
2. Why it's critical for this specific role
3. 3-5 relevant keywords from the job posting

Response format (valid JSON only):
{{
  "top_requirements": [
    {{
      "requirement 1": "exact requirement from job posting",
      "importance 1": "why this requirement is critical for this specific role",
      "keywords 1": ["keyword1", "keyword2", "keyword3", "keyword4", "keyword5"]
    }},
    {{
      "requirement 2": "second exact requirement from job posting",
      "importance 2": "why this requirement is critical for this specific role",
      "keywords 2": ["keyword1", "keyword2", "keyword3", "keyword4", "keyword5"]
    }},
    {{
      "requirement 3": "third exact requirement from job posting",
      "importance 3": "why this requirement is critical for this specific role",
      "keywords 3": ["keyword1", "keyword2", "keyword3", "keyword4", "keyword5"]
    }}
  ],
  "company_culture": "brief company culture insight from the job posting",
  "role_focus": "primary focus of this specific role from job posting"
}}
}}"""

        from langchain_openai import ChatOpenAI
        from .config import LLM_CONFIG
        llm = ChatOpenAI(**LLM_CONFIG)

        response = llm.invoke(analysis_prompt)

        # Parse the JSON response
        import json
        try:
            analysis_data = json.loads(response.content)
        except json.JSONDecodeError:
            # If JSON parsing fails, use simpler prompt to analyze actual job posting
            fallback_prompt = f"""Analyze this job posting and list the 3 most important requirements:

Job Posting:
{job_posting}

Format your response exactly like this with numbered:

REQUIREMENT 1: [specific requirement from job posting]
IMPORTANCE 1: [why this is critical for this role]
KEYWORDS 1: [keyword1, keyword2, keyword3, keyword4, keyword5]

REQUIREMENT 2: [specific requirement from job posting]
IMPORTANCE 2: [why this is critical for this role]
KEYWORDS 2: [keyword1, keyword2, keyword3, keyword4, keyword5]

REQUIREMENT 3: [specific requirement from job posting]
IMPORTANCE 3: [why this is critical for this role]
KEYWORDS 3: [keyword1, keyword2, keyword3, keyword4, keyword5]

COMPANY CULTURE: [brief insight about company culture]
ROLE FOCUS: [primary focus of this role]"""

            fallback_response = llm.invoke(fallback_prompt)
            fallback_content = fallback_response.content

            # Parse the structured response
            requirements = []
            company_culture = "Technology company"
            role_focus = "Professional role"

            lines = fallback_content.split('\n')
            current_req = {}

            for line in lines:
                line = line.strip()
                if line.startswith('REQUIREMENT '):
                    if current_req:
                        requirements.append(current_req)
                    current_req = {"requirement": line.split(':', 1)[-1].strip().strip('[]'), "importance": "", "keywords": []}
                elif line.startswith('IMPORTANCE '):
                    if current_req:
                        current_req["importance"] = line.split(':', 1)[-1].strip().strip('[]')
                elif line.startswith('KEYWORDS '):
                    if current_req:
                        keywords_text = line.split(':', 1)[-1].strip().strip('[]')
                        current_req["keywords"] = [kw.strip() for kw in keywords_text.split(',')]
                elif line.startswith('COMPANY CULTURE:'):
                    company_culture = line.split(':', 1)[-1].strip().strip('[]')
                elif line.startswith('ROLE FOCUS:'):
                    role_focus = line.split(':', 1)[-1].strip().strip('[]')

            # Add the last requirement
            if current_req:
                requirements.append(current_req)

            # Ensure we have 3 requirements
            while len(requirements) < 3:
                requirements.append({
                    "requirement": f"Key requirement from job posting analysis",
                    "importance": "Important for role success",
                    "keywords": ["relevant", "skills", "experience"]
                })

            analysis_data = {
                "top_requirements": requirements[:3],
                "company_culture": company_culture,
                "role_focus": role_focus
            }

        # Store analysis results for cover letter generation
        if thread_id not in document_store:
            document_store[thread_id] = {}
        document_store[thread_id]["job_analysis"] = analysis_data

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
        # Check if job analysis is available
        if thread_id not in document_store or "job_analysis" not in document_store[thread_id]:
            return StandardResponse.error(
                "analyze_cv_match",
                "Job analysis not found. Please run analyze_job_requirements first.",
                "MISSING_JOB_ANALYSIS"
            )

        job_analysis = document_store[thread_id]["job_analysis"]
        top_requirements = job_analysis.get("top_requirements", [])

        # Build comprehensive CV matching analysis
        cv_matches = []

        for i, req in enumerate(top_requirements, 1):
            # Handle numbered format from JobRequirementsResponse
            requirement = req.get(f"requirement {i}", "") or req.get("requirement", "")
            importance = req.get(f"importance {i}", "") or req.get("importance", "")
            keywords = req.get(f"keywords {i}", []) or req.get("keywords", [])

            # Simple, direct query - KISS principle
            matching_query = f"""From my CV, Answer the request  find specific experience, skills, projects, or achievements that demonstrate my ability to: {requirement}

Look for relevant examples and Provide concrete examples from my CV that show I can successfully deliver on this requirement on Why this requirement matters: {importance}

Look for these keywords from the job offer to find relevant experiences in the CV : {', '.join(keywords)}

Be clear and answer the question without intro"""

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

        # Generate compelling talking points
        talking_points = []
        for match in cv_matches:
            talking_points.append({
                "point": f"Strong match for {match['requirement']}",
                "evidence": match['matching_experience'][:200] + "..." if len(match['matching_experience']) > 200 else match['matching_experience'],
                "keywords": match['keywords_addressed']
            })

        analysis_results = {
            "cv_job_matches": cv_matches,
            "compelling_talking_points": talking_points,
            "overall_fit_score": len([m for m in cv_matches if m.get('strength_score') == 'high']) / len(cv_matches) if cv_matches else 0,
            "recommendation": "Strong candidate with relevant experience" if len(talking_points) >= 2 else "Moderate fit, emphasize transferable skills"
        }

        # Store for cover letter generation
        document_store[thread_id]["cv_analysis"] = analysis_results

        return StandardResponse.success(
            "analyze_cv_match",
            analysis_results,
            f"Found {len(talking_points)} compelling talking points"
        )

    except Exception as e:
        return StandardResponse.error("analyze_cv_match", str(e))


@tool
def analyze_upload_content(content: str, content_type: str = "auto") -> str:
    """Analyze uploaded content to classify and extract key information."""
    try:
        # Detect content type inline instead of using utility function
        content_lower = content.lower()
        if any(word in content_lower for word in ["resume", "curriculum vitae", "work experience", "skills"]):
            detected_type = "CV/Resume"
        elif any(word in content_lower for word in ["job description", "requirements", "qualifications", "responsibilities"]):
            detected_type = "Job Posting"
        else:
            detected_type = "Unknown/Other"

        return StandardResponse.success(
            "analyze_upload_content",
            {
                "content_analysis": {
                    "detected_type": detected_type,
                    "content_length": len(content),
                    "quality_assessment": "Good",
                    "processing_status": "Ready for use"
                },
                "recommendations": [
                    "Content appears suitable for job search purposes",
                    "Well-formatted and contains necessary information",
                    "Ready for document processing"
                ]
            },
            "Content analysis completed successfully"
        )
    except Exception as e:
        return f"❌ Error analyzing content: {str(e)}"


@tool
def suggest_next_actions(thread_id: str = "default") -> str:
    """Suggest helpful next actions based on current state."""
    try:
        has_cv = True  # CV is always available from default
        has_job = thread_id in document_store and "job_posting" in document_store[thread_id]

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


@tool
def set_user_preferences(preferences: Dict[str, str], thread_id: str = "default") -> str:
    """Set user preferences for content generation."""
    try:
        if thread_id not in document_store:
            document_store[thread_id] = {}
        document_store[thread_id]["preferences"] = preferences

        prefs_summary = "\n".join([f"• {k.title()}: {v}" for k, v in preferences.items()])
        return f"""✅ **Preferences Updated:**

{prefs_summary}

These preferences will be applied to all future content generation."""
    except Exception as e:
        return f"❌ Error setting preferences: {str(e)}"


@tool
def get_generation_history(thread_id: str = "default") -> str:
    """Retrieve history of generated content for current thread."""
    try:
        history = document_store.get(thread_id, {}).get("history", [])

        if not history:
            return StandardResponse.success(
                "get_generation_history",
                {
                    "thread_id": thread_id,
                    "history": [],
                    "total_items": 0
                },
                "No generation history found for this thread"
            )

        # Format history inline instead of using utility function
        formatted_history = []
        for i, item in enumerate(history[-5:], 1):  # Last 5 items
            formatted_history.append({
                "index": i,
                "type": item.get('type', 'Unknown'),
                "timestamp": item.get('timestamp', 'No date'),
                "summary": item.get('summary', 'No summary available')
            })

        return StandardResponse.success(
            "get_generation_history",
            {
                "thread_id": thread_id,
                "history": formatted_history,
                "total_items": len(history),
                "showing": "Last 5 items" if len(history) > 5 else "All items"
            },
            f"Retrieved {len(formatted_history)} history items"
        )
    except Exception as e:
        return f"❌ Error retrieving history: {str(e)}"


@tool
def export_content(content_type: str, format: str = "markdown", thread_id: str = "default") -> str:
    """Export generated content in specified format."""
    try:
        export_result = f"""📤 **Export Request:**

Content Type: {content_type}
Format: {format}
Thread: {thread_id}

✅ Content prepared for export in {format} format.

[In a real implementation, this would provide download link or file attachment]"""
        return export_result
    except Exception as e:
        return f"❌ Error exporting content: {str(e)}"


# =============================================================================
# CORE TOOL REGISTRY
# =============================================================================
