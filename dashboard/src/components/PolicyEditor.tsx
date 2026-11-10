import React, { useState, useEffect } from 'react';
import { Agent, AgentPolicy } from '../types';
import { getPolicy, updatePolicy } from '../api/client';
import { Sliders, Save, CheckCircle2, AlertCircle } from 'lucide-react';

interface PolicyEditorProps {
  agents: Agent[];
  selectedAgentId: string;
}

export const PolicyEditor: React.FC<PolicyEditorProps> = ({ agents, selectedAgentId }) => {
  const targetAgentId = selectedAgentId === 'all' ? (agents[0]?.id || 'procurement-agent') : selectedAgentId;
  const [policy, setPolicy] = useState<AgentPolicy | null>(null);
  const [loading, setLoading] = useState(false);
  const [savedSuccess, setSavedSuccess] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Form states
  const [dailyCap, setDailyCap] = useState<string>('');
  const [perTxnCap, setPerTxnCap] = useState<string>('');
  const [merchantDenylist, setMerchantDenylist] = useState<string>('');
  const [merchantAllowlist, setMerchantAllowlist] = useState<string>('');
  const [categoryDenylist, setCategoryDenylist] = useState<string>('');

  useEffect(() => {
    if (targetAgentId) {
      loadPolicy(targetAgentId);
    }
  }, [targetAgentId]);

  const loadPolicy = async (agentId: string) => {
    try {
      setLoading(true);
      setError(null);
      const data = await getPolicy(agentId);
      setPolicy(data);
      setDailyCap(data.daily_spend_cap ? String(data.daily_spend_cap) : '');
      setPerTxnCap(data.per_txn_cap ? String(data.per_txn_cap) : '');
      setMerchantDenylist(data.merchant_denylist ? data.merchant_denylist.join(', ') : '');
      setMerchantAllowlist(data.merchant_allowlist ? data.merchant_allowlist.join(', ') : '');
      setCategoryDenylist(data.category_denylist ? data.category_denylist.join(', ') : '');
    } catch (err: any) {
      setError('Failed to load agent policy');
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setLoading(true);
      setError(null);
      setSavedSuccess(false);

      const payload = {
        daily_spend_cap: dailyCap ? parseFloat(dailyCap) : null,
        per_txn_cap: perTxnCap ? parseFloat(perTxnCap) : null,
        merchant_denylist: merchantDenylist.split(',').map((s) => s.trim()).filter(Boolean),
        merchant_allowlist: merchantAllowlist.split(',').map((s) => s.trim()).filter(Boolean),
        category_denylist: categoryDenylist.split(',').map((s) => s.trim()).filter(Boolean),
        category_allowlist: [],
      };

      await updatePolicy(targetAgentId, payload);
      setSavedSuccess(true);
      setTimeout(() => setSavedSuccess(false), 3000);
    } catch (err: any) {
      setError('Failed to save policy updates.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-7 max-w-2xl bg-white dark:bg-white/[0.025] rounded-3xl border border-black/[0.08] dark:border-white/[0.08] backdrop-blur-2xl shadow-xl dark:shadow-2xl text-neutral-800 dark:text-neutral-200 transition-colors duration-200">
      <div className="flex items-center justify-between pb-5 border-b border-black/[0.06] dark:border-white/[0.06] mb-6">
        <div className="flex items-center gap-2.5">
          <div className="w-7 h-7 rounded-xl bg-blue-500/10 border border-blue-500/20 flex items-center justify-center text-blue-500 dark:text-blue-400 shadow-sm">
            <Sliders className="w-4 h-4 stroke-[2]" />
          </div>
          <div>
            <h2 className="text-sm font-semibold tracking-[-0.01em] text-[#1d1d1f] dark:text-white">Policy-as-Code Configuration</h2>
            <p className="text-[11px] text-neutral-500 dark:text-neutral-400">Deterministic spend caps & guardrail parameters</p>
          </div>
        </div>
        <span className="text-[11px] font-mono text-neutral-700 dark:text-neutral-300 bg-black/[0.04] dark:bg-white/[0.04] px-3 py-1 rounded-full border border-black/[0.06] dark:border-white/[0.08]">
          Agent: <strong className="text-black dark:text-white">{targetAgentId}</strong>
        </span>
      </div>

      {error && (
        <div className="mb-5 p-3.5 bg-rose-50 dark:bg-rose-500/[0.08] border border-rose-200 dark:border-rose-500/20 text-rose-800 dark:text-rose-300 rounded-2xl text-xs flex items-center gap-2 shadow-sm">
          <AlertCircle className="w-4 h-4 stroke-[2] shrink-0" /> {error}
        </div>
      )}

      {savedSuccess && (
        <div className="mb-5 p-3.5 bg-emerald-50 dark:bg-emerald-500/[0.08] border border-emerald-200 dark:border-emerald-500/20 text-emerald-800 dark:text-emerald-300 rounded-2xl text-xs flex items-center gap-2 shadow-sm">
          <CheckCircle2 className="w-4 h-4 stroke-[2] shrink-0" /> Policy rules updated successfully.
        </div>
      )}

      <form onSubmit={handleSave} className="space-y-5">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-[11px] font-semibold text-neutral-600 dark:text-neutral-400 uppercase tracking-wider mb-1.5">
              Daily Spend Cap ($ USD)
            </label>
            <input
              type="number"
              step="0.01"
              placeholder="e.g. 2000.00"
              value={dailyCap}
              onChange={(e) => setDailyCap(e.target.value)}
              className="w-full bg-neutral-50 dark:bg-black/40 border border-black/[0.1] dark:border-white/[0.08] rounded-xl px-3.5 py-2.5 text-xs text-[#1d1d1f] dark:text-white placeholder-neutral-400 dark:placeholder-neutral-600 focus:bg-white dark:focus:bg-black/50 focus:outline-none focus:ring-2 focus:ring-blue-500/70 focus:border-transparent transition-all shadow-inner font-mono"
            />
          </div>

          <div>
            <label className="block text-[11px] font-semibold text-neutral-600 dark:text-neutral-400 uppercase tracking-wider mb-1.5">
              Per-Transaction Cap ($ USD)
            </label>
            <input
              type="number"
              step="0.01"
              placeholder="e.g. 500.00"
              value={perTxnCap}
              onChange={(e) => setPerTxnCap(e.target.value)}
              className="w-full bg-neutral-50 dark:bg-black/40 border border-black/[0.1] dark:border-white/[0.08] rounded-xl px-3.5 py-2.5 text-xs text-[#1d1d1f] dark:text-white placeholder-neutral-400 dark:placeholder-neutral-600 focus:bg-white dark:focus:bg-black/50 focus:outline-none focus:ring-2 focus:ring-blue-500/70 focus:border-transparent transition-all shadow-inner font-mono"
            />
          </div>
        </div>

        <div>
          <label className="block text-[11px] font-semibold text-neutral-600 dark:text-neutral-400 uppercase tracking-wider mb-1.5">
            Merchant Denylist (comma-separated IDs)
          </label>
          <input
            type="text"
            placeholder="e.g. merch_anom_02, newvendor-gaming"
            value={merchantDenylist}
            onChange={(e) => setMerchantDenylist(e.target.value)}
            className="w-full bg-neutral-50 dark:bg-black/40 border border-black/[0.1] dark:border-white/[0.08] rounded-xl px-3.5 py-2.5 text-xs text-[#1d1d1f] dark:text-white placeholder-neutral-400 dark:placeholder-neutral-600 focus:bg-white dark:focus:bg-black/50 focus:outline-none focus:ring-2 focus:ring-blue-500/70 focus:border-transparent transition-all shadow-inner font-mono"
          />
        </div>

        <div>
          <label className="block text-[11px] font-semibold text-neutral-600 dark:text-neutral-400 uppercase tracking-wider mb-1.5">
            Merchant Allowlist (optional strictly-allowed IDs)
          </label>
          <input
            type="text"
            placeholder="Leave empty to allow all non-denylisted merchants"
            value={merchantAllowlist}
            onChange={(e) => setMerchantAllowlist(e.target.value)}
            className="w-full bg-neutral-50 dark:bg-black/40 border border-black/[0.1] dark:border-white/[0.08] rounded-xl px-3.5 py-2.5 text-xs text-[#1d1d1f] dark:text-white placeholder-neutral-400 dark:placeholder-neutral-600 focus:bg-white dark:focus:bg-black/50 focus:outline-none focus:ring-2 focus:ring-blue-500/70 focus:border-transparent transition-all shadow-inner font-mono"
          />
        </div>

        <div>
          <label className="block text-[11px] font-semibold text-neutral-600 dark:text-neutral-400 uppercase tracking-wider mb-1.5">
            Restricted Categories (comma-separated)
          </label>
          <input
            type="text"
            placeholder="e.g. gambling, crypto, luxury_goods"
            value={categoryDenylist}
            onChange={(e) => setCategoryDenylist(e.target.value)}
            className="w-full bg-neutral-50 dark:bg-black/40 border border-black/[0.1] dark:border-white/[0.08] rounded-xl px-3.5 py-2.5 text-xs text-[#1d1d1f] dark:text-white placeholder-neutral-400 dark:placeholder-neutral-600 focus:bg-white dark:focus:bg-black/50 focus:outline-none focus:ring-2 focus:ring-blue-500/70 focus:border-transparent transition-all shadow-inner font-mono"
          />
        </div>

        <div className="pt-2">
          <button
            type="submit"
            disabled={loading}
            className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 active:scale-95 text-white text-xs font-medium rounded-xl shadow-[0_2px_12px_rgba(37,99,235,0.35)] border border-blue-400/30 transition-all duration-150 disabled:opacity-50 tracking-tight"
          >
            <Save className="w-3.5 h-3.5 stroke-[2]" />
            {loading ? 'Saving Policy...' : 'Save Policies'}
          </button>
        </div>
      </form>
    </div>
  );
};

