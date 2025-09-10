"""
Standardized JSON Response Schemas for Job Search Agent Tools
Ensures consistent output format across all tools
"""

import json
from typing import Dict, Any, List, Optional
from datetime import datetime


class StandardResponse:
    """Base class for standardized JSON responses"""

    @staticmethod
    def success(
        tool_name: str,
        data: Any,
        message: str = "Operation completed successfully",
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Generate standardized success response"""
        response = {
            "status": "success",
            "tool": tool_name,
            "timestamp": datetime.now().isoformat(),
            "message": message,
            "data": data,
            "metadata": metadata or {}
        }
        return json.dumps(response, indent=2, ensure_ascii=False)

    @staticmethod
    def error(
        tool_name: str,
        error_message: str,
        error_code: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Generate standardized error response"""
        response = {
            "status": "error",
            "tool": tool_name,
            "timestamp": datetime.now().isoformat(),
            "error": {
                "message": error_message,
                "code": error_code or "GENERAL_ERROR"
            },
            "metadata": metadata or {}
        }
        return json.dumps(response, indent=2, ensure_ascii=False)


class DocumentStatusResponse:
    """Schema for document status responses"""

    @staticmethod
    def create(
        cv_status: str,
        job_posting_status: str,
        index_status: str,
        cv_sample: str,
        thread_id: str,
        suggestions: List[str]
    ) -> str:
        data = {
            "thread_id": thread_id,
            "documents": {
                "cv": {
                    "status": cv_status,
                    "indexed": index_status == "✅ Indexed",
                    "sample": cv_sample[:200] + "..." if len(cv_sample) > 200 else cv_sample
                },
                "job_posting": {
                    "status": job_posting_status,
                    "available": job_posting_status == "✅ Uploaded"
                }
            },
            "next_steps": suggestions
        }

        return StandardResponse.success(
            "get_document_status",
            data,
            "Document status retrieved successfully"
        )


class PersonalInfoResponse:
    """Schema for personal information extraction responses"""

    @staticmethod
    def create(
        contact_info: str,
        location: str,
        languages: str,
        name: str,
        email: str,
        professional_title: str
    ) -> str:
        data = {
            "contact_information": {
                "raw_response": contact_info,
                "parsed": {
                    "name": name,
                    "email": email,
                    "location": location
                }
            },
            "location": location,
            "languages": languages,
            "professional_title": professional_title
        }

        return StandardResponse.success(
            "extract_personal_info",
            data,
            "Personal information extracted successfully"
        )


class CoverLetterResponse:
    """Schema for cover letter generation responses"""

    @staticmethod
    def create(
        cover_letter_content: str,
        personal_info_used: Dict[str, str],
        job_info_used: Dict[str, str],
        language: str = "en"
    ) -> str:
        data = {
            "cover_letter": {
                "content": cover_letter_content,
                "language": language,
                "generated_at": datetime.now().isoformat()
            },
            "extraction_details": {
                "personal_info": personal_info_used,
                "job_info": job_info_used
            },
            "generation_metadata": {
                "template_version": "v2.0",
                "rag_enabled": True,
                "anti_hallucination": True
            }
        }

        return StandardResponse.success(
            "generate_cover_letter",
            data,
            "Cover letter generated successfully"
        )


class SearchResponse:
    """Schema for CV search responses"""

    @staticmethod
    def create(
        query: str,
        answer: str,
        context_count: int,
        relevant_sections: List[str] = None
    ) -> str:
        data = {
            "query": query,
            "answer": answer,
            "context": {
                "sections_found": context_count,
                "relevant_sections": relevant_sections or []
            }
        }

        return StandardResponse.success(
            "search_cv_details",
            data,
            f"Found {context_count} relevant sections"
        )


class JobRequirementsResponse:
    """Schema for job requirements analysis responses"""

    @staticmethod
    def create(
        top_requirements: List[Dict[str, Any]],
        company_culture: str,
        role_focus: str
    ) -> str:
        # Convert to numbered format for proper schema compliance
        numbered_requirements = []
        for i, req in enumerate(top_requirements, 1):
            numbered_req = {
                f"requirement {i}": req.get("requirement", ""),
                f"importance {i}": req.get("importance", ""),
                f"keywords {i}": req.get("keywords", [])
            }
            numbered_requirements.append(numbered_req)

        data = {
            "top_requirements": numbered_requirements,
            "company_culture": company_culture,
            "role_focus": role_focus
        }

        return StandardResponse.success(
            "analyze_job_requirements",
            data,
            f"Identified {len(top_requirements)} key requirements"
        )


class UploadResponse:
    """Schema for document upload responses"""

    @staticmethod
    def create(
        document_type: str,
        content_length: int,
        analysis_result: str,
        language_detected: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        data = {
            "document_type": document_type,
            "upload_details": {
                "content_length": content_length,
                "language": language_detected,
                "processed_at": datetime.now().isoformat()
            },
            "analysis": analysis_result,
            "metadata": metadata or {}
        }

        return StandardResponse.success(
            f"upload_{document_type}",
            data,
            f"{document_type.title()} uploaded and analyzed successfully"
        )
