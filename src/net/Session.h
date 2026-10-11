#pragma once

#include "protocol/Packet.h"
#include "protocol/ProtocolMode.h"
#include "protocol/RecoveredC2S0002.h"
#include "protocol/RecoveredCharacterCreate.h"
#include "protocol/RecoveredCharacterDelete.h"
#include "protocol/RecoveredPostServerSelect.h"
#include "protocol/RecoveredPostCreateSelect.h"
#include "protocol/RecoveredWorldEntry.h"
#include "protocol/RecoveredMovement.h"
#include "protocol/RecoveredWorldRecords.h"
#include <asio.hpp>
#include <atomic>
#include <array>
#include <cstdint>
#include <functional>
#include <exception>
#include <memory>
#include <optional>
#include <string>
#include <vector>
#include <utility>

namespace god2 {

enum class SessionState {
    Connected, Handshaked, Authenticated, CharacterSelected,
    InWorld, InBattle, Disconnected
};

class Session : public std::enable_shared_from_this<Session> {
    struct Impl;
public:
    // Private actual accepted C28 occurrence, valid only inside its synchronous
    // game callback. Copies share one take/dispatch state. No native nonce,
    // semantic replay permission, gameplay authority or binary attestation.
    class NativeWorldSelectionInput final {
    public:
        NativeWorldSelectionInput(const NativeWorldSelectionInput&)=default;
        NativeWorldSelectionInput& operator=(const NativeWorldSelectionInput&)=default;
        NativeWorldSelectionInput(NativeWorldSelectionInput&& other) noexcept:data_(other.data_) {}
        NativeWorldSelectionInput& operator=(NativeWorldSelectionInput&& other) noexcept {
            data_=other.data_;return *this;
        }
        const RecoveredSelectionItemRequest::Request& request() const noexcept;
        const RecoveredSelectionItemRequest::LogicalRecord& logical() const noexcept;
        std::uint64_t batch_sequence() const noexcept;
        std::size_t record_index() const noexcept;
    private:
        friend class Session;
        friend struct Impl;
        struct Data;
        explicit NativeWorldSelectionInput(std::shared_ptr<const Data> data):data_(std::move(data)) {}
        std::shared_ptr<const Data> data_;
    };
    using PacketHandler = std::function<void(std::shared_ptr<Session>, Packet)>;
    using DisconnectHandler = std::function<void(std::shared_ptr<Session>)>;
    using RecoveredLoginHandler = std::function<std::uint64_t(const RecoveredC2S0002::Parsed&)>;
    // Once-published owned original account-stage input. Parsing is not target
    // permission or a cross-socket issued-list receipt. No mutable native data.
    struct RecoveredServerAdvertisement {
        enum class Origin {LegacyListCandidate,LoopbackRoutesCandidate};
        std::uint64_t session;
        Origin origin;
        std::vector<std::uint8_t> wire;
        // Exact successful socket-write observation; no client ACK, native
        // source authority or cross-socket admission follows from these bytes.
    };
    struct RecoveredServerSelection {
        std::uint64_t session,account;
        RecoveredPostServerSelect request;
        std::shared_ptr<const RecoveredServerAdvertisement> advertisement;
    };
    // Pure owned data only. Sequence identifies this source preparation, not a
    // native wire nonce, peer ACK, permission or cross-socket selection grant.
    struct NativeCharacterListDelivery {
        std::uint64_t session,account,sequence;
        std::array<std::uint8_t,78> frame;
        std::shared_ptr<const RecoveredServerSelection> selection;
    };
    using NativeCharacterList=std::shared_ptr<const NativeCharacterListDelivery>;
    // Complete immutable native battle publication data only. The sequence is
    // local source correlation, never a client nonce, grant or processing ACK.
    struct NativeBattleSkillDelivery {
        std::uint64_t session,account,character,common_generation,battle_generation,sequence;
        std::vector<std::uint8_t> logical;
    };
    using NativeBattleSkill=std::shared_ptr<const NativeBattleSkillDelivery>;
    // Passive exact-world-frame observation, minted only in the actual game
    // world-records callback. Copies retain data, never source callbacks or
    // gameplay owners. Written means local full async_write only, not ACK,
    // source freshness, a common/world lease, actor membership or permission.
    enum class WorldRecordsWriteStatus {Pending,Written,Failed};
    class WorldRecordsWrite {
    public:
        WorldRecordsWrite(const WorldRecordsWrite&)=default;
        WorldRecordsWrite& operator=(const WorldRecordsWrite&)=default;
        WorldRecordsWriteStatus status() const noexcept;
        const std::vector<std::uint8_t>& logical() const noexcept;
    private:
        friend class Session;
        friend struct Impl;
        struct Data;
        explicit WorldRecordsWrite(std::shared_ptr<Data> data):data_(std::move(data)) {}
        std::shared_ptr<Data> data_;
    };
    // Actual local normal-entry transcript: exact issued S2A, accepted raw tail
    // and successful existing world_ready hook. A private copy can be Pending
    // while that S2A's async_write completes. Neither state attests the remote
    // reset/catalog nor supplies a common lease, battle actor or skill grant.
    class NormalWorldInitialization {
    public:
        NormalWorldInitialization(const NormalWorldInitialization&)=default;
        NormalWorldInitialization& operator=(const NormalWorldInitialization&)=default;
        const RecoveredWorldEntry::Frame& entry_frame() const noexcept;
        const std::vector<std::uint8_t>& entry_logical() const noexcept;
        const std::vector<std::uint8_t>& accepted_tail() const noexcept;
        std::uint8_t config_flag() const noexcept;
        bool entry_written() const noexcept;
    private:
        friend class Session;
        friend struct Impl;
        struct Entry;
        struct Data;
        explicit NormalWorldInitialization(std::shared_ptr<const Data> data):data_(std::move(data)) {}
        std::shared_ptr<const Data> data_;
    };
    class NativeBattleSkillPublicationOwner {
    public:
        virtual ~NativeBattleSkillPublicationOwner()=default;
        // Both callbacks run only on game. No yielding or borrowed retention.
        // These are transport lifecycle hooks, not gameplay/grant authority.
        virtual bool before_native_battle_write(Session&,const NativeBattleSkill&)=0;
        virtual bool complete_native_battle_write(Session&,const NativeBattleSkill&,bool written)=0;
    };
    // CUSTOM-0108 distinct TW waiting PK entry transport. Complete bytes are owned input,
    // not gameplay permission. Only a real room coordinator may start this
    // AFTER accepted69; it must bind the exact ticket and recipient view.
    struct NativePkEntryRequest {
        // world_generation is the PK peer namespace, not the common lease.
        std::uint64_t account,character,common_generation,world_generation,prebattle_generation;
        RecoveredWorldEntry::Frame normal_entry_frame;
        std::vector<std::uint8_t> normal_entry_logical,accepted_tail;
        std::uint8_t config_flag;
        std::vector<std::uint8_t> logical;
    };
    class NativePkEntryHold {
    public:
        NativePkEntryHold(const NativePkEntryHold&)=default;
        NativePkEntryHold& operator=(const NativePkEntryHold&)=default;
        const NativePkEntryRequest& request()const noexcept;
        std::uint64_t session_id()const noexcept;
        std::uint64_t committed_battle_generation()const noexcept;
        bool operator==(const NativePkEntryHold&)const=default;
    private:
        friend class Session;
        friend struct Impl;
        struct Data;
        explicit NativePkEntryHold(std::shared_ptr<Data> data):data_(std::move(data)){}
        std::shared_ptr<Data> data_;
    };
    class NativePkEntryOwner {
    public:
        virtual ~NativePkEntryOwner()=default;
        // Actual serial game executor only. nullopt reports preparation/abort
        // failure once. A token returned by prepare is NOT a ready hold.
        virtual void native_pk_entry_held(Session&,std::optional<NativePkEntryHold>)=0;
        // Exact full local async_write, not native ACK. Return false rejects
        // completion and closes; durable recovery belongs to the room owner.
        virtual bool native_pk_entry_written(Session&,const NativePkEntryHold&,bool)=0;
    };
    // CUSTOM-0131 actual accepted-terminal input drain; not WORLD/DB authority.
    class NativePkTerminalBarrier {
    public:
        NativePkTerminalBarrier(const NativePkTerminalBarrier&)=default;
        NativePkTerminalBarrier& operator=(const NativePkTerminalBarrier&)=default;
        bool operator==(const NativePkTerminalBarrier&)const=default;
    private:
        friend class Session;
        friend struct Impl;
        struct Data;
        explicit NativePkTerminalBarrier(std::shared_ptr<Data> data):data_(std::move(data)){}
        std::shared_ptr<Data> data_;
    };
    class NativePkTerminalOwner {
    public:
        virtual ~NativePkTerminalOwner()=default;
        // Actual game executor only. Ready is a local drained cut, not an ACK.
        virtual bool native_pk_terminal_ready(Session&,const NativePkTerminalBarrier&)=0;
        // CUSTOM-0132 invoked only AFTER the separate accepted stamp/current fence.
        virtual bool native_pk_terminal_accepted(Session&,const NativePkTerminalBarrier&)=0;
        virtual void native_pk_terminal_failed(Session&,const NativePkTerminalBarrier&)=0;
    };
    // CUSTOM-0132 preallocated retained-generation material only. No state,
    // initialization publication, input release or durable/world return permit.
    class NativePkReturnPreparation {
    public:
        NativePkReturnPreparation(const NativePkReturnPreparation&)=default;
        NativePkReturnPreparation& operator=(const NativePkReturnPreparation&)=default;
        bool operator==(const NativePkReturnPreparation&)const=default;
    private:
        friend class Session;
        struct Data;
        explicit NativePkReturnPreparation(std::shared_ptr<const Data> data):data_(std::move(data)){}
        std::shared_ptr<const Data> data_;
    };
    struct NativeCharacterSelectionInput {
        std::uint64_t session,account;
        RecoveredPostCreateSelect::Selection input;
        std::optional<std::uint64_t> created;
    };
    // Passive observation for the explicit native-character source only.
    // Credentials remain owned private data; this does not grant handoff rights.
    struct NativeAuthenticatedInput {
        std::uint64_t session,account;
        ProtocolMode mode;
        RecoveredC2S0002::Parsed input;
    };
    // Passive actual accepted local IPv4 endpoint, not a config port, remote
    // peer address, realm ID or permission. Explicit native G source only.
    struct NativeLocalEndpoint {
        std::uint64_t session;
        ProtocolMode mode;
        std::array<std::uint8_t,4> address;
        std::uint16_t port;
    };
    // Explicit per-connection dual-world extension. Both callbacks run on the
    // serial game executor; the existing entry builder/world_ready remain intact.
    struct CommonWorldLifecycle {
        std::function<bool(Session&,const RecoveredWorldEntry::Frame&)> prepared;
        // Runs only after the transport accepted the native tail and set its
        // synchronized ready flag, before delivering any later world input.
        std::function<bool(Session&)> ready;
        using ReadyCompletion=std::function<void(bool)>;
        // Explicit deferred scene publication only; exclusive with ready.
        // Completion and cancellation run on the serial game owner, once.
        std::function<void(Session&,ReadyCompletion)> ready_async;
        std::function<void(Session&)> cancel;
    };
    using CommonWorldLifecycleFactory=std::function<std::shared_ptr<const CommonWorldLifecycle>(Session&)>;
    struct CommonWorldPublication {
        std::function<bool()> publish;
        std::function<void(bool)> queued;
    };
    struct RecoveredCharacterHandlers {
        // Invoked on game executor; complete exactly once on that same executor.
        // Only immutable password work may leave that executor.
        std::function<void(const RecoveredC2S0002::Parsed&,
            std::function<void(std::uint64_t,std::exception_ptr)>)> authenticate_async;
        std::function<std::array<std::uint8_t,78>(std::uint64_t)> list;
        // Explicit full native TW07 and issued-token source, exclusive with
        // legacy list/select callbacks. Both run only on the serial game owner.
        std::function<NativeCharacterList(Session&)> native_list;
        // Real source callbacks stay on game. Write holds only pure data.
        std::function<bool(Session&,const NativeCharacterList&)> native_list_current;
        std::function<bool(Session&,const NativeCharacterList&,bool)> native_list_complete;
        std::function<std::uint64_t(Session&,const RecoveredPostCreateSelect::Selection&,std::optional<std::uint64_t>)> native_select;
        std::function<std::uint64_t(std::uint64_t,const RecoveredCharacterCreate&)> create;
        std::function<std::uint64_t(std::uint64_t,std::uint64_t,std::uint8_t)> select_created;
        std::function<std::uint64_t(std::uint64_t,std::uint8_t)> select_existing;
        std::function<RecoveredWorldEntry::Frame(std::uint64_t,std::uint64_t,std::uint64_t)> world_entry;
        std::function<void(Session&)> world_ready;
        std::function<std::vector<std::uint8_t>(Session&,std::span<const RecoveredMovement::Request>)> movement;
        // Serial game executor, after authenticated world-tail validation.
        // Mutually exclusive with movement. Own policy/transaction validation
        // belongs to this handler; parsing is not gameplay authorization.
        // nullopt rejects; an empty vector accepts without inventing a reply.
        // Nonempty output must contain complete recovered S2C envelopes.
        // Basic attacks and action0B require InBattle before this callback.
        // The handler still owns participant/turn/target authorization; transport
        // never creates a battle or substitutes the fixture BattleHandler.
        std::function<std::optional<std::vector<std::uint8_t>>(
              Session&,std::span<const RecoveredWorldRecords::Record>)> world_records;
        bool guild_relations53=false; // Only private Application53 explicit branch.
        bool beast_views=false; // CUSTOM0085 opt-in9D/9F, not6B/6C/9E activity admission
        bool companion_controls6b=false; // native shared lanes0..4; no gameplay adapter yet
        bool beast_activity9e=false; // native C2S9E format only; no exploration rule/handler
        bool e4_controls=false; // native C2SE4 format only; no state/effect handler
        bool bf_requests=false; // native C2SBF raw eight-byte variants; no transaction handler
        bool spectator6e=false; // native C2S6E raw9 format; no spectator lifecycle handler
        bool map_panel68=false; // CUSTOM-0087 owned regional-map 68->3F source route when explicitly enabled
        bool c2_controls=false; // native C2 raw8: separate mode1, F5-linked modes2..6; no handler
        bool spectator_close=false; // Actual selected A3/CB owner, not enabled by6E framing.
        std::function<std::uint8_t(std::uint64_t,std::uint64_t)> created_slot;
        std::function<bool(Session&,const RecoveredCharacterDelete&)> delete_character;
        bool pk_invitations=false; // CUSTOM0086 transport; full shared PK room remains required
        std::shared_ptr<const CommonWorldLifecycle> common_world_lifecycle;
        // Exclusive with direct hooks. Invoked once for this selected Session,
        // on game after a full world frame exists; never from the constructor.
        // Must return complete per-Session hooks; no null/default fallback.
        CommonWorldLifecycleFactory common_world_lifecycle_factory;
        // Trusted factory-only ownership adapter. It must retain the actual
        // cleanup on the game owner and return a one-shot transport facade;
        // no source callback may be destroyed by late network handler copies.
        std::function<std::function<void()>(Session&,std::function<void()>)> common_world_cleanup_owner;
        // Paired with cleanup_owner. Game disconnect also abandons a factory
        // slot when closure was requested before prepared could install cleanup.
        std::function<void(Session&)> common_world_lifecycle_abandon;
        // Required for deferred entry publication. Own real callbacks on game;
        // the returned queue facades must remain safe after owner revocation.
        std::function<CommonWorldPublication(Session&,CommonWorldPublication)> common_world_publication_owner;
        // Explicit typed C28 source installed by actual Application plan only.
        // False preserves every existing legacy/frozen dispatch path.
        bool native_selection_input=false;
        // Set only from an installed actual typed game-owner skill binding.
        // Network retains raw command bytes; it never reads a skill catalog.
        bool native_skill_commands=false;
        bool owned_blacklist=false; // Explicit CUSTOM-0096 handler installed by Application.
        bool owned_party_directory=false; // Explicit CUSTOM-0097 final handler installed.
        bool owned_client_options=false; // CUSTOM-0100 exact B1(7/8) parser source opt-in.
    };

