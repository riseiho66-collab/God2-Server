#include "db/DbTypes.h"
#include "db/MySqlDatabase.h"
#include "db/SqliteDatabase.h"
#include "db/SqliteRecoveredCharacterRepository.h"
#include "db/SqliteSupport.h"
#include "protocol/DiagnosticBattleRevival.h"
#include "protocol/RecoveredCharacterDelete.h"
#include "handlers/RecoveredBattleService.h"
#include "handlers/DiagnosticQuestConversation.h"
#include "scripting/LuaEngine.h"
#include <algorithm>
#include <filesystem>
#include <future>
#include <initializer_list>
#include <limits>
#include <random>
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
template<class F> void expect_generic_error(F&& function, const char* expected) {
    try { function(); } catch (const god2::DatabaseError& error) {
        require(std::string(error.what()) == expected, "Recovered character error exposed database details");
        return;
    }
    throw std::runtime_error("Expected recovered character database error");
}
struct TemporaryDatabase {
    std::filesystem::path directory;
    TemporaryDatabase() {
        std::random_device random;
        for (int attempt = 0; attempt < 100; ++attempt) {
            directory = std::filesystem::temp_directory_path() /
                ("god2-recovered-db-test-" + std::to_string(random()) + "-" + std::to_string(random()));
            if (std::filesystem::create_directory(directory)) return;
        }
        throw std::runtime_error("Unable to create recovered character test directory");
    }
    ~TemporaryDatabase() {
        std::error_code error;
        std::filesystem::remove_all(directory, error);
    }
    std::filesystem::path path() const { return directory / "test.sqlite"; }
};
struct RawDatabase {
    sqlite3* db = nullptr;
    explicit RawDatabase(const std::filesystem::path& path) {
        const auto utf8 = path.u8string();
        if (sqlite3_open_v2(reinterpret_cast<const char*>(utf8.c_str()), &db,
                            SQLITE_OPEN_READWRITE, nullptr) != SQLITE_OK) {
            sqlite3_close_v2(db);
            throw std::runtime_error("Unable to open test database");
        }
    }
    ~RawDatabase() { sqlite3_close_v2(db); }
    RawDatabase(const RawDatabase&) = delete;
    RawDatabase& operator=(const RawDatabase&) = delete;
    void execute(const std::string& sql) { god2::sqlite_detail::execute(db, sql); }
    std::int64_t scalar(const char* sql) {
        god2::sqlite_detail::Statement statement(db, sql);
        require(statement.row(), "Missing test query result");
        return statement.integer(0);
    }
};
std::array<std::uint8_t, 40> make_profile(std::initializer_list<std::uint8_t> name) {
    require(name.size() >= 1 && name.size() <= 14, "Invalid test name");
    std::array<std::uint8_t, 40> profile{};
    for (std::size_t i = 0; i < profile.size(); ++i)
        profile[i] = static_cast<std::uint8_t>(0x80 + i);
    std::copy(name.begin(), name.end(), profile.begin());
    profile[name.size()] = 0;
    profile[31] = 0xff;
    return profile;
}
void test_town_guide_progress_disk_reopen() {
    using namespace god2;
    TemporaryDatabase temporary;
    std::uint64_t account{},character{},other{};
    StoredTownGuideProgress saved{};
    {
        SqliteDatabase db(temporary.path());db.initialize();db.migrate();
        account=db.accounts().create("guide-owner","test-hash").id;
        other=db.accounts().create("guide-other","test-hash").id;
        auto& repo=static_cast<SqliteRecoveredCharacterRepository&>(db.recovered_characters());
        character=repo.create(account,make_profile({'G'})).id;
        LuaEngine lua(std::filesystem::path(GOD2_SOURCE_DIR)/"scripts",false);
        require(lua.initialize(),"Guide Lua initialization failed");
        DiagnosticQuestConversation first;
        require(first.bind(1,account,character) && first.spawn(1,account,character),"Guide conversation bind failed");
        const auto offer=lua.town_guide({0,1606});
        require(first.open_town_npc(1,account,character,1606,{2,4,110,70,0}),"Guide opening failed");
        require(first.cancel(1,account,character),"Guide cancellation failed");
        require(!repo.load_town_guide_progress(account,character),"Missing progress became accepted quest");
        expect_database_error([&]{repo.commit_town_guide_progress(account,character,{},2);},"Skipped first stage");
        expect_database_error([&]{repo.commit_town_guide_progress(other,character,{},1);},"Wrong owner wrote progress");
        require(first.open_town_npc(1,account,character,1606,{2,4,110,70,0}),"Guide reopen failed");
        require(!first.consume(1,account,character,{0x1234,2,0x9a,0}),"Cancelled generation accepted");
        require(first.consume_after_commit(1,account,character,{0x1235,2,0x9a,0},[&] {
            saved=repo.commit_town_guide_progress(account,character,{},offer.confirmed_stage);
        }),"Confirmed Lua proposal did not persist");
        require(saved==StoredTownGuideProgress{1,1,1},"First stage mismatch");
        expect_database_error([&]{repo.commit_town_guide_progress(account,character,{},1);},"Duplicate acceptance succeeded");
        expect_database_error([&]{repo.load_town_guide_progress(other,character);},"Wrong owner read progress");
        expect_database_error([&]{repo.commit_town_guide_progress(account,character,saved,1);},"Duplicate stage succeeded");
        expect_database_error([&]{repo.commit_town_guide_progress(account,character,saved,3);},"Unpaid completion succeeded");
        RawDatabase raw(temporary.path());
        DiagnosticQuestConversation second;
        require(second.bind(2,account,character) && second.spawn(2,account,character),"Second guide binding failed");
        const auto visit=lua.town_guide({saved.stage,1607});
        require(second.open_town_npc(2,account,character,1607,{2,4,110,70,0}),"Second guide opening failed");
        raw.execute("CREATE TRIGGER fail_guide AFTER UPDATE ON diagnostic_town_guide_progress BEGIN SELECT RAISE(ABORT,'injected'); END");
        expect_database_error([&]{second.consume_after_commit(2,account,character,{0x1234,2,0x9a,0},[&] {
            repo.commit_town_guide_progress(account,character,saved,visit.confirmed_stage);
        });},"Failed write did not rollback");
        require(repo.load_town_guide_progress(account,character)==std::optional{saved},"Failed write changed progress");
        raw.execute("DROP TRIGGER fail_guide");
        SqliteDatabase peer(temporary.path());peer.initialize();peer.migrate();
        auto& peer_repo=static_cast<SqliteRecoveredCharacterRepository&>(peer.recovered_characters());
        const auto stale=peer_repo.load_town_guide_progress(account,character);
        require(second.consume_after_commit(2,account,character,{0x1234,2,0x9a,0},[&] {
            saved=repo.commit_town_guide_progress(account,character,saved,visit.confirmed_stage);
        }),"Rolled-back confirmation was not retryable");
        require(!second.consume(2,account,character,{0x1234,2,0x9a,0}),"Committed confirmation replayed");
        require(saved==StoredTownGuideProgress{2,2,2},"Second stage mismatch");
        expect_database_error([&]{peer_repo.commit_town_guide_progress(account,character,stale,2);},"Stale peer overwrote progress");
        require(!repo.load_quest_journal(account,character),"Town progress changed unrelated display journal");
        require(raw.scalar("SELECT count(*) FROM accounts")==2,"Progress changed accounts");
        require(raw.scalar("SELECT count(*) FROM diagnostic_town_guide_progress")==1,"Unexpected progress rows");
    }
    {
        SqliteDatabase db(temporary.path());db.initialize();db.migrate();
        auto& repo=static_cast<SqliteRecoveredCharacterRepository&>(db.recovered_characters());
        require(repo.load_town_guide_progress(account,character)==std::optional{saved},"Town progress lost across reopen");
        for(const auto next:{0U,1U,2U,3U,0xffffffffU})
            expect_database_error([&]{repo.commit_town_guide_progress(account,character,saved,next);},"Terminal guard failed");
        RawDatabase raw(temporary.path());
        expect_database_error([&]{raw.execute("UPDATE diagnostic_town_guide_progress SET stage=3");},"Schema accepted unpaid completion");
        expect_database_error([&]{raw.execute("UPDATE diagnostic_town_guide_progress SET journal_description=1");},"Schema accepted inconsistent journal");
        raw.execute("UPDATE diagnostic_town_guide_progress SET source_sha256='"+std::string(64,'a')+"'");
        expect_database_error([&]{repo.load_town_guide_progress(account,character);},"Wrong source provenance accepted");
        raw.execute("UPDATE diagnostic_town_guide_progress SET source_sha256='"+
            std::string(SqliteRecoveredCharacterRepository::town_guide_source_sha256)+
            "',stage=1,journal_description=1,revision=9223372036854775807");
        const auto exhausted=repo.load_town_guide_progress(account,character);
        expect_database_error([&]{repo.commit_town_guide_progress(account,character,exhausted,2);},"Revision overflow accepted");
    }
}

