import React from 'react';
import { Agent } from '../types';
import { TrustScoreCard } from './TrustScoreCard';
import { Bot, RefreshCw } from 'lucide-react';

interface AgentSidebarProps {
  agents: Agent[];
  selectedAgentId: string;
  onSelectAgent: (id: string) => void;
  onRefresh: () => void;
}

export const AgentSidebar: React.FC<AgentSidebarProps> = ({
  agents,
  selectedAgentId,
  onSelectAgent,
  onRefresh,
}) => {
  return (
    <aside className="w-80 border-r border-black/[0.08] dark:border-white/[0.08] bg-white/95 dark:bg-[#0c0c0e]/95 p-5 flex flex-col gap-5 shrink-0 h-full overflow-y-auto z-20 transition-colors duration-200">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="w-6 h-6 rounded-lg bg-blue-500/10 border border-blue-500/20 flex items-center justify-center text-blue-500 dark:text-blue-400">
            <Bot className="w-3.5 h-3.5 stroke-[2]" />
          </div>
          <h2 className="text-xs font-semibold uppercase tracking-wider text-neutral-600 dark:text-neutral-300">Monitored Agents</h2>
        </div>
        <button
          onClick={onRefresh}
          title="Refresh Agents"
          className="p-1.5 rounded-lg text-neutral-500 dark:text-neutral-400 hover:text-black dark:hover:text-white hover:bg-black/[0.05] dark:hover:bg-white/[0.06] transition-all duration-150 active:scale-95"
        >
          <RefreshCw className="w-3.5 h-3.5 stroke-[2]" />
        </button>
      </div>

      <div className="flex flex-col gap-1.5">
        <button
          onClick={() => onSelectAgent('all')}
          className={`px-3.5 py-2 text-xs font-medium rounded-xl text-left transition-all duration-150 active:scale-[0.99] flex items-center justify-between ${
            selectedAgentId === 'all'
              ? 'bg-blue-600 text-white shadow-md shadow-blue-600/25 font-semibold'
              : 'text-neutral-600 dark:text-neutral-400 hover:bg-black/[0.04] dark:hover:bg-white/[0.04] hover:text-black dark:hover:text-white'
          }`}
        >
          <span>All Monitored Agents</span>
          <span className={`text-[10px] font-mono px-1.5 py-0.5 rounded ${selectedAgentId === 'all' ? 'bg-black/20 text-white' : 'bg-black/[0.06] dark:bg-white/[0.08] text-neutral-600 dark:text-neutral-300'}`}>
            {agents.length}
          </span>
        </button>
      </div>

      <div className="flex flex-col gap-3">
        {agents.map((agent) => (
          <div
            key={agent.id}
            onClick={() => onSelectAgent(agent.id)}
            className={`cursor-pointer rounded-2xl transition-all duration-150 active:scale-[0.99] ${
              selectedAgentId === agent.id
                ? 'ring-2 ring-blue-500 shadow-[0_4px_20px_rgba(59,130,246,0.2)]'
                : 'hover:scale-[1.01]'
            }`}
          >
            <TrustScoreCard
              name={agent.name}
              score={agent.trust_score}
              alpha={agent.trust_alpha}
              beta={agent.trust_beta}
            />
          </div>
        ))}
      </div>

      <div className="mt-auto pt-4 border-t border-black/[0.06] dark:border-white/[0.06] text-[11px] text-neutral-500 dark:text-neutral-400 space-y-0.5">
        <p className="font-medium text-neutral-600 dark:text-neutral-300">Beta-Distribution Reputation Model</p>
        <p className="font-mono text-[10px] text-neutral-400 dark:text-neutral-500">Score = α / (α + β) · Real-time Decay</p>
      </div>
    </aside>
  );
};

