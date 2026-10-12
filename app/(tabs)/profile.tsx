import { router } from 'expo-router';
import { Button, Text, View } from 'react-native';

export default function ProfileTab() {
  return (
    <View
      style={{ flex: 1, alignItems: 'center', justifyContent: 'center', gap: 16 }}
      testID="profile-screen"
    >
      <Text style={{ fontSize: 22 }}>Profile tab</Text>
      <Button
        testID="open-settings"
        title="Open settings (header stack)"
        onPress={() => router.push('/settings/first')}
      />
    </View>
  );
}
