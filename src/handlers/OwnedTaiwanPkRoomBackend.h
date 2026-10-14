#pragma once
#include "handlers/OwnedTaiwanPkEntryPreparation.h"
#include "handlers/OwnedTaiwanPkBasicDriver.h"
#include <exception>
#include "handlers/OwnedPkEntryAdmission.h"

namespace god2 {
class SqliteDatabase;
// CUSTOM-0125 one concrete same-DB preparation/admission/basic transport owner.
// Only SqliteDatabase may assemble it. All calls/construction/destruction stay
// on the actual single-thread game executor; both real Sessions prove the
// supplied executor again at bind. Database, initialized Lua, executor and
// external callback captures outlive it. InvitationService borrows a RAW
// RoomAuthority pointer: drain its offers/completions BEFORE stop/destruction.
// Configured return uses the exact private Driver/Admission lifecycle below.
// Conditional Main hosting is explicit; full native provider/return and reconnect recovery remain open.
class OwnedTaiwanPkRoomBackend final:public OwnedPkInvitationService::AsyncRoomAuthority {
    friend class SqliteDatabase;
public:
    using Preparation=OwnedTaiwanPkEntryPreparation;
    using Parameters=OwnedTaiwanPkBasicDriver::Parameters;
    using ReturnSceneSource=OwnedTaiwanPkBasicDriver::ReturnSceneSource; // CUSTOM-0133
    using NativeBatch=OwnedTaiwanPkBasicDriver::NativeBatch;
    ~OwnedTaiwanPkRoomBackend() override{
        stopped_=true;resolvers_->stopped=true;retire_return_lifecycle();
        // Members then drain Admission before Driver/Publication and borrowed
        // Room/repository. External Invitation offers already must be drained.
    }
    OwnedTaiwanPkRoomBackend(const OwnedTaiwanPkRoomBackend&)=delete;
    OwnedTaiwanPkRoomBackend& operator=(const OwnedTaiwanPkRoomBackend&)=delete;

