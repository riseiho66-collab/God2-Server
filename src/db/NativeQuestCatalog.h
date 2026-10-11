#pragma once
#include <cstdint>
#include <array>
#include <optional>
#include <string>
#include <vector>
struct sqlite3;
namespace god2 {
// Source fields and display lookup only. None of these rows authorizes quest
// acceptance, transitions, rewards, resets or a Mission_data/ACTMIS/daily join.
struct NativeQuestSourceRecord {
    std::string source_path,source_sha256,decoded_sha256,record_sha256;
    std::int64_t source_line{};
    std::vector<std::uint8_t> raw_record;
    std::vector<std::vector<std::uint8_t>> fields;
    std::optional<std::vector<std::uint8_t>> field(std::size_t index) const {
        if(index>=fields.size())return std::nullopt;
        return fields[index]; // Empty is present; absent is not synthesized as 0.
    }
};
struct NativeQuestSourceCounts {
    std::int64_t definitions{},descriptions{},requirements{},daily{};
};
struct NativeDailyQuestDisplay {
    std::uint8_t ordinal{},index{},branch{};
    std::int64_t source_line{};
    std::array<std::uint8_t,316> logical{};
    std::uint16_t start_npc() const {return logical[2] | (std::uint16_t{logical[3]}<<8);}
    std::uint16_t end_npc() const {return logical[4] | (std::uint16_t{logical[5]}<<8);}
};
struct OwnedDailyQuestList {
    std::array<std::uint8_t,172> logical{};
    std::int64_t revision{};
    bool operator==(const OwnedDailyQuestList&) const = default;
};
class NativeQuestCatalog final {
public:
    explicit NativeQuestCatalog(sqlite3* db);
    NativeQuestSourceCounts counts() const;
    std::optional<NativeQuestSourceRecord> definition(std::uint16_t mission) const;
    std::optional<NativeQuestSourceRecord> description(std::uint16_t mission,std::uint16_t index) const;
    std::optional<NativeQuestSourceRecord> requirement_display(std::uint16_t serial) const;
    std::optional<NativeQuestSourceRecord> daily_source(std::uint8_t record_index) const;
    // Native 458430 scans source order for narrowed BYTE index/branch, first
    // match wins. This lookup never joins the pair to a journal mission ID.
    std::optional<NativeQuestSourceRecord> daily_lookup(std::uint8_t index,std::uint8_t branch) const;
    // Complete pinned native316 display catalog; includes bounded non-NUL
    // text blocks and source-order duplicate pairs. No availability rule.
    std::vector<NativeDailyQuestDisplay> daily_displays() const;
    // CUSTOM-0049: only an explicitly persisted owner-bound list is shown.
    // No list grants, native availability inference or teleport/reward rule.
    std::optional<OwnedDailyQuestList> owned_daily_list(std::int64_t account,std::int64_t character) const;
private:
    sqlite3* db_;
};
}
