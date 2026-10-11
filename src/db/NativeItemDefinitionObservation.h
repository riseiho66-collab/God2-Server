#pragma once
#include <array>
#include <cstdint>
#include <string>
#include <utility>
#include <vector>

namespace god2 {
class SqliteOwnedInventoryRepository;
// Owned observation of the pinned historical full catalogs, whose parser image
// is149c. This is not a current-ROM re-extraction, common definition ID mapping,
// instance/acquisition, equipment entitlement, final ROM binding or stat rule.
class NativeItemDefinitionObservation final {
public:
    static constexpr const char* parser_image_sha256="149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763";
    static constexpr const char* encoded_source_sha256="70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731";
    static constexpr const char* decoded_source_sha256="75c3c37947a64b0917fbf8e546884d9bf893fe6a606d3e2b8f3b1857966b1815";
    struct Row {
        std::string family;
        std::uint16_t native_key;
        std::uint32_t source_record_index,source_line,decoded_offset;
        std::string record_sha256,parsed_sha256,catalog_sha256;
        std::vector<std::uint8_t> raw_cp950_record;
        std::array<std::uint8_t,396> metadata;
        bool operator==(const Row&) const=default;
    };
    const Row& row() const noexcept{return row_;}
    // The source key is separate. metadataDWORD0 is source token5, NOT the key.
    // 11A comes from tokens14..21 low bits; 11B low4 from22..25 low bits.
    // Keep the supplied high nibble/full396, never fabricate it from flags.
    std::uint8_t action_flags() const noexcept{return row_.metadata[0x11a];}
    std::uint8_t inventory_flags() const noexcept{return row_.metadata[0x11b];}
    bool client_equip_emission_flag() const noexcept{return (action_flags()&4)!=0;}
    bool client_3b_count_add_flag() const noexcept{return (inventory_flags()&1)!=0;}
    bool operator==(const NativeItemDefinitionObservation&) const=default;
private:
    friend class SqliteOwnedInventoryRepository;
    explicit NativeItemDefinitionObservation(Row row):row_(std::move(row)) {}
    Row row_;
};
}
