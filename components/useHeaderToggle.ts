import { useNavigation } from 'expo-router';
import { useEffect, useRef } from 'react';
import { headerToggle } from './monkey';

// Lets the monkey flip headerShown on whichever settings screen is mounted.
export function useHeaderToggle() {
  const navigation = useNavigation();
  const shown = useRef(true);
  useEffect(() => {
    const l = () => {
      shown.current = !shown.current;
      navigation.setOptions({ headerShown: shown.current });
    };
    headerToggle.listeners.add(l);
    return () => {
      headerToggle.listeners.delete(l);
    };
  }, [navigation]);
}
