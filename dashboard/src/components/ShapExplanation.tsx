import React from 'react';
import { ShapExplanation as ShapType } from '../types';
import { AlertTriangle, Lightbulb, TrendingUp } from 'lucide-react';

interface ShapExplanationProps {
  explanation?: ShapType;
}

export const ShapExplanation: React.FC<ShapExplanationProps> = ({ explanation }) => {
  if (!explanation || !explanation.features || explanation.features.length === 0) {
    return null;
  }

  return (
    <div className="mt-3 p-4 bg-black/[0.02] dark:bg-white/[0.025] rounded-2xl border border-black/[0.08] dark:border-white/[0.08] text-xs space-y-3.5 shadow-sm dark:shadow-lg transition-colors duration-200">
      <div className="flex items-center gap-2 text-rose-600 dark:text-rose-400 font-semibold text-[11px] tracking-wider uppercase">
        <AlertTriangle className="w-3.5 h-3.5 stroke-[2.2]" />
        SHAP Explainability · Key Risk Drivers
      </div>

      <ul className="space-y-2">
        {explanation.features.map((f, i) => (
          <li
            key={i}
            className="flex items-start justify-between gap-3 p-2.5 rounded-xl bg-white dark:bg-white/[0.025] border border-black/[0.06] dark:border-white/[0.05] text-neutral-800 dark:text-neutral-200 shadow-sm"
          >
            <div className="flex items-start gap-2.5 min-w-0">
              <TrendingUp className="w-4 h-4 text-rose-500 dark:text-rose-400 shrink-0 mt-0.5 stroke-[2]" />
              <span className="font-medium text-[#1d1d1f] dark:text-white whitespace-normal break-words leading-relaxed text-[12px]">{f.english}</span>
            </div>
            <span className="shrink-0 font-mono text-[10px] font-semibold text-rose-700 dark:text-rose-300 bg-rose-500/10 border border-rose-500/20 px-2 py-0.5 rounded-full">
              +{f.shap_value.toFixed(3)}
            </span>
          </li>
        ))}
      </ul>

      {explanation.counterfactual && (
        <div className="p-3 rounded-xl bg-amber-500/[0.08] border border-amber-500/25 flex items-start gap-2.5 text-amber-900 dark:text-amber-200/95 text-xs shadow-sm">
          <Lightbulb className="w-4 h-4 text-amber-500 dark:text-amber-400 shrink-0 mt-0.5 stroke-[2]" />
          <div>
            <strong className="text-amber-800 dark:text-amber-300 font-semibold mr-1">Counterfactual Insight:</strong>
            <span className="text-neutral-700 dark:text-neutral-200">{explanation.counterfactual}</span>
          </div>
        </div>
      )}
    </div>
  );
};

