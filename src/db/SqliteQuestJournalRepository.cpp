#include "db/SqliteQuestJournalRepository.h"
#include "db/NativeQuestCatalog.h"
#include "db/SqliteSupport.h"
#include "protocol/RecoveredQuestSync.h"
#include <limits>
#include <utility>

namespace god2 {
namespace {
void validate(const QuestJournalSnapshot& value,const std::array<std::uint16_t,418>& counts) {
    if(!value.revision || value.revision>static_cast<std::uint64_t>(std::numeric_limits<std::int64_t>::max()) ||
       (value.origin!="NATIVE_CAPTURE_VERIFIED" && value.origin!="CUSTOM_TEST_NOT_NATIVE") ||
       value.provenance.empty() || value.provenance.size()>255 || value.provenance.find('\0')!=std::string::npos ||
       !RecoveredQuestSync::encodeJournalLogical(value.values,counts))
        throw DatabaseError("Invalid owned quest journal snapshot");
}
}
SqliteQuestJournalRepository::SqliteQuestJournalRepository(sqlite3* db):db_(db) {
    if(!db_) throw DatabaseError("Null quest journal connection");
}
std::array<std::uint16_t,418> SqliteQuestJournalRepository::description_counts() {
    NativeQuestCatalog catalog(db_);
    const auto totals=catalog.counts();
    if(totals.definitions!=418 || totals.descriptions!=2014)
        throw DatabaseError("Incomplete owned journal quest catalog");
    // Validate every definition's source identity and raw index/count/title
    // mapping, not just the particular references in a mostly empty journal.
    for(std::uint16_t mission=1;mission<=418;++mission)
        if(!catalog.definition(mission)) throw DatabaseError("Missing journal quest definition");
    sqlite_detail::Statement rows(db_,
        "SELECT d.mission_index,d.description_count,q.description_index,q.description_count,"
        "s.native_image_sha256,s.source_section,s.loader_rva,s.lookup_rva,s.row_count "
        "FROM native_quest_definitions d LEFT JOIN native_quest_descriptions q "
        "ON q.dataset_id=d.dataset_id AND q.mission_index=d.mission_index "
        "LEFT JOIN native_data_sources s ON s.dataset_id=d.dataset_id "
        "WHERE d.dataset_id='current-quest-descriptions-v1' ORDER BY d.mission_index,q.description_index");
    std::array<std::uint16_t,418> result{};
    std::uint32_t mission=1,index=0,total=0;
    while(rows.row()) {
        const auto count=rows.number<std::uint16_t>(1);
        if(mission>418 || rows.number<std::uint32_t>(0)!=mission || !count || count>32767 ||
           rows.number<std::uint32_t>(2)!=index || rows.number<std::uint16_t>(3)!=count ||
           (index && result[mission-1]!=count) ||
           rows.text(4)!="149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763" ||
           rows.text(5)!="Mission_data" || rows.text(6)!="0x584ae" || rows.text(7)!="0xc9581" || rows.integer(8)!=418)
            throw DatabaseError("Invalid owned journal description catalog");
        result[mission-1]=count;++total;
        if(++index==count) {++mission;index=0;}
    }
    if(mission!=419 || index || total!=2014) throw DatabaseError("Incomplete journal descriptions");
    return result;
}
std::optional<QuestJournalSnapshot> SqliteQuestJournalRepository::load_in_transaction(
        std::uint64_t account,std::uint64_t character,const std::array<std::uint16_t,418>& counts) {
    if(!account || !character) throw DatabaseError("Invalid quest journal owner");
    sqlite_detail::Statement row(db_,
        "SELECT j.character_id IS NOT NULL,j.values_blob,j.revision,j.origin,j.provenance,j.design_id "
        "FROM recovered_characters c LEFT JOIN character_quest_journals j ON j.character_id=c.id "
        "WHERE c.account_id=? AND c.id=?");
    row.bind_id(1,account);row.bind_id(2,character);
    if(!row.row()) throw DatabaseError("Invalid quest journal owner");
    if(!row.integer(0)) return std::nullopt;
    QuestJournalSnapshot result{};
    const auto bytes=row.blob(1,60,60);
    for(std::size_t slot=0;slot<15;++slot)
        for(unsigned byte=0;byte<4;++byte)
            result.values[slot]|=std::uint32_t{bytes[slot*4+byte]}<<(8*byte);
    result.revision=row.number<std::uint64_t>(2);result.origin=row.text(3);result.provenance=row.text(4);
    if(row.text(5)!="CUSTOM-0041") throw DatabaseError("Invalid quest journal design");
    validate(result,counts);return result;
}
std::optional<QuestJournalSnapshot> SqliteQuestJournalRepository::load(std::uint64_t account,std::uint64_t character) {
    // Deferred read transaction: an absent owned snapshot needs no catalog and
    // no write reservation. Existing snapshots must validate their entire
    // pinned catalog in the same read snapshot before any values are returned.
    sqlite_detail::execute(db_,"BEGIN");
    try {
        if(!account || !character) throw DatabaseError("Invalid quest journal owner");
        bool exists=false;
        {
            sqlite_detail::Statement owner(db_,
                "SELECT j.character_id IS NOT NULL FROM recovered_characters c "
                "LEFT JOIN character_quest_journals j ON j.character_id=c.id "
                "WHERE c.account_id=? AND c.id=?");
            owner.bind_id(1,account);owner.bind_id(2,character);
            if(!owner.row()) throw DatabaseError("Invalid quest journal owner");
            exists=owner.integer(0)!=0;
        }
        const auto result=exists ? load_in_transaction(account,character,description_counts()) : std::nullopt;
        sqlite_detail::execute(db_,"COMMIT");return result;
    }catch(...) {
        sqlite3_exec(db_,"ROLLBACK",nullptr,nullptr,nullptr);throw;
    }
}
QuestJournalSnapshot SqliteQuestJournalRepository::save(std::uint64_t account,std::uint64_t character,
        std::optional<std::uint64_t> expected_revision,std::array<std::uint32_t,15> values,
        std::string origin,std::string provenance) {
    if(expected_revision && (!*expected_revision ||
       *expected_revision>=static_cast<std::uint64_t>(std::numeric_limits<std::int64_t>::max())))
        throw DatabaseError("Quest journal revision out of range");
    sqlite_detail::Transaction transaction(db_);
    const auto counts=description_counts();
    const auto previous=load_in_transaction(account,character,counts);
    if(previous.has_value()!=expected_revision.has_value() ||
       (previous && previous->revision!=*expected_revision))
        throw DatabaseError("Quest journal revision conflict");
    QuestJournalSnapshot next{values,expected_revision ? *expected_revision+1 : 1,std::move(origin),std::move(provenance)};
    validate(next,counts);
    std::array<std::uint8_t,60> bytes{};
    for(std::size_t slot=0;slot<15;++slot)
        for(unsigned byte=0;byte<4;++byte) bytes[slot*4+byte]=static_cast<std::uint8_t>(values[slot]>>(8*byte));
    sqlite_detail::Statement write(db_,expected_revision ?
        "UPDATE character_quest_journals SET values_blob=?,revision=?,origin=?,provenance=? WHERE character_id=? AND revision=?" :
        "INSERT INTO character_quest_journals(values_blob,revision,origin,provenance,character_id,design_id) VALUES(?,?,?,?,?,'CUSTOM-0041')");
    write.bind_blob(1,bytes);write.bind_id(2,next.revision);write.bind(3,next.origin);write.bind(4,next.provenance);write.bind_id(5,character);
    if(expected_revision) write.bind_id(6,*expected_revision);
    write.done();
    if(sqlite3_changes(db_)!=1 || load_in_transaction(account,character,counts)!=std::optional{next})
        throw DatabaseError("Quest journal write verification failed");
    transaction.commit();return next;
}
}
