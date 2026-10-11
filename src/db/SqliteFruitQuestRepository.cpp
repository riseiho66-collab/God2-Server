#include "db/SqliteFruitQuestRepository.h"
#include "db/NativeQuestCatalog.h"
#include "db/SqliteSupport.h"
#include "game/FruitVillageQuestRules.h"
#include "protocol/RecoveredRoleLevel.h"
#include "protocol/RecoveredQuestSync.h"
#include <algorithm>
#include <cstdlib>
#include <string_view>

namespace god2 {
namespace q=InferredQuestRules;
namespace f=FruitVillageQuestRules;
namespace {
using sqlite_detail::Statement;
void require(bool value,const char* message){if(!value)throw DatabaseError(message);}
constexpr auto item_source="70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731";
std::vector<std::uint8_t> unhex(std::string_view text) {
    require(text.size()%2==0,"Bad internal fruit source hex");std::vector<std::uint8_t> bytes;
    const auto digit=[](char c)->unsigned {if(c>='0'&&c<='9')return c-'0';if(c>='a'&&c<='f')return c-'a'+10;throw DatabaseError("Bad fruit source hex");};
    for(std::size_t i=0;i<text.size();i+=2)bytes.push_back(static_cast<std::uint8_t>(digit(text[i])*16+digit(text[i+1])));
    return bytes;
}
struct Pin {std::uint16_t mission;std::int64_t line;const char* definition;const char* definition_sha;const char* description;const char* description_sha;};
constexpr Pin pins[]={
    {234,1487,"3233342c5bb773a4e2a5f4b0c85daa47a44fa657b2a32c31","7424b50dd27adbe9b7737c74a24b0e2bb8a0e96c16b7128bab9f601e93f86346","2c2c312caa47a44fa7f8aababc70ae76b1e7bad5283130382f31313029a7c6b1e6a741aeb3a65ea4adadd3bdbda4fba6d7b5b9a54c","5e45a9151239363d92e6cc72c8395a6ace42f25e09c6e9ea6b35852ed0609d9b"},
    {236,1491,"3233362c5bb773a4e2a5f4b0c85dab43b1f6a6cbb0a82c31","a22681d7da1364564c843f4ec42f1b8c32822ee5183597e867c4771b98d15fc8","2c2c312caa47a44fa7f8aabaa7f5bcd6283131332f363929bbddad6ea440b5a7bffaa66eb56eaaf9b4a3bfcba141a7c6b1e6a741afe0c0b0a54ca7e4a8d3a4adadd3a556c2ceae4caff3","116985a5fefba6c37523f1ea94b987286e00d6b32222015a819b96e19f70b68b"},
    {237,1493,"3233372c5bb773a4e2a5f4b0c85db752a4dfab4bb7ed2c31","03c781d4c59c3163d30e6c3206c57867373c95f0dfe62d91b6ae5a52b1723ac6","2c2c312caa47a44fa7f8aabaaafcbbc8c2542836392f373229bbddad6ea451add3bdbda4fba6d7a8d3a7b9a6a8a66facb0a8e0a46cb7c7b3c6aabaab4bb7ed","a240309a04e8841c742e0d714614db14153bc65113031f739d99199e8ab8ea7e"},
    {238,1495,"3233382c5bb773a4e2a5f4b0c85dbf6db448a6e7aaab2c31","3a3d33812b1292a9223a69aaf38e713b101cf2b51cc00f3d99823bcd4018ac0f","2c2c312caa47a44fa7f8aabab0a8a6d1a7422836382f31313629a65dacb0a4d1aef0b448a74ea141bdd0a741c0b0a54ca7e4b44da447a451add3a8dfa5d6a8d3bb73a740bf6db448aabaa6e7aaab","886f2d71e1ba46bdcd0da397645115d5c0c437a610cd7a5ec8b81725978a4436"},
};
std::array<std::uint8_t,60> journal_bytes(const QuestJournalSnapshot& journal) {
    std::array<std::uint8_t,60> bytes{};
    for(std::size_t i=0;i<15;++i)for(unsigned b=0;b<4;++b)bytes[i*4+b]=static_cast<std::uint8_t>(journal.values[i]>>(8*b));
    return bytes;
}
void changed(sqlite3* db){require(sqlite3_changes(db)==1,"Fruit quest CAS rejected");}
}
const char* SqliteFruitQuestRepository::schema() noexcept {
    return R"SQL(
CREATE TABLE character_fruit_quest_balances (
 character_id INTEGER PRIMARY KEY REFERENCES recovered_characters(id) ON DELETE CASCADE,
 reputation INTEGER NOT NULL CHECK(typeof(reputation)='integer' AND reputation>=0),
 currency INTEGER NOT NULL CHECK(typeof(currency)='integer' AND currency=0),
 revision INTEGER NOT NULL CHECK(typeof(revision)='integer' AND revision>0),
 design_id TEXT NOT NULL CHECK(design_id='CUSTOM-0051')
);
CREATE TABLE character_fruit_quest_progress (
 character_id INTEGER NOT NULL REFERENCES recovered_characters(id) ON DELETE CASCADE,
 mission_id INTEGER NOT NULL CHECK(mission_id IN (234,236,237,238)),
 phase TEXT NOT NULL CHECK(phase IN ('ACCEPTED','COMPLETED')),
 revision INTEGER NOT NULL CHECK(typeof(revision)='integer' AND revision>0),
 rule_revision INTEGER NOT NULL CHECK(rule_revision=1),
 bundle_sha256 TEXT NOT NULL CHECK(bundle_sha256='ab3e063564d0e7b351c3abab9e3475419c3a710ec9371b3de4d9b01f44a76541'),
 experience_before INTEGER NOT NULL CHECK(typeof(experience_before)='integer' AND experience_before>=0),
 experience_after INTEGER NOT NULL CHECK(typeof(experience_after)='integer' AND experience_after>=experience_before),
 experience_delta INTEGER NOT NULL CHECK(typeof(experience_delta)='integer' AND experience_delta>=0),
 reputation_before INTEGER NOT NULL CHECK(typeof(reputation_before)='integer' AND reputation_before>=0),
 reputation_after INTEGER NOT NULL CHECK(typeof(reputation_after)='integer' AND reputation_after>=reputation_before),
 reputation_delta INTEGER NOT NULL CHECK(typeof(reputation_delta)='integer' AND reputation_delta>=0),
 experience_was_present INTEGER NOT NULL CHECK(experience_was_present IN (0,1)),
 receipt TEXT NOT NULL,
 design_id TEXT NOT NULL CHECK(design_id='CUSTOM-0051'),
 PRIMARY KEY(character_id,mission_id),
 CHECK((phase='ACCEPTED' AND receipt='' AND experience_before=0 AND experience_after=0 AND experience_delta=0 AND reputation_before=0 AND reputation_after=0 AND reputation_delta=0 AND experience_was_present=0)
    OR (phase='COMPLETED' AND length(receipt)>0 AND experience_delta>0 AND reputation_delta=1 AND experience_after-experience_before=experience_delta AND reputation_after-reputation_before=1))
);
)SQL";
}
SqliteFruitQuestRepository::SqliteFruitQuestRepository(sqlite3* db,SourceGuard guard):db_(db),source_guard_(std::move(guard)) {
    require(db_&&bool(source_guard_),"Fruit quest database and source guard required");
}
std::array<std::uint16_t,418> SqliteFruitQuestRepository::source_counts() {
    NativeQuestCatalog catalog(db_);const auto totals=catalog.counts();
    require(totals.definitions==418&&totals.descriptions==2014,"Fruit quest catalog incomplete");
    std::array<std::uint16_t,418> counts{};
    Statement rows(db_,"SELECT mission_index,description_count FROM native_quest_definitions WHERE dataset_id='current-quest-descriptions-v1' ORDER BY mission_index");
    std::size_t i=0;while(rows.row()) {
        require(i<418&&rows.number<std::uint32_t>(0)==i+1,"Fruit quest definition sequence");
        counts[i++]=rows.number<std::uint16_t>(1);require(counts[i-1]>0&&counts[i-1]<=32767,"Fruit quest description count");
    }
    require(i==418,"Fruit quest definitions missing");
    Statement identity(db_,"SELECT native_image_sha256,source_section,loader_rva,lookup_rva,row_count FROM native_data_sources WHERE dataset_id='current-quest-descriptions-v1'");
    require(identity.row()&&identity.text(0)=="149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763"&&
            identity.text(1)=="Mission_data"&&identity.text(2)=="0x584ae"&&identity.text(3)=="0xc9581"&&identity.integer(4)==418,"Fruit quest source identity");
    for(const auto& pin:pins) {
        const auto definition=catalog.definition(pin.mission),description=catalog.description(pin.mission,0);
        require(definition&&description&&counts[pin.mission-1]==1&&definition->source_line==pin.line&&
                description->source_line==pin.line+1&&definition->raw_record==unhex(pin.definition)&&
                definition->record_sha256==pin.definition_sha&&description->raw_record==unhex(pin.description)&&
                description->record_sha256==pin.description_sha,"Fruit quest fixed source row mismatch");
    }
    return counts;
}
SqliteFruitQuestRepository::View SqliteFruitQuestRepository::read(std::uint64_t account,std::uint64_t character,std::uint32_t mission) {
    const auto* descriptor=f::find(mission);require(descriptor&&account&&character,"Invalid fruit quest owner/mission");
    Statement owner(db_,"SELECT 1 FROM recovered_characters WHERE id=? AND account_id=?");owner.bind_id(1,character);owner.bind_id(2,account);
    require(owner.row(),"Fruit quest ownership rejected");
    const auto counts=source_counts();
    View out;out.mission=mission;out.snapshot.owner={account,character};out.snapshot.quest_history_complete=true;
    Statement role(db_,"SELECT logical,revision,design_id FROM character_role_snapshots WHERE character_id=?");role.bind_id(1,character);
    if(role.row()) {
        const auto raw=role.blob(0,25,25);std::array<std::uint8_t,25> bytes{};std::copy(raw.begin(),raw.end(),bytes.begin());
        const auto parsed=RecoveredRoleLevel::parse(bytes);out.role_revision=role.number<std::uint64_t>(1);
        require(parsed&&parsed->level()&&parsed->max_hp()&&q::valid_revision(out.role_revision)&&role.text(2)=="CUSTOM-0013","Invalid saved fruit quest role");
        out.role_logical=bytes;out.snapshot.role=q::Role{parsed->level(),0,0,0,1};
    }
    Statement xp(db_,"SELECT total,design_id FROM character_experience WHERE character_id=?");xp.bind_id(1,character);
    if(xp.row()) {out.experience_present=true;require(xp.text(1)=="CUSTOM-0012","Fruit quest XP baseline origin");
        const auto value=xp.number<std::uint64_t>(0);require(out.snapshot.role.has_value(),"XP without saved role");out.snapshot.role->experience=value;}
    Statement balance(db_,"SELECT reputation,currency,revision,design_id FROM character_fruit_quest_balances WHERE character_id=?");balance.bind_id(1,character);
    if(balance.row()) {
        out.balance_present=true;require(out.snapshot.role.has_value(),"Fruit balance without saved role");
        out.snapshot.role->reputation=balance.number<std::uint64_t>(0);out.snapshot.role->currency=balance.number<std::uint64_t>(1);
        out.snapshot.role->revision=balance.number<std::uint64_t>(2);
        require(!out.snapshot.role->currency&&q::valid_revision(out.snapshot.role->revision)&&balance.text(3)=="CUSTOM-0051","Invalid fruit balance");
    }
    Statement progress(db_,"SELECT mission_id,phase,revision,rule_revision,bundle_sha256,experience_before,experience_after,experience_delta,reputation_before,reputation_after,reputation_delta,experience_was_present,receipt,design_id FROM character_fruit_quest_progress WHERE character_id=? ORDER BY mission_id");progress.bind_id(1,character);
    while(progress.row()) {
        const auto id=progress.number<std::uint32_t>(0);const auto* d=f::find(id);const auto phase=progress.text(1);
        require(d&&out.balance_present&&(phase=="ACCEPTED"||phase=="COMPLETED")&&progress.text(13)=="CUSTOM-0051","Invalid fruit quest progress");
        q::Progress entry{phase=="ACCEPTED"?q::Phase::Accepted:q::Phase::Completed,progress.number<std::uint64_t>(2),progress.number<std::uint64_t>(3),"CUSTOM-0051",phase=="COMPLETED"?1u:0u};
        require(q::valid_revision(entry.revision)&&entry.accepted_rule_revision==1,"Fruit quest version mismatch");
        Receipt receipt{progress.number<std::uint64_t>(5),progress.number<std::uint64_t>(6),progress.number<std::uint64_t>(7),progress.number<std::uint64_t>(8),progress.number<std::uint64_t>(9),progress.number<std::uint64_t>(10),progress.integer(11)!=0,progress.text(12),progress.text(4)};
        require(receipt.bundle_sha256==f::bundle_sha256&&(progress.integer(11)==0||progress.integer(11)==1),"Fruit receipt source mismatch");
        if(entry.phase==q::Phase::Accepted)require(receipt.token.empty()&&!receipt.experience_before&&!receipt.experience_after&&!receipt.experience_delta&&!receipt.reputation_before&&!receipt.reputation_after&&!receipt.reputation_delta&&!receipt.experience_was_present,"Accepted fruit quest has reward");
        else {
            const auto token="CUSTOM-0051/"+std::to_string(character)+"/"+std::to_string(id)+"/1";
            require(receipt.token==token&&receipt.experience_delta==d->experience&&receipt.reputation_delta==d->reputation&&
                    receipt.experience_after>=receipt.experience_before&&receipt.experience_after-receipt.experience_before==d->experience&&
                    receipt.reputation_after>=receipt.reputation_before&&receipt.reputation_after-receipt.reputation_before==d->reputation&&
                    out.experience_present&&out.snapshot.role->experience>=receipt.experience_after&&out.snapshot.role->reputation>=receipt.reputation_after,"Invalid once-only fruit receipt");
        }
        require(out.snapshot.quests.emplace(id,entry).second&&out.receipts.emplace(id,receipt).second,"Duplicate fruit quest");
    }
    Statement position(db_,"SELECT area,scene,x,y,revision FROM recovered_positions WHERE character_id=?");position.bind_id(1,character);
    if(position.row()) {
        out.position=RecoveredPosition{position.number<std::uint16_t>(0),position.number<std::uint16_t>(1),position.number<std::uint16_t>(2),position.number<std::uint16_t>(3),position.number<std::uint64_t>(4)};
        require(out.position->area<=63&&out.position->scene<=1023&&q::valid_revision(out.position->revision),"Invalid fruit position");
        out.snapshot.mutation_admitted=out.position->area==f::area&&out.position->scene==f::scene&&
            std::abs(int(out.position->x)-int(descriptor->source_x))<=3&&std::abs(int(out.position->y)-int(descriptor->source_y))<=3;
    }
    Statement pending(db_,"SELECT 1 FROM battle_reservations r LEFT JOIN battle_settlements s ON s.battle_id=r.id WHERE r.character_id=? AND s.battle_id IS NULL LIMIT 1");pending.bind_id(1,character);
    if(pending.row())out.snapshot.mutation_admitted=false;
    Statement slots(db_,"SELECT slot,item_id,count,revision,source_sha256,design_id FROM diagnostic_inventory_slots WHERE character_id=? AND slot BETWEEN 0 AND 29 ORDER BY slot");slots.bind_id(1,character);
    while(slots.row()) {
        const auto slot=slots.number<std::uint8_t>(0);require(slot<30&&slots.text(4)==item_source&&slots.text(5)=="CUSTOM-0015","Fruit inventory source mismatch");
        out.snapshot.bag[slot]=q::Slot{slots.number<std::uint16_t>(1),slots.number<std::uint32_t>(2),slots.number<std::uint64_t>(3),std::nullopt,slots.text(4)};
    }
    Statement metadata(db_,"SELECT slot,logical20,revision,origin,provenance,source_sha256,client_sha256,design_id FROM character_weapon_slot_metadata WHERE character_id=? AND slot BETWEEN 0 AND 29 ORDER BY slot");metadata.bind_id(1,character);
    while(metadata.row()) {
        const auto slot=metadata.number<std::uint8_t>(0);require(slot<30&&out.snapshot.bag[slot],"Orphan fruit inventory overlay");
        Overlay overlay;const auto bytes=metadata.blob(1,20,20);std::copy(bytes.begin(),bytes.end(),overlay.logical.begin());
        overlay.revision=metadata.number<std::uint64_t>(2);overlay.origin=metadata.text(3);overlay.provenance=metadata.text(4);
        overlay.source_sha256=metadata.text(5);overlay.client_sha256=metadata.text(6);overlay.design_id=metadata.text(7);
        const auto& scalar=*out.snapshot.bag[slot];
        require(overlay.revision==scalar.revision&&overlay.source_sha256==item_source&&overlay.client_sha256==f::client_sha256&&overlay.design_id=="CUSTOM-0046"&&
                q::item_key(overlay.logical)==scalar.item&&!overlay.provenance.empty(),"Fruit inventory overlay mismatch");
        if(scalar.count) {
            require(overlay.origin=="NATIVE_CAPTURE_VERIFIED"||overlay.origin=="CUSTOM_TEST_NOT_NATIVE","Invalid occupied fruit overlay origin");
            out.snapshot.bag[slot]->instance=overlay.logical; // never eligible for scalar collect.
        } else require(overlay.origin=="EMPTY_SLOT_POLICY","Invalid empty fruit overlay origin");
        out.overlays[slot]=std::move(overlay);
    }
    Statement journal(db_,"SELECT values_blob,revision,origin,provenance,design_id FROM character_quest_journals WHERE character_id=?");journal.bind_id(1,character);
    if(journal.row()) {
        QuestJournalSnapshot value;const auto bytes=journal.blob(0,60,60);
        for(std::size_t slot=0;slot<15;++slot)for(unsigned b=0;b<4;++b)value.values[slot]|=std::uint32_t{bytes[4*slot+b]}<<(8*b);
        value.revision=journal.number<std::uint64_t>(1);value.origin=journal.text(2);value.provenance=journal.text(3);
        require(q::valid_revision(value.revision)&&journal.text(4)=="CUSTOM-0041"&&
                (value.origin=="NATIVE_CAPTURE_VERIFIED"||value.origin=="CUSTOM_TEST_NOT_NATIVE")&&!value.provenance.empty()&&value.provenance.size()<=255&&
                RecoveredQuestSync::encodeJournalLogical(value.values,counts).has_value(),"Invalid fruit journal");
        NativeQuestCatalog catalog(db_);for(auto packed:value.values)if(packed) {
            const auto ref=RecoveredQuestSync::descriptionReference(packed,counts);
            require(ref&&catalog.definition(ref->missionIndex)&&catalog.description(ref->missionIndex,ref->descriptionIndex),"Fruit journal reference unavailable");
        }
        out.journal=value;
    }
    // Missing role is a readable absence, never a fixture grant. Other malformed
    // snapshots fail closed even for a read. Admission is checked by mutation.
    if(out.snapshot.role) {
        auto validate=out.snapshot;validate.mutation_admitted=true;
        require(q::validate_snapshot(validate,{account,character})==q::Error::None,"Malformed fruit planner snapshot");
    }
    return out;
}
SqliteFruitQuestRepository::View SqliteFruitQuestRepository::load(std::uint64_t account,std::uint64_t character,std::uint32_t mission) {
    require(sqlite3_get_autocommit(db_)!=0,"Fruit load needs its own read transaction");source_guard_();sqlite_detail::execute(db_,"BEGIN");
    try {auto result=read(account,character,mission);sqlite_detail::execute(db_,"COMMIT");return result;}
    catch(...){sqlite3_exec(db_,"ROLLBACK",nullptr,nullptr,nullptr);throw;}
}
SqliteFruitQuestRepository::Commit SqliteFruitQuestRepository::accept(std::uint64_t account,std::uint64_t character,std::uint32_t mission,const View& expected,const Prepare& prepare) {
    return mutate(q::Action::Accept,account,character,mission,expected,prepare);
}
SqliteFruitQuestRepository::Commit SqliteFruitQuestRepository::submit(std::uint64_t account,std::uint64_t character,std::uint32_t mission,const View& expected,const Prepare& prepare) {
    return mutate(q::Action::Submit,account,character,mission,expected,prepare);
}
SqliteFruitQuestRepository::Commit SqliteFruitQuestRepository::mutate(q::Action action,std::uint64_t account,std::uint64_t character,std::uint32_t mission,const View& expected,const Prepare& prepare) {
    sqlite_detail::Transaction tx(db_);source_guard_();const auto before=read(account,character,mission);
    require(before==expected,"Fruit quest stale read set");const auto rule=f::rule(mission);require(rule.has_value(),"Unknown fruit quest rule");
    const auto proposal=q::plan(action,*rule,before.snapshot,{account,character});
    require(bool(proposal),"Fruit quest transition rejected");const auto& after=proposal.plan->after;
    // The immutable four recipes have no currency/item rewards; do not grow
    // this repository into a generic grant adapter by accepting new rule shapes.
    require(*rule->rewards.currency.value==0&&rule->rewards.stacks.value->empty(),"Unsupported fruit reward payload");
    auto journal=before.journal.value_or(QuestJournalSnapshot{});
    const auto occurrences=std::count_if(journal.values.begin(),journal.values.end(),[&](auto value){return (value&65535)==mission;});
    if(action==q::Action::Accept) {
        require(occurrences==0,"Fruit journal already contains mission");
        const auto free=std::find(journal.values.begin(),journal.values.end(),0u);require(free!=journal.values.end(),"Fruit journal full");
        *free=0x10000u|mission; // highWORD1 -> description0, never completion flag.
    } else {
        require(occurrences==1,"Accepted fruit mission missing/duplicated in journal");
        for(auto& value:journal.values)if((value&65535)==mission)value=0;
    }
    require(journal.revision<q::max_revision,"Fruit journal revision overflow");++journal.revision;
    journal.origin="CUSTOM_TEST_NOT_NATIVE"; // Existing schema enum; never claim capture.
    journal.provenance="CUSTOM-0051/fruit/"+std::string(action==q::Action::Accept?"accept/":"submit/")+std::to_string(mission);
    Commit result;result.before=before;
    if(!before.balance_present) {
        require(action==q::Action::Accept,"Missing accepted fruit balances");
        Statement insert(db_,"INSERT INTO character_fruit_quest_balances VALUES(?,0,0,1,'CUSTOM-0051')");insert.bind_id(1,character);insert.done();changed(db_);
    }
    for(std::size_t slot=0;slot<30;++slot)if(after.bag[slot]!=before.snapshot.bag[slot]) {
        require(after.bag[slot]&&before.snapshot.bag[slot]&&!before.snapshot.bag[slot]->instance,"Unexpected fruit instance mutation");
        const auto& prior=*before.snapshot.bag[slot];const auto& next=*after.bag[slot];
        Statement update(db_,"UPDATE diagnostic_inventory_slots SET item_id=?,count=?,revision=? WHERE character_id=? AND slot=? AND item_id=? AND count=? AND revision=? AND source_sha256=? AND design_id='CUSTOM-0015'");
        update.bind(1,next.item);update.bind(2,next.count);update.bind_id(3,next.revision);update.bind_id(4,character);update.bind(5,static_cast<std::int64_t>(slot));
        update.bind(6,prior.item);update.bind(7,prior.count);update.bind_id(8,prior.revision);update.bind(9,item_source);update.done();changed(db_);
        result.changed_bags.push_back({static_cast<std::uint8_t>(slot),prior,next});
    }
    if(action==q::Action::Accept) {
        Statement progress(db_,"INSERT INTO character_fruit_quest_progress VALUES(?,?,'ACCEPTED',1,1,?,0,0,0,0,0,0,0,'','CUSTOM-0051')");
        progress.bind_id(1,character);progress.bind(2,mission);progress.bind(3,std::string(f::bundle_sha256));progress.done();changed(db_);
    } else {
        const auto& prior=*before.snapshot.role;const auto& next=*after.role;
        result.experience_delta=*rule->rewards.experience.value;result.reputation_delta=*rule->rewards.reputation.value;
        Statement xp(db_,before.experience_present?
            "UPDATE character_experience SET total=? WHERE character_id=? AND total=? AND design_id='CUSTOM-0012'":
            "INSERT INTO character_experience(total,character_id,design_id) VALUES(?,?,'CUSTOM-0012')");
        xp.bind_id(1,next.experience);xp.bind_id(2,character);if(before.experience_present)xp.bind_id(3,prior.experience);xp.done();changed(db_);
        Statement balance(db_,"UPDATE character_fruit_quest_balances SET reputation=?,revision=? WHERE character_id=? AND reputation=? AND currency=0 AND revision=? AND design_id='CUSTOM-0051'");
        balance.bind_id(1,next.reputation);balance.bind_id(2,next.revision);balance.bind_id(3,character);balance.bind_id(4,prior.reputation);balance.bind_id(5,prior.revision);balance.done();changed(db_);
        const auto token="CUSTOM-0051/"+std::to_string(character)+"/"+std::to_string(mission)+"/1";
        Statement progress(db_,"UPDATE character_fruit_quest_progress SET phase='COMPLETED',revision=?,experience_before=?,experience_after=?,experience_delta=?,reputation_before=?,reputation_after=?,reputation_delta=?,experience_was_present=?,receipt=? WHERE character_id=? AND mission_id=? AND phase='ACCEPTED' AND revision=? AND rule_revision=1 AND bundle_sha256=? AND design_id='CUSTOM-0051'");
        progress.bind_id(1,after.quests.at(mission).revision);progress.bind_id(2,prior.experience);progress.bind_id(3,next.experience);progress.bind_id(4,result.experience_delta);
        progress.bind_id(5,prior.reputation);progress.bind_id(6,next.reputation);progress.bind_id(7,result.reputation_delta);progress.bind(8,before.experience_present?1:0);progress.bind(9,token);
        progress.bind_id(10,character);progress.bind(11,mission);progress.bind_id(12,before.snapshot.quests.at(mission).revision);progress.bind(13,std::string(f::bundle_sha256));progress.done();changed(db_);
    }
    const auto blob=journal_bytes(journal);
    Statement write_journal(db_,before.journal?
        "UPDATE character_quest_journals SET values_blob=?,revision=?,origin=?,provenance=? WHERE character_id=? AND revision=? AND values_blob=? AND design_id='CUSTOM-0041'":
        "INSERT INTO character_quest_journals(values_blob,revision,origin,provenance,character_id,design_id) VALUES(?,?,?,?,?,'CUSTOM-0041')");
    write_journal.bind_blob(1,blob);write_journal.bind_id(2,journal.revision);write_journal.bind(3,journal.origin);write_journal.bind(4,journal.provenance);write_journal.bind_id(5,character);
    if(before.journal){write_journal.bind_id(6,before.journal->revision);write_journal.bind_blob(7,journal_bytes(*before.journal));}
    write_journal.done();changed(db_);
    result.after=read(account,character,mission);
    require(result.after.snapshot==after&&result.after.journal==std::optional{journal}&&result.after.role_logical==before.role_logical&&result.after.role_revision==before.role_revision&&result.after.position==before.position,"Fruit commit readback mismatch");
    const auto projection=RecoveredQuestSync::encodeJournalLogical(journal.values,source_counts());require(projection.has_value(),"Fruit journal projection invalid");
    result.journal_logical.assign(projection->begin(),projection->end());
    const auto changes_before_prepare=sqlite3_total_changes64(db_);
    if(prepare)prepare(result);
    require(sqlite3_total_changes64(db_)==changes_before_prepare,"Fruit projection callback must not write database");
    require(read(account,character,mission)==result.after,"Fruit preparation modified read set");
    tx.commit();return result;
}
}

