"""
Embedding function module for generating embeddings using Ollama
"""
import warnings
from langchain_community.embeddings import OllamaEmbeddings
from backend.config.settings import EMBEDDING_MODEL

warnings.filterwarnings("ignore", category=DeprecationWarning)
from langchain_core._api.deprecation import LangChainDeprecationWarning
warnings.filterwarnings("ignore", category=LangChainDeprecationWarning)


def get_embedding_function():
    """
    Get OllamaEmbeddings instance with configured model
    
    Returns:
        OllamaEmbeddings: Embedding function using configured model
    """
    embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL)
    return embeddings
