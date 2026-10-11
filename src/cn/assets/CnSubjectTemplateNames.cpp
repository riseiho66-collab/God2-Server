#include "cn/assets/CnSubjectTemplateNames.h"
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
    (void)bytes;return std::nullopt;
#endif
}
// Bounded projection of the exact pinned GOD block. Not a general CSV loader
// or reconstruction of the native396-byte item record/unwritten fields.
std::optional<std::vector<CnSubjectTemplateNames::Record>> read_records(
    const CnSubjectTemplateNames::Source& source,std::span<const std::uint8_t> bytes) {
    constexpr std::size_t header_offset=415519,records_end=416611;
    constexpr std::string_view header="GOD,34\r\n";
    if(bytes.size()!=3042675 || !std::equal(header.begin(),header.end(),bytes.begin()+header_offset))return std::nullopt;
    auto offset=header_offset+header.size();
    std::vector<CnSubjectTemplateNames::Record> result;result.reserve(CnSubjectTemplateNames::record_count);
    for(std::size_t index=0;index<CnSubjectTemplateNames::record_count;++index) {
        const auto start=offset;
        while(offset<records_end && bytes[offset]!='\n')++offset;
        if(offset>=records_end || offset==start || bytes[offset-1]!='\r')return std::nullopt;
        const std::string_view line(reinterpret_cast<const char*>(bytes.data()+start),offset-start-1);
        ++offset;
        if(line.find('"')!=std::string_view::npos || line.find('\0')!=std::string_view::npos)return std::nullopt;
        std::array<std::string_view,6> fields;auto remaining=line;
        for(std::size_t column=0;column<fields.size();++column) {
            const auto comma=remaining.find(',');
            if(column+1<fields.size()) {
                if(comma==std::string_view::npos)return std::nullopt;
                fields[column]=remaining.substr(0,comma);remaining.remove_prefix(comma+1);
            }else {
                if(comma!=std::string_view::npos)return std::nullopt;
                fields[column]=remaining;
            }
        }
        unsigned key=0;
        const auto parsed=std::from_chars(fields[0].data(),fields[0].data()+fields[0].size(),key);
        if(parsed.ec!=std::errc{} || parsed.ptr!=fields[0].data()+fields[0].size() || key!=2801+index ||
           fields[4].size()>37)return std::nullopt;
        CnSubjectTemplateNames::Record record{source,static_cast<std::uint16_t>(key),
            static_cast<std::uint32_t>(6610+index),static_cast<std::uint32_t>(start),{},{},std::string(fields[4])};
        record.raw_line.assign(bytes.begin()+start,bytes.begin()+offset);
        const auto identity=digest(record.raw_line);if(!identity)return std::nullopt;
        record.record_sha256=*identity;result.push_back(std::move(record));
    }
    if(offset!=records_end)return std::nullopt;
    return result;
}
std::optional<std::vector<CnSubjectTemplateNames::LevelRecord>> read_levels(
    const CnSubjectTemplateNames::Source& source,std::span<const std::uint8_t> bytes) {
    constexpr std::size_t header_offset=2731988,records_end=2732040;
    constexpr std::string_view header="GodLevel,4\r\n";
    if(bytes.size()!=3042675 || !std::equal(header.begin(),header.end(),bytes.begin()+header_offset))return std::nullopt;
    auto offset=header_offset+header.size();std::vector<CnSubjectTemplateNames::LevelRecord> result;
    result.reserve(CnSubjectTemplateNames::level_record_count);
    for(std::size_t index=0;index<CnSubjectTemplateNames::level_record_count;++index) {
        const auto start=offset;
        while(offset<records_end && bytes[offset]!='\n')++offset;
        if(offset>=records_end || offset==start || bytes[offset-1]!='\r')return std::nullopt;
        const std::string_view line(reinterpret_cast<const char*>(bytes.data()+start),offset-start-1);++offset;
        if(line.find('"')!=std::string_view::npos || line.find('\0')!=std::string_view::npos)return std::nullopt;
        const auto comma=line.find(',');
        if(comma==std::string_view::npos || line.find(',',comma+1)!=std::string_view::npos)return std::nullopt;
        const auto number=line.substr(comma+1);unsigned id=0;
        const auto parsed=std::from_chars(number.data(),number.data()+number.size(),id);
        if(parsed.ec!=std::errc{} || parsed.ptr!=number.data()+number.size() || id!=index+1 || comma!=6)return std::nullopt;
        CnSubjectTemplateNames::LevelRecord record{source,static_cast<std::uint8_t>(index),
            static_cast<std::uint8_t>(id),static_cast<std::uint32_t>(22910+index),static_cast<std::uint32_t>(start),
            {},{},std::string(line.substr(0,comma))};
        record.raw_line.assign(bytes.begin()+start,bytes.begin()+offset);
        const auto identity=digest(record.raw_line);if(!identity)return std::nullopt;
        record.record_sha256=*identity;result.push_back(std::move(record));
    }
    if(offset!=records_end)return std::nullopt;
    return result;
}
}
CnSubjectTemplateNames::CnSubjectTemplateNames(Source source,std::vector<Record> records,
    std::vector<LevelRecord> levels,Current current)
    :source_(std::move(source)),records_(std::move(records)),levels_(std::move(levels)),current_(std::move(current)) {}
