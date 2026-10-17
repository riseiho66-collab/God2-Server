#pragma once
#include "shared/world/SharedActorVisibility.h"
#include "game/SharedNativeWorldTransports.h"
#include "game/SharedPublishedChatNameSource.h"
#include "text/ChineseText.h"
#include "text/LegacyChineseCodec.h"
#include "game/SharedTaiwanWorldRecordSource.h"
#include "game/SharedChatIdentitySource.h"

namespace god2 {
// Explicit native TW2F source. The actual owner qualifies the complete retained
// request and native prose domain; no GM/control/header becomes common chat.
class SharedTaiwanNativeChatSource final {
public:
    using Lease=SharedWorldPresence::Lease;
    enum class WireCodePage {CP950,CP936};
    struct Delivery {
        Lease recipient;
        std::variant<std::weak_ptr<Session>> transport;
        WireCodePage code_page;
        ChineseLanguage preference;
        std::uint8_t native_consumer_tag;
        std::vector<std::uint8_t> full_native_reply;
        std::size_t body_offset,body_size;
        std::string original_body_utf8;
        std::optional<shared::SharedActorVisibility::Binding> visible_peer;
        bool use_common_transport=false;
    };
    struct Prepared {
        std::size_t delivery_index;
        std::vector<std::uint8_t> record;
        std::size_t replacements;
        bool truncated;
    };
    using Reply=SharedTaiwanWorldRecordSource::Reply;
    enum class NativeContent {PlayerText,NamedWhisper};
    struct Input {
        NativeContent kind;
        WireCodePage wire_code_page;
        std::string original_utf8;
        std::size_t body_offset,body_size; // Actual original request wire body.
        std::string body_utf8;
        // Filled by this source after actual native input/provenance qualifies.
        // Exact common ready-name observation, never a native actor or right.
        std::optional<SharedChatIdentitySource::Lookup> named_target;
        std::optional<SharedPublishedChatNameSource::Witness> published_target;
    };
    struct Scope {
        Lease lease;
        RecoveredPosition saved_position;
        SessionState phase;
        std::uint64_t battle_generation;
        std::size_t submitted_recipients;
    };
    struct Publication {
        std::uint64_t source_revision;
        std::vector<Delivery> deliveries;
        bool explicit_no_additional_sender_reply; // Mandatory actual decision.
        // Real target->sender published-peer name incarnation, if this native
        // namespace is selected. Manual/offline/other domains stay qualified
        // separately; missing binding is never implicit name/actor permission.
        std::optional<shared::SharedActorVisibility::Binding> named_peer;
    };
    enum class Check {Resolved,Prepared,BeforeRecipient,AfterRecipient,BeforeReturn};
    struct Budgets {
        std::size_t max_original_utf8_bytes,max_projected_utf8_bytes;
        std::size_t max_deliveries,max_output_bytes;
    };
    struct SenderPrepared {
        std::size_t delivery_index;
        std::vector<std::uint8_t> encrypted;
    };
    class WorldOwner {
    public:
        virtual ~WorldOwner()=default;
        // Real native ordinary/whisper domain, wire profile and body boundaries.
        // Complete raw client_header/text retain names, commands and identity.
        // Unsupported GM/control/unknown branches have no player-prose fallback.
        virtual std::optional<Input> input(const Scope&,const RecoveredChat::Request&)=0;
        // Internal named_target is supplied after input(). The real issuer must
        // bind typed/history/peer names to the common full64-bit ready lease;
        // native15-byte targets and history names are not the common14-byte
        // stored-name domain. No truncation, alias/marker inference or rights
        // follow from a lookup result. Actual body grammar remains input's duty.
        virtual std::optional<Publication> resolve(const Scope&,const RecoveredChat::Request&,const Input&)=0;
        // Observers never yield/send/write/pump or retain borrowed arguments.
        // Actual permission/audience/rate/mute/native fields/resources/window
        // and same publication source revision remain this owner's obligation.
        virtual bool current(const Scope&,Check,const RecoveredChat::Request&,const Input&,const Publication&)=0;
        // Actual same Session cipher/framing profile, exact prepared logical5C.
        // No default zero-seed laboratory encoder, rekey or guessed handshake.
        virtual std::optional<std::vector<std::uint8_t>> sender_wire(const Scope&,const Prepared&)=0;
        // Includes true TW peer bubble authority,
        // all recipient native destination windows and full projected outputs.
        virtual bool qualify_delivery(const Scope&,const RecoveredChat::Request&,const Input&,
            const Publication&,const std::vector<Prepared>&,const std::vector<SenderPrepared>&)=0;
    };
    struct Binding {
        // Sender envelopes return to the ordered mixed dispatcher; never sent
        // ahead of its earlier pending movement/other reply. Peer sends observe
        // source submission only, not atomic fanout or native client acceptance.
        std::function<std::optional<Reply>(Session&,const RecoveredChat::Request&)> dispatch;
        std::function<void(Session&)> release; // Own exact Session bookkeeping.
        std::function<void()> invalidate_active;
    };
    static Binding create(std::shared_ptr<SharedWorldPresence>,std::shared_ptr<shared::SharedActorVisibility>,
        std::shared_ptr<WorldOwner>,std::shared_ptr<const ChineseText>,Budgets,std::size_t actual_session_capacity,
        std::shared_ptr<SharedNativeWorldTransports> = {});
};
}
