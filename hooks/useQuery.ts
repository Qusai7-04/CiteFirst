"use client";
import { useState, useCallback, useRef } from "react";
import { api, streamQuery, type SSEEvent, type QueryResponseRaw } from "@/lib/api";
import type { QueryResponse } from "@/types/api";

export interface PipelineProgress {
  step: string;
  detail: string;
  progress?: number;
}

export function useQuery() {
  const [pipelineSteps, setPipelineSteps] = useState<PipelineProgress[]>([]);
  const [currentStep, setCurrentStep] = useState<string>("");
  const [progress, setProgress] = useState<number | null>(null);
  const abortRef = useRef(false);

  /** Non-streaming fallback */
  const sendQuery = async (question: string): Promise<QueryResponse> => {
    return api.post<QueryResponse>("/api/query", { question });
  };

  /** SSE streaming — pushes live pipeline updates */
  const sendQueryStream = useCallback(
    async (
      question: string,
      file_filter?: string,
      onStep?: (step: PipelineProgress) => void,
    ): Promise<QueryResponseRaw> => {
      setPipelineSteps([]);
      setCurrentStep("");
      setProgress(null);
      abortRef.current = false;

      const result = await streamQuery(question, (event: SSEEvent) => {
        if (abortRef.current) return;

        if (event.step !== "done") {
          const step: PipelineProgress = {
            step: event.step,
            detail: event.detail || "",
            progress: event.progress,
          };
          setPipelineSteps((prev) => [...prev, step]);
          setCurrentStep(event.step);
          setProgress(event.progress ?? null);
          onStep?.(step);
        } else {
          setProgress(100);
          setCurrentStep("done");
        }
      }, file_filter);

      return result;
    },
    [],
  );

  const reset = useCallback(() => {
    setPipelineSteps([]);
    setCurrentStep("");
    setProgress(null);
  }, []);

  return { sendQuery, sendQueryStream, pipelineSteps, currentStep, progress, reset };
}
