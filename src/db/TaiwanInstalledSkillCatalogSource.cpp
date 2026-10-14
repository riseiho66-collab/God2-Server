#include "db/TaiwanInstalledSkillCatalogSource.h"
#include <optional>
#include <string>
#include <utility>
#ifdef _WIN32
#ifndef NOMINMAX
#define NOMINMAX
#endif
#include <windows.h>
#include <bcrypt.h>
#endif

namespace god2 {
namespace {
constexpr char installed_sha256[]="3adcda70a477086da50411fe5d023eec33f915efafd17ec478d55542cae42ea7";
std::optional<std::string> sha256(std::span<const std::uint8_t> bytes) {
#ifdef _WIN32
    struct Algorithm {
        BCRYPT_ALG_HANDLE value=nullptr;
        ~Algorithm(){if(value)BCryptCloseAlgorithmProvider(value,0);}
    } algorithm;
    struct Hash {
        BCRYPT_HASH_HANDLE value=nullptr;
        ~Hash(){if(value)BCryptDestroyHash(value);}
    };
    if(bytes.size()>MAXULONG ||
       BCryptOpenAlgorithmProvider(&algorithm.value,BCRYPT_SHA256_ALGORITHM,nullptr,0)<0)
        return std::nullopt;
    DWORD length=0,returned=0;
    if(BCryptGetProperty(algorithm.value,BCRYPT_OBJECT_LENGTH,reinterpret_cast<PUCHAR>(&length),
        sizeof(length),&returned,0)<0 || returned!=sizeof(length) || !length)return std::nullopt;
    std::vector<std::uint8_t> object(length);
    Hash hash; // Destroy the hash before its backing object and algorithm.
    if(BCryptCreateHash(algorithm.value,&hash.value,object.data(),length,nullptr,0,0)<0)return std::nullopt;
    std::array<std::uint8_t,32> result{};
    if(BCryptHashData(hash.value,const_cast<PUCHAR>(bytes.data()),static_cast<ULONG>(bytes.size()),0)<0 ||
       BCryptFinishHash(hash.value,result.data(),static_cast<ULONG>(result.size()),0)<0)return std::nullopt;
    constexpr char hex[]="0123456789abcdef";
    std::string digest;digest.reserve(64);
    for(const auto byte:result){digest.push_back(hex[byte>>4]);digest.push_back(hex[byte&15]);}
    return digest;
#else
    (void)bytes;return std::nullopt; // Unsupported platforms never claim a pin.
#endif
}
std::uint32_t little_dword(std::span<const std::uint8_t> bytes,std::size_t at) noexcept {
    return std::uint32_t(bytes[at])|(std::uint32_t(bytes[at+1])<<8)|
        (std::uint32_t(bytes[at+2])<<16)|(std::uint32_t(bytes[at+3])<<24);
}
}
TaiwanInstalledSkillCatalogSource::TaiwanInstalledSkillCatalogSource(NativeSkillSource source,
    std::vector<NativeSkillRecord> records,std::vector<std::uint8_t> bytes)
    :source_(std::move(source)),records_(std::move(records)),bytes_(std::move(bytes)) {}
std::shared_ptr<const TaiwanInstalledSkillCatalogSource> TaiwanInstalledSkillCatalogSource::read_actual_source(
    std::span<const std::uint8_t> input) {
    if(input.size()!=file_bytes)return {};
    // Hash, header/bank validation and eager row materialization all use this
    // same owned copy. No later importer reads a mutable borrowed input.
    std::vector<std::uint8_t> owned(input.begin(),input.end());
    const auto identity=sha256(owned);
    if(!identity || *identity!=installed_sha256 || owned[0]!='1' || owned[1]!='.' ||
       owned[2]!='0' || owned[3]!='3')return {};
    NativeSkillSource source{native_taiwan_installed_dataset_id,"Data2/Fight/Spg/cbspec2.bin",
        *identity,*identity,"149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763",
        "1.03","0x12d3b0","0x11c520",static_cast<std::int64_t>(record_count)};
    // Descriptor/RVAs are the original retained TW consumer annotation; they
    // do not attest the current installed EXE or invent a new native loader.
    if(!native_taiwan_skill_source_matches(source,NativeTaiwanSkillProfile::Installed453))return {};
    std::vector<NativeSkillRecord> records;records.reserve(record_count);
    for(std::size_t kind=0;kind<declared_counts.size();++kind) {
        if(little_dword(owned,4+kind*group_bytes)!=declared_counts[kind])return {};
        for(std::uint32_t id=1;id<=declared_counts[kind];++id) {
            const auto at=8+kind*group_bytes+(std::size_t(id)-1)*record_bytes;
            if(at>owned.size() || record_bytes>owned.size()-at)return {};
            const auto raw=std::span<const std::uint8_t>(owned).subspan(at,record_bytes);
            if(raw[0]!=id || raw[1]!=kind)return {};
            auto digest=sha256(raw);if(!digest)return {};
            records.push_back(NativeSkillRecord{source,static_cast<std::int64_t>(records.size()),
                static_cast<std::int64_t>(at),std::move(*digest),
                std::vector<std::uint8_t>(raw.begin(),raw.end()),
                static_cast<std::int64_t>(kind),static_cast<std::int64_t>(id)});
        }
    }
    if(records.size()!=record_count)return {};
    return std::shared_ptr<const TaiwanInstalledSkillCatalogSource>(new TaiwanInstalledSkillCatalogSource(
        std::move(source),std::move(records),std::move(owned)));
}
}
