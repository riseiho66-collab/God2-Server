#pragma once
#include <array>
#include <cstdint>
#include <optional>
#include <span>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

namespace god2 {
// CUSTOM-0162 is an explicit configured formation policy, NOT a recovered
// official row/lane rule. Native has14 local slots, not a proved7+7 layout.
// Configured pair endpoints must come from the room authority's complete DB
// version. Saved B4 is input data, never an actor/pet/Session permission.
struct OwnedBattleFormation {
    static constexpr const char* policy="CUSTOM-0162";
    struct Coordinate {std::int32_t x,y;bool operator==(const Coordinate&)const=default;};
    // Current aaf0 constructor51F410:571AA8 -> B+A7FBCCC,2x14 DWORD pairs.
    static constexpr std::array<Coordinate,28> native_coordinates{{
        {255,548},{389,466},{507,393},{611,330},{705,273},
        {383,548},{510,466},{621,393},{719,330},{515,548},
        {631,466},{736,393},{643,548},{753,466},
        {510,158},{414,210},{307,268},{187,333},{50,408},
        {412,158},{310,210},{193,268},{70,333},{314,158},
        {206,210},{86,268},{214,158},{102,210}}};
    struct Pair {std::uint8_t row0,row1;bool operator==(const Pair&)const=default;};
    struct Topology {
        std::string source_record;
        std::uint64_t version{};
        std::vector<Pair> lanes;
        void validate()const {
            if(source_record.empty()||!version||lanes.empty()||lanes.size()>7)
                throw std::invalid_argument("CUSTOM-0162 requires an explicit versioned pair table");
            std::array<bool,14> used{};
            for(const auto p:lanes){
                if(p.row0>=14||p.row1>=14||p.row0==p.row1||used[p.row0]||used[p.row1])
                    throw std::invalid_argument("CUSTOM-0162 pair table overlaps or leaves native side0");
                used[p.row0]=used[p.row1]=true;
            }
        }
        Pair positions(std::size_t lane,std::uint8_t row)const {
            validate();
            if(lane>=lanes.size()||row>1)throw std::invalid_argument("Unconfigured formation lane/row");
            const auto p=lanes[lane];return row?Pair{p.row1,p.row0}:p;
        }
        bool operator==(const Topology&)const=default;
    };
    struct Owner {
        std::uint64_t session{},account{},character{};
        std::uint16_t native_world_handle{};
        bool operator==(const Owner&)const=default;
    };
    enum class Role {Primary,Pet};
    struct Member {
        Owner owner;
        std::size_t lane{};
        std::uint8_t row{};
        bool has_pet{};
        bool operator==(const Member&)const=default;
    };
    struct Assignment {Owner owner;Role role;std::uint8_t position;bool operator==(const Assignment&)const=default;};
    class Snapshot {
    public:
        const Topology& topology()const noexcept{return topology_;}
        const std::vector<Member>& members()const noexcept{return members_;}
        const std::array<std::optional<Assignment>,28>& actors()const noexcept{return actors_;}
        std::optional<std::uint8_t> position(const Owner& owner,Role role)const noexcept {
            for(const auto& a:actors_)if(a&&a->owner==owner&&a->role==role)return a->position;
            return {};
        }
        // Reservation exists even without a pet. It cannot mint an actor/grant.
        std::optional<Owner> reserved_by(std::uint8_t slot)const noexcept {
            return slot<14?reservations_[slot]:std::optional<Owner>{};
        }
        std::uint64_t revision()const noexcept{return revision_;}
        Snapshot joined(Member member)const {auto next=members_;next.push_back(member);return make(topology_,next,successor());}
        Snapshot departed(const Owner& owner)const {
            std::vector<Member> next;bool found=false;
            for(const auto& m:members_)if(m.owner==owner)found=true;else next.push_back(m);
            if(!found)throw std::invalid_argument("Formation departure is not its exact owner");
            return make(topology_,next,successor());
        }
        // Only a trusted room-authorized successful action9 result may publish
        // this staged value. Native completion is delayed; no Written/ACK or DB
        // B4 persistence follows from preparing a new runtime assignment.
        Snapshot swapped_pair(const Owner& owner)const {
            auto next=members_;bool found=false;
            for(auto& m:next)if(m.owner==owner){
                m.row^=1;found=true;
            }
            if(!found)throw std::invalid_argument("Formation swap is not its exact owner");
            return make(topology_,next,successor());
        }
    private:
        friend struct OwnedBattleFormation;
        Snapshot(Topology topology,std::vector<Member> members,std::uint64_t revision)
            :topology_(std::move(topology)),members_(std::move(members)),revision_(revision){}
        std::uint64_t successor()const {
            if(revision_==UINT64_MAX)throw std::overflow_error("Formation revision exhausted");
            return revision_+1;
        }
        Topology topology_;std::vector<Member> members_;std::uint64_t revision_;
        std::array<std::optional<Assignment>,28> actors_{};
        std::array<std::optional<Owner>,14> reservations_{};
    };
    static Snapshot make(Topology topology,std::span<const Member> members,std::uint64_t revision) {
        topology.validate();if(!revision)throw std::invalid_argument("Formation needs a real room revision");
        if(members.size()>topology.lanes.size())throw std::invalid_argument("Formation exceeds configured lanes");
        Snapshot out(std::move(topology),std::vector<Member>(members.begin(),members.end()),revision);
        for(const auto& m:members){
            if(!m.owner.session||!m.owner.account||!m.owner.character||!m.owner.native_world_handle||m.owner.native_world_handle>=0x4000)
                throw std::invalid_argument("Formation needs exact actual member identity");
            for(const auto& old:out.reservations_)if(old&&
                (old->session==m.owner.session||old->character==m.owner.character||
                 old->native_world_handle==m.owner.native_world_handle))
                    throw std::invalid_argument("Formation duplicate member incarnation");
            const auto p=out.topology_.positions(m.lane,m.row);
            if(out.reservations_[p.row0]||out.reservations_[p.row1])
                throw std::invalid_argument("Formation lane is already reserved");
            out.reservations_[p.row0]=out.reservations_[p.row1]=m.owner;
            out.actors_[p.row0]=Assignment{m.owner,Role::Primary,p.row0};
            if(m.has_pet)out.actors_[p.row1]=Assignment{m.owner,Role::Pet,p.row1};
        }
        return out;
    }
};
}
