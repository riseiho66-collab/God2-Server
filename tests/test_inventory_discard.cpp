#include "handlers/InventoryDiscardService.h"
#include "db/SqliteDatabase.h"
#include "db/SqliteMigrationManager.h"
#include "db/SqliteSupport.h"
#include "protocol/RecoveredWorldRecords.h"
#include <iostream>
#include <memory>
#include <stdexcept>

void require(bool value,const char* message) {if(!value)throw std::runtime_error(message);}
template<class F> void rejects(F&& f) {
    try {f();}catch(const std::exception&){return;}
    throw std::runtime_error("Expected discard rejection");
}
int main() {
    try {
        using namespace god2;
        sqlite3* raw=nullptr;require(sqlite3_open(":memory:",&raw)==SQLITE_OK,"Open failed");
        std::unique_ptr<sqlite3,decltype(&sqlite3_close_v2)> db(raw,sqlite3_close_v2);
        sqlite_detail::execute(raw,"PRAGMA foreign_keys=ON");
        SqliteMigrationManager(raw,default_sqlite_migrations()).migrate();
        sqlite_detail::execute(raw,"INSERT INTO accounts(id,username,password_hash) VALUES(1,'one','hash'),(2,'two','hash')");
        SqliteRecoveredCharacterRepository repo(raw);
        std::array<std::uint8_t,40> profile{};profile[0]='A';
        const auto role=repo.create(1,profile).id;
        auto resources=repo.commit_resources(1,role,{}, {50,120,10,80,0,"CUSTOM-0012"});
        repo.provision_town_reward_slot(1,role);repo.provision_owned_bag(1,role);
        const auto hash=SqliteRecoveredCharacterRepository::town_reward_item_source_sha256;
        auto before=repo.commit_inventory_resources(1,role,5,repo.load_inventory_slot(1,role,5),resources,
            {3107,7,0,hash},resources).slot;
        resources=*repo.load_resources(1,role);
        const auto other=repo.load_inventory_slot(1,role,6);
        InventoryDiscardService service(repo,[&](const StoredInventorySlot& slot){return slot.item_id==3107 && slot.source_sha256==hash;});
        for(const auto r:{RecoveredInventoryDiscard::Request{3107,5,0},{3107,5,8},{3101,5,1},{3107,30,1}})
            rejects([&]{service.discard(1,role,r,before);});
        rejects([&]{service.discard(2,role,{3107,5,1},before);});
        auto corrupted=before;++corrupted.revision;
        rejects([&]{service.discard(1,role,{3107,5,1},corrupted);});
        require(repo.load_inventory_slot(1,role,5)==std::optional{before},"Rejected discard changed stack");
        auto result=service.discard(1,role,{3107,5,4},before);
        require(result.slot.count==3 && result.slot.item_id==3107 && result.slot.revision==before.revision+1 &&
            RecoveredWorldFrame::decode(result.wire)==std::optional{std::vector<std::uint8_t>{0x41,0x23,0x0c,5,3}},"Partial discard/projection mismatch");
        rejects([&]{service.discard(1,role,{3107,5,4},before);});
        before=result.slot;
        for(const char* trigger:{
            "CREATE TRIGGER fail AFTER UPDATE ON diagnostic_inventory_slots WHEN NEW.slot=5 BEGIN SELECT RAISE(ABORT,'injected'); END",
            "CREATE TRIGGER fail AFTER UPDATE ON diagnostic_inventory_slots WHEN NEW.slot=5 BEGIN UPDATE diagnostic_inventory_slots SET count=2 WHERE slot=5; END"}) {
            sqlite_detail::execute(raw,trigger);
            rejects([&]{service.discard(1,role,{3107,5,3},before);});
            require(repo.load_inventory_slot(1,role,5)==std::optional{before},"Failure did not roll back discard");
            sqlite_detail::execute(raw,"DROP TRIGGER fail");
        }
        result=service.discard(1,role,{3107,5,3},before);
        require(!result.slot.count && !result.slot.item_id && result.slot.source_sha256==hash &&
            RecoveredWorldFrame::decode(result.wire)==std::optional{std::vector<std::uint8_t>{0x41,0,0,5,0}},"Whole discard/clear mismatch");
        require(repo.load_resources(1,role)==std::optional{resources} && repo.load_inventory_slot(1,role,6)==other,
            "Discard changed resources/other slot");
        before=repo.commit_inventory_resources(1,role,5,result.slot,resources,{3107,7,0,hash},resources).slot;
        resources=*repo.load_resources(1,role);repo.reserve_battle(1,role,resources);
        rejects([&]{service.discard(1,role,{3107,5,1},before);});
        require(repo.load_inventory_slot(1,role,5)==std::optional{before},"Pending battle discard changed stack");
        for(unsigned slot=0;slot<256;++slot)for(unsigned qty=0;qty<256;++qty) {
            const RecoveredInventoryDiscard::Request r{0x1234,static_cast<std::uint8_t>(slot),static_cast<std::uint8_t>(qty)};
            const auto wire=RecoveredInventoryDiscard::encode(r);
            require(RecoveredInventoryDiscard::decode(wire)==std::optional{r},"Discard byte roundtrip");
            const auto parsed=RecoveredWorldRecords::decode(wire);
            require(parsed && parsed->size()==1 && std::get<RecoveredInventoryDiscard::Request>(parsed->front())==r,"World discard parser mismatch");
        }
        const auto short_wire=RecoveredInventoryDiscard::encode({3107,5,1});
        for(unsigned size=0;size<5;++size)require(!RecoveredWorldRecords::decode(std::span(short_wire).first(size)),"Truncated discard accepted");
        std::cout<<"Discard native codec, owned CAS, partial/whole projection and rollback passed\n";
    }catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}
}
