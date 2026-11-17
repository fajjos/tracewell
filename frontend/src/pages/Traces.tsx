import { useCallback, useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";

import { EmptyState } from "../components/EmptyState";
import { ErrorState } from "../components/ErrorState";
import { LoadingState } from "../components/LoadingState";
import { StatusBadge } from "../components/StatusBadge";
import {
  fetchTraces,
  getErrorMessage,
  type Trace,
  type TraceStatus,
} from "../lib/api";
import {
  formatCurrency,
  formatDateTime,
  formatLatency,
  formatNumber,
} from "../utils/format";

type StatusFilter = "all" | TraceStatus;

export function Traces() {
  const [projectFilter, setProjectFilter] = useState("all");
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("all");
  const [traces, setTraces] = useState<Trace[]>([]);
  const [projectOptions, setProjectOptions] = useState<string[]>([]);
  const [total, setTotal] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const loadProjects = useCallback(async () => {
    const response = await fetchTraces({ pageSize: 100 });
    setProjectOptions(
      Array.from(new Set(response.items.map((trace) => trace.projectId))).sort(),
    );
  }, []);

  const loadTraces = useCallback(async () => {
    setIsLoading(true);
    setErrorMessage(null);

    try {
      const response = await fetchTraces({
        pageSize: 50,
        projectId: projectFilter === "all" ? undefined : projectFilter,
        status: statusFilter === "all" ? undefined : statusFilter,
      });
      setTraces(response.items);
      setTotal(response.total);
    } catch (error) {
      setErrorMessage(getErrorMessage(error));
    } finally {
      setIsLoading(false);
    }
  }, [projectFilter, statusFilter]);

  useEffect(() => {
    void loadProjects().catch(() => {
      setProjectOptions([]);
    });
  }, [loadProjects]);

  useEffect(() => {
    void loadTraces();
  }, [loadTraces]);

  const hasActiveFilters = useMemo(
    () => projectFilter !== "all" || statusFilter !== "all",
    [projectFilter, statusFilter],
  );

  return (
    <div className="space-y-6">
      <section className="flex flex-col justify-between gap-4 xl:flex-row xl:items-end">
        <div>
          <p className="text-sm font-medium uppercase tracking-wide text-teal-700 dark:text-teal-300">
            Traces
          </p>
          <h1 className="mt-2 text-3xl font-semibold tracking-normal">
            Agent trace history
          </h1>
        </div>

        <div className="grid gap-3 sm:grid-cols-2">
          <label className="text-sm font-medium text-slate-700 dark:text-slate-300">
            Project
            <select
              value={projectFilter}
              onChange={(event) => setProjectFilter(event.target.value)}
              className="mt-1 block w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm text-slate-950 outline-none transition focus:border-teal-600 dark:border-slate-800 dark:bg-slate-900 dark:text-white"
            >
              <option value="all">All projects</option>
              {projectOptions.map((project) => (
                <option key={project} value={project}>
                  {project}
                </option>
              ))}
            </select>
          </label>

          <label className="text-sm font-medium text-slate-700 dark:text-slate-300">
            Status
            <select
              value={statusFilter}
              onChange={(event) => setStatusFilter(event.target.value as StatusFilter)}
              className="mt-1 block w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm text-slate-950 outline-none transition focus:border-teal-600 dark:border-slate-800 dark:bg-slate-900 dark:text-white"
            >
              <option value="all">All statuses</option>
              <option value="success">Success</option>
              <option value="error">Error</option>
            </select>
          </label>
        </div>
      </section>

      {isLoading ? <LoadingState label="Loading traces" /> : null}
      {errorMessage ? <ErrorState message={errorMessage} onRetry={loadTraces} /> : null}

      {!isLoading && !errorMessage && traces.length === 0 ? (
        <EmptyState
          title={hasActiveFilters ? "No matching traces" : "No traces yet"}
          message={
            hasActiveFilters
              ? "Try changing the project or status filter."
              : "Send traces from the Python SDK to populate this table."
          }
        />
      ) : null}

      {!isLoading && !errorMessage && traces.length > 0 ? (
        <section className="rounded-md border border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900">
          <div className="flex items-center justify-between border-b border-slate-200 px-5 py-4 dark:border-slate-800">
            <h2 className="text-base font-semibold">Trace events</h2>
            <span className="text-sm text-slate-500 dark:text-slate-400">
              {formatNumber(traces.length)} of {formatNumber(total)} shown
            </span>
          </div>

          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-200 text-left text-sm dark:divide-slate-800">
              <thead className="bg-slate-50 text-xs uppercase tracking-wide text-slate-500 dark:bg-slate-950 dark:text-slate-400">
                <tr>
                  <th className="px-5 py-3 font-medium">Trace</th>
                  <th className="px-5 py-3 font-medium">Status</th>
                  <th className="px-5 py-3 font-medium">Model</th>
                  <th className="px-5 py-3 font-medium">Latency</th>
                  <th className="px-5 py-3 font-medium">Tokens</th>
                  <th className="px-5 py-3 font-medium">Cost</th>
                  <th className="px-5 py-3 font-medium">Created</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200 dark:divide-slate-800">
                {traces.map((trace) => (
                  <tr
                    key={trace.traceId}
                    className="transition hover:bg-slate-50 dark:hover:bg-slate-800"
                  >
                    <td className="max-w-xs px-5 py-4">
                      <Link
                        to={`/traces/${trace.traceId}`}
                        className="font-medium text-slate-950 hover:text-teal-700 dark:text-white dark:hover:text-teal-300"
                      >
                        {trace.projectId}
                      </Link>
                      <div className="mt-1 truncate text-xs text-slate-500 dark:text-slate-400">
                        {trace.traceId}
                      </div>
                    </td>
                    <td className="px-5 py-4">
                      <StatusBadge status={trace.status} />
                    </td>
                    <td className="px-5 py-4 text-slate-600 dark:text-slate-300">
                      {trace.provider} / {trace.model}
                    </td>
                    <td className="px-5 py-4 text-slate-600 dark:text-slate-300">
                      {formatLatency(trace.latencyMs)}
                    </td>
                    <td className="px-5 py-4 text-slate-600 dark:text-slate-300">
                      {trace.totalTokens === null ? "Unknown" : formatNumber(trace.totalTokens)}
                    </td>
                    <td className="px-5 py-4 text-slate-600 dark:text-slate-300">
                      {trace.cost === null ? "Unknown" : formatCurrency(trace.cost)}
                    </td>
                    <td className="px-5 py-4 text-slate-600 dark:text-slate-300">
                      {formatDateTime(trace.createdAt)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      ) : null}
    </div>
  );
}
