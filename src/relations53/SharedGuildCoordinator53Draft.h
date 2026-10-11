#pragma once
#include "RelationsRepositoryDraft.h"
#include "NeighboringGuild53AdmissionRepositoryDraft.h"
#include "WorldHost53Draft.h"
#include "db/SqliteOwnedGuildAnnouncementRepository.h"
#include "GuildAnnouncement53RepositoryDraft.h"
#include "protocol/RecoveredGuildAnnouncement.h"
#include "protocol/RecoveredWorldFrame.h"
#include <memory>
#include <variant>
namespace god2 {
// CUSTOM84 source connection. One composite roster+notice+relations coordinator.
// Trusted GAME executor only; formal activation and client acceptance deferred.
class SharedGuildCoordinator53Draft:public std::enable_shared_from_this<SharedGuildCoordinator53Draft>{
public:
    using Announcement=GuildAnnouncement53RepositoryDraft;using Time=OwnedGuildMembershipConversation::Time;using Clock=std::function<Time()>;
    static constexpr auto notice_lifetime=std::chrono::seconds{300}; // Existing CUSTOM0078.
    using Neighboring=NeighboringGuild53AdmissionRepositoryDraft;
    using Storage=RelationsRepositoryDraft;using Panel=Panel53Draft;using Host=WorldHost53Draft;using Owner=Panel::Owner;using Audience=Panel::Audience;
    using Send=std::function<void(const Owner&,std::vector<std::uint8_t>,std::function<void(bool)>)>;
    using Context=std::function<std::optional<std::uint64_t>(std::uint64_t,std::uint64_t)>;
    struct Baseline {
        Owner recipient;std::vector<native_relation_private::Row> rows;bool roster_empty_verified{};
        enum class Origin {ReceiverObservation,OrderedNativeReset};
        Origin origin{Origin::ReceiverObservation};
    };
    // Origins remain distinct: actual receiver evidence or a source-phase
    // expected state after the build-matched ordered native reset. Neither a
    // client claim nor a new socket alone supplies an empty cache baseline.
    using KnownBaseline=std::function<std::optional<Baseline>(const Owner&)>;
    struct Published {Owner recipient;Storage::View view;Panel::CacheEvidence panel;std::uint64_t epoch{},lifecycle{};bool operator==(const Published&)const=default;};
    struct Action {Published original;Storage::Lease lease;Audience audience;};
    struct Lifecycle {Published original;Storage::LifecycleLease lease;Audience audience;};
    struct Indexed {std::size_t index{};std::vector<std::uint8_t> logical;};
    struct Batch {bool valid{};std::optional<Published> original;std::optional<Action> action;};
    SharedGuildCoordinator53Draft(Storage& storage,Succession53ReaderDraft& reader,SqliteOwnedGuildAnnouncementRepository& notices,
        SqliteRecoveredCharacterRepository& profiles,Panel::Resolve resolve,Host::Enumerate enumerate,Host::PeerReady peer,
        Panel::RecipientReady ready,Panel::ConnectionClosed closed,Context context,Send send,KnownBaseline baseline,bool enabled=false,Neighboring* neighboring=nullptr,Announcement* announcement=nullptr,Clock clock=[] {return OwnedGuildMembershipConversation::Clock::now();},Neighboring::Original* original=nullptr):
        storage_(storage),notices_(notices),resolve_(resolve),closed_(closed),context_(std::move(context)),send_(std::move(send)),baseline_(std::move(baseline)),enabled_(enabled),neighboring_(neighboring),announcement_(announcement),clock_(std::move(clock)),original_(original),
        host_(profiles,std::move(enumerate),resolve,std::move(peer)),panel_(reader,profiles,resolve,[this](const auto& leader,const auto& apps){return host_.capture(leader,apps);},[this](const auto& a){return host_.current(a);},std::move(ready),std::move(closed)){}
    Panel& panel(){return panel_;}
    Host& host(){return host_;}
    std::optional<Owner> owner(std::uint64_t session)const{return resolve_?resolve_(session):std::nullopt;}
    std::optional<std::uint64_t> context(std::uint64_t session)const{
        const auto value=owner(session);return value&&context_?context_(value->account,value->character):std::nullopt;
    }
    void deliver(const Owner& recipient,std::vector<std::uint8_t> logical,std::function<void(bool)> ack){
        if(!send_||owner(recipient.session)!=std::optional{recipient}){ack(false);return;}
        send_(recipient,std::move(logical),std::move(ack));
    }
    // Same composite ACK/cache, accepted ordinary/officer capability is separate
    // from founder-only relation authority. Pending self0 NEVER gets this grant.
    std::optional<Published> publication(std::uint64_t session)const{
        const auto p=member_publication(session);
        return p&&p->view.leader.owner.account_id==p->recipient.account&&p->view.leader.owner.character_id==p->recipient.character?p:std::nullopt;
    }
    std::optional<Published> member_publication(std::uint64_t session)const{
        const auto hold=weak_from_this().lock();if(!hold)return {};
        try{const auto at=publications_.find(session);if(at==publications_.end()||!enabled_)return {};const auto p=at->second;
            if(!unchanged(session,p.lifecycle)||resolve_(session)!=std::optional{p.recipient}||!unchanged(session,p.lifecycle))return {};
            if(panel_.cached(session)!=std::optional{p.panel}||!panel_.publication(session)||!unchanged(session,p.lifecycle))return {};
            if(storage_.view(p.view.leader.guild.id,p.recipient.name_codepage==936)!=p.view||!unchanged(session,p.lifecycle))return {};
            const auto current=publications_.find(session);return current!=publications_.end()&&current->second==p?std::optional{p}:std::nullopt;
        }catch(...){return {};}
    }
    void revoke(std::uint64_t session){
        advance(session);notice_leases_.erase(session);pending_permits_.erase(session);
        if(const auto p=publications_.find(session);p!=publications_.end()){panel_.invalidate_exact(p->second.panel.previous);publications_.erase(p);}active_.erase(session);
        if(const auto at=pending_.find(session);at!=pending_.end())at->second.revoked=true;
        if(const auto at=queued_.find(session);at!=queued_.end()){at->second.help=false;at->second.lifecycle=generation(session);}
    }
    void sync(std::uint64_t session,bool explicit_help=false){
        const auto hold=weak_from_this().lock();if(!hold)return;const auto lifecycle=advance(session);if(!lifecycle)return;
        try{const auto owner=resolve_(session);if(!owner||!unchanged(session,lifecycle)||!send_||!context_)return;
            const auto guild=context_(owner->account,owner->character);if(!unchanged(session,lifecycle))return;
            if(!guild){if(pending_.contains(session))queued_.insert_or_assign(session,Request{*owner,0,false,{},lifecycle});else clear(*owner);return;}
            const auto observed=storage_.view(*guild,owner->name_codepage==936);if(!unchanged(session,lifecycle))return;
            if(pending_.contains(session)){Request request{*owner,*guild,explicit_help,observed,lifecycle};const auto old=queued_.find(session);if(old!=queued_.end()&&old->second.owner==*owner&&old->second.guild==*guild&&old->second.observed==observed)request.help|=old->second.help;queued_.insert_or_assign(session,std::move(request));return;}
            dispatch({*owner,*guild,explicit_help,observed,lifecycle});
        }catch(...){/* No authority/SQL on unqualified context. */}
    }
    std::optional<Action> capture_before_prefix(std::uint64_t session,std::span<const std::uint8_t> raw){
        const auto hold=weak_from_this().lock();if(!hold)return {};
        try{const auto p=publication(session);if(!p)return {};const auto lease=storage_.capture(authority(*p),raw);const auto audience=capture_audience({lease.low,lease.high});if(!audience||lease.whole_typed!=p->view.whole||!exact_publication(*p))return {};return Action{*p,lease,*audience};}catch(...){return {};}
    }
    Batch capture_before_any_prefix(std::uint64_t session,std::span<const Indexed> records){
        Batch batch;if(const auto original=publications_.find(session);original!=publications_.end())batch.original=original->second;std::optional<std::size_t> relation;std::size_t mutations=0;std::size_t previous=0;bool first=true;
        for(std::size_t i=0;i<records.size();++i){const auto& r=records[i];if(r.logical.empty()||(!first&&r.index<=previous))return batch;previous=r.index;first=false;const auto op=r.logical[0];
            if(op==0x76){if(relation)return batch;relation=i;++mutations;}
            else if(op==0x71||op==0x72||op==0x73||op==0x75||op==0x79||op==0x6f)++mutations;
        }
        if(!relation||mutations!=1)return batch;batch.action=capture_before_prefix(session,records[*relation].logical);batch.valid=batch.action.has_value();return batch;
    }
    bool execute(const Batch& batch){if(!batch.valid||!batch.action){if(batch.original)consume(*batch.original);return false;}return execute(*batch.action);}
    bool execute(const Action& plan){
        const auto hold=weak_from_this().lock();if(!hold)return false;
        if(!consume(plan.original))return false;const auto session=plan.original.recipient.session;active_.insert_or_assign(session,plan.original.epoch);
        try{if(!enabled_||!unchanged(session,plan.original.lifecycle)||resolve_(session)!=std::optional{plan.original.recipient}||!unchanged(session,plan.original.lifecycle)||!host_.preflight(plan.audience)||!unchanged(session,plan.original.lifecycle)){erase_active(session,plan.original.epoch);return false;}
            const auto proof=[&]{world_proof(plan.original,plan.audience);};storage_.apply(plan.lease,{proof,proof});erase_active(session,plan.original.epoch);reconcile({plan.lease.low.guild.id,plan.lease.high.guild.id},plan.audience);return true;
        }catch(...){erase_active(session,plan.original.epoch);return false;}
    }
    std::optional<Lifecycle> capture_transfer(std::uint64_t session,const Storage::Effective::Original::Identity& target,const StoredGuildMembership& join){
        const auto hold=weak_from_this().lock();if(!hold)return {};
        try{const auto p=publication(session);if(!p)return {};auto lease=storage_.capture_transfer(authority(*p),target,join);std::vector<Storage::Effective::EffectiveLeader> all{lease.owner};all.insert(all.end(),lease.counterpart_owners.begin(),lease.counterpart_owners.end());const auto a=capture_audience(all);if(!a||lease.whole_typed!=p->view.whole||!exact_publication(*p))return {};return Lifecycle{*p,std::move(lease),*a};}catch(...){return {};}
    }
    std::optional<Lifecycle> capture_disband(std::uint64_t session){
        const auto hold=weak_from_this().lock();if(!hold)return {};
        try{const auto p=publication(session);if(!p)return {};auto lease=storage_.capture_disband(authority(*p));std::vector<Storage::Effective::EffectiveLeader> all{lease.owner};all.insert(all.end(),lease.counterpart_owners.begin(),lease.counterpart_owners.end());const auto a=capture_audience(all);if(!a||lease.whole_typed!=p->view.whole||!exact_publication(*p))return {};return Lifecycle{*p,std::move(lease),*a};}catch(...){return {};}
    }
    bool execute(const Lifecycle& plan){
        const auto hold=weak_from_this().lock();if(!hold)return false;
        if(!consume(plan.original))return false;const auto session=plan.original.recipient.session;active_.insert_or_assign(session,plan.original.epoch);
        try{if(!enabled_||!unchanged(session,plan.original.lifecycle)||resolve_(session)!=std::optional{plan.original.recipient}||!unchanged(session,plan.original.lifecycle)||!host_.preflight(plan.audience)||!unchanged(session,plan.original.lifecycle)){erase_active(session,plan.original.epoch);return false;}const auto proof=[&]{world_proof(plan.original,plan.audience);};storage_.apply_lifecycle(plan.lease,{proof,proof});erase_active(session,plan.original.epoch);std::set<std::uint64_t> guilds{plan.lease.owner.guild.id};for(const auto& other:plan.lease.counterpart_owners)guilds.insert(other.guild.id);reconcile(guilds,plan.audience);return true;}catch(...){erase_active(session,plan.original.epoch);return false;}
    }
    enum class NeighborKind {Approve,Reject,Leave,Kick,Appoint,Demote};
    struct NeighborPlan {
        Published original;NeighborKind kind;std::uint8_t slot{};
        Neighboring::Original::Identity target;
        std::optional<Neighboring::Original::Application> application;
        std::optional<StoredGuildMembership> join;Audience audience;
        bool operator==(const NeighborPlan&)const=default;
    };
    struct NeighborIndexed {std::size_t index{};std::vector<std::uint8_t> logical;};
    struct NeighborCaptured {std::size_t index{};std::optional<NeighborPlan> plan;};
    struct NeighborBatch {bool structurally_valid{};std::optional<Published> original;std::vector<NeighborCaptured> actions;};
    NeighborBatch capture_neighbors_before_any_prefix(std::uint64_t session,std::span<const NeighborIndexed> records){
        NeighborBatch batch;const auto hold=weak_from_this().lock();if(!hold)return batch;
        batch.original=member_publication(session);std::size_t previous=0;bool first=true;
        for(const auto& item:records){
            if((!first&&item.index<=previous)||item.logical.size()!=2||(item.logical[0]!=0x71&&item.logical[0]!=0x72&&item.logical[0]!=0x73))return batch;
            previous=item.index;first=false;
        }
        batch.structurally_valid=true;
        for(const auto& item:records){auto plan=capture_neighbor(session,item.logical);if(!batch.original||!plan||plan->original!=*batch.original)plan.reset();batch.actions.push_back({item.index,std::move(plan)});}
        return batch;
    }
    bool reject_neighbor_batch(const NeighborBatch& batch){if(batch.original)consume(*batch.original);return false;}
    bool execute_neighbor_item(const NeighborBatch& batch,std::size_t ordinal){
        if(!batch.structurally_valid||ordinal>=batch.actions.size()||!batch.actions[ordinal].plan)return reject_neighbor_batch(batch);
        return execute(*batch.actions[ordinal].plan);
    }
    // Only trusted GAME ingress supplies the whole original two-byte native
    // grammar. Capture is before any prefix; no fresh authorization after SQL.
    std::optional<NeighborPlan> capture_neighbor(std::uint64_t session,std::span<const std::uint8_t> raw){
        const auto hold=weak_from_this().lock();if(!hold)return {};
        try{const auto p=member_publication(session);if(!p||!neighboring_||raw.size()!=2)return {};
            const auto& state=p->panel.previous.state;const auto slot=raw[1];
            if(slot>=state.rows.size()||slot>=p->panel.previous.contract.rows.size())return {};
            const auto& row=state.rows[slot];const auto role=p->panel.previous.contract.rows[slot].role;
            const bool founder=p->view.leader.owner.account_id==p->recipient.account&&p->view.leader.owner.character_id==p->recipient.character;
            std::optional<NeighborKind> kind;std::optional<Neighboring::Original::Application> application;
            std::optional<StoredGuildMembership> join;
            if(!row.membership_revision){
                if(!founder||!slot||role!=0||(raw[0]!=0x71&&raw[0]!=0x72))return {};
                const auto at=std::find_if(state.applications.begin(),state.applications.end(),[&](const auto& a){return a.applicant==row;});
                if(at==state.applications.end())return {};application=*at;kind=raw[0]==0x71?NeighborKind::Approve:NeighborKind::Reject;
            }else{
                const auto& guild=p->view.leader.guild;join=StoredGuildMembership{guild.id,guild.name_utf8,guild.revision,row.membership_revision};
                if(raw[0]==0x73&&!slot&&(role==1||role==2)&&row.account_id==p->recipient.account&&row.character_id==p->recipient.character)kind=NeighborKind::Leave;
                else if(founder&&slot&&raw[0]==0x72&&role==1)kind=NeighborKind::Kick;
                else if(founder&&slot&&raw[0]==0x71&&role==1)kind=NeighborKind::Appoint;
                else if(founder&&slot&&raw[0]==0x72&&role==2)kind=NeighborKind::Demote;
                else return {};
            }
            const auto audience=capture_audience({p->view.leader});if(!audience||member_publication(session)!=p)return {};
            auto target=row;target.membership_revision=0;
            return NeighborPlan{*p,*kind,slot,target,application,join,*audience};
        }catch(...){return {};}
    }
    bool execute(const NeighborPlan& plan){
        const auto hold=weak_from_this().lock();if(!hold||!neighboring_)return false;
        const auto session=plan.original.recipient.session;
        try{
            const auto opcode=plan.kind==NeighborKind::Leave?std::uint8_t{0x73}:plan.kind==NeighborKind::Approve||plan.kind==NeighborKind::Appoint?std::uint8_t{0x71}:std::uint8_t{0x72};
            const std::array<std::uint8_t,2> raw{opcode,plan.slot};
            if(member_publication(session)!=std::optional{plan.original})return false;
            if(capture_neighbor(session,raw)!=std::optional{plan}){consume(plan.original);return false;}
            if(!consume(plan.original))return false;active_.insert_or_assign(session,plan.original.epoch);
            if(!host_.preflight(plan.audience)||!unchanged(session,plan.original.lifecycle))throw DatabaseError("shared53 preSQL complete audience changed");
            const auto retained=panel_.cached(session);auto expected=plan.original.panel;expected.consumed=true;
            if(retained!=std::optional{expected})throw DatabaseError("shared53 exact consumed composite cache absent");
            const auto proof=[&]{
                if(panel_.cached(session)!=retained)throw DatabaseError("shared53 consumed cache changed");
                world_proof(plan.original,plan.audience);
                if(panel_.cached(session)!=retained)throw DatabaseError("shared53 WORLD callback changed cache");
            };
            const auto& leader=plan.original.view.leader;const auto& apps=plan.original.view.applications;
            switch(plan.kind){
            case NeighborKind::Approve:neighboring_->approve(leader,apps,plan.application.value(),{proof,proof});break;
            case NeighborKind::Reject:neighboring_->reject(leader,apps,plan.application.value(),{proof,proof});break;
            case NeighborKind::Leave:neighboring_->leave(plan.target,plan.join.value(),leader,apps,{proof,proof});break;
            case NeighborKind::Kick:neighboring_->kick(plan.target,plan.join.value(),leader,apps,{proof,proof});break;
            case NeighborKind::Appoint:neighboring_->change_officer(leader,apps,plan.target,plan.join.value(),Neighboring::Original::OfficerAction::Appoint,{proof,proof});break;
            case NeighborKind::Demote:neighboring_->change_officer(leader,apps,plan.target,plan.join.value(),Neighboring::Original::OfficerAction::RemoveOffice,{proof,proof});break;
            }
            erase_active(session,plan.original.epoch);reconcile({leader.guild.id},plan.audience);return true;
        }catch(...){erase_active(session,plan.original.epoch);return false;}
    }
    struct NoticeAction {Published original;Announcement::Snapshot announcement;Audience audience;Time opened,expires;bool operator==(const NoticeAction&)const=default;};
    std::optional<NoticeAction> capture_announcement(std::uint64_t session,Time now){
        const auto hold=weak_from_this().lock();if(!hold||!announcement_)return {};
        try{const auto at=notice_leases_.find(session);if(at==notice_leases_.end())return {};const auto action=at->second;
            if(now<action.opened||now>=action.expires||publication(session)!=std::optional{action.original}||announcement_->load(action.announcement.guild_id)!=action.announcement||!host_.preflight(action.audience))return {};
            const auto current=notice_leases_.find(session);return current!=notice_leases_.end()&&current->second==action&&exact_publication(action.original)?std::optional{action}:std::nullopt;
        }catch(...){return {};}
    }
    std::optional<Announcement::Snapshot> execute(const NoticeAction& action,const RecoveredGuildAnnouncement::Request& request,Time now){
        const auto hold=weak_from_this().lock();if(!hold||!announcement_)return {};
        const auto session=action.original.recipient.session;
        try{
            const auto at=notice_leases_.find(session);if(at==notice_leases_.end()||at->second!=action)return {};
            const auto qualified=capture_announcement(session,now)==std::optional{action};
            const auto current=notice_leases_.find(session);if(current==notice_leases_.end()||current->second!=action)return {};
            if(!qualified){consume(action.original);return {};}
            if(!consume(action.original))return {};active_.insert_or_assign(session,action.original.epoch);
            if(!host_.preflight(action.audience)||!unchanged(session,action.original.lifecycle))throw DatabaseError("Announcement53 complete audience preSQL changed");
            const auto retained=panel_.cached(session);auto expected=action.original.panel;expected.consumed=true;
            if(retained!=std::optional{expected})throw DatabaseError("Announcement53 consumed composite cache absent");
            const auto proof=[&]{if(panel_.cached(session)!=retained)throw DatabaseError("Announcement53 cache changed");world_proof(action.original,action.audience);if(panel_.cached(session)!=retained)throw DatabaseError("Announcement53 callback changed cache");};
            const auto text=RecoveredGuildAnnouncement::text_utf8(request,action.original.recipient.name_codepage);
            const auto result=announcement_->save(action.original.view.leader,action.announcement,text,{proof,proof});
            erase_active(session,action.original.epoch);reconcile({action.announcement.guild_id},action.audience);return result;
        }catch(...){erase_active(session,action.original.epoch);return {};}
    }
    // Explicit failed-save restore only. No periodic98 overwrites an editor;
    // no Panel publication or authority is created by this native98 echo.
    bool restore_announcement(std::uint64_t session){
        const auto hold=weak_from_this().lock();if(!hold||!announcement_||!send_||!context_)return false;
        const auto lifecycle=generation(session);
        try{const auto owner=resolve_(session);if(!owner||!unchanged(session,lifecycle))return false;
            const auto guild=context_(owner->account,owner->character);if(!guild||!unchanged(session,lifecycle))return false;
            const auto notice=announcement_->load(*guild);const auto raw=RecoveredGuildAnnouncement::update(RecoveredGuildAnnouncement::text_request(notice.value?notice.value->text_utf8:std::string{},owner->name_codepage));
            if(!raw||resolve_(session)!=owner||!unchanged(session,lifecycle)||announcement_->load(*guild)!=notice)return false;
            send_(*owner,*raw,[](bool){});return true;
        }catch(...){return false;}
    }
    static constexpr auto pending_lifetime=OwnedGuildMembershipConversation::lifetime; // Existing CUSTOM83 30 seconds.
    struct PendingPermit {
        Owner recipient;Storage::View view;Panel::CacheEvidence cache;
        Time opened,expires;std::uint64_t epoch{},lifecycle{};
        bool operator==(const PendingPermit&)const=default;
    };
    struct PendingPlan {PendingPermit original;Neighboring::Original::Identity actor;Neighboring::Original::Application application;Audience audience;bool operator==(const PendingPlan&)const=default;};
    std::optional<PendingPermit> pending_permit(std::uint64_t session)const{const auto at=pending_permits_.find(session);return at==pending_permits_.end()?std::nullopt:std::optional{at->second};}
    std::optional<PendingPlan> capture_pending73(std::uint64_t session,const RecoveredGuildLeave::Request& request,Time now){
        const auto hold=weak_from_this().lock();if(!hold||!neighboring_||!original_||request.slot)return {};
        try{const auto permit=pending_permit(session);if(!permit||now<permit->opened||now>=permit->expires)return {};
            const auto& p=*permit;const auto& state=p.cache.previous.state;
            if(!unchanged(session,p.lifecycle)||resolve_(session)!=std::optional{p.recipient}||!unchanged(session,p.lifecycle)||panel_.cached(session)!=std::optional{p.cache}||storage_.view(p.view.leader.guild.id,p.recipient.name_codepage==936)!=p.view)return {};
            const auto application=original_->pending(p.recipient.account,p.recipient.character);
            if(!application||state.rows.empty()||application->applicant!=state.rows.front()||application->target.id!=p.view.leader.guild.id)return {};
            // Saved applicant profile remains history. A legitimately leveled
            // current nonmember can cancel; do not overwrite saved app bytes.
            const auto actor=original_->nonmember(p.recipient.account,p.recipient.character);
            if(!host_.preflight(state.audience)||!unchanged(session,p.lifecycle)||panel_.cached(session)!=std::optional{p.cache}||pending_permit(session)!=permit)return {};
            return PendingPlan{p,actor,*application,state.audience};
        }catch(...){return {};}
    }
    void deny_pending_exact(const PendingPermit& p){const auto session=p.recipient.session;const auto at=pending_permits_.find(session);if(at!=pending_permits_.end()&&at->second==p)pending_permits_.erase(at);(void)panel_.revoke_exact(p.cache);}
    bool execute(const PendingPlan& plan,Time now){
        const auto hold=weak_from_this().lock();if(!hold||!neighboring_||!original_)return false;
        const auto& p=plan.original;const auto session=p.recipient.session;
        try{
            if(pending_permit(session)!=std::optional{p})return false;
            const auto current=capture_pending73(session,RecoveredGuildLeave::Request{0},now);
            if(pending_permit(session)!=std::optional{p})return false;
            if(current!=std::optional{plan}){deny_pending_exact(p);return false;}
            pending_permits_.erase(session);active_.insert_or_assign(session,p.epoch);(void)panel_.revoke_exact(p.cache);
            if(!host_.preflight(plan.audience)||!unchanged(session,p.lifecycle)||panel_.cached(session)!=std::optional{p.cache})throw DatabaseError("Pending73 complete immutable preSQL proof changed");
            const auto proof=[&]{
                if(!unchanged(session,p.lifecycle)||panel_.cached(session)!=std::optional{p.cache}||resolve_(session)!=std::optional{p.recipient}||!unchanged(session,p.lifecycle)||!host_.current(plan.audience)||!unchanged(session,p.lifecycle)||!active_.contains(session)||active_.at(session)!=p.epoch||panel_.cached(session)!=std::optional{p.cache})throw DatabaseError("Pending73 exact consumed pending cache/world changed");
            };
            neighboring_->cancel(plan.actor,p.view.leader,p.view.applications,plan.application,{proof,proof});
            erase_active(session,p.epoch);reconcile({p.view.leader.guild.id},plan.audience);return true;
        }catch(...){erase_active(session,p.epoch);deny_pending_exact(p);return false;}
    }
    struct PendingCaptured {std::size_t index{};RecoveredGuildLeave::Request request;std::optional<PendingPlan> plan;};
    struct PendingBatch {bool structurally_valid{};std::optional<PendingPermit> original;std::vector<PendingCaptured> actions;};
    PendingBatch capture_pending73_before_any_prefix(std::uint64_t session,std::span<const NeighborIndexed> records,Time now){
        const auto hold=weak_from_this().lock();PendingBatch batch;if(!hold)return batch;batch.original=pending_permit(session);std::vector<RecoveredGuildLeave::Request> decoded;std::size_t previous=0;bool first=true;
        for(const auto& item:records){if((!first&&item.index<=previous))return batch;previous=item.index;first=false;const auto raw=RecoveredGuildLeave::decode(item.logical);if(!raw)return batch;decoded.push_back(*raw);}
        batch.structurally_valid=true;
        for(std::size_t i=0;i<records.size();++i){auto plan=capture_pending73(session,decoded[i],now);if(!batch.original||!plan||plan->original!=*batch.original)plan.reset();batch.actions.push_back({records[i].index,decoded[i],std::move(plan)});}
        return batch;
    }
    bool execute_pending73_item(const PendingBatch& batch,std::size_t ordinal,Time now){
        if(!batch.structurally_valid||ordinal>=batch.actions.size()||!batch.actions[ordinal].plan){if(batch.original)deny_pending_exact(*batch.original);return false;}
        return execute(*batch.actions[ordinal].plan,now);
    }
    void disconnected(std::uint64_t session){
        const auto hold=weak_from_this().lock();if(!hold)return;revoke(session);const auto lifecycle=generation(session);
        const auto at=certificates_.find(session);if(at==certificates_.end())return;const auto prior=at->second;
        if(resolve_(session)||!unchanged(session,lifecycle)||!closed_||!closed_(prior.owner)||!unchanged(session,lifecycle))return;
        if(const auto c=panel_.cached(session)){if(!panel_.retire_closed(*c)||!unchanged(session,lifecycle))return;}
        const auto current=certificates_.find(session);if(current==certificates_.end()||current->second!=prior||!unchanged(session,lifecycle))return;
        certificates_.erase(session);queued_.erase(session);
    }
    bool quarantined(std::uint64_t session)const{const auto hold=weak_from_this().lock();if(!hold)return true;const auto lifecycle=generation(session);const auto at=certificates_.find(session);if(at==certificates_.end())return true;const auto prior=at->second;const auto current=resolve_(session);return !unchanged(session,lifecycle)||!current||!same_namespace(prior.owner,*current);}
private:
    struct Request {Owner owner;std::uint64_t guild{};bool help{};Storage::View observed;std::uint64_t lifecycle{};};
    struct Certificate {Owner owner;std::set<std::uint32_t> possible_ids;std::uint64_t epoch{};std::vector<Panel::CanonicalScope> possible_rosters;bool dirty{};bool operator==(const Certificate&)const=default;};
    struct Delivery {std::uint64_t ticket{};bool revoked{};std::uint64_t lifecycle{};};
    std::uint64_t generation(std::uint64_t session)const{const auto at=lifecycle_.find(session);return at==lifecycle_.end()?0:at->second;}
    std::uint64_t advance(std::uint64_t session){if(lifecycle_serial_==UINT64_MAX){lifecycle_.insert_or_assign(session,0);return 0;}const auto value=++lifecycle_serial_;lifecycle_.insert_or_assign(session,value);return value;}
    bool unchanged(std::uint64_t session,std::uint64_t value)const{return value&&generation(session)==value;}
    bool exact_publication(const Published& p)const{const auto at=publications_.find(p.recipient.session);return unchanged(p.recipient.session,p.lifecycle)&&at!=publications_.end()&&at->second==p;}
    bool delivery_current(std::uint64_t session,std::uint64_t ticket,std::uint64_t lifecycle)const{const auto at=pending_.find(session);return unchanged(session,lifecycle)&&at!=pending_.end()&&at->second.ticket==ticket&&at->second.lifecycle==lifecycle&&!at->second.revoked;}
    void erase_active(std::uint64_t session,std::uint64_t epoch){const auto at=active_.find(session);if(at!=active_.end()&&at->second==epoch)active_.erase(at);}
    static bool same_namespace(const Owner& a,const Owner& b){return Panel::same_native_namespace(a,b);}
    static Storage::Authority authority(const Published& p){return {p.recipient.session,p.recipient.account,p.recipient.character,p.recipient.world_generation,p.recipient.position_revision,p.recipient.battle_generation,p.epoch,p.recipient.name_codepage,p.view.leader.owner.account_slot,true};}
    bool certificate(const Owner& owner){
        const auto at=certificates_.find(owner.session);if(at!=certificates_.end()&&same_namespace(at->second.owner,owner))return true;
        if(!baseline_)return false;const auto lifecycle=generation(owner.session);const auto baseline=baseline_(owner);
        if(!unchanged(owner.session,lifecycle)||!baseline||baseline->recipient!=owner||baseline->rows.size()>50)return false;
        const bool observed=baseline->origin==Baseline::Origin::ReceiverObservation&&baseline->roster_empty_verified;
        const bool ordered=baseline->origin==Baseline::Origin::OrderedNativeReset&&baseline->rows.empty();
        if(!observed&&!ordered)return false;
        // A fresh ordered reset replaces old namespace debt only after all
        // eleven original-native reset chunks have entered this same transport.
        if(const auto old=certificates_.find(owner.session);old!=certificates_.end()){
            if(same_namespace(old->second.owner,owner))return true;
            if(!ordered)return false;
            if(const auto cache=panel_.cached(owner.session))panel_.revoke_exact(*cache);
            certificates_.erase(old);publications_.erase(owner.session);notice_leases_.erase(owner.session);pending_permits_.erase(owner.session);
        }
        std::set<std::uint32_t> ids;
        for(const auto& r:baseline->rows)if(!r.opaque_id||r.raw_type<1||r.raw_type>3||!ids.insert(r.opaque_id).second)return false;
        certificates_.emplace(owner.session,Certificate{owner,std::move(ids),0,{},false});return true;
    }
    std::optional<Audience> capture_audience(const std::vector<Storage::Effective::EffectiveLeader>& leaders){
        try{Audience result;std::set<std::uint64_t> guilds;std::map<std::uint64_t,Owner> connected;
            for(const auto& leader:leaders){if(!guilds.insert(leader.guild.id).second)continue;const auto view=storage_.view(leader.guild.id,false);if(view.leader!=leader)return {};const auto a=host_.capture(leader,view.applications);if(!a)return {};
                for(const auto& [id,r]:a->resources)if(!result.resources.emplace(id,r).second)return {};for(const auto& o:a->connected)if(!connected.emplace(o.session,o).second)return {};}
            for(const auto& [id,o]:connected){(void)id;result.connected.push_back(o);}return host_.preflight(result)?std::optional{result}:std::nullopt;
        }catch(...){return {};}
    }
    bool consume(const Published& original){
        const auto at=publications_.find(original.recipient.session);if(at==publications_.end()||at->second!=original)return false;publications_.erase(at);panel_.invalidate_exact(original.panel.previous);
        if(const auto n=notice_leases_.find(original.recipient.session);n!=notice_leases_.end()&&n->second.original==original)notice_leases_.erase(n);
        if(const auto q=queued_.find(original.recipient.session);q!=queued_.end())q->second.help=false;
        if(const auto p=pending_.find(original.recipient.session);p!=pending_.end())p->second.revoked=true;return true;
    }
    void world_proof(const Published& p,const Audience& a){
        if(!unchanged(p.recipient.session,p.lifecycle)||resolve_(p.recipient.session)!=std::optional{p.recipient}||!unchanged(p.recipient.session,p.lifecycle)||!host_.current(a)||!unchanged(p.recipient.session,p.lifecycle)||!active_.contains(p.recipient.session)||active_.at(p.recipient.session)!=p.epoch)throw DatabaseError("CUSTOM84 immutable fullOwner11/audience/consumed proof changed");
    }
    void dispatch(Request request){
        const auto session=request.owner.session;
        if(!request.guild){clear(request.owner);return;}
        if(!unchanged(session,request.lifecycle)||resolve_(session)!=std::optional{request.owner}||!unchanged(session,request.lifecycle))return;
        if(context_(request.owner.account,request.owner.character)!=std::optional{request.guild}||!unchanged(session,request.lifecycle)||!certificate(request.owner)||!unchanged(session,request.lifecycle)||serial_==UINT64_MAX)return;
        const auto current=storage_.view(request.guild,request.owner.name_codepage==936);if(current!=request.observed)request.help=false;
        auto projection=panel_.prepare_projection(session,request.guild,request.help);if(!projection||projection->state.recipient!=request.owner||!unchanged(session,request.lifecycle))return;
        const auto notice=notices_.load(request.guild);const auto text=notice.value?notice.value->text_utf8:std::string{};const auto update=RecoveredGuildAnnouncement::update(RecoveredGuildAnnouncement::text_request(text,request.owner.name_codepage));if(!update)return;
        const auto scope=Panel::canonical_scope(projection->state);if(!scope||!unchanged(session,request.lifecycle))return;auto& cert=certificates_.at(session);auto logical=std::vector<std::uint8_t>{};
        if(cert.dirty){if(std::any_of(cert.possible_rosters.begin(),cert.possible_rosters.end(),[&](const auto& old){return !Panel::same_native_self(old,*scope);}))return;for(unsigned slot=1;slot<50;++slot){const auto bytes=RecoveredGuildRoster::remove(static_cast<std::uint8_t>(slot));logical.insert(logical.end(),bytes.begin(),bytes.end());}}
        logical.insert(logical.end(),projection->logical.begin(),projection->logical.end());logical.insert(logical.end(),update->begin(),update->end());std::set<std::uint32_t> desired;
        for(const auto& row:current.rows)if(!row.opaque_id||row.raw_type<1||row.raw_type>3||!desired.insert(row.opaque_id).second)return;
        // Qualified unique CUSTOM namespace: retire every possible old ID before
        // any95 seed, so capacity50's early return cannot discard replacement.
        for(const auto id:cert.possible_ids){const auto bytes=native_relation_private::encode96(id);logical.insert(logical.end(),bytes.begin(),bytes.end());}
        for(const auto& row:current.rows){const auto bytes=native_relation_private::encode95(row);logical.insert(logical.end(),bytes.begin(),bytes.end());}
        if(logical.size()>RecoveredWorldFrame::max_logical_size||storage_.view(request.guild,request.owner.name_codepage==936)!=current||notices_.load(request.guild)!=notice||!unchanged(session,request.lifecycle))return;
        const auto ticket=++serial_;pending_.emplace(session,Delivery{ticket,false,request.lifecycle});cert.possible_ids.insert(desired.begin(),desired.end());cert.possible_rosters.push_back(*scope);cert.dirty=true;const auto epoch=cert.epoch;auto weak=weak_from_this();
        try{send_(request.owner,std::move(logical),[weak,request,projection=*projection,current,notice,desired,scope=*scope,ticket,epoch](bool accepted){if(const auto self=weak.lock())self->ack(request,projection,current,notice,desired,scope,ticket,epoch,accepted);});}
        catch(...){complete(session,ticket);/* Possible enqueue IDs remain technical debt. */}
    }
    void ack(const Request& request,const Panel::Projection& projection,const Storage::View& current,const SqliteOwnedGuildAnnouncementRepository::Snapshot& notice,const std::set<std::uint32_t>& desired,const Panel::CanonicalScope& scope,std::uint64_t ticket,std::uint64_t epoch,bool accepted){
        const auto session=request.owner.session;
        if(const auto d=pending_.find(session);d==pending_.end()||d->second.ticket!=ticket)return;
        try{
            if(!accepted||!delivery_current(session,ticket,request.lifecycle)) {complete(session,ticket);return;}
            if(resolve_(session)!=std::optional{request.owner}||!delivery_current(session,ticket,request.lifecycle)){complete(session,ticket);return;}
            const auto cert=certificates_.find(session);if(cert==certificates_.end()){complete(session,ticket);return;}const auto prior=cert->second;
            if(prior.epoch!=epoch||!same_namespace(prior.owner,request.owner)||storage_.view(request.guild,request.owner.name_codepage==936)!=current||notices_.load(request.guild)!=notice||!delivery_current(session,ticket,request.lifecycle)){complete(session,ticket);return;}
            // Clock is external too: arithmetic/readiness qualifies before any
            // panel or79 grant, then exact callback lifecycle must still match.
            const bool founder=current.leader.owner.account_id==request.owner.account&&current.leader.owner.character_id==request.owner.character;
            Time opened{};
            const bool pending_self=enabled_&&neighboring_&&original_&&!projection.state.rows.empty()&&!projection.state.rows.front().membership_revision;
            if((announcement_&&request.help&&founder)||pending_self){if(!clock_){complete(session,ticket);return;}opened=clock_();if(!delivery_current(session,ticket,request.lifecycle)||((announcement_&&request.help&&founder)&&opened>Time::max()-notice_lifetime)||(pending_self&&opened>Time::max()-pending_lifetime)){complete(session,ticket);return;}}
            const auto published=panel_.published(projection);const auto installed=panel_.cached(session);
            // published() itself invokes external readers. Revoke only THIS newly
            // installed exact cache on obsolete ACK; never a subsequent Help.
            if(!delivery_current(session,ticket,request.lifecycle)){
                if(published&&installed&&installed!=projection.previous)panel_.revoke_exact(*installed);
                complete(session,ticket);return;
            }
            const auto now=certificates_.find(session);
            if(published&&now!=certificates_.end()&&now->second==prior){
                now->second.possible_ids=desired;now->second.epoch=ticket;now->second.possible_rosters={scope};now->second.dirty=false;
                publications_.erase(session);
                if(enabled_&&request.help&&installed&&!installed->consumed&&installed->previous.contract.explicit_single_use_authority)publications_.emplace(session,Published{request.owner,current,*installed,ticket,request.lifecycle});
                notice_leases_.erase(session);pending_permits_.erase(session);
                if(pending_self&&installed&&installed->consumed&&!installed->previous.contract.explicit_single_use_authority&&!installed->previous.contract.rows.empty()&&installed->previous.contract.rows.front().role==0){
                    const auto& row=projection.state.rows.front();const auto app=std::find_if(current.applications.begin(),current.applications.end(),[&](const auto& a){return a.applicant==row;});const auto high=pending_highest_.find(session);
                    if(row.account_id==request.owner.account&&row.character_id==request.owner.character&&app!=current.applications.end()&&(high==pending_highest_.end()||installed->epoch>high->second)){
                        pending_highest_.insert_or_assign(session,installed->epoch);pending_permits_.emplace(session,PendingPermit{request.owner,current,*installed,opened,opened+pending_lifetime,ticket,request.lifecycle});
                    }
                }
                if(announcement_&&request.help&&founder){const auto p=publications_.find(session);if(p!=publications_.end())notice_leases_.emplace(session,NoticeAction{p->second,notice,projection.state.audience,opened,opened+notice_lifetime});}
            }
        }catch(...){/* Accepted but unqualified rows retain possible-ID debt. */}
        complete(session,ticket);
    }
    void complete(std::uint64_t session,std::uint64_t ticket){
        const auto at=pending_.find(session);if(at==pending_.end()||at->second.ticket!=ticket)return;pending_.erase(at);const auto q=queued_.find(session);if(q==queued_.end())return;auto request=q->second;queued_.erase(q);try{dispatch(std::move(request));}catch(...){ }
    }
    void clear(const Owner& owner){
        const auto session=owner.session;const auto lifecycle=generation(session);
        if(!unchanged(session,lifecycle)||!certificate(owner)||!unchanged(session,lifecycle)||!send_||!context_||context_(owner.account,owner.character)||!unchanged(session,lifecycle)||serial_==UINT64_MAX||pending_.contains(session)||resolve_(session)!=std::optional{owner}||!unchanged(session,lifecycle))return;
        const auto prior=panel_.prepare_clear(session);if(!unchanged(session,lifecycle))return;auto& cert=certificates_.at(session);auto roster=prior?prior->logical:std::vector<std::uint8_t>{};
        if(!prior){
            // Existing accepted-cache readiness/clear proof remains mandatory.
            // This repair concerns possibly delivered91 with NO accepted cache.
            if(panel_.cached(session))return;
            if(!cert.possible_rosters.empty()){
                const auto& first=cert.possible_rosters.front();
                if(!first.serialized_self_matches||!same_namespace(first.recipient,owner)||std::any_of(cert.possible_rosters.begin(),cert.possible_rosters.end(),[&](const auto& scope){return !Panel::same_native_self(first,scope);}))return;
                for(unsigned slot=0;slot<50;++slot){const auto bytes=RecoveredGuildRoster::remove(static_cast<std::uint8_t>(slot));roster.insert(roster.end(),bytes.begin(),bytes.end());}
            }
        }
        if(roster.empty()&&cert.possible_ids.empty())return;
        // Retire every certified possibly enqueued ID before the full roster
        // clear; native self92 may reset both caches and close guild UI.
        auto logical=std::vector<std::uint8_t>{};for(const auto id:cert.possible_ids){const auto wire=native_relation_private::encode96(id);logical.insert(logical.end(),wire.begin(),wire.end());}
        logical.insert(logical.end(),roster.begin(),roster.end());
        const auto ticket=++serial_,epoch=cert.epoch;const auto ids=cert.possible_ids;const auto scopes=cert.possible_rosters;
        pending_.emplace(session,Delivery{ticket,false,lifecycle});cert.dirty=true;auto weak=weak_from_this();
        try{send_(owner,std::move(logical),[weak,owner,prior,ticket,epoch,ids,scopes,lifecycle](bool accepted){if(auto self=weak.lock()){
            const auto session=owner.session;const auto p=self->pending_.find(session);if(p==self->pending_.end()||p->second.ticket!=ticket)return;
            try{
                if(accepted&&self->delivery_current(session,ticket,lifecycle)&&self->resolve_(session)==std::optional{owner}&&self->delivery_current(session,ticket,lifecycle)&&self->context_&&!self->context_(owner.account,owner.character)&&self->delivery_current(session,ticket,lifecycle)){
                    const auto c=self->certificates_.find(session);if(c!=self->certificates_.end()){
                        const auto snapshot=c->second;
                        if(snapshot.epoch==epoch&&snapshot.possible_ids==ids&&snapshot.possible_rosters==scopes&&same_namespace(snapshot.owner,owner)){
                            const bool cleared=prior?self->panel_.cleared(*prior):!self->panel_.cached(session);
                            const auto now=self->certificates_.find(session);
                            if(cleared&&self->delivery_current(session,ticket,lifecycle)&&now!=self->certificates_.end()&&now->second==snapshot){now->second.possible_ids.clear();now->second.epoch=ticket;now->second.possible_rosters.clear();now->second.dirty=false;self->publications_.erase(session);}
                        }
                    }
                }
            }catch(...){/* Retain exact possibly enqueued clear obligations. */}
            self->complete(session,ticket);
        }});}catch(...){complete(session,ticket);}
    }
    void reconcile(const std::set<std::uint64_t>& guilds,const Audience& audience){
        for(const auto guild:guilds)panel_.revoke_guild(guild);
        for(auto at=notice_leases_.begin();at!=notice_leases_.end();)if(guilds.contains(at->second.announcement.guild_id))at=notice_leases_.erase(at);else ++at;
        for(auto at=pending_permits_.begin();at!=pending_permits_.end();)if(guilds.contains(at->second.view.leader.guild.id))at=pending_permits_.erase(at);else ++at;
        for(auto at=publications_.begin();at!=publications_.end();)if(guilds.contains(at->second.view.leader.guild.id))at=publications_.erase(at);else ++at;
        for(const auto& owner:audience.connected){revoke(owner.session);sync(owner.session,false);}
    }
    Storage& storage_;SqliteOwnedGuildAnnouncementRepository& notices_;Panel::Resolve resolve_;Panel::ConnectionClosed closed_;Context context_;Send send_;KnownBaseline baseline_;bool enabled_{};Neighboring* neighboring_{};Announcement* announcement_{};Clock clock_;Neighboring::Original* original_{};std::map<std::uint64_t,NoticeAction> notice_leases_;std::map<std::uint64_t,PendingPermit> pending_permits_;std::map<std::uint64_t,std::uint64_t> pending_highest_;
    Host host_;Panel panel_;std::map<std::uint64_t,Certificate> certificates_;std::map<std::uint64_t,Published> publications_;std::map<std::uint64_t,std::uint64_t> active_;std::map<std::uint64_t,Delivery> pending_;std::map<std::uint64_t,Request> queued_;std::uint64_t serial_{},lifecycle_serial_{};std::map<std::uint64_t,std::uint64_t> lifecycle_;
};
}
