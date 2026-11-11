import React from 'react';

interface RiskBadgeProps {
  score?: number | null;
  threshold?: number | null;
}

export const RiskBadge: React.FC<RiskBadgeProps> = ({ score, threshold = 0.65 }) => {
  if (score === undefined || score === null) {
    return (
      <span className="inline-flex items-center px-2.5 py-1 rounded-full text-[11px] font-medium bg-black/[0.04] dark:bg-white/[0.04] text-neutral-600 dark:text-neutral-400 border border-black/[0.06] dark:border-white/[0.08]">
        N/A (Policy)
      </span>
    );
  }

  const effectiveThresh = threshold ?? 0.65;
  const percent = (score * 100).toFixed(1);

  if (score < 0.3) {
    return (
      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-semibold tracking-wide bg-emerald-50 dark:bg-emerald-500/10 text-emerald-700 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-500/25 shadow-sm dark:shadow-[0_0_12px_rgba(16,185,129,0.15)]">
        <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 dark:bg-emerald-400 shadow-[0_0_6px_rgba(52,211,153,0.8)]"></span>
        Low Risk ({percent}%)
      </span>
    );
  }

  if (score < effectiveThresh) {
    return (
      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-semibold tracking-wide bg-amber-50 dark:bg-amber-500/10 text-amber-800 dark:text-amber-300 border border-amber-200 dark:border-amber-500/25 shadow-sm dark:shadow-[0_0_12px_rgba(245,158,11,0.15)]">
        <span className="w-1.5 h-1.5 rounded-full bg-amber-500 dark:bg-amber-400 shadow-[0_0_6px_rgba(251,191,36,0.8)]"></span>
        Moderate ({percent}%)
      </span>
    );
  }

  return (
    <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-semibold tracking-wide bg-rose-50 dark:bg-rose-500/15 text-rose-700 dark:text-rose-300 border border-rose-200 dark:border-rose-500/35 shadow-sm dark:shadow-[0_0_16px_rgba(244,63,94,0.25)]">
      <span className="w-1.5 h-1.5 rounded-full bg-rose-500 dark:bg-rose-400 shadow-[0_0_8px_rgba(251,113,133,0.9)] animate-ping"></span>
      High Risk ({percent}%)
    </span>
  );
};

