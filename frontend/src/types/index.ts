/**
 * Type definitions for the RAG System frontend
 */

export interface Message {
  id?: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp?: string;
  sources?: ChunkSource[];
  tokensUsed?: number;
}

export interface ChunkSource {
  id: string;
  source: string;
  page: number;
  content: string;
  score: number;
}

export interface ChatSession {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
  message_count?: number;
  metadata?: Record<string, any>;
}

export interface KnowledgeStats {
  total_chunks: number;
  total_sources: number;
  sources: string[];
}

export interface KnowledgeStructure {
  [source: string]: {
    pages: number;
    chunks: number;
    page_details: Record<number, number>;
  };
}

export interface APIResponse<T> {
  data?: T;
  status: 'success' | 'error';
  message?: string;
}

export interface ChatMessageRequest {
  message: string;
  session_id?: string;
}

export interface ChatMessageResponse {
  response: string;
  session_id: string;
  sources: ChunkSource[];
}

export interface UploadResponse {
  status: string;
  filename: string;
  chunks_added: number;
}
