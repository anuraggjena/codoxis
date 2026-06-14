import { GraphQuality } from "@/lib/api";

export default function GraphQualityBadge({ quality }: { quality: GraphQuality | null | undefined }) {
  if (!quality?.quality_tier) return null;

  const tier = quality.quality_tier;
  const colors = {
    high: "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300",
    medium: "bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-300",
    low: "bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300",
  };

  return (
    <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${colors[tier as keyof typeof colors] ?? colors.medium}`}>
      Graph quality: {tier}
      {quality.resolution_rate_imports != null && (
        <span className="ml-1 opacity-75">
          ({Math.round(quality.resolution_rate_imports * 100)}% imports)
        </span>
      )}
    </span>
  );
}
