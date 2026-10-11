#pragma once
#include <algorithm>
#include <array>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <span>
#include <vector>

namespace god2 {
// Native world S2C BE establishes a region of fifty 24-byte UI rows;
// S2C BF updates a slot of the last established region. This is a presentation
// contract only. No C2S BF purchase-to-reply relationship is established.
struct RecoveredBFPanel {
    static constexpr std::uint8_t list_opcode=0xbe, update_opcode=0xbf;
    static constexpr std::size_t row_size=24, update_size=29;
    static constexpr std::size_t region_count=6, slots_per_region=50;
    using Row=std::array<std::uint8_t,row_size>;
    struct List {
        std::uint8_t region{};
        std::vector<Row> rows;
        bool operator==(const List&) const=default;
    };
    struct Update {
        std::array<std::uint8_t,update_size> raw{};
        std::uint8_t region() const noexcept {return raw[1];}
        std::uint8_t slot() const noexcept {return raw[6];}
        bool operator==(const Update&) const=default;
    };
    static std::optional<List> decode_list(std::span<const std::uint8_t> bytes) {
        if(bytes.size()<5 || bytes[0]!=list_opcode ||
           (static_cast<std::size_t>(bytes[1]) | (static_cast<std::size_t>(bytes[2])<<8))!=bytes.size() ||
           bytes.size()!=5+row_size*static_cast<std::size_t>(bytes[3]))return {};
        List list{};list.region=bytes[4];list.rows.reserve(bytes[3]);
        for(std::size_t i=0;i<bytes[3];++i) {
            Row row{};std::copy_n(bytes.begin()+5+i*row_size,row_size,row.begin());
            list.rows.push_back(row);
        }
        return list;
    }
    static bool memory_index_bounded(const List& list) noexcept {
        if(list.region>=region_count || list.rows.size()>slots_per_region)return false;
        return std::all_of(list.rows.begin(),list.rows.end(),[](const Row& row){
            return row[1]<slots_per_region;
        });
    }
    static std::optional<std::vector<std::uint8_t>> encode_bounded_list(const List& list) {
        if(!memory_index_bounded(list))return {};
        const auto size=5+row_size*list.rows.size();
        std::vector<std::uint8_t> bytes{list_opcode,static_cast<std::uint8_t>(size),
            static_cast<std::uint8_t>(size>>8),static_cast<std::uint8_t>(list.rows.size()),list.region};
        bytes.reserve(size);
        for(const auto& row:list.rows)bytes.insert(bytes.end(),row.begin(),row.end());
        return bytes;
    }
    static std::optional<Update> decode_update(std::span<const std::uint8_t> bytes) noexcept {
        if(bytes.size()!=update_size || bytes[0]!=update_opcode)return {};
        Update value{};std::copy(bytes.begin(),bytes.end(),value.raw.begin());return value;
    }
    static bool memory_index_bounded(const Update& update) noexcept {
        return update.region()<region_count && update.slot()<slots_per_region;
    }
    static std::optional<std::array<std::uint8_t,update_size>> encode_bounded_update(
        const Update& update) noexcept {
        if(update.raw[0]!=update_opcode || !memory_index_bounded(update))return {};
        return update.raw;
    }
};
}
