#include "cn/world/SharedPrebornWindowSource.h"
#include "cn/world/CnPrebornSkillReferences.h"
#include <exception>
#include <stdexcept>
#include <utility>

namespace god2::cn {
SharedPrebornWindowSource::SharedPrebornWindowSource(const Lease& lease,Source source)
    :lease_(lease),source_(std::move(source)) {}
void SharedPrebornWindowSource::owner() const {
    if(thread_!=std::this_thread::get_id())throw std::logic_error("CN preborn window source game owner mismatch");
}
struct SharedPrebornWindowSource::Operation {
    SharedPrebornWindowSource& source;
    const int exceptions=std::uncaught_exceptions();
    explicit Operation(SharedPrebornWindowSource& value):source(value) {
        source.owner();
        if(source.operating_){source.terminal_=true;throw std::logic_error("CN preborn source reentry rejected");}
        source.operating_=true;
    }
    ~Operation(){if(std::uncaught_exceptions()>exceptions)source.terminal_=true;source.operating_=false;}
};
std::shared_ptr<SharedPrebornWindowSource> SharedPrebornWindowSource::create(const Lease& lease,Source source) {
    if(!lease.account || !lease.character || !lease.session || !source.prepare || !source.apply ||
       !source.qualify_delivery || !source.skill_catalog || !source.skill_catalog->current() ||
       (source.skill_books && (!source.skill_books->uses_shared_catalog(*source.skill_catalog) ||
        !source.skill_books->current())))return {};
    return std::shared_ptr<SharedPrebornWindowSource>(new SharedPrebornWindowSource(lease,std::move(source)));
}
bool SharedPrebornWindowSource::bind(const std::shared_ptr<Choices>& choices,const Lease& lease) {
    Operation operation(*this);if(terminal_ || bound_ || !choices || lease!=lease_ || !choices->matches_window_owner(*this,lease))return false;
    choices_=choices;bound_=true;return true;
}
void SharedPrebornWindowSource::publish(Choices::Connection::Transport::Completion done) {
    owner();if(!done)throw std::invalid_argument("CN preborn window source completion required");
    std::shared_ptr<Choices> choices;
    {Operation operation(*this);if(!terminal_ && bound_)choices=choices_.lock();}
    if(!choices){done(false);return;}
    // End own observer stage before Choices calls this source's preparation.
    choices->publish_window(std::move(done));
}
std::optional<SharedPrebornWindowSource::Window> SharedPrebornWindowSource::prepare_window(const Lease& lease) {
    Operation operation(*this);const Lease actual_lease=lease;
    if(terminal_ || !bound_ || choices_.expired() || actual_lease!=lease_ || prepared_ || issued_ ||
        !source_.skill_catalog->current() || terminal_ ||
        (source_.skill_books && !source_.skill_books->current()) || terminal_)return std::nullopt;
    auto window=source_.prepare(actual_lease);
    if(terminal_ || !window || window->scope.lease!=lease_ || !window->scope.source_revision || !window->current ||
       (window->subject && (!window->subject->retained_selection() ||
        window->subject->scope().actual_revision!=window->scope.source_revision)) ||
       (consumed_ && consumed_->scope==window->scope))return std::nullopt;
    //Only provided native recovery evidence is checked against real CN rows.
    //No native snapshot is required to operate the own-server common window.
    std::shared_ptr<const PrimarySkills> primary;
    if(source_.read_primary_skills) {
        if(!window->subject)return std::nullopt;
        primary=source_.read_primary_skills(window->scope,*window->subject);
        if(terminal_ || !primary || !primary->matches_subject(*window->subject) || !primary->current() || terminal_)return std::nullopt;
    }
    if(window->subject) {
        const auto references=primary?CnPrebornSkillReferences::resolve_actual_primary_source(*primary,*source_.skill_catalog):
            CnPrebornSkillReferences::resolve_actual_snapshot(*window->subject,*source_.skill_catalog);
        if(!references)return std::nullopt;
    }
    if(terminal_ || prepared_ || issued_ || !source_.skill_catalog->current() || terminal_ ||
       (primary && !primary->current()) || terminal_)return std::nullopt;
    prepared_primary_=std::move(primary);
    prepared_=*window;return window;
}
bool SharedPrebornWindowSource::qualify_window(const Window& window,Check check) {
    Operation operation(*this);
    if(terminal_ || !bound_ || choices_.expired() || !prepared_ || window.scope.lease!=lease_ ||
       prepared_->scope!=window.scope || prepared_->records!=window.records || !prepared_->current)return false;
    const Window actual_window=window,saved=*prepared_;
    const auto scope=actual_window.scope;
    const auto primary=prepared_primary_;
    const auto observe=saved.current;
    if(!source_.skill_catalog->current() || terminal_ || (source_.skill_books && !source_.skill_books->current()) || terminal_ ||
       (saved.subject && !saved.subject->current()) || terminal_ ||
       (primary && (!saved.subject || !primary->matches_subject(*saved.subject) ||
        !primary->current())) || terminal_ || !observe(check))return false;
    if(terminal_ || !prepared_ || prepared_->scope!=scope || prepared_->records!=actual_window.records ||
       issued_ || prepared_primary_!=primary)return false;
    return (!primary || primary->current()) && !terminal_ && prepared_ && prepared_->scope==scope;
}
bool SharedPrebornWindowSource::activate_window(const Window& window) {
    Operation operation(*this);
    if(terminal_ || !prepared_ || issued_ || prepared_->scope!=window.scope || prepared_->records!=window.records)return false;
    //Local scope publication only; caller has qualified the actual held bytes.
    issued_=std::move(prepared_);prepared_.reset();issued_primary_=std::move(prepared_primary_);return true;
}
void SharedPrebornWindowSource::abandon_window(const Scope& scope) {
    Operation operation(*this);
    if(prepared_ && prepared_->scope==scope){prepared_.reset();prepared_primary_.reset();}
    if(issued_ && issued_->scope==scope){issued_.reset();issued_primary_.reset();}
}
std::optional<SharedPrebornWindowSource::Scope> SharedPrebornWindowSource::current_scope(const Lease& lease) {
    Operation operation(*this);if(terminal_ || lease!=lease_ || !issued_)return std::nullopt;
    const auto scope=issued_->scope;return current_retained(scope)?std::optional<Scope>{scope}:std::nullopt;
}
bool SharedPrebornWindowSource::current(const Scope& scope) {
    Operation operation(*this);const Scope owned_scope=scope;return current_retained(owned_scope);
}
bool SharedPrebornWindowSource::current_retained(const Scope& scope) {
    if(terminal_ || !bound_ || choices_.expired() || !issued_ || issued_->scope!=scope || !issued_->current)return false;
    const Window saved=*issued_;const auto primary=issued_primary_;
    const auto observe=saved.current;
    if(!source_.skill_catalog->current() || terminal_ || (source_.skill_books && !source_.skill_books->current()) || terminal_ ||
       (saved.subject && !saved.subject->current()) || terminal_ ||
       (primary && (!saved.subject || !primary->matches_subject(*saved.subject) ||
        !primary->current())) || terminal_ || !observe(Check::BeforeSelection))return false;
    if(terminal_ || !issued_ || issued_->scope!=scope || issued_primary_!=primary)return false;
    return (!primary || primary->current()) && !terminal_ && issued_ && issued_->scope==scope;
}
std::optional<SharedPrebornWindowSource::Publication> SharedPrebornWindowSource::apply(const Scope& scope,const Selection& selection) {
    Operation operation(*this);const Scope actual_scope=scope;const Selection actual_selection=selection;
    if(!current_retained(actual_scope))return std::nullopt;
    const Window saved=*issued_;const auto primary=issued_primary_;
    auto resolved=CnPrebornSkillChoiceSource::resolve_actual_selection(actual_selection.skills.raw,
        saved.subject,*source_.skill_catalog,source_.skill_books.get(),primary.get());
    if(!resolved || !current_retained(actual_scope))return std::nullopt;
    //Retire before the actual single common transaction. No local retries or
    //new default window; cross-connection/reconnect replay belongs to source.
    consumed_=std::move(issued_);issued_.reset();
    consumed_primary_=std::move(issued_primary_); //Retained provenance only after commit.
    consumed_skills_=std::move(resolved->definitions);
    consumed_books_=std::move(resolved->books);
    consumed_choice_facts_=std::move(resolved->facts);
    auto publication=source_.apply(actual_scope,consumed_->subject,actual_selection,consumed_skills_,consumed_books_,consumed_choice_facts_);
    return terminal_?std::nullopt:publication; //A committed effect is never retried/rolled back here.
}
bool SharedPrebornWindowSource::qualify_delivery(const Scope& scope,const Selection& selection,const Publication& publication) {
    Operation operation(*this);const Scope actual_scope=scope;const Selection actual_selection=selection;
    const Publication actual_publication=publication;
    return !terminal_ && consumed_ && consumed_->scope==actual_scope &&
        source_.qualify_delivery(actual_scope,consumed_->subject,actual_selection,consumed_skills_,consumed_books_,consumed_choice_facts_,actual_publication) &&
        !terminal_ && consumed_ && consumed_->scope==actual_scope;
    //The retired prepared-window Current is deliberately not called here.
}
}
