# react-native-screens #4861 reproduction

On iOS 26 with the New Architecture and react-native-screens 4.15.x or 4.16.0, a headerless
native-stack screen can end up with a `RNSScreenContentWrapper` 116 pt shorter than its
`RNSScreenView` (440×840 inside 440×956 on an iPhone 17 Pro Max). Fabric still lays the
children out for 956 pt. Touches in the bottom 116 pt are dropped.

This app reproduces that state without a debugger, and the result matches what we recorded in the
original app:

- the wrapper frame is `(0 0; 440 840)`;
- the `RNSScreenView` is `(0 0; 440 956)`;
- Fabric's cached `_layoutMetrics.frame` is `(0 0; 440 956)`;
- UIKit set the 840 through `-[UIView _applyISEngineLayoutValuesToBoundsOnly:]`, called from
  `resizeSubviewsWithOldSize:`.

## Versions

| | |
| --- | --- |
| react-native | 0.81.5 (New Architecture, Hermes) |
| expo | 54.0.35, expo-router 6.0.24 |
| react-native-screens | 4.16.0 |
| @react-navigation/native-stack | 7.14.12 |
| Simulator | iPhone 17 Pro Max, iOS 26.5 (23F77) |
| Xcode | 27.0 (27A266a), macOS 26.6.2 |
| Build | Release (`-configuration Release -sdk iphonesimulator`) |

## Steps

1. `npm install`, `npx expo prebuild --platform ios`, then build Release:
   `scripts/build.sh <simulator-udid>`. The script builds and installs the app.
2. Launch the app. On the Home tab, tap **Open #4861 repro**. This pushes `app/repro.tsx`, a
   headerless screen in the root native stack.
3. Tap **1. Show and hide the native header**.
4. Tap **Top button (works)**. `top-taps-1` appears.
5. Tap **2. Bottom button**.

- Expected: `bottom-taps-1`.
- Actual: nothing happens, and `bottom-taps` stays at 0. The bottom 116 pt of the screen stay
  dead until the screen unmounts.

Automated: `maestro --device <udid> test .maestro/repro-4861.yaml`. It fails at
`assertVisible: 'bottom-taps-1'`.

Control: `.maestro/repro-4861-control.yaml` runs the same heavy mount without showing the header,
and passes.

### Determinism (unpatched 4.16.0, Release, no debugger)

| Flow | Result |
| --- | --- |
| `repro-4861.yaml` | failed 20 of 21 runs over four batches; one run passed |
| `repro-4861-control.yaml` | passed 5/5 |

A 400-input version failed 3 of 5 runs, which is why the stall uses 800.

### What step 3 does

`app/repro.tsx` calls `navigation.setOptions({ headerShown: true })` and, 16 ms later,
`setOptions({ headerShown: false })`.

The same commit that shows the header also turns on 800 pre-rendered, hidden, non-editable
`TextInput`s. Creating 800 `UITextView`s keeps the main thread busy, so the "hide" commit is
already queued when the "show" mount finishes. Both commits then mount in the same run-loop turn.

Any heavy mount does the same. Without one, the outcome depends on timing:

- 0–500 ms flashes with no heavy mount passed.
- With lldb probes attached, a plain 50 ms flash also failed every time, because the breakpoints
  stall the main thread at the same point.

## Root cause

All references are to `node_modules/react-native-screens/ios` at 4.16.0.

1. **The header is shown.**
   - `+[RNSScreenStackHeaderConfig updateViewController:withConfig:animated:]`
     (`RNSScreenStackHeaderConfig.mm:549`) runs the iOS 26 workaround from PR #3111
     (lines 571–597). With the header visible and not translucent, it sets
     `contentWrapper.translatesAutoresizingMaskIntoConstraints = NO` (line 587) and activates
     the safe-area constraints.
   - `[navctr setNavigationBarHidden:NO animated:YES]` (line 611) then lays out the nav
     controller synchronously, inside the mount. The trace stack runs through
     `_setNavigationBarHidden:edge:duration:`, then `_layoutTopViewControllerLookForNested:`,
     then `_resizeWithOldSuperviewSize:`, then `_applyISEngineLayoutValuesToBoundsOnly:`.
   - The `RNSScreenView` becomes 840 tall, and the Auto Layout engine sets the wrapper to 840.
2. **Fabric hears about it.** `-[RNSScreen viewDidLayoutSubviews]` calls `updateBounds`
   (`RNSScreen.mm:1563`, `:1582`, `:156`), which enqueues an `RNSScreenState` update for the
   840 pt size.
3. **The header is hidden in the same run-loop turn.**
   - The else branch (lines 598–608) deactivates the constraints and sets
     `translatesAutoresizingMaskIntoConstraints = YES` (line 607) while the wrapper is still
     840 pt.
   - UIKit turns the current frame into fixed autoresizing constraints:
     `NSAutoresizingMaskLayoutConstraint … RNSScreenContentWrapper.height == 840`, recorded in
     `evidence/lldb-wrapper.txt`.
   - The nav bar hides again and `updateBounds` enqueues a 956 pt state update.
4. **Fabric never re-lays out the wrapper.**
   - React Native coalesces consecutive state updates for the same family
     (`ReactCommon/react/renderer/core/EventQueue.cpp:68-81`). They are only flushed on the main
     run loop's BeforeWaiting beat (`React/Fabric/RCTSurfacePresenter.mm:261`), so the 840
     update is replaced by the 956 one.
   - Fabric's shadow tree never changes. `RCTViewComponentView` diffs new layout against its
     cached 956 frame and never applies it again.
