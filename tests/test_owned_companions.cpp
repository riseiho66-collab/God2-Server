#include "handlers/RecoveredOwnedCompanions.h"
#include "handlers/RecoveredOwnedPetReserveMove.h"
#include "handlers/RecoveredMovementService.h"
#include "db/SqliteMigrationManager.h"
#include "db/SqliteRecoveredCharacterRepository.h"
#include "db/SqliteSupport.h"
#include <algorithm>
#include <array>
#include <iostream>
#include <memory>
#include <stdexcept>
#include <string>
#include <string_view>
#include <vector>
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
// Synthetic definition bytes qualify only this pure expected-prefix fixture;
// they are never imported, digest-checked or treated as native gameplay proof.
NativeSkillRecord prefix_definition(std::uint8_t id=1) {
    NativeSkillRecord value;
    value.source={native_taiwan_historical_dataset_id,"test-only/prefix.bin",
        TaiwanNativeDeityRosterPrefix::historical_catalog_sha256,
        TaiwanNativeDeityRosterPrefix::historical_catalog_sha256,
        "149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763",
        "test-only","0x1","0x2",448};
    value.source_record_index=id-1;value.source_offset=8+(id-1)*110;value.record_sha256=std::string(64,'a');
    value.raw_record.assign(110,0);value.raw_record[0]=id;value.definition_id=id;
    return value;
}
// Synthetic saved material for the selection-only repository contract. These
// bytes are not imported client definitions or a native learning entitlement.
// The private Restoration and selection commits still come from real issuers.
struct LearningSelectionFixture:Fixture {
    SqliteAccountRepository accounts{db.get()};
    SqliteRecoveredCharacterRepository characters{db.get()};
    SqliteCompanionRepository companions{db.get()};
    SqliteOwnedInventoryRepository inventory{db.get(),accounts,characters};
    SqliteNativeEquipmentSnapshotRepository equipment{db.get(),accounts,characters};
    NativeSkillBookCatalog books{db.get()};
    NativeSkillCatalog skills{db.get()};
    SqliteSkillBookLearningRepository learning{inventory,equipment,companions,books,skills};
    RecoveredOwnedCompanions helper{companions};
    LearningSelectionFixture() {
        sqlite_detail::execute(db.get(),SqliteOwnedInventoryRepository::schema());
        sqlite_detail::execute(db.get(),SqliteNativeEquipmentSnapshotRepository::schema());
        sqlite_detail::execute(db.get(),SqliteSkillBookLearningRepository::schema());
        for(unsigned key=1;key<=16;++key) {
            sqlite_detail::Statement metadata(db.get(),"INSERT INTO native_companion_metadata VALUES('GOD',?,?,1,X'41',?,zeroblob(396))");
            metadata.bind(1,2800+key);metadata.bind(2,std::string(SqliteCompanionRepository::source_sha256));
            metadata.bind(3,std::string(64,'a'));metadata.done();
            companions.store_deity(1,character,deity(static_cast<std::uint8_t>(key)),{},provenance());
        }
        const auto root=characters.list_for_account(1).front();
        const auto position=characters.commit_position(1,character,{},1,1,18,14);
        std::vector<std::uint8_t> alias_bytes(20,0x5a);alias_bytes[0]=0x65;alias_bytes[1]=0x19;
        OwnedItemNativeAlias alias{NativeEquipmentSnapshot::client_pin,"tw149c-item20",std::string(64,'b'),
            "fixture-book-alias",6501,0,1,alias_bytes};
        OwnedInventoryInstance item{9001,6501,2,1,true,std::string(64,'c'),"fixture-acquisition",{alias}};
        OwnedInventorySnapshot bag{root,1,std::string(64,'d'),"fixture-full-inventory",
            {{"bag",0,item},{"bag",1,std::nullopt},{"storage",7,std::nullopt}}};
        require(inventory.replace_from_issuer({},bag,[&](const auto&,const auto&,auto){return std::optional{bag};}).has_value(),
            "Full inventory fixture issuer failed");
        NativeEquipmentSnapshot worn{root,position,NativeEquipmentSnapshot::client_pin,NativeEquipmentSnapshot::kind,
            std::string(64,'e'),"fixture-full-equipment",std::vector<std::uint8_t>(NativeEquipmentSnapshot::record_bytes),1,41};
        worn.record[0]=2;worn.record[1]=0xa5;worn.record[2]=0x5a;worn.record[3]=0xc3;
        std::copy(alias_bytes.begin(),alias_bytes.end(),worn.record.begin()+4);
        worn.record[24+1]=0xf1; // Retain opaque bytes even in an empty native bank row.
        worn.record[1200]=0xda;worn.record[1201]=41;worn.record[1205]=0xb7;worn.record[1214]=0x82;
        require(equipment.replace_from_issuer({},worn,[&](const auto&,const auto&,auto){return std::optional{worn};}).has_value(),
            "Full equipment fixture issuer failed");
        // CUSTOM_TEST_NOT_NATIVE raw activation seed, not a learning commit.
        // A digest-consistent synthetic book supports the existing activation
        // reader. This does not qualify observe/plan/commit or native skill rules.
        sql("INSERT INTO native_data_sources VALUES('current-skill-catalog-v1','fixture-only/skill.bin','aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa','aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa','149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763','fixture-only','0x1','0x2',448)");
        sql("INSERT INTO native_data_sources VALUES('current-skill-books-v1','Data2/Patch/Comm/gamedata.csvZ','70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731','75c3c37947a64b0917fbf8e546884d9bf893fe6a606d3e2b8f3b1857966b1815','149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763','SKB','0x59420','0xA8E10',381)");
        std::array<std::uint8_t,110> definition{};definition[0]=1;
        {
            sqlite_detail::Statement row(db.get(),"INSERT INTO native_skill_catalog VALUES('current-skill-catalog-v1',0,8,?, ?,0,1)");
            row.bind(1,std::string(64,'a'));row.bind_blob(2,definition);row.done();
        }
        sql("INSERT INTO native_skill_books VALUES('current-skill-books-v1',0,1,0,6501,'559aead08264d5795d3909718cdd05abd49572e84fe55590eef31a88a08fdffd',X'41','58553b15fb3888e443e29fff5663675b8f70e37f0ea6c54076489d6ff04c1032',zeroblob(396))");
        sql("INSERT INTO native_skill_book_bindings VALUES('current-skill-books-v1','current-skill-catalog-v1',0,1,6501)");
        const auto saved=companions.load_deities(1,character).front();
        std::vector<std::uint8_t> row_bytes;
        const auto append=[&](const auto& bytes){row_bytes.insert(row_bytes.end(),bytes.begin(),bytes.end());};
        append(saved.snapshot.declaration.encode());append(saved.snapshot.status.encode());
        for(const auto& skill:saved.snapshot.skills)append(skill.encode());
        {
            sqlite_detail::Statement header(db.get(),"INSERT INTO deity_skill_activation_headers VALUES(?,1,?,?,?, ?,?,'CUSTOM-0148')");
            header.bind_id(1,character);header.bind_id(2,saved.revision);header.bind_blob(3,row_bytes);
            header.bind(4,saved.provenance.source_sha256);header.bind(5,saved.provenance.authority);
            header.bind(6,saved.provenance.evidence_id);header.done();
        }
        {
            sqlite_detail::Statement event(db.get(),"INSERT INTO skill_book_learning_events VALUES('CUSTOM_TEST_NOT_NATIVE:fixture-activation',1,?,1,0,1,6501,9001,1,1,?,'559aead08264d5795d3909718cdd05abd49572e84fe55590eef31a88a08fdffd','58553b15fb3888e443e29fff5663675b8f70e37f0ea6c54076489d6ff04c1032',X'41',zeroblob(396),'CUSTOM-0148')");
            event.bind_id(1,character);event.bind(2,std::string(SqliteCompanionRepository::source_sha256));event.done();
            sqlite_detail::Statement link(db.get(),"INSERT INTO deity_skill_activation_links VALUES(?,1,0,'CUSTOM_TEST_NOT_NATIVE:fixture-activation')");
            link.bind_id(1,character);link.done();
        }
    }
    std::vector<std::string> activation_storage() {
        // Hidden header/event fields must remain byte-for-byte stable as well
        // as the public activation list. Ordered text/hex projection is test-only.
        sqlite_detail::Statement rows(db.get(),"SELECT printf('%lld|%lld|%s|%s|%s|%s|%s',row_key,deity_revision,hex(raw_row),source_sha256,authority,evidence_id,design) FROM deity_skill_activation_headers ORDER BY row_key");
        std::vector<std::string> result;while(rows.row())result.push_back(rows.text(0));
        sqlite_detail::Statement events(db.get(),"SELECT printf('%s|%lld|%lld|%lld|%lld|%lld|%lld|%lld|%lld|%lld|%s|%s|%s|%s|%s|%s',event_id,account_id,character_id,row_key,kind,skill_id,book_item,book_instance,book_revision,deity_before_revision,book_source,record_sha256,parsed_sha256,hex(raw_book),hex(parsed_book),design) FROM skill_book_learning_events ORDER BY event_id");
        while(events.row())result.push_back(events.text(0));
        sqlite_detail::Statement links(db.get(),"SELECT printf('%lld|%lld|%lld|%s',character_id,row_key,ordinal,event_id) FROM deity_skill_activation_links ORDER BY character_id,row_key,ordinal");
        while(links.row())result.push_back(links.text(0));return result;
    }
};
// Synthetic book events from LearningSelectionFixture remain test-only.
// This exercises the actual trusted import -> existing activation persistence
// -> fresh restoration chain, not a fabricated first-skill/native-growth grant.
void status_activation_lineage_regression() {
    const auto changed_status=[](RecoveredDeityState::Snapshot row) {
        auto status=row.status.encode();status[8]^=0x51;
        row.status=*RecoveredDeityState::Status::parse(status);return row;
    };
    for(const bool selected:{true,false}) {
        LearningSelectionFixture f;
        if(!selected)require(f.helper.select_deity_with_source(1,f.character,{2}).has_value(),"Alternate selection failed");
        const auto before=f.learning.restore(1,f.character);
        const auto old=before.roster().rows().front();
        const auto selection=f.companions.load_deity_selection(1,f.character);
        const auto original=f.activation_storage();
        require(before.activations().size()==1,"Initial book activation missing");
        const auto chosen=f.companions.load_selected_deity_skill(1,f.character,0,1);
        require(chosen.has_value(),"Selected learned source missing");
        const auto imported=f.companions.store_deity(1,f.character,changed_status(old.snapshot),old.revision,old.provenance);
        require(imported.revision==old.revision+1,"Status-only import did not advance revision");
        require(!f.learning.restoration_current(before),"Old full learning source revived after status import");
        if(selected)require(!f.companions.selected_deity_skill_current(*chosen),"Old selected skill source survived changed row");
        const auto after=f.learning.restore(1,f.character);
        const auto actual=f.activation_storage();
        require(after.activations()==before.activations() && after.inventory()==before.inventory() &&
            after.equipment()==before.equipment(),"Status-only import lost book events or altered inventory/equipment");
        require(actual.size()==original.size() && actual.front()!=original.front() &&
            std::equal(original.begin()+1,original.end(),actual.begin()+1),"Status continuation rewrote original book event/link inputs");
        require(f.companions.load_deity_selection(1,f.character)==selection,"Status import silently selected another deity");
        const auto saved=f.helper.restore_with_source(1,f.character,f.learning);
        require(saved.learning_source() && saved.learning_source()->activations()==before.activations() &&
            f.helper.restoration_current(saved),"Fresh owned restoration did not carry exact activation");
        rejects([&]{f.companions.store_deity(1,f.character,old.snapshot,old.revision,old.provenance);});
        require(f.activation_storage()==actual,"Stale reimport changed activation lineage");
        // An idempotent trusted reimport still advances its epoch, preserving
        // the original event once without duplicating or granting a new skill.
        f.companions.store_deity(1,f.character,imported.snapshot,imported.revision,imported.provenance);
        const auto twice=f.learning.restore(1,f.character);
        require(twice.activations()==before.activations(),"Repeated status import duplicated or lost activation");
    }
    for(unsigned fault=0;fault<8;++fault) {
        LearningSelectionFixture f;
        const auto old=f.companions.load_deities(1,f.character).front();
        auto next=changed_status(old.snapshot);auto origin=old.provenance;
        switch(fault) {
        case 0:f.sql("UPDATE deity_skill_activation_headers SET deity_revision=2 WHERE row_key=1");break;
        case 1:{
            std::vector<std::uint8_t> raw;
            const auto append=[&](const auto& bytes){raw.insert(raw.end(),bytes.begin(),bytes.end());};
            append(old.snapshot.declaration.encode());append(old.snapshot.status.encode());
            for(const auto& skill:old.snapshot.skills)append(skill.encode());raw[21]^=0x31;
            sqlite_detail::Statement update(f.db.get(),"UPDATE deity_skill_activation_headers SET raw_row=? WHERE row_key=1");
            update.bind_blob(1,raw);update.done();break;
        }
        case 2:origin.evidence_id+=";different-import";break;
        case 3:{auto d=next.declaration.encode();d[2]='B';next.declaration=*RecoveredDeityState::Declaration::parse(d);break;}
        case 4:next.skills.push_back(*RecoveredDeityState::Skill::parse(std::array<std::uint8_t,4>{0x34,1,0,2}));break;
        case 5:next.skills.clear();break;
        case 6:f.sql("DELETE FROM deity_skill_activation_links WHERE row_key=1;DELETE FROM deity_skill_activation_headers WHERE row_key=1");break;
        default:f.sql("UPDATE deity_skill_activation_headers SET evidence_id='foreign-header-provenance' WHERE row_key=1");break;
        }
        const auto original=f.activation_storage();
        auto imported=f.companions.store_deity(1,f.character,next,old.revision,origin);
        require(f.activation_storage()==original,"Changed or stale header was adopted by an import");
        require(f.learning.restore(1,f.character).activations().empty(),"Import fabricated or revived inactive book entitlement");
        // Putting an old snapshot back with the CURRENT revision cannot rebase
        // a stale header, even after another same-status revision change.
        imported=f.companions.store_deity(1,f.character,old.snapshot,imported.revision,old.provenance);
        f.companions.store_deity(1,f.character,changed_status(imported.snapshot),imported.revision,imported.provenance);
        require(f.learning.restore(1,f.character).activations().empty() && f.activation_storage()==original,
            "Reimported prior deity revived an old activation header");
    }
    {
        LearningSelectionFixture f;
        const auto before=f.learning.restore(1,f.character),old=before;
        const auto deity_before=before.roster().rows().front();const auto original=f.activation_storage();
        rejects([&]{f.companions.store_deity(2,f.character,changed_status(deity_before.snapshot),deity_before.revision,deity_before.provenance);});
        require(f.activation_storage()==original && f.learning.restoration_current(old),"Foreign account changed book entitlement");
        // Reject the header UPDATE after the deity row has been staged. Both
        // writes must roll back together; no repaired source token is issued.
        sqlite3_set_authorizer(f.db.get(),[](void*,int action,const char* table,const char*,const char*,const char*) {
            return action==SQLITE_UPDATE && table && std::string_view(table)=="deity_skill_activation_headers"?SQLITE_DENY:SQLITE_OK;
        },nullptr);
        rejects([&]{f.companions.store_deity(1,f.character,changed_status(deity_before.snapshot),deity_before.revision,deity_before.provenance);});
        sqlite3_set_authorizer(f.db.get(),nullptr,nullptr);
        require(f.activation_storage()==original && f.learning.restoration_current(before) &&
            f.companions.load_deities(1,f.character).front().revision==deity_before.revision,
            "Header rejection committed only the deity half of the status update");
    }
    {
        LearningSelectionFixture f;auto old=f.companions.load_deities(1,f.character).front();
        auto pair=old.snapshot;pair.skills.push_back(*RecoveredDeityState::Skill::parse(std::array<std::uint8_t,4>{0x34,1,0,2}));
        old=f.companions.store_deity(1,f.character,pair,old.revision,old.provenance);
        // Explicit synthetic header setup isolates an ordered-skill rejection.
        std::vector<std::uint8_t> raw;
        const auto append=[&](const auto& bytes){raw.insert(raw.end(),bytes.begin(),bytes.end());};
        append(old.snapshot.declaration.encode());append(old.snapshot.status.encode());
        for(const auto& skill:old.snapshot.skills)append(skill.encode());
        sqlite_detail::Statement header(f.db.get(),"UPDATE deity_skill_activation_headers SET raw_row=?,deity_revision=? WHERE row_key=1");
        header.bind_blob(1,raw);header.bind_id(2,old.revision);header.done();
        require(f.learning.restore(1,f.character).activations().size()==1,"Ordered-skill fixture has no activation");
        const auto storage=f.activation_storage();std::swap(pair.skills[0],pair.skills[1]);
        f.companions.store_deity(1,f.character,pair,old.revision,old.provenance);
        require(f.activation_storage()==storage && f.learning.restore(1,f.character).activations().empty(),
            "Skill order change carried a different full-row witness");
    }
    {
        LearningSelectionFixture f;const auto old=f.companions.load_deities(1,f.character).front();
        const auto before=f.learning.restore(1,f.character);const auto storage=f.activation_storage();
        struct Probe {LearningSelectionFixture* f;const StoredDeity* row;bool attempted=false,rejected=false;} probe{&f,&old};
        sqlite3_set_authorizer(f.db.get(),[](void* context,int action,const char* table,const char*,const char*,const char*) {
            auto& p=*static_cast<Probe*>(context);
            if(!p.attempted && action==SQLITE_READ && table && std::string_view(table)=="native_companion_metadata") {
                p.attempted=true;
                try {p.f->companions.store_deity(1,p.f->character,p.row->snapshot,p.row->revision,p.row->provenance);}
                catch(...) {p.rejected=true;}
            }
            return SQLITE_OK;
        },&probe);
        rejects([&]{f.companions.store_deity(1,f.character,changed_status(old.snapshot),old.revision,old.provenance);});
        sqlite3_set_authorizer(f.db.get(),nullptr,nullptr);
        require(probe.attempted && probe.rejected && f.activation_storage()==storage && f.learning.restoration_current(before),
            "Caught nested writer reentry did not invalidate the outer import");
    }
    {
        LearningSelectionFixture f;const auto old=f.companions.load_deities(1,f.character).front();
        auto input=changed_status(old.snapshot);auto origin=old.provenance;
        struct Probe {RecoveredDeityState::Snapshot* input;CompanionProvenance* origin;bool changed=false;} probe{&input,&origin};
        sqlite3_set_authorizer(f.db.get(),[](void* context,int action,const char* table,const char*,const char*,const char*) {
            auto& p=*static_cast<Probe*>(context);
            if(!p.changed && action==SQLITE_READ && table && std::string_view(table)=="native_companion_metadata") {
                p.changed=true;p.input->skills.clear();p.origin->evidence_id="observer-replaced-caller";
            }
            return SQLITE_OK;
        },&probe);
        const auto saved=f.companions.store_deity(1,f.character,input,old.revision,origin);
        sqlite3_set_authorizer(f.db.get(),nullptr,nullptr);
        require(probe.changed && input.skills.empty() && saved.snapshot.skills.size()==old.snapshot.skills.size() &&
            saved.provenance==old.provenance && f.learning.restore(1,f.character).activations().size()==1,
            "Import adopted callback-mutated caller inputs instead of its owned values");
    }
    for(const bool shadow:{true,false}) {
        LearningSelectionFixture f;const auto old=f.companions.load_deities(1,f.character).front();
        const auto original=f.activation_storage();
        if(shadow)f.sql("CREATE TEMP TABLE deity_skill_activation_headers(dummy)");
        else f.sql("CREATE TRIGGER activation_import_effect AFTER UPDATE ON deity_skill_activation_headers BEGIN SELECT 1; END");
        rejects([&]{f.companions.store_deity(1,f.character,changed_status(old.snapshot),old.revision,old.provenance);});
        if(shadow)f.sql("DROP TABLE temp.deity_skill_activation_headers");
        else f.sql("DROP TRIGGER activation_import_effect");
        require(f.activation_storage()==original && f.companions.load_deities(1,f.character).front().revision==old.revision,
            "Shadow/trigger refusal left a partial status update");
    }
}

