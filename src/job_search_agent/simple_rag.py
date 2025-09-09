"""
Simple LangGraph-Compliant RAG Implementation
Following LangGraph best practices for CV analysis and job search
Based on: https://python.langchain.com/docs/tutorials/rag/
"""

from typing import List, TypedDict
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_core.prompts import PromptTemplate
from langgraph.graph import StateGraph, START
from langgraph.checkpoint.memory import MemorySaver

from .config import LLM_CONFIG


# =============================================================================
# STATE DEFINITION
# =============================================================================

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
    - Uses InMemoryVectorStore
    - Uses RecursiveCharacterTextSplitter
    - Simple retrieve/generate functions
    """

    def __init__(self, llm_config: dict = None):
        """Initialize simple RAG components"""
        self.llm_config = llm_config or LLM_CONFIG

        # Initialize components following LangGraph pattern
        self.embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
        self.vector_store = InMemoryVectorStore(self.embeddings)
        self.llm = ChatOpenAI(**self.llm_config)

        # Text splitter with good defaults
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            add_start_index=True
        )

        # Simple RAG prompt
        self.prompt = PromptTemplate.from_template(
            """You are an assistant helping with CV and job application questions.
Use the following CV information to answer the question.
If you don't know the answer, just say that you don't know.
Keep the answer concise and relevant.

CV Information:
{context}

Question: {question}
Answer:"""
        )

        self.workflow = None

    def index_cv_content(self, cv_content: str) -> bool:
        """
        Index CV content for retrieval

        Args:
            cv_content: Raw CV text content

        Returns:
            bool: Success status
        """
        try:
            # Create document
            doc = Document(
                page_content=cv_content,
                metadata={"source": "cv", "type": "resume"}
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

    def retrieve(self, state: RAGState) -> RAGState:
        """
        Retrieve relevant CV chunks
        Simple function following LangGraph pattern
        """
        retrieved_docs = self.vector_store.similarity_search(
            state["question"],
            k=4  # Top 4 most relevant chunks
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
