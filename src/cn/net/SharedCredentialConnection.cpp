#include "cn/net/SharedCredentialConnection.h"
#include "cn/protocol/CnPreWorldCloseReply.h"
#include <stdexcept>
#include <utility>

namespace god2::cn {
struct SharedCredentialConnection::AdmissionCleanup {
    std::shared_ptr<SharedWorldAdmission> registry;
    std::optional<SharedWorldAdmission::Ticket> ticket;
    std::uint64_t account_session=0;
    std::optional<SharedWorldAdmission::Grant> unpublished_account_grant;
    std::function<void()> world_cleanup;
    void release() {
        auto cleanup=std::move(world_cleanup);
        if(cleanup)try {cleanup();}catch(...) {}
        if(registry && ticket)registry->release_world(*ticket);
        if(registry && account_session) {
            if(unpublished_account_grant)registry->revoke_pending(*unpublished_account_grant,account_session);
            registry->detach_account(account_session);
        }
        account_session=0;
        unpublished_account_grant.reset();
        ticket.reset();registry.reset();
    }
};
void SharedCredentialConnection::owner() const {
    if(thread_!=std::this_thread::get_id())throw std::logic_error("CN connection game owner mismatch");
}
std::shared_ptr<SharedCredentialConnection> SharedCredentialConnection::create(
    asio::ip::tcp::socket socket,asio::any_io_executor game,std::array<std::uint8_t,16> seed,
    Transport::Role role,std::shared_ptr<const god2cn::CnClientGroupConfiguration> configuration,
    SharedAccountVerifier& verifier,Verified verified,std::function<void()> closed) {
    if(!verified || !closed)throw std::invalid_argument("CN shared connection requires admission and cleanup controllers");
    auto result=std::shared_ptr<SharedCredentialConnection>(new SharedCredentialConnection);
    result->admission_cleanup_=std::make_shared<AdmissionCleanup>();
    std::weak_ptr<SharedCredentialConnection> weak=result;
    result->transport_=std::make_shared<Transport>(std::move(socket),std::move(game),seed,role,std::move(configuration),
        [weak] {
            if(const auto self=weak.lock()){self->owner();if(!self->closed_)self->established_=true;}
        },
        [weak](god2cn::Bytes record,Transport::Completion done) mutable {
            const auto refuse=[&] {
                volatile std::uint8_t* bytes=record.data();
                for(std::size_t i=0;i<record.size();++i)bytes[i]=0;
                done(false);
            };
            const auto self=weak.lock();
            if(!self){refuse();return;}
            self->owner();
            if(self->closed_ || !self->established_){refuse();return;}
            if(self->admitted_)self->admitted_(std::move(record),std::move(done));
            else self->stage_->receive_raw_ui(std::move(record),std::move(done));
        },
        [weak,cleanup=result->admission_cleanup_,closed=std::move(closed)] {
            if(const auto self=weak.lock()) {
                self->owner();self->closed_=true;self->stage_->cancel();self->admitted_={};
                self->verified_credential_source_.reset();
            }
            // Transport owns this cleanup even if the connection wrapper was
            // destroyed before OnClosed. A stale close cannot release a new
            // generation or another world's owner-bound ticket.
            cleanup->release();
            closed();
        });
    result->stage_=std::make_shared<SharedCredentialStage>(verifier,result->transport_,
        [weak,verified=std::move(verified)](CredentialResult account,
            std::shared_ptr<const god2cn::CnAccountWire::Login> login,Transport::Completion done) mutable {
            const auto self=weak.lock();
            if(!self){done(false);return;}
            self->owner();
            if(self->closed_ || self->credentials_verified_){done(false);return;}
            if(account.outcome!=CredentialOutcome::Verified || !account.account_id || !login ||
               !account.source || !account.source->current(account.account_id)){done(false);return;}
            self->verified_account_=account.account_id;
            self->claimed_account_=login->account_id();self->claimed_key_=login->check_key();
            self->verified_login_=login;
            self->verified_credential_source_=account.source;
            self->credentials_verified_=true;
            // A password match alone cannot release the stream into gameplay.
            // The account/world admission owner installs a real next dispatcher.
            verified(self,account,std::move(login),[weak,done=std::move(done)](bool accepted) {
                const auto current=weak.lock();
                if(!current){done(false);return;}
                current->owner();
                done(accepted && !current->closed_ && static_cast<bool>(current->admitted_));
            });
        });
    return result;
}
SharedCredentialConnection::~SharedCredentialConnection() {
    if(transport_)transport_->close();
}
void SharedCredentialConnection::start(){transport_->start();}
void SharedCredentialConnection::close(){transport_->close();}
void SharedCredentialConnection::send(god2cn::Bytes bytes){transport_->send(std::move(bytes));}
void SharedCredentialConnection::send_batch(std::vector<god2cn::Bytes> bytes,Transport::Completion queued) {
    owner();transport_->send_batch(std::move(bytes),std::move(queued));
}
void SharedCredentialConnection::drain_account_replies_and_close(Transport::Completion written) {
    owner();if(!written)throw std::invalid_argument("CN account drain completion required");
    if(closing() || role()!=Transport::Role::Account || !credentials_verified_ || !admitted_ ||
       !admission_cleanup_->registry || !admission_cleanup_->account_session) {
        close();written(false);return;
    }
    transport_->drain_and_close(std::move(written));
}
void SharedCredentialConnection::send_account_batch_with_publication(
    std::vector<god2cn::Bytes> bytes,std::function<bool()> publish,Transport::Completion queued) {
    owner();
    if(!queued)throw std::invalid_argument("CN account publication completion required");
    if(closing() || role()!=Transport::Role::Account || !credentials_verified_ || !admitted_ ||
       !publish || !admission_cleanup_->registry || !admission_cleanup_->account_session) {
        close();queued(false);return;
    }
    transport_->send_batch_with_publication(std::move(bytes),std::move(publish),std::move(queued));
}
void SharedCredentialConnection::send_world_batch_with_publication(
    std::vector<god2cn::Bytes> bytes,std::function<bool()> publish,Transport::Completion queued) {
    owner();if(!queued)throw std::invalid_argument("CN world publication completion required");
    const auto account=verified_account_id();
    const auto session=world_session_id();
    const auto current=[weak=weak_from_this(),account,session] {
        const auto self=weak.lock();if(!self)return false;
        self->owner();
        return account && session && !self->closing() && self->role()==Transport::Role::World &&
            self->verified_account_id()==account && self->world_session_id()==session &&
            self->admitted_ && self->world_admission_current();
    };
    if(!publish || !current()) {close();queued(false);return;}
    transport_->send_batch_with_publication(std::move(bytes),
        [current,publish=std::move(publish)] {return current() && publish() && current();},std::move(queued));
}
void SharedCredentialConnection::send_world_batch_with_commit(
    std::vector<god2cn::Bytes> bytes,std::function<bool()> commit,Transport::Completion queued) {
    owner();if(!queued)throw std::invalid_argument("CN world commit completion required");
    const auto account=verified_account_id();
    const auto session=world_session_id();
    const auto current=[weak=weak_from_this(),account,session] {
        const auto self=weak.lock();if(!self)return false;
        self->owner();
        return account && session && !self->closing() && self->role()==Transport::Role::World &&
            self->verified_account_id()==account && self->world_session_id()==session &&
            self->admitted_ && self->world_admission_current();
    };
    if(!commit || !current()) {close();queued(false);return;}
    // All owned callbacks and native frames are staged before this game call.
    // A false return after durable commit suppresses bytes, not the saved fact.
    transport_->send_batch_with_publication(std::move(bytes),
        [current,commit=std::move(commit)] {return current() && commit() && current();},std::move(queued));
}
void SharedCredentialConnection::close_after_native_world_reply(god2cn::Bytes reply,
    std::function<bool()> current_terminal_owner,Transport::Completion written) {
    owner();
    if(!written)throw std::invalid_argument("CN native close write continuation required");
    if(terminal_world_reply_pending_){written(false);return;}
    const auto session=world_session_id();const auto account=verified_account_id();
    bool owned=false;
    try {owned=current_terminal_owner && current_terminal_owner();}catch(...) {}
    if(closing() || role()!=Transport::Role::World || !session || !account || !world_admission_current() ||
       !owned || !god2cn::CnPreWorldCloseReply::read(reply)) {
        close();written(false);return;
    }
    std::vector<god2cn::Bytes> sequence;sequence.push_back(std::move(reply));
    auto completion=std::make_shared<Transport::Completion>(std::move(written));
    auto finish=[completion](bool accepted) {
        if(!*completion)return;auto done=std::move(*completion);*completion={};done(accepted);
    };
    terminal_world_reply_pending_=true;
    try {
        send_batch(std::move(sequence),[weak=weak_from_this(),session,account,finish,
                                      current_terminal_owner=std::move(current_terminal_owner)](bool queued) {
            const auto self=weak.lock();
            bool owned=false;
            try {owned=current_terminal_owner && current_terminal_owner();}catch(...) {}
            if(!queued || !self || self->closing() || self->world_session_id()!=session ||
               self->verified_account_id()!=account || !self->world_admission_current() || !owned) {
                if(self)self->close();finish(false);return;
            }
            // Hold this transport, not another account/world connection. Its
            // existing ticket-bound OnClosed owns all admission cleanup.
            try {self->transport_->drain_and_close(finish);}catch(...) {self->close();finish(false);}
        });
    }catch(...) {close();finish(false);}
}
bool SharedCredentialConnection::install_account_ingress(
    std::shared_ptr<SharedWorldAdmission> registry,const SharedWorldAdmission::Grant& grant,
    std::uint64_t session,Ingress ingress,SharedWorldAdmission::Clock::time_point now) {
    owner();
    if(closed_ || transport_->closing() || transport_->role()!=Transport::Role::Account ||
       !credentials_verified_ || admitted_ || !ingress || !registry || !session ||
       grant.key.protocol!=SharedWorldAdmission::Protocol::Mainland ||
       !registry->account_owned(grant,session,verified_account_,now))return false;
    admission_cleanup_->registry=std::move(registry);admission_cleanup_->account_session=session;
    admission_cleanup_->unpublished_account_grant=grant;
    admitted_=std::move(ingress);
    return true;
}
bool SharedCredentialConnection::confirm_account_success_queue(
    const SharedWorldAdmission::Grant& grant,std::uint64_t session,SharedWorldAdmission::Clock::time_point now) {
    owner();const auto& pending=admission_cleanup_->unpublished_account_grant;
    if(closing() || transport_->role()!=Transport::Role::Account || !credentials_verified_ || !admitted_ ||
       !admission_cleanup_->registry || !pending || !session || admission_cleanup_->account_session!=session ||
       pending->key!=grant.key || pending->generation!=grant.generation ||
       !admission_cleanup_->registry->account_owned(grant,session,verified_account_,now))return false;
    admission_cleanup_->unpublished_account_grant.reset();return true;
}
bool SharedCredentialConnection::account_success_current(
    const SharedWorldAdmission::Grant& grant,std::uint64_t session,SharedWorldAdmission::Clock::time_point now) const {
    owner();
    return !closing() && transport_->role()==Transport::Role::Account && credentials_verified_ && admitted_ &&
        admission_cleanup_->registry && session && admission_cleanup_->account_session==session &&
        !admission_cleanup_->unpublished_account_grant && grant.key.protocol==SharedWorldAdmission::Protocol::Mainland &&
        admission_cleanup_->registry->account_owned(grant,session,verified_account_,now);
}
bool SharedCredentialConnection::install_world_ingress(
    std::shared_ptr<SharedWorldAdmission> registry,std::uint64_t session,
    SharedWorldAdmission::Target endpoint,Ingress ingress,SharedWorldAdmission::Clock::time_point now) {
    owner();
    if(closed_ || transport_->closing() || transport_->role()!=Transport::Role::World ||
       !credentials_verified_ || admitted_ || !ingress || !registry || !session ||
       claimed_account_!=verified_account_ || endpoint.group>=64 || endpoint.server>=10)
        return false;
    // Grant selection and actual endpoint provide destination authority. A9's
    // group writes are qualified in the transfer and00445B40 producers; A9 is
    // not imposed as
    // a blanket normal-world precondition without a matching producer trace.
    const SharedWorldAdmission::Key key{SharedWorldAdmission::Protocol::Mainland,claimed_account_,claimed_key_};
    const auto ticket=registry->reserve(key,verified_account_,session,endpoint,now);
    if(!ticket)return false;
    if(!registry->commit(*ticket,now)) {
        registry->cancel_reservation(*ticket);return false;
    }
    admission_cleanup_->registry=std::move(registry);admission_cleanup_->ticket=*ticket;
    admitted_=std::move(ingress);
    return true;
}
bool SharedCredentialConnection::world_character_offered(std::uint64_t character) const {
    owner();
    if(closing() || transport_->role()!=Transport::Role::World || !credentials_verified_ ||
       !admitted_ || !admission_cleanup_->registry || !admission_cleanup_->ticket)return false;
    return admission_cleanup_->registry->character_offered(*admission_cleanup_->ticket,character);
}
std::uint64_t SharedCredentialConnection::world_session_id() const {
    owner();
    if(closing() || !admission_cleanup_->ticket || transport_->role()!=Transport::Role::World)return 0;
    return admission_cleanup_->ticket->world_session;
}
std::optional<SharedWorldAdmission::OfferSource> SharedCredentialConnection::world_offer_source() const {
    owner();
    if(closing() || transport_->role()!=Transport::Role::World || !credentials_verified_ ||
       !admitted_ || !admission_cleanup_->registry || !admission_cleanup_->ticket)return std::nullopt;
    return admission_cleanup_->registry->offered_source(*admission_cleanup_->ticket);
}
bool SharedCredentialConnection::world_admission_current() const {
    owner();
    return !closing() && transport_->role()==Transport::Role::World && credentials_verified_ && admitted_ &&
        admission_cleanup_->registry && admission_cleanup_->ticket &&
        admission_cleanup_->registry->world_owned(*admission_cleanup_->ticket);
}
bool SharedCredentialConnection::install_world_cleanup(std::function<void()> cleanup) {
    owner();
    if(!cleanup || !world_session_id() || admission_cleanup_->world_cleanup)return false;
    admission_cleanup_->world_cleanup=std::move(cleanup);return true;
}
std::uint32_t SharedCredentialConnection::verified_account_id() const {
    owner();return credentials_verified_ && !closing()?verified_account_:0;
}
bool SharedCredentialConnection::owns_verified_login(
    const std::shared_ptr<const god2cn::CnAccountWire::Login>& request) const {
    owner();return request && credentials_verified_ && !closing() && verified_login_.lock()==request;
}
std::shared_ptr<const VerifiedCredentialSource> SharedCredentialConnection::retain_verified_credentials(
    const std::shared_ptr<const god2cn::CnAccountWire::Login>& request) const {
    owner();const auto source=verified_credential_source_.lock();
    return verified_credentials_current(source,request)?source:nullptr;
}
std::shared_ptr<const god2cn::CnAccountWire::Login> SharedCredentialConnection::retain_verified_login_for_publication() const {
    owner();const auto request=verified_login_.lock();
    return verified_credentials_current(verified_credential_source_.lock(),request)?request:nullptr;
}
bool SharedCredentialConnection::verified_credentials_current(
    const std::shared_ptr<const VerifiedCredentialSource>& source,
    const std::shared_ptr<const god2cn::CnAccountWire::Login>& request) const {
    owner();return source && owns_verified_login(request) && verified_credential_source_.lock()==source &&
        source->current(verified_account_);
}
}
