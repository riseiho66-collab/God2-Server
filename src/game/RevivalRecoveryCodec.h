#pragma once
#include "game/RevivalRecovery.h"
#include "game/BattleCheckpointCodec.h"
#include <nlohmann/json.hpp>
#include <string_view>

namespace god2 {
// CUSTOM-0017: canonical server recovery document, not a client packet.
struct RevivalRecoveryCodec {
    using State=RevivalRecovery;
    static std::string encode(const State& value) {
        const auto& snapshot=value.battle.snapshot;
        if(value.version!=1 || !value.account || !value.character ||
           snapshot.state!=BattleState::Active || !snapshot.actors[0] ||
           snapshot.actors[0]->controller!=value.character ||
           (value.control_received && !value.action_received) ||
           (value.opening_received && (!value.opening_notice || !value.initial_control_received)))
            throw std::invalid_argument("Invalid revival recovery state");
        return nlohmann::json{{"version",value.version},{"design_id","CUSTOM-0017"},
            {"account",value.account},{"character",value.character},
            {"battle",BattleCheckpointCodec::encode(value.battle)},
            {"initial",value.initial_control_received},{"opening",value.opening_received},
            {"action",value.action_received},{"control",value.control_received},
            {"opening_notice",value.opening_notice}}.dump();
    }
    static State decode(std::string_view text) {
        if(text.empty() || text.size()>65536) throw std::invalid_argument("Revival recovery size limit");
        const auto data=nlohmann::json::parse(text,[](int depth,nlohmann::json::parse_event_t,nlohmann::json&) {
            if(depth>2) throw std::invalid_argument("Revival recovery nesting limit");
            return true;
        });
        if(!data.is_object() || data.size()!=10 || data.at("design_id")!="CUSTOM-0017" ||
           !data.at("version").is_number_unsigned() || data.at("version")!=1 ||
           !data.at("account").is_number_unsigned() || !data.at("character").is_number_unsigned() ||
           !data.at("battle").is_string())
            throw std::invalid_argument("Revival recovery schema mismatch");
        for(const auto* key:{"initial","opening","action","control","opening_notice"})
            if(!data.at(key).is_boolean()) throw std::invalid_argument("Revival recovery requires boolean phase");
        State value{1,data.at("account").get<std::uint64_t>(),data.at("character").get<std::uint64_t>(),
            BattleCheckpointCodec::decode(data.at("battle").get<std::string>()),
            data.at("initial").get<bool>(),data.at("opening").get<bool>(),
            data.at("action").get<bool>(),data.at("control").get<bool>(),data.at("opening_notice").get<bool>()};
        if(encode(value)!=text) throw std::invalid_argument("Noncanonical revival recovery document");
        return value;
    }
};
}
