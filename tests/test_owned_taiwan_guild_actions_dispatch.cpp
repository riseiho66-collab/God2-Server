#include "game/OwnedTaiwanGuildActionsDispatch.h"
#include "protocol/RecoveredCharacterBootstrap.h"
#include "protocol/RecoveredCharacterCreateResult.h"
#include "protocol/RecoveredPostSeed.h"
#include "protocol/RecoveredSeedExchange.h"
#include <algorithm>
#include <array>
#include <chrono>
#include <stdexcept>
#include <string_view>
#include <thread>

namespace {
using namespace god2;
using Dispatch=OwnedTaiwanGuildActionsDispatch;
using Binding=Dispatch::Binding;
using Record=SharedTaiwanWorldRecordSource::Record;
using Reply=SharedTaiwanWorldRecordSource::Reply;
using Bytes=std::vector<std::uint8_t>;
void require(bool value,const char* message){if(!value)throw std::runtime_error(message);}
template<class F> bool refuses(F&& call){try{call();}catch(const std::exception&){return true;}return false;}
// DB-free real Session handshake, adapted from test_world_reply_push_capture.
// The public synthetic lifecycle supplies admission; native ready itself is
// obtained through seed/login/select/2A/tail, never by private-state access.
// These future tests establish callback custody, not native guild permission.
struct Peer {
    static constexpr std::uint64_t account=0x100000007ULL,character=0x200001234ULL;
    static constexpr std::uint16_t actor=0x1234;
    asio::io_context io;
    asio::ip::tcp::acceptor acceptor{io,{asio::ip::address_v4::loopback(),0}};
    asio::ip::tcp::socket socket{io};
    std::shared_ptr<Session> session;
    const RecoveredWorldEntry::Frame entry=RecoveredWorldEntry::wire(actor);
    unsigned ready_calls=0;
    Peer(){
        socket.connect(acceptor.local_endpoint());auto accepted=acceptor.accept();
        Session::RecoveredCharacterHandlers h;
        h.list=[](std::uint64_t){return std::array<std::uint8_t,78>{};};
        h.create=[](std::uint64_t,const RecoveredCharacterCreate&)->std::uint64_t{throw std::runtime_error("No fixture creation");};
        h.select_created=[](std::uint64_t,std::uint64_t,std::uint8_t)->std::uint64_t{throw std::runtime_error("No fixture created selection");};
        h.select_existing=[](std::uint64_t owner,std::uint8_t token){require(owner==account&&token==0,"Guild fixture full64 selection");return character;};
        h.world_entry=[this](std::uint64_t,std::uint64_t owner,std::uint64_t selected){require(owner==account&&selected==character,"Guild fixture exact entry");return entry;};
        h.world_ready=[this](Session& actual){require(actual.account_id==account&&actual.character_id==character,"Guild fixture full64 readiness");++ready_calls;};
        h.world_records=[](Session&,auto)->std::optional<Bytes>{throw std::runtime_error("Fixture does not route world actions");};
        auto lifecycle=std::make_shared<Session::CommonWorldLifecycle>();
        lifecycle->prepared=[this](Session& actual,const auto& frame){return actual.account_id==account&&actual.character_id==character&&frame==entry;};
        lifecycle->prepared_actor=[this](Session&,const auto& frame)->std::optional<std::uint16_t>{return frame==entry?std::optional<std::uint16_t>{actor}:std::nullopt;};
        lifecycle->ready_async=[](Session& actual,auto done){
            actual.set_state(SessionState::InWorld);actual.bind_common_world_delivery_identity(account,character,11);
            actual.bind_world_delivery_identity({account,character,21,actual.battle_generation()});done(true);
        };
        lifecycle->cancel=[](Session&){};h.common_world_lifecycle=std::move(lifecycle);
        session=std::make_shared<Session>(std::move(accepted),io.get_executor(),0x300000002ULL,false,
            Session::PacketHandler{},Session::DisconnectHandler{},ProtocolMode::God2CharacterConnection,
            [](const RecoveredC2S0002::Parsed& request){require(request.logical[0]==0,"Guild fixture login opcode");return account;},std::move(h));
        socket.non_blocking(true);session->start();
    }
    ~Peer(){asio::error_code ignored;socket.close(ignored);session->close();io.restart();io.run_for(std::chrono::milliseconds(20));}
    void pump(){io.restart();io.run_for(std::chrono::milliseconds(5));}
    void send(std::span<const std::uint8_t> bytes){socket.non_blocking(false);asio::write(socket,asio::buffer(bytes.data(),bytes.size()));socket.non_blocking(true);}
    void expect(std::span<const std::uint8_t> expected){
        Bytes actual(expected.size());std::size_t at=0;const auto deadline=std::chrono::steady_clock::now()+std::chrono::seconds(2);
        while(at<actual.size()&&std::chrono::steady_clock::now()<deadline){
            pump();asio::error_code error;at+=socket.read_some(asio::buffer(actual.data()+at,actual.size()-at),error);
            require(!error||error==asio::error::would_block||error==asio::error::try_again,"Guild fixture transport closed during entry");
        }
        require(at==actual.size()&&std::equal(actual.begin(),actual.end(),expected.begin()),"Guild fixture entry wire changed");
    }
    void ready(){
        expect(RecoveredSeedExchange::hello());send(RecoveredSeedExchange::response);expect(RecoveredPostSeed::frame(0xf6));
        RecoveredC2S0002::Payload credentials{};credentials[167]=0xc8;send(RecoveredC2S0002::encode(credentials));expect(RecoveredCharacterBootstrap::candidate());
        std::array<std::uint8_t,38> selected{};selected[0]=0x1a;selected[34]=4;send(RecoveredWorldFrame::encode(selected));
        expect(RecoveredCharacterCreateResult::committed_success());expect(entry);
        send(RecoveredWorldFrame::encode(std::array<std::uint8_t,9>{0x1f,0,0x23,0,0x1c,static_cast<std::uint8_t>(actor),static_cast<std::uint8_t>(actor>>8),1,0}));
        for(unsigned i=0;i<10;++i){pump();std::array<std::uint8_t,128> bytes{};asio::error_code error;const auto n=socket.read_some(asio::buffer(bytes),error);
            require(!n&&(error==asio::error::would_block||error==asio::error::try_again),"Guild fixture leaked unrelated ready output");}
        require(ready_calls==1&&session->recovered_world_ready()&&session->state()==SessionState::InWorld&&
            session->account_id==account&&session->character_id==character,"Guild holder fixture must traverse actual native ready tail");
    }
};
struct SourceBatch final:Binding::Batch {};
struct Fixture {
    Peer peer;
    std::shared_ptr<Dispatch> owner=Dispatch::create();
    Binding binding=owner->binding();
    std::array<Record,3> records{RecoveredGuildRoster::PanelReady{},RecoveredWorldRecords::Tick{},RecoveredGuildLeave::Request{7}};
    std::array<std::size_t,2> indices{0,2};
    std::shared_ptr<SourceBatch> inner;
    std::vector<Binding::Capture> issued;
    unsigned selectors=0,captures=0,invalidations=0,releases=0,accepted=0,failed=0;
    std::vector<std::pair<std::size_t,std::size_t>> executed;
    std::function<void()> on_handles,on_capture,on_dispatch,on_invalidate,on_release;
    std::function<void(bool)> on_finish;
    Fixture(){peer.ready();}
    ~Fixture(){if(owner)owner->stop();}
    Binding source(){
        Binding source;
        source.handles=[this](Session& session,const Record& record){require(&session==peer.session.get(),"Selector receives original Session");++selectors;if(on_handles)on_handles();return !std::holds_alternative<RecoveredWorldRecords::Tick>(record);};
        source.capture=[this](Session& session,std::span<const Record> full,std::span<const std::size_t> selected)->Binding::Capture{
            require(&session==peer.session.get()&&full.data()==records.data()&&full.size()==records.size(),"Capture receives full original batch, never selected copies");
            require(selected.size()==2&&selected[0]==0&&selected[1]==2&&std::get<RecoveredGuildLeave::Request>(full[2]).slot==7,"Capture retains original selected index order and request");
            inner=std::make_shared<SourceBatch>();issued.push_back(inner);++captures;if(on_capture)on_capture();return inner;
        };
        source.dispatch=[this](Session& session,const Binding::Capture& batch,std::size_t index,std::size_t offset)->std::optional<Reply>{
            require(&session==peer.session.get()&&batch==inner,"Private wrapper unwraps only exact source capture");executed.emplace_back(index,offset);if(on_dispatch)on_dispatch();return Reply::no_reply();
        };
        source.finish_batch=[this](Session& session,const Binding::Capture& batch,bool good){
            require(&session==peer.session.get()&&std::find(issued.begin(),issued.end(),batch)!=issued.end(),"Completion returns original issued source batch and Session");good?++accepted:++failed;if(on_finish)on_finish(good);
        };
        source.release=[this](Session& session){require(&session==peer.session.get(),"Release retains exact Session");++releases;if(on_release)on_release();};
        source.invalidate_active=[this]{++invalidations;if(on_invalidate)on_invalidate();};return source;
    }
    void install(){owner->install(source());}
    Binding::Capture capture(){return binding.capture(*peer.session,records,indices);}
    void complete(const Binding::Capture& batch){
        require(binding.dispatch(*peer.session,batch,0,17).has_value()&&binding.dispatch(*peer.session,batch,2,41).has_value(),"Original selected records dispatch in order");
        binding.finish_batch(*peer.session,batch,true);
    }
};
void installation_original_order_and_successor(){
    Fixture f;require(refuses([&]{(void)f.capture();}),"Uninstalled holder has no capture authority");
    require(refuses([&]{f.owner->install({});}),"Incomplete action source cannot install");f.install();
    require(refuses([&]{f.owner->install(f.source());}),"Complete action source installs only once");
    for(const auto& record:f.records)(void)f.binding.handles(*f.peer.session,record);
    require(f.selectors==3&&f.captures==0,"Classification alone never captures or executes gameplay");
    const auto old=f.capture();require(old!=f.inner&&f.captures==1,"Holder returns private wrapper around one source capture");f.complete(old);
    f.binding.finish_batch(*f.peer.session,old,true);
    require(f.executed==std::vector<std::pair<std::size_t,std::size_t>>{{0,17},{2,41}}&&f.accepted==1&&f.failed==0,"Original indices and caller output offsets reach source unchanged");
    const auto next=f.capture();const auto before=f.invalidations;
    require(refuses([&]{(void)f.binding.dispatch(*f.peer.session,old,0,17);})&&f.invalidations==before,"Stale wrapper cannot invalidate active successor");
    f.complete(next);require(f.captures==2&&f.accepted==2&&f.executed.size()==4,"Independent successor remains executable once");
}
void malformed_selection_and_consumed_indices(){
    Fixture f;f.install();
    for(const auto& invalid:std::array<std::array<std::size_t,2>,3>{{{{0,0}},{{2,0}},{{0,3}}}})
        require(refuses([&]{(void)f.binding.capture(*f.peer.session,f.records,invalid);}),"Duplicate descending or out-of-range indices refuse before source capture");
    require(refuses([&]{(void)f.binding.capture(*f.peer.session,f.records,{});})&&
        refuses([&]{(void)f.binding.capture(*f.peer.session,{},f.indices);})&&f.captures==0,"Empty selection and input are not fake successful batches");
    auto batch=f.capture();require(refuses([&]{(void)f.binding.dispatch(*f.peer.session,batch,2,0);})&&f.executed.empty(),"Later selected record cannot execute ahead of original first record");
    f.binding.finish_batch(*f.peer.session,batch,false);
    batch=f.capture();require(f.binding.dispatch(*f.peer.session,batch,0,0).has_value(),"First selected index executes once");
    require(refuses([&]{(void)f.binding.dispatch(*f.peer.session,batch,0,0);})&&f.executed.size()==1,"Consumed original index cannot replay callback");
    f.binding.finish_batch(*f.peer.session,batch,false);
    batch=f.capture();require(refuses([&]{f.binding.finish_batch(*f.peer.session,batch,true);}),"Handler acceptance cannot skip selected records");
    require(f.accepted==0&&f.failed==3,"Invalid sequences finish as explicit handler refusals");
}
void exact_pointer_and_full64_lifecycle(){
    for(unsigned mode=0;mode<3;++mode){
        Fixture f;f.install();const auto batch=f.capture();
        auto impostor=std::make_shared<Session>(asio::ip::tcp::socket(f.peer.io),f.peer.io.get_executor(),f.peer.session->id(),false,Session::PacketHandler{},Session::DisconnectHandler{});
        impostor->account_id=Peer::account;impostor->character_id=Peer::character;impostor->set_state(SessionState::InWorld);
        require(refuses([&]{(void)f.binding.dispatch(*impostor,batch,0,0);})&&refuses([&]{f.binding.release(*impostor);})&&f.invalidations==0,"Same scalar tuple on another pointer cannot consume or cancel actual batch");
        require(f.binding.dispatch(*f.peer.session,batch,0,0).has_value(),"Original Session remains current after foreign pointer attempts");
        if(mode==0)f.peer.session->account_id+=0x100000000ULL;
        if(mode==1)f.peer.session->character_id+=0x100000000ULL;
        if(mode==2){f.peer.session->set_state(SessionState::InBattle);f.peer.session->set_state(SessionState::InWorld);}
        require(refuses([&]{(void)f.binding.dispatch(*f.peer.session,batch,2,0);})&&f.executed.size()==1,"Full64 account/character and out-and-back battle generation remain exact");
        f.binding.finish_batch(*f.peer.session,batch,false);require(f.failed==1,"Changed lifecycle settles original source capture as refused");
    }
}
void reentry_capture_dispatch_and_failed_end(){
    {
        Fixture f;f.install();bool nested=false,synchronous=false;
        f.on_capture=[&]{nested=refuses([&]{(void)f.capture();});synchronous=f.invalidations>0;};
        require(refuses([&]{(void)f.capture();})&&nested&&synchronous&&f.failed==1,"Caught capture reentry cancels before outer callback returns and refuses returned source batch");
        f.on_capture={};const auto next=f.capture();f.complete(next);
    }
    {
        Fixture f;f.install();const auto batch=f.capture();bool nested=false,synchronous=false;
        f.on_dispatch=[&]{nested=refuses([&]{(void)f.binding.dispatch(*f.peer.session,batch,2,0);});synchronous=f.invalidations>0;};
        require(refuses([&]{(void)f.binding.dispatch(*f.peer.session,batch,0,0);})&&nested&&synchronous&&f.executed.size()==1,"Caught nested dispatch cannot replay or publish original result");
        f.binding.finish_batch(*f.peer.session,batch,false);
    }
    {
        Fixture f;f.install();const auto batch=f.capture();
        f.on_finish=[](bool accepted){if(accepted)throw std::runtime_error("Expected finish failure");};
        (void)f.binding.dispatch(*f.peer.session,batch,0,0);(void)f.binding.dispatch(*f.peer.session,batch,2,0);
        bool original=false;try{f.binding.finish_batch(*f.peer.session,batch,true);}catch(const std::runtime_error& error){original=std::string_view(error.what())=="Expected finish failure";}
        require(original&&f.accepted==1&&f.failed==1&&f.invalidations>0,"End failure preserves original exception and synchronously cancels source batch");
        f.on_finish={};const auto next=f.capture();f.complete(next);
    }
}
void stop_release_and_weak_affinity(){
    {
        Fixture f;f.install();const auto batch=f.capture();f.binding.release(*f.peer.session);
        require(f.releases==1&&f.failed==1&&f.invalidations>0,"Actual release invalidates and refuses source capture before releasing Session");
        require(refuses([&]{(void)f.binding.dispatch(*f.peer.session,batch,0,0);})&&f.executed.empty(),"Released capture cannot execute");
        const auto next=f.capture();f.on_dispatch=[&]{f.owner->stop();};
        require(refuses([&]{(void)f.binding.dispatch(*f.peer.session,next,0,0);})&&f.failed==2,"Stop during actual callback refuses copied continuation");
        require(refuses([&]{(void)f.capture();}),"Stopped source cannot regain capture authority");
    }
    Fixture f;
    struct Observation {std::thread::id game=std::this_thread::get_id();bool destroyed=false,wrong=false;};
    struct Affine {std::shared_ptr<Observation> seen;explicit Affine(std::shared_ptr<Observation> value):seen(std::move(value)){}~Affine(){seen->destroyed=true;seen->wrong=std::this_thread::get_id()!=seen->game;}};
    const auto seen=std::make_shared<Observation>();auto affine=std::make_shared<Affine>(seen);std::weak_ptr<Affine> weak=affine;
    auto source=f.source();source.handles=[affine](Session&,const Record&){return true;};f.owner->install(std::move(source));source={};affine.reset();
    bool handles=false,capture=false,release=false,invalidate=false;
    std::thread worker([&]{handles=refuses([&]{(void)f.binding.handles(*f.peer.session,f.records[0]);});capture=refuses([&]{(void)f.capture();});release=refuses([&]{f.binding.release(*f.peer.session);});invalidate=refuses([&]{f.binding.invalidate_active();});});worker.join();
    require(handles&&capture&&release&&invalidate&&!seen->destroyed&&!weak.expired(),"Wrong-thread weak facades refuse before acquiring affine source captures");
    f.owner->stop();require(seen->destroyed&&!seen->wrong&&weak.expired(),"GAME stop releases callback capture while weak facades survive");
    f.owner.reset();f.binding.release(*f.peer.session);f.binding.invalidate_active();
    require(refuses([&]{(void)f.capture();}),"Expired weak capture cannot fabricate a batch");
    bool expired_foreign=false;std::thread expired([&]{expired_foreign=refuses([&]{f.binding.invalidate_active();});});expired.join();
    require(expired_foreign,"Expired facade still checks GAME before weak lock");
}
}
void test_owned_taiwan_guild_actions_dispatch(){installation_original_order_and_successor();malformed_selection_and_consumed_indices();exact_pointer_and_full64_lifecycle();reentry_capture_dispatch_and_failed_end();stop_release_and_weak_affinity();}
