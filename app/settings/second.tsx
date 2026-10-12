import { router } from 'expo-router';
import { useHeaderToggle } from '../../components/useHeaderToggle';
import { Button, ScrollView, Text } from 'react-native';

export default function SettingsSecond() {
  useHeaderToggle();
  return (
    <ScrollView contentContainerStyle={{ padding: 24, gap: 16 }} testID="settings-second">
      <Text style={{ fontSize: 18 }}>Settings 2 (native header visible)</Text>
      <Button
        testID="replace-to-onboarding-2"
        title="router.replace('/(onboarding)/step1')"
        onPress={() => router.replace('/(onboarding)/step1')}
      />
    </ScrollView>
  );
}
