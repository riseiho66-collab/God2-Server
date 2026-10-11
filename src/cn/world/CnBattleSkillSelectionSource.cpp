#include "cn/world/CnBattleSkillSelectionSource.h"
#include <algorithm>
#include <exception>
#include <stdexcept>
#include <thread>
#include <utility>

namespace god2::cn {
namespace {
struct Identity final {};
bool matches(const CnBattleSkillSelectionSource::Native::Entry& native,const NativeSkillRecord& row) {
    // Shared lookup has already qualified its entire source/ordinal/hash/raw
    // against its real native catalog. Retain and compare that whole record.
    return row.source==CnSharedSkillCatalog::expected_source() &&
        row.kind==native.definition.kind && row.definition_id==native.definition.definition_id &&
        row.source_offset==native.file_offset && row.record_sha256==native.definition.record_sha256 &&
        row.raw_record.size()==native.definition.raw.size() &&
        std::equal(row.raw_record.begin(),row.raw_record.end(),native.definition.raw.begin());
}
}
struct CnBattleSkillSelectionSource::Storage {
    const std::shared_ptr<const Identity> identity;
    const Native::Snapshot native;
    const std::vector<Entry> entries;
    Storage(std::shared_ptr<const Identity> id,const Native::Snapshot& source,std::vector<Entry> records)
        :identity(std::move(id)),native(source),entries(std::move(records)) {}
};
struct CnBattleSkillSelectionSource::State {
    const std::thread::id thread=std::this_thread::get_id();
    const std::shared_ptr<const Identity> identity=std::make_shared<const Identity>();
    const std::shared_ptr<const CnSharedSkillCatalog> catalog;
    bool operating=false,terminal=false;
    explicit State(std::shared_ptr<const CnSharedSkillCatalog> c):catalog(std::move(c)) {}
    ~State(){if(thread!=std::this_thread::get_id())std::terminate();}
    void owner() const {
        if(thread!=std::this_thread::get_id())throw std::logic_error("CN battle skill selection game owner mismatch");
    }
    struct Operation {
        State& state;
        const int exceptions=std::uncaught_exceptions();
        explicit Operation(State& s):state(s) {
            state.owner();
            if(state.operating){state.terminal=true;throw std::logic_error("CN battle skill selection reentry rejected");}
            state.operating=true;
        }
        ~Operation(){if(std::uncaught_exceptions()>exceptions)state.terminal=true;state.operating=false;}
    };
    bool observed(const Native::Snapshot& native) const {
        // Real list/bank Current and actual native catalog Current must remain
        // true. This is a pure observer contract, not atomic process access.
        if(terminal || !native.current() || terminal)return false;
        if(!catalog->current() || terminal)return false;
        return native.current() && !terminal;
    }
    bool retained(const Storage& saved) const {
        if(terminal || saved.identity!=identity || saved.entries.size()!=saved.native.entries().size() ||
           !observed(saved.native))return false;
        for(std::size_t i=0;i<saved.entries.size();++i) {
            const auto& entry=saved.entries[i];
            if(entry.native!=saved.native.entries()[i] || !observed(saved.native))return false;
            auto actual=catalog->lookup(entry.native.definition.kind,entry.native.definition.definition_id);
            if(!actual || terminal || *actual!=entry.definition || !matches(entry.native,*actual) ||
               !observed(saved.native))return false;
        }
        return observed(saved.native);
    }
};
CnBattleSkillSelectionSource::Snapshot::Snapshot(std::shared_ptr<const Storage> s):storage_(std::move(s)) {}
const CnBattleSkillSelectionSource::Native::Snapshot& CnBattleSkillSelectionSource::Snapshot::native() const {
    if(!storage_)throw std::logic_error("CN skill selection empty snapshot");return storage_->native;
}
const std::vector<CnBattleSkillSelectionSource::Entry>& CnBattleSkillSelectionSource::Snapshot::entries() const {
    if(!storage_)throw std::logic_error("CN skill selection empty snapshot");return storage_->entries;
}
CnBattleSkillSelectionSource::CnBattleSkillSelectionSource(std::shared_ptr<State> state):state_(std::move(state)) {}
CnBattleSkillSelectionSource::~CnBattleSkillSelectionSource()=default;
std::shared_ptr<CnBattleSkillSelectionSource> CnBattleSkillSelectionSource::create(
    std::shared_ptr<const CnSharedSkillCatalog> catalog) {
    if(!catalog)return {};
    return std::shared_ptr<CnBattleSkillSelectionSource>(new CnBattleSkillSelectionSource(
        std::make_shared<State>(std::move(catalog))));
}
bool CnBattleSkillSelectionSource::owns_catalog(const std::shared_ptr<const CnSharedSkillCatalog>& catalog) const {
    state_->owner();return catalog && catalog==state_->catalog &&
        !catalog.owner_before(state_->catalog) && !state_->catalog.owner_before(catalog);
}
std::optional<CnBattleSkillSelectionSource::Snapshot> CnBattleSkillSelectionSource::resolve(const Native::Snapshot& supplied) {
    auto state=state_;State::Operation operation(*state);
    // Copy complete supplied source before any external observer, so callers
    // cannot mutate a borrowed holder through a caught callback.
    const Native::Snapshot native=supplied;
    if(!state->observed(native))return {};
    std::vector<Entry> records;records.reserve(native.entries().size());
    for(const auto& entry:native.entries()) {
        if(!state->observed(native))return {};
        auto actual=state->catalog->lookup(entry.definition.kind,entry.definition.definition_id);
        if(!actual || state->terminal || !matches(entry,*actual) || !state->observed(native))return {};
        records.push_back({entry,std::move(*actual)});
    }
    auto storage=std::make_shared<const Storage>(state->identity,native,std::move(records));
    if(!state->retained(*storage))return {};
    return Snapshot(std::move(storage));
}
bool CnBattleSkillSelectionSource::current(const Snapshot& supplied) {
    auto state=state_;State::Operation operation(*state);
    const auto saved=supplied.storage_;
    return saved && state->retained(*saved);
}
std::optional<CnBattleSkillSelectionSource::Entry> CnBattleSkillSelectionSource::selected(
    const Snapshot& supplied,std::uint32_t full_operand) {
    auto state=state_;State::Operation operation(*state);
    const auto saved=supplied.storage_;
    if(!saved || full_operand>0xffff || !state->retained(*saved))return {};
    const auto index=saved->native.raw_signed_index();
    if(index<0 || std::size_t(index)>=saved->entries.size())return {};
    const auto& entry=saved->entries[std::size_t(index)];
    if(entry.native!=saved->native.selected())return {};
    // Bit14 routes the captured list, bit15 remains raw writer state. Only
    // the definition's exact two original bytes match this full C35 operand.
    const auto key=std::uint32_t(entry.native.definition.definition_id)|
        (std::uint32_t(entry.native.definition.kind)<<8);
    if(key!=full_operand || !state->retained(*saved))return {};
    return entry;
}
}
