import { useEffect, useState } from 'react';
import { Text } from 'react-native';
import { monkeyLog, subscribeMonkey } from './monkey';

// Tiny non-interactive readout of the last monkey action (only rendered while the monkey ran).
export function MonkeyReadout() {
  const [, force] = useState(0);
  useEffect(() => {
    const unsub = subscribeMonkey(() => force((n) => n + 1));
    return () => {
      unsub();
    };
  }, []);
  if (monkeyLog.length === 0) return null;
  return (
    <Text
      pointerEvents="none"
      testID="monkey-last"
      style={{ position: 'absolute', top: 54, right: 8, fontSize: 10, color: '#888' }}
    >
      {monkeyLog[monkeyLog.length - 1]}
    </Text>
  );
}
