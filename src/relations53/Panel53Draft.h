#pragma once
// PRIVATE CUSTOM-0083. Not an Application or formal database integration.
#include "Succession53ReaderDraft.h"
#include "protocol/NativeGuildTransferContractDraft.h"
#include "handlers/OwnedGuildMembershipConversation.h"
#include "db/SqliteRecoveredCharacterRepository.h"
#include "db/DbTypes.h"
#include "protocol/OwnedGuildPanelHeader.h"
#include "text/LegacyChineseCodec.h"
#include <map>
#include <limits>

namespace god2 {
class Panel53Draft {
public:
    using Repo=Succession53ReaderDraft;
    using Original=Repo::Original;
    using Owner=OwnedGuildMembershipConversation::Owner;
    using Contract=founder_transfer_contract_draft::Publication;
    struct Audience {
        std::vector<Owner> connected; // Every connected session, including duplicates.
        std::map<std::uint64_t,CharacterResources> resources; // ALL accepted + pending, offline too.
        bool operator==(const Audience&) const=default;
    };
    struct State {
        Owner recipient;
        Repo::EffectiveLeader leader;
        std::vector<Original::Application> applications;
        std::vector<Original::Identity> rows; // Exact self0; accepted then pending.
        Audience audience;
        bool operator==(const State&) const=default;
    };
    struct Publication {State state;Contract contract;bool operator==(const Publication&) const=default;};
    struct CacheEvidence {Publication previous;bool consumed{};std::uint64_t epoch{};bool operator==(const CacheEvidence&) const=default;};
    struct Projection {State state;std::vector<std::uint8_t> logical;bool explicit_help{};std::optional<CacheEvidence> previous;bool operator==(const Projection&) const=default;};
    // Complete emitted91 namespace certificate, including accepted AND pending.
    // Native551DE0 folds ASCII bytes, including legacy multibyte trail bytes.
    struct CanonicalScope {
        Owner recipient;std::uint64_t guild{};std::string self_name,primary_name;
        std::vector<std::string> folded_names;bool serialized_self_matches{};
        bool operator==(const CanonicalScope&) const=default;
    };
    static std::string native_name_fold(std::string bytes){
        for(auto& c:bytes)if(static_cast<unsigned char>(c)>='A' && static_cast<unsigned char>(c)<='Z')c=static_cast<char>(c+32);return bytes;
    }
    static std::optional<CanonicalScope> canonical_scope(const State& state){
        try{
            if(state.rows.empty() || state.rows.size()>50 || !state.leader.guild.id ||
                (state.recipient.name_codepage!=950 && state.recipient.name_codepage!=936))return {};
            const auto& first=state.rows.front();if(first.account_id!=state.recipient.account || first.character_id!=state.recipient.character)return {};
            CanonicalScope scope{state.recipient,state.leader.guild.id,{},{},{},false};
            std::set<std::string> names;std::set<std::uint64_t> characters;std::set<std::pair<std::uint64_t,std::uint8_t>> slots;
            for(const auto& row:state.rows){
                if(!row.character_id || !row.account_id || !characters.insert(row.character_id).second || !slots.emplace(row.account_id,row.slot).second)return {};
                const auto encoded=LegacyChineseCodec::encode(row.name_utf8,state.recipient.name_codepage==936);
                if(encoded.empty() || encoded.size()>15 || LegacyChineseCodec::decode(encoded,state.recipient.name_codepage==936)!=row.name_utf8 ||
                    std::any_of(encoded.begin(),encoded.end(),[](char c){const auto b=static_cast<unsigned char>(c);return b<0x20 || b==0x7f || b=='%';}))return {};
                const auto folded=native_name_fold(encoded);if(!names.insert(folded).second)return {};
                scope.folded_names.push_back(folded);if(scope.folded_names.size()==1)scope.self_name=encoded;
            }
            scope.primary_name.assign(first.name_bytes.begin(),first.name_bytes.end());
            scope.serialized_self_matches=!scope.primary_name.empty() && scope.primary_name.size()<=14 &&
                std::equal(first.name_bytes.begin(),first.name_bytes.end(),first.profile.begin()) &&
                first.profile[first.name_bytes.size()]==0 && scope.self_name==scope.primary_name;
            return scope;
        }catch(...){return {};}
    }
    static bool same_native_namespace(const Owner& a,const Owner& b){
        // Native91/92 row identity is independent of position x/y/revision.
        // Authorization/world CAS STILL uses exact whole Owner everywhere else.
        return a.session==b.session && a.account==b.account && a.character==b.character &&
            a.world_generation==b.world_generation && a.area==b.area && a.scene==b.scene &&
            a.name_codepage==b.name_codepage && a.battle_generation==b.battle_generation;
    }
    static bool same_native_self(const CanonicalScope& a,const CanonicalScope& b){
        return a.serialized_self_matches && b.serialized_self_matches && same_native_namespace(a.recipient,b.recipient) && a.guild==b.guild && a.self_name==b.self_name && a.primary_name==b.primary_name;
    }
    struct Plan {Publication publication;std::uint8_t slot{};Original::Identity target;StoredGuildMembership membership;bool operator==(const Plan&) const=default;};
    struct ClearPlan {CacheEvidence previous;Owner recipient;std::vector<std::uint8_t> logical;bool operator==(const ClearPlan&) const=default;};
    using Resolve=std::function<std::optional<Owner>(std::uint64_t)>;
    using Capture=std::function<std::optional<Audience>(const Repo::EffectiveLeader&,const std::vector<Original::Application>&)>;
    // MUST be pure world/executor evidence; no current governance/panel SQL reads.
    // Full exact connected enumeration + readiness + peer/resource projection.
    using WorldCurrent=std::function<bool(const Audience&)>;
    using RecipientReady=std::function<bool(const Owner&)>; // Exact accepted world tail, pure.
    using ConnectionClosed=std::function<bool(const Owner&)>; // Exact retired transport; absent world alone is insufficient.
    Panel53Draft(Repo& repo,SqliteRecoveredCharacterRepository& profiles,
        Resolve resolve,Capture capture,WorldCurrent current,RecipientReady recipient_ready={},ConnectionClosed connection_closed={}):repo_(repo),profiles_(profiles),
        resolve_(std::move(resolve)),capture_(std::move(capture)),world_(std::move(current)),
        recipient_ready_(std::move(recipient_ready)),connection_closed_(std::move(connection_closed)){}

