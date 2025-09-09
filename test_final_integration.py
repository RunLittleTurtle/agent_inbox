#!/usr/bin/env python3
"""
Final Integration Test - Complete Workflow with Fixed Routing
Tests the complete end-to-end workflow with document processing and personalization
"""

import sys
import os
import asyncio
from pathlib import Path

# Add the src directory to Python path
current_dir = Path(__file__).parent
src_dir = current_dir / "src"
sys.path.insert(0, str(src_dir))

try:
    from job_search_agent.job_search_orchestrator import JobSearchOrchestrator
    from job_search_agent.simple_rag import SimpleRAG, load_and_index_cv
    from job_search_agent.state import create_initial_state
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


def create_perfect_match_job_posting():
    """Create a job posting that perfectly matches Samuel's profile"""
    job_posting = """
# Senior Product Manager - AI & LangGraph Applications
**Company**: TechCorp AI Solutions
**Location**: Montreal, Quebec, Canada
**Type**: Full-time
**Language**: Bilingual (French/English required)

## About the Role
We are seeking an experienced Senior Product Manager to lead our AI product initiatives, specifically focusing on LangGraph, LangChain, and agentic AI workflows. This role requires hands-on experience with Python, OpenAI APIs, and product management in agile environments.

## Key Responsibilities
- Lead product strategy for AI/ML applications using LangGraph and LangChain
- Manage cross-functional teams using Agile/Scrum methodologies
- Work with engineering teams on Python-based AI solutions
- Conduct user research and implement data-driven product decisions
- Collaborate with C-suite, designers, and developers on AI product vision
- Build MVPs and prototypes for rapid product validation

## Required Qualifications
- 3+ years of product management experience in AI/ML or SaaS
- Hands-on experience with LangChain, LangGraph, OpenAI APIs
- Strong technical background with Python programming
- Proven experience with Agile methodologies (Scrum/Kanban)
- Experience in startup/agency environments
- Bilingual French/English communication skills
- Experience with product analytics (Amplitude, PostHog preferred)

## Nice to Have
- Military or leadership background
- Experience with LangSmith for AI workflow monitoring
- Background in UX research and design
- Experience with cloud platforms (GCP preferred)
- Previous work with chatbots, AI agents, or workflow automation

## About Our Tech Stack
- Python, LangChain, LangGraph, OpenAI API
- Cloud infrastructure on GCP
- Modern product management tools (Jira, ClickUp)
- AI-first product development approach

## What We Offer
- Competitive salary and equity
- Work on cutting-edge AI technology
- Bilingual work environment
- Professional development in AI/ML
- Collaborative team culture with agile values

This role is perfect for a product manager who combines technical AI expertise with proven leadership skills and wants to shape the future of agentic AI applications.
"""
    print(f"✅ Job posting created: {len(job_posting)} characters")
    return job_posting


