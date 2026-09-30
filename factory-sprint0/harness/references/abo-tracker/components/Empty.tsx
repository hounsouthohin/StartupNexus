import React from "react";

interface EmptyProps {
  title: string;
  description?: string;
  action?: React.ReactNode;
  className?: string;
}

export function Empty({ title, description, action, className = "" }: EmptyProps) {
  return (
    <div className={["flex flex-col items-center justify-center py-16 text-center", className].join(" ")}>
      <div className="mb-4 rounded-full bg-muted p-4">
        <svg
          className="h-8 w-8 text-muted-foreground"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          strokeWidth={1.5}
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M20.25 7.5l-.625 10.632a2.25 2.25 0 01-2.247 2.118H6.622a2.25 2.25 0
               01-2.247-2.118L3.75 7.5m8.25 3v6.75m0 0l-3-3m3 3 3-3M3.75 7.5h16.5"
          />
        </svg>
      </div>
      <h3 className="text-sm font-semibold text-foreground">{title}</h3>
      {description && <p className="mt-1 text-sm text-muted-foreground">{description}</p>}
      {action && <div className="mt-4">{action}</div>}
    </div>
  );
}
