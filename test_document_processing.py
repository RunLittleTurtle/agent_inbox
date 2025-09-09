#!/usr/bin/env python3
"""
Test Document Processing - CV Loading and Analysis
Tests the document processing flow specifically to verify CV analysis and job report generation
"""

import sys
import os
import asyncio
from pathlib import Path

# Add the src directory to Python path
current_dir = Path(__file__).parent
src_dir = current_dir / "src"
sys.path.insert(0, str(src_dir))

# Now import the orchestrator
try:
    from job_search_agent.job_search_orchestrator import JobSearchOrchestrator
    from job_search_agent.state import JobSearchState, create_initial_state
    from job_search_agent.tools import upload_cv, upload_job_posting
    from langchain_core.messages import HumanMessage
    print("✅ All imports successful!")
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)


def load_cv_from_docs():
    """Load CV from docs folder"""
    cv_path = current_dir / "src" / "job_search_agent" / "docs" / "CV - Samuel Audette_Technical_Product_Manager_AI_2025_09.md"

    if cv_path.exists():
        with open(cv_path, 'r', encoding='utf-8') as f:
            cv_content = f.read()
        print(f"✅ CV loaded: {len(cv_content)} characters")
        return cv_content
    else:
        print(f"❌ CV not found at: {cv_path}")
        return None


def create_sample_job_posting():
    """Create a sample job posting for testing"""
    job_posting = """
# Senior Product Manager - AI & Machine Learning
**Company**: TechCorp Inc.
**Location**: Montreal, Quebec
**Type**: Full-time

## About the Role
We are seeking a Senior Product Manager to lead our AI and machine learning product initiatives. This role requires a strong technical background, experience with agile methodologies, and the ability to work with cross-functional teams.

## Key Responsibilities
- Define and execute product strategy for AI/ML products
- Work closely with engineering teams using Python, APIs, and cloud technologies
- Lead agile development processes and manage product roadmaps
- Conduct user research and analyze product metrics
- Collaborate with designers, developers, and stakeholders

## Required Qualifications
- 5+ years of product management experience
- Experience with AI/ML technologies, LangChain, or similar frameworks
- Strong background in agile methodologies (Scrum/Kanban)
- Technical skills: Python, APIs, cloud platforms (GCP preferred)
- Bilingual (French/English) is a strong asset
- Experience with UX research and data analysis

## Nice to Have
- Experience with LangGraph, OpenAI APIs
- Background in SaaS products
- Military or leadership experience
- Startup or agency experience

## What We Offer
- Competitive salary and benefits
- Remote-friendly work environment
- Professional development opportunities
- Work with cutting-edge AI technologies
"""
    print(f"✅ Sample job posting created: {len(job_posting)} characters")
    return job_posting


async def test_document_loading():
    """Test CV and job posting loading"""
    print("\n🧪 Test 1: Document Loading")

    try:
        # Load CV
        cv_content = load_cv_from_docs()
        if not cv_content:
            return False

        # Create job posting
        job_posting = create_sample_job_posting()

        # Test upload tools
        cv_result = upload_cv(cv_content, "test_thread")
        print(f"📄 CV upload result: {cv_result[:100]}...")

        job_result = upload_job_posting(job_posting, "test_thread")
        print(f"📋 Job posting upload result: {job_result[:100]}...")

        return True

    except Exception as e:
        print(f"❌ Document loading failed: {e}")
        return False


