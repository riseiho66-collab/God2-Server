#pragma once
#include "cn/net/SharedCredentialConnection.h"
#include "cn/protocol/CnPrebornChoices.h"
#include "cn/world/CnPrebornSubjectState.h"
#include "game/SharedWorldPresence.h"
#include <functional>
#include <optional>
#include <thread>

namespace god2::cn {
//Conditional native81/83 ->actual common preborn operation ->supplied native
//A0/A1/A2/A3. Real entitlement/cost/skills/transaction/replay owner is required;
//none is manufactured from the client's displayed counts or provided here.
class SharedPrebornChoices:public std::enable_shared_from_this<SharedPrebornChoices> {
public:
    using Connection=SharedCredentialConnection;
    using Lease=SharedWorldPresence::Lease;
    using Wire=god2cn::CnPrebornChoices;
    struct Scope {
        Lease lease;
        std::uint64_t source_revision;
        Wire::Limits actual_issued_limits;
        bool operator==(const Scope&) const=default;
    };
    struct Selection {Wire::Mask mask;Wire::Words skills;};
    struct Publication {
        std::uint64_t committed_revision;
        std::vector<god2cn::Bytes> records; //Actual order/bytes, no inferred reply pairing.
    };
    class WorldOwner {
    public:
        virtual ~WorldOwner()=default;
        //Actual open operation for this lease, with an ALREADY issued nativeA0
        //and exact revision/limits. Readonly, synchronous, no default window.
        virtual std::optional<Scope> current_scope(const Lease&)=0;
        virtual bool current(const Scope&)=0;
        //Non-yielding actual shared-game rule/transaction/save/replay operation.
        //Validates every identity/choice/limit itself, not client display gates.
        //Must neither send/pump events nor return an uncommitted success.
        virtual std::optional<Publication> apply(const Scope&,const Selection&)=0;
        //Observes the REAL POST-COMMIT revision and build-qualified output:
        //all IDs, buffers, ownership, save result, order and replay quiescence.
        //Do not compare the now-obsolete pre-commit scope as current state.
        virtual bool qualify_delivery(const Scope&,const Selection&,const Publication&)=0;
    };
    enum class WindowCheck {BeforeQueue,QueueAccepted,BeforeSelection};
    struct Window {
        Scope scope;
        std::vector<god2cn::Bytes> records; //Actual initial issuer order, including exactly one A0.
        //Optional actual native recovery evidence. Operational common subject
        //authority belongs to current/apply; never require client memory access
        //or invent native UI/pointer words to open an own-server window.
        std::optional<god2cn::CnPrebornSubjectState::Snapshot> subject;
        //Same actual subject/lease/revision/native state/records and timing.
        //Readonly/non-yielding. No default ready-world native timing is implied.
        std::function<bool(WindowCheck)> current;
    };
    class WindowOwner:public WorldOwner {
    public:
        virtual std::optional<Window> prepare_window(const Lease&)=0;
        virtual bool qualify_window(const Window&,WindowCheck)=0;
        //Called inside held publication before ANY window bytes are released.
        //Only publishes the issued scope locally; must not transact/send/yield.
        virtual bool activate_window(const Window&)=0;
        virtual void abandon_window(const Scope&)=0;
    };
    static std::shared_ptr<SharedPrebornChoices> attach(const std::shared_ptr<Connection>&,
        std::shared_ptr<SharedWorldPresence>,const Lease&,WorldOwner&);
    static std::shared_ptr<SharedPrebornChoices> attach_window(const std::shared_ptr<Connection>&,
        std::shared_ptr<SharedWorldPresence>,const Lease&,WindowOwner&);
    Connection::Ingress ingress();
    bool matches_window_owner(const WindowOwner&,const Lease&) const;
    //Actual source event calls this after installation; never emits at attach.
    //A0 activation timing/entitlement/subject/capacity belongs to the issuer.
    void publish_window(Connection::Transport::Completion);
private:
    struct Pending {Scope scope;Wire::Mask mask;};
    SharedPrebornChoices(const std::shared_ptr<Connection>&,std::shared_ptr<SharedWorldPresence>,const Lease&,WorldOwner&);
    void owner() const;
    bool current() const;
    bool current_scope(const Scope&) const;
    bool window_shape(const Window&) const;
    void receive(god2cn::Bytes,Connection::Transport::Completion);
    std::thread::id thread_=std::this_thread::get_id();
    std::weak_ptr<Connection> connection_;
    std::shared_ptr<SharedWorldPresence> presence_;
    Lease lease_;
    WorldOwner& world_;
    WindowOwner* window_=nullptr;
    std::optional<Pending> pending_;
    std::optional<Scope> issued_; //Local duplicate fence; persisted replay still required.
    bool active_=false;
};
}
