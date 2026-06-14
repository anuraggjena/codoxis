import { DebtReport } from "@/lib/api";

export default function DebtSummary({ debt }: { debt: DebtReport }) {
  return (
    <div>
      <p className="text-sm text-zinc-500">Project technical debt score</p>
      <p className="text-2xl font-semibold">{debt.project_technical_debt_score.toFixed(2)}</p>
      <ul className="mt-4 space-y-2 text-sm">
        {debt.files.slice(0, 5).map((f) => (
          <li key={f.file_path} className="flex justify-between gap-2">
            <span className="truncate font-mono text-zinc-600 dark:text-zinc-400">{f.file_path}</span>
            <span className="text-zinc-500">{f.technical_debt_score.toFixed(2)}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
