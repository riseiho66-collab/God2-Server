#include "cn/assets/CnNativeSkillBookBindings.h"
#include <algorithm>
#include <charconv>
#include <stdexcept>
#include <string_view>
#include <utility>
#ifdef _WIN32
#include <windows.h>
#include <bcrypt.h>
#endif

namespace god2::cn {
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
    std::vector<std::uint8_t> object(length); // Outlives Hash on every exit.
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
// This is a bounded projection of THIS pinned SKB block: its386 lines have
// no CSV quotes,29/30 fields and CRLF. No general native tokenizer emulation
// or reconstructed396-byte item buffer is claimed.
std::optional<std::vector<CnNativeSkillBookBindings::Book>> read_books(
    const CnNativeSkillBookBindings::Source& source,std::span<const std::uint8_t> bytes) {
    constexpr std::size_t header_offset=739098,records_end=806862;
    constexpr std::string_view header="SKB,386\r\n";
    if(bytes.size()!=3042675 || !std::equal(header.begin(),header.end(),bytes.begin()+header_offset))
        return std::nullopt;
    std::vector<CnNativeSkillBookBindings::Book> books;books.reserve(386);
    auto offset=header_offset+header.size();
    for(std::uint32_t index=0;index<386;++index) {
        const auto start=offset;
        while(offset<records_end && bytes[offset]!='\n')++offset;
        if(offset>=records_end || offset==start || bytes[offset-1]!='\r')return std::nullopt;
        const std::string_view line(reinterpret_cast<const char*>(bytes.data()+start),offset-start-1);
        ++offset;
        if(line.find('"')!=std::string_view::npos || line.find('\0')!=std::string_view::npos)return std::nullopt;
        std::vector<std::string_view> fields;
        std::size_t begin=0;
        for(std::size_t pos=0;pos<=line.size();++pos)
            if(pos==line.size() || line[pos]==',') {
                fields.push_back(line.substr(begin,pos-begin));begin=pos+1;
            }
        if(fields.size()!=29 && fields.size()!=30)return std::nullopt;
        unsigned item=0;const auto converted=std::from_chars(fields[0].data(),fields[0].data()+fields[0].size(),item);
        if(converted.ec!=std::errc{} || converted.ptr!=fields[0].data()+fields[0].size() ||
           item<6501 || item>6900)return std::nullopt;
        const auto alias=fields[26];
        if(alias.size()<6 || alias.size()>7 || alias.substr(0,3)!="Spc" ||
           alias[3]<'A' || alias[3]>'D' ||
           !std::all_of(alias.begin()+4,alias.end(),[](char c){return c>='0' && c<='9';}))return std::nullopt;
        CnNativeSkillBookBindings::Book book{source,index,9442+index,
            static_cast<std::uint32_t>(start),static_cast<std::uint16_t>(item),{}, {},std::string(alias),{}};
        book.raw_line.assign(bytes.begin()+start,bytes.begin()+offset);
        const auto identity=digest(book.raw_line);if(!identity)return std::nullopt;
        book.record_sha256=*identity;
        for(unsigned tail=0;tail<3;++tail)
            if(27+tail<fields.size())book.opaque_tail_fields[tail]=std::string(fields[27+tail]);
        books.push_back(std::move(book));
    }
    if(offset!=records_end)return std::nullopt;
    std::sort(books.begin(),books.end(),[](const auto& a,const auto& b){return a.item_id<b.item_id;});
    for(std::size_t i=1;i<books.size();++i)if(books[i-1].item_id==books[i].item_id)return std::nullopt;
    return books;
}
}
CnNativeSkillBookBindings::CnNativeSkillBookBindings(Source source,std::vector<Book> books,
    std::shared_ptr<const CnSharedSkillCatalog> skills,Current observe)
    :source_(std::move(source)),books_(std::move(books)),skills_(std::move(skills)),current_(std::move(observe)) {}
