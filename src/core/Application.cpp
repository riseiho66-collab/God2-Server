#include "handlers/OwnedGuildSuccessionApplicationDraft.h"
#include "handlers/OwnedGuildSuccessionSemanticReceiptDraft.h"
#include "db/GuildSuccessionSqliteMigrationsDraft.h"
#include "db/GuildOfficerSqliteMigrations.h"
#include "core/Application.h"
#include "core/SharedWorldHostPlan.h"
#include "db/NativeWorldEntrySnapshotRepository.h"
#include "db/NativeCharacterSummarySnapshotRepository.h"
#include "db/SqliteNativeCharacterSummarySnapshotRepository.h"
#include "db/SqliteNativeWorldEntrySnapshotRepository.h"
#include "db/SqliteNativeEquipmentSnapshotRepository.h"
#include "db/SqliteOwnedInventoryRepository.h"
#include "cn/net/SharedCredentialServer.h"
#include "relations53/GuildRelations53SelectorDraft.h"
#include "relations53/SharedGuildApplication53Draft.h"
#include "relations53/GuildRelationCacheBootstrap53.h"
#include "protocol/StreamerPresentation.h"
#include "handlers/RecoveredFruitQuests.h"
#include "handlers/OwnedBlacklistService.h"
#include "handlers/OwnedPartyDirectoryService.h"
#include "game/OwnedClientOptions.h"
#include "protocol/RecoveredWorldEntryView.h"
#include "text/OwnedCharacterNameText.h"
#include "auth/RecoveredAccountLogin.h"
#include "handlers/RecoveredCharacterService.h"
#include "handlers/RecoveredCharacterGrowth.h"
#include "game/ExtendedExperienceAmount.h"
#include "handlers/OwnedAttributeAllocation.h"
#include "handlers/RecoveredMovementService.h"
#include "handlers/RecoveredWorldService.h"
#include "handlers/RecoveredWorldDisplays.h"
#include "handlers/RecoveredPlayerPresence.h"
#include "handlers/DiagnosticSupplyService.h"
#include "handlers/InventoryMoveService.h"
#include "game/SharedTaiwanOwnedBagMoveSource.h"
#include "handlers/InventoryDiscardService.h"
#include "handlers/OwnedInstanceDiscardService.h"
#include "handlers/RecoveredTradeService.h"
#include "handlers/OwnedInstanceTradeService.h"
#include "handlers/RecoveredBankService.h"
#include "handlers/RecoveredBankItemsService.h"
#include "handlers/OwnedArmorBankService.h"
#include "handlers/OwnedForeignBankService.h"
#include "handlers/OwnedMixedBankService.h"
#include "protocol/RecoveredNpcRecord.h"
#include "game/NativeParty.h"
#include "handlers/RecoveredPlayerSnapshot.h"
#include "handlers/RecoveredOwnedCompanions.h"
#include "handlers/RecoveredOwnedPetReserveMove.h"
#include "handlers/RecoveredPet2RevertGate.h"
#include "handlers/RecoveredPeerRoleText.h"
#include "handlers/DiagnosticQuestConversation.h"
#include "handlers/RecoveredKnowledgeConversation.h"
#include "handlers/RecoveredOwnedMapView.h"
#include "handlers/OwnedBeastPanelService.h"
#include "handlers/OwnedBeastBagService.h"
#include "handlers/OwnedBeastExplorationService.h"
#include "handlers/OwnedBeastEquipmentService.h"
#include "handlers/OwnedBeastDiscardService.h"
#include "handlers/RecoveredOwnedDailyQuestView.h"
#include "handlers/RecoveredOwnedSupply.h"
#include "handlers/OwnedWeaponTransferService.h"
#include "handlers/OwnedArmorTransferService.h"
#include "handlers/OwnedPartyPositionQuery.h"
#include "handlers/OwnedPkInvitationService.h"
#include "handlers/OwnedBagMutationProof.h"
#include "handlers/OwnedGuildPanelService.h"
#include "handlers/OwnedGuildMembershipService.h"
#include "handlers/OwnedGuildEntryService.h"
#include "handlers/OwnedGuildLeaderPanelService.h"
#include "handlers/OwnedGuildKickService.h"
#include "handlers/OwnedGuildOfficerRuntimeDraft.h"
#include "handlers/OwnedGuildOfficerWorldHostDraft.h"
#include "handlers/OwnedGuildDisbandService.h" // CUSTOM-0081 candidate, additive service only.
#include "handlers/OwnedGuildAnnouncementService.h"
#include "handlers/OwnedGuildAnnouncementBatch.h"
#include "handlers/OwnedTeleportGemOffer.h"
#include "handlers/RecoveredOwnedPlayerAppearance.h"
#include "handlers/RecoveredWeaponSexRestriction.h"
#include "protocol/RecoveredEquipmentRejection.h"
#include "protocol/RecoveredInventory.h"
#include "protocol/RecoveredInventoryProjection.h"
#include "handlers/RecoveredBattleService.h"
#include "protocol/RecoveredBattleBootstrap.h"
#include "core/Scheduler.h"
#include "game/FixtureBattle.h"
#include "game/DiagnosticBattleRecovery.h"
#include "game/DiagnosticDoorRule.h"
#include "db/SqliteDatabase.h"
#include "db/ServerSqliteMigrations.h"
#include "db/SqliteRecoveredCharacterRepository.h"
#include "db/DbTypes.h"
#include "net/IoContextPool.h"
#include "net/TcpServer.h"
#include "net/WebServerPlan.h"
#include "handlers/HandlerContext.h"
#include "text/ChineseText.h"
#include "text/LegacyChineseCodec.h"
#include "protocol/RecoveredChat.h"
#include "handlers/OwnedPartyChatService.h"
#include "handlers/OwnedPrivateChatService.h"
#include "handlers/OwnedGuildChatService.h"
#include "handlers/OwnedGuildRosterService.h"
#include "handlers/RegisterHandlers.h"
#include "protocol/OpcodeDispatcher.h"
#include "protocol/Opcode.h"
#include "protocol/PacketWriter.h"
#include "protocol/RecoveredServerRoutes.h"
#include "protocol/RecoveredWorldFrame.h"
#include "protocol/DiagnosticBattleParticipants.h"
#include "protocol/DiagnosticShunyingManual.h"
#include "protocol/ShunyingSanshazhanReply.h"
#include "protocol/ThousandBullsReply.h"
#include "protocol/DiagnosticThousandBullsManual.h"
#include "protocol/DiagnosticShunyingEquipment.h"
#include "protocol/DiagnosticBattleRevival.h"
#include "protocol/RecoveredBattleEntry.h"
#include "protocol/RecoveredRoleVitals.h"
#include "protocol/RecoveredQuestDialogue.h"
#include "protocol/RecoveredQuestSync.h"
#include "protocol/RecoveredWorldClock.h"
#include "protocol/DiagnosticQuestNpc.h"
#include "protocol/DiagnosticTownNpc.h"
#include "protocol/DiagnosticRemoteActor.h"
#include <set>
#include <algorithm>
#include <spdlog/spdlog.h>
#include <future>
#include <random>
#include <map>
#include <csignal>
#include <cstdlib>
#include <thread>
#include <limits>
#include <utility>
#include <exception>
namespace god2 {
namespace {
using ScriptTimes=std::map<std::filesystem::path,std::filesystem::file_time_type>;
ScriptTimes script_times(const std::filesystem::path& root) {
    ScriptTimes times;
    for(const auto& entry:std::filesystem::recursive_directory_iterator(root))
        if(entry.is_regular_file() && entry.path().extension()==".lua") times.emplace(entry.path(),entry.last_write_time());
    return times;
}
// Only the explicit common-world Application path uses this owner. Network
// templates/Session copies retain facades, never the real affine callbacks.
class WorldLifecycleVault final : public std::enable_shared_from_this<WorldLifecycleVault> {
    enum class Operation {Idle,Factory,Preparing,PreparedActor,Ready,Cleanup,Entry,Publication,Movement,Records,Characters};
    struct Slot {
        Session* session;
        std::shared_ptr<const Session::CommonWorldLifecycle> hooks;
        std::function<void()> cleanup;
        Session::CommonWorldLifecycle::ReadyCompletion pending;
        Session::CommonWorldPublication publication;
        std::uint64_t ready_nonce=0,publication_nonce=0;
    };
    const std::thread::id thread_=std::this_thread::get_id();
    const std::size_t capacity_;
    bool closed_=false;
    Operation operation_=Operation::Idle;
    std::uint64_t active_id_=0;
    Session::CommonWorldLifecycleFactory factory_;
    TaiwanWorldEntryIdentity entry_identity_=TaiwanWorldEntryIdentity::SelectedCharacter;
    SharedTaiwanWorldEntrySource::Entry entry_;
    SharedTaiwanMovementSource::Binding movement_;
    SharedTaiwanWorldRecordSource::Binding records_;
    SharedTaiwanNativeCharacterListSource::Binding characters_;
    bool entry_reentered_=false;
    bool actor_reentered_=false;
    std::map<std::uint64_t,Slot> slots_;
    void owner() const {
        if(thread_!=std::this_thread::get_id())throw std::logic_error("World lifecycle vault game owner mismatch");
    }
    void reject_movement_reentry() {
        if(operation_==Operation::PreparedActor) {
            actor_reentered_=true;
            throw std::logic_error("World lifecycle prepared actor source reentered");
        }
        if(operation_==Operation::Entry && characters_.selected) {
            entry_reentered_=true;
            if(characters_.invalidate_selection)characters_.invalidate_selection(active_id_);
            if(characters_.invalidate_active)characters_.invalidate_active();
            throw std::logic_error("World lifecycle native selected entry reentered");
        }
        if(operation_==Operation::Characters) {
            if(characters_.invalidate_active)characters_.invalidate_active();
            throw std::logic_error("World lifecycle native character source reentered");
        }
        if(operation_==Operation::Movement || operation_==Operation::Records) {
            // Propagate the rejected outer facade call to the actual source.
            // A provider catching this exception cannot authorize a later CAS.
            const auto record=records_.invalidate_active;const auto move=movement_.invalidate_active;
            std::exception_ptr failure;
            try {if(record)record();}catch(...) {failure=std::current_exception();}
            try {if(move)move();}catch(...) {if(!failure)failure=std::current_exception();}
            if(failure)std::rethrow_exception(failure);
            throw std::logic_error("World lifecycle native movement reentered");
        }
    }
    void available() {
        owner();
        reject_movement_reentry();
        if(closed_ || operation_!=Operation::Idle)
            throw std::logic_error("World lifecycle vault closed or reentered");
    }
    struct OperationGuard {
        WorldLifecycleVault& vault;
        OperationGuard(WorldLifecycleVault& v,Operation op,std::uint64_t id):vault(v) {
            vault.available();vault.operation_=op;vault.active_id_=id;
        }
        ~OperationGuard() {vault.operation_=Operation::Idle;vault.active_id_=0;}
    };
    void consume(std::uint64_t id) {
        owner();if(closed_)return;
        OperationGuard guard(*this,Operation::Cleanup,id);
        const auto found=slots_.find(id);if(found==slots_.end())return;
        auto slot=std::move(found->second);slots_.erase(found);
        // Remove the slot before the real callback; even a throw cannot retain
        // its hooks/cleanup in a late Session facade or consume it twice.
        std::exception_ptr failure;
        try {if(records_.release)records_.release(*slot.session);}catch(...) {failure=std::current_exception();}
        try {if(movement_.release)movement_.release(*slot.session);}catch(...) {if(!failure)failure=std::current_exception();}
        try {if(slot.hooks->cancel)slot.hooks->cancel(*slot.session);}catch(...) {if(!failure)failure=std::current_exception();}
        try {if(auto cleanup=std::exchange(slot.cleanup,{}))cleanup();}catch(...) {if(!failure)failure=std::current_exception();}
        // Detach every real callback before invoking it. Callback reentry/late
        // facades find no slot; cancellation cannot retain affine payloads.
        auto publication=std::move(slot.publication);auto pending=std::move(slot.pending);
        try {if(publication.queued)publication.queued(false);}catch(...) {if(!failure)failure=std::current_exception();}
        try {if(pending)pending(false);}catch(...) {if(!failure)failure=std::current_exception();}
        if(failure)std::rethrow_exception(failure);
    }
    std::shared_ptr<const Session::CommonWorldLifecycle> create(Session& session) {
        available();const auto id=session.id();
        if(!id || session.closing() || !factory_ || slots_.contains(id) || slots_.size()>=capacity_)
            throw std::invalid_argument("World lifecycle vault requires a fresh actual Session and capacity");
        std::shared_ptr<const Session::CommonWorldLifecycle> actual;
        {
            OperationGuard guard(*this,Operation::Factory,id);actual=factory_(session);
        }
        if(!actual || !actual->prepared || bool(actual->ready)==bool(actual->ready_async) ||
           bool(actual->ready_async)!=bool(actual->cancel) ||
           (entry_identity_==TaiwanWorldEntryIdentity::QualifiedSceneHandle && !actual->prepared_actor))
            throw std::invalid_argument("World lifecycle vault requires complete actual hooks");
        auto facade=std::make_shared<Session::CommonWorldLifecycle>();
        const auto self=shared_from_this();
        facade->prepared=[self,id](Session& current,const RecoveredWorldEntry::Frame& frame) {
            self->available();
            const auto found=self->slots_.find(id);
            if(!id || current.id()!=id || found==self->slots_.end() || found->second.session!=&current)
                throw std::invalid_argument("World lifecycle prepared Session identity mismatch");
            auto hooks=found->second.hooks;
            bool accepted=false;std::exception_ptr failure;
            {
                OperationGuard guard(*self,Operation::Preparing,id);
                try {accepted=hooks->prepared(current,frame);}catch(...) {failure=std::current_exception();}
            }
            if(failure) {self->consume(id);std::rethrow_exception(failure);}
            if(!accepted)self->consume(id);
            return accepted;
        };
        if(actual->prepared_actor)facade->prepared_actor=[self,id](Session& current,const RecoveredWorldEntry::Frame& input) {
            self->available();
            const auto found=self->slots_.find(id);
            if(!id || current.id()!=id || found==self->slots_.end() || found->second.session!=&current ||
               !found->second.hooks->prepared_actor)
                throw std::invalid_argument("World lifecycle prepared actor Session identity mismatch");
            const auto hooks=found->second.hooks;const auto pinned=current.shared_from_this();const auto frame=input;
            const auto account=current.account_id,character=current.character_id,battle=current.battle_generation();
            std::optional<std::uint16_t> actor;std::exception_ptr failure;
            {
                OperationGuard guard(*self,Operation::PreparedActor,id);self->actor_reentered_=false;
                try {actor=hooks->prepared_actor(current,frame);}catch(...) {failure=std::current_exception();}
            }
            const auto retained=self->slots_.find(id);
            if(self->actor_reentered_ || self->closed_ || retained==self->slots_.end() ||
               retained->second.session!=pinned.get() || retained->second.hooks!=hooks || current.closing() ||
               current.account_id!=account || current.character_id!=character || current.battle_generation()!=battle ||
               !actor || !qualified_taiwan_scene_handle(*actor))actor.reset();
            if(failure) {self->consume(id);std::rethrow_exception(failure);}
            if(!actor)self->consume(id);
            return actor;
        };
        if(actual->ready)facade->ready=[self,id](Session& current) {
            self->available();
            const auto found=self->slots_.find(id);
            if(!id || current.id()!=id || found==self->slots_.end() || found->second.session!=&current)
                throw std::invalid_argument("World lifecycle ready Session identity mismatch");
            auto hooks=found->second.hooks;
            bool accepted=false;std::exception_ptr failure;
            {
                OperationGuard guard(*self,Operation::Ready,id);
                try {accepted=hooks->ready(current);}catch(...) {failure=std::current_exception();}
            }
            if(failure) {self->consume(id);std::rethrow_exception(failure);}
            if(!accepted)self->consume(id);
            return accepted;
        };
        if(actual->ready_async) {
            facade->ready_async=[self,id](Session& current,Session::CommonWorldLifecycle::ReadyCompletion complete) {
                self->available();const auto found=self->slots_.find(id);
                if(current.id()!=id || found==self->slots_.end() || found->second.session!=&current ||
                   !complete || found->second.pending || found->second.ready_nonce==std::numeric_limits<std::uint64_t>::max())
                    throw std::invalid_argument("World lifecycle async ready requires actual fresh Session completion");
                const auto nonce=++found->second.ready_nonce;
                auto hooks=found->second.hooks;
                // Allocate revocable weak facade before transferring real done.
                Session::CommonWorldLifecycle::ReadyCompletion facade_done=[weak=std::weak_ptr<WorldLifecycleVault>(self),id,nonce](bool accepted) {
                    const auto vault=weak.lock();if(!vault)return;vault->owner();
                    if(vault->closed_)return;
                    const auto slot=vault->slots_.find(id);
                    if(slot==vault->slots_.end() || slot->second.ready_nonce!=nonce || !slot->second.pending)return;
                    if(vault->operation_!=Operation::Idle &&
                       !(vault->operation_==Operation::Ready && vault->active_id_==id)) {
                        vault->reject_movement_reentry();
                        throw std::logic_error("World lifecycle completion reentered another operation");
                    }
                    auto done=std::move(slot->second.pending);
                    done(accepted);
                };
                found->second.pending=std::move(complete);
                std::exception_ptr failure;
                {
                    OperationGuard guard(*self,Operation::Ready,id);
                    try {hooks->ready_async(current,std::move(facade_done));}catch(...) {failure=std::current_exception();}
                } // No operation guard is retained across deferred publication.
                if(failure) {
                    const auto slot=self->slots_.find(id);
                    if(slot!=self->slots_.end() && slot->second.pending) {
                        self->consume(id);std::rethrow_exception(failure);
                    }
                    // A provider that throws after inline completion cannot
                    // consume an already delivered readiness result again.
                }
            };
            facade->cancel=[self,id](Session& current) {
                self->owner();if(self->closed_)return;self->available();
                const auto found=self->slots_.find(id);if(found==self->slots_.end())return;
                if(current.id()!=id || found->second.session!=&current)
                    throw std::invalid_argument("World lifecycle async cancel Session identity mismatch");
                self->consume(id);
            };
        }
        if(!slots_.emplace(id,Slot{&session,std::move(actual),{},{},{},0,0}).second)
            throw std::logic_error("World lifecycle Session already owned");
        return facade;
    }
public:
    explicit WorldLifecycleVault(std::size_t capacity):capacity_(capacity) {
        if(!capacity_)throw std::invalid_argument("World lifecycle vault requires explicit Session capacity");
    }
    void install(Session::CommonWorldLifecycleFactory factory,
                 TaiwanWorldEntryIdentity identity=TaiwanWorldEntryIdentity::SelectedCharacter) {
        available();if(!valid_taiwan_world_entry_identity(identity) || !factory || factory_)
            throw std::invalid_argument("World lifecycle vault factory already set or incomplete");
        factory_=std::move(factory);entry_identity_=identity;
    }
    void install_entry(SharedTaiwanWorldEntrySource::Entry entry) {
        available();if(!entry || entry_)throw std::invalid_argument("World lifecycle vault entry already set or incomplete");
        entry_=std::move(entry);
    }
    void install_native_characters(SharedTaiwanNativeCharacterListSource::Binding actual) {
        available();
        if(!actual.list || !actual.select || !actual.invalidate_active || !actual.current || !actual.complete ||
           (actual.selected && !actual.invalidate_selection) || characters_.list || characters_.select)
            throw std::invalid_argument("World lifecycle requires fresh complete actual native character sources");
        characters_=std::move(actual);
    }
    decltype(Session::RecoveredCharacterHandlers::native_list) native_list_facade() {
        available();if(!characters_.list)throw std::logic_error("World lifecycle native list source missing");
        return [weak=weak_from_this()](Session& session) {
            const auto vault=weak.lock();
            if(!vault)throw std::logic_error("World lifecycle native character owner expired");
            OperationGuard guard(*vault,Operation::Characters,session.id());
            if(!vault->characters_.list)throw std::logic_error("World lifecycle native list source revoked");
            return vault->characters_.list(session);
        };
    }
    decltype(Session::RecoveredCharacterHandlers::native_select) native_select_facade() {
        available();if(!characters_.select)throw std::logic_error("World lifecycle native selection source missing");
        return [weak=weak_from_this()](Session& session,const RecoveredPostCreateSelect::Selection& input,std::optional<std::uint64_t> created) {
            const auto vault=weak.lock();
            if(!vault)throw std::logic_error("World lifecycle native character owner expired");
            OperationGuard guard(*vault,Operation::Characters,session.id());
            if(!vault->characters_.select)throw std::logic_error("World lifecycle native selection source revoked");
            return vault->characters_.select(session,input,created);
        };
    }
    decltype(Session::RecoveredCharacterHandlers::native_list_current) native_list_current_facade() {
        available();if(!characters_.current)throw std::logic_error("World lifecycle native list Current missing");
        return [weak=weak_from_this()](Session& session,const Session::NativeCharacterList& delivery) {
            const auto vault=weak.lock();if(!vault)throw std::logic_error("World lifecycle native character owner expired");
            OperationGuard guard(*vault,Operation::Characters,session.id());
            if(!vault->characters_.current)throw std::logic_error("World lifecycle native list Current revoked");
            return vault->characters_.current(session,delivery);
        };
    }
    decltype(Session::RecoveredCharacterHandlers::native_list_complete) native_list_complete_facade() {
        available();if(!characters_.complete)throw std::logic_error("World lifecycle native list completion missing");
        return [weak=weak_from_this()](Session& session,const Session::NativeCharacterList& delivery,bool written) {
            const auto vault=weak.lock();if(!vault)throw std::logic_error("World lifecycle native character owner expired");
            OperationGuard guard(*vault,Operation::Characters,session.id());
            if(!vault->characters_.complete)throw std::logic_error("World lifecycle native list completion revoked");
            return vault->characters_.complete(session,delivery,written);
        };
    }
    SharedTaiwanWorldEntrySource::Entry entry_facade() {
        available();if(!entry_)throw std::invalid_argument("World lifecycle vault actual entry source missing");
        return [self=shared_from_this()](std::uint64_t session,std::uint64_t account,std::uint64_t character) {
            self->available();
            if(!session || !account || !character || !self->entry_)
                throw std::invalid_argument("World lifecycle entry requires actual Session/account/character identity");
            OperationGuard guard(*self,Operation::Entry,session);
            self->entry_reentered_=false;
            const auto frame=self->entry_(session,account,character);
            if(self->entry_reentered_)
                throw std::logic_error("World lifecycle native selected entry caught rejected reentry");
            return frame;
        };
    }
    void install_movement(SharedTaiwanMovementSource::Binding actual) {
        available();
        if(!actual.movement || !actual.release || !actual.invalidate_active ||
           movement_.movement || movement_.release || movement_.invalidate_active)
            throw std::invalid_argument("World lifecycle requires a complete fresh actual native movement source");
        movement_=std::move(actual);
    }
    decltype(Session::RecoveredCharacterHandlers::movement) movement_facade() {
        available();
        if(!movement_.movement || !movement_.release || !movement_.invalidate_active)
            throw std::invalid_argument("World lifecycle actual native movement source missing");
        return [weak=weak_from_this()](Session& session,std::span<const RecoveredMovement::Request> requests) {
            const auto vault=weak.lock();
            if(!vault)throw std::logic_error("World lifecycle native movement owner expired");
            vault->available();const auto id=session.id();const auto slot=vault->slots_.find(id);
            if(!id || slot==vault->slots_.end() || slot->second.session!=&session ||
               slot->second.pending || slot->second.publication.publish ||
               !vault->movement_.movement || session.closing() || session.state()!=SessionState::InWorld)
                throw std::invalid_argument("World lifecycle native movement requires this completed actual Session scene");
            OperationGuard guard(*vault,Operation::Movement,id);
            return vault->movement_.movement(session,requests);
        };
    }
    void install_records(SharedTaiwanWorldRecordSource::Binding actual) {
        available();
        if(!movement_.movement || !actual.records || !actual.release || !actual.invalidate_active ||
           records_.records || records_.release || records_.invalidate_active)
            throw std::invalid_argument("World lifecycle requires a fresh complete actual mixed native source");
        records_=std::move(actual);
    }
    decltype(Session::RecoveredCharacterHandlers::world_records) records_facade() {
        available();
        if(!records_.records || !records_.release || !records_.invalidate_active)
            throw std::invalid_argument("World lifecycle mixed native source missing");
        return [weak=weak_from_this()](Session& session,std::span<const RecoveredWorldRecords::Record> records) {
            const auto vault=weak.lock();
            if(!vault)throw std::logic_error("World lifecycle native record owner expired");
            vault->available();const auto id=session.id();const auto slot=vault->slots_.find(id);
            if(!id || slot==vault->slots_.end() || slot->second.session!=&session ||
               slot->second.pending || slot->second.publication.publish || !vault->records_.records ||
               session.closing() || (session.state()!=SessionState::InWorld && session.state()!=SessionState::InBattle))
                throw std::invalid_argument("World lifecycle native records require this completed actual Session scene");
            OperationGuard guard(*vault,Operation::Records,id);
            const auto invoke=vault->records_.records;
            return invoke(session,records);
        };
    }
    Session::CommonWorldLifecycleFactory factory_facade() {
        available();return [self=shared_from_this()](Session& session) {return self->create(session);};
    }
    std::function<std::function<void()>(Session&,std::function<void()>)> cleanup_owner() {
        available();return [self=shared_from_this()](Session& session,std::function<void()> actual) {
            self->owner();const auto id=session.id();
            self->reject_movement_reentry();
            if(self->closed_)throw std::logic_error("World lifecycle cleanup owner revoked");
            const auto found=self->slots_.find(id);
            if(!id || self->operation_!=Operation::Preparing || self->active_id_!=id ||
               found==self->slots_.end() || found->second.session!=&session || !actual || found->second.cleanup)
                throw std::invalid_argument("World lifecycle cleanup requires this actual prepared Session");
            // Allocate the facade before publishing the moved actual closure.
            std::function<void()> facade=[self,id] {self->consume(id);};
            found->second.cleanup=std::move(actual);return facade;
        };
    }
    std::function<void(Session&)> abandon_facade() {
        available();return [self=shared_from_this()](Session& session) {
            self->owner();if(self->closed_)return;
            self->available();const auto id=session.id();
            if(!id)throw std::invalid_argument("World lifecycle abandon requires actual Session identity");
            const auto found=self->slots_.find(id);if(found==self->slots_.end())return;
            if(found->second.session!=&session)
                throw std::invalid_argument("World lifecycle abandon Session identity mismatch");
            self->consume(id);
        };
    }
    std::function<Session::CommonWorldPublication(Session&,Session::CommonWorldPublication)> publication_owner() {
        available();return [self=shared_from_this()](Session& session,Session::CommonWorldPublication actual) {
            self->owner();const auto id=session.id();
            self->reject_movement_reentry();
            if(self->closed_ || (self->operation_!=Operation::Idle &&
               !(self->operation_==Operation::Ready && self->active_id_==id)))
                throw std::logic_error("World entry publication owner revoked or reentered");
            const auto found=self->slots_.find(id);
            if(!id || found==self->slots_.end() || found->second.session!=&session || !found->second.pending ||
               !actual.publish || !actual.queued || found->second.publication.publish ||
               found->second.publication_nonce==std::numeric_limits<std::uint64_t>::max())
                throw std::invalid_argument("World entry publication requires exact pending Session and fresh callbacks");
            const auto nonce=found->second.publication_nonce+1;
            const auto weak=std::weak_ptr<WorldLifecycleVault>(self);
            Session::CommonWorldPublication facade;
            facade.publish=[weak,id,nonce] {
                const auto vault=weak.lock();if(!vault)return false;vault->owner();
                if(vault->closed_)return false;vault->available();
                const auto slot=vault->slots_.find(id);
                if(slot==vault->slots_.end() || slot->second.publication_nonce!=nonce ||
                   !slot->second.publication.publish || slot->second.session->closing())return false;
                OperationGuard guard(*vault,Operation::Publication,id);
                return slot->second.publication.publish();
            };
            facade.queued=[weak,id,nonce](bool accepted) {
                const auto vault=weak.lock();if(!vault)return;vault->owner();
                if(vault->closed_)return;vault->available();
                const auto slot=vault->slots_.find(id);
                if(slot==vault->slots_.end() || slot->second.publication_nonce!=nonce || !slot->second.publication.queued)return;
                auto actual=std::move(slot->second.publication);
                slot->second.publication={}; // Once, before owner callback reentry.
                actual.queued(accepted);
            };
            found->second.publication_nonce=nonce;
            found->second.publication=std::move(actual);return facade;
        };
    }
    void revoke() noexcept {
        if(thread_!=std::this_thread::get_id() || operation_!=Operation::Idle)std::terminate();
        if(closed_)return;
        closed_=true; // Deny every new factory/prepared/ready before real cleanup.
        auto slots=std::move(slots_);
        slots_.clear();
        for(auto& [id,slot]:slots) {
            try {if(records_.release)records_.release(*slot.session);}catch(...) {}
            try {if(movement_.release)movement_.release(*slot.session);}catch(...) {}
            try {if(slot.hooks->cancel)slot.hooks->cancel(*slot.session);}catch(...) {}
            try {if(auto cleanup=std::exchange(slot.cleanup,{}))cleanup();}catch(...) {}
            auto publication=std::move(slot.publication);auto pending=std::move(slot.pending);
            try {if(publication.queued)publication.queued(false);}catch(...) {}
            try {if(pending)pending(false);}catch(...) {}
            slot.hooks.reset();
        }
        slots.clear();characters_={};records_={};movement_={};factory_={};entry_={}; // All source captures die on game, with DB alive.
    }
};
// Game-owned source callbacks borrow movement/storage. Network copies retain
// only weak facades; revocation runs before those borrowed owners are destroyed.
struct WholeBagMoveHost {
    std::shared_ptr<SqliteOwnedEquipmentTransaction> transaction;
    RecoveredMovementService* movement=nullptr; // Actual game-owned service; cleared before borrowed owner destruction.
    std::optional<SharedTaiwanOwnedBagMoveSource::MutationBinding> binding;
    std::shared_ptr<RecoveredWorldService> service;
    struct MutationDraft {
        std::weak_ptr<Session> session;
        Session::NormalWorldInitialization initialization;
        std::optional<SqliteOwnedEquipmentTransaction::Committed> after;
        bool invalid=false;
        MutationDraft(std::weak_ptr<Session> actual,Session::NormalWorldInitialization entry)
            :session(std::move(actual)),initialization(std::move(entry)) {}
    };
    struct MutationResponse {
        std::weak_ptr<Session> session;
        SqliteOwnedEquipmentTransaction::Committed after;
        Session::NormalWorldInitialization initialization;
        Session::WorldResponseWrite write;
    };
    std::shared_ptr<MutationDraft> active;
    std::map<std::uint64_t,std::shared_ptr<const MutationResponse>> mutations;
    std::size_t actual_session_capacity=0;
    bool live=true,accepting=true;
    void stop_dispatch() noexcept {
        accepting=false;
        if(active)active->invalid=true;
        mutations.clear();
        try {if(binding)binding->invalidate_active();}catch(...) {}
    }
    void revoke() noexcept {
        live=false;stop_dispatch();service.reset();binding.reset();movement=nullptr;transaction.reset();
    }
};
struct WholeBagMoveHostGuard {
    std::shared_ptr<WholeBagMoveHost> host;
    ~WholeBagMoveHostGuard(){if(host)host->revoke();}
};
struct WorldLifecycleVaultGuard {
    std::shared_ptr<WorldLifecycleVault> vault;
    ~WorldLifecycleVaultGuard() {if(vault)vault->revoke();}
};
}
static int run_server_impl(const Config& config,const cn::SharedServerPlan* cn_plan,const WebServerPlan* web_plan,unsigned run_for_seconds,
                           const SharedWorldHostPlan* world_plan=nullptr) {
    config.validate_owned_whole_bag_moves();
    if(config.owned_whole_bag_moves_enabled && world_plan)
        throw std::invalid_argument("Normal-entry whole bag moves cannot borrow or compete with an explicit shared world plan");
    const auto taiwan_entry_identity=world_plan?world_plan->taiwan_entry_identity:TaiwanWorldEntryIdentity::SelectedCharacter;
    if(world_plan && (bool(world_plan->make_taiwan_entered)==bool(world_plan->make_taiwan_entered_async) || !config.recovered_account_auth || config.mock_login ||
       config.protocol_mode!=ProtocolMode::God2LegacyCharacterListCandidate || !config.recovered_character_creation ||
       !config.recovered_dual_connection || !config.recovered_world_entry || !config.recovered_movement))
        throw std::invalid_argument("Shared world host requires actual provider and complete native TW login/world configuration");
    if(world_plan && world_plan->make_taiwan_entered_async && !world_plan->make_taiwan_world_entry)
        throw std::invalid_argument("Deferred native TW scene publication requires an explicit full native entry source");
    if(world_plan && world_plan->make_taiwan_movement &&
       (!world_plan->make_taiwan_entered_async || !world_plan->make_taiwan_world_entry))
        throw std::invalid_argument("Explicit native TW movement requires the actual async scene and full native entry sources");
    if(world_plan && world_plan->make_taiwan_world_records && !world_plan->make_taiwan_movement)
        throw std::invalid_argument("Explicit native TW mixed records require the actual same-host movement source");
    if(world_plan && (!valid_taiwan_world_entry_identity(taiwan_entry_identity) ||
       (taiwan_entry_identity==TaiwanWorldEntryIdentity::QualifiedSceneHandle &&
        (!world_plan->make_taiwan_native_characters || !world_plan->make_taiwan_world_entry ||
         !world_plan->make_taiwan_entered_async || !world_plan->make_taiwan_movement))))
        throw std::invalid_argument("Independent TW scene identity requires complete native selection, entry, scene and movement owners");
    if(world_plan && world_plan->requires_native_world_entry_snapshots && !world_plan->make_taiwan_world_entry)
        throw std::invalid_argument("Stored native TW material requires the explicit complete entry factory");
    if(world_plan && world_plan->requires_native_character_summaries && !world_plan->make_taiwan_native_characters)
        throw std::invalid_argument("Stored native TW list material requires the explicit complete character factory");
    if(world_plan && world_plan->make_taiwan_world_entry &&
       (config.owned_player_appearance_enabled || config.diagnostic_owned_weapon_appearance ||
        config.diagnostic_shunying_manual || config.diagnostic_remote_actor ||
        config.diagnostic_player_visibility || config.diagnostic_town_player_visibility ||
        config.diagnostic_visibility_battle))
        throw std::invalid_argument("Full native TW entry requires independent actual appearance/visibility sources; candidate projection modes are incompatible");
    asio::io_context game;
    // The network context can retain queued session/acceptor callbacks containing
    // game executors even after its workers join. Destroy it before the game context.
    IoContextPool network;
    auto game_work=asio::make_work_guard(game);
    std::promise<void> ready;
    auto initialized=ready.get_future();
    network.start(config.worker_threads);
    std::exception_ptr failure;
    std::thread game_thread([&] {
        bool announced=false;
        try {
            bool native_records_lab=false;
#ifdef _WIN32
            char* native_lab_environment=nullptr;std::size_t native_lab_length=0;
            if(_dupenv_s(&native_lab_environment,&native_lab_length,"GOD2_NATIVE_WORLD_RECORDS_LAB")!=0)
                throw std::runtime_error("Cannot read native record lab option");
            native_records_lab=native_lab_environment && std::string_view(native_lab_environment)=="1";
            std::free(native_lab_environment);
#else
            const auto* native_lab_environment=std::getenv("GOD2_NATIVE_WORLD_RECORDS_LAB");
            native_records_lab=native_lab_environment && std::string_view(native_lab_environment)=="1";
#endif
            if(config.owned_whole_bag_moves_enabled && native_records_lab)
                throw std::invalid_argument("Whole bag moves cannot combine native record lab fixture populations");
            if(native_records_lab && (config.host!="127.0.0.1" || config.port!=2598 ||
                !config.database.parent_path().filename().string().starts_with("private-native-blackbox-")))
                throw std::runtime_error("Native record lab requires disposable private-native-blackbox DB and loopback2598");
            // CUSTOM-0078: explicit current-client acceptance gateway only.
            // No formal entry mapping or player grants are inferred from this.
            bool guild_membership_lab=false;
#ifdef _WIN32
            char* guild_lab_environment=nullptr;std::size_t guild_lab_length=0;
            if(_dupenv_s(&guild_lab_environment,&guild_lab_length,"GOD2_NATIVE_GUILD_MEMBERSHIP_LAB")!=0)
                throw std::runtime_error("Cannot read guild membership lab option");
            guild_membership_lab=guild_lab_environment && std::string_view(guild_lab_environment)=="1";
            std::free(guild_lab_environment);
#else
            const auto* guild_lab_environment=std::getenv("GOD2_NATIVE_GUILD_MEMBERSHIP_LAB");
            guild_membership_lab=guild_lab_environment && std::string_view(guild_lab_environment)=="1";
#endif
            if(guild_membership_lab && !native_records_lab)
                throw std::runtime_error("Guild membership lab requires the disposable native-record lab gate");
            // CUSTOM-0078 ordinary help entry requires the separately qualified
            // append2996 resource bundle. Original2995 clients cannot display it.
            bool guild_entry_lab=false;
#ifdef _WIN32
            char* entry_environment=nullptr;std::size_t entry_length=0;
            if(_dupenv_s(&entry_environment,&entry_length,"GOD2_NATIVE_GUILD_ENTRY_LAB")!=0)
                throw std::runtime_error("Cannot read guild entry lab option");
            guild_entry_lab=entry_environment && std::string_view(entry_environment)=="1";
            std::free(entry_environment);
#else
            const auto* entry_environment=std::getenv("GOD2_NATIVE_GUILD_ENTRY_LAB");
            guild_entry_lab=entry_environment && std::string_view(entry_environment)=="1";
#endif
            if(guild_entry_lab && !guild_membership_lab)
                throw std::runtime_error("Guild entry lab requires disposable membership lab and append2996 client resources");
            // CUSTOM-0078: the configured feature never enables lab privileges.
            if(config.owned_guild_membership_enabled && (native_records_lab || guild_membership_lab || guild_entry_lab))
                throw std::runtime_error("Formal guild membership cannot borrow native lab privileges");
            const bool guild_membership_enabled=config.owned_guild_membership_enabled || guild_membership_lab;
            const bool guild_entry_enabled=config.owned_guild_membership_enabled || guild_entry_lab;
            // CUSTOM-0078: Tick may bootstrap diagnostic combat without an actor
            // request. Exclude those experiments from this modal-input lab so
            // an opening cannot survive an unobserved battle/return cycle.
            if(guild_membership_lab && (config.fixture_battle || config.diagnostic_battle_transition ||
               config.diagnostic_battle_after_movement || config.diagnostic_battle_participants ||
               config.diagnostic_battle_player_appearance || config.diagnostic_battle_animations ||
               config.diagnostic_battle_skill_seed || config.diagnostic_shunying_manual ||
               config.diagnostic_thousand_bulls_manual || config.diagnostic_recording_fixed_damage ||
               config.diagnostic_battle_skill_kind || config.diagnostic_battle_revival ||
               config.diagnostic_battle_skill_settlement || config.diagnostic_battle_mp_refusal ||
               config.diagnostic_battle_resources || config.diagnostic_battle_experience ||
               config.diagnostic_battle_terminal || config.diagnostic_role_progress ||
               config.diagnostic_level_snapshot || config.diagnostic_character_growth ||
               config.diagnostic_resume_checkpoint || config.diagnostic_progress_span ||
               config.diagnostic_visibility_battle || config.diagnostic_visibility_skill_recovery ||
               config.diagnostic_town_battle_after_quest || config.diagnostic_town_return_after_battle ||
               config.diagnostic_town_door_after_battle || config.diagnostic_battle_rounds!=1 ||
               config.diagnostic_encounter_limit!=1))
                throw std::runtime_error("Guild membership lab cannot mix diagnostic battle or progression experiments");
            // Startup and --migrate-only retain installed exact50 storage even with gameplay disabled.
            const GuildRelations53FlagsDraft flags53{config.owned_guild_membership_enabled,config.owned_guild_announcements_enabled,config.owned_guild_officers_enabled,config.owned_guild_succession_enabled,config.owned_guild_relations53_enabled};
            const auto migrations=configured_guild_relations53(config.database,flags53);
            SqliteDatabase database(config.database,migrations);database.initialize();database.migrate();
            // One same-repository host on this game owner, retained through all
            // listener/controller drain. No native placement or data is created.
            std::shared_ptr<SharedWorldHost> common_world;
            SharedTaiwanWorldLifecycle::Entered taiwan_entered;
            SharedTaiwanWorldLifecycle::AsyncOwner taiwan_entered_async;
            SharedTaiwanWorldEntrySource::Entry taiwan_world_entry;
            SharedTaiwanMovementSource::Binding taiwan_movement;
            SharedTaiwanWorldRecordSource::Binding taiwan_records;
            SharedTaiwanNativeCharacterListSource::Binding taiwan_native_characters;
            if(world_plan) {
                common_world=std::make_shared<SharedWorldHost>(database.recovered_characters());
                // Only the explicit stored-entry plan requests this capability.
                // Same migrated Database object; accessor performs no SQL/DDL.
                // Its raw material is qualified later by the actual suppliers.
                auto* entry_snapshots=world_plan->requires_native_world_entry_snapshots?
                    &database.native_world_entries():nullptr;
                if(entry_snapshots && !entry_snapshots->owns_sources(database.accounts(),database.recovered_characters()))
                    throw std::invalid_argument("TW entry reader does not own the actual common account/character sources");
                auto* entry_writer=entry_snapshots?&database.native_world_entry_writer():nullptr;
                if(entry_writer && static_cast<NativeWorldEntrySnapshotRepository*>(entry_writer)!=entry_snapshots)
                    throw std::invalid_argument("TW entry writer differs from the actual entry reader");
                auto* summary_snapshots=world_plan->requires_native_character_summaries?
                    &database.native_character_summaries():nullptr;
                auto* equipment_snapshots=world_plan->requires_native_equipment_snapshots?
                    &database.native_equipment_snapshots():nullptr;
                auto* equipment_writer=equipment_snapshots?&database.native_equipment_snapshot_writer():nullptr;
                if(equipment_snapshots && (!equipment_writer ||
                   static_cast<NativeEquipmentSnapshotRepository*>(equipment_writer)!=equipment_snapshots ||
                   !equipment_writer->owns_sources(database.accounts(),database.recovered_characters())))
                    throw std::invalid_argument("TW equipment requires the exact common delivery reader/writer sources");
                auto* owned_inventory=world_plan->requires_owned_inventory_storage?&database.owned_inventory_storage():nullptr;
                auto* owned_inventory_writer=owned_inventory?&database.owned_inventory_writer():nullptr;
                if(owned_inventory && (!owned_inventory_writer ||
                   static_cast<OwnedInventoryRepository*>(owned_inventory_writer)!=owned_inventory ||
                   !owned_inventory_writer->owns_sources(database.accounts(),database.recovered_characters())))
                    throw std::invalid_argument("TW inventory requires exact shared custody reader/writer sources");
                auto* summary_accounts=(summary_snapshots || equipment_snapshots || owned_inventory)?&database.accounts():nullptr;
                auto* summary_writer=summary_snapshots?&database.native_character_summary_writer():nullptr;
                if(summary_snapshots && !summary_snapshots->owns_sources(*summary_accounts,database.recovered_characters()))
                    throw std::invalid_argument("TW list reader does not own the actual common account/character sources");
                if(summary_writer && static_cast<NativeCharacterSummarySnapshotRepository*>(summary_writer)!=summary_snapshots)
                    throw std::invalid_argument("TW list writer differs from the actual summary reader");
                const SharedWorldHostPlan::Context context{database.recovered_characters(),
                    database.native_map_catalog(),game.get_executor(),common_world,
                    &database.native_skill_catalog(),entry_snapshots,summary_accounts,summary_snapshots,summary_writer,entry_writer,
                    &database.native_enemy_display_catalog(),equipment_snapshots,equipment_writer,owned_inventory,owned_inventory_writer,
                    &database.companions()};
                if(world_plan->make_taiwan_entered_async) {
                    taiwan_entered_async=world_plan->make_taiwan_entered_async(context);
                    if(!taiwan_entered_async.entered || !taiwan_entered_async.cancel)
                        throw std::invalid_argument("Shared world host requires actual deferred Taiwan scene and cancellation owners");
                }else taiwan_entered=world_plan->make_taiwan_entered(context);
                if((!taiwan_entered && !taiwan_entered_async.entered) || !common_world->owns_repository(database.recovered_characters()))
                    throw std::invalid_argument("Shared world host requires actual Taiwan Entered owner on the same repository");
                if(world_plan->make_taiwan_world_entry) {
                    taiwan_world_entry=world_plan->make_taiwan_world_entry(context);
                    if(!taiwan_world_entry)throw std::invalid_argument("Shared world host requires actual selected Taiwan entry source");
                }
                if(world_plan->make_taiwan_movement) {
                    taiwan_movement=world_plan->make_taiwan_movement(context);
                    if(!taiwan_movement.movement || !taiwan_movement.release || !taiwan_movement.invalidate_active)
                        throw std::invalid_argument("Shared world host requires actual Taiwan movement, release and active invalidation sources");
                }
                if(world_plan->make_taiwan_world_records) {
                    taiwan_records=world_plan->make_taiwan_world_records(context);
                    if(!taiwan_records.records || !taiwan_records.release || !taiwan_records.invalidate_active)
                        throw std::invalid_argument("Shared world host requires complete actual Taiwan mixed record sources");
                }
                if(world_plan->make_taiwan_native_characters) {
                    taiwan_native_characters=world_plan->make_taiwan_native_characters(context);
                    if(!taiwan_native_characters.list || !taiwan_native_characters.select || !taiwan_native_characters.invalidate_active ||
                       !taiwan_native_characters.current || !taiwan_native_characters.complete)
                        throw std::invalid_argument("Shared world host requires complete actual Taiwan list/token sources");
                }
                // Check the actual constructed owners after all external factories.
                // An explicit independent handle must never fall through to the
                // legacy selected-character movement when a supplier changes plan metadata.
                if(taiwan_entry_identity==TaiwanWorldEntryIdentity::QualifiedSceneHandle &&
                   (!taiwan_world_entry || !taiwan_entered_async.entered || !taiwan_entered_async.cancel ||
                    !taiwan_movement.movement || !taiwan_movement.release || !taiwan_movement.invalidate_active ||
                    !taiwan_movement.retire || !taiwan_native_characters.list || !taiwan_native_characters.select ||
                    !taiwan_native_characters.current || !taiwan_native_characters.complete ||
                    !taiwan_native_characters.invalidate_active || !taiwan_native_characters.selected ||
                    !taiwan_native_characters.invalidate_selection))
                    throw std::invalid_argument("Independent TW scene identity lacks complete actual constructed native owners");
            }
            if(config.owned_beast_panel_enabled)database.install_beast_snapshot_schema();
            // Keep persisted player-created identity available when writes are
            // disabled, so a kill switch cannot borrow legacy0077 authority.
            auto* guild_membership_repository=migrations.back().version==53?&database.guild53(flags53).original():migrations.back().version==52?&database.guild_membership52():migrations.back().version==51?&database.guild_membership51():&database.candidate_guild_membership();
            spdlog::info("OWNED_GUILD_RUNTIME enabled={} ordinary_entry={} lab={} schema={} CUSTOM-0078",
                guild_membership_enabled,guild_entry_enabled,guild_membership_lab,migrations.back().version);
            spdlog::info("OWNED_GUILD_ANNOUNCEMENT_RUNTIME enabled={} CUSTOM-0078",config.owned_guild_announcements_enabled);
            spdlog::get("database")->info("SQLite initialized; migrations applied: {}",config.database.string());
            if(config.fruit_village_quests_enabled)database.fruit_sources().require_qualified();
            const auto npc_sources=database.native_npc_display_catalog().count();
            spdlog::info("NATIVE_NPC_DISPLAY_READY records={} authority=LIVE_MEMORY_VERIFIED_SOURCE_DISPLAY_ONLY no_spawn_or_stat_claim",npc_sources);
            const auto enemy_sources=database.native_enemy_display_catalog().counts();
            spdlog::info("NATIVE_ENEMY_DISPLAY_READY records={} visible={} groups={} authority=LIVE_MEMORY_VERIFIED_SOURCE_DISPLAY_ONLY no_spawn_or_stat_claim",enemy_sources.records,enemy_sources.lookup_visible,enemy_sources.groups);
            const auto quest_sources=database.native_quest_catalog().counts();
            if(config.owned_daily_quest_views_enabled && database.native_quest_catalog().daily_displays().size()!=85)
                throw DatabaseError("Owned daily views require complete pinned native316 catalog");
            if(config.owned_supply_enabled && !database.native_supply_catalog().is_imported())
                throw DatabaseError("Owned supply requires complete pinned MED02 declarations");
            if(database.native_armor_catalog().populated())
                spdlog::info("NATIVE_ARMOR_DEFINITIONS equ=692 teq=662 authority=NATIVE_PARSED_DEFINITION_ONLY no_instances no_combat_formula");
            if(database.native_weapon_catalog().populated())
                spdlog::info("NATIVE_WEAPON_DEFINITIONS wpn=630 twp=629 authority=NATIVE_PARSED_DEFINITION_ONLY no_instances no_combat_formula");
            if(config.owned_weapon_transfers_enabled && !database.native_weapon_catalog().populated())
                throw DatabaseError("Owned weapon transfers require complete pinned native definitions");
            if(config.owned_map_views_enabled) {
                if(!database.native_map_item_catalog().contains(5569) || !database.native_map_item_catalog().contains(5576))
                    throw DatabaseError("Owned map views require pinned SPI sources");
                for(const auto item:{5569,5576}) {
                    const auto map=database.native_map_catalog().lookup(NativeMapCatalog::current_dataset_id,item==5576?4:2,item==5576?3:4);
                    if(!map || !RecoveredOwnedMapView::qualified_map(*map,static_cast<std::uint16_t>(item)))
                        throw DatabaseError("Owned map views require pinned regional map source");
                }
                spdlog::info("OWNED_MAP_VIEW_READY source_items=5569,5576 no_grants no_consumption CUSTOM-0044");
            }
            if(database.native_multi_message_catalog().populated()) {
                const auto count=database.native_multi_message_catalog().knowledge_menu_count();
                spdlog::get("database")->info("NATIVE_MULTI_MESSAGE_SOURCE keys={} text_rows=11794 validated_menu=1434 authority=SOURCE_DISPLAY_ONLY no_npc_or_quest_authority",count);
            }
            spdlog::get("database")->info("NATIVE_QUEST_SOURCE_CATALOG definitions={} descriptions={} requirement_display={} daily_source={} authority=source_display_only gameplay_rules=unrecovered",
                quest_sources.definitions,quest_sources.descriptions,quest_sources.requirements,quest_sources.daily);
            const bool fixture_mode=config.protocol_mode==ProtocolMode::Fixture;
            if(!fixture_mode)database.trades().install_schema();
            if(!fixture_mode){database.banks().install_schema();database.bank_access().install_schema();}
            if(!fixture_mode)database.bank_items().install_schema();
            if(!fixture_mode && config.owned_beast_panel_enabled && config.owned_mixed_bank_enabled)database.install_beast_bank_schema();
            std::optional<ChineseText> fixture_text;
            std::optional<ChineseText> native_chat_text;
            LuaEngine lua(config.script_root,fixture_mode,
                [&database](std::int64_t area, std::int64_t scene) {
                    return database.native_map_catalog().lookup(
                        NativeMapCatalog::current_dataset_id,area,scene);
                },
                [&database](std::int64_t kind, std::int64_t definition_id) {
                    return database.native_skill_catalog().lookup(
                        NativeSkillCatalog::current_dataset_id,kind,definition_id);
                },
                [&database](std::int64_t kind, std::int64_t definition_id) {
                    return database.native_skill_book_catalog().lookup(kind,definition_id);
                },[&database](std::uint16_t item){return database.native_weapon_catalog().lookup(item);},
                [&database](std::uint16_t item){return database.native_armor_catalog().lookup(item);});
            if(!lua.initialize() || !lua.load_script(config.bootstrap)) throw std::runtime_error("Lua bootstrap failed");
            std::unique_ptr<FixtureBattleService> fixture_battles;
            if(config.fixture_battle) {
                fixture_battles=std::make_unique<FixtureBattleService>(
                    [&lua](const FixtureCombatant& attacker,const FixtureCombatant& defender,
                           std::uint8_t skill,std::uint32_t roll) {
                        return lua.fixture_damage(attacker,defender,skill,roll);
                    });
                spdlog::warn("CUSTOM_TEST_NOT_NATIVE: isolated C++/Lua combat enabled; no original-client combat claim");
            }
            World world;
            if(fixture_mode) {
                world.initialize();
                spdlog::get("world")->info("World initialized with mock map 1");
            }
            OpcodeDispatcher dispatcher; register_handlers(dispatcher);
            asio::thread_pool authentication_workers(4);
            RecoveredAccountLogin recovered_accounts(database.accounts(),config.local_account_registration);
            Session::RecoveredLoginHandler recovered_login;
            if(config.recovered_account_auth) recovered_login=[&](const RecoveredC2S0002::Parsed& request) {
                return recovered_accounts.authenticate(request);
            };
            auto async_login=[&](const RecoveredC2S0002::Parsed& request,RecoveredAccountLogin::Completion done) {
                recovered_accounts.authenticate_async(request,authentication_workers.get_executor(),game.get_executor(),std::move(done));
            };
            if(config.recovered_account_auth)
                spdlog::info("Recovered account authentication enabled; local first-login registration={}; loopback only",config.local_account_registration);
            RecoveredCharacterService recovered_characters(database.recovered_characters());
            std::unique_ptr<RecoveredMovementService> recovered_movement;
            std::unique_ptr<RecoveredBattleService> diagnostic_combat;
            if(config.diagnostic_battle_participants)
                diagnostic_combat=std::make_unique<RecoveredBattleService>([&](auto input){
                    if(config.diagnostic_recording_fixed_damage)return RecordingCombatTest::rule(input);
                    return lua.combat_damage(input);
                });
            std::set<std::uint64_t> diagnostic_battle_sent;
            std::map<std::uint64_t,std::pair<std::uint16_t,std::uint16_t>> world_display_scene;
            std::set<std::uint64_t> native_monster_placement_gap_logged;
            std::map<std::uint64_t,bool> diagnostic_movement_ready;
            std::map<std::uint64_t,unsigned> diagnostic_encounters_started;
            std::set<std::uint64_t> diagnostic_world_resources_sent;
            std::set<std::uint64_t> owned_player_and_companions_projected;
            // Game-owned material at the ACTUAL fresh-world companion sender.
            // This retains saved deity revisions/provenance + exact batches;
            // passive exact socket-write handles are separately retained below.
            // No common lease, battle actor, ACK or durable skill authority.
            enum class CompanionWriteObservation {Pending,InitializationUnavailable,InitializationPending,
                PrefixUnavailable,NoRecords,WrittenSavedDeityCurrent,WrittenSavedDeityPrefixCurrent,Stale,Failed};
            struct OwnedCompanionRestorationSource {
                std::weak_ptr<Session> session;
                std::uint64_t account,character,battle_generation_at_restore;
                SessionState phase_at_restore;
                std::shared_ptr<const RecoveredOwnedCompanions::Restoration> material;
                std::size_t submission_calls_completed=0;
                bool all_submission_calls_returned=false;
                std::vector<Session::WorldRecordsWrite> write_observations;
                // Historical result at a later actual game callback only. It
                // must never be consumed as permanent current/grant authority.
                CompanionWriteObservation last_observed_write=CompanionWriteObservation::Pending;
                std::optional<Session::NormalWorldInitialization> normal_initialization;
                // Expected local DATA-prefix only. A later consumer must again
                // requalify normal epoch, saved source and all referenced full
                // catalog rows;
                // never a remote afterstate, battle list, actor or grant.
                std::optional<TaiwanNativeDeityRosterPrefix> expected_receiving_prefix;
            };
            std::map<std::uint64_t,std::shared_ptr<OwnedCompanionRestorationSource>> owned_companion_restoration_sources;
            // CUSTOM-0096: source353 actual original-response custody plus peer attempt chain.
            // Original response Queued means its validated final wire entered the FIFO.
            // Pending endpoints remain provisional, never native adoption or socket Written.
            constexpr std::size_t blacklist_attempt_limit=256; // Existing Session max_writes transport bound.
            struct BlacklistLivePending {
                const std::shared_ptr<const Session::NormalWorldOutputHandle> output;
                const std::shared_ptr<const BlacklistLivePending> previous;
                const std::size_t depth;
                std::optional<Session::NormalWorldOutputAttempt> attempt;
                std::vector<std::uint8_t> logical=std::vector<std::uint8_t>(21);
                BlacklistLivePending(std::shared_ptr<const Session::NormalWorldOutputHandle> handle,
                        std::shared_ptr<const BlacklistLivePending> prior)
                    :output(std::move(handle)),previous(std::move(prior)),depth(previous?previous->depth+1:1) {}
                // No per-node snapshots or fictitious own-reply nodes: only actual attempts.
            };
            struct BlacklistReplay {
                std::weak_ptr<Session> session;
                std::uint64_t account,character,battle;
                std::uint32_t cursor=0;
                bool done=false;
                bool active_phase=false; // Clear all inactive IDs before any active A5.
                std::shared_ptr<const SqliteOwnedBlacklistRepository::Snapshot> snapshot;
                bool live_disabled=false; // Never revive a stale incarnation by accidental DB equality.
                std::shared_ptr<const Session::NormalWorldOutputHandle> output;
                std::shared_ptr<BlacklistLivePending> live_pending;
                std::optional<Session::NormalWorldResponseAttempt> own_response;
            };
            std::map<std::uint64_t,BlacklistReplay> blacklist_replays;
            const auto blacklist_lifetime=std::make_shared<std::atomic_bool>(true);
            const auto retire_blacklist_output=[&](BlacklistReplay& replay) noexcept {
                if(replay.output)replay.output->revoke();
                if(replay.live_pending && replay.live_pending->output)replay.live_pending->output->revoke();
                replay.output.reset();replay.live_pending.reset();replay.own_response.reset();
            };
            const auto stop_blacklist_outputs=[&]() noexcept {
                blacklist_lifetime->store(false);
                for(auto& [id,replay]:blacklist_replays)retire_blacklist_output(replay);
            };
            const auto blacklist_pending_source=[](const BlacklistReplay& replay) {
                return bool(replay.live_pending) || (replay.own_response &&
                    replay.own_response->status()==Session::NormalWorldResponseStatus::Pending);
            };
            // Pure Current: safe inside the existing SQL source callback. Never settle,
            // mutate a map, close a peer or invoke a game/source observer here.
            const auto blacklist_chain_current=[&](const std::shared_ptr<Session>& peer,const BlacklistReplay& replay) {
                // An original endpoint must not bypass Failed custody merely because
                // this incarnation has no incoming peer attempt nodes.
                if(replay.own_response && !peer->normal_world_response_current_on_game(*replay.own_response))return false;
                if(!replay.live_pending)return true;
                if(replay.live_disabled || !replay.output || !replay.snapshot || !replay.snapshot->supported ||
                   !peer->normal_world_output_current_on_game(*replay.output))return false;
                std::size_t count=0;
                for(std::shared_ptr<const BlacklistLivePending> node=replay.live_pending;node;node=node->previous) {
                    if(++count>blacklist_attempt_limit || node->output!=replay.output ||
                       node->depth!=replay.live_pending->depth-count+1 || !node->attempt ||
                       node->attempt->status()==Session::NormalWorldOutputStatus::Failed)return false;
                }
                return count==replay.live_pending->depth;
            };
            // Called on this actual game owner. Copy all identities before any close.
            const auto settle_blacklist_output=[&](const std::shared_ptr<Session>& peer) {
                const auto at=blacklist_replays.find(peer->id());
                if(at==blacklist_replays.end() || at->second.session.lock()!=peer ||
                   (!at->second.live_pending && !at->second.own_response))return;
                const auto source=at->second;const auto pending=source.live_pending;
                bool accepted=blacklist_chain_current(peer,source),queued=accepted;
                if(accepted)for(std::shared_ptr<const BlacklistLivePending> node=pending;node;node=node->previous)
                    queued=queued && node->attempt->status()==Session::NormalWorldOutputStatus::Queued;
                if(accepted && source.live_pending)accepted=peer->normal_world_output_current_on_game(*source.output);
                const auto now=blacklist_replays.find(peer->id());
                if(now==blacklist_replays.end() || now->second.session.lock()!=peer || now->second.live_pending!=pending ||
                   now->second.output!=source.output || now->second.snapshot!=source.snapshot ||
                   now->second.own_response!=source.own_response)return;
                if(!accepted){now->second.live_disabled=true;retire_blacklist_output(now->second);peer->close();}
                else if(queued)now->second.live_pending.reset(); // Clear attempts only; never rewind the submitted endpoint.
            };
            std::unique_ptr<OwnedBlacklistService> owned_blacklist;
            if(config.owned_blacklist_enabled)
                owned_blacklist=std::make_unique<OwnedBlacklistService>(database.blacklist());
            std::set<std::uint64_t> owned_supply_projected;
            // CUSTOM-0016: source text amounts; cap/consumption remain custom.
            const std::string supply_source="70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731";
            const auto qualified_supply_policy=[&database](std::uint16_t item,std::uint16_t target) {
                const auto& catalog=database.native_supply_catalog();
                return catalog.is_imported() ?
                    DiagnosticSupplyService::native_declared_policy(catalog,item,target) :
                    DiagnosticSupplyService::current_supply_policy(item,target);
            };
            auto& supply_repository=static_cast<SqliteRecoveredCharacterRepository&>(database.recovered_characters());
            RecoveredFruitQuests fruit_quests(database.fruit_quests());
            RecoveredOwnedCompanions owned_companions(database.companions());
            const auto observe_companion_restoration_write=[&](Session& session) {
                const auto at=owned_companion_restoration_sources.find(session.id());
                if(at==owned_companion_restoration_sources.end())return;
                const auto source=at->second;
                const auto local=[&] {
                    const auto found=owned_companion_restoration_sources.find(session.id());
                    return found!=owned_companion_restoration_sources.end() && found->second==source &&
                        source->session.lock().get()==&session && source->material && !session.closing() &&
                        source->account==session.account_id && source->character==session.character_id &&
                        source->phase_at_restore==session.state() && session.recovered_world_ready() &&
                        source->battle_generation_at_restore==session.battle_generation();
                };
                source->last_observed_write=CompanionWriteObservation::Pending;
                source->expected_receiving_prefix.reset();
                if(!local()){source->last_observed_write=CompanionWriteObservation::Stale;return;}
                if(!source->normal_initialization) {
                    source->last_observed_write=CompanionWriteObservation::InitializationUnavailable;return;
                }
                if(!session.normal_world_initialization_current(*source->normal_initialization)) {
                    source->last_observed_write=CompanionWriteObservation::Stale;return;
                }
                if(!source->normal_initialization->entry_written()) {
                    source->last_observed_write=CompanionWriteObservation::InitializationPending;return;
                }
                if(!source->all_submission_calls_returned)return;
                const auto& batches=source->material->batches();
                if(source->submission_calls_completed!=batches.size() || source->write_observations.size()!=batches.size()) {
                    source->last_observed_write=CompanionWriteObservation::Failed;return;
                }
                for(std::size_t i=0;i<batches.size();++i) {
                    const auto& observation=source->write_observations[i];
                    if(observation.logical()!=batches[i] || !session.world_records_write_current(observation)) {
                        source->last_observed_write=CompanionWriteObservation::Stale;return;
                    }
                    const auto status=observation.status();
                    if(status==Session::WorldRecordsWriteStatus::Failed) {
                        source->last_observed_write=CompanionWriteObservation::Failed;return;
                    }
                    if(status!=Session::WorldRecordsWriteStatus::Written)return;
                }
                // No network callback retains this source/repository. This is
                // the actual next world-records game callback, AFTER all exact
                // frames wrote. Pet bytes wrote too; only deity state is read
                // here, and no source freshness during the write is claimed.
                bool saved_current=false;
                try {saved_current=owned_companions.restoration_current(*source->material);}
                catch(...) {
                    // A passive observation failure is explicit, not a fake
                    // empty roster or a new rejection of unrelated gameplay.
                    source->last_observed_write=CompanionWriteObservation::Failed;return;
                }
                const auto initialization_current=[&] {
                    return local() && session.normal_world_initialization_current(*source->normal_initialization) &&
                        source->normal_initialization->entry_written();
                };
                if(!saved_current || !initialization_current()) {
                    source->last_observed_write=CompanionWriteObservation::Stale;return;
                }
                source->last_observed_write=CompanionWriteObservation::WrittenSavedDeityCurrent;
                // Actual normal-entry/saved/exact-write caller, not an unused
                // model API. Lookup only the real shared catalog and retain
                // full owned110-byte definitions; no filesystem-profile swap.
                try {
                    auto prefix=owned_companions.normal_entry_prefix(*source->material,database.native_skill_catalog());
                    if(!prefix) {
                        source->last_observed_write=CompanionWriteObservation::PrefixUnavailable;return;
                    }
                    if(!initialization_current() ||
                       !owned_companions.normal_entry_prefix_current(*source->material,*prefix,database.native_skill_catalog()) ||
                       !initialization_current()) {
                        source->last_observed_write=CompanionWriteObservation::Stale;return;
                    }
                    source->expected_receiving_prefix=std::move(prefix);
                    source->last_observed_write=batches.empty()?CompanionWriteObservation::NoRecords:
                        CompanionWriteObservation::WrittenSavedDeityPrefixCurrent;
                } catch(...) {
                    source->expected_receiving_prefix.reset();
                    source->last_observed_write=CompanionWriteObservation::Failed;
                }
            };
    RecoveredPet2RevertGate pet2_revert_gate(supply_repository,database.companions());
            OwnedWeaponTransferService weapon_transfers(database.weapon_slots());
            OwnedArmorTransferService armor_transfers(database.armor_slots());
            std::set<std::uint64_t> owned_armor_projected;
            if(config.owned_armor_transfers_enabled) {
                if(!database.native_armor_catalog().populated())throw DatabaseError("Owned armor requires complete native definitions");
                spdlog::info("OWNED_ARMOR_TRANSFERS_ENABLED CUSTOM-0066 instance_only no_grants no_formula no_appearance");
            }

            std::set<std::uint64_t> owned_weapons_projected;
            OwnedTeleportGemOffer teleport_gem_offers;
            std::set<std::uint64_t> owned_gems_projected;
            const auto gem_projection=[](const StoredTeleportGemSlot& slot) {
                const auto logical=RecoveredInventoryProjection::encode({slot.slot,slot.count,slot.metadata20});
                if(!logical)throw DatabaseError("Owned teleport gem projection rejected");
                return *logical;
            };
            const auto qualified_weapon=[&](std::uint16_t item) {
                const auto row=database.native_weapon_catalog().lookup(item);
                return row && (row->family=="WPN" || row->family=="TWP") && row->parsed_record.size()==396 && (row->parsed_record[0x11a]&4)!=0;
            };
            DiagnosticSupplyService diagnostic_supply(supply_repository,lua);
            // CUSTOM-0037: only the already-owned scalar map/MED02 inventory
            // qualifies. Native 497FE0 clears 50x24 bytes; the existing 41 grant
            // then leaves item WORD + 18 zero metadata bytes. No equipment,
            // enhancement or arbitrary captured instance is reconstructed here.
            const auto bag_slot_eligible=[&](const StoredInventorySlot& slot) {
                return slot.source_sha256==supply_source && slot.count<=127 &&
                    (slot.count ? (((slot.item_id==5569 || (config.owned_map_views_enabled && slot.item_id==5576 &&
                                    database.native_map_item_catalog().contains(slot.item_id))) && slot.count==1) || (config.fruit_village_quests_enabled && RecoveredFruitQuests::material(slot.item_id)) || qualified_supply_policy(slot.item_id,1).has_value())
                                : slot.item_id==0);
            };
            const auto bag_slot_projection=[&](std::uint8_t index,const StoredInventorySlot& slot) {
                if(!bag_slot_eligible(slot)) throw DatabaseError("Unqualified owned bag projection");
                RecoveredInventoryProjection::Metadata metadata{};
                metadata[0]=static_cast<std::uint8_t>(slot.item_id);
                metadata[1]=static_cast<std::uint8_t>(slot.item_id>>8);
                const auto logical=RecoveredInventoryProjection::encode({index,slot.count,metadata});
                if(!logical) throw DatabaseError("Owned bag projection rejected");
                return *logical;
            };
            auto owner_bag_projector=(config.owned_armor_transfers_enabled||config.owned_beast_panel_enabled)?database.make_bag_projection(bag_slot_projection,config.owned_beast_panel_enabled):nullptr;
            auto beast_bag_repository=config.owned_beast_panel_enabled?database.make_beast_bag_repository(*owner_bag_projector):nullptr;
            auto beast_equipment=beast_bag_repository?std::make_unique<OwnedBeastEquipmentService>(*beast_bag_repository,*owner_bag_projector,database.beast_snapshots(),lua):nullptr;
            auto beast_discard=beast_bag_repository?std::make_unique<OwnedBeastDiscardService>(*beast_bag_repository,lua,[] {
                std::random_device entropy;constexpr char digits[]="0123456789abcdef";std::string receipt;receipt.reserve(64);
                for(unsigned n=0;n<8;++n){auto value=entropy();for(unsigned i=0;i<8;++i)receipt.push_back(digits[(value>>(i*4))&15]);}
                return receipt;
            }):nullptr;
            RecoveredTradeService::OwnedProjection owner_bag_projection;
            SqliteTradeRepository::PrepareProof trade_bag_proof;
            SqliteBankItemsRepository::PrepareProof bank_bag_proof;
            if(owner_bag_projector) {
                auto* projector=owner_bag_projector.get();
                owner_bag_projection=[projector](std::uint64_t account,std::uint64_t character,std::uint8_t slot,
                    const StoredInventorySlot& before,const StoredInventorySlot& after) {
                    return before==after?projector->project(account,character,slot,before):projector->project_planned(account,character,slot,before,after);
                };
                const OwnedBagMutationProof proof{projector};
                trade_bag_proof=[proof](const auto& before,const auto& after){return proof.trade(before,after);};
                bank_bag_proof=[proof](const auto& before,const auto& after){return proof.bank(before,after);};
            }
            const auto bag_move_projection=[&](const RecoveredInventoryMoveRequest::Request& request,
                                               const InventoryMoveCommit& next) {
                auto logical=bag_slot_projection(request.source_slot,next.source);
                const auto destination=bag_slot_projection(request.destination_slot,next.destination);
                logical.insert(logical.end(),destination.begin(),destination.end());
                return RecoveredWorldFrame::encode(logical);
            };
            InventoryMoveService inventory_moves(supply_repository,bag_slot_eligible,bag_move_projection);
            InventoryDiscardService inventory_discards(supply_repository,bag_slot_eligible);
            std::set<std::uint64_t> owned_bag_projected;
            std::set<std::uint64_t> owned_beasts_projected;
            OwnedBeastExplorationService beast_exploration;
            std::set<std::uint64_t> diagnostic_vitals_sent;
            std::set<std::uint64_t> diagnostic_quest_dialogue_sent;
            RecoveredKnowledgeConversation knowledge_conversations;
            struct ClockPeer { std::weak_ptr<Session> session; std::chrono::steady_clock::time_point last_sync; };
            std::map<std::uint64_t,ClockPeer> world_clock_sessions;
            struct IssuedDailyList {std::uint64_t account,character;std::uint16_t area,scene;OwnedDailyQuestList list;};
            std::map<std::uint64_t,IssuedDailyList> issued_daily_lists;
            const auto send_world_clock=[&](Session& session) {
                const auto seconds=std::chrono::duration_cast<std::chrono::seconds>(
                    std::chrono::system_clock::now().time_since_epoch()).count();
                const auto logical=RecoveredWorldClock::logical_from_unix_seconds(seconds);
                session.send_world_records(std::vector<std::uint8_t>(logical.begin(),logical.end()));
                spdlog::debug("WORLD_CLOCK_SENT session_id={} unix_seconds={} phase={}:{}:{} CUSTOM-0042",
                    session.id(),seconds,logical[1],logical[2],logical[3]);
            };
            std::set<std::uint64_t> diagnostic_town_guides_sent;
            std::map<std::uint64_t,unsigned> diagnostic_remote_ticks;
            std::map<std::uint64_t,RecoveredWorldEntry::Body> diagnostic_remote_appearance;
            // CUSTOM-0027: isolated same-scene real-session routing, default off.
            RecoveredVisibility player_visibility;
            std::map<std::uint64_t,RecoveredVisibility::Presence> pending_visibility;
            std::set<std::uint64_t> pending_visibility_refresh;
            std::map<std::uint64_t,std::weak_ptr<Session>> visibility_sessions;
            std::map<std::uint64_t,std::weak_ptr<Session>> native_chat_sessions;
            // CUSTOM-0054: last presentation sent per receiver, not a name-based grant.
            std::map<std::uint64_t,std::map<std::uint64_t,std::vector<std::uint8_t>>> streamer_sent;
            const bool player_presence_enabled=config.diagnostic_player_visibility ||
                config.diagnostic_town_player_visibility;
            const auto deliver_visibility=[&](std::vector<RecoveredVisibility::Delivery> deliveries) {
                for(auto& delivery:deliveries) {
                    const auto found=visibility_sessions.find(delivery.recipient);
                    if(found!=visibility_sessions.end())
                        if(auto peer=found->second.lock()) {
                            std::optional<RecoveredCharacterPose::LogicalRecord> pose_after_spawn;
                            if(const auto spawn=RecoveredRemoteActor::parse_logical(delivery.logical)) {
                                pose_after_spawn=player_visibility.pose_after_spawn(*spawn);
                                const auto source=player_visibility.snapshot_character(spawn->identity());
                                if(source)if(const auto saved=database.role_text().load(source->account,source->character)) {
                                    const auto projected=RecoveredPeerRoleText::per_recipient(*spawn,saved,
                                        peer->recovered_client_language()==1?936:950);
                                    const auto logical=RecoveredRemoteActor::encode_logical(projected.spawn);
                                    delivery.logical.assign(logical.begin(),logical.end());
                                }
                            }
                            peer->send_world_records(std::move(delivery.logical));
                            if(pose_after_spawn) {
                                peer->send_world_records(std::vector<std::uint8_t>(pose_after_spawn->begin(),pose_after_spawn->end()));
                                spdlog::debug("NATIVE_POSE_REPLAY actor_id={} recipient_session={} mode={} direction={}",
                                    (*pose_after_spawn)[1]+256u*(*pose_after_spawn)[2],delivery.recipient,
                                    (*pose_after_spawn)[4]>>3,(*pose_after_spawn)[4]&7u);
                            }
                        }
                }
            };
            const auto visibility_at=[&](const RecoveredVisibility::Presence& source,
                                         const RecoveredPosition& position) {
                if(!((position.area==2 && (position.scene==4 || position.scene==15 ||
                      (config.diagnostic_town_island_routes && position.scene==0) ||
                      (config.diagnostic_town_all_door_routes && recovered_movement && recovered_movement->registered_door_pair(4,position.scene)))) ||
                     (position.area==4 && !config.character_birthplace_navigation.empty() &&
                      (position.scene==3 || (config.diagnostic_kunlun_parent_routes && position.scene==0) ||
                       (config.diagnostic_kunlun_door_routes && recovered_movement && recovered_movement->registered_door_pair(4,3,position.scene)))) ||
                     (config.fruit_village_quests_enabled && position.area==13 && position.scene==12)))
                    throw std::runtime_error("Town visibility location projection rejected");
                auto bytes=RecoveredRemoteActor::encode_logical(source.spawn);
                const unsigned kind=position.area==2 ? (position.scene==4?0u:(position.scene==0?1u:2u)) :
                    (position.area==4 ? (position.scene==0?1u:(position.scene==3?0u:2u)) : 0u);
                bytes[13]=static_cast<std::uint8_t>((bytes[13]&~3u)|kind);
                const auto normalized=RecoveredRemoteActor::parse_logical(bytes);
                const auto projected=normalized ? RecoveredRemoteActor::with_position(
                    *normalized,position.x,position.y) : std::nullopt;
                if(!projected) throw std::runtime_error("Town visibility position projection rejected");
                auto next=source;
                if(source.location!=RecoveredVisibility::Scene{position.area,position.scene} ||
                   source.spawn.x()!=position.x || source.spawn.y()!=position.y)next.pose.reset();
                next.location={position.area,position.scene};
                next.spawn=*projected;
                return next;
            };
            const auto publish_visibility_movement=[&](Session& session,
                    const RecoveredMovementService::CommittedMove& committed) {
                if(!player_visibility.contains(session.id())) {
                    if(!config.diagnostic_town_player_visibility || !pending_visibility.contains(session.id()))
                        throw std::runtime_error("Visibility movement without owned presence");
                    pending_visibility.insert_or_assign(session.id(),visibility_at(
                        pending_visibility.at(session.id()),committed.after));
                    return;
                }
                std::vector<RecoveredRemoteActorMove::Record> updates;
                updates.reserve(committed.path.size());
                for(const auto& point:committed.path) {
                    auto bytes=DiagnosticRemoteActor::logical(1,config.diagnostic_remote_actor_language);
                    const auto packed=std::uint32_t{point.x}|(std::uint32_t{point.y}<<11);
                    for(unsigned i=0;i<4;++i) bytes[9+i]=static_cast<std::uint8_t>(packed>>(8*i));
                    const auto parsed=RecoveredRemoteActorMove::parse_logical(bytes).value();
                    updates.push_back(RecoveredRemoteActorMove::with_identity(parsed,session.character_id).value());
                }
                deliver_visibility(player_visibility.move_batch(session.id(),session.account_id,
                    session.character_id,{committed.after.area,committed.after.scene},updates));
            };
            std::set<std::uint64_t> diagnostic_town_map_replied;
            std::set<std::uint64_t> diagnostic_town_scene_pending;
            // CUSTOM-0036: distinguish scene-0 return from other pending town doors.
            std::set<std::uint64_t> diagnostic_island_return_pending;
            // A native61 full reload clears both 256-entry actor pools
            // (46C2CA/46C2D5 -> 4CA730). Restore on the qualified arrival,
            // including a rapid roundtrip with no periodic tick in between.
            // This projects supplied records only; catalogs never create spawns.
            const auto world_display_batches=[&](Session& session) {
                std::vector<std::vector<std::uint8_t>> batches;
                if(!recovered_movement || !session.recovered_world_ready() ||
                   (session.state()!=SessionState::CharacterSelected && session.state()!=SessionState::InWorld) ||
                   diagnostic_town_scene_pending.contains(session.id()) ||
                   diagnostic_island_return_pending.contains(session.id())) return batches;
                const auto location=recovered_movement->current_location(session.id(),session.account_id,session.character_id);
                if(!location) return batches;
                const auto scene=std::pair{static_cast<std::uint16_t>(location->area),static_cast<std::uint16_t>(location->scene)};
                const auto previous=world_display_scene.find(session.id());
                if(previous!=world_display_scene.end() && previous->second==scene) return batches;
                batches=recovered_world_display_batches(database.world_displays(),
                    database.native_npc_display_catalog(),database.native_enemy_display_catalog(),scene.first,scene.second,native_records_lab);
                // Qualify the complete scene before publishing its cache marker.
                world_display_scene.insert_or_assign(session.id(),scene);
                spdlog::info("NATIVE_WORLD_DISPLAY_RESTORED session_id={} area={} scene={} batches={}",session.id(),scene.first,scene.second,batches.size());
                return batches;
            };
            // CUSTOM-0025: ACK the committed move before a later tick emits61.
            struct PendingTownGuide {
                std::optional<StoredTownGuideProgress> expected;
                TownGuidePlan plan;
                std::uint32_t npc;
                std::optional<StoredInventorySlot> reward_slot;
            };
            std::map<std::uint64_t,PendingTownGuide> pending_town_guides;
            DiagnosticQuestConversation diagnostic_quest_conversations;
            std::map<std::uint64_t,unsigned> diagnostic_rounds_granted;
            // A terminal 1C receipt is scoped to this session's committed winner.
            std::map<std::uint64_t,bool> diagnostic_town_battle_won;
            if(config.recovered_movement) {
                if(config.diagnostic_town) {
                    recovered_movement=std::make_unique<RecoveredMovementService>(database.recovered_characters(),
                        RecoveredMovementService::TownDiagnostic{config.recovered_navigation,
                            {config.diagnostic_town_center_x,config.diagnostic_town_center_y},
                            config.diagnostic_town_x,config.diagnostic_town_y,config.diagnostic_town_source_consensus,
                            config.diagnostic_town_indoor_navigation,config.diagnostic_town_island_navigation,
                            config.character_birthplace_navigation,config.character_birthplace_x,config.character_birthplace_y,config.fruit_village_quests_enabled?config.fruit_navigation:std::filesystem::path{},config.diagnostic_town_indoor_scenes,config.diagnostic_kunlun_indoor_scenes,
                            config.diagnostic_kunlun_parent_routes?config.diagnostic_kunlun_parent_navigation:std::filesystem::path{}});
                    spdlog::warn("Town diagnostic: {}, supplied test placement; live acceptance pending",
                        config.diagnostic_town_source_consensus?"CUSTOM-0019 source agreement gate":"fixed navigation window");
                    if(!config.character_birthplace_navigation.empty())
                        spdlog::info("NEW_CHARACTER_BIRTHPLACE area=4 scene=3 kind=0 x={} y={} map=Kunlun existing_saved_positions=preserved coordinate_authority=configured_not_original_verified",
                            config.character_birthplace_x,config.character_birthplace_y);
                } else recovered_movement=std::make_unique<RecoveredMovementService>(database.recovered_characters(),config.recovered_navigation);
            }
            auto whole_bag_moves=config.owned_whole_bag_moves_enabled?std::make_shared<WholeBagMoveHost>():nullptr;
            if(whole_bag_moves)whole_bag_moves->actual_session_capacity=config.max_sessions;
            Session::RecoveredCharacterHandlers character_handlers;
            std::unique_ptr<RecoveredWorldService> recovered_world;
            if(config.recovered_character_creation) {
                character_handlers.list=[&](std::uint64_t account) {
                    return recovered_characters.list(account,config.recovered_dual_connection?1:0);
                };
                character_handlers.create=[&](std::uint64_t account,const RecoveredCharacterCreate& request) {
                    return recovered_characters.create(account,request);
                };
                character_handlers.select_created=[&](std::uint64_t account,std::uint64_t created,std::uint8_t token) {
                    return recovered_characters.select_created(account,created,token);
                };
                character_handlers.select_existing=[&](std::uint64_t account,std::uint8_t token) {
                    return recovered_characters.select_existing(account,token);
                };
                character_handlers.created_slot=[&](std::uint64_t account,std::uint64_t created) {
                    return recovered_characters.created_slot(account,created);
                };
                character_handlers.delete_character=[&](Session& session,const RecoveredCharacterDelete& request) {
                    // Current native19 supplies credentials, slot and name. Reuse
                    // exact login semantics without allowing account registration.
                    RecoveredC2S0002::Payload credentials{};
                    credentials[0]=0;credentials[167]=0xc8;
                    std::copy(request.account.begin(),request.account.end(),credentials.begin()+1);
                    std::copy(request.password.begin(),request.password.end(),credentials.begin()+25);
                    const auto checked=RecoveredC2S0002::parse(RecoveredC2S0002::encode(credentials),0);
                    if(!checked || recovered_accounts.authenticate(*checked)!=session.account_id) return false;
                    const auto name_end=std::find(request.name.begin(),request.name.end(),0);
                    const auto name=std::span<const std::uint8_t>(request.name.begin(),name_end);
                    for(const auto& character:database.recovered_characters().list_for_account(session.account_id)) {
                        if(character.slot!=request.token) continue;
                        if(world.character_online(character.id) ||
                           (recovered_movement && recovered_movement->character_active(session.account_id,character.id))) return false;
                        const auto stored_end=std::find(character.profile.begin(),character.profile.begin()+15,0);
                        if(!std::equal(name.begin(),name.end(),character.profile.begin(),stored_end)) return false;
                        if(migrations.back().version==52||migrations.back().version==53) {
                            // Candidate52-only cross-route invariant: deleting a live
                            // effective owner must not orphan succession history.
                            // Keep existing erase graph/auth and schema51 unchanged.
                            try {
                                const auto membership=database.guilds().load(session.account_id,character.id);
                                if(membership && guild_membership_repository->player_created(membership->guild_id)) {
                                    const bool effective_owner=migrations.back().version==53?([&]{const auto v=database.guild53(flags53).owner().effective_snapshot(membership->guild_id);return v.owner.account_id==session.account_id&&v.owner.character_id==character.id;})():([&]{const auto v=database.guild_succession52(config.owned_guild_succession_enabled).effective_snapshot(membership->guild_id);return v.owner.account_id==session.account_id&&v.owner.character_id==character.id;})();
                                    if(effective_owner)return false;
                                }
                            }catch(const DatabaseError&){return false;}
                        }
                        return supply_repository.erase_owned(session.account_id,character.id,name);
                    }
                    return false;
                };
                spdlog::info("Recovered character persistence enabled; populated list remains an unverified candidate");
            }
            Session::PacketHandler on_packet=[&](std::shared_ptr<Session> session,Packet packet) {
                    if(fixture_mode && (packet.opcode==static_cast<std::uint16_t>(Opcode::C2S_ChatMessage) ||
                       packet.opcode==static_cast<std::uint16_t>(Opcode::C2S_NpcTalk)) &&
                       !fixture_text) {
                        try { fixture_text.emplace(config.chinese_dictionary_root); }
                        catch(const std::exception& e) {
                            spdlog::warn("Chinese text dictionary unavailable: {}",e.what());
                            PacketWriter error;error.write_string("Text conversion unavailable");
                            session->send(Packet{static_cast<std::uint16_t>(Opcode::S2C_Error),error.bytes()});
                            return;
                        }
                    }
                    HandlerContext ctx{*session,world,database,lua,config.mock_login,fixture_battles.get(),
                        fixture_text?&*fixture_text:nullptr}; dispatcher.dispatch(ctx,packet);
                };
            NativeParty native_parties;
            std::unique_ptr<OwnedPartyDirectory> owned_party_directory; // CUSTOM-0097, independent of membership.
            std::function<void(Session&)> owned_party_directory_retire; // Actual ready/disconnect watcher path, game owner only.
            if(config.owned_party_directory_enabled)owned_party_directory=std::make_unique<OwnedPartyDirectory>();
            std::unique_ptr<OwnedClientOptions> owned_client_options; // CUSTOM-0100, never gameplay permissions.
            if(config.owned_client_options_enabled)owned_client_options=std::make_unique<OwnedClientOptions>();
            std::map<std::uint64_t,std::weak_ptr<Session>> party_sessions;
            std::map<std::uint64_t,std::weak_ptr<Session>> trade_sessions;
            std::set<std::uint64_t> trade_wallet_sent;
            std::optional<ChineseText> trade_text;
            const auto trade_peer=[&](std::uint64_t id)->std::optional<RecoveredTradeService::Peer> {
                const auto at=trade_sessions.find(id);if(at==trade_sessions.end())return {};
                auto peer=at->second.lock();if(!peer || !peer->account_id || !peer->character_id || peer->character_id>0x3fff || !recovered_movement)return {};
                const auto here=recovered_movement->current_location(id,peer->account_id,peer->character_id);if(!here)return {};
                return RecoveredTradeService::Peer{id,peer->account_id,peer->character_id,here->area,here->scene,
                    peer->recovered_world_ready() && owned_bag_projected.contains(id) &&
                    (peer->state()==SessionState::CharacterSelected || peer->state()==SessionState::InWorld) &&
                    !diagnostic_town_scene_pending.contains(id) && !diagnostic_island_return_pending.contains(id)};
            };
            RecoveredTradeService native_trades(database.trades(),trade_peer,
                [&](std::uint16_t character)->std::optional<RecoveredTradeService::Peer> {
                    std::optional<RecoveredTradeService::Peer> result;
                    for(const auto& [id,weak]:trade_sessions)if(auto peer=trade_peer(id);peer && peer->character==character) {
                        if(result)return {};result=peer;
                    }
                    return result;
                },[&](const RecoveredTradeService::Peer& recipient,const RecoveredTradeService::Peer& actor) {
                    const auto roles=database.recovered_characters().list_for_account(actor.account);
                    const auto role=std::find_if(roles.begin(),roles.end(),[&](const auto& r){return r.id==actor.character;});
                    if(role==roles.end() || (role->name_codepage!=950 && role->name_codepage!=936))throw DatabaseError("Trade name ownership/encoding invalid");
                    const auto end=std::find(role->profile.begin(),role->profile.begin()+15,0);
                    if(end==role->profile.begin() || end==role->profile.begin()+15)throw DatabaseError("Trade name invalid");
                    const auto name=LegacyChineseCodec::decode(std::string_view(reinterpret_cast<const char*>(role->profile.data()),end-role->profile.begin()),role->name_codepage==936);
                    const auto live=trade_sessions.at(recipient.session).lock();if(!live)throw DatabaseError("Trade name recipient missing");
                    const bool cn=live->recovered_client_language()==1;if(!trade_text)trade_text.emplace(config.chinese_dictionary_root);
                    const auto localized=trade_text->convert(name,cn?ChineseLanguage::Simplified:ChineseLanguage::Traditional);
                    const auto encoded=LegacyChineseCodec::encode_display(localized,cn);
                    if(encoded.replacements || encoded.truncated || encoded.bytes.empty() || encoded.bytes.size()>14)throw DatabaseError("Trade name unrepresentable");
                    RecoveredTrade::Name result{};std::copy(encoded.bytes.begin(),encoded.bytes.end(),result.begin());return result;
                },[&](const StoredInventorySlot& slot) {
                    // Qualified scalar consumables only: no quest/map, bound,
                    // equipment, enhanced or unknown instance grant/inference.
                    return slot.source_sha256==supply_source && slot.count && slot.count<=127 && qualified_supply_policy(slot.item_id,1).has_value();
                },bag_slot_projection,[] {
                    // Server-only collision-resistant receipt, never a client
                    // authority token. DB unique+snapshot checks guard replay.
                    std::random_device entropy;constexpr char digits[]="0123456789abcdef";std::string result;result.reserve(64);
                    for(unsigned n=0;n<8;++n){auto value=entropy();for(unsigned i=0;i<8;++i)result.push_back(digits[(value>>(i*4))&15]);}
                    return result;
                },owner_bag_projection,trade_bag_proof);
            // CUSTOM-0069: new full-instance custody, default off. The accepted
            // scalar service remains unchanged and selected when this is absent.
            std::unique_ptr<SqliteOwnedInstanceTradeRepository> beast_instance_trade_repository;
            if(config.owned_instance_trade_enabled && config.owned_beast_panel_enabled)
                beast_instance_trade_repository=database.make_beast_instance_trade_repository();
            const auto owned_trade_peer=[&](std::uint64_t id)->std::optional<RecoveredTradeService::Peer>{
                auto peer=trade_peer(id);
                if(peer && beast_instance_trade_repository && !owned_beasts_projected.contains(id))peer->ready=false;
                return peer;
            };
            std::unique_ptr<OwnedInstanceTradeService> owned_instance_trades;
            if(config.owned_instance_trade_enabled) {
                owned_instance_trades=std::make_unique<OwnedInstanceTradeService>(
                    beast_instance_trade_repository?*beast_instance_trade_repository:database.instance_trades(),owned_trade_peer,
                    [&](std::uint16_t character)->std::optional<RecoveredTradeService::Peer> {
                        std::optional<RecoveredTradeService::Peer> result;
                        for(const auto& [id,weak]:trade_sessions)if(auto peer=owned_trade_peer(id);peer && peer->character==character) {
                            if(result)return {};result=peer;
                        }
                        return result;
                    },[&](const RecoveredTradeService::Peer& recipient,const RecoveredTradeService::Peer& actor) {
                    const auto roles=database.recovered_characters().list_for_account(actor.account);
                    const auto role=std::find_if(roles.begin(),roles.end(),[&](const auto& r){return r.id==actor.character;});
                    if(role==roles.end() || (role->name_codepage!=950 && role->name_codepage!=936))throw DatabaseError("Trade name ownership/encoding invalid");
                    const auto end=std::find(role->profile.begin(),role->profile.begin()+15,0);
                    if(end==role->profile.begin() || end==role->profile.begin()+15)throw DatabaseError("Trade name invalid");
                    const auto name=LegacyChineseCodec::decode(std::string_view(reinterpret_cast<const char*>(role->profile.data()),end-role->profile.begin()),role->name_codepage==936);
                    const auto live=trade_sessions.at(recipient.session).lock();if(!live)throw DatabaseError("Trade name recipient missing");
                    const bool cn=live->recovered_client_language()==1;if(!trade_text)trade_text.emplace(config.chinese_dictionary_root);
                    const auto localized=trade_text->convert(name,cn?ChineseLanguage::Simplified:ChineseLanguage::Traditional);
                    const auto encoded=LegacyChineseCodec::encode_display(localized,cn);
                    if(encoded.replacements || encoded.truncated || encoded.bytes.empty() || encoded.bytes.size()>14)throw DatabaseError("Trade name unrepresentable");
                    RecoveredTrade::Name result{};std::copy(encoded.bytes.begin(),encoded.bytes.end(),result.begin());return result;
                },[&](const StoredInventorySlot& slot) {
                        return slot.source_sha256==supply_source && slot.count && slot.count<=127 &&
                            qualified_supply_policy(slot.item_id,1).has_value();
                    },bag_slot_projection,[] {
                        std::random_device entropy;constexpr char digits[]="0123456789abcdef";std::string result;result.reserve(64);
                        for(unsigned n=0;n<8;++n){auto value=entropy();for(unsigned i=0;i<8;++i)result.push_back(digits[(value>>(i*4))&15]);}
                        return result;
                    },[&](const StoredBeastSnapshot& value){
                        const auto fields=value.inventory_fields();
                        return fields && lua.beast_transfer_allowed(value.inventory_slot,1,
                            fields->native_exploring_label(),value.panel.control7_alternate(),value.panel.control8_alternate());
                    });
                spdlog::info("OWNED_INSTANCE_TRADE_ENABLED CUSTOM-0069 full_instance no_grants no_formula");
            }
            const auto trade_active=[&](std::uint64_t id){return owned_instance_trades?owned_instance_trades->active(id):native_trades.active(id);};
            const auto deliver_trades=[&](RecoveredTradeService::Deliveries batches) {
                for(auto& [id,logical]:batches)if(const auto at=trade_sessions.find(id);at!=trade_sessions.end())
                    if(auto peer=at->second.lock()){
                        // CUSTOM0085 trade conversation retires only this
                        // session's menu lease; no durable activity cancellation.
                        if(beast_instance_trade_repository)beast_exploration.disconnect(id);
                        peer->send_world_records(std::move(logical));
                    }
            };
            std::optional<ChineseText> party_text;
            RecoveredBankService native_banks(database.banks(),
                [&](std::uint64_t id)->std::optional<RecoveredBankService::Peer> {
                    const auto peer=trade_peer(id);if(!peer || !recovered_movement)return {};
                    const auto where=recovered_movement->current_location(id,peer->account,peer->character);if(!where)return {};
                    return RecoveredBankService::Peer{id,peer->account,peer->character,
                        static_cast<std::uint16_t>(where->area),static_cast<std::uint16_t>(where->scene),
                        static_cast<std::uint16_t>(where->x),static_cast<std::uint16_t>(where->y),peer->ready && !trade_active(id)};
                },[&](const RecoveredBankService::Peer& peer,std::uint16_t target) {
                    // CUSTOM-0064: bank role and native placement are independently
                    // required. Names, catalog entries or guessed coordinates never
                    // authorize an NPC. Test placements stay in the guarded lab.
                    const auto point=database.bank_access().lookup(peer.area,peer.scene,target,native_records_lab);
                    if(!point)return false;
                    const auto npc=RecoveredNpcRecord::parse(point->logical);if(!npc)return false;
                    const auto dx=static_cast<int>(peer.x)-static_cast<int>(npc->x());
                    const auto dy=static_cast<int>(peer.y)-static_cast<int>(npc->y());
                    return dx>=-3 && dx<=3 && dy>=-3 && dy<=3;
                },[] {
                    std::random_device entropy;constexpr char digits[]="0123456789abcdef";std::string result;result.reserve(64);
                    for(unsigned n=0;n<8;++n){auto value=entropy();for(unsigned i=0;i<8;++i)result.push_back(digits[(value>>(i*4))&15]);}
                    return result;
                });
            RecoveredBankItemsService native_bank_items(database.bank_items(),
                [&](std::uint64_t id)->std::optional<RecoveredBankService::Peer> {
                    const auto peer=trade_peer(id);if(!peer || !recovered_movement)return {};
                    const auto where=recovered_movement->current_location(id,peer->account,peer->character);if(!where)return {};
                    return RecoveredBankService::Peer{id,peer->account,peer->character,
                        static_cast<std::uint16_t>(where->area),static_cast<std::uint16_t>(where->scene),
                        static_cast<std::uint16_t>(where->x),static_cast<std::uint16_t>(where->y),peer->ready && !trade_active(id)};
                },[&](std::uint64_t id,std::uint16_t target,auto now){return native_banks.permits_items(id,target,now);},
                [&](std::uint64_t id,auto now){native_banks.renew_items(id,now);},
                [&](const StoredInventorySlot& slot){return slot.count && slot.count<=127 &&
                    slot.source_sha256==supply_source && qualified_supply_policy(slot.item_id,1).has_value();},
                bag_slot_projection,[] {
                    std::random_device entropy;constexpr char digits[]="0123456789abcdef";std::string result;result.reserve(64);
                    for(unsigned n=0;n<8;++n){auto value=entropy();for(unsigned i=0;i<8;++i)result.push_back(digits[(value>>(i*4))&15]);}
                    return result;
                },owner_bag_projection,bank_bag_proof);
            // CUSTOM-0067: independent opt-in unified armor/MED bank context.
            // Existing scalar service remains selected when this flag is false.
            std::unique_ptr<OwnedArmorBankService> owned_armor_bank;
            if(config.owned_armor_bank_enabled) {
                owned_armor_bank=std::make_unique<OwnedArmorBankService>(database.armor_bank(),database.bank_items(),
                    [&](std::uint64_t id)->std::optional<RecoveredBankService::Peer> {
                        const auto peer=trade_peer(id);if(!peer || !recovered_movement)return {};
                        const auto where=recovered_movement->current_location(id,peer->account,peer->character);if(!where)return {};
                        return RecoveredBankService::Peer{id,peer->account,peer->character,
                            static_cast<std::uint16_t>(where->area),static_cast<std::uint16_t>(where->scene),
                            static_cast<std::uint16_t>(where->x),static_cast<std::uint16_t>(where->y),peer->ready && !trade_active(id)};
                    },[&](std::uint64_t id,std::uint16_t target,auto now){return native_banks.permits_items(id,target,now);},
                    [&](std::uint64_t id,auto now){native_banks.renew_items(id,now);},
                    [&](const StoredInventorySlot& slot){return slot.count && slot.count<=127 &&
                        slot.source_sha256==supply_source && qualified_supply_policy(slot.item_id,1).has_value();},
                    bag_slot_projection,[] {
                        std::random_device entropy;constexpr char digits[]="0123456789abcdef";std::string result;result.reserve(64);
                        for(unsigned n=0;n<8;++n){auto value=entropy();for(unsigned i=0;i<8;++i)result.push_back(digits[(value>>(i*4))&15]);}
                        return result;
                    },qualified_weapon);
                spdlog::info("OWNED_ARMOR_BANK_ENABLED CUSTOM-0067 full_instance no_grants no_formula");
            }
            // CUSTOM-0068: independent full weapon/gem route. Disabled by default;
            // accepted armor/MED service selection remains intact when disabled.
            std::unique_ptr<OwnedForeignBankService> owned_foreign_bank;
            if(config.owned_foreign_bank_enabled) {
                owned_foreign_bank=std::make_unique<OwnedForeignBankService>(database.foreign_bank(),database.armor_bank(),database.bank_items(),
                    [&](std::uint64_t id)->std::optional<RecoveredBankService::Peer> {
                        const auto peer=trade_peer(id);if(!peer || !recovered_movement)return {};
                        const auto where=recovered_movement->current_location(id,peer->account,peer->character);if(!where)return {};
                        return RecoveredBankService::Peer{id,peer->account,peer->character,
                            static_cast<std::uint16_t>(where->area),static_cast<std::uint16_t>(where->scene),
                            static_cast<std::uint16_t>(where->x),static_cast<std::uint16_t>(where->y),peer->ready && !trade_active(id)};
                    },[&](std::uint64_t id,std::uint16_t target,auto now){return native_banks.permits_items(id,target,now);},
                    [&](std::uint64_t id,auto now){native_banks.renew_items(id,now);},
                    [&](const StoredInventorySlot& slot){return slot.count && slot.count<=127 &&
                        slot.source_sha256==supply_source && qualified_supply_policy(slot.item_id,1).has_value();},
                    bag_slot_projection,[] {
                        std::random_device entropy;constexpr char digits[]="0123456789abcdef";std::string result;result.reserve(64);
                        for(unsigned n=0;n<8;++n){auto value=entropy();for(unsigned i=0;i<8;++i)result.push_back(digits[(value>>(i*4))&15]);}
                        return result;
                    },qualified_weapon);
                spdlog::info("OWNED_FOREIGN_BANK_ENABLED CUSTOM-0068 full_instance no_grants no_formula");
            }
            // CUSTOM-0070: independent opt-in complete cross-category vault custody.
            std::unique_ptr<SqliteBeastBankRepository> beast_bank_repository;
            if(config.owned_mixed_bank_enabled && config.owned_beast_panel_enabled)beast_bank_repository=database.make_beast_bank_repository();
            std::unique_ptr<OwnedMixedBankService> owned_mixed_bank;
            if(config.owned_mixed_bank_enabled) {
                owned_mixed_bank=std::make_unique<OwnedMixedBankService>(database.mixed_bank(),database.foreign_bank(),database.armor_bank(),database.bank_items(),
                    [&](std::uint64_t id)->std::optional<RecoveredBankService::Peer> {
                        const auto peer=trade_peer(id);if(!peer || !recovered_movement)return {};
                        const auto where=recovered_movement->current_location(id,peer->account,peer->character);if(!where)return {};
                        return RecoveredBankService::Peer{id,peer->account,peer->character,
                            static_cast<std::uint16_t>(where->area),static_cast<std::uint16_t>(where->scene),
                            static_cast<std::uint16_t>(where->x),static_cast<std::uint16_t>(where->y),peer->ready && !trade_active(id) && (!beast_bank_repository || owned_beasts_projected.contains(id))};
                    },[&](std::uint64_t id,std::uint16_t target,auto now){return native_banks.permits_items(id,target,now);},
                    [&](std::uint64_t id,auto now){native_banks.renew_items(id,now);},
                    [&](const StoredInventorySlot& slot){return slot.count && slot.count<=127 &&
                        slot.source_sha256==supply_source && qualified_supply_policy(slot.item_id,1).has_value();},
                    bag_slot_projection,[] {
                        std::random_device entropy;constexpr char digits[]="0123456789abcdef";std::string result;result.reserve(64);
                        for(unsigned n=0;n<8;++n){auto value=entropy();for(unsigned i=0;i<8;++i)result.push_back(digits[(value>>(i*4))&15]);}
                        return result;
                    },qualified_weapon,beast_bank_repository.get(),[&](const StoredVaultBeast& value,const RecoveredBankItems::Request& request){
                        const auto fields=RecoveredBeastInventoryFields::decode(value.inventory_metadata);
                        return fields && lua.beast_bank_allowed(static_cast<std::uint8_t>(request.kind),request.page,request.quantity,
                            fields->native_exploring_label(),value.panel.control7_alternate(),value.panel.control8_alternate());
                    });
                spdlog::info("OWNED_MIXED_BANK_ENABLED CUSTOM-0070 full_instance no_grants no_formula");
            }
            const auto bank_items_disconnect=[&](std::uint64_t id) {
                native_bank_items.disconnect(id);if(owned_armor_bank)owned_armor_bank->disconnect(id);if(owned_foreign_bank)owned_foreign_bank->disconnect(id);if(owned_mixed_bank)owned_mixed_bank->disconnect(id);
            };
            const auto bank_items_open=[&](std::uint64_t id,std::uint16_t target,auto now) {
                if(!owned_armor_bank&&!owned_foreign_bank&&!owned_mixed_bank)return native_bank_items.open(id,target,now);
                // Only the accepted money bank lease may allocate original empty
                // scalar capacity. Metadata/storage reads never grant capacity.
                if(!native_banks.permits_items(id,target,now))throw DatabaseError("Armor bank lease missing");
                const auto peer=trade_peer(id);if(!peer || !peer->ready)throw DatabaseError("Armor bank owner missing");
                database.bank_items().provision_empty(peer->account,peer->character);
                if(owned_mixed_bank){if(beast_bank_repository)beast_exploration.disconnect(id);return owned_mixed_bank->open(id,target,now);}
                if(owned_foreign_bank)return owned_foreign_bank->open(id,target,now);
                return owned_armor_bank->open(id,target,now);
            };
            const auto bank_items_handle=[&](std::uint64_t id,std::span<const RecoveredBankItems::Request> requests,auto now) {
                if(owned_mixed_bank){if(beast_bank_repository)beast_exploration.disconnect(id);auto result=owned_mixed_bank->handle(id,requests,now);return RecoveredBankItemsService::Result{std::move(result.batches),result.committed,result.rejected};}
                if(owned_foreign_bank){auto result=owned_foreign_bank->handle(id,requests,now);return RecoveredBankItemsService::Result{std::move(result.batches),result.committed,result.rejected};}
                if(!owned_armor_bank)return native_bank_items.handle(id,requests,now);
                auto result=owned_armor_bank->handle(id,requests,now);
                return RecoveredBankItemsService::Result{std::move(result.batches),result.committed,result.rejected};
            };
            // CUSTOM-0071: independent typed27 custody. Scalar0061 remains
            // unchanged. Bank leases are invalidated only in legal preparation,
            // without storage writes, so no stale bag snapshot can be reused.
            std::unique_ptr<OwnedInstanceDiscardService> owned_instance_discards;
            if(config.owned_instance_discard_enabled) {
                if(!owner_bag_projector || !database.native_armor_catalog().populated() ||
                   !database.native_weapon_catalog().populated())
                    throw DatabaseError("Owned instance discard requires complete native definitions and bag projection");
                owned_instance_discards=std::make_unique<OwnedInstanceDiscardService>(database.instance_discards(),
                    [&](std::uint64_t id)->std::optional<RecoveredBankService::Peer> {
                        const auto peer=trade_peer(id);if(!peer || !recovered_movement)return {};
                        const auto where=recovered_movement->current_location(id,peer->account,peer->character);if(!where)return {};
                        return RecoveredBankService::Peer{id,peer->account,peer->character,
                            static_cast<std::uint16_t>(where->area),static_cast<std::uint16_t>(where->scene),
                            static_cast<std::uint16_t>(where->x),static_cast<std::uint16_t>(where->y),
                            peer->ready && owned_armor_projected.contains(id) && owned_bag_projected.contains(id) && !trade_active(id)};
                    },[&](std::uint64_t id,std::uint8_t source,auto)->bool {
                        const auto peer=trade_peer(id);
                        if(source>=30 || !peer || !peer->ready || !owned_armor_projected.contains(id) ||
                           !owned_bag_projected.contains(id) || trade_active(id))return false;
                        if(config.diagnostic_town_quest_progress && source==0) {
                            const auto progress=supply_repository.load_town_guide_progress(peer->account,peer->character);
                            if(!progress || progress->stage<3)return false;
                        }
                        return true;
                    },[] {
                        std::random_device entropy;constexpr char digits[]="0123456789abcdef";std::string result;result.reserve(64);
                        for(unsigned n=0;n<8;++n){auto value=entropy();for(unsigned i=0;i<8;++i)result.push_back(digits[(value>>(i*4))&15]);}
                        return result;
                    },bag_slot_projection,[&](std::uint64_t id) {bank_items_disconnect(id);native_banks.disconnect(id);});
                spdlog::info("OWNED_INSTANCE_DISCARD_ENABLED CUSTOM-0071 full_instance no_grants no_formula no_ground_drop");
            }
            const auto party_member=[&](Session& session)->std::optional<NativeParty::Member> {
                if(!recovered_movement || !session.character_id || session.character_id>0x3fff)return {};
                const auto location=recovered_movement->current_location(session.id(),session.account_id,session.character_id);
                if(!location)return {};
                const auto owned=database.recovered_characters().list_for_account(session.account_id);
                const auto role=std::find_if(owned.begin(),owned.end(),[&](const auto& r){return r.id==session.character_id;});
                const auto snapshot=database.recovered_characters().load_role(session.account_id,session.character_id);
                const auto resources=database.recovered_characters().load_resources(session.account_id,session.character_id);
                if(role==owned.end() || !snapshot || !resources)return {};
                const auto level=RecoveredRoleLevel::parse(snapshot->logical);
                const auto end=std::find(role->profile.begin(),role->profile.begin()+15,0);
                if(!level || !level->level() || end==role->profile.begin() || end==role->profile.begin()+15 ||
                   (role->name_codepage!=950 && role->name_codepage!=936) || role->profile[29]<1 || role->profile[29]>8)return {};
                NativeParty::Member m{session.id(),session.account_id,static_cast<std::uint16_t>(session.character_id),
                    location->area,location->scene,location->x,location->y};
                m.name=LegacyChineseCodec::decode(std::string_view(reinterpret_cast<const char*>(role->profile.data()),end-role->profile.begin()),role->name_codepage==936);
                // Native68370 world body20..23 is the HUD4 also used by55.
                m.hud={static_cast<std::uint8_t>(role->profile[36]&0xe7),0,role->profile[38],role->profile[39]};
                m.profession=role->profile[29];m.level=level->level();
                m.resources={resources->hp,resources->max_hp,resources->mp,resources->max_mp};
                m.ready=session.recovered_world_ready() &&
                    (session.state()==SessionState::CharacterSelected || session.state()==SessionState::InWorld) &&
                    !diagnostic_town_scene_pending.contains(session.id()) && !diagnostic_island_return_pending.contains(session.id());
                // Native party bars consume low signed WORD operands. Wider
                // recording/test resource variants remain unqualified here.
                if(std::any_of(m.resources.begin(),m.resources.end(),[](auto n){return n>0x7fff;}))m.ready=false;
                return m;
            };
            OwnedPartyPositionQuery party_position_queries([&](std::uint64_t id)->std::optional<NativeParty::Member> {
                const auto at=party_sessions.find(id);
                if(at==party_sessions.end())return {};
                const auto peer=at->second.lock();return peer?party_member(*peer):std::optional<NativeParty::Member>{};
            });
            OwnedPartyChatService party_chat([&](std::uint64_t id)->std::optional<OwnedPartyChatService::Peer> {
                const auto at=party_sessions.find(id);if(at==party_sessions.end())return {};
                const auto peer=at->second.lock();if(!peer)return {};
                auto member=party_member(*peer);if(!member)return {};
                // Chat carries no coordinates/vitals. Its live lease can also
                // be in battle; preserve the existing party HUD readiness rule.
                member->ready=peer->recovered_world_ready() &&
                    (peer->state()==SessionState::CharacterSelected || peer->state()==SessionState::InWorld ||
                     peer->state()==SessionState::InBattle) &&
                    !diagnostic_town_scene_pending.contains(id) && !diagnostic_island_return_pending.contains(id);
                const auto owned=database.recovered_characters().list_for_account(peer->account_id);
                const auto role=std::find_if(owned.begin(),owned.end(),[&](const auto& r){return r.id==peer->character_id;});
                if(role==owned.end())return {};
                return OwnedPartyChatService::Peer{*member,peer->recovered_client_language()==1,role->streamer_privilege};
            },[&](const auto& source,const auto& recipient,const RecoveredPartyChat::Request& request) {
                if(!native_chat_text)native_chat_text.emplace(config.chinese_dictionary_root);
                const auto unicode=LegacyChineseCodec::decode(request.legacy_text,source.simplified);
                if(unicode.find('\0')!=std::string::npos)throw std::invalid_argument("Party chat embedded NUL");
                const auto text=native_chat_text->convert(unicode,recipient.simplified?ChineseLanguage::Simplified:ChineseLanguage::Traditional);
                const auto encoded=LegacyChineseCodec::encode_display(source.member.name+": "+text,recipient.simplified);
                auto logical=RecoveredPartyChat::display(source.member.character,recipient.simplified,encoded.bytes);
                if(config.streamer_privileges_enabled)StreamerPresentation::annotate(logical,source.privilege);
                return logical;
            });
            // CUSTOM-0074: private name authority is resolved from current
            // authenticated online owners; no translated-name alias grants.
            const auto private_chat_peer=[&](std::uint64_t id)->std::optional<OwnedPrivateChatService::Peer> {
                const auto at=native_chat_sessions.find(id);if(at==native_chat_sessions.end())return {};
                const auto peer=at->second.lock();if(!peer)return {};
                const auto member=party_member(*peer);if(!member)return {};
                const auto owned=database.recovered_characters().list_for_account(peer->account_id);
                const auto role=std::find_if(owned.begin(),owned.end(),[&](const auto& r){return r.id==peer->character_id;});
                if(role==owned.end())return {};
                const bool ready=peer->recovered_world_ready() &&
                    (peer->state()==SessionState::CharacterSelected || peer->state()==SessionState::InWorld ||
                     peer->state()==SessionState::InBattle) &&
                    !diagnostic_town_scene_pending.contains(id) && !diagnostic_island_return_pending.contains(id);
                return OwnedPrivateChatService::Peer{id,peer->account_id,static_cast<std::uint32_t>(peer->character_id),
                    member->name,ready,peer->recovered_client_language()==1,role->streamer_privilege};
            };
            OwnedPrivateChatService private_chat(private_chat_peer,[&] {
                std::vector<OwnedPrivateChatService::Peer> peers;
                for(const auto& [id,unused]:native_chat_sessions)if(auto peer=private_chat_peer(id))peers.push_back(std::move(*peer));
                return peers;
            },[](const auto& source,const RecoveredPrivateChat::Request& request) {
                // Session locale owns decoding, not the sender's header flag.
                return LegacyChineseCodec::decode(request.legacy_text,source.simplified);
            },[&](const auto& source,const auto& target,const auto& recipient,
                   const RecoveredPrivateChat::Request& request,const RecoveredPrivateChat::Text& input) {
                if(!native_chat_text)native_chat_text.emplace(config.chinese_dictionary_root);
                const auto message=native_chat_text->convert(input.message,
                    recipient.simplified?ChineseLanguage::Simplified:ChineseLanguage::Traditional);
                // Native496990 local summary and475E00/47EEB0 dedicated view
                // require [target] on the sender echo. Keep both owned names
                // exact, representable and complete before appending the body.
                const auto prefix=LegacyChineseCodec::encode(source.name+": ["+target.name+"] ",recipient.simplified);
                if(prefix.size()>=RecoveredChat::max_text_bytes)throw std::invalid_argument("Private display prefix bound");
                const auto body=LegacyChineseCodec::encode_display(message,recipient.simplified,
                    RecoveredChat::max_text_bytes-prefix.size());
                auto logical=RecoveredPrivateChat::display(source.character,recipient.simplified,
                    request.client_header[0]&0x7f,prefix+body.bytes);
                if(config.streamer_privileges_enabled)StreamerPresentation::annotate(logical,source.privilege);
                return logical;
            });
            // CUSTOM-0075: authoritative persistent membership, never the
            // native caller WORD or client-side Actor+6 string.
            const auto guild_chat_peer=[&](std::uint64_t id)->std::optional<OwnedGuildChatService::Peer> {
                try {
                const auto actor=private_chat_peer(id);if(!actor)return {};
                const auto membership=database.guilds().load(actor->account,actor->character);
                if(!membership)return {};
                return OwnedGuildChatService::Peer{*actor,*membership};
                }catch(const std::exception&){return {};}
            };
            OwnedGuildChatService guild_chat(guild_chat_peer,[&] {
                std::vector<OwnedGuildChatService::Peer> peers;
                for(const auto& [id,unused]:native_chat_sessions)if(auto peer=guild_chat_peer(id))peers.push_back(std::move(*peer));
                return peers;
            },[&](const auto& source,const auto& recipient,const RecoveredGuildChat::Request& request) {
                auto message=LegacyChineseCodec::decode(request.legacy_text,source.actor.simplified);
                if(LegacyChineseCodec::encode(message,source.actor.simplified)!=request.legacy_text)
                    throw std::invalid_argument("Guild source text is not lossless");
                if(!party_text)party_text.emplace(config.chinese_dictionary_root);
                message=party_text->convert(message,recipient.actor.simplified?ChineseLanguage::Simplified:ChineseLanguage::Traditional);
                const auto prefix=LegacyChineseCodec::encode(source.actor.name+": ",recipient.actor.simplified);
                if(prefix.size()>=RecoveredChat::max_text_bytes)throw std::invalid_argument("Guild display prefix bound");
                const auto body=LegacyChineseCodec::encode_display(message,recipient.actor.simplified,
                    RecoveredChat::max_text_bytes-prefix.size());
                auto logical=RecoveredGuildChat::display(source.actor.character,recipient.actor.simplified,prefix+body.bytes);
                if(config.streamer_privileges_enabled)StreamerPresentation::annotate(logical,source.actor.privilege);
                return logical;
            });
            std::map<std::uint64_t,std::pair<std::uint32_t,std::vector<std::uint8_t>>> guild_names_sent;
            const auto sync_guild_name=[&](Session& session,bool initial=false) {
                try {
                if(!session.recovered_world_ready() || !owned_player_and_companions_projected.contains(session.id()))return;
                const auto actor=private_chat_peer(session.id());if(!actor || !actor->ready)return;
                const auto membership=database.guilds().load(actor->account,actor->character);
                const auto name=membership?LegacyChineseCodec::encode(membership->name_utf8,actor->simplified):std::string{};
                const auto next=std::pair{actor->character,RecoveredGuildChat::name(name)};
                auto& previous=guild_names_sent[session.id()];
                if(previous!=next) {
                    // Preserve the accepted non-member initializer. A prior
                    // nonempty projection needs an explicit native clear.
                    if(membership || (previous.first && previous.second!=RecoveredGuildChat::name(""))) {
                        session.send_world_records(next.second);
                        spdlog::info("OWNED_GUILD_NAME_PROJECTED session_id={} character_id={} initial={} membership={} CUSTOM-0075",
                            session.id(),actor->character,initial,membership.has_value());
                    }
                    previous=next;
                }
                }catch(const std::exception& error) {
                    // Invalid maintenance state must not interrupt unrelated
                    // accepted channels. The guild service fails closed.
                    spdlog::warn("OWNED_GUILD_NAME_UNAVAILABLE session_id={} reason={} CUSTOM-0075",session.id(),error.what());
                }
            };
            // CUSTOM-0076: complete persistent roster cache using native91/92.
            // Initial8E panel/economy authority remains open, not zero-filled.
            OwnedGuildRosterService guild_roster(private_chat_peer,[&](auto account,auto character) {
                return database.guild_roster().load(account,character);
            },[&] {
                std::set<std::uint32_t> online;
                for(const auto& [id,unused]:native_chat_sessions)
                    if(const auto peer=private_chat_peer(id);peer && peer->ready)online.insert(peer->character);
                return online;
            });
            std::set<std::uint64_t> guild_roster_unavailable;
            std::map<std::uint64_t,std::uint64_t> guild_world_generation;
            std::set<std::uint64_t> guild_lab_prompted;
            std::unique_ptr<OwnedGuildMembershipService> guild_membership;
            std::unique_ptr<OwnedGuildEntryService> guild_entry;
            std::unique_ptr<OwnedGuildLeaderPanelService> guild_leader_panel;
            std::unique_ptr<OwnedGuildKickService> guild_kick;
            std::unique_ptr<OwnedGuildDisbandService> guild_disband; // CUSTOM-0081 native75.
            std::unique_ptr<OwnedGuildAnnouncementService> guild_announcements;
std::unique_ptr<OwnedGuildOfficerProjectionDraft> guild_officer_projection;
std::unique_ptr<OwnedGuildOfficerWorldHostDraft> guild_officer_world_host;
std::unique_ptr<OwnedGuildOfficerServiceDraft> guild_officer_service;
std::unique_ptr<OwnedGuildOfficerRuntimeDraft> guild_officer_runtime;


            std::shared_ptr<SharedGuildCoordinator53Draft> guild53;
            std::shared_ptr<GuildRelationCacheBootstrap53> guild_bootstrap53;
            std::shared_ptr<GuildAdmission53Application> guild_admission53;
            std::unique_ptr<SharedGuildApplication53Draft> guild53_routes;
            std::shared_ptr<OwnedGuildSuccessionApplicationDraft> guild_succession;
            std::shared_ptr<EffectiveGuildJoinConversationServiceDraft> guild_membership52;
            std::unique_ptr<EffectiveGuildJoinConversationRuntimeDraft> guild_conversation52;
            std::map<std::uint64_t,EffectiveGuildJoinConversationServiceDraft::Interaction> guild_interactions52;
            std::set<std::uint64_t> closed_guild_transports; // Actual on_disconnect, globally unique Session IDs.
            const auto guild_delivery_lifetime=std::make_shared<std::atomic_bool>(true);
            struct GuildDeliveryLifetime {std::shared_ptr<std::atomic_bool> value;~GuildDeliveryLifetime(){value->store(false);}} guild_delivery_guard{guild_delivery_lifetime};
            bool announcement_write_publication_suppressed=false;
            const auto guild_world_owner=
                    [&](std::uint64_t id)->std::optional<OwnedGuildMembershipService::Owner> {
                        const auto at=native_chat_sessions.find(id);if(at==native_chat_sessions.end())return {};
                        const auto session=at->second.lock();if(!session || !session->recovered_world_ready() ||
                            session->state()==SessionState::InBattle || !owned_player_and_companions_projected.contains(id) ||
                            diagnostic_town_scene_pending.contains(id) || diagnostic_island_return_pending.contains(id) || !recovered_movement)return {};
                        const auto position=recovered_movement->current_location(id,session->account_id,session->character_id);
                        const auto generation=guild_world_generation.find(id);
                        if(!position || generation==guild_world_generation.end() || !generation->second)return {};
                        if((migrations.back().version==52 || migrations.back().version==53) && position->revision==UINT64_MAX)return {};
                        return OwnedGuildMembershipService::Owner{id,session->account_id,session->character_id,generation->second,
                            position->area,position->scene,position->x,position->y,
                            static_cast<std::uint16_t>(session->recovered_client_language()==1?936:950),
                            session->battle_generation(),(migrations.back().version==52||migrations.back().version==53)?position->revision+1:position->revision};
                    };
            if(guild_membership_enabled && migrations.back().version!=53) {
                guild_membership=std::make_unique<OwnedGuildMembershipService>(*guild_membership_repository,
                    guild_world_owner,[&](auto account,auto character){return database.trades().load_wallet(account,character);},
                    [&](const auto& input){return lua.owned_guild_membership(input);});
                if(guild_entry_enabled)guild_entry=std::make_unique<OwnedGuildEntryService>(guild_world_owner,
                    [&](const auto& owner)->std::optional<SqliteOwnedGuildMembershipRepository::Identity> {
                        const auto identity=guild_membership_repository->nonmember(owner.account,owner.character);
                        if(guild_membership_repository->pending(owner.account,owner.character))return {};
                        return identity;
                    });
                guild_leader_panel=std::make_unique<OwnedGuildLeaderPanelService>(*guild_membership_repository,
                    guild_world_owner,[&](auto account,auto character){return database.guilds().load(account,character);},[&] {
                        std::set<std::uint32_t> online;
                        for(const auto& [id,unused]:native_chat_sessions)
                            if(const auto peer=private_chat_peer(id);peer && peer->ready)online.insert(peer->character);
                        return online;
                    });
                // CUSTOM-0080 online targets must remain fully projected and
                // outside battle so qualified native2D/92 clears immediately.
                // Offline targets are qualified by the repository snapshot.
                guild_kick=std::make_unique<OwnedGuildKickService>(*guild_membership_repository,
                    *guild_leader_panel,guild_world_owner,[&](const auto& target) {
                        for(const auto& [id,weak]:native_chat_sessions)if(const auto peer=weak.lock()) {
                            if(peer->character_id!=target.character_id)continue;
                            if(peer->account_id!=target.account_id || !guild_world_owner(id))return false;
                        }
                        return true;
                    });
                // CUSTOM-0081 world-only callback, valid before AND after SQL
                // removes memberships/governance/applications. It must not call
                // private_chat_peer/party_member (SQL reads), panel services,
                // guild repositories, packet sends or executor reentry.
                guild_disband=std::make_unique<OwnedGuildDisbandService>(*guild_membership_repository,
                    *guild_leader_panel,guild_world_owner,[&](const OwnedGuildLeaderPanelService::State& state) {
                        const auto ready=[&](const SqliteOwnedGuildMembershipRepository::Identity& identity) {
                            if(!identity.account_id || !identity.character_id)return false;
                            for(const auto& [id,weak]:native_chat_sessions)if(const auto peer=weak.lock()) {
                                if(peer->character_id!=identity.character_id)continue;
                                // Inspect EVERY matching session, including duplicate
                                // sessions and pending applicants; never stop at first.
                                const auto owner=guild_world_owner(id);
                                if(peer->account_id!=identity.account_id || !owner ||
                                   owner->session!=id || owner->account!=identity.account_id ||
                                   owner->character!=identity.character_id ||
                                   (peer->state()!=SessionState::CharacterSelected &&
                                    peer->state()!=SessionState::InWorld))return false;
                            }
                            return true; // Offline world policy only; storage still qualifies identity/nonbattle.
                        };
                        for(const auto& member:state.leader.roster)if(!ready(member))return false;
                        // Application identity/profile is historical; readiness compares
                        // only saved owned account/character IDs, not current level/name.
                        for(const auto& application:state.applications)if(!ready(application.applicant))return false;
                        return true;
                    });
                if(config.owned_guild_announcements_enabled && migrations.back().version!=52)
                    guild_announcements=std::make_unique<OwnedGuildAnnouncementService>(
                        (migrations.back().version==51?database.guild_announcements51():database.guild_announcements()),*guild_leader_panel,guild_world_owner);
            }
if(config.owned_guild_officers_enabled && migrations.back().version!=52 && migrations.back().version!=53) {
    if(migrations.back().version!=51 || !guild_leader_panel || !guild_kick || !guild_announcements)
        throw std::runtime_error("Officer runtime requires selected exact51 membership+announcements");
    guild_officer_projection=std::make_unique<OwnedGuildOfficerProjectionDraft>(
        *guild_membership_repository,*guild_leader_panel);
    guild_officer_world_host=std::make_unique<OwnedGuildOfficerWorldHostDraft>([&] {
        std::vector<OwnedGuildOfficerWorldHostDraft::Live> live;
        for(const auto& [id,weak]:native_chat_sessions)if(const auto peer=weak.lock())
            live.push_back({id,peer->account_id,peer->character_id,
                peer->state()==SessionState::CharacterSelected || peer->state()==SessionState::InWorld});
        return live;
    },guild_world_owner,[&](const auto& owner) {
        // SQL/profile/resource readability preflight ONLY OUTSIDE transaction.
        const auto actor=private_chat_peer(owner.session);
        return actor && actor->ready && actor->session==owner.session &&
            actor->account==owner.account && actor->character==owner.character;
    });
    guild_officer_service=std::make_unique<OwnedGuildOfficerServiceDraft>(
        *guild_membership_repository,*guild_officer_projection,guild_world_owner,
        [&](const auto& state){return guild_officer_world_host->capture(state);},
        [&](const auto& state,const auto& lease){return guild_officer_world_host->current(state,lease);});
    guild_officer_runtime=std::make_unique<OwnedGuildOfficerRuntimeDraft>(
        *guild_leader_panel,*guild_kick,*guild_officer_projection,*guild_officer_service);
}


            if(migrations.back().version==52) {
                using Adapter=OwnedGuildSuccessionApplicationDraft;
                const auto enumerate_guild_sessions=[&] {
                    std::vector<Adapter::Host::Live> live;
                    for(const auto& [id,weak]:native_chat_sessions)if(const auto peer=weak.lock())
                        live.push_back({id,peer->account_id,peer->character_id,
                            peer->state()==SessionState::CharacterSelected || peer->state()==SessionState::InWorld});
                    return live;
                };
                const auto recipient_ready=[&](const Adapter::Panel::Owner& owner) {
                    const auto at=native_chat_sessions.find(owner.session);if(at==native_chat_sessions.end())return false;
                    const auto peer=at->second.lock();return peer && peer->recovered_world_ready() && guild_world_owner(owner.session)==std::optional{owner};
                };
                const auto guild_context=[&](auto account,auto character)->std::optional<std::uint64_t> {
                    const auto member=database.guilds().load(account,character);
                    if(member && guild_membership_repository->player_created(member->guild_id))return member->guild_id;
                    const auto pending=guild_membership_repository->pending(account,character);
                    if(pending && guild_membership_repository->player_created(pending->target.id))return pending->target.id;
                    return {};
                };
                const auto executor=game.get_executor();
                // No captured App/map reference crosses to the Session strand.
                // The ACK posts GAME, checks lifetime there, then invokes only weak adapter callbacks.
                const auto send_guild=[&,executor,lifetime=guild_delivery_lifetime](const Adapter::Panel::Owner& owner,
                        std::vector<std::uint8_t> logical,std::function<void(bool)> ack) {
                    const auto at=native_chat_sessions.find(owner.session);
                    const auto peer=at==native_chat_sessions.end()?std::shared_ptr<Session>{}:at->second.lock();
                    if(!peer || guild_world_owner(owner.session)!=std::optional{owner}){ack(false);return;}
                    peer->bind_world_delivery_identity({owner.account,owner.character,owner.world_generation,owner.battle_generation});
                    peer->send_world_records_with_acceptance(std::move(logical),owner.account,owner.character,
                        owner.world_generation,owner.battle_generation,[executor,lifetime,ack=std::move(ack)](bool accepted)mutable {
                            if(!lifetime->load())return;
                            asio::post(executor,[lifetime,ack=std::move(ack),accepted]()mutable{if(lifetime->load())ack(accepted);});
                        });
                };
                guild_succession=std::make_shared<Adapter>(database.guild_succession52(config.owned_guild_succession_enabled),
                    database.guild_admission52(config.owned_guild_succession_enabled),database.guild_effective_announcements52(config.owned_guild_succession_enabled),
                    *guild_membership_repository,supply_repository,guild_world_owner,enumerate_guild_sessions,
                    [&](const auto& owner){const auto peer=private_chat_peer(owner.session);return peer && peer->ready && peer->session==owner.session && peer->account==owner.account && peer->character==owner.character;},
                    recipient_ready,[&](const auto& owner){return closed_guild_transports.contains(owner.session);},guild_context,send_guild,
                    config.owned_guild_membership_enabled,config.owned_guild_announcements_enabled,config.owned_guild_officers_enabled);
                guild_membership52=std::make_shared<EffectiveGuildJoinConversationServiceDraft>(database.guild_admission52(config.owned_guild_succession_enabled),
                    *guild_membership_repository,database.guild_succession52(config.owned_guild_succession_enabled),supply_repository,
                    [&](std::uint64_t id)->std::optional<EffectiveGuildJoinConversationServiceDraft::Interaction>{
                        const auto at=guild_interactions52.find(id);if(at==guild_interactions52.end() || guild_world_owner(id)!=std::optional{at->second.owner})return {};return at->second;
                    },recipient_ready,[&](const auto& target,const auto& apps,const auto& actor){return guild_succession->host().capture_membership(target,apps,actor);},
                    [&](const auto& audience){return guild_succession->host().preflight(audience);},[&](const auto& audience){return guild_succession->host().current(audience);},
                    [&](auto account,auto character){return database.trades().load_wallet(account,character);},[&](const auto& input){return lua.owned_guild_membership(input);},
                    [&](const auto& actor){return guild_succession->host().capture_nonmember(actor);});
                guild_conversation52=std::make_unique<EffectiveGuildJoinConversationRuntimeDraft>(*guild_membership52);
            }

            if(migrations.back().version==53){
                using Common=SharedGuildCoordinator53Draft;auto& factory=database.guild53(flags53);
                const auto enumerate=[&]{std::vector<Common::Host::Live> live;for(const auto& [id,weak]:native_chat_sessions)if(const auto peer=weak.lock())live.push_back({id,peer->account_id,peer->character_id,peer->state()==SessionState::CharacterSelected||peer->state()==SessionState::InWorld});return live;};
                const auto recipient_ready53=[&](const Common::Owner& owner){const auto at=native_chat_sessions.find(owner.session);if(at==native_chat_sessions.end())return false;const auto peer=at->second.lock();return peer&&peer->recovered_world_ready()&&guild_world_owner(owner.session)==std::optional{owner};};
                const auto context=[&](auto account,auto character)->std::optional<std::uint64_t>{if(const auto member=database.guilds().load(account,character);member&&factory.original().player_created(member->guild_id))return member->guild_id;if(const auto pending=factory.original().pending(account,character);pending&&factory.original().player_created(pending->target.id))return pending->target.id;return {};};
                const auto executor=game.get_executor();
                const auto send=[&,executor,lifetime=guild_delivery_lifetime](const Common::Owner& owner,std::vector<std::uint8_t> logical,std::function<void(bool)> ack){
                    const auto at=native_chat_sessions.find(owner.session);const auto peer=at==native_chat_sessions.end()?std::shared_ptr<Session>{}:at->second.lock();
                    if(!peer||guild_world_owner(owner.session)!=std::optional{owner}){ack(false);return;}
                    peer->bind_world_delivery_identity({owner.account,owner.character,owner.world_generation,owner.battle_generation});
                    peer->send_world_records_with_acceptance(std::move(logical),owner.account,owner.character,owner.world_generation,owner.battle_generation,[executor,lifetime,ack=std::move(ack)](bool accepted)mutable{if(!lifetime->load())return;asio::post(executor,[lifetime,ack=std::move(ack),accepted]()mutable{if(lifetime->load())ack(accepted);});});
                };
                // Build-matched ordered native reset supplies an EXPECTED cache
                // baseline. Client execution/acceptance stays deferred to phase2.
                guild53=std::make_shared<Common>(factory.relations(),factory.owner(),factory.notice_reader(),supply_repository,guild_world_owner,enumerate,
                    [&](const Common::Owner& owner){const auto peer=private_chat_peer(owner.session);return peer&&peer->ready&&peer->account==owner.account&&peer->character==owner.character;},recipient_ready53,
                    [&](const Common::Owner& owner){return closed_guild_transports.contains(owner.session);},context,send,
                    [&](const Common::Owner& owner)->std::optional<Common::Baseline>{return guild_bootstrap53?guild_bootstrap53->baseline(owner):std::nullopt;},flags53.relations,&factory.neighbors(),&factory.announcements(),
                    []{return OwnedGuildMembershipConversation::Clock::now();},&factory.original());
                guild_bootstrap53=std::make_shared<GuildRelationCacheBootstrap53>(
                    [&](const Common::Owner& owner)->std::optional<GuildRelationCacheBootstrap53::Self>{
                        if(guild_world_owner(owner.session)!=std::optional{owner})return {};
                        const auto identity=factory.original().identity(owner.account,owner.character);if(!identity.role)return {};
                        const auto level=RecoveredRoleLevel::parse(identity.role->logical);if(!level)return {};
                        const auto name=LegacyChineseCodec::encode(identity.name_utf8,owner.name_codepage==936);
                        if(LegacyChineseCodec::decode(name,owner.name_codepage==936)!=identity.name_utf8)return {};
                        return GuildRelationCacheBootstrap53::Self{owner,name,level->level(),identity.profile[29]};
                    },send,[&](const Common::Owner& owner){if(guild53&&guild_world_owner(owner.session)==std::optional{owner})guild53->sync(owner.session,false);});
                guild53_routes=std::make_unique<SharedGuildApplication53Draft>(guild53,factory.original(),[&](auto session,auto index,auto opcode,bool committed){spdlog::info("GUILD53_ACTION session_id={} index={} opcode={} committed={} CUSTOM-0083 CUSTOM-0084 cache_basis=ordered_native_reset acceptance=deferred",session,index,opcode,committed);});
                guild_admission53=std::make_shared<GuildAdmission53Application>(guild53,factory.neighbors(),factory.original(),factory.owner(),supply_repository,
                    recipient_ready53,[&](auto account,auto character){return database.trades().load_wallet(account,character);},
                    [&](const auto& input){return lua.owned_guild_membership(input);});
                guild53_routes->admission(guild_admission53);
            }

            const auto prepare_owned_panel=[&](std::uint64_t id,bool open=false)->std::optional<OwnedGuildOfficerProjectionDraft::Plan> {
                if(guild_officer_projection)return guild_officer_projection->prepare(id,open);
                const auto base=guild_leader_panel->prepare(id,open);
                return base?std::optional{OwnedGuildOfficerProjectionDraft::Plan{*base,{},base->logical}}:std::nullopt;
            };
            const auto current_owned_panel=[&](const OwnedGuildOfficerProjectionDraft::Plan& p) {
                return guild_officer_projection?guild_officer_projection->current(p):guild_leader_panel->current(p.base);
            };
            const auto published_owned_panel=[&](const OwnedGuildOfficerProjectionDraft::Plan& p) {
                return guild_officer_projection?guild_officer_projection->published(p):guild_leader_panel->published(p.base);
            };
            const auto prepare_owned_notice=[&](std::uint64_t id,bool open)->std::optional<OwnedGuildOfficerRuntimeDraft::Notice> {
                if(guild_officer_runtime)return guild_officer_runtime->prepare_notice(*guild_announcements,id,open);
                const auto base=guild_announcements->prepare(id,open);if(!base)return {};
                return OwnedGuildOfficerRuntimeDraft::Notice{*base,{base->panel,{},base->panel.logical},base->logical};
            };
            const auto current_owned_notice=[&](const OwnedGuildOfficerRuntimeDraft::Notice& p) {
                return guild_officer_runtime?guild_officer_runtime->current_notice(*guild_announcements,p):guild_announcements->current(p.original);
            };
            const auto published_owned_notice=[&](const OwnedGuildOfficerRuntimeDraft::Notice& p,OwnedGuildAnnouncementService::Time now) {
                return guild_officer_runtime?guild_officer_runtime->published_notice(*guild_announcements,p,now):guild_announcements->published(p.original,now);
            };
            const auto invalidate_owned_panel=[&](std::uint64_t id) {
                if(guild_officer_runtime)guild_officer_runtime->invalidate(id);else if(guild_leader_panel)guild_leader_panel->invalidate(id);
            };
            const auto observe_owned_panel=[&](std::uint64_t id) {
                if(guild_officer_runtime)guild_officer_runtime->observe_world(id);else if(guild_leader_panel)guild_leader_panel->observe_world(id);
            };
            const auto player_guild=[&](const Session& session) {
                // Presence is independent of enabled mutation services.
                try {
                    const auto membership=database.guilds().load(session.account_id,session.character_id);
                    return membership && guild_membership_repository->player_created(membership->guild_id);
                }catch(const std::exception&){return true;} // invalid lab state must not borrow frozen leave authority
            };
            OwnedGuildPanelService guild_panel(guild_roster,[&](auto account,auto character,const auto& expected) {
                database.guild_leave().leave(account,character,expected);
            }); // CUSTOM-0077: member view and authenticated self-leave only
            // Lifetime spans the running game executor. game_handlers below
            // is moved into TcpServer and must not be captured for recursion.
            std::function<std::optional<std::vector<std::uint8_t>>(
                Session&,std::span<const RecoveredWorldRecords::Record>)> guild_ordered_world_records;
            const auto sync_guild_roster=[&](Session& session) {
                if(!session.recovered_world_ready() || !owned_player_and_companions_projected.contains(session.id()))return;
                if(guild53){guild53->sync(session.id(),false);return;}
                if(guild_succession && (guild_succession->context(session.id()) || guild_succession->panel().cached(session.id()) || player_guild(session))){guild_succession->sync(session.id());return;}
                if(player_guild(session)) {
                    if(!guild_leader_panel)return; // disabled retains player-created classification
                    const auto plan=prepare_owned_panel(session.id());
                    if(!plan || !current_owned_panel(*plan)) {
                        spdlog::warn("OWNED_GUILD_LEADER_PROJECTION_DENIED session_id={} CUSTOM-0078",session.id());return;
                    }
                    if(!plan->logical.empty())session.send_world_records(plan->logical);
                    if(!published_owned_panel(*plan))return;
                    if(!plan->logical.empty())spdlog::info("OWNED_GUILD_LEADER_PROJECTED session_id={} character_id={} members={} pending={} CUSTOM-0078",
                        session.id(),session.character_id,plan->base.next.leader.roster.size(),plan->base.next.applications.size());
                    return;
                }
                if(guild_leader_panel && guild_leader_panel->cached(session.id())) {
                    const auto clear=guild_leader_panel->prepare_clear(session.id());
                    if(!clear || !guild_leader_panel->current(*clear))return;
                    session.send_world_records(clear->logical);
                    if(guild_officer_runtime?!guild_officer_runtime->complete_clear(*clear):!guild_leader_panel->cleared(*clear))return;
                }
                const auto plan=guild_roster.prepare(session.id());
                if(!plan || !guild_roster.current(*plan)) {
                    if(guild_roster_unavailable.insert(session.id()).second)
                        spdlog::warn("OWNED_GUILD_ROSTER_UNAVAILABLE session_id={} character_id={} unqualified_snapshot_or_stale_lease CUSTOM-0076 no_saved_data_change",
                            session.id(),session.character_id);
                    return;
                }
                guild_roster_unavailable.erase(session.id());
                if(!plan->logical.empty()) {
                    session.send_world_records(plan->logical);
                    spdlog::info("OWNED_GUILD_ROSTER_PROJECTED session_id={} character_id={} members={} logical_bytes={} CUSTOM-0076 no_economy_mutation",
                        session.id(),session.character_id,plan->next.roster?plan->next.roster->members.size():0,plan->logical.size());
                }
                guild_roster.published(*plan);
            };
            const auto party_projection=[&](const NativeParty::Deliveries& deliveries) {
                std::map<std::uint64_t,std::vector<std::uint8_t>> batches;
                std::map<std::uint64_t,std::map<std::string,std::uint16_t>> roster_names;
                for(const auto& d:deliveries) {
                    const auto at=party_sessions.find(d.recipient);if(at==party_sessions.end())continue;
                    auto recipient=at->second.lock();if(!recipient || !recipient->recovered_world_ready())continue;
                    if(!party_text)party_text.emplace(config.chinese_dictionary_root);
                    const bool cn=recipient->recovered_client_language()==1;
                    // Native55/57 recognize self by the actor's exact name.
                    // Character-list transcoding preserves Unicode variants;
                    // OpenCC must not turn one's own 台 into 臺 here.
                    const auto translated=d.recipient==d.actor.session?d.actor.name:
                        party_text->convert(d.actor.name,cn?ChineseLanguage::Simplified:ChineseLanguage::Traditional);
                    const auto encoded=LegacyChineseCodec::encode_display(translated,cn);
                    if(encoded.replacements || encoded.truncated || encoded.bytes.empty() || encoded.bytes.size()>14)
                        throw DatabaseError("Party display name unrepresentable");
                    if(d.event==NativeParty::Event::Add) {
                        auto& names=roster_names[d.recipient];
                        const auto [existing,inserted]=names.emplace(encoded.bytes,d.actor.character);
                        if(!inserted && existing->second!=d.actor.character)
                            throw DatabaseError("Party translated names collide in native roster");
                    }
                    RecoveredParty::Name name{};std::copy(encoded.bytes.begin(),encoded.bytes.end(),name.begin());
                    std::vector<std::uint8_t> logical;
                    switch(d.event) {
                    case NativeParty::Event::Preview:logical=RecoveredParty::preview(d.actor.character,name,d.actor.profession,d.actor.transfer,d.actor.hud,d.actor.level);break;
                    case NativeParty::Event::Add:logical=RecoveredParty::member(d.actor.character,name,d.leader,d.actor.hud);break;
                    case NativeParty::Event::Remove:logical=RecoveredParty::remove(d.actor.character,name);break;
                    case NativeParty::Event::Position:logical=RecoveredParty::position(d.actor.character,d.actor.x,d.actor.y);break;
                    case NativeParty::Event::Vitals:logical=RecoveredParty::vitals(d.actor.character,d.actor.resources[0],d.actor.resources[1],d.actor.resources[2],d.actor.resources[3]);break;
                    }
                    auto& batch=batches[d.recipient];batch.insert(batch.end(),logical.begin(),logical.end());
                }
                return batches;
            };
            const auto deliver_parties=[&](std::map<std::uint64_t,std::vector<std::uint8_t>> batches) {
                for(auto& [id,logical]:batches)if(const auto at=party_sessions.find(id);at!=party_sessions.end())
                    if(auto peer=at->second.lock())peer->send_world_records(std::move(logical));
            };
            const auto refresh_party_members=[&](NativeParty& next,std::vector<std::uint64_t> ids) {
                std::sort(ids.begin(),ids.end());ids.erase(std::unique(ids.begin(),ids.end()),ids.end());
                std::map<std::uint64_t,NativeParty::Member> previous;
                // Observe every relevant peer before generating any diffs, so
                // readiness recovery is independent of session iteration order.
                for(const auto id:ids) {
                    const auto before=next.member(id);if(before)previous.emplace(id,*before);
                    const auto at=party_sessions.find(id);
                    const auto peer=at==party_sessions.end()?std::shared_ptr<Session>{}:at->second.lock();
                    const auto observed=peer?party_member(*peer):std::optional<NativeParty::Member>{};
                    if(observed)next.observe(*observed);
                    else if(before){auto unavailable=*before;unavailable.ready=false;next.observe(std::move(unavailable));}
                }
                NativeParty::Deliveries changes;
                for(const auto& [id,before]:previous) {
                    const auto diff=next.refresh(id,before);changes.insert(changes.end(),diff.begin(),diff.end());
                }
                return changes;
            };
            // CUSTOM-0086 shared-state/checkpoint/outbox backend now exists in
            // OwnedPkRoomState + SqliteOwnedPkRoomRepository; native35 owned
            // selection/two-view83/86/88 now joins that shared backend too.
            // No complete RoomAuthority adapter owns profiles, dual Session entry/turns,
            // transport receipts, terminal WORLD re-entry and recovery yet.
            // Do not install the opt-in schema or publish an invitation until
            // that adapter is complete;69 still returns RoomUnavailable.
            std::unique_ptr<OwnedPkInvitationService::RoomAuthority> pk_rooms;
            std::map<std::uint64_t,std::uint64_t> pk_world_generations;
            // This guard covers EVERY PK peer observer, not only the roster
            // reader. A caught nested resolver still poisons the outer result.
            bool pk_peer_reading=false,pk_peer_reentered=false;
            const auto pk_peer=[&](std::uint64_t id)->std::optional<OwnedPkInvitationService::Peer> {
                if(pk_peer_reading){pk_peer_reentered=true;return {};}
                struct Reading {
                    bool& active;
                    explicit Reading(bool& value):active(value){active=true;}
                    ~Reading(){active=false;}
                } reading(pk_peer_reading);
                pk_peer_reentered=false;
                try {
                    const auto peer=[&] {
                        const auto at=party_sessions.find(id);
                        return at==party_sessions.end()?std::shared_ptr<Session>{}:at->second.lock();
                    }();
                    const auto generation=[&] {
                        const auto at=pk_world_generations.find(id);
                        return at==pk_world_generations.end()?std::uint64_t{}:at->second;
                    }();
                    if(!peer || !generation || !recovered_movement)return {};
                    // Own all immutable material/handles BEFORE any repository
                    // observer; retaining the mutable source holder alone is
                    // insufficient if a caught callback replaces its contents.
                    const auto source=[&] {
                        const auto at=owned_companion_restoration_sources.find(id);
                        return at==owned_companion_restoration_sources.end()?
                            std::shared_ptr<OwnedCompanionRestorationSource>{}:at->second;
                    }();
                    const auto material=source?source->material:
                        std::shared_ptr<const RecoveredOwnedCompanions::Restoration>{};
                    const auto initialization=source?source->normal_initialization:
                        std::optional<Session::NormalWorldInitialization>{};
                    const auto prefix=source?source->expected_receiving_prefix:
                        std::optional<TaiwanNativeDeityRosterPrefix>{};
                    const auto receipts=source?source->write_observations:
                        std::vector<Session::WorldRecordsWrite>{};
                    const auto submitted=source?source->submission_calls_completed:std::size_t{};
                    const bool all_submitted=source && source->all_submission_calls_returned;
                    if(initialization && !peer->normal_world_initialization_current_on_game(*initialization))return {};
                    const auto account=peer->account_id,character=peer->character_id;
                    const auto battle=peer->battle_generation();
                    const auto phase=peer->state();
                    if(!account || !character || character>UINT32_MAX)return {};
                    const auto local=[&] {
                        const auto at=party_sessions.find(id);
                        const auto gen=pk_world_generations.find(id);
                        return !pk_peer_reentered && at!=party_sessions.end() &&
                            at->second.lock()==peer && gen!=pk_world_generations.end() && gen->second==generation &&
                            !peer->closing() && peer->account_id==account && peer->character_id==character &&
                            peer->state()==phase && peer->battle_generation()==battle;
                    };
                    const auto source_local=[&] {
                        if(!local() || !source || !material || !initialization || !prefix || !all_submitted ||
                           !peer->recovered_world_ready() ||
                           (phase!=SessionState::CharacterSelected && phase!=SessionState::InWorld))return false;
                        const auto at=owned_companion_restoration_sources.find(id);
                        if(at==owned_companion_restoration_sources.end() || at->second!=source ||
                           source->session.lock()!=peer || source->material!=material ||
                           source->account!=account || source->character!=character ||
                           source->phase_at_restore!=phase || source->battle_generation_at_restore!=battle ||
                           source->all_submission_calls_returned!=all_submitted ||
                           source->submission_calls_completed!=submitted || !source->normal_initialization ||
                           !source->expected_receiving_prefix || source->write_observations.size()!=receipts.size())return false;
                        const auto& now=*source->expected_receiving_prefix;
                        if(now.rows()!=prefix->rows() || now.roster_count()!=prefix->roster_count() ||
                           now.selected_row()!=prefix->selected_row() || now.catalog_records()!=prefix->catalog_records() ||
                           now.actual_batches()!=prefix->actual_batches() ||
                           source->normal_initialization->entry_frame()!=initialization->entry_frame() ||
                           source->normal_initialization->entry_logical()!=initialization->entry_logical() ||
                           source->normal_initialization->accepted_tail()!=initialization->accepted_tail() ||
                           source->normal_initialization->config_flag()!=initialization->config_flag())return false;
                        for(std::size_t i=0;i<receipts.size();++i)
                            if(source->write_observations[i].logical()!=receipts[i].logical())return false;
                        return material->deity_roster().account()==account && material->deity_roster().character()==character;
                    };
                    const auto transport_current=[&] {
                        if(!source_local() || !peer->normal_world_initialization_current_on_game(*initialization) ||
                           !initialization->entry_written())return false;
                        const auto& batches=material->batches();
                        if(submitted!=batches.size() || receipts.size()!=batches.size())return false;
                        for(std::size_t i=0;i<receipts.size();++i)
                            if(receipts[i].logical()!=batches[i] ||
                               !peer->world_records_write_current_on_game(receipts[i]) ||
                               receipts[i].status()!=Session::WorldRecordsWriteStatus::Written)return false;
                        return source_local();
                    };
                    const auto saved_prefix_current=[&] {
                        if(!transport_current() || !owned_companions.restoration_current(*material) ||
                           !transport_current())return false;
                        return owned_companions.normal_entry_prefix_current(*material,*prefix,database.native_skill_catalog()) &&
                            transport_current();
                    };
                    const auto position=recovered_movement->current_location(id,account,character);
                    if(!position || !local())return {};
                    const bool blocked=trade_active(id)||diagnostic_town_scene_pending.contains(id)||
                        diagnostic_island_return_pending.contains(id)||
                        supply_repository.owned_pending_battle(account,character);
                    if(!local())return {};
                    bool ready=owned_player_and_companions_projected.contains(id) && saved_prefix_current();
                    // Reobserve real position after all earlier observers, then
                    // requalify the full saved roster/catalog on both sides of
                    // the pure transport checks. This is a current readset, not
                    // atomic future admission CAS or remote consumer attestation.
                    if(!local() || recovered_movement->current_location(id,account,character)!=position || !local())return {};
                    if(ready)ready=saved_prefix_current();
                    if(!local() || recovered_movement->current_location(id,account,character)!=position || !local())return {};
                    if(ready)ready=owned_player_and_companions_projected.contains(id) && transport_current();
                    if(!local())return {};
                    return OwnedPkInvitationService::Peer{id,account,character,generation,battle,*position,ready,blocked};
                } catch(...) {
                    // A failed passive PK source observer cannot interrupt the
                    // original unrelated world handler or manufacture readiness.
                    return {};
                }
            };
            OwnedPkInvitationService pk_invitations(pk_peer,
                [&](std::uint32_t character)->std::optional<OwnedPkInvitationService::Peer> {
                    std::optional<OwnedPkInvitationService::Peer> result;
                    for(const auto&[id,weak]:party_sessions)if(const auto peer=pk_peer(id);peer&&peer->character==character){
                        if(result)return {};result=peer;
                    }
                    return result;
                },[&](const OwnedPkInvitationService::Pair& pair){
                    return lua.pk_invitation_allowed(pair.challenger.ready,pair.recipient.ready,
                        pair.challenger.position.area==pair.recipient.position.area&&pair.challenger.position.scene==pair.recipient.position.scene,
                        pair.challenger.character!=pair.recipient.character,pair.challenger.blocked,pair.recipient.blocked);
                },[&](const OwnedPkInvitationService::Peer& recipient,const RecoveredPk69::Bytes& bytes){
                    if(pk_peer(recipient.session)!=std::optional{recipient})return false;
                    const auto at=party_sessions.find(recipient.session);if(at==party_sessions.end())return false;
                    const auto peer=at->second.lock();if(!peer)return false;
                    peer->send_world_records(std::vector<std::uint8_t>(bytes.begin(),bytes.end()));
                    return true; // transport submission only; native69 must echo its exact lease
                },[&]{return pk_rooms.get();});
            if(config.owned_pk_invitation_enabled)
                spdlog::warn("OWNED_PK_SOURCE_INCOMPLETE room_authority=unavailable invitations_not_published CUSTOM-0086");
            Session::DisconnectHandler on_disconnect=[&](std::shared_ptr<Session> session) {
                    if(blacklist_lifetime->load()) {
                        const auto at=blacklist_replays.find(session->id());
                        if(at!=blacklist_replays.end() && at->second.session.lock()==session)retire_blacklist_output(at->second);
                    }
                    if(owned_client_options)try{owned_client_options->disconnect(*session);}
                    catch(const std::exception& error){spdlog::warn("CLIENT_OPTIONS_RETIRE_FAILED reason={}",error.what());}
                    // Retire this exact source before any unrelated disconnect
                    // observer can throw. Never erase another Session by ID alone.
                    if(const auto at=owned_companion_restoration_sources.find(session->id());
                       at!=owned_companion_restoration_sources.end() && at->second->session.lock().get()==session.get())
                        owned_companion_restoration_sources.erase(at);
                    if(const auto at=blacklist_replays.find(session->id());at!=blacklist_replays.end() &&
                       at->second.session.lock().get()==session.get())blacklist_replays.erase(at);
                    if(owned_party_directory)try{if(owned_party_directory_retire)owned_party_directory_retire(*session);else owned_party_directory->disconnect(*session);}
                    catch(const std::exception& error){spdlog::warn("PARTY_DIRECTORY_RETIRE_FAILED reason={}",error.what());}
                    pk_invitations.invalidate(session->id());pk_world_generations.erase(session->id());
                    native_banks.disconnect(session->id());
                    bank_items_disconnect(session->id());
                    trade_sessions.erase(session->id());trade_wallet_sent.erase(session->id());
                    try{deliver_trades(owned_instance_trades?owned_instance_trades->disconnect(session->id()):native_trades.disconnect(session->id()));}
                    catch(const std::exception& error){spdlog::warn("NATIVE_TRADE_DISCONNECT_SYNC_FAILED reason={}",error.what());}
                    // Party leases are transient and independent of frozen chat.
                    auto next=native_parties;
                    const auto departures=next.disconnect(session->id());
                    try {auto projected=party_projection(departures);native_parties=std::move(next);deliver_parties(std::move(projected));}
                    catch(const std::exception& error){native_parties=std::move(next);spdlog::warn("NATIVE_PARTY_DISCONNECT_PROJECTION_FAILED reason={}",error.what());}
                    party_sessions.erase(session->id());
                    pending_visibility.erase(session->id());
                    pending_visibility_refresh.erase(session->id());
                    visibility_sessions.erase(session->id());
                    native_chat_sessions.erase(session->id());
                    if(guild53){closed_guild_transports.insert(session->id());guild53->disconnected(session->id());}
                    if(guild_bootstrap53)guild_bootstrap53->revoke(session->id());
                    if(guild_admission53)guild_admission53->disconnected(session->id());
                    if(guild_succession){closed_guild_transports.insert(session->id());guild_succession->disconnected(session->id());}
                    if(guild_membership52)guild_membership52->invalidate(session->id());guild_interactions52.erase(session->id());
                    guild_names_sent.erase(session->id());
                    guild_roster.forget(session->id());
                    if(guild_membership)guild_membership->disconnect(session->id());
                    if(guild_entry)guild_entry->disconnect(session->id());
                    if(guild_officer_projection)guild_officer_projection->forget_after_clear(session->id());
                    else if(guild_leader_panel)guild_leader_panel->forget(session->id());
                    if(guild_announcements)guild_announcements->forget(session->id());
                    guild_world_generation.erase(session->id());guild_lab_prompted.erase(session->id());
                    guild_roster_unavailable.erase(session->id());
                    streamer_sent.erase(session->id());
                    owned_bag_projected.erase(session->id());
                    owned_beasts_projected.erase(session->id());
                    beast_exploration.disconnect(session->id());
                    deliver_visibility(player_visibility.leave(session->id()));
                    world.remove_player(session->id());
                    if(recovered_movement) recovered_movement->remove(session->id());
                    diagnostic_battle_sent.erase(session->id());
                    world_display_scene.erase(session->id());
                    native_monster_placement_gap_logged.erase(session->id());
                    diagnostic_movement_ready.erase(session->id());
                    diagnostic_encounters_started.erase(session->id());
                    diagnostic_world_resources_sent.erase(session->id());
                    owned_player_and_companions_projected.erase(session->id());
                    owned_supply_projected.erase(session->id());
                    owned_weapons_projected.erase(session->id());
                    owned_armor_projected.erase(session->id());
                    owned_gems_projected.erase(session->id());
                    teleport_gem_offers.forget(session->id());
                    diagnostic_vitals_sent.erase(session->id());
                    diagnostic_quest_dialogue_sent.erase(session->id());
                    world_clock_sessions.erase(session->id());
                    issued_daily_lists.erase(session->id());
                    knowledge_conversations.remove(session->id());
                    diagnostic_town_guides_sent.erase(session->id());
                    diagnostic_remote_ticks.erase(session->id());
                    diagnostic_remote_appearance.erase(session->id());
                    diagnostic_town_map_replied.erase(session->id());
                    diagnostic_town_scene_pending.erase(session->id());
                    diagnostic_island_return_pending.erase(session->id());
                    pending_town_guides.erase(session->id());
                    fruit_quests.remove(session->id());
                    diagnostic_quest_conversations.remove(session->id());
                    diagnostic_rounds_granted.erase(session->id());
                    diagnostic_town_battle_won.erase(session->id());
                    if(diagnostic_combat) diagnostic_combat->remove(session->id());
                    if(fixture_battles) fixture_battles->remove(session->id());
                };
            std::unique_ptr<TcpServer> character_server;
            // Retire before character_server and borrowed repository/maps on every unwind.
            struct BlacklistOutputLifetime {
                const decltype(stop_blacklist_outputs)& stop;
                ~BlacklistOutputLifetime(){stop();}
            } blacklist_output_guard{stop_blacklist_outputs};
            // Declared AFTER character_server: revoke real callbacks first on
            // every unwind. Its later destructor post retains only an empty vault.
            WholeBagMoveHostGuard whole_bag_move_lifetime{whole_bag_moves};
            WorldLifecycleVaultGuard common_world_lifetime{
                common_world?std::make_shared<WorldLifecycleVault>(config.max_sessions):nullptr};
            std::vector<std::uint8_t> character_routes;
            if(config.recovered_dual_connection) {
                auto game_handlers=character_handlers;
                if(config.recovered_world_entry) {
                    game_handlers.world_entry=[&](std::uint64_t session,std::uint64_t account,std::uint64_t character) {
                        if(recovered_movement) {
                            auto frame=recovered_movement->prepare(session,account,character);
                            if(config.owned_player_appearance_enabled ||
                               (config.diagnostic_shunying_manual && character==config.diagnostic_shunying_character_id)) {
                                const auto appearance=database.player_appearance().load(account,character);
                                if(appearance) {
                                    const auto projected=RecoveredOwnedPlayerAppearance::world_entry(frame,*appearance);
                                    if(projected.size()!=frame.size())throw DatabaseError("Owned appearance frame width rejected");
                                    std::copy(projected.begin(),projected.end(),frame.begin());
                                }
                            }
                            if(config.diagnostic_owned_weapon_appearance ||
                               (config.diagnostic_shunying_manual && character==config.diagnostic_shunying_character_id)) {
                                // CUSTOM-0047 fixture selects the native ordinary/unmounted
                                // resolver. Historical2A byte6=27 instead forces Drv weapon8.
                                auto logical=RecoveredWorldFrame::decode(frame);
                                if(!logical || logical->size()!=37 || logical->front()!=0x2a)throw DatabaseError("Diagnostic appearance world frame rejected");
                                (*logical)[7]=0;
                                const auto ordinary=RecoveredWorldFrame::encode(*logical);
                                if(ordinary.size()!=frame.size())throw DatabaseError("Diagnostic ordinary frame width rejected");
                                std::copy(ordinary.begin(),ordinary.end(),frame.begin());
                            }
                            if(player_presence_enabled) {
                                const auto owned=database.recovered_characters().list_for_account(account);
                                const auto found=std::find_if(owned.begin(),owned.end(),[&](const auto& row) {
                                    return row.id==character;
                                });
                                if(found==owned.end()) throw std::runtime_error("Visibility profile ownership rejected");
                                const auto spawn=RecoveredRemoteActor::parse_logical(
                                    DiagnosticRemoteActor::logical(0,config.diagnostic_remote_actor_language)).value();
                                const auto removal=RecoveredRemoteActorRemove::parse_logical(
                                    DiagnosticRemoteActor::logical(2,config.diagnostic_remote_actor_language)).value();
                                auto presence=RecoveredPlayerPresence::from_world_entry(
                                    session,account,character,frame,found->profile,spawn,removal);
                                if(const auto saved=database.role_text().load(account,character)) {
                                    const auto text=SqliteRoleTextRepository::project(*saved,
                                        RecoveredRemoteRoleText::source_codepage(presence.spawn));
                                    presence.spawn=RecoveredRemoteRoleText::with_source_text(presence.spawn,
                                        text.value_or(RecoveredRoleText::Text{})).value();
                                }
                                pending_visibility.insert_or_assign(session,presence);
                            }
                            if(config.diagnostic_remote_actor || config.diagnostic_shunying_manual) {
                                const auto logical=RecoveredWorldFrame::decode(frame);
                                if(!logical || logical->size()!=37 || logical->front()!=0x2a)
                                    throw std::runtime_error("Diagnostic remote source world frame rejected");
                                RecoveredWorldEntry::Body body;
                                std::copy_n(logical->begin()+1,body.size(),body.begin());
                                diagnostic_remote_appearance.insert_or_assign(session,body);
                            }
                            return frame;
                        }
                        return recovered_characters.world_entry_candidate(account,character);
                    };
                    spdlog::warn("Historical world-entry candidate enabled; two owned component variants projected, other appearance/map fields unverified; live world acceptance unverified");
                    spdlog::warn("Historical scalar bootstrap retired; no unverified character attributes are replayed after the initialization tail");
                    if(recovered_movement) {
                        game_handlers.world_ready=[&](Session& session) {
                            if(config.owned_pk_invitation_enabled){
                                pk_invitations.invalidate(session.id());auto& generation=pk_world_generations[session.id()];
                                if(generation==UINT64_MAX)throw std::runtime_error("PK world generation exhausted");
                                ++generation;
                            }
                            if(guild_membership || guild_succession || guild53) {
                                auto& generation=guild_world_generation[session.id()];
                                if(generation==UINT64_MAX)throw std::runtime_error("Guild world generation exhausted");
                                ++generation;if(guild_membership)guild_membership->invalidate(session.id());guild_lab_prompted.erase(session.id());
                                if(guild_entry)guild_entry->invalidate(session.id());
                                if(guild_leader_panel)invalidate_owned_panel(session.id());
                                if(guild_announcements)guild_announcements->invalidate(session.id());
                            }
                            if(config.diagnostic_battle_transition)
                                diagnostic_encounters_started.try_emplace(session.id(),0);
                            if(config.diagnostic_battle_after_movement)
                                diagnostic_movement_ready.try_emplace(session.id(),false);
                            if(guild53){guild53->revoke(session.id());if(guild_bootstrap53)guild_bootstrap53->revoke(session.id());if(guild_admission53)guild_admission53->invalidate(session.id());session.bind_world_delivery_identity({session.account_id,session.character_id,guild_world_generation.at(session.id()),session.battle_generation()});}
                            if(guild_succession){
                                guild_succession->revoke(session.id());if(guild_membership52)guild_membership52->invalidate(session.id());guild_interactions52.erase(session.id());
                                session.bind_world_delivery_identity({session.account_id,session.character_id,guild_world_generation.at(session.id()),session.battle_generation()});
                            }
                            recovered_movement->bind(session.id(),session.account_id,session.character_id);
                            party_sessions.insert_or_assign(session.id(),session.weak_from_this());
                            trade_sessions.insert_or_assign(session.id(),session.weak_from_this());
                            database.trades().provision_wallet(session.account_id,session.character_id);
                            // CUSTOM-0050: production supply admission never provisions fixture rewards/bags.
                            if(config.diagnostic_town_quest_progress && !config.owned_supply_enabled &&
                               supply_repository.provision_town_reward_slot(session.account_id,session.character_id))
                                spdlog::warn("DIAGNOSTIC_TOWN_EMPTY_SLOT_PROVISIONED session_id={} CUSTOM-0031",session.id());
                            if(config.diagnostic_town_quest_progress && !config.owned_supply_enabled)
                                supply_repository.provision_owned_bag(session.account_id,session.character_id);
                            // CUSTOM-0030: exact native language flag and bound world identity.
                            supply_repository.bind_name_encoding(session.account_id,session.character_id,
                                session.recovered_client_language()==1);
                            native_chat_sessions.insert_or_assign(session.id(),session.shared_from_this());
                            if((config.diagnostic_quest_dialogue || config.diagnostic_town_spawn_guides) &&
                               !diagnostic_quest_conversations.bind(session.id(),session.account_id,session.character_id))
                                throw std::runtime_error("Diagnostic quest world binding rejected");
                        };
                        recovered_world=std::make_unique<RecoveredWorldService>([&](Session& session,std::span<const RecoveredMovement::Request> requests) {
                            if(config.diagnostic_player_visibility) {
                                if(!player_visibility.contains(session.id()))
                                    throw std::invalid_argument("Visibility movement before first world tick");
                                auto committed=recovered_movement->move_committed(
                                    session.id(),session.account_id,session.character_id,requests);
                                publish_visibility_movement(session,committed);
                                return std::move(committed.reply);
                            }
                            if(config.diagnostic_town_door_routes) {
                                std::optional<DiagnosticDoorPlan> door_plan;
                                auto moved=recovered_movement->move_committed(session.id(),session.account_id,
                                    session.character_id,requests,[&](const RecoveredMovementService::MovePreview& move) {
                                    if(!move.displaced_steps) return;
                                    if(config.diagnostic_town_island_routes && move.scene==0)
                                        spdlog::info("DIAGNOSTIC_ISLAND_STEP session_id={} from=({}, {}) to=({}, {}) steps={}",
                                            session.id(),move.before_x,move.before_y,move.x,move.y,move.displaced_steps);
                                    door_plan=lua.diagnostic_door({move.area,move.scene,
                                        move.before_x,move.before_y,move.x,move.y,
                                        config.diagnostic_town_island_routes,config.diagnostic_town_all_door_routes,config.diagnostic_kunlun_door_routes,config.diagnostic_kunlun_parent_routes});
                                    if(door_plan) {
                                        if(door_plan->area!=move.area || !((move.area==2 && move.scene==4 && door_plan->scene==15) ||
                                                             (move.area==2 && move.scene==15 && door_plan->scene==4) ||
                                                             (((move.area==2 && config.diagnostic_town_all_door_routes) ||
                                                               (move.area==4 && config.diagnostic_kunlun_door_routes)) &&
                                                              recovered_movement->registered_door_pair(static_cast<std::uint16_t>(move.area),static_cast<std::uint16_t>(move.scene),static_cast<std::uint16_t>(door_plan->scene))) ||
                                                             (move.area==2 && config.diagnostic_town_island_routes &&
                                                              ((move.scene==4 && door_plan->scene==0) ||
                                                               (move.scene==0 && door_plan->scene==4))) ||
                                                             (move.area==4 && config.diagnostic_kunlun_parent_routes &&
                                                              recovered_movement->registered_parent_pair(4,static_cast<std::uint16_t>(move.scene),static_cast<std::uint16_t>(door_plan->scene)))) ||
                                           !recovered_movement->qualifies_transfer_destination(
                                               static_cast<std::uint16_t>(door_plan->area),
                                               static_cast<std::uint16_t>(door_plan->scene),
                                               static_cast<std::uint16_t>(door_plan->x),
                                               static_cast<std::uint16_t>(door_plan->y)))
                                            throw std::runtime_error("Door proposal outside registered scene pair");
                                    }
                                });
                                if(config.diagnostic_town_player_visibility)
                                    publish_visibility_movement(session,moved);
                                if(door_plan) {
                                    // The live client may queue another path step before its
                                    // five-second tick. Keep the committed step ACK first, then
                                    // transfer immediately so no old-scene move is authorized.
                                    std::vector<std::uint8_t> transfer;
                                    const auto destination_x=static_cast<std::uint16_t>(door_plan->x);
                                    const auto destination_y=static_cast<std::uint16_t>(door_plan->y);
                                    if(((moved.after.area==2 && config.diagnostic_town_all_door_routes) ||
                                        (moved.after.area==4 && config.diagnostic_kunlun_door_routes)) && recovered_movement->registered_door_pair(
                                           moved.after.area,moved.after.scene,static_cast<std::uint16_t>(door_plan->scene)))
                                        transfer=recovered_movement->begin_registered_door_transfer(session.id(),session.account_id,
                                            session.character_id,moved.after,static_cast<std::uint16_t>(door_plan->scene),destination_x,destination_y);
                                    else if(moved.after.area==4 && config.diagnostic_kunlun_parent_routes)
                                        transfer=recovered_movement->begin_registered_parent_transfer(session.id(),session.account_id,
                                            session.character_id,moved.after,static_cast<std::uint16_t>(door_plan->scene),destination_x,destination_y);
                                    else if(door_plan->scene==15)
                                        transfer=recovered_movement->begin_indoor_transfer(session.id(),session.account_id,
                                            session.character_id,moved.after,destination_x,destination_y);
                                    else if(door_plan->scene==0)
                                        transfer=recovered_movement->begin_island_transfer(session.id(),session.account_id,
                                            session.character_id,moved.after,destination_x,destination_y);
                                    else if(moved.after.scene==0)
                                        transfer=recovered_movement->begin_island_return(session.id(),session.account_id,
                                            session.character_id,moved.after,destination_x,destination_y);
                                    else
                                        transfer=recovered_movement->begin_outdoor_return(session.id(),session.account_id,
                                            session.character_id,moved.after,destination_x,destination_y);
                                    if(config.diagnostic_town_player_visibility) {
                                        const auto destination=database.recovered_characters().load_position(
                                            session.account_id,session.character_id);
                                        if(!destination || destination->area!=door_plan->area || destination->scene!=door_plan->scene ||
                                           destination->x!=door_plan->x || destination->y!=door_plan->y)
                                            throw std::runtime_error("Town visibility transfer location missing");
                                        const auto source=player_visibility.snapshot(session.id());
                                        if(source) {
                                            pending_visibility.insert_or_assign(session.id(),visibility_at(*source,*destination));
                                            deliver_visibility(player_visibility.leave(session.id()));
                                            visibility_sessions.erase(session.id());
                                        } else if(pending_visibility.contains(session.id())) {
                                            pending_visibility.insert_or_assign(session.id(),visibility_at(
                                                pending_visibility.at(session.id()),*destination));
                                        } else throw std::runtime_error("Town visibility transfer presence missing");
                                    }
                                    diagnostic_town_scene_pending.insert(session.id());
                                    if(moved.after.scene==0 && ((moved.after.area==2 && door_plan->scene==4) ||
                                       (moved.after.area==4 && door_plan->scene==3)))
                                        diagnostic_island_return_pending.insert(session.id());
                                    moved.reply.insert(moved.reply.end(),transfer.begin(),transfer.end());
                                    spdlog::warn("DIAGNOSTIC_DOOR_COMMITTED session_id={} source_scene={} destination_scene={} custom_test_not_native",
                                        session.id(),moved.after.scene,door_plan->scene);
                                }
                                return std::move(moved.reply);
                            }
                            if(config.diagnostic_battle_after_movement) {
                                auto& ready=diagnostic_movement_ready.at(session.id());
                                auto committed=recovered_movement->move_committed(session.id(),session.account_id,session.character_id,requests);
                                // CUSTOM-0014: one diagnostic encounter after committed displacement.
                                // ACK is queued first; transition waits for the next accepted world tick.
                                if(committed.displaced_steps) ready=true;
                                return std::move(committed.reply);
                            }
                            if(config.diagnostic_town_player_visibility) {
                                auto committed=recovered_movement->move_committed(
                                    session.id(),session.account_id,session.character_id,requests);
                                publish_visibility_movement(session,committed);
                                return std::move(committed.reply);
                            }
                            return recovered_movement->move(session.id(),session.account_id,session.character_id,requests);
                        },[&](Session& session,std::span<const RecoveredWorldRecords::Record> records)
                            ->std::optional<std::vector<std::uint8_t>> {
                            if(!diagnostic_combat)return std::nullopt;
                            std::optional<std::vector<std::uint8_t>> reply;
                            const auto* lab_action=records.size()==1 ? std::get_if<RecoveredBattleCommand::BasicAttackRequest>(&records.front()) : nullptr;
                            if(native_records_lab && lab_action && lab_action->actor_position==0 && lab_action->side_flag==0 &&
                               lab_action->target_masks==std::array<std::uint16_t,2>{0,1} &&
                               diagnostic_combat->inspect(session.id()).revision==1) {
                                // Synthetic trusted effects, after the real client attack command.
                                RecoveredBattleDelta::Bytes hp{0x83,13,0};
                                hp[7]=1;hp[9]=0xe2;hp[10]=0xff;hp[11]=1;hp[14]=28;
                                RecoveredBattleDelta::Bytes mp{0x83,13,0};
                                mp[5]=1;mp[9]=0xf6;mp[10]=0xff;mp[11]=1;mp[13]=9;mp[14]=28;
                                const std::array deltas{*RecoveredBattleDelta::parse(hp),*RecoveredBattleDelta::parse(mp)};
                                reply=diagnostic_combat->apply_native_deltas(session,1,deltas,
                                    [](const BattleSnapshot&,auto entries) {
                                        const auto prime=diagnostic_battle_basic_animation(0,14,0,0,true);
                                        std::vector<std::uint8_t> logical(prime.begin(),prime.end());
                                        for(const auto& entry:entries) {
                                            const auto raw=RecoveredBattleDelta::encode(entry);
                                            logical.insert(logical.end(),raw.begin(),raw.end());
                                        }
                                        const auto close=diagnostic_battle_basic_animation(14,0,0,1,true);
                                        logical.insert(logical.end(),close.begin(),close.end());
                                        return RecoveredWorldFrame::encode(logical);
                                    });
                                spdlog::info("ISOLATED_NATIVE_DELTA_SENT enemy_hp={} player_mp={} no_followup86_or88_snapshot",
                                    diagnostic_combat->inspect(session.id()).actors[14]->hp,
                                    diagnostic_combat->inspect(session.id()).actors[0]->mp);
                            }else reply=diagnostic_combat->handle(session,records);
                            return reply;
                        },[&](Session& session,const RecoveredTargetItemRequest::Request& request)
                            ->std::optional<std::vector<std::uint8_t>> {
                            if(!config.diagnostic_world_supply || !diagnostic_world_resources_sent.contains(session.id()) ||
                               !session.character_id || session.character_id>0x3fff || request.raw_slot>=30)
                                return std::nullopt;
                            if(config.diagnostic_battle_transition &&
                               (!diagnostic_vitals_sent.contains(session.id()) || diagnostic_rounds_granted.contains(session.id())))
                                return std::nullopt;
                            const auto slot=supply_repository.load_inventory_slot(
                                session.account_id,session.character_id,request.raw_slot);
                            const auto resources=supply_repository.load_resources(session.account_id,session.character_id);
                            if(!slot || !resources) return std::nullopt;
                            // Imported current-client declarations widen this isolated
                            // C2S26 route; consumption and cap stay CUSTOM-0016.
                            // An absent import preserves the prior two-item fixture.
                            const auto policy=qualified_supply_policy(
                                request.client_item_id,static_cast<std::uint16_t>(session.character_id));
                            if(!policy) return std::nullopt;
                            return diagnostic_supply.use(session.account_id,session.character_id,
                                RecoveredTargetItemRequest::encode(request),*policy,*slot,*resources).wire;
                        },RecoveredWorldService::Quest{},
                        [&](Session& session,const RecoveredSelectionItemRequest::Request& request)
                            ->std::optional<std::vector<std::uint8_t>> {
                            if(!owned_player_and_companions_projected.contains(session.id()) ||
                               diagnostic_town_scene_pending.contains(session.id()) ||
                               !recovered_movement->current_location(session.id(),session.account_id,session.character_id))
                                return std::nullopt;
                            auto reply=owned_companions.select_pet2(session.account_id,session.character_id,request);
                            if(reply) spdlog::info("OWNED_PET2_SELECTION_COMMITTED session_id={} character_id={} source={} key={} CUSTOM-0039",
                                session.id(),session.character_id,request.raw_slot,request.client_item_id);
                            return reply;
                        },
                        RecoveredWorldService::Teleport{},
                        [&](Session& session,const RecoveredInventoryMoveRequest::Request& request)
                            ->std::optional<std::vector<std::uint8_t>> {
                            if(RecoveredOwnedPetReserveMove::handles(request)) {
                                const auto empty=[](){return std::optional<std::vector<std::uint8_t>>(std::vector<std::uint8_t>{});};
                                if(!owned_player_and_companions_projected.contains(session.id()) ||
                                   diagnostic_town_scene_pending.contains(session.id()) ||
                                   diagnostic_island_return_pending.contains(session.id()) ||
                                   !recovered_movement->current_location(session.id(),session.account_id,session.character_id))return empty();
                                auto reply=RecoveredOwnedPetReserveMove::move(database.companions(),session.account_id,session.character_id,request);
                                if(!reply)return empty();
                                spdlog::info("OWNED_PET_RESERVE_MOVE session_id={} character_id={} source={} destination={} changed={} CUSTOM-0039",
                                    session.id(),session.character_id,request.source_slot,request.destination_slot,!reply->empty());
                                return reply;
                            }
                            if((!config.diagnostic_town_quest_progress && !config.diagnostic_world_supply && !config.owned_map_views_enabled) ||
                               !owned_bag_projected.contains(session.id()) ||
                               diagnostic_town_scene_pending.contains(session.id()) ||
                               !recovered_movement->current_location(session.id(),session.account_id,session.character_id))
                                return std::nullopt;
                            // Native bag has 30 cells; equipment needs a separate owned rule.
                            // There is no optimistic client swap, so unsupported cells can
                            // leave the connection and current authoritative inventory intact.
                            if(request.source_slot>=30 || request.destination_slot>=30)
                                return std::vector<std::uint8_t>{};
                            // Legacy saves with an unfinished battle defer new empty-cell
                            // allocation at login. Retry after that battle has settled.
                            if(config.diagnostic_town_quest_progress)
                                supply_repository.provision_owned_bag(session.account_id,session.character_id);
                            const auto source=supply_repository.load_inventory_slot(
                                session.account_id,session.character_id,request.source_slot);
                            const auto destination=supply_repository.load_inventory_slot(
                                session.account_id,session.character_id,request.destination_slot);
                            if(!source || !destination || !bag_slot_eligible(*source) || !bag_slot_eligible(*destination))
                                return std::vector<std::uint8_t>{};
                            // The existing introductory reward transaction owns cell 0
                            // until completion. Do not let a new drag strand that grant.
                            if(config.diagnostic_town_quest_progress && request.destination_slot==0 && source->count) {
                                const auto progress=supply_repository.load_town_guide_progress(session.account_id,session.character_id);
                                if(!progress || progress->stage<3)
                                    return bag_move_projection(request,{*source,*destination});
                            }
                            // Empty-source and same-cell drags only reproject the saved state.
                            if(!source->count || request.source_slot==request.destination_slot)
                                return bag_move_projection(request,{*source,*destination});
                            auto result=inventory_moves.move(session.account_id,session.character_id,
                                request,*source,*destination);
                            spdlog::info("OWNED_BAG_MOVE_COMMITTED session_id={} character_id={} source={} destination={} source_revision={} destination_revision={} CUSTOM-0037",
                                session.id(),session.character_id,request.source_slot,request.destination_slot,
                                result.commit.source.revision,result.commit.destination.revision);
                            return std::move(result.wire);
                        },
                        [&](Session& session,const RecoveredDeitySelection::Request& request)
                            ->std::optional<std::vector<std::uint8_t>> {
                            if(!owned_player_and_companions_projected.contains(session.id()) ||
                               diagnostic_town_scene_pending.contains(session.id()) ||
                               !recovered_movement->current_location(session.id(),session.account_id,session.character_id))
                                return std::nullopt;
                            auto reply=owned_companions.select_deity(session.account_id,session.character_id,request);
                            if(reply) spdlog::info("OWNED_DEITY_SELECTION_COMMITTED session_id={} character_id={} key={} CUSTOM-0039",
                                session.id(),session.character_id,request.key);
                            return reply;
                        });
                        guild_ordered_world_records=[&](Session& session,std::span<const RecoveredWorldRecords::Record> records) {
                            observe_companion_restoration_write(session);
                            if(config.owned_pk_invitation_enabled){
                                pk_invitations.expire(OwnedPkInvitationService::Clock::now());
                                if(OwnedPkInvitationService::handles(records)){
                                    const auto request=OwnedPkInvitationService::request(records);
                                    if(!request)return std::optional<std::vector<std::uint8_t>>{std::vector<std::uint8_t>{}};
                                    const auto outcome=pk_invitations.handle(session.id(),*request,OwnedPkInvitationService::Clock::now());
                                    spdlog::info("OWNED_PK_INVITATION_SOURCE session_id={} outcome={} shared_room_required CUSTOM-0086",session.id(),static_cast<int>(outcome));
                                    return std::optional<std::vector<std::uint8_t>>{std::vector<std::uint8_t>{}};
                                }
                                // New invitation leases retire before any potential
                                // topology change; existing movement/teleport
                                // handlers and frozen feature behavior stay intact.
                                if(std::any_of(records.begin(),records.end(),[](const auto&r){
                                    return std::holds_alternative<RecoveredMovement::Request>(r)||
                                        std::holds_alternative<RecoveredTeleport::Selection>(r)||
                                        std::holds_alternative<RecoveredWorldRecords::ContextNotification>(r);
                                }))pk_invitations.invalidate(session.id());
                            }
                            std::optional<RecoveredBankItems::Request> beast_bank_wire;
                            std::optional<RecoveredPosition> beast_bank_position;
                            if(beast_bank_repository){
                                std::size_t count=0;bool whole=true;
                                for(const auto& record:records){
                                    if(const auto* request=std::get_if<RecoveredBankItems::Request>(&record)){beast_bank_wire=*request;++count;}
                                    else if(!std::holds_alternative<RecoveredWorldRecords::Tick>(record)&&!std::holds_alternative<RecoveredChat::Request>(record))whole=false;
                                }
                                if(count){
                                    if(count!=1||!whole){
                                        auto refused=bank_items_handle(session.id(),{},std::chrono::steady_clock::now());
                                        for(auto& batch:refused.batches)session.send_world_records(std::move(batch));
                                        native_banks.disconnect(session.id());
                                        return std::optional<std::vector<std::uint8_t>>(std::vector<std::uint8_t>{});
                                    }
                                    beast_bank_position=recovered_movement->current_location(session.id(),session.account_id,session.character_id);
                                    if(!beast_bank_position||!session.recovered_world_ready()||!owned_beasts_projected.contains(session.id())||trade_active(session.id())||
                                       diagnostic_town_scene_pending.contains(session.id())||diagnostic_island_return_pending.contains(session.id()))
                                        return std::optional<std::vector<std::uint8_t>>(std::vector<std::uint8_t>{});
                                }
                            }
                            std::optional<OwnedBeastDiscardService::Prepared> beast_discard_prepared;
                            std::optional<RecoveredPosition> beast_discard_position;
                            if(beast_discard&&session.account_id&&session.character_id){
                                bool touches_beast=false;
                                for(const auto& record:records)if(const auto* use=std::get_if<RecoveredInventoryDiscard::Request>(&record)){
                                    if(NativeBeastSourceCatalog::lookup(use->item))touches_beast=true;
                                    if(use->slot<50){const auto scalar=supply_repository.load_inventory_slot(session.account_id,session.character_id,use->slot);
                                        if(scalar&&scalar->count&&NativeBeastSourceCatalog::lookup(scalar->item_id))touches_beast=true;}
                                }
                                if(touches_beast){
                                    const auto empty=[](){return std::optional<std::vector<std::uint8_t>>(std::vector<std::uint8_t>{});};
                                    const auto use=OwnedBeastDiscardService::request(records);
                                    if(!use||!session.recovered_world_ready()||(session.state()!=SessionState::CharacterSelected&&session.state()!=SessionState::InWorld)||
                                       !owned_beasts_projected.contains(session.id())||trade_active(session.id())||
                                       diagnostic_town_scene_pending.contains(session.id())||diagnostic_island_return_pending.contains(session.id()))return empty();
                                    beast_discard_position=recovered_movement->current_location(session.id(),session.account_id,session.character_id);
                                    if(!beast_discard_position)return empty();
                                    try{
                                        if(supply_repository.owned_pending_battle(session.account_id,session.character_id))return empty();
                                        if(config.diagnostic_town_quest_progress&&use->slot==0){
                                            const auto progress=supply_repository.load_town_guide_progress(session.account_id,session.character_id);
                                            if(!progress||progress->stage<3)return empty();
                                        }
                                        beast_discard_prepared=beast_discard->capture(session.account_id,session.character_id,*use);
                                        if(!beast_discard_prepared){
                                            const auto live=recovered_movement->current_location(session.id(),session.account_id,session.character_id);
                                            if(!live||*live!=*beast_discard_position)return empty();
                                            return std::optional<std::vector<std::uint8_t>>(beast_bag_repository->refresh_source(session.account_id,session.character_id,use->slot));
                                        }
                                    }catch(const std::exception& error){spdlog::warn("OWNED_BEAST_DISCARD_CAPTURE_DENIED session_id={} reason={}",session.id(),error.what());return empty();}
                                }
                            }
                            std::optional<SqliteBeastBagRepository::Snapshot> beast_equipment_snapshot;
                            std::optional<RecoveredSelectionItemRequest::Request> beast_equipment_use;
                            std::optional<RecoveredPosition> beast_equipment_position;
                            if(beast_equipment&&OwnedBeastEquipmentService::handles(records)){
                                const auto empty=[](){return std::optional<std::vector<std::uint8_t>>(std::vector<std::uint8_t>{});};
                                beast_equipment_use=OwnedBeastEquipmentService::request(records);
                                if(!beast_equipment_use||!session.account_id||!session.character_id||!session.recovered_world_ready()||
                                   (session.state()!=SessionState::CharacterSelected&&session.state()!=SessionState::InWorld)||
                                   !owned_beasts_projected.contains(session.id())||trade_active(session.id())||
                                   diagnostic_town_scene_pending.contains(session.id())||diagnostic_island_return_pending.contains(session.id()))return empty();
                                beast_equipment_position=recovered_movement->current_location(session.id(),session.account_id,session.character_id);if(!beast_equipment_position)return empty();
                                try{
                                    if(supply_repository.owned_pending_battle(session.account_id,session.character_id))return empty();
                                    beast_equipment_snapshot=beast_equipment->capture(session.account_id,session.character_id,*beast_equipment_use);
                                    if(!beast_equipment_snapshot)return empty();
                                }catch(const std::exception& error){spdlog::warn("OWNED_BEAST_EQUIPMENT_CAPTURE_DENIED session_id={} reason={}",session.id(),error.what());return empty();}
                            }
                            std::optional<OwnedBeastExplorationService::Operation> beast_view_operation;
                            std::optional<SqliteBeastSnapshotRepository::Selected> beast_view_selected;
                            std::optional<RecoveredPosition> beast_view_position;
                            if(config.owned_beast_panel_enabled&&OwnedBeastExplorationService::handles(records)){
                                const auto empty=[](){return std::optional<std::vector<std::uint8_t>>(std::vector<std::uint8_t>{});};
                                beast_view_operation=OwnedBeastExplorationService::request(records);
                                if(!beast_view_operation||!session.account_id||!session.character_id)return empty();
                                if(std::holds_alternative<RecoveredBeastPanel::Request>(*beast_view_operation)){
                                    if(!session.recovered_world_ready()||(session.state()!=SessionState::CharacterSelected&&session.state()!=SessionState::InWorld)||
                                       !owned_beasts_projected.contains(session.id())||trade_active(session.id())||diagnostic_town_scene_pending.contains(session.id())||diagnostic_island_return_pending.contains(session.id()))return empty();
                                    beast_view_position=recovered_movement->current_location(session.id(),session.account_id,session.character_id);if(!beast_view_position)return empty();
                                    try{
                                        if(supply_repository.owned_pending_battle(session.account_id,session.character_id))return empty();
                                        beast_view_selected=database.beast_snapshots().load_selected(session.account_id,session.character_id);if(!beast_view_selected)return empty();
                                    }catch(const DatabaseError& error){spdlog::warn("OWNED_BEAST_EXPLORATION_CAPTURE_DENIED session_id={} reason={}",session.id(),error.what());return empty();}
                                }
                            }
                            std::optional<SqliteBeastBagRepository::Snapshot> beast_move_snapshot;
                            std::optional<RecoveredPosition> beast_move_position;
                            if(beast_bag_repository&&session.account_id&&session.character_id){
                                bool touches_beast=false;
                                for(const auto& record:records)if(const auto* move=std::get_if<RecoveredInventoryMoveRequest::Request>(&record)){
                                    for(const auto slot:{move->source_slot,move->destination_slot})if(slot<30){
                                        const auto row=supply_repository.load_inventory_slot(session.account_id,session.character_id,slot);
                                        if(row&&row->count&&NativeBeastSourceCatalog::lookup(row->item_id))touches_beast=true;
                                    }
                                }
                                if(touches_beast){
                                    const auto empty=[](){return std::optional<std::vector<std::uint8_t>>(std::vector<std::uint8_t>{});};
                                    const auto use=OwnedBeastBagService::request(records);
                                    if(!use||!session.recovered_world_ready()||
                                       (session.state()!=SessionState::CharacterSelected&&session.state()!=SessionState::InWorld)||
                                       !owned_beasts_projected.contains(session.id())||trade_active(session.id())||
                                       diagnostic_town_scene_pending.contains(session.id())||diagnostic_island_return_pending.contains(session.id())||
                                       !recovered_movement->current_location(session.id(),session.account_id,session.character_id))return empty();
                                    beast_move_position=recovered_movement->current_location(session.id(),session.account_id,session.character_id);
                                    try{beast_move_snapshot=beast_bag_repository->capture(session.account_id,session.character_id,*use);}
                                    catch(const DatabaseError& error){spdlog::warn("OWNED_BEAST_MOVE_CAPTURE_DENIED session_id={} reason={}",session.id(),error.what());return empty();}
                                }
                            }
                            // CUSTOM-0085 whole-frame admission before any guild,
                            // bank, trade or other prefix callback can mutate state.
                            if(config.owned_beast_panel_enabled&&OwnedBeastPanelService::handles(records)&&
                               !OwnedBeastPanelService::request(records))
                                return std::optional<std::vector<std::uint8_t>>(std::vector<std::uint8_t>{});
                            if(guild53_routes && guild53_routes->handles(session.id(),records))return guild53_routes->handle(session.id(),records,[&](auto prefix){return guild_ordered_world_records(session,prefix);});
                            if(guild_succession) {
                                // Retain existing modal/actor policy before capturing ANY owned write.
                                // Frozen channel dispatch is untouched; it may retire CUSTOM authority.
                                const auto notification=[](const auto& record){return
                                    std::holds_alternative<RecoveredWorldRecords::Tick>(record) ||
                                    std::holds_alternative<RecoveredWorldRecords::ClientOpaque74>(record) ||
                                    std::holds_alternative<RecoveredWorldRecords::ClientControl1F>(record) ||
                                    std::holds_alternative<RecoveredWorldRecords::ClientControl6D>(record) ||
                                    std::holds_alternative<RecoveredWorldRecords::ClientOptionsNotification>(record) ||
                                    std::holds_alternative<RecoveredWorldRecords::ContextNotification>(record) ||
                                    std::holds_alternative<RecoveredWorldRecords::TimerNotification>(record) ||
                                    std::holds_alternative<RecoveredWorldRecords::ClientDiagnostic>(record) ||
                                    std::holds_alternative<RecoveredGuildRoster::PanelReady>(record);};
                                if(std::any_of(records.begin(),records.end(),[&](const auto& record){return !notification(record) &&
                                    !std::holds_alternative<RecoveredGuildLeadership::Request>(record) && !std::holds_alternative<RecoveredGuildLeave::Request>(record) &&
                                    !std::holds_alternative<RecoveredGuildDisband75::Request>(record) && !std::holds_alternative<RecoveredGuildAnnouncement::Request>(record) &&
                                    !std::holds_alternative<RecoveredChat::Request>(record) && !std::holds_alternative<RecoveredPartyChat::Request>(record) &&
                                    !std::holds_alternative<RecoveredPrivateChat::Request>(record) && !std::holds_alternative<RecoveredGuildChat::Request>(record);}))guild_succession->revoke(session.id());
                                if(guild_membership52 && std::any_of(records.begin(),records.end(),[&](const auto& record){return !notification(record) && !std::holds_alternative<RecoveredGuildMembership::Request>(record);})){
                                    guild_membership52->invalidate(session.id());guild_interactions52.erase(session.id());
                                }
                                if(!OwnedGuildAnnouncementBatch::save_only(records))if(const auto old=guild_succession->panel().cached(session.id()))guild_succession->notices().invalidate_exact_publication(old->previous);
                            }
                            if(guild_succession && (guild_succession->context(session.id()) || guild_succession->panel().cached(session.id()) || player_guild(session) ||
                                std::any_of(records.begin(),records.end(),[](const auto& r){return std::holds_alternative<RecoveredGuildMembership::Request>(r);}))) {
                                using Adapter=OwnedGuildSuccessionApplicationDraft;using Indexed=Adapter::Runtime::Indexed;
                                std::vector<Indexed> requests,cancel_requests,conversation_requests;
                                std::vector<std::size_t> indices;
                                for(std::size_t i=0;i<records.size();++i){
                                    if(const auto* r=std::get_if<RecoveredGuildLeadership::Request>(&records[i])){requests.push_back({i,{static_cast<std::uint8_t>(r->action),r->slot}});indices.push_back(i);}
                                    else if(const auto* r=std::get_if<RecoveredGuildLeave::Request>(&records[i])){requests.push_back({i,{0x73,r->slot}});cancel_requests.push_back({i,{0x73,r->slot}});indices.push_back(i);}
                                    else if(const auto* r=std::get_if<RecoveredGuildDisband75::Request>(&records[i])){requests.push_back({i,{0x75,r->slot}});indices.push_back(i);}
                                    else if(const auto* request=std::get_if<RecoveredGuildMembership::Request>(&records[i])){const auto logical=RecoveredGuildMembership::encode_request(*request);if(!logical)return std::optional<std::vector<std::uint8_t>>{};conversation_requests.push_back({i,{logical->begin(),logical->end()}});indices.push_back(i);}
                                    else if(std::holds_alternative<RecoveredGuildAnnouncement::Request>(records[i]))indices.push_back(i);
                                }
                                if(!indices.empty()) {
                                    const auto now=OwnedGuildMembershipConversation::Clock::now();
                                    const auto captured=guild_succession->capture(session.id(),requests);
                                    const auto cancellation=guild_succession->capture_cancel(session.id(),cancel_requests,now);
                                    const auto notice=guild_succession->capture_notice(session.id(),now);
                                    const auto conversations=guild_conversation52->capture_before_any_prefix(session.id(),conversation_requests,now);
                                    const auto previous_suppressed=announcement_write_publication_suppressed;
                                    announcement_write_publication_suppressed=true;
                                    struct SuppressReset{bool& value;bool previous;~SuppressReset(){value=previous;}} reset{announcement_write_publication_suppressed,previous_suppressed};
                                    std::size_t begin=0;
                                    const auto prefix=[&](std::size_t end){if(end==begin)return true;const auto result=guild_ordered_world_records(session,records.subspan(begin,end-begin));if(!result)return false;const auto replies=OwnedGuildPanelService::prefix_replies(*result);if(!replies)return false;for(const auto& reply:*replies)session.send_world_records(reply);return true;};
                                    std::set<std::uint64_t> affected;
                                    if(captured.original)for(const auto& row:captured.original->state.rows)affected.insert(row.character_id);
                                    for(const auto& conversation:conversations.actions)if(conversation.plan)for(const auto& [id,resource]:conversation.plan->audience.resources)affected.insert(id);
                                    if(const auto context=guild_succession->context(session.id()))try{const auto state=database.guild_succession52(config.owned_guild_succession_enabled).effective_snapshot(*context);for(const auto& row:state.roster)affected.insert(row.character_id);for(const auto& app:database.guild_succession52(config.owned_guild_succession_enabled).applications(*context))affected.insert(app.applicant.character_id);}catch(...){guild_succession->revoke(session.id());}
                                    bool committed=false,denied_notice=false;
                                    struct Effective52Reconcile {std::function<void()> complete;~Effective52Reconcile()noexcept{try{complete();}catch(...){}}};
                                    Effective52Reconcile reconcile{[&]{
                                        guild_succession->revoke(session.id());
                                        if(committed)for(const auto& [id,weak]:native_chat_sessions)if(const auto peer=weak.lock();peer && (affected.contains(peer->character_id) || id==session.id())){
                                            guild_succession->revoke(id);sync_guild_name(*peer);guild_succession->sync(id,false,true);
                                        }
                                        if(!committed && denied_notice)guild_succession->echo_notice(session.id());
                                    }};
                                    for(const auto index:indices){
                                        if(!prefix(index)){guild_succession->revoke(session.id());return std::optional<std::vector<std::uint8_t>>{};}
                                        bool accepted=false;
                                        std::optional<OwnedGuildSuccessionSemanticReceiptDraft> semantic;
                                        const auto pending=std::find_if(cancellation.actions.begin(),cancellation.actions.end(),[&](const auto& item){return item.index==index;});
                                        if(pending!=cancellation.actions.end() && pending->original){if(pending->plan)semantic=OwnedGuildSuccessionSemanticReceiptDraft::base(pending->plan->permit.cache.previous.state,0x73,pending->plan->request.slot,pending->plan->actor,"cancel_pending");accepted=guild_succession->execute_cancel(*pending,OwnedGuildMembershipConversation::Clock::now());}
                                        else if(const auto item=std::find_if(captured.actions.begin(),captured.actions.end(),[&](const auto& item){return item.index==index;});item!=captured.actions.end()){semantic=OwnedGuildSuccessionSemanticReceiptDraft::captured(*item);accepted=guild_succession->execute(*item);}
                                        else if(const auto* request=std::get_if<RecoveredGuildAnnouncement::Request>(&records[index])){if(notice){const auto& state=notice->panel.state;if(!state.rows.empty())semantic=OwnedGuildSuccessionSemanticReceiptDraft::base(state,0x79,0,state.rows.front(),"announcement");accepted=guild_succession->execute_notice(*notice,*request,OwnedGuildMembershipConversation::Clock::now());}denied_notice=denied_notice || !accepted;}
                                        else if(const auto item=std::find_if(conversations.actions.begin(),conversations.actions.end(),[&](const auto& value){return value.index==index;});item!=conversations.actions.end()){
                                            // Immutable original6F plan is the audit source, captured before any prefix.
                                            if(item->plan){const auto& plan=*item->plan;const auto& owner=plan.original.interaction.owner;
                                                semantic=OwnedGuildSuccessionSemanticReceiptDraft{plan.request.operation==RecoveredGuildMembership::Operation::Create?"create":"apply",owner.session,owner.account,owner.character,
                                                    plan.target?plan.target->guild.id:0,plan.target?plan.target->guild.revision:0,plan.original.actor.account_id,plan.original.actor.character_id,
                                                    0x6f,0,static_cast<unsigned>(plan.original.actor.slot),plan.target?plan.target->roster.size():0,plan.applications.size()};
                                            }
                                            const auto result=config.owned_guild_membership_enabled?guild_conversation52->execute(*item,OwnedGuildMembershipConversation::Clock::now()):std::nullopt;
                                            accepted=result.has_value();
                                            if(result){
                                                if(const auto* created=std::get_if<EffectiveGuildAdmissionRepositoryDraft::Created52>(&*result))session.send_world_records(RecoveredTrade::wallet(created->wallet.amount));
                                                const auto result_guild=std::visit([](const auto& value)->std::uint64_t{using T=std::decay_t<decltype(value)>;if constexpr(std::is_same_v<T,EffectiveGuildAdmissionRepositoryDraft::Created52>)return value.leader.guild.id;else return value.target.id;},*result);
                                                spdlog::info("OWNED_GUILD_EFFECTIVE52_CONVERSATION_RESULT session_id={} index={} result_guild_id={} committed=true CUSTOM-0083",session.id(),index,result_guild);
                                            }
                                        }
                                        if(accepted && semantic)spdlog::info("OWNED_GUILD_EFFECTIVE52_SEMANTIC session_id={} index={} actor_account={} actor_character={} opcode={} slot={} kind={} guild_id={} captured_guild_revision={} target_account={} target_character={} target_character_slot={} captured_members={} captured_pending={} committed=true CUSTOM-0083",
                                            semantic->session,index,semantic->account,semantic->character,semantic->opcode,semantic->slot,semantic->kind,semantic->guild,semantic->guild_revision,
                                            semantic->target_account,semantic->target_character,semantic->target_slot,semantic->members,semantic->pending);
                                        committed=committed || accepted;
                                        spdlog::info("OWNED_GUILD_EFFECTIVE52_ACTION session_id={} index={} committed={} CUSTOM-0083",session.id(),index,accepted);
                                        begin=index+1;
                                    }
                                    if(!prefix(records.size())){guild_succession->revoke(session.id());return std::optional<std::vector<std::uint8_t>>{};}
                                    return std::optional<std::vector<std::uint8_t>>{std::vector<std::uint8_t>{}};
                                }
                            }
if(guild_officer_runtime && player_guild(session) &&
   std::any_of(records.begin(),records.end(),[](const auto& r) {
       return std::holds_alternative<RecoveredGuildLeadership::Request>(r) ||
              std::holds_alternative<RecoveredGuildLeave::Request>(r);
   })) {
    std::vector<OwnedGuildOfficerRuntimeDraft::Request> requests;
    for(std::size_t i=0;i<records.size();++i) {
        if(const auto* r=std::get_if<RecoveredGuildLeadership::Request>(&records[i]))
            requests.push_back({i,static_cast<std::uint8_t>(r->action),r->slot});
        else if(const auto* r=std::get_if<RecoveredGuildLeave::Request>(&records[i]))requests.push_back({i,0x73,r->slot});
    }
    const auto captured=guild_officer_runtime->capture(session.id(),requests);
    std::set<std::uint64_t> affected;
    const auto revoke=[&] {
        guild_officer_runtime->invalidate(session.id());
        if(guild_announcements)guild_announcements->invalidate(session.id());
        if(guild_entry)guild_entry->invalidate(session.id());
        if(guild_membership)guild_membership->invalidate(session.id());
    };
    struct OfficerBatchGuard {
        bool& suppressed;bool previous;std::function<void()> revoke;
        ~OfficerBatchGuard(){revoke();suppressed=previous;}
    } guard{announcement_write_publication_suppressed,announcement_write_publication_suppressed,revoke};
    announcement_write_publication_suppressed=true;
    std::size_t begin=0;
    const auto prefix=[&](std::size_t end) {
        if(end==begin)return true;
        const auto reply=guild_ordered_world_records(session,records.subspan(begin,end-begin));
        if(!reply)return false;
        const auto logical=OwnedGuildPanelService::prefix_replies(*reply);if(!logical)return false;
        for(const auto& frame:*logical)session.send_world_records(frame);return true;
    };
    // A later malformed/failed prefix cannot skip reconciliation of an earlier
    // committed mutation. Keep cache debt on unready peers; retry on Tick.
    struct OfficerReconcileGuard {
        std::function<void()> reconcile;
        ~OfficerReconcileGuard(){try{reconcile();}catch(...){}}
    } reconcile_guard{[&] {
        for(const auto& [id,weak]:native_chat_sessions)if(const auto peer=weak.lock();peer && affected.contains(peer->character_id)) {
            sync_guild_name(*peer);sync_guild_roster(*peer);
        }
    }};
    for(const auto& item:captured) {
        if(!prefix(item.request.index))return std::optional<std::vector<std::uint8_t>>{};
        bool preflight=true;
        if(const auto* plan=std::get_if<OwnedGuildOfficerServiceDraft::Plan>(&item.action))
            preflight=guild_officer_world_host->preflight(plan->publication.base.state,plan->world);
        const bool committed=preflight && guild_officer_runtime->execute(item);
        // Preserve the established telemetry for old action kinds routed here.
        // These markers describe the actual typed operation, never a synthetic
        // success. New office changes have their own CUSTOM-0082 marker.
        using OfficerKind=OwnedGuildOfficerRuntimeDraft::Kind;
        if(item.kind==OfficerKind::Approve || item.kind==OfficerKind::Reject) {
            spdlog::info("OWNED_GUILD_LEADER_ACTION session_id={} character_id={} action={} slot={} committed={} CUSTOM-0078",
                session.id(),session.character_id,static_cast<unsigned>(item.request.opcode),item.request.slot,committed);
        }else if(item.kind==OfficerKind::KickMember) {
            const auto* kick_plan=std::get_if<OwnedGuildKickService::ActionPlan>(&item.action);
            spdlog::info("OWNED_GUILD_MEMBER_KICK session_id={} character_id={} slot={} target_character={} committed={} CUSTOM-0080",
                session.id(),session.character_id,item.request.slot,kick_plan?kick_plan->target.character_id:0,committed);
        }else if(item.kind==OfficerKind::MemberLeave) {
            spdlog::info("OWNED_GUILD_SELF_LEAVE session_id={} character_id={} slot={} committed={} player_created={} CUSTOM-0077 CUSTOM-0078",
                session.id(),session.character_id,item.request.slot,committed,true);
        }else if(item.kind==OfficerKind::Appoint || item.kind==OfficerKind::RemoveOffice || item.kind==OfficerKind::OfficerLeave) {
            const auto* officer_plan=std::get_if<OwnedGuildOfficerServiceDraft::Plan>(&item.action);
            spdlog::info("OWNED_GUILD_OFFICER_ACTION session_id={} character_id={} action={} slot={} target_character={} committed={} CUSTOM-0082",
                session.id(),session.character_id,static_cast<unsigned>(item.request.opcode),item.request.slot,
                officer_plan?officer_plan->target.character_id:0,committed);
        }
        if(committed && item.publication) {
            // Complete accepted+pending identities already captured, not reread
            // after selfLeave/deletion. Includes every duplicate live session.
            for(const auto& row:item.publication->base.state.rows)affected.insert(row.identity.character_id);
            for(const auto& [id,weak]:native_chat_sessions)if(const auto peer=weak.lock();peer && affected.contains(peer->character_id)) {
                guild_officer_runtime->invalidate(id);
                if(guild_announcements)guild_announcements->invalidate(id);
                if(guild_membership)guild_membership->invalidate(id);
                if(guild_entry)guild_entry->invalidate(id);
            }
        }
        // Same-batch newly opened prefix permission is also revoked before
        // suffix recursion; stale standalone execute preserves unrelated reopen.
        revoke();begin=item.request.index+1;
    }
    if(!prefix(records.size()))return std::optional<std::vector<std::uint8_t>>{};
    // Defer readonly rebuild until the whole action suffix is drained. Help in
    // suffix is never allowed to leave mutation authority at batch end.
    // reconcile_guard runs on successful AND exceptional/early-return suffix.
    return std::optional<std::vector<std::uint8_t>>{std::vector<std::uint8_t>{}};
}


                            // CUSTOM-0081 MUST precede all old guild observers/branches:
                            // old leader actor_action whitelist does not admit native75.
                            // Every75 captures its original full publication BEFORE any
                            // recursive prefix, including announcement/entry/help routes.
                            if(std::any_of(records.begin(),records.end(),[](const auto& record) {
                                return std::holds_alternative<RecoveredGuildDisband75::Request>(record);
                            })) {
                                // CUSTOM-0081 projection preflight is OUTSIDE SQL proofs.
                                // Frozen native2D/92 readers require readable role/resources;
                                // world readiness alone cannot guarantee a name-cache clear.
                                // Check before capture and again after any recursive prefix.
                                // The paired transaction proof remains world-only and works
                                // after governance/member/application rows are removed.
                                const auto projection_ready=[&](const OwnedGuildLeaderPanelService::State& state) {
                                    try {
                                        const auto ready=[&](const SqliteOwnedGuildMembershipRepository::Identity& identity) {
                                            for(const auto& [id,weak]:native_chat_sessions)if(const auto peer=weak.lock()) {
                                                if(peer->character_id!=identity.character_id)continue;
                                                const auto actor=private_chat_peer(id);
                                                if(peer->account_id!=identity.account_id || !actor || !actor->ready ||
                                                   actor->session!=id || actor->account!=identity.account_id ||
                                                   actor->character!=identity.character_id)return false;
                                            }
                                            return true;
                                        };
                                        for(const auto& member:state.leader.roster)if(!ready(member))return false;
                                        for(const auto& application:state.applications)if(!ready(application.applicant))return false;
                                        return true;
                                    }catch(...){return false;}
                                };
                                std::vector<std::optional<OwnedGuildDisbandService::ActionPlan>> leases(records.size());
                                std::vector<std::set<std::uint64_t>> audiences(records.size());
                                if(guild_disband)for(std::size_t index=0;index<records.size();++index)
                                    if(const auto* action=std::get_if<RecoveredGuildDisband75::Request>(&records[index])) {
                                        leases[index]=guild_disband->prepare_action(session.id(),action->slot);
                                        if(leases[index] && !projection_ready(leases[index]->panel))leases[index].reset();
                                        if(leases[index]) {
                                            // Capture COMPLETE accepted and pending audiences
                                            // before prefixes/SQL; do not reconstruct after retirement.
                                            for(const auto& member:leases[index]->panel.leader.roster)
                                                audiences[index].insert(member.character_id);
                                            for(const auto& application:leases[index]->panel.applications)
                                                audiences[index].insert(application.applicant.character_id);
                                        }
                                    }
                                const auto revoke=[&] {
                                    if(guild_leader_panel)invalidate_owned_panel(session.id());
                                    if(guild_announcements)guild_announcements->invalidate(session.id());
                                    if(guild_entry)guild_entry->invalidate(session.id());
                                    if(guild_membership)guild_membership->invalidate(session.id());
                                };
                                struct DisbandBatchGuard {
                                    bool& suppressed;bool previous;std::function<void()> revoke;
                                    ~DisbandBatchGuard(){revoke();suppressed=previous;}
                                } guard{announcement_write_publication_suppressed,announcement_write_publication_suppressed,revoke};
                                announcement_write_publication_suppressed=true;
                                std::size_t begin=0;
                                const auto prefix=[&](std::size_t end) {
                                    if(end==begin)return true;
                                    const auto reply=guild_ordered_world_records(session,records.subspan(begin,end-begin));
                                    if(!reply)return false;
                                    const auto logical=OwnedGuildPanelService::prefix_replies(*reply);if(!logical)return false;
                                    for(const auto& frame:*logical)session.send_world_records(frame);return true;
                                };
                                for(std::size_t index=0;index<records.size();++index) {
                                    const auto* action=std::get_if<RecoveredGuildDisband75::Request>(&records[index]);
                                    if(!action)continue;
                                    if(!prefix(index))return std::optional<std::vector<std::uint8_t>>{};
                                    const bool committed=guild_disband && leases[index] &&
                                        projection_ready(leases[index]->panel) && guild_disband->execute(*leases[index]);
                                    spdlog::info("OWNED_GUILD_DISBAND session_id={} character_id={} slot={} guild_id={} members={} pending={} committed={} CUSTOM-0081",
                                        session.id(),session.character_id,action->slot,
                                        leases[index]?leases[index]->panel.membership.guild_id:0,
                                        leases[index]?leases[index]->panel.leader.roster.size():0,
                                        leases[index]?leases[index]->panel.applications.size():0,committed);
                                    if(committed) {
                                        const auto& affected=audiences[index];
                                        // First invalidate ALL connected mutation permissions.
                                        // invalidate retains cached rows for qualified native92
                                        // slot cleanup; never forget/drop cache before clear.
                                        for(const auto& [id,weak]:native_chat_sessions)if(const auto peer=weak.lock();
                                            peer && affected.contains(peer->character_id)) {
                                            if(guild_entry)guild_entry->invalidate(id);
                                            if(guild_membership)guild_membership->invalidate(id);
                                            if(guild_announcements)guild_announcements->invalidate(id);
                                            if(guild_leader_panel)invalidate_owned_panel(id);
                                        }
                                        // Existing read-only 2D empty-name and92 clear routes
                                        // reconcile actual cached rows after SQL retirement.
                                        // Pending applicants have no fabricated membership.
                                        for(const auto& [id,weak]:native_chat_sessions)if(const auto peer=weak.lock();
                                            peer && affected.contains(peer->character_id)) {
                                            sync_guild_name(*peer);sync_guild_roster(*peer);
                                        }
                                    }else {
                                        // Qualified readonly projection cannot mint a help lease.
                                        sync_guild_roster(session);
                                        const bool simplified=session.recovered_client_language()==1;
                                        const auto message=LegacyChineseCodec::encode(simplified?
                                            "未能解散洞府，请重新打开洞府名单后再试。所有成员和申请者必须不在战斗中。":
                                            "未能解散洞府，請重新開啟洞府名單後再試。所有成員與申請者必須不在戰鬥中。",simplified);
                                        session.send_world_records(RecoveredChat::display(0x7fffffffu,simplified,message));
                                    }
                                    // EACH success/denial boundary revokes prefix-made
                                    // authority BEFORE suffix71/72/73/79 recursion.
                                    // Scope-exit-only revocation is insufficient.
                                    revoke();
                                    begin=index+1;
                                }
                                if(!prefix(records.size()))return std::optional<std::vector<std::uint8_t>>{};
                                // No guessed dedicated75 ACK or opcode mirror. Successful
                                // state is projected only by existing native2D/92 routes.
                                return std::optional<std::vector<std::uint8_t>>{std::vector<std::uint8_t>{}};
                            }
                            if(guild_announcements) {
                                guild_announcements->observe_world(session.id());
                                if(!OwnedGuildAnnouncementBatch::save_only(records))guild_announcements->invalidate(session.id());
                            }
                            const bool entry_dialog_was_open=guild_entry && guild_entry->pending(session.id());
                            if(guild_entry) {
                                guild_entry->observe_world(session.id(),OwnedGuildEntryService::Clock::now());
                                const bool actor_action=std::any_of(records.begin(),records.end(),[&](const auto& record) {
                                    if(const auto* action=std::get_if<RecoveredQuestAction::Request>(&record))
                                        return !guild_entry->recognizes(session.id(),*action);
                                    return !std::holds_alternative<RecoveredQuestAction::Request>(record) &&
                                        !std::holds_alternative<RecoveredQuestClose::Request>(record) &&
                                        !std::holds_alternative<RecoveredWorldRecords::Tick>(record) &&
                                        !std::holds_alternative<RecoveredWorldRecords::ClientOpaque74>(record) &&
                                        !std::holds_alternative<RecoveredWorldRecords::ClientControl1F>(record) &&
                                        !std::holds_alternative<RecoveredWorldRecords::ClientControl6D>(record) &&
                                        !std::holds_alternative<RecoveredWorldRecords::ClientOptionsNotification>(record) &&
                                        !std::holds_alternative<RecoveredWorldRecords::ContextNotification>(record) &&
                                        !std::holds_alternative<RecoveredWorldRecords::TimerNotification>(record) &&
                                        !std::holds_alternative<RecoveredWorldRecords::ClientDiagnostic>(record) &&
                                        !std::holds_alternative<RecoveredGuildRoster::PanelReady>(record);
                                });
                                if(actor_action)guild_entry->invalidate(session.id());
                            }
                            if(guild_leader_panel) {
                                observe_owned_panel(session.id());
                                // Invalidate before any prefix: a move out and back,
                                // or a coalesced help opener, cannot revive an old slot.
                                const bool actor_action=std::any_of(records.begin(),records.end(),[](const auto& record) {
                                    return !std::holds_alternative<RecoveredGuildLeadership::Request>(record) &&
                                        !std::holds_alternative<RecoveredGuildLeave::Request>(record) &&
                                        !std::holds_alternative<RecoveredWorldRecords::Tick>(record) &&
                                        !std::holds_alternative<RecoveredWorldRecords::ClientOpaque74>(record) &&
                                        !std::holds_alternative<RecoveredWorldRecords::ClientControl1F>(record) &&
                                        !std::holds_alternative<RecoveredWorldRecords::ClientControl6D>(record) &&
                                        !std::holds_alternative<RecoveredWorldRecords::ClientOptionsNotification>(record) &&
                                        !std::holds_alternative<RecoveredWorldRecords::ContextNotification>(record) &&
                                        !std::holds_alternative<RecoveredWorldRecords::TimerNotification>(record) &&
                                        !std::holds_alternative<RecoveredWorldRecords::ClientDiagnostic>(record) &&
                                        !std::holds_alternative<RecoveredGuildRoster::PanelReady>(record) &&
                                        !std::holds_alternative<RecoveredChat::Request>(record) &&
                                        !std::holds_alternative<RecoveredPartyChat::Request>(record) &&
                                        !std::holds_alternative<RecoveredPrivateChat::Request>(record) &&
                                        !std::holds_alternative<RecoveredGuildChat::Request>(record);
                                });
                                if(actor_action)invalidate_owned_panel(session.id());
                            }
                            if(guild_membership) {
                                guild_membership->observe_world(session.id());
                                // CUSTOM candidate admission is modal: any gameplay
                                // request invalidates it BEFORE dispatch, even if a
                                // later move returns to the exact opening coordinate.
                                // Opaque UI74 and readonly native notifications do
                                // not grant authority and may accompany native6F.
                                const bool actor_action=std::any_of(records.begin(),records.end(),[](const auto& record) {
                                    return !std::holds_alternative<RecoveredGuildMembership::Request>(record) &&
                                        !std::holds_alternative<RecoveredWorldRecords::Tick>(record) &&
                                        !std::holds_alternative<RecoveredWorldRecords::ClientOpaque74>(record) &&
                                        !std::holds_alternative<RecoveredWorldRecords::ClientControl1F>(record) &&
                                        !std::holds_alternative<RecoveredWorldRecords::ClientControl6D>(record) &&
                                        !std::holds_alternative<RecoveredWorldRecords::ClientOptionsNotification>(record) &&
                                        !std::holds_alternative<RecoveredWorldRecords::ContextNotification>(record) &&
                                        !std::holds_alternative<RecoveredWorldRecords::TimerNotification>(record) &&
                                        !std::holds_alternative<RecoveredWorldRecords::ClientDiagnostic>(record) &&
                                        !std::holds_alternative<RecoveredGuildRoster::PanelReady>(record);
                                });
                                if(actor_action)guild_membership->invalidate(session.id());
                            }
                            if(std::any_of(records.begin(),records.end(),[](const auto& record) {
                                return std::holds_alternative<RecoveredGuildAnnouncement::Request>(record);
                            })) {
                                // CUSTOM-0078: freeze exactly one existing publication
                                // before ANY prefix/suffix. Suppression spans recursion,
                                // so coalesced help+79 never mints borrowed permission.
                                const auto now=OwnedGuildMembershipConversation::Clock::now();
                                const auto lease=guild_announcements?guild_announcements->prepare_action(session.id(),now):std::nullopt;
                                const auto revoke=[&] {
                                    if(guild_announcements)guild_announcements->invalidate(session.id());
                                    if(guild_entry)guild_entry->invalidate(session.id());
                                    if(guild_membership)guild_membership->invalidate(session.id());
                                    if(guild_leader_panel)invalidate_owned_panel(session.id());
                                };
                                struct BatchGuard {
                                    bool& suppressed;bool previous;std::function<void()> revoke;
                                    ~BatchGuard(){revoke();suppressed=previous;}
                                } guard{announcement_write_publication_suppressed,announcement_write_publication_suppressed,revoke};
                                announcement_write_publication_suppressed=true;
                                std::size_t begin=0;
                                const auto prefix=[&](std::size_t end) {
                                    if(end==begin)return true;
                                    const auto reply=guild_ordered_world_records(session,records.subspan(begin,end-begin));
                                    if(!reply)return false;
                                    const auto logical=OwnedGuildPanelService::prefix_replies(*reply);
                                    if(!logical)return false;
                                    for(const auto& frame:*logical)session.send_world_records(frame);
                                    return true;
                                };
                                for(std::size_t index=0;index<records.size();++index) {
                                    const auto* request=std::get_if<RecoveredGuildAnnouncement::Request>(&records[index]);
                                    if(!request)continue;
                                    if(!prefix(index))return std::optional<std::vector<std::uint8_t>>{};
                                    //79 is active for the existing guild services too;
                                    // revoke any authority a recursive help prefix made.
                                    if(guild_entry)guild_entry->invalidate(session.id());
                                    if(guild_membership)guild_membership->invalidate(session.id());
                                    if(guild_leader_panel)invalidate_owned_panel(session.id());
                                    const auto saved=guild_announcements && lease?
                                        guild_announcements->execute(*lease,*request,OwnedGuildMembershipConversation::Clock::now()):std::nullopt;
                                    spdlog::info("OWNED_GUILD_ANNOUNCEMENT_SAVE session_id={} character_id={} guild_id={} committed={} revision={} CUSTOM-0078",
                                        session.id(),session.character_id,lease?lease->announcement.guild_id:0,saved.has_value(),
                                        saved && saved->value?saved->value->revision:0);
                                    if(guild_announcements) {
                                        // Reply only to this explicit save attempt. Native28
                                        // already replaced the local cache before server validation.
                                        // Restore authoritative98 even on denial; never mint a lease.
                                        const auto echo=prepare_owned_notice(session.id(),false);
                                        if(echo && (!saved || echo->original.announcement==*saved) && current_owned_notice(*echo)) {
                                            session.send_world_records(echo->logical);
                                            const bool published=published_owned_notice(*echo,OwnedGuildMembershipConversation::Clock::now());
                                            if(!saved) {
                                                const bool simplified=echo->original.panel.next.owner.name_codepage==936;
                                                const auto message=LegacyChineseCodec::encode(simplified?
                                                    "公告未保存，请重新打开公告页面后再试。文字必须能同时以繁、简体编码表示。":
                                                    "公告未儲存，請重新開啟公告頁面後再試。文字必須能同時以繁、簡體編碼表示。",simplified);
                                                session.send_world_records(RecoveredChat::display(0x7fffffffu,simplified,message));
                                            }
                                            if(saved)spdlog::info("OWNED_GUILD_ANNOUNCEMENT_ECHO session_id={} character_id={} guild_id={} revision={} published={} CUSTOM-0078",
                                                session.id(),session.character_id,echo->original.announcement.guild_id,
                                                echo->original.announcement.value?echo->original.announcement.value->revision:0,published);
                                            else spdlog::info("OWNED_GUILD_ANNOUNCEMENT_DENIED_RESTORED session_id={} character_id={} guild_id={} revision={} published={} CUSTOM-0078",
                                                session.id(),session.character_id,echo->original.announcement.guild_id,
                                                echo->original.announcement.value?echo->original.announcement.value->revision:0,published);
                                        }
                                    }
                                    begin=index+1;
                                }
                                if(!prefix(records.size()))return std::optional<std::vector<std::uint8_t>>{};
                                return std::optional<std::vector<std::uint8_t>>{std::vector<std::uint8_t>{}};
                            }
                            if(guild_entry && std::any_of(records.begin(),records.end(),[&](const auto& record) {
                                const auto* action=std::get_if<RecoveredQuestAction::Request>(&record);
                                return (action && guild_entry->recognizes(session.id(),*action)) ||
                                    (entry_dialog_was_open && std::holds_alternative<RecoveredQuestClose::Request>(record));
                            })) {
                                // Freeze choice permission before recursive prefix handling.
                                // Coalesced help/Tick/6F cannot grant missing authority.
                                const bool mixed_mutation=std::any_of(records.begin(),records.end(),[](const auto& record) {
                                    return !std::holds_alternative<RecoveredQuestAction::Request>(record) &&
                                        !std::holds_alternative<RecoveredQuestClose::Request>(record) &&
                                        !std::holds_alternative<RecoveredWorldRecords::Tick>(record) &&
                                        !std::holds_alternative<RecoveredWorldRecords::ClientOpaque74>(record) &&
                                        !std::holds_alternative<RecoveredWorldRecords::ClientControl1F>(record) &&
                                        !std::holds_alternative<RecoveredWorldRecords::ClientControl6D>(record) &&
                                        !std::holds_alternative<RecoveredWorldRecords::ClientOptionsNotification>(record) &&
                                        !std::holds_alternative<RecoveredWorldRecords::ContextNotification>(record) &&
                                        !std::holds_alternative<RecoveredWorldRecords::TimerNotification>(record) &&
                                        !std::holds_alternative<RecoveredWorldRecords::ClientDiagnostic>(record) &&
                                        !std::holds_alternative<RecoveredGuildRoster::PanelReady>(record) &&
                                        !std::holds_alternative<RecoveredChat::Request>(record) &&
                                        !std::holds_alternative<RecoveredPartyChat::Request>(record) &&
                                        !std::holds_alternative<RecoveredPrivateChat::Request>(record) &&
                                        !std::holds_alternative<RecoveredGuildChat::Request>(record);
                                });
                                if(mixed_mutation) {
                                    guild_entry->invalidate(session.id());
                                    spdlog::info("OWNED_GUILD_ENTRY_MIXED_ACTION_DENIED session_id={} CUSTOM-0078",session.id());
                                    return std::optional<std::vector<std::uint8_t>>{std::vector<std::uint8_t>{}};
                                }
                                const auto lease=guild_entry->prepare_choice(session.id(),OwnedGuildEntryService::Clock::now());
                                std::size_t begin=0;
                                const auto prefix=[&](std::size_t end) {
                                    if(end==begin)return true;
                                    const auto reply=guild_ordered_world_records(session,records.subspan(begin,end-begin));
                                    if(!reply)return false;
                                    const auto logical=OwnedGuildPanelService::prefix_replies(*reply);if(!logical)return false;
                                    for(const auto& frame:*logical)session.send_world_records(frame);return true;
                                };
                                for(std::size_t index=0;index<records.size();++index) {
                                    const auto* action=std::get_if<RecoveredQuestAction::Request>(&records[index]);
                                    const bool close=entry_dialog_was_open && std::holds_alternative<RecoveredQuestClose::Request>(records[index]);
                                    const bool choice=action && guild_entry->recognizes(session.id(),*action);
                                    if(!choice && !close)continue;
                                    if(!prefix(index))return std::optional<std::vector<std::uint8_t>>{};
                                    if(close) {guild_entry->invalidate(session.id());guild_membership->invalidate(session.id());if(guild_membership52)guild_membership52->invalidate(session.id());guild_interactions52.erase(session.id());}
                                    else {
                                        const auto selected=lease?guild_entry->consume(*lease,*action,OwnedGuildEntryService::Clock::now()):std::nullopt;
                                        bool opened=false;
                                        if(selected && *selected!=OwnedGuildEntryService::Choice::Exit) {
                                            const auto operation=*selected==OwnedGuildEntryService::Choice::Create?
                                                RecoveredGuildMembership::Operation::Create:RecoveredGuildMembership::Operation::Join;
                                            if(guild_membership52){
                                                // Exact server lease; no selected_actor_hint or client name supplies service identity.
                                                if(!announcement_write_publication_suppressed && lease && config.owned_guild_membership_enabled){
                                                    guild_interactions52.insert_or_assign(session.id(),EffectiveGuildJoinConversationServiceDraft::Interaction{lease->owner,0x087b,1,lease->request});
                                                    const auto now=OwnedGuildMembershipConversation::Clock::now();
                                                    const auto opening=operation==RecoveredGuildMembership::Operation::Create?guild_membership52->prepare_create(session.id(),now):guild_membership52->prepare_join(session.id(),now);
                                                    if(opening){std::weak_ptr<EffectiveGuildJoinConversationServiceDraft> weak=guild_membership52;
                                                        guild_succession->deliver(opening->interaction.owner,{opening->prompt.begin(),opening->prompt.end()},[weak,opening=*opening](bool accepted){if(accepted)if(auto service=weak.lock())if(service->published(opening,OwnedGuildMembershipConversation::Clock::now()))spdlog::info("OWNED_GUILD_EFFECTIVE52_PROMPT_PUBLICATION session_id={} actor_account={} actor_character={} operation={} request={} accepted=true CUSTOM-0083",opening.interaction.owner.session,opening.interaction.owner.account,opening.interaction.owner.character,static_cast<unsigned>(opening.prompt[3]),opening.interaction.interaction_revision);});opened=true;
                                                    }
                                                }
                                            }else{
                                                const auto prompt=guild_membership->open(session.id(),operation,OwnedGuildMembershipConversation::Clock::now(),true);
                                                if(prompt){session.send_world_records(std::vector<std::uint8_t>(prompt->begin(),prompt->end()));opened=true;}
                                            }
                                        }
                                        spdlog::info("OWNED_GUILD_ENTRY_CHOICE session_id={} character_id={} choice={} accepted={} input_opened={} CUSTOM-0078",
                                            session.id(),session.character_id,action->reply_word,selected.has_value(),opened);
                                    }
                                    begin=index+1;
                                }
                                if(!prefix(records.size()))return std::optional<std::vector<std::uint8_t>>{};
                                return std::optional<std::vector<std::uint8_t>>{std::vector<std::uint8_t>{}};
                            }
                            // CUSTOM-0080 native72 ordinary-member removal is
                            // classified ONCE from the existing recipient cache,
                            // separately from frozen pending rejection. Cached
                            // role chooses the action kind, never its authority.
                            std::vector<bool> kick_kind(records.size(),false);
                            if(guild_leader_panel)for(std::size_t index=0;index<records.size();++index)
                                if(const auto* action=std::get_if<RecoveredGuildLeadership::Request>(&records[index]);
                                    action && action->action==RecoveredGuildLeadership::Action::RejectOrRemove)
                                    kick_kind[index]=guild_leader_panel->cached_row_role(session.id(),action->slot)==std::optional<std::uint8_t>{1};
                            if(std::any_of(kick_kind.begin(),kick_kind.end(),[](bool value){return value;})) {
                                std::vector<std::optional<OwnedGuildKickService::ActionPlan>> leases(records.size());
                                if(guild_kick)for(std::size_t index=0;index<records.size();++index)
                                    if(kick_kind[index])leases[index]=guild_kick->prepare_action(session.id(),
                                        std::get<RecoveredGuildLeadership::Request>(records[index]).slot);
                                const auto revoke=[&] {
                                    if(guild_leader_panel)invalidate_owned_panel(session.id());
                                    if(guild_announcements)guild_announcements->invalidate(session.id());
                                    if(guild_entry)guild_entry->invalidate(session.id());
                                    if(guild_membership)guild_membership->invalidate(session.id());
                                };
                                struct KickBatchGuard {
                                    bool& suppressed;bool previous;std::function<void()> revoke;
                                    ~KickBatchGuard(){revoke();suppressed=previous;}
                                } guard{announcement_write_publication_suppressed,announcement_write_publication_suppressed,revoke};
                                announcement_write_publication_suppressed=true;
                                std::size_t begin=0;
                                const auto prefix=[&](std::size_t end) {
                                    if(end==begin)return true;
                                    const auto reply=guild_ordered_world_records(session,records.subspan(begin,end-begin));
                                    if(!reply)return false;
                                    const auto logical=OwnedGuildPanelService::prefix_replies(*reply);if(!logical)return false;
                                    for(const auto& frame:*logical)session.send_world_records(frame);return true;
                                };
                                for(std::size_t index=0;index<records.size();++index) {
                                    if(!kick_kind[index])continue;
                                    if(!prefix(index))return std::optional<std::vector<std::uint8_t>>{};
                                    const auto& action=std::get<RecoveredGuildLeadership::Request>(records[index]);
                                    const bool committed=guild_kick && leases[index] && guild_kick->execute(*leases[index]);
                                    spdlog::info("OWNED_GUILD_MEMBER_KICK session_id={} character_id={} slot={} target_character={} committed={} CUSTOM-0080",
                                        session.id(),session.character_id,action.slot,leases[index]?leases[index]->target.character_id:0,committed);
                                    if(committed) {
                                        std::set<std::uint64_t> affected;
                                        for(const auto& row:leases[index]->panel.rows)affected.insert(row.identity.character_id);
                                        // Clear ALL affected mutation authorities before any
                                        // readonly native projection; SQL chat qualification
                                        // immediately excludes the removed member.
                                        for(const auto& [id,weak]:native_chat_sessions)if(const auto peer=weak.lock();
                                            peer && affected.contains(peer->character_id)) {
                                            if(guild_entry)guild_entry->invalidate(id);
                                            if(guild_membership)guild_membership->invalidate(id);
                                            if(guild_announcements)guild_announcements->invalidate(id);
                                            if(guild_leader_panel)invalidate_owned_panel(id);
                                        }
                                        for(const auto& [id,weak]:native_chat_sessions)if(const auto peer=weak.lock();
                                            peer && affected.contains(peer->character_id)) {
                                            sync_guild_name(*peer);sync_guild_roster(*peer);
                                        }
                                    }else {
                                        sync_guild_roster(session);
                                        const bool simplified=session.recovered_client_language()==1;
                                        const auto message=LegacyChineseCodec::encode(simplified?
                                            "未能移除成员，请重新打开洞府名单后再试。操作双方必须不在战斗中。":
                                            "未能移除成員，請重新開啟洞府名單後再試。操作雙方必須不在戰鬥中。",simplified);
                                        session.send_world_records(RecoveredChat::display(0x7fffffffu,simplified,message));
                                    }
                                    // Revoke prefix-created authority BEFORE any
                                    // suffix recursion, including a denied kick.
                                    // A help+72+71 batch cannot borrow a fresh
                                    // leader publication to approve an applicant.
                                    revoke();
                                    begin=index+1;
                                }
                                if(!prefix(records.size()))return std::optional<std::vector<std::uint8_t>>{};
                                return std::optional<std::vector<std::uint8_t>>{std::vector<std::uint8_t>{}};
                            }
                            if(std::any_of(records.begin(),records.end(),[](const auto& record) {
                                return std::holds_alternative<RecoveredGuildMembership::Request>(record) ||
                                    std::holds_alternative<RecoveredGuildLeadership::Request>(record);
                            })) {
                                // Capture permission before processing any old-route prefix;
                                // a coalesced Tick cannot create permission for an unsolicited6F.
                                const bool had_opening=guild_membership && guild_membership->pending(session.id());
                                // Preserve0077's immutable WHOLE-batch leave lease.
                                // A6F marker must not let an earlier Tick refresh
                                // the authority later used by a73 suffix.
                                const auto batch_leave_lease=guild_panel.prepare_leave(session.id(),{0});
                                const bool batch_player_guild=player_guild(session);
                                const auto player_leave_lease=guild_leader_panel?
                                    guild_leader_panel->prepare_leave(session.id(),0):std::nullopt;
                                std::vector<std::optional<OwnedGuildLeaderPanelService::ActionPlan>> leader_leases(records.size());
                                if(guild_leader_panel)for(std::size_t i=0;i<records.size();++i)
                                    if(const auto* request=std::get_if<RecoveredGuildLeadership::Request>(&records[i]))
                                        leader_leases[i]=guild_leader_panel->prepare_action(session.id(),
                                            request->action==RecoveredGuildLeadership::Action::ApproveOrAppoint?
                                                OwnedGuildLeaderPanelService::Action::Approve:OwnedGuildLeaderPanelService::Action::Reject,
                                            request->slot);
                                std::size_t begin=0;
                                const auto prefix=[&](std::size_t end) {
                                    if(end==begin)return true;
                                    const auto reply=guild_ordered_world_records(session,records.subspan(begin,end-begin));
                                    if(!reply)return false;
                                    const auto logical=OwnedGuildPanelService::prefix_replies(*reply);if(!logical)return false;
                                    for(const auto& frame:*logical)session.send_world_records(frame);return true;
                                };
                                for(std::size_t index=0;index<records.size();++index) {
                                    const auto* request=std::get_if<RecoveredGuildMembership::Request>(&records[index]);
                                    const auto* leave=std::get_if<RecoveredGuildLeave::Request>(&records[index]);
                                    const auto* leadership=std::get_if<RecoveredGuildLeadership::Request>(&records[index]);
                                    if(!request && !leave && !leadership)continue;
                                    if(!prefix(index))return std::optional<std::vector<std::uint8_t>>{};
                                    if(leadership) {
                                        const bool committed=guild_leader_panel && leader_leases[index] &&
                                            guild_leader_panel->execute(*leader_leases[index]);
                                        spdlog::info("OWNED_GUILD_LEADER_ACTION session_id={} character_id={} action={} slot={} committed={} CUSTOM-0078",
                                            session.id(),session.character_id,static_cast<unsigned>(leadership->action),leadership->slot,committed);
                                        if(committed)for(const auto& [id,weak]:native_chat_sessions)if(const auto peer=weak.lock()) {
                                            sync_guild_name(*peer);sync_guild_roster(*peer);
                                        }
                                        begin=index+1;continue;
                                    }
                                    if(leave) {
                                        const bool admitted=session.recovered_world_ready() && session.state()!=SessionState::InBattle &&
                                            owned_player_and_companions_projected.contains(session.id()) &&
                                            !diagnostic_town_scene_pending.contains(session.id()) &&
                                            !diagnostic_island_return_pending.contains(session.id()) &&
                                            recovered_movement->current_location(session.id(),session.account_id,session.character_id).has_value();
                                        const bool committed=admitted && (batch_player_guild?
                                            (guild_leader_panel && player_leave_lease && guild_leader_panel->leave(*player_leave_lease,leave->slot)):
                                            (!player_guild(session) && batch_leave_lease && guild_panel.leave(*batch_leave_lease,*leave)));
                                        spdlog::info("OWNED_GUILD_SELF_LEAVE session_id={} character_id={} slot={} committed={} player_created={} CUSTOM-0077 CUSTOM-0078",
                                            session.id(),session.character_id,leave->slot,committed,batch_player_guild);
                                        if(committed)for(const auto& [id,weak]:native_chat_sessions)if(const auto peer=weak.lock()) {
                                            sync_guild_name(*peer);sync_guild_roster(*peer);
                                        }
                                        begin=index+1;continue;
                                    }
                                    const auto result=had_opening?guild_membership->submit(session.id(),*request,
                                        OwnedGuildMembershipConversation::Clock::now()):std::nullopt;
                                    spdlog::info("OWNED_GUILD_MEMBERSHIP_REQUEST session_id={} character_id={} operation={} context={} accepted={} scope={} CUSTOM-0078",
                                        session.id(),session.character_id,static_cast<unsigned>(request->operation),request->context,result.has_value(),
                                        guild_membership_lab?"disposable_lab":"configured_server");
                                    if(result && std::holds_alternative<SqliteOwnedGuildMembershipRepository::Created>(*result)) {
                                        const auto& created=std::get<SqliteOwnedGuildMembershipRepository::Created>(*result);
                                        session.send_world_records(RecoveredTrade::wallet(created.wallet.amount));
                                        for(const auto& [id,weak]:native_chat_sessions)if(const auto peer=weak.lock()) {
                                            sync_guild_name(*peer);sync_guild_roster(*peer);
                                        }
                                    }
                                    if(result && std::holds_alternative<SqliteOwnedGuildMembershipRepository::Application>(*result))
                                        for(const auto& [id,weak]:native_chat_sessions)if(const auto peer=weak.lock())sync_guild_roster(*peer);
                                    begin=index+1;
                                }
                                if(!prefix(records.size()))return std::optional<std::vector<std::uint8_t>>{};
                                return std::optional<std::vector<std::uint8_t>>{std::vector<std::uint8_t>{}};
                            }
                            if(std::any_of(records.begin(),records.end(),[](const auto& record) {
                                return std::holds_alternative<RecoveredGuildLeave::Request>(record);
                            })) {
                                // CUSTOM-0077: immutable entry lease, before ANY
                                // Tick/B8/help publication. A stale command must
                                // never be authorized by refreshing this batch.
                                const auto leave_lease=guild_panel.prepare_leave(session.id(),{0});
                                const bool batch_player_guild=player_guild(session);
                                const auto player_leave_lease=guild_leader_panel?
                                    guild_leader_panel->prepare_leave(session.id(),0):std::nullopt;
                                std::size_t begin=0;
                                const auto prefix=[&](std::size_t end) {
                                    if(end==begin)return true;
                                    // No73 in this span, hence depth exactly1.
                                    // Existing routes handle it unchanged.
                                    const auto reply=guild_ordered_world_records(session,records.subspan(begin,end-begin));
                                    if(!reply)return false;
                                    auto logical=OwnedGuildPanelService::prefix_replies(*reply);
                                    if(!logical)return false;
                                    for(auto& frame:*logical)session.send_world_records(std::move(frame));
                                    return true;
                                };
                                for(std::size_t index=0;index<records.size();++index) {
                                    const auto* leave=std::get_if<RecoveredGuildLeave::Request>(&records[index]);
                                    if(!leave)continue;
                                    if(!prefix(index))return std::optional<std::vector<std::uint8_t>>{};
                                    const bool admitted=session.recovered_world_ready() && session.state()!=SessionState::InBattle &&
                                        owned_player_and_companions_projected.contains(session.id()) &&
                                        !diagnostic_town_scene_pending.contains(session.id()) &&
                                        !diagnostic_island_return_pending.contains(session.id()) &&
                                        recovered_movement->current_location(session.id(),session.account_id,session.character_id).has_value();
                                    const bool committed=admitted && (batch_player_guild?
                                        (guild_leader_panel && player_leave_lease && guild_leader_panel->leave(*player_leave_lease,leave->slot)):
                                        (!player_guild(session) && leave_lease && guild_panel.leave(*leave_lease,*leave)));
                                    spdlog::info("OWNED_GUILD_SELF_LEAVE session_id={} character_id={} slot={} committed={} player_created={} CUSTOM-0077 CUSTOM-0078",
                                        session.id(),session.character_id,leave->slot,committed,batch_player_guild);
                                    if(committed)for(const auto& [id,weak]:native_chat_sessions)
                                        if(auto peer=weak.lock()) {
                                            sync_guild_name(*peer);sync_guild_roster(*peer);
                                        }
                                    begin=index+1;
                                }
                                if(!prefix(records.size()))return std::optional<std::vector<std::uint8_t>>{};
                                return std::optional<std::vector<std::uint8_t>>{std::vector<std::uint8_t>{}};
                            }
                            sync_guild_name(session);
                            if(std::any_of(records.begin(),records.end(),[](const auto& record) {
                                return std::holds_alternative<RecoveredWorldRecords::Tick>(record) ||
                                    std::holds_alternative<RecoveredGuildRoster::PanelReady>(record);
                            }))sync_guild_roster(session);
                            std::vector<RecoveredWorldRecords::Record> without_guild_notification;
                            if(std::any_of(records.begin(),records.end(),[](const auto& record) {
                                return std::holds_alternative<RecoveredGuildRoster::PanelReady>(record);
                            })) {
                                spdlog::info("OWNED_GUILD_PANEL_NOTIFICATION session_id={} admitted={} CUSTOM-0076 no_state_change no_reply",
                                    session.id(),guild_roster.panel_ready(session.id()));
                                for(const auto& record:records)
                                    if(!std::holds_alternative<RecoveredGuildRoster::PanelReady>(record))
                                        without_guild_notification.push_back(record);
                                if(without_guild_notification.empty())
                                    return std::optional<std::vector<std::uint8_t>>{std::vector<std::uint8_t>{}};
                                records=without_guild_notification;
                            }
                            // CUSTOM-0077: explicitly CUSTOM fixed help-service
                            // entry, not recovered original NPC/cave mapping.
                            // Preserve coalesced records/frozen channels.
                            std::vector<RecoveredWorldRecords::Record> without_guild_help;
                            if(std::any_of(records.begin(),records.end(),[](const auto& record) {
                                const auto* npc=std::get_if<RecoveredNpcInteraction::Request>(&record);
                                return npc && OwnedGuildPanelService::custom_help_entry(*npc);
                            })) {
                                for(const auto& record:records) {
                                    const auto* npc=std::get_if<RecoveredNpcInteraction::Request>(&record);
                                    if(!npc || !OwnedGuildPanelService::custom_help_entry(*npc)) {
                                        without_guild_help.push_back(record);continue;
                                    }
                                    const bool admitted=session.recovered_world_ready() && session.state()!=SessionState::InBattle &&
                                        owned_player_and_companions_projected.contains(session.id()) &&
                                        !diagnostic_town_scene_pending.contains(session.id()) &&
                                        !diagnostic_island_return_pending.contains(session.id()) &&
                                        recovered_movement->current_location(session.id(),session.account_id,session.character_id).has_value();
                                    if(admitted) {
                                        if(guild_succession && guild_succession->context(session.id())){
                                            guild_succession->sync(session.id(),!announcement_write_publication_suppressed && OwnedGuildAnnouncementBatch::opener_only(records));continue;
                                        }
                                        if(player_guild(session)) {
                                            if(!guild_leader_panel)continue;
                                            if(guild_announcements) {
                                                const auto notice=prepare_owned_notice(session.id(),true);
                                                if(notice && current_owned_notice(*notice)) {
                                                    session.send_world_records(notice->logical);
                                                    const auto now=OwnedGuildMembershipConversation::Clock::now();
                                                    const bool published=published_owned_notice(*notice,now);
                                                    if(announcement_write_publication_suppressed || !OwnedGuildAnnouncementBatch::opener_only(records))
                                                        guild_announcements->invalidate(session.id());
                                                    const bool write_authorized=published && guild_announcements->prepare_action(session.id(),now).has_value();
                                                    spdlog::info("OWNED_GUILD_ANNOUNCEMENT_PUBLISHED session_id={} character_id={} guild_id={} revision={} published={} write_authorized={} entry=native_help_CUSTOM CUSTOM-0078",
                                                        session.id(),session.character_id,notice->original.announcement.guild_id,
                                                        notice->original.announcement.value?notice->original.announcement.value->revision:0,published,write_authorized);
                                                    spdlog::info("OWNED_GUILD_LEADER_PANEL_OPEN session_id={} character_id={} members={} pending={} published={} entry=native_help_CUSTOM CUSTOM-0078",
                                                        session.id(),session.character_id,notice->original.panel.next.leader.roster.size(),notice->original.panel.next.applications.size(),published);
                                                    continue;
                                                }
                                                guild_announcements->invalidate(session.id());
                                                spdlog::warn("OWNED_GUILD_ANNOUNCEMENT_READ_DENIED session_id={} character_id={} existing_panel_fallback CUSTOM-0078",session.id(),session.character_id);
                                            }
                                            const auto panel=prepare_owned_panel(session.id(),true);
                                            if(panel && current_owned_panel(*panel)) {
                                                session.send_world_records(panel->logical);
                                                const bool published=published_owned_panel(*panel);
                                                spdlog::info("OWNED_GUILD_LEADER_PANEL_OPEN session_id={} character_id={} members={} pending={} published={} entry=native_help_CUSTOM CUSTOM-0078",
                                                    session.id(),session.character_id,panel->base.next.leader.roster.size(),panel->base.next.applications.size(),published);
                                            }
                                            continue;
                                        }
                                        if(guild_entry) {
                                            // Chat keeps its existing delivery, but cancels a
                                            // modal input. Do not publish new permission after
                                            // the whole-batch invalidation for help+chat/move.
                                            const bool entry_menu_batch_safe=std::all_of(records.begin(),records.end(),[](const auto& value) {
                                                if(const auto* help=std::get_if<RecoveredNpcInteraction::Request>(&value))
                                                    return OwnedGuildPanelService::custom_help_entry(*help);
                                                return std::holds_alternative<RecoveredWorldRecords::Tick>(value) ||
                                                    std::holds_alternative<RecoveredWorldRecords::ClientOpaque74>(value) ||
                                                    std::holds_alternative<RecoveredWorldRecords::ClientControl1F>(value) ||
                                                    std::holds_alternative<RecoveredWorldRecords::ClientControl6D>(value) ||
                                                    std::holds_alternative<RecoveredWorldRecords::ClientOptionsNotification>(value) ||
                                                    std::holds_alternative<RecoveredWorldRecords::ContextNotification>(value) ||
                                                    std::holds_alternative<RecoveredWorldRecords::TimerNotification>(value) ||
                                                    std::holds_alternative<RecoveredWorldRecords::ClientDiagnostic>(value) ||
                                                    std::holds_alternative<RecoveredGuildRoster::PanelReady>(value);
                                            });
                                            const auto now=OwnedGuildEntryService::Clock::now();
                                            if(const auto menu=entry_menu_batch_safe?guild_entry->prepare(session.id(),now):std::nullopt) {
                                                bool published=false;
                                                if(guild_succession){
                                                    guild_succession->deliver(menu->lease.owner,{menu->logical.begin(),menu->logical.end()},[&,menu=*menu](bool accepted){if(accepted && guild_entry && guild_entry->published(menu,OwnedGuildEntryService::Clock::now()))spdlog::info("OWNED_GUILD_EFFECTIVE52_MENU_PUBLICATION session_id={} actor_account={} actor_character={} request={} key=2996 accepted=true CUSTOM-0083",menu.lease.owner.session,menu.lease.owner.account,menu.lease.owner.character,menu.lease.request);});
                                                }else{session.send_world_records(std::vector<std::uint8_t>(menu->logical.begin(),menu->logical.end()));published=guild_entry->published(*menu,OwnedGuildEntryService::Clock::now());}
                                                spdlog::info("OWNED_GUILD_ENTRY_MENU session_id={} character_id={} request={} published={} key=2996 entry=native_help_CUSTOM CUSTOM-0078",
                                                    session.id(),session.character_id,menu->lease.request,published);
                                                continue;
                                            }
                                        }
                                        if(const auto panel=guild_panel.prepare(session.id());panel && guild_panel.current(*panel)) {
                                            session.send_world_records(panel->logical);
                                            guild_panel.published(*panel);
                                            spdlog::info("OWNED_GUILD_READONLY_PANEL_OPEN session_id={} character_id={} members={} entry=native_help_CUSTOM no_economy_authority CUSTOM-0077",
                                                session.id(),session.character_id,panel->roster.next.roster->members.size());
                                        } else spdlog::info("OWNED_GUILD_READONLY_PANEL_DENIED session_id={} character_id={} no_qualified_owned_roster CUSTOM-0077",
                                            session.id(),session.character_id);
                                    }
                                }
                                if(without_guild_help.empty())return std::optional<std::vector<std::uint8_t>>{std::vector<std::uint8_t>{}};
                                records=without_guild_help;
                            }
                            if(config.streamer_privileges_enabled && session.recovered_world_ready()) {
                                const auto here=recovered_movement->current_location(session.id(),session.account_id,session.character_id);
                                if(here)for(const auto& [sender_id,sender_weak]:native_chat_sessions) {
                                    auto sender=sender_weak.lock();if(!sender || !sender->recovered_world_ready())continue;
                                    const auto where=recovered_movement->current_location(sender_id,sender->account_id,sender->character_id);
                                    if(!where||where->area!=here->area||where->scene!=here->scene)continue;
                                    const auto roles=database.recovered_characters().list_for_account(sender->account_id);
                                    const auto role=std::find_if(roles.begin(),roles.end(),[&](const auto& r){return r.id==sender->character_id;});
                                    if(role==roles.end())continue;
                                    const auto end=std::find(role->profile.begin(),role->profile.begin()+15,0);
                                    const auto name=LegacyChineseCodec::decode(std::string_view(reinterpret_cast<const char*>(role->profile.data()),
                                        static_cast<std::size_t>(end-role->profile.begin())),role->name_codepage==936);
                                    const auto encoded=LegacyChineseCodec::encode_display(name,session.recovered_client_language()==1);
                                    if(encoded.replacements||encoded.truncated||encoded.bytes.size()>14)continue;
                                    auto metadata=StreamerPresentation::metadata(static_cast<std::uint32_t>(role->id),role->streamer_privilege,
                                        session.recovered_client_language()==1,encoded.bytes);
                                    auto& previous=streamer_sent[session.id()][role->id];
                                    if(previous!=metadata){previous=metadata;session.send_world_records(std::move(metadata));}
                                }
                            }
                            const auto gameplay_records=RecoveredWorldRecords::without_client_diagnostics(records);
                            if(gameplay_records.size()!=records.size()) {
                                if(gameplay_records.empty()) return std::optional<std::vector<std::uint8_t>>(
                                    std::vector<std::uint8_t>{});
                                records=std::span<const RecoveredWorldRecords::Record>(gameplay_records);
                            }
                            // CUSTOM-0075: mode3 stays guild-only even after native
                            // 2D clears a name but leaves the old selected channel.
                            std::vector<RecoveredGuildChat::Request> guild_messages;
                            std::vector<RecoveredWorldRecords::Record> guild_moves;
                            bool guild_batch=true;
                            for(const auto& record:records) {
                                if(const auto* message=std::get_if<RecoveredGuildChat::Request>(&record))guild_messages.push_back(*message);
                                else if(std::holds_alternative<RecoveredMovement::Request>(record) ||
                                        std::holds_alternative<RecoveredWorldRecords::Tick>(record))guild_moves.push_back(record);
                                else guild_batch=false;
                            }
                            if(!guild_messages.empty()) {
                                auto deliveries=guild_batch?guild_chat.prepare(session.id(),guild_messages):
                                    std::optional<std::vector<OwnedGuildChatService::Delivery>>{};
                                if(!deliveries) {
                                    spdlog::info("NATIVE_GUILD_CHAT_REQUEST session_id={} character_id={} messages={} delivered=0 accepted=false CUSTOM-0075",
                                        session.id(),session.character_id,guild_messages.size());
                                    return std::optional<std::vector<std::uint8_t>>(std::vector<std::uint8_t>{});
                                }
                                std::optional<std::vector<std::uint8_t>> reply=std::vector<std::uint8_t>{};
                                const bool has_move=std::any_of(guild_moves.begin(),guild_moves.end(),[](const auto& r) {
                                    return std::holds_alternative<RecoveredMovement::Request>(r);
                                });
                                if(has_move) {
                                    reply=recovered_world->handle(session,guild_moves);if(!reply)return reply;
                                    try {
                                        auto next=native_parties;
                                        const auto changes=refresh_party_members(next,next.participants(session.id()));
                                        auto projected=party_projection(changes);native_parties=std::move(next);
                                        deliver_parties(std::move(projected));
                                    }catch(const std::exception& error) {
                                        spdlog::warn("NATIVE_GUILD_CHAT_MOVEMENT_REFRESH_FAILED reason={}",error.what());
                                    }
                                    deliveries=guild_chat.prepare(session.id(),guild_messages);
                                }
                                std::size_t delivered=0;
                                if(deliveries)for(auto& delivery:*deliveries) {
                                    const auto at=native_chat_sessions.find(delivery.recipient);if(at==native_chat_sessions.end())continue;
                                    if(auto peer=at->second.lock()) {
                                        if(has_move && peer->id()==session.id()) {
                                            const auto wire=RecoveredWorldFrame::encode(delivery.logical);
                                            reply->insert(reply->end(),wire.begin(),wire.end());
                                        }else peer->send_world_records(std::move(delivery.logical));
                                        ++delivered;
                                    }
                                }
                                spdlog::info("NATIVE_GUILD_CHAT_REQUEST session_id={} character_id={} messages={} delivered={} accepted={} CUSTOM-0075",
                                    session.id(),session.character_id,guild_messages.size(),delivered,deliveries.has_value());
                                return reply;
                            }
                            // CUSTOM-0074: isolate private2/automatic9 before any
                            // unrelated mutation or the frozen common dispatch.
                            std::vector<RecoveredPrivateChat::Request> private_messages;
                            std::vector<RecoveredWorldRecords::Record> private_moves;
                            bool private_batch=true;
                            for(const auto& record:records) {
                                if(const auto* message=std::get_if<RecoveredPrivateChat::Request>(&record))private_messages.push_back(*message);
                                else if(std::holds_alternative<RecoveredMovement::Request>(record) ||
                                        std::holds_alternative<RecoveredWorldRecords::Tick>(record))private_moves.push_back(record);
                                else private_batch=false;
                            }
                            if(!private_messages.empty()) {
                                auto deliveries=private_batch?private_chat.prepare(session.id(),private_messages):
                                    std::optional<std::vector<OwnedPrivateChatService::Delivery>>{};
                                if(!deliveries) {
                                    spdlog::info("NATIVE_PRIVATE_CHAT_REQUEST session_id={} character_id={} messages={} delivered=0 accepted=false CUSTOM-0074",
                                        session.id(),session.character_id,private_messages.size());
                                    return std::optional<std::vector<std::uint8_t>>(std::vector<std::uint8_t>{});
                                }
                                std::optional<std::vector<std::uint8_t>> reply=std::vector<std::uint8_t>{};
                                const bool has_move=std::any_of(private_moves.begin(),private_moves.end(),[](const auto& r) {
                                    return std::holds_alternative<RecoveredMovement::Request>(r);
                                });
                                if(has_move) {
                                    reply=recovered_world->handle(session,private_moves);if(!reply)return reply;
                                    try {
                                        auto next=native_parties;
                                        const auto changes=refresh_party_members(next,next.participants(session.id()));
                                        auto projected=party_projection(changes);native_parties=std::move(next);
                                        deliver_parties(std::move(projected));
                                    }catch(const std::exception& error) {
                                        spdlog::warn("NATIVE_PRIVATE_CHAT_MOVEMENT_REFRESH_FAILED reason={}",error.what());
                                    }
                                    deliveries=private_chat.prepare(session.id(),private_messages);
                                }
                                std::size_t delivered=0;
                                if(deliveries)for(auto& delivery:*deliveries) {
                                    const auto at=native_chat_sessions.find(delivery.recipient);if(at==native_chat_sessions.end())continue;
                                    if(auto peer=at->second.lock()) {
                                        if(has_move && peer->id()==session.id()) {
                                            const auto wire=RecoveredWorldFrame::encode(delivery.logical);
                                            reply->insert(reply->end(),wire.begin(),wire.end());
                                        } else peer->send_world_records(std::move(delivery.logical));
                                        ++delivered;
                                    }
                                }
                                spdlog::info("NATIVE_PRIVATE_CHAT_REQUEST session_id={} character_id={} messages={} delivered={} accepted={} CUSTOM-0074",
                                    session.id(),session.character_id,private_messages.size(),delivered,deliveries.has_value());
                                return reply;
                            }
                            // CUSTOM-0073: separate party-channel audience before
                            // every mutating route and the frozen common dispatch.
                            std::vector<RecoveredPartyChat::Request> party_messages;
                            std::vector<RecoveredWorldRecords::Record> party_chat_moves;
                            bool party_chat_batch=true;
                            for(const auto& record:records) {
                                if(const auto* message=std::get_if<RecoveredPartyChat::Request>(&record))party_messages.push_back(*message);
                                else if(std::holds_alternative<RecoveredMovement::Request>(record) ||
                                        std::holds_alternative<RecoveredWorldRecords::Tick>(record))party_chat_moves.push_back(record);
                                else party_chat_batch=false;
                            }
                            if(!party_messages.empty()) {
                                auto deliveries=party_chat_batch?party_chat.prepare(native_parties,session.id(),party_messages):
                                    std::optional<std::vector<OwnedPartyChatService::Delivery>>{};
                                if(!deliveries) {
                                    spdlog::info("NATIVE_PARTY_CHAT_REQUEST session_id={} character_id={} messages={} delivered=0 accepted=false CUSTOM-0073",
                                        session.id(),session.character_id,party_messages.size());
                                    return std::optional<std::vector<std::uint8_t>>(std::vector<std::uint8_t>{});
                                }
                                std::optional<std::vector<std::uint8_t>> reply=std::vector<std::uint8_t>{};
                                const bool has_move=std::any_of(party_chat_moves.begin(),party_chat_moves.end(),[](const auto& r) {
                                    return std::holds_alternative<RecoveredMovement::Request>(r);
                                });
                                if(has_move) {
                                    reply=recovered_world->handle(session,party_chat_moves);if(!reply)return reply;
                                    // The separate early return must retain the
                                    // existing accepted movement observer. Publish
                                    // native56 positions before the party text.
                                    try {
                                        auto next=native_parties;
                                        const auto changes=refresh_party_members(next,next.participants(session.id()));
                                        auto projected=party_projection(changes);native_parties=std::move(next);
                                        deliver_parties(std::move(projected));
                                    }catch(const std::exception& error){
                                        spdlog::warn("NATIVE_PARTY_CHAT_MOVEMENT_REFRESH_FAILED reason={}",error.what());
                                    }
                                    deliveries=party_chat.prepare(native_parties,session.id(),party_messages);
                                }
                                std::size_t delivered=0;
                                if(deliveries)for(auto& delivery:*deliveries) {
                                    const auto at=party_sessions.find(delivery.recipient);if(at==party_sessions.end())continue;
                                    if(auto peer=at->second.lock()) {
                                        if(has_move && peer->id()==session.id()) {
                                            const auto wire=RecoveredWorldFrame::encode(delivery.logical);
                                            reply->insert(reply->end(),wire.begin(),wire.end());
                                        } else peer->send_world_records(std::move(delivery.logical));
                                        ++delivered;
                                    }
                                }
                                spdlog::info("NATIVE_PARTY_CHAT_REQUEST session_id={} character_id={} messages={} delivered={} accepted={} CUSTOM-0073",
                                    session.id(),session.character_id,party_messages.size(),delivered,deliveries.has_value());
                                return reply;
                            }
                            // CUSTOM-0064: native bank money and NPC-window close.
                            // NPC37 opens only a role/placement-qualified service.
                            const RecoveredNpcInteraction::Request* bank_opener=nullptr;
                            bool bank_open_batch=true;
                            std::vector<RecoveredWorldRecords::Record> bank_open_remainder;
                            for(const auto& record:records) {
                                if(const auto* npc=std::get_if<RecoveredNpcInteraction::Request>(&record)) {
                                    if(bank_opener)bank_open_batch=false;
                                    bank_opener=npc;
                                } else {
                                    bank_open_remainder.push_back(record);
                                    if(!std::holds_alternative<RecoveredWorldRecords::Tick>(record) &&
                                       !std::holds_alternative<RecoveredChat::Request>(record))bank_open_batch=false;
                                }
                            }
                            if(bank_open_batch && bank_opener && bank_opener->raw_target && bank_opener->raw_target<=0xffff) {
                                try {
                                    const auto owned=trade_peer(session.id());
                                    // A known bank refusal (busy, distant, unready)
                                    // is consumed here; unknown NPCs retain their
                                    // existing route. Refusal must not disconnect
                                    // players and cancel an unrelated active trade.
                                    if(owned && database.bank_access().lookup(owned->area,owned->scene,
                                        static_cast<std::uint16_t>(bank_opener->raw_target),native_records_lab)) {
                                        if(auto opened=native_banks.open(session.id(),static_cast<std::uint16_t>(bank_opener->raw_target),std::chrono::steady_clock::now())) {
                                            auto items=bank_items_open(session.id(),static_cast<std::uint16_t>(bank_opener->raw_target),std::chrono::steady_clock::now());
                                            session.send_world_records(std::move(*opened));
                                            for(auto& batch:items)session.send_world_records(std::move(batch));
                                            spdlog::info("NATIVE_BANK_OPENED session_id={} target={} CUSTOM-0064",session.id(),bank_opener->raw_target);
                                        } else spdlog::info("NATIVE_BANK_OPEN_REJECTED session_id={} target={} CUSTOM-0064",session.id(),bank_opener->raw_target);
                                        if(!std::any_of(bank_open_remainder.begin(),bank_open_remainder.end(),[](const auto& r){return std::holds_alternative<RecoveredChat::Request>(r);}))
                                            return std::optional<std::vector<std::uint8_t>>(std::vector<std::uint8_t>{});
                                        records=std::span<const RecoveredWorldRecords::Record>(bank_open_remainder);
                                    }
                                }catch(const std::exception& error){spdlog::warn("NATIVE_BANK_OPEN_FAILED reason={}",error.what());}
                            }
                            // CUSTOM-0065: one authoritative native63/64/65.
                            // Prepare bounded48/bag replies and commit both cells
                            // atomically. Mixed economic/gameplay records reject.
                            std::vector<RecoveredBankItems::Request> item_bank_requests;
                            std::vector<RecoveredWorldRecords::Record> item_bank_remainder;
                            bool item_bank_batch=true;
                            for(const auto& record:records) {
                                if(const auto* request=std::get_if<RecoveredBankItems::Request>(&record))item_bank_requests.push_back(*request);
                                else {
                                    item_bank_remainder.push_back(record);
                                    if(!std::holds_alternative<RecoveredWorldRecords::Tick>(record) &&
                                       !std::holds_alternative<RecoveredChat::Request>(record))item_bank_batch=false;
                                }
                            }
                            if(!item_bank_requests.empty()) {
                                try {
                                    if(beast_bank_repository){
                                        const auto current=recovered_movement->current_location(session.id(),session.account_id,session.character_id);
                                        item_bank_batch=item_bank_batch&&beast_bank_wire&&item_bank_requests.size()==1&&item_bank_requests.front()==*beast_bank_wire&&
                                            current&&beast_bank_position&&*current==*beast_bank_position;
                                    }
                                    auto result=bank_items_handle(session.id(),item_bank_batch?std::span<const RecoveredBankItems::Request>(item_bank_requests):std::span<const RecoveredBankItems::Request>{},std::chrono::steady_clock::now());
                                    for(auto& batch:result.batches)session.send_world_records(std::move(batch));
                                    if(result.rejected)native_banks.disconnect(session.id());
                                    spdlog::info("NATIVE_BANK_ITEM_REQUEST session_id={} committed={} rejected={} CUSTOM-0065",session.id(),result.committed,result.rejected);
                                    if(owned_mixed_bank)spdlog::info("OWNED_MIXED_BANK_REQUEST session_id={} committed={} rejected={} CUSTOM-0070",session.id(),result.committed,result.rejected);
                                }catch(const std::exception& error){bank_items_disconnect(session.id());native_banks.disconnect(session.id());spdlog::warn("NATIVE_BANK_ITEM_REQUEST_FAILED reason={}",error.what());}
                                if(!item_bank_batch || !std::any_of(item_bank_remainder.begin(),item_bank_remainder.end(),[](const auto& r){return std::holds_alternative<RecoveredChat::Request>(r);}))
                                    return std::optional<std::vector<std::uint8_t>>(std::vector<std::uint8_t>{});
                                records=std::span<const RecoveredWorldRecords::Record>(item_bank_remainder);
                            }
                            std::vector<RecoveredBank::Request> bank_requests;
                            std::vector<RecoveredWorldRecords::Record> bank_remainder;
                            bool bank_batch=true;
                            for(const auto& record:records) {
                                if(const auto* request=std::get_if<RecoveredBank::Request>(&record))bank_requests.push_back(*request);
                                else {
                                    bank_remainder.push_back(record);
                                    if(!std::holds_alternative<RecoveredWorldRecords::Tick>(record) &&
                                       !std::holds_alternative<RecoveredChat::Request>(record))bank_batch=false;
                                }
                            }
                            if(!bank_requests.empty()) {
                                try {
                                    auto result=native_banks.handle(session.id(),bank_batch?std::span<const RecoveredBank::Request>(bank_requests):std::span<const RecoveredBank::Request>{},std::chrono::steady_clock::now());
                                    if(result.rejected || std::any_of(bank_requests.begin(),bank_requests.end(),[](const auto& r){return r.kind==RecoveredBank::Kind::Close;}))bank_items_disconnect(session.id());
                                    if(!result.logical.empty())session.send_world_records(std::move(result.logical));
                                    spdlog::info("NATIVE_BANK_REQUEST session_id={} committed={} rejected={} CUSTOM-0064",session.id(),result.committed,result.rejected);
                                }catch(const std::exception& error){spdlog::warn("NATIVE_BANK_REQUEST_FAILED reason={}",error.what());}
                                if(!bank_batch || !std::any_of(bank_remainder.begin(),bank_remainder.end(),[](const auto& r){return std::holds_alternative<RecoveredChat::Request>(r);}))
                                    return std::optional<std::vector<std::uint8_t>>(std::vector<std::uint8_t>{});
                                records=std::span<const RecoveredWorldRecords::Record>(bank_remainder);
                            }
                            // CUSTOM-0072: native59 readonly roster position query.
                            // Existing party state and common-chat dispatch are
                            // preserved; supplied names cannot authorize a peer.
                            const RecoveredPartyPositionQuery::Request* position_query=nullptr;
                            bool query_batch=true,has_query=false;
                            std::vector<RecoveredWorldRecords::Record> query_remainder;
                            for(const auto& record:records) {
                                if(const auto* query=std::get_if<RecoveredPartyPositionQuery::Request>(&record)) {
                                    has_query=true;if(position_query)query_batch=false;position_query=query;
                                } else {
                                    query_remainder.push_back(record);
                                    if(!std::holds_alternative<RecoveredWorldRecords::Tick>(record) &&
                                        !std::holds_alternative<RecoveredChat::Request>(record))query_batch=false;
                                }
                            }
                            if(has_query) {
                                if(!query_batch)return std::optional<std::vector<std::uint8_t>>(std::vector<std::uint8_t>{});
                                const auto logical=party_position_queries.query(native_parties,session.id(),*position_query);
                                if(logical)session.send_world_records(*logical);
                                spdlog::info("NATIVE_PARTY_POSITION_QUERY session_id={} character_id={} target={} delivered={} CUSTOM-0072",
                                    session.id(),session.character_id,position_query->target,logical.has_value());
                                if(!std::any_of(query_remainder.begin(),query_remainder.end(),[](const auto& record) {
                                    return std::holds_alternative<RecoveredChat::Request>(record);
                                }))return std::optional<std::vector<std::uint8_t>>(std::vector<std::uint8_t>{});
                                records=std::span<const RecoveredWorldRecords::Record>(query_remainder);
                            }
                            // CUSTOM-0062: native consenting party request/answer,
                            // CUSTOM-0063: original trade allows2B+2C coalescing.
                            // Preserve unrelated common chat in its frozen route.
                            std::vector<RecoveredTrade::Request> trade_requests;
                            std::vector<RecoveredWorldRecords::Record> trade_remainder;
                            bool trade_batch=true;
                            for(const auto& record:records) {
                                if(const auto* request=std::get_if<RecoveredTrade::Request>(&record))trade_requests.push_back(*request);
                                else {
                                    trade_remainder.push_back(record);
                                    if(!std::holds_alternative<RecoveredWorldRecords::Tick>(record) &&
                                        !std::holds_alternative<RecoveredChat::Request>(record))trade_batch=false;
                                }
                            }
                            if(!trade_requests.empty()) {
                                try {
                                    const auto trade_input=trade_batch?std::span<const RecoveredTrade::Request>(trade_requests):std::span<const RecoveredTrade::Request>{};
                                    auto result=owned_instance_trades?owned_instance_trades->handle(session.id(),trade_input,std::chrono::steady_clock::now()):native_trades.handle(session.id(),trade_input,std::chrono::steady_clock::now());
                                    deliver_trades(std::move(result.deliveries));
                                    spdlog::info("NATIVE_TRADE_REQUEST session_id={} records={} committed={} rejected={} {}",session.id(),trade_requests.size(),result.committed,result.rejected,owned_instance_trades?"CUSTOM-0069":"CUSTOM-0063");
                                }catch(const std::exception& error){spdlog::warn("NATIVE_TRADE_REQUEST_FAILED session_id={} reason={}",session.id(),error.what());}
                                if(!trade_batch || !std::any_of(trade_remainder.begin(),trade_remainder.end(),[](const auto& r){return std::holds_alternative<RecoveredChat::Request>(r);}))
                                    return std::optional<std::vector<std::uint8_t>>(std::vector<std::uint8_t>{});
                                records=std::span<const RecoveredWorldRecords::Record>(trade_remainder);
                            }
                            // CUSTOM-0062: native consenting party request/answer,
                            // kick and leave. Prepare all native projections before
                            // publishing the ephemeral membership state.
                            const RecoveredParty::Request* party_request=nullptr;
                            bool party_batch=true,has_party=false;
                            std::vector<RecoveredWorldRecords::Record> party_remainder;
                            for(const auto& record:records) {
                                if(const auto* request=std::get_if<RecoveredParty::Request>(&record)) {
                                    has_party=true;if(party_request)party_batch=false;party_request=request;
                                } else if(!std::holds_alternative<RecoveredWorldRecords::Tick>(record) &&
                                          !std::holds_alternative<RecoveredChat::Request>(record))party_batch=false;
                            }
                            if(has_party && !party_batch)return std::optional<std::vector<std::uint8_t>>(std::vector<std::uint8_t>{});
                            if(has_party) {
                                auto next=native_parties;
                                try {
                                    auto relevant=next.participants(session.id());
                                    if(party_request)for(const auto& [id,weak]:party_sessions)if(auto peer=weak.lock())
                                        if(peer->character_id==party_request->target) {
                                            const auto group=next.participants(id);relevant.insert(relevant.end(),group.begin(),group.end());
                                        }
                                    auto refresh=refresh_party_members(next,std::move(relevant));
                                    std::size_t action_events=0;
                                    if(party_request) {
                                        const auto action=next.handle(session.id(),*party_request,std::chrono::steady_clock::now());
                                        refresh.insert(refresh.end(),action.begin(),action.end());
                                        action_events=action.size();
                                    }
                                    auto projections=party_projection(refresh);native_parties=std::move(next);deliver_parties(std::move(projections));
                                    if(party_request)spdlog::info("NATIVE_PARTY_REQUEST session_id={} character_id={} kind={} events={} CUSTOM-0062",
                                        session.id(),session.character_id,static_cast<unsigned>(party_request->kind),action_events);
                                }catch(const std::exception& error){spdlog::warn("NATIVE_PARTY_REJECTED reason={} no_commit",error.what());}
                                // Native queues coalesce records. Preserve common
                                // chat in the same flush by passing it to the
                                // existing frozen handler unchanged.
                                for(const auto& record:records)if(!std::holds_alternative<RecoveredParty::Request>(record))
                                    party_remainder.push_back(record);
                                if(!std::any_of(party_remainder.begin(),party_remainder.end(),[](const auto& record) {
                                    return std::holds_alternative<RecoveredChat::Request>(record);
                                }))return std::optional<std::vector<std::uint8_t>>(std::vector<std::uint8_t>{});
                                records=std::span<const RecoveredWorldRecords::Record>(party_remainder);
                            }
                            if(beast_discard_prepared){
                                const auto empty=[](){return std::optional<std::vector<std::uint8_t>>(std::vector<std::uint8_t>{});};
                                const auto use=OwnedBeastDiscardService::request(records);
                                const auto current=recovered_movement->current_location(session.id(),session.account_id,session.character_id);
                                const auto& captured=beast_discard_prepared->expected;
                                if(!use||*use!=beast_discard_prepared->use||!current||!beast_discard_position||*current!=*beast_discard_position||
                                   captured.bag.account!=session.account_id||captured.bag.character!=session.character_id||
                                   !session.recovered_world_ready()||(session.state()!=SessionState::CharacterSelected&&session.state()!=SessionState::InWorld)||
                                   !owned_beasts_projected.contains(session.id())||trade_active(session.id())||
                                   diagnostic_town_scene_pending.contains(session.id())||diagnostic_island_return_pending.contains(session.id()))return empty();
                                std::optional<SqliteBeastBagRepository::Result> committed;
                                try{
                                    if(supply_repository.owned_pending_battle(session.account_id,session.character_id))return empty();
                                    // Retire bag modal leases before the standalone writer; their
                                    // old cached items cannot acquire new mutation authority.
                                    bank_items_disconnect(session.id());native_banks.disconnect(session.id());
                                    beast_exploration.disconnect(session.id());
                                    committed.emplace(beast_discard->commit(*beast_discard_prepared));
                                }catch(const std::exception& error){
                                    try{spdlog::warn("OWNED_BEAST_DISCARD_DENIED session_id={} reason={} no_commit",session.id(),error.what());}catch(...){}
                                    try{
                                        const auto live=recovered_movement->current_location(session.id(),session.account_id,session.character_id);
                                        if(live&&*live==*beast_discard_position&&session.recovered_world_ready()&&
                                           captured.bag.account==session.account_id&&captured.bag.character==session.character_id&&
                                           owned_beasts_projected.contains(session.id())&&!trade_active(session.id())&&
                                           !diagnostic_town_scene_pending.contains(session.id())&&!diagnostic_island_return_pending.contains(session.id())&&
                                           !supply_repository.owned_pending_battle(session.account_id,session.character_id))
                                            return std::optional<std::vector<std::uint8_t>>(beast_bag_repository->refresh_source(session.account_id,session.character_id,use->slot));
                                    }catch(...){}
                                    return empty();
                                }
                                // After COMMIT logging cannot turn a successful destruction
                                // into a rejection or discard the already allocated reply.
                                try{spdlog::info("OWNED_BEAST_DISCARD_COMMITTED session_id={} character_id={} item={} source={} CUSTOM-0085 whole_instance_journal",session.id(),session.character_id,use->item,use->slot);}catch(...){}
                                return std::optional<std::vector<std::uint8_t>>(std::move(committed->wire));
                            }
                            // CUSTOM-0071 only intercepts an owned typed source.
                            // All existing scalar requests retain their accepted
                            // branch below, including its malformed-batch policy.
                            if(owned_instance_discards && session.account_id && session.character_id) {
                                bool typed_source=false;
                                try {
                                    for(const auto& record:records)if(const auto* discard=std::get_if<RecoveredInventoryDiscard::Request>(&record)) {
                                        if(discard->slot>=50)continue;
                                        const auto saved=supply_repository.load_inventory_slot(session.account_id,session.character_id,discard->slot);
                                        if(saved && bag_slot_eligible(*saved))continue;
                                        if(saved && saved->count && (saved->item_id==RecoveredTeleportGem::item_id ||
                                           database.native_armor_catalog().lookup(saved->item_id) || database.native_weapon_catalog().lookup(saved->item_id))) {
                                            typed_source=true;break;
                                        }
                                    }
                                    if(typed_source) {
                                        auto result=owned_instance_discards->handle(session.id(),records,std::chrono::steady_clock::now());
                                        spdlog::info("OWNED_INSTANCE_DISCARD_REQUEST session_id={} character_id={} committed={} rejected={} CUSTOM-0071",
                                            session.id(),session.character_id,result.committed,result.rejected);
                                        return std::optional<std::vector<std::uint8_t>>(std::move(result.wire));
                                    }
                                }catch(const DatabaseError& error) {
                                    spdlog::warn("OWNED_INSTANCE_DISCARD_UNQUALIFIED session_id={} reason={} no_commit",session.id(),error.what());
                                    return std::optional<std::vector<std::uint8_t>>(std::vector<std::uint8_t>{});
                                }
                            }
                            // CUSTOM-0061: admit one native27 discard plus idle ticks,
                            // before unrelated handlers. No equipment or ground-drop guess.
                            if(std::any_of(records.begin(),records.end(),[](const auto& record) {
                                return std::holds_alternative<RecoveredInventoryDiscard::Request>(record);
                            })) {
                                const RecoveredInventoryDiscard::Request* discard=nullptr;
                                for(const auto& record:records) {
                                    if(const auto* next=std::get_if<RecoveredInventoryDiscard::Request>(&record)) {
                                        if(discard)return std::optional<std::vector<std::uint8_t>>(std::vector<std::uint8_t>{});
                                        discard=next;
                                    } else if(!std::holds_alternative<RecoveredWorldRecords::Tick>(record))
                                        return std::optional<std::vector<std::uint8_t>>(std::vector<std::uint8_t>{});
                                }
                                const auto empty=[](){return std::optional<std::vector<std::uint8_t>>(std::vector<std::uint8_t>{});};
                                if(!discard || !session.recovered_world_ready() ||
                                   (session.state()!=SessionState::CharacterSelected && session.state()!=SessionState::InWorld) ||
                                   !owned_bag_projected.contains(session.id()) ||
                                   diagnostic_town_scene_pending.contains(session.id()) ||
                                   diagnostic_island_return_pending.contains(session.id()) || discard->slot>=30 ||
                                   !recovered_movement->current_location(session.id(),session.account_id,session.character_id))return empty();
                                const auto before=supply_repository.load_inventory_slot(session.account_id,session.character_id,discard->slot);
                                if(!before || !bag_slot_eligible(*before))return empty();
                                const auto unchanged=[&](){return std::optional<std::vector<std::uint8_t>>(
                                    RecoveredWorldFrame::encode(bag_slot_projection(discard->slot,*before)));};
                                if(!discard->quantity || discard->quantity>before->count || discard->item!=before->item_id)return unchanged();
                                if(config.diagnostic_town_quest_progress && discard->slot==0) {
                                    const auto progress=supply_repository.load_town_guide_progress(session.account_id,session.character_id);
                                    if(!progress || progress->stage<3)return unchanged();
                                }
                                try {
                                    auto result=inventory_discards.discard(session.account_id,session.character_id,*discard,*before);
                                    spdlog::info("OWNED_BAG_DISCARD_COMMITTED session_id={} character_id={} item={} slot={} quantity={} remaining={} revision={} CUSTOM-0061",
                                        session.id(),session.character_id,discard->item,discard->slot,discard->quantity,result.slot.count,result.slot.revision);
                                    return std::optional<std::vector<std::uint8_t>>(std::move(result.wire));
                                } catch(const DatabaseError& error) {
                                    spdlog::warn("OWNED_BAG_DISCARD_REJECTED session_id={} reason={} no_commit",session.id(),error.what());
                                    return unchanged();
                                }
                            }
                            if(std::any_of(records.begin(),records.end(),[](const auto& record) {
                                return std::holds_alternative<RecoveredPet2Revert::Request>(record);
                            })) {
                                const RecoveredPet2Revert::Request* request=nullptr;
                                bool batch_valid=true;
                                for(const auto& record:records) {
                                    if(const auto* candidate=std::get_if<RecoveredPet2Revert::Request>(&record)) {
                                        if(request)batch_valid=false;
                                        request=candidate;
                                    } else if(!std::holds_alternative<RecoveredWorldRecords::Tick>(record))batch_valid=false;
                                }
                                const char* reason="mixed_mutation_batch";
                                if(batch_valid && request) {
                                    const bool ready=session.recovered_world_ready() &&
                                        owned_player_and_companions_projected.contains(session.id()) &&
                                        !diagnostic_town_scene_pending.contains(session.id()) &&
                                        !diagnostic_island_return_pending.contains(session.id()) &&
                                        recovered_movement->current_location(session.id(),session.account_id,session.character_id).has_value();
                                    reason=RecoveredPet2RevertGate::name(pet2_revert_gate.inspect(
                                        {session.account_id,session.character_id,ready,session.state()==SessionState::InBattle},*request));
                                }
                                spdlog::info("OWNED_PET2_REVERT_DENIED session_id={} character_id={} reason={} item_slot={} pet_slot={} option={} no_state_change no_success_reply",
                                    session.id(),session.character_id,reason,request?request->item_slot:0xff,
                                    request?request->pet_slot:0xff,request?request->option:0xff);
                                return std::optional<std::vector<std::uint8_t>>(std::vector<std::uint8_t>{});
                            }
                            // Native C2S20/S2C23 secondary role text. CUSTOM-0056
                            // adds owned persistence; the primary name is untouched.
                            if(std::any_of(records.begin(),records.end(),[](const auto& record) {
                                return std::holds_alternative<RecoveredRoleText::Request>(record);
                            })) {
                                const auto empty=[](){return std::optional<std::vector<std::uint8_t>>(std::vector<std::uint8_t>{});};
                                const RecoveredRoleText::Request* request=nullptr;
                                for(const auto& record:records) {
                                    if(const auto* candidate=std::get_if<RecoveredRoleText::Request>(&record)) {
                                        if(request)return empty();
                                        request=candidate;
                                    } else if(!std::holds_alternative<RecoveredWorldRecords::Tick>(record))return empty();
                                }
                                if(!request || !session.recovered_world_ready() ||
                                   !owned_player_and_companions_projected.contains(session.id()) ||
                                   session.state()==SessionState::InBattle || diagnostic_town_scene_pending.contains(session.id()) ||
                                   diagnostic_island_return_pending.contains(session.id()) ||
                                   !recovered_movement->current_location(session.id(),session.account_id,session.character_id))return empty();
                                const auto text=RecoveredRoleText::canonical(*request);
                                if(!text)return empty();
                                const auto logical=RecoveredRoleText::update(*text);
                                if(!logical)return empty();
                                auto wire=RecoveredWorldFrame::encode(*logical);
                                std::optional<RecoveredVisibility::AppearancePlan> role_plan;
                                std::optional<RecoveredVisibility::Presence> pending_role;
                                try {
                                    const auto before=database.role_text().load(session.account_id,session.character_id);
                                    const auto saved=database.role_text().save(session.account_id,session.character_id,
                                        before?std::optional<std::uint64_t>(before->revision):std::nullopt,*text,
                                        session.recovered_client_language()==1?936:950,[&](const StoredRoleText& next) {
                                            if(!player_presence_enabled)return;
                                            if(const auto source=player_visibility.snapshot(session.id())) {
                                                const auto projected=SqliteRoleTextRepository::project(next,
                                                    RecoveredRemoteRoleText::source_codepage(source->spawn));
                                                role_plan=player_visibility.prepare_role_text(session.id(),session.account_id,
                                                    session.character_id,projected.value_or(RecoveredRoleText::Text{}));
                                                std::erase_if(role_plan->deliveries,[&](auto& delivery) {
                                                    const auto receiver=visibility_sessions.find(delivery.recipient);
                                                    if(receiver==visibility_sessions.end())return true;
                                                    const auto peer=receiver->second.lock();
                                                    // A transport can expire before its serialized
                                                    // disconnect removes visibility membership. It
                                                    // cannot veto the owner's durable text change.
                                                    if(!peer)return true;
                                                    const auto projection=RecoveredPeerRoleText::per_recipient(role_plan->after.spawn,next,
                                                        peer->recovered_client_language()==1?936:950);
                                                    const auto bytes=RecoveredRemoteActor::encode_logical(projection.spawn);
                                                    delivery.logical.assign(bytes.begin(),bytes.end());
                                                    return false;
                                                });
                                            } else if(const auto pending=pending_visibility.find(session.id());pending!=pending_visibility.end()) {
                                                if(pending->second.account!=session.account_id || pending->second.character!=session.character_id)
                                                    throw DatabaseError("Pending secondary role text owner mismatch");
                                                pending_role=pending->second;
                                                const auto projected=SqliteRoleTextRepository::project(next,
                                                    RecoveredRemoteRoleText::source_codepage(pending_role->spawn));
                                                pending_role->spawn=RecoveredRemoteRoleText::with_source_text(pending_role->spawn,
                                                    projected.value_or(RecoveredRoleText::Text{})).value();
                                            }
                                        });
                                    spdlog::info("OWNED_ROLE_TEXT_SAVED session_id={} character_id={} revision={} codepage={} CUSTOM-0056",
                                        session.id(),session.character_id,saved.revision,saved.codepage);
                                } catch(const DatabaseError& error) {
                                    spdlog::warn("OWNED_ROLE_TEXT_DENIED session_id={} character_id={} reason={}",
                                        session.id(),session.character_id,error.what());
                                    return empty();
                                }
                                if(role_plan) {
                                    player_visibility.commit_appearance(*role_plan);
                                    // Every recipient's language projection was prepared inside
                                    // the save transaction. Do not re-read/reconvert after COMMIT.
                                    for(auto& delivery:role_plan->deliveries) {
                                        const auto receiver=visibility_sessions.find(delivery.recipient);
                                        if(receiver!=visibility_sessions.end())if(auto peer=receiver->second.lock())
                                            peer->send_world_records(std::move(delivery.logical));
                                    }
                                }
                                if(pending_role)pending_visibility.at(session.id())=*pending_role;
                                return std::optional<std::vector<std::uint8_t>>(std::move(wire));
                            }
                            if(config.fruit_village_quests_enabled && recovered_movement) {
                                const auto location=recovered_movement->current_location(session.id(),session.account_id,session.character_id);
                                if(config.fruit_sourcehint_placements && location && location->area==13 && location->scene==12 && !diagnostic_town_scene_pending.contains(session.id()) && !diagnostic_island_return_pending.contains(session.id()))
                                    if(auto handled=fruit_quests.handle(session,records,location))return handled;
                            }
                            if(config.owned_attribute_allocation_enabled && std::any_of(records.begin(),records.end(),[](const auto& record) {
                                return std::holds_alternative<RecoveredAttributeAllocation::Request>(record);
                            })) {
                                const auto empty=[](){return std::optional<std::vector<std::uint8_t>>(std::vector<std::uint8_t>{});};
                                std::vector<RecoveredAttributeAllocation::Request> requests;
                                for(const auto& record:records) {
                                    if(std::holds_alternative<RecoveredWorldRecords::Tick>(record))continue;
                                    const auto* candidate=std::get_if<RecoveredAttributeAllocation::Request>(&record);
                                    if(!candidate)return empty();
                                    requests.push_back(*candidate);
                                }
                                // Native entry retains CharacterSelected until the first
                                // movement; completed tail + owned projection are the
                                // world qualification, as in the other owned handlers.
                                if(requests.empty() || !session.recovered_world_ready() ||
                                   (session.state()!=SessionState::InWorld && session.state()!=SessionState::CharacterSelected) ||
                                   !owned_player_and_companions_projected.contains(session.id()) ||
                                   diagnostic_town_scene_pending.contains(session.id()) || diagnostic_island_return_pending.contains(session.id()) ||
                                   !recovered_movement->current_location(session.id(),session.account_id,session.character_id) ||
                                   supply_repository.owned_pending_battle(session.account_id,session.character_id))return empty();
                                auto response=allocate_owned_attributes(database.recovered_characters(),lua,
                                    session.account_id,session.character_id,requests);
                                for(const auto request:requests)
                                    spdlog::info("OWNED_ATTRIBUTE_ALLOCATION_HANDLED session_id={} character_id={} selector={} batch_size={} native_one_point_contract derived_stats_unchanged",
                                        session.id(),session.character_id,request.selector,requests.size());
                                return std::optional<std::vector<std::uint8_t>>(std::move(response));
                            }
                            // CUSTOM-0057: native gem25/26 -> owned6D offer ->99.
                            // Only the verified Island01 -> CityI1 arrival is enabled.
                            if(config.owned_teleport_gem_enabled && teleport_gem_offers.claims(session.id(),records)) {
                                const auto empty=[](){return std::optional<std::vector<std::uint8_t>>(std::vector<std::uint8_t>{});};
                                const auto operation=OwnedTeleportGemOffer::preflight(records);
                                if(!operation)return empty();
                                const OwnedTeleportGemOffer::Owner owner{session.id(),session.account_id,session.character_id,
                                    session.recovered_world_ready() && owned_gems_projected.contains(session.id()),
                                    session.state()==SessionState::InBattle,
                                    diagnostic_town_scene_pending.contains(session.id()) || diagnostic_island_return_pending.contains(session.id()),
                                    recovered_movement->current_location(session.id(),session.account_id,session.character_id)};
                                if(operation->kind==OwnedTeleportGemOffer::Kind::Cancel) {
                                    teleport_gem_offers.cancel(owner,*operation);return empty();
                                }
                                if(!owner.ready || owner.in_battle || owner.transfer_pending || !owner.position)return empty();
                                std::vector<std::uint8_t> wire;
                                std::optional<RecoveredMovementService::OwnedIslandReturnPlan> plan;
                                std::optional<TeleportGemTransfer> committed;
                                std::optional<RecoveredVisibility> next_visibility;
                                std::vector<RecoveredVisibility::Delivery> departures;
                                std::map<std::uint64_t,RecoveredVisibility::Presence> prepared_pending;
                                std::set<std::uint64_t> prepared_scene,prepared_return;
                                std::optional<OwnedTeleportGemOffer::Prepared> offered;
                                try {
                                    if(operation->kind==OwnedTeleportGemOffer::Kind::Open) {
                                        const auto item=database.teleport_gems().load(session.account_id,session.character_id,operation->slot);
                                        if(!item)return empty();
                                        const auto menu=teleport_gem_offers.open(owner,*operation,*item);
                                        if(!menu)return empty();
                                        spdlog::info("OWNED_TELEPORT_GEM_OPEN session_id={} character_id={} slot={} revision={} CUSTOM-0057",session.id(),session.character_id,item->slot,item->revision);
                                        return std::optional<std::vector<std::uint8_t>>(RecoveredWorldFrame::encode(*menu));
                                    }
                                    const auto slot=teleport_gem_offers.pending_slot(session.id());
                                    if(!slot)return empty();
                                    const auto item=database.teleport_gems().load(session.account_id,session.character_id,*slot);
                                    if(!item)return empty();
                                    offered=teleport_gem_offers.select(owner,*operation,*item);
                                    if(!offered)return empty();
                                    plan=recovered_movement->prepare_owned_island_return(session.id(),session.account_id,
                                        session.character_id,offered->expected_position);
                                    // Allocate scene/presence changes before committing persistent state.
                                    // Node transfer below is allocation-free on the serialized executor.
                                    prepared_scene.insert(session.id());prepared_return.insert(session.id());
                                    if(player_presence_enabled) {
                                        auto source=player_visibility.snapshot(session.id());
                                        if(!source)if(const auto pending=pending_visibility.find(session.id());pending!=pending_visibility.end())source=pending->second;
                                        if(!source || source->account!=session.account_id || source->character!=session.character_id)
                                            throw DatabaseError("Owned teleport gem presence missing");
                                        prepared_pending.emplace(session.id(),visibility_at(*source,plan->after));
                                        next_visibility=player_visibility;
                                        departures=next_visibility->leave(session.id());
                                    }
                                    committed=database.teleport_gems().prepare_transfer(session.account_id,session.character_id,
                                        offered->expected_item,offered->expected_position,[&](const TeleportGemTransfer& result) {
                                            if(result.position_after!=plan->after)throw DatabaseError("Owned teleport gem destination mismatch");
                                            auto logical=gem_projection(result.after);
                                            logical.insert(logical.end(),plan->logical.begin(),plan->logical.end());
                                            wire=RecoveredWorldFrame::encode(logical);
                                        });
                                } catch(const std::exception& error) {
                                    spdlog::warn("OWNED_TELEPORT_GEM_DENIED session_id={} character_id={} reason={}",session.id(),session.character_id,error.what());
                                    return empty();
                                }
                                recovered_movement->commit_owned_island_return(*plan,committed->position_after);
                                if(!teleport_gem_offers.committed(session.id(),offered->token))std::terminate();
                                diagnostic_town_scene_pending.insert(prepared_scene.extract(session.id()));
                                diagnostic_island_return_pending.insert(prepared_return.extract(session.id()));
                                if(next_visibility) {
                                    static_assert(std::is_nothrow_move_assignable_v<RecoveredVisibility>);
                                    player_visibility=std::move(*next_visibility);
                                    auto inserted=pending_visibility.insert(prepared_pending.extract(session.id()));
                                    if(!inserted.inserted)inserted.position->second=inserted.node.mapped();
                                    visibility_sessions.erase(session.id());
                                    deliver_visibility(std::move(departures));
                                }
                                spdlog::info("OWNED_TELEPORT_GEM_COMMITTED session_id={} character_id={} slot={} item_revision={} position_revision={} target=2/4/56/75 CUSTOM-0057",session.id(),session.character_id,committed->after.slot,committed->after.revision,committed->position_after.revision);
                                return std::optional<std::vector<std::uint8_t>>(std::move(wire));
                            }
                            // Gem instances move as complete20-byte records. Classify only
                            // owned scalar identities; never probe arbitrary weapon overlays.
                            bool gem_move=false;
                            if(config.owned_teleport_gem_enabled)for(const auto& record:records)
                                if(const auto* move=std::get_if<RecoveredInventoryMoveRequest::Request>(&record))
                                    for(const auto slot:{move->source_slot,move->destination_slot})if(slot<30) {
                                        const auto scalar=supply_repository.load_inventory_slot(session.account_id,session.character_id,slot);
                                        if(scalar && scalar->item_id==RecoveredTeleportGem::item_id)gem_move=true;
                                    }
                            if(gem_move) {
                                const auto empty=[](){return std::optional<std::vector<std::uint8_t>>(std::vector<std::uint8_t>{});};
                                const RecoveredInventoryMoveRequest::Request* request=nullptr;
                                for(const auto& record:records) {
                                    if(const auto* move=std::get_if<RecoveredInventoryMoveRequest::Request>(&record)) {
                                        if(request)return empty();request=move;
                                    } else if(!std::holds_alternative<RecoveredWorldRecords::Tick>(record))return empty();
                                }
                                if(!request || request->source_slot>=30 || request->destination_slot>=30 ||
                                   !owned_gems_projected.contains(session.id()) || !session.recovered_world_ready() ||
                                   session.state()==SessionState::InBattle || diagnostic_town_scene_pending.contains(session.id()) ||
                                   !recovered_movement->current_location(session.id(),session.account_id,session.character_id))return empty();
                                try {
                                    const auto source=database.teleport_gems().load(session.account_id,session.character_id,request->source_slot);
                                    const auto destination=database.teleport_gems().load(session.account_id,session.character_id,request->destination_slot);
                                    if(!source || !destination || !source->metadata_present || source->slot==destination->slot)return empty();
                                    std::vector<std::uint8_t> wire;
                                    database.teleport_gems().move_whole(session.account_id,session.character_id,*source,*destination,
                                        [&](const TeleportGemMove& next) {
                                            auto logical=gem_projection(next.source);
                                            const auto other=gem_projection(next.destination);
                                            logical.insert(logical.end(),other.begin(),other.end());
                                            wire=RecoveredWorldFrame::encode(logical);
                                        });
                                    teleport_gem_offers.forget(session.id());
                                    return std::optional<std::vector<std::uint8_t>>(std::move(wire));
                                } catch(const DatabaseError& error) {
                                    spdlog::warn("OWNED_TELEPORT_GEM_MOVE_DENIED session_id={} reason={}",session.id(),error.what());return empty();
                                }
                            }
                            // CUSTOM-0050: ordinary owned self-player supply.
                            // Preflight the full frame before any callback, never
                            // interpret other targets as the player's resources.
                            if(config.owned_supply_enabled && std::any_of(records.begin(),records.end(),[](const auto& record) {
                                return std::holds_alternative<RecoveredTargetItemRequest::Request>(record);
                            })) {
                                const auto empty=[](){return std::optional<std::vector<std::uint8_t>>(std::vector<std::uint8_t>{});};
                                const auto use=RecoveredOwnedSupply::request(records);
                                if(!use || !session.recovered_world_ready() || session.state()==SessionState::InBattle ||
                                   !owned_supply_projected.contains(session.id()) || !session.character_id || session.character_id>0x3fff ||
                                   use->raw_target!=session.character_id || diagnostic_town_scene_pending.contains(session.id()) ||
                                   diagnostic_island_return_pending.contains(session.id()) ||
                                   !recovered_movement->current_location(session.id(),session.account_id,session.character_id))return empty();
                                const auto slot=supply_repository.load_inventory_slot(session.account_id,session.character_id,use->raw_slot);
                                const auto resources=supply_repository.load_resources(session.account_id,session.character_id);
                                if(!slot || !resources || slot->item_id!=use->client_item_id || !slot->count || slot->source_sha256!=supply_source ||
                                   supply_repository.owned_pending_battle(session.account_id,session.character_id))return empty();
                                const auto policy=DiagnosticSupplyService::native_declared_policy(database.native_supply_catalog(),use->client_item_id,static_cast<std::uint16_t>(session.character_id));
                                if(!policy)return empty();
                                auto result=diagnostic_supply.use(session.account_id,session.character_id,RecoveredTargetItemRequest::encode(*use),*policy,*slot,*resources);
                                const auto& after=result.resources?*result.resources:*resources;
                                spdlog::info("OWNED_SUPPLY_USE session_id={} character_id={} target={} slot={} item={} consumed={} hp_before={} hp_after={} mp_before={} mp_after={} resource_revision={} CUSTOM-0050 CUSTOM-0016",
                                    session.id(),session.character_id,use->raw_target,use->raw_slot,use->client_item_id,result.consumed,resources->hp,after.hp,resources->mp,after.mp,after.revision);
                                return std::optional<std::vector<std::uint8_t>>(std::move(result.wire));
                            }
                            // CUSTOM-0049: preflight the complete daily batch.
                            // An issued list is display state, never authority to
                            // teleport, consume a ticket, accept or reward quests.
                            if(std::any_of(records.begin(),records.end(),[](const auto& record) {
                                return std::holds_alternative<RecoveredWorldRecords::DailyPanelOpen>(record) ||
                                    std::holds_alternative<RecoveredDailyQuestRequest::Request>(record);
                            })) {
                                const auto empty=[](){return std::optional<std::vector<std::uint8_t>>(std::vector<std::uint8_t>{});};
                                const auto request=RecoveredOwnedDailyQuestView::request(records);
                                if(!config.owned_daily_quest_views_enabled || !request || !session.recovered_world_ready() ||
                                   session.state()==SessionState::InBattle || diagnostic_town_scene_pending.contains(session.id()) ||
                                   diagnostic_island_return_pending.contains(session.id()))return empty();
                                const auto location=recovered_movement->current_location(session.id(),session.account_id,session.character_id);
                                if(!location)return empty();
                                const auto saved=database.native_quest_catalog().owned_daily_list(session.account_id,session.character_id);
                                if(!saved){issued_daily_lists.erase(session.id());return empty();}
                                if(std::holds_alternative<RecoveredWorldRecords::DailyPanelOpen>(*request)) {
                                    issued_daily_lists.insert_or_assign(session.id(),IssuedDailyList{session.account_id,session.character_id,location->area,location->scene,*saved});
                                    spdlog::info("OWNED_DAILY_LIST_OPEN session_id={} character_id={} revision={} count={} CUSTOM-0049 no_quest_rule",session.id(),session.character_id,saved->revision,saved->logical[164]);
                                    return std::optional<std::vector<std::uint8_t>>(RecoveredWorldFrame::encode(saved->logical));
                                }
                                const auto issued=issued_daily_lists.find(session.id());
                                if(issued==issued_daily_lists.end() || issued->second.account!=session.account_id || issued->second.character!=session.character_id ||
                                   issued->second.area!=location->area || issued->second.scene!=location->scene || issued->second.list!=*saved)return empty();
                                const auto& action=std::get<RecoveredDailyQuestRequest::Request>(*request);
                                if(const auto* selection=std::get_if<RecoveredDailyQuestRequest::Selection>(&action)) {
                                    const auto source=database.native_quest_catalog().daily_displays();
                                    const auto bound=RecoveredOwnedDailyQuestView::binding(*saved,*selection,source);
                                    // Native 48B9B0 copies the panel's retained
                                    // +20FEB byte into this slot; observed original
                                    // producer vectors preserve 00/A5/FF. It is
                                    // neither a permission bit nor a required zero.
                                    if(!bound)return empty();
                                    // Native producer chooses the first bag cell
                                    // with key18CA; no count-based original cost.
                                    std::uint8_t ticket=0xff;
                                    for(std::uint8_t slot=0;slot<30;++slot) {
                                        const auto item=supply_repository.load_inventory_slot(session.account_id,session.character_id,slot);
                                        if(item && item->item_id==0x18ca){ticket=slot;break;}
                                    }
                                    if(selection->item_slot!=ticket)return empty();
                                    spdlog::info("OWNED_DAILY_NPC_INTENT_UNRESOLVED session_id={} character_id={} source_line={} index={} branch={} npc={} side={} ticket_slot={} opaque_tail={} no_state_change no_teleport",session.id(),session.character_id,bound->source_line,selection->index,selection->branch,selection->npc,selection->side,selection->item_slot,selection->opaque_tail);
                                } else if(RecoveredOwnedDailyQuestView::auxiliary(*saved)) {
                                    spdlog::info("OWNED_DAILY_CLAIM_INTENT_UNRESOLVED session_id={} character_id={} no_state_change no_reward",session.id(),session.character_id);
                                }
                                return empty();
                            }
                            // CUSTOM-0049: daily-panel dialog32 contributes one
                            // native BF variant. Match only its issued FD display
                            // context; this is not purchase, payment or an ACK.
                            if(std::any_of(records.begin(),records.end(),[](const auto& record) {
                                return std::holds_alternative<RecoveredBFRequest::Request>(record);
                            })) {
                                const RecoveredBFRequest::Request* purchase=nullptr;
                                for(const auto& record:records) {
                                    if(std::holds_alternative<RecoveredWorldRecords::Tick>(record))continue;
                                    const auto* candidate=std::get_if<RecoveredBFRequest::Request>(&record);
                                    if(!candidate || purchase)return std::nullopt;
                                    purchase=candidate;
                                }
                                if(!config.owned_daily_quest_views_enabled || !purchase || !session.recovered_world_ready() ||
                                   session.state()==SessionState::InBattle || diagnostic_town_scene_pending.contains(session.id()) ||
                                   diagnostic_island_return_pending.contains(session.id()))return std::nullopt;
                                const auto location=recovered_movement->current_location(session.id(),session.account_id,session.character_id);
                                if(!location)return std::nullopt;
                                const auto saved=database.native_quest_catalog().owned_daily_list(session.account_id,session.character_id);
                                if(!saved){issued_daily_lists.erase(session.id());return std::nullopt;}
                                const auto issued=issued_daily_lists.find(session.id());
                                if(issued==issued_daily_lists.end() || issued->second.account!=session.account_id ||
                                   issued->second.character!=session.character_id || issued->second.area!=location->area ||
                                   issued->second.scene!=location->scene || issued->second.list!=*saved)return std::nullopt;
                                const auto shaped=RecoveredOwnedDailyQuestView::purchase(*saved,*purchase);
                                if(!shaped)return std::nullopt;
                                spdlog::info("OWNED_DAILY_PURCHASE_INTENT_UNRESOLVED session_id={} character_id={} item={} displayed_amount={} no_wallet_change no_item_grant CUSTOM-0049",
                                    session.id(),session.character_id,shaped->item,shaped->displayed_amount);
                                return std::optional<std::vector<std::uint8_t>>(std::vector<std::uint8_t>{});
                            }
                            if(beast_equipment_snapshot){
                                const auto empty=[](){return std::optional<std::vector<std::uint8_t>>(std::vector<std::uint8_t>{});};
                                const auto use=OwnedBeastEquipmentService::request(records);
                                if(!use||!beast_equipment_use||use->raw_slot!=beast_equipment_use->raw_slot||use->client_item_id!=beast_equipment_use->client_item_id||
                                   beast_equipment_snapshot->domain!=SqliteBeastBagRepository::Domain::BeastEquipment||
                                   beast_equipment_snapshot->bag.account!=session.account_id||beast_equipment_snapshot->bag.character!=session.character_id||
                                   !session.recovered_world_ready()||(session.state()!=SessionState::CharacterSelected&&session.state()!=SessionState::InWorld)||
                                   !owned_beasts_projected.contains(session.id())||trade_active(session.id())||diagnostic_town_scene_pending.contains(session.id())||
                                   diagnostic_island_return_pending.contains(session.id())||!beast_equipment_position||
                                   recovered_movement->current_location(session.id(),session.account_id,session.character_id)!=beast_equipment_position)return empty();
                                try{
                                    auto result=beast_bag_repository->move(*beast_equipment_snapshot);
                                    // Inventory37 replies close the old native UI. Retire its
                                    // custom presentation too; never synthesize activity authority.
                                    if(result.changed)beast_exploration.disconnect(session.id());
                                    spdlog::info("OWNED_BEAST_EQUIPMENT_MOVE session_id={} character_id={} source={} destination={} CUSTOM-0085 full_instance_no_appearance_claim",session.id(),session.character_id,result.after.request.source_slot,result.after.request.destination_slot);
                                    return std::optional<std::vector<std::uint8_t>>(std::move(result.wire));
                                }catch(const DatabaseError& error){spdlog::warn("OWNED_BEAST_EQUIPMENT_MOVE_DENIED session_id={} reason={}",session.id(),error.what());return empty();}
                            }
                            if(beast_move_snapshot){
                                const auto empty=[](){return std::optional<std::vector<std::uint8_t>>(std::vector<std::uint8_t>{});};
                                const auto use=OwnedBeastBagService::request(records);
                                if(!use||*use!=beast_move_snapshot->request||beast_move_snapshot->bag.account!=session.account_id||beast_move_snapshot->bag.character!=session.character_id||
                                   !session.recovered_world_ready()||(session.state()!=SessionState::CharacterSelected&&session.state()!=SessionState::InWorld)||
                                   !owned_beasts_projected.contains(session.id())||trade_active(session.id())||diagnostic_town_scene_pending.contains(session.id())||
                                   diagnostic_island_return_pending.contains(session.id())||!beast_move_position||
                                   recovered_movement->current_location(session.id(),session.account_id,session.character_id)!=beast_move_position)return empty();
                                try{
                                    auto result=beast_bag_repository->move(*beast_move_snapshot);
                                    spdlog::info("OWNED_BEAST_BAG_MOVE session_id={} character_id={} source={} destination={} changed={} CUSTOM-0085 full_instance_only",session.id(),session.character_id,use->source_slot,use->destination_slot,result.changed);
                                    return std::optional<std::vector<std::uint8_t>>(std::move(result.wire));
                                }catch(const DatabaseError& error){spdlog::warn("OWNED_BEAST_BAG_MOVE_DENIED session_id={} reason={}",session.id(),error.what());return empty();}
                            }
                            // CUSTOM-0066: whole owned armor28/24, source-consistent
                            // metadata only. No inferred stat or appearance update.
                            if(config.owned_armor_transfers_enabled && std::any_of(records.begin(),records.end(),[](const auto& record) {
                                if(const auto* use=std::get_if<RecoveredSelectionItemRequest::Request>(&record))return OwnedArmorTransferService::slot(use->raw_slot);
                                if(const auto* move=std::get_if<RecoveredInventoryMoveRequest::Request>(&record))return move->source_slot<30 && move->destination_slot<30;
                                return false;
                            })) {
                                const auto empty=[](){return std::optional<std::vector<std::uint8_t>>(std::vector<std::uint8_t>{});};
                                const auto operation=OwnedArmorTransferService::request(records);
                                if(!operation || !session.account_id || !session.character_id)return empty();
                                std::uint8_t source=0;std::uint16_t item=0;unsigned opcode=0;
                                bool handled=false;
                                if(const auto* use=std::get_if<RecoveredSelectionItemRequest::Request>(&*operation)) {
                                    source=use->raw_slot;opcode=0x28;
                                    const auto row=supply_repository.load_inventory_slot(session.account_id,session.character_id,source);
                                    if(row){item=row->item_id;handled=(source>=30&&source<34) || (row->count&&database.native_armor_catalog().lookup(item).has_value());}
                                } else if(const auto* move=std::get_if<RecoveredInventoryMoveRequest::Request>(&*operation)) {
                                    source=move->source_slot;opcode=0x24;
                                    const auto a=supply_repository.load_inventory_slot(session.account_id,session.character_id,source);
                                    const auto b=supply_repository.load_inventory_slot(session.account_id,session.character_id,move->destination_slot);
                                    if(a)item=a->item_id;
                                    handled=(a&&a->count&&database.native_armor_catalog().lookup(a->item_id).has_value()) ||
                                        (b&&b->count&&database.native_armor_catalog().lookup(b->item_id).has_value());
                                }
                                if(handled) {
                                    if(!owned_armor_projected.contains(session.id()) || !session.recovered_world_ready() ||
                                       session.state()==SessionState::InBattle || trade_active(session.id()) ||
                                       diagnostic_town_scene_pending.contains(session.id()) || diagnostic_island_return_pending.contains(session.id()) ||
                                       !recovered_movement->current_location(session.id(),session.account_id,session.character_id))return empty();
                                    const auto reject=[&]() {
                                        std::vector<std::uint8_t> logical;
                                        if(item){const auto message=RecoveredEquipmentRejection::logical(item);logical.insert(logical.end(),message.begin(),message.end());}
                                        const auto snapshot=database.armor_slots().load_snapshot(session.account_id,session.character_id);
                                        for(std::uint8_t index=0;index<30;++index)if(snapshot.scalar[index]){
                                            const auto cell=owner_bag_projector->project(session.account_id,session.character_id,index,*snapshot.scalar[index]);logical.insert(logical.end(),cell.begin(),cell.end());
                                        }
                                        for(const auto& row:database.armor_slots().load_saved(session.account_id,session.character_id))if(row.slot>=30){
                                            const auto cell=OwnedArmorTransferService::slot_logical(row);logical.insert(logical.end(),cell.begin(),cell.end());
                                        }
                                        spdlog::info("OWNED_ARMOR_TRANSFER_REJECTED session_id={} account={} character={} item={} source={} opcode={} no_state_change",session.id(),session.account_id,session.character_id,item,source,opcode);
                                        return std::optional<std::vector<std::uint8_t>>(logical.empty()?std::vector<std::uint8_t>{}:RecoveredWorldFrame::encode(logical));
                                    };
                                    try {
                                        std::optional<OwnedArmorTransferService::Result> result;
                                        if(const auto* use=std::get_if<RecoveredSelectionItemRequest::Request>(&*operation))result=armor_transfers.select(session.account_id,session.character_id,*use);
                                        else result=armor_transfers.bag_move(session.account_id,session.character_id,std::get<RecoveredInventoryMoveRequest::Request>(*operation));
                                        if(!result)return reject();
                                        spdlog::info("OWNED_ARMOR_TRANSFER_COMMITTED session_id={} account={} character={} source={} destination={} opcode={} changed={} CUSTOM-0066 no_formula no_appearance no_grant",session.id(),session.account_id,session.character_id,result->state.source.slot,result->state.destination.slot,opcode,result->changed);
                                        return std::optional<std::vector<std::uint8_t>>(std::move(result->wire));
                                    } catch(const DatabaseError& error) {
                                        spdlog::warn("OWNED_ARMOR_TRANSFER_DENIED session_id={} reason={}",session.id(),error.what());
                                        try{return reject();}catch(const DatabaseError&){return empty();}
                                    }
                                }
                            }
                            // CUSTOM-0046: qualify the entire28/weapon24 frame
                            // before an older scalar move/other callback can run.
                            if(config.owned_weapon_transfers_enabled && std::any_of(records.begin(),records.end(),[](const auto& record) {
                                if(const auto* use=std::get_if<RecoveredSelectionItemRequest::Request>(&record))return OwnedWeaponTransferService::slot(use->raw_slot);
                                if(const auto* move=std::get_if<RecoveredInventoryMoveRequest::Request>(&record))return move->source_slot<30 && move->destination_slot<30;
                                return false;
                            })) {
                                const auto operation=OwnedWeaponTransferService::request(records);
                                if(!operation || !owned_weapons_projected.contains(session.id()) || !session.recovered_world_ready() ||
                                   session.state()==SessionState::InBattle || diagnostic_town_scene_pending.contains(session.id()) ||
                                   !recovered_movement->current_location(session.id(),session.account_id,session.character_id))
                                    return std::optional<std::vector<std::uint8_t>>(std::vector<std::uint8_t>{});
                                std::optional<OwnedWeaponTransferService::Result> result;
                                std::optional<RecoveredVisibility::AppearancePlan> appearance_plan;
                                std::optional<RecoveredVisibility::Presence> pending_appearance;
                                bool handled=false;
                                if(const auto* use=std::get_if<RecoveredSelectionItemRequest::Request>(&*operation)) {
                                    handled=true;
                                    if(use->raw_slot<30) {
                                        const auto source=database.weapon_slots().load(session.account_id,session.character_id,use->raw_slot);
                                        if(source && source->count==1 && source->item_id==use->client_item_id) {
                                            const auto definition=database.native_weapon_catalog().lookup(source->item_id);
                                            if(!definition)throw DatabaseError("Owned equipment source missing");
                                            const auto requirement=RecoveredWeaponSexRestriction::requirement(*definition);
                                            if(requirement!=RecoveredWeaponSexRestriction::Requirement::None) {
                                                const auto owned=database.recovered_characters().list_for_account(session.account_id);
                                                const auto found=std::find_if(owned.begin(),owned.end(),[&](const auto& character){return character.id==session.character_id;});
                                                if(found==owned.end())throw DatabaseError("Weapon sex profile ownership missing");
                                                if(!RecoveredWeaponSexRestriction::permits(requirement,RecoveredWeaponSexRestriction::profile_sex(found->profile))) {
                                                    const auto rejected=RecoveredEquipmentRejection::logical(source->item_id);
                                                    spdlog::info("OWNED_WEAPON_SOURCE_SEX_REJECTED session_id={} character_id={} item={} source_line={} no_state_change",session.id(),session.character_id,source->item_id,definition->source_line);
                                                    return std::optional<std::vector<std::uint8_t>>(RecoveredWorldFrame::encode(rejected));
                                                }
                                            }
                                        }
                                    }
                                    OwnedWeaponTransferService::PrepareExtra extra;
                                    if(config.diagnostic_owned_weapon_appearance) {
                                        const auto before=database.player_appearance().load(session.account_id,session.character_id);
                                        if(!before || (use->client_item_id!=1 && use->client_item_id!=2))
                                            return std::optional<std::vector<std::uint8_t>>(std::vector<std::uint8_t>{});
                                        extra=[&,before](const WeaponSlotMove& proposed) {
                                            const auto fields=RecoveredOwnedPlayerAppearance::fixture_after(*before,proposed);
                                            if(player_presence_enabled) {
                                                if(player_visibility.contains(session.id()))
                                                    appearance_plan=player_visibility.prepare_appearance(session.id(),session.account_id,session.character_id,fields);
                                                else {
                                                    const auto found=pending_visibility.find(session.id());
                                                    if(found==pending_visibility.end() || found->second.account!=session.account_id || found->second.character!=session.character_id)
                                                        throw std::runtime_error("Owned weapon appearance lacks bound presence");
                                                    pending_appearance=found->second;
                                                    const auto spawn=RecoveredRemoteActor::with_appearance(pending_appearance->spawn,fields);
                                                    if(!spawn)throw std::runtime_error("Pending weapon appearance rejected");
                                                    pending_appearance->spawn=*spawn;
                                                }
                                            }
                                            const auto saved=database.player_appearance().save(session.account_id,session.character_id,
                                                before->revision,fields,before->origin,before->provenance);
                                            const auto logical=RecoveredPlayerAppearanceUpdate::encode(saved.fields);
                                            return std::vector<std::uint8_t>(logical.begin(),logical.end());
                                        };
                                    }
                                    result=weapon_transfers.select(session.account_id,session.character_id,*use,extra);
                                } else if(const auto* move=std::get_if<RecoveredInventoryMoveRequest::Request>(&*operation)) {
                                    const auto source=supply_repository.load_inventory_slot(session.account_id,session.character_id,move->source_slot);
                                    const auto destination=supply_repository.load_inventory_slot(session.account_id,session.character_id,move->destination_slot);
                                    handled=(source && source->count && qualified_weapon(source->item_id)) ||
                                        (destination && destination->count && qualified_weapon(destination->item_id));
                                    if(handled)result=weapon_transfers.bag_move(session.account_id,session.character_id,*move);
                                }
                                if(handled) {
                                    if(!result)return std::optional<std::vector<std::uint8_t>>(std::vector<std::uint8_t>{});
                                    if(result->changed && appearance_plan) {
                                        player_visibility.commit_appearance(*appearance_plan);
                                        deliver_visibility(std::move(appearance_plan->deliveries));
                                    }
                                    if(result->changed && pending_appearance)
                                        pending_visibility.at(session.id())=*pending_appearance;
                                    spdlog::info("OWNED_WEAPON_TRANSFER_COMMITTED session_id={} character_id={} source={} destination={} source_revision={} destination_revision={} changed={} diagnostic_appearance={} CUSTOM-0046 no_formula no_item_grant",
                                        session.id(),session.character_id,result->state.source.slot,result->state.destination.slot,
                                        result->state.source.revision,result->state.destination.revision,result->changed,config.diagnostic_owned_weapon_appearance);
                                    return std::optional<std::vector<std::uint8_t>>(std::move(result->wire));
                                }
                                // A nonweapon drag is outside this route. If no
                                // scalar bag policy is enabled, leave saved state
                                // and connection intact instead of falling into
                                // a disabled legacy callback that closes it.
                                if(!config.diagnostic_town_quest_progress && !config.diagnostic_world_supply && !config.owned_map_views_enabled)
                                    return std::optional<std::vector<std::uint8_t>>(std::vector<std::uint8_t>{});
                            }
                            // CUSTOM-0044: repeatable owned regional map presentation.
                            // Preflight the entire frame before loading owner-bound state.
                            // Existing laboratory61 scene transport stays separately gated.
                            if(beast_view_operation){
                                const auto empty=[](){return std::optional<std::vector<std::uint8_t>>(std::vector<std::uint8_t>{});};
                                if(const auto* close=std::get_if<RecoveredBeastExploration::Close>(&*beast_view_operation)){
                                    const bool closed=beast_exploration.close(session.id(),session.account_id,session.character_id,*close);
                                    spdlog::info("OWNED_BEAST_EXPLORATION_VIEW_CLOSE session_id={} matched={} CUSTOM0085 no_activity_change",session.id(),closed);return empty();
                                }
                                if(!beast_view_selected||!beast_view_position||!session.recovered_world_ready()||
                                   (session.state()!=SessionState::CharacterSelected&&session.state()!=SessionState::InWorld)||
                                   !owned_beasts_projected.contains(session.id())||trade_active(session.id())||diagnostic_town_scene_pending.contains(session.id())||diagnostic_island_return_pending.contains(session.id())||
                                   recovered_movement->current_location(session.id(),session.account_id,session.character_id)!=beast_view_position)return empty();
                                try{
                                    if(supply_repository.owned_pending_battle(session.account_id,session.character_id)||
                                       database.beast_snapshots().load_selected(session.account_id,session.character_id)!=beast_view_selected)return empty();
                                    auto wire=beast_exploration.open(session.id(),session.account_id,session.character_id,*beast_view_position,std::get<RecoveredBeastPanel::Request>(*beast_view_operation),*beast_view_selected);
                                    if(!wire)return empty();
                                    spdlog::info("OWNED_BEAST_EXPLORATION_VIEW_OPEN session_id={} character_id={} CUSTOM0085 existing_C5_only no_activity_change",session.id(),session.character_id);
                                    return std::optional<std::vector<std::uint8_t>>(std::move(*wire));
                                }catch(const DatabaseError& error){spdlog::warn("OWNED_BEAST_EXPLORATION_VIEW_DENIED session_id={} reason={}",session.id(),error.what());return empty();}
                            }
                            if(config.owned_beast_panel_enabled&&OwnedBeastPanelService::handles(records)) {
                                const auto empty=[](){return std::optional<std::vector<std::uint8_t>>(std::vector<std::uint8_t>{});};
                                const auto use=OwnedBeastPanelService::request(records);
                                if(!use||!session.account_id||!session.character_id||!session.recovered_world_ready()||
                                   (session.state()!=SessionState::CharacterSelected&&session.state()!=SessionState::InWorld)||
                                   !owned_beasts_projected.contains(session.id())||trade_active(session.id())||
                                   diagnostic_town_scene_pending.contains(session.id())||diagnostic_island_return_pending.contains(session.id())||
                                   !recovered_movement->current_location(session.id(),session.account_id,session.character_id))return empty();
                                try {
                                    auto wire=database.beast_snapshots().open_owned_panel(session.account_id,session.character_id,use->raw_slot,use->client_item_id);
                                    if(!wire)return empty();
                                    spdlog::info("OWNED_BEAST_PANEL_OPEN session_id={} character_id={} slot={} item={} CUSTOM-0085 display_only",session.id(),session.character_id,use->raw_slot,use->client_item_id);
                                    return std::optional<std::vector<std::uint8_t>>(std::move(*wire));
                                } catch(const DatabaseError& error){
                                    spdlog::warn("OWNED_BEAST_PANEL_DENIED session_id={} reason={}",session.id(),error.what());return empty();
                                }
                            }
                            // CUSTOM-0087: the native 68 00 control carries no
                            // item identity. Reopen the existing map panel only
                            // from a currently owned, source-qualified regional
                            // map in the saved bag. The original 68->3F pairing
                            // remains unproven; no item or saved state changes.
                            if(config.owned_map_views_enabled && !config.diagnostic_town_scene_probe &&
                               std::any_of(records.begin(),records.end(),[](const auto& record) {
                                   return std::holds_alternative<RecoveredMapPanelControl68::Request>(record);
                               })) {
                                const auto empty=[](){return std::optional<std::vector<std::uint8_t>>(std::vector<std::uint8_t>{});};
                                if(!RecoveredOwnedMapView::map_panel68_request(records) ||
                                   !session.account_id || !session.character_id ||
                                   !session.recovered_world_ready() ||
                                   (session.state()!=SessionState::CharacterSelected && session.state()!=SessionState::InWorld) ||
                                   !owned_bag_projected.contains(session.id()) || trade_active(session.id()) ||
                                   diagnostic_town_scene_pending.contains(session.id()) ||
                                   diagnostic_island_return_pending.contains(session.id()) ||
                                   supply_repository.owned_pending_battle(session.account_id,session.character_id))return empty();
                                const auto position=recovered_movement->current_location(session.id(),session.account_id,session.character_id);
                                if(!position)return empty();
                                const auto item=RecoveredOwnedMapView::map_item_for_scene(position->area,position->scene);
                                if(!item || !database.native_map_item_catalog().contains(*item))return empty();
                                const auto map=database.native_map_catalog().lookup(NativeMapCatalog::current_dataset_id,position->area,position->scene);
                                if(!map || !RecoveredOwnedMapView::qualified_map(*map,*item))return empty();
                                for(std::uint8_t slot=0;slot<30;++slot) {
                                    const auto owned=supply_repository.load_inventory_slot(session.account_id,session.character_id,slot);
                                    if(!owned)continue;
                                    const auto logical=RecoveredOwnedMapView::logical({*item,slot,0},*owned,*map,true);
                                    if(!logical)continue;
                                    spdlog::info("OWNED_MAP_PANEL68_OPEN session_id={} character_id={} item={} slot={} area={} scene={} revision={} CUSTOM-0087 no_consumption native_pairing_unproven",
                                        session.id(),session.character_id,*item,slot,position->area,position->scene,owned->revision);
                                    return std::optional<std::vector<std::uint8_t>>(RecoveredWorldFrame::encode(*logical));
                                }
                                return empty();
                            }
                            if(config.owned_map_views_enabled && !config.diagnostic_town_scene_probe &&
                               std::any_of(records.begin(),records.end(),[](const auto& record) {
                                   const auto* use=std::get_if<RecoveredInventoryItemRequest::Request>(&record);
                                   return use && RecoveredOwnedMapView::supported(use->client_item_id);
                               })) {
                                const auto use=RecoveredOwnedMapView::request(records);
                                if(!use || use->raw_slot>=30 || !session.recovered_world_ready() ||
                                   (session.state()!=SessionState::CharacterSelected && session.state()!=SessionState::InWorld) ||
                                   !owned_bag_projected.contains(session.id()) ||
                                   diagnostic_town_scene_pending.contains(session.id()) ||
                                   diagnostic_island_return_pending.contains(session.id()))
                                    return std::optional<std::vector<std::uint8_t>>(std::vector<std::uint8_t>{});
                                const auto position=recovered_movement->current_location(session.id(),session.account_id,session.character_id);
                                const auto owned=supply_repository.load_inventory_slot(session.account_id,session.character_id,use->raw_slot);
                                if(!position || !owned)return std::optional<std::vector<std::uint8_t>>(std::vector<std::uint8_t>{});
                                const auto map=database.native_map_catalog().lookup(NativeMapCatalog::current_dataset_id,position->area,position->scene);
                                if(!map)return std::optional<std::vector<std::uint8_t>>(std::vector<std::uint8_t>{});
                                const auto logical=RecoveredOwnedMapView::logical(*use,*owned,*map,
                                    database.native_map_item_catalog().contains(use->client_item_id));
                                if(!logical)return std::optional<std::vector<std::uint8_t>>(std::vector<std::uint8_t>{});
                                spdlog::info("OWNED_MAP_VIEW_OPEN session_id={} character_id={} item={} slot={} area={} scene={} revision={} CUSTOM-0044 no_consumption",
                                    session.id(),session.character_id,use->client_item_id,use->raw_slot,position->area,position->scene,owned->revision);
                                return std::optional<std::vector<std::uint8_t>>(RecoveredWorldFrame::encode(*logical));
                            }
                            // CUSTOM-0043: isolated mode4 roundtrip only. This branch
                            // neither spawns an NPC nor mutates any quest or reward.
                            if(config.diagnostic_knowledge_menu && knowledge_conversations.contains(session.id()) &&
                               session.recovered_world_ready() && session.state()!=SessionState::InBattle &&
                               std::any_of(records.begin(),records.end(),[](const auto& record) {
                                   return std::holds_alternative<RecoveredQuestAction::Request>(record) ||
                                       std::holds_alternative<RecoveredQuestClose::Request>(record);
                               })) {
                                unsigned actions=0,closes=0;
                                for(const auto& record:records) {
                                    if(std::holds_alternative<RecoveredWorldRecords::Tick>(record))continue;
                                    if(std::holds_alternative<RecoveredQuestAction::Request>(record)) {if(++actions>1 || closes)return std::optional<std::vector<std::uint8_t>>{};}
                                    else if(std::holds_alternative<RecoveredQuestClose::Request>(record)) {if(++closes>1)return std::optional<std::vector<std::uint8_t>>{};}
                                    else return std::optional<std::vector<std::uint8_t>>{};
                                }
                                for(const auto& record:records) {
                                    if(const auto* action=std::get_if<RecoveredQuestAction::Request>(&record)) {
                                        const auto choice=knowledge_conversations.consume(session.id(),session.account_id,session.character_id,*action);
                                        if(!choice)return std::optional<std::vector<std::uint8_t>>{};
                                        spdlog::info("KNOWLEDGE_MENU_CHOICE session_id={} character_id={} choice={} request={} context={} CUSTOM-0043 no_quest_mutation",
                                            session.id(),session.character_id,*choice,action->request_word,action->context_byte);
                                    } else if(std::holds_alternative<RecoveredQuestClose::Request>(record)) {
                                        if(!knowledge_conversations.close(session.id(),session.account_id,session.character_id))return std::optional<std::vector<std::uint8_t>>{};
                                        spdlog::info("KNOWLEDGE_MENU_CLOSED session_id={} CUSTOM-0043",session.id());
                                    }
                                }
                                return std::optional<std::vector<std::uint8_t>>(std::vector<std::uint8_t>{});
                            }
                            // Restore saved player values before binding any deity row.
                            // Native24 can subtract HP from an already selected companion,
                            // so this runs once on a fresh world, never on later idle ticks.
                            if(!owned_player_and_companions_projected.contains(session.id()) &&
                               session.state()!=SessionState::InBattle && records.size()==1 &&
                               std::holds_alternative<RecoveredWorldRecords::Tick>(records.front())) {
                                const auto admission=recovered_world->handle(session,records);
                                if(!admission) return admission;
                                const auto player=RecoveredPlayerSnapshot::load_for_world_entry(
                                    database.recovered_characters(),session.account_id,session.character_id);
                                const auto actual_session=session.weak_from_this().lock();
                                if(actual_session.get()!=&session)throw DatabaseError("Owned companion source requires actual Session");
                                const auto companions=std::make_shared<const RecoveredOwnedCompanions::Restoration>(
                                    owned_companions.restore_with_source(session.account_id,session.character_id));
                                const auto& roster=companions->deity_roster();
                                if(roster.account()!=session.account_id || roster.character()!=session.character_id)
                                    throw DatabaseError("Owned companion restoration owner changed");
                                const auto lineage=std::make_shared<OwnedCompanionRestorationSource>(
                                    OwnedCompanionRestorationSource{actual_session,roster.account(),roster.character(),
                                        session.battle_generation(),session.state(),companions});
                                // Bind the actual normal-entry epoch to this
                                // saved readset and its exact later writes.
                                // Missing passive metadata preserves old restore
                                // behavior, but cannot qualify initialization.
                                lineage->normal_initialization=session.normal_world_initialization();
                                if(const auto at=owned_companion_restoration_sources.find(session.id());
                                   at!=owned_companion_restoration_sources.end() && at->second->session.lock().get()!=&session)
                                    throw DatabaseError("Owned companion source Session incarnation conflict");
                                owned_companion_restoration_sources.insert_or_assign(session.id(),lineage);
                                const auto journal=database.quest_journals().load(session.account_id,session.character_id);
                                std::optional<RecoveredQuestSync::EmptyJournal> journal_logical;
                                if(journal) {
                                    const auto counts=supply_repository.load_quest_description_counts();
                                    journal_logical=RecoveredQuestSync::encodeJournalLogical(journal->values,counts);
                                    if(!journal_logical)throw DatabaseError("Owned quest journal reference rejected");
                                }
                                const auto auxiliary=database.role_auxiliary().load(session.account_id,session.character_id);
                                const auto weapons=config.owned_weapon_transfers_enabled?
                                    database.weapon_slots().load_saved(session.account_id,session.character_id):std::vector<StoredWeaponSlot>{};
                                const auto armor=config.owned_armor_transfers_enabled?
                                    database.armor_slots().load_saved(session.account_id,session.character_id):std::vector<StoredArmorSlot>{};
                                if(player) session.send_world_records(player->logical_before_companion_binding);
                                if(config.diagnostic_shunying_manual && session.character_id==config.diagnostic_shunying_character_id) {
                                    const auto owned=database.recovered_characters().list_for_account(session.account_id);
                                    const auto found=std::find_if(owned.begin(),owned.end(),[&](const auto& row){return row.id==session.character_id;});
                                    const std::array<std::uint8_t,5> test_name{'t','e','s','t',0};
                                    if(session.account_id!=6 || session.character_id!=6 || found==owned.end() ||
                                       !std::equal(test_name.begin(),test_name.end(),found->profile.begin()))
                                        throw DatabaseError("Shunying equipment fixture requires the authorized test character");
                                    session.send_world_records(DiagnosticShunyingEquipment::projection());
                                    spdlog::info("SHUNYING_TEST_EQUIPMENT character_id=6 slots=30,31,32,33,34 CUSTOM-0058");
                                }
                                if(config.owned_supply_enabled && player) {
                                    std::vector<std::uint8_t> inventory;std::size_t projected=0;
                                    for(const auto& [index,slot]:supply_repository.load_saved_supply_slots(session.account_id,session.character_id)) {
                                        if(slot.source_sha256!=supply_source || (slot.count && !database.native_supply_catalog().lookup(slot.item_id)))continue;
                                        const auto logical=bag_slot_projection(index,slot);
                                        inventory.insert(inventory.end(),logical.begin(),logical.end());++projected;
                                    }
                                    if(!inventory.empty())session.send_world_records(inventory);
                                    owned_supply_projected.insert(session.id());
                                    if(projected)owned_bag_projected.insert(session.id());
                                    spdlog::info("OWNED_SUPPLY_SLOTS_RESTORED session_id={} character_id={} slots={} CUSTOM-0050 no_grants",session.id(),session.character_id,projected);
                                }
                                if(auxiliary) {
                                    session.send_world_records(std::vector<std::uint8_t>(auxiliary->logical.begin(),auxiliary->logical.end()));
                                    spdlog::info("OWNED_ROLE_AUXILIARY_RESTORED session_id={} character_id={} revision={} origin={} CUSTOM-0045 no_formula no_grant",session.id(),session.character_id,auxiliary->revision,auxiliary->origin);
                                }
                                if(config.owned_weapon_transfers_enabled) {
                                    std::vector<std::uint8_t> inventory;
                                    for(const auto& slot:weapons) {
                                        const auto projection=OwnedWeaponTransferService::slot_logical(slot);
                                        inventory.insert(inventory.end(),projection.begin(),projection.end());
                                    }
                                    if(!inventory.empty())session.send_world_records(inventory);
                                    owned_weapons_projected.insert(session.id());
                                    spdlog::info("OWNED_WEAPON_SLOTS_RESTORED session_id={} character_id={} slots={} CUSTOM-0046 instance_only no_grant",session.id(),session.character_id,weapons.size());
                                }

                                if(config.owned_armor_transfers_enabled) {
                                    std::vector<std::uint8_t> inventory;
                                    const auto snapshot=database.armor_slots().load_snapshot(session.account_id,session.character_id);
                                    for(std::uint8_t index=0;index<30;++index)if(snapshot.scalar[index]){
                                        const auto cell=owner_bag_projector->project(session.account_id,session.character_id,index,*snapshot.scalar[index]);inventory.insert(inventory.end(),cell.begin(),cell.end());
                                    }
                                    for(const auto& row:armor)if(row.slot>=30){const auto cell=OwnedArmorTransferService::slot_logical(row);inventory.insert(inventory.end(),cell.begin(),cell.end());}
                                    if(!inventory.empty())session.send_world_records(std::move(inventory));
                                    owned_armor_projected.insert(session.id());owned_bag_projected.insert(session.id());
                                    spdlog::info("OWNED_ARMOR_SLOTS_RESTORED session_id={} account={} character={} slots={} CUSTOM-0066 instance_only no_grant",session.id(),session.account_id,session.character_id,armor.size());
                                }
                                if(config.owned_beast_panel_enabled&&player) {
                                    const auto restored=database.beast_snapshots().restore(session.account_id,session.character_id);
                                    if(!restored.logical.empty())session.send_world_records(restored.logical);
                                    owned_beasts_projected.insert(session.id());
                                    spdlog::info("OWNED_BEASTS_RESTORED session_id={} character_id={} instances={} selected={} CUSTOM-0085 no_grant",session.id(),session.character_id,restored.instances.size(),restored.selected.has_value());
                                }
                                if(config.owned_teleport_gem_enabled) {
                                    const auto gems=database.teleport_gems().load_saved(session.account_id,session.character_id);
                                    std::vector<std::uint8_t> logical;
                                    for(const auto& gem:gems) {
                                        const auto bytes=gem_projection(gem);
                                        logical.insert(logical.end(),bytes.begin(),bytes.end());
                                    }
                                    if(!logical.empty())session.send_world_records(std::move(logical));
                                    owned_gems_projected.insert(session.id());
                                    spdlog::info("OWNED_TELEPORT_GEM_RESTORED session_id={} character_id={} slots={} CUSTOM-0057 no_grant",session.id(),session.character_id,gems.size());
                                }
                                // Requalify the complete saved roster at its real
                                // sender after unrelated world-entry observers.
                                // Passive handles observe exact async writes;
                                // call-return counts remain submission attempts.
                                const auto source_local=[&] {
                                    const auto at=owned_companion_restoration_sources.find(session.id());
                                    return at!=owned_companion_restoration_sources.end() && at->second==lineage &&
                                        lineage->session.lock().get()==&session && !session.closing() &&
                                        lineage->account==session.account_id && lineage->character==session.character_id &&
                                        lineage->phase_at_restore==session.state() && session.recovered_world_ready() &&
                                        lineage->battle_generation_at_restore==session.battle_generation();
                                };
                                if(!source_local() || !owned_companions.restoration_current(*companions) || !source_local())
                                    throw DatabaseError("Owned companion restoration source stale before submission");
                                for(const auto& logical:companions->batches()) {
                                    if(!source_local())throw DatabaseError("Owned companion restoration source changed during submission");
                                    lineage->write_observations.push_back(session.send_world_records_observed(logical));
                                    ++lineage->submission_calls_completed;
                                }
                                lineage->all_submission_calls_returned=true;
                                if(config.diagnostic_shunying_manual && session.account_id==6 &&
                                   session.character_id==config.diagnostic_shunying_character_id) {
                                    const auto deity=DiagnosticShunyingFemaleDeity::world_appearance(session.character_id);
                                    session.send_world_records(std::vector<std::uint8_t>(deity.begin(),deity.end()));
                                    spdlog::info("SHUNYING_TEST_FEMALE_DEITY character_id=6 deity_key=102 CUSTOM-0058");
                                }
                                if(const auto saved_text=database.role_text().load(session.account_id,session.character_id)) {
                                    const auto projected_text=SqliteRoleTextRepository::project(*saved_text,
                                        session.recovered_client_language()==1?936:950);
                                    if(projected_text) {
                                        const auto logical=RecoveredRoleText::update(*projected_text);
                                        if(!logical)throw DatabaseError("Secondary role text projection rejected");
                                        session.send_world_records(std::vector<std::uint8_t>(logical->begin(),logical->end()));
                                        spdlog::info("OWNED_ROLE_TEXT_RESTORED session_id={} character_id={} revision={} CUSTOM-0056",
                                            session.id(),session.character_id,saved_text->revision);
                                    } else {
                                        spdlog::warn("OWNED_ROLE_TEXT_DISPLAY_UNAVAILABLE session_id={} character_id={} revision={} no_saved_data_change",
                                            session.id(),session.character_id,saved_text->revision);
                                    }
                                }
                                if(journal_logical) {
                                    session.send_world_records(std::vector<std::uint8_t>(journal_logical->begin(),journal_logical->end()));
                                    spdlog::info("OWNED_QUEST_JOURNAL_RESTORED session_id={} character_id={} revision={} origin={} CUSTOM-0041 no_reward_mutation",
                                        session.id(),session.character_id,journal->revision,journal->origin);
                                }
                                owned_player_and_companions_projected.insert(session.id());
                                // Native2D follows the completed owned player
                                // projection in this batch, without waiting for
                                // the client's next heartbeat or chat action.
                                sync_guild_name(session,true);
                                sync_guild_roster(session);
                                // Exclusive candidate lab only: third disposable
                                // applicant exercises native72 rejection without
                                // SQL-seeding guilds, members or applications.
                                const bool guild_lab_reject_fixture=[&] {
                                    if(!guild_membership_lab || !guild_membership || session.account_id!=6 || session.character_id!=6)return false;
                                    const auto account=database.accounts().find_by_id(6);
                                    if(!account || account->username!="god2-bytes:636f64657872656a656374")return false;
                                    try {
                                        return guild_membership_repository->identity(6,6).name_utf8=="rejectgirl";
                                    }catch(const DatabaseError&){return false;}
                                }();
                                if(guild_membership_lab && guild_membership && !guild_succession && !guild_entry_lab && (session.character_id==4 || session.character_id==5 || guild_lab_reject_fixture) &&
                                   !guild_lab_prompted.contains(session.id())) {
                                    const auto operation=session.character_id==4?RecoveredGuildMembership::Operation::Create:
                                        RecoveredGuildMembership::Operation::Join;
                                    const auto prompt=guild_membership->open(session.id(),operation,OwnedGuildMembershipConversation::Clock::now(),true);
                                    if(prompt) {
                                        guild_lab_prompted.insert(session.id());
                                        session.send_world_records(std::vector<std::uint8_t>(prompt->begin(),prompt->end()));
                                        spdlog::info("OWNED_GUILD_MEMBERSHIP_PROMPT session_id={} character_id={} operation={} context={} CUSTOM-0078 TEST_ONLY_AUTO_ENTRY no_original_npc_claim",
                                            session.id(),session.character_id,static_cast<unsigned>(operation),(*prompt)[1]+256u*(*prompt)[2]);
                                    }
                                }
                                if(config.diagnostic_knowledge_menu) {
                                    const auto source_count=database.native_multi_message_catalog().knowledge_menu_count();
                                    const auto menu=knowledge_conversations.open(session.id(),session.account_id,session.character_id,0,0x44,source_count);
                                    if(!menu)throw DatabaseError("Knowledge menu binding rejected");
                                    session.send_world_records(std::vector<std::uint8_t>(menu->begin(),menu->end()));
                                    spdlog::info("KNOWLEDGE_MENU_OPENED session_id={} key=1434 request=0 context=68 CUSTOM-0043 no_npc_spawn no_quest_mutation",session.id());
                                }
                                if(config.world_clock_enabled) {
                                    send_world_clock(session);
                                    world_clock_sessions.insert_or_assign(session.id(),ClockPeer{
                                        session.shared_from_this(),std::chrono::steady_clock::now()});
                                }
                                spdlog::info("OWNED_WORLD_SNAPSHOT_RESTORED session_id={} character_id={} saved_player={} companion_batches={}",
                                    session.id(),session.character_id,player.has_value(),companions.size());
                            }
                            // Restore explicitly qualified71/72 records after scene admission.
                            // Empty source means no actors; never infer spawn rows from catalogs.
                            if(records.size()==1 &&
                               std::holds_alternative<RecoveredWorldRecords::Tick>(records.front())) {
                                for(const auto& batch:world_display_batches(session))session.send_world_records(batch);
                            }
                            if(records.size()==1 &&
                               (std::holds_alternative<RecoveredWorldRecords::ClientOpaque74>(records.front()) ||
                                std::holds_alternative<RecoveredWorldRecords::ClientPanelOpen88>(records.front()))) {
                                const auto opcode=std::holds_alternative<RecoveredWorldRecords::ClientOpaque74>(records.front())?0x74:0x88;
                                auto result=recovered_world->handle(session,records);
                                if(result && result->empty())
                                    spdlog::info("NATIVE_PANEL_TRANSPORT_ADMITTED session_id={} opcode={:02x} no_state_change no_reply",session.id(),opcode);
                                return result;
                            }
                            if(records.size()==1 &&
                               std::holds_alternative<RecoveredWorldRecords::ClientOptionsNotification>(records.front())) {
                                auto result=recovered_world->handle(session,records);
                                if(result && result->empty()) {
                                    const auto& bytes=std::get<RecoveredWorldRecords::ClientOptionsNotification>(records.front()).payload;
                                    spdlog::info("NATIVE_OPTIONS_TRANSPORT_ADMITTED session_id={} flags={:04x} no_state_change no_reply",
                                        session.id(),static_cast<unsigned>(bytes[0])|(static_cast<unsigned>(bytes[1])<<8));
                                }
                                return result;
                            }
                            if(records.size()==1 &&
                               std::holds_alternative<RecoveredWorldRecords::ClientPoseNotification>(records.front())) {
                                auto result=recovered_world->handle(session,records);
                                // CUSTOM-0103: battle77 carries an owned symbol,
                                // not a world posture. Preserve the existing
                                // world presence/movement branch for world only.
                                if(session.state()==SessionState::InBattle)return result;
                                if(result && !result->empty() && player_presence_enabled) {
                                    const auto location=recovered_movement->current_location(
                                        session.id(),session.account_id,session.character_id);
                                    if(location) {
                                        const auto& pose=std::get<RecoveredWorldRecords::ClientPoseNotification>(records.front());
                                        if(player_visibility.contains(session.id())) {
                                            deliver_visibility(player_visibility.set_pose(session.id(),session.account_id,
                                                session.character_id,{location->area,location->scene},pose.payload));
                                            spdlog::debug("NATIVE_POSE_PUBLISHED session_id={} character_id={} mode={} direction={}",
                                                session.id(),session.character_id,pose.payload[1]>>3,pose.payload[1]&7u);
                                        } else if(const auto pending=pending_visibility.find(session.id());
                                            pending!=pending_visibility.end() && pending->second.account==session.account_id &&
                                            pending->second.character==session.character_id &&
                                            pending->second.location==RecoveredVisibility::Scene{location->area,location->scene}) {
                                            if(RecoveredCharacterPose::is_persistent_pose(pose.payload))
                                                pending->second.pose=std::array<std::uint8_t,3>{0,pose.payload[1],0};
                                            else pending->second.pose.reset();
                                        }
                                    }
                                }
                                return result;
                            }
                            if(records.size()==1 &&
                               (std::holds_alternative<RecoveredWorldRecords::ClientControl1F>(records.front()) ||
                                std::holds_alternative<RecoveredWorldRecords::ClientControl6D>(records.front())))
                                return recovered_world->handle(session,records);
                            if(std::any_of(records.begin(),records.end(),[](const auto& record) {
                                if(std::holds_alternative<RecoveredInventoryMoveRequest::Request>(record) ||
                                   std::holds_alternative<RecoveredDeitySelection::Request>(record)) return true;
                                const auto* selection=std::get_if<RecoveredSelectionItemRequest::Request>(&record);
                                return selection && selection->raw_slot>=42 && selection->raw_slot<=44;
                            })) return recovered_world->handle(session,records);
                            if(config.diagnostic_town_door_routes && diagnostic_town_scene_pending.contains(session.id())) {
                                // A native periodic tick can arrive before the destination
                                // context receipt, including before the first guide/presence
                                // tick after login. Do not run world admission while movement
                                // still has transfer_pending: current_location is unavailable.
                                if(records.size()==1 &&
                                   std::holds_alternative<RecoveredWorldRecords::Tick>(records.front()))
                                    return std::optional<std::vector<std::uint8_t>>(std::vector<std::uint8_t>{});
                                spdlog::warn("DIAGNOSTIC_DOOR_PENDING_BATCH session_id={} state={} records={} first_variant={} second_variant={}",
                                    session.id(),static_cast<int>(session.state()),records.size(),
                                    records.empty()?99:records.front().index(),records.size()<2?99:records[1].index());
                                if(records.size()==2) if(const auto* move=std::get_if<RecoveredMovement::Request>(&records[1]))
                                    spdlog::warn("DIAGNOSTIC_DOOR_PENDING_NEXT_MOVE session_id={} x={} y={} sequence={}",
                                        session.id(),move->x,move->y,static_cast<unsigned>(move->sequence));
                            }
                            if(session.state()!=SessionState::InBattle &&
                               std::any_of(records.begin(),records.end(),[](const auto& record) {
                                   return std::holds_alternative<RecoveredChat::Request>(record);
                               }) &&
                               std::all_of(records.begin(),records.end(),[](const auto& record) {
                                   return std::holds_alternative<RecoveredChat::Request>(record) ||
                                          std::holds_alternative<RecoveredWorldRecords::Tick>(record) ||
                                          std::holds_alternative<RecoveredMovement::Request>(record);
                               })) {
                                    const auto source_location=recovered_movement->current_location(
                                        session.id(),session.account_id,session.character_id);
                                    if(!source_location || !session.recovered_world_ready() ||
                                       session.character_id>UINT32_MAX ||
                                       !native_chat_sessions.contains(session.id()))
                                        return std::optional<std::vector<std::uint8_t>>{};
                                    // A chat may precede the first standalone periodic tick.
                                    // Publish already-owned presence here, after the world
                                    // tail has been accepted, rather than rejecting the chat
                                    // and disconnecting every player who speaks immediately.
                                    // 6F must precede5C so peers can also bind the bubble.
                                    const auto admit_chat_presence=[&](Session& peer,const RecoveredPosition& position) {
                                        if(!config.diagnostic_town_player_visibility || player_visibility.contains(peer.id()))return true;
                                        if(!peer.recovered_world_ready() ||
                                           diagnostic_town_scene_pending.contains(peer.id()) ||
                                           diagnostic_island_return_pending.contains(peer.id()))return false;
                                        const auto pending=pending_visibility.find(peer.id());
                                        if(pending==pending_visibility.end() || pending->second.session!=peer.id() ||
                                           pending->second.account!=peer.account_id || pending->second.character!=peer.character_id ||
                                           pending->second.location!=RecoveredVisibility::Scene{position.area,position.scene})return false;
                                        const auto projected=visibility_at(pending->second,position);
                                        const auto deliveries=player_visibility.enter(projected);
                                        visibility_sessions.insert_or_assign(peer.id(),peer.shared_from_this());
                                        pending_visibility.erase(pending);
                                        deliver_visibility(deliveries);
                                        spdlog::info("NATIVE_CHAT_PRESENCE_READY session_id={} character_id={} area={} scene={} before_periodic_tick",
                                            peer.id(),peer.character_id,position.area,position.scene);
                                        return true;
                                    };
                                    if(!admit_chat_presence(session,*source_location))
                                        return std::optional<std::vector<std::uint8_t>>{};
                                    if(!native_chat_text) native_chat_text.emplace(config.chinese_dictionary_root);
                                    const auto owned=database.recovered_characters().list_for_account(session.account_id);
                                    const auto speaker=std::find_if(owned.begin(),owned.end(),[&](const auto& character) {
                                        return character.id==session.character_id;
                                    });
                                    if(speaker==owned.end()) return std::optional<std::vector<std::uint8_t>>{};
                                    const auto name_end=std::find(speaker->profile.begin(),speaker->profile.begin()+15,0);
                                    if(name_end==speaker->profile.begin() || name_end==speaker->profile.begin()+15)
                                        return std::optional<std::vector<std::uint8_t>>{};
                                    const auto speaker_name=LegacyChineseCodec::decode(std::string_view(
                                        reinterpret_cast<const char*>(speaker->profile.data()),
                                        static_cast<std::size_t>(name_end-speaker->profile.begin())),
                                        speaker->name_codepage==936);
                                    struct Delivery { std::shared_ptr<Session> recipient; std::vector<std::uint8_t> logical; };
                                    std::vector<Delivery> deliveries;
                                    std::size_t chat_bytes=0;
                                    for(const auto& record:records) {
                                        const auto* chat=std::get_if<RecoveredChat::Request>(&record);
                                        if(!chat) continue;
                                        chat_bytes+=chat->legacy_text.size();
                                        const auto unicode=LegacyChineseCodec::decode(chat->legacy_text,
                                            session.recovered_client_language()==1);
                                        if(unicode.find('\0')!=std::string::npos)
                                            return std::optional<std::vector<std::uint8_t>>{};
                                        for(const auto& [id,weak]:native_chat_sessions) {
                                            auto peer=weak.lock();
                                            if(!peer || !peer->recovered_world_ready() ||
                                               peer->state()==SessionState::InBattle)
                                                continue;
                                            const auto peer_location=recovered_movement->current_location(id,peer->account_id,peer->character_id);
                                            if(!peer_location || peer_location->area!=source_location->area ||
                                               peer_location->scene!=source_location->scene ||
                                               !admit_chat_presence(*peer,*peer_location))continue;
                                            const bool simplified=peer->recovered_client_language()==1;
                                            const auto translated=native_chat_text->convert(unicode,
                                                simplified?ChineseLanguage::Simplified:ChineseLanguage::Traditional);
                                            const auto encoded=LegacyChineseCodec::encode_display(speaker_name+": "+translated,simplified);
                                            if(encoded.replacements || encoded.truncated)
                                                spdlog::warn("NATIVE_CHAT_DISPLAY_LOSS sender={} recipient={} replacements={} truncated={}",
                                                    session.character_id,peer->character_id,
                                                    encoded.replacements,encoded.truncated);
                                            deliveries.push_back({std::move(peer),RecoveredChat::display(
                                                static_cast<std::uint32_t>(session.character_id),simplified,encoded.bytes)});
                                            if(config.streamer_privileges_enabled)
                                                StreamerPresentation::annotate(deliveries.back().logical,speaker->streamer_privilege);
                                        }
                                    }
                                    std::vector<RecoveredWorldRecords::Record> movement_records;
                                    for(const auto& record:records)
                                        if(std::holds_alternative<RecoveredMovement::Request>(record) ||
                                           std::holds_alternative<RecoveredWorldRecords::Tick>(record))
                                            movement_records.push_back(record);
                                    std::optional<std::vector<std::uint8_t>> movement_reply=
                                        std::vector<std::uint8_t>{};
                                    const bool has_movement=std::any_of(movement_records.begin(),movement_records.end(),[](const auto& record) {
                                           return std::holds_alternative<RecoveredMovement::Request>(record);
                                       });
                                    if(has_movement) {
                                        movement_reply=recovered_world->handle(session,movement_records);
                                        if(!movement_reply) return movement_reply;
                                    }
                                    for(auto& delivery:deliveries) {
                                        if(has_movement && delivery.recipient->id()==session.id()) {
                                            // Keep the sender's ACK before its own chat on the same
                                            // connection, even when both records share one native frame.
                                            const auto wire=RecoveredWorldFrame::encode(delivery.logical);
                                            movement_reply->insert(movement_reply->end(),wire.begin(),wire.end());
                                        } else {
                                            delivery.recipient->send_world_records(std::move(delivery.logical));
                                        }
                                    }
                                    spdlog::info("NATIVE_CHAT_ACCEPTED session_id={} characters={} legacy_bytes={} recipients={}",
                                        session.id(),
                                        std::count_if(records.begin(),records.end(),[](const auto& record) {
                                            return std::holds_alternative<RecoveredChat::Request>(record);
                                        }),chat_bytes,deliveries.size());
                                    return movement_reply;
                            }
                            if(config.diagnostic_visibility_battle && pending_visibility_refresh.contains(session.id()) &&
                               session.state()==SessionState::InWorld && records.size()==1 &&
                               std::holds_alternative<RecoveredWorldRecords::Tick>(records.front())) {
                                auto accepted=recovered_world->handle(session,records);
                                if(!accepted) return accepted;
                                for(const auto& delivery:player_visibility.refresh(session.id(),session.account_id,
                                        session.character_id,{2,15})) {
                                    const auto wire=RecoveredWorldFrame::encode(delivery.logical);
                                    accepted->insert(accepted->end(),wire.begin(),wire.end());
                                    if(const auto spawn=RecoveredRemoteActor::parse_logical(delivery.logical))
                                        if(const auto pose=player_visibility.pose_after_spawn(*spawn)) {
                                            const auto pose_wire=RecoveredWorldFrame::encode(*pose);
                                            accepted->insert(accepted->end(),pose_wire.begin(),pose_wire.end());
                                        }
                                }
                                pending_visibility_refresh.erase(session.id());
                                return accepted;
                            }
                            if(config.diagnostic_player_visibility && !player_visibility.contains(session.id())) {
                                if(records.size()!=1 || !std::holds_alternative<RecoveredWorldRecords::Tick>(records.front()))
                                    return std::optional<std::vector<std::uint8_t>>{};
                                auto accepted=recovered_world->handle(session,records);
                                if(!accepted) return accepted;
                                const auto pending=pending_visibility.find(session.id());
                                if(pending==pending_visibility.end())
                                    throw std::runtime_error("Visibility world preparation missing");
                                visibility_sessions.insert_or_assign(session.id(),session.shared_from_this());
                                auto deliveries=player_visibility.enter(pending->second);
                                pending_visibility.erase(pending);
                                deliver_visibility(std::move(deliveries));
                                return accepted;
                            }
                            if(config.diagnostic_remote_actor) {
                                // CUSTOM-0026: stationary single-owner socket qualification only.
                                if(records.size()!=1 || !std::holds_alternative<RecoveredWorldRecords::Tick>(records.front()))
                                    return std::optional<std::vector<std::uint8_t>>{};
                                auto accepted=recovered_world->handle(session,records);
                                if(!accepted) return accepted;
                                const auto position=database.recovered_characters().load_position(session.account_id,session.character_id);
                                // Fresh indoor bootstrap is17/13; no save exists until the first move.
                                // This mode rejects movement and competing spawn/transfer diagnostics.
                                if(session.character_id!=1 || (position && (position->area!=2 || position->scene!=15 ||
                                   position->x!=17 || position->y!=13)))
                                    return std::optional<std::vector<std::uint8_t>>{};
                                auto& ticks=diagnostic_remote_ticks[session.id()];
                                if(ticks>=29) return accepted;
                                ++ticks;
                                if(ticks%2==0) return accepted;
                                if(ticks>=3 && ticks<=25) {
                                    const auto phase=(ticks-3)/2;
                                    const auto status=static_cast<std::uint16_t>(phase%2 ? 0u : phase==10 ? 1u : 0x100u<<(phase/2));
                                    const auto logical=DiagnosticRemoteActor::status(status);
                                    const auto wire=RecoveredWorldFrame::encode(logical);
                                    accepted->insert(accepted->end(),wire.begin(),wire.end());
                                    spdlog::warn("DIAGNOSTIC_REMOTE_STATUS session_id={} status={} CUSTOM-0026",session.id(),status);
                                    return accepted;
                                }
                                const auto stage=ticks==1 ? 0u : ticks==27 ? 1u : 2u;
                                auto logical=DiagnosticRemoteActor::logical(stage,config.diagnostic_remote_actor_language);
                                if(stage==0) {
                                    const auto record=RecoveredRemoteActor::parse_logical(logical);
                                    const auto projected=record ? RecoveredRemoteActor::with_normal_world_components(
                                        *record,diagnostic_remote_appearance.at(session.id())) : std::nullopt;
                                    if(!projected) throw std::runtime_error("Diagnostic normal appearance projection rejected");
                                    const auto characters=database.recovered_characters().list_for_account(session.account_id);
                                    const auto owner=std::find_if(characters.begin(),characters.end(),[&](const auto& value) {
                                        return value.id==session.character_id;
                                    });
                                    if(owner==characters.end())
                                        throw std::runtime_error("Diagnostic remote name ownership rejected");
                                    const auto end=std::find(owner->profile.begin(),owner->profile.begin()+15,0);
                                    if(end==owner->profile.begin() || end==owner->profile.begin()+15)
                                        throw std::runtime_error("Diagnostic remote name bounds rejected");
                                    // CUSTOM-0026: this laboratory actor mirrors the owner's name, not a second player.
                                    const auto named=RecoveredRemoteActor::with_text_fields(*projected,
                                        {std::span<const std::uint8_t>(owner->profile.data(),
                                            static_cast<std::size_t>(end-owner->profile.begin())),
                                         std::span<const std::uint8_t>{},std::span<const std::uint8_t>{}});
                                    if(!named) throw std::runtime_error("Diagnostic remote text projection rejected");
                                    const auto bytes=RecoveredRemoteActor::encode_logical(*named);
                                    logical.assign(bytes.begin(),bytes.end());
                                }
                                auto reply=RecoveredWorldFrame::encode(logical);
                                spdlog::warn("DIAGNOSTIC_REMOTE_ACTOR session_id={} stage={} CUSTOM-0026",session.id(),stage);
                                return std::optional<std::vector<std::uint8_t>>(std::move(reply));
                            }
                            if((config.diagnostic_town_spawn_guides || config.owned_map_views_enabled || config.fruit_village_quests_enabled) && !diagnostic_town_guides_sent.contains(session.id()) &&
                               session.state()!=SessionState::InBattle && records.size()==1 &&
                               std::holds_alternative<RecoveredWorldRecords::Tick>(records.front())) {
                                auto accepted=recovered_world->handle(session,records);
                                if(!accepted) return accepted;
                                const auto position=recovered_movement->current_location(
                                    session.id(),session.account_id,session.character_id);
                                const bool town_location=position && position->area==2 && (position->scene==4 ||
                                   ((config.diagnostic_town_scene_indoor_transfer || config.diagnostic_town_door_routes) && position->scene==15) ||
                                   (config.diagnostic_town_all_door_routes && recovered_movement->registered_door_pair(4,position->scene)) ||
                                   (config.diagnostic_town_island_routes && position->scene==0));
                                const bool kunlun_location=position && position->area==4 && !config.character_birthplace_navigation.empty() &&
                                    (position->scene==3 || (config.diagnostic_kunlun_parent_routes && position->scene==0) ||
                                     (config.diagnostic_kunlun_door_routes && recovered_movement->registered_door_pair(4,3,position->scene)));
                                const bool fruit_location=config.fruit_village_quests_enabled && position && position->area==13 && position->scene==12;
                                if(!town_location && !kunlun_location && !fruit_location)
                                    return std::optional<std::vector<std::uint8_t>>{};
                                // CUSTOM-0020: nearby test positions, not original spawn coordinates.
                                std::vector<std::uint8_t> logical;
                                if(fruit_location && config.fruit_sourcehint_placements) {
                                    // CUSTOM-0051: source-text hint locations and explicit inferred facing0.
                                    for(const auto& npc:FruitVillageQuestRules::descriptors) {
                                        std::array<std::uint8_t,21> record{0x72,0,0,0,0,0,0x60,0,0,1};
                                        // LIVE memory NPCAppearData +12 confirms 23/22/37/33.
                                        // Native case72 reads logical+5 idx before CC380.
                                        const auto source=database.native_npc_display_catalog().lookup(npc.npc_catalog);
                                        if(!source || (source->flags&0x8000) || !source->appearance_code || source->appearance_code>255)
                                            throw DatabaseError("Fruit NPC ordinary source appearance unavailable");
                                        record[5]=static_cast<std::uint8_t>(source->appearance_code);
                                        record[1]=static_cast<std::uint8_t>(npc.npc_catalog);record[2]=static_cast<std::uint8_t>(npc.npc_catalog>>8);
                                        const auto point=(std::uint32_t{npc.source_y}<<17)|(std::uint32_t{npc.source_x}<<2);
                                        for(unsigned n=0;n<4;++n)record[17+n]=static_cast<std::uint8_t>(point>>(8*n));
                                        logical.insert(logical.end(),record.begin(),record.end());
                                    }
                                    spdlog::info("FRUIT_NPCS_RESTORED character_id={} count=4 CUSTOM-0051 source_hint_not_native_spawn facing=custom0",session.character_id);
                                }
                                if(config.diagnostic_town_spawn_guides && position->area==2 && position->scene==4 && !config.native_npc_placements_only) for(const auto& npc:DiagnosticTownNpc::guides) {
                                    const auto record=DiagnosticTownNpc::logical(npc.selector,npc.x,npc.y);
                                    logical.insert(logical.end(),record.begin(),record.end());
                                }
                                if(position->area==2 && position->scene==4 && config.native_npc_placements_only)
                                    spdlog::warn("NATIVE_NPC_PLACEMENT_GAP session_id={} area=2 scene=4 suppressed_unverified_templates=1606,1607 missing=original_position_and_direction",session.id());
                                if(config.diagnostic_town_quest_progress) {
                                    if(const auto saved=supply_repository.load_town_guide_progress(session.account_id,session.character_id);
                                       saved && !database.quest_journals().load(session.account_id,session.character_id)) {
                                        // CUSTOM-0021: dedicated test journal; no shared production slot allocation.
                                        const auto counts=supply_repository.load_quest_description_counts();
                                        RecoveredQuestSync::JournalValues slots{};
                                        slots[0]=saved->journal_description ? (saved->journal_description<<16)|1U : 0U;
                                        const auto restored=RecoveredQuestSync::encodeJournalLogical(slots,counts);
                                        if(!restored) throw DatabaseError("Town journal restore reference unavailable");
                                        logical.insert(logical.end(),restored->begin(),restored->end());
                                        spdlog::warn("DIAGNOSTIC_TOWN_JOURNAL_RESTORE session_id={} stage={} revision={}",
                                            session.id(),saved->stage,saved->revision);
                                    }
                                }
                                if(config.diagnostic_town_quest_progress || config.owned_map_views_enabled || config.fruit_village_quests_enabled) {
                                    // CUSTOM-0037: restore all explicitly owned cells at their
                                    // saved indices. Never replay a grant into its original cell.
                                    const auto bag=supply_repository.load_saved_supply_slots(session.account_id,session.character_id);
                                    if(bag.empty() && config.diagnostic_town_quest_progress && !config.owned_supply_enabled) throw DatabaseError("Owned town bag unavailable");
                                    for(const auto& [index,slot]:bag) {
                                        if(config.owned_weapon_transfers_enabled && slot.count && qualified_weapon(slot.item_id))continue;
                                        if(config.owned_armor_transfers_enabled && slot.count && database.native_armor_catalog().lookup(slot.item_id))continue;
                                        if(config.owned_teleport_gem_enabled && slot.item_id==RecoveredTeleportGem::item_id)continue;
                                        // Production supplies do not turn an unknown
                                        // saved item into a grant or a login failure.
                                        if((config.owned_supply_enabled || config.fruit_village_quests_enabled) && !bag_slot_eligible(slot))continue;
                                        const auto item=bag_slot_projection(index,slot);
                                        logical.insert(logical.end(),item.begin(),item.end());
                                    }
                                }
                                // An indoor character with no saved journal has no guide
                                // records. Keep the tick valid and still join scene presence.
                                auto reply=logical.empty() ? std::vector<std::uint8_t>{}
                                    : RecoveredWorldFrame::encode(logical);
                                if(config.diagnostic_town_chat_welcome) {
                                    // CUSTOM-0034: one localized common-channel entry after
                                    // world admission; reserved high sender misses actor lookup.
                                    const bool simplified=session.recovered_client_language()==1;
                                    const auto text=LegacyChineseCodec::encode(
                                        simplified?"欢迎来到仙界传。":"歡迎來到仙界傳。",simplified);
                                    const auto chat=RecoveredChat::display(0x7fffffffu,simplified,text);
                                    const auto wire=RecoveredWorldFrame::encode(chat);
                                    reply.insert(reply.end(),wire.begin(),wire.end());
                                }
                                if(config.diagnostic_town_spawn_guides && position->area==2 && position->scene==4 &&
                                   !diagnostic_quest_conversations.spawn(session.id(),session.account_id,session.character_id))
                                    return std::optional<std::vector<std::uint8_t>>{};
                                diagnostic_town_guides_sent.insert(session.id());
                                if(config.diagnostic_town_quest_progress || config.owned_map_views_enabled || config.fruit_village_quests_enabled) owned_bag_projected.insert(session.id());
                                if(config.diagnostic_town_player_visibility &&
                                   !player_visibility.contains(session.id())) {
                                    const auto pending=pending_visibility.find(session.id());
                                    if(pending==pending_visibility.end() ||
                                       pending->second.location!=RecoveredVisibility::Scene{position->area,position->scene})
                                        throw std::runtime_error("Town visibility guide join location missing");
                                    visibility_sessions.insert_or_assign(session.id(),session.shared_from_this());
                                    deliver_visibility(player_visibility.enter(pending->second));
                                    pending_visibility.erase(pending);
                                }
                                if(position->area==2 && position->scene==4) {
                                    if(!config.native_npc_placements_only)
                                        spdlog::warn("DIAGNOSTIC_TOWN_GUIDES_SENT session_id={} templates=1606,1607 custom_test_not_native",session.id());
                                } else if(position->scene==0)
                                    spdlog::warn("DIAGNOSTIC_ISLAND_SAVE_RESTORED session_id={} no_town_npcs",session.id());
                                else if(kunlun_location)
                                    spdlog::info("KUNLUN_WORLD_RESTORED session_id={} area=4 scene=3 no_town_npcs",session.id());
                                else spdlog::warn("DIAGNOSTIC_INDOOR_SAVE_RESTORED session_id={} no_town_npcs",session.id());
                                return std::optional<std::vector<std::uint8_t>>(std::move(reply));
                            }
                            if(config.diagnostic_town_player_visibility && !player_visibility.contains(session.id()) &&
                               !diagnostic_town_scene_pending.contains(session.id()) &&
                               session.state()==SessionState::InWorld && records.size()==1 &&
                               std::holds_alternative<RecoveredWorldRecords::Tick>(records.front())) {
                                auto accepted=recovered_world->handle(session,records);
                                if(!accepted) return accepted;
                                const auto pending=pending_visibility.find(session.id());
                                const auto location=recovered_movement->current_location(
                                    session.id(),session.account_id,session.character_id);
                                if(pending==pending_visibility.end() || !location)
                                    throw std::runtime_error("Town visibility world rejoin missing");
                                visibility_sessions.insert_or_assign(session.id(),session.shared_from_this());
                                deliver_visibility(player_visibility.enter(visibility_at(pending->second,*location)));
                                pending_visibility.erase(pending);
                                return accepted;
                            }
                            // CUSTOM-0018: isolated completed-world binding, no general route relaxation.
                            if((config.diagnostic_town_scene_probe || config.diagnostic_town_door_routes) &&
                               (session.state()==SessionState::InWorld || session.state()==SessionState::CharacterSelected) &&
                               (records.size()==1 || (config.diagnostic_town_door_routes && records.size()==2 &&
                                   std::holds_alternative<RecoveredMovement::Request>(records[1]))) &&
                               diagnostic_town_scene_pending.contains(session.id())) {
                                const auto* notice=std::get_if<RecoveredWorldRecords::ContextNotification>(&records.front());
                                if(config.diagnostic_town_door_routes)
                                    spdlog::warn("DIAGNOSTIC_DOOR_PENDING_INPUT session_id={} variant={} context={:02x}{:02x}{:02x}{:02x}",
                                        session.id(),records.front().index(),notice?notice->payload[0]:0,
                                        notice?notice->payload[1]:0,notice?notice->payload[2]:0,
                                        notice?notice->payload[3]:0);
                                // CUSTOM-0036: 4/0 is the observed Island01 arrival receipt,
                                // qualified only by this owned pending scene-0 transfer.
                                const auto destination=notice && session.character_id &&
                                    (config.diagnostic_town_island_routes || config.diagnostic_kunlun_parent_routes)
                                    ? database.recovered_characters().load_position(session.account_id,session.character_id)
                                    : std::nullopt;
                                const bool island_arrival=notice && destination && destination->area==2 &&
                                    diagnostic_island_arrival_receipt(notice->payload,config.diagnostic_town_island_routes,
                                                                      destination->scene,session.character_id,session.recovered_client_language());
                                const bool island_return=notice && destination && destination->area==2 &&
                                    diagnostic_island_return_receipt(notice->payload,
                                        diagnostic_island_return_pending.contains(session.id()),destination->scene,
                                        session.character_id,session.recovered_client_language());
                                // CUSTOM-0053: same native context layout as the qualified
                                // island transport, but only this owned parent pending edge.
                                const bool parent_pending=destination && destination->area==4 && config.diagnostic_kunlun_parent_routes &&
                                    (destination->scene==0 || (destination->scene==3 && diagnostic_island_return_pending.contains(session.id())));
                                const bool parent_receipt=notice && parent_pending && diagnostic_owned_scene_receipt(
                                    notice->payload,session.character_id,session.recovered_client_language());
                                const bool island_pending=parent_pending || (destination && destination->area==2 &&
                                    (destination->scene==0 || diagnostic_island_return_pending.contains(session.id())));
                                if(notice && session.character_id &&
                                   (island_pending ? (island_arrival || island_return || parent_receipt) :
                                    diagnostic_door_context_receipt(notice->payload,
                                        config.diagnostic_town_door_routes || config.diagnostic_town_scene_probe,
                                        session.recovered_client_language(),session.character_id))) {
                                    if(config.diagnostic_town_door_routes || config.diagnostic_town_scene_return_commit ||
                                       (!config.diagnostic_town_scene_return_probe &&
                                        (config.diagnostic_town_scene_relocate || config.diagnostic_town_scene_indoor_transfer)))
                                        recovered_movement->finish_town_transfer(session.id(),session.account_id,session.character_id);
                                    if(config.diagnostic_town_door_routes || config.diagnostic_town_scene_return_commit) {
                                        const bool left=diagnostic_quest_conversations.leave_scene(session.id(),session.account_id,session.character_id);
                                        if(!left) {
                                            spdlog::warn("DIAGNOSTIC_DOOR_SCENE_LEAVE_REJECTED session_id={}",session.id());
                                            return std::optional<std::vector<std::uint8_t>>{};
                                        }
                                    }
                                    if(config.diagnostic_town_door_routes || config.diagnostic_town_scene_return_commit)
                                        diagnostic_town_guides_sent.erase(session.id());
                                    if(config.diagnostic_town_door_routes || config.diagnostic_town_scene_return_commit)
                                        diagnostic_town_map_replied.erase(session.id());
                                    // CUSTOM-0024: exact observed fixture notice; no general context admission.
                                    diagnostic_town_scene_pending.erase(session.id());
                                    diagnostic_island_return_pending.erase(session.id());
                                    std::optional<std::vector<std::uint8_t>> arrival_reply{std::vector<std::uint8_t>{}};
                                    if(records.size()==2) {
                                        // The physical client can queue its first destination
                                        // step with the context receipt in one logical frame.
                                        // After the ring reset, validate and ACK that step in
                                        // the destination scene through the ordinary owner gate.
                                        arrival_reply=recovered_world->handle(session,records.subspan(1));
                                        if(!arrival_reply) return arrival_reply;
                                        spdlog::info("DIAGNOSTIC_TOWN_SCENE_CONTEXT_AND_MOVE_ACCEPTED session_id={}",session.id());
                                    } else spdlog::info("DIAGNOSTIC_TOWN_SCENE_CONTEXT_ACCEPTED session_id={}; no_save_changes",session.id());
                                    // Keep a co-flushed first movement ACK ahead of the scene
                                    // projection. Do not wait up to five seconds for C2S30.
                                    for(const auto& batch:world_display_batches(session)) {
                                        const auto wire=RecoveredWorldFrame::encode(batch);
                                        arrival_reply->insert(arrival_reply->end(),wire.begin(),wire.end());
                                    }
                                    return arrival_reply;
                                }
                            }
                            if(config.diagnostic_town_door_routes &&
                               diagnostic_town_scene_pending.contains(session.id())) {
                                if(records.size()==1 && std::holds_alternative<RecoveredWorldRecords::Tick>(records.front()))
                                    return std::optional<std::vector<std::uint8_t>>(std::vector<std::uint8_t>{});
                                return std::optional<std::vector<std::uint8_t>>{};
                            }
                            if(((config.diagnostic_town_scene_return_probe && !config.diagnostic_town_scene_return_commit) ||
                                (config.diagnostic_town_scene_indoor_probe && !config.diagnostic_town_scene_indoor_transfer)) &&
                               diagnostic_town_map_replied.contains(session.id())) {
                                // The read-only-save probe has no destination movement authority.
                                if(!std::all_of(records.begin(),records.end(),[](const auto& record) {
                                    return std::holds_alternative<RecoveredWorldRecords::Tick>(record);
                                })) return std::optional<std::vector<std::uint8_t>>{};
                            }
                            if(config.diagnostic_town_map_probe &&
                               (!config.diagnostic_town_door_after_battle || !config.diagnostic_town_scene_probe) &&
                               records.size()==1 &&
                               diagnostic_town_guides_sent.contains(session.id()) &&
                               (session.state()==SessionState::CharacterSelected || session.state()==SessionState::InWorld)) {
                                if(const auto* request=std::get_if<RecoveredInventoryItemRequest::Request>(&records.front())) {
                                    // CUSTOM-0023: candidate response experiment, not official item use.
                                    if(request->client_item_id!=5569 || request->raw_slot>=30 ||
                                       diagnostic_town_map_replied.contains(session.id()))
                                        return std::optional<std::vector<std::uint8_t>>{};
                                    const auto position=recovered_movement->current_location(
                                        session.id(),session.account_id,session.character_id);
                                    const auto saved_position=database.recovered_characters().load_position(
                                        session.account_id,session.character_id);
                                    const auto progress=supply_repository.load_town_guide_progress(session.account_id,session.character_id);
                                    const auto slot=supply_repository.load_inventory_slot(session.account_id,session.character_id,request->raw_slot);
                                    if(!position || position->area!=2 ||
                                       (position->scene!=4 && !(config.diagnostic_town_scene_return_probe && position->scene==15)) ||
                                       !progress || progress->stage!=3 ||
                                       !slot || slot->item_id!=5569 || slot->count!=1 || slot->source_sha256!=supply_source)
                                        return std::optional<std::vector<std::uint8_t>>{};
                                    diagnostic_town_map_replied.insert(session.id());
                                    if(config.diagnostic_town_scene_probe) {
                                        // CUSTOM-0024: same-position transport probe, not map-item gameplay or revival.
                                        if(config.diagnostic_town_scene_return_probe && position->scene==15) {
                                            if(position->x!=18 || position->y!=12)
                                                return std::optional<std::vector<std::uint8_t>>{};
                                            if(config.diagnostic_town_scene_return_commit) {
                                                auto reply=recovered_movement->begin_outdoor_return(
                                                    session.id(),session.account_id,session.character_id,*position,110,70);
                                                diagnostic_town_scene_pending.insert(session.id());
                                                spdlog::warn("DIAGNOSTIC_RETURN_TOWN_COMMITTED session_id={} CUSTOM-0024 target=110,70",session.id());
                                                return std::optional<std::vector<std::uint8_t>>(std::move(reply));
                                            }
                                            // Cross-map bit16 is coordinate data, not a reuse flag.
                                            const std::array<std::uint8_t,9> candidate{0x61,2,1,0,0,0xb8,1,0x8c,0};
                                            diagnostic_town_scene_pending.insert(session.id());
                                            spdlog::warn("DIAGNOSTIC_RETURN_TOWN_CANDIDATE session_id={} CUSTOM-0024 no_save_changes",session.id());
                                            return std::optional<std::vector<std::uint8_t>>(RecoveredWorldFrame::encode(candidate));
                                        }
                                        if(position->x!=110 || position->y!=70)
                                            return std::optional<std::vector<std::uint8_t>>{};
                                        if(config.diagnostic_town_scene_indoor_transfer) {
                                            auto reply=saved_position
                                                ? recovered_movement->begin_indoor_transfer(
                                                    session.id(),session.account_id,session.character_id,*saved_position,17,13)
                                                : recovered_movement->begin_initial_indoor_transfer(
                                                    session.id(),session.account_id,session.character_id,17,13);
                                            diagnostic_town_scene_pending.insert(session.id());
                                            spdlog::warn("DIAGNOSTIC_INDOOR_TRANSFER_COMMITTED session_id={} {} scene=15 target=17,13",
                                                session.id(),saved_position?"CUSTOM-0024":"CUSTOM-0032");
                                            return std::optional<std::vector<std::uint8_t>>(std::move(reply));
                                        }
                                        if(config.diagnostic_town_scene_relocate) {
                                            auto reply=recovered_movement->begin_town_transfer(
                                                session.id(),session.account_id,session.character_id,*position,111,70);
                                            diagnostic_town_scene_pending.insert(session.id());
                                            spdlog::warn("DIAGNOSTIC_TOWN_RELOCATION_COMMITTED session_id={} CUSTOM-0024 target=111,70",session.id());
                                            return std::optional<std::vector<std::uint8_t>>(std::move(reply));
                                        }
                                        std::array<std::uint8_t,9> candidate{0x61,2,1,0,0,0,0,0,0};
                                        auto packed=(std::uint32_t{position->x}<<2)|
                                            (std::uint32_t{position->y}<<17)|0x10000u;
                                        if(config.diagnostic_town_scene_indoor_probe) {
                                            // Transport qualification only; never persist or permit destination movement.
                                            candidate[1]=0xc2;candidate[2]=3;
                                            packed=2u|(17u<<2)|(13u<<17);
                                        }
                                        for(unsigned i=0;i<4;++i) candidate[5+i]=static_cast<std::uint8_t>(packed>>(8*i));
                                        diagnostic_town_scene_pending.insert(session.id());
                                        spdlog::warn("DIAGNOSTIC_TOWN_SCENE_CANDIDATE session_id={} CUSTOM-0024 no_save_changes",session.id());
                                        return std::optional<std::vector<std::uint8_t>>(RecoveredWorldFrame::encode(candidate));
                                    }
                                    spdlog::warn("DIAGNOSTIC_TOWN_MAP_CANDIDATE session_id={} CUSTOM-0023 no_consumption",session.id());
                                    const std::array<std::uint8_t,3> candidate{0x3f,1,0};
                                    return std::optional<std::vector<std::uint8_t>>(RecoveredWorldFrame::encode(candidate));
                                }
                            }
                            // The original client can flush dialogue close and the following
                            // ground click in one world frame. Authorize both operations before
                            // consuming the conversation; return the movement ACK unchanged.
                            if((config.diagnostic_quest_dialogue || config.diagnostic_town_spawn_guides) &&
                               !database.quest_journals().load(session.account_id,session.character_id) &&
                               records.size()==2 &&
                               (session.state()==SessionState::CharacterSelected || session.state()==SessionState::InWorld) &&
                               std::holds_alternative<RecoveredQuestClose::Request>(records[0]) &&
                               std::holds_alternative<RecoveredMovement::Request>(records[1])) {
                                if(!diagnostic_quest_conversations.can_cancel(session.id(),session.account_id,session.character_id))
                                    return std::optional<std::vector<std::uint8_t>>{};
                                auto movement_reply=recovered_world->handle(session,records.subspan(1));
                                if(!movement_reply || !diagnostic_quest_conversations.cancel(
                                       session.id(),session.account_id,session.character_id))
                                    return std::optional<std::vector<std::uint8_t>>{};
                                pending_town_guides.erase(session.id());
                                spdlog::warn("DIAGNOSTIC_QUEST_CANCEL_WITH_MOVEMENT_ACCEPTED session_id={} no_journal_mutation_no_rewards",session.id());
                                return movement_reply;
                            }
                            if((config.diagnostic_quest_dialogue || config.diagnostic_town_spawn_guides) &&
                               !database.quest_journals().load(session.account_id,session.character_id) &&
                               (records.size()==1 || (config.diagnostic_town_quest_progress && records.size()==2 &&
                                   std::holds_alternative<RecoveredQuestAction::Request>(records[0]) &&
                                   std::holds_alternative<RecoveredNpcInteraction::Request>(records[1]))) &&
                               (session.state()==SessionState::CharacterSelected || session.state()==SessionState::InWorld)) {
                                if(config.native_npc_placements_only && config.diagnostic_town_spawn_guides &&
                                   (std::holds_alternative<RecoveredNpcInteraction::Request>(records.front()) ||
                                    std::holds_alternative<RecoveredQuestAction::Request>(records.front()))) {
                                    // No native placement means no reachable quest NPC. Do not
                                    // authorize the old diagnostic coordinates or change saves.
                                    spdlog::warn("NATIVE_NPC_INTERACTION_REJECTED session_id={} missing=qualified_native_placement",session.id());
                                    return std::optional<std::vector<std::uint8_t>>(std::vector<std::uint8_t>{});
                                }
                                if(config.diagnostic_quest_npc || config.diagnostic_town_spawn_guides) {
                                    if(const auto* request=std::get_if<RecoveredNpcInteraction::Request>(&records.front())) {
                                        const auto position=config.diagnostic_town_spawn_guides
                                            ? recovered_movement->current_location(session.id(),session.account_id,session.character_id)
                                            : database.recovered_characters().load_position(session.account_id,session.character_id);
                                        const auto word=diagnostic_quest_conversations.next_request_word(session.id(),session.account_id,session.character_id);
                                        if(!word) return std::optional<std::vector<std::uint8_t>>{};
                                        // CUSTOM-0020: source dialogue samples; not official quest-stage selection.
                                        auto text_key=config.diagnostic_town_spawn_guides
                                            ? (request->raw_target==1606?894U:899U) : 3U;
                                        std::optional<PendingTownGuide> pending;
                                        if(config.diagnostic_town_quest_progress) {
                                            if(!position || position->area!=2 || position->scene!=4 ||
                                               !DiagnosticTownNpc::nearby(request->raw_target,position->x,position->y))
                                                return std::optional<std::vector<std::uint8_t>>{};
                                            const auto saved=supply_repository.load_town_guide_progress(session.account_id,session.character_id);
                                            const auto plan=lua.town_guide({saved?saved->stage:0,request->raw_target});
                                            pending=PendingTownGuide{saved,plan,request->raw_target,{}};
                                            if(plan.requires_reward) {
                                                // CUSTOM-0022: only an explicitly owned empty test slot.
                                                const auto slot=supply_repository.load_inventory_slot(session.account_id,session.character_id,0);
                                                if(!slot || slot->item_id || slot->count || slot->source_sha256!=supply_source)
                                                    return std::optional<std::vector<std::uint8_t>>{};
                                                pending->reward_slot=slot;
                                            }
                                            text_key=plan.text_key;
                                        }
                                        auto response=RecoveredWorldFrame::encode(RecoveredQuestDialogue::mode1(*word,2,0x9a,text_key,14600).value());
                                        if(!position) return std::optional<std::vector<std::uint8_t>>{};
                                        const bool opened=config.diagnostic_town_spawn_guides
                                            ? diagnostic_quest_conversations.open_town_npc(session.id(),session.account_id,
                                                session.character_id,request->raw_target,*position)
                                            : diagnostic_quest_conversations.open_npc(session.id(),session.account_id,
                                                session.character_id,request->raw_target,*position);
                                        if(!opened)
                                            return std::optional<std::vector<std::uint8_t>>{};
                                        if(pending) pending_town_guides.insert_or_assign(session.id(),*pending);
                                        spdlog::warn("DIAGNOSTIC_NPC_REQUEST_ACCEPTED session_id={} target={} {}",session.id(),request->raw_target,
                                            position->revision?"owned_saved_position_checked":"owned_initial_position_checked");
                                        return std::optional<std::vector<std::uint8_t>>(std::move(response));
                                    }
                                }
                                if(const auto* request=std::get_if<RecoveredQuestAction::Request>(&records.front())) {
                                    if(config.diagnostic_town_quest_progress) {
                                        const auto found=pending_town_guides.find(session.id());
                                        if(found==pending_town_guides.end()) return std::optional<std::vector<std::uint8_t>>{};
                                        const auto pending=found->second;
                                        const auto position=recovered_movement->current_location(
                                            session.id(),session.account_id,session.character_id);
                                        if(!position || position->area!=2 || position->scene!=4 ||
                                           !DiagnosticTownNpc::nearby(pending.npc,position->x,position->y))
                                            return std::optional<std::vector<std::uint8_t>>{};
                                        const auto* followup=records.size()==2
                                            ? std::get_if<RecoveredNpcInteraction::Request>(&records[1]) : nullptr;
                                        std::optional<TownGuidePlan> followup_plan;
                                        std::optional<StoredInventorySlot> followup_slot;
                                        if(followup) {
                                            // Original producer can queue 85 then 37 together. Preflight
                                            // both operations before committing this CUSTOM-0021 stage.
                                            if(!diagnostic_quest_conversations.can_consume(session.id(),
                                                   session.account_id,session.character_id,*request) ||
                                               request->request_word==0xffff ||
                                               !DiagnosticTownNpc::nearby(followup->raw_target,position->x,position->y))
                                                return std::optional<std::vector<std::uint8_t>>{};
                                            followup_plan=lua.town_guide({pending.plan.confirmed_stage,followup->raw_target});
                                            if(followup_plan->requires_reward) {
                                                const auto slot=supply_repository.load_inventory_slot(
                                                    session.account_id,session.character_id,0);
                                                if(!slot || slot->item_id || slot->count || slot->source_sha256!=supply_source)
                                                    return std::optional<std::vector<std::uint8_t>>{};
                                                followup_slot=slot;
                                            }
                                        }
                                        const auto counts=supply_repository.load_quest_description_counts();
                                        const auto value=pending.plan.journal_description
                                            ? (pending.plan.journal_description<<16)|1U : 0U;
                                        if(value && !RecoveredQuestSync::descriptionReference(value,counts))
                                            throw DatabaseError("Town quest description unavailable");
                                        const auto journal=RecoveredQuestSync::encodeSlotLogical(0,4,value).value();
                                        std::vector<std::uint8_t> logical(journal.begin(),journal.end());
                                        if(pending.plan.requires_reward) {
                                            if(!pending.expected || !pending.reward_slot)
                                                throw DatabaseError("Town reward proposal missing snapshot");
                                            const auto item=RecoveredInventory::encode_slot_update({5569,0,1}).value();
                                            logical.insert(logical.end(),item.begin(),item.end());
                                        }
                                        auto projection=RecoveredWorldFrame::encode(logical);
                                        if(!diagnostic_quest_conversations.consume_after_commit(session.id(),session.account_id,session.character_id,*request,[&] {
                                            if(supply_repository.load_town_guide_progress(session.account_id,session.character_id)!=pending.expected)
                                                throw DatabaseError("Town pending conversation is stale");
                                            if(pending.plan.requires_reward)
                                                supply_repository.complete_town_guide(session.account_id,session.character_id,
                                                    *pending.expected,0,*pending.reward_slot);
                                            else if(pending.plan.confirmed_stage!=(pending.expected?pending.expected->stage:0))
                                                supply_repository.commit_town_guide_progress(session.account_id,session.character_id,
                                                    pending.expected,pending.plan.confirmed_stage);
                                        })) return std::optional<std::vector<std::uint8_t>>{};
                                        pending_town_guides.erase(found);
                                        if(!diagnostic_quest_conversations.allow_followup(session.id(),session.account_id,session.character_id))
                                            throw std::runtime_error("Town confirmed conversation could not rearm");
                                        if(followup) {
                                            const auto saved_after=supply_repository.load_town_guide_progress(
                                                session.account_id,session.character_id);
                                            if((saved_after?saved_after->stage:0)!=pending.plan.confirmed_stage ||
                                               (followup_slot && supply_repository.load_inventory_slot(
                                                   session.account_id,session.character_id,0)!=followup_slot))
                                                throw DatabaseError("Town followup preflight changed after commit");
                                            const auto word=diagnostic_quest_conversations.next_request_word(
                                                session.id(),session.account_id,session.character_id);
                                            if(!word || *word!=request->request_word+1 ||
                                               !diagnostic_quest_conversations.open_town_npc(session.id(),
                                                   session.account_id,session.character_id,followup->raw_target,*position))
                                                throw std::runtime_error("Town same-frame followup could not open");
                                            pending_town_guides.insert_or_assign(session.id(),PendingTownGuide{
                                                saved_after,*followup_plan,followup->raw_target,followup_slot});
                                            const auto next=RecoveredWorldFrame::encode(RecoveredQuestDialogue::mode1(
                                                *word,2,0x9a,followup_plan->text_key,14600).value());
                                            projection.insert(projection.end(),next.begin(),next.end());
                                            spdlog::warn("DIAGNOSTIC_TOWN_CONFIRM_FOLLOWUP_ACCEPTED session_id={} target={} next_word={}",
                                                session.id(),followup->raw_target,*word);
                                        }
                                        spdlog::warn("DIAGNOSTIC_TOWN_PROGRESS_CONFIRMED session_id={} stage={} reward={}",
                                            session.id(),pending.plan.confirmed_stage,pending.plan.requires_reward?"CUSTOM-0022:item5569x1":"none");
                                        return std::optional<std::vector<std::uint8_t>>(std::move(projection));
                                    }
                                    std::vector<std::uint8_t> projection;
                                    std::optional<StoredQuestJournal> previous;
                                    StoredQuestJournal next;
                                    std::array<std::uint16_t,418> counts{};
                                    // CUSTOM-0018: diagnostic journal reference, not an accepted native quest.
                                    if(config.diagnostic_quest_npc) {
                                        counts=supply_repository.load_quest_description_counts();
                                        previous=supply_repository.load_quest_journal(session.account_id,session.character_id);
                                        next=previous.value_or(StoredQuestJournal{});
                                        next.source_sha256=SqliteRecoveredCharacterRepository::quest_source_sha256;
                                        next.slots[0]=1;
                                        projection=RecoveredWorldFrame::encode(RecoveredQuestSync::encodeSlotLogical(0,4,1).value());
                                    }
                                    if(!diagnostic_quest_conversations.consume_after_commit(session.id(),session.account_id,session.character_id,*request,[&] {
                                        if(config.diagnostic_quest_npc)
                                            supply_repository.commit_quest_journal(session.account_id,session.character_id,previous,next,counts);
                                    }))
                                        return std::optional<std::vector<std::uint8_t>>{};
                                    if(!diagnostic_quest_conversations.allow_followup(session.id(),session.account_id,session.character_id))
                                        throw std::runtime_error("Confirmed diagnostic conversation could not rearm");
                                    spdlog::warn("DIAGNOSTIC_QUEST_CONFIRM_ACCEPTED session_id={} no_quest_progress_no_rewards",session.id());
                                    return std::optional<std::vector<std::uint8_t>>(std::move(projection));
                                }
                                if(std::holds_alternative<RecoveredQuestClose::Request>(records.front())) {
                                    if(!diagnostic_quest_conversations.cancel(session.id(),session.account_id,session.character_id))
                                        return std::optional<std::vector<std::uint8_t>>{};
                                    pending_town_guides.erase(session.id());
                                    spdlog::warn("DIAGNOSTIC_QUEST_CANCEL_ACCEPTED session_id={} no_journal_mutation_no_rewards",session.id());
                                    return std::optional<std::vector<std::uint8_t>>(std::vector<std::uint8_t>{});
                                }
                            }
                            if(config.diagnostic_quest_dialogue && !diagnostic_quest_dialogue_sent.contains(session.id()) &&
                               !database.quest_journals().load(session.account_id,session.character_id) &&
                               session.state()!=SessionState::InBattle && records.size()==1 &&
                               std::holds_alternative<RecoveredWorldRecords::Tick>(records.front())) {
                                auto accepted=recovered_world->handle(session,records);
                                if(!accepted) return accepted;
                                // CUSTOM-0018: explicit test conversation, not an accepted quest.
                                const auto logical=RecoveredQuestDialogue::mode1(0x1234,2,0x9a,3,14600).value();
                                auto reply=RecoveredWorldFrame::encode(logical);
                                if(config.diagnostic_quest_npc) {
                                    const auto npc=DiagnosticQuestNpc::logical();
                                    std::vector<std::uint8_t> restored(npc.begin(),npc.end());
                                    if(const auto journal=supply_repository.load_quest_journal(session.account_id,session.character_id)) {
                                        if(journal->source_sha256!=SqliteRecoveredCharacterRepository::quest_source_sha256)
                                            throw DatabaseError("Journal restore source mismatch");
                                        const auto counts=supply_repository.load_quest_description_counts();
                                        const auto batch=RecoveredQuestSync::encodeJournalLogical(journal->slots,counts);
                                        if(!batch) throw DatabaseError("Invalid saved journal reference");
                                        restored.insert(restored.end(),batch->begin(),batch->end());
                                        spdlog::warn("DIAGNOSTIC_JOURNAL_RESTORE session_id={} revision={}",session.id(),journal->revision);
                                    }
                                    reply=RecoveredWorldFrame::encode(restored);
                                    if(!diagnostic_quest_conversations.spawn(session.id(),session.account_id,session.character_id))
                                        return std::optional<std::vector<std::uint8_t>>{};
                                    diagnostic_quest_dialogue_sent.insert(session.id());
                                    spdlog::warn("DIAGNOSTIC_QUEST_NPC_SENT session_id={} template=531 position=17,12 custom_test_not_native",session.id());
                                    return std::optional<std::vector<std::uint8_t>>(std::move(reply));
                                }
                                if(!diagnostic_quest_conversations.open(session.id(),session.account_id,session.character_id))
                                    return std::optional<std::vector<std::uint8_t>>{};
                                diagnostic_quest_dialogue_sent.insert(session.id());
                                spdlog::warn("DIAGNOSTIC_QUEST_DIALOGUE_SENT session_id={} key=3 custom_conversation_no_rewards",session.id());
                                return std::optional<std::vector<std::uint8_t>>(std::move(reply));
                            }
                            if(config.diagnostic_world_resources && !diagnostic_world_resources_sent.contains(session.id()) &&
                               session.state()!=SessionState::InBattle && records.size()==1 &&
                               std::holds_alternative<RecoveredWorldRecords::Tick>(records.front())) {
                                auto accepted=recovered_world->handle(session,records);
                                if(!accepted) return accepted;
                                // CUSTOM-0012 saved resources only; no historical replay or implicit seed.
                                const auto saved=database.recovered_characters().load_resources(session.account_id,session.character_id);
                                if(saved) {
                                    // Fresh-entry saved vitals were already queued before
                                    // companion binding. This optional route only restores
                                    // diagnostic consumables; never resend native24 here.
                                    spdlog::info("DIAGNOSTIC_WORLD_RESOURCES_ALREADY_RESTORED session_id={} character_id={} hp={} max_hp={} mp={} max_mp={} revision={}",
                                                 session.id(),session.character_id,saved->hp,saved->max_hp,saved->mp,saved->max_mp,saved->revision);
                                    if(config.diagnostic_world_supply) {
                                        // CUSTOM-0015/0016: project only explicitly persisted,
                                        // qualified consumable slots. An absent row never clears
                                        // or grants a client item; slots30..49 have other semantics.
                                        std::vector<std::uint8_t> inventory;
                                        inventory.reserve(30*RecoveredInventory::logical_size);
                                        const auto slots=supply_repository.load_saved_supply_slots(
                                            session.account_id,session.character_id);
                                        for(const auto& [index,slot]:slots) {
                                            if(config.owned_weapon_transfers_enabled && slot.count && qualified_weapon(slot.item_id))continue;
                                        if(config.owned_armor_transfers_enabled && slot.count && database.native_armor_catalog().lookup(slot.item_id))continue;
                                            if(config.owned_teleport_gem_enabled && slot.item_id==RecoveredTeleportGem::item_id)continue;
                                            if(!bag_slot_eligible(slot))
                                                throw std::runtime_error("Diagnostic supply contains an unqualified saved slot");
                                            const auto item=bag_slot_projection(index,slot);
                                            inventory.insert(inventory.end(),item.begin(),item.end());
                                        }
                                        if(inventory.empty())
                                            throw std::runtime_error("Diagnostic supply requires an explicit saved slot");
                                        const auto wire=RecoveredWorldFrame::encode(inventory);
                                        accepted->insert(accepted->end(),wire.begin(),wire.end());
                                        owned_bag_projected.insert(session.id());
                                    }
                                } else {
                                    spdlog::warn("DIAGNOSTIC_WORLD_RESOURCES_ABSENT session_id={} character_id={}; no seed or packet",session.id(),session.character_id);
                                    spdlog::default_logger()->flush();
                                }
                                diagnostic_world_resources_sent.insert(session.id());
                                return accepted;
                            }
                            if(config.diagnostic_battle_player_appearance) {
                                spdlog::info("DIAGNOSTIC_PLAYER_BATCH session_id={} state={} count={}",session.id(),static_cast<int>(session.state()),records.size());
                                for(const auto& record:records) {
                                    spdlog::info("DIAGNOSTIC_PLAYER_RECORD type_index={}",record.index());
                                    if(const auto* skill=std::get_if<RecoveredSkillCommand::Record>(&record))
                                        spdlog::info("DIAGNOSTIC_PLAYER_SKILL actor={} kind={} id={} continuation={} side={} masks={:04x},{:04x} context={:08x}",
                                            skill->actor_position,skill->selection_kind_byte,skill->selection_id_byte,
                                            skill->continuation,skill->side_flag,skill->target_masks[0],
                                            skill->target_masks[1],skill->context_storage);
                                    if(const auto* opening=std::get_if<RecoveredBattleCommand::Action2Request>(&record))
                                        spdlog::info("DIAGNOSTIC_PLAYER_ACTION2 actor={} side={} byte3={} masks={:04x},{:04x} context={:08x} parameter={:08x}",
                                            opening->fields.actor_position,opening->fields.side_flag,
                                            opening->fields.unwritten_byte3,opening->fields.target_masks[0],
                                            opening->fields.target_masks[1],opening->fields.context_storage,
                                            opening->fields.unwritten_parameter);
                                    if(const auto* control=std::get_if<RecoveredBattleCommand::ControlRequest>(&record))
                                        spdlog::info("DIAGNOSTIC_PLAYER_CONTROL actor={} side={} byte3={} masks={:04x},{:04x} context={:08x} parameter={:08x}",
                                            control->fields.actor_position,control->fields.side_flag,
                                            control->fields.unwritten_byte3,control->fields.target_masks[0],
                                            control->fields.target_masks[1],control->fields.context_storage,
                                            control->fields.unwritten_parameter);
                                    if(const auto* context=std::get_if<RecoveredWorldRecords::ContextNotification>(&record))
                                        spdlog::info("DIAGNOSTIC_PLAYER_CONTEXT payload={:02x}{:02x}{:02x}{:02x}",
                                            context->payload[0],context->payload[1],context->payload[2],context->payload[3]);
                                }
                            }
                            // CUSTOM-0011: admit one observed post-terminal context notice.
                            // Counter zero marks a committed/released diagnostic, not a wire turn ID.
                            if(config.diagnostic_battle_terminal && session.state()==SessionState::InWorld &&
                               records.size()==1 && diagnostic_rounds_granted.contains(session.id()) &&
                                diagnostic_rounds_granted.at(session.id())==0) {
                                const auto* context=std::get_if<RecoveredWorldRecords::ContextNotification>(&records.front());
                                const auto outcome=diagnostic_town_battle_won.find(session.id());
                                // Current client: win 04 00 01 00, loss 04 00 00 00.
                                // The loss receipt is admitted only for a committed
                                // terminal loss on this same session.
                                const bool town_result=context && config.diagnostic_town_battle_after_quest &&
                                    outcome!=diagnostic_town_battle_won.end() &&
                                    context->payload==std::array<std::uint8_t,4>{4,0,
                                        static_cast<std::uint8_t>(outcome->second ? 1 : 0),0};
                                // Current Taiwan client 20260927 hidden growth run06:
                                // owned, committed victory emits 04 00 00 00. Do not
                                // infer byte2's meaning or admit it outside that fixture.
                                const bool growth_result=context && config.diagnostic_character_growth &&
                                    outcome!=diagnostic_town_battle_won.end() && outcome->second &&
                                    context->payload==std::array<std::uint8_t,4>{4,0,0,0};
                                // CUSTOM-0012: private kind1 cast05 native window
                                // inputs yielded this receipt after committed victory.
                                // Byte2 remains uninterpreted; no reward/state mutation.
                                const bool spell_result=context && config.diagnostic_battle_skill_kind==1 &&
                                    outcome!=diagnostic_town_battle_won.end() && outcome->second &&
                                    context->payload==std::array<std::uint8_t,4>{4,0,0,0};
                                if(context && ((context->payload[0]==1 && context->payload[1]==0 &&
                                                context->payload[2]<=1 && context->payload[3]==0) ||
                                               town_result || growth_result || spell_result)) {
                                    diagnostic_rounds_granted.erase(session.id());
                                    diagnostic_town_battle_won.erase(session.id());
                                    if(config.diagnostic_encounter_limit>1 &&
                                       diagnostic_encounters_started.at(session.id())<config.diagnostic_encounter_limit) {
                                        diagnostic_battle_sent.erase(session.id());
                                        diagnostic_movement_ready.at(session.id())=false;
                                    }
                                    spdlog::info("DIAGNOSTIC_POST_BATTLE_CONTEXT_ACCEPTED session_id={}; no state or reward mutation",session.id());
                                    return std::optional<std::vector<std::uint8_t>>(std::vector<std::uint8_t>{});
                                }
                            }
                            if(config.diagnostic_battle_transition && diagnostic_battle_sent.contains(session.id()) && records.size()==1) {
                                const auto* notice=std::get_if<RecoveredWorldRecords::TimerNotification>(&records.front());
                                if(notice) {
                                    spdlog::info("DIAGNOSTIC_TIMER36_ACCEPTED session_id={}; no gameplay effect",session.id());
                                    if(diagnostic_vitals_sent.insert(session.id()).second) {
                                        std::uint32_t initial_hp=100,initial_mp=config.diagnostic_battle_revival ? 80u : (config.diagnostic_battle_mp_refusal ? 7u : 50u);
                                        RecoveredBattleService::CheckpointCommit resource_commit;
                                        std::shared_ptr<CharacterResources> durable_resources;
                                        std::shared_ptr<StoredBattleCheckpoint> revival_checkpoint;
                                        std::optional<StoredBattleCheckpoint> pending_checkpoint;
                                        auto battle_id=session.id();
                                        if(config.diagnostic_battle_resources) {
                                            auto& repo=static_cast<SqliteRecoveredCharacterRepository&>(database.recovered_characters());
                                            auto saved=repo.load_resources(session.account_id,session.character_id);
                                            if(config.diagnostic_battle_revival && saved && !config.diagnostic_resume_checkpoint)
                                                throw std::runtime_error("Durable revival bootstrap requires a fresh diagnostic character");
                                            if(config.diagnostic_resume_checkpoint && !saved)
                                                throw std::runtime_error("Resume cannot seed missing resources");
                                            if(!saved) saved=repo.commit_resources(session.account_id,session.character_id,{},
                                                CharacterResources{initial_hp,120,initial_mp,80,0,"CUSTOM-0012"});
                                            if(saved->max_hp!=120 || saved->max_mp!=80 || !saved->hp)
                                                throw std::runtime_error("Stored resources incompatible with living diagnostic fixture");
                                            const auto legacy=saved->legacy_vitals();
                                            if(!legacy)throw std::runtime_error("Diagnostic battle requires legacy HP representation");
                                            initial_hp=(*legacy)[0];initial_mp=(*legacy)[2];
                                            if(config.diagnostic_visibility_checkpoint) {
                                                pending_checkpoint=repo.load_pending_checkpoint(session.account_id,session.character_id);
                                                if(pending_checkpoint) {
                                                    if(pending_checkpoint->revival || pending_checkpoint->policy_id!="CUSTOM-0012/diagnostic-v1")
                                                        throw std::runtime_error("Visibility recovery policy differs");
                                                    battle_id=pending_checkpoint->checkpoint.snapshot.id;
                                                }
                                            }
                                            if(config.diagnostic_resume_checkpoint && config.diagnostic_battle_revival) {
                                                pending_checkpoint=repo.load_pending_checkpoint(session.account_id,session.character_id);
                                                if(!pending_checkpoint || !pending_checkpoint->revival || saved->revision<5 ||
                                                   pending_checkpoint->checkpoint.snapshot.revision!=saved->revision-1 ||
                                                   pending_checkpoint->resource_revision!=saved->revision)
                                                    throw std::runtime_error("Revival resume requires durable receipt-complete checkpoint");
                                                (void)diagnostic_revival_resume_participants(session.character_id,*pending_checkpoint->revival);
                                                battle_id=pending_checkpoint->checkpoint.snapshot.id;
                                            } else if(config.diagnostic_resume_checkpoint) {
                                                pending_checkpoint=repo.load_pending_checkpoint(session.account_id,session.character_id);
                                                const auto role=repo.load_role(session.account_id,session.character_id);
                                                if(!pending_checkpoint || !role || role->logical!=diagnostic_role_level_seed() || role->revision!=1 ||
                                                   repo.load_experience(session.account_id,session.character_id) ||
                                                   (saved->revision!=4 && saved->revision!=5) ||
                                                   pending_checkpoint->resource_revision!=saved->revision ||
                                                   pending_checkpoint->revival || pending_checkpoint->policy_id!="CUSTOM-0012/diagnostic-v1" ||
                                                   role->design_id!="CUSTOM-0013" || saved->design_id!="CUSTOM-0012")
                                                    throw std::runtime_error("Resume requires saved diagnostic exchange baseline");
                                                const auto& state=pending_checkpoint->checkpoint.snapshot;
                                                const unsigned exchanges=static_cast<unsigned>(saved->revision-3);
                                                if(state.revision!=2*exchanges+1 || !state.actors[0] ||
                                                   saved->hp!=state.actors[0]->hp || saved->mp!=state.actors[0]->mp)
                                                    throw std::runtime_error("Resume checkpoint differs from qualified diagnostic exchange");
                                                (void)diagnostic_battle_resume_participants(session.character_id,state);
                                                validate_diagnostic_exchange(pending_checkpoint->checkpoint,session.character_id,exchanges,
                                                    [&lua](const auto& input){return lua.combat_damage(input);});
                                                battle_id=state.id;
                                            } else if(config.diagnostic_level_snapshot && diagnostic_encounters_started.at(session.id())>1) {
                                                // CUSTOM-0014: second encounter inherits the qualified first settlement.
                                                const auto role=repo.load_role(session.account_id,session.character_id);
                                                const auto xp=repo.load_experience(session.account_id,session.character_id);
                                                const auto seed=RecoveredRoleLevel::parse(diagnostic_role_level_seed());
                                                auto first_role=RecoveredRoleLevel::with_level_progress(*seed,2,1250);
                                                if(config.diagnostic_character_growth) {
                                                    const auto owned=repo.list_for_account(session.account_id);
                                                    const auto found=std::find_if(owned.begin(),owned.end(),[&](const auto& c){return c.id==session.character_id;});
                                                    if(found==owned.end())throw std::runtime_error("Growth profile ownership missing");
                                                    first_role=project_character_growth(lua,recovered_growth_class(found->profile),*seed,2,1250);
                                                }
                                                const auto expected=RecoveredRoleLevel::encode(first_role);
                                                if(config.diagnostic_encounter_limit!=2 || !role || !xp ||
                                                   role->logical!=expected || role->revision!=2 || role->design_id!="CUSTOM-0013" ||
                                                   xp->total!=250 || xp->design_id!="CUSTOM-0012" ||
                                                   saved->hp!=76 || saved->mp!=26 || saved->revision!=6 || saved->design_id!="CUSTOM-0012" ||
                                                   repo.load_pending_checkpoint(session.account_id,session.character_id))
                                                    throw std::runtime_error("Second encounter requires unchanged first settlement");
                                            } else if(config.diagnostic_level_snapshot) {
                                                // CUSTOM-0013: fresh isolated experiment only; never replace a saved role.
                                                if(repo.load_role(session.account_id,session.character_id) ||
                                                   repo.load_experience(session.account_id,session.character_id))
                                                    throw std::runtime_error("Level snapshot probe requires a fresh character");
                                                saved=repo.commit_role_resources(session.account_id,session.character_id,{},*saved,
                                                    {diagnostic_role_level_seed(),0,"CUSTOM-0013"},*saved).resources;
                                            }
                                            std::optional<CharacterGrowthClass> growth_class;
                                            if(config.diagnostic_character_growth) {
                                                const auto owned=repo.list_for_account(session.account_id);
                                                const auto found=std::find_if(owned.begin(),owned.end(),[&](const auto& c){return c.id==session.character_id;});
                                                if(found==owned.end())throw std::runtime_error("Growth profile ownership missing");
                                                growth_class=recovered_growth_class(found->profile);
                                            }
                                            if(!pending_checkpoint) battle_id=repo.reserve_battle(session.account_id,session.character_id,*saved);
                                            durable_resources=std::make_shared<CharacterResources>(*saved);
                                            resource_commit=[&repo,account=session.account_id,character=session.character_id,saved=durable_resources,battle_id,
                                                    &lua,level_snapshot=config.diagnostic_level_snapshot,growth_class,
                                                    visibility_checkpoint=config.diagnostic_visibility_checkpoint,span=config.diagnostic_progress_span,
                                                    award=config.diagnostic_battle_experience](
                                                    const BattleCheckpoint& before_checkpoint,const BattleCheckpoint& after_checkpoint) {
                                                const auto& before=before_checkpoint.snapshot;
                                                const auto& after=after_checkpoint.snapshot;
                                                const auto& old=*before.actors[0];const auto& next=*after.actors[0];
                                                if(old.controller!=character || next.controller!=character || old.hp!=saved->hp ||
                                                   old.mp!=saved->mp || old.max_hp!=saved->max_hp || old.max_mp!=saved->max_mp)
                                                    throw std::runtime_error("Battle/resource baseline mismatch");
                                                if(before.id!=battle_id || after.id!=battle_id)
                                                    throw std::runtime_error("Battle reservation identity mismatch");
                                                const CharacterResources resources{next.hp,next.max_hp,next.mp,next.max_mp,0,"CUSTOM-0012"};
                                                if(after.state==BattleState::Finished && !after.victorious_side)
                                                    throw std::runtime_error("Finished battle has no authoritative winner");
                                                std::optional<BattleProgressionCommit> progression;
                                                if(level_snapshot && after.state==BattleState::Finished) {
                                                    const auto xp=repo.load_experience(account,character);
                                                    const auto role=repo.load_role(account,character);
                                                    if(!role || role->design_id!="CUSTOM-0013" ||
                                                       (xp && xp->design_id!="CUSTOM-0012"))
                                                        throw std::runtime_error("Missing diagnostic progression baseline");
                                                    const auto total=xp ? xp->total : 0;
                                                    const auto earned=*after.victorious_side==0 ? award : 0;
                                                    const auto advanced=ExtendedExperienceAmount::accumulate(total,earned);
                                                    if(!advanced)
                                                        throw std::runtime_error("Diagnostic progression XP overflow");
                                                    // CUSTOM-0013 XP curve stays isolated. Optional stat growth
                                                    // is OWNER_CONFIRMED; maxima/healing are not inferred.
                                                    const auto projected=lua.progression({advanced->value(),{0,span,std::uint64_t{span}*3},3});
                                                    const auto previous=RecoveredRoleLevel::parse(role->logical);
                                                    if(!previous) throw std::runtime_error("Invalid saved role snapshot");
                                                    auto next_role=*role;
                                                    next_role.logical=RecoveredRoleLevel::encode(RecoveredRoleLevel::with_level_progress(
                                                        *previous,static_cast<std::uint8_t>(projected.level),projected.progress_display));
                                                    if(growth_class)next_role.logical=RecoveredRoleLevel::encode(project_character_growth(
                                                        lua,*growth_class,*previous,static_cast<std::uint16_t>(projected.level),projected.progress_display));
                                                    progression=BattleProgressionCommit{xp,role,std::move(next_role)};
                                                }
                                                // CUSTOM-0012: explicit isolated test amount, never native monster XP.
                                                if(level_snapshot || visibility_checkpoint) {
                                                    const auto stored=repo.load_checkpoint(account,character,battle_id);
                                                    if(!stored || stored->checkpoint!=before_checkpoint)
                                                        throw std::runtime_error("Persisted battle checkpoint diverged");
                                                    if(after.state==BattleState::Finished) {
                                                        auto committed=repo.settle_checkpoint(account,character,*stored,*saved,after_checkpoint,resources,
                                                            *after.victorious_side==0,*after.victorious_side==0 ? award : 0,progression);
                                                        *saved=std::move(committed.resources);
                                                    } else {
                                                        auto next_resources=resources;
                                                        const auto committed=repo.commit_checkpoint(account,character,stored,*saved,after_checkpoint,resources,stored->policy_id);
                                                        next_resources.revision=committed.resource_revision;
                                                        *saved=std::move(next_resources);
                                                    }
                                                    return;
                                                }
                                                auto committed=after.state==BattleState::Finished ?
                                                    repo.settle_battle(account,character,battle_id,*saved,resources,
                                                        *after.victorious_side==0,*after.victorious_side==0 ? award : 0,progression).resources :
                                                    repo.commit_resources(account,character,*saved,resources);
                                                *saved=std::move(committed);
                                            };
                                        }
                                        const bool first_exchange_resume=pending_checkpoint && !config.diagnostic_battle_revival &&
                                            pending_checkpoint->checkpoint.snapshot.revision==3 &&
                                            (!config.diagnostic_visibility_checkpoint || (config.diagnostic_visibility_skill_recovery &&
                                                pending_checkpoint->checkpoint.snapshot.revision==3));
                                        const bool second_exchange_resume=pending_checkpoint && config.diagnostic_resume_checkpoint &&
                                            !config.diagnostic_battle_revival && pending_checkpoint->checkpoint.snapshot.revision==5;
                                        // CUSTOM-0058: only saved learned state on the selected owned
                                        // deity grants126. Catalog presence and C2S requests grant nothing.
                                        const bool owned_shunying=!config.diagnostic_shunying_manual &&
                                            !config.diagnostic_battle_revival &&
                                            database.companions().selected_deity_has_skill(session.account_id,
                                                session.character_id,ShunyingSanshazhan::kind,ShunyingSanshazhan::id);
                                        const bool owned_thousand_bulls=!config.diagnostic_shunying_manual &&
                                            !config.diagnostic_battle_revival &&
                                            database.companions().selected_deity_has_skill(session.account_id,
                                                session.character_id,ThousandBulls::kind,ThousandBulls::id);
                                        const auto manual_resources=config.diagnostic_shunying_manual ?
                                            database.recovered_characters().load_resources(session.account_id,session.character_id) :
                                            std::optional<CharacterResources>{};
                                        std::vector<std::uint8_t> vitals(121,0);vitals[0]=0x88;
                                        if(config.diagnostic_battle_participants) vitals=diagnostic_battle_participants();
                                        if(config.diagnostic_battle_player_appearance)
                                            vitals=diagnostic_battle_player_participants(session.character_id,initial_mp,initial_hp);
                                        if(config.diagnostic_shunying_manual) {
                                            const auto role=database.recovered_characters().load_role(session.account_id,session.character_id);
                                            if(!role) throw std::runtime_error("Missing initial diagnostic role snapshot");
                                            vitals=diagnostic_shunying_manual_participants(session.character_id,
                                                diagnostic_remote_appearance.at(session.id()),manual_resources ? &*manual_resources : nullptr,
                                                role->logical[1],diagnostic_shunying_manual_slot,
                                                config.diagnostic_recording_fixed_damage?RecordingCombatTest::monster_hp:10000);
                                        }
                                        if(first_exchange_resume || second_exchange_resume)
                                            vitals=diagnostic_battle_resume_participants(session.character_id,pending_checkpoint->checkpoint.snapshot);
                                        if(config.diagnostic_battle_skill_seed && !owned_shunying && !owned_thousand_bulls) {
                                            // CUSTOM-0012: same identity as learned seed and trusted policy.
                                            const auto state=config.diagnostic_battle_revival ?
                                                std::array<std::uint8_t,3>{0x87,8,0x83} :
                                                (config.diagnostic_shunying_manual ? (config.diagnostic_thousand_bulls_manual ?
                                                    diagnostic_thousand_bulls_manual_selectable() : diagnostic_shunying_manual_selectable()) :
                                                diagnostic_battle_skill_selectable(static_cast<std::uint8_t>(config.diagnostic_battle_skill_kind)));
                                            vitals.insert(vitals.begin(),state.begin(),state.end());
                                            if(config.diagnostic_recording_fixed_damage){
                                                const auto extra=diagnostic_shunying_manual_selectable();
                                                vitals.insert(vitals.begin(),extra.begin(),extra.end());
                                            }
                                        }
                                        if(owned_shunying) {
                                            const std::array<std::uint8_t,3> selectable{0x87,ShunyingSanshazhan::id,0x80};
                                            vitals.insert(vitals.begin(),selectable.begin(),selectable.end());
                                        }
                                        if(owned_thousand_bulls) {
                                            const std::array<std::uint8_t,3> selectable{0x87,ThousandBulls::id,0x80};
                                            vitals.insert(vitals.begin(),selectable.begin(),selectable.end());
                                        }
                                        if(config.diagnostic_level_snapshot || config.diagnostic_shunying_manual) {
                                            const auto role=database.recovered_characters().load_role(session.account_id,session.character_id);
                                            if(!role) throw std::runtime_error("Missing initial diagnostic role snapshot");
                                            vitals.insert(vitals.begin(),role->logical.begin(),role->logical.end());
                                        }
                                        if(diagnostic_combat) {
                                            // CUSTOM-0010: isolated single-action C++ transaction + Lua test rule.
                                            std::vector<BattleActor> actors{
                                                {0,session.character_id,initial_hp,120,config.diagnostic_battle_revival ? 80u : initial_mp,80,31,40,8,10},
                                                {14,0,150,150,0,0,20,25,13,6}};
                                            if(config.diagnostic_shunying_manual) actors=diagnostic_shunying_manual_actors(session.character_id,
                                                manual_resources ? &*manual_resources : nullptr,diagnostic_shunying_manual_slot,
                                                config.diagnostic_recording_fixed_damage?RecordingCombatTest::monster_hp:10000);
                                            // CUSTOM-0017: living ally receives a real staged lethal action below.
                                            if(config.diagnostic_battle_revival)
                                                actors.push_back({1,0,4,120,5,20,31,40,8,10});
                                            RecoveredBattleService::Policy policy{0,0,0,0,
                                                BattleAction{0,{},false,100,100,0,0,150},{},true};
                                            // CUSTOM-0011: explicit lethal test power, not production balance.
                                            if(config.diagnostic_battle_terminal && config.diagnostic_battle_rounds==1) policy.basic.power_percent=1000;
                                            // CUSTOM-0012: test policy only, not the native skill's formula.
                                            if(config.diagnostic_battle_skill_settlement && !owned_shunying && !owned_thousand_bulls)
                                                policy.skills.emplace(RecoveredBattleService::skill_key(static_cast<std::uint8_t>(config.diagnostic_battle_skill_kind),1),
                                                    BattleAction{0,{},true,config.diagnostic_battle_terminal && config.diagnostic_battle_rounds==1 ? 1000u : 150u,100,8,0,150});
                                            policy.diagnostic_retaliation=BattleAction{14,{0},false,100,100,0,0,150};
                                            policy.diagnostic_player_initial_control=config.diagnostic_battle_player_appearance;
                                            if(config.diagnostic_shunying_manual) {
                                                // CUSTOM-0058: temporary trial policy; native client bridge renders clones.
                                                policy.skills.clear();policy.diagnostic_retaliation.reset();
                                                policy.diagnostic_manual_receipts=true;
                                                policy.client_actor=diagnostic_shunying_manual_slot;
                                                policy.actor_position=diagnostic_shunying_manual_slot;
                                                policy.basic.source=diagnostic_shunying_manual_slot;
                                                if(config.diagnostic_thousand_bulls_manual) {
                                                    ThousandBulls::authorize(policy,policy.basic,
                                                        [&,session_id=session.id()](const auto& state,const auto& result){
                                                            if(config.diagnostic_recording_fixed_damage)
                                                                return diagnostic_recording_bulls_reply(state,result,diagnostic_rounds_granted.at(session_id)-1);
                                                            return thousand_bulls_reply(state,result,diagnostic_rounds_granted.at(session_id)-1);
                                                        });
                                                    if(config.diagnostic_recording_fixed_damage)
                                                        ShunyingSanshazhan::authorize(policy,ShunyingSanshazhan::owned_action(policy.basic),
                                                            [&,session_id=session.id()](const auto& state,const auto& result){
                                                                return diagnostic_shunying_manual_reply(state,diagnostic_recording_display(result),diagnostic_rounds_granted.at(session_id)-1);
                                                            });
                                                } else ShunyingSanshazhan::authorize(policy,
                                                    BattleAction{diagnostic_shunying_manual_slot,{},ShunyingSanshazhan::magical,
                                                        ShunyingSanshazhan::provisional_power_percent,100,0,0,150},
                                                    [&,session_id=session.id()](const auto& state,const auto& result) {
                                                        return diagnostic_shunying_manual_reply(state,result,
                                                            diagnostic_rounds_granted.at(session_id)-1);
                                                    });
                                            }
                                            if(owned_shunying) {
                                                ShunyingSanshazhan::authorize(policy,ShunyingSanshazhan::owned_action(policy.basic),
                                                    [&,session_id=session.id()](const auto& state,const auto& result) {
                                                        // A surviving target is followed by the existing AI
                                                        // action, whose encoder closes this same cycle with88.
                                                        return shunying_sanshazhan_reply(state,result,
                                                            diagnostic_rounds_granted.at(session_id)-1,
                                                            state.state==BattleState::Finished);
                                                    });
                                            }
                                            if(owned_thousand_bulls) {
                                                ThousandBulls::authorize(policy,policy.basic,
                                                    [&,session_id=session.id()](const auto& state,const auto& result){
                                                        return thousand_bulls_reply(state,result,diagnostic_rounds_granted.at(session_id)-1,
                                                            state.state==BattleState::Finished);
                                                    });
                                            }
                                            if(config.diagnostic_battle_skill_kind==1) {
                                                // CUSTOM-0012: named loopback spell fixture only.
                                                // Reissue the native grant after bootstrap's initial0B.
                                                policy.diagnostic_initial_control_reply=[] {
                                                    std::array<std::uint8_t,17> grant{};
                                                    grant[0]=0x86;grant[1]=5;grant[3]=1;
                                                    return RecoveredWorldFrame::encode(grant);
                                                };
                                            }
                                            // CUSTOM-0035: only the isolated quest battle settles
                                            // the current client's expired command as an enemy turn.
                                            policy.diagnostic_timeout_action2=config.diagnostic_town_battle_after_quest &&
                                                !config.diagnostic_battle_revival;
                                            policy.diagnostic_second_encounter_entry=config.diagnostic_encounter_limit==2 &&
                                                diagnostic_encounters_started.at(session.id())==2;
                                            if(config.diagnostic_battle_mp_refusal) {
                                                // CUSTOM-0012: unqualified client recovery candidate, isolated only.
                                                policy.diagnostic_mp_refusal=[](const BattleSnapshot& state,const BattleAction& action,const InsufficientBattleMp&) {
                                                    const auto& actor=*state.actors[action.source];
                                                    const auto mp=diagnostic_battle_mp(action.source,actor.mp,actor.max_mp);
                                                    std::vector<std::uint8_t> logical(mp.begin(),mp.end());
                                                    std::array<std::uint8_t,17> grant{};
                                                    grant[0]=0x86;grant[1]=5;grant[3]=1;grant[4]=action.source;
                                                    logical.insert(logical.end(),grant.begin(),grant.end());
                                                    return RecoveredWorldFrame::encode(logical);
                                                };
                                            }
                                            // CUSTOM-0010: animation run07 preserves the enemy selection in 0B.
                                            if(config.diagnostic_battle_animations) policy.diagnostic_control_targets={0,1};
                                            policy.diagnostic_three_round_friendly_receipts=config.diagnostic_battle_rounds==3;
                                            policy.diagnostic_first_exchange_resume=first_exchange_resume;
                                            policy.diagnostic_second_exchange_resume=second_exchange_resume;
                                            if(config.diagnostic_battle_revival) {
                                                policy.diagnostic_retaliation.reset();
                                                policy.diagnostic_control_targets={1,0};
                                                policy.diagnostic_revival=RecoveredBattleService::DiagnosticRevival{
                                                    [&lua](const RevivalInput& input){return lua.revival(input);},
                                                    diagnostic_revival_reply,true};
                                            }
                                            diagnostic_rounds_granted.emplace(session.id(),second_exchange_resume ? 3 : (first_exchange_resume ? 2 : 1));
                                            if(config.diagnostic_visibility_checkpoint && pending_checkpoint) {
                                                if(first_exchange_resume)
                                                    validate_diagnostic_first_exchange(pending_checkpoint->checkpoint,session.character_id,
                                                        [&lua](const auto& input){return lua.combat_damage(input);});
                                                else if(pending_checkpoint->checkpoint!=Battle(battle_id,actors,123).checkpoint())
                                                    throw std::runtime_error("Visibility recovery requires qualified checkpoint");
                                            }
                                            session.set_state(SessionState::InBattle);
                                            Battle battle=pending_checkpoint ? Battle::restore(pending_checkpoint->checkpoint) : Battle(battle_id,actors,123);
                                            if(config.diagnostic_battle_revival) {
                                                if(durable_resources && !pending_checkpoint) {
                                                    auto& repo=static_cast<SqliteRecoveredCharacterRepository&>(database.recovered_characters());
                                                    revival_checkpoint=std::make_shared<StoredBattleCheckpoint>(repo.commit_checkpoint(
                                                        session.account_id,session.character_id,{},*durable_resources,battle.checkpoint(),
                                                        *durable_resources,"CUSTOM-0012/diagnostic-v1"));
                                                    durable_resources->revision=revival_checkpoint->resource_revision;
                                                }
                                                if(pending_checkpoint) {
                                                    revival_checkpoint=std::make_shared<StoredBattleCheckpoint>(*pending_checkpoint);
                                                    vitals=diagnostic_revival_resume_participants(session.character_id,*pending_checkpoint->revival);
                                                } else vitals=diagnostic_revival_death_setup(session.character_id,battle,
                                                    [&lua](auto input){return lua.combat_damage(input);});
                                                if(revival_checkpoint) {
                                                    auto& repo=static_cast<SqliteRecoveredCharacterRepository&>(database.recovered_characters());
                                                    if(!pending_checkpoint) *revival_checkpoint=repo.commit_checkpoint(session.account_id,session.character_id,
                                                        *revival_checkpoint,*durable_resources,battle.checkpoint(),*durable_resources,revival_checkpoint->policy_id);
                                                    durable_resources->revision=revival_checkpoint->resource_revision;
                                                    resource_commit=[&repo,owner=&session,service=diagnostic_combat.get(),
                                                        saved=durable_resources,stored=revival_checkpoint](const auto& before,const auto& after) {
                                                        if(stored->checkpoint!=before) throw std::runtime_error("Revival checkpoint diverged");
                                                        auto phase=service->checkpoint_revival(*owner);
                                                        if(stored->revival && *stored->revival!=phase)
                                                            throw std::runtime_error("Revival action phase diverged");
                                                        phase.battle=after;phase.action_received=true;phase.control_received=false;
                                                        auto resources=*saved;resources.hp=after.snapshot.actors[0]->hp;
                                                        resources.mp=after.snapshot.actors[0]->mp;
                                                        if(after.snapshot.state==BattleState::Finished) {
                                                            StoredBattleCheckpoint terminal{after,0,stored->policy_id,{}};
                                                            auto settled=repo.settle_checkpoint(owner->account_id,owner->character_id,
                                                                *stored,*saved,after,resources,after.snapshot.victorious_side==0,0);
                                                            terminal.resource_revision=settled.resources.revision;
                                                            *stored=std::move(terminal);*saved=std::move(settled.resources);
                                                            return;
                                                        }
                                                        auto committed=repo.commit_checkpoint(owner->account_id,owner->character_id,
                                                            *stored,*saved,after,resources,stored->policy_id,phase);
                                                        resources.revision=committed.resource_revision;
                                                        *stored=std::move(committed);*saved=std::move(resources);
                                                    };
                                                }
                                                const std::array<std::uint8_t,3> selectable{0x87,8,0x83};
                                                vitals.insert(vitals.begin(),selectable.begin(),selectable.end());
                                            }
                                            if((config.diagnostic_level_snapshot || config.diagnostic_visibility_checkpoint) && !pending_checkpoint) {
                                                auto& repo=static_cast<SqliteRecoveredCharacterRepository&>(database.recovered_characters());
                                                if(!durable_resources) throw std::runtime_error("Missing checkpoint resource baseline");
                                                const auto stored=repo.commit_checkpoint(session.account_id,session.character_id,{},*durable_resources,
                                                    battle.checkpoint(),*durable_resources,"CUSTOM-0012/diagnostic-v1");
                                                durable_resources->revision=stored.resource_revision;
                                            }
                                            if(config.owned_battle_pose_enabled) {
                                                // CUSTOM-0103: retain the ACTUAL final bootstrap
                                                // bytes being returned below. This existing diagnostic
                                                // producer is not ordinary shared PvP or a Written ACK.
                                                policy.pose_publication=RecoveredBattlePose::publication(vitals);
                                                if(!policy.pose_publication)
                                                    throw std::runtime_error("Battle pose actual bootstrap is not qualified");
                                            }
                                            diagnostic_combat->bind(session,std::move(battle),policy,
                                                [&,terminal=config.diagnostic_battle_terminal,
                                                 player=config.diagnostic_battle_player_appearance,
                                                 session_id=session.id()](const BattleSnapshot& state,const BattleActionResult& result) {
                                                    if(config.diagnostic_shunying_manual)
                                                        return diagnostic_shunying_manual_basic_reply(state,
                                                            config.diagnostic_recording_fixed_damage?diagnostic_recording_display(result):result,
                                                            diagnostic_rounds_granted.at(session_id)-1);
                                                    std::vector<std::uint8_t> logical;
                                                    if(result.mp_cost) {
                                                        const auto& caster=*state.actors[result.source];
                                                        const auto mp=diagnostic_battle_mp(result.source,caster.mp,caster.max_mp);
                                                        logical.insert(logical.end(),mp.begin(),mp.end());
                                                    }
                                                    for(const auto& hit:result.hits) {
                                                        if(config.diagnostic_battle_animations) {
                                                            const auto animation=config.diagnostic_battle_skill_settlement && result.source==0 && result.mp_cost
                                                                ? diagnostic_battle_skill_animation(result.source,hit.target,hit.hp_loss,0,state.actors[hit.target]->hp>0,
                                                                    static_cast<std::uint8_t>(config.diagnostic_battle_skill_kind))
                                                                : diagnostic_battle_basic_animation(result.source,hit.target,hit.hp_loss,result.source==14 ? 1 : 0,state.actors[hit.target]->hp>0);
                                                            logical.insert(logical.end(),animation.begin(),animation.end());
                                                        }
                                                        const auto& target=*state.actors[hit.target];
                                                        const auto maximum_hp=RecoveredBattleBootstrap::native_hp_dword(target.max_hp);
                                                        const auto current_hp=RecoveredBattleBootstrap::native_hp_dword(target.hp);
                                                        RecoveredBattleVitals::Bytes record{};
                                                        record[0]=0x86;record[2]=hit.target;
                                                        for(unsigned i=0;i<4;++i) {
                                                            record[5+i]=static_cast<std::uint8_t>(maximum_hp>>(8*i));
                                                            record[9+i]=static_cast<std::uint8_t>(current_hp>>(8*i));
                                                        }
                                                        const auto parsed=RecoveredBattleVitals::parse_logical(record);
                                                        if(!parsed) throw std::runtime_error("Diagnostic damage encoding rejected");
                                                        const auto bytes=RecoveredBattleVitals::encode_logical(*parsed);
                                                        logical.insert(logical.end(),bytes.begin(),bytes.end());
                                                    }
                                                    if(terminal && !player && state.state==BattleState::Finished) {
                                                        const auto outcome=diagnostic_battle_zero_result();
                                                        logical.insert(logical.end(),outcome.begin(),outcome.end());
                                                    }
                                                    // CUSTOM-0009: current-cycle snapshot resets the native
                                                    // control latch; the next grant still waits for its receipt.
                                                    if(player && ((result.source==14 && state.state==BattleState::Active) ||
                                                                  (config.diagnostic_battle_revival && result.source==0 && state.state==BattleState::Active) ||
                                                                  (terminal && state.state==BattleState::Finished))) {
                                                        RecoveredBattleVitalsBatch::Bytes bulk{};bulk[0]=0x88;
                                                        // CUSTOM-0017: revival already consumed cycle1;
                                                        // its no-retaliation followup settles cycle2 here.
                                                        // A fresh restored client counts cycles from zero.
                                                        bulk[1]=config.diagnostic_battle_revival && config.diagnostic_resume_checkpoint ?
                                                            static_cast<std::uint8_t>(diagnostic_rounds_granted.at(session_id)-1) :
                                                            static_cast<std::uint8_t>(diagnostic_rounds_granted.at(session_id)-
                                                            (config.diagnostic_battle_revival ? 0 : 1));
                                                        for(unsigned slot=0;slot<14;++slot) if(state.actors[slot]) {
                                                            const auto current_hp=RecoveredBattleBootstrap::native_hp_dword(state.actors[slot]->hp);
                                                            for(unsigned i=0;i<4;++i) {
                                                                bulk[5+slot*8+i]=static_cast<std::uint8_t>(current_hp>>(8*i));
                                                                bulk[9+slot*8+i]=static_cast<std::uint8_t>(state.actors[slot]->mp>>(8*i));
                                                            }
                                                        }
                                                        logical.insert(logical.end(),bulk.begin(),bulk.end());
                                                    }
                                                    return RecoveredWorldFrame::encode(logical);
                                                },{},std::move(resource_commit));
                                            if(config.diagnostic_visibility_battle)
                                                deliver_visibility(player_visibility.set_fight_title(session.id(),
                                                    session.account_id,session.character_id,{2,15},true));
                                            if(revival_checkpoint) {
                                                if(pending_checkpoint) {
                                                    diagnostic_combat->restore_revival_phase(session,*pending_checkpoint->revival);
                                                    diagnostic_combat->expect_revival_reconnect_notice(session);
                                                }
                                                auto& repo=static_cast<SqliteRecoveredCharacterRepository&>(database.recovered_characters());
                                                diagnostic_combat->set_revival_phase_commit(session,
                                                    [&repo,owner=&session,saved=durable_resources,stored=revival_checkpoint](const auto& before,const auto& after) {
                                                        if(!stored->revival || *stored->revival!=before)
                                                            throw std::runtime_error("Revival receipt phase diverged");
                                                        *stored=repo.commit_revival_phase(owner->account_id,owner->character_id,*stored,*saved,after);
                                                    });
                                            }
                                        }
                                        spdlog::warn("DIAGNOSTIC_VITALS88_SENT_AFTER_TIMER36 session_id={}",session.id());
                                        return std::optional<std::vector<std::uint8_t>>(RecoveredWorldFrame::encode(vitals));
                                    }
                                    return std::optional<std::vector<std::uint8_t>>(std::vector<std::uint8_t>{});
                                }
                            }
                            // CUSTOM-0028: only a qualified completed town save may enter the isolated indoor fixture.
                            if(config.native_monster_placements_only && config.diagnostic_battle_transition &&
                               records.size()==1 && std::holds_alternative<RecoveredWorldRecords::Tick>(records.front()) &&
                               native_monster_placement_gap_logged.insert(session.id()).second)
                                spdlog::warn("NATIVE_MONSTER_PLACEMENT_GAP session_id={} suppressed=diagnostic_encounter missing=original_spawn_or_encounter_assignment",session.id());
                            const auto town_battle_ready=[&] {
                                if(!config.diagnostic_town) return true;
                                if(!config.diagnostic_town_battle_after_quest || !session.character_id) return false;
                                const auto position=database.recovered_characters().load_position(session.account_id,session.character_id);
                                const auto progress=supply_repository.load_town_guide_progress(session.account_id,session.character_id);
                                const auto bag=supply_repository.load_saved_supply_slots(session.account_id,session.character_id);
                                const auto has_map=std::any_of(bag.begin(),bag.end(),[&](const auto& entry) {
                                    const auto& slot=entry.second;
                                    return slot.item_id==5569 && slot.count==1 && slot.source_sha256==supply_source;
                                });
                                return position && position->area==2 && position->scene==15 &&
                                    position->x==18 && position->y==12 && progress && progress->stage==3 &&
                                    has_map &&
                                    !supply_repository.has_settled_diagnostic_battle(session.account_id,session.character_id);
                            };
                            if(!config.native_monster_placements_only && config.diagnostic_battle_transition && !diagnostic_battle_sent.contains(session.id()) &&
                                (!config.diagnostic_shunying_manual || session.character_id==config.diagnostic_shunying_character_id) &&
                                town_battle_ready() &&
                                (!config.diagnostic_visibility_battle || (session.character_id==1 && player_visibility.size()>=2)) &&
                                diagnostic_encounters_started.at(session.id())<config.diagnostic_encounter_limit &&
                                (!config.diagnostic_battle_after_movement ||
                                 (diagnostic_movement_ready.contains(session.id()) && diagnostic_movement_ready.at(session.id()))) &&
                                records.size()==1 && std::holds_alternative<RecoveredWorldRecords::Tick>(records.front())) {
                                auto accepted=recovered_world->handle(session,records);
                                if(!accepted) return accepted;
                                // CUSTOM-0033: native 1117C4/1117FE takes its initial command
                                // window from battle context byte +41. The town fixture uses 30;
                                // other diagnostics preserve their previously qualified context.
                                constexpr std::uint32_t town_command_seconds=30;
                                const auto entry=RecoveredBattleEntry::encode_logical({0,
                                    config.diagnostic_shunying_manual ? 255u<<8 :
                                    config.diagnostic_town_battle_after_quest ? town_command_seconds<<8 : 0});
                                std::vector<std::uint8_t> logical(entry.begin(),entry.end());
                                if(config.diagnostic_battle_skill_seed && diagnostic_encounters_started.at(session.id())==0 &&
                                   (config.diagnostic_shunying_manual ||
                                    (!database.companions().selected_deity_has_skill(session.account_id,session.character_id,
                                        ShunyingSanshazhan::kind,ShunyingSanshazhan::id) &&
                                     !database.companions().selected_deity_has_skill(session.account_id,session.character_id,
                                        ThousandBulls::kind,ThousandBulls::id)))) {
                                    if(config.diagnostic_shunying_manual) {
                                        if(config.diagnostic_thousand_bulls_manual) {
                                            if(config.diagnostic_recording_fixed_damage){
                                                const auto seed=diagnostic_recording_skills();
                                                logical.insert(logical.begin(),seed.begin(),seed.end());
                                            }else{
                                                const auto seed=diagnostic_thousand_bulls_manual_seed();
                                                logical.insert(logical.begin(),seed.begin(),seed.end());
                                            }
                                        } else {
                                            const auto seed=diagnostic_shunying_manual_seed();
                                            logical.insert(logical.begin(),seed.begin(),seed.end());
                                        }
                                    } else {
                                        const auto seed=config.diagnostic_battle_revival ?
                                            diagnostic_revival_skill_seed() : diagnostic_battle_skill_seed(static_cast<std::uint8_t>(config.diagnostic_battle_skill_kind));
                                        logical.insert(logical.begin(),seed.begin(),seed.end());
                                    }
                                }
                                auto wire=RecoveredWorldFrame::encode(logical);
                                // CUSTOM-0014/CUSTOM-0016: keep the settled first battle's
                                // vitals admission through world supply. Reset only when the
                                // next battle actually starts, before its Timer36 bootstrap.
                                if(diagnostic_encounters_started.at(session.id())>0)
                                    diagnostic_vitals_sent.erase(session.id());
                                diagnostic_battle_sent.insert(session.id());
                                ++diagnostic_encounters_started.at(session.id());
                                if(config.diagnostic_town_player_visibility) {
                                    if(const auto present=player_visibility.snapshot(session.id())) {
                                        pending_visibility.insert_or_assign(session.id(),*present);
                                        deliver_visibility(player_visibility.leave(session.id()));
                                        visibility_sessions.erase(session.id());
                                    }
                                }
                                spdlog::warn("DIAGNOSTIC_BATTLE_TRANSITION_SENT session_id={} context_b={:08x}; vitals deferred; no gameplay binding",
                                    session.id(),config.diagnostic_town_battle_after_quest ? town_command_seconds<<8 : 0);
                                return std::optional<std::vector<std::uint8_t>>(std::move(wire));
                            }
                            const auto handle_world=[&] {
                                try { return recovered_world->handle(session,records); }
                                catch(const std::exception& error) {
                                    if(config.diagnostic_battle_player_appearance)
                                        spdlog::error("DIAGNOSTIC_PLAYER_HANDLER_EXCEPTION {}",error.what());
                                    throw;
                                }
                            };
                            auto reply=handle_world();
                            if(config.diagnostic_battle_player_appearance)
                                spdlog::info("DIAGNOSTIC_PLAYER_REPLY accepted={} bytes={}",reply.has_value(),reply ? reply->size() : 0);
                            if(reply && config.diagnostic_battle_revival && config.diagnostic_resume_checkpoint &&
                               diagnostic_combat && records.size()==1 &&
                               std::holds_alternative<RecoveredBattleCommand::Action2Request>(records.front()) &&
                               diagnostic_combat->diagnostic_round_ready(session)) {
                                const auto& state=diagnostic_combat->inspect(session.id());
                                std::array<std::uint8_t,17> grant{};grant[0]=0x86;grant[1]=5;grant[3]=1;
                                const auto wire=RecoveredWorldFrame::encode(grant);
                                reply->insert(reply->end(),wire.begin(),wire.end());
                                diagnostic_combat->rearm_diagnostic(session,state.revision);
                                spdlog::warn("DIAGNOSTIC_REVIVAL_RESUME_REARMED session_id={} custom_not_native",session.id());
                            }
                            std::vector<std::uint8_t> deferred_outcome;
                            std::optional<bool> diagnostic_terminal_won;
                            if(reply && config.diagnostic_battle_terminal && config.diagnostic_battle_player_appearance &&
                               diagnostic_combat && session.state()==SessionState::InBattle) {
                                // CUSTOM-0011: prepare/reserve before release; finished action alone
                                // does not authorize the result or return to world.
                                const auto& state=diagnostic_combat->inspect(session.id());
                                if(state.state==BattleState::Finished) {
                                    if(!state.victorious_side) throw std::runtime_error("Finished diagnostic battle lacks winner");
                                    diagnostic_terminal_won=*state.victorious_side==0;
                                }
                                const auto award=state.state==BattleState::Finished && state.victorious_side==0 ?
                                    config.diagnostic_battle_experience : 0;
                                deferred_outcome=RecoveredWorldFrame::encode(diagnostic_battle_experience_result(award));
                                if(config.diagnostic_role_progress && state.state==BattleState::Finished) {
                                    const auto saved=database.recovered_characters().load_resources(session.account_id,session.character_id);
                                    if(!saved) throw std::runtime_error("Missing committed role progress resources");
                                    std::uint16_t display=2500;
                                    if(config.diagnostic_level_snapshot) {
                                        const auto role=database.recovered_characters().load_role(session.account_id,session.character_id);
                                        if(!role) throw std::runtime_error("Missing committed level snapshot");
                                        const auto parsed=RecoveredRoleLevel::parse(role->logical);
                                        if(!parsed || parsed->max_hp()!=saved->max_hp || parsed->max_mp()!=saved->max_mp)
                                            throw std::runtime_error("Committed level/resource mismatch");
                                        display=parsed->progress_display();
                                        const auto level=RecoveredWorldFrame::encode(role->logical);
                                        deferred_outcome.insert(deferred_outcome.end(),level.begin(),level.end());
                                    } else if(config.diagnostic_progress_span) {
                                        const auto xp=database.recovered_characters().load_experience(session.account_id,session.character_id);
                                        if(!xp || xp->design_id!="CUSTOM-0012")
                                            throw std::runtime_error("Missing diagnostic XP provenance");
                                        // CUSTOM-0013: explicit test interval, not a production level curve.
                                        const auto projected=lua.progression({xp->total,{0,config.diagnostic_progress_span},2});
                                        if(projected.level!=1)
                                            throw std::runtime_error("Level transition is not enabled in progress-only probe");
                                        display=projected.progress_display;
                                    }
                                    const auto progress=RecoveredWorldFrame::encode(diagnostic_role_progress(saved->hp,saved->mp,display));
                                    deferred_outcome.insert(deferred_outcome.end(),progress.begin(),progress.end());
                                }
                                reply->reserve(reply->size()+deferred_outcome.size());
                            }
                            if(reply && config.diagnostic_battle_terminal && diagnostic_combat &&
                               diagnostic_combat->release_finished_diagnostic(session)) {
                                if((config.diagnostic_town_battle_after_quest || config.diagnostic_character_growth) &&
                                   (!diagnostic_terminal_won ||
                                    !diagnostic_town_battle_won.emplace(session.id(),*diagnostic_terminal_won).second))
                                    throw std::runtime_error("Town battle terminal outcome was not unique");
                                recovered_movement->resume_after_battle(session.id(),session.account_id,session.character_id);
                                if(config.diagnostic_visibility_battle)
                                    deliver_visibility(player_visibility.set_fight_title(session.id(),
                                        session.account_id,session.character_id,{2,15},false));
                                if(config.diagnostic_visibility_battle)
                                    pending_visibility_refresh.insert(session.id());
                                reply->insert(reply->end(),deferred_outcome.begin(),deferred_outcome.end());
                                diagnostic_rounds_granted.at(session.id())=0;
                                spdlog::warn("DIAGNOSTIC_FINISHED_BATTLE_RELEASED session_id={}; diagnostic settlement only",session.id());
                            }
                            if(reply && diagnostic_combat && diagnostic_rounds_granted.contains(session.id()) &&
                               (config.diagnostic_shunying_manual ||
                                diagnostic_combat->has_authorized_skill(session.id(),ShunyingSanshazhan::key) ||
                                diagnostic_combat->has_authorized_skill(session.id(),ThousandBulls::key) ||
                                diagnostic_rounds_granted.at(session.id())<config.diagnostic_battle_rounds ||
                                diagnostic_combat->diagnostic_timeout_round_ready(session)) &&
                               diagnostic_combat->diagnostic_round_ready(session)) {
                                const auto& state=diagnostic_combat->inspect(session.id());
                                RecoveredBattleVitalsBatch::Bytes bulk{};bulk[0]=0x88;
                                bulk[1]=static_cast<std::uint8_t>(diagnostic_rounds_granted.at(session.id())+
                                    (config.diagnostic_battle_revival && !config.diagnostic_resume_checkpoint ? 1 : 0));
                                for(unsigned slot=0;slot<14;++slot) if(state.actors[slot]) {
                                    const auto current_hp=RecoveredBattleBootstrap::native_hp_dword(state.actors[slot]->hp);
                                    for(unsigned i=0;i<4;++i) {
                                        bulk[5+slot*8+i]=static_cast<std::uint8_t>(current_hp>>(i*8));
                                        bulk[9+slot*8+i]=static_cast<std::uint8_t>(state.actors[slot]->mp>>(i*8));
                                    }
                                }
                                std::vector<std::uint8_t> logical(bulk.begin(),bulk.end());
                                std::array<std::uint8_t,17> grant{};grant[0]=0x86;grant[1]=5;grant[3]=1;
                                if(config.diagnostic_shunying_manual) grant[4]=diagnostic_shunying_manual_slot;
                                logical.insert(logical.end(),grant.begin(),grant.end());
                                const auto wire=RecoveredWorldFrame::encode(logical);
                                reply->insert(reply->end(),wire.begin(),wire.end());
                                diagnostic_combat->rearm_diagnostic(session,state.revision);
                                ++diagnostic_rounds_granted.at(session.id());
                                spdlog::warn("DIAGNOSTIC_NEXT_ROUND_GRANTED session_id={} round={} custom_not_native",session.id(),diagnostic_rounds_granted.at(session.id()));
                            }
                            // Project party position/vitals after the accepted
                            // handler commits movement/resources, not one later
                            // tick. This independent observer never alters the
                            // existing reply or the frozen chat/auth handlers.
                            if(reply && native_parties.party_size(session.id()))try {
                                auto next=native_parties;
                                const auto changes=refresh_party_members(next,next.participants(session.id()));
                                auto projected=party_projection(changes);native_parties=std::move(next);
                                deliver_parties(std::move(projected));
                            }catch(const std::exception& error){spdlog::warn("NATIVE_PARTY_REFRESH_FAILED reason={}",error.what());}
                            if(reply && owned_bag_projected.contains(session.id()) && !trade_wallet_sent.contains(session.id())) {
                                if(const auto wallet=database.trades().load_wallet(session.account_id,session.character_id)) {
                                    session.send_world_records(RecoveredTrade::wallet(wallet->amount));trade_wallet_sent.insert(session.id());
                                }
                            }
                            return reply;
                        };
                        game_handlers.guild_relations53=bool(guild53_routes);
                        game_handlers.beast_views=config.owned_beast_panel_enabled;
                        game_handlers.pk_invitations=config.owned_pk_invitation_enabled;
                        game_handlers.bf_requests=config.owned_daily_quest_views_enabled;
                        game_handlers.map_panel68=config.owned_map_views_enabled;
                        game_handlers.world_records=guild_ordered_world_records;
                        spdlog::warn("Recovered {} movement enabled; area=2 scene={}; position persistence enabled, speed policy and live acceptance unverified",
                            config.diagnostic_town?"town diagnostic":"indoor",config.diagnostic_town?4:15);
                    }
                }
                if(config.recovered_account_auth) game_handlers.authenticate_async=async_login;
                if(common_world) {
                    if(taiwan_native_characters.list) {
                        common_world_lifetime.vault->install_native_characters(std::move(taiwan_native_characters));
                        const auto list=common_world_lifetime.vault->native_list_facade();
                        const auto select=common_world_lifetime.vault->native_select_facade();
                        const auto list_current=common_world_lifetime.vault->native_list_current_facade();
                        const auto list_complete=common_world_lifetime.vault->native_list_complete_facade();
                        // Both actual listeners share the same game-owned native
                        // raw list/token sources. Network copies hold weak facades.
                        for(auto* handlers:{&character_handlers,&game_handlers}) {
                            handlers->list={};handlers->select_created={};handlers->select_existing={};
                            handlers->native_list=list;handlers->native_select=select;
                            handlers->native_list_current=list_current;handlers->native_list_complete=list_complete;
                        }
                    }
                    const bool native_characters=bool(game_handlers.native_list) && bool(game_handlers.native_select);
                    const bool legacy_characters=bool(game_handlers.list) && bool(game_handlers.select_created) && bool(game_handlers.select_existing);
                    if(!recovered_login || !game_handlers.authenticate_async || native_characters==legacy_characters ||
                       !game_handlers.create ||
                       !game_handlers.world_entry || !game_handlers.world_ready ||
                       bool(game_handlers.movement)==bool(game_handlers.world_records) ||
                       game_handlers.common_world_lifecycle || game_handlers.common_world_lifecycle_factory ||
                       game_handlers.common_world_cleanup_owner || game_handlers.common_world_lifecycle_abandon ||
                       game_handlers.common_world_publication_owner)
                        throw std::invalid_argument("Shared world host requires exclusive complete actual Taiwan handlers");
                    if(taiwan_entered_async.entered)
                        common_world_lifetime.vault->install(SharedTaiwanWorldLifecycle::factory_async(
                            common_world->presence(),common_world->visibility(),std::move(taiwan_entered_async),common_world->transports(),
                            taiwan_entry_identity),taiwan_entry_identity);
                    else common_world_lifetime.vault->install(SharedTaiwanWorldLifecycle::factory(
                            common_world->presence(),common_world->visibility(),std::move(taiwan_entered),common_world->transports(),
                            taiwan_entry_identity),taiwan_entry_identity);
                    if(taiwan_world_entry) {
                        if(!recovered_movement)throw std::invalid_argument("Full native TW entry requires actual movement bookkeeping");
                        common_world_lifetime.vault->install_entry(std::move(taiwan_world_entry));
                        game_handlers.world_entry=[&,entry=common_world_lifetime.vault->entry_facade(),identity=taiwan_entry_identity](
                            std::uint64_t session,std::uint64_t account,std::uint64_t character) {
                            const auto frame=entry(session,account,character);
                            if(identity==TaiwanWorldEntryIdentity::QualifiedSceneHandle)
                                recovered_movement->prepare_native_scene(session,account,character,frame);
                            else recovered_movement->prepare_native(session,account,character,frame);
                            return frame; // Same actual full frame; no candidate builder side effects.
                        };
                    }
                    game_handlers.common_world_lifecycle_factory=common_world_lifetime.vault->factory_facade();
                    game_handlers.common_world_cleanup_owner=common_world_lifetime.vault->cleanup_owner();
                    game_handlers.common_world_lifecycle_abandon=common_world_lifetime.vault->abandon_facade();
                    game_handlers.common_world_publication_owner=common_world_lifetime.vault->publication_owner();
                    if(taiwan_movement.movement) {
                        if(!taiwan_records.records && (game_handlers.world_records || !game_handlers.movement))
                            throw std::invalid_argument("Explicit native TW movement requires its exclusive movement dispatcher; mixed world records remain separately owned");
                        common_world_lifetime.vault->install_movement(std::move(taiwan_movement));
                        if(taiwan_records.records) {
                            const auto spectator6e=taiwan_records.spectator6e;
                            const auto spectator_close=taiwan_records.spectator_close;
                            const auto native_selection_input=taiwan_records.native_selection_input;
                            const auto native_skill_commands=taiwan_records.native_skill_commands;
                            common_world_lifetime.vault->install_records(std::move(taiwan_records));
                            game_handlers.movement={};
                            game_handlers.world_records=common_world_lifetime.vault->records_facade();
                            game_handlers.spectator6e=spectator6e;
                            game_handlers.spectator_close=spectator_close;
                            game_handlers.native_selection_input=native_selection_input;
                            game_handlers.native_skill_commands=native_skill_commands;
                        }else game_handlers.movement=common_world_lifetime.vault->movement_facade();
                    }
                }
                // Install AFTER the final legacy/common handler selection. This
                // wrapper owns only C89/8A; contiguous unrelated runs retain the
                // existing dispatcher and its already-framed reply order.
                if(owned_blacklist) {
                    if(!game_handlers.world_records || !game_handlers.world_ready)
                        throw std::invalid_argument("Owned blacklist requires actual world records and ready handlers");
                    game_handlers.owned_blacklist=true;
                    const auto ready=game_handlers.world_ready;
                    game_handlers.world_ready=[&,ready,lifetime=blacklist_lifetime](Session& session) {
                        if(!lifetime->load())return;
                        if(const auto at=blacklist_replays.find(session.id());at!=blacklist_replays.end() &&
                           at->second.session.lock().get()==&session)retire_blacklist_output(at->second);
                        ready(session); // Mark only after the genuine ready hook succeeds.
                        if(lifetime->load() && !session.closing() && session.account_id && session.character_id)
                            blacklist_replays.insert_or_assign(session.id(),BlacklistReplay{
                                session.shared_from_this(),session.account_id,session.character_id,session.battle_generation()});
                    };
                    const auto original=game_handlers.world_records;
                    struct BlacklistDispatch {bool reading=false,reentered=false;};
                    const auto dispatch=std::make_shared<BlacklistDispatch>();
                    game_handlers.world_records=[&,original,dispatch,lifetime=blacklist_lifetime](Session& session,
                            std::span<const RecoveredWorldRecords::Record> records)->std::optional<std::vector<std::uint8_t>> {
                        if(!lifetime->load())return {};
                        if(dispatch->reading){dispatch->reentered=true;return {};}
                        dispatch->reading=true;dispatch->reentered=false;
                        struct End {BlacklistDispatch& value;~End(){value.reading=false;}} end{*dispatch};
                        const auto held=session.shared_from_this();
                        std::optional<Session::NormalWorldInitialization> blacklist_invocation;
                        try {blacklist_invocation=session.normal_world_initialization();}
                        catch(const std::logic_error&) {} // A copied dispatcher facade cannot mint live submitted source.
                        const auto blacklist_invocation_current=[&] {
                            return blacklist_invocation && session.normal_world_initialization_current(*blacklist_invocation);
                        };
                        settle_blacklist_output(held);
                        const auto account=session.account_id,character=session.character_id,battle=session.battle_generation();
                        const auto phase=session.state();
                        const auto current=[&] {
                            return lifetime->load() && !dispatch->reentered && !session.closing() && session.recovered_world_ready() &&
                                account && character && session.account_id==account && session.character_id==character &&
                                session.battle_generation()==battle && session.state()==phase &&
                                (phase==SessionState::CharacterSelected || phase==SessionState::InWorld);
                        };
                        // Other gameplay phases keep the original dispatcher;
                        // blacklist records are never sent there without ownership.
                        const bool contains_blacklist=std::any_of(records.begin(),records.end(),[](const auto& r){
                            return std::holds_alternative<TaiwanNativeBlacklist::Request>(r);});
                        if(!current() && !contains_blacklist) {
                            if(const auto at=blacklist_replays.find(session.id());at!=blacklist_replays.end() &&
                               at->second.session.lock()==held)retire_blacklist_output(at->second);
                            return original(session,records);
                        }
                        std::vector<std::uint8_t> wire;
                        const auto append=[&](const std::vector<std::uint8_t>& bytes){wire.insert(wire.end(),bytes.begin(),bytes.end());};
                        const auto append_logical=[&](const std::vector<std::uint8_t>& logical){
                            if(!logical.empty())append(RecoveredWorldFrame::encode(logical));
                        };
                        const auto replay_current=[&] {
                            const auto at=blacklist_replays.find(session.id());
                            return at!=blacklist_replays.end() && at->second.session.lock().get()==held.get() &&
                                at->second.account==account && at->second.character==character &&
                                (at->second.done || at->second.battle==battle);
                        };
                        for(std::size_t i=0;i<records.size();) {
                            if(const auto* request=std::get_if<TaiwanNativeBlacklist::Request>(&records[i])) {
                                // CUSTOM-0096 initial replay gate: no mutations
                                // while bounded tombstone/active replay is pending.
                                if(current() && replay_current() && blacklist_replays.at(session.id()).done &&
                                   blacklist_replays.at(session.id()).snapshot && blacklist_replays.at(session.id()).snapshot->supported) {
                                    const auto source=blacklist_replays.at(session.id()); // Own exact map inputs before SQL.
                                    // Earlier admitted peer posts precede this job's original response post.
                                    // Pending may continue only while its entire actual attempt chain is current.
                                    if(blacklist_pending_source(source) && !blacklist_invocation_current()) {
                                        auto& now=blacklist_replays.at(session.id());now.live_disabled=true;
                                        retire_blacklist_output(now);session.close();return {};
                                    }
                                    if(!blacklist_chain_current(held,source))return {};
                                    std::optional<Session::NormalWorldResponseAttempt> response_attempt;
                                    if(blacklist_invocation_current())
                                        response_attempt=session.capture_normal_world_response(*blacklist_invocation);
                                    if(source.own_response && source.own_response->status()==Session::NormalWorldResponseStatus::Pending &&
                                       (!response_attempt || *source.own_response!=*response_attempt)) {
                                        auto& now=blacklist_replays.at(session.id());now.live_disabled=true;
                                        retire_blacklist_output(now);session.close();return {};
                                    }
                                    const auto response_current=[&] {
                                        return response_attempt && session.normal_world_response_callback_current(*response_attempt);
                                    };
                                    const auto source_current=[&] {
                                        if(!current() || !replay_current())return false;
                                        const auto& now=blacklist_replays.at(session.id());
                                        return now.done==source.done && now.cursor==source.cursor && now.active_phase==source.active_phase &&
                                            now.snapshot==source.snapshot && now.live_disabled==source.live_disabled &&
                                            now.output==source.output && now.live_pending==source.live_pending &&
                                            now.own_response==source.own_response && (!response_attempt || response_current()) &&
                                            (!blacklist_pending_source(now) || blacklist_invocation_current()) && blacklist_chain_current(held,now);
                                    };
                                    struct PreparedPeer {
                                        std::shared_ptr<Session> session;
                                        BlacklistReplay source;
                                        std::shared_ptr<BlacklistLivePending> delivery;
                                    };
                                    // Own every candidate and preallocate delivery material before this SQL operation.
                                    std::vector<PreparedPeer> peers;peers.reserve(blacklist_replays.size());
                                    for(const auto& [id,replay]:blacklist_replays) {
                                        const auto peer=replay.session.lock();
                                        if(peer && peer!=held && replay.account==account && replay.character==character)
                                            peers.push_back({peer,replay,{}});
                                    }
                                    for(auto& peer:peers) {
                                        settle_blacklist_output(peer.session);
                                        const auto at=blacklist_replays.find(peer.session->id());
                                        if(at==blacklist_replays.end() || at->second.session.lock()!=peer.session)continue;
                                        peer.source=at->second;
                                        if(peer.source.done && peer.source.snapshot && peer.source.snapshot->supported &&
                                           !peer.source.live_disabled && peer.source.output &&
                                           (!peer.source.live_pending || peer.source.live_pending->depth<blacklist_attempt_limit) &&
                                           blacklist_chain_current(peer.session,peer.source) &&
                                           peer.session->normal_world_output_current_on_game(*peer.source.output)) {
                                            peer.delivery=std::make_shared<BlacklistLivePending>(peer.source.output,peer.source.live_pending);
                                        }
                                    }
                                    if(!source_current())return {};
                                    const auto change=owned_blacklist->handle_committed(account,character,*request,source_current);
                                    if(!source_current())return {};
                                    if(!change){++i;continue;} // Preserve old valid rejection: empty reply, continue records.
                                    const auto reply_begin=wire.size();
                                    append_logical(change->logical()); // Original no-op reply; durable COMMIT is never retried.
                                    const auto before=change->before_ptr(),after=change->after_ptr();
                                    const bool qualified=response_current() && blacklist_invocation_current() && *source.snapshot==*before;
                                    if(!qualified) {
                                        auto& now=blacklist_replays.at(session.id());const bool hazard=blacklist_pending_source(source);
                                        now.live_disabled=true;retire_blacklist_output(now);
                                        if(hazard){session.close();return {};}
                                    } else {
                                        // Actual append-owned framed bytes, not a substring claim about later output.
                                        // Session matches this ordered component at final frame boundaries.
                                        session.expect_normal_world_response(*response_attempt,
                                            std::span<const std::uint8_t>(wire).subspan(reply_begin));
                                        if(!response_current())return {};
                                        auto& now=blacklist_replays.at(session.id());now.own_response=*response_attempt;
                                        if(change->changed())now.snapshot=after; // Provisional until actual final FIFO Queued.
                                    }
                                    if(!change->changed() || !qualified){++i;continue;}
                                    for(auto& peer:peers) {
                                        const auto at=blacklist_replays.find(peer.session->id());
                                        if(at==blacklist_replays.end() || at->second.session.lock()!=peer.session)continue;
                                        const auto now=at->second; // Never carry an iterator through send/close.
                                        const bool same=now.account==account && now.character==character && now.done==peer.source.done &&
                                            now.snapshot==peer.source.snapshot && now.output==peer.source.output &&
                                            now.live_pending==peer.source.live_pending && now.live_disabled==peer.source.live_disabled &&
                                            now.own_response==peer.source.own_response;
                                        if(!same)continue;
                                        if(!peer.delivery || !now.snapshot || *now.snapshot!=*before ||
                                           !blacklist_chain_current(peer.session,now) ||
                                           !peer.session->normal_world_output_current_on_game(*peer.delivery->output)) {
                                            const bool hazard=blacklist_pending_source(now);
                                            at->second.live_disabled=true;retire_blacklist_output(at->second);
                                            if(hazard)peer.session->close(); // Actual old chain cannot skip this committed edge.
                                            continue;
                                        }
                                        const auto delivery=peer.delivery;
                                        std::copy(change->logical().begin(),change->logical().end(),delivery->logical.begin());
                                        delivery->logical.resize(change->logical().size()); // <=21, already allocated before COMMIT.
                                        try {
                                            delivery->attempt.emplace(peer.session->send_normal_world_records(*delivery->output,std::move(delivery->logical)));
                                            if(delivery->attempt->status()==Session::NormalWorldOutputStatus::Failed)
                                                throw std::runtime_error("Blacklist ordered submission failed");
                                            const auto posted=blacklist_replays.find(peer.session->id());
                                            if(posted==blacklist_replays.end() || posted->second.session.lock()!=peer.session ||
                                               posted->second.output!=now.output || posted->second.live_pending!=now.live_pending ||
                                               posted->second.snapshot!=now.snapshot || posted->second.own_response!=now.own_response ||
                                               posted->second.live_disabled ||
                                               !blacklist_chain_current(peer.session,posted->second) ||
                                               !peer.session->normal_world_output_current_on_game(*delivery->output))
                                                throw std::runtime_error("Blacklist submitted source retired");
                                            // Actual successful post, immutable core after, newest ordered-submitted endpoint.
                                            // Pending is admitted transport, not FIFO Queued, Written or native adoption.
                                            posted->second.live_pending=delivery;posted->second.snapshot=after;
                                        } catch(...) {
                                            delivery->output->revoke();
                                            const auto failed=blacklist_replays.find(peer.session->id());
                                            if(failed!=blacklist_replays.end() && failed->second.session.lock()==peer.session &&
                                               failed->second.output==now.output) {
                                                failed->second.live_disabled=true;retire_blacklist_output(failed->second);
                                            }
                                            peer.session->close(); // Durable SQL is never rerun or rolled back.
                                        }
                                        settle_blacklist_output(peer.session);
                                    }
                                }
                                ++i;continue;
                            }
                            const auto begin=i;bool tick=false;
                            while(i<records.size() && !std::holds_alternative<TaiwanNativeBlacklist::Request>(records[i])) {
                                tick=tick || std::holds_alternative<RecoveredWorldRecords::Tick>(records[i]);++i;
                            }
                            const bool tick_only=std::all_of(records.begin()+begin,records.begin()+i,[](const auto& r){
                                return std::holds_alternative<RecoveredWorldRecords::Tick>(r);});
                            if(!tick_only) {
                                const auto at=blacklist_replays.find(session.id());
                                if(at!=blacklist_replays.end() && at->second.session.lock()==held) {
                                    const bool pending=blacklist_pending_source(at->second);
                                    retire_blacklist_output(at->second);
                                    if(pending){at->second.live_disabled=true;session.close();return {};}
                                }
                            }
                            const auto reply=original(session,records.subspan(begin,i-begin));
                            if(!reply || dispatch->reentered)return {};
                            append(*reply); // Preserve successful unrelated phase/owner-policy transitions.
                            if(tick && current()) {
                                const auto at=blacklist_replays.find(session.id());
                                if(at!=blacklist_replays.end() && at->second.session.lock().get()==held.get() &&
                                   at->second.account==account && at->second.character==character &&
                                   !at->second.done && at->second.battle!=battle) {
                                    // A genuine successful World Tick after a battle
                                    // transition restarts this exact owner's bounded
                                    // replay. Previously queued frames remain FIFO;
                                    // never leave an old battle epoch permanently gated.
                                    auto& pending=at->second;pending.battle=battle;pending.cursor=0;
                                    pending.active_phase=false;pending.snapshot.reset();
                                }
                            }
                            if(tick && current() && replay_current() && !blacklist_replays.at(session.id()).done) {
                                const auto cursor=blacklist_replays.at(session.id()).cursor;
                                const auto active_phase=blacklist_replays.at(session.id()).active_phase;
                                const auto pinned=blacklist_replays.at(session.id()).snapshot;
                                const auto prior_response=blacklist_replays.at(session.id()).own_response;
                                if(!blacklist_chain_current(held,blacklist_replays.at(session.id())))return {};
                                std::optional<Session::NormalWorldResponseAttempt> replay_response;
                                if(blacklist_invocation_current())
                                    replay_response=session.capture_normal_world_response(*blacklist_invocation);
                                if(prior_response && prior_response->status()==Session::NormalWorldResponseStatus::Pending &&
                                   (!replay_response || *prior_response!=*replay_response))return {};
                                const auto replay_response_current=[&] {
                                    return !replay_response || session.normal_world_response_callback_current(*replay_response);
                                };
                                auto observed=owned_blacklist->observe(account,character,[&] {
                                    if(!current() || !replay_current())return false;
                                    const auto& now=blacklist_replays.at(session.id());
                                    return !now.done && now.cursor==cursor && now.active_phase==active_phase && now.snapshot==pinned &&
                                        now.own_response==prior_response && replay_response_current() && blacklist_chain_current(held,now);
                                });
                                if(pinned && observed!=*pinned)return {}; // Another Session changed this replay's complete source.
                                const auto material=pinned?pinned:std::make_shared<const SqliteOwnedBlacklistRepository::Snapshot>(std::move(observed));
                                const auto batch=OwnedBlacklistService::restore(*material,cursor,active_phase);
                                if(!current() || !replay_current() || blacklist_replays.at(session.id()).cursor!=cursor ||
                                   blacklist_replays.at(session.id()).active_phase!=active_phase ||
                                   blacklist_replays.at(session.id()).snapshot!=pinned ||
                                   blacklist_replays.at(session.id()).own_response!=prior_response || !replay_response_current())return {};
                                const auto reply_begin=wire.size();append_logical(batch.logical);
                                if(replay_response && !batch.logical.empty()) {
                                    session.expect_normal_world_response(*replay_response,
                                        std::span<const std::uint8_t>(wire).subspan(reply_begin));
                                    if(!replay_response_current())return {};
                                    blacklist_replays.at(session.id()).own_response=*replay_response;
                                }
                                auto& pending=blacklist_replays.at(session.id());pending.cursor=batch.last_row;pending.snapshot=material;
                                if(!material->supported){pending.done=true;continue;} // Valid non950 owner: only this feature unavailable.
                                if(batch.done && !active_phase){pending.active_phase=true;pending.cursor=0;}
                                else pending.done=batch.done;
                                // Attempt assembled in the existing response path;
                                // this is neither socket Written nor client ACK.
                            }
                            if(tick && current() && replay_current()) {
                                const auto source=blacklist_replays.at(session.id());
                                if(source.done && source.snapshot && source.snapshot->supported && !source.live_disabled &&
                                   !source.live_pending && !source.output) {
                                    const auto initialization=session.normal_world_initialization();
                                    if(initialization)if(auto output=session.capture_normal_world_output(*initialization)) {
                                        const auto owned=std::make_shared<const Session::NormalWorldOutputHandle>(std::move(*output));
                                        if(current() && replay_current() && blacklist_replays.at(session.id()).snapshot==source.snapshot &&
                                           !blacklist_replays.at(session.id()).live_disabled && !blacklist_replays.at(session.id()).output)
                                            blacklist_replays.at(session.id()).output=owned;
                                    }
                                }
                            }
                        }
                        return wire;
                    };
                }
                // CUSTOM-0097 discovery wraps the FINAL handler (including the
                // blacklist wrapper). NativeParty consent and frozen chat stay
                // in their original contiguous runs with already-framed replies.
                if(config.owned_party_directory_enabled) {
                    if(!game_handlers.world_records || !game_handlers.world_ready)throw std::invalid_argument("Party directory requires actual world and ready handlers");
                    game_handlers.owned_party_directory=true;
                    const auto original=game_handlers.world_records;
                    struct DirectoryDispatch {bool reading=false,reentered=false;};
                    const auto dispatch=std::make_shared<DirectoryDispatch>();
                    const auto observe_source=[&,dispatch](const std::shared_ptr<Session>& peer,
                            const OwnedPartyDirectory::Actor* previous,const Session* caller)->std::optional<OwnedPartyDirectory::Actor> {
                            if(!peer || dispatch->reentered || !recovered_movement)return {};
                            std::optional<Session::NormalWorldInitialization> init;
                            if(previous)init=previous->initialization;
                            else if(peer.get()==caller)init=peer->normal_world_initialization();
                            else if(const auto at=owned_companion_restoration_sources.find(peer->id());
                                at!=owned_companion_restoration_sources.end() && at->second->session.lock()==peer)
                                init=at->second->normal_initialization;
                            // Guard the genuine receipt's recorded game owner BEFORE
                            // reading another Session's game-owned identity fields.
                            if(!init || !init->entry_written() || !peer->normal_world_initialization_current_on_game(*init))return {};
                            const auto account=peer->account_id,character=peer->character_id,battle=peer->battle_generation();
                            const auto phase=peer->state();
                            const auto local=[&] {
                                return !dispatch->reentered && !peer->closing() && peer->recovered_world_ready() && account && character &&
                                    peer->account_id==account && peer->character_id==character && peer->battle_generation()==battle && peer->state()==phase &&
                                    (phase==SessionState::CharacterSelected || phase==SessionState::InWorld);
                            };
                            if(!local())return {};
                            // Obtain only this callback's genuine private transcript.
                            // Peers reuse their originally captured exact transcript.
                            if(!peer->normal_world_initialization_current_on_game(*init) || !local())return {};
                            const auto entry=RecoveredWorldEntryView::read(init->entry_frame());if(!entry)return {};
                            const auto location=recovered_movement->current_location(peer->id(),account,character);
                            if(!local() || !location)return {};
                            const auto roots=database.recovered_characters().list_for_account(account);if(!local())return {};
                            const RecoveredCharacter* root=nullptr;
                            for(const auto& row:roots)if(row.id==character){if(root)return {};root=&row;}
                            if(!root || root->account_id!=account || root->name_codepage!=950 || root->profile[29]<1 || root->profile[29]>8)return {};
                            const auto end=std::find(root->profile.begin(),root->profile.begin()+15,0);
                            if(end==root->profile.begin() || end==root->profile.begin()+15)return {};
                            const std::string encoded(reinterpret_cast<const char*>(root->profile.data()),end-root->profile.begin());
                            const auto name=OwnedCharacterNameText::from_encoded(encoded,950);if(!name || !local())return {};
                            const auto role=database.recovered_characters().load_role(account,character);if(!role || !local())return {};
                            const auto level=RecoveredRoleLevel::parse(role->logical);if(!level || !level->level())return {};
                            if(!peer->normal_world_initialization_current_on_game(*init) || !local() ||
                               recovered_movement->current_location(peer->id(),account,character)!=location || !local())return {};
                            // Full common IDs remain separate from the actual native
                            // actor handle. No truncation or artificial HP/common-ID cap.
                            return OwnedPartyDirectory::Actor{peer,peer->id(),account,character,battle,phase,*root,*role,*location,*init,
                                entry->actor_handle,encoded,level->level(),root->profile[29]};
                        };
                    const auto publish_watchers=[&,dispatch,observe_source](const OwnedPartyDirectory::Snapshot& before,
                        const OwnedPartyDirectoryService::WatchPlan& plan,const std::vector<OwnedPartyDirectory::Actor>& live,
                        const NativeParty& party_before,Session* caller,std::vector<std::uint8_t>* caller_wire)->bool {
                        std::map<std::uint64_t,std::shared_ptr<Session>> recipients;
                        auto merged=caller_wire?*caller_wire:std::vector<std::uint8_t>{};
                        if(config.max_sessions>std::numeric_limits<std::size_t>::max()/(RecoveredWorldFrame::max_logical_size+16))return false;
                        const auto byte_limit=config.max_sessions*(RecoveredWorldFrame::max_logical_size+16);
                        std::size_t total=0;
                        for(const auto& delivery:plan.deliveries) {
                            if(delivery.logical.empty() || delivery.logical.size()>RecoveredWorldFrame::max_logical_size)return false;
                            const auto peer=delivery.recipient.session.lock();if(!peer)return false;
                            if(std::none_of(live.begin(),live.end(),[&](const auto& actor){return actor.same(delivery.recipient);}))return false;
                            recipients.emplace(delivery.recipient.session_id,peer);
                            const auto frame=RecoveredWorldFrame::encode(delivery.logical);
                            if(frame.size()>byte_limit || total>byte_limit-frame.size())return false;
                            total+=frame.size();
                            if(caller_wire && peer.get()==caller)merged.insert(merged.end(),frame.begin(),frame.end());
                        }
                        // Hold all real incarnations through every observer and
                        // source publication; no weak successor lookup after commit.
                        std::vector<std::shared_ptr<Session>> held;
                        for(const auto& actor:live) {
                            const auto peer=actor.session.lock();if(!peer)return false;held.push_back(peer);
                            const auto current=observe_source(peer,&actor,caller);
                            if(!current || !actor.same(*current))return false;
                        }
                        for(const auto& actor:live) {
                            const auto peer=actor.session.lock();
                            if(!peer || !peer->normal_world_initialization_current_on_game(actor.initialization) ||
                               peer->closing() || peer->account_id!=actor.account || peer->character_id!=actor.character ||
                               peer->state()!=actor.phase || peer->battle_generation()!=actor.battle || !peer->recovered_world_ready())return false;
                        }
                        for(const auto& delivery:plan.deliveries) {
                            const auto peer=recipients.at(delivery.recipient.session_id);
                            if(peer!=delivery.recipient.session.lock() || peer->closing())return false;
                        }
                        // CUSTOM-0101: after ALL observers, a plan retaining AB
                        // must still own each original private entry epoch. A
                        // newer listing with identical bytes cannot renew it.
                        // An invalidated presentation already cleared by the
                        // prepared A7 is deliberately absent from this fence.
                        for(const auto& [id,q]:plan.state->queries)if(q.presentation) {
                            const auto& p=*q.presentation;
                            if(!OwnedPartyDirectoryService::captured_entry_current(p.owner) ||
                               !OwnedPartyDirectoryService::captured_entry_current(p.target))return false;
                            for(const auto& member:p.members)if(!OwnedPartyDirectoryService::captured_entry_current(member))return false;
                        }
                        if(dispatch->reentered || !native_parties.same_state(party_before) ||
                           !owned_party_directory->publish(before,plan.state))return false;
                        if(caller_wire)*caller_wire=std::move(merged);
                        for(const auto& delivery:plan.deliveries) {
                            const auto peer=recipients.at(delivery.recipient.session_id);
                            if(caller_wire && peer.get()==caller)continue;
                            try {peer->send_world_records(delivery.logical);}
                            catch(const std::exception& error) {
                                // Ordinary sender is submission only. Retire/close
                                // this exact recipient, never roll back other prefixes.
                                try{owned_party_directory->disconnect(*peer);}catch(...){}
                                try{peer->close();}catch(...){}
                                spdlog::warn("PARTY_DIRECTORY_WATCH_SUBMIT_FAILED reason={}",error.what());
                            }
                        }
                        return true;
                    };
                    const auto reconcile=[&,dispatch,observe_source,publish_watchers](const Session* retired,
                        Session* caller,std::vector<std::uint8_t>* caller_wire)->bool {
                        const auto before=owned_party_directory->snapshot();
                        std::map<std::uint64_t,OwnedPartyDirectory::Actor> candidates;
                        for(const auto& [id,listing]:before->listings)candidates.insert_or_assign(id,listing.actor);
                        for(const auto& [id,query]:before->queries) {
                            candidates.insert_or_assign(id,query.actor);
                            if(query.detail)for(const auto& member:query.detail->members)candidates.try_emplace(member.session_id,member);
                            if(query.presentation) {
                                candidates.try_emplace(query.presentation->target.session_id,query.presentation->target);
                                for(const auto& member:query.presentation->members)candidates.try_emplace(member.session_id,member);
                            }
                        }
                        std::vector<OwnedPartyDirectory::Actor> live;
                        std::vector<std::shared_ptr<Session>> held;
                        for(const auto& [id,previous]:candidates) {
                            const auto peer=previous.session.lock();if(!peer || peer.get()==retired)continue;
                            held.push_back(peer);const auto actor=observe_source(peer,&previous,caller);
                            if(actor)live.push_back(*actor);
                        }
                        if(dispatch->reentered || owned_party_directory->snapshot()!=before)return false;
                        const auto party_before=native_parties;
                        const auto plan=OwnedPartyDirectoryService::watch(before,before,live,party_before,config.max_sessions,0,retired);
                        return plan && publish_watchers(before,*plan,live,party_before,caller,caller_wire);
                    };
                    owned_party_directory_retire=[&,dispatch,reconcile](Session& session) {
                        if(dispatch->reading) {dispatch->reentered=true;owned_party_directory->disconnect(session);return;}
                        struct Reading {DirectoryDispatch& state;explicit Reading(DirectoryDispatch& s):state(s){state.reading=true;state.reentered=false;}~Reading(){state.reading=false;}} reading(*dispatch);
                        if(!reconcile(&session,nullptr,nullptr))owned_party_directory->disconnect(session);
                    };
                    const auto directory_ready=game_handlers.world_ready;
                    game_handlers.world_ready=[&,directory_ready](Session& session) {
                        directory_ready(session); // Existing ready and blacklist hook first.
                        try{owned_party_directory_retire(session);}
                        catch(const std::exception& error){spdlog::warn("PARTY_DIRECTORY_REENTRY_RETIRE_FAILED reason={}",error.what());}
                    };
                    game_handlers.world_records=[&,original,dispatch,observe_source,publish_watchers,reconcile](Session& session,
                        std::span<const RecoveredWorldRecords::Record> records)->std::optional<std::vector<std::uint8_t>> {
                        if(dispatch->reading){dispatch->reentered=true;return {};}
                        struct Reading {DirectoryDispatch& state;explicit Reading(DirectoryDispatch& s):state(s){state.reading=true;state.reentered=false;}~Reading(){state.reading=false;}} reading(*dispatch);
                        const auto self=session.shared_from_this();std::vector<std::uint8_t> wire;
                        const auto observe=[&](const std::shared_ptr<Session>& peer,const OwnedPartyDirectory::Actor* previous) {
                            return observe_source(peer,previous,&session);
                        };
                        for(std::size_t at=0;at<records.size();) {
                            if(!std::holds_alternative<TaiwanNativePartyMenu::Request>(records[at])) {
                                auto end=at+1;while(end<records.size() && !std::holds_alternative<TaiwanNativePartyMenu::Request>(records[end]))++end;
                                const auto reply=original(session,records.subspan(at,end-at));
                                if(!reply || dispatch->reentered)return {};
                                wire.insert(wire.end(),reply->begin(),reply->end());
                                try{(void)reconcile(nullptr,&session,&wire);}catch(const std::exception& error){spdlog::warn("PARTY_DIRECTORY_WATCH_REFRESH_FAILED reason={}",error.what());}
                                if(dispatch->reentered)return {};at=end;continue;
                            }
                            const auto request=std::get<TaiwanNativePartyMenu::Request>(records[at++]);
                            try {
                                if(request.opcode()==0x8d) {
                                    // Native has closed the window. Revoke this exact
                                    // incarnation before any other watcher/DB can fail.
                                    const auto before=owned_party_directory->snapshot();
                                    auto closed=std::make_shared<OwnedPartyDirectory::State>(*before);
                                    if(const auto query=closed->queries.find(session.id());query!=closed->queries.end() &&
                                       query->second.actor.session.lock()==self && query->second.actor.session_id==session.id())closed->queries.erase(query);
                                    if(request.logical[1]==2)if(const auto listing=closed->listings.find(session.id());listing!=closed->listings.end() &&
                                       listing->second.actor.session.lock()==self && listing->second.actor.session_id==session.id())closed->listings.erase(listing);
                                    if(!owned_party_directory->publish(before,std::move(closed)))continue;
                                    (void)reconcile(nullptr,&session,&wire); // Best effort after irreversible local retirement.
                                    continue;
                                }
                                auto before=owned_party_directory->snapshot();
                                // A new C90 retires this incarnation's old permission
                                // even when the new source is unavailable. CUSTOM-0101
                                // retains actual AB presentation until a new AB/A7 or
                                // query/window retirement; revocation is not native clear.
                                // Revocation needs no fresh DB identity observation.
                                if(request.opcode()==0x90) {
                                    const auto query=before->queries.find(session.id());
                                    if(query!=before->queries.end() && query->second.actor.session_id==session.id() &&
                                       query->second.actor.session.lock()==self &&
                                       (query->second.detail || !query->second.last_join_request.empty())) {
                                        auto retired=std::make_shared<OwnedPartyDirectory::State>(*before);
                                        auto& own_query=retired->queries.at(session.id());
                                        own_query.detail.reset();own_query.last_join_request.clear();
                                        if(!owned_party_directory->publish(before,retired))continue;
                                        before=std::move(retired);
                                    }
                                }
                                const OwnedPartyDirectory::Actor* prior=nullptr;
                                if(const auto found=before->queries.find(session.id());found!=before->queries.end())prior=&found->second.actor;
                                else if(const auto found=before->listings.find(session.id());found!=before->listings.end())prior=&found->second.actor;
                                const auto owner=observe(self,prior);if(!owner)continue; // Feature unavailable only.
                                std::vector<OwnedPartyDirectory::Actor> live{*owner};
                                std::vector<std::shared_ptr<Session>> retained{self};
                                for(const auto& [id,listing]:before->listings) {
                                    if(id==session.id())continue;
                                    const auto peer=listing.actor.session.lock();if(!peer)continue;
                                    retained.push_back(peer);
                                    const auto actor=observe(peer,&listing.actor);if(actor)live.push_back(*actor);
                                }
                                if(dispatch->reentered || owned_party_directory->snapshot()!=before)continue;
                                if(request.opcode()==0x90 || request.opcode()==0x91) {
                                    const auto query=before->queries.find(session.id());
                                    if(query==before->queries.end() || !query->second.actor.same_owner(*owner) ||
                                       std::find(query->second.visible.begin(),query->second.visible.end(),request.target())==query->second.visible.end())continue;
                                    const auto issued=query->second.issued.find(request.target());if(issued==query->second.issued.end())continue;
                                    const auto listing=before->listings.find(issued->second.session_id);
                                    if(listing==before->listings.end() || !listing->second.actor.same_owner(issued->second))continue;
                                    const auto target_peer=issued->second.session.lock();
                                    const auto target=observe(target_peer,&issued->second);if(!target || !target->same_owner(issued->second) ||
                                       target->position.area!=owner->position.area || target->position.scene!=owner->position.scene)continue;
                                    const auto party_before=std::make_shared<const NativeParty>(native_parties);
                                    const auto participants=party_before->participants(target->session_id);
                                    std::vector<OwnedPartyDirectory::Actor> members{*target};
                                    std::vector<std::uint64_t> other_ids;
                                    for(const auto id:participants)if(id!=target->session_id)other_ids.push_back(id);
                                    std::sort(other_ids.begin(),other_ids.end());
                                    bool qualified=true;
                                    for(const auto id:other_ids) {
                                        const auto at=party_sessions.find(id);const auto peer=at==party_sessions.end()?std::shared_ptr<Session>{}:at->second.lock();
                                        if(!peer){qualified=false;break;}retained.push_back(peer);
                                        const OwnedPartyDirectory::Actor* previous=nullptr;
                                        if(const auto item=before->listings.find(id);item!=before->listings.end())previous=&item->second.actor;
                                        else if(const auto item=before->queries.find(id);item!=before->queries.end())previous=&item->second.actor;
                                        const auto actor=observe(peer,previous);
                                        if(!actor || actor->position.area!=owner->position.area || actor->position.scene!=owner->position.scene){qualified=false;break;}
                                        members.push_back(*actor);
                                    }
                                    if(!qualified || members.size()!=participants.size())continue;
                                    std::map<std::uint16_t,std::uint64_t> handles;
                                    for(const auto& member:members) {
                                        if((member.native_actor==owner->native_actor && !member.same_owner(*owner)) ||
                                           !handles.emplace(member.native_actor,member.session_id).second){qualified=false;break;}
                                    }
                                    if(!qualified)continue;
                                    auto next_directory=std::make_shared<OwnedPartyDirectory::State>(*before);
                                    auto& next_query=next_directory->queries.at(session.id());
                                    next_query.actor=*owner;
                                    std::vector<std::uint8_t> logical;
                                    std::optional<NativeParty> next_party;
                                    std::map<std::uint64_t,std::vector<std::uint8_t>> projections;
                                    std::map<std::uint64_t,NativeParty::Member> legacy;
                                    if(request.opcode()==0x90) {
                                        // CUSTOM-0098 target first, then full Session order,
                                        // first four displayed; complete group retained for authority.
                                        std::vector<TaiwanNativePartyMenu::DetailRow> rows;
                                        for(const auto& actor:members) {
                                            if(rows.size()==4)break;
                                            const auto entry=RecoveredWorldEntryView::read(actor.initialization.entry_frame());if(!entry){qualified=false;break;}
                                            std::array<std::uint8_t,4> photo;std::copy_n(entry->logical.begin()+21,4,photo.begin());
                                            rows.push_back({actor.level,static_cast<std::uint8_t>(0x80u|actor.profession),photo,actor.name});
                                        }
                                        if(!qualified)continue;
                                        const auto detail=TaiwanNativePartyMenu::detail(target->native_actor,rows);if(!detail)continue;
                                        logical=*detail;
                                        next_query.detail=std::make_shared<const OwnedPartyDirectory::Detail>(OwnedPartyDirectory::Detail{
                                            *owner,*target,members,party_before,request.logical});
                                        next_query.presentation=std::make_shared<const OwnedPartyDirectory::Presentation>(OwnedPartyDirectory::Presentation{
                                            *owner,*target,members,participants,party_before->party_size(target->session_id)});
                                        next_query.last_join_request.clear();
                                    } else {
                                        const auto detail=query->second.detail;
                                        if(!detail || !detail->party || !OwnedPartyDirectoryService::captured_entry_current(detail->owner) ||
                                           !OwnedPartyDirectoryService::captured_entry_current(detail->target) ||
                                           !detail->owner.same_detail_identity(*owner) ||
                                           !detail->target.same_detail_identity(*target) || detail->target.native_actor!=request.target() ||
                                           detail->party->participants(target->session_id)!=participants ||
                                           detail->party->party_size(target->session_id)!=party_before->party_size(target->session_id) ||
                                           detail->members.size()!=members.size() || owner->same_owner(*target))continue;
                                        for(std::size_t i=0;i<members.size();++i)if(!OwnedPartyDirectoryService::captured_entry_current(detail->members[i]) ||
                                           !detail->members[i].same_detail_identity(members[i]))qualified=false;
                                        if(!qualified)continue;
                                        // Exact adapter to the unchanged CUSTOM-0062 identity
                                        // domain; other native/common mappings remain OPEN.
                                        if(owner->character>0x3fff || target->character>0x3fff ||
                                           owner->native_actor!=owner->character || target->native_actor!=target->character)continue;
                                        std::vector<OwnedPartyDirectory::Actor> relevant=members;
                                        if(std::none_of(relevant.begin(),relevant.end(),[&](const auto& a){return a.same_owner(*owner);}))relevant.push_back(*owner);
                                        // Existing handle rejects a requester already in a group.
                                        // Refuse it before touching cached members or projections.
                                        if(party_before->party_size(owner->session_id))continue;
                                        next_party=*party_before;
                                        std::map<std::uint64_t,NativeParty::Member> old;
                                        for(const auto& actor:relevant) {
                                            const auto peer=actor.session.lock();const auto at=party_sessions.find(actor.session_id);
                                            if(!peer || at==party_sessions.end() || at->second.lock()!=peer || actor.character>0x3fff || actor.native_actor!=actor.character){qualified=false;break;}
                                            const auto member=party_member(*peer);
                                            if(!member || !member->ready || member->account!=actor.account || member->character!=actor.character ||
                                               member->area!=actor.position.area || member->scene!=actor.position.scene || member->x!=actor.position.x || member->y!=actor.position.y){qualified=false;break;}
                                            legacy.emplace(actor.session_id,*member);
                                            if(const auto previous=next_party->member(actor.session_id))old.emplace(actor.session_id,*previous);
                                            next_party->observe(*member);
                                        }
                                        if(!qualified)continue;
                                        NativeParty::Deliveries deliveries;
                                        for(const auto& [id,previous]:old) {
                                            const auto refresh=next_party->refresh(id,previous);deliveries.insert(deliveries.end(),refresh.begin(),refresh.end());
                                        }
                                        const auto action=next_party->handle(session.id(),RecoveredParty::Request{RecoveredParty::Kind::Join,
                                            static_cast<std::uint32_t>(owner->character),static_cast<std::uint32_t>(target->character)},std::chrono::steady_clock::now());
                                        if(action.size()!=1 || action.front().event!=NativeParty::Event::Preview ||
                                           action.front().recipient!=target->session_id || action.front().actor.session!=owner->session_id)continue;
                                        deliveries.insert(deliveries.end(),action.begin(),action.end());
                                        projections=party_projection(deliveries); // Existing CUSTOM display supplier, not AB Photo4 authority.
                                        if(!projections.contains(target->session_id))continue;
                                        // Consume private C91 permission only. Actual AB
                                        // presentation remains tracked through consent and
                                        // subsequent relevant group changes (CUSTOM-0101).
                                        next_query.detail.reset();next_query.last_join_request=request.logical;
                                    }
                                    const auto framed=logical.empty()?std::vector<std::uint8_t>{}:RecoveredWorldFrame::encode(logical);
                                    auto merged=wire;merged.insert(merged.end(),framed.begin(),framed.end());
                                    // Include every recipient in the source fence; no stale
                                    // weak lookup may substitute another incarnation after commit.
                                    std::map<std::uint64_t,std::shared_ptr<Session>> recipients;
                                    for(const auto& [id,bytes]:projections) {
                                        if(bytes.empty() || bytes.size()>RecoveredWorldFrame::max_logical_size){qualified=false;break;}
                                        (void)RecoveredWorldFrame::encode(bytes); // Full projection/framing allocation before commit.
                                        const auto at=party_sessions.find(id);const auto peer=at==party_sessions.end()?std::shared_ptr<Session>{}:at->second.lock();
                                        if(!peer || !legacy.contains(id)){qualified=false;break;}recipients.emplace(id,peer);retained.push_back(peer);
                                    }
                                    if(!qualified)continue;
                                    auto check=live;for(const auto& actor:members)check.push_back(actor);
                                    for(const auto& actor:check) {
                                        const auto peer=actor.session.lock();const auto now=observe(peer,&actor);
                                        if(!now || !actor.same(*now)){qualified=false;break;}
                                    }
                                    for(const auto& [id,member]:legacy) {
                                        const auto at=party_sessions.find(id);const auto peer=at==party_sessions.end()?std::shared_ptr<Session>{}:at->second.lock();
                                        const auto now=peer?party_member(*peer):std::optional<NativeParty::Member>{};
                                        if(!now || *now!=member){qualified=false;break;}
                                    }
                                    for(const auto& actor:check) {
                                        const auto peer=actor.session.lock();
                                        if(!peer || peer->closing() || peer->account_id!=actor.account || peer->character_id!=actor.character ||
                                           peer->state()!=actor.phase || peer->battle_generation()!=actor.battle || !peer->recovered_world_ready() ||
                                           !peer->normal_world_initialization_current_on_game(actor.initialization)){qualified=false;break;}
                                    }
                                    for(const auto& [id,peer]:recipients) {
                                        const auto at=party_sessions.find(id);
                                        if(at==party_sessions.end() || at->second.lock()!=peer || peer->closing()){qualified=false;break;}
                                    }
                                    if(request.opcode()==0x91) {
                                        // CUSTOM-0101 final old-permission epoch fence
                                        // after every observer, independent of AB presentation.
                                        const auto& d=*query->second.detail;
                                        if(!OwnedPartyDirectoryService::captured_entry_current(d.owner) ||
                                           !OwnedPartyDirectoryService::captured_entry_current(d.target))qualified=false;
                                        for(const auto& member:d.members)if(!OwnedPartyDirectoryService::captured_entry_current(member))qualified=false;
                                    }
                                    if(!qualified || dispatch->reentered || !native_parties.same_state(*party_before) ||
                                       !owned_party_directory->publish(before,std::move(next_directory)))continue;
                                    if(next_party)native_parties=std::move(*next_party); // No callback between the two ephemeral commits.
                                    wire=std::move(merged);
                                    // Submission only: a transport failure cannot be called
                                    // consent or rolled back as if the pending prefix never existed.
                                    for(auto& [id,bytes]:projections)recipients.at(id)->send_world_records(std::move(bytes));
                                    continue;
                                }
                                const auto prepared_sources=live; // Own every source referenced by the caller A7 before reobservation.
                                const auto prepared=OwnedPartyDirectoryService::prepare(before,*owner,request,live,config.max_sessions);
                                if(!prepared) {
                                    // CUSTOM-0102 caller-specific projection failure
                                    // must not starve unrelated watchers. Reconcile
                                    // ACTUAL current state only; never publish the
                                    // rejected request's attempted listing mutation.
                                    (void)reconcile(nullptr,&session,&wire);
                                    if(dispatch->reentered)return {};
                                    continue;
                                }
                                // Watchers include private query owners and any retained
                                // detail group, not only currently advertised listings.
                                std::map<std::uint64_t,OwnedPartyDirectory::Actor> watcher_candidates;
                                for(const auto& actor:live)watcher_candidates.emplace(actor.session_id,actor);
                                for(const auto& [id,q]:before->queries) {
                                    watcher_candidates.try_emplace(id,q.actor);
                                    if(q.detail)for(const auto& member:q.detail->members)watcher_candidates.try_emplace(member.session_id,member);
                                    if(q.presentation) {
                                        watcher_candidates.try_emplace(q.presentation->target.session_id,q.presentation->target);
                                        for(const auto& member:q.presentation->members)watcher_candidates.try_emplace(member.session_id,member);
                                    }
                                }
                                live.clear();
                                for(const auto& [id,previous]:watcher_candidates) {
                                    const auto peer=previous.session.lock();if(!peer)continue;retained.push_back(peer);
                                    const auto current=observe(peer,&previous);if(current)live.push_back(*current);
                                }
                                const bool prepared_current=std::all_of(prepared_sources.begin(),prepared_sources.end(),[&](const auto& previous) {
                                    return std::any_of(live.begin(),live.end(),[&](const auto& current){return previous.same(current);});
                                });
                                if(!prepared_current || dispatch->reentered || owned_party_directory->snapshot()!=before)continue;
                                const auto party_before=native_parties;
                                auto plan=OwnedPartyDirectoryService::watch(before,prepared->state,live,party_before,config.max_sessions,session.id());
                                if(!plan)continue;
                                if(!prepared->logical.empty())plan->deliveries.push_back({*owner,prepared->logical});
                                (void)publish_watchers(before,*plan,live,party_before,&session,&wire);

                            } catch(const std::exception&) {
                                // Unsupported/missing source rejects this feature's
                                // request without breaking unrelated world/chat runs.
                                if(dispatch->reentered)return {};
                            }
                        }
                        return wire;
                    };
                }
                // CUSTOM-0100 wraps the FINAL TW handler. C1D remains its old
                // transport-only notification when this explicit opt-in is off.
                // C1D supplies an untrusted full display-preference WORD; B1
                // selectors7/8 only update0200 of a previously supplied WORD.
                // The S1B echo/replay policy is custom, not an original ACK or
                // permission/chat-filter/gameplay rule recovered from the UI.
                if(owned_client_options) {
                    if(!game_handlers.world_records || !game_handlers.world_ready)
                        throw std::invalid_argument("Client options requires actual world and ready handlers");
                    game_handlers.owned_client_options=true;
                    struct OptionsDispatch {bool reading=false,reentered=false;};
                    const auto dispatch=std::make_shared<OptionsDispatch>();
                    const auto ready=game_handlers.world_ready;
                    game_handlers.world_ready=[&,ready,dispatch](Session& session) {
                        ready(session);
                        if(dispatch->reading)dispatch->reentered=true;
                        owned_client_options->ready(session); // No private receipt exists yet at this hook.
                    };
                    const auto original=game_handlers.world_records;
                    game_handlers.world_records=[&,original,dispatch](Session& session,
                            std::span<const RecoveredWorldRecords::Record> records)->std::optional<std::vector<std::uint8_t>> {
                        if(dispatch->reading){dispatch->reentered=true;return {};}
                        dispatch->reading=true;dispatch->reentered=false;
                        struct End {OptionsDispatch& value;~End(){value.reading=false;}} end{*dispatch};
                        if(records.empty())return original(session,records);
                        const auto held=session.shared_from_this();
                        std::vector<std::uint8_t> wire;
                        const auto options=[](const auto& record) {
                            return std::holds_alternative<RecoveredWorldRecords::ClientOptionsNotification>(record) ||
                                std::holds_alternative<TaiwanNativeClientOptions::Control>(record);
                        };
                        const auto synchronize=[&](std::optional<std::uint16_t> supplied,
                                std::optional<std::uint8_t> selector,bool replay) {
                            // Obtain this actual callback's private receipt and
                            // its recorded game owner BEFORE reading game fields.
                            const auto initialization=session.normal_world_initialization();
                            if(!initialization || !initialization->entry_written() ||
                               !session.normal_world_initialization_current_on_game(*initialization))return;
                            const auto account=session.account_id,character=session.character_id,battle=session.battle_generation();
                            const auto phase=session.state();
                            const auto current=[&] {
                                return !dispatch->reentered &&
                                    session.normal_world_initialization_current_on_game(*initialization) &&
                                    !session.closing() && session.recovered_world_ready() && account && character &&
                                    session.account_id==account && session.character_id==character &&
                                    session.battle_generation()==battle && session.state()==phase &&
                                    (phase==SessionState::CharacterSelected || phase==SessionState::InWorld);
                            };
                            if(!current())return;
                            const auto before=owned_client_options->snapshot();
                            if(before->entries.size()>config.max_sessions)return;
                            const auto at=before->entries.find(session.id());
                            const auto* previous=at==before->entries.end()?nullptr:&at->second;
                            if(previous && (previous->session.lock()!=held || previous->session_id!=session.id() ||
                               previous->account!=account || previous->character!=character))return; // Never rebind stale ownership.
                            if(!previous && (replay || selector || before->entries.size()>=config.max_sessions))return;
                            if(replay) {
                                // Reuse only this exact owner's known WORD after
                                // a genuine new/current written entry. No initial0.
                                if(!previous || (!previous->pending_replay &&
                                   session.normal_world_initialization_current_on_game(previous->initialization)))return;
                            }
                            if(selector && *selector!=7 && *selector!=8)return;
                            if(!supplied && !previous)return;
                            auto word=supplied?*supplied:previous->word;
                            if(selector)word=*selector==7?static_cast<std::uint16_t>(word|0x0200u):
                                static_cast<std::uint16_t>(word&~0x0200u);
                            std::uint64_t revision=previous?previous->revision:1;
                            if(previous && word!=previous->word) {
                                if(revision==std::numeric_limits<std::uint64_t>::max())return;
                                ++revision;
                            }
                            auto next=std::make_shared<OwnedClientOptions::State>(*before);
                            next->entries.insert_or_assign(session.id(),OwnedClientOptions::Entry{
                                held,session.id(),account,character,word,revision,*initialization,false});
                            const auto logical=TaiwanNativeClientOptions::synchronize(word);
                            const auto framed=RecoveredWorldFrame::encode(logical);
                            auto merged=wire;merged.insert(merged.end(),framed.begin(),framed.end());
                            // All allocation/framing precedes source publication.
                            // These are pure game-owner/receipt/state fences.
                            if(!current() || owned_client_options->snapshot()!=before ||
                               !owned_client_options->publish(before,std::move(next)))return;
                            wire.swap(merged); // Ordinary returned bytes, not Written/ACK/held delivery.
                        };
                        for(std::size_t i=0;i<records.size();) {
                            if(options(records[i])) {
                                try {
                                    if(const auto* supplied=std::get_if<RecoveredWorldRecords::ClientOptionsNotification>(&records[i])) {
                                        const auto word=static_cast<std::uint16_t>(supplied->payload[0]|
                                            (static_cast<std::uint16_t>(supplied->payload[1])<<8));
                                        synchronize(word,{},false);
                                    } else synchronize({},std::get<TaiwanNativeClientOptions::Control>(records[i]).selector,false);
                                } catch(const std::exception&) {
                                    if(dispatch->reentered)return {};
                                }
                                ++i;continue;
                            }
                            const auto begin=i;
                            while(i<records.size() && !options(records[i]))++i;
                            const auto reply=original(session,records.subspan(begin,i-begin));
                            if(!reply || dispatch->reentered)return {};
                            wire.insert(wire.end(),reply->begin(),reply->end()); // Keep existing framed run ordering.
                            try{synchronize({},{},true);}catch(const std::exception&){if(dispatch->reentered)return {};}
                        }
                        return wire;
                    };
                }
                if(whole_bag_moves) {
                    if(!recovered_movement || !recovered_login || !game_handlers.authenticate_async ||
                       !game_handlers.world_entry || !game_handlers.world_ready || !game_handlers.world_records ||
                       game_handlers.movement || game_handlers.common_world_lifecycle_factory)
                        throw std::invalid_argument("Whole bag moves require complete exclusive actual normal-entry TW handlers");
                    // Exact same migrated Database connection; both explicit
                    // custody schemas/material must already exist. No installer.
                    whole_bag_moves->transaction=std::make_shared<SqliteOwnedEquipmentTransaction>(
                        database.owned_inventory_writer(),database.native_equipment_snapshot_writer());
                    whole_bag_moves->movement=recovered_movement.get();
                    whole_bag_moves->binding=SharedTaiwanOwnedBagMoveSource::create_for_normal_entry_with_item_material_and_receipt(
                        whole_bag_moves->transaction,database.accounts(),database.recovered_characters(),*recovered_movement);
                    const auto& binding=*whole_bag_moves->binding;
                    if(!binding.dispatch || !binding.release || !binding.invalidate_active)
                        throw std::invalid_argument("Whole bag moves require a complete actual inventory binding");
                    const std::weak_ptr<WholeBagMoveHost> weak=whole_bag_moves;
                    whole_bag_moves->service=std::make_shared<RecoveredWorldService>(
                        [weak](Session& session,std::span<const RecoveredMovement::Request> requests) {
                            const auto host=weak.lock();
                            if(!host || !host->live || !host->accepting || !host->transaction || !host->movement)
                                return std::vector<std::uint8_t>{};
                            const auto transaction=host->transaction;
                            auto* const movement=host->movement;
                            const auto draft=host->active;
                            if(!draft || draft->invalid || draft->session.lock().get()!=&session || draft->after) {
                                if(draft)draft->invalid=true;
                                if(host->binding)host->binding->invalidate_active();
                                throw std::logic_error("Owned movement lacks its one actual response batch");
                            }
                            auto committed=movement->move_committed_with_owned_material_and_receipt(session,*transaction,requests);
                            // Actual aftertuple and original per-frame ACKs only;
                            // never observe/rebase a bank after this mutation.
                            if(!host->live || !host->accepting || host->transaction!=transaction || host->movement!=movement ||
                               host->active!=draft || draft->invalid || draft->after)
                                throw std::runtime_error("Normal-entry movement committed but host facade became stale");
                            draft->after.emplace(committed.committed());
                            return std::move(committed).take_movement().reply; // Actual prebuilt ACKs, no wrapper repack.
                        },RecoveredWorldService::Battle{},RecoveredWorldService::Supply{},
                        RecoveredWorldService::Quest{},RecoveredWorldService::SelectionItem{},RecoveredWorldService::Teleport{},
                        [weak](Session& session,const RecoveredInventoryMoveRequest::Request& request)
                                ->std::optional<std::vector<std::uint8_t>> {
                            const auto host=weak.lock();
                            if(!host || !host->live || !host->accepting || !host->binding)return {};
                            const auto draft=host->active;
                            if(!draft || draft->invalid || draft->session.lock().get()!=&session || draft->after) {
                                if(draft)draft->invalid=true;
                                host->binding->invalidate_active();
                                throw std::logic_error("Owned bag move lacks its one actual response batch");
                            }
                            const auto transaction=host->transaction;
                            const auto dispatch=host->binding->dispatch;
                            auto reply=dispatch(session,request);
                            if(!reply)return {};
                            if(!host->live || !host->accepting || host->transaction!=transaction ||
                               host->active!=draft || draft->invalid || draft->after)
                                throw std::runtime_error("Whole bag move committed but host facade became stale");
                            if(reply->native_no_reply())throw std::runtime_error("Whole bag move requires its full native material reply");
                            draft->after.emplace(reply->committed());
                            return std::move(*reply).take_wire(); // Original prebuilt wire, no repack.
                        });
                    const auto original=game_handlers.world_records;
                    game_handlers.world_records=[weak,original](Session& session,
                            std::span<const RecoveredWorldRecords::Record> records)->std::optional<std::vector<std::uint8_t>> {
                        const auto host=weak.lock();
                        if(!host || !host->live || !host->accepting)return {};
                        if(host->active) {
                            host->active->invalid=true;
                            if(host->binding)host->binding->invalidate_active();
                            throw std::logic_error("Owned mutation response facade reentered");
                        }
                        // Entire original batch before typed consumers/observers.
                        // Admit movements plus ticks OR one C24 plus ticks through
                        // the existing service. A mixed C24/move batch rejects
                        // before either source can mutate its complete banks.
                        if(std::any_of(records.begin(),records.end(),[](const auto& record){
                            return std::holds_alternative<RecoveredInventoryMoveRequest::Request>(record) ||
                                std::holds_alternative<RecoveredMovement::Request>(record);
                        })) {
                            const auto initialization=session.normal_world_initialization();
                            const auto actual=session.weak_from_this().lock();
                            if(!initialization || !initialization->entry_written() || actual.get()!=&session ||
                               !session.normal_world_initialization_current(*initialization) || !host->transaction)
                                return {};
                            if(!host->mutations.contains(session.id()) && host->mutations.size()>=host->actual_session_capacity)
                                return {};
                            // Allocate the game-owned draft before any mutation.
                            // No borrowed records/span survives this callback.
                            const auto draft=std::make_shared<WholeBagMoveHost::MutationDraft>(actual,*initialization);
                            host->active=draft;
                            struct End {
                                std::shared_ptr<WholeBagMoveHost> host;
                                std::shared_ptr<WholeBagMoveHost::MutationDraft> draft;
                                ~End(){if(host->active==draft)host->active.reset();}
                            } end{host,draft};
                            const auto transaction=host->transaction;
                            const auto local=[&] {
                                return host->live && host->accepting && host->transaction==transaction && host->active==draft &&
                                    !draft->invalid && draft->session.lock().get()==&session && !session.closing() &&
                                    session.normal_world_initialization_current(draft->initialization) && draft->initialization.entry_written();
                            };
                            std::shared_ptr<const WholeBagMoveHost::MutationResponse> previous;
                            if(const auto at=host->mutations.find(session.id());at!=host->mutations.end())previous=at->second;
                            if(previous) {
                                // Pending is allowed: this passive token neither
                                // imposes a wait/Tick barrier nor grants authority.
                                if(previous->session.lock().get()!=&session ||
                                   previous->write.status()==Session::WorldResponseWriteStatus::Failed ||
                                   !session.world_response_write_current(previous->write) ||
                                   !session.normal_world_initialization_current(previous->initialization) ||
                                   !previous->initialization.entry_written() || !transaction->committed_current(previous->after) || !local())
                                    return {};
                                const auto at=host->mutations.find(session.id());
                                if(at==host->mutations.end() || at->second!=previous ||
                                   previous->write.status()==Session::WorldResponseWriteStatus::Failed)
                                    throw std::runtime_error("Owned mutation response source changed during preparation");
                            }
                            if(!local())return {};
                            const auto service=host->service;
                            auto response=service?service->handle(session,records):std::nullopt;
                            if(!local())throw std::runtime_error("Owned mutation response facade retired during callback");
                            if(!draft->after)return response; // Admission rejection never invents a receipt.
                            if(!response || response->empty() || !local() || !transaction->committed_current(*draft->after) || !local())
                                throw std::runtime_error("Owned mutation committed without current original response");
                            // This is the ORIGINAL complete callback return,
                            // including each native ACK5B frame unchanged.
                            // Allocation/validation failure after COMMIT throws;
                            // no retry/rollback or native adoption is implied.
                            const auto observation=session.observe_world_response(*response);
                            const auto candidate=std::make_shared<const WholeBagMoveHost::MutationResponse>(
                                WholeBagMoveHost::MutationResponse{actual,*draft->after,draft->initialization,observation});
                            if(!local() || observation.status()==Session::WorldResponseWriteStatus::Failed)
                                throw std::runtime_error("Owned mutation response capture became stale");
                            host->mutations.insert_or_assign(session.id(),candidate);
                            return response; // Session consumes this exact raw vector through its old FIFO.
                        }
                        // These always-present legacy services use independent
                        // scalar/typed populations. Whole-batch rejection occurs
                        // before any of their callbacks can mutate or publish.
                        if(std::any_of(records.begin(),records.end(),[](const auto& record){
                            return std::holds_alternative<RecoveredInventoryItemRequest::Request>(record) ||
                                std::holds_alternative<RecoveredTargetItemRequest::Request>(record) ||
                                std::holds_alternative<RecoveredSelectionItemRequest::Request>(record) ||
                                std::holds_alternative<RecoveredInventoryDiscard::Request>(record) ||
                                std::holds_alternative<RecoveredTrade::Request>(record) ||
                                std::holds_alternative<RecoveredBank::Request>(record) ||
                                std::holds_alternative<RecoveredBankItems::Request>(record) ||
                                std::holds_alternative<RecoveredPet2Revert::Request>(record) ||
                                std::holds_alternative<RecoveredBattleCommand::BasicAttackRequest>(record) ||
                                std::holds_alternative<RecoveredBattleCommand::ControlRequest>(record) ||
                                std::holds_alternative<RecoveredBattleCommand::Action2Request>(record) ||
                                std::holds_alternative<RecoveredSkillCommand::Record>(record) ||
                                std::holds_alternative<TaiwanNativeSkillCommand::WireRecord>(record);
                        }))return {};
                        return original(session,records); // Other normal chat/ready Tick behavior.
                    };
                    const auto previous=on_disconnect;
                    on_disconnect=[weak,previous](std::shared_ptr<Session> session) {
                        if(!session)return;
                        const auto host=weak.lock();
                        if(!host || !host->live)return;
                        // Revoke passive per-incarnation custody before any
                        // observer may throw or borrowed movement is removed.
                        if(host->active && host->active->session.lock().get()==session.get())host->active->invalid=true;
                        host->mutations.erase(session->id());
                        std::exception_ptr failure;
                        try {if(host->binding)host->binding->release(*session);}catch(...) {failure=std::current_exception();}
                        try {if(previous)previous(std::move(session));}catch(...) {if(!failure)failure=std::current_exception();}
                        if(failure)std::rethrow_exception(failure);
                    };
                    spdlog::warn("OWNED_WHOLE_BAG_MOVES_SOURCE CUSTOM-0094 full25 only existing_owner no_grants stale_pose_rejected");
                }
                character_server=std::make_unique<TcpServer>(network.context(),game.get_executor(),
                    config.host,config.character_port,config.max_sessions,config.packet_dump,
                    on_packet,on_disconnect,ProtocolMode::God2CharacterConnection,recovered_login,std::move(game_handlers));
                const auto routes=RecoveredServerRoutes::wire(asio::ip::make_address_v4(config.host).to_bytes(),character_server->port());
                character_routes.assign(routes.begin(),routes.end());
            }
            if(config.recovered_account_auth) character_handlers.authenticate_async=async_login;
            TcpServer server(network.context(),game.get_executor(),config.host,config.port,config.max_sessions,config.packet_dump,
                on_packet,on_disconnect,config.protocol_mode,std::move(recovered_login),std::move(character_handlers),std::move(character_routes));
            // Same existing authoritative repositories and serial game owner.
            // No CN DB/schema, protocol guessing or default native success data.
            std::unique_ptr<cn::SharedCredentialServer> cn_server;
            if(cn_plan) {
                for(const auto& endpoint:cn_plan->endpoints) {
                    // Reserve distinct ports also for wildcard/address aliases.
                    // Catalog ports must be supplied explicitly, never relocated.
                    if(endpoint.port==server.port() ||
                       (character_server && endpoint.port==character_server->port()))
                        throw std::invalid_argument("CN endpoint conflicts with an existing TW listener");
                }
                cn_server=std::make_unique<cn::SharedCredentialServer>(network.context(),game.get_executor(),
                    database.accounts(),database.account_native_snapshots(),database.native_character_summaries(),
                    database.recovered_characters(),
                    database.native_map_catalog(),*cn_plan,common_world,database.native_skill_catalog());
            }
            std::unique_ptr<WebClientGateway> web_gateway;
            if(web_plan) {
                std::vector<WebNativeRoute> routes;
                // Wildcard listeners are reached locally. No DNS/destination
                // supplied by the browser, and dynamic TW G uses its bound port.
                auto reachable=[](asio::ip::tcp::endpoint endpoint) {
                    if(endpoint.address().is_unspecified())endpoint.address(endpoint.address().is_v4()?
                        asio::ip::address(asio::ip::address_v4::loopback()):asio::ip::address(asio::ip::address_v6::loopback()));
                    return endpoint;
                };
                const auto cn_bound=cn_server?cn_server->bound_endpoints():std::vector<cn::SharedCredentialServer::BoundEndpoint>{};
                for(const auto& request:web_plan->routes) {
                    using Role=WebServerPlan::Role;
                    if(request.role==Role::TwAccount||request.role==Role::TwWorld) {
                        if(request.target||!config.recovered_account_auth||!is_credential_mode(config.protocol_mode)||
                           config.protocol_mode==ProtocolMode::God2CharacterConnection)
                            throw std::invalid_argument("WEB TW requires hosted native authentication and role");
                        if(request.role==Role::TwWorld&&!character_server)
                            throw std::invalid_argument("WEB TW world listener missing");
                        routes.push_back({request.role==Role::TwAccount?"/tw/native":"/tw/native-game",
                            reachable({asio::ip::make_address(config.host),request.role==Role::TwAccount?server.port():character_server->port()})});
                    } else if(request.role==Role::CnAccount||request.role==Role::CnWorld) {
                        const bool world_role=request.role==Role::CnWorld;
                        if(!cn_server||world_role!=request.target.has_value())
                            throw std::invalid_argument("WEB CN requires hosted native role/target");
                        auto found=std::find_if(cn_bound.begin(),cn_bound.end(),[&](const auto& bound){
                            if(bound.role!=(world_role?cn::SharedServerPlan::Role::World:cn::SharedServerPlan::Role::Account))return false;
                            return !world_role||(bound.target&&bound.target->group==request.target->group&&bound.target->server==request.target->server);
                        });
                        if(found==cn_bound.end())throw std::invalid_argument("WEB CN registry target missing");
                        routes.push_back({world_role?"/cn/native-game":"/cn/native",reachable(found->socket)});
                    } else throw std::invalid_argument("WEB native role invalid");
                }
                web_gateway=std::make_unique<WebClientGateway>(network.context(),web_plan->policy,std::move(routes));
            }
            auto known=script_times(config.script_root);
            unsigned ticks=0;
            auto trade_checked=std::chrono::steady_clock::now();
            auto scheduler=std::make_shared<Scheduler>(game.get_executor(),std::chrono::milliseconds(50),[&] {
                world.update(0.05f);
                const auto clock_now=std::chrono::steady_clock::now();
                if(!fixture_mode && clock_now-trade_checked>=std::chrono::seconds(1)) {
                    trade_checked=clock_now;
                    try{deliver_trades(owned_instance_trades?owned_instance_trades->refresh(clock_now):native_trades.refresh(clock_now));}
                    catch(const std::exception& error){spdlog::warn("NATIVE_TRADE_REFRESH_FAILED reason={}",error.what());}
                }
                for(auto it=world_clock_sessions.begin();it!=world_clock_sessions.end();) {
                    const auto peer=it->second.session.lock();
                    if(!peer) {it=world_clock_sessions.erase(it);continue;}
                    // Native bootstrap deliberately retains CharacterSelected.
                    // Completed tail plus owned restoration authorizes the clock;
                    // do not broaden world/battle state semantics for this packet.
                    if((peer->state()==SessionState::InWorld || peer->state()==SessionState::CharacterSelected) &&
                       peer->recovered_world_ready() && owned_player_and_companions_projected.contains(peer->id()) &&
                       !diagnostic_town_scene_pending.contains(peer->id()) &&
                       clock_now-it->second.last_sync>=std::chrono::seconds(config.world_clock_sync_seconds)) {
                        send_world_clock(*peer);it->second.last_sync=clock_now;
                    }
                    ++it;
                }
                if(config.hot_reload && ++ticks%40==0) {
                    auto changed=script_times(config.script_root);
                    if(changed!=known) {
                        known=std::move(changed);
                        if(lua.reload_all()) spdlog::info("Lua scripts reloaded");
                        else spdlog::warn("Lua reload rejected; previous VM retained");
                    }
                }
            });
            asio::signal_set signals(game,SIGINT,SIGTERM);
            asio::steady_timer deadline(game);
            bool stopping=false;
            auto stop=[&] {
                if(stopping) return;
                guild_delivery_lifetime->store(false);
                stop_blacklist_outputs();
                stopping=true;
                if(whole_bag_moves)whole_bag_moves->stop_dispatch();
                spdlog::info("Stopping server and draining sessions");
                scheduler->stop(); signals.cancel(); deadline.cancel();
                if(web_gateway)web_gateway->stop();
                server.stop();
                if(cn_server)cn_server->stop();
                if(character_server) character_server->stop();
                network.stop();
            };
            signals.async_wait([&](const asio::error_code& ec,int) { if(!ec) stop(); });
            if(run_for_seconds) {
                deadline.expires_after(std::chrono::seconds(run_for_seconds));
                deadline.async_wait([&](const asio::error_code& ec) { if(!ec) stop(); });
            }
            if(character_server) {
                character_server->start();
                spdlog::info("Character connection listening on {}:{}; independent authentication; 1F candidate unverified",config.host,character_server->port());
            }
            if(cn_server)cn_server->start();
            server.start();
            if(web_gateway)web_gateway->start();
            scheduler->start(); lua.call_event("server_start");
            spdlog::info("{} listening on {}:{} [protocol={}; mock_login={}]",config.name,config.host,server.port(),
                config.protocol_mode==ProtocolMode::Fixture?"PLACEHOLDER":config.protocol_mode==ProtocolMode::God2LegacyCharacterListCandidate?"GOD2_LEGACY_CHARACTER_LIST_CANDIDATE_UNVERIFIED":config.protocol_mode==ProtocolMode::God2PostServerSelect?"GOD2_POST_SERVER_SELECT_LAB":config.protocol_mode==ProtocolMode::God2ServerList?"GOD2_SERVER_LIST_LAB":config.protocol_mode==ProtocolMode::God2LoginTerminal?"GOD2_LOGIN_TERMINAL_LAB":config.protocol_mode==ProtocolMode::God2C2S0002?"GOD2_C2S0002_LAB":config.protocol_mode==ProtocolMode::God2PostSeed?"GOD2_POST_SEED_LAB":"GOD2_RECOVERED_SEED_ONLY",config.mock_login);
            ready.set_value(); announced=true;
            game.run();
            lua.call_event("server_stop");
        } catch(...) {
            failure=std::current_exception();
            if(!announced) ready.set_exception(failure);
            network.context().stop();
        }
    });
    try { initialized.get(); } catch(...) {
        network.stop(); network.join(); game_work.reset(); game_thread.join(); throw;
    }
    network.join();
    game_work.reset();
    game_thread.join();
    if(failure) std::rethrow_exception(failure);
    spdlog::info("Server stopped cleanly");
    return 0;
}
int run_server(const Config& config,unsigned run_for_seconds) {
    return run_server_impl(config,nullptr,nullptr,run_for_seconds);
}
int run_server(const Config& config,const cn::SharedServerPlan& plan,unsigned run_for_seconds) {
    return run_server_impl(config,&plan,nullptr,run_for_seconds);
}
int run_server(const Config& config,const WebServerPlan& plan,unsigned run_for_seconds) {
    return run_server_impl(config,nullptr,&plan,run_for_seconds);
}
int run_server(const Config& config,const cn::SharedServerPlan& cn_plan,const WebServerPlan& web_plan,unsigned run_for_seconds) {
    return run_server_impl(config,&cn_plan,&web_plan,run_for_seconds);
}
int run_server(const Config& config,const SharedWorldHostPlan& world_plan,unsigned run_for_seconds) {
    return run_server_impl(config,nullptr,nullptr,run_for_seconds,&world_plan);
}
int run_server(const Config& config,const cn::SharedServerPlan& cn_plan,const SharedWorldHostPlan& world_plan,unsigned run_for_seconds) {
    return run_server_impl(config,&cn_plan,nullptr,run_for_seconds,&world_plan);
}
int run_server(const Config& config,const WebServerPlan& web_plan,const SharedWorldHostPlan& world_plan,unsigned run_for_seconds) {
    return run_server_impl(config,nullptr,&web_plan,run_for_seconds,&world_plan);
}
int run_server(const Config& config,const cn::SharedServerPlan& cn_plan,const WebServerPlan& web_plan,
               const SharedWorldHostPlan& world_plan,unsigned run_for_seconds) {
    return run_server_impl(config,&cn_plan,&web_plan,run_for_seconds,&world_plan);
}
}