void test_town_guide_atomic_reward() {
    using namespace god2;
    TemporaryDatabase temporary;
    std::uint64_t account{},character{};
    const StoredInventorySlot empty{0,0,1,SqliteRecoveredCharacterRepository::town_reward_item_source_sha256};
    {
        SqliteDatabase db(temporary.path());db.initialize();db.migrate();
        account=db.accounts().create("reward-owner","test-hash").id;
        const auto other=db.accounts().create("reward-other","test-hash").id;
        auto& repo=static_cast<SqliteRecoveredCharacterRepository&>(db.recovered_characters());
        character=repo.create(account,make_profile({'R'})).id;
        const auto first=repo.commit_town_guide_progress(account,character,{},1);
        const auto ready=repo.commit_town_guide_progress(account,character,first,2);
        expect_database_error([&]{repo.complete_town_guide(account,character,ready,0,empty);},"Missing slot treated as empty");
        RawDatabase raw(temporary.path());
        raw.execute("CREATE TRIGGER fail_provision AFTER INSERT ON diagnostic_inventory_slots "
            "BEGIN SELECT RAISE(ABORT,'slot provision'); END");
        expect_database_error([&]{repo.provision_town_reward_slot(account,character);},"Failed slot provision committed");
        require(!repo.load_inventory_slot(account,character,0),"Failed provision retained slot");
        require(repo.load_town_guide_progress(account,character)==std::optional{ready},
            "Failed provision changed guide progress");
        raw.execute("DROP TRIGGER fail_provision");
        expect_database_error([&]{repo.provision_town_reward_slot(other,character);},"Foreign owner provisioned town slot");
        require(repo.provision_town_reward_slot(account,character),"Fresh town slot not provisioned");
        require(repo.load_inventory_slot(account,character,0)==std::optional{empty},"Provisioned empty slot mismatch");
        require(!repo.provision_town_reward_slot(account,character),"Town slot provision was not idempotent");
        expect_database_error([&]{repo.complete_town_guide(other,character,ready,0,empty);},"Foreign owner claimed reward");
        expect_database_error([&]{repo.complete_town_guide(account,character,first,0,empty);},"Early reward accepted");
        expect_database_error([&]{repo.complete_town_guide(account,character,ready,50,empty);},"Invalid reward slot accepted");
        auto bad=empty;bad.revision=2;
        expect_database_error([&]{repo.complete_town_guide(account,character,ready,0,bad);},"Stale slot accepted");
        bad=empty;bad.source_sha256=std::string(64,'a');
        expect_database_error([&]{repo.complete_town_guide(account,character,ready,0,bad);},"Wrong item source accepted");
        bad=empty;bad.item_id=5569;bad.count=1;
        expect_database_error([&]{repo.complete_town_guide(account,character,ready,0,bad);},"Occupied slot accepted");
        bad=empty;bad.revision=std::numeric_limits<std::int64_t>::max();
        expect_database_error([&]{repo.complete_town_guide(account,character,ready,0,bad);},"Slot revision overflow accepted");
        for(const auto* trigger:{
            "AFTER UPDATE ON diagnostic_town_guide_progress BEGIN SELECT RAISE(ABORT,'stage'); END",
            "AFTER UPDATE ON diagnostic_inventory_slots BEGIN SELECT RAISE(ABORT,'inventory'); END",
            "AFTER INSERT ON diagnostic_town_guide_reward BEGIN SELECT RAISE(ABORT,'receipt'); END",
            "AFTER INSERT ON diagnostic_town_guide_reward BEGIN UPDATE diagnostic_inventory_slots SET count=2 WHERE character_id=NEW.character_id AND slot=NEW.slot; END"}) {
            raw.execute(std::string("CREATE TRIGGER fail_reward ")+trigger);
            expect_database_error([&]{repo.complete_town_guide(account,character,ready,0,empty);},"Reward failure ignored");
            require(repo.load_town_guide_progress(account,character)==std::optional{ready},"Reward failure changed stage");
            require(repo.load_inventory_slot(account,character,0)==std::optional{empty},"Reward failure changed inventory");
            require(raw.scalar("SELECT count(*) FROM diagnostic_town_guide_reward")==0,"Reward failure retained receipt");
            // A second connection must not observe a partial committed grant.
            SqliteDatabase reader(temporary.path());reader.initialize();reader.migrate();
            auto& observer=static_cast<SqliteRecoveredCharacterRepository&>(reader.recovered_characters());
            require(observer.load_town_guide_progress(account,character)==std::optional{ready},"Partial reward visible externally");
            require(observer.load_inventory_slot(account,character,0)==std::optional{empty},"Partial inventory visible externally");
            raw.execute("DROP TRIGGER fail_reward");
        }
        SqliteDatabase peer(temporary.path());peer.initialize();peer.migrate();
        auto& peer_repo=static_cast<SqliteRecoveredCharacterRepository&>(peer.recovered_characters());
        const auto stale=peer_repo.load_town_guide_progress(account,character);
        const auto result=repo.complete_town_guide(account,character,ready,0,empty);
        require(result.progress==StoredTownGuideProgress{3,0,3},"Reward completion mismatch");
        require(result.slot==StoredInventorySlot{5569,1,2,empty.source_sha256},"Reward item mismatch");
        require(!repo.provision_town_reward_slot(account,character) &&
            repo.load_inventory_slot(account,character,0)==std::optional{result.slot},
            "Town slot provision overwrote completed reward");
        expect_database_error([&]{peer_repo.complete_town_guide(account,character,*stale,0,empty);},"Stale peer duplicated reward");
        expect_database_error([&]{repo.complete_town_guide(account,character,ready,0,empty);},"Reward replay accepted");
        require(raw.scalar("SELECT count(*) FROM diagnostic_town_guide_reward")==1,"Duplicate reward receipt");
        require(raw.scalar("SELECT count(*) FROM accounts")==2,"Reward changed accounts");
        require(!repo.load_resources(account,character),"Reward created resources");
    }
    {
        SqliteDatabase db(temporary.path());db.initialize();db.migrate();
        auto& repo=static_cast<SqliteRecoveredCharacterRepository&>(db.recovered_characters());
        require(repo.load_town_guide_progress(account,character)==std::optional{StoredTownGuideProgress{3,0,3}},"Completion lost on reopen");
        require(repo.load_inventory_slot(account,character,0)==std::optional{StoredInventorySlot{5569,1,2,empty.source_sha256}},"Reward lost on reopen");
        RawDatabase raw(temporary.path());
        raw.execute("UPDATE diagnostic_town_guide_reward SET source_sha256='"+std::string(64,'a')+"'");
        expect_database_error([&]{repo.load_town_guide_progress(account,character);},"Corrupt reward provenance accepted");
        raw.execute("DELETE FROM diagnostic_town_guide_reward");
        expect_database_error([&]{repo.load_town_guide_progress(account,character);},"Unpaid completion accepted");
    }
}

void test_town_guide_reward_migration() {
    using namespace god2;
    TemporaryDatabase temporary;
    std::uint64_t account{},character{};
    auto migrations=default_sqlite_migrations();
    migrations.erase(std::remove_if(migrations.begin(),migrations.end(),
        [](const auto& migration){return migration.version>16;}),migrations.end());
    {
        SqliteDatabase db(temporary.path(),migrations);db.initialize();db.migrate();
        account=db.accounts().create("migration-owner","unchanged-hash").id;
        RawDatabase raw(temporary.path());
        // This fixture deliberately stops at schema16. The current repository
        // writes name_codepage (migration19), so seed through the old schema.
        const auto profile=make_profile({'M'});
        sqlite_detail::Statement old_insert(raw.db,
            "INSERT INTO recovered_characters(account_id,slot,profile,name_bytes) VALUES(?,0,?,?)");
        old_insert.bind_id(1,account);
        old_insert.bind_blob(2,profile);
        old_insert.bind_blob(3,std::span<const std::uint8_t>(profile.data(),1));
        old_insert.done();
        character=static_cast<std::uint64_t>(sqlite3_last_insert_rowid(raw.db));
        raw.execute("INSERT INTO diagnostic_town_guide_progress VALUES("+std::to_string(character)+
            ",2,2,7,'"+SqliteRecoveredCharacterRepository::town_guide_source_sha256+"','CUSTOM-0021')");
    }
    {
        SqliteDatabase db(temporary.path());db.initialize();db.migrate();db.migrate();
        auto& repo=static_cast<SqliteRecoveredCharacterRepository&>(db.recovered_characters());
        require(repo.load_town_guide_progress(account,character)==std::optional{StoredTownGuideProgress{2,2,7}},"Reward migration changed saved progress");
        require(repo.list_for_account(account).size()==1 &&
                repo.list_for_account(account).front().name_codepage==950,
                "Legacy character name encoding migration did not preserve the owner");
        RawDatabase raw(temporary.path());
        require(raw.scalar("SELECT count(*) FROM diagnostic_town_guide_reward")==0,"Migration granted rewards");
        require(raw.scalar("SELECT count(*) FROM diagnostic_inventory_slots")==0,"Migration seeded inventory");
        require(raw.scalar("SELECT count(*) FROM accounts")==1,"Migration changed account count");
        require(raw.scalar("SELECT count(*) FROM pragma_foreign_key_check")==0,"Migration damaged foreign keys");
    }
}

