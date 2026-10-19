#include "protocol/OpcodeDispatcher.h"
#include "net/Session.h"
#include "handlers/RecoveredWorldService.h"
#include "handlers/RecoveredVisibility.h"
#include "handlers/RecoveredPlayerPresence.h"
#include "protocol/DiagnosticRemoteActor.h"
#include "handlers/RecoveredBattleService.h"
#include "scripting/LuaEngine.h"
#include "protocol/RecoveredSeedExchange.h"
#include "protocol/RecoveredTaiwanInventoryItemRecord.h"
#include "protocol/RecoveredPostSeed.h"
#include "protocol/RecoveredCharacterBootstrap.h"
#include "protocol/RecoveredCharacterCreateResult.h"
#include "protocol/RecoveredWorldStateCandidate.h"
#include "protocol/DiagnosticBattleParticipants.h"
#include "db/SqliteMigrationManager.h"
#include "db/SqliteRecoveredCharacterRepository.h"
#include "db/SqliteSupport.h"
#include "handlers/RecoveredOwnedCompanions.h"
#include "game/SharedTaiwanOwnedDeitySkillSource.h"
#include "game/LegacyTaiwanOwnedDeitySelectionRegistry.h"
#include "handlers/OwnedSkillBookLearningService.h"
#include "db/SqliteSkillBookLearningRepository.h"
#include <algorithm>
#include <chrono>
#include <stdexcept>
#include <string>
#include <fstream>
#include <charconv>
#include <optional>
#include <nlohmann/json.hpp>

namespace {
using namespace god2;
void require(bool value,const char* message) { if(!value) throw std::runtime_error(message); }

// Synthetic peer and handlers exercise the real Session socket/state machine.
// Test identities/coordinates are not recovered character attributes.
struct RecoveredSessionPeer {
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

