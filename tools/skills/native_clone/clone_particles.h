#pragma once
#include <cstdint>

// CUSTOM-0058. Preview-matched procedural red/amber additive particles.
// Render-thread only. Each cast owns one native display handle and bitmap;
// nothing is registered as a battle actor or borrowed from an ACT resource.
namespace shunying_clone::particles {
void initialize(std::uintptr_t image_base);
// cast_key = source_side*14+source_slot, 0..27. Call once per rendered frame.
// viewport is the caster display entry's byte3, normally zero.
void begin_frame(void* display, unsigned cast_key, unsigned viewport = 0);
// Exact preview tick units (30 Hz), NOT elapsed native frame counts.
void burst(unsigned cast_key, float x, float y, float age, float span = 12.0f);
// Source is the caller's validated native type0 indexed bitmap (ordinary or
// owned resized clone image). Only its pixel silhouette is read, never changed.
void silhouette(unsigned cast_key, const void* bitmap, float x, float y,
                unsigned flags, float opacity);
void return_stream(unsigned cast_key, float from_x, float from_y,
                   float home_x, float home_y, float progress, float side);
void end_frame(unsigned cast_key);
void release_cast(unsigned cast_key);
// Must run BEFORE the native manager reset/destruction.
void reset_display(void* display);
}
