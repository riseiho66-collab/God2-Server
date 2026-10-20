#pragma once
#include "db/SqliteOwnedEquipmentTransaction.h"
#include "handlers/RecoveredBankService.h"
#include "protocol/RecoveredBankItems.h"
#include <cstddef>
#include <memory>

namespace god2 {
class Session;
class RecoveredMovementService;
// CUSTOM-0160 whole-instance bank custody. This owner never grants cells/items or
// mirrors into legacy scalar/typed bank tables. Native split/merge is OPEN.
class SharedTaiwanOwnedBankSource final {
public:
    class Result final {
    public:
        Result(Result&&) noexcept=default;
        Result& operator=(Result&&) noexcept=default;
        Result(const Result&)=delete;
        Result& operator=(const Result&)=delete;
        const SqliteOwnedEquipmentTransaction::Committed& committed() const noexcept{return committed_;}
        // A false value means this is a read-only opening observation.
        bool mutated() const noexcept{return mutated_;}
        // A durable write stays durable even when delivery subsequently retires.
        // The host MUST retain its actual committed receipt, suppress wire and
        // retire the response path when false; never retry the mutation.
        bool delivery_current() const noexcept{return delivery_current_;}
        const std::vector<std::uint8_t>& wire() const noexcept{return wire_;}
        std::vector<std::uint8_t> take_wire() && noexcept{return std::move(wire_);}
    private:
        friend class SharedTaiwanOwnedBankSource;
        Result(SqliteOwnedEquipmentTransaction::Committed committed,std::vector<std::uint8_t> wire,
            bool mutated,bool delivery_current) noexcept
            :committed_(std::move(committed)),wire_(std::move(wire)),mutated_(mutated),delivery_current_(delivery_current) {}
        SqliteOwnedEquipmentTransaction::Committed committed_;
        std::vector<std::uint8_t> wire_;
        bool mutated_,delivery_current_;
    };
    // All borrowed sources must outlive game-owner drain. The money source is
    // the SAME actual money-bank service whose NPC-authorized open just ran.
    static std::shared_ptr<SharedTaiwanOwnedBankSource> create(
        std::shared_ptr<SqliteOwnedEquipmentTransaction>,AccountRepository&,
        RecoveredCharacterRepository&,RecoveredMovementService&,RecoveredBankService&,std::size_t max_sessions);
    ~SharedTaiwanOwnedBankSource();
    // Call after actual money.open succeeds, inside original world callback.
    // Requires all 300 bank cells explicitly present in the shared population.
    // Framed wire contains bounded S48 batches; missing cells refuse opening.
    std::optional<Result> open(Session&,std::uint16_t target);
    std::optional<Result> dispatch(Session&,const RecoveredBankItems::Request&);
    // Pure GAME-only final composition fence, including retained normal INIT,
    // money LeaseSource and the exact movement snapshot of this opening. No
    // NPC/provider/SQL call. Does not mint authority or extend lease lifetime.
    bool current(Session&) const;
    // Actual close/disconnect/scene-change/normal-init replacement must call
    // release; Application stop calls stop before borrowed sources are drained.
    void release(Session&);
    void invalidate_active();
    void stop();
private:
    struct Impl;
    explicit SharedTaiwanOwnedBankSource(std::unique_ptr<Impl>);
    std::unique_ptr<Impl> impl_;
};
}
