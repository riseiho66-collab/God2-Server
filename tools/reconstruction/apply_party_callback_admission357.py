from pathlib import Path
import hashlib,json,subprocess
R=Path('C:/Users/risei/Desktop/God2/God2-Server');D=Path(__file__).resolve().parent
P=D.parent/'round357-party-callback-admission-proposal'
HEAD='b5a2afd1364c50613525f07757ba31350dad9882'
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=R).decode().strip()==HEAD
names=['src/net/Session.h','src/net/Session.cpp','src/core/Application.cpp','src/game/OwnedPartyPreviewTransport.h']
original={f:(R/f).read_bytes() for f in names};data=dict(original);edits=[]
def sha(b):return hashlib.sha256(b).hexdigest()
for f,b in original.items():
    assert b==(P/'whole'/f).read_bytes();p=D/'before'/f;p.parent.mkdir(parents=True,exist_ok=True);assert not p.exists();p.write_bytes(b)
def edit(f,old,new):
    o=old.encode();n=new.encode()
    if data[f].count(o)!=1:o=old.replace('\n','\r\n').encode();n=new.replace('\n','\r\n').encode()
    assert data[f].count(o)==1,(f,old[:100],data[f].count(o))
    data[f]=data[f].replace(o,n,1);edits.append({'source':f,'before_hex':o.hex(),'after_hex':n.hex()})
