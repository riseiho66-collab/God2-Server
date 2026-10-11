#include "cn/auth/SharedCredentialStage.h"
#include "cn/protocol/CnAccountReplies.h"
#include <stdexcept>
#include <utility>

namespace god2::cn {
namespace {
struct Wipe {
    std::span<std::uint8_t> bytes;
    ~Wipe(){volatile std::uint8_t* p=bytes.data();for(std::size_t i=0;i<bytes.size();++i)p[i]=0;}
};
}
SharedCredentialStage::SharedCredentialStage(SharedAccountVerifier& verifier,
    const std::shared_ptr<god2cn::CnTransportSession>& session,Verified verified)
    :verifier_(verifier),session_(session),verified_(std::move(verified)) {
    if(!session || !verified_)throw std::invalid_argument("CN shared credential stage requires transport and continuation");
}
void SharedCredentialStage::owner() const {
    if(thread_!=std::this_thread::get_id())throw std::logic_error("CN shared credential stage owner mismatch");
}
void SharedCredentialStage::cancel(){owner();cancelled_=true;}
void SharedCredentialStage::receive_raw_ui(god2cn::Bytes record,god2cn::CnTransportSession::Completion acknowledge) {
    Wipe ingress{record};owner();
    if(!acknowledge)throw std::invalid_argument("CN ingress completion required");
    const auto weak=weak_from_this();
    if(weak.expired())throw std::logic_error("CN credential stage requires shared ownership");
    const auto session=session_.lock();
    if(started_ || cancelled_ || !session || session->closing()){acknowledge(false);return;}
    const bool account=session->role()==god2cn::CnTransportSession::Role::Account;
    auto login=account?god2cn::CnAccountWire::parse_login(record):god2cn::CnAccountWire::parse_world_login(record);
    if(!login){acknowledge(false);return;}
    Wipe parsed{login->payload};started_=true;
    if(account && login->game_serial_number()>=1000){acknowledge(false);return;}
    const auto expected=account?god2cn::CnAccountWire::native_ui_login_version:
                                god2cn::CnAccountWire::native_world_login_version;
    if(login->client_version_field()!=expected) {
        session->send(god2cn::CnAccountReplies::failure(god2cn::CnAccountFailure::VersionMismatch));
        acknowledge(true);return;
    }
    std::shared_ptr<const god2cn::CnAccountWire::Login> pending(
        new god2cn::CnAccountWire::Login(*login),[](const god2cn::CnAccountWire::Login* value) {
            auto* owned=const_cast<god2cn::CnAccountWire::Login*>(value);
            {Wipe clear{owned->payload};}delete owned;
        });
    verifier_.verify_raw_ui(login->account(),login->credential(),
        [weak,pending=std::move(pending),acknowledge=std::move(acknowledge)](CredentialResult result) mutable {
            const auto self=weak.lock();
            if(!self){acknowledge(false);return;}
            self->owner();const auto transport=self->session_.lock();
            if(self->cancelled_ || !transport || transport->closing()){acknowledge(false);return;}
            try {
                switch(result.outcome) {
                case CredentialOutcome::Verified:self->verified_(result,std::move(pending),acknowledge);return;
                case CredentialOutcome::NotRegistered:
                    transport->send(god2cn::CnAccountReplies::failure(god2cn::CnAccountFailure::NotRegistered));break;
                case CredentialOutcome::Rejected:
                    transport->send(god2cn::CnAccountReplies::failure(god2cn::CnAccountFailure::CredentialRejected));break;
                case CredentialOutcome::Changed:case CredentialOutcome::Busy:case CredentialOutcome::InternalFailure:
                    acknowledge(false);return;
                }
                acknowledge(true); // Preserve queued native failure instead of dropping it on close.
            } catch(...) {acknowledge(false);}
        });
}
}
