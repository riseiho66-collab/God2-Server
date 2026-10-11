#pragma once
#include <cstddef>
#include <cstdint>
#include <functional>
#include <memory>
#include <optional>
#include <span>
#include <string>
#include <thread>
#include <vector>

namespace god2cn {
// WORLD30 low absolute ID -> actual GOD resource key2800+ID -> column4.
// These are resource names, not common subject IDs, stats or carried skills.
class CnSubjectTemplateNames final {
public:
    static constexpr char client_sha256[]=
        "582f269535f86e95fcd77946821adf79a30d1bd33f21d566cf48c36fd221b3c8";
    static constexpr char encoded_sha256[]=
        "8a72d850a34b14170c4cb0e91da9430559ea7def4e047130c533d666d67b893a";
    static constexpr char decoded_sha256[]=
        "16f7bb0f9cdf2965719408204800b329269c810821b96d3d81b5feca168534a3";
    static constexpr std::size_t record_count=34;
    static constexpr std::size_t level_record_count=4; //GodLevel resource, not character progression cap.
    struct Source {
        std::uint64_t actual_revision;
        std::string actual_client_sha256;
        bool operator==(const Source&) const=default;
    };
    // Actual owner must invalidate this revision when the relevant source or
    // pointer-table meaning changes, including0042D540 replacement writes.
    // Invalidate BEFORE GodLevel reset/load/write begins (00428860/00428C80/
    // 0042CA20); its early-EOF return1 does not establish a complete new table.
    // Row reader00423480 also overwrites parser EAX with1 at004234D5;
    // actual column count remains resource+C. Reader success/379-byte scratch
    // capacity does not prove two columns or94-byte GodLevel slot copy bounds.
    // 004231B0 bank copy and004D5A10 selected-row copy terminate on NUL;
    // parser CRT count bounds do not supply destination capacities. Qualify
    // actual selected source columns/copy boundaries separately.
    // If observing native resource lifetime, invalidate before destructor
    // 00449940 ->member+464 ->00427350 ->00430340/00423020 starts. This does
    // not require process memory for an independent own-server catalog source.
    // File identity alone does not prove a live client's loaded table. No
    // process memory is required for our own configured source authority.
    using Current=std::function<bool(const Source&)>;
    struct Record {
        Source source;
        std::uint16_t resource_key;
        std::uint32_t source_line,decoded_offset;
        std::string record_sha256;
        std::vector<std::uint8_t> raw_line;
        std::string native_column4_cp936;
    };
    struct Lookup {
        Source source;
        std::uint16_t native_absolute_identifier,resource_key;
        std::optional<Record> actual_record;
        // Includes the actual C terminator. Missing pinned keys35..99 resolve
        // to the qualified native literal SPACE+NUL, never another name table.
        std::vector<std::uint8_t> native_name_with_nul;
    };
    struct LevelRecord {
        Source source;
        std::uint8_t native_zero_based_selector,native_csv_number;
        std::uint32_t source_line,decoded_offset;
        std::string record_sha256;
        std::vector<std::uint8_t> raw_line;
        std::string native_column0_cp936;
    };
    enum class LevelAction {CopyKnownSource,RetainExistingText,UnresolvedAcceptedString};
    struct LevelLookup {
        Source source;
        std::uint8_t native_packet_selector;
        std::int8_t native_header_count;
        LevelAction action;
        std::optional<LevelRecord> actual_record;
        std::vector<std::uint8_t> native_name_with_nul;
    };
    static std::shared_ptr<const CnSubjectTemplateNames> read_actual_source(
        Source,std::span<const std::uint8_t> encoded,std::span<const std::uint8_t> decoded,Current);
    bool current() const;
    // ID0 returns before lookup in native30; IDs>=100 use the packet string.
    std::optional<Lookup> lookup_absolute_identifier(std::uint16_t) const;
    //WORLD32 uses packet index directly; loader column1 positive number-1.
    //Pinned count4 accepts index4 beyond the four-row bank. Report UNKNOWN,
    //not a guessed empty string or a silently changed native < comparison.
    std::optional<LevelLookup> lookup_level_selector(std::uint8_t) const;
private:
    CnSubjectTemplateNames(Source,std::vector<Record>,std::vector<LevelRecord>,Current);
    void owner() const;
    Source source_;
    std::vector<Record> records_;
    std::vector<LevelRecord> levels_;
    Current current_;
    std::thread::id thread_=std::this_thread::get_id();
};
}
