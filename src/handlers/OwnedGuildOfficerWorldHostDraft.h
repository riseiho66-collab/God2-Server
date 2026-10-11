#pragma once
#include "handlers/OwnedGuildOfficerService.h"
#include <functional>

namespace god2 {
// Trusted Application host adapter, not client input. Enumerate must include
// EVERY lockable native_chat_sessions entry, including duplicate characters.
// Resolve=guild_world_owner. PeerReady=private_chat_peer exact id/ready check.
class OwnedGuildOfficerWorldHostDraft {
public:
    using Panel=OwnedGuildLeaderPanelService;using Service=OwnedGuildOfficerServiceDraft;
    struct Live {std::uint64_t session{},account{},character{};bool permitted_state{};};
    using Enumerate=std::function<std::vector<Live>()>;
    using PeerReady=std::function<bool(const Panel::Owner&)>;
    OwnedGuildOfficerWorldHostDraft(Enumerate enumerate,Panel::Resolve resolve,PeerReady peer_ready):
        enumerate_(std::move(enumerate)),resolve_(std::move(resolve)),peer_ready_(std::move(peer_ready)){}
    std::optional<Service::WorldLease> capture(const Panel::State& state) const {
        const auto lease=read(state);if(!lease || !preflight(state,*lease))return {};return lease;
    }
    bool preflight(const Panel::State& state,const Service::WorldLease& lease) const {
        // BEFORE prefix and AGAIN BEFORE SQL only. Never put SQL peer/profile/
        // resources access into the paired after-delete repository proof.
        if(!current(state,lease) || !peer_ready_)return false;
        try {for(const auto& owner:lease.connected)if(!peer_ready_(owner))return false;
            return current(state,lease);}catch(...){return false;}
    }
    bool current(const Panel::State& state,const Service::WorldLease& lease) const {
        // WORLD ONLY: re-enumerating detects new or missing duplicate sessions.
        // No membership/governance/history/profile/resources/private_chat_peer.
        const auto fresh=read(state);return fresh && *fresh==lease;
    }
private:
    std::optional<Service::WorldLease> read(const Panel::State& state) const {
        try {
            if(!enumerate_ || !resolve_)return {};Service::WorldLease lease;
            auto live=enumerate_();std::sort(live.begin(),live.end(),[](const auto& a,const auto& b){return a.session<b.session;});
            std::uint64_t previous=0;
            for(const auto& entry:live) {
                if(!entry.session || entry.session<=previous)return {};previous=entry.session;
                const auto row=std::find_if(state.rows.begin(),state.rows.end(),[&](const auto& r){
                    return r.identity.character_id==entry.character;});
                if(row==state.rows.end())continue;
                // Pending app identities are historical; compare owned IDs,
                // not current names/levels/profile against the saved snapshot.
                if(!entry.permitted_state || entry.account!=row->identity.account_id)return {};
                const auto owner=resolve_(entry.session);
                if(!owner || owner->session!=entry.session || owner->account!=entry.account || owner->character!=entry.character)return {};
                lease.connected.push_back(*owner);
            }
            return lease;
        }catch(...){return {};}
    }
    Enumerate enumerate_;Panel::Resolve resolve_;PeerReady peer_ready_;
};
}
