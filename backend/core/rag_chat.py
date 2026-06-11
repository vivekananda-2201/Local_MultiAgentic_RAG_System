"""
Core RAG Chat Pipeline
Orchestrates the multi-agent RAG workflow
"""
from typing import List, Dict, Any, Generator
from backend.modules.vector_db import VectorStore
from backend.agents.query_parser import parse_queries
from backend.agents.rag_query_agent import refine_search_query
from backend.agents.response_agent import generate_response, generate_response_stream
from backend.config.settings import (
    SIMILARITY_THRESHOLD,
    TOP_K_CHUNKS,
    CONTEXT_TURNS
)


class RAGChat:
    """
    Orchestrates the complete RAG pipeline:
    1. Query parsing (resolve pronouns)
    2. Query refinement (optimize for search)
    3. Vector search (retrieve relevant chunks)
    4. Response generation (with context)
    """

    def __init__(self):
        """Initialize RAG Chat with vector store"""
        self.vector_store = VectorStore()
        self.conversation_history: List[Dict[str, str]] = []
        self.context_turns = CONTEXT_TURNS

    def add_to_history(self, role: str, content: str):
        """
        Add message to conversation history
        
        Args:
            role (str): Message role (user/assistant)
            content (str): Message content
        """
        self.conversation_history.append({"role": role, "content": content})

    def get_recent_context(self, turns: int = None) -> str:
        """
        Get recent conversation context for agent input
        
        Args:
            turns (int): Number of user-assistant exchanges to include
            
        Returns:
            str: Formatted recent conversation context
        """
        turns = turns or self.context_turns
        filtered = [m for m in self.conversation_history if m['role'] in ('user', 'assistant')]

        if not filtered or turns <= 0:
            return ""

        recent = filtered[-(turns * 2):]
        return "\n".join([f"{m['role']}: {m['content']}" for m in recent])

    def search_knowledge_base(self, query: str) -> List[Dict[str, Any]]:
        """
        Search vector database for relevant chunks
        
        Args:
            query (str): Search query
            
        Returns:
            List[Dict]: Relevant chunks with scores
        """
        results = self.vector_store.search(
            query=query,
            k=TOP_K_CHUNKS,
            score_threshold=SIMILARITY_THRESHOLD
        )
        return results

    def format_context(self, chunks: List[Dict[str, Any]]) -> str:
        """
        Format retrieved chunks into context string
        
        Args:
            chunks (List[Dict]): Retrieved chunks
            
        Returns:
            str: Formatted context
        """
        if not chunks:
            return "No relevant information found in knowledge base."

        context_parts = []
        for i, chunk in enumerate(chunks, 1):
            source = chunk.get('source', 'Unknown')
            page = chunk.get('page', 'N/A')
            score = chunk.get('score', 0)
            content = chunk.get('content', '')

            context_parts.append(
                f"[Source {i}]: {source} (Page {page}, Score: {score:.2f})\n{content}"
            )

        return "\n\n".join(context_parts)

    def process_query(self, user_query: str) -> str:
        """
        Process a user query through the complete RAG pipeline
        
        Args:
            user_query (str): User's question
            
        Returns:
            str: Generated response
        """
        # Add user query to history
        self.add_to_history("user", user_query)

        # Step 1: Parse and resolve queries
        recent_context = self.get_recent_context()
        parsed_queries = parse_queries(user_query, recent_context)

        # Step 2: Search knowledge base for each parsed query
        all_chunks = []
        for query in parsed_queries:
            # Refine query for better search
            refined_query = refine_search_query(query, recent_context)
            # Search vector database
            chunks = self.search_knowledge_base(refined_query)
            all_chunks.extend(chunks)

        # Step 3: Format context
        formatted_context = self.format_context(all_chunks)

        # Step 4: Generate response with context
        response = generate_response(
            user_query=user_query,
            rag_context=formatted_context,
            conversation_history=self.conversation_history[:-1]  # Exclude current user message
        )

        # Add assistant response to history
        self.add_to_history("assistant", response)

        return response

    def process_query_stream(self, user_query: str) -> Generator[str, None, None]:
        """
        Process a user query and stream the response
        
        Args:
            user_query (str): User's question
            
        Yields:
            str: Response chunks
        """
        # Add user query to history
        self.add_to_history("user", user_query)

        # Step 1: Parse and resolve queries
        recent_context = self.get_recent_context()
        parsed_queries = parse_queries(user_query, recent_context)

        # Step 2: Search knowledge base for each parsed query
        all_chunks = []
        for query in parsed_queries:
            # Refine query for better search
            refined_query = refine_search_query(query, recent_context)
            # Search vector database
            chunks = self.search_knowledge_base(refined_query)
            all_chunks.extend(chunks)

        # Step 3: Format context
        formatted_context = self.format_context(all_chunks)

        # Step 4: Generate streaming response
        full_response = ""
        for chunk in generate_response_stream(
            user_query=user_query,
            rag_context=formatted_context,
            conversation_history=self.conversation_history[:-1]
        ):
            full_response += chunk
            yield chunk

        # Add complete response to history
        self.add_to_history("assistant", full_response)

    def get_sources(self) -> List[Dict[str, str]]:
        """
        Get metadata about available knowledge sources
        
        Returns:
            List[Dict]: Information about sources
        """
        stats = self.vector_store.get_collection_stats()
        return {
            "total_chunks": stats["total_chunks"],
            "sources": stats["sources"],
            "total_sources": stats["total_sources"]
        }
