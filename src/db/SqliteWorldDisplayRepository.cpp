#include "db/SqliteWorldDisplayRepository.h"
#include "db/SqliteSupport.h"
#include "protocol/RecoveredMonsterRecord.h"
#include "protocol/RecoveredNpcRecord.h"
#include <algorithm>
namespace god2 {
namespace {
std::uint16_t validate(const StoredWorldDisplay& row) {
    if(row.area>=17 || row.scene>1023 || row.provenance.empty() || row.provenance.size()>512 ||
       (row.origin!="NATIVE_CAPTURE_VERIFIED" && row.origin!="ISOLATED_TEST_ONLY"))
        throw DatabaseError("World display requires explicit scene and provenance");
    if(const auto npc=RecoveredNpcRecord::parse(row.logical))return npc->instanceIdentity();
    if(const auto monster=RecoveredMonsterRecord::parse(row.logical)) {
        if(monster->catalogArea()>=17 || !monster->catalogOrdinal())throw DatabaseError("Invalid enemy display namespace");
        return monster->identity();
    }
    throw DatabaseError("World display requires exact native71/72 record");
}
}
const char* SqliteWorldDisplayRepository::schema() noexcept {return R"SQL(
CREATE TABLE world_display_records (
 area INTEGER NOT NULL CHECK(area BETWEEN 0 AND 16),
 scene INTEGER NOT NULL CHECK(scene BETWEEN 0 AND 1023),
 opcode INTEGER NOT NULL CHECK(opcode IN (113,114)),
 identity INTEGER NOT NULL CHECK(identity BETWEEN 0 AND 65535),
 logical BLOB NOT NULL CHECK(typeof(logical)='blob' AND length(logical)=21),
 origin TEXT NOT NULL CHECK(origin IN ('NATIVE_CAPTURE_VERIFIED','ISOLATED_TEST_ONLY')),
 provenance TEXT NOT NULL CHECK(length(provenance) BETWEEN 1 AND 512),
 native_image_sha256 TEXT NOT NULL CHECK(native_image_sha256='149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763'),
 PRIMARY KEY(area,scene,opcode,identity)
);
)SQL";}
const char* SqliteWorldDisplayRepository::level_schema() noexcept {return R"SQL(
CREATE TABLE world_monster_levels (
 area INTEGER NOT NULL CHECK(area BETWEEN 0 AND 16),
 scene INTEGER NOT NULL CHECK(scene BETWEEN 0 AND 1023),
 opcode INTEGER NOT NULL DEFAULT 113 CHECK(opcode=113),
 identity INTEGER NOT NULL CHECK(identity BETWEEN 0 AND 65535),
 level INTEGER NOT NULL CHECK(level BETWEEN 0 AND 65535),
 origin TEXT NOT NULL CHECK(origin IN ('NATIVE_CAPTURE_VERIFIED','ISOLATED_TEST_ONLY')),
 provenance TEXT NOT NULL CHECK(length(provenance) BETWEEN 1 AND 512),
 PRIMARY KEY(area,scene,identity),
 FOREIGN KEY(area,scene,opcode,identity) REFERENCES world_display_records(area,scene,opcode,identity)
);
)SQL";}
void SqliteWorldDisplayRepository::insert_level(const StoredMonsterLevel& record) {
    if(record.area>=17 || record.scene>1023 || record.provenance.empty() || record.provenance.size()>512 ||
       (record.origin!="NATIVE_CAPTURE_VERIFIED" && record.origin!="ISOLATED_TEST_ONLY"))
        throw DatabaseError("Monster level requires explicit source provenance");
    sqlite_detail::Statement insert(db_,"INSERT INTO world_monster_levels(area,scene,identity,level,origin,provenance) SELECT ?,?,?,?,?,? FROM world_display_records WHERE area=? AND scene=? AND opcode=113 AND identity=? AND origin=?");
    insert.bind(1,record.area);insert.bind(2,record.scene);insert.bind(3,record.identity);insert.bind(4,record.level);
    insert.bind(5,record.origin);insert.bind(6,record.provenance);insert.bind(7,record.area);insert.bind(8,record.scene);
    insert.bind(9,record.identity);insert.bind(10,record.origin);insert.done();
    if(sqlite3_changes(db_)!=1)throw DatabaseError("Monster level has no matching source-owned instance");
}
std::vector<StoredMonsterLevel> SqliteWorldDisplayRepository::load_levels(std::uint16_t area,std::uint16_t scene,bool isolated_test) const {
    if(area>=17 || scene>1023)throw DatabaseError("Monster level scene out of range");
    sqlite_detail::Statement query(db_,"SELECT l.identity,l.level,l.origin,l.provenance,d.origin FROM world_monster_levels l LEFT JOIN world_display_records d ON d.area=l.area AND d.scene=l.scene AND d.opcode=113 AND d.identity=l.identity WHERE l.area=? AND l.scene=? AND (l.origin='NATIVE_CAPTURE_VERIFIED' OR ?=1) ORDER BY l.identity");
    query.bind(1,area);query.bind(2,scene);query.bind(3,isolated_test?1:0);
    std::vector<StoredMonsterLevel> result;
    while(query.row()) {
        StoredMonsterLevel row{area,scene,query.number<std::uint16_t>(0),query.number<std::uint16_t>(1),query.text(2),query.text(3)};
        if(row.origin!=query.text(4) || row.provenance.empty() || row.provenance.size()>512 ||
           (row.origin!="NATIVE_CAPTURE_VERIFIED" && row.origin!="ISOLATED_TEST_ONLY"))
            throw DatabaseError("Monster level source/instance mismatch");
        if(result.size()>=256)throw DatabaseError("Monster levels exceed pool");
        result.push_back(std::move(row));
    }
    return result;
}
void SqliteWorldDisplayRepository::insert(const StoredWorldDisplay& record) {
    const auto identity=validate(record);
    sqlite_detail::Statement statement(db_,"INSERT INTO world_display_records VALUES(?,?,?,?,?,?,?,?)");
    statement.bind(1,record.area);statement.bind(2,record.scene);statement.bind(3,record.logical[0]);
    statement.bind(4,identity);statement.bind_blob(5,record.logical);statement.bind(6,record.origin);statement.bind(7,record.provenance);
    statement.bind(8,std::string("149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763"));statement.done();
}
std::vector<StoredWorldDisplay> SqliteWorldDisplayRepository::load(std::uint16_t area,std::uint16_t scene,bool isolated_test) const {
    if(area>=17 || scene>1023)throw DatabaseError("World display scene out of range");
    sqlite_detail::Statement query(db_,"SELECT logical,origin,provenance,opcode,identity,native_image_sha256 FROM world_display_records WHERE area=? AND scene=? AND (origin='NATIVE_CAPTURE_VERIFIED' OR ?=1) ORDER BY opcode,identity");
    query.bind(1,area);query.bind(2,scene);query.bind(3,isolated_test?1:0);
    std::vector<StoredWorldDisplay> result;std::size_t npcs=0,monsters=0;
    while(query.row()) {
        StoredWorldDisplay row{area,scene,{},query.text(1),query.text(2)};
        const auto bytes=query.blob(0,21,21);std::copy(bytes.begin(),bytes.end(),row.logical.begin());
        if(validate(row)!=query.number<std::uint16_t>(4) || row.logical[0]!=query.number<std::uint8_t>(3) ||
           query.text(5)!="149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763")
            throw DatabaseError("World display stored identity or build mismatch");
        if(row.logical[0]==0x72)++npcs;else ++monsters;
        // Both 1D878-byte pools contain 256 records at70, stride1D8.
        if(npcs>256 || monsters>256)throw DatabaseError("World display exceeds native pools");
        result.push_back(std::move(row));
    }
    return result;
}
}
