#include "game/SharedTaiwanWorldEntrySource.h"
#include "protocol/RecoveredWorldEntryView.h"
#include <algorithm>
#include <memory>
#include <stdexcept>
#include <thread>
#include <utility>

namespace god2 {
namespace {
bool same_character(const RecoveredCharacter& a,const RecoveredCharacter& b) {
    return a.id==b.id && a.account_id==b.account_id && a.slot==b.slot &&
        a.profile==b.profile && a.created_at==b.created_at &&
        a.name_codepage==b.name_codepage && a.streamer_privilege==b.streamer_privilege;
}
RecoveredCharacter owned_character(RecoveredCharacterRepository& repository,
        std::uint64_t account,std::uint64_t character) {
    std::optional<RecoveredCharacter> found;
    for(const auto& row:repository.list_for_account(account)) {
        if(row.id!=character)continue;
        if(found || row.account_id!=account)
            throw std::invalid_argument("TW entry character ownership is ambiguous");
        found=row;
    }
    if(!found)throw std::invalid_argument("TW entry character is not owned by account");
    return std::move(*found);
}
struct State {
    RecoveredCharacterRepository& characters;
    const NativeMapCatalog& maps;
    SharedTaiwanWorldEntrySource::NativeSource native;
    SharedTaiwanNativeCharacterListSource::SelectedSource selection;
    SharedTaiwanWorldEntrySource::Prepare prepare;
    std::shared_ptr<SharedWorldPresence> presence;
    const std::thread::id thread=std::this_thread::get_id();
    bool active=false,reentered=false;

    bool unchanged(const SharedTaiwanWorldEntrySource::Scope& scope,
                   const RecoveredCharacter& expected) {
        if(presence && (!presence->owns_repository(characters) || presence->character_reserved(scope.character)))return false;
        const auto character=owned_character(characters,scope.account,scope.character);
        const auto position=characters.load_position(scope.account,scope.character);
        if(!same_character(character,expected) || !position || *position!=scope.position)return false;
        const auto map=maps.lookup(NativeMapCatalog::current_dataset_id,position->area,position->scene);
        return map && *map==scope.map && (!presence || !presence->character_reserved(scope.character));
    }
    SharedTaiwanWorldEntrySource::Frame entry(std::uint64_t session,
            std::uint64_t account,std::uint64_t character) {
        // Check thread before touching mutable guard state. A rejected nested
        // call also invalidates its outer invocation if the provider catches it.
        if(std::this_thread::get_id()!=thread)
            throw std::logic_error("TW entry source game owner mismatch");
        if(active) {
            reentered=true;
            throw std::logic_error("TW entry source reentered");
        }
        active=true;reentered=false;
        struct Exit {
            State& owner;
            ~Exit() {owner.active=false;owner.reentered=false;}
        } exit{*this};
        // Frozen TW tail/lifecycle compare the FULL selected character ID to
        // the decoded14-bit actor handle. Never truncate or alias large IDs.
        if(!session || !account || !character || character>0x3fff)
            throw std::invalid_argument("TW entry source requires actual representable identities");
        const auto selected=owned_character(characters,account,character);
        const auto position=characters.load_position(account,character);
        if(!position || !position->revision || position->area<1 || position->area>16 ||
           position->scene>1023 || position->x>0x7fff || position->y>0x7fff)
            throw std::invalid_argument("TW entry requires actual saved native position");
        const auto map=maps.lookup(NativeMapCatalog::current_dataset_id,position->area,position->scene);
        if(!map)throw std::invalid_argument("TW entry saved map is not in the actual catalog");
        std::optional<SharedTaiwanNativeCharacterListSource::SelectedLink> lineage;
        if(selection) {
            lineage=selection(session,account,character);
            if(reentered || !lineage || !lineage->selected || !lineage->current)
                throw std::invalid_argument("TW entry lacks its actual selected provenance");
            const auto& receipt=*lineage->selected;
            const auto roots=receipt.roots();
            const auto root=std::find_if(roots.begin(),roots.end(),[&](const auto& value){return value.id==character;});
            if(!receipt.source_alive() || receipt.scope().session!=session || receipt.scope().account!=account ||
               receipt.character()!=character || root==roots.end() || !same_character(*root,selected))
                throw std::invalid_argument("TW entry differs from the actual full selected common root");
        }
        const SharedTaiwanWorldEntrySource::Scope scope{session,account,character,*position,*map,selected,
            lineage?lineage->selected:nullptr};
        const auto current=[&] {
            if(reentered || !unchanged(scope,selected) || reentered)return false;
            if(lineage && (!lineage->current() || reentered))return false;
            return !reentered && unchanged(scope,selected) && !reentered;
        };
        if(!current())throw std::invalid_argument("TW entry selection changed before native supply");
        if(prepare && (!prepare(scope,current) || !current()))
            throw std::invalid_argument("TW entry actual issuer preparation failed");
        auto material=native(scope);
        if(reentered || !material || !material->current || !current())
            throw std::invalid_argument("TW entry source changed during native supply");
        const auto full=RecoveredWorldEntryView::read(material->frame);
        if(!full || character!=full->actor_handle || full->area!=position->area ||
           full->scene!=position->scene || full->x!=position->x || full->y!=position->y)
            throw std::invalid_argument("TW native entry does not match actual saved character geometry");
        // Map.kind is independent source material; no proven relation licenses
        // a comparison to wire.kind. Full opaque frame bytes stay untouched.
        if(!current() || !material->current(scope,material->frame) || reentered || !current())
            throw std::invalid_argument("TW native entry provenance or saved source is stale");
        return material->frame;
    }
};
}
SharedTaiwanWorldEntrySource::Native::Native(Frame frame_value,Current current_value)
    :frame(std::move(frame_value)),current(std::move(current_value)) {
    if(!current)throw std::invalid_argument("TW native entry requires actual Current qualification");
}
SharedTaiwanWorldEntrySource::Entry SharedTaiwanWorldEntrySource::create(
        RecoveredCharacterRepository& characters,const NativeMapCatalog& maps,NativeSource native,
        SharedTaiwanNativeCharacterListSource::SelectedSource selection,Prepare prepare,
        std::shared_ptr<SharedWorldPresence> presence) {
    if(!native || (prepare && !selection) || bool(selection)!=bool(presence) ||
       (presence && !presence->owns_repository(characters)))
        throw std::invalid_argument("TW entry source requires actual supplier, selected lineage and identical common presence");
    auto state=std::make_shared<State>(State{characters,maps,std::move(native),std::move(selection),std::move(prepare),std::move(presence)});
    return [state=std::move(state)](std::uint64_t session,std::uint64_t account,std::uint64_t character) {
        // Keep invocation ownership local before calling any external supplier.
        const auto owner=state;
        return owner->entry(session,account,character);
    };
}
}
