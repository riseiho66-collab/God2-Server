#pragma once
#include <cstdint>
#include <functional>
#include <optional>
#include <span>

namespace god2cn {
// Pinned CN0049075A/00539624: one retained DWORD operand, not a FIFO.
// Reads supplied actual owner bytes only; no native pointer/process access.
class CnDeferredRoleRefresh {
public:
    struct Scope {
        std::uint32_t actual_owner_word;
        std::uint64_t actual_revision;
    };
    using Current=std::function<bool(const Scope&)>;
    class Snapshot;
    class Drain {
    public:
        bool current() const;
        // Empty only when the actual pending DWORD was zero. Missing/stale
        // source is represented by no Drain, never an empty notification.
        std::optional<std::uint32_t> refresh_flags() const noexcept;
        std::uint32_t actual_pending_word() const noexcept {return pending_;}
        // Same actual owner, retained operand unchanged, pending now cleared.
        // This is a source receipt, not proof the client rendered or sent6D.
        bool completed_by(const Snapshot& actual_after) const;
    private:
        friend class CnDeferredRoleRefresh;
        friend class Snapshot;
        Drain(Scope,Current,std::uint32_t,std::uint32_t);
        Scope scope_;
        Current current_;
        std::uint32_t flags_,pending_;
    };
    class Snapshot {
    public:
        bool current() const;
        // Enclosing native frame source must already qualify entry state8
        // and005393B0 return1. This reader does not simulate motion/refresh.
        std::optional<Drain> completed_step_operand() const;
    private:
        friend class CnDeferredRoleRefresh;
        friend class Drain;
        Snapshot(Scope,Current,std::uint32_t,std::uint32_t);
        Scope scope_;
        Current current_;
        std::uint32_t flags_,pending_;
    };
    // Actual owner+89B240 flags and+89B244 pending; both original DWORDs.
    // Initialization FFFFFFFF/0 does not supply a current runtime snapshot.
    static std::optional<Snapshot> read_actual_owner(
        Scope,std::span<const std::uint8_t> actual_owner_bytes,Current);
};
}
