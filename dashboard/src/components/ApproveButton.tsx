import React, { useState } from 'react';
import { Check, Loader2 } from 'lucide-react';
import { approveTransaction } from '../api/client';

interface ApproveButtonProps {
  txnId: string;
  onSuccess: () => void;
}

export const ApproveButton: React.FC<ApproveButtonProps> = ({ txnId, onSuccess }) => {
  const [loading, setLoading] = useState(false);

  const handleApprove = async (e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      setLoading(true);
      await approveTransaction(txnId);
      onSuccess();
    } catch (err) {
      console.error('Approval failed:', err);
      alert('Approval failed. Check backend logs.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <button
      onClick={handleApprove}
      disabled={loading}
      className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl text-xs font-medium bg-emerald-600 hover:bg-emerald-500 active:scale-95 text-white shadow-[0_2px_12px_rgba(16,185,129,0.35)] transition-all duration-150 disabled:opacity-50 border border-emerald-400/30 tracking-tight"
    >
      {loading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Check className="w-3.5 h-3.5 stroke-[2.5]" />}
      Approve & Capture
    </button>
  );
};

