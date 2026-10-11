#include "handlers/OwnedBagProjectionService.h"
#include "db/SqliteMigrationManager.h"
#include <array>
#include <iostream>
#include <memory>
#include <stdexcept>
using namespace god2;
namespace {
void require(bool yes,const char* message){if(!yes)throw std::runtime_error(message);}
template<class F>void rejects(F&& run){try{run();}catch(const DatabaseError&){return;}throw std::runtime_error("Expected owned bag projection rejection");}
// Synthetic60011 ->30 exercises ownership and byte preservation only; this is
// not a native ID/category/equip mapping, roll, grant, stat or appearance claim.
std::optional<std::uint8_t> armor(std::uint16_t item){return item==60011?std::optional<std::uint8_t>(30):std::nullopt;}
bool weapon(std::uint16_t item){return item==60010;}
std::vector<std::uint8_t> plain(std::uint8_t index,const StoredInventorySlot& row){
    if(row.source_sha256!=SqliteArmorSlotRepository::source_sha256||!row.count||(row.item_id!=3107&&row.item_id!=5569))throw DatabaseError("Unqualified original plain encoder");
    RecoveredInventoryProjection::Metadata metadata{};metadata[0]=static_cast<std::uint8_t>(row.item_id);metadata[1]=static_cast<std::uint8_t>(row.item_id>>8);
    return RecoveredInventoryProjection::encode({index,row.count,metadata}).value();
}
struct Fixture {
    sqlite3* raw{};std::unique_ptr<sqlite3,decltype(&sqlite3_close_v2)> db{nullptr,sqlite3_close_v2};std::array<std::uint64_t,2> characters{};
    Fixture(){require(sqlite3_open(":memory:",&raw)==SQLITE_OK,"Open failed");db.reset(raw);sql("PRAGMA foreign_keys=ON");auto migrations=default_sqlite_migrations();require(migrations.back().version>=42,"Armor migration boundary");while(migrations.back().version>=42)migrations.pop_back();SqliteMigrationManager(raw,std::move(migrations)).migrate();sql(SqliteArmorSlotRepository::schema());
        sql("INSERT INTO accounts(id,username,password_hash) VALUES(1,'project-a','hash'),(2,'project-b','hash')");SqliteRecoveredCharacterRepository roles(raw);
        for(unsigned n=0;n<2;++n){std::array<std::uint8_t,40> profile{};profile[0]=static_cast<std::uint8_t>('A'+n);characters[n]=roles.create(n+1,profile).id;for(unsigned slot=0;slot<50;++slot){sqlite_detail::Statement insert(raw,"INSERT INTO diagnostic_inventory_slots VALUES(?,?,0,0,1,?,'CUSTOM-0015')");insert.bind_id(1,characters[n]);insert.bind(2,slot);insert.bind(3,SqliteArmorSlotRepository::source_sha256);insert.done();}}
    }
    void sql(const std::string& query){sqlite_detail::execute(raw,query);}
    OwnedBagProjectionService service(){return {raw,armor,weapon,plain};}
    StoredInventorySlot scalar(unsigned slot,unsigned owner=0){sqlite_detail::Statement read(raw,"SELECT item_id,count,revision,source_sha256 FROM diagnostic_inventory_slots WHERE character_id=? AND slot=?");read.bind_id(1,characters[owner]);read.bind(2,slot);require(read.row(),"Fixture scalar absent");return {read.number<std::uint16_t>(0),read.number<std::uint8_t>(1),read.number<std::uint64_t>(2),read.text(3)};}
    void scalar(unsigned slot,std::uint16_t item,unsigned count,std::uint64_t revision,unsigned owner=0){sqlite_detail::Statement update(raw,"UPDATE diagnostic_inventory_slots SET item_id=?,count=?,revision=? WHERE character_id=? AND slot=?");update.bind(1,item);update.bind(2,count);update.bind_id(3,revision);update.bind_id(4,characters[owner]);update.bind(5,slot);update.done();}
    RecoveredInventoryProjection::Metadata instance(unsigned slot,std::uint16_t item,std::uint8_t fill,std::uint64_t revision=7,unsigned owner=0){
        scalar(slot,item,item?1:0,revision,owner);RecoveredInventoryProjection::Metadata bytes;bytes.fill(fill);bytes[0]=static_cast<std::uint8_t>(item);bytes[1]=static_cast<std::uint8_t>(item>>8);
        if(item==RecoveredTeleportGem::item_id){bytes[2]=8;bytes[3]=6;}
        const bool gem=item==RecoveredTeleportGem::item_id,a=item==60011;
        if(a)bytes[2]=static_cast<std::uint8_t>((bytes[2]&0xc0u)|2u);
        sqlite_detail::Statement insert(raw,gem?
            "INSERT INTO character_teleport_gem_metadata VALUES(?,?,?,?,?,?,?,'CUSTOM-0057')":a?
            "INSERT INTO character_armor_slot_metadata VALUES(?,?,?,?,?,?,?,?,'CUSTOM-0066')":
            "INSERT INTO character_weapon_slot_metadata VALUES(?,?,?,?,?,?,?,?,'CUSTOM-0046')");
        insert.bind_id(1,characters[owner]);insert.bind(2,slot);insert.bind_blob(3,bytes);insert.bind_id(4,revision);insert.bind(5,std::string(item?"CUSTOM_TEST_NOT_NATIVE":"EMPTY_SLOT_POLICY"));insert.bind(6,"isolated-projector-instance");insert.bind(7,SqliteArmorSlotRepository::source_sha256);if(!gem)insert.bind(8,a?SqliteArmorSlotRepository::client_sha256:SqliteWeaponSlotRepository::client_sha256);insert.done();return bytes;
    }
};
void full_instances_and_owner(){
    Fixture f;const auto w=f.instance(0,60010,0xa1),a=f.instance(1,60011,0xb2),g=f.instance(2,16055,0xc3),other=f.instance(0,60010,0xd4,7,1);f.scalar(3,3107,127,8);f.instance(4,0,0xe5);auto service=f.service();
    const auto changes=sqlite3_total_changes(f.raw);
    for(const auto& [slot,bytes]:std::array<std::pair<std::uint8_t,RecoveredInventoryProjection::Metadata>,3>{{{0,w},{1,a},{2,g}}}){
        const auto projected=service.project(1,f.characters[0],slot,f.scalar(slot));const auto expected=RecoveredInventoryProjection::encode({slot,1,bytes}).value();require(projected==expected,"Full owned20-byte instance was flattened or changed");}
    require(service.project(2,f.characters[1],0,f.scalar(0,1))==RecoveredInventoryProjection::encode({0,1,other}).value(),"Bag projector leaked another owner's20 bytes");
    require(service.project(1,f.characters[0],3,f.scalar(3))==plain(3,f.scalar(3)),"Plain127 stack did not preserve original encoder");
    require(service.project(1,f.characters[0],4,f.scalar(4))==std::vector<std::uint8_t>({0x41,0,0,4,0}),"Explicit empty legacy weapon overlay did not clear only");
    const auto empty=f.scalar(5);require(service.project(1,f.characters[0],5,empty).size()==5,"Explicit owned empty row rejected");
    rejects([&]{service.project(2,f.characters[0],0,f.scalar(0));});rejects([&]{service.project(1,f.characters[0],30,empty);});
    for(unsigned field=0;field<4;++field){auto wrong=f.scalar(0);if(field==0)++wrong.item_id;if(field==1)wrong.count=2;if(field==2)++wrong.revision;if(field==3)wrong.source_sha256=std::string(64,'0');rejects([&]{service.project(1,f.characters[0],0,wrong);});}
    require(sqlite3_total_changes(f.raw)==changes,"Bag projection wrote storage");
    f.sql("DELETE FROM diagnostic_inventory_slots WHERE slot=5");const auto removed=sqlite3_total_changes(f.raw);rejects([&]{service.project(1,f.characters[0],5,empty);});require(sqlite3_total_changes(f.raw)==removed,"Missing cell projection provisioned capacity");
}
void missing_and_conflicting_metadata(){
    Fixture f;auto service=f.service();
    for(const auto item:{60010,60011,16055}){f.scalar(0,static_cast<std::uint16_t>(item),1,9);const auto changes=sqlite3_total_changes(f.raw);rejects([&]{service.project(1,f.characters[0],0,f.scalar(0));});require(sqlite3_total_changes(f.raw)==changes,"Missing metadata was granted by projector");}
    f.scalar(0,999,1,10);rejects([&]{service.project(1,f.characters[0],0,f.scalar(0));});
    f.instance(1,60010,0xa1);f.sql("INSERT INTO character_teleport_gem_metadata SELECT character_id,slot,logical20,revision,'CUSTOM_TEST_NOT_NATIVE','collision',source_sha256,'CUSTOM-0057' FROM character_weapon_slot_metadata WHERE slot=1");rejects([&]{service.project(1,f.characters[0],1,f.scalar(1));});
    Fixture wrong_kind;wrong_kind.instance(1,60010,0xb2);auto bad_qualifier=OwnedBagProjectionService(wrong_kind.raw,armor,[](std::uint16_t){return false;},plain);rejects([&]{bad_qualifier.project(1,wrong_kind.characters[0],1,wrong_kind.scalar(1));});
    Fixture ambiguous;ambiguous.instance(1,60011,0xc3);auto conflicting=OwnedBagProjectionService(ambiguous.raw,armor,[](std::uint16_t item){return item==60011;},plain);rejects([&]{conflicting.project(1,ambiguous.characters[0],1,ambiguous.scalar(1));});
}
void malformed_instance_evidence(){
    for(const auto mutation:{
        "UPDATE character_weapon_slot_metadata SET logical20=zeroblob(20)",
        "UPDATE character_weapon_slot_metadata SET revision=revision+1",
        "UPDATE character_weapon_slot_metadata SET source_sha256=printf('%064d',0)",
        "UPDATE character_weapon_slot_metadata SET client_sha256=printf('%064d',0)",
        "UPDATE character_weapon_slot_metadata SET origin='EMPTY_SLOT_POLICY'",
        "UPDATE character_weapon_slot_metadata SET provenance='a'||char(0)||'b'",
        "UPDATE diagnostic_inventory_slots SET count=127 WHERE slot=0"}){
        Fixture f;f.instance(0,60010,0xa1);f.sql("PRAGMA ignore_check_constraints=ON");f.sql(mutation);auto service=f.service();const auto changes=sqlite3_total_changes(f.raw);rejects([&]{service.project(1,f.characters[0],0,f.scalar(0));});require(sqlite3_total_changes(f.raw)==changes,"Corrupt overlay reader repaired or wrote storage");
    }
    Fixture gem;gem.instance(0,16055,0xb2);gem.sql("UPDATE character_teleport_gem_metadata SET metadata20=CAST(substr(metadata20,1,3)||X'00'||substr(metadata20,5) AS BLOB)");auto service=gem.service();rejects([&]{service.project(1,gem.characters[0],0,gem.scalar(0));});
    Fixture armor_cell;armor_cell.instance(0,60011,0xc3);armor_cell.scalar(0,0,0,7);auto armor_service=armor_cell.service();rejects([&]{armor_service.project(1,armor_cell.characters[0],0,armor_cell.scalar(0));});
    for(const auto family:{0,1,3,8,63}){
        Fixture wrong_family;wrong_family.instance(0,60011,0xc3);wrong_family.sql("DROP TRIGGER armor_update_guard;PRAGMA ignore_check_constraints=ON");
        auto bytes=RecoveredInventoryProjection::Metadata{};bytes.fill(0xc3);bytes[0]=static_cast<std::uint8_t>(60011);bytes[1]=static_cast<std::uint8_t>(60011>>8);bytes[2]=static_cast<std::uint8_t>(0x80u|family);
        sqlite_detail::Statement update(wrong_family.raw,"UPDATE character_armor_slot_metadata SET logical20=?");update.bind_blob(1,bytes);update.done();auto wrong_service=wrong_family.service();rejects([&]{wrong_service.project(1,wrong_family.characters[0],0,wrong_family.scalar(0));});
    }
    Fixture transfigured;auto bytes=transfigured.instance(0,60011,0xc3);bytes[2]=0x9a;sqlite_detail::Statement update(transfigured.raw,"UPDATE character_armor_slot_metadata SET logical20=?");update.bind_blob(1,bytes);update.done();auto armor26=transfigured.service();require(armor26.project(1,transfigured.characters[0],0,transfigured.scalar(0))==RecoveredInventoryProjection::encode({0,1,bytes}).value(),"Armor family26 or high flags were flattened");
}
void planned_scalar_projection(){
    Fixture f;f.scalar(0,3107,127,4);const auto w=f.instance(1,60010,0xa1);f.instance(2,60011,0xb2);f.instance(3,16055,0xc3);f.instance(4,0,0xd4);auto service=f.service();
    const auto before=f.scalar(0);auto after=before;after.count=100;++after.revision;const auto changes=sqlite3_total_changes(f.raw);
    require(service.project_planned(1,f.characters[0],0,before,after)==plain(0,after),"Planned plain count projected from old storage instead of outcome");rejects([&]{service.project(1,f.characters[0],0,after);});
    require(service.project_planned(1,f.characters[0],1,f.scalar(1),f.scalar(1))==RecoveredInventoryProjection::encode({1,1,w}).value(),"Unchanged instance in complete planned bag was flattened");
    for(unsigned slot=1;slot<=3;++slot){const auto instance=f.scalar(slot);auto cleared=instance;cleared.item_id=0;cleared.count=0;++cleared.revision;rejects([&]{service.project_planned(1,f.characters[0],static_cast<std::uint8_t>(slot),instance,cleared);});}
    for(const auto item:{60010,60011,16055}){auto instance=after;instance.item_id=static_cast<std::uint16_t>(item);instance.count=1;rejects([&]{service.project_planned(1,f.characters[0],0,before,instance);});}
    auto bad_revision=after;++bad_revision.revision;rejects([&]{service.project_planned(1,f.characters[0],0,before,bad_revision);});
    const auto empty=f.scalar(4);auto acquired=empty;acquired.item_id=3107;acquired.count=1;++acquired.revision;require(service.project_planned(1,f.characters[0],4,empty,acquired)==plain(4,acquired),"Legacy empty overlay prevents planned ordinary scalar receipt");
    require(f.scalar(0)==before&&f.scalar(4)==empty&&sqlite3_total_changes(f.raw)==changes,"Planned rendering committed or granted its proposal");
    // A bad original scalar encoder cannot emit another player's cell/count.
    auto bad_encoder=OwnedBagProjectionService(f.raw,armor,weapon,[](std::uint8_t,const auto&){return std::vector<std::uint8_t>{0x41,0,0,0,0};});rejects([&]{bad_encoder.project(1,f.characters[0],0,before);});
}
void transaction_proof_and_trigger_rollback(){
    {
        Fixture f;f.scalar(0,3107,10,4);f.instance(1,60010,0xa1);f.instance(2,60011,0xb2);f.instance(3,16055,0xc3);f.instance(4,0,0xd4);f.instance(34,60010,0xe5);auto service=f.service();const auto proof=service.capture_proof(1,f.characters[0]);
        const auto changes_before=sqlite3_total_changes(f.raw);rejects([&]{service.verify_proof_in_transaction(proof);});rejects([&]{service.verify_planned_in_transaction(proof,{});});require(sqlite3_total_changes(f.raw)==changes_before,"Outside-transaction proof check wrote storage");
        const auto before=f.scalar(0),empty=f.scalar(4);auto after=before;after.count=8;++after.revision;auto receipt=empty;receipt.item_id=3107;receipt.count=1;++receipt.revision;
        const std::array<OwnedBagProjectionService::ScalarChange,2> changes{{{0,before,after},{4,empty,receipt}}};
        {sqlite_detail::Transaction tx(f.raw);service.verify_proof_in_transaction(proof);f.scalar(0,after.item_id,after.count,after.revision);f.scalar(4,receipt.item_id,receipt.count,receipt.revision);service.verify_planned_in_transaction(proof,changes);tx.commit();}
        const auto current=service.capture_proof(1,f.characters[0]);require(current.snapshot().armor==proof.snapshot().armor&&current.snapshot().gems==proof.snapshot().gems&&current.snapshot().weapons.size()+1==proof.snapshot().weapons.size(),"Legitimate scalar proof changed full instance or missed empty weapon retirement");
        rejects([&]{sqlite_detail::Transaction tx(f.raw);service.verify_proof_in_transaction(proof);tx.commit();});
        auto full=f.scalar(1),cleared=full;cleared.item_id=0;cleared.count=0;++cleared.revision;const std::array<OwnedBagProjectionService::ScalarChange,1> instance_change{{{1,full,cleared}}};rejects([&]{sqlite_detail::Transaction tx(f.raw);service.verify_planned_in_transaction(current,instance_change);tx.commit();});
    }
    unsigned trigger_index=0;for(const auto mutation:{
        "UPDATE character_weapon_slot_metadata SET logical20=CAST(substr(logical20,1,19)||X'7F' AS BLOB) WHERE character_id=NEW.character_id AND slot=34;",
        "UPDATE character_teleport_gem_metadata SET metadata20=CAST(substr(metadata20,1,19)||X'7F' AS BLOB) WHERE character_id=NEW.character_id AND slot=3;",
        "UPDATE character_armor_slot_metadata SET logical20=CAST(substr(logical20,1,19)||X'7F' AS BLOB) WHERE character_id=NEW.character_id AND slot=2;",
        "UPDATE character_weapon_slot_metadata SET provenance='changed-foreign-evidence' WHERE character_id=NEW.character_id AND slot=34;",
        "UPDATE diagnostic_inventory_slots SET revision=revision+1 WHERE character_id=NEW.character_id AND slot=44;",
        "UPDATE recovered_characters SET account_id=2,slot=1 WHERE id=NEW.character_id;",
        "UPDATE character_weapon_slot_metadata SET revision=revision+1 WHERE character_id=NEW.character_id AND slot=34;",
        "INSERT INTO character_weapon_slot_metadata SELECT character_id,5,zeroblob(20),revision,'EMPTY_SLOT_POLICY','unexpected-empty-overlay',source_sha256,'6bf75ef8ac1e0f6b2240800ff841d205788bd1b6512149584b5386b10f431e98','CUSTOM-0046' FROM diagnostic_inventory_slots WHERE character_id=NEW.character_id AND slot=5;",
        "INSERT INTO character_teleport_gem_metadata SELECT character_id,slot,logical20,revision,'CUSTOM_TEST_NOT_NATIVE','unexpected-cross-overlay',source_sha256,'CUSTOM-0057' FROM character_weapon_slot_metadata WHERE character_id=NEW.character_id AND slot=1;"}){
        ++trigger_index;
        Fixture f;f.scalar(0,3107,10,4);f.instance(1,60010,0xa1);f.instance(2,60011,0xb2);f.instance(3,16055,0xc3);f.instance(34,60010,0xe5);auto service=f.service();const auto proof=service.capture_proof(1,f.characters[0]),other=service.capture_proof(2,f.characters[1]);
        const auto before=f.scalar(0);auto after=before;after.count=9;++after.revision;const std::array<OwnedBagProjectionService::ScalarChange,1> changes{{{0,before,after}}};
        f.sql(std::string("CREATE TRIGGER corrupt_projection AFTER UPDATE ON diagnostic_inventory_slots WHEN NEW.slot=0 BEGIN ")+mutation+" END");const auto changes_before=sqlite3_total_changes(f.raw);bool wrote=false;
        bool rejected=false;std::string failure;try{sqlite_detail::Transaction tx(f.raw);service.verify_proof_in_transaction(proof);f.scalar(0,after.item_id,after.count,after.revision);wrote=true;service.verify_planned_in_transaction(proof,changes);tx.commit();}catch(const DatabaseError& error){rejected=true;failure=error.what();}
        require(rejected,"Mutation proof unexpectedly accepted trigger");
        if(!wrote||sqlite3_total_changes(f.raw)<changes_before+2)throw std::runtime_error("Mutation trigger "+std::to_string(trigger_index)+" was not actually exercised: wrote="+std::to_string(wrote)+" changes="+std::to_string(sqlite3_total_changes(f.raw)-changes_before)+" rejection="+failure);
        require(service.capture_proof(1,f.characters[0]).snapshot()==proof.snapshot()&&service.capture_proof(2,f.characters[1]).snapshot()==other.snapshot(),"Postwrite proof failure did not rollback complete owner/foreign instance state");
    }
}
}
int main(){try{full_instances_and_owner();missing_and_conflicting_metadata();malformed_instance_evidence();planned_scalar_projection();transaction_proof_and_trigger_rollback();std::cout<<"Owner-bound full weapon/armor/gem20, explicit-empty/plain127, stale/cross-overlay/evidence denial, planned scalar projection and transactional full-owner proof/trigger rollback passed; integration/live OPEN\n";}catch(const std::exception& error){std::cerr<<error.what()<<'\n';return 1;}}
