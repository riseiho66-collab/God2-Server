#pragma once
#include "db/NativeSkillCatalog.h"

#include <cstdint>
#include <optional>
#include <string>
#include <vector>

struct sqlite3;
namespace god2 {

// Source and original parsed bytes only. No learned ownership or gameplay rule.
struct NativeSkillBookRecord {
    NativeSkillSource source;
    std::int64_t source_record_index = 0;
    std::int64_t source_line = 0;
    std::int64_t decoded_offset = 0;
    std::int64_t kind = 0;
    std::int64_t definition_id = 0;
    std::int64_t item_id = 0;
    std::string record_sha256;
    std::vector<std::uint8_t> raw_record;
    std::string parsed_sha256;
    std::vector<std::uint8_t> parsed_record;
    bool operator==(const NativeSkillBookRecord&) const = default;
};

class NativeSkillBookCatalog final {
public:
    static constexpr char current_dataset_id[] = "current-skill-books-v1";
    explicit NativeSkillBookCatalog(sqlite3* db);
    bool uses_connection(const sqlite3* db) const noexcept {return db_==db;}
    // Unique forward association on the same actual source; no alias inversion
    // into native learning entitlement. Ambiguous source associations throw.
    std::optional<NativeSkillBookRecord> lookup_item(std::int64_t item_id) const;
    std::optional<NativeSkillBookRecord> lookup(std::int64_t kind,
                                                std::int64_t definition_id) const;
private:
    sqlite3* db_;
};
}
