# Local MultiAgentic RAG System

A production-grade Retrieval Augmented Generation (RAG) system with a multi-agent architecture, powered by Ollama for local LLM inference. This system features intelligent query parsing, semantic search, and multi-turn conversation support with a modern React + TypeScript frontend.

## 🎯 Project Overview

The **Local MultiAgentic RAG System** is designed to provide an enterprise-grade solution for building intelligent conversational applications that can access and reason over custom knowledge bases. It combines multiple specialized agents to break down complex queries, retrieve relevant information, and generate contextually accurate responses.

### Key Features

- **Multi-Agent Architecture**: Specialized agents for query parsing, refinement, and response generation
- **Semantic Search**: Vector-based retrieval using Chroma and Ollama embeddings
- **Local Inference**: Run entirely on your machine using Ollama - no external APIs required
- **Modular Backend**: FastAPI-based architecture with clean separation of concerns
- **Modern Frontend**: React + TypeScript with responsive, cyberpunk-themed UI
- **SQLite Persistence**: Store conversations and metadata locally
- **Session Management**: Multi-session support with full conversation history
- **Production-Ready**: Error handling, logging, and scalable architecture

## 🏗️ Architecture

### System Components

```
┌─────────────────────────────────────────────────────────┐
│                   Frontend (React + TS)                  │
│  ┌──────────┬──────────────┬──────────────────────────┐  │
│  │ Sidebar  │   Chat UI    │   Sources Panel          │  │
│  └──────────┴──────────────┴──────────────────────────┘  │
└────────────────┬─────────────────────────────────────────┘
                 │ HTTP/WebSocket (REST API)
┌────────────────┴─────────────────────────────────────────┐
│              FastAPI Backend (Python)                     │
│  ┌──────────────────────────────────────────────────────┐│
│  │              API Routes Layer                         ││
│  │  ├─ Chat Endpoints      ├─ Knowledge Base           ││
│  │  ├─ Session Management  └─ File Upload             ││
│  └──────────────────────────────────────────────────────┘│
│  ┌──────────────────────────────────────────────────────┐│
│  │           Multi-Agent RAG Pipeline                    ││
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐           ││
│  │  │ Query    │→ │ RAG      │→ │Response  │           ││
│  │  │ Parser   │  │ Query    │  │Generator │           ││
│  │  │ Agent    │  │ Agent    │  │ Agent    │           ││
│  │  └──────────┘  └──────────┘  └──────────┘           ││
│  └──────────────────────────────────────────────────────┘│
│  ┌──────────────────────────────────────────────────────┐│
│  │           Data & Storage Layer                        ││
│  │  ├─ Vector DB (Chroma)      ├─ Chat DB (SQLite)    ││
│  │  ├─ PDF Processing          └─ Embeddings (Ollama) ││
│  └──────────────────────────────────────────────────────┘│
└──────────────────────────────────────────────────────────┘
```

## 🚀 Multi-Agentic Verification Pipeline

The system implements a sophisticated multi-agent verification pipeline:

### 1. Query Parser Agent
- **Purpose**: Analyzes user queries in context of conversation history
- **Functionality**:
  - Resolves pronouns and contextual references
  - Splits compound questions into focused sub-queries
  - Generates explicit, self-contained search queries
  - Handles follow-up questions by enriching with prior context

**Example**:
```
User: "Tell me more about them"
Context: [Prior discussion about Indian laws]
→ Resolved: "Indian laws detailed explanation"
```

### 2. RAG Query Agent
- **Purpose**: Optimizes queries for vector database search
- **Functionality**:
  - Refines parsed queries for semantic similarity
  - Adds domain-specific keywords and context
  - Ensures optimal retrieval from knowledge base
  - Adapts to conversation context

**Example**:
```
Query: "What are fundamental rights?"
Context: [Discussion about Indian Constitution]
→ Refined: "Fundamental rights Indian Constitution Article 12-35 explanation"
```

### 3. Response Generation Agent
- **Purpose**: Generates accurate, context-aware responses
- **Functionality**:
  - Synthesizes information from retrieved chunks
  - Maintains consistency with conversation history
  - Cites sources appropriately
  - Falls back gracefully when information is unavailable

**Verification mechanisms**:
- Context relevance scoring
- Source attribution
- Factual consistency checking
- Conversation coherence validation

## 📁 Project Structure

