#pragma once
#include "net/Session.h"
#include <functional>
#include <optional>

namespace god2 {
// CUSTOM-0159 GAME-owned exports stored INSIDE the held gameplay frame.
// The process host borrows only after require_held(), destroys its listener/
// facade copies after full NET/GAME drain, then resumes the owning frame.
// These supplied handlers remain real application sources, not native grants.
struct ApplicationGameSources final {
    Session::PacketHandler packet;
    Session::DisconnectHandler disconnected;
    Session::RecoveredLoginHandler authenticate;
    Session::RecoveredCharacterHandlers account;
    std::optional<Session::RecoveredCharacterHandlers> character;
    std::function<void()> start;
    std::function<void()> retire;
    // Called on GAME at host-scope exit, after normal drain or explicit abort.
    // Empties transport holders before listener copies can outlive dependencies.
    std::function<void()> revoke_transport;
};
}
