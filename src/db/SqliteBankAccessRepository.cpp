#include "db/SqliteBankAccessRepository.h"
#include "db/SqliteSupport.h"
#include "protocol/RecoveredNpcRecord.h"
namespace god2 {
void SqliteBankAccessRepository::install_schema() {
    sqlite_detail::execute(db_,R"(
CREATE TABLE IF NOT EXISTS world_bank_service_points(
 area INTEGER NOT NULL CHECK(area BETWEEN 0 AND 16),
 scene INTEGER NOT NULL CHECK(scene BETWEEN 0 AND 1023),
 opcode INTEGER NOT NULL DEFAULT 114 CHECK(opcode=114),
 identity INTEGER NOT NULL CHECK(identity BETWEEN 1 AND 65535),
 origin TEXT NOT NULL CHECK(origin IN ('NATIVE_BANK_ROLE_VERIFIED','ISOLATED_TEST_ONLY')),
 provenance TEXT NOT NULL CHECK(length(provenance) BETWEEN 1 AND 512),
 design_id TEXT NOT NULL CHECK(design_id='CUSTOM-0064'),
 PRIMARY KEY(area,scene,identity),
 FOREIGN KEY(area,scene,opcode,identity) REFERENCES world_display_records(area,scene,opcode,identity));
)");
}
std::optional<StoredWorldDisplay> SqliteBankAccessRepository::lookup(std::uint16_t area,
    std::uint16_t scene,std::uint16_t identity,bool isolated) const {
    sqlite_detail::Statement query(db_,"SELECT origin,provenance,design_id FROM world_bank_service_points "
        "WHERE area=? AND scene=? AND identity=? AND (origin='NATIVE_BANK_ROLE_VERIFIED' OR ?=1)");
    query.bind(1,area);query.bind(2,scene);query.bind(3,identity);query.bind(4,isolated?1:0);
    if(!query.row())return {};
    const auto origin=query.text(0),provenance=query.text(1);
    if(query.text(2)!="CUSTOM-0064" || provenance.empty() || provenance.size()>512 ||
       (origin!="NATIVE_BANK_ROLE_VERIFIED" && origin!="ISOLATED_TEST_ONLY"))
        throw DatabaseError("Bank role provenance invalid");
    // Existing reader qualifies byte identity, scene, native build and pools.
    for(const auto& row:SqliteWorldDisplayRepository(db_).load(area,scene,isolated)) {
        const auto npc=RecoveredNpcRecord::parse(row.logical);
        if(!npc || npc->primarySelector()!=identity)continue;
        if((origin=="NATIVE_BANK_ROLE_VERIFIED" && row.origin!="NATIVE_CAPTURE_VERIFIED") ||
           (origin=="ISOLATED_TEST_ONLY" && row.origin!="ISOLATED_TEST_ONLY"))
            throw DatabaseError("Bank role/placement evidence mismatch");
        //61/62 targets are WORDs. A high raw selector is not silently narrowed.
        if(npc->rawSelector()!=identity)throw DatabaseError("Bank target not WORD representable");
        return row;
    }
    throw DatabaseError("Bank role has no qualified matching NPC placement");
}
}
