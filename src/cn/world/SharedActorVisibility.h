#pragma once
#include "cn/net/SharedCredentialConnection.h"
#include "cn/protocol/CnRemoteActor.h"
#include "cn/protocol/CnRemoteActorMove.h"
#include "cn/text/CnNativeActorText.h"
#include "game/SharedWorldPresence.h"
#include "game/OwnedTaiwanReturnActorSavedSource.h"
#include "net/Session.h"
#include "game/TaiwanActorStatusPublication.h"
#include "protocol/RecoveredRemoteActor.h"
#include "protocol/RecoveredTaiwanActorOverride.h"
#include "protocol/RecoveredTaiwanPlayerAppearanceUpdate.h"
#include <functional>
#include <array>
#include <map>
#include <memory>
#include <string>
#include <variant>
#include <vector>

struct sqlite3; // Actual private transaction connection identity; no SQL is invoked by this interface.
namespace god2 {class SharedNativeActorNameSource;class OwnedTaiwanPkReturnRoleTextSource;}
namespace god2::cn {
class SharedInitialScene;
class SharedInitialAppearanceSource;
// Serial common owner tracks expected recipient actors through initial6F
// publication or legacy send submission. It never claims receipt/rendering or
// decides who should be visible.
// Real scene policy supplies each pair and full version-native records. CN/TW
// sources remain distinct; the legacy TW CUSTOM visibility stays frozen.
class SharedActorVisibility:public std::enable_shared_from_this<SharedActorVisibility> {
    struct Identity {};
    struct TaiwanPkDepartureState;
public:
    using Lease=SharedWorldPresence::Lease;
    struct TaiwanRawNameState {
        std::uint64_t source_revision; // Actual issuer lifecycle, not a native counter.
        std::uint16_t wire_codepage,actual_global_word_d8,actual_global_word_da;
        // Real receiving observer's loaded531C10 operands/profile (not the
        // visible source character's globals), pure non-yielding actual owner.
        // No guessed globals, language-bit/ACP codepage or default success.
        std::function<bool(Session&,std::uint64_t,std::uint16_t,std::uint16_t,std::uint16_t)> current;
    };
    // Exact raw-profile authority OR Session-owned accepted C1C occurrence.
    // Typed reports support NO_ADAPTATION only, not NLS/OS attestation.
    class TaiwanReceiverTextState {
    public:
        TaiwanReceiverTextState(TaiwanRawNameState raw):source_(std::move(raw)){}
        TaiwanReceiverTextState(Session::NativeTaiwanReceiverSelector selector):source_(std::move(selector)){}
        std::uint64_t source_revision()const noexcept {
            if(const auto* raw=std::get_if<TaiwanRawNameState>(&source_))return raw->source_revision;
            return std::get<Session::NativeTaiwanReceiverSelector>(source_).source_revision();
        }
        std::uint16_t wire_codepage()const noexcept {
            if(const auto* raw=std::get_if<TaiwanRawNameState>(&source_))return raw->wire_codepage;
            return std::get<Session::NativeTaiwanReceiverSelector>(source_).wire_codepage();
        }
        bool simplified()const noexcept {
            if(const auto* raw=std::get_if<TaiwanRawNameState>(&source_))return raw->actual_global_word_d8==4&&raw->actual_global_word_da==2;
            return std::get<Session::NativeTaiwanReceiverSelector>(source_).reported_simplified();
        }
        bool available()const noexcept {
            const auto* raw=std::get_if<TaiwanRawNameState>(&source_);
            return source_revision()&&(!raw||bool(raw->current))&&
                (wire_codepage()==936||wire_codepage()==950)&&((wire_codepage()==936)==simplified());
        }
        bool permits_source_codepage(std::uint16_t page)const noexcept {
            return std::holds_alternative<TaiwanRawNameState>(source_)||page==wire_codepage();
        }
        bool current(Session& receiver)const {
            if(!available())return false;
            if(const auto* raw=std::get_if<TaiwanRawNameState>(&source_))
                return raw->current(receiver,raw->source_revision,raw->wire_codepage,raw->actual_global_word_d8,raw->actual_global_word_da);
            return receiver.native_taiwan_receiver_selector_current(std::get<Session::NativeTaiwanReceiverSelector>(source_));
        }
        bool same_source(const TaiwanReceiverTextState& other)const noexcept {
            if(source_.index()!=other.source_.index())return false;
            if(const auto* raw=std::get_if<TaiwanRawNameState>(&source_)){
                const auto& next=std::get<TaiwanRawNameState>(other.source_);
                return raw->source_revision==next.source_revision&&raw->wire_codepage==next.wire_codepage&&
                    raw->actual_global_word_d8==next.actual_global_word_d8&&raw->actual_global_word_da==next.actual_global_word_da;
            }
            return std::get<Session::NativeTaiwanReceiverSelector>(source_)==std::get<Session::NativeTaiwanReceiverSelector>(other.source_);
        }
        bool operator==(const TaiwanReceiverTextState& other)const noexcept {return same_source(other);}
    private:
        std::variant<TaiwanRawNameState,Session::NativeTaiwanReceiverSelector> source_;
    };
    struct MainlandRawNameState {
        std::uint64_t source_revision;
        std::uint16_t wire_codepage;
        std::function<bool(SharedCredentialConnection&,std::uint64_t,std::uint16_t)> current;
    };
    struct Taiwan {
        std::weak_ptr<Session> connection;
        RecoveredRemoteActor::Record spawn;
        RecoveredRemoteActorRemove::Record removal;
        RecoveredRemoteActorMove::Record movement;
        std::optional<TaiwanReceiverTextState> raw_name_state; // Raw owner or exact accepted C1C; no synthetic globals.
        // Explicit source selection for stored common original -> first6F name.
        // Full appearance/other fields and legitimate visibility remain issuer inputs.
        std::shared_ptr<god2::SharedNativeActorNameSource> common_name_source;
    };
    class NormalSource {
    private:
        friend class SharedActorVisibility;
        NormalSource(std::shared_ptr<const Identity>,const Lease&,
            std::weak_ptr<SharedCredentialConnection>,std::shared_ptr<const SharedInitialScene>,
            god2cn::CnWorldEntry::BeginPlay,std::shared_ptr<const SharedInitialAppearanceSource> = {});
        std::shared_ptr<const Identity> identity_;
        Lease source_;
        std::weak_ptr<SharedCredentialConnection> connection_;
        std::shared_ptr<const SharedInitialScene> scene_;
        god2cn::CnWorldEntry::BeginPlay begin_;
        std::shared_ptr<const SharedInitialAppearanceSource> appearance_;
    };
    struct Mainland {
        std::weak_ptr<SharedCredentialConnection> connection;
        god2cn::CnRemoteActor::Record spawn;
        god2cn::CnRemoteActorRemove::Record removal;
        god2cn::CnRemoteActorMove::Record movement;
        // Optional success-only prediction from the actual qualified native
        // receiver NLS/gate owner. Sending6F still needs full scene qualification.
        std::optional<god2cn::CnNativeActorText::Projection> native_text;
        std::shared_ptr<const NormalSource> normal_source;
        std::optional<MainlandRawNameState> raw_name_state; // Optional metadata, no legacy success fallback.
        std::shared_ptr<god2::SharedNativeActorNameSource> common_name_source;
    };
    using Native=std::variant<Taiwan,Mainland>;
    struct OutwardRecipient {
        Lease lease;Native native;
        // Publication-local optional proof; movement/removal models remain unchanged.
        std::optional<TaiwanActorStatusPublication::ActorUnit> actor_status{};
    };
    enum class OutwardCheck {Prepare,BeforePublish};
    // The actual issuer owns the complete ordered observer set, visibility,
    // native resources/appearance/text and this source's current generation.
    // Predicate observes only: no yield, save, send or event pumping.
    using OutwardCurrent=std::function<bool(OutwardCheck)>;
    class Binding {
    public:
        const Lease& source() const noexcept {return source_;}
        const Lease& recipient() const noexcept {return recipient_;}
    private:
        friend class SharedActorVisibility;
        Binding(std::shared_ptr<const Identity>,Lease,Lease,std::uint64_t);
        std::shared_ptr<const Identity> identity_;
        Lease source_,recipient_;
        std::uint64_t generation_;
    };
    struct TaiwanMovement {std::weak_ptr<Session> connection;RecoveredRemoteActorMove::Record actual_visible_actor;};
    struct MainlandMovement {std::weak_ptr<SharedCredentialConnection> connection;god2cn::CnRemoteActorMove::Record actual_visible_actor;};
    struct MovementRecipient {Lease lease;std::variant<TaiwanMovement,MainlandMovement> output;};
    struct MainlandChatActor {
        std::weak_ptr<SharedCredentialConnection> connection;
        std::uint32_t native_actor_identity;
        std::string native_name_bytes;
        std::uint8_t native_language_tag;
        std::optional<MainlandRawNameState> raw_name_state;
    };
    struct TaiwanChatActor {
        std::weak_ptr<Session> connection;
        std::uint32_t native_actor_identity;
        std::string native_name_bytes;
        TaiwanReceiverTextState raw_name_state;
    };
    class ChatActorSnapshot {
    public:
        ChatActorSnapshot(const ChatActorSnapshot&)=default;
        ChatActorSnapshot& operator=(const ChatActorSnapshot&)=default;
        ChatActorSnapshot(ChatActorSnapshot&&) noexcept;
        ChatActorSnapshot& operator=(ChatActorSnapshot&&) noexcept;
    private:
        friend class SharedActorVisibility;
        struct State;
        explicit ChatActorSnapshot(std::shared_ptr<const State>);
        std::shared_ptr<const State> state_;
    };
    explicit SharedActorVisibility(std::shared_ptr<SharedWorldPresence>);
    bool owns_presence(const std::shared_ptr<SharedWorldPresence>&) const;
    // Actual same-generation CN normal scene supplies full retained2A. Project
    // only its qualified resolver operands into a separately supplied full6F.
    // Initial/inward/outward publishers requalify this private source witness.
    std::optional<Mainland> normal_mainland_from_scene(const Lease&,
        const std::shared_ptr<SharedCredentialConnection>& source_connection,
        std::shared_ptr<const SharedInitialScene>,Mainland actual_recipient_output) const;
    // Stronger explicit source path: actual same initial scene/full2A/CSV/ROM
    // token. Existing publication points recheck its actual owner's Current.
    // Complete native6F and observer/resource/equipment policy remain required.
    std::optional<Mainland> normal_mainland_with_appearance_source(const Lease&,
        const std::shared_ptr<SharedCredentialConnection>& source_connection,
        std::shared_ptr<const SharedInitialScene>,std::shared_ptr<const SharedInitialAppearanceSource>,
        Mainland actual_recipient_output) const;
    // Fresh show or6F replacement creates a private new incarnation. All records
    // must name the source reserved handle and current persisted coordinates;
    // state must agree between6F and5E. Unknown fields are mandatory full inputs.
    // Resource/appearance/text readiness is the actual scene owner's obligation.
    std::optional<Binding> show(const Lease& source,const Lease& recipient,Native);
    using OutwardCompletion=std::function<void(std::optional<std::vector<Binding>>)>;
    // Fresh source ->actual ready TW/CN observers. Complete6F and same native
    //5E/73 models are mandatory. No replacement, guessed peer set or default.
    // Model nodes publish inside each recipient's held IO boundary, before6F
    // release. Success observes every local queue release, never native receipt.
    void publish_outward_initial(const Lease&,std::vector<OutwardRecipient>,OutwardCurrent,OutwardCompletion);
    struct InitialActor {Lease source;Mainland native;};
    class InitialPublication {
    public:
        std::span<const god2cn::Bytes> records() const;
        // Exact full input models, before optional common first-name projection.
        // Aggregate issuers must match these actual boundaries before replacing
        // them with records(); offsets/other opaque records are never invented.
        std::span<const god2cn::Bytes> supplied_records() const;
    private:
        friend class SharedActorVisibility;
        struct State;
        explicit InitialPublication(std::shared_ptr<State>);
        std::shared_ptr<State> state_;
    };
    // Actual scene owner supplies the complete ordered incoming actor set and
    // full CN records for this inactive recipient. No guessed visibility rule,
    // handle/resource/name/default or send. Nodes are allocated before IO.
    std::shared_ptr<InitialPublication> prepare_initial_recipient(const Lease&,
        const std::shared_ptr<SharedCredentialConnection>&,std::vector<InitialActor>);
    bool initial_current(const std::shared_ptr<InitialPublication>&,
        const std::shared_ptr<SharedCredentialConnection>&,const Lease&,bool activated) const;
    // Same non-yielding game publication after exact recipient activation.
    // Transfers prepared nodes only; never sends, writes saves or pumps events.
    bool publish_initial(const std::shared_ptr<InitialPublication>&,
        const std::shared_ptr<SharedCredentialConnection>&,const Lease&);
    struct InitialTaiwanActor {
        Lease source;Taiwan native;
        // LAST: one directed initial publication only. Never attach this proof
        // to the long-lived Taiwan model or derive it from an EA record.
        std::optional<TaiwanActorStatusPublication::ActorUnit> actor_status{};
    };
    class TaiwanInitialPublication {
    public:
        // Only supplied complete native6F records enter the initial reply.
        // Full5E/73 models are retained for later qualified movement/removal.
        std::span<const god2cn::Bytes> records() const;
        // Exact full input models, before optional common first-name projection.
        // Aggregate issuers must match these actual boundaries before replacing
        // them with records(); offsets/other opaque records are never invented.
        std::span<const god2cn::Bytes> supplied_records() const;
        // One slot per ordered actual incoming actor, including legacy nulls.
        // Present units already match the final projected81-byte model; the
        // Entered sender must additionally match its actual adjacent EA bytes.
        std::span<const std::optional<TaiwanActorStatusPublication::ActorUnit>> actor_status() const;
    private:
        friend class SharedActorVisibility;
        struct State;
        explicit TaiwanInitialPublication(std::shared_ptr<State>);
        std::shared_ptr<State> state_;
    };
    // Separate explicit TW source path. The actual scene owner supplies its
    // complete ordered actor set and all native6F/5E/73 models; no guessed peer,
    // handle, resource, name or empty fallback. Recipient's native tail has
    // completed; real scene installation may occur inside held publication.
    // Its common lease remains inactive until that actual publication boundary.
    std::shared_ptr<TaiwanInitialPublication> prepare_initial_taiwan_recipient(const Lease&,
        const std::shared_ptr<Session>&,std::vector<InitialTaiwanActor>);
    bool taiwan_initial_current(const std::shared_ptr<TaiwanInitialPublication>&,
        const std::shared_ptr<Session>&,const Lease&,bool activated) const;
    // Actual held-queue publication activates/binds the same common recipient
    // first. Transfer preallocated nodes only, with no send/save/event pumping.
    bool publish_initial_taiwan(const std::shared_ptr<TaiwanInitialPublication>&,
        const std::shared_ptr<Session>&,const Lease&);
    struct TaiwanAppearanceAfterState {
        // Actual durable authoritative revision/provenance, supplied by the
        // mutation owner. These are not native counters or an approval receipt.
        std::uint64_t source_revision;
        std::string source_record;
        RecoveredTaiwanPlayerAppearanceUpdate::Record update;
        bool operator==(const TaiwanAppearanceAfterState&) const = default;
    };
    enum class TaiwanAppearanceCheck {Prepare,BeforePublish,AfterPublish};
    // Must read the complete committed afterstate at every boundary. No save,
    // mutation, send, yield or event pumping. A bool-only Current is insufficient.
    // The actual equip transaction/provider remains separate and mandatory;
    // parsing DA or supplying an entry baseline never grants this authority.
    using TaiwanAppearanceSource=std::function<std::optional<TaiwanAppearanceAfterState>(TaiwanAppearanceCheck)>;
    using TaiwanAppearanceCompletion=std::function<void(bool)>;
    // One already spawned TW observer, exact private incarnation. CN/mixed
    // fanout, local-self DA and item->appearance rules are not inferred here.
    // Publishes a wire-history receipt before held DA release. It preserves
    // initial6F; neither receipt nor retained6F is a current full actor cache.
    void publish_taiwan_appearance(const Binding&,const RecoveredPosition&,
        TaiwanAppearanceSource,TaiwanAppearanceCompletion);
    // Game owner must drain before stopping executors. Pending operations retain
    // this registry until once-completion; abandoning executors without drain
    // may retain that lifetime. Real Application hosting is still separate.
    void cancel_taiwan_appearance_publications();
    // Only current stored bindings produce movement recipients. Private identity,
    // incarnation, lease generations and exact expected model position are checked.
    std::optional<MovementRecipient> movement(const Binding&,const RecoveredPosition& before) const;
    // Read current expected6F model, never a fabricated bubble/pool allocation.
    // CN tag0 raw or tag1 with qualified native Windows success projection.
    // Private incarnation binds the actual source/recipient and current position.
    std::optional<MainlandChatActor> mainland_chat_actor(const Binding&,const RecoveredPosition&) const;
    // Only actual same-selector no-adaptation native path. Different selector
    // may rewrite the retained6F strings; that postadapted name issuer is OPEN.
    // Full entry/strong receiver copy precedes all real repository/owner reads.
    std::optional<TaiwanChatActor> taiwan_chat_actor(const Binding&,const RecoveredPosition&) const;
    // Registry-only endpoint fence. No repository, scene, raw-name Current or
    // external observer callbacks. Retains complete models and real transport.
    std::optional<ChatActorSnapshot> chat_actor_snapshot(const Binding&,const RecoveredPosition&) const;
    bool chat_actor_snapshot_current(const ChatActorSnapshot&) const;
    // All registered expected observers of this actual source, never all scene
    // peers. A stale incarnation is an explicit failure, not a silently omitted peer.
    std::optional<std::vector<Binding>> movement_bindings(const Lease&,const RecoveredPosition&) const;
    bool complete_movement_set(const Lease&,const RecoveredPosition& model_before,
        const RecoveredPosition& saved_now,std::span<const Binding>) const;
    // Model may still be at before after the durable position CAS. This requires
    // the separately supplied exact saved position rather than assuming no commit.
    bool current(const Binding&,const RecoveredPosition& model_before,const RecoveredPosition& saved_now) const;
    // After5E submission, update retained spawn/move projections for the next step.
    // No allocation or wire send; known fields only, preserving opaque data.
    bool advance(const Binding&,const RecoveredPosition& before,const RecoveredPosition& after);
    bool hide(const Binding&); // Erase incarnation first, then supplied native73.
    // CUSTOM-0113 paired TW PK world departure. Only exact actual private Held
    // transports may mint this receipt, after the common durable activation.
    // It withdraws visibility only: never release common identity/presence,
    // mutate Session/DB, resume world, or imply native73 receipt/atomic fanout.
    class TaiwanPkDeparture {
    public:
        TaiwanPkDeparture(const TaiwanPkDeparture&)=default;
        TaiwanPkDeparture& operator=(const TaiwanPkDeparture&)=default;
        bool operator==(const TaiwanPkDeparture&)const=default;
    private:
        friend class SharedActorVisibility;
        explicit TaiwanPkDeparture(std::shared_ptr<TaiwanPkDepartureState> state):state_(std::move(state)){}
        std::shared_ptr<TaiwanPkDepartureState> state_;
    };
    std::optional<TaiwanPkDeparture> withdraw_taiwan_pk(std::array<Lease,2>,
        std::array<std::shared_ptr<Session>,2>,std::array<Session::NativePkEntryHold,2>);
    // Exact Held OR Committed, PRE-RELEASE only. No Written/terminal-return
    // authority; pending-cleared/released transports deliberately fail.
    bool taiwan_pk_departure_current(const TaiwanPkDeparture&)const;
    // CUSTOM-0130 pure retained registry/transport guards. No repository or
    // callback observations, world resume, marker retirement or native ACK.
    // Binding requires BOTH Committed holds; retained input requires BOTH
    // binding proofs and only this viewer's accepted Written entry.
    bool taiwan_pk_departure_bound_current(const TaiwanPkDeparture&,
        const std::array<Lease,2>&,const std::array<RecoveredPosition,2>&,
        const std::array<std::shared_ptr<Session>,2>&,
        const std::array<Session::NativePkEntryHold,2>&)const;
    bool taiwan_pk_departure_retained_current(const TaiwanPkDeparture&,
        const std::array<Lease,2>&,const std::array<RecoveredPosition,2>&,
        const std::array<std::shared_ptr<Session>,2>&,
        const std::array<Session::NativePkEntryHold,2>&,std::uint8_t viewer)const;
    // CUSTOM-0133 private paired return preallocation, never a WORLD permit.
    // Supplier owns the COMPLETE current ordered scene and resources.
    // CUSTOM-0135/0136 factory-owned role_text_source projects stored text2 and
    // current guild text3; without it the supplier owns both. CUSTOM-0134 projects text1
    // from the actual common stored original using this presence's selected
    // NameSource and canonical
    // receiver_text. Without common_name_source, supplier owns native text1.
    // Old bindings/DA projections cannot supply a full actor.
    struct TaiwanReturnQualification {
        std::uint64_t revision;
        // Pure actual issuer: full record/resource/text/selection provenance.
        std::function<bool()> current;
        // One actual receiving native profile owner, shared across duplicate
        // mutual-edge inputs. Legacy native.raw_name_state is not authority.
        // Absence selects the concrete same-Session accepted C1C producer:
        // exact private return preparation for returners, Written current INIT
        // for survivors. That typed source permits only same-page6F.
        std::shared_ptr<const TaiwanRawNameState> receiver_text;
    };
    // CUSTOM-0133 explicit current remote override after full6F recreation.
    // Native4FC214/4FC222 reset type/index to0. Explicit absence therefore
    // needs no EA; a supplied exact original EA is replayed AFTER that6F.
    // This immutable source is not reconstructed from a normalized index,
    // an old visibility model, or an assumed missing-packet default.
    class TaiwanReturnActorOverride {
    public:
        explicit TaiwanReturnActorOverride(std::optional<RecoveredTaiwanActorOverride::Record> actual_replay)
            :replay_(std::move(actual_replay)) {}
        const std::optional<RecoveredTaiwanActorOverride::Record>& replay()const noexcept {return replay_;}
    private:
        const std::optional<RecoveredTaiwanActorOverride::Record> replay_;
    };
    struct TaiwanReturnActor {
        Lease source,recipient;
        RecoveredPosition source_position,recipient_position;
        std::shared_ptr<Session> source_connection;
        Taiwan native; // Exact receiving connection plus complete6F/5E/73.
        std::shared_ptr<const TaiwanReturnQualification> qualification;
        // Mandatory explicit current absence or original raw EA witness.
        // qualification.current and whole scene.current own this exact state,
        // including marker resources, at Prepare/Retained/Consumed. Duplicate
        // mutual copies must share THIS witness, not just equal bytes.
        std::shared_ptr<const TaiwanReturnActorOverride> actor_override;
        // LAST: same private owned-status/whole-unit witness. Absent only for
        // the preserved external status provider, never a failed typed mint.
        std::optional<TaiwanActorStatusPublication::ActorUnit> status_publication{};
    };
    enum class TaiwanReturnCheck {Prepare,Retained,Consumed};
    struct TaiwanReturnScene {
        std::array<std::vector<TaiwanReturnActor>,2> incoming,outgoing;
        // Mandatory pure full readset: exact complete ordered sets (including
        // deliberate empties), every source/recipient common root/saved pose,
        // qualification revision/resource availability and receiver_text
        // profile. Supplier owns text1 unless common_name_source supplies it;
        // it owns text2/text3 unless role_text_source supplies them.
        // Actual common name projection remains in this full readset.
        // Concrete text2/guild rows and CUSTOM-0137 current common endpoint
        // roots/poses are jointly requalified in one final snapshot, including
        // both participants even if this ordered scene has no actor edges.
        // Consumed must qualify the same complete bytes/readset against the
        // actual successor identities. A provider retaining old PK predicates
        // must reject, never silently reuse the preparation as current material.
        // Requalifies ALL supplier-owned inputs together,
        // after per-edge observers. No yield/mutation/send/event pumping.
        std::function<bool(TaiwanReturnCheck)> current;
        // CUSTOM-0135/0136 only the same-DB factory can create this owner.
        // Complete saved rows and confirmed guild absence stay distinct from
        // read failure; all share the final snapshot and retained guild epoch.
        std::shared_ptr<god2::OwnedTaiwanPkReturnRoleTextSource> role_text_source;
        // CUSTOM-0133 full stored actor population from the actual same-DB
        // factory. Either all three values are present or all are absent.
        // Readset rows must match the private complete ready population, while
        // directed visible edges remain the complete supplier's scene policy.
        std::optional<SharedWorldPresence::ReadyPopulation> ready_population;
        std::shared_ptr<god2::OwnedTaiwanReturnActorSavedSource> actor_saved_source;
        std::optional<god2::OwnedTaiwanReturnActorSavedSource::Readset> actor_saved_rows;
        // Exact backend-issued input node for the typed complete supplier.
        std::shared_ptr<const god2::OwnedTaiwanReturnActorSavedSource::PopulationInput> actor_input={};
        // Only rendering-selected rows need this genuine same-writers joined
        // equipment witness. Its absence never manufactures appearance.
        std::vector<god2::OwnedTaiwanReturnActorSavedSource::ProfileEquipment> actor_profile_equipment;
        // Set by the actual backend for its typed-input supplier only. Legacy
        // complete suppliers retain their existing appearance/source contract.
        bool actor_profile_equipment_required=false;
    };
    class TaiwanPkReturnPlan {
    public:
        TaiwanPkReturnPlan(const TaiwanPkReturnPlan&)=default;
        TaiwanPkReturnPlan& operator=(const TaiwanPkReturnPlan&)=default;
    private:
        friend class SharedActorVisibility;
        struct State;
        explicit TaiwanPkReturnPlan(std::shared_ptr<State> state):state_(std::move(state)){}
        std::shared_ptr<State> state_;
    };
    std::optional<TaiwanPkReturnPlan> prepare_taiwan_pk_return(const TaiwanPkDeparture&,
        std::array<Lease,2>,std::array<RecoveredPosition,2>,
        std::array<std::shared_ptr<Session>,2>,std::array<Session::NativePkEntryHold,2>,
        std::array<Session::NativePkReturnPreparation,2>,TaiwanReturnScene);
    bool taiwan_pk_return_current(const TaiwanPkReturnPlan&)const;
    // CUSTOM-0136/0137 joint text/guild/current-root/pose cut AFTER terminal ledger
    // reads. No scene/name/profile/presence observers; pure fences follow.
    bool taiwan_pk_return_stored_current(const TaiwanPkReturnPlan&)const;
    // Registry/Session only, for the final cut after actual read-only ledger
    // qualification. This does not refresh resource/text/saved-position data.
    bool taiwan_pk_return_retained_current(const TaiwanPkReturnPlan&)const;
    // CUSTOM-0133 immutable full6F return subset, bound to the exact private
    // plan and reserved pair. No send/merge/consume/WORLD or input permission.
    class TaiwanPkReturnRecords {
    public:
        class Record {
        public:
            const Lease& source() const noexcept {return source_;}
            const Lease& recipient() const noexcept {return recipient_;}
            const std::shared_ptr<Session>& source_session() const noexcept {return source_session_;}
            const std::shared_ptr<Session>& recipient_session() const noexcept {return recipient_session_;}
            const std::vector<std::uint8_t>& logical() const noexcept {return logical_;}
            const std::optional<RecoveredTaiwanActorOverride::LogicalRecord>& override_logical()const noexcept {
                return override_logical_;
            }
            const std::optional<TaiwanActorStatusPublication::ActorUnit>& status_publication()const noexcept {
                return status_publication_;
            }
        private:
            friend class SharedActorVisibility;
            Record(Lease source,Lease recipient,std::shared_ptr<Session> from,
                std::shared_ptr<Session> to,std::vector<std::uint8_t> logical,
                std::optional<RecoveredTaiwanActorOverride::LogicalRecord> actor_override,
                std::optional<TaiwanActorStatusPublication::ActorUnit> status_publication)
                :source_(std::move(source)),recipient_(std::move(recipient)),
                 source_session_(std::move(from)),recipient_session_(std::move(to)),logical_(std::move(logical)),
                 override_logical_(std::move(actor_override)),status_publication_(std::move(status_publication)){}
            Lease source_,recipient_;
            std::shared_ptr<Session> source_session_,recipient_session_;
            std::vector<std::uint8_t> logical_;
            std::optional<RecoveredTaiwanActorOverride::LogicalRecord> override_logical_;
            std::optional<TaiwanActorStatusPublication::ActorUnit> status_publication_;
        };
        TaiwanPkReturnRecords(const TaiwanPkReturnRecords&)=default;
        TaiwanPkReturnRecords& operator=(const TaiwanPkReturnRecords&)=default;
        bool operator==(const TaiwanPkReturnRecords&)const=default;
        const std::vector<Record>& records() const noexcept;
    private:
        friend class SharedActorVisibility;
        struct State;
        explicit TaiwanPkReturnRecords(std::shared_ptr<const State> state):state_(std::move(state)){}
        std::shared_ptr<const State> state_;
    };
    std::optional<TaiwanPkReturnRecords> prepare_taiwan_pk_return_records(
        const TaiwanPkReturnPlan&,const Session::NativePkReturnReservation&);
    bool taiwan_pk_return_records_current(const TaiwanPkReturnRecords&)const;
    bool taiwan_pk_return_records_stored_current(const TaiwanPkReturnRecords&)const;
    bool taiwan_pk_return_records_retained_current(const TaiwanPkReturnRecords&)const;
    bool taiwan_pk_return_records_matches(const TaiwanPkReturnRecords&,const TaiwanPkReturnPlan&,
        const Session::NativePkReturnReservation&)const;
    // Only the actual private records/plan/pair may nominate recipients for
    // the distinct held transport. This prepares no WORLD/visibility release.
    std::optional<Session::NativePkReturnOutputPlan> prepare_taiwan_pk_return_output(
        const TaiwanPkReturnRecords&,const TaiwanPkReturnPlan&,const Session::NativePkReturnReservation&);
    bool taiwan_pk_return_output_plan_matches(const TaiwanPkReturnRecords&,
        const Session::NativePkReturnOutputPlan&,const TaiwanPkReturnPlan&,
        const Session::NativePkReturnReservation&)const;
    // CUSTOM-0133 provisional return commit. Exact private Held cohort only;
    // future Session identities and prepared model nodes, with frames/input held.
    class TaiwanPkReturnConsumption {
    public:
        TaiwanPkReturnConsumption(const TaiwanPkReturnConsumption&)=default;
        TaiwanPkReturnConsumption& operator=(const TaiwanPkReturnConsumption&)=default;
    private:
        friend class SharedActorVisibility;
        struct State;
        explicit TaiwanPkReturnConsumption(std::shared_ptr<State> state):state_(std::move(state)){}
        std::shared_ptr<State> state_;
    };
    std::optional<TaiwanPkReturnConsumption> prepare_taiwan_pk_return_consumption(
        const TaiwanPkReturnRecords&,const TaiwanPkReturnPlan&,const Session::NativePkReturnReservation&,
        const Session::NativePkReturnOutputPlan&,const Session::NativePkReturnOutputHold&,
        std::weak_ptr<Session::NativePkReturnConsumptionOwner>);
    bool consume_taiwan_pk_return(const TaiwanPkReturnConsumption&);
    bool taiwan_pk_return_consumption_current(const TaiwanPkReturnConsumption&)const;
    bool taiwan_pk_return_consumption_source_current(const TaiwanPkReturnConsumption&)const;
    bool taiwan_pk_return_consumption_stored_current(const TaiwanPkReturnConsumption&)const;
    bool taiwan_pk_return_consumption_stored_in_scope(const TaiwanPkReturnConsumption&,sqlite3*)const;
    std::optional<Session::NativePkReturnFinalisation> prepare_taiwan_pk_return_finalisation(
        const TaiwanPkReturnConsumption&,const Session::NativePkReturnPublication&,
        std::weak_ptr<Session::NativePkReturnFinalisationOwner>);
    bool taiwan_pk_return_finalisation_matches(const TaiwanPkReturnConsumption&,
        const Session::NativePkReturnFinalisation&)const;
    bool taiwan_pk_return_finalisation_identity_matches(const TaiwanPkReturnConsumption&,
        const Session::NativePkReturnFinalisation&)const noexcept;
    bool acquire_taiwan_pk_return_finalisation(const TaiwanPkReturnConsumption&,
        const Session::NativePkReturnFinalisation&);
    bool finish_taiwan_pk_return_visibility(const TaiwanPkReturnConsumption&,
        const Session::NativePkReturnFinalisation&);
    std::optional<Session::NativePkReturnPublication> prepare_taiwan_pk_return_publication(
        const TaiwanPkReturnConsumption&,std::weak_ptr<Session::NativePkReturnPublicationOwner>);
    bool taiwan_pk_return_publication_matches(const TaiwanPkReturnConsumption&,
        const Session::NativePkReturnPublication&)const;
    bool taiwan_pk_return_publication_identity_matches(const TaiwanPkReturnConsumption&,
        const Session::NativePkReturnPublication&)const noexcept;
    bool release_taiwan_pk_return_publication(const TaiwanPkReturnConsumption&,
        const Session::NativePkReturnPublication&);
    // Failure matching is exact identity even after Current has retired.
    bool taiwan_pk_return_consumption_matches_transport(const TaiwanPkReturnConsumption&,
        const Session::NativePkReturnConsumption&)const noexcept;
    void cancel_taiwan_pk_return_consumption(const TaiwanPkReturnConsumption&)noexcept;
    void reset_recipient(const Lease&); // Actual native pool reset: invalidate incoming bindings, no invented packets.
    // Generation-qualified source/recipient disconnect or failed-entry cleanup.
    // Departing recipients receive nothing; surviving peers get stored73 when
    // still bound to the old scene. No stale cleanup can remove a successor.
    void release(const Lease&);
private:
    void cancel_taiwan_pk_return_consumption_state(TaiwanPkReturnConsumption::State&)noexcept;
    bool taiwan_pk_return_status_unit_matches(const TaiwanReturnActor&)const noexcept;
    bool taiwan_pk_return_records_fence(const std::shared_ptr<const TaiwanPkReturnRecords::State>&)const;
    bool taiwan_pk_return_fence(const std::shared_ptr<TaiwanPkReturnPlan::State>&)const;
    bool taiwan_pk_return_population_fence(const std::shared_ptr<TaiwanPkReturnPlan::State>&)const;
    bool taiwan_pk_return_read(const std::shared_ptr<TaiwanPkReturnPlan::State>&,TaiwanReturnCheck,
        bool stored_only=false,const std::shared_ptr<TaiwanPkReturnConsumption::State>& successor={},
        sqlite3* in_scope=nullptr)const;
    bool taiwan_pk_return_consumption_fence(const std::shared_ptr<TaiwanPkReturnConsumption::State>&,
        bool guarded_read=false)const;
    void reject_taiwan_return_reentry()const;
    bool taiwan_pk_return_pending(const std::shared_ptr<TaiwanPkReturnPlan::State>&)const;
    bool taiwan_pk_departed(const Lease&)const noexcept;
    bool taiwan_pk_departure_fence(const std::shared_ptr<TaiwanPkDepartureState>&,
        bool installed,bool held_only)const;
    bool taiwan_pk_departure_exact_current(const TaiwanPkDeparture&,
        const std::array<Lease,2>&,const std::array<RecoveredPosition,2>&,
        const std::array<std::shared_ptr<Session>,2>&,
        const std::array<Session::NativePkEntryHold,2>&,bool retained,std::uint8_t viewer)const;
    struct Entry {
        Binding binding;RecoveredPosition position;Native native;
        std::shared_ptr<const TaiwanAppearanceAfterState> last_taiwan_appearance;
    };
    using Key=std::pair<std::uint64_t,std::uint64_t>;
    bool taiwan_pk_return_models_match(const std::map<Key,Entry>&)const;
    struct TaiwanAppearanceState;
    bool taiwan_appearance_pending(const Key&) const;
    bool taiwan_appearance_fence(const std::shared_ptr<TaiwanAppearanceState>&,bool published) const;
    bool taiwan_appearance_check(const std::shared_ptr<TaiwanAppearanceState>&,TaiwanAppearanceCheck,bool published);
    void finish_taiwan_appearance(const std::shared_ptr<TaiwanAppearanceState>&,bool accepted);
    void cancel_taiwan_appearance(const Lease&);
    struct OutwardState;
    bool outward_pending(const Lease&) const;
    bool outward_current(const std::shared_ptr<OutwardState>&,std::size_t,bool published) const;
    void finish_outward(const std::shared_ptr<OutwardState>&,bool accepted);
    void cancel_outward(const Lease&);
    void owner() const;
    bool normal_source_matches(const Lease&,const Mainland&) const;
    bool project_common_name(const Lease&,const Lease&,Native&) const;
    bool common_name_current(const Lease&,const Lease&,const Native&) const;
    bool matches(const Binding&,const Entry&) const;
    bool movement_models_stored_current(const Lease&,std::span<const ChatActorSnapshot>) const;
    bool recipient_bound(const Lease&,const Native&,const RecoveredPosition&) const;
    bool submit(Native&,std::vector<std::uint8_t>);
    void reject_output(const Lease&,Native&);
    std::thread::id thread_=std::this_thread::get_id();
    std::shared_ptr<const Identity> identity_=std::make_shared<const Identity>();
    std::shared_ptr<SharedWorldPresence> presence_;
    std::uint64_t generation_=0; // Integration incarnation, not a native counter.
    std::map<Key,Entry> entries_;
    std::map<std::uint64_t,std::weak_ptr<OutwardState>> outward_;
    std::map<Key,std::shared_ptr<TaiwanAppearanceState>> taiwan_appearance_;
    std::uint64_t taiwan_appearance_generation_=0;
    bool taiwan_appearance_cancelling_=false;
    mutable bool taiwan_chat_busy_=false,taiwan_chat_reentered_=false;
    mutable bool current_busy_=false,current_reentered_=false;
    std::map<std::uint64_t,std::shared_ptr<TaiwanPkDepartureState>> taiwan_pk_departures_;
    // Weak game-owned successor registrations; no registry/token cycle.
    std::map<std::uint64_t,std::weak_ptr<TaiwanPkReturnConsumption::State>> taiwan_pk_return_consumptions_;
    std::shared_ptr<TaiwanPkDepartureState> taiwan_pk_withdrawing_;
    mutable bool taiwan_pk_reading_=false,taiwan_pk_reentered_=false;
    mutable bool taiwan_return_reading_=false,taiwan_return_reentered_=false;
};
}
