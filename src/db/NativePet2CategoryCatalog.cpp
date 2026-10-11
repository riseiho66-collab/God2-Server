#include "db/NativePet2CategoryCatalog.h"
#include "db/SqliteSupport.h"
#include <array>
#ifdef _WIN32
#include <windows.h>
#include <bcrypt.h>
#endif
namespace god2 {
namespace {
std::string sha(std::span<const std::uint8_t> bytes) {
#ifdef _WIN32
    struct Handles {
        BCRYPT_ALG_HANDLE algorithm=nullptr;BCRYPT_HASH_HANDLE hash=nullptr;
        ~Handles(){if(hash)BCryptDestroyHash(hash);if(algorithm)BCryptCloseAlgorithmProvider(algorithm,0);}
    } h;
    std::array<std::uint8_t,32> out{};
    if(!BCRYPT_SUCCESS(BCryptOpenAlgorithmProvider(&h.algorithm,BCRYPT_SHA256_ALGORITHM,nullptr,0)) ||
       !BCRYPT_SUCCESS(BCryptCreateHash(h.algorithm,&h.hash,nullptr,0,nullptr,0,0)) ||
       !BCRYPT_SUCCESS(BCryptHashData(h.hash,const_cast<PUCHAR>(bytes.data()),static_cast<ULONG>(bytes.size()),0)) ||
       !BCRYPT_SUCCESS(BCryptFinishHash(h.hash,out.data(),static_cast<ULONG>(out.size()),0)))
        throw DatabaseError("Pet category SHA256 unavailable");
    std::string text;for(auto b:out){text+="0123456789abcdef"[b>>4];text+="0123456789abcdef"[b&15];}return text;
#else
    (void)bytes;throw DatabaseError("Pet category SHA256 backend unavailable");
#endif
}
struct ReadScope {
    sqlite3* db;bool owned,done=false;
    explicit ReadScope(sqlite3* p):db(p),owned(sqlite3_get_autocommit(p)!=0){if(owned)sqlite_detail::execute(db,"BEGIN");}
    ~ReadScope(){if(owned&&!done)sqlite3_exec(db,"ROLLBACK",nullptr,nullptr,nullptr);}
    void finish(){if(owned)sqlite_detail::execute(db,"COMMIT");done=true;}
};
}
const char* NativePet2CategoryCatalog::schema() noexcept {return R"SQL(
CREATE TABLE native_pet2_category_source (
 id INTEGER PRIMARY KEY CHECK(id=1),source_sha256 TEXT NOT NULL,
 decoded_sha256 TEXT NOT NULL,image_sha256 TEXT NOT NULL,client_sha256 TEXT NOT NULL,
 dataset_sha256 TEXT NOT NULL,authority TEXT NOT NULL);
CREATE TABLE native_pet2_category_rows (
 group_id INTEGER NOT NULL CHECK(typeof(group_id)='integer' AND group_id BETWEEN 1 AND 29),
 category_index INTEGER NOT NULL CHECK(typeof(category_index)='integer' AND category_index BETWEEN 0 AND 15),
 source_line INTEGER NOT NULL CHECK(typeof(source_line)='integer' AND source_line>0),
 raw_record BLOB NOT NULL CHECK(typeof(raw_record)='blob' AND length(raw_record) BETWEEN 1 AND 1024),
 name_encoded BLOB NOT NULL CHECK(typeof(name_encoded)='blob' AND length(name_encoded) BETWEEN 1 AND 15),
 PRIMARY KEY(group_id,category_index));
)SQL";}
std::vector<NativePet2Category> NativePet2CategoryCatalog::read_all() const {
    if(!db_)throw DatabaseError("Null pet category database");
    ReadScope scope(db_);
    sqlite_detail::Statement source(db_,"SELECT id,source_sha256,decoded_sha256,image_sha256,client_sha256,dataset_sha256,authority FROM native_pet2_category_source");
    const bool present=source.row();
    if(present && (source.integer(0)!=1 || source.text(1)!="80c2b7d366d2ef0264df78f20de1b20fa21e14f6592f56676b090f83ddc064c6" ||
       source.text(2)!="f8d1a1c22e8fc9195dd625ffc244e2ebbcee07492116976feece0bd9d26b813b" ||
       source.text(3)!="149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763" ||
       source.text(4)!="6bf75ef8ac1e0f6b2240800ff841d205788bd1b6512149584b5386b10f431e98" ||
       source.text(5)!=dataset_sha256 || source.text(6)!="NATIVE_PARSED_DISPLAY_ONLY"))
        throw DatabaseError("Pet category source identity differs");
    if(present && source.row())throw DatabaseError("Multiple pet category sources");
    sqlite_detail::Statement rows(db_,"SELECT group_id,category_index,source_line,raw_record,name_encoded FROM native_pet2_category_rows ORDER BY group_id,category_index");
    std::vector<NativePet2Category> records;std::vector<std::uint8_t> canonical;
    const auto number=[&](std::uint32_t n,unsigned width){for(unsigned i=0;i<width;++i)canonical.push_back(static_cast<std::uint8_t>(n>>(8*i)));};
    while(rows.row()) {
        if(!present || records.size()>=464)throw DatabaseError("Orphan/excess pet category rows");
        NativePet2Category r{rows.number<std::uint8_t>(0),rows.number<std::uint8_t>(1),rows.number<std::uint32_t>(2),{}};
        if(r.group!=records.size()/16+1 || r.index!=records.size()%16 || !r.source_line)
            throw DatabaseError("Incomplete pet category key sequence");
        const auto raw=rows.blob(3,1,1024),label=rows.blob(4,1,15);
        number(r.group,1);number(r.index,1);number(r.source_line,4);number(static_cast<std::uint32_t>(raw.size()),4);
        canonical.insert(canonical.end(),raw.begin(),raw.end());number(static_cast<std::uint32_t>(label.size()),1);
        canonical.insert(canonical.end(),label.begin(),label.end());r.name.assign(label.begin(),label.end());records.push_back(std::move(r));
    }
    if(present && (records.size()!=464 || sha(canonical)!=dataset_sha256))throw DatabaseError("Pet category dataset differs");
    scope.finish();return records;
}
std::size_t NativePet2CategoryCatalog::count() const {return read_all().size();}
std::optional<NativePet2Category> NativePet2CategoryCatalog::lookup(RecoveredPet2Stats::CategorySelector selector) const {
    if(!selector.display_valid() || selector.index>15)return std::nullopt;
    const auto rows=read_all();
    if(rows.empty())return std::nullopt;
    return rows[(selector.group-1)*16+selector.index];
}
}
