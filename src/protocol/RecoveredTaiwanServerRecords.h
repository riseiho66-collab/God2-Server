#pragma once
#include "protocol/RecoveredWorldFrame.h"
#include <array>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <span>
#include <vector>

namespace god2 {
// TW S2C logical record boundaries from the pinned mapped native image
// 149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763.
// 4134C8 -> 415840 -> 401000 -> 401200 selects the 401324 length table.
// A -2 leaf uses the unsigned little-endian WORD at record+1 as TOTAL size:
// 4134EE..413528 reads the three header bytes; 41354B rejects size >=0xA00;
// 413558..413590 reads up to that total. 413670 resets the consumed record.
// This parser preserves every opaque byte; framing grants no gameplay/state
// authority and does not qualify which opcode is legal in a particular phase.
struct RecoveredTaiwanServerRecords {
    struct Record {
        std::uint8_t opcode;
        std::size_t offset;
        // Borrowed view into the caller's complete unchanged logical buffer.
        // The caller must retain that buffer while using these records.
        std::span<const std::uint8_t> bytes;
    };

    // Existing aggregate transport cap, distinct from the native single
    // variable record's exclusive limit below. No envelope is decoded here.
    static constexpr std::size_t max_logical_size=RecoveredWorldFrame::max_logical_size;
    static constexpr std::size_t variable_record_limit_exclusive=0xA00;
    // Explicit server allocation cap for a complete ordered initial aggregate,
    // not a native record-size limit or a guarantee of packed frame count.
    static constexpr std::size_t max_aggregate_logical_size=max_logical_size*256;

    static std::optional<std::vector<Record>> read(std::span<const std::uint8_t> logical) {
        return read_bounded(logical,max_logical_size);
    }
    static std::optional<std::vector<Record>> read_aggregate(std::span<const std::uint8_t> logical) {
        return read_bounded(logical,max_aggregate_logical_size);
    }

private:
    static std::optional<std::vector<Record>> read_bounded(std::span<const std::uint8_t> logical,
            std::size_t allocation_limit) {
        if(logical.empty() || logical.size()>allocation_limit)return std::nullopt;
        std::vector<Record> records;
        // The smallest recovered fixed record is two bytes; variable records
        // require all three header bytes. This is only an allocation bound.
        records.reserve(logical.size()/2);
        for(std::size_t offset=0;offset<logical.size();) {
            const auto remaining=logical.subspan(offset);
            const auto opcode=remaining.front();
            const auto recovered=native_lengths[opcode];
            std::size_t length;
            if(recovered==-2) {
                if(remaining.size()<3)return std::nullopt;
                length=static_cast<std::size_t>(remaining[1]) |
                       (static_cast<std::size_t>(remaining[2])<<8);
                // Native malformed total0..2 early-finishes after consuming
                // three bytes (413558). Explicitly reject that malformed
                // input rather than emulate its inconsistent boundary.
                if(length<3 || length>=variable_record_limit_exclusive)return std::nullopt;
            } else {
                if(recovered<=0)return std::nullopt; // 21/25/FE/FF unsupported.
                length=static_cast<std::size_t>(recovered);
            }
            // Subtraction-relative bound ensures offset+length cannot overflow
            // and makes forward progress explicit; no unknown record is skipped.
            if(length==0 || length>remaining.size())return std::nullopt;
            records.push_back(Record{opcode,offset,remaining.first(length)});
            offset+=length;
        }
        return records;
    }

    // Exact 00..FD pointer leaves plus the native >FD unsupported branch.
    // Positive values include opcode; -2 means total WORD; -1 unsupported.
    inline static constexpr std::array<std::int16_t,256> native_lengths{{
        /*00*/3,2,23,3,5,9,5,75,65,5,17,33,389,21,9,37,
        /*10*/37,5,8,527,9,13,9,25,3,-2,4,3,45,173,2,125,
        /*20*/-2,-1,25,17,17,-1,11,5,3,9,37,21,61,17,5,5,
        /*30*/19,29,2,2,4,4,11,11,2,17,5,25,5,3,17,3,
        /*40*/17,5,3,29,25,7,13,9,29,5,5,3,17,9,19,3,
        /*50*/25,9,3,3,29,25,7,19,21,9,9,9,-2,2,13,21,
        /*60*/21,9,3,-2,45,-2,2,9,13,7,5,21,27,29,5,81,
        /*70*/9,21,21,5,5,5,5,7,5,9,-2,41,29,25,25,17,
        /*80*/25,261,9,15,15,2,17,3,121,57,45,2,2,5,53,25,
        /*90*/13,22,2,3,3,25,5,3,-2,3,2,2,49,7,205,17,
        /*A0*/3,2,-2,3,5,21,18,-2,3,27,5,-2,3,3,25,-2,
        /*B0*/-2,9,5,3,5,-2,45,9,29,9,3,3,5,5,-2,29,
        /*C0*/9,41,3,13,61,309,7,5,2,9,9,3,-2,65,11,177,
        /*D0*/7,21,21,25,9,9,13,2,-2,2,15,13,-2,-2,2,3,
        /*E0*/3,13,25,53,17,9,13,2,2,2,5,5,19,21,-2,3,
        /*F0*/29,5,1161,-2,5,29,29,1025,125,2105,5,73,-2,-2,-1,-1
    }};
};
}
