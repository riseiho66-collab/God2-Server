#pragma once
#include "protocol/RecoveredWorldSkillRequest.h"
#include <algorithm>
#include <array>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <span>

namespace god2 {
// TW S2C C9 -> WORLD46B2C6/46B2CE ->4E72F0(logical+1).
// BATTLE519370/51982D also forwards logical+1 through its retained B+20
// owner to4E72F0; the selected Main initialization supplies that owner.
// This forwarding does not generate duration, periodic ticks or HP/MP amounts.
// Received role status/display data only; not C2S, a grant or a DoT rule.
struct RecoveredRoleSkillStatus {
    static constexpr std::uint8_t opcode=0xc9;
    static constexpr std::size_t logical_size=9;
    static constexpr bool runtime_emission_enabled=false;
    static constexpr bool runtime_mutation_enabled=false;
    static constexpr char image_sha256[]=
        "aaf0fae66e89c4547244304ecd8f4c2755746ffa6c9b9dfe68a0ff3fd2b4cd48";
    using Bytes=std::array<std::uint8_t,logical_size>;
    struct Countdown {
        std::int32_t remaining_ms;
        std::int32_t hours,minutes,seconds;
        // Native4E89AD tests milliseconds, not truncated seconds.
        bool text_visible() const noexcept {return remaining_ms>0;}
    };
    class Record {
    public:
        std::uint8_t mode_bits() const noexcept {return bytes_[1];}
        std::uint8_t definition_kind_byte() const noexcept {return bytes_[2];}
        std::uint8_t definition_id_byte() const noexcept {return bytes_[3];}
        std::uint8_t opaque4() const noexcept {return bytes_[4];}
        // Mode3 interprets this received DWORD as milliseconds. Other modes
        // retain raw bits without assigning a gameplay duration or magnitude.
        std::uint32_t received_value_bits() const noexcept {
            return std::uint32_t{bytes_[5]} | (std::uint32_t{bytes_[6]}<<8) |
                (std::uint32_t{bytes_[7]}<<16) | (std::uint32_t{bytes_[8]}<<24);
        }
        // Current4E8910 controls17..19 issue the SAME seven-byte C56 grammar
        // as497A90.4132E0 adds opcode to its six-byte body count. This source
        // requires entry mode2, copies WORD[[U+8688C]], definition kind/id,
        // and writes raw5=control-17. The sixth body byte remains unwritten.
        // Caller must bind the actual current entry/slot and control word.
        // Equality does not prove issued generation, ownership, a charge or
        // action authority. Do not compare or interpret the residual tail.
        bool matches_mode2_slot_action(const RecoveredWorldSkillRequest::Request& request,
                                       std::uint8_t native_slot,
                                       std::uint16_t current_control_word) const noexcept {
            return native_slot<3 && mode_bits()==2 &&
                request.raw_target()==current_control_word && request.raw5()==native_slot &&
                request.kind()==definition_kind_byte() &&
                request.definition_id()==definition_id_byte();
        }
        // Exact4E8910 selected countdown arithmetic. Caller supplies the local
        // timeGetTime origin stored on receipt and a sample in the same clock
        // domain. Neither input is a server epoch, turn count or skill owner.
        // Validity of the actual native three-slot entry is a caller obligation.
        std::optional<Countdown> countdown(std::uint32_t local_origin_ms,
                                           std::uint32_t local_now_ms) const noexcept {
            if(mode_bits()!=3)return std::nullopt;
            const std::uint32_t bits=local_origin_ms+received_value_bits()-local_now_ms;
            const auto signed_ms=bits<0x80000000u ? std::int64_t{bits}
                : std::int64_t{bits}-4294967296LL;
            const auto total_seconds=static_cast<std::int32_t>(signed_ms/1000);
            const auto total_minutes=total_seconds/60;
            return Countdown{static_cast<std::int32_t>(signed_ms),total_minutes/60,
                total_minutes%60,total_seconds%60};
        }
    private:
        friend struct RecoveredRoleSkillStatus;
        explicit Record(Bytes bytes) noexcept:bytes_(bytes){}
        Bytes bytes_;
    };
    // Format only. Preserve every mode, identity, duration bit pattern and the
    // opaque byte. No three-slot capacity, definition lookup or eligibility is
    // inferred from this parse, and expiry never clears state or applies HP.
    static std::optional<Record> parse_logical(std::span<const std::uint8_t> raw) noexcept {
        if(raw.size()!=logical_size || raw[0]!=opcode)return std::nullopt;
        Bytes bytes;
        std::copy(raw.begin(),raw.end(),bytes.begin());
        return Record(bytes);
    }
    static Bytes encode_logical(const Record& record) noexcept {return record.bytes_;}
};
}
