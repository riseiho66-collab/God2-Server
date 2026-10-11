#pragma once
#include "OwnedGuildSuccessionServiceDraft.h"
#include "db/EffectiveGuildAnnouncementRepositoryDraft.h"
#include "protocol/RecoveredGuildAnnouncement.h"
#include <chrono>
namespace god2 {
// Private CUSTOM0083; no formal handler. Native79/98 codecs are unchanged.
class EffectiveGuildAnnouncementServiceDraft {
public:
    using Panel=OwnedGuildSuccessionServiceDraft;
    using Repository=EffectiveGuildAnnouncementRepositoryDraft;
    using Time=OwnedGuildMembershipConversation::Time;
    using Wire=RecoveredGuildAnnouncement;
    static constexpr auto lifetime=std::chrono::seconds{300}; // Existing CUSTOM0078 timer.
    enum class PublicationCause {ExplicitHelp,EntryOrSaveEcho};
    struct Projection {Panel::Projection panel;Repository::Snapshot announcement;std::vector<std::uint8_t> logical;PublicationCause cause;};
    struct Action {Panel::Publication panel;Repository::Snapshot announcement;Time opened,expires;bool operator==(const Action&) const=default;};
    using Readiness=std::function<bool(const Panel::State&)>;
    EffectiveGuildAnnouncementServiceDraft(Repository& repository,Panel& panel,Readiness readiness):repository_(repository),panel_(panel),ready_(std::move(readiness)){}
    // Caller allows only explicit help or qualified entry/save echo. There is
    // no unsolicited tick preparation: native98 overwrites local edited text.
    std::optional<Projection> prepare(std::uint64_t session,std::uint64_t guild,PublicationCause cause) const {
        try {
            const auto panel=panel_.prepare_projection(session,guild,cause==PublicationCause::ExplicitHelp);if(!panel)return {};
            const auto value=repository_.load(guild);const auto text=value.value?value.value->text_utf8:std::string{};
            const auto update=Wire::update(Wire::text_request(text,panel->state.recipient.name_codepage));if(!update)return {};
            Projection out{*panel,value,panel->logical,cause};out.logical.insert(out.logical.end(),update->begin(),update->end());
            if(!ready_ || !ready_(panel->state) || repository_.load(guild)!=value)return {};return out;
        }catch(...){return {};}
    }
    bool published(const Projection& projection,Time now) {
        try {
            const auto& state=projection.panel.state;
            // Qualify lease arithmetic BEFORE committing any panel authority.
            if(projection.cause==PublicationCause::ExplicitHelp && state.leader.owner.account_id==state.recipient.account &&
               state.leader.owner.character_id==state.recipient.character && now>Time::max()-lifetime)return false;
            const auto expected=prepare(state.recipient.session,state.leader.guild.id,projection.cause);
            if(!expected || expected->panel!=projection.panel || expected->announcement!=projection.announcement ||
               expected->logical!=projection.logical || !panel_.published(projection.panel))return false;
            leases_.erase(state.recipient.session); // Explicit/entry replaces any old lease.
            consumed_.erase(state.recipient.session);
            if(projection.cause!=PublicationCause::ExplicitHelp || state.leader.owner.account_id!=state.recipient.account ||
               state.leader.owner.character_id!=state.recipient.character)return true;
            const auto pub=panel_.publication(state.recipient.session);if(!pub)return false;
            leases_.emplace(state.recipient.session,Action{*pub,projection.announcement,now,now+lifetime});return true;
        }catch(...){return false;}
    }
    std::optional<Action> capture_before_prefix(std::uint64_t session,Time now) const {
        try {
            const auto at=leases_.find(session);if(at==leases_.end())return {};
            const auto& action=at->second;
            if(!action_current(action,now))return {};return action;
        }catch(...){return {};}
    }
    std::optional<Repository::Snapshot> execute(const Action& action,const Wire::Request& request,Time now) {
        const auto session=action.panel.state.recipient.session;
        try {
            const auto at=leases_.find(session);if(at==leases_.end() || at->second!=action)return {};
            const bool qualified=action_current(action,now);
            if(leases_.find(session)==leases_.end() || leases_.at(session)!=action)return {};
            leases_.erase(session);if(!qualified)return {};
            consumed_.insert_or_assign(session,action);
            panel_.invalidate_exact(action.panel);
            const auto text=Wire::text_utf8(request,action.panel.state.recipient.name_codepage);
            const auto proof=[&] {
                // Pure immutable world/executor/resource qualification, never
                // borrowed newer governance, panel or announcement authority.
                const auto at=consumed_.find(session);
                if(at==consumed_.end() || at->second!=action || !ready_ || !ready_(action.panel.state) ||
                   consumed_.find(session)==consumed_.end() || consumed_.at(session)!=action)
                    throw DatabaseError("CUSTOM0083 announcement audience/consumed lease changed");
            };
            const auto result=repository_.save(action.panel.state.leader,action.announcement,text,{proof,proof});
            consumed_.erase(session);return result;
        }catch(...){const auto at=consumed_.find(session);if(at!=consumed_.end() && at->second==action)consumed_.erase(at);return {};}
    }
    // Revocation only: exact original publication cannot erase a later lease.
    // Host calls after matching panel clear/retired transport or explicit revoke.
    void invalidate_exact_publication(const Panel::Publication& previous) {
        const auto session=previous.state.recipient.session;
        const auto at=leases_.find(session);if(at!=leases_.end() && at->second.panel==previous)leases_.erase(at);
        const auto used=consumed_.find(session);if(used!=consumed_.end() && used->second.panel==previous)consumed_.erase(used);
    }
    void revoke_guild(std::uint64_t guild) {
        for(auto at=leases_.begin();at!=leases_.end();)if(at->second.panel.state.leader.guild.id==guild)at=leases_.erase(at);else ++at;
        for(auto at=consumed_.begin();at!=consumed_.end();)if(at->second.panel.state.leader.guild.id==guild)at=consumed_.erase(at);else ++at;
    }
private:
    bool action_current(const Action& action,Time now) const {
        const auto& state=action.panel.state;
        return now>=action.opened && now<action.expires && state.leader.owner.character_id==state.recipient.character &&
            state.leader.owner.account_id==state.recipient.account && panel_.publication(state.recipient.session)==std::optional{action.panel} &&
            repository_.load(state.leader.guild.id)==action.announcement && ready_ && ready_(state);
    }
    Repository& repository_;Panel& panel_;Readiness ready_;std::map<std::uint64_t,Action> leases_,consumed_;
};
}
