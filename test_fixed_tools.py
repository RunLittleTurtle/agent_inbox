#!/usr/bin/env python3
"""
Test script for fixed job search tools
Tests SimpleRAG integration and document processing
"""

import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_simple_rag_import():
    """Test SimpleRAG can be imported and initialized"""
    print("🧪 Testing SimpleRAG import...")
    try:
        from job_search_agent.simple_rag import SimpleRAG
        rag = SimpleRAG()
        print("✅ SimpleRAG import and initialization successful")
        return rag
    except Exception as e:
        print(f"❌ SimpleRAG import failed: {e}")
        return None

def test_cv_indexing(rag):
    """Test CV content indexing"""
    print("\n🧪 Testing CV indexing...")

    sample_cv = """
    Samuel Audette
    Product Manager specializing in AI workflows

    Experience:
    - Walter Interactive: Product Manager & Operations (2024-2025)
    - Glowtify SaaS: Product Owner (2024)
    - Anekdote App: Product Owner (2022-2024)

    Skills:
    - Python, LangChain, LangGraph
    - Product Management, Agile
    - AI/ML, OpenAI APIs
    """

    try:
        success = rag.index_cv_content(sample_cv)
        if success:
            print("✅ CV indexing successful")
        else:
            print("❌ CV indexing failed")
        return success
    except Exception as e:
        print(f"❌ CV indexing error: {e}")
        return False

def test_cv_query(rag):
    """Test querying CV content"""
    print("\n🧪 Testing CV querying...")

    try:
        result = rag.query_cv("What AI technologies does Samuel know?")
        if result and result.get('answer'):
            print("✅ CV query successful")
            print(f"📝 Answer: {result['answer'][:100]}...")
            print(f"📄 Context chunks: {len(result.get('context', []))}")
            return True
        else:
            print("❌ CV query failed - no answer")
            return False
    except Exception as e:
        print(f"❌ CV query error: {e}")
        return False

def test_tools_import():
    """Test tools can be imported"""
    print("\n🧪 Testing tools import...")
    try:
        from job_search_agent import tools
        print("✅ Tools import successful")

        # Test specific functions exist
        functions = [
            'upload_cv',
            'upload_job_posting',
            'get_document_status',
            'generate_cover_letter',
            'search_cv_details'
        ]

        for func_name in functions:
            if hasattr(tools, func_name):
                print(f"✅ Function {func_name} found")
            else:
                print(f"❌ Function {func_name} missing")

        return True
    except Exception as e:
        print(f"❌ Tools import failed: {e}")
        return False

def test_document_status():
    """Test document status checking"""
    print("\n🧪 Testing document status...")
    try:
        from job_search_agent.tools import get_document_status

        status = get_document_status("test_thread")
        print("✅ Document status check successful")
        print(f"📋 Status:\n{status}")
        return True
    except Exception as e:
        print(f"❌ Document status error: {e}")
        return False

def test_cv_upload():
    """Test CV upload functionality"""
    print("\n🧪 Testing CV upload...")
    try:
        from job_search_agent.tools import upload_cv

        sample_cv = """
        John Doe
        Software Engineer

        Experience:
        - Company A: Senior Developer (2020-2024)
        - Company B: Junior Developer (2018-2020)

        Skills:
        - Python, JavaScript, React
        - Machine Learning, AI
        """

        result = upload_cv(sample_cv, "test_thread")
        print("✅ CV upload successful")
        print(f"📝 Result: {result[:200]}...")
        return True
    except Exception as e:
        print(f"❌ CV upload error: {e}")
        return False

def test_job_posting_upload():
    """Test job posting upload"""
    print("\n🧪 Testing job posting upload...")
    try:
        from job_search_agent.tools import upload_job_posting

        job_posting = """
        Senior Product Manager - AI Solutions

        Requirements:
        - 5+ years product management experience
        - Experience with AI/ML products
        - Strong technical background
        - Python programming skills
        - Agile methodology experience

        Responsibilities:
        - Lead product strategy and roadmap
        - Collaborate with engineering teams
        - Manage product lifecycle
        """

        result = upload_job_posting(job_posting, "test_thread")
        print("✅ Job posting upload successful")
        print(f"📝 Result: {result[:200]}...")
        return True
    except Exception as e:
        print(f"❌ Job posting upload error: {e}")
        return False

def test_cover_letter_generation():
    """Test cover letter generation"""
    print("\n🧪 Testing cover letter generation...")
    try:
        from job_search_agent.tools import generate_cover_letter

        result = generate_cover_letter("test_thread")
        print("✅ Cover letter generation successful")
        print(f"📝 Cover letter preview:\n{result[:300]}...")
        return True
    except Exception as e:
        print(f"❌ Cover letter generation error: {e}")
        return False

def test_cv_search():
    """Test CV search functionality"""
    print("\n🧪 Testing CV search...")
    try:
        from job_search_agent.tools import search_cv_details

        result = search_cv_details("Python experience", "test_thread")
        print("✅ CV search successful")
        print(f"📝 Search result:\n{result[:300]}...")
        return True
    except Exception as e:
        print(f"❌ CV search error: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Starting job search tools tests\n")

    results = {}

    # Test SimpleRAG
    rag = test_simple_rag_import()
    results['rag_import'] = rag is not None

    if rag:
        results['cv_indexing'] = test_cv_indexing(rag)
        results['cv_query'] = test_cv_query(rag)
    else:
        results['cv_indexing'] = False
        results['cv_query'] = False

    # Test tools
    results['tools_import'] = test_tools_import()
    results['document_status'] = test_document_status()
    results['cv_upload'] = test_cv_upload()
    results['job_posting_upload'] = test_job_posting_upload()
    results['cover_letter_generation'] = test_cover_letter_generation()
    results['cv_search'] = test_cv_search()

    # Summary
    print("\n" + "="*50)
    print("🎯 TEST RESULTS SUMMARY")
    print("="*50)

    passed = sum(results.values())
    total = len(results)

    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:<25} {status}")

    print(f"\nOverall: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! The job search tools are working correctly.")
    elif passed >= total * 0.8:
        print("⚠️ Most tests passed. Minor issues may need attention.")
    else:
        print("🚨 Several tests failed. Major issues need fixing.")

    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