async def test_document_processor_node():
    """Test the document processor node directly"""
    print("\n🧪 Test 2: Document Processor Node")

    try:
        # Load documents
        cv_content = load_cv_from_docs()
        job_posting = create_sample_job_posting()

        if not cv_content:
            return False

        # Create orchestrator
        orchestrator = JobSearchOrchestrator()

        # Create initial state with documents
        state = create_initial_state()
        state["cv_content"] = cv_content
        state["job_posting"] = job_posting
        state["current_task"] = "analyze_documents"

        print(f"📊 Initial state created with CV ({len(cv_content)} chars) and job posting ({len(job_posting)} chars)")

        # Test document processor node directly
        config = {"configurable": {"thread_id": "test_doc_processing"}}

        print("🚀 Running document processor node...")
        result_state = await orchestrator.document_processor_node(state, config)

        # Check results
        job_analysis = result_state.get("job_analysis_report", "")
        cv_analysis = result_state.get("cv_analysis_report", "")

        print(f"📋 Job Analysis Report: {len(job_analysis)} chars")
        if job_analysis:
            print(f"   Preview: {job_analysis[:200]}...")
        else:
            print("   ❌ No job analysis generated")

        print(f"📄 CV Analysis Report: {len(cv_analysis)} chars")
        if cv_analysis:
            print(f"   Preview: {cv_analysis[:200]}...")
        else:
            print("   ❌ No CV analysis generated")

        return bool(job_analysis and cv_analysis)

    except Exception as e:
        print(f"❌ Document processor test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_rag_indexer_node():
    """Test the RAG indexer node"""
    print("\n🧪 Test 3: RAG Indexer Node")

    try:
        # Load CV
        cv_content = load_cv_from_docs()
        if not cv_content:
            return False

        # Create orchestrator
        orchestrator = JobSearchOrchestrator()

        # Create state with CV
        state = create_initial_state()
        state["cv_content"] = cv_content

        # Test RAG indexer node
        config = {"configurable": {"thread_id": "test_rag_indexing"}}

        print("🚀 Running RAG indexer node...")
        result_state = await orchestrator.rag_indexer_node(state, config)

        # Check indexing status
        doc_status = result_state.get("document_status", {})
        cv_indexed = doc_status.get("cv_indexed", False)

        print(f"📊 CV Indexed: {cv_indexed}")

        if cv_indexed:
            print("✅ RAG indexing successful")
        else:
            print("❌ RAG indexing failed")

        return cv_indexed

    except Exception as e:
        print(f"❌ RAG indexer test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_complete_document_flow():
    """Test the complete document processing flow"""
    print("\n🧪 Test 4: Complete Document Flow")

    try:
        # Load documents
        cv_content = load_cv_from_docs()
        job_posting = create_sample_job_posting()

        if not cv_content:
            return False

        # Create orchestrator
        orchestrator = JobSearchOrchestrator()

        # Create complete workflow
        workflow = orchestrator.create_complete_workflow()

        # Create initial state with documents pre-loaded
        initial_state = {
            "messages": [HumanMessage(content="Please analyze my CV and the job posting, then generate a personalized cover letter")],
            "cv_content": cv_content,
            "job_posting": job_posting,
            "current_task": "analyze_documents"
        }

        config = {
            "configurable": {"thread_id": "test_complete_flow"},
            "recursion_limit": 10  # Prevent infinite loops
        }

        print("🚀 Running complete document flow...")
        result = await workflow.ainvoke(initial_state, config)

        # Analyze results
        print(f"📊 Final state keys: {list(result.keys())}")
        print(f"📨 Messages: {len(result.get('messages', []))}")

        job_analysis = result.get("job_analysis_report", "")
        cv_analysis = result.get("cv_analysis_report", "")
        cover_letter = result.get("cover_letter", "")

        print(f"📋 Job Analysis: {len(job_analysis)} chars")
        print(f"📄 CV Analysis: {len(cv_analysis)} chars")
        print(f"💌 Cover Letter: {len(cover_letter)} chars")

        if job_analysis:
            print(f"\n📋 Job Analysis Preview:\n{job_analysis[:300]}...\n")

        if cv_analysis:
            print(f"📄 CV Analysis Preview:\n{cv_analysis[:300]}...\n")

        if cover_letter:
            print(f"💌 Cover Letter Preview:\n{cover_letter[:300]}...\n")

        # Check if personalization occurred
        samuel_mentions = cv_content.lower().count("samuel")
        cover_samuel_mentions = cover_letter.lower().count("samuel") if cover_letter else 0

        print(f"🔍 Personalization Check:")
        print(f"   Samuel mentions in CV: {samuel_mentions}")
        print(f"   Samuel mentions in cover letter: {cover_samuel_mentions}")

        if cover_samuel_mentions > 0:
            print("✅ Cover letter appears personalized!")
        else:
            print("❌ Cover letter not personalized")

        return bool(job_analysis and cv_analysis)

    except Exception as e:
        print(f"❌ Complete flow test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all document processing tests"""
    print("🚀 Testing Document Processing Flow")
    print("=" * 60)

    results = []

    # Run tests
    results.append(await test_document_loading())
    results.append(await test_document_processor_node())
    results.append(await test_rag_indexer_node())
    results.append(await test_complete_document_flow())

    # Summary
    print("\n" + "=" * 60)
    print("🏁 Document Processing Test Results")

    passed = sum(results)
    total = len(results)

    print(f"✅ Passed: {passed}/{total}")

    if passed == total:
        print("🎉 All document processing tests passed!")
        print("📊 CV analysis and job reports should now be working!")
    else:
        failed = total - passed
        print(f"❌ {failed} tests failed. Check the logs above.")
        print("🔧 Issues found in document processing pipeline.")

    return passed == total


if __name__ == "__main__":
    """Main execution for document processing tests"""
    print("🔧 Setting up document processing test environment...")

    # Check if we're in the right directory
    if not (Path.cwd() / "src" / "job_search_agent").exists():
        print("❌ Please run this script from the project root directory")
        sys.exit(1)

    print("📁 Project structure validated")

    # Run async tests
    try:
        success = asyncio.run(main())
        print(f"\n{'🎉 SUCCESS!' if success else '❌ FAILED!'}")
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⚠️ Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
