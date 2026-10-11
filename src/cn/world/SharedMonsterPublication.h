#pragma once
#include "cn/net/SharedCredentialConnection.h"
#include "cn/protocol/CnWorldMonsterLifecycle.h"
#include "cn/protocol/CnWorldMonsterMotion.h"
#include "cn/world/CnWorldMonsterDisplay.h"
#include "game/SharedWorldPresence.h"
#include <map>
#include <memory>
#include <thread>
#include <vector>

namespace god2::cn {
// Conditional common monster source ->CN71/5F/78/74 ->actual recipient transport.
// A separate recipient-native instance namespace, NOT a player presence lease.
// Mandatory real authority/resource owners; no spawn/level/removal policies or
// default native records. No production supplier/Application hosting exists.
class SharedMonsterPublication {
    struct Identity {};
public:
    using Lease=SharedWorldPresence::Lease;
    using Connection=SharedCredentialConnection;
    using Display=CnWorldMonsterDisplay;
    using Remove=god2cn::CnWorldMonsterRemove;
    using Level=god2cn::CnWorldMonsterLevel;
    using Motion=god2cn::CnWorldMonsterMotion;
    struct Source {
        std::uint64_t common_monster,incarnation,revision;
        std::uint16_t area,scene;
        bool operator==(const Source&) const=default;
    };
    struct ExpectedMotion {
        std::uint16_t target_x,target_y;
        std::uint8_t state_raw;
        std::optional<Motion::Record> last_submitted_motion;
        // Last source target only, NOT native interpolated/current position,
        // complete path, client clock, rendered coordinates or observed memory.
    };
    struct WorldOwner {
        virtual ~WorldOwner()=default;
        virtual bool current(const Source&)=0;
        // Actual visibility/coords/state/source record ownership, receiver
        // model cache, first free slot/resource creation/name/title validity,
        // shared NPC/monster pool occupancy and native scene reset qualified.
        // Model handles from Display::prepare alone do not prove allocation.
        virtual bool qualify_spawn(const Source&,const Lease&,const Display::Projection&)=0;
        virtual bool qualify_level(const Source&,const Lease&,const Level::Record&)=0;
        // Real common authority step/revision plus actual native anchor/path,
        // terrain, queue/clock and state. Previous target != current location.
        virtual bool qualify_motion(const Source& previous,const Source& current,const Lease&,
            const ExpectedMotion&,const Motion::Record&)=0;
        // Actual authority retirement or visibility departure; not inferred
        // from source.current()==false. Revision belongs to that publication.
        virtual bool qualify_removal(const Source&,const Lease&,std::uint64_t publication_revision,
            const Remove::Record&)=0;
    };
    class Binding {
    public:
        const Source& source() const noexcept {return source_;}
        const Lease& recipient() const noexcept {return recipient_;}
        std::uint16_t native_instance() const noexcept {return instance_;}
    private:
        friend class SharedMonsterPublication;
        Binding(std::shared_ptr<const Identity>,Source,Lease,std::uint16_t,std::uint64_t);
        std::shared_ptr<const Identity> identity_;
        Source source_;
        Lease recipient_;
        std::uint16_t instance_;
        std::uint64_t generation_;
    };
    SharedMonsterPublication(std::shared_ptr<SharedWorldPresence>,std::shared_ptr<WorldOwner>);
    std::optional<Binding> show(Source,const Lease&,std::weak_ptr<Connection>,
        god2cn::CnWorldMonster::Record,god2cn::CnCurrentEnemyDisplayCatalog::Resource,Display::Resources);
    bool level(const Binding&,Source current_source,const Level::Record&);
    bool motion(const Binding&,Source current_source,const Motion::Record&);
    bool hide(const Binding&,std::uint64_t publication_revision,const Remove::Record&);
    // Call only for actual known native +1499FA0 pool reset or departing
    // recipient: invalidate expected tokens, send no invented reset packet.
    bool reset_recipient(const Lease&);
private:
    struct Entry {Binding binding;Source latest;std::weak_ptr<Connection> connection;ExpectedMotion motion;};
    using Key=std::pair<std::uint64_t,std::uint16_t>;
    void owner() const;
    bool recipient_bound(const Lease&,const Source&,const std::shared_ptr<Connection>&) const;
    bool matches(const Binding&,const Entry&) const;
    void failed_output(const Entry&);
    std::thread::id thread_=std::this_thread::get_id();
    std::shared_ptr<const Identity> identity_=std::make_shared<const Identity>();
    std::shared_ptr<SharedWorldPresence> presence_;
    std::shared_ptr<WorldOwner> world_;
    std::uint64_t generation_=0;
    bool busy_=false; // Serialized callback reentry never mutates this registry.
    std::map<Key,Entry> entries_;
};
}
