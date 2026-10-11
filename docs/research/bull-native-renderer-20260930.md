# 牛轉仙界踏 native render bridge (CUSTOM-0059)

Status: implemented candidate; native hook ABI, Win32 unit tests and actual exported frame-pack samples pass. No live client visual/audio acceptance is claimed here.

## Scope and invariants

Skill0/150 only. Existing skill126 hooks, native blade3 remap, dark clones, display lifecycle and battle-background cache restoration remain unchanged. One aggregated cast runs 240 frames at30fps (8 seconds), irrespective of target count. Read-only source frames are the accepted preview export; no new bull choreography is generated at runtime.

`bull_effect.cpp` streams one ground and one foreground frame from the chosen player/enemy pack. It never allocates all813MB of exported data. Each decoded RGBA layer is1040×807; bounded row-span parsing rejects invalid dimensions, offsets, lengths, overlapping/out-of-order rows, reserved bits and trailing data. A missing/corrupt frame disables its visual rendering and logs the failure, while the native eight-second completion contract remains finite.

## Layer and final-present hooks

Original432810 restores cached background A4→A0 via533FC0, draws display+A8 viewport0 and1 using426AB0, then B0/B4 overlays. Existing hooks scope the current battle renderer; ground is composited before viewport0, foreground after viewport0. Viewport1 and later UI remain above the herd. Actual floating-damage depth must still be checked live.

The accepted preview actor mapping is x=nativeX*1.28+8, y=nativeY*1.28-1. The compositor inverses this against the native800×600 baseline (scaling other display dimensions from that baseline); it does not squash the807px canvas height into600px. First rendering logs actual native surface dimensions for acceptance.

The renderer presentation hook is432A20 (`568bf1e8d80efdff`,8 stolen bytes,
ret0), with the common53CA50 hook (`83ec505356`,5 stolen bytes, ret12) retained
for other presentation routes. Nested hooks share one shift/restore scope.
Before native presentation it translates the **entire completed game content
including UI** on screen+10's backbuffer, with clamped edge extension, then
restores that buffer after presentation. It matches only the screen captured
from the active battle renderer+9C. The former4329A0 hook was incorrect for
normal battle presentation and was replaced after the owner's live report on
2026-10-01. The OS window frame never moves. The approved preview amplitude
is retained. The export manifest's `shake.scope: battle viewport only`
describes the unchanged preview source; the later owner instruction applies
the runtime shake to all game content including UI. Source assets are unchanged.

Native524820 generic skill-tick hook (`83ec14535556`,6 bytes, ret4) dispatches150 to `bull_native_tick`; all other definitions execute the original trampoline. Root-owned tick code controls four native hit-text/HP events and native completion. The frame hook retains completion until the eight-second timeline ends.

## Surface and cancellation safety

A0 points to the native CDX wrapper; wrapper+80 is IDirectDrawSurface7. Lock results validate16/32bit RGB, dimensions and signed row pitch. Positive/negative pitch and padding are respected. No pointer to locked memory survives Unlock. Failed locks do not write. Focus/display reset detaches the display pointer while preserving time; the next native frame rebinds it. Real battle reset clears both renderer/tick state and stops audio. Final skill completion releases streams and audio.

## Audio

One owned PCM waveform combines the accepted whistle then stampede, without the rejected bull roar. Runtime filename is `Data2/Fight/Custom/Bull150/bull-stampede-native-voice.wav`.

Original44E870 reads SFX enable owner+7F19 and volume DWORD+7F14;44EBF0 clamps volume0..10 and maps VA570C30 to DirectSound hundredth-dB values [-10000,-5000,-4000,-3000,-2000,-1500,-1000,-700,-500,-250,0]. The new owned PCM buffer uses that same gain via10^(dB/2000), honors mute/device availability, and never changes OS output volume. Mid-cast mute stops the buffer. Other volume changes take effect on the next cast. PCM headers/rates/channels/alignments/duration are validated before waveOut playback; reset/unprepare/close owns cancellation.

