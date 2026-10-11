#pragma once
#include "cn/net/SharedCredentialConnection.h"
#include "cn/protocol/CnCharacterDelete.h"
#include "db/RecoveredCharacterRepository.h"
#include <functional>
#include <optional>
#include <string_view>

namespace god2::cn {
// Native19's offered07 slot/name -> common identity, before any mutation.
// This is a current identity proof, NOT deletion permission, a transaction,
// consumed operation token or a native success/reply provider. Host repository
// must outlive these values. All methods run on its serial game owner.
class SharedCharacterDeleteIdentity {
public:
    using Connection=SharedCredentialConnection;
    using CredentialEcho=std::function<bool(std::string_view,std::string_view)>;
    using CurrentPhase=std::function<bool()>;
    // Both predicates must come from the actual authenticated pre-world owner;
    // neither may be created from incoming19. All eight low3 native slots are
    // structural here, independently of1A's separately qualified slot domain.
    static std::optional<SharedCharacterDeleteIdentity> resolve(
        const std::shared_ptr<Connection>&,RecoveredCharacterRepository&,
        const god2cn::CnCharacterDelete&,CredentialEcho,CurrentPhase);
    std::uint64_t account() const noexcept {return account_;}
    std::uint64_t character() const noexcept {return character_;}
    std::uint64_t world_session() const noexcept {return world_session_;}
    std::uint8_t native_slot() const noexcept {return native_slot_;}
    // Recheck the exact committed offer/generation, phase, connection and
    // current common ownership before handing identity to actual mutation.
    // Actual rule/online-owner/revision/CAS checks still belong to that owner.
    bool current() const;
private:
    SharedCharacterDeleteIdentity(const std::shared_ptr<Connection>&,
        RecoveredCharacterRepository&,SharedWorldAdmission::OfferSource,
        std::uint64_t account,std::uint64_t session,std::uint64_t character,
        std::uint8_t slot,CurrentPhase);
    static bool owned_offer(const std::shared_ptr<Connection>&,
        RecoveredCharacterRepository&,const SharedWorldAdmission::OfferSource&);
    std::weak_ptr<Connection> connection_;
    RecoveredCharacterRepository* characters_;
    SharedWorldAdmission::OfferSource source_;
    std::uint64_t account_,world_session_,character_;
    std::uint8_t native_slot_;
    CurrentPhase phase_;
};
}
