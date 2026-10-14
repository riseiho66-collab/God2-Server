#include "cn/world/SharedPrebornChoices.h"
#include <stdexcept>
#include <utility>

namespace god2::cn {
SharedPrebornChoices::SharedPrebornChoices(const std::shared_ptr<Connection>& connection,
    std::shared_ptr<SharedWorldPresence> presence,const Lease& lease,WorldOwner& world)
    :connection_(connection),presence_(std::move(presence)),lease_(lease),world_(world) {}
void SharedPrebornChoices::owner() const {
    if(thread_!=std::this_thread::get_id())throw std::logic_error("CN preborn choices game owner mismatch");
}
bool SharedPrebornChoices::current() const {
    const auto connection=connection_.lock();
    const auto local=[&] {
        // Pure connection/admission/offer/full-Lease registry checks. The one
        // original ownership observer below may retire any of these sources.
        return connection && !connection->closing() && connection->role()==Connection::Transport::Role::World &&
            connection->world_session_id()==lease_.session && connection->verified_account_id()==lease_.account &&
            connection->world_admission_current() && connection->world_character_offered(lease_.character) &&
            presence_->retained_ready_current(lease_);
    };
    return local() && presence_->ready(lease_) && local();
}
bool SharedPrebornChoices::current_scope(const Scope& scope) const {
    return scope.lease==lease_ && scope.source_revision && current() && world_.current(scope) && current();
}
std::shared_ptr<SharedPrebornChoices> SharedPrebornChoices::attach(const std::shared_ptr<Connection>& connection,
    std::shared_ptr<SharedWorldPresence> presence,const Lease& lease,WorldOwner& world) {
    if(!connection || !presence)return {};
    auto self=std::shared_ptr<SharedPrebornChoices>(new SharedPrebornChoices(connection,std::move(presence),lease,world));
    self->owner();return self->current()?self:std::shared_ptr<SharedPrebornChoices>{};
}
std::shared_ptr<SharedPrebornChoices> SharedPrebornChoices::attach_window(const std::shared_ptr<Connection>& connection,
    std::shared_ptr<SharedWorldPresence> presence,const Lease& lease,WindowOwner& world) {
    auto self=attach(connection,std::move(presence),lease,world);
    if(self)self->window_=&world;
    return self;
}
bool SharedPrebornChoices::window_shape(const Window& window) const {
    if(window.scope.lease!=lease_ || !window.scope.source_revision || !window.current ||
       window.records.empty() || window.records.size()>256)return false;
    if(window.subject && (window.subject->scope().actual_revision!=window.scope.source_revision ||
       !window.subject->retained_selection() || !window.subject->current()))return false;
    std::size_t size=0,a0=0;
    for(const auto& record:window.records) {
        if(record.size()>god2cn::CnTransport::max_logical-size || !Wire::supported_reply(record))return false;
        size+=record.size();
        if(record[0]==0xA0) {
            const auto limits=Wire::read_limits(record);
            if(!limits || *limits!=window.scope.actual_issued_limits || ++a0!=1)return false;
        }
    }
    return a0==1; //Scope association, not a default A0/A1/A2/A3 ordering/rule.
}
bool SharedPrebornChoices::matches_window_owner(const WindowOwner& world,const Lease& lease) const {
    owner();return window_==&world && lease_==lease && current();
}
void SharedPrebornChoices::publish_window(Connection::Transport::Completion done) {
    owner();if(!done)throw std::invalid_argument("CN preborn window completion required");
    if(active_) {if(const auto connection=connection_.lock())connection->close();done(false);return;}
    active_=true;
    auto completion=std::make_shared<Connection::Transport::Completion>(std::move(done));
    auto prepared=std::make_shared<std::optional<Window>>();
    auto published=std::make_shared<bool>(false);
    auto finish=[self=shared_from_this(),completion,prepared,published](bool queued) {
        self->owner();if(!*completion)return;
        auto done=std::move(*completion);*completion={};self->active_=false;
        if(!queued || !*published) {
            if(self->window_ && *prepared)try {self->window_->abandon_window((**prepared).scope);}catch(...) {}
            if(const auto connection=self->connection_.lock())connection->close();
            done(false);return;
        }
        done(true); //Local publication only; no native acceptance claim.
    };
    try {
        if(!window_ || pending_ || !current()){finish(false);return;}
        *prepared=window_->prepare_window(lease_);
        if(!*prepared || !window_shape(**prepared) ||
           (issued_ && *issued_==(**prepared).scope) || !current() ||
           !window_->qualify_window(**prepared,WindowCheck::BeforeQueue) || !current()) {
            finish(false);return;
        }
        const auto connection=connection_.lock();if(!connection){finish(false);return;}
        connection->send_world_batch_with_publication((**prepared).records,
            [self=shared_from_this(),prepared,published] {
                self->owner();if(*published || !*prepared || !self->current() || self->pending_ ||
                   !self->window_->qualify_window(**prepared,WindowCheck::QueueAccepted) || !self->current())return false;
                if(!self->window_->activate_window(**prepared) || !self->current())return false;
                *published=true;return true;
            },finish);
        //No prepared revision check after release. A real later operation may
        //already have advanced the common state before local completion.
    }catch(...) {finish(false);}
}
SharedPrebornChoices::Connection::Ingress SharedPrebornChoices::ingress() {
    owner();return [self=shared_from_this()](god2cn::Bytes bytes,Connection::Transport::Completion done) {
        self->receive(std::move(bytes),std::move(done));
    };
}
void SharedPrebornChoices::receive(god2cn::Bytes bytes,Connection::Transport::Completion done) {
    owner();if(!done)throw std::invalid_argument("CN preborn choices completion required");
    if(active_) {if(const auto connection=connection_.lock())connection->close();done(false);return;}
    active_=true;
    auto completion=std::make_shared<Connection::Transport::Completion>(std::move(done));
    auto finish=[self=shared_from_this(),completion](bool queued) {
        self->owner();if(!*completion)return;
        auto done=std::move(*completion);*completion={};self->active_=false;
        if(!queued)if(const auto connection=self->connection_.lock())connection->close();
        done(queued); //Local source/output acceptance, never a fabricated wire ACK.
    };
    try {
        const auto request=Wire::read_request(bytes);
        if(!request || !current()){finish(false);return;}
        if(const auto mask=std::get_if<Wire::Mask>(&*request)) {
            if(pending_){finish(false);return;}
            const auto scope=world_.current_scope(lease_);
            if(!scope || (issued_ && *issued_==*scope) || !current_scope(*scope)){finish(false);return;}
            //81 stages only this native operation. No gameplay mutation/output.
            pending_=Pending{*scope,*mask};finish(true);return;
        }
        const auto words=std::get_if<Wire::Words>(&*request);
        if(!words || !pending_ || !current_scope(pending_->scope)){finish(false);return;}
        const auto scope=pending_->scope;
        const Selection selection{pending_->mask,*words};
        pending_.reset();issued_=scope; //Designate before actual operation, no local retry.
        auto supplied=world_.apply(scope,selection);
        if(!supplied || !supplied->committed_revision || supplied->records.empty() || !current()) {
            finish(false);return;
        }
        std::size_t size=0;
        for(const auto& record:supplied->records) {
            if(record.size()>god2cn::CnTransport::max_logical-size || !Wire::supported_reply(record)) {
                finish(false);return;
            }
            size+=record.size();
        }
        //POST-COMMIT qualification, not world_.current(old pre-commit scope).
        //A missing native issuer/rule/save owner leaves this branch unavailable.
        auto publication=std::make_shared<const Publication>(std::move(*supplied));
        if(!world_.qualify_delivery(scope,selection,*publication) || !current()){finish(false);return;}
        const auto connection=connection_.lock();if(!connection){finish(false);return;}
        const auto weak=weak_from_this();
        connection->send_world_batch_with_publication(publication->records,[weak,scope,selection,publication] {
            const auto self=weak.lock();
            return self && self->current() && self->world_.qualify_delivery(scope,selection,*publication) && self->current();
        },finish);
    }catch(...) {finish(false);}
}
}
