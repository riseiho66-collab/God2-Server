#pragma once
// Native battle backdrop is a filename-less CDX surface. Preserve only its
// pixels across device recovery; do not replay battle/map initialization.
namespace battle_background {
void captured(void* renderer);
void before_battle_draw(void* renderer);
void screen_rebuilt(void* screen);
}
