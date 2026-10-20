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
private:
    friend class OwnedPveRoomState;
    struct Commit {bool durable{},current{};};
    Ticket reserve(const Types::PureCurrent&);
    void abandon(const Ticket&)noexcept;
    std::shared_ptr<const void> claim_runtime(const Ticket&);
    Commit activate(const Ticket&,const Types::Snapshot&,const Types::PureCurrent&);
    Commit replace(const Ticket&,const Types::Snapshot&,const Types::Snapshot&,const Types::PureCurrent&);
    void validate_member(const Types::MemberInput&);
    Types::MemberInput updated_resources(Types::MemberInput,const BattleSnapshot&,bool withdrawn);
    sqlite3* db_;
    AccountRepository& accounts_;
    SqliteRecoveredCharacterRepository& characters_;
    SqliteRoleAuxiliaryRepository& auxiliary_;
    SqliteCompanionRepository& companions_;
    std::unique_ptr<SqliteNativeWorldEntrySnapshotRepository> row_preferences_;
    std::shared_ptr<Issuer> issuer_;
};
}
