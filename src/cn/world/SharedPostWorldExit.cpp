#include "cn/world/SharedPostWorldExit.h"
#include <stdexcept>
#include <utility>

namespace god2::cn {
SharedPostWorldExit::Reply::Reply(Scope scope,std::array<std::uint8_t,3> record,Current current)
    :scope_(std::move(scope)),record_(record),current_(std::move(current)) {}
std::optional<SharedPostWorldExit::Reply> SharedPostWorldExit::Reply::from_native(
    Scope scope,std::span<const std::uint8_t> record,Current current) {
    const auto native=god2cn::CnPreWorldCloseReply::read(record);
    if(!native || !current || !scope.lease.session || !scope.lease.account ||
       !scope.lease.character || !scope.lease.generation)return std::nullopt;
    switch(scope.form) {
    case Form::Native0:case Form::Native1:case Form::Native2:break;
    default:return std::nullopt;
    }
    return Reply(std::move(scope),native->record_bytes(),std::move(current));
}
bool SharedPostWorldExit::Reply::current(const Scope& scope) const {
    return scope==scope_ && current_ && current_(scope_);
}
SharedPostWorldExit::SharedPostWorldExit(const std::shared_ptr<Connection>& connection,
    std::shared_ptr<SharedWorldPresence> presence,const Lease& lease,Source source)
    :connection_(connection),presence_(std::move(presence)),lease_(lease),source_(std::move(source)) {}
void SharedPostWorldExit::owner() const {
    if(thread_!=std::this_thread::get_id())throw std::logic_error("CN post-world exit game owner mismatch");
}
bool SharedPostWorldExit::current() const {
    const auto connection=connection_.lock();
    return connection && !connection->closing() && connection->role()==Connection::Transport::Role::World &&
        connection->world_session_id()==lease_.session && connection->verified_account_id()==lease_.account &&
        connection->world_admission_current() && connection->world_character_offered(lease_.character) &&
        presence_->ready(lease_);
}
bool SharedPostWorldExit::terminal_current(const Scope& scope) const {
    owner();return terminal_scope_ && *terminal_scope_==scope && scope.lease==lease_ && current() &&
        presence_->saved_position(lease_)==std::optional{scope.saved_position};
}
std::shared_ptr<SharedPostWorldExit> SharedPostWorldExit::attach(const std::shared_ptr<Connection>& connection,
    std::shared_ptr<SharedWorldPresence> presence,const Lease& lease,Source source) {
    if(!connection || !presence || !source)return {};
    auto self=std::shared_ptr<SharedPostWorldExit>(new SharedPostWorldExit(connection,std::move(presence),lease,std::move(source)));
    self->owner();if(!self->current())return {};return self;
}
SharedPostWorldExit::Connection::Ingress SharedPostWorldExit::ingress() {
    owner();return [self=shared_from_this()](god2cn::Bytes bytes,Connection::Transport::Completion done) {
        self->receive(std::move(bytes),std::move(done));
    };
}
void SharedPostWorldExit::receive(god2cn::Bytes bytes,Connection::Transport::Completion done) {
    owner();if(!done)throw std::invalid_argument("CN post-world exit completion required");
    auto completion=std::make_shared<Connection::Transport::Completion>(std::move(done));
    auto finish=[completion](bool written) {
        if(!*completion)return;auto done=std::move(*completion);*completion={};done(written);
    };
    const auto connection=connection_.lock();
    try {
        const auto control=god2cn::CnPostWorldExitControl::read(bytes);
        if(!control || terminal_scope_ || !current()) {
            if(connection)connection->close();finish(false);return;
        }
        const auto position=presence_->saved_position(lease_);
        if(!position){connection->close();finish(false);return;}
        //Designate BEFORE any supplier callback. No second source/retry scope.
        const Scope scope{lease_,*position,control->form};terminal_scope_=scope;
        auto supplied=source_(scope);
        if(!supplied || !terminal_current(scope) || !supplied->current(scope) || !terminal_current(scope)) {
            connection->close();finish(false);return;
        }
        auto reply=std::make_shared<const Reply>(std::move(*supplied));
        const auto weak=weak_from_this();
        connection->close_after_native_world_reply(god2cn::Bytes(reply->record_.begin(),reply->record_.end()),
            [weak,scope,reply] {
                const auto self=weak.lock();
                return self && self->terminal_current(scope) && reply->current(scope) && self->terminal_current(scope);
            },finish);
        //Drain completion runs with a closing transport and may follow cleanup.
        //Do not recheck an obsolete ready/position source after output release.
        //Existing OnClosed owns generation-qualified admission/scene cleanup.
    }catch(...) {if(connection)connection->close();finish(false);}
}
}
