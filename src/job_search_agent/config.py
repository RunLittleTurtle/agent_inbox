"""
Job Search Agent Configuration
Centralizes all configuration settings and defaults
"""
import os
from typing import Dict, Any, List
from dataclasses import dataclass
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


# =============================================================================
# LLM CONFIGURATION
# =============================================================================

@dataclass
class LLMConfig:
    """LLM configuration settings"""
    model: str = "claude-sonnet-4-20250514"
    temperature: float = 0.0
    max_tokens: int = 2000
    timeout: int = 60
    max_retries: int = 3


LLM_CONFIG = {
    "model": os.getenv("JOB_SEARCH_LLM_MODEL", "claude-sonnet-4-20250514"),
    "temperature": float(os.getenv("JOB_SEARCH_LLM_TEMPERATURE", "0.0")),
    "max_tokens": int(os.getenv("JOB_SEARCH_LLM_MAX_TOKENS", "2000")),
    "timeout": int(os.getenv("JOB_SEARCH_LLM_TIMEOUT", "60")),
    "max_retries": int(os.getenv("JOB_SEARCH_LLM_MAX_RETRIES", "3")),
    "anthropic_api_key": os.getenv("ANTHROPIC_API_KEY")
}


# =============================================================================
# STORAGE CONFIGURATION
# =============================================================================

@dataclass
class StorageConfig:
    """Storage configuration settings"""
    base_path: str = "./job_search_data"
    documents_path: str = "./job_search_data/documents"
    vectors_path: str = "./job_search_data/vectors"
    threads_path: str = "./job_search_data/threads"
    cleanup_days: int = 30
    max_file_size_mb: int = 10


STORAGE_CONFIG = {
    "base_path": os.getenv("JOB_SEARCH_STORAGE_PATH", "./job_search_data"),
    "documents_path": os.getenv("JOB_SEARCH_DOCUMENTS_PATH", "./job_search_data/documents"),
    "vectors_path": os.getenv("JOB_SEARCH_VECTORS_PATH", "./job_search_data/vectors"),
    "threads_path": os.getenv("JOB_SEARCH_THREADS_PATH", "./job_search_data/threads"),
    "cleanup_days": int(os.getenv("JOB_SEARCH_CLEANUP_DAYS", "30")),
    "max_file_size_mb": int(os.getenv("JOB_SEARCH_MAX_FILE_SIZE_MB", "10"))
}


# =============================================================================
# PROCESSING CONFIGURATION
# =============================================================================

@dataclass
class ProcessingConfig:
    """Processing configuration settings"""
    chunk_size: int = 500
    chunk_overlap: int = 50
    quality_threshold: int = 8
    max_iterations: int = 3
    rag_top_k: int = 5
    vector_dimensions: int = 384  # For sentence-transformers


PROCESSING_CONFIG = {
    "chunk_size": int(os.getenv("JOB_SEARCH_CHUNK_SIZE", "500")),  # LangGraph best practice with CV optimization
    "chunk_overlap": int(os.getenv("JOB_SEARCH_CHUNK_OVERLAP", "100")),  # 20% overlap (LangGraph standard)
    "quality_threshold": int(os.getenv("JOB_SEARCH_QUALITY_THRESHOLD", "8")),
    "max_iterations": int(os.getenv("JOB_SEARCH_MAX_ITERATIONS", "3")),
    "rag_top_k": int(os.getenv("JOB_SEARCH_RAG_TOP_K", "8")),  # LangGraph-optimized (higher than standard for CV)
    "vector_dimensions": int(os.getenv("JOB_SEARCH_VECTOR_DIMENSIONS", "384"))
}


# =============================================================================
# USER PREFERENCE DEFAULTS
# =============================================================================

@dataclass
class DefaultUserPreferences:
    """Default user preferences"""
    cover_letter_length: str = "short"  # "short", "medium", "long"
    tone: str = "professional"           # "casual", "professional", "enthusiastic"
    format: str = "traditional"          # "modern", "traditional", "creative"
    language: str = "french"             # "english", "french", "bilingual"
    export_format: str = "markdown"      # "markdown", "pdf", "docx"


DEFAULT_USER_PREFERENCES = {
    "cover_letter_length": "medium",
    "tone": "professional",
    "format": "traditional",
    "language": "french",
    "export_format": "markdown"
}


# =============================================================================
# TEMPLATE SYSTEM CONFIGURATION
# =============================================================================

