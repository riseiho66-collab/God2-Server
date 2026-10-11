#pragma once

#include <cstdint>
#include <optional>
#include <string>
#include <vector>

struct sqlite3;

namespace god2 {
struct NativeSkillSource {
    std::string dataset_id;
    std::string source_path;
    std::string source_sha256;
    std::string decoded_sha256;
    std::string native_image_sha256;
    std::string source_section;
    std::string loader_rva;
    std::string lookup_rva;
    std::int64_t row_count = 0;

    bool operator==(const NativeSkillSource&) const = default;
};

struct NativeSkillRecord {
    NativeSkillSource source;
    std::int64_t source_record_index = 0;
    std::int64_t source_offset = 0;
    std::string record_sha256;
    std::vector<std::uint8_t> raw_record;
    std::int64_t kind = 0;
    std::int64_t definition_id = 0;

    // NATIVE_VERIFIED: current-client A9070/A90D0 reads raw WORD+0x42 for its MP eligibility
    // comparison. This is not an authoritative server charge or cast rule.
    std::uint16_t client_mp_threshold() const;

    bool operator==(const NativeSkillRecord&) const = default;
};

// Original definition identities/raw bytes and a verified client-only MP threshold.
class NativeSkillCatalog final {
public:
    static constexpr char current_dataset_id[] = "current-skill-catalog-v1";

    // The caller owns the connection and keeps it alive during every lookup.
    explicit NativeSkillCatalog(sqlite3* db);
    bool uses_connection(const sqlite3* db) const noexcept {return db_==db;}

    // Missing keys return nullopt. Invalid selectors, corrupt matched rows and
    // SQLite failures throw DatabaseError. Returned snapshots own all storage.
    std::optional<NativeSkillRecord> lookup(const std::string& dataset_id,
                                           std::int64_t kind,
                                           std::int64_t definition_id) const;
    // Explicit main-schema source for new owned observations. Uses the same
    // parser/metadata checks; original lookup resolution remains unchanged.
    // This does not attest source files, row digests or a native loaded catalog.
    std::optional<NativeSkillRecord> lookup_main(const std::string& dataset_id,
                                                std::int64_t kind,
                                                std::int64_t definition_id) const;

    // Explicit main row plus recomputed SHA-256 of all110 retained bytes.
    // Absence, digest mismatch or an unavailable digest provider returns null;
    // malformed database rows still throw. No full-file/loaded-image attestation.
    std::optional<NativeSkillRecord> lookup_main_digest_checked(
        const std::string& dataset_id, std::int64_t kind, std::int64_t definition_id) const;
    // Full main provenance observation, including for an empty issued model.
    // Sequential callers must reobserve it; this is not a cross-source CAS.
    std::optional<NativeSkillSource> lookup_main_source(const std::string& dataset_id) const;

private:
    std::optional<NativeSkillRecord> lookup_impl(const std::string&,std::int64_t,std::int64_t,bool main_schema) const;
    sqlite3* db_;
};
}
