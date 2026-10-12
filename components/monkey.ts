import { router } from 'expo-router';
import { flags } from './flags';

// Seeded random navigation for hunting the RNSScreenContentWrapper bug. Started from the control
// route with ?monkey=<steps>&seed=<n>. Ends on /(onboarding)/step4 so the bottom button can be
// checked. Each action is recorded in `monkeyLog` and mirrored to the on-screen readout.
export const monkeyLog: string[] = [];
type Listener = () => void;
const listeners = new Set<Listener>();
export function subscribeMonkey(l: Listener) {
  listeners.add(l);
  return () => listeners.delete(l);
}
export const headerToggle = { listeners: new Set<() => void>() };

function mulberry32(seed: number) {
  let a = seed >>> 0;
  return () => {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

const actions: [string, () => void][] = [
  ['push settings/first', () => router.push('/settings/first')],
  ['push settings/second', () => router.push('/settings/second')],
  ['push settings/third', () => router.push('/settings/third')],
  ['replace onboarding/step1', () => router.replace('/(onboarding)/step1')],
  ['push onboarding/step2', () => router.push('/(onboarding)/step2')],
  ['push onboarding/step3', () => router.push('/(onboarding)/step3')],
  ['back', () => router.canGoBack() && router.back()],
  ['dismissTo tabs', () => (router.canDismiss() ? router.dismissTo('/(tabs)') : router.replace('/'))],
  ['push modal-header', () => router.push('/modal-header')],
  ['push modal-noheader', () => router.push('/modal-noheader')],
  ['toggle header', () => headerToggle.listeners.forEach((l) => l())],
  ['tab profile', () => router.navigate('/(tabs)/profile')],
];

function record(entry: string) {
  monkeyLog.push(entry);
  listeners.forEach((l) => l());
}

export function runMonkey(steps: number, seed: number) {
  const rand = mulberry32(seed);
  let i = 0;
  const tick = () => {
    if (i >= steps) {
      finish();
      return;
    }
    const [name, fn] = actions[Math.floor(rand() * actions.length)];
    record(`${i} ${name}`);
    try {
      fn();
    } catch (e) {
      record(`${i} error ${String(e)}`);
    }
    i += 1;
    setTimeout(tick, flags.monkeyMinMs + Math.floor(rand() * flags.monkeyJitterMs));
  };
  tick();
}

function finish() {
  const seq: [string, () => void][] = [
    ['final dismissAll 1', () => router.canDismiss() && router.dismissAll()],
    ['final dismissAll 2', () => router.canDismiss() && router.dismissAll()],
    ['final dismissAll 3', () => router.canDismiss() && router.dismissAll()],
    ['final dismissTo tabs', () => (router.canDismiss() ? router.dismissTo('/(tabs)') : router.replace('/'))],
    ['final push settings/first', () => router.push('/settings/first')],
    ['final replace onboarding/step1', () => router.replace('/(onboarding)/step1')],
    ['final push step2', () => router.push('/(onboarding)/step2')],
    ['final push step3', () => router.push('/(onboarding)/step3')],
    ['final push step4', () => router.push('/(onboarding)/step4')],
    ['done', () => {}],
  ];
  let j = 0;
  const next = () => {
    const [name, fn] = seq[j];
    record(name);
    try {
      fn();
    } catch (e) {
      record(`error ${String(e)}`);
    }
    j += 1;
    if (j < seq.length) setTimeout(next, 900);
  };
  setTimeout(next, 900);
}