TEMPLATE_CONFIG = {
    "cover_letter_templates": {
        "traditional": {
            "structure": ["header", "opening", "body", "closing", "signature"],
            "tone": "formal",
            "length_limits": {"short": 250, "medium": 400, "long": 600}
        },
        "modern": {
            "structure": ["opening", "highlights", "motivation", "closing"],
            "tone": "professional_casual",
            "length_limits": {"short": 200, "medium": 350, "long": 500}
        },
        "creative": {
            "structure": ["hook", "story", "value_prop", "call_to_action"],
            "tone": "engaging",
            "length_limits": {"short": 180, "medium": 320, "long": 450}
        }
    },
    "industry_variations": {
        "tech": {"keywords": ["innovation", "technical", "scalable", "agile"]},
        "finance": {"keywords": ["analytical", "precise", "compliance", "strategic"]},
        "healthcare": {"keywords": ["compassionate", "detailed", "regulatory", "patient-focused"]},
        "marketing": {"keywords": ["creative", "data-driven", "brand", "growth"]},
        "education": {"keywords": ["pedagogical", "inclusive", "developmental", "research"]}
    }
}


# =============================================================================
# WORKFLOW CONFIGURATION
# =============================================================================

@dataclass
class WorkflowConfig:
    """Workflow configuration settings"""
    enable_interrupts: bool = False
    auto_quality_review: bool = True
    enable_rag_by_default: bool = True
    parallel_processing: bool = False  # MVP: Keep simple
    debug_mode: bool = False


WORKFLOW_CONFIG = {
    "enable_interrupts": os.getenv("JOB_SEARCH_ENABLE_INTERRUPTS", "false").lower() == "true",
    "auto_quality_review": os.getenv("JOB_SEARCH_AUTO_QUALITY", "true").lower() == "true",
    "enable_rag_by_default": os.getenv("JOB_SEARCH_ENABLE_RAG", "true").lower() == "true",
    "parallel_processing": os.getenv("JOB_SEARCH_PARALLEL", "false").lower() == "true",
    "debug_mode": os.getenv("JOB_SEARCH_DEBUG", "false").lower() == "true"
}


# =============================================================================
# SECURITY CONFIGURATION
# =============================================================================

SECURITY_CONFIG = {
    "max_upload_size_mb": 10,
    "allowed_file_types": [".txt", ".md", ".docx", ".pdf"],
    "sanitize_uploads": True,
    "enable_content_filtering": True,
    "rate_limit_per_minute": 60,
    "session_timeout_minutes": 120
}


# =============================================================================
# LOGGING CONFIGURATION
# =============================================================================

LOGGING_CONFIG = {
    "level": os.getenv("JOB_SEARCH_LOG_LEVEL", "INFO"),
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "file": os.getenv("JOB_SEARCH_LOG_FILE", "job_search_agent.log"),
    "max_file_size_mb": 50,
    "backup_count": 5,
    "enable_console": True
}


# =============================================================================
# INTEGRATION CONFIGURATION
# =============================================================================

INTEGRATION_CONFIG = {
    "openai_api_key": os.getenv("OPENAI_API_KEY"),
    "anthropic_api_key": os.getenv("ANTHROPIC_API_KEY"),
    "sentence_transformers_model": "all-MiniLM-L6-v2",
    "faiss_index_type": "IndexFlatIP",  # Inner product for cosine similarity
    "embedding_cache_ttl_hours": 24
}


# =============================================================================
# FEATURE FLAGS
# =============================================================================

FEATURE_FLAGS = {
    "enable_multilingual": True,
    "enable_industry_templates": True,
    "enable_rag_search": True,
    "enable_quality_scoring": True,
    "enable_export_formats": True,
    "enable_batch_processing": False,  # Future feature
    "enable_ai_feedback": True,
    "enable_template_customization": False  # Future feature
}


# =============================================================================
# VALIDATION RULES
# =============================================================================

VALIDATION_RULES = {
    "cv_min_length": 100,
    "cv_max_length": 10000,
    "job_posting_min_length": 50,
    "job_posting_max_length": 5000,
    "cover_letter_min_length": 150,
    "cover_letter_max_length": 800,
    "thread_id_pattern": r"^[a-zA-Z0-9_-]+$",
    "required_cv_sections": ["experience", "skills"],
    "required_job_fields": ["requirements", "responsibilities"]
}


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def get_config(config_name: str) -> Dict[str, Any]:
    """Get configuration by name"""
    configs = {
        "llm": LLM_CONFIG,
        "storage": STORAGE_CONFIG,
        "processing": PROCESSING_CONFIG,
        "user_preferences": DEFAULT_USER_PREFERENCES,
        "template": TEMPLATE_CONFIG,
        "workflow": WORKFLOW_CONFIG,
        "security": SECURITY_CONFIG,
        "logging": LOGGING_CONFIG,
        "integration": INTEGRATION_CONFIG,
        "features": FEATURE_FLAGS,
        "validation": VALIDATION_RULES
    }

    return configs.get(config_name, {})


