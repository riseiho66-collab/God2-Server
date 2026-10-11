#pragma once
#include "game/TaiwanNativeMapAsset.h"
#include "game/TaiwanNativeResourceSelection.h"
#include <memory>
#include <vector>

namespace god2 {
// Game-owned selected-source lineage for the existing TW native scene factory.
// Registry identity never supplies native resource/window authority or a5D.
class TaiwanNativeSceneResourceOwner final {
public:
    using Scene=SharedTaiwanNativeMovementScene;
    using Lease=SharedWorldPresence::Lease;
    struct RomInput {
        std::size_t ordinal;
        std::uint64_t actual_resource_generation;
        TaiwanNativeResourceSelection selected;
    };
    struct Sources {
        TaiwanNativeResourceSelection hmd;
        std::uint64_t actual_hmd_generation;
        // Actual model object's native+1C bytes, not derived from a filename.
        std::vector<std::uint8_t> actual_rom_prefix;
        std::vector<RomInput> roms;
    };
    using ResourceCurrent=std::function<bool(Scene::Check,const Scene::Scope&,
        const Scene::Resources&,const Sources&)>;
    struct Input {
        Sources sources;
        std::size_t max_hmd_plain_bytes,max_rom_plain_bytes;
        std::uint64_t actual_resource_generation,actual_initial_scene_generation;
        RecoveredPosition actual_position;
        std::uint8_t actual_direction;
        // Mandatory real issuer qualifies every retained source generation,
        // exact Lease/map and native object/window/frame lifecycle. Matching a
        // private registry or complete file alone does not satisfy Current.
        // Real callbacks run on game, never retain argument references, yield,
        // pump events, send or perform another common position CAS.
        ResourceCurrent current;
        std::shared_ptr<Scene::Authority> authority;
    };
    static std::shared_ptr<TaiwanNativeSceneResourceOwner> create(
        std::shared_ptr<SharedWorldPresence>,std::size_t actual_session_capacity);
    ~TaiwanNativeSceneResourceOwner();
    TaiwanNativeSceneResourceOwner(const TaiwanNativeSceneResourceOwner&)=delete;
    TaiwanNativeSceneResourceOwner& operator=(const TaiwanNativeSceneResourceOwner&)=delete;
    // Exact ready Session/Lease, saved pose and real source generations are
    // required. Selected originals are parsed here; no new file selection,
    // guessed path, native bank loading or default frame is performed.
    bool install(const std::shared_ptr<Session>&,const Lease&,const Input&);
    bool replace(const std::shared_ptr<Session>&,const Lease&,const Input&);
    // Exact stored pointer+Lease release; works after common identity clears.
    // Never releases common Presence/Visibility or a successor generation.
    bool remove(Session&,const Lease&);
    Scene::MaterialSource material_source();
    SharedTaiwanMovementSource::Factory factory();
    // Hosting owner may propagate a rejected caught nested operation before
    // CAS. No common Presence/Visibility lease cleanup, gameplay mutation or
    // generated native value; only this owner's affected private Entry detaches.
    void invalidate_active();
private:
    struct State;
    explicit TaiwanNativeSceneResourceOwner(std::shared_ptr<State>);
    std::shared_ptr<State> state_;
};
}
