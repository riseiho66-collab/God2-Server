#pragma once
#include "cn/net/SharedCredentialConnection.h"
#include "cn/protocol/CnCharacterCreate.h"
#include "cn/protocol/CnCharacterLocationChoice.h"
#include "cn/protocol/CnCreationLocationProjection.h"
#include "db/RecoveredCharacterRepository.h"
#include <functional>
#include <optional>
#include <span>
#include <thread>
#include <vector>

namespace god2::cn {
// Ordinary17 -> an actually committed common character -> subsequent18.
// Identity/projection only: not a consumed operation token, permission, storage
// CAS, issuer or handler. Repository must outlive the returned snapshot.
class SharedCreationLocationIdentity {
public:
    using Connection=SharedCredentialConnection;
    using Request=god2cn::CnCharacterCreate;
    using Projection=god2cn::CnCreationLocationProjection::Reference;
    // Required actual creation owner checks pointer identity of its retained17,
    // the authoritative created common ID and its exact offered-choice source.
    // Also checks phase/generation, exclusive operation/replay and current rule
    // eligibility. Never build this predicate or permitted set from incoming18.
    using CurrentPendingCreate=std::function<bool(
        const std::shared_ptr<const Request>&,std::uint64_t,
        std::span<const std::uint8_t>)>;
    static std::optional<SharedCreationLocationIdentity> resolve(
        const std::shared_ptr<Connection>&,RecoveredCharacterRepository&,
        std::shared_ptr<const Request> actual_create_request,std::uint64_t created_common_id,
        std::span<const std::uint8_t> permitted_choices,CurrentPendingCreate,
        std::span<const std::uint8_t> record18);
    std::uint64_t account() const noexcept {return account_;}
    std::uint64_t character() const noexcept {return character_;}
    std::uint64_t world_session() const noexcept {return world_session_;}
    const Projection& projection() const noexcept {return projection_;}
    // Before actual transaction/response; actual writer must repeat revision/CAS
    // and consume its exclusive pending operation atomically. This is not CAS.
    bool current() const;
private:
    SharedCreationLocationIdentity(const std::shared_ptr<Connection>&,
        RecoveredCharacterRepository&,std::shared_ptr<const Request>,RecoveredCharacter,
        std::vector<std::uint8_t>,CurrentPendingCreate,Projection);
    void owner() const;
    std::thread::id thread_=std::this_thread::get_id();
    std::weak_ptr<Connection> connection_;
    RecoveredCharacterRepository* characters_;
    std::shared_ptr<const Request> request_;
    RecoveredCharacter created_snapshot_;
    std::vector<std::uint8_t> permitted_choices_;
    CurrentPendingCreate pending_;
    Projection projection_;
    std::uint64_t account_,character_,world_session_;
};
}
