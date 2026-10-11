#include "db/NativeMapItemCatalog.h"
#include "db/SqliteSupport.h"
#include <iostream>
#include <memory>

using namespace god2;
namespace {
unsigned checks{};
void require(bool value) {++checks;if(!value)throw std::runtime_error("Map item catalog check failed");}
template<class F> void rejects(F action) {
    bool rejected=false;try{action();}catch(const DatabaseError&){rejected=true;}require(rejected);
}
using Db=std::unique_ptr<sqlite3,decltype(&sqlite3_close)>;
Db open(const char* path,int flags) {
    sqlite3* raw=nullptr;const auto status=sqlite3_open_v2(path,&raw,flags,nullptr);Db db(raw,sqlite3_close);
    require(status==SQLITE_OK);return db;
}
Db clone(sqlite3* source) {
    auto copy=open(":memory:",SQLITE_OPEN_READWRITE|SQLITE_OPEN_CREATE);
    auto* backup=sqlite3_backup_init(copy.get(),"main",source,"main");require(backup!=nullptr);
    const auto status=sqlite3_backup_step(backup,-1);const auto done=sqlite3_backup_finish(backup);
    require(status==SQLITE_DONE && done==SQLITE_OK);return copy;
}
}
// Explicit disposable imported DB only; opens it READONLY and mutates memory
// clones for negative tests. No shared fixtures or live files are written.
int main(int argc,char** argv) {
    try {
        if(argc!=2)throw std::runtime_error("Usage: native-map-item-catalog imported-test.sqlite");
        auto db=open(argv[1],SQLITE_OPEN_READONLY);NativeMapItemCatalog catalog(db.get());
        rejects([]{NativeMapItemCatalog invalid(nullptr);});
        require(catalog.is_imported());const auto town=catalog.lookup(5569),kunlun=catalog.lookup(5576);
        require(catalog.populated() && catalog.contains(5569) && catalog.contains(5576) && !catalog.contains(5575));
        require(town && kunlun && town->category_code==3 && kunlun->category_code==0);
        require(town->source_line==8236 && kunlun->source_line==8243 && kunlun->icon_id==55076);
        require(town->source_flags==kunlun->source_flags && kunlun->effect_code==8428);
        require(!catalog.lookup(0) && !catalog.lookup(5575) && !catalog.lookup(65535));
        require(sqlite3_total_changes(db.get())==0);
        sqlite_detail::execute(db.get(),"BEGIN");require(catalog.lookup(5576)==kunlun);sqlite_detail::execute(db.get(),"COMMIT");
        {auto empty=clone(db.get());sqlite_detail::execute(empty.get(),"DELETE FROM native_map_item_rows; DELETE FROM native_map_item_sources");
            NativeMapItemCatalog absent(empty.get());require(!absent.is_imported() && !absent.lookup(5576));}
        // Every persisted column is pinned. Altering the OTHER item must also
        // reject a lookup of5576; whole-catalog qualification is mandatory.
        for(const auto* mutation:{
            "DELETE FROM native_map_item_sources", "DELETE FROM native_map_item_rows WHERE item_id=5569",
            "UPDATE native_map_item_sources SET source_file='other'",
            "UPDATE native_map_item_sources SET source_sha256=printf('%064d',0)",
            "UPDATE native_map_item_sources SET decoded_sha256=printf('%064d',0)",
            "UPDATE native_map_item_sources SET source_section='other'",
            "UPDATE native_map_item_sources SET section_row_count=738",
            "UPDATE native_map_item_sources SET row_desc_line=4",
            "UPDATE native_map_item_sources SET row_desc_sha256=printf('%064d',0)",
            "UPDATE native_map_item_sources SET row_desc_raw=X'41'",
            "UPDATE native_map_item_sources SET encoding='UTF8'",
            "UPDATE native_map_item_sources SET authority='NATIVE_VERIFIED'",
            "UPDATE native_map_item_rows SET item_id=5568 WHERE item_id=5569",
            "UPDATE native_map_item_rows SET source_file='other' WHERE item_id=5569",
            "UPDATE native_map_item_rows SET source_line=1 WHERE item_id=5569",
            "UPDATE native_map_item_rows SET decoded_offset=1 WHERE item_id=5569",
            "UPDATE native_map_item_rows SET record_sha256=printf('%064d',0) WHERE item_id=5569",
            "UPDATE native_map_item_rows SET raw_record=X'41' WHERE item_id=5569",
            "UPDATE native_map_item_rows SET category_code=0 WHERE item_id=5569",
            "UPDATE native_map_item_rows SET resource_name=X'41' WHERE item_id=5569",
            "UPDATE native_map_item_rows SET icon_id=55000 WHERE item_id=5569",
            "UPDATE native_map_item_rows SET name_bytes=X'41' WHERE item_id=5569",
            "UPDATE native_map_item_rows SET description_bytes=X'41' WHERE item_id=5569",
            "UPDATE native_map_item_rows SET effect_code=0 WHERE item_id=5569",
            "UPDATE native_map_item_rows SET source_flags=zeroblob(12) WHERE item_id=5569",
            "UPDATE native_map_item_rows SET authority='NATIVE_VERIFIED' WHERE item_id=5569",
            "UPDATE native_map_item_rows SET category_code=3.5 WHERE item_id=5569",
            "UPDATE native_map_item_rows SET name_bytes='not blob' WHERE item_id=5569"
        }) {
            auto copy=clone(db.get());sqlite_detail::execute(copy.get(),"PRAGMA ignore_check_constraints=ON");
            sqlite_detail::execute(copy.get(),mutation);NativeMapItemCatalog bad(copy.get());
            const auto changes=sqlite3_total_changes(copy.get());
            rejects([&]{bad.is_imported();});rejects([&]{bad.lookup(5576);});
            rejects([&]{bad.populated();});rejects([&]{bad.contains(5576);});rejects([&]{bad.contains(5575);});
            require(sqlite3_total_changes(copy.get())==changes);
        }
        require(catalog.lookup(5576)==kunlun && sqlite3_total_changes(db.get())==0);
        std::cout<<"Map item source reader checks passed: "<<checks<<'\n';return 0;
    }catch(const std::exception& error){std::cerr<<error.what()<<'\n';return 1;}
}