## Candidate paths

- `build-bull-native/bin/God2ShunyingClone.dll`
- Runtime packs: executable parent / `Data2/Fight/Custom/Bull150/{player,enemy}-{ground,foreground}.bfx`
- Optional `shake.f32`:240 signed float x/y pairs; absent uses the pinned preview shake formula.
- Source: `tools/skills/native_clone/bull_effect.{h,cpp}`, `bull_frames.h`, `clone_hooks.cpp` and root-owned `bull_native_tick.{h,cpp}`.

## Verification

- `python -B -m tools.skills.native_clone.bull_effect_test`: strict span bounds, RGBA565/32bit compositing, pitch, final-present shift/restoration, failed lock and8000ms lifecycle; reads actual four exported packs atframes0/70/239 and rejects240.
- `python -B -m tools.skills.native_clone.clone_preload_test`:27 accepted preload/result/ACT emission checks pass, including126 remap and unrelated skills unchanged.
- `python -B -m tools.skills.native_clone.clone_evidence`:26 native hooks/API ABI checks pass (17hooks,9APIs).
- `cmake --build build-bull-native --config Release`:Win32 Release candidate passes.

Remaining acceptance: actual player/enemy placement, floating-number depth, map/UI focus roundtrip, completed8s turns and audible volume in the current client. Flattened preview additive particles into straight RGBA are a documented compositing approximation; this is not a pixel-perfect claim on arbitrary native backgrounds.

## Bounded performance review

`bull_effect_benchmark.py` compiles the actual renderer with MSVC/O2 and uses a fake800×600 RGB565 DirectDraw surface with208 real exported frames25..232. It measures streaming decode plus both paint layers, and separately final UI shake/restore. This excludes the native game's other work and device-driver lock cost, so it is not a live FPS claim.

Initial decode+paint average14.33ms/max18.17ms; optimized average6.25ms/max9.62ms. Final UI shake averaged1.06ms. Cached coordinate maps, native-format channel lookup tables and reused RGBA allocation preserve arithmetic and geometry. Tests compare768,000 blends covering all256 alpha values and RGB565/RGB555/RGB888 layouts bit for bit against the original reference, plus all native800×600 coordinate-axis mappings.

Result ingestion deduplicates a bounded28-owner pending registry. The wall clock and sound start only when the actual150 native actor tick claims its pending owner via begin_actor. A different owner waits only while another cast is active, without consuming time or changing HP/poses. Packet receipt order never overrides native actor scheduling. Subsequent targets do not restart a cast. Its native tick and compositor use the same elapsed clock; finish_actor releases the owner only after native8000ms cleanup. Focus/display reset rebinds display ownership without resetting elapsed time.

## Installer cardinality regression

Live startup exposed a bridge implementation defect: the hook table grew from15 to17 while the protection-save array remained15. The final two `VirtualProtect` calls wrote past that stack array, and the process correctly terminated with stack-cookie fast-fail. Root corrected the storage extent to derive from `decltype(hooks)`.

`python -B -m tools.skills.native_clone.clone_installer_test` now instruments a temporary source copy with `static_assert(protections.size()==hooks.size())`. The historical15-slot mutation is required to fail compilation. The corrected source then compiles and executes the actual complete installer on an isolated Win32 memory-image fixture, verifying all17 jump entries and normal process exit. Existing ABI and result-preload tests did not execute installation and therefore were insufficient to detect this bug; installer regression is an additional required bridge check.

## Multi-owner and surface-lifetime regression

Internal testing found the initial single global renderer owner was overwritten when two150 casters arrived in one batch. `on_result` now registers and deduplicates up to28 valid owners; `begin_actor` lets whichever pending owner the native scheduler actually selects claim an idle renderer, and `finish_actor` releases only that exact owner. Each receives its complete independent8s animation. Missing/corrupt visual packs still complete within8s after activation; unstarted stale queue entries do not independently hold native completion forever.

