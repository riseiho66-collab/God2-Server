#include "GuildSuccessionSqliteMigrationsDraft.h"
#include "db/ServerSqliteMigrations.h"
#include "db/SqliteSupport.h"
namespace god2 {
namespace {
void require(bool value,const char* message){if(!value)throw DatabaseError(message);}
bool same(const Migration& a,const Migration& b){return a.version==b.version && a.name==b.name && a.sql==b.sql;}
using Connection=std::unique_ptr<sqlite3,decltype(&sqlite3_close_v2)>;
void flags(GuildSuccessionFlagsDraft f){
    require(!f.officers || (f.membership && f.announcements),"Enabled officers require guild membership/announcements");
    require(!f.succession || (f.membership && f.announcements && f.officers),"CUSTOM0083 enabled transfer requires qualified base guild/officer features");
}
Connection open(const std::filesystem::path& path){
    const auto bytes=path.u8string();sqlite3* raw=nullptr;
    const int result=sqlite3_open_v2(reinterpret_cast<const char*>(bytes.c_str()),&raw,SQLITE_OPEN_READONLY|SQLITE_OPEN_FULLMUTEX,nullptr);
    Connection owned(raw,sqlite3_close_v2);if(result!=SQLITE_OK)throw DatabaseError(raw?sqlite3_errmsg(raw):"Cannot inspect private succession migration storage");
    sqlite_detail::check(raw,sqlite3_busy_timeout(raw,5000));return owned;
}
std::string canonical(const std::string& sql,const char* name){
    sqlite3* raw=nullptr;const auto result=sqlite3_open(":memory:",&raw);Connection owned(raw,sqlite3_close_v2);
    require(result==SQLITE_OK,"Cannot canonicalize private succession schema");sqlite_detail::execute(raw,sql);
    sqlite_detail::Statement q(raw,"SELECT sql FROM sqlite_master WHERE type='table' AND name=?");q.bind(1,name);
    require(q.row(),"Canonical guild schema missing");auto value=q.text(0);require(!q.row(),"Canonical guild schema ambiguous");return value;
}
void exact_objects(sqlite3* raw,const char* name,const std::string& sql,bool expected){
    sqlite_detail::Statement q(raw,"SELECT type,name,tbl_name,sql FROM sqlite_master WHERE tbl_name=? OR name=? ORDER BY type,name");q.bind(1,name);q.bind(2,name);
    if(!expected){require(!q.row(),"Orphan guild schema/table/index/trigger denied");return;}
    const auto ddl=canonical(sql,name);
    require(q.row() && q.text(0)=="table" && q.text(1)==name && q.text(2)==name && q.text(3)==ddl && !q.row(),"Strict guild table/index/trigger/unknown schema mismatch");
}
std::size_t inspect(sqlite3* raw,const std::vector<Migration>& expected){
    bool exists=false;
    {sqlite_detail::Statement q(raw,"SELECT type FROM sqlite_master WHERE name='schema_migrations'");
     if(q.row()){require(q.text(0)=="table" && !q.row(),"Invalid succession history object");exists=true;}}
    std::size_t count=0;
    if(exists){sqlite_detail::Statement q(raw,"SELECT version,name,sql_text,typeof(version),typeof(name),typeof(sql_text) FROM schema_migrations ORDER BY version");
        while(q.row()){
            require(count<expected.size(),"Unknown future succession migration denied");const auto& migration=expected[count++];
            require(q.text(3)=="integer" && q.text(4)=="text" && q.text(5)=="text" && q.integer(0)==migration.version && q.text(1)==migration.name && q.text(2)==migration.sql,"Exact immutable1..52 migration prefix required");
        }}
    exact_objects(raw,"owned_guild_officers_0082",expected[50].sql,count>=51);
    exact_objects(raw,"owned_guild_successions_0083",expected[51].sql,count==52);
    return count;
}
}
std::vector<Migration> owned_guild_succession_migrations_draft(){
    auto migrations=owned_guild_officer_migrations();require(migrations.size()==51 && migrations.back().version==51,"CUSTOM0083 requires unchanged compiled1..51 prefix");
    migrations.push_back({52,"owned_guild_successions_candidate",SqliteOwnedGuildSuccessionRepositoryDraft::schema52_proposal()});return migrations;
}
void require_exact_guild_succession_migrations_draft(sqlite3* raw,const std::vector<Migration>& vector){
    require(raw!=nullptr,"Initialized succession connection required");const auto expected=owned_guild_succession_migrations_draft();
    require(vector.size()==52,"Effective-owner factory requires full52 migration vector");
    for(std::size_t i=0;i<52;++i)require(same(vector[i],expected[i]),"Exact compiled succession migration vector required");
    require(inspect(raw,expected)==52,"Effective-owner factory requires already installed52; no downgrade");
}
std::vector<Migration> configured_guild_succession_migrations_draft(const std::filesystem::path& path,GuildSuccessionFlagsDraft f){
    flags(f);const auto expected=owned_guild_succession_migrations_draft();
    // Frozen selector retains empty/NUL/path/open/physical50 checks. It tolerates
    // future history but NEVER decides52 ownership; our complete inspector does.
    const auto legacy=configured_sqlite_migrations(path,f.announcements);
    if(!std::filesystem::exists(path)){
        if(f.succession)return expected;
        return f.officers?owned_guild_officer_migrations():legacy;
    }
    auto db=open(path);sqlite_detail::execute(db.get(),"BEGIN");const auto count=inspect(db.get(),expected);
    if(count==52 || f.succession)return expected;
    if(count==51 || f.officers)return owned_guild_officer_migrations();
    return legacy;
}
GuildSuccessionRepositoryFactoryDraft::GuildSuccessionRepositoryFactoryDraft(sqlite3* raw,const std::vector<Migration>& vector,GuildSuccessionFlagsDraft f){
    flags(f);require(raw!=nullptr,"Initialized private factory connection required");
    const auto expected=owned_guild_succession_migrations_draft();const auto installed=inspect(raw,expected);
    require(installed==vector.size() && (installed==51 || installed==52),"Private owner factory requires complete51/52 and migrated exact vector");
    for(std::size_t i=0;i<vector.size();++i)require(same(vector[i],expected[i]),"Private factory vector differs");
    require(!f.succession || installed==52,"Enabled transfer cannot use a legacy51 owner factory");
    original_=std::make_unique<SqliteOwnedGuildMembershipRepository>(raw);
    if(installed==52){require_exact_guild_succession_migrations_draft(raw,vector);effective_=std::make_unique<SqliteOwnedGuildSuccessionRepositoryDraft>(raw,*original_,f.succession);}
}
SqliteOwnedGuildSuccessionRepositoryDraft& GuildSuccessionRepositoryFactoryDraft::effective_owner(){
    require(bool(effective_),"No effective-owner52 repository installed; legacy51 path only");return *effective_;
}
}