    Session(asio::ip::tcp::socket socket, asio::any_io_executor game_executor,
            std::uint64_t id, bool packet_dump, PacketHandler on_packet,
            DisconnectHandler on_disconnect, ProtocolMode mode=ProtocolMode::Fixture,
            RecoveredLoginHandler recovered_login={},RecoveredCharacterHandlers characters={},
            std::vector<std::uint8_t> character_routes={});
    ~Session();
    Session(const Session&) = delete;
    Session& operator=(const Session&) = delete;

    void start();
    void send(Packet packet);
    // Recovered logical S2C records, after world-tail acceptance only. Application
    // owns visibility/authorization; queue acceptance does not prove client receipt.
    void send_world_records(std::vector<std::uint8_t> logical);
    // Uses the SAME legacy enqueue/encoding/order/budget path. The actual
    // synchronous world-records game callback alone can create/current this
    // private observation. No new callback, held frame or input barrier.
    WorldRecordsWrite send_world_records_observed(std::vector<std::uint8_t> logical);
    bool world_records_write_current(const WorldRecordsWrite&) const;
    // Only the actual synchronous world-records game callback can obtain or
    // requalify this transcript. Missing metadata leaves the old sender intact.
    std::optional<NormalWorldInitialization> normal_world_initialization() const;
    bool normal_world_initialization_current(const NormalWorldInitialization&) const;
    // Peer observations on the SAME actual game-owner thread. Private receipt
    // constructors record that thread; an unknown/wrong thread or another
    // Session incarnation fails before reading target game-owned identity.
    // These pure checks neither mint receipts nor imply written/ACK/authority.
    // The original callback-local TLS APIs above keep their existing contract.
    bool world_records_write_current_on_game(const WorldRecordsWrite&) const;
    bool normal_world_initialization_current_on_game(const NormalWorldInitialization&) const;
    // PRIVATE0083 enqueue acceptance ONLY; no native/client ACK or receipt claimed.
    void send_world_records_with_acceptance(std::vector<std::uint8_t> logical,
        std::uint64_t expected_account,std::uint64_t expected_character,
        std::uint64_t expected_world_generation,std::uint64_t expected_battle_generation,std::function<void(bool)> acceptance);
    struct WorldDeliveryIdentity {std::uint64_t account{},character{},world_generation{},battle_generation{};};
    // Game executor binds an immutable synchronized world identity after selection.
    void bind_world_delivery_identity(WorldDeliveryIdentity identity);
    // Explicit common-world extension only, bound to its actual presence lease.
    // Independent from PRIVATE0083's world/battle delivery identity.
    void bind_common_world_delivery_identity(std::uint64_t account,std::uint64_t character,std::uint64_t generation);
    void release_common_world_delivery_identity(std::uint64_t account,std::uint64_t character,std::uint64_t generation);
    bool common_world_delivery_current(std::uint64_t account,std::uint64_t character,std::uint64_t generation) const;
    // Separate pending initial publication identity. No ready identity is
    // manufactured here; each binding gets a transport-owned nonreused nonce.
    void bind_common_world_entry_identity(std::uint64_t account,std::uint64_t character,std::uint64_t generation);
    void release_common_world_entry_identity(std::uint64_t account,std::uint64_t character,std::uint64_t generation);
    bool common_world_entry_current(std::uint64_t account,std::uint64_t character,std::uint64_t generation) const;
    void send_common_world_entry_with_publication(std::vector<std::uint8_t> logical,
        std::uint64_t account,std::uint64_t character,std::uint64_t generation,
        std::function<bool()> publish,std::function<void(bool)> queued);
    // Game-executor caller, actual complete native logical aggregate. The queue
    // holds bytes while the same executor qualifies/publishes common owner state.
    // Completion is once on game, local queue release only, not client receipt.
    void send_common_world_records_with_publication(std::vector<std::uint8_t> logical,
        std::uint64_t account,std::uint64_t character,std::uint64_t generation,
        std::function<bool()> publish,std::function<void(bool)> queued);
    // Explicit actual ASYNC common-ready game owner only; an unknown/synchronous
    // owner is rejected. Separate from the frozen world sender.
    // One pending exact common/battle incarnation. Input is held until actual
    // socket write and game completion; Write retains only data/weak owner.
    // Throw before acceptance lets the caller retire its own staged source.
    // The game executor and owner must drain before executor/DB shutdown.
    void send_native_battle_skill_publication(NativeBattleSkill,
        std::weak_ptr<NativeBattleSkillPublicationOwner>);
    // Set only by exact successful async_write. Not native/client acceptance.
    NativeBattleSkill native_battle_skill_written() const noexcept;
    bool native_battle_skill_publication_pending() const noexcept;
    bool same_native_pk_game_executor(const Session&)const noexcept;
    // CUSTOM-0124 executor identity only; no entry/room/output authority.
    bool native_pk_game_executor_matches(const asio::any_io_executor&)const noexcept;
    // Capture exact qualified CharacterSelected/InWorld privately and preserve
    // it until commit; Request cannot choose a phase or manufacture InWorld.
    NativePkEntryHold prepare_native_pk_entry(NativePkEntryRequest,
        std::weak_ptr<NativePkEntryOwner>);
    bool native_pk_entry_current(const NativePkEntryHold&)const noexcept;
    // CUSTOM-0113 exact private post-commit/pre-release fence. This does not
    // authorize a world return, prove socket completion or acknowledge a client.
    bool native_pk_entry_committed_current(const NativePkEntryHold&)const noexcept;
    // CUSTOM-0123 actual game-owner retained binding in Committed/Released/
    // Written phases. This is NOT a fullwrite/submission/output permit.
    bool native_pk_entry_binding_current(const NativePkEntryHold&)const noexcept;
    // CUSTOM-0115 actual full entry write accepted by its exact source owner,
    // after the entry pending handoff clears. No native ACK/turn permission.
    bool native_pk_entry_written_current(const NativePkEntryHold&)const noexcept;
    NativePkTerminalBarrier prepare_native_pk_terminal_barrier(const NativePkEntryHold&,
        NativeBattleSkill,std::weak_ptr<NativePkTerminalOwner>);
    bool native_pk_terminal_barrier_ready_current(const NativePkTerminalBarrier&)const noexcept;
    bool native_pk_terminal_barrier_accepted_current(const NativePkTerminalBarrier&)const noexcept;
    NativePkReturnPreparation prepare_native_pk_return_generation(const NativePkTerminalBarrier&);
    bool native_pk_return_preparation_current(const NativePkReturnPreparation&)const noexcept;
    // Separate retained-entry PK output only; old skill sender grammar stays
    // unchanged. Exact durable grant/result authority belongs to weak owner.
    void send_native_pk_output(const NativePkEntryHold&,NativeBattleSkill,
        std::weak_ptr<NativeBattleSkillPublicationOwner>);
    // Call ONLY after one durable shared activation. No allocation/callback;
    // failure then requires persistent recovery and both peers closed.
    bool commit_native_pk_entry(const NativePkEntryHold&)noexcept;
    void release_native_pk_entry(const NativePkEntryHold&);
    void abort_native_pk_entry(const NativePkEntryHold&);
    // Game-executor, one-shot transport-owned cleanup; independent of lifecycle
    // adapter lifetime. Runs before the existing disconnect callback, even if
    // either callback throws. Only the explicit common-world extension may bind.
    bool install_common_world_cleanup(std::function<void()> cleanup);
    bool closing() const noexcept;
    // Asynchronous: drain queued writes, with a five-second shutdown deadline.
    void close();
    void notify_authenticated();
    SessionState state() const noexcept;
    void set_state(SessionState state) noexcept;
    // Passive lifecycle fingerprint for game-executor modal leases. It changes
    // on entry/exit of battle even when the final state/position is identical.
    std::uint64_t battle_generation() const noexcept;
    std::uint64_t id() const noexcept;
    // Valid in the serial world-ready/world-record callbacks after tail validation.
    std::uint8_t recovered_client_language() const noexcept;
    bool recovered_world_ready() const noexcept;
    const std::string& remote_ip() const noexcept;
    // Actual native-list game callback input. Absence is honest (including an
    // independently authenticated world socket that never received A6).
    // Publication is game-owned; immutable copies retain this exact observation
    // identity, not just equal bytes. No public mutator or guessed realm IDs.
    std::shared_ptr<const RecoveredServerSelection> recovered_server_selection() const noexcept;
    // Actual socket success followed by same-source game Current. Still not a
    // client processing ACK or an independently authenticated world's grant.
    NativeCharacterList recovered_native_character_list() const noexcept;
    // Exact socket success only, even when later source qualification fails.
    NativeCharacterList recovered_native_character_list_written() const noexcept;
    std::shared_ptr<const NativeCharacterSelectionInput> recovered_native_selection_input() const noexcept;
    std::shared_ptr<const NativeAuthenticatedInput> recovered_native_authenticated_input() const noexcept;
    std::shared_ptr<const NativeLocalEndpoint> recovered_native_local_endpoint() const noexcept;

