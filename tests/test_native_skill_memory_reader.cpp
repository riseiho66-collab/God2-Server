#include "db/NativeSkillCatalog.h"
#include <sqlite3.h>
#include <nlohmann/json.hpp>
#include <array>
#include <iostream>
#include <stdexcept>
int main(int argc,char** argv) {
    sqlite3* db=nullptr;
    try {
        if(argc!=2 || sqlite3_open_v2(argv[1],&db,SQLITE_OPEN_READONLY,nullptr)!=SQLITE_OK)
            throw std::runtime_error("Expected readable catalog path");
        nlohmann::json rows=nlohmann::json::array();
        {
            const god2::NativeSkillCatalog catalog(db);
            constexpr std::array<int,4> counts{121,129,87,111};
            for(int kind=0;kind<4;++kind) {
                for(int id=1;id<=counts[static_cast<std::size_t>(kind)];++id) {
                    const auto row=catalog.lookup(god2::NativeSkillCatalog::current_dataset_id,kind,id);
                    if(!row || row->source.row_count!=448)throw std::runtime_error("Full skill source required");
                    std::string bytes;
                    for(const auto value:row->raw_record) {
                        bytes+="0123456789abcdef"[value>>4];bytes+="0123456789abcdef"[value&15];
                    }
                    rows.push_back({{"kind",kind},{"id",id},{"raw_hex",bytes},{"mp",row->client_mp_threshold()}});
                }
                if(catalog.lookup(god2::NativeSkillCatalog::current_dataset_id,kind,counts[static_cast<std::size_t>(kind)]+1))
                    throw std::runtime_error("Unexpected source identity");
            }
        }
        sqlite3_close(db);db=nullptr;
        std::cout<<nlohmann::json{{"rows",rows},{"authority","NATIVE_SKILL_SOURCE_AND_CLIENT_MP_THRESHOLD_ONLY"}}.dump()<<'\n';
        return 0;
    } catch(const std::exception& error) {
        if(db)sqlite3_close(db);std::cerr<<error.what()<<'\n';return 1;
    }
}
