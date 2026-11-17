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
  inputTokens: number | null;
  outputTokens: number | null;
  totalTokens: number | null;
  cost: number | null;
  costSource?: string | null;
  usageSource?: string | null;
  costIsEstimated?: boolean | null;
  llmCalls?: Array<{ model: string; provider: string; inputTokens?: number | null; outputTokens?: number | null; totalTokens?: number | null; latencyMs?: number | null; cost?: number | null; costSource?: string | null; usageSource?: string | null }>;
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
  input_tokens: number | null;
  output_tokens: number | null;
  total_tokens: number | null;
  cost: number | null;
  cost_source?: string | null;
  usage_source?: string | null;
  cost_is_estimated?: boolean | null;
  llm_calls?: Array<{ model: string; provider: string; input_tokens?: number | null; output_tokens?: number | null; total_tokens?: number | null; latency_ms?: number | null; cost?: number | null; cost_source?: string | null; usage_source?: string | null }>;
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

export type EfficiencyInsight = { insightType: string; severity: string; traceId: string; description: string; evidence: Record<string, unknown>; potentialImpact: string; suggestedOptimization: string; confidence: string };
export type EfficiencyTrend = { date: string; tokens: number; cost: number; latency_ms: number; llm_calls: number; executions: number };
export type EfficiencyOverview = { execution_count: number; total_tokens: number; known_token_traces: number; total_estimated_cost: number; known_cost_traces: number; average_tokens_per_execution: number | null; average_execution_latency_ms: number | null; total_llm_calls: number; detected_inefficiencies: number; trends: EfficiencyTrend[]; insights: Array<{ insight_type: string; severity: string; trace_id: string; description: string; evidence: Record<string, unknown>; potential_impact: string; suggested_optimization: string; confidence: string }> };

export async function fetchEfficiencyOverview(): Promise<EfficiencyOverview> {
  const response = await apiClient.get<EfficiencyOverview>("/api/v1/efficiency/overview");
  return response.data;
}

export async function fetchTraceEfficiency(traceId: string): Promise<{ trace_id: string; llm_calls: Array<Record<string, unknown>>; tool_calls: Array<Record<string, unknown>>; insights: EfficiencyOverview["insights"] }> {
  const response = await apiClient.get(`/api/v1/efficiency/traces/${encodeURIComponent(traceId)}`);
  return response.data;
}

export type TraceListParams = {
  page?: number;
  pageSize?: number;
  projectId?: string;
  status?: TraceStatus;
  sortBy?: "created_at" | "latency_ms" | "total_tokens" | "cost";
  sortOrder?: "asc" | "desc";
};

export type AssertionType =
  | "response_non_empty"
  | "response_contains"
  | "status_equals"
  | "required_tool_called"
  | "forbidden_tool_not_called"
  | "max_tool_calls"
  | "max_latency_ms"
  | "max_tokens"
  | "max_input_tokens"
  | "max_output_tokens"
  | "max_llm_calls"
  | "max_estimated_cost";

export type EvaluationAssertion = {
  assertionId: string;
  type: AssertionType;
  name: string;
  expected: unknown;
  severity: "warning" | "error";
};

export type Evaluation = {
  evaluationId: string;
  projectId: string;
  name: string;
  description: string;
  sourceTraceId: string;
  assertions: EvaluationAssertion[];
  status: "active" | "archived";
  createdAt: string;
  updatedAt: string;
};

export type AssertionResult = {
  assertionId: string;
  type: AssertionType;
  name: string;
  passed: boolean;
  expected: unknown;
  actual: unknown;
  message: string;
  severity: "warning" | "error";
};

export type EvaluationRun = {
  runId: string;
  evaluationId: string;
  projectId: string;
  sourceTraceId: string;
  actualTraceId: string;
  status: "passed" | "failed";
  assertionResults: AssertionResult[];
  startedAt: string;
  completedAt: string;
};

export type EvaluationListResponse = {
  items: Evaluation[];
  total: number;
  page: number;
  pageSize: number;
};

type ApiEvaluationAssertion = {
  assertion_id: string;
  type: AssertionType;
  name: string;
  expected?: unknown;
  severity: "warning" | "error";
};

type ApiEvaluation = {
  evaluation_id: string;
  project_id: string;
  name: string;
  description: string;
  source_trace_id: string;
  assertions: ApiEvaluationAssertion[];
  status: "active" | "archived";
  created_at: string;
  updated_at: string;
};

type ApiEvaluationListResponse = {
  items: ApiEvaluation[];
  total: number;
  page: number;
  page_size: number;
};

type ApiAssertionResult = {
  assertion_id: string;
  type: AssertionType;
  name: string;
  passed: boolean;
  expected?: unknown;
  actual?: unknown;
  message: string;
  severity: "warning" | "error";
};

type ApiEvaluationRun = {
  run_id: string;
  evaluation_id: string;
  project_id: string;
  source_trace_id: string;
  actual_trace_id: string;
  status: "passed" | "failed";
  assertion_results: ApiAssertionResult[];
  started_at: string;
  completed_at: string;
};

