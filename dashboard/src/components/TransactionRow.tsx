import React, { useState } from 'react';
import { Transaction } from '../types';
import { RiskBadge } from './RiskBadge';
import { ShapExplanation } from './ShapExplanation';
import { ApproveButton } from './ApproveButton';
import { DenyButton } from './DenyButton';
import { ChevronRight, ShieldAlert, CheckCircle2, XCircle, Clock } from 'lucide-react';

interface TransactionRowProps {
  txn: Transaction;
  onRefresh: () => void;
}

export const TransactionRow: React.FC<TransactionRowProps> = ({ txn, onRefresh }) => {
  const [expanded, setExpanded] = useState(txn.status === 'HELD');

  const isHeld = txn.status === 'HELD';
  const rowBg = isHeld
    ? 'bg-amber-500/[0.08] hover:bg-amber-500/[0.12] border-amber-500/30 dark:bg-amber-500/[0.06] dark:hover:bg-amber-500/[0.10] dark:border-amber-500/20'
    : 'hover:bg-black/[0.025] dark:hover:bg-white/[0.03] border-black/[0.06] dark:border-white/[0.06]';

  const formatStatus = (status: string) => {
    switch (status) {
      case 'AUTO_CAPTURED':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-medium tracking-wide bg-emerald-500/10 text-emerald-700 dark:text-emerald-400 border border-emerald-500/20 backdrop-blur-sm">
            <CheckCircle2 className="w-3.5 h-3.5 stroke-[2]" /> Auto-Captured
          </span>
        );
      case 'CAPTURED':
      case 'APPROVED':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-medium tracking-wide bg-emerald-500/10 text-emerald-700 dark:text-emerald-400 border border-emerald-500/20 backdrop-blur-sm">
            <CheckCircle2 className="w-3.5 h-3.5 stroke-[2]" /> Captured
          </span>
        );
      case 'HELD':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-semibold tracking-wide bg-amber-500/15 text-amber-800 dark:text-amber-300 border border-amber-400/40 dark:border-amber-400/30 shadow-[0_0_14px_rgba(245,158,11,0.15)] animate-pulse">
            <Clock className="w-3.5 h-3.5 stroke-[2.2]" /> Held for Review
          </span>
        );
      case 'VOIDED':
      case 'DENIED':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-medium tracking-wide bg-rose-500/10 text-rose-700 dark:text-rose-400 border border-rose-500/20 backdrop-blur-sm">
            <XCircle className="w-3.5 h-3.5 stroke-[2]" /> Voided
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[11px] font-medium bg-black/[0.04] dark:bg-white/[0.05] text-neutral-600 dark:text-neutral-400 border border-black/[0.06] dark:border-white/[0.08]">
            {status}
          </span>
        );
    }
  };

  const formattedDate = new Date(txn.created_at).toLocaleTimeString([], {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  });

  return (
    <>
      <tr
        onClick={() => setExpanded(!expanded)}
        className={`border-b transition-all duration-150 cursor-pointer select-none active:scale-[0.999] ${rowBg}`}
      >
        <td className="px-4 py-3.5 text-xs text-neutral-500 dark:text-neutral-400 whitespace-nowrap">
          <div className="flex items-center gap-2">
            <ChevronRight
              className={`w-3.5 h-3.5 text-neutral-400 transition-transform duration-200 ease-out ${
                expanded ? 'rotate-90 text-black dark:text-white' : ''
              }`}
            />
            <span className="font-mono text-[12px] text-neutral-500 dark:text-neutral-400 tabular-nums">{formattedDate}</span>
          </div>
        </td>

        <td className="px-4 py-3.5 whitespace-nowrap">
          <span className="inline-block px-2 py-0.5 rounded-md bg-black/[0.04] dark:bg-white/[0.04] border border-black/[0.06] dark:border-white/[0.06] text-[11px] font-mono font-medium text-neutral-700 dark:text-neutral-300">
            {txn.agent_id}
          </span>
        </td>

        <td className="px-4 py-3.5">
          <div className="font-medium text-[13px] text-[#1d1d1f] dark:text-white tracking-[-0.01em]">{txn.merchant_name}</div>
          <div className="text-[11px] text-neutral-500 dark:text-neutral-400 tracking-wide uppercase font-medium">{txn.merchant_category}</div>
        </td>

        <td className="px-4 py-3.5 text-sm font-semibold text-[#1d1d1f] dark:text-white whitespace-nowrap tabular-nums tracking-tight">
          ${txn.amount.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
        </td>

        <td className="px-4 py-3.5 whitespace-nowrap">
          <RiskBadge score={txn.risk_score} threshold={txn.risk_threshold} />
        </td>

        <td className="px-4 py-3.5 whitespace-nowrap">{formatStatus(txn.status)}</td>

        <td className="px-4 py-3.5 whitespace-nowrap text-right">
          {isHeld ? (
            <div className="flex items-center justify-end gap-2">
              <ApproveButton txnId={txn.id} onSuccess={onRefresh} />
              <DenyButton txnId={txn.id} onSuccess={onRefresh} />
            </div>
          ) : (
            <span className="text-[11px] font-medium text-neutral-500">
              {txn.resolved_by ? `By ${txn.resolved_by}` : '—'}
            </span>
          )}
        </td>
      </tr>

      {/* Expanded Details Row */}
      {expanded && (
        <tr className={`border-b ${isHeld ? 'border-amber-500/20 bg-amber-500/[0.02]' : 'border-black/[0.06] dark:border-white/[0.06] bg-black/[0.015] dark:bg-black/20'}`}>
          <td colSpan={7} className="px-6 py-4">
            <div className="rounded-2xl bg-white/90 dark:bg-white/[0.02] border border-black/[0.08] dark:border-white/[0.08] p-4 backdrop-blur-md shadow-lg dark:shadow-2xl space-y-3.5 transition-colors duration-200">
              <div className="flex flex-wrap items-center gap-2 pb-3 border-b border-black/[0.06] dark:border-white/[0.06] text-[11px] text-neutral-500 dark:text-neutral-400">
                <span className="px-2.5 py-1 rounded-lg bg-black/[0.03] dark:bg-white/[0.04] border border-black/[0.06] dark:border-white/[0.06] font-mono text-neutral-800 dark:text-neutral-300">
                  <strong className="text-neutral-500 dark:text-neutral-400 font-sans font-medium mr-1.5">PayPal Order ID:</strong>
                  {txn.paypal_order_id}
                </span>
                {txn.paypal_auth_id && (
                  <span className="px-2.5 py-1 rounded-lg bg-black/[0.03] dark:bg-white/[0.04] border border-black/[0.06] dark:border-white/[0.06] font-mono text-neutral-800 dark:text-neutral-300">
                    <strong className="text-neutral-500 dark:text-neutral-400 font-sans font-medium mr-1.5">Auth ID:</strong>
                    {txn.paypal_auth_id}
                  </span>
                )}
                {txn.paypal_capture_id && (
                  <span className="px-2.5 py-1 rounded-lg bg-black/[0.03] dark:bg-white/[0.04] border border-black/[0.06] dark:border-white/[0.06] font-mono text-neutral-800 dark:text-neutral-300">
                    <strong className="text-neutral-500 dark:text-neutral-400 font-sans font-medium mr-1.5">Capture ID:</strong>
                    {txn.paypal_capture_id}
                  </span>
                )}
                {txn.description && (
                  <span className="px-2.5 py-1 rounded-lg bg-black/[0.03] dark:bg-white/[0.04] border border-black/[0.06] dark:border-white/[0.06] text-neutral-800 dark:text-neutral-300">
                    <strong className="text-neutral-500 dark:text-neutral-400 font-medium mr-1.5">Item:</strong>
                    {txn.description}
                  </span>
                )}
              </div>

              {txn.decision_reason && (
                <div className="text-[12px] font-medium text-neutral-800 dark:text-neutral-200 bg-indigo-500/[0.06] dark:bg-indigo-500/[0.08] border border-indigo-500/20 rounded-xl px-3.5 py-2.5 flex items-center gap-2">
                  <span className="text-indigo-600 dark:text-indigo-400 font-semibold tracking-wide uppercase text-[10px]">Decision:</span>
                  <span>{txn.decision_reason}</span>
                </div>
              )}

              {/* Policy Violations if any */}
              {txn.policy_violations && txn.policy_violations.length > 0 && (
                <div className="p-3.5 rounded-xl bg-rose-50 dark:bg-rose-500/[0.08] border border-rose-200 dark:border-rose-500/20 text-rose-800 dark:text-rose-300 space-y-1.5 shadow-sm">
                  <div className="font-semibold text-xs flex items-center gap-2 text-rose-600 dark:text-rose-400">
                    <ShieldAlert className="w-4 h-4 stroke-[2]" /> Policy Breach Detected
                  </div>
                  {txn.policy_violations.map((pv, i) => (
                    <div key={i} className="text-xs pl-6 text-rose-700 dark:text-rose-200/90">• {pv.detail}</div>
                  ))}
                </div>
              )}

              {/* SHAP Explainability & Counterfactual */}
              <ShapExplanation explanation={txn.shap_explanation} />
            </div>
          </td>
        </tr>
      )}
    </>
  );
};

