#include "db/SqliteGuildRosterRepository.h"
#include "db/SqliteSupport.h"
#include "text/LegacyChineseCodec.h"
#include <chrono>
#include <filesystem>
#include <iostream>
#include <limits>
#include <string>

using namespace god2;
namespace {
unsigned checks=0;
void check(bool value) {++checks;if(!value)throw std::runtime_error("Owned guild roster storage check failed");}
template<class F> void rejects(F operation) {
    bool failed=false;try {operation();}catch(const DatabaseError&) {failed=true;}check(failed);
}
std::string all_rows(sqlite3* db) {
    sqlite_detail::Statement tables(db,"SELECT name FROM sqlite_schema WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name");
    std::string result;
    while(tables.row()) {
        const auto name=tables.text(0);result+=name+"\n";
        const auto sql="SELECT * FROM \""+name+"\" ORDER BY rowid";
        sqlite3_stmt* rows=nullptr;sqlite_detail::check(db,sqlite3_prepare_v2(db,sql.c_str(),-1,&rows,nullptr));
        int code;
        while((code=sqlite3_step(rows))==SQLITE_ROW) {
            for(int i=0;i<sqlite3_column_count(rows);++i) {
                const auto type=sqlite3_column_type(rows,i);result+=std::to_string(type)+":";
                if(type==SQLITE_INTEGER)result+=std::to_string(sqlite3_column_int64(rows,i));
                else if(type==SQLITE_TEXT || type==SQLITE_BLOB) {
                    const auto* bytes=static_cast<const unsigned char*>(sqlite3_column_blob(rows,i));
                    const auto count=sqlite3_column_bytes(rows,i);result+=std::to_string(count)+":";
                    for(int j=0;j<count;++j) {result+="0123456789abcdef"[bytes[j]>>4];result+="0123456789abcdef"[bytes[j]&15];}
                }else if(type!=SQLITE_NULL)throw std::runtime_error("Unexpected fixture SQL type");
                result+='|';
            }
            result+='\n';
        }
        sqlite3_finalize(rows);if(code!=SQLITE_DONE)throw DatabaseError("Fixture row census failed");
    }
    return result;
}
std::optional<StoredGuildRoster> read_unchanged(sqlite3* db,SqliteGuildRosterRepository& reader,std::uint64_t account,std::uint64_t character) {
    const auto before=all_rows(db);const auto changes=sqlite3_total_changes(db);
    const auto result=reader.load(account,character);
    check(all_rows(db)==before && sqlite3_total_changes(db)==changes && sqlite3_get_autocommit(db));return result;
}
void set_name(sqlite3* db,std::uint64_t character,const std::string& raw,std::uint16_t codepage) {
    std::array<std::uint8_t,40> profile{};std::copy(raw.begin(),raw.end(),profile.begin());profile[29]=2;
    sqlite_detail::Statement update(db,"UPDATE recovered_characters SET profile=?,name_bytes=?,name_codepage=? WHERE id=?");
    update.bind_blob(1,profile);update.bind_blob(2,std::span(reinterpret_cast<const std::uint8_t*>(raw.data()),raw.size()));
    update.bind_id(3,codepage);update.bind_id(4,character);update.done();
}
void insert_character(sqlite3* db,std::uint64_t id,std::uint64_t account,std::uint8_t slot,const std::string& raw,std::uint16_t codepage) {
    std::array<std::uint8_t,40> profile{};std::copy(raw.begin(),raw.end(),profile.begin());profile[29]=2;
    sqlite_detail::Statement insert(db,"INSERT INTO recovered_characters(id,account_id,slot,profile,name_bytes,name_codepage) VALUES(?,?,?,?,?,?)");
    insert.bind_id(1,id);insert.bind_id(2,account);insert.bind_id(3,slot);insert.bind_blob(4,profile);
    insert.bind_blob(5,std::span(reinterpret_cast<const std::uint8_t*>(raw.data()),raw.size()));insert.bind_id(6,codepage);insert.done();
}
void role(sqlite3* db,std::uint64_t character,std::uint8_t level,std::uint64_t revision) {
    RecoveredRoleLevel::Bytes logical{};logical[0]=0x22;logical[1]=level;logical[17]=0xf4;logical[18]=1;logical[21]=100;
    sqlite_detail::Statement insert(db,"INSERT OR REPLACE INTO character_role_snapshots(character_id,logical,revision,design_id) VALUES(?,?,?,'CUSTOM-0013')");
    insert.bind_id(1,character);insert.bind_blob(2,logical);insert.bind_id(3,revision);insert.done();
}
}
int main() {
    sqlite3* db=nullptr;if(sqlite3_open(":memory:",&db)!=SQLITE_OK)return 2;
    int result=0;
    try {
        sqlite_detail::execute(db,R"SQL(
PRAGMA foreign_keys=ON;
CREATE TABLE accounts(id INTEGER PRIMARY KEY,username TEXT,password_hash TEXT);
CREATE TABLE recovered_characters(id INTEGER PRIMARY KEY,account_id INTEGER REFERENCES accounts(id),slot INTEGER,profile BLOB,name_bytes BLOB,name_codepage INTEGER);
CREATE TABLE character_role_snapshots(character_id INTEGER PRIMARY KEY REFERENCES recovered_characters(id) ON DELETE CASCADE,logical BLOB,revision INTEGER,design_id TEXT);
CREATE TABLE saved_fixture(character_id INTEGER PRIMARY KEY,hp INTEGER,mp INTEGER,xp INTEGER,revision INTEGER);
INSERT INTO accounts VALUES(1,'Owner','hash-a'),(2,'OfflineOtherOwner','hash-b'),(3,'ElsewhereOwner','hash-c'),(4,'NotMemberOwner','hash-d');
INSERT INTO saved_fixture VALUES(1,500,100,789,7),(2,345,67,890,8),(3,456,78,901,9);
)SQL");
        insert_character(db,1,1,0,"Owner",950);
        insert_character(db,2,1,1,"Sibling",0); // ASCII0 is independently provable.
        const auto chinese=std::string("\xe5\xb0\x8f\xe6\x98\x8e"); // 小明.
        const auto chinese_bytes=LegacyChineseCodec::encode(chinese,true);
        insert_character(db,3,2,0,chinese_bytes,936);
        insert_character(db,4,3,0,"Elsewhere",950);
        insert_character(db,5,4,0,"NoMember",950);
        role(db,1,7,1);role(db,2,8,1); // Offline third member has no role snapshot.
        sqlite_detail::execute(db,SqliteGuildRepository::schema());
        SqliteGuildRepository membership(db);
        const auto guild=membership.admin_create("FirstGuild"),other_guild=membership.admin_create("OtherGuild");
        membership.admin_assign(1,1,guild,std::nullopt);
        membership.admin_assign(1,2,guild,std::nullopt);
        membership.admin_assign(2,3,guild,std::nullopt);
        membership.admin_assign(3,4,other_guild,std::nullopt);
        SqliteGuildRosterRepository reader(db);
        rejects([]{SqliteGuildRosterRepository invalid(nullptr);});
        const auto first=*read_unchanged(db,reader,1,1);
        check(first.requester_account==1 && first.requester_character==1 && first.membership.guild_id==guild && first.members.size()==3);
        check(first.members[0].character_id==1 && first.members[1].character_id==2 && first.members[2].character_id==3);
        check(first.members[0].account_id==1 && first.members[2].account_id==2 && first.members[2].name_utf8==chinese);
        check(first.members[1].name_codepage==0 && first.members[1].name_utf8=="Sibling");
        check(first.members[0].role && first.members[1].role && !first.members[2].role);
        check(RecoveredRoleLevel::parse(first.members[0].role->logical)->level()==7);
        check(read_unchanged(db,reader,1,1)==std::optional(first));
        const auto offline_requester=*read_unchanged(db,reader,2,3);
        check(offline_requester.members==first.members && offline_requester.membership.guild_id==guild);
        const auto elsewhere=*read_unchanged(db,reader,3,4);
        check(elsewhere.membership.guild_id==other_guild && elsewhere.members.size()==1 && elsewhere.members[0].character_id==4);
        check(!read_unchanged(db,reader,4,5));
        for(const auto& owner:{std::pair{0u,1u},std::pair{1u,0u},std::pair{2u,1u},std::pair{1u,3u},std::pair{1u,4u},std::pair{1u,99u}}) {
            const auto rows=all_rows(db);rejects([&]{reader.load(owner.first,owner.second);});check(all_rows(db)==rows && sqlite3_get_autocommit(db));
        }
        rejects([&]{reader.load(std::numeric_limits<std::uint64_t>::max(),1);});
        // A deferred reader refuses nested transactions without committing or
        // rolling back its caller's transaction, including a pending writer.
        sqlite_detail::execute(db,"BEGIN IMMEDIATE");rejects([&]{reader.load(1,1);});check(!sqlite3_get_autocommit(db));
        sqlite_detail::execute(db,"ROLLBACK");
        // Equality detects rename and level mutations which do not advance the
        // existing guild generation. Full field tokens are required at publish.
        set_name(db,2,"Renamed",0);
        const auto renamed=*read_unchanged(db,reader,1,1);
        check(renamed!=first && renamed.membership.guild_revision==first.membership.guild_revision && renamed.members[1].name_utf8=="Renamed");
        set_name(db,2,"Sibling",0);check(read_unchanged(db,reader,1,1)==std::optional(first));
        role(db,2,9,2);
        const auto leveled=*read_unchanged(db,reader,1,1);
        check(leveled!=first && leveled.membership.guild_revision==first.membership.guild_revision && leveled.members[1].role->revision==2);
        role(db,2,8,1);check(read_unchanged(db,reader,1,1)==std::optional(first));
        // Unknown nonASCII page0 must never inherit the requester's locale.
        sqlite_detail::execute(db,"UPDATE recovered_characters SET name_codepage=0 WHERE id=3");
        rejects([&]{reader.load(1,1);});check(read_unchanged(db,reader,3,4)==std::optional(elsewhere));
        sqlite_detail::execute(db,"UPDATE recovered_characters SET name_codepage=936 WHERE id=3");
        for(const auto codepage:{1,65001}) {
            sqlite_detail::execute(db,"UPDATE recovered_characters SET name_codepage="+std::to_string(codepage)+" WHERE id=3");
            rejects([&]{reader.load(1,1);});
        }
        set_name(db,3,std::string(1,static_cast<char>(0x81)),936);rejects([&]{reader.load(1,1);});
        set_name(db,3,chinese_bytes,936);
        sqlite_detail::execute(db,"UPDATE recovered_characters SET name_bytes=X'57726F6E67' WHERE id=2");
        rejects([&]{reader.load(1,1);});set_name(db,2,"Sibling",0);
        sqlite_detail::execute(db,"UPDATE recovered_characters SET profile=X'00' WHERE id=2");
        rejects([&]{reader.load(1,1);});set_name(db,2,"Sibling",0);
        sqlite_detail::execute(db,"UPDATE recovered_characters SET slot=0 WHERE id=2");
        rejects([&]{reader.load(1,1);});sqlite_detail::execute(db,"UPDATE recovered_characters SET slot=1 WHERE id=2");
        sqlite_detail::execute(db,"UPDATE character_role_snapshots SET logical=X'22' WHERE character_id=2");
        rejects([&]{reader.load(1,1);});role(db,2,8,1);
        sqlite_detail::execute(db,"UPDATE character_role_snapshots SET design_id='UNVERIFIED' WHERE character_id=2");
        rejects([&]{reader.load(1,1);});role(db,2,8,1);
        const auto old_generation=first.members[2].membership_revision;
        sqlite_detail::execute(db,"UPDATE owned_guild_members SET revision=9223372036854775807 WHERE character_id=3");
        rejects([&]{reader.load(1,1);});
        sqlite_detail::execute(db,"UPDATE owned_guild_members SET revision="+std::to_string(old_generation)+" WHERE character_id=3");
        // Deliberate foreign-key corruption must be surfaced, never hidden by
        // joining only the characters/accounts that happen to remain valid.
        sqlite_detail::execute(db,"PRAGMA foreign_keys=OFF");
        sqlite_detail::execute(db,"INSERT INTO owned_guild_members SELECT 999,guild_id,revision,origin,design_id,source_sha256 FROM owned_guild_members WHERE character_id=3");
        rejects([&]{reader.load(1,1);});check(read_unchanged(db,reader,3,4)==std::optional(elsewhere));
        sqlite_detail::execute(db,"DELETE FROM owned_guild_members WHERE character_id=999");
        sqlite_detail::execute(db,"DELETE FROM accounts WHERE id=2");rejects([&]{reader.load(1,1);});
        sqlite_detail::execute(db,"INSERT INTO accounts VALUES(2,'OfflineOtherOwner','hash-b')");
        sqlite_detail::execute(db,"DELETE FROM accounts WHERE id=4");rejects([&]{reader.load(4,5);});
        sqlite_detail::execute(db,"INSERT INTO accounts VALUES(4,'NotMemberOwner','hash-d')");
        sqlite_detail::execute(db,"PRAGMA foreign_keys=ON");
        check(read_unchanged(db,reader,1,1)==std::optional(first));
        // The character-delete cascade does not bump frozen guild revision;
        // the complete member vector still detects that removal.
        sqlite_detail::execute(db,"DELETE FROM recovered_characters WHERE id=2");
        const auto deleted=*read_unchanged(db,reader,1,1);
        check(deleted!=first && deleted.members.size()==2 && deleted.membership.guild_revision==first.membership.guild_revision);
        insert_character(db,2,1,1,"Sibling",0);role(db,2,8,1);
        const auto rejoined=membership.admin_assign(1,2,guild,std::nullopt);
        const auto current=*read_unchanged(db,reader,1,1);
        check(current.members.size()==3 && current.members[1].membership_revision==rejoined.membership_revision && current!=first);
        // File-backed read-only reopening exercises the same reader and
        // proves BEGIN/COMMIT is compatible with a genuinely read-only handle.
        const auto path=std::filesystem::temp_directory_path()/
            ("god2-owned-guild-roster-"+std::to_string(std::chrono::steady_clock::now().time_since_epoch().count())+".db");
        struct Cleanup {std::filesystem::path path;~Cleanup(){std::error_code error;std::filesystem::remove(path,error);}} cleanup{path};
        sqlite3* disk=nullptr;check(sqlite3_open(path.string().c_str(),&disk)==SQLITE_OK);
        auto* backup=sqlite3_backup_init(disk,"main",db,"main");check(backup!=nullptr);
        check(sqlite3_backup_step(backup,-1)==SQLITE_DONE);check(sqlite3_backup_finish(backup)==SQLITE_OK);
        check(sqlite3_close(disk)==SQLITE_OK);disk=nullptr;
        check(sqlite3_open_v2(path.string().c_str(),&disk,SQLITE_OPEN_READONLY,nullptr)==SQLITE_OK);
        {SqliteGuildRosterRepository readonly(disk);check(read_unchanged(disk,readonly,1,1)==std::optional(current));}
        check(sqlite3_close(disk)==SQLITE_OK);
        check(sqlite3_get_autocommit(db));
        std::cout<<"PASS "<<checks<<" guild roster ownership/complete-snapshot/offline/encoding/orphan/read-only checks\n";
    }catch(const std::exception& error) {std::cerr<<error.what()<<'\n';result=1;}
    sqlite3_close(db);return result;
}
