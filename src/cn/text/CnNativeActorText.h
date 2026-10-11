#pragma once
#include "cn/protocol/CnRemoteActor.h"
#include <functional>
#include <string>

namespace god2cn {
// Predicted native6F text copies for the pinned self-tag0 CN receiver.
// Not the shared ChineseText preference converter, a native observation or
// permission to change account/character/name lookup identity.
class CnNativeActorText {
public:
    struct State {
        std::uint64_t actual_native_text_revision;
        std::uint32_t actual_unicode_capability; //00405A40 ->008AEEB8.
        std::uint32_t actual_conversion_latch; //008A4594, cleared on failures.
        // Actual owner qualifies the current receiver gate and that this
        // Windows NLS environment/API behavior matches that receiver. Neither
        // the pinned executable nor this server's OS proves that condition.
        std::function<bool()> qualified_receiver_environment_current;
    };
    class Projection {
    public:
        const std::array<std::string,3>& expected_native_strings() const noexcept {return expected_;}
        // Checks only text-relevant identity/tag/all three raw input regions;
        // ordinary movement coordinates are allowed to change independently.
        bool current(const CnRemoteActor::Record&) const;
    private:
        friend class CnNativeActorText;
        Projection(CnRemoteActor::LogicalRecord,State,std::array<std::string,3>);
        CnRemoteActor::LogicalRecord source_;
        State state_;
        std::array<std::string,3> expected_;
    };
    // Successful tag1 -> self0 branch only. All three sequential native copies
    // must terminate within16 bytes so the first copy cannot overwrite the
    // following source fields. Disabled/failed/overflow branches are pending,
    // never silently replaced by raw text or another conversion dictionary.
    // This method is source only during phase1: do not execute native APIs now.
    static std::optional<Projection> prepare(const CnRemoteActor::Record&,State);
};
}