    // Only the serial game callback that owns the ORIGINAL parsed batch may
    // call these. A copied Request is rejected; a copied receipt cannot claim
    // the same occurrence twice. Never retain/yield these as future authority.
    std::optional<NativeWorldSelectionInput> take_world_selection_input(const RecoveredSelectionItemRequest::Request&);
    bool claim_world_selection_action(const NativeWorldSelectionInput&);
    bool world_selection_input_current(const NativeWorldSelectionInput&) const;

    // Only the serial game executor may access these fields. Protocol hooks
    // run on the network strand and must not access game-owned fields.
    std::uint64_t account_id = 0;
    std::uint64_t character_id = 0;

private:
    void send_world_records_impl(std::vector<std::uint8_t>,std::shared_ptr<WorldRecordsWrite::Data>);
    std::unique_ptr<Impl> impl_;
    std::atomic<SessionState> state_{SessionState::Connected};
    std::atomic<std::uint64_t> battle_generation_{0};
    std::atomic<bool> recovered_world_ready_{false};
    std::atomic<std::uint8_t> recovered_client_language_{0};
    std::atomic<std::shared_ptr<const RecoveredServerSelection>> recovered_server_selection_;
    std::atomic<NativeCharacterList> recovered_native_character_list_;
    std::atomic<NativeCharacterList> recovered_native_character_list_written_;
    std::atomic<NativeBattleSkill> native_battle_skill_written_;
    std::atomic<std::shared_ptr<const NativeCharacterSelectionInput>> recovered_native_selection_input_;
    std::atomic<std::shared_ptr<const NativeAuthenticatedInput>> recovered_native_authenticated_input_;
    std::atomic<std::shared_ptr<const NativeLocalEndpoint>> recovered_native_local_endpoint_;
};

} // namespace god2
