#include "db/NativeNpcDisplayCatalog.h"
#include "db/SqliteSupport.h"
#include <iostream>
#include <stdexcept>
#include <string>
using namespace god2;
int main(int argc,char** argv){
    sqlite3* db=nullptr;
    try {
        if(argc!=2)throw std::runtime_error("Expected disposable imported fixture path");
        if(sqlite3_open_v2(argv[1],&db,SQLITE_OPEN_READWRITE,nullptr)!=SQLITE_OK)throw std::runtime_error("Open fixture failed");
        // Requires an explicitly marked isolated test DB, never a formal source catalog.
        sqlite_detail::Statement marker(db,"SELECT value FROM npc_test_fixture_marker");
        if(!marker.row() || marker.text(0)!="DISPOSABLE-NPC-CATALOG")throw std::runtime_error("Missing fixture marker");
        NativeNpcDisplayCatalog catalog(db);
        const auto check=[](bool ok){if(!ok)throw std::runtime_error("NPC C++ check failed");};
        check(catalog.count()==4043);check(!catalog.lookup(0));check(!catalog.lookup(65535));
        for(const auto key:{1,523,1156,2936,3472,6224}){
            const auto r=catalog.lookup(static_cast<std::uint16_t>(key));check(r.has_value() && r->key==key && r->prefix28.size()==28);
        }
        const auto failure=[&](const char* sql){
            sqlite_detail::execute(db,"BEGIN");sqlite_detail::execute(db,sql);bool failed=false;
            try{(void)catalog.lookup(2936);}catch(const DatabaseError&){failed=true;}
            sqlite_detail::execute(db,"ROLLBACK");check(failed);check(catalog.count()==4043);
        };
        failure("UPDATE native_npc_display_rows SET prefix28=zeroblob(28) WHERE npc_key=1");
        failure("UPDATE native_npc_display_rows SET source_line=999 WHERE npc_key=1");
        failure("UPDATE native_npc_display_rows SET raw_record=x'00' WHERE npc_key=1");
        failure("DELETE FROM native_npc_display_rows WHERE npc_key=6224");
        failure("UPDATE native_npc_display_sources SET authority='INVALID'");
        failure("DELETE FROM native_npc_display_sources");
        sqlite_detail::execute(db,"BEGIN");sqlite_detail::execute(db,"DELETE FROM native_npc_display_rows; DELETE FROM native_npc_display_sources");
        check(catalog.count()==0);check(!catalog.lookup(2936));check(sqlite3_get_autocommit(db)==0);sqlite_detail::execute(db,"ROLLBACK");
        std::cout<<"NPC source full 4043 + lookup + 6 corruption/rollback + empty borrowed transaction PASS\n";
        sqlite3_close_v2(db);return 0;
    }catch(const std::exception& error){std::cerr<<error.what()<<'\n';if(db)sqlite3_close_v2(db);return 1;}
}
