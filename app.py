import os
import uuid
import json
import sqlite3
import time
from datetime import datetime
from flask import Flask, request, jsonify, Response, stream_with_context, render_template, send_from_directory, abort
from flask_cors import CORS
from werkzeug.utils import secure_filename
import plotly.io as pio

# Import your existing modules
from main import Chat
from manage_database import DatabaseManager, get_embedding_function
from agents.no_of_queries import parse_queries
from agents.rag_query_agent import rag_query_agent
from agents.response_agent import generate_response_stream

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # change for production
CORS(app)

# Configuration
KNOWLEDGE_BASE_DIR = './knowledge_base'
CHAT_DB_PATH = './chat_history.db'
ALLOWED_EXTENSIONS = {'pdf'}

# In-memory storage for chat sessions (Chat instances)
chat_sessions = {}
db_manager = DatabaseManager()

# ---------------------------
# SQLite chat history helpers
# ---------------------------
def init_chat_db():
    conn = sqlite3.connect(CHAT_DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            id TEXT PRIMARY KEY,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            role TEXT,
            content TEXT,
            sources TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES sessions(id)
        )
    ''')
    conn.commit()
    conn.close()

def save_message(session_id, role, content, sources=None):
    conn = sqlite3.connect(CHAT_DB_PATH)
    c = conn.cursor()
    # Ensure session exists
    c.execute("INSERT OR IGNORE INTO sessions (id) VALUES (?)", (session_id,))
    sources_json = json.dumps(sources) if sources else None
    c.execute(
        "INSERT INTO messages (session_id, role, content, sources) VALUES (?, ?, ?, ?)",
        (session_id, role, content, sources_json)
    )
    conn.commit()
    conn.close()

def load_messages(session_id):
    conn = sqlite3.connect(CHAT_DB_PATH)
    c = conn.cursor()
    c.execute(
        "SELECT role, content, sources FROM messages WHERE session_id = ? ORDER BY timestamp",
        (session_id,)
    )
    rows = c.fetchall()
    conn.close()
    messages = []
    for role, content, sources_json in rows:
        sources = json.loads(sources_json) if sources_json else []
        messages.append({"role": role, "content": content, "sources": sources})
    return messages

def get_all_sessions():
    conn = sqlite3.connect(CHAT_DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, created_at FROM sessions ORDER BY created_at DESC")
    rows = c.fetchall()
    conn.close()
    return [{"id": r[0], "created_at": r[1]} for r in rows]

init_chat_db()

# ---------------------------
# Helper: get or create Chat instance
# ---------------------------
def get_chat(session_id):
    if session_id not in chat_sessions:
        chat_sessions[session_id] = Chat()
    return chat_sessions[session_id]

# ---------------------------
# Routes
# ---------------------------
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/chat/stream', methods=['GET'])
def chat_stream():
    session_id = request.args.get('session_id')
    user_input = request.args.get('message')
    if not session_id or not user_input:
        return jsonify({'error': 'Missing session_id or message'}), 400

    chat = get_chat(session_id)
    save_message(session_id, 'user', user_input)

    def generate():
        recent_context = chat.get_recent_conversation_context(chat.CONTEXT_TURNS)

        # ── AGENT 1: Query Parser ──
        yield f"event: agent\ndata: {json.dumps({'agent': 'query_parser', 'status': 'running', 'output': 'Parsing queries...'})}\n\n"
        try:
            queries = parse_queries(user_input, recent_context)
        except Exception as e:
            queries = [user_input]
            yield f"event: agent\ndata: {json.dumps({'agent': 'query_parser', 'status': 'error', 'output': f'Error: {str(e)}'})}\n\n"
        else:
            yield f"event: agent\ndata: {json.dumps({'agent': 'query_parser', 'status': 'done', 'output': queries})}\n\n"

        all_chunks = []

        # Pre-load all stored embeddings once for real-time viz
        import numpy as np
        from sklearn.metrics.pairwise import cosine_similarity as _cos_sim
        from langchain.vectorstores.chroma import Chroma as _Chroma
        _emb_fn = get_embedding_function()
        try:
            _viz_db = _Chroma(
                persist_directory="./chroma_db/",
                embedding_function=_emb_fn,
                collection_name="pdf_chunks"
            )
            _all = _viz_db.get(include=['embeddings'])
            _stored_embs = np.array(_all['embeddings']) if _all['embeddings'] else None
            _stored_ids  = _all['ids']
        except Exception:
            _stored_embs = None
            _stored_ids  = []

        # ── AGENT 2: RAG Query Refiner ──
        for query in queries:
            yield f"event: agent\ndata: {json.dumps({'agent': 'rag_query', 'status': 'running', 'output': f'Refining: {query[:80]}'})}\n\n"
            try:
                refined = rag_query_agent(query, {"conversation_history": recent_context})
            except Exception as e:
                refined = query
                yield f"event: agent\ndata: {json.dumps({'agent': 'rag_query', 'status': 'error', 'output': f'Error: {str(e)}'})}\n\n"
            else:
                yield f"event: agent\ndata: {json.dumps({'agent': 'rag_query', 'status': 'done', 'output': refined[:120]})}\n\n"

            # ── Emit real cosine scores at the exact moment RAG searches ──
            # This runs BEFORE Chroma's ANN search, using the same embedding model,
            # so the canvas lights up each chunk with its true cosine similarity score.
            if _stored_embs is not None and len(_stored_embs) > 0:
                try:
                    q_vec = np.array(_emb_fn.embed_query(refined)).reshape(1, -1)
                    sims  = _cos_sim(q_vec, _stored_embs)[0]
                    viz_payload = {
                        'refined_query': refined[:80],
                        'total': int(len(sims)),
                        'scores': [
                            {'chunk_id': _stored_ids[i], 'sim': float(sims[i])}
                            for i in range(len(sims))
                        ]
                    }
                    yield f"event: viz_search\ndata: {json.dumps(viz_payload)}\n\n"
                except Exception:
                    pass   # viz is non-critical — never break the chat

            # ── Actual Chroma ANN search ──
            try:
                chunks = chat.search_chunks(refined)
                all_chunks.extend(chunks)
            except Exception as e:
                yield f"event: agent\ndata: {json.dumps({'agent': 'rag_query', 'status': 'error', 'output': f'Search error: {str(e)}'})}\n\n"

        # Prepare sources for UI
        sources_for_ui = []
        if all_chunks:
            all_chunks.sort(key=lambda x: x['score'], reverse=True)
            rag_context = "\n\n".join([
                f"[Chunk {chunk['chunk_id']} (score: {chunk['score']:.2f})]\n{chunk['content']}"
                for chunk in all_chunks
            ])
            for chunk in all_chunks:
                parts = chunk['chunk_id'].split(':')
                source = parts[0] if len(parts) > 0 else 'unknown'
                page = parts[1] if len(parts) > 1 else 0
                sources_for_ui.append({
                    'chunk_id': chunk['chunk_id'],
                    'source': source,
                    'page': page,
                    'score': chunk['score'],
                    'content': chunk['content'][:500] + ('...' if len(chunk['content']) > 500 else '')
                })
        else:
            rag_context = "No relevant context found."

        yield f"event: sources\ndata: {json.dumps(sources_for_ui)}\n\n"

        # Build messages for response
        messages = []
        if recent_context:
            for line in recent_context.splitlines():
                if ':' in line:
                    role, content = line.split(':', 1)
                    messages.append({"role": role.strip(), "content": content.strip()})

        # ── AGENT 3: Response Generator ──
        yield f"event: agent\ndata: {json.dumps({'agent': 'response', 'status': 'running', 'output': 'Generating response...'})}\n\n"

        full_response = ""
        try:
            for token in generate_response_stream(user_input, messages=messages, rag_context=rag_context):
                full_response += token
                yield f"event: token\ndata: {json.dumps({'token': token})}\n\n"
        except Exception as e:
            error_msg = f'[Error: {str(e)}]'
            full_response += error_msg
            yield f"event: token\ndata: {json.dumps({'token': error_msg})}\n\n"

        # Mark response agent done
        yield f"event: agent\ndata: {json.dumps({'agent': 'response', 'status': 'done', 'output': 'Response complete.'})}\n\n"

        # Save assistant message to DB
        save_message(session_id, 'assistant', full_response, sources_for_ui)

        # Also update in-memory chat history so context works correctly next turn
        chat.add_message("user", user_input)
        chat.add_message("assistant", full_response)

        yield f"event: end\ndata: done\n\n"

    return Response(stream_with_context(generate()), mimetype="text/event-stream")

@app.route('/api/chat/history', methods=['GET'])
def chat_history():
    session_id = request.args.get('session_id')
    if not session_id:
        return jsonify({'error': 'Missing session_id'}), 400
    messages = load_messages(session_id)
    return jsonify(messages)

@app.route('/api/chat/sessions', methods=['GET'])
def list_sessions():
    sessions = get_all_sessions()
    return jsonify(sessions)

# ---------------------------
# Document management
# ---------------------------
@app.route('/api/documents', methods=['GET'])
def list_documents():
    try:
        structure = db_manager.get_structure()
        files = []
        for source, pages in structure.items():
            total_chunks = sum(len(chunks) for chunks in pages.values())
            files.append({
                'name': source,
                'pages': len(pages),
                'chunks': total_chunks
            })
        return jsonify(files)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/documents/add', methods=['POST'])
def add_document():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        save_path = os.path.join(KNOWLEDGE_BASE_DIR, filename)
        file.save(save_path)
        try:
            db_manager.add_file(save_path)
            return jsonify({'status': 'ok', 'filename': filename})
        except Exception as e:
            return jsonify({'error': f'Database addition failed: {str(e)}'}), 500
    else:
        return jsonify({'error': 'File type not allowed'}), 400

@app.route('/api/documents/delete', methods=['POST'])
def delete_document():
    data = request.get_json()
    source = data.get('source')
    if not source:
        return jsonify({'error': 'Missing source'}), 400
    try:
        db_manager.delete_file(source)
        return jsonify({'status': 'ok'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ──────────────────────────────────────────────────────────
# PDF serving — serves file AND exposes a page-info endpoint
# ──────────────────────────────────────────────────────────
@app.route('/files/<path:filename>')
def serve_pdf(filename):
    """Serve the raw PDF file from the knowledge base directory.

    The source metadata stored in ChromaDB may contain a full or relative path
    with mixed separators (e.g. 'knowledge_base\\file.pdf' on Windows).
    We always resolve to just the basename so the lookup is OS-agnostic.
    """
    # Strip to bare filename regardless of path separators
    bare = os.path.basename(filename.replace('\\', '/'))
    return send_from_directory(os.path.abspath(KNOWLEDGE_BASE_DIR), bare)

@app.route('/api/pdf/page-count')
def pdf_page_count():
    """Return the total number of pages in a PDF (used by the viewer)."""
    filename = request.args.get('file')
    if not filename:
        return jsonify({'error': 'Missing file param'}), 400
    filepath = os.path.join(KNOWLEDGE_BASE_DIR, filename)
    if not os.path.exists(filepath):
        return jsonify({'error': 'File not found'}), 404
    try:
        import pypdf
        with open(filepath, 'rb') as f:
            reader = pypdf.PdfReader(f)
            return jsonify({'pages': len(reader.pages)})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ---------------------------
# Vector visualization endpoint
# ---------------------------
@app.route('/api/visualization')
def get_visualization():
    """Return the Plotly figure as an HTML page."""
    try:
        from modules.embedding_function import get_embedding_function
        from langchain.vectorstores.chroma import Chroma
        import numpy as np
        from sklearn.decomposition import PCA
        from sklearn.metrics.pairwise import cosine_similarity
        import plotly.graph_objects as go
        import os

        db = Chroma(
            persist_directory="./chroma_db/",
            embedding_function=get_embedding_function(),
            collection_name="pdf_chunks"
        )
        results = db.get(include=['embeddings', 'documents', 'metadatas'])
        if not results['embeddings']:
            return "<h3>No vectors found</h3>"

        embeddings = np.array(results['embeddings'])
        sources = [m['source'] for m in results['metadatas']]

        pca = PCA(n_components=3)
        xyz = pca.fit_transform(embeddings)

        sim = cosine_similarity(embeddings)
        np.fill_diagonal(sim, 0)
        k = 4
        edge_x, edge_y, edge_z = [], [], []
        for i in range(len(sim)):
            nbrs = np.argsort(sim[i])[-k:]
            for j in nbrs:
                edge_x += [xyz[i, 0], xyz[j, 0], None]
                edge_y += [xyz[i, 1], xyz[j, 1], None]
                edge_z += [xyz[i, 2], xyz[j, 2], None]

        edge_trace = go.Scatter3d(
            x=edge_x, y=edge_y, z=edge_z,
            mode="lines",
            line=dict(color="rgba(0,255,255,0.25)", width=2),
            hoverinfo="none",
            name="Connections"
        )

        unique_sources = list(set(sources))
        source_to_idx = {s: i for i, s in enumerate(unique_sources)}
        file_colors = [source_to_idx[s] for s in sources]

        node_trace = go.Scatter3d(
            x=xyz[:, 0], y=xyz[:, 1], z=xyz[:, 2],
            mode="markers",
            marker=dict(
                size=7,
                color=file_colors,
                colorscale="Turbo",
                opacity=0.9,
                colorbar=dict(title="File Index", thickness=18, len=0.7)
            ),
            customdata=list(zip(results['ids'], [os.path.basename(m['source']) for m in results['metadatas']], [m.get('page', 0) for m in results['metadatas']])),
            hovertemplate="<b>Chunk</b><br>File: %{customdata[1]}<br>Page: %{customdata[2]}<extra></extra>",
            name="Chunks"
        )

        fig = go.Figure(data=[edge_trace, node_trace])
        fig.update_layout(
            title="Neural Vector Knowledge Graph",
            paper_bgcolor="#05070D",
            plot_bgcolor="#05070D",
            scene=dict(
                bgcolor="#05070D",
                xaxis=dict(showbackground=False, color="#00FFF6"),
                yaxis=dict(showbackground=False, color="#00FFF6"),
                zaxis=dict(showbackground=False, color="#00FFF6")
            )
        )
        return pio.to_html(fig, include_plotlyjs='cdn')
    except Exception as e:
        return f"<h3>Error generating visualization: {str(e)}</h3>"


# ──────────────────────────────────────────────────────────
# Real vector embeddings for the live viz panel
# ──────────────────────────────────────────────────────────
@app.route('/api/vectors/all', methods=['GET'])
def get_all_vectors():
    """
    Return PCA-reduced (2D) positions + metadata for every chunk in the DB.
    Called once on page load to seed the canvas with real nodes.
    """
    try:
        from langchain.vectorstores.chroma import Chroma
        import numpy as np
        from sklearn.decomposition import PCA

        db = Chroma(
            persist_directory="./chroma_db/",
            embedding_function=get_embedding_function(),
            collection_name="pdf_chunks"
        )
        results = db.get(include=['embeddings', 'metadatas', 'documents'])
        if not results['embeddings']:
            return jsonify({'nodes': [], 'edges': []})

        embeddings = np.array(results['embeddings'])
        n = len(embeddings)

        # PCA → 2D for canvas rendering
        pca = PCA(n_components=2)
        coords = pca.fit_transform(embeddings)  # shape (n, 2)

        # Normalize coords to [0, 1]
        for dim in range(2):
            lo, hi = coords[:, dim].min(), coords[:, dim].max()
            rng = hi - lo if hi != lo else 1
            coords[:, dim] = (coords[:, dim] - lo) / rng

        # Build top-k structural edges (cosine similarity among chunks)
        from sklearn.metrics.pairwise import cosine_similarity as cos_sim
        sim_matrix = cos_sim(embeddings)
        np.fill_diagonal(sim_matrix, 0)
        k = 3
        edges = []
        seen = set()
        for i in range(n):
            top_k = np.argsort(sim_matrix[i])[-k:]
            for j in top_k:
                key = (min(i,j), max(i,j))
                if key not in seen and sim_matrix[i, j] > 0.5:
                    seen.add(key)
                    edges.append({'i': int(i), 'j': int(j), 'sim': float(sim_matrix[i, j])})

        nodes = []
        for idx in range(n):
            m = results['metadatas'][idx]
            nodes.append({
                'id': idx,
                'chunk_id': results['ids'][idx],
                'x': float(coords[idx, 0]),
                'y': float(coords[idx, 1]),
                'source': os.path.basename(m.get('source', 'unknown')),
                'page': m.get('page', 0),
                'preview': results['documents'][idx][:80] if results['documents'][idx] else ''
            })

        return jsonify({'nodes': nodes, 'edges': edges})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/vectors/query', methods=['POST'])
def query_vector_similarity():
    """
    Accepts a query string, embeds it, computes real cosine similarity
    against every chunk in the DB, and streams results back as SSE —
    one event per chunk, in the order the similarity is computed,
    so the frontend can animate exactly in sync with real computation.
    """
    data = request.get_json()
    query_text = data.get('query', '')
    if not query_text:
        return jsonify({'error': 'Missing query'}), 400

    def stream():
        try:
            from langchain.vectorstores.chroma import Chroma
            import numpy as np
            from sklearn.metrics.pairwise import cosine_similarity as cos_sim

            emb_fn = get_embedding_function()

            # Embed the query
            query_vec = np.array(emb_fn.embed_query(query_text)).reshape(1, -1)

            # Get all chunk embeddings
            db = Chroma(
                persist_directory="./chroma_db/",
                embedding_function=emb_fn,
                collection_name="pdf_chunks"
            )
            results = db.get(include=['embeddings', 'metadatas'])
            if not results['embeddings']:
                yield f"event: done\ndata: {{}}\n\n"
                return

            embeddings = np.array(results['embeddings'])
            n = len(embeddings)

            # Compute cosine similarity for each chunk and stream immediately
            for idx in range(n):
                chunk_vec = embeddings[idx].reshape(1, -1)
                sim = float(cos_sim(query_vec, chunk_vec)[0][0])
                payload = json.dumps({'idx': idx, 'sim': sim, 'total': n})
                yield f"event: sim\ndata: {payload}\n\n"

            yield f"event: done\ndata: {{}}\n\n"
        except Exception as e:
            yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"

    return Response(stream_with_context(stream()), mimetype='text/event-stream')


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

if __name__ == '__main__':
    os.makedirs(KNOWLEDGE_BASE_DIR, exist_ok=True)
    app.run(debug=True, host='0.0.0.0', port=5000, threaded=True)