```
Local_MultiAgentic_RAG_System/
├── backend/                          # Backend FastAPI application
│   ├── config/
│   │   └── settings.py              # Central configuration
│   ├── core/
│   │   └── rag_chat.py              # RAG pipeline orchestration
│   ├── agents/
│   │   ├── models.py                # Model configurations
│   │   ├── query_parser.py          # Query resolution agent
│   │   ├── rag_query_agent.py       # Query refinement agent
│   │   └── response_agent.py        # Response generation agent
│   ├── modules/
│   │   ├── embedding_function.py    # Ollama embeddings
│   │   ├── pdf_loader.py            # PDF document loading
│   │   ├── text_splitter.py         # Document chunking
│   │   └── vector_db.py             # Chroma operations
│   ├── database/
│   │   └── chat_db.py               # SQLite operations
│   ├── api/
│   │   └── routes/
│   │       ├── chat.py              # Chat endpoints
│   │       ├── knowledge.py         # Knowledge base endpoints
│   │       └── __init__.py
│   └── main.py                      # Uvicorn, startup config (imported as main.py in root)
│
├── frontend/                         # React + TypeScript application
│   ├── src/
│   │   ├── components/
│   │   │   ├── Chat/               # Chat interface
│   │   │   ├── Sidebar/            # Session management
│   │   │   ├── SourcesPanel/       # Retrieved sources display
│   │   │   └── Common/             # Shared components
│   │   ├── pages/                  # Page components
│   │   ├── services/
│   │   │   └── apiService.ts       # API client
│   │   ├── hooks/
│   │   │   └── index.ts            # Custom React hooks
│   │   ├── types/
│   │   │   └── index.ts            # TypeScript types
│   │   ├── utils/
│   │   │   └── index.ts            # Utility functions
│   │   ├── styles/
│   │   │   ├── globals.css         # Global styles
│   │   │   └── theme.ts            # Theme configuration
│   │   ├── App.tsx                 # Main app component
│   │   └── main.tsx                # React entry point
│   ├── public/                     # Static assets
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   └── index.html
│
├── knowledge_base/                  # PDF documents folder
├── chroma_db/                       # Vector database storage
├── main.py                          # FastAPI entry point
├── requirements_backend.txt         # Python dependencies
├── requirements.txt                 # Legacy
├── README.md                        # This file
└── LICENSE

```

## 🔧 Installation & Setup

### Prerequisites

