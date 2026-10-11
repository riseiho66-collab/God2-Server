#pragma once
#include "cn/net/SharedCredentialConnection.h"
#include "cn/protocol/CnWorldEntry.h"
#include "game/SharedWorldPresence.h"
#include "cn/world/SharedActorVisibility.h"
#include "game/SharedNativeWorldTransports.h"

namespace god2::cn {
// Initial normal/CF bootstrap only. Native0048D87x/0049282x produce
// 1F00 ->2300 ->1C(handle,0). Each record has its own queue lock; background
// 30/36 can interleave and flush. Aggregates are not individual records.
// No guessed reply pairing or default success. Actual data/control handlers,
// world publication and gameplay dispatcher are mandatory, still unhosted.
class SharedWorldReady:public std::enable_shared_from_this<SharedWorldReady> {
public:
    using Connection=SharedCredentialConnection;
    using Lease=SharedWorldPresence::Lease;
    enum class Request {Initial1F,Initial23,Background30,Background36};
    enum class PublicationCheck {BeforePublish,QueueAccepted};
    // Actual issuer/rule observation, bound to the complete request and this
    // reservation. No yield, storage write, event pumping or guessed permission.
    using Current=std::function<bool(PublicationCheck)>;
    class BootstrapResult {
    public:
        struct ActorSlice {std::size_t aggregate,offset;};
        // No output is an explicit actual-source decision, never empty success.
        static std::optional<BootstrapResult> without_output(Current);
        static std::optional<BootstrapResult> with_output(std::vector<god2cn::Bytes>,Current);
        // Required initial1C publication: each actual81-byte6F must match a
        // complete source aggregate slice and its prepared common model node.
        // An empty peer set/output is an explicit actual issuer decision.
        static std::optional<BootstrapResult> with_initial_visibility(std::vector<god2cn::Bytes>,Current,
            std::shared_ptr<SharedActorVisibility::InitialPublication>,std::vector<ActorSlice>,
            std::vector<SharedActorVisibility::OutwardRecipient>,SharedActorVisibility::OutwardCurrent);
    private:
        friend class SharedWorldReady;
        BootstrapResult(std::vector<god2cn::Bytes>,Current);
        std::vector<god2cn::Bytes> replies_;
        Current current_;
        std::shared_ptr<SharedActorVisibility::InitialPublication> initial_;
        std::vector<SharedActorVisibility::OutwardRecipient> outward_;
        SharedActorVisibility::OutwardCurrent outward_current_;
    };
    using BootstrapCompletion=std::function<void(std::optional<BootstrapResult>)>;
    // Full native request, including opaque36 bytes, survives async dispatch.
    // Supply complete actual reply aggregates and a mandatory issuer predicate.
    // The supplier prepares data; it must not send these replies itself.
    // The readiness owner publishes its next state inside the existing IO barrier.
    using Bootstrap=std::function<void(Request,god2cn::Bytes,BootstrapCompletion)>;
    // Ongoing ready-world30/36 has a distinct real authority/lifecycle contract.
    // Its publication is still owned by that source, not initial bootstrap.
    using Background=std::function<void(Request,god2cn::Bytes,Connection::Transport::Completion)>;
    using EnteredResult=BootstrapResult;
    using EnteredCompletion=BootstrapCompletion;
    // Exact original1C and common reservation reach the actual scene issuer.
    // Presence is still prepared; the source must not activate or send output.
    // It supplies both complete incoming CN models and actual outward TW/CN
    // native records. Remainder/gameplay waits for all outward queue releases.
    using Entered=std::function<void(const Lease&,god2cn::Bytes,EnteredCompletion)>;
    // Install this composition's actual gameplay/scene owners after same-lease
    // activation, inside publication. No yield, event pump, wire send or save.
    using Install=std::function<bool()>;
    static std::shared_ptr<SharedWorldReady> attach(const std::shared_ptr<Connection>&,
        std::shared_ptr<SharedWorldPresence>,const Lease&,std::shared_ptr<SharedActorVisibility>,
        Bootstrap,Entered,Install,Connection::Ingress gameplay,std::function<void()> release_world={},
        std::shared_ptr<SharedNativeWorldTransports> world_transports={});
    bool matches(const std::shared_ptr<Connection>&,std::uint64_t character,
                 const RecoveredPosition&,std::uint16_t handle) const;
    // Initial geometry and ready must reserve the same actual registry/lease,
    // including its generation. Equal map/handle values alone cannot prove it.
    bool matches_preparation(const std::shared_ptr<Connection>&,
        const std::shared_ptr<SharedWorldPresence>&,const Lease&) const;
    Connection::Ingress ingress();
private:
    friend class SharedWorldGameplay;
    enum class Stage {First1F,Then23,Then1C,Entering,InWorld,Failed};
    // Local operational budget bounds inline handler recursion, not a native
    // protocol rule. A normal bootstrap uses three records.
    struct Batch {god2cn::Bytes bytes;std::size_t cursor=0,steps=0;Connection::Transport::Completion done;};
    // Independent disconnect capsule: exact incarnation token retains only the
    // actual weak transport. Cleanup can revoke it even after Ready is gone.
    struct NativeTransportState {
        bool released=false,binding=false;
        std::optional<SharedNativeWorldTransports::Token> token;
        void release(const std::shared_ptr<SharedNativeWorldTransports>&);
    };
    SharedWorldReady(const std::shared_ptr<Connection>&,std::shared_ptr<SharedWorldPresence>,
        const Lease&,std::shared_ptr<SharedActorVisibility>,Bootstrap,Entered,Install,Connection::Ingress,
        std::shared_ptr<SharedNativeWorldTransports>);
    void owner() const;
    bool current() const;
    void receive(god2cn::Bytes,Connection::Transport::Completion);
    void consume(const std::shared_ptr<Batch>&);
    void dispatch(const std::shared_ptr<Batch>&,Request,std::size_t,Stage);
    void publish(const std::shared_ptr<Batch>&,std::optional<BootstrapResult>,Stage,Stage,
        std::optional<std::uint16_t> activate_handle);
    void fail(const std::shared_ptr<Batch>&);
    bool bind_native_transport(const std::shared_ptr<Batch>&);
    void release_native_transport(); // Registry only; always before presence cleanup.
    std::thread::id thread_=std::this_thread::get_id();
    std::weak_ptr<Connection> connection_;
    std::shared_ptr<SharedWorldPresence> presence_;
    std::shared_ptr<SharedActorVisibility> visibility_;
    std::shared_ptr<SharedNativeWorldTransports> world_transports_;
    std::shared_ptr<NativeTransportState> native_transport_=std::make_shared<NativeTransportState>();
    Lease lease_;
    Bootstrap bootstrap_;
    Entered entered_;
    Install install_;
    Connection::Ingress gameplay_;
    std::weak_ptr<Batch> active_; // Same serial ingress owner; no native timing claim.
    Stage stage_=Stage::First1F;
};
}
