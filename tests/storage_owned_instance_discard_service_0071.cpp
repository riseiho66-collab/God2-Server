// NEW CUSTOM-0071 service gate. Frozen0068 fixture provides actual qualified
// native weapon definitions; no old fixture/service is changed or executed.
#define main owned_discard_service_fixture_main
#include "storage_owned_foreign_bank_0068.cpp"
#undef main
#include "handlers/OwnedInstanceDiscardService.h"
#include "protocol/RecoveredArmorSourceSlots.h"
#include "protocol/RecoveredWorldFrame.h"
#include <functional>

namespace {
using Discard=OwnedInstanceDiscardService;
using DiscardRepo=SqliteOwnedInstanceDiscardRepository;
template<class T>const T* discard_at(const std::vector<T>& rows,unsigned slot){const auto found=std::find_if(rows.begin(),rows.end(),[&](const auto& row){return row.slot==slot;});return found==rows.end()?nullptr:&*found;}
std::optional<std::uint8_t> discard_armor(std::uint16_t key){return RecoveredArmorSourceSlots::find(key);}
bool discard_armor_exact(std::uint16_t key,const std::array<std::uint8_t,20>& bytes){return discard_armor(key)&&RecoveredArmorSourceInstance::matches(key,key>=20000?"TEQ":"EQU",bytes);}
struct DiscardHarness {
    Fixture f;SqliteArmorSlotRepository reader;DiscardRepo repo;
    std::optional<Discard::Peer> peer;
    bool allowed=true,protected_zero=false,prepare_fail=false,invalidate_fail=false;unsigned prepare_calls{},invalidate_calls{},late_calls{};
    std::function<void()> late;
    std::optional<std::string> fixed_receipt;
    Discard service;
    DiscardHarness():f(50,true),reader(f.db,discard_armor,discard_armor_exact),
        repo(f.db,reader,discard_armor,discard_armor_exact,[this](auto key)->std::optional<NativeWeaponRecord>{const auto found=f.definitions.find(key);return found==f.definitions.end()?std::nullopt:std::optional(found->second);}),
        peer(Discard::Peer{77,1,f.ids[0],4,3,126,132,true}),
        service(repo,[this](auto id)->std::optional<Discard::Peer>{if(sqlite3_get_autocommit(f.db)==0&&late){++late_calls;late();}return id==77?peer:std::nullopt;},
            [this](auto session,auto source,auto){return session==77&&allowed&&!(source==0&&protected_zero);},
            [this]{return fixed_receipt?*fixed_receipt:f.receipt();},
            [](auto slot,const auto& scalar){require(scalar.item_id==3107,"CUSTOM_TEST unsupported plain refusal");RecoveredInventoryProjection::Metadata raw{};raw[0]=0x23;raw[1]=0x0c;return RecoveredInventoryProjection::encode({slot,scalar.count,raw}).value();},
            [this](auto session){require(session==77&&sqlite3_get_autocommit(f.db)!=0,"Bank invalidation must precede BEGIN");++invalidate_calls;if(invalidate_fail)throw DatabaseError("CUSTOM_TEST bank invalidate failure");},
            [this](const auto&){require(sqlite3_get_autocommit(f.db)!=0,"Reply prepare must precede BEGIN");++prepare_calls;if(prepare_fail)throw DatabaseError("CUSTOM_TEST reply prepare failure");}){
        f.sql(DiscardRepo::schema());
    }
    void owner(unsigned id){peer=Discard::Peer{77,id+1,f.ids[id],4,3,126,132,true};}
    auto load(unsigned id=0){return repo.load(id+1,f.ids[id]);}
    auto handle(std::uint16_t item,std::uint8_t source,std::uint8_t quantity=1){const std::array<RecoveredWorldRecords::Record,3> records{RecoveredWorldRecords::Tick{},RecoveredInventoryDiscard::Request{item,source,quantity},RecoveredWorldRecords::Tick{}};return service.handle(77,records,Discard::Clock::now());}
    auto seed(std::uint16_t key,unsigned slot,std::uint8_t fill=0xa2,unsigned owner=0,unsigned charges=3){
        std::array<std::uint8_t,20> raw{};
        if(discard_armor(key)){
            f.scalar(slot,key,1,9,owner);raw.fill(fill);raw[0]=static_cast<std::uint8_t>(key);raw[1]=static_cast<std::uint8_t>(key>>8);raw[2]=static_cast<std::uint8_t>((fill&0xc0u)|(key>=20000?26u:2u));
            sqlite_detail::Statement add(f.db,"INSERT INTO character_armor_slot_metadata VALUES(?,?,?,9,'CUSTOM_TEST_NOT_NATIVE','NEW0071 original source family opaque fixture',?,?,'CUSTOM-0066')");add.bind_id(1,f.ids[owner]);add.bind(2,slot);add.bind_blob(3,raw);add.bind(4,SqliteArmorSlotRepository::source_sha256);add.bind(5,SqliteArmorSlotRepository::client_sha256);add.done();
        }else {
            raw=f.add(slot,key,fill,11,owner);
            if(key==16055){raw[3]=static_cast<std::uint8_t>((fill&1u)|(charges<<1));sqlite_detail::Statement update(f.db,"UPDATE character_teleport_gem_metadata SET metadata20=? WHERE character_id=? AND slot=?");update.bind_blob(1,raw);update.bind_id(2,f.ids[owner]);update.bind(3,slot);update.done();}
        }
        return raw;
    }
};
void discard_service_whole_instances(){
    // Four actual native EQU/TEQ part identities plus WPN1/TWP25/gem1/10.
    for(unsigned owner=0;owner<2;++owner)for(auto key:{1201u,1001u,1501u,1601u,20201u,20001u,20501u,20601u,1u,19001u,16055u})for(unsigned charges:(key==16055?std::vector<unsigned>{1,10}:std::vector<unsigned>{3})){
        DiscardHarness h;h.owner(owner);const auto raw=h.seed(static_cast<std::uint16_t>(key),29,0xa2,owner,charges);h.seed(1,0,0xb3,owner);h.seed(1,34,0xc1,owner);h.seed(16055,1,0xd4,1-owner);h.f.scalar(5,3107,7,3,owner);
        const auto before=h.load(owner),other=h.load(1-owner);const auto result=h.handle(static_cast<std::uint16_t>(key),29);
        const auto clear=RecoveredInventory::clear_slot(29).value();require(result.committed&&!result.rejected&&result.wire==RecoveredWorldFrame::encode(clear),"NEW0071 whole discard exact prepared41 failed");
        const auto after=h.load(owner);auto expected=before;expected.bag.scalar[29]->item_id=0;expected.bag.scalar[29]->count=0;++expected.bag.scalar[29]->revision;
        std::erase_if(expected.bag.armor,[](const auto& row){return row.slot==29;});std::erase_if(expected.bag.weapons,[](const auto& row){return row.slot==29;});std::erase_if(expected.bag.gems,[](const auto& row){return row.slot==29;});
        require(after==expected&&h.load(1-owner).bag==other.bag&&h.prepare_calls==1&&h.invalidate_calls==1,"NEW0071 destruction touched other49/peer/peripheral or skipped prepare/invalidate");
        const auto receipt=h.f.rows();const auto repeated=h.handle(static_cast<std::uint16_t>(key),29);require(repeated.rejected&&!repeated.committed&&h.f.rows()==receipt,"NEW0071 immediate replay deleted or changed state");
        require(repeated.wire==RecoveredWorldFrame::encode(clear),"NEW0071 empty replay should restore native41 only");
        (void)raw;
    }
    // Same key, different complete20 generations: only selected ordinary0.
    DiscardHarness h;const auto first=h.seed(1,0,0xa1),second=h.seed(1,29,0xb2);const auto before=h.load();require(first!=second,"CUSTOM_TEST samekey tails must differ");require(h.handle(1,0).committed,"NEW0071 ordinary source0 rejected");const auto after=h.load();require(after.bag.scalar[29]==before.bag.scalar[29]&&discard_at(after.bag.weapons,29)&&discard_at(after.bag.weapons,29)->logical20==second,"NEW0071 samekey other generation lost metadata");
}
void discard_service_rejects_and_restores(){
    DiscardHarness h;const auto raw=h.seed(1,0,0xa1);h.seed(1,29,0xb2);h.seed(2,34,0xc3);
    const auto logical=RecoveredInventoryProjection::encode({0,1,raw}).value();const auto expected_wire=RecoveredWorldFrame::encode(logical);
    for(auto q:{0u,2u,127u,128u,255u}){const auto before=h.f.rows();const auto result=h.handle(1,0,static_cast<std::uint8_t>(q));require(result.rejected&&!result.committed&&result.wire==expected_wire&&h.f.rows()==before&&h.invalidate_calls==0,"NEW0071 invalid quantity did not preserve full20 or invalidated bank");}
    {const auto before=h.f.rows();const auto result=h.handle(2,0);require(result.rejected&&result.wire==expected_wire&&h.f.rows()==before,"NEW0071 wrongkey restored wrong instance");}
    for(auto slot:{30u,34u,42u,43u,49u,255u}){const auto before=h.f.rows();const auto result=h.handle(1,static_cast<std::uint8_t>(slot));require(result.rejected&&!result.committed&&result.wire.empty()&&h.f.rows()==before,"NEW0071 equipped/special source authority widened");}
    h.protected_zero=true;auto before=h.f.rows();require(h.handle(1,0).rejected&&h.f.rows()==before&&h.invalidate_calls==0,"NEW0071 protected guide0 accepted");h.protected_zero=false;
    h.allowed=false;require(h.handle(1,29).rejected&&h.f.rows()==before,"NEW0071 active trade/lease denial accepted");h.allowed=true;
    const std::array<RecoveredWorldRecords::Record,2> duplicate{RecoveredInventoryDiscard::Request{1,0,1},RecoveredInventoryDiscard::Request{1,29,1}};auto result=h.service.handle(77,duplicate,Discard::Clock::now());require(result.rejected&&result.wire.empty()&&h.f.rows()==before,"NEW0071 duplicate native27 batch destroyed item");
    const std::array<RecoveredWorldRecords::Record,2> mixed{RecoveredInventoryDiscard::Request{1,0,1},RecoveredInventoryMoveRequest::Request{0,29}};result=h.service.handle(77,mixed,Discard::Clock::now());require(result.rejected&&h.f.rows()==before,"NEW0071 mixed mutation destroyed item");
    const auto peer=h.peer;for(unsigned change=0;change<3;++change){h.peer=peer;if(change==0)h.peer->ready=false;else if(change==1)h.peer->account=2;else h.peer->session=78;result=h.handle(1,0);require(result.rejected&&result.wire.empty()&&h.f.rows()==before,"NEW0071 mismatched/notready owner leaked full20");}h.peer=peer;
}
void discard_service_late_and_prepare(){
    for(unsigned change=0;change<7;++change){DiscardHarness h;h.seed(1,0);h.seed(19001,29);const auto before=h.f.rows();const auto peer=h.peer;h.late=[&]{switch(change){case 0:h.peer->ready=false;break;case 1:++h.peer->account;break;case 2:++h.peer->character;break;case 3:++h.peer->session;break;case 4:++h.peer->area;break;case 5:++h.peer->scene;break;case 6:h.allowed=false;break;}};const auto result=h.handle(1,0);h.late={};h.peer=peer;h.allowed=true;require(h.late_calls>0&&result.rejected&&!result.committed&&h.f.rows()==before,"NEW0071 true transactional late lease check failed rollback");}
    for(unsigned failure=0;failure<2;++failure){DiscardHarness h;h.seed(1,0);const auto before=h.f.rows();h.prepare_fail=failure==0;h.invalidate_fail=failure==1;const auto result=h.handle(1,0);require(result.rejected&&!result.committed&&h.f.rows()==before,"NEW0071 preBEGIN prepare/invalidate failure mutated SQL");require(h.invalidate_calls==(failure==0?0u:1u),"NEW0071 bank invalidation ordering wrong");}
    DiscardHarness h;h.seed(1,0);h.fixed_receipt=std::string(64,'a');require(h.handle(1,0).committed,"NEW0071 receipt seed failed");h.seed(1,29);const auto before=h.f.rows();require(h.handle(1,29).rejected&&h.f.rows()==before,"NEW0071 duplicate receipt destroyed second instance");
}
void discard_service_absent_economy(){
    DiscardHarness h;h.f.sql("DELETE FROM character_bank_item_slots");h.seed(1,0);const auto before=h.load();const auto result=h.handle(1,0);require(result.committed&&h.load().bag.scalar[0]->count==0,"NEW0071 required unrelated bank capacity");require(dump(h.f.db,"SELECT * FROM character_bank_item_slots").empty(),"NEW0071 provisioned unrelated bank capacity");
    require(before.bag.scalar[49]==h.load().bag.scalar[49],"NEW0071 protected49 changed");
}
}
int main(){try{discard_service_whole_instances();discard_service_rejects_and_restores();discard_service_late_and_prepare();discard_service_absent_economy();std::cout<<"PASS CUSTOM0071 whole typed27 service: both owners EQU/TEQ fourparts WPN/TWP/gem1/10, exact41/full20 refusal, ordinary0/29 samekey tails, malformed/mixed/equipped/guide/trade/replay, actual transaction late scene/lease rollback, preBEGIN invalidate, no bank capacity grant\n";return 0;}catch(const std::exception& error){std::cerr<<error.what()<<'\n';return 1;}}
