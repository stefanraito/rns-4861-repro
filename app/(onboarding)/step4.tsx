import { useNavigation } from 'expo-router';
import { useState } from 'react';
import { Keyboard, Pressable, Text, TextInput, View } from 'react-native';

// Last screen. On a 956 pt tall iPhone 17 Pro Max the bottom button sits at y ≈ 860–916,
// i.e. inside the bottom 116 pt. When the bug hits, the screen's RNSScreenContentWrapper is
// 840 pt tall, so taps on the bottom button fall outside the wrapper's bounds and are dropped,
// while the upper button keeps working.
export default function Step4() {
  const [top, setTop] = useState(0);
  const [bottom, setBottom] = useState(0);
  const navigation = useNavigation();
  // Shows the native header on this headerless screen and hides it again `ms` later.
  const flashHeader = (ms: number) => {
    navigation.setOptions({ headerShown: true });
    setTimeout(() => navigation.setOptions({ headerShown: false }), ms);
  };
  // Same, but the "show" commit also mounts `n` extra views so the main thread is still busy
  // mounting when the "hide" commit arrives.
  const [heavy, setHeavy] = useState(0);
  const flashHeaderHeavy = (n: number) => {
    navigation.setOptions({ headerShown: true });
    setHeavy(n);
    setTimeout(() => navigation.setOptions({ headerShown: false }), 16);
  };
  // Same, but the views are pre-rendered with display: 'none', so the "show" commit is cheap for
  // JS but makes the main thread mount `n` views.
  const [pre, setPre] = useState(false);
  const flashHeaderPre = () => {
    navigation.setOptions({ headerShown: true });
    setPre(true);
    setTimeout(() => navigation.setOptions({ headerShown: false }), 16);
  };
  // Same, but the "show" commit also mounts an autofocused TextInput: bringing up the keyboard keeps
  // the main thread busy inside that mount while JS already commits the "hide".
  const [input, setInput] = useState(false);
  const flashHeaderInput = (ms: number) => {
    navigation.setOptions({ headerShown: true });
    setInput(true);
    setTimeout(() => navigation.setOptions({ headerShown: false }), ms);
    // Put the keyboard away again so it cannot be what blocks the bottom button.
    setTimeout(() => {
      Keyboard.dismiss();
      setInput(false);
    }, 800);
  };
  // Same, but the "show" commit makes the main thread create `n` multiline TextInputs (UITextView is
  // expensive to create) that were pre-rendered with display: 'none', so JS stays cheap.
  const [inputs, setInputs] = useState(false);
  const flashHeaderInputs = () => {
    navigation.setOptions({ headerShown: true });
    setInputs(true);
    setTimeout(() => navigation.setOptions({ headerShown: false }), 16);
  };
  // Same, but the JS thread is kept busy for `ms` before hiding again, so the native side mounts
  // and lays out the shown header while Fabric cannot yet commit the resulting layout.
  const flashHeaderBusy = (ms: number) => {
    navigation.setOptions({ headerShown: true });
    setTimeout(() => {
      const end = Date.now() + ms;
      while (Date.now() < end) {
        // busy wait
      }
      navigation.setOptions({ headerShown: false });
    }, 0);
  };

  return (
    <View style={{ flex: 1, padding: 24, paddingTop: 100 }} testID="step4">
      <Text style={{ fontSize: 24 }}>Onboarding step 4 (headerless)</Text>
      <Text style={{ fontSize: 20, marginTop: 24 }} testID="top-count">
        top-taps-{top}
      </Text>
      <Text style={{ fontSize: 20 }} testID="bottom-count">
        bottom-taps-{bottom}
      </Text>
      <Pressable
        testID="top-button"
        onPress={() => setTop((c) => c + 1)}
        style={{ marginTop: 24, backgroundColor: '#34c759', padding: 16, borderRadius: 12 }}
      >
        <Text style={{ color: 'white', textAlign: 'center', fontSize: 17 }}>Top button</Text>
      </Pressable>
      <View style={{ flexDirection: 'row', flexWrap: 'wrap', gap: 8, marginTop: 16 }}>
        {[0, 2, 5, 10, 16, 33, 50, 150, 500].map((ms) => (
          <Pressable
            key={ms}
            testID={`flash-header-${ms}`}
            onPress={() => flashHeader(ms)}
            style={{ backgroundColor: '#8e8e93', padding: 10, borderRadius: 8 }}
          >
            <Text style={{ color: 'white' }}>flash {ms}</Text>
          </Pressable>
        ))}
      </View>
      <View style={{ flexDirection: 'row', flexWrap: 'wrap', gap: 8, marginTop: 8 }}>
        {[50, 150, 300, 600].map((ms) => (
          <Pressable
            key={ms}
            testID={`flash-busy-${ms}`}
            onPress={() => flashHeaderBusy(ms)}
            style={{ backgroundColor: '#5856d6', padding: 10, borderRadius: 8 }}
          >
            <Text style={{ color: 'white' }}>busy {ms}</Text>
          </Pressable>
        ))}
      </View>
      <View style={{ flexDirection: 'row', flexWrap: 'wrap', gap: 8, marginTop: 8 }}>
        {[1000, 3000, 6000].map((n) => (
          <Pressable
            key={n}
            testID={`flash-heavy-${n}`}
            onPress={() => flashHeaderHeavy(n)}
            style={{ backgroundColor: '#af52de', padding: 10, borderRadius: 8 }}
          >
            <Text style={{ color: 'white' }}>heavy {n}</Text>
          </Pressable>
        ))}
      </View>
      <View style={{ flexDirection: 'row', flexWrap: 'wrap', gap: 8, marginTop: 8 }}>
        {[0, 16, 50].map((ms) => (
          <Pressable
            key={ms}
            testID={`flash-input-${ms}`}
            onPress={() => flashHeaderInput(ms)}
            style={{ backgroundColor: '#ff2d55', padding: 10, borderRadius: 8 }}
          >
            <Text style={{ color: 'white' }}>input {ms}</Text>
          </Pressable>
        ))}
      </View>
      {input ? (
        <TextInput
          autoFocus
          testID="flash-input"
          style={{ height: 1, width: 1, opacity: 0 }}
          onFocus={() => {}}
        />
      ) : null}
      <Pressable
        testID="flash-inputs"
        onPress={flashHeaderInputs}
        style={{ backgroundColor: '#30b0c7', padding: 10, borderRadius: 8, marginTop: 8, alignSelf: 'flex-start' }}
      >
        <Text style={{ color: 'white' }}>inputs 400</Text>
      </Pressable>
      <View
        pointerEvents="none"
        style={{
          position: 'absolute',
          width: 1,
          height: 1,
          overflow: 'hidden',
          opacity: 0,
          display: inputs ? 'flex' : 'none',
        }}
      >
        {Array.from({ length: 400 }, (_, i) => (
          <TextInput key={i} multiline editable={false} style={{ position: 'absolute', width: 1, height: 1 }} />
        ))}
      </View>
      <Pressable
        testID="flash-pre"
        onPress={flashHeaderPre}
        style={{ backgroundColor: '#ff9500', padding: 10, borderRadius: 8, marginTop: 8, alignSelf: 'flex-start' }}
      >
        <Text style={{ color: 'white' }}>pre 4000</Text>
      </Pressable>
      <View
        style={{
          position: 'absolute',
          width: 1,
          height: 1,
          overflow: 'hidden',
          opacity: 0,
          display: pre ? 'flex' : 'none',
        }}
      >
        {Array.from({ length: 4000 }, (_, i) => (
          <View key={i} collapsable={false} style={{ position: 'absolute', width: 1, height: 1 }} />
        ))}
      </View>
      <View style={{ position: 'absolute', width: 1, height: 1, overflow: 'hidden', opacity: 0 }}>
        {Array.from({ length: heavy }, (_, i) => (
          <View key={i} collapsable={false} style={{ width: 1, height: 1 }} />
        ))}
      </View>
      <View style={{ flex: 1 }} />
      <Pressable
        testID="bottom-button"
        onPress={() => setBottom((c) => c + 1)}
        style={{
          height: 56,
          marginBottom: 40 - 24,
          backgroundColor: '#ff3b30',
          borderRadius: 12,
          justifyContent: 'center',
        }}
      >
        <Text style={{ color: 'white', textAlign: 'center', fontSize: 17 }}>
          Bottom button (inside bottom 116 pt)
        </Text>
      </Pressable>
    </View>
  );
}
