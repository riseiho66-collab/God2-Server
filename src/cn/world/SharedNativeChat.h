#pragma once
#include "cn/net/SharedCredentialConnection.h"
#include "cn/text/CnChatContent.h"
#include "cn/world/SharedActorVisibility.h"
#include "game/SharedWorldPresence.h"
#include "game/SharedNativeWorldTransports.h"
#include "game/SharedChatIdentitySource.h"
#include "game/SharedPublishedChatNameSource.h"
#include "net/Session.h"
#include "text/ChineseText.h"
#include "text/LegacyChineseCodec.h"
#include <variant>

namespace god2::cn {
// Conditional native chat owner, not a production audience/rule implementation.
// Full recipient headers and actual body boundaries come from real authority.
class SharedNativeChat:public std::enable_shared_from_this<SharedNativeChat> {
public:
    ~SharedNativeChat();
    using Connection=SharedCredentialConnection;
    using Lease=SharedWorldPresence::Lease;
    enum class WireCodePage {CP950,CP936};
    struct Input {
        god2cn::CnChatContent::Kind kind;
        std::string target_wire_name; // Identity: never script-convert.
        std::string body_utf8; // Original, distinct from recipient presentation.
        // Internally sourced exact common ready-name observation. It supplies
        // neither native actor mapping nor send rights; WorldOwner qualifies
        // native namespace and handles missing/ambiguous targets explicitly.
        std::optional<SharedChatIdentitySource::Lookup> named_target;
        // Internally qualified only when resolve supplies the actual issued
        // common-peer binding. Other native namespaces remain Owner authority.
        std::optional<SharedPublishedChatNameSource::Witness> published_target;
    };
    struct Delivery {
        Lease recipient;
        std::variant<std::weak_ptr<Connection>,std::weak_ptr<Session>> transport;
        WireCodePage code_page;
        ChineseLanguage preference;
        std::uint8_t native_consumer_tag;
        god2cn::Bytes full_native_reply; // Opaque actor/header/prefix retained.
        std::size_t body_offset,body_size; // Relative to native text offset13.
        std::string original_body_utf8; // Authority proof, not decoded lossy output.
        // Required for ordinary CN0/6 peer bubble publication. A real preceding
        // visibility.show supplies this private token; same scene is insufficient.
        std::optional<SharedActorVisibility::Binding> visible_peer;
        // Explicit real common destination source. Core fills weak transport
        // before Current; audience/rights/full header/text remain Owner inputs.
        bool use_common_transport=false;
    };
    struct Publication {
        std::uint64_t source_revision;
        std::vector<Delivery> deliveries;
        // Explicit actual target -> sender visibility incarnation, never an
        // inferred same-map/name join. Absence grants no alternative namespace.
        std::optional<SharedActorVisibility::Binding> named_peer;
    };
    struct Prepared {
        std::size_t delivery_index;
        god2cn::Bytes record;
        std::size_t replacements;
        bool truncated;
    };
    class WorldOwner {
    public:
        virtual ~WorldOwner()=default;
        // Real scope/permission/name lookup/mute/rate/native actor and bubble
        // ordering. No inferred same-map broadcast, CUSTOM guild or ID mapping.
        // Named input includes only a common ready-root observation. Qualify
        // the actual issued native name namespace and full lease separately;
        // a match is not an actor DWORD/private WORD or recipient permission.
        // NoReadyMatch is not global/offline absence or an invented error reply.
        virtual std::optional<Publication> resolve(const Lease&,const god2cn::CnChat::Request&,const Input&)=0;
        // Observes only: no sends, writes, yield or event pumping. Real CN
        // phase/tickets/loaded native windows/profile remain this owner's
        // authority; this connection API supplies no battle-generation getter.
        virtual bool current(const Lease&,const Publication&)=0;
        // Qualify complete native headers, real text body boundaries, audience,
        // recipient state, loaded native destination capacity and conversions.
        virtual bool qualify_delivery(const Lease&,const god2cn::CnChat::Request&,const Input&,
            const Publication&,const std::vector<Prepared>&)=0;
    };
    static std::shared_ptr<SharedNativeChat> attach(const std::shared_ptr<Connection>&,
        std::shared_ptr<SharedWorldPresence>,const Lease&,std::shared_ptr<SharedActorVisibility>,
        std::shared_ptr<WorldOwner>,std::shared_ptr<const ChineseText>,
        std::shared_ptr<SharedNativeWorldTransports> = {});
    static bool supported_request(std::span<const std::uint8_t>);
    Connection::Ingress ingress();
    // Actual ongoing gameplay facade calls this before rejecting nested ingress.
    // Game owner only; terminalize an active operation, no common cleanup.
    void invalidate_active();
private:
    SharedNativeChat(const std::shared_ptr<Connection>&,std::shared_ptr<SharedWorldPresence>,
        const Lease&,std::shared_ptr<SharedActorVisibility>,std::shared_ptr<WorldOwner>,std::shared_ptr<const ChineseText>,
        std::shared_ptr<SharedNativeWorldTransports>);
    struct SourceState {std::shared_ptr<Connection> connection;RecoveredPosition position;};
    struct RecipientState {
        std::variant<std::shared_ptr<Connection>,std::shared_ptr<Session>> transport;
        RecoveredPosition position;
        std::optional<SessionState> taiwan_phase;
        std::uint64_t taiwan_battle_generation;
    };
    void owner() const;
    bool current() const;
    std::optional<SourceState> source_state() const;
    bool source_current(const SourceState&) const;
    bool recipient_current(const Delivery&) const;
    std::optional<RecipientState> recipient_state(const Delivery&) const;
    bool recipient_current(const Delivery&,const RecipientState&) const;
    bool peer_current(const Delivery&,const RecoveredPosition&,std::span<const std::uint8_t>) const;
    bool dispatch(const god2cn::CnChat::Request&);
    void receive(god2cn::Bytes,Connection::Transport::Completion);
    std::thread::id thread_=std::this_thread::get_id();
    std::weak_ptr<Connection> connection_;
    std::shared_ptr<SharedWorldPresence> presence_;
    Lease lease_;
    std::shared_ptr<SharedActorVisibility> visibility_;
    std::shared_ptr<SharedChatIdentitySource> identities_;
    std::shared_ptr<SharedPublishedChatNameSource> published_names_;
    std::shared_ptr<WorldOwner> world_;
    std::shared_ptr<const ChineseText> text_;
    std::shared_ptr<SharedNativeWorldTransports> transports_;
    bool busy_=false,terminal_=false;
};
}
