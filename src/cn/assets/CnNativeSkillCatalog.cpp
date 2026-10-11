#include "cn/assets/CnNativeSkillCatalog.h"
#include <algorithm>
#include <utility>
#ifdef _WIN32
#include <windows.h>
#include <bcrypt.h>
#endif

namespace god2cn {
namespace {
std::optional<std::string> digest(std::span<const std::uint8_t> bytes) {
#ifdef _WIN32
    struct Algorithm {
        BCRYPT_ALG_HANDLE value=nullptr;
        ~Algorithm(){if(value)BCryptCloseAlgorithmProvider(value,0);}
    } algorithm;
    struct Hash {
        BCRYPT_HASH_HANDLE value=nullptr;
        ~Hash(){if(value)BCryptDestroyHash(value);}
    };
    if(bytes.size()>MAXULONG || BCryptOpenAlgorithmProvider(&algorithm.value,BCRYPT_SHA256_ALGORITHM,nullptr,0)<0)
        return std::nullopt;
    DWORD length=0,returned=0;
    if(BCryptGetProperty(algorithm.value,BCRYPT_OBJECT_LENGTH,reinterpret_cast<PUCHAR>(&length),
        sizeof(length),&returned,0)<0 || returned!=sizeof(length) || !length)return std::nullopt;
    // Object storage outlives the hash handle on all return paths.
    std::vector<std::uint8_t> object(length);
    Hash hash;
    if(BCryptCreateHash(algorithm.value,&hash.value,object.data(),length,nullptr,0,0)<0)return std::nullopt;
    std::array<std::uint8_t,32> result{};
    if(BCryptHashData(hash.value,const_cast<PUCHAR>(bytes.data()),static_cast<ULONG>(bytes.size()),0)<0 ||
       BCryptFinishHash(hash.value,result.data(),static_cast<ULONG>(result.size()),0)<0)return std::nullopt;
    constexpr char hex[]="0123456789abcdef";
    std::string text;text.reserve(64);
    for(const auto byte:result){text.push_back(hex[byte>>4]);text.push_back(hex[byte&15]);}
    return text;
#else
    (void)bytes;return std::nullopt; // No claimed hash qualification on an unsupported platform.
#endif
}
std::uint32_t little_dword(std::span<const std::uint8_t> bytes,std::size_t at) {
    return std::uint32_t(bytes[at])|(std::uint32_t(bytes[at+1])<<8)|
        (std::uint32_t(bytes[at+2])<<16)|(std::uint32_t(bytes[at+3])<<24);
}
}
CnNativeSkillCatalog::CnNativeSkillCatalog(Source source,std::vector<std::uint8_t> bytes,Current current)
    :source_(std::move(source)),bytes_(std::move(bytes)),current_(std::move(current)) {}
std::shared_ptr<const CnNativeSkillCatalog> CnNativeSkillCatalog::read_actual_source(
    Source source,std::span<const std::uint8_t> bytes,Current observe) {
    if(!source.actual_revision || source.actual_client_sha256!=client_sha256 || !observe ||
       bytes.size()!=resource_bytes || !observe(source))return {};
    // Own first; hash and parse the same retained bytes, never a borrowed buffer
    // whose contents can change between qualification and later lookups.
    std::vector<std::uint8_t> owned(bytes.begin(),bytes.end());
    const auto identity=digest(owned);
    if(!identity || *identity!=resource_sha256 || owned[0]!='1' || owned[1]!='.' ||
       owned[2]!='0' || owned[3]!='3')return {};
    for(std::size_t kind=0;kind<declared_counts.size();++kind) {
        if(little_dword(owned,4+kind*group_bytes)!=declared_counts[kind])return {};
        for(std::uint32_t id=1;id<=declared_counts[kind];++id) {
            const auto at=8+kind*group_bytes+(id-1)*record_bytes;
            if(owned[at]!=id || owned[at+1]!=kind)return {};
        }
    }
    if(!observe(source))return {};
    return std::shared_ptr<const CnNativeSkillCatalog>(new CnNativeSkillCatalog(
        std::move(source),std::move(owned),std::move(observe)));
}
bool CnNativeSkillCatalog::current() const {
    const auto observe=current_;const auto source=source_;return observe && observe(source);
}
std::optional<CnNativeSkillCatalog::Record> CnNativeSkillCatalog::retained_lookup(
    std::uint8_t kind,std::uint8_t id) const {
    if(kind>=declared_counts.size() || !id || id>declared_counts[kind])return std::nullopt;
    const auto at=8+std::size_t(kind)*group_bytes+(std::size_t(id)-1)*record_bytes;
    Record record{source_,kind,id,static_cast<std::uint32_t>(at),{}, {}};
    std::copy_n(bytes_.begin()+at,record_bytes,record.raw.begin());
    const auto identity=digest(record.raw);if(!identity)return std::nullopt;
    record.record_sha256=*identity;return record;
}
std::optional<CnNativeSkillCatalog::Record> CnNativeSkillCatalog::lookup(
    std::uint8_t kind,std::uint8_t id) const {
    if(!current())return std::nullopt;
    auto record=retained_lookup(kind,id);if(!record || !current())return std::nullopt;return record;
}
std::optional<std::vector<CnNativeSkillCatalog::Record>> CnNativeSkillCatalog::lookup_words(
    std::span<const std::uint16_t> words) const {
    if(!current())return std::nullopt;
    std::vector<Record> records;records.reserve(words.size());
    for(const auto word:words) {
        auto record=retained_lookup(static_cast<std::uint8_t>(word>>8),static_cast<std::uint8_t>(word&255));
        if(!record)return std::nullopt;records.push_back(std::move(*record));
    }
    if(!current())return std::nullopt;return records;
}
}
