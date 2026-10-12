from pathlib import Path
import hashlib,json
S=Path('C:/Users/risei/Desktop/God2/God2-Server');O=Path('C:/Users/risei/.codex/artifact-archives/god2-server/20261013/round353-normal-original-response-transport-implementation');h=lambda b:hashlib.sha256(b).hexdigest();plans={}
def add(path,old,new):plans.setdefault(path,[]).append((old,new))
H='src/net/Session.h';C='src/net/Session.cpp'
add(H,'    class NativeBattleSkillPublicationOwner {','''    // Actual ORIGINAL callback response FIFO custody, independent of push
    // attempts and WorldResponseWrite. Queued never means Written/native ACK.
    enum class NormalWorldResponseStatus {Pending,Queued,Failed};
    class NormalWorldResponseAttempt {
    public:
        NormalWorldResponseAttempt(const NormalWorldResponseAttempt&)=default;
        NormalWorldResponseAttempt& operator=(const NormalWorldResponseAttempt&)=default;
        NormalWorldResponseStatus status() const noexcept;
        bool operator==(const NormalWorldResponseAttempt& other) const noexcept {return data_==other.data_;}
    private:
        friend class Session;
        friend struct Impl;
        struct Data;
        explicit NormalWorldResponseAttempt(std::shared_ptr<Data> data):data_(std::move(data)) {}
        std::shared_ptr<Data> data_;
    };
    class NativeBattleSkillPublicationOwner {''')
add(H,'    // PRIVATE0083 enqueue acceptance ONLY; no native/client ACK or receipt claimed.','''    // Own actual callback only; reuse one private Data through split inner runs.
    // Original response custody requires current INIT, not prior S2A Written.
    std::optional<NormalWorldResponseAttempt> capture_normal_world_response(const NormalWorldInitialization&);
    void expect_normal_world_response(const NormalWorldResponseAttempt&,std::span<const std::uint8_t> framed_component);
    bool normal_world_response_current_on_game(const NormalWorldResponseAttempt&) const;
    bool normal_world_response_callback_current(const NormalWorldResponseAttempt&) const;
    // PRIVATE0083 enqueue acceptance ONLY; no native/client ACK or receipt claimed.''')
add(C,'thread_local std::atomic<Session::WorldResponseWriteStatus>* observed_response_status=nullptr;','''thread_local std::atomic<Session::WorldResponseWriteStatus>* observed_response_status=nullptr;
thread_local std::atomic<Session::NormalWorldResponseStatus>* observed_normal_response_status=nullptr;''')
add(C,'''        observed_response_status->compare_exchange_strong(pending,Session::WorldResponseWriteStatus::Failed);
    }
}''','''        observed_response_status->compare_exchange_strong(pending,Session::WorldResponseWriteStatus::Failed);
    }
    if(observed_normal_response_status) {
        auto pending=Session::NormalWorldResponseStatus::Pending;
        observed_normal_response_status->compare_exchange_strong(pending,Session::NormalWorldResponseStatus::Failed);
    }
}''')
add(C,'        observed_response_status=nullptr;\n    }','        observed_response_status=nullptr;observed_normal_response_status=nullptr;\n    }')
add(C,'        observed_response_status=nullptr;observed_response_poison=nullptr;observed_world_callback=nullptr;','        observed_response_status=nullptr;observed_normal_response_status=nullptr;observed_response_poison=nullptr;observed_world_callback=nullptr;')
add(C,'struct Session::NativePkEntryHold::Data {','''struct Session::NormalWorldResponseAttempt::Data {
    const std::thread::id game_thread=std::this_thread::get_id();
    const std::shared_ptr<NormalWorldOutputHandle::Data> recipient;
    std::atomic<NormalWorldResponseStatus> status{NormalWorldResponseStatus::Pending};
    std::atomic<bool> armed{false},retired{false};
    // Game callback writes these before handoff; strand receives frozen values.
    std::vector<std::vector<std::uint8_t>> components;
    std::size_t component_bytes=0;
    explicit Data(std::shared_ptr<NormalWorldOutputHandle::Data> source):recipient(std::move(source)) {}
};
Session::NormalWorldResponseStatus Session::NormalWorldResponseAttempt::status() const noexcept {
    return data_->status.load();
}

struct Session::NativePkEntryHold::Data {''')
add(C,'    struct SelectionEntry {','''    struct NormalResponsePending {
        const std::shared_ptr<NormalWorldResponseAttempt::Data> receipt;
        explicit NormalResponsePending(std::shared_ptr<NormalWorldResponseAttempt::Data> data):receipt(std::move(data)) {}
        void fail() noexcept {
            auto pending=NormalWorldResponseStatus::Pending;
            receipt->status.compare_exchange_strong(pending,NormalWorldResponseStatus::Failed);
            // TLS poison may already have changed status; still retire exactly once.
            if(receipt->status.load()!=NormalWorldResponseStatus::Failed || !receipt->armed.load() ||
               receipt->retired.exchange(true))return;
            const auto recipient=receipt->recipient;
            {
                std::lock_guard lock(recipient->sync->mutex);
                recipient->revoked.store(true);
                const auto epoch=recipient->sync->epoch.load();
                if(epoch!=std::numeric_limits<std::uint64_t>::max())recipient->sync->epoch.store(epoch+1);
            }
            if(const auto actual=recipient->initialization->entry->session.lock())
                actual->impl_->close_requested.store(true); // No post/source callback on failure.
        }
        ~NormalResponsePending(){fail();}
    };
    std::shared_ptr<NormalResponsePending> normal_response_callback_capture; // Serial game callback ONLY.
    struct SelectionEntry {''')
