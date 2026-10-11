#pragma once
#include "cn/protocol/CnWorldMonster.h"
#include <algorithm>
#include <array>
#include <cstdint>
#include <optional>
#include <string>

namespace god2cn {
// Current8A72/16F7 resource, native0042E010/00428500.
// Native calloc26 records, category replacement and group scan order.
// All keys remain presentation keys; names/row labels do not identify stats.
class CnCurrentEnemyDisplayCatalog {
public:
    static constexpr std::size_t ordered_source_rows=8076,active_rows=8052;
    struct Resource {
        std::uint64_t revision{};
        std::string client_sha256,encoded_sha256,decoded_sha256;
        std::uint32_t actual_loaded_record_count{},actual_special_record_count{};
    };
    struct Row {
        std::uint32_t key,source_index,source_line;
        std::array<std::uint8_t,26> native_record;
    };
    struct Appearance {
        Row base;
        std::uint8_t header,single_model_selector;
        std::array<std::uint8_t,16> name;
        std::optional<std::array<std::uint16_t,4>> components;
        bool override_invoked,override_applied;
        bool composite() const noexcept {return (header&1)!=0;}
        std::uint8_t pose_raw() const noexcept {return (header>>1)&7;}
        std::uint8_t color_selector_raw() const noexcept {return header>>4;}
    };
    static bool matches(const Resource& resource) noexcept {
        return resource.revision && resource.actual_loaded_record_count==ordered_source_rows &&
            resource.actual_special_record_count==1 &&
            resource.client_sha256=="582f269535f86e95fcd77946821adf79a30d1bd33f21d566cf48c36fd221b3c8" &&
            resource.encoded_sha256=="8a72d850a34b14170c4cb0e91da9430559ea7def4e047130c533d666d67b893a" &&
            resource.decoded_sha256=="16f7bb0f9cdf2965719408204800b329269c810821b96d3d81b5feca168534a3";
    }
    static const Row* lookup(const CnWorldMonster::Record& record) noexcept {
        if(record.catalog_category()>=17 || !record.catalog_ordinal())return nullptr;
        const std::uint32_t key=(std::uint32_t(record.catalog_category())<<23)|
            (std::uint32_t(record.catalog_group())<<13)|record.catalog_ordinal();
        const auto found=std::lower_bound(rows_.begin(),rows_.end(),key,
            [](const Row& row,std::uint32_t wanted){return row.key<wanted;});
        return found!=rows_.end() && found->key==key?&*found:nullptr;
    }
    static std::optional<Appearance> project(const CnWorldMonster::Record& record,const Resource& resource) {
        if(!matches(resource))return std::nullopt;
        const auto* row=lookup(record);if(!row)return std::nullopt;
        Appearance result{*row,row->native_record[0],row->native_record[1],{},std::nullopt,
            record.resource_override()!=0,record.resource_override()==1};
        std::copy_n(row->native_record.begin()+2,16,result.name.begin());
        if(result.override_applied) {
            // Current sole SpecialEnyInfo is IGS_SPECIAL, single selector149,
            // pose1. 00430A50 retains BASE HIGH nibble and16-byte base name.
            // Special table uses malloc; untouched bytes18..25 are UNKNOWN.
            // No fabricated full26-byte override record is produced here.
            result.header=static_cast<std::uint8_t>((result.header&0xf0)|2);
            result.single_model_selector=149;
        }else if(result.composite()) {
            std::array<std::uint16_t,4> parts;
            for(unsigned n=0;n<4;++n)parts[n]=static_cast<std::uint16_t>(
                row->native_record[18+n*2]|(std::uint16_t(row->native_record[19+n*2])<<8));
            result.components=parts; // Native order body,face,head,weapon.
        }
        return result;
    }
private:
    inline static constexpr std::array<Row,active_rows> rows_={{
#include "cn/assets/CnCurrentEnemyDisplayRows.inc"
    }};
};
}
