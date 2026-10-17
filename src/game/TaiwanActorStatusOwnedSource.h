#pragma once
#include "game/OwnedTaiwanReturnActorSavedSource.h"
#include "game/TaiwanActorStatusIncarnationSource.h"
#include "game/TaiwanActorStatusPublication.h"
#include "shared/world/SharedActorVisibility.h"
#include <cstdint>
#include <map>
#include <memory>
#include <optional>
#include <thread>
#include <utility>

namespace god2 {
class Session;
class SharedTaiwanNativeWorldHostPlan;
class OwnedTaiwanPkReturnSceneSource;
class OwnedTaiwanInitialActorSceneSource;
// CUSTOM-0133 explicit initial-install clear policy. This owned ordinary subset
// is not recovered native status, complete writer custody or a byte permission.
class TaiwanActorStatusOwnedSource final {
    struct Identity;
    struct Entry;
    struct InstallData;
    struct Data;
    class Operation;
public:
    using Input=OwnedTaiwanReturnActorSavedSource::PopulationInput;
    using Equipment=OwnedTaiwanReturnActorSavedSource::ProfileEquipment;
    using Lease=SharedWorldPresence::Lease;
    using Incarnation=TaiwanActorStatusIncarnationSource::Token;
    using Override=shared::SharedActorVisibility::TaiwanReturnActorOverride;
    class Policy final {
    public:
        enum class Version {Custom0133OrdinaryInitialClearV1};
        Policy(Version,std::uint32_t explicit_raw_clear_index);
        const Version version;
        const std::uint32_t raw_clear_index;
    };
    class InitialInstall final {
    public:
        InitialInstall(const InitialInstall&) noexcept=default;
        InitialInstall& operator=(const InitialInstall&) noexcept=default;
    private:
        friend class TaiwanActorStatusOwnedSource;
        explicit InitialInstall(std::shared_ptr<InstallData> data) noexcept:data_(std::move(data)){}
        std::shared_ptr<InstallData> data_;
    };
    class Observation final {
    public:
        Observation(const Observation&) noexcept=default;
        Observation& operator=(const Observation&) noexcept=default;
        std::uint64_t revision() const noexcept;
        const std::shared_ptr<const Override>& actor_override() const noexcept;
        const std::shared_ptr<const Input>& saved_input() const noexcept;
        std::size_t row_index() const noexcept;
        const Equipment& equipment() const noexcept;
        const Lease& source() const noexcept;
        const Lease& recipient() const noexcept;
        const Incarnation& source_incarnation() const noexcept;
        const Incarnation& recipient_incarnation() const noexcept;
        bool operator==(const Observation& other) const noexcept{return data_==other.data_;}
    private:
        friend class TaiwanActorStatusOwnedSource;
        explicit Observation(std::shared_ptr<const Data> data) noexcept:data_(std::move(data)){}
        std::shared_ptr<const Data> data_;
    };
    static std::shared_ptr<TaiwanActorStatusOwnedSource> create(
        std::shared_ptr<SharedWorldPresence>,std::shared_ptr<TaiwanActorStatusIncarnationSource>,Policy);
    ~TaiwanActorStatusOwnedSource() noexcept;
    TaiwanActorStatusOwnedSource(const TaiwanActorStatusOwnedSource&)=delete;
    TaiwanActorStatusOwnedSource& operator=(const TaiwanActorStatusOwnedSource&)=delete;
    bool owns_presence(const std::shared_ptr<SharedWorldPresence>&) const noexcept;
    bool owns_incarnations(const std::shared_ptr<TaiwanActorStatusIncarnationSource>&) const noexcept;
    std::optional<Observation> observe(std::shared_ptr<const Input>,std::size_t,Equipment,Lease recipient) const noexcept;
    bool matches_inputs(const Observation&,const std::shared_ptr<const Input>&,
        std::size_t,const Equipment&,const Lease& recipient) const noexcept;
    // Pure cached input/private-state and atomic incarnation retention only.
    // No Session, SQL, callback, allocation or quiescence inference.
    bool retained(const Observation&) const noexcept;
    bool current(const Observation&) const noexcept;
    void stop() noexcept;
private:
    friend class SharedTaiwanNativeWorldHostPlan;
    friend class OwnedTaiwanPkReturnSceneSource;
    friend class OwnedTaiwanInitialActorSceneSource;
    friend class TaiwanActorStatusPublication;
    TaiwanActorStatusOwnedSource(const std::shared_ptr<SharedWorldPresence>&,
        std::shared_ptr<TaiwanActorStatusIncarnationSource>,Policy);
    // Actual real native.install boundary only. A failed/dropped attempt never
    // becomes clear, and this exact incarnation can never be reinitialized.
    std::optional<InitialInstall> begin_initial_install(Session&,const Lease&) noexcept;
    bool commit_initial_clear(const InitialInstall&) noexcept;
    void retire_initial_install(const InitialInstall&) noexcept;
    // Only the actual qualified Scene builder may bind the whole6F+EA bytes;
    // observe() itself never mints publication evidence.
    std::optional<TaiwanActorStatusPublication::ActorUnit> prepare_publication(
        const Observation&,std::span<const std::uint8_t> whole_unit) const noexcept;
    bool entry_retained(const Entry&) const noexcept;
    bool entry_current(const std::shared_ptr<Entry>&) const;
    bool retained_data(const Data&) const;
    const std::thread::id thread_=std::this_thread::get_id();
    const std::weak_ptr<SharedWorldPresence> presence_;
    const SharedWorldPresence* const presence_address_;
    const std::shared_ptr<TaiwanActorStatusIncarnationSource> incarnations_;
    const Policy policy_;
    const std::shared_ptr<Identity> identity_;
    std::map<std::uint64_t,std::shared_ptr<Entry>> entries_;
    std::uint64_t revision_=0;
    mutable bool busy_=false;
};
}
