import axios from "axios";

export type TraceStatus = "success" | "error";

export type TraceToolCall = {
  name: string;
  [key: string]: unknown;
};

export type Trace = {
  traceId: string;
  projectId: string;
  sessionId: string;
  prompt: string;
  response: string;
  provider: string;
  model: string;
  latencyMs: number;
  inputTokens: number;
  outputTokens: number;
  totalTokens: number;
  cost: number;
  status: TraceStatus;
  toolCalls: TraceToolCall[];
  createdAt: string;
};

type ApiTraceToolCall = {
  name: string;
  [key: string]: unknown;
};

type ApiTrace = {
  trace_id: string;
  project_id: string;
  session_id: string;
  prompt: string;
  response: string;
  provider: string;
  model: string;
  latency_ms: number;
  input_tokens: number;
  output_tokens: number;
  total_tokens: number;
  cost: number;
  status: TraceStatus;
  tool_calls?: ApiTraceToolCall[];
  created_at: string;
};

type ApiTraceListResponse = {
  items: ApiTrace[];
  total: number;
  page: number;
  page_size: number;
};

export type TraceListResponse = {
  items: Trace[];
  total: number;
  page: number;
  pageSize: number;
};

export type TraceListParams = {
  page?: number;
  pageSize?: number;
  projectId?: string;
  status?: TraceStatus;
  sortBy?: "created_at" | "latency_ms" | "total_tokens" | "cost";
  sortOrder?: "asc" | "desc";
};

const apiBaseUrl =
  import.meta.env.VITE_TRACEWELL_API_BASE_URL ?? "http://localhost:8000";

const apiClient = axios.create({
  baseURL: apiBaseUrl,
  timeout: 10_000,
  headers: {
    "Content-Type": "application/json",
  },
});

function mapTrace(trace: ApiTrace): Trace {
  return {
    traceId: trace.trace_id,
    projectId: trace.project_id,
    sessionId: trace.session_id,
    prompt: trace.prompt,
    response: trace.response,
    provider: trace.provider,
    model: trace.model,
    latencyMs: trace.latency_ms,
    inputTokens: trace.input_tokens,
    outputTokens: trace.output_tokens,
    totalTokens: trace.total_tokens,
    cost: trace.cost,
    status: trace.status,
    toolCalls: trace.tool_calls ?? [],
    createdAt: trace.created_at,
  };
}

export function getErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    if (error.response?.data && typeof error.response.data === "object") {
      const detail = (error.response.data as { detail?: unknown }).detail;
      if (typeof detail === "string") {
        return detail;
      }
    }

    if (error.response?.status === 404) {
      return "The requested trace was not found.";
    }

    if (error.message) {
      return error.message;
    }
  }

  return "Something went wrong while talking to the Tracewell API.";
}

export async function fetchTraces(
  params: TraceListParams = {},
): Promise<TraceListResponse> {
  const response = await apiClient.get<ApiTraceListResponse>("/api/v1/traces", {
    params: {
      page: params.page ?? 1,
      page_size: params.pageSize ?? 50,
      project_id: params.projectId,
      status: params.status,
      sort_by: params.sortBy ?? "created_at",
      sort_order: params.sortOrder ?? "desc",
    },
  });

  return {
    items: response.data.items.map(mapTrace),
    total: response.data.total,
    page: response.data.page,
    pageSize: response.data.page_size,
  };
}

export async function fetchTrace(traceId: string): Promise<Trace> {
  const response = await apiClient.get<ApiTrace>(
    `/api/v1/traces/${encodeURIComponent(traceId)}`,
  );
  return mapTrace(response.data);
}
