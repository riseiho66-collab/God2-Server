#pragma once
#include "cn/assets/CnNativeSkillBookBindings.h"
#include "db/NativeSkillBookSourceCatalog.h"
#include <functional>
#include <memory>
#include <thread>

namespace god2::cn {
// Actual pinned raw CN SKB -> exact same-store shared source row. This is not
// a learned grant, common item mapping, book custody or acquisition authority.
class CnSharedSkillBookSourceCatalog final {
public:
    using Books=CnNativeSkillBookBindings;
    using Reader=NativeSkillBookSourceCatalog;
    // Actual supplied store owner/lifetime, NOT a nonnull placeholder. Must
    // qualify this reader and Books' borrowed shared-skill reader as the same
    // actual live DB, current source/population policy and game-owner epoch.
    // Pure/non-yielding/non-reentrant; no sends/writes/pumping/retained borrowed
    // arguments. A resource SHA or native Current alone cannot supply DB Current.
    using StoreCurrent=std::function<bool(const Reader&,const std::shared_ptr<const void>&)>;
    struct Binding {Books::Book book;NativeSkillBookSourceRecord stored;};
    static std::shared_ptr<const CnSharedSkillBookSourceCatalog> bind_actual_shared_store(
        const Reader&,std::shared_ptr<const Books>,std::shared_ptr<const void> actual_store_lifetime,StoreCurrent);
    ~CnSharedSkillBookSourceCatalog();
    // Store qualification precedes every native/book or borrowed DB read.
    // Factory matches all386 expected item AND index rows; it does not COUNT
    // unrelated extra invalid rows or import/install missing data. Actual
    // StoreCurrent supplies the population/epoch policy. Mismatch has no fallback.
    bool current() const;
    std::optional<Binding> lookup_item(std::uint16_t) const;
    bool uses_native_books(const Books&) const; // Pointer identity only, no observers/SQL.
    bool uses_source_reader(const Reader&) const;
private:
    CnSharedSkillBookSourceCatalog(const Reader&,std::shared_ptr<const Books>,std::shared_ptr<const void>,StoreCurrent);
    struct Operation;
    void owner() const;
    bool observe() const;
    std::optional<Binding> retained_lookup(std::uint16_t) const;
    const Reader& reader_;
    const std::shared_ptr<const Books> books_;
    const std::shared_ptr<const void> lifetime_;
    const StoreCurrent store_current_;
    const std::thread::id thread_=std::this_thread::get_id();
    mutable bool busy_=false,terminal_=false;
};
}
