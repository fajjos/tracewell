import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { EmptyState } from "../components/EmptyState";
import { ErrorState } from "../components/ErrorState";
import { LoadingState } from "../components/LoadingState";
import {
  fetchEvaluations,
  getErrorMessage,
  type Evaluation,
} from "../lib/api";
import { formatDateTime, formatNumber } from "../utils/format";

export function Evaluations() {
  const [evaluations, setEvaluations] = useState<Evaluation[]>([]);
  const [total, setTotal] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const loadEvaluations = useCallback(async () => {
    setIsLoading(true);
    setErrorMessage(null);

    try {
      const response = await fetchEvaluations({ pageSize: 50 });
      setEvaluations(response.items);
      setTotal(response.total);
    } catch (error) {
      setErrorMessage(getErrorMessage(error));
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadEvaluations();
  }, [loadEvaluations]);

  return (
    <div className="space-y-6">
      <section>
        <p className="text-sm font-medium uppercase tracking-wide text-teal-700 dark:text-teal-300">
          Evaluations
        </p>
        <h1 className="mt-2 text-3xl font-semibold tracking-normal">
          Regression tests
        </h1>
      </section>

      {isLoading ? <LoadingState label="Loading evaluations" /> : null}
      {errorMessage ? (
        <ErrorState message={errorMessage} onRetry={loadEvaluations} />
      ) : null}

      {!isLoading && !errorMessage && evaluations.length === 0 ? (
        <EmptyState
          title="No regression tests yet"
          message="Open a trace detail page and create a regression test from it."
        />
      ) : null}

      {!isLoading && !errorMessage && evaluations.length > 0 ? (
        <section className="rounded-md border border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900">
          <div className="flex items-center justify-between border-b border-slate-200 px-5 py-4 dark:border-slate-800">
            <h2 className="text-base font-semibold">Saved evaluations</h2>
            <span className="text-sm text-slate-500 dark:text-slate-400">
              {formatNumber(evaluations.length)} of {formatNumber(total)} shown
            </span>
          </div>

          <div className="divide-y divide-slate-200 dark:divide-slate-800">
            {evaluations.map((evaluation) => (
              <Link
                key={evaluation.evaluationId}
                to={`/evaluations/${evaluation.evaluationId}`}
                className="block px-5 py-4 transition hover:bg-slate-50 dark:hover:bg-slate-800"
              >
                <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                  <div className="min-w-0">
                    <div className="truncate text-sm font-medium">
                      {evaluation.name}
                    </div>
                    <div className="mt-1 truncate text-sm text-slate-500 dark:text-slate-400">
                      {evaluation.projectId} - source {evaluation.sourceTraceId}
                    </div>
                  </div>
                  <div className="text-sm text-slate-500 dark:text-slate-400">
                    {formatDateTime(evaluation.createdAt)}
                  </div>
                </div>
              </Link>
            ))}
          </div>
        </section>
      ) : null}
    </div>
  );
}