`bull_effect_lifecycle_test.py` executes the actual C++ renderer with deterministic time and fake DirectDraw memory surfaces. It verifies repeated target receipts, consecutive casts by the same owner, two-owner native-order/clock isolation, including A-then-B receipt with B selected first, focus reset/rebind, bounded28-owner cancellation, missing packs and valid-header/corrupt-payload packs, plus full UI translation/restoration at800×600 and1024×768 in16/32bit with padded positive/negative pitches. These are internal harness tests, not player-operated/live UI evidence.

The final-present bridge now AddRefs the exact COM surface before calling the native presenter and Releases it after restoration, including failed relocks. This closes a lifetime risk if native presentation rebuilds or replaces the surface on focus change. The harness simulates replacement mid-presentation and verifies the old surface remains alive until restoration, the replacement pixels stay unchanged, and reference counts return to their expected values.

Native damage float layering and visible death pose remain separate checks; renderer memory-surface tests do not establish them. Updated208-frame benchmark after these changes: paint/decode7.11ms average/max11.95ms and final UI shake1.05ms average, with normal machine-load variability.

The pending-owner registry deliberately does **not** impose FIFO receipt ordering: native result arrival and actual actor execution order are separate contracts. A regression enqueues A then B, starts B first, blocks A only while B is active, then gives A its complete8s cast. This avoids waiting for an actor that the native scheduler cannot yet execute.

## 2026-10-01 shared-target death repair and internal retest

Confirmed defect: when two casters hit the same target and only the later
result is lethal, original83 ingestion sets target+232 to9 and target+277 to2,
but the earlier caster's own +224 status is0. The custom tick previously
decremented +277 only for a caster whose own status was9. Consequently the
earlier hit left2 pending, the final hit left1, and HP reached0 without final
death. The failing receipt is preserved at
`artifacts/reviews/bull-20261001/pending-hits-result.json`.

The only runtime source change is in `bull_native_tick.cpp`: at the fourth
impact, perform the death-counter decision if either the saved batch-final
target state or the individual action state is9. The saved state is required
because +232 is deliberately hidden until the fourth visual impact. Native
00524D86..00524DCD uses this same OR condition. Pending actions now drain2→1→0,
reaction15 postpones death after the first cast, and reaction9 finalizes the
last cast. The skill150 dispatch boundary and other skill behavior are intact.

Internal evidence (all passed):

- `python -B -m tools.skills.verify_thousand_bulls_shared_native`: executes
  original x86 result ingestion and death-decision instructions for both
  sides,1/2/14 targets and both playback orders,12 cases. The pinned image hash
  and observations are in `shared-target-native-20261001.json`.
- `python -B -m tools.skills.native_clone.bull_native_tick_test`: existing
  rounding, timing, validation and126 passthrough tests plus12 shared-target
  cases executing the actual repaired C++ tick.
- `python -B -m tools.skills.native_clone.bull_native_pipeline_test`: actual
  C++ tick plus actual renderer and exported player/enemy frame packs,
  18 scenarios/36 casts (9 scenarios for each side). Covers repeated casts,
  shared targets in both orders, four HP phases, delayed death, independent
  eight-second clocks, waiting owners, focus rebind, compositing and full-screen
  restoration. A temporary old-condition mutation must fail with
  `shared pending count`; it does. Evidence: `native-pipeline-20261001.json`.
- Both-side TCP blackbox18 cases and the four skill CTest entries pass.
  Full Application isolated authentication/world/battle flow passes two
  player casts against14 targets; it is not an enemy Application AI test.
- Renderer lifecycle, original x86 helper/cleanup ABI,17-hook installer and
  existing result/preload27 checks pass. Frozen-chat verification passes.

The candidate DLL was rebuilt. `internal-blackbox-report.json` records the
new binary hash, test paths and candidate snapshot. Formal server/client,
accounts and saves were not changed. The integration harness uses deterministic
time, native API sinks and DirectDraw memory surfaces; it does not establish
live window rendering, audible playback or GPU-driver acceptance. Those remain
explicitly pending rather than being counted as internal-test failures.