void test_journal_disk_reopen() {
    using namespace god2;
    TemporaryDatabase temporary;
    std::uint64_t account{},character{},other{};
    StoredQuestJournal saved{};
    const std::array<std::uint16_t,2> counts{2,7};
    {
        SqliteDatabase db(temporary.path());db.initialize();db.migrate();
        account=db.accounts().create("journal-owner","test-hash").id;
        other=db.accounts().create("journal-other","test-hash").id;
        auto& repo=static_cast<SqliteRecoveredCharacterRepository&>(db.recovered_characters());
        character=repo.create(account,make_profile({'J'})).id;
        require(!repo.load_quest_journal(account,character),"Missing journal became accepted quest");
        saved.source_sha256=std::string(64,'a');saved.slots[0]=1;saved.slots[14]=0x70002;
        saved=repo.commit_quest_journal(account,character,{},saved,counts);
        require(saved.revision==1,"Initial journal revision incorrect");
        expect_database_error([&]{repo.load_quest_journal(other,character);},"Journal owner leaked");
        expect_database_error([&]{repo.commit_quest_journal(other,character,saved,saved,counts);},"Wrong owner wrote journal");
        expect_database_error([&]{repo.commit_quest_journal(account,character,{},saved,counts);},"Stale journal overwrote save");
        auto invalid=saved;invalid.slots[7]=3;
        expect_database_error([&]{repo.commit_quest_journal(account,character,saved,invalid,counts);},"Invalid reference saved");
        invalid=saved;invalid.source_sha256=std::string(64,'b');
        expect_database_error([&]{repo.commit_quest_journal(account,character,saved,invalid,counts);},"Catalog silently replaced");
        RawDatabase raw(temporary.path());
        raw.execute("CREATE TRIGGER fail_journal AFTER UPDATE ON diagnostic_quest_journal BEGIN SELECT RAISE(ABORT,'injected'); END");
        auto next=saved;next.slots[0]=0x20001;
        DiagnosticQuestConversation conversation;
        require(conversation.bind(1,account,character) && conversation.open(1,account,character),"Journal conversation bind failed");
        const RecoveredQuestAction::Request request{0x1234,2,0x9a,0};
        unsigned commits=0;
        auto commit=[&]{++commits;next=repo.commit_quest_journal(account,character,saved,next,counts);};
        require(!conversation.consume_after_commit(1,other,character,request,commit) && commits==0,
                "Wrong owner reached journal transaction");
        expect_database_error([&]{conversation.consume_after_commit(1,account,character,request,commit);},"Failed journal write succeeded");
        require(repo.load_quest_journal(account,character)==saved,"Journal failure changed snapshot");
        raw.execute("DROP TRIGGER fail_journal");
        require(conversation.consume_after_commit(1,account,character,request,commit),"Failed transaction consumed confirmation");
        require(commits==2,"Confirmation retry did not commit exactly once");
        require(!conversation.consume_after_commit(1,account,character,request,commit) && commits==2,
                "Duplicate confirmation repeated journal write");
        saved=next;
        require(saved.revision==2,"Journal revision did not advance");
    }
    {
        SqliteDatabase db(temporary.path());db.initialize();db.migrate();
        auto& repo=static_cast<SqliteRecoveredCharacterRepository&>(db.recovered_characters());
        require(repo.load_quest_journal(account,character)==saved,"Journal disk reopen lost values or provenance");
        require(RecoveredQuestSync::encodeJournalLogical(saved.slots,counts).has_value(),"Saved journal cannot project");
        auto empty=saved;empty.slots.fill(0);
        saved=repo.commit_quest_journal(account,character,saved,empty,counts);
        require(saved.revision==3 && repo.load_quest_journal(account,character)==saved,"Journal clear failed");
    }
}

