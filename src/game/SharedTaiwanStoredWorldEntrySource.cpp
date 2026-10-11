#include "game/SharedTaiwanStoredWorldEntrySource.h"
#include "protocol/RecoveredWorldEntryView.h"
#include <algorithm>
#include <memory>
#include <stdexcept>
#include <thread>
#include <utility>

namespace god2 {
namespace {
using Source=SharedTaiwanStoredWorldEntrySource;
bool same_scope(const Source::Scope& a,const Source::Scope& b) {
    return a.session==b.session && a.account==b.account && a.character==b.character &&
        a.position==b.position && a.map==b.map && a.selection==b.selection &&
        Source::Snapshot::same_root(a.selected,b.selected);
}
struct State {
    NativeWorldEntrySnapshotRepository& storage;
    RecoveredCharacterRepository& characters;
    const NativeMapCatalog& maps;
    const std::string client;
    Source::Qualify qualify;
    const std::thread::id thread=std::this_thread::get_id();
    bool active=false,reentered=false;
    struct Lease {
        State& state;
        explicit Lease(State& value):state(value) {
            if(std::this_thread::get_id()!=state.thread)throw std::logic_error("TW stored entry owner mismatch");
            if(state.active) {state.reentered=true;throw std::logic_error("TW stored entry reentered");}
            state.active=true;state.reentered=false;
        }
        ~Lease(){state.active=false;state.reentered=false;}
    };
    bool common_current(const Source::Scope& scope) {
        if(!storage.owns_characters(characters) || !scope.session || !scope.account || !scope.character ||
           scope.selected.account_id!=scope.account || scope.selected.id!=scope.character)return false;
        std::size_t found=0;
        for(const auto& root:characters.list_for_account(scope.account))if(root.id==scope.character) {
            if(!Source::Snapshot::same_root(root,scope.selected))return false;
            ++found;
        }
        const auto saved=characters.load_position(scope.account,scope.character);
        const auto map=maps.lookup(NativeMapCatalog::current_dataset_id,scope.position.area,scope.position.scene);
        return found==1 && saved && *saved==scope.position && map && *map==scope.map;
    }
    bool current(const Source::Snapshot& expected,const Source::Scope& scope) {
        if(reentered || !common_current(scope))return false;
        const auto actual=storage.load(scope.account,scope.character,client,Source::record_kind);
        return actual && *actual==expected && common_current(scope) && !reentered;
    }
};
}
SharedTaiwanWorldEntrySource::NativeSource SharedTaiwanStoredWorldEntrySource::create(
        NativeWorldEntrySnapshotRepository& storage,RecoveredCharacterRepository& characters,
        const NativeMapCatalog& maps,std::string client,Qualify qualify) {
    const auto digest=client.size()==64 && std::all_of(client.begin(),client.end(),[](char c) {
        return (c>='0' && c<='9') || (c>='a' && c<='f');
    });
    if(!digest || !qualify || !storage.owns_characters(characters))
        throw std::invalid_argument("TW stored entry needs actual same-owner material and qualification");
    auto state=std::make_shared<State>(State{storage,characters,maps,std::move(client),std::move(qualify)});
    return [state=std::move(state)](const Scope& input)->std::optional<SharedTaiwanWorldEntrySource::Native> {
        const auto owner=state;
        State::Lease lease(*owner);
        const Scope scope=input; // Owned before any external observer.
        if(!owner->common_current(scope))return std::nullopt;
        auto observed=owner->storage.load(scope.account,scope.character,owner->client,record_kind);
        if(!observed || observed->client_sha256!=owner->client || observed->record_kind!=record_kind ||
           !Snapshot::same_root(observed->root,scope.selected) || observed->position!=scope.position ||
           !observed->revision || !observed->position.revision || observed->record.size()!=Frame{}.size())return std::nullopt;
        const auto material=std::make_shared<const Snapshot>(std::move(*observed));
        Frame frame;
        std::copy(material->record.begin(),material->record.end(),frame.begin());
        const auto view=RecoveredWorldEntryView::read(frame);
        if(!view || scope.character!=view->actor_handle || scope.position.area!=view->area ||
           scope.position.scene!=view->scene || scope.position.x!=view->x || scope.position.y!=view->y ||
           !owner->current(*material,scope))return std::nullopt;
        if(!owner->qualify(*material,scope,frame,Check::Supply) || !owner->current(*material,scope))return std::nullopt;
        // Full original frame is returned without rewriting opaque selectors,
        // reserved bytes, appearance/resource words or map high WORD.
        SharedTaiwanWorldEntrySource::Current current=[owner,material,scope,frame](const Scope& supplied,const Frame& sent) {
            const auto held=owner;const auto snapshot=material;
            State::Lease guard(*held);
            if(!same_scope(supplied,scope) || sent!=frame || !held->current(*snapshot,scope))return false;
            return held->qualify(*snapshot,scope,frame,Check::Current) && held->current(*snapshot,scope);
        };
        return SharedTaiwanWorldEntrySource::Native{frame,std::move(current)};
    };
}
}
