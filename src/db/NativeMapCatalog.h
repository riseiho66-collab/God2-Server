#pragma once

#include <cstdint>
#include <optional>
#include <string>
#include <vector>

struct sqlite3;

namespace god2 {
struct NativeMapSource {
    std::string dataset_id;
    std::string source_path;
    std::string source_sha256;
    std::string decoded_sha256;
    std::string native_image_sha256;
    std::string source_section;
    std::string loader_rva;
    std::string lookup_rva;
    std::int64_t row_count = 0;

    bool operator==(const NativeMapSource&) const = default;
};

struct NativeMapRecord {
    NativeMapSource source;
    std::int64_t source_record_index = 0;
    std::int64_t source_line = 0;
    std::string record_sha256;
    std::vector<std::uint8_t> raw_record;
    std::int64_t area = 0;
    std::int64_t scene = 0;
    std::int64_t kind = 0;

    bool operator==(const NativeMapRecord&) const = default;
};

// Read readiness only: raw records carry no spawn or gameplay interpretation.
class NativeMapCatalog final {
public:
    static constexpr char current_dataset_id[] = "current-map-catalog-v1";

    // The caller owns the connection and must keep it alive during every lookup.
    explicit NativeMapCatalog(sqlite3* db);

    // A missing key returns nullopt. Invalid input, corrupt matched data, and
    // SQLite failures throw DatabaseError. The returned record owns all bytes.
    std::optional<NativeMapRecord> lookup(const std::string& dataset_id,
                                         std::int64_t area,
                                         std::int64_t scene) const;

private:
    sqlite3* db_;
};
}
