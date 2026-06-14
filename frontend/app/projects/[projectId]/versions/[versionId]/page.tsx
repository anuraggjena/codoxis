"use client";

import { FormEvent, useEffect, useState } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import Header from "@/components/Header";
import DependencyGraph from "@/components/DependencyGraph";
import GraphQualityBadge from "@/components/GraphQualityBadge";
import EvolutionPanel from "@/components/EvolutionPanel";
import RootCauseCard from "@/components/RootCauseCard";
import DebtSummary from "@/components/DebtSummary";
import HeatmapGraph from "@/components/HeatmapGraph";
import CopilotChat from "@/components/CopilotChat";
import DependencyPathExplorer from "@/components/DependencyPathExplorer";
import {
  api,
  ApiError,
  Dashboard,
  DebtReport,
  EvolutionDiff,
  GraphData,
  HeatmapData,
  RefactorPlan,
  RootCauseResponse,
} from "@/lib/api";
import { isAuthenticated } from "@/lib/auth";

export default function VersionPage() {
  const { projectId, versionId } = useParams<{ projectId: string; versionId: string }>();
  const router = useRouter();
  const [dashboard, setDashboard] = useState<Dashboard | null>(null);
  const [graph, setGraph] = useState<GraphData | null>(null);
  const [plan, setPlan] = useState<RefactorPlan | null>(null);
  const [evolution, setEvolution] = useState<EvolutionDiff | null>(null);
  const [rootCause, setRootCause] = useState<RootCauseResponse | null>(null);
  const [debt, setDebt] = useState<DebtReport | null>(null);
  const [heatmap, setHeatmap] = useState<HeatmapData | null>(null);
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");
  const [mode, setMode] = useState<"beginner" | "advanced">("beginner");
  const [loadingPlan, setLoadingPlan] = useState(false);
  const [loadingAsk, setLoadingAsk] = useState(false);
  const [loadingEvolution, setLoadingEvolution] = useState(false);
  const [loadingRootCause, setLoadingRootCause] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!isAuthenticated()) {
      router.replace("/login");
      return;
    }
    loadDashboard();
    loadGraph();
    loadIntelligence();
  }, [versionId, router]);

  async function loadIntelligence() {
    try {
      const [debtData, heatData] = await Promise.all([
        api.getTechnicalDebt(versionId),
        api.getHeatmap(versionId),
      ]);
      setDebt(debtData);
      setHeatmap(heatData);
    } catch {
      // supplementary panels
    }
  }

  async function loadGraph() {
    try {
      const data = await api.getGraph(versionId);
      setGraph(data);
    } catch {
      // supplementary
    }
  }

  async function loadDashboard() {
    try {
      const data = await api.getDashboard(versionId);
      setDashboard(data);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to load dashboard");
    }
  }

  async function loadEvolution() {
    setLoadingEvolution(true);
    setError("");
    try {
      setEvolution(await api.getEvolution(versionId));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "No previous version to compare");
    } finally {
      setLoadingEvolution(false);
    }
  }

  async function loadRootCause() {
    setLoadingRootCause(true);
    setError("");
    try {
      setRootCause(await api.getRootCause(versionId, mode));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Root cause analysis unavailable");
    } finally {
      setLoadingRootCause(false);
    }
  }

  async function loadRefactorPlan() {
    setLoadingPlan(true);
    setError("");
    try {
      const data = await api.getRefactorPlan(versionId, mode);
      setPlan(data);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to load refactor plan");
    } finally {
      setLoadingPlan(false);
    }
  }

  async function handleAsk(e: FormEvent) {
    e.preventDefault();
    if (!question.trim()) return;
    setLoadingAsk(true);
    setAnswer("");
    try {
      const data = await api.askArchitecture(versionId, question.trim());
      setAnswer(data.answer);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to get answer");
    } finally {
      setLoadingAsk(false);
    }
  }

  const metrics = dashboard?.metrics;

  return (
    <div className="min-h-screen bg-zinc-50 dark:bg-zinc-950">
      <Header />
      <main className="mx-auto max-w-5xl px-6 py-8">
        <Link href={`/projects/${projectId}`} className="text-sm text-zinc-500 hover:text-zinc-700">
          ← Back to project
        </Link>

        <div className="mt-4 flex flex-wrap items-center gap-3">
          <h1 className="text-2xl font-semibold">
            Version {dashboard?.version_info.version_number ?? "…"}
          </h1>
          <GraphQualityBadge quality={dashboard?.graph_quality} />
        </div>

        {error && <p className="mt-4 text-sm text-red-600">{error}</p>}

        {dashboard && (
          <section className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <MetricCard
              label="Architecture Score"
              value={dashboard.version_info.architecture_score?.toFixed(1) ?? "—"}
            />
            <MetricCard label="Files" value={String(metrics?.total_files ?? 0)} />
            <MetricCard label="Coupling" value={metrics?.coupling_score?.toFixed(2) ?? "—"} />
            <MetricCard label="Circular Deps" value={String(metrics?.circular_dependencies ?? 0)} />
          </section>
        )}

        <section className="mt-8 grid gap-6 lg:grid-cols-2">
          <div className="rounded-xl border border-zinc-200 bg-white p-6 dark:border-zinc-800 dark:bg-zinc-900">
            <div className="flex items-center justify-between">
              <h2 className="font-medium">Evolution</h2>
              <button
                type="button"
                onClick={loadEvolution}
                disabled={loadingEvolution}
                className="text-sm text-zinc-600 hover:underline disabled:opacity-50"
              >
                {loadingEvolution ? "Loading…" : "Load diff"}
              </button>
            </div>
            {evolution ? (
              <div className="mt-4">
                <EvolutionPanel evolution={evolution} />
              </div>
            ) : (
              <p className="mt-2 text-sm text-zinc-500">Compare with the previous uploaded version.</p>
            )}
          </div>

          <div className="rounded-xl border border-zinc-200 bg-white p-6 dark:border-zinc-800 dark:bg-zinc-900">
            <div className="flex items-center justify-between">
              <h2 className="font-medium">Root cause</h2>
              <button
                type="button"
                onClick={loadRootCause}
                disabled={loadingRootCause}
                className="text-sm text-zinc-600 hover:underline disabled:opacity-50"
              >
                {loadingRootCause ? "Analyzing…" : "Analyze"}
              </button>
            </div>
            {rootCause ? (
              <div className="mt-4">
                <RootCauseCard data={rootCause} />
              </div>
            ) : (
              <p className="mt-2 text-sm text-zinc-500">Explain score changes since last version.</p>
            )}
          </div>
        </section>

        <section className="mt-8 grid gap-6 lg:grid-cols-2">
          <div className="rounded-xl border border-zinc-200 bg-white p-6 dark:border-zinc-800 dark:bg-zinc-900">
            <h2 className="font-medium">Technical debt</h2>
            <div className="mt-4">{debt ? <DebtSummary debt={debt} /> : <p className="text-sm text-zinc-500">Loading…</p>}</div>
          </div>
          <div className="rounded-xl border border-zinc-200 bg-white p-6 dark:border-zinc-800 dark:bg-zinc-900">
            <h2 className="font-medium">Risk heatmap</h2>
            <div className="mt-4">
              {heatmap ? <HeatmapGraph data={heatmap} /> : <p className="text-sm text-zinc-500">Loading…</p>}
            </div>
          </div>
        </section>

        {dashboard?.top_critical_files && dashboard.top_critical_files.length > 0 && (
          <section className="mt-8 rounded-xl border border-zinc-200 bg-white p-6 dark:border-zinc-800 dark:bg-zinc-900">
            <h2 className="font-medium">Critical files</h2>
            <ul className="mt-3 space-y-2 text-sm">
              {dashboard.top_critical_files.map((f) => (
                <li key={f.file_path} className="flex justify-between gap-4">
                  <span className="truncate font-mono text-zinc-700 dark:text-zinc-300">{f.file_path}</span>
                  <span className="text-zinc-500">{f.centrality_score.toFixed(2)}</span>
                </li>
              ))}
            </ul>
          </section>
        )}

        {graph && (
          <section className="mt-8 rounded-xl border border-zinc-200 bg-white p-6 dark:border-zinc-800 dark:bg-zinc-900">
            <h2 className="font-medium">Dependency graph</h2>
            <p className="mt-1 text-sm text-zinc-500">File import relationships — drag nodes, scroll to zoom</p>
            <div className="mt-4">
              <DependencyGraph data={graph} />
            </div>
          </section>
        )}

        <section className="mt-8 rounded-xl border border-zinc-200 bg-white p-6 dark:border-zinc-800 dark:bg-zinc-900">
          <h2 className="font-medium">Dependency path explorer</h2>
          <div className="mt-4">
            <DependencyPathExplorer versionId={versionId} />
          </div>
        </section>

        <section className="mt-8 rounded-xl border border-zinc-200 bg-white p-6 dark:border-zinc-800 dark:bg-zinc-900">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <h2 className="font-medium">Refactor plan</h2>
            <div className="flex items-center gap-2">
              <select
                value={mode}
                onChange={(e) => setMode(e.target.value as "beginner" | "advanced")}
                className="rounded-lg border border-zinc-300 px-2 py-1 text-sm dark:border-zinc-700 dark:bg-zinc-950"
              >
                <option value="beginner">Beginner</option>
                <option value="advanced">Advanced</option>
              </select>
              <button
                type="button"
                onClick={loadRefactorPlan}
                disabled={loadingPlan}
                className="rounded-lg bg-zinc-900 px-4 py-2 text-sm text-white hover:bg-zinc-800 disabled:opacity-50 dark:bg-zinc-100 dark:text-zinc-900"
              >
                {loadingPlan ? "Generating…" : "Get refactor plan"}
              </button>
            </div>
          </div>

          {plan && (
            <div className="mt-6 space-y-4">
              <p className="text-sm text-zinc-600 dark:text-zinc-400">{plan.summary}</p>
              {plan.recommendations.map((rec) => (
                <div key={rec.priority} className="rounded-lg border border-zinc-200 p-4 dark:border-zinc-700">
                  <div className="flex items-start justify-between gap-2">
                    <p className="font-medium">{rec.priority}. {rec.title}</p>
                    <span className="shrink-0 rounded-full bg-zinc-100 px-2 py-0.5 text-xs dark:bg-zinc-800">{rec.severity}</span>
                  </div>
                  <p className="mt-2 text-sm text-zinc-600 dark:text-zinc-400">
                    {mode === "beginner" ? rec.beginner_explanation : rec.recommended_action}
                  </p>
                </div>
              ))}
            </div>
          )}
        </section>

        <section className="mt-8 rounded-xl border border-zinc-200 bg-white p-6 dark:border-zinc-800 dark:bg-zinc-900">
          <h2 className="font-medium">Evidence copilot</h2>
          <div className="mt-4">
            <CopilotChat versionId={versionId} />
          </div>
        </section>

        <section className="mt-8 rounded-xl border border-zinc-200 bg-white p-6 dark:border-zinc-800 dark:bg-zinc-900">
          <h2 className="font-medium">Quick ask</h2>
          <form onSubmit={handleAsk} className="mt-4 flex gap-3">
            <input
              type="text"
              placeholder="Which file should I refactor first?"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              className="flex-1 rounded-lg border border-zinc-300 px-3 py-2 text-sm dark:border-zinc-700 dark:bg-zinc-950"
            />
            <button type="submit" disabled={loadingAsk} className="rounded-lg border border-zinc-300 px-4 py-2 text-sm disabled:opacity-50 dark:border-zinc-700">
              {loadingAsk ? "…" : "Ask"}
            </button>
          </form>
          {answer && <p className="mt-4 whitespace-pre-wrap text-sm text-zinc-700 dark:text-zinc-300">{answer}</p>}
        </section>
      </main>
    </div>
  );
}

function MetricCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl border border-zinc-200 bg-white p-5 dark:border-zinc-800 dark:bg-zinc-900">
      <p className="text-sm text-zinc-500">{label}</p>
      <p className="mt-1 text-2xl font-semibold">{value}</p>
    </div>
  );
}
