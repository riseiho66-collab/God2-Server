#include "game/TaiwanNativeDrvDoll.h"
#include <algorithm>
#include <charconv>
#include <stdexcept>
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
[[noreturn]] void invalid(){throw std::invalid_argument("Unqualified TW DrvDoll source");}
std::string digest(std::span<const std::uint8_t> bytes) {
#ifdef _WIN32
    BCRYPT_ALG_HANDLE algorithm=nullptr;BCRYPT_HASH_HANDLE hash=nullptr;
    if(!BCRYPT_SUCCESS(BCryptOpenAlgorithmProvider(&algorithm,BCRYPT_SHA256_ALGORITHM,nullptr,0)))invalid();
    DWORD size=0,returned=0;
    auto status=BCryptGetProperty(algorithm,BCRYPT_OBJECT_LENGTH,reinterpret_cast<PUCHAR>(&size),sizeof(size),&returned,0);
    std::vector<std::uint8_t> object(size);std::array<std::uint8_t,32> result{};
    if(BCRYPT_SUCCESS(status))status=BCryptCreateHash(algorithm,&hash,object.data(),size,nullptr,0,0);
    if(BCRYPT_SUCCESS(status))status=BCryptHashData(hash,const_cast<PUCHAR>(bytes.data()),static_cast<ULONG>(bytes.size()),0);
    if(BCRYPT_SUCCESS(status))status=BCryptFinishHash(hash,result.data(),static_cast<ULONG>(result.size()),0);
    const auto destroyed=hash?BCryptDestroyHash(hash):0;const auto closed=BCryptCloseAlgorithmProvider(algorithm,0);
    if(!BCRYPT_SUCCESS(status)||!BCRYPT_SUCCESS(destroyed)||!BCRYPT_SUCCESS(closed))invalid();
    std::string out;for(const auto b:result){out+="0123456789abcdef"[b>>4];out+="0123456789abcdef"[b&15];}return out;
#else
    (void)bytes;throw std::runtime_error("Qualified TW DrvDoll SHA256 backend unavailable");
#endif
}
struct Line {std::size_t offset,size;}; // Raw size includes CRLF.
std::string_view text(const std::vector<std::uint8_t>& data,Line line) {
    return {reinterpret_cast<const char*>(data.data()+line.offset),line.size-2};
}
std::vector<std::vector<std::uint8_t>> fields(std::string_view value) {
    std::vector<std::vector<std::uint8_t>> out;std::size_t begin=0;
    const auto* bytes=reinterpret_cast<const std::uint8_t*>(value.data());
    for(std::size_t i=0;i<=value.size();++i)if(i==value.size()||value[i]==',') {
        out.emplace_back(bytes+begin,bytes+i);begin=i+1;
    }
    return out;
}
std::int32_t number(std::span<const std::uint8_t> bytes,bool empty_zero=false) {
    if(bytes.empty()){if(empty_zero)return 0;invalid();}
    const auto field=std::string_view(reinterpret_cast<const char*>(bytes.data()),bytes.size());
    std::int32_t value{};const auto parsed=std::from_chars(field.data(),field.data()+field.size(),value);
    // Exact source has ASCII integer spelling, no quotes/whitespace/junk.
    if(parsed.ec!=std::errc{}||parsed.ptr!=field.data()+field.size())invalid();return value;
}
}
TaiwanNativeDrvDoll::TaiwanNativeDrvDoll(std::filesystem::path origin,
        std::vector<std::uint8_t> plain,std::vector<std::uint8_t> header,std::vector<Record> records)
    :origin_(std::move(origin)),plain_(std::move(plain)),header_(std::move(header)),records_(std::move(records)) {}
std::shared_ptr<const TaiwanNativeDrvDoll> TaiwanNativeDrvDoll::from_pinned_decoded(
        std::filesystem::path origin,std::span<const std::uint8_t> bytes) {
    if(origin.empty()||!origin.is_absolute()||bytes.size()!=7620)invalid();
    std::vector<std::uint8_t> plain(bytes.begin(),bytes.end());if(digest(plain)!=decoded_sha256)invalid();
    if(std::find(plain.begin(),plain.end(),0)!=plain.end()||std::find(plain.begin(),plain.end(),'"')!=plain.end())invalid();
    std::vector<Line> lines;std::size_t begin=0;
    for(std::size_t i=0;i<plain.size();++i)if(plain[i]=='\n') {
        if(i==begin||plain[i-1]!='\r')invalid();
        lines.push_back({begin,i-begin+1});begin=i+1;
    }
    if(begin!=plain.size()||lines.size()!=145)invalid();
    const auto envelope=fields(text(plain,lines[0]));
    // Envelope source values, not a guessed native tokenizer configuration.
    if(envelope.size()!=5||number(envelope[1])!=1||number(envelope[2])!=26||number(envelope[4])!=120)invalid();
    std::vector<Record> records;records.reserve(120);
    for(std::size_t index=0;index<120;++index) {
        const auto line=lines[index+25];const auto value=text(plain,line);
        if(value.size()>=4096||value.find('\r')!=std::string_view::npos)invalid();
        auto columns=fields(value);if(columns.size()!=7)invalid();
        for(std::size_t i=0;i<5;++i)if(columns[i].size()>=380)invalid();
        // This label check qualifies this fixed original source only. Native
        //46382E addresses the current signedWORD ordinal, not column0.
        if(number(columns[0])!=static_cast<std::int32_t>(index)||columns[4].size()>=128)invalid();
        Record record;
        record.ordinal=static_cast<std::uint16_t>(index);
        record.source_word_was_empty=columns[1].empty();
        record.source_word_value=number(columns[1],true);
        record.word0=static_cast<std::uint16_t>(record.source_word_value);
        record.source_scale_value=number(columns[3]);
        record.filename=columns[4];
        record.source.source_record_index=index;record.source.source_line=index+26;record.source.source_offset=line.offset;
        record.source.raw_record.assign(plain.begin()+line.offset,plain.begin()+line.offset+line.size);
        for(std::size_t i=0;i<columns.size();++i)record.source.fields[i]=std::move(columns[i]);
        records.push_back(std::move(record));
    }
    std::vector<std::uint8_t> header(plain.begin(),plain.begin()+lines[25].offset);
    return std::shared_ptr<const TaiwanNativeDrvDoll>(new TaiwanNativeDrvDoll(
        std::move(origin),std::move(plain),std::move(header),std::move(records)));
}
const TaiwanNativeDrvDoll::Record* TaiwanNativeDrvDoll::find(std::uint16_t ordinal) const noexcept {
    if(ordinal>=records_.size())return nullptr;return &records_[ordinal];
}
TaiwanNativeDrvDoll::NativeRomRequest::NativeRomRequest(std::shared_ptr<const TaiwanNativeDrvDoll> bank,
        std::size_t ordinal,NativeRomContext context,TaiwanNativeResourceSelection::Request request)
    :bank_(std::move(bank)),ordinal_(ordinal),context_(std::move(context)),request_(std::move(request)){}
