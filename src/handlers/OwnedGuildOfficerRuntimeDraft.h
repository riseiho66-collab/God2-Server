#pragma once
// CUSTOM-0082 Application adapter DRAFT; no root source integration.
#include "handlers/OwnedGuildOfficerService.h"
#include "handlers/OwnedGuildKickService.h"
#include "handlers/OwnedGuildAnnouncementService.h"
#include <span>
#include <variant>

namespace god2 {
class OwnedGuildOfficerRuntimeDraft {
public:
    using Panel=OwnedGuildLeaderPanelService;
    using Projection=OwnedGuildOfficerProjectionDraft;
    using Service=OwnedGuildOfficerServiceDraft;
    using Kick=OwnedGuildKickService;
    using Announcement=OwnedGuildAnnouncementService;
    enum class Kind {Approve,Reject,KickMember,MemberLeave,Appoint,RemoveOffice,OfficerLeave,Denied};
    // Host supplies only strict C2S71/72/73 parser results, in original batch
    // order. World S2C71/72 entities must NEVER enter this adapter.
    struct Request {std::size_t index{};std::uint8_t opcode{},slot{};};
    using Action=std::variant<std::monostate,Panel::ActionPlan,Kick::ActionPlan,Panel::LeavePlan,Service::Plan>;
    struct Captured {
        Request request;Kind kind=Kind::Denied;
        std::optional<Projection::Publication> publication;
        Action action;
    };
    struct Notice {Announcement::Plan original;Projection::Plan decorated;std::vector<std::uint8_t> logical;};
    struct Selection {
        bool installed51{},membership_enabled{},announcement_enabled{},officers_enabled{};
        bool valid() const noexcept {
            return !officers_enabled || (installed51 && membership_enabled && announcement_enabled);
        }
        // Installed51 != enabled. False must leave rank history inert and
        // use51 baseline repositories without constructing this runtime.
        bool instantiate_officer_runtime() const noexcept {return valid() && officers_enabled;}
    };
    OwnedGuildOfficerRuntimeDraft(Panel& panel,Kick& kick,Projection& projection,Service& service):
        panel_(panel),kick_(kick),projection_(projection),service_(service){}

    std::vector<Captured> capture(std::uint64_t session,std::span<const Request> requests) const {
        std::vector<Captured> result;result.reserve(requests.size());
        // Capture once BEFORE any prefix, even for the frozen routes.
        const auto publication=projection_.publication(session);
        std::size_t previous=0;bool first=true;
        for(const auto request:requests) {
            Captured item{request,Kind::Denied,publication,{}};
            if((!first && request.index<=previous) || request.slot>=50 ||
               (request.opcode!=0x71 && request.opcode!=0x72 && request.opcode!=0x73)) {
                // Invalid host extraction is rejected as a whole, not partially
                // reordered or passed through to the frozen dispatcher.
                for(auto& old:result){old.kind=Kind::Denied;old.action={};}
                result.push_back(std::move(item));return result;
            }
            previous=request.index;first=false;
            const auto role=projection_.cached_role(session,request.slot);
            const auto self=projection_.cached_role(session,0);
            if(publication && role && self) {
                if(request.opcode==0x71 && *role==0) {
                    item.kind=Kind::Approve;
                    if(const auto plan=panel_.prepare_action(session,Panel::Action::Approve,request.slot))item.action=*plan;
                }else if(request.opcode==0x72 && *role==0) {
                    item.kind=Kind::Reject;
                    if(const auto plan=panel_.prepare_action(session,Panel::Action::Reject,request.slot))item.action=*plan;
                }else if(request.opcode==0x72 && *role==1) {
                    item.kind=Kind::KickMember;
                    if(const auto plan=kick_.prepare_action(session,request.slot))item.action=*plan;
                }else if(request.opcode==0x73 && request.slot==0 && *self==1) {
                    item.kind=Kind::MemberLeave;
                    if(const auto plan=panel_.prepare_leave(session,0))item.action=*plan;
                }else if(request.opcode==0x71 && *role==1 && request.slot && *self==3) {
                    item.kind=Kind::Appoint;
                    if(const auto plan=service_.prepare(session,Service::Action::Appoint,request.slot))item.action=*plan;
                }else if(request.opcode==0x72 && *role==2 && request.slot && *self==3) {
                    item.kind=Kind::RemoveOffice;
                    if(const auto plan=service_.prepare(session,Service::Action::RemoveOffice,request.slot))item.action=*plan;
                }else if(request.opcode==0x73 && request.slot==0 && *self==2) {
                    item.kind=Kind::OfficerLeave;
                    if(const auto plan=service_.prepare(session,Service::Action::SelfLeave,0))item.action=*plan;
                }
                // role3 demotion/kick/leave, role2 admission, succession73,
                // quota/fees remain DENIED/OPEN, never fallback to ordinarykick.
                if(projection_.publication(session)!=publication)item.action={};
                if(!bound(item))item.action={};
            }
            result.push_back(std::move(item));
        }
        return result;
    }
    bool execute(const Captured& item) {
        // Stale requests may not consume a different fresh publication. No
        // fallback, no re-prepare from a possibly repurposed recipient slot.
        if(!item.publication)return false;
        const auto& pub=*item.publication;const auto session=pub.base.state.owner.session;
        if(projection_.publication(session)!=item.publication)return false;
        bool result=false;
        if(bound(item)) {
            if(const auto action=std::get_if<Panel::ActionPlan>(&item.action)) {
                if(panel_.current(*action) && projection_.publication(session)==item.publication)result=panel_.execute(*action);
            }else if(const auto action=std::get_if<Kick::ActionPlan>(&item.action)) {
                if(kick_.current(*action) && projection_.publication(session)==item.publication)result=kick_.execute(*action);
            }else if(const auto action=std::get_if<Panel::LeavePlan>(&item.action)) {
                if(panel_.current(*action) && projection_.publication(session)==item.publication)result=panel_.leave(*action,0);
            }else if(const auto action=std::get_if<Service::Plan>(&item.action))return service_.execute(*action);
        }
        // Frozen methods already consume before SQL. If they fail before doing
        // so, consume this same publication. Cache remains for92 reconciliation.
        if(projection_.publication(session)==item.publication)projection_.invalidate(session);
        return result;
    }
    // Host calls for the actor and all captured connected accepted+pending
    // sessions after a successful write; actor also on denial/canceled suffix.
    // This is a batch-owned revocation: do not call against an unrelated later
    // async publication. Defer all reconcile/open writes until suffix drained.
    void invalidate(std::uint64_t session){projection_.invalidate(session);}
    void observe_world(std::uint64_t session){projection_.observe_world(session);}

