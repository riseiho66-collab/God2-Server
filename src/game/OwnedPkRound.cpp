#include "game/OwnedPkRound.h"
#include <nlohmann/json.hpp>
#include <limits>
#include <stdexcept>
namespace god2 {
namespace {
using Json=nlohmann::json;
constexpr auto max_revision=static_cast<std::uint64_t>(INT64_MAX);
template<class T>T number(const Json& j){
    if(!j.is_number_integer()||(!j.is_number_unsigned()&&j.get<std::int64_t>()<0))
        throw std::invalid_argument("PK round requires bounded nonnegative integers");
    const auto n=j.get<std::uint64_t>();if(n>std::numeric_limits<T>::max())throw std::invalid_argument("PK round integer overflow");
    return static_cast<T>(n);
}
bool boolean(const Json& j){if(!j.is_boolean())throw std::invalid_argument("PK round requires boolean flags");return j.get<bool>();}
Json action_json(const BattleAction& a){
    return Json::array({a.source,a.targets,a.magical,a.power_percent,a.defense_percent,a.mp_cost,a.critical_chance_bp,a.critical_multiplier_percent});
}
BattleAction action_read(const Json& j){
    if(!j.is_array()||j.size()!=8||!j[1].is_array()||j[1].size()!=1)throw std::invalid_argument("PK round action shape");
    return {number<std::uint8_t>(j[0]),{number<std::uint8_t>(j[1][0])},boolean(j[2]),
        number<std::uint32_t>(j[3]),number<std::uint32_t>(j[4]),number<std::uint32_t>(j[5]),
        number<std::uint32_t>(j[6]),number<std::uint32_t>(j[7])};
}
}
bool OwnedPkRound::masks_valid(const Masks& masks)noexcept{
    // Only the present slot0 of each side; empty native notification allowed.
    for(const auto& m:masks)if((m[0]&~1u)||(m[1]&~1u))return false;
    return true;
}
OwnedPkRound OwnedPkRound::waiting(std::array<Header,2> headers,Masks masks,std::uint64_t revision){
    OwnedPkRound result;result.headers_=headers;result.expected_masks_=masks;result.battle_revision_=revision;
    result.validate();return result;
}
OwnedPkRound OwnedPkRound::waiting_notification(std::array<Header,2> headers,Masks bounds,std::uint64_t revision){
    auto result=waiting(headers,bounds,revision);result.notification_bounds_=bounds;
    result.validate();return result;
}
void OwnedPkRound::bump(){if(revision_>=max_revision)throw std::overflow_error("PK round revision exhausted");++revision_;}
bool OwnedPkRound::control(std::uint8_t viewer,const RecoveredBattleCommand::ControlRequest& r){
    if(viewer>1||(phase_!=Phase::InitialControl&&phase_!=Phase::ResultsControl)||controls_[viewer])return false;
    const auto& h=headers_[viewer];const auto& f=r.fields;
    if(f.actor_position!=h.actor||f.side_flag!=h.side||f.context_storage!=h.context)return false;
    const bool notification=phase_==Phase::InitialControl&&notification_bounds_.has_value();
    if(notification){
        const auto& bounds=(*notification_bounds_)[viewer];
        for(std::size_t i=0;i<2;++i)if(f.target_masks[i]&~bounds[i])return false;
    }else if(f.target_masks!=expected_masks_[viewer])return false;
    auto next=*this;
    if(notification){
        next.notification_observations_[viewer]=f.target_masks;
        next.expected_masks_[viewer]=f.target_masks;
    }
    next.controls_[viewer]=true;next.bump();
    if(next.controls_[0]&&next.controls_[1]){
        if(next.phase_==Phase::ResultsControl){if(next.round_>=max_revision)throw std::overflow_error("PK round number exhausted");++next.round_;}
        next.phase_=Phase::Grants;next.grant_epoch_=next.revision_;next.grant_submissions_={false,false};next.intents_={};
    }
    next.validate();*this=std::move(next);return true;
}
bool OwnedPkRound::grant_submitted(std::uint64_t epoch,std::uint8_t viewer){
    if(viewer>1||phase_!=Phase::Grants||epoch!=grant_epoch_||grant_submissions_[viewer])return false;
    auto next=*this;next.grant_submissions_[viewer]=true;next.bump();
    if(next.grant_submissions_[0]&&next.grant_submissions_[1])
        next.phase_=next.intents_[0]&&next.intents_[1]?Phase::Ready:Phase::Collect;
    next.validate();*this=std::move(next);return true;
}
bool OwnedPkRound::submit(std::uint8_t viewer,Intent intent){
    // One peer can reply quickly while the other queue callback is pending;
    // store its selection, but Ready requires BOTH grant submissions/inputs.
    if(viewer>1||(phase_!=Phase::Collect&&phase_!=Phase::Grants)||!grant_submissions_[viewer]||intents_[viewer])return false;
    auto next=*this;next.intents_[viewer]=std::move(intent);next.bump();
    if(next.grant_submissions_[0]&&next.grant_submissions_[1]&&next.intents_[0]&&next.intents_[1])next.phase_=Phase::Ready;
    next.validate();*this=std::move(next);return true;
}
bool OwnedPkRound::results_issued(std::uint64_t next_revision,Masks masks,bool terminal){
    if(phase_!=Phase::Ready||next_revision<=battle_revision_||next_revision-battle_revision_>2||!masks_valid(masks))return false;
    auto next=*this;next.battle_revision_=next_revision;next.expected_masks_=masks;next.controls_={false,false};
    next.phase_=terminal?Phase::Terminal:Phase::ResultsControl;next.bump();next.validate();*this=std::move(next);return true;
}
void OwnedPkRound::validate()const{
    if(!revision_||revision_>max_revision||!battle_revision_||battle_revision_>max_revision||!round_||round_>max_revision||
       grant_epoch_>revision_||!masks_valid(expected_masks_))throw std::invalid_argument("PK round header bounds");
    for(const auto& h:headers_)if(h.actor!=0||h.side!=0)throw std::invalid_argument("PK primary owned slot0 header required");
    if(notification_bounds_){
        if(phase_==Phase::InitialControl&&round_!=1)
            throw std::invalid_argument("PK initial notification cannot recur in a later round");
        // This profile is exactly two ordinary players: relative slots0/14.
        for(const auto& b:*notification_bounds_)if(b!=std::array<std::uint16_t,2>{1,1})
            throw std::invalid_argument("PK notification bounds require the complete two-player roster");
        for(std::size_t i=0;i<2;++i){
            const auto& observed=notification_observations_[i];
            if(observed)for(std::size_t side=0;side<2;++side)
                if((*observed)[side]&~(*notification_bounds_)[i][side])
                    throw std::invalid_argument("PK initial notification outside retained roster");
            if(phase_==Phase::InitialControl){
                if(controls_[i]!=observed.has_value()||
                   expected_masks_[i]!=(observed?*observed:(*notification_bounds_)[i]))
                    throw std::invalid_argument("PK initial notification observation mismatch");
            }else{
                if(!observed)throw std::invalid_argument("PK post-initial phase lacks first notification");
                if(round_==1&&(phase_==Phase::Grants||phase_==Phase::Collect||phase_==Phase::Ready)&&
                   expected_masks_[i]!=*observed)
                    throw std::invalid_argument("PK first-round mask changed before results");
            }
        }
    }else for(const auto& observed:notification_observations_)if(observed)
        throw std::invalid_argument("PK legacy round cannot contain notification observations");
    for(std::size_t i=0;i<2;++i)if(intents_[i]){
        const auto& v=*intents_[i];const auto& a=v.action;
        if(a.source!=14*i||a.targets.size()!=1||a.targets[0]!=14*(1-i)||a.power_percent>10000||a.defense_percent>100||
           a.mp_cost>1000000||a.critical_chance_bp>10000||a.critical_multiplier_percent<100||a.critical_multiplier_percent>1000||
           (v.skill_key?(!(*v.skill_key&0xff)||(*v.skill_key>>8)>1||v.definition_readset.empty()||v.definition_readset.size()>8192)
                       :!v.definition_readset.empty()))throw std::invalid_argument("PK round canonical attack policy bounds");
        if(!grant_submissions_[i])throw std::invalid_argument("PK round command before viewer grant submission");
    }
    if((phase_==Phase::Collect||phase_==Phase::Ready)&&(!grant_submissions_[0]||!grant_submissions_[1]))
        throw std::invalid_argument("PK collect requires both queue submissions");
    if((phase_==Phase::Ready||phase_==Phase::ResultsControl||phase_==Phase::Terminal)&&(!intents_[0]||!intents_[1]))
        throw std::invalid_argument("PK resolved phase requires both canonical intents");
    if((phase_==Phase::InitialControl&&controls_[0]&&controls_[1])||
       (phase_==Phase::Grants&&grant_submissions_[0]&&grant_submissions_[1])||
       (phase_==Phase::Collect&&intents_[0]&&intents_[1])||
       ((phase_==Phase::ResultsControl||phase_==Phase::Terminal)&&
        (!grant_submissions_[0]||!grant_submissions_[1]||(controls_[0]&&controls_[1])))||
       (phase_==Phase::Terminal&&(controls_[0]||controls_[1])))
        throw std::invalid_argument("PK round phase/flag combination is not reachable");
    if(phase_==Phase::InitialControl&&(grant_epoch_||grant_submissions_[0]||grant_submissions_[1]||intents_[0]||intents_[1]))
        throw std::invalid_argument("PK initial phase cannot already have grants/actions");
    if(phase_!=Phase::InitialControl&&(!grant_epoch_||
       ((phase_==Phase::Grants||phase_==Phase::Collect||phase_==Phase::Ready)&&(!controls_[0]||!controls_[1]))))
        throw std::invalid_argument("PK grant phase lacks both preceding notifications");
}
std::string OwnedPkRound::document()const{
    validate();Json actions=Json::array();
    for(const auto& intent:intents_)
        actions.push_back(intent?Json::array({action_json(intent->action),intent->skill_key?Json(*intent->skill_key):Json(nullptr),intent->definition_readset}):Json(nullptr));
    Json headers=Json::array();for(const auto& h:headers_)headers.push_back(Json::array({h.actor,h.side,h.context}));
    auto result=Json{{"version",1},{"design_id","CUSTOM-0086"},{"phase",static_cast<unsigned>(phase_)},
        {"revision",revision_},{"battle_revision",battle_revision_},{"round",round_},{"grant_epoch",grant_epoch_},
        {"headers",headers},{"masks",expected_masks_},{"controls",controls_},{"submitted",grant_submissions_},{"intents",actions}};
    if(notification_bounds_){
        result["version"]=2;result["design_id"]="CUSTOM-0104";
        result["initial_notification_bounds"]=*notification_bounds_;
        auto observations=Json::array();
        for(const auto& observed:notification_observations_)
            observations.push_back(observed?Json(*observed):Json(nullptr));
        result["initial_notification_observations"]=std::move(observations);
    }
    return result.dump();
}
OwnedPkRound OwnedPkRound::from_document(std::string_view text){
    if(text.empty()||text.size()>32768)throw std::invalid_argument("PK round document size");
    const auto j=Json::parse(text,[](int depth,Json::parse_event_t,Json&){if(depth>7)throw std::invalid_argument("PK round document depth");return true;});
    if(!j.is_object())throw std::invalid_argument("PK round schema");
    const bool notification=j.size()==14&&j.at("version")==2&&j.at("design_id")=="CUSTOM-0104";
    if(!notification&&(j.size()!=12||j.at("version")!=1||j.at("design_id")!="CUSTOM-0086"))
        throw std::invalid_argument("PK round schema");
    OwnedPkRound result;
    if(notification){
        const auto& bounds=j.at("initial_notification_bounds");
        const auto& observations=j.at("initial_notification_observations");
        if(!bounds.is_array()||bounds.size()!=2||!observations.is_array()||observations.size()!=2)
            throw std::invalid_argument("PK notification evidence shape");
        result.notification_bounds_.emplace();
        for(std::size_t i=0;i<2;++i){
            if(!bounds[i].is_array()||bounds[i].size()!=2)throw std::invalid_argument("PK notification bounds shape");
            (*result.notification_bounds_)[i]={number<std::uint16_t>(bounds[i][0]),number<std::uint16_t>(bounds[i][1])};
            if(!observations[i].is_null()){
                if(!observations[i].is_array()||observations[i].size()!=2)throw std::invalid_argument("PK notification observation shape");
                result.notification_observations_[i]=std::array<std::uint16_t,2>{
                    number<std::uint16_t>(observations[i][0]),number<std::uint16_t>(observations[i][1])};
            }
        }
    }
    const auto phase=number<unsigned>(j.at("phase"));
    if(phase>static_cast<unsigned>(Phase::Terminal))throw std::invalid_argument("PK round phase");result.phase_=static_cast<Phase>(phase);
    result.revision_=number<std::uint64_t>(j.at("revision"));result.battle_revision_=number<std::uint64_t>(j.at("battle_revision"));
    result.round_=number<std::uint64_t>(j.at("round"));result.grant_epoch_=number<std::uint64_t>(j.at("grant_epoch"));
    for(const auto* key:{"headers","masks","controls","submitted","intents"})
        if(!j.at(key).is_array()||j.at(key).size()!=2)throw std::invalid_argument("PK round two-view arrays");
    for(std::size_t i=0;i<2;++i){
        const auto& h=j.at("headers")[i];const auto& m=j.at("masks")[i];
        if(!h.is_array()||h.size()!=3||!m.is_array()||m.size()!=2)throw std::invalid_argument("PK round header/mask shape");
        result.headers_[i]={number<std::uint8_t>(h[0]),number<std::uint8_t>(h[1]),number<std::uint32_t>(h[2])};
        result.expected_masks_[i]={number<std::uint16_t>(m[0]),number<std::uint16_t>(m[1])};
        result.controls_[i]=boolean(j.at("controls")[i]);result.grant_submissions_[i]=boolean(j.at("submitted")[i]);
        const auto& action=j.at("intents")[i];
        if(!action.is_null()){
            if(!action.is_array()||action.size()!=3||!action[2].is_string())throw std::invalid_argument("PK round intent shape");
            result.intents_[i]=Intent{action_read(action[0]),action[1].is_null()?std::optional<std::uint16_t>{}:std::optional{number<std::uint16_t>(action[1])},action[2].get<std::string>()};
        }
    }
    if(result.document()!=text)throw std::invalid_argument("Noncanonical PK round document");return result;
}
}
