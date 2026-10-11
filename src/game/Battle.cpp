#include "game/Battle.h"
#include "game/ExtendedHealthAmount.h"
#include <algorithm>
#include <limits>
#include <stdexcept>
#include <type_traits>
#include <sstream>
#include <locale>
namespace god2 {
Battle::Battle(std::uint64_t id, std::span<const BattleActor> actors, std::uint32_t seed,
        BattleNumericProfile profile)
    : snapshot_{id,1,BattleState::Active,{}}, rng_(seed) {
    if (!id || actors.size()<2 || actors.size()>28 ||
        (profile!=BattleNumericProfile::LegacyCustom && profile!=BattleNumericProfile::ExtendedHealth64))
        throw std::invalid_argument("Battle requires ID and 2..28 actors");
    snapshot_.numeric_profile=profile;
    std::array<bool,2> sides{};
    for (const auto& actor : actors) {
        if (actor.position>=28 || snapshot_.actors[actor.position] || !actor.hp ||
            actor.hp>actor.max_hp || actor.mp>actor.max_mp ||
            !ExtendedHealthAmount::from(actor.hp) || !ExtendedHealthAmount::from(actor.max_hp) ||
            actor.max_mp>1'000'000 ||
            (profile==BattleNumericProfile::LegacyCustom &&
             (actor.max_hp>1'000'000 || actor.physical_attack>1'000'000 ||
              actor.magical_attack>1'000'000 || actor.physical_defense>1'000'000 ||
              actor.magical_defense>1'000'000)))
            throw std::invalid_argument("Invalid explicit battle actor");
        snapshot_.actors[actor.position]=actor;
        sides[actor.position/14]=true;
    }
    if (!sides[0] || !sides[1]) throw std::invalid_argument("Battle requires opposing sides");
}
std::vector<std::uint8_t> Battle::revive(std::uint64_t controller,std::uint64_t revision,
        std::uint8_t source,std::uint8_t target,const RevivalRule& rule,const RevivalEncode& encode) {
    if(!active() || revision!=snapshot_.revision || revision==std::numeric_limits<std::uint64_t>::max() ||
       !rule || !encode || source>=28 || target>=28 || source==target || source/14!=target/14 ||
       !snapshot_.actors[source] || !snapshot_.actors[target] ||
       snapshot_.actors[source]->controller!=controller || !snapshot_.actors[source]->hp ||
       snapshot_.actors[target]->hp)
        throw std::invalid_argument("Invalid, stale or unauthorized revival");
    const auto projected=rule({snapshot_.actors[target]->max_hp,snapshot_.numeric_profile});
    if(!projected.hp || !ExtendedHealthAmount::from(projected.hp) ||
       projected.hp>snapshot_.actors[target]->max_hp ||
       !projected.mp_cost || projected.mp_cost>1'000'000)
        throw std::invalid_argument("Invalid revival rule result");
    if(projected.mp_cost>snapshot_.actors[source]->mp)
        throw InsufficientBattleMp(snapshot_.actors[source]->mp,projected.mp_cost);
    auto staged=snapshot_;
    staged.actors[source]->mp=RecoveredBattleDelta::apply(staged.actors[source]->mp,
        0u-projected.mp_cost,staged.actors[source]->max_mp);
    if(staged.numeric_profile==BattleNumericProfile::LegacyCustom) {
        // Legacy actor maximum was admitted under the original 1m bound.
        staged.actors[target]->hp=RecoveredBattleDelta::apply(0,
            static_cast<std::uint32_t>(projected.hp),static_cast<std::uint32_t>(staged.actors[target]->max_hp));
    } else {
        const auto health=ExtendedHealthAmount::apply(0,staged.actors[target]->max_hp,
            {static_cast<std::int64_t>(projected.hp)});
        if(!health)throw std::invalid_argument("Invalid extended revival health");
        staged.actors[target]->hp=health->value();
    }
    ++staged.revision;
    auto wire=encode(staged,{source,target,projected.hp,projected.mp_cost});
    if(wire.empty()) throw std::invalid_argument("Revival encoder returned no response");
    static_assert(std::is_nothrow_copy_assignable_v<BattleSnapshot>);
    snapshot_=staged;
    return wire;
}
bool Battle::active() const noexcept { return snapshot_.state == BattleState::Active; }

BattleCheckpoint Battle::checkpoint() const {
    std::ostringstream out;out.imbue(std::locale::classic());out<<rng_;
    if(!out) throw std::runtime_error("Battle random state serialization failed");
    return {snapshot_.numeric_profile==BattleNumericProfile::LegacyCustom?1u:2u,snapshot_,out.str()};
}
Battle Battle::restore(const BattleCheckpoint& checkpoint) {
    const auto& state=checkpoint.snapshot;
    if(!((checkpoint.version==1 && state.numeric_profile==BattleNumericProfile::LegacyCustom) ||
         (checkpoint.version==2 && state.numeric_profile==BattleNumericProfile::ExtendedHealth64)) ||
       !state.id || !state.revision ||
       (state.state!=BattleState::Active && state.state!=BattleState::Finished) ||
       checkpoint.random_state.empty() || checkpoint.random_state.size()>10000)
        throw std::invalid_argument("Invalid battle checkpoint header");
    std::array<bool,2> present{},living{};
    for(std::size_t slot=0;slot<state.actors.size();++slot) if(state.actors[slot]) {
        const auto& actor=*state.actors[slot];
        if(actor.position!=slot || !actor.max_hp || actor.hp>actor.max_hp || actor.mp>actor.max_mp ||
           !ExtendedHealthAmount::from(actor.hp) || !ExtendedHealthAmount::from(actor.max_hp) ||
           actor.max_mp>1'000'000 ||
           (state.numeric_profile==BattleNumericProfile::LegacyCustom &&
            (actor.max_hp>1'000'000 || actor.physical_attack>1'000'000 ||
             actor.magical_attack>1'000'000 || actor.physical_defense>1'000'000 || actor.magical_defense>1'000'000)))
            throw std::invalid_argument("Invalid checkpoint actor");
        present[slot/14]=true;
        living[slot/14]=living[slot/14] || actor.hp!=0;
    }
    if(!present[0] || !present[1] ||
       (state.state==BattleState::Active && (!living[0] || !living[1] || state.victorious_side)) ||
       (state.state==BattleState::Finished && (living[0]==living[1] || !state.victorious_side ||
         *state.victorious_side!=(living[0]?0:1))))
        throw std::invalid_argument("Inconsistent checkpoint outcome");
    std::istringstream input(checkpoint.random_state);input.imbue(std::locale::classic());
    // MSVC emits 624 rotated words; other runtimes may append an engine cursor.
    std::ostringstream layout;layout.imbue(std::locale::classic());layout<<std::mt19937{};
    std::istringstream tokens(layout.str());tokens.imbue(std::locale::classic());
    std::uint64_t token{};std::size_t count=0;
    while(tokens>>token) ++count;
    if(count!=std::mt19937::state_size && count!=std::mt19937::state_size+1)
        throw std::invalid_argument("Unsupported checkpoint random layout");
    for(std::size_t index=0;index<count;++index) {
        std::uint64_t value{};
        if(!(input>>value) || value>(index==std::mt19937::state_size ?
            std::mt19937::state_size : std::uint64_t{0xffffffff}))
            throw std::invalid_argument("Checkpoint random word or cursor out of range");
    }
    input>>std::ws;
    if(!input.eof()) throw std::invalid_argument("Trailing checkpoint random state");
    input.clear();input.seekg(0);
    std::mt19937 rng;
    if(!(input>>rng)) throw std::invalid_argument("Invalid checkpoint random state");
    input>>std::ws;
    if(!input.eof()) throw std::invalid_argument("Trailing checkpoint random state");
    // Require the canonical representation emitted by our standard-library runtime.
    std::ostringstream canonical;canonical.imbue(std::locale::classic());canonical<<rng;
    if(canonical.str()!=checkpoint.random_state)
        throw std::invalid_argument("Noncanonical checkpoint random state");
    return Battle(state,std::move(rng));
}

std::vector<std::uint8_t> Battle::act(std::uint64_t controller, std::uint64_t revision,
        const BattleAction& action, const Rule& rule, const Encode& encode) {
    if (!active() || revision!=snapshot_.revision || revision==std::numeric_limits<std::uint64_t>::max() ||
        !rule || !encode || action.source>=28 || !snapshot_.actors[action.source] ||
        action.targets.empty() || action.targets.size()>14 || action.power_percent>10000 ||
        action.defense_percent>100 || action.critical_chance_bp>10000 ||
        action.critical_multiplier_percent<100 || action.critical_multiplier_percent>1000)
        throw std::invalid_argument("Invalid or stale battle action");
    const auto& source=*snapshot_.actors[action.source];
    if (source.controller!=controller || !source.hp)
        throw std::invalid_argument("Battle ownership or life check failed");
    std::array<bool,28> targeted{};
    for (const auto target : action.targets) {
        if (target>=28 || targeted[target] || target/14==action.source/14 ||
            !snapshot_.actors[target] || !snapshot_.actors[target]->hp)
            throw std::invalid_argument("Invalid, duplicate, friendly or dead target");
        targeted[target]=true;
    }
    if(action.mp_cost>source.mp) throw InsufficientBattleMp(source.mp,action.mp_cost);
    auto staged=snapshot_;
    auto next_rng=rng_;
    BattleActionResult result{action.source,action.mp_cost,{}};
    result.hits.reserve(action.targets.size());
    for (const auto position : action.targets) {
        auto& target=*staged.actors[position];
        const auto roll=static_cast<std::uint32_t>(next_rng()%10000u);
        const CombatRuleInput input{
            action.magical?source.magical_attack:source.physical_attack,
            action.magical?target.magical_defense:target.physical_defense,
            action.power_percent,action.defense_percent,action.mp_cost,source.mp,
            action.critical_chance_bp,action.critical_multiplier_percent,roll,snapshot_.numeric_profile};
        const auto damage=rule(input);
        if (!damage.damage || !ExtendedHealthAmount::from(damage.damage) ||
            (snapshot_.numeric_profile==BattleNumericProfile::LegacyCustom && damage.damage>1'000'000) ||
            damage.mp_cost!=action.mp_cost)
            throw std::invalid_argument("Battle rule returned invalid damage or cost");
        const auto loss=std::min(target.hp,damage.damage);
        if(staged.numeric_profile==BattleNumericProfile::LegacyCustom) {
            target.hp=RecoveredBattleDelta::apply(static_cast<std::uint32_t>(target.hp),
                0u-static_cast<std::uint32_t>(damage.damage),static_cast<std::uint32_t>(target.max_hp));
        } else {
            const auto health=ExtendedHealthAmount::apply(target.hp,target.max_hp,
                {-static_cast<std::int64_t>(damage.damage)});
            if(!health)throw std::invalid_argument("Invalid extended damage health");
            target.hp=health->value();
        }
        result.hits.push_back({position,damage.damage,loss,damage.critical});
    }
    staged.actors[action.source]->mp=RecoveredBattleDelta::apply(
        staged.actors[action.source]->mp,0u-action.mp_cost,staged.actors[action.source]->max_mp);
    ++staged.revision;
    std::array<bool,2> living{};
    for (const auto& actor : staged.actors)
        if (actor && actor->hp) living[actor->position/14]=true;
    if (!living[0] || !living[1]) {
        staged.state=BattleState::Finished;
        // The validated living source cannot target its own side in this core.
        staged.victorious_side=static_cast<std::uint8_t>(living[0] ? 0 : 1);
    }
    auto wire=encode(staged,result);
    if (wire.empty()) throw std::invalid_argument("Battle encoder returned no response");
    // Every allocating or fallible operation is above this commit point.
    static_assert(std::is_nothrow_copy_assignable_v<BattleSnapshot>);
    static_assert(std::is_nothrow_copy_assignable_v<std::mt19937>);
    snapshot_=staged;
    rng_=next_rng;
    return wire;
}
std::vector<std::uint8_t> Battle::apply_native_deltas(std::uint64_t controller,std::uint64_t revision,
        std::span<const RecoveredBattleDelta::Record> records,const NativeDeltaEncode& encode) {
    if(snapshot_.numeric_profile!=BattleNumericProfile::LegacyCustom ||
       !controller || !active() || revision!=snapshot_.revision ||
       revision==std::numeric_limits<std::uint64_t>::max() || records.empty() || records.size()>64 || !encode)
        throw std::invalid_argument("Invalid native result exchange");
    auto staged=snapshot_;
    // Validate the complete exchange against the pre-exchange ownership snapshot.
    for(const auto& record:records) {
        if(record.targetOutcome()!=0 && record.targetOutcome()!=28)
            throw std::invalid_argument("Native result target outcome is unqualified");
        const auto& source=snapshot_.actors[record.source()];
        if(!source || source->controller!=controller || !source->hp)
            throw std::invalid_argument("Native result source is not owned and living");
        for(unsigned side=0;side<2;++side) for(unsigned slot=0;slot<14;++slot)
            if(record.targetMask(side)&(1u<<slot))
                if(!snapshot_.actors[side*14+slot])throw std::invalid_argument("Native result target absent");
    }
    for(const auto& record:records) {
        const auto delta=record.accumulate({});
        for(unsigned side=0;side<2;++side) for(unsigned slot=0;slot<14;++slot) {
            if(!(record.targetMask(side)&(1u<<slot)))continue;
            auto& target=*staged.actors[side*14+slot];
            target.hp=RecoveredBattleDelta::apply(static_cast<std::uint32_t>(target.hp),delta.hp,
                static_cast<std::uint32_t>(target.max_hp));
            target.mp=RecoveredBattleDelta::apply(target.mp,delta.mp,target.max_mp);
            if((target.hp>0)!=(record.targetOutcome()==28))
                throw std::invalid_argument("Native result HP and target outcome disagree");
        }
    }
    std::array<bool,2> living{};
    for(const auto& actor:staged.actors)if(actor && actor->hp)living[actor->position/14]=true;
    // No native simultaneous-elimination outcome rule has been recovered.
    if(!living[0] && !living[1])throw std::invalid_argument("Native simultaneous outcome is unqualified");
    if(!living[0] || !living[1]) {
        staged.state=BattleState::Finished;staged.victorious_side=static_cast<std::uint8_t>(living[0]?0:1);
    }
    ++staged.revision;
    auto wire=encode(staged,records);
    if(wire.empty())throw std::invalid_argument("Native result encoder returned no response");
    snapshot_=staged;
    return wire;
}
}
