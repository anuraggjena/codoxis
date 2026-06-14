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
