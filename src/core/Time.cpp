#include "core/Time.h"
#include <chrono>
namespace god2 { std::uint32_t unix_seconds() { return static_cast<std::uint32_t>(std::chrono::duration_cast<std::chrono::seconds>(std::chrono::system_clock::now().time_since_epoch()).count()); } }
