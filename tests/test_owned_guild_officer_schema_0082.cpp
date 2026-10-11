#include "db/GuildOfficerSqliteMigrations.h"
#include "db/ServerSqliteMigrations.h"
#include "db/SqliteDatabase.h"
#include "db/SqliteSupport.h"
#include "core/Config.h"
#include <nlohmann/json.hpp>
#include <fstream>
#include <iostream>
#include <iterator>
#include <functional>
#include <chrono>
using namespace god2;
namespace {
unsigned checks=0,cases=0;
void check(bool ok) {++checks;if(!ok)throw std::runtime_error("Schema51 independent assertion failed");}
void denied(const std::function<void()>& run) {bool failed=false;try{run();}catch(const std::exception&){failed=true;}check(failed);}
std::string bytes(const std::filesystem::path& p) {std::ifstream f(p,std::ios::binary);return {std::istreambuf_iterator<char>(f),{}};}
void edit(const std::filesystem::path& p,const std::string& sql) {
    sqlite3* raw=nullptr;check(sqlite3_open(p.string().c_str(),&raw)==SQLITE_OK);
    std::unique_ptr<sqlite3,decltype(&sqlite3_close_v2)> owned(raw,sqlite3_close_v2);sqlite_detail::execute(raw,sql);
}
void create(const std::filesystem::path& p,const std::vector<Migration>& migrations) {
    SqliteDatabase db(p,migrations);db.initialize();db.migrate();
}
bool same(const std::vector<Migration>& a,const std::vector<Migration>& b) {
    if(a.size()!=b.size())return false;
    for(std::size_t i=0;i<a.size();++i)if(a[i].version!=b[i].version || a[i].name!=b[i].name || a[i].sql!=b[i].sql)return false;
    return true;
}
}
int main(int argc,char** argv) {
    try {
        if(argc!=3)throw std::runtime_error("Private output root and READONLY formal config required");
        const std::filesystem::path parent=std::filesystem::absolute(argv[1]);
        std::filesystem::create_directories(parent);
        const auto nonce=std::chrono::steady_clock::now().time_since_epoch().count();
        const std::filesystem::path root=parent/("run-"+std::to_string(nonce));
        check(!std::filesystem::exists(root));std::filesystem::create_directory(root);
        const auto all=owned_guild_officer_migrations(),ann=owned_guild_announcement_migrations(),baseline=default_sqlite_migrations();
        check(all.size()==51 && ann.size()==50 && baseline.size()==49);
        check(same({all.begin(),all.begin()+50},ann));check(same({all.begin(),all.begin()+49},baseline));++cases;
        const auto missing=root/"absent.db";
        check(same(configured_guild_officer_sqlite_migrations(missing,false,false),baseline));
        check(same(configured_guild_officer_sqlite_migrations(missing,true,false),ann));
        check(same(configured_guild_officer_sqlite_migrations(missing,true,true),all));
        denied([&]{configured_guild_officer_sqlite_migrations(missing,false,true);});check(!std::filesystem::exists(missing));++cases;
        for(unsigned version:{49U,50U,51U}) {
            const auto p=root/("exact"+std::to_string(version)+".db");create(p,{all.begin(),all.begin()+version});
            const auto before=bytes(p);
            check(configured_guild_officer_sqlite_migrations(p,false,false).size()==version);
            check(configured_guild_officer_sqlite_migrations(p,true,false).size()==(version==51?51:50));
            check(same(configured_guild_officer_sqlite_migrations(p,true,true),all));check(before==bytes(p));++cases;
        }
        std::vector<std::pair<std::string,std::string>> faults={
            {"extraIndex","CREATE INDEX private_unknown_index ON owned_guild_officers_0082(role)"},
            {"extraUniqueIndex","CREATE UNIQUE INDEX private_unknown_unique ON owned_guild_officers_0082(character_id,membership_revision)"},
            {"extraTrigger","CREATE TRIGGER private_unknown_trigger AFTER UPDATE ON owned_guild_officers_0082 BEGIN SELECT 1; END"},
            {"wrongSQL","UPDATE schema_migrations SET sql_text=sql_text||' ' WHERE version=51"},
            {"wrongName","UPDATE schema_migrations SET name='fake' WHERE version=51"},
            {"wrongPrefix49","UPDATE schema_migrations SET sql_text=sql_text||' ' WHERE version=49"},
            {"wrongPrefix50","UPDATE schema_migrations SET sql_text=sql_text||' ' WHERE version=50"},
            {"missingPrefix","DELETE FROM schema_migrations WHERE version=1"},
            {"orphanTable","DELETE FROM schema_migrations WHERE version=51"},
            {"orphanHistory","DROP TABLE owned_guild_officers_0082"},
            {"unknownFuture","INSERT INTO schema_migrations(version,name,sql_text,applied_at) VALUES(52,'future','future','future')"},
            {"falsePhysicalDDL","DROP TABLE owned_guild_officers_0082;CREATE TABLE owned_guild_officers_0082(guild_id INTEGER PRIMARY KEY)"},
            {"opaqueSchema","ALTER TABLE owned_guild_officers_0082 ADD COLUMN opaque BLOB;"
                "INSERT INTO owned_guilds VALUES(100,'Kept',1,'CUSTOM_DESIGNED','CUSTOM-0075','149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763');"
                "INSERT INTO owned_guild_officers_0082 VALUES(100,1,2,0,1,1,2,'CUSTOM_DESIGNED','CUSTOM-0082','149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763',x'00ff')"}};
        for(const auto& [name,sql]:faults) {
            const auto p=root/(name+".db");create(p,all);edit(p,sql);const auto before=bytes(p);
            for(const auto flags:{std::pair{false,false},std::pair{true,false},std::pair{true,true}})
                denied([&]{configured_guild_officer_sqlite_migrations(p,flags.first,flags.second);});
            // Both selected exact51 accessor entry points share the strict
            // inspector; no configured flag fallback bypasses attached objects.
            if(name=="extraIndex" || name=="extraUniqueIndex" || name=="extraTrigger") {
                SqliteDatabase access(p,all);access.initialize();access.migrate();
                denied([&]{access.guild_membership51();});denied([&]{access.guild_announcements51();});
            }
            check(before==bytes(p));++cases;
        }
        {
            const auto p=root/"noHistory.db";edit(p,SqliteOwnedGuildMembershipRepository::officer_schema());const auto before=bytes(p);
            denied([&]{configured_guild_officer_sqlite_migrations(p,false,false);});check(before==bytes(p));++cases;
        }
        {
            const auto p=root/"exact51-access.db";SqliteDatabase db(p,all);db.initialize();
            denied([&]{db.guild_membership51();});denied([&]{db.guild_announcements51();});db.migrate();
            // Frozen legacy membership validates only when constructing its cache.
            // Test rejection BEFORE the exact51 accessor constructs that cache.
            denied([&]{db.candidate_guild_membership();});denied([&]{db.guild_announcements();});
            check(&db.guild_membership51()==&db.guild_membership51());check(&db.guild_announcements51()==&db.guild_announcements51());
            check(&db.candidate_guild_membership()==&db.guild_membership51());++cases;
        }
        {
            const auto p=root/"exact50-access.db";SqliteDatabase db(p,ann);db.initialize();db.migrate();
            db.candidate_guild_membership();db.guild_announcements();
            denied([&]{db.guild_membership51();});denied([&]{db.guild_announcements51();});++cases;
        }
        {
            const auto p=root/"tampered51-access.db";SqliteDatabase db(p,all);db.initialize();db.migrate();
            edit(p,"UPDATE schema_migrations SET name='fake' WHERE version=49");const auto before=bytes(p);
            denied([&]{db.guild_membership51();});denied([&]{db.guild_announcements51();});check(before==bytes(p));++cases;
        }
        for(const std::size_t index:{48U,49U,50U}) {
            auto forged=all;forged[index].sql+=' ';
            const auto p=root/("forged-vector"+std::to_string(index)+".db");
            SqliteDatabase db(p,forged);db.initialize();db.migrate();const auto before=bytes(p);
            denied([&]{db.guild_membership51();});denied([&]{db.guild_announcements51();});check(before==bytes(p));++cases;
        }
        {
            std::ifstream f(argv[2]);nlohmann::json config;f>>config;
            const auto p=root/"config.json";
            auto load=[&](const nlohmann::json& j){std::ofstream o(p);o<<j.dump();o.close();return Config::load(p);};
            check(!load(config).owned_guild_officers_enabled);
            config["world"]["owned_guild_officers"]={{"enabled",false}};check(!load(config).owned_guild_officers_enabled);
            config["world"]["owned_guild_officers"]["enabled"]=true;check(load(config).owned_guild_officers_enabled);
            for(const auto& value:{nlohmann::json(1),nlohmann::json("true"),nlohmann::json(nullptr)}) {
                auto bad=config;bad["world"]["owned_guild_officers"]["enabled"]=value;denied([&]{load(bad);});
            }
            for(const auto& dependency:{"owned_guild_membership","owned_guild_announcements"}) {
                auto bad=config;bad["world"][dependency]["enabled"]=false;denied([&]{load(bad);});
            }
            ++cases;
        }
        std::cout<<"Schema51Draft "<<cases<<" cases / "<<checks<<" checks passed; private SQLite only; no server/client\n";
        return 0;
    }catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}
}
