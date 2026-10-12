import { useNavigation } from 'expo-router';
import { useState } from 'react';
import { Pressable, Text, TextInput, View } from 'react-native';

// Minimal reproduction for software-mansion/react-native-screens#4861 (RNS 4.15.x/4.16.0, iOS 26,
// Fabric). A headerless native-stack screen briefly shows its native header and hides it again
// before Fabric has re-laid out the screen for the header. RNS leaves the screen's
// RNSScreenContentWrapper at the header-sized height (956 - 116 = 840 pt on an iPhone 17 Pro Max)
// while Fabric still lays the children out for 956 pt, so the bottom 116 pt stop taking touches.
//
// The 800 hidden TextInputs only keep the main thread busy while it mounts the "show header"
// commit, so that the "hide header" commit is mounted in the same run-loop turn. Any heavy mount
// does the same; without that the outcome depends on timing.
export default function Repro() {
  const navigation = useNavigation();
  const [busy, setBusy] = useState(false);
  const [top, setTop] = useState(0);
  const [bottom, setBottom] = useState(0);

  const flashHeader = () => {
    navigation.setOptions({ headerShown: true });
    setBusy(true);
    setTimeout(() => navigation.setOptions({ headerShown: false }), 16);
  };

  // Control: the same heavy mount without touching the header. Does not break anything.
  const mountOnly = () => setBusy(true);

  return (
    <View style={{ flex: 1, padding: 24, paddingTop: 100 }} testID="repro-screen">
      <Text style={{ fontSize: 22 }}>RNS #4861 repro (headerless screen)</Text>
      <Text style={{ fontSize: 18, marginTop: 16 }}>top-taps-{top}</Text>
      <Text style={{ fontSize: 18 }}>bottom-taps-{bottom}</Text>
      <Pressable
        testID="repro-flash-header"
        onPress={flashHeader}
        style={{ marginTop: 16, backgroundColor: '#007aff', padding: 16, borderRadius: 12 }}
      >
        <Text style={{ color: 'white', textAlign: 'center', fontSize: 17 }}>
          1. Show and hide the native header
        </Text>
      </Pressable>
      <Pressable
        testID="repro-control"
        onPress={mountOnly}
        style={{ marginTop: 8, backgroundColor: '#8e8e93', padding: 10, borderRadius: 12 }}
      >
        <Text style={{ color: 'white', textAlign: 'center' }}>Control: heavy mount only</Text>
      </Pressable>
      <Pressable
        testID="repro-top-button"
        onPress={() => setTop((c) => c + 1)}
        style={{ marginTop: 16, backgroundColor: '#34c759', padding: 16, borderRadius: 12 }}
      >
        <Text style={{ color: 'white', textAlign: 'center', fontSize: 17 }}>Top button (works)</Text>
      </Pressable>
      <View
        pointerEvents="none"
        style={{
          position: 'absolute',
          width: 1,
          height: 1,
          overflow: 'hidden',
          opacity: 0,
          display: busy ? 'flex' : 'none',
        }}
      >
        {Array.from({ length: 800 }, (_, i) => (
          <TextInput
            key={i}
            multiline
            editable={false}
            style={{ position: 'absolute', width: 1, height: 1 }}
          />
        ))}
      </View>
      <View style={{ flex: 1 }} />
      <Pressable
        testID="repro-bottom-button"
        onPress={() => setBottom((c) => c + 1)}
        style={{
          height: 56,
          marginBottom: 16,
          backgroundColor: '#ff3b30',
          borderRadius: 12,
          justifyContent: 'center',
        }}
      >
        <Text style={{ color: 'white', textAlign: 'center', fontSize: 17 }}>
          2. Bottom button (inside the bottom 116 pt)
        </Text>
      </Pressable>
    </View>
  );
}
