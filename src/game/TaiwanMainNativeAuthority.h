#pragma once
#include "game/SharedTaiwanCharacterListHandoff.h"
#include "game/SharedTaiwanNativeCharacterOfferSource.h"
#include <array>
#include <memory>

namespace god2 {
// CUSTOM-0159: own-server primary/common-identity login permissions. This is
// not recovered original visibility policy or a native07/2A byte generator.
// Actual complete07 Supply remains mandatory; no DB witness can mint a grant.
class TaiwanMainNativeAuthority final {
public:
    using Source=SharedTaiwanNativeCharacterListSource;
    using Handoff=SharedTaiwanCharacterListHandoff;
    struct StorageScope {std::uint16_t group,server;bool operator==(const StorageScope&) const=default;};
    class Binding final {
    public:
        const Source::TargetSource target;
        const Source::Qualify qualify;
        const Handoff::Live live;
        const Handoff::Authority authority;
        const Source::Prepare prepare;
    private:
        friend class TaiwanMainNativeAuthority;
        Binding(Source::TargetSource,Source::Qualify,Handoff::Live,Handoff::Authority,Source::Prepare);
    };
    // GAME-owned, same existing DB readers/writer. publication_capacity bounds
    // retained (account,native subgroup) publications, NOT sessions/tickets.
    // The host explicitly maps exactly three native slots to storage scopes.
    // Supply must produce complete original bytes and observe its resource
    // lifecycle; withdrawal must call revoke, never silently reuse old policy.
    // Its native Issuer is evaluated by the existing CAS adapter, not replayed
    // outside a transaction. Afterwards this CUSTOM publication stays approved
    // until exact tuple/root drift, replacement or explicit revoke. It is not
    // a claim of automatic native-resource epoch monitoring. Producer owners
    // must revoke before changing/withdrawing their backing native source.
    static std::shared_ptr<TaiwanMainNativeAuthority> create(AccountRepository&,
        RecoveredCharacterRepository&,SqliteNativeCharacterSummarySnapshotRepository&,
        std::shared_ptr<const TaiwanNativeClientGroupConfiguration>,std::string client,
        std::uint8_t native_group,std::array<StorageScope,3>,std::size_t publication_capacity,
        SharedTaiwanNativeCharacterOfferSource::Supply);
    Binding binding() const;
    bool matches_sources(const AccountRepository&,const RecoveredCharacterRepository&,
        const NativeCharacterSummarySnapshotRepository&) const;
    void revoke(std::uint64_t account,std::uint8_t native_subgroup);
private:
    struct State;
    explicit TaiwanMainNativeAuthority(std::shared_ptr<State> state):state_(std::move(state)) {}
    std::shared_ptr<State> state_;
};
}
