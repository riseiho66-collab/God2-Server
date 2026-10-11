#pragma once
#include "cn/net/SharedCredentialConnection.h"
#include "cn/protocol/CnPostWorldExitControl.h"
#include "cn/protocol/CnPreWorldCloseReply.h"
#include "game/SharedWorldPresence.h"
#include <array>
#include <functional>
#include <memory>
#include <optional>
#include <span>
#include <thread>

namespace god2::cn {
//Ready world exit is independent from pre-world create/delete. Real gameplay
//rules/pending saves/quiescence and complete native03 must come from its owner.
class SharedPostWorldExit:public std::enable_shared_from_this<SharedPostWorldExit> {
public:
    using Connection=SharedCredentialConnection;
    using Lease=SharedWorldPresence::Lease;
    using Form=god2cn::CnPostWorldExitControl::Form;
    struct Scope {
        Lease lease;
        RecoveredPosition saved_position;
        Form form;
        bool operator==(const Scope&) const=default;
    };
    class Reply {
    public:
        using Current=std::function<bool(const Scope&)>;
        //Complete3 bytes, including both opaque payload bytes; no generic ACK.
        //Source must qualify actual rule/operation/save/replay quiescence.
        //Non-yielding observation; owns captured lifetimes, no sends/events.
        static std::optional<Reply> from_native(Scope,std::span<const std::uint8_t>,Current);
        Reply(const Reply&)=delete;
        Reply& operator=(const Reply&)=delete;
        Reply(Reply&&)=default;
        Reply& operator=(Reply&&)=default;
    private:
        friend class SharedPostWorldExit;
        Reply(Scope,std::array<std::uint8_t,3>,Current);
        bool current(const Scope&) const;
        Scope scope_;
        std::array<std::uint8_t,3> record_;
        Current current_;
    };
    //Synchronously prepare actual native03 under the designated terminal scope;
    //never manufacture values, mutate saves, yield or send from this callback.
    using Source=std::function<std::optional<Reply>(const Scope&)>;
    static std::shared_ptr<SharedPostWorldExit> attach(const std::shared_ptr<Connection>&,
        std::shared_ptr<SharedWorldPresence>,const Lease&,Source);
    Connection::Ingress ingress();
private:
    SharedPostWorldExit(const std::shared_ptr<Connection>&,std::shared_ptr<SharedWorldPresence>,const Lease&,Source);
    void owner() const;
    bool current() const;
    bool terminal_current(const Scope&) const;
    void receive(god2cn::Bytes,Connection::Transport::Completion);
    std::thread::id thread_=std::this_thread::get_id();
    std::weak_ptr<Connection> connection_;
    std::shared_ptr<SharedWorldPresence> presence_;
    Lease lease_;
    Source source_;
    std::optional<Scope> terminal_scope_;
};
}
