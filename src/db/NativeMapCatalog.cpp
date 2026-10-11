#include "db/NativeMapCatalog.h"
#include "db/SqliteSupport.h"

#include <algorithm>
#include <limits>

namespace god2 {
namespace {
bool valid_text(const std::string& text) {
    return !text.empty() && text.find('\0') == std::string::npos;
}

std::string required_text(sqlite_detail::Statement& statement, int column) {
    auto text = statement.text(column);
    if (!valid_text(text)) throw DatabaseError("Invalid native map provenance text");
    return text;
}

std::string sha256_text(sqlite_detail::Statement& statement, int column) {
    auto text = statement.text(column);
    const auto hex = [](unsigned char value) {
        return (value >= '0' && value <= '9') || (value >= 'a' && value <= 'f');
    };
    if (text.size() != 64 || !std::all_of(text.begin(), text.end(), hex))
        throw DatabaseError("Invalid native map SHA-256 text");
    return text;
}
}

NativeMapCatalog::NativeMapCatalog(sqlite3* db) : db_(db) {
    if (!db_) throw DatabaseError("Null native map catalog connection");
}

std::optional<NativeMapRecord> NativeMapCatalog::lookup(
    const std::string& dataset_id, std::int64_t area, std::int64_t scene) const {
    if (!valid_text(dataset_id) ||
        dataset_id.size() > static_cast<std::size_t>(std::numeric_limits<int>::max()) ||
        area < 1 || area > 16 || scene < 0 || scene > 1023)
        throw DatabaseError("Invalid native map catalog selector");

    // One snapshot, with an outer join to expose orphaned catalog records.
    // Read at most two matches so a damaged uniqueness constraint cannot hide duplicates.
    sqlite_detail::Statement statement(db_,
        "SELECT c.dataset_id,c.source_record_index,c.source_line,c.record_sha256,"
        "c.raw_record,c.area,c.scene,c.kind,"
        "s.dataset_id,s.source_path,s.source_sha256,s.decoded_sha256,s.native_image_sha256,"
        "s.source_section,s.loader_rva,s.lookup_rva,s.row_count "
        "FROM native_map_catalog c LEFT JOIN native_data_sources s ON s.dataset_id=c.dataset_id "
        "WHERE c.dataset_id=? AND c.area=? AND c.scene=? LIMIT 2");
    statement.bind(1, dataset_id);
    statement.bind(2, area);
    statement.bind(3, scene);
    if (!statement.row()) return std::nullopt;

    if (required_text(statement, 0) != dataset_id)
        throw DatabaseError("Native map catalog dataset mismatch");
    NativeMapRecord result;
    result.source_record_index = statement.integer(1);
    result.source_line = statement.integer(2);
    result.record_sha256 = sha256_text(statement, 3);
    const auto raw = statement.blob(4, 1, 4095);
    result.raw_record.assign(raw.begin(), raw.end());
    result.area = statement.integer(5);
    result.scene = statement.integer(6);
    result.kind = statement.integer(7);
    if (result.source_record_index < 0 || result.source_record_index > 32766 || result.source_line < 1 ||
        result.area < 1 || result.area > 16 || result.scene < 0 || result.scene > 1023 ||
        result.kind < 0 || result.kind > 3 || result.area != area || result.scene != scene)
        throw DatabaseError("Invalid native map catalog record bounds");

    auto& source = result.source;
    source.dataset_id = required_text(statement, 8);
    source.source_path = required_text(statement, 9);
    source.source_sha256 = sha256_text(statement, 10);
    source.decoded_sha256 = sha256_text(statement, 11);
    source.native_image_sha256 = sha256_text(statement, 12);
    source.source_section = required_text(statement, 13);
    source.loader_rva = required_text(statement, 14);
    source.lookup_rva = required_text(statement, 15);
    source.row_count = statement.integer(16);
    if (source.dataset_id != dataset_id || source.row_count < 1 || source.row_count > 32767 ||
        result.source_record_index >= source.row_count)
        throw DatabaseError("Invalid native map catalog source");
    if (statement.row()) throw DatabaseError("Duplicate native map catalog lookup");
    return result;
}
}
