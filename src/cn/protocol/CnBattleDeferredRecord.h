#pragma once
#include "cn/protocol/CnBattleScalarUpdate.h"
#include "cn/protocol/CnBattleRoundBatch.h"
#include "cn/protocol/CnBattleCommandGate.h"
#include "cn/protocol/CnBattleSkillUpdate87.h"
#include <algorithm>
#include <cstdint>
#include <optional>
#include <span>
#include <utility>
#include <vector>

namespace god2cn {
// Retained native BATTLE queue records only. This is not a server queue, a
// battle event owner, or permission to emit packets before battle admission.
struct CnBattleDeferredRecord {
    static constexpr std::size_t native_logical_size(std::uint8_t opcode) noexcept {
        switch(opcode) {
        case 0x1c:return 45;case 0x38:return 2;
        case 0x83:case 0x84:return 15;case 0x85:return 2;
        case 0x86:return 17;case 0x87:return 3;
        case 0x88:return 121;case 0x89:return 57;
        default:return 0;
        }
    }
    class Record {
    public:
        std::uint8_t opcode() const noexcept {return bytes_[0];}
        //005488B0 breaks the current battle receive drain after queued89;
        // it does not imply a disconnect, battle result or final consumption.
        bool yields_native_receive_drain() const noexcept {return opcode()==0x89;}
        std::span<const std::uint8_t> logical_bytes() const noexcept {return bytes_;}
        // Narrow recovered86 subtype dispatch. Other queued86 subtypes remain
        // retained by this record and require their own native consumers.
        std::optional<CnBattleScalarUpdate::Record> scalar_update() const noexcept {
            return CnBattleScalarUpdate::parse_logical(bytes_);
        }
        std::optional<CnBattleRoundBatch::Record> round_batch() const noexcept {
            return CnBattleRoundBatch::parse_logical(bytes_);
        }
        std::optional<CnBattleCommandGate::Record> command_gate() const noexcept {
            return CnBattleCommandGate::parse_logical(bytes_);
        }
        // Actual deferred87 writes the selected primary/secondary list. The
        // complete rawWORD and flags remain source state, not cast rights.
        std::optional<CnBattleSkillUpdate87::Record> skill_update() const noexcept {
            return CnBattleSkillUpdate87::decode(bytes_);
        }
    private:
        friend struct CnBattleDeferredRecord;
        explicit Record(std::vector<std::uint8_t> bytes):bytes_(std::move(bytes)){}
        std::vector<std::uint8_t> bytes_;
    };
    static std::optional<Record> parse_logical(std::span<const std::uint8_t> bytes) {
        if(bytes.empty() || !native_logical_size(bytes[0]) || bytes.size()!=native_logical_size(bytes[0]))return std::nullopt;
        return Record(std::vector<std::uint8_t>(bytes.begin(),bytes.end()));
    }
};
static_assert(CnBattleDeferredRecord::native_logical_size(0x87)==CnBattleSkillUpdate87::logical_size);
}
