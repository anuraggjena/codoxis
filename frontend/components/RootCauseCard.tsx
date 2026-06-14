import { RootCauseResponse } from "@/lib/api";

export default function RootCauseCard({ data }: { data: RootCauseResponse }) {
  return (
    <div className="space-y-4">
      <p className="text-sm font-medium">{data.headline}</p>
      <p className="text-xs text-zinc-500">Confidence: {data.confidence} · {data.data_quality_note}</p>
      {data.root_causes.map((cause, i) => (
        <div key={i} className="rounded-lg border border-zinc-200 p-3 dark:border-zinc-700">
          <div className="flex justify-between gap-2">
            <p className="font-medium text-sm">{cause.title}</p>
            <span className="text-xs text-zinc-500">{cause.severity}</span>
          </div>
          <p className="mt-2 text-sm text-zinc-600 dark:text-zinc-400">{cause.explanation}</p>
          <p className="mt-2 text-sm text-zinc-700 dark:text-zinc-300">{cause.recommended_action}</p>
        </div>
      ))}
    </div>
  );
}
