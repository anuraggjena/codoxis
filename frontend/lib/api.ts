import { getToken, clearToken } from "./auth";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
  ) {
    super(message);
  }
}

async function request<T>(
  path: string,
  options: RequestInit = {},
  auth = true,
): Promise<T> {
  const headers: Record<string, string> = {
    ...(options.headers as Record<string, string>),
  };

  if (auth) {
    const token = getToken();
    if (!token) throw new ApiError("Not authenticated", 401);
    headers.Authorization = `Bearer ${token}`;
  }

  if (options.body && !(options.body instanceof FormData)) {
    headers["Content-Type"] = "application/json";
  }

  const response = await fetch(`${API_URL}${path}`, {
    ...options,
    headers,
  });

  if (response.status === 401 && auth) {
    clearToken();
    if (typeof window !== "undefined") {
      window.location.href = "/login";
    }
  }

  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    throw new ApiError(data.detail ?? data.error ?? "Request failed", response.status);
  }

  return data as T;
}

export const api = {
  register: (email: string, password: string) =>
    request("/auth/register", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }, false),

  login: (email: string, password: string) =>
    request<{ access_token: string; token_type: string }>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }, false),

  listProjects: () =>
    request<Project[]>("/projects/"),

  createProject: (name: string, description?: string) =>
    request<Project>("/projects/", {
      method: "POST",
      body: JSON.stringify({ name, description }),
    }),

  getTimeline: (projectId: string) =>
    request<{ project_id: string; timeline: TimelineEntry[] }>(
      `/analysis/timeline/${projectId}`,
    ),

  uploadZip: (projectId: string, file: File) => {
    const form = new FormData();
    form.append("file", file);
    return request<UploadResult>(`/ingestion/upload/${projectId}`, {
      method: "POST",
      body: form,
    });
  },

  getDashboard: (versionId: string) =>
    request<Dashboard>(`/analysis/dashboard/${versionId}`),

  getRefactorPlan: (versionId: string, mode: "beginner" | "advanced" = "beginner") =>
    request<RefactorPlan>(
      `/ai/refactor-plan/${versionId}?mode=${mode}&limit=10`,
    ),

  askArchitecture: (versionId: string, question: string) =>
    request<{ answer: string }>(
      `/ai/ask/${versionId}?question=${encodeURIComponent(question)}`,
    ),

  getGraph: (versionId: string) =>
    request<GraphData>(`/analysis/graph/${versionId}`),

  getEvolution: (versionId: string) =>
    request<EvolutionDiff>(`/analysis/evolution/${versionId}`),

  getRootCause: (versionId: string, mode: "beginner" | "advanced" = "beginner") =>
    request<RootCauseResponse>(`/ai/root-cause/${versionId}?mode=${mode}`),

  getTechnicalDebt: (versionId: string) =>
    request<DebtReport>(`/analysis/debt/${versionId}`),

  getHeatmap: (versionId: string) =>
    request<HeatmapData>(`/analysis/heatmap/${versionId}`),

  getArchitectureReport: (versionId: string, mode: "beginner" | "advanced" = "advanced") =>
    request<{ analysis: string }>(`/ai/architecture-report/${versionId}?mode=${mode}`),

  copilotAsk: (versionId: string, question: string, mode: "beginner" | "advanced" = "advanced") =>
    request<CopilotResponse>("/ai/copilot/ask", {
      method: "POST",
      body: JSON.stringify({ version_id: versionId, question, mode }),
    }),

  getCopilotSuggestions: (versionId: string) =>
    request<{ suggestions: string[] }>(`/ai/copilot/suggestions/${versionId}`),

  getGraphQuality: (versionId: string) =>
    request<GraphQuality>(`/analysis/graph-quality/${versionId}`),

  compareVersions: (versionId1: string, versionId2: string) =>
    request<Record<string, unknown>>(`/analysis/compare/${versionId1}/${versionId2}`),

  getDependencyPath: (versionId: string, fromFile: string, toFile: string) =>
    request<{ shortest_path: string[] | null; all_paths: string[][]; path_count: number }>(
      `/analysis/dependency-path/${versionId}?from=${encodeURIComponent(fromFile)}&to=${encodeURIComponent(toFile)}`,
    ),

  getClusters: (versionId: string) =>
    request<Record<string, unknown>>(`/analysis/clusters/${versionId}`),

  getBoundaries: (versionId: string) =>
    request<Record<string, unknown>>(`/analysis/boundaries/${versionId}`),

  uploadZipAsync: (projectId: string, file: File) => {
    const form = new FormData();
    form.append("file", file);
    return request<{ job_id: string; version_id: string }>(`/ingestion/upload-async/${projectId}`, {
      method: "POST",
      body: form,
    });
  },

  getIngestionStatus: (jobId: string) =>
    request<{ job_id: string; status: string; result?: Record<string, unknown>; error?: string }>(
      `/ingestion/status/${jobId}`,
    ),
};