void joint_material_successor_regression() {
    LearningSelectionFixture f;
    const auto before=f.helper.restore_with_source(1,f.character,f.learning);
    const auto activation=f.activation_storage();
    SqliteOwnedEquipmentTransaction joint(f.inventory,f.equipment);
    const auto observed=joint.observe_before(1,f.character);require(observed && observed->inventory && observed->equipment,"Actual joint fixture before");
    SqliteOwnedEquipmentTransaction::State next{*observed->inventory,*observed->equipment};
    std::swap(next.inventory.cells[0].instance,next.inventory.cells[1].instance);
    auto& moved=*next.inventory.cells[1].instance;++moved.revision;
    moved.aliases[0].native_slot=1;moved.aliases[0].revision=moved.revision;
    next.equipment.record[0]=next.equipment.record[4]=next.equipment.record[5]=0;
    next.equipment.record[24]=static_cast<std::uint8_t>(moved.quantity);
    std::copy(moved.aliases[0].record.begin(),moved.aliases[0].record.end(),next.equipment.record.begin()+28);
    ++next.inventory.revision;++next.equipment.revision;
    // Synthetic source-only issuer exercises custody-edge continuation. It is
    // not a real native bank/capacity/acquisition or Written Session fixture.
    const auto saved=joint.replace_from_issuer(*observed,next,
        [](const auto&,const auto& proposed,auto){return std::optional{proposed};});
    require(saved && !f.helper.restoration_current(before),"Joint material mutation must retire old complete restoration");
    require(joint.committed_predecessor_matches(*saved,before.learning_source()->inventory(),before.learning_source()->equipment()),
        "Actual mutation must retain its exact complete predecessor");
    const auto read_only=joint.observe_committed(1,f.character);
    require(read_only && !joint.committed_predecessor_matches(*read_only,before.learning_source()->inventory(),before.learning_source()->equipment()) &&
        !f.helper.material_successor_from_committed(before,joint,*read_only),"Observation cannot be relabeled a mutation successor");
    SqliteOwnedEquipmentTransaction foreign(f.inventory,f.equipment);
    require(!f.helper.material_successor_from_committed(before,foreign,*saved),"Same writers do not supply another joint identity's mutation edge");
    const auto fresh=f.helper.restore_with_source(1,f.character,f.learning);
    require(!f.helper.material_successor_from_committed(fresh,joint,*saved),"Fresh after observation cannot replace exact committed before");
    const auto after=f.helper.material_successor_from_committed(before,joint,*saved);
    require(after && after->learning_source() && f.helper.restoration_current(*after) &&
        after->learning_source()->inventory()==next.inventory && after->learning_source()->equipment()==next.equipment &&
        after->batches()==before.batches() && after->deity_roster().selection()==before.deity_roster().selection() &&
        after->learning_source()->activations()==before.learning_source()->activations() && f.activation_storage()==activation,
        "Material successor must retain actual deity/activation/history bytes without restoration replay");
    const auto selected=f.helper.select_deity_with_source(1,f.character,{2});require(selected.has_value(),"Real selection after material continuation");
    const std::array publications{selected->publication()};
    const auto selection_after=f.helper.selection_successor_from_committed(*after,publications);
    require(selection_after && f.helper.restoration_current(*selection_after),"Material continuation must permit subsequent genuine C67 successor");
    const auto movement_before=joint.observe_before(1,f.character);require(movement_before.has_value(),"Current actual movement material");
    const auto walk=joint.move_position_from_current(*movement_before,next.equipment.actor_handle,19,14,[]{return true;});
    require(walk.has_value(),"Isolated permitted ordinary movement");
    const auto second_move_before=joint.observe_before(1,f.character);require(second_move_before.has_value(),"Second move exact predecessor");
    const auto walk2=joint.move_position_from_current(*second_move_before,next.equipment.actor_handle,20,14,[]{return true;});
    require(walk2.has_value(),"Second actual material mutation in one callback-style chain");
    const std::array<const SqliteOwnedEquipmentTransaction::Committed*,2> moves{&*walk,&*walk2},reversed{&*walk2,&*walk};
    const std::array<const SqliteOwnedEquipmentTransaction::Committed*,1> skipped{&*walk2};
    require(!f.helper.material_successor_from_committed(*selection_after,joint,*walk) &&
        !f.helper.material_successor_from_committed_chain(*selection_after,joint,reversed) &&
        !f.helper.material_successor_from_committed_chain(*selection_after,joint,skipped),
        "Consumed intermediate, reversed or skipped private edge cannot be a current material successor");
    const auto walked=f.helper.material_successor_from_committed_chain(*selection_after,joint,moves);
    require(walked && f.helper.restoration_current(*walked) && walked->learning_source()->equipment().position.x==20 &&
        walked->batches()==selection_after->batches() && f.activation_storage()==activation,
        "Real ordinary movement edge may advance saved pose without replaying/deleting companion history");
    require(!f.helper.material_successor_from_committed_chain(before,joint,moves),"Cannot skip the actual material/selection predecessor");
}
void learning_selection_source_regression() {
    // Each after-state fault owns an isolated source; none is repaired in order
    // to revive a stale token. No test-only constructor mints private receipts.
    for(unsigned fault=0;fault<=5;++fault) {
        LearningSelectionFixture f;
        const auto before=f.helper.restore_with_source(1,f.character,f.learning);
        require(before.learning_source()&&before.deity_roster().rows().size()==16&&
            before.learning_source()->activations().size()==1,"Full learning restoration fixture missing active lineage");
        require(f.helper.restoration_current(before),"Initial full learning fixture is stale");
        auto foreign_companions=f.repo();
        SqliteSkillBookLearningRepository foreign_roster(f.inventory,f.equipment,foreign_companions,f.books,f.skills);
        const auto foreign_before=foreign_roster.restore(1,f.character);
        const auto original_storage=f.activation_storage();
        auto first=f.helper.select_deity_with_source(1,f.character,{2});
        auto second=f.helper.select_deity_with_source(1,f.character,{16});
        require(first&&second,"Private selection chain missing from learning fixture");
        const std::array publications{first->publication(),second->publication()};
        const std::array<const SqliteCompanionRepository::CommittedDeitySelection*,2> commits{&first->committed(),&second->committed()};
        require(!f.learning.restoration_current(*before.learning_source()),"Consumed full before State remained Current");
        const std::array<const SqliteCompanionRepository::CommittedDeitySelection*,2> reversed{commits[1],commits[0]},duplicated{commits[0],commits[0]},missing{commits[0],nullptr};
        require(!f.learning.selection_successor(*before.learning_source(),reversed)&&
            !f.learning.selection_successor(*before.learning_source(),duplicated)&&
            !f.learning.selection_successor(*before.learning_source(),missing)&&
            !f.learning.selection_successor(*before.learning_source(),{}),"Invalid selection chain adopted full learning State");
        SqliteSkillBookLearningRepository foreign(f.inventory,f.equipment,f.companions,f.books,f.skills);
        require(!foreign.selection_successor(*before.learning_source(),commits),"Same connection borrowed another learning issuer");
        require(!foreign_roster.selection_successor(foreign_before,commits),"Other roster issuer borrowed private selection commits");
        const auto after=f.learning.selection_successor(*before.learning_source(),commits);
        const auto restored=f.helper.selection_successor_from_committed(before,publications);
        require(after&&restored&&restored->learning_source()&&f.learning.restoration_current(*after)&&
            f.helper.restoration_current(*restored),"Selection failed to retain full learning source");
        require(after->inventory()==before.learning_source()->inventory()&&
            after->equipment()==before.learning_source()->equipment()&&
            after->activations()==before.learning_source()->activations()&&f.activation_storage()==original_storage,
            "Selection modified inventory/equipment or activation header/event/link material");
        require(after->roster().selection()==std::optional{second->committed().after()}&&
            after->roster().rows().size()==16&&after->roster().template_keys()==before.deity_roster().template_keys(),
            "Selection lost complete roster ownership");
        for(std::size_t i=0;i<16;++i) {
            const auto& old=before.deity_roster().rows()[i];const auto& next=after->roster().rows()[i];
            require(old.revision==next.revision&&old.provenance==next.provenance&&
                old.snapshot.declaration.encode()==next.snapshot.declaration.encode()&&
                old.snapshot.status.encode()==next.snapshot.status.encode()&&old.snapshot.skills.size()==next.snapshot.skills.size(),
                "Selection changed a full saved deity row");
            for(std::size_t j=0;j<old.snapshot.skills.size();++j)require(old.snapshot.skills[j].encode()==next.snapshot.skills[j].encode(),
                "Selection changed saved learned skill bytes");
        }
        require(restored->batches().size()==before.batches().size()+2,"Selection replayed complete restoration");
        for(std::size_t i=0;i<before.batches().size();++i)require(restored->batches()[i]==before.batches()[i],
            "Selection changed original S30/S34/S35 restoration history");
        for(std::size_t i=0;i<2;++i) {
            const auto logical=RecoveredWorldFrame::decode(publications[i].wire());
            require(logical&&restored->batches()[before.batches().size()+i]==*logical,
                "Selection history did not append actual private S31 in order");
        }
        require(!f.learning.restoration_current(*before.learning_source()),"Successor revived consumed before State");
        // Every negative starts from its own proven-current positive successor.
        switch(fault) {
        case 1:f.sql("UPDATE owned_inventory_headers SET source_record='changed-inventory-source'");break;
        case 2:f.sql("UPDATE character_native_equipment_snapshots SET source_record='changed-equipment-source'");break;
        case 3:f.sql("UPDATE deity_skill_activation_headers SET evidence_id='changed-header-evidence'");break;
        case 4:f.sql("UPDATE skill_book_learning_events SET book_revision=2");break;
        case 5:{auto row=deity(3);auto status=row.status.encode();status[8]=77;row.status=*RecoveredDeityState::Status::parse(status);
            f.companions.store_deity(1,f.character,row,1,provenance());break;}
        default:break;
        }
        if(fault) {
            require(!f.learning.restoration_current(*after)&&!f.helper.restoration_current(*restored)&&
                !f.learning.selection_successor(*before.learning_source(),commits)&&
                !f.helper.selection_successor_from_committed(before,publications),
                "Changed complete after State escaped selection-only qualification");
            require(f.companions.load_deity_selection(1,f.character)==std::optional{second->committed().after()},
                "Failed source qualification changed durable selection");
        }
    }
}
void selection_source_regression() {
    Fixture f;auto repo=f.repo();RecoveredOwnedCompanions helper(repo);
    for(unsigned key=1;key<=16;++key) {
        sqlite_detail::Statement metadata(f.db.get(),"INSERT INTO native_companion_metadata VALUES('GOD',?,?,1,X'41',?,zeroblob(396))");
        metadata.bind(1,2800+key);metadata.bind(2,std::string(SqliteCompanionRepository::source_sha256));
        metadata.bind(3,std::string(64,'a'));metadata.done();
        repo.store_deity(1,f.character,deity(static_cast<std::uint8_t>(key)),{},provenance());
    }
    const auto before=helper.restore_with_source(1,f.character);
    require(before.deity_roster().rows().size()==16 && !before.deity_roster().selection(),"Full saved roster fixture missing");
    auto first=helper.select_deity_with_source(1,f.character,{2});
    auto second=helper.select_deity_with_source(1,f.character,{16});
    require(first&&second,"Actual selection commit chain missing");
    const std::array publications{first->publication(),second->publication()};
    require(second->committed().before()==std::optional{first->committed().after()},"Consecutive C67 did not chain selection revisions");
    const auto intermediate=repo.selection_roster_successor(before.deity_roster(),first->committed());
    const auto final=intermediate?repo.selection_roster_successor(*intermediate,second->committed()):std::nullopt;
    require(intermediate&&final&&!repo.deity_roster_current(before.deity_roster())&&
        !repo.deity_roster_current(*intermediate)&&repo.deity_roster_current(*final),"Consumed before selection was revived or final roster refused");
    const auto after=helper.selection_successor_from_committed(before,publications);
    require(after&&helper.restoration_current(*after)&&!helper.restoration_current(before),"Full restoration selection successor failed");
    require(after->deity_roster().selection()==std::optional{second->committed().after()}&&
        after->deity_roster().template_keys()==before.deity_roster().template_keys()&&
        after->deity_roster().rows().size()==16,"Selection changed full roster/template ownership");
    for(std::size_t i=0;i<16;++i) {
        const auto& a=before.deity_roster().rows()[i];const auto& b=after->deity_roster().rows()[i];
        require(a.revision==b.revision&&a.provenance==b.provenance&&
            a.snapshot.declaration.encode()==b.snapshot.declaration.encode()&&a.snapshot.status.encode()==b.snapshot.status.encode()&&
            a.snapshot.skills.size()==b.snapshot.skills.size()&&a.snapshot.skills.front().encode()==b.snapshot.skills.front().encode(),
            "Selection altered a saved row instead of its selector");
    }
    require(after->batches().size()==before.batches().size()+2,"Selection invented restoration batches");
    for(std::size_t i=0;i<before.batches().size();++i)require(before.batches()[i]==after->batches()[i],"Original S30/S34 history changed");
    for(std::size_t i=0;i<2;++i) {
        const auto& delta=after->batches()[before.batches().size()+i];
        const auto wire=RecoveredWorldFrame::decode(publications[i].wire());
        require(delta.size()==29&&delta[0]==0x31&&wire&&*wire==delta,"Selection replayed S30 or lost actual S31 order");
    }
    const std::array definitions{prefix_definition()};
    const auto prefix=TaiwanNativeDeityRosterPrefix::from_reset_and_records(before.batches(),definitions);
    const auto next=TaiwanNativeDeityRosterPrefix::from_reset_and_records(after->batches(),definitions);
    require(prefix&&next&&next->roster_count()==16&&next->rows()==prefix->rows()&&
        next->rows()[std::size_t(next->selected_row())].row_key==16,"S31 history changed physical roster/skill tails");
    for(const auto& row:next->rows()) {
        require(row.learned_definitions.size()==100&&row.auxiliary_definitions.size()==100,"Inactive tail capacity lost");
        for(std::size_t i=1;i<100;++i)require(!row.learned_definitions[i]&&!row.auxiliary_definitions[i]&&row.learned_flags[i]==0,
            "Selection fabricated inactive learned/auxiliary entries");
    }
    // Separate pure prefix case exercises nonzero inactive tails from actual
    // supported direct30/34/35 footprints; it mints no private Written source.
    std::vector<std::uint8_t> logical;
    const auto append=[&](const auto& bytes){logical.insert(logical.end(),bytes.begin(),bytes.end());};
    auto declaration=deity(101).declaration.encode();append(declaration);
    append(std::array<std::uint8_t,4>{0x34,101,0,1});append(std::array<std::uint8_t,4>{0x34,101,0,2});
    append(std::array<std::uint8_t,4>{0x35,101,0,1});append(std::array<std::uint8_t,4>{0x35,101,0,2});
    declaration[18]=1;append(declaration); // reset count only, preserving old physical tails
    append(std::array<std::uint8_t,4>{0x34,101,0,3});
    for(std::uint8_t key=1;key<=15;++key)append(deity(key).declaration.encode());
    const std::array tail_definitions{prefix_definition(1),prefix_definition(2),prefix_definition(3)};
    const std::array tail_history{logical};
    const auto tails=TaiwanNativeDeityRosterPrefix::from_reset_and_records(tail_history,tail_definitions,true);
    append(deity(1).status.encode());const std::array selected_history{logical};
    const auto selected_tails=TaiwanNativeDeityRosterPrefix::from_reset_and_records(selected_history,tail_definitions,true);
    require(tails&&selected_tails&&tails->roster_count()==16&&tails->rows()[0].learned_count==1&&
        tails->rows()[0].auxiliary_count==0&&tails->rows()[0].learned_definitions[1]&&
        tails->rows()[0].auxiliary_definitions[1]&&selected_tails->rows()==tails->rows()&&
        selected_tails->selected_row()==1,"S31 reset nonzero inactive learned/auxiliary tails or reordered16 rows");
    const std::array reversed{second->publication(),first->publication()};
    const std::array duplicated{first->publication(),first->publication()};
    require(!helper.selection_successor_from_committed(before,reversed)&&
        !helper.selection_successor_from_committed(before,duplicated),"Wrong C67 order/repeated commit adopted");
    auto foreign=f.repo();
    require(!foreign.selection_roster_successor(before.deity_roster(),first->committed()),"Equal DB connection borrowed another private issuer");
    auto other_profile=std::array<std::uint8_t,40>{};other_profile[0]='B';
    const auto other=f.roles().create(2,other_profile).id;
    repo.store_deity(2,other,deity(101),{},provenance());
    const auto other_before=repo.load_deity_roster(2,other);
    require(!repo.selection_roster_successor(other_before,first->committed()),"Other account/character borrowed commit chain");
    auto changed=deity(3);auto status=changed.status.encode();status[8]=77;changed.status=*RecoveredDeityState::Status::parse(status);
    repo.store_deity(1,f.character,changed,1,provenance());
    require(!helper.selection_successor_from_committed(before,publications),"Changed unselected full row escaped final restoration Current");
    require(repo.load_deity_selection(1,f.character)==std::optional{second->committed().after()},"Metadata refusal rolled back durable selection");
}
// SOURCE ONLY: exact pet namespace classification, actual two-cell CAS and
// pre/post-COMMIT truth. No game DB or native execution is authorized here.
void pet_selection_continuation_regression() {
    using Batch=RecoveredOwnedCompanions::PetSelectionBatch;
    const auto classify=[](std::vector<RecoveredWorldRecords::Record> records){return RecoveredOwnedCompanions::pet_selection_batch(records).kind;};
    const RecoveredSelectionItemRequest::Request pet_request{28001,42};
    require(classify({pet_request,RecoveredWorldRecords::Tick{},RecoveredWorldRecords::ClientControl1F{}})==Batch::Kind::Selection,"Pet batch with actual trailing control rejected");
    require(classify({RecoveredWorldRecords::ClientControl1F{},pet_request})==Batch::Kind::Rejected,"Control prefix entered pet route");
    require(classify({pet_request,pet_request})==Batch::Kind::Rejected,"Two pet writes entered one callback");
    require(classify({pet_request,RecoveredSelectionItemRequest::Request{28001,0}})==Batch::Kind::Rejected,"Pet/item namespace mixed batch escaped");
    require(classify({RecoveredMovement::Request{},pet_request})==Batch::Kind::Rejected,"Movement prefix entered pet route");
    require(classify({RecoveredSelectionItemRequest::Request{28001,0}})==Batch::Kind::Absent,"Ordinary item selection borrowed pet route");
    for(unsigned mode=0;mode<9;++mode) {
        Fixture f;auto repo=f.repo();RecoveredOwnedCompanions helper(repo);repo.provision_pet2_slots(1,f.character);
        repo.store_pet2(1,f.character,42,pet(f.character,42,28001),1,provenance());
        const auto before42=f.slot(42),before44=f.slot(44),before43=f.slot(43);
        struct Observe {sqlite3* db;SqliteCompanionRepository* repo;std::uint64_t character;StoredPet2Slot source,destination;
            unsigned mode,loads=0;bool live=true,fired=false,nested_rejected=false,wrote=false;int ddl=SQLITE_ERROR;} observed{f.db.get(),&repo,f.character,before42,before44,mode};
        const auto trace=[](unsigned type,void* context,void* statement,void*)->int {
            auto& o=*static_cast<Observe*>(context);
            const auto* raw_sql=sqlite3_sql(static_cast<sqlite3_stmt*>(statement));if(!raw_sql)return 0;const std::string_view sql(raw_sql);
            if(type==SQLITE_TRACE_PROFILE) {
                // PROFILE occurs after this COMMIT has finished; unlike STMT,
                // these cases exercise the actual durable-return cut.
                if((o.mode==6||o.mode==7)&&o.wrote&&sql=="COMMIT"&&!o.fired) {
                    o.fired=true;if(o.mode==6)o.live=false;
                    else sqlite3_exec(o.db,"UPDATE main.character_pet2_slots SET evidence_id='profile-observer-change' WHERE slot=43",nullptr,nullptr,nullptr);
                }
                return 0;
            }
            if(type!=SQLITE_TRACE_STMT)return 0;
            if(o.mode==8&&o.wrote&&o.loads==2&&!o.fired&&sql.starts_with("SELECT 1 FROM main.recovered_characters")){
                o.fired=true;
                o.ddl=sqlite3_exec(o.db,"ALTER TABLE main.character_pet2_slots RENAME TO replaced_pet_cells; CREATE TEMP VIEW character_pet2_slots AS SELECT * FROM main.replaced_pet_cells",nullptr,nullptr,nullptr);
            }
            if(sql.starts_with("SELECT slot,metadata,stats")){
                ++o.loads;if(o.loads==3&&(o.mode==0||o.mode==2)){
                    o.fired=true;if(o.mode==0)o.live=false;
                    else sqlite3_exec(o.db,"UPDATE character_pet2_slots SET evidence_id='unexpected-final-source' WHERE slot=43",nullptr,nullptr,nullptr);
                }
            }
            if(sql.starts_with("UPDATE main.character_pet2_slots"))o.wrote=true;
            if(o.mode==1&&o.wrote&&sql=="COMMIT"){o.live=false;o.fired=true;}
            if(o.mode==5&&o.wrote&&sql=="COMMIT"&&!o.fired){o.fired=true;
                sqlite3_exec(o.db,"UPDATE character_pet2_slots SET evidence_id='commit-observer-change' WHERE slot=43",nullptr,nullptr,nullptr);}
            if((o.mode==3||o.mode==4)&&!o.fired&&sql.starts_with("UPDATE main.character_pet2_slots")){
                o.fired=true;
                try{if(o.mode==3)(void)o.repo->transfer_pet2(1,o.character,o.source,o.destination);
                    else {SqliteCompanionRepository other(o.db);(void)other.transfer_pet2(1,o.character,o.source,o.destination);}}
                catch(const std::exception&){o.nested_rejected=true;}
            }
            return 0;
        };
        struct TraceEnd {sqlite3* db;~TraceEnd(){sqlite3_trace_v2(db,0,nullptr,nullptr);}} trace_end{f.db.get()};
        require(sqlite3_trace_v2(f.db.get(),SQLITE_TRACE_STMT|SQLITE_TRACE_PROFILE,trace,&observed)==SQLITE_OK,"Pet trace source installation failed");
        rejects([&]{(void)helper.select_pet2(1,f.character,pet_request,[&]{return observed.live;});});
        sqlite3_trace_v2(f.db.get(),0,nullptr,nullptr);
        require(observed.fired,"Pet final/commit/reentry observer did not reach its intended cut");
        if(mode==1||mode==5||mode==6||mode==7)require(!f.slot(42).occupied()&&f.slot(44).occupied(),"Post-COMMIT retirement falsely rolled back actual pet custody");
        else require(raw(f.slot(42))==raw(before42)&&f.slot(42).revision==before42.revision&&
            raw(f.slot(44))==raw(before44)&&f.slot(43).provenance==before43.provenance,"Pet precommit retirement leaked partial/cross-cell writes");
        if(mode==3||mode==4)require(observed.nested_rejected,"Caught pet reentry failed to poison the outer actual connection operation");
        if(mode==5)require(f.slot(43).provenance.evidence_id=="commit-observer-change","Durable COMMIT observer write was falsely described as rollback");
        if(mode==7)require(f.slot(43).provenance.evidence_id=="profile-observer-change","Successful COMMIT PROFILE write lost durable truth");
        if(mode==8)require(observed.ddl==SQLITE_OK,"Final owner-read DDL fixture did not reach its intended namespace replacement");
    }
    for(const char* claim:{"owned_pve_character_claims","owned_pk_room_members"}) {
        Fixture f;auto repo=f.repo();RecoveredOwnedCompanions helper(repo);repo.provision_pet2_slots(1,f.character);
        repo.store_pet2(1,f.character,42,pet(f.character,42,28001),1,provenance());
        const auto table=std::string("CREATE TABLE ")+claim+"(character INTEGER PRIMARY KEY)";f.sql(table.c_str());
        const auto insert=std::string("INSERT INTO ")+claim+" VALUES("+std::to_string(f.character)+")";f.sql(insert.c_str());
        rejects([&]{(void)helper.select_pet2(1,f.character,pet_request,[]{return true;});});
        require(f.slot(42).occupied()&&!f.slot(44).occupied(),"Retained room claim allowed pet ownership change");
    }
    LearningSelectionFixture f;const auto original=f.helper.restore_with_source(1,f.character,f.learning);
    f.companions.provision_pet2_slots(1,f.character);f.companions.store_pet2(1,f.character,42,pet(f.character,42,28001),1,provenance());
    require(f.helper.select_pet2(1,f.character,pet_request,[]{return true;}).has_value()&&
        f.learning.restoration_current(*original.learning_source()),"Pet activation retired the unrelated complete learning/material graph");
    f.companions.store_pet2(1,f.character,42,pet(f.character,42,28001),f.slot(42).revision,provenance());
    require(RecoveredOwnedPetReserveMove::move(f.companions,1,f.character,{42,43},[]{return true;}).has_value()&&
        f.learning.restoration_current(*original.learning_source()),"Pet reserve reorder retired the unrelated complete learning/material graph");
}
void deity_selection_live_source_regression() {
    // Actual movement bindings and selection repositories; no Session Written
    // receipt is invented by these focused storage/helper SOURCE cases.
    for(unsigned mode=1;mode<=5;++mode) {
        LearningSelectionFixture f;
        const auto old_position=f.characters.load_position(1,f.character);
        f.characters.commit_position(1,f.character,old_position,2,15,17,13);
        const auto root=f.characters.list_for_account(1).front();
        const auto frame=RecoveredWorldEntry::wire(f.character,root.profile,17,13,2,15,2);
        RecoveredMovementService movement(f.characters,std::filesystem::path(GOD2_SOURCE_DIR)/"artifacts/world-atlas/indoor-2-15.json");
        movement.prepare_native(71,1,f.character,frame);movement.bind(71,1,f.character);
        const auto actual=movement.observe_world_location(71,1,f.character);require(actual.has_value(),"C67 ready movement fixture absent");
        const auto before=f.companions.load_deity_roster(1,f.character);const auto activation=f.activation_storage();
        const auto selected=f.companions.load_deity_selection(1,f.character);
        const auto rows=f.companions.load_deities(1,f.character);
        const auto chosen=std::find_if(rows.begin(),rows.end(),[](const auto& d){return d.snapshot.status.key_raw()==2;});
        require(chosen!=rows.end(),"C67 full expected deity missing");
        struct Observe {RecoveredMovementService* movement;RecoveredWorldEntry::Frame frame;std::uint64_t character;
            unsigned mode;bool wrote=false,fired=false,failed=false;
        } observed{&movement,frame,f.character,mode};
        const auto trace=[](unsigned type,void* context,void* statement,void*)->int {
            auto& o=*static_cast<Observe*>(context);const auto* text=sqlite3_sql(static_cast<sqlite3_stmt*>(statement));
            if(!text)return 0;const std::string_view sql(text);
            const bool write=sql.starts_with("UPDATE main.character_deity_selection")||sql.starts_with("INSERT INTO main.character_deity_selection");
            if(type==SQLITE_TRACE_STMT&&write)o.wrote=true;
            if(!o.fired&&o.wrote&&((o.mode<=2&&type==SQLITE_TRACE_STMT&&write)||
                (o.mode>=3&&type==SQLITE_TRACE_PROFILE&&sql=="COMMIT"))) {
                o.fired=true;
                try {
                    const auto old=o.movement->current_world_location(71,1,o.character);o.movement->remove(71);
                    if(o.mode==2||o.mode==4) {
                        o.movement->prepare_native(71,1,o.character,o.frame);o.movement->bind(71,1,o.character);
                        if(o.movement->current_world_location(71,1,o.character)!=old)throw std::runtime_error("C67 rebind altered pose fixture");
                    }
                }catch(...){o.failed=true;}
            }
            return 0;
        };
        struct TraceEnd {sqlite3* db;~TraceEnd(){sqlite3_trace_v2(db,0,nullptr,nullptr);}} end{f.db.get()};
        require(sqlite3_trace_v2(f.db.get(),SQLITE_TRACE_STMT|SQLITE_TRACE_PROFILE,trace,&observed)==SQLITE_OK,"C67 source trace registration failed");
        const auto pure=[&]{return movement.world_location_current(*actual);};
        if(mode==5) {
            auto durable=f.companions.select_deity_with_source(1,f.character,2,selected,*chosen,pure);
            require(!durable.current()&&!f.companions.issued_selection(durable)&&
                !f.companions.selection_roster_successor(before,durable),"Retired durable delivery cut minted live selection authority");
        }else rejects([&]{(void)f.helper.select_deity_with_source(1,f.character,{2},pure);});
        sqlite3_trace_v2(f.db.get(),0,nullptr,nullptr);
        const auto saved=f.companions.load_deity_selection(1,f.character);
        require(observed.fired&&!observed.failed&&saved&&saved->key==(mode>=3?2:1)&&f.activation_storage()==activation,
            "C67 movement source cut leaked a precommit change, lost durable truth or changed learning history");
        require(!movement.world_binding_current(*actual),"Removed/same-value movement incarnation remained current");
    }
}
}
int main() {
    try {
        selection_source_regression();
        learning_selection_source_regression();
        joint_material_successor_regression();
        status_activation_lineage_regression();
        pet_selection_continuation_regression();
        deity_selection_live_source_regression();
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
