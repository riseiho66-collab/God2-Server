#include "handlers/InventoryMoveService.h"
#include "db/SqliteMigrationManager.h"
#include "db/SqliteDatabase.h"
#include "db/SqliteSupport.h"
#include "protocol/RecoveredWorldFrame.h"
#include <iostream>
#include <memory>
#include <limits>
#include <stdexcept>
#include <random>

namespace {
void require(bool value,const char* message) { if(!value) throw std::runtime_error(message); }
template<class F> void rejects(F&& f) {
    try { f(); } catch(const std::exception&) { return; }
    throw std::runtime_error("Expected inventory move rejection");
}
struct Fixture {
    struct Close { void operator()(sqlite3* value) const { sqlite3_close_v2(value); } };
    std::unique_ptr<sqlite3,Close> db;
    std::uint64_t character{};
    Fixture() {
        sqlite3* raw=nullptr;
        require(sqlite3_open(":memory:",&raw)==SQLITE_OK,"Open failed"); db.reset(raw);
        god2::sqlite_detail::execute(raw,"PRAGMA foreign_keys=ON");
        god2::SqliteMigrationManager(raw,god2::default_sqlite_migrations()).migrate();
        god2::sqlite_detail::execute(raw,"INSERT INTO accounts(id,username,password_hash) VALUES(1,'first','hash'),(2,'other','hash')");
        std::array<std::uint8_t,40> profile{};profile[0]='A';
        character=repo().create(1,profile).id;
        repo().commit_resources(1,character,{}, {52,120,2,80,0,"CUSTOM-0012"});
    }
    god2::SqliteRecoveredCharacterRepository repo() { return god2::SqliteRecoveredCharacterRepository(db.get()); }
    void sql(const char* text) { god2::sqlite_detail::execute(db.get(),text); }
    god2::StoredInventorySlot get(std::uint8_t slot) { return *repo().load_inventory_slot(1,character,slot); }
    void seed(std::uint8_t slot,std::uint16_t item,std::uint8_t count,const std::string& hash) {
        auto r=repo();const auto resources=*r.load_resources(1,character);
        r.commit_inventory_resources(1,character,slot,r.load_inventory_slot(1,character,slot),resources,
            {item,count,0,hash},resources);
    }
};
void delayed_allocation() {
    using namespace god2;
    Fixture f;auto repo=f.repo();
    repo.provision_town_reward_slot(1,f.character);
    f.seed(0,5569,1,SqliteRecoveredCharacterRepository::town_reward_item_source_sha256);
    const auto existing=repo.load_saved_supply_slots(1,f.character);
    const auto resources=*repo.load_resources(1,f.character);
    const auto battle=repo.reserve_battle(1,f.character,resources);
    const auto changes=sqlite3_total_changes64(f.db.get());
    require(existing.size()==1 && repo.provision_owned_bag(1,f.character)==0 &&
        repo.provision_owned_bag(1,f.character)==0,"Pending legacy bag allocation was not deferred");
    require(sqlite3_total_changes64(f.db.get())==changes &&
        repo.load_saved_supply_slots(1,f.character)==existing &&
        repo.load_resources(1,f.character)==resources,"Deferred allocation changed database");
    repo.settle_battle(1,f.character,battle,resources,resources,true,0);
    const auto settled_resources=repo.load_resources(1,f.character);
    require(repo.provision_owned_bag(1,f.character)==29 &&
        repo.load_saved_supply_slots(1,f.character).size()==30 &&
        f.get(0)==existing.front().second &&
        repo.load_resources(1,f.character)==settled_resources,
        "Settled legacy bag did not allocate without changing existing state");
    require(repo.provision_owned_bag(1,f.character)==0,"Settled allocation was not idempotent");
}
void disk_reopen() {
    using namespace god2;
    struct TemporaryDirectory {
        std::filesystem::path path;
        TemporaryDirectory() {
            std::random_device random;
            for(unsigned attempt=0;attempt<100;++attempt) {
                path=std::filesystem::temp_directory_path()/
                    ("god2-inventory-move-"+std::to_string(random())+"-"+std::to_string(random()));
                if(std::filesystem::create_directory(path)) return;
            }
            throw std::runtime_error("Cannot create inventory persistence fixture");
        }
        ~TemporaryDirectory() { std::error_code error;std::filesystem::remove_all(path,error); }
    } temporary;
    const auto file=temporary.path/"fixture.sqlite";
    std::uint64_t account{},character{};
    std::vector<std::pair<std::uint8_t,StoredInventorySlot>> expected;
    {
        SqliteDatabase db(file);db.initialize();db.migrate();
        auto& repo=static_cast<SqliteRecoveredCharacterRepository&>(db.recovered_characters());
        account=db.accounts().create("persistence","hash").id;
        std::array<std::uint8_t,40> profile{};profile[0]='P';character=repo.create(account,profile).id;
        repo.provision_town_reward_slot(account,character);repo.provision_owned_bag(account,character);
        auto resources=repo.commit_resources(account,character,{}, {52,120,2,80,0,"CUSTOM-0012"});
        const auto seeded=repo.commit_inventory_resources(account,character,0,
            repo.load_inventory_slot(account,character,0),resources,
            {5569,1,0,SqliteRecoveredCharacterRepository::town_reward_item_source_sha256},resources);
        repo.commit_inventory_move(account,character,0,29,seeded.slot,*repo.load_inventory_slot(account,character,29));
        expected=repo.load_saved_supply_slots(account,character);
    }
    {
        SqliteDatabase db(file);db.initialize();db.migrate();
        auto& repo=static_cast<SqliteRecoveredCharacterRepository&>(db.recovered_characters());
        require(repo.load_saved_supply_slots(account,character)==expected &&
            repo.load_inventory_slot(account,character,29)->item_id==5569 &&
            repo.provision_owned_bag(account,character)==0,"Disk reopen lost saved move");
    }
}
}
int main() {
    try {
        using namespace god2;
        Fixture f;auto repo=f.repo();const auto character=f.character;
        const std::string hash=SqliteRecoveredCharacterRepository::town_reward_item_source_sha256;
        rejects([&]{repo.provision_owned_bag(1,character);});
        require(repo.load_saved_supply_slots(1,character).empty(),"Absent slot treated as empty");
        repo.provision_town_reward_slot(1,character);
        f.seed(0,5569,1,hash);f.seed(12,3107,7,std::string(64,'a'));f.seed(30,111,2,hash);
        const auto initial=f.get(0),other=f.get(12),equipment=f.get(30);
        const auto resources=repo.load_resources(1,character);
        rejects([&]{repo.provision_owned_bag(2,character);});
        f.sql("CREATE TRIGGER fail_allocate AFTER INSERT ON diagnostic_inventory_slots WHEN NEW.slot=8 BEGIN SELECT RAISE(ABORT,'injected'); END");
        rejects([&]{repo.provision_owned_bag(1,character);});
        require(!repo.load_inventory_slot(1,character,1) && f.get(0)==initial && f.get(12)==other,"Allocation failed to roll back");
        f.sql("DROP TRIGGER fail_allocate");
        f.sql("CREATE TRIGGER corrupt_allocate AFTER INSERT ON diagnostic_inventory_slots WHEN NEW.slot=8 BEGIN UPDATE diagnostic_inventory_slots SET revision=2 WHERE slot=1; END");
        rejects([&]{repo.provision_owned_bag(1,character);});
        require(!repo.load_inventory_slot(1,character,1),"Delayed allocation corruption did not roll back");
        f.sql("DROP TRIGGER corrupt_allocate");
        require(repo.provision_owned_bag(1,character)==28,"Wrong allocation count");
        const auto baseline=repo.load_saved_supply_slots(1,character);
        require(repo.provision_owned_bag(1,character)==0 && repo.load_saved_supply_slots(1,character)==baseline,
            "Allocation was not idempotent");
        require(f.get(0)==initial && f.get(12)==other && f.get(30)==equipment &&
            repo.load_resources(1,character)==resources,"Allocation changed existing state");
        const auto empty=f.get(5);
        const auto moved=repo.commit_inventory_move(1,character,0,5,initial,empty);
        require(moved.source.item_id==0 && moved.source.revision==initial.revision+1 &&
            moved.destination.item_id==5569 && moved.destination.revision==empty.revision+1 &&
            moved.destination.count==1 && moved.destination.source_sha256==hash,"Move mismatch");
        rejects([&]{repo.commit_inventory_move(1,character,0,5,initial,empty);});
        rejects([&]{repo.commit_inventory_move(1,character,0,5,moved.source,moved.destination);});
        rejects([&]{repo.commit_inventory_move(2,character,5,12,moved.destination,other);});
        rejects([&]{repo.commit_inventory_move(1,character,5,5,moved.destination,moved.destination);});
        rejects([&]{repo.commit_inventory_move(1,character,5,30,moved.destination,equipment);});
        f.sql("DELETE FROM diagnostic_inventory_slots WHERE slot=29");
        rejects([&]{repo.commit_inventory_move(1,character,5,29,moved.destination,empty);});
        repo.provision_owned_bag(1,character);
        f.sql("CREATE TRIGGER fail_second AFTER UPDATE ON diagnostic_inventory_slots WHEN NEW.slot=12 BEGIN SELECT RAISE(ABORT,'injected'); END");
        rejects([&]{repo.commit_inventory_move(1,character,5,12,moved.destination,other);});
        require(f.get(5)==moved.destination && f.get(12)==other,"Second write failure did not roll back first");
        f.sql("DROP TRIGGER fail_second");
        f.sql("CREATE TRIGGER corrupt_second AFTER UPDATE ON diagnostic_inventory_slots WHEN NEW.slot=12 BEGIN UPDATE diagnostic_inventory_slots SET count=6 WHERE slot=12; END");
        rejects([&]{repo.commit_inventory_move(1,character,5,12,moved.destination,other);});
        require(f.get(5)==moved.destination && f.get(12)==other,"Readback corruption did not roll back");
        f.sql("DROP TRIGGER corrupt_second");
        const auto swapped=repo.commit_inventory_move(1,character,5,12,moved.destination,other);
        require(swapped.source.item_id==3107 && swapped.source.count==7 && swapped.source.source_sha256==other.source_sha256 &&
            swapped.destination.item_id==5569 && swapped.destination.count==1 && swapped.destination.source_sha256==hash,
            "Swap lost counts or provenance");
        // Same-item whole-stack swap preserves both independent counts; no merge.
        f.seed(6,3107,4,other.source_sha256);
        const auto six=f.get(6);
        const auto same=repo.commit_inventory_move(1,character,5,6,swapped.source,six);
        require(same.source.count==4 && same.destination.count==7,"Same-item stacks merged");
        auto eligible=[&](const StoredInventorySlot& slot) { return slot.item_id==5569 && slot.source_sha256==hash; };
        // Test-only wire projection: real native encoding is supplied by Application.
        auto encoder=[](const InventoryMoveService::Request& request,const InventoryMoveCommit& next) {
            return RecoveredWorldFrame::encode(std::array<std::uint8_t,3>{0xee,request.source_slot,next.destination.count});
        };
        InventoryMoveService service(repo,eligible,encoder);
        const auto map=f.get(12),blank=f.get(0);
        rejects([&]{service.move(1,character,{12,5},map,same.source);});
        InventoryMoveService missing(repo,eligible,{});
        rejects([&]{missing.move(1,character,{12,0},map,blank);});
        InventoryMoveService throwing(repo,eligible,[](const auto&,const auto&)->std::vector<std::uint8_t>{throw std::runtime_error("encode");});
        rejects([&]{throwing.move(1,character,{12,0},map,blank);});
        for(const auto wire: {std::vector<std::uint8_t>{},std::vector<std::uint8_t>{4,0,0,0}}) {
            InventoryMoveService bad(repo,eligible,[&](const auto&,const auto&){return wire;});
            rejects([&]{bad.move(1,character,{12,0},map,blank);});
        }
        require(f.get(12)==map && f.get(0)==blank,"Encoder failure changed database");
        const auto result=service.move(1,character,{12,0},map,blank);
        require(result.commit.source.item_id==0 && result.commit.destination.item_id==5569 &&
            RecoveredWorldFrame::decode(result.wire)==std::optional{std::vector<std::uint8_t>{0xee,12,1}},"Service result mismatch");
        f.sql("UPDATE diagnostic_inventory_slots SET revision=9223372036854775807 WHERE slot=29");
        rejects([&]{repo.commit_inventory_move(1,character,0,29,f.get(0),f.get(29));});
        const auto before_battle=repo.load_saved_supply_slots(1,character);
        const auto current_resources=*repo.load_resources(1,character);
        repo.reserve_battle(1,character,current_resources);
        rejects([&]{repo.commit_inventory_move(1,character,0,12,f.get(0),f.get(12));});
        require(repo.provision_owned_bag(1,character)==0,"Complete bag was not a no-op during battle");
        require(repo.load_saved_supply_slots(1,character)==before_battle && f.get(30)==equipment &&
            repo.load_resources(1,character)==current_resources,"Battle rejection changed state");
        // A new repository instance reads the committed persisted rows.
        require(f.repo().load_saved_supply_slots(1,character)==before_battle,"Repository reload lost inventory");
        f.sql("DELETE FROM diagnostic_inventory_slots WHERE slot=28");
        const auto pending_changes=sqlite3_total_changes64(f.db.get());
        require(repo.provision_owned_bag(1,character)==0 &&
            sqlite3_total_changes64(f.db.get())==pending_changes &&
            !repo.load_inventory_slot(1,character,28),"Pending battle initialized missing slot");
        delayed_allocation();
        disk_reopen();
        std::cout<<"Owned bag allocation, CAS move/swap, service encoding and rollback passed\n";
    } catch(const std::exception& e) { std::cerr<<e.what()<<'\n';return 1; }
}
