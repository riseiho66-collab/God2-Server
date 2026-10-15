#pragma once
#include "game/OwnedTaiwanReturnActorSavedSource.h"
#include "game/TaiwanNativeActorResourceBank.h"
#include "game/TaiwanNativeActorArgumentSource.h"
#include "game/TaiwanNativeDrvDoll.h"
#include "game/TaiwanActorStatusProfileScope.h"
#include "game/TaiwanActorStatusOwnedSource.h"
#include "cn/world/SharedActorVisibility.h"
#include <functional>
#include <asio/any_io_executor.hpp>
#include <memory>
#include <optional>
#include <thread>
#include <utility>
#include <vector>

namespace god2 {
class TaiwanInitialActorEndpoints;
// A private direction/input/phase leaf issued only by the actual initial
// endpoint owner. Public callbacks cannot replace this receipt.
class TaiwanInitialActorEndpointProof final {
    struct Data;
public:
    TaiwanInitialActorEndpointProof(const TaiwanInitialActorEndpointProof&)=default;
    TaiwanInitialActorEndpointProof& operator=(const TaiwanInitialActorEndpointProof&)=default;
private:
    friend class TaiwanInitialActorEndpoints;
    explicit TaiwanInitialActorEndpointProof(std::shared_ptr<const Data> data):data_(std::move(data)){}
    std::shared_ptr<const Data> data_;
};
// Explicit CUSTOM-0133 fresh full records, not a recovered native producer,
// equipment permission, canonical-slot mapping or default emission switch.
class TaiwanCustomFullActorProfile final {
    struct Identity {};
    struct Data;
public:
    using Check=cn::SharedActorVisibility::TaiwanReturnCheck;
    using Lease=SharedWorldPresence::Lease;
    using SavedInput=OwnedTaiwanReturnActorSavedSource::PopulationInput;
    using Equipment=OwnedTaiwanReturnActorSavedSource::ProfileEquipment;
    class Policy final {
    public:
        enum class Version {Custom0133FullActorV1};
        Policy(Version,std::uint32_t word1_unknown,std::uint32_t word5_unknown,
            std::uint32_t opaque9,std::uint32_t opaque17,std::uint8_t position_low2,
            std::uint16_t move_identity_upper,std::uint16_t move_state_upper,
            std::uint32_t move_position_upper,std::uint16_t remove_identity_upper);
        const Version version;
        const std::uint32_t word1_unknown,word5_unknown,opaque9,opaque17;
        const std::uint8_t position_low2;
        const std::uint16_t move_identity_upper,move_state_upper;
        const std::uint32_t move_position_upper;
        const std::uint16_t remove_identity_upper;
    };
    struct SourceInput {
        std::shared_ptr<Session> session;
        // Actual normal-transport/return phase leaf; do not strongly retain
        // the SceneOwner which itself retains this Profile (ownership cycle).
        std::shared_ptr<const void> phase_owner;
        std::function<bool(Check,const Lease&,Session&)> current;
        // LAST: required only for a private initial PopulationInput.
        std::optional<TaiwanInitialActorEndpointProof> initial_endpoint{};
    };
    struct ReceiverInput {
        std::shared_ptr<Session> session;
        Session::NativeTaiwanReceiverSelector selector;
        std::shared_ptr<const void> phase_owner;
        // Exact private report/phase proof, including the consumed successor.
        // Never qualify Consumed by old prebattle NormalINIT/Appearance Current.
        std::function<bool(Check,Session&,const Session::NativeTaiwanReceiverSelector&)> current;
        // LAST: a receiver receipt cannot be substituted by a source receipt.
        std::optional<TaiwanInitialActorEndpointProof> initial_endpoint{};
    };
    struct ComponentRom {
        TaiwanNativeActorResourceBank::HeroLookup lookup;
        // Null only for an actual qualified empty-filename/not-requested row.
        std::shared_ptr<const TaiwanNativeActorResourceBank::ResolvedRom> rom;
    };
    struct ResourceInput {
        enum class Origin {Custom0133Explicit,SavedWorldSelectors};
        enum class Mode {DrvOnly,HeroComponents,HeroComponentsAndDrv};
        std::shared_ptr<const TaiwanNativeActorResourceBank> bank;
        std::shared_ptr<const TaiwanNativeDrvDoll> drv_doll_bank;
        std::uint64_t epoch;
        Origin origin;
        Mode mode;
        std::uint8_t first_selector,second_selector;
        // Independent from both wire selectors. Drv.col2 is NOT ROM action.
        std::uint32_t full_drv_ordinal;
        std::shared_ptr<const TaiwanNativeActorResourceBank::ResolvedRom> drv;
        std::vector<ComponentRom> components;
        // Exact private derivation from the same backend input/equipment.
        // Public header values or lookup vectors cannot replace this witness.
        std::shared_ptr<TaiwanNativeActorArgumentSource> arguments_source;
        std::optional<TaiwanNativeActorArgumentSource::Observation> arguments;
        std::shared_ptr<const void> dependency_owner;
        // Real resource/selection/window/action epoch over this entire material.
        // Files/bank membership or an always-true callback are not Current.
        std::function<bool(Check,const ResourceInput&)> current;
        // LAST: independent136-byte DrvDoll tail, not ordinary32-byte Drv.
        // Empty only when the actual pinned first-selector row has no filename.
        std::shared_ptr<const TaiwanNativeDrvDoll::ResolvedRom> tail{};
    };
    struct StatusInput {
        enum class Domain {OrdinaryKnownAbsence,OrdinaryExplicitClear};
        Domain domain;
        std::uint64_t epoch;
        std::uint32_t unsupported_domains;
        std::shared_ptr<const cn::SharedActorVisibility::TaiwanReturnActorOverride> actor_override;
        std::shared_ptr<const void> dependency_owner;
        std::function<bool(Check,const StatusInput&)> current;
        // LAST: private same saved-input/row/EQ and BOTH actor incarnations.
        // Lifetime/input scope only; does not establish the status values.
        std::shared_ptr<TaiwanActorStatusProfileScope> profile_scope_source{};
        std::optional<TaiwanActorStatusProfileScope::Observation> profile_scope{};
        // LAST: optional typed CUSTOM initial-install policy owner. Both fields
        // are mandatory together; the external provider path remains supported.
        std::shared_ptr<TaiwanActorStatusOwnedSource> owned_status_source{};
        std::optional<TaiwanActorStatusOwnedSource::Observation> owned_status{};
    };
    class Profile final {
    public:
        Profile(const Profile&)=default;
        Profile& operator=(const Profile&)=default;
        Profile(Profile&& other) noexcept:data_(other.data_){}
        Profile& operator=(Profile&& other) noexcept{data_=other.data_;return *this;}
        const RecoveredRemoteActor::Record& spawn() const noexcept;
        const RecoveredRemoteActorMove::Record& movement() const noexcept;
        const RecoveredRemoteActorRemove::Record& removal() const noexcept;
        const std::shared_ptr<const SavedInput>& saved_input() const noexcept;
        const Equipment& equipment() const noexcept;
        const OwnedTaiwanPkReturnRoleTextSource::Observation& role_text() const noexcept;
        const Lease& source() const noexcept;
        const Lease& recipient() const noexcept;
        const std::shared_ptr<Session>& source_session() const noexcept;
        const SourceInput& source_input() const noexcept;
        const ReceiverInput& receiver() const noexcept;
        const ResourceInput& resources() const noexcept;
        const StatusInput& status() const noexcept;
        const std::shared_ptr<const cn::SharedActorVisibility::TaiwanReturnActorOverride>& actor_override() const noexcept;
        std::uint64_t revision() const noexcept;
        bool operator==(const Profile& other) const noexcept{return data_==other.data_;}
    private:
        friend class TaiwanCustomFullActorProfile;
        explicit Profile(std::shared_ptr<const Data> data):data_(std::move(data)){}
        std::shared_ptr<const Data> data_;
    };
    static std::shared_ptr<TaiwanCustomFullActorProfile> create(
        std::shared_ptr<SharedWorldPresence>,std::shared_ptr<const TaiwanNativeActorResourceBank>,
        std::shared_ptr<const TaiwanNativeDrvDoll>,Policy);
    ~TaiwanCustomFullActorProfile();
    TaiwanCustomFullActorProfile(const TaiwanCustomFullActorProfile&)=delete;
    TaiwanCustomFullActorProfile& operator=(const TaiwanCustomFullActorProfile&)=delete;
    std::optional<Profile> observe(std::shared_ptr<const SavedInput>,std::size_t source_row,
        Equipment,SourceInput,Lease recipient,ReceiverInput,ResourceInput,StatusInput);
    bool current(const Profile&,Check) const;
    // Pure private identity/population/immutable input fence; no allocation,
    // SQL, encoding, provider or resource callbacks; initial endpoint phases
    // are checked through their private pure receipts.
    bool owns_profile(const Profile&) const noexcept;
    bool owns_presence(const std::shared_ptr<SharedWorldPresence>&) const noexcept;
    bool owns_resource_bank(const std::shared_ptr<const TaiwanNativeActorResourceBank>&) const noexcept;
private:
    struct Operation;
    TaiwanCustomFullActorProfile(std::shared_ptr<SharedWorldPresence>,
        std::shared_ptr<const TaiwanNativeActorResourceBank>,std::shared_ptr<const TaiwanNativeDrvDoll>,Policy);
    const std::shared_ptr<SharedWorldPresence> presence_;
    const std::shared_ptr<const TaiwanNativeActorResourceBank> bank_;
    const std::shared_ptr<const TaiwanNativeDrvDoll> drv_doll_bank_;
    const Policy policy_;
    const std::shared_ptr<const Identity> identity_=std::make_shared<const Identity>();
    const std::thread::id thread_=std::this_thread::get_id();
    mutable bool busy_=false,poisoned_=false,stopped_=false;
    std::uint64_t next_revision_=1;
    bool retained(const Data&) const noexcept;
    bool owned_status_qualified(const StatusInput&,const std::shared_ptr<const SavedInput>&,
        std::size_t,const Equipment&,const Lease&,bool live) const noexcept;
    bool resources_qualified(const Data&) const;
    bool observers_current(const Data&,Check) const;
    bool joint_current(const Data&) const;
};
}

