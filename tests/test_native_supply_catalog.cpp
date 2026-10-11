#include "db/NativeSupplyCatalog.h"
#include "db/SqliteMigrationManager.h"
#include "db/SqliteSupport.h"
#include "handlers/DiagnosticSupplyService.h"

#include <iostream>
#include <memory>
#include <stdexcept>

namespace {
void require(bool value,const char* message) {
    if(!value) throw std::runtime_error(message);
}
struct Close { void operator()(sqlite3* db) const { sqlite3_close_v2(db); } };
}

int main(int argc,char** argv) {
    try {
        require(argc==1 || argc==2,"Usage: native-supply-catalog [imported-database]");
        sqlite3* raw=nullptr;
        const int result=argc==2 ? sqlite3_open_v2(argv[1],&raw,SQLITE_OPEN_READONLY,nullptr)
                                : sqlite3_open(":memory:",&raw);
        require(result==SQLITE_OK,"Unable to open MED02 database");
        std::unique_ptr<sqlite3,Close> db(raw);
        if(argc==1) {
            god2::sqlite_detail::execute(db.get(),"PRAGMA foreign_keys=ON");
            god2::SqliteMigrationManager(db.get(),god2::default_sqlite_migrations()).migrate();
            god2::SqliteMigrationManager(db.get(),god2::default_sqlite_migrations()).migrate();
            god2::NativeSupplyCatalog catalog(db.get());
            require(!catalog.is_imported() && !catalog.lookup(3101),
                    "Empty migration invented native recovery amounts");
            try { (void)catalog.lookup(0); }
            catch(const god2::DatabaseError&) { std::cout<<"Native MED02 empty migration passed\n"; return 0; }
            throw std::runtime_error("Invalid MED02 item zero accepted");
        }
        god2::NativeSupplyCatalog catalog(db.get());
        require(catalog.is_imported(),"MED02 source was not imported");
        const auto hp=catalog.lookup(3101);
        const auto mp=catalog.lookup(3107);
        const auto both=catalog.lookup(3113);
        require(hp && mp && both && hp->declared_hp==100 && hp->declared_mp==0 &&
                hp->source_line==6354 && mp->declared_hp==0 && mp->declared_mp==50 &&
                mp->source_line==6360 && both->declared_hp==500 && both->declared_mp==150 &&
                both->source_line==6366 && !catalog.lookup(3120),
                "Imported MED02 declaration lookup mismatch");
        const auto policy=god2::DiagnosticSupplyService::native_declared_policy(catalog,3113,0x1234);
        require(policy && policy->restore_hp==500 && policy->restore_mp==150 &&
                policy->source_sha256==god2::NativeSupplyCatalog::current_source_sha256 &&
                !god2::DiagnosticSupplyService::native_declared_policy(catalog,3113,0),
                "Native declaration was not connected to isolated C2S26 policy");
        std::cout<<"Imported MED02 C++ catalog and supply policy passed\n";
    } catch(const std::exception& error) { std::cerr<<error.what()<<'\n'; return 1; }
}
