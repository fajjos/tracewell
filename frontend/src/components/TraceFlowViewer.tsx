import {
  Background,
  Controls,
  Handle,
  MarkerType,
  MiniMap,
  Position,
  ReactFlow,
  type Edge,
  type Node,
  type NodeProps,
} from "@xyflow/react";

import type { Trace } from "../lib/api";
import { formatLatency, formatNumber } from "../utils/format";

type TraceNodeData = {
  title: string;
  subtitle: string;
  metric: string;
  detail: string;
  tone: "user" | "llm" | "tool" | "response";
};

type TraceFlowNode = Node<TraceNodeData, "traceNode">;

type TraceFlowViewerProps = {
  trace: Trace;
};

const nodeToneClasses: Record<TraceNodeData["tone"], string> = {
  user: "border-sky-200 bg-sky-50 text-sky-950 dark:border-sky-900 dark:bg-sky-950 dark:text-sky-100",
  llm: "border-teal-200 bg-teal-50 text-teal-950 dark:border-teal-900 dark:bg-teal-950 dark:text-teal-100",
  tool: "border-amber-200 bg-amber-50 text-amber-950 dark:border-amber-900 dark:bg-amber-950 dark:text-amber-100",
  response:
    "border-slate-200 bg-white text-slate-950 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100",
};

function TraceNode({ data }: NodeProps<TraceFlowNode>) {
  return (
    <div
      className={`w-64 rounded-md border px-4 py-3 shadow-sm ${nodeToneClasses[data.tone]}`}
    >
      <Handle
        type="target"
        position={Position.Top}
        className="!h-2 !w-2 !border-slate-400 !bg-white dark:!border-slate-500 dark:!bg-slate-950"
      />
      <div className="text-xs font-medium uppercase tracking-wide opacity-70">
        {data.subtitle}
      </div>
      <div className="mt-1 text-base font-semibold tracking-normal">{data.title}</div>
      <div className="mt-3 grid grid-cols-2 gap-2 text-xs">
        <div className="rounded bg-white/60 px-2 py-1.5 dark:bg-black/20">
          <div className="opacity-60">Latency</div>
          <div className="mt-0.5 font-semibold">{data.metric}</div>
        </div>
        <div className="rounded bg-white/60 px-2 py-1.5 dark:bg-black/20">
          <div className="opacity-60">Tokens</div>
          <div className="mt-0.5 font-semibold">{data.detail}</div>
        </div>
      </div>
      <Handle
        type="source"
        position={Position.Bottom}
        className="!h-2 !w-2 !border-slate-400 !bg-white dark:!border-slate-500 dark:!bg-slate-950"
      />
    </div>
  );
}

const nodeTypes = {
  traceNode: TraceNode,
};

function summarizeTool(trace: Trace): string {
  if (trace.toolCalls.length === 0) {
    return "No tool call captured";
  }

  if (trace.toolCalls.length === 1) {
    return trace.toolCalls[0].name;
  }

  return `${trace.toolCalls[0].name} + ${trace.toolCalls.length - 1} more`;
}

function buildNodes(trace: Trace): TraceFlowNode[] {
  const centerX = 220;
  const verticalGap = 150;
  const latency = formatLatency(trace.latencyMs);

  return [
    {
      id: "user",
      type: "traceNode",
      position: { x: centerX, y: 0 },
      data: {
        title: "User",
        subtitle: "Prompt submitted",
        metric: "0ms",
        detail: trace.inputTokens === null ? "Unknown" : formatNumber(trace.inputTokens),
        tone: "user",
      },
    },
    {
      id: "llm-request",
      type: "traceNode",
      position: { x: centerX, y: verticalGap },
      data: {
        title: trace.model,
        subtitle: `${trace.provider} LLM`,
        metric: latency,
        detail: trace.totalTokens === null ? "Unknown" : formatNumber(trace.totalTokens),
        tone: "llm",
      },
    },
    {
      id: "tool",
      type: "traceNode",
      position: { x: centerX, y: verticalGap * 2 },
      data: {
        title: "Tool",
        subtitle: summarizeTool(trace),
        metric: trace.toolCalls.length > 0 ? latency : "n/a",
        detail: `${formatNumber(trace.toolCalls.length)} calls`,
        tone: "tool",
      },
    },
    {
      id: "llm-response",
      type: "traceNode",
      position: { x: centerX, y: verticalGap * 3 },
      data: {
        title: trace.model,
        subtitle: "LLM response pass",
        metric: latency,
        detail: trace.outputTokens === null ? "Unknown" : formatNumber(trace.outputTokens),
        tone: "llm",
      },
    },
    {
      id: "response",
      type: "traceNode",
      position: { x: centerX, y: verticalGap * 4 },
      data: {
        title: "Response",
        subtitle: trace.status,
        metric: latency,
        detail: trace.totalTokens === null ? "Unknown" : formatNumber(trace.totalTokens),
        tone: "response",
      },
    },
  ];
}

const edges: Edge[] = [
  { id: "user-llm", source: "user", target: "llm-request" },
  { id: "llm-tool", source: "llm-request", target: "tool" },
  { id: "tool-llm", source: "tool", target: "llm-response" },
  { id: "llm-response", source: "llm-response", target: "response" },
].map((edge) => ({
  ...edge,
  type: "smoothstep",
  animated: true,
  markerEnd: {
    type: MarkerType.ArrowClosed,
  },
  style: {
    strokeWidth: 2,
    stroke: "#0f766e",
  },
}));

export function TraceFlowViewer({ trace }: TraceFlowViewerProps) {
  return (
    <section className="rounded-md border border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900">
      <div className="border-b border-slate-200 px-5 py-4 dark:border-slate-800">
        <h2 className="text-base font-semibold">Trace viewer</h2>
        <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
          User to LLM to tool execution flow for this trace.
        </p>
      </div>
      <div className="h-[760px] min-h-[620px] w-full">
        <ReactFlow
          nodes={buildNodes(trace)}
          edges={edges}
          nodeTypes={nodeTypes}
          fitView
          fitViewOptions={{ padding: 0.18 }}
          minZoom={0.45}
          maxZoom={1.4}
          nodesDraggable
          nodesConnectable={false}
          elementsSelectable
        >
          <Background gap={18} size={1} />
          <Controls position="bottom-right" />
          <MiniMap
            pannable
            zoomable
            className="!bg-white dark:!bg-slate-950"
            nodeColor="#0f766e"
          />
        </ReactFlow>
      </div>
    </section>
  );
}