void test_checkpoint_disk_reopen() {
    using namespace god2;
    TemporaryDatabase temporary;
    std::uint64_t account{},character{},battle_id{};
    StoredBattleCheckpoint saved{};
    CharacterResources resources{};
    {
        SqliteDatabase db(temporary.path());db.initialize();db.migrate();
        account=db.accounts().create("checkpoint-owner","test-hash").id;
        auto& repo=static_cast<SqliteRecoveredCharacterRepository&>(db.recovered_characters());
        character=repo.create(account,make_profile({'S'})).id;
        resources=repo.commit_resources(account,character,{}, {100,120,50,80,0,"CUSTOM-0012"});
        battle_id=repo.reserve_battle(account,character,resources);
        const std::array<BattleActor,2> actors{{
            {0,character,100,120,50,80,31,40,8,10},{14,0,150,150,0,0,20,25,13,6}}};
        Battle battle(battle_id,actors,123);
        saved=repo.commit_checkpoint(account,character,{},resources,battle.checkpoint(),resources,"CUSTOM-0012/diagnostic-v1");
        resources=*repo.load_resources(account,character);
    }
    {
        SqliteDatabase db(temporary.path());db.initialize();db.migrate();
        auto& repo=static_cast<SqliteRecoveredCharacterRepository&>(db.recovered_characters());
        require(repo.load_checkpoint(account,character,battle_id)==saved && repo.load_resources(account,character)==resources,
                "Disk reopen lost checkpoint/resource pair");
        require(repo.load_pending_checkpoint(account,character)==saved,"Reopened character did not find pending battle");
        auto battle=Battle::restore(saved.checkpoint);
        battle.act(character,1,{0,{14},true,150,100,8,0,150},
            [](const auto& input){return CombatRuleResult{10,input.mp_cost,false};},
            [](const auto&,const auto&){return std::vector<std::uint8_t>{1};});
        auto next=resources;next.mp=42;
        saved=repo.commit_checkpoint(account,character,saved,resources,battle.checkpoint(),next,saved.policy_id);
        resources=*repo.load_resources(account,character);
    }
    {
        SqliteDatabase db(temporary.path());db.initialize();db.migrate();
        auto& repo=static_cast<SqliteRecoveredCharacterRepository&>(db.recovered_characters());
        require(repo.load_checkpoint(account,character,battle_id)==saved && repo.load_resources(account,character)==resources &&
                resources.mp==42 && saved.checkpoint.snapshot.actors[14]->hp==140,
                "Second reopen lost resumed exchange");
    }
    auto final_battle=Battle::restore(saved.checkpoint);
    final_battle.act(character,final_battle.inspect().revision,{0,{14},true,1000,100,0,0,150},
        [](const auto& input){return CombatRuleResult{1000,input.mp_cost,false};},
        [](const auto&,const auto&){return std::vector<std::uint8_t>{1};});
    const auto terminal=final_battle.checkpoint();
    BattleSettlement settled{};
    {
        SqliteDatabase first(temporary.path());first.initialize();first.migrate();
        SqliteDatabase second(temporary.path());second.initialize();second.migrate();
        auto& a=static_cast<SqliteRecoveredCharacterRepository&>(first.recovered_characters());
        auto& b=static_cast<SqliteRecoveredCharacterRepository&>(second.recovered_characters());
        std::promise<void> start;auto ready=start.get_future().share();
        auto submit=[&](SqliteRecoveredCharacterRepository& repo) {
            ready.wait();
            return repo.settle_checkpoint(account,character,saved,resources,terminal,resources,true,25);
        };
        auto one=std::async(std::launch::async,[&]{return submit(a);});
        auto two=std::async(std::launch::async,[&]{return submit(b);});
        start.set_value();settled=one.get();
        require(two.get()==settled && settled.total_experience==25 &&
                settled.resources.revision==resources.revision+1,"Concurrent terminal checkpoint duplicated reward or revision");
        require(a.load_checkpoint(account,character,battle_id)==b.load_checkpoint(account,character,battle_id) &&
                a.load_checkpoint(account,character,battle_id)->checkpoint==terminal,
                "Concurrent terminal checkpoint readers disagree");
    }
    {
        SqliteDatabase db(temporary.path());db.initialize();db.migrate();
        auto& repo=static_cast<SqliteRecoveredCharacterRepository&>(db.recovered_characters());
        require(repo.load_checkpoint(account,character,battle_id)->checkpoint==terminal &&
                repo.load_resources(account,character)==settled.resources &&
                repo.load_experience(account,character)->total==25,"Terminal disk reopen lost atomic state");
        require(repo.settle_checkpoint(account,character,saved,resources,terminal,resources,true,25)==settled,
                "Terminal retry after restart differs");
        auto later=settled.resources;later.mp=41;
        later=repo.commit_resources(account,character,settled.resources,later);
        require(repo.settle_checkpoint(account,character,saved,resources,terminal,resources,true,25)==settled &&
                repo.load_resources(account,character)==later,"Historical retry rewrote later resources");
        expect_database_error([&]{repo.settle_checkpoint(account,character,saved,resources,terminal,resources,true,26);},
                              "Changed terminal replay after restart accepted");
        RawDatabase raw(temporary.path());
        require(raw.scalar("SELECT count(*) FROM battle_settlements")==1 &&
                raw.scalar("SELECT total FROM character_experience")==25,"Restart or concurrent retry duplicated ledger/XP");
    }
}
void test_revival_checkpoint_atomicity() {
    using namespace god2;
    TemporaryDatabase temporary;
    std::uint64_t account{},character{};
    StoredBattleCheckpoint dead{},revived{};
    CharacterResources before{},after{};
    {
        SqliteDatabase db(temporary.path());db.initialize();db.migrate();
        account=db.accounts().create("revival-checkpoint-owner","test-hash").id;
        auto& repo=static_cast<SqliteRecoveredCharacterRepository&>(db.recovered_characters());
        character=repo.create(account,make_profile({'V'})).id;
        before=repo.commit_resources(account,character,{}, {100,120,80,80,0,"CUSTOM-0012"});
        const auto id=repo.reserve_battle(account,character,before);
        const std::array<BattleActor,3> actors{{
            {0,character,100,120,80,80,31,40,8,10},
            {1,0,4,120,5,20,31,40,8,10},{14,0,150,150,0,0,20,25,13,6}}};
        Battle battle(id,actors,123);
        auto saved=repo.commit_checkpoint(account,character,{},before,battle.checkpoint(),before,"CUSTOM-0012/diagnostic-v1");
        before=*repo.load_resources(account,character);
        const auto encode=[](const auto&,const auto&){return std::vector<std::uint8_t>{1};};
        battle.act(0,1,{14,{1},false,100,100,0,0,150},
            [](const auto&){return CombatRuleResult{4,0,false};},encode);
        dead=repo.commit_checkpoint(account,character,saved,before,battle.checkpoint(),before,saved.policy_id);
        before=*repo.load_resources(account,character);
        // CUSTOM-0017 arithmetic fixture; storage qualification, not native formula recovery.
        battle.revive(character,2,0,1,[](const auto&){return RevivalResult{1,66};},encode);
        after=before;after.mp=14;
        const auto revived_state=battle.checkpoint();
        auto mismatch=after;mismatch.mp=15;
        expect_database_error([&]{repo.commit_checkpoint(account,character,dead,before,revived_state,mismatch,dead.policy_id);},
                              "Revival resource/checkpoint mismatch accepted");
        LuaEngine lua(std::filesystem::path(GOD2_SOURCE_DIR)/"scripts",false);
        require(lua.initialize(),"Revival transaction Lua initialization failed");
        asio::io_context io;
        auto session=std::make_shared<Session>(asio::ip::tcp::socket(io),io.get_executor(),1,false,
            Session::PacketHandler{},Session::DisconnectHandler{});
        session->account_id=account;session->character_id=character;session->set_state(SessionState::InBattle);
        RecoveredBattleService service([&](auto input){return lua.combat_damage(input);});
        RecoveredBattleService::Policy policy{0,0,0,0,{0,{},false,100,100,0,0,150},{}};
        policy.diagnostic_single_action=true;
        policy.diagnostic_revival=RecoveredBattleService::DiagnosticRevival{
            [&](const auto& input){return lua.revival(input);},diagnostic_revival_reply,false};
        unsigned attempts=0;
        service.bind(*session,Battle::restore(dead.checkpoint),policy,
            [](const auto&,const auto&){return RecoveredWorldFrame::encode(std::array<std::uint8_t,2>{0x30,0});},{},
            [&](const BattleCheckpoint& previous,const BattleCheckpoint& next) {
                require(previous==dead.checkpoint && next==revived_state,"Revival service checkpoint differs from domain transition");
                ++attempts;
                auto resources=before;resources.hp=next.snapshot.actors[0]->hp;resources.mp=next.snapshot.actors[0]->mp;
                auto phase=service.checkpoint_revival(*session);
                phase.battle=next;phase.action_received=true;phase.control_received=false;
                revived=repo.commit_checkpoint(account,character,dead,before,next,resources,dead.policy_id,phase);
            });
        const std::array<std::uint8_t,17> request{0x35,0,3,0,0x2d,2,0,0,0,0,0,0,0,8,3,0,0};
        const auto command=*RecoveredWorldRecords::decode(request);
        {
            RawDatabase raw(temporary.path());
            raw.execute("CREATE TRIGGER fail_revival_checkpoint BEFORE UPDATE ON battle_checkpoints BEGIN SELECT RAISE(ABORT,'test revival failure'); END");
            expect_database_error([&]{repo.commit_checkpoint(account,character,dead,before,revived_state,after,dead.policy_id);},
                                  "Injected revival write failure accepted");
            expect_database_error([&]{service.handle(*session,command);},"Service ignored checkpoint failure");
            require(service.inspect(1)==dead.checkpoint.snapshot && attempts==1,
                    "Failed checkpoint published revived service state");
            raw.execute("DROP TRIGGER fail_revival_checkpoint");
        }
        require(repo.load_resources(account,character)==before && repo.load_pending_checkpoint(account,character)==dead,
                "Failed revival partially committed MP or ally HP");
        const auto reply=service.handle(*session,command);
        require(reply && reply->size()==173 && RecoveredWorldFrame::decode(*reply).has_value() &&
                service.inspect(1)==revived_state.snapshot && attempts==2,
                "Revival service did not publish committed response/state");
        require(!service.handle(*session,command) && attempts==2,
                "Duplicate revival reached durable commit");
        after=*repo.load_resources(account,character);
        require(revived.revival && revived.revival->action_received && !revived.revival->control_received &&
                revived.revival->battle==revived_state && !dead.revival,
                "Revival phase did not commit with resource/checkpoint transaction");
        auto advanced=Battle::restore(revived_state);
        advanced.act(character,3,{0,{14},false,100,100,0,0,150},
            [](const auto&){return CombatRuleResult{1,0,false};},encode);
        expect_database_error([&]{repo.commit_checkpoint(account,character,revived,after,advanced.checkpoint(),after,revived.policy_id);},
                              "Checkpoint update silently discarded revival phase");
        auto wrong_phase=*revived.revival;++wrong_phase.account;
        expect_database_error([&]{repo.commit_checkpoint(account,character,dead,before,revived_state,after,dead.policy_id,wrong_phase);},
                              "Wrong-owner phase accepted");
        expect_database_error([&]{repo.commit_checkpoint(account,character,dead,before,revived_state,after,dead.policy_id);},
                              "Stale revival retry accepted");
        require(repo.load_resources(account,character)==after && repo.load_pending_checkpoint(account,character)==revived,
                "Stale revival changed committed state");
    }
    {
        SqliteDatabase db(temporary.path());db.initialize();db.migrate();
        auto& repo=static_cast<SqliteRecoveredCharacterRepository&>(db.recovered_characters());
        require(repo.load_pending_checkpoint(account,character)==revived && repo.load_resources(account,character)==after,
                "Disk reopen lost revival transaction");
        require(repo.load_pending_checkpoint(account,character)->revival==revived.revival,
                "Disk reopen lost committed revival phase");
        auto battle=Battle::restore(revived.checkpoint);
        require(battle.inspect().actors[1]->hp==1 && battle.inspect().actors[1]->mp==5 &&
                battle.inspect().actors[0]->mp==14 && battle.inspect().revision==3,
                "Disk reopen changed revived actor or caster resources");
        const auto state=battle.checkpoint();
        const auto projection=diagnostic_revival_participants(character,state.snapshot);
        require(projection.size()==375,"Reopened revival bootstrap changed record layout");
        const auto logical=std::span<const std::uint8_t>(projection);
        // Enumerate record boundaries; never search arbitrary resource bytes for opcodes.
        const std::array<std::pair<std::size_t,std::uint8_t>,11> records{{
            {0,0x86},{17,0x1c},{62,0x86},{79,0x86},{96,0x1c},{141,0x86},
            {158,0x86},{175,0x1c},{220,0x86},{237,0x88},{358,0x86}}};
        for(const auto& [offset,opcode]:records)
            require(projection[offset]==opcode,"Reopened revival replayed an effect instead of state");
        const auto check_resource=[&](std::size_t offset,std::uint8_t slot,
                                     RecoveredBattleVitals::Resource resource,
                                     std::uint32_t current,std::uint32_t maximum) {
            const auto record=RecoveredBattleVitals::parse_logical(logical.subspan(offset,17));
            require(record && record->position()==slot && record->resource()==resource &&
                    record->current()==current && record->maximum()==maximum,
                    "Reopened revival bootstrap altered saved resources");
        };
        check_resource(62,0,RecoveredBattleVitals::Resource::Hp,100,120);
        check_resource(79,0,RecoveredBattleVitals::Resource::Mp,14,80);
        check_resource(141,1,RecoveredBattleVitals::Resource::Hp,1,120);
        check_resource(158,1,RecoveredBattleVitals::Resource::Mp,5,20);
        check_resource(220,14,RecoveredBattleVitals::Resource::Hp,150,150);
        const auto bulk=RecoveredBattleVitalsBatch::parse_logical(logical.subspan(237,121));
        require(bulk && bulk->at(0)->hp==100 && bulk->at(0)->mp==14 &&
                bulk->at(1)->hp==1 && bulk->at(1)->mp==5,
                "Reopened revival bulk disagrees with individual resources");
        require(projection[358]==0x86 && projection[359]==5 && projection[362]==0,
                "Reopened revival grant differs from caster slot");
        require(RecoveredWorldFrame::decode(RecoveredWorldFrame::encode(projection))==projection,
                "Reopened revival frame roundtrip failed");
        require(battle.checkpoint()==state && repo.load_resources(account,character)==after &&
                repo.load_pending_checkpoint(account,character)==revived,
                "Projection replay mutated battle or durable resources");
        bool rejected=false;
        try {
            battle.revive(character,3,0,1,[](const auto&){return RevivalResult{1,66};},
                [](const auto&,const auto&){return std::vector<std::uint8_t>{1};});
        } catch(const std::exception&) { rejected=true; }
        require(rejected && battle.checkpoint()==state,"Reopened revival replay consumed resources");
        const auto pending=revived;
        asio::io_context io;
        auto session=std::make_shared<Session>(asio::ip::tcp::socket(io),io.get_executor(),2,false,
            Session::PacketHandler{},Session::DisconnectHandler{});
        session->account_id=account;session->character_id=character;session->set_state(SessionState::InBattle);
        RecoveredBattleService restored([](const auto&)->CombatRuleResult {throw std::runtime_error("Unexpected action in phase test");});
        RecoveredBattleService::Policy policy{0,0,0,0,{0,{},false,100,100,0,0,150},{}};
        policy.diagnostic_single_action=true;
        policy.diagnostic_revival=RecoveredBattleService::DiagnosticRevival{
            [](const auto&){return RevivalResult{1,66};},diagnostic_revival_reply,false};
        restored.bind(*session,Battle::restore(pending.checkpoint),policy,
            [](const auto&,const auto&){return RecoveredWorldFrame::encode(std::array<std::uint8_t,2>{0x30,0});},{},
            [](const auto&,const auto&){throw std::runtime_error("Unexpected action commit in phase test");});
        restored.restore_revival_phase(*session,*pending.revival);
        unsigned phase_attempts=0;
        restored.set_revival_phase_commit(*session,[&](const auto& previous,const auto& next) {
            require(revived.revival && previous==*revived.revival,"Service phase differs from durable phase");
            ++phase_attempts;
            revived=repo.commit_revival_phase(account,character,revived,after,next);
        });
        const std::array<std::uint8_t,17> receipt{0x35,0,0x0b,0,0,1};
        const auto receipt_records=*RecoveredWorldRecords::decode(receipt);
        auto ready=*pending.revival;ready.control_received=true;
        auto skipped=*pending.revival;skipped.action_received=false;
        expect_database_error([&]{repo.commit_revival_phase(account,character,pending,after,skipped);},
                              "Revival rearm skipped pending receipt");
        auto wrong=ready;++wrong.battle.snapshot.revision;
        expect_database_error([&]{repo.commit_revival_phase(account,character,pending,after,wrong);},
                              "Phase-only update changed battle revision");
        {
            RawDatabase failure(temporary.path());
            failure.execute("CREATE TRIGGER fail_revival_phase BEFORE UPDATE OF revival_document ON battle_checkpoints BEGIN SELECT RAISE(ABORT,'test phase failure'); END");
            expect_database_error([&]{repo.commit_revival_phase(account,character,pending,after,ready);},
                                  "Failed receipt phase write accepted");
            expect_database_error([&]{restored.handle(*session,receipt_records);},
                                  "Service accepted receipt before durable phase commit");
            require(restored.checkpoint_revival(*session)==*pending.revival && phase_attempts==1,
                    "Failed receipt phase advanced service memory");
            failure.execute("DROP TRIGGER fail_revival_phase");
        }
        require(repo.load_pending_checkpoint(account,character)==pending && repo.load_resources(account,character)==after,
                "Failed phase write changed checkpoint/resources");
        const auto accepted_receipt=restored.handle(*session,receipt_records);
        require(accepted_receipt && accepted_receipt->empty() && phase_attempts==2 &&
                restored.checkpoint_revival(*session)==ready,"Service did not publish committed receipt");
        require(!restored.handle(*session,receipt_records) && phase_attempts==2,"Repeated receipt invoked phase commit");
        expect_database_error([&]{repo.commit_revival_phase(account,character,pending,after,ready);},
                              "Stale receipt phase replay accepted");
        {
            SqliteDatabase reopened(temporary.path());reopened.initialize();reopened.migrate();
            auto& reader=static_cast<SqliteRecoveredCharacterRepository&>(reopened.recovered_characters());
            require(reader.load_pending_checkpoint(account,character)==revived && reader.load_resources(account,character)==after,
                    "Reopened connection lost receipt phase or changed resources");
        }
        auto armed=ready;armed.action_received=false;armed.control_received=false;
        const auto receipt_complete=revived;
        {
            RawDatabase failure(temporary.path());
            failure.execute("CREATE TRIGGER fail_rearm_phase BEFORE UPDATE OF revival_document ON battle_checkpoints BEGIN SELECT RAISE(ABORT,'test rearm failure'); END");
            expect_database_error([&]{restored.rearm_diagnostic(*session,state.snapshot.revision);},
                                  "Service rearmed before durable phase commit");
            require(restored.checkpoint_revival(*session)==ready && phase_attempts==3 &&
                    repo.load_pending_checkpoint(account,character)==receipt_complete,
                    "Failed rearm advanced phase or storage");
            failure.execute("DROP TRIGGER fail_rearm_phase");
        }
        restored.rearm_diagnostic(*session,state.snapshot.revision);
        require(restored.checkpoint_revival(*session)==armed && phase_attempts==4,
                "Service did not publish committed rearm");
        expect_database_error([&]{repo.commit_revival_phase(account,character,receipt_complete,after,armed);},
                              "Stale rearm phase accepted");
        expect_database_error([&]{repo.commit_revival_phase(account,character,revived,after,ready);},
                              "Idle phase fabricated an action receipt");
        require(revived.checkpoint==pending.checkpoint && revived.resource_revision==pending.resource_revision &&
                repo.load_resources(account,character)==after,
                "Receipt/rearm changed battle state or resource version");
        RawDatabase raw(temporary.path());
        require(raw.scalar("SELECT count(*) FROM battle_settlements")==0,"Active revival created settlement");
        battle.act(character,battle.inspect().revision,{0,{14},false,1000,100,0,0,150},
            [](const auto&){return CombatRuleResult{1000,0,false};},
            [](const auto&,const auto&){return std::vector<std::uint8_t>{1};});
        const auto settled=repo.settle_checkpoint(account,character,revived,after,battle.checkpoint(),after,true,25);
        const auto finished=repo.load_checkpoint(account,character,battle.inspect().id);
        require(finished && !finished->revival && finished->checkpoint==battle.checkpoint() &&
                finished->resource_revision==settled.resources.revision,
                "Terminal settlement retained invalid active revival phase");
        require(repo.settle_checkpoint(account,character,revived,after,battle.checkpoint(),after,true,25)==settled,
                "Revival terminal settlement retry changed result");
    }
}
void test_inventory_resource_atomicity() {
    using namespace god2;
    TemporaryDatabase temporary;
    std::uint64_t account{},character{};
    InventoryResourceCommit saved{};
    {
        SqliteDatabase db(temporary.path());db.initialize();db.migrate();
        account=db.accounts().create("supply-owner","test-hash").id;
        const auto other=db.accounts().create("supply-other","test-hash").id;
        auto& repo=static_cast<SqliteRecoveredCharacterRepository&>(db.recovered_characters());
        character=repo.create(account,make_profile({'P'})).id;
        const auto resources=repo.commit_resources(account,character,{}, {52,120,2,80,0,"CUSTOM-0012"});
        const StoredInventorySlot item{3107,1,0,"70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731"};
        require(!repo.load_inventory_slot(account,character,0),"Absent slot fabricated occupancy");
        require(repo.load_saved_supply_slots(account,character).empty(),"Absent slots fabricated supply occupancy");
        expect_database_error([&]{repo.load_saved_supply_slots(other,character);},"Foreign supply listing accepted");
        expect_database_error([&]{repo.load_inventory_slot(other,character,0);},"Foreign slot lookup accepted");
        expect_database_error([&]{repo.load_inventory_slot(account,character,50);},"Slot overflow accepted");
        saved=repo.commit_inventory_resources(account,character,0,{},resources,item,resources);
        require(repo.load_saved_supply_slots(account,character)==
                std::vector<std::pair<std::uint8_t,StoredInventorySlot>>{{0,saved.slot}},
                "Saved supply listing lost slot or item provenance");
        auto consumed=saved.slot;consumed.item_id=0;consumed.count=0;
        auto restored=saved.resources;restored.mp=52;
        RawDatabase raw(temporary.path());
        raw.execute("CREATE TRIGGER fail_supply AFTER UPDATE ON diagnostic_inventory_slots BEGIN SELECT RAISE(ABORT,'injected'); END");
        expect_database_error([&]{repo.commit_inventory_resources(account,character,0,saved.slot,saved.resources,consumed,restored);},"Late inventory failure committed");
        require(repo.load_resources(account,character)==saved.resources && repo.load_inventory_slot(account,character,0)==saved.slot,
                "Late inventory failure leaked resource or item update");
        raw.execute("DROP TRIGGER fail_supply");
        auto invalid=item;invalid.count=128;
        expect_database_error([&]{repo.commit_inventory_resources(account,character,0,saved.slot,saved.resources,invalid,restored);},"Signed count overflow accepted");
        const auto prior=saved;
        saved=repo.commit_inventory_resources(account,character,0,prior.slot,prior.resources,consumed,restored);
        require(saved.slot.count==0 && saved.slot.item_id==0 && saved.slot.revision==2 && saved.resources.mp==52,
                "Atomic consume/resource result incorrect");
        expect_database_error([&]{repo.commit_inventory_resources(account,character,0,prior.slot,prior.resources,consumed,restored);},"Stale consumption replay accepted");
        expect_database_error([&]{repo.commit_inventory_resources(other,character,0,saved.slot,saved.resources,item,saved.resources);},"Foreign resource mutation accepted");
    }
    {
        SqliteDatabase db(temporary.path());db.initialize();db.migrate();
        auto& repo=static_cast<SqliteRecoveredCharacterRepository&>(db.recovered_characters());
        require(repo.load_resources(account,character)==saved.resources && repo.load_inventory_slot(account,character,0)==saved.slot,
                "Reopen lost consumed slot or resources");
        repo.reserve_battle(account,character,saved.resources);
        expect_database_error([&]{repo.commit_inventory_resources(account,character,0,saved.slot,saved.resources,saved.slot,saved.resources);},
                              "World inventory mutation invalidated pending battle");
    }
}
void test_battle_reservation_reopen_and_contention() {
    using namespace god2;
    TemporaryDatabase temporary;
    std::uint64_t account=0,character=0,first_battle=0;
    CharacterResources saved{};
    {
        SqliteDatabase db(temporary.path());db.initialize();db.migrate();
        account=db.accounts().create("reservation-owner","test-hash").id;
        auto& repository=db.recovered_characters();
        character=repository.create(account,make_profile({'R'})).id;
        saved=repository.commit_resources(account,character,{}, {100,120,50,80,0,"CUSTOM-0012"});
        first_battle=repository.reserve_battle(account,character,saved);
    }
    {
        SqliteDatabase first(temporary.path());first.initialize();first.migrate();
        SqliteDatabase second(temporary.path());second.initialize();second.migrate();
        require(first.recovered_characters().reserve_battle(account,character,saved)==first_battle,
                "Reopening database changed reserved battle identity");
        auto next=saved;next.hp=88;next.mp=42;
        saved=first.recovered_characters().commit_resources(account,character,saved,next);
        expect_database_error([&]{first.recovered_characters().reserve_battle(account,character,saved);},
                              "Advanced resources admitted an overlapping battle");
        expect_database_error([&]{second.recovered_characters().reserve_battle(account,character,saved);},
                              "Independent connection ignored active battle");
        std::promise<void> reject_start;
        auto reject_ready=reject_start.get_future().share();
        auto reject_overlap=[&](SqliteDatabase& db) {
            reject_ready.wait();
            expect_database_error([&]{db.recovered_characters().reserve_battle(account,character,saved);},
                                  "Concurrent overlapping battle accepted");
        };
        auto reject_a=std::async(std::launch::async,[&]{reject_overlap(first);});
        auto reject_b=std::async(std::launch::async,[&]{reject_overlap(second);});
        reject_start.set_value();reject_a.get();reject_b.get();
        saved=first.recovered_characters().settle_battle(account,character,first_battle,saved,saved,true,0).resources;
        std::promise<void> start;
        auto ready=start.get_future().share();
        auto reserve=[&](SqliteDatabase& db) {
            ready.wait();
            return db.recovered_characters().reserve_battle(account,character,saved);
        };
        auto a=std::async(std::launch::async,[&]{return reserve(first);});
        auto b=std::async(std::launch::async,[&]{return reserve(second);});
        start.set_value();
        const auto first_result=a.get(),second_result=b.get();
        require(first_result==second_result && first_result>first_battle,
                "Concurrent same-version requests allocated different battles");
        first_battle=first_result;
        require(first.recovered_characters().load_resources(account,character)==saved &&
                second.recovered_characters().load_resources(account,character)==saved,
                "Reservation race mutated resource snapshot");
        RawDatabase raw(temporary.path());
        require(raw.scalar("SELECT count(*) FROM battle_reservations")==2,
                "Reservation race inserted duplicate rows");
    }
    {
        SqliteDatabase db(temporary.path());db.initialize();db.migrate();
        require(db.recovered_characters().reserve_battle(account,character,saved)==first_battle &&
                db.recovered_characters().load_resources(account,character)==saved,
                "Committed concurrent reservation did not survive close/reopen");
    }
}

