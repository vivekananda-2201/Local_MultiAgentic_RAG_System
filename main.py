"""
Main FastAPI application for Local MultiAgentic RAG System
Entry point for the backend server
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
from pathlib import Path
import warnings

# Suppress deprecation warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)
from langchain_core._api.deprecation import LangChainDeprecationWarning
warnings.filterwarnings("ignore", category=LangChainDeprecationWarning)

# Import routes
from backend.api.routes import chat, knowledge
from backend.config.settings import API_HOST, API_PORT

# Initialize FastAPI app
app = FastAPI(
    title="Local MultiAgentic RAG System",
    description="A production-grade RAG system with multi-agent architecture",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(chat.router)
app.include_router(knowledge.router)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "Local MultiAgentic RAG System",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "chat": "/api/chat/message",
            "websocket": "/api/chat/ws/{session_id}",
            "knowledge": "/api/knowledge/stats",
            "docs": "/docs"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Local MultiAgentic RAG System"
    }


# Serve frontend if available
frontend_path = Path(__file__).parent / "frontend" / "dist"
if frontend_path.exists():
    app.mount("/", StaticFiles(directory=str(frontend_path), html=True), name="frontend")


if __name__ == "__main__":
    import uvicorn
    print(f"Starting server on {API_HOST}:{API_PORT}")
    uvicorn.run(app, host=API_HOST, port=API_PORT, reload=False)