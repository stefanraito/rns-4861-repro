import { router } from 'expo-router';
import { useHeaderToggle } from '../../components/useHeaderToggle';
import { useState } from 'react';
import { Button, Modal, Pressable, ScrollView, Text, View } from 'react-native';
import { flags, spinnerEvents } from '../../components/flags';

function goToOnboarding() {
  const go = () => router.replace('/(onboarding)/step1');
  if (flags.unmountStackMs >= 0) {
    spinnerEvents.forEach((l) => l());
    setTimeout(go, flags.unmountStackMs);
    return;
  }
  if (flags.replaceDelayMs > 0) setTimeout(go, flags.replaceDelayMs);
  else go();
}

export default function SettingsFirst() {
  useHeaderToggle();
  const [confirmVisible, setConfirmVisible] = useState(false);
  return (
    <ScrollView contentContainerStyle={{ padding: 24, gap: 16 }} testID="settings-first">
      <Text style={{ fontSize: 18 }}>Settings 1 (native header visible)</Text>
      <Button
        testID="open-settings-second"
        title="Push Settings 2"
        onPress={() => router.push('/settings/second')}
      />
      <Button
        testID="replace-to-onboarding"
        title="router.replace('/(onboarding)/step1')"
        onPress={() => (flags.modal ? setConfirmVisible(true) : goToOnboarding())}
      />
      <Modal
        visible={confirmVisible}
        transparent
        animationType="fade"
        onRequestClose={() => setConfirmVisible(false)}
      >
        <View
          style={{
            flex: 1,
            backgroundColor: 'rgba(0,0,0,0.4)',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          <Pressable
            testID="confirm-replace"
            onPress={() => {
              setConfirmVisible(false);
              goToOnboarding();
            }}
            style={{ backgroundColor: 'white', padding: 24, borderRadius: 12 }}
          >
            <Text style={{ fontSize: 17 }}>Confirm</Text>
          </Pressable>
        </View>
      </Modal>
    </ScrollView>
  );
}
