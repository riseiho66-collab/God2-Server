#include "db/SqliteMigrationManager.h"
#include "db/SqliteRecoveredCharacterRepository.h"
#include "db/SqliteSupport.h"
#include <limits>
#include <memory>
#include <stdexcept>
#include <string>

namespace {
void require(bool condition, const char* message) {
    if (!condition) throw std::runtime_error(message);
}
template<class F> void expect_database_error(F&& function, const char* message) {
    try { function(); } catch (const god2::DatabaseError&) { return; }
    throw std::runtime_error(message);
}
struct Fixture {
    struct Close { void operator()(sqlite3* db) const { sqlite3_close_v2(db); } };
    std::unique_ptr<sqlite3, Close> db;
    god2::RecoveredCharacter first, second, other;

    Fixture() {
        sqlite3* raw = nullptr;
        const int result = sqlite3_open(":memory:", &raw);
        db.reset(raw);
        require(result == SQLITE_OK, "Unable to open position test database");
        execute("PRAGMA foreign_keys=ON");
        auto migrations = god2::default_sqlite_migrations();
        require(migrations.size() >= 3 && migrations[2].version == 3 &&
                migrations[2].name == "recovered_positions", "Missing position migration");
        auto old = migrations;
        old.resize(2);
        god2::SqliteMigrationManager(db.get(), old).migrate();
        execute("INSERT INTO accounts(id,username,password_hash) VALUES(1,'first','hash'),(2,'other','hash')");
        execute("INSERT INTO characters(account_id,name,x,y) VALUES(1,'mock',123,456)");
        std::array<std::uint8_t, 40> profile{};
        profile[0] = 'A';
        profile[39] = 0xff;
        // Seed the historical v2 schema directly. The current repository
        // requires name_codepage from later migrations and is not a v2 API.
        // Keep characters present before v3 to verify no position backfill.
        auto seed = [&](std::uint64_t account, std::uint8_t slot) {
            god2::sqlite_detail::Statement insert(db.get(),
                "INSERT INTO recovered_characters(account_id,slot,profile,name_bytes) VALUES(?,?,?,?)");
            insert.bind_id(1,account);insert.bind(2,slot);insert.bind_blob(3,profile);
            insert.bind_blob(4,std::span<const std::uint8_t>(profile.data(),1));insert.done();
        };
        seed(1,0);
        profile[0] = 'B';
        seed(1,1);
        profile[0] = 'C';
        seed(2,0);
        god2::SqliteMigrationManager(db.get(), migrations).migrate();
        god2::SqliteMigrationManager(db.get(), migrations).migrate();
        const auto own=repository().list_for_account(1);
        const auto others=repository().list_for_account(2);
        require(own.size()==2 && others.size()==1,"Historical profiles missing after migration");
        first=own[0];second=own[1];other=others[0];
        require(scalar("SELECT count(*) FROM recovered_positions") == 0,
                "Migration synthesized positions");
    }
    god2::SqliteRecoveredCharacterRepository repository() { return god2::SqliteRecoveredCharacterRepository(db.get()); }
    void execute(const std::string& sql) { god2::sqlite_detail::execute(db.get(), sql); }
    std::int64_t scalar(const char* sql) {
        god2::sqlite_detail::Statement statement(db.get(), sql);
        require(statement.row(), "Missing position test scalar");
        return statement.integer(0);
    }
    void require_unrelated_unchanged() {
        const auto own = repository().list_for_account(1);
        const auto others = repository().list_for_account(2);
        require(own.size() == 2 && others.size() == 1 && own[0].id == first.id &&
                own[1].id == second.id && others[0].id == other.id &&
                own[0].profile == first.profile && own[1].profile == second.profile &&
                others[0].profile == other.profile && own[0].created_at == first.created_at,
                "Position operation changed recovered character profiles");
        require(scalar("SELECT count(*) FROM accounts WHERE password_hash='hash'") == 2 &&
                scalar("SELECT count(*) FROM characters") == 1 &&
                scalar("SELECT count(*) FROM characters WHERE name='mock' AND x=123 AND y=456") == 1,
                "Position operation mutated accounts or mock characters");
    }
};

void test_ownership_and_cas() {
    using namespace god2;
    Fixture f;
    auto repository = f.repository();
    RecoveredCharacterRepository& api = repository;
    require(!api.load_position(1, f.first.id), "New character unexpectedly has a position");
    for (const auto invalid : {std::uint64_t{0}, std::uint64_t{999999},
                              std::numeric_limits<std::uint64_t>::max()}) {
        expect_database_error([&] { api.load_position(invalid, f.first.id); }, "Invalid account loaded position");
        expect_database_error([&] { api.load_position(1, invalid); }, "Invalid character loaded position");
        expect_database_error([&] { api.commit_position(invalid, f.first.id, {}, 0, 0, 0, 0); },
                              "Invalid account committed position");
        expect_database_error([&] { api.commit_position(1, invalid, {}, 0, 0, 0, 0); },
                              "Invalid character committed position");
    }
    expect_database_error([&] { api.load_position(2, f.first.id); }, "Unowned absent position returned empty");
    expect_database_error([&] { api.commit_position(2, f.first.id, {}, 0, 0, 0, 0); },
                          "Unowned absent position was inserted");
    const RecoveredPosition initial{0, 0, 0, 0, 1};
    expect_database_error([&] { api.commit_position(1, f.first.id, initial, 0, 0, 0, 0); },
                          "Expected existing position inserted missing row");
    require(api.commit_position(1, f.first.id, {}, 0, 0, 0, 0) == initial,
            "Initial position or revision is incorrect");
    expect_database_error([&] { api.load_position(2, f.first.id); }, "Unowned saved position was loaded");
    expect_database_error([&] { api.commit_position(2, f.first.id, initial, 0, 0, 1, 1); },
                          "Unowned saved position was updated");
    expect_database_error([&] { api.commit_position(1, f.first.id, {}, 0, 0, 1, 1); },
                          "Absent expectation replaced an existing position");
    for (int field = 0; field < 5; ++field) {
        auto stale = initial;
        switch (field) {
        case 0: ++stale.area; break;
        case 1: ++stale.scene; break;
        case 2: ++stale.x; break;
        case 3: ++stale.y; break;
        case 4: ++stale.revision; break;
        }
        expect_database_error([&] { api.commit_position(1, f.first.id, stale, 1, 2, 3, 4); },
                              "CAS did not compare every prior position field");
        require(api.load_position(1, f.first.id) == initial, "Failed CAS mutated position");
    }
    const RecoveredPosition maximum{63, 1023, 65535, 65535, 2};
    require(api.commit_position(1, f.first.id, initial, 63, 1023, 65535, 65535) == maximum &&
            f.repository().load_position(1, f.first.id) == maximum, "Maximum position did not commit");
    expect_database_error([&] { api.commit_position(1, f.first.id, initial, 0, 0, 0, 0); },
                          "Old reader overwrote committed position");
    const RecoveredPosition unchanged{63, 1023, 65535, 65535, 3};
    require(api.commit_position(1, f.first.id, maximum, 63, 1023, 65535, 65535) == unchanged,
            "Same-position commit did not advance revision");
    for (const auto invalid : {std::uint16_t{64}, std::uint16_t{65535}})
        expect_database_error([&] { api.commit_position(1, f.first.id, unchanged, invalid, 0, 0, 0); },
                              "Invalid area accepted");
    for (const auto invalid : {std::uint16_t{1024}, std::uint16_t{65535}})
        expect_database_error([&] { api.commit_position(1, f.second.id, {}, 0, invalid, 0, 0); },
                              "Invalid scene accepted");
    require(api.load_position(1, f.first.id) == unchanged && !api.load_position(1, f.second.id) &&
            !api.load_position(2, f.other.id), "Rejected writes affected another position");
    f.require_unrelated_unchanged();
}

void test_constraints_corruption_and_overflow() {
    using namespace god2;
    Fixture f;
    auto repository = f.repository();
    const auto initial = repository.commit_position(1, f.first.id, {}, 1, 2, 3, 4);
    const auto where = " WHERE character_id=" + std::to_string(f.first.id);
    expect_database_error([&] {
        f.execute("INSERT INTO recovered_positions VALUES(999999,0,0,0,0,1)");
    }, "Position schema accepted an unknown character");
    expect_database_error([&] {
        f.execute("DELETE FROM recovered_characters WHERE id=" + std::to_string(f.first.id));
    }, "Position foreign key allowed removal of its character");
    for (const auto* mutation : {
            "area=-1", "area=64", "area=65536", "area=1.5", "area='bad'", "area=X'01'",
            "scene=-1", "scene=1024", "scene=1.5", "scene='bad'", "scene=X'01'",
            "x=-1", "x=65536", "x=1.5", "x='bad'", "x=X'01'",
            "y=-1", "y=65536", "y=1.5", "y='bad'", "y=X'01'",
            "revision=0", "revision=-1", "revision=1.5", "revision='bad'", "revision=X'01'",
            "revision=9223372036854775808"}) {
        const auto sql = std::string("UPDATE recovered_positions SET ") + mutation + where;
        expect_database_error([&] { f.execute(sql); }, "Position schema accepted invalid data");
        require(repository.load_position(1, f.first.id) == initial, "Constraint failure changed position");
        f.execute("PRAGMA ignore_check_constraints=ON");
        f.execute(sql);
        expect_database_error([&] { repository.load_position(1, f.first.id); }, "Corrupt position was loaded");
        expect_database_error([&] { repository.commit_position(1, f.first.id, initial, 0, 0, 0, 0); },
                              "Corrupt position was overwritten");
        expect_database_error([&] { repository.commit_position(1, f.first.id, {}, 0, 0, 0, 0); },
                              "Corrupt position was treated as absent");
        f.execute("UPDATE recovered_positions SET area=1,scene=2,x=3,y=4,revision=1" + where);
        f.execute("PRAGMA ignore_check_constraints=OFF");
    }
    for (const auto* column : {"area", "scene", "x", "y", "revision"})
        expect_database_error([&] {
            f.execute(std::string("UPDATE recovered_positions SET ") + column + "=NULL" + where);
        }, "Position schema accepted null data");
    f.execute("UPDATE recovered_positions SET revision=9223372036854775806" + where);
    auto penultimate = *repository.load_position(1, f.first.id);
    const auto last = repository.commit_position(1, f.first.id, penultimate, 1, 2, 3, 4);
    require(last.revision == static_cast<std::uint64_t>(std::numeric_limits<std::int64_t>::max()),
            "Last signed SQLite revision could not commit");
    expect_database_error([&] { repository.commit_position(1, f.first.id, last, 0, 0, 0, 0); },
                          "Revision overflow accepted");
    auto oversized = last;
    oversized.revision = std::numeric_limits<std::uint64_t>::max();
    expect_database_error([&] { repository.commit_position(1, f.first.id, oversized, 0, 0, 0, 0); },
                          "Unsigned expected revision overflow accepted");
    require(repository.load_position(1, f.first.id) == last, "Overflow changed position");
    f.require_unrelated_unchanged();
}

void test_battle_settlement_atomicity() {
    using namespace god2;
    Fixture f;
    auto repo=f.repository();
    require(!repo.load_experience(1,f.first.id),"Missing XP row treated as existing zero");
    for(const auto invalid:{std::uint64_t{0},std::uint64_t{99999},std::numeric_limits<std::uint64_t>::max()}) {
        expect_database_error([&]{repo.load_experience(invalid,f.first.id);},"Invalid account read XP");
        expect_database_error([&]{repo.load_experience(1,invalid);},"Invalid character read XP");
    }
    expect_database_error([&]{repo.load_experience(2,f.first.id);},"Foreign missing XP read");
    const auto initial=repo.commit_resources(1,f.first.id,{},CharacterResources{100,120,50,80,0,"CUSTOM-0012"});
    const auto battle=repo.reserve_battle(1,f.first.id,initial);
    auto next=initial;next.hp=76;next.mp=26;
    const auto attempt=[&] { return repo.settle_battle(1,f.first.id,battle,initial,next,true,25); };
    const auto unchanged=[&] {
        require(repo.load_resources(1,f.first.id)==initial &&
                f.scalar("SELECT count(*) FROM character_experience")==0 &&
                f.scalar("SELECT count(*) FROM battle_settlements")==0 &&
                sqlite3_get_autocommit(f.db.get()),"Settlement failure left partial state");
        f.require_unrelated_unchanged();
    };
    expect_database_error([&]{repo.settle_battle(2,f.first.id,battle,initial,next,true,25);},"Foreign settlement accepted");
    expect_database_error([&]{repo.settle_battle(1,f.first.id,99999,initial,next,true,25);},"Unknown battle accepted");
    expect_database_error([&]{repo.settle_battle(1,f.first.id,battle,initial,next,false,25);},"Loss awarded experience");
    auto stale=initial;stale.mp--;
    expect_database_error([&]{repo.settle_battle(1,f.first.id,battle,stale,next,true,25);},"Stale settlement accepted");
    unchanged();
    for(const auto* table : {"character_resources","character_experience","battle_settlements"}) {
        const std::string event=std::string(table)=="character_resources" ? "UPDATE" : "INSERT";
        f.execute("CREATE TRIGGER settlement_fail AFTER "+event+" ON "+table+
            " BEGIN UPDATE accounts SET password_hash='changed' WHERE id=1; SELECT RAISE(FAIL,'injected'); END");
        expect_database_error(attempt,"Injected settlement failure accepted");
        unchanged();f.execute("DROP TRIGGER settlement_fail");
    }
    for(const auto* effect : {
            "UPDATE character_resources SET mp=0;",
            "UPDATE character_experience SET total=999;",
            "UPDATE battle_settlements SET resource_revision=99;",
            "DELETE FROM battle_settlements;"}) {
        f.execute(std::string("CREATE TRIGGER settlement_corrupt AFTER INSERT ON battle_settlements BEGIN ")+effect+" END");
        expect_database_error(attempt,"Corrupt settlement passed readback");
        unchanged();f.execute("DROP TRIGGER settlement_corrupt");
    }
    const auto result=attempt();
    require(repo.load_experience(1,f.first.id)==CharacterExperience{25,"CUSTOM-0012"},"Owned XP unavailable");
    expect_database_error([&]{repo.load_experience(2,f.first.id);},"Foreign saved XP read");
    require(result.resources.hp==76 && result.resources.mp==26 && result.resources.revision==2 &&
            result.total_experience==25 && attempt()==result,"Settlement or exact retry differs");
    auto changed=next;changed.hp--;
    expect_database_error([&]{repo.settle_battle(1,f.first.id,battle,initial,changed,true,25);},"Changed terminal resources replayed");
    expect_database_error([&]{repo.settle_battle(1,f.first.id,battle,initial,next,true,26);},"Changed award replayed");
    expect_database_error([&]{repo.settle_battle(2,f.first.id,battle,initial,next,true,25);},"Foreign retry accepted");
    const auto second=repo.reserve_battle(1,f.first.id,result.resources);
    auto dead=result.resources;dead.hp=0;
    const auto lost=repo.settle_battle(1,f.first.id,second,result.resources,dead,false,0);
    require(lost.total_experience==25 && lost.resources.hp==0 && lost.resources.revision==3,
            "Loss changed experience or failed persistence");
    require(attempt()==result && repo.load_resources(1,f.first.id)==lost.resources &&
            f.scalar("SELECT total FROM character_experience")==25 &&
            f.scalar("SELECT count(*) FROM battle_settlements")==2,"Old replay overwrote later settlement");
    auto alive=lost.resources;alive.hp=100;
    alive=repo.commit_resources(1,f.first.id,lost.resources,alive);
    const auto third=repo.reserve_battle(1,f.first.id,alive);
    f.execute("UPDATE character_experience SET total=9223372036854775807");
    require(repo.load_experience(1,f.first.id)->total==static_cast<std::uint64_t>(std::numeric_limits<std::int64_t>::max()),
            "XP load truncated signed64 maximum");
    expect_database_error([&]{repo.settle_battle(1,f.first.id,third,alive,next,true,1);},"XP overflow accepted");
    require(repo.load_resources(1,f.first.id)==alive && f.scalar("SELECT count(*) FROM battle_settlements")==2,
            "XP overflow partially committed");
    f.require_unrelated_unchanged();
}

void test_role_resource_transaction() {
    using namespace god2;
    Fixture f;auto repo=f.repository();
    require(!repo.load_role(1,f.first.id),"Migration fabricated role state");
    const auto initial=repo.commit_resources(1,f.first.id,{}, {76,120,26,80,0,"CUSTOM-0012"});
    CharacterRoleSnapshot role{};role.logical.fill(0xa5);role.logical[0]=0x22;role.logical[1]=2;
    role.design_id="CUSTOM-0013";
    const auto set_max=[](auto& row,std::uint32_t hp,std::uint32_t mp) {
        for(unsigned i=0;i<4;++i) {row.logical[17+i]=static_cast<std::uint8_t>(hp>>(8*i));row.logical[21+i]=static_cast<std::uint8_t>(mp>>(8*i));}
    };
    set_max(role,120,80);
    expect_database_error([&]{repo.load_role(2,f.first.id);},"Foreign role read accepted");
    expect_database_error([&]{repo.commit_role_resources(2,f.first.id,{},initial,role,initial);},"Foreign role write accepted");
    auto invalid=role;invalid.logical[1]=0;
    expect_database_error([&]{repo.commit_role_resources(1,f.first.id,{},initial,invalid,initial);},"Invalid zero role level accepted");
    invalid=role;set_max(invalid,121,80);
    expect_database_error([&]{repo.commit_role_resources(1,f.first.id,{},initial,invalid,initial);},"Divergent resource maxima accepted");
    auto first=repo.commit_role_resources(1,f.first.id,{},initial,role,initial);
    require(first.role.revision==1 && first.resources.revision==2 && repo.load_role(1,f.first.id)==first.role,
            "Initial full role snapshot failed");
    auto next=first.role;next.logical[1]=3;set_max(next,50,10);
    auto resources=first.resources;resources.hp=50;resources.max_hp=50;resources.mp=10;resources.max_mp=10;
    const auto attempt=[&]{return repo.commit_role_resources(1,f.first.id,first.role,first.resources,next,resources);};
    expect_database_error([&]{repo.commit_resources(1,f.first.id,first.resources,resources);},"Resource-only write split stored maxima");
    for(const auto* effect:{"SELECT RAISE(FAIL,'injected');",
                           "DELETE FROM character_role_snapshots;",
                           "UPDATE character_role_snapshots SET revision=99;"}) {
        f.execute(std::string("CREATE TRIGGER role_fail AFTER UPDATE ON character_resources BEGIN ")+effect+" END");
        expect_database_error(attempt,"Role/resource transaction ignored late failure");
        require(repo.load_role(1,f.first.id)==first.role && repo.load_resources(1,f.first.id)==first.resources &&
                sqlite3_get_autocommit(f.db.get()),"Role/resource write partially committed");
        f.execute("DROP TRIGGER role_fail");
    }
    const auto committed=attempt();
    require(committed.role.revision==2 && committed.resources.revision==3 && committed.resources.hp==50 && committed.resources.mp==10,
            "Atomic role/resource update failed");
    for(std::size_t i=0;i<25;++i) if(i!=1 && i<17) require(committed.role.logical[i]==first.role.logical[i],"Opaque/base fields changed");
    expect_database_error(attempt,"Stale full role snapshot accepted");
    auto ordinary=committed.resources;ordinary.hp=40;
    require(repo.commit_resources(1,f.first.id,committed.resources,ordinary).hp==40,"Normal damage blocked by role state");
    require(repo.load_role(1,f.first.id)==committed.role,"Ordinary HP debit rewrote role snapshot");
    require(f.scalar("SELECT count(*) FROM character_experience")==0,"Role commit invented XP");
    const auto before=*repo.load_resources(1,f.first.id);
    const auto battle=repo.reserve_battle(1,f.first.id,before);
    auto leveled=committed.role;leveled.logical[1]=4;set_max(leveled,70,20);
    auto final_resources=before;final_resources.max_hp=70;final_resources.max_mp=20;final_resources.mp=5;
    const BattleProgressionCommit change{{},committed.role,leveled};
    const auto settle=[&]{return repo.settle_battle(1,f.first.id,battle,before,final_resources,true,25,change);};
    auto stale_xp=change;stale_xp.expected_experience=CharacterExperience{1,"CUSTOM-0012"};
    expect_database_error([&]{repo.settle_battle(1,f.first.id,battle,before,final_resources,true,25,stale_xp);},
                          "Progression computed against stale XP accepted");
    auto stale_role=change;stale_role.expected_role->revision--;
    expect_database_error([&]{repo.settle_battle(1,f.first.id,battle,before,final_resources,true,25,stale_role);},
                          "Progression computed against stale role accepted");
    for(const auto* effect:{"SELECT RAISE(FAIL,'late failure');",
                           "UPDATE character_role_snapshots SET revision=99;",
                           "UPDATE character_experience SET total=999;"}) {
        f.execute(std::string("CREATE TRIGGER progression_fail AFTER INSERT ON battle_settlements BEGIN ")+effect+" END");
        expect_database_error(settle,"Combined progression ignored late failure");
        require(repo.load_role(1,f.first.id)==committed.role && repo.load_resources(1,f.first.id)==before &&
                !repo.load_experience(1,f.first.id) && f.scalar("SELECT count(*) FROM battle_settlements")==0,
                "Combined progression partially committed");
        f.execute("DROP TRIGGER progression_fail");
    }
    const auto settled=settle();
    require(settled.role && settled.role->revision==3 && settled.role->logical[1]==4 &&
            settled.total_experience==25 && settled.resources.max_hp==70 && settled.resources.revision==before.revision+1,
            "Combined role/XP/resources settlement failed");
    require(settle()==settled,"Exact combined retry changed result");
    auto changed=change;changed.next_role.logical[5]++;
    expect_database_error([&]{repo.settle_battle(1,f.first.id,battle,before,final_resources,true,25,changed);},
                          "Changed stat growth reused settlement ID");
    expect_database_error([&]{repo.settle_battle(1,f.first.id,battle,before,final_resources,true,25);},
                          "Role-bearing settlement replayed without role payload");
    auto later=settled.resources;later.hp--;
    later=repo.commit_resources(1,f.first.id,settled.resources,later);
    require(settle()==settled && repo.load_resources(1,f.first.id)==later && repo.load_role(1,f.first.id)==settled.role,
            "Old combined replay overwrote newer character state");
    f.require_unrelated_unchanged();
}

void test_experience_read_corruption() {
    using namespace god2;
    Fixture f;
    auto repo=f.repository();
    const auto id=std::to_string(f.first.id);
    f.execute("INSERT INTO character_experience VALUES("+id+",0,'CUSTOM-0012')");
    require(repo.load_experience(1,f.first.id)==CharacterExperience{0,"CUSTOM-0012"},"Persisted zero confused with absent XP");
    for(const auto* mutation:{"total=-1","total=1.5","total='bad'","total=X'01'",
                             "total=9223372036854775808","design_id='NATIVE_VERIFIED'"}) {
        f.execute("PRAGMA ignore_check_constraints=ON");
        f.execute(std::string("UPDATE character_experience SET ")+mutation);
        expect_database_error([&]{repo.load_experience(1,f.first.id);},"Corrupt XP or false provenance loaded");
        f.execute("UPDATE character_experience SET total=0,design_id='CUSTOM-0012'");
        f.execute("PRAGMA ignore_check_constraints=OFF");
    }
    require(f.scalar("SELECT count(*) FROM character_resources")==0 &&
            f.scalar("SELECT count(*) FROM battle_settlements")==0,"XP reads created resources or settlement");
    f.require_unrelated_unchanged();
}

void test_failure_atomicity() {
    using namespace god2;
    Fixture f;
    auto repository = f.repository();
    const auto initial = repository.commit_position(1, f.first.id, {}, 1, 2, 3, 4);
    f.execute("CREATE TABLE position_commit_probe(account_id INTEGER REFERENCES accounts(id) "
              "DEFERRABLE INITIALLY DEFERRED)");
    // Exercise both first persistence and an update, including errors after SQLite wrote the row.
    for (const bool update : {false, true}) {
        const auto id = update ? f.first.id : f.second.id;
        const std::optional<RecoveredPosition> expected = update ? std::optional{initial} : std::nullopt;
        const std::string event = update ? "UPDATE" : "INSERT";
        const auto attempt = [&] { repository.commit_position(1, id, expected, 10, 20, 30, 40); };
        const auto unchanged = [&] {
            require(repository.load_position(1, f.first.id) == initial &&
                    !repository.load_position(1, f.second.id) &&
                    f.scalar("SELECT count(*) FROM position_commit_probe") == 0 &&
                    sqlite3_get_autocommit(f.db.get()) != 0, "Failed write left partial changes or transaction");
            f.require_unrelated_unchanged();
        };
        for (const auto* effect : {
                "SELECT RAISE(FAIL,'injected private write failure');",
                "DELETE FROM recovered_positions WHERE character_id=NEW.character_id;",
                "UPDATE recovered_positions SET x=31 WHERE character_id=NEW.character_id;",
                "UPDATE recovered_characters SET account_id=2,slot=1 WHERE id=NEW.character_id;",
                "INSERT INTO position_commit_probe VALUES(999999);"}) {
            f.execute("CREATE TRIGGER position_failure AFTER " + event + " ON recovered_positions BEGIN "
                      "UPDATE accounts SET password_hash='changed' WHERE id=1; " + effect + " END");
            expect_database_error(attempt, "Injected write/readback/commit failure returned success");
            unchanged();
            f.execute("DROP TRIGGER position_failure");
        }
        f.execute("CREATE TRIGGER position_ignore BEFORE " + event + " ON recovered_positions BEGIN "
                  "SELECT RAISE(IGNORE); END");
        expect_database_error(attempt, "Ignored write returned success");
        unchanged();
        f.execute("DROP TRIGGER position_ignore");
        f.execute("PRAGMA query_only=ON");
        expect_database_error(attempt, "Read-only database returned successful write");
        unchanged();
        f.execute("PRAGMA query_only=OFF");
    }
    require(repository.commit_position(1, f.first.id, initial, 10, 20, 30, 40).revision == 2 &&
            repository.commit_position(1, f.second.id, {}, 10, 20, 30, 40).revision == 1,
            "Failure consumed a revision or prevented retry");
    f.require_unrelated_unchanged();
}
}

