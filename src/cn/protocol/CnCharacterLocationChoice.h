#pragma once
#include <cstdint>
#include <optional>
#include <span>

namespace god2cn {
// C2S18 and S2C18 are different native records. No producer/consumer pairing
// by opcode equality. Ordinary17 explicitly sends18 after02 then waits18;
// qualified1B caller00448950 sends18 then1A without that ordinary18 waiter.
struct CnCharacterLocationChoice {
    // Wire value is raw. Ordinary UI producers add1 to Low8(UI+1612C),
    // but0043D610 forwards an explicit BYTE without that transformation.
    // Its upstream owner is unresolved; do not infer the ordinary choice
    // domain or permission from this producer primitive. Qualified ordinary
    // creation applies its real pending/permitted source before projection.
    struct Request {std::uint8_t raw_choice_byte;};
    struct Confirmation {
        std::uint8_t raw_slot_byte;
        std::uint8_t unresolved_payload_byte_1;
    };
    static std::optional<Request> read_request(std::span<const std::uint8_t> record) {
        // Exact native record only; no global server choice domain is proved.
        // Source: cn-creation-choice-producer-frontier-01. UI WORD and wire
        // BYTE are distinct; no clamp, modulo-table index or default choice.
        if(record.size()!=2 || record[0]!=0x18)return std::nullopt;
        return Request{record[1]};
    }
    static std::optional<Confirmation> read_confirmation(std::span<const std::uint8_t> record) {
        // Native length table18=3;0047DB70 copies only its first payloadBYTE.
        // The ordinary caller subsequently uses only its low3 bits in07.
        // The following byte remains opaque and cannot be synthesized as zero.
        if(record.size()!=3 || record[0]!=0x18)return std::nullopt;
        return Confirmation{record[1],record[2]};
    }
};
}
