"use client";

import dynamic from "next/dynamic";
import type { GraphData } from "@/lib/api";

const ForceGraph2D = dynamic(() => import("react-force-graph-2d"), { ssr: false });

const MAX_NODES = 200;

type Props = {
  data: GraphData;
};

export default function DependencyGraph({ data }: Props) {
  const sorted = [...data.nodes].sort((a, b) => b.centrality - a.centrality);
  const visibleNodes = sorted.slice(0, MAX_NODES);
  const nodeIds = new Set(visibleNodes.map((n) => n.id));

  const graphData = {
    nodes: visibleNodes.map((n) => ({
      id: n.id,
      label: n.label,
      full_path: n.full_path,
      val: Math.max(2, n.centrality * 12 + 2),
    })),
    links: data.edges
      .filter((e) => nodeIds.has(e.source) && nodeIds.has(e.target))
      .map((e) => ({ source: e.source, target: e.target })),
  };

  if (graphData.nodes.length === 0) {
    return <p className="text-sm text-zinc-500">No dependency graph data for this version.</p>;
  }

  const showingCap = data.truncated && data.total_nodes;

  return (
    <div>
      {showingCap && (
        <p className="mb-2 text-xs text-zinc-500">
          Showing top {graphData.nodes.length} of {data.total_nodes} files by centrality
        </p>
      )}
      <div className="h-[420px] overflow-hidden rounded-lg border border-zinc-200 bg-zinc-950 dark:border-zinc-700">
        <ForceGraph2D
          graphData={graphData}
          nodeLabel="full_path"
          nodeAutoColorBy="label"
          linkDirectionalArrowLength={4}
          linkDirectionalArrowRelPos={1}
          cooldownTicks={80}
          backgroundColor="#09090b"
        />
      </div>
    </div>
  );
}
