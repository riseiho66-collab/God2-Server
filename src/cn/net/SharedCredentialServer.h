#pragma once
#include "cn/net/SharedCredentialConnection.h"
#include "cn/net/SharedListenerRegistry.h"
#include "db/RecoveredCharacterRepository.h"
#include "db/NativeMapCatalog.h"
#include "db/NativeAccountSnapshotRepository.h"
#include "db/NativeCharacterSummarySnapshotRepository.h"
#include "cn/assets/CnSharedSkillCatalog.h"
#include <memory>
#include <optional>
#include <string>
#include <thread>
#include <vector>

namespace god2 {class SharedWorldHost;class NativeSkillCatalog;}
namespace god2cn {class CnNativeSkillCatalog;}
namespace god2::cn {
class CnSharedSkillCatalog;
// Source-only Application hosting contract. No default plan or wire suppliers
// exist. Account/world roles and destinations belong to the listening socket,
// never to an opcode guess, claimed login ID or text-encoding preference.
struct SharedServerPlan {
    using Connection=SharedCredentialConnection;
    using Role=Connection::Transport::Role;
    struct Endpoint {
        std::string host;
        std::uint16_t port=0; // Invalid until explicitly supplied.
        Role role=static_cast<Role>(2); // Invalid; never defaults to account/world.
        std::optional<SharedWorldAdmission::Target> target;
    };
    struct Context {
        AccountRepository& accounts;
        //Same existing SQLite reader; no schema install or default snapshot.
        NativeAccountSnapshotRepository& account_snapshots;
        NativeCharacterSummarySnapshotRepository& character_summaries;
        RecoveredCharacterRepository& characters;
        const NativeMapCatalog& maps;
        std::shared_ptr<SharedWorldAdmission> admission;
        asio::any_io_executor game;
        const std::vector<Endpoint>& endpoints;
        // Minted from actual successfully bound sockets before this factory.
        // Observe during active account source work, never infer from the plan.
        std::shared_ptr<const SharedListenerRegistry> listeners;
        // Optional explicit common Application owner, appended for old aggregate
        // compatibility. A legacy null never creates a separate CN registry.
        std::shared_ptr<god2::SharedWorldHost> common_world;
        // Same Application SQLite reader supplied to the TW source factory.
        // Borrow on this game owner while that DB outlives controller drain.
        // Legacy absence stays null; no import, TW fallback or learned grant.
        // Actual CN providers still require CnSharedSkillCatalog qualification.
        const god2::NativeSkillCatalog* native_skills=nullptr;
        // Explicit pinned CN definitions qualified against that same reader.
        // Copy this strong owner into sources; never retain a Context reference.
        // Null preserves legacy absence. Definition membership is not learned
        // authority. Each later lookup must still qualify its actual row.
        std::shared_ptr<const CnSharedSkillCatalog> cn_native_skills;
    };
    struct Controllers {
        // Actual16-byte transport seed source; no implicit zero/random fallback.
        // An explicitly selected own-server operational CNG source is separate
        // from recovered native intake/key/challenge and official RNG policy.
        using Seed=std::function<std::optional<std::array<std::uint8_t,16>>(
            std::uint64_t,const Endpoint&)>;
        // The real success/selection controller must install owned ingress and
        // supply complete native records before acknowledging this continuation.
        using Verified=std::function<void(std::uint64_t,const Endpoint&,
            std::shared_ptr<Connection>,CredentialResult,
            std::shared_ptr<const god2cn::CnAccountWire::Login>,Connection::Transport::Completion)>;
        Seed seed;
        Verified account;
        Verified world;
        // The SAME selected immutable config retained by account composition
        // and directory. Mandatory even though the pinned wire byte stays40.
        std::shared_ptr<const god2cn::CnClientGroupConfiguration> account_configuration;
    };
    std::vector<Endpoint> endpoints;
    // Zero operational budgets are rejected, not inferred from native packets.
    std::size_t max_sessions=0,live_grants=0,issued_keys=0,authentication_workers=0,authentication_capacity=0;
    std::function<Controllers(const Context&)> controllers;
    // Opt-in actual immutable provider. The host qualifies all453 definitions
    // against its already migrated/populated shared reader before controllers
    // or acceptance. Missing/conflicting rows fail; never import or grant here.
    // Its Current must observe the retained actual source on this game owner,
    // without pumping events/reentering the host or mutating the shared store.
    std::shared_ptr<const god2cn::CnNativeSkillCatalog> native_skill_definitions;
    // Mandatory with the opt-in definitions. Actual same Application store
    // lifetime/current owner, retained by the qualified catalog through drain;
    // no non-owning marker or default resource-current substitute.
    std::shared_ptr<const void> native_skill_store_lifetime;
    CnSharedSkillCatalog::StoreCurrent native_skill_store_current;
};

// Construct/start/stop/destroy on the single Application game thread. The same
// repositories and both executors must outlive connection/authentication drain.
// Socket acceptance runs on a network strand; all credential/controller/registry
// work runs on the supplied serial game owner. No CN database is opened here.
class SharedCredentialServer {
public:
    SharedCredentialServer(asio::io_context& network,asio::any_io_executor game,
        AccountRepository&,NativeAccountSnapshotRepository&,NativeCharacterSummarySnapshotRepository&,
        RecoveredCharacterRepository&,
        const NativeMapCatalog&,const SharedServerPlan&);
    SharedCredentialServer(asio::io_context& network,asio::any_io_executor game,
        AccountRepository&,NativeAccountSnapshotRepository&,NativeCharacterSummarySnapshotRepository&,
        RecoveredCharacterRepository&,
        const NativeMapCatalog&,const SharedServerPlan&,std::shared_ptr<god2::SharedWorldHost>);
    // Explicit real shared definition reader. Legacy absence of the opt-in
    // provider only forwards it; native_skill_definitions additionally performs
    // the read-only all453 qualification before the existing source factory.
    SharedCredentialServer(asio::io_context& network,asio::any_io_executor game,
        AccountRepository&,NativeAccountSnapshotRepository&,NativeCharacterSummarySnapshotRepository&,
        RecoveredCharacterRepository&,
        const NativeMapCatalog&,const SharedServerPlan&,std::shared_ptr<god2::SharedWorldHost>,
        const god2::NativeSkillCatalog&);
    ~SharedCredentialServer();
    SharedCredentialServer(const SharedCredentialServer&)=delete;
    SharedCredentialServer& operator=(const SharedCredentialServer&)=delete;
    void start();
    void stop();
    using BoundEndpoint=SharedListenerRegistry::Endpoint;
    // Actual successfully bound listener registry; inspect on the game owner.
    std::vector<BoundEndpoint> bound_endpoints() const;
private:
    SharedCredentialServer(asio::io_context& network,asio::any_io_executor game,
        AccountRepository&,NativeAccountSnapshotRepository&,NativeCharacterSummarySnapshotRepository&,
        RecoveredCharacterRepository&,
        const NativeMapCatalog&,const SharedServerPlan&,std::shared_ptr<god2::SharedWorldHost>,
        const god2::NativeSkillCatalog*);
    struct State;
    struct Listener;
    std::thread::id thread_=std::this_thread::get_id();
    std::unique_ptr<SharedAccountVerifier> verifier_;
    std::shared_ptr<State> state_;
    std::shared_ptr<Listener> listener_;
    std::shared_ptr<SharedListenerRegistry> registry_;
    void owner() const;
};
}
