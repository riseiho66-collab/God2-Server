// PHASE1 regression SOURCE ONLY. No test/build/SQLite/codec execution was run.
#include "game/OwnedPveRoomState.h"
#include "game/OwnedPveTimeoutPair.h"
#include "game/OwnedBattleRowPreference.h"
#include "db/SqliteAccountRepository.h"
#include "db/SqliteMigrationManager.h"
#include "db/SqliteSupport.h"
#include <algorithm>
#include <cstring>
#include <iostream>
#include <memory>
namespace {
using namespace god2;using T=OwnedPveRoomTypes;
void require(bool b,const char* why){if(!b)throw std::runtime_error(why);}
template<class F>void rejects(F f){try{f();}catch(const std::exception&){return;}throw std::runtime_error("Expected actual PvE rejection");}
struct Fixture {
    sqlite3* db{};
    std::unique_ptr<sqlite3,decltype(&sqlite3_close_v2)> owner{nullptr,sqlite3_close_v2};
    std::unique_ptr<SqliteAccountRepository> accounts;
    std::unique_ptr<SqliteRecoveredCharacterRepository> characters;
    std::unique_ptr<SqliteRoleAuxiliaryRepository> auxiliary;
    std::unique_ptr<SqliteCompanionRepository> pets;
    std::unique_ptr<SqliteOwnedPveRoomRepository> repository;
    std::vector<T::MemberInput> inputs;
    Fixture(){
        require(sqlite3_open(":memory:",&db)==SQLITE_OK,"Open isolated memory fixture");owner.reset(db);
        auto migrations=default_sqlite_migrations();std::erase_if(migrations,[](const auto& m){return m.version>42;});
        SqliteMigrationManager(db,migrations).migrate();
        accounts=std::make_unique<SqliteAccountRepository>(db);characters=std::make_unique<SqliteRecoveredCharacterRepository>(db);
        auxiliary=std::make_unique<SqliteRoleAuxiliaryRepository>(db);pets=std::make_unique<SqliteCompanionRepository>(db);
        sqlite_detail::execute(db,SqliteNativeWorldEntrySnapshotRepository::schema());
        SqliteNativeWorldEntrySnapshotRepository row(db,*accounts,*characters);
        for(unsigned n=0;n<3;++n){
            const auto account=accounts->create("pve-fixture-"+std::to_string(n),"fixture-only-not-a-login");
            std::array<std::uint8_t,40> profile{};profile[0]=std::uint8_t('A'+n);
            T::MemberInput m;m.root=characters->create(account.id,profile);
            m.identity={100+n,account.id,m.root.id,1,1,1,std::uint16_t(10+n)};
            m.return_position=characters->commit_position(account.id,m.root.id,{},4,3,10,10);
            m.primary_slot=std::uint8_t(n*2);m.command_context=1000+n;
            m.role.logical.fill(0);m.role.logical[0]=0x22;m.role.logical[1]=1;m.role.logical[17]=100;m.role.logical[21]=20;
            m.role.revision=1;m.role.design_id="CUSTOM-0013";
            sqlite_detail::Statement role(db,"INSERT INTO character_role_snapshots VALUES(?,?,1,'CUSTOM-0013')");role.bind_id(1,m.root.id);role.bind_blob(2,m.role.logical);role.done();
            m.resources={100,100,20,20,1,"CUSTOM-0012"};
            sqlite_detail::Statement resources(db,"INSERT INTO character_resources VALUES(?,100,100,20,20,1,'CUSTOM-0012')");resources.bind_id(1,m.root.id);resources.done();
            RecoveredRoleAuxiliary::Logical raw{};raw[0]=0x2c;raw[49]=20;raw[57]=20;
            m.auxiliary=auxiliary->save(account.id,m.root.id,{},raw,"CUSTOM_TEST_NOT_NATIVE","CUSTOM-0161:isolated-source-regression");
            NativeWorldEntrySnapshot preference{m.root,m.return_position,OwnedBattleRowPreference::client_pin,
                OwnedBattleRowPreference::record_kind,OwnedBattleRowPreference::client_pin,OwnedBattleRowPreference::source_record,{0xe8,std::uint8_t(n&1)},1};
            // Fixture grants only this isolated memory DB; never a production
            // issuer, actual Session preparation or native receipt factory.
            m.row_preference=row.replace_from_issuer({},preference,[](const auto&,const auto&,auto){return true;},[]{return true;});
            require(m.row_preference.has_value(),"Save explicit fixture B4 choice");inputs.push_back(std::move(m));
        }
        SqliteOwnedPveRoomRepository::install_schema(db);
        repository=std::make_unique<SqliteOwnedPveRoomRepository>(db,*accounts,*characters,*auxiliary,*pets);
    }
    T::Encounter encounter(unsigned members=1){T::Encounter e;e.members.assign(inputs.begin(),inputs.begin()+members);
        e.enemies={{14,0,1000,1000,0,0,10,10,0,0},{15,0,1000,1000,0,0,10,10,0,0}};
        e.seed=7;e.source_sha256=std::string(64,'a');e.source_record="CUSTOM_TEST_NOT_NATIVE:0161-actual-repository";e.support_enabled=true;return e;}
};
T::Project project=[](const T::Snapshot& s,const T::Change& c){std::vector<T::Output> out;
    for(const auto& [id,m]:s.members)if(m.status!=T::MemberStatus::Returned&&m.status!=T::MemberStatus::Retired&&!m.disconnected&&!m.return_context)
        out.push_back({id,(c.kind==T::Change::Kind::Entry||(c.kind==T::Change::Kind::Admission&&c.character==id))?T::OutputKind::Entry:T::OutputKind::Grant,{0xe8,0}});
    return out;}; // Structurally complete E8 only: not a native battle acceptance fixture.
const T::PureCurrent current=[]{return true;};
const Battle::Rule damage=[](const CombatRuleInput& in){return CombatRuleResult{10,in.mp_cost,false};};
void written_all(OwnedPveRoomState& room,const OwnedPveRoomState::Ticket& t){for(const auto& d:room.pending(t))room.written(t,d.sequence,d.recipient,true,current);}
void shared_admission_and_claims(){
    Fixture f;OwnedPveRoomState room(*f.repository);auto ticket=room.create(f.encounter(2),project,current);written_all(room,ticket);
    room.act_ai(ticket,{14,{0,2},false,100,0,0,0,100},damage,project,current);written_all(room,ticket);
    room.act(ticket,f.inputs[0].identity,1,{0,{14},false,100,0,0,0,100},
        [](const auto& in){return CombatRuleResult{1000,in.mp_cost,false};},project,current);written_all(room,ticket);
    auto before=room.inspect(ticket);const auto random=before->checkpoint.random_state;
    require(before->members.at(f.inputs[0].identity.character).input.resources.hp==90&&before->members.at(f.inputs[1].identity.character).input.resources.hp==90,"All member resources not saved together");
    room.admit(ticket,f.inputs[2],project,current);auto joined=room.inspect(ticket);
    require(joined->checkpoint.snapshot.actors[0]->hp==90&&joined->checkpoint.snapshot.actors[2]->hp==90&&joined->checkpoint.snapshot.actors[14]->hp==0&&joined->checkpoint.random_state==random,"Late join reset old HP/dead monster/RNG");
    require(!joined->members.at(f.inputs[2].identity.character).primary_grant,"Late join manufactured a current consumed-round grant");written_all(room,ticket);
    const auto helper=f.inputs[2].identity;
    rejects([&]{room.act(ticket,helper,joined->grant_epoch,{4,{14},false,100,0,0,0,100},damage,project,current);});
    auto forged=f.inputs[0].identity;++forged.session;
    rejects([&]{room.act(ticket,forged,1,{0,{14},false,100,0,0,0,100},damage,project,current);});
    room.withdraw(ticket,f.inputs[0].identity,true,project,current);written_all(room,ticket);
    require(!f.repository->character_claimed(f.inputs[0].identity.account,f.inputs[0].identity.character)&&
        f.repository->character_claimed(f.inputs[1].identity.account,f.inputs[1].identity.character),"Leader disconnect released wrong/all claims");
    require(f.characters->load_resources(f.inputs[0].identity.account,f.inputs[0].identity.character)->hp==90,
        "Disconnect tombstone incorrectly killed the actual saved character");
    room.pass(ticket,f.inputs[1].identity,1,2,project,current);written_all(room,ticket);
    room.grant_round(ticket,project,current);written_all(room,ticket);
    require(room.inspect(ticket)->members.at(f.inputs[0].identity.character).grant_epoch==1&&
        room.inspect(ticket)->members.at(f.inputs[1].identity.character).grant_epoch==2&&
        f.repository->read_retained(ticket.id()).members.at(f.inputs[0].identity.character).grant_epoch==1,
        "Next round rewrote Retired member history instead of continuing remaining members");
}
void rollback_and_postcommit_truth(){
    Fixture f;OwnedPveRoomState room(*f.repository);auto t=room.create(f.encounter(2),project,current);written_all(room,t);
    const auto initial=room.inspect(t);const auto hp=f.characters->load_resources(f.inputs[0].identity.account,f.inputs[0].identity.character);
    // The SECOND actor's saved row changes after projection, before BEGIN.
    auto stale=[&](const T::Snapshot& s,const T::Change& c){auto outputs=project(s,c);sqlite_detail::execute(f.db,"UPDATE character_resources SET revision=revision+1 WHERE character_id="+std::to_string(f.inputs[1].identity.character));return outputs;};
    rejects([&]{room.act_ai(t,{14,{0,2},false,100,0,0,0,100},damage,stale,current);});
    require(room.inspect(t)==initial&&f.characters->load_resources(f.inputs[0].identity.account,f.inputs[0].identity.character)==hp,"Later member stale CAS partially saved earlier member");
    Fixture fence;OwnedPveRoomState fenced(*fence.repository);auto v=fenced.create(fence.encounter(),project,current);written_all(fenced,v);
    const auto prior=fenced.inspect(v);bool before_commit=true;
    sqlite3_trace_v2(fence.db,SQLITE_TRACE_STMT,[](unsigned,void* p,void*,void* sql){
        constexpr auto prefix="SELECT document FROM main.owned_pve_rooms WHERE id=? AND revision=?";
        if(sql&&std::strncmp(static_cast<const char*>(sql),prefix,std::strlen(prefix))==0)*static_cast<bool*>(p)=false;return 0;},&before_commit);
    rejects([&]{fenced.act_ai(v,{14,{0},false,100,0,0,0,100},damage,project,[&]{return before_commit;});});
    sqlite3_trace_v2(fence.db,0,nullptr,nullptr);
    require(fenced.inspect(v)==prior&&fence.characters->load_resources(fence.inputs[0].identity.account,fence.inputs[0].identity.character)->hp==100,
        "Final pure fence failed to rollback complete candidate before COMMIT");
    Fixture observed;OwnedPveRoomState observed_room(*observed.repository);auto w=observed_room.create(observed.encounter(2),project,current);written_all(observed_room,w);
    const auto observed_before=observed_room.inspect(w);
    struct Trace{sqlite3* db;bool injected=false,ok=false;} trace{observed.db};
    sqlite3_trace_v2(observed.db,SQLITE_TRACE_STMT,[](unsigned,void* p,void*,void* sql){auto& t=*static_cast<Trace*>(p);
        constexpr auto prefix="SELECT document FROM main.owned_pve_rooms WHERE id=? AND revision=?";
        if(!t.injected&&sql&&std::strncmp(static_cast<const char*>(sql),prefix,std::strlen(prefix))==0){t.injected=true;
            t.ok=sqlite3_exec(t.db,"UPDATE character_resources SET hp=hp-1",nullptr,nullptr,nullptr)==SQLITE_OK;}
        return 0;},&trace);
    rejects([&]{observed_room.act_ai(w,{14,{0,2},false,100,0,0,0,100},damage,project,current);});
    sqlite3_trace_v2(observed.db,0,nullptr,nullptr);
    require(trace.injected&&trace.ok&&observed_room.inspect(w)==observed_before&&
        observed.characters->load_resources(observed.inputs[0].identity.account,observed.inputs[0].identity.character)->hp==100&&
        observed.characters->load_resources(observed.inputs[1].identity.account,observed.inputs[1].identity.character)->hp==100,
        "Final SQL observer changed actual source after validation without rolling back all-member candidate");
    // A fresh fixture tests a pure final fence retired by the final SQL trace.
    Fixture g;OwnedPveRoomState next(*g.repository);auto u=next.create(g.encounter(),project,current);written_all(next,u);
    bool live=true;
    sqlite3_trace_v2(g.db,SQLITE_TRACE_STMT,[](unsigned,void* p,void*,void* sql){if(sql&&std::strcmp(static_cast<const char*>(sql),"COMMIT")==0)*static_cast<bool*>(p)=false;return 0;},&live);
    next.act_ai(u,{14,{0},false,100,0,0,0,100},damage,project,[&]{return live;});
    sqlite3_trace_v2(g.db,0,nullptr,nullptr);
    require(next.recovery_required(u)&&g.characters->load_resources(g.inputs[0].identity.account,g.inputs[0].identity.character)->hp==90,"Post-COMMIT retirement pretended rollback or reopened old input");
    require(g.repository->read_retained(u.id()).checkpoint.snapshot.actors[0]->hp==90,"Durable checkpoint diverged from committed resource");
    Fixture commit_changed;OwnedPveRoomState changed(*commit_changed.repository);auto x=changed.create(commit_changed.encounter(),project,current);written_all(changed,x);
    Trace commit_trace{commit_changed.db};
    sqlite3_trace_v2(commit_changed.db,SQLITE_TRACE_STMT,[](unsigned,void* p,void*,void* sql){auto& t=*static_cast<Trace*>(p);
        if(!t.injected&&sql&&std::strcmp(static_cast<const char*>(sql),"COMMIT")==0){t.injected=true;
            t.ok=sqlite3_exec(t.db,"UPDATE character_resources SET hp=hp-1",nullptr,nullptr,nullptr)==SQLITE_OK;}return 0;},&commit_trace);
    changed.act_ai(x,{14,{0},false,100,0,0,0,100},damage,project,current);sqlite3_trace_v2(commit_changed.db,0,nullptr,nullptr);
    require(commit_trace.injected&&commit_trace.ok&&changed.recovery_required(x)&&
        commit_changed.characters->load_resources(commit_changed.inputs[0].identity.account,commit_changed.inputs[0].identity.character)->hp==89&&
        commit_changed.repository->read_retained(x.id()).checkpoint.snapshot.actors[0]->hp==90,
        "COMMIT observer DB write pretended rollback/current room instead of retained durable recovery");
    Fixture uncertain;OwnedPveRoomState uncertain_room(*uncertain.repository);auto uncertain_ticket=uncertain_room.create(uncertain.encounter(),project,current);written_all(uncertain_room,uncertain_ticket);
    sqlite3_commit_hook(uncertain.db,[](void*){return 1;},nullptr);
    rejects([&]{uncertain_room.act_ai(uncertain_ticket,{14,{0},false,100,0,0,0,100},damage,project,current);});
    sqlite3_commit_hook(uncertain.db,nullptr,nullptr);
    require(uncertain_room.recovery_required(uncertain_ticket)&&uncertain.repository->character_claimed(uncertain.inputs[0].identity.account,uncertain.inputs[0].identity.character)&&
        uncertain.characters->load_resources(uncertain.inputs[0].identity.account,uncertain.inputs[0].identity.character)->hp==100,
        "COMMIT failure reopened old gameplay input or falsely claimed after-state durable success");
}
void full_choice_and_absent_active_pet_readsets(){
    Fixture f;OwnedPveRoomState room(*f.repository);
    auto changed_choice=[&](const T::Snapshot& s,const T::Change& c){auto outputs=project(s,c);
        sqlite_detail::execute(f.db,"UPDATE character_native_world_entries SET record=X'E801',revision=revision+1 WHERE character_id="+std::to_string(f.inputs[0].identity.character));return outputs;};
    rejects([&]{room.create(f.encounter(),changed_choice,current);});
    require(!f.repository->character_claimed(f.inputs[0].identity.account,f.inputs[0].identity.character),"Changed B4 choice admitted stale configured slots");
    Fixture g;OwnedPveRoomState next(*g.repository);
    auto appeared_pet=[&](const T::Snapshot& s,const T::Change& c){auto outputs=project(s,c);
        RecoveredPet1Stats::LogicalRecord raw{};raw[0]=0xe3;raw[0x27]=44;raw[0x1d]=0x91;raw[0x1e]=0x33;
        std::array<std::uint8_t,20> metadata{};metadata[0]=0x91;metadata[1]=0x33;metadata[2]=32;
        sqlite_detail::Statement q(g.db,"INSERT INTO character_pet2_slots VALUES(?,44,?,?,1,?,'CUSTOM_TEST_NOT_NATIVE','CUSTOM-0161:appeared-active44')");
        q.bind_id(1,g.inputs[0].identity.character);q.bind_blob(2,metadata);q.bind_blob(3,raw);q.bind(4,SqliteCompanionRepository::source_sha256);q.done();return outputs;};
    rejects([&]{next.create(g.encounter(),appeared_pet,current);});
    require(!g.repository->character_claimed(g.inputs[0].identity.account,g.inputs[0].identity.character),"Active44 appeared between source read and transaction but was omitted");
}
void individual_return_and_no_reset(){
    Fixture f;OwnedPveRoomState room(*f.repository);auto t=room.create(f.encounter(2),project,current);written_all(room,t);
    auto input=f.inputs[0];room.withdraw(t,input.identity,false,project,current);written_all(room,t);
    const std::array<std::uint8_t,4> context{10,0,0,0};std::vector<std::uint8_t> scene;
    for(unsigned n=0;n<3000;++n)scene.insert(scene.end(),{0xe8,0}); // Full record boundaries across three frames.
    room.prepare_return(t,input.identity,std::move(scene),context,current);
    rejects([&]{room.complete_return(t,input.identity,context,current);});
    auto pending=room.pending(t);require(pending.size()==3,"Return aggregate not split losslessly on complete native records");
    auto wrong=input.identity;++wrong.battle_generation;
    rejects([&]{room.written(t,pending[0].sequence,wrong,true,current);});
    room.written(t,pending[0].sequence,input.identity,true,current);
    rejects([&]{room.complete_return(t,input.identity,context,current);});
    room.written(t,pending[1].sequence,input.identity,true,current);
    rejects([&]{room.complete_return(t,input.identity,context,current);});
    room.written(t,pending[2].sequence,input.identity,true,current);
    auto bad=context;bad[3]=1;rejects([&]{room.complete_return(t,input.identity,bad,current);});
    const auto continuation=room.complete_return(t,input.identity,context,current);
    require(continuation.identity()==input.identity&&continuation.room()==t.id()&&continuation.incarnation()==t.incarnation()&&
        continuation.admission().resources==input.resources&&continuation.saved().resources.hp==100&&
        f.repository->return_continuation_current(continuation,current),"Durable return did not mint exact original-admission/full-saved continuation");
    require(!f.repository->return_continuation_current(continuation,[]{return false;}),"Return lineage bypassed current actual post-return Session witness");
    SqliteOwnedPveRoomRepository other_repository(f.db,*f.accounts,*f.characters,*f.auxiliary,*f.pets);
    // Even another facade on the same connection is not this token's exact
    // continuation issuer; public values cannot replace retained ownership.
    require(!other_repository.return_continuation_current(continuation,current),"Foreign repository facade borrowed private continuation authority");
    require(!f.repository->character_claimed(input.identity.account,input.identity.character)&&
        f.repository->character_claimed(f.inputs[1].identity.account,f.inputs[1].identity.character),"Individual return released another participant");
    room.pass(t,f.inputs[1].identity,1,2,project,current);written_all(room,t);room.grant_round(t,project,current);written_all(room,t);
    require(room.inspect(t)->members.at(input.identity.character).grant_epoch==1&&
        room.inspect(t)->members.at(f.inputs[1].identity.character).grant_epoch==2,
        "Next round changed a previously Returned member's immutable grant history");
    room.withdraw(t,f.inputs[1].identity,true,project,current);require(room.inspect(t)->closed,"Last disconnect did not close independently returned room");
    room.retire_closed(t);require(f.repository->read_retained(t.id()).closed,"Runtime retirement deleted durable room history");
}
void both_pet_generations_save_full_blobs(){
    Fixture f;
    for(unsigned n=0;n<2;++n){auto& m=f.inputs[n];StoredPet2Slot saved;saved.slot=44;saved.revision=7;
        saved.provenance={SqliteCompanionRepository::source_sha256,"CUSTOM_TEST_NOT_NATIVE","CUSTOM-0161:pet-raw-fixture"};
        std::array<std::uint8_t,20> metadata{};metadata[2]=32;metadata[19]=0xa5;
        std::vector<std::uint8_t> stats;
        if(n==0){RecoveredPet1Stats::LogicalRecord b{};b[0]=0xe3;b[1]=100;b[3]=100;b[5]=20;b[7]=20;b[0x1d]=0x91;b[0x1e]=0x33;b[0x27]=44;b.back()=0xa5;
            metadata[0]=0x91;metadata[1]=0x33;auto raw=RecoveredPet1Stats::parse_logical(b);require(bool(raw),"Fixture E3 source invalid");
            saved.pet1=RecoveredPet1Lifecycle::Snapshot{{m.identity.account,m.identity.character},metadata,*raw};stats.assign(b.begin(),b.end());
        }else{metadata[2]=34;RecoveredPet2Stats::LogicalRecord b{};b[0]=0xfb;b[1]=0x61;b[2]=0x6d;b[3]=44;b[4]=1;b.back()=0xa5;
            const std::uint32_t value=100u|(20u<<14)|0x92000000u;
            for(unsigned i=0;i<4;++i){b[5+i]=std::uint8_t(value>>(8*i));b[13+i]=std::uint8_t(value>>(8*i));}
            metadata[0]=0x61;metadata[1]=0x6d;auto raw=RecoveredPet2Stats::parse_logical(b);require(bool(raw),"Fixture FB source invalid");
            saved.pet=RecoveredPet2Lifecycle::Snapshot{{m.identity.account,m.identity.character},metadata,*raw};stats.assign(b.begin(),b.end());
        }
        sqlite_detail::Statement q(f.db,"INSERT INTO character_pet2_slots VALUES(?,44,?,?,7,?,'CUSTOM_TEST_NOT_NATIVE','CUSTOM-0161:pet-raw-fixture')");
        q.bind_id(1,m.identity.character);q.bind_blob(2,metadata);q.bind_blob(3,stats);q.bind(4,SqliteCompanionRepository::source_sha256);q.done();
        m.pet=T::PetInput{std::uint8_t(n*2+1),saved};
    }
    OwnedPveRoomState room(*f.repository);auto ticket=room.create(f.encounter(2),project,current);written_all(room,ticket);
    room.act_ai(ticket,{14,{0,1,2,3},false,100,0,0,0,100},damage,project,current);auto saved=room.inspect(ticket);
    for(unsigned n=0;n<2;++n){const auto& m=saved->members.at(f.inputs[n].identity.character).input;const auto& p=m.pet->saved;
        require(m.resources.hp==90&&p.revision==8&&p.provenance.authority=="CUSTOM_DESIGNED","All-member player/pet save was not atomic");
        std::vector<std::uint8_t> actual,old;
        if(n==0){const auto a=RecoveredPet1Stats::encode_logical(p.pet1->stats),b=RecoveredPet1Stats::encode_logical(f.inputs[n].pet->saved.pet1->stats);actual.assign(a.begin(),a.end());old.assign(b.begin(),b.end());}
        else{const auto a=RecoveredPet2Stats::encode_logical(p.pet->stats),b=RecoveredPet2Stats::encode_logical(f.inputs[n].pet->saved.pet->stats);actual.assign(a.begin(),a.end());old.assign(b.begin(),b.end());}
        for(std::size_t k=0;k<old.size();++k)if(n==0?(k!=1&&k!=2&&k!=5&&k!=6):(k<5||k>8))
            require(actual[k]==old[k],"Pet save replaced unrelated raw field/metadata/source bytes");
        sqlite_detail::Statement q(f.db,"SELECT stats,revision FROM character_pet2_slots WHERE character_id=? AND slot=44");q.bind_id(1,m.identity.character);require(q.row(),"Actual pet row lost");const auto raw=q.blob(0,1,73);
        require(std::vector<std::uint8_t>(raw.begin(),raw.end())==actual&&q.integer(1)==8,"Pet saved only in shadow room document");
    }
    written_all(room,ticket);room.act_ai(ticket,{14,{1},false,100,0,0,0,100},damage,project,current);written_all(room,ticket);
    const auto before_swap=room.inspect(ticket);const auto pet_before=RecoveredPet1Stats::encode_logical(before_swap->members.at(f.inputs[0].identity.character).input.pet->saved.pet1->stats);
    room.swap_pair(ticket,f.inputs[0].identity,1,1,0,project,current);written_all(room,ticket);room.complete_swap(ticket,project,current);written_all(room,ticket);
    const auto swapped=room.inspect(ticket);const auto& actor=swapped->members.at(f.inputs[0].identity.character);
    require(actor.primary_position()==1&&actor.pet_position()==0&&actor.input.primary_slot==0&&actor.input.pet->actor_slot==1&&
        swapped->checkpoint.snapshot.actors[1]->hp==90&&swapped->checkpoint.snapshot.actors[0]->hp==80&&
        RecoveredPet1Stats::encode_logical(actor.input.pet->saved.pet1->stats)==pet_before&&actor.input.pet->saved.revision==9&&
        swapped->checkpoint.random_state==before_swap->checkpoint.random_state&&!actor.primary_grant&&actor.secondary_grant,
        "Actual pet swap exchanged vitals/rawsource/roles or manufactured another turn");
    room.act_ai(ticket,{14,{0},false,100,0,0,0,100},damage,project,current);written_all(room,ticket);
    require(f.characters->load_resources(f.inputs[0].identity.account,f.inputs[0].identity.character)->hp==90&&
        room.inspect(ticket)->members.at(f.inputs[0].identity.character).input.pet->saved.pet1->stats.vitals().current_hp==70,
        "Post-swap damage saved into old slot's wrong player/pet record");
    auto dead=*f.inputs[0].pet;dead.actor_slot=5;auto raw=RecoveredPet1Stats::encode_logical(dead.saved.pet1->stats);raw[1]=0;raw[2]=0;
    dead.saved.pet1->stats=*RecoveredPet1Stats::parse_logical(raw);dead.saved.pet1->owner={f.inputs[2].identity.account,f.inputs[2].identity.character};
    sqlite_detail::Statement insert(f.db,"INSERT INTO character_pet2_slots VALUES(?,44,?,?,7,?,'CUSTOM_TEST_NOT_NATIVE','CUSTOM-0161:pet-raw-fixture')");
    insert.bind_id(1,f.inputs[2].identity.character);insert.bind_blob(2,dead.saved.pet1->inventory);insert.bind_blob(3,raw);insert.bind(4,SqliteCompanionRepository::source_sha256);insert.done();
    f.inputs[2].pet=dead;written_all(room,ticket);room.admit(ticket,f.inputs[2],project,current);
    require(room.inspect(ticket)->checkpoint.snapshot.actors[5]->hp==0&&!room.inspect(ticket)->members.at(f.inputs[2].identity.character).secondary_grant&&
        room.inspect(ticket)->checkpoint.snapshot.actors[1]->hp==90,"Late join revived dead saved pet or reset an incumbent pet");
}
void failed_multiframe_entry_and_return(){
    Fixture f;OwnedPveRoomState room(*f.repository);
    const auto multi=[](const T::Snapshot& s,const T::Change& c){auto outputs=project(s,c);
        if(c.kind==T::Change::Kind::Entry||c.kind==T::Change::Kind::Admission){auto copy=outputs;outputs.insert(outputs.end(),copy.begin(),copy.end());outputs.insert(outputs.end(),copy.begin(),copy.end());}return outputs;};
    auto t=room.create(f.encounter(2),multi,current);auto frames=room.pending(t);require(frames.size()==6,"Fixture is not genuinely multi-frame entry");
    const auto id=f.inputs[0].identity;room.written(t,frames[0].sequence,id,false,current);
    auto failed=room.inspect(t);require(failed->members.at(id.character).disconnected&&std::none_of(failed->outbox.begin(),failed->outbox.end(),[&](const auto& d){return d.recipient==id&&d.status==T::OutputStatus::Pending;}),"Failed entry left unsendable Pending frames");
    room.withdraw(t,id,true,project,current);written_all(room,t);
    require(!f.repository->character_claimed(id.account,id.character)&&f.repository->character_claimed(f.inputs[1].identity.account,f.inputs[1].identity.character),"Failed multi-entry released wrong member");
    const auto second=f.inputs[1].identity;room.withdraw(t,second,false,project,current);written_all(room,t);
    std::vector<std::uint8_t> aggregate;for(unsigned i=0;i<3000;++i)aggregate.insert(aggregate.end(),{0xe8,0});
    const std::array<std::uint8_t,4> context{11,0,0,0};room.prepare_return(t,second,std::move(aggregate),context,current);frames=room.pending(t);require(frames.size()==3,"Return source not multi-frame");
    room.written(t,frames[0].sequence,second,true,current);room.written(t,frames[1].sequence,second,false,current);
    rejects([&]{room.complete_return(t,second,context,current);});
    require(room.pending(t).empty(),"Failed return retained pending suffix");
    room.withdraw(t,second,true,project,current);require(room.inspect(t)->members.at(second.character).status==T::MemberStatus::Retired,"Failed return falsely completed normal WORLD return");
}
void simultaneous_disconnect_is_one_room_commit(){
    Fixture f;OwnedPveRoomState room(*f.repository);auto t=room.create(f.encounter(2),project,current);written_all(room,t);
    const auto revision=room.inspect(t)->revision;
    room.retire_disconnected(t,{f.inputs[0].identity,f.inputs[1].identity},project,current);
    const auto after=room.inspect(t);require(after->revision==revision+1&&after->closed&&room.pending(t).empty(),"Simultaneous private cleanup did not commit one canonical room transition");
    for(unsigned n=0;n<2;++n)require(after->members.at(f.inputs[n].identity.character).status==T::MemberStatus::Retired&&
        !f.repository->character_claimed(f.inputs[n].identity.account,f.inputs[n].identity.character)&&
        f.characters->load_resources(f.inputs[n].identity.account,f.inputs[n].identity.character)->hp==100,
        "Simultaneous disconnect retained wrong claim or wrote combat tombstone into actual HP");
}
void configured_empty_swap_is_canonical_and_durable(){
    Fixture f;f.inputs[0].reserved_partner=1;OwnedPveRoomState room(*f.repository);
    auto t=room.create(f.encounter(2),project,current);written_all(room,t);const auto before=room.inspect(t);const auto id=f.inputs[0].identity;
    room.swap_pair(t,id,1,1,0,project,current);auto swapped=room.inspect(t);const auto& m=swapped->members.at(id.character);
    require(m.primary_position()==1&&!m.pet_position()&&m.partner_position()==0&&m.positions().revision==2&&
        m.input.primary_slot==0&&m.input.reserved_partner==1&&m.admission_source&&m.admission_source->primary_slot==0&&
        !swapped->checkpoint.snapshot.actors[0]&&swapped->checkpoint.snapshot.actors[1]->hp==100&&
        swapped->checkpoint.random_state==before->checkpoint.random_state&&m.input.row_preference==f.inputs[0].row_preference&&
        swapped->pending_swap&&!m.primary_grant&&swapped->animation_sequence==1,
        "Empty configured swap invented a pet/death/grant or rewrote saved B4/source/RNG");
    rejects([&]{room.complete_swap(t,project,current);}); // Exact output has not been Written.
    rejects([&]{room.admit(t,f.inputs[2],project,current);});
    rejects([&]{room.pass(t,f.inputs[1].identity,1,2,project,current);});
    written_all(room,t);require(room.inspect(t)->pending_swap.has_value(),"Written was mistaken for native renderer completion");
    room.complete_swap(t,project,current);written_all(room,t);require(!room.inspect(t)->pending_swap,"Qualified custom progress did not clear exact pending edge");
    const auto retained=f.repository->read_retained(t.id());require(retained.members.at(id.character).primary_position()==1&&
        retained.members.at(id.character).admission_source->primary_slot==0&&retained.animation_sequence==1,"Durable room lost live assignment/original admission/label lineage");
    room.pass(t,f.inputs[1].identity,1,2,project,current);written_all(room,t);room.grant_round(t,project,current);written_all(room,t);
    rejects([&]{room.swap_pair(t,id,1,2,1,project,current);});
    rejects([&]{room.swap_pair(t,id,2,1,1,project,current);});
    room.swap_pair(t,id,2,2,1,project,current);written_all(room,t);room.complete_swap(t,project,current);written_all(room,t);
    require(room.inspect(t)->members.at(id.character).primary_position()==0&&room.inspect(t)->members.at(id.character).positions().revision==3,"Repeated pair swap lost monotonic assignment ABA fence");
    // A failure after any projected swap must preserve the prior whole room.
    Fixture stale;stale.inputs[0].reserved_partner=1;OwnedPveRoomState other(*stale.repository);auto u=other.create(stale.encounter(2),project,current);written_all(other,u);const auto prior=other.inspect(u);
    auto provider=[&](const T::Snapshot& s,const T::Change& c){auto output=project(s,c);sqlite_detail::execute(stale.db,"UPDATE character_resources SET revision=revision+1 WHERE character_id="+std::to_string(stale.inputs[1].identity.character));return output;};
    rejects([&]{other.swap_pair(u,stale.inputs[0].identity,1,1,0,provider,current);});require(other.inspect(u)==prior,"Later member CAS failure partially published pair permutation");
}
void individual_return_excludes_later_room_cleanup_outputs(){
    Fixture f;OwnedPveRoomState room(*f.repository);auto t=room.create(f.encounter(2),project,current);written_all(room,t);
    const auto returning=f.inputs[0].identity;room.withdraw(t,returning,false,project,current);written_all(room,t);
    const std::array<std::uint8_t,4> context{7,6,5,4};std::vector<std::uint8_t> scene;
    for(unsigned n=0;n<3000;++n)scene.insert(scene.end(),{0xe8,0});
    room.prepare_return(t,returning,std::move(scene),context,current);
    room.retire_disconnected(t,{f.inputs[1].identity},project,current);
    const auto pending=room.pending(t);require(pending.size()==3&&std::all_of(pending.begin(),pending.end(),[&](const auto& d){return d.recipient==returning&&d.kind==T::OutputKind::Return;}),
        "Other member cleanup appended battle output into retained individual return transport");
    written_all(room,t);const auto token=room.complete_return(t,returning,context,current);
    require(room.inspect(t)->closed&&f.repository->return_continuation_current(token,current)&&!f.repository->character_claimed(returning.account,returning.character),
        "Concurrent cleanup stopped exact all-written individual claim release/continuation");
    room.retire_closed(t);
}
void native_timeout_pair_preflight_and_saved_boundaries(){
    Fixture f;auto& input=f.inputs[0];StoredPet2Slot pet{};pet.slot=44;pet.revision=1;
    pet.provenance={SqliteCompanionRepository::source_sha256,"CUSTOM_TEST_NOT_NATIVE","pass6:timeout-active44"};
    std::array<std::uint8_t,20> meta{};meta[0]=0x91;meta[1]=0x33;meta[2]=32;
    RecoveredPet1Stats::LogicalRecord stats{};stats[0]=0xe3;stats[1]=stats[3]=100;stats[5]=stats[7]=20;
    stats[0x1d]=0x91;stats[0x1e]=0x33;stats[0x27]=44;
    const auto parsed_pet=RecoveredPet1Stats::parse_logical(stats);require(bool(parsed_pet),"Timeout fixture pet grammar failed");
    pet.pet1=RecoveredPet1Lifecycle::Snapshot{{input.identity.account,input.identity.character},meta,*parsed_pet};
    sqlite_detail::Statement insert(f.db,"INSERT INTO character_pet2_slots VALUES(?,44,?,?,1,?,'CUSTOM_TEST_NOT_NATIVE','pass6:timeout-active44')");
    insert.bind_id(1,input.identity.character);insert.bind_blob(2,meta);insert.bind_blob(3,stats);insert.bind(4,SqliteCompanionRepository::source_sha256);insert.done();
    input.pet=T::PetInput{1,pet};OwnedPveRoomState room(*f.repository);auto ticket=room.create(f.encounter(2),project,current);written_all(room,ticket);
    const auto before=room.inspect(ticket);const auto id=input.identity;
    std::vector<std::uint8_t> wire;
    const auto append_command=[&](std::uint8_t action,std::uint8_t actor,std::uint8_t side,std::uint16_t mask,std::uint32_t opaque){
        std::array<std::uint8_t,17> b{};b[0]=0x35;b[1]=actor;b[2]=action;b[3]=side;b[4]=0xa5;
        b[5]=std::uint8_t(mask);b[6]=std::uint8_t(mask>>8);
        for(unsigned n=0;n<4;++n){b[9+n]=std::uint8_t(input.command_context>>(8*n));b[13+n]=std::uint8_t(opaque>>(8*n));}
        wire.insert(wire.end(),b.begin(),b.end());
    };
    append_command(2,0,0,1,0xfedcba98u);append_command(2,1,1,2,0x89abcdefu);
    // Native512620 retains count1; second action2 leaves the pet target mask
    // for a coalesced auto0B whose SOURCE is still primary B51.
    append_command(0x0b,0,0,2,0x76543210u);
    const auto records=RecoveredWorldRecords::read(wire);require(bool(records),"Actual parser rejected native two-role timeout payload");
    const auto batch=OwnedPveTimeoutPair::read(*records);require(batch&&OwnedPveTimeoutPair::current(*batch,before->members.at(id.character),*before),"Native timeout pair did not qualify exact living owner roles");
    require(batch->roles[0].unwritten_byte3==0xa5&&batch->roles[0].unwritten_parameter==0xfedcba98u&&
        batch->roles[1].unwritten_parameter==0x89abcdefu&&batch->progress&&batch->progress->target_masks[0]==2,
        "Timeout pair normalized original opaque bits or rejected genuine nonzero progress mask");
    auto invalid=*records;std::swap(invalid[0],invalid[1]);rejects([&]{OwnedPveTimeoutPair::read(invalid);});
    invalid=*records;invalid.push_back((*records)[0]);rejects([&]{OwnedPveTimeoutPair::read(invalid);});
    invalid=*records;invalid.push_back((*records)[2]);rejects([&]{OwnedPveTimeoutPair::read(invalid);});
    invalid=*records;invalid.emplace_back(RecoveredWorldRecords::ContextNotification{{1,2,3,4}});rejects([&]{OwnedPveTimeoutPair::read(invalid);});
    invalid=*records;invalid.emplace_back(batch->roles[0]);rejects([&]{OwnedPveTimeoutPair::read(invalid);});
    auto wrong=*before;wrong.members.at(id.character).primary_grant=false;
    require(!OwnedPveTimeoutPair::current(*batch,wrong.members.at(id.character),wrong),"Timeout pair manufactured a consumed primary grant");
    wrong=*before;wrong.checkpoint.snapshot.actors[1]->controller=f.inputs[1].identity.character;
    require(!OwnedPveTimeoutPair::current(*batch,wrong.members.at(id.character),wrong),"Timeout pair borrowed another owner's actor");
    wrong=*before;wrong.members.at(id.character).assignment=T::Assignment{1,0,2};
    require(!OwnedPveTimeoutPair::current(*batch,wrong.members.at(id.character),wrong),"Old native timeout pair was relabelled after a row swap");
    room.pass(ticket,id,1,batch->roles[0].actor_position,project,current);
    auto first=room.inspect(ticket);require(!first->members.at(id.character).primary_grant&&first->members.at(id.character).secondary_grant&&
        first->animation_sequence==before->animation_sequence+1&&first->grant_epoch==1,"First timeout pass consumed both roles or minted a round");
    rejects([&]{room.pass(ticket,id,1,batch->roles[1].actor_position,project,current);});
    written_all(room,ticket);room.pass(ticket,id,1,batch->roles[1].actor_position,project,current);written_all(room,ticket);
    const auto after=room.inspect(ticket);require(!after->members.at(id.character).primary_grant&&!after->members.at(id.character).secondary_grant&&
        after->animation_sequence==before->animation_sequence+2&&after->grant_epoch==1&&after->checkpoint==before->checkpoint&&
        after->members.at(id.character).input.resources==before->members.at(id.character).input.resources,
        "Two native timeout roles lost separate progress boundaries or changed HP/RNG/round");
    require(f.repository->read_retained(ticket.id()).animation_sequence==after->animation_sequence,"Timeout publication sequence was only transient");
}
}
int main(){try{native_timeout_pair_preflight_and_saved_boundaries();shared_admission_and_claims();rollback_and_postcommit_truth();individual_return_and_no_reset();both_pet_generations_save_full_blobs();failed_multiframe_entry_and_return();full_choice_and_absent_active_pet_readsets();simultaneous_disconnect_is_one_room_commit();configured_empty_swap_is_canonical_and_durable();individual_return_excludes_later_room_cleanup_outputs();std::cout<<"owned PvE room0161 source cases passed\n";return 0;}catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}}
