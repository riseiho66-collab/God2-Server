#include "handlers/OwnedGuildEntryService.h"
#include "net/Session.h"
#include <iostream>
#include <stdexcept>

namespace {
using namespace god2;
unsigned checks=0;
void check(bool value,const char* message) {
    ++checks;if(!value)throw std::runtime_error(message);
}
}

int main() {
    try {
        asio::io_context io;
        auto session=std::make_shared<Session>(asio::ip::tcp::socket(io),io.get_executor(),7,false,
            Session::PacketHandler{},Session::DisconnectHandler{});
        for(const auto state:{SessionState::Handshaked,SessionState::Authenticated,
            SessionState::CharacterSelected,SessionState::InWorld,SessionState::InWorld}) {
            session->set_state(state);
            check(session->state()==state,"Original nonbattle transition changed");
            check(session->battle_generation()==0,"Nonbattle transition altered battle epoch");
        }
        using Entry=OwnedGuildEntryService;
        using Conversation=OwnedGuildMembershipConversation;
        using Wire=RecoveredGuildMembership;
        Entry::Owner owner{7,17,27,1,4,3,126,126,950,0,1};
        Entry::Repository::Identity identity{};
        identity.account_id=17;identity.character_id=27;
        const auto resolve=[&](std::uint64_t id)->std::optional<Entry::Owner> {
            if(id!=7 || session->state()==SessionState::InBattle || session->state()==SessionState::Disconnected)return {};
            auto current=owner;current.battle_generation=session->battle_generation();return current;
        };
        Entry entry(resolve,[&](const auto&)->std::optional<Entry::Repository::Identity>{return identity;});
        const auto now=Entry::Clock::now();
        auto menu=entry.prepare(7,now);check(menu.has_value(),"Fresh entry did not prepare");
        session->set_state(SessionState::InBattle);
        check(session->battle_generation()==1,"Battle entry did not advance epoch");
        session->set_state(SessionState::InBattle);
        check(session->battle_generation()==1,"Repeated battle state invented a boundary");
        session->set_state(SessionState::InWorld);
        check(session->battle_generation()==2,"Battle return did not advance epoch");
        check(!entry.published(*menu,now),"Prepared menu survived battle out-and-back");
        menu=entry.prepare(7,now);check(menu && entry.published(*menu,now),"Postbattle fresh menu failed");
        auto lease=entry.prepare_choice(7,now);check(lease.has_value(),"Published menu lease missing");
        session->set_state(SessionState::InBattle);session->set_state(SessionState::InWorld);
        check(!entry.consume(*lease,{lease->request,0,Entry::context,0},now),"Published menu survived battle out-and-back");
        check(!entry.pending(7),"Stale battle menu was not consumed");
        menu=entry.prepare(7,now);check(menu && entry.published(*menu,now),"New menu after invalidation failed");
        lease=entry.prepare_choice(7,now);check(lease.has_value(),"New lease missing");
        owner.position_revision+=2; // same coordinates, two committed transfers
        check(!entry.consume(*lease,{lease->request,1,Entry::context,0},now),"Published menu survived position revision ABA");
        menu=entry.prepare(7,now);check(menu && entry.published(*menu,now),"Posttransfer fresh menu failed");
        lease=entry.prepare_choice(7,now);check(lease && entry.consume(*lease,{lease->request,1,Entry::context,0},now)==Entry::Choice::Apply,"Fresh posttransfer selection denied");

        Conversation conversation([](const Wire::Name& name,std::uint16_t page){return name[0]=='A' && page==950;});
        const auto request=[](const Wire::Prompt& prompt) {
            Wire::Request result{};result.context=static_cast<std::uint16_t>(prompt[1]+256u*prompt[2]);
            result.operation=Wire::Operation::Join;result.raw_name[0]='A';return result;
        };
        auto current=resolve(7).value();
        auto prompt=conversation.open(current,Wire::Operation::Join,now,true);check(prompt.has_value(),"Fresh8D failed");
        session->set_state(SessionState::InBattle);session->set_state(SessionState::InWorld);
        check(!conversation.consume(resolve(7).value(),request(*prompt),now,true),"6F authority survived battle ABA");
        check(!conversation.pending(7),"Stale8D battle authority remained");
        prompt=conversation.open(resolve(7).value(),Wire::Operation::Join,now,true);check(prompt.has_value(),"New8D after battle failed");
        owner.position_revision+=2;
        check(!conversation.consume(resolve(7).value(),request(*prompt),now,true),"6F authority survived transfer ABA");
        prompt=conversation.open(resolve(7).value(),Wire::Operation::Join,now,true);check(prompt.has_value(),"New8D after transfer failed");
        check(conversation.consume(resolve(7).value(),request(*prompt),now,true).has_value(),"Fresh6F after transfer denied");

        const auto epoch=session->battle_generation();
        session->set_state(SessionState::Disconnected);session->set_state(SessionState::InBattle);
        check(session->state()==SessionState::Disconnected,"Original terminal state no longer terminal");
        check(session->battle_generation()==epoch,"Rejected transition invented battle epoch");
        std::cout<<checks<<" lifecycle checks passed; not native UI acceptance\n";
        return 0;
    }catch(const std::exception& error){std::cerr<<error.what()<<'\n';return 1;}
}
