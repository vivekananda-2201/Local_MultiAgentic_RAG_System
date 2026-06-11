"""
PDF loader module for loading PDF documents from knowledge base directory
"""
import warnings
from pathlib import Path
from langchain_community.document_loaders import PyPDFDirectoryLoader
from backend.config.settings import KNOWLEDGE_BASE_DIR

warnings.filterwarnings("ignore", category=DeprecationWarning)
from langchain_core._api.deprecation import LangChainDeprecationWarning
warnings.filterwarnings("ignore", category=LangChainDeprecationWarning)


def load_pdf_documents():
    """
    Load all PDF documents from the knowledge base directory
    
    Returns:
        list: List of Document objects from all PDFs
        
    Raises:
        Exception: If error occurs during PDF loading
    """
    try:
        document_loader = PyPDFDirectoryLoader(str(KNOWLEDGE_BASE_DIR))
        documents = document_loader.load()
        return documents
    except Exception as e:
        print(f"Error loading PDF documents: {e}")
        return None


def get_available_pdfs():
    """
    Get list of available PDF files in knowledge base
    
    Returns:
        list: List of PDF file names in knowledge base directory
    """
    pdf_path = Path(KNOWLEDGE_BASE_DIR)
    if not pdf_path.exists():
        return []
    return [f.name for f in pdf_path.glob("*.pdf")]
