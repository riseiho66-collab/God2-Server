#include "game/OwnedPveWorldCatalog.h"
#include <stdexcept>
#include <vector>
// SOURCE ONLY. These are material-affinity checks, not native gameplay or
// socket acceptance. PHASE1 does not execute this target.
namespace {
void require(bool condition){if(!condition)throw std::runtime_error("PvE source material affinity mismatch");}
using J=nlohmann::json;
using Bytes=std::vector<std::uint8_t>;
Bytes bytes(std::size_t n,std::uint8_t opcode){Bytes b(n);b[0]=opcode;return b;}
void put(Bytes& b,std::size_t at,std::uint32_t n,unsigned width=4){for(unsigned i=0;i<width;++i)b.at(at+i)=std::uint8_t(n>>(8*i));}
template<class Fn>void rejected(Fn fn){bool refused=false;try{fn();}catch(const std::exception&){refused=true;}require(refused);}
J actor(std::uint8_t slot,bool pet=false,bool enemy=false){
    auto id=bytes(45,0x1c);id[1]=slot;id[2]=1;id[3]=pet?0x11:0x12;id[4]=pet?0x40:0;
    id[6]=enemy?4:(pet?0x40:0x20);auto hp=bytes(17,0x86);hp[2]=slot;put(hp,5,100);put(hp,9,100);
    auto mp=hp;mp[1]=1;put(mp,5,50);put(mp,9,10);
    auto appearance=bytes(17,0x86);appearance[1]=4;appearance[2]=slot;appearance[3]=1;
    return {{"identity",id},{"hp",hp},{"mp",enemy?J(nullptr):J(mp)},
        {"appearance",pet||enemy?J(nullptr):J(appearance)}};
}
// Complete CUSTOM_TEST_NOT_NATIVE material; never imported or used as a native
// source. Construct the actual immutable catalog to exercise whole validation.
J catalog(god2::StoredPet2Slot& pet1,god2::StoredPet2Slot& pet2){
    auto stat1=bytes(god2::RecoveredPet1Stats::logical_size,0xe3);
    stat1[0x1d]=0x91;stat1[0x1e]=0x33;stat1[0x27]=44;
    put(stat1,1,20,2);put(stat1,3,100,2);put(stat1,5,10,2);put(stat1,7,50,2);
    auto stat2=bytes(god2::RecoveredPet2Stats::logical_size,0xfb);
    stat2[1]=0x61;stat2[2]=0x6d;stat2[3]=44;
    put(stat2,5,30|(10u<<14)|0xa0000000u);put(stat2,13,100|(50u<<14));
    god2::RecoveredPet2Lifecycle::Metadata metadata{};metadata[0]=0x91;metadata[1]=0x33;metadata[2]=32;
    pet1.slot=44;pet1.provenance.source_sha256=std::string(64,'a');
    const auto s1=god2::RecoveredPet1Stats::parse_logical(stat1);require(s1.has_value());
    pet1.pet1=god2::RecoveredPet1Lifecycle::Snapshot{{1,11},metadata,*s1};
    metadata[0]=0x61;metadata[1]=0x6d;metadata[2]=34;
    pet2.slot=44;pet2.provenance.source_sha256=std::string(64,'b');
    const auto s2=god2::RecoveredPet2Stats::parse_logical(stat2);require(s2.has_value());
    pet2.pet=god2::RecoveredPet2Lifecycle::Snapshot{{1,11},metadata,*s2};
    auto bulk=bytes(121,0x88);put(bulk,1,37);auto grant=bytes(17,0x86);grant[1]=5;
    auto attack=bytes(15,0x83);attack[1]=1;attack[7]=1;attack[12]=28;
    auto support=bytes(15,0x83);support[1]=8;support[9]=1;
    auto withdrawal=bytes(15,0x83);withdrawal[1]=6;withdrawal[12]=2;
    auto swap=bytes(15,0x83);swap[1]=9;swap[7]=1;swap[9]=1;
    const J templates{{"bulk",bulk},{"grant",grant},{"attack",attack},{"support",support},
        {"withdrawal",withdrawal},{"row_swap",swap},{"terminal",bytes(57,0x89)},{"entry_context_b",0},
        {"animation_group_policy","custom_contiguous_batch_0_254"},{"cycle_counter_policy","fixed_complete_profile"}};
    const J policy{{"magical",false},{"power_percent",100},{"defense_percent",100},{"mp_cost",0},
        {"critical_chance_bp",0},{"critical_multiplier_percent",100}};
    const J enemy{{"position",14},{"hp",100},{"max_hp",100},{"mp",0},{"max_mp",0},
        {"physical_attack",1},{"magical_attack",1},{"physical_defense",1},{"magical_defense",1},{"native",actor(14,false,true)}};
    const J scene{{"id",1},{"area",2},{"scene",15},{"movement_steps",1},
        {"formation",{{"version",1},{"source_record","CUSTOM_TEST_NOT_NATIVE"},{"lanes",J::array({J::array({0,5})})}}},
        {"basic",policy},{"ai",policy},{"templates",templates},{"support_enabled",false},{"enemies",J::array({enemy})}};
    const J variant{{"pet",actor(5,true)},{"active_pet_material",{{"kind","Pet2"},{"metadata",metadata},
        {"stats",stat2},{"source_sha256",pet2.provenance.source_sha256}}}};
    const J character{{"character",11},{"root_profile",Bytes(40)},{"entry_logical",bytes(37,0x2a)},
        {"world_spawn",bytes(81,0x6f)},{"world_remove",bytes(5,0x73)},{"world_move",bytes(13,0x5e)},
        {"primary",actor(0)},{"pet",actor(5,true)},
        {"active_pet_material",{{"kind","Pet1"},{"metadata",pet1.pet1->inventory},{"stats",stat1},
            {"source_sha256",pet1.provenance.source_sha256}}},{"pet_profiles",J::array({variant})}};
    return {{"design_id","CUSTOM-0161"},{"native_client_sha256","aaf0fae66e89c4547244304ecd8f4c2755746ffa6c9b9dfe68a0ff3fd2b4cd48"},
        {"version",1},{"source_sha256",std::string(64,'c')},{"source_record","CUSTOM_TEST_NOT_NATIVE:catalog"},
        {"scenes",J::array({scene})},{"character_profiles",J::array({character})}};
}
void variants(){
    god2::StoredPet2Slot one{},two{};const auto source=catalog(one,two);const god2::OwnedPveWorldCatalog immutable(source);
    require(immutable.pet_profile(11,one).mp->maximum()==50&&immutable.pet_profile(11,two).hp.maximum()==100);
    auto first=one;auto stat1=god2::RecoveredPet1Stats::encode_logical(first.pet1->stats);stat1[1]^=1;
    first.pet1->stats=*god2::RecoveredPet1Stats::parse_logical(stat1);
    require(immutable.pet_profile(11,first).mp->maximum()==50);
    stat1[9]^=1;first.pet1->stats=*god2::RecoveredPet1Stats::parse_logical(stat1);
    rejected([&]{immutable.pet_profile(11,first);});
    auto changed=two;auto stats=god2::RecoveredPet2Stats::encode_logical(changed.pet->stats);
    stats[5]^=1;changed.pet->stats=*god2::RecoveredPet2Stats::parse_logical(stats);
    require(immutable.pet_profile(11,changed).hp.maximum()==100); // Only current HP changed.
    changed=two;stats=god2::RecoveredPet2Stats::encode_logical(changed.pet->stats);stats[8]^=2;
    changed.pet->stats=*god2::RecoveredPet2Stats::parse_logical(stats);rejected([&]{immutable.pet_profile(11,changed);});
    changed=two;changed.pet->inventory[19]^=1;rejected([&]{immutable.pet_profile(11,changed);});
    changed=two;changed.provenance.source_sha256=std::string(64,'d');rejected([&]{immutable.pet_profile(11,changed);});
    changed=two;changed.slot=43;rejected([&]{immutable.pet_profile(11,changed);});
    auto duplicate=source;duplicate["character_profiles"][0]["pet_profiles"].push_back(duplicate["character_profiles"][0]["pet_profiles"][0]);
    rejected([&]{god2::OwnedPveWorldCatalog invalid(duplicate);});
    auto mismatch=source;mismatch["character_profiles"][0]["pet_profiles"][0]["pet"]["hp"][5]=99;
    rejected([&]{god2::OwnedPveWorldCatalog invalid(mismatch);});
    auto family=source;family["character_profiles"][0]["pet_profiles"][0]["active_pet_material"]["metadata"][2]=32;
    rejected([&]{god2::OwnedPveWorldCatalog invalid(family);});
    auto key=source;key["character_profiles"][0]["pet_profiles"][0]["active_pet_material"]["metadata"][0]=0x62;
    rejected([&]{god2::OwnedPveWorldCatalog invalid(key);});
    auto counter=source;counter["scenes"][0]["templates"]["cycle_counter_policy"]="grant_epoch";
    rejected([&]{god2::OwnedPveWorldCatalog invalid(counter);});
    auto sentinel=source;for(unsigned n=1;n<5;++n)sentinel["scenes"][0]["templates"]["bulk"][n]=255;
    rejected([&]{god2::OwnedPveWorldCatalog invalid(sentinel);});
    auto group=source;group["scenes"][0]["templates"]["support"][3]=255;
    rejected([&]{god2::OwnedPveWorldCatalog invalid(group);});
}
}
int main() {
    variants();
    std::vector<std::uint8_t> source(37,0);source[0]=0x2a;
    source[2]=0x80;source[13]=0x56;source[27]=0xa5;source[29]=2;
    const nlohmann::json prototype=source;
    auto moved=source;moved[1]=0x23;moved[2]=0x91;moved[25]=7;moved[26]=9;
    moved[29]=0xfe;moved[30]=0x12;moved[31]=0x23;moved[32]=0x34;
    require(god2::OwnedPveWorldCatalog::same_entry_material(prototype,moved));
    auto changed=moved;changed[13]^=1;
    require(!god2::OwnedPveWorldCatalog::same_entry_material(prototype,changed));
    changed=moved;changed[2]^=0x40;
    require(!god2::OwnedPveWorldCatalog::same_entry_material(prototype,changed));
    changed=moved;changed[27]^=1;
    require(!god2::OwnedPveWorldCatalog::same_entry_material(prototype,changed));
    changed=moved;changed[29]^=1;
    require(!god2::OwnedPveWorldCatalog::same_entry_material(prototype,changed));
    changed.pop_back();
    require(!god2::OwnedPveWorldCatalog::same_entry_material(prototype,changed));
}
