import { Stack } from 'expo-router';
import { ActivityIndicator, View } from 'react-native';
import { flags } from '../../components/flags';
import { useSpinner } from '../../components/useSpinner';

// Nested headerless native stack.
export default function OnboardingLayout() {
  const loading = useSpinner(flags.onboardingSpinnerMs);
  if (loading) {
    return (
      <View style={{ flex: 1, alignItems: 'center', justifyContent: 'center' }}>
        <ActivityIndicator />
      </View>
    );
  }
  return (
    <>
      <Stack
        screenOptions={{
          headerShown: false,
          contentStyle: { flex: 1, backgroundColor: '#ffffff' },
          animation: 'slide_from_right',
          animationDuration: 250,
        }}
      >
        <Stack.Screen name="step1" />
        <Stack.Screen name="step2" />
        <Stack.Screen name="step3" />
        <Stack.Screen name="step4" />
      </Stack>
      {flags.marker ? (
        <View
          pointerEvents="none"
          style={{ position: 'absolute', top: '25%', left: 0, width: 1, height: 1 }}
        />
      ) : null}
    </>
  );
}
