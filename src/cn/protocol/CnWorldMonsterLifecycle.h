#pragma once
#include <algorithm>
#include <array>
#include <cstdint>
#include <optional>
#include <span>

namespace god2cn {
// Primary CN582F WORLD74/78 use the SAME this-owner+1499FA0 as WORLD71.
// WORLD75/77 use +147C720 instead: no interchangeable actor namespace.
struct CnWorldMonsterRemove {
    static constexpr std::size_t logical_size=5;
    using LogicalRecord=std::array<std::uint8_t,logical_size>;
    class Record {
    public:
        std::uint16_t instance() const noexcept {return bytes_[1]|(std::uint16_t(bytes_[2])<<8);}
    private:
        friend struct CnWorldMonsterRemove;
        explicit Record(LogicalRecord bytes):bytes_(bytes){}
        LogicalRecord bytes_;
    };
    static std::optional<Record> parse_logical(std::span<const std::uint8_t> bytes) noexcept {
        if(bytes.size()!=logical_size || bytes[0]!=0x74)return std::nullopt;
        LogicalRecord retained;std::copy(bytes.begin(),bytes.end(),retained.begin());return Record(retained);
    }
    static LogicalRecord encode_logical(const Record& record) noexcept {return record.bytes_;}
    // Logical bytes3/4 are not consumed by this branch, and remain mandatory
    // full-source opaque bytes. Do not initialize them as invented zeros.
};
struct CnWorldMonsterLevel {
    static constexpr std::size_t logical_size=5;
    using LogicalRecord=std::array<std::uint8_t,logical_size>;
    enum class NativeLabel {Numeric,Band,Special};
    class Record {
    public:
        std::uint16_t instance() const noexcept {return word(1);}
        std::uint16_t supplied_level() const noexcept {return word(3);}
        std::uint8_t retained_level_byte() const noexcept {return bytes_[3];}
        NativeLabel label_kind() const noexcept {
            return supplied_level()<31?NativeLabel::Numeric:
                supplied_level()<100?NativeLabel::Band:NativeLabel::Special;
        }
        std::optional<std::uint8_t> band_slot() const noexcept {
            if(label_kind()!=NativeLabel::Band)return std::nullopt;
            return static_cast<std::uint8_t>((supplied_level()-30)/10);
        }
    private:
        friend struct CnWorldMonsterLevel;
        explicit Record(LogicalRecord bytes):bytes_(bytes){}
        std::uint16_t word(std::size_t at) const noexcept {return bytes_[at]|(std::uint16_t(bytes_[at+1])<<8);}
        LogicalRecord bytes_;
    };
    static std::optional<Record> parse_logical(std::span<const std::uint8_t> bytes) noexcept {
        if(bytes.size()!=logical_size || bytes[0]!=0x78)return std::nullopt;
        LogicalRecord retained;std::copy(bytes.begin(),bytes.end(),retained.begin());return Record(retained);
    }
    static LogicalRecord encode_logical(const Record& record) noexcept {return record.bytes_;}
    //004FB290 formats full WORD then retains only its low BYTE at entry+17B.
    // This is not a stat formula or proof of a server's true combat level.
};
}
