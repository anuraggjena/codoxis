"use client";

import { FormEvent, useEffect, useState } from "react";
import { api, ApiError, CopilotResponse } from "@/lib/api";

export default function CopilotChat({ versionId }: { versionId: string }) {
  const [question, setQuestion] = useState("");
  const [response, setResponse] = useState<CopilotResponse | null>(null);
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    api.getCopilotSuggestions(versionId).then((d) => setSuggestions(d.suggestions)).catch(() => {});
  }, [versionId]);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!question.trim()) return;
    setLoading(true);
    setError("");
    try {
      const data = await api.copilotAsk(versionId, question.trim());
      setResponse(data);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Copilot request failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      {suggestions.length > 0 && (
        <div className="mb-3 flex flex-wrap gap-2">
          {suggestions.map((s) => (
            <button
              key={s}
              type="button"
              onClick={() => setQuestion(s)}
              className="rounded-full border border-zinc-300 px-3 py-1 text-xs hover:bg-zinc-50 dark:border-zinc-700"
            >
              {s}
            </button>
          ))}
        </div>
      )}
      <form onSubmit={handleSubmit} className="flex gap-3">
        <input
          type="text"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="Ask with graph evidence…"
          className="flex-1 rounded-lg border border-zinc-300 px-3 py-2 text-sm dark:border-zinc-700 dark:bg-zinc-950"
        />
        <button
          type="submit"
          disabled={loading}
          className="rounded-lg bg-zinc-900 px-4 py-2 text-sm text-white disabled:opacity-50 dark:bg-zinc-100 dark:text-zinc-900"
        >
          {loading ? "…" : "Ask"}
        </button>
      </form>
      {error && <p className="mt-2 text-sm text-red-600">{error}</p>}
      {response && (
        <div className="mt-4 space-y-2">
          <p className="whitespace-pre-wrap text-sm">{response.answer}</p>
          <p className="text-xs text-zinc-500">Confidence: {response.confidence}</p>
          {response.citations.length > 0 && (
            <ul className="text-xs text-zinc-500">
              {response.citations.slice(0, 5).map((c, i) => (
                <li key={i}>{c.type}: {c.evidence_id}</li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}