add(C,'    std::array<std::uint8_t,23> normal_tail_bytes{}; // Strand only; maximum existing grammar.','''    // Own ORIGINAL response needs the actual INIT/epoch, not S2A Written.
    // Caller holds Sync::mutex; no public account/character reads or callbacks.
    bool normal_response_transport_current_locked(const std::shared_ptr<NormalWorldOutputHandle::Data>& data) const {
        if(!data || data->sync!=normal_output_sync || data->revoked.load() ||
           data->epoch==std::numeric_limits<std::uint64_t>::max() || data->epoch!=normal_output_sync->epoch.load())return false;
        const auto init=data->initialization;const auto entry=init->entry;
        return mode==ProtocolMode::God2CharacterConnection && !close_requested.load() &&
            owner.recovered_world_ready() && owner.state()==data->phase &&
            (data->phase==SessionState::CharacterSelected || data->phase==SessionState::InWorld) &&
            owner.battle_generation()==data->battle && init->effective_battle==data->battle &&
            normal_entry.load()==entry && normal_initialization.load()==init &&
            entry->session.lock().get()==&owner && entry->account==data->account && entry->character==data->character &&
            data->account && data->character && !entry->retired.load() &&
            !native_pk_pending.load() && !native_battle_pending.load() && !native_pk_terminal.load();
    }
    std::array<std::uint8_t,23> normal_tail_bytes{}; // Strand only; maximum existing grammar.''')
add(C,'    void resume_world_input(bool awaiting_skill=false) {','''    // Final wire has already passed existing complete-frame validation. Match
    // exact registered components at frame boundaries, in order/nonoverlapping.
    static bool normal_response_components_match(const NormalWorldResponseAttempt::Data& receipt,
            std::span<const std::uint8_t> wire) {
        if(!receipt.armed.load() || receipt.components.empty())return false;
        std::size_t at=0;
        for(const auto& component:receipt.components) {
            bool found=false;
            while(at<wire.size()) {
                if(component.size()<=wire.size()-at &&
                   std::equal(component.begin(),component.end(),wire.begin()+static_cast<std::ptrdiff_t>(at))) {
                    at+=component.size();found=true;break;
                }
                if(wire.size()-at<2)return false;
                const auto length=static_cast<std::size_t>(wire[at])+256u*wire[at+1];
                if(length<4 || length>wire.size()-at)return false;
                at+=length;
            }
            if(!found)return false;
        }
        return true;
    }
    void resume_world_input(bool awaiting_skill=false) {''')
add(C,'            s.world_response_callback_capture.reset(); // Previous unhanded attempt retires Failed.','''            s.world_response_callback_capture.reset(); // Previous unhanded attempt retires Failed.
            s.normal_response_callback_capture.reset(); // Independent private original-response attempt.''')
