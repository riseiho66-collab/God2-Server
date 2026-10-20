#include "net/Session.h"
#include "net/NativeTaiwanChannelBinding.h"
#include "net/Buffer.h"
#include "protocol/God2ProtocolSpec.h"
#include "protocol/Opcode.h"
#include "protocol/RecoveredSeedExchange.h"
#include "protocol/RecoveredPostSeed.h"
#include "protocol/RecoveredC2S0002.h"
#include "protocol/RecoveredLoginTerminal.h"
#include "protocol/RecoveredLoginFailure.h"
#include "protocol/RecoveredServerList.h"
#include "protocol/RecoveredPostServerSelect.h"
#include "protocol/LegacyCharacterListCandidate.h"
#include "protocol/RecoveredCharacterCreate.h"
#include "protocol/RecoveredCharacterCreateResult.h"
#include "protocol/RecoveredPostCreateSelect.h"
#include "protocol/RecoveredCharacterBootstrap.h"
#include "protocol/RecoveredWorldReady.h"
#include "protocol/RecoveredWorldEntryView.h"
#include "game/LegacyWorldReply.h"
#include "game/TaiwanWorldEntryIdentity.h"
#include "game/TaiwanWorldIdentityWriteFence.h"
#include "game/TaiwanBattleSelfViewWriteFence.h"
#include "game/TaiwanActorStatusWriteFence.h"
#include "protocol/RecoveredTaiwanServerRecords.h"
#include "protocol/RecoveredBattleBootstrap.h"
#include "protocol/RecoveredBattlePlayerAppearance.h"
#include "protocol/RecoveredBattlePlayerGrant.h"
#include "protocol/RecoveredBattleAttackPresentation.h"
#include "protocol/RecoveredBattleVitals.h"
#include "protocol/RecoveredBattleVitalsBatch.h"
#include "protocol/RecoveredTaiwanPkTerminalNotification.h"
#include "protocol/RecoveredRemoteActor.h"
#include "protocol/RecoveredTaiwanActorOverride.h"
#include <asio/bind_cancellation_slot.hpp>
#include <asio/cancellation_signal.hpp>
#include <spdlog/spdlog.h>
#include <algorithm>
#include <array>
#include <chrono>
#include <deque>
#include <mutex>
#include <span>
#include <utility>
#include <vector>
#include <cstdlib>
#include <filesystem>
#include <fstream>
#include <limits>
#include <thread>
#include <type_traits>
#include <nlohmann/json.hpp>
#ifdef _WIN32
#include <windows.h>
#endif

namespace god2 {
namespace {
// Explicit C++20 member order: body cleanup finishes BEFORE writer release.
// Lambda capture member order alone cannot provide this lifetime guarantee.
template<class Body>
struct ActorStatusWriterWork {
    std::array<std::optional<TaiwanActorStatusWriteFence::Writer>,2> writers;
    Body body; // LAST: destroys first, including existing cleanup/post owners.
    template<class... Args>
    decltype(auto) operator()(Args&&... args) {
        return body(std::forward<Args>(args)...);
    }
};
template<class Body>
auto retain_actor_status_writer(std::optional<TaiwanActorStatusWriteFence::Writer> writer,Body body) {
    return ActorStatusWriterWork<Body>{{std::move(writer),{}},std::move(body)};
}
constexpr std::size_t max_buffer = 1024 * 1024;
constexpr std::size_t max_writes = 256;
constexpr std::size_t max_batch = 4096;
constexpr auto idle_timeout = std::chrono::seconds(120);
constexpr auto close_timeout = std::chrono::seconds(5);
// Conservative transport deadline, not a recovered cast/turn duration.
constexpr auto skill_sequence_timeout = std::chrono::seconds(5);

// Installed only by the real posted world-records game job below. A foreign
// public caller cannot nominate itself as game owner or read game-owned IDs.
thread_local const Session* observed_world_callback=nullptr;
thread_local Session* qualified_world_push_profile=nullptr; // Actual GAME-only framer, never a NET callback.
// Separate actual callback occurrence for opt-in movement sender custody.
// No old normal/bootstrap capture API is broadened by this TLS scope.
thread_local const Session* observed_movement_callback=nullptr;
thread_local std::atomic<bool>* observed_movement_poison=nullptr;
thread_local std::span<const RecoveredWorldRecords::Record> observed_world_records;
thread_local bool* observed_response_poison=nullptr;
thread_local std::atomic<Session::WorldResponseWriteStatus>* observed_response_status=nullptr;
thread_local std::atomic<Session::WorldCallbackOutputStatus>* observed_callback_output_status=nullptr;
thread_local std::atomic<Session::NormalWorldResponseStatus>* observed_normal_response_status=nullptr;
thread_local std::atomic<Session::NormalWorldCallbackAdmissionStatus>* observed_callback_admission_status=nullptr;
void poison_world_response() noexcept {
    if(observed_callback_output_status){
        auto pending=Session::WorldCallbackOutputStatus::Pending;
        observed_callback_output_status->compare_exchange_strong(pending,Session::WorldCallbackOutputStatus::Failed);
    }
    if(observed_response_poison)*observed_response_poison=true;
    if(observed_response_status) {
        auto pending=Session::WorldResponseWriteStatus::Pending;
        observed_response_status->compare_exchange_strong(pending,Session::WorldResponseWriteStatus::Failed);
    }
    if(observed_callback_admission_status) {
        auto pending=Session::NormalWorldCallbackAdmissionStatus::Pending;
        observed_callback_admission_status->compare_exchange_strong(pending,Session::NormalWorldCallbackAdmissionStatus::Failed);
    }
    if(observed_normal_response_status) {
        auto pending=Session::NormalWorldResponseStatus::Pending;
        observed_normal_response_status->compare_exchange_strong(pending,Session::NormalWorldResponseStatus::Failed);
    }
}
struct WorldRecordsObservationScope {
    bool response_poisoned=false;
    explicit WorldRecordsObservationScope(const Session& session,std::span<const RecoveredWorldRecords::Record> records) {
        if(observed_world_callback) {
            poison_world_response();
            throw std::logic_error("World observation callback reentry rejected");
        }
        observed_world_callback=&session;observed_world_records=records;observed_response_poison=&response_poisoned;
        observed_callback_output_status=nullptr;observed_response_status=nullptr;observed_normal_response_status=nullptr;observed_callback_admission_status=nullptr;
    }
    ~WorldRecordsObservationScope(){
        observed_callback_output_status=nullptr;observed_response_status=nullptr;observed_normal_response_status=nullptr;observed_callback_admission_status=nullptr;observed_response_poison=nullptr;observed_world_records={};observed_world_callback=nullptr;
    }
    WorldRecordsObservationScope(const WorldRecordsObservationScope&)=delete;
    WorldRecordsObservationScope& operator=(const WorldRecordsObservationScope&)=delete;
};

std::shared_ptr<spdlog::logger> logger(const char* channel) {
    auto result = spdlog::get(channel);
    return result ? result : spdlog::default_logger();
}
std::string dump(std::span<const std::uint8_t> bytes) {
    constexpr char digits[] = "0123456789ABCDEF";
    std::string result;
    result.reserve(bytes.size() * 3);
    for (auto b : bytes) {
        result.push_back(digits[b >> 4]);
        result.push_back(digits[b & 15]);
        result.push_back(' ');
    }
    return result;
}
struct Budget {
    std::mutex mutex;
    std::size_t bytes = 0;
    std::size_t count = 0;
};
struct Reservation {
    std::shared_ptr<Budget> budget;
    std::size_t bytes;
    const std::size_t count;
    bool charged;
    Reservation(std::shared_ptr<Budget> budget_, std::size_t bytes_,std::size_t count_=1,bool charged_=true)
        : budget(std::move(budget_)), bytes(bytes_),count(count_),charged(charged_) {}
    ~Reservation() {
        if(!charged)return;
        std::lock_guard lock(budget->mutex);
        budget->bytes -= bytes;
        budget->count -= count;
    }
};
} // namespace

struct Session::WorldRecordsWrite::Data {
    // Minted only by the actual TLS-gated world sender, never a first caller.
    const std::thread::id game_thread=std::this_thread::get_id();
    const std::weak_ptr<Session> session;
    const std::uint64_t account,character,battle;
    const SessionState phase;
    const std::vector<std::uint8_t> logical;
    std::atomic<WorldRecordsWriteStatus> status{WorldRecordsWriteStatus::Pending};
    Data(std::weak_ptr<Session> owner,std::uint64_t a,std::uint64_t c,std::uint64_t b,
         SessionState p,std::vector<std::uint8_t> bytes)
        :session(std::move(owner)),account(a),character(c),battle(b),phase(p),logical(std::move(bytes)) {}
};
Session::WorldRecordsWriteStatus Session::WorldRecordsWrite::status() const noexcept {return data_->status.load();}
const std::vector<std::uint8_t>& Session::WorldRecordsWrite::logical() const noexcept {return data_->logical;}

struct Session::WorldResponseWrite::Data {
    const std::thread::id game_thread=std::this_thread::get_id();
    const std::weak_ptr<Session> session;
    const std::uint64_t account,character,battle,self_view_intent;
    const SessionState phase;
    const std::vector<std::uint8_t> wire;
    std::atomic<WorldResponseWriteStatus> status{WorldResponseWriteStatus::Pending};
    Data(std::weak_ptr<Session> owner,std::uint64_t a,std::uint64_t c,std::uint64_t b,
         SessionState p,std::span<const std::uint8_t> raw,std::uint64_t intent)
        :session(std::move(owner)),account(a),character(c),battle(b),self_view_intent(intent),
         phase(p),wire(raw.begin(),raw.end()) {}
};
Session::WorldResponseWriteStatus Session::WorldResponseWrite::status() const noexcept {return data_->status.load();}
const std::vector<std::uint8_t>& Session::WorldResponseWrite::wire() const noexcept {return data_->wire;}

struct Session::BattleSelfView::Data {
    const std::weak_ptr<Session> session;
    const std::uint64_t session_id,account,character,battle,epoch,intent;
    const std::uint8_t slot;
    const std::thread::id game_thread;
    const std::shared_ptr<const void> source; // Exact pure original-response occurrence.
    const std::shared_ptr<std::vector<std::uint8_t>> frame;
    TaiwanBattleSelfViewWriteFence::Occurrence completion;
    Data(std::weak_ptr<Session> owner,std::uint64_t id,std::uint64_t a,std::uint64_t c,
         std::uint64_t b,std::uint64_t generation,std::uint64_t writer_intent,std::uint8_t primary,std::thread::id game,
         std::shared_ptr<const void> original,std::shared_ptr<std::vector<std::uint8_t>> bytes)
        :session(std::move(owner)),session_id(id),account(a),character(c),battle(b),epoch(generation),intent(writer_intent),
         slot(primary),game_thread(game),source(std::move(original)),frame(std::move(bytes)){}
};
std::uint8_t Session::BattleSelfView::primary_slot() const noexcept {return data_->slot;}

struct Session::MovementStepWrite::Data {
    const std::weak_ptr<Session> session;
    const std::shared_ptr<const void> occurrence,common;
    const SharedWorldPresence::Lease lease;
    const RecoveredPosition before,expected_after;
    const RecoveredMovement::Request request;
    const std::uint64_t battle,scene_revision;
    const std::size_t record_index;
    const SessionState phase;
    const std::uint8_t direction,native_cell;
    const std::array<std::uint8_t,2> logical;
    const std::array<std::uint8_t,5> frame;
    bool committed=false; // Actual serial game callback only, frozen before IO.
    std::optional<std::size_t> offset;
    Data(std::weak_ptr<Session> owner,std::shared_ptr<const void> scope,std::shared_ptr<const void> identity,
         SharedWorldPresence::Lease actual,RecoveredPosition old,RecoveredPosition next,
         RecoveredMovement::Request input,std::size_t index,std::uint64_t generation,std::uint64_t scene,
         SessionState state,std::uint8_t facing,std::uint8_t cell,
         std::array<std::uint8_t,2> ack,std::array<std::uint8_t,5> bytes)
        :session(std::move(owner)),occurrence(std::move(scope)),common(std::move(identity)),lease(actual),
         before(old),expected_after(next),request(input),battle(generation),scene_revision(scene),record_index(index),phase(state),
         direction(facing),native_cell(cell),logical(ack),frame(bytes) {}
};
// A genuine normal owner commits one WHOLE batch, with one saved/native
// revision increment. This is deliberately separate from Core per-step CAS.
struct Session::NormalMovementBatchWrite::Data {
    const std::weak_ptr<Session> session;
    const std::shared_ptr<const void> occurrence;
    const NormalWorldInitialization initialization;
    const SqliteOwnedEquipmentTransaction::Before before;
    const NativeEquipmentSnapshot expected_equipment;
    const std::vector<RecoveredMovement::Request> requests;
    const std::vector<std::size_t> record_indices;
    const std::vector<Destination> displaced_path;
    const std::uint8_t old_slot,new_slot;
    const std::uint64_t battle;
    const SessionState phase;
    const std::vector<std::uint8_t> wire;
    bool committed=false; // Game only; frozen before the original sender cut.
    std::optional<std::size_t> offset;
    Data(std::weak_ptr<Session> owner,std::shared_ptr<const void> scope,NormalWorldInitialization init,
        SqliteOwnedEquipmentTransaction::Before old,NativeEquipmentSnapshot expected,
        std::vector<RecoveredMovement::Request> input,std::vector<std::size_t> indices,
        std::vector<Destination> path,std::uint8_t previous,std::uint8_t next,
        std::uint64_t generation,SessionState state,std::vector<std::uint8_t> bytes)
        :session(std::move(owner)),occurrence(std::move(scope)),initialization(std::move(init)),
         before(std::move(old)),expected_equipment(std::move(expected)),requests(std::move(input)),
         record_indices(std::move(indices)),displaced_path(std::move(path)),old_slot(previous),new_slot(next),
         battle(generation),phase(state),wire(std::move(bytes)) {}
};
struct Session::MovementResponseWrite::Data {
    const std::thread::id game_thread=std::this_thread::get_id();
    const std::weak_ptr<Session> session;
    const std::shared_ptr<const void> occurrence,common,world;
    const std::optional<SharedWorldPresence::Lease> lease;
    const std::optional<NormalWorldInitialization> initialization;
    const std::vector<std::shared_ptr<const NormalMovementBatchWrite::Data>> normal_batches;
    const std::uint64_t battle;
    const SessionState phase;
    const std::vector<std::shared_ptr<const MovementStepWrite::Data>> steps;
    const std::vector<std::uint8_t> wire;
    std::atomic<MovementResponseWriteStatus> status{MovementResponseWriteStatus::Pending};
    Data(std::weak_ptr<Session> owner,std::shared_ptr<const void> scope,std::shared_ptr<const void> identity,
         std::shared_ptr<const void> delivery,SharedWorldPresence::Lease actual,std::uint64_t generation,
         SessionState state,std::vector<std::shared_ptr<const MovementStepWrite::Data>> components,
         std::span<const std::uint8_t> bytes)
        :session(std::move(owner)),occurrence(std::move(scope)),common(std::move(identity)),world(std::move(delivery)),
         lease(actual),battle(generation),phase(state),steps(std::move(components)),wire(bytes.begin(),bytes.end()) {}
    Data(std::weak_ptr<Session> owner,std::shared_ptr<const void> scope,NormalWorldInitialization init,
         std::shared_ptr<const void> delivery,std::uint64_t generation,SessionState state,
         std::vector<std::shared_ptr<const NormalMovementBatchWrite::Data>> batches,
         std::span<const std::uint8_t> bytes)
        :session(std::move(owner)),occurrence(std::move(scope)),world(std::move(delivery)),
         initialization(std::move(init)),normal_batches(std::move(batches)),battle(generation),phase(state),wire(bytes.begin(),bytes.end()) {}
};
Session::MovementResponseWriteStatus Session::MovementResponseWrite::status() const noexcept {return data_->status.load();}
const std::vector<std::uint8_t>& Session::MovementResponseWrite::wire() const noexcept {return data_->wire;}

struct Session::NormalWorldInitialization::Entry {
    // The actual select game job constructs Entry; tail Data may be on strand.
    const std::thread::id game_thread=std::this_thread::get_id();
    const std::weak_ptr<Session> session;
    const std::uint64_t account,character,battle;
    const RecoveredWorldEntry::Frame frame;
    const std::vector<std::uint8_t> logical;
    const bool qualified_scene_identity; // Set only by the actual validated prepared_actor hook.
    TaiwanWorldIdentityWriteFence world_identity_sender; // Separate original-Write custody only.
    std::atomic<bool> written{false},retired{false};
    Entry(std::weak_ptr<Session> owner,std::uint64_t a,std::uint64_t c,std::uint64_t b,
          RecoveredWorldEntry::Frame wire,std::vector<std::uint8_t> bytes,bool qualified=false)
        :session(std::move(owner)),account(a),character(c),battle(b),frame(std::move(wire)),logical(std::move(bytes)),
         qualified_scene_identity(qualified) {}
};
struct Session::NativeTaiwanReceiverSelector::Data {
    const std::shared_ptr<NormalWorldInitialization::Entry> entry;
    const std::uint64_t revision; // Local accepted-occurrence identity, not native nonce.
    const std::array<std::uint8_t,4> context;
    Data(std::shared_ptr<NormalWorldInitialization::Entry> source,std::uint64_t epoch,
        std::array<std::uint8_t,4> received):entry(std::move(source)),revision(epoch),context(received){}
};
std::uint64_t Session::NativeTaiwanReceiverSelector::source_revision()const noexcept {return data_->revision;}
bool Session::NativeTaiwanReceiverSelector::reported_simplified()const noexcept {return data_->context[2]!=0;}
std::uint16_t Session::NativeTaiwanReceiverSelector::wire_codepage()const noexcept {
    return reported_simplified()?936:950; // Same-page native6F branch only.
}
const std::array<std::uint8_t,4>& Session::NativeTaiwanReceiverSelector::context_payload()const noexcept {return data_->context;}
struct Session::NormalWorldInitialization::Data {
    const std::shared_ptr<Entry> entry;
    const std::vector<std::uint8_t> tail;
    const std::uint8_t config;
    // CUSTOM-0132 physical Entry::battle/Written stay the actual original IO.
    const std::uint64_t effective_battle;
    const std::weak_ptr<const Data> previous;
    const std::shared_ptr<const NativeTaiwanReceiverSelector::Data> receiver_selector;
    Data(std::shared_ptr<Entry> source,std::vector<std::uint8_t> bytes,std::uint8_t flag,
        std::shared_ptr<const NativeTaiwanReceiverSelector::Data> selector)
        :entry(std::move(source)),tail(std::move(bytes)),config(flag),effective_battle(entry->battle),
         receiver_selector(std::move(selector)) {}
    Data(std::shared_ptr<const Data> prior,std::uint64_t future,
        std::shared_ptr<const NativeTaiwanReceiverSelector::Data> latest)
        :entry(prior->entry),tail(prior->tail),config(prior->config),effective_battle(future),previous(std::move(prior)),
         receiver_selector(std::move(latest)) {}
};
const RecoveredWorldEntry::Frame& Session::NormalWorldInitialization::entry_frame() const noexcept {return data_->entry->frame;}
const std::vector<std::uint8_t>& Session::NormalWorldInitialization::entry_logical() const noexcept {return data_->entry->logical;}
const std::vector<std::uint8_t>& Session::NormalWorldInitialization::accepted_tail() const noexcept {return data_->tail;}
std::uint8_t Session::NormalWorldInitialization::config_flag() const noexcept {return data_->config;}
bool Session::NormalWorldInitialization::qualified_scene_identity() const noexcept {return data_->entry->qualified_scene_identity;}
bool Session::NormalWorldInitialization::entry_written() const noexcept {
    return data_->entry->written.load() && !data_->entry->retired.load();
}
bool Session::NormalWorldInitialization::original_entry_battle_phase() const noexcept {
    return data_&&data_->entry&&data_->effective_battle==data_->entry->battle;
}
bool Session::NormalWorldInitialization::world_identity_sender_current() const noexcept {
    return entry_written() && data_->entry->world_identity_sender.eligible();
}

// Composite callback metadata is distinct from both legacy write receipts.
struct Session::WorldCallbackOutput::Data {
    const std::thread::id game_thread=std::this_thread::get_id();
    const std::weak_ptr<Session> session;
    const std::uint64_t session_id,account,character,battle;
    const SessionState phase;
    const std::shared_ptr<const NormalWorldInitialization::Data> initialization;
    const std::vector<SelectionKey> keys;
    std::vector<Component> components; // GAME only until release-store seal.
    std::vector<std::uint8_t> final_wire; // GAME only until seal.
    struct ReplyRange {WorldCallbackSelectionEmission emission;std::size_t offset;};
    struct ReplyFragment {
        const std::size_t base;
        const std::vector<std::uint8_t> wire;
        const std::vector<ReplyRange> ranges;
        ReplyFragment(std::size_t offset,std::vector<std::uint8_t> bytes,std::vector<ReplyRange> tags)
            :base(offset),wire(std::move(bytes)),ranges(std::move(tags)){}
    };
    std::vector<WorldCallbackSelectionEmission> emissions; // GAME until seal.
    std::vector<bool> issued; // Original C67 ordinal, allocated before SQL.
    std::vector<std::shared_ptr<const ReplyFragment>> final_fragments;
    std::size_t claimed=0; // Only the actual synchronous game callback.
    std::atomic<WorldCallbackOutputStatus> status{WorldCallbackOutputStatus::Pending};
    std::atomic<bool> sealed{false},accepted{false},armed{false},released{false};
    Data(std::weak_ptr<Session> owner,std::uint64_t id,std::uint64_t a,std::uint64_t c,
         std::uint64_t generation,SessionState state,std::shared_ptr<const NormalWorldInitialization::Data> init,
         std::vector<SelectionKey> input)
        :session(std::move(owner)),session_id(id),account(a),character(c),battle(generation),phase(state),
         initialization(std::move(init)),keys(std::move(input)),issued(keys.size(),false){emissions.reserve(keys.size());}
    void fail() noexcept;
    void complete() noexcept;
};
struct Session::WorldCallbackSelectionEmission::Data {
    enum class Phase {Created,Deferred,FinalReserved,Bound};
    const std::weak_ptr<WorldCallbackOutput::Data> cohort;
    const std::size_t input_ordinal,minimum_component;
    const std::vector<std::uint8_t> wire,logical;
    std::atomic<Phase> phase{Phase::Created};
    WorldCallbackEmissionLocation location{}; // GAME writes before Bound/whole seal.
    Data(std::shared_ptr<WorldCallbackOutput::Data> source,std::size_t input,std::size_t first,
         std::span<const std::uint8_t> bytes,std::vector<std::uint8_t> decoded)
        :cohort(source),input_ordinal(input),minimum_component(first),wire(bytes.begin(),bytes.end()),logical(std::move(decoded)){}
};
std::size_t Session::WorldCallbackSelectionEmission::selection_ordinal() const noexcept{return data_->input_ordinal;}
const std::vector<std::uint8_t>& Session::WorldCallbackSelectionEmission::expected_wire() const noexcept{return data_->wire;}
struct Session::WorldCallbackOutput::Component::Data {
    const std::weak_ptr<WorldCallbackOutput::Data> cohort;
    const Kind kind;
    const std::size_t ordinal;
    const std::vector<std::uint8_t> logical;
    std::vector<WorldCallbackSelectionEmission> emissions; // GAME only until whole seal.
    std::atomic<std::shared_ptr<const std::vector<std::uint8_t>>> wire;
    std::atomic<WorldCallbackOutputStatus> status{WorldCallbackOutputStatus::Pending};
    Data(std::shared_ptr<WorldCallbackOutput::Data> owner,Kind form,std::size_t index,
         std::span<const std::uint8_t> input):cohort(owner),kind(form),ordinal(index),logical(input.begin(),input.end()){emissions.reserve(1);}
};
struct Session::WorldCallbackSelectionInput::Data {
    const std::shared_ptr<WorldCallbackOutput::Data> cohort;
    const WorldCallbackOutput::SelectionKey key;
    const RecoveredDeitySelection::Request request;
    Data(std::shared_ptr<WorldCallbackOutput::Data> owner,WorldCallbackOutput::SelectionKey value)
        :cohort(std::move(owner)),key(value),request{value.key}{}
};
struct Session::WorldCallbackOutputCursor::Data {
    const std::shared_ptr<WorldCallbackOutput::Data> cohort;
    const std::size_t first;
    Data(std::shared_ptr<WorldCallbackOutput::Data> owner,std::size_t value):cohort(std::move(owner)),first(value){}
};
Session::WorldCallbackOutputStatus Session::WorldCallbackOutput::status() const noexcept{return data_->status.load();}
bool Session::WorldCallbackOutput::sealed() const noexcept{return data_->sealed.load(std::memory_order_acquire);}
bool Session::WorldCallbackOutput::callback_accepted() const noexcept{return data_->accepted.load();}
std::span<const Session::WorldCallbackOutput::SelectionKey> Session::WorldCallbackOutput::selection_keys() const noexcept{return data_->keys;}
std::span<const Session::WorldCallbackOutput::Component> Session::WorldCallbackOutput::components() const noexcept{
    return sealed()?std::span<const Component>(data_->components):std::span<const Component>{};
}
std::span<const std::uint8_t> Session::WorldCallbackOutput::final_return_wire() const noexcept{
    return sealed()?std::span<const std::uint8_t>(data_->final_wire):std::span<const std::uint8_t>{};
}
Session::WorldCallbackOutputStatus Session::WorldCallbackOutput::Component::status() const noexcept{return data_->status.load();}
Session::WorldCallbackOutput::Kind Session::WorldCallbackOutput::Component::kind() const noexcept{return data_->kind;}
std::span<const Session::WorldCallbackSelectionEmission> Session::WorldCallbackOutput::Component::emissions() const noexcept{
    const auto owner=data_->cohort.lock();
    if(!owner||!owner->sealed.load(std::memory_order_acquire)||owner->status.load()!=WorldCallbackOutputStatus::Written)return {};
    return data_->emissions;
}
std::size_t Session::WorldCallbackOutput::Component::ordinal() const noexcept{return data_->ordinal;}
const std::vector<std::uint8_t>& Session::WorldCallbackOutput::Component::logical() const noexcept{return data_->logical;}
std::shared_ptr<const std::vector<std::uint8_t>> Session::WorldCallbackOutput::Component::wire() const noexcept{return data_->wire.load();}
const RecoveredDeitySelection::Request& Session::WorldCallbackSelectionInput::request() const noexcept{return data_->request;}
std::size_t Session::WorldCallbackSelectionInput::selection_ordinal() const noexcept{return data_->key.ordinal;}
std::size_t Session::WorldCallbackSelectionInput::record_index() const noexcept{return data_->key.record_index;}
std::size_t Session::WorldCallbackOutputCursor::first_component_ordinal() const noexcept{return data_->first;}
void Session::WorldCallbackOutput::Data::complete() noexcept {
    if(!sealed.load(std::memory_order_acquire)||!accepted.load()||status.load()!=WorldCallbackOutputStatus::Pending)return;
    // Physical whole-Written custody preserves actual FIFO order. Whether
    // that order can be adopted as canonical selection state is the registry
    // policy, not a reason to close otherwise unchanged original writes.
    for(const auto& emission:emissions){
        const auto tag=emission.data_;const auto location=tag->location;
        if(tag->phase.load()!=WorldCallbackSelectionEmission::Data::Phase::Bound||
           location.component_ordinal>=components.size()||location.component_ordinal<tag->minimum_component){
            fail();return;
        }
    }
    if(components.empty()){
        auto pending=WorldCallbackOutputStatus::Pending;
        status.compare_exchange_strong(pending,WorldCallbackOutputStatus::NoOutput);
        return; // Accepted empty callback, explicitly no Written/Write receipt.
    }
    for(const auto& part:components)if(part.status()!=WorldCallbackOutputStatus::Written)return;
    auto pending=WorldCallbackOutputStatus::Pending;
    status.compare_exchange_strong(pending,WorldCallbackOutputStatus::Written);
}

struct Session::NormalWorldOutputHandle::Sync {
    std::mutex mutex; // Revocation/epoch retirement versus actual FIFO insertion.
    std::atomic<std::uint64_t> epoch{1}; // Saturates: no old epoch can wrap current.
};
struct Session::NormalWorldOutputHandle::Data {
    const std::shared_ptr<Sync> sync;
    const std::shared_ptr<const NormalWorldInitialization::Data> initialization;
    const std::uint64_t epoch,account,character,battle;
    const SessionState phase;
    std::atomic<bool> revoked{false};
    Data(std::shared_ptr<Sync> guard,std::shared_ptr<const NormalWorldInitialization::Data> source,
         std::uint64_t version,SessionState p)
        :sync(std::move(guard)),initialization(std::move(source)),epoch(version),
         account(initialization->entry->account),character(initialization->entry->character),
         battle(initialization->effective_battle),phase(p) {}
};
void Session::NormalWorldOutputHandle::revoke() const noexcept {
    if(!data_)return;
    std::lock_guard lock(data_->sync->mutex);
    data_->revoked.store(true);
}
struct Session::NormalWorldOutputAttempt::Data {
    std::atomic<NormalWorldOutputStatus> status{NormalWorldOutputStatus::Pending};
};
Session::NormalWorldOutputStatus Session::NormalWorldOutputAttempt::status() const noexcept {
    return data_->status.load();
}

struct Session::NormalWorldResponseAttempt::Data {
    const std::thread::id game_thread=std::this_thread::get_id();
    const std::shared_ptr<NormalWorldOutputHandle::Data> recipient;
    std::atomic<NormalWorldResponseStatus> status{NormalWorldResponseStatus::Pending};
    std::atomic<bool> armed{false},retired{false};
    // Game callback writes these before handoff; strand receives frozen values.
    std::vector<std::vector<std::uint8_t>> components;
    std::size_t component_bytes=0;
    explicit Data(std::shared_ptr<NormalWorldOutputHandle::Data> source):recipient(std::move(source)) {}
};
Session::NormalWorldResponseStatus Session::NormalWorldResponseAttempt::status() const noexcept {
    return data_->status.load();
}

struct Session::NormalWorldCallbackAdmission::Data {
    const std::thread::id game_thread=std::this_thread::get_id();
    const std::shared_ptr<NormalWorldOutputHandle::Data> source;
    std::atomic<NormalWorldCallbackAdmissionStatus> status{NormalWorldCallbackAdmissionStatus::Pending};
    explicit Data(std::shared_ptr<NormalWorldOutputHandle::Data> actual):source(std::move(actual)) {}
};
Session::NormalWorldCallbackAdmissionStatus Session::NormalWorldCallbackAdmission::status() const noexcept {
    return data_->status.load();
}
void Session::NormalWorldCallbackAdmission::reject() const noexcept {
    auto pending=NormalWorldCallbackAdmissionStatus::Pending;
    data_->status.compare_exchange_strong(pending,NormalWorldCallbackAdmissionStatus::Failed);
}

struct Session::NativePkEntryHold::Data {
    enum class Phase {Preparing,Held,Committed,Released,Written,Failed,Aborted};
    const std::weak_ptr<Session> session;
    const std::uint64_t session_id;
    const std::thread::id thread=std::this_thread::get_id();
    const asio::any_io_executor game;
    const NativePkEntryRequest request;
    const SessionState prebattle_phase;
    const NormalWorldInitialization initialization;
    const std::shared_ptr<const void> common;
    const std::shared_ptr<const WorldDeliveryIdentity> battle_identity;
    // Actual pre-PK WORLD identity; not Request::world_generation's namespace.
    const std::shared_ptr<const WorldDeliveryIdentity> original_world_identity;
    const std::shared_ptr<std::vector<std::uint8_t>> frame;
    const std::weak_ptr<NativePkEntryOwner> source;
    std::atomic<Phase> phase{Phase::Preparing};
    std::atomic<bool> held_notified{false},completing{false},clean_abort{false};
    std::atomic<bool> written_accepted{false}; // Only actual game completion may set true.
    Data(std::weak_ptr<Session> s,std::uint64_t id,asio::any_io_executor executor,
         NativePkEntryRequest r,SessionState phase,NormalWorldInitialization init,std::shared_ptr<const void> c,
         std::shared_ptr<const WorldDeliveryIdentity> identity,std::shared_ptr<const WorldDeliveryIdentity> original,
         std::shared_ptr<std::vector<std::uint8_t>> bytes,std::weak_ptr<NativePkEntryOwner> owner)
        :session(std::move(s)),session_id(id),game(std::move(executor)),request(std::move(r)),prebattle_phase(phase),
         initialization(std::move(init)),common(std::move(c)),battle_identity(std::move(identity)),
         original_world_identity(std::move(original)),frame(std::move(bytes)),source(std::move(owner)){}
};
const Session::NativePkEntryRequest& Session::NativePkEntryHold::request()const noexcept{return data_->request;}
std::uint64_t Session::NativePkEntryHold::session_id()const noexcept{return data_->session_id;}
std::uint64_t Session::NativePkEntryHold::committed_battle_generation()const noexcept{return data_->request.prebattle_generation+1;}
struct Session::NativePkTerminalBarrier::Data {
    enum class Phase {Draining,Ready,Consumed,Returned,Failed};
    const std::weak_ptr<Session> session;
    const std::thread::id thread=std::this_thread::get_id();
    const asio::any_io_executor game;
    const NativePkEntryHold entry;
    const NativeBattleSkill final;
    const std::weak_ptr<NativePkTerminalOwner> source;
    const std::shared_ptr<const NativeTaiwanReceiverSelector::Data> receiver_selector;
    std::mutex finalisation_mutex;
    std::weak_ptr<NativePkReturnFinalisation::Data> finalisation; // No Term→Final→Term strong cycle.
    std::atomic<Phase> phase{Phase::Draining};
    std::atomic<bool> accepted{false},ready_notified{false},failed_notified{false},armed{false},acknowledged{false},ack_handoff_failed{false};
    Data(std::weak_ptr<Session> s,asio::any_io_executor executor,NativePkEntryHold hold,
         NativeBattleSkill output,std::weak_ptr<NativePkTerminalOwner> owner,
         std::shared_ptr<const NativeTaiwanReceiverSelector::Data> selector)
        :session(std::move(s)),game(std::move(executor)),entry(std::move(hold)),
         final(std::move(output)),source(std::move(owner)),receiver_selector(std::move(selector)){}
};

struct Session::NativePkReturnPreparation::Data {
    const NativePkTerminalBarrier terminal;
    const NormalWorldInitialization initialization;
    const std::shared_ptr<const WorldDeliveryIdentity> world_identity;
    Data(NativePkTerminalBarrier barrier,NormalWorldInitialization normal,
         std::shared_ptr<const WorldDeliveryIdentity> world)
        :terminal(std::move(barrier)),initialization(std::move(normal)),world_identity(std::move(world)) {}
};

struct Session::NativePkReturnReservation::Data {
    enum class Phase {Pending,Reserved,Consuming,Consumed,Returned,Failed};
    const std::array<std::weak_ptr<Session>,2> sessions;
    const std::array<NativePkReturnPreparation,2> preparations;
    const asio::any_io_executor game;
    const std::thread::id thread=std::this_thread::get_id();
    const std::weak_ptr<NativePkReturnOwner> source;
    std::atomic<Phase> phase{Phase::Pending};
    std::atomic<unsigned> cuts{0};
    std::atomic<bool> installed{false},game_posted{false},failed_notified{false};
    Data(const std::array<std::shared_ptr<Session>,2>& actual,
        std::array<NativePkReturnPreparation,2> prepared,asio::any_io_executor executor,
        std::weak_ptr<NativePkReturnOwner> owner)
        :sessions{actual[0],actual[1]},preparations(std::move(prepared)),
         game(std::move(executor)),source(std::move(owner)) {}
};

namespace {
// Pure private plan lifetime. Seals never retain a Plan, Records, Session,
// gameplay input, source, callback or game-affine owner.
struct ActorStatusPublicationPlanIdentity final {std::atomic<bool> active{true};};
}
struct TaiwanActorStatusPublication::FrameSeal::Data final {
    struct Unit {std::size_t offset;TaiwanActorStatusPublication::ActorUnit actor;};
    const std::shared_ptr<ActorStatusPublicationPlanIdentity> plan;
    const Session* const recipient_address;
    const std::weak_ptr<Session> recipient_owner;
    const std::uint64_t recipient_id;
    const std::size_t ordinal,logical_size;
    const std::shared_ptr<const std::vector<std::uint8_t>> frame;
    const std::vector<std::uint8_t> encoded; // Whole immutable frame copy.
    const std::vector<Unit> units; // Ordered actual logical offsets, not guessed wire offsets.
    Data(std::shared_ptr<ActorStatusPublicationPlanIdentity> identity,const std::shared_ptr<Session>& recipient,
        std::size_t index,std::size_t size,std::shared_ptr<std::vector<std::uint8_t>> bytes,std::vector<Unit> actors)
        :plan(std::move(identity)),recipient_address(recipient.get()),recipient_owner(recipient),
         recipient_id(recipient->id()),ordinal(index),logical_size(size),frame(std::move(bytes)),
         encoded(*frame),units(std::move(actors)){}
    bool retained() const noexcept {
        if(!plan||!plan->active.load()||!frame||encoded!=*frame||units.empty()||
           encoded.size()!=logical_size+3)return false;
        std::size_t end=0;
        for(const auto& unit:units){
            const auto& actor=unit.actor;
            if(unit.offset<end||unit.offset>logical_size||actor.logical().size()>logical_size-unit.offset||
               actor.recipient().session!=recipient_id||!actor.retained())return false;
            end=unit.offset+actor.logical().size();
        }
        return plan->active.load();
    }
};
// Network-owned return data contains only capabilities/bytes/weak source identity.
// Never lock Records identity on a strand: its actual owning State is game-only.
struct Session::NativePkReturnOutputPlan::Data {
    struct Group {
        std::shared_ptr<Session> recipient;
        std::optional<NormalWorldOutputHandle> normal;
        std::vector<std::shared_ptr<std::vector<std::uint8_t>>> frames;
        std::vector<std::optional<TaiwanActorStatusPublication::FrameSeal>> frame_seals{};
    };
    const std::shared_ptr<ActorStatusPublicationPlanIdentity> status_identity;
    const NativePkReturnReservation reservation;
    const std::array<std::shared_ptr<Session>,2> sessions;
    const std::array<NativePkReturnPreparation,2> preparations;
    const std::weak_ptr<const void> records;
    const std::thread::id thread=std::this_thread::get_id();
    const asio::any_io_executor game;
    const std::vector<Group> groups;
    std::atomic<bool> claimed{false};
    Data(NativePkReturnReservation pair,std::array<std::shared_ptr<Session>,2> actual,
        std::array<NativePkReturnPreparation,2> prepared,std::weak_ptr<const void> source,
        asio::any_io_executor executor,std::vector<Group> ordered,std::shared_ptr<ActorStatusPublicationPlanIdentity> identity)
        :status_identity(std::move(identity)),reservation(std::move(pair)),sessions(std::move(actual)),preparations(std::move(prepared)),
         records(std::move(source)),game(std::move(executor)),groups(std::move(ordered)){}
    ~Data(){status_identity->active.store(false);}
};
bool Session::actor_status_frame_matches(const std::optional<TaiwanActorStatusPublication::FrameSeal>& seal,
        const std::shared_ptr<std::vector<std::uint8_t>>& frame,const Session& recipient,std::size_t ordinal,
        const NativePkReturnOutputPlan::Data& plan) noexcept {
    if(!seal)return true; // Existing unowned producer has no new synthetic authority.
    const auto& data=seal->data_;
    const auto actual_owner=recipient.weak_from_this();
    return data&&data->plan==plan.status_identity&&data->recipient_address==&recipient&&data->recipient_id==recipient.id()&&data->ordinal==ordinal&&
        !data->recipient_owner.owner_before(actual_owner)&&!actual_owner.owner_before(data->recipient_owner)&&
        data->frame.get()==frame.get()&&!data->frame.owner_before(frame)&&!frame.owner_before(data->frame)&&data->retained();
}
struct Session::NativePkReturnOutputHold::Data {
    enum class Phase {Pending,Held,Consuming,Consumed,Returned,Failed};
    struct Frame {
        const std::shared_ptr<std::vector<std::uint8_t>> bytes;
        std::atomic<std::shared_ptr<Reservation>> budget;
        const std::optional<TaiwanActorStatusPublication::FrameSeal> status_seal;
        explicit Frame(std::shared_ptr<std::vector<std::uint8_t>> value,
            std::optional<TaiwanActorStatusPublication::FrameSeal> seal)
            :bytes(std::move(value)),status_seal(std::move(seal)){}
    };
    struct Recipient {
        const std::shared_ptr<Session> session;
        const std::optional<NormalWorldOutputHandle> normal;
        const std::vector<std::shared_ptr<Frame>> frames;
        std::atomic<bool> held{false},slot_owned{false},failure_closed{false},close_posted{false};
        Recipient(std::shared_ptr<Session> actual,std::optional<NormalWorldOutputHandle> proof,
            std::vector<std::shared_ptr<Frame>> bytes)
            :session(std::move(actual)),normal(std::move(proof)),frames(std::move(bytes)){}
    };
    const std::shared_ptr<NativePkReturnOutputPlan::Data> plan;
    const std::weak_ptr<NativePkReturnOutputOwner> source;
    const std::vector<std::shared_ptr<Recipient>> recipients;
    std::mutex transition; // Failure vs one-use consume; never source/close under lock.
    std::atomic<std::shared_ptr<NativePkReturnConsumption::Data>> consumption;
    std::atomic<std::shared_ptr<NativePkReturnPublication::Data>> publication;
    std::atomic<std::shared_ptr<NativePkReturnFinalisation::Data>> finalisation;
    std::atomic<Phase> phase{Phase::Pending};
    std::atomic<std::size_t> cuts{0};
    std::atomic<bool> installed{false},game_posted{false},failed_notified{false};
    Data(std::shared_ptr<NativePkReturnOutputPlan::Data> value,std::weak_ptr<NativePkReturnOutputOwner> owner,
        std::vector<std::shared_ptr<Recipient>> actual)
        :plan(std::move(value)),source(std::move(owner)),recipients(std::move(actual)){}
};
struct Session::NativePkReturnConsumption::Data {
    enum class Phase {Prepared,Consuming,Consumed,Returned,Failed};
    const std::weak_ptr<NativePkReturnOutputHold::Data> output;
    const std::shared_ptr<NativePkReturnOutputPlan::Data> plan;
    const std::weak_ptr<NativePkReturnConsumptionOwner> source;
    const std::array<std::uint64_t,2> old_epochs,new_epochs;
    std::atomic<Phase> phase{Phase::Prepared};
    std::atomic<bool> failed_notified{false};
    Data(std::shared_ptr<NativePkReturnOutputHold::Data> held,std::weak_ptr<NativePkReturnConsumptionOwner> owner,
        std::array<std::uint64_t,2> old,std::array<std::uint64_t,2> future)
        :output(held),plan(held->plan),source(std::move(owner)),old_epochs(old),new_epochs(future){}
};
struct Session::NativePkReturnConsumption::Custody {
    const std::shared_ptr<Data> data;
    explicit Custody(std::shared_ptr<Data> source):data(std::move(source)){}
    ~Custody(){
        if(data->phase.load()!=Data::Phase::Failed&&data->phase.load()!=Data::Phase::Returned)
            if(const auto output=data->output.lock())Session::fail_native_pk_return_output(output);
    }
};
struct Session::NativePkReturnPublication::Data {
    struct Progress {
        std::atomic<std::size_t> next{0};
        std::atomic<bool> released{false},done{false};
    };
    const std::weak_ptr<NativePkReturnOutputHold::Data> output;
    const std::weak_ptr<NativePkReturnConsumption::Data> consumption;
    const std::shared_ptr<NativePkReturnOutputPlan::Data> plan;
    const std::weak_ptr<NativePkReturnPublicationOwner> source;
    const std::vector<std::shared_ptr<Progress>> progress;
    std::atomic<NativePkReturnPublicationStatus> phase{NativePkReturnPublicationStatus::Prepared};
    std::atomic<bool> exposed{false},game_posted{false},failed_notified{false},successfully_returned{false};
    std::atomic<std::size_t> cuts{0};
    Data(std::shared_ptr<NativePkReturnOutputHold::Data> held,
        std::shared_ptr<NativePkReturnConsumption::Data> consumed,std::weak_ptr<NativePkReturnPublicationOwner> owner,
        std::vector<std::shared_ptr<Progress>> values)
        :output(held),consumption(consumed),plan(held->plan),source(std::move(owner)),progress(std::move(values)){}
};
struct Session::NativePkReturnPublication::Work {
    const std::shared_ptr<Data> data;
    explicit Work(std::shared_ptr<Data> value):data(std::move(value)){}
    ~Work(){
        if(data->phase.load()==NativePkReturnPublicationStatus::Released)
            if(const auto output=data->output.lock())Session::fail_native_pk_return_output(output);
    }
};
struct Session::NativePkReturnPublication::Custody {
    const std::shared_ptr<Data> data;
    std::shared_ptr<Work> prepared_work; // Transferred to REAL posts/async handlers on release.
    Custody(std::shared_ptr<Data> value,std::shared_ptr<Work> work):data(std::move(value)),prepared_work(std::move(work)){}
    ~Custody(){if(data->phase.load()!=NativePkReturnPublicationStatus::Failed&&!data->successfully_returned.load())
        if(const auto output=data->output.lock())Session::fail_native_pk_return_output(output);}
};
struct Session::NativePkReturnFinalisation::Data {
    const std::weak_ptr<NativePkReturnPublication::Data> publication;
    const std::weak_ptr<NativePkReturnOutputHold::Data> output;
    const std::array<std::weak_ptr<Session>,2> sessions;
    const std::array<NativePkReturnPreparation,2> preparations;
    const std::array<std::shared_ptr<const void>,2> common;
    const std::array<std::uint64_t,2> epochs;
    const std::weak_ptr<const void> records;
    const asio::any_io_executor game;
    const std::thread::id thread=std::this_thread::get_id();
    const std::weak_ptr<NativePkReturnFinalisationOwner> source;
    std::mutex transition;
    std::weak_ptr<Work> work; // Actual tasks only; never retained by network slots.
    std::atomic<NativePkReturnFinalisationStatus> phase{NativePkReturnFinalisationStatus::Prepared};
    std::array<std::atomic<bool>,2> ready{},resume_started{};
    std::atomic<unsigned> ready_cuts{0},resume_cuts{0};
    std::atomic<bool> detached{false},returned_notified{false},failed_notified{false};
    Data(std::shared_ptr<NativePkReturnPublication::Data> pub,std::shared_ptr<NativePkReturnOutputHold::Data> held,
        std::weak_ptr<NativePkReturnFinalisationOwner> owner,std::array<std::shared_ptr<const void>,2> roots,
        std::array<std::uint64_t,2> values)
        :publication(pub),output(held),sessions{held->plan->sessions[0],held->plan->sessions[1]},
         preparations(held->plan->preparations),common(std::move(roots)),epochs(values),records(held->plan->records),
         game(held->plan->game),source(std::move(owner)){}
};
struct Session::NativePkReturnFinalisation::Work {
    const std::shared_ptr<Data> data;
    explicit Work(std::shared_ptr<Data> value):data(std::move(value)){}
    ~Work(){const auto phase=data->phase.load();
        if(phase!=NativePkReturnFinalisationStatus::Prepared&&phase!=NativePkReturnFinalisationStatus::Failed&&
           !data->returned_notified.load())Session::fail_native_pk_return_finalisation(data);}
};
struct Session::NativePkReturnFinalisation::Custody {
    const std::shared_ptr<Data> data;
    std::shared_ptr<Work> prepared_work;
    Custody(std::shared_ptr<Data> value,std::shared_ptr<Work> work):data(std::move(value)),prepared_work(std::move(work)){}
    ~Custody(){if(data->phase.load()!=NativePkReturnFinalisationStatus::Returned&&
        data->phase.load()!=NativePkReturnFinalisationStatus::Failed)Session::fail_native_pk_return_finalisation(data);}
};
struct Session::NativeWorldSelectionInput::Data {
    const std::weak_ptr<Session> session;
    const std::shared_ptr<const void> world_identity;
    const std::uint64_t account,character,generation,batch,battle;
    const std::size_t index;
    const SessionState phase;
    const RecoveredSelectionItemRequest::Request request;
    const RecoveredSelectionItemRequest::LogicalRecord logical;
};
const RecoveredSelectionItemRequest::Request& Session::NativeWorldSelectionInput::request() const noexcept {return data_->request;}
const RecoveredSelectionItemRequest::LogicalRecord& Session::NativeWorldSelectionInput::logical() const noexcept {return data_->logical;}
std::uint64_t Session::NativeWorldSelectionInput::batch_sequence() const noexcept {return data_->batch;}
std::size_t Session::NativeWorldSelectionInput::record_index() const noexcept {return data_->index;}

template<bool Dispatch,class Executor,class Body>
void Session::schedule_actor_status_work(const Executor& executor,
        const std::array<std::shared_ptr<Session>,2>& sessions,Body&& body) {
    // Actual call sites use plain lambdas and the same explicit executor.
    // Preserve the original handler type/path when this monitor is absent.
    const bool monitored=(sessions[0]&&sessions[0]->has_actor_status_write_fence())||
        (sessions[1]&&sessions[1]->has_actor_status_write_fence());
    if(!monitored) {
        if constexpr(Dispatch)asio::dispatch(executor,std::forward<Body>(body));
        else asio::post(executor,std::forward<Body>(body));
        return;
    }
    std::array<std::optional<TaiwanActorStatusWriteFence::Writer>,2> writers;
    for(std::size_t i=0;i<sessions.size();++i)
        if(sessions[i])writers[i]=sessions[i]->begin_actor_status_writer();
    // A failed monitor admission poisons its node, not the legacy send.
    // Fixed ticket holders own no Session, Presence or game-affine callback.
    ActorStatusWriterWork<std::decay_t<Body>> held{
        std::move(writers),std::forward<Body>(body)};
    if constexpr(Dispatch)asio::dispatch(executor,std::move(held));
    else asio::post(executor,std::move(held));
}

struct Session::WorldReplyPushCapture::Data {
    struct Pending {
        struct Frame {std::shared_ptr<Reservation> reservation;std::function<void(bool)> callback;std::shared_ptr<const std::atomic_bool> source_live{};};
        const std::weak_ptr<Session> session;
        const std::uint64_t account,character,battle;
        const SessionState phase;
        const std::shared_ptr<const WorldDeliveryIdentity> delivery;
        std::atomic<bool> settled{false},failed{false};
        std::vector<Frame> frames;
        std::vector<std::uint8_t> wire;
        std::size_t base=0;
        Pending(Session& owner,std::shared_ptr<const WorldDeliveryIdentity> identity)
            :session(owner.weak_from_this()),account(owner.account_id),character(owner.character_id),battle(owner.battle_generation()),phase(owner.state()),delivery(std::move(identity)){}
        void collect(bool accepted,std::array<std::function<void(bool)>,max_writes>& callbacks,std::size_t& count) noexcept {
            if(settled.exchange(true))return;
            if(!accepted)failed.store(true);
            for(auto& frame:frames)if(frame.callback){if(count>=callbacks.size())std::terminate();callbacks[count++]=std::move(frame.callback);}
        }
        static void invoke(std::array<std::function<void(bool)>,max_writes>& callbacks,std::size_t count,bool accepted) noexcept {
            for(std::size_t i=0;i<count;++i)try{callbacks[i](accepted);}catch(...){}
        }
        void settle(bool accepted) noexcept {
            std::array<std::function<void(bool)>,max_writes> callbacks;std::size_t count=0;
            collect(accepted,callbacks,count);invoke(callbacks,count,accepted);
        }
        ~Pending(){settle(false);}
    };
    const std::thread::id thread=std::this_thread::get_id();
    const std::weak_ptr<Session> session;
    const std::shared_ptr<Pending> pending;
    std::shared_ptr<void> window;
    WorldReplyPushWire profile; // GAME only; never retained by Pending/NET.
    bool finished=false,encoding=false;
    Data(Session& owner,WorldReplyPushWire encoder,std::shared_ptr<const WorldDeliveryIdentity> identity)
        :session(owner.weak_from_this()),pending(std::make_shared<Pending>(owner,std::move(identity))),profile(std::move(encoder)){}
    ~Data(){if(thread!=std::this_thread::get_id())std::terminate();}
};

struct Session::Impl {
    using ReplyPushPending=WorldReplyPushCapture::Data::Pending;
    struct ReplyPushFinal {
        std::vector<std::shared_ptr<ReplyPushPending>> fragments;
        std::vector<std::uint8_t> wire;
        std::atomic<bool> settled{false};
        void settle(bool accepted) noexcept {
            if(settled.exchange(true))return;
            std::array<std::function<void(bool)>,max_writes> callbacks;std::size_t count=0;
            for(const auto& fragment:fragments)fragment->collect(accepted,callbacks,count);
            ReplyPushPending::invoke(callbacks,count,accepted);
        }
        ~ReplyPushFinal(){settle(false);}
    };
    struct QualifiedWorldPushPending {
        std::atomic<bool> settled{false},invalid{false};
        std::function<void(bool)> callback;
        explicit QualifiedWorldPushPending(std::function<void(bool)> value):callback(std::move(value)){}
        void settle(bool accepted) noexcept {
            if(settled.exchange(true))return;
            if(callback){auto once=std::move(callback);try{once(accepted);}catch(...){}}
        }
        ~QualifiedWorldPushPending(){settle(false);}
    };
    std::shared_ptr<QualifiedWorldPushPending> qualified_push_active; // GAME-only framing reentry fence, no profile retained.
    [[noreturn]] void reject_qualified_profile_sender(){
        if(qualified_world_push_profile){auto& source=*qualified_world_push_profile->impl_;
            if(const auto pending=source.qualified_push_active){pending->invalid.store(true);source.poison_callback_reply();poison_world_response();pending->settle(false);}}
        throw std::logic_error("Qualified world profile may frame but may not send/reenter");
    }
    // This marker is DISTINCT from the Data retained by Application. Its last
    // post/Write owner retiring an uncompleted attempt marks Failed even while
    // the game still retains the private handle. Pure data only, on any thread.
    struct CallbackOutputAttempt {
        const std::shared_ptr<WorldCallbackOutput::Data> receipt;
        std::atomic<bool> accepted{false};
        explicit CallbackOutputAttempt(std::shared_ptr<WorldCallbackOutput::Data> value):receipt(std::move(value)){}
        ~CallbackOutputAttempt(){if(!accepted.load())receipt->fail();}
    };
    struct CallbackComponentAttempt {
        const std::shared_ptr<WorldCallbackOutput::Component::Data> receipt;
        // Actual post/Write owns the observation even if passive public Data
        // is dropped. Cohort owns ComponentData, never this Attempt: no cycle.
        const std::shared_ptr<WorldCallbackOutput::Data> cohort;
        std::shared_ptr<std::vector<std::uint8_t>> frame; // Strand only.
        std::atomic<bool> completed{false};
        explicit CallbackComponentAttempt(std::shared_ptr<WorldCallbackOutput::Component::Data> value)
            :receipt(std::move(value)),cohort(receipt->cohort.lock()){}
        ~CallbackComponentAttempt(){
            if(completed.load())return;
            auto pending=WorldCallbackOutputStatus::Pending;
            receipt->status.compare_exchange_strong(pending,WorldCallbackOutputStatus::Failed);
            if(const auto cohort=receipt->cohort.lock())cohort->fail();
        }
    };
    struct CallbackReplyWindow {
        const std::thread::id thread=std::this_thread::get_id();
        const std::weak_ptr<Session> session;
        std::atomic<bool> active{true},poisoned{false};
        std::size_t base=0;
        std::uint64_t next_nonce=0,nonce=0;
        std::vector<std::shared_ptr<const WorldCallbackOutput::Data::ReplyFragment>> fragments;
        struct Deferred {WorldCallbackSelectionEmission emission;std::size_t offset;};
        std::vector<Deferred> deferred;
        std::vector<std::shared_ptr<ReplyPushPending>> pushes;
        std::size_t deferred_bytes=0;
        explicit CallbackReplyWindow(std::weak_ptr<Session> owner):session(std::move(owner)){}
    };
    std::shared_ptr<CallbackReplyWindow> callback_reply_window; // Actual callback GAME only.
    std::shared_ptr<WorldReplyPushCapture::Data> reply_push_capture;
    bool reply_push_failed=false; // Actual callback GAME only.
    std::size_t reply_push_frames=0; // Bounded across all scopes in one callback.
    static bool reply_push_sources_live(const std::shared_ptr<ReplyPushPending>& pending) noexcept {
        if(!pending)return false;
        for(const auto& frame:pending->frames)if(frame.source_live&&!frame.source_live->load())return false;
        return true;
    }
    static bool reply_push_sources_live(const std::shared_ptr<ReplyPushFinal>& final) noexcept {
        if(!final)return true;
        // FIFO acceptance settles Pending, but its pure source flags remain
        // retained by the actual Write until physical write/remove.
        for(const auto& pending:final->fragments)if(!reply_push_sources_live(pending))return false;
        return true;
    }
    bool reply_push_current(const std::shared_ptr<ReplyPushPending>& pending,bool game) const {
        const auto delivery=world_delivery_identity.load();
        if(!pending||pending->failed.load()||pending->settled.load()||!reply_push_sources_live(pending)||pending->session.lock().get()!=&owner||close_requested.load()||
           mode!=ProtocolMode::God2CharacterConnection||!owner.recovered_world_ready()||owner.state()!=pending->phase||owner.battle_generation()!=pending->battle||
           !delivery||!pending->delivery||delivery->account!=pending->account||delivery->character!=pending->character||delivery->battle_generation!=pending->battle||
           delivery->world_generation!=pending->delivery->world_generation||!delivery->world_generation)return false;
        return !game||(owner.account_id==pending->account&&owner.character_id==pending->character&&owner.native_channel_binding_current());
    }
    void fail_reply_pushes() noexcept {
        reply_push_failed=true;poison_callback_reply();poison_world_response();
        std::array<std::function<void(bool)>,max_writes> callbacks;std::size_t count=0;
        if(callback_reply_window)for(const auto& pending:callback_reply_window->pushes)pending->collect(false,callbacks,count);
        if(reply_push_capture)reply_push_capture->pending->collect(false,callbacks,count);
        ReplyPushPending::invoke(callbacks,count,false);
    }
    void capture_reply_push(std::span<const std::uint8_t> logical,std::function<void(bool)> callback={},const WorldDeliveryIdentity* expected=nullptr,
        std::shared_ptr<const std::atomic_bool> source_live={}){
        const auto capture=reply_push_capture;
        try{
            if(logical.empty()||logical.size()>RecoveredWorldFrame::max_logical_size)throw std::logic_error("Captured logical bounds rejected");
            // Copy borrowed caller storage before any allocation or supplier can
            // reenter and retire that storage. Neither view escapes this call.
            const auto logical_size=logical.size();
            std::array<std::uint8_t,RecoveredWorldFrame::max_logical_size> original_bytes;
            std::copy_n(logical.begin(),logical_size,original_bytes.begin());
            const std::span<const std::uint8_t> original(original_bytes.data(),logical_size);
            const auto expected_copy=expected?std::optional<WorldDeliveryIdentity>{*expected}:std::nullopt;
            const auto current=[&]{
                return capture&&reply_push_capture==capture&&capture->thread==std::this_thread::get_id()&&observed_world_callback==&owner&&callback_output_active&&
                    !reply_push_failed&&!capture->finished&&callback_reply_window&&callback_reply_window->active.load()&&!callback_reply_window->poisoned.load()&&
                    capture->window==callback_reply_window&&reply_push_current(capture->pending,true)&&(!source_live||source_live->load());
            };
            if(!current()||capture->encoding||!capture->profile||reply_push_frames>=max_writes)
                throw std::logic_error("Original-run world push capture retired/reentered");
            capture->encoding=true;struct Reset {bool& flag;~Reset(){flag=false;}} reset{capture->encoding};
            // Moving is noexcept. invalidate/finish may clear Data::profile,
            // but cannot destroy the callable currently executing on GAME.
            auto encoder=std::move(capture->profile);
            const auto pending=capture->pending;const auto delivery=pending->delivery;
            if(expected_copy&&(expected_copy->account!=delivery->account||expected_copy->character!=delivery->character||expected_copy->world_generation!=delivery->world_generation||expected_copy->battle_generation!=delivery->battle_generation))
                throw std::logic_error("Captured push expected delivery tuple differs");
            // The provider sees only this owned mutable copy, never the
            // caller's memory or the private original used for qualification.
            std::vector<std::uint8_t> provider_logical(original.begin(),original.end());
            const auto charge=logical_size+3;
            auto reservation=std::make_shared<Reservation>(budget,charge,1,false);
            {std::lock_guard lock(budget->mutex);if(charge>max_buffer-budget->bytes||budget->count>=max_writes)throw std::overflow_error("Captured world push producer budget");
                budget->bytes+=charge;++budget->count;reservation->charged=true;}
            if(!current())throw std::logic_error("Captured world push source retired before profile");
            auto framed=encoder(owner,provider_logical);
            if(!framed||framed->size()!=charge||framed->size()<4||std::size_t((*framed)[0])+256u*(*framed)[1]!=framed->size()||
               !current()||provider_logical.size()!=logical_size||!std::equal(original.begin(),original.end(),provider_logical.begin()))
                throw std::logic_error("Captured world push profile/source/bounds mismatch");
            // Preserve the provider's exact returned bytes in private bounded
            // storage before decoder/reserve allocations can reenter suppliers.
            std::array<std::uint8_t,RecoveredWorldFrame::max_logical_size+3> original_wire;
            std::copy_n(framed->begin(),charge,original_wire.begin());
            const std::span<const std::uint8_t> wire(original_wire.data(),charge);
            const auto decoded=RecoveredWorldFrame::decode(wire);
            if(!decoded||decoded->size()!=logical_size||!std::equal(original.begin(),original.end(),decoded->begin())||!current())
                throw std::logic_error("Captured world push differs from original fixed-profile logical");
            // Complete every potentially allocating growth before moving the
            // sole acceptance callback into a noexcept Frame commit.
            if(pending->wire.size()>max_buffer-charge||pending->frames.size()>=max_writes)throw std::overflow_error("Captured world push aggregate bounds");
            pending->frames.reserve(pending->frames.size()+1);
            pending->wire.reserve(pending->wire.size()+charge);
            if(!current()||reply_push_frames>=max_writes||pending->frames.size()>=max_writes||pending->wire.size()>max_buffer-charge||
               provider_logical.size()!=logical_size||!std::equal(original.begin(),original.end(),provider_logical.begin())||
               callback_output_activity==std::numeric_limits<std::size_t>::max())
                throw std::logic_error("Captured world push retired during allocation");
            static_assert(std::is_nothrow_move_constructible_v<ReplyPushPending::Frame>);
            pending->frames.push_back({std::move(reservation),std::move(callback),std::move(source_live)});++reply_push_frames;
            pending->wire.insert(pending->wire.end(),wire.begin(),wire.end());
            ++callback_output_activity; // No independent observed component/Write.
            capture->profile=std::move(encoder);
        }catch(...){fail_reply_pushes();if(callback)try{callback(false);}catch(...){}throw;}
    }
    bool reply_push_slices(const std::shared_ptr<ReplyPushFinal>& final,std::span<const std::uint8_t> actual,bool game) const {
        if(!final||final->wire.size()!=actual.size()||!std::equal(final->wire.begin(),final->wire.end(),actual.begin()))return false;
        std::size_t previous=0;bool first=true;
        for(const auto& pending:final->fragments){const auto at=pending->base;
            if(!reply_push_current(pending,game)||at>actual.size()||pending->wire.size()>actual.size()-at||(!first&&at<previous)||
               !reply_frame_boundary(actual,at)||!std::equal(pending->wire.begin(),pending->wire.end(),actual.begin()+at))return false;
            previous=at+pending->wire.size();first=false;
        }return true;
    }
    std::shared_ptr<ReplyPushFinal> finish_reply_pushes(std::span<const std::uint8_t> actual){
        const auto window=callback_reply_window;
        if(!reply_push_failed&&!reply_push_capture&&(!window||window->pushes.empty()))return {};
        if(reply_push_failed||reply_push_capture||!window||!window->active.load()||window->poisoned.load()||window->thread!=std::this_thread::get_id()||window->nonce||window->base)
            throw std::logic_error("Unbalanced/failed original-run world push capture");
        std::size_t frames=0;for(const auto& pending:window->pushes){if(pending->frames.size()>max_writes-frames)throw std::logic_error("Captured callback aggregate frame bound");frames+=pending->frames.size();}
        auto final=std::make_shared<ReplyPushFinal>();final->fragments=window->pushes;final->wire.assign(actual.begin(),actual.end());
        if(!reply_push_slices(final,actual,true))throw std::logic_error("Original-run world push final exact slices changed");
        for(const auto& pending:final->fragments)for(const auto& existing:window->fragments)
            if(pending->base<existing->base+existing->wire.size()&&existing->base<pending->base+pending->wire.size())throw std::logic_error("Generic and causal final fragments overlap");
        return final;
    }
    std::shared_ptr<CallbackReplyWindow> reply_window() {
        if(observed_world_callback!=&owner||!callback_output_active)throw std::logic_error("Reply provenance requires actual callback");
        if(!callback_reply_window)callback_reply_window=std::make_shared<CallbackReplyWindow>(owner.weak_from_this());
        const auto window=callback_reply_window;
        if(!window->active.load()||window->poisoned.load()||window->thread!=std::this_thread::get_id()||
           window->session.lock().get()!=&owner)throw std::logic_error("Reply provenance callback retired");
        return window;
    }
    void poison_callback_reply() noexcept {
        if(callback_reply_window)callback_reply_window->poisoned.store(true);
        if(callback_output_capture)callback_output_capture->receipt->fail();
    }
    static bool reply_frame_boundary(std::span<const std::uint8_t> wire,std::size_t wanted) noexcept {
        for(std::size_t at=0;at<wire.size();){
            if(wire.size()-at<2)return false;
            const auto size=std::size_t(wire[at])+256u*wire[at+1];
            if(size<4||size>wire.size()-at)return false;
            if(at==wanted)return true;if(at>wanted)return false;at+=size;
        }
        return false;
    }
    void bind_side_emission(const std::shared_ptr<CallbackComponentAttempt>& component,
            const WorldCallbackSelectionEmission& emission,std::span<const std::uint8_t> logical){
        const auto data=component?component->cohort:nullptr;const auto tag=emission.data_;
        if(!data||tag->cohort.lock()!=data||component->receipt->ordinal<tag->minimum_component||
           tag->phase.load()!=WorldCallbackSelectionEmission::Data::Phase::Created||
           logical.size()!=tag->logical.size()||!std::equal(logical.begin(),logical.end(),tag->logical.begin())){
            if(data)data->fail();throw std::logic_error("Causal side emission not its exact current logical frame");
        }
        component->receipt->emissions.push_back(emission);
        tag->location={component->receipt->ordinal,0,0,tag->logical.size()};
        tag->phase.store(WorldCallbackSelectionEmission::Data::Phase::Bound);
    }

    // A later tagged guild prefix must not overtake an earlier selection that
    // an outer appender already reserved in its final reply. Keep its original
    // occurrence at the exact raw-prefix fence; ordinary pushes stay unchanged.
    bool defer_selection_reply(const WorldCallbackSelectionEmission& emission,
            std::span<const std::uint8_t> logical) {
        const auto window=reply_window();const auto tag=emission.data_;
        const auto capture=callback_output_capture;const auto data=capture?capture->receipt:nullptr;
        if(!data || tag->cohort.lock()!=data ||
           tag->phase.load()!=WorldCallbackSelectionEmission::Data::Phase::Created ||
           logical.size()!=tag->logical.size() ||
           !std::equal(logical.begin(),logical.end(),tag->logical.begin()))
            throw std::logic_error("Deferred selection is not its exact original source");
        bool preceding=false;std::size_t preceding_end=0;
        for(const auto& fragment:window->fragments)for(const auto& range:fragment->ranges) {
            const auto previous=range.emission.data_;
            if(previous->input_ordinal<tag->input_ordinal &&
               previous->phase.load()==WorldCallbackSelectionEmission::Data::Phase::FinalReserved) {
                if(fragment->base>max_buffer || range.offset>max_buffer-fragment->base ||
                   previous->wire.size()>max_buffer-fragment->base-range.offset)
                    throw std::logic_error("Buffered selection bounds overflow");
                preceding=true;preceding_end=std::max(preceding_end,fragment->base+range.offset+previous->wire.size());
            }
        }
        if(!preceding)return false; // No earlier final-buffered selection to overtake.
        if(window->base<preceding_end || window->base>max_buffer ||
           window->deferred.size()>=8192 || tag->wire.size()>max_buffer-window->deferred_bytes ||
           (!window->deferred.empty() && (window->base<window->deferred.back().offset ||
             emission.selection_ordinal()<=window->deferred.back().emission.selection_ordinal())))
            throw std::logic_error("Deferred selection fence is not a bounded ordered prefix");
        window->deferred.push_back({emission,window->base});
        auto created=WorldCallbackSelectionEmission::Data::Phase::Created;
        if(!tag->phase.compare_exchange_strong(created,WorldCallbackSelectionEmission::Data::Phase::Deferred))
            throw std::logic_error("Selection already handed to another output");
        window->deferred_bytes+=tag->wire.size();return true;
    }

    void materialize_deferred_selections(std::vector<std::uint8_t>& raw) {
        const auto window=callback_reply_window;if(!window || window->deferred.empty())return;
        const auto reject=[] {throw std::logic_error("Deferred selection source/fence changed");};
        const auto capture=callback_output_capture;const auto data=capture?capture->receipt:nullptr;
        if(!data || !window->active.load() || window->poisoned.load() ||
           window->thread!=std::this_thread::get_id() || window->nonce || window->base ||
           raw.size()>max_buffer || window->deferred_bytes>max_buffer-raw.size() ||
           !valid_world_response(raw))reject();
        const auto boundary=[&](std::size_t at) {
            return at==raw.size() || reply_frame_boundary(raw,at);
        };
        const auto translated=[&](std::size_t at) {
            std::size_t result=at;
            for(const auto& added:window->deferred)
                if(added.offset<=at)result+=added.emission.expected_wire().size();
            return result;
        };
        const auto intact=[&](std::size_t at,std::size_t size) {
            if(at>raw.size() || size>raw.size()-at)return false;
            for(const auto& added:window->deferred)
                if(at<added.offset && added.offset<at+size)return false;
            return true;
        };
        auto originals=window->fragments;
        std::sort(originals.begin(),originals.end(),[](const auto& a,const auto& b){return a->base<b->base;});
        std::size_t previous_end=0;bool first=true;
        using Fragment=WorldCallbackOutput::Data::ReplyFragment;
        using Range=WorldCallbackOutput::Data::ReplyRange;
        std::vector<std::shared_ptr<const Fragment>> next;
        for(const auto& fragment:originals) {
            const auto at=fragment->base;
            if(at>raw.size() || fragment->wire.size()>raw.size()-at ||
               (!first && at<previous_end) || !boundary(at) ||
               !std::equal(fragment->wire.begin(),fragment->wire.end(),raw.begin()+at))reject();
            first=false;previous_end=at+fragment->wire.size();
            std::size_t range_end=0;
            for(const auto& range:fragment->ranges) {
                const auto tag=range.emission.data_;
                if(tag->cohort.lock()!=data ||
                   tag->phase.load()!=WorldCallbackSelectionEmission::Data::Phase::FinalReserved ||
                   range.offset<range_end || range.offset>fragment->wire.size() ||
                   tag->wire.size()>fragment->wire.size()-range.offset ||
                   !reply_frame_boundary(fragment->wire,range.offset) ||
                   !std::equal(tag->wire.begin(),tag->wire.end(),fragment->wire.begin()+range.offset) ||
                   !intact(at+range.offset,tag->wire.size()))reject();
                range_end=range.offset+tag->wire.size();
                // The whole original fragment was verified before narrowing to
                // exact source frames. Never discover provenance by byte search.
                next.push_back(std::make_shared<const Fragment>(translated(at+range.offset),
                    tag->wire,std::vector<Range>{{range.emission,0}}));
            }
        }
        for(const auto& pending:window->pushes){
            if(!reply_push_current(pending,true)||!intact(pending->base,pending->wire.size())||!boundary(pending->base)||
               !std::equal(pending->wire.begin(),pending->wire.end(),raw.begin()+pending->base))reject();
            for(const auto& fragment:originals)if(pending->base<fragment->base+fragment->wire.size()&&fragment->base<pending->base+pending->wire.size())reject();
        }
        std::vector<std::uint8_t> merged;merged.reserve(raw.size()+window->deferred_bytes);
        std::size_t cursor=0;
        for(const auto& added:window->deferred) {
            const auto tag=added.emission.data_;
            if(tag->cohort.lock()!=data ||
               tag->phase.load()!=WorldCallbackSelectionEmission::Data::Phase::Deferred ||
               added.offset<cursor || !boundary(added.offset))reject();
            merged.insert(merged.end(),raw.begin()+cursor,raw.begin()+added.offset);
            next.push_back(std::make_shared<const Fragment>(merged.size(),tag->wire,
                std::vector<Range>{{added.emission,0}}));
            merged.insert(merged.end(),tag->wire.begin(),tag->wire.end());cursor=added.offset;
        }
        merged.insert(merged.end(),raw.begin()+cursor,raw.end());
        std::sort(next.begin(),next.end(),[](const auto& a,const auto& b){return a->base<b->base;});
        // Check physical order, including already posted tagged side outputs.
        std::optional<std::size_t> last;
        for(const auto& component:data->components)for(const auto& emission:component.data_->emissions) {
            if(last && emission.selection_ordinal()<=*last)reject();last=emission.selection_ordinal();
        }
        previous_end=0;first=true;
        for(const auto& fragment:next) {
            const auto ordinal=fragment->ranges.front().emission.selection_ordinal();
            if((!first && fragment->base<previous_end) || (last && ordinal<=*last))reject();
            first=false;previous_end=fragment->base+fragment->wire.size();last=ordinal;
        }
        if(movement_collector) {
            for(const auto& step:movement_collector->steps)
                if(!step->offset || !intact(*step->offset,step->frame.size()))reject();
            for(const auto& batch:movement_collector->normal_batches)
                if(!batch->offset || !intact(*batch->offset,batch->wire.size()))reject();
        }
        // Whole-response custody is immutable. Never rewrite a preexisting
        // exact receipt to bless different bytes. Current conflicting paths
        // must reject rather than borrow it; normal component checks run later.
        if(world_response_callback_capture && world_response_callback_capture->receipt->wire!=merged)reject();
        for(const auto& added:window->deferred) {
            auto deferred=WorldCallbackSelectionEmission::Data::Phase::Deferred;
            if(!added.emission.data_->phase.compare_exchange_strong(deferred,
                    WorldCallbackSelectionEmission::Data::Phase::FinalReserved))reject();
        }
        if(movement_collector) {
            for(const auto& step:movement_collector->steps)step->offset=translated(*step->offset);
            for(const auto& batch:movement_collector->normal_batches)batch->offset=translated(*batch->offset);
        }
        for(const auto& pending:window->pushes)pending->base=translated(pending->base);
        window->fragments.swap(next);window->deferred.clear();window->deferred_bytes=0;raw.swap(merged);
    }

    void bind_final_emissions(const std::shared_ptr<WorldCallbackOutput::Data>& data,
            const std::shared_ptr<CallbackComponentAttempt>& component,std::span<const std::uint8_t> actual){
        const auto window=callback_reply_window;
        if(!window)return;
        if(window->thread!=std::this_thread::get_id()||!window->active.load()||window->poisoned.load()||window->nonce||window->base){
            data->fail();throw std::logic_error("Final reply offset scopes not balanced");
        }
        auto fragments=window->fragments;
        std::sort(fragments.begin(),fragments.end(),[](const auto& a,const auto& z){return a->base<z->base;});
        std::size_t previous_end=0;bool first=true;
        for(const auto& fragment:fragments){
            const auto at=fragment->base;
            if(!component||at>actual.size()||fragment->wire.size()>actual.size()-at||
               (!first&&at<previous_end)||!reply_frame_boundary(actual,at)||
               !std::equal(fragment->wire.begin(),fragment->wire.end(),actual.begin()+at)){
                data->fail();throw std::logic_error("Exact indexed child reply fragment changed or overlaps");
            }
            previous_end=at+fragment->wire.size();first=false;
            for(const auto& range:fragment->ranges){
                const auto tag=range.emission.data_;
                if(tag->cohort.lock()!=data||tag->phase.load()!=WorldCallbackSelectionEmission::Data::Phase::FinalReserved||
                   component->receipt->ordinal<tag->minimum_component||range.offset>fragment->wire.size()||
                   tag->wire.size()>fragment->wire.size()-range.offset||!reply_frame_boundary(fragment->wire,range.offset)||
                   !reply_frame_boundary(actual,at+range.offset)||
                   !std::equal(tag->wire.begin(),tag->wire.end(),actual.begin()+at+range.offset)){
                    data->fail();throw std::logic_error("Causal final emission lost its exact indexed source frame");
                }
                component->receipt->emissions.push_back(range.emission);
                tag->location={component->receipt->ordinal,at+range.offset,0,tag->logical.size()};
                tag->phase.store(WorldCallbackSelectionEmission::Data::Phase::Bound);
            }
        }
        data->final_fragments=std::move(fragments);window->active.store(false);
    }
    bool callback_output_active=false; // Actual synchronous GAME callback only.
    std::size_t callback_output_activity=0;
    std::shared_ptr<CallbackOutputAttempt> callback_output_capture;
    std::atomic<std::shared_ptr<WorldCallbackOutput::Data>> callback_output_input_hold;
    bool has_input_hold() const noexcept{return bool(owned_response_input_hold.load())||bool(callback_output_input_hold.load());}
    std::shared_ptr<CallbackComponentAttempt> add_callback_component(
            const std::shared_ptr<WorldCallbackOutput::Data>& cohort,WorldCallbackOutput::Kind kind,
            std::span<const std::uint8_t> logical) noexcept {
        if(!cohort||cohort->status.load()!=WorldCallbackOutputStatus::Pending||cohort->sealed.load())return {};
        try{
            auto data=std::make_shared<WorldCallbackOutput::Component::Data>(cohort,kind,cohort->components.size(),logical);
            auto attempt=std::make_shared<CallbackComponentAttempt>(data);
            cohort->components.push_back(WorldCallbackOutput::Component(data));return attempt;
        }catch(...){cohort->fail();return {};}
    }
    std::shared_ptr<CallbackComponentAttempt> observe_callback_push(WorldCallbackOutput::Kind kind,
            std::span<const std::uint8_t> logical) noexcept {
        if(observed_world_callback!=&owner||!callback_output_active)return {};
        if(callback_output_activity!=std::numeric_limits<std::size_t>::max())++callback_output_activity;
        else if(callback_output_capture)callback_output_capture->receipt->fail();
        return callback_output_capture?add_callback_component(callback_output_capture->receipt,kind,logical):nullptr;
    }
    void unsupported_callback_output() noexcept {
        if(observed_world_callback!=&owner||!callback_output_active)return;
        if(callback_output_activity!=std::numeric_limits<std::size_t>::max())++callback_output_activity;
        if(callback_output_capture)callback_output_capture->receipt->fail();
    }
    bool callback_output_transport_current(const std::shared_ptr<WorldCallbackOutput::Data>& data) const noexcept {
        if(!data||data->session.lock().get()!=&owner||data->session_id!=id||close_requested.load()||
           mode!=ProtocolMode::God2CharacterConnection||!owner.recovered_world_ready()||owner.state()!=data->phase||
           owner.battle_generation()!=data->battle||
           (data->phase!=SessionState::CharacterSelected&&data->phase!=SessionState::InWorld))return false;
        const auto init=data->initialization;const auto entry=init->entry;
        return normal_initialization.load()==init&&normal_entry.load()==entry&&!entry->retired.load()&&
            entry->session.lock().get()==&owner&&entry->account==data->account&&entry->character==data->character&&
            init->effective_battle==data->battle&&!native_pk_pending.load()&&!native_battle_pending.load()&&!native_pk_terminal.load();
    }
    void release_callback_input_if_ready(const std::shared_ptr<WorldCallbackOutput::Data>& data) {
        if(!data||!data->armed.load()||data->released.load())return;
        if(!callback_output_transport_current(data)||data->status.load()==WorldCallbackOutputStatus::Failed){
            fail_owned_input("Callback output input hold retired");return;
        }
        if(data->status.load()!=WorldCallbackOutputStatus::Written&&
           data->status.load()!=WorldCallbackOutputStatus::NoOutput)return;
        auto expected=data;
        if(!callback_output_input_hold.compare_exchange_strong(expected,{})){
            fail_owned_input("Callback output input hold identity changed");return;
        }
        data->released.store(true);
        if(game_busy||read_inflight)return;
        try{resume_world_input(bool(skill_deadline));}catch(...){fail_owned_input("Callback output input continuation failed");}
    }
    struct WorldWriteAttempt {
        std::shared_ptr<WorldRecordsWrite::Data> receipt;
        std::shared_ptr<std::vector<std::uint8_t>> frame;
        explicit WorldWriteAttempt(std::shared_ptr<WorldRecordsWrite::Data> value):receipt(std::move(value)) {}
        ~WorldWriteAttempt() {
            auto pending=WorldRecordsWriteStatus::Pending;
            receipt->status.compare_exchange_strong(pending,WorldRecordsWriteStatus::Failed);
        }
    };
    struct MovementResponseAttempt {
        const std::shared_ptr<MovementResponseWrite::Data> receipt;
        std::shared_ptr<std::vector<std::uint8_t>> frame; // Assigned once on strand.
        explicit MovementResponseAttempt(std::shared_ptr<MovementResponseWrite::Data> value):receipt(std::move(value)) {}
        void fail() noexcept {
            auto state=receipt->status.load();
            while(state!=MovementResponseWriteStatus::Written && state!=MovementResponseWriteStatus::Failed &&
                !receipt->status.compare_exchange_weak(state,MovementResponseWriteStatus::Failed)) {}
        }
        ~MovementResponseAttempt(){fail();}
    };
    struct MovementCollector {
        const std::thread::id thread=std::this_thread::get_id();
        const std::shared_ptr<const void> occurrence=std::make_shared<const std::uint8_t>(0);
        const std::shared_ptr<const void> common;
        const std::span<const RecoveredWorldRecords::Record> original_records;
        std::vector<std::shared_ptr<MovementStepWrite::Data>> steps;
        std::vector<std::shared_ptr<NormalMovementBatchWrite::Data>> normal_batches;
        std::optional<NormalWorldInitialization> normal_initialization;
        const bool normal_mode;
        std::size_t run_first_batch=0,normal_assigned=0;
        std::vector<std::size_t> run_records;
        std::optional<SharedWorldPresence::Lease> lease;
        std::optional<std::size_t> last_registered_record;
        std::size_t assigned=0,output_base=0,run_first_step=0;
        std::uint64_t next_scope_nonce=0,offset_scope_nonce=0,run_nonce=0;
        std::atomic<bool> poisoned{false};
        bool active=true;
        MovementCollector(std::shared_ptr<const void> identity,std::span<const RecoveredWorldRecords::Record> original,
            std::size_t capacity,bool normal):common(std::move(identity)),original_records(original),normal_mode(normal) {
            steps.reserve(capacity);normal_batches.reserve(capacity);run_records.reserve(capacity);
        }
    };
    std::shared_ptr<MovementCollector> movement_collector; // Game callback only.
    std::atomic<std::shared_ptr<MovementResponseWrite::Data>> latest_movement_response; // Pure Data, thread-qualified getter.
    std::thread::id movement_game_thread;
    // Captured on game; only immutable bytes/weak Session/atomic status cross
    // to strand. Attempt retirement closes Pending even if Main keeps Data.
    struct WorldResponseAttempt {
        std::shared_ptr<WorldResponseWrite::Data> receipt;
        std::shared_ptr<std::vector<std::uint8_t>> frame;
        enum class InputPhase {Unarmed,Armed,Released,Retired};
        std::atomic<InputPhase> input_phase{InputPhase::Unarmed};
        explicit WorldResponseAttempt(std::shared_ptr<WorldResponseWrite::Data> value):receipt(std::move(value)) {}
        void fail() noexcept {
            auto pending=WorldResponseWriteStatus::Pending;
            receipt->status.compare_exchange_strong(pending,WorldResponseWriteStatus::Failed);
            auto armed=InputPhase::Armed;
            input_phase.compare_exchange_strong(armed,InputPhase::Retired);
            if(input_phase.load()==InputPhase::Retired)
                if(const auto self=receipt->session.lock()) {
                    self->impl_->owned_input_retired.store(true);
                    self->impl_->close_requested.store(true);
                }
        }
        ~WorldResponseAttempt(){fail();}
    };
    struct OwnedInputLease {
        const std::shared_ptr<WorldResponseAttempt> attempt;
        explicit OwnedInputLease(std::shared_ptr<WorldResponseAttempt> value):attempt(std::move(value)){}
        ~OwnedInputLease(){if(attempt->input_phase.load()!=WorldResponseAttempt::InputPhase::Released)attempt->fail();}
    };
    // The atomic hold is installed on GAME before any strand response post.
    // A separate callback/post/Write lease retires dropped delivery even while
    // this strong hold keeps the immutable private Attempt alive.
    std::atomic<std::shared_ptr<WorldResponseAttempt>> owned_response_input_hold;
    std::atomic<bool> owned_input_retired{false}; // Persistent opt-in-only failure ingress latch.
    std::shared_ptr<OwnedInputLease> owned_input_callback_lease; // Serial GAME only.
    std::shared_ptr<WorldResponseAttempt> world_response_callback_capture; // Serial game callback ONLY.
    struct NormalOutputPending {
        const std::shared_ptr<NormalWorldOutputAttempt::Data> data;
        explicit NormalOutputPending(std::shared_ptr<NormalWorldOutputAttempt::Data> value):data(std::move(value)) {}
        ~NormalOutputPending() {
            auto pending=NormalWorldOutputStatus::Pending;
            data->status.compare_exchange_strong(pending,NormalWorldOutputStatus::Failed);
        }
    };
    struct NormalResponsePending {
        const std::shared_ptr<NormalWorldResponseAttempt::Data> receipt;
        explicit NormalResponsePending(std::shared_ptr<NormalWorldResponseAttempt::Data> data):receipt(std::move(data)) {}
        void fail() noexcept {
            auto pending=NormalWorldResponseStatus::Pending;
            receipt->status.compare_exchange_strong(pending,NormalWorldResponseStatus::Failed);
            // TLS poison may already have changed status; still retire exactly once.
            if(receipt->status.load()!=NormalWorldResponseStatus::Failed || !receipt->armed.load() ||
               receipt->retired.exchange(true))return;
            const auto recipient=receipt->recipient;
            {
                std::lock_guard lock(recipient->sync->mutex);
                recipient->revoked.store(true);
                const auto epoch=recipient->sync->epoch.load();
                if(epoch!=std::numeric_limits<std::uint64_t>::max())recipient->sync->epoch.store(epoch+1);
            }
            if(const auto actual=recipient->initialization->entry->session.lock())
                actual->impl_->close_requested.store(true); // No post/source callback on failure.
        }
        ~NormalResponsePending(){fail();}
    };
    std::shared_ptr<NormalResponsePending> normal_response_callback_capture; // Serial game callback ONLY.
    struct NormalCallbackPending {
        const std::shared_ptr<NormalWorldCallbackAdmission::Data> receipt;
        explicit NormalCallbackPending(std::shared_ptr<NormalWorldCallbackAdmission::Data> data):receipt(std::move(data)) {}
        void fail() noexcept {
            auto pending=NormalWorldCallbackAdmissionStatus::Pending;
            receipt->status.compare_exchange_strong(pending,NormalWorldCallbackAdmissionStatus::Failed);
        }
        ~NormalCallbackPending(){fail();}
    };
    std::shared_ptr<NormalCallbackPending> normal_callback_admission_capture; // Actual whole game callback ONLY.
    struct SelectionEntry {
        const RecoveredSelectionItemRequest::Request* original;
        std::shared_ptr<const NativeWorldSelectionInput::Data> data;
        bool taken=false,dispatched=false;
    };
    struct SelectionWindow {
        const std::thread::id thread=std::this_thread::get_id();
        std::vector<SelectionEntry> entries;
        bool live=true;
    };
    std::shared_ptr<SelectionWindow> selection_window; // Serial game owner only.
    std::uint64_t selection_batch_sequence=0; // Server-local occurrence, not wire.
    std::shared_ptr<SelectionWindow> begin_selection_window(std::span<const RecoveredWorldRecords::Record> records) {
        if(selection_window) {
            selection_window->live=false;
            throw std::logic_error("Native C28 input scope reentry rejected");
        }
        if(!character_handlers.native_selection_input)return {};
        const auto count=std::count_if(records.begin(),records.end(),[](const auto& record){
            return std::holds_alternative<RecoveredSelectionItemRequest::Request>(record);
        });
        if(!count)return {};
        const auto identity=common_world_identity.load();const auto phase=owner.state();
        if(mode!=ProtocolMode::God2CharacterConnection || owner.closing() || !owner.recovered_world_ready() ||
           !owner.account_id || !owner.character_id || !identity || common_entry_identity.load() ||
           identity->account!=owner.account_id || identity->character!=owner.character_id ||
           (phase!=SessionState::InWorld && phase!=SessionState::InBattle) ||
           selection_batch_sequence==std::numeric_limits<std::uint64_t>::max())
            throw std::runtime_error("Native C28 input lacks actual authenticated ready identity");
        const auto batch=++selection_batch_sequence;
        auto window=std::make_shared<SelectionWindow>();window->entries.reserve(static_cast<std::size_t>(count));
        const auto connection=owner.shared_from_this();
        for(std::size_t index=0;index<records.size();++index) {
            const auto* request=std::get_if<RecoveredSelectionItemRequest::Request>(&records[index]);
            if(!request)continue;
            auto data=std::make_shared<const NativeWorldSelectionInput::Data>(NativeWorldSelectionInput::Data{
                connection,identity,identity->account,identity->character,identity->generation,batch,
                owner.battle_generation(),index,phase,*request,RecoveredSelectionItemRequest::encode(*request)});
            window->entries.push_back({request,std::move(data),false,false});
        }
        selection_window=window;return window;
    }
    struct SelectionScope {
        Impl& state;
        std::shared_ptr<SelectionWindow> window;
        SelectionScope(Impl& actual,std::span<const RecoveredWorldRecords::Record> records)
            :state(actual),window(actual.begin_selection_window(records)) {}
        ~SelectionScope() {
            if(window)window->live=false;
            if(window && state.selection_window==window)state.selection_window.reset();
        }
    };
    SelectionEntry* selection_entry(const NativeWorldSelectionInput& input) const {
        const auto window=selection_window;
        if(!window)return nullptr;
        if(window->thread!=std::this_thread::get_id())throw std::logic_error("Native C28 input game owner mismatch");
        const auto& data=input.data_;
        if(!window->live || !data || data->session.lock().get()!=&owner || owner.closing() ||
           !owner.recovered_world_ready() || owner.account_id!=data->account || owner.character_id!=data->character ||
           owner.state()!=data->phase || owner.battle_generation()!=data->battle || common_entry_identity.load() ||
           common_world_identity.load().get()!=data->world_identity.get() || data->batch!=selection_batch_sequence)
            return nullptr;
        for(auto& entry:window->entries)if(entry.data==data)return &entry;
        return nullptr;
    }
    std::atomic<std::shared_ptr<const Session::WorldDeliveryIdentity>> world_delivery_identity;
    struct CommonWorldIdentity {std::uint64_t account,character,generation;};
    std::atomic<std::shared_ptr<const CommonWorldIdentity>> common_world_identity;
    // Immutable data plus a weak game owner only. No game-owned callback or
    // source destructor is retained by network Write/handler copies.
    struct NativeBattlePending {
        Session::NativeBattleSkill delivery;
        std::shared_ptr<const CommonWorldIdentity> common;
        std::weak_ptr<Session::NativeBattleSkillPublicationOwner> source;
        std::shared_ptr<NativePkEntryHold::Data> pk_entry; // Absent for unchanged legacy sender.
        std::atomic<bool> completing{false};
    };
    std::atomic<std::shared_ptr<NativeBattlePending>> native_battle_pending;
    // New PK output only: wait until ordinary game callback ACK has queued
    // its response before inserting the held output. Network strand owns both.
    std::shared_ptr<NativeBattlePending> native_pk_output_staged;
    std::shared_ptr<Reservation> native_pk_output_reservation;
    std::atomic<std::shared_ptr<NativePkEntryHold::Data>> native_pk_pending;
    std::atomic<std::shared_ptr<NativePkTerminalBarrier::Data>> native_pk_terminal;
    std::atomic<std::shared_ptr<NativePkReturnReservation::Data>> native_pk_return;
    std::atomic<std::shared_ptr<NativePkReturnOutputHold::Data>> native_pk_return_output;
    std::atomic<std::shared_ptr<NativePkReturnConsumption::Data>> native_pk_return_consumption;
    std::atomic<std::shared_ptr<NativePkReturnFinalisation::Data>> native_pk_return_finalisation;
    std::atomic<std::shared_ptr<NativePkReturnFinalisation::Data>> native_pk_return_finalisation_history; // Exact pending handoff, not Current/Work.
    struct NativePkReturnOutputAttempt {
        const std::shared_ptr<NativePkReturnOutputHold::Data> data;
        explicit NativePkReturnOutputAttempt(std::shared_ptr<NativePkReturnOutputHold::Data> value):data(std::move(value)){}
        ~NativePkReturnOutputAttempt(){
            if(data->phase.load()==NativePkReturnOutputHold::Data::Phase::Pending)
                Session::fail_native_pk_return_output(data);
        }
    };
    struct NativePkReturnOutputWrite {
        // Queued nodes must NOT retain the pending task Attempt. Otherwise a
        // dropped last game post cannot poison Data and a queue cycle survives.
        const std::weak_ptr<NativePkReturnOutputHold::Data> cohort;
        const std::shared_ptr<NativePkReturnOutputHold::Data::Frame> frame;
        const std::size_t recipient,ordinal;
        NativePkReturnOutputWrite(std::weak_ptr<NativePkReturnOutputHold::Data> owner,
            std::shared_ptr<NativePkReturnOutputHold::Data::Frame> bytes,std::size_t at,std::size_t index)
            :cohort(std::move(owner)),frame(std::move(bytes)),recipient(at),ordinal(index){}
    };
    struct ActiveWriteContinuation {
        std::shared_ptr<NativePkReturnPublication::Work> work;
        const std::shared_ptr<std::vector<std::uint8_t>> frame;
        ActiveWriteContinuation(std::shared_ptr<NativePkReturnPublication::Work> value,
            std::shared_ptr<std::vector<std::uint8_t>> bytes):work(std::move(value)),frame(std::move(bytes)){}
    };
    // Pure actual initial-entry cohort bookkeeping. Queue tickets never own
    // tasks, game callbacks, the cohort or a Session. Task abandonment therefore
    // cannot form a queue/task cycle; removal revokes pre-release membership.
    struct InitialEntryStatusContext {
        const std::shared_ptr<ActorStatusPublicationPlanIdentity> identity=std::make_shared<ActorStatusPublicationPlanIdentity>();
        const Session* const recipient_address;
        const std::weak_ptr<Session> recipient_owner;
        const SharedWorldPresence::Lease recipient;
        std::atomic<std::size_t> frame_count{0},next{0};
        std::atomic<bool> completed{false};
        InitialEntryStatusContext(const std::shared_ptr<Session>& session,SharedWorldPresence::Lease lease)
            :recipient_address(session.get()),recipient_owner(session),recipient(std::move(lease)){}
        bool current() const noexcept {
            return identity->active.load()&&!completed.load()&&frame_count.load()!=0;
        }
        bool matches(const Session& session) const noexcept {
            const auto actual=session.weak_from_this();
            return recipient_address==&session&&recipient.session==session.id()&&
                !recipient_owner.owner_before(actual)&&!actual.owner_before(recipient_owner);
        }
        void retire() noexcept {identity->active.store(false);}
        ~InitialEntryStatusContext(){retire();}
    };
    struct InitialEntryIdentity {
        enum class Phase {Preparing,Installed,Publishing,Published,Released};
        std::atomic<Phase> phase{Phase::Preparing};
        std::atomic<bool> revoked{false};
        const std::shared_ptr<InitialEntryStatusContext> status;
        explicit InitialEntryIdentity(std::shared_ptr<InitialEntryStatusContext> value={}) noexcept:status(std::move(value)){}
        void revoke() noexcept {revoked.store(true);if(status)status->retire();}
        ~InitialEntryIdentity(){if(status)status->retire();}
    };
    struct InitialEntryMember {
        const std::shared_ptr<InitialEntryIdentity> identity;
        const std::size_t ordinal;
        const std::shared_ptr<std::vector<std::uint8_t>> frame;
        const std::vector<std::uint8_t> encoded;
        std::atomic<bool> present{false},completed{false};
        const std::optional<TaiwanActorStatusPublication::FrameSeal> status_seal;
        InitialEntryMember(std::shared_ptr<InitialEntryIdentity> key,std::size_t index,
            std::shared_ptr<std::vector<std::uint8_t>> bytes,
            std::optional<TaiwanActorStatusPublication::FrameSeal> seal={})
            :identity(std::move(key)),ordinal(index),frame(std::move(bytes)),encoded(*frame),status_seal(std::move(seal)){}
        bool retained_status() const noexcept {
            const auto& context=identity->status;
            if(!context)return !status_seal; // Original unowned initial path.
            if(identity->revoked.load()||!context->current()||ordinal>=context->frame_count.load()||
               !frame||encoded!=*frame)return false;
            if(!status_seal)return true; // This complete frame has no owned units.
            const auto& data=status_seal->data_;
            if(!data||data->plan!=context->identity||data->recipient_address!=context->recipient_address||
               data->recipient_id!=context->recipient.session||data->ordinal!=ordinal||
               data->recipient_owner.owner_before(context->recipient_owner)||context->recipient_owner.owner_before(data->recipient_owner)||
               data->frame.get()!=frame.get()||data->frame.owner_before(frame)||frame.owner_before(data->frame))return false;
            for(const auto& unit:data->units)if(unit.actor.recipient()!=context->recipient)return false;
            return data->retained()&&context->current()&&!identity->revoked.load();
        }
    };
    struct InitialEntryQueueTicket {
        const std::shared_ptr<InitialEntryMember> member;
        explicit InitialEntryQueueTicket(std::shared_ptr<InitialEntryMember> value):member(std::move(value)){}
        ~InitialEntryQueueTicket(){
            const bool present=member->present.exchange(false);
            if((present&&member->identity->phase.load()!=InitialEntryIdentity::Phase::Released)||
               (member->identity->status&&!member->completed.load()))member->identity->revoke();
        }
    };
    struct InitialEntryCohort {
        const std::shared_ptr<InitialEntryIdentity> identity;
        const std::vector<std::shared_ptr<InitialEntryMember>> members;
        const std::vector<std::shared_ptr<ActiveWriteContinuation>> holders;
        const std::shared_ptr<Reservation> reservation;
        const std::size_t charge;
        InitialEntryCohort(std::shared_ptr<InitialEntryIdentity> key,
            std::vector<std::shared_ptr<InitialEntryMember>> frames,
            std::vector<std::shared_ptr<ActiveWriteContinuation>> continuations,
            std::shared_ptr<Reservation> budget,std::size_t bytes)
            :identity(std::move(key)),members(std::move(frames)),holders(std::move(continuations)),
             reservation(std::move(budget)),charge(bytes){}
        bool held_current(InitialEntryIdentity::Phase expected) const noexcept {
            if(identity->revoked.load()||identity->phase.load()!=expected||members.empty()||
               members.size()!=holders.size()||!reservation||!reservation->charged||reservation->count!=members.size()||
               reservation->bytes!=charge)return false;
            for(std::size_t i=0;i<members.size();++i){
                const auto& member=members[i];const auto& holder=holders[i];
                if(!member||member->identity!=identity||member->ordinal!=i||!member->present.load()||
                   !member->frame||member->encoded!=*member->frame||!holder||holder->frame!=member->frame||
                   holder->frame.owner_before(member->frame)||member->frame.owner_before(holder->frame)||
                   !member->retained_status())return false;
            }
            return !identity->revoked.load()&&identity->phase.load()==expected;
        }
    };
    // The final queued notification has its OWN task-drop guard. Scheduling
    // is not delivery: only the actual game callback marks this delivered.
    // Last-drop closes/revokes without recursively posting another notification;
    // the existing game-vault teardown owns real affine cancellation callbacks.
    // Outward-only pure frame domain. No Profile, Scope, saved input, game
    // callback, pending-entry ticket or PK plan is retained by this context.
    struct OutwardStatusFrame {
        enum class Phase {Preparing,Held,Publishing,Published,Released,Written,Revoked};
        const std::shared_ptr<ActorStatusPublicationPlanIdentity> identity;
        const std::shared_ptr<const CommonWorldIdentity> common;
        const Session* const recipient_address;
        const std::weak_ptr<Session> recipient_owner;
        const SharedWorldPresence::Lease recipient;
        const std::uint64_t battle;
        const TaiwanActorStatusPublication::ActorUnit actor;
        const std::shared_ptr<std::vector<std::uint8_t>> frame;
        const std::vector<std::uint8_t> encoded;
        const TaiwanActorStatusPublication::FrameSeal seal;
        const std::shared_ptr<Reservation> reservation;
        std::atomic<Phase> phase{Phase::Preparing};
        std::atomic<bool> present{false};
        OutwardStatusFrame(std::shared_ptr<ActorStatusPublicationPlanIdentity> plan,
                std::shared_ptr<const CommonWorldIdentity> ready,const std::shared_ptr<Session>& session,
                ActorStatusOutputInput input,std::uint64_t generation,
                std::shared_ptr<std::vector<std::uint8_t>> bytes,TaiwanActorStatusPublication::FrameSeal proof,
                std::shared_ptr<Reservation> budget)
            :identity(std::move(plan)),common(std::move(ready)),recipient_address(session.get()),recipient_owner(session),
             recipient(std::move(input.recipient)),battle(generation),actor(std::move(input.actor)),
             frame(std::move(bytes)),encoded(*frame),seal(std::move(proof)),reservation(std::move(budget)){}
        bool retained() const noexcept {
            const auto value=phase.load();const auto& data=seal.data_;
            if(value==Phase::Revoked||value==Phase::Written||!identity->active.load()||
               !common||common->account!=recipient.account||common->character!=recipient.character||
               common->generation!=recipient.generation||!frame||encoded!=*frame||
               !reservation||!reservation->charged||reservation->count!=1||reservation->bytes!=frame->size()||
               actor.recipient()!=recipient||actor.source().session==recipient.session||!actor.retained()||
               !data||data->plan!=identity||data->recipient_address!=recipient_address||data->recipient_id!=recipient.session||
               data->ordinal!=0||data->logical_size!=RecoveredRemoteActor::logical_size+RecoveredTaiwanActorOverride::logical_size||
               data->recipient_owner.owner_before(recipient_owner)||recipient_owner.owner_before(data->recipient_owner)||
               data->frame.get()!=frame.get()||data->frame.owner_before(frame)||frame.owner_before(data->frame)||
               data->units.size()!=1||data->units[0].offset!=0||data->units[0].actor!=actor||!data->retained())return false;
            return identity->active.load()&&phase.load()==value;
        }
        bool matches(const Session& session) const noexcept {
            const auto actual=session.weak_from_this();
            return recipient_address==&session&&recipient.session==session.id()&&
                !recipient_owner.owner_before(actual)&&!actual.owner_before(recipient_owner);
        }
        void revoke() noexcept {
            auto value=phase.load();
            while(value!=Phase::Written&&value!=Phase::Revoked&&
                  !phase.compare_exchange_weak(value,Phase::Revoked)){}
            identity->active.store(false);
        }
        ~OutwardStatusFrame(){revoke();}
    };
    struct OutwardStatusWrite {
        const std::shared_ptr<OutwardStatusFrame> frame;
        explicit OutwardStatusWrite(std::shared_ptr<OutwardStatusFrame> value):frame(std::move(value)){}
        ~OutwardStatusWrite(){
            frame->present.store(false);
            if(frame->phase.load()!=OutwardStatusFrame::Phase::Written)frame->revoke();
        }
    };
    // GAME ONLY. The ready vault owns the forwarding callbacks after adoption.
    // This box is never captured by a strand/finish/async-write task.
    struct OutwardPublicationSubmission {
        const std::thread::id thread=std::this_thread::get_id();
        CommonWorldPublication actual;
        bool started=false,finished=false;
        bool publish() {
            if(thread!=std::this_thread::get_id())std::terminate();
            if(started||finished)return false;started=true;
            bool accepted=false;
            {const auto callback=std::move(actual.publish);if(callback)accepted=callback();}
            return accepted&&!finished; // Actual publisher destructor already ran.
        }
        void complete(bool accepted) {
            if(thread!=std::this_thread::get_id())std::terminate();
            if(finished)return;finished=true;
            auto callback=std::move(actual.queued);actual.publish={};
            if(callback)callback(accepted);
        }
        ~OutwardPublicationSubmission(){
            if(thread!=std::this_thread::get_id())std::terminate();
            if(!finished)try{complete(false);}catch(...){}
        }
    };
    struct OutwardQueuedDelivery {
        const std::weak_ptr<Session> session;
        const std::shared_ptr<OutwardStatusFrame> frame;
        std::atomic<bool> delivered{false};
        OutwardQueuedDelivery(std::weak_ptr<Session> actual,std::shared_ptr<OutwardStatusFrame> value)
            :session(std::move(actual)),frame(std::move(value)){}
        ~OutwardQueuedDelivery(){
            if(!delivered.load()){
                frame->revoke();
                if(const auto actual=session.lock())try{actual->close();}catch(...){}
            }
        }
    };
    // Actual posted tasks alone own this once guard. Its functions are ONLY
    // weak ready-vault facades; the game-affine submission box is absent here.
    struct OutwardStatusAttempt {
        const std::weak_ptr<Session> session;
        const std::shared_ptr<OutwardStatusFrame> frame;
        const asio::any_io_executor game;
        CommonWorldPublication publication;
        std::atomic<bool> armed{false},finished{false};
        OutwardStatusAttempt(std::weak_ptr<Session> actual,std::shared_ptr<OutwardStatusFrame> value,asio::any_io_executor executor)
            :session(std::move(actual)),frame(std::move(value)),game(std::move(executor)){}
        void complete(bool accepted) noexcept {
            if(!armed.load()||finished.exchange(true))return;
            if(!accepted)frame->revoke();
            try {
                auto queued=std::move(publication.queued);const auto actual=session.lock();
                if(!queued||!actual)throw std::logic_error("Ready publication completion facade unavailable");
                const auto delivery=std::make_shared<OutwardQueuedDelivery>(session,frame);
                actual->impl_->post_status_work(game,[queued=std::move(queued),accepted,delivery] {
                    const auto phase=delivery->frame->phase.load();
                    const bool granted=accepted&&(phase==OutwardStatusFrame::Phase::Released||
                        phase==OutwardStatusFrame::Phase::Written);
                    delivery->delivered.store(true);try{queued(granted);}catch(...){}
                });
            }catch(...){frame->revoke();if(const auto actual=session.lock())try{actual->close();}catch(...){}}
        }
        void abort() noexcept {
            frame->revoke();if(const auto actual=session.lock())try{actual->close();}catch(...){}
            complete(false);
        }
        ~OutwardStatusAttempt(){if(armed.load()&&!finished.load())abort();}
    };
    struct InitialEntryQueuedDelivery {
        const std::weak_ptr<Session> session;
        std::atomic<bool> delivered{false};
        explicit InitialEntryQueuedDelivery(std::weak_ptr<Session> owner):session(std::move(owner)){}
        ~InitialEntryQueuedDelivery(){
            if(!delivered.load())if(const auto owner=session.lock())try{owner->close();}catch(...){}
        }
    };
    // Pure ready-publication transport fact. GAME cleanup may cancel a
    // pending handoff; only the final IO cut can commit Released. This is not
    // a source Current, native ACK, Written or permission for later input.
    enum class CommonPublicationReleasePhase {Pending,Released,Cancelled};
    // The actual posted tasks alone own this guard. Actual callbacks stay in
    // the game vault; finish contains only its revocable facade and executor.
    // Genuine ready publications reuse the same pure once/drop guard.
    struct InitialEntryAttempt {
        const std::weak_ptr<Session> session;
        const std::function<void(bool)> finish;
        std::atomic<bool> finished{false};
        InitialEntryAttempt(std::weak_ptr<Session> owner,std::function<void(bool)> completion)
            :session(std::move(owner)),finish(std::move(completion)){}
        void complete(bool accepted) noexcept {
            if(finished.exchange(true))return;
            try{finish(accepted);}catch(...){if(const auto owner=session.lock())try{owner->close();}catch(...){}}
        }
        void abort() noexcept {
            if(const auto owner=session.lock())try{owner->close();}catch(...){}
            complete(false);
        }
        ~InitialEntryAttempt(){if(!finished.load())abort();}
    };
    // Weak bookkeeping only: the REAL async operation owns the continuation.
    std::weak_ptr<ActiveWriteContinuation> active_write_continuation;
    // Separate from the pair Data kept by the game owner. Last abandoned post
    // marks Pending failed even when that owning capability is still retained.
    struct NativePkReturnAttempt {
        const std::shared_ptr<NativePkReturnReservation::Data> data;
        explicit NativePkReturnAttempt(std::shared_ptr<NativePkReturnReservation::Data> value):data(std::move(value)) {}
        ~NativePkReturnAttempt() {
            if(data->phase.load()==NativePkReturnReservation::Data::Phase::Pending)
                Session::fail_native_pk_return_reservation(data);
        }
    };
    // Game-only incarnation of this actual callback, surviving strand retirement.
    std::shared_ptr<NativePkTerminalBarrier::Data> native_pk_terminal_callback_capture;
    // Strand-only staging until the accepted world's callback ACK has queued
    // its ordinary response. Never put that response behind the held entry.
    std::shared_ptr<Reservation> native_pk_reservation;
    struct CommonEntryIdentity {std::uint64_t account,character,generation,nonce,battle;SessionState state;};
    std::atomic<std::shared_ptr<const CommonEntryIdentity>> common_entry_identity;
    std::uint64_t common_entry_nonce=0; // Game owner; never reused.
    std::function<void(bool)> common_ready_completion; // Game owner only.
    std::uint64_t common_ready_nonce=0; // Game owner only.
    std::thread::id common_ready_thread; // Set before publishing a completion facade.
    std::atomic<bool> common_ready_waiting{false};
    bool common_ready_cancel_posted=false; // Network strand only.
    Session& owner;
    asio::ip::tcp::socket socket;
    asio::strand<asio::any_io_executor> strand;
    asio::any_io_executor game;
    asio::steady_timer timer;
    asio::steady_timer hold_timer;
    asio::steady_timer native_pk_timer;
    asio::steady_timer native_pk_terminal_timer;
    enum class SessionTimeoutPolicy { Normal, UiGateHold };
    SessionTimeoutPolicy timeout_policy=SessionTimeoutPolicy::Normal;
    std::filesystem::path hold_control;
    std::int64_t hold_entered_at=0;
    std::int64_t last_real_protocol_activity=0;
    std::uint64_t timer_generation=0;
    // Keeps the game context alive across the network-to-game handoff.
    asio::executor_work_guard<asio::any_io_executor> game_work;
    asio::executor_work_guard<asio::any_io_executor> network_work;
    const std::uint64_t id;
    std::string ip;
    bool packet_dump;
    ProtocolMode mode;
    std::vector<std::uint8_t> recovered_input;
    bool recovered_hello_written=false;
    bool post_select_strike_hold=false;
    RecoveredPostSeed::State post_seed_state=RecoveredPostSeed::State::Connected;
    enum class C2S0002State { AwaitSeed, AwaitRequest, RequestReceived, ResponseSent, ServerListSent, TerminalSent, PostSelectReceived, CharacterReady, CharacterCreateReceived, CharacterCreateCommitted, CharacterSelected, WorldEntrySent, WorldTailAccepted };
    C2S0002State c2s0002_state=C2S0002State::AwaitSeed;
    std::vector<std::uint8_t> c2s0002_input;
    std::vector<std::uint8_t> post_select_input;
    std::vector<std::uint8_t> character_create_input;
    std::vector<std::uint8_t> post_create_input;
    bool native_create_refresh=false;
    bool native_create_ack_sent=false;
    std::uint64_t pending_created_character=0; // Serial game executor only.
    std::optional<RecoveredWorldReady> world_ready;
    std::atomic<std::shared_ptr<NormalWorldInitialization::Entry>> normal_entry;
    std::atomic<std::shared_ptr<const NormalWorldInitialization::Data>> normal_initialization;
    TaiwanBattleSelfViewWriteFence battle_self_view_fence;
    TaiwanBattleSelfViewWriteFence battle_self_view_intents; // Pre-post output admission, not input work.
    std::atomic<std::shared_ptr<BattleSelfView::Data>> battle_self_view_source;
    // Serial GAME only. Original INIT tail/config remain immutable history.
    std::shared_ptr<const NativeTaiwanReceiverSelector::Data> receiver_selector;
    std::uint64_t receiver_selector_revision=0;
    std::shared_ptr<const NativeTaiwanReceiverSelector::Data> make_receiver_selector(
            const std::shared_ptr<NormalWorldInitialization::Entry>& entry,
            const std::array<std::uint8_t,4>& payload){
        if(!entry||entry->game_thread!=std::this_thread::get_id()||entry->session.lock().get()!=&owner||
           entry->retired.load()||payload[2]>1||payload[3]||
           receiver_selector_revision==std::numeric_limits<std::uint64_t>::max())return {};
        const auto world=RecoveredWorldEntryView::read(entry->frame);
        if(!world||world->actor_handle!=(std::uint16_t(payload[0])|(std::uint16_t(payload[1])<<8)))return {};
        const auto next=receiver_selector_revision+1;
        auto result=std::make_shared<const NativeTaiwanReceiverSelector::Data>(entry,next,payload);
        receiver_selector_revision=next;return result;
    }
    void accept_receiver_selector_records(std::span<const RecoveredWorldRecords::Record> records,
            const std::shared_ptr<NativePkTerminalBarrier::Data>& terminal){
        const auto normal=normal_initialization.load();
        bool seen=false;
        auto next=receiver_selector;
        for(const auto& record:records)if(const auto* context=std::get_if<RecoveredWorldRecords::ContextNotification>(&record)){
            seen=true;
            // A terminal retains THIS original callback's exact source node.
            if(terminal&&terminal->receiver_selector&&terminal->receiver_selector->context==context->payload)
                next=terminal->receiver_selector;
            else if(normal&&normal->entry&&normal->entry->written.load())
                next=make_receiver_selector(normal->entry,context->payload);
            else next.reset();
        }
        // Invalid accepted reports retire the old selector, never default it.
        if(seen)receiver_selector=std::move(next);
    }
    const std::shared_ptr<NormalWorldOutputHandle::Sync> normal_output_sync=
        std::make_shared<NormalWorldOutputHandle::Sync>();
    void retire_normal_output() noexcept {
        {
            std::lock_guard lock(normal_output_sync->mutex);
            const auto old=normal_output_sync->epoch.load();
            if(old!=std::numeric_limits<std::uint64_t>::max())normal_output_sync->epoch.store(old+1);
        }
        // No failure/close under Sync: own fresh cohort handles may lock it.
        if(const auto final=native_pk_return_finalisation.load()){
            const auto index=final->sessions[0].lock().get()==&owner?0u:1u;
            if(final->phase.load()==NativePkReturnFinalisationStatus::Returned&&final->resume_started[index].load()){
                auto expected=final;native_pk_return_finalisation.compare_exchange_strong(expected,{});
            }else Session::fail_native_pk_return_finalisation(final);
        }
        if(const auto output=native_pk_return_output.load())Session::fail_native_pk_return_output(output);
    }
    // Strand checks only immutable Entry/Data and synchronized/atomic fields.
    // Caller holds Sync::mutex through final validation and FIFO insertion.
    bool normal_output_transport_current_locked(const std::shared_ptr<NormalWorldOutputHandle::Data>& data) const {
        if(!data || data->sync!=normal_output_sync || data->revoked.load() ||
           data->epoch==std::numeric_limits<std::uint64_t>::max() || data->epoch!=normal_output_sync->epoch.load())return false;
        const auto init=data->initialization;const auto entry=init->entry;
        return mode==ProtocolMode::God2CharacterConnection && !close_requested.load() &&
            owner.recovered_world_ready() && owner.state()==data->phase &&
            (data->phase==SessionState::CharacterSelected || data->phase==SessionState::InWorld) &&
            owner.battle_generation()==data->battle && init->effective_battle==data->battle &&
            normal_entry.load()==entry && normal_initialization.load()==init &&
            entry->session.lock().get()==&owner && entry->account==data->account && entry->character==data->character &&
            data->account && data->character && entry->written.load() && !entry->retired.load() && !init->tail.empty() &&
            !native_pk_pending.load() && !native_battle_pending.load() && !native_pk_terminal.load();
    }
    // Own ORIGINAL response needs the actual INIT/epoch, not S2A Written.
    // Caller holds Sync::mutex; no public account/character reads or callbacks.
    bool normal_response_transport_current_locked(const std::shared_ptr<NormalWorldOutputHandle::Data>& data) const {
        if(!data || data->sync!=normal_output_sync || data->revoked.load() ||
           data->epoch==std::numeric_limits<std::uint64_t>::max() || data->epoch!=normal_output_sync->epoch.load())return false;
        const auto init=data->initialization;const auto entry=init->entry;
        return mode==ProtocolMode::God2CharacterConnection && !close_requested.load() &&
            owner.recovered_world_ready() && owner.state()==data->phase &&
            (data->phase==SessionState::CharacterSelected || data->phase==SessionState::InWorld) &&
            owner.battle_generation()==data->battle && init->effective_battle==data->battle &&
            normal_entry.load()==entry && normal_initialization.load()==init &&
            entry->session.lock().get()==&owner && entry->account==data->account && entry->character==data->character &&
            data->account && data->character && !entry->retired.load() &&
            !native_pk_pending.load() && !native_battle_pending.load() && !native_pk_terminal.load();
    }
    std::array<std::uint8_t,23> normal_tail_bytes{}; // Strand only; maximum existing grammar.
    std::size_t normal_tail_size=0;
    bool normal_tail_observable=true;
    std::vector<std::uint8_t> world_input;
    std::vector<RecoveredWorldRecords::Record> world_pending_records;
    // Only the explicit native skill lane. Context DWORD is not a nonce;
    // staged prefixes must not cross a leave/re-enter battle incarnation.
    std::optional<std::uint64_t> native_skill_generation;
    std::optional<std::chrono::steady_clock::time_point> skill_deadline;
    PacketHandler on_packet;
    DisconnectHandler on_disconnect;
    DisconnectCompletion disconnect_complete;
    RecoveredLoginHandler recovered_login;
    RecoveredCharacterHandlers character_handlers;
    bool common_world_lifecycle_factory_invoked=false; // Serial game executor only.
    std::function<void()> common_world_cleanup; // Serial game executor only.
    std::function<void()> common_world_terminal_begin; // GAME only; never copied to NET.
    std::function<bool(bool)> common_world_terminal_finish; // Paired cleanup settlement, not recovery authority.
    std::atomic<bool> common_world_cleanup_failed{false}; // Sticky GAME-originated failure, no clear operation.
    std::vector<std::uint8_t> character_routes;
    God2ProtocolSpec protocol;
    Buffer input;
    std::array<std::uint8_t, 8192> read_bytes{};
    struct Write {
        std::shared_ptr<std::vector<std::uint8_t>> bytes;
        std::shared_ptr<Reservation> reservation;
        bool world_entry{};
        bool held{}; // Explicit common-world/skill/PK transport holds only.
        std::shared_ptr<const Session::RecoveredServerAdvertisement> advertisement{};
        Session::NativeCharacterList native_list{}; // Pure data; callbacks stay in game vault.
        std::shared_ptr<NativeBattlePending> native_battle{};
        std::shared_ptr<WorldWriteAttempt> observed_world{};
        std::shared_ptr<NormalWorldInitialization::Entry> normal_entry{};
        std::shared_ptr<NativePkEntryHold::Data> native_pk{};
        std::shared_ptr<WorldResponseAttempt> observed_response{}; // Preserve old aggregate initializers.
        std::shared_ptr<OwnedInputLease> owned_input_lease{}; // Old aggregate positions preserved.
        std::shared_ptr<NativePkReturnOutputWrite> return_output{}; // Existing private cohort position.
        std::weak_ptr<ActiveWriteContinuation> pending_return_continuation{}; // Existing held-task holder.
        std::optional<TaiwanActorStatusWriteFence::Writer> status_writer{}; // Existing queue lifetime position.
        std::optional<TaiwanActorStatusPublication::FrameSeal> status_seal{}; // Existing pure exact frame version.
        std::shared_ptr<InitialEntryQueueTicket> initial_entry{}; // LAST: exact initial cohort membership.
        std::shared_ptr<OutwardStatusWrite> outward_status{}; // Existing ready whole86 status publication.
        std::shared_ptr<MovementResponseAttempt> movement_response{}; // Existing original sender custody.
        std::shared_ptr<BattleSelfView::Data> battle_self_view{}; // LAST: exact whole-Write occurrence.
        std::shared_ptr<CallbackComponentAttempt> callback_component{}; // LAST: actual self-Write only.
        std::shared_ptr<ReplyPushFinal> reply_pushes{}; // LAST: producer reservations through actual FIFO lifetime.
        std::shared_ptr<const std::atomic_bool> qualified_source_live{}; // LAST: pure cancellation, never authority.
    };
    std::deque<Write> writes;
    template<class Executor,class Body>
    void post_status_work(const Executor& executor,Body&& body) {
        Session::schedule_actor_status_work<false>(executor,{owner.shared_from_this(),{}},
            std::forward<Body>(body));
    }
    void append_write(Write value) {
        if(native_logout_phase==NativeLogoutPhase::Cleaning||native_logout_phase==NativeLogoutPhase::AckQueued||native_logout_phase==NativeLogoutPhase::Failed){
            if(native_logout_phase!=NativeLogoutPhase::AckQueued||value.bytes!=native_logout_ack||!writes.empty()){
                native_logout_phase=NativeLogoutPhase::Failed;close_requested.store(true);
                throw std::logic_error("Native logout cleanup cut acquired new output");
            }
        }
        // Every actual FIFO producer reaches this sink. Original provenance
        // must be on Write BEFORE insertion, never attached to writes.back().
        const auto entry=normal_entry.load();const auto original=value.normal_entry;
        if(mode==ProtocolMode::God2CharacterConnection){
            if(original){
                const bool exact=original==entry && !original->retired.load() &&
                    original->session.lock().get()==&owner && value.world_entry && !value.held && value.bytes &&
                    value.bytes->size()==original->frame.size() &&
                    std::equal(value.bytes->begin(),value.bytes->end(),original->frame.begin());
                if(!exact || !original->world_identity_sender.admit_original())original->world_identity_sender.revoke();
                if(entry && !exact)entry->world_identity_sender.revoke();
            }else if(entry && !entry->retired.load() &&
                (!value.bytes || TaiwanWorldIdentityWriteFence::conflicts_with_world_identity(*value.bytes))){
                // A live Entry also exists in CharacterSelected and InBattle.
                // Complete receiver phase routing is not qualified here. Revoke
                // only sender custody, not output, whole Init Current or selfslot.
                entry->world_identity_sender.revoke();
            }
        }
        // Self-view is a different source from original world identity. Every
        // relevant enqueue retires the prior epoch, even if it never writes.
        if(mode==ProtocolMode::God2CharacterConnection &&
           (entry || owner.state()==SessionState::InBattle || battle_self_view_source.load())){
            const auto analysis=value.bytes ? TaiwanBattleSelfViewWriteFence::inspect(*value.bytes) :
                TaiwanBattleSelfViewWriteFence::Analysis{true,{}};
            if(analysis.changes_view){
                const auto epoch=battle_self_view_fence.advance();
                if(const auto old=battle_self_view_source.exchange({}))old->completion.revoke();
                const auto response=value.observed_response;
                const auto source=response?response->receipt:nullptr;
                // Only one complete original callback Write qualifies. Generic
                // grants, split/cohort frames and native PK publications retire
                // the old source but do not mint one through this bounded path.
                if(epoch && analysis.primary_slot && source && value.bytes && response->frame==value.bytes &&
                   !value.held && source->session.lock().get()==&owner && source->account && source->character &&
                   source->phase==SessionState::InBattle && owner.state()==SessionState::InBattle &&
                   source->battle==owner.battle_generation() && source->wire==*value.bytes &&
                   battle_self_view_intents.current(source->self_view_intent) &&
                   source->status.load()==WorldResponseWriteStatus::Pending){
                    try {
                        value.battle_self_view=std::make_shared<BattleSelfView::Data>(owner.weak_from_this(),id,
                            source->account,source->character,source->battle,epoch,source->self_view_intent,*analysis.primary_slot,
                            source->game_thread,source,value.bytes);
                        battle_self_view_source.store(value.battle_self_view);
                    }catch(...){/* Optional sender metadata never changes legacy output. */}
                }
            }
        }
        const auto self_view=value.battle_self_view;
        // Conflict revocation precedes insertion, including failed/cancelled
        // insertion. A delayed original Written callback cannot undo it.
        try {
            owner.invalidate_actor_status_writes();
            value.status_writer=owner.begin_actor_status_writer();
            writes.push_back(std::move(value));
        }catch(...){
            if(original)original->world_identity_sender.revoke();
            if(self_view){
                self_view->completion.revoke();auto expected=self_view;
                battle_self_view_source.compare_exchange_strong(expected,{});
            }
            throw;
        }
    }
    // Strand-only full contiguous cohort validation. The game task uses the
    // corresponding pure ticket-presence proof, never reads this deque.
    bool initial_entry_queued(const std::shared_ptr<const InitialEntryCohort>& cohort,
            InitialEntryIdentity::Phase phase,std::size_t& first) const noexcept {
        if(!cohort||!cohort->held_current(phase))return false;
        std::size_t seen=0,index=0;bool ended=false;
        for(const auto& queued:writes){
            if(queued.initial_entry&&queued.initial_entry->member->identity==cohort->identity){
                if(ended||seen>=cohort->members.size())return false;
                const auto& member=cohort->members[seen];
                const auto holder=queued.pending_return_continuation.lock();
                if(!queued.held||queued.world_entry||queued.return_output||queued.status_seal||
                   queued.initial_entry->member!=member||queued.bytes!=member->frame||
                   queued.bytes.owner_before(member->frame)||member->frame.owner_before(queued.bytes)||
                   queued.reservation!=cohort->reservation||queued.reservation.owner_before(cohort->reservation)||
                   cohort->reservation.owner_before(queued.reservation)||holder!=cohort->holders[seen]||
                   holder.owner_before(cohort->holders[seen])||cohort->holders[seen].owner_before(holder))return false;
                if(!seen)first=index;
                ++seen;
            }else if(seen)ended=true;
            ++index;
        }
        return seen==cohort->members.size()&&cohort->held_current(phase);
    }
    // Strand-only released frame proof. Earlier completed frames may already
    // be gone; this must never demand the old entire held cohort.
    bool initial_entry_released_current(const std::shared_ptr<InitialEntryQueueTicket>& ticket,
            const std::optional<TaiwanActorStatusPublication::FrameSeal>& seal,
            const std::shared_ptr<std::vector<std::uint8_t>>& bytes) const noexcept {
        if(!ticket||!ticket->member||closing||close_requested.load()||writes.empty())return false;
        const auto& member=ticket->member;const auto& identity=member->identity;const auto& status=identity->status;
        const auto& queued=writes.front();
        return status&&status->matches(owner)&&!identity->revoked.load()&&status->current()&&
            identity->phase.load()==InitialEntryIdentity::Phase::Released&&
            status->next.load()==member->ordinal&&member->ordinal<status->frame_count.load()&&
            member->present.load()&&!member->completed.load()&&queued.initial_entry==ticket&&
            !queued.held&&!queued.world_entry&&!queued.return_output&&!queued.status_seal&&
            queued.bytes.get()==bytes.get()&&!queued.bytes.owner_before(bytes)&&!bytes.owner_before(queued.bytes)&&
            member->frame.get()==bytes.get()&&!member->frame.owner_before(bytes)&&!bytes.owner_before(member->frame)&&
            member->status_seal==seal&&member->retained_status();
    }
    // Atomic/private transport identity only. Safe on GAME or strand; never
    // read public account/character fields or the strand deque on game.
    bool outward_status_transport_current(const std::shared_ptr<OutwardStatusFrame>& frame) const noexcept {
        if(!frame)return false;
        const auto common=common_world_identity.load();
        return frame->matches(owner)&&!owner.closing()&&owner.recovered_world_ready()&&
            owner.state()==SessionState::InWorld&&owner.battle_generation()==frame->battle&&
            common==frame->common&&!common.owner_before(frame->common)&&!frame->common.owner_before(common)&&
            !common_entry_identity.load()&&frame->retained();
    }
    bool outward_status_held_current(const std::shared_ptr<OutwardStatusFrame>& frame,
            OutwardStatusFrame::Phase phase) const noexcept {
        return outward_status_transport_current(frame)&&frame->present.load()&&frame->phase.load()==phase;
    }
    // Strand-only complete actual marker/buffer/budget/holder identity.
    bool outward_status_queued(const std::shared_ptr<OutwardStatusWrite>& marker,
            const std::shared_ptr<ActiveWriteContinuation>& holder,OutwardStatusFrame::Phase phase,
            std::size_t& index) const noexcept {
        if(!marker||!holder||!outward_status_held_current(marker->frame,phase))return false;
        std::size_t seen=0,at=0;
        for(const auto& queued:writes){
            if(queued.outward_status==marker){
                const auto& frame=marker->frame;const auto held=queued.pending_return_continuation.lock();
                if(++seen!=1||!queued.held||queued.world_entry||queued.return_output||queued.status_seal||queued.initial_entry||
                   queued.bytes.get()!=frame->frame.get()||queued.bytes.owner_before(frame->frame)||frame->frame.owner_before(queued.bytes)||
                   queued.reservation!=frame->reservation||queued.reservation.owner_before(frame->reservation)||
                   frame->reservation.owner_before(queued.reservation)||held!=holder||held.owner_before(holder)||holder.owner_before(held)||
                   holder->frame.get()!=frame->frame.get()||holder->frame.owner_before(frame->frame)||frame->frame.owner_before(holder->frame))return false;
                index=at;
            }
            ++at;
        }
        return seen==1&&outward_status_held_current(marker->frame,phase);
    }
    bool outward_status_released_current(const std::shared_ptr<OutwardStatusWrite>& marker,
            const TaiwanActorStatusPublication::FrameSeal& seal,
            const std::shared_ptr<std::vector<std::uint8_t>>& bytes) const noexcept {
        if(!marker||closing||close_requested.load()||writes.empty())return false;
        const auto& frame=marker->frame;const auto& queued=writes.front();
        return outward_status_transport_current(frame)&&frame->present.load()&&
            frame->phase.load()==OutwardStatusFrame::Phase::Released&&frame->seal==seal&&queued.outward_status==marker&&
            !queued.held&&!queued.world_entry&&!queued.return_output&&!queued.status_seal&&!queued.initial_entry&&
            queued.reservation==frame->reservation&&!queued.reservation.owner_before(frame->reservation)&&
            !frame->reservation.owner_before(queued.reservation)&&
            queued.bytes.get()==bytes.get()&&!queued.bytes.owner_before(bytes)&&!bytes.owner_before(queued.bytes)&&
            frame->frame.get()==bytes.get()&&!frame->frame.owner_before(bytes)&&!bytes.owner_before(frame->frame);
    }
    void retire_outward_status_writes() noexcept {
        for(const auto& queued:writes)if(queued.outward_status)queued.outward_status->frame->revoke();
    }
    void retire_initial_status_writes() noexcept {
        for(const auto& queued:writes)if(queued.initial_entry&&queued.initial_entry->member->identity->status)
            queued.initial_entry->member->identity->revoke();
    }
    // Network strand only; set by the exact marked Write's success completion,
    // then captured as immutable owned data into the account selection game job.
    std::shared_ptr<const Session::RecoveredServerAdvertisement> written_advertisement;
    Session::NativeCharacterList active_native_list; // Strand; exact once completion correlation.
    std::size_t write_bytes = 0;
    std::shared_ptr<Budget> budget = std::make_shared<Budget>();
    std::atomic<bool> close_requested{false};
    std::atomic<bool> auth_requested{false};
    bool started = false;
    bool closing = false;
    bool finished = false;
    bool game_busy = false;
    enum class NativeLogoutPhase {None,Draining,Cleaning,AckQueued,Failed};
    NativeLogoutPhase native_logout_phase=NativeLogoutPhase::None; // NET only; no new input authority.
    std::uint8_t native_logout_reason=0;
    std::shared_ptr<std::vector<std::uint8_t>> native_logout_ack; // Exact private terminal Write only.
    bool disconnect_cleanup_started=false,disconnect_completion_posted=false; // NET only.
    std::atomic<bool> disconnect_cleanup_done{false},disconnect_cleanup_clean{false};
    std::atomic<bool> native_logout_terminal{false}; // GAME-visible retirement, distinct from external stop.
    bool native_battle_read_paused=false; // Network strand only; separate hold.
    bool native_pk_read_paused=false;
    asio::cancellation_signal native_pk_read_cancel;
    bool native_pk_cancel_read=false; // Strand; acknowledgement precedes Held.
    bool native_pk_terminal_cancel_read=false;
    bool read_inflight=false; // Passive read ownership; avoids duplicate resume.
    bool resume_after_login_write = false;

    Impl(Session& owner_, asio::ip::tcp::socket socket_, asio::any_io_executor game_,
         std::uint64_t id_, bool dump_, PacketHandler packet_, DisconnectHandler disconnect_,ProtocolMode mode_,
         RecoveredLoginHandler login_,RecoveredCharacterHandlers characters_,std::vector<std::uint8_t> routes_,
         DisconnectCompletion disconnect_complete_)
        : owner(owner_), socket(std::move(socket_)), strand(asio::make_strand(socket.get_executor())),
          game(std::move(game_)), timer(strand), hold_timer(strand), native_pk_timer(strand), native_pk_terminal_timer(strand), game_work(asio::make_work_guard(game)),
          network_work(asio::make_work_guard(socket.get_executor())),
          id(id_), packet_dump(dump_), mode(mode_), on_packet(std::move(packet_)),
          on_disconnect(std::move(disconnect_)), disconnect_complete(std::move(disconnect_complete_)),
          recovered_login(std::move(login_)),character_handlers(std::move(characters_)),character_routes(std::move(routes_)) {
        if(recovered_login && mode!=ProtocolMode::God2LegacyCharacterListCandidate && mode!=ProtocolMode::God2CharacterConnection)
            throw std::invalid_argument("Recovered authentication requires candidate mode");
        if((character_handlers.native_list || character_handlers.native_select || character_handlers.native_list_current || character_handlers.native_list_complete) &&
           (!character_handlers.native_list || !character_handlers.native_select || character_handlers.list ||
            !character_handlers.native_list_current || !character_handlers.native_list_complete ||
            character_handlers.select_created || character_handlers.select_existing || !recovered_login || !character_handlers.create))
            throw std::invalid_argument("Native character list/selection requires exclusive complete actual handlers");
        if(!character_handlers.native_list &&
           (character_handlers.list || character_handlers.create || character_handlers.select_created || character_handlers.select_existing) &&
           (!recovered_login || !character_handlers.list || !character_handlers.create || !character_handlers.select_created))
            throw std::invalid_argument("Recovered characters require authentication and complete handlers");
        if(mode==ProtocolMode::God2CharacterConnection && (!recovered_login ||
           (!character_handlers.select_existing && !character_handlers.native_select)))
            throw std::invalid_argument("Character connection requires independent authentication and selection handler");
        if(character_handlers.world_entry && mode!=ProtocolMode::God2CharacterConnection)
            throw std::invalid_argument("World entry candidate requires character connection");
        if(character_handlers.native_selection_input &&
           (mode!=ProtocolMode::God2CharacterConnection || !character_handlers.world_records ||
            (!character_handlers.common_world_lifecycle && !character_handlers.common_world_lifecycle_factory)))
            throw std::invalid_argument("Native C28 input requires explicit complete common world records");
        if(character_handlers.native_movement_response_custody &&
           (mode!=ProtocolMode::God2CharacterConnection || !has_world_handler() ||
            (!character_handlers.common_world_lifecycle && !character_handlers.common_world_lifecycle_factory)))
            throw std::invalid_argument("Movement response custody requires actual TW common world handlers");
        if(character_handlers.owned_normal_movement_response_custody &&
           (character_handlers.native_movement_response_custody || mode!=ProtocolMode::God2CharacterConnection ||
            !character_handlers.world_records || character_handlers.common_world_lifecycle ||
            character_handlers.common_world_lifecycle_factory))
            throw std::invalid_argument("Normal movement custody requires exclusive actual normal world owner");
        if(character_handlers.movement && character_handlers.world_records)
            throw std::invalid_argument("Recovered world handlers are mutually exclusive");
        if(character_handlers.owned_battle_row_preference &&
           (!character_handlers.owned_normal_movement_response_custody ||
            !character_handlers.world_entry || !character_handlers.world_ready || !character_handlers.world_records ||
            character_handlers.common_world_lifecycle || character_handlers.common_world_lifecycle_factory))
            throw std::invalid_argument("B4 preference requires the actual exclusive normal-entry owner");
        if((character_handlers.world_ready || has_world_handler()) &&
           (!character_handlers.world_entry || !character_handlers.world_ready || !has_world_handler()))
            throw std::invalid_argument("Recovered world routing requires world entry and complete handlers");
        if(const auto& lifecycle=character_handlers.common_world_lifecycle; lifecycle &&
           (mode!=ProtocolMode::God2CharacterConnection || !lifecycle->prepared ||
            bool(lifecycle->ready)==bool(lifecycle->ready_async) || bool(lifecycle->ready_async)!=bool(lifecycle->cancel) ||
            !character_handlers.world_entry || !character_handlers.world_ready || !has_world_handler()))
            throw std::invalid_argument("Common world lifecycle requires full character/world handlers");
        if(character_handlers.common_world_lifecycle_factory &&
           (character_handlers.common_world_lifecycle || mode!=ProtocolMode::God2CharacterConnection ||
            !character_handlers.world_entry || !character_handlers.world_ready || !has_world_handler()))
            throw std::invalid_argument("Common world lifecycle factory requires exclusive full character/world handlers");
        if(bool(character_handlers.common_world_cleanup_owner)!=bool(character_handlers.common_world_lifecycle_abandon) ||
           (character_handlers.common_world_cleanup_owner && !character_handlers.common_world_lifecycle_factory))
            throw std::invalid_argument("Common world cleanup owner requires the explicit lifecycle factory");
        if(character_handlers.common_world_publication_owner && !character_handlers.common_world_cleanup_owner)
            throw std::invalid_argument("Common world publication requires the game-owned lifecycle vault");
        if(character_handlers.common_world_ready_publication_owner && !character_handlers.common_world_cleanup_owner)
            throw std::invalid_argument("Ready common publication requires the actual game-owned lifecycle vault");
        if(!character_routes.empty() && (mode!=ProtocolMode::God2LegacyCharacterListCandidate ||
           (!character_handlers.list && !character_handlers.native_list)))
            throw std::invalid_argument("Character routes require authenticated login list mode");
        asio::error_code ec;
        const auto endpoint = socket.remote_endpoint(ec);
        ip = ec ? std::string("unknown") : endpoint.address().to_string();
        if(mode==ProtocolMode::God2PostServerSelect && !ec && endpoint.address().is_loopback()) {
            if(const char* flag=std::getenv("GOD2_POST6B_STRIKE_HOLD"))
                post_select_strike_hold=std::string(flag)=="1";
        }
        if(is_server_list_mode(mode) && id==1 && !ec && endpoint.address().is_loopback()) {
            if(const char* path=std::getenv("GOD2_UI_GATE_CONTROL")) hold_control=path;
        }
    }

    static std::int64_t now_ms() {
        return std::chrono::duration_cast<std::chrono::milliseconds>(
            std::chrono::system_clock::now().time_since_epoch()).count();
    }
    void hold_status() {
        if(hold_control.empty()) return;
        const bool held=timeout_policy==SessionTimeoutPolicy::UiGateHold;
        const nlohmann::json value={{"session_id",id},{"ui_gate_hold_active",held},
            {"session_timeout_policy",held?"UiGateHold":"Normal"},
            {"hold_entered_at",hold_entered_at},{"last_real_protocol_activity",last_real_protocol_activity},
            {"session_alive",!closing && socket.is_open()},{"updated_at",now_ms()}};
        auto path=hold_control;path += ".status";
        auto temp=path;temp += ".tmp";
        { std::ofstream stream(temp);stream << value.dump();if(!stream) throw std::runtime_error("hold telemetry write failed"); }
#ifdef _WIN32
        if(!MoveFileExW(temp.c_str(),path.c_str(),MOVEFILE_REPLACE_EXISTING|MOVEFILE_WRITE_THROUGH))
            throw std::runtime_error("hold telemetry replace failed");
#else
        std::filesystem::rename(temp,path);
#endif
    }
    void set_hold(bool enabled) {
        const bool held=timeout_policy==SessionTimeoutPolicy::UiGateHold;
        if(enabled==held) return;
        timeout_policy=enabled?SessionTimeoutPolicy::UiGateHold:SessionTimeoutPolicy::Normal;
        if(enabled) { hold_entered_at=now_ms();++timer_generation;timer.cancel(); }
        else if(!closing) arm_timer(idle_timeout);
        logger("session")->info("session_id={} UI_GATE_HOLD active={}",id,enabled);
    }
    void poll_hold() {
        if(hold_control.empty() || closing) return;
        bool requested=false;
        try {
            std::ifstream stream(hold_control);
            if(stream) {
                const auto request=nlohmann::json::parse(stream);
                const auto until=request.at("lease_until_ms").get<std::int64_t>();
                requested=request.at("session_id").get<std::uint64_t>()==id &&
                    request.at("hold").get<bool>() && until>now_ms() && until<=now_ms()+15000 &&
                    c2s0002_state==C2S0002State::TerminalSent;
            }
        } catch(...) { requested=false; }
        set_hold(requested);
        try { hold_status(); } catch(...) { fail("hold telemetry failure");return; }
        hold_timer.expires_after(std::chrono::milliseconds(250));
        hold_timer.async_wait([self=owner.shared_from_this()](const asio::error_code& ec) {
            if(!ec) self->impl_->poll_hold();
        });
    }

    void log_packet(const Packet& packet, const char* direction) {
        if (!packet_dump) return;
        if (auto log = logger("packet"))
            log->debug("session_id={} remote_ip={} state={} direction={} opcode={} size={} hex_dump={}",
                       id, ip, static_cast<int>(owner.state()), direction, packet.opcode,
                       packet.payload.size(),
                       packet.opcode == static_cast<std::uint16_t>(Opcode::C2S_LoginRequest)
                           ? std::string("[REDACTED LOGIN PAYLOAD]") : dump(packet.payload));
    }
    void arm_timer(std::chrono::steady_clock::duration duration) {
        if(duration==idle_timeout && post_select_strike_hold &&
           c2s0002_state==C2S0002State::PostSelectReceived) {
            ++timer_generation;
            timer.cancel();
            return;
        }
        if(duration==idle_timeout && timeout_policy==SessionTimeoutPolicy::UiGateHold) return;
        const auto generation=++timer_generation;
        timer.expires_after(duration);
        timer.async_wait([self = owner.shared_from_this(),generation](const asio::error_code& ec) {
            if (!ec && generation==self->impl_->timer_generation) self->impl_->fail("session timeout");
        });
    }
    void start() {
        if (started || closing) return;
        started = true;
        try {
            if(is_recovered(mode)) {
                if(!socket.remote_endpoint().address().is_loopback()) { fail("Recovered peer must be loopback");return; }
                const auto hello=RecoveredSeedExchange::hello();
                auto bytes=std::make_shared<std::vector<std::uint8_t>>(hello.begin(),hello.end());
                if(!terminal_write_allowed())return;
                write_bytes+=bytes->size();append_write({bytes,{}});write();
                logger("session")->debug("session_id={} GOD2_INITIAL_S2C_QUEUED length=19",id);
            } else protocol.on_session_created(owner);
            arm_timer(idle_timeout);
            poll_hold();
            read();
        } catch (const std::exception& e) { fail(e.what()); }
        catch (...) { fail("protocol creation hook failed"); }
    }
    bool native_battle_current(const std::shared_ptr<NativeBattlePending>& pending) const {
        if(!pending || !pending->delivery || native_battle_pending.load()!=pending)return false;
        const auto& delivery=*pending->delivery;
        // Pure synchronized transport identity only. Never read the game-owned
        // account_id/character_id from the network strand.
        return !close_requested.load() && owner.state()==SessionState::InBattle &&
            owner.battle_generation()==delivery.battle_generation && owner.recovered_world_ready() &&
            id==delivery.session && common_world_identity.load()==pending->common &&
            pending->common && pending->common->account==delivery.account &&
            pending->common->character==delivery.character &&
            pending->common->generation==delivery.common_generation && !common_entry_identity.load() &&
            (!pending->pk_entry || native_pk_written_transport_current(pending->pk_entry));
    }
    void complete_native_battle(const std::shared_ptr<NativeBattlePending>& pending,bool written) {
        if(!pending || native_battle_pending.load()!=pending || pending->completing.exchange(true))return;
        // The weak source is locked and released ONLY on game, including the
        // last strong reference. Network copies retain no source callback.
        try {post_status_work(game,[self=owner.shared_from_this(),pending,written] {
            auto& s=*self->impl_;
                [[maybe_unused]] const auto status_admission=self->begin_actor_status_writer();bool accepted=false;
            const auto delivery=pending->delivery;
            {
                const auto source=pending->source.lock();
                const bool actual_written=written && s.native_battle_current(pending) &&
                    self->account_id==delivery->account && self->character_id==delivery->character &&
                    self->native_battle_skill_written_.load()==delivery;
                if(source)try {
                    accepted=source->complete_native_battle_write(*self,delivery,actual_written);
                    accepted=accepted && actual_written && s.native_battle_current(pending) &&
                        self->account_id==delivery->account && self->character_id==delivery->character;
                }catch(...) {}
            }
            try {s.post_status_work(s.strand,[self,pending,accepted] {
                auto& s=*self->impl_;
                [[maybe_unused]] const auto status_admission=self->begin_actor_status_writer();
                const bool final_current=s.native_battle_current(pending);
                auto expected=pending;
                if(!s.native_battle_pending.compare_exchange_strong(expected,{}))return;
                if(pending->pk_entry)s.native_pk_timer.cancel();
                if(!accepted || !final_current || s.closing || s.close_requested.load()) {
                    s.fail("Native battle skill publication completion rejected");return;
                }
                // An older read may still be outstanding. Resume only the
                // explicit paused continuation, never create a second read.
                if(s.native_battle_read_paused && !s.game_busy && !s.read_inflight) {
                    s.native_battle_read_paused=false;s.resume_world_input(bool(s.skill_deadline));
                }
            });}catch(...) {
                if(!pending->pk_entry)throw; // Preserve legacy sender failure behavior.
                s.close_requested.store(true); // Strand deadline retires this exact pending.
            }
        });}catch(...) {
            if(!pending->pk_entry)throw;
            auto expected=pending;native_battle_pending.compare_exchange_strong(expected,{});
            native_pk_timer.cancel();fail("Native PK output completion handoff failed");
        }
    }
    void release_native_battle(const std::shared_ptr<NativeBattlePending>& pending,
        const std::shared_ptr<std::vector<std::uint8_t>>& bytes) {
        try {post_status_work(game,[self=owner.shared_from_this(),pending,bytes] {
            auto& s=*self->impl_;
                [[maybe_unused]] const auto status_admission=self->begin_actor_status_writer();bool accepted=false;
            {
                const auto source=pending->source.lock();
                const auto delivery=pending->delivery;
                if(source && s.native_battle_current(pending) &&
                   self->account_id==delivery->account && self->character_id==delivery->character)try {
                    accepted=source->before_native_battle_write(*self,delivery) &&
                        s.native_battle_current(pending) && self->account_id==delivery->account &&
                        self->character_id==delivery->character;
                }catch(...) {}
            }
            try {s.post_status_work(s.strand,[self,pending,bytes,accepted] {
                auto& s=*self->impl_;
                [[maybe_unused]] const auto status_admission=self->begin_actor_status_writer();
                if(s.native_battle_pending.load()!=pending || pending->completing.load())return;
                if(!accepted || s.closing || !s.native_battle_current(pending)) {
                    s.fail("Native battle source changed before write");return;
                }
                const auto found=std::find_if(s.writes.begin(),s.writes.end(),[&](const Write& value) {
                    return value.native_battle==pending;
                });
                if(found==s.writes.end() || !found->held || found->bytes!=bytes) {
                    s.fail("Native battle held frame identity mismatch");return;
                }
                if(pending->pk_entry && (!s.world_input.empty() || !s.world_pending_records.empty() ||
                    s.skill_deadline || s.native_skill_generation)){
                    s.fail("Native PK output acquired input before held write release");return;
                }
                found->held=false;if(found==s.writes.begin())s.write();
            });}catch(...) {
                if(!pending->pk_entry)throw;
                s.close_requested.store(true); // Keep exact pending for bounded strand retirement.
            }
        });}catch(...) {
            if(!pending->pk_entry)throw;
            auto expected=pending;native_battle_pending.compare_exchange_strong(expected,{});
            native_pk_timer.cancel();fail("Native PK output qualification handoff failed");
        }
    }
    bool native_pk_transport_current(const std::shared_ptr<NativePkEntryHold::Data>& data,bool committed)const {
        if(!data || native_pk_pending.load()!=data || close_requested.load() ||
           mode!=ProtocolMode::God2CharacterConnection || !owner.recovered_world_ready() ||
           common_world_identity.load().get()!=data->common.get() || common_entry_identity.load() ||
           normal_initialization.load()!=data->initialization.data_ ||
           !data->initialization.entry_written())return false;
        // Consume the exact prebattle sender source before commit. The held
        // bootstrap is already in FIFO; later alias writes follow it. Once
        // committed, its private battle hold owns output, not old world Current.
        if(!committed && data->initialization.qualified_scene_identity() &&
           !data->initialization.world_identity_sender_current())return false;
        if(!committed && data->original_world_identity && world_delivery_identity.load()!=data->original_world_identity)
            return false; // Qualify the actual captured WORLD namespace until PK commit.
        const auto& r=data->request;
        const auto common=common_world_identity.load();
        return common && common->account==r.account && common->character==r.character &&
            common->generation==r.common_generation &&
            (data->prebattle_phase==SessionState::CharacterSelected || data->prebattle_phase==SessionState::InWorld) &&
            owner.state()==(committed?SessionState::InBattle:data->prebattle_phase) &&
            owner.battle_generation()==r.prebattle_generation+(committed?1u:0u);
    }
    bool native_pk_written_transport_current(const std::shared_ptr<NativePkEntryHold::Data>& data)const {
        // Atomic/immutable transport material only: callable from network.
        // The old InWorld initialization-current and native_pk_pending==data
        // conditions must not qualify a post-entry battle publication.
        if(!data || !data->written_accepted.load() || native_pk_pending.load() ||
           data->phase.load()!=NativePkEntryHold::Data::Phase::Written ||
           data->session.lock().get()!=&owner || data->session_id!=id || data->game!=game || !data->battle_identity ||
           close_requested.load() || mode!=ProtocolMode::God2CharacterConnection ||
           !owner.recovered_world_ready() || common_entry_identity.load() ||
           normal_initialization.load()!=data->initialization.data_ ||
           !data->initialization.entry_written() ||
           world_delivery_identity.load()!=data->battle_identity)return false;
        const auto common=common_world_identity.load();const auto& r=data->request;
        return common && common.get()==data->common.get() &&
            common->account==r.account && common->character==r.character && common->generation==r.common_generation &&
            data->battle_identity->account==r.account && data->battle_identity->character==r.character &&
            data->battle_identity->world_generation==r.world_generation &&
            data->battle_identity->battle_generation==r.prebattle_generation+1 &&
            owner.state()==SessionState::InBattle && owner.battle_generation()==r.prebattle_generation+1;
    }
    void complete_native_pk(const std::shared_ptr<NativePkEntryHold::Data>& data,bool written) {
        if(!data || native_pk_pending.load()!=data || data->completing.exchange(true))return;
        if(!written && !data->clean_abort.load())data->phase.store(NativePkEntryHold::Data::Phase::Failed);
        try {post_status_work(game,[self=owner.shared_from_this(),data,written] {
            auto& s=*self->impl_;
                [[maybe_unused]] const auto status_admission=self->begin_actor_status_writer();bool accepted=false;
            const bool had_hold=data->held_notified.exchange(true);
            // Strong source reference and callback destruction stay on game.
            if(const auto source=data->source.lock())try {
                if(!had_hold)source->native_pk_entry_held(*self,std::nullopt);
                else {
                    const bool actual_written=written && s.native_pk_transport_current(data,true) &&
                        data->phase.load()==NativePkEntryHold::Data::Phase::Written &&
                        s.world_delivery_identity.load()==data->battle_identity &&
                        self->account_id==data->request.account && self->character_id==data->request.character;
                    accepted=source->native_pk_entry_written(*self,NativePkEntryHold(data),actual_written);
                    accepted=accepted && actual_written && s.native_pk_transport_current(data,true) &&
                        data->phase.load()==NativePkEntryHold::Data::Phase::Written &&
                        s.world_delivery_identity.load()==data->battle_identity &&
                        self->account_id==data->request.account && self->character_id==data->request.character;
                }
            }catch(...) {accepted=false;}
            // Not usable until the exact pending entry is cleared on strand.
            data->written_accepted.store(accepted);
            try {s.post_status_work(s.strand,[self,data,written,accepted] {
                auto& s=*self->impl_;
                [[maybe_unused]] const auto status_admission=self->begin_actor_status_writer();
                auto expected=data;
                if(!s.native_pk_pending.compare_exchange_strong(expected,{}))return;
                s.native_pk_timer.cancel();s.native_pk_reservation.reset();
                const bool clean=data->clean_abort.load() && !s.closing && !s.close_requested.load() &&
                    self->state()==data->prebattle_phase &&
                    self->battle_generation()==data->request.prebattle_generation;
                if(!clean && (!written || !accepted || s.closing || s.close_requested.load())) {
                    s.fail("Native PK entry completion rejected; durable recovery may be required");return;
                }
                if(s.native_pk_read_paused && !s.game_busy && !s.read_inflight) {
                    s.native_pk_read_paused=false;s.resume_world_input();
                }
            });}catch(...) {self->close();} // Strand deadline can retire a completing handoff.
        });}catch(...) {
            // Executor allocation failure cannot leave an immortal held queue.
            auto expected=data;native_pk_pending.compare_exchange_strong(expected,{});
            native_pk_reservation.reset();fail("Native PK completion handoff failed");
        }
    }
    bool native_pk_terminal_transport_current(const std::shared_ptr<NativePkTerminalBarrier::Data>& data)const {
        // Atomic/immutable only: no game-owned account/character reads here.
        return data && native_pk_terminal.load()==data && !close_requested.load() &&
            data->session.lock().get()==&owner && data->game==game && !data->source.expired() &&
            data->phase.load()!=NativePkTerminalBarrier::Data::Phase::Failed &&
            !native_battle_pending.load() && native_pk_written_transport_current(data->entry.data_) &&
            owner.native_battle_skill_written_.load()==data->final;
    }
    bool native_pk_return_transport_current(const std::shared_ptr<NativePkReturnReservation::Data>& data,
            std::size_t index) const {
        // Atomic/immutable only. Never use public game-owned account/character.
        if(!data || index>=2 || !data->installed.load() || data->game!=game ||
           data->sessions[index].lock().get()!=&owner || native_pk_return.load()!=data ||
           data->phase.load()==NativePkReturnReservation::Data::Phase::Failed || data->source.expired())return false;
        const auto terminal=data->preparations[index].data_->terminal.data_;
        return terminal && terminal->phase.load()==NativePkTerminalBarrier::Data::Phase::Ready &&
            terminal->accepted.load() && terminal->armed.load() && terminal->acknowledged.load() &&
            native_pk_terminal_transport_current(terminal);
    }
    void stage_native_pk_return(const std::shared_ptr<NativePkReturnReservation::Data>& data,
            std::size_t index,const std::shared_ptr<NativePkReturnAttempt>& attempt) {
        if(!native_pk_return_transport_current(data,index) || closing || game_busy || read_inflight ||
           !writes.empty() || write_bytes || input.size() || !world_input.empty() || !world_pending_records.empty() ||
           skill_deadline || native_skill_generation || native_pk_terminal_cancel_read || native_pk_cancel_read ||
           native_pk_output_staged || native_pk_output_reservation || native_pk_reservation ||
           common_ready_waiting.load() || common_entry_identity.load() ||
           c2s0002_state!=C2S0002State::WorldTailAccepted) {
            Session::fail_native_pk_return_reservation(data);return;
        }
        const auto cut=1u<<index;
        if((data->cuts.fetch_or(cut)|cut)!=3u || data->game_posted.exchange(true))return;
        try {post_status_work(data->game,[data,attempt] {
            if(data->thread!=std::this_thread::get_id()) {Session::fail_native_pk_return_reservation(data);return;}
            auto pending=NativePkReturnReservation::Data::Phase::Pending;
            if(!data->phase.compare_exchange_strong(pending,NativePkReturnReservation::Data::Phase::Reserved))return;
            const NativePkReturnReservation reservation(data);
            bool accepted=false;
            if(Session::native_pk_return_reservation_current(reservation))
                if(const auto source=data->source.lock())try {
                    accepted=source->native_pk_return_reserved(reservation);
                }catch(...) {}
            if(!accepted || !Session::native_pk_return_reservation_current(reservation))
                Session::fail_native_pk_return_reservation(data);
        });}catch(...) {Session::fail_native_pk_return_reservation(data);}
    }
    bool native_pk_return_consumption_transport_current(
            const std::shared_ptr<NativePkReturnConsumption::Data>& data,std::size_t index)const{
        if(!data||index>=2||data->phase.load()!=NativePkReturnConsumption::Data::Phase::Consumed||
           native_pk_return_consumption.load()!=data||data->plan->sessions[index].get()!=&owner||
           data->plan->game!=game||data->source.expired()||data->plan->records.expired()||
           close_requested.load()||mode!=ProtocolMode::God2CharacterConnection||
           !owner.recovered_world_ready()||common_entry_identity.load())return false;
        const auto output=data->output.lock();const auto prep=data->plan->preparations[index].data_;
        const auto terminal=prep->terminal.data_;const auto entry=terminal->entry.data_;
        const auto future=prep->initialization.data_;const auto common=common_world_identity.load();
        return output&&native_pk_return_output.load()==output&&
            output->phase.load()==NativePkReturnOutputHold::Data::Phase::Consumed&&
            native_pk_return.load()==data->plan->reservation.data_&&
            data->plan->reservation.data_->phase.load()==NativePkReturnReservation::Data::Phase::Consumed&&
            native_pk_terminal.load()==terminal&&terminal->phase.load()==NativePkTerminalBarrier::Data::Phase::Consumed&&
            !terminal->accepted.load()&&terminal->armed.load()&&terminal->acknowledged.load()&&
            normal_initialization.load()==future&&normal_entry.load()==future->entry&&
            future->entry==entry->initialization.data_->entry&&prep->initialization.entry_written()&&
            world_delivery_identity.load()==prep->world_identity&&common==entry->common&&common&&
            common->account==prep->world_identity->account&&common->character==prep->world_identity->character&&
            owner.state()==SessionState::InWorld&&owner.battle_generation()==future->effective_battle&&
            normal_output_sync->epoch.load()==data->new_epochs[index]&&
            !native_battle_pending.load()&&!native_pk_pending.load();
    }
    bool native_pk_return_output_transport_current(
            const std::shared_ptr<NativePkReturnOutputHold::Data>& data,std::size_t index) const {
        if(!data||index>=data->recipients.size()||!data->installed.load()||
           data->phase.load()==NativePkReturnOutputHold::Data::Phase::Failed||data->source.expired()||
           data->plan->records.expired()||data->plan->game!=game||close_requested.load()||
           native_pk_return_output.load()!=data||data->recipients[index]->session.get()!=&owner)return false;
        if(index<2)return native_pk_return_transport_current(data->plan->reservation.data_,index);
        const auto& proof=data->recipients[index]->normal;
        if(!proof)return false;
        std::lock_guard lock(proof->data_->sync->mutex);
        return normal_output_transport_current_locked(proof->data_);
    }
    void stage_native_pk_return_output(const std::shared_ptr<NativePkReturnOutputHold::Data>& data,
            std::size_t index,std::vector<std::shared_ptr<NativePkReturnOutputWrite>> markers,
            const std::shared_ptr<NativePkReturnOutputAttempt>& attempt){
        if(!native_pk_return_output_transport_current(data,index)||closing||
           mode!=ProtocolMode::God2CharacterConnection||c2s0002_state!=C2S0002State::WorldTailAccepted){
            Session::fail_native_pk_return_output(data);return;
        }
        const auto& recipient=data->recipients[index];
        // Returning barriers keep the exact full original drain. Survivors keep
        // normal input and older FIFO writes; held frames append without reorder.
        if(index<2&&(game_busy||read_inflight||!writes.empty()||write_bytes||input.size()||
           !world_input.empty()||!world_pending_records.empty()||skill_deadline||native_skill_generation||
           native_pk_terminal_cancel_read||native_pk_cancel_read||native_pk_output_staged||
           native_pk_output_reservation||native_pk_reservation||common_ready_waiting.load()||common_entry_identity.load())){
            Session::fail_native_pk_return_output(data);return;
        }
        const bool was_empty=writes.empty();
        try{
            const auto insert=[&]{
                if(markers.size()!=recipient->frames.size())throw std::logic_error("Return held marker count");
                std::size_t bytes=0;
                for(const auto& frame:recipient->frames){
                    if(frame->bytes->size()>max_buffer-bytes)throw std::length_error("Return held frame bytes");
                    bytes+=frame->bytes->size();
                }
                if(write_bytes>max_buffer||writes.size()>max_writes||bytes>max_buffer-write_bytes||
                   recipient->frames.size()>max_writes-writes.size())
                    throw std::length_error("Return held queue budget");
                for(std::size_t ordinal=0;ordinal<recipient->frames.size();++ordinal){
                    if(data->phase.load()!=NativePkReturnOutputHold::Data::Phase::Pending||
                       native_pk_return_output.load()!=data)throw std::logic_error("Return cohort retired during insertion");
                    const auto& frame=recipient->frames[ordinal];
                    auto budget=frame->budget.exchange({});
                    if(!budget||!markers[ordinal]||markers[ordinal]->cohort.owner_before(data)||
                       data.owner_before(markers[ordinal]->cohort)||markers[ordinal]->frame!=frame||
                       markers[ordinal]->recipient!=index||markers[ordinal]->ordinal!=ordinal)
                        throw std::logic_error("Return held frame marker identity");
                    if(!Session::actor_status_frame_matches(frame->status_seal,frame->bytes,owner,ordinal,*data->plan))
                        throw std::logic_error("Return held owned-status frame retired");
                    Write value{frame->bytes,std::move(budget),false,true};
                    value.status_seal=frame->status_seal;
                    value.return_output=markers[ordinal];append_write(std::move(value));write_bytes+=frame->bytes->size();
                }
            };
            if(index<2){insert();}
            else{
                // Only immutable capability/atomic identity on network; no bare IDs.
                const auto proof=recipient->normal->data_;
                std::lock_guard lock(proof->sync->mutex);
                if(!normal_output_transport_current_locked(proof))throw std::logic_error("Return survivor epoch retired");
                insert();
            }
            if(!native_pk_return_output_transport_current(data,index)||
               recipient->held.exchange(true))throw std::logic_error("Return held cut retired or repeated");
            // Prior survivor writes may proceed; a held front cannot start.
            if(was_empty&&!writes.empty())write();
            if(data->cuts.fetch_add(1)+1!=data->recipients.size()||data->game_posted.exchange(true))return;
            post_status_work(data->plan->game,[data,attempt]{
                if(data->plan->thread!=std::this_thread::get_id()){
                    Session::fail_native_pk_return_output(data);return;
                }
                auto pending=NativePkReturnOutputHold::Data::Phase::Pending;
                if(!data->phase.compare_exchange_strong(pending,NativePkReturnOutputHold::Data::Phase::Held))return;
                const NativePkReturnOutputHold token(data);bool accepted=false;
                {
                    const auto source=data->source.lock(); // weak owner locked/destroyed ONLY on game.
                    if(source&&Session::native_pk_return_output_current(token))try{
                        accepted=source->native_pk_return_output_held(token);
                        // Exactly THIS cohort may have deliberately consumed old
                        // Held authority. No unrelated Current token substitutes.
                        const auto successor=data->consumption.load();
                        accepted=accepted&&(Session::native_pk_return_output_current(token)||
                            (successor&&successor->output.lock()==data&&
                             Session::native_pk_return_consumption_current(NativePkReturnConsumption(successor))));
                    }catch(...){}
                }
                if(!accepted)Session::fail_native_pk_return_output(data);
            });
        }catch(...){Session::fail_native_pk_return_output(data);}
    }
    bool native_pk_return_publication_transport_current(
            const std::shared_ptr<NativePkReturnPublication::Data>& data,std::size_t index)const{
        if(!data||index>=data->progress.size()||data->phase.load()==NativePkReturnPublicationStatus::Failed||
           data->source.expired()||data->plan->records.expired()||data->plan->game!=game||close_requested.load())return false;
        const auto output=data->output.lock();const auto consumed=data->consumption.lock();
        if(!output||!consumed||output->publication.load()!=data||output->consumption.load()!=consumed||
           native_pk_return_output.load()!=output||output->recipients[index]->session.get()!=&owner||
           output->phase.load()!=NativePkReturnOutputHold::Data::Phase::Consumed||
           consumed->phase.load()!=NativePkReturnConsumption::Data::Phase::Consumed)return false;
        if(index<2)return native_pk_return_consumption_transport_current(consumed,index);
        const auto& proof=output->recipients[index]->normal;if(!proof)return false;
        std::lock_guard lock(proof->data_->sync->mutex);
        return normal_output_transport_current_locked(proof->data_);
    }
    void complete_native_pk_return_publication_recipient(
            const std::shared_ptr<NativePkReturnPublication::Work>& work,std::size_t index){
        const auto data=work->data;const auto output=data->output.lock();
        if(!output||!native_pk_return_publication_transport_current(data,index)||
           data->phase.load()!=NativePkReturnPublicationStatus::Released||!data->progress[index]->released.load()||
           data->progress[index]->next.load()!=output->recipients[index]->frames.size()){
            if(output)Session::fail_native_pk_return_output(output);return;
        }
        if(data->progress[index]->done.exchange(true))return;
        if(data->cuts.fetch_add(1)+1!=data->progress.size()||data->game_posted.exchange(true))return;
        try{post_status_work(data->plan->game,[data,work]{
            const NativePkReturnPublication token(data);const auto output=data->output.lock();
            if(!output||!Session::native_pk_return_publication_current(token)){
                if(output)Session::fail_native_pk_return_output(output);return;
            }
            auto released=NativePkReturnPublicationStatus::Released;
            if(!data->phase.compare_exchange_strong(released,NativePkReturnPublicationStatus::Written)){
                Session::fail_native_pk_return_output(output);return;
            }
            bool accepted=false;
            {const auto owner=data->source.lock();if(owner&&Session::native_pk_return_publication_current(token))
                try{accepted=owner->native_pk_return_publication_written(token)&&
                    Session::native_pk_return_publication_current(token);}catch(...){}}
            if(!accepted)Session::fail_native_pk_return_output(output);
        });}catch(...){Session::fail_native_pk_return_output(output);}
    }
    void release_native_pk_return_publication_recipient(
            const std::shared_ptr<NativePkReturnPublication::Work>& work,std::size_t index){
        const auto data=work->data;const auto output=data->output.lock();
        try{
            if(!output||closing||data->phase.load()!=NativePkReturnPublicationStatus::Released||
               !data->exposed.load()||!native_pk_return_publication_transport_current(data,index))
                throw std::logic_error("Return publication lost exact released source");
            const auto& recipient=output->recipients[index];std::size_t seen=0;bool ended=false;
            // Actual FIFO order, exact original frames; older survivor output stays ahead.
            for(const auto& queued:writes){
                const auto marker=queued.return_output;
                if(marker&&marker->cohort.lock()==output){
                    if(ended||seen>=recipient->frames.size()||!queued.held||marker->recipient!=index||
                       marker->ordinal!=seen||marker->frame!=recipient->frames[seen]||
                       queued.bytes!=marker->frame->bytes||queued.status_seal!=marker->frame->status_seal||
                       !Session::actor_status_frame_matches(queued.status_seal,queued.bytes,owner,seen,*output->plan))
                        throw std::logic_error("Return publication FIFO identity/status version");
                    ++seen;
                }else if(seen)ended=true;
            }
            if(seen!=recipient->frames.size()||data->progress[index]->released.exchange(true))
                throw std::logic_error("Return publication missing/repeated release");
            const bool start=!writes.empty()&&writes.front().held&&writes.front().return_output&&
                writes.front().return_output->cohort.lock()==output;
            for(auto& queued:writes)if(queued.return_output&&queued.return_output->cohort.lock()==output){
                if(!Session::actor_status_frame_matches(queued.status_seal,queued.bytes,owner,queued.return_output->ordinal,*output->plan))
                    throw std::logic_error("Return owned-status retired at unhold");
                queued.held=false;
            }
            if(recipient->frames.empty()){
                if(index<2&&(!writes.empty()||write_bytes))throw std::logic_error("Empty returner has output");
                complete_native_pk_return_publication_recipient(work,index);return;
            }
            if(start)write(work);
            else{
                const auto active=active_write_continuation.lock();
                if(active){
                    if(active->work||writes.empty()||active->frame!=writes.front().bytes)
                        throw std::logic_error("Return publication older async identity");
                    active->work=work; // Same strand; actual handler owns this holder, never queue/Impl.
                }else{
                    const auto pending=writes.empty()?nullptr:writes.front().pending_return_continuation.lock();
                    if(!pending||!writes.front().held||pending->frame!=writes.front().bytes||pending->work)
                        throw std::logic_error("Return publication lacks actual older held-task continuation");
                    pending->work=work; // Strong ownership remains ONLY in the old game/strand tasks.
                }
            }
        }catch(...){if(output)Session::fail_native_pk_return_output(output);}
    }
    bool native_pk_return_finalisation_transport_current(
            const std::shared_ptr<NativePkReturnFinalisation::Data>& data,std::size_t index)const{
        if(!data||index>=2||data->sessions[index].lock().get()!=&owner||data->game!=game||
           native_pk_return_finalisation.load()!=data||close_requested.load()||
           data->phase.load()==NativePkReturnFinalisationStatus::Failed||mode!=ProtocolMode::God2CharacterConnection||
           !owner.recovered_world_ready()||owner.state()!=SessionState::InWorld||common_entry_identity.load()||
           native_battle_pending.load()||native_pk_pending.load())return false;
        const auto prep=data->preparations[index].data_;const auto normal=prep->initialization.data_;
        return normal_initialization.load()==normal&&normal_entry.load()==normal->entry&&
            normal->entry->session.lock().get()==&owner&&normal->entry->written.load()&&!normal->entry->retired.load()&&
            world_delivery_identity.load()==prep->world_identity&&common_world_identity.load()==data->common[index]&&
            owner.battle_generation()==normal->effective_battle&&normal_output_sync->epoch.load()==data->epochs[index];
    }
    bool native_pk_return_finalisation_quiet()const{
        return !closing&&!game_busy&&!read_inflight&&writes.empty()&&!write_bytes&&input.size()==0&&
            world_input.empty()&&world_pending_records.empty()&&!skill_deadline&&!native_skill_generation&&
            !native_pk_terminal_cancel_read&&!native_pk_cancel_read&&!native_pk_output_staged&&
            !native_pk_output_reservation&&!native_pk_reservation&&!common_ready_waiting.load()&&
            !has_input_hold()&&!owned_input_retired.load();
    }
    void stage_native_pk_return_finalisation(const std::shared_ptr<NativePkReturnFinalisation::Work>& work,std::size_t index){
        const auto data=work->data;
        if(data->phase.load()!=NativePkReturnFinalisationStatus::Checking||
           !native_pk_return_finalisation_transport_current(data,index)||!native_pk_return_finalisation_quiet()){
            Session::fail_native_pk_return_finalisation(data);return;
        }
        const auto pub=data->publication.lock();
        if(!pub||pub->phase.load()!=NativePkReturnPublicationStatus::Written||
           !native_pk_return_publication_transport_current(pub,index)||data->ready[index].exchange(true)){
            Session::fail_native_pk_return_finalisation(data);return;
        }
        if(data->ready_cuts.fetch_add(1)+1!=2)return;
        try{post_status_work(data->game,[data,work]{
            if(data->thread!=std::this_thread::get_id()) {Session::fail_native_pk_return_finalisation(data);return;}
            auto checking=NativePkReturnFinalisationStatus::Checking;
            if(!data->phase.compare_exchange_strong(checking,NativePkReturnFinalisationStatus::Ready))return;
            bool accepted=false;const NativePkReturnFinalisation token(data);
            {const auto source=data->source.lock();if(source&&Session::native_pk_return_finalisation_current(token))
                try{accepted=source->native_pk_return_finalisation_ready(token);}catch(...){}}
            // Actual owner may have durably released/adopted/completed inline.
            // Old Publication/Consumption Current deliberately no longer exists.
            if(!accepted||data->phase.load()!=NativePkReturnFinalisationStatus::Returned||!data->detached.load())
                Session::fail_native_pk_return_finalisation(data);
        });}catch(...){Session::fail_native_pk_return_finalisation(data);}
    }
    void resume_native_pk_return_finalisation(const std::shared_ptr<NativePkReturnFinalisation::Work>& work,std::size_t index){
        const auto data=work->data;
        try{
            // The OTHER peer may already receive legitimate new input. Own exact
            // successor only, never whole historical peer Current after resume.
            if(data->phase.load()!=NativePkReturnFinalisationStatus::Returned||!data->detached.load()||
               !data->ready[0].load()||!data->ready[1].load()||
               !native_pk_return_finalisation_transport_current(data,index)||!native_pk_return_finalisation_quiet()||
               native_pk_terminal.load()||native_pk_return.load()||native_pk_return_output.load()||
               native_pk_return_consumption.load()||data->resume_started[index].exchange(true))
                throw std::logic_error("Return resume lost exact own adopted source");
            native_pk_read_paused=false;native_battle_read_paused=false;
            resume_world_input(); // Existing idle timer + ONE real async read, no fake cut.
            if(!read_inflight||closing||close_requested.load())throw std::logic_error("Return resume did not initiate read");
            if(data->resume_cuts.fetch_add(1)+1!=2)return;
            post_status_work(data->game,[data,work]{
                if(data->thread!=std::this_thread::get_id()||data->phase.load()!=NativePkReturnFinalisationStatus::Returned||
                   data->resume_cuts.load()!=2||!data->resume_started[0].load()||!data->resume_started[1].load()){
                    Session::fail_native_pk_return_finalisation(data);return;
                }
                // Historical REAL resume cuts. Gameplay may already change the
                // future tuple; never close it using obsolete whole Current.
                bool notified=false;{const auto source=data->source.lock();if(source)try{
                    source->native_pk_return_finalisation_returned(NativePkReturnFinalisation(data));notified=true;
                }catch(...){}}
                if(!notified){Session::fail_native_pk_return_finalisation(data);return;}
                data->returned_notified.store(true);
                for(std::size_t index=0;index<2;++index)if(const auto session=data->sessions[index].lock())try{
                    session->impl_->post_status_work(session->impl_->strand,[session,data,index]{
                        auto history=data;session->impl_->native_pk_return_finalisation_history.compare_exchange_strong(history,{});
                        const auto terminal=session->impl_->native_pk_terminal.load();
                        if(!terminal||terminal==data->preparations[index].data_->terminal.data_)
                            session->impl_->native_pk_terminal_timer.cancel(); // Never cancel a successor terminal.
                    });
                }catch(...){} // Completion already real; obsolete timer checks exact pending identity.
            });
        }catch(...){Session::fail_native_pk_return_finalisation(data);}
    }
    void retire_native_pk_terminal() {
        if(const auto pair=native_pk_return.exchange({}))Session::fail_native_pk_return_reservation(pair);
        const auto data=native_pk_terminal.exchange({});if(!data)return;
        // Only this exact returned game callback may retire its busy latch.
        if(data->ack_handoff_failed.load())game_busy=false;
        data->accepted.store(false);data->phase.store(NativePkTerminalBarrier::Data::Phase::Failed);
        native_pk_terminal_timer.cancel();
        // Only game owns the strong callback reference and its destruction.
        try {post_status_work(game,[self=owner.shared_from_this(),data] {
            if(data->failed_notified.exchange(true))return;
            if(const auto source=data->source.lock())try {
                source->native_pk_terminal_failed(*self,NativePkTerminalBarrier(data));
            }catch(...) {try {self->close();}catch(...) {self->impl_->close_requested.store(true);}}
        });}catch(...) {close_requested.store(true);}
    }
    bool terminal_write_allowed() {
        const auto data=native_pk_terminal.load();
        if(data && data->phase.load()!=NativePkTerminalBarrier::Data::Phase::Draining) {
            fail("Native PK terminal drained cut acquired new output");return false;
        }
        return true;
    }
    void stage_native_pk_terminal() {
        const auto data=native_pk_terminal.load();if(!data)return;
        if(const auto final=native_pk_return_finalisation.load();final&&
           final->phase.load()==NativePkReturnFinalisationStatus::Returned){
            const auto index=final->sessions[0].lock().get()==&owner?0u:1u;
            if(final->preparations[index].data_->terminal.data_==data&&
               native_pk_return_finalisation_transport_current(final,index))return; // ONLY input hold during retirement.
            Session::fail_native_pk_return_finalisation(final);return;
        }
        // The coupled stores intentionally retire old predicates before both
        // tuples are complete. This exact private window ONLY keeps input held.
        if(const auto switching=native_pk_return_consumption.load();
           switching&&switching->phase.load()==NativePkReturnConsumption::Data::Phase::Consuming){
            const auto index=switching->plan->sessions[0].get()==&owner?0u:1u;
            const auto output=switching->output.lock();
            const auto pair=switching->plan->reservation.data_;
            const auto term_phase=data->phase.load();
            const auto pair_phase=pair->phase.load();
            const auto output_phase=output?output->phase.load():NativePkReturnOutputHold::Data::Phase::Failed;
            if(index<2&&switching->plan->sessions[index].get()==&owner&&
               switching->plan->game==game&&data->game==game&&data->session.lock().get()==&owner&&
               switching->plan->preparations[index].data_->terminal.data_==data&&
               native_pk_return.load()==pair&&output&&native_pk_return_output.load()==output&&
               output->plan==switching->plan&&output->consumption.load()==switching&&
               (pair_phase==NativePkReturnReservation::Data::Phase::Consuming||
                pair_phase==NativePkReturnReservation::Data::Phase::Consumed)&&
               (output_phase==NativePkReturnOutputHold::Data::Phase::Consuming||
                output_phase==NativePkReturnOutputHold::Data::Phase::Consumed)&&
               (term_phase==NativePkTerminalBarrier::Data::Phase::Ready||
                term_phase==NativePkTerminalBarrier::Data::Phase::Consumed)&&
               data->armed.load()&&data->acknowledged.load()&&!close_requested.load()&&
               !switching->source.expired()&&!output->source.expired()&&!data->source.expired()&&
               !switching->plan->records.expired())return;
        }
        if(data->phase.load()==NativePkTerminalBarrier::Data::Phase::Consumed){
            const auto successor=native_pk_return_consumption.load();
            const auto index=successor&&successor->plan->sessions[0].get()==&owner?0u:1u;
            if(!native_pk_return_consumption_transport_current(successor,index)||closing)
                fail("Consumed native return lost its exact held input source");
            return; // Same original terminal slot/timer holds input; no old PK predicate.
        }
        if(!native_pk_terminal_transport_current(data) || closing) {
            fail("Native PK terminal barrier lost retained source");return;
        }
        if(!data->armed.load() || data->phase.load()==NativePkTerminalBarrier::Data::Phase::Ready)return;
        if(game_busy || !data->acknowledged.load())return; // Its exact accepted ACK must enqueue first.
        if(c2s0002_state!=C2S0002State::WorldTailAccepted || !world_input.empty() ||
           !world_pending_records.empty() || skill_deadline || native_skill_generation ||
           common_ready_waiting.load() || common_entry_identity.load()) {
            fail("Native PK terminal intersects buffered or staged input");return;
        }
        if(read_inflight) {
            if(!native_pk_terminal_cancel_read) {
                native_pk_terminal_cancel_read=true;
                native_pk_read_cancel.emit(asio::cancellation_type::terminal);
            }
            return;
        }
        if(!writes.empty() || write_bytes)return; // Real full-write drain hook retries.
        auto draining=NativePkTerminalBarrier::Data::Phase::Draining;
        if(!data->phase.compare_exchange_strong(draining,NativePkTerminalBarrier::Data::Phase::Ready))return;
        try {post_status_work(game,[self=owner.shared_from_this(),data] {
            if(data->ready_notified.exchange(true))return;
            bool accepted=false;
            if(self->native_pk_terminal_barrier_ready_current(NativePkTerminalBarrier(data)))
                if(const auto source=data->source.lock())try {
                    accepted=source->native_pk_terminal_ready(*self,NativePkTerminalBarrier(data));
                }catch(...) {}
            if(!accepted || !self->native_pk_terminal_barrier_ready_current(NativePkTerminalBarrier(data))) {
                data->phase.store(NativePkTerminalBarrier::Data::Phase::Failed);
                data->accepted.store(false);
                try {self->close();}catch(...) {self->impl_->close_requested.store(true);}
                return;
            }
            data->accepted.store(true); // Deadline intentionally remains armed.
            bool notified=false;
            if(self->native_pk_terminal_barrier_accepted_current(NativePkTerminalBarrier(data)))
                if(const auto source=data->source.lock())try {
                    notified=source->native_pk_terminal_accepted(*self,NativePkTerminalBarrier(data));
                }catch(...) {}
            if(!notified || !self->native_pk_terminal_barrier_accepted_current(NativePkTerminalBarrier(data))) {
                data->accepted.store(false);data->phase.store(NativePkTerminalBarrier::Data::Phase::Failed);
                try {self->close();}catch(...) {self->impl_->close_requested.store(true);}
            }
        });}catch(...) {fail("Native PK terminal ready handoff failed");}
    }
    void stage_native_pk() {
        [[maybe_unused]] const auto status_admission=owner.begin_actor_status_writer();
        const auto data=native_pk_pending.load();
        if(!data || data->completing.load() || data->phase.load()!=NativePkEntryHold::Data::Phase::Preparing)return;
        if(closing || !native_pk_transport_current(data,false) || data->source.expired()) {
            fail("Native PK preparation lost exact world source");return;
        }
        if(game_busy)return; // Actual callback ACK must enqueue its reply first.
        if(!world_input.empty() || !world_pending_records.empty() || skill_deadline || native_skill_generation) {
            fail("Native PK entry intersects buffered or staged world input");return;
        }
        if(read_inflight) {
            if(!native_pk_cancel_read) {
                native_pk_cancel_read=true;
                native_pk_read_cancel.emit(asio::cancellation_type::terminal);
            }
            return;
        }
        if(!native_pk_reservation)return; // Initial strand reservation job not received yet.
        try {
            if(data->frame->size()>max_buffer-write_bytes || writes.size()>=max_writes)
                throw std::length_error("Native PK held queue limit");
            Write held{data->frame,std::move(native_pk_reservation),false,true};held.native_pk=data;
            if(!terminal_write_allowed())return;
            append_write(std::move(held));write_bytes+=data->frame->size();
            auto preparing=NativePkEntryHold::Data::Phase::Preparing;
            if(!data->phase.compare_exchange_strong(preparing,NativePkEntryHold::Data::Phase::Held)) {
                write_bytes-=data->frame->size();writes.pop_back();return;
            }
            post_status_work(game,[self=owner.shared_from_this(),data] {
                if(data->completing.load())return;
                if(!self->native_pk_entry_current(NativePkEntryHold(data))) {
                    self->close();return;
                }
                if(data->held_notified.exchange(true))return;
                if(const auto source=data->source.lock())try {
                    source->native_pk_entry_held(*self,NativePkEntryHold(data));
                }catch(...) {self->close();}
                else self->close();
            });
        }catch(...) {fail("Native PK hold allocation or game handoff failed");}
    }
    void stage_native_pk_output(){
        const auto pending=native_pk_output_staged;
        if(!pending || native_battle_pending.load()!=pending || pending->completing.load())return;
        if(game_busy)return; // Actual ordinary response ACK must enqueue first.
        if(!native_battle_current(pending) || closing || !native_pk_output_reservation ||
           c2s0002_state!=C2S0002State::WorldTailAccepted || !world_input.empty() ||
           !world_pending_records.empty() || skill_deadline || native_skill_generation){
            fail("Stale staged native PK output or incomplete input prefix");return;
        }
        try{
            auto bytes=std::make_shared<std::vector<std::uint8_t>>(RecoveredWorldFrame::encode(pending->delivery->logical));
            if(bytes->size()>max_buffer-write_bytes || writes.size()>=max_writes){
                fail("Native PK output queue limit");return;
            }
            if(!terminal_write_allowed())return;
            append_write({bytes,std::move(native_pk_output_reservation),false,true,{},{},pending});
            write_bytes+=bytes->size();native_pk_output_staged.reset();
            release_native_battle(pending,bytes);
        }catch(...){fail("Native PK output staged encoding or handoff failed");}
    }
    void read() {
        if(native_logout_phase!=NativeLogoutPhase::None){
            if(native_logout_phase==NativeLogoutPhase::Draining)post_status_work(strand,[self=owner.shared_from_this()]{self->impl_->advance_native_logout();});
            return;
        }
        if(owned_input_paused())return;
        if(const auto final=native_pk_return_finalisation.load();final&&
           final->phase.load()==NativePkReturnFinalisationStatus::Returned){
            const auto index=final->sessions[0].lock().get()==&owner?0u:1u;
            if(!final->resume_started[index].load())return;
        }
        if(native_pk_terminal.load()) {stage_native_pk_terminal();return;}
        if(native_pk_pending.load()) {native_pk_read_paused=true;stage_native_pk();return;}
        if(native_battle_pending.load()) {native_battle_read_paused=true;stage_native_pk_output();return;}
        if (closing || game_busy) return;
        native_battle_read_paused=false;
        read_inflight=true;
        socket.async_read_some(asio::buffer(read_bytes), asio::bind_cancellation_slot(native_pk_read_cancel.slot(),asio::bind_executor(strand,
            [self = owner.shared_from_this()](const asio::error_code& ec, std::size_t size) {
                auto& s = *self->impl_;
                [[maybe_unused]] const auto status_admission=self->begin_actor_status_writer();
                s.read_inflight=false;
                if(s.native_pk_terminal_cancel_read) {
                    s.native_pk_terminal_cancel_read=false;
                    if(ec==asio::error::operation_aborted && size==0 && !s.closing && s.native_pk_terminal.load()) {
                        s.stage_native_pk_terminal();return;
                    }
                    s.fail("Native PK terminal read cancellation was ambiguous");return;
                }
                if(s.native_pk_terminal.load()) {
                    s.fail("Native PK terminal received ambiguous in-flight bytes");return;
                }
                if(s.native_pk_cancel_read) {
                    s.native_pk_cancel_read=false;
                    if(ec==asio::error::operation_aborted && size==0 && !s.closing) {
                        if(s.native_pk_pending.load())s.stage_native_pk();
                        else if(!s.game_busy)s.resume_world_input();
                        return;
                    }
                }
                if(s.native_pk_pending.load()) {
                    s.fail("Native PK barrier received ambiguous in-flight world bytes");return;
                }
                if(!ec && size>0) s.last_real_protocol_activity=now_ms();
                if (s.closing) return;
                if (ec) { s.fail(ec.message()); return; }
                try {
                    if(is_recovered(s.mode)) {
                        if(is_post_select_mode(s.mode) &&
                           s.c2s0002_state==C2S0002State::TerminalSent) {
                            if(size>6-s.post_select_input.size()) { s.fail("Post-selection unexpected data or length");return; }
                            s.post_select_input.insert(s.post_select_input.end(),s.read_bytes.begin(),s.read_bytes.begin()+size);
                            if(s.post_select_input.size()==6) {
                                const auto selection=s.character_handlers.native_list?
                                    ParseNativePostServerSelectRequest(s.post_select_input):ParsePostServerSelectRequest(s.post_select_input);
                                if(!selection) { s.fail("Post-selection contract rejected");return; }
                                s.c2s0002_state=C2S0002State::PostSelectReceived;
                                s.set_hold(false);
                                s.post_select_input.clear();
                                if(s.post_select_strike_hold)
                                    logger("session")->info("session_id={} POST6B_STRIKE_IDLE_TIMEOUT_SUSPENDED",s.id);
                                if(s.mode==ProtocolMode::God2LegacyCharacterListCandidate) {
                                    if(s.character_handlers.list || s.character_handlers.native_list) {
                                        logger("session")->info("session_id={} POST_SERVER_SELECT_C2S_ACCEPTED length=6; requesting account-owned character list",s.id);
                                        s.character_operation(std::nullopt,selection,s.written_advertisement);return;
                                    }
                                    const auto candidate=LegacyCharacterListCandidate::wire();
                                    auto bytes=std::make_shared<std::vector<std::uint8_t>>(candidate.begin(),candidate.end());
                                    if(!s.terminal_write_allowed())return;
                                    s.write_bytes+=bytes->size();s.append_write({bytes,{}});
                                    if(s.writes.size()==1) s.write();
                                    logger("session")->info("session_id={} POST_SERVER_SELECT_C2S_ACCEPTED length=6; legacy character-list candidate queued; current client acceptance UNKNOWN",s.id);
                                } else {
                                    logger("session")->info("session_id={} POST_SERVER_SELECT_C2S_ACCEPTED length=6; next direction unknown; no response sent",s.id);
                                }
                            }
                            s.arm_timer(idle_timeout);s.read();return;
                        }
                        if((is_post_select_mode(s.mode) && s.c2s0002_state==C2S0002State::PostSelectReceived) ||
                           s.c2s0002_state==C2S0002State::CharacterReady) {
                            if(!s.character_routes.empty()) {
                                s.fail("Character operation requires advertised independent connection");return;
                            }
                            if(s.mode==ProtocolMode::God2CharacterConnection) {
                                auto& input=s.character_create_input;
                                if(size>256-input.size()) { s.fail("Character preselection input limit");return; }
                                input.insert(input.end(),s.read_bytes.begin(),s.read_bytes.begin()+size);
                                if(s.packet_dump)
                                    logger("session")->debug("session_id={} CHARACTER_C2S_PROBE chunk={} assembled={} first_four={}",
                                        s.id,size,input.size(),dump(std::span<const std::uint8_t>(input).first(std::min<std::size_t>(input.size(),4))));
                                std::optional<std::uint8_t> selected_token;
                                std::optional<RecoveredPostCreateSelect::Selection> selected_input;
                                std::optional<RecoveredCharacterCreate> created_request;
                                std::optional<RecoveredCharacterDelete> deleted_request;
                                std::size_t at=0;
                                while(input.size()-at>=2) {
                                    const auto length=static_cast<std::size_t>(input[at])+256u*input[at+1];
                                    if(length!=5 && length!=41 && length!=RecoveredCharacterCreate::wire_size &&
                                       length!=RecoveredCharacterDelete::wire_size) {
                                        s.fail("Post-selection next C2S contract unknown");return;
                                    }
                                    if(input.size()-at<length) break;
                                    const auto frame=std::span<const std::uint8_t>(input).subspan(at,length);
                                    if(length==5) {
                                        const auto logical=RecoveredWorldFrame::decode(frame);
                                        // Native delete success405A67 sends02/04;
                                        // menu/back and creation use02/00. Both
                                        // block in415180 until opcode03 arrives.
                                        if(logical && logical->size()==2 && (*logical)[0]==2 &&
                                           ((*logical)[1]==0 || (*logical)[1]==4) &&
                                           !selected_token && !created_request && !deleted_request &&
                                           at+length==input.size()) {
                                            auto reply=std::make_shared<std::vector<std::uint8_t>>(
                                                RecoveredWorldFrame::encode(std::array<std::uint8_t,3>{3,0,0}));
                                            if(!s.terminal_write_allowed())return;
                                            s.write_bytes+=reply->size();s.append_write({reply,{}});
                                            if(s.writes.size()==1)s.write();
                                            logger("session")->info("session_id={} CHARACTER_TERMINAL_ACK_QUEUED reason={}",s.id,(*logical)[1]);
                                            s.close();return;
                                        }
                                        if(!logical || logical->size()!=2 || (*logical)[0]!=0x30 || (*logical)[1]!=0) {
                                            s.fail("Character idle tick rejected");return;
                                        }
                                        if(s.packet_dump)
                                            logger("session")->debug("session_id={} CHARACTER_IDLE_TICK_ACCEPTED",s.id);
                                    } else if(length==RecoveredCharacterDelete::wire_size) {
                                        if(selected_token || created_request || deleted_request) { s.fail("Multiple character actions");return; }
                                        deleted_request=RecoveredCharacterDelete::parse(frame);
                                        if(!deleted_request) { s.fail("Character-delete contract rejected");return; }
                                    } else if(length==41) {
                                        if(selected_token || created_request || deleted_request) { s.fail("Multiple character actions");return; }
                                        selected_input=RecoveredPostCreateSelect::selection_from_frame(frame);
                                        if(selected_input)selected_token=selected_input->token();
                                        if(!selected_token) { s.fail("Existing selection contract rejected");return; }
                                    } else {
                                        if(selected_token || created_request || deleted_request) { s.fail("Multiple character actions");return; }
                                        created_request=RecoveredCharacterCreate::parse(frame);
                                        if(!created_request || !created_request->name_bytes()) {
                                            s.fail("Character-create contract rejected");return;
                                        }
                                    }
                                    at+=length;
                                }
                                if(at!=input.size()) { s.arm_timer(idle_timeout);s.read();return; }
                                input.clear();
                                if(deleted_request) { s.delete_character(*deleted_request);return; }
                                if(selected_token) { s.select_character(*selected_token,false,std::move(selected_input));return; }
                                if(created_request) {
                                    s.c2s0002_state=C2S0002State::CharacterCreateReceived;
                                    s.native_create_refresh=created_request->opcode==0x17;
                                    if(s.character_handlers.create) {
                                        logger("session")->info("session_id={} CHARACTER_CREATE_FRAME_VALID length=48 opcode={}; fields=REDACTED; committing profile",s.id,created_request->opcode);
                                        s.character_operation(*created_request);return;
                                    }
                                    logger("session")->info("session_id={} CHARACTER_CREATE_FRAME_VALID length=48 opcode={}; fields=REDACTED; creation not committed; response not implemented",s.id,created_request->opcode);
                                }
                                s.arm_timer(idle_timeout);s.read();return;
                            }
                            if(s.mode==ProtocolMode::God2LegacyCharacterListCandidate) {
                                if(size>RecoveredCharacterCreate::wire_size-s.character_create_input.size()) {
                                    s.fail("Character-create unexpected data or length");return;
                                }
                                auto& input=s.character_create_input;
                                input.insert(input.end(),s.read_bytes.begin(),s.read_bytes.begin()+size);
                                if(input.size()>=2 && (input[0]!=48 || input[1]!=0)) {
                                    s.fail("Post-selection next C2S contract unknown");return;
                                }
                                if(input.size()==RecoveredCharacterCreate::wire_size) {
                                    const auto parsed=RecoveredCharacterCreate::parse(input);
                                    if(!parsed) {
                                        s.fail("Character-create contract rejected");return;
                                    }
                                    if(!parsed->name_bytes()) {
                                        s.fail("Character-create name rejected");return;
                                    }
                                    s.c2s0002_state=C2S0002State::CharacterCreateReceived;
                                    s.native_create_refresh=parsed->opcode==0x17;
                                    if(s.character_handlers.create) {
                                        logger("session")->info("session_id={} CHARACTER_CREATE_FRAME_VALID length=48 opcode={}; fields=REDACTED; committing profile",s.id,parsed->opcode);
                                        s.character_operation(*parsed);return;
                                    }
                                    logger("session")->info("session_id={} CHARACTER_CREATE_FRAME_VALID length=48 opcode={}; fields=REDACTED; creation not committed; response not implemented",s.id,parsed->opcode);
                                }
                                s.arm_timer(idle_timeout);s.read();return;
                            }
                            s.fail("Post-selection next C2S contract unknown");return;
                        }
                        if(s.c2s0002_state==C2S0002State::CharacterCreateReceived) {
                            s.fail("Character-create result contract not implemented");return;
                        }
                        if(s.c2s0002_state==C2S0002State::CharacterCreateCommitted) {
                            auto& input=s.post_create_input;
                            if(s.native_create_refresh) {
                                if(size>5-input.size()) { s.fail("Native creation refresh length rejected");return; }
                                input.insert(input.end(),s.read_bytes.begin(),s.read_bytes.begin()+size);
                                if(input.size()<5) { s.arm_timer(idle_timeout);s.read();return; }
                                const auto decoded=RecoveredPostCreateSelect::decode<5>(input);
                                if(s.native_create_ack_sent) {
                                    if(!decoded || (*decoded)[0]!=2 || (*decoded)[1]!=0) {
                                        s.fail("Native creation refresh disconnect rejected");return;
                                    }
                                    // Success C064 ->15730(2,0,1) waits15180 for03.
                                    // Length table requires3 logical bytes; trailing bytes unread here.
                                    auto bytes=std::make_shared<std::vector<std::uint8_t>>(
                                        RecoveredWorldFrame::encode(std::array<std::uint8_t,3>{3,0,0}));
                                    if(!s.terminal_write_allowed())return;
                                    s.write_bytes+=bytes->size();s.append_write({bytes,{}});
                                    if(s.writes.size()==1) s.write();
                                    s.close();return;
                                }
                                if(!decoded || (*decoded)[0]!=0x18 || !s.character_handlers.created_slot) {
                                    s.fail("Native creation refresh request rejected");return;
                                }
                                s.acknowledge_created_slot();return;
                            }
                            if(size>RecoveredPostCreateSelect::wire_size-input.size()) {
                                s.fail("Post-create selection length rejected");return;
                            }
                            input.insert(input.end(),s.read_bytes.begin(),s.read_bytes.begin()+size);
                            if((input.size()>=2 && (input[0]!=5 || input[1]!=0)) ||
                               (input.size()>=5 && !RecoveredPostCreateSelect::valid_prefix(input)) ||
                               (input.size()>=7 && (input[5]!=41 || input[6]!=0))) {
                                s.fail("Post-create selection prefix rejected");return;
                            }
                            if(input.size()==RecoveredPostCreateSelect::wire_size) {
                                const auto request=RecoveredPostCreateSelect::parse(input);
                                if(!request) { s.fail("Post-create selection contract rejected");return; }
                                s.select_character(request->selection_token,true,request->native_selection);return;
                            }
                            s.arm_timer(idle_timeout);s.read();return;
                        }
                        if(s.c2s0002_state==C2S0002State::WorldEntrySent) {
                            if(s.has_world_handler()) {
                                // The tail is at most 23 bytes; stop at its exact boundary
                                // so TCP coalescing cannot consume the first world frame.
                                for(std::size_t at=0;at<size;++at) {
                                    s.observe_normal_tail(std::span<const std::uint8_t>(s.read_bytes.data()+at,1));
                                    const auto result=s.world_ready->feed(std::span<const std::uint8_t>(s.read_bytes.data()+at,1));
                                    if(result==RecoveredWorldReady::Result::Rejected) {
                                        s.fail("World initialization tail contract rejected");return;
                                    }
                                    if(result==RecoveredWorldReady::Result::Complete) {
                                        s.world_input.assign(s.read_bytes.begin()+static_cast<std::ptrdiff_t>(at+1),
                                            s.read_bytes.begin()+static_cast<std::ptrdiff_t>(size));
                                        s.accept_world_tail();return;
                                    }
                                }
                                s.arm_timer(idle_timeout);s.read();return;
                            }
                            s.observe_normal_tail(std::span<const std::uint8_t>(s.read_bytes.data(),size));
                            const auto result=s.world_ready->feed(std::span<const std::uint8_t>(s.read_bytes.data(),size));
                            if(result==RecoveredWorldReady::Result::Rejected) {
                                s.fail("World initialization tail contract rejected");return;
                            }
                            if(result==RecoveredWorldReady::Result::Complete) {
                                s.accept_world_tail();return;
                            }
                            s.arm_timer(idle_timeout);s.read();return;
                        }
                        if(s.c2s0002_state==C2S0002State::WorldTailAccepted) {
                            if(!s.has_world_handler()) {
                                s.fail("Post-initializer world contract not implemented");return;
                            }
                            s.feed_world(std::span<const std::uint8_t>(s.read_bytes.data(),size));return;
                        }
                        if(s.c2s0002_state==C2S0002State::CharacterSelected) {
                            s.fail("Selected character next world contract not implemented");return;
                        }
                        if(is_credential_mode(s.mode) && s.c2s0002_state!=C2S0002State::AwaitSeed) {
                            if(s.c2s0002_state!=C2S0002State::AwaitRequest || size>176-s.c2s0002_input.size()) {
                                s.fail("C2S0002 unexpected data or length");return;
                            }
                            s.c2s0002_input.insert(s.c2s0002_input.end(),s.read_bytes.begin(),s.read_bytes.begin()+size);
                            if(s.c2s0002_input.size()>=2 && (s.c2s0002_input[0]!=176 || s.c2s0002_input[1]!=0)) {
                                s.fail("C2S0002 invalid header");return;
                            }
                            if(s.c2s0002_input.size()==176) {
                                const auto parsed=RecoveredC2S0002::parse(s.c2s0002_input,
                                    s.mode==ProtocolMode::God2CharacterConnection?0:4);
                                if(!parsed) { s.fail("C2S0002 contract rejected");return; }
                                std::vector<std::uint8_t> response;
                                if(s.mode==ProtocolMode::God2CharacterConnection) {
                                    const auto bootstrap=RecoveredCharacterBootstrap::candidate();
                                    response.assign(bootstrap.begin(),bootstrap.end());
                                } else {
                                    const auto login=RecoveredC2S0002::response(*parsed);
                                    if(!login) { s.fail("S2C0003 unsupported flag branch");return; }
                                    response.assign(login->begin(),login->end());
                                }
                                s.c2s0002_state=C2S0002State::RequestReceived;
                                logger("session")->info("session_id={} C2S0002_ACCEPTED length=176 opcode={} credentials=REDACTED",s.id,parsed->logical[0]);
                                if(s.recovered_login) {
                                    s.authenticate_recovered(*parsed,std::move(response));return;
                                }
                                s.send_recovered_login(response);
                            }
                            s.arm_timer(idle_timeout);s.read();return;
                        }
                        if(size>RecoveredSeedExchange::response.size()-s.recovered_input.size()) {
                            s.fail("Recovered next transition is not implemented");return;
                        }
                        s.recovered_input.insert(s.recovered_input.end(),s.read_bytes.begin(),s.read_bytes.begin()+size);
                        if(s.recovered_input.size()==RecoveredSeedExchange::response.size()) {
                            if(!RecoveredSeedExchange::accepts(s.recovered_input)) { s.fail("Recovered seed proof rejected");return; }
                            s.owner.set_state(SessionState::Handshaked);
                            logger("session")->info("session_id={} GOD2_SEED_EXCHANGE_ACCEPTED; awaiting next recovered S2C contract",s.id);
                            if(s.mode==ProtocolMode::God2PostSeed || is_credential_mode(s.mode)) {
                                if(is_credential_mode(s.mode)) s.c2s0002_state=C2S0002State::AwaitRequest;
                                s.post_seed_state=RecoveredPostSeed::State::SeedAccepted;
                                const auto frame=RecoveredPostSeed::frame(s.mode==ProtocolMode::God2CharacterConnection?0xf6:0x53);
                                auto bytes=std::make_shared<std::vector<std::uint8_t>>(frame.begin(),frame.end());
                                if(!s.terminal_write_allowed())return;
                                s.write_bytes+=bytes->size();s.append_write({bytes,{}});
                                if(s.writes.size()==1) s.write();
                            }
                        }
                        s.arm_timer(idle_timeout);s.read();return;
                    }
                    if (size > max_buffer - s.input.size()) { s.fail("read buffer limit"); return; }
                    s.input.append(std::span<const std::uint8_t>(s.read_bytes.data(), size));
                    std::vector<Packet> packets;
                    auto result = s.protocol.try_decode(s.input, packets);
                    if (!result.ok) { s.fail(result.error); return; }
                    std::size_t bytes = 0;
                    for (const auto& packet : packets) {
                        if (packet.payload.size() > max_buffer - bytes) {
                            s.fail("decoded packet byte limit"); return;
                        }
                        bytes += packet.payload.size();
                    }
                    if (packets.size() > max_batch) { s.fail("decoded packet count limit"); return; }
                    s.arm_timer(idle_timeout);
                    if (packets.empty()) s.read();
                    else s.deliver(std::move(packets));
                } catch (const std::exception& e) { s.fail(e.what()); }
                catch (...) { s.fail("protocol decode failed"); }
            })));
    }
    void send_recovered_login(std::span<const std::uint8_t> response) {
        auto bytes=std::make_shared<std::vector<std::uint8_t>>(response.begin(),response.end());
        if(!terminal_write_allowed())return;
        write_bytes+=bytes->size();append_write({bytes,{}});
        if(is_server_list_mode(mode)) {
            const auto entry=RecoveredServerList::one_entry();
            auto next=character_routes.empty()
                ?std::make_shared<std::vector<std::uint8_t>>(entry.begin(),entry.end())
                :std::make_shared<std::vector<std::uint8_t>>(character_routes);
            std::shared_ptr<const Session::RecoveredServerAdvertisement> observation;
            if(character_handlers.native_list)observation=std::make_shared<const Session::RecoveredServerAdvertisement>(
                Session::RecoveredServerAdvertisement{id,character_routes.empty()?
                    Session::RecoveredServerAdvertisement::Origin::LegacyListCandidate:
                    Session::RecoveredServerAdvertisement::Origin::LoopbackRoutesCandidate,*next});
            if(!terminal_write_allowed())return;
            write_bytes+=next->size();append_write({next,{},false,false,std::move(observation)});
        }
        if(is_terminal_mode(mode)) {
            const auto terminal=RecoveredLoginTerminal::success();
            auto next=std::make_shared<std::vector<std::uint8_t>>(terminal.begin(),terminal.end());
            if(!terminal_write_allowed())return;
            write_bytes+=next->size();append_write({next,{}});
        }
        if(writes.front().bytes==bytes) write();
    }
    void authenticate_recovered(RecoveredC2S0002::Parsed request,std::vector<std::uint8_t> response) {
        game_busy=true;
        // Suspend reads until the game-owned account repository has completed.
        // The same acknowledgement discipline as deliver() gates disconnect.
        post_status_work(game,[self=owner.shared_from_this(),request=std::move(request),response]() mutable {
            auto& s=*self->impl_;
                [[maybe_unused]] const auto status_admission=self->begin_actor_status_writer();
            auto complete=retain_actor_status_writer(s.owner.begin_actor_status_writer(),
                [self,response,request](std::uint64_t account,std::exception_ptr error) {
                auto& s=*self->impl_;
                [[maybe_unused]] const auto status_admission=self->begin_actor_status_writer();
                if(error) logger("session")->error("session_id={} AUTHENTICATION_SERVICE_ERROR",s.id);
                if(account && !s.close_requested.load()) {
                    s.retire_normal_output();
                    self->account_id=account;
                }
                if(s.character_handlers.native_select && account && !error && !s.close_requested.load()) {
                    // Observational allocation failure must never rewrite the
                    // frozen login outcome. Missing observation rejects only
                    // the explicitly selected native handoff downstream.
                    try {
                        auto value=std::make_shared<const NativeAuthenticatedInput>(
                            NativeAuthenticatedInput{s.id,account,s.mode,request});
                        std::shared_ptr<const NativeAuthenticatedInput> empty;
                        self->recovered_native_authenticated_input_.compare_exchange_strong(empty,std::move(value));
                    } catch(...) {}
                }
                s.post_status_work(s.strand,[self,account,response,error] {
                auto& s=*self->impl_;
                [[maybe_unused]] const auto status_admission=self->begin_actor_status_writer();
                s.game_busy=false;
                if(s.closing) { s.finish();return; }
                if(s.close_requested.load()) { s.close();return; }
                if(!account) {
                    if(s.mode==ProtocolMode::God2CharacterConnection) {
                        s.fail("Recovered character authentication rejected");return;
                    }
                    const auto frame=error ? RecoveredLoginFailure::server_error() : RecoveredLoginFailure::password_mismatch();
                    auto bytes=std::make_shared<std::vector<std::uint8_t>>(frame.begin(),frame.end());
                    if(!s.terminal_write_allowed())return;
                    s.write_bytes+=bytes->size();s.append_write({bytes,{}});
                    logger("session")->info("session_id={} LOGIN_REJECTION_QUEUED opcode=30 result={} bytes=5",s.id,error?255:3);
                    if(s.writes.size()==1) s.write();
                    s.close();
                    return;
                }
                try {
                    self->set_state(SessionState::Authenticated);
                    if(s.mode==ProtocolMode::God2CharacterConnection)
                        s.c2s0002_state=C2S0002State::CharacterReady;
                    logger("session")->info("session_id={} RECOVERED_ACCOUNT_BOUND account_id={}; original-client acceptance unconfirmed",s.id,account);
                    // The peer can receive the last login bytes before this
                    // strand runs their write completion. Keep reads suspended
                    // until that completion advances TerminalSent; otherwise
                    // a valid immediate6B is parsed as another credential.
                    s.resume_after_login_write=true;
                    s.send_recovered_login(response);
                    s.arm_timer(idle_timeout);
                } catch(...) { s.fail("Recovered login response failed"); }
                });
            });
            try {
                if(s.close_requested.load()) complete(std::uint64_t{0},std::exception_ptr{});
                else if(s.character_handlers.authenticate_async)
                    s.character_handlers.authenticate_async(request,complete);
                else complete(s.recovered_login(request),std::exception_ptr{});
            } catch(...) { complete(0,std::current_exception()); }
        });
    }
    void character_operation(std::optional<RecoveredCharacterCreate> request=std::nullopt,
                             std::optional<RecoveredPostServerSelect> selection=std::nullopt,
                             std::shared_ptr<const Session::RecoveredServerAdvertisement> advertisement={}) {
        game_busy=true;
        post_status_work(game,[self=owner.shared_from_this(),request,selection,advertisement=std::move(advertisement)] {
            auto& s=*self->impl_;
                [[maybe_unused]] const auto status_admission=self->begin_actor_status_writer();
            std::vector<std::uint8_t> response;
            std::uint64_t created_id=0;
            Session::NativeCharacterList delivery;
            bool succeeded=false;
            try {
                if(!s.close_requested.load() && self->account_id) {
                    if(selection && s.character_handlers.native_list) {
                        if(request || s.mode!=ProtocolMode::God2LegacyCharacterListCandidate ||
                           self->state()!=SessionState::Authenticated || self->character_id || self->recovered_server_selection_.load() ||
                           !advertisement || advertisement->session!=s.id || advertisement->wire.empty())
                            throw std::logic_error("Native list selection input requires fresh actual authenticated account Session");
                        auto observed=std::make_shared<const Session::RecoveredServerSelection>(
                            Session::RecoveredServerSelection{s.id,self->account_id,*selection,advertisement});
                        self->recovered_server_selection_.store(std::move(observed));
                    }
                    if(request) {
                        created_id=s.character_handlers.create(self->account_id,*request);
                        if(!created_id) throw std::runtime_error("Character commit missing identity");
                        s.pending_created_character=created_id;
                        const auto frame=RecoveredCharacterCreateResult::committed_success();
                        response.assign(frame.begin(),frame.end());
                    } else {
                        if(s.character_handlers.native_list) {
                            delivery=s.character_handlers.native_list(*self);
                            if(!delivery || delivery->session!=s.id || delivery->account!=self->account_id ||
                               !delivery->sequence || delivery->selection!=self->recovered_server_selection())
                                throw std::invalid_argument("Native character delivery identity mismatch");
                            response.assign(delivery->frame.begin(),delivery->frame.end());
                        } else {
                            const auto frame=s.character_handlers.list(self->account_id);
                            response.assign(frame.begin(),frame.end());
                        }
                    }
                    succeeded=true;
                }
            } catch(...) { succeeded=false; }
            s.post_status_work(s.strand,[self,succeeded,created_id,delivery=std::move(delivery),response=std::move(response)]() mutable {
                auto& s=*self->impl_;
                [[maybe_unused]] const auto status_admission=self->begin_actor_status_writer();
                if(delivery)s.active_native_list=delivery;
                if(!delivery)s.game_busy=false;
                if(s.closing) {if(delivery)s.fail("Native character delivery closed before queue");else s.finish();return;}
                if(s.close_requested.load()) { s.close();return; }
                if(!succeeded) { s.fail("Recovered character operation rejected");return; }
                try {
                    auto bytes=std::make_shared<std::vector<std::uint8_t>>(std::move(response));
                    if(delivery) {
                        if(s.writes.size()>=max_writes || s.write_bytes>max_buffer-bytes->size())
                            throw std::invalid_argument("Native character list queue capacity exhausted");
                        if(!s.terminal_write_allowed())return;
                        s.append_write({bytes,{},false,true,{},delivery});s.write_bytes+=bytes->size();
                    } else { if(!s.terminal_write_allowed())return; s.write_bytes+=bytes->size();s.append_write({bytes,{}});}
                    if(created_id) {
                        s.c2s0002_state=C2S0002State::CharacterCreateCommitted;
                        s.character_create_input.clear();
                        logger("session")->info("session_id={} CHARACTER_PROFILE_COMMITTED character_id={}; world state not initialized; client acceptance unconfirmed",s.id,created_id);
                    } else {
                        s.c2s0002_state=C2S0002State::PostSelectReceived;
                        logger("session")->info("session_id={} ACCOUNT_CHARACTER_LIST_QUEUED length=78 source={}; queue is not client receipt",s.id,
                            s.character_handlers.native_list?"supplied_native":"populated_candidate");
                    }
                    if(delivery) {s.release_native_list(delivery,bytes);return;}
                    if(s.writes.size()==1) s.write();
                    s.arm_timer(idle_timeout);s.read();
                } catch(...) { s.fail("Recovered character response failed"); }
            });
        });
    }
    // Network -> game -> network handoff. No SQLite/source callbacks on strand,
    // nor real game-affine closures in Write. A held frame cannot start early.
    void release_native_list(Session::NativeCharacterList delivery,std::shared_ptr<std::vector<std::uint8_t>> bytes) {
        post_status_work(game,[self=owner.shared_from_this(),delivery,bytes] {
            auto& s=*self->impl_;
                [[maybe_unused]] const auto status_admission=self->begin_actor_status_writer();bool accepted=false;
            try {accepted=!s.close_requested.load() && s.character_handlers.native_list_current(*self,delivery);}
            catch(...) {}
            s.post_status_work(s.strand,[self,delivery,bytes,accepted] {
                auto& s=*self->impl_;
                [[maybe_unused]] const auto status_admission=self->begin_actor_status_writer();
                if(s.active_native_list!=delivery)return; // Cancellation already owns completion.
                if(!accepted || s.closing || s.close_requested.load()) {s.fail("Native list source changed before write");return;}
                const auto found=std::find_if(s.writes.begin(),s.writes.end(),[&](const Write& value){return value.native_list==delivery;});
                if(found==s.writes.end() || !found->held || found->bytes!=bytes ||
                   bytes->size()!=delivery->frame.size() || !std::equal(bytes->begin(),bytes->end(),delivery->frame.begin())) {
                    s.fail("Native list held queue identity mismatch");return;
                }
                found->held=false;if(found==s.writes.begin())s.write();
            });
        });
    }
    void complete_native_list(Session::NativeCharacterList delivery,bool written) {
        if(!delivery || active_native_list!=delivery)return;
        active_native_list.reset(); // Once before any deferred completion or queue clear.
        post_status_work(game,[self=owner.shared_from_this(),delivery,written] {
            auto& s=*self->impl_;
                [[maybe_unused]] const auto status_admission=self->begin_actor_status_writer();bool accepted=false;
            try {
                accepted=s.character_handlers.native_list_complete(*self,delivery,written);
                accepted=accepted && written && !self->closing() && self->account_id==delivery->account &&
                    self->id()==delivery->session && self->recovered_server_selection()==delivery->selection;
                if(accepted)self->recovered_native_character_list_.store(delivery);
            }catch(...) {accepted=false;}
            s.post_status_work(s.strand,[self,accepted] {
                auto& s=*self->impl_;
                [[maybe_unused]] const auto status_admission=self->begin_actor_status_writer();s.game_busy=false;
                if(s.closing) {s.finish();return;}
                if(!accepted || s.close_requested.load()) {s.fail("Native list delivery source completion rejected");return;}
                s.arm_timer(idle_timeout);s.read();
            });
        });
    }
    void delete_character(RecoveredCharacterDelete request) {
        game_busy=true;
        post_status_work(game,[self=owner.shared_from_this(),request] {
            auto& s=*self->impl_;
                [[maybe_unused]] const auto status_admission=self->begin_actor_status_writer();
            bool accepted=false;
            try {
                if(!s.close_requested.load() && self->account_id && !self->character_id &&
                   s.character_handlers.delete_character)
                    accepted=s.character_handlers.delete_character(*self,request);
            } catch(const std::exception& error) {
                logger("session")->warn("session_id={} CHARACTER_DELETE_REJECTED reason={}",s.id,error.what());
            } catch(...) {}
            s.post_status_work(s.strand,[self,accepted] {
                auto& s=*self->impl_;
                [[maybe_unused]] const auto status_admission=self->begin_actor_status_writer();s.game_busy=false;
                if(s.closing) { s.finish();return; }
                if(s.close_requested.load()) { s.close();return; }
                auto bytes=std::make_shared<std::vector<std::uint8_t>>(
                    RecoveredCharacterDelete::response(accepted));
                if(!s.terminal_write_allowed())return;
                s.write_bytes+=bytes->size();s.append_write({bytes,{}});
                logger("session")->info("session_id={} CHARACTER_DELETE_RESULT accepted={}",s.id,accepted);
                if(s.writes.size()==1)s.write();
                s.arm_timer(idle_timeout);s.read();
            });
        });
    }
    void acknowledge_created_slot() {
        game_busy=true;
        post_status_work(game,[self=owner.shared_from_this()] {
            auto& s=*self->impl_;
                [[maybe_unused]] const auto status_admission=self->begin_actor_status_writer();
            std::optional<std::uint8_t> slot;
            try {
                if(!s.close_requested.load())
                    slot=s.character_handlers.created_slot(self->account_id,s.pending_created_character);
            } catch(...) {}
            s.post_status_work(s.strand,[self,slot] {
                auto& s=*self->impl_;
                [[maybe_unused]] const auto status_admission=self->begin_actor_status_writer();
                s.game_busy=false;
                if(s.closing) { s.finish();return; }
                if(s.close_requested.load()) { s.close();return; }
                if(!slot || *slot>=2) { s.fail("Native creation slot ownership rejected");return; }
                try {
                    // 15210 reads byte1; byte2 is unread here, zero candidate only.
                    auto bytes=std::make_shared<std::vector<std::uint8_t>>(
                        RecoveredWorldFrame::encode(std::array<std::uint8_t,3>{0x18,*slot,0}));
                    if(!s.terminal_write_allowed())return;
                    s.write_bytes+=bytes->size();s.append_write({bytes,{}});
                    s.native_create_ack_sent=true;s.post_create_input.clear();
                    logger("session")->info("session_id={} NATIVE_CREATE_SLOT_ACK_QUEUED slot={}; tail=unverified_zero; world not entered",s.id,*slot);
                    if(s.writes.size()==1) s.write();
                    s.arm_timer(idle_timeout);s.read();
                } catch(...) { s.fail("Native creation slot response failed"); }
            });
        });
    }
    void select_character(std::uint8_t token,bool created,
                          std::optional<RecoveredPostCreateSelect::Selection> native_input=std::nullopt) {
        retire_normal_output(); // Before any selection callback or game-owned identity write.
        game_busy=true;
        post_status_work(game,[self=owner.shared_from_this(),token,created,native_input=std::move(native_input)] {
            auto& s=*self->impl_;
                [[maybe_unused]] const auto status_admission=self->begin_actor_status_writer();
            std::uint64_t selected=0;
            std::optional<RecoveredWorldEntry::Frame> world_frame;
            std::optional<std::uint16_t> prepared_actor;
            std::uint64_t entry_account=0,entry_battle=0;
            try {
                if(!s.close_requested.load()) {
                    if(s.character_handlers.native_select) {
                        if(!native_input || native_input->token()!=token)
                            throw std::invalid_argument("Native character selection requires the actual owned input");
                        if(!self->account_id || self->character_id || self->state()!=SessionState::Authenticated ||
                           self->recovered_native_selection_input_.load())
                            throw std::invalid_argument("Native character selection input is not fresh");
                        self->recovered_native_selection_input_.store(std::make_shared<const Session::NativeCharacterSelectionInput>(
                            Session::NativeCharacterSelectionInput{s.id,self->account_id,*native_input,
                                created?std::optional<std::uint64_t>{s.pending_created_character}:std::nullopt}));
                        selected=s.character_handlers.native_select(*self,*native_input,created?
                            std::optional<std::uint64_t>{s.pending_created_character}:std::nullopt);
                    } else selected=created?s.character_handlers.select_created(self->account_id,s.pending_created_character,token)
                        :s.character_handlers.select_existing(self->account_id,token);
                    if(selected && s.character_handlers.world_entry) {
                        // Capture the supplier's actual tuple BEFORE external
                        // callbacks; never relabel old bytes with a changed owner.
                        entry_account=self->account_id;entry_battle=self->battle_generation();
                        world_frame=s.character_handlers.world_entry(s.id,entry_account,selected);
                    }
                    if(selected && !s.close_requested.load()) self->character_id=selected;
                    if(selected && world_frame && !s.close_requested.load()) {
                        if(s.character_handlers.common_world_lifecycle_factory) {
                            if(s.common_world_lifecycle_factory_invoked)
                                throw std::logic_error("Common world lifecycle factory already invoked");
                            s.common_world_lifecycle_factory_invoked=true;
                            auto lifecycle=s.character_handlers.common_world_lifecycle_factory(*self);
                            if(!lifecycle || !lifecycle->prepared || bool(lifecycle->ready)==bool(lifecycle->ready_async) ||
                               bool(lifecycle->ready_async)!=bool(lifecycle->cancel) ||
                               (lifecycle->ready_async && !s.character_handlers.common_world_publication_owner))
                                throw std::invalid_argument("Common world lifecycle factory returned incomplete hooks");
                            s.character_handlers.common_world_lifecycle=std::move(lifecycle);
                        }
                        const auto lifecycle=s.character_handlers.common_world_lifecycle;
                        const auto supplied=*world_frame;
                        if(s.close_requested.load() || (lifecycle && !lifecycle->prepared(*self,lifecycle->prepared_actor?supplied:*world_frame)))selected=0;
                        if(selected && lifecycle && lifecycle->prepared_actor) {
                            const auto full=RecoveredWorldEntryView::read(supplied);
                            const auto unchanged=[&] {
                                return !s.close_requested.load() && !self->closing() && self->account_id==entry_account &&
                                    self->character_id==selected && self->battle_generation()==entry_battle &&
                                    world_frame && *world_frame==supplied && s.character_handlers.common_world_lifecycle==lifecycle;
                            };
                            if(!full || !qualified_taiwan_scene_handle(full->actor_handle) || !unchanged())
                                throw std::invalid_argument("Qualified world entry identity changed before preparation receipt");
                            const auto actor=lifecycle->prepared_actor(*self,supplied);
                            if(!actor || !qualified_taiwan_scene_handle(*actor) || *actor!=full->actor_handle || !unchanged())
                                throw std::invalid_argument("Qualified world entry preparation receipt rejected");
                            prepared_actor=*actor;
                        }
                    }
                }
            } catch(...) { selected=0; }
            // Passive metadata follows the actual supplier/prepared hook. A
            // decode/allocation failure cannot change frozen selection routing.
            std::shared_ptr<NormalWorldInitialization::Entry> normal_entry;
            try {
                if(selected && world_frame && entry_account && !s.close_requested.load() &&
                   self->account_id==entry_account && self->character_id==selected &&
                   self->battle_generation()==entry_battle) {
                    auto logical=RecoveredWorldFrame::decode(*world_frame);
                    if(logical && logical->size()==37 && logical->front()==0x2a)
                        normal_entry=std::make_shared<NormalWorldInitialization::Entry>(self,
                            entry_account,selected,entry_battle,*world_frame,std::move(*logical),prepared_actor.has_value());
                }
            } catch(...) {}
            s.post_status_work(s.strand,[self,selected,created,world_frame,prepared_actor,normal_entry=std::move(normal_entry)] {
                auto& s=*self->impl_;
                [[maybe_unused]] const auto status_admission=self->begin_actor_status_writer();
                s.game_busy=false;
                if(s.closing) { s.finish();return; }
                if(s.close_requested.load()) { s.close();return; }
                if(!selected) { s.fail("Character selection ownership rejected");return; }
                try {
                    // Current 14D20 accepts the same 02/result-WORD-zero shape.
                    const auto frame=RecoveredCharacterCreateResult::committed_success();
                    auto bytes=std::make_shared<std::vector<std::uint8_t>>(frame.begin(),frame.end());
                    if(!s.terminal_write_allowed())return;
                    s.write_bytes+=bytes->size();s.append_write({bytes,{}});
                    s.retire_normal_output(); // Before replacement, not after new identity publication.
                    s.owner.invalidate_actor_status_writes(); // Before incarnation replacement.
                    if(const auto old=s.normal_entry.exchange(normal_entry))old->retired.store(true);
                    s.normal_initialization.store({});
                    s.normal_tail_size=0;s.normal_tail_observable=true;
                    if(world_frame) {
                        auto next=std::make_shared<std::vector<std::uint8_t>>(world_frame->begin(),world_frame->end());
                        if(!s.terminal_write_allowed())return;
                        Write original{next,{},true};original.normal_entry=normal_entry;
                        s.write_bytes+=next->size();s.append_write(std::move(original));
                    }
                    s.c2s0002_state=world_frame?C2S0002State::WorldEntrySent:C2S0002State::CharacterSelected;
                    if(world_frame) {
                        if(prepared_actor)s.world_ready.emplace(*prepared_actor);
                        else s.world_ready.emplace(selected);
                    }
                    self->set_state(SessionState::CharacterSelected);
                    logger("session")->info("session_id={} {} character_id={}; world_candidate={}; InWorld not established",s.id,
                        created?"POST_CREATE_CHARACTER_BOUND":"EXISTING_CHARACTER_BOUND",selected,world_frame.has_value());
                    if(s.writes.front().bytes==bytes) s.write();
                    s.arm_timer(idle_timeout);s.read();
                } catch(...) { s.fail("Post-create selection response failed"); }
            });
        });
    }
    void observe_normal_tail(std::span<const std::uint8_t> bytes) noexcept {
        if(!normal_tail_observable)return;
        if(bytes.size()>normal_tail_bytes.size()-normal_tail_size) {
            normal_tail_observable=false;return;
        }
        std::copy(bytes.begin(),bytes.end(),normal_tail_bytes.begin()+normal_tail_size);
        normal_tail_size+=bytes.size();
    }
    void retire_normal_initialization() noexcept {
        owner.invalidate_actor_status_writes();
        retire_normal_output();
        if(const auto entry=normal_entry.load())entry->retired.store(true);
        normal_initialization.store({});
    }
    void accept_world_tail() {
        retire_normal_output(); // Before the actual world_ready observer can mutate owner state.
        game_busy=true;
        owner.recovered_client_language_.store(world_ready->config_flag());
        const auto entry=normal_entry.load();
        const auto tail=normal_tail_bytes;
        const auto tail_size=normal_tail_size;
        const auto observable=normal_tail_observable;
        const auto config=world_ready->config_flag();
        const auto context=world_ready->context_payload();
        post_status_work(game,[self=owner.shared_from_this(),entry,tail,tail_size,observable,config,context] {
            auto& s=*self->impl_;
                [[maybe_unused]] const auto status_admission=self->begin_actor_status_writer();
            bool accepted=false;
            std::shared_ptr<const NormalWorldInitialization::Data> initialization;
            try {
                if(!s.close_requested.load()) {
                    if(s.character_handlers.world_ready) s.character_handlers.world_ready(*self);
                    accepted=true;
                }
            } catch(...) {}
            // The existing hook has genuinely returned. These owned bytes are
            // observations only; a forged tail cannot attest remote execution.
            try {
                if(accepted && s.character_handlers.world_ready && observable && tail_size && entry &&
                   s.normal_entry.load()==entry && !entry->retired.load() && !s.close_requested.load() &&
                   entry->session.lock().get()==self.get() && entry->account==self->account_id &&
                   entry->character==self->character_id && entry->battle==self->battle_generation())
                    {
                        const auto selector=s.make_receiver_selector(entry,context);
                        initialization=std::make_shared<const NormalWorldInitialization::Data>(entry,
                            std::vector<std::uint8_t>(tail.begin(),tail.begin()+tail_size),config,selector);
                        s.receiver_selector=selector;
                    }
            } catch(...) {}
            s.post_status_work(s.strand,[self,accepted,initialization=std::move(initialization)] {
                auto& s=*self->impl_;
                [[maybe_unused]] const auto status_admission=self->begin_actor_status_writer();
                s.game_busy=false;
                if(s.closing) { s.finish();return; }
                if(s.close_requested.load()) { s.close();return; }
                if(!accepted) { s.fail("Recovered world binding rejected");return; }
                try {
                    s.c2s0002_state=C2S0002State::WorldTailAccepted;
                    s.retire_normal_output();
                    self->recovered_world_ready_.store(true);
                    if(initialization && s.normal_entry.load()==initialization->entry &&
                       !initialization->entry->retired.load())s.normal_initialization.store(initialization);
                    logger("session")->info("session_id={} WORLD_INITIALIZER_TAIL_ACCEPTED opcodes=31,35,28 config_flag={}; live rendered world not verified",s.id,s.world_ready->config_flag());
                    if(s.character_handlers.common_world_lifecycle) {
                        // No new read/dispatch while the common actor is being
                        // activated. The frozen legacy ready hook already ran.
                        s.game_busy=true;
                        s.post_status_work(s.game,[self] {
                            auto& s=*self->impl_;
                [[maybe_unused]] const auto status_admission=self->begin_actor_status_writer();bool common_accepted=false;
                            if(s.character_handlers.common_world_lifecycle->ready_async) {
                                s.begin_common_ready_async(self);return;
                            }
                            try {
                                if(!s.close_requested.load())
                                    common_accepted=s.character_handlers.common_world_lifecycle->ready(*self);
                            }catch(...) {}
                            s.post_status_work(s.strand,[self,common_accepted] {
                                auto& s=*self->impl_;
                [[maybe_unused]] const auto status_admission=self->begin_actor_status_writer();s.game_busy=false;
                                if(s.closing){s.finish();return;}
                                if(s.close_requested.load()){s.close();return;}
                                if(!common_accepted){s.fail("Common world activation rejected");return;}
                                try {
                                    if(!s.world_input.empty()){s.feed_world({});return;}
                                    s.arm_timer(idle_timeout);s.read();
                                }catch(...){s.fail("Common world input resume failed");}
                            });
                        });
                        return;
                    }
                    // Native scalar consumers prove layouts, not selected-character
                    // values or a reply to this tail. Keep the old replay diagnostic-only.
                    if(!s.world_input.empty()) { s.feed_world({});return; }
                    s.arm_timer(idle_timeout);s.read();
                } catch(...) { s.fail("Recovered world-ready response failed"); }
            });
        });
    }
    void finish_common_ready(std::uint64_t nonce,bool accepted) {
        if(nonce!=common_ready_nonce || !common_ready_completion)return;
        auto complete=std::move(common_ready_completion);
        common_ready_waiting.store(false);
        if(!accepted)common_entry_identity.store({});
        complete(accepted && !close_requested.load());
    }
    void begin_common_ready_async(const std::shared_ptr<Session>& self) {
        common_ready_thread=std::this_thread::get_id();
        if(common_ready_completion || common_ready_nonce==std::numeric_limits<std::uint64_t>::max()) {
            post_status_work(strand,[self] {auto& s=*self->impl_;
                [[maybe_unused]] const auto status_admission=self->begin_actor_status_writer();s.game_busy=false;s.fail("Common world async readiness already pending or exhausted");});
            return;
        }
        const auto nonce=++common_ready_nonce;
        common_ready_completion=[self](bool accepted) {
            self->impl_->post_status_work(self->impl_->strand,[self,accepted] {
                auto& s=*self->impl_;
                [[maybe_unused]] const auto status_admission=self->begin_actor_status_writer();s.game_busy=false;
                if(s.closing){s.finish();return;}
                if(s.close_requested.load()){s.close();return;}
                if(!accepted){s.fail("Common world async activation rejected");return;}
                try {
                    if(!s.world_input.empty()){s.feed_world({});return;}
                    s.arm_timer(idle_timeout);s.read();
                }catch(...){s.fail("Common world async input resume failed");}
            });
        };
        common_ready_waiting.store(true);
        if(close_requested.load()) {finish_common_ready(nonce,false);return;}
        auto done=retain_actor_status_writer(owner.begin_actor_status_writer(),
            [weak=std::weak_ptr<Session>(self),nonce,thread=common_ready_thread](bool accepted) {
            if(thread!=std::this_thread::get_id())throw std::logic_error("Common world readiness completion game owner mismatch");
            if(const auto current=weak.lock())current->impl_->finish_common_ready(nonce,accepted);
        });
        try {character_handlers.common_world_lifecycle->ready_async(*self,std::move(done));}
        catch(...) {
            if(!common_ready_completion)return; // An inline completion already consumed its result.
            try {character_handlers.common_world_lifecycle->cancel(*self);}catch(...) {}
            finish_common_ready(nonce,false);
        }
    }
    void cancel_common_ready() {
        common_entry_identity.store({}); // Invalidate held publications immediately.
        if(common_ready_cancel_posted || !common_ready_waiting.load())return;
        common_ready_cancel_posted=true;
        post_status_work(game,[self=owner.shared_from_this()] {
            auto& s=*self->impl_;
                [[maybe_unused]] const auto status_admission=self->begin_actor_status_writer();const auto nonce=s.common_ready_nonce;
            try {
                if(s.common_ready_completion && s.character_handlers.common_world_lifecycle &&
                   s.character_handlers.common_world_lifecycle->cancel)
                    s.character_handlers.common_world_lifecycle->cancel(*self);
            }catch(...) {}
            // A cancel supplier cannot strand the transport's game_busy hold.
            s.finish_common_ready(nonce,false);
        });
    }
    bool has_world_handler() const noexcept {
        return character_handlers.movement || character_handlers.world_records;
    }
    static bool valid_world_response(std::span<const std::uint8_t> bytes) {
        if(bytes.size()>max_buffer) return false;
        for(std::size_t at=0;at<bytes.size();) {
            if(bytes.size()-at<2) return false;
            const auto length=static_cast<std::size_t>(bytes[at])+256u*bytes[at+1];
            if(length<4 || length>bytes.size()-at ||
               !RecoveredWorldFrame::decode(bytes.subspan(at,length))) return false;
            at+=length;
        }
        return true;
    }
    // Final wire has already passed existing complete-frame validation. Match
    // exact registered components at frame boundaries, in order/nonoverlapping.
    static bool normal_response_components_match(const NormalWorldResponseAttempt::Data& receipt,
            std::span<const std::uint8_t> wire) {
        if(!receipt.armed.load() || receipt.components.empty())return false;
        std::size_t at=0;
        for(const auto& component:receipt.components) {
            bool found=false;
            while(at<wire.size()) {
                if(component.size()<=wire.size()-at &&
                   std::equal(component.begin(),component.end(),wire.begin()+static_cast<std::ptrdiff_t>(at))) {
                    at+=component.size();found=true;break;
                }
                if(wire.size()-at<2)return false;
                const auto length=static_cast<std::size_t>(wire[at])+256u*wire[at+1];
                if(length<4 || length>wire.size()-at)return false;
                at+=length;
            }
            if(!found)return false;
        }
        return true;
    }
    static bool same_movement_request(const RecoveredMovement::Request& a,const RecoveredMovement::Request& b) noexcept {
        return a.x==b.x && a.y==b.y && a.sequence==b.sequence && a.opaque_tail==b.opaque_tail;
    }
    bool movement_transport_current(const std::shared_ptr<MovementResponseAttempt>& attempt) const noexcept {
        if(!attempt || !attempt->receipt)return false;
        const auto& data=*attempt->receipt;
        const auto status=data.status.load();
        // Accepted original sender custody is historical after the GAME cut.
        // A later legitimate callback can change phase/common/battle before
        // this older FIFO frame finishes. No live gameplay gate belongs on IO.
        return status!=MovementResponseWriteStatus::Failed && !owner.closing() &&
            mode==ProtocolMode::God2CharacterConnection && data.occurrence &&
            data.session.lock().get()==&owner;
    }
    bool movement_frame_current(const std::shared_ptr<MovementResponseAttempt>& attempt,
        const std::shared_ptr<std::vector<std::uint8_t>>& bytes) const noexcept {
        return movement_transport_current(attempt) && attempt->frame==bytes &&
            !attempt->frame.owner_before(bytes) && !bytes.owner_before(attempt->frame) &&
            attempt->receipt->wire==*bytes;
    }
    struct MovementCallbackScope {
        Impl& state;
        std::shared_ptr<MovementCollector> collector;
        explicit MovementCallbackScope(Impl& actual,std::span<const RecoveredWorldRecords::Record> records):state(actual) {
            if(!state.character_handlers.native_movement_response_custody &&
               !state.character_handlers.owned_normal_movement_response_custody)return;
            if(observed_movement_callback || state.movement_collector) {
                if(observed_movement_poison)*observed_movement_poison=true;
                if(state.movement_collector)state.movement_collector->poisoned=true;
                throw std::logic_error("Movement response callback reentry rejected");
            }
            if(state.movement_game_thread!=std::thread::id{} && state.movement_game_thread!=std::this_thread::get_id())
                throw std::logic_error("Movement response callback game owner mismatch");
            state.movement_game_thread=std::this_thread::get_id();
            // Parsed2E bounds allocations only. Legacy intercepted movement
            // which never enters an actual registered Core run is unattested.
            const auto capacity=std::count_if(records.begin(),records.end(),[](const auto& record) {
                return std::holds_alternative<RecoveredMovement::Request>(record);
            });
            collector=std::make_shared<MovementCollector>(state.common_world_identity.load(),records,
                static_cast<std::size_t>(capacity),state.character_handlers.owned_normal_movement_response_custody);
            state.movement_collector=collector;
            observed_movement_callback=&state.owner;observed_movement_poison=&collector->poisoned;
        }
        std::shared_ptr<MovementResponseAttempt> finish(bool accepted,std::span<const std::uint8_t> response) {
            if(!collector)return {};
            if(collector->poisoned || collector->run_nonce || collector->offset_scope_nonce || !collector->active)
                throw std::runtime_error("Movement response scope incomplete or poisoned");
            if(collector->normal_mode)return finish_normal(accepted,response);
            if(collector->steps.empty())return {}; // Preserve unregistered legacy acceptance, without proof.
            if(!accepted || !collector->lease || collector->assigned!=collector->steps.size() ||
               state.common_world_identity.load().get()!=collector->common.get() || state.owner.closing() ||
               !state.owner.recovered_world_ready() || state.common_entry_identity.load())
                throw std::runtime_error("Movement response original callback incomplete or retired");
            std::vector<std::shared_ptr<const MovementStepWrite::Data>> frozen;frozen.reserve(collector->steps.size());
            std::size_t index=0;
            for(std::size_t offset=0;offset<response.size();) {
                if(response.size()-offset<2)throw std::runtime_error("Movement response boundary truncated");
                const auto length=std::size_t(response[offset])+256u*response[offset+1];
                if(length<4 || length>response.size()-offset)throw std::runtime_error("Movement response boundary invalid");
                if(index<collector->steps.size() && collector->steps[index]->offset==offset) {
                    const auto step=collector->steps[index];
                    if(!step->committed || length!=step->frame.size() || step->common!=collector->common ||
                       step->lease!=*collector->lease || step->occurrence!=collector->occurrence ||
                       step->session.lock().get()!=&state.owner ||
                       !std::equal(step->frame.begin(),step->frame.end(),response.begin()+static_cast<std::ptrdiff_t>(offset)))
                        throw std::runtime_error("Movement response original step frame mismatch");
                    frozen.push_back(step);++index;
                }
                offset+=length;
            }
            if(index!=collector->steps.size())throw std::runtime_error("Movement response components are not exact boundaries");
            // Historical steps keep their own phase/pose. The original WHOLE
            // callback freezes its actual final phase/battle/delivery separately.
            const auto data=std::make_shared<MovementResponseWrite::Data>(state.owner.weak_from_this(),collector->occurrence,
                collector->common,state.world_delivery_identity.load(),*collector->lease,state.owner.battle_generation(),
                state.owner.state(),std::move(frozen),response);
            const auto attempt=std::make_shared<MovementResponseAttempt>(data);
            if(!state.movement_transport_current(attempt) || state.owner.state()!=data->phase ||
               state.owner.battle_generation()!=data->battle ||
               state.common_world_identity.load().get()!=data->common.get() ||
               state.world_delivery_identity.load().get()!=data->world.get() ||
               state.common_entry_identity.load() || !state.owner.recovered_world_ready())
                throw std::runtime_error("Movement response final source cut retired");
            state.latest_movement_response.store(data);return attempt;
        }
        std::shared_ptr<MovementResponseAttempt> finish_normal(bool accepted,std::span<const std::uint8_t> response) {
            if(collector->normal_batches.empty())return {}; // Unregistered non-movement remains unattested.
            if(!accepted || !collector->normal_initialization || collector->lease || !collector->steps.empty() ||
               collector->normal_assigned!=collector->normal_batches.size() || collector->common ||
               state.common_world_identity.load() || state.common_entry_identity.load() ||
               state.owner.closing() || !state.owner.recovered_world_ready())
                throw std::runtime_error("Normal movement original callback incomplete or retired");
            const auto init=*collector->normal_initialization;
            const auto init_data=init.data_;
            if(!init_data || !init_data->entry || state.normal_initialization.load()!=init_data ||
               state.normal_entry.load()!=init_data->entry || !init.entry_written() ||
               init_data->entry->session.lock().get()!=&state.owner ||
               init_data->entry->account!=state.owner.account_id || init_data->entry->character!=state.owner.character_id)
                throw std::runtime_error("Normal movement original initialization retired");
            std::vector<std::shared_ptr<const NormalMovementBatchWrite::Data>> frozen;
            frozen.reserve(collector->normal_batches.size());
            std::size_t index=0;
            for(std::size_t offset=0;offset<response.size();) {
                if(response.size()-offset<2)throw std::runtime_error("Normal movement response boundary truncated");
                const auto length=std::size_t(response[offset])+256u*response[offset+1];
                if(length<4 || length>response.size()-offset)throw std::runtime_error("Normal movement response boundary invalid");
                if(index<collector->normal_batches.size() && collector->normal_batches[index]->offset==offset) {
                    const auto batch=collector->normal_batches[index];
                    if(!batch->committed || length!=5 || batch->wire.empty() || batch->wire.size()>response.size()-offset ||
                       batch->occurrence!=collector->occurrence || batch->session.lock().get()!=&state.owner ||
                       !batch->initialization.same_initialization(init) ||
                       !std::equal(batch->wire.begin(),batch->wire.end(),response.begin()+static_cast<std::ptrdiff_t>(offset)))
                        throw std::runtime_error("Normal movement original whole-batch frames mismatch");
                    frozen.push_back(batch);++index;offset+=batch->wire.size();
                } else offset+=length;
            }
            if(index!=collector->normal_batches.size())throw std::runtime_error("Normal movement batches are not exact boundaries");
            // Later work in this same callback may legitimately enter battle.
            // Keep the original normal INIT and each historical batch, while
            // the whole sender records its ACTUAL final phase/delivery cut.
            const auto data=std::make_shared<MovementResponseWrite::Data>(state.owner.weak_from_this(),collector->occurrence,
                init,state.world_delivery_identity.load(),state.owner.battle_generation(),state.owner.state(),std::move(frozen),response);
            const auto attempt=std::make_shared<MovementResponseAttempt>(data);
            if(!state.movement_transport_current(attempt) || state.owner.state()!=data->phase ||
               state.owner.battle_generation()!=data->battle || state.normal_initialization.load()!=init_data ||
               state.normal_entry.load()!=init_data->entry || !init.entry_written() ||
               state.world_delivery_identity.load().get()!=data->world.get() || state.common_world_identity.load() ||
               state.common_entry_identity.load() || !state.owner.recovered_world_ready())
                throw std::runtime_error("Normal movement final original sender cut retired");
            state.latest_movement_response.store(data);return attempt;
        }
        ~MovementCallbackScope() {
            if(!collector)return;
            collector->active=false;
            if(state.movement_collector==collector)state.movement_collector.reset();
            observed_movement_poison=nullptr;observed_movement_callback=nullptr;
        }
    };
    bool owned_input_transport_current(const std::shared_ptr<WorldResponseAttempt>& held) const {
        return held && owned_response_input_hold.load()==held && !owned_input_retired.load() && !close_requested.load() &&
            held->input_phase.load()==WorldResponseAttempt::InputPhase::Armed &&
            held->receipt->status.load()!=WorldResponseWriteStatus::Failed &&
            held->receipt->session.lock().get()==&owner && mode==ProtocolMode::God2CharacterConnection &&
            owner.state()==held->receipt->phase && owner.battle_generation()==held->receipt->battle &&
            !native_pk_terminal.load() && !native_pk_pending.load() && !native_battle_pending.load();
    }
    void retire_owned_input() noexcept {
        if(const auto cohort=callback_output_input_hold.exchange({})){
            owned_input_retired.store(true);cohort->fail();close_requested.store(true);closing=true;
            asio::error_code ignored;socket.close(ignored);
        }
        if(const auto held=owned_response_input_hold.exchange({})) {
            owned_input_retired.store(true);held->fail();close_requested.store(true);closing=true;
            asio::error_code ignored;socket.close(ignored);
        }
    }
    void fail_owned_input(const char* reason) noexcept {
        // Preserve opted identity after pointer removal, including a failure
        // after physical Written/release. No logger precedes retirement.
        owned_input_retired.store(true);close_requested.store(true);closing=true;
        retire_owned_input();asio::error_code ignored;socket.close(ignored);
        try {fail(reason);}catch(...) {} // Socket/input are already retired; no native convergence claim.
    }
    bool owned_input_paused() {
        if(owned_input_retired.load()) {
            if(!closing)fail_owned_input("Owned bootstrap input already retired");
            return true;
        }
        if(const auto cohort=callback_output_input_hold.load()){
            if(!callback_output_transport_current(cohort)||cohort->status.load()==WorldCallbackOutputStatus::Failed)
                fail_owned_input("Callback output raw input hold retired");
            return true;
        }
        const auto held=owned_response_input_hold.load();if(!held)return false;
        if(!owned_input_transport_current(held))fail_owned_input("Owned bootstrap input hold retired");
        return true;
    }
    void release_owned_input(const std::shared_ptr<OwnedInputLease>& lease) {
        const auto held=lease->attempt;
        if(!owned_input_transport_current(held) ||
           held->receipt->status.load()!=WorldResponseWriteStatus::Written) {
            fail_owned_input("Owned bootstrap input continuation is not exact Written/current");return;
        }
        auto armed=WorldResponseAttempt::InputPhase::Armed;
        if(!held->input_phase.compare_exchange_strong(armed,WorldResponseAttempt::InputPhase::Released)) {
            fail_owned_input("Owned bootstrap input continuation retired");return;
        }
        auto expected=held;
        if(!owned_response_input_hold.compare_exchange_strong(expected,{})) {
            fail_owned_input("Owned bootstrap input continuation identity changed");return;
        }
        // An older read/game completion owns its existing continuation. Never
        // issue a second read merely because this exact write has now finished.
        if(game_busy || read_inflight)return;
        try {resume_world_input(bool(skill_deadline));}
        catch(...) {
            // Written stays a physical fact. Failure of this later continuation
            // retires input/owner before the old logger can itself throw.
            fail_owned_input("Owned bootstrap input continuation failed");
        }
    }
    void resume_world_input(bool awaiting_skill=false) {
        if(native_logout_phase!=NativeLogoutPhase::None){
            // Defer past the current NET callback's remaining admission/receipt
            // bookkeeping before posting the terminal GAME cleanup.
            if(native_logout_phase==NativeLogoutPhase::Draining)post_status_work(strand,[self=owner.shared_from_this()]{self->impl_->advance_native_logout();});
            return;
        }
        if(owned_input_paused())return;
        if(const auto final=native_pk_return_finalisation.load();final&&
           final->phase.load()==NativePkReturnFinalisationStatus::Returned){
            const auto index=final->sessions[0].lock().get()==&owner?0u:1u;
            if(!final->resume_started[index].load())return;
        }
        if(native_pk_terminal.load()) {stage_native_pk_terminal();return;}
        if(native_pk_pending.load()) {native_pk_read_paused=true;stage_native_pk();return;}
        if(native_battle_pending.load()) {native_battle_read_paused=true;stage_native_pk_output();return;}
        if(world_input.size()>=2) {
            const auto length=static_cast<std::size_t>(world_input[0])+256u*world_input[1];
            if(length<5 || length>RecoveredWorldRecords::max_logical_size+3 ||
               world_input.size()>=length) {
                post_status_work(strand,[self=owner.shared_from_this()] { self->impl_->feed_world({}); });
                return;
            }
        }
        if(awaiting_skill)
            arm_timer(*skill_deadline-std::chrono::steady_clock::now());
        else
            arm_timer(idle_timeout);
        read();
    }
    void feed_world(std::span<const std::uint8_t> bytes) {
        if(native_logout_phase!=NativeLogoutPhase::None)return; // Never redispatch a suffix after terminal02.
        if(owned_input_retired.load()){owned_input_paused();return;}
        if(has_input_hold()) {
            // Retain raw suffix/in-flight bytes at the original limit. Do not
            // move staged records, decode, reclassify or dispatch a second job.
            try {
                if(world_input.size()>16384 || bytes.size()>16384-world_input.size()) {
                    fail_owned_input("World input limit");return;
                }
                world_input.insert(world_input.end(),bytes.begin(),bytes.end());
                if((native_skill_generation && owner.battle_generation()!=*native_skill_generation) ||
                   (skill_deadline && (std::chrono::steady_clock::now()>=*skill_deadline ||
                                      owner.state()!=SessionState::InBattle))) {
                    fail_owned_input("Owned bootstrap retained skill input expired");return;
                }
                if(owned_input_paused())return;
                fail_owned_input("Owned bootstrap input hold disappeared");return;
            }catch(...){fail_owned_input("Owned bootstrap raw input retention failed");return;}
        }
        if(native_pk_terminal.load()) {
            if(!bytes.empty() || !world_input.empty() || !world_pending_records.empty()) {
                fail("Native PK terminal cannot reclassify old input");return;
            }
            stage_native_pk_terminal();return;
        }
        if(native_pk_pending.load()) {
            native_pk_read_paused=true;
            if(!bytes.empty() || !world_input.empty() || !world_pending_records.empty()) {
                fail("Native PK barrier cannot reclassify old world bytes");return;
            }
            stage_native_pk();return;
        }
        if(native_skill_generation && owner.battle_generation()!=*native_skill_generation) {
            fail("Native skill prefix belongs to a retired battle generation");return;
        }
        if(skill_deadline && (std::chrono::steady_clock::now()>=*skill_deadline ||
                             owner.state()!=SessionState::InBattle)) {
            fail("Incomplete skill sequence expired or left battle");return;
        }
        if(bytes.size()>16384-world_input.size()) { fail("World input limit");return; }
        world_input.insert(world_input.end(),bytes.begin(),bytes.end());
        if(native_battle_pending.load()) {native_battle_read_paused=true;stage_native_pk_output();return;}
        auto records=std::move(world_pending_records);
        world_pending_records.clear();
        const auto previously_staged=records.size();
        auto native_batch_generation=native_skill_generation;
        std::vector<RecoveredMovement::Request> requests;
        std::size_t consumed=0;
        while(world_input.size()-consumed>=2) {
            const auto length=static_cast<std::size_t>(world_input[consumed])+256u*world_input[consumed+1];
            if(length<5 || length>RecoveredWorldRecords::max_logical_size+3) {
                fail("World frame length rejected");return;
            }
            if(world_input.size()-consumed<length) break;
            // Native415730 waits for03 for thirty seconds. Character logout
            // uses02/01; a bare TCP close leaves its wait unresolved.
            const auto control=RecoveredWorldFrame::decode(
                std::span<const std::uint8_t>(world_input).subspan(consumed,length));
            // Outer40E17C/40E18D/40E249 emits02 reason1/2/0, then waits
            // for03. Reason alone does not identify the outer destination.
            if(control && control->size()==2 && (*control)[0]==2 && (*control)[1]<=2 &&
               records.empty() && !skill_deadline) {
                native_logout_reason=(*control)[1];native_logout_phase=NativeLogoutPhase::Draining;
                world_input.clear();world_pending_records.clear();
                arm_timer(close_timeout); // A stuck/drained-away GAME post never earns03.
                advance_native_logout();return;
            }
            std::optional<RecoveredWorldRecords::UnsupportedRecord> unsupported;
            const auto batch=RecoveredWorldRecords::parse_frame(
                std::span<const std::uint8_t>(world_input).subspan(consumed,length),&unsupported,
                character_handlers.guild_relations53,character_handlers.beast_views,
                character_handlers.pk_invitations,character_handlers.companion_controls6b,
                character_handlers.beast_activity9e,character_handlers.e4_controls,
                character_handlers.bf_requests,character_handlers.spectator6e,
                character_handlers.map_panel68,character_handlers.c2_controls,character_handlers.spectator_close,
                character_handlers.native_skill_commands,character_handlers.owned_blacklist,character_handlers.owned_party_directory,
                character_handlers.owned_client_options,character_handlers.native_world_skill_requests,character_handlers.native_preborn_requests,
                character_handlers.native_skill_selection_requests,character_handlers.owned_battle_row_preference);
            if(!batch) {
                // Local protocol diagnosis: never log payloads, names, or chat.
                if(unsupported)
                    logger("session")->warn("session_id={} WORLD_UNSUPPORTED_RECORD offset={} opcode={:02x}",
                        id,unsupported->offset,unsupported->opcode);
                const auto logical=RecoveredWorldFrame::decode(
                    std::span<const std::uint8_t>(world_input).subspan(consumed,length));
                logger("session")->warn("session_id={} WORLD_FRAME_REJECTED wire_length={} decoded={} logical_length={} first_opcode={}",
                    id,length,logical.has_value(),logical?logical->size():0,
                    logical && !logical->empty()?static_cast<unsigned>((*logical)[0]):256u);
                // CUSTOM-0058 diagnostic evidence only; retain all parsing/authorization gates.
                if(packet_dump && logical && logical->size()==17 && (*logical)[0]==0x35)
                    logger("session")->warn("session_id={} BATTLE_COMMAND_STRUCTURE_REJECTED hex_dump={}",id,dump(*logical));
                if(logical && logical->size()>=3 && (*logical)[0]==RecoveredChat::c2s_opcode) {
                    const auto declared=static_cast<std::size_t>((*logical)[1])+256u*(*logical)[2];
                    const bool reserved_zero=logical->size()>=7 &&
                        std::all_of(logical->begin()+3,logical->begin()+7,[](auto value){return value==0;});
                    const bool final_nul=logical->back()==0;
                    const bool interior_nul=logical->size()>=9 &&
                        std::find(logical->begin()+7,logical->end()-1,0)!=logical->end()-1;
                    logger("session")->warn("session_id={} NATIVE_CHAT_STRUCTURE_REJECTED declared={} actual={} reserved_zero={} final_nul={} interior_nul={}",
                        id,declared,logical->size(),reserved_zero,final_nul,interior_nul);
                    if(logical->size()>=7)
                        logger("session")->warn("session_id={} NATIVE_CHAT_HEADER_BYTES {:02x} {:02x} {:02x} {:02x}",
                            id,(*logical)[3],(*logical)[4],(*logical)[5],(*logical)[6]);
                }
                fail("World frame contract rejected");return;
            }
            for(const auto& record:*batch) {
                if(const auto* diagnostic=std::get_if<RecoveredWorldRecords::ClientDiagnostic>(&record)) {
                    std::string report;
                    for(std::size_t at=4;at+2<diagnostic->bytes.size();++at) {
                        const auto byte=diagnostic->bytes[at];
                        report.push_back(byte>=0x20 && byte<=0x7e ? static_cast<char>(byte) : '?');
                    }
                    logger("session")->warn("session_id={} NATIVE_CLIENT_DIAGNOSTIC severity={} text={}",
                        id,static_cast<unsigned>(diagnostic->bytes[3]),report);
                }
            }
            records.insert(records.end(),batch->begin(),batch->end());
            consumed+=length;
            // A TCP read is not a gameplay transaction. Preserve each complete
            // native frame as its own operation; only a continuing skill
            // sequence may span frames before its policy callback.
            const auto* trailing_skill=records.empty()?nullptr:
                std::get_if<RecoveredSkillCommand::Record>(&records.back());
            const auto* trailing_native_skill=records.empty()?nullptr:
                std::get_if<TaiwanNativeSkillCommand::WireRecord>(&records.back());
            if(!(trailing_skill && trailing_skill->continuation) &&
               !(trailing_native_skill && trailing_native_skill->continuation())) break;
        }
        if(records.size()>8192) { fail("World record staging limit");return; }
        std::optional<RecoveredSkillCommand::Record> first_skill;
        std::optional<TaiwanNativeSkillCommand::WireRecord> first_native_skill;
        std::size_t skill_count=0;
        for(std::size_t index=0;index<records.size();++index) {
            const auto& record=records[index];
            if(const auto* skill=std::get_if<RecoveredSkillCommand::Record>(&record)) {
                if(first_native_skill) {fail("Native skill sequence interrupted by legacy command");return;}
                if(owner.state()!=SessionState::InBattle || !character_handlers.world_records) {
                    fail("Skill sequence has no battle policy");return;
                }
                if(!first_skill) first_skill=*skill;
                if(!RecoveredSkillCommand::same_sequence(*first_skill,*skill) ||
                   ++skill_count>RecoveredSkillCommand::max_sequence_records ||
                   (skill->continuation && skill_count==RecoveredSkillCommand::max_sequence_records)) {
                    fail("Skill sequence contract rejected");return;
                }
                if(!skill->continuation) {
                    first_skill.reset();skill_count=0;
                    if(index>=previously_staged) skill_deadline.reset();
                }
            } else if(const auto* skill=std::get_if<TaiwanNativeSkillCommand::WireRecord>(&record)) {
                if(first_skill || owner.state()!=SessionState::InBattle ||
                   !character_handlers.world_records || !character_handlers.native_skill_commands) {
                    fail("Native skill sequence has no matching battle owner");return;
                }
                if(!native_batch_generation)native_batch_generation=owner.battle_generation();
                if(owner.battle_generation()!=*native_batch_generation) {
                    fail("Native skill sequence battle generation changed");return;
                }
                if(!first_native_skill)first_native_skill=*skill;
                if(!TaiwanNativeSkillCommand::same_sequence(*first_native_skill,*skill) ||
                   ++skill_count>RecoveredSkillCommand::max_sequence_records ||
                   (skill->continuation() && skill_count==RecoveredSkillCommand::max_sequence_records)) {
                    fail("Native skill sequence structure rejected");return;
                }
                if(!skill->continuation()) {
                    first_native_skill.reset();skill_count=0;
                    if(index>=previously_staged)skill_deadline.reset();
                }
            } else if(first_skill || first_native_skill) {
                fail("Skill sequence interrupted");return;
            }
        }
        if(first_skill || first_native_skill) {
            world_input.erase(world_input.begin(),world_input.begin()+static_cast<std::ptrdiff_t>(consumed));
            world_pending_records=std::move(records);
            native_skill_generation=native_batch_generation;
            if(!skill_deadline) skill_deadline=std::chrono::steady_clock::now()+skill_sequence_timeout;
            resume_world_input(true);return;
        }
        skill_deadline.reset();
        native_skill_generation.reset();
        if(previously_staged) {
            ++timer_generation;
            timer.cancel();
            arm_timer(idle_timeout);
        }
        // Validate the entire available batch before any game callback. Legacy
        // movement policy cannot silently consume quest/item records.
        if(!character_handlers.world_records) {
            for(const auto& record:records) {
                if(const auto* movement=std::get_if<RecoveredMovement::Request>(&record))
                    requests.push_back(*movement);
                else if(!std::holds_alternative<RecoveredWorldRecords::Tick>(record)) {
                    fail("Recovered world handler unavailable");return;
                }
            }
        }
        world_input.erase(world_input.begin(),world_input.begin()+static_cast<std::ptrdiff_t>(consumed));
        if(records.empty() || (!character_handlers.world_records && requests.empty())) {
            resume_world_input();return;
        }
        game_busy=true;
        post_status_work(game,[self=owner.shared_from_this(),records=std::move(records),requests=std::move(requests),native_batch_generation] {
            auto& s=*self->impl_;
                [[maybe_unused]] const auto status_admission=self->begin_actor_status_writer();
            // A batch parsed/posted BEFORE arm cannot be rolled back into raw
            // input. Reject it before ANY callback/capture/owner mutation; no
            // splitting, redispatch, or reclassification of those records.
            if(const auto held=s.owned_response_input_hold.load();s.has_input_hold() || s.owned_input_retired.load()) {
                if(held)held->fail();
                if(const auto cohort=s.callback_output_input_hold.load())cohort->fail();
                s.owned_input_retired.store(true);s.close_requested.store(true);
                try {s.post_status_work(s.strand,[self] {
                    auto& s=*self->impl_;
                [[maybe_unused]] const auto status_admission=self->begin_actor_status_writer();s.game_busy=false;
                    s.fail_owned_input("Pre-arm world batch reached game during owned input hold");
                });}catch(...) {} // No executor-abort convergence claim.
                return;
            }
            s.native_pk_terminal_callback_capture.reset(); // This exact serial input callback only.
            s.owned_input_callback_lease.reset(); // Retire an unhanded opt-in independently of the strong hold.
            if(s.reply_push_capture||(s.callback_reply_window&&!s.callback_reply_window->pushes.empty()))s.fail_reply_pushes();
            if(s.reply_push_capture)s.reply_push_capture->profile={};s.reply_push_capture.reset();s.reply_push_failed=false;s.reply_push_frames=0;
            if(s.callback_reply_window)s.callback_reply_window->active.store(false);
            s.callback_reply_window.reset();
            s.callback_output_capture.reset();s.callback_output_active=false;s.callback_output_activity=0;
            s.world_response_callback_capture.reset(); // Previous unhanded attempt retires Failed.
            s.normal_response_callback_capture.reset(); // Independent private original-response attempt.
            s.normal_callback_admission_capture.reset(); // Unhanded whole-callback Attempt fails, not Data-only Pending.
            struct ResponseCaptureEnd {
                Impl& state;
                ~ResponseCaptureEnd(){
                    state.owned_input_callback_lease.reset();
                    if(state.reply_push_capture||(state.callback_reply_window&&!state.callback_reply_window->pushes.empty()))state.fail_reply_pushes();
                    if(state.reply_push_capture)state.reply_push_capture->profile={};state.reply_push_capture.reset();
                    if(state.callback_reply_window)state.callback_reply_window->active.store(false);
                    state.callback_reply_window.reset();
                    state.callback_output_active=false;state.callback_output_capture.reset();
                    state.world_response_callback_capture.reset();
                    state.normal_response_callback_capture.reset();
                    state.normal_callback_admission_capture.reset();
                }
            } response_capture_end{s}; // Unhanded attempt fails on every exceptional unwind.
            std::vector<std::uint8_t> response;
            bool accepted=false;
            std::shared_ptr<MovementResponseAttempt> movement_write;
            std::shared_ptr<ReplyPushFinal> reply_pushes;
            try {
                MovementCallbackScope movement_scope(s,records);
                if(!s.close_requested.load()) {
                    if(native_batch_generation && self->battle_generation()!=*native_batch_generation)
                        throw std::runtime_error("Native skill batch belongs to a retired battle generation");
                    if(s.native_battle_pending.load() || s.native_pk_pending.load() || s.native_pk_terminal.load())
                        throw std::runtime_error("Native world batch reached game during battle publication");
                    // Conservative server gate, not recovered turn/actor authority.
                    // Check the full batch before any handler can commit a prefix.
                    const bool has_battle_command=std::any_of(records.begin(),records.end(),[](const auto& record) {
                        return std::holds_alternative<RecoveredBattleCommand::BasicAttackRequest>(record) ||
                               std::holds_alternative<RecoveredBattleCommand::Action2Request>(record) ||
                               std::holds_alternative<RecoveredBattleCommand::ControlRequest>(record) ||
                               std::holds_alternative<RecoveredSkillCommand::Record>(record) ||
                               std::holds_alternative<TaiwanNativeSkillCommand::WireRecord>(record);
                    });
                    if(has_battle_command && self->state()!=SessionState::InBattle)
                        throw std::runtime_error("Recovered attack outside battle state");
                    if(s.character_handlers.world_records) {
                        WorldRecordsObservationScope observation_scope(*self,records);
                        s.callback_output_active=true;s.callback_output_activity=0;
                        Impl::SelectionScope input_scope(s,records);
                        auto result=s.character_handlers.world_records(*self,records);
                        accepted=result.has_value() && (!s.normal_callback_admission_capture || !observation_scope.response_poisoned) && !s.reply_push_failed;
                        if(result) {
                            response=std::move(*result);
                            s.materialize_deferred_selections(response);
                            reply_pushes=s.finish_reply_pushes(response);
                            if(reply_pushes)s.callback_reply_window->pushes.clear(); // Pure post/Write owner takes custody below.
                        }
                    } else {
                        const auto movement_run=self->movement_response_input_run(records);
                        response=s.character_handlers.movement(*self,requests);
                        accepted=!response.empty();
                        if(!self->locate_movement_response_run(0,response))accepted=false;
                    }
                    accepted=accepted && valid_world_response(response);
                    movement_write=movement_scope.finish(accepted,response);
                    if(records.size()==1) {
                        if(const auto* pose=std::get_if<RecoveredWorldRecords::ClientPoseNotification>(&records.front()))
                            logger("session")->info("session_id={} NATIVE_POSE_EXCHANGE character_id={} state={} ready={} payload={} response={} accepted={}",
                                s.id,self->character_id,static_cast<int>(self->state()),self->recovered_world_ready(),
                                dump(pose->payload),dump(response),accepted);
                    }
                    if(!accepted && s.packet_dump) {
                        const auto* move=records.empty()?nullptr:
                            std::get_if<RecoveredMovement::Request>(&records.front());
                        logger("session")->warn(
                            "session_id={} WORLD_POLICY_REJECTED state={} records={} first_variant={} second_variant={} first_move_x={} first_move_y={} response_bytes={}",
                            s.id,static_cast<int>(self->state()),records.size(),
                            records.empty()?99:records.front().index(),
                            records.size()<2?99:records[1].index(),
                            move?move->x:0,move?move->y:0,response.size());
                    }
                }
            } catch(const std::exception& error) {
                if(s.callback_output_capture)s.callback_output_capture->receipt->fail();
                if(reply_pushes||s.reply_push_failed||s.reply_push_capture||(s.callback_reply_window&&!s.callback_reply_window->pushes.empty())||s.callback_output_capture || s.character_handlers.native_movement_response_custody || s.character_handlers.owned_normal_movement_response_custody || s.native_pk_terminal_callback_capture || s.world_response_callback_capture ||
                   s.normal_callback_admission_capture ||
                   (s.normal_response_callback_capture && s.normal_response_callback_capture->receipt->armed.load()))accepted=false;
                logger("session")->warn("Recovered world callback exception session_id={} reason={}",s.id,error.what());
            } catch(...) {
                if(s.callback_output_capture)s.callback_output_capture->receipt->fail();
                if(reply_pushes||s.reply_push_failed||s.reply_push_capture||(s.callback_reply_window&&!s.callback_reply_window->pushes.empty())||s.callback_output_capture || s.character_handlers.native_movement_response_custody || s.character_handlers.owned_normal_movement_response_custody || s.native_pk_terminal_callback_capture || s.world_response_callback_capture ||
                   s.normal_callback_admission_capture ||
                   (s.normal_response_callback_capture && s.normal_response_callback_capture->receipt->armed.load()))accepted=false;
                logger("session")->warn("Recovered world callback exception session_id={} reason=unknown",s.id);
            }
            // The game-owned incarnation survives deadline/close retirement.
            // Only this actual TLS handler could mint it. No later generic ACK
            // can qualify it; rejection/throw never acknowledges acceptance.
            const auto terminal_ack=std::exchange(s.native_pk_terminal_callback_capture,{});
            auto response_write=std::exchange(s.world_response_callback_capture,{});
            const auto input_lease=std::exchange(s.owned_input_callback_lease,{});
            auto normal_response=std::exchange(s.normal_response_callback_capture,{});
            const auto admission=std::exchange(s.normal_callback_admission_capture,{});
            if(admission && (!accepted || admission->receipt->status.load()!=NormalWorldCallbackAdmissionStatus::Pending ||
               !self->normal_world_callback_admission_current_on_game(NormalWorldCallbackAdmission(admission->receipt)))) {
                admission->fail();accepted=false;
            }
            if(normal_response && !normal_response->receipt->armed.load())normal_response.reset(); // Unarmed legacy reply unchanged.
            if(normal_response && (!accepted || normal_response->receipt->status.load()!=NormalWorldResponseStatus::Pending ||
               !normal_response_components_match(*normal_response->receipt,response))) {
                normal_response->fail();accepted=false;
            }
            if(response_write && (!accepted || response_write->receipt->wire!=response ||
               response_write->receipt->status.load()!=WorldResponseWriteStatus::Pending)) {
                response_write->fail();accepted=false;
            }
            // Publish only after all actual callback/response-component checks.
            if(accepted)try{s.accept_receiver_selector_records(records,terminal_ack);}
            catch(...){
                s.receiver_selector.reset();accepted=false;
                if(normal_response)normal_response->fail();
                if(response_write)response_write->fail();
            }
            // Genuine final original response, captured on its actual game owner.
            // This does not install a public observer, owned DB bootstrap flag or
            // input barrier. Existing captures keep their exact original source.
            if(accepted && !response_write && !response.empty() &&
               s.mode==ProtocolMode::God2CharacterConnection && self->state()==SessionState::InBattle &&
               self->account_id && self->character_id){
                try {
                    response_write=std::make_shared<Impl::WorldResponseAttempt>(
                        std::make_shared<WorldResponseWrite::Data>(self,self->account_id,self->character_id,
                            self->battle_generation(),self->state(),response,
                            self->retire_battle_self_view_wire_output(response)));
                }catch(...){/* Missing optional metadata grants no sender qualification. */}
            }
            if(admission && !accepted)admission->fail(); // Existing response-prefix checks apply symmetrically.
            if(movement_write && !accepted)movement_write->fail();
            const auto callback_output=std::exchange(s.callback_output_capture,{});
            s.callback_output_active=false;
            std::shared_ptr<Impl::CallbackComponentAttempt> callback_final;
            if(callback_output){
                const auto data=callback_output->receipt;
                if(!accepted||!s.callback_output_transport_current(data))data->fail();
                try{
                    if(accepted&&!response.empty())callback_final=s.add_callback_component(data,WorldCallbackOutput::Kind::FinalResponse,{});
                    if(accepted)s.bind_final_emissions(data,callback_final,response);
                    data->final_wire=response;data->sealed.store(true,std::memory_order_release);
                }catch(...){data->fail();}
            }
            if(reply_pushes)try{
                if(!accepted||!s.reply_push_slices(reply_pushes,response,true)||(callback_output&&callback_output->receipt->status.load()==WorldCallbackOutputStatus::Failed)){
                    accepted=false;reply_pushes->settle(false);
                }
            }catch(...){accepted=false;reply_pushes->settle(false);}
            if(!accepted&&(s.reply_push_capture||(s.callback_reply_window&&!s.callback_reply_window->pushes.empty())))s.fail_reply_pushes();
            try {s.post_status_work(s.strand,[self,accepted,terminal_ack,response_write,input_lease,normal_response,admission,movement_write,callback_output,callback_final,reply_pushes,response=std::move(response),
                                 count=records.size(),movement_count=requests.size()]() mutable {
                auto& s=*self->impl_;
                [[maybe_unused]] const auto status_admission=self->begin_actor_status_writer();
                const bool owned_handoff=bool(input_lease) || s.has_input_hold() || s.owned_input_retired.load();
                try {
                s.game_busy=false;
                if(s.closing) { s.finish();return; }
                if(s.close_requested.load()) { s.close();return; }
                if(!accepted) { s.fail("Recovered world policy or response rejected");return; }
                if(input_lease && (input_lease->attempt!=response_write ||
                   !s.owned_input_transport_current(input_lease->attempt))) {
                    s.fail("Owned bootstrap exact input continuation handoff changed");return;
                }
                try {
                    if(!response.empty()) {
                        if(response.size()>max_buffer-s.write_bytes || s.writes.size()>=max_writes) {
                            s.fail("World response queue limit");return;
                        }
                        auto bytes=std::make_shared<std::vector<std::uint8_t>>(std::move(response));
                        if(!s.terminal_write_allowed())return;
                        if(response_write && (response_write->receipt->wire!=*bytes ||
                           response_write->receipt->session.lock().get()!=self.get() ||
                           response_write->receipt->status.load()!=WorldResponseWriteStatus::Pending)) {
                            response_write->fail();s.fail("Observed original world response identity mismatch");return;
                        }
                        if(reply_pushes&&!s.reply_push_slices(reply_pushes,*bytes,false)){reply_pushes->settle(false);s.fail("Captured world push final delivery changed");return;}
                        if(callback_final){callback_final->frame=bytes;callback_final->receipt->wire.store(bytes);}
                        if(response_write)response_write->frame=bytes;
                        if(movement_write) {
                            movement_write->frame=bytes;
                            if(!s.movement_frame_current(movement_write,bytes)) {
                                movement_write->fail();s.fail("Movement response retired before FIFO insertion");return;
                            }
                        }
                        if(normal_response) {
                            bool queued=false;
                            {
                                std::lock_guard lock(normal_response->receipt->recipient->sync->mutex);
                                if(s.normal_response_transport_current_locked(normal_response->receipt->recipient) &&
                                   normal_response->receipt->status.load()==NormalWorldResponseStatus::Pending &&
                                   (!admission || (admission->receipt->status.load()==NormalWorldCallbackAdmissionStatus::Pending &&
                                    s.normal_output_transport_current_locked(admission->receipt->source)))) {
                                    Impl::Write output{bytes,{}};output.observed_response=response_write;output.callback_component=callback_final;
                                    output.reply_pushes=reply_pushes;
                                    s.append_write(std::move(output));s.write_bytes+=bytes->size();
                                    auto pending=NormalWorldResponseStatus::Pending;
                                    queued=normal_response->receipt->status.compare_exchange_strong(pending,NormalWorldResponseStatus::Queued);
                                }
                            }
                            if(!queued){normal_response->fail();s.fail("Normal original response retired before FIFO insertion");return;}
                        } else if(admission) {
                            bool queued=false;
                            {
                                std::lock_guard lock(admission->receipt->source->sync->mutex);
                                if(admission->receipt->status.load()==NormalWorldCallbackAdmissionStatus::Pending &&
                                   s.normal_output_transport_current_locked(admission->receipt->source)) {
                                    Impl::Write output{bytes,{}};output.observed_response=response_write;output.callback_component=callback_final;
                                    output.reply_pushes=reply_pushes;
                                    s.append_write(std::move(output));s.write_bytes+=bytes->size();queued=true;
                                }
                            }
                            if(!queued){admission->fail();s.fail("Original callback prefix source retired");return;}
                        } else {
                            Impl::Write output{bytes,{}};output.observed_response=response_write;output.callback_component=callback_final;
                            output.reply_pushes=reply_pushes;
                            s.write_bytes+=bytes->size();s.append_write(std::move(output));
                        }
                        if(movement_write) {
                            s.writes.back().movement_response=movement_write;
                            auto pending=MovementResponseWriteStatus::Pending;
                            if(!s.movement_frame_current(movement_write,bytes) ||
                               !movement_write->receipt->status.compare_exchange_strong(pending,MovementResponseWriteStatus::Queued)) {
                                movement_write->fail();s.fail("Movement response FIFO custody retired");return;
                            }
                        }
                        if(input_lease)s.writes.back().owned_input_lease=input_lease;
                        if(reply_pushes){
                            if(!s.reply_push_slices(reply_pushes,*bytes,false)){reply_pushes->settle(false);s.fail("Captured world push FIFO custody retired");return;}
                            // FIFO acceptance only: after every append branch and
                            // movement/input attachment, outside all source locks.
                            reply_pushes->settle(true);
                            if(!s.writes.empty()&&s.writes.front().bytes==bytes&&!s.close_requested.load())s.write();
                        }else if(s.writes.front().bytes==bytes) s.write();
                    }
                    if(s.character_handlers.world_records)
                        logger("session")->info("session_id={} RECOVERED_WORLD_BATCH_HANDLED records={}; live acceptance UNKNOWN",s.id,count);
                    else
                        logger("session")->info("session_id={} RECOVERED_MOVEMENT_ACCEPTED records={}; live acceptance UNKNOWN",s.id,movement_count);
                    if(terminal_ack && s.native_pk_terminal.load()==terminal_ack)
                        terminal_ack->acknowledged.store(true);
                    s.resume_world_input();
                    // Complete actual callback only, after all throwing work.
                    // Empty response creates no Write; a nonempty true prefix
                    // has already queued above and cannot be rolled back.
                    if(admission) {
                        bool admitted=false;
                        {
                            std::lock_guard lock(admission->receipt->source->sync->mutex);
                            auto pending=NormalWorldCallbackAdmissionStatus::Pending;
                            if(s.normal_output_transport_current_locked(admission->receipt->source))
                                admitted=admission->receipt->status.compare_exchange_strong(pending,NormalWorldCallbackAdmissionStatus::Admitted);
                        }
                        if(!admitted){admission->fail();s.fail("Actual callback admission source retired");return;}
                    }
                    if(callback_output){
                        const auto data=callback_output->receipt;
                        if(!s.callback_output_transport_current(data))data->fail();
                        else data->accepted.store(true);
                        callback_output->accepted.store(true);data->complete();
                        s.release_callback_input_if_ready(data);
                    }
                } catch(...) {
                    if(input_lease || s.has_input_hold() || s.owned_input_retired.load())
                        s.fail_owned_input("Recovered owned world response failed");
                    else s.fail("Recovered world response failed");
                }
                }catch(...) {
                    if(owned_handoff || s.has_input_hold() || s.owned_input_retired.load()) {s.fail_owned_input("Owned bootstrap complete strand handoff failed");return;}
                    throw; // Preserve the old unobserved outer error behavior.
                }
            });}catch(...) {
                if(input_lease) {
                    input_lease->attempt->fail(); // Atomic retirement before preserving old rethrow.
                    try {s.post_status_work(s.strand,[self] {
                        auto& s=*self->impl_;
                [[maybe_unused]] const auto status_admission=self->begin_actor_status_writer();s.game_busy=false;s.fail_owned_input("Owned bootstrap response handoff failed");
                    });}catch(...) {} // Undestroyed/unrun executor convergence remains OPEN.
                }
                if(callback_output)callback_output->receipt->fail();
                if(movement_write)movement_write->fail(); // No posted handoff custody survives a throwing post.
                if(admission)admission->fail(); // Post/drop never leaves retained Data Pending.
                if(normal_response)normal_response->fail(); // Before preserving the existing rethrow/context-abort path.
                if(!terminal_ack)throw; // Existing nonterminal handoff semantics.
                // The actual callback returned; this is failure, never its ACK.
                terminal_ack->ack_handoff_failed.store(true);
                terminal_ack->accepted.store(false);
                terminal_ack->phase.store(NativePkTerminalBarrier::Data::Phase::Failed);
                s.close_requested.store(true);
                try {s.post_status_work(s.strand,[self,terminal_ack] {
                    auto& s=*self->impl_;
                [[maybe_unused]] const auto status_admission=self->begin_actor_status_writer();
                    // No next input job can start before this callback's ACK.
                    // Cleanup must still finish if deadline retired its token.
                    s.game_busy=false;s.fail("Native PK terminal exact ACK handoff failed");
                });}catch(...) {} // Independently armed strand deadline remains.
            }
        });
    }
    void deliver(std::vector<Packet> packets) {
        for (const auto& packet : packets) log_packet(packet, "C2S");
        game_busy = true;
        // Exactly one batch per session is outstanding. The acknowledgement
        // resumes reads and gates disconnect, even if close races this callback.
        post_status_work(game, [self = owner.shared_from_this(), packets = std::move(packets)]() mutable {
            auto& s = *self->impl_;
                [[maybe_unused]] const auto status_admission=self->begin_actor_status_writer();
            bool failed = false;
            for (auto& packet : packets) {
                try { if (s.on_packet) s.on_packet(self, std::move(packet)); }
                catch (...) { failed = true; }
            }
            s.post_status_work(s.strand, [self, failed] {
                auto& s = *self->impl_;
                [[maybe_unused]] const auto status_admission=self->begin_actor_status_writer();
                s.game_busy = false;
                if (failed) s.fail("game packet callback failed");
                else if (s.closing) s.finish();
                else s.read();
            });
        });
    }
    void enqueue(Packet packet, std::shared_ptr<Reservation> reservation) {
        if (closing) return;
        if(is_recovered(mode)) { fail("Fixture packet refused in recovered mode");return; }
        try {
            auto bytes = std::make_shared<std::vector<std::uint8_t>>(protocol.encode(packet));
            if (bytes->empty() || bytes->size() > max_buffer - write_bytes) {
                fail("encoded write queue limit"); return;
            }
            log_packet(packet, "S2C");
            if(!terminal_write_allowed())return;
            write_bytes += bytes->size();
            append_write({std::move(bytes), std::move(reservation)});
            if (writes.size() == 1) write();
        } catch (const std::exception& e) { fail(e.what()); }
        catch (...) { fail("protocol encode failed"); }
    }
    void write(std::shared_ptr<NativePkReturnPublication::Work> carried={}) {
        if(writes.empty())return;
        if(native_logout_ack&&writes.front().bytes==native_logout_ack&&(!disconnect_cleanup_done.load()||!disconnect_cleanup_clean.load()||common_world_cleanup_failed.load()||
           native_logout_phase!=NativeLogoutPhase::AckQueued||(owner.native_channel_&&!owner.native_channel_->live_.load()))){
            fail("Native logout acknowledgment source retired before write");return;
        }
        if(!reply_push_sources_live(writes.front().reply_pushes)){
            fail("Captured world push source retired before actual write");return;
        }
        if(writes.front().qualified_source_live&&!writes.front().qualified_source_live->load()){
            fail("Qualified world push source retired before actual write");return;
        }
        if(writes.front().held){
            if(carried){
                const auto pending=writes.front().pending_return_continuation.lock();
                if(!pending||pending->frame!=writes.front().bytes||(pending->work&&pending->work!=carried)){
                    if(const auto output=carried->data->output.lock())Session::fail_native_pk_return_output(output);return;
                }
                pending->work=std::move(carried); // Multiple older held prefixes retain actual task custody.
            }
            return;
        }
        const auto marked=writes.front().return_output;
        if(marked){
            const auto output=marked->cohort.lock();const auto publication=output?output->publication.load():nullptr;
            if(!output||!publication||!carried||carried->data!=publication||
               publication->phase.load()!=NativePkReturnPublicationStatus::Released||
               marked->recipient>=publication->progress.size()||marked->recipient>=output->recipients.size()||
               marked->ordinal>=output->recipients[marked->recipient]->frames.size()||
               !publication->progress[marked->recipient]->released.load()||
               !native_pk_return_publication_transport_current(publication,marked->recipient)||
               marked->ordinal!=publication->progress[marked->recipient]->next.load()||
               marked->frame!=output->recipients[marked->recipient]->frames[marked->ordinal]||
               writes.front().bytes!=marked->frame->bytes||writes.front().status_seal!=marked->frame->status_seal||
               !Session::actor_status_frame_matches(writes.front().status_seal,writes.front().bytes,owner,marked->ordinal,*output->plan)){
                if(output)Session::fail_native_pk_return_output(output);else fail("Return frame lost exact cohort");return;
            }
        }
        auto bytes = writes.front().bytes;
        const auto qualified_source_live=writes.front().qualified_source_live;
        const auto captured_pushes=writes.front().reply_pushes;
        const auto movement_marker=writes.front().movement_response;
        if(movement_marker && (!movement_frame_current(movement_marker,bytes) || writes.front().held ||
           movement_marker->receipt->status.load()!=MovementResponseWriteStatus::Queued)) {
            movement_marker->fail();fail("Movement response lost exact FIFO front");return;
        }
        const auto outward_marker=writes.front().outward_status;
        const auto outward_seal=outward_marker?std::optional<TaiwanActorStatusPublication::FrameSeal>{outward_marker->frame->seal}:
            std::optional<TaiwanActorStatusPublication::FrameSeal>{};
        if(outward_marker&&!outward_status_released_current(outward_marker,*outward_seal,bytes)){
            outward_marker->frame->revoke();fail("Outward status frame lost exact released source");return;
        }
        const auto initial_ticket=writes.front().initial_entry;
        const bool initial_status=initial_ticket&&bool(initial_ticket->member->identity->status);
        const auto initial_seal=initial_status?initial_ticket->member->status_seal:
            std::optional<TaiwanActorStatusPublication::FrameSeal>{};
        if(initial_status&&!initial_entry_released_current(initial_ticket,initial_seal,bytes)){
            initial_ticket->member->identity->revoke();fail("Initial status frame lost exact released cohort");return;
        }
        const auto callback_component=writes.front().callback_component;
        const auto status_seal=writes.front().status_seal;
        const auto status_writer=writes.front().status_writer;
        // The completion owns the active buffer even when fail() clears the queue.
        const bool owned_initiation=has_input_hold() || owned_input_retired.load();
        std::shared_ptr<ActiveWriteContinuation> continuation;
        try {
        continuation=std::make_shared<ActiveWriteContinuation>(carried,bytes);
        active_write_continuation=continuation;
        owner.invalidate_actor_status_writes(); // Final exhaustive socket sink.
        auto completion=
            [self = owner.shared_from_this(), bytes,marked,continuation,status_seal,initial_ticket,initial_status,initial_seal,outward_marker,outward_seal,movement_marker,callback_component](const asio::error_code& ec, std::size_t transferred) {
                auto& s = *self->impl_;
                [[maybe_unused]] const auto status_admission=self->begin_actor_status_writer();
                const bool owned_completion=s.has_input_hold() || s.owned_input_retired.load();
                try {
                if(outward_marker&&!s.outward_status_released_current(outward_marker,*outward_seal,bytes)){
                    outward_marker->frame->revoke();s.fail("Outward status completion lost exact frame");return;
                }
                // Both domains retain their pure exact markers/seals directly,
                // even when failure already cleared the FIFO.
                if(initial_status&&!s.initial_entry_released_current(initial_ticket,initial_seal,bytes)){
                    initial_ticket->member->identity->revoke();s.fail("Initial status completion lost exact frame");return;
                }
                const auto sealed_output=marked?marked->cohort.lock():nullptr;
                if(status_seal&&(!sealed_output||status_seal!=marked->frame->status_seal||
                   !Session::actor_status_frame_matches(status_seal,bytes,*self,marked->ordinal,*sealed_output->plan))){
                    if(sealed_output)Session::fail_native_pk_return_output(sealed_output);
                    return;
                }
                if(movement_marker && (!s.movement_frame_current(movement_marker,bytes) || ec ||
                   transferred!=bytes->size() || s.finished || s.writes.empty() || s.writes.front().held ||
                   s.writes.front().movement_response!=movement_marker || s.writes.front().bytes!=bytes ||
                   s.writes.front().bytes.owner_before(bytes) || bytes.owner_before(s.writes.front().bytes) ||
                   movement_marker->receipt->status.load()!=MovementResponseWriteStatus::Queued)) {
                    movement_marker->fail();s.fail("Movement response actual full write custody failed");return;
                }
                if (s.finished || s.writes.empty()) return;
                const auto publication=continuation->work?continuation->work->data:nullptr;
                const auto output=publication?publication->output.lock():nullptr;
                if(publication&&(!output||s.closing||publication->phase.load()!=NativePkReturnPublicationStatus::Released||
                   !s.native_pk_return_publication_transport_current(publication,
                        output->plan->sessions[0].get()==self.get()?0u:
                        output->plan->sessions[1].get()==self.get()?1u:
                        std::size_t(std::find_if(output->recipients.begin(),output->recipients.end(),
                            [&](const auto& recipient){return recipient->session==self;})-output->recipients.begin())))){
                    if(output)Session::fail_native_pk_return_output(output);return;
                }
                if (ec) { s.fail(ec.message()); return; }
                if(outward_marker&&transferred!=bytes->size()){
                    outward_marker->frame->revoke();s.fail("Outward status completion was not whole");return;
                }
                if(initial_status&&transferred!=bytes->size()){
                    initial_ticket->member->identity->revoke();s.fail("Initial status completion was not a whole frame");return;
                }
                if(marked&&(!publication||!output||s.writes.front().return_output!=marked||s.writes.front().held||
                   s.writes.front().bytes!=bytes||bytes!=marked->frame->bytes||transferred!=bytes->size()||
                   s.writes.front().status_seal!=status_seal||status_seal!=marked->frame->status_seal||
                   marked->recipient>=output->recipients.size()||marked->ordinal>=output->recipients[marked->recipient]->frames.size()||
                   output->recipients[marked->recipient]->session!=self||
                   output->recipients[marked->recipient]->frames[marked->ordinal]!=marked->frame||
                   publication->progress[marked->recipient]->next.load()!=marked->ordinal)){
                    if(output)Session::fail_native_pk_return_output(output);else s.fail("Return write lost exact publication");return;
                }
                if(const auto entry=s.writes.front().normal_entry) {
                    // Strand-owned exact Write; do not read game-owned IDs or
                    // change legacy write/close policy for passive metadata.
                    const bool exact=!s.writes.front().held && s.writes.front().world_entry &&
                        s.writes.front().bytes==bytes && transferred==bytes->size() &&
                        bytes->size()==entry->frame.size() && s.normal_entry.load()==entry &&
                        entry->session.lock().get()==self.get() && !entry->retired.load() &&
                        std::equal(bytes->begin(),bytes->end(),entry->frame.begin());
                    if(exact)entry->written.store(true);else entry->retired.store(true);
                    // Physical Written is historical. Sender eligibility is a
                    // separate monotonic source and cannot revive after conflict.
                    (void)entry->world_identity_sender.complete_original(exact);
                }
                if(const auto attempt=s.writes.front().observed_world) {
                    if(s.writes.front().held || s.writes.front().bytes!=bytes || attempt->frame!=bytes ||
                       transferred!=bytes->size() || !attempt->receipt ||
                       attempt->receipt->session.lock().get()!=self.get()) {
                        s.fail("Observed world actual write identity mismatch");return;
                    }
                    auto pending=WorldRecordsWriteStatus::Pending;
                    if(!attempt->receipt->status.compare_exchange_strong(pending,WorldRecordsWriteStatus::Written)) {
                        s.fail("Observed world write already retired");return;
                    }
                }
                if(const auto attempt=s.writes.front().observed_response) {
                    if(s.closing || s.close_requested.load())attempt->fail();
                    else {
                        if(s.writes.front().held || s.writes.front().bytes!=bytes || attempt->frame!=bytes ||
                           transferred!=bytes->size() || !attempt->receipt ||
                           attempt->receipt->session.lock().get()!=self.get() || attempt->receipt->wire!=*bytes) {
                            s.fail("Observed original world response actual write mismatch");return;
                        }
                        auto pending=WorldResponseWriteStatus::Pending;
                        if(!attempt->receipt->status.compare_exchange_strong(pending,WorldResponseWriteStatus::Written)) {
                            s.fail("Observed original world response already retired");return;
                        }
                    }
                }
                if(const auto view=s.writes.front().battle_self_view){
                    const auto response=s.writes.front().observed_response;
                    const bool exact=response && response->receipt && view->source==response->receipt &&
                        response->receipt->status.load()==WorldResponseWriteStatus::Written &&
                        !s.writes.front().held && s.writes.front().bytes==bytes && view->frame==bytes &&
                        transferred==bytes->size() && view->session.lock().get()==self.get() &&
                        view->session_id==s.id && self->state()==SessionState::InBattle &&
                        self->battle_generation()==view->battle && s.battle_self_view_source.load()==view &&
                        s.battle_self_view_fence.current(view->epoch) &&
                        s.battle_self_view_intents.current(view->intent);
                    if(!view->completion.complete(exact)){
                        auto expected=view;s.battle_self_view_source.compare_exchange_strong(expected,{});
                    }
                }
                if(s.writes.front().advertisement) {
                    const auto observed=s.writes.front().advertisement;
                    if(s.writes.front().bytes!=bytes || observed->session!=s.id || observed->wire!=*bytes || s.written_advertisement) {
                        s.fail("Native account advertisement write observation mismatch");return;
                    }
                    s.written_advertisement=observed;
                }
                if(s.writes.front().native_list) {
                    const auto delivery=s.writes.front().native_list;
                    if(s.writes.front().held || s.writes.front().bytes!=bytes || s.active_native_list!=delivery ||
                       bytes->size()!=delivery->frame.size() || !std::equal(bytes->begin(),bytes->end(),delivery->frame.begin())) {
                        s.fail("Native list actual write identity mismatch");return;
                    }
                    self->recovered_native_character_list_written_.store(delivery);
                    s.complete_native_list(delivery,true);
                }
                if(s.writes.front().native_battle) {
                    const auto pending=s.writes.front().native_battle;
                    if(s.writes.front().held || s.writes.front().bytes!=bytes ||
                       pending->completing.load() || !s.native_battle_current(pending) ||
                       (pending->pk_entry && transferred!=bytes->size())) {
                        s.fail("Native battle actual write identity mismatch");return;
                    }
                    self->native_battle_skill_written_.store(pending->delivery);
                    s.complete_native_battle(pending,true);
                }
                if(const auto data=s.writes.front().native_pk) {
                    if(s.writes.front().held || s.writes.front().bytes!=bytes ||
                       bytes!=data->frame || transferred!=bytes->size() ||
                       data->phase.load()!=NativePkEntryHold::Data::Phase::Released ||
                       !s.native_pk_transport_current(data,true)) {
                        s.fail("Native PK exact full write identity mismatch");return;
                    }
                    data->phase.store(NativePkEntryHold::Data::Phase::Written);
                    s.complete_native_pk(data,true);
                }
                s.last_real_protocol_activity=now_ms();
                if(is_recovered(s.mode) && !s.recovered_hello_written) {
                    s.recovered_hello_written=true;
                    if(s.mode==ProtocolMode::God2PostSeed && s.post_seed_state==RecoveredPostSeed::State::Connected)
                        s.post_seed_state=RecoveredPostSeed::State::SeedSent;
                    logger("session")->info("session_id={} GOD2_INITIAL_S2C_SENT length={}",s.id,bytes->size());
                }
                if(s.mode==ProtocolMode::God2PostSeed && bytes->size()==5) {
                    s.post_seed_state=RecoveredPostSeed::State::PostSeedResponseSent;
                    logger("session")->info("session_id={} GOD2_POST_SEED_SENT length=5; client acceptance unconfirmed",s.id);
                }
                if(is_credential_mode(s.mode) && bytes->size()==176) {
                    s.c2s0002_state=C2S0002State::ResponseSent;
                    logger("session")->info("session_id={} S2C0003_SENT length=176 opcode=29; client acceptance unconfirmed",s.id);
                }
                if(is_terminal_mode(s.mode) && bytes->size()==20) {
                    s.c2s0002_state=C2S0002State::TerminalSent;
                    logger("session")->info("session_id={} LOGIN_TERMINAL_SENT length=20 opcode=10; acceptance unconfirmed",s.id);
                }
                if(is_server_list_mode(s.mode) && (bytes->size()==8 || (!s.character_routes.empty() && bytes->size()==s.character_routes.size()))) {
                    s.c2s0002_state=C2S0002State::ServerListSent;
                    logger("session")->info("session_id={} SERVER_LIST_SENT entry_id=0 length={} character_routes={}",s.id,bytes->size(),!s.character_routes.empty());
                }
                if(s.mode==ProtocolMode::God2CharacterConnection && bytes->size()==128) {
                    logger("session")->info("session_id={} CHARACTER_BOOTSTRAP_SENT length=128 opcode=31; opaque payload candidate; current client acceptance UNKNOWN",s.id);
                }
                if(s.writes.front().world_entry) {
                    logger("session")->info("session_id={} WORLD_ENTRY_CANDIDATE_SENT length=40 opcode=42; current client world acceptance UNKNOWN",s.id);
                }
                if(s.mode==ProtocolMode::God2LegacyCharacterListCandidate && bytes->size()==78) {
                    logger("session")->info("session_id={} LEGACY_CHARACTER_LIST_CANDIDATE_SENT length=78 opcode=7; current client acceptance UNKNOWN",s.id);
                }
                if(status_seal&&!Session::actor_status_frame_matches(status_seal,bytes,*self,marked->ordinal,*output->plan)){
                    Session::fail_native_pk_return_output(output);return;
                }
                if(outward_marker){
                    if(!s.outward_status_released_current(outward_marker,*outward_seal,bytes)){
                        outward_marker->frame->revoke();s.fail("Outward status retired before completion accounting");return;
                    }
                    auto released=OutwardStatusFrame::Phase::Released;
                    if(!outward_marker->frame->phase.compare_exchange_strong(released,OutwardStatusFrame::Phase::Written)){
                        outward_marker->frame->revoke();s.fail("Outward status completion repeated");return;
                    }
                }
                if(initial_status){
                    if(!s.initial_entry_released_current(initial_ticket,initial_seal,bytes)){
                        initial_ticket->member->identity->revoke();s.fail("Initial status retired before completion accounting");return;
                    }
                    auto expected=initial_ticket->member->ordinal;
                    if(!initial_ticket->member->identity->status->next.compare_exchange_strong(expected,expected+1)){
                        initial_ticket->member->identity->revoke();s.fail("Initial status completion ordinal changed");return;
                    }
                    initial_ticket->member->completed.store(true);
                }
                if(movement_marker) {
                    // Exact actual whole local write, before FIFO ownership is
                    // released. No client ACK or next-input permission follows.
                    auto queued=MovementResponseWriteStatus::Queued;
                    if(!s.movement_frame_current(movement_marker,bytes) ||
                       !movement_marker->receipt->status.compare_exchange_strong(queued,MovementResponseWriteStatus::Written)) {
                        movement_marker->fail();s.fail("Movement response completion already retired");return;
                    }
                }
                if(callback_component&&(!callback_component->receipt||s.writes.front().callback_component!=callback_component||
                   callback_component->frame!=bytes||s.writes.front().bytes!=bytes||s.writes.front().held||
                   transferred!=bytes->size()||!s.callback_output_transport_current(callback_component->receipt->cohort.lock()))){
                    if(const auto data=callback_component->receipt->cohort.lock())data->fail();
                    s.fail("Callback component actual write identity mismatch");return;
                }
                const auto completed_input_lease=s.writes.front().owned_input_lease;
                s.write_bytes -= s.writes.front().bytes->size();
                s.writes.pop_front();
                if(outward_marker)outward_marker->frame->identity->active.store(false); // Actual full write only.
                if(initial_status){
                    const auto& context=initial_ticket->member->identity->status;
                    if(context->next.load()==context->frame_count.load()){
                        context->completed.store(true);context->retire(); // LAST actual frame completion, not queue release.
                    }
                }
                if(marked){
                    auto expected=marked->ordinal;
                    if(!publication->progress[marked->recipient]->next.compare_exchange_strong(expected,marked->ordinal+1)){
                        Session::fail_native_pk_return_output(output);return;
                    }
                }
                if(s.native_pk_terminal.load())s.stage_native_pk_terminal();
                auto next_work=continuation->work;
                if(marked&&marked->ordinal+1==output->recipients[marked->recipient]->frames.size())
                    next_work.reset(); // Unrelated suffix handlers must not retain this pending publication.
                if (!s.writes.empty()) s.write(std::move(next_work));
                else if (s.closing) s.finish();
                else if(s.resume_after_login_write) {
                    s.resume_after_login_write=false;
                    s.read();
                }
                // Every original marker/log/pop/queue operation above completed
                // before the exact owned response releases a single continuation.
                if(completed_input_lease)s.release_owned_input(completed_input_lease);
                if(marked&&publication->progress[marked->recipient]->next.load()==output->recipients[marked->recipient]->frames.size())
                    s.complete_native_pk_return_publication_recipient(continuation->work,marked->recipient);
                if(callback_component){
                    auto pending=WorldCallbackOutputStatus::Pending;
                    if(!callback_component->receipt->status.compare_exchange_strong(pending,WorldCallbackOutputStatus::Written)){
                        if(const auto data=callback_component->receipt->cohort.lock())data->fail();
                        s.fail("Callback component already retired");return;
                    }
                    callback_component->completed.store(true);
                    if(const auto data=callback_component->receipt->cohort.lock()){
                        data->complete();s.release_callback_input_if_ready(data);
                    }
                }
                if(s.native_logout_phase==NativeLogoutPhase::Draining)s.advance_native_logout();
                }catch(...) {
                    if(movement_marker){movement_marker->fail();s.fail("Movement response completion failed");return;}
                    if(outward_marker){outward_marker->frame->revoke();s.fail("Outward status completion failed");return;}
                    if(initial_status){
                        initial_ticket->member->identity->revoke();s.fail("Initial status completion failed");return;
                    }
                    if(continuation->work){if(const auto output=continuation->work->data->output.lock())
                        Session::fail_native_pk_return_output(output);return;}
                    if(owned_completion || s.has_input_hold() || s.owned_input_retired.load()) {s.fail_owned_input("Owned bootstrap FIFO completion failed");return;}
                    throw; // Preserve the original unobserved completion path.
                }
            };
        auto initiate=[&](auto handler) {
            // Finish handler wrapping/executor binding/buffer construction FIRST.
            // This is the final pure version cut immediately before socket initiation.
            auto bound=asio::bind_executor(strand,std::move(handler));
            const auto buffer=asio::buffer(*bytes);
            if(outward_marker&&!outward_status_released_current(outward_marker,*outward_seal,bytes))
                throw std::logic_error("Outward owned-status retired before async_write");
            if(initial_status&&!initial_entry_released_current(initial_ticket,initial_seal,bytes))
                throw std::logic_error("Initial owned-status retired before async_write");
            const auto sealed_output=marked?marked->cohort.lock():nullptr;
            if(status_seal&&(!sealed_output||status_seal!=marked->frame->status_seal||
               !Session::actor_status_frame_matches(status_seal,bytes,owner,marked->ordinal,*sealed_output->plan)))
                throw std::logic_error("Return owned-status retired before async_write");
            if(movement_marker && (!movement_frame_current(movement_marker,bytes) || writes.empty() ||
               writes.front().movement_response!=movement_marker || writes.front().bytes!=bytes || writes.front().held ||
               movement_marker->receipt->status.load()!=MovementResponseWriteStatus::Queued))
                throw std::logic_error("Movement response retired before async_write");
            if(qualified_source_live&&!qualified_source_live->load())throw std::logic_error("Qualified world source retired before async_write");
            if(!reply_push_sources_live(captured_pushes))throw std::logic_error("Captured world source retired before async_write");
            if(native_logout_ack&&bytes==native_logout_ack&&(native_logout_phase!=NativeLogoutPhase::AckQueued||!disconnect_cleanup_done.load()||!disconnect_cleanup_clean.load()||common_world_cleanup_failed.load()||
               (owner.native_channel_&&!owner.native_channel_->live_.load())))throw std::logic_error("Native logout source retired before async_write");
            asio::async_write(socket,buffer,std::move(bound));
        };
        if(status_writer)initiate(retain_actor_status_writer(status_writer,std::move(completion)));
        else initiate(std::move(completion)); // Exact original plain handler without a ticket.
        }catch(...) {
            if(movement_marker){movement_marker->fail();fail("Movement response write initiation failed");return;}
            if(outward_marker){outward_marker->frame->revoke();fail("Outward status write initiation failed");return;}
            if(initial_status){
                initial_ticket->member->identity->revoke();fail("Initial status write initiation failed");return;
            }
            if(continuation&&continuation->work){if(const auto output=continuation->work->data->output.lock())
                Session::fail_native_pk_return_output(output);return;}
            if(marked){if(const auto output=marked->cohort.lock())Session::fail_native_pk_return_output(output);return;}
            if(carried){if(const auto output=carried->data->output.lock())Session::fail_native_pk_return_output(output);return;}
            if(owned_initiation || has_input_hold() || owned_input_retired.load()) {fail_owned_input("Owned bootstrap async write initiation failed");return;}
            throw; // Original unobserved initiation behavior.
        }
    }
    void close() {
        if(native_logout_phase!=NativeLogoutPhase::None&&native_logout_phase!=NativeLogoutPhase::AckQueued)native_logout_phase=NativeLogoutPhase::Failed;
        for(const auto& queued:writes)if(queued.movement_response)queued.movement_response->fail();
        retire_outward_status_writes();
        retire_initial_status_writes(); // Pure revoke BEFORE any cleanup/queue removal, including Released.
        owner.retire_actor_status_incarnation();
        owner.invalidate_actor_status_writes();
        if(const auto final=native_pk_return_finalisation_history.load();final&&!final->returned_notified.load())
            Session::fail_native_pk_return_finalisation(final);
        const bool was_closing=closing;
        retire_owned_input();
        if (was_closing) return; // First opted close still executes ALL original cleanup.
        closing = true;
        close_requested.store(true);
        for(const auto& queued:writes)if(queued.observed_response)queued.observed_response->fail();
        retire_normal_initialization();
        retire_native_pk_terminal();
        if(native_pk_pending.load()) {fail("Native PK closed while entry pending");return;}
        if(native_battle_pending.load()) {fail("Native battle closed while publication pending");return;}
        if(active_native_list) {fail("Native list closed while delivery pending");return;}
        cancel_common_ready();
        world_pending_records.clear();skill_deadline.reset();native_skill_generation.reset();
        asio::error_code ignored;
        socket.shutdown(asio::ip::tcp::socket::shutdown_receive, ignored);
        arm_timer(close_timeout);
        finish();
    }
    void fail(const std::string& reason) {
        if(native_logout_phase!=NativeLogoutPhase::None)native_logout_phase=NativeLogoutPhase::Failed;
        // Pure selected movement retirement precedes old callbacks/logging.
        // Written remains a historical physical fact after later failure.
        for(const auto& queued:writes)if(queued.movement_response)queued.movement_response->fail();
        retire_outward_status_writes();
        retire_initial_status_writes();
        owner.retire_actor_status_incarnation();
        [[maybe_unused]] const auto status_admission=owner.begin_actor_status_writer();
        owner.invalidate_actor_status_writes();
        if(const auto final=native_pk_return_finalisation_history.load();final&&!final->returned_notified.load())
            Session::fail_native_pk_return_finalisation(final);
        if(const auto output=native_pk_return_output.load())Session::fail_native_pk_return_output(output);
        if(const auto pair=native_pk_return.load())Session::fail_native_pk_return_reservation(pair);
        retire_owned_input(); // Opt-in socket/atomic retirement precedes potentially throwing logging.
        if (finished) return;
        if (auto log = logger("session")) log->debug("session_id={} remote_ip={} closing: {}", id, ip, reason);
        closing = true;
        close_requested.store(true);
        for(const auto& queued:writes)if(queued.observed_response)queued.observed_response->fail();
        retire_normal_initialization();
        retire_native_pk_terminal();
        cancel_common_ready();
        world_pending_records.clear();skill_deadline.reset();native_skill_generation.reset();
        asio::error_code ignored;
        socket.close(ignored);
        native_pk_output_staged.reset();native_pk_output_reservation.reset();
        if(const auto pending=native_pk_pending.load())complete_native_pk(pending,false);
        if(const auto pending=native_battle_pending.load())complete_native_battle(pending,false);
        if(active_native_list)complete_native_list(active_native_list,false);
        writes.clear();
        write_bytes = 0;
        finish();
    }
    void start_disconnect_cleanup() {
        if(disconnect_cleanup_started)return;
        disconnect_cleanup_started=true;
        post_status_work(game, [self = owner.shared_from_this()] {
            auto& s = *self->impl_;
            [[maybe_unused]] const auto status_admission=self->begin_actor_status_writer();
            // Diagnostics cannot skip any cleanup or its transport receipt.
            auto report=[&](const char* message) noexcept {
                try{if(auto log=logger("session"))log->error("session_id={} {}",s.id,message);}catch(...){}
            };
            try{if(auto log=logger("session"))log->info("session_id={} DISCONNECT_GAME_ENTER",s.id);}catch(...){}
            const auto original_account=self->account_id,original_character=self->character_id;
            const auto original_phase=self->state();const auto original_battle=self->battle_generation();
            const auto original_current=[&]{return self->account_id==original_account&&self->character_id==original_character&&
                self->state()==original_phase&&self->battle_generation()==original_battle;};
            bool clean=!s.common_world_cleanup_failed.load();
            {
                auto terminal_finish=std::exchange(s.common_world_terminal_finish,{});
                {
                    // Exchange every callback once before entering a supplier.
                    // The original common owner survives application disconnect.
                    auto terminal_begin=std::exchange(s.common_world_terminal_begin,{});
                    auto disconnect=std::exchange(s.on_disconnect,{});
                    auto cleanup=std::exchange(s.common_world_cleanup,{});
                    auto abandon=std::exchange(s.character_handlers.common_world_lifecycle_abandon,{});
                    if(self->native_channel_bound()&&s.native_logout_terminal.load()&&s.character_handlers.common_world_lifecycle&&
                       (!terminal_begin||!terminal_finish)){
                        clean=false;report("native channel logout lacks paired terminal claim hooks");
                    }
                    try {if(terminal_begin)terminal_begin();}catch(...) {clean=false;report("common world terminal begin failed");}
                    try {if(disconnect)disconnect(self);}catch(...) {clean=false;report("disconnect callback failed");}
                    try {if(cleanup)cleanup();}catch(...) {clean=false;report("common world cleanup failed");}
                    try {if(abandon)abandon(*self);}catch(...) {clean=false;report("common world lifecycle abandon failed");}
                }
                if(!original_current()){clean=false;report("disconnect source identity changed during cleanup");}
                if(s.common_world_cleanup_failed.load())clean=false;
                try {if(terminal_finish&&!terminal_finish(clean)){clean=false;report("common world terminal settlement refused");}}
                catch(...) {clean=false;report("common world terminal finish failed");}
            }
            // Finish is destroyed on GAME before the final identity/result cut.
            if(!original_current()){clean=false;report("disconnect source identity changed during terminal settlement");}
            if(s.common_world_cleanup_failed.load())clean=false;
            // Pure results publish only after every callback copy died on GAME.
            // An unrun GAME post cannot publish this result; a dropped NET
            // continuation below cannot publish successful03.
            s.disconnect_cleanup_clean.store(clean);s.disconnect_cleanup_done.store(true);
            try{if(auto log=logger("session"))log->info("session_id={} DISCONNECT_GAME_EXIT",s.id);}catch(...){}
            s.post_status_work(s.strand,[self]{
                auto& state=*self->impl_;
                [[maybe_unused]] const auto status_admission=self->begin_actor_status_writer();
                state.advance_native_logout();state.finish();
            });
        });
    }
    void advance_native_logout() {
        if(native_logout_phase==NativeLogoutPhase::Draining){
            if(closing||close_requested.load()||finished){native_logout_phase=NativeLogoutPhase::Failed;return;}
            if(game_busy||!writes.empty()||native_battle_pending.load()||native_pk_pending.load()||native_pk_terminal.load())return;
            native_logout_phase=NativeLogoutPhase::Cleaning;native_logout_terminal.store(true);
            start_disconnect_cleanup();return;
        }
        if(native_logout_phase!=NativeLogoutPhase::Cleaning||!disconnect_cleanup_done.load())return;
        if(closing||close_requested.load()||finished||(owner.native_channel_&&!owner.native_channel_->live_.load())){
            native_logout_phase=NativeLogoutPhase::Failed;if(!closing)close();return;
        }
        if(!disconnect_cleanup_clean.load()||common_world_cleanup_failed.load()){fail("Native logout GAME cleanup failed");return;}
        if(game_busy||!writes.empty()||native_battle_pending.load()||native_pk_pending.load()||native_pk_terminal.load()){
            fail("Native logout terminal drain changed during cleanup");return;
        }
        native_logout_ack=std::make_shared<std::vector<std::uint8_t>>(
            RecoveredWorldFrame::encode(std::array<std::uint8_t,3>{3,0,0}));
        native_logout_phase=NativeLogoutPhase::AckQueued;
        append_write({native_logout_ack,{}});write_bytes+=native_logout_ack->size();
        try{if(auto log=logger("session"))log->info("session_id={} NATIVE_LOGOUT_ACK_QUEUED reason={}",id,native_logout_reason);}catch(...){}
        write();close(); // Existing03 only, once, after actual GAME cleanup.
    }
    void finish() {
        if(!finished){
            if(!closing||game_busy||!writes.empty()||native_battle_pending.load()||native_pk_pending.load()||native_pk_terminal.load())return;
            finished=true;
            timeout_policy=SessionTimeoutPolicy::Normal;
            hold_timer.cancel();native_pk_timer.cancel();native_pk_terminal_timer.cancel();
            try {hold_status();}catch(...){}
            owner.state_.store(SessionState::Disconnected);
            asio::error_code ignored;timer.cancel();
            socket.shutdown(asio::ip::tcp::socket::shutdown_both,ignored);socket.close(ignored);
        }
        start_disconnect_cleanup();
        if(!disconnect_cleanup_done.load()||disconnect_completion_posted)return;
        disconnect_completion_posted=true;
        post_status_work(game,[self=owner.shared_from_this()]{
            auto& state=*self->impl_;
            [[maybe_unused]] const auto status_admission=self->begin_actor_status_writer();
            // SessionManager removal is downstream of BOTH final socket close
            // and the exact all-attempted GAME cleanup, never the earlier03.
            if(auto complete=std::exchange(state.disconnect_complete,{}))complete(self,state.disconnect_cleanup_clean.load()&&!state.common_world_cleanup_failed.load());
            state.game_work.reset();state.network_work.reset();
        });
    }
};

Session::Session(asio::ip::tcp::socket socket, asio::any_io_executor game_executor,
                 std::uint64_t id, bool packet_dump, PacketHandler on_packet,
                 DisconnectHandler on_disconnect,ProtocolMode mode,RecoveredLoginHandler recovered_login,RecoveredCharacterHandlers characters,
                 std::vector<std::uint8_t> character_routes,std::shared_ptr<const NativeTaiwanChannelBinding> native_channel,
                 DisconnectCompletion disconnect_complete)
    : impl_(std::make_unique<Impl>(*this, std::move(socket), std::move(game_executor), id,
                                  packet_dump, std::move(on_packet), std::move(on_disconnect),mode,std::move(recovered_login),std::move(characters),std::move(character_routes),std::move(disconnect_complete))),
      native_channel_(std::move(native_channel)),native_channel_acceptance_([&]()->std::optional<NativeChannelAcceptance>{
          if(!native_channel_)return {};
          if(mode!=ProtocolMode::God2CharacterConnection||!id||!impl_->character_handlers.native_select)
              throw std::invalid_argument("Native channel requires an actual authenticated G source");
          const auto local=impl_->socket.local_endpoint();
          if(!native_channel_->accepts(local))throw std::invalid_argument("Accepted socket does not match its native channel listener");
          return NativeChannelAcceptance{this,id,local};
      }()) {
    // Constructor body: all Session atomics now exist. This passive observation
    // never changes legacy/authentication/socket acceptance on lookup failure.
    if(impl_->character_handlers.native_select && mode==ProtocolMode::God2CharacterConnection) {
        try {
            asio::error_code ec;
            const auto local=impl_->socket.local_endpoint(ec);
            if(!ec && local.address().is_v4() && local.port())
                recovered_native_local_endpoint_.store(std::make_shared<const NativeLocalEndpoint>(
                    NativeLocalEndpoint{id,mode,local.address().to_v4().to_bytes(),local.port()}));
        } catch(...) {if(native_channel_)throw;}
        if(native_channel_&&!recovered_native_local_endpoint_.load())
            throw std::invalid_argument("Channel socket has no exact native local-endpoint observation");
        if(native_channel_&&(!native_channel_acceptance_||!native_channel_->accepts(native_channel_acceptance_->local)))
            throw std::invalid_argument("Channel listener retired during accepted-socket construction");
    }
}
bool Session::native_channel_bound() const noexcept {return bool(native_channel_);}
std::optional<std::uint8_t> Session::native_channel_ordinal() const noexcept {
    return native_channel_?std::optional{native_channel_->channel_}:std::nullopt;
}
bool Session::native_channel_binding_current() const {
    return !native_channel_||native_channel_allows_destination(native_channel_->group_,native_channel_->channel_);
}
bool Session::native_channel_allows_presence(const std::shared_ptr<SharedWorldPresence>& presence) const {
    if(!native_channel_)return true;
    return native_channel_->matches_presence(presence)&&native_channel_acceptance_&&
        native_channel_acceptance_->session==this&&native_channel_acceptance_->id==id()&&
        native_channel_->accepts(native_channel_acceptance_->local);
}
bool Session::native_channel_allows_destination(std::uint8_t group,std::uint8_t subgroup) const {
    if(!native_channel_)return true;
    return native_channel_->matches_destination(group,subgroup)&&native_channel_acceptance_&&
        native_channel_acceptance_->session==this&&native_channel_acceptance_->id==id()&&
        native_channel_->accepts(native_channel_acceptance_->local);
}
Session::~Session() {
    retire_actor_status_incarnation();
    destruction_status_writer_=begin_actor_status_writer();
    invalidate_actor_status_writes();
}
bool Session::actor_status_incarnation_matches(const TaiwanActorStatusIncarnationSource::Token& token) const noexcept {
    if(actor_status_incarnation_closed_.load(std::memory_order_acquire))return false;
    const auto retained=actor_status_incarnation_.load(std::memory_order_acquire);
    return retained&&*retained==token&&!actor_status_incarnation_closed_.load(std::memory_order_acquire);
}
void Session::retire_actor_status_incarnation() noexcept {
    // Independent early latch: legacy close_requested is published later.
    actor_status_incarnation_closed_.store(true,std::memory_order_release);
    if(const auto token=actor_status_incarnation_.exchange({},std::memory_order_acq_rel))token->retire();
}
bool Session::bind_actor_status_incarnation(TaiwanActorStatusIncarnationSource::Token token) {
    if(actor_status_incarnation_closed_.load(std::memory_order_acquire)||closing()||!token.can_bind(*this))return false;
    auto expected=actor_status_incarnation_.load(std::memory_order_acquire);
    if(expected&&*expected==token)return token.can_bind(*this)&&!actor_status_incarnation_closed_.load(std::memory_order_acquire);
    if(expected&&expected->live())return false; // Never replace another live private owner.
    const auto retained=std::make_shared<const TaiwanActorStatusIncarnationSource::Token>(token);
    if(actor_status_incarnation_closed_.load(std::memory_order_acquire)||closing()||!token.can_bind(*this))return false;
    if(!actor_status_incarnation_.compare_exchange_strong(expected,retained,std::memory_order_acq_rel))return false;
    if(actor_status_incarnation_closed_.load(std::memory_order_acquire)||closing()||!token.can_bind(*this)) {
        auto own=retained;
        actor_status_incarnation_.compare_exchange_strong(own,{},std::memory_order_acq_rel);
        token.retire();return false; // Only this private entry, never a successor.
    }
    if(expected)expected->retire();
    return true;
}
bool Session::has_actor_status_write_fence() const noexcept {
    return impl_ && bool(impl_->character_handlers.actor_status_write_fence);
}
std::optional<TaiwanActorStatusWriteFence::Writer> Session::begin_actor_status_writer() noexcept {
    if(!has_actor_status_write_fence())return {};
    return impl_->character_handlers.actor_status_write_fence->begin_writer();
}
void Session::invalidate_actor_status_writes() noexcept {
    if(impl_ && impl_->character_handlers.actor_status_write_fence)
        impl_->character_handlers.actor_status_write_fence->invalidate();
}
bool Session::actor_status_write_fence_matches(
        const std::shared_ptr<TaiwanActorStatusWriteFence>& fence) const noexcept {
    return fence && impl_->character_handlers.actor_status_write_fence==fence;
}
void Session::WorldCallbackOutput::Data::fail() noexcept {
    auto pending=WorldCallbackOutputStatus::Pending;
    status.compare_exchange_strong(pending,WorldCallbackOutputStatus::Failed);
    if(status.load()==WorldCallbackOutputStatus::Failed&&armed.load()&&!released.load())
        if(const auto actual=session.lock()){
            actual->impl_->owned_input_retired.store(true);actual->impl_->close_requested.store(true);
        }
}
std::optional<Session::WorldCallbackOutput> Session::capture_world_callback_output(const NormalWorldInitialization& init){
    if(observed_world_callback!=this||!impl_->callback_output_active)return {};
    if(impl_->callback_output_capture||impl_->callback_output_activity){
        if(impl_->callback_output_capture)impl_->callback_output_capture->receipt->fail();return {};
    }
    if(impl_->callback_reply_window&&impl_->callback_reply_window->poisoned.load())return {};
    if(!normal_world_initialization_current(init)||!account_id||!character_id||closing())return {};
    std::vector<WorldCallbackOutput::SelectionKey> keys;
    for(std::size_t index=0;index<observed_world_records.size();++index)
        if(const auto* input=std::get_if<RecoveredDeitySelection::Request>(&observed_world_records[index]))
            keys.push_back({keys.size(),index,input->key});
    auto data=std::make_shared<WorldCallbackOutput::Data>(weak_from_this(),id(),account_id,character_id,
        battle_generation(),state(),init.data_,std::move(keys));
    impl_->callback_output_capture=std::make_shared<Impl::CallbackOutputAttempt>(data);
    observed_callback_output_status=&data->status;
    return WorldCallbackOutput(std::move(data));
}
bool Session::world_callback_output_current_on_game(const WorldCallbackOutput& output) const {
    const auto data=output.data_;
    if(!data||data->game_thread!=std::this_thread::get_id()||data->session.lock().get()!=this)return false;
    return data->status.load()!=WorldCallbackOutputStatus::Failed&&impl_->callback_output_transport_current(data)&&
        account_id==data->account&&character_id==data->character;
}
std::optional<Session::WorldCallbackSelectionInput> Session::claim_next_callback_selection(
        const WorldCallbackOutput& output,const RecoveredDeitySelection::Request& request){
    const auto data=output.data_;
    if(observed_world_callback!=this||!impl_->callback_output_active||!impl_->callback_output_capture||
       impl_->callback_output_capture->receipt!=data||data->sealed.load()||!world_callback_output_current_on_game(output))return {};
    if(data->claimed>=data->keys.size()||data->keys[data->claimed].key!=request.key){data->fail();return {};}
    auto input=std::make_shared<const WorldCallbackSelectionInput::Data>(data,data->keys[data->claimed]);
    ++data->claimed;return WorldCallbackSelectionInput(std::move(input));
}
bool Session::callback_output_selection_current(const WorldCallbackOutput& output,const WorldCallbackSelectionInput& input) const {
    return observed_world_callback==this&&impl_->callback_output_active&&impl_->callback_output_capture&&
        impl_->callback_output_capture->receipt==output.data_&&input.data_->cohort==output.data_&&
        !output.data_->sealed.load()&&world_callback_output_current_on_game(output)&&
        input.data_->key.ordinal<output.data_->claimed;
}
std::optional<Session::WorldCallbackOutputCursor> Session::capture_world_callback_output_cursor(const WorldCallbackOutput& output){
    if(observed_world_callback!=this||!impl_->callback_output_active||!impl_->callback_output_capture||
       impl_->callback_output_capture->receipt!=output.data_||output.data_->sealed.load()||!world_callback_output_current_on_game(output))return {};
    return WorldCallbackOutputCursor(std::make_shared<const WorldCallbackOutputCursor::Data>(output.data_,output.data_->components.size()));
}
bool Session::callback_output_component_after_cursor(const WorldCallbackOutput& output,
        const WorldCallbackOutputCursor& cursor,const WorldCallbackOutput::Component& component) const noexcept{
    return cursor.data_->cohort==output.data_&&component.data_->cohort.lock()==output.data_&&
        component.ordinal()>=cursor.data_->first;
}
Session::WorldReplyPushCapture::WorldReplyPushCapture(Session& session,WorldReplyPushWire profile){
    auto& state=*session.impl_;
    if(observed_world_callback!=&session||!state.callback_output_active)throw std::logic_error("World reply pushes require actual GAME world callback");
    try{
        if(state.reply_push_capture){state.fail_reply_pushes();throw std::logic_error("Nested world reply push capture");}
        const auto delivery=state.world_delivery_identity.load();
        if(!profile||state.reply_push_failed||session.closing()||!session.recovered_world_ready()||!session.account_id||!session.character_id||
           state.mode!=ProtocolMode::God2CharacterConnection||!delivery||delivery->account!=session.account_id||delivery->character!=session.character_id||
           !delivery->world_generation||delivery->battle_generation!=session.battle_generation()||!session.native_channel_binding_current()||
           (session.state()!=SessionState::CharacterSelected&&session.state()!=SessionState::InWorld&&session.state()!=SessionState::InBattle))
            throw std::logic_error("World reply push capture needs exact ready delivery owner/profile");
        const auto window=state.reply_window();
        auto data=std::make_shared<Data>(session,std::move(profile),delivery);data->window=window;
        state.reply_push_capture=data;data_=std::move(data);
    }catch(...){state.fail_reply_pushes();throw;}
}
Session::WorldReplyPushCapture::~WorldReplyPushCapture() noexcept{
    if(!data_)return;if(data_->thread!=std::this_thread::get_id())std::terminate();
    if(!data_->finished)invalidate();data_->profile={};
}
void Session::WorldReplyPushCapture::invalidate() noexcept{
    const auto data=data_;if(!data)return;
    const auto window=std::static_pointer_cast<Impl::CallbackReplyWindow>(data->window);
    if(window)window->poisoned.store(true);
    if(data->thread!=std::this_thread::get_id()){data->pending->failed.store(true);return;}
    data->finished=true;data->profile={};
    if(const auto session=data->session.lock()){
        auto& state=*session->impl_;
        if(observed_world_callback==session.get()&&state.callback_output_active&&state.callback_reply_window==window&&window&&window->active.load()){
            state.fail_reply_pushes();if(state.reply_push_capture==data)state.reply_push_capture.reset();
        }else data->pending->settle(false); // An old scope cannot poison a successor callback.
    }else data->pending->settle(false);
}
std::vector<std::uint8_t> Session::WorldReplyPushCapture::finish(std::size_t relative_output_offset){
    const auto data=data_;if(!data||data->thread!=std::this_thread::get_id())throw std::logic_error("World reply push finish requires original GAME owner");
    try{
        const auto session=data->session.lock();if(!session)throw std::logic_error("World reply push source expired");auto& state=*session->impl_;
        if(observed_world_callback!=session.get()||!state.callback_output_active||state.reply_push_capture!=data||state.callback_reply_window!=data->window)
            throw std::logic_error("World reply push finish belongs to another callback");
        const auto window=state.reply_window();const auto pending=data->pending;
        if(data->finished||data->encoding||observed_world_callback!=session.get()||!state.callback_output_active||state.reply_push_capture!=data||
           data->window!=window||state.reply_push_failed||!state.reply_push_current(pending,true)||relative_output_offset>max_buffer||window->base>max_buffer-relative_output_offset)
            throw std::logic_error("World reply push final scope/source/offset changed");
        const auto base=window->base+relative_output_offset;
        if(pending->wire.size()>max_buffer-base)throw std::overflow_error("World reply push final fragment bounds");
        if(!pending->wire.empty()&&!window->pushes.empty()){
            const auto previous=window->pushes.back();
            if(base<previous->base||base-previous->base<previous->wire.size())throw std::logic_error("Captured push source order/overlap changed");
        }
        auto result=pending->wire;pending->base=base;
        if(!pending->wire.empty())window->pushes.push_back(pending);
        data->finished=true;data->profile={};state.reply_push_capture.reset();return result;
    }catch(...){invalidate();throw;}
}
Session::WorldReplyPushCapture Session::capture_world_reply_pushes(WorldReplyPushWire profile){return WorldReplyPushCapture(*this,std::move(profile));}

Session::CallbackReplyOutputOffset::CallbackReplyOutputOffset(Session& session,std::size_t prefix){
    try{
        const auto window=session.impl_->reply_window();
        if(prefix>std::numeric_limits<std::size_t>::max()-window->base||
           window->next_nonce==std::numeric_limits<std::uint64_t>::max())throw std::overflow_error("Reply output offset overflow");
        capture_=window;old_base_=window->base;parent_=window->nonce;
        nonce_=++window->next_nonce;window->nonce=nonce_;window->base+=prefix;
    }catch(...){session.impl_->poison_callback_reply();throw;}
}
Session::CallbackReplyOutputOffset::~CallbackReplyOutputOffset() noexcept{
    if(!capture_)return;
    const auto window=std::static_pointer_cast<Impl::CallbackReplyWindow>(capture_);
    if(window->thread!=std::this_thread::get_id()||!window->active.load()||window->nonce!=nonce_){
        window->poisoned.store(true);return;
    }
    window->base=old_base_;window->nonce=parent_;
}
Session::CallbackReplyOutputOffset Session::callback_reply_output_offset(std::size_t relative_prefix){
    return CallbackReplyOutputOffset(*this,relative_prefix);
}
std::optional<Session::WorldCallbackSelectionEmission> Session::mint_callback_selection_emission(
        const WorldCallbackOutput& output,const WorldCallbackSelectionInput& input,std::span<const std::uint8_t> wire){
    const auto data=output.data_;
    if(!callback_output_selection_current(output,input))return {};
    const auto ordinal=input.selection_ordinal();
    if(ordinal>=data->issued.size()||data->issued[ordinal]||
       (!data->emissions.empty()&&data->emissions.back().selection_ordinal()>=ordinal)){
        data->fail();return {};
    }
    try{
        auto logical=RecoveredWorldFrame::decode(wire);
        if(wire.size()!=32||!logical||logical->size()!=29||(*logical)[0]!=0x31||(*logical)[1]!=input.request().key){data->fail();return {};}
        WorldCallbackSelectionEmission emission(std::make_shared<WorldCallbackSelectionEmission::Data>(
            data,ordinal,data->components.size(),wire,std::move(*logical)));
        data->emissions.push_back(emission);data->issued[ordinal]=true;return emission;
    }catch(...){data->fail();return {};}
}
void Session::send_world_callback_reply_frame(LegacyWorldReplyFrame frame){
    if(qualified_world_push_profile){[[maybe_unused]] const auto status_admission=begin_actor_status_writer();invalidate_actor_status_writes();impl_->reject_qualified_profile_sender();}
    if(observed_world_callback==this&&impl_->reply_push_capture&&frame.emission_){[[maybe_unused]] const auto status_admission=begin_actor_status_writer();invalidate_actor_status_writes();impl_->fail_reply_pushes();throw std::logic_error("Causal selection push cannot use generic reply capture");}
    if(frame.emission_){
        const auto source=impl_->callback_output_capture;
        if(observed_world_callback!=this||!impl_->callback_output_active||!source||
           !world_callback_output_current_on_game(WorldCallbackOutput(source->receipt))||frame.emission_->data_->cohort.lock()!=source->receipt){
            impl_->poison_callback_reply();close();throw std::logic_error("Tagged reply frame outside actual source callback");
        }
    }
    if(frame.emission_)try {
        if(impl_->defer_selection_reply(*frame.emission_,frame.logical_)) {
            // Preserve the original send call's GAME-side invalidation even
            // though this occurrence joins the later actual final Write.
            (void)retire_battle_self_view_logical_output(frame.logical_);
            [[maybe_unused]] const auto status_admission=begin_actor_status_writer();
            invalidate_actor_status_writes();return;
        }
    }catch(...) {impl_->poison_callback_reply();throw;}
    send_world_records_impl(std::move(frame.logical_),{},std::move(frame.emission_));
}
std::vector<std::uint8_t> Session::take_world_callback_reply(LegacyWorldReply reply){
    if(reply.ranges_.empty())return std::move(reply.wire_);
    if(qualified_world_push_profile)impl_->reject_qualified_profile_sender();
    if(observed_world_callback==this&&impl_->reply_push_capture){impl_->fail_reply_pushes();throw std::logic_error("Causal selection final reply cannot use generic capture");}
    const auto source=impl_->callback_output_capture;
    if(observed_world_callback!=this||!impl_->callback_output_active||!source||
       !world_callback_output_current_on_game(WorldCallbackOutput(source->receipt))){
        impl_->poison_callback_reply();close();throw std::logic_error("Tagged reply outside its actual callback");
    }
    const auto data=source->receipt;
    try{
        const auto window=impl_->reply_window();
        if(reply.wire_.size()>std::numeric_limits<std::size_t>::max()-window->base)throw std::overflow_error("Final fragment offset overflow");
        std::vector<WorldCallbackOutput::Data::ReplyRange> ranges;ranges.reserve(reply.ranges_.size());
        std::size_t previous_end=0;bool first=true;
        for(const auto& range:reply.ranges_){
            const auto tag=range.emission.data_;
            if(tag->cohort.lock()!=data||tag->phase.load()!=WorldCallbackSelectionEmission::Data::Phase::Created||
               range.wire_offset>reply.wire_.size()||tag->wire.size()>reply.wire_.size()-range.wire_offset||
               (!first&&range.wire_offset<previous_end)||!Impl::reply_frame_boundary(reply.wire_,range.wire_offset)||
               !std::equal(tag->wire.begin(),tag->wire.end(),reply.wire_.begin()+range.wire_offset))
                throw std::logic_error("Tagged child reply range is not its exact complete source frame");
            previous_end=range.wire_offset+tag->wire.size();first=false;
            ranges.push_back({range.emission,range.wire_offset});
        }
        const auto fragment=std::make_shared<const WorldCallbackOutput::Data::ReplyFragment>(window->base,reply.wire_,std::move(ranges));
        window->fragments.push_back(fragment);
        for(const auto& range:fragment->ranges){
            auto created=WorldCallbackSelectionEmission::Data::Phase::Created;
            if(!range.emission.data_->phase.compare_exchange_strong(created,WorldCallbackSelectionEmission::Data::Phase::FinalReserved))
                throw std::logic_error("Causal selection emission already reserved");
        }
        return std::move(reply.wire_);
    }catch(...){data->fail();impl_->poison_callback_reply();throw;}
}
std::optional<Session::WorldCallbackEmissionLocation> Session::callback_output_emission_location(
        const WorldCallbackOutput& output,const WorldCallbackSelectionEmission& emission) const{
    const auto data=output.data_;const auto tag=emission.data_;
    if(output.status()!=WorldCallbackOutputStatus::Written||!output.sealed()||!output.callback_accepted()||
       !world_callback_output_current_on_game(output)||tag->cohort.lock()!=data||
       tag->phase.load()!=WorldCallbackSelectionEmission::Data::Phase::Bound)return {};
    const auto found=std::count_if(data->emissions.begin(),data->emissions.end(),[&](const auto& value){return value.same_occurrence(emission);});
    return found==1?std::optional{tag->location}:std::nullopt;
}
bool Session::callback_output_emission_written(const WorldCallbackOutput& output,const WorldCallbackSelectionEmission& emission) const{
    return callback_output_emission_location(output,emission).has_value();
}
void Session::hold_world_input_until_callback_output_written(const WorldCallbackOutput& output){
    const auto data=output.data_;
    if(observed_world_callback!=this||!impl_->callback_output_active||!impl_->callback_output_capture||
       impl_->callback_output_capture->receipt!=data||data->sealed.load()||!world_callback_output_current_on_game(output)||
       impl_->owned_input_retired.load()||data->armed.exchange(true)){
        data->fail();throw std::logic_error("Callback output input hold requires exact new active capture");
    }
    std::shared_ptr<WorldCallbackOutput::Data> empty;
    if(!impl_->callback_output_input_hold.compare_exchange_strong(empty,data)){
        data->fail();throw std::logic_error("Callback output input already held");
    }
}
void Session::start() {
    Session::schedule_actor_status_work<true>(impl_->strand,{shared_from_this(),{}},
        [self = shared_from_this()] { self->impl_->start(); });
}
void Session::send(Packet packet) {
    impl_->unsupported_callback_output();
    // Fixture Packet is not an owned native-world envelope at this handoff.
    (void)retire_battle_self_view_wire_output({});
    [[maybe_unused]] const auto status_admission=begin_actor_status_writer();
    invalidate_actor_status_writes();
    if (impl_->close_requested.load()) return;
    const auto charge = packet.payload.size();
    auto budget = impl_->budget;
    std::shared_ptr<Reservation> reservation;
    {
        std::lock_guard lock(budget->mutex);
        if (charge <= max_buffer - budget->bytes && budget->count < max_writes) {
            // Allocate before incrementing so an allocation failure cannot leak capacity.
            reservation = std::make_shared<Reservation>(budget, charge);
            budget->bytes += charge;
            ++budget->count;
        }
    }
    if (!reservation) { close(); return; }
    impl_->post_status_work(impl_->strand, [self = shared_from_this(), packet = std::move(packet), reservation]() mutable {
        self->impl_->enqueue(std::move(packet), std::move(reservation));
    });
}
bool Session::native_movement_response_custody_enabled() const noexcept {
    return impl_->character_handlers.native_movement_response_custody;
}
bool Session::owned_normal_movement_response_custody_enabled() const noexcept {
    return impl_->character_handlers.owned_normal_movement_response_custody;
}
Session::MovementResponseOutputOffset::MovementResponseOutputOffset(Session& session,std::size_t relative_prefix) {
    if(!session.native_movement_response_custody_enabled() && !session.owned_normal_movement_response_custody_enabled())return;
    if(observed_movement_callback!=&session) {
        if(observed_movement_poison)observed_movement_poison->store(true);
        throw std::logic_error("Movement output offset requires actual callback");
    }
    const auto collector=session.impl_->movement_collector;
    if(!collector || !collector->active || collector->poisoned || collector->thread!=std::this_thread::get_id() ||
       collector->run_nonce || relative_prefix>max_buffer || collector->output_base>max_buffer-relative_prefix ||
       collector->next_scope_nonce==std::numeric_limits<std::uint64_t>::max()) {
        if(collector)collector->poisoned=true;
        throw std::logic_error("Movement output offset scope invalid or reentered");
    }
    capture_=collector;old_base_=collector->output_base;parent_=collector->offset_scope_nonce;
    nonce_=++collector->next_scope_nonce;collector->offset_scope_nonce=nonce_;collector->output_base+=relative_prefix;
}
Session::MovementResponseOutputOffset::~MovementResponseOutputOffset() noexcept {
    if(!capture_)return;
    const auto collector=std::static_pointer_cast<Impl::MovementCollector>(capture_);
    if(collector->thread!=std::this_thread::get_id()) {collector->poisoned=true;return;}
    if(!collector->active || collector->offset_scope_nonce!=nonce_ || collector->run_nonce) {collector->poisoned=true;return;}
    collector->output_base=old_base_;collector->offset_scope_nonce=parent_;
}
Session::MovementResponseInputRun::MovementResponseInputRun(Session& session,
    std::span<const RecoveredWorldRecords::Record> input) {
    if(!session.native_movement_response_custody_enabled() && !session.owned_normal_movement_response_custody_enabled())return;
    if(observed_movement_callback!=&session) {
        if(observed_movement_poison)observed_movement_poison->store(true);
        throw std::logic_error("Movement input run requires actual callback");
    }
    const auto collector=session.impl_->movement_collector;
    if(!collector || !collector->active || collector->poisoned || collector->run_nonce ||
       collector->thread!=std::this_thread::get_id() || input.empty() ||
       collector->next_scope_nonce==std::numeric_limits<std::uint64_t>::max()) {
        if(collector)collector->poisoned=true;
        throw std::logic_error("Movement input run invalid or reentered");
    }
    std::optional<std::size_t> first;
    // Equality with bounded valid original pointers first. No subtraction or
    // relational comparison on an unrelated caller-supplied pointer.
    for(std::size_t index=0;index<collector->original_records.size();++index)
        if(collector->original_records.data()+index==input.data()) {first=index;break;}
    if(!first || input.size()>collector->original_records.size()-*first ||
       (collector->last_registered_record && *first<=*collector->last_registered_record)) {
        collector->poisoned=true;throw std::invalid_argument("Movement input run not exact ordered original records");
    }
    collector->run_records.clear();
    for(std::size_t index=0;index<input.size();++index) {
        if(std::holds_alternative<RecoveredMovement::Request>(input[index]))collector->run_records.push_back(*first+index);
        else if(!std::holds_alternative<RecoveredWorldRecords::Tick>(input[index])) {
            collector->poisoned=true;throw std::invalid_argument("Movement input run contains foreign command");
        }
    }
    if(collector->run_records.empty() ||
       (collector->normal_mode ? collector->normal_assigned!=collector->normal_batches.size() : collector->assigned!=collector->steps.size())) {
        collector->poisoned=true;throw std::invalid_argument("Movement input run has no actual ordered Core steps");
    }
    capture_=collector;nonce_=++collector->next_scope_nonce;collector->run_nonce=nonce_;
    collector->run_first_step=collector->steps.size();collector->run_first_batch=collector->normal_batches.size();
    collector->last_registered_record=*first+input.size()-1;
}
Session::MovementResponseInputRun::~MovementResponseInputRun() noexcept {
    if(!capture_)return;
    const auto collector=std::static_pointer_cast<Impl::MovementCollector>(capture_);
    if(collector->thread!=std::this_thread::get_id()) {collector->poisoned=true;return;}
    if(!collector->active || collector->run_nonce!=nonce_) {collector->poisoned=true;return;}
    if(collector->normal_mode) {
        if(collector->normal_batches.size()!=collector->run_first_batch+1 ||
           collector->normal_assigned!=collector->normal_batches.size())collector->poisoned=true;
        else {
            const auto& batch=collector->normal_batches.back();
            if(!batch->committed || !batch->offset || batch->record_indices!=collector->run_records)collector->poisoned=true;
        }
        collector->run_nonce=0;collector->run_records.clear();return;
    }
    if(collector->steps.size()-collector->run_first_step!=collector->run_records.size() ||
       collector->assigned!=collector->steps.size())collector->poisoned=true;
    for(std::size_t index=collector->run_first_step;index<collector->steps.size();++index)
        if(!collector->steps[index]->committed || !collector->steps[index]->offset)collector->poisoned=true;
    collector->run_nonce=0;collector->run_records.clear();
}
Session::MovementResponseOutputOffset Session::movement_response_output_offset(std::size_t relative_prefix) {
    return MovementResponseOutputOffset(*this,relative_prefix);
}
Session::MovementResponseInputRun Session::movement_response_input_run(std::span<const RecoveredWorldRecords::Record> input) {
    return MovementResponseInputRun(*this,input);
}
std::optional<Session::MovementStepWrite> Session::prepare_movement_response_write(
    const SharedWorldPresence::Lease& lease,const RecoveredPosition& before,
    const RecoveredMovement::Request& request,std::uint8_t direction,std::uint8_t native_cell,
    std::uint64_t scene_revision,std::span<const std::uint8_t> logical_ack,
    std::span<const std::uint8_t> encoded_frame) {
    if(!native_movement_response_custody_enabled())return {};
    if(observed_movement_callback!=this) {
        if(observed_movement_poison)observed_movement_poison->store(true);
        return {};
    }
    const auto collector=impl_->movement_collector;
    const auto reject=[&]() -> std::optional<MovementStepWrite> {if(collector)collector->poisoned=true;return {};};
    if(!collector || !collector->active || collector->poisoned || !collector->run_nonce ||
       collector->thread!=std::this_thread::get_id() || collector->steps.size()<collector->run_first_step ||
       collector->steps.size()-collector->run_first_step>=collector->run_records.size())return reject();
    const auto run_index=collector->steps.size()-collector->run_first_step;
    const auto record_index=collector->run_records[run_index];
    const auto* actual_request=std::get_if<RecoveredMovement::Request>(&collector->original_records[record_index]);
    const auto common=impl_->common_world_identity.load();
    if(!common || common.get()!=collector->common.get() || closing() || !recovered_world_ready() ||
       state()!=SessionState::InWorld || impl_->common_entry_identity.load() || lease.session!=id() ||
       lease.account!=account_id || lease.character!=character_id || lease.account!=common->account ||
       lease.character!=common->character || lease.generation!=common->generation ||
       before.area!=lease.position.area || before.scene!=lease.position.scene ||
       !before.revision || before.revision==std::numeric_limits<std::uint64_t>::max() || direction>7 || !scene_revision ||
       request.sequence>=40 || !actual_request || !Impl::same_movement_request(request,*actual_request) ||
       (run_index && (collector->steps.back()->expected_after!=before || collector->steps.back()->battle!=battle_generation())) ||
       (collector->lease && *collector->lease!=lease) ||
       (!collector->steps.empty() && !collector->steps.back()->committed) ||
       logical_ack.size()!=2 || logical_ack[0]!=0x5d || encoded_frame.size()!=5)return reject();
    const auto decoded=RecoveredWorldFrame::decode(encoded_frame);
    if(!decoded || decoded->size()!=logical_ack.size() || !std::equal(decoded->begin(),decoded->end(),logical_ack.begin()))return reject();
    RecoveredPosition expected=before;expected.x=request.x;expected.y=request.y;++expected.revision;
    std::array<std::uint8_t,2> logical;std::copy(logical_ack.begin(),logical_ack.end(),logical.begin());
    std::array<std::uint8_t,5> frame;std::copy(encoded_frame.begin(),encoded_frame.end(),frame.begin());
    const auto data=std::make_shared<MovementStepWrite::Data>(weak_from_this(),collector->occurrence,common,lease,before,expected,
        request,record_index,battle_generation(),scene_revision,state(),direction,native_cell,logical,frame);
    collector->steps.push_back(data);collector->lease=lease;
    return MovementStepWrite(data); // All step metadata/frame ownership exists before durable CAS.
}
bool Session::commit_movement_response_write(const MovementStepWrite& write,const RecoveredPosition& actual_after) {
    if(!native_movement_response_custody_enabled() || observed_movement_callback!=this) {
        if(observed_movement_poison)observed_movement_poison->store(true);
        return false;
    }
    const auto collector=impl_->movement_collector;
    const auto reject=[&] {if(collector)collector->poisoned=true;return false;};
    const auto data=write.data_;
    if(!collector || !collector->run_nonce ||
       !collector->active || collector->poisoned || collector->thread!=std::this_thread::get_id() || !data ||
       collector->steps.empty() || collector->steps.back()!=data || data->committed ||
       data->occurrence!=collector->occurrence || data->common!=collector->common ||
       impl_->common_world_identity.load().get()!=collector->common.get() || data->session.lock().get()!=this ||
       closing() || !recovered_world_ready() || state()!=data->phase || battle_generation()!=data->battle ||
       data->lease.account!=account_id || data->lease.character!=character_id || impl_->common_entry_identity.load() ||
       actual_after!=data->expected_after)return reject();
    data->committed=true;return true; // Game-only marker, never another position writer.
}
std::optional<Session::NormalMovementBatchWrite> Session::prepare_normal_movement_response_write(
    const NormalWorldInitialization& initialization,const SqliteOwnedEquipmentTransaction::Before& before,
    const NativeEquipmentSnapshot& expected_equipment,std::span<const RecoveredMovement::Request> requests,
    std::uint8_t old_slot,std::uint8_t new_slot,
    std::span<const NormalMovementBatchWrite::Destination> displaced_path,std::span<const std::uint8_t> whole_ack) {
    if(!owned_normal_movement_response_custody_enabled())return {};
    if(observed_movement_callback!=this) {
        if(observed_movement_poison)observed_movement_poison->store(true);
        return {};
    }
    const auto collector=impl_->movement_collector;
    const auto reject=[&]() -> std::optional<NormalMovementBatchWrite> {if(collector)collector->poisoned=true;return {};};
    if(!collector || !collector->normal_mode || !collector->active || collector->poisoned || !collector->run_nonce ||
       collector->thread!=std::this_thread::get_id() || collector->normal_batches.size()!=collector->run_first_batch ||
       collector->normal_assigned!=collector->normal_batches.size() || !collector->steps.empty() || collector->lease ||
       collector->common || impl_->common_world_identity.load() || impl_->common_entry_identity.load() ||
       requests.empty() || requests.size()!=collector->run_records.size() || requests.size()>max_buffer/5 ||
       whole_ack.size()!=requests.size()*5 || old_slot>=40 || new_slot>=40 ||
       !before.inventory || !before.equipment || !initialization.entry_written() ||
       !normal_world_initialization_current_on_game(initialization) || closing() || !recovered_world_ready() ||
       (state()!=SessionState::CharacterSelected && state()!=SessionState::InWorld) ||
       before.inventory->root.account_id!=account_id || before.inventory->root.id!=character_id ||
       !NativeEquipmentSnapshot::same_root(before.inventory->root,before.equipment->root) ||
       (collector->normal_initialization && !collector->normal_initialization->same_initialization(initialization)))return reject();
    const auto limit=static_cast<std::uint64_t>(std::numeric_limits<std::int64_t>::max());
    if(!before.equipment->position.revision || before.equipment->position.revision>=limit ||
       !before.equipment->revision || before.equipment->revision>=limit || !before.inventory->revision)return reject();
    if(!collector->normal_batches.empty()) {
        const auto previous=collector->normal_batches.back();
        if(!previous->committed || !previous->offset || previous->new_slot!=old_slot || previous->phase!=state() ||
           previous->battle!=battle_generation() || previous->expected_equipment!=*before.equipment ||
           *previous->before.inventory!=*before.inventory)return reject();
    }
    auto x=before.equipment->position.x,y=before.equipment->position.y;
    auto slot=old_slot;std::size_t path_index=0;
    for(std::size_t index=0;index<requests.size();++index) {
        const auto& request=requests[index];
        const auto* original=std::get_if<RecoveredMovement::Request>(&collector->original_records[collector->run_records[index]]);
        slot=static_cast<std::uint8_t>((slot+1)%40);
        const auto ack=RecoveredMovement::ack(request.sequence);
        if(!original || !Impl::same_movement_request(request,*original) || request.sequence!=slot ||
           !std::equal(ack.begin(),ack.end(),whole_ack.begin()+static_cast<std::ptrdiff_t>(index*5)))return reject();
        if(x!=request.x || y!=request.y) {
            if(path_index>=displaced_path.size() || displaced_path[path_index]!=NormalMovementBatchWrite::Destination{request.x,request.y})return reject();
            ++path_index;
        }
        x=request.x;y=request.y;
    }
    if(slot!=new_slot || path_index!=displaced_path.size())return reject();
    auto expected=*before.equipment;
    expected.position.x=x;expected.position.y=y;++expected.position.revision;++expected.revision;
    constexpr std::string_view marker=";CUSTOM-0095:ordinary-move-preserves-material";
    if(expected.source_record.find(marker)==std::string::npos) {
        if(expected.source_record.size()>2048-marker.size())return reject();
        expected.source_record.append(marker);
    }
    if(expected!=expected_equipment)return reject();
    const auto data=std::make_shared<NormalMovementBatchWrite::Data>(weak_from_this(),collector->occurrence,initialization,
        before,expected_equipment,std::vector<RecoveredMovement::Request>(requests.begin(),requests.end()),collector->run_records,
        std::vector<NormalMovementBatchWrite::Destination>(displaced_path.begin(),displaced_path.end()),old_slot,new_slot,
        battle_generation(),state(),std::vector<std::uint8_t>(whole_ack.begin(),whole_ack.end()));
    // All copies/allocations precede the caller's sole joint SQL COMMIT. There
    // is no DB owner, callback, common lease or invented intermediate revision.
    collector->normal_batches.push_back(data);collector->normal_initialization=initialization;
    return NormalMovementBatchWrite(data);
}
bool Session::commit_normal_movement_response_write(const NormalMovementBatchWrite& write,
    const SqliteOwnedEquipmentTransaction::Committed& committed,const RecoveredPosition& published_after) {
    if(!owned_normal_movement_response_custody_enabled() || observed_movement_callback!=this) {
        if(observed_movement_poison)observed_movement_poison->store(true);
        return false;
    }
    const auto collector=impl_->movement_collector;
    const auto reject=[&] {if(collector)collector->poisoned=true;return false;};
    const auto data=write.data_;
    if(!collector || !collector->normal_mode || !collector->active || collector->poisoned || !collector->run_nonce ||
       collector->thread!=std::this_thread::get_id() || !data ||
       collector->normal_batches.size()!=collector->run_first_batch+1 || collector->normal_batches.back()!=data ||
       collector->normal_assigned!=collector->run_first_batch || data->committed || data->offset ||
       data->occurrence!=collector->occurrence || data->record_indices!=collector->run_records ||
       data->session.lock().get()!=this || !collector->normal_initialization ||
       !data->initialization.same_initialization(*collector->normal_initialization) ||
       !normal_world_initialization_current_on_game(data->initialization) || !data->initialization.entry_written() ||
       closing() || !recovered_world_ready() || state()!=data->phase || battle_generation()!=data->battle ||
       impl_->common_world_identity.load() || impl_->common_entry_identity.load() ||
       data->before.inventory->root.account_id!=account_id || data->before.inventory->root.id!=character_id ||
       committed.inventory().snapshot()!=*data->before.inventory || committed.equipment().snapshot()!=data->expected_equipment ||
       published_after!=data->expected_equipment.position)return reject();
    data->committed=true;return true; // Actual private joint receipt, never a second writer or ACK.
}
bool Session::locate_movement_response_run(std::size_t actual_output_offset,
    std::span<const std::uint8_t> actual_run_wire) {
    if(!native_movement_response_custody_enabled() && !owned_normal_movement_response_custody_enabled())return true;
    if(observed_movement_callback!=this) {
        if(observed_movement_poison)observed_movement_poison->store(true);
        return false;
    }
    const auto collector=impl_->movement_collector;
    const auto reject=[&] {if(collector)collector->poisoned=true;return false;};
    if(!collector || !collector->active || collector->poisoned || !collector->run_nonce ||
       collector->thread!=std::this_thread::get_id() || actual_run_wire.empty() || actual_run_wire.size()%5 ||
       actual_output_offset>max_buffer || collector->output_base>max_buffer-actual_output_offset)return reject();
    actual_output_offset+=collector->output_base;
    if(actual_run_wire.size()>max_buffer-actual_output_offset)return reject();
    if(collector->normal_mode) {
        if(collector->normal_batches.size()!=collector->run_first_batch+1 ||
           collector->normal_assigned!=collector->run_first_batch)return reject();
        const auto batch=collector->normal_batches.back();
        if(!batch->committed || batch->offset || batch->occurrence!=collector->occurrence ||
           batch->record_indices!=collector->run_records || batch->requests.size()!=collector->run_records.size() ||
           batch->wire.size()!=actual_run_wire.size() ||
           !std::equal(batch->wire.begin(),batch->wire.end(),actual_run_wire.begin()))return reject();
        if(collector->normal_assigned) {
            const auto previous=collector->normal_batches[collector->normal_assigned-1];
            if(!previous->offset || actual_output_offset<*previous->offset+previous->wire.size())return reject();
        }
        batch->offset=actual_output_offset;++collector->normal_assigned;return true;
    }
    const auto count=actual_run_wire.size()/5;
    if(collector->assigned!=collector->run_first_step || collector->steps.size()<collector->run_first_step ||
       count!=collector->run_records.size() || count!=collector->steps.size()-collector->run_first_step)return reject();
    if(collector->assigned) {
        const auto previous=collector->steps[collector->assigned-1];
        if(!previous->offset || actual_output_offset<*previous->offset+previous->frame.size())return reject();
    }
    // Verify the entire run before assigning any component. No scanning,
    // ciphertext search, omitted-step acceptance or equal-byte substitution.
    for(std::size_t index=0;index<count;++index) {
        const auto step=collector->steps[collector->assigned+index];
        if(!step->committed || step->offset || step->occurrence!=collector->occurrence ||
           !std::equal(step->frame.begin(),step->frame.end(),actual_run_wire.begin()+static_cast<std::ptrdiff_t>(index*5)))return reject();
    }
    for(std::size_t index=0;index<count;++index)collector->steps[collector->assigned+index]->offset=actual_output_offset+index*5;
    collector->assigned+=count;return true;
}
std::optional<Session::MovementResponseWrite> Session::movement_response_write_on_game() const {
    if(!native_movement_response_custody_enabled() && !owned_normal_movement_response_custody_enabled())return {};
    const auto data=impl_->latest_movement_response.load();
    if(!data || data->game_thread!=std::this_thread::get_id() || data->session.lock().get()!=this)return {};
    return MovementResponseWrite(data); // Historical observation; no current permission inferred.
}
void Session::send_world_records(std::vector<std::uint8_t> logical) {
    [[maybe_unused]] const auto status_admission=begin_actor_status_writer();
    invalidate_actor_status_writes();
    send_world_records_impl(std::move(logical),{});
}
Session::WorldRecordsWrite Session::send_world_records_observed(std::vector<std::uint8_t> logical) {
    [[maybe_unused]] const auto status_admission=begin_actor_status_writer();
    invalidate_actor_status_writes();
    if(qualified_world_push_profile)impl_->reject_qualified_profile_sender();
    if(observed_world_callback!=this)
        throw std::logic_error("Observed world sender requires actual world-records game callback");
    if(impl_->mode!=ProtocolMode::God2CharacterConnection || closing() || !recovered_world_ready() ||
       (state()!=SessionState::CharacterSelected && state()!=SessionState::InWorld) || !account_id || !character_id ||
       logical.empty() || logical.size()>RecoveredWorldFrame::max_logical_size){
        impl_->unsupported_callback_output();
        throw std::invalid_argument("Observed world sender requires exact ready world owner and complete batch");
    }
    auto data=std::make_shared<WorldRecordsWrite::Data>(weak_from_this(),account_id,character_id,
        battle_generation(),state(),logical);
    send_world_records_impl(std::move(logical),data);
    return WorldRecordsWrite(std::move(data));
}
bool Session::world_records_write_current(const WorldRecordsWrite& observation) const {
    if(observed_world_callback!=this)
        throw std::logic_error("Observed world current requires actual world-records game callback");
    const auto& data=*observation.data_;
    return data.session.lock().get()==this && !closing() && recovered_world_ready() &&
        impl_->mode==ProtocolMode::God2CharacterConnection && state()==data.phase &&
        battle_generation()==data.battle && account_id==data.account && character_id==data.character;
}
Session::WorldResponseWrite Session::observe_world_response(std::span<const std::uint8_t> wire) {
    if(observed_world_callback!=this || !observed_response_poison)
        throw std::logic_error("World response capture requires actual world-records game callback");
    if(*observed_response_poison || impl_->world_response_callback_capture) {
        poison_world_response();
        throw std::logic_error("World response capture reentry or duplicate rejected");
    }
    if(impl_->mode!=ProtocolMode::God2CharacterConnection || closing() || !recovered_world_ready() ||
       !account_id || !character_id || wire.empty() || !Impl::valid_world_response(wire))
        throw std::invalid_argument("World response capture requires complete original framed response and ready owner");
    auto data=std::make_shared<WorldResponseWrite::Data>(weak_from_this(),account_id,character_id,
        battle_generation(),state(),wire,retire_battle_self_view_wire_output(wire));
    impl_->world_response_callback_capture=std::make_shared<Impl::WorldResponseAttempt>(data);
    observed_response_status=&data->status;
    return WorldResponseWrite(std::move(data));
}
bool Session::world_response_write_current(const WorldResponseWrite& observation) const {
    if(observed_world_callback!=this)
        throw std::logic_error("World response current requires actual world-records game callback");
    return world_response_write_current_on_game(observation);
}
bool Session::world_response_write_current_on_game(const WorldResponseWrite& observation) const {
    const auto data=observation.data_;
    if(!data || data->game_thread!=std::this_thread::get_id())return false;
    const auto actual=data->session.lock();
    if(actual.get()!=this)return false;
    return !closing() && recovered_world_ready() && impl_->mode==ProtocolMode::God2CharacterConnection &&
        state()==data->phase && battle_generation()==data->battle && account_id==data->account && character_id==data->character;
}
std::uint64_t Session::retire_battle_self_view_logical_output(std::span<const std::uint8_t> logical) noexcept {
    if(impl_->mode!=ProtocolMode::God2CharacterConnection ||
       (!impl_->normal_entry.load() && state()!=SessionState::InBattle && !impl_->battle_self_view_source.load()))return 0;
    if(!TaiwanBattleSelfViewWriteFence::inspect_logical(logical).changes_view)return 0;
    const auto intent=impl_->battle_self_view_intents.advance();
    if(const auto old=impl_->battle_self_view_source.exchange({}))old->completion.revoke();
    return intent;
}
std::uint64_t Session::retire_battle_self_view_wire_output(std::span<const std::uint8_t> wire) noexcept {
    if(impl_->mode!=ProtocolMode::God2CharacterConnection ||
       (!impl_->normal_entry.load() && state()!=SessionState::InBattle && !impl_->battle_self_view_source.load()))return 0;
    if(!TaiwanBattleSelfViewWriteFence::inspect(wire).changes_view)return 0;
    const auto intent=impl_->battle_self_view_intents.advance();
    if(const auto old=impl_->battle_self_view_source.exchange({}))old->completion.revoke();
    return intent;
}
std::optional<Session::BattleSelfView> Session::battle_self_view() const {
    const auto data=impl_->battle_self_view_source.load();
    if(!data)return {};
    const BattleSelfView view(data);
    if(!battle_self_view_current(view))return {};
    return view;
}
bool Session::battle_self_view_current(const BattleSelfView& view) const {
    const auto data=view.data_;
    if(!data || data->game_thread!=std::this_thread::get_id())return false;
    const auto actual=data->session.lock();
    if(actual.get()!=this || data->session_id!=id() || closing() || !recovered_world_ready() ||
       impl_->mode!=ProtocolMode::God2CharacterConnection || state()!=SessionState::InBattle ||
       account_id!=data->account || character_id!=data->character ||
       battle_generation()!=data->battle || data->slot>=14)return false;
    return impl_->battle_self_view_source.load()==data && impl_->battle_self_view_fence.current(data->epoch) &&
        impl_->battle_self_view_intents.current(data->intent) && data->completion.written();
}
void Session::hold_world_input_until_response_written(const WorldResponseWrite& write) {
    if(observed_world_callback!=this || (observed_response_poison && *observed_response_poison)) {
        poison_world_response();throw std::logic_error("Owned input continuation requires actual callback TLS");
    }
    const auto captured=impl_->world_response_callback_capture;
    if(impl_->owned_input_retired.load() || !captured || captured->receipt!=write.data_ || impl_->owned_input_callback_lease ||
       write.status()!=WorldResponseWriteStatus::Pending || !world_response_write_current(write)) {
        poison_world_response();throw std::logic_error("Owned input continuation requires exact current original callback");
    }
    auto lease=std::make_shared<Impl::OwnedInputLease>(captured);
    auto unarmed=Impl::WorldResponseAttempt::InputPhase::Unarmed;
    if(!captured->input_phase.compare_exchange_strong(unarmed,Impl::WorldResponseAttempt::InputPhase::Armed)) {
        poison_world_response();throw std::logic_error("Owned input continuation duplicate rejected");
    }
    std::shared_ptr<Impl::WorldResponseAttempt> empty;
    if(!impl_->owned_response_input_hold.compare_exchange_strong(empty,captured)) {
        captured->fail();poison_world_response();throw std::logic_error("Owned input continuation already held");
    }
    impl_->owned_input_callback_lease=std::move(lease);
}
std::optional<Session::NormalWorldInitialization> Session::normal_world_initialization() const {
    if(observed_world_callback!=this)
        throw std::logic_error("Normal initialization requires actual world-records game callback");
    const auto data=impl_->normal_initialization.load();
    if(!data)return std::nullopt;
    const NormalWorldInitialization result(data);
    if(!normal_world_initialization_current(result))return std::nullopt;
    return result;
}
std::optional<Session::NormalWorldInitialization> Session::normal_world_initialization_on_game() const {
    const auto data=impl_->normal_initialization.load();
    if(!data)return std::nullopt;
    const NormalWorldInitialization result(data);
    if(!normal_world_initialization_current_on_game(result))return std::nullopt;
    return result;
}
bool Session::normal_world_initialization_current(const NormalWorldInitialization& observation) const {
    if(observed_world_callback!=this)
        throw std::logic_error("Normal initialization current requires actual world-records game callback");
    const auto& data=*observation.data_;
    const auto& entry=*data.entry;
    return impl_->normal_initialization.load()==observation.data_ && impl_->normal_entry.load()==data.entry &&
        entry.session.lock().get()==this && !entry.retired.load() && !closing() && recovered_world_ready() &&
        impl_->mode==ProtocolMode::God2CharacterConnection &&
        (state()==SessionState::CharacterSelected || state()==SessionState::InWorld) &&
        entry.account==account_id && entry.character==character_id && data.effective_battle==battle_generation();
}
bool Session::world_records_write_current_on_game(const WorldRecordsWrite& observation) const {
    const auto data=observation.data_;
    if(!data || data->game_thread!=std::this_thread::get_id())return false;
    const auto actual=data->session.lock();
    if(actual.get()!=this)return false;
    // Retain the exact actual Session until all game-owned fields are checked.
    return !closing() && recovered_world_ready() &&
        impl_->mode==ProtocolMode::God2CharacterConnection && state()==data->phase &&
        battle_generation()==data->battle && account_id==data->account && character_id==data->character;
}
bool Session::normal_world_initialization_current_on_game(const NormalWorldInitialization& observation) const {
    const auto data=observation.data_;
    if(!data || !data->entry || data->entry->game_thread!=std::this_thread::get_id())return false;
    const auto entry=data->entry;
    const auto actual=entry->session.lock();
    if(actual.get()!=this)return false;
    return impl_->normal_initialization.load()==data && impl_->normal_entry.load()==entry &&
        !entry->retired.load() && !closing() && recovered_world_ready() &&
        impl_->mode==ProtocolMode::God2CharacterConnection &&
        (state()==SessionState::CharacterSelected || state()==SessionState::InWorld) &&
        entry->account==account_id && entry->character==character_id && data->effective_battle==battle_generation();
}
std::optional<Session::NormalWorldOutputHandle> Session::capture_normal_world_output(
        const NormalWorldInitialization& initialization) {
    if(observed_world_callback!=this)
        throw std::logic_error("Normal output recipient requires its own actual world callback");
    return capture_normal_world_output_on_game(initialization);
}
std::optional<Session::NormalWorldOutputHandle> Session::capture_normal_world_output_on_game(
        const NormalWorldInitialization& initialization) {
    if(!normal_world_initialization_current_on_game(initialization) || !initialization.entry_written())return std::nullopt;
    std::lock_guard lock(impl_->normal_output_sync->mutex);
    const auto epoch=impl_->normal_output_sync->epoch.load();
    if(epoch==std::numeric_limits<std::uint64_t>::max())return std::nullopt;
    auto data=std::make_shared<NormalWorldOutputHandle::Data>(impl_->normal_output_sync,initialization.data_,epoch,state());
    if(!impl_->normal_output_transport_current_locked(data) ||
       !normal_world_initialization_current_on_game(initialization))return std::nullopt;
    return NormalWorldOutputHandle(std::move(data));
}
bool Session::normal_world_output_current_on_game(const NormalWorldOutputHandle& handle) const {
    const auto data=handle.data_;
    if(!data || !data->initialization || !data->initialization->entry ||
       data->initialization->entry->game_thread!=std::this_thread::get_id())return false;
    const auto actual=data->initialization->entry->session.lock();
    if(actual.get()!=this)return false; // No game-owned fields before exact thread/Session qualification.
    std::lock_guard lock(data->sync->mutex);
    return impl_->normal_output_transport_current_locked(data) &&
        account_id==data->account && character_id==data->character;
}
Session::NormalWorldOutputAttempt Session::send_normal_world_records(
        const NormalWorldOutputHandle& handle,std::vector<std::uint8_t> logical) {
    const auto component=impl_->observe_callback_push(WorldCallbackOutput::Kind::NormalWorldRecords,logical);
    (void)retire_battle_self_view_logical_output(logical);
    [[maybe_unused]] const auto status_admission=begin_actor_status_writer();
    invalidate_actor_status_writes();
    auto data=std::make_shared<NormalWorldOutputAttempt::Data>();
    const NormalWorldOutputAttempt result(data);
    const auto pending=std::make_shared<Impl::NormalOutputPending>(data);
    if(!normal_world_output_current_on_game(handle))return result;
    if(logical.empty() || logical.size()>RecoveredWorldFrame::max_logical_size) {close();return result;}
    const auto charge=logical.size()+3;
    auto budget=impl_->budget;std::shared_ptr<Reservation> reservation;
    {
        std::lock_guard lock(budget->mutex);
        if(charge<=max_buffer-budget->bytes && budget->count<max_writes) {
            reservation=std::make_shared<Reservation>(budget,charge);
            budget->bytes+=charge;++budget->count;
        }
    }
    if(!reservation) {close();return result;}
    // All game-owned capture is complete before post. Strand never reads bare
    // public account_id/character_id or invokes a game Current/source callback.
    const auto recipient=handle.data_;
    impl_->post_status_work(impl_->strand,[self=shared_from_this(),recipient,logical=std::move(logical),reservation,pending,component]() mutable {
        auto& s=*self->impl_;
                [[maybe_unused]] const auto status_admission=self->begin_actor_status_writer();
        if(s.closing || s.close_requested.load())return;
        if(s.mode!=ProtocolMode::God2CharacterConnection || s.c2s0002_state!=Impl::C2S0002State::WorldTailAccepted)return;
        try {
            auto bytes=std::make_shared<std::vector<std::uint8_t>>(RecoveredWorldFrame::encode(logical));
            if(bytes->size()>max_buffer-s.write_bytes || s.writes.size()>=max_writes) {
                s.fail("Normal world output queue limit");return;
            }
            if(!s.terminal_write_allowed())return;
            {
                std::lock_guard lock(recipient->sync->mutex);
                if(!s.normal_output_transport_current_locked(recipient))return;
                Impl::Write output{bytes,std::move(reservation)};
                if(component){component->frame=bytes;component->receipt->wire.store(bytes);output.callback_component=component;}
                s.append_write(std::move(output));
                s.write_bytes+=bytes->size();
                auto expected=NormalWorldOutputStatus::Pending;
                pending->data->status.compare_exchange_strong(expected,NormalWorldOutputStatus::Queued);
            }
            if(s.writes.size()==1)s.write();
        }catch(...) {s.fail("Normal world output encoding or handoff failed");}
    });
    return result;
}
std::optional<Session::NormalWorldCallbackAdmission> Session::capture_normal_world_callback_admission(
        const NormalWorldInitialization& initialization) {
    if(observed_world_callback!=this || !observed_response_poison || *observed_response_poison) {
        poison_world_response();
        throw std::logic_error("Callback admission requires its own actual unpoisoned callback");
    }
    if(const auto existing=impl_->normal_callback_admission_capture) {
        const NormalWorldCallbackAdmission result(existing->receipt);
        if(existing->receipt->source->initialization==initialization.data_ &&
           result.status()==NormalWorldCallbackAdmissionStatus::Pending &&
           normal_world_callback_admission_current_on_game(result))return result;
        poison_world_response();existing->fail();
        throw std::logic_error("Actual callback admission identity changed");
    }
    auto source=capture_normal_world_output(initialization);
    if(!source)return std::nullopt;
    auto data=std::make_shared<NormalWorldCallbackAdmission::Data>(source->data_);
    impl_->normal_callback_admission_capture=std::make_shared<Impl::NormalCallbackPending>(data);
    observed_callback_admission_status=&data->status;
    return NormalWorldCallbackAdmission(std::move(data));
}
bool Session::normal_world_callback_admission_callback_current_on_game(const NormalWorldCallbackAdmission& admission) const noexcept {
    const auto& data=admission.data_;
    if(!data || data->game_thread!=std::this_thread::get_id() || observed_world_callback!=this)return false;
    const auto& capture=impl_->normal_callback_admission_capture;
    return capture && capture->receipt==data && observed_callback_admission_status==&data->status;
}
bool Session::normal_world_callback_admission_current_on_game(const NormalWorldCallbackAdmission& admission) const {
    const auto data=admission.data_;
    if(!data || data->game_thread!=std::this_thread::get_id() ||
       data->status.load()==NormalWorldCallbackAdmissionStatus::Failed)return false;
    // Existing predicate proves actual Entry thread/Session before bare IDs.
    return normal_world_output_current_on_game(NormalWorldOutputHandle(data->source));
}
std::optional<Session::NormalWorldResponseAttempt> Session::capture_normal_world_response(
        const NormalWorldInitialization& initialization) {
    if(observed_world_callback!=this || !observed_response_poison)
        throw std::logic_error("Normal original response requires own actual callback");
    if(*observed_response_poison)return std::nullopt;
    if(!normal_world_initialization_current(initialization))return std::nullopt;
    if(const auto existing=impl_->normal_response_callback_capture) {
        const NormalWorldResponseAttempt result(existing->receipt);
        if(existing->receipt->recipient->initialization==initialization.data_ &&
           normal_world_response_callback_current(result))return result;
        poison_world_response();existing->fail();
        throw std::logic_error("Normal original response callback identity changed");
    }
    std::lock_guard lock(impl_->normal_output_sync->mutex);
    const auto epoch=impl_->normal_output_sync->epoch.load();
    if(epoch==std::numeric_limits<std::uint64_t>::max())return std::nullopt;
    auto recipient=std::make_shared<NormalWorldOutputHandle::Data>(impl_->normal_output_sync,initialization.data_,epoch,state());
    if(!impl_->normal_response_transport_current_locked(recipient))return std::nullopt;
    auto data=std::make_shared<NormalWorldResponseAttempt::Data>(std::move(recipient));
    impl_->normal_response_callback_capture=std::make_shared<Impl::NormalResponsePending>(data);
    observed_normal_response_status=&data->status;
    return NormalWorldResponseAttempt(std::move(data));
}
void Session::expect_normal_world_response(const NormalWorldResponseAttempt& attempt,
        std::span<const std::uint8_t> framed_component) {
    if(!normal_world_response_callback_current(attempt)) {
        poison_world_response();
        if(impl_->normal_response_callback_capture)impl_->normal_response_callback_capture->fail();
        throw std::logic_error("Normal original component requires its own current callback");
    }
    if(framed_component.empty())return;
    const auto pending=impl_->normal_response_callback_capture;
    pending->receipt->armed.store(true); // Every following failure retires the actual live source.
    try {
        if(pending->receipt->components.size()>=8192 ||
           framed_component.size()>max_buffer-pending->receipt->component_bytes ||
           !Impl::valid_world_response(framed_component))
            throw std::invalid_argument("Normal original response component bounds or frame invalid");
        pending->receipt->components.emplace_back(framed_component.begin(),framed_component.end());
        pending->receipt->component_bytes+=framed_component.size();
    } catch(...) {poison_world_response();pending->fail();throw;}
}
bool Session::normal_world_response_current_on_game(const NormalWorldResponseAttempt& attempt) const {
    const auto data=attempt.data_;
    if(!data || data->game_thread!=std::this_thread::get_id() || data->status.load()==NormalWorldResponseStatus::Failed)return false;
    const auto recipient=data->recipient;
    if(!recipient || !recipient->initialization || !recipient->initialization->entry ||
       recipient->initialization->entry->game_thread!=std::this_thread::get_id() ||
       recipient->initialization->entry->session.lock().get()!=this)return false;
    std::lock_guard lock(recipient->sync->mutex);
    return data->status.load()!=NormalWorldResponseStatus::Failed && impl_->normal_response_transport_current_locked(recipient) &&
        account_id==recipient->account && character_id==recipient->character;
}
bool Session::normal_world_response_callback_current(const NormalWorldResponseAttempt& attempt) const {
    if(observed_world_callback!=this || !observed_response_poison || *observed_response_poison)return false;
    const auto capture=impl_->normal_response_callback_capture;
    return capture && capture->receipt==attempt.data_ && normal_world_response_current_on_game(attempt);
}
void Session::send_world_records_impl(std::vector<std::uint8_t> logical,
        std::shared_ptr<WorldRecordsWrite::Data> observed,std::optional<WorldCallbackSelectionEmission> emission) {
    if(qualified_world_push_profile){
        (void)retire_battle_self_view_logical_output(logical);[[maybe_unused]] const auto status_admission=begin_actor_status_writer();invalidate_actor_status_writes();
        impl_->reject_qualified_profile_sender();
    }
    // Cleanup may broadcast party departure to the departing self. Its old
    // FIFO has drained; this terminal recipient must not mint another push.
    if(impl_->native_logout_terminal.load())return;
    if(observed_world_callback==this&&impl_->reply_push_capture){
        (void)retire_battle_self_view_logical_output(logical);
        [[maybe_unused]] const auto status_admission=begin_actor_status_writer();invalidate_actor_status_writes();
        if(observed||emission){impl_->fail_reply_pushes();throw std::logic_error("Observed/C67 sender cannot use generic reply capture");}
        impl_->capture_reply_push(logical);return;
    }
    const auto component=impl_->observe_callback_push(WorldCallbackOutput::Kind::WorldRecords,logical);
    if(emission)impl_->bind_side_emission(component,*emission,logical);
    (void)retire_battle_self_view_logical_output(logical);
    [[maybe_unused]] const auto status_admission=begin_actor_status_writer();
    invalidate_actor_status_writes();
    const auto attempt=observed?std::make_shared<Impl::WorldWriteAttempt>(std::move(observed)):
        std::shared_ptr<Impl::WorldWriteAttempt>{};
    if(impl_->close_requested.load()) return;
    if(logical.empty() || logical.size()>RecoveredWorldFrame::max_logical_size) { close();return; }
    const auto charge=logical.size()+3;
    auto budget=impl_->budget;
    std::shared_ptr<Reservation> reservation;
    {
        std::lock_guard lock(budget->mutex);
        if(charge<=max_buffer-budget->bytes && budget->count<max_writes) {
            reservation=std::make_shared<Reservation>(budget,charge);
            budget->bytes+=charge;
            ++budget->count;
        }
    }
    if(!reservation) { close();return; }
    impl_->post_status_work(impl_->strand,[self=shared_from_this(),logical=std::move(logical),reservation,attempt,component]() mutable {
        auto& s=*self->impl_;
                [[maybe_unused]] const auto status_admission=self->begin_actor_status_writer();
        if(s.closing || s.close_requested.load() || s.native_logout_terminal.load()) return;
        if(!is_recovered(s.mode) || s.c2s0002_state!=Impl::C2S0002State::WorldTailAccepted) {
            s.fail("Recovered world push before accepted world tail");return;
        }
        try {
            if(attempt && attempt->receipt->logical!=logical) {
                s.fail("Observed world logical batch identity mismatch");return;
            }
            auto bytes=std::make_shared<std::vector<std::uint8_t>>(RecoveredWorldFrame::encode(logical));
            if(bytes->size()>max_buffer-s.write_bytes || s.writes.size()>=max_writes) {
                s.fail("Recovered world push queue limit");return;
            }
            if(!s.terminal_write_allowed())return;
            s.write_bytes+=bytes->size();
            if(attempt)attempt->frame=bytes;
            Impl::Write output{bytes,std::move(reservation),false,false,{},{},{},attempt};
            if(component){component->frame=bytes;component->receipt->wire.store(bytes);output.callback_component=component;}
            s.append_write(std::move(output));
            if(s.writes.size()==1) s.write();
        } catch(...) { s.fail("Recovered world push encoding failed"); }
    });
}
void Session::bind_world_delivery_identity(WorldDeliveryIdentity identity) {
    if(!identity.account || !identity.character || !identity.world_generation)
        throw std::invalid_argument("Complete owned world delivery identity required");
    impl_->world_delivery_identity.store(std::make_shared<const WorldDeliveryIdentity>(identity));
}
bool Session::install_common_world_cleanup(std::function<void()> cleanup,std::function<void()> terminal_begin,std::function<bool(bool)> terminal_finish) {
    if(bool(terminal_begin)!=bool(terminal_finish)||!cleanup||closing()||impl_->mode!=ProtocolMode::God2CharacterConnection||
       !impl_->character_handlers.common_world_lifecycle||impl_->common_world_cleanup||impl_->common_world_terminal_begin||impl_->common_world_terminal_finish)return false;
    if(const auto& own=impl_->character_handlers.common_world_cleanup_owner; own) {
        try {cleanup=own(*this,std::move(cleanup));}catch(...) {return false;}
        if(!cleanup)return false;
    }
    if(closing()||impl_->common_world_cleanup||impl_->common_world_terminal_begin||impl_->common_world_terminal_finish)return false;
    impl_->common_world_cleanup=std::move(cleanup);
    impl_->common_world_terminal_begin=std::move(terminal_begin);impl_->common_world_terminal_finish=std::move(terminal_finish);return true;
}
void Session::mark_common_world_cleanup_failed() noexcept {
    // Actual lifecycle/vault GAME cleanup callers may only make this Session
    // permanently less permissive, including before a ready receipt exists.
    impl_->common_world_cleanup_failed.store(true);
}
bool Session::closing() const noexcept {return impl_->close_requested.load()||impl_->native_logout_terminal.load();}
std::optional<Session::NativeWorldSelectionInput> Session::take_world_selection_input(
    const RecoveredSelectionItemRequest::Request& request) {
    const auto window=impl_->selection_window;
    if(!window)return std::nullopt;
    if(window->thread!=std::this_thread::get_id())throw std::logic_error("Native C28 take game owner mismatch");
    for(auto& entry:window->entries)if(entry.original==&request) {
        NativeWorldSelectionInput input(entry.data);
        if(entry.taken || !impl_->selection_entry(input) || request.client_item_id!=input.request().client_item_id ||
           request.raw_slot!=input.request().raw_slot) {window->live=false;return std::nullopt;}
        entry.taken=true;return input;
    }
    window->live=false;return std::nullopt;
}
bool Session::claim_world_selection_action(const NativeWorldSelectionInput& input) {
    auto* entry=impl_->selection_entry(input);
    if(!entry || !entry->taken || entry->dispatched) {
        if(impl_->selection_window)impl_->selection_window->live=false;
        return false;
    }
    entry->dispatched=true;return true;
}
bool Session::world_selection_input_current(const NativeWorldSelectionInput& input) const {
    const auto* entry=impl_->selection_entry(input);return entry && entry->taken;
}
void Session::bind_common_world_delivery_identity(std::uint64_t account,std::uint64_t character,std::uint64_t generation) {
    if(!account || !character || !generation || closing() || account_id!=account || character_id!=character ||
       !recovered_world_ready() || state()!=SessionState::InWorld ||
       impl_->mode!=ProtocolMode::God2CharacterConnection || !impl_->character_handlers.common_world_lifecycle)
        throw std::invalid_argument("Actual ready common-world identity required");
    const auto identity=std::make_shared<const Impl::CommonWorldIdentity>(Impl::CommonWorldIdentity{account,character,generation});
    std::shared_ptr<const Impl::CommonWorldIdentity> absent;
    if(!impl_->common_world_identity.compare_exchange_strong(absent,identity))
        throw std::logic_error("Common world delivery identity already bound");
}
void Session::release_common_world_delivery_identity(std::uint64_t account,std::uint64_t character,std::uint64_t generation) {
    [[maybe_unused]] const auto status_admission=begin_actor_status_writer();
    invalidate_actor_status_writes();
    auto current=impl_->common_world_identity.load();
    if(current && current->account==account && current->character==character && current->generation==generation)
        impl_->common_world_identity.compare_exchange_strong(current,{});
}
bool Session::common_world_delivery_current(std::uint64_t account,std::uint64_t character,std::uint64_t generation) const {
    const auto current=impl_->common_world_identity.load();
    return account && character && generation && !closing() && current &&
        current->account==account && current->character==character && current->generation==generation;
}
void Session::bind_common_world_entry_identity(std::uint64_t account,std::uint64_t character,std::uint64_t generation) {
    if(impl_->common_ready_thread!=std::this_thread::get_id())
        throw std::logic_error("Pending common entry game owner mismatch");
    const auto state=this->state();
    if(!account || !character || !generation || account_id!=account || character_id!=character || closing() ||
       !recovered_world_ready() || (state!=SessionState::CharacterSelected && state!=SessionState::InWorld) ||
       impl_->mode!=ProtocolMode::God2CharacterConnection || !impl_->common_ready_waiting.load() ||
       !impl_->character_handlers.common_world_publication_owner || impl_->common_world_identity.load() ||
       impl_->common_entry_nonce==std::numeric_limits<std::uint64_t>::max())
        throw std::invalid_argument("Pending common entry requires actual deferred tail/session identity");
    auto identity=std::make_shared<const Impl::CommonEntryIdentity>(Impl::CommonEntryIdentity{
        account,character,generation,++impl_->common_entry_nonce,battle_generation(),state});
    std::shared_ptr<const Impl::CommonEntryIdentity> absent;
    if(!impl_->common_entry_identity.compare_exchange_strong(absent,identity))
        throw std::invalid_argument("Pending common entry already bound");
}
void Session::release_common_world_entry_identity(std::uint64_t account,std::uint64_t character,std::uint64_t generation) {
    [[maybe_unused]] const auto status_admission=begin_actor_status_writer();
    invalidate_actor_status_writes();
    auto current=impl_->common_entry_identity.load();
    if(current && current->account==account && current->character==character && current->generation==generation)
        impl_->common_entry_identity.compare_exchange_strong(current,{});
}
bool Session::common_world_entry_current(std::uint64_t account,std::uint64_t character,std::uint64_t generation) const {
    const auto current=impl_->common_entry_identity.load();
    return current && !closing() && recovered_world_ready() && current->account==account &&
        current->character==character && current->generation==generation && current->battle==battle_generation();
}
void Session::send_common_world_entry_with_publication(std::vector<std::uint8_t> logical,
    std::uint64_t account,std::uint64_t character,std::uint64_t generation,
    std::function<bool()> publish,std::function<void(bool)> queued,std::optional<InitialActorStatusInput> status) {
    impl_->unsupported_callback_output();
    (void)retire_battle_self_view_logical_output(logical);
    [[maybe_unused]] const auto status_admission=begin_actor_status_writer();
    invalidate_actor_status_writes();
    if(impl_->common_ready_thread!=std::this_thread::get_id())
        throw std::logic_error("Pending common publication game owner mismatch");
    if(!queued)throw std::invalid_argument("Pending common entry completion required");
    const auto pending=impl_->common_entry_identity.load();
    if(!publish || !pending || !common_world_entry_current(account,character,generation) ||
       account_id!=account || character_id!=character || logical.empty() ||
       logical.size()>RecoveredTaiwanServerRecords::max_aggregate_logical_size || !impl_->character_handlers.common_world_publication_owner) {
        try {queued(false);}catch(...) {}close();return;
    }
    // Only this explicit native entry path accepts a larger complete grammar
    // aggregate. Native record limits and all generic world sends stay unchanged.
    std::optional<std::vector<RecoveredTaiwanServerRecords::Record>> records;
    try {records=RecoveredTaiwanServerRecords::read_aggregate(logical);}catch(...) {}
    if(!records) {try {queued(false);}catch(...) {}close();return;}
    const auto status_current=[&] {
        if(!status)return true; // Frozen no-input sender remains supported.
        const auto& recipient=status->recipient;
        if(recipient.session!=id()||recipient.account!=account||recipient.character!=character||
           recipient.generation!=generation)return false;
        std::size_t index=0;
        for(std::size_t i=0;i<records->size();++i){
            const auto& record=(*records)[i];if(record.opcode!=0x6f)continue;
            if(index>=status->actors.size()||status->actors[index].aggregate_offset!=record.offset)return false;
            const auto& unit=status->actors[index++].actor;if(!unit)continue;
            constexpr auto actor_size=RecoveredRemoteActor::logical_size;
            constexpr auto override_size=RecoveredTaiwanActorOverride::logical_size;
            if(record.bytes.size()!=actor_size||i+1>=records->size()||(*records)[i+1].opcode!=0xea||
               (*records)[i+1].offset!=record.offset+actor_size||(*records)[i+1].bytes.size()!=override_size||
               unit->recipient()!=recipient||unit->source().session==recipient.session||
               unit->logical().size()!=actor_size+override_size||
               !std::equal(unit->logical().begin(),unit->logical().end(),logical.begin()+record.offset)||
               !unit->retained())return false;
            const auto actor=RecoveredRemoteActor::parse_logical(record.bytes);
            const auto replay=RecoveredTaiwanActorOverride::parse_logical((*records)[i+1].bytes);
            if(!actor||!replay||actor->identity()!=unit->source().actor_handle||
               replay->identity()!=actor->identity())return false;
        }
        return index==status->actors.size();
    };
    if(!status_current()){try {queued(false);}catch(...) {}close();return;}
    CommonWorldPublication owned;
    try {owned=impl_->character_handlers.common_world_publication_owner(*this,{std::move(publish),std::move(queued)});}
    catch(...) {close();return;}
    if(!owned.publish || !owned.queued){close();return;}
    // Both functions are revocable facades; actual captures remain on game.
    const auto finish=[self=shared_from_this(),queued=std::move(owned.queued)](bool accepted) {
        const auto delivery=std::make_shared<Impl::InitialEntryQueuedDelivery>(self);
        self->impl_->post_status_work(self->impl_->game,[queued,accepted,delivery] {
            delivery->delivered.store(true); // Actual game delivery, never mere post acceptance.
            try {queued(accepted);}catch(...) {}
        });
    };
    const auto before=[self=shared_from_this(),pending,account,character,generation] {
        return self->impl_->common_entry_identity.load()==pending &&
            self->common_world_entry_current(account,character,generation) &&
            self->state()==pending->state && !self->impl_->common_world_identity.load();
    };
    const auto after=[self=shared_from_this(),pending,account,character,generation] {
        return self->impl_->common_entry_identity.load()==pending &&
            self->common_world_entry_current(account,character,generation) &&
            self->state()==SessionState::InWorld && self->common_world_delivery_current(account,character,generation);
    };
    if(!before()||!status_current()){close();finish(false);return;}
    std::shared_ptr<Impl::InitialEntryAttempt> attempt;
    try {
        attempt=std::make_shared<Impl::InitialEntryAttempt>(weak_from_this(),finish);
        const auto status_context=status?std::make_shared<Impl::InitialEntryStatusContext>(shared_from_this(),status->recipient):nullptr;
        const auto identity=std::make_shared<Impl::InitialEntryIdentity>(status_context);
        std::vector<std::shared_ptr<Impl::InitialEntryMember>> members;
        std::vector<std::shared_ptr<Impl::ActiveWriteContinuation>> holders;
        std::vector<std::uint8_t> part;part.reserve(RecoveredWorldFrame::max_logical_size);
        std::vector<TaiwanActorStatusPublication::FrameSeal::Data::Unit> status_units;
        std::size_t charge=0,actor_index=0;
        const auto flush=[&] {
            if(part.empty())return;
            if(members.size()>=max_writes)throw std::length_error("Initial aggregate exceeds frame budget");
            auto bytes=std::make_shared<std::vector<std::uint8_t>>(RecoveredWorldFrame::encode(part));
            if(bytes->size()>max_buffer-charge)throw std::length_error("Initial aggregate exceeds byte budget");
            std::optional<TaiwanActorStatusPublication::FrameSeal> seal;
            if(!status_units.empty()){
                const auto data=std::make_shared<TaiwanActorStatusPublication::FrameSeal::Data>(status_context->identity,
                    shared_from_this(),members.size(),part.size(),bytes,std::move(status_units));
                if(!data->retained())throw std::logic_error("Initial owned-status retired during exact framing");
                seal=TaiwanActorStatusPublication::FrameSeal(data);
            }
            const auto member=std::make_shared<Impl::InitialEntryMember>(identity,members.size(),bytes,std::move(seal));
            const auto holder=std::make_shared<Impl::ActiveWriteContinuation>(nullptr,bytes);
            members.push_back(member);holders.push_back(holder);charge+=bytes->size();part.clear();status_units.clear();
        };
        for(std::size_t i=0;i<records->size();++i){
            const auto& record=(*records)[i];std::size_t size=record.bytes.size();
            // Adjacent full6F+EA is one unit. Do not split, skip or reinterpret
            // opaque bytes; semantic actor/status qualification stays with Source.
            if(record.opcode==0x6f&&i+1<records->size()&&(*records)[i+1].opcode==0xea)
                size+=(*records)[++i].bytes.size();
            if(size>RecoveredWorldFrame::max_logical_size)throw std::length_error("Initial record unit exceeds frame");
            if(part.size()>RecoveredWorldFrame::max_logical_size-size)flush();
            if(status&&record.opcode==0x6f){
                const auto& unit=status->actors[actor_index++].actor;
                if(unit)status_units.push_back({part.size(),*unit});
            }
            part.insert(part.end(),logical.begin()+record.offset,logical.begin()+record.offset+size);
        }
        flush();
        if(status_context)status_context->frame_count.store(members.size());
        if(members.empty()||!before()||!status_current()||
           (status&&actor_index!=status->actors.size()))throw std::logic_error("Initial aggregate source retired during framing");
        const auto budget=impl_->budget;
        // Allocate uncharged OUTSIDE the mutex. An allocation/new-handler may
        // reenter close and release older tickets without deadlocking this lock.
        auto reservation=std::make_shared<Reservation>(budget,charge,members.size(),false);
        bool charged=false;
        {
            std::lock_guard lock(budget->mutex);
            if(budget->bytes<=max_buffer&&budget->count<=max_writes&&charge<=max_buffer-budget->bytes&&
               members.size()<=max_writes-budget->count){
                budget->bytes+=charge;budget->count+=members.size();
                reservation->charged=true;charged=true; // No allocation/destruction under lock.
            }
        }
        if(!charged)throw std::length_error("Initial aggregate reservation exhausted");
        // One aggregate reservation refunds its exact byte/count charge once,
        // conservatively when the LAST frame/task reference is released.
        const auto cohort=std::make_shared<const Impl::InitialEntryCohort>(identity,std::move(members),
            std::move(holders),std::move(reservation),charge);
        std::vector<Impl::Write> prepared;prepared.reserve(cohort->members.size());
        for(std::size_t i=0;i<cohort->members.size();++i){
            Impl::Write value{cohort->members[i]->frame,cohort->reservation,false,true};
            value.pending_return_continuation=cohort->holders[i];
            value.initial_entry=std::make_shared<Impl::InitialEntryQueueTicket>(cohort->members[i]);
            prepared.push_back(std::move(value));
        }
        if(!before()||!status_current())throw std::logic_error("Initial status retired after queue preparation");
        for(const auto& member:cohort->members)if(!member->retained_status())
            throw std::logic_error("Initial exact status frame retired before queue handoff");
        impl_->post_status_work(impl_->strand,[self=shared_from_this(),cohort,attempt,prepared=std::move(prepared),before,after,
                account,character,publish=std::move(owned.publish)]() mutable {
            auto& s=*self->impl_;
            [[maybe_unused]] const auto status_admission=self->begin_actor_status_writer();
            if(s.closing||!before()||s.mode!=ProtocolMode::God2CharacterConnection||
               s.c2s0002_state!=Impl::C2S0002State::WorldTailAccepted){
                s.fail("Stale pending common entry publication");attempt->abort();return;
            }
            try {
                if(s.write_bytes>max_buffer||s.writes.size()>max_writes||cohort->charge>max_buffer-s.write_bytes||
                   cohort->members.size()>max_writes-s.writes.size()||prepared.size()!=cohort->members.size())
                    throw std::length_error("Pending common entry aggregate queue limit");
                if(!s.terminal_write_allowed()){attempt->abort();return;}
                // All encoding/tickets/holders are complete before the FIRST
                // append. A failed append leaves only held bytes; fail() clears
                // that entire unpublished prefix before any write can start.
                for(std::size_t i=0;i<prepared.size();++i){
                    if(!before()||cohort->identity->revoked.load()||
                       cohort->identity->phase.load()!=Impl::InitialEntryIdentity::Phase::Preparing)
                        throw std::logic_error("Initial aggregate retired during insertion");
                    s.append_write(std::move(prepared[i]));s.write_bytes+=cohort->members[i]->frame->size();
                    cohort->members[i]->present.store(true);
                }
                auto preparing=Impl::InitialEntryIdentity::Phase::Preparing;
                if(!cohort->identity->phase.compare_exchange_strong(preparing,Impl::InitialEntryIdentity::Phase::Installed))
                    throw std::logic_error("Initial aggregate installed twice");
                std::size_t first=0;
                if(!before()||!s.initial_entry_queued(cohort,Impl::InitialEntryIdentity::Phase::Installed,first))
                    throw std::logic_error("Initial aggregate not wholly held before publication");
                // Only private queue tickets can revoke/remove membership. The
                // game task validates ALL their atomic presences without reading
                // the strand deque. No held frame can be popped by write().
                s.post_status_work(s.game,[self,cohort,attempt,before,after,account,character,publish=std::move(publish)] {
                    bool accepted=false;
                    try {
                        auto installed=Impl::InitialEntryIdentity::Phase::Installed;
                        accepted=cohort->held_current(installed)&&before()&&self->account_id==account&&
                            self->character_id==character&&cohort->identity->phase.compare_exchange_strong(
                                installed,Impl::InitialEntryIdentity::Phase::Publishing);
                        if(accepted)accepted=cohort->held_current(Impl::InitialEntryIdentity::Phase::Publishing)&&
                            before()&&publish()&&after()&&self->account_id==account&&self->character_id==character&&
                            cohort->held_current(Impl::InitialEntryIdentity::Phase::Publishing);
                        auto publishing=Impl::InitialEntryIdentity::Phase::Publishing;
                        accepted=accepted&&cohort->identity->phase.compare_exchange_strong(publishing,
                            Impl::InitialEntryIdentity::Phase::Published);
                    }catch(...) {}
                    try {self->impl_->post_status_work(self->impl_->strand,[self,cohort,attempt,after,accepted] {
                        auto& s=*self->impl_;
                        [[maybe_unused]] const auto status_admission=self->begin_actor_status_writer();
                        try {
                            std::size_t first=0;
                            if(!accepted||s.closing||!after()||s.c2s0002_state!=Impl::C2S0002State::WorldTailAccepted||
                               !s.initial_entry_queued(cohort,Impl::InitialEntryIdentity::Phase::Published,first))
                                throw std::logic_error("Pending common entry whole cohort refused");
                            // Preserve any real earlier PK task custody. Each
                            // held frame has its OWN exact-frame holder; queued
                            // metadata never becomes the strong task owner.
                            std::shared_ptr<NativePkReturnPublication::Work> carried;
                            for(const auto& holder:cohort->holders)if(holder->work){
                                if(carried&&carried!=holder->work)throw std::logic_error("Initial cohort has conflicting PK continuations");
                                carried=holder->work;
                            }
                            if(first&&carried){
                                const auto active=s.active_write_continuation.lock();
                                if(active){
                                    if(active->frame!=s.writes.front().bytes||(active->work&&active->work!=carried))
                                        throw std::logic_error("Initial cohort older active continuation mismatch");
                                    active->work=carried;
                                }else{
                                    const auto pending=s.writes.front().pending_return_continuation.lock();
                                    if(!pending||!s.writes.front().held||pending->frame!=s.writes.front().bytes||
                                       (pending->work&&pending->work!=carried))
                                        throw std::logic_error("Initial cohort older held continuation mismatch");
                                    pending->work=carried;
                                }
                            }
                            // Validate the ENTIRE exact contiguous cohort before
                            // unholding ANY member. The following transition and
                            // flag writes do not allocate, publish or pump events.
                            if(!after()||!s.initial_entry_queued(cohort,Impl::InitialEntryIdentity::Phase::Published,first))
                                throw std::logic_error("Initial cohort retired before whole release");
                            auto published=Impl::InitialEntryIdentity::Phase::Published;
                            if(!cohort->identity->phase.compare_exchange_strong(published,Impl::InitialEntryIdentity::Phase::Released))
                                throw std::logic_error("Initial aggregate released twice");
                            for(std::size_t i=0;i<cohort->members.size();++i)s.writes[first+i].held=false;
                            if(!first)s.write(std::move(carried));
                            attempt->complete(true); // WHOLE queue release only; no socket/native ACK.
                        }catch(...){s.fail("Pending common entry aggregate release failed");attempt->abort();}
                    });}catch(...){cohort->identity->revoke();attempt->abort();}
                });
            }catch(...){cohort->identity->revoke();s.fail("Pending common entry aggregate insertion failed");attempt->abort();}
        });
    }catch(...){if(attempt)attempt->abort();else{close();finish(false);}}
}
void Session::send_common_world_records_with_publication(std::vector<std::uint8_t> logical,
    std::uint64_t account,std::uint64_t character,std::uint64_t generation,
    std::function<bool()> publish,std::function<void(bool)> queued,std::optional<ActorStatusOutputInput> status,
    std::optional<SharedWorldPresence::Lease> publication_recipient) {
    impl_->unsupported_callback_output();
    (void)retire_battle_self_view_logical_output(logical);
    std::shared_ptr<std::atomic<Impl::CommonPublicationReleasePhase>> release;
    std::shared_ptr<Impl::InitialEntryAttempt> ready_attempt;
    std::optional<TaiwanActorStatusWriteFence::Writer> ready_status_writer;
    if(publication_recipient) {
        if(status)throw std::invalid_argument("Ready Lease and actor-status publication are mutually exclusive");
        if(impl_->common_ready_thread==std::thread::id{} || impl_->common_ready_thread!=std::this_thread::get_id())
            throw std::logic_error("Ready publication requires actual GAME owner");
        // The new GAME adoption/callback destruction/drain belongs inside the
        // existing writer monitor, before any allocation or real vault call.
        ready_status_writer=begin_actor_status_writer();invalidate_actor_status_writes();
        // Allocate the empty affine box and pure latch BEFORE moving payload.
        // Failed allocation can still complete the untouched caller on GAME.
        std::shared_ptr<Impl::OutwardPublicationSubmission> submission;
        try {
            submission=std::make_shared<Impl::OutwardPublicationSubmission>();
            release=std::make_shared<std::atomic<Impl::CommonPublicationReleasePhase>>(
                Impl::CommonPublicationReleasePhase::Pending);
        }catch(...){try{if(queued)queued(false);}catch(...){}close();return;}
        submission->actual={std::move(publish),std::move(queued)};publish={};queued={};
        CommonWorldPublication owned;
        try {
            const auto self=shared_from_this();const auto common=impl_->common_world_identity.load();
            const auto& recipient=*publication_recipient;
            if(!submission->actual.publish || !submission->actual.queued ||
               !impl_->character_handlers.common_world_ready_publication_owner || !common ||
               recipient.session!=id() || recipient.account!=account || recipient.character!=character ||
               recipient.generation!=generation || common->account!=account || common->character!=character ||
               common->generation!=generation || !account || !character || !generation ||
               account_id!=account || character_id!=character || closing() || !recovered_world_ready() ||
               state()!=SessionState::InWorld || impl_->common_entry_identity.load() ||
               impl_->mode!=ProtocolMode::God2CharacterConnection || logical.empty() ||
               logical.size()>RecoveredWorldFrame::max_logical_size)
                throw std::invalid_argument("Ready publication requires the actual complete ready recipient and callbacks");
            // Actual vault checks the FULL supplied Lease against its real
            // Presence/Session slot, then owns ALL affine captures on GAME.
            owned=impl_->character_handlers.common_world_ready_publication_owner(*this,recipient,
                {[submission]{return submission->publish();},[submission,release](bool) {
                    auto pending=Impl::CommonPublicationReleasePhase::Pending;
                    release->compare_exchange_strong(pending,Impl::CommonPublicationReleasePhase::Cancelled);
                    // Preserve true LOCAL release after a later phase/cleanup
                    // change. Cancel-before-release must instead prevent unhold.
                    submission->complete(release->load()==Impl::CommonPublicationReleasePhase::Released);
                }});
            if(!owned.publish || !owned.queued || submission->finished)
                throw std::logic_error("Ready vault did not retain complete actual callbacks");
            const auto finish=[self,queued_facade=owned.queued,release](bool accepted) {
                if(!accepted) {
                    auto pending=Impl::CommonPublicationReleasePhase::Pending;
                    release->compare_exchange_strong(pending,Impl::CommonPublicationReleasePhase::Cancelled);
                }
                const auto delivery=std::make_shared<Impl::InitialEntryQueuedDelivery>(self);
                self->impl_->post_status_work(self->impl_->game,[queued_facade,accepted,delivery] {
                    delivery->delivered.store(true);
                    try{queued_facade(accepted);}catch(...){}
                });
            };
            ready_attempt=std::make_shared<Impl::InitialEntryAttempt>(weak_from_this(),finish);
            publish=std::move(owned.publish);
            queued=[ready_attempt](bool accepted){ready_attempt->complete(accepted);};
            submission.reset(); // BEFORE the first IO post: no affine source in transport tasks.
        }catch(...) {
            if(release) {
                auto pending=Impl::CommonPublicationReleasePhase::Pending;
                release->compare_exchange_strong(pending,Impl::CommonPublicationReleasePhase::Cancelled);
            }
            if(submission)try{submission->complete(false);}catch(...){}
            if(ready_attempt)ready_attempt->abort();
            else {try{if(owned.queued)owned.queued(false);}catch(...){}close();}
            return; // Explicit capability never falls back to the legacy owner path.
        }
    }
    try {
    if(status){
        send_actor_status_output(std::move(logical),account,character,generation,
            std::move(publish),std::move(queued),std::move(*status));return;
    }
    [[maybe_unused]] const auto status_admission=begin_actor_status_writer();
    invalidate_actor_status_writes();
    if(!queued)throw std::invalid_argument("Common world publication completion required");
    auto completion=std::make_shared<std::function<void(bool)>>(std::move(queued));
    const auto finish=[self=shared_from_this(),completion,release](bool accepted) {
        if(release && !accepted) {
            auto pending=Impl::CommonPublicationReleasePhase::Pending;
            release->compare_exchange_strong(pending,Impl::CommonPublicationReleasePhase::Cancelled);
        }
        self->impl_->post_status_work(self->impl_->game,[completion,accepted] {
            auto callback=std::move(*completion);
            if(callback)try {callback(accepted);}catch(...) {}
        });
    };
    const auto battle=battle_generation();
    const auto common=[self=shared_from_this(),account,character,generation,battle] {
        const auto state=self->state();
        return self->common_world_delivery_current(account,character,generation) &&
            self->recovered_world_ready() && self->battle_generation()==battle &&
            (state==SessionState::InWorld || state==SessionState::CharacterSelected);
    };
    if(!publish || !common() || account_id!=account || character_id!=character || logical.empty() ||
       logical.size()>RecoveredWorldFrame::max_logical_size) {close();finish(false);return;}
    const auto charge=logical.size()+3;auto budget=impl_->budget;std::shared_ptr<Reservation> reservation;
    try {
        std::lock_guard lock(budget->mutex);
        if(charge<=max_buffer-budget->bytes && budget->count<max_writes) {
            reservation=std::make_shared<Reservation>(budget,charge);budget->bytes+=charge;++budget->count;
        }
    }catch(...) {close();finish(false);return;}
    if(!reservation){close();finish(false);return;}
    impl_->post_status_work(impl_->strand,[self=shared_from_this(),logical=std::move(logical),reservation,
        account,character,common,publish=std::move(publish),finish,release]() mutable {
        auto& s=*self->impl_;
                [[maybe_unused]] const auto status_admission=self->begin_actor_status_writer();
        if(s.closing || !common() || s.mode!=ProtocolMode::God2CharacterConnection ||
           s.c2s0002_state!=Impl::C2S0002State::WorldTailAccepted) {
            s.fail("Stale common world publication");finish(false);return;
        }
        try {
            auto bytes=std::make_shared<std::vector<std::uint8_t>>(RecoveredWorldFrame::encode(logical));
            if(bytes->size()>max_buffer-s.write_bytes || s.writes.size()>=max_writes) {
                s.fail("Common world publication queue limit");finish(false);return;
            }
            // Prepare the queue entry before accounting; allocation failure may
            // not strand bytes or the reservation. Prior writes may finish.
            if(!s.terminal_write_allowed()){finish(false);return;}
            const auto held_continuation=std::make_shared<Impl::ActiveWriteContinuation>(nullptr,bytes);
            s.append_write({bytes,std::move(reservation),false,true});s.write_bytes+=bytes->size();
            s.writes.back().pending_return_continuation=held_continuation;
            s.post_status_work(s.game,[self,bytes,held_continuation,account,character,common,publish=std::move(publish),finish,release]() mutable {
                bool accepted=false;
                try {
                    accepted=common() && self->account_id==account && self->character_id==character &&
                        publish() && common() && self->account_id==account && self->character_id==character;
                }catch(...) {}
                self->impl_->post_status_work(self->impl_->strand,[self,bytes,held_continuation,common,accepted,finish,release] {
                    auto& s=*self->impl_;
                [[maybe_unused]] const auto status_admission=self->begin_actor_status_writer();
                    if(!accepted || s.closing || !common() || s.c2s0002_state!=Impl::C2S0002State::WorldTailAccepted) {
                        s.fail("Common world publication refused");finish(false);return;
                    }
                    const auto held=std::find_if(s.writes.begin(),s.writes.end(),[&](const auto& entry){return entry.bytes==bytes;});
                    if(held==s.writes.end() || !held->held) {
                        s.fail("Common world held frame missing");finish(false);return;
                    }
                    if(release) {
                        auto pending=Impl::CommonPublicationReleasePhase::Pending;
                        if(!release->compare_exchange_strong(pending,Impl::CommonPublicationReleasePhase::Released)) {
                            s.fail("Ready publication cancelled before actual queue release");finish(false);return;
                        }
                    }
                    // No callback/allocation between this pure release CAS and
                    // unhold. A later write/post failure preserves Released.
                    held->held=false;
                    if(held==s.writes.begin())s.write(held_continuation->work);
                    finish(true); // Published before IO release; local queue only.
                });
            });
        }catch(...) {s.fail("Common world publication encoding failed");finish(false);}
    });
    }catch(...) {
        if(ready_attempt)ready_attempt->abort(); // Post/alloc throw cancels pending before preserving old rethrow.
        throw;
    }
}
std::size_t Session::common_world_publication_capacity() noexcept {return max_writes;}
void Session::send_actor_status_output(std::vector<std::uint8_t> logical,
        std::uint64_t account,std::uint64_t character,std::uint64_t generation,
        std::function<bool()> publish,std::function<void(bool)> queued,ActorStatusOutputInput input) {
    impl_->unsupported_callback_output();
    (void)retire_battle_self_view_logical_output(logical);
    if(impl_->common_ready_thread==std::thread::id{}||impl_->common_ready_thread!=std::this_thread::get_id())
        throw std::logic_error("Typed outward publication requires actual game owner");
    [[maybe_unused]] const auto status_admission=begin_actor_status_writer();
    invalidate_actor_status_writes();
    if(!queued)throw std::invalid_argument("Typed outward completion required");
    // Allocate empty BEFORE moving actual callbacks, so an allocation failure
    // can still complete the original caller on its real game owner.
    std::shared_ptr<Impl::OutwardPublicationSubmission> submission;
    try {submission=std::make_shared<Impl::OutwardPublicationSubmission>();}
    catch(...){try{queued(false);}catch(...){}close();return;}
    submission->actual={std::move(publish),std::move(queued)};publish={};queued={};
    std::shared_ptr<Impl::OutwardStatusAttempt> attempt;
    try {
        const auto self=shared_from_this();const auto common=impl_->common_world_identity.load();
        const auto battle=battle_generation();const auto& recipient=input.recipient;
        constexpr auto actor_size=RecoveredRemoteActor::logical_size;
        constexpr auto replay_size=RecoveredTaiwanActorOverride::logical_size;
        if(!submission->actual.publish||!impl_->character_handlers.common_world_ready_publication_owner||
           !common||common->account!=account||common->character!=character||common->generation!=generation||
           recipient.session!=id()||recipient.account!=account||recipient.character!=character||recipient.generation!=generation||
           closing()||state()!=SessionState::InWorld||!recovered_world_ready()||impl_->common_entry_identity.load()||
           account_id!=account||character_id!=character||impl_->mode!=ProtocolMode::God2CharacterConnection||
           input.actor.recipient()!=recipient||input.actor.source().session==recipient.session||
           logical.size()!=actor_size+replay_size||logical!=input.actor.logical()||!input.actor.retained())
            throw std::invalid_argument("Typed outward requires exact ready recipient and private whole86 actor");
        const auto actor=RecoveredRemoteActor::parse_logical(std::span<const std::uint8_t>(logical).first(actor_size));
        const auto replay=RecoveredTaiwanActorOverride::parse_logical(std::span<const std::uint8_t>(logical).subspan(actor_size));
        if(!actor||!replay||actor->identity()!=input.actor.source().actor_handle||replay->identity()!=actor->identity())
            throw std::invalid_argument("Typed outward whole6F/EA identity mismatch");
        const auto bytes=std::make_shared<std::vector<std::uint8_t>>(RecoveredWorldFrame::encode(logical));
        const auto identity=std::make_shared<ActorStatusPublicationPlanIdentity>();
        const auto seal_data=std::make_shared<TaiwanActorStatusPublication::FrameSeal::Data>(
            identity,self,0,logical.size(),bytes,
            std::vector<TaiwanActorStatusPublication::FrameSeal::Data::Unit>{{0,input.actor}});
        if(!seal_data->retained())throw std::logic_error("Typed outward status retired while framing");
        const auto budget=impl_->budget;
        auto reservation=std::make_shared<Reservation>(budget,bytes->size(),1,false);
        bool charged=false;
        {
            std::lock_guard lock(budget->mutex);
            if(budget->bytes<=max_buffer&&budget->count<max_writes&&bytes->size()<=max_buffer-budget->bytes){
                budget->bytes+=bytes->size();++budget->count;reservation->charged=true;charged=true;
            }
        }
        if(!charged)throw std::length_error("Typed outward reservation exhausted");
        const auto frame=std::make_shared<Impl::OutwardStatusFrame>(identity,common,self,std::move(input),battle,
            bytes,TaiwanActorStatusPublication::FrameSeal(seal_data),reservation);
        const auto marker=std::make_shared<Impl::OutwardStatusWrite>(frame);
        const auto holder=std::make_shared<Impl::ActiveWriteContinuation>(nullptr,bytes);
        attempt=std::make_shared<Impl::OutwardStatusAttempt>(weak_from_this(),frame,impl_->game);
        if(!impl_->outward_status_transport_current(frame))throw std::logic_error("Typed outward source retired before vault adoption");
        // The factory owns real callbacks on game. This call/its failure handler
        // share the submission once box, so queued(false) cannot run twice.
        auto owned=impl_->character_handlers.common_world_ready_publication_owner(*this,frame->recipient,
            {[submission]{return submission->publish();},[submission](bool accepted){submission->complete(accepted);}});
        if(!owned.publish||!owned.queued||submission->finished)
            throw std::logic_error("Ready owner did not retain a complete actual publication");
        attempt->publication=std::move(owned);attempt->armed.store(true);
        // Detach ALL strong affine payload before the first IO post. Only
        // weak-vault facades inside Attempt cross transport executors.
        submission.reset();
        if(!impl_->outward_status_transport_current(frame))throw std::logic_error("Typed outward source retired after vault callback copies");
        impl_->post_status_work(impl_->strand,[self,frame,marker,holder,attempt] {
            auto& s=*self->impl_;
            try {
                if(s.closing||s.c2s0002_state!=Impl::C2S0002State::WorldTailAccepted||
                   !s.outward_status_transport_current(frame)||frame->phase.load()!=Impl::OutwardStatusFrame::Phase::Preparing||
                   s.write_bytes>max_buffer||s.writes.size()>=max_writes||frame->frame->size()>max_buffer-s.write_bytes||
                   !s.terminal_write_allowed())throw std::logic_error("Typed outward queue admission refused");
                Impl::Write value{frame->frame,frame->reservation,false,true};
                value.pending_return_continuation=holder;value.outward_status=marker;
                s.append_write(std::move(value));s.write_bytes+=frame->frame->size();frame->present.store(true);
                auto preparing=Impl::OutwardStatusFrame::Phase::Preparing;
                if(!frame->phase.compare_exchange_strong(preparing,Impl::OutwardStatusFrame::Phase::Held))
                    throw std::logic_error("Typed outward frame installed twice");
                std::size_t index=0;
                if(!s.outward_status_queued(marker,holder,Impl::OutwardStatusFrame::Phase::Held,index))
                    throw std::logic_error("Typed outward actual held marker missing");
                s.post_status_work(s.game,[self,frame,marker,holder,attempt] {
                    bool accepted=false;
                    try {
                        auto held=Impl::OutwardStatusFrame::Phase::Held;
                        accepted=self->impl_->outward_status_held_current(frame,held)&&
                            frame->phase.compare_exchange_strong(held,Impl::OutwardStatusFrame::Phase::Publishing);
                        if(accepted)accepted=self->impl_->outward_status_held_current(frame,Impl::OutwardStatusFrame::Phase::Publishing)&&
                            attempt->publication.publish()&&
                            self->impl_->outward_status_held_current(frame,Impl::OutwardStatusFrame::Phase::Publishing);
                        auto publishing=Impl::OutwardStatusFrame::Phase::Publishing;
                        accepted=accepted&&frame->phase.compare_exchange_strong(publishing,Impl::OutwardStatusFrame::Phase::Published);
                    }catch(...){}
                    try {self->impl_->post_status_work(self->impl_->strand,[self,frame,marker,holder,attempt,accepted] {
                        auto& s=*self->impl_;
                        try {
                            std::size_t index=0;
                            if(!accepted||!s.outward_status_queued(marker,holder,Impl::OutwardStatusFrame::Phase::Published,index))
                                throw std::logic_error("Typed outward publication refused");
                            // Whole single-frame proof immediately before ANY
                            // release; no callback/allocation occurs in this cut.
                            auto published=Impl::OutwardStatusFrame::Phase::Published;
                            if(!frame->phase.compare_exchange_strong(published,Impl::OutwardStatusFrame::Phase::Released))
                                throw std::logic_error("Typed outward repeated release");
                            s.writes[index].held=false;
                            if(!index)s.write(holder->work);
                            if(frame->phase.load()!=Impl::OutwardStatusFrame::Phase::Released&&
                               frame->phase.load()!=Impl::OutwardStatusFrame::Phase::Written)
                                throw std::logic_error("Typed outward retired during write handoff");
                            attempt->complete(true); // Local queue release, never native ACK.
                        }catch(...){frame->revoke();s.fail("Typed outward release failed");attempt->abort();}
                    });}catch(...){frame->revoke();attempt->abort();}
                });
            }catch(...){frame->revoke();s.fail("Typed outward held insertion failed");attempt->abort();}
        });
    }catch(...){
        if(submission)try{submission->complete(false);}catch(...){}
        if(attempt&&attempt->armed.load())attempt->abort();
        else close();
    }
}
void Session::send_native_battle_skill_publication(NativeBattleSkill delivery,
    std::weak_ptr<NativeBattleSkillPublicationOwner> source) {
    impl_->unsupported_callback_output();
    if(delivery)(void)retire_battle_self_view_logical_output(delivery->logical);
    [[maybe_unused]] const auto status_admission=begin_actor_status_writer();
    invalidate_actor_status_writes();
    // Game-owner-only entry. All game-owned fields are checked here or in the
    // posted game hooks, never by the strand. No default/frozen sender changes.
    const auto self=shared_from_this();
    const auto common=impl_->common_world_identity.load();
    // The actual async common-ready path set this owner before publishing the
    // ready common identity. Load that identity first, then reject an unknown
    // or foreign owner BEFORE touching any game-owned account/character data.
    if(!common || impl_->common_ready_thread==std::thread::id{} ||
       impl_->common_ready_thread!=std::this_thread::get_id())
        throw std::logic_error("Native battle publication requires actual async common game owner");
    if(impl_->native_pk_terminal.load() || !delivery || source.expired() || !delivery->sequence || delivery->session!=id() ||
       delivery->account!=account_id || delivery->character!=character_id ||
       !delivery->account || !delivery->character || !delivery->common_generation ||
       closing() || state()!=SessionState::InBattle || battle_generation()!=delivery->battle_generation ||
       !recovered_world_ready() || impl_->mode!=ProtocolMode::God2CharacterConnection ||
       !common || common->account!=delivery->account || common->character!=delivery->character ||
       common->generation!=delivery->common_generation || impl_->common_entry_identity.load())
        throw std::invalid_argument("Native battle publication requires exact ready common battle owner");
    const auto records=RecoveredTaiwanServerRecords::read(delivery->logical);
    if(!records || std::any_of(records->begin(),records->end(),[](const auto& record) {
        return record.opcode!=0x87 && record.opcode!=0x38 &&
            !(record.opcode==0x86 && record.bytes.size()==17 && record.bytes[1]==5);
    }))throw std::invalid_argument("Native battle publication requires complete87/38/86-5 records");
    const auto charge=delivery->logical.size()+3;
    auto budget=impl_->budget;std::shared_ptr<Reservation> reservation;
    {
        std::lock_guard lock(budget->mutex);
        if(charge<=max_buffer-budget->bytes && budget->count<max_writes) {
            reservation=std::make_shared<Reservation>(budget,charge);
            budget->bytes+=charge;++budget->count;
        }
    }
    if(!reservation)throw std::length_error("Native battle publication queue reservation failed");
    auto pending=std::make_shared<Impl::NativeBattlePending>();
    pending->delivery=std::move(delivery);pending->common=common;pending->source=std::move(source);
    std::shared_ptr<Impl::NativeBattlePending> absent;
    impl_->retire_normal_output(); // Before actual publication/PK hold is installed.
    if(!impl_->native_battle_pending.compare_exchange_strong(absent,pending))
        throw std::logic_error("Native battle publication already pending");
    try {
        impl_->post_status_work(impl_->strand,[self,pending,reservation=std::move(reservation)]() mutable {
            auto& s=*self->impl_;
                [[maybe_unused]] const auto status_admission=self->begin_actor_status_writer();
            if(s.native_battle_pending.load()!=pending || pending->completing.load())return;
            if(s.closing || !s.native_battle_current(pending) ||
               s.c2s0002_state!=Impl::C2S0002State::WorldTailAccepted) {
                s.fail("Stale native battle publication");return;
            }
            // A continuation prefix has no native grant/list nonce. Never
            // combine its old83 records with03 received after new list/control
            // bytes, even when battle_generation has not changed.
            // Also refuse any already-buffered partial envelope: its command
            // cannot yet be identified. This rejects partial ticks too. Bytes
            // not yet received have no native grant nonce; that remains open.
            if(!s.world_input.empty() || !s.world_pending_records.empty() ||
               s.skill_deadline || s.native_skill_generation) {
                s.fail("Native battle publication intersects an incomplete command prefix");return;
            }
            try {
                auto bytes=std::make_shared<std::vector<std::uint8_t>>(RecoveredWorldFrame::encode(pending->delivery->logical));
                if(bytes->size()>max_buffer-s.write_bytes || s.writes.size()>=max_writes) {
                    s.fail("Native battle publication queue limit");return;
                }
                if(!s.terminal_write_allowed())return;
                s.append_write({bytes,std::move(reservation),false,true,{},{},pending});
                s.write_bytes+=bytes->size();
                s.release_native_battle(pending,bytes);
            }catch(...) {s.fail("Native battle publication encoding or handoff failed");}
        });
    }catch(...) {
        auto expected=pending;impl_->native_battle_pending.compare_exchange_strong(expected,{});
        throw; // No network operation accepted; caller retires its staged source.
    }
}
Session::NativeBattleSkill Session::native_battle_skill_written() const noexcept {
    return native_battle_skill_written_.load();
}
bool Session::native_battle_skill_publication_pending() const noexcept {
    return bool(impl_->native_battle_pending.load());
}
bool Session::same_native_pk_game_executor(const Session& other)const noexcept {
    const auto a=impl_->common_world_identity.load(),b=other.impl_->common_world_identity.load();
    return a && b && impl_->common_ready_thread!=std::thread::id{} &&
        impl_->common_ready_thread==std::this_thread::get_id() &&
        other.impl_->common_ready_thread==std::this_thread::get_id() && impl_->game==other.impl_->game;
}
Session::NativePkEntryHold Session::prepare_native_pk_entry(NativePkEntryRequest request,
        std::weak_ptr<NativePkEntryOwner> source) {
    impl_->unsupported_callback_output();
    (void)retire_battle_self_view_logical_output(request.logical);
    const auto common=impl_->common_world_identity.load();
    const auto data=impl_->normal_initialization.load();
    if(!common || !data || impl_->common_ready_thread!=std::this_thread::get_id() ||
       impl_->common_ready_thread==std::thread::id{})
        throw std::logic_error("Native PK entry requires the actual async common game owner");
    if(const auto pending=impl_->native_pk_return_finalisation_history.load()){
        if(!pending->returned_notified.load())
            throw std::logic_error("Native PK entry cannot replace an unfinished original return deadline");
        auto completed=pending;impl_->native_pk_return_finalisation_history.compare_exchange_strong(completed,{});
    }
    const NormalWorldInitialization initialization(data);
    if(!normal_world_initialization_current_on_game(initialization) || !initialization.entry_written())
        throw std::invalid_argument("Native PK entry lacks actual Written private initialization");
    // CUSTOM-0116 capture the actual qualified phase; no request scalar or
    // synthetic InWorld transition can select or later widen this hold.
    const auto prebattle_phase=state();
    if(source.expired() || closing() ||
       (prebattle_phase!=SessionState::CharacterSelected && prebattle_phase!=SessionState::InWorld) ||
       impl_->mode!=ProtocolMode::God2CharacterConnection || !recovered_world_ready() ||
       !request.account || !request.character || !request.common_generation || !request.world_generation ||
       request.account!=account_id || request.character!=character_id ||
       request.prebattle_generation!=battle_generation() ||
       request.prebattle_generation==std::numeric_limits<std::uint64_t>::max() ||
       common->account!=request.account || common->character!=request.character ||
       common->generation!=request.common_generation || impl_->common_entry_identity.load() ||
       impl_->native_battle_pending.load() ||
       initialization.entry_frame()!=request.normal_entry_frame ||
       initialization.entry_logical()!=request.normal_entry_logical ||
       initialization.accepted_tail()!=request.accepted_tail || initialization.config_flag()!=request.config_flag)
        throw std::invalid_argument("Native PK entry lacks exact current private world initialization");
    // Exact existing waiting two-player projection grammar only. No future
    // 86/5 grant is released before the room's initial notifications. Framing
    // validation is not ticket/actor/stat/context/source authority.
    const auto records=RecoveredTaiwanServerRecords::read(request.logical);
    if(!records || records->size()!=9)
        throw std::invalid_argument("Native PK entry needs complete waiting two-player records");
    constexpr std::array<std::uint8_t,9> opcodes{0x82,0x86,0x86,0x1c,0x86,0x86,0x1c,0x86,0x88};
    for(std::size_t i=0;i<opcodes.size();++i)if((*records)[i].opcode!=opcodes[i])
        throw std::invalid_argument("Native PK entry record order mismatch");
    for(const auto index:{1u,2u}) {
        const auto record=RecoveredBattlePlayerAppearance::parse((*records)[index].bytes);
        if(!record || record->position()!=(index==1?0:14))
            throw std::invalid_argument("Native PK entry needs both ordinary relative appearances");
    }
    const auto own=RecoveredBattleIdentity::parse_logical((*records)[3].bytes);
    const auto other=RecoveredBattleIdentity::parse_logical((*records)[6].bytes);
    // CUSTOM-0086 preserve historical SelectedCharacter equality. Only the
    // actual original qualified INIT may use its independently prepared actor.
    // This is not a caller actor scalar or a mask of incoming S1C identity.
    std::uint64_t own_actor=request.character;
    if(data->entry->qualified_scene_identity){
        if(!initialization.world_identity_sender_current())
            throw std::invalid_argument("Native PK entry original world identity sender was revoked");
        const auto entry=RecoveredWorldEntryView::read(data->entry->frame);
        if(!entry||!qualified_taiwan_scene_handle(entry->actor_handle)||
           !std::equal(entry->logical.begin(),entry->logical.end(),
               data->entry->logical.begin(),data->entry->logical.end()))
            throw std::invalid_argument("Native PK entry lacks its actual qualified normal actor");
        own_actor=entry->actor_handle;
    }
    if(!own || !other || own->position()!=0 || other->position()!=14 ||
       !own->displayed_level() || !other->displayed_level() ||
       (own->variant()&0x6000)!=0x2000 || (other->variant()&0x6000)!=0x2000 ||
       own->identity_word()!=own_actor || !other->identity_word() ||
       own->identity_word()==other->identity_word())
        throw std::invalid_argument("Native PK entry player identities mismatch");
    for(const auto index:{4u,5u,7u}) {
        const auto record=RecoveredBattleVitals::parse_logical((*records)[index].bytes);
        if(!record || record->position()!=(index==7?14:0) ||
           record->resource()!=(index==5?RecoveredBattleVitals::Resource::Mp:RecoveredBattleVitals::Resource::Hp) ||
           record->current()>record->maximum())
            throw std::invalid_argument("Native PK entry complete vitals mismatch");
    }
    auto frame=std::make_shared<std::vector<std::uint8_t>>(RecoveredWorldFrame::encode(request.logical));
    auto identity=std::make_shared<const WorldDeliveryIdentity>(WorldDeliveryIdentity{
        request.account,request.character,request.world_generation,request.prebattle_generation+1});
    auto original_world=impl_->world_delivery_identity.load();
    // Do not narrow historical entry transport. Missing/stale actual WORLD
    // identity disables only new retained-return preparation, never fabricates it.
    if(original_world && (!original_world->world_generation || original_world->account!=request.account ||
       original_world->character!=request.character || original_world->battle_generation!=request.prebattle_generation))
        original_world.reset();
    auto pending=std::make_shared<NativePkEntryHold::Data>(shared_from_this(),id(),impl_->game,
        std::move(request),prebattle_phase,initialization,common,std::move(identity),std::move(original_world),frame,std::move(source));
    auto budget=impl_->budget;std::shared_ptr<Reservation> reservation;
    {
        std::lock_guard lock(budget->mutex);
        if(frame->size()<=max_buffer-budget->bytes && budget->count<max_writes) {
            reservation=std::make_shared<Reservation>(budget,frame->size());
            budget->bytes+=frame->size();++budget->count;
        }
    }
    if(!reservation)throw std::length_error("Native PK entry queue reservation failed");
    std::shared_ptr<NativePkEntryHold::Data> absent;
    impl_->retire_normal_output(); // Before actual publication/PK hold is installed.
    if(!impl_->native_pk_pending.compare_exchange_strong(absent,pending))
        throw std::logic_error("Native PK entry already pending");
    try {impl_->post_status_work(impl_->strand,[self=shared_from_this(),pending,reservation=std::move(reservation)]()mutable {
        auto& s=*self->impl_;
                [[maybe_unused]] const auto status_admission=self->begin_actor_status_writer();
        if(s.native_pk_pending.load()!=pending || pending->completing.load())return;
        try {
            s.native_pk_read_paused=true;s.native_pk_reservation=std::move(reservation);
            s.native_pk_timer.expires_after(close_timeout);
            s.native_pk_timer.async_wait([self,pending](const asio::error_code& ec) {
                auto& s=*self->impl_;
                [[maybe_unused]] const auto status_admission=self->begin_actor_status_writer();
                if(ec || s.native_pk_pending.load()!=pending)return;
                // A game->strand completion post can itself fail allocation.
                // Game completion may be queued, or its final strand post may
                // have failed. Timeout cannot wait forever for either case.
                if(pending->completing.load()) {
                    auto expected=pending;s.native_pk_pending.compare_exchange_strong(expected,{});
                }
                s.fail("Native PK entry hold/write deadline expired");
            });
            s.stage_native_pk();
        }catch(...) {s.fail("Native PK preparation timer or strand handoff failed");}
    });}catch(...) {
        auto expected=pending;impl_->native_pk_pending.compare_exchange_strong(expected,{});throw;
    }
    return NativePkEntryHold(std::move(pending)); // PREPARING cancellation token, not a Held result.
}
bool Session::native_pk_game_executor_matches(const asio::any_io_executor& executor)const noexcept {
    return impl_->common_world_identity.load() &&
        impl_->common_ready_thread==std::this_thread::get_id() && impl_->game==executor;
}
bool Session::native_pk_entry_current(const NativePkEntryHold& hold)const noexcept {
    const auto data=hold.data_;
    if(!data || data->thread!=std::this_thread::get_id() || data->game!=impl_->game ||
       data->session.lock().get()!=this || data->completing.load() ||
       data->phase.load()!=NativePkEntryHold::Data::Phase::Held)return false;
    return impl_->native_pk_transport_current(data,false) &&
        normal_world_initialization_current_on_game(data->initialization) &&
        account_id==data->request.account && character_id==data->request.character;
}
bool Session::native_pk_entry_committed_current(const NativePkEntryHold& hold)const noexcept {
    const auto data=hold.data_;
    if(!data || data->thread!=std::this_thread::get_id() || data->game!=impl_->game ||
       data->session.lock().get()!=this || data->completing.load() ||
       data->phase.load()!=NativePkEntryHold::Data::Phase::Committed)return false;
    return impl_->native_pk_transport_current(data,true) &&
        impl_->world_delivery_identity.load()==data->battle_identity &&
        account_id==data->request.account && character_id==data->request.character;
}
bool Session::native_pk_entry_binding_current(const NativePkEntryHold& hold)const noexcept {
    const auto data=hold.data_;
    if(!data || data->thread!=std::this_thread::get_id() || data->game!=impl_->game ||
       data->session.lock().get()!=this || data->session_id!=id() || !data->battle_identity ||
       account_id!=data->request.account ||
       character_id!=data->request.character)return false;
    const auto phase=data->phase.load();
    if(phase!=NativePkEntryHold::Data::Phase::Committed &&
       phase!=NativePkEntryHold::Data::Phase::Released &&
       phase!=NativePkEntryHold::Data::Phase::Written)return false;
    // Before completion clears the pending token, prove the exact common/
    // initialization/phase/generation identities already committed by entry.
    // After clear only the existing accepted Written predicate qualifies it.
    return (impl_->native_pk_transport_current(data,true) &&
            impl_->world_delivery_identity.load()==data->battle_identity) ||
           impl_->native_pk_written_transport_current(data);
}
bool Session::native_pk_entry_written_current(const NativePkEntryHold& hold)const noexcept {
    const auto data=hold.data_;
    // Private immutable owner/executor check BEFORE game-owned IDs.
    if(!data || data->thread!=std::this_thread::get_id() || data->game!=impl_->game ||
       data->session.lock().get()!=this)return false;
    return impl_->native_pk_written_transport_current(data) &&
        account_id==data->request.account && character_id==data->request.character;
}
Session::NativePkTerminalBarrier Session::prepare_native_pk_terminal_barrier(
        const NativePkEntryHold& hold,NativeBattleSkill final,std::weak_ptr<NativePkTerminalOwner> source,
        const RecoveredWorldRecords::ContextNotification& original_context) {
    // CUSTOM-0131 Publication owns Finished/context semantics. This TLS proves
    // the actual synchronous Session world callback, not arbitrary caller IDs.
    if(observed_world_callback!=this || !native_pk_entry_written_current(hold) || !final ||
       native_battle_skill_written()!=final || source.expired() ||
       impl_->native_battle_pending.load() || impl_->native_pk_pending.load())
        throw std::logic_error("Native PK terminal barrier requires actual accepted input and final write");
    const auto& request=hold.request();
    if(final->session!=id() || final->account!=request.account || final->character!=request.character ||
       final->common_generation!=request.common_generation || final->battle_generation!=hold.committed_battle_generation())
        throw std::logic_error("Native PK terminal final delivery differs from private entry identity");
    // Exact original parsed input address, not a copied/scalar C1C argument.
    const auto actual=std::find_if(observed_world_records.begin(),observed_world_records.end(),[&](const auto& record){
        return std::get_if<RecoveredWorldRecords::ContextNotification>(&record)==&original_context;
    });
    if(actual==observed_world_records.end()||!observed_response_poison||*observed_response_poison)
        throw std::logic_error("PK terminal selector lacks original C1C occurrence");
    const auto selector=impl_->make_receiver_selector(hold.data_->initialization.data_->entry,original_context.payload);
    if(!selector)throw std::logic_error("PK terminal selector differs from exact native identity/0or1 report");
    auto data=std::make_shared<NativePkTerminalBarrier::Data>(shared_from_this(),impl_->game,
        hold,std::move(final),std::move(source),selector);
    std::shared_ptr<NativePkTerminalBarrier::Data> absent;
    if(!impl_->native_pk_terminal.compare_exchange_strong(absent,data))
        throw std::logic_error("Native PK terminal barrier already pending");
    impl_->native_pk_terminal_callback_capture=data;
    try {impl_->post_status_work(impl_->strand,[self=shared_from_this(),data] {
        auto& s=*self->impl_;
                [[maybe_unused]] const auto status_admission=self->begin_actor_status_writer();if(s.native_pk_terminal.load()!=data)return;
        try {
            s.native_pk_terminal_timer.expires_after(close_timeout);
            s.native_pk_terminal_timer.async_wait([self,data](const asio::error_code& ec) {
                if(!ec){
                    std::shared_ptr<NativePkReturnFinalisation::Data> final;
                    {std::lock_guard lock(data->finalisation_mutex);final=data->finalisation.lock();}
                    const auto index=final&&final->sessions[0].lock()==self?0u:1u;
                    if(final&&final->preparations[index].data_->terminal.data_==data&&
                       final->phase.load()==NativePkReturnFinalisationStatus::Returned&&!final->returned_notified.load()){
                        Session::fail_native_pk_return_finalisation(final);return; // SAME original 5s deadline, not renewed.
                    }
                    if(self->impl_->native_pk_terminal.load()==data){
                        if(data->ack_handoff_failed.load())self->impl_->game_busy=false;
                        self->impl_->fail("Native PK terminal barrier deadline expired; retained recovery required");
                    }
                }
            });
            data->armed.store(true);s.stage_native_pk_terminal();
        }catch(...) {s.fail("Native PK terminal barrier timer/staging failed");}
    });}catch(...) {
        data->phase.store(NativePkTerminalBarrier::Data::Phase::Failed);
        auto expected=data;impl_->native_pk_terminal.compare_exchange_strong(expected,{});
        if(!data->failed_notified.exchange(true))if(const auto actual=data->source.lock())try {
            actual->native_pk_terminal_failed(*this,NativePkTerminalBarrier(data));
        }catch(...) {}
        try {close();}catch(...) {impl_->close_requested.store(true);}
        throw;
    }
    return NativePkTerminalBarrier(std::move(data));
}
bool Session::native_pk_terminal_barrier_ready_current(const NativePkTerminalBarrier& barrier)const noexcept {
    const auto data=barrier.data_;
    if(!data || data->thread!=std::this_thread::get_id() || data->game!=impl_->game ||
       data->session.lock().get()!=this || data->phase.load()!=NativePkTerminalBarrier::Data::Phase::Ready)
        return false;
    return impl_->native_pk_terminal_transport_current(data) && native_pk_entry_written_current(data->entry);
}
bool Session::native_pk_terminal_barrier_accepted_current(const NativePkTerminalBarrier& barrier)const noexcept {
    return barrier.data_ && barrier.data_->accepted.load() && native_pk_terminal_barrier_ready_current(barrier);
}
Session::NativePkReturnPreparation Session::prepare_native_pk_return_generation(const NativePkTerminalBarrier& barrier) {
    if(!native_pk_terminal_barrier_accepted_current(barrier))
        throw std::logic_error("PK return preparation requires actual accepted terminal barrier");
    const auto entry=barrier.data_->entry.data_;
    const auto original=entry->original_world_identity;
    const auto& request=entry->request;
    if(!original || request.prebattle_generation>std::numeric_limits<std::uint64_t>::max()-2 ||
       original->account!=request.account || original->character!=request.character ||
       !original->world_generation || original->battle_generation!=request.prebattle_generation ||
       entry->initialization.data_->effective_battle!=request.prebattle_generation)
        throw std::logic_error("PK return lacks its original WORLD namespace or checked next generation");
    const auto future=request.prebattle_generation+2;
    const auto selector=barrier.data_->receiver_selector;
    if(!selector||impl_->receiver_selector!=selector)
        throw std::logic_error("PK return lacks latest accepted original C1C selector");
    auto normal=std::make_shared<const NormalWorldInitialization::Data>(entry->initialization.data_,future,selector);
    auto identity=std::make_shared<const WorldDeliveryIdentity>(WorldDeliveryIdentity{
        original->account,original->character,original->world_generation,future});
    NativePkReturnPreparation result(std::make_shared<const NativePkReturnPreparation::Data>(
        barrier,NormalWorldInitialization(std::move(normal)),std::move(identity)));
    if(!native_pk_return_preparation_current(result))
        throw std::logic_error("PK return preparation lost exact retained source during allocation");
    return result; // No store into live normal/world identity or state.
}
bool Session::native_pk_return_preparation_current(const NativePkReturnPreparation& preparation)const noexcept {
    const auto data=preparation.data_;
    if(!data || !native_pk_terminal_barrier_accepted_current(data->terminal))return false;
    const auto entry=data->terminal.data_->entry.data_;
    const auto original=entry->original_world_identity;
    const auto prior=entry->initialization.data_;
    const auto future=data->initialization.data_;
    const auto& request=entry->request;
    return original && future && data->world_identity &&
        request.prebattle_generation<=std::numeric_limits<std::uint64_t>::max()-2 &&
        original->account==request.account && original->character==request.character &&
        original->world_generation && original->battle_generation==request.prebattle_generation &&
        prior->effective_battle==request.prebattle_generation && future->previous.lock()==prior &&
        future->entry==prior->entry && future->tail==prior->tail && future->config==prior->config &&
        future->receiver_selector && future->receiver_selector==data->terminal.data_->receiver_selector &&
        impl_->receiver_selector==future->receiver_selector &&
        future->effective_battle==request.prebattle_generation+2 &&
        data->world_identity->account==original->account && data->world_identity->character==original->character &&
        data->world_identity->world_generation==original->world_generation &&
        data->world_identity->battle_generation==future->effective_battle;
}
std::optional<Session::NativeTaiwanReceiverSelector> Session::native_taiwan_receiver_selector_on_game()const {
    const auto init=impl_->normal_initialization.load();
    if(!init||!normal_world_initialization_current_on_game(NormalWorldInitialization(init))||!init->entry->written.load())return {};
    const auto source=impl_->receiver_selector;
    if(!source||source->entry!=init->entry)return {};
    const NativeTaiwanReceiverSelector result(source);
    return native_taiwan_receiver_selector_current(result)?std::optional{result}:std::nullopt;
}
std::optional<Session::NativeTaiwanReceiverSelector> Session::native_taiwan_return_receiver_selector(
        const NativePkReturnPreparation& prepared)const {
    if(!native_pk_return_preparation_current(prepared))return {};
    const auto source=prepared.data_->initialization.data_->receiver_selector;
    if(!source||impl_->receiver_selector!=source)return {};
    const NativeTaiwanReceiverSelector result(source);
    return native_taiwan_receiver_selector_current(result)?std::optional{result}:std::nullopt;
}
bool Session::native_taiwan_receiver_selector_current(const NativeTaiwanReceiverSelector& selector)const noexcept {
    const auto source=selector.data_;
    if(!source||!source->entry||source->entry->game_thread!=std::this_thread::get_id()||
       source->entry->session.lock().get()!=this)return false;
    const auto entry=source->entry;
    if(impl_->receiver_selector!=source||entry->retired.load()||!entry->written.load()||closing()||
       !recovered_world_ready()||impl_->mode!=ProtocolMode::God2CharacterConnection||
       account_id!=entry->account||character_id!=entry->character)return false;
    const auto normal=impl_->normal_initialization.load();
    if(normal&&normal->entry==entry&&normal_world_initialization_current_on_game(NormalWorldInitialization(normal)))return true;
    const auto terminal=impl_->native_pk_terminal.load();
    return terminal&&terminal->receiver_selector==source&&
        native_pk_terminal_barrier_accepted_current(NativePkTerminalBarrier(terminal));
}
bool Session::native_taiwan_initial_game_executor_matches(const NativeTaiwanReceiverSelector& selector,
        const asio::any_io_executor& executor) const noexcept {
    if(!native_taiwan_receiver_selector_current(selector))return false;
    const auto source=selector.data_;const auto entry=source->entry;
    const auto normal=impl_->normal_initialization.load();
    if(!normal||normal->entry!=entry||entry->game_thread!=std::this_thread::get_id()||
       entry->session.lock().get()!=this||!entry->written.load()||entry->retired.load()||
       impl_->game!=executor||!normal_world_initialization_current_on_game(NormalWorldInitialization(normal)))return false;
    // Retain the original private observations through executor equality and
    // repeat Current; a terminal-only PK selector cannot supply this NormalINIT.
    return native_taiwan_receiver_selector_current(selector)&&impl_->receiver_selector==source&&
        impl_->normal_entry.load()==entry&&impl_->normal_initialization.load()==normal&&
        entry->game_thread==std::this_thread::get_id()&&entry->session.lock().get()==this&&
        entry->written.load()&&!entry->retired.load()&&
        normal_world_initialization_current_on_game(NormalWorldInitialization(normal));
}
void Session::fail_native_pk_return_reservation(
        const std::shared_ptr<NativePkReturnReservation::Data>& data) noexcept {
    if(!data||data->phase.load()==NativePkReturnReservation::Data::Phase::Returned)return;
    // Actual output transition serializes pair failure against successful detach.
    for(const auto& weak:data->sessions)if(const auto session=weak.lock())
        if(const auto output=session->impl_->native_pk_return_output.load();output&&
           output->plan->reservation.data_==data&&output->phase.load()!=NativePkReturnOutputHold::Data::Phase::Failed){
            fail_native_pk_return_output(output);return;
        }
    if(data->phase.load()==NativePkReturnReservation::Data::Phase::Returned)return;
    const bool first=data->phase.exchange(NativePkReturnReservation::Data::Phase::Failed)!=
        NativePkReturnReservation::Data::Phase::Failed;
    for(const auto& weak:data->sessions)if(const auto session=weak.lock())
        if(const auto output=session->impl_->native_pk_return_output.load())
            if(output->plan->reservation.data_==data)fail_native_pk_return_output(output);
    // Always remove exact slots: a concurrent installation may finish AFTER
    // the first failure swept them. Only the first transition closes/notifies.
    for(std::size_t index=0;index<2;++index)if(const auto session=data->sessions[index].lock()) {
        const auto terminal=data->preparations[index].data_->terminal.data_;
        if(session->impl_->native_pk_terminal.load()==terminal) {
            terminal->accepted.store(false);
            terminal->phase.store(NativePkTerminalBarrier::Data::Phase::Failed);
        }
        auto expected=data;session->impl_->native_pk_return.compare_exchange_strong(expected,{});
    }
    if(!first)return;
    // The ENTIRE pair is poisoned before callbacks/close posts; no peer IDs read.
    for(const auto& weak:data->sessions)if(const auto session=weak.lock())
        try {session->close();}catch(...) {session->impl_->close_requested.store(true);}
    try {Session::schedule_actor_status_work<false>(data->game,
        {data->sessions[0].lock(),data->sessions[1].lock()},[data] {
        if(data->failed_notified.exchange(true))return;
        if(data->thread!=std::this_thread::get_id())return;
        if(const auto source=data->source.lock())try {
            source->native_pk_return_failed(NativePkReturnReservation(data));
        }catch(...) {} // Both exact peers are already poisoned/closing.
    });}catch(...) {} // Failed remains durable-in-process; no fake callback or rollback.
}
Session::NativePkReturnReservation Session::reserve_native_pk_return_pair(
        std::array<std::shared_ptr<Session>,2> sessions,std::array<NativePkReturnPreparation,2> preparations,
        std::weak_ptr<NativePkReturnOwner> source) {
    if(!sessions[0] || !sessions[1] || sessions[0]==sessions[1])
        throw std::invalid_argument("PK return reservation requires two distinct actual Sessions");
    // Qualify the actual recorded game thread BEFORE any game-owned fields.
    for(std::size_t i=0;i<2;++i) {
        const auto data=preparations[i].data_;
        if(!data || !data->terminal.data_ || data->terminal.data_->thread!=std::this_thread::get_id() ||
           data->terminal.data_->session.lock()!=sessions[i] || data->terminal.data_->game!=sessions[i]->impl_->game)
            throw std::logic_error("PK return pair game owner or private preparation mismatch");
    }
    std::shared_ptr<NativePkReturnReservation::Data> data;
    try {
        if(source.expired() || sessions[0]->impl_->game!=sessions[1]->impl_->game)
            throw std::logic_error("PK return pair requires one actual game executor and live owner");
        for(std::size_t i=0;i<2;++i) {
            if(const auto existing=sessions[i]->impl_->native_pk_return.load()) {
                fail_native_pk_return_reservation(existing);
                throw std::logic_error("PK return pair already reserved");
            }
            if(!sessions[i]->native_pk_return_preparation_current(preparations[i]))
                throw std::logic_error("PK return pair lost original accepted terminal preparation");
        }
        // Two immutable slots and the independent attempt are allocated before
        // installation. No observer, state publication or output lies between.
        data=std::make_shared<NativePkReturnReservation::Data>(sessions,std::move(preparations),
            sessions[0]->impl_->game,std::move(source));
        auto attempt=std::make_shared<Impl::NativePkReturnAttempt>(data);
        for(std::size_t i=0;i<2;++i) {
            if(!sessions[i]->native_pk_return_preparation_current(data->preparations[i]))
                throw std::logic_error("PK return pair source changed before slot installation");
        }
        for(std::size_t i=0;i<2;++i) {
            std::shared_ptr<NativePkReturnReservation::Data> absent;
            if(!sessions[i]->impl_->native_pk_return.compare_exchange_strong(absent,data))
                throw std::logic_error("PK return pair slot installation rejected");
        }
        data->installed.store(true);
        if(data->phase.load()!=NativePkReturnReservation::Data::Phase::Pending ||
           sessions[0]->impl_->native_pk_return.load()!=data || sessions[1]->impl_->native_pk_return.load()!=data ||
           !sessions[0]->native_pk_return_preparation_current(data->preparations[0]) ||
           !sessions[1]->native_pk_return_preparation_current(data->preparations[1]))
            throw std::logic_error("PK return pair retired during slot installation");
        for(std::size_t i=0;i<2;++i)
            sessions[i]->impl_->post_status_work(sessions[i]->impl_->strand,[self=sessions[i],data,attempt,i] {
                self->impl_->stage_native_pk_return(data,i,attempt);
            });
        return NativePkReturnReservation(data);
    }catch(...) {
        if(data)fail_native_pk_return_reservation(data);
        else for(const auto& session:sessions)try {session->close();}catch(...) {session->impl_->close_requested.store(true);}
        throw;
    }
}
bool Session::native_pk_return_reservation_current(const NativePkReturnReservation& reservation) noexcept {
    const auto data=reservation.data_;
    if(!data || data->thread!=std::this_thread::get_id() || !data->installed.load() ||
       data->phase.load()!=NativePkReturnReservation::Data::Phase::Reserved || data->cuts.load()!=3u ||
       data->source.expired())return false;
    const auto first=data->sessions[0].lock(),second=data->sessions[1].lock();
    if(!first || !second || first==second || first->impl_->game!=data->game || second->impl_->game!=data->game)return false;
    return first->impl_->native_pk_return.load()==data && second->impl_->native_pk_return.load()==data &&
        first->native_pk_return_preparation_current(data->preparations[0]) &&
        second->native_pk_return_preparation_current(data->preparations[1]) &&
        data->phase.load()==NativePkReturnReservation::Data::Phase::Reserved;
}
bool Session::native_pk_return_reservation_matches(const NativePkReturnReservation& reservation,
        const std::array<std::shared_ptr<Session>,2>& sessions,
        const std::array<NativePkReturnPreparation,2>& preparations) noexcept {
    // Prove the owning game thread before examining private prepared state.
    // Equal actor/account keys or two independent Current results cannot join
    // one scene plan to an unrelated genuine Reserved pair.
    if(!native_pk_return_reservation_current(reservation))return false;
    const auto data=reservation.data_;
    if(data->sessions[0].lock()!=sessions[0] || data->sessions[1].lock()!=sessions[1] ||
       data->preparations!=preparations)return false;
    return native_pk_return_reservation_current(reservation);
}
Session::NativePkReturnOutputPlan Session::prepare_native_pk_return_output(
        const NativePkReturnReservation& reservation,const std::array<std::shared_ptr<Session>,2>& sessions,
        const std::array<NativePkReturnPreparation,2>& preparations,std::weak_ptr<const void> identity,
        std::vector<NativePkReturnOutputGroup> groups){
    if(!native_pk_return_reservation_matches(reservation,sessions,preparations)||identity.expired()||
       groups.size()<2||groups[0].recipient!=sessions[0]||groups[1].recipient!=sessions[1])
        throw std::invalid_argument("Return output requires exact private paired Records source");
    const auto status_identity=std::make_shared<ActorStatusPublicationPlanIdentity>();
    std::vector<NativePkReturnOutputPlan::Data::Group> owned;owned.reserve(groups.size());
    constexpr auto record_size=RecoveredRemoteActor::logical_size;
    constexpr auto override_size=RecoveredTaiwanActorOverride::logical_size;
    static_assert(record_size+override_size<=RecoveredWorldFrame::max_logical_size);
    for(std::size_t index=0;index<groups.size();++index){
        auto& supplied=groups[index];const auto session=supplied.recipient;
        if(!session||!session->same_native_pk_game_executor(*sessions[0])||
           (supplied.actors.empty()&&index>=2))
            throw std::invalid_argument("Return output recipient or record boundaries");
        for(const auto& prior:owned)if(prior.recipient==session)throw std::invalid_argument("Duplicate return output recipient");
        std::optional<NormalWorldOutputHandle> normal;
        if(index>=2){
            // Exact private recorded game owner BEFORE reading public owner IDs.
            const auto init=session->impl_->normal_initialization.load();
            if(!init||!init->entry||init->entry->game_thread!=std::this_thread::get_id()||
               init->entry->session.lock()!=session||!init->entry->written.load())
                throw std::invalid_argument("Return survivor lacks private Written INIT");
            normal=session->capture_normal_world_output_on_game(NormalWorldInitialization(init));
            if(!normal)throw std::invalid_argument("Return survivor private output epoch");
        }
        if(!supplied.actor_status.empty()&&supplied.actor_status.size()!=supplied.actors.size())
            throw std::invalid_argument("Return owned-status actor witnesses must be parallel");
        NativePkReturnOutputPlan::Data::Group recipient{session,std::move(normal),{}};
        // CUSTOM-0133 known native records, deterministic replay composition.
        // Each supplied actor stays whole across outer0xA00 frame boundaries.
        // All allocations/encoding precede source observers and IO installation.
        std::vector<std::uint8_t> frame;frame.reserve(RecoveredWorldFrame::max_logical_size);
        std::vector<TaiwanActorStatusPublication::FrameSeal::Data::Unit> status_units;
        const auto flush=[&]{
            if(frame.empty())return;
            auto bytes=std::make_shared<std::vector<std::uint8_t>>(RecoveredWorldFrame::encode(frame));
            std::optional<TaiwanActorStatusPublication::FrameSeal> seal;
            if(!status_units.empty()){
                const auto data=std::make_shared<TaiwanActorStatusPublication::FrameSeal::Data>(status_identity,session,
                    recipient.frames.size(),frame.size(),bytes,std::move(status_units));
                seal=TaiwanActorStatusPublication::FrameSeal(data);
                if(data->plan!=status_identity||!data->retained())
                    throw std::invalid_argument("Return framed owned-status source retired");
            }
            recipient.frames.push_back(std::move(bytes));recipient.frame_seals.push_back(std::move(seal));
            frame.clear();status_units.clear();
        };
        for(std::size_t actor_index=0;actor_index<supplied.actors.size();++actor_index){
            const auto& actor=supplied.actors[actor_index];
            if(actor.size()!=record_size&&actor.size()!=record_size+override_size)
                throw std::invalid_argument("Return output whole6F/EA boundaries");
            const auto logical=std::span<const std::uint8_t>(actor);
            const auto spawn=RecoveredRemoteActor::parse_logical(logical.first(record_size));
            if(!spawn)throw std::invalid_argument("Return output full6F source only");
            if(actor.size()!=record_size){
                const auto replay=RecoveredTaiwanActorOverride::parse_logical(logical.subspan(record_size));
                if(!replay||replay->identity()!=spawn->identity())
                    throw std::invalid_argument("Return output EA full identity mismatch");
            }
            const auto* status=supplied.actor_status.empty()?nullptr:&supplied.actor_status[actor_index];
            if(status&&*status&&((*status)->recipient().session!=session->id()||
               (*status)->source().actor_handle!=spawn->identity()||(*status)->logical()!=actor||!(*status)->retained()))
                throw std::invalid_argument("Return actor bytes differ from exact owned-status publication");
            if(frame.size()>RecoveredWorldFrame::max_logical_size-actor.size())flush();
            if(status&&*status)status_units.push_back({frame.size(),**status});
            frame.insert(frame.end(),actor.begin(),actor.end());
        }
        flush();
        owned.push_back(std::move(recipient));
    }
    const auto data=std::make_shared<NativePkReturnOutputPlan::Data>(reservation,sessions,preparations,
        std::move(identity),sessions[0]->impl_->game,std::move(owned),status_identity);
    if(!native_pk_return_output_plan_current(data))throw std::invalid_argument("Return output source changed during preparation");
    return NativePkReturnOutputPlan(data);
}
bool Session::native_pk_return_output_plan_current(const std::shared_ptr<NativePkReturnOutputPlan::Data>& data) noexcept{
    try{
    if(!data||data->thread!=std::this_thread::get_id()||data->records.expired()||
       !native_pk_return_reservation_matches(data->reservation,data->sessions,data->preparations))return false;
    if(!data->status_identity->active.load())return false;
    for(std::size_t index=0;index<data->groups.size();++index){
        const auto& group=data->groups[index];
        if(index>=2&&(!group.normal||!group.recipient->normal_world_output_current_on_game(*group.normal)))return false;
        if(group.frame_seals.size()!=group.frames.size())return false;
        for(std::size_t ordinal=0;ordinal<group.frames.size();++ordinal)
            if(!actor_status_frame_matches(group.frame_seals[ordinal],group.frames[ordinal],*group.recipient,ordinal,*data))return false;
    }
    return native_pk_return_reservation_matches(data->reservation,data->sessions,data->preparations)&&!data->records.expired();
    }catch(...){return false;}
}
bool Session::native_pk_return_output_plan_matches(const NativePkReturnOutputPlan& plan,
        const NativePkReturnReservation& reservation,const std::weak_ptr<const void>& identity) noexcept{
    const auto data=plan.data_;
    if(!native_pk_return_output_plan_current(data)||data->reservation!=reservation||
       data->records.owner_before(identity)||identity.owner_before(data->records))return false;
    // Lock only on the recorded game owner; never retain this State on network.
    const auto actual=data->records.lock(),requested=identity.lock();
    return actual&&actual==requested&&native_pk_return_output_plan_current(data);
}
void Session::fail_native_pk_return_output(const std::shared_ptr<NativePkReturnOutputHold::Data>& data) noexcept{
    if(!data)return;
    bool first;
    std::shared_ptr<NativePkReturnConsumption::Data> successor;
    std::shared_ptr<NativePkReturnPublication::Data> publication;
    std::shared_ptr<NativePkReturnFinalisation::Data> finalisation;
    {
        std::lock_guard lock(data->transition);
        if(data->phase.load()==NativePkReturnOutputHold::Data::Phase::Returned)return; // Old sticky observers no longer owned.
        data->plan->status_identity->active.store(false); // Revoke pure seals before any callbacks/queue cleanup.
        finalisation=data->finalisation.load();
        if(finalisation)finalisation->phase.store(NativePkReturnFinalisationStatus::Failed);
        publication=data->publication.load();
        if(publication)publication->phase.store(NativePkReturnPublicationStatus::Failed);
        successor=data->consumption.load(); // Same guard as prepare/consume association.
        first=data->phase.exchange(NativePkReturnOutputHold::Data::Phase::Failed)!=
            NativePkReturnOutputHold::Data::Phase::Failed;
        if(successor)successor->phase.store(NativePkReturnConsumption::Data::Phase::Failed);
    }
    if(successor)for(const auto& session:data->plan->sessions){
        auto expected=successor;session->impl_->native_pk_return_consumption.compare_exchange_strong(expected,{});
    }
    // The genuine returning pair fails even before installation. Observers
    // belong to this failure ONLY once this exact Data acquired their slot.
    const auto owned=[&](std::size_t index){
        const auto& recipient=data->recipients[index];
        return index<2||recipient->slot_owned.load()||
            recipient->session->impl_->native_pk_return_output.load()==data;
    };
    for(std::size_t index=0;index<data->recipients.size();++index)if(owned(index)){
        const auto& recipient=data->recipients[index];recipient->slot_owned.store(true);
        recipient->session->impl_->close_requested.store(true); // BEFORE any exact slot removal.
    }
    // Repeated failure also discovers late successful CAS before ownership stamp.
    // Unowned nominated observers keep their prior slot/epoch/queue unchanged.
    for(std::size_t index=0;index<data->recipients.size();++index){
        const auto& recipient=data->recipients[index];
        if(owned(index)){
            recipient->slot_owned.store(true);recipient->session->impl_->close_requested.store(true);
            auto expected=data;recipient->session->impl_->native_pk_return_output.compare_exchange_strong(expected,{});
        }
        for(const auto& frame:recipient->frames)frame->budget.exchange({}); // Always refund this Data only.
    }
    if(first)fail_native_pk_return_reservation(data->plan->reservation.data_);
    for(std::size_t index=0;index<data->recipients.size();++index)if(owned(index)){
        const auto& recipient=data->recipients[index];
        if(!recipient->failure_closed.exchange(true)){
            if(recipient->normal)recipient->normal->revoke(); // Own acquired observer's fresh handle only.
            recipient->session->impl_->retire_normal_output(); // Outside all Sync/Budget locks.
        }
        // This flag records one scheduling attempt, not successful execution.
        // Repeated failure must still close each newly-owned late receiver once.
        if(!recipient->close_posted.exchange(true))try{
            recipient->session->impl_->post_status_work(recipient->session->impl_->strand,[session=recipient->session]{session->impl_->close();});
        }catch(...){recipient->session->impl_->close_requested.store(true);}
    }
    if(finalisation){
        for(const auto& weak:finalisation->sessions)if(const auto session=weak.lock()){
            auto expected=finalisation;session->impl_->native_pk_return_finalisation.compare_exchange_strong(expected,{});
            auto history=finalisation;session->impl_->native_pk_return_finalisation_history.compare_exchange_strong(history,{});
        }
        try{Session::schedule_actor_status_work<false>(finalisation->game,
            {finalisation->sessions[0].lock(),finalisation->sessions[1].lock()},[finalisation]{
            if(finalisation->failed_notified.exchange(true)||finalisation->thread!=std::this_thread::get_id())return;
            if(const auto source=finalisation->source.lock())try{
                source->native_pk_return_finalisation_failed(NativePkReturnFinalisation(finalisation));
            }catch(...){}
        });}catch(...){}
    }
    if(publication)try{Session::schedule_actor_status_work<false>(data->plan->game,data->plan->sessions,[publication]{
        if(publication->failed_notified.exchange(true)||publication->plan->thread!=std::this_thread::get_id())return;
        if(const auto owner=publication->source.lock())try{
            owner->native_pk_return_publication_failed(NativePkReturnPublication(publication));
        }catch(...){}
    });}catch(...){}
    if(!first)return;
    try{Session::schedule_actor_status_work<false>(data->plan->game,data->plan->sessions,[data]{
        if(data->failed_notified.exchange(true)||data->plan->thread!=std::this_thread::get_id())return;
        if(const auto source=data->source.lock())try{source->native_pk_return_output_failed(NativePkReturnOutputHold(data));}catch(...){}
    });}catch(...){} // No retry, synthetic notification, rollback or deadline renewal.
    if(successor)try{Session::schedule_actor_status_work<false>(data->plan->game,data->plan->sessions,[successor]{
        if(successor->failed_notified.exchange(true)||successor->plan->thread!=std::this_thread::get_id())return;
        if(const auto source=successor->source.lock())try{
            source->native_pk_return_consumption_failed(NativePkReturnConsumption(successor));
        }catch(...){}
    });}catch(...){}
}
Session::NativePkReturnOutputHold Session::hold_native_pk_return_output(
        const NativePkReturnOutputPlan& plan,std::weak_ptr<NativePkReturnOutputOwner> source){
    const auto prepared=plan.data_;
    if(!native_pk_return_output_plan_current(prepared)||source.expired())
        throw std::invalid_argument("Return output lacks current own private plan/owner");
    // Pure fast admission: an existing healthy observer cohort is not ours.
    // No Data/budget/slot is owned yet, so reject only this genuine returning pair.
    for(const auto& group:prepared->groups)if(group.recipient->impl_->native_pk_return_output.load()){
        fail_native_pk_return_reservation(prepared->reservation.data_);
        throw std::logic_error("Return recipient already belongs to another held cohort");
    }
    bool unused=false;
    if(!prepared->claimed.compare_exchange_strong(unused,true))throw std::logic_error("Return output plan already used");
    std::shared_ptr<NativePkReturnOutputHold::Data> data;
    try{
        std::vector<std::shared_ptr<NativePkReturnOutputHold::Data::Recipient>> recipients;
        recipients.reserve(prepared->groups.size());
        for(const auto& group:prepared->groups){
            std::vector<std::shared_ptr<NativePkReturnOutputHold::Data::Frame>> frames;frames.reserve(group.frames.size());
            for(std::size_t ordinal=0;ordinal<group.frames.size();++ordinal)
                frames.push_back(std::make_shared<NativePkReturnOutputHold::Data::Frame>(group.frames[ordinal],group.frame_seals[ordinal]));
            recipients.push_back(std::make_shared<NativePkReturnOutputHold::Data::Recipient>(group.recipient,group.normal,std::move(frames)));
        }
        data=std::make_shared<NativePkReturnOutputHold::Data>(prepared,std::move(source),std::move(recipients));
        const auto attempt=std::make_shared<Impl::NativePkReturnOutputAttempt>(data);
        std::vector<std::vector<std::shared_ptr<Impl::NativePkReturnOutputWrite>>> markers;markers.reserve(data->recipients.size());
        // Every frame/budget/marker is owned before the FIRST strand post.
        for(std::size_t index=0;index<data->recipients.size();++index){
            const auto& recipient=data->recipients[index];std::vector<std::shared_ptr<Impl::NativePkReturnOutputWrite>> group;
            group.reserve(recipient->frames.size());
            for(std::size_t ordinal=0;ordinal<recipient->frames.size();++ordinal){
                const auto& frame=recipient->frames[ordinal];const auto charge=frame->bytes->size();
                const auto budget=recipient->session->impl_->budget;std::shared_ptr<Reservation> reserved;
                {
                    std::lock_guard lock(budget->mutex);
                    if(charge<=max_buffer-budget->bytes&&budget->count<max_writes){
                        reserved=std::make_shared<Reservation>(budget,charge);budget->bytes+=charge;++budget->count;
                    }
                }
                if(!reserved)throw std::length_error("Return output budget exhausted");
                frame->budget.store(std::move(reserved));
                group.push_back(std::make_shared<Impl::NativePkReturnOutputWrite>(data,frame,index,ordinal));
            }
            markers.push_back(std::move(group));
        }
        if(!native_pk_return_output_plan_current(prepared))throw std::logic_error("Return output source retired before install");
        for(const auto& recipient:data->recipients){
            if(data->phase.load()!=NativePkReturnOutputHold::Data::Phase::Pending)
                throw std::logic_error("Return cohort retired before recipient install");
            std::shared_ptr<NativePkReturnOutputHold::Data> absent;
            if(!recipient->session->impl_->native_pk_return_output.compare_exchange_strong(absent,data))
                throw std::logic_error("Recipient already owns a held return cohort");
            recipient->slot_owned.store(true);
            if(data->phase.load()!=NativePkReturnOutputHold::Data::Phase::Pending){
                fail_native_pk_return_output(data); // Idempotent late-owned cleanup, not first-only.
                throw std::logic_error("Return cohort retired during recipient install");
            }
        }
        data->installed.store(true);
        if(data->phase.load()!=NativePkReturnOutputHold::Data::Phase::Pending||!native_pk_return_output_plan_current(prepared))
            throw std::logic_error("Return output retired during installation");
        for(const auto& recipient:data->recipients)
            if(recipient->session->impl_->native_pk_return_output.load()!=data)throw std::logic_error("Return output halfslot lost");
        for(std::size_t index=0;index<data->recipients.size();++index){
            const auto session=data->recipients[index]->session;
            session->invalidate_actor_status_writes(); // Before held return-group handoff.
            for(const auto& frame:data->recipients[index]->frames)
                (void)session->retire_battle_self_view_wire_output(*frame->bytes);
            session->impl_->post_status_work(session->impl_->strand,[session,data,index,owned=std::move(markers[index]),attempt]()mutable{
                session->impl_->stage_native_pk_return_output(data,index,std::move(owned),attempt);
            });
        }
        return NativePkReturnOutputHold(data);
    }catch(...){
        if(data)fail_native_pk_return_output(data);
        else fail_native_pk_return_reservation(prepared->reservation.data_);
        throw;
    }
}
bool Session::native_pk_return_output_current(const NativePkReturnOutputHold& hold) noexcept{
    const auto data=hold.data_;
    if(!data||data->plan->thread!=std::this_thread::get_id()||
       data->phase.load()!=NativePkReturnOutputHold::Data::Phase::Held||!data->installed.load()||
       data->source.expired()||data->cuts.load()!=data->recipients.size()||
       !native_pk_return_output_plan_current(data->plan))return false;
    for(const auto& recipient:data->recipients)
        if(!recipient->held.load()||recipient->session->impl_->native_pk_return_output.load()!=data)return false;
    return data->phase.load()==NativePkReturnOutputHold::Data::Phase::Held&&native_pk_return_output_plan_current(data->plan);
}
bool Session::native_pk_return_output_matches(const NativePkReturnOutputHold& hold,
        const NativePkReturnOutputPlan& plan,const NativePkReturnReservation& reservation) noexcept{
    const auto data=hold.data_;
    return native_pk_return_output_current(hold)&&data->plan==plan.data_&&
        data->plan->reservation==reservation&&native_pk_return_output_current(hold);
}
Session::NativePkReturnConsumption Session::prepare_native_pk_return_consumption(
        const NativePkReturnOutputHold& held,std::weak_ptr<NativePkReturnConsumptionOwner> owner){
    if(!native_pk_return_output_current(held)||owner.expired())
        throw std::invalid_argument("Return consumption requires actual whole Held cohort/owner");
    const auto output=held.data_;std::array<std::uint64_t,2> old{},future{};
    for(std::size_t index=0;index<2;++index){
        const auto sync=output->plan->sessions[index]->impl_->normal_output_sync;
        std::lock_guard lock(sync->mutex);old[index]=sync->epoch.load();
        if(old[index]==std::numeric_limits<std::uint64_t>::max())
            throw std::overflow_error("Return consumption normal output epoch exhausted");
        future[index]=old[index]+1;
    }
    const auto data=std::make_shared<NativePkReturnConsumption::Data>(output,std::move(owner),old,future);
    const auto custody=std::make_shared<NativePkReturnConsumption::Custody>(data);
    {
        std::lock_guard lock(output->transition);
        if(!native_pk_return_output_current(held)||output->consumption.load())
            throw std::logic_error("Return consumption source already prepared or retired");
        output->consumption.store(data);
    }
    return NativePkReturnConsumption(data,custody); // Prepared is NOT successor Current.
}
bool Session::consume_native_pk_return_output(const NativePkReturnConsumption& value) noexcept{
    const auto data=value.data_;
    const auto custody=value.custody_; // Own proof through the complete no-observer transition.
    if(!data||data->plan->thread!=std::this_thread::get_id())return false;
    const auto output=data->output.lock();if(!output)return false;
    bool success=false;
    try{
        {
            std::lock_guard transition(output->transition);
            const auto first=data->plan->sessions[0],second=data->plan->sessions[1];
            std::scoped_lock sync(first->impl_->normal_output_sync->mutex,second->impl_->normal_output_sync->mutex);
            const auto apply=[&]()->bool{
            // Survivor handle checks lock only their distinct Syncs; returning
            // Syncs are held here. No callback/allocation/yield inside transition.
            auto prepared=NativePkReturnConsumption::Data::Phase::Prepared;
            if(output->consumption.load()!=data||data->source.expired()||
               !native_pk_return_output_current(NativePkReturnOutputHold(output))||
               first->impl_->normal_output_sync->epoch.load()!=data->old_epochs[0]||
               second->impl_->normal_output_sync->epoch.load()!=data->old_epochs[1]||
               !data->phase.compare_exchange_strong(prepared,NativePkReturnConsumption::Data::Phase::Consuming))
                return false;
            auto held=NativePkReturnOutputHold::Data::Phase::Held;
            auto reserved=NativePkReturnReservation::Data::Phase::Reserved;
            if(!output->phase.compare_exchange_strong(held,NativePkReturnOutputHold::Data::Phase::Consuming)||
               !data->plan->reservation.data_->phase.compare_exchange_strong(reserved,NativePkReturnReservation::Data::Phase::Consuming))
                return false;
            for(const auto& session:data->plan->sessions){
                std::shared_ptr<NativePkReturnConsumption::Data> absent;
                if(!session->impl_->native_pk_return_consumption.compare_exchange_strong(absent,data))
                    return false;
            }
            for(std::size_t index=0;index<2;++index){
                const auto session=data->plan->sessions[index];auto& s=*session->impl_;
                const auto prep=data->plan->preparations[index].data_;const auto terminal=prep->terminal.data_;
                const auto entry=terminal->entry.data_;const auto& request=entry->request;
                if(s.close_requested.load()||s.native_pk_terminal.load()!=terminal||
                   s.native_pk_return_output.load()!=output||s.native_pk_return_consumption.load()!=data)
                    return false;
                auto old_normal=entry->initialization.data_;auto old_world=entry->battle_identity;
                auto old_battle=request.prebattle_generation+1;
                if(!s.normal_initialization.compare_exchange_strong(old_normal,prep->initialization.data_)||
                   !s.world_delivery_identity.compare_exchange_strong(old_world,prep->world_identity)||
                   !session->battle_generation_.compare_exchange_strong(old_battle,prep->initialization.data_->effective_battle))
                    return false;
                s.normal_output_sync->epoch.store(data->new_epochs[index]);
                auto battle=SessionState::InBattle;
                if(!session->state_.compare_exchange_strong(battle,SessionState::InWorld))
                    return false;
                terminal->accepted.store(false);terminal->phase.store(NativePkTerminalBarrier::Data::Phase::Consumed);
            }
            auto consuming=NativePkReturnReservation::Data::Phase::Consuming;
            if(!data->plan->reservation.data_->phase.compare_exchange_strong(consuming,NativePkReturnReservation::Data::Phase::Consumed))
                return false;
            output->phase.store(NativePkReturnOutputHold::Data::Phase::Consumed);
            data->phase.store(NativePkReturnConsumption::Data::Phase::Consumed);
            return native_pk_return_consumption_current(value);
            };success=apply();
        }
    }catch(...){}
    if(!success)fail_native_pk_return_output(output); // No rollback of changed prefix; close exact owned cohort.
    return success;
}
bool Session::native_pk_return_consumption_current(const NativePkReturnConsumption& value) noexcept{
    try{
    const auto data=value.data_;
    if(!data||data->plan->thread!=std::this_thread::get_id()||
       data->phase.load()!=NativePkReturnConsumption::Data::Phase::Consumed||data->source.expired()||
       data->plan->records.expired())return false;
    const auto output=data->output.lock();
    if(!output||output->consumption.load()!=data||
       output->phase.load()!=NativePkReturnOutputHold::Data::Phase::Consumed||
       output->cuts.load()!=output->recipients.size())return false;
    for(std::size_t index=0;index<2;++index){
        const auto session=data->plan->sessions[index];
        if(!session->impl_->native_pk_return_consumption_transport_current(data,index))return false;
        const auto prep=data->plan->preparations[index].data_;
        if(session->account_id!=prep->world_identity->account||session->character_id!=prep->world_identity->character)return false;
    }
    for(std::size_t index=0;index<output->recipients.size();++index){
        const auto& recipient=output->recipients[index];
        if(!recipient->held.load()||recipient->session->impl_->native_pk_return_output.load()!=output)return false;
        if(index>=2){
            if(!recipient->normal||!recipient->session->normal_world_output_current_on_game(*recipient->normal))return false;
        }
    }
    return data->phase.load()==NativePkReturnConsumption::Data::Phase::Consumed&&
        output->phase.load()==NativePkReturnOutputHold::Data::Phase::Consumed&&
        data->plan->sessions[0]->impl_->native_pk_return_consumption_transport_current(data,0)&&
        data->plan->sessions[1]->impl_->native_pk_return_consumption_transport_current(data,1);
    }catch(...){return false;}
}
bool Session::native_pk_return_consumption_matches(const NativePkReturnConsumption& value,
        const NativePkReturnOutputHold& held,const NativePkReturnOutputPlan& plan,
        const NativePkReturnReservation& reservation) noexcept{
    const auto data=value.data_;
    return native_pk_return_consumption_current(value)&&data->output.lock()==held.data_&&
        data->plan==plan.data_&&data->plan->reservation==reservation&&native_pk_return_consumption_current(value);
}
bool Session::native_pk_return_consumption_records_matches(const NativePkReturnConsumption& value,
        const std::weak_ptr<const void>& identity) noexcept{
    const auto data=value.data_;
    if(!native_pk_return_consumption_current(value)||data->plan->records.owner_before(identity)||
       identity.owner_before(data->plan->records))return false;
    const auto actual=data->plan->records.lock(),requested=identity.lock(); // Recorded game thread only.
    return actual&&actual==requested&&native_pk_return_consumption_current(value);
}
Session::NativePkReturnPublicationStatus Session::NativePkReturnPublication::status()const noexcept{
    return data_?data_->phase.load():NativePkReturnPublicationStatus::Failed;
}
Session::NativePkReturnPublication Session::prepare_native_pk_return_publication(
        const NativePkReturnConsumption& consumed,std::weak_ptr<NativePkReturnPublicationOwner> owner){
    if(!native_pk_return_consumption_current(consumed)||owner.expired())
        throw std::invalid_argument("Return publication lacks exact consumed source");
    const auto output=consumed.data_->output.lock();
    std::vector<std::shared_ptr<NativePkReturnPublication::Data::Progress>> progress;progress.reserve(output->recipients.size());
    for(const auto& recipient:output->recipients)progress.push_back(std::make_shared<NativePkReturnPublication::Data::Progress>());
    const auto data=std::make_shared<NativePkReturnPublication::Data>(output,consumed.data_,std::move(owner),std::move(progress));
    const auto work=std::make_shared<NativePkReturnPublication::Work>(data);
    const auto custody=std::make_shared<NativePkReturnPublication::Custody>(data,work);
    {
        std::lock_guard lock(output->transition);
        if(!native_pk_return_consumption_current(consumed)||output->publication.load())
            throw std::logic_error("Return publication already prepared or retired");
        output->publication.store(data);
    }
    return NativePkReturnPublication(data,custody);
}
bool Session::native_pk_return_publication_current(const NativePkReturnPublication& value) noexcept{
    try{
    const auto data=value.data_;
    if(!data||data->plan->thread!=std::this_thread::get_id()||data->source.expired()||
       data->phase.load()==NativePkReturnPublicationStatus::Failed||data->plan->records.expired())return false;
    const auto output=data->output.lock();const auto consumption=data->consumption.lock();
    if(!output||!consumption||output->publication.load()!=data||output->consumption.load()!=consumption||
       !native_pk_return_consumption_current(NativePkReturnConsumption(consumption)))return false;
    if(data->phase.load()==NativePkReturnPublicationStatus::Written){
        if(data->cuts.load()!=data->progress.size())return false;
        for(std::size_t index=0;index<data->progress.size();++index)
            if(!data->progress[index]->done.load()||!data->progress[index]->released.load()||
               data->progress[index]->next.load()!=output->recipients[index]->frames.size())return false;
    }
    return data->phase.load()!=NativePkReturnPublicationStatus::Failed&&
        native_pk_return_consumption_current(NativePkReturnConsumption(consumption));
    }catch(...){return false;}
}
bool Session::native_pk_return_publication_matches(const NativePkReturnPublication& value,
        const NativePkReturnConsumption& consumed) noexcept{
    return native_pk_return_publication_current(value)&&value.data_->consumption.lock()==consumed.data_&&
        native_pk_return_publication_current(value);
}
bool Session::native_pk_return_publication_records_matches(const NativePkReturnPublication& value,
        const std::weak_ptr<const void>& identity) noexcept{
    if(!native_pk_return_publication_current(value)||value.data_->plan->records.owner_before(identity)||
       identity.owner_before(value.data_->plan->records))return false;
    const auto actual=value.data_->plan->records.lock(),requested=identity.lock();
    return actual&&actual==requested&&native_pk_return_publication_current(value);
}
bool Session::native_pk_return_publication_exposure_possible(const NativePkReturnPublication& value) noexcept{
    return value.data_&&value.data_->exposed.load(); // Sticky after Failed, no Current requirement.
}
void Session::abandon_native_pk_return_publication(const NativePkReturnPublication& value) noexcept{
    if(value.data_)if(const auto output=value.data_->output.lock())fail_native_pk_return_output(output);
}
bool Session::release_native_pk_return_publication(const NativePkReturnPublication& value) noexcept{
    const auto data=value.data_;const auto custody=value.custody_;
    if(!data||data->plan->thread!=std::this_thread::get_id())return false;
    const auto output=data->output.lock();if(!output)return false;
    try{
        std::shared_ptr<NativePkReturnPublication::Work> work;
        {
            std::lock_guard lock(output->transition);
            auto prepared=NativePkReturnPublicationStatus::Prepared;
            if(!custody||!custody->prepared_work||!native_pk_return_publication_current(value)||
               !data->phase.compare_exchange_strong(prepared,NativePkReturnPublicationStatus::Released))
                throw std::logic_error("Return publication release already consumed or stale");
            data->exposed.store(true); // BEFORE first post/unhold; even a dropped task may have exposed peers.
            work=std::move(custody->prepared_work);
        }
        for(std::size_t index=0;index<output->recipients.size();++index){
            if(data->phase.load()!=NativePkReturnPublicationStatus::Released)throw std::logic_error("Return release failed midpost");
            const auto session=output->recipients[index]->session;
            session->impl_->post_status_work(session->impl_->strand,[session,work,index]{session->impl_->release_native_pk_return_publication_recipient(work,index);});
        }
        return true;
    }catch(...){fail_native_pk_return_output(output);return false;}
}
Session::NativePkReturnFinalisationStatus Session::NativePkReturnFinalisation::status()const noexcept{
    return data_?data_->phase.load():NativePkReturnFinalisationStatus::Failed;
}
Session::NativePkReturnFinalisation Session::prepare_native_pk_return_finalisation(
        const NativePkReturnPublication& value,std::weak_ptr<NativePkReturnFinalisationOwner> owner){
    if(value.status()!=NativePkReturnPublicationStatus::Written||!native_pk_return_publication_current(value)||owner.expired())
        throw std::invalid_argument("Return finalisation requires actual whole Written source");
    const auto output=value.data_->output.lock();const auto consumed=value.data_->consumption.lock();
    std::array<std::shared_ptr<const void>,2> common{
        output->plan->sessions[0]->impl_->common_world_identity.load(),output->plan->sessions[1]->impl_->common_world_identity.load()};
    const auto data=std::make_shared<NativePkReturnFinalisation::Data>(value.data_,output,std::move(owner),common,consumed->new_epochs);
    const auto work=std::make_shared<NativePkReturnFinalisation::Work>(data);data->work=work;
    const auto custody=std::make_shared<NativePkReturnFinalisation::Custody>(data,work);
    {
        std::lock_guard lock(output->transition);
        if(!native_pk_return_publication_current(value)||output->finalisation.load())
            throw std::logic_error("Return finalisation already prepared or retired");
        for(const auto& session:output->plan->sessions){
            if(session->impl_->native_pk_return_finalisation.load())
                throw std::logic_error("Returning Session already has a finalisation");
            if(const auto old=session->impl_->native_pk_return_finalisation_history.load()){
                if(!old->returned_notified.load())throw std::logic_error("Returning Session has unfinished return history");
                auto completed=old;session->impl_->native_pk_return_finalisation_history.compare_exchange_strong(completed,{});
            }
        }
        for(std::size_t index=0;index<2;++index){
            const auto terminal=data->preparations[index].data_->terminal.data_;
            std::lock_guard terminal_lock(terminal->finalisation_mutex);
            if(!terminal->finalisation.expired())throw std::logic_error("Original terminal already has a finalisation");
            terminal->finalisation=data;
        }
        output->finalisation.store(data);
        for(const auto& session:output->plan->sessions){
            session->impl_->native_pk_return_finalisation_history.store(data);
            session->impl_->native_pk_return_finalisation.store(data);
        }
    }
    return NativePkReturnFinalisation(data,custody);
}
bool Session::native_pk_return_finalisation_current(const NativePkReturnFinalisation& value) noexcept{
    try{
    const auto data=value.data_;if(!data||data->thread!=std::this_thread::get_id()||
        data->phase.load()==NativePkReturnFinalisationStatus::Failed)return false;
    for(std::size_t index=0;index<2;++index){
        const auto session=data->sessions[index].lock();
        if(!session||!session->impl_->native_pk_return_finalisation_transport_current(data,index)||
           session->account_id!=data->preparations[index].data_->world_identity->account||
           session->character_id!=data->preparations[index].data_->world_identity->character)return false;
    }
    if(data->phase.load()!=NativePkReturnFinalisationStatus::Returned){
        const auto pub=data->publication.lock();const auto output=data->output.lock();
        if(data->source.expired()||!pub||!output||output->finalisation.load()!=data||
           pub->phase.load()!=NativePkReturnPublicationStatus::Written||
           !native_pk_return_publication_current(NativePkReturnPublication(pub)))return false;
        if(data->phase.load()==NativePkReturnFinalisationStatus::Ready&&
           (data->ready_cuts.load()!=2||!data->ready[0].load()||!data->ready[1].load()))return false;
    }
    return data->phase.load()!=NativePkReturnFinalisationStatus::Failed;
    }catch(...){return false;}
}
bool Session::native_pk_return_finalisation_matches(const NativePkReturnFinalisation& value,
        const NativePkReturnPublication& pub) noexcept{
    return native_pk_return_finalisation_current(value)&&value.data_->publication.lock()==pub.data_&&
        native_pk_return_finalisation_current(value);
}
bool Session::native_pk_return_finalisation_records_matches(const NativePkReturnFinalisation& value,
        const std::weak_ptr<const void>& records) noexcept{
    if(!native_pk_return_finalisation_current(value)||value.data_->records.owner_before(records)||
       records.owner_before(value.data_->records))return false;
    const auto actual=value.data_->records.lock(),requested=records.lock();
    return actual&&actual==requested&&native_pk_return_finalisation_current(value);
}
void Session::fail_native_pk_return_finalisation(const std::shared_ptr<NativePkReturnFinalisation::Data>& data) noexcept{
    if(!data)return;
    {std::lock_guard lock(data->transition);
     if(data->phase.load()==NativePkReturnFinalisationStatus::Returned&&data->returned_notified.load())return;
     data->phase.store(NativePkReturnFinalisationStatus::Failed);}
    if(!data->detached.load())if(const auto output=data->output.lock())fail_native_pk_return_output(output);
    // After accepted detach ONLY returning Sessions remain owned; sticky old
    // observer history must not close their new unrelated cohorts or epochs.
    for(const auto& weak:data->sessions)if(const auto session=weak.lock()){
        session->impl_->close_requested.store(true);
        auto expected=data;session->impl_->native_pk_return_finalisation.compare_exchange_strong(expected,{});
        auto history=data;session->impl_->native_pk_return_finalisation_history.compare_exchange_strong(history,{});
    }
    for(const auto& weak:data->sessions)if(const auto session=weak.lock())try{
        session->impl_->post_status_work(session->impl_->strand,[session]{session->impl_->close();});
    }catch(...){}
    try{Session::schedule_actor_status_work<false>(data->game,
        {data->sessions[0].lock(),data->sessions[1].lock()},[data]{
        if(data->failed_notified.exchange(true)||data->thread!=std::this_thread::get_id())return;
        if(const auto source=data->source.lock())try{source->native_pk_return_finalisation_failed(NativePkReturnFinalisation(data));}catch(...){}
    });}catch(...){}
}
void Session::abandon_native_pk_return_finalisation(const NativePkReturnFinalisation& value) noexcept{
    if(value.data_&&value.status()!=NativePkReturnFinalisationStatus::Returned)fail_native_pk_return_finalisation(value.data_);
}
bool Session::acquire_native_pk_return_finalisation(const NativePkReturnFinalisation& value) noexcept{
    const auto data=value.data_;const auto custody=value.custody_;
    if(!data||data->thread!=std::this_thread::get_id())return false;
    try{
        if(!custody||!custody->prepared_work||!native_pk_return_finalisation_current(value))throw std::logic_error("Finalisation stale");
        auto prepared=NativePkReturnFinalisationStatus::Prepared;
        if(!data->phase.compare_exchange_strong(prepared,NativePkReturnFinalisationStatus::Checking))throw std::logic_error("Finalisation reused");
        const auto work=std::move(custody->prepared_work);
        for(std::size_t index=0;index<2;++index){
            const auto session=data->sessions[index].lock();if(!session)throw std::logic_error("Finalisation Session lost");
            session->impl_->post_status_work(session->impl_->strand,[session,work,index]{session->impl_->stage_native_pk_return_finalisation(work,index);});
        }
        return true;
    }catch(...){fail_native_pk_return_finalisation(data);return false;}
}
bool Session::complete_native_pk_return_finalisation(const NativePkReturnFinalisation& value) noexcept{
    const auto data=value.data_;if(!data||data->thread!=std::this_thread::get_id()||
        data->phase.load()==NativePkReturnFinalisationStatus::Returned)return false;
    const auto output=data->output.lock();const auto work=data->work.lock();
    bool applied=false;
    try{
        if(!output||!work)throw std::logic_error("Finalisation lacks actual pending task");
        {
            std::scoped_lock transition(output->transition,data->transition);
            const auto detach=[&]()->bool{
            if(data->phase.load()!=NativePkReturnFinalisationStatus::Ready||!native_pk_return_finalisation_current(value))
                return false;
            const auto consumed=output->consumption.load();const auto pub=output->publication.load();
            if(!consumed||!pub)return false;
            // No source/provider/query/allocation under the transition. The
            // actual owner already durably released and adopted the registry.
            for(std::size_t index=0;index<2;++index){
                const auto session=data->sessions[index].lock();
                if(!session||session->impl_->native_pk_terminal.load()!=data->preparations[index].data_->terminal.data_)
                    return false;
            }
            data->detached.store(true);data->phase.store(NativePkReturnFinalisationStatus::Returned);
            output->phase.store(NativePkReturnOutputHold::Data::Phase::Returned);
            output->plan->reservation.data_->phase.store(NativePkReturnReservation::Data::Phase::Returned);
            consumed->phase.store(NativePkReturnConsumption::Data::Phase::Returned);pub->successfully_returned.store(true);
            for(std::size_t index=0;index<2;++index){
                const auto session=data->sessions[index].lock();auto& impl=*session->impl_;
                auto term=data->preparations[index].data_->terminal.data_;
                term->accepted.store(false);term->phase.store(NativePkTerminalBarrier::Data::Phase::Returned);
                impl.native_pk_terminal.compare_exchange_strong(term,{});
                auto pair=output->plan->reservation.data_;impl.native_pk_return.compare_exchange_strong(pair,{});
                auto current=consumed;impl.native_pk_return_consumption.compare_exchange_strong(current,{});
            }
            for(const auto& recipient:output->recipients){
                auto old=output;recipient->session->impl_->native_pk_return_output.compare_exchange_strong(old,{});
            } // Observer caps/epochs/queues preserved, no revocation or close.
            return true;
            };applied=detach();
        }
        if(!applied){fail_native_pk_return_finalisation(data);return false;}
        for(std::size_t index=0;index<2;++index){
            const auto session=data->sessions[index].lock();if(!session)throw std::logic_error("Returned Session lost");
            session->impl_->post_status_work(session->impl_->strand,[session,work,index]{session->impl_->resume_native_pk_return_finalisation(work,index);});
        }
        return true;
    }catch(...){fail_native_pk_return_finalisation(data);return false;} // Durable prefix never rolled back.
}
void Session::send_native_pk_output(const NativePkEntryHold& hold,NativeBattleSkill delivery,
        std::weak_ptr<NativeBattleSkillPublicationOwner> source){
    impl_->unsupported_callback_output();
    if(delivery)(void)retire_battle_self_view_logical_output(delivery->logical);
    [[maybe_unused]] const auto status_admission=begin_actor_status_writer();
    invalidate_actor_status_writes();
    // CUSTOM-0115 explicit exact accepted entry. Raw output is never room,
    // grant/skill or current checkpoint authority; its game owner must prove it.
    if(impl_->native_pk_terminal.load() || !native_pk_entry_written_current(hold))
        throw std::invalid_argument("Native PK output requires its actual accepted written entry");
    const auto data=hold.data_;const auto common=impl_->common_world_identity.load();
    if(!delivery || source.expired() || !delivery->sequence || delivery->session!=id() ||
       delivery->account!=data->request.account || delivery->character!=data->request.character ||
       delivery->common_generation!=data->request.common_generation ||
       delivery->battle_generation!=data->request.prebattle_generation+1 ||
       impl_->common_ready_thread!=std::this_thread::get_id() || !common)
        throw std::invalid_argument("Native PK output recipient identity mismatch");
    const auto records=RecoveredTaiwanServerRecords::read(delivery->logical);
    // Exact retained outbox bytes can use either the current per-consumer HP
    // policy or the old all-HP86 policy. Publication still binds this delivery
    // to the private room and exact persisted row; grammar grants no authority.
    const bool grant=records&&records->size()==1&&records->front().opcode==0x86&&
        RecoveredBattlePlayerGrant::parse(records->front().bytes).has_value();
    const bool valid=grant||RecoveredTaiwanPkTerminalNotification::matches_retained_output_sequence(delivery->logical);
    if(!valid)throw std::invalid_argument("Native PK output requires standalone primary grant or qualified scalar result records");
    const auto charge=delivery->logical.size()+3;
    auto budget=impl_->budget;std::shared_ptr<Reservation> reservation;
    {
        std::lock_guard lock(budget->mutex);
        if(charge<=max_buffer-budget->bytes && budget->count<max_writes){
            reservation=std::make_shared<Reservation>(budget,charge);
            budget->bytes+=charge;++budget->count;
        }
    }
    if(!reservation)throw std::length_error("Native PK output queue reservation failed");
    auto pending=std::make_shared<Impl::NativeBattlePending>();
    pending->delivery=std::move(delivery);pending->common=common;
    pending->source=std::move(source);pending->pk_entry=data;
    std::shared_ptr<Impl::NativeBattlePending> absent;
    impl_->retire_normal_output(); // Before actual publication/PK hold is installed.
    if(!impl_->native_battle_pending.compare_exchange_strong(absent,pending))
        throw std::logic_error("Native battle publication already pending");
    try {impl_->post_status_work(impl_->strand,[self=shared_from_this(),pending,reservation=std::move(reservation)]()mutable{
        auto& s=*self->impl_;
                [[maybe_unused]] const auto status_admission=self->begin_actor_status_writer();
        if(s.native_battle_pending.load()!=pending || pending->completing.load())return;
        try{
            s.native_pk_timer.expires_after(close_timeout);
            s.native_pk_timer.async_wait([self,pending](const asio::error_code& ec){
                auto& s=*self->impl_;
                [[maybe_unused]] const auto status_admission=self->begin_actor_status_writer();
                if(ec || s.native_battle_pending.load()!=pending)return;
                // Schedule at most one failure completion if the game executor
                // can accept it. Never wait forever for a delayed final post.
                s.complete_native_battle(pending,false);
                auto expected=pending;s.native_battle_pending.compare_exchange_strong(expected,{});
                s.fail("Native PK output hold/write completion deadline expired");
            });
            s.native_pk_output_staged=pending;s.native_pk_output_reservation=std::move(reservation);
            s.native_battle_read_paused=true;s.stage_native_pk_output();
        }catch(...){
            // Timer allocation can fail before any bounded callback exists.
            s.complete_native_battle(pending,false);
            auto expected=pending;s.native_battle_pending.compare_exchange_strong(expected,{});
            s.native_pk_timer.cancel();s.fail("Native PK output encoding/timer/handoff failed");
        }
    });}catch(...){
        auto expected=pending;impl_->native_battle_pending.compare_exchange_strong(expected,{});
        throw; // No strand acceptance; source retains its durable row unsubmitted.
    }
}
bool Session::commit_native_pk_entry(const NativePkEntryHold& hold)noexcept {
    if(!native_pk_entry_current(hold))return false;
    const auto data=hold.data_;
    auto expected=NativePkEntryHold::Data::Phase::Held;
    if(!data->phase.compare_exchange_strong(expected,NativePkEntryHold::Data::Phase::Committed))return false;
    set_state(SessionState::InBattle);
    impl_->world_delivery_identity.store(data->battle_identity); // Preallocated before room COMMIT.
    return !closing() && state()==SessionState::InBattle &&
        battle_generation()==data->request.prebattle_generation+1;
}
void Session::release_native_pk_entry(const NativePkEntryHold& hold) {
    [[maybe_unused]] const auto status_admission=begin_actor_status_writer();
    invalidate_actor_status_writes();
    const auto data=hold.data_;
    if(!data || data->thread!=std::this_thread::get_id() || data->game!=impl_->game ||
       data->session.lock().get()!=this || data->phase.load()!=NativePkEntryHold::Data::Phase::Committed ||
       !impl_->native_pk_transport_current(data,true) || account_id!=data->request.account ||
       character_id!=data->request.character)
        throw std::logic_error("Native PK release lacks exact committed transport hold");
    // This post can allocate/throw AFTER durable activation; caller must close
    // both peers and retain durable recovery, never pretend rollback succeeded.
    impl_->post_status_work(impl_->strand,[self=shared_from_this(),data] {
        auto& s=*self->impl_;
                [[maybe_unused]] const auto status_admission=self->begin_actor_status_writer();
        if(data->completing.load())return;
        if(!s.native_pk_transport_current(data,true) ||
           data->phase.load()!=NativePkEntryHold::Data::Phase::Committed) {
            s.fail("Native PK source changed before release");return;
        }
        const auto found=std::find_if(s.writes.begin(),s.writes.end(),[&](const Impl::Write& w){return w.native_pk==data;});
        if(found==s.writes.end() || !found->held || found->bytes!=data->frame) {
            s.fail("Native PK held write missing at release");return;
        }
        data->phase.store(NativePkEntryHold::Data::Phase::Released);
        found->held=false;if(found==s.writes.begin())s.write();
    });
}
void Session::abort_native_pk_entry(const NativePkEntryHold& hold) {
    [[maybe_unused]] const auto status_admission=begin_actor_status_writer();
    invalidate_actor_status_writes();
    const auto data=hold.data_;
    if(!data || data->thread!=std::this_thread::get_id() || data->game!=impl_->game ||
       data->session.lock().get()!=this)throw std::logic_error("Native PK abort game owner mismatch");
    if(impl_->native_pk_pending.load()!=data || data->completing.load())return;
    auto phase=data->phase.load();
    for(;;) {
        if(phase!=NativePkEntryHold::Data::Phase::Preparing && phase!=NativePkEntryHold::Data::Phase::Held) {
            close();return;
        }
        if(data->phase.compare_exchange_weak(phase,NativePkEntryHold::Data::Phase::Aborted))break;
    }
    data->clean_abort.store(true);
    impl_->post_status_work(impl_->strand,[self=shared_from_this(),data] {
        auto& s=*self->impl_;
                [[maybe_unused]] const auto status_admission=self->begin_actor_status_writer();
        if(s.native_pk_pending.load()!=data || data->completing.load())return;
        const auto found=std::find_if(s.writes.begin(),s.writes.end(),[&](const Impl::Write& w){return w.native_pk==data;});
        if(found!=s.writes.end()) {
            if(!found->held || found->bytes!=data->frame) {s.fail("Native PK abort encountered released write");return;}
            const bool front=found==s.writes.begin();
            s.write_bytes-=found->bytes->size();s.writes.erase(found);
            if(front && !s.writes.empty())s.write();
        }
        s.native_pk_reservation.reset();s.complete_native_pk(data,false);
    });
}
void Session::send_qualified_world_records_with_acceptance(const NormalWorldInitialization& initialization,
    std::vector<std::uint8_t> logical,WorldReplyPushWire profile,WorldDeliveryIdentity expected,std::function<void(bool)> acceptance,
    std::shared_ptr<const std::atomic_bool> source_live){
    const auto init=initialization; // Retain exact receipt across synchronous provider reentry.
    std::shared_ptr<Impl::QualifiedWorldPushPending> pending;
    try{pending=std::make_shared<Impl::QualifiedWorldPushPending>(std::move(acceptance));}
    catch(...){if(acceptance){auto once=std::move(acceptance);try{once(false);}catch(...){}}return;}
    try{
        // The private receipt proves the actual GAME thread before any bare
        // account/character read. A caller cannot nominate a new owner thread.
        if(!normal_world_initialization_current_on_game(init)||!native_channel_binding_current()||(source_live&&!source_live->load())){
            if(observed_world_callback==this&&impl_->reply_push_capture)impl_->fail_reply_pushes();
            pending->settle(false);return;
        }
        if(qualified_world_push_profile)impl_->reject_qualified_profile_sender();
        if(observed_world_callback==this&&impl_->reply_push_capture){
            // The enclosing original-run profile owns these bytes. Do not
            // invoke the async profile or mint an independent side component.
            if(source_live&&!source_live->load()){impl_->fail_reply_pushes();pending->settle(false);return;}
            (void)retire_battle_self_view_logical_output(logical);
            [[maybe_unused]] const auto status_admission=begin_actor_status_writer();invalidate_actor_status_writes();
            impl_->capture_reply_push(logical,[pending](bool enqueued){pending->settle(enqueued);},&expected,std::move(source_live));return;
        }
        if(impl_->qualified_push_active){
            impl_->qualified_push_active->invalid.store(true);impl_->qualified_push_active->settle(false);pending->settle(false);return;
        }
        impl_->qualified_push_active=pending;
        struct Reset {Impl& state;std::shared_ptr<Impl::QualifiedWorldPushPending> pending;~Reset(){if(state.qualified_push_active==pending)state.qualified_push_active.reset();}} reset{*impl_,pending};
        const auto component=impl_->observe_callback_push(WorldCallbackOutput::Kind::AcceptedWorldRecords,logical);
        (void)retire_battle_self_view_logical_output(logical);
        [[maybe_unused]] const auto status_admission=begin_actor_status_writer();invalidate_actor_status_writes();
        const auto tuple_current=[&]{const auto actual=impl_->world_delivery_identity.load();return actual&&expected.account&&expected.character&&expected.world_generation&&
            expected.account==account_id&&expected.character==character_id&&actual->account==expected.account&&actual->character==expected.character&&
            actual->world_generation==expected.world_generation&&actual->battle_generation==expected.battle_generation&&battle_generation()==expected.battle_generation;};
        if(!profile||logical.empty()||logical.size()>RecoveredWorldFrame::max_logical_size||!tuple_current()) {pending->settle(false);return;}
        const auto recipient=capture_normal_world_output_on_game(init);
        if(!recipient){pending->settle(false);return;}
        const auto charge=logical.size()+3;auto budget=impl_->budget;
        auto reservation=std::make_shared<Reservation>(budget,charge,1,false);
        bool reserved=false;
        {std::lock_guard lock(budget->mutex);if(charge<=max_buffer-budget->bytes&&budget->count<max_writes){budget->bytes+=charge;++budget->count;reservation->charged=true;reserved=true;}}
        if(!reserved){pending->settle(false);return;}
        if(source_live&&!source_live->load()){pending->settle(false);return;}
        // The explicit provider receives a view of mutable owned input. Keep
        // its original value private so a provider cannot relabel its output
        // by modifying that input before the current-profile validation.
        const auto original_logical=logical;
        if(pending->invalid.load()||pending->settled.load()||(source_live&&!source_live->load())||
           !normal_world_initialization_current_on_game(init)||!normal_world_output_current_on_game(*recipient)||
           !native_channel_binding_current()||!tuple_current()){pending->settle(false);return;}
        std::optional<std::vector<std::uint8_t>> framed;
        {
            struct ProfileScope {Session* previous;explicit ProfileScope(Session& owner):previous(qualified_world_push_profile){qualified_world_push_profile=&owner;}~ProfileScope(){qualified_world_push_profile=previous;}} scope(*this);
            framed=profile(*this,logical); // Synchronous GAME-only explicit profile; no sender side effects.
        }
        if(!framed||framed->size()!=charge||framed->size()<4||std::size_t((*framed)[0])+256u*(*framed)[1]!=framed->size()||
           pending->invalid.load()||pending->settled.load()||(source_live&&!source_live->load())||!normal_world_initialization_current_on_game(init)||
           !normal_world_output_current_on_game(*recipient)||!native_channel_binding_current()||!tuple_current()){
            pending->settle(false);return;
        }
        // Actual accepted connections currently use the fixed zero-seed
        // handshake. Header/length alone does not qualify this peer's cipher
        // or logical message. Keep the provider's original wire unchanged.
        const auto decoded=RecoveredWorldFrame::decode(*framed);
        if(!decoded||*decoded!=original_logical||logical!=original_logical){pending->settle(false);return;}
        const auto wire=std::make_shared<const std::vector<std::uint8_t>>(std::move(*framed));
        // Snapshot/decode/immutable-wire allocations may invoke allocation
        // failure handlers. Requalify the complete GAME source at handoff.
        if(pending->invalid.load()||pending->settled.load()||(source_live&&!source_live->load())||
           !normal_world_initialization_current_on_game(init)||!normal_world_output_current_on_game(*recipient)||
           !native_channel_binding_current()||!tuple_current()){pending->settle(false);return;}
        const auto target=recipient->data_;
        // No profile, logical renderer or GAME-owned supplier crosses this
        // handoff. The private pending owner fails a dropped/unrun post once.
        impl_->post_status_work(impl_->strand,[self=shared_from_this(),target,wire,reservation,pending,component,expected,source_live]() mutable {
            auto& state=*self->impl_;
            [[maybe_unused]] const auto status_admission=self->begin_actor_status_writer();
            const auto tuple_current=[&]{const auto actual=state.world_delivery_identity.load();return actual&&actual->account==expected.account&&actual->character==expected.character&&
                actual->world_generation==expected.world_generation&&actual->battle_generation==expected.battle_generation&&self->battle_generation()==expected.battle_generation;};
            if(state.closing||state.close_requested.load()||pending->invalid.load()||pending->settled.load()||(source_live&&!source_live->load())||
               state.mode!=ProtocolMode::God2CharacterConnection||state.c2s0002_state!=Impl::C2S0002State::WorldTailAccepted||!tuple_current()){pending->settle(false);return;}
            try{
                auto bytes=std::make_shared<std::vector<std::uint8_t>>(*wire);
                if(bytes->empty()||bytes->size()!=reservation->bytes||*bytes!=*wire||bytes->size()>max_buffer-state.write_bytes||state.writes.size()>=max_writes){
                    pending->settle(false);state.fail("Qualified world push frame/queue limit");return;
                }
                if(!state.terminal_write_allowed()){pending->settle(false);return;}
                bool queued=false;
                {
                    std::lock_guard lock(target->sync->mutex);
                    if(!pending->invalid.load()&&!pending->settled.load()&&(!source_live||source_live->load())&&state.normal_output_transport_current_locked(target)&&tuple_current()){
                        Impl::Write output{bytes,std::move(reservation)};
                        output.qualified_source_live=source_live;
                        if(component){component->frame=bytes;component->receipt->wire.store(bytes);output.callback_component=component;}
                        state.append_write(std::move(output));state.write_bytes+=bytes->size();queued=true;
                    }
                }
                // Source mutex is released before the once callback. Queued
                // records may still fail later; this is not Written/client ACK.
                if(queued&&source_live&&!source_live->load()){pending->settle(false);state.fail("Qualified world push source retired after insertion");return;}
                pending->settle(queued);
                if(queued&&!state.writes.empty()&&state.writes.front().bytes==bytes&&!state.close_requested.load())state.write();
            }catch(...){pending->settle(false);state.fail("Qualified world push handoff failed");}
        });
    }catch(...){
        if(observed_world_callback==this&&impl_->reply_push_capture)impl_->fail_reply_pushes();
        pending->invalid.store(true);pending->settle(false);
    }
}

void Session::send_world_records_with_acceptance(std::vector<std::uint8_t> logical,
    std::uint64_t expected_account,std::uint64_t expected_character,std::uint64_t expected_world_generation,std::uint64_t expected_battle_generation,std::function<void(bool)> acceptance) {
    if(qualified_world_push_profile){
        (void)retire_battle_self_view_logical_output(logical);[[maybe_unused]] const auto status_admission=begin_actor_status_writer();invalidate_actor_status_writes();
        try{impl_->reject_qualified_profile_sender();}catch(...){if(acceptance){auto once=std::move(acceptance);try{once(false);}catch(...){}}throw;}
    }
    if(impl_->native_logout_terminal.load()){
        if(acceptance){auto once=std::move(acceptance);try{once(false);}catch(...){}}return;
    }
    if(observed_world_callback==this&&impl_->reply_push_capture){
        (void)retire_battle_self_view_logical_output(logical);
        [[maybe_unused]] const auto status_admission=begin_actor_status_writer();invalidate_actor_status_writes();
        const WorldDeliveryIdentity expected{expected_account,expected_character,expected_world_generation,expected_battle_generation};
        impl_->capture_reply_push(logical,std::move(acceptance),&expected);return;
    }
    const auto component=impl_->observe_callback_push(WorldCallbackOutput::Kind::AcceptedWorldRecords,logical);
    (void)retire_battle_self_view_logical_output(logical);
    [[maybe_unused]] const auto status_admission=begin_actor_status_writer();
    invalidate_actor_status_writes();
    auto complete=[callback=std::move(acceptance)](bool enqueued) mutable {if(callback){auto once=std::move(callback);try{once(enqueued);}catch(...){}}};
    if(impl_->close_requested.load()) {complete(false);return;}
    if(logical.empty() || logical.size()>RecoveredWorldFrame::max_logical_size) {complete(false);close();return; }
    const auto charge=logical.size()+3;
    auto budget=impl_->budget;
    std::shared_ptr<Reservation> reservation;
    {
        std::lock_guard lock(budget->mutex);
        if(charge<=max_buffer-budget->bytes && budget->count<max_writes) {
            reservation=std::make_shared<Reservation>(budget,charge);
            budget->bytes+=charge;
            ++budget->count;
        }
    }
    if(!reservation) {complete(false);close();return; }
    impl_->post_status_work(impl_->strand,[self=shared_from_this(),logical=std::move(logical),reservation,expected_account,expected_character,expected_world_generation,expected_battle_generation,complete=std::move(complete),component]() mutable {
        auto& s=*self->impl_;
                [[maybe_unused]] const auto status_admission=self->begin_actor_status_writer();
        if(s.closing || s.close_requested.load() || s.native_logout_terminal.load()) {complete(false);return;}
        const auto delivery=s.world_delivery_identity.load();
        if(!is_recovered(s.mode) || s.c2s0002_state!=Impl::C2S0002State::WorldTailAccepted || !delivery ||
           delivery->account!=expected_account || delivery->character!=expected_character ||
           delivery->world_generation!=expected_world_generation || delivery->battle_generation!=expected_battle_generation ||
           self->battle_generation()!=expected_battle_generation) {
            complete(false);return;
        }
        try {
            auto bytes=std::make_shared<std::vector<std::uint8_t>>(RecoveredWorldFrame::encode(logical));
            if(bytes->size()>max_buffer-s.write_bytes || s.writes.size()>=max_writes) {
                complete(false);s.fail("Recovered world push queue limit");return;
            }
            if(!s.terminal_write_allowed()){complete(false);return;}
            s.write_bytes+=bytes->size();
            Impl::Write output{bytes,std::move(reservation)};
            if(component){component->frame=bytes;component->receipt->wire.store(bytes);output.callback_component=component;}
            s.append_write(std::move(output));
            complete(true);
            if(s.writes.size()==1) s.write();
        } catch(...) {complete(false);s.fail("Recovered world push encoding failed"); }
    });
}
void Session::close() {
    retire_actor_status_incarnation();
    [[maybe_unused]] const auto status_admission=begin_actor_status_writer();
    invalidate_actor_status_writes();
    if(const auto pair=impl_->native_pk_return.load())fail_native_pk_return_reservation(pair);
    impl_->retire_normal_output(); // Synchronized retirement before close publication/post.
    if (impl_->close_requested.exchange(true)) return;
    impl_->post_status_work(impl_->strand, [self = shared_from_this()] { self->impl_->close(); });
}
void Session::notify_authenticated() {
    if (impl_->close_requested.load() || impl_->auth_requested.exchange(true)) return;
    impl_->post_status_work(impl_->strand, [self = shared_from_this()] {
        auto& s = *self->impl_;
                [[maybe_unused]] const auto status_admission=self->begin_actor_status_writer();
        if (s.closing) return;
        try { s.protocol.on_session_authenticated(*self); }
        catch (const std::exception& e) { s.fail(e.what()); }
        catch (...) { s.fail("authentication hook failed"); }
    });
}
std::shared_ptr<const Session::RecoveredServerSelection> Session::recovered_server_selection() const noexcept {
    return recovered_server_selection_.load();
}
Session::NativeCharacterList Session::recovered_native_character_list() const noexcept {
    return recovered_native_character_list_.load();
}
Session::NativeCharacterList Session::recovered_native_character_list_written() const noexcept {
    return recovered_native_character_list_written_.load();
}
std::shared_ptr<const Session::NativeCharacterSelectionInput> Session::recovered_native_selection_input() const noexcept {
    return recovered_native_selection_input_.load();
}
std::shared_ptr<const Session::NativeAuthenticatedInput> Session::recovered_native_authenticated_input() const noexcept {
    return recovered_native_authenticated_input_.load();
}
std::shared_ptr<const Session::NativeLocalEndpoint> Session::recovered_native_local_endpoint() const noexcept {
    return recovered_native_local_endpoint_.load();
}
SessionState Session::state() const noexcept { return state_.load(); }
void Session::set_state(SessionState state) noexcept {
    auto current = state_.load();
    while(current!=SessionState::Disconnected) {
        if(current!=state) {
            // No old battle occurrence survives a phase boundary, even if a
            // later original response callback completes with the old bytes.
            (void)impl_->battle_self_view_fence.advance();
            (void)impl_->battle_self_view_intents.advance();
            if(const auto view=impl_->battle_self_view_source.exchange({}))view->completion.revoke();
            if(const auto pair=impl_->native_pk_return.load())fail_native_pk_return_reservation(pair);
            impl_->retire_normal_output(); // Before phase/battle mutation, even same final pose.
        }
        if(state_.compare_exchange_weak(current,state))break;
    }
    // Preserve the existing state transition; observe only successful battle
    // boundaries. No callback, packet, authentication or battle behavior change.
    if(current!=SessionState::Disconnected && current!=state &&
       (current==SessionState::InBattle || state==SessionState::InBattle))
        battle_generation_.fetch_add(1);
}
std::uint64_t Session::battle_generation() const noexcept { return battle_generation_.load(); }
std::uint64_t Session::id() const noexcept { return impl_->id; }
std::uint8_t Session::recovered_client_language() const noexcept {
    return recovered_client_language_.load();
}
bool Session::recovered_world_ready() const noexcept { return recovered_world_ready_.load()&&!impl_->native_logout_terminal.load(); }
const std::string& Session::remote_ip() const noexcept { return impl_->ip; }
} // namespace god2
