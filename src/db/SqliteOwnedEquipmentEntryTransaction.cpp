#include "db/SqliteOwnedEquipmentTransaction.h"
#include "db/SqliteSupport.h"
#include "game/SharedTaiwanStoredWorldEntrySource.h"
#include "protocol/RecoveredWorldEntryView.h"
#include <algorithm>
#include <vector>

namespace god2 {
namespace {
void entry_namespaces(sqlite3* db) {
    // Qualify every namespace before borrowed common readers. A main witness
    // alone cannot prevent an unqualified common reader from seeing TEMP data.
    sqlite_detail::Statement shadow(db,"SELECT 1 FROM temp.sqlite_master WHERE name COLLATE NOCASE IN ('accounts','recovered_characters','recovered_positions','battle_reservations','battle_settlements','owned_inventory_headers','owned_item_instances','owned_inventory_cells','owned_item_native_aliases','character_native_equipment_snapshots','character_native_world_entries') OR tbl_name COLLATE NOCASE IN ('accounts','recovered_characters','recovered_positions','battle_reservations','battle_settlements','owned_inventory_headers','owned_item_instances','owned_inventory_cells','owned_item_native_aliases','character_native_equipment_snapshots','character_native_world_entries')");
    if(shadow.row())throw DatabaseError("Joint entry TEMP shadow rejected");
    sqlite_detail::Statement tables(db,"SELECT count(*) FROM main.sqlite_master WHERE type='table' AND name COLLATE NOCASE IN ('accounts','recovered_characters','recovered_positions','battle_reservations','battle_settlements','owned_inventory_headers','owned_item_instances','owned_inventory_cells','owned_item_native_aliases','character_native_equipment_snapshots','character_native_world_entries')");
    if(!tables.row()||tables.integer(0)!=11||tables.row())
        throw DatabaseError("Joint entry requires actual main source tables");
}
std::optional<RecoveredWorldEntryView> entry_view(const NativeWorldEntrySnapshot& entry,
    const SqliteOwnedEquipmentTransaction::State& material,bool equal_appearance) {
    const auto& equipment=material.equipment;
    if(entry.client_sha256!=NativeEquipmentSnapshot::client_pin ||
       entry.record_kind!=SharedTaiwanStoredWorldEntrySource::record_kind ||
       equipment.client_sha256!=NativeEquipmentSnapshot::client_pin || equipment.record_kind!=NativeEquipmentSnapshot::kind ||
       !NativeWorldEntrySnapshot::same_root(entry.root,material.inventory.root) ||
       !NativeWorldEntrySnapshot::same_root(entry.root,equipment.root) || entry.position!=equipment.position ||
       entry.record.size()!=RecoveredWorldEntry::Frame{}.size())return std::nullopt;
    RecoveredWorldEntry::Frame frame;
    std::copy(entry.record.begin(),entry.record.end(),frame.begin());
    const auto view=RecoveredWorldEntryView::read(frame);
    const auto appearance=equipment.appearance();
    if(!view||!appearance||view->actor_handle!=equipment.actor_handle ||
       appearance->actor_identity()!=equipment.actor_handle ||
       view->area!=entry.position.area||view->scene!=entry.position.scene||
       view->x!=entry.position.x||view->y!=entry.position.y)return std::nullopt;
    if(equal_appearance) {
        const auto baseline=view->entry_appearance_baseline();
        const auto& da=RecoveredTaiwanPlayerAppearanceUpdate::encode_logical(*appearance);
        if(!std::equal(baseline.components.begin(),baseline.components.end(),da.begin()+7) ||
           baseline.transform_key!=(std::uint16_t(da[3])|(std::uint16_t(da[4])<<8)) ||
           baseline.raw_scalar5!=da[5] || baseline.raw_scalar6!=da[6])return std::nullopt;
    }
    return view;
}
bool appearance_only(const RecoveredWorldEntryView& before,const RecoveredWorldEntryView& next) {
    for(std::size_t i=0;i<before.logical.size();++i) {
        if((i>=13&&i<=20)||(i>=33&&i<=36))continue;
        if(before.logical[i]!=next.logical[i])return false;
    }
    return true;
}
bool same_roots(const std::vector<RecoveredCharacter>& a,const std::vector<RecoveredCharacter>& b) {
    if(a.size()!=b.size())return false;
    for(std::size_t i=0;i<a.size();++i)if(!NativeWorldEntrySnapshot::same_root(a[i],b[i]))return false;
    return true;
}
}
SqliteOwnedEquipmentTransaction::SqliteOwnedEquipmentTransaction(SqliteOwnedInventoryRepository& inventory,
    SqliteNativeEquipmentSnapshotRepository& equipment,SqliteNativeWorldEntrySnapshotRepository& world)
    :SqliteOwnedEquipmentTransaction(inventory,equipment) {
    world.owner();
    if(inventory_.db_!=world.db_ || &inventory_.accounts_!=&world.accounts_ ||
       &inventory_.characters_!=&world.characters_ || !world.owns_sources(inventory_.accounts_,inventory_.characters_))
        throw DatabaseError("Joint entry requires exact same common connection and writers");
    worlds_=&world;
}
bool SqliteOwnedEquipmentTransaction::owns_entry_writer(const SqliteNativeWorldEntrySnapshotRepository& world) const noexcept {
    return worlds_==&world && inventory_.db_==world.db_ &&
        world.owns_sources(inventory_.accounts_,inventory_.characters_);
}
void SqliteOwnedEquipmentTransaction::entry_owner() const {
    owner();
    if(!worlds_)throw DatabaseError("Joint entry requires explicit three-writer binding");
    worlds_->owner();
}
bool SqliteOwnedEquipmentTransaction::entry_stored_current(const WithEntryBefore& wanted,const WithEntryState& next) {
    if(!worlds_||inventory_.reentered_||equipment_.reentered_||worlds_->reentered_||
       sqlite3_get_autocommit(inventory_.db_))return false;
    entry_namespaces(inventory_.db_);
    if(!stored_current(wanted.material,next.material))return false;
    const auto entry=worlds_->load(next.entry.root.account_id,next.entry.root.id,next.entry.client_sha256,next.entry.record_kind);
    return entry==std::optional{wanted.entry} && common_current(next.entry.root,next.entry.position) &&
        !inventory_.reentered_&&!equipment_.reentered_&&!worlds_->reentered_;
}
std::optional<SqliteOwnedEquipmentTransaction::EntryCommitted>
SqliteOwnedEquipmentTransaction::replace_with_entry_from_issuer(WithEntryBefore expected,WithEntryState next,EntryIssuer issuer) {
    entry_owner();
    if(inventory_.writing_||equipment_.writing_||worlds_->writing_) {
        inventory_.reentered_=equipment_.reentered_=worlds_->reentered_=true;
        throw DatabaseError("Joint entry writer reentered");
    }
    auto* db=inventory_.db_;
    if(!issuer||!sqlite3_get_autocommit(db)||!owns_sources(inventory_.accounts_,inventory_.characters_)||
       !owns_entry_writer(*worlds_)||!expected.material.inventory||!expected.material.equipment)
        throw DatabaseError("Joint entry requires complete existing owned tuples and own transaction");
    const State old_material{*expected.material.inventory,*expected.material.equipment};
    const auto before_view=entry_view(expected.entry,old_material,false);
    const auto next_view=entry_view(next.entry,next.material,true);
    if(!before_view||!next_view||!appearance_only(*before_view,*next_view) ||
       !NativeWorldEntrySnapshot::same_root(expected.entry.root,next.entry.root)||expected.entry.position!=next.entry.position)
        throw DatabaseError("Joint entry requires exact frozen native entry and aligned DA after-state");
    inventory_.validate_change(expected.material.inventory,next.material.inventory);
    equipment_.validate_change(expected.material.equipment,next.material.equipment);
    worlds_->validate_change(std::optional{expected.entry},next.entry);
    inventory_.writing_=equipment_.writing_=worlds_->writing_=true;
    inventory_.reentered_=equipment_.reentered_=worlds_->reentered_=false;
    struct End {
        SqliteOwnedInventoryRepository& a;SqliteNativeEquipmentSnapshotRepository& b;SqliteNativeWorldEntrySnapshotRepository& c;
        ~End(){a.writing_=a.reentered_=a.issuer_active_=false;b.writing_=b.reentered_=b.issuer_active_=false;c.writing_=c.reentered_=c.issuer_active_=false;}
    } end{inventory_,equipment_,*worlds_};
    {sqlite_detail::Statement fk(db,"PRAGMA foreign_keys");
     if(!fk.row()||fk.integer(0)!=1||fk.row())throw DatabaseError("Joint entry requires foreign keys");}
    sqlite_detail::Transaction tx(db);
    entry_namespaces(db);
    if(!entry_stored_current(expected,next))throw DatabaseError("Joint entry before tuple changed");
    const auto roots=inventory_.characters_.list_for_account(next.entry.root.account_id);
    const auto check=[&](const WithEntryBefore& wanted) {
        if(!entry_stored_current(wanted,next)||
           !same_roots(roots,inventory_.characters_.list_for_account(next.entry.root.account_id)) ||
           !common_current(next.entry.root,next.entry.position) || inventory_.reentered_||equipment_.reentered_||worlds_->reentered_)
            throw DatabaseError("Joint entry complete source/root/pose changed");
    };
    const auto issue=[&](Check phase) {
        const auto changes=sqlite3_total_changes64(db);
        inventory_.issuer_active_=equipment_.issuer_active_=worlds_->issuer_active_=true;
        struct Leave {bool& a;bool& b;bool& c;~Leave(){a=b=c=false;}} leave{inventory_.issuer_active_,equipment_.issuer_active_,worlds_->issuer_active_};
        const auto supplied=issuer(expected,next,phase);
        if(inventory_.reentered_||equipment_.reentered_||worlds_->reentered_||sqlite3_get_autocommit(db)||sqlite3_total_changes64(db)!=changes)
            throw DatabaseError("Joint entry issuer reentered or changed storage/transaction");
        return supplied&&*supplied==next;
    };
    check(expected);if(!issue(Check::Prepared))return std::nullopt;check(expected);
    if(!issue(Check::BeforeWrite))return std::nullopt;check(expected);
    inventory_.stage_replace(expected.material.inventory,next.material.inventory);
    equipment_.stage_replace(expected.material.equipment,next.material.equipment);
    worlds_->stage_replace(std::optional{expected.entry},next.entry);
    const WithEntryBefore staged{{next.material.inventory,next.material.equipment},next.entry};
    check(staged);if(!issue(Check::BeforeCommit))return std::nullopt;check(staged);
    std::optional<EntryCommitted> result{EntryCommitted(Committed(identity_,
        SqliteOwnedInventoryRepository::Committed(inventory_.identity_,std::make_shared<const OwnedInventorySnapshot>(next.material.inventory)),
        SqliteNativeEquipmentSnapshotRepository::Committed(equipment_.identity_,std::make_shared<const NativeEquipmentSnapshot>(next.material.equipment))),
        std::make_shared<const NativeWorldEntrySnapshot>(next.entry))};
    tx.commit();return result; // No post-COMMIT supplier, read, retry or allocation.
}
bool SqliteOwnedEquipmentTransaction::committed_current(const EntryCommitted& token) {
    entry_owner();
    if(inventory_.writing_||equipment_.writing_||worlds_->writing_) {
        inventory_.reentered_=equipment_.reentered_=worlds_->reentered_=true;return false;
    }
    auto* db=inventory_.db_;
    const auto& material=token.material_;
    if(!sqlite3_get_autocommit(db)||material.identity_!=identity_ ||
       material.inventory_.identity_!=inventory_.identity_||material.equipment_.identity_!=equipment_.identity_ ||
       !owns_sources(inventory_.accounts_,inventory_.characters_)||!owns_entry_writer(*worlds_))return false;
    inventory_.writing_=equipment_.writing_=worlds_->writing_=true;
    inventory_.reentered_=equipment_.reentered_=worlds_->reentered_=false;
    struct End {
        SqliteOwnedInventoryRepository& a;SqliteNativeEquipmentSnapshotRepository& b;SqliteNativeWorldEntrySnapshotRepository& c;
        ~End(){a.writing_=a.reentered_=a.issuer_active_=false;b.writing_=b.reentered_=b.issuer_active_=false;c.writing_=c.reentered_=c.issuer_active_=false;}
    } end{inventory_,equipment_,*worlds_};
    sqlite_detail::execute(db,"BEGIN");
    struct Read {sqlite3* db;bool finished=false;~Read(){if(!finished)sqlite3_exec(db,"ROLLBACK",nullptr,nullptr,nullptr);}} read{db};
    entry_namespaces(db);
    const WithEntryState wanted{{material.inventory_.snapshot(),material.equipment_.snapshot()},*token.entry_};
    const WithEntryBefore same{{wanted.material.inventory,wanted.material.equipment},wanted.entry};
    const auto roots=inventory_.characters_.list_for_account(wanted.entry.root.account_id);
    const bool current=entry_view(wanted.entry,wanted.material,true).has_value() && entry_stored_current(same,wanted) &&
        same_roots(roots,inventory_.characters_.list_for_account(wanted.entry.root.account_id));
    sqlite_detail::execute(db,"COMMIT");read.finished=true;return current;
}
}