add(C,'                ~ResponseCaptureEnd(){state.world_response_callback_capture.reset();}','''                ~ResponseCaptureEnd(){
                    state.world_response_callback_capture.reset();
                    state.normal_response_callback_capture.reset();
                }''')
old='                if(s.native_pk_terminal_callback_capture || s.world_response_callback_capture)accepted=false;'
new='''                if(s.native_pk_terminal_callback_capture || s.world_response_callback_capture ||
                   (s.normal_response_callback_capture && s.normal_response_callback_capture->receipt->armed.load()))accepted=false;'''
# Two catch clauses use the identical conditional; preserve explicit count metadata.
plans.setdefault(C,[]).append((old,new,2))
add(C,'            const auto response_write=std::exchange(s.world_response_callback_capture,{});','''            const auto response_write=std::exchange(s.world_response_callback_capture,{});
            auto normal_response=std::exchange(s.normal_response_callback_capture,{});
            if(normal_response && !normal_response->receipt->armed.load())normal_response.reset(); // Unarmed legacy reply unchanged.
            if(normal_response && (!accepted || normal_response->receipt->status.load()!=NormalWorldResponseStatus::Pending ||
               !normal_response_components_match(*normal_response->receipt,response))) {
                normal_response->fail();accepted=false;
            }''')
add(C,'            try {asio::post(s.strand,[self,accepted,terminal_ack,response_write,response=std::move(response),','            try {asio::post(s.strand,[self,accepted,terminal_ack,response_write,normal_response,response=std::move(response),')
add(C,'''                        s.write_bytes+=bytes->size();s.writes.push_back({bytes,{}});
                        s.writes.back().observed_response=response_write;''','''                        if(normal_response) {
                            bool queued=false;
                            {
                                std::lock_guard lock(normal_response->receipt->recipient->sync->mutex);
                                if(s.normal_response_transport_current_locked(normal_response->receipt->recipient) &&
                                   normal_response->receipt->status.load()==NormalWorldResponseStatus::Pending) {
                                    s.write_bytes+=bytes->size();s.writes.push_back({bytes,{}});
                                    s.writes.back().observed_response=response_write;
                                    auto pending=NormalWorldResponseStatus::Pending;
                                    queued=normal_response->receipt->status.compare_exchange_strong(pending,NormalWorldResponseStatus::Queued);
                                }
                            }
                            if(!queued){normal_response->fail();s.fail("Normal original response retired before FIFO insertion");return;}
                        } else {
                            s.write_bytes+=bytes->size();s.writes.push_back({bytes,{}});
                            s.writes.back().observed_response=response_write;
                        }''')
add(C,'                if(!terminal_ack)throw; // Existing nonterminal handoff semantics.','''                if(normal_response)normal_response->fail(); // Before preserving the existing rethrow/context-abort path.
                if(!terminal_ack)throw; // Existing nonterminal handoff semantics.''')
