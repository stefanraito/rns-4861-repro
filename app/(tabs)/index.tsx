import { router } from 'expo-router';
import { Button, Text, View } from 'react-native';

export default function HomeTab() {
  return (
    <View style={{ flex: 1, alignItems: 'center', justifyContent: 'center' }} testID="home-screen">
      <Text style={{ fontSize: 22 }}>Home tab</Text>
      <Button testID="open-repro" title="Open #4861 repro" onPress={() => router.push('/repro')} />
    </View>
  );
}
