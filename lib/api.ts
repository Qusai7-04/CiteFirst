import type { Evidence } from "@/types/api";

export const BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ||
  (typeof window !== "undefined" && window.location.hostname === "127.0.0.1"
    ? "http://127.0.0.1:8000"
    : "http://localhost:8000");

export function getApiUrl(path: string = ""): string {
  const cleanPath = path.startsWith("/") ? path : `/${path}`;
  return `${BASE_URL}${cleanPath}`;
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json", ...options?.headers },
    ...options,
  });
  if (!res.ok) {
    const err = await res.text();
    throw new Error(err || `HTTP ${res.status}`);
  }
  return res.json();
}

// ── Typed API client ────────────────────────────────────────────────────────
export const api = {
  get: <T>(path: string) => request<T>(path),
  post: <T>(path: string, body: unknown) =>
    request<T>(path, { method: "POST", body: JSON.stringify(body) }),
  put: <T>(path: string, body: unknown) =>
    request<T>(path, { method: "PUT", body: JSON.stringify(body) }),
  delete: <T>(path: string) => request<T>(path, { method: "DELETE" }),
  upload: async <T>(path: string, file: File): Promise<T> => {
    const form = new FormData();
    form.append("file", file);
    const res = await fetch(`${BASE_URL}${path}`, { method: "POST", body: form });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return res.json();
  },
};

// ── SSE stream helper ───────────────────────────────────────────────────────
export interface SSEEvent {
  step: string;
  detail?: string;
  progress?: number;
  result?: QueryResponseRaw;
}

export interface QueryResponseRaw {
  status: string;
  answer: string;
  facts: string[];
  sources: string[];
  evidence?: Evidence[];
  query_used: string;
}

export async function streamQuery(
  question: string,
  onEvent: (event: SSEEvent) => void,
  file_filter?: string,
): Promise<QueryResponseRaw> {
  const body: { question: string; file_filter?: string } = { question };
  if (file_filter) body.file_filter = file_filter;

  const res = await fetch(`${BASE_URL}/api/query/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  if (!res.body) throw new Error("No response body");

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let finalResult: QueryResponseRaw | null = null;

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() || "";

    for (const line of lines) {
      if (line.startsWith("data: ")) {
        try {
          const event: SSEEvent = JSON.parse(line.slice(6));
          onEvent(event);
          if (event.step === "done" && event.result) {
            finalResult = event.result;
          }
        } catch {
          // Skip malformed lines
        }
      }
    }
  }

  if (!finalResult) {
    throw new Error("Stream ended without result");
  }

  return finalResult;
}

// ── Health & Readiness check ────────────────────────────────────────────────
export interface HealthResponse {
  status: string;
  ready?: boolean;
  pipeline_available?: boolean;
  crag_available: boolean; // Retained compatibility alias
  detail?: string;
}

export async function checkHealth(): Promise<HealthResponse> {
  try {
    return await api.get<HealthResponse>("/api/health");
  } catch {
    return { status: "unreachable", ready: false, pipeline_available: false, crag_available: false };
  }
}

// ── Evaluation helpers ──────────────────────────────────────────────────────
export async function startEvaluation(): Promise<string> {
  const res = await api.post<{ task_id: string }>("/api/evaluate", {});
  return res.task_id;
}

export interface EvalTaskStatus {
  status: "pending" | "running" | "completed" | "failed";
  result: Record<string, unknown> | null;
}

export async function pollEvaluation(taskId: string): Promise<EvalTaskStatus> {
  return api.get<EvalTaskStatus>(`/api/evaluate/${taskId}`);
}
