#include "db/NativeNpcDisplayCatalog.h"
#include "db/SqliteSupport.h"
#include <array>
#include <algorithm>
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
        throw DatabaseError("NPC display SHA256 unavailable");
    std::string text;for(auto byte:out){text+="0123456789abcdef"[byte>>4];text+="0123456789abcdef"[byte&15];}return text;
#else
    (void)payload;throw DatabaseError("NPC display SHA256 backend unavailable");
#endif
}
}
NativeNpcDisplayCatalog::NativeNpcDisplayCatalog(sqlite3* db):db_(db){if(!db_)throw DatabaseError("Null NPC display connection");}
const char* NativeNpcDisplayCatalog::schema() noexcept {return R"SQL(
CREATE TABLE native_npc_display_sources (
 id INTEGER PRIMARY KEY CHECK(id=1), source_file TEXT NOT NULL,
 source_sha256 TEXT NOT NULL, decoded_sha256 TEXT NOT NULL, client_sha256 TEXT NOT NULL,
 memory_receipt_sha256 TEXT NOT NULL, dataset_sha256 TEXT NOT NULL,
 row_count INTEGER NOT NULL CHECK(row_count=4043), section TEXT NOT NULL,
 loader_rva TEXT NOT NULL, authority TEXT NOT NULL);
CREATE TABLE native_npc_display_rows (
 npc_key INTEGER PRIMARY KEY CHECK(npc_key BETWEEN 1 AND 6999),
 source_line INTEGER NOT NULL CHECK(source_line>0), decoded_offset INTEGER NOT NULL CHECK(decoded_offset>=0),
 record_sha256 TEXT NOT NULL, raw_record BLOB NOT NULL CHECK(typeof(raw_record)='blob'),
 prefix28 BLOB NOT NULL CHECK(typeof(prefix28)='blob' AND length(prefix28)=28));
)SQL";}
std::vector<NativeNpcDisplayRecord> NativeNpcDisplayCatalog::read_all() const {
    ReadScope scope(db_);
    sqlite_detail::Statement source(db_,"SELECT id,source_file,source_sha256,decoded_sha256,client_sha256,memory_receipt_sha256,dataset_sha256,row_count,section,loader_rva,authority FROM native_npc_display_sources ORDER BY id");
    const bool present=source.row();
    if(present && (source.integer(0)!=1 || source.integer(7)!=4043 || source.text(1)!="Data2/Patch/Comm/gamedata.csvZ" || source.text(2)!="70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731" || source.text(3)!="75c3c37947a64b0917fbf8e546884d9bf893fe6a606d3e2b8f3b1857966b1815" || source.text(4)!="6bf75ef8ac1e0f6b2240800ff841d205788bd1b6512149584b5386b10f431e98" || source.text(5)!="1f3de6e0f62c340b20447c3b868907103b01caa64074688ebf47e9b5c725930a" || source.text(6)!="b770c11e516b488adba54ab7b2bee5d1fee3eaf1c5deb3dafe2e22962ccd343c" || source.text(8)!="NPCAppearData" || source.text(9)!="0x570f0" || source.text(10)!="SOURCE_DISPLAY_ONLY"))throw DatabaseError("NPC display source identity mismatch");
    if(present && source.row())throw DatabaseError("Multiple NPC display sources");
    sqlite_detail::Statement rows(db_,"SELECT npc_key,source_line,decoded_offset,record_sha256,raw_record,prefix28 FROM native_npc_display_rows ORDER BY npc_key");
    std::vector<NativeNpcDisplayRecord> records;
    std::vector<std::uint8_t> canonical;
    const auto append=[&canonical](std::uint32_t value,unsigned width){for(unsigned i=0;i<width;++i)canonical.push_back(static_cast<std::uint8_t>(value>>(8*i)));};
    while(rows.row()) {
        if(!present || records.size()>=4043)throw DatabaseError("NPC display orphan/excess rows");
        NativeNpcDisplayRecord r;
        r.key=rows.number<std::uint16_t>(0);r.source_line=rows.number<std::uint32_t>(1);r.decoded_offset=rows.number<std::uint32_t>(2);
        if(!r.key || r.key>=7000 || !r.source_line || (!records.empty() && records.back().key>=r.key))throw DatabaseError("NPC display row bounds");
        r.record_sha256=rows.text(3);
        const auto raw=rows.blob(4,1,4096);r.raw_record.assign(raw.begin(),raw.end());
        const auto prefix=rows.blob(5,28,28);std::copy(prefix.begin(),prefix.end(),r.prefix28.begin());
        if(digest(raw)!=r.record_sha256)throw DatabaseError("NPC display record SHA mismatch");
        std::copy_n(r.prefix28.begin(),16,r.name16.begin());
        const auto word=[&r](unsigned offset){return static_cast<std::uint16_t>(r.prefix28[offset]|(static_cast<unsigned>(r.prefix28[offset+1])<<8));};
        r.flags=word(16);r.appearance_code=word(18);r.body=word(20);r.face=word(22);r.head=word(24);r.weapon=word(26);
        append(r.key,2);append(r.source_line,4);append(r.decoded_offset,4);append(static_cast<std::uint32_t>(r.raw_record.size()),4);
        canonical.insert(canonical.end(),raw.begin(),raw.end());canonical.insert(canonical.end(),prefix.begin(),prefix.end());
        records.push_back(std::move(r));
    }
    if(present && (records.size()!=4043 || digest(canonical)!=dataset_sha256))throw DatabaseError("NPC display full dataset mismatch");
    scope.finish();return records;
}
std::size_t NativeNpcDisplayCatalog::count() const {return read_all().size();}
bool NativeNpcDisplayCatalog::contains_all(std::span<const std::uint16_t> keys) const {
    if(keys.empty())return true;
    const auto rows=read_all();
    for(const auto key:keys) {
        const auto match=std::lower_bound(rows.begin(),rows.end(),key,[](const auto& row,std::uint16_t id){return row.key<id;});
        if(match==rows.end() || match->key!=key)return false;
    }
    return true;
}
std::optional<NativeNpcDisplayRecord> NativeNpcDisplayCatalog::lookup(std::uint16_t key) const {
    const auto rows=read_all();
    const auto match=std::lower_bound(rows.begin(),rows.end(),key,[](const NativeNpcDisplayRecord& row,std::uint16_t id){return row.key<id;});
    if(match==rows.end() || match->key!=key)return std::nullopt;
    return *match;
}
}
