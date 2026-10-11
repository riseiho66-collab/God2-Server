#include "db/SqliteRoleTextRepository.h"
#include "db/SqliteSupport.h"
#include "text/LegacyChineseCodec.h"
#include <chrono>
#include <filesystem>
#include <iostream>
#include <memory>

namespace {
using namespace god2;
unsigned checks=0;
void require(bool value,const char* message) {++checks;if(!value)throw std::runtime_error(message);}
template<class F> void rejects(F action) {bool denied=false;try{action();}catch(const DatabaseError&){denied=true;}require(denied,"Expected DB rejection");}
RecoveredRoleText::Text text(std::string_view value) {
    if(value.size()>15)throw std::runtime_error("Review fixture overlength");
    RecoveredRoleText::Text result{};std::copy(value.begin(),value.end(),result.begin());return result;
}
void projection_expansion() {
    const std::string euro="\xe2\x82\xac";
    const auto input=LegacyChineseCodec::encode(euro,true);
    const auto output=LegacyChineseCodec::encode(euro,false);
    require(input.size()==1 && output.size()==2,"Expected Windows 936/950 euro expansion changed");
    std::string utf8,raw;
    for(unsigned count=1;count<=15;++count) {
        utf8+=euro;raw+=input;
        const StoredRoleText saved{text(raw),utf8,936,1};
        require(SqliteRoleTextRepository::project(saved,936)==saved.text,"Same-page projection changed native bytes");
        const auto converted=SqliteRoleTextRepository::project(saved,950);
        if(count<=7) {
            require(converted.has_value(),"Representable expansion was rejected");
            std::string expected;for(unsigned i=0;i<count;++i)expected+=output;
            require(*converted==text(expected),"Expansion was replaced or truncated");
        } else require(!converted,"Expansion escaped 15-byte native bound");
    }
    StoredRoleText row{text("ASCII"),"ASCII",950,1};
    for(const auto codepage:{0u,949u,65001u,65535u}) {
        require(!SqliteRoleTextRepository::project(row,static_cast<std::uint16_t>(codepage)),"Unsupported target page admitted");
        auto malformed=row;malformed.codepage=static_cast<std::uint16_t>(codepage);
        require(!SqliteRoleTextRepository::project(malformed,950),"Unsupported stored page admitted");
    }
}
void two_connections() {
    struct Close {void operator()(sqlite3* db)const{sqlite3_close_v2(db);}};
    const auto file=std::filesystem::temp_directory_path()/
        ("god2-role-text-review-"+std::to_string(std::chrono::steady_clock::now().time_since_epoch().count())+".db");
    struct Remove {std::filesystem::path file;~Remove(){std::error_code error;std::filesystem::remove(file,error);}} cleanup{file};
    sqlite3* first_raw=nullptr;require(sqlite3_open(file.string().c_str(),&first_raw)==SQLITE_OK,"First DB open");
    const std::unique_ptr<sqlite3,Close> first(first_raw);
    sqlite_detail::execute(first_raw,"PRAGMA foreign_keys=ON;CREATE TABLE recovered_characters(id INTEGER PRIMARY KEY,account_id INTEGER);INSERT INTO recovered_characters VALUES(1,7),(2,8);");
    sqlite_detail::execute(first_raw,SqliteRoleTextRepository::schema());
    sqlite3* second_raw=nullptr;require(sqlite3_open(file.string().c_str(),&second_raw)==SQLITE_OK,"Second DB open");
    const std::unique_ptr<sqlite3,Close> second(second_raw);
    sqlite_detail::execute(second_raw,"PRAGMA foreign_keys=ON");
    SqliteRoleTextRepository a(first_raw),b(second_raw);
    const auto original=a.save(7,1,{},text("first"),950);
    require(b.load(7,1)==original,"Second connection lost saved revision");
    const auto winner=a.save(7,1,original.revision,text("winner"),950);
    rejects([&]{b.save(7,1,original.revision,text("stale"),950);});
    require(b.load(7,1)==winner,"Stale connection overwrote winner");
    rejects([&]{b.save(8,1,winner.revision,text("foreign"),950);});
    require(a.load(7,1)==winner,"Foreign session changed owner text");
    sqlite_detail::execute(first_raw,"BEGIN IMMEDIATE");
    rejects([&]{b.save(7,1,winner.revision,text("busy"),950);});
    sqlite_detail::execute(first_raw,"ROLLBACK");
    require(a.load(7,1)==winner,"Write conflict changed text");
    // Verify readback failure, not only statement failure, rolls back the write.
    sqlite_detail::execute(first_raw,"CREATE TRIGGER tamper_role_text AFTER UPDATE ON character_role_text BEGIN UPDATE character_role_text SET utf8_text='corrupted' WHERE character_id=NEW.character_id; END");
    rejects([&]{b.save(7,1,winner.revision,text("next"),950);});
    require(a.load(7,1)==winner,"After-write mismatch survived rollback");
}
}
int main() {try{projection_expansion();two_connections();std::cout<<"PASS "<<checks<<" independent role text expansion/concurrency checks\n";return 0;}
catch(const std::exception& error){std::cerr<<error.what()<<'\n';return 1;}}
