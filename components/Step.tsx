import { type Href, router } from 'expo-router';
import { Pressable, Text, View } from 'react-native';

export function Step({ n, next }: { n: number; next: Href }) {
  return (
    <View style={{ flex: 1, padding: 24, paddingTop: 100, gap: 16 }} testID={`step${n}`}>
      <Text style={{ fontSize: 24 }}>Onboarding step {n} (headerless)</Text>
      <Pressable
        testID={`step${n}-continue`}
        onPress={() => router.push(next)}
        style={{ backgroundColor: '#007aff', padding: 16, borderRadius: 12 }}
      >
        <Text style={{ color: 'white', textAlign: 'center', fontSize: 17 }}>Continue</Text>
      </Pressable>
    </View>
  );
}
