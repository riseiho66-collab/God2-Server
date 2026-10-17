#pragma once
#include "shared/world/SharedActorVisibility.h"
#include "game/SharedWorldPresence.h"
#include <memory>
#include <optional>
#include <thread>

namespace god2 {
// Actual common stored original -> only the native6F first name field. Full
// native models, receiver raw profile/current and publication authority remain
// supplied. Does not retain Visibility, create actors or change display script.
class SharedNativeActorNameSource {
public:
    using Lease=SharedWorldPresence::Lease;
    using Native=shared::SharedActorVisibility::Native;
    static std::shared_ptr<SharedNativeActorNameSource> create(std::shared_ptr<SharedWorldPresence>);
    ~SharedNativeActorNameSource();
    SharedNativeActorNameSource(const SharedNativeActorNameSource&)=delete;
    SharedNativeActorNameSource& operator=(const SharedNativeActorNameSource&)=delete;
    bool owns_presence(const std::shared_ptr<SharedWorldPresence>&) const;
    // Source must be active; recipient may still be prepared for initial6F.
    // Actual publisher owns recipient ready/admission/phase/resource boundaries.
    // supplied.common_name_source must explicitly select this exact owner.
    // Actual repository/raw-state observers are read-only/non-yielding: no
    // pumping, sends, writes or retained borrowed arguments. Not atomic fanout.
    // Missing/adapted/unrepresentable name has no truncation/default fallback.
    std::optional<Native> project(const Lease& source,const Lease& recipient,Native supplied) const;
    bool current(const Lease& source,const Lease& recipient,const Native&) const;
private:
    explicit SharedNativeActorNameSource(std::shared_ptr<SharedWorldPresence>);
    void owner() const;
    std::optional<Native> project_owned(const Lease&,const Lease&,Native) const;
    std::shared_ptr<SharedWorldPresence> presence_;
    std::thread::id thread_=std::this_thread::get_id();
    mutable bool busy_=false,reentered_=false;
    bool terminal_=false;
};
}