export type Project = {
  id: string;
  name: string;
  description: string | null;
  created_at: string;
};

export type TimelineEntry = {
  version: number;
  version_id: string;
  architecture_score: number | null;
  coupling: number | null;
  dependency_depth: number | null;
  circular_dependencies: number | null;
  delta_from_previous?: number | null;
  commit_sha?: string | null;
  source_type?: string | null;
};

export type UploadResult = {
  message: string;
  version_id: string;
  version_number: number;
  architecture_score: number;
};

export type Dashboard = {
  version_info: {
    version_id: string;
    version_number: number;
    architecture_score: number | null;
  };
  metrics: {
    circular_dependencies: number;
    dependency_depth: number;
    coupling_score: number;
    total_files: number;
    total_dependencies: number;
  };
  top_critical_files: Array<{
    file_path: string;
    centrality_score: number;
  }>;
  graph_quality?: GraphQuality | null;
};

export type RefactorPlan = {
  summary: string;
  architecture_score: number | null;
  data_quality: string;
  ai_enhanced: boolean;
  recommendations: Array<{
    priority: number;
    title: string;
    category: string;
    severity: string;
    affected_files: string[];
    recommended_action: string;
    beginner_explanation: string;
    estimated_ahs_impact: string;
  }>;
};

export type GraphData = {
  nodes: Array<{
    id: string;
    label: string;
    full_path: string;
    centrality: number;
  }>;
  edges: Array<{
    source: string;
    target: string;
    type: string;
  }>;
  total_nodes?: number;
  truncated?: boolean;
};

export type GraphQuality = {
  resolution_rate_imports?: number;
  resolution_rate_calls?: number;
  quality_tier: string;
  warnings?: string[];
};

export type EvolutionDiff = {
  base_version_id: string;
  target_version_id: string;
  summary: {
    files_added: number;
    files_removed: number;
    files_modified: number;
    edges_added: number;
    edges_removed: number;
    ahs_change: number;
    coupling_change: number;
    cycle_change: number;
    depth_change: number;
  };
  file_changes: Array<{ path: string; change: string; hash_changed?: boolean }>;
  edge_changes: Array<{
    change: string;
    source: string;
    target: string;
    relation_type: string;
    introduces_cycle?: boolean;
  }>;
  metric_attribution: Array<{ rank: number; factor: string; contribution_estimate: number }>;
  data_quality: string;
};

export type RootCauseResponse = {
  version_id: string;
  headline: string;
  root_causes: Array<{
    title: string;
    severity: string;
    evidence_refs: string[];
    explanation: string;
    recommended_action: string;
  }>;
  confidence: string;
  data_quality_note: string;
};

export type DebtReport = {
  project_technical_debt_score: number;
  files: Array<{ file_path: string; technical_debt_score: number; in_cycle: boolean }>;
  files_in_cycles: number;
};

export type HeatmapData = {
  nodes: Array<{ file_path: string; heat: number }>;
  max_heat: number;
};

export type CopilotResponse = {
  answer: string;
  citations: Array<{ evidence_id: string; type: string }>;
  confidence: string;
};
