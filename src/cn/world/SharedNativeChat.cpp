#include "cn/world/SharedNativeChat.h"
#include "cn/protocol/CnChatConsumerContract.h"
#include "protocol/RecoveredTaiwanChatConsumerContract.h"
#include <exception>
#include <set>
#include <stdexcept>
#include <utility>
#include <type_traits>

namespace god2::cn {
SharedNativeChat::SharedNativeChat(const std::shared_ptr<Connection>& connection,
    std::shared_ptr<SharedWorldPresence> presence,const Lease& lease,std::shared_ptr<SharedActorVisibility> visibility,std::shared_ptr<WorldOwner> world,
    std::shared_ptr<const ChineseText> text,std::shared_ptr<SharedNativeWorldTransports> transports):connection_(connection),presence_(std::move(presence)),
    lease_(lease),visibility_(std::move(visibility)),identities_(SharedChatIdentitySource::create(presence_)),
    published_names_(SharedPublishedChatNameSource::create(identities_,presence_,visibility_)),
    world_(std::move(world)),text_(std::move(text)),transports_(std::move(transports)) {}
SharedNativeChat::~SharedNativeChat() {
    if(thread_!=std::this_thread::get_id())std::terminate();
    busy_=true;terminal_=true;
    world_.reset();text_.reset();transports_.reset();published_names_.reset();visibility_.reset();identities_.reset();presence_.reset();
}
void SharedNativeChat::owner() const {
    if(thread_!=std::this_thread::get_id())throw std::logic_error("CN chat game owner mismatch");
}
bool SharedNativeChat::current() const {
    owner();
    if(terminal_)return false;
    const auto c=connection_.lock();
    const auto actual=presence_->ready_lease(lease_.session,lease_.account,lease_.character);
    return c && !c->closing() && c->role()==Connection::Transport::Role::World &&
        c->world_admission_current() && actual && *actual==lease_ &&
        c->world_session_id()==lease_.session && c->verified_account_id()==lease_.account &&
        c->world_character_offered(lease_.character) && presence_->ready(lease_);
}
std::optional<SharedNativeChat::SourceState> SharedNativeChat::source_state() const {
    if(!current())return std::nullopt;
    const auto position=presence_->saved_position(lease_);const auto connection=connection_.lock();
    if(!position || !connection)return std::nullopt;
    return SourceState{connection,*position};
}
bool SharedNativeChat::source_current(const SourceState& retained) const {
    const auto actual=source_state();
    return actual && actual->connection==retained.connection && actual->position==retained.position;
}
void SharedNativeChat::invalidate_active() {
    owner();if(busy_)terminal_=true;
}
std::shared_ptr<SharedNativeChat> SharedNativeChat::attach(const std::shared_ptr<Connection>& c,
    std::shared_ptr<SharedWorldPresence> p,const Lease& l,std::shared_ptr<SharedActorVisibility> v,
    std::shared_ptr<WorldOwner> w,std::shared_ptr<const ChineseText> t,std::shared_ptr<SharedNativeWorldTransports> transports) {
    if(!c || !p || !v || !v->owns_presence(p) || !w || !t || (transports && !transports->owns_presence(p)))return {};
    auto self=std::shared_ptr<SharedNativeChat>(new SharedNativeChat(c,std::move(p),l,std::move(v),std::move(w),std::move(t),std::move(transports)));
    self->owner();return self->current()?self:std::shared_ptr<SharedNativeChat>{};
}
bool SharedNativeChat::supported_request(std::span<const std::uint8_t> record) {
    const auto request=god2cn::CnChat::parse(record);if(!request)return false;
    const auto content=god2cn::CnChatContent::split(*request);
    return content.kind==god2cn::CnChatContent::Kind::PlayerText ||
        content.kind==god2cn::CnChatContent::Kind::NamedWhisper;
}
bool SharedNativeChat::recipient_current(const Delivery& d) const {
    const auto actual=presence_->ready_lease(d.recipient.session,d.recipient.account,d.recipient.character);
    if(!actual || *actual!=d.recipient || d.native_consumer_tag>1 ||
       (d.code_page!=WireCodePage::CP950 && d.code_page!=WireCodePage::CP936) ||
       (d.preference!=ChineseLanguage::Traditional && d.preference!=ChineseLanguage::Simplified))return false;
    if(const auto cn=std::get_if<std::weak_ptr<Connection>>(&d.transport)) {
        const auto c=cn->lock();
        // Pinned405A30 returns0. This unhosted adapter's explicit CN profile
        // selectsCP936 independently; that bit alone does not prove a wire
        // codepage. Actual receiver/text fields still need WorldOwner qualification.
        return c && !c->closing() && c->role()==Connection::Transport::Role::World &&
            c->world_admission_current() &&
            c->world_session_id()==d.recipient.session && c->verified_account_id()==d.recipient.account &&
            c->world_character_offered(d.recipient.character) && d.code_page==WireCodePage::CP936 &&
            d.native_consumer_tag==0;
    }
    const auto c=std::get<std::weak_ptr<Session>>(d.transport).lock();
    // Actual wire profile is d.code_page qualified above and by WorldOwner;
    // the native consumer tag never selects its encoding.
    return c && !c->closing() && c->recovered_world_ready() && c->id()==d.recipient.session &&
        c->account_id==d.recipient.account && c->character_id==d.recipient.character &&
        (c->state()==SessionState::InWorld || c->state()==SessionState::InBattle) &&
        c->common_world_delivery_current(d.recipient.account,d.recipient.character,d.recipient.generation) &&
        !c->common_world_entry_current(d.recipient.account,d.recipient.character,d.recipient.generation) &&
        c->recovered_client_language()<=1 && d.native_consumer_tag==c->recovered_client_language();
}
std::optional<SharedNativeChat::RecipientState> SharedNativeChat::recipient_state(const Delivery& delivery) const {
    if(!recipient_current(delivery))return std::nullopt;
    const auto position=presence_->saved_position(delivery.recipient);if(!position)return std::nullopt;
    if(const auto native=std::get_if<std::weak_ptr<Connection>>(&delivery.transport)) {
        const auto connection=native->lock();if(!connection)return std::nullopt;
        // This CN connection API has no battle-generation getter. Actual CN
        // phase/ticket/formatter state remains mandatory WorldOwner Current.
        return RecipientState{connection,*position,std::nullopt,0};
    }
    const auto connection=std::get<std::weak_ptr<Session>>(delivery.transport).lock();if(!connection)return std::nullopt;
    return RecipientState{connection,*position,connection->state(),connection->battle_generation()};
}
bool SharedNativeChat::recipient_current(const Delivery& delivery,const RecipientState& retained) const {
    const auto actual=recipient_state(delivery);
    return actual && actual->transport==retained.transport && actual->position==retained.position &&
        actual->taiwan_phase==retained.taiwan_phase && actual->taiwan_battle_generation==retained.taiwan_battle_generation;
}
bool SharedNativeChat::peer_current(const Delivery& d,const RecoveredPosition& position,
    std::span<const std::uint8_t> record) const {
    const auto cn=std::get_if<std::weak_ptr<Connection>>(&d.transport);
    if(!cn)return !d.visible_peer; // No CN-as-TW chat identity equivalence claim.
    const auto reply=god2cn::CnChat::read_reply(record);if(!reply)return false;
    const bool peer_bubble=(reply->channel()==0 || reply->channel()==6) && d.recipient!=lease_;
    if(!peer_bubble)return !d.visible_peer; // Self/non-bubble authority remains separate.
    if(!d.visible_peer || d.visible_peer->source()!=lease_ || d.visible_peer->recipient()!=d.recipient)return false;
    const auto actor=visibility_->mainland_chat_actor(*d.visible_peer,position);
    if(!actor || actor->connection.lock()!=cn->lock() || actor->native_actor_identity!=reply->actor())return false;
    const auto raw=reply->text();const auto prefix=actor->native_name_bytes+": ";
    // Native ordinary peer text only. Board/named-control branches need their
    // own state/formatter owners; never script-convert them as player prose.
    return raw.starts_with(prefix) && d.body_offset==prefix.size() &&
        d.body_size<=raw.size()-prefix.size() && raw.size()==prefix.size()+d.body_size &&
        raw.find(": /board ")==std::string_view::npos && raw.find(": $")==std::string_view::npos;
}
bool SharedNativeChat::dispatch(const god2cn::CnChat::Request& request) {
    const auto source=source_state();if(!source)return false;
    const auto content=god2cn::CnChatContent::split(request);
    if(content.kind!=god2cn::CnChatContent::Kind::PlayerText &&
       content.kind!=god2cn::CnChatContent::Kind::NamedWhisper)return false;
    Input input{content.kind,std::string(content.target_wire_name),
        LegacyChineseCodec::decode(content.body_wire_text,true),std::nullopt,std::nullopt};
    if(!ChineseText::valid_utf8(input.body_utf8))return false;
    if(content.kind==god2cn::CnChatContent::Kind::NamedWhisper) {
        input.named_target=identities_->lookup(input.target_wire_name,936);
        if(!input.named_target || !source_current(*source))return false;
        // This is the common ready-name observation only. Actual native name
        // namespace/publication binding, audience and replies remain resolve's
        // obligation, including every explicit non-matching lookup result.
    }
    auto publication=world_->resolve(lease_,request,input);
    if(!publication || !publication->source_revision || publication->deliveries.empty() || !source_current(*source))return false;
    if(publication->named_peer) {
        if(!input.named_target || publication->named_peer->recipient()!=lease_)return false;
        input.published_target=published_names_->qualify(*input.named_target,*publication->named_peer,936);
        if(!input.published_target || !input.published_target->recipient_is(source->connection) || !source_current(*source))return false;
        // This explicit current issued-peer name binds the common target only.
        // Actual permission/audience and reply fields remain WorldOwner duties.
    }
    std::vector<std::optional<SharedNativeWorldTransports::Snapshot>> routes;
    routes.reserve(publication->deliveries.size());
    for(auto& delivery:publication->deliveries) {
        std::optional<SharedNativeWorldTransports::Snapshot> route;
        if(delivery.use_common_transport) {
            if(!transports_)return false;
            route=transports_->lookup(delivery.recipient);
            if(!route || !source_current(*source))return false;
            const auto actual=std::visit([](const auto& c)->decltype(delivery.transport) {
                using T=typename std::decay_t<decltype(c)>::element_type;return std::weak_ptr<T>(c);
            },route->transport());
            const bool supplied=std::visit([](const auto& c){return !c.expired();},delivery.transport);
            if(supplied && (delivery.transport.index()!=actual.index() ||
               !std::visit([&](const auto& c) {
                    using T=std::decay_t<decltype(c)>;const auto expected=std::get_if<T>(&actual);
                    return expected && c.lock()==expected->lock();
                },delivery.transport)))return false;
            delivery.transport=actual;
        }
        routes.push_back(std::move(route));
    }
    const auto routed_source_current=[&] {
        // Endpoint after every real observer in the explicitly selected path.
        // This does not replace source_current's actual ready/root/position reads.
        bool selected=false;for(const auto& route:routes)if(route){selected=true;break;}
        if(!selected)return true;
        const auto& c=source->connection;
        return !terminal_ && c && connection_.lock()==c && !c->closing() &&
            c->role()==Connection::Transport::Role::World && c->world_admission_current() &&
            c->world_session_id()==lease_.session && c->verified_account_id()==lease_.account &&
            c->world_character_offered(lease_.character);
    };
    std::vector<RecipientState> destinations;
    destinations.reserve(publication->deliveries.size());
    std::vector<Prepared> prepared;
    prepared.reserve(publication->deliveries.size());
    std::set<std::pair<std::uint64_t,std::uint64_t>> recipients;
    std::size_t total=0;
    for(std::size_t i=0;i<publication->deliveries.size();++i) {
        const auto& d=publication->deliveries[i];
        const auto destination=recipient_state(d);
        if(!destination || !recipients.emplace(d.recipient.session,d.recipient.generation).second ||
           d.original_body_utf8!=input.body_utf8)return false;
        destinations.push_back(*destination);
    }
    const auto retained_current=[&] {
        if(!source_current(*source))return false;
        for(const auto& route:routes)
            if(route && (!transports_->current(*route) || !source_current(*source)))return false;
        if(input.named_target && (!identities_->current(*input.named_target) || !source_current(*source)))return false;
        if(input.published_target && (!published_names_->current(*input.published_target) ||
           !input.published_target->recipient_is(source->connection) || !source_current(*source)))return false;
        for(std::size_t i=0;i<publication->deliveries.size();++i)
            if(!recipient_current(publication->deliveries[i],destinations[i]))return false;
        // After every real source/recipient observer, check the original
        // registry incarnations without any repository/current callbacks.
        for(const auto& route:routes)
            if(route && !transports_->registry_current(*route))return false;
        return routed_source_current() && (!input.published_target || published_names_->registry_current(*input.published_target));
    };
    const auto observe_current=[&] {
        if(!retained_current())return false;
        const bool qualified=world_->current(lease_,*publication);
        return qualified && retained_current();
    };
    const auto qualified_peer=[&](const Delivery& delivery,std::span<const std::uint8_t> record) {
        if(!retained_current())return false;
        // Actual visibility may call native-text Current. Poison from a caught
        // outer ingress must be seen after that callback and before any queue.
        const bool qualified=peer_current(delivery,source->position,record);
        return qualified && retained_current();
    };
    if(!observe_current())return false;
    for(std::size_t i=0;i<publication->deliveries.size();++i) {
        const auto& d=publication->deliveries[i];
        // Shape of this full supplier envelope only. CN and TW length limits
        // stay separate; a TW serializer is not evidence for CN opaque fields.
        const bool cn=std::holds_alternative<std::weak_ptr<Connection>>(d.transport);
        std::optional<god2cn::CnChat::Reply> reply;
        std::optional<RecoveredTaiwanChatConsumerContract::Reply> taiwan;
        std::string_view raw;
        std::size_t budget=0;
        if(cn) {
            reply=god2cn::CnChat::read_reply(d.full_native_reply);if(!reply)return false;
            raw=reply->text();
            const auto native_budget=god2cn::CnChatConsumerContract::world_plain_text_budget(reply->channel());
            if(!native_budget)return false; // Other consumers need their actual native destination owner.
            budget=std::min(*native_budget,god2cn::CnChat::Reply::max_text_bytes);
        }else {
            taiwan=RecoveredTaiwanChatConsumerContract::read_reply(d.full_native_reply);if(!taiwan)return false;
            const auto native_budget=RecoveredTaiwanChatConsumerContract::world_plain_text_budget(taiwan->channel());
            if(!native_budget || taiwan->text().size()>*native_budget)return false;
            raw=taiwan->text();budget=*native_budget;
        }
        if(d.body_offset>raw.size() || d.body_size>raw.size()-d.body_offset)return false;
        const auto prefix=raw.substr(0,d.body_offset),suffix=raw.substr(d.body_offset+d.body_size);
        if(prefix.size()>budget || suffix.size()>budget-prefix.size())return false;
        const auto converted=text_->convert(input.body_utf8,d.preference);
        auto encoded=LegacyChineseCodec::encode_display(converted,d.code_page==WireCodePage::CP936,
            budget-prefix.size()-suffix.size());
        // Never change names, control tokens or unknown prefix/suffix/header.
        const auto projected=std::string(prefix)+encoded.bytes+std::string(suffix);
        god2cn::Bytes record;
        if(cn)record=reply->replace_text(projected,d.native_consumer_tag);
        else {
            if(projected.empty() || projected.size()>budget || projected.find('\0')!=std::string::npos)return false;
            const auto header=taiwan->header();record.assign(header.begin(),header.end());
            record.insert(record.end(),projected.begin(),projected.end());record.push_back(0);
            record[1]=static_cast<std::uint8_t>(record.size());record[2]=static_cast<std::uint8_t>(record.size()>>8);
            record[9]=static_cast<std::uint8_t>((record[9]&0x7f)|(d.native_consumer_tag<<7));
        }
        if(record.size()>god2cn::CnTransport::max_logical-total)return false;
        total+=record.size();prepared.push_back({i,std::move(record),encoded.replacements,encoded.truncated});
        // Check projected body extent separately: conversion may change bytes.
        auto projected_delivery=d;projected_delivery.body_size=encoded.bytes.size();
        if(!qualified_peer(projected_delivery,prepared.back().record))return false;
    }
    if(!observe_current())return false;
    const bool qualified=world_->qualify_delivery(lease_,request,input,*publication,prepared);
    if(!qualified || !retained_current() || !observe_current())return false;
    // Queue all qualified outputs in authority order on the game owner.
    // No atomic fanout/rollback promise if a transport closes during sending.
    for(auto& out:prepared) {
        const auto& d=publication->deliveries[out.delivery_index];
        if(!observe_current())return false;
        auto projected_delivery=d;
        // The body-only projector preserves original prefix/suffix; ordinary
        // CN peer text requires no suffix, so actual projected length is known.
        if(d.visible_peer)projected_delivery.body_size=out.record.size()-14-d.body_offset;
        if(!qualified_peer(projected_delivery,out.record))return false;
        if(const auto cn=std::get_if<std::shared_ptr<Connection>>(&destinations[out.delivery_index].transport)) {
            (*cn)->send(std::move(out.record));
        }else {
            const auto& c=std::get<std::shared_ptr<Session>>(destinations[out.delivery_index].transport);
            c->send_world_records(std::move(out.record));
        }
        if(!observe_current())return false;
    }
    return observe_current();
}
SharedNativeChat::Connection::Ingress SharedNativeChat::ingress() {
    owner();return [self=shared_from_this()](god2cn::Bytes b,Connection::Transport::Completion done) {
        self->receive(std::move(b),std::move(done));
    };
}
void SharedNativeChat::receive(god2cn::Bytes records,Connection::Transport::Completion done) {
    owner();if(!done)throw std::invalid_argument("CN chat completion required");
    if(busy_) {invalidate_active();if(const auto c=connection_.lock())c->close();done(false);return;}
    busy_=true;bool accepted=false;
    try {
        const auto process=[&] {
            if(records.empty() || records.size()>god2cn::CnTransport::max_logical || !current())return false;
            std::vector<god2cn::CnChat::Request> requests;
            const auto bytes=std::span<const std::uint8_t>(records);
            for(std::size_t offset=0;offset<records.size();) {
                const auto rest=bytes.subspan(offset);if(rest.size()<3)return false;
                const auto size=std::size_t(rest[1])+256u*rest[2];
                if(size>rest.size() || !supported_request(rest.first(size)))return false;
                requests.push_back(*god2cn::CnChat::parse(rest.first(size)));offset+=size;
            }
            for(const auto& r:requests)if(!dispatch(r))return false;
            return true;
        };accepted=process();
    }catch(...) {accepted=false;}
    if(!accepted)terminal_=true;
    busy_=false;
    if(!accepted)if(const auto c=connection_.lock())c->close();
    done(accepted); // Source queue processing only, not native client acceptance.
}
}
