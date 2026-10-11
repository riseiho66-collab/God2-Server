#include "db/NativeEnemyDisplayCatalog.h"
#include "protocol/RecoveredBattleEnemyDisplay.h"
#include "db/SqliteMigrationManager.h"
#include "db/SqliteSupport.h"

#include <iostream>
#include <memory>
#include <stdexcept>
#include <string>

namespace {
void require(bool value,const char* message) {
    if(!value) throw std::runtime_error(message);
}
template<class F> void rejects(F&& f) {
    try { f(); } catch(const god2::DatabaseError&) { return; }
    throw std::runtime_error("Invalid enemy display lookup accepted");
}
struct Fixture {
    struct Close { void operator()(sqlite3* db) const { sqlite3_close_v2(db); } };
    std::unique_ptr<sqlite3,Close> db;
    Fixture() {
        sqlite3* raw=nullptr;
        require(sqlite3_open(":memory:",&raw)==SQLITE_OK,"Unable to open SQLite test database");
        db.reset(raw);
        god2::sqlite_detail::execute(db.get(),"PRAGMA foreign_keys=ON");
        god2::SqliteMigrationManager(db.get(),god2::default_sqlite_migrations()).migrate();
        god2::SqliteMigrationManager(db.get(),god2::default_sqlite_migrations()).migrate();
        god2::sqlite_detail::Statement count(db.get(),"SELECT count(*) FROM native_enemy_display_catalog");
        require(count.row() && count.integer(0)==0,"Migration invented enemy display records");
    }
    void source() {
        god2::sqlite_detail::Statement row(db.get(),
            "INSERT INTO native_data_sources VALUES(?,?,?,?,?,?,?,?,?)");
        row.bind(1,std::string(god2::NativeEnemyDisplayCatalog::current_dataset_id));
        row.bind(2,std::string("test-only/gamedata.csvZ"));
        row.bind(3,std::string(64,'a'));row.bind(4,std::string(64,'b'));
        row.bind(5,std::string(64,'c'));row.bind(6,std::string("EnyName"));
        row.bind(7,std::string("0x5a1a0"));row.bind(8,std::string("0x5a0a0"));
        row.bind(9,std::int64_t{7815});row.done();
    }
    void record(int index,int visible,int area,int scene,int ordinal) {
        god2::sqlite_detail::Statement row(db.get(),
            "INSERT INTO native_enemy_display_catalog VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)");
        row.bind(1,std::string(god2::NativeEnemyDisplayCatalog::current_dataset_id));
        row.bind(2,std::int64_t{index});row.bind(3,std::int64_t{21732+index});
        row.bind(4,std::int64_t{2500917+index});row.bind(5,std::string(64,'d'));
        const std::vector<std::uint8_t> raw{'1',',','A','B','\n'};
        row.bind_blob(6,raw);row.bind(7,std::int64_t{1});
        row.bind(8,std::int64_t{area});row.bind(9,std::int64_t{scene});
        row.bind(10,std::int64_t{ordinal});row.bind(11,std::int64_t{visible});
        row.bind(12,std::int64_t{1});
        const std::vector<std::uint8_t> name{'A','B'};
        row.bind_blob(13,name);row.done();
    }
    god2::NativeEnemyDisplayCatalog reader() const {
        return god2::NativeEnemyDisplayCatalog(db.get());
    }
};
}

int main(int argc,char** argv) {
    try {
        if(argc==2) {
            sqlite3* raw=nullptr;
            require(sqlite3_open_v2(argv[1],&raw,SQLITE_OPEN_READONLY,nullptr)==SQLITE_OK,
                    "Unable to open imported SQLite database");
            Fixture::Close close;
            std::unique_ptr<sqlite3,Fixture::Close> db(raw,close);
            const god2::NativeEnemyDisplayCatalog reader(db.get());
            god2::RecoveredBattleIdentity::Bytes packet{};
            packet[0]=0x1c;packet[1]=14;packet[6]=4;packet[7]=1;packet[9]=2;
            const auto identity=god2::RecoveredBattleIdentity::parse_logical(packet);
            require(identity.has_value(),"Unable to parse normal enemy display packet");
            const auto first=god2::resolve_normal_enemy_display(reader,*identity);
            const auto last=reader.lookup(god2::NativeEnemyDisplayCatalog::current_dataset_id,2,0,27);
            require(first && last && first->source_line==21732 && last->source_line==21758 &&
                    first->source.source_sha256==last->source.source_sha256 &&
                    first->name_bytes==std::vector<std::uint8_t>({0xb5,0xb3,0xa4,0xf2,0xc0,0x6e}) &&
                    last->name_bytes==std::vector<std::uint8_t>({0xbf,0xb3,0xbe,0xc4,0xb7,0xe1,0xb5,0x55}),
                    "Imported Island01 enemy identity mismatch");
            packet[7]=28;
            require(!god2::resolve_normal_enemy_display(reader,*god2::RecoveredBattleIdentity::parse_logical(packet)),
                    "Island01 accepted an absent enemy display ordinal");
            packet[6]=0;
            try {
                (void)god2::resolve_normal_enemy_display(reader,*god2::RecoveredBattleIdentity::parse_logical(packet));
                throw std::runtime_error("Unsupported display variant was accepted");
            } catch(const std::invalid_argument&) {}
            std::cout<<"Imported Island01 C++ enemy display lookups passed\n";
            return 0;
        }
        require(argc==1,"Usage: native-enemy-display-catalog [imported-database]");
        Fixture fixture;
        fixture.source();
        fixture.record(0,0,2,0,1); // Superseded area generation does not shadow lookup.
        fixture.record(1,1,2,0,1);
        const auto reader=fixture.reader();
        const auto found=reader.lookup(god2::NativeEnemyDisplayCatalog::current_dataset_id,2,0,1);
        require(found && found->source_record_index==1 && found->source_line==21733 &&
                found->name_bytes==std::vector<std::uint8_t>({'A','B'}) &&
                found->source.row_count==7815,"Visible enemy display lookup mismatch");
        require(!reader.lookup(god2::NativeEnemyDisplayCatalog::current_dataset_id,2,0,2),
                "Missing enemy display key should stay absent");
        rejects([&]{(void)reader.lookup(god2::NativeEnemyDisplayCatalog::current_dataset_id,17,0,1);});
        rejects([&]{(void)reader.lookup(god2::NativeEnemyDisplayCatalog::current_dataset_id,2,0,0);});
        rejects([&]{(void)reader.lookup("",2,0,1);});
        god2::sqlite_detail::execute(fixture.db.get(),
            "UPDATE native_data_sources SET row_count=1 WHERE dataset_id='current-enyname-display-v1'");
        rejects([&]{(void)reader.lookup(god2::NativeEnemyDisplayCatalog::current_dataset_id,2,0,1);});
        std::cout<<"Native enemy display migration and read-only selector passed\n";
    } catch(const std::exception& error) { std::cerr<<error.what()<<'\n'; return 1; }
}