TaiwanNativeDrvDoll::ResolvedRom::ResolvedRom(std::shared_ptr<const NativeRomRequest> request,
        TaiwanNativeResourceSelection selected,std::shared_ptr<const TaiwanNativeRomAsset> rom,std::uint32_t action)
    :request_(std::move(request)),selected_(std::move(selected)),rom_(std::move(rom)),action_operand_(action){}
std::shared_ptr<const TaiwanNativeDrvDoll::NativeRomRequest> TaiwanNativeDrvDoll::native_rom_request(
        std::shared_ptr<const TaiwanNativeDrvDoll> bank,std::uint32_t ordinal,const NativeRomContext& context) {
    if(!bank||ordinal>=bank->records_.size())return {};
    const auto& source=bank->records_[ordinal];
    const auto printable=[](const auto& bytes){return std::all_of(bytes.begin(),bytes.end(),
        [](auto c){return c>=0x20&&c<0x7f;});};
    if(source.filename.empty()||source.filename.size()>=128||!printable(source.filename)||
       context.actual_52f550_root.empty()||context.actual_52f550_root.size()>=256||!printable(context.actual_52f550_root)||
       !context.actual_working_directory.is_absolute()||context.actual_manager_bank_operand>=512)return {};
    std::wstring root;for(const auto c:context.actual_52f550_root)root.push_back(static_cast<wchar_t>(c));
    const std::filesystem::path root_path(root);
    if(!root_path.has_root_name()||!root_path.has_root_directory())return {};
    const std::size_t separator=source.filename.front()=='\\'?0:1;
    if(source.filename.size()>=256-context.actual_52f550_root.size()-separator)return {};
    // Actual52F550: leading backslash uses5847F8 "%s%s"; otherwise585BC8
    // "%s\\%s". Preserve actual raw path/case/separators, no guessed dirname.
    auto reference=context.actual_52f550_root;
    if(source.filename.front()!='\\')reference.push_back('\\');
    reference.insert(reference.end(),source.filename.begin(),source.filename.end());
    if(reference.size()>=256)return {};
    //463B65 calls429820 directly: model+1C concatenation in44D520 does not
    // occur here. Allocator WORD operand is independent of this source ordinal.
    TaiwanNativeResourceSelection::Request request{TaiwanNativeResourceSelection::Kind::RomBinary,
        std::move(reference),{},context.actual_working_directory,context.actual_manager_bank_operand};
    const auto source_ordinal=source.ordinal;
    return std::shared_ptr<const NativeRomRequest>(new NativeRomRequest(std::move(bank),source_ordinal,context,std::move(request)));
}
std::shared_ptr<const TaiwanNativeDrvDoll::ResolvedRom> TaiwanNativeDrvDoll::bind_native_rom(
        std::shared_ptr<const NativeRomRequest> request,const TaiwanNativeResourceSelection& selected,
        std::shared_ptr<const TaiwanNativeRomAsset> rom,std::uint32_t action) {
    if(!request||!rom)return {};
    const auto& expected=request->request();const auto& actual=selected.request();
    if(expected.kind!=actual.kind||expected.original_reference!=actual.original_reference||
       expected.native_prefix!=actual.native_prefix||expected.actual_working_directory!=actual.actual_working_directory||
       expected.full_bank_operand!=actual.full_bank_operand)return {};
    // Retain an immutable VALUE before validation; a mutable public ROM object's
    // later reassignment must not change this private selection/action binding.
    auto owned=std::make_shared<const TaiwanNativeRomAsset>(*rom);
    if(owned->source()!=selected.actual_source()||owned->encoded_bytes()!=selected.encoded_bytes()||
       owned->images().empty()||!owned->find_action(action))return {};
    return std::shared_ptr<const ResolvedRom>(new ResolvedRom(std::move(request),selected,std::move(owned),action));
}
}
