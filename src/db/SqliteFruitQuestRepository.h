#pragma once
#include "game/InferredQuestRules.h"
#include "game/RecoveredPosition.h"
#include "db/SqliteQuestJournalRepository.h"
#include <functional>
struct sqlite3;
namespace god2 {
// CUSTOM-0051: inferred, once-only fruit collection persistence. No native
// acceptance/reward authority is claimed. No DB writes are performed by load.
class SqliteFruitQuestRepository final {
public:
    struct Overlay {
        InferredQuestRules::Instance logical{};
        std::uint64_t revision{};
        std::string origin,provenance,source_sha256,client_sha256,design_id;
        bool operator==(const Overlay&) const = default;
    };
    struct Receipt {
        std::uint64_t experience_before{},experience_after{},experience_delta{};
        std::uint64_t reputation_before{},reputation_after{},reputation_delta{};
        bool experience_was_present{};
        std::string token,bundle_sha256;
        bool operator==(const Receipt&) const = default;
    };
    struct View {
        std::uint32_t mission{};
        InferredQuestRules::Snapshot snapshot;
        std::optional<std::array<std::uint8_t,25>> role_logical;
        std::uint64_t role_revision{};
        bool experience_present{},balance_present{};
        std::optional<RecoveredPosition> position;
        std::optional<QuestJournalSnapshot> journal;
        std::array<std::optional<Overlay>,30> overlays;
        std::map<std::uint32_t,Receipt> receipts;
        bool operator==(const View&) const = default;
    };
    struct BagChange {
        std::uint8_t slot{};
        InferredQuestRules::Slot before,after;
    };
    struct Commit {
        View before,after;
        std::vector<std::uint8_t> journal_logical;
        std::vector<BagChange> changed_bags;
        std::uint64_t experience_delta{},reputation_delta{};
    };
    // Mandatory startup/current source qualification for the three MIS/MAT01
    // items. The existing DB has no general material catalog. Read-only callback
    // must throw unless the pinned FruitVillage source bundle is qualified.
    using SourceGuard=std::function<void()>;
    using Prepare=std::function<void(const Commit&)>;
    explicit SqliteFruitQuestRepository(sqlite3* db,SourceGuard source_guard);
    static const char* schema() noexcept;
    View load(std::uint64_t account,std::uint64_t character,std::uint32_t mission);
    Commit accept(std::uint64_t account,std::uint64_t character,std::uint32_t mission,
                  const View& expected,const Prepare& prepare={});
    Commit submit(std::uint64_t account,std::uint64_t character,std::uint32_t mission,
                  const View& expected,const Prepare& prepare={});
private:
    View read(std::uint64_t account,std::uint64_t character,std::uint32_t mission);
    std::array<std::uint16_t,418> source_counts();
    Commit mutate(InferredQuestRules::Action action,std::uint64_t account,std::uint64_t character,
                  std::uint32_t mission,const View& expected,const Prepare& prepare);
    sqlite3* db_;
    SourceGuard source_guard_;
};
}
