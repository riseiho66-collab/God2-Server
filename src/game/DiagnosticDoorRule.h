#pragma once
#include <array>
#include <cstdint>

namespace god2 {
// CUSTOM-0025: trusted committed movement snapshot, never client destination data.
struct DiagnosticDoorInput {
    std::uint32_t area{},scene{},before_x{},before_y{},x{},y{};
    bool allow_island=false;
    bool allow_all_town_doors=false; // CUSTOM-0052: explicitly configured current point bundle.
    bool allow_kunlun_doors=false;
    bool allow_kunlun_parent=false; // CUSTOM-0053 native points/custom activation.
};
struct DiagnosticDoorPlan {
    std::uint32_t area{},scene{},x{},y{};
    bool operator==(const DiagnosticDoorPlan&) const = default;
};

// Current4157F0: lowWORD is the local character identity, not a caller code.
// Current46C4EA loads World+1539683C before queuing the transfer receipt;
// 531C10 supplies the same 0/1 flag accepted in this session's world tail.
// Application additionally requires an owned pending committed transfer.
constexpr bool diagnostic_owned_scene_receipt(std::array<std::uint8_t,4> payload,
                                              std::uint64_t character,
                                              std::uint8_t session_config) {
    return character>0 && character<=0x3fff && session_config<=1 &&
           payload==std::array<std::uint8_t,4>{static_cast<std::uint8_t>(character),
                static_cast<std::uint8_t>(character>>8),session_config,0};
}
constexpr bool diagnostic_door_context_receipt(std::array<std::uint8_t,4> payload,
                                               bool door_routes,
                                               std::uint8_t session_config,
                                               std::uint64_t character) {
    return door_routes && diagnostic_owned_scene_receipt(payload,character,session_config);
}
// CUSTOM-0036: the current client used 4/0 when entering scene 0 from town.
// The caller must also prove an owned, pending transfer saved for scene 0.
constexpr bool diagnostic_island_arrival_receipt(std::array<std::uint8_t,4> payload,
                                                 bool island_routes,std::uint16_t saved_scene,
                                                 std::uint64_t character,std::uint8_t session_config) {
    return island_routes && saved_scene==0 &&
           diagnostic_owned_scene_receipt(payload,character,session_config);
}
// CUSTOM-0036: the reverse transition uses the same observed 4/0 words.
// The caller must prove this session's pending transfer originated in scene 0.
constexpr bool diagnostic_island_return_receipt(std::array<std::uint8_t,4> payload,
                                                bool island_return_pending,
                                                std::uint16_t saved_scene,
                                                std::uint64_t character,std::uint8_t session_config) {
    return island_return_pending && saved_scene==4 &&
           diagnostic_owned_scene_receipt(payload,character,session_config);
}
}
