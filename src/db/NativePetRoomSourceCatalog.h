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
    // Supplemental decoded75c3 location proof for a returned lookup copy.
    // The original SQLv1 row/pin still stores an unknown offset; its catalog
    // fingerprint does not attest this supplemental location.
    std::optional<std::string> source_location_sha256{};
    bool operator==(const NativePetRoomSourceRecord&) const=default;
};
// Meaningful text from the common parser's +8/+2E/+54 C strings, without
// terminators or fabricated396 padding. This describes the historical source
// definitions only; it is not a current native-bank or player observation.
struct NativePetRoomDefinitionText {
    NativePetRoomSourceRecord source_record;
    std::vector<std::uint8_t> definition_name_cp950; // token4, record+8
    std::vector<std::uint8_t> caption_cp950;         // token7, record+2E
    std::vector<std::uint8_t> description_cp950;     // nonempty tokens8..12, LF between
};
// Conditional historical source-value projection of physical metadata fields.
// The required classification profile is not observed/satisfied by this API.
// These values are not current native-bank state or gameplay attributes.
struct NativePetRoomDefinitionScalars {
    static constexpr char qualification[]="CONDITIONAL_EXACT_INPUT_AND_STABLE_CLASSIFICATION";
    static constexpr char required_input[]=
        "Native conversion receives the exact normalized 1..5 ASCII digit field bytes "
        "in its ordinary flags0x49 string descriptor; original CRLF final-token "
        "line-reader behavior is not established";
    static constexpr char required_classification[]=
        "Valid stable table for -1..255 throughout native call: percent mask0x0008 clear; "
        "d mask0x0004 clear; ASCII digits mask0x0004 set and mask0x0008 clear; "
        "EOF masks0x0004/0x0008 clear";
    NativePetRoomSourceRecord source_record;
    std::uint32_t metadata_dword0,metadata_dword4; // tokens5/6
    std::uint16_t metadata_word114,metadata_word112; // tokens3/13, lowWORD
    std::uint8_t metadata_byte11A,metadata_byte11B_low4; // tokens14..25 low bits
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
    static constexpr char source_locations_sha256[]="e9c54a0f4dfac81fa630513d352574b9c888cf2b2cbc52dac147baf19191e8b7";
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
    // lookup enriches its returned copy with independently proven historical
    // decoded offset and supplemental fingerprint. StoredSQLv1 pins are unchanged.
    bool populated() const;
    std::optional<NativePetRoomSourceRecord> lookup(std::uint16_t native_key) const;
    // Validates the same complete dataset before projecting the exact source
    // text. The finite22 pins fit the native buffers; arbitrary native overflow,
    // numeric conversion, RomMaps lookup and full396 output are not modeled.
    std::optional<NativePetRoomDefinitionText> lookup_definition_text(std::uint16_t native_key) const;
    // Exact22 nonnegative ASCII-decimal source fields only. This is conditional
    // on required_classification; it is not a general sscanf implementation.
    std::optional<NativePetRoomDefinitionScalars> lookup_definition_scalars(std::uint16_t native_key) const;
private:
    std::vector<NativePetRoomSourceRecord> read() const;
    sqlite3* db_;
};
}
