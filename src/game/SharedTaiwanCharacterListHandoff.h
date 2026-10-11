#pragma once
#include "game/SharedTaiwanNativeCharacterListSource.h"
#include "game/TaiwanNativeClientGroupConfiguration.h"
#include <string_view>

namespace god2 {
// Serial game-owner storage for actual issued TW lists. Neither credentials
// nor an account's newest list are a replacement for native route authority.
class SharedTaiwanCharacterListHandoff final {
public:
    using Source=SharedTaiwanNativeCharacterListSource;
    using Auth=Session::NativeAuthenticatedInput;
    using Current=std::function<bool(Session&,const Source::Scope&)>;
    // Must observe the real issuer epoch/catalog/visibility/lifecycle. Called
    // for a dormant ticket during Publish, without requiring its final receipt.
    using Live=std::function<bool(const Source::Issued&,const Auth&)>;
    struct DestinationAuthority {
        // Native configured namespace, distinct from storage group/server.
        // Supplier must qualify real catalog/epoch/local-backing variant; A6
        // lowBYTE equality alone does not prove the full original UI WORDs.
        // Count is derived from our retained actual configuration, not policy.
        std::uint8_t group,subgroup;
        Current current;
    };
    // Independent G authentication and projected bytes are only predicates.
    // The supplier must qualify actual destination/native variant/rights.
    // All suppliers are pure, synchronous, non-yielding game-owner calls.
    using Authority=std::function<std::optional<DestinationAuthority>(Session&,const Source::Scope&,
        const Source::Issued&,const Auth& issuer,const Auth& peer)>;
    struct Binding {Source::Publish publish;Source::LinkSource link;};
    static std::shared_ptr<SharedTaiwanCharacterListHandoff> create(AccountRepository&,
        RecoveredCharacterRepository&,NativeCharacterSummarySnapshotRepository&,
        std::string client_sha256,std::size_t actual_session_capacity,
        std::shared_ptr<const TaiwanNativeClientGroupConfiguration>,Live,Authority);
    Binding binding();
    bool matches_sources(const AccountRepository&,const RecoveredCharacterRepository&,
        const NativeCharacterSummarySnapshotRepository&,std::string_view,std::size_t) const;
    // Real lifecycle withdrawal by exact ticket. Closing L alone does not
    // revoke a legitimate pending G handoff. No invented timeout or L keepalive.
    void retire(const Source::IssuedPtr&);
private:
    struct State;
    explicit SharedTaiwanCharacterListHandoff(std::shared_ptr<State> state):state_(std::move(state)) {}
    std::shared_ptr<State> state_;
};
}
