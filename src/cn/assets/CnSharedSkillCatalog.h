#pragma once
#include "cn/assets/CnNativeSkillCatalog.h"
#include "db/NativeSkillCatalog.h"
#include <functional>
#include <thread>

namespace god2::cn {
// One existing native_skill_catalog/native_data_sources store. CN uses its
// pinned dataset selector; never falls back to the TW current_dataset_id.
// This qualifies definition provenance, not a shared gameplay-skill identity.
// Existing TW-only NativeSkillRecord field accessors do not qualify CN rules.
class CnSharedSkillCatalog final {
public:
    using Native=god2cn::CnNativeSkillCatalog;
    using Record=god2::NativeSkillRecord;
    // Actual same store/reader lifetime and population/epoch qualification,
    // before every native callback or borrowed SQL read. A nonnull marker or
    // immutable resource revision is not a DB lifetime. No writes/yields or
    // reentry; the supplied strong owner must keep this actual reader alive.
    using StoreCurrent=std::function<bool(const NativeSkillCatalog&,const Native&,
        const std::shared_ptr<const void>&)>;
    // Exact metadata for a later explicit import into the EXISTING tables.
    // Source-section/RVA strings are provenance annotations, not wire fields.
    static NativeSkillSource expected_source();
    // Caller keeps this same shared DB reader/connection alive; all calls on
    // its game owner. Both provider and all453 actual rows must be available.
    // Reads only; does not create a schema, import rows or grant learned skills.
    static std::shared_ptr<const CnSharedSkillCatalog> bind_actual_shared_store(
        const NativeSkillCatalog&,std::shared_ptr<const Native>,
        std::shared_ptr<const void> actual_store_lifetime,StoreCurrent);
    ~CnSharedSkillCatalog();
    bool current() const;
    std::optional<Record> lookup(std::uint8_t kind,std::uint8_t id) const;
    // Actual private native/source qualification first; same common resolver
    // then supplies owning definition metadata. Original lookups stay exact.
    std::optional<SharedSkillLookup> lookup_shared(std::uint8_t kind,std::uint8_t id) const;
    std::optional<std::vector<Record>> lookup_words(std::span<const std::uint16_t>) const;
private:
    CnSharedSkillCatalog(const NativeSkillCatalog&,std::shared_ptr<const Native>,
        std::shared_ptr<const void>,StoreCurrent);
    struct Operation;
    void owner() const;
    bool observe() const;
    std::optional<Record> retained_lookup(std::uint8_t,std::uint8_t) const;
    const NativeSkillCatalog& shared_;
    std::shared_ptr<const Native> native_;
    std::shared_ptr<const void> actual_store_lifetime_;
    StoreCurrent store_current_;
    std::thread::id thread_=std::this_thread::get_id();
    mutable bool operating_=false,terminal_=false;
};
}