add(C,'void Session::send_world_records_impl(std::vector<std::uint8_t> logical,','''std::optional<Session::NormalWorldResponseAttempt> Session::capture_normal_world_response(
        const NormalWorldInitialization& initialization) {
    if(observed_world_callback!=this || !observed_response_poison)
        throw std::logic_error("Normal original response requires own actual callback");
    if(*observed_response_poison)return std::nullopt;
    if(!normal_world_initialization_current(initialization))return std::nullopt;
    if(const auto existing=impl_->normal_response_callback_capture) {
        const NormalWorldResponseAttempt result(existing->receipt);
        if(existing->receipt->recipient->initialization==initialization.data_ &&
           normal_world_response_callback_current(result))return result;
        poison_world_response();existing->fail();
        throw std::logic_error("Normal original response callback identity changed");
    }
    std::lock_guard lock(impl_->normal_output_sync->mutex);
    const auto epoch=impl_->normal_output_sync->epoch.load();
    if(epoch==std::numeric_limits<std::uint64_t>::max())return std::nullopt;
    auto recipient=std::make_shared<NormalWorldOutputHandle::Data>(impl_->normal_output_sync,initialization.data_,epoch,state());
    if(!impl_->normal_response_transport_current_locked(recipient))return std::nullopt;
    auto data=std::make_shared<NormalWorldResponseAttempt::Data>(std::move(recipient));
    impl_->normal_response_callback_capture=std::make_shared<Impl::NormalResponsePending>(data);
    observed_normal_response_status=&data->status;
    return NormalWorldResponseAttempt(std::move(data));
}
void Session::expect_normal_world_response(const NormalWorldResponseAttempt& attempt,
        std::span<const std::uint8_t> framed_component) {
    if(!normal_world_response_callback_current(attempt)) {
        poison_world_response();
        if(impl_->normal_response_callback_capture)impl_->normal_response_callback_capture->fail();
        throw std::logic_error("Normal original component requires its own current callback");
    }
    if(framed_component.empty())return;
    const auto pending=impl_->normal_response_callback_capture;
    pending->receipt->armed.store(true); // Every following failure retires the actual live source.
    try {
        if(pending->receipt->components.size()>=8192 ||
           framed_component.size()>max_buffer-pending->receipt->component_bytes ||
           !Impl::valid_world_response(framed_component))
            throw std::invalid_argument("Normal original response component bounds or frame invalid");
        pending->receipt->components.emplace_back(framed_component.begin(),framed_component.end());
        pending->receipt->component_bytes+=framed_component.size();
    } catch(...) {poison_world_response();pending->fail();throw;}
}
bool Session::normal_world_response_current_on_game(const NormalWorldResponseAttempt& attempt) const {
    const auto data=attempt.data_;
    if(!data || data->game_thread!=std::this_thread::get_id() || data->status.load()==NormalWorldResponseStatus::Failed)return false;
    const auto recipient=data->recipient;
    if(!recipient || !recipient->initialization || !recipient->initialization->entry ||
       recipient->initialization->entry->game_thread!=std::this_thread::get_id() ||
       recipient->initialization->entry->session.lock().get()!=this)return false;
    std::lock_guard lock(recipient->sync->mutex);
    return data->status.load()!=NormalWorldResponseStatus::Failed && impl_->normal_response_transport_current_locked(recipient) &&
        account_id==recipient->account && character_id==recipient->character;
}
bool Session::normal_world_response_callback_current(const NormalWorldResponseAttempt& attempt) const {
    if(observed_world_callback!=this || !observed_response_poison || *observed_response_poison)return false;
    const auto capture=impl_->normal_response_callback_capture;
    return capture && capture->receipt==attempt.data_ && normal_world_response_current_on_game(attempt);
}
void Session::send_world_records_impl(std::vector<std::uint8_t> logical,''')
receipts=[];outputs={}
for rel,edits in plans.items():
 before=(O/'before'/rel).read_bytes();assert (S/rel).read_bytes()==before
 after=before;exact=[]
 for e in edits:
  old,new=e[:2];count=e[2] if len(e)>2 else 1;pairs=[]
  for nl in ['\n','\r\n']:
   a=old.replace('\r\n','\n').replace('\n',nl).encode();b=new.replace('\r\n','\n').replace('\n',nl).encode()
   if (a,b) not in pairs:pairs.append((a,b))
  found=[(a,b) for a,b in pairs if after.count(a)==count]
  if len(found)>1 and '\n' not in old and '\r' not in old:
   a=found[0][0];tail=after[after.index(a)+len(a):];nl='\r\n' if tail.startswith(b'\r\n') else '\n'
   wanted=new.replace('\r\n','\n').replace('\n',nl).encode();found=[(x,y) for x,y in found if y==wanted]
  assert len(found)==1,(rel,old[:90],len(found))
  a,b=found[0];after=after.replace(a,b,count);exact.append({'old':a.decode(),'new':b.decode(),'count':count})
 inverse=after
 for e in reversed(exact):
  a=e['new'].encode();b=e['old'].encode();assert inverse.count(a)==e['count'],e['new'][:100];inverse=inverse.replace(a,b,e['count'])
 assert inverse==before
 receipts.append({'path':rel,'before_bytes':len(before),'before_sha256':h(before),'after_bytes':len(after),'after_sha256':h(after),'inverse_whole_exact':True,'edits':exact});outputs[rel]=after
# Both complete plans/inverses qualify before either tracked write.
for rel,after in outputs.items():
 (S/rel).write_bytes(after);p=O/'candidate'/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(after)
(O/'exact-edits-and-inverse.json').write_text(json.dumps(receipts,indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps([{k:r[k] for k in ['path','before_bytes','after_bytes','after_sha256','inverse_whole_exact']} for r in receipts]))
