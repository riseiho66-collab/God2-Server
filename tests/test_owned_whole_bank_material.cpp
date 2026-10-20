#include "game/TaiwanOwnedBankItemMaterial.h"
#include "game/TaiwanOwnedBagItemMaterial.h"
#include "protocol/RecoveredWorldFrame.h"
#include "db/SqliteMigrationManager.h"
#include "db/SqliteSupport.h"
#include <algorithm>
#include <cstring>
#include <iostream>
#include <limits>
#include <memory>
#include <stdexcept>

namespace {
using namespace god2;
using Material=TaiwanOwnedBankItemMaterial;
using Tx=SqliteOwnedEquipmentTransaction;
using Kind=RecoveredBankItems::Kind;
void require(bool value,const char* text){if(!value)throw std::runtime_error(text);}
// Synthetic preservation fixture, NOT a native feather grant/source, unlock,
// live normal-entry, successful game reply, or client opaque-helper test.
Tx::State synthetic() {
    Tx::State state;
    auto& inv=state.inventory;inv.root.id=1;inv.root.account_id=1;inv.root.created_at="synthetic";
    inv.revision=1;inv.source_sha256=std::string(64,'a');inv.source_record="SYNTHETIC-WHOLE-BANK";
    for(unsigned i=0;i<30;++i)inv.cells.push_back({"bag",i,{}});
    for(unsigned i=0;i<300;++i)inv.cells.push_back({"bank",i,{}});
    OwnedInventoryInstance item;item.id=113;item.definition_key=4422;item.quantity=17;item.stackable=true;
    item.revision=1;item.acquisition_sha256=std::string(64,'b');item.acquisition_record="SYNTHETIC-ACQUISITION";
    std::vector<std::uint8_t> raw(20,0x79);raw[0]=0x46;raw[1]=0x11;raw[2]=3;
    std::vector<std::uint8_t> full{0x3b,9,5,0x8e,0xf2};full.insert(full.end(),raw.begin(),raw.end());
    for(const auto& profile:{std::string(SharedTaiwanOwnedItemSelectionSource::alias_profile),std::string(TaiwanOwnedBagItemMaterial::profile)})
        item.aliases.push_back({NativeEquipmentSnapshot::client_pin,profile,std::string(64,'c'),"SYNTHETIC-FULL25",4422,5,1,
            profile==SharedTaiwanOwnedItemSelectionSource::alias_profile?raw:full});
    inv.cells[5].instance=item;
    auto& equipment=state.equipment;equipment.root=inv.root;equipment.position={1,1,18,14,1};
    equipment.client_sha256=NativeEquipmentSnapshot::client_pin;equipment.record_kind=NativeEquipmentSnapshot::kind;
    equipment.source_sha256=std::string(64,'d');equipment.source_record="SYNTHETIC-CACHE-WITH-OPAQUE-PREFIX";
    equipment.revision=1;equipment.actor_handle=7;equipment.record.resize(NativeEquipmentSnapshot::record_bytes);
    for(unsigned slot=0;slot<50;++slot) {
        equipment.record[slot*24+1]=static_cast<std::uint8_t>(slot+37);
        equipment.record[slot*24+2]=0x82;equipment.record[slot*24+3]=0xe9;
    }
    equipment.record[5*24]=17;std::copy(raw.begin(),raw.end(),equipment.record.begin()+5*24+4);
    equipment.record[1200]=0xda;equipment.record[1201]=7;
    return state;
}
const OwnedInventoryCell& cell(const Tx::State& state,std::string_view kind,unsigned index) {
    const auto it=std::find_if(state.inventory.cells.begin(),state.inventory.cells.end(),
        [&](const auto& value){return value.location_kind==kind && value.location_index==index;});
    if(it==state.inventory.cells.end())throw std::runtime_error("Missing fixture cell");return *it;
}
std::optional<Tx::State> plan(const Tx::State& state,RecoveredBankItems::Request request) {
    return Material::plan({state.inventory,state.equipment},request);
}
void material_round_trip() {
    const auto initial=synthetic();require(Material::qualified(initial),"Qualified synthetic bag+explicit capacity");
    const auto original=*cell(initial,"bag",5).instance;
    const RecoveredBankItems::Request deposit{Kind::Deposit,531,2,5,49,17};
    const auto bank=plan(initial,deposit);require(bank.has_value(),"Whole amount should enter explicitly present bank cell");
    const auto& deposited=*cell(*bank,"bank",149).instance;
    require(!cell(*bank,"bag",5).instance && deposited.id==original.id && deposited.quantity==17 &&
        deposited.definition_key==original.definition_key && deposited.acquisition_record==original.acquisition_record &&
        deposited.acquisition_sha256==original.acquisition_sha256 && deposited.aliases[0].record==original.aliases[0].record &&
        deposited.aliases[1].record==original.aliases[1].record,"Deposit conserves one ID/acquisition/whole25");
    require(Material::observe(deposited,2,49).has_value() && !Material::observe(deposited,0,49),"Page/local aliases remain disjoint");
    require(!Material::plan({initial.inventory,initial.equipment},{Kind::Deposit,531,2,5,49,8}),"Split is not invented");
    require(Material::mutation_wire(*bank,deposit).size()>3,"Prebuilt native deposit response");
    const RecoveredBankItems::Request move{Kind::Move,531,2,49,2,1};
    const auto moved=plan(*bank,move);require(moved && cell(*moved,"bank",102).instance->id==original.id &&
        cell(*moved,"bank",102).instance->quantity==17 && !cell(*moved,"bank",149).instance,"65 marker1 moves the whole stack");
    require(cell(*moved,"bank",102).instance->aliases[1].record==original.aliases[1].record,"Bank move retains original full25 slot and opaque");
    const RecoveredBankItems::Request withdraw{Kind::Withdraw,531,2,2,8,17};
    const auto restored=plan(*moved,withdraw);require(restored && !cell(*restored,"bank",102).instance,"Whole withdrawal leaves one custody");
    const auto& returned=*cell(*restored,"bag",8).instance;
    auto expected25=original.aliases[1].record;expected25[2]=8;
    require(returned.id==original.id && returned.quantity==original.quantity && returned.stackable==original.stackable &&
        returned.aliases[0].record==original.aliases[0].record && returned.aliases[1].record==expected25 &&
        TaiwanOwnedBagItemMaterial::observe(returned,8).has_value(),"Withdrawal only retargets known bag slot in full25");
    const auto logic=RecoveredWorldFrame::decode(Material::mutation_wire(*restored,withdraw));
    require(logic && logic->size()==64 && (*logic)[0]==0x48 && (*logic)[29]==0x41 && (*logic)[34]==0x3b &&
        (*logic)[59]==0x41,"Withdrawal clears bank/bag, replays own25, sets final quantity");
    require(restored->equipment.position==initial.equipment.position && restored->equipment.actor_handle==7 &&
        std::equal(initial.equipment.record.begin()+1200,initial.equipment.record.end(),restored->equipment.record.begin()+1200),
        "Banking preserves pose/actor/entire DA");
    for(unsigned slot=0;slot<50;++slot)require(std::equal(initial.equipment.record.begin()+slot*24+1,
        initial.equipment.record.begin()+slot*24+4,restored->equipment.record.begin()+slot*24+1),"Unknown cache prefix is preserved");
}
void namespace_capacity_and_invalid_requests() {
    const auto initial=synthetic();auto missing=initial;missing.inventory.cells.pop_back();
    require(!Material::qualified(missing) && !plan(missing,{Kind::Deposit,531,0,5,2,17}),"Absent bank cells cannot grant capacity");
    auto absent_bag=initial;absent_bag.inventory.cells.erase(absent_bag.inventory.cells.begin()+8);
    auto bank=plan(absent_bag,{Kind::Deposit,531,0,5,2,17});require(bank.has_value(),"Unrelated missing bag cell remains missing");
    require(!plan(*bank,{Kind::Withdraw,531,0,2,8,17}),"Absent bag destination is not free capacity");
    require(!plan(initial,{Kind::Deposit,531,3,5,2,17}) && !plan(initial,{Kind::Deposit,531,0,5,0,17}) &&
        !plan(initial,{Kind::Deposit,531,0,42,2,17}),"Unknown unlocked pages/special slots are not granted");
    auto misplaced=initial;misplaced.inventory.cells[5].location_kind="aaa";
    require(!Material::qualified(misplaced),"Nonbag location may not masquerade as active bag alias");
    auto extra=initial;extra.inventory.cells[5].instance->aliases.push_back(extra.inventory.cells[5].instance->aliases.back());
    require(!plan(extra,{Kind::Deposit,531,0,5,2,17}),"Unknown aliases must not be discarded");
    auto corrupt=initial;corrupt.inventory.cells[5].instance->aliases[1].record[3]^=0x80;
    // Opaque itself is explicitly retained; corrupting full20 correspondence is rejected.
    corrupt.inventory.cells[5].instance->aliases[1].record[24]^=1;
    require(!plan(corrupt,{Kind::Deposit,531,0,5,2,17}),"Full25/full20 disagreement is rejected");
    const auto wire=Material::opening_wire(initial);std::size_t offset=0,records=0;
    while(offset<wire.size()) {
        require(offset+3<=wire.size(),"Opening frame boundary");
        const auto size=std::size_t(wire[offset])+256u*wire[offset+1];
        require(size>=4 && offset+size<=wire.size(),"Opening frame size");
        const auto logical=RecoveredWorldFrame::decode(std::span<const std::uint8_t>(wire).subspan(offset,size));
        require(logical && logical->size()%29==0,"Opening frames only complete48 rows");
        for(std::size_t i=0;i<logical->size();i+=29,++records)require((*logical)[i]==0x48 &&
            (*logical)[i+1]==records/50 && (*logical)[i+6]==records%50,"All six pages retain local namespace");
        offset+=size;
    }
    require(records==300,"Opening projects exactly all explicit source cells");
}
void occupied_swap_and_reopen() {
    auto state=synthetic();
    auto second=*state.inventory.cells[5].instance;second.id=114;second.acquisition_record="SYNTHETIC-SECOND-ACQUISITION";
    for(auto& alias:second.aliases)alias.native_slot=6;
    second.aliases[1].record[2]=6;second.aliases[1].record[3]=0xa7;
    state.inventory.cells[6].instance=second;state.equipment.record[6*24]=17;
    std::copy(second.aliases[0].record.begin(),second.aliases[0].record.end(),state.equipment.record.begin()+6*24+4);
    const auto first=plan(state,{Kind::Deposit,531,0,5,2,17});require(first.has_value(),"First whole deposit");
    require(!plan(*first,{Kind::Deposit,531,0,6,2,17}),"Occupied destination may not merge a second whole identity");
    const auto both=plan(*first,{Kind::Deposit,531,0,6,3,17});require(both.has_value(),"Second whole deposit");
    const auto a=*cell(*both,"bank",2).instance,b=*cell(*both,"bank",3).instance;
    require(!plan(*both,{Kind::Deposit,531,0,5,3,17}) && !plan(*both,{Kind::Move,531,0,2,3,17}),
        "No occupied-target merge or quantity-as65-marker");
    const auto swapped=plan(*both,{Kind::Move,531,0,2,3,1});require(swapped.has_value(),"Whole occupied bank swap");
    require(cell(*swapped,"bank",3).instance->id==a.id && cell(*swapped,"bank",2).instance->id==b.id &&
        cell(*swapped,"bank",3).instance->aliases[1].record==a.aliases[1].record &&
        cell(*swapped,"bank",2).instance->aliases[1].record==b.aliases[1].record,
        "Swap conserves each own original full25, ID and opaque");
    require(!Material::opening_wire(*swapped).empty(),"Reopen projects latest same-custody state");
    auto stale_namespace=*swapped;
    stale_namespace.inventory.cells[32].instance->aliases[0].profile=Material::identity_profile(1);
    require(!Material::qualified(stale_namespace),"Wrong page alias cannot be accepted as local bank identity");
    auto exhausted=state;exhausted.inventory.revision=std::numeric_limits<std::int64_t>::max();
    require(!plan(exhausted,{Kind::Deposit,531,0,5,2,17}),"Revision overflow cannot wrap custody");
}
struct Fixture {
    struct Close{void operator()(sqlite3* db)const{sqlite3_close_v2(db);}};
    std::unique_ptr<sqlite3,Close> db;
    std::unique_ptr<SqliteAccountRepository> accounts;
    std::unique_ptr<SqliteRecoveredCharacterRepository> characters;
    std::unique_ptr<SqliteOwnedInventoryRepository> inventory;
    std::unique_ptr<SqliteNativeEquipmentSnapshotRepository> equipment;
    std::unique_ptr<Tx> transaction;
    Tx::State initial=synthetic();
    Fixture() {
        sqlite3* raw=nullptr;require(sqlite3_open(":memory:",&raw)==SQLITE_OK,"Open isolated fixture");db.reset(raw);
        sqlite_detail::execute(raw,"PRAGMA foreign_keys=ON");SqliteMigrationManager(raw,default_sqlite_migrations()).migrate();
        accounts=std::make_unique<SqliteAccountRepository>(raw);characters=std::make_unique<SqliteRecoveredCharacterRepository>(raw);
        const auto account=accounts->create("whole-bank-fixture","fixture-hash");
        std::array<std::uint8_t,40> profile{};profile[0]='A';
        const auto root=characters->create(account.id,profile);
        const auto position=characters->commit_position(account.id,root.id,{},1,1,18,14);
        initial.inventory.root=initial.equipment.root=root;initial.equipment.position=position;
        sqlite_detail::execute(raw,SqliteOwnedInventoryRepository::schema());
        sqlite_detail::execute(raw,SqliteNativeEquipmentSnapshotRepository::schema());
        inventory=std::make_unique<SqliteOwnedInventoryRepository>(raw,*accounts,*characters);
        equipment=std::make_unique<SqliteNativeEquipmentSnapshotRepository>(raw,*accounts,*characters);
        transaction=std::make_unique<Tx>(*inventory,*equipment);
        require(transaction->replace_from_issuer({},initial,[](const auto&,const auto& next,auto){return std::optional{next};}).has_value(),
            "Only isolated fixture issuer creates synthetic material");
    }
    auto before(){return transaction->observe_before(initial.inventory.root.account_id,initial.inventory.root.id);}
};
struct Observation {bool after_issuer=false,live=true,commit_profile=false;};
int trace(unsigned event,void* context,void* statement,void*) noexcept {
    auto& state=*static_cast<Observation*>(context);
    if(event==SQLITE_TRACE_STMT && state.after_issuer && !state.commit_profile)state.live=false;
    if(event==SQLITE_TRACE_PROFILE && state.commit_profile) {
        const auto sql=sqlite3_sql(static_cast<sqlite3_stmt*>(statement));
        if(sql && std::strcmp(sql,"COMMIT")==0)state.live=false;
    }
    return 0;
}
void final_fence_and_commit_truth() {
    Fixture f;const auto expected=f.before();require(expected.has_value(),"Read actual common/joint fixture tuple");
    const auto next=Material::plan(*expected,{Kind::Deposit,531,0,5,2,17});require(next.has_value(),"Plan fixture deposit");
    Observation state;sqlite3_trace_v2(f.db.get(),SQLITE_TRACE_STMT,trace,&state);
    const auto rejected=f.transaction->replace_from_issuer(*expected,*next,[&](const auto&,const auto& proposed,auto check) {
        if(check==Tx::Check::BeforeCommit)state.after_issuer=true;return std::optional{proposed};
    },[&]{return state.live;});
    sqlite3_trace_v2(f.db.get(),0,nullptr,nullptr);
    const auto unchanged=f.before();
    require(!rejected && unchanged && unchanged->inventory==expected->inventory && unchanged->equipment==expected->equipment,
        "Retirement by last SQL observer must rollback both full populations");
    state={};state.commit_profile=true;sqlite3_trace_v2(f.db.get(),SQLITE_TRACE_PROFILE,trace,&state);
    const auto committed=f.transaction->replace_from_issuer(*expected,*next,
        [](const auto&,const auto& proposed,auto){return std::optional{proposed};},[&]{return state.live;});
    sqlite3_trace_v2(f.db.get(),0,nullptr,nullptr);
    require(committed && !state.live && f.transaction->committed_current(*committed),"Postcommit retirement preserves durable actual receipt");
    bool stale=false;try{(void)f.transaction->replace_from_issuer(*expected,*next,
        [](const auto&,const auto& proposed,auto){return std::optional{proposed};});}catch(const DatabaseError&){stale=true;}
    require(stale && f.transaction->committed_current(*committed),"Stale expected tuple cannot overwrite new custody");
}
}
int main()try {
    material_round_trip();namespace_capacity_and_invalid_requests();occupied_swap_and_reopen();final_fence_and_commit_truth();
    std::cout<<"Whole-bank preservation/source regressions (no native acceptance claim)\n";return 0;
}catch(const std::exception& error){std::cerr<<error.what()<<'\n';return 1;}
