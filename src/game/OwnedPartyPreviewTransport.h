#pragma once
#include "game/OwnedPartyDirectory.h"
#include "net/Session.h"
#include "protocol/RecoveredWorldFrame.h"
#include <algorithm>
#include <cstddef>
#include <list>
#include <map>
#include <memory>
#include <optional>
#include <stdexcept>
#include <thread>
#include <utility>
#include <vector>

namespace god2 {
// Actual C91 peer courier only. FIFO Queued is not Written, consent or ACK.
// All methods and Prepared lifetimes belong to the actual serial game owner.
class OwnedPartyPreviewTransport final {
    struct Source {
        OwnedPartyDirectory::Actor actor;
        std::shared_ptr<Session> peer;
        bool current() const {
            // The private INIT proves thread/incarnation before bare owner IDs.
            return peer && actor.session.lock()==peer && actor.initialization.entry_written() &&
                peer->normal_world_initialization_current_on_game(actor.initialization) &&
                peer->id()==actor.session_id && peer->account_id==actor.account &&
                peer->character_id==actor.character && peer->state()==actor.phase &&
                peer->battle_generation()==actor.battle && !peer->closing() && peer->recovered_world_ready();
        }
    };
    struct Recipient {
        std::shared_ptr<Session> peer;
        Session::NormalWorldOutputHandle handle;
        const std::vector<std::uint8_t> expected;
        std::vector<std::uint8_t> logical;
        std::optional<Session::NormalWorldOutputAttempt> attempt;
        Recipient(std::shared_ptr<Session> p,Session::NormalWorldOutputHandle h,
                  const std::vector<std::uint8_t>& bytes)
            :peer(std::move(p)),handle(std::move(h)),expected(bytes),logical(bytes) {}
    };
    struct Flight {
        std::vector<Source> sources;
        std::vector<Recipient> recipients;
        std::shared_ptr<Session> admission_owner;
        std::optional<Session::NormalWorldCallbackAdmission> admission;
        bool committed=false,deferred=false,submitted=false,retired=false;
        bool current() const {
            return !retired && admission_owner && admission &&
                admission_owner->normal_world_callback_admission_current_on_game(*admission) &&
                std::all_of(sources.begin(),sources.end(),[](const auto& s){return s.current();}) &&
                std::all_of(recipients.begin(),recipients.end(),[](const auto& r){
                    return r.peer->normal_world_output_current_on_game(r.handle);
                });
        }
        void retire(bool close) noexcept {
            if(retired)return;
            retired=true;
            for(const auto& r:recipients)r.handle.revoke();
            // Exact held objects only. No successor lookup, model rollback or retry.
            if(close)for(const auto& s:sources)try{s.peer->close();}catch(...){}
        }
        void submit() {
            if(!committed || !deferred || submitted || !current() ||
               admission->status()!=Session::NormalWorldCallbackAdmissionStatus::Admitted)
                throw std::logic_error("Party preview requires actual complete callback admission");
            for(auto& recipient:recipients) {
                if(!current() || recipient.logical!=recipient.expected)
                    throw std::logic_error("Party preview exact deferred projection changed");
                recipient.attempt=recipient.peer->send_normal_world_records(recipient.handle,std::move(recipient.logical));
                if(recipient.attempt->status()==Session::NormalWorldOutputStatus::Failed)
                    throw std::logic_error("Party preview deferred submission failed");
            }
            if(!current())throw std::logic_error("Party preview source changed during deferred submission");
            submitted=true;
        }
        ~Flight(){if(!retired)retire(committed);}
    };
    struct State {
        const std::thread::id game_thread=std::this_thread::get_id();
        const std::size_t capacity;
        std::list<std::shared_ptr<Flight>> flights;
        std::size_t held_sources=0;
        bool stopped=false;
        explicit State(std::size_t c):capacity(c) {}
        void erase(const std::shared_ptr<Flight>& f) noexcept {
            const auto at=std::find(flights.begin(),flights.end(),f);
            if(at!=flights.end()){held_sources-=f->sources.size();flights.erase(at);}
        }
        void stop() noexcept {
            if(stopped)return;
            stopped=true;
            for(const auto& f:flights)f->retire(f->committed);
            flights.clear();held_sources=0;
        }
        ~State(){stop();}
    };
public:
    class Prepared final {
    public:
        Prepared(const Prepared&)=delete;
        Prepared& operator=(const Prepared&)=delete;
        Prepared(Prepared&&)=default;
        Prepared& operator=(Prepared&&)=delete;
        ~Prepared() {
            if(!flight_)return;
            if(!flight_->committed || !flight_->deferred) {
                flight_->retire(flight_->committed);state_->erase(flight_);
            }
        }
        bool current() const {
            return flight_ && !state_->stopped && state_->game_thread==std::this_thread::get_id() && flight_->current();
        }
        // Immediately after actual Directory CAS, before the NativeParty move.
        void mark_committed() noexcept {flight_->committed=true;}
        // Actual two models committed; registry owns Pending admission.
        // No allocation, send, callback or peer close at this handoff.
        void hand_off() noexcept {flight_->deferred=true;}
    private:
        friend class OwnedPartyPreviewTransport;
        std::shared_ptr<State> state_;
        std::shared_ptr<Flight> flight_;
        Prepared(std::shared_ptr<State> s,std::shared_ptr<Flight> f):state_(std::move(s)),flight_(std::move(f)) {}
    };
    explicit OwnedPartyPreviewTransport(std::size_t capacity):state_(std::make_shared<State>(capacity)) {}
    OwnedPartyPreviewTransport(const OwnedPartyPreviewTransport&)=delete;
    OwnedPartyPreviewTransport& operator=(const OwnedPartyPreviewTransport&)=delete;
    ~OwnedPartyPreviewTransport(){stop();}
    std::optional<Prepared> prepare(const std::vector<OwnedPartyDirectory::Actor>& actors,
            const std::map<std::uint64_t,std::shared_ptr<Session>>& peers,
            const std::map<std::uint64_t,std::vector<std::uint8_t>>& projections,
            const std::shared_ptr<Session>& caller,const Session::NormalWorldCallbackAdmission& admission) {
        if(state_->stopped || state_->game_thread!=std::this_thread::get_id() || projections.empty() ||
           state_->flights.size()>=state_->capacity)return std::nullopt;
        if(!caller || !caller->normal_world_callback_admission_current_on_game(admission) ||
           admission.status()!=Session::NormalWorldCallbackAdmissionStatus::Pending)return std::nullopt;
        auto flight=std::make_shared<Flight>();
        flight->admission_owner=caller;flight->admission=admission;
        for(const auto& actor:actors) {
            const auto peer=actor.session.lock();
            if(!peer)return std::nullopt;
            const auto at=std::find_if(flight->sources.begin(),flight->sources.end(),[&](const auto& s){return s.peer==peer;});
            if(at!=flight->sources.end()){if(!at->actor.same(actor))return std::nullopt;continue;}
            flight->sources.push_back({actor,peer});
        }
        if(std::none_of(flight->sources.begin(),flight->sources.end(),[&](const auto& s){return s.peer==caller;}))return std::nullopt;
        if(flight->sources.empty() || flight->sources.size()>state_->capacity-state_->held_sources ||
           !std::all_of(flight->sources.begin(),flight->sources.end(),[](const auto& s){return s.current();}))return std::nullopt;
        if(projections.size()>flight->sources.size())return std::nullopt;
        flight->recipients.reserve(projections.size());
        for(const auto& [id,bytes]:projections) {
            const auto peer=peers.find(id);
            const auto source=std::find_if(flight->sources.begin(),flight->sources.end(),[&](const auto& s){return s.actor.session_id==id;});
            if(peer==peers.end() || source==flight->sources.end() || peer->second!=source->peer || bytes.empty() ||
               bytes.size()>RecoveredWorldFrame::max_logical_size)return std::nullopt;
            // Existing frame supplier validation and all payload storage before CAS.
            (void)RecoveredWorldFrame::encode(bytes);
            auto handle=source->peer->capture_normal_world_output_on_game(source->actor.initialization);
            if(!handle)return std::nullopt;
            try {flight->recipients.emplace_back(source->peer,*handle,bytes);}
            catch(...) {handle->revoke();throw;}
        }
        if(!flight->current())return std::nullopt;
        state_->flights.push_back(flight); // Registry allocation before commit.
        state_->held_sources+=flight->sources.size();
        return Prepared(state_,std::move(flight));
    }
    void settle() noexcept {
        if(state_->stopped)return;
        if(state_->game_thread!=std::this_thread::get_id()){state_->stop();return;}
        for(auto it=state_->flights.begin();it!=state_->flights.end();) {
            const auto f=*it;
            if(!f->committed){++it;continue;}
            bool failed=!f->deferred;
            try {if(!f->current())failed=true;}catch(...) {failed=true;}
            if(!failed && !f->submitted) {
                const auto status=f->admission->status();
                if(status==Session::NormalWorldCallbackAdmissionStatus::Pending){++it;continue;}
                if(status!=Session::NormalWorldCallbackAdmissionStatus::Admitted)failed=true;
                else try {f->submit();}catch(...) {failed=true;}
            }
            bool queued=!failed;
            for(const auto& r:f->recipients) {
                if(!r.attempt || r.attempt->status()==Session::NormalWorldOutputStatus::Failed)failed=true;
                if(!r.attempt || r.attempt->status()!=Session::NormalWorldOutputStatus::Queued)queued=false;
            }
            if(failed || queued) {
                if(failed)f->retire(true);
                else f->retired=true; // Do not revoke a successful queued Write's Data.
                state_->held_sources-=f->sources.size();it=state_->flights.erase(it);
            } else ++it; // Pending has no native timeout or acceptance implication.
        }
    }
    void stop() noexcept {state_->stop();}
private:
    const std::shared_ptr<State> state_;
};
}
