#pragma once
#include <cstdint>
#include <optional>
#include <string>
#include <vector>
struct sqlite3;
namespace god2 {
// Historical SPI source text, normalized by the retained source inventory.
// The native token0 key, source ordinal and line are separate identities.
// No full396 output, inventory20 instance, common definition ID, acquisition,
// eligibility, current population or operation rule is supplied.
struct NativePetRoomSourceRecord {
    std::uint16_t native_key;
    std::uint32_t source_record_index,source_line,field_count;
    std::optional<std::uint32_t> decoded_offset;
    std::string record_sha256;
    std::vector<std::uint8_t> normalized_cp950_record;
    bool operator==(const NativePetRoomSourceRecord&) const=default;
};
class NativePetRoomSourceCatalog final {
public:
    static constexpr char dataset_id[]="tw149c-historical-spi-petroom-source-window-v1";
    static constexpr char authority[]="HISTORICAL_RAW_DEFINITION_ONLY";
    static constexpr char source_file[]="Data2/Patch/Comm/gamedata.csvZ";
    static constexpr char encoded_sha256[]="70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731";
    static constexpr char decoded_sha256[]="75c3c37947a64b0917fbf8e546884d9bf893fe6a606d3e2b8f3b1857966b1815";
    static constexpr char parser_image_sha256[]="149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763";
    static constexpr char catalog_sha256[]="8435556d891ba80780225c0ae07631d46d45e802a38b1e8a4ae1669df47b193b";
    explicit NativePetRoomSourceCatalog(sqlite3* db);
    // Explicit, atomic and idempotent source-data import into the caller's main
    // connection. Requires autocommit; a present corrupt dataset is never replaced.
    // Nothing invokes this from Main, Migration or a gameplay request.
    static void import_pinned_source(sqlite3* db);
    // Each read checks actual main tables and the whole envelope/all22 records
    // in a consistent scope with one joined data SELECT.
    // Missing schema or incomplete/orphan/corrupt data throws. Empty installed
    // tables return no observation; lookup6181/6182 is absent in this dataset.
    // A caller's transaction view is source data, not a committed action receipt.
    bool populated() const;
    std::optional<NativePetRoomSourceRecord> lookup(std::uint16_t native_key) const;
private:
    std::vector<NativePetRoomSourceRecord> read() const;
    sqlite3* db_;
};
}
