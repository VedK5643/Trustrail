import axios from 'axios';
import { Transaction, Agent, AgentPolicy } from '../types';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
  timeout: 10000,
});

export const getTransactions = async (agentId?: string, status?: string): Promise<Transaction[]> => {
  const params: Record<string, string | number> = { limit: 50 };
  if (agentId && agentId !== 'all') params.agent_id = agentId;
  if (status && status !== 'all') params.status = status;
  const res = await api.get<Transaction[]>('/transactions', { params });
  return res.data;
};

export const getAgents = async (): Promise<Agent[]> => {
  const res = await api.get<Agent[]>('/agents');
  return res.data;
};

export const approveTransaction = async (txnId: string) => {
  const res = await api.post(`/decisions/${txnId}/approve`);
  return res.data;
};

export const denyTransaction = async (txnId: string) => {
  const res = await api.post(`/decisions/${txnId}/deny`);
  return res.data;
};

export const getPolicy = async (agentId: string): Promise<AgentPolicy> => {
  const res = await api.get<AgentPolicy>(`/policies/${agentId}`);
  return res.data;
};

export const updatePolicy = async (agentId: string, policy: Partial<AgentPolicy>) => {
  const res = await api.put(`/policies/${agentId}`, policy);
  return res.data;
};

export default api;

