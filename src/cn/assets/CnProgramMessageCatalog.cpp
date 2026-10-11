#include "cn/assets/CnProgramMessageCatalog.h"
#include <algorithm>
#include <array>
#include <charconv>
#include <stdexcept>
#include <string_view>
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
    std::vector<std::uint8_t> object(length); // Hash is destroyed first.
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
    (void)bytes;return std::nullopt;
#endif
}
// Bounded projection of this exact pinned ProgramMsg block, not a general
// native CSV tokenizer. All1116 rows have no quotes/NUL and actual CRLF. The
// native ProgramMsg loader reads column0 ID then column1 text, ignoring tails.
std::optional<std::vector<CnProgramMessageCatalog::Record>> read_records(
    const CnProgramMessageCatalog::Source& source,std::span<const std::uint8_t> bytes) {
    constexpr std::size_t header_offset=89354,records_end=112839;
    constexpr std::string_view header="ProgramMsg,1116\r\n";
    if(bytes.size()!=records_end || !std::equal(header.begin(),header.end(),bytes.begin()+header_offset))return std::nullopt;
    std::vector<CnProgramMessageCatalog::Record> result;result.reserve(CnProgramMessageCatalog::record_count);
    auto offset=header_offset+header.size();
    for(std::size_t index=0;index<CnProgramMessageCatalog::record_count;++index) {
        const auto start=offset;
        while(offset<records_end && bytes[offset]!='\n')++offset;
        if(offset>=records_end || offset==start || bytes[offset-1]!='\r')return std::nullopt;
        const std::string_view line(reinterpret_cast<const char*>(bytes.data()+start),offset-start-1);
        ++offset;
        if(line.find('"')!=std::string_view::npos || line.find('\0')!=std::string_view::npos)return std::nullopt;
        const auto comma=line.find(',');
        const auto id_text=line.substr(0,comma);
        unsigned id=0;const auto parsed=std::from_chars(id_text.data(),id_text.data()+id_text.size(),id);
        if(parsed.ec!=std::errc{} || parsed.ptr!=id_text.data()+id_text.size() || id!=index+1)return std::nullopt;
        CnProgramMessageCatalog::Record record{source,static_cast<std::uint16_t>(id),
            static_cast<std::uint16_t>(index),static_cast<std::uint32_t>(2028+index),
            static_cast<std::uint32_t>(start),{}, {},{}};
        record.raw_line.assign(bytes.begin()+start,bytes.begin()+offset);
        const auto identity=digest(record.raw_line);if(!identity)return std::nullopt;
        record.record_sha256=*identity;
        if(comma!=std::string_view::npos) {
            const auto text=line.substr(comma+1);
            record.native_column1_cp936=std::string(text.substr(0,text.find(',')));
        }
        //004231B0 explicitly writes NUL when column1 is absent/empty. Do not
        //append the extra comma-separated column of record291 to native text.
        result.push_back(std::move(record));
    }
    if(offset!=records_end)return std::nullopt;
    return result;
}
}
CnProgramMessageCatalog::CnProgramMessageCatalog(Source source,std::vector<Record> records,Current observe)
    :source_(std::move(source)),records_(std::move(records)),current_(std::move(observe)) {}
void CnProgramMessageCatalog::owner() const {
    if(thread_!=std::this_thread::get_id())throw std::logic_error("CN ProgramMsg resource owner mismatch");
}
std::shared_ptr<const CnProgramMessageCatalog> CnProgramMessageCatalog::read_actual_source(
    Source source,std::span<const std::uint8_t> encoded,std::span<const std::uint8_t> decoded,Current observe) {
    if(!source.actual_revision || source.actual_client_sha256!=client_sha256 || !observe ||
       encoded.size()!=59375 || decoded.size()!=112839 || !observe(source))return {};
    const std::vector<std::uint8_t> owned_encoded(encoded.begin(),encoded.end()),owned_decoded(decoded.begin(),decoded.end());
    const auto encoded_identity=digest(owned_encoded),decoded_identity=digest(owned_decoded);
    if(!encoded_identity || !decoded_identity || *encoded_identity!=encoded_sha256 || *decoded_identity!=decoded_sha256)return {};
    auto records=read_records(source,owned_decoded);
    if(!records || !observe(source))return {};
    return std::shared_ptr<const CnProgramMessageCatalog>(new CnProgramMessageCatalog(
        std::move(source),std::move(*records),std::move(observe)));
}
bool CnProgramMessageCatalog::current() const {
    owner();const auto observe=current_;const auto source=source_;
    return observe && observe(source);
}
std::optional<CnProgramMessageCatalog::Record> CnProgramMessageCatalog::lookup_id(std::uint16_t id) const {
    if(!id)return std::nullopt;
    return lookup_zero_based_index(static_cast<std::size_t>(id)-1);
}
std::optional<CnProgramMessageCatalog::Record> CnProgramMessageCatalog::lookup_zero_based_index(std::size_t index) const {
    if(!current() || index>=records_.size())return std::nullopt;
    auto result=records_[index];
    if(!current())return std::nullopt;
    return result;
}
}
