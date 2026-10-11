#pragma once
#include "db/NativeSkillCatalog.h"

namespace god2 {
// Shared raw source evidence, independent of the frozen TW396 parsed image.
// Dataset-qualified native items are neither common item identities nor learned
// ownership. Raw bytes/hashes retain their actual dataset's CRLF convention.
struct NativeSkillBookSourceRecord {
    NativeSkillSource source;
    std::int64_t source_record_index=0,source_line=0,decoded_offset=0,item_id=0;
    std::string record_sha256;
    std::vector<std::uint8_t> raw_record;
    bool operator==(const NativeSkillBookSourceRecord&) const=default;
};
class NativeSkillBookSourceCatalog final {
public:
    // Caller retains this same SQLite connection/store on the database/game
    // owner. Construction performs no reads, installs, imports or migration.
    explicit NativeSkillBookSourceCatalog(sqlite3*);
    // Explicit installer/import owner only; never a default migration or login
    // side effect. Existing native_data_sources is mandatory. No parsed image,
    // alias inversion, learned grant or version-specific gameplay table.
    static const char* schema_sql() noexcept;
    std::optional<NativeSkillBookSourceRecord> lookup(const std::string& dataset,std::int64_t item_id) const;
    std::optional<NativeSkillBookSourceRecord> lookup_by_index(const std::string& dataset,std::int64_t index) const;
private:
    std::optional<NativeSkillBookSourceRecord> read(const std::string&,std::int64_t,bool) const;
    sqlite3* db_;
};
}
