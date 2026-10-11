#include "handlers/RecoveredWorldService.h"
#include "protocol/RecoveredCharacterPose.h"
#include "protocol/RecoveredSeedExchange.h"
#include "protocol/RecoveredPostSeed.h"
#include "protocol/RecoveredCharacterBootstrap.h"
#include "protocol/RecoveredCharacterCreateResult.h"
#include <algorithm>
#include <array>
#include <chrono>
#include <iostream>
#include <stdexcept>

namespace {
void require(bool condition, const char* message) {
    if (!condition) throw std::runtime_error(message);
}

void inventory_move_routing() {
    using namespace god2;
    using Record=RecoveredWorldRecords::Record;
    asio::io_context io;
    asio::ip::tcp::acceptor acceptor(io,{asio::ip::address_v4::loopback(),0});
    asio::ip::tcp::socket peer(io);peer.connect(acceptor.local_endpoint());
    unsigned ready_calls=0;
    Session::RecoveredCharacterHandlers handlers;
    handlers.list=[](std::uint64_t){return std::array<std::uint8_t,78>{};};
    handlers.create=[](std::uint64_t,const RecoveredCharacterCreate&)->std::uint64_t{
        throw std::runtime_error("Inventory fixture unexpectedly created a character");};
    handlers.select_created=[](std::uint64_t,std::uint64_t,std::uint8_t)->std::uint64_t{
        throw std::runtime_error("Inventory fixture unexpectedly selected a new character");};
    handlers.select_existing=[](std::uint64_t account,std::uint8_t token){
        require(account==7 && token==0,"Inventory fixture owner changed");return std::uint64_t{0x1234};};
    const auto world=RecoveredWorldEntry::wire(0x1234);
    handlers.world_entry=[&](std::uint64_t,std::uint64_t account,std::uint64_t character){
        require(account==7 && character==0x1234,"Inventory fixture character changed");return world;};
    handlers.world_ready=[&](Session&){++ready_calls;};
    handlers.world_records=[](Session&,std::span<const Record>)->std::optional<std::vector<std::uint8_t>>{
        return std::vector<std::uint8_t>{};};
    auto session=std::make_shared<Session>(acceptor.accept(),io.get_executor(),100,false,
        Session::PacketHandler{},Session::DisconnectHandler{},ProtocolMode::God2CharacterConnection,
        [](const RecoveredC2S0002::Parsed&){return std::uint64_t{7};},std::move(handlers));
    peer.non_blocking(true);session->start();
    const auto pump=[&]{io.restart();io.run_for(std::chrono::milliseconds(5));};
    const auto send=[&](std::span<const std::uint8_t> bytes){
        peer.non_blocking(false);asio::write(peer,asio::buffer(bytes.data(),bytes.size()));peer.non_blocking(true);};
    const auto expect=[&](std::span<const std::uint8_t> bytes){
        std::vector<std::uint8_t> actual(bytes.size());std::size_t received=0;
        const auto deadline=std::chrono::steady_clock::now()+std::chrono::seconds(2);
        while(received<actual.size() && std::chrono::steady_clock::now()<deadline){
            pump();asio::error_code error;
            received+=peer.read_some(asio::buffer(actual.data()+received,actual.size()-received),error);
            require(!error || error==asio::error::would_block || error==asio::error::try_again,
                    "Inventory fixture handshake closed");
        }
        require(received==actual.size() && std::equal(actual.begin(),actual.end(),bytes.begin()),
                "Inventory fixture handshake reply mismatch");
    };
    unsigned moves=0,other_callbacks=0;bool allow=true;
    RecoveredInventoryMoveRequest::Request received{};
    RecoveredWorldService service(
        [&](Session&,std::span<const RecoveredMovement::Request>){++other_callbacks;return std::vector<std::uint8_t>{1};},
        [&](Session&,std::span<const Record>)->std::optional<std::vector<std::uint8_t>>{++other_callbacks;return std::vector<std::uint8_t>{};},
        [&](Session&,const RecoveredTargetItemRequest::Request&)->std::optional<std::vector<std::uint8_t>>{++other_callbacks;return std::vector<std::uint8_t>{};},
        [&](Session&,const RecoveredWorldService::QuestRequest&)->std::optional<std::vector<std::uint8_t>>{++other_callbacks;return std::vector<std::uint8_t>{};},
        [&](Session&,const RecoveredSelectionItemRequest::Request&)->std::optional<std::vector<std::uint8_t>>{++other_callbacks;return std::vector<std::uint8_t>{};},
        [&](Session&,const RecoveredTeleport::Selection&)->std::optional<std::vector<std::uint8_t>>{++other_callbacks;return std::vector<std::uint8_t>{};},
        [&](Session& actual,const RecoveredInventoryMoveRequest::Request& request)->std::optional<std::vector<std::uint8_t>>{
            require(&actual==session.get(),"Move session changed");++moves;received=request;
            if(!allow)return std::nullopt;return std::vector<std::uint8_t>{0x41,0,0,29,0};});
    const Record move=RecoveredInventoryMoveRequest::Request{0,29};
    const Record tick=RecoveredWorldRecords::Tick{};
    const std::array standalone{move};
    // Acquire ready through the real socket/state machine, not private-state writes.
    expect(RecoveredSeedExchange::hello());send(RecoveredSeedExchange::response);
    expect(RecoveredPostSeed::frame(0xf6));
    RecoveredC2S0002::Payload credentials{};credentials[167]=0xc8;
    send(RecoveredC2S0002::encode(credentials));expect(RecoveredCharacterBootstrap::candidate());
    std::array<std::uint8_t,38> select{};select[0]=0x1a;select[34]=4;
    send(RecoveredWorldFrame::encode(select));expect(RecoveredCharacterCreateResult::committed_success());expect(world);
    require(!session->recovered_world_ready(),"Fixture became ready before initializer tail");
    for(const auto state:{SessionState::CharacterSelected,SessionState::InWorld,SessionState::InBattle}){
        session->set_state(state);
        require(!service.handle(*session,standalone) && moves==0 && other_callbacks==0,
                "Unready inventory transaction reached a callback");
    }
    session->set_state(SessionState::CharacterSelected);
    send(RecoveredWorldFrame::encode(std::array<std::uint8_t,9>{0x1f,0,0x23,0,0x1c,0x34,0x12,1,0}));
    const auto deadline=std::chrono::steady_clock::now()+std::chrono::seconds(2);
    while(!session->recovered_world_ready() && std::chrono::steady_clock::now()<deadline)pump();
    require(session->recovered_world_ready() && ready_calls==1,"Real initializer tail failed");
    const std::array pose_notification{Record{RecoveredWorldRecords::ClientPoseNotification{{0,8,0xfe}}}};
    require(session->state()==SessionState::CharacterSelected,
        "Native ready fixture unexpectedly changed session state");
    const auto native_pose_reply=service.handle(*session,pose_notification);
    require(native_pose_reply && RecoveredWorldFrame::decode(*native_pose_reply)==
        std::optional<std::vector<std::uint8_t>>{std::vector<std::uint8_t>{0x77,0x34,0x12,0,8,0,0}} &&
        moves==0 && other_callbacks==0,"Native CharacterSelected ready lease rejected exact pose77");
    session->set_state(SessionState::InBattle);
    require(!service.handle(*session,pose_notification),"Ready lease admitted battle pose");
    session->set_state(SessionState::CharacterSelected);
    unsigned deities=0,pets=0;
    RecoveredWorldService companions({}, {}, {}, {},
        [&](Session&,const RecoveredSelectionItemRequest::Request& request)->std::optional<std::vector<std::uint8_t>> {
            require(request.raw_slot==42 && request.client_item_id==28001,"Pet request changed");
            ++pets;return std::vector<std::uint8_t>{};
        },{}, {},
        [&](Session&,const RecoveredDeitySelection::Request& request)->std::optional<std::vector<std::uint8_t>> {
            require(request.key==100,"Deity request changed");++deities;return std::vector<std::uint8_t>{};
        });
    const Record deity=RecoveredDeitySelection::Request{100};
    const Record pet=RecoveredSelectionItemRequest::Request{28001,42};
    const Record control=RecoveredWorldRecords::ClientControl1F{};
    require(companions.handle(*session,std::array{deity,tick}) && deities==1,"Deity route failed");
    require(companions.handle(*session,std::array{tick,pet,control,tick}) && pets==1,"Native pet28+1F route failed");
    for(const auto& batch:std::vector<std::vector<Record>>{{deity,deity},{deity,pet},{deity,move},
        {pet,control,control},{control,pet},{pet,Record{RecoveredSelectionItemRequest::Request{28001,0}}},
        {pet,Record{RecoveredSelectionItemRequest::Request{28001,43}}},{pet,move},{deity,control}})
        require(!companions.handle(*session,batch) && deities==1 && pets==1,"Mixed companion operation reached callback");
    session->set_state(SessionState::InBattle);
    require(!companions.handle(*session,std::array{deity}) && !companions.handle(*session,std::array{pet}),"Companion changed during battle");
    session->set_state(SessionState::CharacterSelected);
    const auto decoded=RecoveredWorldRecords::decode(std::array<std::uint8_t,4>{0x67,100,0x30,0});
    require(decoded && decoded->size()==2 && std::get<RecoveredDeitySelection::Request>((*decoded)[0]).key==100,
        "Native67 grammar not connected");
    RecoveredWorldService disabled({});
    require(!disabled.handle(*session,standalone),"Missing inventory authority accepted");
    for(const auto state:{SessionState::CharacterSelected,SessionState::InWorld}){
        session->set_state(state);
        for(const auto& batch:std::vector<std::vector<Record>>{{move},{tick,move},{move,tick},{tick,move,tick}}){
            const auto before=moves;const auto reply=service.handle(*session,batch);
            require(reply && *reply==std::vector<std::uint8_t>({0x41,0,0,29,0}) && moves==before+1 &&
                received==RecoveredInventoryMoveRequest::Request{0,29} && other_callbacks==0,
                "Ready move/tick batch changed callback fields/count/response");
        }
    }
    allow=false;require(!service.handle(*session,standalone),"Inventory authority denial ignored");
    allow=true;const auto before=moves;
    for(const Record other:{move,Record{RecoveredInventoryMoveRequest::Request{29,0}},
        Record{RecoveredMovement::Request{}},Record{RecoveredTargetItemRequest::Request{}},
        Record{RecoveredInventoryItemRequest::Request{}},Record{RecoveredSelectionItemRequest::Request{}},
        Record{RecoveredQuestAction::Request{}},Record{RecoveredQuestClose::Request{}},
        Record{RecoveredBattleCommand::BasicAttackRequest{}},Record{RecoveredSkillCommand::Record{}},
        Record{RecoveredTeleport::Selection{}},Record{RecoveredWorldRecords::ClientControl6D{}},
        Record{RecoveredWorldRecords::ClientDiagnostic{{0x9a,6,0,0,0,0}}}}){
        for(const auto& batch:std::vector<std::vector<Record>>{{move,other},{other,move},{tick,move,tick,other,tick}})
            require(!service.handle(*session,batch) && moves==before && other_callbacks==0,
                    "Mixed/duplicate inventory batch committed a callback prefix");
    }
    for(const auto state:{SessionState::Connected,SessionState::Handshaked,SessionState::Authenticated,
        SessionState::InBattle,SessionState::Disconnected}){
        session->set_state(state);
        const std::array with_tick{tick,move,tick};
        require(!service.handle(*session,with_tick) && moves==before && other_callbacks==0,
                "Inventory transaction ran outside ready world state");
    }
    session->set_state(SessionState::InWorld);session->account_id=0;
    require(!service.handle(*session,standalone) && moves==before,"Anonymous move routed");
    session->account_id=7;session->character_id=0;
    require(!service.handle(*session,standalone) && moves==before,"Unowned move routed");
    peer.close();session->close();pump();
}
void teleport_routing() {
    using namespace god2;
    using Record=RecoveredWorldRecords::Record;
    asio::io_context io;
    auto session=std::make_shared<Session>(asio::ip::tcp::socket(io),io.get_executor(),99,false,
        Session::PacketHandler{},Session::DisconnectHandler{});
    session->account_id=7;session->character_id=9;session->set_state(SessionState::InWorld);
    unsigned selections=0;
    bool allow=true;
    RecoveredTeleport::Selection received{};
    RecoveredWorldService enabled({}, {}, {}, {}, {},
        [&](Session& actual,const RecoveredTeleport::Selection& request)
            ->std::optional<std::vector<std::uint8_t>> {
            require(&actual==session.get(),"Teleport session changed");
            ++selections;received=request;
            if(!allow) return std::nullopt;
            return std::vector<std::uint8_t>{0x71,0x82};
        });
    RecoveredWorldService disabled({});
    std::vector<Record> request;
    for(const auto context:{0x1234u,0x61eu,0x622u}) {
        for(unsigned tail=0;tail<256;++tail) {
            const auto opcode=static_cast<std::uint8_t>(RecoveredTeleport::special_context(
                static_cast<std::uint16_t>(context))?0xa9:0x99);
            const RecoveredTeleport::SelectionBytes bytes{opcode,static_cast<std::uint8_t>(context),
                static_cast<std::uint8_t>(context>>8),5,static_cast<std::uint8_t>(tail)};
            request=RecoveredWorldRecords::parse_frame(RecoveredWorldFrame::encode(bytes)).value();
            require(!disabled.handle(*session,request),"Teleport selection accepted without authority");
            const auto result=enabled.handle(*session,request);
            require(result && *result==std::vector<std::uint8_t>({0x71,0x82}) &&
                received==RecoveredTeleport::Selection{opcode,static_cast<std::uint16_t>(context),5,
                    static_cast<std::uint8_t>(tail)},"Teleport callback payload/response changed");
        }
    }
    allow=false;
    require(!enabled.handle(*session,request),"Teleport authority denial ignored");
    const auto before=selections;
    const Record control=RecoveredWorldRecords::ClientControl6D{};
    const std::array control_only{control};
    const auto control_reply=enabled.handle(*session,control_only);
    require(control_reply && control_reply->empty() && selections==before,
        "Opaque 6D control incorrectly invoked teleport selection authority");
    for(const Record other:{Record{RecoveredWorldRecords::Tick{}},
        Record{RecoveredMovement::Request{}},Record{RecoveredBattleCommand::BasicAttackRequest{}},
        Record{RecoveredNpcInteraction::Request{42}},control,request.front()}) {
        const std::array forward{request.front(),other},reverse{other,request.front()};
        require(!enabled.handle(*session,forward) && !enabled.handle(*session,reverse) && selections==before,
            "Mixed teleport batch committed a prefix");
    }
    for(const auto state:{SessionState::Connected,SessionState::Handshaked,SessionState::Authenticated,
        SessionState::CharacterSelected,SessionState::InBattle,SessionState::Disconnected}) {
        session->set_state(state);
        require(!session->recovered_world_ready(),"Uninitialized test session unexpectedly world-ready");
        require(!enabled.handle(*session,request) && selections==before,
            "Teleport selection routed during bootstrap/battle/disconnect");
    }
    session->set_state(SessionState::InWorld);
    session->account_id=0;
    require(!enabled.handle(*session,request) && selections==before,"Anonymous teleport selection routed");
    session->account_id=7;session->character_id=0;
    require(!enabled.handle(*session,request) && selections==before,"Unowned teleport selection routed");
}
}
int main() {
    try {
        using namespace god2;
        using Record = RecoveredWorldRecords::Record;
        asio::io_context io;
        auto session=std::make_shared<Session>(asio::ip::tcp::socket(io),io.get_executor(),1,false,
            Session::PacketHandler{},Session::DisconnectHandler{});
        session->account_id=7;session->character_id=9;session->set_state(SessionState::InWorld);
        unsigned movements=0,battles=0;
        RecoveredWorldService service(
            [&](Session& actual,std::span<const RecoveredMovement::Request> moves) {
                require(&actual==session.get() && moves.size()==2,"Movement batch changed");
                require(moves[0].x==18 && moves[1].x==19,"Movement order changed");
                ++movements;return std::vector<std::uint8_t>{1};
            },
            [&](Session&,std::span<const Record> records)->std::optional<std::vector<std::uint8_t>> {
                require(!records.empty(),"Empty battle callback");++battles;
                return std::vector<std::uint8_t>{2};
            });
        const Record tick=RecoveredWorldRecords::Tick{};
        const Record npc=RecoveredNpcInteraction::Request{42};
        for(const auto& batch:std::vector<std::vector<Record>>{
            {npc},{tick,npc},{npc,tick},{npc,npc},
            {RecoveredQuestAction::Request{0x1234,2,0x9a,0x18},npc},
            {RecoveredMovement::Request{},npc},{npc,RecoveredMovement::Request{}}})
            require(!service.handle(*session,batch) && movements==0 && battles==0,
                    "NPC grammar authorized operation or committed prefix");
        const auto item_bytes=RecoveredTargetItemRequest::encode({9,3107,0,0xa5});
        const auto parsed=RecoveredWorldRecords::parse_frame(RecoveredWorldFrame::encode(item_bytes));
        require(parsed && parsed->size()==1,"Native26 grammar missing");
        const Record item=parsed->front();
        require(!service.handle(*session,*parsed),"Default supply route enabled");
        // EGG 9301 is a real current-definition flag-4 native request.
        const auto selection_bytes=RecoveredSelectionItemRequest::encode({9301,0});
        const auto selection=RecoveredWorldRecords::parse_frame(
            RecoveredWorldFrame::encode(selection_bytes));
        require(selection && selection->size()==1 &&
            std::holds_alternative<RecoveredSelectionItemRequest::Request>(selection->front()),
            "Native28 grammar missing");
        require(!service.handle(*session,*selection),
            "Selection item request admitted without a proven reply policy");
        for(std::size_t length=1;length<item_bytes.size();++length)
            require(!RecoveredWorldRecords::decode(std::span(item_bytes).first(length)),"Truncated26 accepted");
        auto malformed=std::vector<std::uint8_t>(item_bytes.begin(),item_bytes.end());
        malformed.push_back(0xff);
        require(!RecoveredWorldRecords::decode(malformed),"Unknown suffix admitted26 prefix");
        unsigned supplies=0;
        RecoveredWorldService with_supply({}, {},
            [&](Session& actual,const RecoveredTargetItemRequest::Request& request)
                ->std::optional<std::vector<std::uint8_t>> {
                require(&actual==session.get() && request.raw_target==9 && request.client_item_id==3107 &&
                    request.raw_slot==0 && request.raw_tail==0xa5,"Supply fields changed");
                ++supplies;return std::vector<std::uint8_t>{3};
            });
        require(with_supply.handle(*session,*parsed).has_value() && supplies==1,"Supply not routed");
        require(!with_supply.handle(*session,*selection) && supplies==1,
            "Selection item request aliased target-item supply policy");
        unsigned selections=0;
        RecoveredWorldService with_selection({}, {}, {}, {},
            [&](Session& actual,const RecoveredSelectionItemRequest::Request& request)
                ->std::optional<std::vector<std::uint8_t>> {
                require(&actual==session.get() && request.client_item_id==9301 &&
                        request.raw_slot==0,"Selection item fields or owner changed");
                ++selections;return std::vector<std::uint8_t>{4};
            });
        require(with_selection.handle(*session,*selection)==
                std::optional<std::vector<std::uint8_t>>{std::vector<std::uint8_t>{4}} &&
                selections==1,"Qualified selection callback not reached");
        const std::array selection_ticks{tick,selection->front(),tick};
        require(with_selection.handle(*session,selection_ticks).has_value() &&
                selections==2,"Selection/tick batch rejected");
        for(const auto& batch:std::vector<std::vector<Record>>{
            {selection->front(),selection->front()},
            {selection->front(),item},
            {item,selection->front()},
            {selection->front(),RecoveredMovement::Request{}},
            {selection->front(),RecoveredBattleCommand::BasicAttackRequest{}}})
            require(!with_selection.handle(*session,batch) && selections==2,
                    "Mixed selection batch invoked callback");
        const std::array supply_ticks{tick,item,tick};
        require(with_supply.handle(*session,supply_ticks).has_value() && supplies==2,"Supply/tick batch rejected");
        for(const auto& batch:std::vector<std::vector<Record>>{
            {item,item},{item,RecoveredMovement::Request{}},{RecoveredMovement::Request{},item},
            {item,RecoveredBattleCommand::BasicAttackRequest{}},{item,RecoveredInventoryItemRequest::Request{}}})
            require(!with_supply.handle(*session,batch) && supplies==2,"Mixed supply batch invoked callback");
        session->set_state(SessionState::InBattle);
        require(!with_supply.handle(*session,*parsed) && supplies==2,"Battle accepted world supply");
        require(!with_selection.handle(*session,*selection) && selections==2,
                "Battle accepted world selection item");
        session->set_state(SessionState::InWorld);
        const Record move=RecoveredMovement::Request{18,12,1,0};
        const Record attack=RecoveredBattleCommand::BasicAttackRequest{};
        const std::array heartbeat{tick};
        const std::array timer{Record{RecoveredWorldRecords::TimerNotification{{0,0,0,0,1,0,0,0}}}};
        require(!service.handle(*session,timer),"Timer36 parser accidentally authorized normal-world behavior");
        const std::array context{Record{RecoveredWorldRecords::ContextNotification{{1,0,0,0}}}};
        require(!service.handle(*session,context),"Context1C parser accidentally authorized normal-world behavior");
        const Record diagnostic=RecoveredWorldRecords::ClientDiagnostic{{0x9a,10,0,0,'t','e','s','t',0,0}};
        const std::array diagnostic_only{diagnostic};
        const auto diagnostic_reply=service.handle(*session,diagnostic_only);
        require(diagnostic_reply && diagnostic_reply->empty() && movements==0 && battles==0,
                "Native client diagnostic should have no game action or response");
        const Record control=RecoveredWorldRecords::ClientControl1F{};
        const std::array control_only{control};
        const auto control_reply=service.handle(*session,control_only);
        require(control_reply && control_reply->empty() &&
                movements==0 && battles==0,"Standalone client 1F control not accepted cleanly");
        const std::array control_and_move{control,move};
        require(!service.handle(*session,control_and_move) && movements==0,
                "Client 1F control mixed with movement");
        const Record control6d=RecoveredWorldRecords::ClientControl6D{};
        const std::array control6d_only{control6d};
        const auto control6d_reply=service.handle(*session,control6d_only);
        require(control6d_reply && control6d_reply->empty() && movements==0 && battles==0,
                "Standalone native 6D control changed state or emitted a fabricated reply");
        const std::array control6d_and_move{control6d,move};
        require(!service.handle(*session,control6d_and_move) && movements==0,
                "Client 6D control mixed with movement");
        const Record opaque74=RecoveredWorldRecords::ClientOpaque74{0xa5};
        const std::array opaque74_only{opaque74};
        const auto opaque74_reply=service.handle(*session,opaque74_only);
        require(opaque74_reply && opaque74_reply->empty() && movements==0 && battles==0,
                "Standalone native74 changed gameplay or invented a response");
        const std::array opaque74_and_move{opaque74,move};
        require(!service.handle(*session,opaque74_and_move) && movements==0,
                "Native74 mixed with movement accepted");
        const Record panel88=RecoveredWorldRecords::ClientPanelOpen88{{0x34,0x12}};
        const std::array panel88_only{panel88};
        const auto panel88_reply=service.handle(*session,panel88_only);
        require(panel88_reply && panel88_reply->empty() && movements==0 && battles==0,
                "Standalone native88 changed gameplay or invented a response");
        const std::array panel88_and_move{panel88,move};
        require(!service.handle(*session,panel88_and_move) && movements==0,
                "Native88 mixed with movement accepted");
        const Record options=RecoveredWorldRecords::ClientOptionsNotification{{0xff,0xff}};
        const std::array options_only{options};
        const auto options_reply=service.handle(*session,options_only);
        require(options_reply && options_reply->empty() && movements==0 && battles==0,
                "Native1D changed gameplay or invented an S2C1D reply");
        const std::array options_and_move{options,move};
        require(!service.handle(*session,options_and_move) && movements==0,"Native1D mixed mutation admitted");
        const Record pose=RecoveredWorldRecords::ClientPoseNotification{{0,0xf7,0xa5}};
        const std::array pose_only{pose};
        const auto pose_reply=service.handle(*session,pose_only);
        require(pose_reply && pose_reply->empty() && movements==0 && battles==0,
                "Native66 notification invoked gameplay or fabricated reply");
        for(unsigned mode=1;mode<=3;++mode) {
            const Record pose_mode=RecoveredWorldRecords::ClientPoseNotification{{0,static_cast<std::uint8_t>((mode<<3)|5),0}};
            const std::array pose_mode_only{pose_mode};
            const auto pose_mode_reply=service.handle(*session,pose_mode_only);
            const auto logical=pose_mode_reply ? RecoveredWorldFrame::decode(*pose_mode_reply) : std::nullopt;
            require(logical && *logical==std::vector<std::uint8_t>{0x77,9,0,0,static_cast<std::uint8_t>((mode<<3)|5),0,0} && movements==0 && battles==0,
                "Owned native pose did not produce exact77 or invoked gameplay");
        }
        require(!RecoveredCharacterPose::synchronize(65536,{0,8,0}) &&
                !RecoveredCharacterPose::synchronize(0,{0,8,0}) &&
                !RecoveredCharacterPose::synchronize(session->character_id,{1,8,0}) &&
                !RecoveredCharacterPose::synchronize(session->character_id,{0,32,0}),
                "Pose admitted invalid identity or unqualified pose producer bytes");
        require(RecoveredCharacterPose::synchronize(session->character_id,{0,8,0xff})==
                RecoveredCharacterPose::synchronize(session->character_id,{0,8,0}),
                "Unwritten native66 tail changed pose semantics");
        const std::array pose_and_move{pose,move};
        require(!service.handle(*session,pose_and_move) && movements==0,"Native66 mixed with gameplay");
        session->set_state(SessionState::InBattle);
        require(!service.handle(*session,pose_only),"Battle accepted unqualified66 pose notification");
        const std::array pose_mode_only{Record{RecoveredWorldRecords::ClientPoseNotification{{0,8,0}}}};
        require(!service.handle(*session,pose_mode_only),"Battle accepted native character pose without authority");
        require(!service.handle(*session,control_only),"Battle accepted client 1F control");
        require(!service.handle(*session,control6d_only),"Battle accepted client 6D control");
        require(!service.handle(*session,opaque74_only),"Battle accepted unqualified client74");
        require(!service.handle(*session,panel88_only),"Battle accepted unqualified client88");
        require(!service.handle(*session,options_only),"Battle accepted unqualified client1D");
        session->set_state(SessionState::CharacterSelected);
        require(!service.handle(*session,pose_mode_only),"Premature character selection accepted native world pose");
        require(service.handle(*session,control_only).has_value(),
                "Post-initializer client 1F control rejected");
        require(!service.handle(*session,control6d_only),"Premature client 6D control accepted");
        require(!service.handle(*session,opaque74_only),"Premature client74 accepted");
        require(!service.handle(*session,panel88_only),"Premature client88 accepted");
        require(!service.handle(*session,options_only),"Premature client1D accepted");
        session->set_state(SessionState::InWorld);
        const std::array diagnostic_mixed{diagnostic,move,tick};
        const auto gameplay_only=RecoveredWorldRecords::without_client_diagnostics(diagnostic_mixed);
        unsigned diagnostic_moves=0;
        RecoveredWorldService diagnostic_route(
            [&](Session& actual,std::span<const RecoveredMovement::Request> requests) {
                require(&actual==session.get() && requests.size()==1 && requests[0].x==18 &&
                    requests[0].y==12,"Diagnostic filtering changed movement fields");
                ++diagnostic_moves;return std::vector<std::uint8_t>{1};
            });
        require(gameplay_only.size()==2 && diagnostic_route.handle(*session,gameplay_only).has_value() &&
                diagnostic_moves==1 && movements==0 && battles==0,
                "Mixed native client diagnostic blocked valid movement");
        const auto heartbeat_reply=service.handle(*session,heartbeat);
        require(heartbeat_reply && heartbeat_reply->empty(),"Heartbeat response invented");
        const std::array good{move,tick,Record{RecoveredMovement::Request{19,12,2,1}}};
        require(service.handle(*session,good).has_value() && movements==1,"World movement not routed");
        const std::array mixed{move,attack};
        require(!service.handle(*session,mixed) && movements==1 && battles==0,"Mixed batch committed a prefix");
        const std::array unsupported{move,Record{RecoveredQuestClose::Request{}}};
        require(!service.handle(*session,unsupported) && movements==1,"Unsupported batch committed movement");
        const std::array attacks{attack};
        require(!service.handle(*session,attacks),"World attack accepted");
        session->set_state(SessionState::InBattle);
        require(service.handle(*session,attacks).has_value() && battles==1,"Battle callback not routed");
        require(!service.handle(*session,good) && movements==1,"Movement accepted during battle");
        RecoveredWorldService disabled({});
        require(!disabled.handle(*session,attacks),"Missing battle handler faked success");
        RecoveredSkillCommand::Record skill{};skill.continuation=true;
        const std::array partial{Record{skill}};
        require(!service.handle(*session,partial) && battles==1,"Partial skill sequence committed");
        auto terminal=skill;terminal.continuation=false;
        const std::array complete{Record{skill},Record{terminal}};
        require(service.handle(*session,complete).has_value() && battles==2,"Complete skill batch not routed");
        terminal.context_storage=1;
        const std::array spliced{Record{skill},Record{terminal}};
        require(!service.handle(*session,spliced) && battles==2,"Spliced sequence accepted");
        terminal.context_storage=skill.context_storage;
        std::vector<Record> too_many(15,Record{skill});too_many.back()=Record{terminal};
        require(!service.handle(*session,too_many),"Overlong skill sequence accepted");
        const std::array interrupted{Record{skill},tick,Record{terminal}};
        require(!service.handle(*session,interrupted),"Interrupted skill sequence accepted");
        const std::array opening{Record{RecoveredBattleCommand::Action2Request{}},
                                 Record{RecoveredBattleCommand::ControlRequest{}}};
        require(service.handle(*session,opening).has_value() && battles==3,"Action2 batch not routed to battle policy");
        require(!disabled.handle(*session,opening),"Action2 without handler faked success");
        session->set_state(SessionState::InWorld);
        require(!service.handle(*session,opening) && battles==3,"Action2 admitted outside battle");
        session->set_state(SessionState::InBattle);
        session->character_id=0;
        require(!service.handle(*session,heartbeat),"Missing character accepted");
        session->character_id=9;session->account_id=0;
        require(!service.handle(*session,heartbeat),"Missing account accepted");
        session->account_id=7;session->set_state(SessionState::Disconnected);
        require(!service.handle(*session,heartbeat),"Disconnected session accepted");
        session->set_state(SessionState::InWorld);
        require(!service.handle(*session,std::span<const Record>{}),"Empty batch accepted");
        std::vector<Record> oversized(8193,tick);
        require(!service.handle(*session,oversized),"Oversized batch accepted");
        session=std::make_shared<Session>(asio::ip::tcp::socket(io),io.get_executor(),2,false,
            Session::PacketHandler{},Session::DisconnectHandler{});
        session->account_id=7;session->character_id=9;session->set_state(SessionState::InWorld);
        unsigned quests=0;
        bool allow=false;
        RecoveredWorldService with_quest({}, {}, {},
            [&](Session& actual,const RecoveredWorldService::QuestRequest& request)
                ->std::optional<std::vector<std::uint8_t>> {
                require(&actual==session.get(),"Quest session changed");
                if(const auto* action=std::get_if<RecoveredQuestAction::Request>(&request))
                    require(action->request_word==0x8123 && action->reply_word==0x4567 &&
                            action->context_byte==0xab && action->opaque_tail==0xcd,"Quest action fields changed");
                else if(const auto* close=std::get_if<RecoveredQuestClose::Request>(&request)) {
                    require(close->source_low_word==0x1234 && close->this_high_word==0xbeef,"Quest close fields changed");
                } else {
                    const auto& daily=std::get<RecoveredDailyQuestRequest::Request>(request);
                    if(const auto* selection=std::get_if<RecoveredDailyQuestRequest::Selection>(&daily))
                        require(*selection==RecoveredDailyQuestRequest::Selection{0,0,0xff,4992,1,0xa5},"Daily selection fields changed");
                    else require(std::holds_alternative<RecoveredDailyQuestRequest::Auxiliary>(daily),"Daily mode changed");
                }
                ++quests;
                if(!allow) return std::nullopt;
                return std::vector<std::uint8_t>{};
            });
        const auto action_records=RecoveredWorldRecords::parse_frame(RecoveredWorldFrame::encode(
            RecoveredQuestAction::encode({0x8123,0x4567,0xab,0xcd}))).value();
        const auto close_records=RecoveredWorldRecords::parse_frame(RecoveredWorldFrame::encode(
            RecoveredQuestClose::encode({0x1234,0xbeef}))).value();
        const auto daily_records=RecoveredWorldRecords::parse_frame(RecoveredWorldFrame::encode(
            *RecoveredDailyQuestRequest::encode(RecoveredDailyQuestRequest::Selection{0,0,0xff,4992,1,0xa5}))).value();
        const auto auxiliary_records=RecoveredWorldRecords::parse_frame(RecoveredWorldFrame::encode(
            RecoveredDailyQuestRequest::encode(RecoveredDailyQuestRequest::Auxiliary{}))).value();
        for(const auto& request:{action_records,close_records,daily_records,auxiliary_records}) {
            require(!service.handle(*session,request),"Quest enabled without service");
            require(!with_quest.handle(*session,request),"Quest policy denial ignored");
            allow=true;
            const auto result=with_quest.handle(*session,request);
            require(result && result->empty(),"Quest callback response changed");
            allow=false;
            const auto before=quests;
            for(const auto state:{SessionState::CharacterSelected,SessionState::InBattle}) {
                session->set_state(state);
                require(!with_quest.handle(*session,request) && quests==before,"Quest ran outside world");
            }
            session->set_state(SessionState::InWorld);
            session->account_id=0;
            require(!with_quest.handle(*session,request) && quests==before,"Anonymous quest routed");
            session->account_id=7;session->character_id=0;
            require(!with_quest.handle(*session,request) && quests==before,"Unowned quest routed");
            session->character_id=9;
            for(const Record other:{tick,move,attack,item,action_records[0],close_records[0]}) {
                const std::array forward{request[0],other},reverse{other,request[0]};
                require(!with_quest.handle(*session,forward) && !with_quest.handle(*session,reverse) &&
                        quests==before,"Mixed quest committed a prefix");
            }
        }
        require(quests==8,"Unexpected quest callback count");
        session->set_state(SessionState::Disconnected);
        require(!with_quest.handle(*session,action_records) && !with_quest.handle(*session,close_records) &&
                !with_quest.handle(*session,daily_records) && !with_quest.handle(*session,auxiliary_records) &&
                quests==8,"Disconnected quest routed");
        teleport_routing();
        inventory_move_routing();
        std::cout << "Recovered world service routing checks passed\n";
    } catch(const std::exception& error) { std::cerr<<error.what()<<'\n';return 1; }
}
