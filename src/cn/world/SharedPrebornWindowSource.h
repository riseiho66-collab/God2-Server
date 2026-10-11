#pragma once
#include "cn/world/SharedPrebornChoices.h"
#include "cn/assets/CnSharedSkillCatalog.h"
#include "cn/assets/CnNativeSkillBookBindings.h"
#include "cn/world/CnPrebornSkillChoiceSource.h"

namespace god2::cn {
//Concrete issued-window lifecycle on the SAME world game owner. Source supplies
//actual native timing/subject/resources/limits and common rule/save/replay;
//this owner never guesses them or equates a native WORD with a common object ID.
class SharedPrebornWindowSource final:public SharedPrebornChoices::WindowOwner {
public:
    using Choices=SharedPrebornChoices;
    using Lease=Choices::Lease;
    using Scope=Choices::Scope;
    using Selection=Choices::Selection;
    using Publication=Choices::Publication;
    using Window=Choices::Window;
    using Check=Choices::WindowCheck;
    using Subject=god2cn::CnPrebornSubjectState::Snapshot;
    using SkillCatalog=CnSharedSkillCatalog;
    using SkillDefinitions=std::vector<SkillCatalog::Record>;
    using SkillBookBindings=std::vector<CnNativeSkillBookBindings::Binding>;
    using SkillChoiceFacts=CnPrebornSkillChoiceSource::Facts;
    using PrimarySkills=god2cn::CnWorldPrimarySkillSource;
    struct Source {
        //Actual pinned CN definitions in the EXISTING shared catalog tables,
        //qualified against the actual immutable native source. Independent of
        //common operation revision; no TW dataset fallback or learned grants.
        std::shared_ptr<const SkillCatalog> skill_catalog;
        // Optional pinned resource bindings from the SAME shared catalog.
        // Absent provider means evidence unavailable, not all books absent.
        // Each lookup can legitimately retain a definition with no SKB match.
        std::shared_ptr<const CnNativeSkillBookBindings> skill_books;
        //Actual immutable native records/subject/resources and Current owner.
        //No output, transaction, yielding or default window during preparation.
        std::function<std::optional<Window>(const Lease&)> prepare;
        //Actual non-yielding common Lua/rule/save/replay operation; no sends.
        //Required real common subject/skill authority, independent of optional
        //native recovery evidence. No client-memory dependency or pointer as ID.
        //Own CN records corresponding to every raw83 WORD, in original order.
        //Actual common mapping/eligibility/cost remains required inside apply.
        std::function<std::optional<Publication>(const Scope&,const std::optional<Subject>&,
            const Selection&,const SkillDefinitions&,const std::optional<SkillBookBindings>&,
            const SkillChoiceFacts&)> apply;
        //Actual post-commit revision/issuer/save observation, never old Current.
        //Subject is retained identity/provenance here; do not call its obsolete
        //Current to qualify the actual new common revision after the commit.
        std::function<bool(const Scope&,const std::optional<Subject>&,const Selection&,
            const SkillDefinitions&,const std::optional<SkillBookBindings>&,
            const SkillChoiceFacts&,const Publication&)> qualify_delivery;
        // Optional actual captured bank/selected-primary source. If selected,
        // missing subject/source or any mismatch is rejected, never retried
        // through geometry-only evidence. Own-server operation never requires
        // native process access; absent supplier leaves bank identity unknown.
        std::function<std::shared_ptr<const PrimarySkills>(const Scope&,const Subject&)> read_primary_skills;
    };
    static std::shared_ptr<SharedPrebornWindowSource> create(const Lease&,Source);
    //Bind once during actual ready-world installation. Binding sends nothing.
    bool bind(const std::shared_ptr<Choices>&,const Lease&);
    void publish(Choices::Connection::Transport::Completion);
    std::optional<Scope> current_scope(const Lease&) override;
    bool current(const Scope&) override;
    std::optional<Publication> apply(const Scope&,const Selection&) override;
    bool qualify_delivery(const Scope&,const Selection&,const Publication&) override;
    std::optional<Window> prepare_window(const Lease&) override;
    bool qualify_window(const Window&,Check) override;
    bool activate_window(const Window&) override;
    void abandon_window(const Scope&) override;
private:
    SharedPrebornWindowSource(const Lease&,Source);
    struct Operation;
    void owner() const;
    bool current_retained(const Scope&);
    std::thread::id thread_=std::this_thread::get_id();
    Lease lease_;
    Source source_;
    std::weak_ptr<Choices> choices_;
    bool bound_=false;
    bool operating_=false,terminal_=false;
    std::optional<Window> prepared_,issued_;
    std::optional<Window> consumed_;
    std::shared_ptr<const PrimarySkills> prepared_primary_,issued_primary_,consumed_primary_;
    SkillDefinitions consumed_skills_;
    std::optional<SkillBookBindings> consumed_books_;
    SkillChoiceFacts consumed_choice_facts_;
};
}
