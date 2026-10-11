#pragma once
#include "cn/auth/SharedWorldSelection.h"
#include "cn/world/SharedWorldGameplay.h"
#include "cn/world/SharedNativeMovementScene.h"

namespace god2::cn {
// Real pending selection ->same common repository position ->reserved actor
// ->same generation lease ->real native scene snapshot ->existing ready/mixed
// controllers ->complete supplied02/2A. No spawn, handles or replies invented.
class SharedWorldPreparation:public std::enable_shared_from_this<SharedWorldPreparation> {
public:
    using Connection=SharedCredentialConnection;
    using Choice=SharedWorldSelection::Choice;
    using Lease=SharedWorldPresence::Lease;
    struct Native {
        god2cn::Bytes status02,begin2a;
        std::uint64_t scene_revision;
        std::optional<RecoveredPosition> previous; // Required actual predecessor on transfer only.
    };
    class Reservation {
    public:
        virtual ~Reservation()=default;
        // Real scene allocator/native supplier reserves its own actor handle.
        // Neither common character ID nor a renderer resource key supplies it.
        virtual Native snapshot()=0;
        // Observe native reservation/rules at the specified publication stage;
        // QueueAccepted is after actual IO encoding/capacity, before bytes leave.
        virtual bool current(const Choice&,const RecoveredPosition&,const Native&,
            SharedWorldSelection::PublicationCheck=SharedWorldSelection::PublicationCheck::BeforePublish)=0;
        // Normal scene is the exact asset snapshot. Transfer must qualify its
        // own retained/reload lifecycle; it receives no fake initial snapshot.
        virtual bool qualify_transfer(const std::shared_ptr<Connection>&,const Lease&,const Native&)=0;
        virtual std::optional<SharedWorldGameplay::Sources> gameplay(
            const std::shared_ptr<Connection>&,const Lease&,const std::shared_ptr<SharedInitialScene>&)=0;
        virtual std::shared_ptr<SharedNativeMovementScene::Authority> normal_movement_authority()=0;
        // Actual actor/timing/native supplier cleanup. Called once on failure
        // or this transport's cleanup, not on another actor incarnation.
        virtual void release() noexcept=0;
    };
    using Reserve=std::function<std::shared_ptr<Reservation>(const Choice&,const RecoveredPosition&)>;
    static std::shared_ptr<SharedWorldPreparation> create(RecoveredCharacterRepository&,const NativeMapCatalog&,
        std::shared_ptr<SharedWorldPresence>,std::shared_ptr<SharedActorVisibility>,
        std::shared_ptr<const god2cn::CnSceneAssets>,Reserve,
        std::size_t max_encoded_bytes,std::size_t max_plain_bytes,
        std::shared_ptr<SharedNativeWorldTransports> world_transports={});
    SharedWorldSelection::Selected selected();
    // Exact storage/catalog retained by this controller, including transfers.
    // Composition must use the listener's actual common source objects. This
    // identity observation supplies neither native data nor entry permission.
    bool owns_sources(const RecoveredCharacterRepository& characters,
                      const NativeMapCatalog& maps) const {
        owner();return &characters_==&characters && &maps_==&maps;
    }
    // Exact retained pair, not merely a visibility object owning some equivalent
    // presence. This observation supplies no reservation/native authority.
    bool owns_registries(const std::shared_ptr<SharedWorldPresence>&,
                         const std::shared_ptr<SharedActorVisibility>&) const;
    // Exact configured native endpoint source, including the null legacy
    // path. Equal repository/presence alone cannot qualify a foreign source.
    bool owns_transport_source(const std::shared_ptr<SharedNativeWorldTransports>&) const;
    // Exact registry retained by this actual preparation controller. The login
    // source may bind removal exclusion to it; no lease or authority is granted.
    std::shared_ptr<const SharedWorldPresence> presence_registry() const {
        owner();return presence_;
    }
private:
    SharedWorldPreparation(RecoveredCharacterRepository&,const NativeMapCatalog&,
        std::shared_ptr<SharedWorldPresence>,std::shared_ptr<SharedActorVisibility>,
        std::shared_ptr<const god2cn::CnSceneAssets>,Reserve,std::size_t,std::size_t,
        std::shared_ptr<SharedNativeWorldTransports>);
    void owner() const;
    void prepare(const std::shared_ptr<SharedWorldSelection>&,Choice,Connection::Transport::Completion);
    std::thread::id thread_=std::this_thread::get_id();
    RecoveredCharacterRepository& characters_;
    const NativeMapCatalog& maps_;
    std::shared_ptr<SharedWorldPresence> presence_;
    std::shared_ptr<SharedActorVisibility> visibility_;
    std::shared_ptr<SharedNativeWorldTransports> world_transports_;
    std::shared_ptr<const god2cn::CnSceneAssets> assets_;
    Reserve reserve_;
    std::size_t encoded_budget_,plain_budget_;
};
}
