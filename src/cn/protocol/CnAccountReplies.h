#pragma once
#include "cn/protocol/CnTransport.h"
#include <array>
#include <cstdint>

namespace god2cn {
// 00480650 native switch -> message.csvZ/SystemMessage. No synthetic success.
enum class CnAccountFailure : std::uint8_t {
    NotRegistered=0, AlreadyLoggedIn=1, Disabled=2, CredentialRejected=3,
    NetworkDisconnected=4, InvalidCharacter=5, VersionMismatch=6,
    BillingRestricted=7, ServerFull=9, NoServerOpen=0x11,
    PasswordMaintenance=0x12, CharacterNameTaken=0x13, TelephoneLock=0x1e,
    ServerMaintenance=0x20, ExternalAuthenticationRejected=0x21,
    RealNameRequired=0x22
};

struct CnAccountReplies {
    struct Group {
        std::uint8_t index;
        std::uint8_t billing_type;
        std::uint16_t enabled_servers;
    };
    struct Node {
        std::uint8_t server_index;
        std::uint8_t load;
        std::array<std::uint8_t,4> ipv4;
        std::uint16_t port;
    };
    // Exact S2C06 bytes. Byte0 is the native routing key; byte1/u16+2
    // also enter a character summary but their gameplay meaning is unresolved.
    // Supply authoritative native data; never fabricate a map/coordinate here.
    struct Location { std::array<std::uint8_t,4> raw; };
    struct CatalogNode { Node endpoint; std::vector<Location> locations; };
    struct CatalogGroup {
        Group header;
        // Slot count from the pinned client group configuration, not a count
        // derived from server_index or the 04 enable word.
        std::uint8_t configured_server_slots;
        std::vector<CatalogNode> nodes;
    };
    static Bytes failure(CnAccountFailure reason);
    // 0047FE30 consumes group first, then ordered node records and their
    // location records. These builders alone do not establish account success.
    static Bytes group(const Group& value);
    static Bytes node(const Node& value);
    static Bytes location(const Location& value);
    // Whole catalog is qualified/serialized before the caller queues frames.
    // Native 0047FE30 has a GROUP-wide node ordinal, not a per-server ordinal.
    // Preserves input order and record boundaries across transport aggregates.
    // This supplies directory bytes only: no 1D/0A, admission or live listener.
    static std::vector<Bytes> catalog(std::span<const CatalogGroup> groups);
};
}