type ApiEvaluationRunListResponse = {
  items: ApiEvaluationRun[];
  total: number;
  page: number;
  page_size: number;
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
    costSource: trace.cost_source,
    usageSource: trace.usage_source,
    costIsEstimated: trace.cost_is_estimated,
    llmCalls: (trace.llm_calls ?? []).map((call) => ({ model: call.model, provider: call.provider, inputTokens: call.input_tokens, outputTokens: call.output_tokens, totalTokens: call.total_tokens, latencyMs: call.latency_ms, cost: call.cost, costSource: call.cost_source, usageSource: call.usage_source })),
    status: trace.status,
    toolCalls: trace.tool_calls ?? [],
    createdAt: trace.created_at,
  };
}

function mapAssertion(assertion: ApiEvaluationAssertion): EvaluationAssertion {
  return {
    assertionId: assertion.assertion_id,
    type: assertion.type,
    name: assertion.name,
    expected: assertion.expected ?? null,
    severity: assertion.severity,
  };
}

function toApiAssertion(assertion: EvaluationAssertion): ApiEvaluationAssertion {
  return {
    assertion_id: assertion.assertionId,
    type: assertion.type,
    name: assertion.name,
    expected: assertion.expected,
    severity: assertion.severity,
  };
}

function mapEvaluation(evaluation: ApiEvaluation): Evaluation {
  return {
    evaluationId: evaluation.evaluation_id,
    projectId: evaluation.project_id,
    name: evaluation.name,
    description: evaluation.description,
    sourceTraceId: evaluation.source_trace_id,
    assertions: evaluation.assertions.map(mapAssertion),
    status: evaluation.status,
    createdAt: evaluation.created_at,
    updatedAt: evaluation.updated_at,
  };
}

function mapAssertionResult(result: ApiAssertionResult): AssertionResult {
  return {
    assertionId: result.assertion_id,
    type: result.type,
    name: result.name,
    passed: result.passed,
    expected: result.expected ?? null,
    actual: result.actual ?? null,
    message: result.message,
    severity: result.severity,
  };
}

function mapEvaluationRun(run: ApiEvaluationRun): EvaluationRun {
  return {
    runId: run.run_id,
    evaluationId: run.evaluation_id,
    projectId: run.project_id,
    sourceTraceId: run.source_trace_id,
    actualTraceId: run.actual_trace_id,
    status: run.status,
    assertionResults: run.assertion_results.map(mapAssertionResult),
    startedAt: run.started_at,
    completedAt: run.completed_at,
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

export async function createEvaluationFromTrace(
  traceId: string,
): Promise<Evaluation> {
  const response = await apiClient.post<ApiEvaluation>(
    `/api/v1/evaluations/from-trace/${encodeURIComponent(traceId)}`,
  );
  return mapEvaluation(response.data);
}

export async function fetchEvaluations(
  params: { page?: number; pageSize?: number; projectId?: string } = {},
): Promise<EvaluationListResponse> {
  const response = await apiClient.get<ApiEvaluationListResponse>(
    "/api/v1/evaluations",
    {
      params: {
        page: params.page ?? 1,
        page_size: params.pageSize ?? 50,
        project_id: params.projectId,
      },
    },
  );

  return {
    items: response.data.items.map(mapEvaluation),
    total: response.data.total,
    page: response.data.page,
    pageSize: response.data.page_size,
  };
}

export async function fetchEvaluation(
  evaluationId: string,
): Promise<Evaluation> {
  const response = await apiClient.get<ApiEvaluation>(
    `/api/v1/evaluations/${encodeURIComponent(evaluationId)}`,
  );
  return mapEvaluation(response.data);
}

export async function updateEvaluation(
  evaluationId: string,
  payload: Pick<Evaluation, "name" | "description" | "assertions">,
): Promise<Evaluation> {
  const response = await apiClient.patch<ApiEvaluation>(
    `/api/v1/evaluations/${encodeURIComponent(evaluationId)}`,
    {
      name: payload.name,
      description: payload.description,
      assertions: payload.assertions.map(toApiAssertion),
    },
  );
  return mapEvaluation(response.data);
}

export async function runEvaluation(
  evaluationId: string,
  actualTraceId: string,
): Promise<EvaluationRun> {
  const response = await apiClient.post<ApiEvaluationRun>(
    `/api/v1/evaluations/${encodeURIComponent(evaluationId)}/runs`,
    { actual_trace_id: actualTraceId },
  );
  return mapEvaluationRun(response.data);
}

export async function fetchEvaluationRuns(
  evaluationId: string,
): Promise<{ items: EvaluationRun[]; total: number }> {
  const response = await apiClient.get<ApiEvaluationRunListResponse>(
    `/api/v1/evaluations/${encodeURIComponent(evaluationId)}/runs`,
  );
  return {
    items: response.data.items.map(mapEvaluationRun),
    total: response.data.total,
  };
}

export async function fetchEvaluationRun(runId: string): Promise<EvaluationRun> {
  const response = await apiClient.get<ApiEvaluationRun>(
    `/api/v1/evaluation-runs/${encodeURIComponent(runId)}`,
  );
  return mapEvaluationRun(response.data);
}
