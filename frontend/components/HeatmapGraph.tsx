import { HeatmapData } from "@/lib/api";

function heatColor(heat: number, max: number): string {
  const t = max > 0 ? heat / max : 0;
  const r = Math.round(220 + t * 35);
  const g = Math.round(220 - t * 120);
  const b = Math.round(220 - t * 120);
  return `rgb(${r},${g},${b})`;
}

export default function HeatmapGraph({ data }: { data: HeatmapData }) {
  const top = data.nodes.slice(0, 15);
  return (
    <ul className="space-y-1 text-sm">
      {top.map((node) => (
        <li key={node.file_path} className="flex items-center gap-2">
          <span
            className="inline-block h-3 w-3 shrink-0 rounded-sm"
            style={{ backgroundColor: heatColor(node.heat, data.max_heat) }}
          />
          <span className="truncate font-mono text-zinc-600 dark:text-zinc-400">{node.file_path}</span>
          <span className="ml-auto text-zinc-500">{node.heat.toFixed(2)}</span>
        </li>
      ))}
    </ul>
  );
}
