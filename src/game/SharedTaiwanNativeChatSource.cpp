#include "game/SharedTaiwanNativeChatSource.h"
#include "cn/protocol/CnChatConsumerContract.h"
#include "protocol/RecoveredWorldFrame.h"
#include "protocol/RecoveredPrivateChat.h"
#include "protocol/RecoveredTaiwanChatConsumerContract.h"
#include <algorithm>
#include <exception>
#include <map>
#include <set>
#include <stdexcept>
#include <thread>
#include <utility>
#include <type_traits>

namespace god2 {
namespace {
using Source=SharedTaiwanNativeChatSource;
using Connection=cn::SharedCredentialConnection;
struct Slot {
    const Source::Lease lease;
    const std::weak_ptr<Session> session;
    bool live=true;
    Slot(const Source::Lease& actual,const std::shared_ptr<Session>& connection):lease(actual),session(connection) {}
};
struct Recipient {
    std::variant<std::shared_ptr<Connection>,std::shared_ptr<Session>> transport;
    RecoveredPosition saved_position;
    std::optional<SessionState> taiwan_phase;
    std::uint64_t taiwan_battle_generation;
};
struct Owner {
    const std::thread::id thread=std::this_thread::get_id();
    const std::shared_ptr<SharedWorldPresence> presence;
    const std::shared_ptr<SharedChatIdentitySource> identities;
    const std::shared_ptr<cn::SharedActorVisibility> visibility;
    const std::shared_ptr<SharedPublishedChatNameSource> published_names;
    const std::shared_ptr<Source::WorldOwner> world;
    const std::shared_ptr<const ChineseText> text;
    const std::shared_ptr<SharedNativeWorldTransports> transports;
    const Source::Budgets budgets;
    const std::size_t capacity;
    std::map<std::uint64_t,std::shared_ptr<Slot>> slots;
    std::shared_ptr<Slot> active;
    std::vector<std::optional<SharedNativeWorldTransports::Snapshot>> active_routes;
    bool operating=false,reentered=false;
    Owner(std::shared_ptr<SharedWorldPresence> p,std::shared_ptr<cn::SharedActorVisibility> v,
        std::shared_ptr<Source::WorldOwner> w,std::shared_ptr<const ChineseText> t,Source::Budgets b,std::size_t c,
        std::shared_ptr<SharedNativeWorldTransports> routes)
        :presence(std::move(p)),identities(SharedChatIdentitySource::create(presence)),visibility(std::move(v)),
         published_names(SharedPublishedChatNameSource::create(identities,presence,visibility)),
         world(std::move(w)),text(std::move(t)),transports(std::move(routes)),budgets(b),capacity(c) {}
    ~Owner() {
        if(thread!=std::this_thread::get_id())std::terminate();
        operating=true;reentered=true;
        for(auto& row:slots)row.second->live=false;
        active_routes.clear();slots.clear();active.reset();
        // Strong real affine inputs then drain here. No common lease cleanup.
    }
    void owner() const {
        if(thread!=std::this_thread::get_id())throw std::logic_error("TW native chat source game owner mismatch");
    }
    void poison() {
        owner();if(!operating)return;
        reentered=true;if(active)active->live=false;
    }
    struct Operation {
        Owner& state;
        explicit Operation(Owner& actual):state(actual) {
            state.owner();
            if(state.operating) {state.poison();throw std::logic_error("TW native chat source reentry rejected");}
            state.operating=true;state.reentered=false;
        }
        ~Operation() {state.active_routes.clear();state.active.reset();state.operating=false;}
    };
    bool ready(Session& session,const Source::Lease& lease) const {
        const auto phase=session.state();
        if(reentered || session.closing() || session.id()!=lease.session || session.account_id!=lease.account ||
           session.character_id!=lease.character || (phase!=SessionState::InWorld && phase!=SessionState::InBattle) ||
           !session.recovered_world_ready() ||
           !session.common_world_delivery_current(lease.account,lease.character,lease.generation) ||
           session.common_world_entry_current(lease.account,lease.character,lease.generation))return false;
        const auto actual=presence->ready_lease(lease.session,lease.account,lease.character);
        return actual && *actual==lease;
    }
    std::optional<Source::Scope> snapshot(Session& session,const std::shared_ptr<Slot>& slot,std::size_t submitted) const {
        if(!slot || !slot->live || slot->session.lock().get()!=&session || !ready(session,slot->lease))return std::nullopt;
        const auto found=slots.find(slot->lease.session);
        if(found==slots.end() || found->second!=slot)return std::nullopt;
        const auto position=presence->saved_position(slot->lease);if(!position)return std::nullopt;
        return Source::Scope{slot->lease,*position,session.state(),session.battle_generation(),submitted};
    }
    static bool same(const Source::Scope& before,const std::optional<Source::Scope>& after) {
        return after && before.lease==after->lease && before.saved_position==after->saved_position &&
            before.phase==after->phase && before.battle_generation==after->battle_generation &&
            before.submitted_recipients==after->submitted_recipients;
    }
    bool routes_current() const {
        if(reentered)return false;
        for(const auto& route:active_routes)
            if(route && (!transports || !transports->current(*route) || reentered))return false;
        return true;
    }
    bool routes_registry_current() const {
        if(reentered)return false;
        for(const auto& route:active_routes)
            if(route && (!transports || !transports->registry_current(*route)))return false;
        return true;
    }
    bool routed_source_current(Session& session,const std::shared_ptr<Slot>& slot,const Source::Scope& original) const {
        // Only the new selected transport-source path needs this endpoint.
        // Real ready/root/saved-position observations still occur in snapshot().
        if(std::none_of(active_routes.begin(),active_routes.end(),[](const auto& route){return bool(route);}))return true;
        if(reentered || !slot || !slot->live || slot->lease!=original.lease || slot->session.lock().get()!=&session)return false;
        const auto found=slots.find(original.lease.session);
        return found!=slots.end() && found->second==slot && !session.closing() &&
            session.id()==original.lease.session && session.account_id==original.lease.account &&
            session.character_id==original.lease.character && session.recovered_world_ready() &&
            session.state()==original.phase && session.battle_generation()==original.battle_generation &&
            session.common_world_delivery_current(original.lease.account,original.lease.character,original.lease.generation) &&
            !session.common_world_entry_current(original.lease.account,original.lease.character,original.lease.generation);
    }
    bool qualified(Session& session,const std::shared_ptr<Slot>& slot,Source::Check check,
        const RecoveredChat::Request& request,const Source::Input& input,const Source::Publication& publication,
        const Source::Scope& original,std::size_t submitted) {
        if(!routes_current())return false;
        const auto before=snapshot(session,slot,submitted);
        if(!before || before->lease!=original.lease || before->saved_position!=original.saved_position ||
           before->phase!=original.phase || before->battle_generation!=original.battle_generation)return false;
        if(input.named_target && (!identities->current(*input.named_target) || !same(*before,snapshot(session,slot,submitted))))return false;
        const auto published_current=[&] {
            return !input.published_target || (published_names->current(*input.published_target) &&
                input.published_target->recipient_is(session.shared_from_this()) &&
                same(*before,snapshot(session,slot,submitted)) &&
                published_names->registry_current(*input.published_target));
        };
        if(!published_current())return false;
        const bool actual=world->current(*before,check,request,input,publication);
        if(!actual || !same(*before,snapshot(session,slot,submitted)))return false;
        return (!input.named_target || (identities->current(*input.named_target) && same(*before,snapshot(session,slot,submitted)))) &&
            published_current() && routes_current() && routes_registry_current() && routed_source_current(session,slot,original) &&
            (!input.published_target || published_names->registry_current(*input.published_target));
    }
    std::optional<Recipient> recipient(const Source::Delivery& delivery) const {
        const auto actual=presence->ready_lease(delivery.recipient.session,delivery.recipient.account,delivery.recipient.character);
        if(!actual || *actual!=delivery.recipient || delivery.native_consumer_tag>1 ||
           (delivery.code_page!=Source::WireCodePage::CP950 && delivery.code_page!=Source::WireCodePage::CP936) ||
           (delivery.preference!=ChineseLanguage::Traditional && delivery.preference!=ChineseLanguage::Simplified))return std::nullopt;
        const auto position=presence->saved_position(delivery.recipient);if(!position)return std::nullopt;
        if(const auto native=std::get_if<std::weak_ptr<Connection>>(&delivery.transport)) {
            const auto connection=native->lock();
            if(!connection || connection->closing() || connection->role()!=Connection::Transport::Role::World ||
               !connection->world_admission_current() || connection->world_session_id()!=delivery.recipient.session ||
               connection->verified_account_id()!=delivery.recipient.account ||
               !connection->world_character_offered(delivery.recipient.character) ||
               delivery.code_page!=Source::WireCodePage::CP936 || delivery.native_consumer_tag!=0)return std::nullopt;
            // CN battle/formatter state remains actual WorldOwner qualification;
            // this connection API supplies no battle-generation getter.
            return Recipient{connection,*position,std::nullopt,0};
        }
        const auto connection=std::get<std::weak_ptr<Session>>(delivery.transport).lock();
        if(!connection || connection->closing() || !connection->recovered_world_ready() ||
           connection->id()!=delivery.recipient.session || connection->account_id!=delivery.recipient.account ||
           connection->character_id!=delivery.recipient.character ||
           (connection->state()!=SessionState::InWorld && connection->state()!=SessionState::InBattle) ||
           !connection->common_world_delivery_current(delivery.recipient.account,delivery.recipient.character,delivery.recipient.generation) ||
           connection->common_world_entry_current(delivery.recipient.account,delivery.recipient.character,delivery.recipient.generation) ||
           connection->recovered_client_language()>1 ||
           delivery.native_consumer_tag!=connection->recovered_client_language())return std::nullopt;
        // Language tag qualifies the native consumer only, never selects the
        // wire codepage. The actual destination profile is mandatory authority.
        return Recipient{connection,*position,connection->state(),connection->battle_generation()};
    }
    bool recipient_current(const Source::Delivery& delivery,const Recipient& retained) const {
        const auto actual=recipient(delivery);
        return actual && actual->transport==retained.transport && actual->saved_position==retained.saved_position &&
            actual->taiwan_phase==retained.taiwan_phase && actual->taiwan_battle_generation==retained.taiwan_battle_generation;
    }
    bool peer_current(const Source::Delivery& delivery,const Source::Scope& source,std::span<const std::uint8_t> record,
        std::size_t projected_body_size) const {
        const auto native=std::get_if<std::weak_ptr<Connection>>(&delivery.transport);
        if(!native)return !delivery.visible_peer; // TW peer bubble belongs to actual WorldOwner, not a CN token.
        const auto reply=god2cn::CnChat::read_reply(record);if(!reply)return false;
        const bool bubble=(reply->channel()==0 || reply->channel()==6) && delivery.recipient!=source.lease;
        if(!bubble)return !delivery.visible_peer;
        if(!delivery.visible_peer || delivery.visible_peer->source()!=source.lease ||
           delivery.visible_peer->recipient()!=delivery.recipient)return false;
        const auto actor=visibility->mainland_chat_actor(*delivery.visible_peer,source.saved_position);
        if(!actor || actor->connection.lock()!=native->lock() || actor->native_actor_identity!=reply->actor())return false;
        const auto prefix=actor->native_name_bytes+": ";const auto raw=reply->text();
        return raw.starts_with(prefix) && delivery.body_offset==prefix.size() &&
            projected_body_size<=raw.size()-prefix.size() && raw.size()==prefix.size()+projected_body_size &&
            raw.find(": /board ")==std::string_view::npos && raw.find(": $")==std::string_view::npos;
    }
    bool peer_qualified(Session& session,const std::shared_ptr<Slot>& slot,const Source::Delivery& delivery,
        const Recipient& recipient,const Source::Scope& origin,std::span<const std::uint8_t> record,
        std::size_t projected_body_size,std::size_t submitted) const {
        const auto before=snapshot(session,slot,submitted);
        if(!before || before->lease!=origin.lease || before->saved_position!=origin.saved_position ||
           before->phase!=origin.phase || before->battle_generation!=origin.battle_generation ||
           !recipient_current(delivery,recipient))return false;
        // Visibility may consult a real native text Current. Caught callback
        // reentry must remain visible to this source before any queue submit.
        const bool actual=peer_current(delivery,origin,record,projected_body_size);
        return actual && same(*before,snapshot(session,slot,submitted)) && recipient_current(delivery,recipient);
    }
    std::optional<Source::Reply> dispatch(Session& session,const RecoveredChat::Request& request) {
        Operation operation(*this);
        const auto lease=presence->ready_lease(session.id(),session.account_id,session.character_id);
        if(!lease || !ready(session,*lease))return std::nullopt;
        const auto found=slots.find(session.id());
        if(found==slots.end()) {
            if(slots.size()>=capacity)return std::nullopt;
            active=std::make_shared<Slot>(*lease,session.shared_from_this());slots.emplace(lease->session,active);
        }else active=found->second;
        const auto slot=active;
        if(slot->session.lock().get()!=&session || slot->lease!=*lease)return std::nullopt;
        try {
            const auto origin=snapshot(session,slot,0);
            if(!origin || request.legacy_text.empty() || request.legacy_text.size()>RecoveredChat::max_text_bytes ||
               request.legacy_text.find('\0')!=std::string::npos)throw std::invalid_argument("TW native chat exact original request rejected");
            auto input=world->input(*origin,request);
            if(!same(*origin,snapshot(session,slot,0)) || !input ||
               (input->kind!=Source::NativeContent::PlayerText && input->kind!=Source::NativeContent::NamedWhisper) ||
               (input->wire_code_page!=Source::WireCodePage::CP950 && input->wire_code_page!=Source::WireCodePage::CP936) ||
               input->original_utf8.size()>budgets.max_original_utf8_bytes || input->body_utf8.empty() ||
               input->body_utf8.size()>budgets.max_original_utf8_bytes || !ChineseText::valid_utf8(input->original_utf8) ||
               !ChineseText::valid_utf8(input->body_utf8) || input->body_offset>request.legacy_text.size() ||
               !input->body_size || input->body_size>request.legacy_text.size()-input->body_offset)
                throw std::invalid_argument("TW native chat lacks actual native prose/codepage/body source");
            if(input->named_target || input->published_target)
                throw std::invalid_argument("TW native input cannot supply this source's identity observation");
            const bool simplified=input->wire_code_page==Source::WireCodePage::CP936;
            if(LegacyChineseCodec::decode(request.legacy_text,simplified)!=input->original_utf8 ||
               LegacyChineseCodec::decode(std::string_view(request.legacy_text).substr(input->body_offset,input->body_size),simplified)!=input->body_utf8)
                throw std::invalid_argument("TW native chat original source text/codepage mismatch");
            if(input->kind==Source::NativeContent::NamedWhisper) {
                // Only the retained target envelope is checked here. Exact
                // native body boundaries/provenance are supplied by input();
                // do not invent whitespace trimming or a complete body grammar.
                const auto separator=request.legacy_text.find(' ',1);
                if(!RecoveredPrivateChat::selected(request) || request.legacy_text.front()!='$' ||
                   separator==std::string::npos || separator<=1 || input->body_offset<=separator)
                    throw std::invalid_argument("TW native named input lacks its actual target/body envelope");
                input->named_target=identities->lookup(std::string_view(request.legacy_text).substr(1,separator-1),
                    simplified?936:950);
                if(!input->named_target || !same(*origin,snapshot(session,slot,0)))
                    throw std::runtime_error("TW native named input lacks a current common identity observation");
                // Native target/history/spawn names are a distinct source
                // namespace. Resolve must qualify their actual issuer binding;
                // no result here grants a recipient, permission or reply.
            }
            auto publication=world->resolve(*origin,request,*input);
            if(publication && publication->named_peer) {
                if(!same(*origin,snapshot(session,slot,0)) || !input->named_target ||
                   publication->named_peer->recipient()!=origin->lease)
                    throw std::invalid_argument("TW named publication lacks its actual target-to-sender binding");
                input->published_target=published_names->qualify(*input->named_target,*publication->named_peer,
                    simplified?936:950);
                if(!input->published_target || !input->published_target->recipient_is(session.shared_from_this()) ||
                   !same(*origin,snapshot(session,slot,0)))
                    throw std::runtime_error("TW named publication lacks a current issued common-peer name");
                // Actual native raw-copy state/encoding and private incarnation
                // qualify this branch; adapted/other namespaces need real owners.
            }
            if(!same(*origin,snapshot(session,slot,0)) || !publication || !publication->source_revision ||
               !publication->explicit_no_additional_sender_reply || publication->deliveries.empty() ||
               publication->deliveries.size()>budgets.max_deliveries)
                throw std::runtime_error("TW native chat actual publication/permission rejected");
            active_routes.reserve(publication->deliveries.size());
            for(auto& delivery:publication->deliveries) {
                std::optional<SharedNativeWorldTransports::Snapshot> route;
                if(delivery.use_common_transport) {
                    if(!transports)throw std::invalid_argument("TW chat common native transport source missing");
                    route=transports->lookup(delivery.recipient);
                    if(!route || !same(*origin,snapshot(session,slot,0)))
                        throw std::runtime_error("TW chat actual common recipient route unavailable");
                    const auto actual=std::visit([](const auto& c)->decltype(delivery.transport) {
                        using T=typename std::decay_t<decltype(c)>::element_type;return std::weak_ptr<T>(c);
                    },route->transport());
                    const bool supplied=std::visit([](const auto& c){return !c.expired();},delivery.transport);
                    if(supplied && (delivery.transport.index()!=actual.index() ||
                       !std::visit([&](const auto& c) {
                            using T=std::decay_t<decltype(c)>;const auto expected=std::get_if<T>(&actual);
                            return expected && c.lock()==expected->lock();
                        },delivery.transport)))
                        throw std::invalid_argument("TW chat supplied common transport differs from actual registered receiver");
                    delivery.transport=actual;
                }
                active_routes.push_back(std::move(route));
            }
            if(!qualified(session,slot,Source::Check::Resolved,request,*input,*publication,*origin,0))
                throw std::runtime_error("TW native chat common recipient/actual permission rejected");
            std::vector<Source::Prepared> prepared;prepared.reserve(publication->deliveries.size());
            std::vector<Recipient> recipients;recipients.reserve(publication->deliveries.size());
            std::vector<std::size_t> body_sizes;body_sizes.reserve(publication->deliveries.size());
            std::vector<Source::SenderPrepared> sender_prepared;sender_prepared.reserve(publication->deliveries.size());
            std::set<std::pair<std::uint64_t,std::uint64_t>> unique;
            std::vector<std::uint8_t> sender_output;sender_output.reserve(budgets.max_output_bytes);
            std::size_t total=0;
            for(std::size_t i=0;i<publication->deliveries.size();++i) {
                const auto& delivery=publication->deliveries[i];const auto destination=recipient(delivery);
                if(!destination || !unique.emplace(delivery.recipient.session,delivery.recipient.generation).second ||
                   delivery.original_body_utf8!=input->body_utf8)
                    throw std::runtime_error("TW native chat actual recipient/original identity rejected");
                recipients.push_back(*destination);
                const bool mainland=std::holds_alternative<std::weak_ptr<Connection>>(delivery.transport);
                std::optional<god2cn::CnChat::Reply> native;
                std::optional<RecoveredTaiwanChatConsumerContract::Reply> taiwan;std::string_view raw;
                std::size_t budget=0;
                if(mainland) {
                    native=god2cn::CnChat::read_reply(delivery.full_native_reply);
                    if(!native)throw std::invalid_argument("TW native chat missing actual complete CN5C");
                    const auto actual_budget=god2cn::CnChatConsumerContract::world_plain_text_budget(native->channel());
                    if(!actual_budget)throw std::invalid_argument("TW native chat unsupported CN destination consumer");
                    budget=std::min(*actual_budget,god2cn::CnChat::Reply::max_text_bytes);raw=native->text();
                }else {
                    taiwan=RecoveredTaiwanChatConsumerContract::read_reply(delivery.full_native_reply);
                    if(!taiwan)throw std::invalid_argument("TW native chat missing actual complete TW5C");
                    const auto actual_budget=RecoveredTaiwanChatConsumerContract::world_plain_text_budget(taiwan->channel());
                    if(!actual_budget || taiwan->text().size()>*actual_budget)
                        throw std::invalid_argument("TW native chat unsupported complete TW5C consumer");
                    raw=taiwan->text();budget=*actual_budget;
                }
                if(delivery.body_offset>raw.size() || delivery.body_size>raw.size()-delivery.body_offset)
                    throw std::invalid_argument("TW native chat supplied body boundary rejected");
                const auto prefix=raw.substr(0,delivery.body_offset),suffix=raw.substr(delivery.body_offset+delivery.body_size);
                if(prefix.size()>budget || suffix.size()>budget-prefix.size())
                    throw std::invalid_argument("TW native chat retained native prefix/suffix budget rejected");
                // Incoming original wire text was strictly decoded above. The
                // actual original UTF8 proof remains separate from a recipient
                // field that may already contain display substitutions; real
                // authority qualifies its full body boundaries/native header.
                const auto converted=text->convert(input->body_utf8,delivery.preference);
                if(converted.size()>budgets.max_projected_utf8_bytes)
                    throw std::invalid_argument("TW native chat projected UTF8 budget exceeded");
                const auto encoded=LegacyChineseCodec::encode_display(converted,delivery.code_page==Source::WireCodePage::CP936,
                    budget-prefix.size()-suffix.size());
                const auto projected=std::string(prefix)+encoded.bytes+std::string(suffix);
                std::vector<std::uint8_t> record;
                if(mainland)record=native->replace_text(projected,delivery.native_consumer_tag);
                else {
                    if(projected.empty() || projected.size()>budget || projected.find('\0')!=std::string::npos)
                        throw std::invalid_argument("TW native chat final TW sink budget rejected");
                    const auto header=taiwan->header();record.assign(header.begin(),header.end());
                    record.insert(record.end(),projected.begin(),projected.end());record.push_back(0);
                    record[1]=static_cast<std::uint8_t>(record.size());record[2]=static_cast<std::uint8_t>(record.size()>>8);
                    record[9]=static_cast<std::uint8_t>((record[9]&0x7f)|(delivery.native_consumer_tag<<7));
                }
                if(record.size()>budgets.max_output_bytes-total ||
                   !peer_qualified(session,slot,delivery,*destination,*origin,record,encoded.bytes.size(),0))
                    throw std::runtime_error("TW native chat native actor/body/output qualification rejected");
                total+=record.size();body_sizes.push_back(encoded.bytes.size());
                prepared.push_back({i,std::move(record),encoded.replacements,encoded.truncated});
                if(delivery.recipient==origin->lease) {
                    const auto connection=std::get_if<std::shared_ptr<Session>>(&destination->transport);
                    if(!connection || connection->get()!=&session)
                        throw std::invalid_argument("TW native chat sender delivery transport mismatch");
                    if(!qualified(session,slot,Source::Check::Prepared,request,*input,*publication,*origin,0))
                        throw std::runtime_error("TW native chat sender profile Current expired");
                    const auto before_wire=snapshot(session,slot,0);
                    if(!before_wire)throw std::runtime_error("TW native chat sender scope expired");
                    const auto wire=world->sender_wire(*before_wire,prepared.back());
                    if(!same(*before_wire,snapshot(session,slot,0)) || !wire || wire->size()<4 ||
                       wire->size()>RecoveredWorldFrame::max_logical_size+3 ||
                       std::size_t((*wire)[0])+256u*(*wire)[1]!=wire->size() ||
                       !qualified(session,slot,Source::Check::Prepared,request,*input,*publication,*origin,0))
                        throw std::runtime_error("TW native chat missing actual complete sender cipher envelope");
                    if(wire->size()>budgets.max_output_bytes-sender_output.size())
                        throw std::invalid_argument("TW native chat ordered sender envelope budget exceeded");
                    sender_prepared.push_back({i,*wire});
                    sender_output.insert(sender_output.end(),wire->begin(),wire->end());
                }
            }
            if(!qualified(session,slot,Source::Check::Prepared,request,*input,*publication,*origin,0))
                throw std::runtime_error("TW native chat prepared output Current failed");
            const auto before=snapshot(session,slot,0);
            if(!before || !world->qualify_delivery(*before,request,*input,*publication,prepared,sender_prepared) ||
               !same(*before,snapshot(session,slot,0)) ||
               !qualified(session,slot,Source::Check::Prepared,request,*input,*publication,*origin,0))
                throw std::runtime_error("TW native chat actual native output/authority rejected");
            for(std::size_t i=0;i<publication->deliveries.size();++i)
                if(!peer_qualified(session,slot,publication->deliveries[i],recipients[i],*origin,prepared[i].record,body_sizes[i],0))
                    throw std::runtime_error("TW native chat full prepared recipient set expired");
            // Entire native output preparation precedes any submission. Sender
            // bytes stay in mixed-dispatch order; other transports are separate
            // queues, with no distributed atomicity or rollback guarantee.
            std::size_t submitted=0;
            for(std::size_t i=0;i<publication->deliveries.size();++i) {
                const auto& delivery=publication->deliveries[i];
                if(!qualified(session,slot,Source::Check::BeforeRecipient,request,*input,*publication,*origin,submitted) ||
                   !peer_qualified(session,slot,delivery,recipients[i],*origin,prepared[i].record,body_sizes[i],submitted) ||
                   !routes_registry_current() || !routed_source_current(session,slot,*origin) ||
                   (input->published_target && !published_names->registry_current(*input->published_target)))
                    throw std::runtime_error("TW native chat before native recipient submission expired");
                if(delivery.recipient!=origin->lease) {
                    if(const auto mainland=std::get_if<std::shared_ptr<Connection>>(&recipients[i].transport))
                        (*mainland)->send(std::move(prepared[i].record));
                    else std::get<std::shared_ptr<Session>>(recipients[i].transport)->send_world_records(std::move(prepared[i].record));
                    ++submitted;
                }
                if(!recipient_current(delivery,recipients[i]) ||
                   !qualified(session,slot,Source::Check::AfterRecipient,request,*input,*publication,*origin,submitted))
                    throw std::runtime_error("TW native chat after native submission Current failed");
            }
            if(!qualified(session,slot,Source::Check::BeforeReturn,request,*input,*publication,*origin,submitted))
                throw std::runtime_error("TW native chat final current source failed");
            return sender_output.empty()?Source::Reply::no_reply():Source::Reply::wire(std::move(sender_output));
        }catch(...) {
            slot->live=false; // Exact immutable generation terminal until lifecycle release.
            // Earlier peer submissions may already exist. Never replay or undo.
            throw;
        }
    }
    void release(Session& session) {
        Operation operation(*this);const auto found=slots.find(session.id());if(found==slots.end())return;
        if(found->second->session.lock().get()!=&session || found->second->lease.session!=session.id())
            throw std::invalid_argument("TW native chat bookkeeping release foreign Session rejected");
        found->second->live=false;slots.erase(found);
    }
};
}
SharedTaiwanNativeChatSource::Binding SharedTaiwanNativeChatSource::create(
    std::shared_ptr<SharedWorldPresence> presence,std::shared_ptr<cn::SharedActorVisibility> visibility,
    std::shared_ptr<WorldOwner> world,std::shared_ptr<const ChineseText> text,Budgets budgets,std::size_t capacity,
    std::shared_ptr<SharedNativeWorldTransports> transports) {
    if(!presence || !visibility || !visibility->owns_presence(presence) || !world || !text || !capacity ||
       (transports && !transports->owns_presence(presence)) ||
       !budgets.max_original_utf8_bytes || !budgets.max_projected_utf8_bytes || !budgets.max_deliveries ||
       budgets.max_output_bytes<4)
        throw std::invalid_argument("TW native chat requires actual common owners/native authority/text/budgets/capacity");
    auto owner=std::make_shared<Owner>(std::move(presence),std::move(visibility),std::move(world),std::move(text),budgets,capacity,std::move(transports));
    return {
        [owner](Session& session,const RecoveredChat::Request& request){return owner->dispatch(session,request);},
        [owner](Session& session){owner->release(session);},
        [owner]{owner->poison();}
    };
}
}
