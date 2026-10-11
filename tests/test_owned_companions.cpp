#include "handlers/RecoveredOwnedCompanions.h"
#include "db/SqliteMigrationManager.h"
#include "db/SqliteRecoveredCharacterRepository.h"
#include "db/SqliteSupport.h"
#include <iostream>
#include <memory>
#include <stdexcept>
namespace {
using namespace god2;
void require(bool value,const char* message) {if(!value) throw std::runtime_error(message);}
template<class F> void rejects(F&& action) {try{action();}catch(const std::exception&){return;}throw std::runtime_error("Expected rejection");}
struct Fixture {
    struct Close {void operator()(sqlite3* db)const{sqlite3_close_v2(db);}};
    std::unique_ptr<sqlite3,Close> db;std::uint64_t character;
    explicit Fixture(bool previous_schema=false) {
        sqlite3* raw=nullptr;require(sqlite3_open(":memory:",&raw)==SQLITE_OK,"Open failed");db.reset(raw);
        sqlite_detail::execute(raw,"PRAGMA foreign_keys=ON");auto migrations=default_sqlite_migrations();
        if(previous_schema)migrations.resize(36);SqliteMigrationManager(raw,migrations).migrate();
        sqlite_detail::execute(raw,"INSERT INTO accounts(id,username,password_hash) VALUES(1,'first','hash'),(2,'other','hash')");
        std::array<std::uint8_t,40> profile{};profile[0]='A';
        if(previous_schema) {
            sqlite_detail::Statement insert(raw,"INSERT INTO recovered_characters(account_id,slot,profile,name_bytes) VALUES(1,0,?,X'41')");
            insert.bind_blob(1,profile);insert.done();character=sqlite3_last_insert_rowid(raw);
        } else character=roles().create(1,profile).id;
        for(const auto key:{28001,28002,28003}) {
            sqlite_detail::Statement row(raw,"INSERT INTO native_companion_metadata VALUES('NCP',?,?,1,X'41',?,zeroblob(396))");
            row.bind(1,key);row.bind(2,std::string(SqliteCompanionRepository::source_sha256));row.bind(3,std::string(64,'a'));row.done();
        }
    }
    SqliteRecoveredCharacterRepository roles(){return SqliteRecoveredCharacterRepository(db.get());}
    SqliteCompanionRepository repo(){return SqliteCompanionRepository(db.get());}
    StoredPet2Slot slot(std::uint8_t index){const auto all=repo().load_pet2_slots(1,character);return *std::find_if(all.begin(),all.end(),[&](auto& row){return row.slot==index;});}
    void sql(const char* text){sqlite_detail::execute(db.get(),text);}
};
CompanionProvenance provenance(){return {SqliteCompanionRepository::source_sha256,"CUSTOM_TEST_NOT_NATIVE","owned-companions-isolated-fixture"};}
RecoveredDeityState::Snapshot deity(std::uint8_t key) {
    RecoveredDeityState::Declaration::Bytes d{};d[0]=0x30;d[1]=key;d[2]='A';
    RecoveredDeityState::Status::Bytes s{};s[0]=0x31;s[1]=key;s[2]=1;
    std::array<std::uint8_t,4> skill{0x34,key,0,1};
    return {*RecoveredDeityState::Declaration::parse(d),*RecoveredDeityState::Status::parse(s),{*RecoveredDeityState::Skill::parse(skill)}};
}
RecoveredPet2Lifecycle::Snapshot pet(std::uint64_t character,std::uint8_t slot,std::uint16_t key) {
    RecoveredPet2Stats::LogicalRecord raw{};raw[0]=0xfb;raw[1]=static_cast<std::uint8_t>(key);raw[2]=static_cast<std::uint8_t>(key>>8);raw[3]=slot;
    raw[17]=31;raw[19]=12; // Test-only distinguishable raw stats, no balance claim.
    raw[4]=255; // Full native unsigned level byte survives save/slot transfer.
    raw[5]=0xff;raw[6]=0xff;raw[7]=0xff;raw[8]=0xff;
    raw[12]=0xa5;raw[13]=1;raw[14]=0x40;
    RecoveredPet2Lifecycle::Metadata metadata{};metadata[0]=raw[1];metadata[1]=raw[2];metadata[2]=34;
    return {{1,character},metadata,*RecoveredPet2Stats::parse_logical(raw)};
}
RecoveredPet1Lifecycle::Snapshot pet1(std::uint64_t character,std::uint8_t slot) {
    RecoveredPet1Stats::LogicalRecord raw{};raw[0]=0xe3;raw[0x1d]=0xc1;raw[0x1e]=0x5d;raw[0x27]=slot;
    raw[0x24]=255;raw[9]=0xff;raw[10]=0xff;raw[11]=0xff;raw[12]=0xff;
    RecoveredPet1Lifecycle::Metadata metadata{};metadata[0]=0xc1;metadata[1]=0x5d;metadata[2]=32;
    return {{1,character},metadata,*RecoveredPet1Stats::parse_logical(raw)};
}
std::vector<std::uint8_t> raw(const StoredPet2Slot& value) {
    if(value.pet1) {const auto result=RecoveredPet1Stats::encode_logical(value.pet1->stats);return {result.begin(),result.end()};}
    if(!value.pet)return {};
    auto result=RecoveredPet2Stats::encode_logical(value.pet->stats);return {result.begin(),result.end()};
}
}
int main() {
    try {
        Fixture f;auto repo=f.repo();RecoveredOwnedCompanions service(repo);const auto c=f.character;
        require(service.restore(1,c).empty(),"Absent ownership emitted packets");
        require(!repo.selected_deity_has_skill(1,c,0,126),"Absent ownership granted custom skill");
        require(!repo.selected_deity_has_skill(1,c,0,150),"Absent ownership granted bull skill");
        rejects([&]{repo.load_deities(2,c);});rejects([&]{repo.provision_pet2_slots(2,c);});
        const auto one=repo.store_deity(1,c,deity(101),{},provenance());
        const auto two=repo.store_deity(1,c,deity(102),{},provenance());
        {
            auto custom=deity(102);
            custom.skills.push_back(*RecoveredDeityState::Skill::parse(std::array<std::uint8_t,4>{0x34,102,0,126}));
            custom.skills.push_back(*RecoveredDeityState::Skill::parse(std::array<std::uint8_t,4>{0x34,102,0,150}));
            repo.store_deity(1,c,custom,1,provenance());
            require(!repo.selected_deity_has_skill(1,c,0,126),"Unselected deity granted skill");
            require(!repo.selected_deity_has_skill(1,c,0,150),"Unselected deity granted bulls");
            repo.select_deity(1,c,102,repo.load_deity_selection(1,c));
            require(repo.selected_deity_has_skill(1,c,0,126),"Selected learned custom skill not authorized");
            require(repo.selected_deity_has_skill(1,c,0,150),"Selected learned bull skill not authorized");
            require(!repo.selected_deity_has_skill(1,c,1,150),"Wrong kind gained bull authorization");
            rejects([&]{repo.selected_deity_has_skill(2,c,0,150);});
            require(!repo.selected_deity_has_skill(1,c,1,126),"Wrong kind gained custom authorization");
            rejects([&]{repo.selected_deity_has_skill(2,c,0,126);});
            const auto restored=service.restore(1,c);
            bool learned=false;
            for(const auto& batch:restored) for(std::size_t i=0;i+3<batch.size();++i)
                if(batch[i]==0x34 && batch[i+1]==102 && batch[i+2]==0 && batch[i+3]==126) learned=true;
            require(learned,"Saved custom learned state not restored");
            bool bull_learned=false;
            for(const auto& batch:restored)for(std::size_t i=0;i+3<batch.size();++i)
                if(batch[i]==0x34 && batch[i+1]==102 && batch[i+2]==0 && batch[i+3]==150)bull_learned=true;
            require(bull_learned,"Saved bull learned state not restored");
            auto invalid=custom;invalid.skills.back()=*RecoveredDeityState::Skill::parse(
                std::array<std::uint8_t,4>{0x34,102,0,125});
            rejects([&]{repo.store_deity(1,c,invalid,2,provenance());});
            // Restore the original fixture baseline for the independent tests below.
            f.sql("UPDATE character_deities SET skills=X'34660001',revision=1 WHERE row_key=102");
            f.sql("UPDATE character_deity_selection SET row_key=101,revision=1");
        }
        require(one.revision==1 && two.revision==1,"Deity import revisions");
        const auto unchanged_deities=repo.load_deities(1,c);
        auto unsafe=deity(102);unsafe.skills[0]=*RecoveredDeityState::Skill::parse(
            std::array<std::uint8_t,4>{0x34,102,0,120});
        rejects([&]{repo.store_deity(1,c,unsafe,1,provenance());});
        require(repo.load_deities(1,c).size()==unchanged_deities.size() &&
            repo.load_deities(1,c)[1].snapshot.skills[0].encode()==two.snapshot.skills[0].encode() &&
            repo.load_deities(1,c)[1].revision==1,"Unavailable icon import changed saved skills");
        f.sql("UPDATE character_deities SET skills=X'34660078' WHERE row_key=102");
        rejects([&]{service.restore(1,c);});
        f.sql("UPDATE character_deities SET skills=X'34660001' WHERE row_key=102");
        require(service.select_deity(1,c,{101}).has_value(),"Owned deity selection failed");
        const auto selected=repo.load_deity_selection(1,c);
        require(selected->key==101 && selected->revision==1,"Selection not saved");
        require(service.select_deity(1,c,{101}).has_value() && repo.load_deity_selection(1,c)==selected,"Same selection changed revision");
        require(!service.select_deity(1,c,{103}) && repo.load_deity_selection(1,c)==selected,"Foreign deity selected");
        repo.select_deity(1,c,102,selected);
        rejects([&]{repo.select_deity(1,c,101,selected);});
        require(repo.load_deity_selection(1,c)->key==102,"Stale selection wrote");
        auto p=provenance();p.source_sha256=std::string(64,'b');
        rejects([&]{repo.store_deity(1,c,deity(102),{},p);});
        rejects([&]{repo.store_deity(1,c,deity(1),{},provenance());});
        rejects([&]{repo.store_deity(1,c,deity(100),{},provenance());});
        rejects([&]{repo.store_deity(1,c,deity(109),{},provenance());});
        require(repo.load_deities(1,c).size()==2,"Invalid import granted deity");
        f.sql("CREATE TRIGGER fail_selection AFTER UPDATE ON character_deity_selection BEGIN SELECT RAISE(ABORT,'injected'); END");
        rejects([&]{service.select_deity(1,c,{101});});
        require(repo.load_deity_selection(1,c)->key==102,"Selection transaction did not roll back");
        f.sql("DROP TRIGGER fail_selection");
        require(repo.provision_pet2_slots(1,c)==3 && repo.provision_pet2_slots(1,c)==0,"Pet capacity not explicit/idempotent");
        require(f.slot(42).revision==1 && !f.slot(42).pet,"Empty slot inferred pet");
        repo.store_pet2(1,c,42,pet(c,42,28001),1,provenance());
        repo.store_pet2(1,c,43,pet(c,43,28002),1,provenance());
        rejects([&]{repo.store_pet2(1,c,42,pet(c,42,28003),1,provenance());});
        rejects([&]{repo.store_pet2(2,c,44,pet(c,44,28003),1,provenance());});
        require(!service.select_pet2(1,c,{28002,42}),"Client item lie accepted");
        require(service.select_pet2(1,c,{28001,42}).has_value(),"Reserve selection failed");
        require(!f.slot(42).pet && f.slot(44).pet->stats.metadata_key()==28001,"Pet not moved to active44");
        const auto active=f.slot(44).pet->stats;
        require(active.level()==255 && active.star_rank()==10 && active.star_rating()==5,
            "Pet transfer changed level or star fields");
        const auto vitals=active.vitals();
        require(vitals.current_hp==16383 && vitals.current_mp==2047 &&
            vitals.maximum_hp==1 && vitals.maximum_mp==1,
            "Pet transfer changed packed HP/MP values");
        require(service.select_pet2(1,c,{28002,43}).has_value(),"Active swap failed");
        require(f.slot(43).pet->stats.metadata_key()==28001 && f.slot(44).pet->stats.metadata_key()==28002,"Swap lost an instance");
        require(service.select_pet2(1,c,{28002,44}).has_value(),"Return active failed");
        require(f.slot(42).pet->stats.metadata_key()==28002 && !f.slot(44).pet,"Return did not pick explicit empty42");
        const auto before42=f.slot(42),before44=f.slot(44);
        f.sql("CREATE TRIGGER fail_second AFTER UPDATE ON character_pet2_slots WHEN NEW.slot=44 BEGIN SELECT RAISE(ABORT,'injected'); END");
        rejects([&]{service.select_pet2(1,c,{28002,42});});
        require(raw(f.slot(42))==raw(before42) && f.slot(42).revision==before42.revision && !f.slot(44).pet,"Partial pet transfer survived failed second write");
        f.sql("DROP TRIGGER fail_second");
        service.select_pet2(1,c,{28002,42});
        rejects([&]{repo.transfer_pet2(1,c,before42,before44);});
        repo.store_pet2(1,c,42,pet(c,42,28003),f.slot(42).revision,provenance());
        require(!service.select_pet2(1,c,{28002,44}),"Return silently overwrote full reserves");
        const auto resources=f.roles().commit_resources(1,c,{}, {52,120,2,80,0,"CUSTOM-0012"});
        const auto reservation=f.roles().reserve_battle(1,c,resources);
        rejects([&]{service.select_pet2(1,c,{28003,42});});
        rejects([&]{service.select_deity(1,c,{101});});
        require(f.roles().load_resources(1,c)==resources,"Companion changed player resources");
        f.roles().settle_battle(1,c,reservation,resources,resources,true,0);
        const auto frames=service.restore(1,c);require(!frames.empty(),"Owned restore empty");
        for(const auto& frame:frames)require(frame.size()<=RecoveredWorldFrame::max_logical_size,"Native queue cap exceeded");
        std::vector<std::uint8_t> flattened;
        for(const auto& frame:frames)flattened.insert(flattened.end(),frame.begin(),frame.end());
        require(flattened[0]==0x30 && flattened[19]==0x30,"Deity rows not declared before status");
        // New repository on the same saved connection must restore the exact
        // selected row and both complete instance byte sequences.
        auto reopened=f.repo();RecoveredOwnedCompanions restarted(reopened);
        require(restarted.restore(1,c)==frames && reopened.load_deity_selection(1,c)->key==102,"Reload lost owned state");
        // Migrate populated schema36: same saved bytes, provenance and revision.
        Fixture old(true);auto oldrepo=old.repo();oldrepo.provision_pet2_slots(1,old.character);
        oldrepo.store_pet2(1,old.character,42,pet(old.character,42,28001),1,provenance());
        const auto old42=old.slot(42),old43=old.slot(43);
        SqliteMigrationManager(old.db.get(),default_sqlite_migrations()).migrate();
        require(raw(old.slot(42))==raw(old42) && old.slot(42).revision==old42.revision && old.slot(42).provenance==old42.provenance &&
            raw(old.slot(43))==raw(old43) && old.slot(43).revision==old43.revision,"Schema37 changed old owned instances");
        old.sql("INSERT INTO native_pet1_metadata VALUES('COM',24001,'70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731',1,X'41','aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa',zeroblob(396))");
        RecoveredOwnedCompanions mixed(oldrepo);
        oldrepo.store_pet1(1,old.character,43,pet1(old.character,43),1,provenance());
        require(old.slot(43).pet1 && !old.slot(43).pet && oldrepo.load_pet2_slots(1,old.character).size()==3,"Pet1 allocated overlapping capacity");
        auto wrong=pet1(old.character,43);wrong.inventory[2]=34;
        rejects([&]{oldrepo.store_pet1(1,old.character,43,wrong,2,provenance());});
        auto absentBytes=RecoveredPet1Stats::encode_logical(pet1(old.character,43).stats);absentBytes[0x1d]=0xc2;
        auto absent=pet1(old.character,43);absent.inventory[0]=0xc2;absent.stats=*RecoveredPet1Stats::parse_logical(absentBytes);
        rejects([&]{oldrepo.store_pet1(1,old.character,43,absent,2,provenance());});
        rejects([&]{oldrepo.store_pet1(2,old.character,43,pet1(old.character,43),2,provenance());});
        require(!mixed.select_pet2(1,old.character,{28001,43}),"Mixed source key spoof accepted");
        require(mixed.select_pet2(1,old.character,{24001,43}).has_value(),"E3 reserve selection failed");
        require(old.slot(44).pet1 && !old.slot(43).occupied(),"E3 active ownership missing");
        require(mixed.select_pet2(1,old.character,{28001,42}).has_value(),"FB/E3 active swap failed");
        require(old.slot(44).pet && old.slot(42).pet1,"Mixed swap lost generation");
        auto saved1=RecoveredPet1Stats::encode_logical(pet1(old.character,43).stats);saved1[0x27]=42;
        require(raw(old.slot(42))==std::vector<std::uint8_t>(saved1.begin(),saved1.end()),"Mixed swap changed E3 opaque data");
        const auto beforeMixed=mixed.restore(1,old.character);const auto prior42=raw(old.slot(42));
        old.sql("CREATE TRIGGER fail_mixed AFTER UPDATE ON character_pet2_slots WHEN NEW.slot=44 BEGIN SELECT RAISE(ABORT,'injected'); END");
        rejects([&]{mixed.select_pet2(1,old.character,{24001,42});});
        require(mixed.restore(1,old.character)==beforeMixed && raw(old.slot(42))==prior42,"Mixed failure partially committed");
        old.sql("DROP TRIGGER fail_mixed");
        require(mixed.select_pet2(1,old.character,{28001,44}).has_value(),"FB return from mixed failed");
        require(mixed.select_pet2(1,old.character,{24001,42}).has_value(),"E3 reselection failed");
        require(mixed.select_pet2(1,old.character,{24001,44}).has_value(),"E3 return failed");
        require(old.slot(42).pet1 && old.slot(43).pet && !old.slot(44).occupied(),"Mixed return overwrote occupied reserve");
        const auto mixedFrames=mixed.restore(1,old.character);auto mixedRepo=old.repo();
        require(RecoveredOwnedCompanions(mixedRepo).restore(1,old.character)==mixedFrames,"Mixed reload changed projection");
        std::cout<<"Owned deity/pet2 transactions, projections, rollback, ownership, pending battle and reload passed\n";
        return 0;
    } catch(const std::exception& error){std::cerr<<error.what()<<'\n';return 1;}
}
