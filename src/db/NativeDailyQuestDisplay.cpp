#include "db/NativeQuestCatalog.h"
#include "db/SqliteSupport.h"
#include "protocol/RecoveredDailyQuestRequest.h"
#include <algorithm>
#include <span>
#ifdef _WIN32
#include <windows.h>
#include <bcrypt.h>
#endif
namespace god2 {
namespace {
constexpr const char* client="6bf75ef8ac1e0f6b2240800ff841d205788bd1b6512149584b5386b10f431e98";
constexpr const char* source="4a347d56706946d7004b2bd2118500ffc60844628fa461862b2f6d5320a90e54";
constexpr const char* decoded="2848b95b0af99eac10ca4dff61a5533c13917127c4738039e263c60a1be45eaf";
constexpr const char* fingerprint="df0bc3a96425c3440cd2fefc867840aa10e3ad35c4a3be32e332c6204f30236a";
std::string sha(std::span<const std::uint8_t> bytes) {
#ifdef _WIN32
    BCRYPT_ALG_HANDLE algorithm=nullptr;BCRYPT_HASH_HANDLE hash=nullptr;
    if(!BCRYPT_SUCCESS(BCryptOpenAlgorithmProvider(&algorithm,BCRYPT_SHA256_ALGORITHM,nullptr,0)))throw DatabaseError("Daily SHA256 provider unavailable");
    DWORD size=0,returned=0;auto status=BCryptGetProperty(algorithm,BCRYPT_OBJECT_LENGTH,reinterpret_cast<PUCHAR>(&size),sizeof(size),&returned,0);
    std::vector<std::uint8_t> object(size);std::array<std::uint8_t,32> result{};
    if(BCRYPT_SUCCESS(status))status=BCryptCreateHash(algorithm,&hash,object.data(),size,nullptr,0,0);
    if(BCRYPT_SUCCESS(status))status=BCryptHashData(hash,const_cast<PUCHAR>(bytes.data()),static_cast<ULONG>(bytes.size()),0);
    if(BCRYPT_SUCCESS(status))status=BCryptFinishHash(hash,result.data(),static_cast<ULONG>(result.size()),0);
    const auto destroyed=hash?BCryptDestroyHash(hash):0;const auto closed=BCryptCloseAlgorithmProvider(algorithm,0);
    if(!BCRYPT_SUCCESS(status) || !BCRYPT_SUCCESS(destroyed) || !BCRYPT_SUCCESS(closed))throw DatabaseError("Daily SHA256 failed");
    std::string value;for(const auto b:result){value+="0123456789abcdef"[b>>4];value+="0123456789abcdef"[b&15];}return value;
#else
    (void)bytes;throw DatabaseError("Qualified daily SHA256 backend unavailable");
#endif
}
}
std::vector<NativeDailyQuestDisplay> NativeQuestCatalog::daily_displays() const {
    sqlite_detail::Statement rows(db_,"SELECT ordinal,source_line,pair_index,pair_branch,logical,source_record_sha256,client_sha256,source_sha256,decoded_sha256,catalog_sha256,authority FROM native_daily_quest_parsed ORDER BY ordinal");
    std::vector<NativeDailyQuestDisplay> result;std::vector<std::uint8_t> full,raw_full;
    while(rows.row()) {
        const auto ordinal=rows.number<std::uint8_t>(0);const auto raw=daily_source(ordinal);
        NativeDailyQuestDisplay value{ordinal,rows.number<std::uint8_t>(2),rows.number<std::uint8_t>(3),rows.integer(1),{}};
        const auto bytes=rows.blob(4,316,316);std::copy(bytes.begin(),bytes.end(),value.logical.begin());
        if(ordinal!=result.size() || !raw || raw->source_line!=value.source_line || value.source_line!=ordinal+6 || rows.text(5)!=raw->record_sha256 ||
           rows.text(6)!=client || rows.text(7)!=source || rows.text(8)!=decoded || rows.text(9)!=fingerprint ||
           rows.text(10)!="NATIVE_PARSED_DISPLAY_ONLY" || value.logical[0]!=value.index || value.logical[1]!=value.branch ||
           sha(raw->raw_record)!=raw->record_sha256)throw DatabaseError("Daily parsed provenance mismatch");
        for(unsigned i=0;i<4;++i)raw_full.push_back(static_cast<std::uint8_t>(raw->raw_record.size()>>(8*i)));
        raw_full.insert(raw_full.end(),raw->raw_record.begin(),raw->raw_record.end());
        full.insert(full.end(),bytes.begin(),bytes.end());result.push_back(value);
    }
    if(!result.empty() && (result.size()!=85 || sha(full)!=fingerprint ||
       sha(raw_full)!="29b67f9d734a30ca584b6b09a295713cd2e32e00de44ce4472c47a2d65dc079b"))throw DatabaseError("Incomplete or changed daily native316 catalog");
    return result;
}
std::optional<OwnedDailyQuestList> NativeQuestCatalog::owned_daily_list(std::int64_t account,std::int64_t character) const {
    if(account<=0 || character<=0)return std::nullopt;
    sqlite_detail::Statement row(db_,"SELECT q.logical,q.revision,q.origin,q.provenance,q.client_sha256,q.design_id FROM character_daily_quest_lists q JOIN recovered_characters c ON c.id=q.character_id WHERE c.account_id=? AND c.id=?");
    row.bind(1,account);row.bind(2,character);if(!row.row())return std::nullopt;
    OwnedDailyQuestList value;const auto logical=row.blob(0,172,172);std::copy(logical.begin(),logical.end(),value.logical.begin());value.revision=row.integer(1);
    const auto origin=row.text(2),provenance=row.text(3);
    if(value.revision<=0 || (origin!="NATIVE_CAPTURE_VERIFIED" && origin!="CUSTOM_TEST_NOT_NATIVE") || provenance.empty() || provenance.size()>512 ||
       row.text(4)!=client || row.text(5)!="CUSTOM-0049" || !RecoveredDailyQuestRequest::valid_list(value.logical))throw DatabaseError("Invalid owned daily display list");
    if(row.row())throw DatabaseError("Duplicate daily list owner");
    const auto source_rows=daily_displays();
    if(source_rows.empty())throw DatabaseError("Owned daily list requires full native316 source");
    for(std::size_t i=0;i<value.logical[164];++i) {
        const auto offset=4+4*i;
        if(std::none_of(source_rows.begin(),source_rows.end(),[&](const auto& source_row){return source_row.index==value.logical[offset] && source_row.branch==value.logical[offset+1];}))
            throw DatabaseError("Daily issued pair missing native source");
    }
    return value;
}
}