    explicit RecoveredSessionPeer(bool movement,WorldHandler world={},
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
    ~RecoveredSessionPeer() {
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

// Real Session/loopback source regressions, not a test-only receipt factory.
// Synthetic S31 bytes exercise transport custody, not original selection policy.
void recovered_callback_output_transport() {
    using Status=Session::WorldCallbackOutputStatus;
    const auto logical=[](std::uint8_t key){
        RecoveredDeityState::Status::Bytes row{0x31,key,1};
        return std::vector<std::uint8_t>(row.begin(),row.end());
    };
    for(const bool in_world:{false,true})for(const bool final_nonempty:{false,true}){
        std::optional<Session::WorldCallbackOutput> output;
        std::optional<Session::WorldRecordsWrite> old_push;
        std::optional<Session::WorldCallbackSelectionInput> first_input,second_input;
        std::optional<Session::WorldCallbackOutputCursor> before,after_first;
        bool queued=false,pending_inside=false,successor_after_written=false;
        RecoveredSessionPeer other(false,[](Session&,auto)->std::optional<std::vector<std::uint8_t>>{
            return std::vector<std::uint8_t>{};
        },0x2345,47601);
        other.select(false);other.send(RecoveredSessionPeer::tail());other.silent();
        const auto first=logical(101),second=logical(102),third=logical(103),last=logical(104);
        RecoveredSessionPeer peer(false,[&](Session& session,auto records)->std::optional<std::vector<std::uint8_t>>{
            if(output){
                require(records.size()==1&&std::holds_alternative<RecoveredWorldRecords::Tick>(records.front()),
                    "Raw suffix changed after callback output barrier");
                successor_after_written=output->status()==Status::Written&&output->callback_accepted()&&
                    session.world_callback_output_current_on_game(*output)&&
                    !session.callback_output_selection_current(*output,*first_input);
                return std::vector<std::uint8_t>{};
            }
            const auto init=session.normal_world_initialization();require(init.has_value(),"Composite actual INIT missing");
            output=session.capture_world_callback_output(*init);require(output.has_value(),"Composite capture rejected actual callback");
            require(output->selection_keys().size()==2&&output->selection_keys()[0].ordinal==0&&
                output->selection_keys()[1].record_index==1&&output->selection_keys()[0].key==101&&
                output->selection_keys()[1].key==101,"Composite original C67 order/payload changed");
            // Explicit copied-adapter contract. Equal payload still mints two
            // distinct actual original-input occurrences in source order.
            RecoveredDeitySelection::Request copied{101};
            first_input=session.claim_next_callback_selection(*output,copied);
            second_input=session.claim_next_callback_selection(*output,copied);
            require(first_input&&second_input&&!first_input->same_occurrence(*second_input)&&
                first_input->selection_ordinal()==0&&second_input->selection_ordinal()==1&&
                session.callback_output_selection_current(*output,*first_input),"C67 one-use input occurrence claim changed");
            before=session.capture_world_callback_output_cursor(*output);require(before.has_value(),"Composite initial cursor missing");
            session.hold_world_input_until_callback_output_written(*output);
            old_push=session.send_world_records_observed(first);
            after_first=session.capture_world_callback_output_cursor(*output);
            other.session->send_world_records(std::vector<std::uint8_t>{0x73,8,0,0,0});
            session.bind_world_delivery_identity({session.account_id,session.character_id,21,session.battle_generation()});
            session.send_world_records_with_acceptance(second,session.account_id,session.character_id,21,
                session.battle_generation(),[&](bool value){queued=value;});
            const auto recipient=session.capture_normal_world_output(*init);require(recipient.has_value(),"Composite normal output handle missing");
            const auto normal=session.send_normal_world_records(*recipient,third);
            pending_inside=output->status()==Status::Pending&&!output->sealed()&&!output->callback_accepted()&&
                output->components().empty()&&old_push->status()==Session::WorldRecordsWriteStatus::Pending&&
                normal.status()==Session::NormalWorldOutputStatus::Pending;
            return final_nonempty?RecoveredWorldFrame::encode(last):std::vector<std::uint8_t>{};
        },in_world?(std::uint64_t{1}<<32)|RecoveredSessionPeer::character:RecoveredSessionPeer::character,
            47602,in_world?std::optional<std::uint16_t>{0x345}:std::nullopt);
        peer.select(false);peer.send(RecoveredSessionPeer::tail(in_world?0x345:RecoveredSessionPeer::character));peer.silent();
        auto input=RecoveredWorldFrame::encode(std::array<std::uint8_t,4>{0x67,101,0x67,101});
        const auto tick=RecoveredWorldFrame::encode(std::array<std::uint8_t,2>{0x30,0});
        input.insert(input.end(),tick.begin(),tick.end()); // Separate raw frame, not a parsed record replay.
        peer.send(input);
        peer.expect(RecoveredWorldFrame::encode(first));peer.expect(RecoveredWorldFrame::encode(second));
        peer.expect(RecoveredWorldFrame::encode(third));if(final_nonempty)peer.expect(RecoveredWorldFrame::encode(last));
        peer.silent();other.expect(RecoveredWorldFrame::encode(std::array<std::uint8_t,5>{0x73,8,0,0,0}));other.silent();
        require(output&&pending_inside&&queued&&successor_after_written&&peer.world_calls==2&&
            output->status()==Status::Written&&output->sealed()&&output->callback_accepted()&&
            old_push->status()==Session::WorldRecordsWriteStatus::Written,"Composite completed early or lost legacy receipt/raw hold");
        const auto parts=output->components();require(parts.size()==(final_nonempty?4u:3u),"Other peer/empty return became a self Write");
        require(parts[0].kind()==Session::WorldCallbackOutput::Kind::WorldRecords&&
            parts[1].kind()==Session::WorldCallbackOutput::Kind::AcceptedWorldRecords&&
            parts[2].kind()==Session::WorldCallbackOutput::Kind::NormalWorldRecords&&
            parts[0].logical()==first&&parts[1].logical()==second&&parts[2].logical()==third&&
            !parts[0].same_occurrence(parts[1]),"Original self sender order/encoding identity changed");
        for(std::size_t i=0;i<parts.size();++i)require(parts[i].ordinal()==i&&parts[i].status()==Status::Written&&
            parts[i].wire()&&!parts[i].wire()->empty(),"Composite component lacked exact full Write");
        require(after_first&&after_first->first_component_ordinal()==1&&
            !peer.session->callback_output_component_after_cursor(*output,*after_first,parts[0])&&
            peer.session->callback_output_component_after_cursor(*output,*after_first,parts[1])&&
            peer.session->callback_output_component_after_cursor(*output,*before,parts[0]),"Private component frontier borrowed older output");
        require(output->final_return_wire().size()==(final_nonempty?RecoveredWorldFrame::encode(last).size():0),
            "Original final return was recombined with side sends");
        const auto account=peer.session->account_id,character=peer.session->character_id;
        peer.session->account_id^=std::uint64_t{1}<<32;
        require(!peer.session->world_callback_output_current_on_game(*output),"Composite narrowed account");peer.session->account_id=account;
        peer.session->character_id^=std::uint64_t{1}<<32;
        require(!peer.session->world_callback_output_current_on_game(*output),"Composite narrowed character");peer.session->character_id=character;
        require(!other.session->world_callback_output_current_on_game(*output)&&
            !peer.session->capture_world_callback_output_cursor(*output)&&
            !peer.session->claim_next_callback_selection(*output,{101}),"Stale callback/foreign Session reclaimed private input");
    }
    // Public passive Data may be dropped; the real post/Write still owns its
    // whole source. Observation lifetime must not close unchanged output.
    {
        unsigned calls=0;const auto row=logical(101);
        RecoveredSessionPeer peer(false,[&](Session& session,auto)->std::optional<std::vector<std::uint8_t>>{
            if(++calls==1){
                const auto init=*session.normal_world_initialization();
                {const auto temporary=session.capture_world_callback_output(init);
                 require(temporary.has_value(),"Passive capture missing");session.send_world_records(row);}
            }
            return std::vector<std::uint8_t>{};
        });
        peer.select(false);peer.send(RecoveredSessionPeer::tail());peer.silent();
        peer.send(RecoveredWorldFrame::encode(std::array<std::uint8_t,2>{0x67,101}));
        peer.expect(RecoveredWorldFrame::encode(row));peer.silent();
        peer.send(RecoveredWorldFrame::encode(std::array<std::uint8_t,2>{0x30,0}));peer.silent();
        require(calls==2&&!peer.session->closing(),"Dropped public observer revoked an actual retained Write");
    }
    // A genuinely accepted empty callback releases its independent raw hold,
    // with an explicit NoOutput terminal rather than a fabricated Written.
    {
        std::optional<Session::WorldCallbackOutput> empty;bool resumed=false;
        RecoveredSessionPeer peer(false,[&](Session& session,auto)->std::optional<std::vector<std::uint8_t>>{
            if(empty){resumed=empty->status()==Status::NoOutput&&empty->callback_accepted();return std::vector<std::uint8_t>{};}
            empty=session.capture_world_callback_output(*session.normal_world_initialization());
            require(empty.has_value(),"Empty actual callback capture missing");
            session.hold_world_input_until_callback_output_written(*empty);return std::vector<std::uint8_t>{};
        });
        peer.select(false);peer.send(RecoveredSessionPeer::tail());peer.silent();
        auto input=RecoveredWorldFrame::encode(std::array<std::uint8_t,2>{0x67,101});
        const auto tick=RecoveredWorldFrame::encode(std::array<std::uint8_t,2>{0x30,0});input.insert(input.end(),tick.begin(),tick.end());
        peer.send(input);peer.silent();require(empty&&resumed&&peer.world_calls==2&&empty->sealed()&&
            empty->status()==Status::NoOutput&&empty->components().empty()&&empty->final_return_wire().empty(),
            "Accepted no-output callback closed, stalled or minted a fake Write");
    }
    // Duplicate capture, wrong input order and unsupported own sender all
    // poison the optional transcript; ordinary side-send bytes remain original.
    for(unsigned failure=0;failure<4;++failure){
        std::optional<Session::WorldCallbackOutput> failed;bool rejected=false;
        const auto row=logical(101);
        RecoveredSessionPeer peer(false,[&](Session& session,auto)->std::optional<std::vector<std::uint8_t>>{
            const auto init=*session.normal_world_initialization();
            if(failure==0){session.send_world_records(row);rejected=!session.capture_world_callback_output(init);return std::vector<std::uint8_t>{};}
            failed=session.capture_world_callback_output(init);require(failed.has_value(),"Failure fixture capture missing");
            if(failure==1)rejected=!session.capture_world_callback_output(init);
            if(failure==2)rejected=!session.claim_next_callback_selection(*failed,{102});
            if(failure==3){session.send(Packet{});rejected=failed->status()==Status::Failed;}
            return std::vector<std::uint8_t>{};
        });
        peer.select(false);peer.send(RecoveredSessionPeer::tail());peer.silent();
        peer.send(RecoveredWorldFrame::encode(std::array<std::uint8_t,2>{0x67,101}));
        if(failure==0){peer.expect(RecoveredWorldFrame::encode(row));peer.silent();require(!failed&&rejected,"Late capture borrowed prior output");}
        else if(failure<3){peer.silent();require(rejected&&failed&&failed->status()==Status::Failed,
            "Duplicate capture or wrong original input revived composite");}
        else {for(unsigned i=0;i<8;++i)peer.pump();require(rejected&&failed&&failed->status()==Status::Failed&&peer.session->closing(),
            "Unsupported fixture Packet sender silently became Written");}
    }
    // Phase retirement and close-before-queue cannot expose a Written source.
    for(const bool phase_change:{false,true}){
        std::optional<Session::WorldCallbackOutput> failed;
        RecoveredSessionPeer peer(false,[&](Session& session,auto)->std::optional<std::vector<std::uint8_t>>{
            failed=session.capture_world_callback_output(*session.normal_world_initialization());
            session.hold_world_input_until_callback_output_written(*failed);
            session.send_world_records(logical(101));
            if(phase_change)session.set_state(SessionState::InBattle);else session.close();
            return std::vector<std::uint8_t>{};
        });
        peer.select(false);peer.send(RecoveredSessionPeer::tail());peer.silent();
        peer.send(RecoveredWorldFrame::encode(std::array<std::uint8_t,2>{0x67,101}));
        for(unsigned i=0;i<8;++i)peer.pump();require(failed&&failed->status()==Status::Failed&&peer.session->closing()&&
            !peer.session->world_callback_output_current_on_game(*failed),"Retired phase or unqueued close minted Written");
    }
    // Destroy a stopped real IO owner with side/final posts still pending.
    // Retained Data cannot keep its private delivery Attempt Pending forever.
    {
        std::optional<Session::WorldCallbackOutput> dropped;
        {
            RecoveredSessionPeer* actual=nullptr;
            RecoveredSessionPeer peer(false,[&](Session& session,auto)->std::optional<std::vector<std::uint8_t>>{
                dropped=session.capture_world_callback_output(*session.normal_world_initialization());
                session.hold_world_input_until_callback_output_written(*dropped);session.send_world_records(logical(101));
                actual->drain_on_destroy=false;actual->io.stop();return std::vector<std::uint8_t>{};
            });actual=&peer;
            peer.select(false);peer.send(RecoveredSessionPeer::tail());peer.silent();
            peer.send(RecoveredWorldFrame::encode(std::array<std::uint8_t,2>{0x67,101}));peer.pump();
            require(dropped&&dropped->status()==Status::Pending&&dropped->sealed()&&!dropped->callback_accepted(),
                "Dropped-post fixture did not retain real unrun side/final posts");
        }
        require(dropped->status()==Status::Failed,"Destroyed actual post handlers left retained composite Pending");
    }
}

// True Registry -> helper private commit -> typed original sender custody.
// These are source regressions only; matching baseline S31 bytes carry no tag.
// Isolated regression material: empty mode has no book entitlement; book mode
// declares a synthetic acquisition and obtains actual learning events through
// repository issuers. Neither mode proves a native grant or gameplay formula.
// The actual Session writes the original restoration and learning responses.
void recovered_legacy_selection_learning_reanchor(bool with_book=false) {
    using Source=LegacyTaiwanOwnedDeitySelectionRegistry::WrittenSelectionSource;
    using Restoration=RecoveredOwnedCompanions::Restoration;
    struct Close {void operator()(sqlite3* value)const {sqlite3_close_v2(value);}};
    sqlite3* raw=nullptr;require(sqlite3_open(":memory:",&raw)==SQLITE_OK,"Legacy learning DB open failed");
    std::unique_ptr<sqlite3,Close> db(raw);
    sqlite_detail::execute(raw,"PRAGMA foreign_keys=ON");
    SqliteMigrationManager(raw,default_sqlite_migrations()).migrate();
    sqlite_detail::execute(raw,"INSERT INTO accounts(id,username,password_hash) VALUES(7,'legacy-learning-fixture','hash')");
    SqliteAccountRepository accounts(raw);
    SqliteRecoveredCharacterRepository characters(raw);
    SqliteCompanionRepository companions(raw);
    SqliteOwnedInventoryRepository inventory(raw,accounts,characters);
    SqliteNativeEquipmentSnapshotRepository equipment(raw,accounts,characters);
    NativeSkillBookCatalog books(raw);NativeSkillCatalog skills(raw);
    SqliteSkillBookLearningRepository repository(inventory,equipment,companions,books,skills);
    RecoveredOwnedCompanions helper(companions);
    sqlite_detail::execute(raw,SqliteOwnedInventoryRepository::schema());
    sqlite_detail::execute(raw,SqliteNativeEquipmentSnapshotRepository::schema());
    sqlite_detail::execute(raw,SqliteSkillBookLearningRepository::schema());
    std::array<std::uint8_t,40> profile{};profile[0]='L';
    const auto character=characters.create(RecoveredSessionPeer::account,profile).id;
    require(character>0&&character<=0x3fff,"Legacy learning test actor outside native domain");
    const auto actor=static_cast<std::uint16_t>(character);
    const auto position=characters.commit_position(RecoveredSessionPeer::account,character,{},1,1,18,14);
    for(std::uint8_t key=1;key<=16;++key) {
        sqlite_detail::Statement metadata(raw,"INSERT INTO native_companion_metadata VALUES('GOD',?,?,1,X'4C',?,zeroblob(396))");
        metadata.bind(1,2800+key);metadata.bind(2,std::string(SqliteCompanionRepository::source_sha256));
        metadata.bind(3,std::string(64,'a'));metadata.done();
        RecoveredDeityState::Declaration::Bytes declaration{0x30,key,'L'};
        RecoveredDeityState::Status::Bytes status{0x31,key,1};
        const std::array<std::uint8_t,4> skill{0x34,key,0,static_cast<std::uint8_t>(with_book?2:1)};
        companions.store_deity(RecoveredSessionPeer::account,character,
            {*RecoveredDeityState::Declaration::parse(declaration),*RecoveredDeityState::Status::parse(status),
                {*RecoveredDeityState::Skill::parse(skill)}},{},
            {SqliteCompanionRepository::source_sha256,"CUSTOM_TEST_NOT_NATIVE","legacy-learning-selection-fixture"});
    }
    const auto root=characters.list_for_account(RecoveredSessionPeer::account).front();
    // An explicitly empty full population is not an implicit free-cell grant.
    OwnedInventorySnapshot bag{root,1,std::string(64,'b'),"fixture-empty-full-population",{}};
    // Optional chronology run: explicit CUSTOM_TEST_NOT_NATIVE acquisition and
    // binding. Both aliases come from this ONE complete fixture S3B25 record.
    // Neither the fixture nor its copied definition proves native entitlement.
    RecoveredTaiwanInventoryItemRecord::Instance book_instance{};
    book_instance[0]=0x65;book_instance[1]=0x19;book_instance[18]=0xa5;book_instance[19]=0x5a;
    const RecoveredTaiwanInventoryItemRecord::Fields book_fields{2,0,0xb7a5,book_instance};
    const auto book_record=RecoveredTaiwanInventoryItemRecord::encode(book_fields);
    require(book_record.has_value(),"Fixture full skill-book material rejected");
    if(with_book) {
        const auto identity=std::vector<std::uint8_t>(book_instance.begin(),book_instance.end());
        const auto material=std::vector<std::uint8_t>(book_record->begin(),book_record->end());
        const auto pin=NativeEquipmentSnapshot::client_pin;
        const std::string evidence="CUSTOM_TEST_NOT_NATIVE:round482-book-source";
        OwnedItemNativeAlias item20{pin,"tw149c-item20",std::string(64,'d'),evidence,6501,0,1,identity};
        OwnedItemNativeAlias item25{pin,"tw149c-item3b25-material",std::string(64,'d'),evidence,6501,0,1,material};
        OwnedInventoryInstance item{9001,6501,2,1,true,std::string(64,'e'),
            "CUSTOM_TEST_NOT_NATIVE:round482-authorized-acquisition",{item20,item25}};
        bag.cells={{"bag",0,item},{"bag",1,std::nullopt}};
        bag.source_record="CUSTOM_TEST_NOT_NATIVE:round482-whole-book-population";
    }
    require(inventory.replace_from_issuer({},bag,[&](const auto&,const auto&,auto){return std::optional{bag};}).has_value(),
        "Legacy learning full inventory fixture missing");
    NativeEquipmentSnapshot worn{root,position,NativeEquipmentSnapshot::client_pin,NativeEquipmentSnapshot::kind,
        std::string(64,'c'),"fixture-full-empty-native-bank",std::vector<std::uint8_t>(NativeEquipmentSnapshot::record_bytes),1,actor};
    worn.record[1]=0xa5;worn.record[2]=0x5a; // Opaque empty-cell bytes must survive.
    worn.record[1200]=0xda;worn.record[1201]=static_cast<std::uint8_t>(actor);
    worn.record[1202]=static_cast<std::uint8_t>(actor>>8);worn.record[1214]=0x82;
    if(with_book) {
        worn.record[0]=2;
        std::copy(book_instance.begin(),book_instance.end(),worn.record.begin()+4);
        worn.source_record="CUSTOM_TEST_NOT_NATIVE:round482-complete-book-bank";
    }
    require(equipment.replace_from_issuer({},worn,[&](const auto&,const auto&,auto){return std::optional{worn};}).has_value(),
        "Legacy learning full equipment fixture missing");
    if(with_book) {
        // Copy the exact retained historical Taiwan0/1 definition, NOT an
        // invented native row. The SKB raw/parsed bytes and acquisition below
        // are digest-consistent synthetic TEST material for CUSTOM-0148 only.
        sqlite_detail::execute(raw,"INSERT INTO native_data_sources VALUES('current-skill-catalog-v1','fixture-only/retained-tw0-1.bin','7676acd93f164d071f7681a3fe74de94d65892759dbf2e69e3c0f748423d2f51','7676acd93f164d071f7681a3fe74de94d65892759dbf2e69e3c0f748423d2f51','149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763','fixture-retained-source','0x1','0x2',448)");
        sqlite_detail::execute(raw,"INSERT INTO native_data_sources VALUES('current-skill-books-v1','Data2/Patch/Comm/gamedata.csvZ','70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731','75c3c37947a64b0917fbf8e546884d9bf893fe6a606d3e2b8f3b1857966b1815','149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763','SKB','0x59420','0xA8E10',381)");
        const std::array<std::uint8_t,110> definition{
            0x01,0x00,0xbc,0x43,0xb3,0x4e,0x4c,0x76,0x31,0x00,0x00,0x00,0x00,0x00,0x00,0x00,
            0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,
            0xbc,0x43,0xa4,0x40,0x20,0x20,0xbb,0x61,0xaa,0xc6,0xb3,0x5a,0x20,0x20,0xbc,0x43,
            0xae,0xf0,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,
            0x01,0x00,0x05,0x00,0x03,0x01,0x3c,0x01,0x01,0x00,0x11,0x00,0x00,0x00,0x00,0x00,
            0x00,0x00,0x00,0x00,0x00,0x00,0x01,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,
            0x00,0x00,0x00,0x00,0x00,0x00,0x01,0x00,0x00,0x00,0x00,0x01,0x01,0x00
        };
        sqlite_detail::Statement row(raw,"INSERT INTO native_skill_catalog VALUES('current-skill-catalog-v1',0,8,'a9ae52a190a314de68c86fea4fbc8a59d4e70ede8287e349f38638335596c5ab',?,0,1)");
        row.bind_blob(1,definition);row.done();
        // SHA256('A') and SHA256(396 zero bytes), independently fixed fixture
        // bytes; no claim these are a recovered original SKB resource record.
        sqlite_detail::execute(raw,"INSERT INTO native_skill_books VALUES('current-skill-books-v1',0,1,0,6501,'559aead08264d5795d3909718cdd05abd49572e84fe55590eef31a88a08fdffd',X'41','58553b15fb3888e443e29fff5663675b8f70e37f0ea6c54076489d6ff04c1032',zeroblob(396))");
        sqlite_detail::execute(raw,"INSERT INTO native_skill_book_bindings VALUES('current-skill-books-v1','current-skill-catalog-v1',0,1,6501)");
        const auto bound=books.lookup_item(6501);const auto native=skills.lookup_shared_definition_main(0,1);
        require(bound&&native&&native->definition.chosen_profile,"Fixture book or exact pinned source was not admitted by real readers");
    }
    auto canonical=std::make_shared<const Restoration>(helper.restore_with_source(RecoveredSessionPeer::account,character,repository));
    require(canonical->learning_source()&&canonical->learning_source()->activations().empty(),
        "Legacy learning fixture manufactured an activation");
    const auto original=canonical;
    LuaEngine lua(std::filesystem::path(GOD2_SOURCE_DIR)/"scripts");
    if(with_book)require(lua.initialize(),"CUSTOM-0148 real Lua policy initialization failed");
    OwnedSkillBookLearningService learning(repository,lua,1);
    LegacyTaiwanOwnedDeitySelectionRegistry registry(1,helper);
    std::vector<Session::WorldRecordsWrite> restoration_writes;
    std::optional<Session::NormalWorldInitialization> initialization;
    std::optional<Session::WorldCallbackOutput> output;
    std::optional<Source> applied;
    unsigned idle_stage=0,selection_callbacks=0,pending_refusals=0;
    unsigned learning_callbacks=0;
    bool learning_pending_refused=false;
    std::optional<Session::WorldResponseWrite> bootstrap_response,learning_response;
    std::optional<OwnedSkillBookLearningService::LearningPublication> latest_learning;
    std::optional<OwnedSkillBookLearningService::WrittenLearningSource> last_learning_source;
    bool pending_registry_refused=false,bootstrapped=false;
    RecoveredSessionPeer peer(false,[&](Session& session,auto records)->std::optional<std::vector<std::uint8_t>> {
        if(with_book&&records.size()==1)if(const auto* request=std::get_if<RecoveredInventoryItemRequest::Request>(&records.front())) {
            require(bootstrapped&&applied&&applied->current(session),"Book use lost the actual prior Written legacy selection");
            auto result=learning.use_with_source(session,*request);
            require(result&&result->publication(),"Actual CUSTOM-0148 learning did not issue its private committed publication");
            const auto publication=*result->publication();
            auto response=std::move(*result).take_wire();
            require(!response.empty(),"Real learning debit returned no original output");
            learning_response=session.observe_world_response(response);
            session.hold_world_input_until_response_written(*learning_response);
            learning.bind_learning_response(session,publication,*learning_response);
            latest_learning=publication;++learning_callbacks;
            learning_pending_refused=learning_response->status()==Session::WorldResponseWriteStatus::Pending&&
                !learning.written_learning_source(session,publication)&&!learning.learning_publication_current(session,publication);
            return response;
        }
        const bool idle=std::all_of(records.begin(),records.end(),[](const auto& record){
            return std::holds_alternative<RecoveredWorldRecords::Tick>(record);
        });
        if(idle) {
            if(idle_stage++==0) {
                initialization=session.normal_world_initialization();require(initialization.has_value(),"Legacy restoration INIT absent");
                for(const auto& batch:original->batches())restoration_writes.push_back(session.send_world_records_observed(batch));
            }else if(!bootstrapped) {
                const auto supplied=[&](Session& actual)->std::shared_ptr<const Restoration> {
                    if(!initialization||!actual.normal_world_initialization_current_on_game(*initialization)||
                       restoration_writes.size()!=original->batches().size()||!helper.restoration_current(*original))return {};
                    for(std::size_t i=0;i<restoration_writes.size();++i)
                        if(restoration_writes[i].status()!=Session::WorldRecordsWriteStatus::Written||
                           restoration_writes[i].logical()!=original->batches()[i]||
                           !actual.world_records_write_current(restoration_writes[i]))return {};
                    return original;
                };
                const auto bootstrap=learning.bootstrap(session,{},supplied);
                require(bootstrap.has_value(),"Real learning bootstrap source was rejected");
                if(with_book) {
                    require(!bootstrap->empty(),"Owned book bootstrap omitted actual material");
                    bootstrap_response=session.observe_world_response(*bootstrap);
                    session.hold_world_input_until_response_written(*bootstrap_response);
                    learning.bind_bootstrap_response(session,*bootstrap_response);
                    bootstrapped=true;
                    return *bootstrap;
                }
                require(bootstrap->empty(),"Empty real learning bootstrap fabricated an output receipt");
                bootstrapped=true;
            }
            return std::vector<std::uint8_t>{};
        }
        require(bootstrapped,"Legacy C67 preceded actual restoration/learning entry");
        const auto init=session.normal_world_initialization();require(init.has_value(),"Legacy selection INIT absent");
        output=session.capture_world_callback_output(*init);require(output.has_value(),"Legacy reanchor output capture absent");
        session.hold_world_input_until_callback_output_written(*output);
        const auto callback=registry.begin(session,*init,*output);
        if(applied) {
            // begin invalidates the old callback source before any new SQL.
            // An old Written token cannot stand in for this Pending callback.
            require(!applied->current(session)&&!learning.reanchor_selection(session,canonical,canonical,*applied),
                "Pending next C67 borrowed the old Written source");
            ++pending_refusals;
        }
        LegacyWorldReply reply(std::vector<std::uint8_t>{});
        for(const auto& record:records) {
            const auto* request=std::get_if<RecoveredDeitySelection::Request>(&record);
            require(request!=nullptr,"Legacy selection regression received an unrelated record");
            auto child=registry.select(session,*request);require(child.has_value(),"Legacy true selection producer refused fixture");
            reply.append(std::move(*child));
        }
        registry.finish(session,callback,true);registry.abandon(callback);
        pending_registry_refused=!registry.observe(session)&&output->status()==Session::WorldCallbackOutputStatus::Pending;
        ++selection_callbacks;
        return session.take_world_callback_reply(std::move(reply));
    },character,48171);
    peer.select(false);peer.send(RecoveredSessionPeer::tail(actor));peer.silent();
    const auto tick=RecoveredWorldFrame::encode(std::array<std::uint8_t,2>{0x30,0});
    peer.send(tick);
    for(const auto& batch:original->batches())peer.expect(RecoveredWorldFrame::encode(batch));
    peer.silent();peer.send(tick);
    if(with_book) {
        std::vector<std::uint8_t> logical(book_record->begin(),book_record->end());
        const auto absolute=RecoveredInventory::encode_slot_update({6501,0,2});require(absolute.has_value(),"Fixture absolute book count invalid");
        logical.insert(logical.end(),absolute->begin(),absolute->end());
        peer.expect(RecoveredWorldFrame::encode(logical));
    }
    peer.silent();
    if(with_book)require(bootstrap_response&&bootstrap_response->status()==Session::WorldResponseWriteStatus::Written,
        "Actual original book bootstrap output did not become Written");
    require(bootstrapped&&initialization&&peer.session->normal_world_initialization_current_on_game(*initialization),
        "Legacy learning bootstrap did not retain its real INIT");
    const auto send_selection=[&](std::initializer_list<std::uint8_t> keys) {
        std::vector<std::uint8_t> logical,expected;
        for(const auto key:keys) {
            logical.insert(logical.end(),{0x67,key});
            const auto rows=companions.load_deities(RecoveredSessionPeer::account,character);
            const auto found=std::find_if(rows.begin(),rows.end(),[&](const auto& row){return row.snapshot.status.key_raw()==key;});
            require(found!=rows.end(),"Legacy reanchor test selection has no saved deity");
            const auto frame=RecoveredWorldFrame::encode(found->snapshot.status.encode());
            expected.insert(expected.end(),frame.begin(),frame.end());
        }
        peer.send(RecoveredWorldFrame::encode(logical));peer.expect(expected);peer.silent();
        require(pending_registry_refused&&output&&output->status()==Session::WorldCallbackOutputStatus::Written,
            "Legacy selection became observable before its complete original output");
        const auto written=registry.observe(*peer.session);
        require(written&&written->current(*peer.session),"Actual legacy Written source missing");
        return *written;
    };
    const auto first=send_selection({1,1});
    require(first.publications().size()==2&&!first.publications()[1].committed().changed(),
        "Idempotent C67 did not retain its separate private commit");
    const auto next_value=helper.selection_successor_from_committed(*canonical,first.publications());
    require(next_value.has_value(),"Legacy private chain could not advance full restoration");
    const auto next=std::make_shared<const Restoration>(*next_value);
    require(!learning.reanchor_selection(*peer.session,next,next,first)&&
            !learning.reanchor_selection(*peer.session,canonical,canonical,first),
        "Wrong complete predecessor or after-state adopted a legacy selection");
    const auto saved_character=peer.session->character_id;
    peer.session->character_id^=std::uint64_t{1}<<32;
    require(!learning.reanchor_selection(*peer.session,canonical,next,first),"Legacy reanchor narrowed common character identity");
    peer.session->character_id=saved_character;
    const auto saved_account=peer.session->account_id;
    peer.session->account_id^=std::uint64_t{1}<<32;
    require(!learning.reanchor_selection(*peer.session,canonical,next,first),"Legacy reanchor narrowed common account identity");
    peer.session->account_id=saved_account;
    RecoveredSessionPeer foreign(false,[](Session&,auto)->std::optional<std::vector<std::uint8_t>>{
        return std::vector<std::uint8_t>{};
    },character,48172);
    foreign.select(false);foreign.send(RecoveredSessionPeer::tail(actor));foreign.silent();
    const auto foreign_init=foreign.session->normal_world_initialization();
    require(foreign_init&&!foreign_init->same_initialization(first.initialization())&&
            !learning.reanchor_selection(*foreign.session,canonical,next,first),
        "Foreign real INIT/Session adopted a legacy selection");
    require(learning.reanchor_selection(*peer.session,canonical,next,first),"Real Written legacy selection failed to reanchor existing learning Entry");
    require(!learning.reanchor_selection(*peer.session,canonical,next,first)&&
            !learning.reanchor_selection(*peer.session,next,next,first),"Same private legacy source reanchored twice");
    canonical=next;applied=first;
    // This is the actual Session/Service/repository chronology, not execution
    // of Application's outer wrapper graph. No private source is test-minted.
    const auto learn_book=[&](std::uint8_t subject,std::uint8_t remaining) {
        const auto previous=latest_learning;
        const auto predecessor=canonical;
        const auto prior_source=last_learning_source;
        const auto request=RecoveredInventoryItemRequest::encode({6501,0,0xa5});
        const std::array<std::uint8_t,13> delta{0x34,subject,0,1,0x35,subject,0,1,0x41,
            static_cast<std::uint8_t>(remaining?0x65:0),static_cast<std::uint8_t>(remaining?0x19:0),0,remaining};
        peer.send(RecoveredWorldFrame::encode(request));peer.expect(RecoveredWorldFrame::encode(delta));peer.silent();
        require(learning_pending_refused&&latest_learning&&learning_response&&
                learning_response->status()==Session::WorldResponseWriteStatus::Written,
            "Learning adopted before its true original response was Written");
        const auto written=learning.written_learning_source(*peer.session,*latest_learning);
        require(written&&written->current(*peer.session)&&written->follows(previous)&&
                written->original_restoration()==predecessor&&written->logical_delta()==delta,
            "Learning lost its full predecessor, real13-byte delta or private chronology");
        if(previous)require(!written->follows({}),"A later real learning event forgot its selection-separated predecessor");
        if(prior_source)require(!prior_source->current(*peer.session),"New learning revived the older consumed learning source");
        auto history=predecessor->batches();history.emplace_back(delta.begin(),delta.end());
        const auto successor=helper.learning_successor_from_committed(*predecessor,written->committed(),std::move(history));
        require(successor&&successor->learning_source()&&helper.restoration_current(*successor),
            "Real learning commit did not advance the complete restoration");
        const auto& state=*successor->learning_source();
        require(state.activations().size()==learning_callbacks&&state.activations().back().subject==subject&&
                state.activations().back().event_id.starts_with("CUSTOM-0148:"),
            "Actual learning issuer failed to preserve activation header/event lineage");
        const auto slot=std::find_if(state.inventory().cells.begin(),state.inventory().cells.end(),[](const auto& cell){
            return cell.location_kind=="bag"&&cell.location_index==0;
        });
        require(slot!=state.inventory().cells.end()&&
                (remaining?(slot->instance&&slot->instance->quantity==remaining):!slot->instance)&&
                state.equipment().record[0]==remaining&&state.equipment().record[1]==0xa5&&state.equipment().record[2]==0x5a,
            "Actual book debit corrupted canonical count, full native bank or opaque bytes");
        require(inventory.load(RecoveredSessionPeer::account,character)==std::optional{state.inventory()}&&
                equipment.load(RecoveredSessionPeer::account,character,NativeEquipmentSnapshot::client_pin,NativeEquipmentSnapshot::kind)==std::optional{state.equipment()},
            "Written learning did not retain its actual committed complete material");
        canonical=std::make_shared<const Restoration>(*successor);last_learning_source=written;
    };
    if(with_book)learn_book(1,1);
    for(const std::uint8_t key:{std::uint8_t{1},std::uint8_t{2}}) {
        const auto written=send_selection({key});
        const auto successor=helper.selection_successor_from_committed(*canonical,written.publications());
        require(successor.has_value(),"Repeated/next C67 lost full private predecessor");
        auto after=std::make_shared<const Restoration>(*successor);
        require(learning.reanchor_selection(*peer.session,canonical,after,written)&&
                !learning.reanchor_selection(*peer.session,canonical,after,written),
            "Repeated selected key or next C67 failed exactly-once reanchor");
        canonical=std::move(after);applied=written;
        if(with_book&&last_learning_source)require(!last_learning_source->current(*peer.session),
            "Written next C67 failed to retire the old learning Current");
    }
    if(with_book) {
        // A second genuine learning event on the newly selected deity proves
        // prior chronology survives BOTH repeated-key and changed-key C67.
        learn_book(2,0);
        require(learning_callbacks==2,"Chronology fixture did not perform both actual book debits");
    }
    // Complete equipment provenance changes are not cured by matching S31 bytes.
    const auto last=send_selection({3});
    const auto last_value=helper.selection_successor_from_committed(*canonical,last.publications());
    require(last_value.has_value(),"Final legacy selection full successor missing");
    const auto last_after=std::make_shared<const Restoration>(*last_value);
    const auto equipment_before=equipment.load(RecoveredSessionPeer::account,character,NativeEquipmentSnapshot::client_pin,NativeEquipmentSnapshot::kind);
    require(equipment_before.has_value(),"Legacy stale-equipment fixture missing before state");
    auto changed=*equipment_before;++changed.revision;changed.source_record="fixture-opaque-after-selection";changed.record[1]^=0x01;
    require(equipment.replace_from_issuer(equipment_before,changed,[&](const auto&,const auto&,auto){return std::optional{changed};}).has_value(),
        "Legacy stale-equipment fixture issuer failed");
    require(last.current(*peer.session)&&!learning.reanchor_selection(*peer.session,canonical,last_after,last),
        "Written S31 alone renewed a stale complete equipment source");
    registry.release(*peer.session);
    require(!last.current(*peer.session)&&!learning.reanchor_selection(*peer.session,canonical,last_after,last),
        "Released legacy source revived through saved equality");
    require(selection_callbacks==4&&pending_refusals==3&&!peer.session->closing(),
        "Legacy learning reanchor test lost a real callback or changed transport");
}

void recovered_causal_deity_reply_transport() {
    using Status=Session::WorldCallbackOutputStatus;
    struct Close {void operator()(sqlite3* value)const {sqlite3_close_v2(value);}};
    sqlite3* raw=nullptr;require(sqlite3_open(":memory:",&raw)==SQLITE_OK,"Causal fixture DB open failed");
    std::unique_ptr<sqlite3,Close> db(raw);
    sqlite_detail::execute(raw,"PRAGMA foreign_keys=ON");
    SqliteMigrationManager(raw,default_sqlite_migrations()).migrate();
    sqlite_detail::execute(raw,"INSERT INTO accounts(id,username,password_hash) VALUES(7,'causal-test','hash')");
    SqliteRecoveredCharacterRepository characters(raw);
    std::array<std::uint8_t,40> profile{};profile[0]='C';
    const auto character=characters.create(RecoveredSessionPeer::account,profile).id;
    SqliteCompanionRepository companions(raw);RecoveredOwnedCompanions helper(companions);
    RecoveredDeityState::Declaration::Bytes declaration{0x30,101,'C'};
    RecoveredDeityState::Status::Bytes status{0x31,101,1};
    const std::array<std::uint8_t,4> skill{0x34,101,0,1};
    companions.store_deity(RecoveredSessionPeer::account,character,
        {*RecoveredDeityState::Declaration::parse(declaration),*RecoveredDeityState::Status::parse(status),
            {*RecoveredDeityState::Skill::parse(skill)}},{},
        {SqliteCompanionRepository::source_sha256,"CUSTOM_TEST_NOT_NATIVE","causal-real-session-fixture"});
    const auto frame=RecoveredWorldFrame::encode(status);
    require(frame.size()==32,"Causal fixture is not a complete S31 frame");
    const auto copies=[&](unsigned count){
        std::vector<std::uint8_t> wire;
        for(unsigned i=0;i<count;++i)wire.insert(wire.end(),frame.begin(),frame.end());
        return wire;
    };
    // Canonical and physically reordered output both preserve every original
    // self Write. Only canonical input order is eligible for Registry adoption.
    for(const bool reordered:{false,true}) {
        LegacyTaiwanOwnedDeitySelectionRegistry registry(1,helper);
        std::optional<Session::WorldCallbackOutput> output;
        bool pending=false,resumed=false,raw_refused=false,uncaptured_refused=false;
        unsigned producers=0;
        RecoveredWorldService service({}, {}, {}, {}, {}, {}, {}, {},
            [&](Session& session,const auto& request)->std::optional<LegacyWorldReply>{
                ++producers;return registry.select(session,request);
            });
        RecoveredSessionPeer peer(false,[&](Session& session,auto records)->std::optional<std::vector<std::uint8_t>> {
            if(output) {
                require(records.size()==1&&std::holds_alternative<RecoveredWorldRecords::Tick>(records.front()),
                    "Causal raw-input suffix changed");
                resumed=output->status()==Status::Written&&!session.closing();return std::vector<std::uint8_t>{};
            }
            require(records.size()==2,"Causal original C67 batch changed");
            const auto before=companions.load_deity_selection(session.account_id,session.character_id);
            raw_refused=!service.handle(session,records.first(1))&&producers==0&&
                companions.load_deity_selection(session.account_id,session.character_id)==before;
            try{(void)registry.select(session,{101});}catch(const std::runtime_error&){uncaptured_refused=true;}
            require(uncaptured_refused&&companions.load_deity_selection(session.account_id,session.character_id)==before,
                "Selection mutated SQL before actual callback capture");
            const auto init=*session.normal_world_initialization();
            output=session.capture_world_callback_output(init);require(output.has_value(),"Causal capture missing");
            session.hold_world_input_until_callback_output_written(*output);
            auto callback=registry.begin(session,init,*output);
            auto first=service.handle_reply(session,records.first(1));
            require(first&&first->has_emissions(),"First real private C67 leaf missing its emission");
            std::vector<std::uint8_t> final;
            if(reordered) {
                auto second=service.handle_reply(session,records.subspan(1,1));
                require(second&&second->has_emissions(),"Second real private C67 leaf missing");
                auto frames=std::move(*second).split_frames();require(frames&&frames->size()==1,"Second leaf split failed");
                session.send_world_callback_reply_frame(std::move(frames->front()));
                final=session.take_world_callback_reply(std::move(*first));
            }else {
                // Equal-byte plain baseline is a DIFFERENT actual component.
                LegacyWorldReply side(frame);side.append(std::move(*first));
                auto frames=std::move(side).split_frames();require(frames&&frames->size()==2,"Typed prefix split lost original frame");
                require(!side.has_emissions()&&side.empty(),"Successful consuming split retained reusable tags");
                for(auto& part:*frames)session.send_world_callback_reply_frame(std::move(part));
                auto second=service.handle_reply(session,records.subspan(1,1));
                require(second&&second->has_emissions(),"Second idempotent true publication missing");
                LegacyWorldReply child(frame);child.append(std::move(*second));
                std::vector<std::uint8_t> inner;
                {
                    const auto outer_offset=session.callback_reply_output_offset(frame.size());
                    {
                        const auto inner_offset=session.callback_reply_output_offset(frame.size());
                        inner=session.take_world_callback_reply(std::move(child));
                    }
                }
                // Simulate nested outer append prefixes through the same API.
                // This is not execution of the Application wrapper graph.
                final=copies(2);final.insert(final.end(),inner.begin(),inner.end());
            }
            registry.finish(session,callback,true);registry.abandon(callback);
            pending=output->status()==Status::Pending&&!output->sealed()&&output->components().empty()&&
                !registry.observe(session);
            return final;
        },character,reordered?47702:47701);
        peer.select(false);peer.send(RecoveredSessionPeer::tail(static_cast<std::uint16_t>(character)));peer.silent();
        auto input=RecoveredWorldFrame::encode(std::array<std::uint8_t,4>{0x67,101,0x67,101});
        const auto tick=RecoveredWorldFrame::encode(std::array<std::uint8_t,2>{0x30,0});input.insert(input.end(),tick.begin(),tick.end());
        peer.send(input);peer.expect(copies(reordered?2:6));peer.silent();
        require(output&&raw_refused&&uncaptured_refused&&pending&&resumed&&producers==2&&peer.world_calls==2&&
            output->status()==Status::Written&&output->sealed()&&output->callback_accepted()&&!peer.session->closing(),
            "Causal physical writes changed order, failed input barrier or completed before full acceptance");
        const auto parts=output->components();require(parts.size()==(reordered?2u:3u),"Causal sender component count changed");
        if(reordered) {
            const auto a=parts[0].emissions(),b=parts[1].emissions();
            require(a.size()==1&&b.size()==1&&a[0].selection_ordinal()==1&&b[0].selection_ordinal()==0&&
                !a[0].same_occurrence(b[0])&&peer.session->callback_output_emission_written(*output,a[0])&&
                peer.session->callback_output_emission_written(*output,b[0])&&!registry.observe(*peer.session),
                "Physical out-of-input-order custody closed or falsely adopted canonical selection state");
        }else {
            require(parts[0].emissions().empty()&&parts[1].emissions().size()==1&&parts[2].emissions().size()==1,
                "Equal baseline S31 borrowed a true producer tag");
            const auto first=parts[1].emissions().front(),second=parts[2].emissions().front();
            const auto a=peer.session->callback_output_emission_location(*output,first);
            const auto b=peer.session->callback_output_emission_location(*output,second);
            require(!first.same_occurrence(second)&&first.selection_ordinal()==0&&second.selection_ordinal()==1&&
                first.expected_wire()==second.expected_wire()&&first.expected_wire()==frame&&a&&b&&
                a->component_ordinal==1&&a->frame_wire_offset==0&&b->component_ordinal==2&&b->frame_wire_offset==96&&
                a->logical_record_offset==0&&b->logical_record_offset==0&&a->logical_record_size==29&&b->logical_record_size==29,
                "Distinct same-byte input occurrences or nested actual frame locations were lost");
            const auto written=registry.observe(*peer.session);
            require(written&&written->publications().size()==2&&!written->publications()[1].committed().changed()&&
                written->publications()[1].committed().before()==std::optional{written->publications()[0].committed().after()}&&
                written->current(*peer.session),"True idempotent private commit chain did not survive exact output binding");
            const auto owner=peer.session->character_id;peer.session->character_id^=std::uint64_t{1}<<32;
            require(!written->current(*peer.session)&&!peer.session->callback_output_emission_written(*output,first),
                "Causal source narrowed full character identity");peer.session->character_id=owner;
            registry.release(*peer.session);require(!written->current(*peer.session)&&!registry.observe(*peer.session),
                "Released private selection source revived from equal bytes");
        }
    }

    // Real Session + private Registry/SQL producer, simulating the exact
    // Application appender boundary. These regression sources are not run in
    // PHASE1 and do not claim to execute the full Application wrapper graph.
    {
        for(const std::uint8_t key:{std::uint8_t{102},std::uint8_t{103}}) {
            auto next_declaration=declaration;next_declaration[1]=key;
            auto next_status=status;next_status[1]=key;
            auto next_skill=skill;next_skill[1]=key;
            companions.store_deity(RecoveredSessionPeer::account,character,
                {*RecoveredDeityState::Declaration::parse(next_declaration),
                 *RecoveredDeityState::Status::parse(next_status),
                 {*RecoveredDeityState::Skill::parse(next_skill)}},{},
                {SqliteCompanionRepository::source_sha256,"CUSTOM_TEST_NOT_NATIVE","causal-buffer-order-fixture"});
        }
        for(unsigned mode=0;mode<5;++mode) {
            const unsigned count=mode==1 || mode==2?3:2;
            const bool bad_fence=mode==3,changed_fragment=mode==4;
            LegacyTaiwanOwnedDeitySelectionRegistry registry(1,helper);
            std::optional<Session::WorldCallbackOutput> output;
            std::optional<Session::NormalWorldResponseAttempt> options_receipt;
            std::vector<std::vector<std::uint8_t>> produced;
            const auto option=RecoveredWorldFrame::encode(std::array<std::uint8_t,3>{0x1b,0x34,0x12});
            std::vector<std::uint8_t> expected;bool pending=false;
            RecoveredSessionPeer peer(false,[&](Session& session,auto records)->std::optional<std::vector<std::uint8_t>> {
                require(records.size()==count,"Buffered causal original input count changed");
                const auto init=*session.normal_world_initialization();
                output=session.capture_world_callback_output(init);require(output.has_value(),"Buffered capture absent");
                session.hold_world_input_until_callback_output_written(*output);
                auto callback=registry.begin(session,init,*output);
                struct End {
                    LegacyTaiwanOwnedDeitySelectionRegistry& registry;
                    LegacyTaiwanOwnedDeitySelectionRegistry::Callback callback;
                    ~End(){registry.abandon(callback);}
                } end{registry,callback};
                auto first=registry.select(session,{101});
                require(first&&first->has_emissions(),"Buffered first private producer missing");
                produced.push_back(first->wire());
                auto raw=session.take_world_callback_reply(std::move(*first));
                options_receipt=session.capture_normal_world_response(init);
                require(options_receipt.has_value(),"Buffered normal S1B receipt missing");
                session.expect_normal_world_response(*options_receipt,option);
                raw.insert(raw.end(),option.begin(),option.end());
                for(unsigned i=1;i<count;++i) {
                    const auto offset=session.callback_reply_output_offset(raw.size()-(bad_fence?1:0));
                    auto next=registry.select(session,{static_cast<std::uint8_t>(101+i)});
                    require(next&&next->has_emissions(),"Buffered subsequent private producer missing");
                    produced.push_back(next->wire());
                    if(mode==2 && i==2) {
                        auto last=session.take_world_callback_reply(std::move(*next));
                        raw.insert(raw.end(),last.begin(),last.end());
                    }else {
                        auto frames=std::move(*next).split_frames();
                        require(frames&&frames->size()==1,"Buffered private frame split failed");
                        session.send_world_callback_reply_frame(std::move(frames->front()));
                    }
                }
                pending=output->status()==Status::Pending && !output->sealed() &&
                    output->components().empty() && !registry.observe(session);
                expected=produced[0];expected.insert(expected.end(),option.begin(),option.end());
                for(unsigned i=1;i<count;++i)expected.insert(expected.end(),produced[i].begin(),produced[i].end());
                if(changed_fragment)raw.front()^=1;
                registry.finish(session,callback,true);return raw;
            },character,47900+mode);
            peer.select(false);peer.send(RecoveredSessionPeer::tail(static_cast<std::uint16_t>(character)));peer.silent();
            std::vector<std::uint8_t> input;
            for(unsigned i=0;i<count;++i){input.push_back(0x67);input.push_back(static_cast<std::uint8_t>(101+i));}
            peer.send(RecoveredWorldFrame::encode(input));
            if(bad_fence || changed_fragment) {
                for(unsigned i=0;i<12;++i)peer.pump();
                require(output&&output->status()==Status::Failed&&peer.session->closing()&&!registry.observe(*peer.session),
                    "Invalid deferred fence/fragment created usable selection custody");
                continue;
            }
            // expected is populated by the actual callback during IO pumping.
            for(unsigned i=0;i<20 && produced.size()!=count;++i)peer.pump();
            require(produced.size()==count&&!expected.empty(),"Buffered callback did not produce expected source frames");
            peer.expect(expected);peer.silent();
            require(pending&&produced.size()==count&&output&&output->status()==Status::Written&&
                output->callback_accepted()&&!peer.session->closing()&&options_receipt&&
                options_receipt->status()==Session::NormalWorldResponseStatus::Queued,
                "Buffered selections or original normal option receipt failed real transport");
            const auto parts=output->components();
            require(parts.size()==1&&parts.front().kind()==Session::WorldCallbackOutput::Kind::FinalResponse&&
                parts.front().emissions().size()==count,"Deferred selection leaked an early side Write");
            const auto written=registry.observe(*peer.session);
            require(written&&written->publications().size()==count&&
                written->publications().back().committed().after().key==100+count,
                "Correct final selected deity did not survive canonical physical output");
            const auto emissions=parts.front().emissions();
            for(unsigned i=0;i<count;++i) {
                const auto location=peer.session->callback_output_emission_location(*output,emissions[i]);
                const auto wanted=i?produced[0].size()+option.size()+(i-1)*frame.size():0;
                require(emissions[i].selection_ordinal()==i&&emissions[i].expected_wire()==produced[i]&&location&&
                    location->component_ordinal==0&&location->frame_wire_offset==wanted,
                    "Deferred occurrence was guessed, duplicated or bound at the wrong actual frame");
            }
        }
    }

    // A committed tag cannot be recovered from equal plain bytes, an incorrect
    // trusted append offset, or a changed registered fragment. No SQL replay.
    for(unsigned failure=0;failure<3;++failure) {
        LegacyTaiwanOwnedDeitySelectionRegistry registry(1,helper);
        std::optional<Session::WorldCallbackOutput> output;
        RecoveredSessionPeer peer(false,[&](Session& session,auto)->std::optional<std::vector<std::uint8_t>> {
            const auto init=*session.normal_world_initialization();output=session.capture_world_callback_output(init);
            require(output.has_value(),"Failed causal fixture missing actual capture");
            session.hold_world_input_until_callback_output_written(*output);
            auto callback=registry.begin(session,init,*output);
            auto leaf=registry.select(session,{101});require(leaf&&leaf->has_emissions(),"Failed causal fixture did not commit real C67");
            std::vector<std::uint8_t> final;
            if(failure==0)final=leaf->wire(); // Intentionally discard private carrier, despite exact same S31 bytes.
            else {
                if(failure==1){const auto offset=session.callback_reply_output_offset(frame.size());final=session.take_world_callback_reply(std::move(*leaf));}
                else {final=session.take_world_callback_reply(std::move(*leaf));final.back()^=1;}
            }
            registry.finish(session,callback,true);registry.abandon(callback);return final;
        },character,47710+failure);
        peer.select(false);peer.send(RecoveredSessionPeer::tail(static_cast<std::uint16_t>(character)));peer.silent();
        peer.send(RecoveredWorldFrame::encode(std::array<std::uint8_t,2>{0x67,101}));
        for(unsigned i=0;i<12;++i)peer.pump();
        require(output&&output->status()==Status::Failed&&peer.session->closing()&&!registry.observe(*peer.session),
            "Lost causal tag/offset/fragment minted Written or left committed prefix replayable");
        for(const auto& part:output->components())require(part.emissions().empty(),"Failed cohort exposed Written emission authority");
    }
}

void recovered_written_deity_selection_transport() {
    struct Close {void operator()(sqlite3* db)const {sqlite3_close_v2(db);}};
    sqlite3* raw=nullptr;require(sqlite3_open(":memory:",&raw)==SQLITE_OK,"Selection fixture DB open failed");
    std::unique_ptr<sqlite3,Close> db(raw);
    sqlite_detail::execute(raw,"PRAGMA foreign_keys=ON");
    SqliteMigrationManager(raw,default_sqlite_migrations()).migrate();
    sqlite_detail::execute(raw,"INSERT INTO accounts(id,username,password_hash) VALUES(7,'selection-test','hash')");
    SqliteRecoveredCharacterRepository characters(raw);
    std::array<std::uint8_t,40> profile{};profile[0]='S';
    const auto character=characters.create(RecoveredSessionPeer::account,profile).id;
    const auto position=characters.commit_position(RecoveredSessionPeer::account,character,{},1,1,18,14);
    SqliteCompanionRepository companions(raw);RecoveredOwnedCompanions helper(companions);
    for(const std::uint8_t key:{101,102}) {
        RecoveredDeityState::Declaration::Bytes declaration{0x30,key,'S'};
        RecoveredDeityState::Status::Bytes status{0x31,key,1};
        const std::array<std::uint8_t,4> skill{0x34,key,0,1};
        companions.store_deity(RecoveredSessionPeer::account,character,
            {*RecoveredDeityState::Declaration::parse(declaration),*RecoveredDeityState::Status::parse(status),
                {*RecoveredDeityState::Skill::parse(skill)}},{},
            {SqliteCompanionRepository::source_sha256,"CUSTOM_TEST_NOT_NATIVE","selection-real-session-fixture"});
    }
    auto presence=std::make_shared<SharedWorldPresence>(characters);
    NativeSkillCatalog catalog(raw);
    auto source=SharedTaiwanOwnedDeitySkillSource::create(presence,companions,catalog,
        SharedTaiwanOwnedDeitySkillSource::Mode::SelectionPublicationRequired,2);
    std::optional<SharedTaiwanOwnedDeitySkillSource::WrittenSelectionSource> previous;
    unsigned callbacks=0;bool pending_rejected=false,old_retired=false;
    constexpr std::uint16_t actor=0x345;
    RecoveredSessionPeer peer(false,[&](Session& session,auto records)->std::optional<std::vector<std::uint8_t>> {
        std::vector<std::uint8_t> keys;
        for(const auto& record:records) {
            const auto* selected=std::get_if<RecoveredDeitySelection::Request>(&record);
            require(selected!=nullptr,"Selection fixture accepted a non-C67 input");keys.push_back(selected->key);
        }
        auto callback=source->begin_selection_callback(session,keys);
        require(callback.has_value(),"Actual selection callback was not captured");
        if(previous)old_retired=!previous->current(session);
        std::vector<std::uint8_t> reply;
        for(const auto key:keys) {
            auto wire=source->select_deity_for_callback(session,helper,{key});
            require(wire.has_value(),"Actual private selection failed");reply.insert(reply.end(),wire->begin(),wire->end());
        }
        require(source->selection_response_matches(session,*callback,reply),"Ordered private S31 components did not match whole reply");
        const auto write=session.observe_world_response(reply);
        session.hold_world_input_until_response_written(write);
        source->publish_selection_callback(session,*callback,write);
        pending_rejected=!source->observe_selection_publication(session);
        source->abandon_selection_callback(*callback);++callbacks;return reply;
    },character,4740,actor);
    const auto lease=presence->prepare(peer.session->id(),RecoveredSessionPeer::account,character,actor,position);
    require(lease&&presence->activate(*lease,actor),"Actual common selection lease missing");
    peer.common_source_generation=lease->generation;
    peer.select(false);peer.send(RecoveredSessionPeer::tail(actor));peer.silent();
    const auto expected=[&](std::initializer_list<std::uint8_t> keys) {
        std::vector<std::uint8_t> wire;
        for(const auto key:keys) {
            RecoveredDeityState::Status::Bytes status{0x31,key,1};
            const auto frame=RecoveredWorldFrame::encode(status);wire.insert(wire.end(),frame.begin(),frame.end());
        }
        return wire;
    };
    peer.send(RecoveredWorldFrame::encode(std::array<std::uint8_t,4>{0x67,101,0x67,102}));
    peer.expect(expected({101,102}));peer.silent();
    previous=source->observe_selection_publication(*peer.session);
    require(previous&&pending_rejected&&callbacks==1&&previous->current(*peer.session),"Pending selection minted early or whole Written failed");
    require(previous->publications().size()==2&&previous->publications()[0].committed().after().key==101&&
        previous->publications()[1].committed().after().key==102&&
        previous->publications()[1].committed().before()==std::optional{previous->publications()[0].committed().after()}&&
        previous->response().wire()==expected({101,102}),"Consecutive C67 private commits/order/history were truncated to last");
    const auto old=*previous;
    const auto account=peer.session->account_id;
    peer.session->account_id^=std::uint64_t{1}<<32;
    require(!old.current(*peer.session),"Selection source narrowed account identity");peer.session->account_id=account;
    peer.session->character_id^=std::uint64_t{1}<<32;
    require(!old.current(*peer.session),"Selection source narrowed character identity");peer.session->character_id=character;
    RecoveredSessionPeer foreign(false,[](Session&,auto)->std::optional<std::vector<std::uint8_t>>{return std::vector<std::uint8_t>{};},
        character,4741,actor);
    foreign.select(false);foreign.send(RecoveredSessionPeer::tail(actor));foreign.silent();
    require(!old.current(*foreign.session)&&!source->observe_selection_publication(*foreign.session),
        "Another Session/normal-init borrowed equal-owner selection bytes");
    peer.send(RecoveredWorldFrame::encode(std::array<std::uint8_t,2>{0x67,101}));
    peer.expect(expected({101}));peer.silent();
    const auto fresh=source->observe_selection_publication(*peer.session);
    require(fresh&&old_retired&&!old.current(*peer.session)&&!fresh->same_source(old)&&
        fresh->publications().size()==1&&fresh->publications().front().committed().before()==
            std::optional{old.publications().back().committed().after()},"New selection revived old token or lost the prior commit boundary");
    previous=*fresh;
    peer.send(RecoveredWorldFrame::encode(std::array<std::uint8_t,2>{0x67,101}));
    peer.expect(expected({101}));peer.silent();
    const auto equal_bytes=source->observe_selection_publication(*peer.session);
    require(equal_bytes&&old_retired&&!fresh->current(*peer.session)&&!equal_bytes->same_source(*fresh)&&
        equal_bytes->response().wire()==fresh->response().wire()&&
        !equal_bytes->publications().front().committed().changed()&&
        equal_bytes->publications().front().committed().after()==fresh->publications().front().committed().after(),
        "Idempotent equal-byte S31 revived the old occurrence or changed saved revision");
    source->release_selection(*peer.session);
    require(!equal_bytes->current(*peer.session)&&!source->observe_selection_publication(*peer.session),"Released selection occurrence survived");
}

void recovered_character_idle_tick_transport() {
    const auto tick=RecoveredWorldFrame::encode(std::array<std::uint8_t,2>{0x30,0});
    require(tick==std::vector<std::uint8_t>({5,0,0x2d,0x2d,0x22}),
            "Native character idle tick wire changed");
    std::array<std::uint8_t,38> request{};request[0]=0x1a;request[34]=4;
    const auto selection=RecoveredWorldFrame::encode(request);
    {
        RecoveredSessionPeer peer(true);peer.authenticate(false);
        peer.send(std::span(tick).first(2));peer.silent();
        peer.send(std::span(tick).subspan(2));peer.silent();
        peer.send(selection);
        peer.expect(RecoveredCharacterCreateResult::committed_success());peer.expect(peer.world_frame);
        require(peer.selection_calls==1 && peer.session->state()==SessionState::CharacterSelected,
                "Delayed character selection lost binding after idle tick");
        peer.send(RecoveredSessionPeer::tail());peer.silent();
        require(peer.ready_calls==1,"Delayed selection lost world initializer");
    }
    {
        RecoveredSessionPeer peer(true);peer.authenticate(false);
        std::vector<std::uint8_t> together=tick;
        together.insert(together.end(),tick.begin(),tick.end());
        together.insert(together.end(),selection.begin(),selection.end());
        peer.send(together);
        peer.expect(RecoveredCharacterCreateResult::committed_success());peer.expect(peer.world_frame);
        require(peer.selection_calls==1,"Coalesced ticks and selection selected more than once");
    }
    for(bool checksum_bad:{false,true}) {
        RecoveredSessionPeer peer(true);peer.authenticate(false);
        auto bad=checksum_bad?tick:RecoveredWorldFrame::encode(std::array<std::uint8_t,2>{0x31,0});
        if(checksum_bad) bad.back()^=1;
        peer.send(bad);peer.closed();
        require(peer.selection_calls==0,"Invalid character idle tick selected a character");
    }
}

// These fixtures exercise actual Session append_write, paused held output and
// its original full-write callback. They establish sender custody only, never
// client R0 adoption or the eventual native meaning of an InBattle output.
std::vector<std::uint8_t> sender_pk_fixture(std::uint16_t own_actor) {
    std::vector<std::uint8_t> out;
    const auto append=[&](const auto& bytes){out.insert(out.end(),bytes.begin(),bytes.end());};
    std::array<std::uint8_t,9> context{0x82};context[1]=1;append(context);
    for(const std::uint8_t position:{0,14}) {
        std::array<std::uint8_t,17> appearance{0x86,4};appearance[2]=position;appearance[3]=1;append(appearance);
    }
    for(const std::uint8_t position:{0,14}) {
        std::array<std::uint8_t,45> identity{0x1c};identity[1]=position;identity[2]=1;
        const auto actor=static_cast<std::uint16_t>(own_actor+(position?1:0));
        identity[3]=static_cast<std::uint8_t>(actor);identity[4]=static_cast<std::uint8_t>(actor>>8);
        identity[6]=0x20;append(identity);
        std::array<std::uint8_t,17> hp{0x86};hp[2]=position;hp[5]=100;hp[9]=80;append(hp);
        if(!position){auto mp=hp;mp[1]=1;mp[5]=20;mp[9]=10;append(mp);}
    }
    std::array<std::uint8_t,121> bulk{0x88};bulk[1]=1;bulk[5]=80;bulk[9]=10;append(bulk);
    return out;
}
struct SenderPkOwner final:Session::NativePkEntryOwner {
    std::optional<Session::NativePkEntryHold> held;
    unsigned held_calls=0,written_calls=0;
    bool whole_written=false;
    void native_pk_entry_held(Session&,std::optional<Session::NativePkEntryHold> value)override{
        ++held_calls;held=std::move(value);
    }
    bool native_pk_entry_written(Session&,const Session::NativePkEntryHold&,bool value)override{
        ++written_calls;whole_written=value;return true;
    }
};
Session::NativePkEntryRequest sender_pk_request(RecoveredSessionPeer& peer,
        const Session::NormalWorldInitialization& init,std::uint16_t actor) {
    return {RecoveredSessionPeer::account,peer.selected_character,RecoveredSessionPeer::common_generation,
        RecoveredSessionPeer::world_generation,peer.session->battle_generation(),init.entry_frame(),
        init.entry_logical(),init.accepted_tail(),init.config_flag(),sender_pk_fixture(actor)};
}
void recovered_world_identity_sender_transport() {
    constexpr std::uint16_t actor=0x345;
    constexpr std::uint64_t wide_character=(std::uint64_t{1}<<40)|0x1234;
    const auto probe=RecoveredWorldFrame::encode(std::array<std::uint8_t,5>{0x25,1,0,0,0});
    const auto initialize=[&](RecoveredSessionPeer& peer,std::optional<Session::NormalWorldInitialization>& init){
        peer.select(false);peer.send(RecoveredSessionPeer::tail(actor));peer.silent();
        peer.send(probe);peer.silent();
        require(init&&init->qualified_scene_identity()&&init->entry_written()&&init->world_identity_sender_current(),
            "Actual qualified original2A full write did not establish sender custody");
        require(peer.session->character_id==wide_character&&peer.session->normal_world_initialization_current_on_game(*init),
            "Native scene handle narrowed full character ownership or replaced initialization");
    };
    const auto capture=[](std::optional<Session::NormalWorldInitialization>& init){
        return [&init](Session& s,auto)->std::optional<std::vector<std::uint8_t>>{
            const auto current=s.normal_world_initialization();
            require(current&&s.normal_world_initialization_current(*current),"Original callback lost NormalInit");
            if(init)require(init->same_initialization(*current),"Sender metadata replaced the original initialization");
            init=current;return std::vector<std::uint8_t>{};
        };
    };
    // Unknown or incomplete native records remain unchanged output; only the
    // separate sender qualification is revoked, not whole NormalInit Current.
    for(const unsigned conflict:{0u,1u,2u,3u}) {
        std::optional<Session::NormalWorldInitialization> init;
        RecoveredSessionPeer peer(false,capture(init),wide_character,200+conflict,actor);initialize(peer,init);
        const auto original_frame=init->entry_frame();const auto original_logical=init->entry_logical();
        const auto original_tail=init->accepted_tail();const auto original_config=init->config_flag();
        auto logical=sender_pk_fixture(actor);
        if(conflict==0)logical.insert(logical.end(),original_logical.begin(),original_logical.end());
        else if(conflict==1){std::array<std::uint8_t,177> cf{0xcf};logical.insert(logical.end(),cf.begin(),cf.end());}
        else if(conflict==2)logical.push_back(0xfe);
        else logical.push_back(0xcf); // Valid envelope with truncated native record.
        peer.session->send_world_records(logical);peer.expect(RecoveredWorldFrame::encode(logical));peer.silent();
        require(!init->world_identity_sender_current()&&peer.session->normal_world_initialization_current_on_game(*init)&&
            init->entry_frame()==original_frame&&init->entry_logical()==original_logical&&
            init->accepted_tail()==original_tail&&init->config_flag()==original_config&&init->entry_written(),
            "Conflicting sender changed original bytes/profile or retired whole NormalInit");
        peer.send(probe);peer.silent();
        require(!init->world_identity_sender_current(),"A later callback revived stale sender custody");
        auto owner=std::make_shared<SenderPkOwner>();bool rejected=false;
        try{(void)peer.session->prepare_native_pk_entry(sender_pk_request(peer,*init,actor),owner);}
        catch(const std::exception&){rejected=true;}
        require(rejected,"A qualified PK prepare reused revoked original2A sender custody");
    }
    for(const bool conflict_while_held:{false,true}) {
        std::optional<Session::NormalWorldInitialization> init;
        RecoveredSessionPeer peer(false,capture(init),wide_character,210+conflict_while_held,actor);initialize(peer,init);
        const auto safe=sender_pk_fixture(actor);
        peer.session->send_world_records(safe);peer.expect(RecoveredWorldFrame::encode(safe));peer.silent();
        std::array<std::uint8_t,17> grant{0x86,5,0,1,2};
        peer.session->send_world_records(std::vector<std::uint8_t>(grant.begin(),grant.end()));
        peer.expect(RecoveredWorldFrame::encode(grant));peer.silent();
        require(init->world_identity_sender_current(),"Normal1C/86-5 or complete PK bootstrap self-revoked sender");
        auto owner=std::make_shared<SenderPkOwner>();auto request=sender_pk_request(peer,*init,actor);
        for(const bool character_field:{false,true}){
            auto wrong=request;bool rejected=false;
            if(character_field)wrong.character^=std::uint64_t{1}<<32;
            else wrong.account^=std::uint64_t{1}<<32;
            try{(void)peer.session->prepare_native_pk_entry(std::move(wrong),owner);}
            catch(const std::exception&){rejected=true;}
            require(rejected&&init->world_identity_sender_current(),"PK owner comparison narrowed64-bit identity");
        }
        const auto pending=peer.session->prepare_native_pk_entry(request,owner);
        for(unsigned spin=0;spin<200&&!owner->held;++spin)peer.pump();
        require(owner->held&&*owner->held==pending&&owner->held_calls==1&&
            peer.session->native_pk_entry_current(*owner->held)&&init->world_identity_sender_current(),
            "Actual held bootstrap bypassed source custody or revoked itself");
        peer.silent(); // Held FIFO has not released a single bootstrap byte.
        if(conflict_while_held){
            const auto conflicting=init->entry_logical();
            peer.session->send_world_records(conflicting);peer.silent();
            require(!init->world_identity_sender_current()&&!peer.session->native_pk_entry_current(*owner->held)&&
                !peer.session->commit_native_pk_entry(*owner->held)&&
                peer.session->normal_world_initialization_current_on_game(*init),
                "Conflict was deferred until socket completion or preserved the precommit hold");
            peer.session->abort_native_pk_entry(*owner->held);
            peer.expect(RecoveredWorldFrame::encode(conflicting));peer.silent();
            require(!init->world_identity_sender_current()&&owner->written_calls==1&&!owner->whole_written,
                "Cancellation of held output restored revoked sender custody");
        }else{
            require(peer.session->commit_native_pk_entry(*owner->held)&&
                peer.session->native_pk_entry_committed_current(*owner->held),"Actual held PK transition failed");
            peer.session->release_native_pk_entry(*owner->held);
            peer.expect(RecoveredWorldFrame::encode(request.logical));peer.silent();
            require(owner->written_calls==1&&owner->whole_written&&
                peer.session->native_pk_entry_written_current(*owner->held)&&init->world_identity_sender_current(),
                "PK commit/release/full write self-revoked its original sender custody");
            std::array<std::uint8_t,177> cf{0xcf};
            peer.session->send_world_records(std::vector<std::uint8_t>(cf.begin(),cf.end()));
            peer.expect(RecoveredWorldFrame::encode(cf));peer.silent();
            require(!init->world_identity_sender_current()&&peer.session->native_pk_entry_written_current(*owner->held),
                "Unknown future-world output phase revived custody or destroyed the committed hold");
        }
    }
    for(const bool in_battle:{false,true}){
        std::optional<Session::NormalWorldInitialization> init;
        RecoveredSessionPeer peer(false,capture(init));
        peer.select(false);peer.send(RecoveredSessionPeer::tail());peer.silent();peer.send(probe);peer.silent();
        require(init&&init->world_identity_sender_current()&&peer.session->state()==SessionState::CharacterSelected,
            "Actual Selected original sender was never established");
        if(in_battle)peer.session->set_state(SessionState::InBattle); // Transport phase fixture only.
        peer.session->send_world_records(init->entry_logical());peer.expect(init->entry_frame());peer.silent();
        require(!init->world_identity_sender_current(),
            "Selected/InBattle output phase incorrectly exempted later2A sender conflict");
    }
}

void recovered_battle_self_view_transport() {
    constexpr std::uint16_t actor=0x345;
    constexpr std::uint64_t character=(std::uint64_t{1}<<40)|0x1234;
    const auto probe=RecoveredWorldFrame::encode(std::array<std::uint8_t,5>{0x25,1,0,0,0});
    const std::array<std::uint8_t,17> primary{0x86,5,0,1,0};
    const auto grant=RecoveredWorldFrame::encode(primary);
    const auto bootstrap=[&]{
        std::vector<std::uint8_t> logical;
        const auto append=[&](const auto& bytes){logical.insert(logical.end(),bytes.begin(),bytes.end());};
        append(std::array<std::uint8_t,9>{0x82});
        for(const std::uint8_t position:{0,1,14}){
            std::array<std::uint8_t,45> identity{0x1c};identity[1]=position;identity[2]=1;identity[6]=0x20;
            identity[3]=static_cast<std::uint8_t>(actor+position);identity[4]=static_cast<std::uint8_t>((actor+position)>>8);append(identity);
            std::array<std::uint8_t,17> hp{0x86};hp[2]=position;hp[5]=120;hp[9]=position==1?50:100;append(hp);
            if(position<14){auto mp=hp;mp[1]=1;mp[5]=30;mp[9]=position==1?12:20;append(mp);}
        }
        std::array<std::uint8_t,121> bulk{0x88};bulk[1]=1;bulk[5]=100;bulk[9]=20;bulk[13]=50;bulk[17]=12;
        append(bulk);append(primary);return RecoveredWorldFrame::encode(logical);
    }();
    const std::array<BattleActor,3> actors{{{0,character,100,120,20,30,10,10,10,10},
        {1,character,50,120,12,30,10,10,10,10},{14,0,100,120,0,0,10,10,10,10}}};
    const auto effect=[](std::uint8_t target,std::uint8_t outcome,std::uint8_t selector=9){
        RecoveredBattleDelta::Bytes raw{0x83,13,0};raw[5+2*(target/14)]=static_cast<std::uint8_t>(1u<<(target%14));
        raw[9]=0xfe;raw[10]=0xff;raw[11]=1;raw[13]=selector;raw[14]=outcome;return raw;
    };
    const auto encode=[](const BattleSnapshot&,auto entries){
        const auto prime=diagnostic_battle_basic_animation(0,14,0,0,true);
        std::vector<std::uint8_t> logical(prime.begin(),prime.end());
        for(const auto& entry:entries){const auto raw=RecoveredBattleDelta::encode(entry);logical.insert(logical.end(),raw.begin(),raw.end());}
        const auto close=diagnostic_battle_basic_animation(14,0,0,1,true);logical.insert(logical.end(),close.begin(),close.end());
        return RecoveredWorldFrame::encode(logical);
    };
    for(const std::uint8_t outcome:{0,28,255}){
        RecoveredBattleService service([](const CombatRuleInput& input){return CombatRuleResult{1,input.mp_cost,false};});
        RecoveredBattleService::Policy policy{0,0,0,0,{0,{14},false,100,100,0,0,150},{}};
        unsigned commits=0;bool bootstrapped=false;
        const auto checkpoint=[&](const BattleCheckpoint& before,const BattleCheckpoint& after){
            require(before.random_state==after.random_state,"Native self-view effects changed RNG");++commits;
        };
        const auto bind=[&](Session& session){
            service.bind(session,Battle(2000+outcome+session.battle_generation(),actors,123),policy,
                [](const auto&,const auto&){return RecoveredWorldFrame::encode(std::array<std::uint8_t,2>{0x85,0});},
                {},checkpoint);
        };
        RecoveredSessionPeer peer(false,[&](Session& session,auto)->std::optional<std::vector<std::uint8_t>>{
            if(!bootstrapped){session.set_state(SessionState::InBattle);bind(session);bootstrapped=true;return bootstrap;}
            return grant; // A fresh actual game callback, not a generic slot setter.
        },character,500+outcome,actor);
        peer.select(false);peer.send(RecoveredSessionPeer::tail(actor));peer.silent();peer.send(probe);peer.expect(bootstrap);peer.silent();
        auto view=peer.session->battle_self_view();
        require(view&&view->primary_slot()==0&&peer.session->battle_self_view_current(*view),
            "Actual full Written bootstrap did not supply its primary self-view");
        const auto initial=service.inspect(peer.session->id());
        const auto rejected=[&](auto action){bool failed=false;try{action();}catch(const std::exception&){failed=true;}
            require(failed&&service.inspect(peer.session->id())==initial&&!commits,
                "Unqualified self-view result published state or persistence");};
        const std::array nonself{*RecoveredBattleDelta::parse(effect(1,255))};
        rejected([&]{service.apply_native_deltas(*peer.session,1,nonself,encode);});
        for(const auto raw:{effect(0,255),effect(1,255,0),effect(1,255,20)}){
            const std::array entries{*RecoveredBattleDelta::parse(raw)};
            rejected([&]{service.apply_native_deltas(*peer.session,1,entries,encode,view);});
        }
        auto kind=effect(1,255);kind[11]=2;const std::array kinds{*RecoveredBattleDelta::parse(kind)};
        rejected([&]{service.apply_native_deltas(*peer.session,1,kinds,encode,view);});
        auto wrong_source=effect(1,255);wrong_source[2]=1;
        const std::array wrong{*RecoveredBattleDelta::parse(wrong_source)};
        rejected([&]{service.apply_native_deltas(*peer.session,1,wrong,encode,view);});
        const std::array mixed{nonself.front(),*RecoveredBattleDelta::parse(effect(0,255))};
        rejected([&]{service.apply_native_deltas(*peer.session,1,mixed,encode,view);});
        if(outcome==255){
            bool foreign_bootstrap=false;
            RecoveredSessionPeer foreign(false,[&](Session& session,auto)->std::optional<std::vector<std::uint8_t>>{
                if(!foreign_bootstrap){session.set_state(SessionState::InBattle);foreign_bootstrap=true;return bootstrap;}return grant;
            },character,900,actor);
            foreign.select(false);foreign.send(RecoveredSessionPeer::tail(actor));foreign.silent();foreign.send(probe);
            foreign.expect(bootstrap);foreign.silent();const auto other=foreign.session->battle_self_view();
            require(other&&!peer.session->battle_self_view_current(*other),"Another Session's Written grant borrowed this view");
            rejected([&]{service.apply_native_deltas(*peer.session,1,nonself,encode,other);});
            const auto account=peer.session->account_id;peer.session->account_id^=std::uint64_t{1}<<32;
            require(!peer.session->battle_self_view_current(*view),"Self-view narrowed account identity");peer.session->account_id=account;
            peer.session->character_id^=std::uint64_t{1}<<32;
            require(!peer.session->battle_self_view_current(*view),"Self-view narrowed character identity");peer.session->character_id=character;
            // A generic equal-byte grant is not the original accepted callback source.
            peer.session->send_world_records(std::vector<std::uint8_t>(primary.begin(),primary.end()));peer.expect(grant);peer.silent();
            require(!peer.session->battle_self_view_current(*view)&&!peer.session->battle_self_view(),
                "An unowned generic grant minted or revived a view");
            rejected([&]{service.apply_native_deltas(*peer.session,1,nonself,encode,view);});
            peer.send(probe);peer.expect(grant);peer.silent();view=peer.session->battle_self_view();
            require(view&&peer.session->battle_self_view_current(*view),"Fresh original callback failed to qualify a new occurrence");
            std::array<std::uint8_t,45> identity{0x1c};
            peer.session->send_world_records(std::vector<std::uint8_t>(identity.begin(),identity.end()));
            peer.expect(RecoveredWorldFrame::encode(identity));peer.silent();
            require(!peer.session->battle_self_view_current(*view),"Later identity writer preserved a stale self-view");
            peer.send(probe);peer.expect(grant);peer.silent();view=peer.session->battle_self_view();
            require(view.has_value(),"Fresh primary source after invalidation remained unavailable");
            // Fault injection: the writer has been posted, but its strand has
            // not run yet. It will precede any returned native result on wire.
            auto next_primary=primary;next_primary[4]=1;
            rejected([&]{service.apply_native_deltas(*peer.session,1,nonself,[&](const auto& state,auto entries){
                peer.session->send_world_records(std::vector<std::uint8_t>(next_primary.begin(),next_primary.end()));
                return encode(state,entries);
            },view);});
            require(!peer.session->battle_self_view_current(*view),"Posted writer left an old nonself view current");
            peer.expect(RecoveredWorldFrame::encode(next_primary));peer.silent();
            peer.send(probe);peer.expect(grant);peer.silent();view=peer.session->battle_self_view();
            require(view.has_value(),"Original callback after posted writer did not refresh its view");
            // Fault injection: a user encoder changes the phase after staging.
            rejected([&]{service.apply_native_deltas(*peer.session,1,nonself,[&](const auto& state,auto entries){
                auto wire=encode(state,entries);peer.session->set_state(SessionState::InWorld);return wire;
            },view);});
            require(!peer.session->battle_self_view_current(*view),"Leaving battle did not retire the view occurrence");
            peer.session->set_state(SessionState::InBattle);peer.send(probe);peer.expect(grant);peer.silent();
            view=peer.session->battle_self_view();require(view.has_value(),"New battle generation lacked its new grant source");
            rejected([&]{service.apply_native_deltas(*peer.session,1,nonself,encode,view);});
            service.remove(peer.session->id());bind(*peer.session); // Explicitly bind this new generation.
        }
        const std::array entries{*RecoveredBattleDelta::parse(effect(1,outcome))};
        const auto wire=service.apply_native_deltas(*peer.session,1,entries,encode,view);
        const auto decoded=RecoveredWorldFrame::decode(wire);
        const auto& after=service.inspect(peer.session->id());
        require(decoded&&decoded->size()==45&&after.revision==2&&after.actors[1]->mp==10&&
            after.actors[0]->mp==20&&after.actors[0]->hp==100&&after.actors[1]->hp==50&&
            after.actors[14]->hp==100&&commits==1,
            "Current nonself view lost exact friendly MP effect, framing or single atomic commit");
        service.remove(peer.session->id());
    }
}

void recovered_world_push_transport() {
    const std::vector<std::uint8_t> remove{0x73,7,0,0,0};
    {
        RecoveredSessionPeer peer(true);peer.select(false);
        peer.session->send_world_records(remove);
        peer.closed();
        require(peer.ready_calls==0,"World push bypassed initialization tail");
    }
    {
        RecoveredSessionPeer first(true),second(true);
        first.select(false);second.select(false);
        first.send(RecoveredSessionPeer::tail());first.silent();
        second.send(RecoveredSessionPeer::tail());second.silent();
        auto next=remove;next[1]=8;
        first.session->send_world_records(remove);
        first.session->send_world_records(next);
        first.expect(RecoveredWorldFrame::encode(remove));
        first.expect(RecoveredWorldFrame::encode(next));
        second.silent();
        second.session->send_world_records(next);
        second.expect(RecoveredWorldFrame::encode(next));
        first.silent();
        first.send(RecoveredMovement::encode({18,14,3,0}));
        first.expect(RecoveredMovement::ack(3));
        require(first.movement_calls==1,"World push broke subsequent movement handling");
        first.session->close();first.closed();
        first.session->send_world_records(remove);first.pump();
        second.silent();
    }
    for(const auto size:{std::size_t{0},RecoveredWorldFrame::max_logical_size+1}) {
        RecoveredSessionPeer peer(true);peer.select(false);
        peer.send(RecoveredSessionPeer::tail());peer.silent();
        peer.session->send_world_records(std::vector<std::uint8_t>(size,0x73));
        peer.closed();
    }
}

void recovered_visibility_transport() {
    RecoveredSessionPeer first(true,{},7,101),second(true,{},8,102),outside(true,{},9,103);
    std::array<std::uint8_t,40> outside_profile{};
    outside.world_frame=RecoveredWorldEntry::wire(9,outside_profile,17,13,2,4,2);
    const std::array peers{&first,&second,&outside};
    for(auto* peer:peers) {
        peer->select(false);
        peer->send(RecoveredSessionPeer::tail(static_cast<std::uint16_t>(peer->selected_character)));
        peer->silent();
    }
    RecoveredVisibility registry;
    const auto presence=[](RecoveredSessionPeer& peer) {
        const auto spawn=RecoveredRemoteActor::parse_logical(DiagnosticRemoteActor::logical(0,0)).value();
        const auto remove=RecoveredRemoteActorRemove::parse_logical(DiagnosticRemoteActor::logical(2,0)).value();
        std::array<std::uint8_t,40> profile{};
        profile[0]=static_cast<std::uint8_t>('A'+peer.selected_character);
        profile[29]=1;profile[31]=1;
        return RecoveredPlayerPresence::from_world_entry(peer.session->id(),peer.session->account_id,
            peer.session->character_id,peer.world_frame,profile,spawn,remove);
    };
    const auto deliver=[&](std::vector<RecoveredVisibility::Delivery> deliveries) {
        for(auto& delivery:deliveries) {
            const auto found=std::find_if(peers.begin(),peers.end(),[&](const auto* peer) {
                return peer->session->id()==delivery.recipient;
            });
            require(found!=peers.end(),"Visibility routed to unknown session");
            (*found)->session->send_world_records(std::move(delivery.logical));
        }
    };
    const auto a=presence(first),b=presence(second),c=presence(outside);
    deliver(registry.enter(a));deliver(registry.enter(c));
    for(auto* peer:peers) peer->silent();
    deliver(registry.enter(b));
    first.expect(RecoveredWorldFrame::encode(RecoveredRemoteActor::encode_logical(b.spawn)));
    second.expect(RecoveredWorldFrame::encode(RecoveredRemoteActor::encode_logical(a.spawn)));
    for(auto* peer:peers) peer->silent();
    auto logical=DiagnosticRemoteActor::logical(1,0);
    logical[9]=18;
    const auto outward=RecoveredRemoteActorMove::parse_logical(logical).value();
    logical[9]=17;logical[10]=13<<3;
    const auto back=RecoveredRemoteActorMove::parse_logical(logical).value();
    const std::array path{outward,back};
    deliver(registry.move_batch(first.session->id(),first.session->account_id,
        first.session->character_id,{2,15},path));
    for(const auto& step:path)
        second.expect(RecoveredWorldFrame::encode(RecoveredRemoteActorMove::encode_logical(step)));
    for(auto* peer:peers) peer->silent();
    for(const bool active:{true,false,true}) {
        deliver(registry.set_fight_title(first.session->id(),first.session->account_id,
            first.session->character_id,{2,15},active));
        auto expected=RecoveredRemoteActorMove::encode_logical(back);
        expected[5]=static_cast<std::uint8_t>(active);
        second.expect(RecoveredWorldFrame::encode(expected));
        for(auto* peer:peers) peer->silent();
        deliver(registry.set_fight_title(first.session->id(),first.session->account_id,
            first.session->character_id,{2,15},active));
        for(auto* peer:peers) peer->silent();
    }
    first.session->close();first.closed();
    // The test invokes disconnect cleanup explicitly; Application wiring is separate.
    deliver(registry.leave(first.session->id()));
    second.expect(RecoveredWorldFrame::encode(RecoveredRemoteActorRemove::encode_logical(a.departure)));
    deliver(registry.leave(first.session->id()));
    second.silent();outside.silent();
    require(!registry.contains(first.session->id()) && registry.size()==2,
        "Disconnected visibility membership survived cleanup");
}

void recovered_runtime_without_scalar_replay() {
    for(bool created:{false,true}) for(bool movement:{false,true}) {
        RecoveredSessionPeer peer(movement);
        peer.select(created);
        const auto tail=RecoveredSessionPeer::tail();
        const auto move=RecoveredMovement::encode({18,14,3,0});
        if(created && movement) {
            auto combined=tail;
            combined.insert(combined.end(),move.begin(),move.end());
            peer.send(combined);
            peer.expect(RecoveredMovement::ack(3));
        } else {
            // No response for a partial checksum, nor for the completed tail.
            peer.send(std::span(tail).first(tail.size()-1));
            peer.silent();
            require(peer.ready_calls==0,"Incomplete tail advanced state");
            peer.send(std::span(tail).last(1));
            peer.silent();
            if(movement) { peer.send(move);peer.expect(RecoveredMovement::ack(3)); }
        }
        peer.silent();
        require(peer.session->state()==SessionState::CharacterSelected,"Tail invented InWorld state");
        require(peer.ready_calls==(movement?1u:0u) && peer.movement_calls==(movement?1u:0u),
                "World-ready/movement continuation changed");
        peer.send(tail);peer.closed();
    }
    for(bool bad_checksum:{false,true}) {
        RecoveredSessionPeer peer(true);peer.select(false);
        auto tail=RecoveredSessionPeer::tail();
        if(bad_checksum) tail.back()^=1;
        else tail=RecoveredWorldFrame::encode(std::array<std::uint8_t,9>{0x1f,0,0x23,0,0x1c,0x35,0x12,1,0});
        peer.send(tail);peer.closed();
        require(peer.ready_calls==0 && peer.movement_calls==0,"Invalid tail reached world handlers");
    }
}

void recovered_world_service_transport() {
    unsigned moves=0;
    RecoveredWorldService service([&](Session& session, auto requests) {
        require(session.state()==SessionState::CharacterSelected,
                "Routing invented a world state transition");
        require(requests.size()==1 && requests[0].x==18 && requests[0].y==14,
                "Service lost decoded movement");
        ++moves;
        const auto ack=RecoveredMovement::ack(requests[0].sequence);
        return std::vector<std::uint8_t>(ack.begin(),ack.end());
    });
    RecoveredSessionPeer peer(false,[&](Session& session,auto records) {
        return service.handle(session,records);
    });
    peer.select(false);
    auto joined=RecoveredSessionPeer::tail();
    const auto move=RecoveredMovement::encode({18,14,3,0});
    joined.insert(joined.end(),move.begin(),move.end());
    peer.send(joined);peer.expect(RecoveredMovement::ack(3));peer.silent();
    require(moves==1 && peer.ready_calls==1,"Tail/movement service bridge failed");
    peer.send(RecoveredWorldFrame::encode(std::array<std::uint8_t,2>{0x30,0}));
    peer.silent();
    const std::array<std::uint8_t,12> invalid{
        0x2e,18,0,14,0,3,0,0x86,0,0,0,0};
    peer.send(RecoveredWorldFrame::encode(invalid));peer.closed();
    require(moves==1,"Rejected service batch committed movement prefix");
}

void recovered_world_record_routing() {
    using Records=RecoveredWorldRecords;
    // A synthetic policy supplies responses solely to test the actual socket
    // route. These responses establish no original item or quest operation.
    const auto ack=RecoveredMovement::ack(3);
    const std::vector<std::uint8_t> reply(ack.begin(),ack.end());
    const std::array<std::uint8_t,26> logical{
        0x85,0x34,0x12,2,0,0x9a,0xa5,
        0x30,0,
        0x25,0x78,0x56,0xff,0x81,
        0x2e,18,0,14,0,3,0xfe,
        0x86,0xef,0xbe,0,0x10};
    const auto wire=RecoveredWorldFrame::encode(logical);
    const auto check=[](std::span<const Records::Record> records) {
        require(records.size()==5,"World record count changed");
        require(std::holds_alternative<RecoveredQuestAction::Request>(records[0]) &&
                std::holds_alternative<Records::Tick>(records[1]) &&
                std::holds_alternative<RecoveredInventoryItemRequest::Request>(records[2]) &&
                std::holds_alternative<RecoveredMovement::Request>(records[3]) &&
                std::holds_alternative<RecoveredQuestClose::Request>(records[4]),
                "World records reordered or reinterpreted");
        const auto& item=std::get<RecoveredInventoryItemRequest::Request>(records[2]);
        const auto& quest=std::get<RecoveredQuestAction::Request>(records[0]);
        require(quest.request_word==0x1234 && quest.reply_word==2 &&
                quest.context_byte==0x9a && quest.opaque_tail==0xa5,
                "Quest action lost opaque fields");
        require(item.client_item_id==0x5678 && item.raw_slot==0xff && item.raw_tail==0x81,
                "Item request lost raw fields");
        const auto& move=std::get<RecoveredMovement::Request>(records[3]);
        require(move.x==18 && move.y==14 && move.sequence==3 && move.opaque_tail==0xfe,
                "Movement request lost raw fields");
        const auto& close=std::get<RecoveredQuestClose::Request>(records[4]);
        require(close.source_low_word==0xbeef && close.this_high_word==0x1000,
                "Close request lost source/pointer residue");
    };
    for(std::size_t split=1;split<wire.size();++split) {
        RecoveredSessionPeer peer(false,[&](Session&,auto records) {
            check(records);return std::optional(reply);
        });
        peer.select(false);peer.send(RecoveredSessionPeer::tail());peer.silent();
        peer.send(std::span(wire).first(split));peer.silent();
        require(peer.world_calls==0,"Partial world envelope dispatched");
        peer.send(std::span(wire).subspan(split));peer.expect(reply);
        require(peer.world_calls==1 && peer.movement_calls==0,"Wrong world handler selected");
        peer.silent();
    }
    {
        RecoveredSessionPeer peer(false,[&](Session&,auto records) {
            check(records);auto response=reply;
            response.insert(response.end(),reply.begin(),reply.end());
            return std::optional(response);
        });
        peer.select(true);
        auto combined=RecoveredSessionPeer::tail();
        combined.insert(combined.end(),wire.begin(),wire.end());
        peer.send(combined);peer.expect(reply);peer.expect(reply);
        require(peer.world_calls==1,"Coalesced tail consumed world records");
        peer.silent();
    }
    {
        std::size_t handled=0;
        RecoveredSessionPeer peer(false,[&](Session&,auto records) {
            require(records.size()%5==0,"Coalesced frame split a logical record");
            std::vector<std::uint8_t> response;
            for(std::size_t at=0;at<records.size();at+=5) {
                check(records.subspan(at,5));++handled;
                response.insert(response.end(),reply.begin(),reply.end());
            }
            return std::optional(response);
        });
        peer.select(false);peer.send(RecoveredSessionPeer::tail());peer.silent();
        auto combined=wire;combined.insert(combined.end(),wire.begin(),wire.end());
        peer.send(combined);peer.expect(reply);peer.expect(reply);peer.silent();
        require(handled==2 && peer.world_calls==2,
                "Independent coalesced world frames were merged into one policy transaction");
    }
    {
        // TCP grouping must not turn two complete native frames into a mixed
        // policy request. A single logical frame still retains its own batch.
        RecoveredSessionPeer peer(false,[](Session&,auto records)
                ->std::optional<std::vector<std::uint8_t>> {
            if(records.size()!=1) return std::nullopt;
            if(std::holds_alternative<RecoveredMovement::Request>(records[0])) {
                const auto ack=RecoveredMovement::ack(3);
                return std::vector<std::uint8_t>(ack.begin(),ack.end());
            }
            if(std::holds_alternative<RecoveredChat::Request>(records[0]))
                return std::vector<std::uint8_t>{};
            return std::nullopt;
        });
        peer.select(false);peer.send(RecoveredSessionPeer::tail());peer.silent();
        const auto move=RecoveredMovement::encode({18,14,3,0});
        const std::array<std::uint8_t,9> chat{0x2f,9,0,0,0,0,0,'A',0};
        const auto message=RecoveredWorldFrame::encode(chat);
        std::vector<std::uint8_t> combined(move.begin(),move.end());
        combined.insert(combined.end(),message.begin(),message.end());
        peer.send(combined);peer.expect(RecoveredMovement::ack(3));peer.silent();
        require(peer.world_calls==2,"Independent movement/chat frames did not reach separate policies");
    }
    {
        RecoveredSessionPeer peer(false,[](Session&,auto records) {
            require(records.size()==1 && std::holds_alternative<Records::Tick>(records[0]),
                    "Typed handler lost exact tick");
            return std::optional(std::vector<std::uint8_t>{});
        });
        peer.select(false);peer.send(RecoveredSessionPeer::tail());peer.silent();
        const auto tick=RecoveredWorldFrame::encode(std::array<std::uint8_t,2>{0x30,0});
        peer.send(tick);peer.silent();peer.send(tick);peer.silent();
        require(peer.world_calls==2,"Empty accepted response stopped reads");
    }
    for(unsigned bad=0;bad<7;++bad) {
        RecoveredSessionPeer peer(false,[&](Session& session,auto records)
                ->std::optional<std::vector<std::uint8_t>> {
            check(records);
            if(bad==0) return std::nullopt;
            if(bad==1) throw std::runtime_error("Synthetic policy rejection");
            if(bad==2) return std::vector<std::uint8_t>{1};
            if(bad==3) { auto corrupt=reply;corrupt.back()^=1;return corrupt; }
            if(bad==4) { auto truncated=reply;truncated.push_back(5);return truncated; }
            if(bad==5) return std::vector<std::uint8_t>(1024*1024+1);
            session.close();return reply;
        });
        peer.select(false);peer.send(RecoveredSessionPeer::tail());peer.silent();
        peer.send(wire);peer.closed();
        require(peer.world_calls==1,"Policy rejection did not reach exactly one handler");
    }
    for(unsigned bad=0;bad<4;++bad) {
        RecoveredSessionPeer peer(false,[&](Session&,auto) { return std::optional(reply); });
        peer.select(false);
        if(bad!=0) { peer.send(RecoveredSessionPeer::tail());peer.silent(); }
        auto invalid=wire;
        if(bad==1) invalid.back()^=1;
        if(bad==2) {
            auto suffix=std::vector<std::uint8_t>(logical.begin(),logical.end());
            suffix.push_back(0x85); // A valid prefix must not reach game code.
            invalid=RecoveredWorldFrame::encode(suffix);
        }
        if(bad==3) invalid=RecoveredWorldFrame::encode(std::array<std::uint8_t,2>{0x30,1});
        peer.send(invalid);peer.closed();
        require(peer.world_calls==0,"Invalid or pre-tail record reached game code");
    }
    for(const auto opcode:std::array<std::uint8_t,3>{0x25,0x85,0x86}) {
        RecoveredSessionPeer peer(true);peer.select(false);
        peer.send(RecoveredSessionPeer::tail());peer.silent();
        std::vector<std::uint8_t> mixed{0x2e,18,0,14,0,3,0};
        mixed.push_back(opcode);mixed.resize(mixed.size()+(opcode==0x85?6:4),0);
        peer.send(RecoveredWorldFrame::encode(mixed));peer.closed();
        require(peer.movement_calls==0,"Unhandled suffix partially committed movement");
    }
    bool rejected=false;
    try { RecoveredSessionPeer peer(true,[&](Session&,auto) { return std::optional(reply); }); }
    catch(const std::invalid_argument&) { rejected=true; }
    require(rejected,"Ambiguous world handler configuration accepted");
}

void diagnostic_scalar_codec_unchanged() {
    // Pinned from the pre-retirement C++ encoder, not a source corpus read.
    const std::string expected=
        "900028f4c9fdfd191bfffd3333fdfdccccfdba03b3d61f2e519e1213d7a79f0f7264"
        "bef9621d93f67639a5010db5e2e03294e356dde7729bc0ae490913591d18cb05db8c"
        "dff232ed04ef5138bce5f2d4cbdf97c7c930df2ab4d883da0ce40d7172c77d75a2"
        "02bde9323adb4d6f172fa69445ac10116b9eb85174a5e997bf390ec57a9f8ef9cbc"
        "e46e47b630539fe9680";
    const auto wire=RecoveredWorldStateCandidate::wire();
    std::string hex;
    constexpr char digits[]="0123456789abcdef";
    for(auto byte:wire) { hex+=digits[byte>>4];hex+=digits[byte&15]; }
    require(hex==expected,"Diagnostic scalar fixture bytes changed");
    const auto logical=RecoveredWorldFrame::decode(wire);
    require(logical && std::equal(logical->begin(),logical->end(),
            RecoveredWorldStateCandidate::historical_logical.begin(),RecoveredWorldStateCandidate::historical_logical.end()),
            "Diagnostic scalar fixture decode/checksum changed");
}

void recovered_battle_transport(std::uint8_t action) {
    using Attack=RecoveredBattleCommand::BasicAttackRequest;
    // Synthetic participant state and results test transport only. No formula,
    // native encounter setup or automatic transition to InBattle is implied.
    std::array<std::uint8_t,17> command{
        0x35,13,action,1,0xa5,1,0,0,0x20,0x78,0x56,0x34,0x12,0xff,0x80,0x86,0x35};
    const bool skill=action==3 || action==0x83;
    if(skill) { command[8]=0;command[13]=7;command[14]=command[15]=command[16]=0; }
    const auto wire=RecoveredWorldFrame::encode(command);
    const auto reply=RecoveredWorldFrame::encode(std::array<std::uint8_t,17>{
        0x86,3,13,0x34,0x12,2,0,0,0,0xa5,0x80,0,0xff,0x35,3,4,5});
    const auto check=[action](std::span<const RecoveredWorldRecords::Record> records) {
        require(records.size()==1,"Battle command count changed");
        if(action==3 || action==0x83) {
            const auto* request=std::get_if<RecoveredSkillCommand::Record>(&records[0]);
            require(request && request->actor_position==13 && request->side_flag==1 &&
                    request->unwritten_byte3==0xa5 && request->target_masks[0]==1 &&
                    request->target_masks[1]==0 && request->context_storage==0x12345678 &&
                    request->selection_id_byte==7 && request->continuation==(action==0x83),
                    "Skill record changed or aliased in transport");
            return;
        }
        require(action==1 ? std::holds_alternative<Attack>(records[0]) :
                std::holds_alternative<RecoveredBattleCommand::ControlRequest>(records[0]),
                "Battle command reached the wrong typed route");
        const auto& request=action==1 ? std::get<Attack>(records[0]) :
            std::get<RecoveredBattleCommand::ControlRequest>(records[0]).fields;
        require(request.actor_position==13 && request.side_flag==1 &&
                request.unwritten_byte3==0xa5 && request.target_masks[0]==1 &&
                request.target_masks[1]==0x2000 && request.context_storage==0x12345678 &&
                request.unwritten_parameter==0x358680ff,"Attack bytes changed in transport");
    };
    for(std::size_t split=1;split<wire.size();++split) {
        RecoveredSessionPeer peer(false,[&](Session& session,auto records) {
            require(session.state()==SessionState::InBattle,"Attack lost game-owned battle state");
            check(records);return std::optional(reply);
        });
        peer.select(false);peer.send(RecoveredSessionPeer::tail());peer.silent();
        peer.session->set_state(SessionState::InBattle);
        peer.send(std::span(wire).first(split));peer.silent();
        require(peer.world_calls==0,"Fragmented attack reached game policy");
        peer.send(std::span(wire).subspan(split));peer.expect(reply);peer.silent();
        require(peer.world_calls==1,"Attack callback count changed");
    }
    for(const auto state:{SessionState::Connected,SessionState::Handshaked,
            SessionState::Authenticated,SessionState::CharacterSelected,SessionState::InWorld}) {
        RecoveredSessionPeer peer(false,[&](Session&,auto) { return std::optional(reply); });
        peer.select(false);peer.send(RecoveredSessionPeer::tail());peer.silent();
        peer.session->set_state(state);
        // A structurally valid movement prefix cannot commit before rejected combat.
        std::vector<std::uint8_t> mixed{0x2e,18,0,14,0,3,0};
        mixed.insert(mixed.end(),command.begin(),command.end());
        peer.send(RecoveredWorldFrame::encode(mixed));peer.closed();
        require(peer.world_calls==0,"Attack outside InBattle reached policy");
    }
    {
        unsigned handled=0;
        RecoveredSessionPeer peer(false,[&](Session&,auto records) {
            std::vector<std::uint8_t> output;
            for(std::size_t i=0;i<records.size();++i) {
                check(records.subspan(i,1));++handled;
                output.insert(output.end(),reply.begin(),reply.end());
            }
            return std::optional(output);
        });
        peer.select(false);peer.send(RecoveredSessionPeer::tail());peer.silent();
        peer.session->set_state(SessionState::InBattle);
        auto coalesced=wire;coalesced.insert(coalesced.end(),wire.begin(),wire.end());
        peer.send(coalesced);peer.expect(reply);peer.expect(reply);peer.silent();
        require(handled==2,"Coalesced attacks were lost");
    }
    for(unsigned bad=0;bad<4;++bad) {
        RecoveredSessionPeer peer(false,[&](Session&,auto records)
                ->std::optional<std::vector<std::uint8_t>> {
            check(records);
            if(bad==2) return std::nullopt;
            if(bad==3) throw std::runtime_error("Unproven combat policy");
            return reply;
        });
        peer.select(false);peer.send(RecoveredSessionPeer::tail());peer.silent();
        peer.session->set_state(SessionState::InBattle);
        auto input=wire;
        if(bad==0) input.back()^=1;
        if(bad==1) {
            auto invalid=command;invalid[2]=0x7f; // Unsupported action is not a skill.
            input=RecoveredWorldFrame::encode(invalid);
        }
        peer.send(input);peer.closed();
        require(peer.world_calls==(bad<2?0u:1u),"Attack rejection order changed");
    }
    {
        RecoveredSessionPeer peer(true);peer.select(false);
        peer.send(RecoveredSessionPeer::tail());peer.silent();
        peer.session->set_state(SessionState::InBattle);
        peer.send(wire);peer.closed();
        require(peer.movement_calls==0,"Movement-only Application consumed an attack");
    }
    {
        RecoveredSessionPeer peer(false,[&](Session&,auto) { return std::optional(reply); });
        peer.select(false);peer.session->set_state(SessionState::InBattle);
        peer.send(wire);peer.closed();
        require(peer.world_calls==0,"InBattle bypassed authenticated world-tail gate");
    }
}

void recovered_skill_sequence_transport() {
    const std::array<std::uint8_t,17> first{
        0x35,13,0x83,1,0xa5,1,0,0,0,0x78,0x56,0x34,0x12,7,0,0,0};
    auto last=first;last[2]=3;last[4]=0x5a;last[5]=2;
    const auto prefix=RecoveredWorldFrame::encode(first);
    const auto suffix=RecoveredWorldFrame::encode(last);
    auto check=[](Session&,std::span<const RecoveredWorldRecords::Record> records) {
        require(records.size()>=2 && records.size()<=14,"Incomplete skill escaped staging");
        for(std::size_t i=0;i<records.size();++i) {
            const auto* item=std::get_if<RecoveredSkillCommand::Record>(&records[i]);
            require(item && item->continuation==(i+1<records.size()) &&
                    item->actor_position==13 && item->selection_id_byte==7,
                    "Assembled skill fields changed");
        }
        return std::optional(std::vector<std::uint8_t>{});
    };
    for(std::size_t split=1;split<prefix.size()+suffix.size();++split) {
        RecoveredSessionPeer peer(false,check);
        peer.select(false);peer.send(RecoveredSessionPeer::tail());peer.silent();
        peer.session->set_state(SessionState::InBattle);
        auto joined=prefix;joined.insert(joined.end(),suffix.begin(),suffix.end());
        peer.send(std::span(joined).first(split));peer.silent();
        require(peer.world_calls==0,"Incomplete skill sequence reached policy");
        peer.send(std::span(joined).subspan(split));peer.silent();
        require(peer.world_calls==1,"Complete skill sequence was not delivered once");
    }
    for(unsigned malformed=0;malformed<3;++malformed) {
        RecoveredSessionPeer peer(false,check);
        peer.select(false);peer.send(RecoveredSessionPeer::tail());peer.silent();
        peer.session->set_state(SessionState::InBattle);
        peer.send(prefix);peer.silent();
        require(peer.world_calls==0,"Pending skill prefix reached policy");
        auto invalid=suffix;
        if(malformed==0) invalid.back()^=1;
        else if(malformed==1) { invalid[0]=4;invalid[1]=0; }
        else invalid=RecoveredWorldFrame::encode(std::array<std::uint8_t,2>{0xff,0});
        peer.send(invalid);peer.closed();
        require(peer.world_calls==0,"Malformed suffix committed pending skill");
    }
    for(unsigned bad=0;bad<8;++bad) {
        RecoveredSessionPeer peer(false,check);
        peer.select(false);peer.send(RecoveredSessionPeer::tail());peer.silent();
        peer.session->set_state(SessionState::InBattle);
        std::vector<std::uint8_t> staged{0x2e,18,0,14,0,3,0};
        if(bad==7) staged.insert(staged.begin(),last.begin(),last.end());
        staged.insert(staged.end(),first.begin(),first.end());
        peer.send(RecoveredWorldFrame::encode(staged));peer.silent();
        require(peer.world_calls==0,"Continuation reached policy");
        auto changed=last;
        if(bad<4) changed[std::array<unsigned,4>{1,3,9,13}[bad]]^=1;
        if(bad==4) { peer.session->set_state(SessionState::InWorld); }
        if(bad==5) { // Other commands cannot interrupt a pending cast.
            peer.send(RecoveredWorldFrame::encode(std::array<std::uint8_t,2>{0x30,0}));
        } else if(bad==6) {
            std::vector<std::uint8_t> overflow;
            for(unsigned i=0;i<13;++i) overflow.insert(overflow.end(),first.begin(),first.end());
            peer.send(RecoveredWorldFrame::encode(overflow));
        } else if(bad==7) {
            peer.io.restart();peer.io.run_for(std::chrono::milliseconds(3000));
            peer.send(prefix);peer.silent();
            peer.io.restart();peer.io.run_for(std::chrono::milliseconds(2100));
        } else peer.send(RecoveredWorldFrame::encode(changed));
        peer.closed();require(peer.world_calls==0,"Invalid pending sequence committed");
    }
    {
        RecoveredSessionPeer peer(false,check);
        peer.select(false);peer.send(RecoveredSessionPeer::tail());peer.silent();
        peer.session->set_state(SessionState::InBattle);
        std::vector<std::uint8_t> maximum;
        for(unsigned i=0;i<13;++i) maximum.insert(maximum.end(),first.begin(),first.end());
        maximum.insert(maximum.end(),last.begin(),last.end());
        peer.send(RecoveredWorldFrame::encode(maximum));peer.silent();
        require(peer.world_calls==1,"Native maximum sequence rejected");
        peer.send(prefix);peer.silent();
        require(peer.world_calls==1,"Previous sequence contaminated next staging");
        peer.send(suffix);peer.silent();
        require(peer.world_calls==2,"Second sequence lost");
    }
}
}

void test_session_state() {
    using namespace god2;
    if(!state_allows(Opcode::C2S_LoginRequest,SessionState::Connected) || !state_allows(Opcode::C2S_LoginRequest,SessionState::Handshaked)) throw std::runtime_error("Login state");
    if(state_allows(Opcode::C2S_PlayerMove,SessionState::Connected) || state_allows(Opcode::C2S_EnterWorld,SessionState::Authenticated)) throw std::runtime_error("Invalid state accepted");
    if(!state_allows(Opcode::C2S_PlayerMove,SessionState::InWorld) || !state_allows(Opcode::C2S_BattleAction,SessionState::InBattle)) throw std::runtime_error("World state");
    for(auto s:{SessionState::Connected,SessionState::Handshaked,SessionState::Authenticated,SessionState::CharacterSelected,SessionState::InWorld,SessionState::InBattle})
        if(!state_allows(Opcode::C2S_Heartbeat,s)) throw std::runtime_error("Heartbeat state");
    if(state_allows(Opcode::C2S_Heartbeat,SessionState::Disconnected)) throw std::runtime_error("Disconnected heartbeat");
    diagnostic_scalar_codec_unchanged();
    recovered_world_identity_sender_transport();
    recovered_battle_self_view_transport();
    recovered_callback_output_transport();
    recovered_causal_deity_reply_transport();
    recovered_legacy_selection_learning_reanchor();
    recovered_legacy_selection_learning_reanchor(true);
    recovered_written_deity_selection_transport();
    for(std::uint8_t reason:{0,1,2}) {
        RecoveredSessionPeer peer(false,[](Session&,auto)->std::optional<std::vector<std::uint8_t>> {
            return std::vector<std::uint8_t>{};
        });
        peer.select(false);peer.send(RecoveredSessionPeer::tail());peer.silent();
        peer.send(RecoveredWorldFrame::encode(std::array<std::uint8_t,2>{2,reason}));
        peer.expect(RecoveredWorldFrame::encode(std::array<std::uint8_t,3>{3,0,0}));
        peer.closed();
        require(peer.world_calls==0,"Native logout invoked gameplay callback");
    }
    {
        RecoveredSessionPeer peer(false);
        peer.expect(RecoveredSeedExchange::hello());
        peer.send(RecoveredSeedExchange::response);
        peer.expect(RecoveredPostSeed::frame(0xf6));
        RecoveredC2S0002::Payload credentials{};credentials[167]=0xc8;
        peer.send(RecoveredC2S0002::encode(credentials));
        peer.expect(RecoveredCharacterBootstrap::candidate());
        std::array<std::uint8_t,45> create{};create[0]=0x17;create[1]='T';create[41]=4;
        peer.send(RecoveredWorldFrame::encode(create));
        peer.expect(RecoveredCharacterCreateResult::committed_success());
        auto request=RecoveredWorldFrame::encode(std::array<std::uint8_t,2>{0x18,1});
        peer.send(std::span(request).first(4));peer.silent();
        peer.send(std::span(request).subspan(4));
        peer.expect(RecoveredWorldFrame::encode(std::array<std::uint8_t,3>{0x18,0,0}));
        require(peer.selection_calls==0 && peer.session->character_id==0 &&
                peer.session->state()==SessionState::Authenticated,"Slot ack prematurely selected character");
        peer.send(RecoveredWorldFrame::encode(std::array<std::uint8_t,2>{2,0}));
        peer.expect(RecoveredWorldFrame::encode(std::array<std::uint8_t,3>{3,0,0}));
        peer.closed();
    }
    recovered_runtime_without_scalar_replay();
    recovered_character_idle_tick_transport();
    recovered_world_push_transport();
    recovered_visibility_transport();
    recovered_world_service_transport();
    recovered_world_record_routing();
    recovered_battle_transport(1);
    recovered_battle_transport(0x0b);
    recovered_battle_transport(3);
}

void test_session_skill_sequence() { recovered_skill_sequence_transport(); }

void test_session_battle_service() {
    using namespace god2;
    LuaEngine lua(std::filesystem::path(GOD2_SOURCE_DIR)/"scripts",false);
    require(lua.initialize(),"Battle TCP Lua initialization failed");
    RecoveredBattleService battles([&](const CombatRuleInput& input){return lua.combat_damage(input);});
    RecoveredWorldService world({},[&](Session& session,auto records){return battles.handle(session,records);});
    RecoveredSessionPeer peer(false,[&](Session& session,auto records){return world.handle(session,records);});
    peer.select(false);peer.send(RecoveredSessionPeer::tail());peer.silent();
    // Explicit test-only admission: does not claim the original client's battle
    // bootstrap or native turn handshake is implemented by Application.
    peer.session->set_state(SessionState::InBattle);
    const std::array<BattleActor,3> actors{{
        {0,RecoveredSessionPeer::character,100,100,20,20,31,40,8,10},
        {14,0,100,100,0,0,20,25,13,6},
        {15,0,100,100,0,0,20,25,13,6}}};
    const BattleAction basic{0,{},false,100,100,0,0,150};
    auto skill=basic;skill.magical=true;skill.mp_cost=8;
    RecoveredBattleService::Policy policy{2,1,0,0x1234,basic,{{5,skill}}};
    const auto vital=[](unsigned kind,unsigned position,unsigned maximum,unsigned current) {
        std::array<std::uint8_t,17> bytes{0x86,static_cast<std::uint8_t>(kind),
            static_cast<std::uint8_t>(position)};
        for(unsigned i=0;i<4;++i) {
            bytes[5+i]=static_cast<std::uint8_t>(maximum>>(8*i));
            bytes[9+i]=static_cast<std::uint8_t>(current>>(8*i));
        }
        return bytes;
    };
    unsigned encoded=0;
    battles.bind(*peer.session,Battle(17,actors,123),policy,
        [&](const BattleSnapshot& state,const BattleActionResult& result) {
            ++encoded;
            std::vector<std::uint8_t> logical;
            for(const auto& hit:result.hits) {
                const auto& actor=*state.actors[hit.target];
                const auto bytes=vital(0,hit.target,actor.max_hp,actor.hp);
                logical.insert(logical.end(),bytes.begin(),bytes.end());
            }
            const auto& source=*state.actors[result.source];
            const auto mp=vital(1,result.source,source.max_mp,source.mp);
            logical.insert(logical.end(),mp.begin(),mp.end());
            return RecoveredWorldFrame::encode(logical);
        });
    const std::array<std::uint8_t,17> first{
        0x35,2,0x83,1,0,0,0,1,0,0x34,0x12,0,0,5,0,0,0};
    auto last=first;last[2]=3;last[7]=2;
    const auto prefix=RecoveredWorldFrame::encode(first);
    peer.send(std::span(prefix).first(prefix.size()-1));peer.silent();
    require(battles.inspect(peer.session->id()).revision==1 && encoded==0,"Partial wire committed");
    peer.send(std::span(prefix).last(1));peer.silent();
    require(battles.inspect(peer.session->id()).revision==1 && encoded==0,"Partial skill committed");
    peer.send(RecoveredWorldFrame::encode(last));
    std::vector<std::uint8_t> expected;
    for(const auto& bytes:{vital(0,14,100,66),vital(0,15,100,66),vital(1,0,20,12)})
        expected.insert(expected.end(),bytes.begin(),bytes.end());
    peer.expect(RecoveredWorldFrame::encode(expected));peer.silent();
    const auto& state=battles.inspect(peer.session->id());
    require(encoded==1 && state.revision==2 && state.actors[0]->mp==12 &&
        state.actors[14]->hp==66 && state.actors[15]->hp==66,"TCP skill transaction changed");
    auto corrupted=RecoveredWorldFrame::encode(last);corrupted.back()^=1;
    peer.send(corrupted);peer.closed();
    require(encoded==1 && battles.inspect(peer.session->id()).revision==2,
            "Corrupt incoming frame changed battle");
    battles.remove(peer.session->id());

    // Captured native stack body, replayed by a synthetic TCP peer. The opcode
    // was inferred at the disconnected native callsite, not captured on wire.
    std::ifstream capture(std::filesystem::path(GOD2_SOURCE_DIR)/
        "artifacts/runs/offline-battle-action-20260920-02/offline-result.json");
    require(capture.good(),"Missing native action evidence");
    const auto evidence=nlohmann::json::parse(capture);
    require(evidence.at("result")=="NATIVE_DISCONNECTED_ACTION_RETURNED",
            "Native action evidence did not complete");
    const auto hex=evidence.at("action_probe").at("logical_hex").get<std::string>();
    require(hex.size()==34,"Native action evidence length changed");
    std::vector<std::uint8_t> captured;
    for(std::size_t i=0;i<hex.size();i+=2) {
        unsigned value=0;
        const auto parsed=std::from_chars(hex.data()+i,hex.data()+i+2,value,16);
        require(parsed.ec==std::errc{} && parsed.ptr==hex.data()+i+2,"Invalid capture hex");
        captured.push_back(static_cast<std::uint8_t>(value));
    }
    RecoveredSessionPeer native_peer(false,[&](Session& session,auto records){return world.handle(session,records);});
    native_peer.select(false);native_peer.send(RecoveredSessionPeer::tail());native_peer.silent();
    native_peer.session->set_state(SessionState::InBattle); // Explicit test-only admission.
    auto native_policy=policy;
    native_policy.client_actor=0;native_policy.client_side=0;native_policy.context=0;
    unsigned native_encoded=0;
    battles.bind(*native_peer.session,Battle(18,actors,123),native_policy,
        [&](const BattleSnapshot& state,const BattleActionResult& result) {
            ++native_encoded;
            require(result.hits.size()==1 && result.hits[0].target==14,"Native replay targets changed");
            const auto& target=*state.actors[14];
            return RecoveredWorldFrame::encode(vital(0,14,target.max_hp,target.hp));
        });
    const auto native_wire=RecoveredWorldFrame::encode(captured);
    native_peer.send(std::span(native_wire).first(native_wire.size()-1));native_peer.silent();
    require(native_encoded==0 && battles.inspect(native_peer.session->id()).actors[14]->hp==100,
            "Fragmented native replay committed early");
    native_peer.send(std::span(native_wire).last(1));
    native_peer.expect(RecoveredWorldFrame::encode(vital(0,14,100,82)));native_peer.silent();
    const auto& native_state=battles.inspect(native_peer.session->id());
    require(native_encoded==1 && native_state.revision==2 && native_state.actors[14]->hp==82 &&
            native_state.actors[0]->mp==20,"Native replay transaction changed");
    battles.remove(native_peer.session->id());
    // Current limitation: resource rejection is still fatal at the Session boundary.
    // Keep real TCP evidence distinct from the in-process admission recovery test.
    for(const auto available:{0u,5u,7u}) {
        RecoveredSessionPeer low_peer(false,[&](Session& session,auto records){return world.handle(session,records);});
        low_peer.select(false);low_peer.send(RecoveredSessionPeer::tail());low_peer.silent();
        low_peer.session->set_state(SessionState::InBattle);
        auto low_actors=actors;low_actors[0].mp=available;
        unsigned rejected_encoded=0;
        battles.bind(*low_peer.session,Battle(30+available,low_actors,123),policy,
            [&](const BattleSnapshot&,const BattleActionResult&) {
                ++rejected_encoded;
                return RecoveredWorldFrame::encode(vital(1,0,20,0));
            });
        auto cast=first;cast[2]=3;
        const auto low_wire=RecoveredWorldFrame::encode(cast);
        low_peer.send(std::span(low_wire).first(low_wire.size()-1));low_peer.silent();
        require(low_peer.world_calls==0,"Incomplete low-MP frame reached game policy");
        low_peer.send(std::span(low_wire).last(1));low_peer.closed();
        const auto& unchanged=battles.inspect(low_peer.session->id());
        require(low_peer.world_calls==1 && rejected_encoded==0 && unchanged.revision==1 &&
                unchanged.actors[0]->mp==available && unchanged.actors[0]->hp==100 &&
                unchanged.actors[14]->hp==100 && unchanged.actors[15]->hp==100,
                "TCP resource rejection mutated battle or emitted a fabricated reply");
        battles.remove(low_peer.session->id());
    }
    // Explicit response candidate: TCP liveness is not native-client regrant proof.
    for(const auto available:{0u,5u,7u}) {
        RecoveredSessionPeer retry_peer(false,[&](Session& session,auto records){return world.handle(session,records);});
        retry_peer.select(false);retry_peer.send(RecoveredSessionPeer::tail());retry_peer.silent();
        retry_peer.session->set_state(SessionState::InBattle);
        auto low_actors=actors;low_actors[0].mp=available;
        auto recover=policy;recover.diagnostic_single_action=true;
        unsigned refusals=0,successes=0;
        const auto mp=vital(1,0,20,available);
        std::vector<std::uint8_t> refusal_logical(mp.begin(),mp.end());
        std::array<std::uint8_t,17> grant{0x86,5,0,1,2};
        refusal_logical.insert(refusal_logical.end(),grant.begin(),grant.end());
        const auto refused_wire=RecoveredWorldFrame::encode(refusal_logical);
        recover.diagnostic_mp_refusal=[&](const BattleSnapshot& snapshot,const BattleAction& action,
                                         const InsufficientBattleMp& refusal) {
            ++refusals;
            require(snapshot.revision==1 && snapshot.actors[0]->mp==available && action.source==0 &&
                    action.targets==std::vector<std::uint8_t>{14} && refusal.required==8 &&
                    refusal.available==available,"Resource reply received mutated or foreign state");
            return refused_wire;
        };
        battles.bind(*retry_peer.session,Battle(50+available,low_actors,123),recover,
            [&](const BattleSnapshot& snapshot,const BattleActionResult&) {
                ++successes;
                return RecoveredWorldFrame::encode(vital(0,14,100,snapshot.actors[14]->hp));
            });
        auto cast=first;cast[2]=3;
        retry_peer.send(RecoveredWorldFrame::encode(cast));retry_peer.expect(refused_wire);retry_peer.silent();
        require(refusals==1 && successes==0 && battles.inspect(retry_peer.session->id()).revision==1 &&
                !battles.diagnostic_round_ready(*retry_peer.session),"Resource reply consumed a turn");
        auto fallback=cast;fallback[2]=1;
        retry_peer.send(RecoveredWorldFrame::encode(fallback));
        retry_peer.expect(RecoveredWorldFrame::encode(vital(0,14,100,82)));retry_peer.silent();
        const auto& after=battles.inspect(retry_peer.session->id());
        require(retry_peer.world_calls==2 && successes==1 && refusals==1 && after.revision==2 &&
                after.actors[0]->mp==available && after.actors[14]->hp==82,
                "Same-connection fallback after resource refusal failed");
        battles.remove(retry_peer.session->id());
    }
}