- **Python 3.9+**
- **Node.js 18+**
- **Ollama** (Download from [ollama.ai](https://ollama.ai))

### Backend Setup

1. **Install Python dependencies**:
```bash
pip install -r requirements_backend.txt
```

2. **Pull required Ollama models**:
```bash
# LLM model for agents
ollama pull qwen2.5:3b

# Embedding model for semantic search
ollama pull bge-m3:latest
```

3. **Verify Ollama is running** (should be accessible at `http://localhost:11434`)

### Frontend Setup

1. **Navigate to frontend directory**:
```bash
cd frontend
```

2. **Install Node dependencies**:
```bash
npm install
```

3. **Create environment file**:
```bash
cp .env.example .env
# Edit .env if needed (default points to localhost:8000)
```

## 🚀 Running the Application

### Start Backend

From project root:
```bash
python main.py
```

The backend will start at `http://localhost:8000`

Available endpoints:
- API: `http://localhost:8000/api/`
- Docs: `http://localhost:8000/docs`

### Start Frontend

In a new terminal:
```bash
cd frontend
npm run dev
```

Frontend will be available at `http://localhost:3000`

### Using the Application

1. **Add Knowledge Base**:
   - Place PDF files in `./knowledge_base/` directory
   - Or use the upload feature in the UI
   - Frontend will automatically index new PDFs

2. **Chat Interface**:
   - Type questions in the input box
   - Chat history is automatically saved in SQLite
   - Sources are displayed alongside responses

3. **Session Management**:
   - Create new chat sessions using the "+" button
   - View all past sessions in the sidebar
   - Delete sessions to clean up

## 📊 Database Schema

### SQLite Tables

#### `sessions`
Stores chat session metadata:
```sql
CREATE TABLE sessions (
    id TEXT PRIMARY KEY,
    title TEXT DEFAULT 'New Chat',
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    metadata TEXT -- JSON metadata
);
```

#### `messages`
Stores all messages in sessions:
```sql
CREATE TABLE messages (
    id INTEGER PRIMARY KEY,
    session_id TEXT,
    role TEXT,              -- 'user' or 'assistant'
    content TEXT,
    sources TEXT,           -- JSON array of sources
    tokens_used INTEGER,
    timestamp TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES sessions(id)
);
```

#### `chunk_references`
Tracks which chunks were used for each message:
```sql
CREATE TABLE chunk_references (
    id INTEGER PRIMARY KEY,
    message_id INTEGER,
    chunk_id TEXT,
    source_file TEXT,
    page_number INTEGER,
    relevance_score REAL,
    FOREIGN KEY (message_id) REFERENCES messages(id)
);
```

#### `conversation_metadata`
Stores additional session metadata:
```sql
CREATE TABLE conversation_metadata (
    id INTEGER PRIMARY KEY,
    session_id TEXT,
    key TEXT,
    value TEXT,
    FOREIGN KEY (session_id) REFERENCES sessions(id)
);
```

### Vector Database (Chroma)

- **Collection**: `pdf_chunks`
- **Embeddings**: bge-m3 (384-dimensional vectors)
- **Similarity Metric**: Cosine similarity
- **Chunk Size**: 600 tokens
- **Chunk Overlap**: 200 tokens
- **Threshold**: 0.6 similarity score

## 🤖 Agent Specifications

### Query Parser Agent
- **Model**: qwen2.5:3b
- **Input**: User query + recent conversation context
- **Output**: List of explicit search queries
- **Key Features**:
  - Pronoun resolution
  - Context enrichment
  - Query decomposition

### RAG Query Agent
- **Model**: qwen2.5:3b
- **Input**: Parsed query + conversation context
- **Output**: Optimized search query
- **Key Features**:
  - Keyword extraction
  - Domain adaptation
  - Semantic optimization

### Response Agent
- **Model**: qwen2.5:3b
- **Input**: Question + retrieved context + history
- **Output**: Natural language response
- **Key Features**:
  - Context synthesis
  - Source attribution
  - Hallucination prevention

## 📡 API Endpoints

### Chat API

```
POST /api/chat/message
- Send a message and get a response
- Request: { message: string, session_id?: string }
- Response: { response: string, session_id: string, sources: [] }

WebSocket /api/chat/ws/{session_id}
- Streaming responses via WebSocket
- Message format: { message: string }

GET /api/chat/sessions
- Get all sessions

GET /api/chat/session/{session_id}
- Get specific session with messages

POST /api/chat/session/create
- Create new session

DELETE /api/chat/session/{session_id}
- Delete session
```

### Knowledge Base API

```
GET /api/knowledge/stats
- Get knowledge base statistics

GET /api/knowledge/structure
- Get KB structure (files → pages → chunks)

GET /api/knowledge/chunks
- Get all indexed chunks

POST /api/knowledge/refresh
- Refresh/reindex knowledge base

GET /api/knowledge/search?query=...&k=5
- Search knowledge base
```

## 🎨 Frontend Features

### Components

- **Chat**: Main conversation interface with auto-scroll
- **Sidebar**: Session management with quick access
- **SourcesPanel**: Display retrieved sources with scores
- **Common**: Reusable UI components

### Hooks

- `useChat()`: Chat state management
- `useSessions()`: Session management
- `useKnowledgeBase()`: Knowledge base operations
- `useWebSocket()`: WebSocket connection handling

### Styling

- Cyberpunk-inspired dark theme
- Responsive design (mobile, tablet, desktop)
- Smooth animations and transitions
- Accessibility-focused

## 🔒 Security Considerations

- CORS configured for localhost only (configure for production)
- No external API calls - completely local
- PDFs processed locally without transmission
- SQLite database is local and encrypted via filesystem permissions
- Implement authentication layer for production deployment

## 📈 Performance Optimization

- **Chunking Strategy**: 600 tokens with 200-token overlap optimizes balance between context and retrieval
- **Similarity Threshold**: 0.6 ensures relevant results while maintaining precision
- **Context Window**: Last 3 conversational turns (6 messages) for agent context
- **Embedding Model**: bge-m3 provides high-quality semantic representations

## 🛠️ Development & Maintenance

### Adding Custom Agents

1. Create new agent file in `backend/agents/`
2. Implement agent logic using Ollama chat API
3. Register in `backend/core/rag_chat.py`
4. Update API routes if needed

### Customizing the Frontend

- Modify component files in `frontend/src/components/`
- Update styles in component `.css` files
- Extend types in `frontend/src/types/index.ts`
- Add hooks in `frontend/src/hooks/index.ts`

### Extending Knowledge Base

- Add PDFs to `knowledge_base/` directory
- Use upload endpoint to add files programmatically
- System automatically detects and indexes new PDFs
- Use `/api/knowledge/refresh` to reprocess all files

## 📚 Dependencies

### Backend
- **FastAPI**: Modern async web framework
- **Uvicorn**: ASGI server
- **LangChain**: LLM and vector store abstractions
- **Chroma**: Vector database
- **Ollama**: Local LLM inference
- **SQLite3**: Persistent message storage

### Frontend
- **React 18**: UI framework
- **TypeScript**: Type-safe JavaScript
- **Axios**: HTTP client
- **Vite**: Build tool and dev server
- **Marked**: Markdown rendering
- **Lucide React**: Icon library

## 🐛 Troubleshooting

### Ollama Models Not Found
```bash
# Verify Ollama is running
ollama list

# Re-pull required models
ollama pull qwen2.5:3b
ollama pull bge-m3:latest
```

### Backend Connection Issues
- Ensure port 8000 is available
- Check CORS settings if frontend can't reach backend
- Verify Ollama is running on port 11434

### Frontend Build Issues
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
npm run build
```

## 📝 License

This project is licensed under the MIT License - see LICENSE file for details.

## 🙋 Support & Contributing

For issues, questions, or contributions:
1. Check existing documentation
2. Review the project structure and code comments
3. Test locally before submitting changes
4. Follow the existing code style and patterns

## 🚀 Future Enhancements

- [ ] User authentication and authorization
- [ ] Fine-tuning support for domain-specific models
- [ ] Advanced query expansion and synonymy handling
- [ ] Document versioning and management
- [ ] Real-time collaboration features
- [ ] Advanced analytics and insights
- [ ] Multi-language support
- [ ] GPU optimization for faster inference
- [ ] API rate limiting and usage tracking
- [ ] Backup and disaster recovery

---

**Last Updated**: June 2026  
**Version**: 1.0.0  
**Status**: Production-Ready