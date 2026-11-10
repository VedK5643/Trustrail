import React from 'react';
import { Transaction } from '../types';
import { TransactionRow } from './TransactionRow';
import { ShieldCheck, Inbox } from 'lucide-react';

interface TransactionFeedProps {
  transactions: Transaction[];
  statusFilter: string;
  onStatusFilterChange: (status: string) => void;
  onRefresh: () => void;
}

export const TransactionFeed: React.FC<TransactionFeedProps> = ({
  transactions,
  statusFilter,
  onStatusFilterChange,
  onRefresh,
}) => {
  const heldCount = transactions.filter((t) => t.status === 'HELD').length;

  return (
    <div className="flex-1 flex flex-col h-full overflow-hidden bg-[#f5f5f7] dark:bg-[#08080a] transition-colors duration-200">
      {/* Top Filter Bar with Frosted Translucency */}
      <div className="px-6 py-3 border-b border-black/[0.08] dark:border-white/[0.08] flex items-center justify-between bg-white/70 dark:bg-[#0c0c0e]/60 backdrop-blur-xl shrink-0 z-20 transition-colors duration-200">
        <div className="flex items-center gap-1.5 bg-black/[0.05] dark:bg-black/40 p-1 rounded-xl border border-black/[0.06] dark:border-white/[0.08] shadow-inner">
          {['all', 'HELD', 'AUTO_CAPTURED', 'CAPTURED', 'VOIDED'].map((st) => (
            <button
              key={st}
              onClick={() => onStatusFilterChange(st)}
              className={`px-3 py-1 rounded-lg text-xs font-medium transition-all duration-150 active:scale-[0.98] flex items-center gap-1.5 ${
                statusFilter === st
                  ? 'bg-white dark:bg-white/[0.14] text-black dark:text-white shadow-sm border border-black/[0.06] dark:border-white/[0.10]'
                  : 'text-neutral-600 dark:text-neutral-400 hover:text-black dark:hover:text-white hover:bg-black/[0.03] dark:hover:bg-white/[0.04]'
              }`}
            >
              {st === 'all' ? 'All Transactions' : st.replace('_', ' ')}
              {st === 'HELD' && heldCount > 0 && (
                <span className="flex h-2 w-2 relative">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-amber-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-amber-400"></span>
                </span>
              )}
            </button>
          ))}
        </div>

        <div className="flex items-center gap-2 text-xs text-neutral-500 dark:text-neutral-400">
          <ShieldCheck className="w-4 h-4 text-emerald-500 dark:text-emerald-400 stroke-[2]" />
          <span className="text-[11px] font-medium tracking-wide">PayPal Sandbox Authorize-Gated Feed</span>
        </div>
      </div>

      {/* Transactions Table Container */}
      <div className="flex-1 overflow-y-auto">
        {transactions.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-72 text-neutral-500 gap-3">
            <div className="w-12 h-12 rounded-2xl bg-black/[0.03] dark:bg-white/[0.03] border border-black/[0.06] dark:border-white/[0.06] flex items-center justify-center text-neutral-400">
              <Inbox className="w-6 h-6 stroke-[1.5]" />
            </div>
            <p className="text-sm font-medium text-neutral-600 dark:text-neutral-400">No transactions match current filter.</p>
          </div>
        ) : (
          <table className="w-full text-left border-collapse">
            <thead className="sticky top-0 bg-[#f5f5f7]/95 dark:bg-[#0c0c0e]/95 backdrop-blur-2xl border-b border-black/[0.08] dark:border-white/[0.08] text-[11px] font-medium uppercase tracking-wider text-neutral-500 dark:text-neutral-400 z-10 select-none transition-colors duration-200">
              <tr>
                <th className="px-5 py-3">Time</th>
                <th className="px-5 py-3">Agent</th>
                <th className="px-5 py-3">Merchant</th>
                <th className="px-5 py-3">Amount</th>
                <th className="px-5 py-3">Risk Assessment</th>
                <th className="px-5 py-3">Firewall Status</th>
                <th className="px-5 py-3 text-right">Action / Resolution</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-black/[0.04] dark:divide-white/[0.04]">
              {transactions.map((txn) => (
                <TransactionRow key={txn.id} txn={txn} onRefresh={onRefresh} />
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
};

