#include "db/NativeSupplyCatalog.h"
#include "db/SqliteSupport.h"
#include <nlohmann/json.hpp>
#include <chrono>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <memory>
#include <stdexcept>

namespace {
void require(bool value,const char* message){if(!value)throw std::runtime_error(message);}
template<class F>void rejects(F f){try{f();}catch(const god2::DatabaseError&){return;}throw std::runtime_error("Corrupt MED02 catalog accepted");}
struct Close{void operator()(sqlite3* db)const{sqlite3_close_v2(db);}};
using Db=std::unique_ptr<sqlite3,Close>;
Db open(const std::string& name,int flags=SQLITE_OPEN_READWRITE|SQLITE_OPEN_CREATE){sqlite3* raw=nullptr;const auto rc=sqlite3_open_v2(name.c_str(),&raw,flags,nullptr);Db db(raw);require(rc==SQLITE_OK,"Open test DB");return db;}
std::vector<std::uint8_t> unhex(const std::string& text){
    require(text.size()%2==0,"Odd native cache hex");std::vector<std::uint8_t> out;
    auto digit=[](char c){if(c>='0'&&c<='9')return c-'0';if(c>='a'&&c<='f')return c-'a'+10;throw std::runtime_error("Invalid native hex");};
    for(std::size_t i=0;i<text.size();i+=2)out.push_back(static_cast<std::uint8_t>(digit(text[i])*16+digit(text[i+1])));return out;
}
void schema(sqlite3* db){god2::sqlite_detail::execute(db,R"SQL(
CREATE TABLE native_data_sources(dataset_id TEXT PRIMARY KEY,source_path TEXT,source_sha256 TEXT,decoded_sha256 TEXT,
native_image_sha256 TEXT,source_section TEXT,loader_rva TEXT,lookup_rva TEXT,row_count INTEGER);
CREATE TABLE native_med02_recovery_declarations(dataset_id TEXT,source_record_index INTEGER,source_line INTEGER,
item_id INTEGER,record_sha256 TEXT,raw_record BLOB,tooltip_bytes BLOB,declared_hp INTEGER,declared_mp INTEGER,
normal_use INTEGER,hotkey_allowed INTEGER,PRIMARY KEY(dataset_id,source_record_index));
)SQL");}
void seed(sqlite3* db){
    std::ifstream file(std::filesystem::path(GOD2_SOURCE_DIR)/"artifacts/research/current-med02-source-gate-20260927/source.json");
    require(file.good(),"Missing current MED02 cache; run current_med02_source_gate_20260927");nlohmann::json data;file>>data;
    require(data.at("catalog_sha256")==god2::NativeSupplyCatalog::current_catalog_sha256,"Cache catalog pin mismatch");
    const auto& groups=data.at("groups");require(groups.size()==2&&groups[0].size()==1&&groups[1].size()==71,"Native cache count");
    for(std::size_t group=0;group<2;++group)for(const auto& row:groups[group]){
        require(row.size()==(group==0?9:11),"Cache row width");
        god2::sqlite_detail::Statement insert(db,group==0?"INSERT INTO native_data_sources VALUES(?,?,?,?,?,?,?,?,?)":
            "INSERT INTO native_med02_recovery_declarations VALUES(?,?,?,?,?,?,?,?,?,?,?)");
        for(int i=0;i<static_cast<int>(row.size());++i){
            if(group==1&&(i==5||i==6)){const auto raw=unhex(row[i].get<std::string>());insert.bind_blob(i+1,raw);}
            else if((group==0&&i==8)||(group==1&&((i>=1&&i<=3)||i>=7))){require(row[i].is_number_integer(),"Cache integer");insert.bind(i+1,row[i].get<std::int64_t>());}
            else insert.bind(i+1,row[i].get<std::string>());
        }insert.done();
    }
}
struct Temporary{
    std::filesystem::path path;
    Temporary(){const auto tick=std::chrono::steady_clock::now().time_since_epoch().count();path=std::filesystem::temp_directory_path()/("god2-med02-integrity-"+std::to_string(tick)+".db");require(!std::filesystem::exists(path),"Unexpected temporary file collision");}
    ~Temporary(){std::error_code ec;std::filesystem::remove(path,ec);}
};
}
int main(int argc,char** argv){try{
    if(argc==2) {
        auto db=open(argv[1],SQLITE_OPEN_READONLY);god2::NativeSupplyCatalog catalog(db.get());
        require(catalog.is_imported()&&catalog.lookup(3101)&&catalog.lookup(3107),"Complete pinned MED02 source required");
        std::cout<<"71\n";return 0;
    }
    require(argc==1,"Unexpected source reader arguments");
    rejects([]{god2::NativeSupplyCatalog catalog(nullptr);});
    auto missing=open(":memory:");rejects([&]{(void)god2::NativeSupplyCatalog(missing.get()).is_imported();});
    Temporary temporary;auto db=open(temporary.path.string());schema(db.get());god2::NativeSupplyCatalog catalog(db.get());
    require(!catalog.is_imported()&&!catalog.lookup(3101),"Absent source synthesized supply");rejects([&]{(void)catalog.lookup(0);});
    seed(db.get());require(catalog.is_imported(),"Actual pinned71 rejected");
    const auto hp=catalog.lookup(3101),mp=catalog.lookup(3107),both=catalog.lookup(3113);
    require(hp&&mp&&both&&hp->declared_hp==100&&hp->declared_mp==0&&mp->declared_hp==0&&mp->declared_mp==50&&both->declared_hp==500&&both->declared_mp==150,"Actual source amounts differ");
    unsigned selected=0;for(unsigned item=3101;item<=3200;++item)selected+=catalog.lookup(static_cast<std::uint16_t>(item)).has_value();
    require(selected==71&&!catalog.lookup(3120)&&!catalog.lookup(65535),"Native eligible boundary mismatch");
    unsigned cases=0;
    for(const char* sql:{
        "DELETE FROM native_med02_recovery_declarations WHERE item_id=3101",
        "DELETE FROM native_data_sources",
        "UPDATE native_med02_recovery_declarations SET dataset_id='wrong-dataset'",
        "DELETE FROM native_data_sources; UPDATE native_med02_recovery_declarations SET dataset_id='wrong-dataset'",
        "DELETE FROM native_med02_recovery_declarations",
        "UPDATE native_data_sources SET source_sha256=replace(source_sha256,'7','6')",
        "UPDATE native_data_sources SET row_count=99",
        "UPDATE native_med02_recovery_declarations SET raw_record=CAST(X'30'||substr(raw_record,2) AS BLOB) WHERE item_id=3101",
        "UPDATE native_med02_recovery_declarations SET raw_record=CAST(X'30'||substr(raw_record,2) AS BLOB),record_sha256=printf('%064d',0) WHERE item_id=3101",
        "UPDATE native_med02_recovery_declarations SET tooltip_bytes=X'313030' WHERE item_id=3101",
        "UPDATE native_med02_recovery_declarations SET tooltip_bytes=CAST(tooltip_bytes AS TEXT) WHERE item_id=3101",
        "UPDATE native_med02_recovery_declarations SET raw_record=CAST(raw_record AS TEXT) WHERE item_id=3101",
        "UPDATE native_med02_recovery_declarations SET declared_hp=101 WHERE item_id=3101",
        "UPDATE native_med02_recovery_declarations SET declared_mp=1 WHERE item_id=3101",
        "UPDATE native_med02_recovery_declarations SET declared_hp=4294967396 WHERE item_id=3101",
        "UPDATE native_med02_recovery_declarations SET declared_hp=-4294967196 WHERE item_id=3101",
        "UPDATE native_med02_recovery_declarations SET declared_hp=-1 WHERE item_id=3101",
        "UPDATE native_med02_recovery_declarations SET declared_hp=100.5 WHERE item_id=3101",
        "UPDATE native_med02_recovery_declarations SET declared_hp=NULL WHERE item_id=3101",
        "UPDATE native_med02_recovery_declarations SET declared_hp=4001 WHERE item_id=3101",
        "UPDATE native_med02_recovery_declarations SET item_id=68637 WHERE item_id=3101",
        "UPDATE native_med02_recovery_declarations SET source_line=source_line+1 WHERE item_id=3101",
        "UPDATE native_med02_recovery_declarations SET source_record_index=100 WHERE item_id=3101",
        "UPDATE native_med02_recovery_declarations SET normal_use=0 WHERE item_id=3101",
        "UPDATE native_med02_recovery_declarations SET hotkey_allowed=0 WHERE item_id=3101",
        "UPDATE native_med02_recovery_declarations SET record_sha256=upper(record_sha256) WHERE item_id=3101"}){
        god2::sqlite_detail::execute(db.get(),"BEGIN");god2::sqlite_detail::execute(db.get(),sql);
        const auto changes=sqlite3_total_changes(db.get());
        rejects([&]{(void)catalog.is_imported();});rejects([&]{(void)catalog.lookup(3107);});rejects([&]{(void)catalog.lookup(65535);});
        require(sqlite3_get_autocommit(db.get())==0&&sqlite3_total_changes(db.get())==changes,"Reader mutated/ended caller transaction");
        god2::sqlite_detail::execute(db.get(),"ROLLBACK");require(catalog.is_imported(),"Rollback source not restored");++cases;
    }
    auto ro=open(temporary.path.string(),SQLITE_OPEN_READONLY);god2::NativeSupplyCatalog readonly(ro.get());
    require(readonly.is_imported()&&readonly.lookup(3107)==mp&&sqlite3_total_changes(ro.get())==0&&sqlite3_get_autocommit(ro.get())!=0,"Read-only catalog/transaction leak");
    god2::sqlite_detail::execute(db.get(),"DELETE FROM native_med02_recovery_declarations; DELETE FROM native_data_sources");
    require(!readonly.is_imported()&&!readonly.lookup(3101),"Read-only reader cached stale qualified supply");
    std::cout<<"PASS MED02 actual71/100, "<<cases<<" corruption cases, orphan/absent/unknown/read-only/reload/transaction preservation\n";
    return 0;
}catch(const std::exception& error){std::cerr<<error.what()<<'\n';return 1;}}