namespace god2 {
class SharedNativeWorldTransports;
// Actual initial-entry endpoint phases only. No audience selection, actor
// material, status initialization, transport registration or publication.
class TaiwanInitialActorEndpoints final {
    friend class TaiwanInitialActorEndpointProof;
    struct Identity;
    struct Data;
    struct Leaf;
    struct Operation;
    enum class Purpose {Source,Receiver};
public:
    using ProfileOwner=TaiwanCustomFullActorProfile;
    using SavedInput=ProfileOwner::SavedInput;
    using Lease=ProfileOwner::Lease;
    static std::shared_ptr<TaiwanInitialActorEndpoints> create(
        std::shared_ptr<SharedWorldPresence>,std::shared_ptr<SharedNativeWorldTransports>,
        Session& joining,std::shared_ptr<const SavedInput>,asio::any_io_executor);
    ~TaiwanInitialActorEndpoints() noexcept;
    TaiwanInitialActorEndpoints(const TaiwanInitialActorEndpoints&)=delete;
    TaiwanInitialActorEndpoints& operator=(const TaiwanInitialActorEndpoints&)=delete;
    std::optional<ProfileOwner::SourceInput> source(const Lease&) const;
    std::optional<ProfileOwner::ReceiverInput> receiver(const Lease&) const;
    bool matches_input(const std::shared_ptr<const SavedInput>&) const noexcept;
    static bool qualify_source(const std::shared_ptr<const SavedInput>&,const Lease&,
        const ProfileOwner::SourceInput&,bool live) noexcept;
    static bool qualify_receiver(const std::shared_ptr<const SavedInput>&,const Lease&,
        const ProfileOwner::ReceiverInput&,bool live) noexcept;
    // Pure identity/input/registry/Session cuts, with no SQL or observers.
    bool retained() const noexcept;
    void retire() noexcept;
private:
    explicit TaiwanInitialActorEndpoints(std::shared_ptr<const Data> data):data_(std::move(data)){}
    const std::shared_ptr<const Data> data_;
    static std::shared_ptr<const Leaf> select(std::shared_ptr<const Data>,Lease,Purpose);
    static bool retained_data(const Data&) noexcept;
    static bool retained_leaf(const Leaf&) noexcept;
    static bool current_leaf_body(const Leaf&,ProfileOwner::Check) noexcept;
    static bool current_leaf(const std::shared_ptr<const Leaf>&,ProfileOwner::Check) noexcept;
};
}
