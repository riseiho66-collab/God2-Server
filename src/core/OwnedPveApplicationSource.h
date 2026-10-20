#pragma once
#include "game/OwnedPveWorldCatalog.h"
#include "handlers/OwnedPveRoomHost.h"
#include "handlers/RecoveredVisibility.h"
#include "handlers/RecoveredMovementService.h"
#include "db/SqliteDatabase.h"
#include "scripting/LuaEngine.h"
namespace god2 {
// Actual normal Taiwan Application mount, independent of fixture combat and
// the shared-common-world/paired PK host. Explicit complete catalog required.
class OwnedPveApplicationSource {
public:
    class ReturnHandoff {
    public:
        virtual ~ReturnHandoff()=default;
        virtual bool retained_current(Session&,const Session::OwnedPveBinding&)const noexcept=0;
        virtual void returned(Session&,const Session::OwnedPveBinding&,
            std::shared_ptr<SqliteOwnedPveRoomRepository>,const SqliteOwnedPveRoomRepository::ReturnContinuation&,
            const Session::OwnedPveReturnSource&)=0;
    };
    using PrepareReturnHandoff=std::function<std::shared_ptr<ReturnHandoff>(Session&,const Session::OwnedPveBinding&)>;
    OwnedPveApplicationSource(SqliteDatabase&,LuaEngine&,RecoveredMovementService&,
        RecoveredVisibility&,std::function<void(std::vector<RecoveredVisibility::Delivery>)>);
    ~OwnedPveApplicationSource();
    void install_return_handoff(PrepareReturnHandoff);
    bool bound(const Session&)const noexcept;
    void observe_world(Session&); // Actual ready callback, full current native material only.
    void committed_movement(Session&,const RecoveredMovementService::CommittedMove&);
    bool handle(Session&,std::span<const RecoveredWorldRecords::Record>);
    void observe_movement(Session&,std::span<const RecoveredWorldRecords::Record>,
        std::span<const std::uint8_t> final_response);
    void poll(); // Actual GAME scheduler, not a native ACK/turn timer.
    void disconnected(Session&);
    void retire_dispatch()noexcept; // Preserve canonical disconnect/save cleanup through host drain.
    void stop()noexcept;
private:
    using T=OwnedPveRoomTypes;using Binding=Session::OwnedPveBinding;
    struct WorldBefore {Binding binding;RecoveredPosition position;std::vector<RecoveredVisibility::Presence> actors;
        std::optional<std::vector<RecoveredVisibility::Presence>> return_actors;std::shared_ptr<ReturnHandoff> handoff;
        std::optional<RecoveredMovementService::WorldLocationObservation> movement;};
    struct Pending {std::weak_ptr<Session> session;Session::NormalWorldInitialization initialization;
        Session::WorldResponseWrite written;RecoveredPosition position;};
    std::shared_ptr<const OwnedPveRoomHost::Sources> sources(const OwnedPveWorldCatalog::Scene&);
    T::MemberInput member(const OwnedPveWorldCatalog::Scene&,const std::shared_ptr<Session>&,
        const Binding&,std::shared_ptr<const T::Snapshot>);
    std::vector<std::uint8_t> return_world(const std::shared_ptr<Session>&,const Binding&,
        const T::MemberInput&,const RecoveredWorldRecords::ContextNotification&);
    void title(Session&,bool);
    std::vector<std::uint8_t> world_reconciliation(Session&,
        const std::vector<RecoveredVisibility::Presence>& previous,
        const std::vector<RecoveredVisibility::Presence>& current);
    SqliteDatabase& db_;LuaEngine& lua_;RecoveredMovementService& movement_;RecoveredVisibility& visibility_;
    std::function<void(std::vector<RecoveredVisibility::Delivery>)> deliver_;
    std::shared_ptr<const OwnedPveWorldCatalog> catalog_;
    std::shared_ptr<SqliteOwnedPveRoomRepository> repository_;
    std::shared_ptr<OwnedPveRoomHost> host_;
    std::map<std::uint64_t,WorldBefore> worlds_;
    std::map<std::uint64_t,Pending> pending_;
    std::map<std::uint64_t,std::uint64_t> steps_;
    bool stopped_=false,retiring_=false,busy_=false;
    PrepareReturnHandoff prepare_return_handoff_;
};
}
