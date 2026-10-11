#pragma once
#include <algorithm>
#include <array>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <span>
#include <vector>

namespace god2 {
// Current-native S2C EE/F3 fill the two UI row families that later produce
// C2S BF. This preserves only the observed wire and memory layout. It does
// not authorize a purchase, an owned item, or a causal BF response.
struct RecoveredBFSourceLists {
    static constexpr std::uint8_t even_opcode=0xee, odd_opcode=0xf3;
    static constexpr std::size_t header_size=9, small_row_size=6;
    // Destination arrays end before the next known UI fields.
    static constexpr std::size_t even_row_capacity=90, odd_row_capacity=106;
    static constexpr std::size_t odd_native_copy_capacity=0x800;
    using SmallRow=std::array<std::uint8_t,small_row_size>;

    struct Even {
        std::array<std::uint8_t,header_size> header{};
        std::vector<SmallRow> rows;
        bool operator==(const Even&) const=default;
    };
    struct Odd {
        std::array<std::uint8_t,header_size> header{};
        std::vector<std::vector<std::uint8_t>> first_rows;
        std::vector<SmallRow> middle_rows;
        std::vector<SmallRow> last_rows;
        bool operator==(const Odd&) const=default;
    };

    static std::uint16_t declared_size(std::span<const std::uint8_t> bytes) noexcept {
        return static_cast<std::uint16_t>(bytes[1] | (static_cast<std::uint16_t>(bytes[2])<<8));
    }
    static std::size_t row_count(std::span<const std::uint8_t> bytes) noexcept {
        return static_cast<std::size_t>(bytes[5])+bytes[6]+bytes[8];
    }

    static std::optional<Even> decode_even(std::span<const std::uint8_t> bytes) {
        if(bytes.size()<header_size || bytes[0]!=even_opcode ||
           declared_size(bytes)!=bytes.size() || bytes[7]<1 || bytes[7]>4 ||
           row_count(bytes)>even_row_capacity ||
           bytes.size()!=header_size+small_row_size*row_count(bytes))return {};
        Even out{};
        std::copy_n(bytes.begin(),header_size,out.header.begin());
        out.rows.reserve(row_count(bytes));
        for(std::size_t p=header_size;p<bytes.size();p+=small_row_size) {
            SmallRow row{};
            std::copy_n(bytes.begin()+p,small_row_size,row.begin());
            out.rows.push_back(row);
        }
        return out;
    }

    static std::optional<std::vector<std::uint8_t>> encode_even_bounded(const Even& value) {
        const auto counts=static_cast<std::size_t>(value.header[5])+value.header[6]+value.header[8];
        if(value.header[0]!=even_opcode || value.header[7]<1 || value.header[7]>4 ||
           counts!=value.rows.size() || counts>even_row_capacity)return {};
        const auto size=header_size+small_row_size*counts;
        std::vector<std::uint8_t> bytes(value.header.begin(),value.header.end());
        bytes[1]=static_cast<std::uint8_t>(size);
        bytes[2]=static_cast<std::uint8_t>(size>>8);
        bytes.reserve(size);
        for(const auto& row:value.rows)bytes.insert(bytes.end(),row.begin(),row.end());
        return bytes;
    }

    static std::optional<Odd> decode_odd(std::span<const std::uint8_t> bytes) {
        if(bytes.size()<header_size || bytes.size()>odd_native_copy_capacity ||
           bytes[0]!=odd_opcode || declared_size(bytes)!=bytes.size() ||
           bytes[7]<1 || bytes[7]>4 || row_count(bytes)>odd_row_capacity)return {};
        Odd out{};
        std::copy_n(bytes.begin(),header_size,out.header.begin());
        std::size_t p=header_size;
        for(std::size_t i=0;i<bytes[5];++i) {
            if(bytes.size()-p<8)return {};
            const auto n=static_cast<std::size_t>(bytes[p+4]);
            // The native 48-byte destination places n words at +8 and n
            // bytes at +34; n>14 writes past the destination row.
            if(n>14 || bytes.size()-p<8+3*n)return {};
            out.first_rows.emplace_back(bytes.begin()+p,bytes.begin()+p+8+3*n);
            p+=8+3*n;
        }
        for(std::size_t i=0;i<static_cast<std::size_t>(bytes[6])+bytes[8];++i) {
            if(bytes.size()-p<small_row_size)return {};
            SmallRow row{};
            std::copy_n(bytes.begin()+p,small_row_size,row.begin());
            (i<bytes[6]?out.middle_rows:out.last_rows).push_back(row);
            p+=small_row_size;
        }
        if(p!=bytes.size())return {};
        return out;
    }

    static std::optional<std::vector<std::uint8_t>> encode_odd_bounded(const Odd& value) {
        const auto total=value.first_rows.size()+value.middle_rows.size()+value.last_rows.size();
        if(value.header[0]!=odd_opcode || value.header[7]<1 || value.header[7]>4 ||
           value.first_rows.size()>255 || value.middle_rows.size()>255 ||
           value.last_rows.size()>255 || total>odd_row_capacity)return {};
        std::vector<std::uint8_t> bytes(value.header.begin(),value.header.end());
        bytes[5]=static_cast<std::uint8_t>(value.first_rows.size());
        bytes[6]=static_cast<std::uint8_t>(value.middle_rows.size());
        bytes[8]=static_cast<std::uint8_t>(value.last_rows.size());
        for(const auto& row:value.first_rows) {
            if(row.size()<8 || row[4]>14 || row.size()!=8+3*static_cast<std::size_t>(row[4]))return {};
            bytes.insert(bytes.end(),row.begin(),row.end());
        }
        for(const auto& row:value.middle_rows)bytes.insert(bytes.end(),row.begin(),row.end());
        for(const auto& row:value.last_rows)bytes.insert(bytes.end(),row.begin(),row.end());
        if(bytes.size()>odd_native_copy_capacity)return {};
        bytes[1]=static_cast<std::uint8_t>(bytes.size());
        bytes[2]=static_cast<std::uint8_t>(bytes.size()>>8);
        return bytes;
    }
};
}
