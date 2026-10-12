import { router } from 'expo-router';
import { Button, ScrollView, Text } from 'react-native';

export default function ModalNoHeader() {
  return (
    <ScrollView contentContainerStyle={{ padding: 24, paddingTop: 80, gap: 16 }} testID="modal-noheader">
      <Text style={{ fontSize: 18 }}>Modal without header</Text>
      <Button title="Close" onPress={() => router.back()} />
    </ScrollView>
  );
}
