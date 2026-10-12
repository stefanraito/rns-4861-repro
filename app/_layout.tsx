import { Stack } from 'expo-router';
import { MonkeyReadout } from '../components/MonkeyReadout';

// Root native stack. Every root screen is headerless; the `settings` group owns its own
// native stack with visible headers.
export default function RootLayout() {
  return (
    <>
    <Stack
      screenOptions={{
        headerShown: false,
        contentStyle: { flex: 1, backgroundColor: '#ffffff' },
        animation: 'fade_from_bottom',
        animationDuration: 250,
      }}
    >
      <Stack.Screen name="(tabs)" options={{ animation: 'none' }} />
      <Stack.Screen name="(onboarding)" />
      <Stack.Screen name="settings" />
      <Stack.Screen name="control" />
      <Stack.Screen name="repro" options={{ title: 'Repro' }} />
      <Stack.Screen
        name="modal-header"
        options={{ presentation: 'modal', headerShown: true, title: 'Modal header' }}
      />
      <Stack.Screen name="modal-noheader" options={{ presentation: 'modal' }} />
    </Stack>
    <MonkeyReadout />
    </>
  );
}
