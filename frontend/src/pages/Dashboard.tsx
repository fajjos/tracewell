import { useCallback, useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";

import { EmptyState } from "../components/EmptyState";
import { ErrorState } from "../components/ErrorState";
import { LoadingState } from "../components/LoadingState";
import { StatusBadge } from "../components/StatusBadge";
import { fetchTraces, getErrorMessage, type Trace } from "../lib/api";
import {
  formatCurrency,
  formatDateTime,
  formatLatency,
  formatNumber,
} from "../utils/format";

export function Dashboard() {
  const [traces, setTraces] = useState<Trace[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const loadDashboard = useCallback(async () => {
    setIsLoading(true);
    setErrorMessage(null);

    try {
      const response = await fetchTraces({ pageSize: 100 });
      setTraces(response.items);
    } catch (error) {
      setErrorMessage(getErrorMessage(error));
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadDashboard();
  }, [loadDashboard]);

  const metrics = useMemo(() => {
    const totalTraces = traces.length;
    const failedTraces = traces.filter((trace) => trace.status === "error").length;
    const totalCost = traces.reduce((sum, trace) => sum + (trace.cost ?? 0), 0);
    const averageLatency =
      totalTraces === 0
        ? 0
        : Math.round(
            traces.reduce((sum, trace) => sum + trace.latencyMs, 0) / totalTraces,
          );

    return [
      {
        label: "Total traces",
        value: formatNumber(totalTraces),
        detail: "from backend",
      },
      {
        label: "Failures",
        value: formatNumber(failedTraces),
        detail: "needs review",
      },
      {
        label: "Avg latency",
        value: totalTraces === 0 ? "0ms" : formatLatency(averageLatency),
        detail: "current page",
      },
      {
        label: "Spend",
        value: formatCurrency(totalCost),
        detail: "estimated",
      },
    ];
  }, [traces]);

  const recentTraces = traces.slice(0, 4);
  const failedTraces = traces.filter((trace) => trace.status === "error").slice(0, 4);

  return (
    <div className="space-y-6">
      <section className="flex flex-col justify-between gap-4 sm:flex-row sm:items-end">
        <div>
          <p className="text-sm font-medium uppercase tracking-wide text-teal-700 dark:text-teal-300">
            MVP Dashboard
          </p>
          <h1 className="mt-2 text-3xl font-semibold tracking-normal text-slate-950 dark:text-white">
            Agent activity overview
          </h1>
        </div>
        <Link
          to="/traces"
          className="inline-flex w-fit items-center rounded-md bg-slate-950 px-4 py-2 text-sm font-medium text-white transition hover:bg-slate-800 dark:bg-white dark:text-slate-950 dark:hover:bg-slate-200"
        >
          View traces
        </Link>
      </section>

      {isLoading ? <LoadingState label="Loading dashboard" /> : null}
      {errorMessage ? (
        <ErrorState message={errorMessage} onRetry={loadDashboard} />
      ) : null}

      {!isLoading && !errorMessage && traces.length === 0 ? (
        <EmptyState
          title="No traces yet"
          message="Send your first trace from the Python SDK and it will appear here."
        />
      ) : null}

      {!isLoading && !errorMessage && traces.length > 0 ? (
        <>
          <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            {metrics.map((metric) => (
              <article
                key={metric.label}
                className="rounded-md border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-900"
              >
                <div className="text-sm text-slate-500 dark:text-slate-400">
                  {metric.label}
                </div>
                <div className="mt-3 text-2xl font-semibold tracking-normal">
                  {metric.value}
                </div>
                <div className="mt-1 text-sm text-slate-500 dark:text-slate-400">
                  {metric.detail}
                </div>
              </article>
            ))}
          </section>

          <section className="grid gap-6 xl:grid-cols-[1.5fr_1fr]">
            <div className="rounded-md border border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900">
              <div className="border-b border-slate-200 px-5 py-4 dark:border-slate-800">
                <h2 className="text-base font-semibold">Recent traces</h2>
              </div>
              <div className="divide-y divide-slate-200 dark:divide-slate-800">
                {recentTraces.map((trace) => (
                  <Link
                    key={trace.traceId}
                    to={`/traces/${trace.traceId}`}
                    className="block px-5 py-4 transition hover:bg-slate-50 dark:hover:bg-slate-800"
                  >
                    <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                      <div className="min-w-0">
                        <div className="truncate text-sm font-medium">
                          {trace.projectId}
                        </div>
                        <div className="mt-1 truncate text-sm text-slate-500 dark:text-slate-400">
                          {trace.prompt}
                        </div>
                      </div>
                      <div className="flex shrink-0 items-center gap-3">
                        <StatusBadge status={trace.status} />
                        <span className="text-sm text-slate-500 dark:text-slate-400">
                          {formatLatency(trace.latencyMs)}
                        </span>
                      </div>
                    </div>
                  </Link>
                ))}
              </div>
            </div>

            <div className="rounded-md border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-900">
              <h2 className="text-base font-semibold">Failure signals</h2>
              {failedTraces.length === 0 ? (
                <p className="mt-5 text-sm leading-6 text-slate-500 dark:text-slate-400">
                  No failed traces in the current dataset.
                </p>
              ) : (
                <div className="mt-5 space-y-4">
                  {failedTraces.map((trace) => (
                    <Link
                      key={trace.traceId}
                      to={`/traces/${trace.traceId}`}
                      className="block rounded-md border border-rose-200 bg-rose-50 p-4 transition hover:bg-rose-100 dark:border-rose-900 dark:bg-rose-950 dark:hover:bg-rose-900"
                    >
                      <div className="text-sm font-medium text-rose-800 dark:text-rose-200">
                        {trace.projectId}
                      </div>
                      <div className="mt-1 text-sm text-rose-700 dark:text-rose-300">
                        {formatDateTime(trace.createdAt)} -{" "}
                        {formatLatency(trace.latencyMs)}
                      </div>
                    </Link>
                  ))}
                </div>
              )}
            </div>
          </section>
        </>
      ) : null}
    </div>
  );
}
