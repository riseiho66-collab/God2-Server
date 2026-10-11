#pragma once
#include <cstdint>
namespace bull_native_tick {
using Original=unsigned(__thiscall*)(void*,void*);
void initialize(std::uintptr_t image_base);
unsigned step(void* war,void* actor,Original original);
void reset(void* war);
}
