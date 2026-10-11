#pragma once
#include "handlers/CombinedGuildLifecycleRuntimeDraft.h"
#include <memory>
#include <set>
#include "spdlog/spdlog.h"
#include "handlers/EffectiveGuildPendingCancellationServiceDraft.h"
#include "protocol/RecoveredWorldFrame.h"
namespace god2 {
// PRIVATE83 real Application composition. No formal activation or native ACK.
class OwnedGuildSuccessionApplicationDraft:public std::enable_shared_from_this<OwnedGuildSuccessionApplicationDraft>{
public:
    using Panel=OwnedGuildSuccessionServiceDraft;using Host=OwnedGuildSuccessionWorldHostDraft;using Ann=EffectiveGuildAnnouncementServiceDraft;using Runtime=CombinedGuildLifecycleRuntimeDraft;
    using Context=std::function<std::optional<std::uint64_t>(std::uint64_t,std::uint64_t)>;
    // MUST invoke ack on game executor, after actual exact Session strand enqueue.
    using Send=std::function<void(const Panel::Owner&,std::vector<std::uint8_t>,std::function<void(bool)>)>;
    OwnedGuildSuccessionApplicationDraft(Panel::Repo& repo,EffectiveGuildAdmissionRepositoryDraft& admissions,
        Ann::Repository& notices,Panel::Original& original,SqliteRecoveredCharacterRepository& profiles,Panel::Resolve resolve,
        Host::Enumerate enumerate,Host::PeerReady peers,Panel::RecipientReady recipient_ready,
        Panel::ConnectionClosed closed,Context context,Send send,bool membership,bool announcements,bool offices):
        resolve_(resolve),closed_(closed),context_(std::move(context)),send_(std::move(send)),membership_(membership),announcements_(announcements),offices_(offices),
        host_(profiles,std::move(enumerate),resolve,std::move(peers)),
        panel_(repo,profiles,resolve,[this](const auto& leader,const auto& apps){return host_.capture(leader,apps);},
            [this](const auto& audience){return host_.current(audience);},std::move(recipient_ready),std::move(closed)),
        notices_(notices,panel_,[this](const auto& state){return host_.current(state.audience);}),
        admission_(admissions,panel_,[this](const auto& state){return host_.current(state.audience);}),
        removal_(admissions,panel_,[this](const auto& state){return host_.current(state.audience);}),
        governance_(admissions,panel_,[this](const auto& state){return host_.current(state.audience);}),
        runtime_(panel_,host_,admission_,removal_,governance_,notices_),
        cancel_(admissions,original,repo,profiles,panel_,resolve,[this](const auto& a){return host_.preflight(a);},[this](const auto& a){return host_.current(a);},[this](const auto& pub){notices_.invalidate_exact_publication(pub);}),cancel_runtime_(cancel_){}
    std::optional<std::uint64_t> context(std::uint64_t session)const{try{const auto owner=resolve_(session);return owner&&context_?context_(owner->account,owner->character):std::nullopt;}catch(...){return {};}}
    Runtime::Batch capture(std::uint64_t session,std::span<const Runtime::Indexed> records)const{return runtime_.capture_before_any_prefix(session,records);}
    bool execute(const Runtime::Captured& item){
        const auto office=std::get_if<EffectiveGuildGovernanceServiceDraft::Plan>(&item.intent);
        if(!membership_ || (!offices_ && office && office->action!=EffectiveGuildGovernanceServiceDraft::Action::Disband)){retire(item.original);return false;}
        return runtime_.execute(item);
    }
    std::optional<Ann::Action> capture_notice(std::uint64_t session,Ann::Time now)const{return membership_&&announcements_?notices_.capture_before_prefix(session,now):std::nullopt;}
    bool execute_notice(const Ann::Action& action,const Ann::Wire::Request& request,Ann::Time now){
        if(!membership_ || !announcements_){retire(action.panel);return false;}
        return Runtime::execute_announcement(panel_,host_,notices_,action,request,now).has_value();
    }
    auto capture_cancel(std::uint64_t session,std::span<const Runtime::Indexed> records,Ann::Time now)const{return cancel_runtime_.capture_before_any_prefix(session,records,now);}
    bool execute_cancel(const EffectiveGuildPendingCancellationRuntimeDraft::Captured& item,Ann::Time now){if(!membership_){if(item.original)cancel_.deny_exact(*item.original);return false;}return cancel_runtime_.execute(item,now);}
    void revoke(std::uint64_t session){
        if(const auto at=pending_sync_.find(session);at!=pending_sync_.end())revoked_sync_.insert(at->second);
        if(const auto queued=queued_sync_.find(session);queued!=queued_sync_.end()){queued->second.explicit_help=false;queued->second.force=true;}
        if(const auto permit=cancel_.permit(session))cancel_.deny_exact(*permit);const auto old=panel_.cached(session);if(old){panel_.revoke_exact(*old);notices_.invalidate_exact_publication(old->previous);}}
    void guild_changed(std::uint64_t guild){panel_.revoke_guild(guild);notices_.revoke_guild(guild);}
    void disconnected(std::uint64_t session){const auto old=panel_.cached(session);if(old && panel_.retire_closed(*old))notices_.invalidate_exact_publication(old->previous);const auto debt=transport_debt_.find(session);if(debt!=transport_debt_.end() && !resolve_(session) && closed_ && closed_(debt->second.owner)){transport_debt_.erase(debt);completed_delivery_.erase(session);}
        if(old && !resolve_(session) && closed_ && closed_(old->previous.state.recipient))completed_delivery_.erase(session);}
    // Extra full native92 sweep prevents enqueued-but-unqualified projections
    // from leaving unknown slots. Every sweep is technical cache cleanup only.
    void sync(std::uint64_t session,bool explicit_help=false,bool force=false){
        try{
            const auto owner=resolve_(session);if(!owner || !send_ || serial_==UINT64_MAX)return;
            // GAME-owned arbitration: prepare the latest queued projection only
            // after the previous enqueue ACK has qualified its cache epoch.
            if(pending_sync_.contains(session)){
                const auto guild=context_(owner->account,owner->character);
                const auto observed=guild?notices_.prepare(session,*guild,Ann::PublicationCause::EntryOrSaveEcho):std::nullopt;
                SyncRequest request{*owner,explicit_help && observed.has_value(),force,observed};
                const auto prior=queued_sync_.find(session);
                if(prior!=queued_sync_.end() && prior->second.owner==*owner && same_observation(prior->second.observed,observed)){
                    request.explicit_help=request.explicit_help || prior->second.explicit_help;request.force=request.force || prior->second.force;
                }
                queued_sync_.insert_or_assign(session,std::move(request));return;
            }
            const auto guild=context_(owner->account,owner->character);
            if(!guild){
                const auto clear=panel_.prepare_clear(session);
                if(!clear && !transport_debt_.contains(session))return;
                const auto ticket=++serial_;pending_sync_.emplace(session,ticket);auto logical=sweep();auto weak=weak_from_this();
                send_sync(*owner,std::move(logical),ticket,[weak,owner=*owner,clear,ticket](bool accepted){if(auto self=weak.lock()){
                    SyncCompletion complete{self,owner.session,ticket};
                    if(!accepted)return;self->note_enqueued(owner,ticket);
                    if(self->resolve_(owner.session)!=std::optional{owner})return;
                    if(clear && !self->panel_.cleared(*clear))return;
                    if(clear)self->notices_.invalidate_exact_publication(clear->previous.previous);
                    self->clear_transport_debt(owner.session,ticket);
                }});return;
            }
            auto projection=notices_.prepare(session,*guild,explicit_help&&membership_?Ann::PublicationCause::ExplicitHelp:Ann::PublicationCause::EntryOrSaveEcho);
            if(!projection)return;
            if(!force && !explicit_help && !transport_debt_.contains(session))if(const auto cache=panel_.cached(session);cache && cache->previous.state==projection->panel.state)return;
            // Self92 resets/closes the native main panel. Sweep unknown slots
            // only after an enqueued projection could not qualify its cache.
            const auto scope=Panel::canonical_scope(projection->panel.state);if(!scope)return;
            // Only canonical same-recipient/self history permits nonself reset.
            // Unknown identity, clear/self92 history and cross-locale primary-name
            // mismatch retain the complete clear; native reopening remains OPEN.
            const bool debt=transport_debt_.contains(session);
            const bool safe_reset=debt && self_preserving_debt(session,*scope);
            auto logical=debt?sweep(!safe_reset):std::vector<std::uint8_t>{};
            const bool preserve_self=(!debt || safe_reset) && projection_preserves_self(*projection,*scope);
            logical.insert(logical.end(),projection->logical.begin(),projection->logical.end());
            if(logical.size()>RecoveredWorldFrame::max_logical_size)return;
            const auto ticket=++serial_;pending_sync_.emplace(session,ticket);auto weak=weak_from_this();
            send_sync(projection->panel.state.recipient,std::move(logical),ticket,[weak,projection=*projection,scope=*scope,preserve_self,ticket](bool accepted){if(auto self=weak.lock()){
                const auto session=projection.panel.state.recipient.session;SyncCompletion complete{self,session,ticket};
                if(!accepted)return;self->note_enqueued(projection.panel.state.recipient,ticket,preserve_self?std::optional{scope}:std::nullopt);
                if(!self->revoked_sync_.contains(ticket) && self->notices_.published(projection,Ann::Time::clock::now())){
                    const auto& state=projection.panel.state;
                    spdlog::info("OWNED_GUILD_EFFECTIVE52_PUBLICATION session_id={} actor_account={} actor_character={} guild_id={} captured_guild_revision={} captured_members={} captured_pending={} cause={} accepted=true CUSTOM-0083",
                        state.recipient.session,state.recipient.account,state.recipient.character,state.leader.guild.id,state.leader.guild.revision,state.leader.roster.size(),state.applications.size(),projection.cause==Ann::PublicationCause::ExplicitHelp?"explicit_help":"readonly");
                    if(!self->announcements_)if(const auto pub=self->panel_.publication(session))self->notices_.invalidate_exact_publication(*pub);
                    if(projection.cause==Ann::PublicationCause::ExplicitHelp && self->membership_)if(const auto cache=self->panel_.cached(session))self->cancel_.arm_after_publication(*cache,Ann::Time::clock::now());
                    self->clear_transport_debt(session,ticket);
                }
            }});
        }catch(...){/* Keep debt; failed readiness cannot manufacture a publication. */}
    }
    // Actor-only authoritative native98 echo after denied79. Preparation is
    // read-only; never publish/replace panel cache or grant a new73/79 lease.
    void echo_notice(std::uint64_t session){
        try{
            const auto owner=resolve_(session);const auto guild=context(session);if(!owner || !guild || !send_)return;
            const auto projection=notices_.prepare(session,*guild,Ann::PublicationCause::EntryOrSaveEcho);if(!projection)return;
            const auto text=projection->announcement.value?projection->announcement.value->text_utf8:std::string{};
            const auto logical=Ann::Wire::update(Ann::Wire::text_request(text,owner->name_codepage));if(!logical)return;
            if(resolve_(session)!=std::optional{*owner} || projection->panel.state.recipient!=*owner)return;
            send_(*owner,*logical,[owner=*owner,guild=*guild](bool accepted){if(accepted)spdlog::info("OWNED_GUILD_EFFECTIVE52_NOTICE_ECHO session_id={} actor_account={} actor_character={} guild_id={} accepted=true readonly=true CUSTOM-0083",owner.session,owner.account,owner.character,guild);});
        }catch(...){/* No new cache or authority on failed read/delivery. */}
    }
    void deliver(const Panel::Owner& owner,std::vector<std::uint8_t> bytes,std::function<void(bool)> accepted){if(send_)send_(owner,std::move(bytes),std::move(accepted));else if(accepted)accepted(false);}
    Panel& panel(){return panel_;}Host& host(){return host_;}Ann& notices(){return notices_;}
private:
    struct SyncRequest{Panel::Owner owner;bool explicit_help,force;std::optional<Ann::Projection> observed;};
    static bool same_observation(const std::optional<Ann::Projection>& a,const std::optional<Ann::Projection>& b){
        if(!a || !b)return !a && !b;return a->panel.state==b->panel.state && a->announcement==b->announcement;
    }
    struct SyncCompletion{std::shared_ptr<OwnedGuildSuccessionApplicationDraft> self;std::uint64_t session,ticket;~SyncCompletion()noexcept{try{self->complete_sync(session,ticket);}catch(...){}}};
    void send_sync(const Panel::Owner& owner,std::vector<std::uint8_t> logical,std::uint64_t ticket,std::function<void(bool)> ack){
        try{send_(owner,std::move(logical),std::move(ack));}catch(...){complete_sync(owner.session,ticket);}
    }
    void complete_sync(std::uint64_t session,std::uint64_t ticket){
        const auto at=pending_sync_.find(session);if(at==pending_sync_.end() || at->second!=ticket)return;
        pending_sync_.erase(at);revoked_sync_.erase(ticket);const auto next=queued_sync_.find(session);if(next==queued_sync_.end())return;
        auto request=next->second;queued_sync_.erase(next);
        if(resolve_(session)!=std::optional{request.owner})return;
        if(request.explicit_help){
            const auto guild=context_(request.owner.account,request.owner.character);
            const auto current=guild?notices_.prepare(session,*guild,Ann::PublicationCause::EntryOrSaveEcho):std::nullopt;
            if(!same_observation(request.observed,current)){request.explicit_help=false;request.force=true;}
        }
        sync(session,request.explicit_help,request.force);
    }
    static std::vector<std::uint8_t> sweep(bool include_self=true){std::vector<std::uint8_t> bytes;for(unsigned slot=1;slot<50;++slot){bytes.push_back(0x92);bytes.push_back(static_cast<std::uint8_t>(slot));}if(include_self)bytes.insert(bytes.end(),{0x92,0});return bytes;}
    void retire(const std::optional<Panel::Publication>& previous){if(previous){panel_.invalidate_exact(*previous);notices_.invalidate_exact_publication(*previous);}}
    struct TransportDebt{Panel::Owner owner;std::uint64_t ticket;std::optional<Panel::CanonicalScope> common_scope;bool uncertified{};};
    static bool projection_preserves_self(const Ann::Projection& next,const Panel::CanonicalScope& scope){
        if(!scope.serialized_self_matches)return false;
        if(!next.panel.previous)return true;
        const auto previous=Panel::canonical_scope(next.panel.previous->previous.state);
        return previous && Panel::same_native_self(*previous,scope);
    }
    bool self_preserving_debt(std::uint64_t session,const Panel::CanonicalScope& next)const{
        const auto at=transport_debt_.find(session);
        if(at==transport_debt_.end() || at->second.uncertified || !at->second.common_scope || !Panel::same_native_self(*at->second.common_scope,next))return false;
        if(const auto cached=panel_.cached(session)){
            const auto previous=Panel::canonical_scope(cached->previous.state);
            if(!previous || !Panel::same_native_self(*previous,next))return false;
        }
        return true;
    }
    void note_enqueued(const Panel::Owner& owner,std::uint64_t ticket,std::optional<Panel::CanonicalScope> scope={}){
        if(!resolve_(owner.session) && closed_ && closed_(owner))return;
        const auto done=completed_delivery_.find(owner.session);if(done!=completed_delivery_.end() && done->second>=ticket)return;
        auto at=transport_debt_.find(owner.session);if(at!=transport_debt_.end() && at->second.ticket>=ticket)return;
        const bool certified=scope && scope->recipient==owner && scope->serialized_self_matches;
        if(at==transport_debt_.end()){
            transport_debt_.emplace(owner.session,TransportDebt{owner,ticket,certified?scope:std::nullopt,!certified});return;
        }
        // Compact conjunction over EVERY possibly-enqueued projection, not a
        // latest-owner overwrite. Unproved history stays poisoned until the
        // existing exact publication/clear acknowledgement discharges this debt.
        auto& debt=at->second;
        debt.uncertified=debt.uncertified || !certified || !debt.common_scope || !Panel::same_native_self(*debt.common_scope,*scope);
        debt.owner=owner;debt.ticket=ticket;
        if(debt.uncertified)debt.common_scope.reset();
    }
    void clear_transport_debt(std::uint64_t session,std::uint64_t ticket){auto& done=completed_delivery_[session];done=std::max(done,ticket);const auto at=transport_debt_.find(session);if(at!=transport_debt_.end()&&at->second.ticket<=ticket)transport_debt_.erase(at);}
    Panel::Resolve resolve_;Panel::ConnectionClosed closed_;Context context_;Send send_;bool membership_,announcements_,offices_;
    Host host_;Panel panel_;Ann notices_;EffectiveGuildAdmissionServiceDraft admission_;EffectiveGuildRemovalServiceDraft removal_;EffectiveGuildGovernanceServiceDraft governance_;Runtime runtime_;EffectiveGuildPendingCancellationServiceDraft cancel_;EffectiveGuildPendingCancellationRuntimeDraft cancel_runtime_;
    std::set<std::uint64_t> revoked_sync_;std::map<std::uint64_t,std::uint64_t> pending_sync_;std::map<std::uint64_t,SyncRequest> queued_sync_;
    std::map<std::uint64_t,TransportDebt> transport_debt_;std::map<std::uint64_t,std::uint64_t> completed_delivery_;std::uint64_t serial_{};
};
}