void test_settlement_reopen_and_contention() {
    using namespace god2;
    for(const bool with_role:{false,true}) {
    TemporaryDatabase temporary;
    std::uint64_t account=0,character=0,battle=0;
    CharacterResources saved{},next{};
    BattleSettlement committed{};
    std::optional<BattleProgressionCommit> progression;
    {
        SqliteDatabase db(temporary.path());db.initialize();db.migrate();
        account=db.accounts().create("settlement-owner","test-hash").id;
        auto& repo=static_cast<SqliteRecoveredCharacterRepository&>(db.recovered_characters());
        character=repo.create(account,make_profile({'S'})).id;
        require(!repo.load_experience(account,character),"New character acquired fabricated XP row");
        saved=repo.commit_resources(account,character,{}, {100,120,50,80,0,"CUSTOM-0012"});
        if(with_role) {
            CharacterRoleSnapshot initial{};initial.logical.fill(0xa5);
            initial.logical[0]=0x22;initial.logical[1]=1;initial.design_id="CUSTOM-0013";
            for(unsigned i=0;i<4;++i) {
                initial.logical[17+i]=static_cast<std::uint8_t>(120u>>(8*i));
                initial.logical[21+i]=static_cast<std::uint8_t>(80u>>(8*i));
            }
            const auto seed=repo.commit_role_resources(account,character,{},saved,initial,saved);
            saved=seed.resources;
            auto next_role=seed.role;next_role.logical[1]=2;next_role.logical[13]=0;next_role.logical[14]=0;
            progression=BattleProgressionCommit{{},seed.role,next_role};
        }
        battle=repo.reserve_battle(account,character,saved);
        next=saved;next.hp=76;next.mp=26;
    }
    {
        SqliteDatabase first(temporary.path());first.initialize();first.migrate();
        SqliteDatabase second(temporary.path());second.initialize();second.migrate();
        std::promise<void> start;
        auto ready=start.get_future().share();
        const auto settle=[&](SqliteDatabase& db) {
            ready.wait();
            return db.recovered_characters().settle_battle(account,character,battle,saved,next,true,25,progression);
        };
        auto a=std::async(std::launch::async,[&]{return settle(first);});
        auto b=std::async(std::launch::async,[&]{return settle(second);});
        start.set_value();
        committed=a.get();
        require(b.get()==committed && committed.total_experience==25 && committed.resources.revision==saved.revision+1,
                "Concurrent settlement duplicated reward or resource mutation");
        require(committed.role.has_value()==with_role &&
                first.recovered_characters().load_role(account,character)==committed.role &&
                second.recovered_characters().load_role(account,character)==committed.role,
                "Concurrent settlement disagrees on role snapshot");
        if(with_role) require(committed.role->revision==2 && committed.role->logical[1]==2,
                              "Role settlement duplicated or lost level update");
        require(first.recovered_characters().load_experience(account,character)==CharacterExperience{25,"CUSTOM-0012"} &&
                second.recovered_characters().load_experience(account,character)==CharacterExperience{25,"CUSTOM-0012"},
                "Independent connections disagree on committed XP");
    }
    {
        SqliteDatabase db(temporary.path());db.initialize();db.migrate();
        auto& repo=db.recovered_characters();
        require(repo.load_experience(account,character)==CharacterExperience{25,"CUSTOM-0012"},
                "Reopened owner could not load total XP with provenance");
        require(repo.load_resources(account,character)==committed.resources &&
                repo.settle_battle(account,character,battle,saved,next,true,25,progression)==committed &&
                repo.load_role(account,character)==committed.role,
                "Settlement did not survive close/reopen or retry");
        expect_database_error([&]{repo.settle_battle(account,character,battle,saved,next,true,26,progression);},
                              "Reopened settlement accepted different award");
        RawDatabase raw(temporary.path());
        require(raw.scalar("SELECT count(*) FROM battle_settlements")==1 &&
                raw.scalar("SELECT total FROM character_experience")==25,
                "Reopened settlement duplicated ledger");
    }
    }
}

