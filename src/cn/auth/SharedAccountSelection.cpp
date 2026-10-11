#include "cn/auth/SharedAccountSelection.h"
#include "cn/protocol/CnCharacterSummary.h"
#include "cn/protocol/CnCatalogRoute.h"
#include <set>
#include <stdexcept>
#include <utility>

namespace god2::cn {
namespace {
bool same_common_root(const RecoveredCharacter& left,const RecoveredCharacter& right) {
    return left.id==right.id && left.account_id==right.account_id && left.slot==right.slot &&
        left.profile==right.profile && left.created_at==right.created_at &&
        left.name_codepage==right.name_codepage && left.streamer_privilege==right.streamer_privilege;
}
}
SharedAccountSelection::NativeSummary::NativeSummary(Scope scope,god2cn::Bytes record,
    std::vector<std::uint64_t> ids,std::vector<RecoveredCharacter> snapshot,Current current)
    :scope_(scope),record_(std::move(record)),character_ids_(std::move(ids)),
     account_snapshot_(std::move(snapshot)),current_(std::move(current)) {}
std::optional<SharedAccountSelection::NativeSummary> SharedAccountSelection::NativeSummary::from_native(
    Scope scope,god2cn::Bytes record,std::vector<std::uint64_t> ids,
    std::vector<RecoveredCharacter> snapshot,Current current) {
    const auto native=god2cn::CnCharacterSummary::read(record);
    if(!scope.account || scope.target.group>=64 || scope.target.server>=10 || !native ||
       ids.size()!=native->count() || !current)return std::nullopt;
    std::set<std::uint64_t> roots,active;
    std::set<std::uint8_t> slots;
    for(const auto& row:snapshot)
        if(!row.id || row.account_id!=scope.account || !roots.insert(row.id).second)return std::nullopt;
    for(unsigned index=0;index<native->count();++index) {
        const auto row=native->character(index);
        if(!row || !roots.contains(ids[index]) || !active.insert(ids[index]).second ||
           !slots.insert(row->native_slot()).second)return std::nullopt;
    }
    return NativeSummary(scope,std::move(record),std::move(ids),std::move(snapshot),std::move(current));
}
SharedAccountSelection::SharedAccountSelection(std::shared_ptr<Admission> admission,
    Admission::Grant grant,std::uint64_t session,std::string account_echo,RecoveredCharacterRepository& characters,
    std::vector<god2cn::CnAccountReplies::CatalogGroup> catalog,SummarySource source)
    :admission_(std::move(admission)),grant_(grant),account_session_(session),
     account_echo_(std::move(account_echo)),
     characters_(characters),catalog_(std::move(catalog)),source_(std::move(source)) {
    if(!admission_ || !source_ || !account_session_ || !grant_.key.account || account_echo_.empty() ||
       grant_.key.protocol!=Admission::Protocol::Mainland)
        throw std::invalid_argument("CN selection requires owned grant and native summary source");
    // Same complete catalog bounds/order as the bytes given to the client.
    // This constructor does not send a catalog or assert account success.
    (void)god2cn::CnAccountReplies::catalog(catalog_);
}
std::shared_ptr<SharedAccountSelection> SharedAccountSelection::attach(
    const std::shared_ptr<Connection>& connection,std::shared_ptr<Admission> admission,
    Admission::Grant grant,std::uint64_t session,std::string account_echo,RecoveredCharacterRepository& characters,
    std::vector<god2cn::CnAccountReplies::CatalogGroup> catalog,SummarySource source,
    Admission::Clock::time_point now) {
    if(!connection)return {};
    auto result=std::shared_ptr<SharedAccountSelection>(new SharedAccountSelection(
        admission,grant,session,std::move(account_echo),characters,std::move(catalog),std::move(source)));
    result->connection_=connection;
    // Connection independently matches grant.account to the verified identity.
    // Strong ingress ownership / weak transport ownership avoids a cycle.
    if(!connection->install_account_ingress(std::move(admission),grant,session,
        [result](god2cn::Bytes bytes,Connection::Transport::Completion done) {
            result->receive(std::move(bytes),std::move(done));
        },now))return {};
    return result;
}
const god2cn::CnAccountReplies::CatalogGroup* SharedAccountSelection::catalog_group(Admission::Target target) const {
    const auto group=std::find_if(catalog_.begin(),catalog_.end(),[target](const auto& row) {
        return row.header.index==target.group;
    });
    // Enabled bits are consumed by00443FA0; actual slots are client config.
    if(group==catalog_.end() || target.server>=group->configured_server_slots ||
       !(group->header.enabled_servers&(std::uint16_t{1}<<target.server)))return nullptr;
    for(const auto& node:group->nodes)
        if(node.endpoint.server_index==target.server)return &*group;
    return nullptr;
}
bool SharedAccountSelection::snapshot_current(const NativeSummary& value) {
    const auto owned=characters_.list_for_account(grant_.key.account);
    if(owned.size()!=value.account_snapshot_.size())return false;
    std::set<std::uint64_t> seen;
    for(const auto& row:owned) {
        if(row.account_id!=grant_.key.account || !seen.insert(row.id).second)return false;
        const auto saved=std::find_if(value.account_snapshot_.begin(),value.account_snapshot_.end(),
            [&row](const auto& item) {return item.id==row.id;});
        if(saved==value.account_snapshot_.end() || !same_common_root(row,*saved))return false;
    }
    return true;
}
bool SharedAccountSelection::qualify(Admission::Target target,const NativeSummary& value,NativeSummary::Check check) {
    if(value.scope_!=NativeSummary::Scope{grant_.key.account,target} || !value.current_ ||
       !snapshot_current(value) || !value.current_(value.scope_,check) || !snapshot_current(value))return false;
    const auto* group=catalog_group(target);
    if(!group)return false;
    const auto summary=god2cn::CnCharacterSummary::read(value.record_);
    if(!summary || value.character_ids_.size()!=summary->count())return false;
    std::set<std::uint64_t> ids;
    std::set<std::uint8_t> slots;
    for(unsigned index=0;index<summary->count();++index) {
        const auto row=summary->character(index);
        const auto id=value.character_ids_[index];
        if(!row || !id || !ids.insert(id).second || !slots.insert(row->native_slot()).second)return false;
        const auto character=std::find_if(value.account_snapshot_.begin(),value.account_snapshot_.end(),[id](const auto& item) {
            return item.id==id;
        });
        if(character==value.account_snapshot_.end() || character->account_id!=grant_.key.account)return false;
        // 0047FAA0 explicitly falls back to0047C830 when the row's route
        // is absent. Preserve the native07 bytes; an existing fallback node
        // is a concrete catalog endpoint, not fabricated character metadata.
        if(!god2cn::CnCatalogRoute::resolve(*group,target.server,row->endpoint_routing_key()))return false;
    }
    return true;
}
void SharedAccountSelection::receive(god2cn::Bytes aggregate,Connection::Transport::Completion done) {
    if(thread_!=std::this_thread::get_id())throw std::logic_error("CN selection game owner mismatch");
    if(!done)throw std::invalid_argument("CN selection completion required");
    const auto connection=connection_.lock();
    if(selection_queue_pending_ || active_name_ || !connection || connection->closing() ||
       connection->role()!=Connection::Transport::Role::Account ||
       connection->verified_account_id()!=grant_.key.account || aggregate.empty() ||
       aggregate.size()>god2cn::CnTransport::max_logical) {done(false);return;}
    if(aggregate[0]==0xd3) {
        // Scoped47F750 producer flushes one complete25-byte D3. Mixed/batched
        // name mutations remain unqualified; reject ALL bytes before a write.
        if(aggregate.size()!=god2cn::CnSelectionNameSubmission::record_size) {done(false);return;}
        receive_name(std::move(aggregate),std::move(done));return;
    }
    auto completion=std::make_shared<Connection::Transport::Completion>(std::move(done));
    const auto finish=[completion](bool accepted) {
        auto callback=std::move(*completion);
        if(callback)callback(accepted);
    };
    std::optional<Admission::QueuedSelection> ticket;
    try {
        // Transport yields aggregates. Qualify every fixed-size request/data
        // record first; malformed trailing bytes cannot cause an earlier07.
        struct Prepared {Admission::Target target;NativeSummary summary;};
        auto prepared=std::make_shared<std::vector<Prepared>>();
        bool disconnect=false;
        for(std::size_t offset=0;offset<aggregate.size();) {
            if(aggregate[offset]==0x0a) {
                const auto request=god2cn::CnAccountWire::parse_disconnect(
                    std::span<const std::uint8_t>(aggregate).subspan(offset));
                // Native0A is terminal and names this connection only. All
                // prior requests are qualified before any reply is queued.
                // Longer/nonterminated names and case-changing issuer forms
                // remain unqualified; never disconnect by a claimed name.
                if(!request || request->claimed_account()!=account_echo_) {finish(false);return;}
                disconnect=true;break;
            }
            if(aggregate.size()-offset<3) {finish(false);return;}
            const auto request=god2cn::CnAccountWire::parse_select_server(
                std::span<const std::uint8_t>(aggregate).subspan(offset,3));
            if(!request) {finish(false);return;}
            const Admission::Target target{request->group,request->server};
            if(!catalog_group(target) ||
               !admission_->account_target_allowed(grant_,account_session_,target,Admission::Clock::now())) {
                finish(false);return;
            }
            auto summary=source_(grant_.key.account,target);
            if(!summary || !qualify(target,*summary,NativeSummary::Check::Prepared)) {finish(false);return;}
            prepared->push_back({target,std::move(*summary)});
            offset+=3;
        }
        // A later source preparation may supersede a previously prepared row
        // set. Qualify every complete record again before publishing any07,
        // then retain the immutable sources through actual queue acceptance.
        for(const auto& reply:*prepared)
            if(!qualify(reply.target,reply.summary,NativeSummary::Check::BeforePublish)) {finish(false);return;}
        // No0A response is invented. With no preceding A6 there is no new
        // reply/selection attempt to publish or drain.
        if(prepared->empty()) {
            if(disconnect)connection->close();
            finish(disconnect);return;
        }
        std::vector<god2cn::Bytes> frames;frames.reserve(prepared->size());
        for(const auto& reply:*prepared)frames.push_back(reply.summary.record_);
        const auto published=std::make_shared<bool>(false);
        const auto completed=std::make_shared<bool>(false);
        // Ordered requests supersede the same grant; only the final target and
        // exact raw07/ordered common IDs become its current offer. Every prior
        // target/source was qualified, and every full07 is queued in order.
        const auto& last=prepared->back();
        const std::shared_ptr<const NativeSummary> retained_summary(prepared,&last.summary);
        ticket=admission_->begin_selection_queue(grant_,account_session_,last.target,
            last.summary.character_ids_,Admission::Clock::now(),last.summary.record_);
        if(!ticket) {finish(false);return;}
        selection_queue_pending_=true;
        const auto registry=admission_;
        connection->send_account_batch_with_publication(std::move(frames),
            [weak=weak_from_this(),registry,token=*ticket,prepared,published,retained_summary] {
                const auto self=weak.lock();
                if(!self || !self->selection_queue_pending_)return false;
                const auto current=self->connection_.lock();
                if(!current || current->closing() ||
                   current->verified_account_id()!=self->grant_.key.account ||
                   !registry->queued_selection_current(token,Admission::Clock::now()))return false;
                for(const auto& reply:*prepared)
                    if(!self->qualify(reply.target,reply.summary,NativeSummary::Check::QueueAccepted))return false;
                // Observing suppliers cannot mutate/yield. Recheck the exact
                // attempt after them; commit has no allocation or callbacks.
                if(current->closing() || !registry->commit_selection_queue(token,Admission::Clock::now()))return false;
                self->published_summary_=retained_summary;
                self->published_ticket_=token;
                *published=true;return true;
            },
            [weak=weak_from_this(),registry,token=*ticket,published,completed,
             completion,finish,disconnect](bool queued) {
                if(*completed || !*completion)return;
                *completed=true;
                const auto self=weak.lock();
                const auto current=self?self->connection_.lock():std::shared_ptr<Connection>{};
                if(self)self->selection_queue_pending_=false;
                if(!queued || !*published || !current || current->closing() ||
                   current->verified_account_id()!=self->grant_.key.account) {
                    registry->cancel_selection_queue(token);
                    if(current)current->close();
                    finish(false);return;
                }
                // A fast native peer may already have claimed this published
                // grant on its world transport. Do not revalidate a queued
                // stage here or revoke a Reserved/WorldOwned handoff.
                if(disconnect) {
                    try {current->drain_account_replies_and_close(finish);}
                    catch(...) {current->close();finish(false);}
                }else finish(true);
            });
    } catch(...) {
        if(ticket) {
            admission_->cancel_selection_queue(*ticket);
            selection_queue_pending_=false;
            connection->close();
        }
        finish(false);
    }
}
}
