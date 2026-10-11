#include "handlers/RecoveredBattleService.h"
#include "protocol/RecoveredWorldFrame.h"
#include <stdexcept>
#include <bit>
#include <type_traits>
#include <limits>

namespace god2 {
namespace {
void validate_reply(std::span<const std::uint8_t> reply) {
    if (reply.empty()) throw std::invalid_argument("Missing battle reply");
    while (!reply.empty()) {
        if (reply.size()<2) throw std::invalid_argument("Truncated battle reply");
        const auto size=std::size_t{reply[0]}+(std::size_t{reply[1]}<<8);
        if (size>reply.size() || !RecoveredWorldFrame::decode(reply.first(size)))
            throw std::invalid_argument("Invalid battle reply envelope");
        reply=reply.subspan(size);
    }
}
}
RecoveredBattleService::RecoveredBattleService(Battle::Rule rule) : rule_(std::move(rule)) {
    if (!rule_) throw std::invalid_argument("Missing battle rule");
}
void RecoveredBattleService::bind(Session& session, Battle battle, Policy policy, Battle::Encode encode,Commit commit,CheckpointCommit checkpoint_commit) {
    const auto profile=battle.inspect().numeric_profile;
    if((policy.numeric_profile!=BattleNumericProfile::LegacyCustom &&
        policy.numeric_profile!=BattleNumericProfile::ExtendedHealth64) ||
       (profile!=BattleNumericProfile::LegacyCustom && profile!=BattleNumericProfile::ExtendedHealth64) ||
       policy.numeric_profile!=profile)
        throw std::invalid_argument("Unknown or mismatched trusted battle numeric profile");
    if (!session.account_id || !session.character_id || session.state()!=SessionState::InBattle ||
        bindings_.contains(session.id()) || !battle.active() || !encode || (commit && checkpoint_commit) ||
        policy.client_actor>14 || policy.client_side>1 || policy.actor_position>=28 ||
        !battle.inspect().actors[policy.actor_position] ||
        battle.inspect().actors[policy.actor_position]->controller!=session.character_id)
        throw std::invalid_argument("Invalid native battle binding");
    if(policy.diagnostic_manual_receipts && (!policy.diagnostic_single_action ||
       !policy.diagnostic_player_initial_control || policy.diagnostic_retaliation ||
       policy.diagnostic_revival || policy.diagnostic_timeout_action2 || commit || checkpoint_commit))
        throw std::invalid_argument("Manual trial receipt requires nonpersistent no-retaliation diagnostic");
    if(policy.diagnostic_mp_refusal && !policy.diagnostic_single_action)
        throw std::invalid_argument("MP refusal reply requires explicit diagnostic action policy");
    if(policy.diagnostic_initial_control_reply && (!policy.diagnostic_single_action ||
       !policy.diagnostic_player_initial_control || policy.diagnostic_revival))
        throw std::invalid_argument("Initial grant requires isolated non-revival receipt policy");
    if(policy.diagnostic_revival && (!policy.diagnostic_single_action || policy.diagnostic_retaliation ||
       !policy.diagnostic_revival->rule || !policy.diagnostic_revival->encode))
        throw std::invalid_argument("Revival requires isolated single-action policy and callbacks");
    if(policy.diagnostic_second_encounter_entry &&
       (!policy.diagnostic_player_initial_control || !policy.diagnostic_single_action ||
        policy.diagnostic_first_exchange_resume || policy.diagnostic_second_exchange_resume || battle.inspect().revision!=1))
        throw std::invalid_argument("Unqualified second encounter entry policy");
    if(policy.diagnostic_first_exchange_resume &&
       (!policy.diagnostic_three_round_friendly_receipts || !policy.diagnostic_single_action ||
        !policy.diagnostic_retaliation || battle.inspect().revision!=3 ||
        policy.diagnostic_control_targets!=std::array<std::uint16_t,2>{0,1}))
        throw std::invalid_argument("Unqualified diagnostic resume receipt policy");
    if(policy.diagnostic_second_exchange_resume &&
       (!policy.diagnostic_three_round_friendly_receipts || !policy.diagnostic_single_action ||
        !policy.diagnostic_player_initial_control || !policy.diagnostic_retaliation ||
        policy.diagnostic_first_exchange_resume || policy.diagnostic_revival || battle.inspect().revision!=5 ||
        policy.diagnostic_control_targets!=std::array<std::uint16_t,2>{0,1}))
        throw std::invalid_argument("Unqualified second exchange resume policy");
    if(policy.diagnostic_timeout_action2 &&
       (!policy.diagnostic_single_action || !policy.diagnostic_player_initial_control ||
        !policy.diagnostic_retaliation || policy.diagnostic_opening_action2 || policy.diagnostic_revival))
        throw std::invalid_argument("Unqualified diagnostic timeout action policy");
    // Each binding owns a mutable Battle, not a shared multiplayer battle reference.
    for(const auto& [id,bound]:bindings_) {
        (void)id;
        if(bound.character==session.character_id || bound.battle.inspect().id==battle.inspect().id)
            throw std::invalid_argument("Character or battle already bound to a live session");
    }
    if(policy.diagnostic_retaliation) {
        const auto& action=*policy.diagnostic_retaliation;
        if(!policy.diagnostic_single_action || action.source>=28 || !battle.inspect().actors[action.source] ||
           battle.inspect().actors[action.source]->controller!=0 || action.source/14==policy.actor_position/14 ||
           action.targets!=std::vector<std::uint8_t>{policy.actor_position})
            throw std::invalid_argument("Invalid diagnostic retaliation policy");
    }
    for(const auto& [key,limit]:policy.skill_target_limits)
        if(!policy.skills.contains(key) || !limit || limit>14)
            throw std::invalid_argument("Invalid authorized skill target limit");
    for(const auto& [key,encoder]:policy.skill_encoders)
        if(!policy.skills.contains(key) || !encoder)
            throw std::invalid_argument("Invalid authorized skill presentation encoder");
    for(const auto key:policy.skill_all_living_opponents)
        if(key!=skill_key(0,150) || !policy.skills.contains(key) ||
           !policy.skill_target_limits.contains(key) || policy.skill_target_limits.at(key)!=14)
            throw std::invalid_argument("Invalid all-living-opponents skill policy");
    const auto pose_session=session.weak_from_this();
    if(policy.pose_publication) {
        // CUSTOM-0103: full controller and actual S1C native WORD stay separate.
        // 515D10..23 -> variant2000 516149..15C copies that complete WORD to
        // actor+DB0. Do not derive it from position or narrow the controller.
        const auto& publication=*policy.pose_publication;
        const auto& roster=publication.actors();
        const auto& grant=publication.grant();
        // This actual historical primary write is initial publication metadata.
        // CUSTOM cosmetic authority is the exact active binding below; it is
        // not a claim of current client selector/model or turn eligibility.
        for(std::size_t slot=0;slot<roster.size();++slot) {
            if(bool(roster[slot])!=bool(battle.inspect().actors[slot]))
                throw std::invalid_argument("Battle pose publication has incomplete actual roster");
            // Only these actual diagnostic variants have a qualified metadata
            // low-WORD ->DB0 copy. Unknown constructors could shadow the owner
            // with a different identity; never infer their eventual IDs here.
            if(roster[slot] && roster[slot]->variant()!=0x2000 && roster[slot]->variant()!=0x0400)
                throw std::invalid_argument("Battle pose roster has unqualified native identity mapping");
        }
        const auto& owner=roster[policy.actor_position];
        if(pose_session.expired() || !owner || owner->variant()!=0x2000 || !owner->identity_word() ||
           policy.actor_position>=14 || !(grant[3]&0x01) || (grant[4]&0x0f)!=policy.actor_position)
            throw std::invalid_argument("Battle pose needs actual primary owner identity and grant");
        for(std::size_t slot=0;slot<roster.size();++slot)
            if(slot!=policy.actor_position && roster[slot] &&
               roster[slot]->identity_word()==owner->identity_word())
                throw std::invalid_argument("Battle pose native identity has ambiguous first match");
    }
    const auto pose_generation=session.battle_generation();
    bindings_.emplace(session.id(),Bound{&session,session.account_id,session.character_id,
                                      std::move(battle),std::move(policy),std::move(encode),std::move(commit),std::move(checkpoint_commit)});
    bindings_.at(session.id()).pose_battle_generation=pose_generation;
    bindings_.at(session.id()).pose_session=pose_session;
}
std::optional<std::vector<std::uint8_t>> RecoveredBattleService::handle(
        Session& session, std::span<const RecoveredWorldRecords::Record> records) {
    const auto found=bindings_.find(session.id());
    if (found==bindings_.end() || session.state()!=SessionState::InBattle ||
        records.empty() || records.size()>8192) return std::nullopt;
    auto& bound=found->second;
    if (bound.session!=&session || bound.account!=session.account_id ||
        bound.character!=session.character_id) return std::nullopt;
    if(records.size()==1) {
        if(const auto* pose=std::get_if<RecoveredWorldRecords::ClientPoseNotification>(&records.front())) {
            // CUSTOM-0103: standalone native battle symbol echo, never a combat
            // action or acknowledgement. Old-world initialization is irrelevant.
            const auto owner=bound.pose_session.lock();
            if(!bound.policy.pose_publication || owner.get()!=&session || session.closing() ||
               session.battle_generation()!=bound.pose_battle_generation || !bound.battle.active() ||
               !RecoveredBattlePose::qualified_request(pose->payload))return std::nullopt;
            const auto& actor=bound.battle.inspect().actors[bound.policy.actor_position];
            if(!actor || actor->controller!=bound.character)return std::nullopt;
            const auto now=std::chrono::steady_clock::now();
            // Server cosmetic quota uses its own monotonic clock. Native local
            // unsigned DWORD elapsed>500 is independent, not a server receipt.
            if(bound.pose_last_sent && now-*bound.pose_last_sent<=std::chrono::milliseconds(500))
                return std::vector<std::uint8_t>{};
            const auto& source=bound.policy.pose_publication->actors()[bound.policy.actor_position];
            const auto logical=RecoveredBattlePose::logical(source->identity_word(),pose->payload[0]);
            auto reply=RecoveredWorldFrame::encode(logical);
            validate_reply(reply); // allocation/encoding before cosmetic publication
            bound.pose_last_symbol=pose->payload[0];bound.pose_last_sent=now;
            return reply;
        }
    }
    // A terminal diagnostic action may precede its separately framed receipt.
    // Only that one control is admitted; finished battles cannot act again.
    if(!bound.battle.active() && (!bound.policy.diagnostic_single_action ||
       !bound.action_received || bound.control_received || records.size()!=1 ||
       !std::holds_alternative<RecoveredBattleCommand::ControlRequest>(records.front())))
        return std::nullopt;
    std::optional<BattleAction> action;
    std::optional<RecoveredSkillCommand::Record> first;
    bool pending=false;
    std::size_t skill_count=0;
    bool manual_selection_refused=false;
    bool control_received=false;
    bool initial_control_received=false;
    const auto authorized=[&](const auto& record) {
        return record.actor_position==bound.policy.client_actor &&
            record.side_flag==bound.policy.client_side && record.context_storage==bound.policy.context;
    };
    if(bound.policy.diagnostic_manual_receipts && records.size()==1) {
        if(const auto* timeout=std::get_if<RecoveredBattleCommand::Action2Request>(&records.front())) {
            std::array<std::uint16_t,2> self{};
            self[bound.policy.actor_position/14]=static_cast<std::uint16_t>(1u<<(bound.policy.actor_position%14));
            if(!bound.initial_control_received || bound.action_received || bound.control_received ||
               !bound.battle.active() || !authorized(timeout->fields) || timeout->fields.target_masks!=self)
                return std::nullopt;
            // Native518E50 never initializes logical4/13..16 for action2/0B.
            // Stack residue is not authority; retain actor/side/context/mask guards.
            // CUSTOM-0058: this no-retaliation recording fixture waits for the
            // player. Native command expiry must not disconnect the test game.
            // Reopen input without damage, defense arithmetic or state mutation.
            std::array<std::uint8_t,17> grant{};
            grant[0]=0x86;grant[1]=5;grant[3]=1;grant[4]=bound.policy.actor_position;
            auto reply=RecoveredWorldFrame::encode(grant);
            validate_reply(reply);
            return reply;
        }
    }
    if(bound.reconnect_notice==Bound::ReconnectNotice::Pending) {
        const auto* control=records.size()==1 ?
            std::get_if<RecoveredBattleCommand::ControlRequest>(&records.front()) : nullptr;
        if(!control || !authorized(control->fields) ||
           control->fields.target_masks!=std::array<std::uint16_t,2>{0,0} ||
           control->fields.unwritten_byte3 || control->fields.unwritten_parameter)
            return std::nullopt;
        // CUSTOM-0017: connection-local initialization, not a saved battle receipt.
        bound.reconnect_notice=Bound::ReconnectNotice::Consumed;
        return std::vector<std::uint8_t>{};
    }
    if(bound.reconnect_notice==Bound::ReconnectNotice::Consumed && records.size()==1) {
        const auto* opening=std::get_if<RecoveredBattleCommand::Action2Request>(&records.front());
        if(opening && authorized(opening->fields) &&
           opening->fields.target_masks==std::array<std::uint16_t,2>{1,0} &&
           !opening->fields.unwritten_byte3 && !opening->fields.unwritten_parameter) {
            bound.reconnect_notice=Bound::ReconnectNotice::OpeningConsumed;
            return std::vector<std::uint8_t>{};
        }
        return std::nullopt;
    }
    if(bound.policy.diagnostic_timeout_action2 && records.size()==1) {
        if(const auto* timeout=std::get_if<RecoveredBattleCommand::Action2Request>(&records.front())) {
            if(!bound.initial_control_received || bound.action_received || bound.control_received ||
               !bound.battle.active() || !authorized(timeout->fields) ||
               timeout->fields.target_masks!=std::array<std::uint16_t,2>{1,0} ||
               timeout->fields.unwritten_byte3 || timeout->fields.unwritten_parameter)
                return std::nullopt;
            // CUSTOM-0035: a no-input turn consumes this player's command and
            // lets the configured isolated enemy act. Native defense mitigation
            // is unknown; do not fabricate a zero-damage defense or victory.
            auto staged=bound.battle;
            const auto& retaliation=*bound.policy.diagnostic_retaliation;
            const auto reply=staged.act(0,staged.inspect().revision,retaliation,rule_,
                [&](const auto& state,const auto& result) {
                    auto wire=bound.encode(state,result);
                    validate_reply(wire);
                    return wire;
                });
            if(bound.commit) bound.commit(bound.battle.inspect(),staged.inspect());
            if(bound.checkpoint_commit)
                bound.checkpoint_commit(bound.battle.checkpoint(),staged.checkpoint());
            static_assert(std::is_nothrow_move_assignable_v<Battle>);
            bound.battle=std::move(staged);
            bound.action_received=true;
            bound.timeout_action2_received=true;
            return reply;
        }
    }
    if(bound.policy.diagnostic_opening_action2 && records.size()==1) {
        if(const auto* opening=std::get_if<RecoveredBattleCommand::Action2Request>(&records.front())) {
            if(!bound.initial_control_received || bound.opening_action2_received ||
               bound.action_received || bound.control_received || !bound.battle.active() ||
               !authorized(opening->fields) ||
               opening->fields.target_masks!=std::array<std::uint16_t,2>{1,0} ||
               opening->fields.unwritten_byte3 || opening->fields.unwritten_parameter)
                return std::nullopt;
            bound.opening_action2_received=true;
            return std::vector<std::uint8_t>{};
        }
    }
    if(records.size()==2 && bound.policy.diagnostic_revival && bound.policy.diagnostic_revival->opening_notice) {
        const auto* opening=std::get_if<RecoveredBattleCommand::Action2Request>(&records[0]);
        const auto* control=std::get_if<RecoveredBattleCommand::ControlRequest>(&records[1]);
        const auto exact=[&](const RecoveredBattleCommand::BasicAttackRequest& fields) {
            return authorized(fields) && fields.target_masks==std::array<std::uint16_t,2>{1,0} &&
                fields.unwritten_byte3==0 && fields.unwritten_parameter==0;
        };
        const auto& snapshot=bound.battle.inspect();
        if(!opening || !control || !exact(opening->fields) || !exact(control->fields) ||
           !bound.initial_control_received || bound.revival_opening_received || bound.action_received ||
           bound.control_received || bound.policy.actor_position!=0 || bound.policy.client_actor!=0 ||
           bound.policy.client_side!=0 || snapshot.revision!=2 || !snapshot.actors[1] || snapshot.actors[1]->hp)
            return std::nullopt;
        // CUSTOM-0017: candidate next-control response, not an animation ACK.
        std::array<std::uint8_t,17> grant{};grant[0]=0x86;grant[1]=5;grant[3]=1;
        auto reply=RecoveredWorldFrame::encode(grant);
        bound.revival_opening_received=true;
        return reply;
    }
    if(records.size()==1) {
        const auto* skill=std::get_if<RecoveredSkillCommand::Record>(&records.front());
        if(skill && skill->selection_kind_byte==3) {
            if(!bound.policy.diagnostic_revival || skill->selection_id_byte!=8 || skill->continuation ||
               !authorized(*skill) || bound.action_received || bound.control_received ||
               !bound.battle.active() || ((skill->target_masks[0]|skill->target_masks[1])&0xc000u) ||
               std::popcount(skill->target_masks[0])+std::popcount(skill->target_masks[1])!=1)
                return std::nullopt;
            const auto side=skill->target_masks[0] ? 0u : 1u;
            const auto target=static_cast<std::uint8_t>(side*14+std::countr_zero(skill->target_masks[side]));
            auto staged=bound.battle;
            auto reply=staged.revive(bound.character,staged.inspect().revision,bound.policy.actor_position,
                target,bound.policy.diagnostic_revival->rule,[&](const auto& state,const auto& result) {
                    auto wire=bound.policy.diagnostic_revival->encode(state,result);
                    validate_reply(wire);
                    return wire;
                });
            if(bound.commit) bound.commit(bound.battle.inspect(),staged.inspect());
            if(bound.checkpoint_commit) bound.checkpoint_commit(bound.battle.checkpoint(),staged.checkpoint());
            static_assert(std::is_nothrow_move_assignable_v<Battle>);
            bound.battle=std::move(staged);
            bound.action_received=true;
            return reply;
        }
    }
    const auto add_targets=[&](const auto& masks) {
        for (unsigned side=0;side<2;++side) {
            if (masks[side]&0xc000u) return false;
            for (unsigned slot=0;slot<14;++slot)
                if (masks[side]&(1u<<slot)) action->targets.push_back(static_cast<std::uint8_t>(side*14+slot));
        }
        return true;
    };
    for (const auto& record : records) {
        if (std::holds_alternative<RecoveredWorldRecords::Tick>(record)) {
            if (pending) return std::nullopt;
            continue;
        }
        if (const auto* basic=std::get_if<RecoveredBattleCommand::BasicAttackRequest>(&record)) {
            if (action || control_received || !authorized(*basic) ||
                (bound.policy.diagnostic_single_action && bound.action_received)) return std::nullopt;
            action=bound.policy.basic;action->targets.clear();
            if (!add_targets(basic->target_masks)) return std::nullopt;
            if(action->targets.size()!=1) {
                if(!bound.policy.diagnostic_manual_receipts) return std::nullopt;
                manual_selection_refused=true;
            }
        } else if (const auto* skill=std::get_if<RecoveredSkillCommand::Record>(&record)) {
            // Kinds0/1 require their own explicit trusted rule. Kind3's
            // separate revival/healing semantics must not enter attack rules.
            if (skill->selection_kind_byte > 1 || control_received || (bound.policy.diagnostic_single_action && bound.action_received) ||
                !authorized(*skill) || ++skill_count>14) return std::nullopt;
            if (!first) {
                if (action) return std::nullopt;
                const auto rule=bound.policy.skills.find(skill_key(skill->selection_kind_byte,skill->selection_id_byte));
                if (rule==bound.policy.skills.end()) return std::nullopt;
                action=rule->second;action->targets.clear();first=*skill;
            } else if (!pending || !RecoveredSkillCommand::same_sequence(*first,*skill)) return std::nullopt;
            const auto previous=action->targets.size();
            const auto key=skill_key(skill->selection_kind_byte,skill->selection_id_byte);
            if(bound.policy.skill_all_living_opponents.contains(key)) {
                // Native mode5 is one side-wide record, not a target sequence.
                // Never accept a subset/friendly side, or depend on empty/dead
                // slots that the native 0x3FFF marker necessarily includes.
                std::array<std::uint16_t,2> expected{};
                const unsigned enemy=1-bound.policy.actor_position/14;
                expected[enemy]=0x3fff;
                if(skill_count!=1 || skill->continuation || skill->target_masks!=expected) return std::nullopt;
                const auto& state=bound.battle.inspect();
                for(unsigned slot=enemy*14;slot<(enemy+1)*14;++slot)
                    if(state.actors[slot] && state.actors[slot]->hp)
                        action->targets.push_back(static_cast<std::uint8_t>(slot));
                if(action->targets.empty())return std::nullopt;
            } else if (!add_targets(skill->target_masks) || action->targets.size()!=previous+1) return std::nullopt;
            const auto limit=bound.policy.skill_target_limits.find(
                skill_key(skill->selection_kind_byte,skill->selection_id_byte));
            if(limit!=bound.policy.skill_target_limits.end() && action->targets.size()>limit->second) {
                if(!bound.policy.diagnostic_manual_receipts) return std::nullopt;
                manual_selection_refused=true;
            }
            pending=skill->continuation;
        } else if (const auto* control=std::get_if<RecoveredBattleCommand::ControlRequest>(&record)) {
            if(bound.policy.diagnostic_single_action && bound.policy.diagnostic_player_initial_control &&
               records.size()==1 && !action && !bound.action_received && !bound.control_received &&
               !bound.initial_control_received && authorized(control->fields) &&
               control->fields.target_masks==(bound.policy.diagnostic_second_encounter_entry ?
                   std::array<std::uint16_t,2>{1,0} : std::array<std::uint16_t,2>{0,0}) &&
               (bound.policy.diagnostic_manual_receipts ||
                (control->fields.unwritten_byte3==0 && control->fields.unwritten_parameter==0))) {
                initial_control_received=true;
                continue;
            }
            // CUSTOM-0010: diagnostic receipt only, never an inferred official turn advance.
            const auto expected_targets=bound.timeout_action2_received ?
                std::array<std::uint16_t,2>{1,0} :
                (bound.policy.diagnostic_three_round_friendly_receipts &&
                bound.policy.diagnostic_retaliation && ((bound.battle.inspect().revision==5 &&
                    !bound.policy.diagnostic_first_exchange_resume) ||
                    (bound.battle.inspect().revision==6 && bound.battle.inspect().state==BattleState::Finished &&
                     !bound.policy.diagnostic_second_exchange_resume)) &&
                bound.action_received && records.size()==1 && !action)
                ? std::array<std::uint16_t,2>{1,0} :
                (bound.reconnect_notice==Bound::ReconnectNotice::OpeningConsumed &&
                 bound.battle.inspect().revision==bound.reconnect_revision+1 && bound.action_received && records.size()==1 && !action)
                    ? std::array<std::uint16_t,2>{0,1} : bound.policy.diagnostic_control_targets;
            bool manual_targets=bound.policy.diagnostic_manual_receipts;
            if(manual_targets) for(unsigned side=0;side<2;++side) {
                const auto mask=control->fields.target_masks[side];
                if(mask&0xc000u) manual_targets=false;
                for(unsigned bit=0;bit<14;++bit)
                    if((mask&(1u<<bit)) && !bound.battle.inspect().actors[side*14+bit]) manual_targets=false;
            }
            if(!bound.policy.diagnostic_single_action || control_received || bound.control_received ||
               (!action && !bound.action_received) || !authorized(control->fields) ||
               (bound.policy.diagnostic_manual_receipts ? !manual_targets : control->fields.target_masks!=expected_targets)) return std::nullopt;
            control_received=true;
        } else return std::nullopt;
    }
    if (pending) return std::nullopt;
    // Durable revival qualification covers separate action and receipt frames.
    if(action && control_received && bound.phase_commit) return std::nullopt;
    if (!action) {
        std::vector<std::uint8_t> initial_reply;
        if(initial_control_received && bound.policy.diagnostic_initial_control_reply) {
            initial_reply=bound.policy.diagnostic_initial_control_reply();
            validate_reply(initial_reply);
        }
        if(control_received && bound.phase_commit && bound.battle.active()) {
            const auto previous=checkpoint_revival(session);
            auto next=previous;next.control_received=true;
            bound.phase_commit(previous,next);
        }
        if(initial_control_received) bound.initial_control_received=true;
        if(control_received) bound.control_received=true;
        return initial_reply;
    }
    action->source=bound.policy.actor_position;
    if(bound.policy.diagnostic_manual_receipts) {
        // CUSTOM-0058: the native UI permits selecting the same monster more
        // than once. Reject the COMPLETE authenticated selection, not the
        // connection. Never deduplicate into an unintended cheaper cast, and
        // never catch arbitrary rule/renderer exceptions as input mistakes.
        const auto& state=bound.battle.inspect();
        std::array<bool,28> seen{};
        for(const auto target:action->targets) {
            if(target>=state.actors.size() || seen[target] ||
               target/14==action->source/14 || !state.actors[target] || !state.actors[target]->hp)
                manual_selection_refused=true;
            else seen[target]=true;
        }
        if(action->targets.empty()) manual_selection_refused=true;
        if(manual_selection_refused) {
            // Same native86/5 re-grant shape as the existing MP refusal lane.
            // No 88 cycle advance, RNG, HP/MP, revision or action-latch change.
            std::array<std::uint8_t,17> grant{};
            grant[0]=0x86;grant[1]=5;grant[3]=1;grant[4]=bound.policy.actor_position;
            auto refused=RecoveredWorldFrame::encode(grant);
            validate_reply(refused);
            return refused;
        }
    }
    // No client revision field is invented. This is internal optimistic state;
    // native turn/ack admission and replay detection remain separate work.
    const auto encode=[&](const auto& state,const auto& result) {
            auto reply=bound.encode(state,result);
            validate_reply(reply); // Validation must occur before Battle commits.
            return reply;
        };
    // A skill encoder applies only to this cast, never the subsequent enemy
    // retaliation. The existing native reply validation/atomic commit remains.
    const auto encode_skill=[&](const auto& state,const auto& result) {
        if(first) {
            const auto found=bound.policy.skill_encoders.find(
                skill_key(first->selection_kind_byte,first->selection_id_byte));
            if(found!=bound.policy.skill_encoders.end()) {
                auto wire=found->second(state,result);
                validate_reply(wire);
                return wire;
            }
        }
        return encode(state,result);
    };
    auto staged=bound.battle;
    std::vector<std::uint8_t> reply;
    try {
        reply=staged.act(bound.character,staged.inspect().revision,*action,rule_,encode_skill);
    } catch(const InsufficientBattleMp& refusal) {
        const auto& source=*bound.battle.inspect().actors[action->source];
        if(!bound.policy.diagnostic_mp_refusal || control_received || initial_control_received ||
           !first || records.size()!=1 || action->targets.size()!=1 ||
           source.mp>=action->mp_cost || refusal.available!=source.mp || refusal.required!=action->mp_cost)
            throw;
        auto refused=bound.policy.diagnostic_mp_refusal(bound.battle.inspect(),*action,refusal);
        validate_reply(refused);
        return refused;
    }
    if(bound.policy.diagnostic_retaliation && staged.active()) {
        const auto& retaliation=*bound.policy.diagnostic_retaliation;
        if(staged.inspect().actors[retaliation.source]->hp) {
            const auto counter=staged.act(0,staged.inspect().revision,retaliation,rule_,encode);
            reply.insert(reply.end(),counter.begin(),counter.end());
        }
    }
    static_assert(std::is_nothrow_move_assignable_v<Battle>);
    if(bound.commit) bound.commit(bound.battle.inspect(),staged.inspect());
    if(bound.checkpoint_commit) {
        const auto before=bound.battle.checkpoint();
        const auto after=staged.checkpoint();
        bound.checkpoint_commit(before,after);
    }
    bound.battle=std::move(staged);
    bound.action_received=true;
    if(control_received) bound.control_received=true;
    return reply;
}
const BattleSnapshot& RecoveredBattleService::inspect(std::uint64_t session) const {
    return bindings_.at(session).battle.inspect();
}
std::vector<std::uint8_t> RecoveredBattleService::apply_native_deltas(Session& session,std::uint64_t revision,
        std::span<const RecoveredBattleDelta::Record> records,const Battle::NativeDeltaEncode& encode) {
    const auto found=bindings_.find(session.id());
    if(found==bindings_.end())throw std::invalid_argument("Native results require a bound battle");
    auto& bound=found->second;
    if(bound.session!=&session || bound.account!=session.account_id || bound.character!=session.character_id ||
       session.state()!=SessionState::InBattle || bound.action_received || records.empty())
        throw std::invalid_argument("Native result session or phase mismatch");
    for(const auto& record:records)if(record.source()!=bound.policy.actor_position)
        throw std::invalid_argument("Native result source differs from authorized actor");
    auto staged=bound.battle;
    const auto validated=[&](const BattleSnapshot& state,std::span<const RecoveredBattleDelta::Record> deltas) {
        if(!encode)throw std::invalid_argument("Missing native result encoder");
        auto wire=encode(state,deltas);validate_reply(wire);return wire;
    };
    auto reply=staged.apply_native_deltas(session.character_id,revision,records,validated);
    if(bound.commit)bound.commit(bound.battle.inspect(),staged.inspect());
    if(bound.checkpoint_commit)bound.checkpoint_commit(bound.battle.checkpoint(),staged.checkpoint());
    bound.battle=std::move(staged);bound.action_received=true;
    return reply;
}
void RecoveredBattleService::rearm_diagnostic(Session& session,std::uint64_t expected_revision) {
    const auto it=bindings_.find(session.id());
    if(it==bindings_.end()) throw std::invalid_argument("Missing diagnostic battle");
    auto& bound=it->second;
    if(bound.session!=&session || bound.account!=session.account_id || bound.character!=session.character_id ||
       session.state()!=SessionState::InBattle || !bound.policy.diagnostic_single_action ||
       !bound.battle.active() || bound.battle.inspect().revision!=expected_revision ||
       !bound.battle.inspect().actors[bound.policy.actor_position]->hp ||
       (bound.policy.diagnostic_retaliation && !bound.battle.inspect().actors[bound.policy.diagnostic_retaliation->source]->hp) ||
       !bound.action_received || !bound.control_received ||
       bound.reconnect_notice==Bound::ReconnectNotice::Pending ||
       bound.reconnect_notice==Bound::ReconnectNotice::Consumed)
        throw std::invalid_argument("Diagnostic rearm preconditions failed");
    if(bound.phase_commit) {
        const auto previous=checkpoint_revival(session);
        auto next=previous;next.action_received=false;next.control_received=false;
        bound.phase_commit(previous,next);
    }
    bound.action_received=false;
    bound.control_received=false;
    bound.timeout_action2_received=false;
}
bool RecoveredBattleService::diagnostic_round_ready(const Session& session) const noexcept {
    const auto it=bindings_.find(session.id());
    if(it==bindings_.end()) return false;
    const auto& b=it->second;
    return b.session==&session && b.account==session.account_id && b.character==session.character_id &&
        session.state()==SessionState::InBattle && b.policy.diagnostic_single_action && b.battle.active() &&
        b.action_received && b.control_received && b.reconnect_notice!=Bound::ReconnectNotice::Pending &&
        b.reconnect_notice!=Bound::ReconnectNotice::Consumed &&
        b.battle.inspect().actors[b.policy.actor_position]->hp &&
        (!b.policy.diagnostic_retaliation || b.battle.inspect().actors[b.policy.diagnostic_retaliation->source]->hp);
}
bool RecoveredBattleService::diagnostic_timeout_round_ready(const Session& session) const noexcept {
    const auto it=bindings_.find(session.id());
    return it!=bindings_.end() && it->second.timeout_action2_received &&
        diagnostic_round_ready(session);
}
void RecoveredBattleService::set_revival_phase_commit(Session& session,PhaseCommit commit) {
    (void)checkpoint_revival(session);
    auto& bound=bindings_.at(session.id());
    if(!commit || bound.phase_commit || !bound.checkpoint_commit)
        throw std::invalid_argument("Revival phase persistence requires one paired checkpoint callback");
    bound.phase_commit=std::move(commit);
}
void RecoveredBattleService::remove(std::uint64_t session) noexcept { bindings_.erase(session); }
RecoveredBattleService::RevivalRecovery RecoveredBattleService::checkpoint_revival(const Session& session) const {
    const auto it=bindings_.find(session.id());
    if(it==bindings_.end()) throw std::invalid_argument("Missing revival recovery binding");
    const auto& b=it->second;
    const auto& p=b.policy;
    if(b.session!=&session || b.account!=session.account_id || b.character!=session.character_id ||
       session.state()!=SessionState::InBattle || !b.battle.active() ||
       !p.diagnostic_single_action || !p.diagnostic_revival || p.diagnostic_retaliation ||
       p.client_actor || p.client_side || p.actor_position || p.context || !p.skills.empty() ||
       p.diagnostic_control_targets!=std::array<std::uint16_t,2>{1,0} ||
       p.diagnostic_mp_refusal || p.diagnostic_three_round_friendly_receipts ||
       p.diagnostic_first_exchange_resume || p.diagnostic_second_exchange_resume || p.diagnostic_second_encounter_entry)
        throw std::invalid_argument("Unqualified revival recovery policy");
    return {1,b.account,b.character,b.battle.checkpoint(),b.initial_control_received,
        b.revival_opening_received,b.action_received,b.control_received,p.diagnostic_revival->opening_notice};
}
void RecoveredBattleService::restore_revival_phase(Session& session,const RevivalRecovery& recovery) {
    const auto current=checkpoint_revival(session);
    if(recovery.version!=1 || recovery.account!=current.account || recovery.character!=current.character ||
       recovery.battle!=current.battle || recovery.opening_notice!=current.opening_notice ||
       current.initial_control_received || current.opening_received || current.action_received || current.control_received ||
       (recovery.control_received && !recovery.action_received) ||
       (recovery.opening_received && (!recovery.opening_notice || !recovery.initial_control_received)))
        throw std::invalid_argument("Revival recovery phase mismatch");
    auto& bound=bindings_.at(session.id());
    if(bound.revival_phase_restored)
        throw std::invalid_argument("Revival phase already restored");
    if(recovery.initial_control_received && !bound.policy.diagnostic_player_initial_control)
        throw std::invalid_argument("Revival recovery initial control policy mismatch");
    bound.initial_control_received=recovery.initial_control_received;
    bound.revival_opening_received=recovery.opening_received;
    bound.action_received=recovery.action_received;
    bound.control_received=recovery.control_received;
    bound.revival_phase_restored=true;
}
void RecoveredBattleService::expect_revival_reconnect_notice(Session& session) {
    const auto phase=checkpoint_revival(session);
    auto& bound=bindings_.at(session.id());
    if(!bound.revival_phase_restored || bound.reconnect_notice!=Bound::ReconnectNotice::None ||
       !bound.policy.diagnostic_player_initial_control || !phase.initial_control_received ||
       !phase.opening_received || !phase.action_received || !phase.control_received ||
       phase.battle.snapshot.revision>=std::numeric_limits<std::uint64_t>::max()-1)
        throw std::invalid_argument("Unqualified revival reconnect notice");
    bound.reconnect_notice=Bound::ReconnectNotice::Pending;
    bound.reconnect_revision=phase.battle.snapshot.revision;
}
bool RecoveredBattleService::release_finished_diagnostic(Session& session) {
    const auto it=bindings_.find(session.id());
    if(it==bindings_.end()) return false;
    const auto& b=it->second;
    if(b.session!=&session || b.account!=session.account_id || b.character!=session.character_id ||
       session.state()!=SessionState::InBattle || !b.policy.diagnostic_single_action ||
       !b.action_received || !b.control_received || b.battle.inspect().state!=BattleState::Finished) return false;
    // CUSTOM-0011: trusted committed diagnostic outcome, not a client ACK.
    session.set_state(SessionState::InWorld);
    bindings_.erase(it);
    return true;
}
}
