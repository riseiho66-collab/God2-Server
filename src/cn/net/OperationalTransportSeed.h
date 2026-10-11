#pragma once
#include "cn/net/SharedCredentialServer.h"

namespace god2::cn {
// Own-server operational policy, NOT recovered official-server randomness.
// The pinned client consumes16 literal seed bytes; no gameplay or entitlement
// rule is supplied by choosing how our server obtains those transport bytes.
enum class OperationalTransportSeedPolicy { WindowsSystemCngV1 };

// Explicit opt-in only. Construct/call on the same serial Application game
// owner. Copies actual listener identities; each callback copy shares the
// one-shot connection-ID gate. No seed cache, retry, fixed seed or RNG fallback.
// Unsupported platforms/policies or unqualified endpoints reject construction;
// an unsuccessful CNG call returns nullopt and the listener closes that socket.
SharedServerPlan::Controllers::Seed make_operational_transport_seed_source(
    OperationalTransportSeedPolicy,std::vector<SharedServerPlan::Endpoint>);
}
