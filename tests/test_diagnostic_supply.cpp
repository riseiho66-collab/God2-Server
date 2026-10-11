#include "handlers/DiagnosticSupplyService.h"
#include "db/SqliteDatabase.h"
#include "db/SqliteSupport.h"
#include "protocol/RecoveredInventoryItemRequest.h"
#include "protocol/RecoveredTargetItemRequest.h"
#include "protocol/RecoveredWorldFrame.h"
#include <iostream>
#include <stdexcept>

static void require(bool yes) { if (!yes) throw std::runtime_error("Supply transaction mismatch"); }
template<class F> void rejects(F f) {
    bool rejected=false;
    try { f(); } catch (const std::exception&) { rejected=true; }
    require(rejected);
}
static void prepare_copy(const char* input, const char* output, std::uint8_t count=3, bool healing=false) {
    using namespace god2;
    const auto root=std::filesystem::canonical(std::filesystem::path(GOD2_SOURCE_DIR)/"artifacts/runs");
    const auto source=std::filesystem::canonical(input);
    const auto directory=std::filesystem::weakly_canonical(output);
    require(source.filename()=="diagnostic-accounts.db" && directory.parent_path()==root &&
        source.parent_path().parent_path()==root && !std::filesystem::exists(directory));
    require(std::filesystem::create_directory(directory));
    const auto target=directory/"diagnostic-accounts.db";
    sqlite3 *from=nullptr,*to=nullptr;
    auto path_text=[](const auto& p) { const auto s=p.u8string(); return std::string(s.begin(),s.end()); };
    try {
        require(sqlite3_open_v2(path_text(source).c_str(),&from,SQLITE_OPEN_READONLY,nullptr)==SQLITE_OK);
        require(sqlite3_open_v2(path_text(target).c_str(),&to,SQLITE_OPEN_READWRITE|SQLITE_OPEN_CREATE,nullptr)==SQLITE_OK);
        auto* copy=sqlite3_backup_init(to,"main",from,"main"); require(copy!=nullptr);
        const int step=sqlite3_backup_step(copy,-1);
        const int finish=sqlite3_backup_finish(copy);
        require(step==SQLITE_DONE && finish==SQLITE_OK);
    } catch(...) { sqlite3_close_v2(to);sqlite3_close_v2(from);throw; }
    sqlite3_close_v2(to);sqlite3_close_v2(from);
    SqliteDatabase db(target); db.initialize(); db.migrate();
    auto& repo=static_cast<SqliteRecoveredCharacterRepository&>(db.recovered_characters());
    const auto characters=repo.list_for_account(1);
    require(characters.size()==1 && characters.front().id==1);
    const auto resources=repo.load_resources(1,1);
    const unsigned hp=healing?4:52,mp=healing?56:2;
    const std::uint16_t item=healing?3101:3107;
    require(resources && resources->hp==hp && resources->max_hp==120 && resources->mp==mp &&
        resources->max_mp==80 && resources->design_id=="CUSTOM-0012");
    const auto previous=repo.load_inventory_slot(1,1,0);
    require(healing ? (previous && !previous->item_id && !previous->count && previous->revision==4 && resources->revision==20) : !previous);
    const auto saved=repo.commit_inventory_resources(1,1,0,previous,*resources,
        {item,count,0,"70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731"},*resources);
    require(saved.slot.count==count && saved.resources.hp==hp && saved.resources.mp==mp);
    std::cout<<"CUSTOM-0016 isolated copy prepared; item="<<item<<" count="<<unsigned(count)<<"; source read-only\n";
}
int main(int argc,char** argv) {
    try {
        if(argc==4 && std::string(argv[1])=="--prepare-copy") { prepare_copy(argv[2],argv[3]); return 0; }
        if(argc==4 && std::string(argv[1])=="--prepare-single-copy") { prepare_copy(argv[2],argv[3],1); return 0; }
        if(argc==4 && std::string(argv[1])=="--prepare-healing-copy") { prepare_copy(argv[2],argv[3],3,true); return 0; }
        require(argc==1);
        using namespace god2;
        SqliteDatabase db(":memory:"); db.initialize(); db.migrate();
        const auto account=db.accounts().create("supply-test","test-hash").id;
        const auto other=db.accounts().create("supply-other","test-hash").id;
        auto& repo=static_cast<SqliteRecoveredCharacterRepository&>(db.recovered_characters());
        std::array<std::uint8_t,40> profile{}; profile[0]='P';
        const auto character=repo.create(account,profile).id;
        auto resources=repo.commit_resources(account,character,{}, {52,120,2,80,0,"CUSTOM-0012"});
        const std::string source="70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731";
        auto saved=repo.commit_inventory_resources(account,character,0,{},resources,
            {3107,3,0,source},resources);
        LuaEngine lua(std::filesystem::path(GOD2_SOURCE_DIR)/"scripts",false);
        require(lua.initialize());
        DiagnosticSupplyService service(repo,lua);
        const DiagnosticSupplyService::Policy policy{3107,0x1234,source,0,50};
        const auto request=RecoveredTargetItemRequest::encode({0x1234,3107,0,0xa5});
        require(request==RecoveredTargetItemRequest::LogicalRecord{0x26,0x34,0x12,0x23,0x0c,0,0xa5});
        for (unsigned tail=0;tail<256;++tail) {
            const auto raw=RecoveredTargetItemRequest::encode({0xffff,0xffff,255,static_cast<std::uint8_t>(tail)});
            const auto decoded=RecoveredTargetItemRequest::decode(raw);
            require(decoded && decoded->raw_target==65535 && decoded->client_item_id==65535 &&
                decoded->raw_slot==255 && decoded->raw_tail==tail);
        }
        const auto old=RecoveredInventoryItemRequest::encode({3107,0,0});
        rejects([&]{service.use(account,character,old,policy,saved.slot,saved.resources);});
        for (const auto bad : {RecoveredTargetItemRequest::encode({0x1234,3108,0,0}),
                RecoveredTargetItemRequest::encode({0x1234,3107,30,0}),
                RecoveredTargetItemRequest::encode({0x1235,3107,0,0}),
                RecoveredTargetItemRequest::encode({0x1234,3107,1,0})})
            rejects([&]{service.use(account,character,bad,policy,saved.slot,saved.resources);});
        for(std::size_t size=0;size<request.size();++size)
            rejects([&]{service.use(account,character,std::span(request).first(size),policy,saved.slot,saved.resources);});
        auto extended=std::vector<std::uint8_t>(request.begin(),request.end());extended.push_back(0);
        rejects([&]{service.use(account,character,extended,policy,saved.slot,saved.resources);});
        rejects([&]{service.use(other,character,request,policy,saved.slot,saved.resources);});
        auto wrong=policy; wrong.source_sha256=std::string(64,'a');
        rejects([&]{service.use(account,character,request,wrong,saved.slot,saved.resources);});
        for (const auto target : {0u,0x4000u,0xffffu}) {
            auto invalid_target=policy; invalid_target.expected_target=static_cast<std::uint16_t>(target);
            const auto forged=RecoveredTargetItemRequest::encode({static_cast<std::uint16_t>(target),3107,0,0});
            rejects([&]{service.use(account,character,forged,invalid_target,saved.slot,saved.resources);});
        }
        require(repo.load_resources(account,character)==saved.resources);
        require(repo.load_inventory_slot(account,character,0)==saved.slot);
        const auto result=service.use(account,character,request,policy,saved.slot,saved.resources);
        require(result.consumed);
        require(result.resources==repo.load_resources(account,character));
        const auto logical=RecoveredWorldFrame::decode(result.wire);
        require(logical && logical->size()==22 && (*logical)[0]==0x41 && (*logical)[4]==2 &&
            (*logical)[5]==0x24 && (*logical)[6]==52 && (*logical)[10]==52);
        require(repo.load_inventory_slot(account,character,0)->count==2 &&
            repo.load_resources(account,character)->mp==52);
        rejects([&]{service.use(account,character,request,policy,saved.slot,saved.resources);});
        auto slot=*repo.load_inventory_slot(account,character,0);
        resources=*repo.load_resources(account,character);
        const auto changed_tail=RecoveredTargetItemRequest::encode({0x1234,3107,0,0xff});
        require(service.use(account,character,changed_tail,policy,slot,resources).consumed);
        slot=*repo.load_inventory_slot(account,character,0);
        resources=*repo.load_resources(account,character);
        require(slot.count==1 && resources.mp==80);
        const auto noop=service.use(account,character,request,policy,slot,resources);
        require(!noop.consumed && noop.wire.empty() && !noop.resources && repo.load_resources(account,character)==resources &&
            repo.load_inventory_slot(account,character,0)==slot);
        auto drained=resources; drained.mp=2;
        resources=repo.commit_resources(account,character,resources,drained);
        const auto first_battle=repo.reserve_battle(account,character,resources);
        require(repo.owned_pending_battle(account,character));
        rejects([&]{(void)repo.owned_pending_battle(other,character);});
        rejects([&]{service.use(account,character,request,policy,slot,resources);});
        require(repo.load_resources(account,character)==resources && repo.load_inventory_slot(account,character,0)==slot);
        // Explicit transaction outcomes, not an emulated fight or native formula.
        const auto before_first=resources;
        auto after_first=resources;after_first.hp=40;
        const auto first_settlement=repo.settle_battle(account,character,first_battle,before_first,after_first,true,25);
        require(!repo.owned_pending_battle(account,character));
        resources=first_settlement.resources;
        require(service.use(account,character,request,policy,slot,resources).consumed);
        const auto supplied=*repo.load_resources(account,character);
        const auto empty=*repo.load_inventory_slot(account,character,0);
        require(supplied.hp==40 && supplied.mp==52 && empty.count==0 && empty.item_id==0);
        require(repo.settle_battle(account,character,first_battle,before_first,after_first,true,25)==first_settlement);
        require(repo.load_resources(account,character)==supplied && repo.load_inventory_slot(account,character,0)==empty);
        rejects([&]{repo.reserve_battle(account,character,resources);});
        const auto second_battle=repo.reserve_battle(account,character,supplied);
        require(second_battle!=first_battle);
        rejects([&]{repo.commit_inventory_resources(account,character,0,empty,supplied,
            {3107,1,empty.revision,source},supplied);});
        auto after_second=supplied;after_second.hp=28;after_second.mp=44;
        const auto second_settlement=repo.settle_battle(account,character,second_battle,supplied,after_second,true,25);
        require(second_settlement.resources.hp==28 && second_settlement.resources.mp==44 &&
            second_settlement.total_experience==50);
        require(repo.settle_battle(account,character,first_battle,before_first,after_first,true,25)==first_settlement);
        require(repo.load_resources(account,character)==second_settlement.resources &&
            repo.load_experience(account,character)->total==50 && repo.load_inventory_slot(account,character,0)==empty);
        const auto healing=DiagnosticSupplyService::current_supply_policy(3101,0x1234);
        require(healing && healing->restore_hp==100 && healing->restore_mp==0 && healing->source_sha256==source);
        const auto mana=DiagnosticSupplyService::current_supply_policy(3107,0x1234);
        require(mana && mana->restore_hp==0 && mana->restore_mp==50);
        require(!DiagnosticSupplyService::current_supply_policy(3102,1) &&
            !DiagnosticSupplyService::current_supply_policy(3101,0) &&
            !DiagnosticSupplyService::current_supply_policy(3101,0x4000));
        const auto healing_seed=repo.commit_inventory_resources(account,character,0,empty,second_settlement.resources,
            {3101,1,0,source},second_settlement.resources);
        const auto heal_request=RecoveredTargetItemRequest::encode({0x1234,3101,0,0xff});
        require(service.use(account,character,heal_request,*healing,healing_seed.slot,healing_seed.resources).consumed);
        const auto healed=repo.load_resources(account,character);
        require(healed->hp==120 && healed->mp==44 && repo.load_inventory_slot(account,character,0)->count==0);
        auto dead=*healed;dead.hp=0;dead.mp=0;
        const auto dead_seed=repo.commit_inventory_resources(account,character,0,
            repo.load_inventory_slot(account,character,0),*healed,{3101,1,0,source},dead);
        for(unsigned tail=0;tail<256;++tail) {
            const auto input=RecoveredTargetItemRequest::encode({0x1234,3101,0,static_cast<std::uint8_t>(tail)});
            const auto refused=service.use(account,character,input,*healing,dead_seed.slot,dead_seed.resources);
            require(!refused.consumed && refused.wire.empty());
            require(repo.load_resources(account,character)==dead_seed.resources &&
                    repo.load_inventory_slot(account,character,0)==dead_seed.slot);
        }
        std::cout<<"Supply request, Lua projection, atomic storage and encoded replies passed\n";
    } catch (const std::exception& e) { std::cerr<<e.what()<<'\n'; return 1; }
}
