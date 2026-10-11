#include "cn/protocol/CnAccountReplies.h"
#include <stdexcept>

namespace god2cn {
Bytes CnAccountReplies::failure(CnAccountFailure reason) {
    switch(reason) {
    case CnAccountFailure::NotRegistered:case CnAccountFailure::AlreadyLoggedIn:
    case CnAccountFailure::Disabled:case CnAccountFailure::CredentialRejected:
    case CnAccountFailure::NetworkDisconnected:case CnAccountFailure::InvalidCharacter:
    case CnAccountFailure::VersionMismatch:case CnAccountFailure::BillingRestricted:
    case CnAccountFailure::ServerFull:case CnAccountFailure::NoServerOpen:
    case CnAccountFailure::PasswordMaintenance:case CnAccountFailure::CharacterNameTaken:
    case CnAccountFailure::TelephoneLock:case CnAccountFailure::ServerMaintenance:
    case CnAccountFailure::ExternalAuthenticationRejected:case CnAccountFailure::RealNameRequired:
        return {0x1e,static_cast<std::uint8_t>(reason)};
    }
    throw std::invalid_argument("Unrecovered CN account error code");
}
Bytes CnAccountReplies::group(const Group& value) {
    // 0047FE30 bounds the group index at 64; 00443FA0 consumes its billing
    // type and enable bits. The catalog must additionally validate real slots.
    if(value.index>=64 || value.billing_type>8)
        throw std::invalid_argument("CN group native field bounds");
    return {0x04,value.index,value.billing_type,
        static_cast<std::uint8_t>(value.enabled_servers),
        static_cast<std::uint8_t>(value.enabled_servers>>8)};
}
Bytes CnAccountReplies::node(const Node& value) {
    // 0047FE30 copies 8 bytes into server+0xC4. 0047C830 consumes IPv4
    // at +0xC6..C9 and LE port at +0xCA. No host/system codepage involved.
    if(value.server_index>=10 || !value.port)
        throw std::invalid_argument("CN node native field bounds");
    return {0x05,value.server_index,value.load,
        value.ipv4[0],value.ipv4[1],value.ipv4[2],value.ipv4[3],
        static_cast<std::uint8_t>(value.port),static_cast<std::uint8_t>(value.port>>8)};
}
Bytes CnAccountReplies::location(const Location& value) {
    return {0x06,value.raw[0],value.raw[1],value.raw[2],value.raw[3]};
}
std::vector<Bytes> CnAccountReplies::catalog(std::span<const CatalogGroup> groups) {
    // Evidence: cn-account-catalog-layout-01. 0047C830/0047D1C0 scan
    // ten nodes, each ten four-byte locations, with node stride30h.
    // The consumer does not guard these writes; these are server serialization
    // bounds, not invented gameplay eligibility or native authority rules.
    if(groups.size()>64)throw std::invalid_argument("CN catalog group capacity");
    std::array<bool,64> seen{};
    std::vector<Bytes> frames;
    const auto append=[&frames](Bytes record) {
        if(frames.empty() || frames.back().size()+record.size()>CnTransport::max_logical)
            frames.emplace_back();
        frames.back().insert(frames.back().end(),record.begin(),record.end());
    };
    for(const auto& entry:groups) {
        if(entry.header.index>=seen.size() || seen[entry.header.index] ||
           entry.configured_server_slots>10 ||
           entry.nodes.size()>10)
            throw std::invalid_argument("CN catalog group/order capacity");
        seen[entry.header.index]=true;
        append(group(entry.header));
        // Do not sort or reset the ordinal when server_index changes. Native
        // ordinal advances for EVERY05 since04. Missing slots stay zero after
        // the client's pre-login clear; no synthetic padding05 is emitted.
        for(const auto& value:entry.nodes) {
            if(value.endpoint.server_index>=entry.configured_server_slots || value.locations.size()>10)
                throw std::invalid_argument("CN catalog node/location capacity");
            append(node(value.endpoint));
            for(const auto& row:value.locations)append(location(row));
        }
    }
    return frames;
}
}
