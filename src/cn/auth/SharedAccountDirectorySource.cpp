#include "cn/auth/SharedAccountDirectorySource.h"
#include <algorithm>
#include <map>
#include <set>
#include <utility>

namespace god2::cn {
namespace {
using Key=std::pair<std::uint16_t,std::uint16_t>;
using Bound=std::map<Key,asio::ip::tcp::endpoint>;
std::optional<Bound> world_endpoints(const SharedListenerRegistry::Snapshot& snapshot) {
    if(!snapshot.current())return std::nullopt;
    Bound result;
    for(const auto& e:snapshot.endpoints()) {
        if(e.role!=SharedListenerRegistry::Role::World)continue;
        // Existing qualified native form: concrete IPv4. Never invent a NAT,
        // wildcard/IPv6 translation, loopback replacement or public address.
        if(!e.target || !e.socket.address().is_v4() || e.socket.address().is_unspecified() ||
           !e.socket.port() || !result.emplace(Key{e.target->group,e.target->server},e.socket).second)
            return std::nullopt;
    }
    if(result.empty() || !snapshot.current())return std::nullopt;
    return result;
}
bool qualified(std::span<const god2cn::CnAccountReplies::CatalogGroup> groups,const Bound& bound,
    const god2cn::CnClientGroupConfiguration& configured) {
    if(groups.empty() || groups.size()>64)return false;
    std::set<std::uint8_t> seen;
    std::set<Key> advertised;
    for(const auto& group:groups) {
        const auto slots=configured.configured_slots(group.header.index);
        if(group.header.index>=64 || group.header.billing_type>8 ||
           !slots || group.configured_server_slots!=*slots ||
           group.configured_server_slots>10 || group.nodes.size()>10 ||
           !seen.insert(group.header.index).second)return false;
        for(const auto& node:group.nodes) {
            if(node.endpoint.server_index>=group.configured_server_slots ||
               node.endpoint.server_index>=10 || !node.endpoint.port || node.locations.size()>10)return false;
            if(!(group.header.enabled_servers&(std::uint16_t{1}<<node.endpoint.server_index)))continue;
            const Key key{group.header.index,node.endpoint.server_index};
            const auto found=bound.find(key);
            if(found==bound.end() || !advertised.insert(key).second ||
               found->second.address().to_v4().to_bytes()!=node.endpoint.ipv4 ||
               found->second.port()!=node.endpoint.port)return false;
        }
    }
    if(advertised.size()!=bound.size())return false;
    for(const auto& row:bound)if(!advertised.contains(row.first))return false;
    return true;
}
struct Cursor {
    std::span<const god2cn::Bytes> frames;
    std::size_t frame=0,offset=0;
    std::optional<std::span<const std::uint8_t>> take(std::size_t count) {
        if(frame<frames.size() && offset==frames[frame].size()){++frame;offset=0;}
        if(frame>=frames.size() || count>frames[frame].size()-offset)return std::nullopt;
        const auto record=std::span<const std::uint8_t>(frames[frame]).subspan(offset,count);
        offset+=count;return record;
    }
    bool done() const {return frame<frames.size() && frame+1==frames.size() && offset==frames[frame].size();}
};
std::uint16_t word16(std::span<const std::uint8_t> bytes,std::size_t offset) {
    return static_cast<std::uint16_t>(bytes[offset]|(std::uint16_t(bytes[offset+1])<<8));
}
}

SharedAccountDirectorySource::Plan::Plan(std::vector<god2cn::CnAccountReplies::CatalogGroup> catalog,
    SharedListenerRegistry::Snapshot listeners,std::shared_ptr<const god2cn::CnClientGroupConfiguration> client_groups)
    :catalog_(std::move(catalog)),listeners_(std::move(listeners)),client_groups_(std::move(client_groups)) {}
std::optional<SharedAccountDirectorySource::Plan> SharedAccountDirectorySource::from_catalog(
    std::span<const god2cn::CnAccountReplies::CatalogGroup> groups,SharedListenerRegistry::Snapshot listeners,
    std::shared_ptr<const god2cn::CnClientGroupConfiguration> client_groups) {
    const auto bound=world_endpoints(listeners);
    if(!bound || !client_groups || !qualified(groups,*bound,*client_groups) || !listeners.current())return std::nullopt;
    return Plan(std::vector<god2cn::CnAccountReplies::CatalogGroup>(groups.begin(),groups.end()),
        std::move(listeners),std::move(client_groups));
}
std::optional<SharedAccountDirectorySource::Plan> SharedAccountDirectorySource::from_source(
    std::span<const Group> groups,SharedListenerRegistry::Snapshot listeners,
    std::shared_ptr<const god2cn::CnClientGroupConfiguration> client_groups) {
    if(!client_groups || groups.empty() || groups.size()>64)return std::nullopt;
    const auto bound=world_endpoints(listeners);
    if(!bound)return std::nullopt;
    std::vector<god2cn::CnAccountReplies::CatalogGroup> catalog;
    catalog.reserve(groups.size());
    for(const auto& group:groups) {
        const auto slots=client_groups->configured_slots(group.header.index);
        if(!slots || group.header.index>=64 || group.header.billing_type>8 || *slots>10 ||
           group.nodes.size()>10)return std::nullopt;
        god2cn::CnAccountReplies::CatalogGroup item{group.header,*slots,{}};
        item.nodes.reserve(group.nodes.size());
        for(const auto& node:group.nodes) {
            if(node.server_index>=*slots || node.locations.size()>10)return std::nullopt;
            const auto found=bound->find(Key{group.header.index,node.server_index});
            if(found==bound->end())return std::nullopt;
            item.nodes.push_back({{node.server_index,node.load,found->second.address().to_v4().to_bytes(),
                found->second.port()},node.locations});
        }
        catalog.push_back(std::move(item));
    }
    if(!qualified(catalog,*bound,*client_groups) || !listeners.current())return std::nullopt;
    return Plan(std::move(catalog),std::move(listeners),std::move(client_groups));
}
bool SharedAccountDirectorySource::Plan::matches(std::span<const god2cn::Bytes> frames) const {
    if(!current() || frames.empty())return false;
    for(const auto& frame:frames)if(frame.empty() || frame.size()>god2cn::CnTransport::max_logical)return false;
    Cursor cursor{frames};
    for(const auto& group:catalog_) {
        auto g=cursor.take(5);
        if(!g || (*g)[0]!=0x04 || (*g)[1]!=group.header.index || (*g)[2]!=group.header.billing_type ||
           word16(*g,3)!=group.header.enabled_servers)return false;
        for(const auto& node:group.nodes) {
            auto n=cursor.take(9);
            if(!n || (*n)[0]!=0x05 || (*n)[1]!=node.endpoint.server_index || (*n)[2]!=node.endpoint.load ||
               !std::equal(node.endpoint.ipv4.begin(),node.endpoint.ipv4.end(),n->begin()+3) ||
               word16(*n,7)!=node.endpoint.port)return false;
            for(const auto& location:node.locations) {
                auto l=cursor.take(5);
                if(!l || (*l)[0]!=0x06 || !std::equal(location.raw.begin(),location.raw.end(),l->begin()+1))return false;
            }
        }
    }
    return cursor.done() && current();
}
}
