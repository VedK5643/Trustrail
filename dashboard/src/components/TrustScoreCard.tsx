import React from 'react';
import { Shield, ShieldAlert, ShieldCheck } from 'lucide-react';

interface TrustScoreCardProps {
  score: number;
  alpha: number;
  beta: number;
  name: string;
}

export const TrustScoreCard: React.FC<TrustScoreCardProps> = ({ score, alpha, beta, name }) => {
  const percent = Math.round(score * 100);

  let badgeClasses = 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20';
  let barGradient = 'from-emerald-500 to-emerald-400 shadow-[0_0_12px_rgba(16,185,129,0.35)]';
  let Icon = ShieldCheck;

  if (score < 0.4) {
    badgeClasses = 'text-rose-400 bg-rose-500/10 border-rose-500/20';
    barGradient = 'from-rose-500 to-rose-400 shadow-[0_0_12px_rgba(244,63,94,0.35)]';
    Icon = ShieldAlert;
  } else if (score < 0.7) {
    badgeClasses = 'text-amber-400 bg-amber-500/10 border-amber-500/20';
    barGradient = 'from-amber-500 to-amber-400 shadow-[0_0_12px_rgba(245,158,11,0.35)]';
    Icon = Shield;
  }

  return (
    <div className="p-4 rounded-2xl border border-black/[0.08] dark:border-white/[0.08] bg-white dark:bg-[#141418] hover:bg-neutral-50 dark:hover:bg-[#19191f] transition-all duration-200 shadow-[0_2px_10px_rgba(0,0,0,0.03)] dark:shadow-lg">
      <div className="flex items-center justify-between">
        <span className="text-[11px] font-semibold uppercase tracking-wider text-neutral-500 dark:text-neutral-400">{name}</span>
        <div className={`p-1 rounded-full border ${badgeClasses}`}>
          <Icon className="w-3.5 h-3.5 stroke-[2.2]" />
        </div>
      </div>

      <div className="mt-3 flex items-baseline justify-between">
        <div className="flex items-baseline gap-1.5">
          <span className="text-3xl font-semibold tracking-tight text-[#1d1d1f] dark:text-white tabular-nums">{percent}%</span>
        </div>
        <span className="text-[11px] font-medium text-neutral-500 dark:text-neutral-400 tracking-wide uppercase">Trust Score</span>
      </div>

      {/* Apple-style Progress Track */}
      <div className="w-full bg-black/[0.06] dark:bg-white/[0.08] rounded-full h-1.5 mt-2.5 overflow-hidden">
        <div
          className={`h-full rounded-full bg-gradient-to-r ${barGradient} transition-all duration-500 ease-out`}
          style={{ width: `${percent}%` }}
        ></div>
      </div>

      <div className="mt-3 flex items-center justify-between text-[11px] text-neutral-500 dark:text-neutral-400 pt-2 border-t border-black/[0.05] dark:border-white/[0.05]">
        <span className="flex items-center gap-1 font-mono">
          α: <strong className="text-neutral-900 dark:text-white font-semibold">{alpha.toFixed(1)}</strong>
        </span>
        <span className="flex items-center gap-1 font-mono">
          β: <strong className="text-neutral-900 dark:text-white font-semibold">{beta.toFixed(1)}</strong>
        </span>
      </div>
    </div>
  );
};

