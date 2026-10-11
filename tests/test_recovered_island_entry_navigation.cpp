#include "game/RecoveredIslandEntryNavigation.h"
#include <fstream>
#include <nlohmann/json.hpp>
#include <stdexcept>

int main() {
    const auto source=std::filesystem::path(GOD2_SOURCE_DIR)/
        "artifacts/world-atlas/island01-entry-2-0.json";
    const god2::RecoveredIslandEntryNavigation navigation(source);
    if(navigation.conflict_count()!=212 || navigation.consistent_cell(477,209)!=2 ||
       navigation.consistent_cell(476,209)!=1 || navigation.consistent_cell(472,223) ||
       navigation.consistent_cell(1,1)) return 1;
    nlohmann::json data;
    { std::ifstream in(source); in>>data; }
    const auto temporary=std::filesystem::temp_directory_path()/"god2-island-nav-invalid.json";
    data["windows"][0]["cells_hex"]="00";
    { std::ofstream out(temporary); out<<data; }
    bool rejected=false;
    try { (void)god2::RecoveredIslandEntryNavigation(temporary); }
    catch(const std::exception&) { rejected=true; }
    std::filesystem::remove(temporary);
    return rejected?0:2;
}
