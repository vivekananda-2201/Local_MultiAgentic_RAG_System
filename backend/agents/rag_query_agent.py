"""
RAG Query Agent - Refines user queries for vector database search
Generates optimal search queries based on context
"""
import warnings
import ollama
from colorama import init, Fore, Style
from backend.agents.models import LLM_MODEL

init()
warnings.filterwarnings("ignore", category=DeprecationWarning)
from langchain_core._api.deprecation import LangChainDeprecationWarning
warnings.filterwarnings("ignore", category=LangChainDeprecationWarning)


def refine_search_query(query: str, conversation_context: str = "") -> str:
    """
    Refine user query for optimal vector database search
    
    Args:
        query (str): Original user query
        conversation_context (str): Previous conversation history
        
    Returns:
        str: Refined search query optimized for vector search
    """
    system_prompt = (
        "You are an AI agent that generates optimal search queries for RAG (Retrieval Augmented Generation) systems. "
        "Given a user query, generate a single, well-crafted search query that will retrieve the most relevant documents "
        "from a vector database. The query should be specific, clear, and include relevant keywords."
    )

    messages = [
        {"role": "system", "content": system_prompt},
    ]

    # Include conversation context if provided
    if conversation_context:
        messages.append({
            "role": "user",
            "content": f"Conversation context:\n{conversation_context}"
        })

    messages.append({
        "role": "user",
        "content": f"Query to refine: {query}"
    })

    try:
        response = ollama.chat(
            messages=messages,
            model=LLM_MODEL
        )
        refined_query = response['message']['content']
        
        print(
            f"{Fore.LIGHTMAGENTA_EX}[RAG Query Agent] Refined Search Query:{Style.RESET_ALL} {refined_query}\n"
        )
        return refined_query
    except Exception as e:
        print(f"{Fore.RED}[RAG Query Agent] Error refining query: {e}{Style.RESET_ALL}")
        return query
