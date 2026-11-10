import { useEffect, useRef } from 'react';

export function usePolling(callback: () => void | Promise<void>, intervalMs: number = 2000) {
  const savedCallback = useRef(callback);

  useEffect(() => {
    savedCallback.current = callback;
  }, [callback]);

  useEffect(() => {
    const tick = () => {
      savedCallback.current();
    };

    tick(); // initial call
    const id = setInterval(tick, intervalMs);
    return () => clearInterval(id);
  }, [intervalMs]);
}

