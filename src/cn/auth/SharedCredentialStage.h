#pragma once
#include "cn/auth/SharedAccountVerifier.h"
#include "cn/net/CnTransportSession.h"
#include "cn/protocol/CnAccountWire.h"
#include <thread>

namespace god2::cn {
// Explicit raw-UI credential path only, for Account04 and World00 independently.
// Successful password verification is not account/world admission. The required
// next callback must enforce server-owned leases, catalog, roles and native
// response contracts before acknowledging or installing the next ingress stage.
class SharedCredentialStage:public std::enable_shared_from_this<SharedCredentialStage> {
public:
    using Verified=std::function<void(CredentialResult,
        std::shared_ptr<const god2cn::CnAccountWire::Login>,god2cn::CnTransportSession::Completion)>;
    SharedCredentialStage(SharedAccountVerifier&,const std::shared_ptr<god2cn::CnTransportSession>&,Verified);
    void receive_raw_ui(god2cn::Bytes,god2cn::CnTransportSession::Completion);
    void cancel();
private:
    void owner() const;
    SharedAccountVerifier& verifier_;
    std::weak_ptr<god2cn::CnTransportSession> session_;
    Verified verified_;
    std::thread::id thread_=std::this_thread::get_id();
    bool started_=false;
    bool cancelled_=false;
};
}
