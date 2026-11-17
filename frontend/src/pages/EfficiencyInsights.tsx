import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { EmptyState } from "../components/EmptyState";
import { ErrorState } from "../components/ErrorState";
import { LoadingState } from "../components/LoadingState";
import { fetchEfficiencyOverview, type EfficiencyOverview } from "../lib/api";
import { formatCurrency, formatLatency, formatNumber } from "../utils/format";

function Metric({ label, value, detail }: { label: string; value: string; detail?: string }) {
  return <article className="rounded-md border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-900"><div className="text-sm text-slate-500 dark:text-slate-400">{label}</div><div className="mt-3 text-xl font-semibold">{value}</div>{detail && <div className="mt-1 text-xs text-slate-500 dark:text-slate-400">{detail}</div>}</article>;
}

export function EfficiencyInsights() {
  const [data, setData] = useState<EfficiencyOverview | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const load = useCallback(async () => { setLoading(true); setError(null); try { setData(await fetchEfficiencyOverview()); } catch (e) { setError(e instanceof Error ? e.message : "Unable to load efficiency data."); } finally { setLoading(false); } }, []);
  useEffect(() => { void load(); }, [load]);
  if (loading) return <LoadingState label="Analyzing recent executions" />;
  if (error) return <ErrorState title="Unable to load efficiency insights" message={error} onRetry={load} />;
  if (!data || data.execution_count === 0) return <div className="space-y-5"><h1 className="text-3xl font-semibold">Efficiency Insights</h1><EmptyState title="No executions in this period" message="Efficiency metrics appear here after traces are recorded." /></div>;
  const trends = data.trends.slice(-14);
  const maxTokens = Math.max(1, ...trends.map((item) => item.tokens));
  return <div className="space-y-6">
    <section><h1 className="text-3xl font-semibold">Efficiency Insights</h1><p className="mt-2 text-sm text-slate-500 dark:text-slate-400">Rule based signals from up to 30 days of recent executions. Findings are opportunities to investigate.</p></section>
    <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
      <Metric label="Total tokens" value={formatNumber(data.total_tokens)} detail={`${data.known_token_traces} executions with usage data`} />
      <Metric label="Estimated cost" value={formatCurrency(data.total_estimated_cost)} detail={`${data.known_cost_traces} executions with known cost`} />
      <Metric label="Average tokens / execution" value={data.average_tokens_per_execution === null ? "Unknown" : formatNumber(Math.round(data.average_tokens_per_execution))} />
      <Metric label="Average execution latency" value={data.average_execution_latency_ms === null ? "Unknown" : formatLatency(Math.round(data.average_execution_latency_ms))} />
      <Metric label="LLM calls" value={formatNumber(data.total_llm_calls)} />
      <Metric label="Detected inefficiencies" value={formatNumber(data.detected_inefficiencies)} />
    </section>
    <section className="rounded-md border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-900"><h2 className="text-base font-semibold">Efficiency trends</h2><p className="mt-1 text-xs text-slate-500">Daily aggregate. Token bars are scaled to the largest day shown.</p><div className="mt-5 space-y-3">{trends.map((trend) => <div key={trend.date} className="grid grid-cols-[6rem_1fr_5rem] items-center gap-3 text-xs"><span className="text-slate-500">{trend.date}</span><div className="h-3 overflow-hidden rounded bg-slate-100 dark:bg-slate-800"><div className="h-full rounded bg-teal-600" style={{ width: `${Math.max(2, trend.tokens / maxTokens * 100)}%` }} /></div><span className="text-right font-medium">{formatNumber(trend.tokens)}</span><div className="col-span-3 grid grid-cols-3 text-slate-500"><span>Cost {formatCurrency(trend.cost)}</span><span>Latency {formatLatency(trend.executions ? Math.round(trend.latency_ms / trend.executions) : 0)}</span><span className="text-right">{trend.executions ? (trend.llm_calls / trend.executions).toFixed(1) : "0"} calls / run</span></div></div>)}</div></section>
    <section className="space-y-3"><h2 className="text-base font-semibold">Insights</h2>{data.insights.length === 0 ? <EmptyState title="No signals detected" message="The rules did not find issues in the available traces." /> : data.insights.map((item, index) => <article key={`${item.trace_id}-${item.insight_type}-${index}`} className="rounded-md border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-900"><div className="flex flex-wrap items-start justify-between gap-3"><div><div className="font-semibold">{item.description}</div><div className="mt-1 text-sm text-slate-500">{item.potential_impact}</div></div><span className="rounded-full bg-amber-100 px-2.5 py-1 text-xs font-semibold capitalize text-amber-900">{item.severity}</span></div><div className="mt-4 text-sm"><span className="font-medium">Recommended action: </span>{item.suggested_optimization}</div><div className="mt-2 text-xs text-slate-500">{item.confidence}</div><Link className="mt-4 inline-block text-sm font-medium text-teal-700 dark:text-teal-300" to={`/traces/${encodeURIComponent(item.trace_id)}`}>View execution {item.trace_id}</Link></article>)}</section>
  </div>;
}
