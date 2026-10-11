#include "db/SqliteTeleportGemRepository.h"
#include "db/SqliteSupport.h"
#include <filesystem>
#include <iostream>

// Test-only importer: never creates a scalar or resets an existing overlay.
int main(int argc,char** argv){
    sqlite3* db=nullptr;
    try{
        if(argc!=2)throw std::runtime_error("Expected isolated fixture database path");
        const auto path=std::filesystem::absolute(argv[1]).generic_string();
        if(path.find("/artifacts/playtests/private-teleport-gem-")==std::string::npos ||
           !std::filesystem::exists(path))throw std::runtime_error("Refusing non-fixture database");
        if(sqlite3_open_v2(path.c_str(),&db,SQLITE_OPEN_READWRITE,nullptr)!=SQLITE_OK)
            throw std::runtime_error("Cannot open existing test database");
        god2::sqlite_detail::execute(db,"PRAGMA foreign_keys=ON");
        std::uint64_t account{},revision{};
        {
            god2::sqlite_detail::Statement query(db,"SELECT c.account_id,s.revision FROM recovered_characters c JOIN diagnostic_inventory_slots s ON s.character_id=c.id WHERE c.id=4 AND s.slot=12 AND s.item_id=16055 AND s.count=1");
            if(!query.row())throw std::runtime_error("Expected owned test scalar missing");
            account=query.number<std::uint64_t>(0);revision=query.number<std::uint64_t>(1);
        }
        god2::RecoveredTeleportGem::Metadata metadata{};
        metadata[0]=0xb7;metadata[1]=0x3e;metadata[2]=8;metadata[3]=4;
        god2::SqliteTeleportGemRepository repository(db);
        const auto row=repository.save_existing(account,4,12,
            {16055,1,revision,god2::SqliteTeleportGemRepository::source_sha256},metadata,
            "CUSTOM_TEST_NOT_NATIVE","private-teleport-gem-20260930-two-charge-explicit-test-operand;current_teleport_gem_20260930 full20 native projection");
        if(row.metadata20!=metadata || repository.load(account,4,12)!=std::optional(row))
            throw std::runtime_error("Fixture full instance mismatch");
        std::cout<<"ATTACHED_EXISTING slot=12 charges=2 revision="<<revision<<'\n';
        sqlite3_close(db);return 0;
    }catch(const std::exception& e){std::cerr<<e.what()<<'\n';if(db)sqlite3_close(db);return 1;}
}
