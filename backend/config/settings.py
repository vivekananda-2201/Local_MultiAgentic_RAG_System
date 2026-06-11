"""
Configuration settings for the Local MultiAgentic RAG System
"""
import os
from pathlib import Path

# Project root
PROJECT_ROOT = Path(__file__).parent.parent.parent

# Database paths
KNOWLEDGE_BASE_DIR = PROJECT_ROOT / "knowledge_base"
CHROMA_DB_PATH = PROJECT_ROOT / "chroma_db"
CHAT_DB_PATH = PROJECT_ROOT / "chat_history.db"

# Ollama Models
LLM_MODEL = "qwen2.5:3b"
EMBEDDING_MODEL = "bge-m3:latest"

# RAG Configuration
SIMILARITY_THRESHOLD = 0.6
TOP_K_CHUNKS = 5
CONTEXT_TURNS = 3  # Number of previous conversation turns to include as context

# API Configuration
API_HOST = "0.0.0.0"
API_PORT = 8000
API_RELOAD = True

# File Upload
ALLOWED_EXTENSIONS = {"pdf"}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB

# Create directories if they don't exist
os.makedirs(KNOWLEDGE_BASE_DIR, exist_ok=True)
os.makedirs(CHROMA_DB_PATH, exist_ok=True)
