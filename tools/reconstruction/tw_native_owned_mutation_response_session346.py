"""Authorized three-file SOURCE edit only; byte-preserving outside exact hunks."""
from pathlib import Path
import hashlib,json,base64
ROOT=Path('C:/Users/risei/Desktop/God2/God2-Server')
OUT=Path(__file__).resolve().parent
changes=[]
prepared=[]
def edit(rel,items):
    p=ROOT/rel;before=p.read_bytes();data=before;hunks=[]
    for item in items:
        old,new=item[:2];wanted=item[2] if len(item)>2 else 1
        variants=[old.encode()]
        if '\n' in old:variants.append(old.replace('\n','\r\n').encode())
        matches=[v for v in variants if data.count(v)==wanted]
        if len(matches)!=1:raise RuntimeError(f'nonunique source needle {rel}: {old[:90]!r}')
        needle=matches[0];replacement=new.replace('\n','\r\n').encode() if b'\r\n' in needle else new.encode()
        for _ in range(wanted):
            at=data.index(needle);data=data[:at]+replacement+data[at+len(needle):]
            hunks.append({'offset':at,'before_b64':base64.b64encode(needle).decode(),'after_b64':base64.b64encode(replacement).decode()})
    inverse=data
    for h in reversed(hunks):
        a=base64.b64decode(h['after_b64']);b=base64.b64decode(h['before_b64']);at=h['offset']
        assert inverse[at:at+len(a)]==a
        inverse=inverse[:at]+b+inverse[at+len(a):]
    assert inverse==before
    prepared.append((p,before,data))
    stem=p.name
    for name,value in [('before-'+stem,before),('after-'+stem,data)]:
        if (OUT/name).exists():raise RuntimeError('immutable snapshot exists')
    changes.append({'path':rel,'before_bytes':len(before),'before_sha256':hashlib.sha256(before).hexdigest(),
        'after_bytes':len(data),'after_sha256':hashlib.sha256(data).hexdigest(),'exact_inverse':True,'hunks':hunks})

edit('src/net/Session.h',[
('''    // Actual local normal-entry transcript: exact issued S2A, accepted raw tail''','''    // Passive ORIGINAL callback-response wire custody, distinct from logical
    // push records. One token per actual world-records callback; no ACK/native
    // cache adoption, input barrier or gameplay permission is inferred.
    enum class WorldResponseWriteStatus {Pending,Written,Failed};
    class WorldResponseWrite {
    public:
        WorldResponseWrite(const WorldResponseWrite&)=default;
        WorldResponseWrite& operator=(const WorldResponseWrite&)=default;
        WorldResponseWriteStatus status() const noexcept;
        const std::vector<std::uint8_t>& wire() const noexcept;
    private:
        friend class Session;
        friend struct Impl;
        struct Data;
        explicit WorldResponseWrite(std::shared_ptr<Data> data):data_(std::move(data)) {}
        std::shared_ptr<Data> data_;
    };
    // Actual local normal-entry transcript: exact issued S2A, accepted raw tail'''),
('''    bool world_records_write_current(const WorldRecordsWrite&) const;''','''    bool world_records_write_current(const WorldRecordsWrite&) const;
    // Capture only the exact ORIGINAL complete framed callback return. This
    // does not send/decode/reframe bytes. Double capture/reentry poisons it.
    WorldResponseWrite observe_world_response(std::span<const std::uint8_t> wire);
    bool world_response_write_current(const WorldResponseWrite&) const;
    bool world_response_write_current_on_game(const WorldResponseWrite&) const;''')])

