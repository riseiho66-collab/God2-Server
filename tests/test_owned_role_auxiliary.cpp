#include "db/SqliteRoleAuxiliaryRepository.h"
#include "db/SqliteSupport.h"
#include "db/Migration.h"
#include <iostream>
#include <limits>
#include <filesystem>
#include <chrono>
using namespace god2;
namespace {unsigned checks=0;void check(bool b){++checks;if(!b)throw std::runtime_error("Auxiliary ownership/CAS test failed");}
template<class F> void rejects(F fn){bool rejected=false;try{fn();}catch(const DatabaseError&){rejected=true;}check(rejected);}}
int main() {
    sqlite3* db=nullptr;if(sqlite3_open(":memory:",&db)!=SQLITE_OK)return 2;
    int result=0;
    try {
        sqlite_detail::execute(db,"PRAGMA foreign_keys=ON");
        for(const auto& migration:default_sqlite_migrations())sqlite_detail::execute(db,migration.sql);
        sqlite_detail::execute(db,"INSERT INTO accounts(id,username,password_hash) VALUES(1,'aux-owner','test'),(2,'aux-other','test')");
        const std::array<std::uint8_t,40> profile{'A'};
        sqlite_detail::Statement insert(db,"INSERT INTO recovered_characters(id,account_id,slot,profile,name_bytes) VALUES(1,1,0,?,?)");
        insert.bind_blob(1,profile);insert.bind_blob(2,std::span(profile).first(1));insert.done();
        SqliteRoleAuxiliaryRepository repository(db);rejects([]{SqliteRoleAuxiliaryRepository null(nullptr);});
        check(!repository.load(1,1));
        RecoveredRoleAuxiliary::Logical raw{};raw[0]=0x2c;
        for(unsigned i=1;i<61;++i)raw[i]=static_cast<std::uint8_t>(i*23+11);
        for(const auto owner:{std::pair{0u,1u},std::pair{1u,0u},std::pair{2u,1u},std::pair{1u,99u}}) {
            rejects([&]{repository.load(owner.first,owner.second);});
            rejects([&]{repository.save(owner.first,owner.second,std::nullopt,raw,"CUSTOM_TEST_NOT_NATIVE","test");});
        }
        const auto first=repository.save(1,1,std::nullopt,raw,"CUSTOM_TEST_NOT_NATIVE","owned-test");
        check(first.logical==raw && first.revision==1 && repository.load(1,1)==std::optional(first));
        rejects([&]{repository.save(1,1,std::nullopt,raw,"CUSTOM_TEST_NOT_NATIVE","duplicate");});
        for(const auto revision:{0ULL,2ULL,std::numeric_limits<unsigned long long>::max()})rejects([&]{repository.save(1,1,revision,raw,"CUSTOM_TEST_NOT_NATIVE","bad-CAS");});
        for(const auto origin:{"","CUSTOM_DESIGNED","unknown"})rejects([&]{repository.save(1,1,1,raw,origin,"test");});
        for(const auto text:{std::string{},std::string(256,'x'),std::string("a\0b",3)})rejects([&]{repository.save(1,1,1,raw,"CUSTOM_TEST_NOT_NATIVE",text);});
        auto invalid=raw;invalid[0]=0x22;rejects([&]{repository.save(1,1,1,invalid,"CUSTOM_TEST_NOT_NATIVE","invalid");});
        check(repository.load(1,1)==std::optional(first));
        auto next_raw=raw;next_raw[45]^=0x80;
        const auto second=repository.save(1,1,1,next_raw,"NATIVE_CAPTURE_VERIFIED","test-capture-contract");
        check(second.logical==next_raw && second.revision==2);
        sqlite_detail::execute(db,"INSERT INTO battle_reservations(id,character_id,resource_revision,design_id) VALUES(1,1,1,'CUSTOM-0012')");
        rejects([&]{repository.save(1,1,2,raw,"CUSTOM_TEST_NOT_NATIVE","pending-battle");});check(repository.load(1,1)==std::optional(second));
        sqlite_detail::execute(db,"DELETE FROM battle_reservations");
        sqlite_detail::execute(db,"CREATE TRIGGER fail_aux BEFORE UPDATE ON character_role_auxiliary_snapshots BEGIN SELECT RAISE(ABORT,'fail'); END");
        rejects([&]{repository.save(1,1,2,raw,"CUSTOM_TEST_NOT_NATIVE","rollback");});check(repository.load(1,1)==std::optional(second));
        // Close/reopen a real SQLite file: all opaque wire bytes and ownership
        // must survive, including high DWORD/mask bytes, without re-encoding.
        const auto path=std::filesystem::temp_directory_path()/
            ("god2-owned-aux-"+std::to_string(std::chrono::steady_clock::now().time_since_epoch().count())+".db");
        struct Cleanup {std::filesystem::path path;~Cleanup(){std::error_code ec;std::filesystem::remove(path,ec);}} cleanup{path};
        sqlite3* disk=nullptr;check(sqlite3_open(path.string().c_str(),&disk)==SQLITE_OK);
        auto* backup=sqlite3_backup_init(disk,"main",db,"main");check(backup!=nullptr);
        check(sqlite3_backup_step(backup,-1)==SQLITE_DONE);check(sqlite3_backup_finish(backup)==SQLITE_OK);
        check(sqlite3_close(disk)==SQLITE_OK);disk=nullptr;
        check(sqlite3_open_v2(path.string().c_str(),&disk,SQLITE_OPEN_READONLY,nullptr)==SQLITE_OK);
        {SqliteRoleAuxiliaryRepository reopened(disk);check(reopened.load(1,1)==std::optional(second));
         rejects([&]{reopened.load(2,1);});}
        check(sqlite3_close(disk)==SQLITE_OK);
        std::cout<<"PASS "<<checks<<" owned raw auxiliary ownership/CAS/rollback checks\n";
    }catch(const std::exception& error){std::cerr<<error.what()<<'\n';result=1;}
    sqlite3_close(db);return result;
}
