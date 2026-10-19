#include "game/TaiwanNativeHmdBundleSource.h"
#include "game/TaiwanNativeHmdPreparedBundle.h"
#include "db/SqliteMigrationManager.h"
#include "db/SqliteRecoveredCharacterRepository.h"
#include "db/SqliteSupport.h"
#include "shared/world/SharedActorVisibility.h"
#include "protocol/RecoveredSeedExchange.h"
#include "protocol/RecoveredPostSeed.h"
#include "protocol/RecoveredCharacterBootstrap.h"
#include "protocol/RecoveredCharacterCreateResult.h"
#include "protocol/RecoveredWorldStateCandidate.h"
#include "protocol/RecoveredWorldEntryView.h"
#include <algorithm>
#include <chrono>
#include <fstream>
#include <stdexcept>
#include <string>
#include <thread>
#include <vector>
#ifdef _WIN32
#ifndef NOMINMAX
#define NOMINMAX
#endif
#include <windows.h>
#include <bcrypt.h>
#endif

namespace {
using namespace god2;
using Bytes=std::vector<std::uint8_t>;
using Bundle=TaiwanNativeHmdBundleSource;
using Scene=SharedTaiwanNativeMovementScene;
void require(bool value,const char* message){if(!value)throw std::runtime_error(message);}
Bytes bytes(std::string_view text){return {text.begin(),text.end()};}
void u32(Bytes& out,std::size_t at,std::uint32_t value){
    require(at+4<=out.size(),"Synthetic DWORD outside fixture");
    for(unsigned i=0;i<4;++i)out[at+i]=static_cast<std::uint8_t>(value>>(8*i));
}
std::string digest(const Bytes& value){
#ifdef _WIN32
    struct Algorithm{BCRYPT_ALG_HANDLE value=nullptr;~Algorithm(){if(value)BCryptCloseAlgorithmProvider(value,0);}} algorithm;
    struct Hash{BCRYPT_HASH_HANDLE value=nullptr;~Hash(){if(value)BCryptDestroyHash(value);}};
    require(BCryptOpenAlgorithmProvider(&algorithm.value,BCRYPT_SHA256_ALGORITHM,nullptr,0)>=0,"Fixture SHA algorithm unavailable");
    DWORD count=0,returned=0;
    require(BCryptGetProperty(algorithm.value,BCRYPT_OBJECT_LENGTH,reinterpret_cast<PUCHAR>(&count),sizeof(count),&returned,0)>=0&&
        returned==sizeof(count)&&count,"Fixture SHA storage unavailable");
    Bytes object(count);Hash hash;
    require(BCryptCreateHash(algorithm.value,&hash.value,object.data(),count,nullptr,0,0)>=0&&
        BCryptHashData(hash.value,const_cast<PUCHAR>(value.data()),static_cast<ULONG>(value.size()),0)>=0,"Fixture SHA update failed");
    std::array<std::uint8_t,32> result{};
    require(BCryptFinishHash(hash.value,result.data(),static_cast<ULONG>(result.size()),0)>=0,"Fixture SHA finish failed");
    constexpr char hex[]="0123456789abcdef";std::string out;
    for(const auto part:result){out+=hex[part>>4];out+=hex[part&15];}return out;
#else
    (void)value;throw std::runtime_error("This fixture requires the actual Windows SHA provider");
#endif
}
void write(const std::filesystem::path& path,const Bytes& value){
    std::filesystem::create_directories(path.parent_path());
    std::ofstream stream(path,std::ios::binary|std::ios::trunc);
    require(bool(stream),"Synthetic source file could not open");
    stream.write(reinterpret_cast<const char*>(value.data()),static_cast<std::streamsize>(value.size()));
    require(bool(stream),"Synthetic source file write failed");
}
struct TemporaryFiles {
    const std::filesystem::path root=std::filesystem::temp_directory_path()/
        ("g2-hmd483-"+std::to_string(std::chrono::steady_clock::now().time_since_epoch().count()));
    TemporaryFiles(){require(std::filesystem::create_directory(root),"Unique synthetic directory unavailable");}
    ~TemporaryFiles(){std::error_code ignored;std::filesystem::remove_all(root,ignored);}
};
// Entirely synthetic CAN, retaining opaque bytes past each terminating NUL.
Bytes can(const std::vector<std::string>& names,const std::vector<std::uint16_t>& indices,std::uint8_t tag=7){
    Bytes result(16+64*names.size()+2*indices.size(),0);
    const auto header=bytes("CAN v1.0");std::copy(header.begin(),header.end(),result.begin());
    u32(result,8,static_cast<std::uint32_t>(names.size()));
    for(std::size_t i=0;i<names.size();++i){
        require(!names[i].empty()&&names[i].size()<62,"Synthetic CAN name too long");
        const auto at=12+64*i;result[at]=tag;
        std::copy(names[i].begin(),names[i].end(),result.begin()+at+1);result[at+63]=0xa5;
    }
    const auto count_at=12+64*names.size();u32(result,count_at,static_cast<std::uint32_t>(indices.size()));
    for(std::size_t i=0;i<indices.size();++i){result[count_at+4+2*i]=static_cast<std::uint8_t>(indices[i]);result[count_at+5+2*i]=static_cast<std::uint8_t>(indices[i]>>8);}
    return result;
}
Bytes hmd(unsigned pass){
    std::string text="HMD v1.6\nROMFILE 1 one.rom\nTileModel 1\ntile 2 8 8 0 0\nModelDat 1\n";
    text+="0 0 0 -1 0 0 -1 0 0 1 0 0 0 0 0 0 0 0 0 0 Pass 8 8 ";
    for(unsigned i=0;i<64;++i)text+=std::to_string(pass)+" ";
    text+="\nModel 1\n0 0 0 0 0 0\n";return bytes(text);
}
Bytes rom(){
    auto result=bytes("IGSROM02");result.resize(12,0);
    const auto end=bytes("FILE_END");result.insert(result.end(),end.begin(),end.end());result.resize(24,0);return result;
}
RecoveredWorldEntry::Frame entry_with_direction_selector(const RecoveredWorldEntry::Frame& wire,std::uint8_t selector){
    auto logical=RecoveredWorldFrame::decode(wire);
    require(logical&&logical->size()==37&&(*logical)[0]==0x2a&&selector<8,"Synthetic entry selector requires full actual 2A");
    (*logical)[5]=static_cast<std::uint8_t>(((*logical)[5]&0xf8u)|selector);
    const auto encoded=RecoveredWorldFrame::encode(*logical);
    RecoveredWorldEntry::Frame result{};require(encoded.size()==result.size(),"Synthetic entry selector changed frame size");
    std::copy(encoded.begin(),encoded.end(),result.begin());return result;
}
void entry_direction_projection(){
    const auto original=RecoveredWorldEntry::wire(41);
    const auto before=RecoveredWorldEntryView::read(original);require(bool(before),"Full original entry unavailable");
    constexpr std::array<std::uint8_t,8> expected{7,0,1,2,3,4,5,6};
    for(std::uint8_t selector=0;selector<8;++selector){
        const auto changed=entry_with_direction_selector(original,selector);
        const auto after=RecoveredWorldEntryView::read(changed);
        require(after&&after->entry_movement_direction()==expected[selector]&&
            (after->logical[5]&0xf8u)==(before->logical[5]&0xf8u),"Native B4 selector did not retain its non-direction bits/projection");
        for(std::size_t at=0;at<before->logical.size();++at)
            require(at==5||after->logical[at]==before->logical[at],"Selector fixture changed unrelated full entry bytes");
    }
}
void complete_can_bounds(){
    TemporaryFiles files;const auto path=files.root/"fixture.can";
    const auto original=can({"zero.hmd","indoor\\one.hmd"},{1,0});
    const auto pin=digest(original);const auto parsed=TaiwanNativeCanAsset::from_bytes(path,original,pin);
    require(parsed&&parsed->bytes()==original&&parsed->files().size()==2&&parsed->scene_indices()==std::vector<std::uint16_t>{1,0},
        "Complete synthetic CAN lost its actual table or opaque tail");
    require(parsed->scene(0)&&parsed->scene(0)->ordinal==1&&parsed->scene(0)->source_offset==76&&
        parsed->scene(0)->tag==7&&parsed->scene(0)->reference==bytes("indoor\\one.hmd")&&
        parsed->scene(0)->raw.back()==0xa5&&!parsed->scene(2),"CAN scene indexed the wrong actual file");
    require(!TaiwanNativeCanAsset::from_bytes("relative.can",original,pin)&&
        !TaiwanNativeCanAsset::from_bytes(path,original,std::string(64,'0')),"CAN accepted missing path/digest qualification");
    auto wrong_header=original;wrong_header[0]='X';
    require(!TaiwanNativeCanAsset::from_bytes(path,wrong_header,digest(wrong_header)),"CAN accepted a wrong complete header");
    for(const std::size_t length:{std::size_t{0},std::size_t{7},std::size_t{11},std::size_t{15}})
        require(!TaiwanNativeCanAsset::from_bytes(path,std::span<const std::uint8_t>(original).first(length),pin),
            "CAN accepted an incomplete header/count prefix");
    auto invalid=original;invalid.back()=0xff;
    require(!TaiwanNativeCanAsset::from_bytes(path,invalid,digest(invalid)),"CAN admitted an out-of-file scene index");
    invalid=original;invalid.push_back(0);
    require(!TaiwanNativeCanAsset::from_bytes(path,invalid,digest(invalid)),"CAN ignored a trailing byte");
    invalid=original;invalid.pop_back();
    require(!TaiwanNativeCanAsset::from_bytes(path,invalid,digest(invalid)),"CAN accepted truncated index table");
    invalid=original;std::fill(invalid.begin()+13,invalid.begin()+76,'X');
    require(!TaiwanNativeCanAsset::from_bytes(path,invalid,digest(invalid)),"CAN accepted a nonterminated record");
    invalid=original;invalid[13]=0;
    require(!TaiwanNativeCanAsset::from_bytes(path,invalid,digest(invalid)),"CAN accepted an empty original reference");
    invalid=original;u32(invalid,8,257);
    require(!TaiwanNativeCanAsset::from_bytes(path,invalid,digest(invalid)),"CAN file-count allocation bound disappeared");
    invalid=original;u32(invalid,140,257);
    require(!TaiwanNativeCanAsset::from_bytes(path,invalid,digest(invalid)),"CAN scene-count allocation bound disappeared");
    std::vector<std::string> maximum_names(256,"x.hmd");std::vector<std::uint16_t> maximum_indices(256,255);
    const auto maximum=can(maximum_names,maximum_indices);
    require(maximum.size()==TaiwanNativeCanAsset::max_bytes&&
        TaiwanNativeCanAsset::from_bytes(path,maximum,digest(maximum)),"Complete maximum CAN was rejected or partially retained");
    invalid=maximum;invalid.push_back(0);
    write(path,invalid);require(!TaiwanNativeCanAsset::load_file(path,digest(invalid)),"CAN file read exceeded its total allocation bound");
    write(path,original);const auto from_file=TaiwanNativeCanAsset::load_file(path,pin);
    require(from_file&&from_file->bytes()==original,"Full original CAN file read changed bytes");
}
// Reused actual Session handshake/lifecycle scaffold; synthetic owner values only.
struct BundleSessionPeer {
    using WorldHandler=std::function<std::optional<std::vector<std::uint8_t>>(
        Session&,std::span<const RecoveredWorldRecords::Record>)>;
    asio::io_context io;
    asio::ip::tcp::acceptor acceptor{io,{asio::ip::address_v4::loopback(),0}};
    asio::ip::tcp::socket peer{io};
    std::shared_ptr<Session> session;
    unsigned ready_calls=0,movement_calls=0,selection_calls=0,world_calls=0;
    bool drain_on_destroy=true; // One source-only regression deliberately drops posted handlers.
    static constexpr std::uint64_t account=7,character=0x1234;
    std::uint64_t selected_character=character;
    RecoveredWorldEntry::Frame world_frame;
    static constexpr std::uint64_t common_generation=11,world_generation=21;
    std::uint64_t common_source_generation=common_generation;