H='src/net/Session.h';C='src/net/Session.cpp';A='src/core/Application.cpp';T='src/game/OwnedPartyPreviewTransport.h'
edit(H,'''    // Private actual normal-entry output recipient, minted only by its OWN
    // synchronous world callback after local S2A Written. No peer TLS mint,
    // ACK, native adoption, lease or gameplay entitlement is supplied.
''','''    // Private actual Written normal-entry output recipient, minted by its OWN
    // callback or the trusted SAME game owner from its exact private INIT.
    // No peer TLS impersonation, ACK, adoption or gameplay entitlement.
''')
edit(H,'''    // Actual ORIGINAL callback response FIFO custody, independent of push
''','''    // Whole actual OWN callback admission, independent of response/push FIFO.
    // Empty accepted response has no Write. Admitted is never Written/ACK.
    enum class NormalWorldCallbackAdmissionStatus {Pending,Admitted,Failed};
    class NormalWorldCallbackAdmission {
    public:
        NormalWorldCallbackAdmission(const NormalWorldCallbackAdmission&)=default;
        NormalWorldCallbackAdmission& operator=(const NormalWorldCallbackAdmission&)=default;
        NormalWorldCallbackAdmissionStatus status() const noexcept;
        void reject() const noexcept; // May only fail Pending, never admit.
    private:
        friend class Session;
        friend struct Impl;
        struct Data;
        explicit NormalWorldCallbackAdmission(std::shared_ptr<Data> data):data_(std::move(data)) {}
        std::shared_ptr<Data> data_;
    };
    // Actual ORIGINAL callback response FIFO custody, independent of push
''')
edit(H,'''    // Own actual callback only; reuse one private Data through split inner runs.
''','''    // One actual OWN complete callback Data, reused by its C91 prefix flights.
    std::optional<NormalWorldCallbackAdmission> capture_normal_world_callback_admission(const NormalWorldInitialization&);
    bool normal_world_callback_admission_current_on_game(const NormalWorldCallbackAdmission&) const;
    // Own actual callback only; reuse one private Data through split inner runs.
''')
edit(C,'''thread_local std::atomic<Session::NormalWorldResponseStatus>* observed_normal_response_status=nullptr;
''','''thread_local std::atomic<Session::NormalWorldResponseStatus>* observed_normal_response_status=nullptr;
thread_local std::atomic<Session::NormalWorldCallbackAdmissionStatus>* observed_callback_admission_status=nullptr;
''')
edit(C,'''    if(observed_normal_response_status) {
''','''    if(observed_callback_admission_status) {
        auto pending=Session::NormalWorldCallbackAdmissionStatus::Pending;
        observed_callback_admission_status->compare_exchange_strong(pending,Session::NormalWorldCallbackAdmissionStatus::Failed);
    }
    if(observed_normal_response_status) {
''')
edit(C,'''        observed_response_status=nullptr;observed_normal_response_status=nullptr;
''','''        observed_response_status=nullptr;observed_normal_response_status=nullptr;observed_callback_admission_status=nullptr;
''')
edit(C,'''        observed_response_status=nullptr;observed_normal_response_status=nullptr;observed_response_poison=nullptr;observed_world_callback=nullptr;
''','''        observed_response_status=nullptr;observed_normal_response_status=nullptr;observed_callback_admission_status=nullptr;observed_response_poison=nullptr;observed_world_callback=nullptr;
''')
edit(C,'''struct Session::NativePkEntryHold::Data {
''','''struct Session::NormalWorldCallbackAdmission::Data {
    const std::thread::id game_thread=std::this_thread::get_id();
    const std::shared_ptr<NormalWorldOutputHandle::Data> source;
    std::atomic<NormalWorldCallbackAdmissionStatus> status{NormalWorldCallbackAdmissionStatus::Pending};
    explicit Data(std::shared_ptr<NormalWorldOutputHandle::Data> actual):source(std::move(actual)) {}
};
Session::NormalWorldCallbackAdmissionStatus Session::NormalWorldCallbackAdmission::status() const noexcept {
    return data_->status.load();
}
void Session::NormalWorldCallbackAdmission::reject() const noexcept {
    auto pending=NormalWorldCallbackAdmissionStatus::Pending;
    data_->status.compare_exchange_strong(pending,NormalWorldCallbackAdmissionStatus::Failed);
}

struct Session::NativePkEntryHold::Data {
''')
edit(C,'''    std::shared_ptr<NormalResponsePending> normal_response_callback_capture; // Serial game callback ONLY.
''','''    std::shared_ptr<NormalResponsePending> normal_response_callback_capture; // Serial game callback ONLY.
    struct NormalCallbackPending {
        const std::shared_ptr<NormalWorldCallbackAdmission::Data> receipt;
        explicit NormalCallbackPending(std::shared_ptr<NormalWorldCallbackAdmission::Data> data):receipt(std::move(data)) {}
        void fail() noexcept {
            auto pending=NormalWorldCallbackAdmissionStatus::Pending;
            receipt->status.compare_exchange_strong(pending,NormalWorldCallbackAdmissionStatus::Failed);
        }
        ~NormalCallbackPending(){fail();}
    };
    std::shared_ptr<NormalCallbackPending> normal_callback_admission_capture; // Actual whole game callback ONLY.
''')
edit(C,'''            s.normal_response_callback_capture.reset(); // Independent private original-response attempt.
''','''            s.normal_response_callback_capture.reset(); // Independent private original-response attempt.
            s.normal_callback_admission_capture.reset(); // Unhanded whole-callback Attempt fails, not Data-only Pending.
''')
edit(C,'''                    state.normal_response_callback_capture.reset();
''','''                    state.normal_response_callback_capture.reset();
                    state.normal_callback_admission_capture.reset();
''')
edit(C,'''                        accepted=result.has_value();
                        if(result) response=std::move(*result);
''','''                        accepted=result.has_value() && !observation_scope.response_poisoned;
                        if(result) response=std::move(*result);
''')
old='''                   (s.normal_response_callback_capture && s.normal_response_callback_capture->receipt->armed.load()))accepted=false;
'''
new='''                   s.normal_callback_admission_capture ||
                   (s.normal_response_callback_capture && s.normal_response_callback_capture->receipt->armed.load()))accepted=false;
'''
o=old.encode();n=new.encode()
if data[C].count(o)!=2:o=old.replace('\n','\r\n').encode();n=new.replace('\n','\r\n').encode()
assert data[C].count(o)==2
# Two exact distinct occurrences, retained as one deterministic multiplicity edit.
data[C]=data[C].replace(o,n);edits.append({'source':C,'before_hex':o.hex(),'after_hex':n.hex(),'multiplicity':2})
edit(C,'''            auto normal_response=std::exchange(s.normal_response_callback_capture,{});
''','''            auto normal_response=std::exchange(s.normal_response_callback_capture,{});
            const auto admission=std::exchange(s.normal_callback_admission_capture,{});
            if(admission && (!accepted || admission->receipt->status.load()!=NormalWorldCallbackAdmissionStatus::Pending ||
               !self->normal_world_callback_admission_current_on_game(NormalWorldCallbackAdmission(admission->receipt)))) {
                admission->fail();accepted=false;
            }
''')
edit(C,'''            try {asio::post(s.strand,[self,accepted,terminal_ack,response_write,normal_response,response=std::move(response),
''','''            if(admission && !accepted)admission->fail(); // Existing response-prefix checks apply symmetrically.
            try {asio::post(s.strand,[self,accepted,terminal_ack,response_write,normal_response,admission,response=std::move(response),
''')
edit(C,'''                                   normal_response->receipt->status.load()==NormalWorldResponseStatus::Pending) {
''','''                                   normal_response->receipt->status.load()==NormalWorldResponseStatus::Pending &&
                                   (!admission || (admission->receipt->status.load()==NormalWorldCallbackAdmissionStatus::Pending &&
                                    s.normal_output_transport_current_locked(admission->receipt->source)))) {
''')
edit(C,'''                        } else {
                            s.write_bytes+=bytes->size();s.writes.push_back({bytes,{}});
                            s.writes.back().observed_response=response_write;
                        }
''','''                        } else if(admission) {
                            bool queued=false;
                            {
                                std::lock_guard lock(admission->receipt->source->sync->mutex);
                                if(admission->receipt->status.load()==NormalWorldCallbackAdmissionStatus::Pending &&
                                   s.normal_output_transport_current_locked(admission->receipt->source)) {
                                    s.writes.push_back({bytes,{}});s.write_bytes+=bytes->size();
                                    s.writes.back().observed_response=response_write;queued=true;
                                }
                            }
                            if(!queued){admission->fail();s.fail("Original callback prefix source retired");return;}
                        } else {
                            s.write_bytes+=bytes->size();s.writes.push_back({bytes,{}});
                            s.writes.back().observed_response=response_write;
                        }
''')
edit(C,'''                    s.resume_world_input();
                } catch(...) { s.fail("Recovered world response failed"); }
            });}catch(...) {
                if(normal_response)normal_response->fail(); // Before preserving the existing rethrow/context-abort path.
''','''                    s.resume_world_input();
                    // Complete actual callback only, after all throwing work.
                    // Empty response creates no Write; a nonempty true prefix
                    // has already queued above and cannot be rolled back.
                    if(admission) {
                        bool admitted=false;
                        {
                            std::lock_guard lock(admission->receipt->source->sync->mutex);
                            auto pending=NormalWorldCallbackAdmissionStatus::Pending;
                            if(s.normal_output_transport_current_locked(admission->receipt->source))
                                admitted=admission->receipt->status.compare_exchange_strong(pending,NormalWorldCallbackAdmissionStatus::Admitted);
                        }
                        if(!admitted){admission->fail();s.fail("Actual callback admission source retired");return;}
                    }
                } catch(...) { s.fail("Recovered world response failed"); }
            });}catch(...) {
                if(admission)admission->fail(); // Post/drop never leaves retained Data Pending.
                if(normal_response)normal_response->fail(); // Before preserving the existing rethrow/context-abort path.
''')
edit(C,'''std::optional<Session::NormalWorldResponseAttempt> Session::capture_normal_world_response(
''','''std::optional<Session::NormalWorldCallbackAdmission> Session::capture_normal_world_callback_admission(
        const NormalWorldInitialization& initialization) {
    if(observed_world_callback!=this || !observed_response_poison || *observed_response_poison) {
        poison_world_response();
        throw std::logic_error("Callback admission requires its own actual unpoisoned callback");
    }
    if(const auto existing=impl_->normal_callback_admission_capture) {
        const NormalWorldCallbackAdmission result(existing->receipt);
        if(existing->receipt->source->initialization==initialization.data_ &&
           result.status()==NormalWorldCallbackAdmissionStatus::Pending &&
           normal_world_callback_admission_current_on_game(result))return result;
        poison_world_response();existing->fail();
        throw std::logic_error("Actual callback admission identity changed");
    }
    auto source=capture_normal_world_output(initialization);
    if(!source)return std::nullopt;
    auto data=std::make_shared<NormalWorldCallbackAdmission::Data>(source->data_);
    impl_->normal_callback_admission_capture=std::make_shared<Impl::NormalCallbackPending>(data);
    observed_callback_admission_status=&data->status;
    return NormalWorldCallbackAdmission(std::move(data));
}
bool Session::normal_world_callback_admission_current_on_game(const NormalWorldCallbackAdmission& admission) const {
    const auto data=admission.data_;
    if(!data || data->game_thread!=std::this_thread::get_id() ||
       data->status.load()==NormalWorldCallbackAdmissionStatus::Failed)return false;
    // Existing predicate proves actual Entry thread/Session before bare IDs.
    return normal_world_output_current_on_game(NormalWorldOutputHandle(data->source));
}
std::optional<Session::NormalWorldResponseAttempt> Session::capture_normal_world_response(
''')
edit(A,'''                    struct DirectoryDispatch {bool reading=false,reentered=false;};
''','''                    struct DirectoryDispatch {
                        bool reading=false,reentered=false,committed_preview=false;
                        std::optional<Session::NormalWorldCallbackAdmission> admission;
                        void reject_admission() noexcept {if(admission)admission->reject();}
                    };
''')
edit(A,'''                        if(dispatch->reading) {dispatch->reentered=true;owned_party_directory->disconnect(session);return;}
''','''                        if(dispatch->reading) {dispatch->reentered=true;dispatch->reject_admission();owned_party_directory->disconnect(session);return;}
''')
old='''                        struct Reading {DirectoryDispatch& state;explicit Reading(DirectoryDispatch& s):state(s){state.reading=true;state.reentered=false;}~Reading(){state.reading=false;}} reading(*dispatch);
'''
new='''                        struct Reading {DirectoryDispatch& state;explicit Reading(DirectoryDispatch& s):state(s){state.reading=true;state.reentered=false;state.committed_preview=false;state.admission.reset();}~Reading(){state.admission.reset();state.committed_preview=false;state.reading=false;}} reading(*dispatch);
'''
o=old.encode();n=new.encode()
if data[A].count(o)!=2:o=old.replace('\n','\r\n').encode();n=new.replace('\n','\r\n').encode()
assert data[A].count(o)==2;data[A]=data[A].replace(o,n);edits.append({'source':A,'before_hex':o.hex(),'after_hex':n.hex(),'multiplicity':2})
# Different blacklist and client-options dispatches keep their old reentry paths.
edit(A,'''                    game_handlers.world_records=[&,original,dispatch,observe_source,publish_watchers,reconcile](Session& session,
                        std::span<const RecoveredWorldRecords::Record> records)->std::optional<std::vector<std::uint8_t>> {
                        if(dispatch->reading){dispatch->reentered=true;return {};}
''','''                    game_handlers.world_records=[&,original,dispatch,observe_source,publish_watchers,reconcile](Session& session,
                        std::span<const RecoveredWorldRecords::Record> records)->std::optional<std::vector<std::uint8_t>> {
                        if(dispatch->reading){dispatch->reentered=true;dispatch->reject_admission();return {};}
''')
edit(A,'''                                        auto prepared=party_preview_transport->prepare(sources,recipients,projections);
''','''                                        auto admission=session.capture_normal_world_callback_admission(owner->initialization);
                                        if(!admission)continue;
                                        dispatch->admission=*admission; // Same complete actual callback Data for every prefix flight.
                                        auto prepared=party_preview_transport->prepare(sources,recipients,projections,self,*admission);
''')
edit(A,'''                                    if(preview)preview->mark_committed(); // No allocation, immediately after successful CAS.
''','''                                    if(preview) {preview->mark_committed();dispatch->committed_preview=true;} // No allocation, immediately after actual CAS.
''')
edit(A,'''                                    // Actual peer FIFO custody only. Caller final rejection,
                                    // consent, Written/native ACK and all variants remain OPEN.
                                    // A postcommit exception retires/closes exact held peers;
                                    // committed state is never rolled back or retried.
                                    if(preview)preview->submit();
''','''                                    // Own registry waits for the COMPLETE actual callback
                                    // admission before any peer write. No fake empty FIFO.
                                    // Committed model prefix is never rolled back/retried;
                                    // consent, Written/native ACK and all variants remain OPEN.
                                    if(preview)preview->hand_off();
''')
edit(A,'''                                // Unsupported/missing source rejects this feature's
                                // request without breaking unrelated world/chat runs.
                                if(dispatch->reentered)return {};
''','''                                // Before a committed prefix keep old feature availability.
                                // After one, caught failure rejects its whole admission.
                                if(dispatch->committed_preview){dispatch->reject_admission();return {};}
                                if(dispatch->reentered)return {};
''')
edit(T,'''        bool committed=false,submitted=false,retired=false;
''','''        std::shared_ptr<Session> admission_owner;
        std::optional<Session::NormalWorldCallbackAdmission> admission;
        bool committed=false,deferred=false,submitted=false,retired=false;
''')
edit(T,'''            return !retired && std::all_of(sources.begin(),sources.end(),[](const auto& s){return s.current();}) &&
''','''            return !retired && admission_owner && admission &&
                admission_owner->normal_world_callback_admission_current_on_game(*admission) &&
                std::all_of(sources.begin(),sources.end(),[](const auto& s){return s.current();}) &&
''')
edit(T,'''        ~Flight(){if(!retired)retire(committed);}
''','''        void submit() {
            if(!committed || !deferred || submitted || !current() ||
               admission->status()!=Session::NormalWorldCallbackAdmissionStatus::Admitted)
                throw std::logic_error("Party preview requires actual complete callback admission");
            for(auto& recipient:recipients) {
                if(!current() || recipient.logical!=recipient.expected)
                    throw std::logic_error("Party preview exact deferred projection changed");
                recipient.attempt=recipient.peer->send_normal_world_records(recipient.handle,std::move(recipient.logical));
                if(recipient.attempt->status()==Session::NormalWorldOutputStatus::Failed)
                    throw std::logic_error("Party preview deferred submission failed");
            }
            if(!current())throw std::logic_error("Party preview source changed during deferred submission");
            submitted=true;
        }
        ~Flight(){if(!retired)retire(committed);}
''')
edit(T,'''            if(!flight_->committed || !flight_->submitted) {
''','''            if(!flight_->committed || !flight_->deferred) {
''')
start='''        void submit() {
            try {
''';end='''    private:
        friend class OwnedPartyPreviewTransport;
'''
b=data[T];sb=start.encode();eb=end.encode();assert b.count(sb)==1;lo=b.index(sb);hi=b.index(eb,lo)
edit(T,b[lo:hi].decode(),'''        // Actual two models committed; registry owns Pending admission.
        // No allocation, send, callback or peer close at this handoff.
        void hand_off() noexcept {flight_->deferred=true;}
''')
edit(T,'''            const std::map<std::uint64_t,std::vector<std::uint8_t>>& projections) {
''','''            const std::map<std::uint64_t,std::vector<std::uint8_t>>& projections,
            const std::shared_ptr<Session>& caller,const Session::NormalWorldCallbackAdmission& admission) {
''')
edit(T,'''        auto flight=std::make_shared<Flight>();
''','''        if(!caller || !caller->normal_world_callback_admission_current_on_game(admission) ||
           admission.status()!=Session::NormalWorldCallbackAdmissionStatus::Pending)return std::nullopt;
        auto flight=std::make_shared<Flight>();
        flight->admission_owner=caller;flight->admission=admission;
''')
edit(T,'''        if(flight->sources.empty() || flight->sources.size()>state_->capacity-state_->held_sources ||
''','''        if(std::none_of(flight->sources.begin(),flight->sources.end(),[&](const auto& s){return s.peer==caller;}))return std::nullopt;
        if(flight->sources.empty() || flight->sources.size()>state_->capacity-state_->held_sources ||
''')
edit(T,'''            bool failed=!f->submitted;
            try {if(!f->current())failed=true;}catch(...) {failed=true;}
            bool queued=!failed;
''','''            bool failed=!f->deferred;
            try {if(!f->current())failed=true;}catch(...) {failed=true;}
            if(!failed && !f->submitted) {
                const auto status=f->admission->status();
                if(status==Session::NormalWorldCallbackAdmissionStatus::Pending){++it;continue;}
                if(status!=Session::NormalWorldCallbackAdmissionStatus::Admitted)failed=true;
                else try {f->submit();}catch(...) {failed=true;}
            }
            bool queued=!failed;
''')
for f,b in data.items():
    inverse=b
    for e in reversed(edits):
        if e['source']!=f:continue
        n=bytes.fromhex(e['after_hex']);o=bytes.fromhex(e['before_hex']);count=e.get('multiplicity',1)
        assert inverse.count(n)==count,(f,'inverse',count,inverse.count(n));inverse=inverse.replace(n,o)
    assert inverse==original[f],f
for f,b in original.items():assert (R/f).read_bytes()==b
for f,b in data.items():(R/f).write_bytes(b)
manifest=[]
for f,b in data.items():
    assert (R/f).read_bytes()==b;p=D/'candidate'/f;p.parent.mkdir(parents=True,exist_ok=True);assert not p.exists();p.write_bytes(b)
    manifest.append({'source':f,'bytes':len(b),'sha256':sha(b),'before_bytes':len(original[f]),'before_sha256':sha(original[f]),'whole_inverse_equal':True})
(D/'apply-receipt.json').write_bytes((json.dumps({'head':HEAD,'scope':'Source only; all four existing whole byte-inverses exact; no product execution','edits':edits,'candidate':manifest},indent=2)+'\n').encode())
print(json.dumps({'status':'applied','literal_edit_count':len(edits),'candidate':manifest}))
