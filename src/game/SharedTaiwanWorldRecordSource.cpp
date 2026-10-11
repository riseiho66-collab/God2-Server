#include "game/SharedTaiwanWorldRecordSource.h"
#include <exception>
#include <map>
#include <stdexcept>
#include <thread>
#include <utility>

namespace god2 {
SharedTaiwanWorldRecordSource::Reply::Reply(bool silent,std::vector<std::uint8_t> actual)
    :no_reply_(silent),bytes_(std::move(actual)) {}
SharedTaiwanWorldRecordSource::Reply SharedTaiwanWorldRecordSource::Reply::wire(std::vector<std::uint8_t> bytes) {
    if(bytes.empty())throw std::invalid_argument("TW mixed-record wire reply requires actual encrypted native envelopes");
    return Reply(false,std::move(bytes));
}
SharedTaiwanWorldRecordSource::Reply SharedTaiwanWorldRecordSource::Reply::no_reply() {return Reply(true,{});}
bool SharedTaiwanWorldRecordSource::Reply::native_no_reply() const noexcept {return no_reply_;}
const std::vector<std::uint8_t>& SharedTaiwanWorldRecordSource::Reply::bytes() const noexcept {return bytes_;}
namespace {
using Source=SharedTaiwanWorldRecordSource;
struct Slot {
    const Source::Lease lease;
    const std::weak_ptr<Session> connection;
    bool live=true;
    Slot(const Source::Lease& actual,const std::shared_ptr<Session>& session):lease(actual),connection(session) {}
};
struct Work {
    Source::Run run;
    std::vector<RecoveredMovement::Request> movements;
    std::vector<TaiwanNativeSkillCommand::WireRecord> skills;
};
struct Owner {
    const std::thread::id thread=std::this_thread::get_id();
    const std::shared_ptr<SharedWorldPresence> presence;
    SharedTaiwanMovementSource::Binding movement;
    Source::OtherBinding others;
    Source::Current current;
    const Source::Budgets budgets;
    const std::size_t capacity;
    std::map<std::uint64_t,std::shared_ptr<Slot>> slots;
    std::shared_ptr<Slot> active;
    bool operating=false,reentered=false,invalidating=false;
    Owner(std::shared_ptr<SharedWorldPresence> common,SharedTaiwanMovementSource::Binding actual,
        Source::OtherBinding remaining,Source::Current qualified,Source::Budgets limits,std::size_t count)
        :presence(std::move(common)),movement(std::move(actual)),others(std::move(remaining)),
         current(std::move(qualified)),budgets(limits),capacity(count) {}
    ~Owner() {
        if(thread!=std::this_thread::get_id())std::terminate();
        operating=true;reentered=true;
        for(auto& row:slots)row.second->live=false;
        slots.clear();active.reset();others={};current={};movement={};
        // Bookkeeping/strong callback ownership only. Actual Application drain
        // owns controller/resource/common lifecycle cleanup while DB is alive.
    }
    void owner() const {
        if(thread!=std::this_thread::get_id())throw std::logic_error("TW mixed-record source game owner mismatch");
    }
    void poison() {
        owner();
        if(!operating)return;
        reentered=true;if(active)active->live=false;
        if(invalidating)return;
        invalidating=true;
        struct Reset {bool& flag;~Reset(){flag=false;}} reset{invalidating};
        std::exception_ptr failure;
        // Each callback copy is protected too: allocation failure must not
        // skip another actual child, and nested invalidation cannot recurse.
        try {const auto remaining=others.invalidate_active;remaining();}catch(...) {failure=std::current_exception();}
        try {const auto selection=others.selection_item;if(selection)selection->invalidate_active();}
        catch(...) {if(!failure)failure=std::current_exception();}
        try {const auto move=others.inventory_move;if(move)move->invalidate_active();}
        catch(...) {if(!failure)failure=std::current_exception();}
        try {const auto skill=others.native_skills;if(skill)skill->invalidate_active();}
        catch(...) {if(!failure)failure=std::current_exception();}
        try {const auto invalidate=movement.invalidate_active;invalidate();}catch(...) {if(!failure)failure=std::current_exception();}
        if(failure)std::rethrow_exception(failure);
    }
    struct Operation {
        Owner& state;
        explicit Operation(Owner& actual):state(actual) {
            state.owner();
            if(state.operating) {state.poison();throw std::logic_error("TW mixed-record source reentry rejected");}
            state.operating=true;state.reentered=false;
        }
        ~Operation() {state.active.reset();state.operating=false;}
    };
    bool local(Session& session,const Source::Lease& lease) const {
        const auto phase=session.state();
        if(reentered || session.closing() || session.id()!=lease.session || session.account_id!=lease.account ||
           session.character_id!=lease.character || (phase!=SessionState::InWorld && phase!=SessionState::InBattle) ||
           !session.recovered_world_ready() ||
           !session.common_world_delivery_current(lease.account,lease.character,lease.generation) ||
           session.common_world_entry_current(lease.account,lease.character,lease.generation))return false;
        return true;
    }
    bool ready(Session& session,const Source::Lease& lease) const {
        if(!local(session,lease))return false;
        const auto actual=presence->ready_lease(lease.session,lease.account,lease.character);
        return actual && *actual==lease && local(session,lease);
    }
    bool stored(Session& session,const std::shared_ptr<Slot>& slot) const {
        const auto exact=[&] {
            if(!slot || !slot->live || slot->connection.lock().get()!=&session)return false;
            const auto found=slots.find(slot->lease.session);
            return found!=slots.end() && found->second==slot;
        };
        return exact() && ready(session,slot->lease) && exact() && local(session,slot->lease);
    }
    std::optional<Source::Scope> snapshot(Session& session,const std::shared_ptr<Slot>& slot,
        std::size_t run,std::size_t completed,std::size_t bytes,std::size_t frames) const {
        if(!stored(session,slot))return std::nullopt;
        const auto phase=session.state();const auto battle=session.battle_generation();
        const auto saved=presence->saved_position(slot->lease);
        // Repository observers can reject/reenter and then return data. Fence
        // the actual slot and complete local source again before any next run.
        if(!saved || !stored(session,slot) || session.state()!=phase || session.battle_generation()!=battle)return std::nullopt;
        return Source::Scope{slot->lease,*saved,phase,battle,run,completed,bytes,frames};
    }
    bool qualify(Session& session,const std::shared_ptr<Slot>& slot,Source::Check check,
        std::span<const Source::Record> records,std::span<const Source::Run> runs,
        std::size_t run,std::size_t completed,std::span<const std::uint8_t> output,std::size_t frames) {
        const auto before=snapshot(session,slot,run,completed,output.size(),frames);
        if(!before)return false;
        const auto observe=current;
        const bool actual=observe(session,check,*before,records,runs,output);
        const auto after=snapshot(session,slot,run,completed,output.size(),frames);
        return actual && after && before->lease==after->lease && before->saved_position==after->saved_position &&
            before->phase==after->phase && before->battle_generation==after->battle_generation;
    }
    std::optional<std::size_t> frame_count(std::span<const std::uint8_t> output) const {
        std::size_t frames=0;
        for(std::size_t at=0;at<output.size();) {
            if(output.size()-at<2)return std::nullopt;
            const auto bytes=std::size_t(output[at])+256u*output[at+1];
            if(bytes<4 || bytes>RecoveredWorldFrame::max_logical_size+3 || bytes>output.size()-at ||
               frames==budgets.max_output_frames)return std::nullopt;
            at+=bytes;++frames;
        }
        // Ciphertext is retained exactly. Existing Session performs its full
        // native envelope/checksum validation; no decode/repack in this source.
        return frames;
    }
    std::optional<std::vector<std::uint8_t>> records(Session& session,std::span<const Source::Record> records) {
        Operation operation(*this);
        const auto actual_lease=presence->ready_lease(session.id(),session.account_id,session.character_id);
        if(!actual_lease || !ready(session,*actual_lease))return std::nullopt;
        auto found=slots.find(session.id());
        if(found==slots.end()) {
            if(slots.size()>=capacity)return std::nullopt;
            active=std::make_shared<Slot>(*actual_lease,session.shared_from_this());
            slots.emplace(actual_lease->session,active);
        }else active=found->second;
        const auto slot=active;
        // A stale caller must not terminalize a different Session or successor
        // lease occupying the same bookkeeping key.
        if(slot->connection.lock().get()!=&session || slot->lease!=*actual_lease)return std::nullopt;
        if(!stored(session,slot)) {slot->live=false;return std::nullopt;}
        try {
            if(records.empty() || records.size()>budgets.max_records)throw std::invalid_argument("TW mixed native record budget rejected");
            std::vector<Work> prepared;std::vector<Source::Run> runs;
            // Prepare every run and allocate all movement vectors before any
            // policy/gameplay callback can commit a prefix.
            for(std::size_t at=0;at<records.size();) {
                if(records[at].valueless_by_exception())throw std::invalid_argument("TW mixed native record has no variant");
                const auto classify=[this](const Source::Record& record) {
                    if(std::holds_alternative<RecoveredMovement::Request>(record))return Source::Kind::Movement;
                    if(others.selection_item && std::holds_alternative<RecoveredSelectionItemRequest::Request>(record))
                        return Source::Kind::SelectionItem;
                    if(others.inventory_move && std::holds_alternative<RecoveredInventoryMoveRequest::Request>(record))
                        return Source::Kind::InventoryMove;
                    if(others.native_skills && std::holds_alternative<TaiwanNativeSkillCommand::WireRecord>(record))
                        return Source::Kind::NativeSkill;
                    return Source::Kind::Others;
                };
                const auto kind=classify(records[at]);const bool moving=kind==Source::Kind::Movement;
                std::size_t end=at+1;
                if(kind==Source::Kind::NativeSkill) {
                    const auto& first=std::get<TaiwanNativeSkillCommand::WireRecord>(records[at]);
                    while(std::get<TaiwanNativeSkillCommand::WireRecord>(records[end-1]).continuation()) {
                        if(end==records.size() || end-at>=RecoveredSkillCommand::max_sequence_records ||
                           records[end].valueless_by_exception() || classify(records[end])!=kind ||
                           !TaiwanNativeSkillCommand::same_sequence(first,
                               std::get<TaiwanNativeSkillCommand::WireRecord>(records[end])))
                            throw std::invalid_argument("TW native skill run requires one complete original sequence");
                        ++end;
                    }
                }else if(kind!=Source::Kind::SelectionItem && kind!=Source::Kind::InventoryMove)
                    while(end<records.size() && !records[end].valueless_by_exception() && classify(records[end])==kind)++end;
                if(end==at || prepared.size()>=budgets.max_runs)throw std::invalid_argument("TW mixed native run budget rejected");
                Work work{{at,end-at,kind},{},{}};
                if(moving) {
                    work.movements.reserve(end-at);
                    for(std::size_t i=at;i<end;++i) {
                        const auto request=std::get<RecoveredMovement::Request>(records[i]);
                        if(!RecoveredNativeMovement::ordinary_request(request))
                            throw std::invalid_argument("TW mixed movement ordinary ring contract rejected");
                        work.movements.push_back(request);
                    }
                }else if(kind==Source::Kind::NativeSkill) {
                    work.skills.reserve(end-at);
                    for(std::size_t i=at;i<end;++i)
                        work.skills.push_back(std::get<TaiwanNativeSkillCommand::WireRecord>(records[i]));
                }
                runs.push_back(work.run);prepared.push_back(std::move(work));at=end;
            }
            std::vector<std::uint8_t> output;output.reserve(budgets.max_output_bytes);
            std::size_t completed=0,frames=0;
            if(!qualify(session,slot,Source::Check::BeforeBatch,records,runs,0,0,output,0))
                throw std::runtime_error("TW mixed whole-batch native qualification failed");
            for(std::size_t index=0;index<prepared.size();++index) {
                const auto& work=prepared[index];
                if(work.run.kind==Source::Kind::Movement && session.state()!=SessionState::InWorld)
                    throw std::invalid_argument("TW mixed movement requires actual InWorld phase");
                if(work.run.kind==Source::Kind::NativeSkill && session.state()!=SessionState::InBattle)
                    throw std::invalid_argument("TW native skill requires actual InBattle phase");
                if(!qualify(session,slot,Source::Check::BeforeRun,records,runs,index,completed,output,frames))
                    throw std::runtime_error("TW mixed native run qualification failed");
                std::vector<std::uint8_t> response;
                if(work.run.kind==Source::Kind::Movement) {
                    const auto dispatch=movement.movement;
                    response=dispatch(session,work.movements);
                    if(response.empty())throw std::runtime_error("TW mixed movement omitted actual native reply");
                }else {
                    std::optional<Source::Reply> reply;
                    if(work.run.kind==Source::Kind::SelectionItem) {
                        const auto* request=std::get_if<RecoveredSelectionItemRequest::Request>(&records[work.run.offset]);
                        const auto input=request?session.take_world_selection_input(*request):std::nullopt;
                        if(!input || !others.selection_item)throw std::runtime_error("TW C28 actual original input unavailable");
                        const auto dispatch=others.selection_item->dispatch;reply=dispatch(session,*input);
                    }else if(work.run.kind==Source::Kind::InventoryMove) {
                        const auto* request=std::get_if<RecoveredInventoryMoveRequest::Request>(&records[work.run.offset]);
                        if(!request||!others.inventory_move)throw std::runtime_error("TW C24 actual original run unavailable");
                        const auto dispatch=others.inventory_move->dispatch;reply=dispatch(session,*request);
                    }else if(work.run.kind==Source::Kind::NativeSkill) {
                        if(!others.native_skills)throw std::runtime_error("TW native skill owner unavailable");
                        const auto dispatch=others.native_skills->dispatch;reply=dispatch(session,work.skills);
                    }else {
                        const auto dispatch=others.records;reply=dispatch(session,records.subspan(work.run.offset,work.run.count));
                    }
                    if(!reply || (reply->native_no_reply() && !reply->bytes().empty()) ||
                       (!reply->native_no_reply() && reply->bytes().empty()))
                        throw std::runtime_error("TW mixed Others lacks explicit native response decision");
                    response=reply->bytes();
                }
                if(response.size()>budgets.max_output_bytes-output.size())
                    throw std::runtime_error("TW mixed native output byte budget exceeded after committed prefix");
                const auto count=frame_count(response);
                if(!count || *count>budgets.max_output_frames-frames)
                    throw std::runtime_error("TW mixed native encrypted frame boundary/budget rejected");
                // Original encrypted envelopes and maximal run order unchanged.
                output.insert(output.end(),response.begin(),response.end());frames+=*count;completed+=work.run.count;
                if(!qualify(session,slot,Source::Check::AfterRun,records,runs,index,completed,output,frames))
                    throw std::runtime_error("TW mixed native advanced-prefix qualification failed");
            }
            if(completed!=records.size() || !qualify(session,slot,Source::Check::BeforeReturn,records,runs,
                prepared.size(),completed,output,frames))throw std::runtime_error("TW mixed final native source qualification failed");
            return output;
        }catch(...) {
            slot->live=false; // Terminal for this exact stored generation until lifecycle release.
            // Actual handler prefixes may already be durable. No rollback,
            // replay, tick discard or fabricated failure/success packet.
            throw;
        }
    }
    void release(Session& session) {
        Operation operation(*this);
        const auto found=slots.find(session.id());if(found==slots.end())return;
        if(found->second->connection.lock().get()!=&session || found->second->lease.session!=session.id())
            throw std::invalid_argument("TW mixed-record bookkeeping cleanup Session mismatch");
        found->second->live=false;slots.erase(found);
        std::exception_ptr failure;
        try {const auto release=others.release;release(session);}catch(...) {failure=std::current_exception();}
        try {const auto selection=others.selection_item;if(selection)selection->release(session);}
        catch(...) {if(!failure)failure=std::current_exception();}
        try {const auto move=others.inventory_move;if(move)move->release(session);}
        catch(...) {if(!failure)failure=std::current_exception();}
        try {const auto skill=others.native_skills;if(skill)skill->release(session);}
        catch(...) {if(!failure)failure=std::current_exception();}
        if(failure)std::rethrow_exception(failure);
        // Application separately performs actual movement/resource retirement.
    }
};
}
SharedTaiwanWorldRecordSource::Binding SharedTaiwanWorldRecordSource::create(
    std::shared_ptr<SharedWorldPresence> presence,SharedTaiwanMovementSource::Binding movement,
    OtherBinding others,Current current,Budgets budgets,std::size_t capacity) {
    if(!presence || !movement.movement || !movement.release || !movement.invalidate_active || !movement.retire ||
       !others.records || !others.release || !others.invalidate_active || !current || !capacity || !budgets.max_records || !budgets.max_runs ||
       budgets.max_output_bytes<4 || !budgets.max_output_frames)
        throw std::invalid_argument("TW mixed-record source requires exact common owner, complete actual movement/Others/Current/budgets/capacity");
    if(others.selection_item && (!others.selection_item->dispatch || !others.selection_item->release ||
       !others.selection_item->invalidate_active))throw std::invalid_argument("TW C28 requires complete actual typed owner");
    const bool native_selection_input=others.selection_item.has_value();
    if(others.inventory_move && (!others.inventory_move->dispatch || !others.inventory_move->release ||
       !others.inventory_move->invalidate_active))throw std::invalid_argument("TW C24 requires complete actual bag owner");
    const auto spectator6e=others.spectator6e;
    const auto spectator_close=others.spectator_close;
    if(others.native_skills && (!others.native_skills->dispatch || !others.native_skills->release ||
       !others.native_skills->invalidate_active))throw std::invalid_argument("TW C35 requires complete actual skill owner");
    const bool native_skill_commands=others.native_skills.has_value();
    auto owner=std::make_shared<Owner>(std::move(presence),std::move(movement),std::move(others),std::move(current),budgets,capacity);
    return {
        [owner](Session& session,std::span<const Record> records){return owner->records(session,records);},
        [owner](Session& session){owner->release(session);},
        [owner]{owner->poison();},
        spectator6e,spectator_close,native_selection_input,native_skill_commands
    };
}
}
