#pragma once
#include <cstdint>
// CUSTOM bull skill 150. Fixed approved eight-second composition, independent
// of target count. Render-thread only; no battle slots or damage are invented.
namespace bull_effect {
void initialize(std::uintptr_t base);
void preload(void* ui);
void on_result(void* war,unsigned side,unsigned slot);
bool begin_actor(void* war,unsigned side,unsigned slot);
void finish_actor(void* war,unsigned side,unsigned slot);
void before_frame(void* war);
bool has_tail(void* war);
unsigned elapsed_ms(void* war);
void reset(void* war);
void reset_display(void* display);
void begin_battle_draw(void* renderer);
void end_battle_draw();
void draw_ground(void* display,unsigned viewport);
void draw_foreground(void* display,unsigned viewport);
const void* damage_source(void* display,unsigned viewport);
unsigned recording_damage(); // Explicit isolated recording configuration, else zero.
}

namespace bull_effect { void before_present(void* renderer); void before_screen_present(void* screen); void after_present(); }
namespace bull_effect { void before_renderer_present(void* renderer); }
