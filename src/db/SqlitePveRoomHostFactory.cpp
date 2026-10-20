#include "db/SqliteDatabase.h"
#include "db/SqliteOwnedPveRoomRepository.h"
#include "db/SqliteSupport.h"
#include "game/OwnedPveWorldCatalog.h"
#include <stdexcept>
#include <set>
namespace god2 {
std::unique_ptr<SqliteOwnedPveRoomRepository> SqliteDatabase::make_owned_pve_room_repository() {
    auto* connection=owned_pve_connection();
    auto* characters=dynamic_cast<SqliteRecoveredCharacterRepository*>(&recovered_characters());
    if(!characters)throw std::logic_error("PvE host requires the actual same-connection character repository");
    auto result=std::make_unique<SqliteOwnedPveRoomRepository>(connection,accounts(),*characters,
        role_auxiliary(),companions());
    if(!result->uses_connection(connection))throw std::logic_error("PvE repository connection drift");
    return result;
}
void SqliteDatabase::install_owned_pve_room_schema() {
    // Explicit source-only operation. Neither normal startup nor this factory
    // silently creates tables or adopts durable claims from an older process.
    SqliteOwnedPveRoomRepository::install_schema(owned_pve_connection());
}
void SqliteDatabase::install_owned_pve_world_catalog_schema() {
    sqlite_detail::execute(owned_pve_connection(),
        "CREATE TABLE owned_pve_world_catalog("
        "slot INTEGER PRIMARY KEY CHECK(slot=1),version INTEGER NOT NULL CHECK(version>0),"
        "source_sha256 TEXT NOT NULL CHECK(length(source_sha256)=64),"
        "source_record TEXT NOT NULL,catalog_json TEXT NOT NULL) STRICT;");
}
std::shared_ptr<const OwnedPveWorldCatalog> SqliteDatabase::load_owned_pve_world_catalog() {
    auto* db=owned_pve_connection();
    if(!sqlite3_get_autocommit(db))throw DatabaseError("PvE catalog requires an independent whole-version read");
    sqlite_detail::Statement shadow(db,"SELECT name FROM sqlite_temp_schema WHERE name='owned_pve_world_catalog'");
    if(shadow.row())throw DatabaseError("PvE catalog TEMP shadow refused");
    sqlite_detail::Statement table(db,"SELECT type FROM main.sqlite_schema WHERE name='owned_pve_world_catalog'");
    if(!table.row()||table.text(0)!="table"||table.row())throw DatabaseError("PvE catalog requires its actual main table");
    sqlite_detail::Statement q(db,"SELECT slot,version,source_sha256,source_record,catalog_json FROM main.owned_pve_world_catalog");
    if(!q.row()||q.number<std::uint64_t>(0)!=1)throw DatabaseError("PvE requires one explicitly provisioned complete source catalog");
    const auto version=q.number<std::uint64_t>(1);const auto sha=q.text(2),record=q.text(3),document=q.text(4);
    if(q.row()||document.empty()||document.size()>64u*1024u*1024u)throw DatabaseError("PvE whole catalog rows/size invalid");
    std::vector<std::set<std::string>> keys;
    const auto parse=[&](int depth,nlohmann::json::parse_event_t event,nlohmann::json& value) {
        if(depth>32)throw DatabaseError("PvE catalog nesting exceeds bounded source format");
        if(event==nlohmann::json::parse_event_t::object_start)keys.emplace_back();
        if(event==nlohmann::json::parse_event_t::key&&
           (keys.empty()||!keys.back().insert(value.get<std::string>()).second))
            throw DatabaseError("PvE catalog duplicate source field");
        if(event==nlohmann::json::parse_event_t::object_end)keys.pop_back();
        if(event==nlohmann::json::parse_event_t::value&&value.is_number_float())
            throw DatabaseError("PvE catalog requires exact integer units");
        return true;
    };
    auto result=std::make_shared<const OwnedPveWorldCatalog>(nlohmann::json::parse(document,parse));
    if(result->version()!=version||result->source_sha256()!=sha||result->source_record()!=record)
        throw DatabaseError("PvE whole catalog provenance/version differs from its document");
    return result;
}
}
