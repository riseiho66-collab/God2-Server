#pragma once
#include "game/SharedTaiwanWorldEntrySource.h"
#include "game/SharedTaiwanStoredWorldEntrySource.h"
#include "db/SqliteNativeWorldEntrySnapshotRepository.h"
#include "db/NativeEnemyDisplayCatalog.h"
#include "game/TaiwanNativeNpcSceneGroups.h"
#include "game/TaiwanNativeTransformCards.h"
#include <memory>
#include <utility>

namespace god2 {
// Complete actual TW2A issuer -> same-Database raw writer -> entry reader.
// A supplied frame remains source material, never a guessed serializer.
class SharedTaiwanNativeWorldEntryOfferSource final {
public:
    using Source=SharedTaiwanWorldEntrySource;
    using Snapshot=NativeWorldEntrySnapshot;
    using Issuer=SqliteNativeWorldEntrySnapshotRepository::Issuer;
    class Offer {
    public:
        static std::optional<Offer> from_actual_source(Snapshot,Issuer);
        Offer(const Offer&)=delete;
        Offer& operator=(const Offer&)=delete;
        Offer(Offer&&) noexcept=default;
        Offer& operator=(Offer&&)=delete;
    private:
        friend class SharedTaiwanNativeWorldEntryOfferSource;
        Offer(Snapshot next,Issuer current):next_(std::move(next)),current_(std::move(current)) {}
        Snapshot next_;
        Issuer current_;
    };
    // Actual complete native resources/rules/phase producer, not geometry-only
    // permission. No SQL writes, pumping or retention of borrowed arguments.
    using Supply=std::function<std::optional<Offer>(const Source::Scope&,
        const std::optional<Snapshot>&)>;
    // Actual full resource observations supplied to the complete frame issuer.
    // Construction is private: callers cannot substitute a hand-written list
    // for the immutable NPC source or the fully qualified EnyName read snapshot.
    class SceneContent final {
    public:
        const TaiwanNativeNpcSceneGroups& npc_source() const noexcept {return *npcs_;}
        const NativeEnemyDisplayCatalog::Scene& enemies() const noexcept {return enemies_;}
        // Present only in the explicit card-aware binding. Supplies exact
        // source selectors; the offered2A's nonzero key is qualified separately
        // against its target scene before every existing issuer/CAS boundary.
        const TaiwanNativeTransformCards* transform_cards() const noexcept {return cards_.get();}
        // A missing/empty group is an observed resource fact, not admission.
        // Full WORD scene comparison; no BYTE alias for scene256..1023.
        const TaiwanNativeNpcSceneGroups::Group* npc_group() const {
            return npcs_->find(static_cast<std::uint8_t>(enemies_.area),static_cast<std::uint16_t>(enemies_.scene));
        }
    private:
        friend class SharedTaiwanNativeWorldEntryOfferSource;
        SceneContent(std::shared_ptr<const TaiwanNativeNpcSceneGroups> npcs,NativeEnemyDisplayCatalog::Scene enemies,
                std::shared_ptr<const TaiwanNativeTransformCards> cards)
            :npcs_(std::move(npcs)),enemies_(std::move(enemies)),cards_(std::move(cards)) {}
        const std::shared_ptr<const TaiwanNativeNpcSceneGroups> npcs_;
        const NativeEnemyDisplayCatalog::Scene enemies_;
        const std::shared_ptr<const TaiwanNativeTransformCards> cards_;
    };
    using SceneContentPtr=std::shared_ptr<const SceneContent>;
    // Complete actual2A producer remains mandatory. It receives actual resource
    // bytes/occurrences, not resource-derived guesses for opaque frame fields.
    // Copy SceneContentPtr if retaining it; never retain borrowed arguments.
    using SceneSupply=std::function<std::optional<Offer>(const Source::Scope&,
        const std::optional<Snapshot>&,const SceneContentPtr&)>;
    // Create on the real serial game owner. NPC full original stays strongly
    // owned; catalog borrows the Application database through all issuer drain.
    // Before/after producer and each real writer Issuer check compare the full
    // scene observation. No encoded file read, codec, scene grant or2A padding.
    // Same-Database identity is supplied by the actual Context host helper;
    // this generic adapter does not certify arbitrary catalog/writer pairs.
    static Supply with_scene_content(const NativeEnemyDisplayCatalog&,
        std::shared_ptr<const TaiwanNativeNpcSceneGroups>,SceneSupply);
    // Exact card row + possibly different EnyName target scene. Full producer
    // still mandatory; no new serializer, synthesized padding or Main opt-in.
    static Supply with_scene_content(const NativeEnemyDisplayCatalog&,
        std::shared_ptr<const TaiwanNativeNpcSceneGroups>,
        std::shared_ptr<const TaiwanNativeTransformCards>,SceneSupply);
    struct SceneBinding {
        Supply offer;
        SharedTaiwanStoredWorldEntrySource::Qualify qualify;
    };
    // One resource owner for both the issuer/CAS and stored Supply/Current.
    // The real complete qualifier stays mandatory and receives Check unchanged.
    // After durable COMMIT, stale resources suppress delivery, not undo storage.
    // Catalog must outlive every copied issuer, Native and Current closure.
    static SceneBinding with_scene_content_and_qualification(const NativeEnemyDisplayCatalog&,
        std::shared_ptr<const TaiwanNativeNpcSceneGroups>,
        std::shared_ptr<const TaiwanNativeTransformCards>,SceneSupply,
        SharedTaiwanStoredWorldEntrySource::Qualify);
    // Only the explicit Entry Prepare invokes the writer. Native/Current reads
    // never prepare. Repositories outlive the actual game-owner facade drain.
    static Source::Prepare create(SqliteNativeWorldEntrySnapshotRepository&,
        AccountRepository&,RecoveredCharacterRepository&,const NativeMapCatalog&,
        std::string client_sha256,Supply);
private:
    static SceneBinding bind_scene_content(const NativeEnemyDisplayCatalog&,
        std::shared_ptr<const TaiwanNativeNpcSceneGroups>,
        std::shared_ptr<const TaiwanNativeTransformCards>,SceneSupply,
        SharedTaiwanStoredWorldEntrySource::Qualify={});
};
}
