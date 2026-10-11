#include "handlers/OwnedTeleportGemOffer.h"
#include <iostream>
#include <stdexcept>

using Service=god2::OwnedTeleportGemOffer;
using Records=god2::RecoveredWorldRecords;
using Item=god2::StoredTeleportGemSlot;
static unsigned checks=0;
static void check(bool value) { ++checks;if(!value)throw std::runtime_error("OwnedTeleportGemOffer failure"); }
static Service::Operation op(std::initializer_list<Records::Record> records) {
    const auto value=Service::preflight(std::span<const Records::Record>(records.begin(),records.size()));
    check(value.has_value());return *value;
}
static Item item() {
    Item value{};value.slot=12;value.item_id=16055;value.count=1;value.revision=9;
    value.metadata20={0xb7,0x3e,8,20};value.metadata_present=true;
    value.origin="CUSTOM_TEST_NOT_NATIVE";value.provenance="owned offer unit fixture";
    return value;
}
int main() {
    try {
        const Service::Time now=Service::Time{}+std::chrono::seconds(100);
        const Service::Owner owner{7,3,4,true,false,false,god2::RecoveredPosition{2,0,476,209,11}};
        const auto i=item();
        const auto open=op({god2::RecoveredInventoryItemRequest::Request{16055,12,0xff}});
        const auto shortcut=op({god2::RecoveredTargetItemRequest::Request{4,16055,12,0xee}});
        const auto select=op({god2::RecoveredTeleport::Selection{0x99,16055,5,0xaa}});
        const auto cancel=op({god2::RecoveredQuestClose::Request{4,0xffff}});
        Service service;
        const auto menu=service.open(owner,open,i,now);check(menu.has_value());
        const auto decoded=god2::RecoveredTeleport::decode_menu(*menu);
        check(decoded && decoded->context==16055 && decoded->message_id==280 && decoded->count_flags==0x81 &&
              decoded->minutes==0 && decoded->level==10 && decoded->destinations[0].id==5 &&
              decoded->destinations[0].displayed_cost==0);
        check(service.pending_slot(7)==12);
        const auto ready=service.select(owner,select,i,now+std::chrono::seconds(1));check(ready.has_value());
        check(ready->expected_item==i && ready->expected_position==*owner.position);
        check(service.pending_slot(7).has_value()); // prepare is not a commit
        check(!service.committed(7,ready->token+1));
        check(service.committed(7,ready->token));check(!service.select(owner,select,i,now));
        check(!service.committed(7,ready->token));
        check(service.open(owner,shortcut,i,now).has_value());
        auto wrong=shortcut;wrong.target=5;
        check(!service.open(owner,wrong,i,now));
        auto foreign=owner;foreign.account_id=99;
        check(!service.select(foreign,select,i,now));check(!service.cancel(foreign,cancel,now));
        check(service.pending_slot(7).has_value());
        foreign=owner;foreign.character_id=5;
        check(!service.select(foreign,select,i,now));
        wrong=cancel;wrong.target=5;check(!service.cancel(owner,wrong,now));
        check(service.cancel(owner,cancel,now));check(!service.pending_slot(7));
        check(!service.cancel(owner,cancel,now));

        for(unsigned changed=0;changed<8;++changed) {
            auto unavailable=owner;
            switch(changed) {
            case 0:unavailable.ready=false;break;
            case 1:unavailable.in_battle=true;break;
            case 2:unavailable.transfer_pending=true;break;
            case 3:unavailable.position.reset();break;
            case 4:unavailable.position->area=4;break;
            case 5:unavailable.position->scene=4;break;
            case 6:unavailable.position->revision=0;break;
            default:unavailable.character_id=65536;break;
            }
            check(!service.open(unavailable,open,i,now));
        }
        for(unsigned changed=0;changed<8;++changed) {
            auto stale=i;
            switch(changed) {
            case 0:stale.revision++;break;
            case 1:stale.count=2;break;
            case 2:stale.metadata20[19]^=1;break;
            case 3:stale.slot=13;break;
            case 4:stale.metadata_present=false;break;
            case 5:stale.origin="CUSTOM_DESIGNED";break;
            case 6:stale.provenance="other";break;
            default:stale.metadata20[3]=18;break;
            }
            check(service.open(owner,open,i,now).has_value());
            check(!service.select(owner,select,stale,now));check(!service.pending_slot(7));
        }
        for(unsigned changed=0;changed<2;++changed) {
            auto moved=owner;if(changed)moved.position->revision++;else moved.position->x++;
            check(service.open(owner,open,i,now).has_value());
            check(!service.select(moved,select,i,now));check(!service.pending_slot(7));
        }
        for(auto invalid_time:{now-std::chrono::seconds(1),now+Service::lifetime}) {
            check(service.open(owner,open,i,now).has_value());
            check(!service.select(owner,select,i,invalid_time));check(!service.pending_slot(7));
        }
        check(service.open(owner,open,i,now).has_value());
        check(service.select(owner,select,i,now+Service::lifetime-std::chrono::milliseconds(1)).has_value());
        const auto older=service.select(owner,select,i,now);check(older.has_value());
        check(service.open(owner,open,i,now).has_value());check(!service.committed(7,older->token));
        check(service.pending_slot(7).has_value());service.forget(7);check(!service.pending_slot(7));
        const auto cleared=god2::RecoveredTeleportGem::with_charges(i.metadata20,0);
        auto zero=i;zero.metadata20=*cleared;check(!service.open(owner,open,zero,now));

        const Records::Record tick=Records::Tick{};
        const Records::Record control=Records::ClientControl1F{};
        const Records::Record request=god2::RecoveredInventoryItemRequest::Request{16055,12,0};
        const Records::Record targeted=god2::RecoveredTargetItemRequest::Request{4,16055,12,0};
        const Records::Record chosen=god2::RecoveredTeleport::Selection{0x99,16055,5,0};
        const Records::Record close=god2::RecoveredQuestClose::Request{4,0};
        const Records::Record other=god2::RecoveredRoleText::Request{};
        for(const auto& good:std::vector<std::vector<Records::Record>>{
            {request},{tick,request,tick},{request,control},{request,tick,control,tick},
            {targeted,tick},{chosen,tick},{close,tick}})check(Service::preflight(good).has_value());
        for(const auto& bad:std::vector<std::vector<Records::Record>>{
            {},{tick},{request,request},{request,other},{other,request},{control,request},
            {request,control,control},{targeted,control},{chosen,control},{close,control},
            {god2::RecoveredInventoryItemRequest::Request{16055,30,0}},
            {god2::RecoveredInventoryItemRequest::Request{16056,12,0}},
            {god2::RecoveredTeleport::Selection{0xa9,16055,5,0}},
            {god2::RecoveredTeleport::Selection{0x99,16055,4,0}},
            {god2::RecoveredTeleport::Selection{0x99,16054,5,0}}})check(!Service::preflight(bad));
        const std::vector<Records::Record> close_batch{close},open_batch{request},mixed{request,other};
        check(!service.claims(7,close_batch));check(service.claims(7,open_batch));check(service.claims(7,mixed));
        check(service.open(owner,open,i,now).has_value());check(service.claims(7,close_batch));
        check(!service.claims(8,close_batch));
        std::cout << "PASS " << checks << " checks\n";
    } catch(const std::exception& error) {
        std::cerr<<error.what()<<'\n';return 1;
    }
}
