#include "net/Session.h"
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
#include "game/TaiwanWorldEntryIdentity.h"
#include "protocol/RecoveredTaiwanServerRecords.h"
#include "protocol/RecoveredBattleBootstrap.h"
#include "protocol/RecoveredBattlePlayerAppearance.h"
#include "protocol/RecoveredBattlePlayerGrant.h"
#include "protocol/RecoveredBattleAttackPresentation.h"
#include "protocol/RecoveredBattleVitals.h"
#include "protocol/RecoveredBattleVitalsBatch.h"
#include "protocol/RecoveredTaiwanPkTerminalNotification.h"
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
#include <nlohmann/json.hpp>
#ifdef _WIN32
#include <windows.h>
#endif

namespace god2 {
namespace {
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
thread_local bool* observed_response_poison=nullptr;
thread_local std::atomic<Session::WorldResponseWriteStatus>* observed_response_status=nullptr;
void poison_world_response() noexcept {
    if(observed_response_poison)*observed_response_poison=true;
    if(observed_response_status) {
        auto pending=Session::WorldResponseWriteStatus::Pending;
        observed_response_status->compare_exchange_strong(pending,Session::WorldResponseWriteStatus::Failed);
    }
}
struct WorldRecordsObservationScope {
    bool response_poisoned=false;
    explicit WorldRecordsObservationScope(const Session& session) {
        if(observed_world_callback) {
            poison_world_response();
            throw std::logic_error("World observation callback reentry rejected");
        }
        observed_world_callback=&session;observed_response_poison=&response_poisoned;
        observed_response_status=nullptr;
    }
    ~WorldRecordsObservationScope(){
        observed_response_status=nullptr;observed_response_poison=nullptr;observed_world_callback=nullptr;
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
    Reservation(std::shared_ptr<Budget> budget_, std::size_t bytes_)
        : budget(std::move(budget_)), bytes(bytes_) {}
    ~Reservation() {
        std::lock_guard lock(budget->mutex);
        budget->bytes -= bytes;
        --budget->count;
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
    const std::uint64_t account,character,battle;
    const SessionState phase;
    const std::vector<std::uint8_t> wire;
    std::atomic<WorldResponseWriteStatus> status{WorldResponseWriteStatus::Pending};
    Data(std::weak_ptr<Session> owner,std::uint64_t a,std::uint64_t c,std::uint64_t b,
         SessionState p,std::span<const std::uint8_t> raw)
        :session(std::move(owner)),account(a),character(c),battle(b),phase(p),wire(raw.begin(),raw.end()) {}
};
Session::WorldResponseWriteStatus Session::WorldResponseWrite::status() const noexcept {return data_->status.load();}
const std::vector<std::uint8_t>& Session::WorldResponseWrite::wire() const noexcept {return data_->wire;}

struct Session::NormalWorldInitialization::Entry {
    // The actual select game job constructs Entry; tail Data may be on strand.
    const std::thread::id game_thread=std::this_thread::get_id();
    const std::weak_ptr<Session> session;
    const std::uint64_t account,character,battle;
    const RecoveredWorldEntry::Frame frame;
    const std::vector<std::uint8_t> logical;
    std::atomic<bool> written{false},retired{false};
    Entry(std::weak_ptr<Session> owner,std::uint64_t a,std::uint64_t c,std::uint64_t b,
          RecoveredWorldEntry::Frame wire,std::vector<std::uint8_t> bytes)
        :session(std::move(owner)),account(a),character(c),battle(b),frame(std::move(wire)),logical(std::move(bytes)) {}
};
struct Session::NormalWorldInitialization::Data {
    const std::shared_ptr<Entry> entry;
    const std::vector<std::uint8_t> tail;
    const std::uint8_t config;
    // CUSTOM-0132 physical Entry::battle/Written stay the actual original IO.
    const std::uint64_t effective_battle;
    const std::weak_ptr<const Data> previous;
    Data(std::shared_ptr<Entry> source,std::vector<std::uint8_t> bytes,std::uint8_t flag)
        :entry(std::move(source)),tail(std::move(bytes)),config(flag),effective_battle(entry->battle) {}
    Data(std::shared_ptr<const Data> prior,std::uint64_t future)
        :entry(prior->entry),tail(prior->tail),config(prior->config),effective_battle(future),previous(std::move(prior)) {}
};
const RecoveredWorldEntry::Frame& Session::NormalWorldInitialization::entry_frame() const noexcept {return data_->entry->frame;}
const std::vector<std::uint8_t>& Session::NormalWorldInitialization::entry_logical() const noexcept {return data_->entry->logical;}
const std::vector<std::uint8_t>& Session::NormalWorldInitialization::accepted_tail() const noexcept {return data_->tail;}
std::uint8_t Session::NormalWorldInitialization::config_flag() const noexcept {return data_->config;}
bool Session::NormalWorldInitialization::entry_written() const noexcept {
    return data_->entry->written.load() && !data_->entry->retired.load();
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
    enum class Phase {Draining,Ready,Failed};
    const std::weak_ptr<Session> session;
    const std::thread::id thread=std::this_thread::get_id();
    const asio::any_io_executor game;
    const NativePkEntryHold entry;
    const NativeBattleSkill final;
    const std::weak_ptr<NativePkTerminalOwner> source;
    std::atomic<Phase> phase{Phase::Draining};
    std::atomic<bool> accepted{false},ready_notified{false},failed_notified{false},armed{false},acknowledged{false},ack_handoff_failed{false};
    Data(std::weak_ptr<Session> s,asio::any_io_executor executor,NativePkEntryHold hold,
         NativeBattleSkill output,std::weak_ptr<NativePkTerminalOwner> owner)
        :session(std::move(s)),game(std::move(executor)),entry(std::move(hold)),
         final(std::move(output)),source(std::move(owner)){}
};

struct Session::NativePkReturnPreparation::Data {
    const NativePkTerminalBarrier terminal;
    const NormalWorldInitialization initialization;
    const std::shared_ptr<const WorldDeliveryIdentity> world_identity;
    Data(NativePkTerminalBarrier barrier,NormalWorldInitialization normal,
         std::shared_ptr<const WorldDeliveryIdentity> world)
        :terminal(std::move(barrier)),initialization(std::move(normal)),world_identity(std::move(world)) {}
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

struct Session::Impl {
    // This marker is DISTINCT from the Data retained by Application. Its last
    // post/Write owner retiring an uncompleted attempt marks Failed even while
    // the game still retains the private handle. Pure data only, on any thread.
    struct WorldWriteAttempt {
        std::shared_ptr<WorldRecordsWrite::Data> receipt;
        std::shared_ptr<std::vector<std::uint8_t>> frame;
        explicit WorldWriteAttempt(std::shared_ptr<WorldRecordsWrite::Data> value):receipt(std::move(value)) {}
        ~WorldWriteAttempt() {
            auto pending=WorldRecordsWriteStatus::Pending;
            receipt->status.compare_exchange_strong(pending,WorldRecordsWriteStatus::Failed);
        }
    };
    // Captured on game; only immutable bytes/weak Session/atomic status cross
    // to strand. Attempt retirement closes Pending even if Main keeps Data.
    struct WorldResponseAttempt {
        std::shared_ptr<WorldResponseWrite::Data> receipt;
        std::shared_ptr<std::vector<std::uint8_t>> frame;
        explicit WorldResponseAttempt(std::shared_ptr<WorldResponseWrite::Data> value):receipt(std::move(value)) {}
        void fail() noexcept {
            auto pending=WorldResponseWriteStatus::Pending;
            receipt->status.compare_exchange_strong(pending,WorldResponseWriteStatus::Failed);
        }
        ~WorldResponseAttempt(){fail();}
    };
    std::shared_ptr<WorldResponseAttempt> world_response_callback_capture; // Serial game callback ONLY.
    struct NormalOutputPending {
        const std::shared_ptr<NormalWorldOutputAttempt::Data> data;
        explicit NormalOutputPending(std::shared_ptr<NormalWorldOutputAttempt::Data> value):data(std::move(value)) {}
        ~NormalOutputPending() {
            auto pending=NormalWorldOutputStatus::Pending;
            data->status.compare_exchange_strong(pending,NormalWorldOutputStatus::Failed);
        }
    };
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
    const std::shared_ptr<NormalWorldOutputHandle::Sync> normal_output_sync=
        std::make_shared<NormalWorldOutputHandle::Sync>();
    void retire_normal_output() noexcept {
        std::lock_guard lock(normal_output_sync->mutex);
        const auto old=normal_output_sync->epoch.load();
        if(old!=std::numeric_limits<std::uint64_t>::max())normal_output_sync->epoch.store(old+1);
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
    RecoveredLoginHandler recovered_login;
    RecoveredCharacterHandlers character_handlers;
    bool common_world_lifecycle_factory_invoked=false; // Serial game executor only.
    std::function<void()> common_world_cleanup; // Serial game executor only.
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
        std::shared_ptr<WorldResponseAttempt> observed_response{}; // LAST: preserve every old aggregate initializer.
    };
    std::deque<Write> writes;
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
    bool native_battle_read_paused=false; // Network strand only; separate hold.
    bool native_pk_read_paused=false;
    asio::cancellation_signal native_pk_read_cancel;
    bool native_pk_cancel_read=false; // Strand; acknowledgement precedes Held.
    bool native_pk_terminal_cancel_read=false;
    bool read_inflight=false; // Passive read ownership; avoids duplicate resume.
    bool resume_after_login_write = false;

    Impl(Session& owner_, asio::ip::tcp::socket socket_, asio::any_io_executor game_,
         std::uint64_t id_, bool dump_, PacketHandler packet_, DisconnectHandler disconnect_,ProtocolMode mode_,
         RecoveredLoginHandler login_,RecoveredCharacterHandlers characters_,std::vector<std::uint8_t> routes_)
        : owner(owner_), socket(std::move(socket_)), strand(asio::make_strand(socket.get_executor())),
          game(std::move(game_)), timer(strand), hold_timer(strand), native_pk_timer(strand), native_pk_terminal_timer(strand), game_work(asio::make_work_guard(game)),
          network_work(asio::make_work_guard(socket.get_executor())),
          id(id_), packet_dump(dump_), mode(mode_), on_packet(std::move(packet_)),
          on_disconnect(std::move(disconnect_)), recovered_login(std::move(login_)),character_handlers(std::move(characters_)),character_routes(std::move(routes_)) {
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
        if(character_handlers.movement && character_handlers.world_records)
            throw std::invalid_argument("Recovered world handlers are mutually exclusive");
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
                write_bytes+=bytes->size();writes.push_back({bytes,{}});write();
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
        try {asio::post(game,[self=owner.shared_from_this(),pending,written] {
            auto& s=*self->impl_;bool accepted=false;
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
            try {asio::post(s.strand,[self,pending,accepted] {
                auto& s=*self->impl_;
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
        try {asio::post(game,[self=owner.shared_from_this(),pending,bytes] {
            auto& s=*self->impl_;bool accepted=false;
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
            try {asio::post(s.strand,[self,pending,bytes,accepted] {
                auto& s=*self->impl_;
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
        try {asio::post(game,[self=owner.shared_from_this(),data,written] {
            auto& s=*self->impl_;bool accepted=false;
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
            try {asio::post(s.strand,[self,data,written,accepted] {
                auto& s=*self->impl_;
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
    void retire_native_pk_terminal() {
        const auto data=native_pk_terminal.exchange({});if(!data)return;
        // Only this exact returned game callback may retire its busy latch.
        if(data->ack_handoff_failed.load())game_busy=false;
        data->accepted.store(false);data->phase.store(NativePkTerminalBarrier::Data::Phase::Failed);
        native_pk_terminal_timer.cancel();
        // Only game owns the strong callback reference and its destruction.
        try {asio::post(game,[self=owner.shared_from_this(),data] {
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
        try {asio::post(game,[self=owner.shared_from_this(),data] {
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
            writes.push_back(std::move(held));write_bytes+=data->frame->size();
            auto preparing=NativePkEntryHold::Data::Phase::Preparing;
            if(!data->phase.compare_exchange_strong(preparing,NativePkEntryHold::Data::Phase::Held)) {
                write_bytes-=data->frame->size();writes.pop_back();return;
            }
            asio::post(game,[self=owner.shared_from_this(),data] {
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
            writes.push_back({bytes,std::move(native_pk_output_reservation),false,true,{},{},pending});
            write_bytes+=bytes->size();native_pk_output_staged.reset();
            release_native_battle(pending,bytes);
        }catch(...){fail("Native PK output staged encoding or handoff failed");}
    }
    void read() {
        if(native_pk_terminal.load()) {stage_native_pk_terminal();return;}
        if(native_pk_pending.load()) {native_pk_read_paused=true;stage_native_pk();return;}
        if(native_battle_pending.load()) {native_battle_read_paused=true;stage_native_pk_output();return;}
        if (closing || game_busy) return;
        native_battle_read_paused=false;
        read_inflight=true;
        socket.async_read_some(asio::buffer(read_bytes), asio::bind_cancellation_slot(native_pk_read_cancel.slot(),asio::bind_executor(strand,
            [self = owner.shared_from_this()](const asio::error_code& ec, std::size_t size) {
                auto& s = *self->impl_;
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
                                    s.write_bytes+=bytes->size();s.writes.push_back({bytes,{}});
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
                                            s.write_bytes+=reply->size();s.writes.push_back({reply,{}});
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
                                    s.write_bytes+=bytes->size();s.writes.push_back({bytes,{}});
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
                                s.write_bytes+=bytes->size();s.writes.push_back({bytes,{}});
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
        write_bytes+=bytes->size();writes.push_back({bytes,{}});
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
            write_bytes+=next->size();writes.push_back({next,{},false,false,std::move(observation)});
        }
        if(is_terminal_mode(mode)) {
            const auto terminal=RecoveredLoginTerminal::success();
            auto next=std::make_shared<std::vector<std::uint8_t>>(terminal.begin(),terminal.end());
            if(!terminal_write_allowed())return;
            write_bytes+=next->size();writes.push_back({next,{}});
        }
        if(writes.front().bytes==bytes) write();
    }
    void authenticate_recovered(RecoveredC2S0002::Parsed request,std::vector<std::uint8_t> response) {
        game_busy=true;
        // Suspend reads until the game-owned account repository has completed.
        // The same acknowledgement discipline as deliver() gates disconnect.
        asio::post(game,[self=owner.shared_from_this(),request=std::move(request),response]() mutable {
            auto& s=*self->impl_;
            auto complete=[self,response,request](std::uint64_t account,std::exception_ptr error) {
                auto& s=*self->impl_;
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
                asio::post(s.strand,[self,account,response,error] {
                auto& s=*self->impl_;
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
                    s.write_bytes+=bytes->size();s.writes.push_back({bytes,{}});
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
            };
            try {
                if(s.close_requested.load()) complete(0,{});
                else if(s.character_handlers.authenticate_async)
                    s.character_handlers.authenticate_async(request,complete);
                else complete(s.recovered_login(request),{});
            } catch(...) { complete(0,std::current_exception()); }
        });
    }
    void character_operation(std::optional<RecoveredCharacterCreate> request=std::nullopt,
                             std::optional<RecoveredPostServerSelect> selection=std::nullopt,
                             std::shared_ptr<const Session::RecoveredServerAdvertisement> advertisement={}) {
        game_busy=true;
        asio::post(game,[self=owner.shared_from_this(),request,selection,advertisement=std::move(advertisement)] {
            auto& s=*self->impl_;
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
            asio::post(s.strand,[self,succeeded,created_id,delivery=std::move(delivery),response=std::move(response)]() mutable {
                auto& s=*self->impl_;
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
                        s.writes.push_back({bytes,{},false,true,{},delivery});s.write_bytes+=bytes->size();
                    } else { if(!s.terminal_write_allowed())return; s.write_bytes+=bytes->size();s.writes.push_back({bytes,{}});}
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
        asio::post(game,[self=owner.shared_from_this(),delivery,bytes] {
            auto& s=*self->impl_;bool accepted=false;
            try {accepted=!s.close_requested.load() && s.character_handlers.native_list_current(*self,delivery);}
            catch(...) {}
            asio::post(s.strand,[self,delivery,bytes,accepted] {
                auto& s=*self->impl_;
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
        asio::post(game,[self=owner.shared_from_this(),delivery,written] {
            auto& s=*self->impl_;bool accepted=false;
            try {
                accepted=s.character_handlers.native_list_complete(*self,delivery,written);
                accepted=accepted && written && !self->closing() && self->account_id==delivery->account &&
                    self->id()==delivery->session && self->recovered_server_selection()==delivery->selection;
                if(accepted)self->recovered_native_character_list_.store(delivery);
            }catch(...) {accepted=false;}
            asio::post(s.strand,[self,accepted] {
                auto& s=*self->impl_;s.game_busy=false;
                if(s.closing) {s.finish();return;}
                if(!accepted || s.close_requested.load()) {s.fail("Native list delivery source completion rejected");return;}
                s.arm_timer(idle_timeout);s.read();
            });
        });
    }
    void delete_character(RecoveredCharacterDelete request) {
        game_busy=true;
        asio::post(game,[self=owner.shared_from_this(),request] {
            auto& s=*self->impl_;
            bool accepted=false;
            try {
                if(!s.close_requested.load() && self->account_id && !self->character_id &&
                   s.character_handlers.delete_character)
                    accepted=s.character_handlers.delete_character(*self,request);
            } catch(const std::exception& error) {
                logger("session")->warn("session_id={} CHARACTER_DELETE_REJECTED reason={}",s.id,error.what());
            } catch(...) {}
            asio::post(s.strand,[self,accepted] {
                auto& s=*self->impl_;s.game_busy=false;
                if(s.closing) { s.finish();return; }
                if(s.close_requested.load()) { s.close();return; }
                auto bytes=std::make_shared<std::vector<std::uint8_t>>(
                    RecoveredCharacterDelete::response(accepted));
                if(!s.terminal_write_allowed())return;
                s.write_bytes+=bytes->size();s.writes.push_back({bytes,{}});
                logger("session")->info("session_id={} CHARACTER_DELETE_RESULT accepted={}",s.id,accepted);
                if(s.writes.size()==1)s.write();
                s.arm_timer(idle_timeout);s.read();
            });
        });
    }
    void acknowledge_created_slot() {
        game_busy=true;
        asio::post(game,[self=owner.shared_from_this()] {
            auto& s=*self->impl_;
            std::optional<std::uint8_t> slot;
            try {
                if(!s.close_requested.load())
                    slot=s.character_handlers.created_slot(self->account_id,s.pending_created_character);
            } catch(...) {}
            asio::post(s.strand,[self,slot] {
                auto& s=*self->impl_;
                s.game_busy=false;
                if(s.closing) { s.finish();return; }
                if(s.close_requested.load()) { s.close();return; }
                if(!slot || *slot>=2) { s.fail("Native creation slot ownership rejected");return; }
                try {
                    // 15210 reads byte1; byte2 is unread here, zero candidate only.
                    auto bytes=std::make_shared<std::vector<std::uint8_t>>(
                        RecoveredWorldFrame::encode(std::array<std::uint8_t,3>{0x18,*slot,0}));
                    if(!s.terminal_write_allowed())return;
                    s.write_bytes+=bytes->size();s.writes.push_back({bytes,{}});
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
        asio::post(game,[self=owner.shared_from_this(),token,created,native_input=std::move(native_input)] {
            auto& s=*self->impl_;
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
                            entry_account,selected,entry_battle,*world_frame,std::move(*logical));
                }
            } catch(...) {}
            asio::post(s.strand,[self,selected,created,world_frame,prepared_actor,normal_entry=std::move(normal_entry)] {
                auto& s=*self->impl_;
                s.game_busy=false;
                if(s.closing) { s.finish();return; }
                if(s.close_requested.load()) { s.close();return; }
                if(!selected) { s.fail("Character selection ownership rejected");return; }
                try {
                    // Current 14D20 accepts the same 02/result-WORD-zero shape.
                    const auto frame=RecoveredCharacterCreateResult::committed_success();
                    auto bytes=std::make_shared<std::vector<std::uint8_t>>(frame.begin(),frame.end());
                    if(!s.terminal_write_allowed())return;
                    s.write_bytes+=bytes->size();s.writes.push_back({bytes,{}});
                    s.retire_normal_output(); // Before replacement, not after new identity publication.
                    if(const auto old=s.normal_entry.exchange(normal_entry))old->retired.store(true);
                    s.normal_initialization.store({});
                    s.normal_tail_size=0;s.normal_tail_observable=true;
                    if(world_frame) {
                        auto next=std::make_shared<std::vector<std::uint8_t>>(world_frame->begin(),world_frame->end());
                        if(!s.terminal_write_allowed())return;
                        s.write_bytes+=next->size();s.writes.push_back({next,{},true});
                        s.writes.back().normal_entry=normal_entry;
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
        asio::post(game,[self=owner.shared_from_this(),entry,tail,tail_size,observable,config] {
            auto& s=*self->impl_;
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
                    initialization=std::make_shared<const NormalWorldInitialization::Data>(entry,
                        std::vector<std::uint8_t>(tail.begin(),tail.begin()+tail_size),config);
            } catch(...) {}
            asio::post(s.strand,[self,accepted,initialization=std::move(initialization)] {
                auto& s=*self->impl_;
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
                        asio::post(s.game,[self] {
                            auto& s=*self->impl_;bool common_accepted=false;
                            if(s.character_handlers.common_world_lifecycle->ready_async) {
                                s.begin_common_ready_async(self);return;
                            }
                            try {
                                if(!s.close_requested.load())
                                    common_accepted=s.character_handlers.common_world_lifecycle->ready(*self);
                            }catch(...) {}
                            asio::post(s.strand,[self,common_accepted] {
                                auto& s=*self->impl_;s.game_busy=false;
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
            asio::post(strand,[self] {auto& s=*self->impl_;s.game_busy=false;s.fail("Common world async readiness already pending or exhausted");});
            return;
        }
        const auto nonce=++common_ready_nonce;
        common_ready_completion=[self](bool accepted) {
            asio::post(self->impl_->strand,[self,accepted] {
                auto& s=*self->impl_;s.game_busy=false;
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
        auto done=[weak=std::weak_ptr<Session>(self),nonce,thread=common_ready_thread](bool accepted) {
            if(thread!=std::this_thread::get_id())throw std::logic_error("Common world readiness completion game owner mismatch");
            if(const auto current=weak.lock())current->impl_->finish_common_ready(nonce,accepted);
        };
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
        asio::post(game,[self=owner.shared_from_this()] {
            auto& s=*self->impl_;const auto nonce=s.common_ready_nonce;
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
    void resume_world_input(bool awaiting_skill=false) {
        if(native_pk_terminal.load()) {stage_native_pk_terminal();return;}
        if(native_pk_pending.load()) {native_pk_read_paused=true;stage_native_pk();return;}
        if(native_battle_pending.load()) {native_battle_read_paused=true;stage_native_pk_output();return;}
        if(world_input.size()>=2) {
            const auto length=static_cast<std::size_t>(world_input[0])+256u*world_input[1];
            if(length<5 || length>RecoveredWorldRecords::max_logical_size+3 ||
               world_input.size()>=length) {
                asio::post(strand,[self=owner.shared_from_this()] { self->impl_->feed_world({}); });
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
                auto reply=std::make_shared<std::vector<std::uint8_t>>(
                    RecoveredWorldFrame::encode(std::array<std::uint8_t,3>{3,0,0}));
                if(!terminal_write_allowed())return;
                write_bytes+=reply->size();writes.push_back({reply,{}});
                if(writes.size()==1)write();
                logger("session")->info("session_id={} NATIVE_LOGOUT_ACK_QUEUED reason={}",id,(*control)[1]);
                close();return;
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
                character_handlers.owned_client_options);
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
        asio::post(game,[self=owner.shared_from_this(),records=std::move(records),requests=std::move(requests),native_batch_generation] {
            auto& s=*self->impl_;
            s.native_pk_terminal_callback_capture.reset(); // This exact serial input callback only.
            s.world_response_callback_capture.reset(); // Previous unhanded attempt retires Failed.
            struct ResponseCaptureEnd {
                Impl& state;
                ~ResponseCaptureEnd(){state.world_response_callback_capture.reset();}
            } response_capture_end{s}; // Unhanded attempt fails on every exceptional unwind.
            std::vector<std::uint8_t> response;
            bool accepted=false;
            try {
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
                        WorldRecordsObservationScope observation_scope(*self);
                        Impl::SelectionScope input_scope(s,records);
                        auto result=s.character_handlers.world_records(*self,records);
                        accepted=result.has_value();
                        if(result) response=std::move(*result);
                    } else {
                        response=s.character_handlers.movement(*self,requests);
                        accepted=!response.empty();
                    }
                    accepted=accepted && valid_world_response(response);
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
                if(s.native_pk_terminal_callback_capture || s.world_response_callback_capture)accepted=false;
                logger("session")->warn("Recovered world callback exception session_id={} reason={}",s.id,error.what());
            } catch(...) {
                if(s.native_pk_terminal_callback_capture || s.world_response_callback_capture)accepted=false;
                logger("session")->warn("Recovered world callback exception session_id={} reason=unknown",s.id);
            }
            // The game-owned incarnation survives deadline/close retirement.
            // Only this actual TLS handler could mint it. No later generic ACK
            // can qualify it; rejection/throw never acknowledges acceptance.
            const auto terminal_ack=std::exchange(s.native_pk_terminal_callback_capture,{});
            const auto response_write=std::exchange(s.world_response_callback_capture,{});
            if(response_write && (!accepted || response_write->receipt->wire!=response ||
               response_write->receipt->status.load()!=WorldResponseWriteStatus::Pending)) {
                response_write->fail();accepted=false;
            }
            try {asio::post(s.strand,[self,accepted,terminal_ack,response_write,response=std::move(response),
                                 count=records.size(),movement_count=requests.size()]() mutable {
                auto& s=*self->impl_;
                s.game_busy=false;
                if(s.closing) { s.finish();return; }
                if(s.close_requested.load()) { s.close();return; }
                if(!accepted) { s.fail("Recovered world policy or response rejected");return; }
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
                        if(response_write)response_write->frame=bytes;
                        s.write_bytes+=bytes->size();s.writes.push_back({bytes,{}});
                        s.writes.back().observed_response=response_write;
                        if(s.writes.front().bytes==bytes) s.write();
                    }
                    if(s.character_handlers.world_records)
                        logger("session")->info("session_id={} RECOVERED_WORLD_BATCH_HANDLED records={}; live acceptance UNKNOWN",s.id,count);
                    else
                        logger("session")->info("session_id={} RECOVERED_MOVEMENT_ACCEPTED records={}; live acceptance UNKNOWN",s.id,movement_count);
                    if(terminal_ack && s.native_pk_terminal.load()==terminal_ack)
                        terminal_ack->acknowledged.store(true);
                    s.resume_world_input();
                } catch(...) { s.fail("Recovered world response failed"); }
            });}catch(...) {
                if(!terminal_ack)throw; // Existing nonterminal handoff semantics.
                // The actual callback returned; this is failure, never its ACK.
                terminal_ack->ack_handoff_failed.store(true);
                terminal_ack->accepted.store(false);
                terminal_ack->phase.store(NativePkTerminalBarrier::Data::Phase::Failed);
                s.close_requested.store(true);
                try {asio::post(s.strand,[self,terminal_ack] {
                    auto& s=*self->impl_;
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
        asio::post(game, [self = owner.shared_from_this(), packets = std::move(packets)]() mutable {
            auto& s = *self->impl_;
            bool failed = false;
            for (auto& packet : packets) {
                try { if (s.on_packet) s.on_packet(self, std::move(packet)); }
                catch (...) { failed = true; }
            }
            asio::post(s.strand, [self, failed] {
                auto& s = *self->impl_;
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
            writes.push_back({std::move(bytes), std::move(reservation)});
            if (writes.size() == 1) write();
        } catch (const std::exception& e) { fail(e.what()); }
        catch (...) { fail("protocol encode failed"); }
    }
    void write() {
        if(writes.empty() || writes.front().held)return;
        auto bytes = writes.front().bytes;
        // The completion owns the active buffer even when fail() clears the queue.
        asio::async_write(socket, asio::buffer(*bytes), asio::bind_executor(strand,
            [self = owner.shared_from_this(), bytes](const asio::error_code& ec, std::size_t transferred) {
                auto& s = *self->impl_;
                if (s.finished || s.writes.empty()) return;
                if (ec) { s.fail(ec.message()); return; }
                if(const auto entry=s.writes.front().normal_entry) {
                    // Strand-owned exact Write; do not read game-owned IDs or
                    // change legacy write/close policy for passive metadata.
                    if(!s.writes.front().held && s.writes.front().world_entry &&
                       s.writes.front().bytes==bytes && transferred==bytes->size() &&
                       bytes->size()==entry->frame.size() && s.normal_entry.load()==entry &&
                       entry->session.lock().get()==self.get() && !entry->retired.load() &&
                       std::equal(bytes->begin(),bytes->end(),entry->frame.begin()))entry->written.store(true);
                    else entry->retired.store(true);
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
                if(is_server_list_mode(s.mode) && (bytes->size()==8 || (!s.character_routes.empty() && bytes->size()==28))) {
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
                s.write_bytes -= s.writes.front().bytes->size();
                s.writes.pop_front();
                if(s.native_pk_terminal.load())s.stage_native_pk_terminal();
                if (!s.writes.empty()) s.write();
                else if (s.closing) s.finish();
                else if(s.resume_after_login_write) {
                    s.resume_after_login_write=false;
                    s.read();
                }
            }));
    }
    void close() {
        if (closing) return;
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
    void finish() {
        if (finished || !closing || game_busy || !writes.empty() || native_battle_pending.load() || native_pk_pending.load() || native_pk_terminal.load()) return;
        finished = true;
        timeout_policy=SessionTimeoutPolicy::Normal;
        hold_timer.cancel();
        native_pk_timer.cancel();
        native_pk_terminal_timer.cancel();
        try { hold_status(); } catch(...) {}
        owner.state_.store(SessionState::Disconnected);
        asio::error_code ignored;
        timer.cancel();
        socket.shutdown(asio::ip::tcp::socket::shutdown_both, ignored);
        socket.close(ignored);
        asio::post(game, [self = owner.shared_from_this()] {
            auto& s = *self->impl_;
            logger("session")->info("session_id={} DISCONNECT_GAME_ENTER",s.id);
            try {if(auto cleanup=std::exchange(s.common_world_cleanup,{}))cleanup();}
            catch(...) {
                if(auto log=logger("session"))log->error("session_id={} common world cleanup failed",s.id);
            }
            try {if(s.character_handlers.common_world_lifecycle_abandon)s.character_handlers.common_world_lifecycle_abandon(*self);}
            catch(...) {
                if(auto log=logger("session"))log->error("session_id={} common world lifecycle abandon failed",s.id);
            }
            try { if (s.on_disconnect) s.on_disconnect(self); }
            catch (...) {
                if (auto log = logger("session")) log->error("session_id={} disconnect callback failed", s.id);
            }
            s.game_work.reset();
            s.network_work.reset();
            logger("session")->info("session_id={} DISCONNECT_GAME_EXIT",s.id);
        });
    }
};

Session::Session(asio::ip::tcp::socket socket, asio::any_io_executor game_executor,
                 std::uint64_t id, bool packet_dump, PacketHandler on_packet,
                 DisconnectHandler on_disconnect,ProtocolMode mode,RecoveredLoginHandler recovered_login,RecoveredCharacterHandlers characters,
                 std::vector<std::uint8_t> character_routes)
    : impl_(std::make_unique<Impl>(*this, std::move(socket), std::move(game_executor), id,
                                  packet_dump, std::move(on_packet), std::move(on_disconnect),mode,std::move(recovered_login),std::move(characters),std::move(character_routes))) {
    // Constructor body: all Session atomics now exist. This passive observation
    // never changes legacy/authentication/socket acceptance on lookup failure.
    if(impl_->character_handlers.native_select && mode==ProtocolMode::God2CharacterConnection) {
        try {
            asio::error_code ec;
            const auto local=impl_->socket.local_endpoint(ec);
            if(!ec && local.address().is_v4() && local.port())
                recovered_native_local_endpoint_.store(std::make_shared<const NativeLocalEndpoint>(
                    NativeLocalEndpoint{id,mode,local.address().to_v4().to_bytes(),local.port()}));
        } catch(...) {}
    }
}
Session::~Session() = default;
void Session::start() {
    asio::dispatch(impl_->strand, [self = shared_from_this()] { self->impl_->start(); });
}
void Session::send(Packet packet) {
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
    asio::post(impl_->strand, [self = shared_from_this(), packet = std::move(packet), reservation]() mutable {
        self->impl_->enqueue(std::move(packet), std::move(reservation));
    });
}
void Session::send_world_records(std::vector<std::uint8_t> logical) {
    send_world_records_impl(std::move(logical),{});
}
Session::WorldRecordsWrite Session::send_world_records_observed(std::vector<std::uint8_t> logical) {
    if(observed_world_callback!=this)
        throw std::logic_error("Observed world sender requires actual world-records game callback");
    if(impl_->mode!=ProtocolMode::God2CharacterConnection || closing() || !recovered_world_ready() ||
       (state()!=SessionState::CharacterSelected && state()!=SessionState::InWorld) || !account_id || !character_id ||
       logical.empty() || logical.size()>RecoveredWorldFrame::max_logical_size)
        throw std::invalid_argument("Observed world sender requires exact ready world owner and complete batch");
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
        battle_generation(),state(),wire);
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
std::optional<Session::NormalWorldInitialization> Session::normal_world_initialization() const {
    if(observed_world_callback!=this)
        throw std::logic_error("Normal initialization requires actual world-records game callback");
    const auto data=impl_->normal_initialization.load();
    if(!data)return std::nullopt;
    const NormalWorldInitialization result(data);
    if(!normal_world_initialization_current(result))return std::nullopt;
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
    asio::post(impl_->strand,[self=shared_from_this(),recipient,logical=std::move(logical),reservation,pending]() mutable {
        auto& s=*self->impl_;
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
                s.writes.push_back({bytes,std::move(reservation)});
                s.write_bytes+=bytes->size();
                auto expected=NormalWorldOutputStatus::Pending;
                pending->data->status.compare_exchange_strong(expected,NormalWorldOutputStatus::Queued);
            }
            if(s.writes.size()==1)s.write();
        }catch(...) {s.fail("Normal world output encoding or handoff failed");}
    });
    return result;
}
void Session::send_world_records_impl(std::vector<std::uint8_t> logical,
        std::shared_ptr<WorldRecordsWrite::Data> observed) {
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
    asio::post(impl_->strand,[self=shared_from_this(),logical=std::move(logical),reservation,attempt]() mutable {
        auto& s=*self->impl_;
        if(s.closing || s.close_requested.load()) return;
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
            s.writes.push_back({std::move(bytes),std::move(reservation),false,false,{},{},{},attempt});
            if(s.writes.size()==1) s.write();
        } catch(...) { s.fail("Recovered world push encoding failed"); }
    });
}
void Session::bind_world_delivery_identity(WorldDeliveryIdentity identity) {
    if(!identity.account || !identity.character || !identity.world_generation)
        throw std::invalid_argument("Complete owned world delivery identity required");
    impl_->world_delivery_identity.store(std::make_shared<const WorldDeliveryIdentity>(identity));
}
bool Session::install_common_world_cleanup(std::function<void()> cleanup) {
    if(!cleanup || closing() || impl_->mode!=ProtocolMode::God2CharacterConnection ||
       !impl_->character_handlers.common_world_lifecycle || impl_->common_world_cleanup)return false;
    if(const auto& own=impl_->character_handlers.common_world_cleanup_owner; own) {
        try {cleanup=own(*this,std::move(cleanup));}catch(...) {return false;}
        if(!cleanup)return false;
    }
    impl_->common_world_cleanup=std::move(cleanup);return true;
}
bool Session::closing() const noexcept {return impl_->close_requested.load();}
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
    std::function<bool()> publish,std::function<void(bool)> queued) {
    if(impl_->common_ready_thread!=std::this_thread::get_id())
        throw std::logic_error("Pending common publication game owner mismatch");
    if(!queued)throw std::invalid_argument("Pending common entry completion required");
    const auto pending=impl_->common_entry_identity.load();
    if(!publish || !pending || !common_world_entry_current(account,character,generation) ||
       account_id!=account || character_id!=character || logical.empty() ||
       logical.size()>RecoveredWorldFrame::max_logical_size || !impl_->character_handlers.common_world_publication_owner) {
        try {queued(false);}catch(...) {}close();return;
    }
    // Only this explicit native entry path uses the pinned TW S2C grammar.
    // Qualify the whole unchanged aggregate before owning publication, charging
    // transport capacity or encoding. Lengths do not grant phase/gameplay rights.
    bool complete_native_records=false;
    try {complete_native_records=bool(RecoveredTaiwanServerRecords::read(logical));}
    catch(...) {}
    if(!complete_native_records) {
        try {queued(false);}catch(...) {}close();return;
    }
    CommonWorldPublication owned;
    try {owned=impl_->character_handlers.common_world_publication_owner(*this,{std::move(publish),std::move(queued)});}
    catch(...) {close();return;}
    if(!owned.publish || !owned.queued){close();return;}
    // Both functions are revocable facades. Their actual captures stay on game
    // in the lifecycle owner, including cancellation and startup unwind.
    const auto finish=[self=shared_from_this(),queued=std::move(owned.queued)](bool accepted) {
        asio::post(self->impl_->game,[queued,accepted] {try {queued(accepted);}catch(...) {}});
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
    if(!before()){close();finish(false);return;}
    const auto charge=logical.size()+3;auto budget=impl_->budget;std::shared_ptr<Reservation> reservation;
    try {
        std::lock_guard lock(budget->mutex);
        if(charge<=max_buffer-budget->bytes && budget->count<max_writes) {
            reservation=std::make_shared<Reservation>(budget,charge);budget->bytes+=charge;++budget->count;
        }
    }catch(...) {close();finish(false);return;}
    if(!reservation){close();finish(false);return;}
    asio::post(impl_->strand,[self=shared_from_this(),logical=std::move(logical),reservation,before,after,
        account,character,publish=std::move(owned.publish),finish]() mutable {
        auto& s=*self->impl_;
        if(s.closing || !before() || s.mode!=ProtocolMode::God2CharacterConnection ||
           s.c2s0002_state!=Impl::C2S0002State::WorldTailAccepted) {
            s.fail("Stale pending common entry publication");finish(false);return;
        }
        try {
            auto bytes=std::make_shared<std::vector<std::uint8_t>>(RecoveredWorldFrame::encode(logical));
            if(bytes->size()>max_buffer-s.write_bytes || s.writes.size()>=max_writes) {
                s.fail("Pending common entry queue limit");finish(false);return;
            }
            if(!s.terminal_write_allowed()){finish(false);return;}
            s.writes.push_back({bytes,std::move(reservation),false,true});s.write_bytes+=bytes->size();
            asio::post(s.game,[self,bytes,before,after,account,character,publish=std::move(publish),finish] {
                bool accepted=false;
                try {accepted=before() && self->account_id==account && self->character_id==character &&
                    publish() && after() && self->account_id==account && self->character_id==character;}catch(...) {}
                asio::post(self->impl_->strand,[self,bytes,after,accepted,finish] {
                    auto& s=*self->impl_;
                    if(!accepted || s.closing || !after() || s.c2s0002_state!=Impl::C2S0002State::WorldTailAccepted) {
                        s.fail("Pending common entry publication refused");finish(false);return;
                    }
                    const auto held=std::find_if(s.writes.begin(),s.writes.end(),[&](const auto& entry){return entry.bytes==bytes;});
                    if(held==s.writes.end() || !held->held){s.fail("Pending common entry held frame missing");finish(false);return;}
                    held->held=false;if(held==s.writes.begin())s.write();
                    finish(true); // Queue released, never a client/native ACK.
                });
            });
        }catch(...) {s.fail("Pending common entry encoding failed");finish(false);}
    });
}
void Session::send_common_world_records_with_publication(std::vector<std::uint8_t> logical,
    std::uint64_t account,std::uint64_t character,std::uint64_t generation,
    std::function<bool()> publish,std::function<void(bool)> queued) {
    if(!queued)throw std::invalid_argument("Common world publication completion required");
    auto completion=std::make_shared<std::function<void(bool)>>(std::move(queued));
    const auto finish=[self=shared_from_this(),completion](bool accepted) {
        asio::post(self->impl_->game,[completion,accepted] {
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
    asio::post(impl_->strand,[self=shared_from_this(),logical=std::move(logical),reservation,
        account,character,common,publish=std::move(publish),finish]() mutable {
        auto& s=*self->impl_;
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
            s.writes.push_back({bytes,std::move(reservation),false,true});s.write_bytes+=bytes->size();
            asio::post(s.game,[self,bytes,account,character,common,publish=std::move(publish),finish]() mutable {
                bool accepted=false;
                try {
                    accepted=common() && self->account_id==account && self->character_id==character &&
                        publish() && common() && self->account_id==account && self->character_id==character;
                }catch(...) {}
                asio::post(self->impl_->strand,[self,bytes,common,accepted,finish] {
                    auto& s=*self->impl_;
                    if(!accepted || s.closing || !common() || s.c2s0002_state!=Impl::C2S0002State::WorldTailAccepted) {
                        s.fail("Common world publication refused");finish(false);return;
                    }
                    const auto held=std::find_if(s.writes.begin(),s.writes.end(),[&](const auto& entry){return entry.bytes==bytes;});
                    if(held==s.writes.end() || !held->held) {
                        s.fail("Common world held frame missing");finish(false);return;
                    }
                    held->held=false;
                    if(held==s.writes.begin())s.write();
                    finish(true); // Published before IO release; local queue only.
                });
            });
        }catch(...) {s.fail("Common world publication encoding failed");finish(false);}
    });
}
void Session::send_native_battle_skill_publication(NativeBattleSkill delivery,
    std::weak_ptr<NativeBattleSkillPublicationOwner> source) {
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
        asio::post(impl_->strand,[self,pending,reservation=std::move(reservation)]() mutable {
            auto& s=*self->impl_;
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
                s.writes.push_back({bytes,std::move(reservation),false,true,{},{},pending});
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
    const auto common=impl_->common_world_identity.load();
    const auto data=impl_->normal_initialization.load();
    if(!common || !data || impl_->common_ready_thread!=std::this_thread::get_id() ||
       impl_->common_ready_thread==std::thread::id{})
        throw std::logic_error("Native PK entry requires the actual async common game owner");
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
    if(!own || !other || own->position()!=0 || other->position()!=14 ||
       !own->displayed_level() || !other->displayed_level() ||
       (own->variant()&0x6000)!=0x2000 || (other->variant()&0x6000)!=0x2000 ||
       own->identity_word()!=request.character || !other->identity_word() ||
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
    try {asio::post(impl_->strand,[self=shared_from_this(),pending,reservation=std::move(reservation)]()mutable {
        auto& s=*self->impl_;
        if(s.native_pk_pending.load()!=pending || pending->completing.load())return;
        try {
            s.native_pk_read_paused=true;s.native_pk_reservation=std::move(reservation);
            s.native_pk_timer.expires_after(close_timeout);
            s.native_pk_timer.async_wait([self,pending](const asio::error_code& ec) {
                auto& s=*self->impl_;
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
        const NativePkEntryHold& hold,NativeBattleSkill final,std::weak_ptr<NativePkTerminalOwner> source) {
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
    auto data=std::make_shared<NativePkTerminalBarrier::Data>(shared_from_this(),impl_->game,
        hold,std::move(final),std::move(source));
    std::shared_ptr<NativePkTerminalBarrier::Data> absent;
    if(!impl_->native_pk_terminal.compare_exchange_strong(absent,data))
        throw std::logic_error("Native PK terminal barrier already pending");
    impl_->native_pk_terminal_callback_capture=data;
    try {asio::post(impl_->strand,[self=shared_from_this(),data] {
        auto& s=*self->impl_;if(s.native_pk_terminal.load()!=data)return;
        try {
            s.native_pk_terminal_timer.expires_after(close_timeout);
            s.native_pk_terminal_timer.async_wait([self,data](const asio::error_code& ec) {
                if(!ec && self->impl_->native_pk_terminal.load()==data) {
                    if(data->ack_handoff_failed.load())self->impl_->game_busy=false;
                    self->impl_->fail("Native PK terminal barrier deadline expired; retained recovery required");
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
    auto normal=std::make_shared<const NormalWorldInitialization::Data>(entry->initialization.data_,future);
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
        future->effective_battle==request.prebattle_generation+2 &&
        data->world_identity->account==original->account && data->world_identity->character==original->character &&
        data->world_identity->world_generation==original->world_generation &&
        data->world_identity->battle_generation==future->effective_battle;
}
void Session::send_native_pk_output(const NativePkEntryHold& hold,NativeBattleSkill delivery,
        std::weak_ptr<NativeBattleSkillPublicationOwner> source){
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
    // CUSTOM-0126 only a canonical final89 after the final88 may use this
    // accepted-entry writer. No arbitrary experience record/standalone89.
    const bool terminal=records&&records->size()>=4&&records->back().opcode==0x89&&
        RecoveredTaiwanPkTerminalNotification::matches(records->back().bytes);
    bool valid=false;
    if(records && records->size()==1 && records->front().opcode==0x86 &&
       RecoveredBattlePlayerGrant::parse(records->front().bytes))valid=true;
    else if(records && records->size()>=3 &&
            (*records)[records->size()-1-(terminal?1:0)].opcode==0x88 &&
            RecoveredBattleVitalsBatch::parse_logical((*records)[records->size()-1-(terminal?1:0)].bytes)){
        // Current RecoveredPkActionProjection: one/two scalar action groups,
        // each [own MP?],83,matching target HP; one final friendly bulk.
        std::size_t at=0;unsigned groups=0,seen=0;valid=true;
        const auto end=records->size()-1-(terminal?1:0);
        while(at<end){
            bool own_mp=false;
            if((*records)[at].opcode==0x86){
                const auto mp=RecoveredBattleVitals::parse_logical((*records)[at].bytes);
                if(!mp || mp->resource()!=RecoveredBattleVitals::Resource::Mp || mp->position()!=0){valid=false;break;}
                own_mp=true;++at;
            }
            if(at>=end){valid=false;break;}
            const auto& animation=(*records)[at++];
            const auto attack=RecoveredBattleAttackPresentation::parse(animation.bytes);
            if(!attack || (attack->source()!=0&&attack->source()!=14) ||
               (animation.bytes[5]&~1u)||animation.bytes[6]||(animation.bytes[7]&~1u)||animation.bytes[8] ||
               (own_mp&&attack->source()!=0) || at>=end){valid=false;break;}
            const auto side=static_cast<unsigned>(attack->source()/14);
            if(seen&(1u<<side)){valid=false;break;}seen|=1u<<side;
            const auto hp=RecoveredBattleVitals::parse_logical((*records)[at++].bytes);
            if(!hp || hp->resource()!=RecoveredBattleVitals::Resource::Hp ||
               hp->position()!=14*(1-side) || ++groups>2){valid=false;break;}
        }
        valid=valid&&at==end&&groups>=1;
    }
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
    try {asio::post(impl_->strand,[self=shared_from_this(),pending,reservation=std::move(reservation)]()mutable{
        auto& s=*self->impl_;
        if(s.native_battle_pending.load()!=pending || pending->completing.load())return;
        try{
            s.native_pk_timer.expires_after(close_timeout);
            s.native_pk_timer.async_wait([self,pending](const asio::error_code& ec){
                auto& s=*self->impl_;
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
    const auto data=hold.data_;
    if(!data || data->thread!=std::this_thread::get_id() || data->game!=impl_->game ||
       data->session.lock().get()!=this || data->phase.load()!=NativePkEntryHold::Data::Phase::Committed ||
       !impl_->native_pk_transport_current(data,true) || account_id!=data->request.account ||
       character_id!=data->request.character)
        throw std::logic_error("Native PK release lacks exact committed transport hold");
    // This post can allocate/throw AFTER durable activation; caller must close
    // both peers and retain durable recovery, never pretend rollback succeeded.
    asio::post(impl_->strand,[self=shared_from_this(),data] {
        auto& s=*self->impl_;
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
    asio::post(impl_->strand,[self=shared_from_this(),data] {
        auto& s=*self->impl_;
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
void Session::send_world_records_with_acceptance(std::vector<std::uint8_t> logical,
    std::uint64_t expected_account,std::uint64_t expected_character,std::uint64_t expected_world_generation,std::uint64_t expected_battle_generation,std::function<void(bool)> acceptance) {
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
    asio::post(impl_->strand,[self=shared_from_this(),logical=std::move(logical),reservation,expected_account,expected_character,expected_world_generation,expected_battle_generation,complete=std::move(complete)]() mutable {
        auto& s=*self->impl_;
        if(s.closing || s.close_requested.load()) {complete(false);return;}
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
            s.writes.push_back({std::move(bytes),std::move(reservation)});
            complete(true);
            if(s.writes.size()==1) s.write();
        } catch(...) {complete(false);s.fail("Recovered world push encoding failed"); }
    });
}
void Session::close() {
    impl_->retire_normal_output(); // Synchronized retirement before close publication/post.
    if (impl_->close_requested.exchange(true)) return;
    asio::post(impl_->strand, [self = shared_from_this()] { self->impl_->close(); });
}
void Session::notify_authenticated() {
    if (impl_->close_requested.load() || impl_->auth_requested.exchange(true)) return;
    asio::post(impl_->strand, [self = shared_from_this()] {
        auto& s = *self->impl_;
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
        if(current!=state)impl_->retire_normal_output(); // Before phase/battle mutation, even same final pose.
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
bool Session::recovered_world_ready() const noexcept { return recovered_world_ready_.load(); }
const std::string& Session::remote_ip() const noexcept { return impl_->ip; }
} // namespace god2
