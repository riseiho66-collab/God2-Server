#pragma once
// Protocol-contract/mock-cache artifact ONLY. No SQL, network, runtime actions,
// native business-rule recovery, or storage permission is provided here.
#include "protocol/RecoveredGuildLeave.h"
#include "protocol/RecoveredGuildLeadership.h"
#include "protocol/RecoveredGuildRoster.h"
#include <array>
#include <set>
#include <vector>

namespace god2::founder_transfer_contract_draft {
using Wire73=RecoveredGuildLeave; // exact immutable existing two-byte parser
enum class Intent {Denied,OrdinarySelfLeave,OfficerSelfLeave,Transfer};
enum class Denial {None,MissingPublication,InvalidPanel,MissingLocalSlot,RoleOrTargetDenied};
struct Row {
    std::uint8_t local_slot{},role{},account_slot{};
    std::uint64_t account{},character{},join_revision{};
    bool pending{};
    bool operator==(const Row&) const=default;
};
struct Publication {
    std::uint64_t serial{},guild{},guild_revision{},world_generation{},actor_account{},actor_character{};
    bool explicit_single_use_authority{};
    std::vector<Row> rows; // complete recipient-local panel, self == slot0
    bool operator==(const Publication&) const=default;
};
struct IndexedLogical {std::size_t index{};std::vector<std::uint8_t> logical;};
struct Capture {
    std::size_t record_index{};
    std::uint8_t local_slot{};
    Intent intent=Intent::Denied;
    Denial denial=Denial::None;
    std::optional<Row> selected;
    std::optional<Publication> before_prefix;
    bool current(const std::optional<Publication>& now) const {
        return intent!=Intent::Denied && before_prefix && now==before_prefix;
    }
    // Intent/panel display is never DB authority. Role2 transfer eligibility
    // remains OPEN; the first storage-policy proposal restricts target role1.
    constexpr bool authorizes_storage() const noexcept {return false;}
};
struct CapturedBatch {bool structurally_valid{};std::vector<Capture> actions;};

inline bool valid_panel(const Publication& p) {
    if(!p.serial || !p.guild || !p.guild_revision || !p.world_generation || !p.actor_account ||
       !p.actor_character || !p.explicit_single_use_authority || p.rows.empty() || p.rows.size()>50)return false;
    std::set<std::uint64_t> characters;std::set<std::pair<std::uint64_t,std::uint8_t>> account_slots;
    for(std::size_t i=0;i<p.rows.size();++i) {
        const auto& r=p.rows[i];
        if(r.local_slot!=i || r.role>3 || !r.account || !r.character || r.account_slot>1 ||
           !characters.insert(r.character).second || !account_slots.emplace(r.account,r.account_slot).second)return false;
        if(r.pending) {if(r.role!=0 || r.join_revision)return false;}
        else if(!r.role || !r.join_revision || r.join_revision>p.guild_revision)return false;
    }
    const auto& self=p.rows.front();
    return !self.pending && self.account==p.actor_account && self.character==p.actor_character;
}
inline Capture classify(std::size_t index,const Wire73::Request& wire,const std::optional<Publication>& original) {
    Capture out{index,wire.slot,Intent::Denied,Denial::None,{},original};
    if(!original) {out.denial=Denial::MissingPublication;return out;}
    if(!valid_panel(*original)) {out.denial=Denial::InvalidPanel;return out;}
    if(wire.slot>=original->rows.size()) {out.denial=Denial::MissingLocalSlot;return out;}
    const auto& self=original->rows.front();const auto& target=original->rows[wire.slot];out.selected=target;
    if(wire.slot==0 && self.role==1)out.intent=Intent::OrdinarySelfLeave;
    else if(wire.slot==0 && self.role==2)out.intent=Intent::OfficerSelfLeave;
    else if(self.role==3 && wire.slot!=0 && !target.pending && (target.role==1 || target.role==2))out.intent=Intent::Transfer;
    else out.denial=Denial::RoleOrTargetDenied;
    // Pendingrole0/targetrole3 denials are CUSTOM DTO eligibility constraints.
    // Native004EF710/790 only prove selfrole3 + selected nonself local row;
    // do not claim the producer itself checks the selected target's role.
    return out;
}
inline CapturedBatch capture_checked_before_prefix(std::span<const IndexedLogical> logical73,
    const std::optional<Publication>& published_before_any_prefix) {
    // No callbacks/prefix/SQL/network. All structural requests validate BEFORE
    // any intents are returned. Neither a refreshed slot nor future panel open
    // can classify a request differently; caller must keep this original value.
    std::vector<Wire73::Request> decoded;decoded.reserve(logical73.size());
    std::size_t previous=0;bool first=true;
    for(const auto& item:logical73) {
        if(!first && item.index<=previous)return {};
        first=false;previous=item.index;const auto wire=Wire73::decode(item.logical);
        if(!wire)return {};decoded.push_back(*wire);
    }
    CapturedBatch out{true,{}};out.actions.reserve(decoded.size());
    for(std::size_t i=0;i<decoded.size();++i)
        out.actions.push_back(classify(logical73[i].index,decoded[i],published_before_any_prefix));
    return out;
}

// Mock consumer of the existing client record layout. Not the client's real
// renderer, UI controls, packet processor, or a native acceptance substitute.
class ConsumerContract {
    std::array<std::optional<std::array<std::uint8_t,21>>,50> rows_{};
    std::uint8_t self_slot_{};std::optional<std::uint8_t> self_role_;
public:
    explicit ConsumerContract(std::uint8_t self_slot=0):self_slot_(self_slot) {
        if(self_slot>=50)throw std::invalid_argument("mock self slot");
    }
    bool seed91(std::span<const std::uint8_t> logical) {
        if(logical.size()!=22 || logical[0]!=0x91 || logical[1]>=50 || logical[2]>3)return false;
        std::array<std::uint8_t,21> raw{};std::copy(logical.begin()+1,logical.end(),raw.begin());rows_[logical[1]]=raw;
        if(logical[1]==self_slot_)self_role_=logical[2];return true;
    }
    bool consume93(std::span<const std::uint8_t> logical) {
        const auto r=RecoveredGuildLeadership::decode_role_update(logical);
        if(!r || !rows_[r->slot])return false;
        (*rows_[r->slot])[1]=r->role;if(r->slot==self_slot_)self_role_=r->role;return true;
    }
    std::optional<std::uint8_t> role(std::uint8_t slot) const {
        return slot<50 && rows_[slot]?std::optional{(*rows_[slot])[1]}:std::nullopt;
    }
    std::size_t count() const {return std::count_if(rows_.begin(),rows_.end(),[](const auto& r){return bool(r);});}
    std::optional<std::uint8_t> self_role() const {return self_role_;}
};
inline std::optional<std::vector<std::array<std::uint8_t,3>>> role_projection_for_recipient(
    const Publication& recipient,std::uint64_t former_owner,std::uint64_t new_owner) {
    if(!valid_panel(recipient) || !former_owner || former_owner==new_owner)return {};
    std::optional<std::uint8_t> former,newer;
    for(const auto& row:recipient.rows) {
        if(row.pending)continue;
        if(row.character==former_owner)former=row.local_slot;
        if(row.character==new_owner)newer=row.local_slot;
    }
    if(!former || !newer)return {};
    return std::vector{RecoveredGuildLeadership::role_update(*former,1),RecoveredGuildLeadership::role_update(*newer,3)};
}
}
