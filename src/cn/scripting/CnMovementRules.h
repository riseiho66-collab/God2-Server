#pragma once
#include "cn/protocol/CnMovement.h"
#include "cn/world/CnMapPassability.h"
#include <filesystem>
#include <memory>
#include <thread>

namespace god2cn {
struct CnPreparedStep {
    CnMovement::Point destination;
    std::uint8_t client_ring_index;
    std::uint8_t direction;
};
struct CnMapPreparedStep {
    CnPreparedStep step;
    std::uint8_t native_cell; // Preserve value2 and all other raw native values.
};
// Pure native geometry preparation. Session ownership, current map, collision,
// speed, pending sequence, persistence and replies belong to later segments.
class CnMovementRules {
public:
    explicit CnMovementRules(const std::filesystem::path& script);
    ~CnMovementRules();
    CnMovementRules(const CnMovementRules&)=delete;
    CnMovementRules& operator=(const CnMovementRules&)=delete;
    // Origin/direction must come from connection-owned actor state. Neither
    // the request's ring index nor its opaque byte can select another actor.
    std::optional<CnPreparedStep> prepare_native_step(std::span<const std::uint8_t> record,
        CnMovement::Point origin,std::uint8_t previous_direction);
    // Caller must obtain this complete map snapshot from the actor's actual
    // map/revision. This adds the recovered client neighbor filter, not server
    // permission, path search, speed validation, position commit or an ack.
    std::optional<CnMapPreparedStep> prepare_native_map_step(
        std::span<const std::uint8_t> record, CnMovement::Point origin,
        std::uint8_t previous_direction, const CnMapPassability& map);
private:
    struct Vm;
    std::unique_ptr<Vm> vm_;
    std::thread::id thread_=std::this_thread::get_id();
};
}
