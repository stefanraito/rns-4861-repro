import { router, useLocalSearchParams } from 'expo-router';
import { useEffect } from 'react';
import { ActivityIndicator, Text, View } from 'react-native';
import { applyFlagParams, flags } from '../components/flags';
import { runMonkey } from '../components/monkey';

// Opened by a deep link (rns4861://control). Mimics a test-control route: it mounts on top of
// whatever is on screen, does some async work, then returns to the tab shell with dismissTo.
// Query params also set the experiment flags in components/flags.ts.
export default function ControlScreen() {
  const params = useLocalSearchParams<Record<string, string>>();
  const delay = params.delay;

  useEffect(() => {
    applyFlagParams(params);
    const timer = setTimeout(
      () => {
        if (router.canDismiss()) {
          router.dismissTo('/(tabs)');
        } else {
          router.replace('/');
        }
        if (flags.monkey > 0) {
          const steps = flags.monkey;
          flags.monkey = 0;
          setTimeout(() => runMonkey(steps, flags.seed), 800);
        }
      },
      Number(delay ?? 500)
    );
    return () => clearTimeout(timer);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [delay]);

  return (
    <View style={{ flex: 1, alignItems: 'center', justifyContent: 'center' }} testID="control">
      <ActivityIndicator />
      <Text>Control route: dismissing to tabs…</Text>
    </View>
  );
}
