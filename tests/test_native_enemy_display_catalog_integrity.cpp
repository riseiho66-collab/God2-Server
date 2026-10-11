#include "db/NativeEnemyDisplayCatalog.h"
#include "db/SqliteSupport.h"
#include <iostream>
#include <memory>
#include <stdexcept>
#include <string>

int main(int argc,char** argv) {
    try {
        if(argc!=3)throw std::runtime_error("Usage: enemy-integrity full|empty|reject database");
        sqlite3* raw=nullptr;
        if(sqlite3_open_v2(argv[2],&raw,SQLITE_OPEN_READONLY,nullptr)!=SQLITE_OK) {
            if(raw)sqlite3_close_v2(raw);
            throw std::runtime_error("Cannot open isolated fixture");
        }
        const std::unique_ptr<sqlite3,decltype(&sqlite3_close_v2)> db(raw,sqlite3_close_v2);
        const god2::NativeEnemyDisplayCatalog catalog(db.get());
        const std::string mode=argv[1];
        if(mode=="reject") {
            bool rejected=false;
            try{(void)catalog.counts();}catch(const god2::DatabaseError&){rejected=true;}
            if(!rejected)throw std::runtime_error("Malformed complete-source fixture accepted");
        } else {
            const auto wanted=mode=="full"?god2::NativeEnemyDisplayCatalog::Counts{7815,7791,96}:
                god2::NativeEnemyDisplayCatalog::Counts{};
            if(mode!="full"&&mode!="empty")throw std::runtime_error("Unknown test mode");
            if(catalog.counts()!=wanted)throw std::runtime_error("Count mismatch");
            // counts owns a read transaction only when the caller does not.
            god2::sqlite_detail::execute(db.get(),"BEGIN");
            if(catalog.counts()!=wanted||sqlite3_get_autocommit(db.get())!=0)
                throw std::runtime_error("Caller transaction not preserved");
            god2::sqlite_detail::execute(db.get(),"ROLLBACK");
        }
        if(sqlite3_get_autocommit(db.get())==0)throw std::runtime_error("Leaked read transaction");
        std::cout<<"PASS "<<mode<<'\n';return 0;
    }catch(const std::exception& error){std::cerr<<error.what()<<'\n';return 1;}
}
