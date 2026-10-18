#include "protocol/RecoveredBattleBootstrap.h"
#include "protocol/DiagnosticBattleParticipants.h"
#include "protocol/RecoveredRoleVitals.h"
#include <iostream>
#include <string_view>

namespace {
using namespace god2;
using Bootstrap = RecoveredBattleBootstrap;
void require(bool value, const char* message) {
    if (!value) throw std::runtime_error(message);
}
template<class F> void rejected(F action) {
    bool threw = false;
    try { action(); } catch (const std::invalid_argument&) { threw = true; }
    require(threw, "Invalid bootstrap accepted");
}
// Explicit synthetic byte patterns, never production defaults or native stats.
Bootstrap::Actor fixture(std::uint8_t position) {
    RecoveredBattleIdentity::Bytes identity;
    for (unsigned i=0;i<identity.size();++i) identity[i]=static_cast<std::uint8_t>(i);
    identity[0]=0x1c;identity[1]=position;identity[2]=30;
    identity[5]=0;identity[6]=4;identity[7]=1;identity[8]=0;
    identity[9]=1;identity[11]=0;identity[12]=0;
    RecoveredBattleVitals::Bytes hp{};
    hp[0]=0x86;hp[2]=position;hp[3]=0xa5;hp[5]=120;hp[9]=100;hp[16]=0x5a;
    auto mp=hp;mp[1]=1;mp[5]=24;mp[9]=20;
    return {*RecoveredBattleIdentity::parse_logical(identity),
            *RecoveredBattleVitals::parse_logical(hp),
            position<14 ? RecoveredBattleVitals::parse_logical(mp) : std::nullopt};
}
void assertions() {
    using Entry=RecoveredBattleEntry;
    const Entry::Record context{0x12345678,0x9abcdeff};
    const auto entry=Entry::encode_logical(context);
    require(entry==Entry::Bytes{0x82,0x78,0x56,0x34,0x12,0xff,0xde,0xbc,0x9a},"Entry native byte order");
    require(Entry::encode_logical({0,30u<<8})==Entry::Bytes{0x82,0,0,0,0,0,30,0,0},
        "Diagnostic command window must occupy battle context byte +41");
    require(Entry::parse_logical(entry)==context,"Entry context round trip");
    for(std::size_t n=0;n<entry.size();++n)
        require(!Entry::parse_logical(std::span(entry).first(n)),"Truncated entry accepted");
    std::array<std::uint8_t,10> oversized{};oversized[0]=0x82;
    require(!Entry::parse_logical(oversized),"Oversized entry accepted");
    auto bad_entry=entry;bad_entry[0]=0x83;
    require(!Entry::parse_logical(bad_entry),"Wrong entry opcode accepted");
    for(auto a:{0u,0xffffffffu,0x80000000u})
        for(auto b:{0u,0xffffffffu,0x80000000u})
            require(Entry::parse_logical(Entry::encode_logical({a,b}))==Entry::Record{a,b},"Opaque context narrowed");
    const auto role=RecoveredRoleVitals::encode(76,26,120,80);
    require(role==std::array<std::uint8_t,17>{0x24,76,0,0,0,26,0,0,0,120,0,0,0,80,0,0,0},"Role resource wire order");
    rejected([]{RecoveredRoleVitals::encode(121,26,120,80);});
    rejected([]{RecoveredRoleVitals::encode(76,81,120,80);});
    rejected([]{RecoveredRoleVitals::encode(0,0,0,80);});
    const auto normal=diagnostic_battle_player_participants(1);
    {
        const std::array<BattleActor,2> actors{{
            {0,1,88,120,42,80,31,40,8,10},{14,0,96,150,0,0,20,25,13,6}}};
        BattleSnapshot checkpoint{1,3,BattleState::Active,{}};
        for(const auto& actor:actors) checkpoint.actors[actor.position]=actor;
        const auto projected=diagnostic_battle_resume_participants(1,checkpoint);
        require(projected==diagnostic_battle_player_participants(1,42,88,96),"Resume bootstrap lost saved resources");
        constexpr std::size_t enemy_offset=17+45+17+17+45;
        const auto enemy=RecoveredBattleVitals::parse_logical(std::span(projected).subspan(enemy_offset,17));
        require(enemy && enemy->current()==96 && enemy->maximum()==150,"Resume healed enemy or changed maximum");
        for(const auto hp:{1u,42u,96u,150u}) {
            const auto changed=diagnostic_battle_player_participants(1,50,100,hp);
            for(std::size_t i=0;i<normal.size();++i)
                require(changed[i]==(i==enemy_offset+9 ? hp : normal[i]),"Enemy HP change altered another field");
        }
        rejected([&]{diagnostic_battle_resume_participants(2,checkpoint);});
        auto bad=checkpoint;bad.actors[14]->max_hp=151;
        rejected([&]{diagnostic_battle_resume_participants(1,bad);});
        bad=checkpoint;bad.actors[1]=bad.actors[0];bad.actors[1]->position=1;
        rejected([&]{diagnostic_battle_resume_participants(1,bad);});
        rejected([]{diagnostic_battle_player_participants(1,50,100,0);});
        rejected([]{diagnostic_battle_player_participants(1,50,100,151);});
    }
    for(const auto mp:{0u,7u,8u,50u,80u}) {
        const auto low=diagnostic_battle_player_participants(1,mp);
        require(low.size()==normal.size(),"Initial MP must not change bootstrap layout");
        unsigned changed=0;
        for(std::size_t i=0;i<normal.size();++i) if(low[i]!=normal[i]) {
            require(normal[i]==50 && low[i]==mp,"Only scalar/bulk initial MP may change");
            ++changed;
        }
        require(changed==(mp==50 ? 0u : 2u),"Scalar and bulk initial MP must agree");
    }
    rejected([]{diagnostic_battle_player_participants(1,81);});
    for(const auto hp:{1u,88u,100u,120u}) {
        const auto restored=diagnostic_battle_player_participants(1,50,hp);
        unsigned changed=0;
        for(std::size_t i=0;i<normal.size();++i) if(restored[i]!=normal[i]) {
            require(normal[i]==100 && restored[i]==hp,"Only scalar/bulk initial HP may change");
            ++changed;
        }
        require(changed==(hp==100 ? 0u : 2u),"Scalar and bulk initial HP must agree");
    }
    rejected([]{diagnostic_battle_player_participants(1,50,0);});
    rejected([]{diagnostic_battle_player_participants(1,50,121);});
    const auto skill_seed=diagnostic_battle_skill_seed();
    const auto spell_seed=diagnostic_battle_skill_seed(1);
    require(spell_seed[21]==1 && spell_seed[22]==1,"Spell learned identity");
    require(diagnostic_battle_skill_selectable(1)==std::array<std::uint8_t,3>{0x87,1,0x81},
            "Spell selectable identity must match learned seed");
    require(diagnostic_battle_skill_selectable()==std::array<std::uint8_t,3>{0x87,1,0x80},
            "Physical selectable identity unchanged");
    const auto spell_effect=diagnostic_battle_skill_animation(0,14,54,0,true,1);
    require(spell_effect[11]==1 && spell_effect[12]==1 && spell_effect[14]==28,
            "Spell result identity must match learned seed");
    rejected([]{diagnostic_battle_skill_seed(2);});
    rejected([]{diagnostic_battle_skill_selectable(2);});
    rejected([]{diagnostic_battle_skill_animation(0,14,54,0,true,2);});
    require(skill_seed.size()==23 && skill_seed[0]==0x30 && skill_seed[1]==0xff &&
            skill_seed[19]==0x34 && skill_seed[20]==1 && skill_seed[21]==0 && skill_seed[22]==1,
            "Explicit diagnostic skill seed changed");
    for(unsigned position=0;position<14;++position) {
        const auto bytes=diagnostic_battle_mp(static_cast<std::uint8_t>(position),123456,654321);
        const auto parsed=RecoveredBattleVitals::parse_logical(bytes);
        require(parsed && parsed->native_actor_write_supported() && parsed->position()==position &&
                parsed->current()==123456 && parsed->maximum()==654321,"Diagnostic MP encoding changed");
    }
    rejected([]{diagnostic_battle_mp(14,1,2);});
    rejected([]{diagnostic_battle_mp(0,3,2);});
    for(unsigned source=0;source<28;++source) for(unsigned target=0;target<28;++target) {
        if(source/14==target/14) continue;
        const auto a=diagnostic_battle_basic_animation(static_cast<std::uint8_t>(source),static_cast<std::uint8_t>(target),18);
        require(a[0]==0x83 && a[1]==1 && a[2]==source && a[9]==0xee && a[10]==0xff,"Basic animation signed HP delta");
        const auto off=5+2*(target/14);
        require((unsigned(a[off])+(unsigned(a[off+1])<<8))==(1u<<(target%14)),"Basic animation target mask");
        const auto skill=diagnostic_battle_skill_animation(static_cast<std::uint8_t>(source),static_cast<std::uint8_t>(target),54,2);
        require(skill[0]==0x83 && skill[1]==3 && skill[2]==source && skill[3]==2 &&
                skill[9]==0xca && skill[10]==0xff && skill[11]==1 && skill[12]==0,
                "Skill animation must retain distinct action and catalog identity");
        require((unsigned(skill[off])+(unsigned(skill[off+1])<<8))==(1u<<(target%14)),"Skill target mask");
        require(a[12]==28 && a[14]==0 && skill[14]==28,"Surviving targets must not receive death outcome");
    }
    const auto zero=diagnostic_battle_basic_animation(0,14,0);
    require(diagnostic_battle_basic_animation(0,14,150,0,false)[12]==0 &&
            diagnostic_battle_skill_animation(0,14,150,0,false)[14]==0,"Explicit lethal outcome mapping");
    const auto counter_group=diagnostic_battle_basic_animation(14,0,12,1);
    require(counter_group[3]==1 && counter_group[9]==0xf4 && counter_group[10]==0xff,
            "Retaliation action group must preserve signed display delta");
    require(zero[9]==0 && zero[10]==0,"Zero HP delta");
    const auto maximum=diagnostic_battle_basic_animation(14,0,32767);
    require(maximum[9]==1 && maximum[10]==0x80,"Loss32767 is negative signed16");
    for(const std::uint8_t source:{0,14})for(const bool alive:{false,true}) {
        const auto target=static_cast<std::uint8_t>(14-source);
        const auto endpoint=diagnostic_battle_basic_animation(source,target,32768,37,alive);
        require(endpoint[9]==0&&endpoint[10]==0x80&&endpoint[2]==source&&endpoint[3]==37&&
            endpoint[12]==(alive?28:0),"BASIC -32768 endpoint or outcome changed");
        for(const std::uint8_t kind:{0,1}) {
            const auto spell=diagnostic_battle_skill_animation(source,target,32768,37,alive,kind);
            require(spell[9]==0&&spell[10]==0x80&&spell[11]==1&&spell[12]==kind&&
                spell[14]==(alive?28:0),"Standard skill -32768 endpoint or identity changed");
        }
    }
    rejected([]{diagnostic_battle_basic_animation(28,0,18);});
    rejected([]{diagnostic_battle_basic_animation(0,28,18);});
    rejected([]{diagnostic_battle_basic_animation(0,1,18);});
    rejected([]{diagnostic_battle_basic_animation(0,14,32769);});
    rejected([]{diagnostic_battle_skill_animation(0,14,32769);});
    rejected([]{diagnostic_battle_basic_animation(0,14,0x100008000ULL);});
    rejected([]{diagnostic_battle_skill_animation(0,14,0x100008000ULL);});
    rejected([]{diagnostic_battle_skill_animation(0,1,54);});
    rejected([]{diagnostic_battle_skill_animation(28,0,54);});
    const auto skill_zero=diagnostic_battle_skill_animation(0,14,0);
    const auto skill_max=diagnostic_battle_skill_animation(0,14,32767);
    require(skill_zero[9]==0 && skill_zero[10]==0 && skill_max[9]==1 && skill_max[10]==0x80,
            "Skill delta signed16 boundaries");
    const auto outcome=diagnostic_battle_zero_result();
    const auto progress_bytes=diagnostic_role_progress(76,26);
    const auto progress=RecoveredRoleProgress::parse(progress_bytes);
    if(!progress || progress->role_hp()!=76 || progress->role_mp()!=26 || progress->role_progress_display()!=2500 ||
       progress->companion_hp()!=0 || progress->companion_scalar_raw()!=0 || progress->companion_progress_display()!=0)
        throw std::runtime_error("Isolated progress sentinel differs");
    for(const std::uint32_t award:{0u,25u,0x7fffffffu}) {
        const auto awarded=diagnostic_battle_experience_result(award);
        const auto parsed=RecoveredBattleExperience::parse_logical(awarded);
        if(!parsed || parsed->character_received_exp_display()!=award)
            throw std::runtime_error("Diagnostic EXP field differs");
        for(std::size_t i=0;i<awarded.size();++i)
            if((i<5 || i>8) && awarded[i]!=outcome[i])
                throw std::runtime_error("Diagnostic EXP changed opaque or other recipient bytes");
    }
    try { diagnostic_battle_experience_result(0x80000000u);throw std::runtime_error("Signed EXP bound accepted"); }
    catch(const std::invalid_argument&) {}
    require(outcome.size()==57 && outcome[0]==0x89 &&
            std::all_of(outcome.begin()+1,outcome.end(),[](auto b){return b==0;}),"Zero-award diagnostic outcome changed");
    const auto diagnostic=diagnostic_battle_participants();
    require(diagnostic.size()==279,"Deferred participant size");
    const auto player=diagnostic_battle_player_participants(0x1234);
    require(player.size()==296 && player[0]==0x86 && player[1]==4 && player[3]==1,
            "Player appearance must precede identity");
    require(player[17]==0x1c && player[20]==0x34 && player[21]==0x12 && player[23]==0x20,
            "Diagnostic player identity projection");
    require(std::equal(player.begin()+4,player.begin()+12,RecoveredWorldEntry::historical_body.begin()+12),
            "Diagnostic appearance source");
    require(std::equal(player.begin()+62,player.end(),diagnostic.begin()+45),
            "Player diagnostic altered other participant records");
    rejected([]{diagnostic_battle_player_participants(0);});
    rejected([]{diagnostic_battle_player_participants(0x4000);});
    require(diagnostic[0]==0x1c && diagnostic[1]==0 && diagnostic[79]==0x1c && diagnostic[80]==14,
            "Diagnostic side ordering");
    require(diagnostic[141]==0x88 && diagnostic[146]==100 && diagnostic[150]==50,
            "Diagnostic bulk vitals mismatch");
    require(diagnostic[262]==0x86 && diagnostic[263]==5 && diagnostic[265]==1,
            "Diagnostic grant must follow bulk vitals");
    auto actor=fixture(0);
    const auto original=RecoveredBattleIdentity::encode_logical(actor.identity);
    require(actor.identity.enemy_area()==1 && actor.identity.enemy_scene()==0 &&
            actor.identity.ordinal()==1 && actor.identity.displayed_level()==30,"Identity field offset");
    for (std::size_t size=0;size<45;++size)
        require(!RecoveredBattleIdentity::parse_logical(std::span(original).first(size)),"Truncated identity");
    auto bad=original;bad[0]=0x83;
    require(!RecoveredBattleIdentity::parse_logical(bad),"Wrong construction opcode");
    for (unsigned position=0;position<256;++position) {
        bad=original;bad[1]=static_cast<std::uint8_t>(position);
        const auto parsed=RecoveredBattleIdentity::parse_logical(bad);
        require(parsed.has_value()==(position<28),"Position bound");
        if(parsed) require(RecoveredBattleIdentity::encode_logical(*parsed)==bad,"Opaque identity lost");
    }
    bad=original;bad[6]=0x60;
    require(!RecoveredBattleIdentity::parse_logical(bad)->enemy_area(),"Alternate bank mislabeled");
    for (unsigned count : {1u,14u,28u}) {
        std::vector<Bootstrap::Actor> actors;
        for(unsigned i=0;i<count;++i) actors.push_back(fixture(static_cast<std::uint8_t>(i)));
        const auto logical=Bootstrap::logical(0x12345678,0x9abcdeff,actors);
        require(logical.size()==9+count*62+std::min(count,14u)*17,"Batch size");
        require(logical[0]==0x82 && logical[1]==0x78 && logical[8]==0x9a,"Transition byte order");
        require(RecoveredWorldFrame::decode(Bootstrap::wire(0x12345678,0x9abcdeff,actors))==logical,
                "Bootstrap framing changed bytes");
        std::size_t offset=9;
        for(const auto& value:actors) {
            const auto bytes=RecoveredBattleIdentity::encode_logical(value.identity);
            require(std::equal(bytes.begin(),bytes.end(),logical.begin()+offset),"Identity reordered");
            offset+=45;
            const auto hp=RecoveredBattleVitals::encode_logical(value.hp);
            require(std::equal(hp.begin(),hp.end(),logical.begin()+offset),"HP opaque fields changed");
            offset+=17;
            if(value.mp) offset+=17;
        }
        require(offset==logical.size(),"Record boundary lost");
    }
    const auto encode=[&](auto actors) { return Bootstrap::logical(0,0,actors); };
    RecoveredBattleVitalsBatch::Bytes bulk{};
    bulk[0]=0x88;bulk[5]=100;bulk[9]=20;
    std::array<std::uint8_t,17> grant{};
    grant[0]=0x86;grant[1]=5;grant[3]=1;
    const auto actors=std::array{fixture(0),fixture(14)};
    const auto ready=[&](const auto& values, const auto& permission) {
        return Bootstrap::ready_logical(0,0,actors,*RecoveredBattleVitalsBatch::parse_logical(values),permission);
    };
    const auto base=Bootstrap::logical(0,0,actors);
    const auto sequence=ready(bulk,grant);
    require(sequence.size()==base.size()+138,"Ready size");
    require(std::equal(base.begin(),base.end(),sequence.begin()),"Bootstrap prefix changed");
    require(std::equal(bulk.begin(),bulk.end(),sequence.begin()+base.size()),"Bulk must precede grant");
    require(std::equal(grant.begin(),grant.end(),sequence.end()-17),"Grant bytes changed");
    require(RecoveredWorldFrame::decode(RecoveredWorldFrame::encode(sequence))==sequence,"Ready frame roundtrip");
    auto bad_bulk=bulk;bad_bulk[5]=101;
    rejected([&]{ready(bad_bulk,grant);});
    bad_bulk=bulk;bad_bulk[13]=1;
    rejected([&]{ready(bad_bulk,grant);});
    bad_bulk=bulk;std::fill(bad_bulk.begin()+1,bad_bulk.begin()+5,0xff);
    rejected([&]{ready(bad_bulk,grant);});
    for (unsigned slot : {1u,13u,14u,255u}) {
        auto bad_grant=grant;bad_grant[4]=static_cast<std::uint8_t>(slot);
        rejected([&]{ready(bulk,bad_grant);});
    }
    for (unsigned flags : {0u,2u,3u,255u}) {
        auto bad_grant=grant;bad_grant[3]=static_cast<std::uint8_t>(flags);
        rejected([&]{ready(bulk,bad_grant);});
    }
    rejected([&]{ready(bulk,std::span(grant).first(16));});
    auto missing_mp=actors;missing_mp[0].mp.reset();
    rejected([&]{Bootstrap::ready_logical(0,0,missing_mp,*RecoveredBattleVitalsBatch::parse_logical(bulk),grant);});
    rejected([&]{encode(std::vector<Bootstrap::Actor>{});});
    rejected([&]{encode(std::vector<Bootstrap::Actor>(29,actor));});
    rejected([&]{encode(std::array{actor,actor});});
    auto mismatched=actor;mismatched.hp=fixture(1).hp;
    rejected([&]{encode(std::array{mismatched});});
    auto swapped=actor;swapped.hp=*actor.mp;
    rejected([&]{encode(std::array{swapped});});
    auto enemy=fixture(14);auto unsupported=RecoveredBattleVitals::encode_logical(enemy.hp);unsupported[1]=1;
    enemy.mp=RecoveredBattleVitals::parse_logical(unsupported);
    rejected([&]{encode(std::array{enemy});});
    auto overflow=RecoveredBattleVitals::encode_logical(actor.hp);overflow[9]=121;
    actor.hp=*RecoveredBattleVitals::parse_logical(overflow);
    rejected([&]{encode(std::array{actor});});
}
}
int main(int argc,char** argv) {
    try {
        if(argc==2 && std::string_view(argv[1])=="--diagnostic-skill-effect") {
            const auto bytes=diagnostic_battle_skill_animation(0,14,54);
            constexpr char digits[]="0123456789abcdef";
            for(auto b:bytes) std::cout<<digits[b>>4]<<digits[b&15];
            std::cout<<'\n';
        } else if(argc==2 && std::string_view(argv[1])=="--diagnostic-wire") {
            const auto wire=Bootstrap::wire(0x12345678,0x9abcdeff,std::array{fixture(0),fixture(14)});
            constexpr char digits[]="0123456789abcdef";
            for(auto b:wire) std::cout<<digits[b>>4]<<digits[b&15];
            std::cout<<'\n';
        } else if(argc==2 && std::string_view(argv[1])=="--diagnostic-participant-logical") {
            const auto logical=diagnostic_battle_player_participants(1);
            constexpr char digits[]="0123456789abcdef";
            for(auto b:logical) std::cout<<digits[b>>4]<<digits[b&15];
            std::cout<<'\n';
        } else {require(argc==1,"Unexpected arguments");assertions();}
    } catch(const std::exception& error) {std::cerr<<error.what()<<'\n';return 1;}
}