void test_persistence_and_bounds() {
    using namespace god2;
    TemporaryDatabase temporary;
    std::uint64_t first_account = 0, second_account = 0;
    const auto binary = make_profile({0x81, 0xa4, 0xff, 0x27});
    const auto maximum = make_profile({'a','b','c','d','e','f','g','h','i','j','k','l','m',0xfe});
    RecoveredCharacter first, second, other;
    {
        auto old_migrations = default_sqlite_migrations();
        require(old_migrations.size() >= 2 && old_migrations[1].version == 2,
                "Recovered schema must be migration 2");
        old_migrations.resize(1);
        SqliteDatabase old(temporary.path(), old_migrations);
        old.initialize();
        old.migrate();
        first_account = old.accounts().create("existing-first", "existing-hash").id;
        second_account = old.accounts().create("existing-second", "second-hash").id;
        Character legacy;
        legacy.account_id = first_account;
        legacy.name = "existing-character";
        old.characters().create(legacy);
    }
    {
        SqliteDatabase db(temporary.path());
        expect_database_error([&] { db.recovered_characters(); }, "Uninitialized repository access accepted");
        db.initialize();
        expect_database_error([&] { db.recovered_characters(); }, "Unmigrated repository access accepted");
        db.migrate();
        db.migrate();
        require(db.accounts().find_by_id(first_account)->password_hash == "existing-hash",
                "Migration changed an existing account");
        require(db.characters().list_for_account(first_account).size() == 1,
                "Migration changed existing mock characters");
        auto& repository = db.recovered_characters();
        require(repository.list_for_account(first_account).empty(), "Migration synthesized recovered characters");
        first = repository.create(first_account, binary);
        require(first.id > 0 && first.account_id == first_account && first.slot == 0 &&
                first.profile == binary && !first.created_at.empty(), "Binary profile creation failed");
        auto duplicate = binary;
        duplicate[14] ^= 0x7f;
        duplicate[39] ^= 0x7f;
        expect_generic_error([&] { repository.create(first_account, duplicate); },
                             "Unable to create recovered character");
        expect_generic_error([&] { repository.create(second_account, duplicate); },
                             "Unable to create recovered character");
        require(repository.list_for_account(second_account).empty(), "Duplicate created another account's character");
        require(repository.list_for_account(first_account)[0].profile == binary, "Duplicate silently updated profile");
        for (const auto invalid : {std::uint64_t{0}, std::uint64_t{999999}, std::numeric_limits<std::uint64_t>::max()}) {
            expect_database_error([&] { repository.create(invalid, maximum); }, "Invalid account accepted on create");
            expect_database_error([&] { repository.list_for_account(invalid); }, "Invalid account accepted on list");
        }
        auto bad = binary;
        bad[0] = 0;
        expect_database_error([&] { repository.create(first_account, bad); }, "Empty name accepted");
        bad.fill('x');
        bad[15] = 0;
        expect_database_error([&] { repository.create(first_account, bad); }, "15-byte name accepted");
        bad.fill(0xff);
        expect_database_error([&] { repository.create(first_account, bad); }, "Unterminated name accepted");
        second = repository.create(first_account, maximum);
        require(second.slot == 1 && second.profile == maximum, "Second slot or 14-byte raw name failed");
        expect_database_error([&] { repository.create(first_account, make_profile({'z'})); }, "Third slot accepted");
        auto distinct = binary;
        distinct[2] = 0xfe;
        other = repository.create(second_account, distinct);
        require(other.slot == 0 && other.account_id == second_account && other.profile == distinct,
                "Distinct binary name or account allocation failed");
        const auto own = repository.list_for_account(first_account);
        const auto isolated = repository.list_for_account(second_account);
        require(own.size() == 2 && own[0].id == first.id && own[1].id == second.id &&
                isolated.size() == 1 && isolated[0].id == other.id, "Ownership or slot ordering failed");
        require(db.characters().list_for_account(first_account).size() == 1,
                "Recovered create synthesized mock character state");
        SqliteDatabase observer(temporary.path());
        observer.initialize();
        observer.migrate();
        require(observer.recovered_characters().list_for_account(first_account).size() == 2,
                "Create returned before committing");
        RawDatabase raw(temporary.path());
        require(raw.scalar("SELECT count(*) FROM recovered_characters WHERE typeof(profile)='blob' "
                           "AND length(profile)=40 AND typeof(name_bytes)='blob'") == 3,
                "Profiles or names were not stored as blobs");
        require(raw.scalar("SELECT count(*) FROM schema_migrations") ==
                static_cast<std::int64_t>(default_sqlite_migrations().size()), "Migration history is incorrect");
    }
    {
        SqliteDatabase db(temporary.path());
        db.initialize();
        db.migrate();
        const auto own = db.recovered_characters().list_for_account(first_account);
        const auto isolated = db.recovered_characters().list_for_account(second_account);
        require(own.size() == 2 && own[0].id == first.id && own[0].profile == binary &&
                own[0].created_at == first.created_at && own[1].id == second.id &&
                own[1].profile == maximum && own[1].created_at == second.created_at &&
                isolated.size() == 1 && isolated[0].id == other.id && isolated[0].profile == other.profile,
                "Recovered profiles did not persist across reopen");
    }
}
void test_constraints_corruption_and_rollback() {
    using namespace god2;
    TemporaryDatabase temporary;
    SqliteDatabase db(temporary.path());
    db.initialize();
    db.migrate();
    const auto account = db.accounts().create("owner", "original-hash");
    auto& repository = db.recovered_characters();
    const auto original = repository.create(account.id, make_profile({'A'}));
    RawDatabase raw(temporary.path());
    raw.execute("PRAGMA foreign_keys=ON");
    const std::string insert = "INSERT INTO recovered_characters(account_id,slot,profile,name_bytes) VALUES(";
    const std::string profile = "CAST(X'4200' || zeroblob(38) AS BLOB)";
    expect_database_error([&] { raw.execute(insert + "999999,0," + profile + ",X'42')"); },
                          "Schema accepted a missing account");
    const auto owner = std::to_string(account.id);
    expect_database_error([&] { raw.execute("DELETE FROM accounts WHERE id=" + owner); },
                          "Foreign key allowed removal of an owner");
    for (const auto* slot : {"-1", "2", "0.5", "0"})
        expect_database_error([&] { raw.execute(insert + owner + "," + slot + "," + profile + ",X'42')"); },
                              "Schema accepted invalid or duplicate slot");
    const auto row = " WHERE id=" + std::to_string(original.id);
    for (const auto* mutation : {
            "profile=zeroblob(39)", "profile=zeroblob(41)", "profile=printf('%040d',0)",
            "name_bytes=X''", "name_bytes=zeroblob(15)", "name_bytes='A'", "name_bytes=X'42'",
            "name_bytes=X'4100'"})
        expect_database_error([&] { raw.execute(std::string("UPDATE recovered_characters SET ") + mutation + row); },
                              "Schema accepted invalid profile or name data");
    raw.execute("PRAGMA ignore_check_constraints=ON");
    for (const auto* mutation : {
            "profile=X''", "profile=zeroblob(39)", "profile=zeroblob(41)",
            "profile=printf('%040d',0)", "profile=zeroblob(40)",
            "profile=CAST('abcdefghijklmno' || zeroblob(25) AS BLOB)",
            "name_bytes=X''", "name_bytes=zeroblob(15)", "name_bytes='A'", "name_bytes=X'42'",
            "name_bytes=X'4100'", "slot=-1", "slot=2", "slot=256", "slot=0.5"}) {
        raw.execute("BEGIN IMMEDIATE");
        raw.execute(std::string("UPDATE recovered_characters SET ") + mutation + row);
        raw.execute("COMMIT");
        expect_generic_error([&] { repository.list_for_account(account.id); },
                             "Unable to list recovered characters");
        // Restore from the known original without reinterpreting the encoded bytes.
        sqlite_detail::Statement restore(raw.db,
            "UPDATE recovered_characters SET profile=?,name_bytes=?,slot=0 WHERE id=?");
        restore.bind_blob(1, original.profile);
        restore.bind_blob(2, std::span<const std::uint8_t>(original.profile.data(), 1));
        restore.bind_id(3, original.id);
        restore.done();
    }
    raw.execute("PRAGMA ignore_check_constraints=OFF");
    raw.execute("CREATE TRIGGER recovered_rollback AFTER INSERT ON recovered_characters BEGIN "
                "UPDATE accounts SET password_hash='changed' WHERE id=NEW.account_id; "
                "DELETE FROM recovered_characters WHERE id=NEW.id; END");
    expect_generic_error([&] { repository.create(account.id, make_profile({'B'})); },
                         "Unable to create recovered character");
    require(db.accounts().find_by_id(account.id)->password_hash == "original-hash" &&
            repository.list_for_account(account.id).size() == 1, "Failed readback did not roll back transaction");
    raw.execute("DROP TRIGGER recovered_rollback");
    raw.execute("CREATE TRIGGER recovered_error BEFORE INSERT ON recovered_characters BEGIN "
                "SELECT RAISE(ABORT,'private raw character name'); END");
    expect_generic_error([&] { repository.create(account.id, make_profile({'B'})); },
                         "Unable to create recovered character");
    raw.execute("DROP TRIGGER recovered_error");
    raw.execute("CREATE TABLE recovered_commit_probe(account_id INTEGER REFERENCES accounts(id) "
                "DEFERRABLE INITIALLY DEFERRED)");
    raw.execute("CREATE TRIGGER recovered_commit_failure AFTER INSERT ON recovered_characters BEGIN "
                "INSERT INTO recovered_commit_probe VALUES(999999); END");
    expect_generic_error([&] { repository.create(account.id, make_profile({'B'})); },
                         "Unable to create recovered character");
    require(repository.list_for_account(account.id).size() == 1 &&
            raw.scalar("SELECT count(*) FROM recovered_commit_probe") == 0,
            "Failed commit returned success or did not roll back");
    raw.execute("DROP TRIGGER recovered_commit_failure");
    const auto second = repository.create(account.id, make_profile({'a'}));
    require(second.slot == 1, "Failed transactions consumed a slot or raw names were normalized");
    raw.execute("DELETE FROM recovered_characters" + row);
    const auto replacement = repository.create(account.id, make_profile({'C'}));
    const auto listed = repository.list_for_account(account.id);
    require(replacement.slot == 0 && listed.size() == 2 && listed[0].id == replacement.id && listed[1].id == second.id,
            "Allocation did not reuse the first free slot or listing did not use slot order");
}

