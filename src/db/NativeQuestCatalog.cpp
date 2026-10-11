#include "db/NativeQuestCatalog.h"
#include "db/SqliteSupport.h"
#include <algorithm>
namespace god2 {
namespace {
constexpr char mission_sha[]="659c8f38ffd9c34107969b449afd16488665a08970110910c9aed8448a0bb716";
constexpr char mission_plain[]="f57cb8d1a9426e2f797c9cdfea32beb07642415ae3e2bb30a8909373a1c0a5f0";
constexpr char actmis_sha[]="e1e35ee689d12ef265be8620b21f856709976896a46edeb9f31c15622041accf";
constexpr char actmis_plain[]="10f76969d60d3a46fdd937510f1b480bc12a07b4a07b7f98774fa6df9df97548";
constexpr char daily_sha[]="4a347d56706946d7004b2bd2118500ffc60844628fa461862b2f6d5320a90e54";
constexpr char daily_plain[]="2848b95b0af99eac10ca4dff61a5533c13917127c4738039e263c60a1be45eaf";
NativeQuestSourceRecord source(sqlite_detail::Statement& row,const char* path,const char* sha,const char* plain) {
    NativeQuestSourceRecord result;
    result.source_line=row.integer(0);result.record_sha256=row.text(1);
    const auto raw=row.blob(2,1,65535);result.raw_record.assign(raw.begin(),raw.end());
    result.source_path=row.text(3);result.source_sha256=row.text(4);result.decoded_sha256=row.text(5);
    if(result.source_line<1 || result.record_sha256.size()!=64 ||
       result.record_sha256.find_first_not_of("0123456789abcdef")!=std::string::npos ||
       result.source_path!=path || result.source_sha256!=sha || result.decoded_sha256!=plain)
        throw DatabaseError("Quest source provenance mismatch");
    result.fields.emplace_back();
    for(const auto byte:raw) {
        if(!byte || byte=='\r' || byte=='\n')throw DatabaseError("Invalid quest source row bytes");
        if(byte==',')result.fields.emplace_back();else result.fields.back().push_back(byte);
    }
    return result;
}
std::uint32_t number(const std::vector<std::uint8_t>& field,std::uint32_t limit) {
    if(field.empty())throw DatabaseError("Missing quest source numeric field");
    std::uint32_t value=0;
    for(const auto c:field) {
        if(c<'0' || c>'9' || value>limit/10 || (value==limit/10 && static_cast<std::uint32_t>(c-'0')>limit%10))
            throw DatabaseError("Quest source number out of range");
        value=value*10+c-'0';
    }
    return value;
}
void unique(sqlite_detail::Statement& row) {
    if(row.row())throw DatabaseError("Duplicate quest source lookup");
}
}
NativeQuestCatalog::NativeQuestCatalog(sqlite3* db):db_(db) {
    if(!db_)throw DatabaseError("Null quest catalog connection");
}
NativeQuestSourceCounts NativeQuestCatalog::counts() const {
    sqlite_detail::Statement row(db_,"SELECT (SELECT count(*) FROM native_quest_definitions),"
        "(SELECT count(*) FROM native_quest_descriptions),(SELECT count(*) FROM native_quest_requirement_display),"
        "(SELECT count(*) FROM native_daily_quest_source)");
    if(!row.row())throw DatabaseError("Quest source counts unavailable");
    NativeQuestSourceCounts result{row.integer(0),row.integer(1),row.integer(2),row.integer(3)};
    if((result.definitions!=0 && result.definitions!=418) ||
       (result.descriptions!=0 && result.descriptions!=2014) ||
       (result.requirements!=0 && result.requirements!=169) ||
       (result.daily!=0 && result.daily!=85))throw DatabaseError("Incomplete quest source catalog");
    return result;
}
std::optional<NativeQuestSourceRecord> NativeQuestCatalog::definition(std::uint16_t mission) const {
    if(mission<1 || mission>418)throw DatabaseError("Invalid mission display selector");
    sqlite_detail::Statement row(db_,"SELECT q.source_line,q.record_sha256,q.raw_record,s.source_path,s.source_sha256,"
        "s.decoded_sha256,q.description_count,q.title_bytes FROM native_quest_definitions q "
        "LEFT JOIN native_data_sources s ON s.dataset_id=q.dataset_id WHERE q.dataset_id='current-quest-descriptions-v1' AND q.mission_index=?");
    row.bind(1,mission);if(!row.row())return std::nullopt;
    auto result=source(row,"Data2/Patch/Comm/Mission_data.csvZ",mission_sha,mission_plain);
    if(result.fields.size()!=3 || number(result.fields[0],418)!=mission ||
       number(result.fields[2],32767)!=row.integer(6))throw DatabaseError("Mission source mapping mismatch");
    const auto title=row.blob(7,1,65535);
    if(!std::equal(title.begin(),title.end(),result.fields[1].begin(),result.fields[1].end()))
        throw DatabaseError("Mission title bytes mismatch");
    unique(row);return result;
}
std::optional<NativeQuestSourceRecord> NativeQuestCatalog::description(std::uint16_t mission,std::uint16_t index) const {
    if(mission<1 || mission>418 || index>32766)throw DatabaseError("Invalid description display selector");
    sqlite_detail::Statement row(db_,"SELECT q.source_line,q.record_sha256,q.raw_record,s.source_path,s.source_sha256,"
        "s.decoded_sha256,q.description_count FROM native_quest_descriptions q LEFT JOIN native_data_sources s "
        "ON s.dataset_id=q.dataset_id WHERE q.dataset_id='current-quest-descriptions-v1' AND q.mission_index=? AND q.description_index=?");
    row.bind(1,mission);row.bind(2,index);if(!row.row())return std::nullopt;
    auto result=source(row,"Data2/Patch/Comm/Mission_data.csvZ",mission_sha,mission_plain);
    if(result.fields.size()!=4 || !result.fields[0].empty() || !result.fields[1].empty() ||
       number(result.fields[2],32767)!=static_cast<std::uint32_t>(index)+1 || row.integer(6)<=index)
        throw DatabaseError("Mission description source mapping mismatch");
    unique(row);return result;
}
std::optional<NativeQuestSourceRecord> NativeQuestCatalog::requirement_display(std::uint16_t serial) const {
    if(serial<1 || serial>169)throw DatabaseError("Invalid ACTMIS display selector");
    sqlite_detail::Statement row(db_,"SELECT q.source_line,q.record_sha256,q.raw_record,s.source_path,s.source_sha256,"
        "s.decoded_sha256,q.item_quantity_pairs FROM native_quest_requirement_display q LEFT JOIN native_data_sources s "
        "ON s.dataset_id=q.dataset_id WHERE q.dataset_id='current-actmis-display-v1' AND q.serial=?");
    row.bind(1,serial);if(!row.row())return std::nullopt;
    auto result=source(row,"Data2/Patch/Comm/ActMis.csvZ",actmis_sha,actmis_plain);
    if(result.fields.size()!=10 || number(result.fields[0],169)!=serial)throw DatabaseError("ACTMIS source mapping mismatch");
    const auto pairs=row.blob(6,12,12);
    for(std::size_t i=0;i<4;++i) {
        const auto key=number(result.fields[2+i*2],65535),qty=number(result.fields[3+i*2],255);
        if(pairs[i*3]!=(key&255) || pairs[i*3+1]!=(key>>8) || pairs[i*3+2]!=qty)
            throw DatabaseError("ACTMIS pair mapping mismatch");
    }
    unique(row);return result;
}
std::optional<NativeQuestSourceRecord> NativeQuestCatalog::daily_source(std::uint8_t record_index) const {
    if(record_index>84)throw DatabaseError("Invalid daily source row selector");
    sqlite_detail::Statement row(db_,"SELECT source_line,record_sha256,raw_record,source_path,source_sha256,decoded_sha256,"
        "field_count,authority FROM native_daily_quest_source WHERE record_index=?");
    row.bind(1,record_index);if(!row.row())return std::nullopt;
    auto result=source(row,"Data2/Patch/Comm/DayMissionDesc.csvZ",daily_sha,daily_plain);
    if((result.fields.size()!=12 && result.fields.size()!=19) ||
       result.fields.size()!=static_cast<std::size_t>(row.integer(6)) || row.text(7)!="SOURCE_FIELDS_ONLY")
        throw DatabaseError("Daily source shape/authority mismatch");
    unique(row);return result;
}
std::optional<NativeQuestSourceRecord> NativeQuestCatalog::daily_lookup(std::uint8_t index,std::uint8_t branch) const {
    const auto size=counts().daily;
    for(std::uint8_t record=0;record<size;++record) {
        auto source=daily_source(record);
        if(!source)throw DatabaseError("Daily lookup source incomplete");
        if(static_cast<std::uint8_t>(number(source->fields[0],0xffffffffu))==index &&
           static_cast<std::uint8_t>(number(source->fields[1],0xffffffffu))==branch)return source;
    }
    return std::nullopt;
}
}
