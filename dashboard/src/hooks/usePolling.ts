import { useEffect, useRef } from 'react';

export function usePolling(callback: () => void | Promise<void>, intervalMs: number = 5000) {
  const savedCallback = useRef(callback);
  const inFlightRef = useRef(false);
  const pendingRef = useRef(false);

  savedCallback.current = callback;

  useEffect(() => {
    let cancelled = false;

    const execute = async (queueIfBusy: boolean) => {
      if (inFlightRef.current) {
        if (queueIfBusy) {
          pendingRef.current = true;
        }
        return;
      }

      inFlightRef.current = true;
      try {
        await savedCallback.current();
      } finally {
        inFlightRef.current = false;
        if (!cancelled && pendingRef.current) {
          pendingRef.current = false;
          void execute(false);
        }
      }
    };

    void execute(true); // Immediate fetch on mount & whenever filter callback changes
    const id = setInterval(() => {
      void execute(false); // Skip overlapping ticks if previous poll is still in flight
    }, intervalMs);

    return () => {
      cancelled = true;
      clearInterval(id);
    };
  }, [callback, intervalMs]);
}

