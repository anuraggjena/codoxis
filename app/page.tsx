"use client";

import { useEffect, useState } from "react";
import { apiGet, apiPost } from "@/lib/api";

type Project = {
  id: string;
  name: string;
  createdAt: string;
};

export default function Home() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [name, setName] = useState("");
  const [loading, setLoading] = useState(false);

  async function loadProjects() {
    const data = await apiGet<{ projects: Project[] }>("/api/projects");
    setProjects(data.projects);
  }

  async function createProject() {
    if (!name) return;

    setLoading(true);
    await apiPost<Project>("/api/projects", { name });
    setName("");
    await loadProjects();
    setLoading(false);
  }

  useEffect(() => {
    loadProjects();
  }, []);

  return (
    <main className="min-h-screen p-8 max-w-md mx-auto">
      <h1 className="text-lg font-medium mb-4">Projects</h1>

      <div className="flex gap-2 mb-6">
        <input
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="Project name"
          className="border px-2 py-1 flex-1"
        />
        <button
          onClick={createProject}
          disabled={loading}
          className="border px-3"
        >
          {loading ? "Creating..." : "Add"}
        </button>
      </div>

      {projects.length === 0 ? (
        <p className="text-neutral-500">No projects yet</p>
      ) : (
        <ul className="space-y-2">
          {projects.map((project) => (
            <li key={project.id} className="text-sm">
              {project.name}
            </li>
          ))}
        </ul>
      )}
    </main>
  );
}
