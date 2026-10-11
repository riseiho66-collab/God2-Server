#include "db/SqliteOwnedGuildMembershipRepository.h"
#include "db/SqliteOwnedGuildLeaveRepository.h"
#include "db/SqliteSupport.h"
#include "text/LegacyChineseCodec.h"
#include <chrono>
#include <filesystem>
#include <iostream>
#include <limits>
#include <source_location>
#include <utility>

using namespace god2;
namespace {
using Repo=SqliteOwnedGuildMembershipRepository;
unsigned checks=0;
void check(bool value,const std::source_location at=std::source_location::current()) {
    ++checks;if(!value)throw std::runtime_error("Guild membership0078 storage check "+std::to_string(checks)+" failed at line "+std::to_string(at.line()));
}
template<class F> void rejects(F f,const std::source_location at=std::source_location::current()) {
    bool rejected=false;try{f();}catch(const DatabaseError&){rejected=true;}check(rejected,at);
}
std::string rows(sqlite3* db,const std::string& sql) {
    sqlite_detail::Statement q(db,sql.c_str());std::string result;while(q.row())result+=q.text(0)+"\n";return result;
}
std::int64_t scalar(sqlite3* db,const std::string& sql) {sqlite_detail::Statement q(db,sql.c_str());check(q.row());return q.integer(0);}
std::string all(sqlite3* db) {
    return rows(db,"SELECT 'a'||id||hex(username)||hex(password_hash) FROM accounts ORDER BY id")+
      rows(db,"SELECT 'c'||id||':'||account_id||':'||slot||':'||hex(profile)||':'||hex(name_bytes)||':'||name_codepage FROM recovered_characters ORDER BY id")+
      rows(db,"SELECT 'r'||character_id||':'||hex(logical)||':'||revision||':'||design_id FROM character_role_snapshots ORDER BY character_id")+
      rows(db,"SELECT 'w'||character_id||':'||amount||':'||revision||':'||design_id FROM character_trade_wallets ORDER BY character_id")+
      rows(db,"SELECT 's'||character_id||':'||hp||':'||mp||':'||map||':'||xp FROM saved_fixture ORDER BY character_id")+
      rows(db,"SELECT 'g'||id||':'||hex(name_utf8)||':'||revision||':'||origin||':'||design_id||':'||source_sha256 FROM owned_guilds ORDER BY id")+
      rows(db,"SELECT 'm'||character_id||':'||guild_id||':'||revision||':'||origin||':'||design_id||':'||source_sha256 FROM owned_guild_members ORDER BY character_id")+
      rows(db,"SELECT 'o'||guild_id||':'||owner_account||':'||owner_character||':'||created_revision||':'||created_cost||':'||capacity||':'||origin||':'||design_id||':'||source_sha256 FROM owned_guild_governance_0078 ORDER BY guild_id")+
      rows(db,"SELECT 'p'||id||':'||guild_id||':'||hex(guild_name)||':'||observed_revision||':'||character_id||':'||account_id||':'||slot||':'||hex(profile)||':'||hex(name_bytes)||':'||name_codepage||':'||hex(name_utf8)||':'||hex(role)||':'||role_revision||':'||role_design||':'||origin||':'||design_id||':'||source_sha256 FROM owned_guild_applications_0078 ORDER BY id")+
      rows(db,"SELECT name||':'||seq FROM sqlite_sequence ORDER BY name")+
      rows(db,"SELECT 'b'||id||':'||character_id FROM battle_reservations ORDER BY id")+
      rows(db,"SELECT 'bs'||battle_id FROM battle_settlements ORDER BY battle_id");
}
std::string saved(sqlite3* db) {
    return rows(db,"SELECT 'a'||id||hex(username)||hex(password_hash) FROM accounts ORDER BY id")+
      rows(db,"SELECT 'c'||id||':'||account_id||':'||slot||':'||hex(profile)||':'||hex(name_bytes)||':'||name_codepage FROM recovered_characters ORDER BY id")+
      rows(db,"SELECT 'r'||character_id||':'||hex(logical)||':'||revision||':'||design_id FROM character_role_snapshots ORDER BY character_id")+
      rows(db,"SELECT 's'||character_id||':'||hp||':'||mp||':'||map||':'||xp FROM saved_fixture ORDER BY character_id");
}
struct Connection {
    sqlite3* db=nullptr;
    explicit Connection(const std::string& path=":memory:") {
        if(sqlite3_open(path.c_str(),&db)!=SQLITE_OK)throw std::runtime_error("Cannot open isolated membership database");
        sqlite_detail::execute(db,"PRAGMA foreign_keys=ON");
    }
    ~Connection(){if(db)sqlite3_close(db);}
};
struct Fixture {
    Connection connection;
    Repo repo{connection.db};SqliteTradeRepository money{connection.db};SqliteGuildRepository maintenance{connection.db};
    const Repo::Policy policy{50000,30,20};
    const Repo::Proof proof{[]{},[]{}}; // TEST_ONLY isolated readiness fixture.
    explicit Fixture(const std::string& path=":memory:"):connection(path) {
        sqlite_detail::execute(db(),R"SQL(
CREATE TABLE accounts(id INTEGER PRIMARY KEY,username TEXT,password_hash TEXT);
CREATE TABLE recovered_characters(id INTEGER PRIMARY KEY,account_id INTEGER NOT NULL REFERENCES accounts(id),slot INTEGER,profile BLOB,name_bytes BLOB,name_codepage INTEGER);
CREATE TABLE character_role_snapshots(character_id INTEGER PRIMARY KEY REFERENCES recovered_characters(id),logical BLOB,revision INTEGER,design_id TEXT);
CREATE TABLE battle_reservations(id INTEGER PRIMARY KEY,character_id INTEGER REFERENCES recovered_characters(id));
CREATE TABLE battle_settlements(battle_id INTEGER PRIMARY KEY REFERENCES battle_reservations(id));
CREATE TABLE saved_fixture(character_id INTEGER PRIMARY KEY REFERENCES recovered_characters(id),hp INTEGER,mp INTEGER,map INTEGER,xp INTEGER);
)SQL");
        sqlite_detail::execute(db(),SqliteGuildRepository::schema());sqlite_detail::execute(db(),Repo::schema());money.install_schema();
        for(unsigned i=1;i<=55;++i) {
            sqlite_detail::Statement a(db(),"INSERT INTO accounts VALUES(?,?,'untouched-password-hash')");a.bind(1,i);a.bind(2,"Account"+std::to_string(i));a.done();
            const auto text="Player"+std::to_string(i);const std::vector<std::uint8_t> name(text.begin(),text.end());
            std::array<std::uint8_t,40> profile{};std::copy(name.begin(),name.end(),profile.begin());profile[29]=1;
            sqlite_detail::Statement c(db(),"INSERT INTO recovered_characters VALUES(?,?,0,?,?,0)");c.bind(1,i);c.bind(2,i);c.bind_blob(3,profile);c.bind_blob(4,name);c.done();
            RecoveredRoleLevel::Bytes role{};role[0]=0x22;role[1]=35;role[17]=100;role[21]=50;
            sqlite_detail::Statement r(db(),"INSERT INTO character_role_snapshots VALUES(?,?,1,'CUSTOM-0013')");r.bind(1,i);r.bind_blob(2,role);r.done();
            sqlite_detail::Statement s(db(),"INSERT INTO saved_fixture VALUES(?,234,56,101,789)");s.bind(1,i);s.done();
            money.provision_wallet(i,i);
        }
        // Explicit TEST_ONLY money; production never provisions creation credit.
        sqlite_detail::execute(db(),"UPDATE character_trade_wallets SET amount=100000");
    }
    sqlite3* db()const{return connection.db;}
    template<class F> void failed(F f,const std::source_location at=std::source_location::current()) {
        const auto before=all(db());rejects(f,at);check(all(db())==before,at);check(sqlite3_get_autocommit(db())==1,at);
    }
    Repo::Created create(const std::string& name="Guild",unsigned owner=1) {
        return repo.create(repo.nonmember(owner,owner),*money.load_wallet(owner,owner),name,policy,proof);
    }
    Repo::Application apply(std::uint64_t guild,unsigned person=2) {return repo.apply(repo.nonmember(person,person),repo.guild(guild),proof);}
    void rename(unsigned person,const std::string& text) {
        std::array<std::uint8_t,40> profile{};std::copy(text.begin(),text.end(),profile.begin());profile[29]=1;
        const std::vector<std::uint8_t> bytes(text.begin(),text.end());sqlite_detail::Statement q(db(),"UPDATE recovered_characters SET profile=?,name_bytes=? WHERE id=?");
        q.bind_blob(1,profile);q.bind_blob(2,bytes);q.bind(3,person);q.done();
    }
    void rename_legacy(unsigned person,const std::string& text) {
        const auto encoded=LegacyChineseCodec::encode(text,false);
        std::array<std::uint8_t,40> profile{};std::copy(encoded.begin(),encoded.end(),profile.begin());profile[29]=1;
        const std::vector<std::uint8_t> bytes(encoded.begin(),encoded.end());sqlite_detail::Statement q(db(),"UPDATE recovered_characters SET profile=?,name_bytes=?,name_codepage=950 WHERE id=?");
        q.bind_blob(1,profile);q.bind_blob(2,bytes);q.bind(3,person);q.done();
    }
};
}
int main() {
    try {
        rejects([]{Repo invalid(nullptr);});Fixture f;
        const auto identity=f.repo.nonmember(1,1);const auto wallet=*f.money.load_wallet(1,1);const auto saved_before=saved(f.db());
        for(const auto owner:{std::pair{0u,1u},std::pair{1u,0u},std::pair{2u,1u},std::pair{1u,2u},std::pair{99u,99u}})
            f.failed([&]{f.repo.nonmember(owner.first,owner.second);});
        for(const auto text:{"","%s","Has\nControl","0123456789012345"})f.failed([&]{f.repo.create(identity,wallet,text,f.policy,f.proof);});
        f.failed([&]{f.repo.create(identity,wallet,std::string("N\0ul",4),f.policy,f.proof);});
        f.failed([&]{f.repo.create(identity,wallet,"Guild",f.policy,{});});
        f.failed([&]{f.repo.create(identity,wallet,"Guild",f.policy,{[]{},{}});});
        for(const auto policy:{Repo::Policy{0,30,20},Repo::Policy{50000,0,20},Repo::Policy{50000,30,0},Repo::Policy{50000,30,51},Repo::Policy{50000,36,20}})
            f.failed([&]{f.repo.create(identity,wallet,"Guild",policy,f.proof);});
        auto stale=identity;stale.account_id=2;f.failed([&]{f.repo.create(stale,wallet,"Guild",f.policy,f.proof);});
        stale=identity;stale.profile[30]++;f.failed([&]{f.repo.create(stale,wallet,"Guild",f.policy,f.proof);});
        stale=identity;stale.role->revision++;f.failed([&]{f.repo.create(stale,wallet,"Guild",f.policy,f.proof);});
        stale=identity;stale.role.reset();f.failed([&]{f.repo.create(stale,wallet,"Guild",f.policy,f.proof);});
        for(const auto invalid:{Repo::Wallet{49999,1},Repo::Wallet{100000,0},Repo::Wallet{100000,2},Repo::Wallet{100000,9223372036854775807ULL}})
            f.failed([&]{f.repo.create(identity,invalid,"Guild",f.policy,f.proof);});
        sqlite_detail::execute(f.db(),"INSERT INTO battle_reservations VALUES(1,1)");
        f.failed([&]{f.repo.create(identity,wallet,"Guild",f.policy,f.proof);});sqlite_detail::execute(f.db(),"DELETE FROM battle_reservations");
        const auto fail=[]{throw DatabaseError("Test proof rejects");};
        f.failed([&]{f.repo.create(identity,wallet,"Guild",f.policy,{fail,[]{}});});
        f.failed([&]{f.repo.create(identity,wallet,"Guild",f.policy,{[]{},fail});});
        for(const auto trigger:{
            "CREATE TRIGGER fault BEFORE INSERT ON owned_guilds BEGIN SELECT RAISE(ABORT,'guild failure'); END",
            "CREATE TRIGGER fault BEFORE INSERT ON owned_guild_members BEGIN SELECT RAISE(ABORT,'member failure'); END",
            "CREATE TRIGGER fault BEFORE INSERT ON owned_guild_governance_0078 BEGIN SELECT RAISE(ABORT,'governance failure'); END",
            "CREATE TRIGGER fault BEFORE UPDATE ON character_trade_wallets BEGIN SELECT RAISE(ABORT,'wallet failure'); END",
            "CREATE TRIGGER fault AFTER INSERT ON owned_guilds BEGIN UPDATE owned_guilds SET name_utf8='Wrong' WHERE id=NEW.id; END",
            "CREATE TRIGGER fault AFTER INSERT ON owned_guild_governance_0078 BEGIN UPDATE owned_guild_governance_0078 SET capacity=10 WHERE guild_id=NEW.guild_id; END",
            "CREATE TRIGGER fault AFTER UPDATE ON character_trade_wallets BEGIN UPDATE character_trade_wallets SET amount=77 WHERE character_id=NEW.character_id; END",
            "CREATE TRIGGER fault AFTER INSERT ON owned_guild_members BEGIN UPDATE saved_fixture SET hp=1 WHERE character_id=2; END",
            "CREATE TRIGGER fault AFTER INSERT ON owned_guild_members BEGIN UPDATE accounts SET password_hash='corrupt' WHERE id=2; END",
            "CREATE TRIGGER fault AFTER INSERT ON owned_guild_members BEGIN UPDATE character_trade_wallets SET amount=0 WHERE character_id=2; END"}) {
            sqlite_detail::execute(f.db(),trigger);f.failed([&]{f.create();});sqlite_detail::execute(f.db(),"DROP TRIGGER fault");
        }
        const auto created=f.create();const auto guild=created.leader.governance.guild_id;
        check(created.wallet==Repo::Wallet{50000,2});check(created.leader.governance.capacity==20);
        check(created.leader.membership.name_utf8=="Guild");check(saved(f.db())==saved_before);
        check(f.maintenance.load(1,1)==std::optional(created.leader.membership));
        check(f.repo.find_by_name("gUiLd")==std::optional(f.repo.guild(guild)));
        check(!f.repo.find_by_name("Missing"));check(f.repo.applications(guild).empty());
        f.failed([&]{f.repo.create(identity,wallet,"Other",f.policy,f.proof);});
        f.failed([&]{f.create("gUiLd",2);});f.failed([&]{f.create("Guild",2);});
        const auto second=f.create("Other",3);check(second.leader.governance.guild_id!=guild);
        const auto applicant=f.repo.nonmember(2,2);const auto target=f.repo.guild(guild);
        auto wrong=target;wrong.revision++;f.failed([&]{f.repo.apply(applicant,wrong,f.proof);});
        wrong=target;wrong.name_utf8="guild";f.failed([&]{f.repo.apply(applicant,wrong,f.proof);});
        f.failed([&]{f.repo.apply(applicant,target,{});});
        f.failed([&]{f.repo.apply(applicant,target,{[]{},fail});});
        const auto applied=f.apply(guild);check(!f.maintenance.load(2,2));check(f.repo.pending(2,2)==std::optional(applied));
        check(f.repo.applications(guild)==std::vector<Repo::Application>{applied});
        f.failed([&]{f.apply(guild);});f.failed([&]{f.repo.create(applicant,*f.money.load_wallet(2,2),"Third",f.policy,f.proof);});
        f.failed([&]{f.repo.cancel(f.repo.identity(4,4),applied,f.proof);});
        f.failed([&]{f.repo.reject(second.leader,applied,f.proof);});
        f.failed([&]{f.repo.approve(second.leader,applied,f.proof);});
        auto changed_applied=applied;changed_applied.id++;f.failed([&]{f.repo.approve(f.repo.leader(1,1),changed_applied,f.proof);});
        changed_applied=applied;changed_applied.applicant.role->revision++;f.failed([&]{f.repo.approve(f.repo.leader(1,1),changed_applied,f.proof);});
        auto old_leader=f.repo.leader(1,1);auto changed_leader=old_leader;changed_leader.governance.capacity++;
        f.failed([&]{f.repo.approve(changed_leader,applied,f.proof);});
        changed_leader=old_leader;changed_leader.roster.clear();f.failed([&]{f.repo.approve(changed_leader,applied,f.proof);});
        sqlite_detail::execute(f.db(),"UPDATE character_role_snapshots SET revision=2 WHERE character_id=2");
        f.failed([&]{f.repo.approve(old_leader,applied,f.proof);});sqlite_detail::execute(f.db(),"UPDATE character_role_snapshots SET revision=1 WHERE character_id=2");
        f.failed([&]{f.repo.approve(old_leader,applied,{[]{},fail});});
        f.failed([&]{f.repo.approve(old_leader,applied,{[]{},[&]{sqlite_detail::execute(f.db(),"UPDATE saved_fixture SET hp=1 WHERE character_id=5");}});});
        for(const auto trigger:{
            "CREATE TRIGGER fault BEFORE INSERT ON owned_guild_members BEGIN SELECT RAISE(ABORT,'member failure'); END",
            "CREATE TRIGGER fault BEFORE DELETE ON owned_guild_applications_0078 BEGIN SELECT RAISE(ABORT,'pending failure'); END",
            "CREATE TRIGGER fault AFTER INSERT ON owned_guild_members BEGIN UPDATE saved_fixture SET xp=0 WHERE character_id=4; END",
            "CREATE TRIGGER fault AFTER DELETE ON owned_guild_applications_0078 BEGIN UPDATE owned_guilds SET revision=revision+1 WHERE id=OLD.guild_id; END"}) {
            sqlite_detail::execute(f.db(),trigger);f.failed([&]{f.repo.approve(old_leader,applied,f.proof);});sqlite_detail::execute(f.db(),"DROP TRIGGER fault");
        }
        const auto before_approval=saved(f.db());const auto wallet_rows=rows(f.db(),"SELECT character_id||':'||amount||':'||revision FROM character_trade_wallets ORDER BY character_id");
        const auto approved=f.repo.approve(old_leader,applied,f.proof);check(approved.leader.roster.size()==2);
        check(f.maintenance.load(2,2)==std::optional(approved.joined));check(!f.repo.pending(2,2));check(saved(f.db())==before_approval);
        check(rows(f.db(),"SELECT character_id||':'||amount||':'||revision FROM character_trade_wallets ORDER BY character_id")==wallet_rows);
        f.failed([&]{f.repo.approve(old_leader,applied,f.proof);}); // Duplicate approval/replay.
        auto cancel=f.apply(guild,4);f.repo.cancel(cancel.applicant,cancel,f.proof);check(!f.repo.pending(4,4));
        auto reapplied=f.apply(guild,4);check(reapplied.id>cancel.id);f.failed([&]{f.repo.cancel(reapplied.applicant,cancel,f.proof);});
        f.repo.reject(f.repo.leader(1,1),reapplied,f.proof);check(!f.repo.pending(4,4));
        f.failed([&]{f.repo.reject(f.repo.leader(1,1),reapplied,f.proof);});
        const auto stale_application=f.apply(guild,4);
        sqlite_detail::execute(f.db(),"UPDATE character_role_snapshots SET revision=revision+1 WHERE character_id=4");
        f.failed([&]{f.repo.approve(f.repo.leader(1,1),stale_application,f.proof);});
        f.repo.cancel(f.repo.nonmember(4,4),stale_application,f.proof);check(!f.repo.pending(4,4));

        // Native bytewise folded name ambiguity must reject both create and join.
        Fixture collision;collision.rename(2,"pLaYeR1");const auto cg=collision.create().leader.governance.guild_id;
        collision.failed([&]{collision.apply(cg);});
        // Distinct Unicode characters encode CP950 A141/A161: original bytewise
        // ASCII folding aliases the trail bytes even though CP936 differs.
        check(LegacyChineseCodec::encode("，",false)==std::string("\xA1\x41",2));
        check(LegacyChineseCodec::encode("｛",false)==std::string("\xA1\x61",2));
        Fixture multibyte;multibyte.create("，");multibyte.failed([&]{multibyte.create("｛",2);});
        multibyte.failed([&]{multibyte.repo.find_by_name("｛");});
        Fixture member_multibyte;member_multibyte.rename_legacy(1,"，");member_multibyte.rename_legacy(2,"｛");
        const auto mg=member_multibyte.create().leader.governance.guild_id;
        member_multibyte.failed([&]{member_multibyte.apply(mg);});
        // Creation minimum level and absent role/foreign provenance are fail closed.
        Fixture missing;sqlite_detail::execute(missing.db(),"DELETE FROM character_role_snapshots WHERE character_id=1");
        missing.failed([&]{missing.create();});
        Fixture wallet_missing;sqlite_detail::execute(wallet_missing.db(),"DELETE FROM character_trade_wallets WHERE character_id=1");
        wallet_missing.failed([&]{wallet_missing.repo.create(wallet_missing.repo.nonmember(1,1),wallet,"Guild",wallet_missing.policy,wallet_missing.proof);});
        Fixture battle;const auto bg=battle.create().leader.governance.guild_id;const auto ba=battle.apply(bg);
        const auto bl=battle.repo.leader(1,1);sqlite_detail::execute(battle.db(),"INSERT INTO battle_reservations VALUES(1,2)");
        battle.failed([&]{battle.repo.approve(bl,ba,battle.proof);});
        sqlite_detail::execute(battle.db(),"INSERT INTO battle_settlements VALUES(1)");
        battle.repo.approve(battle.repo.leader(1,1),ba,battle.proof);check(bool(battle.maintenance.load(2,2)));
        Fixture pending_trigger;const auto ptg=pending_trigger.create().leader.governance.guild_id;
        for(const auto trigger:{
            "CREATE TRIGGER fault AFTER INSERT ON owned_guild_applications_0078 BEGIN UPDATE owned_guild_applications_0078 SET id=id+100 WHERE id=NEW.id; END",
            "CREATE TRIGGER fault AFTER INSERT ON owned_guild_applications_0078 BEGIN UPDATE owned_guild_applications_0078 SET role_revision=role_revision+1 WHERE id=NEW.id; END",
            "CREATE TRIGGER fault AFTER INSERT ON owned_guild_applications_0078 BEGIN UPDATE saved_fixture SET hp=0 WHERE character_id=4; END"}) {
            sqlite_detail::execute(pending_trigger.db(),trigger);pending_trigger.failed([&]{pending_trigger.apply(ptg);});sqlite_detail::execute(pending_trigger.db(),"DROP TRIGGER fault");
        }
        pending_trigger.failed([&]{pending_trigger.repo.apply(pending_trigger.repo.nonmember(2,2),pending_trigger.repo.guild(ptg),
            {[]{},[&]{sqlite_detail::execute(pending_trigger.db(),"UPDATE sqlite_sequence SET seq=seq+100 WHERE name='owned_guild_applications_0078'");}});});
        Fixture provenance;const auto pg=provenance.create().leader.governance.guild_id;
        const auto pa=provenance.apply(pg);const auto pl=provenance.repo.leader(1,1);
        sqlite_detail::execute(provenance.db(),"PRAGMA ignore_check_constraints=ON");
        sqlite_detail::execute(provenance.db(),"UPDATE owned_guild_governance_0078 SET source_sha256='wrong'");
        provenance.failed([&]{provenance.repo.approve(pl,pa,provenance.proof);});
        provenance.failed([&]{provenance.repo.find_by_name("Guild");});
        Fixture sequence_overflow;const auto sg=sequence_overflow.create().leader.governance.guild_id;
        const auto sa=sequence_overflow.apply(sg);sequence_overflow.repo.cancel(sa.applicant,sa,sequence_overflow.proof);
        sqlite_detail::execute(sequence_overflow.db(),"UPDATE sqlite_sequence SET seq=9223372036854775807 WHERE name='owned_guild_applications_0078'");
        sequence_overflow.failed([&]{sequence_overflow.apply(sg);});

        // Capacity is reviewed policy20, not native technical50. Pending grants
        // are rechecked under the reserved writer lock, including the last seat.
        Fixture full;const auto fg=full.create().leader.governance.guild_id;
        auto final_pending=full.apply(fg,21);
        for(unsigned i=2;i<=20;++i) {auto app=full.apply(fg,i);full.repo.approve(full.repo.leader(1,1),app,full.proof);}
        check(full.repo.leader(1,1).roster.size()==20);
        full.failed([&]{full.repo.approve(full.repo.leader(1,1),final_pending,full.proof);});
        full.failed([&]{full.apply(fg,22);});check(!full.maintenance.load(21,21));

        Fixture overflow;const auto og=overflow.create().leader.governance.guild_id;const auto oa=overflow.apply(og);
        const auto ol=overflow.repo.leader(1,1);overflow.maintenance.admin_create("Clock");
        sqlite_detail::execute(overflow.db(),"UPDATE owned_guilds SET revision=9223372036854775807 WHERE name_utf8='Clock'");
        overflow.failed([&]{overflow.repo.approve(ol,oa,overflow.proof);});overflow.failed([&]{overflow.create("New",3);});

        // Original owner leaving cannot silently give another member approval
        // authority; retained governance does not authenticate a departed owner.
        Fixture left;const auto lc=left.create();const auto lg=lc.leader.governance.guild_id;const auto la=left.apply(lg);
        SqliteOwnedGuildLeaveRepository leave(left.db());leave.leave(1,1,lc.leader.membership);
        left.failed([&]{left.repo.approve(lc.leader,la,left.proof);});

        const auto path=std::filesystem::temp_directory_path()/
            ("god2-owned-guild-membership-0078-"+std::to_string(std::chrono::steady_clock::now().time_since_epoch().count())+".db");
        struct Cleanup {std::filesystem::path path;~Cleanup(){std::error_code e;std::filesystem::remove(path,e);}} cleanup{path};
        {
            Fixture disk(path.string());Connection other(path.string());Repo peer(other.db);
            const auto created_disk=disk.create();const auto dg=created_disk.leader.governance.guild_id;
            const auto first=disk.apply(dg,2),second_pending=disk.apply(dg,3);const auto lease=disk.repo.leader(1,1);
            peer.approve(peer.leader(1,1),second_pending,disk.proof);
            disk.failed([&]{disk.repo.approve(lease,first,disk.proof);});
            disk.repo.approve(disk.repo.leader(1,1),first,disk.proof);check(peer.leader(1,1).roster.size()==3);
            disk.failed([&]{peer.approve(peer.leader(1,1),first,disk.proof);});
        }
        check(scalar(f.db(),"SELECT count(*) FROM pragma_foreign_key_check")==0);
        check(scalar(full.db(),"SELECT count(*) FROM pragma_foreign_key_check")==0);
        std::cout<<"PASS "<<checks<<" isolated CUSTOM-0078 create/apply/approve/deny/CAS/rollback/preservation checks\n";
        return 0;
    }catch(const std::exception& error) {std::cerr<<error.what()<<'\n';return 1;}
}