void test_recovered_position_repository() {
    for(const bool with_progression:{false,true}) {
        using namespace god2;
        Fixture f;auto repo=f.repository();
        auto resources=repo.commit_resources(1,f.first.id,{}, {100,120,50,80,0,"CUSTOM-0012"});
        require(!repo.load_pending_checkpoint(1,f.first.id),"No battle falsely reported pending");
        expect_database_error([&]{repo.load_pending_checkpoint(2,f.first.id);},"Foreign pending lookup accepted");
        const auto id=repo.reserve_battle(1,f.first.id,resources);
        expect_database_error([&]{repo.load_pending_checkpoint(1,f.first.id);},"Missing checkpoint treated as no pending battle");
        const std::array<BattleActor,2> actors{{
            {0,f.first.id,100,120,50,80,31,40,8,10}, {14,0,150,150,0,0,20,25,13,6}}};
        Battle battle(id,actors,123);
        require(!repo.load_checkpoint(1,f.first.id,id),"Migration seeded a checkpoint");
        const std::string policy="CUSTOM-0012/diagnostic-v1";
        auto first=repo.commit_checkpoint(1,f.first.id,{},resources,battle.checkpoint(),resources,policy);
        resources=*repo.load_resources(1,f.first.id);
        require(first.resource_revision==resources.revision && first.checkpoint==battle.checkpoint(),"Checkpoint seed mismatch");
        require(f.repository().load_checkpoint(1,f.first.id,id)==first,"New repository lost checkpoint");
        require(repo.load_pending_checkpoint(1,f.first.id)==first,"Owned pending lookup lost checkpoint");
        f.execute("INSERT INTO battle_reservations(character_id,resource_revision,design_id) VALUES("+
            std::to_string(f.first.id)+",999,'CUSTOM-0012')");
        expect_database_error([&]{repo.load_pending_checkpoint(1,f.first.id);},"Multiple pending reservations silently selected");
        f.execute("DELETE FROM battle_reservations WHERE resource_revision=999");
        f.execute("UPDATE character_resources SET mp=49 WHERE character_id="+std::to_string(f.first.id));
        expect_database_error([&]{repo.load_pending_checkpoint(1,f.first.id);},"Divergent pending resources accepted");
        f.execute("UPDATE character_resources SET mp=50 WHERE character_id="+std::to_string(f.first.id));
        f.execute("UPDATE character_resources SET revision=revision+1 WHERE character_id="+std::to_string(f.first.id));
        expect_database_error([&]{repo.load_pending_checkpoint(1,f.first.id);},"Stale pending resource revision accepted");
        f.execute("UPDATE character_resources SET revision=revision-1 WHERE character_id="+std::to_string(f.first.id));
        expect_database_error([&]{repo.load_checkpoint(2,f.first.id,id);},"Foreign checkpoint read");
        expect_database_error([&]{repo.load_checkpoint(1,f.second.id,id);},"Other character read checkpoint");
        battle.act(f.first.id,1,{0,{14},true,150,100,8,0,150},
            [](const auto& input){return CombatRuleResult{10,input.mp_cost,false};},
            [](const auto&,const auto&){return std::vector<std::uint8_t>{1};});
        auto next=resources;next.mp=42;
        auto wrong=next;wrong.hp=99;
        expect_database_error([&]{repo.commit_checkpoint(1,f.first.id,first,resources,battle.checkpoint(),wrong,policy);},
                              "Mismatched resources accepted");
        f.execute("CREATE TRIGGER checkpoint_fail BEFORE INSERT ON battle_checkpoints BEGIN SELECT RAISE(ABORT,'injected'); END");
        expect_database_error([&]{repo.commit_checkpoint(1,f.first.id,first,resources,battle.checkpoint(),next,policy);},
                              "Failed checkpoint write accepted");
        require(repo.load_resources(1,f.first.id)==resources && repo.load_checkpoint(1,f.first.id,id)==first,
                "Failed checkpoint left partial MP debit");
        f.execute("DROP TRIGGER checkpoint_fail");
        f.execute("CREATE TRIGGER checkpoint_corrupt AFTER UPDATE ON battle_checkpoints BEGIN UPDATE battle_checkpoints SET document='{}' WHERE battle_id=NEW.battle_id; END");
        expect_database_error([&]{repo.commit_checkpoint(1,f.first.id,first,resources,battle.checkpoint(),next,policy);},
                              "Corrupt checkpoint readback accepted");
        require(repo.load_resources(1,f.first.id)==resources && repo.load_checkpoint(1,f.first.id,id)==first,
                "Corrupt checkpoint failed to roll back");
        f.execute("DROP TRIGGER checkpoint_corrupt");
        const auto second=repo.commit_checkpoint(1,f.first.id,first,resources,battle.checkpoint(),next,policy);
        require(second.resource_revision==resources.revision+1,"Checkpoint revision did not advance exactly once");
        require(repo.load_resources(1,f.first.id)->mp==42 &&
                Battle::restore(repo.load_checkpoint(1,f.first.id,id)->checkpoint).checkpoint()==battle.checkpoint(),
                "Checkpoint continuation or MP lost");
        expect_database_error([&]{repo.commit_checkpoint(1,f.first.id,first,resources,battle.checkpoint(),next,policy);},
                              "Stale checkpoint update accepted");
        resources=*repo.load_resources(1,f.first.id);
        expect_database_error([&]{repo.commit_checkpoint(1,f.first.id,second,resources,battle.checkpoint(),next,policy);},
                              "Duplicate battle revision committed");
        require(f.scalar("SELECT count(*) FROM battle_checkpoints")==1 &&
                f.scalar("SELECT count(*) FROM battle_settlements")==0,"Checkpoint created settlement or duplicate");
        battle.act(f.first.id,battle.inspect().revision,{0,{14},true,1000,100,0,0,150},
            [](const auto& input){return CombatRuleResult{1000,input.mp_cost,false};},
            [](const auto&,const auto&){return std::vector<std::uint8_t>{1};});
        const auto terminal=battle.checkpoint();
        std::optional<BattleProgressionCommit> growth;
        if(with_progression) {
            RecoveredRoleLevel::Bytes role{};role[0]=0x22;role[1]=2;role[17]=120;role[21]=80;
            growth=BattleProgressionCommit{{},{},{role,0,"CUSTOM-0013"}};
        }
        expect_database_error([&]{repo.settle_battle(1,f.first.id,id,resources,resources,true,25);},
                              "Legacy settlement bypassed active checkpoint");
        expect_database_error([&]{repo.settle_checkpoint(1,f.first.id,second,resources,terminal,resources,false,0,growth);},
                              "Wrong winner passed checkpoint settlement");
        f.execute("CREATE TRIGGER ledger_fail BEFORE INSERT ON battle_settlements BEGIN SELECT RAISE(ABORT,'injected'); END");
        expect_database_error([&]{repo.settle_checkpoint(1,f.first.id,second,resources,terminal,resources,true,25,growth);},
                              "Late ledger failure ignored");
        require(repo.load_checkpoint(1,f.first.id,id)==second && repo.load_resources(1,f.first.id)==resources &&
                !repo.load_experience(1,f.first.id) && !repo.load_role(1,f.first.id),
                "Failed terminal transaction partially wrote checkpoint/resources/XP/role");
        f.execute("DROP TRIGGER ledger_fail");
        const auto finished=repo.settle_checkpoint(1,f.first.id,second,resources,terminal,resources,true,25,growth);
        require(finished.role.has_value()==with_progression && repo.load_role(1,f.first.id)==finished.role,
                "Terminal progression role missing or fabricated");
        if(growth) require(finished.role->logical==growth->next_role.logical && finished.role->revision==1,
                           "Terminal role values or revision differ");
        require(finished.total_experience==25 && repo.load_checkpoint(1,f.first.id,id)->checkpoint==terminal &&
                repo.load_checkpoint(1,f.first.id,id)->resource_revision==finished.resources.revision,
                "Terminal checkpoint not committed with award");
        require(!repo.load_pending_checkpoint(1,f.first.id),"Finished battle offered for resume");
        require(repo.settle_checkpoint(1,f.first.id,second,resources,terminal,resources,true,25,growth)==finished,
                "Exact terminal retry differed");
        expect_database_error([&]{repo.settle_checkpoint(1,f.first.id,second,resources,terminal,resources,true,26,growth);},
                              "Altered terminal retry accepted");
        auto altered_terminal=terminal;altered_terminal.random_state=first.checkpoint.random_state;
        expect_database_error([&]{repo.settle_checkpoint(1,f.first.id,second,resources,altered_terminal,resources,true,25,growth);},
                              "Changed terminal RNG replay accepted");
        if(growth) {
            expect_database_error([&]{repo.settle_checkpoint(1,f.first.id,second,resources,terminal,resources,true,25);},
                                  "Omitted progression accepted on terminal retry");
            auto altered=*growth;altered.next_role.logical[1]=3;
            expect_database_error([&]{repo.settle_checkpoint(1,f.first.id,second,resources,terminal,resources,true,25,altered);},
                                  "Altered terminal level replay accepted");
        }
        require(f.scalar("SELECT count(*) FROM battle_settlements")==1 && repo.load_experience(1,f.first.id)->total==25,
                "Terminal replay awarded twice");
        require(repo.reserve_battle(1,f.first.id,finished.resources)>id,"Finished checkpoint blocked next reservation");
    }
    {
        Fixture f;auto repository=f.repository();
        require(!repository.load_resources(1,f.first.id),"Migration must not invent resource values");
        const god2::CharacterResources seed{100,120,50,80,0,"CUSTOM-0012"};
        auto first=repository.commit_resources(1,f.first.id,{},seed);
        require(first.revision==1 && f.repository().load_resources(1,f.first.id)==first,"Resource insert/readback failed");
        require(f.scalar("SELECT count(*) FROM battle_reservations")==0,"Migration fabricated battles");
        const auto battle_id=repository.reserve_battle(1,f.first.id,first);
        require(battle_id && f.repository().reserve_battle(1,f.first.id,first)==battle_id,
                "Same resource reservation retry allocated a second battle");
        require(repository.load_resources(1,f.first.id)==first,"Reservation changed resources");
        expect_database_error([&]{repository.reserve_battle(2,f.first.id,first);},"Foreign owner reserved battle");
        expect_database_error([&]{repository.reserve_battle(1,f.second.id,first);},"Missing resource row reserved battle");
        auto altered=first;altered.mp=49;
        expect_database_error([&]{repository.reserve_battle(1,f.first.id,altered);},"Different resource snapshot reused reservation");
        expect_database_error([&]{repository.load_resources(2,f.first.id);},"Foreign account read resources");
        expect_database_error([&]{repository.commit_resources(2,f.first.id,first,seed);},"Foreign account wrote resources");
        auto next=seed;next.hp=88;next.mp=42;
        auto second=repository.commit_resources(1,f.first.id,first,next);
        require(second.revision==2 && second.hp==88 && second.mp==42,"Resource exchange not persisted");
        expect_database_error([&]{repository.reserve_battle(1,f.first.id,first);},"Stale reservation snapshot accepted");
        expect_database_error([&]{repository.reserve_battle(1,f.first.id,second);},"Advanced resources admitted overlapping battle");
        require(f.scalar("SELECT count(*) FROM battle_reservations")==1,"Overlap rejection allocated battle");
        second=repository.settle_battle(1,f.first.id,battle_id,second,second,true,0).resources;
        f.execute("CREATE TRIGGER reservation_fail BEFORE INSERT ON battle_reservations BEGIN SELECT RAISE(ABORT,'injected'); END");
        expect_database_error([&]{repository.reserve_battle(1,f.first.id,second);},"Reservation insert failure ignored");
        require(f.scalar("SELECT count(*) FROM battle_reservations")==1 && repository.load_resources(1,f.first.id)==second,
                "Failed reservation changed resources or allocated a battle");
        f.execute("DROP TRIGGER reservation_fail");
        require(repository.reserve_battle(1,f.first.id,second)>battle_id,"New resource version reused previous battle ID");
        expect_database_error([&]{repository.commit_resources(1,f.first.id,first,next);},"Stale resources overwrote new version");
        auto invalid=next;invalid.mp=81;
        expect_database_error([&]{repository.commit_resources(1,f.first.id,second,invalid);},"Out-of-bounds MP stored");
        invalid=next;invalid.design_id="NATIVE_VERIFIED";
        expect_database_error([&]{repository.commit_resources(1,f.first.id,second,invalid);},"Unverified resources relabeled native");
        f.execute("CREATE TRIGGER resource_corrupt AFTER UPDATE ON character_resources BEGIN UPDATE character_resources SET mp=0 WHERE character_id=NEW.character_id; END");
        expect_database_error([&]{repository.commit_resources(1,f.first.id,second,next);},"Trigger corruption passed readback");
        require(repository.load_resources(1,f.first.id)==second,"Failed readback did not roll back");
        f.execute("DROP TRIGGER resource_corrupt");
        require(repository.commit_resources(1,f.first.id,second,next).revision==second.revision+1,"Rollback consumed revision");
        const auto alive=repository.load_resources(1,f.first.id);
        auto dead=*alive;dead.hp=0;
        dead=repository.commit_resources(1,f.first.id,alive,dead);
        expect_database_error([&]{repository.reserve_battle(1,f.first.id,dead);},"Dead character reserved new battle");
        f.require_unrelated_unchanged();
    }
    test_ownership_and_cas();
    test_constraints_corruption_and_overflow();
    test_failure_atomicity();
    test_battle_settlement_atomicity();
    test_experience_read_corruption();
    test_role_resource_transaction();
}
