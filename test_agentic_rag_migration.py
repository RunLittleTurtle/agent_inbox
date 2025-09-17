#!/usr/bin/env python3
"""
Test the agentic RAG migration for analyse_cv_match tool
"""

import os
import sys
import json

# Add the src directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from job_search_agent.tools import analyze_cv_match, upload_job_posting, analyze_job_requirements

def test_agentic_rag_migration():
    """Test that analyse_cv_match now uses agentic RAG successfully"""
    print("🧪 Testing agentic RAG migration for analyse_cv_match...")

    # Test data - simple job posting
    test_job_posting = """
    Senior Software Engineer - AI/ML Focus

    We are looking for a Senior Software Engineer with expertise in:
    - Python programming and machine learning frameworks
    - Experience with data analysis and statistical modeling
    - Strong problem-solving skills and project management experience

    Responsibilities:
    - Develop and deploy machine learning models
    - Lead technical projects from conception to production
    - Collaborate with cross-functional teams
    """

    thread_id = "agentic_test"

    try:
        # Step 1: Upload job posting
        print("📋 Step 1: Uploading test job posting...")
        upload_result = upload_job_posting.invoke({
            "content": test_job_posting,
            "thread_id": thread_id
        })
        print(f"Upload result: {upload_result[:100]}...")

        # Step 2: Analyze job requirements
        print("🔍 Step 2: Analyzing job requirements...")
        job_analysis_result = analyze_job_requirements.invoke({"thread_id": thread_id})
        print(f"Job analysis result: {job_analysis_result[:100]}...")

        # Step 3: Test the improved analyse_cv_match with agentic RAG
        print("🤖 Step 3: Testing analyse_cv_match with agentic RAG...")
        cv_match_result = analyze_cv_match.invoke({"thread_id": thread_id})

        # Parse the JSON response to check for agentic RAG indicators
        if isinstance(cv_match_result, str) and cv_match_result.startswith('{'):
            result_data = json.loads(cv_match_result)

            # Check for success and agentic RAG message
            if result_data.get("status") == "success":
                message = result_data.get("message", "")
                if "🤖 Agentic RAG Analysis Complete" in message and "queries intelligently rewritten" in message:
                    print("✅ SUCCESS: analyse_cv_match now uses agentic RAG!")
                    print(f"📊 Result message: {message}")

                    # Extract data to show agentic improvements
                    data = result_data.get("data", {})
                    talking_points = data.get("compelling_talking_points", [])
                    print(f"📈 Found {len(talking_points)} compelling talking points")

                    if talking_points:
                        print("💡 Sample talking point:")
                        print(f"   - {talking_points[0].get('point', 'N/A')}")

                    return True
                else:
                    print("❌ FAIL: Message doesn't indicate agentic RAG usage")
                    print(f"Message: {message}")
            else:
                print(f"❌ FAIL: Tool returned error: {result_data.get('error', {}).get('message', 'Unknown error')}")
        else:
            print(f"❌ FAIL: Unexpected response format: {cv_match_result}")

    except Exception as e:
        print(f"❌ FAIL: Exception during testing: {e}")
        import traceback
        traceback.print_exc()

    return False

if __name__ == "__main__":
    success = test_agentic_rag_migration()
    if success:
        print("\n🎉 MIGRATION SUCCESS: analyse_cv_match now uses intelligent agentic RAG!")
        print("Benefits:")
        print("  - Automatic query rewriting for better job-CV matching")
        print("  - Document relevance grading")
        print("  - Answer quality assessment")
        print("  - Up to 3 iterative attempts per requirement")
        print("  - Detailed performance metrics")
    else:
        print("\n💥 MIGRATION ISSUES: Please check the implementation")

    sys.exit(0 if success else 1)
