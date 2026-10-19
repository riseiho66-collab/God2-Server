#pragma once
#include "handlers/OwnedGuildMembershipConversation.h"
#include "db/SqliteOwnedGuildMembershipRepository.h"
#include "protocol/RecoveredQuestAction.h"
#include <limits>

namespace god2 {
// CUSTOM-0078: toolbar help087B offers explicit create/apply/exit choices.
// Resource key2996 is a CUSTOM append, not an original NPC/service mapping.
// Original/current machine codec, full loader and mode4 consumer are recorded
// in entry-resource-parser-v01 and entry-resource-consumer-v01. Original2995
// catalog remains unchanged. Enable only with the qualified resource bundle.
class OwnedGuildEntryService {
public:
    using Repository=SqliteOwnedGuildMembershipRepository;
    using Owner=OwnedGuildMembershipConversation::Owner;
    using Clock=OwnedGuildMembershipConversation::Clock;
    using Time=Clock::time_point;
    using Resolve=std::function<std::optional<Owner>(std::uint64_t)>;
    using ReadEligible=std::function<std::optional<Repository::Identity>(const Owner&)>;
    using Menu=std::array<std::uint8_t,28>;
    // CUSTOM namespace: preserve existing quest9A and knowledge44 contexts.
    static constexpr std::uint8_t context=0xe7;
    static constexpr std::uint16_t resource_key=2996;
    static constexpr auto lifetime=std::chrono::seconds{30}; // CUSTOM lease
    enum class Choice : std::uint8_t {Create=0,Apply=1,Exit=2};
    struct Lease {
        Owner owner;
        Repository::Identity identity;
        std::uint16_t request{};
        Time opened,expires;
        bool operator==(const Lease&) const=default;
    };
    struct Plan {Lease lease;Menu logical;bool operator==(const Plan&) const=default;};
    OwnedGuildEntryService(Resolve resolve,ReadEligible eligible):
        resolve_(std::move(resolve)),eligible_(std::move(eligible)){}
    std::optional<Plan> prepare(std::uint64_t session,Time now) {
        invalidate(session);
        try {
            if(now>Time::max()-lifetime)return {};
            const auto owner=resolve_(session);
            if(!owner || !valid(*owner) || owner->session!=session)return {};
            const auto identity=eligible_(*owner);
            if(!identity || identity->account_id!=owner->account || identity->character_id!=owner->character ||
                identity->membership_revision!=0)return {};
            auto& generation=generations_[session];
            if(generation==0xffff)return {}; // never wrap a transport nonce
            const Lease lease{*owner,*identity,static_cast<std::uint16_t>(++generation),now,now+lifetime};
            if(!current(lease,now))return {};
            Menu menu{};menu[0]=0x7a;menu[1]=28;menu[3]=4;menu[4]=context;
            menu[5]=static_cast<std::uint8_t>(lease.request);menu[6]=static_cast<std::uint8_t>(lease.request>>8);
            menu[7]=static_cast<std::uint8_t>(resource_key);menu[8]=static_cast<std::uint8_t>(resource_key>>8);
            // reply0 prevents close from producing a second fixed-choice85.
            // name16 and parameter_count0 carry no gameplay authority.
            Plan plan{lease,menu};prepared_.insert_or_assign(session,plan);
            return plan;
        }catch(const std::exception&){return {};}
    }
    bool published(const Plan& plan,Time now) {
        const auto at=prepared_.find(plan.lease.owner.session);
        if(at==prepared_.end() || at->second!=plan)return false;
        prepared_.erase(at);
        if(!current(plan.lease,now))return false;
        pending_.insert_or_assign(plan.lease.owner.session,plan.lease);return true;
    }
    // A rejected enqueue retires only its still-prepared menu. A later menu
    // or an already-published choice is outside this delivery receipt.
    void reject_exact(const Plan& plan) {
        const auto at=prepared_.find(plan.lease.owner.session);
        if(at!=prepared_.end() && at->second==plan)prepared_.erase(at);
    }
    std::optional<Lease> prepare_choice(std::uint64_t session,Time now) {
        observe_world(session,now);
        const auto at=pending_.find(session);return at==pending_.end()?std::nullopt:std::optional{at->second};
    }
    std::optional<Choice> consume(const Lease& lease,const RecoveredQuestAction::Request& action,Time now) {
        const auto at=pending_.find(lease.owner.session);
        if(at==pending_.end() || at->second!=lease)return {};
        if(!current(lease,now)){invalidate(lease.owner.session);return {};}
        if(action.context_byte!=context || action.request_word!=lease.request)return {};
        pending_.erase(at); // bound attempt is one-use, including illegal choices
        // Native handler permits choice4 even for three labels. Enforce all
        // authority here; neither pointer residue nor a client flag grants it.
        if(action.reply_word>2)return {};
        return static_cast<Choice>(action.reply_word);
    }
    void observe_world(std::uint64_t session,Time now) {
        const auto at=pending_.find(session);
        if(at!=pending_.end() && !current(at->second,now))invalidate(session);
        const auto prepared=prepared_.find(session);
        if(prepared!=prepared_.end() && !current(prepared->second.lease,now))invalidate(session);
    }
    bool pending(std::uint64_t session) const{return pending_.contains(session);}
    bool recognizes(std::uint64_t session,const RecoveredQuestAction::Request& action) const {
        const auto at=generations_.find(session);
        return action.context_byte==context && action.request_word &&
            at!=generations_.end() && action.request_word<=at->second;
    }
    void invalidate(std::uint64_t session){pending_.erase(session);prepared_.erase(session);}
    void disconnect(std::uint64_t session){invalidate(session);generations_.erase(session);}
private:
    static bool valid(const Owner& owner) {
        return owner.session && owner.account && owner.character && owner.world_generation &&
            (owner.name_codepage==950 || owner.name_codepage==936);
    }
    bool current(const Lease& lease,Time now) const {
        try {
            const auto generation=generations_.find(lease.owner.session);
            return now>=lease.opened && now<lease.expires && generation!=generations_.end() &&
                generation->second==lease.request && resolve_ && eligible_ &&
                resolve_(lease.owner.session)==std::optional{lease.owner} &&
                eligible_(lease.owner)==std::optional{lease.identity} &&
                resolve_(lease.owner.session)==std::optional{lease.owner};
        }catch(const std::exception&){return false;}
    }
    Resolve resolve_;ReadEligible eligible_;
    std::map<std::uint64_t,Lease> pending_;
    std::map<std::uint64_t,Plan> prepared_;
    std::map<std::uint64_t,std::uint32_t> generations_;
};
}
