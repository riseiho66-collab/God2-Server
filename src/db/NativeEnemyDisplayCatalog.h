#pragma once

#include <cstdint>
#include <optional>
#include <span>
#include <string>
#include <vector>

struct sqlite3;

namespace god2 {
struct NativeEnemyDisplaySource {
    std::string dataset_id;
    std::string source_path;
    std::string source_sha256;
    std::string decoded_sha256;
    std::string native_image_sha256;
    std::string source_section;
    std::string loader_rva;
    std::string lookup_rva;
    std::int64_t row_count{};
    bool operator==(const NativeEnemyDisplaySource&) const = default;
};

// EnyName lookup identity only. No species, combat value, spawn or drop authority.
struct NativeEnemyDisplayRecord {
    NativeEnemyDisplaySource source;
    std::int64_t source_record_index{};
    std::int64_t source_line{};
    std::int64_t source_offset{};
    std::string record_sha256;
    std::vector<std::uint8_t> raw_record;
    std::int64_t area_generation{};
    std::int64_t area{};
    std::int64_t scene{};
    std::int64_t ordinal{};
    std::int64_t source_label{}; // Not a proven global monster ID.
    std::vector<std::uint8_t> name_bytes; // Raw current-client bytes, not normalized text.
    bool operator==(const NativeEnemyDisplayRecord&) const = default;
};

class NativeEnemyDisplayCatalog final {
public:
    static constexpr char current_dataset_id[] = "current-enyname-display-v1";
    // Length-prefixed source row followed by all 7,815 ordered catalog rows.
    // Generated only from import_native_enemy_display.pinned_rows/current source.
    static constexpr char current_catalog_sha256[] = "677c274ea71e917914455f5939564fe9080ea584dd3cabbb7d653648a6316e94";
    struct Counts {
        std::uint32_t records{},lookup_visible{},groups{};
        bool operator==(const Counts&) const = default;
    };
    struct Key {
        std::int64_t area{},scene{},ordinal{};
        bool operator==(const Key&) const = default;
    };
    struct References {
        std::optional<NativeEnemyDisplaySource> source;
        std::vector<NativeEnemyDisplayRecord> records;
        bool operator==(const References&) const = default;
    };
    // One complete source-qualified scene observation. Records preserve final
    // native lookup order and original occurrences, not a synthesized26B bank.
    struct Scene {
        NativeEnemyDisplaySource source;
        std::string catalog_sha256;
        std::int64_t area{},scene{};
        std::vector<NativeEnemyDisplayRecord> records;
        bool operator==(const Scene&) const = default;
    };
    explicit NativeEnemyDisplayCatalog(sqlite3* db);
    bool uses_connection(const sqlite3* db) const noexcept {return db_==db;}
    // Empty source+table -> zeros. Otherwise requires the complete pinned
    // source and all row bytes/metadata, including 24 superseded arena rows.
    // Intended for startup integrity qualification, not per-frame hashing.
    Counts counts() const;
    // Only final native-lookup-visible rows are returned. Missing -> nullopt;
    // malformed selectors, records or provenance throw DatabaseError.
    std::optional<NativeEnemyDisplayRecord> lookup(const std::string& dataset_id,
        std::int64_t area,std::int64_t scene,std::int64_t ordinal) const;
    // Same read snapshot first qualifies the complete pinned catalog, including
    // superseded rows. nullopt means no catalog loaded; an empty Scene means a
    // qualified catalog with no visible group at this exact selector. Callers
    // qualify any native BYTE/WORD projection; this API never truncates input.
    // Uses main tables and rejects temp shadows; existing lookup/counts keep
    // their original behavior. No spawn/stat/skill or2A issuer authority.
    std::optional<Scene> read_scene(std::int64_t area,std::int64_t scene) const;
    // Empty keys are unrequested, with no catalog/absence qualification. A
    // nonempty request hashes the complete pinned main catalog once, then
    // captures sorted unique visible keys. Missing catalog/keys throw.
    References read_references(std::span<const Key> keys) const;
private:
    Counts counts_for_source(bool main) const;
    std::optional<NativeEnemyDisplayRecord> lookup_for_source(const std::string& dataset_id,
        std::int64_t area,std::int64_t scene,std::int64_t ordinal,bool main) const;
    sqlite3* db_;
};
}
