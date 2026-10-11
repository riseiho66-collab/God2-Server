#include "cn/world/SharedSubjectStatusPublication.h"
#include <stdexcept>
#include <utility>

namespace god2::cn {
SharedSubjectStatusPublication::SharedSubjectStatusPublication(Qualify qualify):qualify_(std::move(qualify)) {}
void SharedSubjectStatusPublication::owner() const {
    if(thread_!=std::this_thread::get_id())throw std::logic_error("CN subject status publication game owner mismatch");
}
std::shared_ptr<SharedSubjectStatusPublication> SharedSubjectStatusPublication::create(Qualify qualify) {
    if(!qualify)return {};
    return std::shared_ptr<SharedSubjectStatusPublication>(new SharedSubjectStatusPublication(std::move(qualify)));
}
bool SharedSubjectStatusPublication::current() const {
    owner();const auto connection=connection_.lock();
    return bound_ && presence_ && connection && !connection->closing() &&
        connection->role()==Connection::Transport::Role::World &&
        connection->verified_account_id()==lease_.account && connection->world_session_id()==lease_.session &&
        connection->world_character_offered(lease_.character) && connection->world_admission_current() &&
        presence_->ready(lease_);
}
bool SharedSubjectStatusPublication::bind(const std::shared_ptr<Connection>& connection,
    std::shared_ptr<SharedWorldPresence> presence,const Lease& lease) {
    owner();if(bound_ || !connection || !presence || !lease.account || !lease.session || !lease.character)return false;
    connection_=connection;presence_=std::move(presence);lease_=lease;bound_=true;
    if(current())return true;
    bound_=false;connection_.reset();presence_.reset();lease_={};return false;
}
void SharedSubjectStatusPublication::publish(Plan supplied,Connection::Transport::Completion done) {
    owner();if(!done)throw std::invalid_argument("CN subject status publication completion required");
    if(active_) {if(const auto connection=connection_.lock())connection->close();done(false);return;}
    active_=true;
    auto completion=std::make_shared<Connection::Transport::Completion>(std::move(done));
    auto finish=[self=shared_from_this(),completion](bool queued) {
        self->owner();if(!*completion)return;
        auto done=std::move(*completion);*completion={};self->active_=false;
        if(!queued)if(const auto connection=self->connection_.lock())connection->close();
        done(queued); //Local transport acceptance only, no ACK/client acceptance claim.
    };
    try {
        if(!current() || supplied.recipient!=lease_ || !supplied.actual_event_id ||
           !supplied.actual_committed_revision || supplied.actual_records.empty() ||
           (last_attempt_ && *last_attempt_==supplied.actual_event_id)) {finish(false);return;}
        std::vector<god2cn::Bytes> bytes;
        std::size_t size=0;
        for(const auto& record:supplied.actual_records) {
            const auto raw=record.record_bytes();
            if(raw.size()>god2cn::CnTransport::max_logical-size) {finish(false);return;}
            size+=raw.size();bytes.emplace_back(raw.begin(),raw.end());
        }
        auto plan=std::make_shared<const Plan>(std::move(supplied));
        if(!current() || !qualify_(*plan,Check::BeforeQueue) || !current()) {finish(false);return;}
        //No old pre-commit native Current or client snapshot is consulted.
        //Common issuer must observe the actual new revision/save/event/replay.
        last_attempt_=plan->actual_event_id;
        const auto connection=connection_.lock();if(!connection){finish(false);return;}
        connection->send_world_batch_with_publication(std::move(bytes),
            [weak=weak_from_this(),plan] {
                const auto self=weak.lock();if(!self)return false;
                self->owner();
                return self->active_ && self->last_attempt_==plan->actual_event_id && self->current() &&
                    self->qualify_(*plan,Check::QueueAccepted) && self->current();
            },finish);
    }catch(...) {finish(false);}
}
}
