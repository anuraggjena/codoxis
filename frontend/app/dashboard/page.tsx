"use client";

import { FormEvent, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import Header from "@/components/Header";
import { api, ApiError, Project } from "@/lib/api";
import { isAuthenticated } from "@/lib/auth";

export default function DashboardPage() {
  const router = useRouter();
  const [projects, setProjects] = useState<Project[]>([]);
  const [name, setName] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!isAuthenticated()) {
      router.replace("/login");
      return;
    }
    loadProjects();
  }, [router]);

  async function loadProjects() {
    try {
      const data = await api.listProjects();
      setProjects(data);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to load projects");
    } finally {
      setLoading(false);
    }
  }

  async function handleCreate(e: FormEvent) {
    e.preventDefault();
    if (!name.trim()) return;
    setError("");

    try {
      const project = await api.createProject(name.trim());
      setProjects((prev) => [project, ...prev]);
      setName("");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to create project");
    }
  }

  return (
    <div className="min-h-screen bg-zinc-50 dark:bg-zinc-950">
      <Header />
      <main className="mx-auto max-w-5xl px-6 py-8">
        <h1 className="text-2xl font-semibold">Your projects</h1>
        <p className="mt-1 text-sm text-zinc-500">Upload a repository and analyze its architecture</p>

        <form onSubmit={handleCreate} className="mt-8 flex gap-3">
          <input
            type="text"
            placeholder="New project name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="flex-1 rounded-lg border border-zinc-300 px-3 py-2 dark:border-zinc-700 dark:bg-zinc-900"
          />
          <button
            type="submit"
            className="rounded-lg bg-zinc-900 px-4 py-2 text-white hover:bg-zinc-800 dark:bg-zinc-100 dark:text-zinc-900"
          >
            Create
          </button>
        </form>

        {error && <p className="mt-4 text-sm text-red-600">{error}</p>}

        {loading ? (
          <p className="mt-8 text-sm text-zinc-500">Loading projects…</p>
        ) : projects.length === 0 ? (
          <p className="mt-8 text-sm text-zinc-500">No projects yet. Create one to get started.</p>
        ) : (
          <ul className="mt-8 divide-y divide-zinc-200 rounded-xl border border-zinc-200 bg-white dark:divide-zinc-800 dark:border-zinc-800 dark:bg-zinc-900">
            {projects.map((project) => (
              <li key={project.id}>
                <Link
                  href={`/projects/${project.id}`}
                  className="flex items-center justify-between px-5 py-4 hover:bg-zinc-50 dark:hover:bg-zinc-800/50"
                >
                  <div>
                    <p className="font-medium">{project.name}</p>
                    {project.description && (
                      <p className="text-sm text-zinc-500">{project.description}</p>
                    )}
                  </div>
                  <span className="text-sm text-zinc-400">Open →</span>
                </Link>
              </li>
            ))}
          </ul>
        )}
      </main>
    </div>
  );
}
