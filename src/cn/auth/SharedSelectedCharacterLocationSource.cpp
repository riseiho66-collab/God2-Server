#include "cn/auth/SharedSelectedCharacterLocationSource.h"
#include "cn/protocol/CnCharacterSummary.h"
#include <algorithm>
#include <exception>
#include <stdexcept>
#include <thread>

namespace god2::cn {
namespace {
using Source=SharedSelectedCharacterLocationSource;
std::optional<Source::Location> first_location(
    const SharedAccountDirectorySource::Plan& directory,Source::Scope scope) {
    if(!directory.current())return std::nullopt;
    const auto& catalog=directory.catalog();
    const auto group=std::find_if(catalog.begin(),catalog.end(),[&](const auto& entry) {
        return entry.header.index==scope.target.group;
    });
    if(group==catalog.end() || scope.target.server>=group->configured_server_slots ||
       scope.target.server>=10 ||
       !(group->header.enabled_servers&(std::uint16_t{1}<<scope.target.server)))return std::nullopt;
    // NativeC6C0/C760/C900: first nonzero raw BYTE+0 in selected server,
    // keeping GROUP-wide node ordinal and the actual four raw bytes.
    for(std::size_t node=0;node<group->nodes.size();++node) {
        const auto& value=group->nodes[node];
        if(value.endpoint.server_index!=scope.target.server)continue;
        for(std::size_t row=0;row<value.locations.size();++row)
            if(value.locations[row].raw[0])return Source::Location{value.locations[row],node,row};
    }
    // Native empty-scan zero return is not a source for a fabricated07 row.
    return std::nullopt;
}
struct Preparing {
    bool& busy;
    bool& terminal;
    const int exceptions=std::uncaught_exceptions();
    Preparing(bool& value,bool& invalid):busy(value),terminal(invalid){busy=true;}
    ~Preparing(){if(std::uncaught_exceptions()>exceptions)terminal=true;busy=false;}
};
}
SharedSelectedCharacterLocationSource::State1A::State1A(Scope scope,std::uint64_t revision,
    SelectedRow row,Current current)
    :scope_(scope),revision_(revision),selected_(row),current_(std::move(current)) {}
std::optional<SharedSelectedCharacterLocationSource::State1A>
SharedSelectedCharacterLocationSource::State1A::from_source(Scope scope,std::uint64_t revision,
    SelectedRow row,Current current) {
    if(!scope.account || scope.target.group>=64 || scope.target.server>=10 || !revision ||
       row.native_row_ordinal>=god2cn::CnCharacterSummary::capacity || !row.character || !current)
        return std::nullopt;
    return State1A(scope,revision,row,std::move(current));
}
SharedAccountSelection::SummarySource SharedSelectedCharacterLocationSource::bind(
    std::uint64_t account,SharedAccountDirectorySource::Plan directory,
    SharedAccountSelection::SummarySource source,Config config) {
    if(!account || !directory.current() || !source || !config.prepare)
        throw std::invalid_argument("CN selected location requires actual account/directory/summary/state1A source");
    struct State {
        std::uint64_t account;
        SharedAccountDirectorySource::Plan directory;
        SharedAccountSelection::SummarySource summary;
        Prepare prepare;
        const std::thread::id owner=std::this_thread::get_id();
        bool busy=false;
        // Nested summary/current observation permanently invalidates this
        // bound account source and every retained proof. Never reset/retry it.
        bool terminal=false;
        State(std::uint64_t id,SharedAccountDirectorySource::Plan plan,
            SharedAccountSelection::SummarySource source,Prepare current)
            :account(id),directory(std::move(plan)),summary(std::move(source)),prepare(std::move(current)) {}
    };
    auto state=std::make_shared<State>(account,std::move(directory),std::move(source),std::move(config.prepare));
    return [state=std::move(state)](std::uint64_t account,SharedWorldAdmission::Target target)
        ->std::optional<Summary> {
        if(state->owner!=std::this_thread::get_id())throw std::logic_error("CN selected location game owner mismatch");
        if(state->busy) {state->terminal=true;return std::nullopt;}
        if(state->terminal || account!=state->account || !state->directory.current())return std::nullopt;
        Preparing preparing(state->busy,state->terminal);
        const Scope scope{account,target};
        auto value=state->summary(account,target);
        if(state->terminal || !state->directory.current() || !value || value->scope_!=scope || !value->current_)
            return std::nullopt;
        const auto native=god2cn::CnCharacterSummary::read(value->record_);
        const auto location=first_location(state->directory,scope);
        if(!native || !location || value->character_ids_.size()!=native->count())return std::nullopt;
        const Input input{scope,value->record_,value->character_ids_,value->account_snapshot_,
                          state->directory.catalog(),*location};
        if(state->terminal || !state->directory.current())return std::nullopt;
        auto selected=state->prepare(input);
        if(state->terminal || !state->directory.current() || !selected || selected->scope_!=scope ||
           selected->selected_.native_row_ordinal>=native->count())return std::nullopt;
        const auto row=selected->selected_.native_row_ordinal;
        if(value->character_ids_[row]!=selected->selected_.character ||
           std::none_of(value->account_snapshot_.begin(),value->account_snapshot_.end(),[&](const auto& root) {
               return root.id==selected->selected_.character && root.account_id==scope.account;
           }))return std::nullopt;
        auto local=value->record_;
        // Wire07 opcode+count+flags precede row. Raw payload offsets+0x22,
        // +0x23,WORD+0x24 are character-row+0x20,+0x21,WORD+0x22.
        const auto start=std::size_t{3}+row*god2cn::CnCharacterSummary::character_stride+0x20;
        std::copy(location->original.raw.begin(),location->original.raw.end(),local.begin()+start);
        const Observation observation{input,selected->selected_,local};
        const auto observe=[&](auto&& callback) {
            if(state->terminal || !state->directory.current())return false;
            const bool accepted=callback();
            return !state->terminal && state->directory.current() && accepted;
        };
        if(!observe([&]{return value->current_(scope,Summary::Check::Prepared);}) ||
           !observe([&]{return selected->current_(scope,selected->revision_,Summary::Check::Prepared,observation);}) ||
           !observe([&]{return value->current_(scope,Summary::Check::Prepared);}))return std::nullopt;
        // Retain full immutable input/output and proof; returned original07,
        // ordered IDs/common roots and original issuer are never replaced.
        struct Proof {
            Scope scope;
            god2cn::Bytes native,local;
            std::vector<std::uint64_t> ids;
            std::vector<RecoveredCharacter> roots;
            Location location;
            State1A state1a;
            Proof(Scope s,god2cn::Bytes original,god2cn::Bytes projected,
                std::vector<std::uint64_t> ordered_ids,std::vector<RecoveredCharacter> account_roots,
                Location chosen,State1A proof)
                :scope(s),native(std::move(original)),local(std::move(projected)),ids(std::move(ordered_ids)),
                 roots(std::move(account_roots)),location(chosen),state1a(std::move(proof)) {}
        };
        auto proof=std::make_shared<const Proof>(scope,value->record_,std::move(local),
            value->character_ids_,value->account_snapshot_,*location,std::move(*selected));
        auto original=std::move(value->current_);
        value->current_=[state,proof,original=std::move(original)](const Scope& actual,Summary::Check check) {
            // Wrong-thread requests cannot touch game-affine poison flags.
            if(state->owner!=std::this_thread::get_id())return false;
            if(state->busy) {state->terminal=true;return false;}
            if(state->terminal || actual!=proof->scope ||
               !state->directory.current())return false;
            Preparing preparing(state->busy,state->terminal);
            const Input input{actual,proof->native,proof->ids,proof->roots,state->directory.catalog(),proof->location};
            const Observation observation{input,proof->state1a.selected_,proof->local};
            const auto observe=[&](auto&& callback) {
                if(state->terminal || !state->directory.current())return false;
                const bool accepted=callback();
                return !state->terminal && state->directory.current() && accepted;
            };
            return observe([&]{return original(actual,check);}) &&
                observe([&]{return proof->state1a.current_(actual,proof->state1a.revision_,check,observation);}) &&
                observe([&]{return original(actual,check);});
        };
        return value;
    };
}
}
