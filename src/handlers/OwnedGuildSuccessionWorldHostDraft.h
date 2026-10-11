#pragma once
// PRIVATE CUSTOM-0083. Trusted executor adapter; no native acceptance claimed.
#include "handlers/OwnedGuildSuccessionServiceDraft.h"

namespace god2 {
class OwnedGuildSuccessionWorldHostDraft {
public:
    using Service=OwnedGuildSuccessionServiceDraft;
    using Owner=Service::Owner;
    struct Live {std::uint64_t session{},account{},character{};bool permitted_state{};};
    // Enumerate EVERY lockable session, including duplicate characters.
    using Enumerate=std::function<std::vector<Live>()>;
    using PeerReady=std::function<bool(const Owner&)>;
    OwnedGuildSuccessionWorldHostDraft(SqliteRecoveredCharacterRepository& profiles,
        Enumerate enumerate,Service::Resolve resolve,PeerReady ready):profiles_(profiles),
        enumerate_(std::move(enumerate)),resolve_(std::move(resolve)),ready_(std::move(ready)){}

    std::optional<Service::Audience> capture(const Service::Repo::EffectiveLeader& leader,
        const std::vector<Service::Original::Application>& applications) const {
        try {
            Service::Audience result;std::map<std::uint64_t,std::uint64_t> identities;
            const auto add=[&](const auto& row){
                if(!row.account_id || !row.character_id || !identities.emplace(row.character_id,row.account_id).second)
                    throw DatabaseError("Succession audience duplicate/missing owned identity");
                const auto resources=profiles_.load_resources(row.account_id,row.character_id);
                if(!resources || !resources->revision || !resources->max_hp || resources->hp>resources->max_hp ||
                    resources->mp>resources->max_mp || resources->design_id.empty())
                    throw DatabaseError("Succession complete audience resources absent");
                result.resources.emplace(row.character_id,*resources);
            };
            for(const auto& member:leader.roster)add(member);
            for(const auto& application:applications)add(application.applicant);
            const auto live=read(result);if(!live)return {};
            for(const auto& owner:*live)if(identities.at(owner.character)!=owner.account)return {};
            result.connected=*live;
            return preflight(result)?std::optional{result}:std::nullopt;
        }catch(...){return {};}
    }
    std::optional<Service::Audience> capture_membership(const Service::Repo::EffectiveLeader& leader,
        const std::vector<Service::Original::Application>& applications,const Service::Original::Identity& actor) const {
        try {
            Service::Audience result;std::map<std::uint64_t,std::uint64_t> identities;
            const auto add=[&](const auto& row){
                if(!row.account_id || !row.character_id || !identities.emplace(row.character_id,row.account_id).second)
                    throw DatabaseError("Succession audience duplicate/missing owned identity");
                const auto resources=profiles_.load_resources(row.account_id,row.character_id);
                if(!resources || !resources->revision || !resources->max_hp || resources->hp>resources->max_hp ||
                    resources->mp>resources->max_mp || resources->design_id.empty())
                    throw DatabaseError("Succession complete audience resources absent");
                result.resources.emplace(row.character_id,*resources);
            };
            for(const auto& member:leader.roster)add(member);
            for(const auto& application:applications)add(application.applicant);
            if(!identities.contains(actor.character_id))add(actor);else if(identities.at(actor.character_id)!=actor.account_id)return {};
            const auto live=read(result);if(!live)return {};
            for(const auto& owner:*live)if(identities.at(owner.character)!=owner.account)return {};
            result.connected=*live;
            return preflight(result)?std::optional{result}:std::nullopt;
        }catch(...){return {};}
    }
    std::optional<Service::Audience> capture_nonmember(const Service::Original::Identity& actor)const{
        try{Service::Audience audience;const auto resource=profiles_.load_resources(actor.account_id,actor.character_id);if(!resource)return {};audience.resources.emplace(actor.character_id,*resource);
            const auto live=read(audience);if(!live)return {};for(const auto& owner:*live)if(owner.account!=actor.account_id || owner.character!=actor.character_id)return {};audience.connected=*live;
            return preflight(audience)?std::optional{audience}:std::nullopt;
        }catch(...){return {};}
    }
    // BEFORE prefix and BEFORE SQL only: ready_ may query peer projections.
    bool preflight(const Service::Audience& audience) const {
        try {
            if(!ready_ || !current(audience))return false;
            for(const auto& owner:audience.connected)if(!ready_(owner))return false;
            return current(audience);
        }catch(...){return false;}
    }
    // WORLD ONLY. Safe for paired repository after-write evidence; no SQL,
    // membership/profile/resources reads or peer-projection callback.
    bool current(const Service::Audience& audience) const {
        const auto live=read(audience);return live && *live==audience.connected;
    }
private:
    std::optional<std::vector<Owner>> read(const Service::Audience& audience) const {
        try {
            if(!enumerate_ || !resolve_ || audience.resources.empty())return {};
            auto live=enumerate_();std::sort(live.begin(),live.end(),[](const auto& a,const auto& b){return a.session<b.session;});
            std::vector<Owner> result;std::uint64_t previous=0;
            for(const auto& item:live) {
                if(!item.session || item.session<=previous)return {};previous=item.session;
                if(!audience.resources.contains(item.character))continue;
                if(!item.permitted_state || !item.account)return {};
                const auto owner=resolve_(item.session);
                if(!owner || owner->session!=item.session || owner->account!=item.account || owner->character!=item.character ||
                    !owner->world_generation || !owner->position_revision ||
                    (owner->name_codepage!=950 && owner->name_codepage!=936))return {};
                result.push_back(*owner);
            }
            return result;
        }catch(...){return {};}
    }
    SqliteRecoveredCharacterRepository& profiles_;Enumerate enumerate_;Service::Resolve resolve_;PeerReady ready_;
};
}
