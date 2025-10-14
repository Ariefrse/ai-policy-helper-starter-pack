// Shared TypeScript types for the AI Policy Helper frontend

export interface Citation {
  title: string;
  section?: string;
}

export interface Chunk {
  title: string;
  section?: string;
  text: string;
}

export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  citations?: Citation[];
  chunks?: Chunk[];
}

export interface AskResponse {
  query: string;
  answer: string;
  citations: Citation[];
  chunks: Chunk[];
  metrics?: {
    retrieval_ms: number;
    generation_ms: number;
  };
}

export interface IngestResponse {
  indexed_docs: number;
  indexed_chunks: number;
}

export interface MetricsData {
  total_docs: number;
  total_chunks: number;
  embedding_model: string;
  llm_model: string;
  avg_retrieval_latency_ms: number;
  avg_generation_latency_ms: number;
  p95_retrieval_latency_ms: number;
  p95_generation_latency_ms: number;
  total_asks: number;
  total_ingests: number;
}
