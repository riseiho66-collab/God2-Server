#pragma once
#include <cstdint>

// CUSTOM-0058. Display-only current-caster clones. Called exclusively on the
// game's render thread; never adds battle slots or sends damage packets.
namespace shunying_clone {
void initialize(std::uintptr_t image_base);
// Call BEFORE the native 0052C520 consumer, while packet still identifies 126.
void on_result(void* war, unsigned source_side, unsigned source_slot,
               unsigned target_side, unsigned target_slot, bool is_custom);
// Restore transient real-caster display coordinates BEFORE native 00529020.
void before_frame(void* war);
// Call AFTER native 00529020 (which advances the native ACT frames).
void after_frame(void* war);
// Capture final native composite RTG/ACT display state immediately before draw.
void before_render(void* display);
// 0041B9C0 BEFORE initialization, with the scoped 0041C360 parent (or null).
// Observes detached native emissions; never takes ownership of native ACTs.
void on_action_initializing(void* manager,const void* parent,unsigned child_handle);
// 0041B330 BEFORE release. Prevents recycled handles from becoming slash images.
void before_action_release(void* manager,const void* action);
// Call BEFORE 0051FC40 resets battle/display ownership, and before renderer
// teardown. Never call after those managers have been destroyed.
void reset(void* war);
// Call BEFORE 00427400 on the matching display manager only.
void before_display_reset(void* display);
// A completed native action may still have its visual-only 20/30 tick tail (30 ticks per second).
bool has_tail(void* war);
}
