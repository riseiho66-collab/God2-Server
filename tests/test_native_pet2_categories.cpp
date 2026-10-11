#include "db/NativePet2CategoryCatalog.h"
#include "db/SqliteMigrationManager.h"
#include "db/SqliteSupport.h"
#include <iostream>
#include <memory>
#include <string>
namespace {
void require(bool v,const char* m){if(!v)throw std::runtime_error(m);}
template<class F>void rejects(F f){try{f();}catch(const god2::DatabaseError&){return;}throw std::runtime_error("Corrupt catalog accepted");}
struct Close{void operator()(sqlite3* p)const{sqlite3_close_v2(p);}};
}
int main(int argc,char** argv){
 try{
    if(argc!=3)return 2;
    const std::string mode=argv[1];
    sqlite3* raw=nullptr;require(sqlite3_open_v2(argv[2],&raw,
        mode=="--read-only"?SQLITE_OPEN_READONLY:SQLITE_OPEN_READWRITE|SQLITE_OPEN_CREATE,nullptr)==SQLITE_OK,"Open database");
    std::unique_ptr<sqlite3,Close> db(raw);god2::sqlite_detail::execute(raw,"PRAGMA foreign_keys=ON");
    if(mode!="--read-only")god2::SqliteMigrationManager(raw,god2::default_sqlite_migrations()).migrate();
    god2::NativePet2CategoryCatalog catalog(raw);
    if(mode=="--read-only"){
        require(catalog.count()==464,"Native formal category denominator");
        require(catalog.lookup({1,2}).has_value()&&catalog.lookup({29,15}).has_value(),"Formal native boundary lookup");
        std::cout<<"Native pet2 formal catalog: 464 complete pinned rows, read-only C++ PASS\n";return 0;
    }
    if(std::string(argv[1])=="--initialize"){
        require(catalog.count()==0,"Fresh migration fabricated category values");return 0;
    }
    if(std::string(argv[1])!="--test")return 2;
    require(catalog.count()==464,"Native category denominator");
    for(unsigned group=0;group<256;++group){
        god2::RecoveredPet2Stats::LogicalRecord packet{};packet[0]=0xfb;packet[1]=0x61;packet[2]=0x6d;packet[3]=42;
        packet[61]=static_cast<std::uint8_t>(group);
        for(unsigned index=0;index<16;++index){
            packet[45]=static_cast<std::uint8_t>(0xf0|index);
            auto parsed=god2::RecoveredPet2Stats::parse_logical(packet);
            require(parsed.has_value(),"Category selector changed structural packet acceptance");
            const auto selector=parsed->category_selector();
            require(selector.group==group&&selector.index==index,"FB bit selector mismatch");
            const auto row=catalog.lookup(selector);
            require(bool(row)==(group>=1&&group<=29),"Native category bounds mismatch");
            if(row)require(row->group==group&&row->index==index&&!row->name.empty(),"Wrong source category selected");
            require(god2::RecoveredPet2Stats::encode_logical(*parsed)==packet,"Category lookup altered instance");
        }
    }
    require(!catalog.lookup({1,16}),"Out of range direct selector accepted");
    const auto corrupt=[&](const char* sql){
        god2::sqlite_detail::execute(raw,"BEGIN");god2::sqlite_detail::execute(raw,sql);
        rejects([&]{catalog.count();});god2::sqlite_detail::execute(raw,"ROLLBACK");
        require(catalog.count()==464,"Corruption rollback failed");
    };
    corrupt("DELETE FROM native_pet2_category_rows WHERE group_id=1 AND category_index=0");
    corrupt("UPDATE native_pet2_category_rows SET name_encoded=X'41' WHERE group_id=1 AND category_index=0");
    corrupt("UPDATE native_pet2_category_rows SET source_line=source_line+1 WHERE group_id=1 AND category_index=0");
    corrupt("UPDATE native_pet2_category_source SET decoded_sha256='wrong'");
    corrupt("DELETE FROM native_pet2_category_source");
    std::cout<<"Native pet2 categories: 464 rows, 4096 selectors, immutable packet and corruption checks PASS\n";
    return 0;
 }catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}
}
