// Runtime switches for experiments, set through the control deep link, e.g.
// rns4861://control?settingsSpinnerMs=300&modal=1. They live in module scope so they survive
// navigation but reset on app relaunch.
export const flags = {
  settingsSpinnerMs: 0,
  onboardingSpinnerMs: 0,
  modal: false,
  replaceDelayMs: 0,
  headerRightNull: false,
  marker: false,
  // When >= 0: on confirm, swap the settings Stack for a spinner (unmounting the header stack in
  // place) and router.replace after this many ms.
  unmountStackMs: -1,
  monkey: 0,
  seed: 1,
  monkeyMinMs: 350,
  monkeyJitterMs: 600,
};

export function applyFlagParams(params: Record<string, string | string[] | undefined>) {
  for (const key of Object.keys(flags) as (keyof typeof flags)[]) {
    const raw = params[key];
    if (raw === undefined) continue;
    const value = Array.isArray(raw) ? raw[0] : raw;
    if (typeof flags[key] === 'boolean') {
      (flags as Record<string, unknown>)[key] = value === '1' || value === 'true';
    } else {
      (flags as Record<string, unknown>)[key] = Number(value);
    }
  }
}

type Listener = () => void;
export const spinnerEvents = new Set<Listener>();
