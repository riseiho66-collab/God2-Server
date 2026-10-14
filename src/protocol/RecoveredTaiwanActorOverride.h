#pragma once
#include <algorithm>
#include <array>
#include <cstdint>
#include <optional>
#include <span>

namespace god2 {
// Native TW149c world EA: exact length5, dispatcher46B492, remote4FC020,
// self503B00. Format/projection only: no status authority or emission owner.
struct RecoveredTaiwanActorOverride {
    static constexpr std::size_t logical_size=5;
    using LogicalRecord=std::array<std::uint8_t,logical_size>;
    class Record {
    public:
        std::uint16_t identity()const noexcept {
            return static_cast<std::uint16_t>(std::uint16_t{bytes_[1]}|
                (std::uint16_t{bytes_[2]}<<8));
        }
        std::uint8_t type()const noexcept{return bytes_[3];}
        std::uint8_t raw_index()const noexcept{return bytes_[4];}
        // The dispatch compares zero-extended FULL WORD to the full local
        // DWORD. Neither branch masks identity to a scene-handle width.
        bool is_self(std::uint32_t actual_local_identity)const noexcept {
            return identity()==actual_local_identity;
        }
        // Remote4FC020 stores byte subtraction modulo256, then resets values
        // above8 to0. This is an index0..8, never an enable/disable Boolean.
        // Self503B00 ignores this input and uses its distinct retained scalar.
        std::uint8_t remote_index()const noexcept {
            const auto raw=raw_index();
            return raw>=2&&raw<=9?static_cast<std::uint8_t>(raw-1):std::uint8_t{0};
        }
    private:
        friend struct RecoveredTaiwanActorOverride;
        explicit Record(const LogicalRecord& bytes)noexcept:bytes_(bytes){}
        LogicalRecord bytes_;
    };
    static std::optional<Record> parse_logical(std::span<const std::uint8_t> logical)noexcept {
        if(logical.size()!=logical_size||logical[0]!=0xea)return std::nullopt;
        LogicalRecord bytes;std::copy(logical.begin(),logical.end(),bytes.begin());
        return Record(bytes); // All raw byte values retained; no invented type restrictions.
    }
    static LogicalRecord encode_logical(const Record& record)noexcept {
        // The native remote consumer mutates its incoming index byte. Preserve
        // the ORIGINAL received record here, not that mutable scratch afterstate.
        return record.bytes_;
    }
};
}
