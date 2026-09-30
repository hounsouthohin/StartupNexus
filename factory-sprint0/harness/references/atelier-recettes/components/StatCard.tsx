import React from "react";

type TrendDirection = "up" | "down" | "flat";

interface StatCardProps {
  label: string;
  value: string | number;
  trend?: string;
  trendDirection?: TrendDirection;
  className?: string;
}

const TREND_CLASSES: Record<TrendDirection, string> = {
  up:   "text-green-600",
  down: "text-destructive",
  flat: "text-muted-foreground",
};

export function StatCard({ label, value, trend, trendDirection = "flat", className = "" }: StatCardProps) {
  return (
    <div className={["bg-card rounded-lg border border-border shadow-sm px-6 py-5", className].join(" ")}>
      <p className="text-sm font-medium text-muted-foreground truncate">{label}</p>
      <p className="mt-1 text-3xl font-bold tracking-tight text-foreground">{value}</p>
      {trend && (
        <p className={["mt-2 flex items-center gap-1 text-sm font-medium", TREND_CLASSES[trendDirection]].join(" ")}>
          {trendDirection === "up" ? "↑" : trendDirection === "down" ? "↓" : "→"}
          {trend}
        </p>
      )}
    </div>
  );
}
