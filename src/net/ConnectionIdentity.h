#pragma once
#include <cstdint>

namespace god2 {
// Shared by all protocol listeners, never by client packet fields. IDs are
// process-lifetime unique; exhaustion throws rather than wrapping/reusing.
std::uint64_t next_connection_identity();
}
