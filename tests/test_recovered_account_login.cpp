#include "auth/RecoveredAccountLogin.h"
#include "db/SqliteDatabase.h"
#include <algorithm>
#include <stdexcept>
#include <string_view>

namespace {
void require(bool ok,const char* message) { if(!ok) throw std::runtime_error(message); }
god2::RecoveredC2S0002::Parsed request(std::string_view name,std::string_view password) {
    require(name.size()<=23 && password.size()<=131,"test credential overflow");
    god2::RecoveredC2S0002::Payload p{};
    p[0]=4;p[167]=0xc8;
    std::copy(name.begin(),name.end(),p.begin()+1);
    std::copy(password.begin(),password.end(),p.begin()+25);
    return *god2::RecoveredC2S0002::parse(god2::RecoveredC2S0002::encode(p));
}
}
void test_recovered_account_login() {
#ifdef _WIN32
    god2::SqliteDatabase db(":memory:");db.initialize();db.migrate();
    god2::RecoveredAccountLogin closed(db.accounts(),false), registration(db.accounts(),true);
    const auto input=request("account","local-secret");
    require(closed.authenticate(input)==0,"unknown account accepted without registration");
    const auto id=registration.authenticate(input);
    require(id!=0,"account not committed");
    require(closed.authenticate(input)==id,"existing account did not bind");
    require(registration.authenticate(input)==id,"repeat registration changed account identity");
    require(closed.authenticate(request("ACCOUNT","local-secret"))==id,
        "uppercase account could not reach original lowercase identity");
    require(registration.authenticate(request("ACCOUNT","wrong"))==0,
        "uppercase account bypassed the original password");
    const auto upper_new=registration.authenticate(request("NewCASE7","Original7"));
    require(upper_new!=0,"mixed-case account could not register");
    require(closed.authenticate(request("newcase7","Original7"))==upper_new,
        "new account was not stored under the stable folded identity");
    require(closed.authenticate(request("NEWCASE7","Changed7"))==0,
        "mixed-case account accepted a changed password");
    auto bridge_payload=input.logical;bridge_payload[0]=0;
    const auto bridge_wire=god2::RecoveredC2S0002::encode(bridge_payload);
    require(!god2::RecoveredC2S0002::parse(bridge_wire),"L accepted G credentials");
    const auto bridge=god2::RecoveredC2S0002::parse(bridge_wire,0);
    require(bridge.has_value(),"G credentials rejected by decoder");
    require(!god2::RecoveredC2S0002::response(*bridge),"G credential reflected as L reply");
    require(!god2::RecoveredC2S0002::parse(input.raw,0),"G accepted L credentials");
    require(!god2::RecoveredC2S0002::parse(input.raw,29),"unsupported credential opcode accepted");
    require(registration.authenticate(*bridge)==id,"independent G authentication failed");
    auto unknown_bridge=request("unknown-g","secret").logical;unknown_bridge[0]=0;
    const auto unknown=god2::RecoveredC2S0002::parse(god2::RecoveredC2S0002::encode(unknown_bridge),0);
    require(unknown && registration.authenticate(*unknown)==0,"G performed first-login registration");
    require(closed.authenticate(request("account","wrong"))==0,"wrong password accepted");
    require(registration.authenticate(request("account","wrong"))==0,"registration overwrote existing credentials");
    const auto mixed=request("case-user","AbC123");
    const auto mixed_id=registration.authenticate(mixed);
    require(mixed_id!=0,"mixed-case account not created");
    const auto original_mixed_hash=db.accounts().find_by_id(mixed_id)->password_hash;
    require(closed.authenticate(mixed)==mixed_id,"exact mixed-case password rejected");
    require(closed.authenticate(request("case-user","aBc123"))==0,
        "wrong password letter case bypassed the original hash");
    require(closed.authenticate(request("case-user","aBc124"))==0,
        "changed digit passed password verification");
    require(closed.authenticate(request("case-user","xBc123"))==0,
        "changed letter passed password verification");
    require(closed.authenticate(request("case-user","aBc123!"))==0,
        "punctuation passed password verification");
    require(db.accounts().find_by_id(mixed_id)->password_hash==original_mixed_hash,
        "password verification changed stored password hash");
    const auto saved=db.accounts().find_by_id(id);
    require(saved && saved->username=="god2-bytes:6163636f756e74","raw account identity not preserved");
    require(saved->password_hash.find("local-secret")==std::string::npos,"plaintext password persisted");
    require(db.characters().list_for_account(id).empty(),"login fabricated a character");
    require(registration.authenticate(request("","password"))==0,"empty account accepted");
    require(registration.authenticate(request("account",""))==0,"empty password accepted");
    auto tampered=input;tampered.logical[1]^=1;
    require(registration.authenticate(tampered)==0,"forged parsed request accepted");
    tampered=input;tampered.raw.back()^=1;
    require(registration.authenticate(tampered)==0,"checksum bypassed");
    const std::string binary_name("\xa4\x40",2),binary_password("\xff\x81",2);
    const auto binary_id=registration.authenticate(request(binary_name,binary_password));
    require(binary_id!=0 && binary_id!=id,"encoded identity collision");
    require(closed.authenticate(request(binary_name,binary_password))==binary_id,"encoded credentials not preserved");
    const std::string yi("\xa4\x41",2), wu("\xa4\x61",2);
    const auto yi_id=registration.authenticate(request(yi,"Original1"));
    const auto wu_id=registration.authenticate(request(wu,"Original2"));
    require(yi_id && wu_id && yi_id!=wu_id,"Big5 trailing ASCII byte folded into another account");
    require(closed.authenticate(request(yi,"Original1"))==yi_id,"Big5 account changed identity");
    require(closed.authenticate(request(wu,"Original1"))==0,"Big5 accounts share password identity");
    asio::io_context game;
    asio::thread_pool workers(4);
    bool tick=false;
    unsigned completed=0;
    std::uint64_t concurrent_id=0;
    for(unsigned i=0;i<8;++i) registration.authenticate_async(request("Concurrent7","Original7"),
        workers.get_executor(),game.get_executor(),[&](auto result,auto error){
            require(!error && result,"concurrent registration failed");
            require(tick,"password hashing blocked the game executor");
            if(concurrent_id) require(result==concurrent_id,"concurrent registration duplicated identity");
            concurrent_id=result;++completed;
        });
    asio::post(game,[&]{tick=true;});
    game.run();workers.join();
    require(completed==8,"async authentication did not drain");
    require(closed.authenticate(request("Concurrent7","Changed7"))==0,"concurrent registration replaced password");
    asio::io_context race_game;
    asio::thread_pool race_workers(2);
    unsigned race_completed=0,race_accepted=0;
    for(auto password:{"First7","Second7"})
        registration.authenticate_async(request("Race7",password),race_workers.get_executor(),
            race_game.get_executor(),[&](auto result,auto error) {
                require(!error,"registration race raised an internal failure");
                ++race_completed;if(result) ++race_accepted;
            });
    race_game.run();race_workers.join();
    require(race_completed==2 && race_accepted==1,"registration race accepted conflicting passwords");
    const auto maximum=request(std::string(23,'n'),std::string(131,'p'));
    require(registration.authenticate(maximum)!=0,"maximum legal credential length rejected");
#endif
}
