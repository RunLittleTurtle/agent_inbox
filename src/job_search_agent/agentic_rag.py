"""
LangGraph Agentic RAG Implementation for CV Search
Following LangGraph tutorial best practices with query rewriting and quality assessment
Based on: https://langchain-ai.github.io/langgraph/tutorials/rag/langgraph_agentic_rag/
"""

from typing import List, Literal
from typing_extensions import TypedDict

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_core.tools import create_retriever_tool
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END, MessagesState
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from pydantic import BaseModel, Field

from .simple_rag import SimpleRAG
from .config import LLM_CONFIG


# =============================================================================
# STATE SCHEMA - LangGraph Best Practice
# =============================================================================

class AgenticRAGState(MessagesState):
    """
    State for agentic RAG operations extending MessagesState
    Following LangGraph best practices for state management
    """
    original_query: str = ""
    current_query: str = ""
    retrieval_attempts: int = 0
    document_grade: str = ""  # "relevant" | "not_relevant"
    answer_grade: str = ""    # "useful" | "not_useful"


# =============================================================================
# PYDANTIC MODELS FOR STRUCTURED OUTPUT
# =============================================================================

class DocumentGrade(BaseModel):
    """Binary score for document relevance to question"""
    binary_score: Literal["relevant", "not_relevant"] = Field(
        description="Documents are relevant to the question, 'relevant' or 'not_relevant'"
    )

class AnswerGrade(BaseModel):
    """Binary score for answer quality and usefulness"""
    binary_score: Literal["useful", "not_useful"] = Field(
        description="Answer addresses the question, 'useful' or 'not_useful'"
    )


# =============================================================================
# AGENTIC CV RAG CLASS
# =============================================================================

