import { useCallback, useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { ErrorState } from "../components/ErrorState";
import { LoadingState } from "../components/LoadingState";
import {
  fetchEvaluation,
  fetchEvaluationRuns,
  fetchTraces,
  getErrorMessage,
  runEvaluation,
  type Evaluation,
  type EvaluationRun,
  type Trace,
} from "../lib/api";
import { formatDateTime } from "../utils/format";

export function EvaluationDetails() {
  const { evaluationId } = useParams<{ evaluationId: string }>();
  const [evaluation, setEvaluation] = useState<Evaluation | null>(null);
  const [runs, setRuns] = useState<EvaluationRun[]>([]);
  const [traces, setTraces] = useState<Trace[]>([]);
  const [actualTraceId, setActualTraceId] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [isRunning, setIsRunning] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const loadEvaluation = useCallback(async () => {
    if (!evaluationId) {
      setErrorMessage("Missing evaluation id.");
      setIsLoading(false);
      return;
    }

    setIsLoading(true);
    setErrorMessage(null);

    try {
      const [evaluationResponse, runsResponse, tracesResponse] = await Promise.all([
        fetchEvaluation(evaluationId),
        fetchEvaluationRuns(evaluationId),
        fetchTraces({ pageSize: 100 }),
      ]);
      setEvaluation(evaluationResponse);
      setRuns(runsResponse.items);
      setTraces(tracesResponse.items);
      setActualTraceId(
        tracesResponse.items.find(
          (trace) => trace.traceId !== evaluationResponse.sourceTraceId,
        )?.traceId ?? "",
      );
    } catch (error) {
      setErrorMessage(getErrorMessage(error));
    } finally {
      setIsLoading(false);
    }
  }, [evaluationId]);

  useEffect(() => {
    void loadEvaluation();
  }, [loadEvaluation]);

  const selectableTraces = useMemo(
    () =>
      traces.filter((trace) => trace.traceId !== evaluation?.sourceTraceId),
    [evaluation?.sourceTraceId, traces],
  );

  async function handleRun() {
    if (!evaluation || !actualTraceId) {
      return;
    }

    setIsRunning(true);
    setErrorMessage(null);
    try {
      const run = await runEvaluation(evaluation.evaluationId, actualTraceId);
      window.location.href = `/evaluation-runs/${run.runId}`;
    } catch (error) {
      setErrorMessage(getErrorMessage(error));
    } finally {
      setIsRunning(false);
    }
  }

  if (isLoading) {
    return <LoadingState label="Loading evaluation" />;
  }

  if (errorMessage || !evaluation) {
    return (
      <ErrorState
        title="Unable to load evaluation"
        message={errorMessage ?? "The requested evaluation was not found."}
        onRetry={loadEvaluation}
      />
    );
  }

  return (
    <div className="space-y-6">
      <section className="flex flex-col justify-between gap-4 xl:flex-row xl:items-end">
        <div className="min-w-0">
          <Link
            to="/evaluations"
            className="text-sm font-medium text-teal-700 hover:text-teal-800 dark:text-teal-300 dark:hover:text-teal-200"
          >
            Back to evaluations
          </Link>
          <h1 className="mt-3 truncate text-3xl font-semibold tracking-normal">
            {evaluation.name}
          </h1>
          <p className="mt-2 text-sm text-slate-500 dark:text-slate-400">
            Source trace {evaluation.sourceTraceId}
          </p>
        </div>
        <Link
          to={`/evaluations/${evaluation.evaluationId}/edit`}
          className="inline-flex w-fit rounded-md border border-slate-200 px-4 py-2 text-sm font-medium transition hover:bg-slate-100 dark:border-slate-800 dark:hover:bg-slate-900"
        >
          Edit
        </Link>
      </section>

      <section className="rounded-md border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-900">
        <h2 className="text-base font-semibold">Run test</h2>
        <div className="mt-4 grid gap-3 lg:grid-cols-[1fr_auto]">
          <select
            value={actualTraceId}
            onChange={(event) => setActualTraceId(event.target.value)}
            className="rounded-md border border-slate-200 bg-white px-3 py-2 text-sm outline-none focus:border-teal-600 dark:border-slate-800 dark:bg-slate-950"
          >
            <option value="">Select an actual trace</option>
            {selectableTraces.map((trace) => (
              <option key={trace.traceId} value={trace.traceId}>
                {trace.projectId} - {trace.traceId}
              </option>
            ))}
          </select>
          <button
            type="button"
            onClick={handleRun}
            disabled={!actualTraceId || isRunning}
            className="rounded-md bg-slate-950 px-4 py-2 text-sm font-medium text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-60 dark:bg-white dark:text-slate-950 dark:hover:bg-slate-200"
          >
            {isRunning ? "Running..." : "Run Test"}
          </button>
        </div>
      </section>

      <section className="grid gap-6 xl:grid-cols-[1fr_1fr]">
        <article className="rounded-md border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-900">
          <h2 className="text-base font-semibold">Assertions</h2>
          <div className="mt-5 space-y-3">
            {evaluation.assertions.map((assertion) => (
              <div
                key={assertion.assertionId}
                className="rounded-md border border-slate-200 p-4 dark:border-slate-800"
              >
                <div className="text-sm font-medium">{assertion.name}</div>
                <div className="mt-1 text-xs text-slate-500 dark:text-slate-400">
                  {assertion.type} - expected {String(assertion.expected)}
                </div>
              </div>
            ))}
          </div>
        </article>

        <article className="rounded-md border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-900">
          <h2 className="text-base font-semibold">Recent runs</h2>
          {runs.length === 0 ? (
            <p className="mt-5 text-sm text-slate-500 dark:text-slate-400">
              No runs yet.
            </p>
          ) : (
            <div className="mt-5 space-y-3">
              {runs.map((run) => (
                <Link
                  key={run.runId}
                  to={`/evaluation-runs/${run.runId}`}
                  className="block rounded-md border border-slate-200 p-4 transition hover:bg-slate-50 dark:border-slate-800 dark:hover:bg-slate-800"
                >
                  <div className="flex items-center justify-between gap-3">
                    <span className="text-sm font-medium uppercase">
                      {run.status}
                    </span>
                    <span className="text-xs text-slate-500 dark:text-slate-400">
                      {formatDateTime(run.completedAt)}
                    </span>
                  </div>
                  <div className="mt-1 truncate text-xs text-slate-500 dark:text-slate-400">
                    actual {run.actualTraceId}
                  </div>
                </Link>
              ))}
            </div>
          )}
        </article>
      </section>
    </div>
  );
}
