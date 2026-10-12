import { router, Stack } from 'expo-router';
import { ActivityIndicator, Pressable, Text, View } from 'react-native';
import { useEffect, useState } from 'react';
import { flags, spinnerEvents } from '../../components/flags';
import { useSpinner } from '../../components/useSpinner';

// Root-level stack of settings screens that show the native header.
export default function SettingsLayout() {
  const loading = useSpinner(flags.settingsSpinnerMs);
  const [forced, setForced] = useState(false);
  useEffect(() => {
    const l = () => setForced(true);
    spinnerEvents.add(l);
    return () => {
      spinnerEvents.delete(l);
    };
  }, []);
  if (loading || forced) {
    return (
      <View style={{ flex: 1, alignItems: 'center', justifyContent: 'center' }}>
        <ActivityIndicator />
      </View>
    );
  }
  return (
    <View style={{ flex: 1, backgroundColor: '#ffffff' }}>
      <Stack
        screenOptions={{
          headerShown: true,
          headerShadowVisible: false,
          headerBackTitle: 'Back',
          contentStyle: { flex: 1, backgroundColor: '#ffffff' },
          animation: 'slide_from_right',
          animationDuration: 250,
          headerLeft: () => (
            <Pressable onPress={() => router.back()} testID="settings-back" hitSlop={10}>
              <Text style={{ fontSize: 17, color: '#007aff' }}>Back</Text>
            </Pressable>
          ),
          ...(flags.headerRightNull ? { headerRight: () => null } : {}),
        }}
      >
        <Stack.Screen name="first" options={{ title: 'Settings 1' }} />
        <Stack.Screen name="second" options={{ title: 'Settings 2' }} />
        <Stack.Screen name="third" options={{ headerShown: false }} />
      </Stack>
    </View>
  );
}
