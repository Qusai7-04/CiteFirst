export const GRADE_COLORS = {
  correct: { bg: "bg-green-500/20", text: "text-green-400", border: "border-green-500/30" },
  ambiguous: { bg: "bg-yellow-500/20", text: "text-yellow-400", border: "border-yellow-500/30" },
  incorrect: { bg: "bg-red-500/20", text: "text-red-400", border: "border-red-500/30" },
};

export const STATUS_COLORS = {
  success: { bg: "bg-green-500/20", text: "text-green-400", label: "✅ Success" },
  fallback_success: { bg: "bg-yellow-500/20", text: "text-yellow-400", label: "🔄 Fallback Success" },
  partial_match: { bg: "bg-orange-500/20", text: "text-orange-400", label: "⚠️ Partial Match" },
  failed: { bg: "bg-red-500/20", text: "text-red-400", label: "❌ Failed" },
};

export const DEFAULT_SETTINGS = {
  FETCH_K: 30,
  PROCESS_K: 10,
  CHUNK_WORD_LIMIT: 300,
  CORRECT_THRESHOLD: 0.55,
  AMBIGUOUS_THRESHOLD: 0.25,
  BENDY_THRESHOLD: 0.10,
  MAX_VERIFIED_CHUNKS: 2,
  SOFTMAX_MASS_CUTOFF: 0.90,
  DISTANCE_THRESHOLD: 0.70,
  TOTAL_DOCS: 60,
};
