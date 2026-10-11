#include "db/SqliteRecoveredCharacterRepository.h"
#include "db/NativeQuestCatalog.h"
#include <nlohmann/json.hpp>
#include <sqlite3.h>
#include <filesystem>
#include <iostream>
#include <memory>

int main(int argc,char** argv) {
    if(argc!=2 && argc!=3) return 2;
    sqlite3* raw=nullptr;
    const auto path=std::filesystem::path(argv[1]).u8string();
    const auto status=sqlite3_open_v2(reinterpret_cast<const char*>(path.c_str()),&raw,SQLITE_OPEN_READONLY,nullptr);
    std::unique_ptr<sqlite3,decltype(&sqlite3_close_v2)> db(raw,sqlite3_close_v2);
    if(status!=SQLITE_OK) return 2;
    try {
        if(argc==3) {
            if(std::string(argv[2])=="--daily-parsed") {
                god2::NativeQuestCatalog catalog(db.get());const auto rows=catalog.daily_displays();
                if(rows.size()!=85)throw std::runtime_error("Complete85 parsed daily rows required");
                nlohmann::json output={{"rows",rows.size()},{"authority","NATIVE_PARSED_DISPLAY_ONLY"},{"gameplay_quests_restored",0}};
                std::cout<<output.dump()<<'\n';return 0;
            }
            if(std::string(argv[2])!="--source-records")return 2;
            god2::NativeQuestCatalog catalog(db.get());const auto counts=catalog.counts();
            nlohmann::json output={{"definitions",nlohmann::json::array()},{"descriptions",nlohmann::json::array()},
                {"requirements",nlohmann::json::array()},{"daily",nlohmann::json::array()},
                {"counts",{counts.definitions,counts.descriptions,counts.requirements,counts.daily}},
                {"authority","SOURCE_FIELDS_ONLY"}};
            const auto hex=[](const std::vector<std::uint8_t>& bytes) {
                std::string result;for(const auto byte:bytes) {
                    result.push_back("0123456789abcdef"[byte>>4]);result.push_back("0123456789abcdef"[byte&15]);
                }return result;
            };
            const auto append=[&](const char* key,const std::optional<god2::NativeQuestSourceRecord>& row) {
                if(!row)throw std::runtime_error("Incomplete source lookup");
                nlohmann::json fields=nlohmann::json::array();for(const auto& field:row->fields)fields.push_back(hex(field));
                output[key].push_back({{"raw_hex",hex(row->raw_record)},{"fields_hex",fields},
                    {"line",row->source_line},{"record_sha256",row->record_sha256}});
            };
            if(counts.definitions)for(std::uint16_t mission=1;mission<=418;++mission) {
                append("definitions",catalog.definition(mission));
                for(std::uint16_t index=0;catalog.description(mission,index);++index)
                    append("descriptions",catalog.description(mission,index));
            }
            if(counts.requirements)for(std::uint16_t serial=1;serial<=169;++serial)append("requirements",catalog.requirement_display(serial));
            if(counts.daily)for(std::uint8_t row=0;row<85;++row) {
                const auto value=catalog.daily_source(row);append("daily",value);
                const auto integer=[](const std::vector<std::uint8_t>& bytes) {
                    return static_cast<std::uint8_t>(std::stoul(std::string(bytes.begin(),bytes.end())));
                };
                const auto resolved=catalog.daily_lookup(integer(value->fields[0]),integer(value->fields[1]));
                if(!resolved || resolved->raw_record!=value->raw_record)throw std::runtime_error("Daily pair lookup mismatch");
                const auto reward=value->field(17);output["daily"].back()["reward_hex"]=reward?nlohmann::json(hex(*reward)):nlohmann::json(nullptr);
            }
            std::cout<<output.dump()<<'\n';return 0;
        }
        god2::SqliteRecoveredCharacterRepository repository(db.get());
        const auto counts=repository.load_quest_description_counts();
        for(const auto count:counts) std::cout<<count<<' ';
        std::cout<<'\n';
        return 0;
    } catch(const std::exception& error) {
        std::cerr<<error.what()<<'\n';return 1;
    }
}
