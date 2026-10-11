#pragma once
#include "handlers/OwnedPkOutboxPublication.h"
#include "scripting/LuaEngine.h"

namespace god2 {
// CUSTOM-0123 concrete, opt-in TW BASIC1 rule/transport composition. This
// owner owns its Publication and binds it to exactly the supplied RoomState;
// a second independently supplied transport/room cannot split authority.
// Lua and RoomState/repository must outlive this owner on the SAME game
// executor. Construct after Lua initialization and drain/destroy Admission
// before this owner. No asynchronous callback captures Lua or this owner.
// This does not install Application hosting, invent seed/coefficients/order,
// schedule idle retries, rehydrate a room or return players to WORLD.
class OwnedTaiwanPkLuaBasicOwner final {
    friend class OwnedTaiwanPkBasicDriver;
public:
    using Parameters=OwnedPkOutboxPublication::BasicParameters;
    using NativeBatch=OwnedPkOutboxPublication::NativeBatch;
    using Advance=OwnedPkOutboxPublication::BasicAdvance;
    using Ticket=OwnedPkOutboxPublication::Ticket;
    using ReturnSceneSource=OwnedPkOutboxPublication::ReturnSceneSource; // CUSTOM-0133
    using WorldDeparture=OwnedPkOutboxPublication::WorldDeparture;

    OwnedTaiwanPkLuaBasicOwner(OwnedPkRoomState& rooms,LuaEngine& lua,
            Parameters parameters,std::array<std::uint8_t,2> server_order,ReturnSceneSource return_scene={})
        :lua_(lua),parameters_(checked(parameters)),order_(checked(server_order)),publication_(rooms,std::move(return_scene)){}
    OwnedTaiwanPkLuaBasicOwner(const OwnedTaiwanPkLuaBasicOwner&)=delete;
    OwnedTaiwanPkLuaBasicOwner& operator=(const OwnedTaiwanPkLuaBasicOwner&)=delete;

    // Admission supplies both original private committed holds before their
    // release. No entry/output send or callback registration occurs here.
    bool bind(const Ticket& ticket,const std::array<std::shared_ptr<Session>,2>& sessions,
            const std::array<Session::NativePkEntryHold,2>& holds,
            std::optional<WorldDeparture> departure={}){
        check_thread();return publication_.bind(ticket,sessions,holds,std::move(departure));
    }

    // One complete native frame only. Actual private binding derives identity,
    // profile, headers, phase and epoch. Client supplies no stats/Rule/order.
    // No resolution/output inside this input path, including Tick-only frames.
    std::optional<NativeBatch> dispatch_native_basic(Session& session,
            std::span<const RecoveredWorldRecords::Record> records){
        check_thread();return publication_.dispatch_native_basic(session,parameters_,records);
    }

    // Explicit later scheduler seam. Caller must establish the actual idle
    // boundary after ordinary ACK/entry/output completion and strand pending
    // clear, and retry AwaitingTransport later. Neither this method nor one
    // asio::post proves that boundary. OutputVisited/Resolved mean an owner
    // visit/settlement, NOT full write, peer ACK or native acceptance.
    std::optional<Advance> advance_at_idle(Session& session){
        return advance(session);
    }
private:
    // CUSTOM-0124 actual later game-timer visit, NOT an idle certificate.
    // The original Session strand staging remains the ACK/prefix authority.
    std::optional<Advance> advance_from_scheduled_turn(Session& session){return advance(session);}
    std::optional<Advance> advance(Session& session){
        check_thread();
        const Battle::Rule rule=[this](const CombatRuleInput& input){
            // Snapshot stats and roll originate in the actual room Battle.
            // Only this owner's immutable physical-basic policy is accepted.
            if(input.numeric_profile!=BattleNumericProfile::LegacyCustom || input.mp_cost!=0 ||
               input.power_percent!=parameters_.power_percent ||
               input.defense_percent!=parameters_.defense_percent ||
               input.critical_chance_bp!=parameters_.critical_chance_bp ||
               input.critical_multiplier_percent!=parameters_.critical_multiplier_percent)
                throw DatabaseError("TW PK Lua basic input differs from its immutable owner policy");
            return lua_.combat_damage(input); // CUSTOM-0006, not original balance.
        };
        // Synchronous call only. Publication checks actual Ready/both Written,
        // private profile/checkpoint before/after Lua, reentry and one settle.
        return publication_.advance_basic_notifications_at_idle(session,order_,rule);
    }
    LuaEngine& lua_;
    const Parameters parameters_;
    const std::array<std::uint8_t,2> order_;
    const std::thread::id thread_=std::this_thread::get_id();
    OwnedPkOutboxPublication publication_; // Destroy before borrowed Lua/rooms.

    static Parameters checked(Parameters value){
        if(value.power_percent>10000 || value.defense_percent>100 ||
           value.critical_chance_bp>10000 || value.critical_multiplier_percent<100 ||
           value.critical_multiplier_percent>1000)
            throw std::invalid_argument("TW PK Lua owner requires explicit bounded basic coefficients");
        return value;
    }
    static std::array<std::uint8_t,2> checked(std::array<std::uint8_t,2> value){
        if(value!=std::array<std::uint8_t,2>{0,1} && value!=std::array<std::uint8_t,2>{1,0})
            throw std::invalid_argument("TW PK Lua owner requires an explicit two-viewer execution order");
        return value;
    }
    void check_thread()const{
        if(thread_!=std::this_thread::get_id())
            throw std::logic_error("TW PK Lua owner game executor mismatch");
    }
};
}
