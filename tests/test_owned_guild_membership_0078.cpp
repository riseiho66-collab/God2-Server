#include "handlers/OwnedGuildMembershipConversation.h"
#include <iostream>
#include <string>
#include <stdexcept>

using namespace god2;
namespace {
unsigned checks=0;
void check(bool v) {++checks;if(!v)throw std::runtime_error("Owned guild membership0078 check "+std::to_string(checks));}
using Wire=RecoveredGuildMembership;
using Service=OwnedGuildMembershipConversation;
using Owner=Service::Owner;
using Op=Wire::Operation;
const auto epoch=Service::Time{std::chrono::seconds{500}};
Owner owner{11,21,31,41,1,2,55,66,950};
Wire::Request request(std::uint16_t context=1,Op operation=Op::Create) {
    Wire::Request r{context,0xfedc,{},operation,0xa5};
    const std::string name="OwnCave";std::copy(name.begin(),name.end(),r.raw_name.begin());
    std::fill(r.raw_name.begin()+8,r.raw_name.end(),0xa5);return r;
}
bool name_valid(const Wire::Name& name,std::uint16_t cp) {
    return (cp==950 || cp==936) && name[0]!=0 &&
        std::find(name.begin(),name.end(),static_cast<std::uint8_t>('%'))==name.end();
}
void wire_tests() {
    // Fixed actual unchanged-machine producer case, independently pinned in
    // name-producer.json: interaction5678, selectedactor1234, nameOwnCave.
    const std::array<std::uint8_t,23> native={0x6f,0x78,0x56,0x34,0x12,
        'O','w','n','C','a','v','e',0,0xa5,0xa5,0xa5,0xa5,0xa5,0xa5,0xa5,0xa5,0,0xa5};
    const auto decoded=Wire::decode(native);check(decoded.has_value());
    check(decoded->context==0x5678 && decoded->selected_actor_hint==0x1234 &&
          decoded->operation==Op::Create && decoded->opaque_stack_byte==0xa5);
    check(Wire::encode_request(*decoded)==std::optional(native));
    const auto canonical=Wire::canonical(*decoded);check(canonical.has_value());
    check((*canonical)[7]==0 && (*canonical)[8]==0 && (*canonical)[15]==0);
    for(unsigned residue=0;residue<256;++residue) {
        auto raw=native;raw[22]=static_cast<std::uint8_t>(residue);
        std::fill(raw.begin()+13,raw.begin()+21,static_cast<std::uint8_t>(residue));
        const auto r=Wire::decode(raw);check(r.has_value());check(Wire::canonical(*r)==canonical);
        check(Wire::encode_request(*r)==std::optional(raw));
    }
    for(std::size_t n=0;n<native.size();++n)check(!Wire::decode(std::span(native).first(n)));
    auto raw=native;raw[0]=0x8d;check(!Wire::decode(raw));
    raw=native;raw[21]=2;check(!Wire::decode(raw));
    raw=native;std::fill(raw.begin()+5,raw.begin()+21,1);check(!Wire::decode(raw));
    auto r=request();r.raw_name.fill(1);check(!Wire::canonical(r));check(!Wire::encode_request(r));
    r=request();r.operation=static_cast<Op>(2);check(!Wire::encode_request(r));
    check(!Wire::prompt(1,static_cast<Op>(2)));
    check(Wire::prompt(0x5678,Op::Create)==std::optional(Wire::Prompt{0x8d,0x78,0x56,0,0}));
    check(Wire::prompt(0x5678,Op::Join)==std::optional(Wire::Prompt{0x8d,0x78,0x56,1,0}));
    // Consumer copies even0/FFFF context; operation is the actual branch.
    check(Wire::prompt(0,Op::Create).has_value());check(Wire::prompt(0xffff,Op::Join).has_value());
    auto max=request();max.raw_name.fill('a');max.raw_name[15]=0;check(Wire::canonical(max).has_value());
}
void lifecycle_tests() {
    Service s{name_valid};
    check(!s.consume(owner,request(),epoch,true));
    check(!s.open(owner,Op::Create,epoch,false));
    check(!s.open(owner,static_cast<Op>(2),epoch,true));
    for(unsigned field=0;field<5;++field) {
        auto bad=owner;
        if(field==0)bad.session=0;if(field==1)bad.account=0;
        if(field==2)bad.character=0;if(field==3)bad.world_generation=0;if(field==4)bad.name_codepage=1252;
        check(!s.open(bad,Op::Create,epoch,true));
    }
    check(!s.open(owner,Op::Create,Service::Time::max(),true));
    check(s.open(owner,Op::Create,epoch,true).has_value());
    check(!s.open(owner,Op::Join,epoch,true));
    auto wrong=request();wrong.context=2;check(!s.consume(owner,wrong,epoch,true));check(s.pending(owner.session));
    wrong=request();wrong.operation=Op::Join;check(!s.consume(owner,wrong,epoch,true));check(s.pending(owner.session));
    auto foreign=owner;foreign.session=12;check(!s.consume(foreign,request(),epoch,true));check(s.pending(owner.session));
    check(!s.consume(owner,request(),epoch-std::chrono::seconds{1},true));check(s.pending(owner.session));
    const auto accepted=s.consume(owner,request(),epoch,true);check(accepted.has_value());
    check(accepted->owner==owner && accepted->operation==Op::Create && accepted->name==*Wire::canonical(request()));
    check(!s.pending(owner.session));check(!s.consume(owner,request(),epoch,true));
    const auto again=s.open(owner,Op::Join,epoch,true);check(again && (*again)[1]==2);
    check(!s.consume(owner,request(),epoch,true));check(s.pending(owner.session));
    const auto joined=s.consume(owner,request(2,Op::Join),epoch,true);check(joined.has_value());
    // Selected actor/stack residue cannot change the accepted owner/name.
    const auto third=s.open(owner,Op::Create,epoch,true);check(third && (*third)[1]==3);
    auto arbitrary=request(3);arbitrary.selected_actor_hint=0;arbitrary.opaque_stack_byte=0;
    const auto clean=s.consume(owner,arbitrary,epoch,true);check(clean && clean->name==accepted->name && clean->owner==owner);
    // Any owned world/character/language change invalidates the old opening.
    for(unsigned field=0;field<9;++field) {
        Service q{name_valid};check(q.open(owner,Op::Create,epoch,true).has_value());auto moved=owner;
        if(field==0)++moved.account;if(field==1)++moved.character;if(field==2)++moved.world_generation;
        if(field==3)++moved.area;if(field==4)++moved.scene;if(field==5)++moved.x;if(field==6)++moved.y;
        if(field==7)moved.name_codepage=936;if(field==8)moved.world_generation=0;
        check(!q.consume(moved,request(),epoch,true));check(!q.pending(owner.session));
        check(!q.consume(owner,request(),epoch,true));
    }
    Service q{name_valid};check(q.open(owner,Op::Create,epoch,true).has_value());
    check(!q.consume(owner,request(),epoch,false));check(!q.pending(owner.session));
    for(auto invalid_name:{std::string{},std::string{"%evil"}}) {
        Service z{name_valid};check(z.open(owner,Op::Create,epoch,true).has_value());auto bad=request();bad.raw_name.fill(0);
        std::copy(invalid_name.begin(),invalid_name.end(),bad.raw_name.begin());
        check(!z.consume(owner,bad,epoch,true));check(!z.consume(owner,request(),epoch,true));
    }
    Service throws{[](const auto&,auto)->bool {throw std::runtime_error("storage unavailable");}};
    check(throws.open(owner,Op::Create,epoch,true).has_value());check(!throws.consume(owner,request(),epoch,true));
    check(!throws.pending(owner.session));
    Service empty{{}};check(!empty.open(owner,Op::Create,epoch,true));
    Service expiry{name_valid};check(expiry.open(owner,Op::Create,epoch,true).has_value());
    check(expiry.consume(owner,request(),epoch+std::chrono::seconds{29},true).has_value());
    check(expiry.open(owner,Op::Create,epoch,true).has_value());
    check(!expiry.consume(owner,request(2),epoch+std::chrono::seconds{30},true));
    const auto replaced=expiry.open(owner,Op::Create,epoch+std::chrono::seconds{31},true);
    check(replaced && (*replaced)[1]==3);check(!expiry.consume(owner,request(2),epoch+std::chrono::seconds{31},true));
    expiry.invalidate(owner.session);check(!expiry.pending(owner.session));
    const auto fourth=expiry.open(owner,Op::Create,epoch+std::chrono::seconds{31},true);check(fourth && (*fourth)[1]==4);
    // Exhaust native context without wrapping/reusing an accepted nonce.
    Service exhausted{name_valid};
    for(unsigned n=1;n<=65535;++n) {
        const auto p=exhausted.open(owner,Op::Create,epoch,true);
        check(p && ((*p)[1]|(unsigned{(*p)[2]}<<8))==n);exhausted.invalidate(owner.session);
    }
    check(!exhausted.open(owner,Op::Create,epoch,true));
    exhausted.disconnect(owner.session);auto new_session=owner;++new_session.session;
    check(exhausted.open(new_session,Op::Create,epoch,true).has_value());
    check(!exhausted.consume(owner,request(),epoch,true));
}
}
int main() {
    try {wire_tests();lifecycle_tests();std::cout<<"Owned guild membership0078 checks="<<checks<<" PASSED (isolated; not runtime/client acceptance)\n";return 0;}
    catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}
}
