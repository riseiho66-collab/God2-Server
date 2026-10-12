#pragma once
#include <cstdint>
#include <string>
#include <vector>
struct sqlite3;
namespace god2 {
// Exact historical RomMaps source text. The native token0 slot and physical
// source ordinal are separate fields even though both are0..56 in these pins.
// normalized_record preserves all5 raw CP950 fields, including both paths;
// token4 meaning, native converted ranges and current bank state are not supplied.
struct NativeRomMapSourceRecord {
    std::uint16_t slot_index;
    std::uint32_t source_record_index,source_line,decoded_offset;
    std::string record_sha256;
    std::vector<std::uint8_t> normalized_record;
    bool operator==(const NativeRomMapSourceRecord&) const=default;
};
class NativeRomMapSourceCatalog final {
public:
    static constexpr char dataset_id[]="tw149c-historical-rommaps-source-v1";
    static constexpr char authority[]="HISTORICAL_RAW_RESOURCE_SOURCE_ONLY";
    static constexpr char source_file[]="Data2/Patch/Comm/gamedata.csvZ";
    static constexpr char encoded_sha256[]="70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731";
    static constexpr char decoded_sha256[]="75c3c37947a64b0917fbf8e546884d9bf893fe6a606d3e2b8f3b1857966b1815";
    static constexpr char parser_image_sha256[]="149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763";
    static constexpr char catalog_sha256[]="99f0feabbc9fd0cddeeddaf6248fbac146e8b11f4a07cc1107cc3a4c71cb959b";
    explicit NativeRomMapSourceCatalog(sqlite3* db);
    // Reads actual main tables and validates the entire envelope/all57 exact
    // records in one joined snapshot. Empty installed tables return no records;
    // absent/partial schema or orphan/partial/corrupt source data throws.
    // Borrows a caller transaction; otherwise owns a read transaction.
    std::vector<NativeRomMapSourceRecord> records() const;
    // Explicit atomic, idempotent source import into the caller's main database.
    // Requires nonnull/autocommit, uses BEGIN IMMEDIATE, and never repairs or
    // replaces present corrupt data. No Main/Migration/gameplay caller is added.
    static void import_pinned_source(sqlite3* db);
private:
    sqlite3* db_;
};
}
