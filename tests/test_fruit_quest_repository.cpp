#include "db/SqliteFruitQuestRepository.h"
#include "db/SqliteSupport.h"
#include "db/NativeFruitQuestSources.h"
#include "game/FruitVillageQuestRules.h"
#include <chrono>
#include <filesystem>
#include <iostream>
#include <memory>
#include <string>

using namespace god2;
namespace q=InferredQuestRules;
namespace f=FruitVillageQuestRules;
namespace {
using Db=std::unique_ptr<sqlite3,decltype(&sqlite3_close)>;
unsigned checks{};
void require(bool value,const char* message){++checks;if(!value)throw std::runtime_error(message);}
template<class F> void rejects(F&& f){bool rejected=false;try{f();}catch(const DatabaseError&){rejected=true;}require(rejected,"Expected DatabaseError");}
Db open(const char* path){sqlite3* raw=nullptr;const auto code=sqlite3_open(path,&raw);Db db(raw,sqlite3_close);require(code==SQLITE_OK,"Open failed");sqlite_detail::execute(raw,"PRAGMA foreign_keys=ON");return db;}
Db copy(sqlite3* source,const char* path=":memory:") {
    auto db=open(path);auto* backup=sqlite3_backup_init(db.get(),"main",source,"main");require(backup!=nullptr,"Backup init");
    const auto step=sqlite3_backup_step(backup,-1);const auto done=sqlite3_backup_finish(backup);require(step==SQLITE_DONE&&done==SQLITE_OK,"Backup failed");return db;
}
std::vector<std::uint8_t> image(sqlite3* db){sqlite3_int64 size=0;auto* raw=sqlite3_serialize(db,"main",&size,0);require(raw&&size>0,"Serialize fixture");std::vector<std::uint8_t> bytes(raw,raw+size);sqlite3_free(raw);return bytes;}
std::int64_t number(sqlite3* db,const char* sql){sqlite_detail::Statement s(db,sql);require(s.row(),"No scalar");return s.integer(0);}
void position(sqlite3* db,std::uint32_t mission){const auto* d=f::find(mission);require(d!=nullptr,"Test descriptor");sqlite_detail::Statement s(db,"UPDATE recovered_positions SET area=13,scene=12,x=?,y=?,revision=revision+1 WHERE character_id=4");s.bind(1,d->source_x);s.bind(2,d->source_y);s.done();}
void initialize(sqlite3* db) {
    // Disposable minimal compatibility schema; actual migration31 schema is
    // executed verbatim below. Source rows are imported separately from current
    // pinned Mission_data, never fabricated as418 placeholders.
    sqlite_detail::execute(db,R"SQL(
CREATE TABLE fruit_test_fixture_marker(value TEXT NOT NULL);
INSERT INTO fruit_test_fixture_marker VALUES('DISPOSABLE-CUSTOM-0051-TEST-ONLY');
CREATE TABLE schema_migrations(version INTEGER PRIMARY KEY,name TEXT NOT NULL);
INSERT INTO schema_migrations VALUES(14,'native_quest_descriptions'),(23,'native_quest_source_catalog');
CREATE TABLE native_data_sources(dataset_id TEXT PRIMARY KEY,source_path TEXT,source_sha256 TEXT,decoded_sha256 TEXT,native_image_sha256 TEXT,source_section TEXT,loader_rva TEXT,lookup_rva TEXT,row_count INTEGER);
CREATE TABLE native_quest_descriptions(dataset_id TEXT,mission_index INTEGER,description_index INTEGER,description_count INTEGER,source_line INTEGER,record_sha256 TEXT,raw_record BLOB,PRIMARY KEY(dataset_id,mission_index,description_index));
CREATE TABLE native_quest_definitions(dataset_id TEXT,mission_index INTEGER,description_count INTEGER,source_line INTEGER,record_sha256 TEXT,raw_record BLOB,title_bytes BLOB,PRIMARY KEY(dataset_id,mission_index));
CREATE TABLE native_daily_quest_source(record_index INTEGER PRIMARY KEY,source_path TEXT,source_sha256 TEXT,decoded_sha256 TEXT,source_line INTEGER,record_sha256 TEXT,raw_record BLOB,field_count INTEGER,authority TEXT);
CREATE TABLE native_quest_requirement_display(serial INTEGER PRIMARY KEY);
CREATE TABLE recovered_characters(id INTEGER PRIMARY KEY,account_id INTEGER NOT NULL);
INSERT INTO recovered_characters VALUES(4,1),(5,2);
CREATE TABLE recovered_positions(character_id INTEGER PRIMARY KEY,area INTEGER,scene INTEGER,x INTEGER,y INTEGER,revision INTEGER);
INSERT INTO recovered_positions VALUES(4,13,12,108,110,1),(5,13,12,108,110,1);
CREATE TABLE character_role_snapshots(character_id INTEGER PRIMARY KEY,logical BLOB,revision INTEGER,design_id TEXT);
CREATE TABLE character_resources(character_id INTEGER PRIMARY KEY,hp INTEGER,mp INTEGER,max_hp INTEGER,max_mp INTEGER,revision INTEGER,design_id TEXT);
INSERT INTO character_resources VALUES(4,77,55,100,80,11,'CUSTOM-0012'),(5,66,44,100,80,12,'CUSTOM-0012');
CREATE TABLE character_experience(character_id INTEGER PRIMARY KEY,total INTEGER CHECK(total>=0),design_id TEXT CHECK(design_id='CUSTOM-0012'));
CREATE TABLE diagnostic_inventory_slots(character_id INTEGER,slot INTEGER CHECK(slot BETWEEN 0 AND 49),item_id INTEGER CHECK(item_id BETWEEN 0 AND 65535),count INTEGER CHECK(count BETWEEN 0 AND 127),revision INTEGER CHECK(revision>0),source_sha256 TEXT,design_id TEXT CHECK(design_id='CUSTOM-0015'),PRIMARY KEY(character_id,slot),CHECK((count=0 AND item_id=0)OR(count>0 AND item_id>0)));
CREATE TABLE character_weapon_slot_metadata(character_id INTEGER,slot INTEGER,logical20 BLOB,revision INTEGER,origin TEXT,provenance TEXT,source_sha256 TEXT,client_sha256 TEXT,design_id TEXT,PRIMARY KEY(character_id,slot),FOREIGN KEY(character_id,slot) REFERENCES diagnostic_inventory_slots(character_id,slot));
CREATE TRIGGER retire_empty_weapon_overlay AFTER UPDATE OF item_id,count,revision ON diagnostic_inventory_slots BEGIN DELETE FROM character_weapon_slot_metadata WHERE character_id=NEW.character_id AND slot=NEW.slot AND origin='EMPTY_SLOT_POLICY'; END;
CREATE TABLE battle_reservations(id INTEGER PRIMARY KEY,character_id INTEGER,resource_revision INTEGER,design_id TEXT);
CREATE TABLE battle_settlements(battle_id INTEGER PRIMARY KEY,request TEXT,resource_revision INTEGER,total_experience INTEGER,design_id TEXT);
CREATE TABLE character_quest_journals(character_id INTEGER PRIMARY KEY,values_blob BLOB CHECK(length(values_blob)=60),revision INTEGER CHECK(revision>0),origin TEXT CHECK(origin IN ('NATIVE_CAPTURE_VERIFIED','CUSTOM_TEST_NOT_NATIVE')),provenance TEXT,design_id TEXT CHECK(design_id='CUSTOM-0041'));
CREATE TABLE diagnostic_quest_journals(character_id INTEGER PRIMARY KEY,slots BLOB,revision INTEGER,design_id TEXT);
INSERT INTO diagnostic_quest_journals VALUES(4,zeroblob(60),23,'CUSTOM-0018');
)SQL");
    sqlite_detail::execute(db,SqliteFruitQuestRepository::schema());
    sqlite_detail::execute(db,NativeFruitQuestSources::schema());
    for(int character:{4,5}) {
        std::array<std::uint8_t,25> logical{};logical[0]=0x22;logical[1]=15;logical[17]=100;logical[21]=80;
        sqlite_detail::Statement r(db,"INSERT INTO character_role_snapshots VALUES(?,?,5,'CUSTOM-0013')");r.bind(1,character);r.bind_blob(2,logical);r.done();
        for(int slot=0;slot<30;++slot){sqlite_detail::Statement b(db,"INSERT INTO diagnostic_inventory_slots VALUES(?,?,0,0,7,?,'CUSTOM-0015')");b.bind(1,character);b.bind(2,slot);b.bind(3,"70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731");b.done();}
    }
    sqlite_detail::execute(db,"UPDATE diagnostic_inventory_slots SET item_id=5098,count=CASE slot WHEN 2 THEN 3 ELSE 4 END WHERE character_id=4 AND slot IN(2,9);UPDATE diagnostic_inventory_slots SET item_id=5091,count=CASE slot WHEN 10 THEN 2 ELSE 4 END WHERE character_id=4 AND slot IN(10,15);UPDATE diagnostic_inventory_slots SET item_id=3464,count=CASE slot WHEN 22 THEN 17 ELSE 4 END WHERE character_id=4 AND slot IN(22,29)");
}
void journal(sqlite3* db,bool full) {
    std::array<std::uint8_t,60> bytes{};
    for(unsigned i=0;i<(full?15u:2u);++i){bytes[i*4]=static_cast<std::uint8_t>(i+1);bytes[i*4+2]=1;}
    sqlite_detail::Statement s(db,"INSERT INTO character_quest_journals VALUES(4,?,13,'NATIVE_CAPTURE_VERIFIED','synthetic enum fixture not a capture','CUSTOM-0041')");s.bind_blob(1,bytes);s.done();
}
void tests(sqlite3* source,const std::string& base_path) {
    require(number(source,"SELECT count(*) FROM fruit_test_fixture_marker WHERE value='DISPOSABLE-CUSTOM-0051-TEST-ONLY'")==1,"Not a disposable test fixture");
    require(number(source,"SELECT count(*) FROM native_quest_definitions")==418&&number(source,"SELECT count(*) FROM native_quest_descriptions")==2014,"Import real native source first");
    // Exercise the actual immutable source guard against every cloned DB.
    unsigned source_calls=0;auto guard=[&](sqlite3* db){return [&,db]{++source_calls;NativeFruitQuestSources(db).require_qualified();};};
    {auto db=copy(source);SqliteFruitQuestRepository r(db.get(),guard(db.get()));require(source_calls==0,"Constructor must be safe before migrations");
     const auto before=image(db.get());const auto v=r.load(1,4,234);require(image(db.get())==before,"Read seeded state");
     require(!v.balance_present&&!v.experience_present&&!v.journal&&v.snapshot.role->experience==0,"Explicit initial-zero view");
     rejects([&]{r.load(2,4,234);});rejects([&]{r.load(1,5,234);});rejects([&]{r.load(1,4,235);});
     require(image(db.get())==before,"Owner/unknown mutation");}
    for(const auto& descriptor:f::descriptors) {
        auto db=copy(source);position(db.get(),descriptor.mission_id);journal(db.get(),false);
        if(descriptor.mission_id==237)sqlite_detail::execute(db.get(),"UPDATE diagnostic_inventory_slots SET count=7 WHERE character_id=4 AND slot=9");
        if(descriptor.mission_id==236)sqlite_detail::execute(db.get(),"INSERT INTO character_experience VALUES(4,123,'CUSTOM-0012')");
        SqliteFruitQuestRepository r(db.get(),guard(db.get()));const auto initial=r.load(1,4,descriptor.mission_id);
        const auto before=image(db.get());
        rejects([&]{r.accept(1,4,descriptor.mission_id,initial,[](const auto&){throw DatabaseError("projection fixture failure");});});
        require(image(db.get())==before,"Accept prepare failure rollback");
        auto accepted=r.accept(1,4,descriptor.mission_id,initial);
        require(accepted.changed_bags.empty()&&!accepted.experience_delta&&!accepted.reputation_delta,"Accept granted reward");
        require(accepted.after.snapshot.quests.at(descriptor.mission_id).phase==q::Phase::Accepted,"Accept phase");
        require(accepted.after.journal->values[0]==0x10001&&accepted.after.journal->values[1]==0x10002&&accepted.after.journal->values[2]==(0x10000|descriptor.mission_id),"Journal unrelated values changed");
        require(accepted.after.journal->revision==14&&accepted.journal_logical.size()==195,"Journal atomic accept projection");
        require(accepted.after.experience_present==initial.experience_present&&accepted.after.snapshot.role->experience==initial.snapshot.role->experience,"Accept seeded XP");
        rejects([&]{r.accept(1,4,descriptor.mission_id,initial);});
        const auto accepted_image=image(db.get());
        rejects([&]{r.submit(1,4,descriptor.mission_id,accepted.after,[](const auto&){throw DatabaseError("submit projection failed");});});
        require(image(db.get())==accepted_image,"Multi-slot/reward/journal rollback after all writes");
        sqlite_detail::execute(db.get(),"CREATE TRIGGER reject_journal BEFORE UPDATE ON character_quest_journals BEGIN SELECT RAISE(ABORT,'test journal reject'); END");
        const auto trigger_before=image(db.get());rejects([&]{r.submit(1,4,descriptor.mission_id,accepted.after);});
        require(image(db.get())==trigger_before,"SQL trigger rollback across all tables");sqlite_detail::execute(db.get(),"DROP TRIGGER reject_journal");
        const auto done=r.submit(1,4,descriptor.mission_id,accepted.after);
        require(done.changed_bags.size()==2,"Expected material split across two slots");
        std::uint32_t debit=0;for(const auto& change:done.changed_bags){debit+=change.before.count-change.after.count;require(change.after.revision==change.before.revision+1,"Bag revision");}
        require(debit==descriptor.quantity&&done.experience_delta==descriptor.experience&&done.reputation_delta==1,"Exact recipe delta");
        require(done.after.snapshot.role->experience==initial.snapshot.role->experience+descriptor.experience&&done.after.snapshot.role->reputation==1,"Stored rewards");
        require(done.after.journal->values[0]==0x10001&&done.after.journal->values[1]==0x10002&&done.after.journal->values[2]==0,"Submit preserves other journal slots");
        require(done.after.role_logical==initial.role_logical&&done.after.role_revision==initial.role_revision,"Saved22 unexpectedly changed");
        require(number(db.get(),"SELECT hp*1000+mp FROM character_resources WHERE character_id=4")==77055,"HPMP mutated");
        require(number(db.get(),"SELECT count(*) FROM character_fruit_quest_progress WHERE character_id=5")==0&&number(db.get(),"SELECT count(*) FROM character_experience WHERE character_id=5")==0,"Other owner mutated");
        const auto receipt=done.after.receipts.at(descriptor.mission_id);
        require(receipt.experience_delta==descriptor.experience&&receipt.experience_was_present==initial.experience_present&&!receipt.token.empty(),"Durable once receipt");
        require(number(db.get(),"SELECT count(*) FROM character_experience WHERE design_id='CUSTOM-0012'")==1,"XP baseline relabeled");
        const auto completed_image=image(db.get());rejects([&]{r.submit(1,4,descriptor.mission_id,done.after);});rejects([&]{r.accept(1,4,descriptor.mission_id,done.after);});
        require(image(db.get())==completed_image,"Replay mutated state");
    }
    {auto db=copy(source);journal(db.get(),true);SqliteFruitQuestRepository r(db.get(),guard(db.get()));auto v=r.load(1,4,234);const auto before=image(db.get());rejects([&]{r.accept(1,4,234,v);});require(image(db.get())==before,"Full journal overwrote/seeded");}
    for(const auto* mutation:{"UPDATE recovered_positions SET x=112 WHERE character_id=4",
                             "UPDATE recovered_positions SET area=2,scene=4 WHERE character_id=4",
                             "INSERT INTO battle_reservations VALUES(1,4,11,'CUSTOM-0012')",
                             "DELETE FROM character_role_snapshots WHERE character_id=4"}) {
        auto db=copy(source);sqlite_detail::execute(db.get(),mutation);SqliteFruitQuestRepository r(db.get(),guard(db.get()));auto v=r.load(1,4,234);auto before=image(db.get());rejects([&]{r.accept(1,4,234,v);});require(image(db.get())==before,"Admission failure mutated rows");
    }
    for(const auto* mutation:{"DELETE FROM diagnostic_inventory_slots WHERE character_id=4 AND slot=29",
                             "UPDATE diagnostic_inventory_slots SET count=1 WHERE character_id=4 AND slot=9",
                             "UPDATE recovered_positions SET x=x+1,revision=revision+1 WHERE character_id=4"}) {
        auto db=copy(source);SqliteFruitQuestRepository r(db.get(),guard(db.get()));auto accepted=r.accept(1,4,234,r.load(1,4,234));sqlite_detail::execute(db.get(),mutation);
        const auto before=image(db.get());rejects([&]{r.submit(1,4,234,accepted.after);});require(image(db.get())==before,"Stale full read set accepted");
        if(std::string(mutation).find("recovered_positions")==std::string::npos){auto current=r.load(1,4,234);rejects([&]{r.submit(1,4,234,current);});require(image(db.get())==before,"Incomplete collection mutated");}
    }
    {auto db=copy(source);SqliteFruitQuestRepository r(db.get(),guard(db.get()));auto accepted=r.accept(1,4,234,r.load(1,4,234));
     q::Instance bytes{};bytes[0]=0xea;bytes[1]=0x13;bytes[19]=0xa5;
     sqlite_detail::Statement m(db.get(),"INSERT INTO character_weapon_slot_metadata VALUES(4,9,?,7,'CUSTOM_TEST_NOT_NATIVE','protected unrelated instance',?,?,'CUSTOM-0046')");m.bind_blob(1,bytes);m.bind(2,"70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731");m.bind(3,std::string(f::client_sha256));m.done();
     auto v=r.load(1,4,234);require(v.snapshot.bag[9]->instance==std::optional{bytes},"Overlay lost");const auto before=image(db.get());rejects([&]{r.submit(1,4,234,v);});require(image(db.get())==before,"Occupied overlay consumed as scalar");}
    {auto db=copy(source);SqliteFruitQuestRepository r(db.get(),[]{throw DatabaseError("source guard rejects");});const auto before=image(db.get());rejects([&]{r.load(1,4,234);});require(image(db.get())==before,"Source failure writes");}
    {auto db=copy(source);sqlite_detail::execute(db.get(),"DELETE FROM qualified_fruit_quest_sources");
     NativeFruitQuestSources source_guard(db.get());require(!source_guard.populated(),"Empty source must be distinguishable");
     rejects([&]{source_guard.require_qualified();});SqliteFruitQuestRepository r(db.get(),guard(db.get()));rejects([&]{r.load(1,4,234);});}
    {auto db=copy(source);sqlite_detail::execute(db.get(),"BEGIN");NativeFruitQuestSources source_guard(db.get());
     source_guard.require_qualified();require(sqlite3_get_autocommit(db.get())==0,"Source guard committed caller transaction");sqlite_detail::execute(db.get(),"ROLLBACK");}
    {auto db=copy(source);sqlite_detail::execute(db.get(),"UPDATE qualified_fruit_quest_sources SET payload=CAST(X'00'||substr(payload,2) AS BLOB)");
     rejects([&]{NativeFruitQuestSources(db.get()).require_qualified();});}
    {auto db=copy(source);SqliteFruitQuestRepository r(db.get(),guard(db.get()));auto v=r.load(1,4,234);const auto before=image(db.get());
     rejects([&]{r.accept(1,4,234,v,[&](const auto&){sqlite_detail::execute(db.get(),"UPDATE character_resources SET hp=1 WHERE character_id=5");});});
     require(image(db.get())==before,"Prepare unrelated-row write did not roll back");}
    for(const auto* sql:{"UPDATE native_quest_definitions SET raw_record=X'00' WHERE mission_index=234",
                         "UPDATE native_quest_descriptions SET raw_record=X'00' WHERE mission_index=236 AND description_index=0"}) {
        auto db=copy(source);sqlite_detail::execute(db.get(),sql);SqliteFruitQuestRepository r(db.get(),guard(db.get()));rejects([&]{r.load(1,4,234);});
    }
    // Real separate connections, stale accept/submit and disk reopen.
    const auto path=base_path+".race-"+std::to_string(std::chrono::steady_clock::now().time_since_epoch().count())+".sqlite";
    require(!std::filesystem::exists(path),"Test race file collision");
    {auto db=copy(source,path.c_str());auto second=open(path.c_str());SqliteFruitQuestRepository a(db.get(),guard(db.get())),b(second.get(),guard(second.get()));
     const auto va=a.load(1,4,234),vb=b.load(1,4,234);auto accepted=a.accept(1,4,234,va);rejects([&]{b.accept(1,4,234,vb);});
     const auto stale=b.load(1,4,234);auto done=a.submit(1,4,234,accepted.after);rejects([&]{b.submit(1,4,234,stale);});require(b.load(1,4,234)==done.after,"Second connection once state");
     second.reset();db.reset();auto reopened=open(path.c_str());SqliteFruitQuestRepository resumed(reopened.get(),guard(reopened.get()));require(resumed.load(1,4,234)==done.after,"Disk resume exact state");}
    require(std::filesystem::remove(path),"Remove own race fixture");
    require(source_calls>20,"Source guard not used");
    std::cout<<"Fruit quest repository: "<<checks<<" checks PASS; real pinned418/2014 source fixture, isolated SQL only\n";
}
}
int main(int argc,char** argv) {
    try {
        if(argc!=3)throw std::runtime_error("Usage: fruit-quest-repository --initialize|--test disposable.db");
        auto db=open(argv[2]);if(std::string(argv[1])=="--initialize")initialize(db.get());
        else if(std::string(argv[1])=="--test")tests(db.get(),argv[2]);else throw std::runtime_error("Invalid mode");return 0;
    }catch(const std::exception& error){std::cerr<<error.what()<<'\n';return 1;}
}
