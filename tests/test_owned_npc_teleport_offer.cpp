#include "handlers/OwnedNpcTeleportOffer.h"
#include <functional>
#include <iostream>
#include <source_location>
#include <stdexcept>
#include <utility>

// CUSTOM-0156 policy tests use an explicitly synthetic private host authority.
// No NPC placement, event rule, DB payment, route destination or native-client
// gameplay qualification follows from these in-memory lifecycle fixtures.
namespace {
using Service=god2::OwnedNpcTeleportOffer;
using Reason=Service::Reason;
using Record=god2::RecoveredWorldRecords::Record;
const Service::Identity identity{7,11,13};
const Service::Time instant{std::chrono::seconds(100)};
void require(bool good,const std::source_location where=std::source_location::current()) {
    if(!good)throw std::runtime_error("NPC offer invariant at line "+std::to_string(where.line()));
}
class FixtureAuthority final:public Service::Authority {
public:
    Service::Observation state;
    bool available=true,throwing=false,projection_available=true,malformed_projection=false;
    mutable std::function<void()> callback;
    std::optional<Service::Observation> observe(const Service::Identity&,const Service::Definition&) const override {
        if(callback)callback();
        if(throwing)throw std::runtime_error("Synthetic observation failure");
        if(!available)return std::nullopt;
        return state;
    }
    std::optional<Service::MenuProjection> project_dialogue(const Service::Definition&,
        const Service::DialogueMenu& menu,const Service::Observation&) const override {
        if(!projection_available)return std::nullopt;
        // Explicit synthetic complete packet fixture, never a product encoder
        // or a claim about the actual source text's formatting parameters.
        Service::MenuProjection result{{},"SYNTHETIC_FULL_MENU_FIXTURE"};
        result.logical.resize(menu.mode==4?28:27);
        result.logical[0]=0x7a;result.logical[1]=static_cast<std::uint8_t>(result.logical.size());
        result.logical[3]=menu.mode;result.logical[4]=menu.context;
        const auto word=[&](std::size_t at,std::uint16_t value) {
            result.logical[at]=static_cast<std::uint8_t>(value);
            result.logical[at+1]=static_cast<std::uint8_t>(value>>8);
        };
        word(5,menu.request);word(7,menu.text_key);word(9,menu.reply_control);
        if(malformed_projection)result.logical[7]^=1;
        return result;
    }
};
Service::Definition definition() {
    Service::Definition d;
    d.id="synthetic-npc-policy";d.revision=4;d.policy_revision=9;d.enabled=true;
    d.source={301,3058,2,4,60,75,0,0};
    d.menu=Service::DialogueMenu{4,1626,0x1234,0,0x4a,2};
    d.choices={{0,"synthetic-route-a"},{1,"synthetic-route-b"}};
    d.lifetime=std::chrono::seconds(20);d.interaction_range=3;
    d.source_evidence="SYNTHETIC_TEST_ONLY_NOT_AN_ACTUAL_NPC_PLACEMENT";
    d.condition_evidence="SYNTHETIC_TEST_REQUIREMENT";d.cost_evidence="SYNTHETIC_TEST_RESOURCE_COST";
    d.cost_policy=Service::CostPolicy::QualifiedResources;
    return d;
}
Service::Definition city(bool special=false) {
    auto d=definition();d.id=special?"synthetic-special-city":"synthetic-city";
    god2::RecoveredTeleport::Menu menu{};
    menu.context=special?0x61e:0x1234;menu.message_id=280;menu.count_flags=0x82;
    menu.level=10;menu.destinations[0]={5,0,500};menu.destinations[1]={1,0,1000};
    d.menu=menu;d.choices={{5,"synthetic-route-a"},{1,"synthetic-route-b"}};
    return d;
}
Service::Observation observation(const Service::Definition& d) {
    Service::Observation o;
    o.owner=identity;o.ready=true;o.position=god2::RecoveredPosition{2,4,59,75,23};
    o.world_generation=8;o.actor_identity=0;o.close_source_low_word=0xbeef;o.npc=d.source;o.npc.generation=14;
    o.policy={d.policy_revision,33,true,true};return o;
}
struct Fixture {
    Service::Definition d=definition();
    std::shared_ptr<FixtureAuthority> host=std::make_shared<FixtureAuthority>();
    Service service{host};
    explicit Fixture(Service::Definition value=definition()):d(std::move(value)) {
        host->state=observation(d);require(service.install({d})==Reason::Ok);
    }
    Service::Issued open(Service::Time now=instant) {
        const auto opened=service.open(identity,{d.source.instance},now);require(bool(opened));return *opened.value;
    }
};
god2::RecoveredQuestAction::Request reply(const Service::Issued& issued,std::uint16_t choice=0) {
    const auto& m=std::get<Service::DialogueMenu>(issued.menu);
    return {m.request,choice,m.context,0xa5};
}
god2::RecoveredTeleport::Selection selection(const Service::Issued& issued,std::uint8_t destination=5) {
    const auto& m=std::get<god2::RecoveredTeleport::Menu>(issued.menu);
    return {std::uint8_t(god2::RecoveredTeleport::special_context(m.context)?0xa9:0x99),m.context,destination,0xff};
}
void missing_definitions_and_authority() {
    Service empty;
    const std::vector<Record> records{god2::RecoveredNpcInteraction::Request{301},
        god2::RecoveredQuestAction::Request{0,0,0,0},god2::RecoveredTeleport::Selection{0x99,0,5,0}};
    require(!empty.claims(identity.session,records,instant));
    require(!empty.claims(identity,records,instant));
    require(empty.open(identity,{301},instant).reason==Reason::NoDefinition);
    require(empty.select_dialogue(identity,{0,0,0,0},instant).reason==Reason::NoOffer);
    auto d=definition();require(empty.install({d})==Reason::Ok);
    require(empty.open(identity,{301},instant).reason==Reason::AuthorityUnavailable);
    require(!empty.claims(identity,records,instant));
    auto host=std::make_shared<FixtureAuthority>();host->state=observation(d);Service service(host);
    d.enabled=false;d.cost_evidence.clear();d.choices.clear();require(service.install({d})==Reason::Ok);
    require(service.open(identity,{301},instant).reason==Reason::DisabledDefinition);
    require(!service.claims(identity,records,instant));
    d.enabled=true;require(service.install({d})==Reason::IncompleteDefinition);
    require(service.open(identity,{301},instant).reason==Reason::DisabledDefinition);
    auto complete=definition();require(service.install({complete})==Reason::Ok);
    host->projection_available=false;
    require(service.open(identity,{301},instant).reason==Reason::MenuProjectionUnavailable);
    require(!service.has_offer(identity.session));
    host->projection_available=true;host->malformed_projection=true;
    require(service.open(identity,{301},instant).reason==Reason::MenuProjectionUnavailable);
    require(!service.has_offer(identity.session));
}
void dialogue_preparation_and_replay() {
    Fixture f;const std::vector<Record> npc{god2::RecoveredNpcInteraction::Request{301}};
    require(!f.service.claims(identity.session,npc,instant)); // Raw37 alone is not proof.
    require(f.service.claims(identity,npc,instant));
    const auto issued=f.open();auto request=reply(issued);
    require(issued.logical_menu.size()==28 && issued.logical_menu[0]==0x7a);
    require(f.service.claims(identity.session,std::vector<Record>{request},instant));
    auto unrelated=request;++unrelated.request_word;
    require(!f.service.claims(identity.session,std::vector<Record>{unrelated},instant));
    require(f.service.select_dialogue(identity,unrelated,instant).reason==Reason::WrongContext);
    auto impossible=request;impossible.reply_word=7;
    require(f.service.select_dialogue(identity,impossible,instant).reason==Reason::ChoiceNotOffered);
    require(f.service.select_city(identity,{0x99,0,5,0},instant).reason==Reason::WrongMenu);
    require(!f.service.committed(identity.session,issued.token));
    auto foreign=identity;++foreign.account;
    require(f.service.select_dialogue(foreign,request,instant).reason==Reason::WrongOwner);
    require(f.service.has_offer(identity.session));
    const auto prepared=f.service.select_dialogue(identity,request,instant);require(bool(prepared));
    require(prepared.value->route_id=="synthetic-route-a");
    require(prepared.value->expected_position==*f.host->state.position);
    require(prepared.value->issuer==f.host->state.npc);
    require(prepared.value->definition_revision==4 && prepared.value->policy_revision==9);
    require(prepared.value->policy_readset_revision==33);
    require(prepared.value->cost_policy==Service::CostPolicy::QualifiedResources);
    require(f.service.select_dialogue(identity,request,instant).reason==Reason::AlreadyPrepared);
    require(f.service.revalidate(identity,*prepared.value,instant).value==Service::CostPolicy::QualifiedResources);
    auto altered=*prepared.value;altered.route_id="synthetic-route-b";
    require(f.service.revalidate(identity,altered,instant).reason==Reason::WrongContext);
    altered=*prepared.value;altered.cost_policy=Service::CostPolicy::ExplicitNoCost;
    require(f.service.revalidate(identity,altered,instant).reason==Reason::WrongContext);
    altered=*prepared.value;++altered.issuer.instance;
    require(f.service.revalidate(identity,altered,instant).reason==Reason::WrongContext);
    require(f.service.revalidate(identity,*prepared.value,instant).value==Service::CostPolicy::QualifiedResources);
    // No payment is performed by this service. The host still needs a joint
    // resource/position transaction; merely preparing must not mean free travel.
    require(f.host->state.policy.readset_revision==33 && f.host->state.position->revision==23);
    require(f.service.committed(identity.session,prepared.value->token));
    require(!f.service.committed(identity.session,prepared.value->token));
    require(f.service.select_dialogue(identity,request,instant).reason==Reason::NoOffer);
    const auto next=f.open();require(reply(next).request_word!=request.request_word);
    require(f.service.select_dialogue(identity,request,instant).reason==Reason::WrongContext);
    require(!f.service.committed(identity.session,prepared.value->token));
    require(bool(f.service.select_dialogue(identity,reply(next,1),instant)));
}
void city_and_cancel() {
    Fixture f(city());const auto issued=f.open();auto request=selection(issued);
    require(issued.logical_menu.size()==29 && issued.logical_menu[0]==0x6d);
    require(f.service.claims(identity.session,std::vector<Record>{request},instant));
    require(f.service.select_dialogue(identity,{0,0,0,0},instant).reason==Reason::WrongMenu);
    auto wrong=request;wrong.opcode=0xa9;
    require(!f.service.claims(identity.session,std::vector<Record>{wrong},instant));
    require(f.service.select_city(identity,wrong,instant).reason==Reason::WrongContext);
    wrong=request;wrong.destination=2;
    require(f.service.select_city(identity,wrong,instant).reason==Reason::ChoiceNotOffered);
    require(f.service.cancel(identity,{1,0xaaaa},instant)==Reason::WrongContext);
    require(!f.service.claims(identity.session,std::vector<Record>{god2::RecoveredQuestClose::Request{1,0xaaaa}},instant));
    require(f.service.has_offer(identity.session));
    // This independently qualified raw close source is neither own actor0 nor
    // character DB identity13. The native upperWORD remains opaque.
    require(f.service.claims(identity.session,std::vector<Record>{god2::RecoveredQuestClose::Request{0xbeef,0xffff}},instant));
    require(f.service.cancel(identity,{0xbeef,0xffff},instant)==Reason::Cancelled);
    require(!f.service.has_offer(identity.session));
    const auto next=f.open();require(selection(next).context!=request.context);
    require(f.service.select_city(identity,request,instant).reason==Reason::WrongContext);
    const auto prepared=f.service.select_city(identity,selection(next),instant);require(bool(prepared));
    require(prepared.value->route_id=="synthetic-route-a");
    f.service.forget(identity.session);
    require(f.service.revalidate(identity,*prepared.value,instant).reason==Reason::NoOffer);
    Fixture special(city(true));const auto special_issued=special.open();
    require(selection(special_issued).opcode==0xa9);
    const auto special_plan=special.service.select_city(identity,selection(special_issued),instant);require(bool(special_plan));
    require(special.service.committed(identity.session,special_plan.value->token));
    require(special.service.select_city(identity,selection(special_issued),instant).reason==Reason::NoOffer);
    const auto reopened=special.open();require(reopened.token!=special_issued.token);
    require(selection(reopened).context==selection(special_issued).context);
    const auto reopened_plan=special.service.select_city(identity,selection(reopened),instant);require(bool(reopened_plan));
    require(special.service.revalidate(identity,*special_plan.value,instant).reason==Reason::WrongContext);
    require(bool(special.service.revalidate(identity,*reopened_plan.value,instant)));
    require(!special.service.committed(identity.session,special_plan.value->token));
    require(special.service.committed(identity.session,reopened_plan.value->token));
    // A9 has no wire nonce: once a new legitimate offer is issued, an identical
    // old payload is indistinguishable from a new click of the same offered row.
    const auto third=special.open();require(third.token!=reopened.token);
    require(bool(special.service.select_city(identity,selection(special_issued),instant)));
    Fixture unknown_close(city());unknown_close.host->state.close_source_low_word.reset();unknown_close.open();
    require(!unknown_close.service.claims(identity.session,std::vector<Record>{god2::RecoveredQuestClose::Request{0,0}},instant));
    require(unknown_close.service.cancel(identity,{0,0},instant)==Reason::AuthorityUnavailable);
    Fixture zero_close(city());zero_close.host->state.close_source_low_word=0;zero_close.open();
    require(zero_close.service.claims(identity.session,std::vector<Record>{god2::RecoveredQuestClose::Request{0,0xffff}},instant));
    require(zero_close.service.cancel(identity,{0,0xffff},instant)==Reason::Cancelled);
}
void correlation_rollover_keeps_normal_use() {
    Fixture dialogue;Fixture normal_city(city());
    const auto first_dialogue=dialogue.open();
    const auto first_dialogue_plan=dialogue.service.select_dialogue(identity,reply(first_dialogue),instant);
    require(bool(first_dialogue_plan));require(dialogue.service.committed(identity.session,first_dialogue_plan.value->token));
    const auto first_city=normal_city.open();
    const auto first_city_plan=normal_city.service.select_city(identity,selection(first_city),instant);
    require(bool(first_city_plan));require(normal_city.service.committed(identity.session,first_city_plan.value->token));
    bool saw_dialogue_wrap=false,saw_city_wrap=false;
    auto last_dialogue=reply(first_dialogue).request_word;
    auto last_city=selection(first_city).context;
    // More than the entire native WORD space; these are policy fixtures only,
    // with no actual movement/payment or original NPC availability claim.
    for(std::uint32_t i=0;i<65540u;++i) {
        const auto issued=dialogue.open();const auto wire=reply(issued);
        if(wire.request_word<last_dialogue)saw_dialogue_wrap=true;
        last_dialogue=wire.request_word;
        const auto plan=dialogue.service.select_dialogue(identity,wire,instant);require(bool(plan));
        require(issued.token!=first_dialogue.token);
        require(dialogue.service.revalidate(identity,*first_dialogue_plan.value,instant).reason==Reason::WrongContext);
        require(dialogue.service.committed(identity.session,plan.value->token));
        const auto city_issued=normal_city.open();const auto city_wire=selection(city_issued);
        require(city_wire.opcode==0x99 && city_wire.context!=16055u && !god2::RecoveredTeleport::special_context(city_wire.context));
        if(city_wire.context<last_city)saw_city_wrap=true;
        last_city=city_wire.context;
        const auto city_plan=normal_city.service.select_city(identity,city_wire,instant);require(bool(city_plan));
        require(city_issued.token!=first_city.token);
        require(normal_city.service.revalidate(identity,*first_city_plan.value,instant).reason==Reason::WrongContext);
        require(normal_city.service.committed(identity.session,city_plan.value->token));
    }
    require(saw_dialogue_wrap && saw_city_wrap);
}
void state_invalidation() {
    const std::vector<std::pair<std::function<void(Service::Observation&)>,Reason>> cases{
        {[](auto& s){s.ready=false;},Reason::NotReady},
        {[](auto& s){s.in_battle=true;},Reason::InBattle},
        {[](auto& s){s.transfer_pending=true;},Reason::TransferPending},
        {[](auto& s){++s.position->x;},Reason::PositionChanged},
        {[](auto& s){++s.position->revision;},Reason::PositionChanged},
        {[](auto& s){++s.world_generation;},Reason::WorldChanged},
        {[](auto& s){s.actor_identity=1;},Reason::WorldChanged},
        {[](auto& s){s.close_source_low_word=1;},Reason::WorldChanged},
        {[](auto& s){++s.npc.generation;},Reason::NpcChanged},
        {[](auto& s){++s.npc.catalog_key;},Reason::WrongNpc},
        {[](auto& s){++s.policy.readset_revision;},Reason::PolicyChanged},
        {[](auto& s){s.policy.conditions_satisfied=false;},Reason::PolicyDenied},
        {[](auto& s){s.policy.costs_satisfied=false;},Reason::PolicyDenied}
    };
    for(const auto& [change,expected]:cases) {
        Fixture f;const auto issued=f.open();change(f.host->state);
        require(f.service.observe(identity,instant)==expected);
        require(!f.service.has_offer(identity.session));
        require(f.service.select_dialogue(identity,reply(issued),instant).reason==Reason::NoOffer);
        f.host->state=observation(f.d);const auto again=f.open();
        const auto plan=f.service.select_dialogue(identity,reply(again),instant);require(bool(plan));
        change(f.host->state);require(f.service.revalidate(identity,*plan.value,instant).reason==expected);
        require(!f.service.has_offer(identity.session));
    }
    Fixture expiry;const auto issued=expiry.open();
    require(!expiry.service.claims(identity.session,std::vector<Record>{reply(issued)},instant+std::chrono::seconds(20)));
    require(expiry.service.observe(identity,instant+std::chrono::seconds(20))==Reason::Expired);
    expiry.open();require(expiry.service.observe(identity,instant-std::chrono::seconds(1))==Reason::ClockRollback);
    require(expiry.service.open(identity,{301},Service::Time::max()).reason==Reason::ClockOverflow);
    Fixture unavailable;unavailable.open();unavailable.host->available=false;
    require(unavailable.service.observe(identity,instant)==Reason::AuthorityUnavailable);
    require(!unavailable.service.has_offer(identity.session));
    unavailable.host->available=true;unavailable.open();unavailable.host->throwing=true;
    require(unavailable.service.observe(identity,instant)==Reason::AuthorityUnavailable);
    require(!unavailable.service.has_offer(identity.session));
}
void snapshot_validation() {
    Fixture f;const auto issued=f.open();
    auto bad=f.d;bad.choices.push_back(bad.choices.front());
    require(f.service.install({bad})==Reason::InvalidDefinition);
    require(f.service.has_offer(identity.session));
    require(f.service.install({f.d,f.d})==Reason::DuplicateDefinition);
    auto duplicate=f.d;duplicate.id="duplicate-npc";
    require(f.service.install({f.d,duplicate})==Reason::DuplicateNpcBinding);
    bad=f.d;bad.cost_policy=Service::CostPolicy::Unqualified;
    require(f.service.install({bad})==Reason::IncompleteDefinition);
    bad=f.d;bad.condition_evidence.clear();
    require(f.service.install({bad})==Reason::IncompleteDefinition);
    bad=city();std::get<god2::RecoveredTeleport::Menu>(bad.menu).destinations[1].id=5;
    require(f.service.install({bad})==Reason::InvalidDefinition);
    auto without_high_flag=city();std::get<god2::RecoveredTeleport::Menu>(without_high_flag.menu).count_flags=2;
    require(Service::definition_status(without_high_flag)==Reason::Ok);
    require(f.service.install({f.d})==Reason::Ok);
    require(!f.service.has_offer(identity.session));
    require(f.service.select_dialogue(identity,reply(issued),instant).reason==Reason::NoOffer);
    // Replacing definitions does not reset wire correlations and admit replays.
    const auto replacement=f.open();require(reply(replacement).request_word!=reply(issued).request_word);
    f.host->callback=[&]{f.service.forget(identity.session);};
    require(f.service.observe(identity,instant)==Reason::Reentered);
    require(!f.service.has_offer(identity.session));
    f.host->callback={};
    f.d.cost_policy=Service::CostPolicy::ExplicitNoCost;
    f.d.cost_evidence="EXPLICIT_SYNTHETIC_NO_COST_NOT_DEFAULT";
    require(f.service.install({f.d})==Reason::Ok);const auto free=f.open();
    const auto prepared=f.service.select_dialogue(identity,reply(free),instant);require(bool(prepared));
    require(f.service.revalidate(identity,*prepared.value,instant).value==Service::CostPolicy::ExplicitNoCost);
}
}
int main() {
    try {
        missing_definitions_and_authority();dialogue_preparation_and_replay();
        city_and_cancel();correlation_rollover_keeps_normal_use();state_invalidation();snapshot_validation();
        std::cout<<"Owned NPC teleport policy fixtures passed; actual definitions/routes/native gameplay are not qualified.\n";
        return 0;
    } catch(const std::exception& error) {std::cerr<<error.what()<<'\n';return 1;}
}
