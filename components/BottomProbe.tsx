import { useState } from 'react';
import { Pressable, Text, View } from 'react-native';

// Two counters: a button near the top and a 56 pt button pinned to the very bottom of the
// screen's content. If the screen's RNSScreenContentWrapper is natively shorter than the
// Fabric layout, the bottom button (or its lower part) is outside the wrapper's bounds and
// UIKit hit-testing drops the taps, while the top button keeps working.
export function BottomProbe({ title, testPrefix }: { title: string; testPrefix: string }) {
  const [top, setTop] = useState(0);
  const [bottom, setBottom] = useState(0);
  return (
    <View style={{ flex: 1, padding: 24 }} testID={`${testPrefix}-screen`}>
      <Text style={{ fontSize: 22 }}>{title}</Text>
      <Text style={{ fontSize: 18, marginTop: 16 }} testID={`${testPrefix}-top-count`}>
        top-taps-{top}
      </Text>
      <Text style={{ fontSize: 18 }} testID={`${testPrefix}-bottom-count`}>
        bottom-taps-{bottom}
      </Text>
      <Pressable
        testID={`${testPrefix}-top-button`}
        onPress={() => setTop((c) => c + 1)}
        style={{ marginTop: 16, backgroundColor: '#34c759', padding: 16, borderRadius: 12 }}
      >
        <Text style={{ color: 'white', textAlign: 'center', fontSize: 17 }}>Top button</Text>
      </Pressable>
      <View style={{ flex: 1 }} />
      <Pressable
        testID={`${testPrefix}-bottom-button`}
        onPress={() => setBottom((c) => c + 1)}
        style={{
          position: 'absolute',
          left: 24,
          right: 24,
          bottom: 0,
          height: 56,
          backgroundColor: '#ff3b30',
          borderTopLeftRadius: 12,
          borderTopRightRadius: 12,
          justifyContent: 'center',
        }}
      >
        <Text style={{ color: 'white', textAlign: 'center', fontSize: 17 }}>Bottom button</Text>
      </Pressable>
    </View>
  );
}