    std::optional<OwnedPkInvitationService::Reservation> prepare(
            const OwnedPkInvitationService::Pair& pair)override{
        check_thread();if(stopped_)return {};return admission_->prepare(pair);
    }
    bool current(const OwnedPkInvitationService::Reservation& reservation)override{
        check_thread();return !stopped_&&admission_->current(reservation);
    }
    bool commit(const OwnedPkInvitationService::Reservation&)override{return false;}
    bool begin_commit(const OwnedPkInvitationService::Accepted& accepted,Completion completion)override{
        check_thread();return !stopped_&&admission_->begin_commit(accepted,std::move(completion));
    }
    void abandon(const OwnedPkInvitationService::Reservation& reservation)noexcept override{
        // Admission preserves its existing thread guard and exact ticket lookup.
        admission_->abandon(reservation);
    }
    std::optional<NativeBatch> dispatch_native_basic(Session& session,
            std::span<const RecoveredWorldRecords::Record> records){
        check_thread();if(stopped_)throw DatabaseError("PK backend stopped; durable recovery required");
        return driver_->dispatch_native_basic(session,records);
    }
    void disconnected(Session& session){check_thread();driver_->disconnected(session);}
    void stop(){
        check_thread();if(stopped_)return;stopped_=true;resolvers_->stopped=true;
        retire_return_lifecycle(); // Before any callback or borrowed Admission teardown.
        // Keep Admission alive even if stop was requested from one of its
        // synchronous source callbacks. Invalidate weak entry callbacks first;
        // cancel reservations/close active peers, then cancel scheduled output.
        // Invitation offers must already be drained; no completion is invented.
        std::exception_ptr failure;
        try{admission_->stop();}catch(...){failure=std::current_exception();}
        try{driver_->stop();}catch(...){if(!failure)failure=std::current_exception();}
        if(failure)std::rethrow_exception(failure);
    }
private:
    static bool admission_return_lifecycle(OwnedPkEntryAdmission& admission,
            const OwnedPkOutboxPublication::ReturnLifecycle& token)noexcept{
        return admission.receive_return_lifecycle(token);
    }
    // Allocated by the one common factory before Driver/Admission construction.
    // Its private pointer is armed only after both owners are fully assembled;
    // Driver holds only a weak subscriber, never a RAW borrowed callback target.
    struct ReturnLifecycleCoordinator final:OwnedPkOutboxPublication::ReturnLifecycleOwner {
        OwnedPkEntryAdmission* admission=nullptr;
        bool stopped=false;
        bool native_pk_return_lifecycle(const OwnedPkOutboxPublication::ReturnLifecycle& token)override{
            if(stopped||!admission)return false;
            return OwnedTaiwanPkRoomBackend::admission_return_lifecycle(*admission,token);
        }
    };
    struct Resolvers {
        Preparation::Sessions sessions;
        Preparation::Initializations initializations;
        Preparation::Resolve peers;
        Preparation::Seed seed;
        Preparation::Companions companions;
        ReturnSceneSource return_scene;
        Preparation::Players players;
        bool stopped=false;
    };
    // Exactly one instance of every potentially mutable callable. Preparation
    // and Admission forward into this bundle, never copy its function targets.
    const std::shared_ptr<Resolvers> resolvers_;
    const std::shared_ptr<ReturnLifecycleCoordinator> return_lifecycle_;
    const std::thread::id thread_=std::this_thread::get_id();
    bool stopped_=false;
    // Reverse destruction order is essential: Admission callbacks/holds first,
    // then driver timer/Publication, preparation, mutable room, finally issuer.
    const std::unique_ptr<SqliteOwnedPkRoomRepository> repository_;
    const std::unique_ptr<OwnedPkRoomState> rooms_;
    const std::shared_ptr<Preparation> preparation_;
    const std::unique_ptr<OwnedTaiwanPkBasicDriver> driver_;
    const std::unique_ptr<OwnedPkEntryAdmission> admission_;

    OwnedTaiwanPkRoomBackend(std::shared_ptr<Resolvers> resolvers,
            std::shared_ptr<ReturnLifecycleCoordinator> return_lifecycle,
            std::unique_ptr<SqliteOwnedPkRoomRepository> repository,
            std::unique_ptr<OwnedPkRoomState> rooms,std::shared_ptr<Preparation> preparation,
            std::unique_ptr<OwnedTaiwanPkBasicDriver> driver,
            std::unique_ptr<OwnedPkEntryAdmission> admission)
        :resolvers_(std::move(resolvers)),return_lifecycle_(std::move(return_lifecycle)),
         repository_(std::move(repository)),rooms_(std::move(rooms)),
         preparation_(std::move(preparation)),driver_(std::move(driver)),admission_(std::move(admission)){
        // No callback/SQL/allocation: only the actual private matching Admission
        // is made visible after the complete backend ownership graph exists.
        return_lifecycle_->admission=admission_.get();
    }
    void retire_return_lifecycle()noexcept{
        return_lifecycle_->stopped=true;return_lifecycle_->admission=nullptr;
    }
    void check_thread()const{
        if(thread_!=std::this_thread::get_id())throw std::logic_error("PK backend game owner mismatch");
    }
    static void require_policy(Parameters p,std::array<std::uint8_t,2> order,
            std::chrono::milliseconds retry){
        // Same explicit bounds as the concrete Lua owner/driver. Check before
        // archive I/O or constructing any repository/source owners.
        if(p.power_percent>10000||p.defense_percent>100||p.critical_chance_bp>10000||
           p.critical_multiplier_percent<100||p.critical_multiplier_percent>1000||
           (order!=std::array<std::uint8_t,2>{0,1}&&order!=std::array<std::uint8_t,2>{1,0})||
           retry.count()<1||retry>std::chrono::seconds(1))
            throw std::invalid_argument("PK backend requires explicit bounded basic/order/retry policy");
    }
};
}
