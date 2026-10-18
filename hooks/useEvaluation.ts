"use client";
import { useState, useCallback, useRef } from "react";
import { startEvaluation, pollEvaluation, type EvalTaskStatus } from "@/lib/api";

export function useEvaluation() {
  const [status, setStatus] = useState<"idle" | "pending" | "running" | "completed" | "failed">("idle");
  const [result, setResult] = useState<Record<string, unknown> | null>(null);
  const [error, setError] = useState("");
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const runEvaluation = useCallback(async () => {
    setStatus("pending");
    setResult(null);
    setError("");

    try {
      const taskId = await startEvaluation();
      setStatus("running");

      // Poll every 2 seconds
      return new Promise<Record<string, unknown>>((resolve, reject) => {
        intervalRef.current = setInterval(async () => {
          try {
            const task: EvalTaskStatus = await pollEvaluation(taskId);

            if (task.status === "completed") {
              clearInterval(intervalRef.current!);
              intervalRef.current = null;
              setStatus("completed");
              setResult(task.result);
              resolve(task.result || {});
            } else if (task.status === "failed") {
              clearInterval(intervalRef.current!);
              intervalRef.current = null;
              setStatus("failed");
              const errMsg = (task.result as Record<string, string>)?.error || "Evaluation failed";
              setError(errMsg);
              reject(new Error(errMsg));
            }
            // pending/running → keep polling
          } catch (pollErr) {
            clearInterval(intervalRef.current!);
            intervalRef.current = null;
            setStatus("failed");
            setError("Lost connection to backend");
            reject(pollErr);
          }
        }, 2000);
      });
    } catch (e: unknown) {
      setStatus("failed");
      setError("Backend not reachable. Start the API server first.");
      throw e;
    }
  }, []);

  const reset = useCallback(() => {
    if (intervalRef.current) clearInterval(intervalRef.current);
    setStatus("idle");
    setResult(null);
    setError("");
  }, []);

  return { status, result, error, runEvaluation, reset };
}
