#include "db/SqliteQuestJournalRepository.h"
#include "db/Migration.h"
#include "db/SqliteSupport.h"
#include "protocol/RecoveredQuestSync.h"
#include <algorithm>
#include <iostream>
#include <limits>
#include <memory>
#include <string>

using namespace god2;
namespace {
int checks{};
void require(bool value,const char* message) {++checks;if(!value)throw std::runtime_error(message);}
template<class F> void rejects(F action) {
    bool rejected=false;
    try {action();} catch(const DatabaseError&) {rejected=true;}
    require(rejected,"Expected DatabaseError");
}
using Db=std::unique_ptr<sqlite3,decltype(&sqlite3_close)>;
Db open(const char* path) {
    sqlite3* raw=nullptr;const auto code=sqlite3_open(path,&raw);Db result(raw,sqlite3_close);
    if(code!=SQLITE_OK)throw std::runtime_error("Unable to open test database");
    sqlite_detail::execute(raw,"PRAGMA foreign_keys=ON");return result;
}
void initialize(sqlite3* db) {
    sqlite_detail::execute(db,"CREATE TABLE schema_migrations(version INTEGER PRIMARY KEY,name TEXT NOT NULL)");
    for(const auto& migration:default_sqlite_migrations()) {
        sqlite_detail::execute(db,migration.sql);
        sqlite_detail::Statement row(db,"INSERT INTO schema_migrations VALUES(?,?)");
        row.bind(1,migration.version);row.bind(2,migration.name);row.done();
    }
    sqlite_detail::execute(db,"INSERT INTO accounts(id,username,password_hash) VALUES(1,'journal-owner','test'),(2,'other-owner','test')");
    for(unsigned id=1;id<=2;++id) {
        std::array<std::uint8_t,40> profile{};profile[0]=static_cast<std::uint8_t>('A'+id);
        sqlite_detail::Statement row(db,"INSERT INTO recovered_characters(id,account_id,slot,profile,name_bytes) VALUES(?,?,0,?,?)");
        row.bind(1,id);row.bind(2,id);row.bind_blob(3,profile);row.bind_blob(4,std::span(profile).first(1));row.done();
    }
}
void tests(const char* path) {
    auto db=open(path);SqliteQuestJournalRepository repository(db.get());
    rejects([]{SqliteQuestJournalRepository invalid(nullptr);});
    require(!repository.load(1,1),"Missing journal seeded");
    for(const auto pair:{std::pair{0u,1u},std::pair{1u,0u},std::pair{2u,1u},std::pair{1u,2u},std::pair{1u,99u}}) {
        rejects([&]{repository.load(pair.first,pair.second);});
        rejects([&]{repository.save(pair.first,pair.second,std::nullopt,{},"CUSTOM_TEST_NOT_NATIVE","test");});
    }
    std::array<std::uint16_t,418> counts{};
    {
        sqlite_detail::Statement rows(db.get(),"SELECT mission_index,description_count FROM native_quest_definitions ORDER BY mission_index");
        unsigned i=0;while(rows.row()) {require(rows.integer(0)==++i,"Definition gap");counts[i-1]=rows.number<std::uint16_t>(1);}
        require(i==418,"Real pinned catalog missing");
    }
    QuestJournalSnapshot initial;
    initial.values[0]=1;initial.values[1]=0x10001; // Both select first text, bytes must remain distinct.
    initial.values[14]=(std::uint32_t{counts[417]}<<16)|418;
    auto saved=repository.save(1,1,std::nullopt,initial.values,"CUSTOM_TEST_NOT_NATIVE","test:current-Mission_data-reference");
    require(saved.revision==1 && saved.values==initial.values,"Initial snapshot changed packed values");
    require(repository.load(1,1)==saved,"Readback mismatch");
    require(!repository.load(2,2),"Other character acquired journal");
    {
        sqlite_detail::Statement row(db.get(),"SELECT values_blob FROM character_quest_journals WHERE character_id=1");
        require(row.row(),"No saved blob");const auto bytes=row.blob(0,60,60);
        require(bytes[0]==1 && bytes[1]==0 && bytes[4]==1 && bytes[6]==1,"Wrong little-endian packing");
        require(bytes[56]==0xa2 && bytes[57]==1 && bytes[58]==counts[417],"Last slot lost");
    }
    rejects([&]{repository.save(1,1,std::nullopt,{},saved.origin,saved.provenance);});
    rejects([&]{repository.save(1,1,0,{},saved.origin,saved.provenance);});
    rejects([&]{repository.save(1,1,2,{},saved.origin,saved.provenance);});
    rejects([&]{repository.save(1,1,std::numeric_limits<std::uint64_t>::max(),{},saved.origin,saved.provenance);});
    for(const auto invalid:{0x10000u,419u,0xffff0001u,(std::uint32_t{counts[0]+1u}<<16)|1u}) {
        auto values=saved.values;values[3]=invalid;
        rejects([&]{repository.save(1,1,saved.revision,values,saved.origin,saved.provenance);});
        require(repository.load(1,1)==saved,"Invalid reference changed snapshot");
    }
    for(const auto& origin:{std::string{},std::string{"NATIVE_VERIFIED"},std::string{"CUSTOM_DESIGNED"}})
        rejects([&]{repository.save(1,1,saved.revision,saved.values,origin,saved.provenance);});
    for(const auto& provenance:{std::string{},std::string(256,'x'),std::string("x\0y",3)})
        rejects([&]{repository.save(1,1,saved.revision,saved.values,saved.origin,provenance);});
    auto same=repository.save(1,1,saved.revision,saved.values,saved.origin,saved.provenance);
    require(same.revision==2 && same.values==saved.values,"Same-value revision policy wrong");
    rejects([&]{repository.save(1,1,saved.revision,{},saved.origin,saved.provenance);});
    // A second actual SQLite connection sees the committed revision and cannot
    // overwrite it with the first connection's stale token.
    {auto second=open(path);SqliteQuestJournalRepository other(second.get());
        require(other.load(1,1)==same,"Second connection cannot resume");
        rejects([&]{other.save(1,1,1,{},same.origin,same.provenance);});}
    sqlite_detail::execute(db.get(),"CREATE TRIGGER journal_reject BEFORE UPDATE ON character_quest_journals BEGIN SELECT RAISE(ABORT,'fixture'); END");
    rejects([&]{repository.save(1,1,same.revision,{},same.origin,same.provenance);});
    sqlite_detail::execute(db.get(),"DROP TRIGGER journal_reject");
    require(repository.load(1,1)==same,"Aborted write did not roll back");
    sqlite_detail::execute(db.get(),"CREATE TRIGGER journal_corrupt AFTER UPDATE ON character_quest_journals BEGIN UPDATE character_quest_journals SET provenance='tampered' WHERE character_id=NEW.character_id; END");
    rejects([&]{repository.save(1,1,same.revision,{},same.origin,same.provenance);});
    sqlite_detail::execute(db.get(),"DROP TRIGGER journal_corrupt");
    require(repository.load(1,1)==same,"Readback mismatch did not roll back");
    // Corruption trials run on independent memory backups, never nested inside
    // the repository transaction (which would trivially fail BEGIN).
    for(const auto* sql:{
        "DELETE FROM native_quest_definitions WHERE mission_index=418",
        "DELETE FROM native_quest_descriptions WHERE mission_index=418 AND description_index=0",
        "UPDATE native_quest_definitions SET description_count=description_count+1 WHERE mission_index=1",
        "UPDATE native_quest_descriptions SET description_count=description_count+1 WHERE mission_index=1",
        "UPDATE native_data_sources SET native_image_sha256='0000000000000000000000000000000000000000000000000000000000000000' WHERE dataset_id='current-quest-descriptions-v1'",
        "UPDATE native_data_sources SET source_sha256='0000000000000000000000000000000000000000000000000000000000000000' WHERE dataset_id='current-quest-descriptions-v1'",
        "UPDATE character_quest_journals SET values_blob=CAST(X'00000100'||substr(values_blob,5) AS BLOB) WHERE character_id=1",
        "PRAGMA ignore_check_constraints=ON; UPDATE character_quest_journals SET revision=0 WHERE character_id=1",
        "PRAGMA ignore_check_constraints=ON; UPDATE character_quest_journals SET design_id='CUSTOM-0018' WHERE character_id=1"}) {
        auto copy=open(":memory:");auto* backup=sqlite3_backup_init(copy.get(),"main",db.get(),"main");
        require(backup!=nullptr,"Backup unavailable");const auto step=sqlite3_backup_step(backup,-1);
        const auto finish=sqlite3_backup_finish(backup);require(step==SQLITE_DONE && finish==SQLITE_OK,"Backup failed");
        sqlite_detail::execute(copy.get(),sql);SqliteQuestJournalRepository corrupt(copy.get());
        rejects([&]{corrupt.load(1,1);});
        rejects([&]{corrupt.save(1,1,same.revision,same.values,same.origin,same.provenance);});
    }
    const auto cleared=repository.save(1,1,same.revision,{},same.origin,"test:explicit-clear");
    require(cleared.revision==3 && cleared.values==std::array<std::uint32_t,15>{},"Clear failed");
    const auto projection=RecoveredQuestSync::encodeJournalLogical(cleared.values,counts);
    require(projection && *projection==RecoveredQuestSync::emptyJournalLogical(),"Clear projection differs");
    db.reset();db=open(path);SqliteQuestJournalRepository resumed(db.get());
    require(resumed.load(1,1)==cleared && !resumed.load(2,2),"Disk reopen lost clear/ownership");
    auto capture=resumed.save(1,1,cleared.revision,initial.values,"NATIVE_CAPTURE_VERIFIED","test:synthetic-origin-enum-check-not-real-capture");
    require(capture.origin=="NATIVE_CAPTURE_VERIFIED" && resumed.load(1,1)==capture,"Origin metadata not preserved");
    std::cout<<"Owned journal checks passed: "<<checks<<"; pinned definitions=418 descriptions=2014\n";
}
}
int main(int argc,char** argv) {
    try {
        if(argc!=3)throw std::runtime_error("Usage: quest-journal --initialize|--test disposable.db");
        if(std::string(argv[1])=="--initialize") {auto db=open(argv[2]);initialize(db.get());}
        else if(std::string(argv[1])=="--empty-test") {
            auto db=open(argv[2]);SqliteQuestJournalRepository repository(db.get());
            require(!repository.load(1,1),"No-catalog empty journal must stay absent");
            rejects([&]{repository.load(2,1);});rejects([&]{repository.load(0,1);});
            rejects([&]{repository.save(1,1,std::nullopt,{},"CUSTOM_TEST_NOT_NATIVE","test:missing-source");});
            require(!repository.load(1,1),"Missing-source save created journal");
            std::cout<<"No-catalog journal checks passed: "<<checks<<'\n';
        }
        else if(std::string(argv[1])=="--test")tests(argv[2]);
        else throw std::runtime_error("Unknown test mode");
        return 0;
    }catch(const std::exception& error){std::cerr<<error.what()<<'\n';return 1;}
}
