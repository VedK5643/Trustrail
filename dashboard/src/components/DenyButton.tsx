import React, { useState } from 'react';
import { X, Loader2 } from 'lucide-react';
import { denyTransaction } from '../api/client';

interface DenyButtonProps {
  txnId: string;
  onSuccess: () => void;
}

export const DenyButton: React.FC<DenyButtonProps> = ({ txnId, onSuccess }) => {
  const [loading, setLoading] = useState(false);

  const handleDeny = async (e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      setLoading(true);
      await denyTransaction(txnId);
      onSuccess();
    } catch (err) {
      console.error('Denial failed:', err);
      alert('Denial failed. Check backend logs.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <button
      onClick={handleDeny}
      disabled={loading}
      className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl text-xs font-medium bg-rose-600 hover:bg-rose-500 active:scale-95 text-white shadow-[0_2px_12px_rgba(244,63,94,0.35)] transition-all duration-150 disabled:opacity-50 border border-rose-400/30 tracking-tight"
    >
      {loading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <X className="w-3.5 h-3.5 stroke-[2.5]" />}
      Deny & Void
    </button>
  );
};

