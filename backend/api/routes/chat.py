"""
Chat API routes for FastAPI application
Handles chat endpoint and message processing
"""
from fastapi import APIRouter, WebSocket, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
import uuid
import json
from typing import Optional
from backend.core.rag_chat import RAGChat
from backend.database.chat_db import ChatDatabase
from backend.modules.pdf_loader import load_pdf_documents
from backend.modules.text_splitter import split_documents
from backend.modules.vector_db import VectorStore

router = APIRouter(prefix="/api/chat", tags=["chat"])

# Global instances
chat_instances = {}
db = ChatDatabase()
vector_store = VectorStore()


# Request/Response models
from pydantic import BaseModel


class MessageRequest(BaseModel):
    """Chat message request"""
    message: str
    session_id: Optional[str] = None


class MessageResponse(BaseModel):
    """Chat message response"""
    response: str
    session_id: str
    sources: list = []


class SessionInfo(BaseModel):
    """Session information"""
    id: str
    title: str
    created_at: str
    updated_at: str


def get_or_create_chat(session_id: str) -> RAGChat:
    """Get existing chat instance or create new one"""
    if session_id not in chat_instances:
        chat_instances[session_id] = RAGChat()
    return chat_instances[session_id]


@router.post("/message")
async def send_message(request: MessageRequest) -> MessageResponse:
    """
    Send a message and get a response
    
    Args:
        request: MessageRequest with message and optional session_id
        
    Returns:
        MessageResponse with response and session info
    """
    # Generate session ID if not provided
    session_id = request.session_id or str(uuid.uuid4())

    # Create session in database if new
    if not db.get_session(session_id):
        db.create_session(session_id)

    # Get or create chat instance
    chat = get_or_create_chat(session_id)

    # Process query
    response = chat.process_query(request.message)

    # Save to database
    db.add_message(session_id, "user", request.message)
    db.add_message(session_id, "assistant", response, sources=[])

    return MessageResponse(
        response=response,
        session_id=session_id,
        sources=[]
    )


@router.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """
    WebSocket endpoint for streaming responses
    """
    await websocket.accept()
    
    # Create session if new
    if not db.get_session(session_id):
        db.create_session(session_id)
    
    # Get or create chat instance
    chat = get_or_create_chat(session_id)
    
    try:
        while True:
            # Receive message
            data = await websocket.receive_text()
            message_data = json.loads(data)
            user_message = message_data.get("message", "")

            if not user_message:
                continue

            # Save user message
            db.add_message(session_id, "user", user_message)

            # Stream response
            full_response = ""
            for chunk in chat.process_query_stream(user_message):
                full_response += chunk
                await websocket.send_text(json.dumps({
                    "type": "stream",
                    "content": chunk
                }))

            # Save full response
            db.add_message(session_id, "assistant", full_response)

            # Send completion signal
            await websocket.send_text(json.dumps({
                "type": "complete",
                "content": ""
            }))

    except Exception as e:
        print(f"WebSocket error: {e}")
        await websocket.close(code=1000)


@router.get("/sessions")
async def get_sessions():
    """Get all chat sessions"""
    sessions = db.get_all_sessions()
    return {
        "sessions": sessions,
        "count": len(sessions)
    }


@router.get("/session/{session_id}")
async def get_session(session_id: str):
    """Get session and message history"""
    session = db.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    messages = db.get_messages(session_id)
    return {
        "session": session,
        "messages": messages,
        "message_count": len(messages)
    }


@router.post("/session/create")
async def create_session(title: str = "New Chat"):
    """Create a new chat session"""
    session_id = str(uuid.uuid4())
    db.create_session(session_id, title)
    return {
        "session_id": session_id,
        "title": title,
        "status": "created"
    }


@router.delete("/session/{session_id}")
async def delete_session(session_id: str):
    """Delete a session"""
    success = db.delete_session(session_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete session")

    # Remove from cache
    if session_id in chat_instances:
        del chat_instances[session_id]

    return {"status": "deleted", "session_id": session_id}


@router.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    """
    Upload and process PDF file
    Adds new content to vector database
    """
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="File must be a PDF")

    try:
        # Save file to knowledge base
        from backend.config.settings import KNOWLEDGE_BASE_DIR
        import os

        file_path = os.path.join(KNOWLEDGE_BASE_DIR, file.filename)
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)

        # Load and process PDF
        documents = load_pdf_documents()
        if documents:
            chunks = split_documents(documents)
            added = vector_store.add_documents(chunks)

            return {
                "status": "success",
                "filename": file.filename,
                "chunks_added": added
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to process PDF")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload error: {str(e)}")