## 2026-10-01 live-report follow-up: absent shake and sound

The owner reported neither effect during the actual trial. Two bridge-wiring
defects were found. First, the selected4329A0 wrapper is not called by the
normal battle-present path. The native53CA50 presenter is called from normal
paths including432A20/435DC0; its screen+10 backbuffer already contains the
composed frame. The hook now surrounds53CA50 with its correct three-argument
thiscall ABI. Second,516AE0 receives the battle owner, not the UI owner.
Audio must resolve battle+20 → UI+CFF5C → sound owner. The previous direct
battle+CFF5C read suppressed playback.

The integration test now uses separate composition and presentation surfaces,
requires the presentation pixels to shift while composition pixels remain
unchanged, and verifies restoration. It supplies the real battle→UI→audio
pointer chain and actual waveform, intercepting waveOut only at the OS boundary.
All36 casts across both sides submit non-silent buffers and release them;
mute/zero volume remain honored. Negative mutations for the wrong audio owner
and absent final-screen shift must fail. The installer,26 ABI checks and28
preload/presentation-hook checks pass. Cast diagnostics now log successful
audio submission and actual backbuffer shift, as well as unavailable/muted
audio and waveOut failures. OS audible output and visible shake still require
the reopened trial's live acceptance; mocked-device success is not that claim.

### Second live report: direct blit branch and hoofbeat loudness

The owner still saw no shake and heard weak hoofbeats. The runtime log confirmed
audio submission and no applied backbuffer shift. Original432A20 mode!=0 uses
IDirectDrawSurface::Blt directly and bypasses53CA50, explaining the remaining
uncovered branch. `verify_bull_present_paths.py` executes original instructions
for mode0 and mode1 and confirms the distinct routes. The added432A20 wrapper
now encloses both; the common53CA50 hook nests without a second shift or an
early restoration. The installer now has18 hooks and explicitly relocates
432A20's stolen rel32 call to403900. Its regression verifies both the relocated
call destination and trampoline return, in addition to bounded protection
storage.27 native ABI checks and29 hook checks pass.

Only the audio buffer's hoofbeat portion after0.8373923s receives a gain ramp
up to2.5 with a tanh soft limiter; the first20ms smooths the transition. Native
volume and mute settings still apply. Measured output from the actual C++
audio path, at full native volume: hoofbeat RMS increases2.243x (+7.02dB),
whistle bytes are unchanged and hard-clipped samples remain0. Both-side
18-scenario/36-cast integration and lifecycle regressions pass. The live
trial still needs visual/audible acceptance; these tests do not replace it.

## 2026-10-01 upper-edge clipping repair

The owner supplied a live screenshot showing a horizontal cut through the herd
below the top shortcut bar as damage appeared. Two preview-specific crops
were retained incorrectly: all exported layers clipped to canvas y99..758,
and native paint additionally restricted destination rows to preview y100..759.
The native exporter now changes only those three preview clip rectangles to
the full1040x807 canvas in its isolated VM; source preview files and animation
routes remain unchanged. Native paint now traverses every surface row. The
original viewport1/UI render still runs after the effect layers, providing
normal UI occlusion without an artificial horizontal cut through the herd.

All960 layer frames pass bounds/source/hash verification. Four damage-phase
frames restore225623 upper-edge foreground pixels on the player side and30671
on the enemy side (summed source pixels, not display resolution). Interior
comparisons record small canvas-rasterizer rounding differences rather than
claiming byte identity. The actual C++ pipeline independently compares every
destination pixel for all four impacts over36 casts on both sides; all pass.
A temporary old-crop mutation is required to fail full-canvas composition.
The old packs are retained in
`artifacts/releases/thousand-bulls-fullcanvas-20261001/visualpack-before`.
Visible native-client confirmation remains separate from these internal tests.
