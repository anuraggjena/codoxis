"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import Header from "@/components/Header";
import { api, ApiError, TimelineEntry } from "@/lib/api";
import { isAuthenticated } from "@/lib/auth";

export default function ProjectPage() {
  const { projectId } = useParams<{ projectId: string }>();
  const router = useRouter();
  const [timeline, setTimeline] = useState<TimelineEntry[]>([]);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  useEffect(() => {
    if (!isAuthenticated()) {
      router.replace("/login");
      return;
    }
    loadTimeline();
  }, [projectId, router]);

  async function loadTimeline() {
    try {
      const data = await api.getTimeline(projectId);
      setTimeline(data.timeline);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to load versions");
    }
  }

  async function handleUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploading(true);
    setError("");
    setMessage("");

    try {
      const result = await api.uploadZip(projectId, file);
      setMessage(`Version ${result.version_number} analyzed. Score: ${result.architecture_score?.toFixed(1) ?? "—"}`);
      await loadTimeline();
      router.push(`/projects/${projectId}/versions/${result.version_id}`);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Upload failed");
    } finally {
      setUploading(false);
      e.target.value = "";
    }
  }

  return (
    <div className="min-h-screen bg-zinc-50 dark:bg-zinc-950">
      <Header />
      <main className="mx-auto max-w-5xl px-6 py-8">
        <Link href="/dashboard" className="text-sm text-zinc-500 hover:text-zinc-700">
          ← Back to projects
        </Link>

        <h1 className="mt-4 text-2xl font-semibold">Project</h1>
        <p className="mt-1 text-sm text-zinc-500">Upload a ZIP of your repository to analyze</p>

        <div className="mt-8 rounded-xl border border-dashed border-zinc-300 bg-white p-8 text-center dark:border-zinc-700 dark:bg-zinc-900">
          <p className="text-sm text-zinc-600 dark:text-zinc-400">
            {uploading ? "Analyzing repository…" : "Drop a .zip file or click to upload"}
          </p>
          <label className="mt-4 inline-block cursor-pointer rounded-lg bg-zinc-900 px-4 py-2 text-sm text-white hover:bg-zinc-800 dark:bg-zinc-100 dark:text-zinc-900">
            {uploading ? "Uploading…" : "Choose ZIP file"}
            <input
              type="file"
              accept=".zip"
              className="hidden"
              disabled={uploading}
              onChange={handleUpload}
            />
          </label>
        </div>

        {message && <p className="mt-4 text-sm text-green-600">{message}</p>}
        {error && <p className="mt-4 text-sm text-red-600">{error}</p>}

        <h2 className="mt-10 text-lg font-medium">Versions</h2>
        {timeline.length === 0 ? (
          <p className="mt-2 text-sm text-zinc-500">No versions yet.</p>
        ) : (
          <ul className="mt-4 divide-y divide-zinc-200 rounded-xl border border-zinc-200 bg-white dark:divide-zinc-800 dark:border-zinc-800 dark:bg-zinc-900">
            {timeline.map((entry) => (
              <li key={entry.version_id}>
                <Link
                  href={`/projects/${projectId}/versions/${entry.version_id}`}
                  className="flex items-center justify-between px-5 py-4 hover:bg-zinc-50 dark:hover:bg-zinc-800/50"
                >
                  <div>
                    <p className="font-medium">Version {entry.version}</p>
                    <p className="text-sm text-zinc-500">
                      Score {entry.architecture_score?.toFixed(1) ?? "—"} ·{" "}
                      {entry.circular_dependencies ?? 0} cycles
                    </p>
                  </div>
                  <span className="text-sm text-zinc-400">View →</span>
                </Link>
              </li>
            ))}
          </ul>
        )}
      </main>
    </div>
  );
}
