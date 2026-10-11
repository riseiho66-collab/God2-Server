#include "db/SqlitePlayerAppearanceRepository.h"
#include "db/SqliteSupport.h"
#include <filesystem>
#include <iostream>
#include <limits>
#include <memory>
#include <random>
#include <stdexcept>

namespace {
using Repo = god2::SqlitePlayerAppearanceRepository;
using Fields = god2::RecoveredPlayerAppearanceUpdate::Fields;
void require(bool value, const char* message) { if (!value) throw std::runtime_error(message); }
template<class F> void rejects(F call) {
    try { call(); } catch (const god2::DatabaseError&) { return; }
    throw std::runtime_error("Expected appearance DatabaseError");
}
struct Close { void operator()(sqlite3* db) const { sqlite3_close_v2(db); } };
struct Fixture {
    std::unique_ptr<sqlite3,Close> db;
    explicit Fixture(const std::string& path=":memory:", bool initialize=true, bool readonly=false) {
        sqlite3* raw=nullptr;
        const int flags=readonly ? SQLITE_OPEN_READONLY : SQLITE_OPEN_READWRITE|SQLITE_OPEN_CREATE;
        const int code=sqlite3_open_v2(path.c_str(),&raw,flags,nullptr); db.reset(raw);
        require(code==SQLITE_OK,"Open disposable appearance DB");
        sql("PRAGMA foreign_keys=ON");
        if (initialize) {
            sql("CREATE TABLE recovered_characters(id INTEGER PRIMARY KEY,account_id INTEGER NOT NULL);"
                "INSERT INTO recovered_characters VALUES(4,1),(5,2),(16383,1),(16384,1);"
                "CREATE TABLE battle_reservations(id INTEGER PRIMARY KEY,character_id INTEGER NOT NULL);"
                "CREATE TABLE battle_settlements(battle_id INTEGER PRIMARY KEY);"
                "CREATE TABLE outer_work(value INTEGER NOT NULL);");
            sql(Repo::schema());
        }
    }
    void sql(const char* text) { god2::sqlite_detail::execute(db.get(),text); }
    Repo repo() { return Repo(db.get()); }
    int outer_count() {
        god2::sqlite_detail::Statement q(db.get(),"SELECT count(*) FROM outer_work");
        require(q.row(),"Outer count"); return q.number<int>(0);
    }
    std::string snapshot() {
        god2::sqlite_detail::Statement q(db.get(),
            "SELECT quote(character_id),quote(logical),quote(base_components),quote(revision),quote(origin),quote(provenance),quote(client_sha256),quote(design_id) "
            "FROM character_player_appearance_snapshots ORDER BY character_id");
        std::string out;
        while(q.row()) for(int i=0;i<8;++i) { auto text=q.text(i); out+=std::to_string(text.size())+":"+text; }
        return out;
    }
    template<class F> void unchanged(F call) {
        const auto before=snapshot(); const auto autocommit=sqlite3_get_autocommit(db.get());
        rejects(call); require(snapshot()==before,"Failed appearance operation changed rows");
        require(sqlite3_get_autocommit(db.get())==autocommit,"Failed appearance operation changed transaction ownership");
    }
};
Fields fields(std::uint16_t actor=4) { return {actor,0,0xfa,0xb7,{0x10,0x81,0x22,0xe3,0x45,0xa6,0x17,0xff}}; }
god2::StoredPlayerAppearance seed(Fixture& f) {
    return f.repo().save(1,4,std::nullopt,fields(),"CUSTOM_TEST_NOT_NATIVE","isolated synthetic DA fields; no item mapping");
}
void preservation_and_cas() {
    Fixture f; auto r=f.repo(); require(!r.load(1,4),"Load granted appearance");
    auto a=seed(f); require(a.revision==1 && a.fields==fields() && a.base_components==fields().components,"Initial DA bytes/baseline");
    require(a.client_sha256==Repo::client_sha256 && a.design_id==Repo::design_id,"Identity qualification");
    require(r.load(1,4)==std::optional(a),"Load did not preserve full record");
    auto updated=a.fields; updated.raw_scalar5=0x9a; updated.raw_scalar6=0xc1;
    for(auto& byte:updated.components) byte^=0x5a;
    auto b=r.save(1,4,1,updated,"NATIVE_CAPTURE_VERIFIED","test-only origin validation; no actual native capture");
    require(b.revision==2 && b.fields==updated && b.base_components==a.base_components,"Update lost fields or original baseline");
    f.unchanged([&]{r.save(1,4,1,updated,a.origin,a.provenance);});
    f.unchanged([&]{r.save(1,4,std::nullopt,updated,a.origin,a.provenance);});
    f.unchanged([&]{r.save(1,4,2,updated,a.origin,a.provenance,updated.components);});
    auto c=r.save(1,4,2,updated,a.origin,a.provenance,a.base_components);
    require(c.base_components==a.base_components && c.revision==3,"Matching baseline rejected");
    // A supplied baseline is permitted only on an explicit first save.
    auto far=fields(16383);auto base=far.components;base[6]=0; base[7]=0;
    auto d=r.save(1,16383,std::nullopt,far,a.origin,a.provenance,base);
    require(d.base_components==base && d.fields==far,"Explicit first baseline lost");
    require(!r.load(2,5),"Unrelated owner granted appearance");
}
void invalid_inputs_and_pending() {
    Fixture f; auto r=f.repo(); auto a=seed(f);
    for(const auto account:{std::uint64_t{0},std::uint64_t{2},std::numeric_limits<std::uint64_t>::max()}) {
        f.unchanged([&]{r.load(account,4);});
        f.unchanged([&]{r.save(account,4,1,a.fields,a.origin,a.provenance);});
    }
    for(const auto character:{std::uint64_t{0},std::uint64_t{6},std::uint64_t{16384},std::numeric_limits<std::uint64_t>::max()})
        f.unchanged([&]{r.load(1,character);});
    for(const auto revision:{std::uint64_t{0},std::uint64_t{2},std::uint64_t{9223372036854775807ULL},std::numeric_limits<std::uint64_t>::max()})
        f.unchanged([&]{r.save(1,4,revision,a.fields,a.origin,a.provenance);});
    f.unchanged([&]{r.save(1,16383,1,fields(16383),a.origin,a.provenance);});
    for(const auto actor:{0,5,16384,65535}) {auto invalid=a.fields;invalid.actor_identity=static_cast<std::uint16_t>(actor);
        f.unchanged([&]{r.save(1,4,1,invalid,a.origin,a.provenance);});}
    auto transform=a.fields;transform.transform_key=1;
    f.unchanged([&]{r.save(1,4,1,transform,a.origin,a.provenance);});
    for(const auto& provenance:{std::string{},std::string(256,'x'),std::string("x\0y",3)})
        f.unchanged([&]{r.save(1,4,1,a.fields,a.origin,provenance);});
    f.unchanged([&]{r.save(1,4,1,a.fields,"UNKNOWN",a.provenance);});
    rejects([&]{Repo(nullptr);});
    f.sql("INSERT INTO battle_reservations VALUES(1,4)");
    require(r.load(1,4)==std::optional(a),"Pending battle blocked read-only restore");
    f.unchanged([&]{r.save(1,4,1,a.fields,a.origin,a.provenance);});
    f.sql("INSERT INTO battle_settlements VALUES(1)");
    require(r.save(1,4,1,a.fields,a.origin,a.provenance).revision==2,"Settled battle still blocks save");
}
void corruption_and_readback() {
    Fixture f;auto r=f.repo();auto a=seed(f);
    const char* corruptions[]={
        "UPDATE character_player_appearance_snapshots SET logical=zeroblob(14)",
        "UPDATE character_player_appearance_snapshots SET logical=zeroblob(16)",
        "UPDATE character_player_appearance_snapshots SET logical=CAST(logical AS TEXT)",
        "UPDATE character_player_appearance_snapshots SET logical=zeroblob(15)",
        "UPDATE character_player_appearance_snapshots SET logical=X'DA05000000FAB7108122E345A617FF'",
        "UPDATE character_player_appearance_snapshots SET logical=X'DA04000100FAB7108122E345A617FF'",
        "UPDATE character_player_appearance_snapshots SET base_components=zeroblob(7)",
        "UPDATE character_player_appearance_snapshots SET base_components=zeroblob(9)",
        "UPDATE character_player_appearance_snapshots SET base_components=CAST(base_components AS TEXT)",
        "UPDATE character_player_appearance_snapshots SET revision=0",
        "UPDATE character_player_appearance_snapshots SET revision=1.5",
        "UPDATE character_player_appearance_snapshots SET provenance=''",
        "UPDATE character_player_appearance_snapshots SET provenance=CAST(X'610062' AS TEXT)",
        "UPDATE character_player_appearance_snapshots SET origin='UNQUALIFIED'",
        "UPDATE character_player_appearance_snapshots SET client_sha256=printf('%064d',0)",
        "UPDATE character_player_appearance_snapshots SET design_id='CUSTOM-0000'"};
    for(const char* change:corruptions) {
        f.sql("PRAGMA ignore_check_constraints=ON;BEGIN");f.sql(change);
        f.unchanged([&]{r.load(1,4);}); f.unchanged([&]{r.save(1,4,1,a.fields,a.origin,a.provenance);});
        f.sql("ROLLBACK;PRAGMA ignore_check_constraints=OFF");
        require(r.load(1,4)==std::optional(a),"Corruption fixture rollback");
    }
    // Trigger modifies a valid body byte after SQL succeeds: full readback must reject it.
    f.sql("CREATE TRIGGER alter_appearance AFTER UPDATE ON character_player_appearance_snapshots BEGIN "
          "UPDATE character_player_appearance_snapshots SET logical=X'DA04000000FAB7108122E345A617FE' WHERE character_id=NEW.character_id; END");
    f.unchanged([&]{r.save(1,4,1,a.fields,a.origin,a.provenance);}); f.sql("DROP TRIGGER alter_appearance");
    f.sql("CREATE TRIGGER alter_baseline AFTER UPDATE ON character_player_appearance_snapshots BEGIN "
          "UPDATE character_player_appearance_snapshots SET base_components=zeroblob(8) WHERE character_id=NEW.character_id; END");
    f.unchanged([&]{r.save(1,4,1,a.fields,a.origin,a.provenance);}); f.sql("DROP TRIGGER alter_baseline");
}
void borrowed_transaction_atomicity() {
    Fixture f;auto r=f.repo();
    f.sql("BEGIN IMMEDIATE;INSERT INTO outer_work VALUES(1)");auto a=seed(f);
    require(!sqlite3_get_autocommit(f.db.get()) && f.outer_count()==1,"Save committed caller transaction");
    f.sql("ROLLBACK");require(!r.load(1,4) && f.outer_count()==0,"Caller rollback did not remove owned snapshot");
    a=seed(f);
    f.sql("BEGIN IMMEDIATE;INSERT INTO outer_work VALUES(2)");
    f.unchanged([&]{r.save(2,4,1,a.fields,a.origin,a.provenance);});
    f.sql("CREATE TRIGGER reject_appearance BEFORE UPDATE ON character_player_appearance_snapshots BEGIN SELECT RAISE(ABORT,'fixture'); END");
    f.unchanged([&]{r.save(1,4,1,a.fields,a.origin,a.provenance);});
    require(f.outer_count()==1,"Borrowed failure rolled back caller work");
    f.sql("DROP TRIGGER reject_appearance");
    f.sql("CREATE TRIGGER alter_appearance AFTER UPDATE ON character_player_appearance_snapshots BEGIN UPDATE character_player_appearance_snapshots SET provenance='changed' WHERE character_id=NEW.character_id; END");
    f.unchanged([&]{r.save(1,4,1,a.fields,a.origin,a.provenance);});
    require(f.outer_count()==1,"Readback failure rolled back caller work");
    f.sql("DROP TRIGGER alter_appearance");
    auto b=r.save(1,4,1,a.fields,a.origin,a.provenance);
    require(b.revision==2 && !sqlite3_get_autocommit(f.db.get()),"Borrowed transaction unusable after failures");
    f.sql("COMMIT");require(f.outer_count()==1 && r.load(1,4)==std::optional(b),"Caller commit lost after-state");
    // Standalone insertion errors must not leave an open transaction or a row.
    Fixture empty;empty.sql("CREATE TRIGGER reject_new BEFORE INSERT ON character_player_appearance_snapshots BEGIN SELECT RAISE(ABORT,'fixture'); END");
    empty.unchanged([&]{seed(empty);});
}
void reopen_and_readonly() {
    struct Temp {
        std::filesystem::path root;
        Temp() { std::random_device rd;for(int i=0;i<100;++i) {
            root=std::filesystem::temp_directory_path()/("god2-player-appearance-"+std::to_string(rd()));
            if(std::filesystem::create_directory(root))return;
        }throw std::runtime_error("Create appearance temporary directory"); }
        ~Temp() {std::error_code ec;std::filesystem::remove_all(root,ec);}
    } temp;
    const auto path=(temp.root/"fixture.sqlite").string();god2::StoredPlayerAppearance expected;
    { Fixture f(path);auto a=seed(f);auto updated=a.fields;updated.components[6]=0x32;updated.components[7]=0xe2;
      expected=f.repo().save(1,4,1,updated,a.origin,a.provenance); }
    { Fixture f(path,false);require(f.repo().load(1,4)==std::optional(expected),"Reopen lost DA/baseline");
      auto restored=expected.fields;restored.components[6]=expected.base_components[6];restored.components[7]=expected.base_components[7];
      auto saved=f.repo().save(1,4,2,restored,expected.origin,expected.provenance);
      require(saved.fields.components==fields().components && saved.base_components==fields().components,"Unequip baseline not durable");expected=saved; }
    { Fixture f(path,false,true);require(f.repo().load(1,4)==std::optional(expected),"Read-only load");
      f.unchanged([&]{f.repo().save(1,4,expected.revision,expected.fields,expected.origin,expected.provenance);}); }
}
}
int main() {
    try {preservation_and_cas();invalid_inputs_and_pending();corruption_and_readback();borrowed_transaction_atomicity();reopen_and_readonly();
        std::cout<<"PASS player appearance: exact DA/baseline, owner/CAS/pending, corruption/readback, borrowed atomicity, reopen/RO\n";return 0;
    } catch(const std::exception& error) {std::cerr<<error.what()<<'\n';return 1;}
}