def validate_config() -> List[str]:
    """Validate configuration settings"""
    issues = []

    # Check required API keys
    if not INTEGRATION_CONFIG.get("ANTHROPIC_API_KEY"):
        issues.append("Missing ANTHROPIC_API_KEY environment variable")

    # Check storage paths
    try:
        os.makedirs(STORAGE_CONFIG["base_path"], exist_ok=True)
    except Exception as e:
        issues.append(f"Cannot create storage directory: {e}")

    # Check processing limits
    if PROCESSING_CONFIG["chunk_size"] < 100:
        issues.append("Chunk size too small (minimum 100)")

    if PROCESSING_CONFIG["quality_threshold"] < 1 or PROCESSING_CONFIG["quality_threshold"] > 10:
        issues.append("Quality threshold must be between 1-10")

    # Check LLM config
    if LLM_CONFIG["temperature"] < 0 or LLM_CONFIG["temperature"] > 1:
        issues.append("LLM temperature must be between 0-1")

    if LLM_CONFIG["max_tokens"] < 100:
        issues.append("LLM max_tokens too low (minimum 100)")

    return issues


def get_user_preferences_schema() -> Dict[str, Dict[str, Any]]:
    """Get schema for user preferences validation"""
    return {
        "cover_letter_length": {
            "type": "string",
            "choices": ["short", "medium", "long"],
            "default": "medium"
        },
        "tone": {
            "type": "string",
            "choices": ["casual", "professional", "enthusiastic"],
            "default": "professional"
        },
        "format": {
            "type": "string",
            "choices": ["modern", "traditional", "creative"],
            "default": "traditional"
        },
        "language": {
            "type": "string",
            "choices": ["english", "french", "bilingual"],
            "default": "french"
        },
        "export_format": {
            "type": "string",
            "choices": ["markdown", "pdf", "docx"],
            "default": "markdown"
        }
    }


def load_environment_overrides() -> None:
    """Load any environment variable overrides"""
    global LLM_CONFIG, STORAGE_CONFIG, PROCESSING_CONFIG

    # Update configs with environment variables
    for key, value in LLM_CONFIG.items():
        env_key = f"JOB_SEARCH_LLM_{key.upper()}"
        if env_key in os.environ:
            if isinstance(value, bool):
                LLM_CONFIG[key] = os.environ[env_key].lower() == "true"
            elif isinstance(value, int):
                LLM_CONFIG[key] = int(os.environ[env_key])
            elif isinstance(value, float):
                LLM_CONFIG[key] = float(os.environ[env_key])
            else:
                LLM_CONFIG[key] = os.environ[env_key]


def get_feature_flag(flag_name: str) -> bool:
    """Get feature flag value"""
    return FEATURE_FLAGS.get(flag_name, False)


def is_debug_mode() -> bool:
    """Check if debug mode is enabled"""
    return WORKFLOW_CONFIG.get("debug_mode", False)


def get_quality_threshold() -> int:
    """Get quality threshold for reviews"""
    return PROCESSING_CONFIG.get("quality_threshold", 8)


def get_max_iterations() -> int:
    """Get maximum iterations for improvement"""
    return PROCESSING_CONFIG.get("max_iterations", 3)


# =============================================================================
# INITIALIZATION
# =============================================================================

def initialize_config() -> Dict[str, Any]:
    """Initialize and validate all configuration"""
    load_environment_overrides()

    issues = validate_config()
    if issues:
        print("Configuration issues found:")
        for issue in issues:
            print(f"  - {issue}")

    return {
        "llm": LLM_CONFIG,
        "storage": STORAGE_CONFIG,
        "processing": PROCESSING_CONFIG,
        "user_preferences": DEFAULT_USER_PREFERENCES,
        "workflow": WORKFLOW_CONFIG,
        "features": FEATURE_FLAGS,
        "validation_issues": issues
    }


# Initialize on import
_config = initialize_config()

if __name__ == "__main__":
    print("Job Search Agent Configuration:")
    print("=" * 50)

    for section, config in _config.items():
        if section != "validation_issues":
            print(f"\n{section.upper()}:")
            for key, value in config.items():
                print(f"  {key}: {value}")

    if _config["validation_issues"]:
        print(f"\nValidation Issues:")
        for issue in _config["validation_issues"]:
            print(f"  - {issue}")
    else:
        print("\n✅ Configuration validation passed!")
