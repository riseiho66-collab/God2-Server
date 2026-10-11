#include "handlers/OwnedGuildRosterService.h"
#include "protocol/RecoveredWorldRecords.h"
#include <iostream>
#include <stdexcept>
using namespace god2;
namespace {
unsigned checks=0;
void check(bool value){++checks;if(!value)throw std::runtime_error("Guild roster check failed: "+std::to_string(checks));}
void emit(const char* name,const std::vector<std::uint8_t>& logical) {
    std::cout<<"NATIVE_CASE "<<name<<" ";
    for(auto byte:logical)std::cout<<"0123456789abcdef"[byte>>4]<<"0123456789abcdef"[byte&15];
    std::cout<<'\n';
}
GuildRosterMember member(std::uint64_t id,std::string name,std::uint8_t level=35) {
    GuildRosterMember result{};result.character_id=id;result.account_id=id;
    result.membership_revision=1;result.profile[29]=2;result.name_utf8=name;
    result.name_bytes.assign(name.begin(),name.end());
    std::copy(name.begin(),name.end(),result.profile.begin());
    CharacterRoleSnapshot role{};role.logical[0]=0x22;role.logical[1]=level;
    role.logical[17]=200;role.revision=1;role.design_id="CUSTOM-0013";result.role=role;
    return result;
}
struct Fixture {
    OwnedGuildRosterService::Peer peer{10,1,1,"self",true,false,0};
    std::optional<StoredGuildRoster> roster;
    std::set<std::uint32_t> online{1};
    int reads=0;bool change_on_second=false;
    Fixture() {
        roster=StoredGuildRoster{1,1,StoredGuildMembership{}, {member(1,"self"),member(2,"other")}};
        roster->membership.guild_id=1;roster->membership.guild_revision=1;
        roster->membership.membership_revision=1;roster->membership.name_utf8="guild";
    }
    OwnedGuildRosterService service() {
        return OwnedGuildRosterService([&](auto session)->std::optional<OwnedGuildRosterService::Peer>{
            if(session!=peer.session)return {};return peer;
        },[&](auto account,auto character){
            if(account!=peer.account || character!=peer.character)throw std::runtime_error("Foreign owner");
            if(change_on_second && ++reads==2)roster->members[1].name_utf8="changed";
            return roster;
        },[&]{return online;});
    }
};
}
int main() {
    try {
        check(RecoveredGuildRoster::panel_ready(std::array<std::uint8_t,2>{0xb8,0}).has_value());
        check(!RecoveredGuildRoster::panel_ready(std::array<std::uint8_t,2>{0xb8,1}));
        const auto batch=RecoveredWorldRecords::decode(std::array<std::uint8_t,4>{0xb8,0,0x30,0});
        check(batch && batch->size()==2 && std::holds_alternative<RecoveredGuildRoster::PanelReady>((*batch)[0]));
        check(!RecoveredWorldRecords::decode(std::array<std::uint8_t,1>{0xb8}));
        check(!RecoveredWorldRecords::decode(std::array<std::uint8_t,4>{0xb8,0,0xb8,1}));
        const auto raw=RecoveredGuildRoster::member(49,3,255,8,0,"last");
        check(raw.size()==22 && raw[1]==49 && raw[2]==3 && raw[3]==255 && raw[4]==8 && raw.back()==0);
        for(const auto& name:{std::string("%bad"),std::string(16,'a'),std::string("a\0b",3)}) {
            bool rejected=false;try{RecoveredGuildRoster::member(0,1,1,1,0,name);}catch(...){rejected=true;}check(rejected);
        }
        Fixture f;auto service=f.service();
        check(!service.panel_ready(10));
        auto plan=service.prepare(10);check(plan && plan->logical.size()==44 && service.current(*plan));
        emit("two_initial",plan->logical);service.published(*plan);check(service.panel_ready(10));
        check(service.prepare(10)->logical.empty());
        f.roster->members.push_back(member(3,"third",40));f.online.insert(3);
        plan=service.prepare(10);check(plan && plan->logical.size()==68);
        emit("three_join",plan->logical);service.published(*plan);
        f.roster->members.erase(f.roster->members.begin()+1);
        plan=service.prepare(10);check(plan && plan->logical.size()==48);
        emit("two_delete",plan->logical);service.published(*plan);
        // Equality token includes a saved level revision; guild generation does
        // not have to change to project a real level change.
        f.roster->members[1].role->logical[1]=60;f.roster->members[1].role->revision++;
        plan=service.prepare(10);check(plan && !plan->logical.empty());
        emit("two_level",plan->logical);service.published(*plan);
        f.online.erase(3);plan=service.prepare(10);check(plan && !plan->logical.empty());service.published(*plan);
        f.roster.reset();plan=service.prepare(10);check(plan && plan->logical==std::vector<std::uint8_t>({0x92,1,0x92,0}));
        emit("self_leave",plan->logical);service.published(*plan);check(!service.panel_ready(10));
        check(service.prepare(10)->logical.empty());
        Fixture full;full.roster->members.clear();full.roster->members.push_back(member(1,"self"));
        for(unsigned id=2;id<=50;++id)full.roster->members.push_back(member(id,"member"+std::to_string(id)));
        auto fifty=full.service();plan=fifty.prepare(10);check(plan && plan->logical.size()==1100);
        emit("fifty_initial",plan->logical);fifty.published(*plan);
        full.roster->members.back().role->logical[1]=99;
        plan=fifty.prepare(10);check(plan && plan->logical.size()==1198);
        emit("fifty_update",plan->logical);fifty.published(*plan);
        full.peer.name="renamed";full.roster->members[0].name_utf8="renamed";
        plan=fifty.prepare(10);check(plan && plan->logical.size()==1200);
        emit("fifty_rename",plan->logical);fifty.published(*plan);
        full.roster->members.push_back(member(51,"overflow"));check(!fifty.prepare(10));
        full.roster->members.pop_back();full.roster->members.back().name_utf8="renamed";check(!fifty.prepare(10));
        Fixture invalid;auto reject=invalid.service();
        invalid.roster->members[1].role.reset();check(!reject.prepare(10));
        invalid.roster->members[1]=member(2,"other");invalid.roster->members[1].profile[29]=9;check(!reject.prepare(10));
        invalid.roster->members[1].profile[29]=2;invalid.roster->requester_account=99;check(!reject.prepare(10));
        invalid.roster->requester_account=1;invalid.roster->members[1].name_utf8="SELF";check(!reject.prepare(10));
        invalid.roster->members[1].name_utf8="other";
        invalid.roster->requester_account=1;invalid.peer.name="another";check(!reject.prepare(10));
        invalid.peer.name="self";invalid.peer.ready=false;check(!reject.prepare(10));
        invalid.peer.ready=true;invalid.roster->members[1].name_utf8="😀";check(!reject.prepare(10));
        invalid.roster->members[1].name_utf8="測試";
        for(bool cn:{false,true}) {
            invalid.peer.simplified=cn;plan=reject.prepare(10);check(plan && plan->logical.size()==44);
            const auto expected=LegacyChineseCodec::encode("測試",cn);
            check(std::equal(expected.begin(),expected.end(),plan->logical.begin()+28,
                [](char a,std::uint8_t b){return static_cast<std::uint8_t>(a)==b;}));
        }
        Fixture changed;changed.change_on_second=true;auto stale=changed.service();check(!stale.prepare(10));
        Fixture later;auto current=later.service();plan=current.prepare(10);check(plan.has_value());
        later.peer.account=99;check(!current.current(*plan));
        later.peer.account=1;current.published(*plan);current.forget(10);check(!current.panel_ready(10));
        std::cout<<"PASS "<<checks<<" checks\n";return 0;
    }catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}
}