    std::optional<Projection> prepare_projection(std::uint64_t session,std::uint64_t guild,bool explicit_help=false) const {
        try {
            if(!resolve_ || !capture_ || !world_)return {};
            const auto recipient=resolve_(session);if(!recipient)return {};
            State state{*recipient,repo_.effective_snapshot(guild),repo_.applications(guild),{}, {}};
            const auto self=std::find_if(state.leader.roster.begin(),state.leader.roster.end(),[&](const auto& member){
                return member.account_id==recipient->account && member.character_id==recipient->character;});
            const auto pending_self=std::find_if(state.applications.begin(),state.applications.end(),[&](const auto& app){
                return app.applicant.account_id==recipient->account && app.applicant.character_id==recipient->character;});
            if(self==state.leader.roster.end() && pending_self==state.applications.end())return {};
            if(self!=state.leader.roster.end() && pending_self!=state.applications.end())return {};
            state.rows.push_back(self!=state.leader.roster.end()?*self:pending_self->applicant);
            for(const auto& member:state.leader.roster)if(member.character_id!=recipient->character)state.rows.push_back(member);
            for(const auto& app:state.applications)if(app.applicant.character_id!=recipient->character)state.rows.push_back(app.applicant);
            if(state.rows.size()>50 || !canonical_scope(state))return {}; // Fail closed BEFORE capture/send for combined encoded aliases.
            const auto audience=capture_(state.leader,state.applications);if(!audience)return {};
            state.audience=*audience;if(!world_valid(state) || !sql_resources_current(state))return {};
            Projection result{state,{},explicit_help,{}};
            std::vector<std::array<std::uint8_t,3>> rank_updates;
            const auto append=[&](const auto& bytes){result.logical.insert(result.logical.end(),bytes.begin(),bytes.end());};
            // Full previous-row removal is a caller debt, never bypassed by count50.
            const auto old=caches_.find(session);
            if(old!=caches_.end())for(std::size_t slot=1;slot<old->second.value.state.rows.size();++slot)
                append(RecoveredGuildRoster::remove(static_cast<std::uint8_t>(slot)));
            if(old!=caches_.end()) {
                result.previous=evidence(old->second);
                const auto& previous=old->second.value.state;
                if(!same_native_namespace(previous.recipient,*recipient) || previous.leader.guild.id!=guild ||
                   previous.rows.front().name_utf8!=state.rows.front().name_utf8)append(RecoveredGuildRoster::remove(0));
            }
            for(std::size_t slot=0;slot<state.rows.size();++slot) {
                const auto& row=state.rows[slot];const bool pending=!row.membership_revision;
                if(!row.role)return {};const auto level=RecoveredRoleLevel::parse(row.role->logical);if(!level)return {};
                const auto role=pending?std::uint8_t{0}:Repo::effective_display_role(state.leader,row);
                const bool online=std::any_of(state.audience.connected.begin(),state.audience.connected.end(),[&](const auto& owner){return owner.character==row.character_id;});
                const auto name=LegacyChineseCodec::encode(row.name_utf8,recipient->name_codepage==936);
                append(RecoveredGuildRoster::member(static_cast<std::uint8_t>(slot),role==2?1:role,level->level(),row.profile[29],online?1:0,name));
                if(role==2)rank_updates.push_back(RecoveredGuildLeadership::role_update(static_cast<std::uint8_t>(slot),role));
            }
            // Native8E opens/resets the main panel. Background/entry publication
            // seeds the complete roster and cache without opening that UI.
            if(explicit_help) {
                const auto header=OwnedGuildPanelHeader::readonly_members(state.leader.roster.size());if(!header)return {};
                auto bytes=*header;bytes[1+0x17]=state.leader.original_creation.capacity;append(bytes);
            }
            for(const auto& update:rank_updates)append(update); // All91 seed existing slots before93.
            return current_state(state)?std::optional{result}:std::nullopt;
        }catch(...){return {};}
    }
    // Host calls ONLY after exact complete logical batch reaches accepted world tail.
    // This acknowledges server publication, not client render/native acceptance.
    bool published(const Projection& projection) {
        try {
            if(prepare_projection(projection.state.recipient.session,projection.state.leader.guild.id,projection.explicit_help)!=std::optional{projection} ||
               !current_state(projection.state) || cached(projection.state.recipient.session)!=projection.previous ||
               serial_==std::numeric_limits<std::uint64_t>::max())return false;
            Contract contract{++serial_,projection.state.leader.guild.id,projection.state.leader.guild.revision,
                projection.state.recipient.world_generation,projection.state.recipient.account,projection.state.recipient.character,true,{}};
            for(std::size_t slot=0;slot<projection.state.rows.size();++slot) {
                const auto& row=projection.state.rows[slot];const bool pending=!row.membership_revision;
                contract.rows.push_back({static_cast<std::uint8_t>(slot),pending?std::uint8_t{0}:Repo::effective_display_role(projection.state.leader,row),
                    row.slot,row.account_id,row.character_id,row.membership_revision,pending});
            }
            const bool grants=projection.explicit_help && projection.state.rows.front().membership_revision!=0;
            if(grants && !founder_transfer_contract_draft::valid_panel(contract))return false;
            if(epoch_==std::numeric_limits<std::uint64_t>::max())return false;
            contract.explicit_single_use_authority=grants;
            caches_.insert_or_assign(projection.state.recipient.session,Cache{{projection.state,contract},!grants,++epoch_});return true;
        }catch(...){return false;}
    }
    std::optional<Publication> publication(std::uint64_t session) const {
        try {const auto prior=cached(session);if(!prior || prior->consumed || !current_state(prior->previous.state) || cached(session)!=prior)return {};
            return prior->previous;}catch(...){return {};}
    }
    std::optional<Plan> prepare(const Publication& original,std::uint8_t slot) const {
        try {
            if(publication(original.state.recipient.session)!=std::optional{original})return {};
            const auto action=founder_transfer_contract_draft::classify(0,RecoveredGuildLeave::Request{slot},original.contract);
            if(action.intent!=founder_transfer_contract_draft::Intent::Transfer || !action.selected || (action.selected->role!=1 && action.selected->role!=2))return {};
            const auto& row=original.state.rows.at(slot);auto identity=row;identity.membership_revision=0;
            const auto& guild=original.state.leader.guild;
            return Plan{original,slot,identity,{guild.id,guild.name_utf8,guild.revision,row.membership_revision}};
        }catch(...){return {};}
    }
    bool execute(const Plan& plan) {
        const auto session=plan.publication.state.recipient.session;
        try {
            // Never consume a different, newer publication or freshly remap slot.
            if(publication(session)!=std::optional{plan.publication})return false;
            if(prepare(plan.publication,plan.slot)!=std::optional{plan}){invalidate_exact(plan.publication);return false;}
            auto at=caches_.find(session);if(at==caches_.end() || at->second.value!=plan.publication)return false;
            at->second.consumed=true;
            const auto proof=[&] {
                const auto now=caches_.find(session);
                if(now==caches_.end() || now->second.value!=plan.publication || !now->second.consumed ||
                   !world_valid(plan.publication.state) || !sql_resources_current(plan.publication.state))
                    throw DatabaseError("CUSTOM-0083 consumed publication/world/resource lease changed");
            };
            repo_.transfer(plan.publication.state.leader,plan.publication.state.applications,plan.target,plan.membership,{proof,proof});
            // Preserve row caches for92 reconciliation; revoke exact related authority.
            for(auto& [key,cache]:caches_)if(cache.value.state.leader.guild.id==plan.membership.guild_id)cache.consumed=true;
            return true;
        }catch(...){invalidate_exact(plan.publication);return false;}
    }
    void invalidate_exact(const Publication& original) {
        const auto at=caches_.find(original.state.recipient.session);
        if(at!=caches_.end() && at->second.value==original)at->second.consumed=true;
    }
    std::optional<CacheEvidence> cached(std::uint64_t session) const {
        const auto at=caches_.find(session);return at==caches_.end()?std::nullopt:std::optional{evidence(at->second)};
    }
    bool revoke_exact(const CacheEvidence& previous) {
        const auto at=caches_.find(previous.previous.state.recipient.session);
        if(at==caches_.end() || evidence(at->second)!=previous)return false;
        if(!at->second.consumed){if(epoch_==std::numeric_limits<std::uint64_t>::max())return false;
            at->second.consumed=true;at->second.epoch=++epoch_;}return true;
    }
    // Revocation retains exact previous rows for deferred92. No SQL refresh.
    void revoke_guild(std::uint64_t guild) {
        for(auto& [session,cache]:caches_)if(cache.value.state.leader.guild.id==guild && !cache.consumed){
            cache.consumed=true;if(epoch_<std::numeric_limits<std::uint64_t>::max())cache.epoch=++epoch_;}
    }
    // Revoke before preparation; readiness failure RETAINS92 debt.
    std::optional<ClearPlan> prepare_clear(std::uint64_t session) {
        const auto prior=cached(session);if(!prior || !revoke_exact(*prior))return {};
        return clear_current(session);
    }
    // Host invokes ONLY after this exact batch reaches accepted current tail.
    bool cleared(const ClearPlan& plan) {
        const auto session=plan.previous.previous.state.recipient.session;
        if(cached(session)!=std::optional{plan.previous})return false;
        if(clear_current(session)!=std::optional{plan})return false;
        if(cached(session)!=std::optional{plan.previous})return false;
        caches_.erase(session);return true;
    }
    // Exact closed-transport proof is distinct from character picker absence.
    bool retire_closed(const CacheEvidence& previous) {
        try {
        const auto session=previous.previous.state.recipient.session;
        if(!resolve_ || !connection_closed_ || cached(session)!=std::optional{previous} || resolve_(session))return false;
        if(!connection_closed_(previous.previous.state.recipient) || resolve_(session) || cached(session)!=std::optional{previous})return false;
        if(!connection_closed_(previous.previous.state.recipient) || resolve_(session) || cached(session)!=std::optional{previous})return false;
        caches_.erase(session);return true;
        }catch(...){return false;}
    }
    enum class FounderMutation {Approve,Reject,Kick,Disband,Appoint,RemoveOffice,Announcement,Transfer};
    // Read lease for ALL future52-aware founder routes. Never manufacture an
    // Original::Leader or dispatch52 history into any old founder mutation.
    std::optional<Repo::EffectiveLeader> founder_authority(std::uint64_t account,std::uint64_t character,FounderMutation) const {
        try{return repo_.effective_leader(account,character);}catch(...){return {};}
    }
private:
    struct Cache {Publication value;bool consumed{};std::uint64_t epoch{};};
    static CacheEvidence evidence(const Cache& cache){return {cache.value,cache.consumed,cache.epoch};}
    std::optional<ClearPlan> clear_current(std::uint64_t session) const {
        try {
            const auto prior=cached(session);if(!prior || !prior->consumed || !resolve_ || !recipient_ready_)return {};
            const auto current=resolve_(session);if(!current || !current->session || current->session!=session || !current->account ||
                !current->character || !current->world_generation || !current->position_revision ||
                (current->name_codepage!=950 && current->name_codepage!=936) || !recipient_ready_(*current))return {};
            if(resolve_(session)!=current || cached(session)!=prior)return {};
            ClearPlan plan{*prior,*current,{}};
            for(std::size_t slot=1;slot<prior->previous.state.rows.size();++slot){const auto wire=RecoveredGuildRoster::remove(static_cast<std::uint8_t>(slot));plan.logical.insert(plan.logical.end(),wire.begin(),wire.end());}
            const auto self=RecoveredGuildRoster::remove(0);plan.logical.insert(plan.logical.end(),self.begin(),self.end());
            return recipient_ready_(*current) && resolve_(session)==current && cached(session)==prior?std::optional{plan}:std::nullopt;
        }catch(...){return {};}
    }
    bool world_valid(const State& state) const {
        if(!resolve_ || !world_ || !world_(state.audience) || state.audience.connected.empty())return false;
        std::set<std::uint64_t> required;for(const auto& row:state.rows)required.insert(row.character_id);
        if(required.size()!=state.rows.size() || state.audience.resources.size()!=required.size())return false;
        for(const auto& [character,resource]:state.audience.resources)if(!required.contains(character) || !resource.revision ||
            !resource.max_hp || resource.hp>resource.max_hp || resource.mp>resource.max_mp || resource.design_id.empty())return false;
        std::uint64_t previous=0;bool actor=false;
        for(const auto& owner:state.audience.connected) {
            if(owner.session<=previous || !owner.world_generation || !owner.position_revision || !owner.account || !owner.character ||
               (owner.name_codepage!=950 && owner.name_codepage!=936) || resolve_(owner.session)!=std::optional{owner})return false;
            previous=owner.session;if(owner==state.recipient)actor=true;
            if(std::none_of(state.rows.begin(),state.rows.end(),[&](const auto& row){return row.account_id==owner.account && row.character_id==owner.character;}))return false;
        }
        return actor && resolve_(state.recipient.session)==std::optional{state.recipient};
    }
    bool sql_resources_current(const State& state) const {
        for(const auto& row:state.rows) {
            const auto at=state.audience.resources.find(row.character_id);if(at==state.audience.resources.end() ||
                profiles_.load_resources(row.account_id,row.character_id)!=std::optional{at->second})return false;
        }
        return true;
    }
    bool current_state(const State& state) const {
        return repo_.effective_snapshot(state.leader.guild.id)==state.leader && repo_.applications(state.leader.guild.id)==state.applications &&
            world_valid(state) && sql_resources_current(state);
    }
    Repo& repo_;SqliteRecoveredCharacterRepository& profiles_;Resolve resolve_;Capture capture_;WorldCurrent world_;
    RecipientReady recipient_ready_;ConnectionClosed connection_closed_;
    std::map<std::uint64_t,Cache> caches_;std::uint64_t serial_{},epoch_{};
};

}
