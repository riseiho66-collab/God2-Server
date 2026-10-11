#pragma once
#include "cn/net/SharedCredentialConnection.h"
#include "cn/protocol/CnCharacterSummary.h"
#include "cn/protocol/CnSpecialDirectoryWire.h"
#include "cn/assets/CnNpcNameCatalog.h"
#include "cn/assets/CnCurrentNpcNameCatalog.h"
#include "game/SharedWorldPresence.h"

namespace god2::cn {
// Admitted same common actor/current native mode0 ->D1(25/26) ->required
// real data authority ->fullF9 +qualified25 NPC names ->same CN connection.
// Conditional source: no actual backend, fake reward, rank or native name supplier.
class SharedSpecialDirectory:public std::enable_shared_from_this<SharedSpecialDirectory> {
public:
    using Connection=SharedCredentialConnection;
    using Lease=SharedWorldPresence::Lease;
    using Wire=god2cn::CnSpecialDirectoryWire;
    using Request=Wire::Request;
    struct Publication {
        std::uint64_t source_revision;
        god2cn::Bytes record; // Actual full2105bytes, including opaque fields/tail.
        std::optional<Wire::NpcNameEvidence> npc_names;
        // Optional actual snapshot for the exactly matching historical or
        // current native source projection. Never switch by EXE hash alone.
        std::optional<god2cn::CnNpcNameCatalog::Resource> npc_resource;
    };
    class WorldOwner {
    public:
        virtual ~WorldOwner()=default;
        virtual std::optional<Publication> resolve(const Lease&,const Request&)=0;
        // Own actual shared gameplay data/permissions/revision/native issuance,
        // page/row scope and strings.25 names must be qualified to the exact CN
        // NPCAppearData selectors and resource snapshot; never assume TW/common
        // key equivalence or use appearance data as monster stats/world IDs.
        virtual bool qualify_delivery(const Lease&,const Request&,const Publication&)=0;
    };
    static std::shared_ptr<SharedSpecialDirectory> attach(const std::shared_ptr<Connection>&,
        std::shared_ptr<SharedWorldPresence>,const Lease&,WorldOwner&);
    Connection::Ingress ingress(); // General ready-world mixed-record dispatcher still required.
private:
    SharedSpecialDirectory(const std::shared_ptr<Connection>&,std::shared_ptr<SharedWorldPresence>,const Lease&,WorldOwner&);
    void owner() const;
    bool current() const;
    bool dispatch(const Request&);
    void receive(god2cn::Bytes,Connection::Transport::Completion);
    std::thread::id thread_=std::this_thread::get_id();
    std::weak_ptr<Connection> connection_;
    std::shared_ptr<SharedWorldPresence> presence_;
    Lease lease_;
    WorldOwner& world_;
};
}
