#include "cn/world/CnDeferredRoleRefresh.h"
#include <utility>

namespace god2cn {
namespace {
std::uint32_t word(std::span<const std::uint8_t> bytes,std::size_t offset) {
    return std::uint32_t(bytes[offset]) | (std::uint32_t(bytes[offset+1])<<8) |
        (std::uint32_t(bytes[offset+2])<<16) | (std::uint32_t(bytes[offset+3])<<24);
}
}
CnDeferredRoleRefresh::Snapshot::Snapshot(Scope scope,Current current,
    std::uint32_t flags,std::uint32_t pending)
    :scope_(scope),current_(std::move(current)),flags_(flags),pending_(pending) {}
CnDeferredRoleRefresh::Drain::Drain(Scope scope,Current current,
    std::uint32_t flags,std::uint32_t pending)
    :scope_(scope),current_(std::move(current)),flags_(flags),pending_(pending) {}
bool CnDeferredRoleRefresh::Snapshot::current() const {return current_(scope_);}
bool CnDeferredRoleRefresh::Drain::current() const {return current_(scope_);}
std::optional<CnDeferredRoleRefresh::Snapshot> CnDeferredRoleRefresh::read_actual_owner(
    Scope scope,std::span<const std::uint8_t> bytes,Current current) {
    if(!scope.actual_owner_word || !scope.actual_revision || !current ||
       bytes.size()<0x89b248 || !current(scope))return std::nullopt;
    const auto flags=word(bytes,0x89b240),pending=word(bytes,0x89b244);
    if(!current(scope))return std::nullopt;
    return Snapshot(scope,std::move(current),flags,pending);
}
std::optional<CnDeferredRoleRefresh::Drain>
CnDeferredRoleRefresh::Snapshot::completed_step_operand() const {
    if(!current())return std::nullopt;
    return Drain(scope_,current_,flags_,pending_);
}
std::optional<std::uint32_t> CnDeferredRoleRefresh::Drain::refresh_flags() const noexcept {
    if(pending_==0)return std::nullopt;
    return flags_; // Any nonzero pending value qualifies; flags0 is a real operand.
}
bool CnDeferredRoleRefresh::Drain::completed_by(const Snapshot& after) const {
    return after.scope_.actual_owner_word==scope_.actual_owner_word &&
        after.flags_==flags_ && after.pending_==0 && after.current();
}
}
