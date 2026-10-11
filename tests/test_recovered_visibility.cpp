#include "handlers/RecoveredVisibility.h"
#include "handlers/RecoveredPlayerPresence.h"
#include "protocol/RecoveredWorldEntry.h"
#include "protocol/DiagnosticRemoteActor.h"
#include <iostream>
#include <stdexcept>

using Registry=god2::RecoveredVisibility;
void check(bool value) { if(!value) throw std::runtime_error("Visibility regression"); }
Registry::Presence actor(std::uint64_t session,std::uint16_t id,Registry::Scene scene={2,15}) {
    const auto spawn=god2::RecoveredRemoteActor::parse_logical(god2::DiagnosticRemoteActor::logical(0,0)).value();
    const auto removal=god2::RecoveredRemoteActorRemove::parse_logical(god2::DiagnosticRemoteActor::logical(2,0)).value();
    return {session,session,session,scene,
        god2::RecoveredRemoteActor::with_identity(spawn,id).value(),
        god2::RecoveredRemoteActorRemove::with_identity(removal,id).value()};
}
template<class Function> void rejects(Function&& function) {
    bool rejected=false;
    try { function(); } catch(const std::invalid_argument&) { rejected=true; }
    check(rejected);
}
int main() {
    try {
        {
            Registry poses;
            poses.enter(actor(1,1));poses.enter(actor(2,2));
            poses.enter(actor(3,3,{2,4}));poses.enter(actor(4,4,{3,15}));
            for(unsigned mode=1;mode<=3;++mode)for(unsigned direction=0;direction<8;++direction) {
                const std::array<std::uint8_t,3> payload{0,static_cast<std::uint8_t>((mode<<3)|direction),0xfe};
                const auto messages=poses.set_pose(1,1,1,{2,15},payload);
                check(messages.size()==1 && messages[0].recipient==2);
                check(messages[0].logical==std::vector<std::uint8_t>({0x77,1,0,0,payload[1],0,0}));
                const auto replay=poses.pose_after_spawn(poses.snapshot(1)->spawn);
                if(mode<3)
                    check(replay && std::vector<std::uint8_t>(replay->begin(),replay->end())==messages[0].logical);
                else check(!replay); // Native one-shot18 must not replay on new6F.
            }
            const auto baseline=poses.snapshot(1)->pose;
            rejects([&]{poses.set_pose(99,1,1,{2,15},{0,8,0});});
            rejects([&]{poses.set_pose(1,99,1,{2,15},{0,8,0});});
            rejects([&]{poses.set_pose(1,1,99,{2,15},{0,8,0});});
            rejects([&]{poses.set_pose(1,1,1,{2,4},{0,8,0});});
            rejects([&]{poses.set_pose(1,1,1,{2,15},{1,8,0});});
            rejects([&]{poses.set_pose(1,1,1,{2,15},{0,32,0});});
            check(poses.snapshot(1)->pose==baseline);
            poses.set_pose(1,1,1,{2,15},{0,23,0});
            poses.enter(actor(5,5));
            check(poses.pose_after_spawn(poses.snapshot(1)->spawn).has_value());
            poses.set_fight_title(1,1,1,{2,15},true);
            check(!poses.pose_after_spawn(poses.snapshot(1)->spawn));
            poses.set_fight_title(1,1,1,{2,15},false);
            poses.set_pose(1,1,1,{2,15},{0,8,0});
            auto transferred=poses.snapshot(1).value();transferred.location={2,4};
            poses.transfer(transferred);check(!poses.snapshot(1)->pose);
            poses.set_pose(1,1,1,{2,4},{0,8,0});
            const auto departed=poses.snapshot(1)->spawn;
            poses.leave(1);check(!poses.pose_after_spawn(departed));
            // Movement without any observers must also invalidate cached pose.
            Registry alone;alone.enter(actor(8,8));alone.set_pose(8,8,8,{2,15},{0,8,0});
            const auto original=alone.snapshot(8)->spawn;
            const auto movement=[&](unsigned x,unsigned y) {
                god2::RecoveredRemoteActorMove::LogicalRecord bytes{0x5e,8};
                const auto point=x|(y<<11);
                for(unsigned i=0;i<4;++i)bytes[9+i]=static_cast<std::uint8_t>(point>>(8*i));
                return god2::RecoveredRemoteActorMove::parse_logical(bytes).value();
            };
            alone.move(8,8,8,{2,15},movement(original.x(),original.y()));
            check(alone.snapshot(8)->pose.has_value());
            const std::array steps{movement(original.x()+1,original.y()),movement(original.x(),original.y())};
            alone.move_batch(8,8,8,{2,15},steps);
            check(!alone.snapshot(8)->pose);
        }
        std::array<std::uint8_t,40> profile{};
        profile[0]='A';profile[29]=1;profile[31]=1;
        const auto templates=actor(1,7);
        const auto project=[&](std::uint64_t id,const auto& wire) {
            return god2::RecoveredPlayerPresence::from_world_entry(99,100,id,wire,profile,
                templates.spawn,templates.departure);
        };
        for(const auto id:{1u,4095u}) {
            const auto wire=god2::RecoveredWorldEntry::wire(id,profile,18,12);
            const auto projected=project(id,wire);
            check(projected.session==99 && projected.account==100 && projected.character==id);
            check(projected.spawn.identity()==id && projected.departure.identity()==id);
            check(projected.spawn.x()==18 && projected.spawn.y()==12);
            check(projected.location==Registry::Scene{2,15});
            const auto bytes=god2::RecoveredRemoteActor::encode_logical(projected.spawn);
            check(bytes[29]=='A' && bytes[30]==0);
            auto corrupted=wire;corrupted.back()^=1;
            rejects([&]{project(id,corrupted);});
        }
        const auto source=god2::RecoveredWorldEntry::wire(1,profile,18,12);
        const auto town=project(1,god2::RecoveredWorldEntry::wire(1,profile,18,12,2,4,0));
        check(town.location==Registry::Scene{2,4});
        check((god2::RecoveredRemoteActor::encode_logical(town.spawn)[13]&3u)==0);
        for(const auto area:{2u,4u}) {
            const auto island=project(1,god2::RecoveredWorldEntry::wire(1,profile,318,363,
                static_cast<std::uint16_t>(area),0,1));
            check(island.location==Registry::Scene{static_cast<std::uint16_t>(area),0});
            const auto bytes=god2::RecoveredRemoteActor::encode_logical(island.spawn);
            check((bytes[13]&3u)==1 && island.spawn.x()==318 && island.spawn.y()==363);
            const auto moved=god2::RecoveredRemoteActor::with_position(island.spawn,317,364).value();
            check((god2::RecoveredRemoteActor::encode_logical(moved)[13]&3u)==1);
            check(moved.x()==317 && moved.y()==364);
            // from_world_entry includes with_normal_world_components; the
            // normal appearance copy must preserve the original kind bits.
            const auto peer=project(2,god2::RecoveredWorldEntry::wire(2,profile,317,364,
                static_cast<std::uint16_t>(area),0,1));
            Registry islands;check(islands.enter(island).empty());
            auto second=peer;second.session=101;second.account=101;
            const auto messages=islands.enter(second);check(messages.size()==2);
            for(const auto& message:messages)check((message.logical[13]&3u)==1);
        }
        rejects([&]{project(1,god2::RecoveredWorldEntry::wire(1,profile,318,363,2,4,1));});
        rejects([&]{project(1,god2::RecoveredWorldEntry::wire(1,profile,318,363,4,3,1));});
        rejects([&]{project(1,god2::RecoveredWorldEntry::wire(1,profile,318,363,3,0,1));});
        rejects([&]{project(1,god2::RecoveredWorldEntry::wire(1,profile,318,363,4,0,3));});
        rejects([&]{project(2,source);});
        rejects([&]{project(4096,god2::RecoveredWorldEntry::wire(4096,profile,18,12));});
        rejects([&]{project(1,god2::RecoveredWorldEntry::wire(1,profile,2048,12));});
        rejects([&]{project(1,god2::RecoveredWorldEntry::wire(1,profile,18,12,2,15,0));});
        rejects([&]{project(1,std::span(source).first(source.size()-1));});
        static_assert(!Registry::production_enabled);
        Registry registry;
        check(registry.enter(actor(1,1)).empty());
        const auto pair=registry.enter(actor(2,2));
        check(pair.size()==2 && pair[0].recipient==2 && pair[1].recipient==1);
        check(god2::RecoveredRemoteActor::parse_logical(pair[0].logical)->identity()==1);
        check(god2::RecoveredRemoteActor::parse_logical(pair[1].logical)->identity()==2);
        check(registry.enter(actor(3,3,{2,4})).empty());
        check(registry.enter(actor(4,4,{3,15})).empty());
        {
            using Codec=god2::RecoveredRemoteActor;
            using Appearance=god2::RecoveredPlayerAppearanceUpdate;
            const auto previous=Codec::encode_logical(registry.snapshot(1)->spawn);
            Appearance::Fields fields{1,0,0x87,0xf9,{1,0xc0,1,0x60,1,0x60,1,1}};
            const auto plan=registry.prepare_appearance(1,1,1,fields);
            check(Codec::encode_logical(registry.snapshot(1)->spawn)==previous);
            check(plan.deliveries.size()==1 && plan.deliveries[0].recipient==2);
            check(Appearance::decode(plan.deliveries[0].logical)==fields);
            rejects([&]{registry.prepare_appearance(1,99,1,fields);});
            rejects([&]{registry.prepare_appearance(1,1,99,fields);});
            auto invalid=fields;invalid.actor_identity=0x4001;
            rejects([&]{registry.prepare_appearance(1,1,1,invalid);});
            invalid=fields;invalid.transform_key=1;
            rejects([&]{registry.prepare_appearance(1,1,1,invalid);});
            registry.commit_appearance(plan);
            const auto after=Codec::encode_logical(registry.snapshot(1)->spawn);
            for(unsigned i=0;i<after.size();++i)
                if(i>=21 && i<29)check(after[i]==fields.components[i-21]);
                else if(i==79)check(after[i]==fields.raw_scalar5);
                else if(i==80)check(after[i]==fields.raw_scalar6);
                else check(after[i]==previous[i]);
            const auto late=registry.enter(actor(5,5));
            check(late[0].recipient==5 && late[0].logical==std::vector<std::uint8_t>(after.begin(),after.end()));
            registry.leave(5);
        }
        rejects([&]{registry.enter(actor(1,5));});
        rejects([&]{registry.enter(actor(5,1,{2,4}));});
        auto duplicate=actor(5,5);duplicate.character=1;
        rejects([&]{registry.enter(duplicate);});
        auto mismatched=actor(5,5);mismatched.departure=actor(6,6).departure;
        rejects([&]{registry.enter(mismatched);});
        rejects([&]{registry.enter(actor(5,0));});
        rejects([&]{registry.enter(actor(0,5));});
        rejects([&]{registry.enter(actor(5,5,{0,15}));});
        rejects([&]{registry.enter(actor(5,5,{2,1024}));});
        check(registry.size()==4);
        const auto departed=registry.leave(1);
        check(departed.size()==1 && departed[0].recipient==2);
        check(god2::RecoveredRemoteActorRemove::parse_logical(departed[0].logical)->identity()==1);
        check(registry.leave(1).empty() && registry.leave(999).empty());
        check(!registry.contains(1) && registry.size()==3);
        const auto reconnected=registry.enter(actor(9,1));
        check(reconnected.size()==2 && reconnected[0].recipient==9 && reconnected[1].recipient==2);
        check(registry.leave(9).size()==1);
        check(registry.leave(2).empty());
        Registry crowded;
        for(unsigned n=1;n<=129;++n) {
            const auto messages=crowded.enter(actor(n,static_cast<std::uint16_t>(n)));
            check(messages.size()==2*(n-1));
            for(const auto& message:messages)check(message.recipient!=0);
        }
        rejects([&]{crowded.enter(actor(130,130));});
        check(crowded.size()==129 && !crowded.contains(130));
        check(crowded.enter(actor(130,130,{2,4})).empty());
        rejects([&]{crowded.transfer(actor(130,130));});
        check(crowded.size()==130 && crowded.contains(130));
        check(crowded.enter(actor(132,132,{2,4})).size()==2);
        check(crowded.leave(132).size()==1);
        check(crowded.leave(1).size()==128);
        check(crowded.transfer(actor(130,130)).size()==256);
        check(crowded.leave(130).size()==128);
        check(crowded.enter(actor(131,131)).size()==256);
        Registry scenes;
        scenes.enter(actor(1,1));scenes.enter(actor(2,2));
        scenes.enter(actor(3,3,{2,4}));scenes.enter(actor(4,4,{3,15}));
        auto destination=actor(1,1,{2,4});
        auto invalid=destination;invalid.account=99;
        rejects([&]{scenes.transfer(invalid);});
        invalid=destination;invalid.character=99;
        rejects([&]{scenes.transfer(invalid);});
        rejects([&]{scenes.transfer(actor(1,5,{2,4}));});
        rejects([&]{scenes.transfer(actor(99,99,{2,4}));});
        rejects([&]{scenes.transfer(actor(1,1));});
        invalid=destination;invalid.location.area=0;
        rejects([&]{scenes.transfer(invalid);});
        auto switched=scenes.transfer(destination);
        check(switched.size()==4 && scenes.size()==4);
        check(switched[0].recipient==2 && switched[1].recipient==1);
        check(switched[2].recipient==1 && switched[3].recipient==3);
        check(switched[0].logical[0]==0x73 && switched[0].logical[1]==1);
        check(switched[1].logical[0]==0x73 && switched[1].logical[1]==2);
        check(switched[2].logical[0]==0x6f && switched[2].logical[1]==3);
        check(switched[3].logical[0]==0x6f && switched[3].logical[1]==1);
        rejects([&]{scenes.transfer(destination);});
        check(scenes.leave(2).empty());
        const auto leave_new=scenes.leave(1);
        check(leave_new.size()==1 && leave_new[0].recipient==3);
        check(scenes.transfer(actor(3,3,{2,15})).empty());
        Registry moving;
        moving.enter(actor(1,1));moving.enter(actor(2,2));moving.enter(actor(3,3,{2,4}));
        auto move_bytes=god2::DiagnosticRemoteActor::logical(1,0);move_bytes[1]=1;
        const auto move=god2::RecoveredRemoteActorMove::parse_logical(move_bytes).value();
        rejects([&]{moving.move(1,99,1,{2,15},move);});
        rejects([&]{moving.move(1,1,99,{2,15},move);});
        rejects([&]{moving.move(1,1,1,{2,4},move);});
        rejects([&]{moving.move(99,1,1,{2,15},move);});
        rejects([&]{moving.move(2,2,2,{2,15},move);});
        for(const auto offset:{3,4,5,7,8,12}) {
            auto bad=move_bytes;bad[offset]=1;
            rejects([&]{moving.move(1,1,1,{2,15},god2::RecoveredRemoteActorMove::parse_logical(bad).value());});
        }
        auto distant=move_bytes;distant[9]=21;
        rejects([&]{moving.move(1,1,1,{2,15},god2::RecoveredRemoteActorMove::parse_logical(distant).value());});
        const auto moved=moving.move(1,1,1,{2,15},move);
        check(moved.size()==1 && moved[0].recipient==2 && moved[0].logical==move_bytes);
        check(moving.move(1,1,1,{2,15},move).empty());
        const auto arrival=moving.enter(actor(4,4));
        check(arrival.size()==4);
        const auto latest=god2::RecoveredRemoteActor::parse_logical(arrival[0].logical).value();
        check(arrival[0].recipient==4 && latest.identity()==1 && latest.x()==19 && latest.y()==12);
        check(moving.leave(1).size()==2);
        Registry batched;
        batched.enter(actor(1,1));batched.enter(actor(2,2));
        batched.enter(actor(3,3));batched.enter(actor(4,4,{2,4}));
        auto at=[&](std::uint8_t x) {
            auto bytes=move_bytes;bytes[9]=x;
            return god2::RecoveredRemoteActorMove::parse_logical(bytes).value();
        };
        const std::array bad_path{at(19),at(22)};
        rejects([&]{batched.move_batch(1,1,1,{2,15},bad_path);});
        const auto after_failure=batched.enter(actor(5,5));
        check(god2::RecoveredRemoteActor::parse_logical(after_failure[0].logical)->x()==18);
        batched.leave(5);
        const std::array path{at(19),at(19),at(20),at(19),at(18)};
        const auto routed=batched.move_batch(1,1,1,{2,15},path);
        check(routed.size()==8);
        const std::array<unsigned,4> expected_x{19,20,19,18};
        for(std::size_t step=0;step<expected_x.size();++step) {
            for(std::size_t peer=0;peer<2;++peer) {
                const auto& delivery=routed[step*2+peer];
                const auto decoded=god2::RecoveredRemoteActorMove::parse_logical(delivery.logical).value();
                check(delivery.recipient==peer+2 && decoded.identity()==1 && decoded.x()==expected_x[step]);
            }
        }
        check(batched.move_batch(1,1,1,{2,15},{}).empty());
        rejects([&]{batched.move_batch(1,99,1,{2,15},{});});
        const auto after_roundtrip=batched.enter(actor(6,6));
        check(god2::RecoveredRemoteActor::parse_logical(after_roundtrip[0].logical)->x()==18);
        Registry fighting;
        fighting.enter(actor(1,4095));fighting.enter(actor(2,2));
        fighting.enter(actor(3,3,{2,4}));
        rejects([&]{fighting.set_fight_title(99,1,1,{2,15},true);});
        rejects([&]{fighting.set_fight_title(1,99,1,{2,15},true);});
        rejects([&]{fighting.set_fight_title(1,1,99,{2,15},true);});
        rejects([&]{fighting.set_fight_title(1,1,1,{2,4},true);});
        check(fighting.set_fight_title(1,1,1,{2,15},false).empty());
        auto title=fighting.set_fight_title(1,1,1,{2,15},true);
        check(title.size()==1 && title[0].recipient==2);
        auto title_record=god2::RecoveredRemoteActorMove::parse_logical(title[0].logical).value();
        check(title_record.identity()==4095 && title_record.state()==1 && title_record.x()==18 && title_record.y()==12);
        check(fighting.set_fight_title(1,1,1,{2,15},true).empty());
        const auto joining=fighting.enter(actor(4,4));
        check(joining[0].recipient==4 && joining[0].logical[7]==1 && joining[0].logical[8]==0);
        auto expected_spawn=god2::RecoveredRemoteActor::encode_logical(actor(1,4095).spawn);
        expected_spawn[7]=1;
        check(std::equal(joining[0].logical.begin(),joining[0].logical.end(),expected_spawn.begin(),expected_spawn.end()));
        auto own_move=move_bytes;own_move[1]=255;own_move[2]=15;
        rejects([&]{fighting.move(1,1,1,{2,15},god2::RecoveredRemoteActorMove::parse_logical(own_move).value());});
        title=fighting.set_fight_title(1,1,1,{2,15},false);
        check(title.size()==2 && title[0].recipient==2 && title[1].recipient==4);
        for(const auto& delivery:title)
            check(god2::RecoveredRemoteActorMove::parse_logical(delivery.logical)->state()==0);
        check(fighting.move(1,1,1,{2,15},god2::RecoveredRemoteActorMove::parse_logical(own_move).value()).size()==2);
        fighting.set_fight_title(1,1,1,{2,15},true);
        check(fighting.leave(1).size()==2);
        const auto fresh=fighting.enter(actor(9,4095));
        check(fresh[1].recipient==2 && fresh[1].logical[7]==0);
        Registry alone;
        alone.enter(actor(1,1));
        check(alone.set_fight_title(1,1,1,{2,15},true).empty());
        check(alone.enter(actor(2,2))[0].logical[7]==1);
        rejects([&]{alone.refresh(1,99,1,{2,15});});
        rejects([&]{alone.refresh(1,1,99,{2,15});});
        rejects([&]{alone.refresh(99,1,1,{2,15});});
        rejects([&]{alone.refresh(1,1,1,{2,4});});
        const auto refresh=alone.refresh(2,2,2,{2,15});
        check(refresh.size()==1 && refresh[0].recipient==2 && refresh[0].logical[7]==1);
        alone.enter(actor(3,3,{2,4}));
        check(alone.refresh(2,2,2,{2,15}).size()==1 && alone.size()==3);
        alone.set_fight_title(1,1,1,{2,15},false);
        check(alone.refresh(2,2,2,{2,15})[0].logical[7]==0);
        alone.leave(1);
        check(alone.refresh(2,2,2,{2,15}).empty());
        for(const auto offset:{7,8,77,78}) {
            Registry invalid_title;
            auto presence=actor(1,1);
            auto bytes=god2::RecoveredRemoteActor::encode_logical(presence.spawn);
            bytes[offset]=2;
            presence.spawn=god2::RecoveredRemoteActor::parse_logical(bytes).value();
            invalid_title.enter(presence);
            rejects([&]{invalid_title.set_fight_title(1,1,1,{2,15},true);});
            check(invalid_title.enter(actor(2,2))[0].logical[offset]==2);
        }
        for(const auto point:{std::pair{2048u,12u},std::pair{18u,2048u}}) {
            Registry invalid_title;
            auto presence=actor(1,1);
            presence.spawn=god2::RecoveredRemoteActor::with_position(presence.spawn,point.first,point.second).value();
            invalid_title.enter(presence);
            rejects([&]{invalid_title.set_fight_title(1,1,1,{2,15},true);});
        }
        std::cout<<"Visibility membership, isolation, identity and capacity passed; production disabled\n";
    } catch(const std::exception& error) { std::cerr<<error.what()<<'\n';return 1; }
}
