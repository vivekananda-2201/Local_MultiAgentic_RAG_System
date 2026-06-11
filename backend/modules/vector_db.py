"""
Vector database module for managing Chroma vector store operations
"""
import os
import warnings
from typing import List, Dict, Any, Optional
from pathlib import Path
from colorama import init, Fore, Style
from langchain.schema import Document
from langchain.vectorstores.chroma import Chroma
from backend.modules.embedding_function import get_embedding_function
from backend.config.settings import CHROMA_DB_PATH

init()
warnings.filterwarnings("ignore", category=DeprecationWarning)
from langchain_core._api.deprecation import LangChainDeprecationWarning
warnings.filterwarnings("ignore", category=LangChainDeprecationWarning)


class VectorStore:
    """
    Manages Chroma vector store operations for RAG system
    """
    
    def __init__(self, collection_name: str = "pdf_chunks"):
        """
        Initialize VectorStore
        
        Args:
            collection_name (str): Name of the Chroma collection
        """
        self.db = Chroma(
            persist_directory=str(CHROMA_DB_PATH),
            embedding_function=get_embedding_function(),
            collection_name=collection_name
        )
        self.embeddings = get_embedding_function()
        self.collection_name = collection_name

    def add_documents(self, chunks: List[Document]) -> int:
        """
        Add documents to vector store
        
        Args:
            chunks (List[Document]): List of document chunks to add
            
        Returns:
            int: Number of new documents added
        """
        chunks_with_ids = self._get_chunk_ids(chunks)
        existing_items = self.db.get(include=[])
        existing_ids = set(existing_items["ids"])
        
        print(f"Number of existing documents in DB: {len(existing_ids)}")
        
        new_chunks = []
        for chunk in chunks_with_ids:
            if chunk.metadata["chunk_id"] not in existing_ids:
                new_chunks.append(chunk)
        
        if len(new_chunks):
            print(f"👉 Adding {len(new_chunks)} new documents to DB...")
            new_chunk_ids = [chunk.metadata["chunk_id"] for chunk in new_chunks]
            self.db.add_documents(new_chunks, ids=new_chunk_ids)
            self.db.persist()
            return len(new_chunks)
        else:
            print("✅ Database is up to date")
            return 0

    def search(self, query: str, k: int = 5, score_threshold: float = 0.6) -> List[Dict[str, Any]]:
        """
        Search for similar chunks in vector store
        
        Args:
            query (str): Search query
            k (int): Number of results to return
            score_threshold (float): Minimum similarity score
            
        Returns:
            List[Dict]: List of matching chunks with scores
        """
        results = self.db.similarity_search_with_score(query, k=k)
        filtered_results = []
        
        for doc, score in results:
            if score >= score_threshold:
                filtered_results.append({
                    "chunk_id": doc.metadata.get("chunk_id", "unknown"),
                    "content": doc.page_content,
                    "score": score,
                    "source": doc.metadata.get("source", "unknown"),
                    "page": doc.metadata.get("page", 0)
                })
        
        return filtered_results

    def get_all_chunks(self) -> List[Dict[str, Any]]:
        """
        Get all chunks from the database with their embeddings
        
        Returns:
            List[Dict]: All chunks with metadata and embeddings
        """
        results = self.db.get(include=['embeddings', 'documents', 'metadatas'])
        chunks = []
        for i, (doc, metadata, embedding) in enumerate(zip(
            results['documents'],
            results['metadatas'],
            results['embeddings']
        )):
            chunks.append({
                'id': results['ids'][i],
                'content': doc,
                'metadata': metadata,
                'embedding': embedding
            })
        return chunks

    def get_structure(self) -> Dict[str, Dict[Any, List[Dict[str, Any]]]]:
        """
        Return a nested structure: {source: {page: [chunks]}}
        
        Returns:
            Dict: Nested structure of knowledge base
        """
        chunks = self.get_all_chunks()
        structure: Dict[str, Dict[Any, List[Dict[str, Any]]]] = {}
        for chunk in chunks:
            source = chunk['metadata'].get('source', 'unknown')
            page = chunk['metadata'].get('page', 0)
            structure.setdefault(source, {}).setdefault(page, []).append(chunk)
        return structure

    def get_collection_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the collection
        
        Returns:
            Dict: Statistics including total chunks, sources, pages
        """
        structure = self.get_structure()
        total_chunks = sum(
            sum(len(chunks) for chunks in pages.values())
            for pages in structure.values()
        )
        return {
            "total_chunks": total_chunks,
            "total_sources": len(structure),
            "sources": list(structure.keys())
        }

    @staticmethod
    def _get_chunk_ids(chunks: List[Document]) -> List[Document]:
        """
        Generate unique chunk IDs based on source and page
        
        Args:
            chunks (List[Document]): List of document chunks
            
        Returns:
            List[Document]: Chunks with added chunk_id in metadata
        """
        last_page_id = None
        current_chunk_index = 0

        for chunk in chunks:
            source = chunk.metadata.get("source")
            page = chunk.metadata.get("page")
            current_page_id = f"{source}:{page}"

            if current_page_id == last_page_id:
                current_chunk_index += 1
            else:
                current_chunk_index = 0

            chunk_id = f"{current_page_id}:{current_chunk_index}"
            last_page_id = current_page_id
            chunk.metadata["chunk_id"] = chunk_id

        return chunks
