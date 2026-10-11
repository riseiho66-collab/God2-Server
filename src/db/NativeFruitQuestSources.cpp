#include "db/NativeFruitQuestSources.h"
#include "db/SqliteSupport.h"
#include <array>
#include <string>
#ifdef _WIN32
#include <windows.h>
#include <bcrypt.h>
#endif
namespace god2 {
namespace {
struct ReadScope {
    sqlite3* db;bool owns,finished=false;
    explicit ReadScope(sqlite3* value):db(value),owns(sqlite3_get_autocommit(value)!=0){if(owns)sqlite_detail::execute(db,"BEGIN");}
    ~ReadScope(){if(owns&&!finished)sqlite3_exec(db,"ROLLBACK",nullptr,nullptr,nullptr);}
    void finish(){if(owns)sqlite_detail::execute(db,"COMMIT");finished=true;}
};
std::string digest(std::span<const std::uint8_t> payload) {
#ifdef _WIN32
    struct Handles {
        BCRYPT_ALG_HANDLE algorithm=nullptr;BCRYPT_HASH_HANDLE hash=nullptr;
        ~Handles(){if(hash)BCryptDestroyHash(hash);if(algorithm)BCryptCloseAlgorithmProvider(algorithm,0);}
    } handles;
    std::array<std::uint8_t,32> out{};
    if(!BCRYPT_SUCCESS(BCryptOpenAlgorithmProvider(&handles.algorithm,BCRYPT_SHA256_ALGORITHM,nullptr,0)) ||
       !BCRYPT_SUCCESS(BCryptCreateHash(handles.algorithm,&handles.hash,nullptr,0,nullptr,0,0)) ||
       !BCRYPT_SUCCESS(BCryptHashData(handles.hash,const_cast<PUCHAR>(payload.data()),static_cast<ULONG>(payload.size()),0)) ||
       !BCRYPT_SUCCESS(BCryptFinishHash(handles.hash,out.data(),static_cast<ULONG>(out.size()),0)))
        throw DatabaseError("Fruit source SHA256 unavailable");
    std::string text;for(auto byte:out){text+="0123456789abcdef"[byte>>4];text+="0123456789abcdef"[byte&15];}return text;
#else
    (void)payload;throw DatabaseError("Fruit source SHA256 backend unavailable");
#endif
}
}
NativeFruitQuestSources::NativeFruitQuestSources(sqlite3* db):db_(db){if(!db_)throw DatabaseError("Null fruit source connection");}
const char* NativeFruitQuestSources::schema() noexcept {return R"SQL(
CREATE TABLE qualified_fruit_quest_sources (
 id INTEGER PRIMARY KEY CHECK(id=1),
 payload BLOB NOT NULL CHECK(typeof(payload)='blob' AND length(payload)=30421),
 payload_sha256 TEXT NOT NULL CHECK(payload_sha256='ab3e063564d0e7b351c3abab9e3475419c3a710ec9371b3de4d9b01f44a76541'),
 client_sha256 TEXT NOT NULL CHECK(client_sha256='6bf75ef8ac1e0f6b2240800ff841d205788bd1b6512149584b5386b10f431e98'),
 authority TEXT NOT NULL CHECK(authority='PINNED_SOURCE_AND_INFERENCE_BUNDLE'),
 design_id TEXT NOT NULL CHECK(design_id='CUSTOM-0051')
);
)SQL";}
bool NativeFruitQuestSources::populated() const {
    ReadScope read(db_);sqlite_detail::Statement row(db_,"SELECT id,payload,payload_sha256,client_sha256,authority,design_id FROM qualified_fruit_quest_sources ORDER BY id");
    if(!row.row()){read.finish();return false;}
    const auto payload=row.blob(1,30421,30421);
    if(row.integer(0)!=1 || row.text(2)!=bundle_sha256 || row.text(3)!=client_sha256 ||
       row.text(4)!="PINNED_SOURCE_AND_INFERENCE_BUNDLE" || row.text(5)!="CUSTOM-0051" || digest(payload)!=bundle_sha256)
        throw DatabaseError("Fruit source bundle identity mismatch");
    if(row.row())throw DatabaseError("Multiple fruit source bundles");read.finish();return true;
}
void NativeFruitQuestSources::require_qualified() const {if(!populated())throw DatabaseError("Fruit quest source bundle absent");}
}
