#pragma once
#include "game/SharedChatIdentitySource.h"
#include "shared/world/SharedActorVisibility.h"

namespace god2 {
// Exact common ready-name identity joined to an actual preceding private
// visibility publication. No actor allocation, name alias, send permission,
// reply or universal private-message namespace is inferred from this proof.
class SharedPublishedChatNameSource {
    struct Identity;
    struct Storage;
    struct Observed;
public:
    using Lookup=SharedChatIdentitySource::Lookup;
    using Binding=shared::SharedActorVisibility::Binding;
    using Lease=SharedWorldPresence::Lease;
    class Witness {
    public:
        Witness(const Witness&)=default;
        Witness& operator=(const Witness&)=default;
        Witness(Witness&&) noexcept;
        Witness& operator=(Witness&&) noexcept;
        const Binding& binding() const noexcept;
        const Lease& source() const noexcept;
        const Lease& recipient() const noexcept;
        std::uint32_t native_actor_identity() const noexcept;
        std::string_view native_name_bytes() const noexcept;
        std::uint16_t codepage() const noexcept; // Actual C2S target input page.
        std::uint16_t native_name_codepage() const noexcept; // Actual preceding6F name page.
        const Lookup& lookup() const noexcept;
        bool recipient_is(const std::shared_ptr<Session>&) const noexcept;
    private:
        friend class SharedPublishedChatNameSource;
        explicit Witness(std::shared_ptr<const Storage>);
        std::shared_ptr<const Storage> storage_;
    };
    static std::shared_ptr<SharedPublishedChatNameSource> create(std::shared_ptr<SharedChatIdentitySource>,
        std::shared_ptr<SharedWorldPresence>,std::shared_ptr<shared::SharedActorVisibility>);
    ~SharedPublishedChatNameSource();
    SharedPublishedChatNameSource(const SharedPublishedChatNameSource&)=delete;
    SharedPublishedChatNameSource& operator=(const SharedPublishedChatNameSource&)=delete;
    // Matched common original, strictly encoded separately in actual C2S target
    // input page and actual preceding6F name page; bytes may differ. Requires actual
    // raw-name issuer/profile Current: TW bit25
    // only chooses adaptation, never codepage. Native adapted names remain OPEN.
    std::optional<Witness> qualify(const Lookup&,const Binding&,std::uint16_t explicit_wire_page) const;
    bool current(const Witness&) const;
    // Final callback-free private-publication fence after caller repository reads.
    // It does not replace full current() or qualify resource/permission state.
    bool registry_current(const Witness&) const;
private:
    SharedPublishedChatNameSource(std::shared_ptr<SharedChatIdentitySource>,std::shared_ptr<SharedWorldPresence>,
        std::shared_ptr<shared::SharedActorVisibility>);
    void owner() const;
    std::optional<Observed> observe(const Lookup&,const Binding&,std::uint16_t) const;
    std::shared_ptr<SharedChatIdentitySource> identities_;
    std::shared_ptr<SharedWorldPresence> presence_;
    std::shared_ptr<shared::SharedActorVisibility> visibility_;
    std::shared_ptr<const Identity> identity_;
    std::thread::id thread_=std::this_thread::get_id();
    mutable bool busy_=false,reentered_=false;
    bool terminal_=false;
};
}
