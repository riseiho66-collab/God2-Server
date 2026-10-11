#include "handlers/OwnedGuildPanelService.h"
#include "protocol/RecoveredWorldRecords.h"
#include "db/DbTypes.h"
#include <iostream>
#include <stdexcept>
using namespace god2;
namespace {
unsigned checks=0;
void check(bool value){++checks;if(!value)throw std::runtime_error("Panel check "+std::to_string(checks));}
GuildRosterMember member(std::uint64_t id,std::string name) {
    GuildRosterMember m{};m.character_id=id;m.account_id=id;m.membership_revision=1;
    m.profile[29]=2;m.name_utf8=name;m.name_bytes.assign(name.begin(),name.end());
    std::copy(name.begin(),name.end(),m.profile.begin());
    CharacterRoleSnapshot r{};r.logical[0]=0x22;r.logical[1]=35;r.logical[17]=200;
    r.revision=1;r.design_id="CUSTOM-0013";m.role=r;return m;
}
}
int main() {try {
    for(unsigned slot=0;slot<50;++slot) {
        const std::array<std::uint8_t,2> logical{0x73,static_cast<std::uint8_t>(slot)};
        auto request=RecoveredGuildLeave::decode(logical);check(request && request->slot==slot);
    }
    check(!RecoveredGuildLeave::decode(std::array<std::uint8_t,1>{0x73}));
    check(!RecoveredGuildLeave::decode(std::array<std::uint8_t,3>{0x73,0,0}));
    check(!RecoveredGuildLeave::decode(std::array<std::uint8_t,2>{0x73,50}));
    check(!RecoveredWorldRecords::decode(std::array<std::uint8_t,3>{0x73,0,0x73}));
    const auto batch=RecoveredWorldRecords::decode(std::array<std::uint8_t,6>{0x73,0,0x30,0,0xb8,0});
    check(batch && batch->size()==3 && std::get<RecoveredGuildLeave::Request>((*batch)[0]).slot==0 &&
        std::holds_alternative<RecoveredWorldRecords::Tick>((*batch)[1]) &&
        std::holds_alternative<RecoveredGuildRoster::PanelReady>((*batch)[2]));
    const std::vector<std::uint8_t> first_reply{0x92,1},second_reply{0x92,0};
    auto replies=RecoveredWorldFrame::encode(first_reply);
    const auto second_wire=RecoveredWorldFrame::encode(second_reply);
    replies.insert(replies.end(),second_wire.begin(),second_wire.end());
    auto parsed=OwnedGuildPanelService::prefix_replies(replies);
    check(parsed && *parsed==std::vector<std::vector<std::uint8_t>>({first_reply,second_reply}));
    replies.pop_back();check(!OwnedGuildPanelService::prefix_replies(replies));
    check(OwnedGuildPanelService::prefix_replies({})->empty());
    check(OwnedGuildPanelService::custom_help_entry({0x087b}));
    check(!OwnedGuildPanelService::custom_help_entry({0x1000087b}));
    check(!OwnedGuildPanelService::custom_help_entry({0x14f8}));
    check(!OwnedGuildPanelHeader::readonly_members(0));check(!OwnedGuildPanelHeader::readonly_members(51));
    for(auto count:{std::size_t{1},std::size_t{50}}) {
        auto h=OwnedGuildPanelHeader::readonly_members(count);check(h && h->size()==53);
        check((*h)[0]==0x8e && (*h)[14]==6 && (*h)[20]==count && (*h)[24]==50);
        for(std::size_t i=1;i<h->size();++i)if(i!=14 && i!=20 && i!=24)check((*h)[i]==0);
    }
    OwnedGuildRosterService::Peer peer{10,1,1,"self",true,false,0};
    std::optional<StoredGuildRoster> roster{StoredGuildRoster{1,1,{}, {member(1,"self"),member(2,"other")}}};
    roster->membership.guild_id=1;roster->membership.guild_revision=1;roster->membership.membership_revision=1;
    roster->membership.name_utf8="guild";
    std::set<std::uint32_t> online{1};
    OwnedGuildRosterService cache([&](auto id)->std::optional<OwnedGuildRosterService::Peer>{if(id==peer.session)return peer;return {};},
        [&](auto a,auto c){check(a==1 && c==1);return roster;},[&]{return online;});
    unsigned leaves=0;bool fail_storage=false;
    OwnedGuildPanelService panel(cache,[&](auto account,auto character,const auto& expected) {
        check(account==1 && character==1 && roster && expected==roster->membership);
        if(fail_storage)throw DatabaseError("Injected transactional failure");
        ++leaves;roster.reset();
    });
    check(!panel.leave(10,{0}) && !panel.leave(99,{0}) && leaves==0);
    check(!panel.prepare(99));
    auto initial=panel.prepare(10);check(initial && initial->logical.size()==97 && panel.current(*initial));
    check(initial->logical[44]==0x8e && initial->logical[64]==2);
    panel.published(*initial);
    auto leave_lease=panel.prepare_leave(10,{0});check(leave_lease.has_value());
    check(!panel.leave(10,{1}) && leaves==0);
    auto reopen=panel.prepare(10);check(reopen && reopen->logical.size()==53 && reopen->logical[0]==0x8e);
    roster->members[1].role->logical[1]=45;roster->members[1].role->revision++;
    check(!panel.current(*initial));check(!panel.current(*reopen));
    check(!panel.leave(10,{0}) && leaves==0);
    auto fresh=panel.prepare(10);check(fresh && fresh->logical.size()==99);panel.published(*fresh);
    // A refresh in the same batch cannot renew a captured stale command.
    check(!panel.leave(*leave_lease,{0}) && leaves==0);
    // Incomplete/foreign/nonmember snapshots do not produce a fake empty panel.
    roster->members[1].role.reset();check(!panel.prepare(10));
    roster->members[1]=member(2,"other");roster->requester_account=99;check(!panel.prepare(10));
    roster->requester_account=1;peer.ready=false;check(!panel.prepare(10));peer.ready=true;
    auto ready=panel.prepare(10);check(ready.has_value());panel.published(*ready);
    fail_storage=true;check(!panel.leave(10,{0}) && roster && leaves==0);fail_storage=false;
    check(panel.leave(10,{0}) && !roster && leaves==1);
    check(!panel.leave(10,{0}) && leaves==1); // duplicate confirmation never mutates twice
    auto removed=cache.prepare(10);check(removed && removed->logical==std::vector<std::uint8_t>({0x92,1,0x92,0}));
    roster.reset();check(!panel.prepare(10));
    std::cout<<"Passed "<<checks<<" panel checks\n";return 0;
}catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}}
