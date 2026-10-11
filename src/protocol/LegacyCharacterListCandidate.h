#pragma once
#include "protocol/RecoveredZeroSeedKey.h"
#include <array>
#include <cstddef>
#include <cstdint>

namespace god2 {
// UNVERIFIED candidate: historical logical layout, current zero-seed transform.
// No current-client acceptance evidence; explicit unverified loopback mode only.
// Source: C:/God2Evidence/classic-20260820/files/
// God2-Classic-Server-Formal-Handoff-20260820-020345/ServerSource/src/
// God2.ClassicServer.Protocol/OfficialServerSelectionWire.cs
// Source file SHA-256:
// 7D388D13BE3620EC1734DD4EEC4BC26666751994AFC0781C48295ED08C9EA2CA
// Members: EmptyCharacterResponseModel, EmptyCharacterOpaquePrefixHex,
// EmptyCharacterOpaqueSuffixHex, SerializeResponse, ComputeChecksum.
// Historical EXE SHA-256 (the source's "current-build" comments refer to this):
// 6B127086E0C00014DE26137B4EC482801E06E0724C5C05C64561D7F9FF32BD9B
// Current repo EXE SHA-256 (docs/CLIENT_REVERSE_NOTES.md):
// FB72296CAB5950B74D8F7C98155145F7C5F58749C3011ADB0540325B60749DD1
// Historical logical frame SHA-256:
// 1E087135069D6891DD725F8CF00FB41C591F829EDC1CEA0577CA6B4E36B09567
// Neither the historical fixed wire nor its key/0xAF feedback is reused.
// Static image SHA-256 (not runtime acceptance):
// 149C1B4510A2DEE85EB988D3F6C05785A69CBF50BB8FB751AF7D9814A5A6E763
// opcode07 handler RVA 0x148B9 copies frame[3..76] (74 bytes); the opcode
// length table gives 75 logical bytes + 3 envelope/checksum bytes = 78.
// frame[3] is a uint8 count; frame[4] contains flags (bit 0), NOT a LE16 count.
// Historical DecodeResponse interpreted [3..4] as LE16; EMPTY 00 00 agrees
// under both interpretations. Count 0 implies no active records/names.
// A6 function RVA 0x147D0 waits for 07: structural direction evidence only.
struct LegacyCharacterListCandidate {
    using Frame = std::array<std::uint8_t, 78>;

    static constexpr Frame decoded() {
        Frame frame{};
        frame[0] = 78; // [0..1]: little-endian total length; [2]: opcode.
        frame[2] = 0x07;
        // [3]: count 0; [4]: flags 0; [5..20]: empty historical first name.
        // [21..40]: historical opaque empty-slot tail, not field semantics.
        constexpr std::array<std::uint8_t, 20> tail{
            0x01, 0x02, 0x03, 0x00, 0x20, 0x00, 0x11, 0x14, 0x01, 0x60,
            0x01, 0x20, 0x01, 0x20, 0x81, 0x20, 0x04, 0x00, 0x03, 0x00,
        };
        for (std::size_t i = 0; i < tail.size(); ++i) frame[21 + i] = tail[i];
        // [41..76]: zero second slot, including name [41..56].
        // [77]: sum(frame[i] + 0x3C, i=0..76) modulo 256, including length.
        std::uint8_t checksum = 0;
        for (std::size_t i = 0; i < frame.size() - 1; ++i)
            checksum = static_cast<std::uint8_t>(checksum + frame[i] + 0x3c);
        frame.back() = checksum;
        return frame;
    }

    static constexpr Frame wire() {
        const auto plain = decoded();
        auto wire = plain;
        std::uint8_t previous = 0;
        for (std::size_t i = 2; i < wire.size(); ++i) {
            wire[i] = static_cast<std::uint8_t>(
                (plain[i] ^ recovered_zero_seed_key[i - 2]) + previous - 3);
            previous = plain[i];
        }
        return wire;
    }
};
}
