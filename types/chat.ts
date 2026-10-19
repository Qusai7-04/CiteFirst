export interface Source {
  filename: string;
  score: number;
  grade?: "correct" | "ambiguous" | "incorrect";
  evidenceStatus?: "evidence" | "partial";
  pageNumber?: number | null;
  evidenceId?: string | null;
  text: string;
}

export interface PipelineInfo {
  status: string;
  chunksKept: number;
  queryUsed: string;
}

export interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
  sources?: Source[];
  pipeline?: PipelineInfo;
}

export type PipelineStepStatus = "pending" | "in-progress" | "complete" | "error";

export interface PipelineStep {
  name: string;
  status: PipelineStepStatus;
  detail: string;
}
