"""
Pydantic v2 models for structured LLM output
Ensures consistent, validated responses from LLM calls
"""
from typing import List, Dict, Optional
from pydantic import BaseModel, Field


class JobRequirement(BaseModel):
    """Single job requirement with importance and keywords"""
    requirement: str = Field(..., description="Specific requirement from job posting")
    importance: str = Field(..., description="Why this requirement is critical for this role")
    keywords: List[str] = Field(..., description="3-5 relevant keywords from job posting")


class JobAnalysis(BaseModel):
    """Complete job analysis with top requirements"""
    top_requirements: List[JobRequirement] = Field(..., description="Top 3 most important requirements")
    company_culture: str = Field(..., description="Brief company culture insight from job posting")
    role_focus: str = Field(..., description="Primary focus of this specific role")


class CVMatch(BaseModel):
    """CV experience matching a job requirement"""
    requirement: str = Field(..., description="The job requirement this addresses")
    matching_experience: str = Field(..., description="Specific CV experience that matches")
    keywords_addressed: List[str] = Field(..., description="Keywords from requirement found in CV")
    strength_score: str = Field(..., description="Assessment of match strength: high, medium, low")


class TalkingPoint(BaseModel):
    """Compelling talking point for cover letter"""
    point: str = Field(..., description="Short title of the talking point")
    evidence: str = Field(..., description="Evidence from CV supporting this point")
    keywords: List[str] = Field(..., description="Relevant keywords for this point")


class CVAnalysis(BaseModel):
    """Complete CV analysis with matches and talking points"""
    cv_job_matches: List[CVMatch] = Field(..., description="CV experiences matching job requirements")
    compelling_talking_points: List[TalkingPoint] = Field(..., description="Key talking points for cover letter")
    overall_fit_score: float = Field(..., description="Overall fit score between 0 and 1")
    recommendation: str = Field(..., description="Brief recommendation for candidacy")


class PersonalInfo(BaseModel):
    """Structured personal information from CV"""
    full_name: str = Field(..., description="Full name from CV header")
    email: Optional[str] = Field(None, description="Email address if present")
    phone: Optional[str] = Field(None, description="Phone number if present")
    location: Optional[str] = Field(None, description="City, province/state, country")
    languages: List[str] = Field(default_factory=list, description="Languages spoken")
    current_title: Optional[str] = Field(None, description="Current job title")
    current_company: Optional[str] = Field(None, description="Current company name if present")
