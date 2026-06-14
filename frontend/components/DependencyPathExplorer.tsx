"use client";

import { useState } from "react";
import { api, ApiError } from "@/lib/api";

export default function DependencyPathExplorer({ versionId }: { versionId: string }) {
  const [fromFile, setFromFile] = useState("");
  const [toFile, setToFile] = useState("");
  const [paths, setPaths] = useState<string[][] | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function search() {
    if (!fromFile.trim() || !toFile.trim()) return;
    setLoading(true);
    setError("");
    try {
      const data = await api.getDependencyPath(versionId, fromFile.trim(), toFile.trim());
      setPaths(data.all_paths ?? (data.shortest_path ? [data.shortest_path] : []));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Path not found");
      setPaths(null);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <div className="flex flex-wrap gap-2">
        <input
          value={fromFile}
          onChange={(e) => setFromFile(e.target.value)}
          placeholder="From file (e.g. main.py)"
          className="flex-1 rounded-lg border border-zinc-300 px-3 py-2 text-sm dark:border-zinc-700 dark:bg-zinc-950"
        />
        <input
          value={toFile}
          onChange={(e) => setToFile(e.target.value)}
          placeholder="To file (e.g. utils.py)"
          className="flex-1 rounded-lg border border-zinc-300 px-3 py-2 text-sm dark:border-zinc-700 dark:bg-zinc-950"
        />
        <button
          type="button"
          onClick={search}
          disabled={loading}
          className="rounded-lg border border-zinc-300 px-4 py-2 text-sm dark:border-zinc-700"
        >
          {loading ? "…" : "Find path"}
        </button>
      </div>
      {error && <p className="mt-2 text-sm text-red-600">{error}</p>}
      {paths && paths.length > 0 && (
        <ul className="mt-3 space-y-2 text-xs font-mono">
          {paths.map((path, i) => (
            <li key={i} className="rounded border border-zinc-200 p-2 dark:border-zinc-700">
              {path.join(" → ")}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
