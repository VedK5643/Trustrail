import React, { useState, useEffect, useCallback } from 'react';
import { Agent, Transaction } from './types';
import { getAgents, getTransactions } from './api/client';
import { usePolling } from './hooks/usePolling';
import { AgentSidebar } from './components/AgentSidebar';
import { TransactionFeed } from './components/TransactionFeed';
import { PolicyEditor } from './components/PolicyEditor';
import { Shield, Activity, Sliders, Sun, Moon } from 'lucide-react';

export default function App() {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [selectedAgentId, setSelectedAgentId] = useState<string>('all');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [activeTab, setActiveTab] = useState<'feed' | 'policies'>('feed');
  const [theme, setTheme] = useState<'dark' | 'light'>(() => {
    return (localStorage.getItem('trustrail_theme') as 'dark' | 'light') || 'dark';
  });

  useEffect(() => {
    const isDark = theme === 'dark';
    if (isDark) {
      document.documentElement.classList.add('dark');
      document.body.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
      document.body.classList.remove('dark');
    }
    localStorage.setItem('trustrail_theme', theme);
  }, [theme]);

  const toggleTheme = () => {
    setTheme((prev) => (prev === 'dark' ? 'light' : 'dark'));
  };

  const fetchData = useCallback(async () => {
    try {
      const [agentList, txnList] = await Promise.all([
        getAgents(),
        getTransactions(selectedAgentId, statusFilter),
      ]);
      setAgents(agentList);
      setTransactions(txnList);
    } catch (err) {
      console.warn('Polling fetch error:', err);
    }
  }, [selectedAgentId, statusFilter]);

  usePolling(fetchData, 5000);

  return (
    <div className={`flex flex-col h-screen w-screen overflow-hidden ${theme === 'dark' ? 'dark' : ''} bg-[#f5f5f7] dark:bg-[#08080a] text-[#1d1d1f] dark:text-[#f5f5f7] font-sans antialiased selection:bg-blue-500/20 dark:selection:bg-blue-500/30 selection:text-blue-900 dark:selection:text-white transition-colors duration-200`}>
      {/* Translucent Apple Glass Header */}
      <header className="h-14 border-b border-black/[0.08] dark:border-white/[0.08] bg-white/80 dark:bg-[#0c0c0e]/80 backdrop-blur-2xl px-6 flex items-center justify-between shrink-0 z-30 shadow-[0_2px_12px_rgba(0,0,0,0.03)] dark:shadow-[0_4px_20px_rgba(0,0,0,0.3)] transition-colors duration-200">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-xl bg-gradient-to-b from-blue-500 to-blue-600 flex items-center justify-center shadow-[0_2px_8px_rgba(37,99,235,0.3)] border border-blue-400/30">
            <Shield className="w-4 h-4 text-white stroke-[2.2]" />
          </div>
          <div className="flex items-center gap-2.5">
            <h1 className="text-sm font-semibold tracking-[-0.02em] text-[#1d1d1f] dark:text-white">
              TrustRail
            </h1>
            <span className="text-[10px] font-mono font-medium px-2 py-0.5 rounded-full bg-black/[0.04] dark:bg-white/[0.05] text-neutral-600 dark:text-neutral-400 border border-black/[0.06] dark:border-white/[0.08] tracking-wider uppercase">
              PayPal Spend Firewall
            </span>
          </div>
        </div>

        {/* Apple Segmented Control for Navigation Tabs */}
        <div className="flex items-center bg-black/[0.05] dark:bg-black/40 p-1 rounded-xl border border-black/[0.06] dark:border-white/[0.08] shadow-inner">
          <button
            onClick={() => setActiveTab('feed')}
            className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-medium transition-all duration-150 active:scale-[0.98] ${
              activeTab === 'feed'
                ? 'bg-white dark:bg-white/[0.12] text-black dark:text-white shadow-sm border border-black/[0.06] dark:border-white/[0.10]'
                : 'text-neutral-600 dark:text-neutral-400 hover:text-black dark:hover:text-white hover:bg-black/[0.03] dark:hover:bg-white/[0.04]'
            }`}
          >
            <Activity className="w-3.5 h-3.5 stroke-[2]" /> Live Spend Firewall
          </button>
          <button
            onClick={() => setActiveTab('policies')}
            className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-medium transition-all duration-150 active:scale-[0.98] ${
              activeTab === 'policies'
                ? 'bg-white dark:bg-white/[0.12] text-black dark:text-white shadow-sm border border-black/[0.06] dark:border-white/[0.10]'
                : 'text-neutral-600 dark:text-neutral-400 hover:text-black dark:hover:text-white hover:bg-black/[0.03] dark:hover:bg-white/[0.04]'
            }`}
          >
            <Sliders className="w-3.5 h-3.5 stroke-[2]" /> Policy-as-Code
          </button>
        </div>

        {/* Right Header Actions: Theme Toggle & Live Indicator */}
        <div className="flex items-center gap-3">
          {/* Apple Appearance Switcher Button */}
          <button
            onClick={toggleTheme}
            title={`Switch to ${theme === 'dark' ? 'Light' : 'Dark'} Mode`}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-black/[0.05] dark:bg-white/[0.08] border border-black/[0.08] dark:border-white/[0.10] text-xs font-medium text-neutral-700 dark:text-neutral-200 hover:text-black dark:hover:text-white hover:bg-black/[0.08] dark:hover:bg-white/[0.14] transition-all duration-150 active:scale-95 shadow-sm"
          >
            {theme === 'dark' ? (
              <>
                <Sun className="w-3.5 h-3.5 stroke-[2.2] text-amber-400" />
                <span>Light</span>
              </>
            ) : (
              <>
                <Moon className="w-3.5 h-3.5 stroke-[2.2] text-blue-600" />
                <span>Dark</span>
              </>
            )}
          </button>

          {/* Live Indicator Capsule */}
          <div className="flex items-center gap-2 px-2.5 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-600 dark:text-emerald-400 text-xs font-medium shadow-[0_0_12px_rgba(16,185,129,0.12)]">
            <span className="w-2 h-2 rounded-full bg-emerald-500 dark:bg-emerald-400 animate-pulse shadow-[0_0_8px_rgba(52,211,153,0.8)]"></span>
            <span className="text-[11px] tracking-wide font-medium">Live Ingestion Active</span>
          </div>
        </div>
      </header>

      {/* Main Content Area */}
      <div className="flex flex-1 overflow-hidden">
        {/* Left Agent Reputation Sidebar */}
        <AgentSidebar
          agents={agents}
          selectedAgentId={selectedAgentId}
          onSelectAgent={setSelectedAgentId}
          onRefresh={fetchData}
        />

        {/* Central View */}
        <main className="flex-1 overflow-hidden flex flex-col bg-[#f5f5f7] dark:bg-[#08080a] transition-colors duration-200">
          {activeTab === 'feed' ? (
            <TransactionFeed
              transactions={transactions}
              statusFilter={statusFilter}
              onStatusFilterChange={setStatusFilter}
              onRefresh={fetchData}
            />
          ) : (
            <div className="p-8 overflow-y-auto">
              <PolicyEditor agents={agents} selectedAgentId={selectedAgentId} />
            </div>
          )}
        </main>
      </div>
    </div>
  );
}