    std::optional<Notice> prepare_notice(Announcement& announcements,std::uint64_t session,bool open=false) const {
        const auto original=announcements.prepare(session,open);if(!original)return {};
        const auto decorated=projection_.decorate_existing_base_plan(original->panel);if(!decorated)return {};
        if(original->logical.size()<original->panel.logical.size() ||
           !std::equal(original->panel.logical.begin(),original->panel.logical.end(),original->logical.begin()))return {};
        Notice next{*original,*decorated,decorated->logical};
        next.logical.insert(next.logical.end(),original->logical.begin()+original->panel.logical.size(),original->logical.end());
        if(!current_notice(announcements,next))return {};return next;
    }
    bool current_notice(const Announcement& announcements,const Notice& plan) const {
        // Exact originalPlan drives98/current authority; never mutate its
        // panel.logical to fool the frozen publisher into a new plan.
        return announcements.current(plan.original) && projection_.current(plan.decorated) &&
            plan.original.panel.next==plan.decorated.base.next &&
            plan.original.panel.open_panel==plan.decorated.base.open_panel &&
            plan.original.panel.logical==plan.decorated.base.logical;
    }
    bool published_notice(Announcement& announcements,const Notice& plan,Announcement::Time now) {
        if(!current_notice(announcements,plan)){announcements.invalidate(plan.original.panel.next.owner.session);return false;}
        const bool result=projection_.published_with_external(plan.decorated,[&]{return announcements.published(plan.original,now);});
        if(!result)announcements.invalidate(plan.original.panel.next.owner.session);return result;
    }
    // prepare_clear/current/send_world_records/Cleared must use SAME exact
    // Base::ClearPlan (old nonself92 then self92). Do not forget cache on an
    // unready receiver or failed tail; retry debt later. Only after cleared true:
    bool complete_clear(const Panel::ClearPlan& plan) {
        if(!panel_.cleared(plan))return false;projection_.forget_after_clear(plan.owner.session);return true;
    }
private:
    static bool bound(const Captured& item) {
        if(!item.publication)return false;const auto& pub=*item.publication;
        if(const auto p=std::get_if<Panel::ActionPlan>(&item.action))return
            (item.kind==Kind::Approve || item.kind==Kind::Reject) && p->panel==pub.base.state &&
            p->publication==pub.base.serial && p->slot==item.request.slot &&
            p->action==(item.kind==Kind::Approve?Panel::Action::Approve:Panel::Action::Reject);
        if(const auto p=std::get_if<Kick::ActionPlan>(&item.action))return item.kind==Kind::KickMember &&
            p->panel==pub.base.state && p->publication==pub.base.serial && p->slot==item.request.slot;
        if(const auto p=std::get_if<Panel::LeavePlan>(&item.action))return item.kind==Kind::MemberLeave &&
            item.request.slot==0 && p->panel==pub.base.state && p->publication==pub.base.serial;
        if(const auto p=std::get_if<Service::Plan>(&item.action))return p->publication==pub && p->slot==item.request.slot &&
            ((item.kind==Kind::Appoint && p->action==Service::Action::Appoint) ||
             (item.kind==Kind::RemoveOffice && p->action==Service::Action::RemoveOffice) ||
             (item.kind==Kind::OfficerLeave && p->action==Service::Action::SelfLeave));
        return false;
    }
    Panel& panel_;Kick& kick_;Projection& projection_;Service& service_;
};
}
