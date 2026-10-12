import { useEffect, useState } from 'react';

// Mimics a navigation guard that renders a spinner until async state resolves.
export function useSpinner(ms: number) {
  const [loading, setLoading] = useState(ms > 0);
  useEffect(() => {
    if (ms <= 0) return;
    const timer = setTimeout(() => setLoading(false), ms);
    return () => clearTimeout(timer);
  }, [ms]);
  return loading;
}
