#include "game/SharedTaiwanNativeSkillCommandSource.h"
#include <exception>
#include <stdexcept>
#include <thread>
#include <utility>
#include <vector>

namespace god2 {
namespace {
using Source=SharedTaiwanNativeSkillCommandSource;
struct Owner {
    const std::thread::id thread=std::this_thread::get_id();
    const std::shared_ptr<SharedWorldPresence> presence;
    const NativeSkillCatalog& catalog;
    const std::shared_ptr<SharedTaiwanIssuedSkillSource> issued;
    const std::shared_ptr<Source::WorldOwner> world;
    const Source::Budgets budgets;
    bool operating=false,reentered=false,invalidating=false,releasing=false;
    Owner(std::shared_ptr<SharedWorldPresence> common,const NativeSkillCatalog& skills,
        std::shared_ptr<SharedTaiwanIssuedSkillSource> lists,
        std::shared_ptr<Source::WorldOwner> actual,Source::Budgets limits)
        :presence(std::move(common)),catalog(skills),issued(std::move(lists)),world(std::move(actual)),budgets(limits) {}
    ~Owner(){if(thread!=std::this_thread::get_id())std::terminate();}
    void owner() const {
        if(thread!=std::this_thread::get_id())throw std::logic_error("TW C35 game owner mismatch");
    }
    void invalidate() {
        owner();if(!operating && !releasing)return;
        reentered=true;if(invalidating)return;
        invalidating=true;
        struct Reset {bool& active;~Reset(){active=false;}} reset{invalidating};
        issued->invalidate_active();
        const auto actual=world;actual->invalidate_active();
    }
    struct Operation {
        Owner& state;
        explicit Operation(Owner& actual):state(actual) {
            state.owner();
            if(state.operating || state.releasing){state.invalidate();throw std::logic_error("TW C35 reentry rejected");}
            state.operating=true;state.reentered=false;
        }
        ~Operation(){state.operating=false;}
    };
    bool local(Session& session,const Source::Scope& scope,bool before) const {
        const auto& lease=scope.lease;
        return !reentered && !session.closing() && session.id()==lease.session &&
            session.account_id==lease.account && session.character_id==lease.character &&
            (before ? session.state()==SessionState::InBattle && session.battle_generation()==scope.battle_generation :
                session.state()==SessionState::InBattle || session.state()==SessionState::InWorld) &&
            session.recovered_world_ready() &&
            session.common_world_delivery_current(lease.account,lease.character,lease.generation) &&
            !session.common_world_entry_current(lease.account,lease.character,lease.generation);
    }
    bool ready(Session& session,const Source::Scope& scope,bool before) const {
        if(!local(session,scope,before))return false;
        const auto actual=presence->ready_lease(scope.lease.session,scope.lease.account,scope.lease.character);
        const auto saved=presence->saved_position(scope.lease);
        // Recheck pure state AFTER repository observers. After durable action
        // observe real next position/phase, not the old consumed battle tuple.
        return actual && *actual==scope.lease && saved &&
            (!before || *saved==scope.saved_position) && local(session,scope,before);
    }
    std::optional<Source::Scope> capture(Session& session) const {
        if(reentered || session.closing() || session.state()!=SessionState::InBattle ||
           !session.account_id || !session.character_id)return std::nullopt;
        const auto generation=session.battle_generation();
        const auto lease=presence->ready_lease(session.id(),session.account_id,session.character_id);
        if(!lease)return std::nullopt;
        const auto position=presence->saved_position(*lease);
        if(!position)return std::nullopt;
        Source::Scope scope{*lease,*position,generation};
        return ready(session,scope,true)?std::optional{scope}:std::nullopt;
    }
    bool base_definition_current(Session& session,const Source::Scope& scope,const NativeSkillRecord& expected) const {
        if(!ready(session,scope,true))return false;
        const auto actual=catalog.lookup_main_digest_checked(NativeSkillCatalog::current_dataset_id,expected.kind,expected.definition_id);
        return actual && *actual==expected && ready(session,scope,true);
    }
    bool definition_current(Session& session,const Source::Scope& scope,const NativeSkillRecord& expected) const {
        if(!scope.common_definition || !base_definition_current(session,scope,expected))return false;
        const auto shared=catalog.lookup_shared_definition_main(expected.kind,expected.definition_id);
        // Compare the retained whole value; never refresh Scope from a later
        // counterpart observation. Requested TW raw remains the command input.
        return shared && shared->requested_native && *shared->requested_native==expected &&
            shared->definition==*scope.common_definition && ready(session,scope,true);
    }
    bool current(Session& session,const Source::Scope& scope,Source::Check check,
        const Source::Command& command,const Source::Qualification& qualification,
        const SharedTaiwanIssuedSkillSource::Selection& selection) const {
        if(!definition_current(session,scope,command.definition()) || !issued->current(session,selection))return false;
        const auto actual=world;
        if(!actual->current(session,scope,check,command,qualification) || !ready(session,scope,true))return false;
        return issued->current(session,selection) && definition_current(session,scope,command.definition());
    }
    bool complete_reply(const Source::Reply& reply) const {
        if(reply.native_no_reply() || reply.bytes().empty() || reply.bytes().size()>budgets.max_output_bytes)return false;
        // Shape-only complete envelope accounting; no codec/profile guessed.
        std::span<const std::uint8_t> bytes=reply.bytes();std::size_t frames=0;
        while(!bytes.empty()) {
            if(bytes.size()<2 || ++frames>budgets.max_output_frames)return false;
            const auto size=std::size_t{bytes[0]}+(std::size_t{bytes[1]}<<8);
            if(size<4 || size>bytes.size())return false;
            bytes=bytes.subspan(size);
        }
        return true;
    }
    std::optional<Source::Reply> dispatch(Session& session,std::span<const Source::WireRecord> records) {
        Operation operation(*this);
        try {
            const auto actual_session=session.weak_from_this().lock();
            if(actual_session.get()!=&session)return std::nullopt;
            if(records.empty() || records.size()>budgets.max_records)return std::nullopt;
            const std::vector<Source::WireRecord> owned(records.begin(),records.end());
            auto scope=capture(session);if(!scope)return std::nullopt;
            const auto& first=owned.front();
            for(const auto& record:owned)
                if(!TaiwanNativeSkillCommand::parse_wire(record.logical) ||
                   !TaiwanNativeSkillCommand::same_sequence(first,record))return std::nullopt;
            // Actual issued control selects the independent primary/secondary
            // list and BYTE+51/52 actor. A C2S side flag cannot choose a list.
            if(first.kind()>3 || !first.definition_id())return std::nullopt;
            const auto selection=issued->select(session,first.raw_operand());
            if(!selection || first.actor_position()!=selection->lookup().actor_position ||
               first.side_flag()!=selection->lookup().side_flag || !ready(session,*scope,true))return std::nullopt;
            const auto definition=catalog.lookup_main_digest_checked(NativeSkillCatalog::current_dataset_id,first.kind(),first.definition_id());
            if(!definition || definition->source.native_image_sha256!=TaiwanNativeSkillCommand::image_sha256 ||
               *definition!=selection->lookup().definition ||
               !base_definition_current(session,*scope,*definition))return std::nullopt;
            // Enrich only after the original TW digest/image/issued gates. The
            // captured presence/position/battle tuple is never rebased here.
            auto shared=catalog.lookup_shared_definition_main(first.kind(),first.definition_id());
            if(!shared || !shared->requested_native || *shared->requested_native!=*definition ||
               !ready(session,*scope,true) || !issued->current(session,*selection))return std::nullopt;
            scope->common_definition=std::move(shared->definition);
            if(!definition_current(session,*scope,*definition))return std::nullopt;
            const auto actual=world;
            const auto qualification=actual->qualification(session,*scope,owned,*definition);
            if(!qualification || !qualification->actor_position || !qualification->side_flag ||
               *qualification->actor_position!=selection->lookup().actor_position ||
               *qualification->side_flag!=selection->lookup().side_flag ||
               !issued->current(session,*selection) || !definition_current(session,*scope,*definition) ||
               (qualification->formation_sources && qualification->formation_sources->size()>14) ||
               (qualification->formation_identity_sources && qualification->formation_identity_sources->size()>14))return std::nullopt;
            const auto command=TaiwanNativeSkillCommand::parse_qualified(owned,*definition,*qualification);
            if(!command || !current(session,*scope,Source::Check::Qualified,*command,*qualification,*selection) ||
               !current(session,*scope,Source::Check::BeforeAction,*command,*qualification,*selection))return std::nullopt;
            auto reply=actual->action(session,*scope,*command,*qualification);
            // Intended mutation consumes old grant/resources. No old catalog /
            // authority Current is queried here; the actual next receipt owns
            // settlement freshness. Failure cannot undo or replay its prefix.
            if(!reply || !ready(session,*scope,false) || !complete_reply(*reply) ||
               !actual->after_action(session,*scope,*command,*qualification,*reply) ||
               !ready(session,*scope,false) || !complete_reply(*reply)) {
                invalidate();return std::nullopt;
            }
            return reply;
        }catch(...) {
            const auto failure=std::current_exception();
            try{invalidate();}catch(...){}
            std::rethrow_exception(failure);
        }
    }
    void release(Session& session) {
        owner();
        const auto actual_session=session.weak_from_this().lock();
        if(actual_session.get()!=&session)throw std::invalid_argument("TW C35 release requires the actual owned Session");
        if(releasing){invalidate();throw std::logic_error("TW C35 recursive release rejected");}
        releasing=true;
        struct Reset {bool& active;~Reset(){active=false;}} reset{releasing};
        std::exception_ptr failure;
        try{invalidate();}catch(...){failure=std::current_exception();}
        try{const auto actual=world;actual->release(session);}catch(...){if(!failure)failure=std::current_exception();}
        try{issued->release(session);}catch(...){if(!failure)failure=std::current_exception();}
        if(failure)std::rethrow_exception(failure);
    }
};
}
SharedTaiwanNativeSkillCommandSource::Binding SharedTaiwanNativeSkillCommandSource::create(
    std::shared_ptr<SharedWorldPresence> presence,const NativeSkillCatalog& catalog,
    std::shared_ptr<SharedTaiwanIssuedSkillSource> issued,std::shared_ptr<WorldOwner> world,Budgets budgets) {
    if(!presence || !issued || !issued->owns_sources(presence,catalog) || !world || !budgets.max_records || budgets.max_records>14 ||
       budgets.max_output_bytes<4 || !budgets.max_output_frames)
        throw std::invalid_argument("TW C35 requires actual common presence/catalog/action owner and bounded complete replies");
    auto state=std::make_shared<Owner>(std::move(presence),catalog,std::move(issued),std::move(world),budgets);
    return {
        [state](Session& session,std::span<const WireRecord> records){const auto held=state;return held->dispatch(session,records);},
        [state](Session& session){const auto held=state;held->release(session);},
        [state]{const auto held=state;held->invalidate();}
    };
}
}
