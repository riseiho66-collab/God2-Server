#pragma once
#include "cn/assets/CnSharedSkillCatalog.h"
#include <array>
#include <functional>
#include <span>
#include <thread>

namespace god2::cn {
// Pinned CN SKB source -> native first matching item -> actual shared CN
// definition. Item/resource identity is not learned ownership, common skill
// identity, MP cost or a server rule. No client memory or native execution.
class CnNativeSkillBookBindings final {
public:
    static constexpr char client_sha256[] =
        "582f269535f86e95fcd77946821adf79a30d1bd33f21d566cf48c36fd221b3c8";
    static constexpr char encoded_sha256[] =
        "8a72d850a34b14170c4cb0e91da9430559ea7def4e047130c533d666d67b893a";
    static constexpr char decoded_sha256[] =
        "16f7bb0f9cdf2965719408204800b329269c810821b96d3d81b5feca168534a3";
    static constexpr char resource_path[] = "Data2/Patch/Comm/gamedata.csvZ";
    static constexpr std::size_t book_count=386;
    struct Source {
        std::uint64_t actual_revision;
        std::string actual_client_sha256;
        bool operator==(const Source&) const=default;
    };
    using Current=std::function<bool(const Source&)>;
    struct Book {
        Source source;
        std::uint32_t source_record_index,source_line,decoded_offset;
        std::uint16_t item_id;
        std::string record_sha256;
        std::vector<std::uint8_t> raw_line; // Includes actual CRLF.
        std::string native_alias; // Column26 -> parsed+11C, not localized name.
        std::array<std::string,3> opaque_tail_fields; // Raw27/28/29, last can be absent.
    };
    struct Binding {
        CnSharedSkillCatalog::Record definition;
        // No matching SKB is a valid result. It does not qualify the native
        // caller's existing out-item fallback or any server eligibility.
        std::optional<Book> matching_book;
        std::string native_selector;
        std::uint8_t native_compare_bytes;
    };
    // Supplied actual bytes are copied before hashing. The pinned pair is
    // already decoded input; this class never executes a native decoder.
    // All453 shared skill rows must already have a qualified actual provider.
    static std::shared_ptr<const CnNativeSkillBookBindings> read_actual_source(
        Source,std::span<const std::uint8_t> encoded,std::span<const std::uint8_t> decoded,
        std::shared_ptr<const CnSharedSkillCatalog>,Current);
    bool current() const;
    bool uses_shared_catalog(const CnSharedSkillCatalog&) const;
    // Exact pinned item -> owned SKB record only. The native skill-selector
    // lookup below is one-way and must not be inverted into learned rights,
    // common IDs or a kind/id grant from an alias string.
    std::optional<Book> lookup_item(std::uint16_t item_id) const;
    std::optional<Binding> lookup(std::uint8_t kind,std::uint8_t id) const;
    std::optional<std::vector<Binding>> lookup_words(std::span<const std::uint16_t>) const;
private:
    CnNativeSkillBookBindings(Source,std::vector<Book>,
        std::shared_ptr<const CnSharedSkillCatalog>,Current);
    void owner() const;
    std::optional<Binding> retained_lookup(std::uint8_t,std::uint8_t) const;
    Source source_;
    std::vector<Book> books_; // Ascending actual item ID, as native lookup.
    std::shared_ptr<const CnSharedSkillCatalog> skills_;
    Current current_;
    std::thread::id thread_=std::this_thread::get_id();
};
}