void test_owned_character_deletion() {
    using namespace god2;
    TemporaryDatabase temporary;
    SqliteDatabase db(temporary.path());db.initialize();db.migrate();
    auto& repo=static_cast<SqliteRecoveredCharacterRepository&>(db.recovered_characters());
    const auto account=db.accounts().create("delete-owner","preserved-hash").id;
    const auto other=db.accounts().create("delete-other","other-hash").id;
    const auto first=repo.create(account,make_profile({'D'}));
    const auto second=repo.create(account,make_profile({'S'}));
    const auto foreign=repo.create(other,make_profile({'F'}));
    repo.commit_position(account,first.id,{},4,3,126,126);
    const auto resources=repo.commit_resources(account,first.id,{}, {100,120,50,80,0,"CUSTOM-0012"});
    const auto battle=repo.reserve_battle(account,first.id,resources);
    const auto settled=repo.settle_battle(account,first.id,battle,resources,resources,true,7);
    const std::array<std::uint8_t,1> name{'D'},wrong{'X'};
    require(!repo.erase_owned(other,first.id,name) && !repo.erase_owned(account,first.id,wrong),
        "Deletion accepted foreign owner or stale name");
    RawDatabase raw(temporary.path());
    raw.execute("CREATE TABLE delete_leaf(character_id INTEGER REFERENCES recovered_characters(id), value TEXT)");
    raw.execute("INSERT INTO delete_leaf VALUES("+std::to_string(first.id)+",'owned'),("+std::to_string(foreign.id)+",'foreign')");
    raw.execute("CREATE TABLE delete_unrelated_legacy(character_id INTEGER, value TEXT)");
    raw.execute("INSERT INTO delete_unrelated_legacy VALUES("+std::to_string(first.id)+",'preserved')");
    raw.execute("CREATE TABLE delete_commit_guard(owner INTEGER REFERENCES recovered_characters(id))");
    raw.execute("INSERT INTO delete_commit_guard VALUES("+std::to_string(first.id)+")");
    expect_database_error([&]{repo.erase_owned(account,first.id,name);},"Unknown restricted descendant did not roll back deletion");
    require(repo.list_for_account(account).size()==2 && repo.load_resources(account,first.id)==settled.resources,
        "Failed deletion lost parent or resources");
    require(raw.scalar("SELECT count(*) FROM delete_leaf")==2,"Failed deletion lost descendant");
    raw.execute("DROP TABLE delete_commit_guard");
    require(repo.erase_owned(account,first.id,name),"Owned deletion failed");
    require(!repo.erase_owned(account,first.id,name),"Repeated deletion falsely succeeded");
    require(repo.list_for_account(account).size()==1 && repo.list_for_account(account)[0].id==second.id &&
        repo.list_for_account(other)[0].id==foreign.id && db.accounts().find_by_id(account)->password_hash=="preserved-hash",
        "Deletion touched sibling, foreign owner or account");
    require(raw.scalar("SELECT count(*) FROM recovered_positions")==0 &&
        raw.scalar("SELECT count(*) FROM character_resources")==0 &&
        raw.scalar("SELECT count(*) FROM battle_reservations")==0 &&
        raw.scalar("SELECT count(*) FROM battle_settlements")==0 &&
        raw.scalar("SELECT count(*) FROM delete_leaf")==1 &&
        raw.scalar("SELECT count(*) FROM delete_unrelated_legacy")==1,
        "Deletion left owned descendants or deleted foreign leaf");
    require(repo.create(account,make_profile({'N'})).slot==0,"Deletion did not free slot");
    std::array<std::uint8_t,54> logical{};logical[0]=0x19;logical[1]='u';logical[17]='p';logical[38]='D';logical[34]=4;
    auto wire=RecoveredWorldFrame::encode(logical);
    require(RecoveredCharacterDelete::parse(wire).has_value(),"Native deletion shape rejected");
    logical[33]=2;require(!RecoveredCharacterDelete::parse(RecoveredWorldFrame::encode(logical)),"Foreign slot accepted");
    const auto response=RecoveredWorldFrame::decode(RecoveredCharacterDelete::response(true));
    require(response && response->size()==23 && (*response)[0]==2 && (*response)[1]==0 && (*response)[2]==0,
        "Deletion response native WORD contract mismatch");
}
void test_settled_diagnostic_battle_ownership() {
    using namespace god2;
    TemporaryDatabase temporary;
    std::uint64_t account{},other_account{},character{},other_character{};
    {
        SqliteDatabase db(temporary.path());db.initialize();db.migrate();
        account=db.accounts().create("battle-owner","test-hash").id;
        other_account=db.accounts().create("other-battle-owner","test-hash").id;
        auto& repo=static_cast<SqliteRecoveredCharacterRepository&>(db.recovered_characters());
        character=repo.create(account,make_profile({'F'})).id;
        other_character=repo.create(other_account,make_profile({'G'})).id;
        require(!repo.has_settled_diagnostic_battle(account,character) &&
                !repo.has_settled_diagnostic_battle(other_account,other_character),
                "Fresh character has a settled diagnostic battle");
        const auto initial=repo.commit_resources(account,character,{},
            {100,120,50,80,0,"CUSTOM-0012"});
        const auto battle=repo.reserve_battle(account,character,initial);
        require(!repo.has_settled_diagnostic_battle(account,character),
                "Unsettled reservation suppressed the encounter");
        auto final=initial;final.mp=42;
        repo.settle_battle(account,character,battle,initial,final,true,0);
        require(repo.has_settled_diagnostic_battle(account,character) &&
                !repo.has_settled_diagnostic_battle(other_account,character) &&
                !repo.has_settled_diagnostic_battle(account,other_character),
                "Settled battle crossed the owned character boundary");
    }
    {
        SqliteDatabase db(temporary.path());db.initialize();db.migrate();
        auto& repo=static_cast<SqliteRecoveredCharacterRepository&>(db.recovered_characters());
        require(repo.has_settled_diagnostic_battle(account,character) &&
                !repo.has_settled_diagnostic_battle(other_account,other_character),
                "Battle settlement admission did not survive cold reopen");
    }
}
}

void test_recovered_character_repository() {
    const auto run=[](const char* name,auto test) {
        try { test(); }
        catch(const std::exception& error) { throw std::runtime_error(std::string(name)+": "+error.what()); }
    };
    run("settled battle ownership",test_settled_diagnostic_battle_ownership);
    run("owned character deletion",test_owned_character_deletion);
    run("town guide progress",test_town_guide_progress_disk_reopen);
    run("town guide reward",test_town_guide_atomic_reward);
    run("town guide migration",test_town_guide_reward_migration);
    run("journal reopen",test_journal_disk_reopen);
    run("inventory resource",test_inventory_resource_atomicity);
    run("checkpoint reopen",test_checkpoint_disk_reopen);
    run("revival checkpoint",test_revival_checkpoint_atomicity);
    run("battle reservation",test_battle_reservation_reopen_and_contention);
    run("settlement reopen",test_settlement_reopen_and_contention);
    run("persistence bounds",test_persistence_and_bounds);
    run("constraint rollback",test_constraints_corruption_and_rollback);
    god2::MySqlDatabase mysql;
    expect_database_error([&] { mysql.recovered_characters(); }, "MySQL recovered repository silently succeeded");
}