void CnNativeSkillBookBindings::owner() const {
    if(thread_!=std::this_thread::get_id())throw std::logic_error("CN skill book source game owner mismatch");
}
std::shared_ptr<const CnNativeSkillBookBindings> CnNativeSkillBookBindings::read_actual_source(
    Source source,std::span<const std::uint8_t> encoded,std::span<const std::uint8_t> decoded,
    std::shared_ptr<const CnSharedSkillCatalog> skills,Current observe) {
    if(!source.actual_revision || source.actual_client_sha256!=client_sha256 || !observe ||
       !skills || !skills->current() || encoded.size()!=795868 || decoded.size()!=3042675 || !observe(source))return {};
    const std::vector<std::uint8_t> owned_encoded(encoded.begin(),encoded.end()),owned_decoded(decoded.begin(),decoded.end());
    const auto encoded_identity=digest(owned_encoded),decoded_identity=digest(owned_decoded);
    if(!encoded_identity || !decoded_identity || *encoded_identity!=encoded_sha256 ||
       *decoded_identity!=decoded_sha256)return {};
    auto books=read_books(source,owned_decoded);
    if(!books || !skills->current() || !observe(source))return {};
    return std::shared_ptr<const CnNativeSkillBookBindings>(new CnNativeSkillBookBindings(
        std::move(source),std::move(*books),std::move(skills),std::move(observe)));
}
bool CnNativeSkillBookBindings::current() const {
    owner();const auto observe=current_;const auto source=source_;
    return skills_->current() && observe && observe(source);
}
bool CnNativeSkillBookBindings::uses_shared_catalog(const CnSharedSkillCatalog& skills) const {
    owner();return skills_.get()==&skills;
}
std::optional<CnNativeSkillBookBindings::Book> CnNativeSkillBookBindings::lookup_item(
    std::uint16_t item_id) const {
    if(!current())return std::nullopt;
    const auto found=std::lower_bound(books_.begin(),books_.end(),item_id,
        [](const Book& book,std::uint16_t item){return book.item_id<item;});
    if(found==books_.end() || found->item_id!=item_id)return std::nullopt;
    Book result=*found;
    if(!current())return std::nullopt;
    return result;
}
std::optional<CnNativeSkillBookBindings::Binding> CnNativeSkillBookBindings::retained_lookup(
    std::uint8_t kind,std::uint8_t id) const {
    auto definition=skills_->lookup(kind,id);if(!definition)return std::nullopt;
    constexpr std::array<unsigned,4> bases{6500,6600,6700,6800};
    constexpr std::array<char,4> letters{'A','D','C','B'};
    // Native4D2BB0 uses SpcA%3d for A>=100,otherwise the category's%02d.
    // For the qualified unsigned IDs100..255,%3d has no leading space.
    auto selector=std::string("Spc")+letters[kind]+(id<10?"0":"")+std::to_string(id);
    Binding result{std::move(*definition),std::nullopt,std::move(selector),static_cast<std::uint8_t>(id<100?6:7)};
    // Exactly offsets1..399 in the native base range, first matching pointer.
    // The pinned65 PFD and47 GEH rows retain zero at parsed+11C: zeroed
    // allocation plus parser type9/type0's default branch (retained proof).
    for(const auto& book:books_) {
        if(book.item_id<=bases[kind] || book.item_id>=bases[kind]+400)continue;
        if(book.native_alias.compare(0,result.native_compare_bytes,result.native_selector,0,result.native_compare_bytes)==0) {
            result.matching_book=book;break;
        }
    }
    return result;
}
std::optional<CnNativeSkillBookBindings::Binding> CnNativeSkillBookBindings::lookup(
    std::uint8_t kind,std::uint8_t id) const {
    if(!current())return std::nullopt;
    auto result=retained_lookup(kind,id);if(!result || !current())return std::nullopt;return result;
}
std::optional<std::vector<CnNativeSkillBookBindings::Binding>> CnNativeSkillBookBindings::lookup_words(
    std::span<const std::uint16_t> words) const {
    if(!current())return std::nullopt;
    std::vector<Binding> result;result.reserve(words.size());
    for(const auto word:words) {
        auto binding=retained_lookup(static_cast<std::uint8_t>(word>>8),static_cast<std::uint8_t>(word&255));
        if(!binding)return std::nullopt;result.push_back(std::move(*binding));
    }
    if(!current())return std::nullopt;return result;
}
}
