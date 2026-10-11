#pragma once
#include "cn/net/SharedCredentialConnection.h"
#include "cn/protocol/CnCharacterSummary.h"
#include "cn/protocol/CnGenericDirectoryWire.h"
#include "game/SharedWorldPresence.h"

namespace god2::cn {
// Admitted common actor ->bounded native mode0 refresh94 ->actual common
// owner ->fully supplied AF ->same CN connection. Conditional source only;
// no default supplier or invented score/sort/permission/empty success exists.
class SharedGenericDirectory:public std::enable_shared_from_this<SharedGenericDirectory> {
public:
    using Connection=SharedCredentialConnection;
    using Lease=SharedWorldPresence::Lease;
    using Request=god2cn::CnGenericDirectoryWire::Request;
    struct Publication {
        std::uint64_t source_revision;
        std::vector<god2cn::Bytes> records; // Fully supplied actual AF order and raw bytes.
    };
    class WorldOwner {
    public:
        virtual ~WorldOwner()=default;
        // Resolve from real common state, origin/identity/permissions and native
        // classification. UI conditions are context, never an authorization grant.
        virtual std::optional<Publication> resolve(const Lease&,const Request&)=0;
        // Required before queuing: real snapshot revision/permissions, actual
        // AF issuance, client destination capacity, CP936 string termination
        // (including special14 fallback), opaque fields and all state conditions.
        virtual bool qualify_delivery(const Lease&,const Request&,const Publication&)=0;
    };
    static std::shared_ptr<SharedGenericDirectory> attach(const std::shared_ptr<Connection>&,
        std::shared_ptr<SharedWorldPresence>,const Lease&,WorldOwner&);
    Connection::Ingress ingress(); // Later general ready-world dispatcher owns mixed-record splitting.
private:
    SharedGenericDirectory(const std::shared_ptr<Connection>&,std::shared_ptr<SharedWorldPresence>,const Lease&,WorldOwner&);
    void owner() const;
    bool current() const;
    bool dispatch(const Request&);
    void receive(god2cn::Bytes,Connection::Transport::Completion);
    std::thread::id thread_=std::this_thread::get_id();
    std::weak_ptr<Connection> connection_;
    std::shared_ptr<SharedWorldPresence> presence_;
    Lease lease_;
    WorldOwner& world_;
};
}
