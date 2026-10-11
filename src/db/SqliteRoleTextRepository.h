#pragma once
#include "protocol/RecoveredRoleText.h"
#include <optional>
#include <functional>
#include <string>
struct sqlite3;

namespace god2 {
struct StoredRoleText {
    RecoveredRoleText::Text text{};
    std::string utf8;
    std::uint16_t codepage=950;
    std::uint64_t revision=0;
    bool operator==(const StoredRoleText&) const=default;
};

// CUSTOM-0056: owned durable secondary text and CAS are server storage policy.
// Native C2S20/S2C23 establish bytes/display only, not original persistence or
// moderation. This repository never changes the primary character name.
class SqliteRoleTextRepository {
    sqlite3* db_;
public:
    using Prepare=std::function<void(const StoredRoleText&)>;
    explicit SqliteRoleTextRepository(sqlite3* db);
    // Concrete backend identity only; no SQL, text write or source permission.
    bool uses_connection(const sqlite3* db)const noexcept{return db_==db;}
    static std::string schema();
    // Strict lossless projection for a different current client language.
    // Unrepresentable text or more than15 encoded bytes returns nullopt;
    // no substitution/truncation and no persisted value is changed.
    static std::optional<RecoveredRoleText::Text> project(const StoredRoleText& row,std::uint16_t output_codepage);
    std::optional<StoredRoleText> load(std::uint64_t account,std::uint64_t character);
    StoredRoleText save(std::uint64_t account,std::uint64_t character,
        std::optional<std::uint64_t> expected_revision,
        const RecoveredRoleText::Text& canonical_text,std::uint16_t codepage,const Prepare& prepare={});
};
}
