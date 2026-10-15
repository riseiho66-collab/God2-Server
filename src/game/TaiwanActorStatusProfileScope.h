#pragma once
#include "game/OwnedTaiwanReturnActorSavedSource.h"
#include "game/TaiwanActorStatusIncarnationSource.h"
#include <cstddef>
#include <memory>
#include <optional>
#include <thread>
#include <utility>

namespace god2 {
// Private same-input/row/equipment and two-incarnation join only. This scope
// supplies no status values, Known/None/EA, writer permission or delivery proof.
class TaiwanActorStatusProfileScope final {
    struct Identity;
    struct Data;
    class Operation;
public:
    using Input=OwnedTaiwanReturnActorSavedSource::PopulationInput;
    using Equipment=OwnedTaiwanReturnActorSavedSource::ProfileEquipment;
    using Lease=SharedWorldPresence::Lease;
    using Incarnation=TaiwanActorStatusIncarnationSource::Token;
    class Observation final {
    public:
        Observation(const Observation&) noexcept=default;
        Observation& operator=(const Observation&) noexcept=default;
        const std::shared_ptr<const Input>& saved_input() const noexcept;
        std::size_t row_index() const noexcept;
        const Equipment& equipment() const noexcept;
        const Lease& source() const noexcept;
        const Lease& recipient() const noexcept;
        const Incarnation& source_incarnation() const noexcept;
        const Incarnation& recipient_incarnation() const noexcept;
        bool operator==(const Observation& other) const noexcept{return data_==other.data_;}
    private:
        friend class TaiwanActorStatusProfileScope;
        explicit Observation(std::shared_ptr<const Data> data) noexcept:data_(std::move(data)){}
        std::shared_ptr<const Data> data_;
    };
    static std::shared_ptr<TaiwanActorStatusProfileScope> create(
        std::shared_ptr<SharedWorldPresence>,std::shared_ptr<TaiwanActorStatusIncarnationSource>);
    ~TaiwanActorStatusProfileScope() noexcept;
    TaiwanActorStatusProfileScope(const TaiwanActorStatusProfileScope&)=delete;
    TaiwanActorStatusProfileScope& operator=(const TaiwanActorStatusProfileScope&)=delete;
    bool owns_presence(const std::shared_ptr<SharedWorldPresence>&) const noexcept;
    bool owns_incarnations(const std::shared_ptr<TaiwanActorStatusIncarnationSource>&) const noexcept;
    std::optional<Observation> observe(std::shared_ptr<const Input>,std::size_t,Equipment,Lease recipient) const noexcept;
    // Pure cached/private-node joins only. No saved SQL or status callback.
    bool matches_inputs(const Observation&,const std::shared_ptr<const Input>&,
        std::size_t,const Equipment&,const Lease& recipient) const noexcept;
    bool retained(const Observation&) const noexcept;
    // Adds actual game-owner Session/incarnation registry checks, no SQL.
    bool current(const Observation&) const noexcept;
    void stop() noexcept;
private:
    TaiwanActorStatusProfileScope(const std::shared_ptr<SharedWorldPresence>&,
        std::shared_ptr<TaiwanActorStatusIncarnationSource>);
    bool shape(const Data&) const noexcept;
    bool retained_data(const Data&) const;
    const std::thread::id thread_=std::this_thread::get_id();
    const std::weak_ptr<SharedWorldPresence> presence_;
    const SharedWorldPresence* const presence_address_;
    const std::shared_ptr<TaiwanActorStatusIncarnationSource> incarnations_;
    const std::shared_ptr<Identity> identity_;
    mutable bool busy_=false;
};
}
