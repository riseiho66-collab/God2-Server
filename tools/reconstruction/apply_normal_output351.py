"""Authorized source edits only; exact inverse checks, never compile/run target."""
from pathlib import Path
import hashlib,json
O=Path(__file__).resolve().parent
R=Path('C:/Users/risei/Desktop/God2/God2-Server/src/net')
H=lambda b:hashlib.sha256(b).hexdigest()
def main():
    changes=[]
    def edit(name):
        p=R/name;before=p.read_bytes();assert before==(O/('before-'+name)).read_bytes()
        return p,before,before
    def replace(b,old,new):
        old=old.encode();new=new.encode();assert b.count(old)==1,old[:90]
        changes.append(dict(old=old.hex(),new=new.hex()))
        return b.replace(old,new,1)
    p,h0,h=edit('Session.h');changes=[]
    anchor='    class NativeBattleSkillPublicationOwner {\n'
    h=replace(h,anchor,'''    // Private actual normal-entry output recipient, minted only by its OWN
    // synchronous world callback after local S2A Written. No peer TLS mint,
    // ACK, native adoption, lease or gameplay entitlement is supplied.
    class NormalWorldOutputHandle {
    public:
        NormalWorldOutputHandle(const NormalWorldOutputHandle&)=default;
        NormalWorldOutputHandle& operator=(const NormalWorldOutputHandle&)=default;
        void revoke() const noexcept;
    private:
        friend class Session;
        friend struct Impl;
        struct Sync;
        struct Data;
        explicit NormalWorldOutputHandle(std::shared_ptr<Data> data):data_(std::move(data)) {}
        std::shared_ptr<Data> data_;
    };
    enum class NormalWorldOutputStatus {Pending,Queued,Failed};
    class NormalWorldOutputAttempt {
    public:
        NormalWorldOutputAttempt(const NormalWorldOutputAttempt&)=default;
        NormalWorldOutputAttempt& operator=(const NormalWorldOutputAttempt&)=default;
        NormalWorldOutputStatus status() const noexcept;
    private:
        friend class Session;
        friend struct Impl;
        struct Data;
        explicit NormalWorldOutputAttempt(std::shared_ptr<Data> data):data_(std::move(data)) {}
        std::shared_ptr<Data> data_;
    };
'''+anchor)
    anchor='    // PRIVATE0083 enqueue acceptance ONLY; no native/client ACK or receipt claimed.\n'
    h=replace(h,anchor,'''    std::optional<NormalWorldOutputHandle> capture_normal_world_output(const NormalWorldInitialization&);
    bool normal_world_output_current_on_game(const NormalWorldOutputHandle&) const;
    // SAME recorded game owner can later enqueue for this recipient. Queued
    // means actual FIFO insertion only; frames may subsequently fail/close.
    NormalWorldOutputAttempt send_normal_world_records(const NormalWorldOutputHandle&,std::vector<std::uint8_t> logical);
'''+anchor)
    hd=list(changes)
    p2,c0,c=edit('Session.cpp');changes=[]
    anchor='struct Session::NativePkEntryHold::Data {\n'
    c=replace(c,anchor,'''struct Session::NormalWorldOutputHandle::Sync {
    std::mutex mutex; // Revocation/epoch retirement versus actual FIFO insertion.
    std::atomic<std::uint64_t> epoch{1}; // Saturates: no old epoch can wrap current.
};
struct Session::NormalWorldOutputHandle::Data {
    const std::shared_ptr<Sync> sync;
    const std::shared_ptr<const NormalWorldInitialization::Data> initialization;
    const std::uint64_t epoch,account,character,battle;
    const SessionState phase;
    std::atomic<bool> revoked{false};
    Data(std::shared_ptr<Sync> guard,std::shared_ptr<const NormalWorldInitialization::Data> source,
         std::uint64_t version,SessionState p)
        :sync(std::move(guard)),initialization(std::move(source)),epoch(version),
         account(initialization->entry->account),character(initialization->entry->character),
         battle(initialization->effective_battle),phase(p) {}
};
void Session::NormalWorldOutputHandle::revoke() const noexcept {
    if(!data_)return;
    std::lock_guard lock(data_->sync->mutex);
    data_->revoked.store(true);
}
struct Session::NormalWorldOutputAttempt::Data {
    std::atomic<NormalWorldOutputStatus> status{NormalWorldOutputStatus::Pending};
};
Session::NormalWorldOutputStatus Session::NormalWorldOutputAttempt::status() const noexcept {
    return data_->status.load();
}

'''+anchor)
    anchor='    std::shared_ptr<WorldResponseAttempt> world_response_callback_capture; // Serial game callback ONLY.\n'
    c=replace(c,anchor,anchor+'''    struct NormalOutputPending {
        const std::shared_ptr<NormalWorldOutputAttempt::Data> data;
        explicit NormalOutputPending(std::shared_ptr<NormalWorldOutputAttempt::Data> value):data(std::move(value)) {}
        ~NormalOutputPending() {
            auto pending=NormalWorldOutputStatus::Pending;
            data->status.compare_exchange_strong(pending,NormalWorldOutputStatus::Failed);
        }
    };
''')
    anchor='    std::atomic<std::shared_ptr<const NormalWorldInitialization::Data>> normal_initialization;\n'
    c=replace(c,anchor,anchor+'''    const std::shared_ptr<NormalWorldOutputHandle::Sync> normal_output_sync=
        std::make_shared<NormalWorldOutputHandle::Sync>();
    void retire_normal_output() noexcept {
        std::lock_guard lock(normal_output_sync->mutex);
        const auto old=normal_output_sync->epoch.load();
        if(old!=std::numeric_limits<std::uint64_t>::max())normal_output_sync->epoch.store(old+1);
    }
    // Strand checks only immutable Entry/Data and synchronized/atomic fields.
    // Caller holds Sync::mutex through final validation and FIFO insertion.
    bool normal_output_transport_current_locked(const std::shared_ptr<NormalWorldOutputHandle::Data>& data) const {
        if(!data || data->sync!=normal_output_sync || data->revoked.load() ||
           data->epoch==std::numeric_limits<std::uint64_t>::max() || data->epoch!=normal_output_sync->epoch.load())return false;
        const auto init=data->initialization;const auto entry=init->entry;
        return mode==ProtocolMode::God2CharacterConnection && !close_requested.load() &&
            owner.recovered_world_ready() && owner.state()==data->phase &&
            (data->phase==SessionState::CharacterSelected || data->phase==SessionState::InWorld) &&
            owner.battle_generation()==data->battle && init->effective_battle==data->battle &&
            normal_entry.load()==entry && normal_initialization.load()==init &&
            entry->session.lock().get()==&owner && entry->account==data->account && entry->character==data->character &&
            data->account && data->character && entry->written.load() && !entry->retired.load() && !init->tail.empty() &&
            !native_pk_pending.load() && !native_battle_pending.load() && !native_pk_terminal.load();
    }
''')
    c=replace(c,'                if(account && !s.close_requested.load()) self->account_id=account;\n','''                if(account && !s.close_requested.load()) {
                    s.retire_normal_output();
                    self->account_id=account;
                }
''')
    anchor='                          std::optional<RecoveredPostCreateSelect::Selection> native_input=std::nullopt) {\n'
    c=replace(c,anchor,anchor+'        retire_normal_output(); // Before any selection callback or game-owned identity write.\n')
    anchor='                    if(const auto old=s.normal_entry.exchange(normal_entry))old->retired.store(true);\n'
    c=replace(c,anchor,'                    s.retire_normal_output(); // Before replacement, not after new identity publication.\n'+anchor)
    anchor='    void retire_normal_initialization() noexcept {\n'
    c=replace(c,anchor,anchor+'        retire_normal_output();\n')
    anchor='    void accept_world_tail() {\n'
    c=replace(c,anchor,anchor+'        retire_normal_output(); // Before the actual world_ready observer can mutate owner state.\n')
    anchor='                    self->recovered_world_ready_.store(true);\n'
    c=replace(c,anchor,'                    s.retire_normal_output();\n'+anchor)
    anchor='void Session::send_world_records_impl(std::vector<std::uint8_t> logical,\n'
    c=replace(c,anchor,'''std::optional<Session::NormalWorldOutputHandle> Session::capture_normal_world_output(
        const NormalWorldInitialization& initialization) {
    if(observed_world_callback!=this)
        throw std::logic_error("Normal output recipient requires its own actual world callback");
    if(!normal_world_initialization_current_on_game(initialization) || !initialization.entry_written())return std::nullopt;
    std::lock_guard lock(impl_->normal_output_sync->mutex);
    const auto epoch=impl_->normal_output_sync->epoch.load();
    if(epoch==std::numeric_limits<std::uint64_t>::max())return std::nullopt;
    auto data=std::make_shared<NormalWorldOutputHandle::Data>(impl_->normal_output_sync,initialization.data_,epoch,state());
    if(!impl_->normal_output_transport_current_locked(data) ||
       !normal_world_initialization_current_on_game(initialization))return std::nullopt;
    return NormalWorldOutputHandle(std::move(data));
}
bool Session::normal_world_output_current_on_game(const NormalWorldOutputHandle& handle) const {
    const auto data=handle.data_;
    if(!data || !data->initialization || !data->initialization->entry ||
       data->initialization->entry->game_thread!=std::this_thread::get_id())return false;
    const auto actual=data->initialization->entry->session.lock();
    if(actual.get()!=this)return false; // No game-owned fields before exact thread/Session qualification.
    std::lock_guard lock(data->sync->mutex);
    return impl_->normal_output_transport_current_locked(data) &&
        account_id==data->account && character_id==data->character;
}
Session::NormalWorldOutputAttempt Session::send_normal_world_records(
        const NormalWorldOutputHandle& handle,std::vector<std::uint8_t> logical) {
    auto data=std::make_shared<NormalWorldOutputAttempt::Data>();
    const NormalWorldOutputAttempt result(data);
    const auto pending=std::make_shared<Impl::NormalOutputPending>(data);
    if(!normal_world_output_current_on_game(handle))return result;
    if(logical.empty() || logical.size()>RecoveredWorldFrame::max_logical_size) {close();return result;}
    const auto charge=logical.size()+3;
    auto budget=impl_->budget;std::shared_ptr<Reservation> reservation;
    {
        std::lock_guard lock(budget->mutex);
        if(charge<=max_buffer-budget->bytes && budget->count<max_writes) {
            reservation=std::make_shared<Reservation>(budget,charge);
            budget->bytes+=charge;++budget->count;
        }
    }
    if(!reservation) {close();return result;}
    // All game-owned capture is complete before post. Strand never reads bare
    // public account_id/character_id or invokes a game Current/source callback.
    const auto recipient=handle.data_;
    asio::post(impl_->strand,[self=shared_from_this(),recipient,logical=std::move(logical),reservation,pending]() mutable {
        auto& s=*self->impl_;
        if(s.closing || s.close_requested.load())return;
        if(s.mode!=ProtocolMode::God2CharacterConnection || s.c2s0002_state!=Impl::C2S0002State::WorldTailAccepted)return;
        try {
            auto bytes=std::make_shared<std::vector<std::uint8_t>>(RecoveredWorldFrame::encode(logical));
            if(bytes->size()>max_buffer-s.write_bytes || s.writes.size()>=max_writes) {
                s.fail("Normal world output queue limit");return;
            }
            if(!s.terminal_write_allowed())return;
            {
                std::lock_guard lock(recipient->sync->mutex);
                if(!s.normal_output_transport_current_locked(recipient))return;
                s.writes.push_back({bytes,std::move(reservation)});
                s.write_bytes+=bytes->size();
                auto expected=NormalWorldOutputStatus::Pending;
                pending->data->status.compare_exchange_strong(expected,NormalWorldOutputStatus::Queued);
            }
            if(s.writes.size()==1)s.write();
        }catch(...) {s.fail("Normal world output encoding or handoff failed");}
    });
    return result;
}
'''+anchor)
    for needle in ['    if(!impl_->native_pk_pending.compare_exchange_strong(absent,pending))\n','    if(!impl_->native_battle_pending.compare_exchange_strong(absent,pending))\n']:
        count=c.count(needle.encode());assert count in (1,2)
        old=needle.encode();new=('    impl_->retire_normal_output(); // Before actual publication/PK hold is installed.\n'+needle).encode()
        changes.append(dict(old=old.hex(),new=new.hex(),count=count));c=c.replace(old,new)
    c=replace(c,'    if (impl_->close_requested.exchange(true)) return;\n','''    impl_->retire_normal_output(); // Synchronized retirement before close publication/post.
    if (impl_->close_requested.exchange(true)) return;
''')
    c=replace(c,'    while (current != SessionState::Disconnected && !state_.compare_exchange_weak(current, state)) {}\n','''    while(current!=SessionState::Disconnected) {
        if(current!=state)impl_->retire_normal_output(); // Before phase/battle mutation, even same final pose.
        if(state_.compare_exchange_weak(current,state))break;
    }
''')
    cd=list(changes)
    for old,new,rows in [(h0,h,hd),(c0,c,cd)]:
        inv=new
        for r in reversed(rows):
            a=bytes.fromhex(r['new']);b=bytes.fromhex(r['old']);assert inv.count(a)==r.get('count',1);inv=inv.replace(a,b)
        assert inv==old
    assert R.joinpath('Session.h').read_bytes()==h0 and R.joinpath('Session.cpp').read_bytes()==c0
    R.joinpath('Session.h').write_bytes(h);R.joinpath('Session.cpp').write_bytes(c)
    v=dict(files=[dict(name='Session.h',before_sha256=H(h0),after_sha256=H(h),before_bytes=len(h0),after_bytes=len(h),changes=hd),dict(name='Session.cpp',before_sha256=H(c0),after_sha256=H(c),before_bytes=len(c0),after_bytes=len(c),changes=cd)],exact_inverse=True,scope='Source changes only; old generic sender/FIFO functions remain byte-identical')
    with (O/'apply-receipt.json').open('xb') as f:f.write((json.dumps(v,indent=2)+'\n').encode())
    for name,b in [('candidate-Session.h',h),('candidate-Session.cpp',c)]:
        with (O/name).open('xb') as f:f.write(b)
    print(json.dumps({k:v for k,v in v.items() if k!='files'}));print(json.dumps([dict(name=r['name'],bytes=r['after_bytes'],sha256=r['after_sha256']) for r in v['files']]))
if __name__=='__main__':main()
