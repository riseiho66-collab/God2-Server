#include "db/SqliteOwnedEquipmentTransaction.h"
#include "db/SqliteSupport.h"
#include <limits>
#include <string_view>

namespace god2 {
SqliteOwnedEquipmentTransaction::SqliteOwnedEquipmentTransaction(SqliteOwnedInventoryRepository& inventory,
    SqliteNativeEquipmentSnapshotRepository& equipment):inventory_(inventory),equipment_(equipment) {
    owner();
    if(inventory_.db_!=equipment_.db_ || &inventory_.accounts_!=&equipment_.accounts_ ||
       &inventory_.characters_!=&equipment_.characters_ ||
       !owns_sources(inventory_.accounts_,inventory_.characters_))
        throw DatabaseError("Joint equipment requires exact same common connection and writers");
}
void SqliteOwnedEquipmentTransaction::owner() const {inventory_.owner();equipment_.owner();}
bool SqliteOwnedEquipmentTransaction::owns_sources(const AccountRepository& a,const RecoveredCharacterRepository& c) const noexcept {
    return inventory_.db_==equipment_.db_ && inventory_.owns_sources(a,c) && equipment_.owns_sources(a,c);
}
bool SqliteOwnedEquipmentTransaction::owns_writers(const SqliteOwnedInventoryRepository& a,
    const SqliteNativeEquipmentSnapshotRepository& b) const noexcept {return &a==&inventory_ && &b==&equipment_;}
bool SqliteOwnedEquipmentTransaction::common_current(const RecoveredCharacter& root,const RecoveredPosition& position) {
    return inventory_.root_current(root) &&
        inventory_.characters_.load_position(root.account_id,root.id)==std::optional{position};
}
bool SqliteOwnedEquipmentTransaction::stored_current(const Before& wanted,const State& next) {
    if(inventory_.reentered_||equipment_.reentered_||sqlite3_get_autocommit(inventory_.db_))return false;
    // Native load rejects all common/native TEMP shadows before borrowed common
    // reads. Inventory load additionally rejects shadows of its full population.
    const auto equipment=equipment_.load(next.equipment.root.account_id,next.equipment.root.id,
        next.equipment.client_sha256,next.equipment.record_kind);
    const auto inventory=inventory_.load(next.inventory.root.account_id,next.inventory.root.id);
    return equipment==wanted.equipment && inventory==wanted.inventory &&
        common_current(next.inventory.root,next.equipment.position) &&
        !inventory_.reentered_ && !equipment_.reentered_;
}
std::optional<SqliteOwnedEquipmentTransaction::Committed> SqliteOwnedEquipmentTransaction::replace_from_issuer(
    Before expected,State next,Issuer issuer) {
    owner();
    if(inventory_.writing_||equipment_.writing_) {
        inventory_.reentered_=equipment_.reentered_=true;
        throw DatabaseError("Joint equipment writer reentered");
    }
    auto* db=inventory_.db_;
    if(!issuer||!sqlite3_get_autocommit(db)||!owns_sources(inventory_.accounts_,inventory_.characters_)||
       !NativeEquipmentSnapshot::same_root(next.inventory.root,next.equipment.root))
        throw DatabaseError("Joint equipment requires full same-owner state and own outer transaction");
    inventory_.validate_change(expected.inventory,next.inventory);
    equipment_.validate_change(expected.equipment,next.equipment);
    inventory_.writing_=equipment_.writing_=true;
    inventory_.reentered_=equipment_.reentered_=false;
    struct End {
        SqliteOwnedInventoryRepository& a;SqliteNativeEquipmentSnapshotRepository& b;
        ~End(){a.writing_=a.reentered_=a.issuer_active_=false;b.writing_=b.reentered_=b.issuer_active_=false;}
    } end{inventory_,equipment_};
    {sqlite_detail::Statement fk(db,"PRAGMA foreign_keys");
     if(!fk.row()||fk.integer(0)!=1||fk.row())throw DatabaseError("Joint equipment requires foreign keys");}
    sqlite_detail::Transaction tx(db);
    if(!stored_current(expected,next))throw DatabaseError("Joint equipment before tuple changed");
    const auto roots=inventory_.characters_.list_for_account(next.inventory.root.account_id);
    const auto check=[&](const Before& wanted) {
        if(!stored_current(wanted,next))throw DatabaseError("Joint equipment full source changed");
        const auto actual=inventory_.characters_.list_for_account(next.inventory.root.account_id);
        if(actual.size()!=roots.size())throw DatabaseError("Joint equipment common root population changed");
        for(std::size_t i=0;i<roots.size();++i)
            if(!NativeEquipmentSnapshot::same_root(actual[i],roots[i]))throw DatabaseError("Joint equipment common root changed");
        if(!common_current(next.inventory.root,next.equipment.position)||inventory_.reentered_||equipment_.reentered_)
            throw DatabaseError("Joint equipment common position/battle state changed");
    };
    const auto issue=[&](Check phase) {
        const auto changes=sqlite3_total_changes64(db);
        inventory_.issuer_active_=equipment_.issuer_active_=true;
        struct Leave {bool& a;bool& b;~Leave(){a=b=false;}} leave{inventory_.issuer_active_,equipment_.issuer_active_};
        const auto supplied=issuer(expected,next,phase);
        if(inventory_.reentered_||equipment_.reentered_||sqlite3_get_autocommit(db)||sqlite3_total_changes64(db)!=changes)
            throw DatabaseError("Joint equipment issuer reentered or changed transaction/storage");
        return supplied&&*supplied==next;
    };
    check(expected);if(!issue(Check::Prepared))return std::nullopt;check(expected);
    if(!issue(Check::BeforeWrite))return std::nullopt;check(expected);
    inventory_.stage_replace(expected.inventory,next.inventory);
    equipment_.stage_replace(expected.equipment,next.equipment);
    const Before staged{next.inventory,next.equipment};
    check(staged);if(!issue(Check::BeforeCommit))return std::nullopt;check(staged);
    // No externally visible uncommitted token: all three receipts remain local
    // until the one outer COMMIT has succeeded. Allocation failure rolls back.
    std::optional<Committed> result{Committed(identity_,
        SqliteOwnedInventoryRepository::Committed(inventory_.identity_,std::make_shared<const OwnedInventorySnapshot>(next.inventory)),
        SqliteNativeEquipmentSnapshotRepository::Committed(equipment_.identity_,std::make_shared<const NativeEquipmentSnapshot>(next.equipment)))};
    tx.commit();return result; // No post-COMMIT issuer/read/retry/allocation.
}
std::optional<SqliteOwnedEquipmentTransaction::Committed> SqliteOwnedEquipmentTransaction::move_position_from_current(
    Before expected,std::uint16_t actor_handle,std::uint16_t x,std::uint16_t y,MovementCurrent current) {
    owner();
    if(inventory_.writing_||equipment_.writing_) {
        inventory_.reentered_=equipment_.reentered_=true;
        throw DatabaseError("Joint movement writer reentered");
    }
    auto* db=inventory_.db_;
    if(!current||!expected.inventory||!expected.equipment||!sqlite3_get_autocommit(db)||
       !owns_sources(inventory_.accounts_,inventory_.characters_)||
       !NativeEquipmentSnapshot::same_root(expected.inventory->root,expected.equipment->root)||
       expected.equipment->actor_handle!=actor_handle)
        throw DatabaseError("Joint movement requires complete exact owned material and actor");
    const auto limit=static_cast<std::uint64_t>(std::numeric_limits<std::int64_t>::max());
    if(!expected.equipment->position.revision||expected.equipment->position.revision>=limit||
       !expected.equipment->revision||expected.equipment->revision>=limit)
        throw DatabaseError("Joint movement revision overflow");
    // This is an explicit persistence policy, not a claim that walking produced
    // a new native inventory or DA observation. Every material byte stays owned.
    State next{*expected.inventory,*expected.equipment};
    next.equipment.position.x=x;next.equipment.position.y=y;
    ++next.equipment.position.revision;++next.equipment.revision;
    constexpr std::string_view marker=";CUSTOM-0095:ordinary-move-preserves-material";
    if(next.equipment.source_record.find(marker)==std::string::npos) {
        if(next.equipment.source_record.size()>2048-marker.size())
            throw DatabaseError("Joint movement provenance exceeds bounded storage");
        next.equipment.source_record.append(marker);
    }
    equipment_.validate_change(expected.equipment,next.equipment);
    inventory_.writing_=equipment_.writing_=true;
    inventory_.reentered_=equipment_.reentered_=false;
    struct End {
        SqliteOwnedInventoryRepository& a;SqliteNativeEquipmentSnapshotRepository& b;
        ~End(){a.writing_=a.reentered_=a.issuer_active_=false;b.writing_=b.reentered_=b.issuer_active_=false;}
    } end{inventory_,equipment_};
    {sqlite_detail::Statement fk(db,"PRAGMA foreign_keys");
     if(!fk.row()||fk.integer(0)!=1||fk.row())throw DatabaseError("Joint movement requires foreign keys");}
    sqlite_detail::Transaction tx(db);
    const auto namespaces=[&] {
        if(inventory_.reentered_||equipment_.reentered_||sqlite3_get_autocommit(db))
            throw DatabaseError("Joint movement reentered or lost its transaction");
        sqlite_detail::Statement shadow(db,"SELECT 1 FROM temp.sqlite_master WHERE name COLLATE NOCASE IN ('accounts','recovered_characters','recovered_positions','battle_reservations','battle_settlements','owned_inventory_headers','owned_item_instances','owned_inventory_cells','owned_item_native_aliases','character_native_equipment_snapshots') OR tbl_name COLLATE NOCASE IN ('accounts','recovered_characters','recovered_positions','battle_reservations','battle_settlements','owned_inventory_headers','owned_item_instances','owned_inventory_cells','owned_item_native_aliases','character_native_equipment_snapshots')");
        if(shadow.row())throw DatabaseError("Joint movement TEMP shadow rejected");
        sqlite_detail::Statement tables(db,"SELECT count(*) FROM main.sqlite_master WHERE type='table' AND name COLLATE NOCASE IN ('accounts','recovered_characters','recovered_positions','battle_reservations','battle_settlements','owned_inventory_headers','owned_item_instances','owned_inventory_cells','owned_item_native_aliases','character_native_equipment_snapshots')");
        if(!tables.row()||tables.integer(0)!=10||tables.row())
            throw DatabaseError("Joint movement requires actual main source tables");
    };
    // Qualify namespaces before the concrete common readers' existing names.
    namespaces();
    const auto roots=inventory_.characters_.list_for_account(next.inventory.root.account_id);
    const auto check=[&](const Before& wanted,const RecoveredPosition& position) {
        namespaces();
        const auto actual_equipment=equipment_.load(next.equipment.root.account_id,next.equipment.root.id,
            next.equipment.client_sha256,next.equipment.record_kind);
        const auto actual_inventory=inventory_.load(next.inventory.root.account_id,next.inventory.root.id);
        if(actual_equipment!=wanted.equipment||actual_inventory!=wanted.inventory)
            throw DatabaseError("Joint movement full material changed");
        const auto actual_roots=inventory_.characters_.list_for_account(next.inventory.root.account_id);
        if(actual_roots.size()!=roots.size())throw DatabaseError("Joint movement common root population changed");
        for(std::size_t i=0;i<roots.size();++i)
            if(!NativeEquipmentSnapshot::same_root(actual_roots[i],roots[i]))
                throw DatabaseError("Joint movement common root changed");
        if(!common_current(next.inventory.root,position))
            throw DatabaseError("Joint movement common position/root/battle changed");
        namespaces();
    };
    const auto observe=[&] {
        const auto changes=sqlite3_total_changes64(db);
        inventory_.issuer_active_=equipment_.issuer_active_=true;
        struct Leave {bool& a;bool& b;~Leave(){a=b=false;}} leave{inventory_.issuer_active_,equipment_.issuer_active_};
        const bool allowed=current();
        if(inventory_.reentered_||equipment_.reentered_||sqlite3_get_autocommit(db)||sqlite3_total_changes64(db)!=changes)
            throw DatabaseError("Joint movement Current reentered or changed transaction/storage");
        return allowed;
    };
    const auto& old_position=expected.equipment->position;
    check(expected,old_position);
    if(!observe())return std::nullopt; // Prepared: actual native scene still OLD.
    check(expected,old_position);
    if(!observe())return std::nullopt; // BeforeWrite: never called after staging.
    check(expected,old_position);
    {
        sqlite_detail::Statement write(db,"UPDATE main.recovered_positions SET x=?,y=?,revision=? WHERE character_id=? AND revision=? AND area=? AND scene=? AND x=? AND y=?");
        write.bind(1,x);write.bind(2,y);write.bind_id(3,next.equipment.position.revision);
        write.bind_id(4,next.inventory.root.id);write.bind_id(5,old_position.revision);
        write.bind(6,old_position.area);write.bind(7,old_position.scene);write.bind(8,old_position.x);write.bind(9,old_position.y);
        write.done();if(sqlite3_changes(db)!=1)throw DatabaseError("Joint movement saved position CAS failed");
    }
    // Closed checks also catch any source-table trigger side effects before the
    // old native witness is replaced; no supplier may observe staged position.
    check(expected,next.equipment.position);
    equipment_.stage_replace(expected.equipment,next.equipment);
    const Before staged{next.inventory,next.equipment};
    check(staged,next.equipment.position);
    // Inventory is not rewritten, so its complete bytes/identity/revision and
    // provenance remain exact. Both immutable receipts allocate BEFORE COMMIT.
    std::optional<Committed> result{Committed(identity_,
        SqliteOwnedInventoryRepository::Committed(inventory_.identity_,std::make_shared<const OwnedInventorySnapshot>(next.inventory)),
        SqliteNativeEquipmentSnapshotRepository::Committed(equipment_.identity_,std::make_shared<const NativeEquipmentSnapshot>(next.equipment)))};
    tx.commit();return result; // No callback/read/retry/allocation after COMMIT.
}
std::optional<SqliteOwnedEquipmentTransaction::Before> SqliteOwnedEquipmentTransaction::observe_before(
    std::uint64_t account,std::uint64_t character) {
    owner();
    if(inventory_.writing_||equipment_.writing_){inventory_.reentered_=equipment_.reentered_=true;return std::nullopt;}
    auto* db=inventory_.db_;
    if(!sqlite3_get_autocommit(db)||!owns_sources(inventory_.accounts_,inventory_.characters_))
        throw DatabaseError("Joint bag observation requires its actual sources and own read scope");
    inventory_.writing_=equipment_.writing_=true;
    inventory_.reentered_=equipment_.reentered_=false;
    struct End {
        SqliteOwnedInventoryRepository& a;SqliteNativeEquipmentSnapshotRepository& b;
        ~End(){a.writing_=a.reentered_=false;b.writing_=b.reentered_=false;}
    } end{inventory_,equipment_};
    sqlite_detail::execute(db,"BEGIN");
    struct Read {sqlite3* db;bool finished=false;~Read(){if(!finished)sqlite3_exec(db,"ROLLBACK",nullptr,nullptr,nullptr);}} read{db};
    sqlite_detail::Statement shadow(db,"SELECT 1 FROM temp.sqlite_master WHERE name COLLATE NOCASE IN ('accounts','recovered_characters','recovered_positions','battle_reservations','battle_settlements','owned_inventory_headers','owned_item_instances','owned_inventory_cells','owned_item_native_aliases','character_native_equipment_snapshots') OR tbl_name COLLATE NOCASE IN ('accounts','recovered_characters','recovered_positions','battle_reservations','battle_settlements','owned_inventory_headers','owned_item_instances','owned_inventory_cells','owned_item_native_aliases','character_native_equipment_snapshots')");
    if(shadow.row())throw DatabaseError("Joint bag observation TEMP shadow rejected");
    sqlite_detail::Statement tables(db,"SELECT count(*) FROM main.sqlite_master WHERE type='table' AND name COLLATE NOCASE IN ('accounts','recovered_characters','recovered_positions','battle_reservations','battle_settlements','owned_inventory_headers','owned_item_instances','owned_inventory_cells','owned_item_native_aliases','character_native_equipment_snapshots')");
    if(!tables.row()||tables.integer(0)!=10||tables.row())throw DatabaseError("Joint bag observation requires actual main tables");
    Before result{inventory_.load(account,character),equipment_.load(account,character,
        NativeEquipmentSnapshot::client_pin,NativeEquipmentSnapshot::kind)};
    if(!result.inventory||!result.equipment || !NativeEquipmentSnapshot::same_root(result.inventory->root,result.equipment->root) ||
       !common_current(result.inventory->root,result.equipment->position))return std::nullopt;
    if(inventory_.reentered_||equipment_.reentered_||sqlite3_get_autocommit(db))
        throw DatabaseError("Joint bag observation reentered or lost read scope");
    sqlite_detail::execute(db,"COMMIT");read.finished=true;return result;
}
std::optional<SqliteOwnedEquipmentTransaction::Committed> SqliteOwnedEquipmentTransaction::observe_committed(
    std::uint64_t account,std::uint64_t character) {
    // CUSTOM-0112: reuse the actual joint read/namespace/root qualification,
    // never combine two independently observed writer receipts.
    auto observed=observe_before(account,character);
    if(!observed||!observed->inventory||!observed->equipment)return std::nullopt;
    std::optional<Committed> result{Committed(identity_,
        SqliteOwnedInventoryRepository::Committed(inventory_.identity_,
            std::make_shared<const OwnedInventorySnapshot>(std::move(*observed->inventory))),
        SqliteNativeEquipmentSnapshotRepository::Committed(equipment_.identity_,
            std::make_shared<const NativeEquipmentSnapshot>(std::move(*observed->equipment))))};
    if(!committed_current(*result))return std::nullopt;
    return result;
}
bool SqliteOwnedEquipmentTransaction::before_current(const Before& expected) {
    owner();
    if(inventory_.writing_||equipment_.writing_){inventory_.reentered_=equipment_.reentered_=true;return false;}
    auto* db=inventory_.db_;
    if(!expected.inventory||!expected.equipment||!sqlite3_get_autocommit(db)||
       !owns_sources(inventory_.accounts_,inventory_.characters_)||
       !NativeEquipmentSnapshot::same_root(expected.inventory->root,expected.equipment->root))return false;
    sqlite_detail::execute(db,"BEGIN");
    struct Read {sqlite3* db;bool finished=false;~Read(){if(!finished)sqlite3_exec(db,"ROLLBACK",nullptr,nullptr,nullptr);}} read{db};
    const State wanted{*expected.inventory,*expected.equipment};
    const bool current=stored_current(expected,wanted);
    sqlite_detail::execute(db,"COMMIT");read.finished=true;return current;
}
bool SqliteOwnedEquipmentTransaction::committed_current(const Committed& token) {
    owner();
    if(inventory_.writing_||equipment_.writing_){inventory_.reentered_=equipment_.reentered_=true;return false;}
    auto* db=inventory_.db_;
    if(!sqlite3_get_autocommit(db)||token.identity_!=identity_||
       token.inventory_.identity_!=inventory_.identity_||token.equipment_.identity_!=equipment_.identity_||
       !owns_sources(inventory_.accounts_,inventory_.characters_))return false;
    // Own one read transaction. Private stored_current uses both readers inside
    // that same scope, not their separate public committed_current scopes.
    sqlite_detail::execute(db,"BEGIN");
    struct Read {sqlite3* db;bool finished=false;~Read(){if(!finished)sqlite3_exec(db,"ROLLBACK",nullptr,nullptr,nullptr);}} read{db};
    const State wanted{token.inventory_.snapshot(),token.equipment_.snapshot()};
    const Before same{wanted.inventory,wanted.equipment};
    const bool current=NativeEquipmentSnapshot::same_root(wanted.inventory.root,wanted.equipment.root)&&stored_current(same,wanted);
    sqlite_detail::execute(db,"COMMIT");read.finished=true;return current;
}
bool SqliteOwnedEquipmentTransaction::committed_current_in_scope(sqlite3* connection,const Committed& token) {
    owner();
    const Committed retained=token; // Own the immutable input BEFORE SQL hooks.
    if(closed_reading_){closed_poisoned_=true;return false;}
    if(inventory_.writing_||equipment_.writing_){
        inventory_.reentered_=equipment_.reentered_=true;return false;
    }
    if(closed_poisoned_||inventory_.issuer_active_||equipment_.issuer_active_||
       inventory_.reentered_||equipment_.reentered_||connection!=inventory_.db_||
       connection!=equipment_.db_||!connection||sqlite3_get_autocommit(connection)||
       retained.identity_!=identity_||retained.inventory_.identity_!=inventory_.identity_||
       retained.equipment_.identity_!=equipment_.identity_||
       !owns_sources(inventory_.accounts_,inventory_.characters_))return false;
    const auto changes=sqlite3_total_changes64(connection);
    // These flags belong to this read only after the foreign-operation checks.
    // Reentry flags remain sticky; no foreign issuer flag is reset on exit.
    closed_reading_=true;inventory_.writing_=equipment_.writing_=true;
    struct Exit {
        SqliteOwnedEquipmentTransaction& joint;
        ~Exit(){joint.inventory_.writing_=joint.equipment_.writing_=false;joint.closed_reading_=false;}
    } exit{*this};
    const auto fence=[&] {
        owner();
        if(closed_poisoned_||!closed_reading_||!inventory_.writing_||!equipment_.writing_||
           inventory_.issuer_active_||equipment_.issuer_active_||inventory_.reentered_||equipment_.reentered_||
           connection!=inventory_.db_||connection!=equipment_.db_||sqlite3_get_autocommit(connection)||
           sqlite3_total_changes64(connection)!=changes||
           !owns_sources(inventory_.accounts_,inventory_.characters_)){
            closed_poisoned_=true;throw DatabaseError("Joint equipment closed read changed or reentered");
        }
    };
    const auto namespaces=[&] {
        sqlite_detail::Statement shadow(connection,"SELECT 1 FROM temp.sqlite_master WHERE name COLLATE NOCASE IN ('accounts','recovered_characters','recovered_positions','battle_reservations','battle_settlements','owned_inventory_headers','owned_item_instances','owned_inventory_cells','owned_item_native_aliases','character_native_equipment_snapshots') OR tbl_name COLLATE NOCASE IN ('accounts','recovered_characters','recovered_positions','battle_reservations','battle_settlements','owned_inventory_headers','owned_item_instances','owned_inventory_cells','owned_item_native_aliases','character_native_equipment_snapshots')");
        if(shadow.row())throw DatabaseError("Joint equipment closed TEMP namespace rejected");fence();
        sqlite_detail::Statement tables(connection,"SELECT count(*) FROM main.sqlite_master WHERE type='table' AND name COLLATE NOCASE IN ('accounts','recovered_characters','recovered_positions','battle_reservations','battle_settlements','owned_inventory_headers','owned_item_instances','owned_inventory_cells','owned_item_native_aliases','character_native_equipment_snapshots')");
        if(!tables.row()||tables.integer(0)!=10||tables.row())throw DatabaseError("Joint equipment closed read requires main tables");fence();
        sqlite_detail::Statement triggers(connection,"SELECT 1 FROM main.sqlite_master WHERE type='trigger' AND tbl_name COLLATE NOCASE IN ('accounts','recovered_characters','recovered_positions','battle_reservations','battle_settlements','owned_inventory_headers','owned_item_instances','owned_inventory_cells','owned_item_native_aliases','character_native_equipment_snapshots')");
        if(triggers.row())throw DatabaseError("Joint equipment closed trigger namespace rejected");fence();
    };
    fence();
    const State wanted{retained.inventory_.snapshot(),retained.equipment_.snapshot()};
    const Before same{wanted.inventory,wanted.equipment};
    namespaces();
    const bool current=NativeEquipmentSnapshot::same_root(wanted.inventory.root,wanted.equipment.root)&&stored_current(same,wanted);
    fence();namespaces();fence();return current;
}
}
