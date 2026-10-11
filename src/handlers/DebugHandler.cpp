#include "handlers/DebugHandler.h"
#include "protocol/OpcodeDispatcher.h"
namespace god2 {
void register_debug_handlers(OpcodeDispatcher&) {
    // Unknown opcode diagnostics live in the dispatcher. No unauthenticated GM opcode.
}
}
