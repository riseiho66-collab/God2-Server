// NEW actual storage/lease/native projection gate. Frozen0068 fixture supplies
// real complete1259 source definitions, historical schemas and isolated owners.
#define main included_owned_foreign_bank_fixture_main
#include "storage_owned_foreign_bank_0068.cpp"
#undef main
#include "handlers/OwnedInstanceTradeService.h"

namespace {
using InstanceService=OwnedInstanceTradeService;
using InstanceRepo=SqliteOwnedInstanceTradeRepository;
using TradeKind=RecoveredTrade::Kind;
using TradeRequest=RecoveredTrade::Request;
struct InstanceServiceFixture {
    Fixture f;InstanceRepo repo;
    std::map<std::uint64_t,InstanceService::Peer> peers;
    bool fail_prepare_once=false,late_lease=false;unsigned prepare_failures{},late_checks{};
    std::optional<std::string> fixed_receipt;
    InstanceService service;
    InstanceServiceFixture():f(50),repo(f.db,armor,armor_exact,[this](auto id)->std::optional<NativeWeaponRecord>{const auto at=f.definitions.find(id);return at==f.definitions.end()?std::nullopt:std::optional(at->second);},[](auto id){return id==3107;}),
        service(repo,[this](auto session)->std::optional<InstanceService::Peer>{
            if(late_lease&&sqlite3_get_autocommit(f.db)==0){++late_checks;peers.at(22).scene=9;}
            const auto at=peers.find(session);return at==peers.end()?std::nullopt:std::optional(at->second);},
            [this](auto character)->std::optional<InstanceService::Peer>{for(const auto& [id,peer]:peers)if(peer.character==character)return peer;return {};},
            [](const auto&,const auto& peer){RecoveredTrade::Name name{};name[0]=static_cast<std::uint8_t>('A'+peer.character);return name;},
            [](const auto& scalar){return scalar.item_id==3107&&scalar.count&&scalar.source_sha256==SqliteArmorSlotRepository::source_sha256;},
            [this](auto slot,const auto& scalar){
                if(fail_prepare_once){fail_prepare_once=false;++prepare_failures;throw DatabaseError("CUSTOM_TEST genuine prepare projection failure");}
                RecoveredInventoryProjection::Metadata bytes{};bytes[0]=static_cast<std::uint8_t>(scalar.item_id);bytes[1]=static_cast<std::uint8_t>(scalar.item_id>>8);
                return RecoveredInventoryProjection::encode({slot,scalar.count,bytes}).value();},
            [this]{return fixed_receipt?*fixed_receipt:f.receipt();}){
        f.install();f.sql(InstanceRepo::schema());SqliteTradeRepository wallets(f.db);wallets.install_schema();
        for(unsigned owner=0;owner<2;++owner){wallets.provision_wallet(owner+1,f.ids[owner]);peers.emplace(owner?22:11,InstanceService::Peer{owner?22u:11u,owner+1,f.ids[owner],4,3,true});}
        f.sql("UPDATE character_trade_wallets SET amount=1000,revision=1");
    }
    static auto now(){return InstanceService::Clock::now();}
    auto load(unsigned owner=0){return repo.load(owner+1,f.ids[owner]);}
    auto act(unsigned owner,std::initializer_list<TradeRequest> requests){const std::vector copied(requests);return service.handle(owner?22:11,copied,now());}
    auto open(unsigned owner=0){TradeRequest request{TradeKind::Open};request.target=static_cast<std::uint16_t>(f.ids[1-owner]);return act(owner,{request});}
    auto offer(unsigned owner,unsigned slot,unsigned count=1){const auto saved=load(owner);TradeRequest request{TradeKind::OfferItem};request.target=static_cast<std::uint16_t>(f.ids[1-owner]);request.slot=static_cast<std::uint8_t>(slot);request.quantity=static_cast<std::uint8_t>(count);request.item=saved.bag.scalar[slot]->item_id;return act(owner,{request});}
    auto confirm(unsigned owner,unsigned money=0){TradeRequest request{TradeKind::OfferMoney};request.target=static_cast<std::uint16_t>(f.ids[1-owner]);request.money=money;return act(owner,{request,TradeRequest{TradeKind::Confirm}});}
};
std::array<std::uint8_t,20> expected_instance_bytes(const InstanceRepo::Snapshot& saved,unsigned slot){
    for(const auto& value:saved.bag.armor)if(value.slot==slot)return value.logical20;
    for(const auto& value:saved.bag.weapons)if(value.slot==slot)return value.logical20;
    for(const auto& value:saved.bag.gems)if(value.slot==slot)return value.logical20;
    std::array<std::uint8_t,20> bytes{};bytes[0]=static_cast<std::uint8_t>(saved.bag.scalar[slot]->item_id);bytes[1]=static_cast<std::uint8_t>(saved.bag.scalar[slot]->item_id>>8);return bytes;
}
std::vector<std::uint8_t> expected_owner_reply(const InstanceRepo::Snapshot& saved,bool rollback){
    auto bytes=rollback?RecoveredTrade::rollback_close():RecoveredTrade::close_without_refund();
    for(std::uint8_t slot=0;slot<30;++slot){const auto& scalar=*saved.bag.scalar[slot];const auto metadata=scalar.count?expected_instance_bytes(saved,slot):std::array<std::uint8_t,20>{};const auto logical=RecoveredInventoryProjection::encode({slot,scalar.count,metadata}).value();bytes.insert(bytes.end(),logical.begin(),logical.end());}
    const auto wallet=RecoveredTrade::wallet(saved.wallet.amount);bytes.insert(bytes.end(),wallet.begin(),wallet.end());return bytes;
}
void exact_restore(const InstanceService::Deliveries& deliveries,InstanceServiceFixture& h){for(unsigned owner=0;owner<2;++owner){const auto id=owner?22u:11u;require(deliveries.contains(id)&&deliveries.at(id)==expected_owner_reply(h.load(owner),true),"Owned trade rollback/cancel did not return exact30 authoritative slots and absolute wallet");}}
void protected_equal(const ArmorSnapshot& before,const ArmorSnapshot& after){
    for(unsigned slot=30;slot<50;++slot)require(before.scalar[slot]==after.scalar[slot],"Owned trade changed protected/equipped scalar");
    const auto filtered=[](const auto& rows){auto values=rows;std::erase_if(values,[](const auto& row){return row.slot<30;});return values;};
    require(filtered(before.armor)==filtered(after.armor)&&filtered(before.weapons)==filtered(after.weapons)&&filtered(before.gems)==filtered(after.gems),"Owned trade changed protected/equipped full20");
}
void native_peer50(const InstanceService::Result& result,std::uint64_t peer,std::uint8_t index,std::uint8_t quantity,const std::array<std::uint8_t,20>& metadata){
    RecoveredTrade::Item item{};item[0]=quantity;item[1]=index;std::copy(metadata.begin(),metadata.end(),item.begin()+4);
    require(!result.rejected&&!result.committed&&result.deliveries.size()==1&&result.deliveries.at(peer)==RecoveredTrade::peer_item(item).value(),"Peer50 did not preserve exact full20/quantity/offerindex and reserved bytes");
}
void seed_mixed(InstanceServiceFixture& h){for(unsigned owner=0;owner<2;++owner){h.f.add_armor(0,1001,owner);h.f.add(1,1,owner?0xb2:0xa1,7,owner);h.f.add(2,19001,owner?0xd4:0xc3,9,owner);h.f.add(3,16055,owner?0xf6:0xe5,11,owner);h.f.scalar(4,3107,owner?9:7,13,owner);h.f.add_armor(30,1201,owner);h.f.add(34,2,owner?0x81:0xc2,17,owner);}}
void two_owner_mixed_settlement_and_replay(){
    InstanceServiceFixture h;seed_mixed(h);const std::array before{h.load(0),h.load(1)};const auto stored=h.f.rows();h.fixed_receipt=std::string(64,'a');
    const auto opened=h.open();require(!opened.rejected&&opened.deliveries.size()==2&&h.service.active(11)&&h.service.active(22),"Owned trade did not open both native peers");
    for(unsigned owner=0;owner<2;++owner)for(unsigned slot=0;slot<5;++slot){const auto quantity=slot==4?(owner?3u:2u):1u;native_peer50(h.offer(owner,slot,quantity),owner?11:22,static_cast<std::uint8_t>(slot),static_cast<std::uint8_t>(quantity),expected_instance_bytes(before[owner],slot));require(h.f.rows()==stored,"Transient full20 offer mutated storage");}
    require(!h.confirm(0,100).committed&&h.f.rows()==stored,"Single owned trade confirmation mutated storage");const auto result=h.confirm(1,40);require(result.committed&&!result.rejected&&!h.service.active(11)&&!h.service.active(22),"Owned trade both confirmations did not settle");
    const std::array after{h.load(0),h.load(1)};
    for(unsigned owner=0;owner<2;++owner){for(unsigned slot=0;slot<4;++slot)require(expected_instance_bytes(after[owner],slot)==expected_instance_bytes(before[1-owner],slot),"Mixed armor/WPN/TWP/Gem bidirectional full20 custody failed");protected_equal(before[owner].bag,after[owner].bag);const auto suffix=expected_owner_reply(after[owner],false);const auto& actual=result.deliveries.at(owner?22:11);require(actual.size()>=suffix.size()&&std::equal(suffix.rbegin(),suffix.rend(),actual.rbegin()),"Owned trade durable reply not exact current full20 and wallet");}
    require(after[0].wallet.amount==940&&after[1].wallet.amount==1060&&after[0].bag.scalar[4]->count==5&&after[1].bag.scalar[4]->count==6&&after[0].bag.scalar[5]->count==3&&after[1].bag.scalar[5]->count==2,"Owned trade MED partial/money conservation failed");
    require(expected_instance_bytes(before[0],1)!=expected_instance_bytes(before[1],1)&&after[0].bag.scalar[1]->item_id==1&&after[1].bag.scalar[1]->item_id==1,"Same-ID distinct-tail fixture not exercised");
    const auto committed=h.f.rows();h.open(1);h.offer(1,1);h.offer(0,1);h.confirm(1);const auto replay=h.confirm(0);require(replay.rejected&&!replay.committed&&h.f.rows()==committed&&!h.service.active(11),"Owned service replay receipt committed either owner");exact_restore(replay.deliveries,h);
}
void cancel_timeout_disconnect_and_mutated_peer(){
    InstanceServiceFixture h;seed_mixed(h);const auto initial=h.f.rows();h.open();h.offer(0,1);h.offer(1,3);const auto cancel=h.act(1,{TradeRequest{TradeKind::Cancel}});require(!cancel.committed&&!cancel.rejected&&h.f.rows()==initial,"Owned trade cancel wrote storage");exact_restore(cancel.deliveries,h);
    h.open();h.offer(0,2);const auto timed=h.service.refresh(InstanceService::Clock::now()+std::chrono::seconds(61));require(!h.service.active(11)&&h.f.rows()==initial,"Owned trade timeout changed durable instances");exact_restore(timed,h);
    h.open();h.offer(0,0);h.peers.erase(22);const auto disconnected=h.service.disconnect(22);require(disconnected.size()==1&&disconnected.at(11)==expected_owner_reply(h.load(),true)&&!h.service.active(11)&&h.f.rows()==initial,"Owned trade disconnect retained context or lost surviving owner full20");
    h.peers.emplace(22,InstanceService::Peer{22,2,h.f.ids[1],4,3,true});h.open();h.offer(0,1);h.peers.at(22).scene=4;const auto changed=h.confirm(0);require(changed.rejected&&!changed.committed&&!h.service.active(22)&&h.f.rows()==initial,"Mutated scene peer settled full20 trade");exact_restore(changed.deliveries,h);h.peers.at(22).scene=3;
    h.open();h.offer(0,1);h.f.scalar(20,3107,1,3,1);const auto authorized_new_save=h.f.rows();const auto stale=h.confirm(0);require(stale.rejected&&!stale.committed&&h.f.rows()==authorized_new_save,"Stale offer overwrote independently changed peer save");exact_restore(stale.deliveries,h);
}
void preparation_latelease_and_fullbag_refusal(){
    InstanceServiceFixture h;seed_mixed(h);h.open();h.offer(0,1);h.offer(1,4,2);h.confirm(0);auto rows=h.f.rows();h.fail_prepare_once=true;const auto prepared=h.confirm(1);require(prepared.rejected&&!prepared.committed&&h.prepare_failures==1&&h.f.rows()==rows&&!h.service.active(11),"Actual two-reply preparation failure wrote instances or retained context");exact_restore(prepared.deliveries,h);
    h.open();h.offer(0,1);h.offer(1,1);h.confirm(0);rows=h.f.rows();h.late_lease=true;const auto late=h.confirm(1);h.late_lease=false;require(late.rejected&&!late.committed&&h.late_checks>0&&h.f.rows()==rows&&!h.service.active(11),"Actual preCOMMIT live scene check was skipped or failed rollback");exact_restore(late.deliveries,h);h.peers.at(22).scene=3;
    for(unsigned slot=0;slot<30;++slot){if(slot<4)continue;h.f.scalar(slot,3107,1,20,1);}h.open();h.offer(0,1);h.confirm(0);rows=h.f.rows();const auto full=h.confirm(1);require(full.rejected&&!full.committed&&h.f.rows()==rows&&!h.service.active(22),"Owned trade fullbag refused transfer changed either owner");exact_restore(full.deliveries,h);
}
void empty_tail_and_offer_rules(){
    InstanceServiceFixture h;h.f.add(0,1,0xb2,7,1);std::array<std::uint8_t,20> empty{};empty[2]=0xc1;empty[19]=0x7f;
    sqlite_detail::Statement insert(h.f.db,"INSERT INTO character_weapon_slot_metadata VALUES(?,?,?,1,'EMPTY_SLOT_POLICY','CUSTOM_TEST empty-tail',?,?,'CUSTOM-0046')");insert.bind_id(1,h.f.ids[0]);insert.bind(2,0);insert.bind_blob(3,empty);insert.bind(4,SqliteWeaponSlotRepository::source_sha256);insert.bind(5,SqliteWeaponSlotRepository::client_sha256);insert.done();
    const auto saved=h.f.rows();h.open();h.offer(1,0);const auto cancel=h.act(0,{TradeRequest{TradeKind::Cancel}});require(h.f.rows()==saved,"Empty-tail opening/cancellation mutated stored opaque20");exact_restore(cancel.deliveries,h);const auto clear=RecoveredInventory::clear_slot(0).value();require(std::equal(clear.begin(),clear.end(),cancel.deliveries.at(11).begin()+3),"Empty ordinarycell did not use native5byte41 clear (inactive tail is not zeroed)");
    h.open();h.offer(1,0);h.confirm(0);const auto moved=h.confirm(1);require(moved.committed&&expected_instance_bytes(h.load(),0)!=expected_instance_bytes(h.load(1),0),"Empty-tail transfer did not install a new whole instance");
    const auto installed=h.load();require(installed.bag.scalar[0]->count==1&&std::any_of(installed.bag.weapons.begin(),installed.bag.weapons.end(),[](const auto& row){return row.slot==0&&row.origin=="CUSTOM_TEST_NOT_NATIVE"&&row.logical20[19]==0xb2;}),"Real incoming instance did not replace EMPTY_SLOT_POLICY overlay");
    h.open();auto wrong=TradeRequest{TradeKind::OfferItem};wrong.target=static_cast<std::uint16_t>(h.f.ids[1]);wrong.slot=0;wrong.item=1;wrong.quantity=2;const auto state=h.f.rows();require(h.act(0,{wrong}).rejected&&h.f.rows()==state,"Whole-instance quantity2 accepted");
    h.open();h.offer(0,0);require(h.offer(0,0).rejected&&h.f.rows()==state,"Duplicate instance source offered twice");
    h.open();require(h.act(0,{TradeRequest{TradeKind::Confirm},TradeRequest{TradeKind::Confirm}}).rejected&&h.f.rows()==state,"Non-native coalesced confirm batch accepted");
    for(unsigned slot=1;slot<9;++slot)h.f.scalar(slot,3107,1,3);
    h.open();const auto capacity_state=h.f.rows();h.offer(0,0);for(unsigned slot=1;slot<8;++slot)require(!h.offer(0,slot).rejected,"Valid first8 native offer entries refused");require(h.offer(0,8).rejected&&h.f.rows()==capacity_state&&!h.service.active(11),"Ninth native offer exceeded8 cap or changed durable state");
}
}
int main(){try{two_owner_mixed_settlement_and_replay();cancel_timeout_disconnect_and_mutated_peer();preparation_latelease_and_fullbag_refusal();empty_tail_and_offer_rules();std::cout<<"PASS CUSTOM0069 owned instance trade service: real two-owner armor/WPN/TWP/Gem full20+MED/money; exact peer50 prefix; same-ID distinct-tail custody; pure prepared replies; original60s custom policy/cancel/disconnect; stale peer, replay, actual prepare/latelease/fullbag rollback; native5byte empty clear and stored opaque-tail preservation; no live activation/grants/stat claims\n";return 0;}catch(const std::exception& error){std::cerr<<error.what()<<'\n';return 1;}}
