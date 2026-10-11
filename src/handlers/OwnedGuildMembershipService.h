#pragma once
#include "db/SqliteOwnedGuildMembershipRepository.h"
#include "db/DbTypes.h"
#include "game/OwnedGuildMembershipRule.h"
#include "handlers/OwnedGuildMembershipConversation.h"
#include "handlers/OwnedGuildMembershipName.h"
#include "protocol/RecoveredTrade.h"
#include <variant>

namespace god2 {
// CUSTOM-0078: candidate orchestration for real SQL transactions. Application
// calls it only through the disposable loopback lab; the formal player entry
// and complete leader UI are pending.
// The host returns only ready, non-battle, non-transfer owned world snapshots.
class OwnedGuildMembershipService {
public:
    using Repository=SqliteOwnedGuildMembershipRepository;
    using Conversation=OwnedGuildMembershipConversation;
    using Owner=Conversation::Owner;
    using Wire=RecoveredGuildMembership;
    using Time=Conversation::Time;
    using Resolve=std::function<std::optional<Owner>(std::uint64_t)>;
    using ReadWallet=std::function<std::optional<Repository::Wallet>(std::uint64_t,std::uint64_t)>;
    using Rule=std::function<OwnedGuildMembershipPolicy(const OwnedGuildMembershipInput&)>;
    using Result=std::variant<Repository::Created,Repository::Application>;
    OwnedGuildMembershipService(Repository& repository,Resolve resolve,ReadWallet wallet,Rule rule):
        repository_(repository),resolve_(std::move(resolve)),wallet_(std::move(wallet)),rule_(std::move(rule)),
        conversations_(OwnedGuildMembershipName::valid) {}
    std::optional<Wire::Prompt> open(std::uint64_t session,Wire::Operation operation,Time now,
                                     bool qualified_interaction) {
        try {
            if(!qualified_interaction || !resolve_ || !wallet_ || !rule_)return {};
            const auto owner=resolve_(session);if(!owner || owner->session!=session)return {};
            const auto identity=repository_.nonmember(owner->account,owner->character);
            if(repository_.pending(owner->account,owner->character))return {};
            Opening state{*owner,identity,{},{},{}};
            if(operation==Wire::Operation::Create) {
                state.wallet=wallet_(owner->account,owner->character);if(!state.wallet || !identity.role)return {};
                // The host sends legacy27 after create. Reject unrepresentable
                // wallets before a conversation can authorize any SQL debit.
                if(!RecoveredTrade::wallet_amount_representable(state.wallet->amount))return {};
                const auto role=RecoveredRoleLevel::parse(identity.role->logical);if(!role || !role->level())return {};
                state.input={role->level(),state.wallet->amount};state.policy=rule_(state.input);
                if(!state.policy.may_create)return {};
            }
            if(resolve_(session)!=owner)return {};
            const auto prompt=conversations_.open(*owner,operation,now,true);
            if(!prompt)return {};
            openings_.insert_or_assign(session,std::move(state));return prompt;
        }catch(const std::exception&){return {};}
    }
    std::optional<Result> submit(std::uint64_t session,const Wire::Request& request,Time now) {
        const auto at=openings_.find(session);if(at==openings_.end())return {};
        const auto saved=at->second;
        std::optional<Conversation::Accepted> accepted;
        try {
            const auto current=resolve_?resolve_(session):std::nullopt;
            if(!current || current->session!=session) {invalidate(session);return {};}
            accepted=conversations_.consume(*current,request,now,true);
            if(!accepted) {
                if(!conversations_.pending(session))openings_.erase(session);
                return {};
            }
            // Erase before any name conversion, rule evaluation or SQL attempt.
            // Replays cannot retry failed transactions or perform another debit.
            openings_.erase(session);
            if(accepted->owner!=saved.owner)return {};
            const auto name=OwnedGuildMembershipName::decode(accepted->name,saved.owner.name_codepage);
            const auto proof=[this,saved,operation=accepted->operation] {
                if(!resolve_ || resolve_(saved.owner.session)!=std::optional{saved.owner})
                    throw DatabaseError("Guild conversation world lease changed");
                if(operation==Wire::Operation::Create && (!rule_ || rule_(saved.input)!=saved.policy))
                    throw DatabaseError("Guild conversation policy changed");
            };
            const Repository::Proof paired{proof,proof};
            if(accepted->operation==Wire::Operation::Create) {
                if(!saved.wallet || !saved.policy.may_create)return {};
                const Repository::Policy policy{saved.policy.creation_fee,saved.policy.minimum_level,saved.policy.initial_capacity};
                return Result{repository_.create(saved.identity,*saved.wallet,name,policy,paired)};
            }
            const auto target=repository_.find_by_name(name);if(!target)return {};
            return Result{repository_.apply(saved.identity,*target,paired)};
        }catch(const std::exception&) {
            if(accepted || !conversations_.pending(session))openings_.erase(session);
            return {};
        }
    }
    void invalidate(std::uint64_t session) {conversations_.invalidate(session);openings_.erase(session);}
    // Host calls this on benign heartbeat/notifications too, so a transient
    // non-ready or changed owner cannot regain permission by returning later.
    void observe_world(std::uint64_t session) {
        const auto at=openings_.find(session);if(at==openings_.end())return;
        try {
            if(!resolve_ || resolve_(session)!=std::optional{at->second.owner})invalidate(session);
        }catch(const std::exception&) {invalidate(session);}
    }
    void disconnect(std::uint64_t session) {conversations_.disconnect(session);openings_.erase(session);}
    bool pending(std::uint64_t session) const {return conversations_.pending(session);}
private:
    struct Opening {
        Owner owner;Repository::Identity identity;std::optional<Repository::Wallet> wallet;
        OwnedGuildMembershipInput input;OwnedGuildMembershipPolicy policy;
    };
    Repository& repository_;Resolve resolve_;ReadWallet wallet_;Rule rule_;
    Conversation conversations_;std::map<std::uint64_t,Opening> openings_;
};
}