void CnSubjectTemplateNames::owner() const {
    if(thread_!=std::this_thread::get_id())throw std::logic_error("CN subject template source owner mismatch");
}
std::shared_ptr<const CnSubjectTemplateNames> CnSubjectTemplateNames::read_actual_source(
    Source source,std::span<const std::uint8_t> encoded,std::span<const std::uint8_t> decoded,Current observe) {
    if(!source.actual_revision || source.actual_client_sha256!=client_sha256 || !observe ||
       encoded.size()!=795868 || decoded.size()!=3042675 || !observe(source))return {};
    const std::vector<std::uint8_t> owned_encoded(encoded.begin(),encoded.end()),owned_decoded(decoded.begin(),decoded.end());
    const auto encoded_identity=digest(owned_encoded),decoded_identity=digest(owned_decoded);
    if(!encoded_identity || !decoded_identity || *encoded_identity!=encoded_sha256 || *decoded_identity!=decoded_sha256)return {};
    auto records=read_records(source,owned_decoded);
    auto levels=read_levels(source,owned_decoded);
    if(!records || !levels || !observe(source))return {};
    return std::shared_ptr<const CnSubjectTemplateNames>(new CnSubjectTemplateNames(
        std::move(source),std::move(*records),std::move(*levels),std::move(observe)));
}
bool CnSubjectTemplateNames::current() const {
    owner();const auto observe=current_;const auto source=source_;
    return observe && observe(source);
}
std::optional<CnSubjectTemplateNames::Lookup> CnSubjectTemplateNames::lookup_absolute_identifier(std::uint16_t id) const {
    if(!current() || !id || id>=100)return std::nullopt;
    Lookup result{source_,id,static_cast<std::uint16_t>(2800+id),std::nullopt,{}};
    if(id<=records_.size()) {
        result.actual_record=records_[id-1];
        const auto& name=result.actual_record->native_column4_cp936;
        result.native_name_with_nul.assign(name.begin(),name.end());
        result.native_name_with_nul.push_back(0);
    }else result.native_name_with_nul={' ',0};
    if(!current())return std::nullopt;
    return result;
}
std::optional<CnSubjectTemplateNames::LevelLookup> CnSubjectTemplateNames::lookup_level_selector(std::uint8_t selector) const {
    if(!current())return std::nullopt;
    LevelLookup result{source_,selector,4,LevelAction::RetainExistingText,std::nullopt,{}};
    if(selector<levels_.size()) {
        result.action=LevelAction::CopyKnownSource;result.actual_record=levels_[selector];
        const auto& name=result.actual_record->native_column0_cp936;
        result.native_name_with_nul.assign(name.begin(),name.end());result.native_name_with_nul.push_back(0);
    }else if(selector==4)result.action=LevelAction::UnresolvedAcceptedString;
    if(!current())return std::nullopt;
    return result;
}
}
