#pragma once
#include "cn/protocol/CnAccountReplies.h"
#include <optional>

namespace god2cn {
// Exact native endpoint choice for an already qualified ordered catalog.
// 0047FAA0 ->0047D1C0 uses a07 row's nonzero routing key; if not found,
// it calls0047C830 and takes the first node with any nonzero06 location key.
// This does not change07's bytes, invent location metadata or authorize entry.
struct CnCatalogRoute {
    struct Endpoint {
        CnAccountReplies::Node endpoint;
        std::size_t group_node_ordinal;
        std::size_t location_ordinal;
        bool used_fallback;
    };
    static std::optional<Endpoint> resolve(
        const CnAccountReplies::CatalogGroup& group,std::uint16_t server,
        std::uint8_t routing_key) {
        if(group.nodes.size()>10 || server>=group.configured_server_slots || server>=10)return std::nullopt;
        std::optional<Endpoint> fallback;
        for(std::size_t index=0;index<group.nodes.size();++index) {
            const auto& node=group.nodes[index];
            if(node.locations.size()>10)return std::nullopt;
            if(node.endpoint.server_index!=server)continue;
            for(std::size_t location=0;location<node.locations.size();++location) {
                const auto key=node.locations[location].raw[0];
                if(!key)continue;
                if(!fallback)fallback=Endpoint{node.endpoint,index,location,true};
                if(routing_key && key==routing_key)
                    return Endpoint{node.endpoint,index,location,false};
            }
        }
        return fallback;
    }
};
}
