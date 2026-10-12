import { router } from 'expo-router';
import { Button, ScrollView, Text } from 'react-native';

// A headerless screen inside the header stack (like a full-screen form in a settings stack).
export default function SettingsThird() {
  return (
    <ScrollView contentContainerStyle={{ padding: 24, paddingTop: 100, gap: 16 }} testID="settings-third">
      <Text style={{ fontSize: 18 }}>Settings 3 (headerShown: false)</Text>
      <Button title="Back" onPress={() => router.back()} />
    </ScrollView>
  );
}
