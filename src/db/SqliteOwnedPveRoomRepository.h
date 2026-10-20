#pragma once
#include "game/OwnedPveRoomTypes.h"
#include "db/AccountRepository.h"
#include "db/SqliteRecoveredCharacterRepository.h"
#include "db/SqliteNativeWorldEntrySnapshotRepository.h"
#include <memory>
#include <thread>
struct sqlite3;
namespace god2 {
class OwnedPveRoomState;
// CUSTOM-0161. Independent tables and same-connection actual resource CAS.
// Constructor checks schema; installation is an EXPLICIT separate caller action.
class SqliteOwnedPveRoomRepository {
    struct Issuer;
    struct TicketData;
    struct ReturnData;
public:
    using Types=OwnedPveRoomTypes;
    class Ticket {
    public:
        Ticket(const Ticket&)=default;Ticket& operator=(const Ticket&)=default;
        std::uint64_t id()const noexcept;
        const std::string& incarnation()const noexcept;
        bool same_incarnation(const Ticket&)const noexcept;
    private:
        friend class SqliteOwnedPveRoomRepository;
        explicit Ticket(std::shared_ptr<TicketData> value):data_(std::move(value)){}
        std::shared_ptr<TicketData> data_;
    };
    // Minted only by this repository's successful newly-Returned transaction.
    // Values expose provenance, never a fresh Session/INIT capability.
    class ReturnContinuation {
    public:
        ReturnContinuation(const ReturnContinuation&)=default;
        ReturnContinuation& operator=(const ReturnContinuation&)=default;
        const Types::MemberInput& admission()const noexcept;
        const Types::MemberInput& saved()const noexcept;
        const Types::Identity& identity()const noexcept;
        std::uint64_t room()const noexcept;
        const std::string& incarnation()const noexcept;
    private:
        friend class SqliteOwnedPveRoomRepository;
        explicit ReturnContinuation(std::shared_ptr<ReturnData> p):data_(std::move(p)){}
        std::shared_ptr<ReturnData> data_;
    };
    SqliteOwnedPveRoomRepository(sqlite3*,AccountRepository&,SqliteRecoveredCharacterRepository&,
        SqliteRoleAuxiliaryRepository&,SqliteCompanionRepository&);
    ~SqliteOwnedPveRoomRepository();
    SqliteOwnedPveRoomRepository(const SqliteOwnedPveRoomRepository&)=delete;
    SqliteOwnedPveRoomRepository& operator=(const SqliteOwnedPveRoomRepository&)=delete;
    bool uses_connection(const sqlite3*)const noexcept;
    static std::string schema_sql();
    static void require_schema(sqlite3*);
    static void install_schema(sqlite3*); // PHASE1 callers MUST NOT invoke.
    bool character_claimed(std::uint64_t account,std::uint64_t character);
    // Read only: full durable history, not a live Session grant/rebind capability.
    Types::Snapshot read_retained(std::uint64_t room);
    bool return_continuation_current(const ReturnContinuation&,Types::PureCurrent);
private:
    friend class OwnedPveRoomState;
    struct Commit {bool durable{},current{};std::optional<ReturnContinuation> returned;};
    Ticket reserve(const Types::PureCurrent&);
    void abandon(const Ticket&)noexcept;
    std::shared_ptr<const void> claim_runtime(const Ticket&);
    Commit activate(const Ticket&,const Types::Snapshot&,const Types::PureCurrent&);
    Commit replace(const Ticket&,const Types::Snapshot&,const Types::Snapshot&,const Types::PureCurrent&);
    bool commit_uncertain(const Ticket&)const noexcept;
    void validate_member(const Types::MemberInput&);
    Types::MemberInput updated_resources(Types::MemberInput,const BattleSnapshot&,bool withdrawn,Types::Assignment);
    sqlite3* db_;
    AccountRepository& accounts_;
    SqliteRecoveredCharacterRepository& characters_;
    SqliteRoleAuxiliaryRepository& auxiliary_;
    SqliteCompanionRepository& companions_;
    std::unique_ptr<SqliteNativeWorldEntrySnapshotRepository> row_preferences_;
    std::shared_ptr<Issuer> issuer_;
    std::shared_ptr<const std::uint8_t> continuation_issuer_=std::make_shared<const std::uint8_t>(0);
};
}
