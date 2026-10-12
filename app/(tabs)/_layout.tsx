import { Tabs } from 'expo-router';

export default function TabsLayout() {
  return (
    <Tabs
      screenOptions={{
        headerShown: false,
        tabBarStyle: { position: 'absolute' },
      }}
    >
      <Tabs.Screen name="index" options={{ title: 'Home', tabBarButtonTestID: 'tab-home' }} />
      <Tabs.Screen
        name="profile"
        options={{ title: 'Profile', tabBarButtonTestID: 'tab-profile' }}
      />
    </Tabs>
  );
}
