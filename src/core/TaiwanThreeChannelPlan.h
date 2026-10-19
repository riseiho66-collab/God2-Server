#pragma once
#include "core/SharedWorldHostPlan.h"
#include "game/SharedTaiwanCharacterListHandoff.h"
#include "net/TaiwanChannelServers.h"
#include <array>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <span>
#include <vector>
#include <stdexcept>
#include <functional>
#include <memory>
#include <string>
#include <utility>

namespace god2 {
class SqliteDatabase;
// CUSTOM-0159 explicit complete native three-world Application recipe.
// Main/default CLI does not manufacture missing native sources or permissions.
struct TaiwanThreeChannelPlan final {
    struct Context {
        SqliteDatabase& database;
        asio::any_io_executor game;
        const SharedTaiwanChannelWorlds& worlds;
        std::shared_ptr<SharedTaiwanCharacterListHandoff> handoff;
    };
    // Invoked once on GAME. Return three fresh native plans, each of which
    // constructs its own Owner from its exact later world Context. Use this
    // one actual handoff with ListSources::with_handoff for all three plans;
    // do not retain Context/borrowed locals or share one cached plan Owner.
    using WorldPlans=std::array<SharedWorldHostPlan,3>;
    using Factory=std::function<WorldPlans(const Context&)>;
    std::shared_ptr<const TaiwanNativeClientGroupConfiguration> configuration;
    std::uint8_t group,group_byte_1;
    std::array<TaiwanChannelServers::EndpointPolicy,3> endpoints;
    std::string client_sha256;
    std::size_t handoff_capacity;
    SharedTaiwanCharacterListHandoff::Live live;
    SharedTaiwanCharacterListHandoff::Authority authority;
    Factory make_world_plans;
    // Explicit same authenticated Session cipher/framing source, mandatory
    // for schema53 Application guild chat. No default lab encoder is selected.
    // Qualify its actual peer/profile; return complete native envelopes only.
    using NativeGuildSenderWire=std::function<std::optional<std::vector<std::uint8_t>>(
        Session&,std::span<const std::uint8_t>)>;
    NativeGuildSenderWire guild_chat_sender_wire={};
    // Guild actions and async bootstrap/name pushes use this actual same-peer source.
    NativeGuildSenderWire guild_action_sender_wire={};
    TaiwanThreeChannelPlan(std::shared_ptr<const TaiwanNativeClientGroupConfiguration> configured,
        std::uint8_t actual_group,std::uint8_t byte_1,
        std::array<TaiwanChannelServers::EndpointPolicy,3> actual_endpoints,
        std::string actual_client,std::size_t capacity,
        SharedTaiwanCharacterListHandoff::Live actual_live,
        SharedTaiwanCharacterListHandoff::Authority actual_authority,Factory factory)
        :configuration(std::move(configured)),group(actual_group),group_byte_1(byte_1),
         endpoints(actual_endpoints),client_sha256(std::move(actual_client)),handoff_capacity(capacity),
         live(std::move(actual_live)),authority(std::move(actual_authority)),make_world_plans(std::move(factory)) {
        validate();
    }
    void validate() const {
        if(!configuration||group>=10||configuration->configured_slots(group)!=std::optional<std::uint8_t>{3}||
           !handoff_capacity||!live||!authority||!make_world_plans||client_sha256.size()!=64||
           client_sha256.find_first_not_of("0123456789abcdef")!=std::string::npos)
            throw std::invalid_argument("Three-channel host requires actual three slots, full native handoff sources and fresh world-plan factory");
        for(std::size_t k=0;k<3;++k) {
            if(endpoints[k].address[0]!=127||!endpoints[k].route_body[0])
                throw std::invalid_argument("Three-channel host requires explicit loopback native routing material");
            for(std::size_t j=0;j<k;++j)
                if(endpoints[k].port&&endpoints[k].port==endpoints[j].port&&endpoints[k].address==endpoints[j].address)
                    throw std::invalid_argument("Three-channel endpoints cannot alias");
        }
    }
};
}
