#include "game/SharedTaiwanNativeWorldEntryOfferSource.h"
#include "game/SharedTaiwanStoredWorldEntrySource.h"
#include "game/TaiwanNativeClientGroupConfiguration.h"
#include "protocol/RecoveredWorldEntryView.h"
#include <algorithm>
#include <limits>
#include <stdexcept>
#include <thread>

namespace god2 {
namespace {
using OfferSource=SharedTaiwanNativeWorldEntryOfferSource;
bool positive(std::uint64_t value) {
    return value && value<=static_cast<std::uint64_t>(std::numeric_limits<std::int64_t>::max());
}
bool shape(const OfferSource::Snapshot& next) {
    const auto digest=[](std::string_view value) {
        return value.size()==64 && std::all_of(value.begin(),value.end(),[](char c) {
            return (c>='0' && c<='9') || (c>='a' && c<='f');
        });
    };
    if(!positive(next.root.account_id) || !next.root.id || next.root.id>0x3fff || next.root.slot>=2 ||
       next.root.created_at.empty() || next.root.created_at.size()>2048 || next.root.created_at.find('\0')!=std::string::npos ||
       (next.root.name_codepage!=0 && next.root.name_codepage!=936 && next.root.name_codepage!=950) ||
       next.root.streamer_privilege>3 || !positive(next.revision) || !positive(next.position.revision) ||
       next.client_sha256!=TaiwanNativeClientGroupConfiguration::client_sha256 ||
       next.record_kind!=SharedTaiwanStoredWorldEntrySource::record_kind || !digest(next.source_sha256) ||
       next.source_record.empty() || next.source_record.size()>2048 || next.source_record.find('\0')!=std::string::npos ||
       next.record.size()!=OfferSource::Source::Frame{}.size())return false;
    OfferSource::Source::Frame frame;
    std::copy(next.record.begin(),next.record.end(),frame.begin());
    const auto native=RecoveredWorldEntryView::read(frame);
    return native && next.root.id==native->actor_handle && next.position.area==native->area &&
        next.position.scene==native->scene && next.position.x==native->x && next.position.y==native->y;
}
struct State {
    SqliteNativeWorldEntrySnapshotRepository& writer;
    AccountRepository& accounts;
    RecoveredCharacterRepository& characters;
    const NativeMapCatalog& maps;
    const std::string client;
    OfferSource::Supply supply;
    const std::thread::id thread=std::this_thread::get_id();
    bool busy=false,reentered=false;
    void check() const {
        if(thread!=std::this_thread::get_id() || reentered)
            throw std::logic_error("TW entry offer source owner/reentry mismatch");
    }
    struct Guard {
        State& state;
        explicit Guard(State& s):state(s) {
            state.check();
            if(state.busy){state.reentered=true;throw std::logic_error("TW entry offer source reentered");}
            state.busy=true;
        }
        ~Guard(){state.busy=false;state.reentered=false;}
    };
    bool common_current(const OfferSource::Source::Scope& scope) {
        check();
        if(!writer.owns_sources(accounts,characters) || !scope.session || !scope.account || !scope.character ||
           !scope.selection || !scope.selection->source_alive() || scope.selection->scope().session!=scope.session ||
           scope.selection->scope().account!=scope.account || scope.selection->character()!=scope.character ||
           scope.selected.account_id!=scope.account || scope.selected.id!=scope.character)return false;
        const auto roots=characters.list_for_account(scope.account);
        const auto retained=scope.selection->roots();
        if(roots.size()!=retained.size())return false;
        std::size_t selected=0;
        for(std::size_t i=0;i<roots.size();++i) {
            if(!NativeWorldEntrySnapshot::same_root(roots[i],retained[i]))return false;
            if(roots[i].id==scope.character) {
                if(!NativeWorldEntrySnapshot::same_root(roots[i],scope.selected))return false;
                ++selected;
            }
        }
        const auto position=characters.load_position(scope.account,scope.character);
        const auto map=maps.lookup(NativeMapCatalog::current_dataset_id,scope.position.area,scope.position.scene);
        return selected==1 && position && *position==scope.position && map && *map==scope.map;
    }
};
struct SceneState {
    const NativeEnemyDisplayCatalog& enemies;
    std::shared_ptr<const TaiwanNativeNpcSceneGroups> npcs;
    std::shared_ptr<const TaiwanNativeTransformCards> cards;
    OfferSource::SceneSupply supply;
    const std::thread::id thread=std::this_thread::get_id();
    bool busy=false,reentered=false;
    void check() const {
        if(thread!=std::this_thread::get_id() || reentered)
            throw std::logic_error("TW entry scene source owner/reentry mismatch");
    }
    struct Guard {
        SceneState& state;
        explicit Guard(SceneState& s):state(s) {
            state.check();
            if(state.busy){state.reentered=true;throw std::logic_error("TW entry scene source reentered");}
            state.busy=true;
        }
        ~Guard(){state.busy=false;state.reentered=false;}
    };
    using TargetScene=std::shared_ptr<const NativeEnemyDisplayCatalog::Scene>;
    bool current(const OfferSource::SceneContent& content,const TargetScene& target={}) const {
        check();
        const auto actual=enemies.read_scene(content.enemies().area,content.enemies().scene);
        check();
        if(!actual || *actual!=content.enemies() || &content.npc_source()!=npcs.get() ||
           content.transform_cards()!=cards.get())return false;
        if(!target)return true;
        const auto actual_target=enemies.read_scene(target->area,target->scene);
        check();return actual_target && *actual_target==*target;
    }
    bool card_target(const OfferSource::Snapshot& next,TargetScene& target) const {
        check();target.reset();
        if(!cards)return true; // Existing non-card binding retains its contract.
        if(next.record.size()!=OfferSource::Source::Frame{}.size())return false;
        OfferSource::Source::Frame frame;
        std::copy(next.record.begin(),next.record.end(),frame.begin());
        const auto native=RecoveredWorldEntryView::read(frame);
        if(!native)return false;
        const auto key=native->entry_appearance_baseline().transform_key;
        if(!key)return true; // Actual zero-transform branch does not use45C000.
        const auto* card=cards->find(key);
        if(!card || card->target.area>=17 || !card->target.ordinal)return false;
        auto scene=enemies.read_scene(card->target.area,card->target.scene);check();
        if(!scene || scene->source.native_image_sha256!=TaiwanNativeTransformCards::native_image_sha256 ||
           scene->source.decoded_sha256!=TaiwanNativeNpcSceneGroups::decoded_sha256 ||
           scene->source.source_sha256!=TaiwanNativeNpcSceneGroups::historical_encoded_sha256 ||
           card->target.ordinal>scene->records.size())return false;
        const auto& record=scene->records[card->target.ordinal-1];
        if(record.area!=card->target.area || record.scene!=card->target.scene ||
           record.ordinal!=card->target.ordinal)return false;
        // A complete qualified scene owns the exact target occurrence. Never
        // substitute current-world geometry or a name/label-based monster join.
        target=std::make_shared<const NativeEnemyDisplayCatalog::Scene>(std::move(*scene));
        return true;
    }
};
}
std::optional<SharedTaiwanNativeWorldEntryOfferSource::Offer>
SharedTaiwanNativeWorldEntryOfferSource::Offer::from_actual_source(Snapshot next,Issuer current) {
    if(!current || !shape(next))return std::nullopt;
    return Offer(std::move(next),std::move(current));
}
SharedTaiwanNativeWorldEntryOfferSource::Supply SharedTaiwanNativeWorldEntryOfferSource::with_scene_content(
        const NativeEnemyDisplayCatalog& enemies,std::shared_ptr<const TaiwanNativeNpcSceneGroups> npcs,
        SceneSupply supply) {
    return bind_scene_content(enemies,std::move(npcs),{},std::move(supply));
}
SharedTaiwanNativeWorldEntryOfferSource::Supply SharedTaiwanNativeWorldEntryOfferSource::with_scene_content(
        const NativeEnemyDisplayCatalog& enemies,std::shared_ptr<const TaiwanNativeNpcSceneGroups> npcs,
        std::shared_ptr<const TaiwanNativeTransformCards> cards,SceneSupply supply) {
    if(!cards)throw std::invalid_argument("TW card-aware entry requires actual pinned card source");
    return bind_scene_content(enemies,std::move(npcs),std::move(cards),std::move(supply));
}
SharedTaiwanNativeWorldEntryOfferSource::Supply SharedTaiwanNativeWorldEntryOfferSource::bind_scene_content(
        const NativeEnemyDisplayCatalog& enemies,std::shared_ptr<const TaiwanNativeNpcSceneGroups> npcs,
        std::shared_ptr<const TaiwanNativeTransformCards> cards,SceneSupply supply) {
    if(!npcs || !supply)throw std::invalid_argument("TW entry scene content requires actual full sources and producer");
    auto state=std::make_shared<SceneState>(SceneState{enemies,std::move(npcs),std::move(cards),std::move(supply)});
    return [state](const Source::Scope& input,const std::optional<Snapshot>& before)->std::optional<Offer> {
        const auto owner=state;SceneState::Guard guard(*owner);
        const auto scope=input;const auto expected=before;
        if(scope.position.area<1 || scope.position.area>16 || scope.position.scene>1023)return std::nullopt;
        auto enemies=owner->enemies.read_scene(scope.position.area,scope.position.scene);owner->check();
        if(!enemies)return std::nullopt; // Whole catalog absent is not an empty scene.
        // The qualified reader pins149c/70a4/75c3; NPC constructor independently
        // pins the complete same75c3 bytes. No encoded-present assertion follows.
        if(enemies->source.native_image_sha256!=TaiwanNativeNpcSceneGroups::native_image_sha256 ||
           enemies->source.decoded_sha256!=TaiwanNativeNpcSceneGroups::decoded_sha256 ||
           enemies->source.source_sha256!=TaiwanNativeNpcSceneGroups::historical_encoded_sha256)return std::nullopt;
        SceneContentPtr content(new SceneContent(owner->npcs,std::move(*enemies),owner->cards));
        if(!owner->current(*content))return std::nullopt;
        const auto producer=owner->supply;
        auto supplied=producer(scope,expected,content);owner->check();
        if(!supplied || !owner->current(*content) || supplied->next_.position!=scope.position ||
           !Snapshot::same_root(supplied->next_.root,scope.selected))return std::nullopt;
        SceneState::TargetScene target;
        if(!owner->card_target(supplied->next_,target) || !owner->current(*content,target))return std::nullopt;
        const auto issuer=supplied->current_;
        const auto issued=supplied->next_;
        supplied->current_=[owner,content,target,issuer,issued](const std::optional<Snapshot>& previous,
                const Snapshot& next,SqliteNativeWorldEntrySnapshotRepository::WriteCheck check) {
            const auto retained=owner;const auto actual_content=content;const auto actual_issuer=issuer;
            SceneState::Guard guard(*retained);
            if(next!=issued || !retained->current(*actual_content,target))return false;
            const bool accepted=actual_issuer(previous,next,check);retained->check();
            return accepted && retained->current(*actual_content,target);
        };
        return supplied;
    };
}
SharedTaiwanWorldEntrySource::Prepare SharedTaiwanNativeWorldEntryOfferSource::create(
        SqliteNativeWorldEntrySnapshotRepository& writer,AccountRepository& accounts,
        RecoveredCharacterRepository& characters,const NativeMapCatalog& maps,std::string client,Supply supply) {
    if(!writer.owns_sources(accounts,characters) || client!=TaiwanNativeClientGroupConfiguration::client_sha256 || !supply)
        throw std::invalid_argument("TW entry offer requires exact shared writer/readers/build and actual issuer");
    auto state=std::make_shared<State>(State{writer,accounts,characters,maps,std::move(client),std::move(supply)});
    return [state](const Source::Scope& input,const std::function<bool()>& parent_current) {
        const auto owner=state;State::Guard guard(*owner);
        const auto scope=input;const auto current=parent_current;
        const auto ready=[&] {
            if(!current || !owner->common_current(scope))return false;
            const bool accepted=current();owner->check();
            return accepted && owner->common_current(scope);
        };
        if(!ready())return false;
        auto expected=owner->writer.load(scope.account,scope.character,owner->client,
            SharedTaiwanStoredWorldEntrySource::record_kind);
        if(!ready())return false;
        auto supplied=owner->supply(scope,expected);owner->check();
        if(!supplied || !ready())return false;
        const auto offer=std::make_shared<Offer>(std::move(*supplied));
        const auto next=offer->next_;
        if(!shape(next) || !Snapshot::same_root(next.root,scope.selected) || next.position!=scope.position ||
           next.client_sha256!=owner->client || (expected && next.revision<=expected->revision))return false;
        // Expected may witness an older profile/position. Only next must match
        // the current root. BeforeCommit observes staged next, so this parent
        // fence deliberately never compares entry.load to the old tuple.
        auto committed=owner->writer.replace_from_issuer(std::move(expected),next,
            [&](const std::optional<Snapshot>& before,const Snapshot& actual,
                    SqliteNativeWorldEntrySnapshotRepository::WriteCheck check) {
                if(actual!=next || !ready())return false;
                const auto issuer=offer->current_;
                const bool accepted=issuer(before,actual,check);owner->check();
                return accepted && ready();
            });
        // No provider/reload/retry after durable COMMIT. Later entry Current
        // may suppress delivery, but cannot retroactively undo this replacement.
        return committed && *committed==next;
    };
}
}
