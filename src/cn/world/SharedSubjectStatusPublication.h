#pragma once
#include "cn/protocol/CnSubjectStatus31.h"
#include "cn/net/SharedCredentialConnection.h"
#include "game/SharedWorldPresence.h"
#include <functional>
#include <thread>
#include <vector>

namespace god2::cn {
// Actual committed common event ->recipient-native WORLD31 publication source.
// Bind at the same1C installation, emit only from the actual common issuer.
// Does not create a game rule, mutate/save a subject or invent C2S31 causality.
class SharedSubjectStatusPublication final:public std::enable_shared_from_this<SharedSubjectStatusPublication> {
public:
    using Connection=SharedCredentialConnection;
    using Lease=SharedWorldPresence::Lease;
    using Wire=god2cn::CnSubjectStatus31;
    struct Plan {
        Lease recipient;
        std::uint64_t actual_event_id,actual_committed_revision;
        std::vector<Wire> actual_records; //Native order/bytes retained, including unconsumed bytes.
    };
    enum class Check {BeforeQueue,QueueAccepted};
    // Required readonly/non-yielding actual post-commit common owner. Qualifies
    // the real subject/recipient mapping, native signed-WORD FIRST roster hit,
    // all fields/current state, rules/save/durable replay/event/order/revision.
    // Raw native identifiers cannot supply their own common authority. No
    // client process memory/pointers/Snapshot required for own-server output.
    using Qualify=std::function<bool(const Plan&,Check)>;
    static std::shared_ptr<SharedSubjectStatusPublication> create(Qualify);
    bool bind(const std::shared_ptr<Connection>&,std::shared_ptr<SharedWorldPresence>,const Lease&);
    void publish(Plan,Connection::Transport::Completion);
private:
    explicit SharedSubjectStatusPublication(Qualify);
    void owner() const;
    bool current() const;
    Qualify qualify_;
    std::thread::id thread_=std::this_thread::get_id();
    std::weak_ptr<Connection> connection_;
    std::shared_ptr<SharedWorldPresence> presence_;
    Lease lease_{};
    bool bound_=false,active_=false;
    std::optional<std::uint64_t> last_attempt_; //Local fence; actual durable replay is required.
};
}