class AgenticCVRAG:
    """
    Agentic RAG system for CV search with query rewriting and quality assessment
    """

    def __init__(self, simple_rag: SimpleRAG):
        self.simple_rag = simple_rag
        self.llm = ChatOpenAI(**LLM_CONFIG)

        # Create retriever tool from existing SimpleRAG
        self.retriever_tool = create_retriever_tool(
            retriever=simple_rag.vector_store.as_retriever(k=8),
            name="cv_retriever",
            description="Retrieve relevant information from Samuel's CV to answer questions about his experience, skills, projects, and background."
        )

        # Bind tools to LLM for generate_query_or_respond node
        self.llm_with_tools = self.llm.bind_tools([self.retriever_tool])

        # Create structured LLMs for grading
        self.doc_grader = self.llm.with_structured_output(DocumentGrade)
        self.answer_grader = self.llm.with_structured_output(AnswerGrade)

        # Build the graph
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """
        Assemble the agentic RAG graph following LangGraph tutorial pattern
        """
        workflow = StateGraph(AgenticRAGState)

        # Add nodes
        workflow.add_node("generate_query_or_respond", self.generate_query_or_respond)
        workflow.add_node("retrieve", ToolNode([self.retriever_tool]))
        workflow.add_node("grade_documents", self.grade_documents)
        workflow.add_node("generate_answer", self.generate_answer)
        workflow.add_node("rewrite_question", self.rewrite_question)

        # Add edges
        workflow.add_edge(START, "generate_query_or_respond")

        # Conditional edge after generate_query_or_respond
        workflow.add_conditional_edges(
            "generate_query_or_respond",
            tools_condition,
            {
                "tools": "retrieve",
                END: END,
            }
        )

        # After retrieval, grade documents
        workflow.add_edge("retrieve", "grade_documents")

        # Conditional edge after document grading
        workflow.add_conditional_edges(
            "grade_documents",
            self.decide_to_generate,
            {
                "generate": "generate_answer",
                "rewrite": "rewrite_question",
            }
        )

        # After answer generation, evaluate quality
        workflow.add_conditional_edges(
            "generate_answer",
            self.grade_generation_vs_question,
            {
                "useful": END,
                "not_useful": "rewrite_question",
            }
        )

        # After rewriting, go back to generate_query_or_respond
        workflow.add_edge("rewrite_question", "generate_query_or_respond")

        return workflow.compile()

    # =============================================================================
    # NODE IMPLEMENTATIONS
    # =============================================================================

    def generate_query_or_respond(self, state: AgenticRAGState) -> AgenticRAGState:
        """
        Generate query using retrieval tool or respond directly
        Following LangGraph tutorial pattern
        """
        print("🧠 Node: generate_query_or_respond")

        messages = state["messages"]

        # Track original query on first attempt
        if not state.get("original_query") and messages:
            last_human_msg = next((msg for msg in reversed(messages) if isinstance(msg, HumanMessage)), None)
            if last_human_msg:
                return {
                    "original_query": last_human_msg.content,
                    "current_query": last_human_msg.content,
                    "messages": [self.llm_with_tools.invoke(messages)]
                }

        # Use current query for subsequent attempts
        current_query = state.get("current_query", "")
        if current_query:
            # Create new message with rewritten query
            rewritten_messages = messages + [HumanMessage(content=current_query)]
            response = self.llm_with_tools.invoke(rewritten_messages)
            return {"messages": [response]}

        # Fallback
        response = self.llm_with_tools.invoke(messages)
        return {"messages": [response]}

    def grade_documents(self, state: AgenticRAGState) -> AgenticRAGState:
        """
        Grade retrieved documents for relevance to question
        """
        print("📊 Node: grade_documents")

        messages = state["messages"]

        # Get the last tool call result (retrieved documents)
        last_message = messages[-1]
        if hasattr(last_message, 'content') and last_message.content:
            retrieved_docs = last_message.content
        else:
            retrieved_docs = "No documents retrieved"

        # Get the current query
        current_query = state.get("current_query", state.get("original_query", ""))

        # Grade document relevance
        grade_prompt = f"""You are a grader assessing relevance of retrieved CV documents to a user question.

Here is the retrieved CV content:
{retrieved_docs}

Here is the user question: {current_query}

Grade as "relevant" if the CV content contains information that can answer the question, including:
- PROJECTS section for questions about projects, side projects, or "projets"
- TECHNICAL SKILLS for technology questions
- EXPERIENCE sections for work history
- Any semantic meaning related to the question

The CV content should be graded as relevant if it contains the information needed to answer the question."""

        grade = self.doc_grader.invoke([HumanMessage(content=grade_prompt)])

        print(f"📊 Document relevance: {grade.binary_score}")

        return {
            "document_grade": grade.binary_score,
            "retrieval_attempts": state.get("retrieval_attempts", 0) + 1
        }

    def decide_to_generate(self, state: AgenticRAGState) -> Literal["generate", "rewrite"]:
        """
        Decision node to generate answer or rewrite question based on document grade
        """
        print("🤔 Decision: decide_to_generate")

        # Check iteration limit first
        if state.get("retrieval_attempts", 0) >= 3:
            print("🔄 Max iterations reached, forcing generation")
            return "generate"

        document_grade = state.get("document_grade", "not_relevant")
        print(f"📊 Document grade: {document_grade}")

        if document_grade == "relevant":
            return "generate"
        else:
            return "rewrite"

    def generate_answer(self, state: AgenticRAGState) -> AgenticRAGState:
        """
        Generate answer based on retrieved documents
        """
        print("✍️ Node: generate_answer")

        messages = state["messages"]

        # Get retrieved documents from the last tool message
        retrieved_docs = ""
        for msg in reversed(messages):
            if hasattr(msg, 'content') and msg.content and "Samuel" in str(msg.content):
                retrieved_docs = msg.content
                break

        current_query = state.get("current_query", state.get("original_query", ""))

        # Generate answer with improved project recognition
        generation_prompt = f"""You are an assistant for question-answering tasks about Samuel's CV.
Use the following retrieved CV information to answer the question.

CRITICAL ANTI-HALLUCINATION RULES:
- ONLY use information explicitly stated in the retrieved CV content below
- NEVER invent or assume details not present in the CV
- If you cannot answer based on the CV content, say so clearly
- Quote or reference the CV content when possible

IMPORTANT: When answering about projects, side projects, or "projets":
- Look for the "PROJECTS:" section in the CV content
- These are Samuel's actual projects and should be presented clearly
- Include project names, years, and key technologies when available

Retrieved CV Information:
{retrieved_docs}

Question: {current_query}

Provide a helpful answer based only on the CV information above."""

        response = self.llm.invoke([HumanMessage(content=generation_prompt)])

        return {"messages": [response]}

    def grade_generation_vs_question(self, state: AgenticRAGState) -> Literal["useful", "not_useful"]:
        """
        Grade whether the generated answer addresses the question
        """
        print("🎯 Decision: grade_generation_vs_question")

        messages = state["messages"]
        current_query = state.get("current_query", state.get("original_query", ""))

        # Get the last generated answer
        last_message = messages[-1]
        answer = last_message.content if hasattr(last_message, 'content') else str(last_message)

        # Grade answer usefulness
        grade_prompt = f"""You are a grader assessing whether an answer addresses/resolves a question.

Question: {current_query}
Answer: {answer}

Give a binary score to indicate whether the answer addresses the question and is useful."""

        grade = self.answer_grader.invoke([HumanMessage(content=grade_prompt)])

        print(f"🎯 Answer grade: {grade.binary_score}")

        return grade.binary_score

    def rewrite_question(self, state: AgenticRAGState) -> AgenticRAGState:
        """
        Rewrite the question to improve retrieval
        """
        print("🔄 Node: rewrite_question")

        original_query = state.get("original_query", "")
        current_query = state.get("current_query", original_query)

        # Rewrite prompt tailored for CV queries
        rewrite_prompt = f"""You are a question rewriter for CV search.

The original question was: {original_query}
The current query attempt was: {current_query}

This query failed to retrieve relevant CV information. Rewrite it to be more specific and likely to match CV content.

Consider these CV search strategies:
- Use professional terminology (e.g., "side projects" instead of "projets on the side")
- Be specific about what CV section to search (experience, skills, projects, education)
- Use common CV keywords (technologies, job titles, achievements)
- Translate foreign terms to English if needed

Return ONLY the rewritten question, nothing else."""

        response = self.llm.invoke([HumanMessage(content=rewrite_prompt)])
        rewritten_query = response.content.strip()

        print(f"🔄 Rewritten query: '{current_query}' → '{rewritten_query}'")

        return {
            "current_query": rewritten_query
        }

    # =============================================================================
    # PUBLIC INTERFACE
    # =============================================================================

    def search(self, query: str, thread_id: str = "default") -> dict:
        """
        Main entry point for agentic CV search
        """
        print(f"🚀 Starting agentic RAG search for: '{query}'")

        # Create initial state
        initial_state = AgenticRAGState(
            messages=[HumanMessage(content=query)],
            original_query=query,
            current_query=query,
            retrieval_attempts=0,
            document_grade="",
            answer_grade=""
        )

        # Run the graph
        result = self.graph.invoke(initial_state)

        # Extract final answer
        final_messages = result.get("messages", [])
        if final_messages:
            final_answer = final_messages[-1].content
        else:
            final_answer = "No answer generated"

        return {
            "query": query,
            "answer": final_answer,
            "retrieval_attempts": result.get("retrieval_attempts", 0),
            "final_query": result.get("current_query", query),
            "context": final_messages
        }


# =============================================================================
# FACTORY FUNCTION
# =============================================================================

def create_agentic_cv_rag(simple_rag: SimpleRAG) -> AgenticCVRAG:
    """
    Factory function to create AgenticCVRAG instance
    """
    return AgenticCVRAG(simple_rag)