edit('src/net/Session.cpp',[
('''thread_local const Session* observed_world_callback=nullptr;
struct WorldRecordsObservationScope {
    explicit WorldRecordsObservationScope(const Session& session) {
        if(observed_world_callback)throw std::logic_error("World observation callback reentry rejected");
        observed_world_callback=&session;
    }
    ~WorldRecordsObservationScope(){observed_world_callback=nullptr;}''','''thread_local const Session* observed_world_callback=nullptr;
thread_local bool* observed_response_poison=nullptr;
thread_local std::atomic<Session::WorldResponseWriteStatus>* observed_response_status=nullptr;
void poison_world_response() noexcept {
    if(observed_response_poison)*observed_response_poison=true;
    if(observed_response_status) {
        auto pending=Session::WorldResponseWriteStatus::Pending;
        observed_response_status->compare_exchange_strong(pending,Session::WorldResponseWriteStatus::Failed);
    }
}
struct WorldRecordsObservationScope {
    bool response_poisoned=false;
    explicit WorldRecordsObservationScope(const Session& session) {
        if(observed_world_callback) {
            poison_world_response();
            throw std::logic_error("World observation callback reentry rejected");
        }
        observed_world_callback=&session;observed_response_poison=&response_poisoned;
        observed_response_status=nullptr;
    }
    ~WorldRecordsObservationScope(){
        observed_response_status=nullptr;observed_response_poison=nullptr;observed_world_callback=nullptr;
    }'''),
('''struct Session::NormalWorldInitialization::Entry {''','''struct Session::WorldResponseWrite::Data {
    const std::thread::id game_thread=std::this_thread::get_id();
    const std::weak_ptr<Session> session;
    const std::uint64_t account,character,battle;
    const SessionState phase;
    const std::vector<std::uint8_t> wire;
    std::atomic<WorldResponseWriteStatus> status{WorldResponseWriteStatus::Pending};
    Data(std::weak_ptr<Session> owner,std::uint64_t a,std::uint64_t c,std::uint64_t b,
         SessionState p,std::span<const std::uint8_t> raw)
        :session(std::move(owner)),account(a),character(c),battle(b),phase(p),wire(raw.begin(),raw.end()) {}
};
Session::WorldResponseWriteStatus Session::WorldResponseWrite::status() const noexcept {return data_->status.load();}
const std::vector<std::uint8_t>& Session::WorldResponseWrite::wire() const noexcept {return data_->wire;}

struct Session::NormalWorldInitialization::Entry {'''),
('''    struct SelectionEntry {''','''    // Captured on game; only immutable bytes/weak Session/atomic status cross
    // to strand. Attempt retirement closes Pending even if Main keeps Data.
    struct WorldResponseAttempt {
        std::shared_ptr<WorldResponseWrite::Data> receipt;
        std::shared_ptr<std::vector<std::uint8_t>> frame;
        explicit WorldResponseAttempt(std::shared_ptr<WorldResponseWrite::Data> value):receipt(std::move(value)) {}
        void fail() noexcept {
            auto pending=WorldResponseWriteStatus::Pending;
            receipt->status.compare_exchange_strong(pending,WorldResponseWriteStatus::Failed);
        }
        ~WorldResponseAttempt(){fail();}
    };
    std::shared_ptr<WorldResponseAttempt> world_response_callback_capture; // Serial game callback ONLY.
    struct SelectionEntry {'''),
('''        std::shared_ptr<NativePkEntryHold::Data> native_pk{};
    };
    std::deque<Write> writes;''','''        std::shared_ptr<NativePkEntryHold::Data> native_pk{};
        std::shared_ptr<WorldResponseAttempt> observed_response{}; // LAST: preserve every old aggregate initializer.
    };
    std::deque<Write> writes;'''),
('''            s.native_pk_terminal_callback_capture.reset(); // This exact serial input callback only.''','''            s.native_pk_terminal_callback_capture.reset(); // This exact serial input callback only.
            s.world_response_callback_capture.reset(); // Previous unhanded attempt retires Failed.'''),
('''                if(s.native_pk_terminal_callback_capture)accepted=false;''','''                if(s.native_pk_terminal_callback_capture || s.world_response_callback_capture)accepted=false;''',2),
('''                logger("session")->warn("Recovered world callback exception session_id={} reason=unknown",s.id);''','''                logger("session")->warn("Recovered world callback exception session_id={} reason=unknown",s.id);'''),
('''            const auto terminal_ack=std::exchange(s.native_pk_terminal_callback_capture,{});
            try {asio::post(s.strand,[self,accepted,terminal_ack,response=std::move(response),''','''            const auto terminal_ack=std::exchange(s.native_pk_terminal_callback_capture,{});
            const auto response_write=std::exchange(s.world_response_callback_capture,{});
            if(response_write && (!accepted || response_write->receipt->wire!=response ||
               response_write->receipt->status.load()!=WorldResponseWriteStatus::Pending)) {
                response_write->fail();accepted=false;
            }
            try {asio::post(s.strand,[self,accepted,terminal_ack,response_write,response=std::move(response),'''),
('''                        s.write_bytes+=bytes->size();s.writes.push_back({bytes,{}});
                        if(s.writes.front().bytes==bytes) s.write();''','''                        if(response_write && (response_write->receipt->wire!=*bytes ||
                           response_write->receipt->session.lock().get()!=self.get() ||
                           response_write->receipt->status.load()!=WorldResponseWriteStatus::Pending)) {
                            response_write->fail();s.fail("Observed original world response identity mismatch");return;
                        }
                        if(response_write)response_write->frame=bytes;
                        s.write_bytes+=bytes->size();s.writes.push_back({bytes,{}});
                        s.writes.back().observed_response=response_write;
                        if(s.writes.front().bytes==bytes) s.write();'''),
('''                if(s.writes.front().advertisement) {''','''                if(const auto attempt=s.writes.front().observed_response) {
                    if(s.closing || s.close_requested.load())attempt->fail();
                    else {
                        if(s.writes.front().held || s.writes.front().bytes!=bytes || attempt->frame!=bytes ||
                           transferred!=bytes->size() || !attempt->receipt ||
                           attempt->receipt->session.lock().get()!=self.get() || attempt->receipt->wire!=*bytes) {
                            s.fail("Observed original world response actual write mismatch");return;
                        }
                        auto pending=WorldResponseWriteStatus::Pending;
                        if(!attempt->receipt->status.compare_exchange_strong(pending,WorldResponseWriteStatus::Written)) {
                            s.fail("Observed original world response already retired");return;
                        }
                    }
                }
                if(s.writes.front().advertisement) {'''),
('''        closing = true;
        close_requested.store(true);
        retire_normal_initialization();''','''        closing = true;
        close_requested.store(true);
        for(const auto& queued:writes)if(queued.observed_response)queued.observed_response->fail();
        retire_normal_initialization();''',2),
('''std::optional<Session::NormalWorldInitialization> Session::normal_world_initialization() const {''','''Session::WorldResponseWrite Session::observe_world_response(std::span<const std::uint8_t> wire) {
    if(observed_world_callback!=this || !observed_response_poison)
        throw std::logic_error("World response capture requires actual world-records game callback");
    if(*observed_response_poison || impl_->world_response_callback_capture) {
        poison_world_response();
        throw std::logic_error("World response capture reentry or duplicate rejected");
    }
    if(impl_->mode!=ProtocolMode::God2CharacterConnection || closing() || !recovered_world_ready() ||
       !account_id || !character_id || wire.empty() || !Impl::valid_world_response(wire))
        throw std::invalid_argument("World response capture requires complete original framed response and ready owner");
    auto data=std::make_shared<WorldResponseWrite::Data>(weak_from_this(),account_id,character_id,
        battle_generation(),state(),wire);
    impl_->world_response_callback_capture=std::make_shared<Impl::WorldResponseAttempt>(data);
    observed_response_status=&data->status;
    return WorldResponseWrite(std::move(data));
}
bool Session::world_response_write_current(const WorldResponseWrite& observation) const {
    if(observed_world_callback!=this)
        throw std::logic_error("World response current requires actual world-records game callback");
    return world_response_write_current_on_game(observation);
}
bool Session::world_response_write_current_on_game(const WorldResponseWrite& observation) const {
    const auto data=observation.data_;
    if(!data || data->game_thread!=std::this_thread::get_id())return false;
    const auto actual=data->session.lock();
    if(actual.get()!=this)return false;
    return !closing() && recovered_world_ready() && impl_->mode==ProtocolMode::God2CharacterConnection &&
        state()==data->phase && battle_generation()==data->battle && account_id==data->account && character_id==data->character;
}
std::optional<Session::NormalWorldInitialization> Session::normal_world_initialization() const {''')])
for p,before,data in prepared:
    (OUT/('before-'+p.name)).write_bytes(before)
    (OUT/('after-'+p.name)).write_bytes(data)
    p.write_bytes(data)
(OUT/'apply-source-manifest.json').write_text(json.dumps({'scope':'SOURCE edits only; no execution of target APIs','changes':changes},indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps([{k:v for k,v in c.items() if k!='hunks'} for c in changes]))
