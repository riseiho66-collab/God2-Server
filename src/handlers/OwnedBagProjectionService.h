#pragma once
#include "db/DbTypes.h"
#include "db/SqliteArmorSlotRepository.h"
#include "db/SqliteBeastSnapshotRepository.h"
#include "db/SqliteSupport.h"
#include "db/SqliteTeleportGemRepository.h"
#include "db/SqliteWeaponSlotRepository.h"
#include "protocol/RecoveredArmorInstance.h"
#include "protocol/RecoveredInventoryProjection.h"
#include <algorithm>
#include <array>
#include <cstdint>
#include <functional>
#include <limits>
#include <optional>
#include <span>
#include <string>
#include <utility>
#include <vector>

namespace god2 {
// CUSTOM-0066: read-only, owner-bound bag rendering. Projection eligibility is
// not bank/trade eligibility. Requires the three existing metadata tables;
// neither construction nor reading installs schema, capacity or instances.
class OwnedBagProjectionService {
public:
    bool shares_connection(sqlite3* db) const noexcept{return db_==db;}
    using QualifyArmor=SqliteArmorSlotRepository::QualifyArmor;
    using QualifyWeapon=std::function<bool(std::uint16_t)>;
    using PlainProjection=std::function<std::vector<std::uint8_t>(std::uint8_t,const StoredInventorySlot&)>;
    struct ScalarChange {std::uint8_t slot;StoredInventorySlot before,after;};
    class Proof {
        friend class OwnedBagProjectionService;
        ArmorSnapshot expected_;
        std::vector<StoredBeastSnapshot> beasts_;
        std::optional<SqliteBeastSnapshotRepository::SelectionRecord> selection_;
        explicit Proof(ArmorSnapshot value):expected_(std::move(value)){}
    public:
        const ArmorSnapshot& snapshot() const {return expected_;}
    };
    OwnedBagProjectionService(sqlite3* db,QualifyArmor armor,QualifyWeapon weapon,PlainProjection plain,SqliteArmorSlotRepository::QualifyInstance instance={},SqliteBeastSnapshotRepository* beasts=nullptr)
        :db_(db),armor_(std::move(armor)),weapon_(std::move(weapon)),plain_(std::move(plain)),instance_(std::move(instance)),beasts_(beasts) {
        require(db_&&bool(armor_)&&bool(weapon_)&&bool(plain_),"Bag projector requires database and qualified encoders");
        require(!beasts_||beasts_->shares_connection(db_),"Bag beast custody must share writer connection");
    }
    // Full-owner proof is independent of bank/trade eligibility and receipts.
    // Capture both trade participants separately. No schema/grants are made.
    Proof capture_proof(std::uint64_t account,std::uint64_t character) const {
        ReadScope scope(db_);SqliteArmorSlotRepository repository(db_,armor_,instance_);auto saved=repository.load_snapshot(account,character);
        for(std::uint8_t slot=0;slot<30;++slot)if(saved.scalar[slot])encode(slot,read(account,character,slot));
        require(repository.load_snapshot(account,character)==saved,"Bag proof changed during capture");
        Proof proof(std::move(saved));
        if(beasts_){proof.beasts_=beasts_->load_owned(account,character);proof.selection_=beasts_->load_selection_record(account,character);}
        scope.finish();return proof;
    }
    // Invoke immediately before writes INSIDE the mutation transaction.
    void verify_proof_in_transaction(const Proof& proof) const {
        require(sqlite3_get_autocommit(db_)==0,"Bag proof verification requires active mutation transaction");
        SqliteArmorSlotRepository repository(db_,armor_,instance_);require(repository.load_snapshot(proof.expected_.account,proof.expected_.character)==proof.expected_,"Bag full-owner prewrite proof conflict");
        verify_beasts(proof);
    }
    // Invoke after all scalar writes and before COMMIT, in the SAME transaction.
    // SQL triggers cannot change another instance's bytes/revision/provenance,
    // protected34..49, owner, or introduce/remove foreign overlays unnoticed.
    void verify_planned_in_transaction(const Proof& proof,std::span<const ScalarChange> changes) const {
        require(sqlite3_get_autocommit(db_)==0,"Bag planned proof requires active mutation transaction");auto expected=proof.expected_;std::array<bool,30> seen{};
        for(const auto& change:changes){
            require(change.slot<30&&!seen[change.slot],"Bag planned proof duplicate/protected slot");seen[change.slot]=true;
            const auto& baseline=proof.expected_.scalar[change.slot];require(baseline&&*baseline==change.before,"Bag planned proof baseline mismatch");
            if(change.before==change.after)continue;
            scalar_valid(change.after);require(change.before.revision<revision_limit&&change.after.revision==change.before.revision+1,"Bag planned proof physical revision invalid");
            require(!instance(change.before.item_id,change.before.count)&&!instance(change.after.item_id,change.after.count),"Bag planned proof changes instance category");
            require(std::none_of(expected.armor.begin(),expected.armor.end(),[&](const auto& row){return row.slot==change.slot;})&&std::none_of(expected.gems.begin(),expected.gems.end(),[&](const auto& row){return row.slot==change.slot;}),"Bag planned proof changes owned armor/gem metadata");
            require(std::none_of(expected.weapons.begin(),expected.weapons.end(),[&](const auto& row){return row.slot==change.slot&&row.origin!="EMPTY_SLOT_POLICY";}),"Bag planned proof changes occupied weapon metadata");
            if(change.before.count)plain(change.slot,change.before);if(change.after.count)plain(change.slot,change.after);
            // Original scalar-update trigger retires only empty weapon overlays.
            std::erase_if(expected.weapons,[&](const auto& row){return row.slot==change.slot&&row.origin=="EMPTY_SLOT_POLICY";});expected.scalar[change.slot]=change.after;
        }
        SqliteArmorSlotRepository repository(db_,armor_,instance_);require(repository.load_snapshot(expected.account,expected.character)==expected,"Bag full-owner postwrite proof conflict");
        verify_beasts(proof);
    }
    // Saved restoration: the entire supplied scalar, including source and
    // physical revision, must equal the explicit currently owned database row.
    std::vector<std::uint8_t> project(std::uint64_t account,std::uint64_t character,
        std::uint8_t slot,const StoredInventorySlot& expected) const {
        ReadScope scope(db_);const auto cell=read(account,character,slot);
        require(cell.scalar==expected,"Bag projection scalar snapshot conflict");
        auto logical=encode(slot,cell);require(read(account,character,slot)==cell,"Bag projection changed while encoding");
        scope.finish();return logical;
    }
    // Precommit bank/trade callers have a current baseline and a planned
    // outcome. Only independently qualified plain scalar cells may change.
    // Unchanged full instances are rendered exactly. This does not grant or
    // commit the proposed cell; callers retain their original CAS/eligibility.
    std::vector<std::uint8_t> project_planned(std::uint64_t account,std::uint64_t character,
        std::uint8_t slot,const StoredInventorySlot& before,const StoredInventorySlot& after) const {
        ReadScope scope(db_);const auto cell=read(account,character,slot);
        require(cell.scalar==before,"Planned bag projection baseline conflict");
        auto logical=encode(slot,cell);
        if(after!=before){
            scalar_valid(after);require(before.revision<revision_limit&&after.revision==before.revision+1,"Planned bag projection physical revision invalid");
            require(!cell.beast&&(!cell.metadata||(cell.metadata->kind==Kind::Weapon&&!before.count&&cell.metadata->origin=="EMPTY_SLOT_POLICY")),"Planned scalar change captures owned instance metadata");
            require(!instance(before.item_id,before.count)&&!instance(after.item_id,after.count),"Planned scalar change captures instance category");
            logical=after.count?plain(slot,after):empty(slot);
        }
        require(read(account,character,slot)==cell,"Planned bag projection changed while encoding");scope.finish();return logical;
    }
private:
    enum class Kind{Weapon,Armor,Gem};
    struct Metadata {
        Kind kind{};RecoveredInventoryProjection::Metadata bytes{};std::uint64_t revision{};
        std::string origin,provenance,source,client,design;
        bool operator==(const Metadata&) const=default;
    };
    struct Cell {StoredInventorySlot scalar;std::optional<Metadata> metadata;std::optional<StoredBeastSnapshot> beast;bool operator==(const Cell&) const=default;};
    struct ReadScope {
        sqlite3* db;bool owns,finished=false;
        explicit ReadScope(sqlite3* value):db(value),owns(sqlite3_get_autocommit(value)!=0){if(owns)sqlite_detail::execute(db,"BEGIN");}
        ~ReadScope(){if(owns&&!finished)sqlite3_exec(db,"ROLLBACK",nullptr,nullptr,nullptr);}
        void finish(){if(owns)sqlite_detail::execute(db,"COMMIT");finished=true;}
    };
    static constexpr auto revision_limit=static_cast<std::uint64_t>(std::numeric_limits<std::int64_t>::max());
    static void require(bool yes,const char* reason){if(!yes)throw DatabaseError(reason);}
    static void scalar_valid(const StoredInventorySlot& row){require(row.revision&&row.revision<=revision_limit&&row.count<=127&&((row.count==0)==(row.item_id==0))&&row.source_sha256.size()==64&&row.source_sha256.find_first_not_of("0123456789abcdef")==std::string::npos,"Malformed owned bag scalar");}
    std::optional<std::uint8_t> armor(std::uint16_t item) const {const auto target=armor_(item);require(!target||(*target>=30&&*target<=33),"Bag armor mapping outside qualified domain");return target;}
    bool instance(std::uint16_t item,std::uint8_t count) const {
        if(!count)return false;const bool w=weapon_(item),a=armor(item).has_value(),g=item==RecoveredTeleportGem::item_id;
        const bool b=beasts_&&NativeBeastSourceCatalog::lookup(item);
        require(unsigned(w)+unsigned(a)+unsigned(g)+unsigned(b)<=1,"Bag item classification conflicts");return w||a||g||b;
    }
    Cell read(std::uint64_t account,std::uint64_t character,std::uint8_t slot) const {
        require(account&&account<=revision_limit&&character&&character<=revision_limit&&slot<30,"Bag projector owner/slot invalid");
        sqlite_detail::Statement owner(db_,"SELECT 1 FROM recovered_characters WHERE account_id=? AND id=?");owner.bind_id(1,account);owner.bind_id(2,character);require(owner.row(),"Bag projection owner rejected");
        sqlite_detail::Statement scalar(db_,"SELECT item_id,count,revision,source_sha256,design_id FROM diagnostic_inventory_slots WHERE character_id=? AND slot=?");scalar.bind_id(1,character);scalar.bind(2,slot);
        require(scalar.row()&&scalar.text(4)=="CUSTOM-0015","Bag projection needs explicit owned scalar row");
        Cell cell{{scalar.number<std::uint16_t>(0),scalar.number<std::uint8_t>(1),scalar.number<std::uint64_t>(2),scalar.text(3)},{},{}};scalar_valid(cell.scalar);
        const auto metadata=[&](Kind kind,const char* query){
            sqlite_detail::Statement read(db_,query);read.bind_id(1,character);read.bind(2,slot);if(!read.row())return;
            require(!cell.metadata,"Bag projection cross-overlay conflict");Metadata row;row.kind=kind;const auto bytes=read.blob(0,20,20);std::copy(bytes.begin(),bytes.end(),row.bytes.begin());
            row.revision=read.number<std::uint64_t>(1);row.origin=read.text(2);row.provenance=read.text(3);row.source=read.text(4);row.client=read.text(5);row.design=read.text(6);require(!read.row(),"Duplicate owned bag overlay");cell.metadata=std::move(row);
        };
        metadata(Kind::Weapon,"SELECT logical20,revision,origin,provenance,source_sha256,client_sha256,design_id FROM character_weapon_slot_metadata WHERE character_id=? AND slot=?");
        metadata(Kind::Armor,"SELECT logical20,revision,origin,provenance,source_sha256,client_sha256,design_id FROM character_armor_slot_metadata WHERE character_id=? AND slot=?");
        metadata(Kind::Gem,"SELECT metadata20,revision,origin,provenance,source_sha256,'',design_id FROM character_teleport_gem_metadata WHERE character_id=? AND slot=?");
        if(beasts_)cell.beast=beasts_->load(account,character,slot);
        require(!cell.beast||!cell.metadata,"Bag beast cross-overlay conflict");return cell;
    }
    static std::vector<std::uint8_t> empty(std::uint8_t slot){const auto clear=RecoveredInventory::clear_slot(slot);require(clear.has_value(),"Bag empty projection rejected");return {clear->begin(),clear->end()};}
    std::vector<std::uint8_t> plain(std::uint8_t slot,const StoredInventorySlot& row) const {
        // Preserve the original CUSTOM-0037 plain encoder and its restrictions.
        // Zero tails are permitted here only, never for an owned full instance.
        auto logical=plain_(slot,row);RecoveredInventoryProjection::Metadata bytes{};bytes[0]=static_cast<std::uint8_t>(row.item_id);bytes[1]=static_cast<std::uint8_t>(row.item_id>>8);
        const auto canonical=RecoveredInventoryProjection::encode({slot,row.count,bytes});require(canonical&&logical==*canonical,"Plain bag encoder is not canonical scalar projection");return logical;
    }
    std::vector<std::uint8_t> encode(std::uint8_t slot,const Cell& cell) const {
        const auto& scalar=cell.scalar;const bool classified=instance(scalar.item_id,scalar.count);
        if(cell.beast){
            // CUSTOM-0085 exact owned metadata, never the plain zero-tail path.
            require(scalar.count==1&&cell.beast->inventory_slot==slot&&cell.beast->bag_revision==scalar.revision&&cell.beast->panel.metadata_key()==scalar.item_id,"Bag beast snapshot mismatch");
            const auto bytes=RecoveredInventoryProjection::encode({slot,1,cell.beast->inventory_metadata});require(bytes.has_value(),"Bag beast metadata projection rejected");return *bytes;
        }
        if(!cell.metadata){require(!classified,"Owned bag instance lacks full metadata");return scalar.count?plain(slot,scalar):empty(slot);}
        const auto& row=*cell.metadata;const auto key=static_cast<std::uint16_t>(row.bytes[0]|(std::uint16_t{row.bytes[1]}<<8));
        require(row.revision==scalar.revision&&key==scalar.item_id&&row.source==scalar.source_sha256&&row.source==SqliteArmorSlotRepository::source_sha256&&!row.provenance.empty()&&row.provenance.size()<=512&&row.provenance.find('\0')==std::string::npos,"Owned bag metadata/scalar evidence mismatch");
        if(row.kind==Kind::Weapon)require(row.design=="CUSTOM-0046"&&row.client==SqliteWeaponSlotRepository::client_sha256,"Owned bag weapon pins mismatch");
        else if(row.kind==Kind::Armor)require(row.design==SqliteArmorSlotRepository::design_id&&row.client==SqliteArmorSlotRepository::client_sha256,"Owned bag armor pins mismatch");
        else require(row.design=="CUSTOM-0057"&&row.client.empty(),"Owned bag gem pins mismatch");
        if(!scalar.count){require(row.kind==Kind::Weapon&&row.origin=="EMPTY_SLOT_POLICY","Empty bag has occupied overlay");return empty(slot);}
        require(scalar.count==1&&(row.origin=="NATIVE_CAPTURE_VERIFIED"||row.origin=="CUSTOM_TEST_NOT_NATIVE"),"Owned bag instance count/origin rejected");
        if(row.kind==Kind::Weapon)require(weapon_(scalar.item_id)&&!armor(scalar.item_id)&&scalar.item_id!=RecoveredTeleportGem::item_id,"Bag weapon overlay category conflict");
        else if(row.kind==Kind::Armor)require(armor(scalar.item_id).has_value()&&!weapon_(scalar.item_id)&&scalar.item_id!=RecoveredTeleportGem::item_id&&RecoveredArmorInstance::armor_family(row.bytes)&&(!instance_||instance_(scalar.item_id,row.bytes)),"Bag armor overlay category/family conflict");
        else require(scalar.item_id==RecoveredTeleportGem::item_id&&!weapon_(scalar.item_id)&&!armor(scalar.item_id)&&RecoveredTeleportGem::displayed_charges(row.bytes).has_value(),"Bag gem overlay key/type/charges conflict");
        const auto logical=RecoveredInventoryProjection::encode({slot,scalar.count,row.bytes});require(logical.has_value(),"Owned full bag projection rejected");return *logical;
    }
    void verify_beasts(const Proof& proof) const {
        if(beasts_)require(beasts_->load_owned(proof.expected_.account,proof.expected_.character)==proof.beasts_&&
            beasts_->load_selection_record(proof.expected_.account,proof.expected_.character)==proof.selection_,"Bag beast custody/selection preservation conflict");
    }
    sqlite3* db_;QualifyArmor armor_;QualifyWeapon weapon_;PlainProjection plain_;SqliteArmorSlotRepository::QualifyInstance instance_;
    SqliteBeastSnapshotRepository* beasts_{}; // explicit opt-in; same managed DB connection
};
}
