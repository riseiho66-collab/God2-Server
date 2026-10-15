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
    reject_scene_reentry();
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
    reject_scene_reentry();return load_levels_impl(area,scene,isolated_test,false);
}
std::vector<StoredMonsterLevel> SqliteWorldDisplayRepository::load_levels_impl(
        std::uint16_t area,std::uint16_t scene,bool isolated_test,bool main) const {
    if(area>=17 || scene>1023)throw DatabaseError("Monster level scene out of range");
    sqlite_detail::Statement query(db_,main?
        "SELECT l.identity,l.level,l.origin,l.provenance,d.origin FROM main.world_monster_levels l LEFT JOIN main.world_display_records d ON d.area=l.area AND d.scene=l.scene AND d.opcode=113 AND d.identity=l.identity WHERE l.area=? AND l.scene=? AND (l.origin='NATIVE_CAPTURE_VERIFIED' OR ?=1) ORDER BY l.identity":
        "SELECT l.identity,l.level,l.origin,l.provenance,d.origin FROM world_monster_levels l LEFT JOIN world_display_records d ON d.area=l.area AND d.scene=l.scene AND d.opcode=113 AND d.identity=l.identity WHERE l.area=? AND l.scene=? AND (l.origin='NATIVE_CAPTURE_VERIFIED' OR ?=1) ORDER BY l.identity");
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
    reject_scene_reentry();
    const auto identity=validate(record);
    sqlite_detail::Statement statement(db_,"INSERT INTO world_display_records VALUES(?,?,?,?,?,?,?,?)");
    statement.bind(1,record.area);statement.bind(2,record.scene);statement.bind(3,record.logical[0]);
    statement.bind(4,identity);statement.bind_blob(5,record.logical);statement.bind(6,record.origin);statement.bind(7,record.provenance);
    statement.bind(8,std::string("149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763"));statement.done();
}
std::vector<StoredWorldDisplay> SqliteWorldDisplayRepository::load(std::uint16_t area,std::uint16_t scene,bool isolated_test) const {
    reject_scene_reentry();return load_rows_impl(area,scene,isolated_test,false);
}
std::vector<StoredWorldDisplay> SqliteWorldDisplayRepository::load_rows_impl(
        std::uint16_t area,std::uint16_t scene,bool isolated_test,bool main) const {
    if(area>=17 || scene>1023)throw DatabaseError("World display scene out of range");
    sqlite_detail::Statement query(db_,main?
        "SELECT logical,origin,provenance,opcode,identity,native_image_sha256 FROM main.world_display_records WHERE area=? AND scene=? AND (origin='NATIVE_CAPTURE_VERIFIED' OR ?=1) ORDER BY opcode,identity":
        "SELECT logical,origin,provenance,opcode,identity,native_image_sha256 FROM world_display_records WHERE area=? AND scene=? AND (origin='NATIVE_CAPTURE_VERIFIED' OR ?=1) ORDER BY opcode,identity");
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

struct SqliteWorldDisplayRepository::SceneReadset::Data {
    const std::shared_ptr<const Identity> issuer;
    const std::uint16_t area,scene;
    const bool isolated;
    const std::vector<StoredWorldDisplay> rows;
    const std::vector<StoredMonsterLevel> levels;
    const NativeNpcDisplayCatalog::References npcs;
    const NativeEnemyDisplayCatalog::References enemies;
    Data(std::shared_ptr<const Identity> identity,std::uint16_t a,std::uint16_t s,bool test,
        std::vector<StoredWorldDisplay> records,std::vector<StoredMonsterLevel> attributes,
        NativeNpcDisplayCatalog::References npc_rows,NativeEnemyDisplayCatalog::References enemy_rows)
        :issuer(std::move(identity)),area(a),scene(s),isolated(test),rows(std::move(records)),
         levels(std::move(attributes)),npcs(std::move(npc_rows)),enemies(std::move(enemy_rows)){}
    bool operator==(const Data&) const=default;
};
struct SqliteWorldDisplayRepository::Operation {
    const SqliteWorldDisplayRepository& source;
    explicit Operation(const SqliteWorldDisplayRepository& owner):source(owner) {
        if(source.thread_!=std::this_thread::get_id()||!source.db_)
            throw DatabaseError("World display scene observation owner mismatch");
        if(source.poisoned_.load())throw DatabaseError("World display scene observer retired");
        if(source.busy_.exchange(true)){
            source.poisoned_.store(true);throw DatabaseError("World display scene observer reentered");
        }
    }
    ~Operation(){source.busy_.store(false);}
};
void SqliteWorldDisplayRepository::reject_scene_reentry() const {
    if(busy_.load()){
        poisoned_.store(true);throw DatabaseError("World display legacy access during scene observation");
    }
}
struct SqliteWorldDisplayRepository::ReadScope {
    const SqliteWorldDisplayRepository& source;
    const sqlite3_int64 changes;
    bool owns=false,finished=false;
    explicit ReadScope(const SqliteWorldDisplayRepository& owner)
        :source(owner),changes(sqlite3_total_changes64(owner.db_)) {}
    void begin(){
        // The Scope is already constructed before BEGIN or any fence can throw.
        if(sqlite3_get_autocommit(source.db_)){
            sqlite_detail::execute(source.db_,"BEGIN");owns=true;
        }
        fence();
    }
    void fence(){
        if(sqlite3_get_autocommit(source.db_)){
            // Once an end is OBSERVED this scope permanently loses rollback
            // ownership; a later foreign transaction cannot revive it.
            owns=false;throw DatabaseError("World display scene read transaction ended");
        }
        if(source.poisoned_.load()||!source.busy_.load()||sqlite3_total_changes64(source.db_)!=changes)
            throw DatabaseError("World display scene read changed or reentered");
    }
    void finish(){
        fence();
        if(owns){
            try{sqlite_detail::execute(source.db_,"COMMIT");}
            catch(...){if(sqlite3_get_autocommit(source.db_))owns=false;throw;}
            owns=false;finished=true; // Never roll back a post-COMMIT successor.
            if(!sqlite3_get_autocommit(source.db_)||source.poisoned_.load()||
               sqlite3_total_changes64(source.db_)!=changes)
                throw DatabaseError("World display scene read changed at commit");
        }else finished=true; // Borrowed caller transaction remains untouched.
    }
    ~ReadScope(){
        if(owns&&!finished){
            if(sqlite3_get_autocommit(source.db_))owns=false;
            else sqlite3_exec(source.db_,"ROLLBACK",nullptr,nullptr,nullptr);
        }
    }
};
namespace {
void world_display_scene_namespaces(sqlite3* db,bool npcs,bool enemies) {
    sqlite_detail::Statement shadows(db,
        "SELECT 1 FROM temp.sqlite_master WHERE "
        "name COLLATE NOCASE IN ('world_display_records','world_monster_levels') OR "
        "tbl_name COLLATE NOCASE IN ('world_display_records','world_monster_levels') OR "
        "(?=1 AND (name COLLATE NOCASE IN ('native_npc_display_sources','native_npc_display_rows') OR "
        "tbl_name COLLATE NOCASE IN ('native_npc_display_sources','native_npc_display_rows'))) OR "
        "(?=1 AND (name COLLATE NOCASE IN ('native_data_sources','native_enemy_display_catalog') OR "
        "tbl_name COLLATE NOCASE IN ('native_data_sources','native_enemy_display_catalog'))) LIMIT 1");
    shadows.bind(1,npcs?1:0);shadows.bind(2,enemies?1:0);
    if(shadows.row())throw DatabaseError("World display scene namespace shadow");
    sqlite_detail::Statement tables(db,
        "SELECT count(*) FROM main.sqlite_master WHERE type='table' AND ("
        "name COLLATE NOCASE IN ('world_display_records','world_monster_levels') OR "
        "(?=1 AND name COLLATE NOCASE IN ('native_npc_display_sources','native_npc_display_rows')) OR "
        "(?=1 AND name COLLATE NOCASE IN ('native_data_sources','native_enemy_display_catalog')))");
    tables.bind(1,npcs?1:0);tables.bind(2,enemies?1:0);
    if(!tables.row()||tables.integer(0)!=2+(npcs?2:0)+(enemies?2:0))
        throw DatabaseError("World display scene requires actual main tables");
}
}
std::shared_ptr<const SqliteWorldDisplayRepository::SceneReadset::Data>
SqliteWorldDisplayRepository::capture_scene(const NativeNpcDisplayCatalog& npcs,const NativeEnemyDisplayCatalog& enemies,
        std::uint16_t area,std::uint16_t scene,bool isolated) const {
    if(area>=17||scene>1023||!npcs.uses_connection(db_)||!enemies.uses_connection(db_))
        throw DatabaseError("World display scene requires exact same connection and selectors");
    ReadScope scope(*this);scope.begin();
    world_display_scene_namespaces(db_,false,false);scope.fence();
    auto rows=load_rows_impl(area,scene,isolated,true);scope.fence();
    auto levels=load_levels_impl(area,scene,isolated,true);scope.fence();
    std::vector<std::uint16_t> npc_keys;
    std::vector<NativeEnemyDisplayCatalog::Key> enemy_keys;
    for(const auto& row:rows){
        if(const auto npc=RecoveredNpcRecord::parse(row.logical)){
            npc_keys.push_back(npc->primarySelector());
            if(npc->secondarySelector())npc_keys.push_back(npc->secondarySelector());
        }else if(const auto enemy=RecoveredMonsterRecord::parse(row.logical)){
            // Native catalog selector namespace is independent of placement.
            enemy_keys.push_back({enemy->catalogArea(),enemy->catalogScene(),enemy->catalogOrdinal()});
        }else throw DatabaseError("World display scene contains unknown full record");
    }
    const bool needs_npcs=!npc_keys.empty(),needs_enemies=!enemy_keys.empty();
    world_display_scene_namespaces(db_,needs_npcs,needs_enemies);scope.fence();
    NativeNpcDisplayCatalog::References npc_refs;
    NativeEnemyDisplayCatalog::References enemy_refs;
    if(needs_npcs){npc_refs=npcs.read_references(npc_keys);scope.fence();}
    if(needs_enemies){enemy_refs=enemies.read_references(enemy_keys);scope.fence();}
    world_display_scene_namespaces(db_,needs_npcs,needs_enemies);scope.fence();
    // All returned statements are finalized before commit. Own every value
    // allocation BEFORE the final fence; subsequent shared-pointer copies and
    // the private SceneReadset constructor do not allocate or call observers.
    auto result=std::make_shared<const SceneReadset::Data>(identity_,area,scene,isolated,
        std::move(rows),std::move(levels),std::move(npc_refs),std::move(enemy_refs));
    scope.fence();scope.finish();return result;
}
SqliteWorldDisplayRepository::SceneReadset SqliteWorldDisplayRepository::observe_scene(
        const NativeNpcDisplayCatalog& npcs,const NativeEnemyDisplayCatalog& enemies,
        std::uint16_t area,std::uint16_t scene,bool isolated) const {
    Operation operation(*this);return SceneReadset(capture_scene(npcs,enemies,area,scene,isolated));
}
bool SqliteWorldDisplayRepository::current_scene(const SceneReadset& value,
        const NativeNpcDisplayCatalog& npcs,const NativeEnemyDisplayCatalog& enemies) const noexcept {
    const auto retained=value.data_; // Own the actual old value BEFORE any SQL.
    if(!retained||retained->issuer!=identity_)return false;
    try{
        Operation operation(*this);
        const auto fresh=capture_scene(npcs,enemies,retained->area,retained->scene,retained->isolated);
        return !poisoned_.load()&&retained->issuer==identity_&&*fresh==*retained;
    }catch(...){return false;}
}
std::uint16_t SqliteWorldDisplayRepository::SceneReadset::area() const noexcept{return data_->area;}
std::uint16_t SqliteWorldDisplayRepository::SceneReadset::scene() const noexcept{return data_->scene;}
bool SqliteWorldDisplayRepository::SceneReadset::isolated_test() const noexcept{return data_->isolated;}
const std::vector<StoredWorldDisplay>& SqliteWorldDisplayRepository::SceneReadset::rows() const noexcept{return data_->rows;}
const std::vector<StoredMonsterLevel>& SqliteWorldDisplayRepository::SceneReadset::levels() const noexcept{return data_->levels;}
const NativeNpcDisplayCatalog::References& SqliteWorldDisplayRepository::SceneReadset::npc_references() const noexcept{return data_->npcs;}
const NativeEnemyDisplayCatalog::References& SqliteWorldDisplayRepository::SceneReadset::enemy_references() const noexcept{return data_->enemies;}
}
