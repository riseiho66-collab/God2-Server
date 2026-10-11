#pragma once
#include "protocol/RecoveredBattlePlayerAppearance.h"
#include <array>
#include <charconv>
#include <cstdint>
#include <map>
#include <memory>
#include <optional>
#include <span>
#include <stdexcept>
#include <string>
#include <string_view>
#include <system_error>
#include <utility>
#include <vector>
#include <nlohmann/json.hpp>
#ifdef _WIN32
#ifndef NOMINMAX
#define NOMINMAX
#endif
#include <windows.h>
#include <bcrypt.h>
#endif

namespace god2 {
// Current149c Fight row/key semantics, with an independently hash-bound
// historical parsed-field data representation. NOT original decoded CSV,
// world->battle conversion, equipped-item/owner authority or renderer success.
class TaiwanNativeFightCatalog final {
public:
    static constexpr char audit_sha256[]="5500950022f789d1372f92fe2dd6ebee936c2e7f5a04b133c45151f3aabd142d";
    static constexpr char encoded_sha256[]="1195afeeb060d7d81c07e65476da8089d5ab72edea90971d72a07f20863338b8";
    // A claim retained in the historical audit, NOT independently decoded here.
    static constexpr char recorded_decoded_sha256[]="7cf2b923aff6f306115e04f9b680efe35724dfb8a78e71e61cdbf284ae976ace";
    static constexpr char current_image_sha256[]="149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763";
    static constexpr char audit_image_sha256[]="c5d8f79baa36879851703ac05d2b5caddf44a907677f7de114f568eeaf14f575";
    struct SourceRow {
        std::uint32_t record_index,line;
        std::string key;
        // Exact Unicode strings from the pinned JSON representation. These
        // normalized parsed fields are NOT original CP950/raw CSV bytes.
        std::array<std::string,7> historical_fields;
        std::uint8_t family_byte,derived_ordinal_byte;
        bool operator==(const SourceRow&)const=default;
    };
private:
    struct Storage {
        std::vector<std::uint8_t> audit_bytes;
        std::vector<SourceRow> rows;
        std::map<std::string,std::size_t,std::less<>> keys;
    };
public:
    class Selection {
    public:
        const RecoveredBattlePlayerAppearance::Bytes& input()const noexcept{return input_;}
        // Primary component order0,1,2,3. Component3 is also the family read;
        // component2 is also the component1-derived ordinal read.
        const SourceRow& row(std::size_t component)const{if(!source_)throw std::logic_error("Moved-from TW Fight selection");return source_->rows.at(indices_.at(component));}
        std::span<const std::uint8_t> historical_audit_bytes()const noexcept{return source_?std::span<const std::uint8_t>(source_->audit_bytes):std::span<const std::uint8_t>{};}
        bool operator==(const Selection& other)const noexcept{
            // Every constructible Storage is the same complete pinned input.
            return input_==other.input_&&indices_==other.indices_;
        }
    private:
        friend class TaiwanNativeFightCatalog;
        Selection(std::shared_ptr<const Storage> source,RecoveredBattlePlayerAppearance::Bytes input,
                  std::array<std::size_t,4> indices)
            :source_(std::move(source)),input_(input),indices_(indices){}
        std::shared_ptr<const Storage> source_;
        RecoveredBattlePlayerAppearance::Bytes input_;
        std::array<std::size_t,4> indices_;
    };
    // This parses a known archived JSON representation, NOT CSVZ/CSV/native.
    // Full byte pin precedes parsing; no caller-supplied digest/bool is trusted.
    static TaiwanNativeFightCatalog from_archive(std::span<const std::uint8_t> bytes){
        if(bytes.size()!=2853351)throw std::invalid_argument("TW Fight audit byte bound mismatch");
        auto storage=std::make_shared<Storage>();
        storage->audit_bytes.assign(bytes.begin(),bytes.end());
        if(digest(storage->audit_bytes)!=audit_sha256)
            throw std::invalid_argument("TW Fight audit full byte pin mismatch");
        const auto audit=nlohmann::json::parse(storage->audit_bytes.begin(),storage->audit_bytes.end());
        const auto& table=audit.at("resource_tables").at("HeroDoll_Fight.csvZ");
        if(audit.at("client_sha256")!=audit_image_sha256||table.at("sha256")!=encoded_sha256||
           table.at("decoded_sha256")!=recorded_decoded_sha256||table.at("count")!=3578||
           table.at("first_data_line")!=26||table.at("blank_data_lines")!=nlohmann::json::array({2852})||
           !table.at("keys_and_source_records").is_array()||table.at("keys_and_source_records").size()!=3578)
            throw std::invalid_argument("TW Fight archived representation identity mismatch");
        storage->rows.reserve(3578);
        for(const auto& item:table.at("keys_and_source_records")){
            const auto index=storage->rows.size();
            const auto line=static_cast<std::uint32_t>(26+index+(index>=2826?1:0));
            if(item.at("line")!=line||!item.at("fields").is_array()||item.at("fields").size()!=7)
                throw std::invalid_argument("TW Fight archived row shape/sequence mismatch");
            std::array<std::string,7> fields;
            for(std::size_t i=0;i<7;++i)fields[i]=item.at("fields").at(i).get<std::string>();
            // All current-consumed source fields must be exact ASCII; comments
            // are retained as Unicode parsed fields, without claiming raw CSV bytes.
            for(const auto i:{0u,1u,3u,4u,5u})if(!ascii(fields[i]))
                throw std::invalid_argument("TW Fight consumed source field is not ASCII");
            const auto key=item.at("key").get<std::string>();
            if(key.empty()||key!=fields[0]+fields[1]||fields[3].empty()||
               !storage->keys.emplace(key,index).second)
                throw std::invalid_argument("TW Fight missing/ambiguous archived resource key");
            // Current451BA0 %d -> signedINT;454D9C/454DB9 store AL. Empty
            // field5 is the qualified failed-number->0 case, not invented data.
            const auto family=number(fields[4],false),derived=number(fields[5],true);
            storage->rows.push_back(SourceRow{static_cast<std::uint32_t>(index),line,key,std::move(fields),
                static_cast<std::uint8_t>(family),static_cast<std::uint8_t>(derived)});
        }
        return TaiwanNativeFightCatalog(std::move(storage));
    }
    std::size_t size()const noexcept{return source_?source_->rows.size():0;}
    // Only complete already-supplied ordinary86/4 material. Position is actual
    // recipient-relative source; selecting rows grants no owner/game permission.
    std::optional<Selection> select(const RecoveredBattlePlayerAppearance::Record& record)const{
        if(!source_||!record.ordinary_mode1())return std::nullopt;
        const auto input=RecoveredBattlePlayerAppearance::encode(record);
        if(input[2]>=28)return std::nullopt;
        const auto side=std::uint8_t(input[2]/14);
        const auto lookup=[&](std::uint8_t family,std::uint8_t binary,std::uint8_t component,
                              std::uint8_t category,std::uint8_t ordinal)->std::optional<std::size_t>{
            const auto key=resource_key(side,family,binary,component,category,ordinal);
            const auto found=source_->keys.find(key);
            return found==source_->keys.end()?std::nullopt:std::optional(found->second);
        };
        const auto last=lookup(1,input[10]&15,3,input[10]>>4,input[11]&31);
        if(!last)return std::nullopt; // native missing-row epilogue is NOT a valid selection.
        const auto family=source_->rows[*last].family_byte;
        const auto first=lookup(family,input[4]&15,0,input[4]>>4,input[5]&31);
        const auto third=lookup(family,input[8]&15,2,input[8]>>4,input[9]&31);
        if(!first||!third)return std::nullopt;
        auto ordinal=source_->rows[*third].derived_ordinal_byte;
        if(ordinal>=2)ordinal=static_cast<std::uint8_t>(unsigned(ordinal)+(input[7]&31));
        const auto second=lookup(family,input[6]&15,1,input[6]>>4,ordinal);
        if(!second)return std::nullopt;
        return Selection(source_,input,{*first,*second,*third,*last});
    }
private:
    explicit TaiwanNativeFightCatalog(std::shared_ptr<const Storage> source):source_(std::move(source)){}
    std::shared_ptr<const Storage> source_;
    static bool ascii(std::string_view text)noexcept{
        for(const unsigned char c:text)if(!c||c>127)return false;
        return true;
    }
    static std::int32_t number(std::string_view text,bool empty_zero){
        if(text.empty()){
            if(empty_zero)return 0;
            throw std::invalid_argument("TW Fight missing numeric source field");
        }
        std::int32_t value;
        const auto parsed=std::from_chars(text.data(),text.data()+text.size(),value,10);
        if(parsed.ec!=std::errc{}||parsed.ptr!=text.data()+text.size())
            throw std::invalid_argument("TW Fight malformed/overflow numeric source field");
        return value;
    }
    static std::string resource_key(std::uint8_t side,std::uint8_t family,std::uint8_t binary,
                                    std::uint8_t component,std::uint8_t category,std::uint8_t ordinal){
        if(side>=2||component>=4)throw std::invalid_argument("TW Fight resource selector out of range");
        auto key="r"+std::to_string(unsigned(binary)+1);
        key+="15"[side];key+=std::to_string(family);key+="bfhw"[component];
        key+=std::to_string(category);if(ordinal<10)key+='0';key+=std::to_string(ordinal);
        return key;
    }
    static std::string digest(std::span<const std::uint8_t> bytes){
#ifdef _WIN32
        struct Handles{
            BCRYPT_ALG_HANDLE algorithm=nullptr;BCRYPT_HASH_HANDLE hash=nullptr;
            std::vector<std::uint8_t> object;
            ~Handles(){if(hash)BCryptDestroyHash(hash);if(algorithm)BCryptCloseAlgorithmProvider(algorithm,0);}
        } handles;
        if(!BCRYPT_SUCCESS(BCryptOpenAlgorithmProvider(&handles.algorithm,BCRYPT_SHA256_ALGORITHM,nullptr,0)))
            throw std::runtime_error("TW Fight SHA256 provider unavailable");
        DWORD size=0,returned=0;
        auto status=BCryptGetProperty(handles.algorithm,BCRYPT_OBJECT_LENGTH,reinterpret_cast<PUCHAR>(&size),sizeof(size),&returned,0);
        if(!BCRYPT_SUCCESS(status))throw std::runtime_error("TW Fight SHA256 object length failed");
        handles.object.resize(size);std::array<std::uint8_t,32> result{};
        status=BCryptCreateHash(handles.algorithm,&handles.hash,handles.object.data(),size,nullptr,0,0);
        if(BCRYPT_SUCCESS(status))status=BCryptHashData(handles.hash,const_cast<PUCHAR>(bytes.data()),static_cast<ULONG>(bytes.size()),0);
        if(BCRYPT_SUCCESS(status))status=BCryptFinishHash(handles.hash,result.data(),static_cast<ULONG>(result.size()),0);
        if(!BCRYPT_SUCCESS(status))throw std::runtime_error("TW Fight SHA256 failed");
        std::string out;out.reserve(64);
        for(const auto byte:result){out+="0123456789abcdef"[byte>>4];out+="0123456789abcdef"[byte&15];}return out;
#else
        (void)bytes;throw std::runtime_error("Qualified TW Fight SHA256 backend unavailable");
#endif
    }
};
}