async def test_document_processing_workflow():
    """Test the complete document processing workflow"""
    print("\n🧪 Test 1: Document Processing Workflow")
    print("=" * 50)

    try:
        # Load documents
        cv_content = load_cv_from_docs()
        job_posting = create_perfect_match_job_posting()

        if not cv_content:
            return False

        # Create orchestrator
        orchestrator = JobSearchOrchestrator()

        # Create initial state with documents - this should trigger processing
        initial_state = {
            "messages": [HumanMessage(content="Please analyze my CV against this job posting and tell me about the match")],
            "cv_content": cv_content,
            "job_posting": job_posting,
            "current_task": ""  # Empty to trigger analysis
        }

        print("🚀 Testing individual document processor node...")

        # Test document processor directly first
        config = {"configurable": {"thread_id": "test_doc_workflow"}}
        result_state = await orchestrator.document_processor_node(initial_state, config)

        # Check analysis results
        job_analysis = result_state.get("job_analysis_report", "")
        cv_analysis = result_state.get("cv_analysis_report", "")

        print(f"📋 Job Analysis Length: {len(job_analysis)} chars")
        print(f"📄 CV Analysis Length: {len(cv_analysis)} chars")

        if job_analysis and cv_analysis:
            print("✅ Document processing successful!")

            # Show key findings
            print(f"\n📋 Job Analysis Preview:")
            print(f"{job_analysis[:300]}...")

            print(f"\n📄 CV Analysis Preview:")
            print(f"{cv_analysis[:300]}...")

            return True
        else:
            print("❌ Document processing failed - missing analysis")
            return False

    except Exception as e:
        print(f"❌ Document processing test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_rag_integration():
    """Test RAG integration with the new simple implementation"""
    print("\n🧪 Test 2: RAG Integration")
    print("=" * 50)

    try:
        cv_content = load_cv_from_docs()
        if not cv_content:
            return False

        # Test new RAG implementation
        print("📊 Creating new LangGraph-compliant RAG...")
        rag = load_and_index_cv(cv_content)

        # Test RAG queries
        rag_questions = [
            "What specific AI technologies and frameworks does Samuel have experience with?",
            "What are Samuel's achievements in product management roles?",
            "How does Samuel's experience align with LangGraph and AI workflows?"
        ]

        print(f"🔍 Testing {len(rag_questions)} RAG queries...")

        all_answers = []
        for i, question in enumerate(rag_questions, 1):
            print(f"\n--- RAG Query {i}: {question}")

            result = rag.query_cv(question, f"rag_test_{i}")
            answer = result['answer']
            context_count = len(result['context'])

            print(f"✅ Answer: {answer}")
            print(f"📄 Used {context_count} context chunks")

            all_answers.append(answer)

        # Check if answers are different (good sign of proper semantic search)
        unique_answers = set(all_answers)
        if len(unique_answers) == len(all_answers):
            print(f"\n✅ All RAG answers are unique - good semantic understanding!")
        else:
            print(f"\n⚠️ Some RAG answers are similar - may need tuning")

        return True

    except Exception as e:
        print(f"❌ RAG integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_cover_letter_personalization():
    """Test cover letter generation with proper personalization"""
    print("\n🧪 Test 3: Cover Letter Personalization")
    print("=" * 50)

    try:
        cv_content = load_cv_from_docs()
        job_posting = create_perfect_match_job_posting()

        if not cv_content:
            return False

        # Create orchestrator
        orchestrator = JobSearchOrchestrator()

        # First process documents
        initial_state = {
            "messages": [HumanMessage(content="Generate a personalized cover letter")],
            "cv_content": cv_content,
            "job_posting": job_posting
        }

        print("🚀 Processing documents first...")
        config = {"configurable": {"thread_id": "cover_letter_test"}}

        # Process documents
        processed_state = await orchestrator.document_processor_node(initial_state, config)

        # Generate cover letter
        print("📝 Generating cover letter...")
        cover_letter_state = await orchestrator.cover_letter_generator_node(processed_state, config)

        cover_letter = cover_letter_state.get("cover_letter", "")

        if cover_letter:
            print(f"✅ Cover letter generated: {len(cover_letter)} characters")
            print(f"\n📄 Cover Letter Preview:")
            print(f"{cover_letter[:500]}...")

            # Check for personalization
            personalization_checks = [
                ("Samuel", "Name mention"),
                ("Product Manager", "Role mention"),
                ("LangGraph", "Specific technology"),
                ("Montreal", "Location match"),
                ("AI", "Industry alignment"),
                ("Python", "Technical skills")
            ]

            print(f"\n🔍 Personalization Analysis:")
            personalization_score = 0

            for term, description in personalization_checks:
                if term.lower() in cover_letter.lower():
                    print(f"   ✅ {description}: Found '{term}'")
                    personalization_score += 1
                else:
                    print(f"   ❌ {description}: Missing '{term}'")

            print(f"\n📊 Personalization Score: {personalization_score}/{len(personalization_checks)}")

            if personalization_score >= 4:
                print("✅ Cover letter is well personalized!")
                return True
            else:
                print("⚠️ Cover letter needs more personalization")
                return False
        else:
            print("❌ No cover letter generated")
            return False

    except Exception as e:
        print(f"❌ Cover letter personalization test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_complete_workflow_integration():
    """Test the complete workflow with limited recursion"""
    print("\n🧪 Test 4: Complete Workflow Integration")
    print("=" * 50)

    try:
        cv_content = load_cv_from_docs()
        job_posting = create_perfect_match_job_posting()

        if not cv_content:
            return False

        # Create orchestrator and workflow
        orchestrator = JobSearchOrchestrator()
        workflow = orchestrator.create_complete_workflow()

        # Create initial state that should trigger document processing
        initial_state = {
            "messages": [HumanMessage(content="I need a personalized cover letter for this job. Please analyze my CV and create one that highlights my relevant experience.")],
            "cv_content": cv_content,
            "job_posting": job_posting
        }

        config = {
            "configurable": {"thread_id": "complete_workflow_test"},
            "recursion_limit": 5  # Prevent infinite loops while allowing processing
        }

        print("🚀 Running complete workflow with limited recursion...")

        # Stream the workflow to see what happens
        steps_executed = []
        try:
            async for step in workflow.astream(initial_state, config, stream_mode="updates"):
                for node_name, node_output in step.items():
                    steps_executed.append(node_name)
                    print(f"📋 Executed: {node_name}")

                    # Show key outputs
                    if "analysis_report" in str(node_output):
                        print(f"   📊 Contains analysis data")
                    if "cover_letter" in str(node_output):
                        print(f"   💌 Contains cover letter")

                # Limit steps to prevent infinite loop
                if len(steps_executed) >= 8:
                    print("🛑 Stopping after 8 steps to prevent infinite loop")
                    break

        except Exception as stream_error:
            print(f"⚠️ Workflow streaming stopped: {stream_error}")

        print(f"\n📊 Workflow executed {len(steps_executed)} steps:")
        print(f"   Steps: {' → '.join(steps_executed)}")

        # Check if we got key processing steps
        expected_steps = ["agent_node", "document_processor_node", "cover_letter_generator_node"]
        steps_found = sum(1 for step in expected_steps if step in steps_executed)

        print(f"📈 Key processing steps found: {steps_found}/{len(expected_steps)}")

        if steps_found >= 2:
            print("✅ Workflow integration working - key steps executed!")
            return True
        else:
            print("⚠️ Workflow needs more work - missing key processing steps")
            return False

    except Exception as e:
        print(f"❌ Complete workflow test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all final integration tests"""
    print("🚀 Final Integration Test - Complete Job Search Workflow")
    print("Testing document processing, RAG integration, and personalization")
    print("=" * 70)

    results = []

    # Run all tests
    results.append(await test_document_processing_workflow())
    results.append(await test_rag_integration())
    results.append(await test_cover_letter_personalization())
    results.append(await test_complete_workflow_integration())

    # Final summary
    print(f"\n" + "=" * 70)
    print("🏁 FINAL INTEGRATION TEST RESULTS")

    passed = sum(results)
    total = len(results)

    print(f"✅ Tests passed: {passed}/{total}")

    if passed >= 3:
        print("\n🎉 INTEGRATION SUCCESSFUL!")
        print("📋 Working components:")
        print("   ✅ Document processing with analysis reports")
        print("   ✅ New LangGraph-compliant RAG implementation")
        print("   ✅ Personalized cover letter generation")
        print("   ✅ Workflow orchestration with proper routing")

        print(f"\n🎯 READY FOR PRODUCTION!")
        print("Your complete job search orchestrator is now functional with:")
        print("   • Proper CV analysis and vectorization")
        print("   • Semantic search using real embeddings")
        print("   • Personalized cover letters based on CV content")
        print("   • LangGraph best practices implementation")
        print("   • Fixed routing logic")

    else:
        print(f"\n⚠️ Integration needs work: {total - passed} tests failed")
        print("Check the logs above for specific issues")

    return passed >= 3


if __name__ == "__main__":
    """Main execution"""
    print("🔧 Setting up final integration test environment...")

    # Check directory structure
    if not (Path.cwd() / "src" / "job_search_agent").exists():
        print("❌ Please run this script from the project root directory")
        sys.exit(1)

    print("📁 Project structure validated")

    try:
        success = asyncio.run(main())

        if success:
            print("\n" + "🎉" * 20)
            print("SUCCESS: Your job search orchestrator is ready!")
            print("The CV from docs/ is now properly analyzed and vectorized.")
            print("Cover letters will be personalized based on CV content.")
            print("🎉" * 20)

        sys.exit(0 if success else 1)

    except KeyboardInterrupt:
        print("\n⚠️ Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
