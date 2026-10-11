#include "db/SqliteArmorSlotRepository.h"
#include "db/SqliteSupport.h"
#include "db/SqliteWeaponSlotRepository.h"
#include "protocol/RecoveredArmorInstance.h"
#include <algorithm>
#include <limits>
#include <utility>

namespace god2 {
namespace {
void require(bool ok,const char* message){if(!ok)throw DatabaseError(message);}
constexpr auto revision_limit=static_cast<std::uint64_t>(std::numeric_limits<std::int64_t>::max());
bool domain(std::uint8_t slot){return slot<34;}
bool hash(const std::string& text){return text.size()==64&&text.find_first_not_of("0123456789abcdef")==std::string::npos;}
bool evidence(const std::string& value){return !value.empty()&&value.size()<=512&&value.find('\0')==std::string::npos;}
std::uint16_t key(const std::array<std::uint8_t,20>& b){return static_cast<std::uint16_t>(b[0]|(std::uint16_t{b[1]}<<8));}
struct ReadScope {
    sqlite3* db;bool owns,finished=false;
    explicit ReadScope(sqlite3* value):db(value),owns(sqlite3_get_autocommit(value)!=0){if(owns)sqlite_detail::execute(db,"BEGIN");}
    ~ReadScope(){if(owns&&!finished)sqlite3_exec(db,"ROLLBACK",nullptr,nullptr,nullptr);}
    void finish(){if(owns)sqlite_detail::execute(db,"COMMIT");finished=true;}
};
template<class T>const T* overlay(const std::vector<T>& values,std::uint8_t slot){
    const auto found=std::find_if(values.begin(),values.end(),[&](const auto& row){return row.slot==slot;});
    return found==values.end()?nullptr:&*found;
}
std::vector<ArmorForeignOverlay> foreign(sqlite3* db,std::uint64_t character,bool weapons){
    sqlite_detail::Statement read(db,weapons?
        "SELECT slot,logical20,revision,origin,provenance,source_sha256,client_sha256,design_id FROM character_weapon_slot_metadata WHERE character_id=? ORDER BY slot":
        "SELECT slot,metadata20,revision,origin,provenance,source_sha256,'',design_id FROM character_teleport_gem_metadata WHERE character_id=? ORDER BY slot");
    read.bind_id(1,character);std::vector<ArmorForeignOverlay> rows;
    while(read.row()){
        ArmorForeignOverlay value;value.slot=read.number<std::uint8_t>(0);
        const auto bytes=read.blob(1,20,20);std::copy(bytes.begin(),bytes.end(),value.logical20.begin());
        value.revision=read.number<std::uint64_t>(2);value.origin=read.text(3);value.provenance=read.text(4);
        value.source_sha256=read.text(5);value.client_sha256=read.text(6);value.design_id=read.text(7);rows.push_back(std::move(value));
    }
    return rows;
}
}
std::string SqliteArmorSlotRepository::schema(){return R"SQL(
CREATE TABLE character_armor_slot_metadata(
 character_id INTEGER NOT NULL,
 slot INTEGER NOT NULL CHECK(typeof(slot)='integer' AND slot BETWEEN 0 AND 33),
 logical20 BLOB NOT NULL CHECK(typeof(logical20)='blob' AND length(logical20)=20),
 revision INTEGER NOT NULL CHECK(typeof(revision)='integer' AND revision>0),
 origin TEXT NOT NULL CHECK(origin IN ('NATIVE_CAPTURE_VERIFIED','CUSTOM_TEST_NOT_NATIVE')),
 provenance TEXT NOT NULL CHECK(typeof(provenance)='text' AND length(CAST(provenance AS BLOB)) BETWEEN 1 AND 512 AND instr(provenance,char(0))=0),
 source_sha256 TEXT NOT NULL CHECK(source_sha256='70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731'),
 client_sha256 TEXT NOT NULL CHECK(client_sha256='c5d8f79baa36879851703ac05d2b5caddf44a907677f7de114f568eeaf14f575'),
 design_id TEXT NOT NULL CHECK(design_id='CUSTOM-0066'),
 PRIMARY KEY(character_id,slot),
 FOREIGN KEY(character_id,slot) REFERENCES diagnostic_inventory_slots(character_id,slot) ON DELETE CASCADE
);
CREATE TRIGGER armor_insert_guard BEFORE INSERT ON character_armor_slot_metadata BEGIN
 SELECT CASE WHEN NOT EXISTS(SELECT 1 FROM diagnostic_inventory_slots WHERE character_id=NEW.character_id AND slot=NEW.slot AND count=1 AND revision=NEW.revision AND source_sha256=NEW.source_sha256 AND design_id='CUSTOM-0015' AND hex(substr(NEW.logical20,1,2))=printf('%02X%02X',item_id&255,(item_id>>8)&255)) THEN RAISE(ABORT,'Armor scalar/instance mismatch') END;
 SELECT CASE WHEN EXISTS(SELECT 1 FROM character_weapon_slot_metadata WHERE character_id=NEW.character_id AND slot=NEW.slot) OR EXISTS(SELECT 1 FROM character_teleport_gem_metadata WHERE character_id=NEW.character_id AND slot=NEW.slot) THEN RAISE(ABORT,'Armor overlay collision') END;
END;
CREATE TRIGGER armor_update_guard BEFORE UPDATE ON character_armor_slot_metadata BEGIN
 SELECT CASE WHEN NEW.character_id<>OLD.character_id OR NEW.slot<>OLD.slot OR NOT EXISTS(SELECT 1 FROM diagnostic_inventory_slots WHERE character_id=NEW.character_id AND slot=NEW.slot AND count=1 AND revision=NEW.revision AND source_sha256=NEW.source_sha256 AND design_id='CUSTOM-0015' AND hex(substr(NEW.logical20,1,2))=printf('%02X%02X',item_id&255,(item_id>>8)&255)) THEN RAISE(ABORT,'Armor scalar/instance mismatch') END;
 SELECT CASE WHEN EXISTS(SELECT 1 FROM character_weapon_slot_metadata WHERE character_id=NEW.character_id AND slot=NEW.slot) OR EXISTS(SELECT 1 FROM character_teleport_gem_metadata WHERE character_id=NEW.character_id AND slot=NEW.slot) THEN RAISE(ABORT,'Armor overlay collision') END;
END;
CREATE TRIGGER weapon_armor_insert_guard BEFORE INSERT ON character_weapon_slot_metadata WHEN EXISTS(SELECT 1 FROM character_armor_slot_metadata WHERE character_id=NEW.character_id AND slot=NEW.slot) BEGIN SELECT RAISE(ABORT,'Weapon/armor overlay collision'); END;
CREATE TRIGGER weapon_armor_update_guard BEFORE UPDATE ON character_weapon_slot_metadata WHEN EXISTS(SELECT 1 FROM character_armor_slot_metadata WHERE character_id=NEW.character_id AND slot=NEW.slot) BEGIN SELECT RAISE(ABORT,'Weapon/armor overlay collision'); END;
CREATE TRIGGER gem_armor_insert_guard BEFORE INSERT ON character_teleport_gem_metadata WHEN EXISTS(SELECT 1 FROM character_armor_slot_metadata WHERE character_id=NEW.character_id AND slot=NEW.slot) BEGIN SELECT RAISE(ABORT,'Gem/armor overlay collision'); END;
CREATE TRIGGER gem_armor_update_guard BEFORE UPDATE ON character_teleport_gem_metadata WHEN EXISTS(SELECT 1 FROM character_armor_slot_metadata WHERE character_id=NEW.character_id AND slot=NEW.slot) BEGIN SELECT RAISE(ABORT,'Gem/armor overlay collision'); END;
)SQL";}
SqliteArmorSlotRepository::SqliteArmorSlotRepository(sqlite3* db,QualifyArmor qualify,QualifyInstance instance):db_(db),qualify_(std::move(qualify)),qualify_instance_(std::move(instance)){
    require(db_&&bool(qualify_),"Armor repository requires database and mapping qualifier");
}
void SqliteArmorSlotRepository::owner(std::uint64_t account,std::uint64_t character){
    require(account&&account<=revision_limit&&character&&character<=revision_limit,"Invalid armor owner");
    sqlite_detail::Statement read(db_,"SELECT 1 FROM recovered_characters WHERE account_id=? AND id=?");
    read.bind_id(1,account);read.bind_id(2,character);require(read.row(),"Armor owner rejected");
}
std::optional<std::uint8_t> SqliteArmorSlotRepository::target(std::uint16_t item) const{
    const auto mapped=qualify_(item);require(!mapped||(*mapped>=30&&*mapped<=33),"Armor mapping outside qualified domain");return mapped;
}
void SqliteArmorSlotRepository::validate(const ArmorSnapshot& saved) const{
    require(saved.account&&saved.account<=revision_limit&&saved.character&&saved.character<=revision_limit,"Invalid armor snapshot owner");
    for(std::size_t i=0;i<saved.scalar.size();++i)if(const auto& row=saved.scalar[i])
        require(row->revision&&row->revision<=revision_limit&&row->count<=127&&((row->count==0)==(row->item_id==0))&&hash(row->source_sha256),"Invalid observed armor scalar");
    std::uint8_t previous=0;bool first=true;
    for(const auto& row:saved.armor){
        require(domain(row.slot)&&(first||row.slot>previous),"Armor metadata duplicate/out-of-domain");first=false;previous=row.slot;
        const auto& scalar=saved.scalar[row.slot];const auto mapped=target(row.item_id);
        require(scalar&&scalar->count==1&&row.count==1&&row.metadata_present&&mapped&&RecoveredArmorInstance::armor_family(row.logical20)&&(!qualify_instance_||qualify_instance_(row.item_id,row.logical20))&&scalar->item_id==row.item_id&&key(row.logical20)==row.item_id&&
            scalar->revision==row.revision&&scalar->source_sha256==source_sha256&&
            (row.slot<30||row.slot==*mapped)&&(row.origin=="NATIVE_CAPTURE_VERIFIED"||row.origin=="CUSTOM_TEST_NOT_NATIVE")&&evidence(row.provenance),"Unqualified armor instance");
        require(!overlay(saved.weapons,row.slot)&&!overlay(saved.gems,row.slot),"Armor has foreign metadata collision");
    }
    const auto check_foreign=[&](const auto& rows,bool weapons){
        std::uint8_t last=0;bool initial=true;
        for(const auto& row:rows){
            require((weapons?(row.slot<30||row.slot==34):row.slot<30)&&(initial||row.slot>last),"Foreign armor observation out-of-domain/duplicate");initial=false;last=row.slot;
            const auto& scalar=saved.scalar[row.slot];
            require(scalar&&row.revision==scalar->revision&&key(row.logical20)==scalar->item_id&&row.source_sha256==source_sha256&&scalar->source_sha256==row.source_sha256&&evidence(row.provenance),"Foreign armor observation orphan/version conflict");
            if(weapons){require(row.design_id=="CUSTOM-0046"&&row.client_sha256==SqliteWeaponSlotRepository::client_sha256&&
                (scalar->count?scalar->count==1&&(row.origin=="NATIVE_CAPTURE_VERIFIED"||row.origin=="CUSTOM_TEST_NOT_NATIVE"):row.origin=="EMPTY_SLOT_POLICY"),"Foreign weapon observation malformed");}
            else require(scalar->count==1&&row.design_id=="CUSTOM-0057"&&(row.origin=="NATIVE_CAPTURE_VERIFIED"||row.origin=="CUSTOM_TEST_NOT_NATIVE"),"Foreign gem observation malformed");
            require(!overlay(saved.armor,row.slot)&&!(weapons?overlay(saved.gems,row.slot):overlay(saved.weapons,row.slot)),"Foreign metadata domains collide");
        }
    };
    check_foreign(saved.weapons,true);check_foreign(saved.gems,false);
    for(std::uint8_t i=0;i<34;++i)if(const auto& scalar=saved.scalar[i];scalar&&scalar->count&&target(scalar->item_id))
        require(overlay(saved.armor,i)!=nullptr,"Qualified armor missing complete instance metadata");
}
ArmorSnapshot SqliteArmorSlotRepository::load_snapshot(std::uint64_t account,std::uint64_t character){
    ReadScope scope(db_);owner(account,character);ArmorSnapshot saved;saved.account=account;saved.character=character;
    sqlite_detail::Statement read(db_,"SELECT slot,item_id,count,revision,source_sha256,design_id FROM diagnostic_inventory_slots WHERE character_id=? ORDER BY slot");read.bind_id(1,character);
    while(read.row()){
        const auto index=read.number<std::uint8_t>(0);require(index<50&&!saved.scalar[index]&&read.text(5)=="CUSTOM-0015","Armor scalar domain/provenance invalid");
        saved.scalar[index]=StoredInventorySlot{read.number<std::uint16_t>(1),read.number<std::uint8_t>(2),read.number<std::uint64_t>(3),read.text(4)};
    }
    sqlite_detail::Statement metadata(db_,"SELECT slot,logical20,revision,origin,provenance,source_sha256,client_sha256,design_id FROM character_armor_slot_metadata WHERE character_id=? ORDER BY slot");metadata.bind_id(1,character);
    while(metadata.row()){
        StoredArmorSlot row;row.slot=metadata.number<std::uint8_t>(0);row.count=1;row.metadata_present=true;
        const auto bytes=metadata.blob(1,20,20);std::copy(bytes.begin(),bytes.end(),row.logical20.begin());row.item_id=key(row.logical20);
        row.revision=metadata.number<std::uint64_t>(2);row.origin=metadata.text(3);row.provenance=metadata.text(4);
        require(metadata.text(5)==source_sha256&&metadata.text(6)==client_sha256&&metadata.text(7)==design_id,"Armor metadata source/build mismatch");saved.armor.push_back(std::move(row));
    }
    saved.weapons=foreign(db_,character,true);saved.gems=foreign(db_,character,false);validate(saved);scope.finish();return saved;
}
std::optional<StoredArmorSlot> SqliteArmorSlotRepository::inspect(const ArmorSnapshot& saved,std::uint8_t index) const{
    require(domain(index),"Armor slot outside domain");const auto& scalar=saved.scalar[index];if(!scalar)return {};
    if(const auto* row=overlay(saved.armor,index))return *row;
    if(scalar->count)return {};
    require(!overlay(saved.gems,index),"Empty armor target has gem metadata");
    if(const auto* other=overlay(saved.weapons,index))require(other->origin=="EMPTY_SLOT_POLICY"&&other->revision==scalar->revision,"Empty armor target has occupied weapon metadata");
    return StoredArmorSlot{index,0,0,scalar->revision,{},"","",false};
}
std::optional<StoredArmorSlot> SqliteArmorSlotRepository::load(std::uint64_t account,std::uint64_t character,std::uint8_t index){return inspect(load_snapshot(account,character),index);}
std::vector<StoredArmorSlot> SqliteArmorSlotRepository::load_saved(std::uint64_t account,std::uint64_t character){
    auto saved=load_snapshot(account,character);std::vector<StoredArmorSlot> rows;
    for(std::uint8_t index=0;index<34;++index)if(auto row=inspect(saved,index))rows.push_back(std::move(*row));return rows;
}
ArmorSlotMove SqliteArmorSlotRepository::plan(const ArmorSnapshot& expected,std::uint8_t source,std::uint8_t destination) const{
    validate(expected);require(domain(source)&&domain(destination)&&source!=destination,"Invalid armor move domain");
    const auto from=inspect(expected,source),to=inspect(expected,destination);
    require(from&&to&&from->count==1&&from->metadata_present,"Armor transfer needs a complete source and owned destination");
    require(expected.scalar[source]->source_sha256==source_sha256&&expected.scalar[destination]->source_sha256==source_sha256&&
        from->revision<revision_limit&&to->revision<revision_limit,"Armor transfer source/revision invalid");
    const auto mapped=target(from->item_id);require(mapped.has_value(),"Armor source not qualified");
    if(source>=30||destination>=30){const auto equipped=source>=30?source:destination;
        require((source<30||destination<30)&&*mapped==equipped&&(!to->count||target(to->item_id)==mapped),"Armor equipment exchange crosses mapped parts");}
    ArmorSlotMove next{*to,*from,expected};
    next.source.slot=source;next.source.revision=from->revision+1;
    next.destination.slot=destination;next.destination.revision=to->revision+1;
    if(!to->count)next.source={source,0,0,from->revision+1,{},"","",false};
    for(const auto* row:{&next.source,&next.destination}){
        auto& scalar=*next.after.scalar[row->slot];scalar.item_id=row->item_id;scalar.count=row->count;scalar.revision=row->revision;
    }
    std::erase_if(next.after.armor,[&](const auto& row){return row.slot==source||row.slot==destination;});
    if(next.source.count)next.after.armor.push_back(next.source);if(next.destination.count)next.after.armor.push_back(next.destination);
    std::sort(next.after.armor.begin(),next.after.armor.end(),[](const auto& a,const auto& b){return a.slot<b.slot;});
    // Preserve the original empty-weapon retirement semantics exactly. No
    // occupied foreign overlay is admitted or deleted by this repository.
    std::erase_if(next.after.weapons,[&](const auto& row){return (row.slot==source||row.slot==destination)&&row.origin=="EMPTY_SLOT_POLICY";});
    validate(next.after);return next;
}
ArmorSlotMove SqliteArmorSlotRepository::move(const ArmorSnapshot& expected,std::uint8_t source,std::uint8_t destination,const Prepare& prepare){
    require(bool(prepare),"Armor transfer requires prepared response");auto next=plan(expected,source,destination);
    sqlite_detail::Transaction transaction(db_);owner(expected.account,expected.character);
    require(load_snapshot(expected.account,expected.character)==expected,"Armor complete snapshot conflict");
    const auto no_pending_battle=[&]{sqlite_detail::Statement pending(db_,"SELECT 1 FROM battle_reservations r LEFT JOIN battle_settlements s ON s.battle_id=r.id WHERE r.character_id=? AND s.battle_id IS NULL LIMIT 1");pending.bind_id(1,expected.character);require(!pending.row(),"Armor transfer during pending battle");};
    no_pending_battle();
    for(const auto index:{source,destination})if(const auto* row=overlay(expected.armor,index)){
        sqlite_detail::Statement erase(db_,"DELETE FROM character_armor_slot_metadata WHERE character_id=? AND slot=? AND logical20=? AND revision=? AND origin=? AND provenance=? AND source_sha256=? AND client_sha256=? AND design_id='CUSTOM-0066'");
        erase.bind_id(1,expected.character);erase.bind(2,index);erase.bind_blob(3,row->logical20);erase.bind_id(4,row->revision);erase.bind(5,row->origin);erase.bind(6,row->provenance);erase.bind(7,source_sha256);erase.bind(8,client_sha256);erase.done();require(sqlite3_changes(db_)==1,"Armor metadata CAS removal failed");
    }
    for(const auto* after:{&next.source,&next.destination}){
        const auto& before=*expected.scalar[after->slot];
        sqlite_detail::Statement update(db_,"UPDATE diagnostic_inventory_slots SET item_id=?,count=?,revision=? WHERE character_id=? AND slot=? AND item_id=? AND count=? AND revision=? AND source_sha256=? AND design_id='CUSTOM-0015'");
        update.bind(1,after->item_id);update.bind(2,after->count);update.bind_id(3,after->revision);update.bind_id(4,expected.character);update.bind(5,after->slot);
        update.bind(6,before.item_id);update.bind(7,before.count);update.bind_id(8,before.revision);update.bind(9,before.source_sha256);update.done();require(sqlite3_changes(db_)==1,"Armor scalar CAS failed");
        if(after->count){
            sqlite_detail::Statement insert(db_,"INSERT INTO character_armor_slot_metadata(character_id,slot,logical20,revision,origin,provenance,source_sha256,client_sha256,design_id) VALUES(?,?,?,?,?,?,?,?,'CUSTOM-0066')");
            insert.bind_id(1,expected.character);insert.bind(2,after->slot);insert.bind_blob(3,after->logical20);insert.bind_id(4,after->revision);insert.bind(5,after->origin);insert.bind(6,after->provenance);insert.bind(7,source_sha256);insert.bind(8,client_sha256);insert.done();require(sqlite3_changes(db_)==1,"Armor metadata install failed");
        }
    }
    const auto verify=[&]{require(load_snapshot(expected.account,expected.character)==next.after,"Armor full scalar/overlay readback failed");};
    verify();prepare(next);verify();no_pending_battle();transaction.commit();return next;
}
}
