#pragma once
#include "db/DbTypes.h"
#include "db/NativeSkillCatalog.h"
#include "db/SqliteRecoveredCharacterRepository.h"
#include "handlers/OwnedPkInvitationService.h"
#include "game/Battle.h"
#include "game/OwnedPkRound.h"
#include "game/OwnedTaiwanPkCombatSource.h"
#include "game/OwnedTaiwanPkCompanionSource.h"
#include <array>
#include <memory>
#include <map>
#include <mutex>
#include <utility>
#include <string>
struct sqlite3;
namespace god2 {
// CUSTOM-0086 independent, opt-in PK storage. No character/resource grants,
// experience awards, diagnostic reservation reuse or implicit schema install.
// This is a shared-state backend, NOT the Session RoomAuthority adapter.
class SqliteOwnedPkRoomRepository {
    struct RuntimeOwner {};
    struct Issuer {
        // Copies of this concrete repository share the same runtime namespace.
        std::mutex mutex; // Claim registry only, not SQLite/RoomState safety.
        std::map<std::uint64_t,std::weak_ptr<const RuntimeOwner>> claims;
    };
public:
    using Pair=OwnedPkInvitationService::Pair;
    using Replies=std::array<std::vector<std::uint8_t>,2>;
    using OwnedCombatSources=std::array<OwnedTaiwanPkCombatSource::Observation,2>;
    using OwnedCompanionSources=std::array<OwnedTaiwanPkCompanionSource::Observation,2>;
    struct Input {
        Pair pair;
        RecoveredPkEntryProjection::Prepared entry;
        std::array<CharacterResources,2> resources;
        std::array<CharacterRoleSnapshot,2> roles;
        std::array<BattleActor,2> actors;
        std::uint32_t seed{};
        // Digest of the owner-qualified profile/skill evidence readset.
        // A digest is a binding, not proof of native provenance. The adapter
        // must re-read the underlying evidence before admission/actions.
        std::string profile_readset_sha256;
        // Legacy: exact build-qualified initial0B masks per relative owner.
        // CUSTOM-0104 notification entry: ONLY exact allowed roster bounds
        // retained by Prepared, not an expected native target mask.
        // No room-ID, hit-target or guessed client-counter derivation.
        OwnedPkRound::Masks initial_control_masks;
        // CUSTOM-0106 optional at END: old aggregate/factory paths stay absent.
        std::optional<OwnedCombatSources> combat_sources{};
        // CUSTOM-0129 optional exact published normal-entry companion lineage.
        // Absent legacy input is never evidence of an empty native roster.
        std::optional<OwnedCompanionSources> companion_sources{};
    };
    class Ticket {
    public:
        std::uint64_t id()const noexcept{return id_;}
        std::uint64_t generation()const noexcept{return 1;}
        const Input& input()const noexcept{return *input_;}
        bool operator==(const Ticket& other)const noexcept{
            return id_==other.id_&&readset_==other.readset_;
        }
        // CUSTOM-0115 process-local capability identity, not serialized
        // readset equality or permission to recover a replacement ticket.
        bool same_incarnation(const Ticket& other)const noexcept{
            return id_==other.id_&&issuer_==other.issuer_&&input_==other.input_;
        }
    private:
        friend class SqliteOwnedPkRoomRepository;
        Ticket(std::uint64_t id,std::shared_ptr<const Input> input,std::string readset,
               std::shared_ptr<Issuer> issuer)
            :id_(id),input_(std::move(input)),readset_(std::move(readset)),issuer_(std::move(issuer)){}
        std::uint64_t id_;
        std::shared_ptr<const Input> input_;
        std::string readset_;
        std::shared_ptr<Issuer> issuer_; // NEW recovery/claim identity only.
    };
    struct Delivery {
        std::uint64_t room{},revision{},session{},world_generation{},battle_generation{};
        std::uint8_t viewer{};
        std::vector<std::uint8_t> logical;
    };
    struct GrantDelivery {
        std::uint64_t room{},epoch{},session{},world_generation{},battle_generation{};
        std::uint8_t viewer{};
        std::vector<std::uint8_t> logical;
    };
    // CUSTOM-0114 one same-process mutable Room owner, not a database lease.
    // A copied recovery snapshot cannot copy or share this owning capability.
    class RuntimeClaim {
    public:
        RuntimeClaim(const RuntimeClaim&)=delete;
        RuntimeClaim& operator=(const RuntimeClaim&)=delete;
        RuntimeClaim(RuntimeClaim&&)noexcept=default;
        RuntimeClaim& operator=(RuntimeClaim&&)noexcept=default;
    private:
        friend class SqliteOwnedPkRoomRepository;
        explicit RuntimeClaim(std::shared_ptr<const RuntimeOwner> owner):owner_(std::move(owner)){}
        std::shared_ptr<const RuntimeOwner> owner_;
    };
    struct RetainedOutbox {
        Delivery delivery;
        bool submitted;
    };
    class RetainedRecovery {
    public:
        const Ticket& ticket()const noexcept{return ticket_;}
        const BattleCheckpoint& checkpoint()const noexcept{return checkpoint_;}
        const OwnedPkRound& round()const noexcept{return round_;}
        const std::vector<RetainedOutbox>& outboxes()const noexcept{return outboxes_;}
    private:
        friend class SqliteOwnedPkRoomRepository;
        RetainedRecovery(Ticket ticket,BattleCheckpoint checkpoint,OwnedPkRound round,
                         std::vector<RetainedOutbox> outboxes,std::optional<std::string> terminal_resources)
            :ticket_(std::move(ticket)),checkpoint_(std::move(checkpoint)),round_(std::move(round)),
             outboxes_(std::move(outboxes)),terminal_resources_(std::move(terminal_resources)){}
        Ticket ticket_;
        BattleCheckpoint checkpoint_;
        OwnedPkRound round_;
        std::vector<RetainedOutbox> outboxes_;
        std::optional<std::string> terminal_resources_;
    };
    explicit SqliteOwnedPkRoomRepository(sqlite3* db):db_(db),owners_(db){require_schema(db_);require_round_schema(db_);}
    // Identity only; no read, schema installation or admission permission.
    bool uses_connection(const sqlite3* supplied)const noexcept{return supplied==db_;}
    static void install_schema(sqlite3*); // explicit caller; never called on read
    static void require_schema(sqlite3*); // exact own DDL; no DDL-on-read
    static void install_round_schema(sqlite3*); // separate opt-in; base DDL unchanged
    static void require_round_schema(sqlite3*);
    // CUSTOM-0127 explicit extension, never installed by a read or factory.
    static void install_terminal_resource_schema(sqlite3*);
    static void require_terminal_resource_schema(sqlite3*);
    Ticket prepare(Input);
    // Explicit custom stored-total adoption. Actor/resources/role values and
    // complete retained-source digest are produced internally, not caller stats.
    Ticket prepare_owned(Pair,RecoveredPkEntryProjection::Prepared,OwnedCombatSources,
        std::uint32_t seed,OwnedPkRound::Masks initial_control_masks,
        std::optional<OwnedCompanionSources> companion_sources={});
    bool current(const Ticket&); // RESERVED only; full two-owner readset
    BattleCheckpoint initial(const Ticket&); // no activation or sends
    // ONE transaction: both owner locks, one checkpoint, BOTH durable entries.
    // Outbox insertion is not a socket enqueue/client ACK or Session binding.
    void activate(const Ticket&);
    // Original retained private Ticket only. No JSON/scalar ticket rehydration,
    // live world qualification, state transition, resends or submitted resets.
    RuntimeClaim claim_runtime(const Ticket&);
    RetainedRecovery recover_retained(const Ticket&);
    bool retained_recovery_current(const RetainedRecovery&);
    // CUSTOM-0119 current durable binding to this active room's immutable
    // admitted profile. Expected checkpoint MUST come from its actual runtime
    // Battle, never native bytes. Read snapshot only, not a reusable permit,
    // stat refresh, skill ownership, Session qualification or runtime claim.
    std::string require_active_owned_profile(const Ticket&,const BattleCheckpoint& expected);
    // ONE shared checkpoint + TWO viewer projections, or no durable change.
    void advance(const Ticket&,const BattleCheckpoint& expected,
                 const BattleCheckpoint& next,const Replies&,
                 const std::optional<NativeSkillRecord>& definition={});
    // Paired CUSTOM-0086 collection settlement; one transaction publishes
    // checkpoint, round phase and BOTH viewer results or none of them.
    void settle(const Ticket&,const BattleCheckpoint& expected,
                const BattleCheckpoint& next,const OwnedPkRound& expected_round,
                const OwnedPkRound& next_round,const Replies&);
    // Presentation membership only, never skill ownership or native cost.
    NativeSkillRecord scalar_definition(std::uint16_t skill_key);
    std::string scalar_definition_document(std::uint16_t skill_key);
    // Snapshot/phase CAS only. Neither path changes HP/MP or battle revision.
    OwnedPkRound round(const Ticket&);
    void control(const Ticket&,const OwnedPkRound& expected,std::uint8_t viewer,
                 const RecoveredBattleCommand::ControlRequest&);
    void submit_intent(const Ticket&,const OwnedPkRound& expected,std::uint8_t viewer,
                       OwnedPkRound::Intent);
    std::vector<GrantDelivery> pending_grants(const Ticket&);
    // CUSTOM-0121 later grants require the actual runtime owner's checkpoint.
    // Original overload remains initial-only; no legacy/raw ticket promotion.
    std::vector<GrantDelivery> pending_grants(const Ticket&,const BattleCheckpoint& actual);
    void grant_submitted(const Ticket&,std::uint64_t epoch,std::uint8_t viewer);
    void abandon(const Ticket&)noexcept; // reserved only; IDs always retained
    bool occupied(std::uint64_t account,std::uint64_t character);
    std::vector<Delivery> pending(const Ticket&);
    // Only the eventual exact-identity enqueue callback may call this. This
    // marks submission to its queue, NOT delivery, rendering or a native ACK.
    void submitted(const Ticket&,std::uint64_t revision,std::uint8_t viewer);
private:
    friend class OwnedPkRoomState;
    struct TerminalResources {
        std::array<CharacterResources,2> after;
        Replies outputs;
        std::string document;
        bool both_submitted;
    };
    sqlite3* db_;
    SqliteRecoveredCharacterRepository owners_; // SAME SQLite connection
    std::shared_ptr<Issuer> issuer_=std::make_shared<Issuer>();
    static void validate(const Input&);
    static std::string readset(const Input&);
    bool owners_current(const Input&);
    std::optional<std::string> terminal_resource_ledger(const Ticket&);
    TerminalResources terminal_resources_in_scope(const Ticket&,const BattleCheckpoint* actual=nullptr);
    bool finished_owners_current(const Ticket&);
    // Called ONLY by the private RoomState seam consumed by Publication's
    // actual two fullwrite callbacks in one original binding; DB flags alone
    // cannot mint those transport observations or authorize this write.
    void commit_terminal_resources(const Ticket&,const BattleCheckpoint& actual,const Replies& actually_written);
    // CUSTOM-0132 paired return preparation requires the EXISTING exact saved
    // player ledger. Read snapshot only; never create/retry a missing save.
    void require_terminal_resources_saved(const Ticket&,const BattleCheckpoint& actual,const Replies& actually_written);
    // CUSTOM-0128 read-only qualification of this original viewer's native1C
    // after its actual final fullwrite. Not a save, ACK or WORLD permit.
    void require_terminal_context(const Ticket&,const BattleCheckpoint& actual,std::uint8_t viewer,
        const std::array<std::uint8_t,4>& payload,const std::vector<std::uint8_t>& actually_written);
    void require_ticket(const Ticket&,const char* state);
    void enqueue(const Ticket&,std::uint64_t revision,const Replies&);
    OwnedPkRound read_round(const Ticket&); // inside existing read/write transaction
    std::string require_active_owned_profile_in_scope(const Ticket&,const BattleCheckpoint&);
    std::vector<GrantDelivery> pending_grants_in_scope(const Ticket&,const BattleCheckpoint*);
    void store_round(const Ticket&,const OwnedPkRound& expected,const OwnedPkRound& next);
};
}
