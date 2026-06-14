"use client";

import { useEffect, useState } from "react";
import { api, ApiError, TimelineEntry } from "@/lib/api";

export default function CompareVersions({
  timeline,
}: {
  timeline: TimelineEntry[];
}) {
  const [fromId, setFromId] = useState("");
  const [toId, setToId] = useState("");
  const [result, setResult] = useState<Record<string, unknown> | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (timeline.length >= 2) {
      setFromId(timeline[timeline.length - 2].version_id);
      setToId(timeline[timeline.length - 1].version_id);
    } else if (timeline.length === 1) {
      setToId(timeline[0].version_id);
    }
  }, [timeline]);

  async function compare() {
    if (!fromId || !toId) return;
    setLoading(true);
    setError("");
    try {
      const data = await api.compareVersions(fromId, toId);
      setResult(data);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Compare failed");
    } finally {
      setLoading(false);
    }
  }

  if (timeline.length < 2) {
    return <p className="text-sm text-zinc-500">Upload at least two versions to compare.</p>;
  }

  return (
    <div>
      <div className="flex flex-wrap gap-2">
        <select
          value={fromId}
          onChange={(e) => setFromId(e.target.value)}
          className="rounded-lg border border-zinc-300 px-2 py-1 text-sm dark:border-zinc-700 dark:bg-zinc-950"
        >
          {timeline.map((t) => (
            <option key={t.version_id} value={t.version_id}>v{t.version}</option>
          ))}
        </select>
        <span className="self-center text-sm text-zinc-500">→</span>
        <select
          value={toId}
          onChange={(e) => setToId(e.target.value)}
          className="rounded-lg border border-zinc-300 px-2 py-1 text-sm dark:border-zinc-700 dark:bg-zinc-950"
        >
          {timeline.map((t) => (
            <option key={t.version_id} value={t.version_id}>v{t.version}</option>
          ))}
        </select>
        <button
          type="button"
          onClick={compare}
          disabled={loading}
          className="rounded-lg bg-zinc-900 px-4 py-2 text-sm text-white dark:bg-zinc-100 dark:text-zinc-900"
        >
          {loading ? "…" : "Compare"}
        </button>
      </div>
      {error && <p className="mt-2 text-sm text-red-600">{error}</p>}
      {result && (
        <pre className="mt-4 max-h-64 overflow-auto rounded-lg bg-zinc-100 p-3 text-xs dark:bg-zinc-800">
          {JSON.stringify(result, null, 2)}
        </pre>
      )}
    </div>
  );
}