5. **The wrapper stays short.**
   - The `RNSScreenView` grows back to 956, but the wrapper keeps its fixed-height autoresizing
     constraint and stays 840.
   - `-[RCTViewComponentView betterHitTest:]` treats a view with no overflow as clipping
     (`RCTViewComponentView.mm:645-653`). Touches below y = 840 never reach the children.

Even if Fabric does lay out 840 first, any path that runs the if branch and then the else branch
on the same screen before Fabric commits the 840 layout leaves the wrapper stuck.

## The recycling hypothesis was wrong

The starting hypothesis was that the wrapper goes back to Fabric's recycle pool with
`translatesAutoresizingMaskIntoConstraints == NO` and stale engine values. All checks below were
run with lldb (`scripts/probe4861.py`, `scripts/leaksim.py`, `scripts/faultsim.py`):

- **The config resets recycled wrappers.** `-[RNSScreenStackHeaderConfig prepareForRecycle]`
  (lines 1017–1031) runs right after the wrapper's own `prepareForRecycle` and sets
  `translatesAutoresizingMaskIntoConstraints = YES` on it. In every trace, a recycled header
  wrapper went back into service with YES (`evidence/probe-trace-baseline-sequence.txt`).
- **A forced leak is fixed on the next show.** With the reset skipped from lldb
  (`scripts/leaksim.sh`), the headerless-screen branch of `updateViewController` resets the
  wrapper on the next `willShowViewController`. The flow still passed.
- **A leaked wrapper collapses to zero, not to 840.** When both the reset and that branch were
  skipped (`scripts/faultsim2.sh`), the leaked wrapper became 0 pt tall, which does not match
  what we saw in the original app.
- **The stuck wrapper has YES, not NO.** Prediction (a) is false. The stuck wrapper is held by
  autoresizing constraints, not by Auto Layout.
- **Prediction (c) does not fix it.** Adding `prepareForRecycle` to `RNSScreenContentWrapper.mm`
  that resets YES still failed 4/5.

## Fix experiments (node_modules patches, all reverted)

| Patch | Result |
| --- | --- |
| (c) `RNSScreenContentWrapper prepareForRecycle` resets YES | still fails 4/5 |
| After line 607, re-apply Fabric's frame (`self.frame = RCTCGRectFromRect(_layoutMetrics.frame)` through a new `rns_applyFabricFrame` method on the wrapper) | passes 6/6. Also passes the nested-stack variant 2/2, `.maestro/repro.yaml`, and a header-stack variant |
| Turn off the whole iOS 26 block (line 573 `if ((false))`), which is how RNS ≥ 4.17.0 behaves | passes 4/4 |

## Latest react-native-screens

- The iOS 26 `_safeAreaConstraints` workaround shipped in 4.15.0 through 4.16.0.
- PR #3206, "remove workaround for content under header in modal" (merged 2025-09-10), removed
  it in 4.17.0. There is no `_safeAreaConstraints` or wrapper
  `translatesAutoresizingMaskIntoConstraints` toggling in 4.17.0 through 4.29.0 (latest);
  checked from `npm pack` tarballs.
- PR #3187 is the one that brought wrapper recycling back with the `prepareForRecycle` reset.
- Not tested by installing 4.17+ here. Turning the block off in 4.16.0 is a stand-in for that.

## Relation to the original app

The failure state matches the original app exactly, but the trigger there is still unknown: its
screens never call `setOptions({ headerShown })`. It has to be either an `updateViewController`
call with a visible, non-translucent header config followed by a hidden one before Fabric commits
the 840 layout, or the same if/else sequence reached on that screen's view through another path.
`scripts/probe4861.py` in `light` mode logs every `updateViewController` call (vc, config, `show`,
`translucent`) and every `translatesAutoresizingMaskIntoConstraints` write on a wrapper, with its
caller, which is how to find it.

## Other variants tried that did not reproduce the 116 pt state

These are still in the app and set by flags on `rns4861://control?...`, see
`components/flags.ts`:

- two header-stack visits followed by `router.replace` into a nested headerless stack;
- loading spinners before the nested stacks mount;
- a `headerRight` that returns `null`, and a sibling marker after the nested stack;
- a transparent RN `Modal` confirm before the replace, with 0–400 ms delays;
- unmounting the header stack in place before the replace;
- seeded random navigation (`scripts/monkey.sh`, 10 seeds × 60–80 steps), mixing pushes, back,
  replace, dismissTo, modals with and without headers, and header toggling, with lldb checks for
  leaked or mismatched wrappers.

A related but different bug does reproduce every time: a `presentation: 'modal'` screen with
`headerShown: true` (`app/modal-header.tsx`). Its inner wrapper is `(0 20; 440 820)` while Fabric
has `(0 0; 440 840)`. That is the "content under header in modal" problem from PR #3206, and it
is not this issue.

## Tooling

| Script | What it does |
| --- | --- |
| `scripts/build.sh <udid>` | Release build and install |
| `scripts/scan.sh <udid>` | Lists every mounted wrapper: tAMIC, frame, Fabric cache, the screen's header config. Flags `SHORT` and `BAD` |
| `scripts/probe.sh <udid> <flow> [out]` | Runs a flow with `scripts/probe4861.py` attached (set `PROBE_MODE` to `light`, `minimal` or `wlm`) |
| `scripts/leaksim.sh`, `scripts/faultsim2.sh` | Fault injection for the recycling hypothesis |
| `scripts/run-variant.sh`, `scripts/monkey.sh` | Navigation variants and fuzzing |

`evidence/` holds the Maestro log, the screenshot (`top-taps-1`, `bottom-taps-0`), the lldb view
and constraint dump, and the probe trace of the show/hide sequence.
