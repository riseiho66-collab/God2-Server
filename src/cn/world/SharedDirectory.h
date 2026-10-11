#pragma once
#include "cn/net/SharedCredentialConnection.h"
#include "cn/protocol/CnDirectoryWire.h"
#include "cn/protocol/CnCharacterSummary.h"
#include "game/SharedWorldPresence.h"

namespace god2::cn {
// Actual admitted common actor ->94/A4 bounded native view ->required world
// directory authority ->fully supplied AE/B0 ->same CN transport. Conditional
// source composition only: no production authority, issuance rules or default
// response exists. Native bit0 is a presentation variant, never permission.
class SharedDirectory:public std::enable_shared_from_this<SharedDirectory> {
public:
    using Connection=SharedCredentialConnection;
    using Lease=SharedWorldPresence::Lease;
    using Request=god2cn::CnDirectoryWire::Request;
    struct Publication {
        std::uint64_t source_revision;
        std::vector<god2cn::Bytes> records; // Actual order, actual bytes; never inferred from request.
    };
    class WorldOwner {
    public:
        virtual ~WorldOwner()=default;
        // Owner performs actual common-state ownership/visibility/rules and
        // projects build-qualified native fields. Preserve all opaque request
        // bytes; a wire cursor/index/name is never a common ID or entitlement.
        virtual std::optional<Publication> resolve(const Lease&,const Request&,bool native_mode_bit0)=0;
        // Mandatory before any queued output: real data revision, permissions,
        // native row destination capacities, terminated text and opaque fields
        // must all be qualified by that source. This adapter's shape checks
        // alone do not prove safe client storage or native business rules.
        virtual bool qualify_delivery(const Lease&,const Request&,bool native_mode_bit0,const Publication&)=0;
    };
    static std::shared_ptr<SharedDirectory> attach(const std::shared_ptr<Connection>&,
        std::shared_ptr<SharedWorldPresence>,const Lease&,WorldOwner&);
    // Later ready-world dispatcher must route a homogeneous94/A4 run here;
    // other opcodes remain with that dispatcher. S2C lengths never split C2S.
    Connection::Ingress ingress();
private:
    SharedDirectory(const std::shared_ptr<Connection>&,std::shared_ptr<SharedWorldPresence>,
        const Lease&,WorldOwner&,bool native_mode);
    void owner() const;
    bool current() const;
    bool dispatch(const Request&);
    void receive(god2cn::Bytes,Connection::Transport::Completion);
    std::thread::id thread_=std::this_thread::get_id();
    std::weak_ptr<Connection> connection_;
    std::shared_ptr<SharedWorldPresence> presence_;
    Lease lease_;
    WorldOwner& world_;
    bool native_mode_;
};
}
