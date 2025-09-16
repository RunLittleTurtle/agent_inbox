"""
Simple LangGraph-Compliant RAG Implementation
Following LangGraph best practices for CV analysis and job search
Based on: https://python.langchain.com/docs/tutorials/rag/
"""

import os
import json
from typing import List, TypedDict
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_core.prompts import PromptTemplate
from langgraph.graph import StateGraph, START
from langgraph.checkpoint.memory import MemorySaver

from .config import LLM_CONFIG
from .prompt import RAG_CV_QUERY_PROMPT



class RAGState(TypedDict):
    """Simple state for RAG operations"""
    question: str
    context: List[Document]
    answer: str


# =============================================================================
# SIMPLE RAG CLASS
# =============================================================================

class SimpleRAG:
    """
    Simple LangGraph-compliant RAG implementation

    Follows LangGraph best practices:
    - Uses OpenAIEmbeddings
    - Uses InMemoryVectorStore (shared across instances)
    - Uses RecursiveCharacterTextSplitter
    - Simple retrieve/generate functions
    """

    # Class-level shared components to persist across instances
    _shared_embeddings = None
    _shared_vector_store = None

    def __init__(self, llm_config: dict = None):
        """Initialize simple RAG components"""
        self.llm_config = llm_config or LLM_CONFIG

        # Initialize shared components only once
        if SimpleRAG._shared_embeddings is None:
            SimpleRAG._shared_embeddings = OpenAIEmbeddings(model="text-embedding-3-large")

        if SimpleRAG._shared_vector_store is None:
            SimpleRAG._shared_vector_store = InMemoryVectorStore(SimpleRAG._shared_embeddings)
            # Load persistent CV data on first initialization
            self._load_persistent_cv()

        # Use shared components
        self.embeddings = SimpleRAG._shared_embeddings
        self.vector_store = SimpleRAG._shared_vector_store
        self.llm = ChatOpenAI(**self.llm_config)

        # Text splitter optimized for comprehensive CV context preservation
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=800,  # Larger chunks to preserve project context and descriptions
            chunk_overlap=200,  # Substantial overlap (25%) to ensure continuity across chunks
            add_start_index=True,
            separators=["\n\n", "\n", ".", "!", "?", ",", " ", ""]  # Better CV structure recognition
        )

        # RAG prompt from centralized prompts
        self.prompt = PromptTemplate.from_template(RAG_CV_QUERY_PROMPT)

        self.workflow = None

    def _load_persistent_cv(self):
        """Load CV from persistent storage using existing data structure"""
        try:
            # Get project root directory (3 levels up from simple_rag.py)
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            cv_metadata_path = os.path.join(project_root, "job_search_data", "vectors", "global_cv_index_metadata.json")

            if os.path.exists(cv_metadata_path):
                with open(cv_metadata_path, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)

                if metadata.get("status") == "ready" and "chunks" in metadata:
                    # Create documents from pre-chunked content
                    documents = []
                    for chunk_content in metadata["chunks"]:
                        doc = Document(
                            page_content=chunk_content,
                            metadata={
                                "source": "persistent_cv",
                                "type": "resume",
                                "content_type": "cv"
                            }
                        )
                        documents.append(doc)

                    # Add to vector store
                    SimpleRAG._shared_vector_store.add_documents(documents)
                    print(f"✅ Loaded persistent CV: {len(documents)} chunks from storage")
                    return True
        except Exception as e:
            print(f"⚠️ Could not load persistent CV: {e}")

        return False

    def index_cv_content(self, cv_content: str) -> bool:
        """
        Index CV content for retrieval (adds to existing content)

        Args:
            cv_content: Raw CV text content

        Returns:
            bool: Success status
        """
        try:
            # Create document with language metadata
            doc = Document(
                page_content=cv_content,
                metadata={
                    "source": "cv",
                    "type": "resume",
                    "content_type": "cv"
                }
            )

            # Split into chunks
            chunks = self.text_splitter.split_documents([doc])

            # Add to vector store
            self.vector_store.add_documents(chunks)

            print(f"✅ Indexed CV content: {len(chunks)} chunks created")
            return True

        except Exception as e:
            print(f"❌ Error indexing CV: {e}")
            return False

    def replace_cv_content(self, cv_content: str) -> bool:
        """
        Replace all existing CV content with new content

        Args:
            cv_content: Raw CV text content

        Returns:
            bool: Success status
        """
        try:
            # Create new shared vector store to replace old content
            SimpleRAG._shared_vector_store = InMemoryVectorStore(SimpleRAG._shared_embeddings)
            self.vector_store = SimpleRAG._shared_vector_store

            # Create document with language metadata
            doc = Document(
                page_content=cv_content,
                metadata={
                    "source": "cv",
                    "type": "resume",
                    "content_type": "cv"
                }
            )

            # Split into chunks with better strategy for CV
            chunks = self.text_splitter.split_documents([doc])

            # Add to fresh vector store
            self.vector_store.add_documents(chunks)

            # Update persistent storage
            self._save_to_persistent_storage(cv_content, chunks)

            print(f"✅ Replaced CV content: {len(chunks)} chunks created")
            return True

        except Exception as e:
            print(f"❌ Error replacing CV: {e}")
            return False

    def _save_to_persistent_storage(self, cv_content: str, chunks: List[Document]):
        """Save CV content to persistent storage using existing data structure"""
        try:
            import hashlib
            from datetime import datetime

            # Get project root directory (3 levels up from simple_rag.py)
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))

            # Create directories if they don't exist
            documents_dir = os.path.join(project_root, "job_search_data", "documents")
            vectors_dir = os.path.join(project_root, "job_search_data", "vectors")
            os.makedirs(documents_dir, exist_ok=True)
            os.makedirs(vectors_dir, exist_ok=True)

            # Save CV content
            cv_path = os.path.join(documents_dir, "global_cv.md")
            with open(cv_path, 'w', encoding='utf-8') as f:
                f.write(cv_content)

            # Create content hash
            content_hash = hashlib.md5(cv_content.encode()).hexdigest()

            # Save document metadata
            doc_metadata = {
                "global_cv": {
                    "upload_timestamp": datetime.now().isoformat(),
                    "file_size": len(cv_content),
                    "content_hash": content_hash
                }
            }

            metadata_path = os.path.join(documents_dir, "document_metadata.json")
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(doc_metadata, f, indent=2)

            # Save vector index metadata
            vector_metadata = {
                "chunks": [chunk.page_content for chunk in chunks],
                "created_at": datetime.now().isoformat(),
                "status": "ready",
                "content_hash": content_hash
            }

            vector_metadata_path = os.path.join(vectors_dir, "global_cv_index_metadata.json")
            with open(vector_metadata_path, 'w', encoding='utf-8') as f:
                json.dump(vector_metadata, f, indent=2)

            print(f"✅ Saved to persistent storage: {len(chunks)} chunks")

        except Exception as e:
            print(f"⚠️ Could not save to persistent storage: {e}")

    def retrieve(self, state: RAGState) -> RAGState:
        """
        Retrieve relevant CV chunks
        Simple function following LangGraph pattern
        """
        retrieved_docs = self.vector_store.similarity_search(
            state["question"],
            k=8  # More chunks for comprehensive coverage with larger chunk sizes
        )
        return {"context": retrieved_docs}

    def generate(self, state: RAGState) -> RAGState:
        """
        Generate answer using retrieved context
        Simple function following LangGraph pattern
        """
        try:
            # Combine context
            docs_content = "\n\n".join(doc.page_content for doc in state["context"])

            # Format prompt - limit length to prevent token issues
            if len(docs_content) > 3000:
                docs_content = docs_content[:3000] + "..."

            # Format prompt
            formatted_prompt = self.prompt.format(
                question=state["question"],
                context=docs_content
            )

            # Generate response
            response = self.llm.invoke(formatted_prompt)

            return {"answer": response.content}
        except Exception as e:
            # Handle API errors gracefully
            error_msg = str(e)
            if "server had an error" in error_msg or "APIError" in error_msg:
                return {"answer": "Sorry, there's a temporary API issue. Please try again in a moment."}
            else:
                return {"answer": f"Error generating response: {error_msg}"}

    def create_workflow(self) -> StateGraph:
        """
        Create LangGraph workflow
        Following the exact LangGraph pattern
        """
        # Build graph with sequence
        graph_builder = StateGraph(RAGState).add_sequence([self.retrieve, self.generate])
        graph_builder.add_edge(START, "retrieve")

        # Compile with checkpointer
        self.workflow = graph_builder.compile(checkpointer=MemorySaver())

        return self.workflow

    def query_cv(self, question: str, thread_id: str = "default") -> dict:
        """
        Query CV content with a question

        Args:
            question: User question
            thread_id: Thread ID for conversation persistence

        Returns:
            dict: Complete response with context and answer
        """
        try:
            if not self.workflow:
                self.create_workflow()

            # Invoke workflow
            config = {"configurable": {"thread_id": thread_id}}
            result = self.workflow.invoke({"question": question}, config)

            return result
        except Exception as e:
            # Handle API errors gracefully
            error_msg = str(e)
            if "server had an error" in error_msg or "APIError" in error_msg:
                return {
                    "question": question,
                    "context": [],
                    "answer": "Sorry, there's a temporary API issue. Please try again in a moment."
                }
            else:
                return {
                    "question": question,
                    "context": [],
                    "answer": f"Error processing your question: {error_msg}"
                }

    async def aquery_cv(self, question: str, thread_id: str = "default") -> dict:
        """
        Async query CV content

        Args:
            question: User question
            thread_id: Thread ID for conversation persistence

        Returns:
            dict: Complete response with context and answer
        """
        try:
            if not self.workflow:
                self.create_workflow()

            config = {"configurable": {"thread_id": thread_id}}
            result = await self.workflow.ainvoke({"question": question}, config)

            return result
        except Exception as e:
            # Handle API errors gracefully
            error_msg = str(e)
            if "server had an error" in error_msg or "APIError" in error_msg:
                return {
                    "question": question,
                    "context": [],
                    "answer": "Sorry, there's a temporary API issue. Please try again in a moment."
                }
            else:
                return {
                    "question": question,
                    "context": [],
                    "answer": f"Error processing your question: {error_msg}"
                }

    # =============================================================================
    # JOB DATA MANAGEMENT (replaces document_store) - FILE-BASED PERSISTENCE
    # =============================================================================

    def _get_thread_data_path(self, thread_id: str) -> str:
        """Get file path for thread data storage"""
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        thread_data_dir = os.path.join(project_root, "job_search_data", "threads")
        os.makedirs(thread_data_dir, exist_ok=True)
        return os.path.join(thread_data_dir, f"{thread_id}_data.json")

    def _load_thread_data(self, thread_id: str) -> dict:
        """Load thread data from file"""
        try:
            data_path = self._get_thread_data_path(thread_id)
            if os.path.exists(data_path):
                with open(data_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            print(f"Error loading thread data: {e}")
            return {}

    def _save_thread_data(self, thread_id: str, data: dict) -> bool:
        """Save thread data to file"""
        try:
            data_path = self._get_thread_data_path(thread_id)
            with open(data_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error saving thread data: {e}")
            return False

    def store_job_posting(self, thread_id: str, job_posting: str) -> bool:
        """Store job posting for thread"""
        try:
            thread_data = self._load_thread_data(thread_id)
            thread_data["job_posting"] = job_posting
            return self._save_thread_data(thread_id, thread_data)
        except Exception as e:
            print(f"Error storing job posting: {e}")
            return False

    def get_job_posting(self, thread_id: str) -> str:
        """Get job posting for thread"""
        thread_data = self._load_thread_data(thread_id)
        return thread_data.get("job_posting")

    def store_job_analysis(self, thread_id: str, analysis: dict) -> bool:
        """Store job analysis for thread"""
        try:
            thread_data = self._load_thread_data(thread_id)
            thread_data["job_analysis"] = analysis
            return self._save_thread_data(thread_id, thread_data)
        except Exception as e:
            print(f"Error storing job analysis: {e}")
            return False

    def get_job_analysis(self, thread_id: str) -> dict:
        """Get job analysis for thread"""
        thread_data = self._load_thread_data(thread_id)
        return thread_data.get("job_analysis")

    def store_cv_analysis(self, thread_id: str, analysis: dict) -> bool:
        """Store CV analysis for thread"""
        try:
            thread_data = self._load_thread_data(thread_id)
            thread_data["cv_analysis"] = analysis
            return self._save_thread_data(thread_id, thread_data)
        except Exception as e:
            print(f"Error storing CV analysis: {e}")
            return False

    def get_cv_analysis(self, thread_id: str) -> dict:
        """Get CV analysis for thread"""
        thread_data = self._load_thread_data(thread_id)
        return thread_data.get("cv_analysis")

    def has_job_posting(self, thread_id: str) -> bool:
        """Check if job posting exists for thread"""
        return bool(self.get_job_posting(thread_id))

    def clear_thread_data(self, thread_id: str) -> bool:
        """Clear all data for thread"""
        try:
            data_path = self._get_thread_data_path(thread_id)
            if os.path.exists(data_path):
                os.remove(data_path)
            return True
        except Exception as e:
            print(f"Error clearing thread data: {e}")
            return False



    def get_preferences(self, thread_id: str) -> dict:
        """Get user preferences for thread"""
        thread_data = self._load_thread_data(thread_id)
        return thread_data.get("preferences", {})

    def store_history_item(self, thread_id: str, history_item: dict) -> bool:
        """Add item to generation history for thread"""
        try:
            thread_data = self._load_thread_data(thread_id)
            if "history" not in thread_data:
                thread_data["history"] = []
            thread_data["history"].append(history_item)
            return self._save_thread_data(thread_id, thread_data)
        except Exception as e:
            print(f"Error storing history item: {e}")
            return False



    def get_raw_cv_chunks(self, query: str, k: int = 10) -> List[str]:
        """
        Get raw CV chunks directly from vector store without LLM processing
        Enhanced with Maximum Marginal Relevance for diverse results

        Args:
            query: Search query for relevant chunks
            k: Number of chunks to retrieve

        Returns:
            List of raw chunk content strings
        """
        try:
            # Use Maximum Marginal Relevance for diverse results - LangGraph best practice
            retrieved_docs = self.get_diverse_cv_chunks(query, k)

            # Return raw chunk content
            return [doc.page_content for doc in retrieved_docs]

        except Exception as e:
            print(f"Error retrieving raw chunks: {e}")
            return []

    def get_diverse_cv_chunks(self, query: str, k: int = 10):
        """
        Get diverse CV chunks using Maximum Marginal Relevance for variety
        Prevents retrieving too many similar chunks from same CV sections

        Args:
            query: Search query for relevant chunks
            k: Number of chunks to retrieve

        Returns:
            List of document chunks with diversity
        """
        try:
            # Use Maximum Marginal Relevance for diverse results
            retrieved_docs = self.vector_store.max_marginal_relevance_search(
                query,
                k=k,
                lambda_mult=0.7  # Balance relevance (0.0) vs diversity (1.0)
            )
            return retrieved_docs
        except (AttributeError, Exception) as e:
            # Fallback to regular similarity search if MMR not supported
            print(f"MMR not available ({type(e).__name__}), using similarity search")
            retrieved_docs = self.vector_store.similarity_search(query, k=k)
            return retrieved_docs

    def force_cv_reindex(self) -> bool:
        """
        Force re-indexing of CV content with new chunking parameters
        Use this when chunking strategy has been updated
        """
        try:
            # Get stored CV content
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            cv_path = os.path.join(project_root, "job_search_data", "documents", "global_cv.md")

            if os.path.exists(cv_path):
                with open(cv_path, 'r', encoding='utf-8') as f:
                    cv_content = f.read()

                print(f"🔄 Re-indexing CV with new chunking strategy...")
                print(f"📊 Optimized chunking parameters: 800 chars with 200 overlap")

                # Force replacement with new chunking
                success = self.replace_cv_content(cv_content)
                if success:
                    print(f"✅ CV re-indexed successfully with optimized chunks")
                    return True
                else:
                    print(f"❌ Failed to re-index CV")
                    return False
            else:
                print(f"❌ CV file not found at {cv_path}")
                return False
        except Exception as e:
            print(f"❌ Error during re-indexing: {e}")
            return False


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def create_simple_rag(llm_config: dict = None) -> SimpleRAG:
    """Factory function to create SimpleRAG instance"""
    return SimpleRAG(llm_config)


def load_and_index_cv(cv_content: str, llm_config: dict = None) -> SimpleRAG:
    """
    One-shot function to create RAG and index CV

    Args:
        cv_content: Raw CV text
        llm_config: Optional LLM configuration

    Returns:
        SimpleRAG: Ready-to-use RAG instance
    """
    rag = SimpleRAG(llm_config)
    success = rag.index_cv_content(cv_content)

    if not success:
        raise Exception("Failed to index CV content")

    return rag


# =============================================================================
# EXAMPLE USAGE
# =============================================================================

if __name__ == "__main__":
    """Example usage following LangGraph tutorial pattern"""

    # Sample CV content
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
        # Create and index
        rag = load_and_index_cv(sample_cv)

        # Query examples
        questions = [
            "What AI technologies does Samuel know?",
            "What is Samuel's product management experience?",
            "What companies has Samuel worked at?"
        ]

        for question in questions:
            print(f"\n🔍 Question: {question}")
            result = rag.query_cv(question)
            print(f"📝 Answer: {result['answer']}")
            print(f"📄 Context chunks: {len(result['context'])}")

    except Exception as e:
        print(f"❌ Error: {e}")