    explicit BundleSessionPeer(bool movement,WorldHandler world={},
        std::uint64_t selected=character,std::uint64_t session_id=2,
        std::optional<std::uint16_t> scene_handle={}):selected_character(selected),
        world_frame(RecoveredWorldEntry::wire(scene_handle?std::uint64_t{*scene_handle}:selected)) {
        peer.connect(acceptor.local_endpoint());
        auto socket=acceptor.accept();
        Session::RecoveredCharacterHandlers handlers;
        handlers.list=[](std::uint64_t) { return std::array<std::uint8_t,78>{}; };
        handlers.create=[this](std::uint64_t owner,const RecoveredCharacterCreate& request) {
            require(owner==account && request.payload[0]=='T',"Create lost account/profile");
            return selected_character;
        };
        handlers.select_existing=[this](std::uint64_t owner,std::uint8_t token) {
            require(owner==account && token==0,"Selection lost account/token");
            ++selection_calls;return selected_character;
        };
        handlers.select_created=[this](std::uint64_t owner,std::uint64_t id,std::uint8_t token) {
            require(owner==account && id==selected_character && token==0,"Created selection lost ownership");
            ++selection_calls;return selected_character;
        };
        handlers.created_slot=[this](std::uint64_t owner,std::uint64_t id) -> std::uint8_t {
            require(owner==account && id==selected_character,"Slot lookup lost committed ownership");
            return 0;
        };
        handlers.world_entry=[this](std::uint64_t,std::uint64_t owner,std::uint64_t id) {
            require(owner==account && id==selected_character,"World entry lost ownership");
            return world_frame;
        };
        if(movement || world) {
            handlers.world_ready=[this](Session& s) {
                require(s.account_id==account && s.character_id==selected_character,"World-ready lost binding");
                ++ready_calls;
            };
        }
        if(movement) {
            handlers.movement=[this](Session& s,std::span<const RecoveredMovement::Request> requests) {
                require(ready_calls==1 && s.character_id==selected_character,"Movement preceded world-ready");
                require(requests.size()==1 && requests[0].x==18 && requests[0].y==14 &&
                        requests[0].sequence==3,"Movement request changed");
                ++movement_calls;
                const auto ack=RecoveredMovement::ack(requests[0].sequence);
                return std::vector<std::uint8_t>(ack.begin(),ack.end());
            };
        }
        if(world) {
            handlers.world_records=[this,world=std::move(world)](
                    Session& s,std::span<const RecoveredWorldRecords::Record> records) {
                require(ready_calls==1 && s.account_id==account && s.character_id==selected_character,
                        "World records preceded authenticated character/world binding");
                ++world_calls;
                return world(s,records);
            };
        }
        if(scene_handle) {
            // Explicit test-only common-world admission still goes through the
            // actual prepared/ready_async hooks and original Session2A Write.
            auto lifecycle=std::make_shared<Session::CommonWorldLifecycle>();
            lifecycle->prepared=[this](Session& s,const auto& frame){
                return s.account_id==account&&s.character_id==selected_character&&frame==world_frame;
            };
            lifecycle->prepared_actor=[this,scene_handle](Session&,const auto& frame)->std::optional<std::uint16_t>{
                return frame==world_frame?scene_handle:std::nullopt;
            };
            lifecycle->ready_async=[this](Session& s,auto complete){
                s.set_state(SessionState::InWorld);
                s.bind_common_world_delivery_identity(account,selected_character,common_source_generation);
                s.bind_world_delivery_identity({account,selected_character,world_generation,s.battle_generation()});
                complete(true);
            };
            lifecycle->cancel=[](Session&){};
            handlers.common_world_lifecycle=std::move(lifecycle);
        }
        session=std::make_shared<Session>(std::move(socket),io.get_executor(),session_id,false,
            Session::PacketHandler{},Session::DisconnectHandler{},ProtocolMode::God2CharacterConnection,
            [](const RecoveredC2S0002::Parsed& request) {
                require(request.logical[0]==0,"Character connection login opcode changed");
                return account;
            },std::move(handlers));
        peer.non_blocking(true);
        session->start();
    }
    ~BundleSessionPeer() {
        asio::error_code ignored;
        peer.close(ignored);
        if(!drain_on_destroy)return;
        session->close();
        io.restart();io.run_for(std::chrono::milliseconds(20));
    }
    void pump() { io.restart();io.run_for(std::chrono::milliseconds(5)); }
    void send(std::span<const std::uint8_t> bytes) {
        // These bounded test frames fit the loopback send buffer.
        peer.non_blocking(false);
        asio::write(peer,asio::buffer(bytes.data(),bytes.size()));
        peer.non_blocking(true);
    }
    void expect(std::span<const std::uint8_t> expected) {
        std::vector<std::uint8_t> actual(expected.size());
        std::size_t received=0;
        const auto deadline=std::chrono::steady_clock::now()+std::chrono::seconds(2);
        while(received<actual.size() && std::chrono::steady_clock::now()<deadline) {
            pump();
            asio::error_code error;
            received+=peer.read_some(asio::buffer(actual.data()+received,actual.size()-received),error);
            require(!error || error==asio::error::would_block || error==asio::error::try_again,
                    "Session closed before expected reply");
        }
        require(received==expected.size() && std::equal(actual.begin(),actual.end(),expected.begin()),
                "Recovered session deterministic reply changed");
    }
    void silent() {
        // Pump both executors before checking: queued writes must get a chance to run.
        for(unsigned i=0;i<10;++i) {
            pump();
            std::array<std::uint8_t,256> bytes{};
            asio::error_code error;
            const auto count=peer.read_some(asio::buffer(bytes),error);
            require(count==0 && (error==asio::error::would_block || error==asio::error::try_again),
                    "Recovered session injected unsolicited bytes or closed");
        }
    }
    void closed() {
        const auto deadline=std::chrono::steady_clock::now()+std::chrono::seconds(2);
        while(session->state()!=SessionState::Disconnected && std::chrono::steady_clock::now()<deadline) pump();
        require(session->state()==SessionState::Disconnected,"Invalid/repeated tail did not fail closed");
        std::array<std::uint8_t,256> bytes{};
        asio::error_code error;
        const auto count=peer.read_some(asio::buffer(bytes),error);
        require(count==0 && (error==asio::error::eof || error==asio::error::connection_reset),
                "Rejected tail emitted unsolicited bytes");
    }
    void authenticate(bool created) {
        expect(RecoveredSeedExchange::hello());
        send(RecoveredSeedExchange::response);
        expect(RecoveredPostSeed::frame(0xf6));
        RecoveredC2S0002::Payload credentials{};credentials[167]=0xc8;
        send(RecoveredC2S0002::encode(credentials));
        expect(RecoveredCharacterBootstrap::candidate());
        require(session->state()==SessionState::Authenticated,"Recovered login disabled");
        if(created) {
            std::array<std::uint8_t,45> request{};
            request[0]=0x1b;request[1]='T';request[41]=4;
            send(RecoveredWorldFrame::encode(request));
            expect(RecoveredCharacterCreateResult::committed_success());
        }
    }
    void select(bool created) {
        authenticate(created);
        std::array<std::uint8_t,38> request{};request[0]=0x1a;request[34]=4;
        auto selection=RecoveredWorldFrame::encode(request);
        if(created) {
            auto prefix=RecoveredWorldFrame::encode(std::array<std::uint8_t,2>{0x18,1});
            prefix.insert(prefix.end(),selection.begin(),selection.end());
            selection=std::move(prefix);
        }
        send(selection);
        expect(RecoveredCharacterCreateResult::committed_success());
        expect(world_frame);
        require(session->state()==SessionState::CharacterSelected && selection_calls==1 &&
                session->account_id==account && session->character_id==selected_character,"Selection binding changed");
        silent();
    }
    static std::vector<std::uint8_t> tail(std::uint16_t id=character) {
        return RecoveredWorldFrame::encode(std::array<std::uint8_t,9>{0x1f,0,0x23,0,0x1c,
            static_cast<std::uint8_t>(id),static_cast<std::uint8_t>(id>>8),1,0});
    }
};

struct CatalogFixture {
    struct Close{void operator()(sqlite3* value)const{sqlite3_close_v2(value);}};
    std::unique_ptr<sqlite3,Close> db;
    std::unique_ptr<SqliteRecoveredCharacterRepository> characters;
    std::unique_ptr<NativeMapCatalog> catalog;
    std::size_t traced_statements=0;
    static int trace(unsigned event,void* context,void*,void*) noexcept{
        if(event==SQLITE_TRACE_STMT)++static_cast<CatalogFixture*>(context)->traced_statements;
        return 0;
    }
    NativeMapSource source{NativeMapCatalog::current_dataset_id,"CUSTOM_TEST_NOT_NATIVE:map-catalog",std::string(64,'a'),
        std::string(64,'b'),"149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763",
        "Map_City_Coordniate","0x59a80","0x59d80",1};
    CatalogFixture(){
        sqlite3* raw=nullptr;require(sqlite3_open(":memory:",&raw)==SQLITE_OK,"Synthetic catalog open failed");db.reset(raw);
        sqlite_detail::execute(raw,"PRAGMA foreign_keys=ON");
        SqliteMigrationManager(raw,default_sqlite_migrations()).migrate();
        sqlite_detail::execute(raw,"INSERT INTO accounts(id,username,password_hash) VALUES(7,'hmd-source-fixture','hash')");
        characters=std::make_unique<SqliteRecoveredCharacterRepository>(raw);catalog=std::make_unique<NativeMapCatalog>(raw);
        sqlite_detail::Statement insert(raw,"INSERT INTO native_data_sources VALUES(?,?,?,?,?,?,?,?,?)");
        insert.bind(1,source.dataset_id);insert.bind(2,source.source_path);insert.bind(3,source.source_sha256);
        insert.bind(4,source.decoded_sha256);insert.bind(5,source.native_image_sha256);insert.bind(6,source.source_section);
        insert.bind(7,source.loader_rva);insert.bind(8,source.lookup_rva);insert.bind(9,source.row_count);insert.done();
        // Literal indexed fields3/4/5 are area1/kind2/scene0; field10 supplies MDT name.
        // All coordinates, classes, filenames and catalog declarations are TEST data.
        const auto row=bytes("0,0,0,1,2,0,0,0,0,0,fix\\base.mdt,0,0,0");
        sqlite_detail::Statement record(raw,"INSERT INTO native_map_catalog VALUES(?,0,1,?,?,1,0,2)");
        record.bind(1,source.dataset_id);record.bind(2,digest(row));record.bind_blob(3,row);record.done();
        require(sqlite3_trace_v2(raw,SQLITE_TRACE_STMT,&trace,this)==SQLITE_OK,"Fixture statement trace unavailable");
        // Positive control keeps zero-SQL assertions from silently using an inert trace.
        const auto before=traced_statements;
        sqlite_detail::Statement probe(raw,"SELECT 1");require(probe.row()&&traced_statements>before,"Fixture trace did not observe SQL");
    }
    ~CatalogFixture(){sqlite3_trace_v2(db.get(),0,nullptr,nullptr);}
};
void hmd_bundle_lifecycle(std::uint16_t selected_scene,unsigned entry_geometry_fault=0,int native_entry_selector=-1){
    TemporaryFiles files;CatalogFixture catalog;
    const auto map=files.root/"Data2"/"map"/"fix";
    const auto selected=selected_scene==0?map/"indoor"/"one.hmd":map/"zero.hmd";
    const auto selected_rom=selected.parent_path()/"one.rom";
    const auto original_can=can({"zero.hmd","indoor\\one.hmd"},{1,0});
    write(map/"base.can",original_can);write(map/"zero.hmd",hmd(0));write(map/"one.rom",rom());
    write(map/"indoor"/"one.hmd",hmd(1));write(map/"indoor"/"one.rom",rom());
    Bundle::Configuration config{catalog.source,files.root,
        {{1,map/"base.can",digest(original_can),7}},{4096,4096,4096,4096,2}};
    std::array<std::uint8_t,40> profile{};profile[0]='A';
    const auto a=catalog.characters->create(BundleSessionPeer::account,profile).id;profile[0]='B';
    const auto b=catalog.characters->create(BundleSessionPeer::account,profile).id;
    const auto pa=catalog.characters->commit_position(BundleSessionPeer::account,a,{},1,selected_scene,1,1);
    const auto pb=catalog.characters->commit_position(BundleSessionPeer::account,b,{},1,selected_scene,1,1);
    auto presence=std::make_shared<SharedWorldPresence>(*catalog.characters);
    const auto no_reply=[](Session&,auto)->std::optional<Bytes>{return Bytes{};};
    BundleSessionPeer first(false,no_reply,a,48301,41),second(false,no_reply,b,48302,42);
    // Fault5 leaves actual2A/prepared_actor/tail coherently41, but the genuine
    // independent reservation issuer uses43. Neither private source is forged.
    const auto reservation_actor=static_cast<std::uint16_t>(entry_geometry_fault==5?43:41);
    const auto la=presence->prepare(first.session->id(),BundleSessionPeer::account,a,reservation_actor,pa);
    const auto lb=presence->prepare(second.session->id(),BundleSessionPeer::account,b,42,pb);
    require(la&&lb&&presence->activate(*la,reservation_actor)&&presence->activate(*lb,42),"Real prepared/ready scene leases unavailable");
    first.common_source_generation=la->generation;second.common_source_generation=lb->generation;
    // The actual Session writes these full bytes. Faults do NOT alter the
    // original ready lease or its durable saved position to make a false match.
    // Fault6 retains exact actor/geometry but issues kind1, whose native loader
    // branch is not HMD; the generic entry view remains valid and unmodified.
    require(entry_geometry_fault<=6,"Unknown entry geometry fixture fault");
    first.world_frame=RecoveredWorldEntry::wire(41,profile,
        static_cast<std::uint16_t>(pa.x+(entry_geometry_fault==1)),
        static_cast<std::uint16_t>(pa.y+(entry_geometry_fault==2)),
        static_cast<std::uint16_t>(pa.area+(entry_geometry_fault==3)),
        static_cast<std::uint16_t>(entry_geometry_fault==4?(pa.scene^1):pa.scene),
        static_cast<std::uint16_t>(entry_geometry_fault==6?1:2));
    second.world_frame=RecoveredWorldEntry::wire(42,profile,pb.x,pb.y,pb.area,pb.scene);
    require(native_entry_selector>=-1&&native_entry_selector<8,"Unknown native entry direction fixture selector");
    const bool initial_only=native_entry_selector>=0;
    const auto expected_direction=static_cast<std::uint8_t>(initial_only?(native_entry_selector+7)%8:2);
    if(initial_only){
        // Actual kind2 CAN dispatch consumes row+1, without testing byte0.
        // This tag7 fixture therefore needs no invented native tag discriminator.
        config.areas[0].expected_hmd_tag.reset();
        first.world_frame=entry_with_direction_selector(first.world_frame,static_cast<std::uint8_t>(native_entry_selector));
        second.world_frame=entry_with_direction_selector(second.world_frame,static_cast<std::uint8_t>(native_entry_selector));
    }
    first.select(false);first.send(BundleSessionPeer::tail(41));first.silent();
    second.select(false);second.send(BundleSessionPeer::tail(42));second.silent();
    bool pose_available=true;
    Bundle::PoseSource pose=[&](Session& session,const Scene::FactoryScope& scope)->std::optional<Bundle::InitialPose>{
        if(!pose_available||session.id()!=scope.lease.session||session.account_id!=scope.lease.account||
           session.character_id!=scope.lease.character)return {};
        return Bundle::InitialPose{scope.saved_position,2,
            [](Session& actual,const Scene::FactoryScope& current,const RecoveredPosition& saved,std::uint8_t direction){
                return actual.id()==current.lease.session&&actual.account_id==current.lease.account&&
                    actual.character_id==current.lease.character&&saved==current.saved_position&&direction==2;
            }};
    };
    if(initial_only)pose=Bundle::initial_entry_pose_source(presence);
    bool absent_pose_refused=false;
    try{(void)Bundle::create(*catalog.catalog,presence,2,config,{});}catch(const std::invalid_argument&){absent_pose_refused=true;}
    require(absent_pose_refused,"Bundle source invented its mandatory pose supplier");
    auto bundle=Bundle::create(*catalog.catalog,presence,2,config,pose);
    const auto supply=bundle->input_source();
    const Scene::FactoryScope sa{*la,pa},sb{*lb,pb};
    const auto original_init=first.session->normal_world_initialization_on_game();
    require(original_init&&original_init->qualified_scene_identity()&&original_init->entry_written()&&original_init->original_entry_battle_phase()&&
        first.session->normal_world_initialization_current_on_game(*original_init),"Actual original 2A INIT not Written/current");
    const auto entry=RecoveredWorldEntryView::read(original_init->entry_frame());
    require(entry&&entry->actor_handle==41,"Actual original 2A actor differs from its real Session prepared actor");
    if(initial_only){
        bool tls_refused=false;
        try{(void)first.session->normal_world_initialization();}catch(const std::logic_error&){tls_refused=true;}
        require(tls_refused,"Readonly game INIT accessor weakened the original world-callback TLS guard");
        bool wrong_thread_observed=false;
        std::thread other([&]{wrong_thread_observed=bool(first.session->normal_world_initialization_on_game());});other.join();
        require(!wrong_thread_observed&&first.session->normal_world_initialization_current_on_game(*original_init),
            "Readonly game INIT accessor exposed custody on another thread or retired the actual owner");
    }
    auto ia=supply(*first.session,sa),ib=supply(*second.session,sb);
    if(entry_geometry_fault) {
        require((entry->kind!=2||entry->actor_handle!=la->actor_handle||entry->area!=la->position.area||entry->scene!=la->position.scene||entry->x!=la->position.x||entry->y!=la->position.y)&&
            !ia&&ib&&ib->prepared_bundle&&presence->retained_ready_current(*la)&&presence->saved_position(*la)==std::optional{pa}&&
            first.session->normal_world_initialization_current_on_game(*original_init)&&!first.session->closing(),
            "Mismatched actual 2A kind/actor/geometry supplied HMD resources, rewrote saved pose or closed a valid real Session");
        bundle->stop();return;
    }
    require(entry->kind==2&&entry->actor_handle==la->actor_handle&&entry->area==la->position.area&&entry->scene==la->position.scene&&entry->x==la->position.x&&entry->y==la->position.y,
        "Positive bundle fixture does not match its original actual 2A/lease");
    require(ia&&ib&&ia->prepared_bundle&&ib->prepared_bundle&&ia->source_lifetime&&ib->source_lifetime,
        "Actual CAN selection did not issue complete prepared scene supplies");
    require(!ia->authority&&!ia->owned_ordinary&&ia->actual_direction==expected_direction&&ia->actual_position==pa,
        "File source invented authority or a default initial pose");
    require(ia->prepared_bundle->matches(*ia)&&ib->prepared_bundle->matches(*ib),"Private prepared source failed its own full identity");
    require(ia->sources.hmd.actual_source().lexically_normal()==selected.lexically_normal()&&
        ia->sources.roms.size()==1&&ia->sources.roms[0].selected.actual_source().lexically_normal()==selected_rom.lexically_normal(),
        "CAN scene index or native ROM prefix selected the wrong original file");
    auto expected_prefix=selected.parent_path().string();std::replace(expected_prefix.begin(),expected_prefix.end(),'/','\\');expected_prefix+='\\';
    require(ia->sources.actual_rom_prefix==bytes(expected_prefix)&&
        ia->sources.roms[0].selected.request().native_prefix==bytes(expected_prefix)&&
        ia->sources.roms[0].selected.request().original_reference==bytes("one.rom"),
        "Native model prefix bytes were normalized, truncated or silently substituted");
    const auto& ga=ia->prepared_bundle->resources();const auto& gb=ib->prepared_bundle->resources();
    require(ga.composed_grid&&gb.composed_grid&&ga.complete()&&gb.complete()&&
        &ga.composed_grid->bytes()==&gb.composed_grid->bytes()&&
        &ga.composed_grid->material()==&gb.composed_grid->material(),
        "Two actual Sessions reparsed/copied the same immutable cached grid");
    const auto current=[&](const Bundle::Input& input,const SharedWorldPresence::Lease& lease){
        const auto& images=input.prepared_bundle->resources();
        const Scene::Scope scope{lease,input.actual_position,input.actual_direction,input.actual_initial_scene_generation};
        const auto before=catalog.traced_statements;
        const auto result=input.current(Scene::Check::Adopt,scope,images,input.sources);
        require(catalog.traced_statements==before,"Held bundle Current entered SQLite instead of retained state");
        return result;
    };
    std::optional<Bundle::InitialPose> held_entry_pose;
    const auto pose_current=[&](Session& actual,const Scene::FactoryScope& scope,const RecoveredPosition& saved,std::uint8_t direction){
        require(held_entry_pose&&held_entry_pose->current,"Actual first-entry pose Current missing");
        const auto before=catalog.traced_statements;
        const auto result=held_entry_pose->current(actual,scope,saved,direction);
        require(catalog.traced_statements==before,"Held first-entry pose Current entered SQLite");return result;
    };
    if(initial_only){
        held_entry_pose=pose(*first.session,sa);
        require(held_entry_pose&&held_entry_pose->position==pa&&held_entry_pose->direction==expected_direction&&
            pose_current(*first.session,sa,pa,expected_direction)&&!pose_current(*second.session,sa,pa,expected_direction)&&
            !pose_current(*first.session,sa,pa,static_cast<std::uint8_t>((expected_direction+1)%8))&&
            !pose(*second.session,sa),"Actual first-entry supplier substituted facing or borrowed another Session");
        auto wrong=pa;++wrong.x;
        require(!pose_current(*first.session,Scene::FactoryScope{*la,wrong},wrong,expected_direction)&&
            !pose(*first.session,Scene::FactoryScope{*la,wrong}),"First-entry supplier accepted a fabricated saved prefix");
    }
    require(current(*ia,*la)&&current(*ib,*lb)&&!current(*ia,*lb)&&!supply(*second.session,sa),
        "Foreign full Session/Lease borrowed a selected scene source");
    auto changed=*ia;changed.sources.actual_rom_prefix.push_back('x');
    require(!changed.prepared_bundle->matches(changed),"Prepared bundle admitted altered native prefix");
    changed=*ia;++changed.actual_initial_scene_generation;
    require(!changed.prepared_bundle->matches(changed),"Prepared bundle admitted a fabricated scene epoch");
    const auto actual_account=first.session->account_id;first.session->account_id^=std::uint64_t{1}<<32;
    require(!current(*ia,*la)&&!supply(*first.session,sa),"Bundle source narrowed full account identity");first.session->account_id=actual_account;
    if(!initial_only){pose_available=false;require(!supply(*first.session,sa),"Absent real initial pose became a zero/default pose");pose_available=true;}

    // File parsing/composition gives no movement authority. Supply the existing
    // explicit CUSTOM-0150 policy only at the actual host's installation seam.
    auto visibility=std::make_shared<shared::SharedActorVisibility>(presence);
    auto rules=std::make_shared<TaiwanMovementRules>(std::filesystem::path(GOD2_SOURCE_DIR)/"scripts/tw/owned_ordinary_movement.lua");
    auto host=SharedTaiwanNativeMovementHost::create(presence,visibility,rules,2);
    auto hosted=*ia;
    hosted.owned_ordinary.emplace(TaiwanNativeSceneResourceOwner::OwnedOrdinary{rules,
        TaiwanMovementRules::OrdinaryPolicy{1,1000,2,1,0,false,true,false}});
    require(host->install(first.session,*la,hosted),"Real host refused the explicit source/CUSTOM-0150 integration");
    require(!host->install(second.session,*lb,hosted)&&!host->install(first.session,*la,hosted)&&current(*ia,*la),
        "Foreign or duplicate token installation revoked the retained actual source");
    require(host->remove(*first.session,*la)&&!ia->source_lifetime->current()&&!current(*ia,*la),
        "Actual host retirement left raw source Current usable");
    auto fresh=supply(*first.session,sa);
    require(fresh&&fresh->source_lifetime!=ia->source_lifetime&&
        fresh->actual_initial_scene_generation!=ia->actual_initial_scene_generation&&current(*fresh,*la),
        "New actual scene supply reused a retired lifetime/epoch");
    const auto stable=fresh;

    auto bad=config;bad.areas[0].expected_can_sha256=std::string(64,'0');
    require(!bundle->publish(bad)&&current(*stable,*la)&&current(*ib,*lb),"Failed CAN publication discarded the previous whole version");
    bad=config;bad.areas[0].expected_hmd_tag=6;
    require(!bundle->publish(bad)&&current(*stable,*la),"Cached HMD tag failure changed the previous whole version");
    bad=config;bad.expected_catalog.source_sha256=std::string(64,'c');
    require(!bundle->publish(bad)&&current(*stable,*la),"Catalog declaration mismatch adopted a new whole version");
    bad=config;bad.limits.rom_encoded=1;
    require(!bundle->publish(bad)&&current(*stable,*la),"Failed encoded resource limit discarded the current version");
    const auto original_row=bytes("0,0,0,1,2,0,0,0,0,0,fix\\base.mdt,0,0,0");
    const auto set_row=[&](const Bytes& raw,std::string sha){
        sqlite_detail::Statement change(catalog.db.get(),"UPDATE native_map_catalog SET raw_record=?,record_sha256=? WHERE area=1 AND scene=0");
        change.bind_blob(1,raw);change.bind(2,sha);change.done();
    };
    set_row(original_row,std::string(64,'0'));
    require(!bundle->publish(config)&&current(*stable,*la),"Catalog raw-byte digest was not checked at publication");
    const auto wrong_selector=bytes("0,0,0,2,2,0,0,0,0,0,fix\\base.mdt,0,0,0");
    set_row(wrong_selector,digest(wrong_selector));
    require(!bundle->publish(config)&&current(*stable,*la),"Raw area field disagreed with typed catalog but was published");
    for(const auto& selectors:{std::string("0,0,0,1,1,0,0,0,0,0,fix\\base.mdt,0,0,0"),
                               std::string("0,0,0,1,2,1,0,0,0,0,fix\\base.mdt,0,0,0")}) {
        const auto row=bytes(selectors);set_row(row,digest(row));
        require(!bundle->publish(config)&&current(*stable,*la),"Raw kind/scene selectors were swapped or trusted independently");
    }
    set_row(original_row,digest(original_row));
    write(selected_rom,bytes("malformed whole ROM"));
    require(!bundle->publish(config)&&current(*stable,*la)&&current(*ib,*lb),"Failed cached ROM rebuild published a partial asset version");
    write(selected_rom,rom());
    require(bundle->publish(config)&&!current(*stable,*la)&&!current(*ib,*lb),"Successful whole-version publication retained old Current");
    auto latest=supply(*first.session,sa);require(latest&&current(*latest,*la),"Published complete version could not supply actual current scene");
    auto latest_other=supply(*second.session,sb);require(latest_other&&current(*latest_other,*lb),"New version could not supply second actual Session");
    // Genuine same-map common position CAS: this tests source lineage, not a
    // native movement permit or walkability rule. The original 2A and lease
    // remain the actual entry pose; only saved position/revision advances.
    const auto moved=presence->commit_owned_step(*la,pa,static_cast<std::uint16_t>(pa.x+1),pa.y);
    require(moved&&moved->revision>pa.revision&&moved->x==pa.x+1&&presence->saved_position(*la)==moved,
        "Actual common position CAS did not advance the durable saved prefix");
    const Scene::FactoryScope moved_scope{*la,*moved};
    auto moved_input=supply(*first.session,moved_scope);
    const auto after_init=first.session->normal_world_initialization_on_game();
    require(after_init&&after_init->same_initialization(*original_init)&&after_init->original_entry_battle_phase()&&
        first.session->normal_world_initialization_current_on_game(*original_init),"Position CAS rewrote original actual INIT lineage");
    if(initial_only){
        // Native initial facing is qualified only for the original saved prefix.
        // A real durable move needs a later genuine pose issuer; never recycle B4.
        require(!moved_input&&!pose(*first.session,moved_scope)&&!pose(*first.session,sa)&&!supply(*first.session,sa),
            "First-entry-only supplier reused original B4 after a real common position CAS");
    }else{
        require(moved_input&&moved_input->actual_position==*moved&&moved_input->actual_direction==2&&
            moved_input->actual_initial_scene_generation!=latest->actual_initial_scene_generation&&
            !current(*latest,*la)&&current(*moved_input,*la)&&!supply(*first.session,sa)&&current(*moved_input,*la),
            "Saved-after pose was compared to original 2A instead of its immutable lease entry pose");
    }
    const auto retained_entry=RecoveredWorldEntryView::read(after_init->entry_frame());
    require(retained_entry&&retained_entry->x==la->position.x&&retained_entry->y==la->position.y&&retained_entry->x!=moved->x,
        "Position advance rewrote or reminted the original entry evidence");
    // A bare phase toggle is NOT a genuine post-battle INIT issuer. Prove it
    // cannot bypass that prerequisite; successful real return refresh is outside
    // this fixture until the actual native return/INIT owner is supplied.
    first.session->set_state(SessionState::InBattle);first.session->set_state(SessionState::InWorld);
    require((!moved_input||!current(*moved_input,*la))&&!current(*latest,*la)&&
        !supply(*first.session,moved_scope)&&current(*latest_other,*lb),
        "Battle transition reused a pre-battle INIT/source or retired another Session");
    if(initial_only){
        require(!pose_current(*first.session,sa,pa,expected_direction),"Held initial facing survived an actual battle phase change");
        // Isolate battle refusal from the first character's already-advanced
        // position: this second Session has never committed a movement step.
        const auto second_pose=pose(*second.session,sb);
        require(second_pose&&second_pose->direction==expected_direction,"Unmoved second Session lost genuine first-entry pose");
        second.session->set_state(SessionState::InBattle);
        const auto before=catalog.traced_statements;
        require(!second_pose->current(*second.session,sb,pb,expected_direction)&&catalog.traced_statements==before,
            "Battle-phase initial pose Current remained usable or entered SQLite");
        require(!pose(*second.session,sb)&&!current(*latest_other,*lb),"Battle Session reused original first-entry supply");
        second.session->set_state(SessionState::InWorld);
        require(!pose(*second.session,sb)&&!supply(*second.session,sb),"Bare battle return fabricated a genuine successor INIT/pose");
        // This deliberately does not forge the private post-battle INIT receipt;
        // successful genuine return refresh is not exercised by this fixture.
    }
    bundle->stop();
    bool stopped_current=false,stopped_read=false;
    try{stopped_current=!current(*latest_other,*lb);}catch(const std::logic_error&){stopped_current=true;}
    try{stopped_read=!supply(*second.session,sb);}catch(const std::logic_error&){stopped_read=true;}
    require(stopped_current&&stopped_read,"Stopped bundle source revived old raw Current or a supply");
}
} // namespace

// Parent registers this named suite; no static initializer runs test code.
void test_taiwan_native_hmd_bundle_source(){
    entry_direction_projection();complete_can_bounds();hmd_bundle_lifecycle(0);hmd_bundle_lifecycle(1);
    for(unsigned fault=1;fault<=6;++fault)hmd_bundle_lifecycle(0,fault);
    // Boundary projections reach the actual Session -> supplier -> bundle ->
    // Host path, including selector0 -> direction7 and selector1 -> direction0.
    hmd_bundle_lifecycle(0,0,0);hmd_bundle_lifecycle(1,0,1);
}
