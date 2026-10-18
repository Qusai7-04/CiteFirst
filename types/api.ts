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
  facts: Chunk[];
  sources: string[];
  query_used: string;
}

export interface EvaluationResponse {
  precision: number;
  recall: number;
  f1: number;
  accuracy: number;
  llm: { precision: number; recall: number; f1: number; accuracy: number };
  llm_confusion: { tp: number; fp: number; fn: number; tn: number };
  queries?: QueryResult[];
}

export interface QueryResult {
  id: number;
  question: string;
  status: string;
  chunks: string;
  grade: string;
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
