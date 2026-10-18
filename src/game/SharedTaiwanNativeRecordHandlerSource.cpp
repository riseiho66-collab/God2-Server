#include "game/SharedTaiwanNativeRecordHandlerSource.h"
#include <exception>
#include <stdexcept>
#include <thread>
#include <utility>

namespace god2 {
namespace {
using Source=SharedTaiwanWorldRecordSource;
using Handler=SharedTaiwanNativeRecordHandlerSource;
struct Segment {
    std::size_t offset,count;
    std::optional<RecoveredChat::Request> chat;
    std::optional<RecoveredSpectator6E::Request> spectator;
    std::optional<RecoveredSpectatorClose::Request> close;
};
struct Owner {
    const std::thread::id thread=std::this_thread::get_id();
    SharedTaiwanNativeChatSource::Binding chat;
    std::optional<SharedTaiwanNativeSpectatorSource::Binding> spectator;
    Source::OtherBinding remaining;
    const std::size_t byte_budget;
    const bool spectator6e;
    const bool spectator_close;
    bool busy=false,reentered=false,invalidating=false,releasing=false;
    Owner(SharedTaiwanNativeChatSource::Binding actual_chat,
        std::optional<SharedTaiwanNativeSpectatorSource::Binding> actual_spectator,
        Source::OtherBinding actual_remaining,std::size_t bytes)
        :chat(std::move(actual_chat)),spectator(std::move(actual_spectator)),remaining(std::move(actual_remaining)),
         byte_budget(bytes),spectator6e(bool(spectator) || remaining.spectator6e),
         spectator_close((spectator && bool(spectator->close_dispatch)) || remaining.spectator_close) {}
    ~Owner() {
        if(std::this_thread::get_id()!=thread)std::terminate();
        busy=true;reentered=true;
        chat={};spectator.reset();remaining={};
    }
    void check() const {
        if(std::this_thread::get_id()!=thread)
            throw std::logic_error("TW native record handlers game owner mismatch");
    }
    void invalidate() {
        check();if(!busy)return;
        reentered=true;if(invalidating)return;
        invalidating=true;
        struct EndInvalidation {bool& active;~EndInvalidation(){active=false;}} end{invalidating};
        std::exception_ptr failure;
        // Invoke every actual child even if an earlier child throws. No
        // callback copy/allocation outside the individual protected calls.
        try {chat.invalidate_active();}catch(...) {failure=std::current_exception();}
        try {if(spectator)spectator->invalidate_active();}catch(...) {if(!failure)failure=std::current_exception();}
        try {remaining.invalidate_active();}catch(...) {if(!failure)failure=std::current_exception();}
        if(failure)std::rethrow_exception(failure);
    }
    struct Operation {
        Owner& owner;
        explicit Operation(Owner& actual):owner(actual) {
            owner.check();
            if(owner.busy) {owner.invalidate();throw std::logic_error("TW native record handlers reentered");}
            owner.busy=true;owner.reentered=false;
        }
        ~Operation() {owner.busy=false;}
    };
    void current(Session& session) const {
        if(reentered || session.closing() ||
           (session.state()!=SessionState::InWorld && session.state()!=SessionState::InBattle))
            throw std::runtime_error("TW native record handler source is no longer current");
        // Exact lease/position/whole-batch phase/permissions are requalified by
        // the actual enclosing WorldRecordSource Current and each real handler.
    }
    std::optional<Source::Reply> records(Session& session,std::span<const Source::Record> records) {
        Operation operation(*this);
        try {
        current(session);
        if(records.empty())return std::nullopt;
        // Retain every complete original variant before any actual handler
        // runs. A prefix callback cannot replace later borrowed request data.
        const std::vector<Source::Record> owned(records.begin(),records.end());
        records=owned;
        std::vector<Segment> prepared;prepared.reserve(records.size());
        for(std::size_t at=0;at<records.size();) {
            if(records[at].valueless_by_exception() ||
               std::holds_alternative<RecoveredMovement::Request>(records[at]))return std::nullopt;
            const bool is_chat=Handler::native_chat_record(records[at]);
            const bool is_spectator=spectator && std::holds_alternative<RecoveredSpectator6E::Request>(records[at]);
            const bool is_close=spectator && spectator->close_dispatch &&
                std::holds_alternative<RecoveredSpectatorClose::Request>(records[at]);
            auto request=Handler::chat_request(records[at]);
            std::optional<RecoveredSpectator6E::Request> spectator_request;
            if(is_spectator)spectator_request=std::get<RecoveredSpectator6E::Request>(records[at]);
            std::optional<RecoveredSpectatorClose::Request> close_request;
            if(is_close)close_request=std::get<RecoveredSpectatorClose::Request>(records[at]);
            if(is_chat && !request)
                throw std::invalid_argument("TW native typed chat selector/header mismatch");
            auto end=at+1;
            // Chat source receives the exact original Request in sequence.
            // Other native handlers receive maximal contiguous complete spans.
            if(!is_chat && !is_spectator && !is_close)while(end<records.size() && !records[end].valueless_by_exception() &&
                !std::holds_alternative<RecoveredMovement::Request>(records[end]) &&
                !Handler::native_chat_record(records[end]) &&
                !(spectator && std::holds_alternative<RecoveredSpectator6E::Request>(records[end])) &&
                !(spectator && spectator->close_dispatch &&
                  std::holds_alternative<RecoveredSpectatorClose::Request>(records[end])))++end;
            // Copy every exact chat request before any actual handler can
            // publish a prefix; source allocation cannot change batch order.
            prepared.push_back({at,end-at,std::move(request),std::move(spectator_request),std::move(close_request)});at=end;
        }
        std::vector<std::uint8_t> output;output.reserve(byte_budget);
        for(const auto& segment:prepared) {
            current(session);std::optional<Source::Reply> reply;
            if(segment.chat) {
                const auto invoke=chat.dispatch;
                reply=invoke(session,*segment.chat);
            }else if(segment.spectator) {
                const auto invoke=spectator->dispatch;
                reply=invoke(session,*segment.spectator);
            }else if(segment.close) {
                const auto invoke=spectator->close_dispatch;
                reply=invoke(session,*segment.close);
            }else {
                const auto invoke=remaining.records;
                reply=invoke(session,records.subspan(segment.offset,segment.count));
            }
            current(session);
            if(!reply || (reply->native_no_reply() && !reply->bytes().empty()) ||
               (!reply->native_no_reply() && reply->bytes().empty()))return std::nullopt;
            const auto& bytes=reply->bytes();
            if(bytes.size()>byte_budget-output.size())
                throw std::length_error("TW native record handler output capacity exceeded after durable prefix");
            output.insert(output.end(),bytes.begin(),bytes.end());
        }
        current(session);
        return output.empty()?Source::Reply::no_reply():Source::Reply::wire(std::move(output));
        }catch(...) {
            const auto failure=std::current_exception();
            try {invalidate();}catch(...) {}
            std::rethrow_exception(failure);
        }
    }
    void release(Session& session) {
        check();
        if(releasing) {
            reentered=true;invalidate();
            throw std::logic_error("TW native record cleanup reentered");
        }
        const bool outer_busy=busy;
        busy=true;releasing=true;if(outer_busy)reentered=true;else reentered=false;
        struct EndRelease {
            Owner& owner;bool outer_busy;
            ~EndRelease(){owner.releasing=false;owner.busy=outer_busy;}
        } end{*this,outer_busy};
        std::exception_ptr failure;
        if(outer_busy)try {invalidate();}catch(...) {failure=std::current_exception();}
        // Nested cleanup terminalizes an observing operation, but still runs
        // every real release. Never repeat recursive release of these children.
        try {chat.release(session);}catch(...) {if(!failure)failure=std::current_exception();}
        try {if(spectator)spectator->release(session);}catch(...) {if(!failure)failure=std::current_exception();}
        try {remaining.release(session);}catch(...) {if(!failure)failure=std::current_exception();}
        if(failure)std::rethrow_exception(failure);
    }
};
Source::OtherBinding make_binding(const std::shared_ptr<Owner>& owner) {
    return {
        [owner](Session& session,std::span<const Source::Record> records){return owner->records(session,records);},
        [owner](Session& session){owner->release(session);},
        [owner]{owner->invalidate();},owner->spectator6e,owner->spectator_close,
        owner->remaining.selection_item,owner->remaining.inventory_move,owner->remaining.native_skills,owner->remaining.native_world_skill_requests,
        {},owner->remaining.native_preborn_requests, // C67 remains injected by the final Context owner.
        owner->remaining.native_skill_selection_requests
    };
}
}
bool SharedTaiwanNativeRecordHandlerSource::native_chat_record(const RecoveredWorldRecords::Record& record) noexcept {
    return std::holds_alternative<RecoveredChat::Request>(record) ||
        std::holds_alternative<RecoveredPrivateChat::Request>(record) ||
        std::holds_alternative<RecoveredPartyChat::Request>(record) ||
        std::holds_alternative<RecoveredGuildChat::Request>(record);
}
std::optional<RecoveredChat::Request> SharedTaiwanNativeRecordHandlerSource::chat_request(
    const RecoveredWorldRecords::Record& record) {
    if(const auto request=std::get_if<RecoveredChat::Request>(&record)) {
        if(RecoveredPartyChat::selected(*request) || RecoveredPrivateChat::selected(*request) ||
           RecoveredGuildChat::selected(*request))return std::nullopt;
        return *request;
    }
    if(const auto request=std::get_if<RecoveredPrivateChat::Request>(&record)) {
        RecoveredChat::Request exact{request->client_header,request->legacy_text};
        return RecoveredPrivateChat::selected(exact)?std::optional{std::move(exact)}:std::nullopt;
    }
    if(const auto request=std::get_if<RecoveredPartyChat::Request>(&record)) {
        RecoveredChat::Request exact{request->client_header,request->legacy_text};
        return RecoveredPartyChat::selected(exact)?std::optional{std::move(exact)}:std::nullopt;
    }
    if(const auto request=std::get_if<RecoveredGuildChat::Request>(&record)) {
        RecoveredChat::Request exact{request->client_header,request->legacy_text};
        return RecoveredGuildChat::selected(exact)?std::optional{std::move(exact)}:std::nullopt;
    }
    return std::nullopt;
}
SharedTaiwanNativeRecordHandlerSource::Binding SharedTaiwanNativeRecordHandlerSource::create(
    SharedTaiwanNativeChatSource::Binding chat,Binding remaining,std::size_t actual_output_byte_budget) {
    if(!chat.dispatch || !chat.release || !chat.invalidate_active ||
       !remaining.records || !remaining.release || !remaining.invalidate_active || actual_output_byte_budget<4)
        throw std::invalid_argument("TW native record handlers require complete actual chat and remaining sources");
    return make_binding(std::make_shared<Owner>(std::move(chat),std::nullopt,std::move(remaining),actual_output_byte_budget));
}
SharedTaiwanNativeRecordHandlerSource::Binding SharedTaiwanNativeRecordHandlerSource::create(
    SharedTaiwanNativeChatSource::Binding chat,SharedTaiwanNativeSpectatorSource::Binding spectator,
    Binding remaining,std::size_t actual_output_byte_budget) {
    if(!chat.dispatch || !chat.release || !chat.invalidate_active ||
       !spectator.dispatch || !spectator.release || !spectator.invalidate_active ||
       !remaining.records || !remaining.release || !remaining.invalidate_active || actual_output_byte_budget<4)
        throw std::invalid_argument("TW native typed spectator records require complete actual child sources");
    return make_binding(std::make_shared<Owner>(std::move(chat),std::move(spectator),std::move(remaining),actual_output_byte_budget));
}
}
