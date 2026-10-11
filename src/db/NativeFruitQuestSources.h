#pragma once
struct sqlite3;
namespace god2 {
// Immutable source/inference bundle qualification, not original server rules.
class NativeFruitQuestSources final {
public:
    static constexpr const char* bundle_sha256="ab3e063564d0e7b351c3abab9e3475419c3a710ec9371b3de4d9b01f44a76541";
    static constexpr const char* client_sha256="6bf75ef8ac1e0f6b2240800ff841d205788bd1b6512149584b5386b10f431e98";
    explicit NativeFruitQuestSources(sqlite3* db);
    static const char* schema() noexcept;
    bool populated() const; // empty=false; malformed/non-pinned throws.
    void require_qualified() const; // empty does not authorize gameplay.
private:
    sqlite3* db_;
};
}
