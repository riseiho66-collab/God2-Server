#include "db/SqliteRoleTextRepository.h"
#include "db/SqliteSupport.h"
#include "db/Migration.h"
#include "text/LegacyChineseCodec.h"
#include <chrono>
#include <filesystem>
#include <iostream>
#include <limits>

using namespace god2;
namespace {
unsigned checks=0;
void check(bool value){++checks;if(!value)throw std::runtime_error("Owned role text test failed");}
template<class F> void rejects(F fn){bool failed=false;try{fn();}catch(const DatabaseError&){failed=true;}check(failed);}
RecoveredRoleText::Text text(std::string_view value) {
    if(value.size()>15)throw std::runtime_error("Invalid role text test input");
    RecoveredRoleText::Text result{};std::copy(value.begin(),value.end(),result.begin());return result;
}
}
int main() {
    sqlite3* db=nullptr;if(sqlite3_open(":memory:",&db)!=SQLITE_OK)return 2;
    int result=0;
    try {
        sqlite_detail::execute(db,"PRAGMA foreign_keys=ON");
        const auto migrations=default_sqlite_migrations();
        check(migrations.size()>=39 && migrations[38].version==39 && migrations[38].name=="owned_secondary_role_text");
        // Upgrade an existing version38 character. The new table starts empty.
        for(const auto& migration:migrations)if(migration.version<39)sqlite_detail::execute(db,migration.sql);
        sqlite_detail::execute(db,"INSERT INTO accounts(id,username,password_hash) VALUES(1,'role-text-owner','test'),(2,'role-text-other','test')");
        const std::array<std::uint8_t,40> profile{'A'};
        for(std::uint64_t id:{1ULL,2ULL}) {
            auto owned_profile=profile;owned_profile[0]=static_cast<std::uint8_t>('A'+id-1);
            sqlite_detail::Statement insert(db,"INSERT INTO recovered_characters(id,account_id,slot,profile,name_bytes) VALUES(?,1,?,?,?)");
            insert.bind_id(1,id);insert.bind_id(2,id-1);insert.bind_blob(3,owned_profile);insert.bind_blob(4,std::span(owned_profile).first(1));insert.done();
        }
        for(const auto& migration:migrations)if(migration.version>=39)sqlite_detail::execute(db,migration.sql);
        SqliteRoleTextRepository repository(db);rejects([]{SqliteRoleTextRepository invalid(nullptr);});
        check(!repository.load(1,1) && !repository.load(1,2));
        for(const auto owner:{std::pair{0u,1u},std::pair{1u,0u},std::pair{2u,1u},std::pair{1u,99u}}) {
            rejects([&]{repository.load(owner.first,owner.second);});
            rejects([&]{repository.save(owner.first,owner.second,std::nullopt,text("text"),950);});
        }
        const auto first=repository.save(1,1,std::nullopt,text("ABCDEFGHIJKLMNO"),950);
        check(first.text==text("ABCDEFGHIJKLMNO") && first.utf8=="ABCDEFGHIJKLMNO" && first.codepage==950 && first.revision==1);
        check(repository.load(1,1)==std::optional(first));
        check(repository.save(1,1,1,first.text,950)==first);
        rejects([&]{repository.save(1,1,std::nullopt,first.text,950);});
        for(const auto revision:{0ULL,2ULL,std::numeric_limits<unsigned long long>::max()})
            rejects([&]{repository.save(1,1,revision,first.text,950);});
        for(const auto codepage:{0u,65001u,949u})
            rejects([&]{repository.save(1,1,1,first.text,static_cast<std::uint16_t>(codepage));});
        auto unterminated=first.text;unterminated[15]=1;
        rejects([&]{repository.save(1,1,1,unterminated,950);});
        auto hidden_tail=text("hi");hidden_tail[10]=0xff;
        rejects([&]{repository.save(1,1,1,hidden_tail,950);});
        for(const auto codepage:{936u,950u})
            rejects([&]{repository.save(1,1,1,text(std::string(1,static_cast<char>(0x81))),static_cast<std::uint16_t>(codepage));});
        check(repository.load(1,1)==std::optional(first));
        // Native strings are bytes; the stored Unicode copy is independently
        // checked and must reproduce every original byte in its recorded page.
        const std::string utf8="\xe8\xa7\x92\xe8\x89\xb2\xe6\x96\x87\xe5\xad\x97";
        auto saved=first;
        for(const auto codepage:{950u,936u}) {
            const auto encoded=LegacyChineseCodec::encode(utf8,codepage==936);
            saved=repository.save(1,1,saved.revision,text(encoded),static_cast<std::uint16_t>(codepage));
            check(saved.text==text(encoded) && saved.utf8==utf8 && saved.codepage==codepage);
            check(repository.load(1,1)==std::optional(saved));
            check(RecoveredRoleText::update(saved.text).has_value());
            for(const auto output:{950u,936u})
                check(SqliteRoleTextRepository::project(saved,static_cast<std::uint16_t>(output))==text(LegacyChineseCodec::encode(utf8,output==936)));
        }
        check(!SqliteRoleTextRepository::project(saved,0));
        auto corrupted=saved;corrupted.utf8="wrong";check(!SqliteRoleTextRepository::project(corrupted,936));
        // CP936 U+4E13 is unavailable in CP950: projection may fail, storage
        // must keep the original Simplified bytes without a '?' replacement.
        const auto simplified_only=repository.save(1,2,std::nullopt,text("\xd7\xa8"),936);
        check(!SqliteRoleTextRepository::project(simplified_only,950));
        check(SqliteRoleTextRepository::project(simplified_only,936)==text("\xd7\xa8"));
        check(repository.load(1,2)==std::optional(simplified_only));
        const auto cleared=repository.save(1,1,saved.revision,text(""),936);
        check(cleared.utf8.empty() && cleared.text==RecoveredRoleText::Text{} && cleared.revision==saved.revision+1);
        saved=repository.save(1,1,cleared.revision,text(LegacyChineseCodec::encode(utf8,true)),936);
        // Independent owner slot and the original name/profile remain intact.
        const auto sibling=repository.save(1,2,simplified_only.revision,text("other"),950);
        check(repository.load(1,1)==std::optional(saved) && repository.load(1,2)==std::optional(sibling));
        {
            sqlite_detail::Statement unchanged(db,"SELECT profile,name_bytes,name_codepage FROM recovered_characters WHERE id=1");
            check(unchanged.row());const auto bytes=unchanged.blob(0,40,40);
            check(std::equal(bytes.begin(),bytes.end(),profile.begin()));
            check(unchanged.blob(1,1,1)[0]=='A' && unchanged.integer(2)==950);
        }
        sqlite_detail::execute(db,"CREATE TRIGGER fail_role_text BEFORE UPDATE ON character_role_text BEGIN SELECT RAISE(ABORT,'fail'); END");
        rejects([&]{repository.save(1,1,saved.revision,text("rollback"),950);});
        check(repository.load(1,1)==std::optional(saved));
        sqlite_detail::execute(db,"DROP TRIGGER fail_role_text");
        // Corrupted UTF8/raw coherence is rejected on load, never replayed.
        sqlite_detail::execute(db,"UPDATE character_role_text SET utf8_text='wrong' WHERE character_id=2");
        rejects([&]{repository.load(1,2);});
        sqlite_detail::execute(db,"UPDATE character_role_text SET utf8_text='other' WHERE character_id=2");
        check(repository.load(1,2)==std::optional(sibling));
        sqlite_detail::execute(db,"UPDATE character_role_text SET revision=9223372036854775807 WHERE character_id=2");
        const auto maximum=static_cast<std::uint64_t>(std::numeric_limits<std::int64_t>::max());
        check(repository.save(1,2,maximum,sibling.text,950).revision==maximum);
        rejects([&]{repository.save(1,2,maximum,text("changed"),950);});
        const auto path=std::filesystem::temp_directory_path()/
            ("god2-owned-role-text-"+std::to_string(std::chrono::steady_clock::now().time_since_epoch().count())+".db");
        struct Cleanup {std::filesystem::path path;~Cleanup(){std::error_code error;std::filesystem::remove(path,error);}} cleanup{path};
        sqlite3* disk=nullptr;check(sqlite3_open(path.string().c_str(),&disk)==SQLITE_OK);
        auto* backup=sqlite3_backup_init(disk,"main",db,"main");check(backup!=nullptr);
        check(sqlite3_backup_step(backup,-1)==SQLITE_DONE);check(sqlite3_backup_finish(backup)==SQLITE_OK);
        check(sqlite3_close(disk)==SQLITE_OK);disk=nullptr;
        check(sqlite3_open_v2(path.string().c_str(),&disk,SQLITE_OPEN_READONLY,nullptr)==SQLITE_OK);
        {SqliteRoleTextRepository reopened(disk);check(reopened.load(1,1)==std::optional(saved));
         rejects([&]{reopened.load(2,1);});
         rejects([&]{reopened.save(1,1,saved.revision,text("readonly"),950);});
         check(reopened.load(1,1)==std::optional(saved));}
        check(sqlite3_close(disk)==SQLITE_OK);
        // Only the owned text row follows its deleted character.
        sqlite_detail::execute(db,"DELETE FROM recovered_characters WHERE id=2");
        {sqlite_detail::Statement count(db,"SELECT count(*) FROM character_role_text");check(count.row() && count.integer(0)==1);}
        check(repository.load(1,1)==std::optional(saved));
        std::cout<<"PASS "<<checks<<" role text migration/ownership/CAS/encoding/rollback/reopen checks\n";
    }catch(const std::exception& error){std::cerr<<error.what()<<'\n';result=1;}
    sqlite3_close(db);return result;
}
