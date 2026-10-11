#pragma once
#include "cn/protocol/CnBattleSkillDefinition.h"
#include <algorithm>
#include <bit>
#include <cstddef>
#include <cstdint>
#include <functional>
#include <memory>
#include <optional>
#include <span>
#include <string>
#include <utility>
#include <vector>

namespace god2cn {
// CN582f 554750 writes actual catalog addresses into the two 549A70 lists.
// Supplied captured projections only; this reader does not access a process,
// create native addresses, issue a learned-skill grant, or infer server rights.
class CnBattleSkillSelection final {
public:
    static constexpr std::size_t component_size=0x351c;
    // 561BB0 consumes the file's four-byte header separately. Native memory
    // holds the remaining payload; file offset 8 maps to bank offset 4.
    static constexpr std::size_t bank_size=CnNativeSkillCatalog::resource_bytes-4;
    struct Buffer {std::uint32_t address;std::span<const std::uint8_t> bytes;};
    struct Input {Buffer component,bank,index,flags;};
    struct Scope {
        std::uint64_t actual_revision;
        std::uint32_t actual_battle_owner;
        std::string actual_client_sha256;
        CnNativeSkillCatalog::Source actual_catalog_source;
        bool operator==(const Scope&) const=default;
    };
    // Pure, nonyielding and nonreentrant actual owner qualification. It binds
    // the same complete native bank, battle/list/slot
    // and flag epoch against this exact catalog source. Raw equality alone
    // does not establish that lifecycle or the issuer of a supplied projection.
    using Current=std::function<bool(const Scope&)>;
    enum class Path {Primary,Secondary};
    struct Entry {
        std::uint16_t raw_word;
        std::uint32_t actual_record_address,file_offset;
        CnNativeSkillCatalog::Record definition;
        bool operator==(const Entry&) const=default;
    };
    class Snapshot final {
    public:
        const Scope& scope() const noexcept {return scope_;}
        Path selected_path() const noexcept {return path_;}
        std::uint8_t selector() const noexcept {return selector_;}
        std::int32_t raw_signed_index() const noexcept {return index_;}
        std::uint32_t raw_primary_flag() const noexcept {return word32(flags_,0);}
        std::uint32_t raw_secondary_flag() const noexcept {return word32(flags_,4);}
        std::span<const Entry> entries() const noexcept {return entries_;}
        const Entry& selected() const {return entries_.at(std::size_t(index_));}
        std::span<const std::uint8_t> component_bytes() const noexcept {return component_;}
        std::span<const std::uint8_t> bank_bytes() const noexcept {return bank_;}
        std::span<const std::uint8_t> index_bytes() const noexcept {return index_bytes_;}
        std::span<const std::uint8_t> flag_bytes() const noexcept {return flags_;}
        const std::shared_ptr<const CnNativeSkillCatalog>& catalog() const noexcept {return catalog_;}
        bool current() const {
            return current_ && current_(scope_) && catalog_ &&
                catalog_->source()==scope_.actual_catalog_source && catalog_->current() &&
                current_(scope_);
        }
    private:
        friend class CnBattleSkillSelection;
        Snapshot(Scope scope,const Input& input,
                 std::shared_ptr<const CnNativeSkillCatalog> catalog,Current current)
            :scope_(std::move(scope)),catalog_(std::move(catalog)),current_(std::move(current)),
             component_(input.component.bytes.begin(),input.component.bytes.end()),
             bank_(input.bank.bytes.begin(),input.bank.bytes.end()),
             index_bytes_(input.index.bytes.begin(),input.index.bytes.end()),
             flags_(input.flags.bytes.begin(),input.flags.bytes.end()){}
        Scope scope_;
        std::shared_ptr<const CnNativeSkillCatalog> catalog_;
        Current current_;
        std::vector<std::uint8_t> component_,bank_,index_bytes_,flags_;
        std::vector<Entry> entries_;
        Path path_=Path::Primary;
        std::uint8_t selector_=0;
        std::int32_t index_=0;
    };
    static std::shared_ptr<const Snapshot> read_actual_source(
        Scope scope,const Input& input,std::shared_ptr<const CnNativeSkillCatalog> catalog,
        Current current) {
        if(!current || !catalog || !scope.actual_battle_owner ||
           scope.actual_client_sha256!=CnNativeSkillCatalog::client_sha256 ||
           catalog->source()!=scope.actual_catalog_source || !current(scope) || !catalog->current() ||
           input.component.bytes.size()!=component_size || input.bank.bytes.size()!=bank_size ||
           input.index.bytes.size()!=4 || input.flags.bytes.size()!=8 ||
           !located(input.component,scope.actual_battle_owner,0xa89658) ||
           !located(input.bank,scope.actual_battle_owner,0x9d223c) ||
           !located(input.index,scope.actual_battle_owner,0xa8cbfc) ||
           !located(input.flags,scope.actual_battle_owner,0xa970f8) ||
           word32(input.component.bytes,0x3518)!=input.bank.address)return {};
        auto owned=std::shared_ptr<Snapshot>(new Snapshot(std::move(scope),input,std::move(catalog),std::move(current)));
        if(!owned->current())return {};
        owned->index_=std::bit_cast<std::int32_t>(word32(owned->index_bytes_,0));
        owned->path_=owned->raw_primary_flag()==0 && owned->raw_secondary_flag()!=0 ? Path::Secondary:Path::Primary;
        const bool primary=owned->path_==Path::Primary;
        owned->selector_=owned->component_[primary?4:0x2d10];
        if(owned->selector_>=(primary?16:3))return {};
        const std::size_t group=std::size_t(owned->selector_)*(primary?0x2d0:0x54);
        const auto count=std::bit_cast<std::int32_t>(word32(owned->component_,group+(primary?0x10:0x2d64)));
        // A qualified captured-layout domain, not a bound checked by 554750:
        // primary reserves 100 WORDs/pointers; secondary reserves ten.
        if(count<=0 || count>(primary?100:10) || owned->index_<0 || owned->index_>=count)return {};
        owned->entries_.reserve(std::size_t(count));
        for(std::size_t i=0;i<std::size_t(count);++i) {
            const auto raw=word16(owned->component_,group+(primary?0x14:0x2d14)+i*2);
            if(bool(raw&0x4000)==primary)return {};
            const auto kind=std::uint8_t((raw>>8)&0x3f),id=std::uint8_t(raw);
            auto record=owned->catalog_->lookup(kind,id);
            if(!record || record->source!=owned->scope_.actual_catalog_source ||
               record->file_offset<4 || !owned->current())return {};
            const std::size_t at=record->file_offset-4;
            if(at>owned->bank_.size() || record->raw.size()>owned->bank_.size()-at)return {};
            const auto address=word32(owned->component_,group+(primary?0xdc:0x2d28)+i*4);
            const auto expected=std::uint64_t(owned->scope_.actual_battle_owner)+0x9d223c+at;
            if(expected>UINT32_MAX || address!=expected ||
               !std::equal(record->raw.begin(),record->raw.end(),owned->bank_.begin()+at) ||
               !CnBattleSkillDefinition::from_record(*record))return {};
            owned->entries_.push_back({raw,address,record->file_offset,std::move(*record)});
        }
        if(!owned->current())return {};
        return owned;
    }
private:
    static bool located(const Buffer& b,std::uint32_t owner,std::uint32_t offset) noexcept {
        const auto at=std::uint64_t(owner)+offset;
        return at<=UINT32_MAX && b.address==at &&
            std::uint64_t(b.address)+b.bytes.size()<=std::uint64_t(UINT32_MAX)+1;
    }
    static std::uint16_t word16(std::span<const std::uint8_t> b,std::size_t at) noexcept {
        return std::uint16_t(b[at])|(std::uint16_t(b[at+1])<<8);
    }
    static std::uint32_t word32(std::span<const std::uint8_t> b,std::size_t at) noexcept {
        return std::uint32_t(b[at])|(std::uint32_t(b[at+1])<<8)|
            (std::uint32_t(b[at+2])<<16)|(std::uint32_t(b[at+3])<<24);
    }
};
}
