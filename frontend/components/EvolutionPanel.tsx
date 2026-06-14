import { EvolutionDiff } from "@/lib/api";

export default function EvolutionPanel({ evolution }: { evolution: EvolutionDiff }) {
  const s = evolution.summary;
  return (
    <div className="space-y-4">
      <div className="grid gap-3 sm:grid-cols-3 text-sm">
        <div>
          <p className="text-zinc-500">AHS change</p>
          <p className={`font-semibold ${s.ahs_change < 0 ? "text-red-600" : "text-green-600"}`}>
            {s.ahs_change >= 0 ? "+" : ""}{s.ahs_change.toFixed(1)}
          </p>
        </div>
        <div>
          <p className="text-zinc-500">Files changed</p>
          <p className="font-semibold">+{s.files_added} / −{s.files_removed} / ~{s.files_modified}</p>
        </div>
        <div>
          <p className="text-zinc-500">Edges changed</p>
          <p className="font-semibold">+{s.edges_added} / −{s.edges_removed}</p>
        </div>
      </div>

      {evolution.edge_changes.length > 0 && (
        <div>
          <p className="text-sm font-medium">Top dependency changes</p>
          <ul className="mt-2 space-y-1 text-xs font-mono text-zinc-600 dark:text-zinc-400">
            {evolution.edge_changes.slice(0, 5).map((e, i) => (
              <li key={i}>
                [{e.change}] {e.source} → {e.target}
                {e.introduces_cycle && " ⚠ cycle"}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
