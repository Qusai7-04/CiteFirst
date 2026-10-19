export type PipelineStatus = "success" | "fallback_success" | "partial_match" | "failed";
export type ChunkGrade = "correct" | "ambiguous" | "incorrect";

export interface Chunk {
  text: string;
  score: number;
  grade: ChunkGrade;
  source?: string;
}

export interface QueryResponse {
  status: PipelineStatus;
  answer: string;
  facts: string[];
  sources: string[];
  evidence?: Evidence[];
  query_used: string;
}

export interface Evidence {
  id: string | null;
  document_id: string | null;
  source: string;
  page_index: number | null;
  page_number: number | null;
  text: string;
}

export interface EvaluationResponse {
  baseline_status: string;
  dataset_sha256: string;
  counts: Record<string, number>;
  metrics: Record<string, { mean: number; count: number }>;
}

export interface VaultDocument {
  id: string;
  filename: string;
  chunks: number;
  indexedAt: string;
  fileType: string;
}

export interface Settings {
  FETCH_K: number;
  PROCESS_K: number;
  CHUNK_WORD_LIMIT: number;
  CORRECT_THRESHOLD: number;
  AMBIGUOUS_THRESHOLD: number;
  BENDY_THRESHOLD: number;
  MAX_VERIFIED_CHUNKS: number;
  SOFTMAX_MASS_CUTOFF: number;
  DISTANCE_THRESHOLD: number;
  TOTAL_DOCS: number;
}
