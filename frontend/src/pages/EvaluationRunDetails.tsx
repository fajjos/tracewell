import { useCallback, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { ErrorState } from "../components/ErrorState";
import { LoadingState } from "../components/LoadingState";
import {
  fetchEvaluationRun,
  getErrorMessage,
  type EvaluationRun,
} from "../lib/api";
import { formatDateTime } from "../utils/format";

function formatValue(value: unknown): string {
  if (value === null || value === undefined) {
    return "n/a";
  }

  if (typeof value === "string") {
    return value;
  }

  return JSON.stringify(value);
}

export function EvaluationRunDetails() {
  const { runId } = useParams<{ runId: string }>();
  const [run, setRun] = useState<EvaluationRun | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const loadRun = useCallback(async () => {
    if (!runId) {
      setErrorMessage("Missing run id.");
      setIsLoading(false);
      return;
    }

    setIsLoading(true);
    setErrorMessage(null);

    try {
      setRun(await fetchEvaluationRun(runId));
    } catch (error) {
      setErrorMessage(getErrorMessage(error));
    } finally {
      setIsLoading(false);
    }
  }, [runId]);

  useEffect(() => {
    void loadRun();
  }, [loadRun]);

  if (isLoading) {
    return <LoadingState label="Loading evaluation run" />;
  }

  if (errorMessage || !run) {
    return (
      <ErrorState
        title="Unable to load run"
        message={errorMessage ?? "The requested run was not found."}
        onRetry={loadRun}
      />
    );
  }

  const passed = run.status === "passed";

  return (
    <div className="space-y-6">
      <section>
        <Link
          to={`/evaluations/${run.evaluationId}`}
          className="text-sm font-medium text-teal-700 hover:text-teal-800 dark:text-teal-300 dark:hover:text-teal-200"
        >
          Back to evaluation
        </Link>
        <h1 className="mt-3 text-3xl font-semibold tracking-normal">
          {passed ? "PASS" : "FAIL"}
        </h1>
        <p className="mt-2 text-sm text-slate-500 dark:text-slate-400">
          Source {run.sourceTraceId} - actual {run.actualTraceId} -{" "}
          {formatDateTime(run.completedAt)}
        </p>
      </section>

      <section className="rounded-md border border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900">
        <div className="border-b border-slate-200 px-5 py-4 dark:border-slate-800">
          <h2 className="text-base font-semibold">Assertion results</h2>
        </div>
        <div className="divide-y divide-slate-200 dark:divide-slate-800">
          {run.assertionResults.map((result) => (
            <article key={result.assertionId} className="px-5 py-4">
              <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
                <div>
                  <div className="text-sm font-medium">{result.name}</div>
                  <div className="mt-1 text-xs text-slate-500 dark:text-slate-400">
                    {result.type} - {result.message}
                  </div>
                </div>
                <span
                  className={`w-fit rounded px-2.5 py-1 text-xs font-semibold uppercase ${
                    result.passed
                      ? "bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-200"
                      : "bg-rose-100 text-rose-800 dark:bg-rose-950 dark:text-rose-200"
                  }`}
                >
                  {result.passed ? "passed" : "failed"}
                </span>
              </div>
              <div className="mt-4 grid gap-3 lg:grid-cols-2">
                <div className="rounded-md bg-slate-50 p-3 text-xs dark:bg-slate-950">
                  <div className="font-medium uppercase text-slate-500 dark:text-slate-400">
                    Expected
                  </div>
                  <div className="mt-2 break-words">{formatValue(result.expected)}</div>
                </div>
                <div className="rounded-md bg-slate-50 p-3 text-xs dark:bg-slate-950">
                  <div className="font-medium uppercase text-slate-500 dark:text-slate-400">
                    Actual
                  </div>
                  <div className="mt-2 break-words">{formatValue(result.actual)}</div>
                </div>
              </div>
            </article>
          ))}
        </div>
      </section>
    </div>
  );
}
