"""Authorized Application SOURCE edit only; no target/API execution."""
from pathlib import Path
import hashlib,json,base64
ROOT=Path('C:/Users/risei/Desktop/God2/God2-Server')
OUT=Path(__file__).resolve().parent
p=ROOT/'src/core/Application.cpp';before=p.read_bytes();data=before;hunks=[]
assert hashlib.sha256(before).hexdigest()=='324cd6ba747df82f9624766570aa63d74fc7c0098221ae337210d5ed95cb6cb4'
def replace(old,new):
    global data
    choices=[old.encode()]
    if '\n' in old:choices.append(old.replace('\n','\r\n').encode())
    choices=[v for v in choices if data.count(v)==1]
    if len(choices)!=1:raise RuntimeError('Nonunique Application needle: '+old[:100])
    b=choices[0];a=new.replace('\n','\r\n').encode() if b'\r\n' in b else new.encode();at=data.index(b)
    data=data[:at]+a+data[at+len(b):]
    hunks.append({'offset':at,'before_b64':base64.b64encode(b).decode(),'after_b64':base64.b64encode(a).decode()})
replace('''    std::optional<SharedTaiwanWorldRecordSource::InventoryMoveBinding> binding;
    std::shared_ptr<RecoveredWorldService> service;
    bool live=true,accepting=true;
    void stop_dispatch() noexcept {
        accepting=false;
        try {if(binding)binding->invalidate_active();}catch(...) {}
    }''','''    std::optional<SharedTaiwanOwnedBagMoveSource::MutationBinding> binding;
    std::shared_ptr<RecoveredWorldService> service;
    struct MutationDraft {
        std::weak_ptr<Session> session;
        Session::NormalWorldInitialization initialization;
        std::optional<SqliteOwnedEquipmentTransaction::Committed> after;
        bool invalid=false;
        MutationDraft(std::weak_ptr<Session> actual,Session::NormalWorldInitialization entry)
            :session(std::move(actual)),initialization(std::move(entry)) {}
    };
    struct MutationResponse {
        std::weak_ptr<Session> session;
        SqliteOwnedEquipmentTransaction::Committed after;
        Session::NormalWorldInitialization initialization;
        Session::WorldResponseWrite write;
    };
    std::shared_ptr<MutationDraft> active;
    std::map<std::uint64_t,std::shared_ptr<const MutationResponse>> mutations;
    std::size_t actual_session_capacity=0;
    bool live=true,accepting=true;
    void stop_dispatch() noexcept {
        accepting=false;
        if(active)active->invalid=true;
        mutations.clear();
        try {if(binding)binding->invalidate_active();}catch(...) {}
    }''')
replace('''            auto whole_bag_moves=config.owned_whole_bag_moves_enabled?std::make_shared<WholeBagMoveHost>():nullptr;
            Session::RecoveredCharacterHandlers character_handlers;''','''            auto whole_bag_moves=config.owned_whole_bag_moves_enabled?std::make_shared<WholeBagMoveHost>():nullptr;
            if(whole_bag_moves)whole_bag_moves->actual_session_capacity=config.max_sessions;
            Session::RecoveredCharacterHandlers character_handlers;''')
replace('''                    whole_bag_moves->binding=SharedTaiwanOwnedBagMoveSource::create_for_normal_entry_with_item_material(''','''                    whole_bag_moves->binding=SharedTaiwanOwnedBagMoveSource::create_for_normal_entry_with_item_material_and_receipt(''')
replace('''                            auto committed=movement->move_committed_with_owned_material(session,*transaction,requests);
                            // A committed move may never be silently discarded
                            // because its facade was retired during publication.
                            if(!host->live || !host->accepting || host->transaction!=transaction || host->movement!=movement)
                                throw std::runtime_error("Normal-entry movement committed but host facade became stale");
                            return std::move(committed.reply); // Actual prebuilt ACKs, no wrapper repack.''','''                            const auto draft=host->active;
                            if(!draft || draft->invalid || draft->session.lock().get()!=&session || draft->after) {
                                if(draft)draft->invalid=true;
                                if(host->binding)host->binding->invalidate_active();
                                throw std::logic_error("Owned movement lacks its one actual response batch");
                            }
                            auto committed=movement->move_committed_with_owned_material_and_receipt(session,*transaction,requests);
                            // Actual aftertuple and original per-frame ACKs only;
                            // never observe/rebase a bank after this mutation.
                            if(!host->live || !host->accepting || host->transaction!=transaction || host->movement!=movement ||
                               host->active!=draft || draft->invalid || draft->after)
                                throw std::runtime_error("Normal-entry movement committed but host facade became stale");
                            draft->after.emplace(committed.committed());
                            return std::move(committed).take_movement().reply; // Actual prebuilt ACKs, no wrapper repack.''')
replace('''                            const auto dispatch=host->binding->dispatch;
                            const auto reply=dispatch(session,request);
                            if(!reply)return {};
                            if(!host->live || !host->accepting)
                                throw std::runtime_error("Whole bag move committed but host facade became stale");
                            if(reply->native_no_reply())throw std::runtime_error("Whole bag move requires its full native material reply");
                            return reply->bytes(); // Already-framed wire through the existing Session sender.''','''                            const auto draft=host->active;
                            if(!draft || draft->invalid || draft->session.lock().get()!=&session || draft->after) {
                                if(draft)draft->invalid=true;
                                host->binding->invalidate_active();
                                throw std::logic_error("Owned bag move lacks its one actual response batch");
                            }
                            const auto transaction=host->transaction;
                            const auto dispatch=host->binding->dispatch;
                            auto reply=dispatch(session,request);
                            if(!reply)return {};
                            if(!host->live || !host->accepting || host->transaction!=transaction ||
                               host->active!=draft || draft->invalid || draft->after)
                                throw std::runtime_error("Whole bag move committed but host facade became stale");
                            if(reply->native_no_reply())throw std::runtime_error("Whole bag move requires its full native material reply");
                            draft->after.emplace(reply->committed());
                            return std::move(*reply).take_wire(); // Original prebuilt wire, no repack.''')
replace('''                            const auto service=host->service;
                            return service?service->handle(session,records):std::nullopt;
                        }
                        // These always-present legacy services use independent''','''                            if(host->active) {
                                host->active->invalid=true;
                                if(host->binding)host->binding->invalidate_active();
                                throw std::logic_error("Owned mutation response facade reentered");
                            }
                            const auto initialization=session.normal_world_initialization();
                            const auto actual=session.weak_from_this().lock();
                            if(!initialization || !initialization->entry_written() || actual.get()!=&session ||
                               !session.normal_world_initialization_current(*initialization) || !host->transaction)
                                return {};
                            if(!host->mutations.contains(session.id()) && host->mutations.size()>=host->actual_session_capacity)
                                return {};
                            // Allocate the game-owned draft before any mutation.
                            // No borrowed records/span survives this callback.
                            const auto draft=std::make_shared<WholeBagMoveHost::MutationDraft>(actual,*initialization);
                            host->active=draft;
                            struct End {
                                std::shared_ptr<WholeBagMoveHost> host;
                                std::shared_ptr<WholeBagMoveHost::MutationDraft> draft;
                                ~End(){if(host->active==draft)host->active.reset();}
                            } end{host,draft};
                            const auto transaction=host->transaction;
                            const auto local=[&] {
                                return host->live && host->accepting && host->transaction==transaction && host->active==draft &&
                                    !draft->invalid && draft->session.lock().get()==&session && !session.closing() &&
                                    session.normal_world_initialization_current(draft->initialization) && draft->initialization.entry_written();
                            };
                            std::shared_ptr<const WholeBagMoveHost::MutationResponse> previous;
                            if(const auto at=host->mutations.find(session.id());at!=host->mutations.end())previous=at->second;
                            if(previous) {
                                // Pending is allowed: this passive token neither
                                // imposes a wait/Tick barrier nor grants authority.
                                if(previous->session.lock().get()!=&session ||
                                   previous->write.status()==Session::WorldResponseWriteStatus::Failed ||
                                   !session.world_response_write_current(previous->write) ||
                                   !session.normal_world_initialization_current(previous->initialization) ||
                                   !previous->initialization.entry_written() || !transaction->committed_current(previous->after) || !local())
                                    return {};
                                const auto at=host->mutations.find(session.id());
                                if(at==host->mutations.end() || at->second!=previous ||
                                   previous->write.status()==Session::WorldResponseWriteStatus::Failed)
                                    throw std::runtime_error("Owned mutation response source changed during preparation");
                            }
                            if(!local())return {};
                            const auto service=host->service;
                            auto response=service?service->handle(session,records):std::nullopt;
                            if(!draft->after)return response; // Admission rejection never invents a receipt.
                            if(!response || response->empty() || !local() || !transaction->committed_current(*draft->after) || !local())
                                throw std::runtime_error("Owned mutation committed without current original response");
                            // This is the ORIGINAL complete callback return,
                            // including each native ACK5B frame unchanged.
                            // Allocation/validation failure after COMMIT throws;
                            // no retry/rollback or native adoption is implied.
                            const auto observation=session.observe_world_response(*response);
                            const auto candidate=std::make_shared<const WholeBagMoveHost::MutationResponse>(
                                WholeBagMoveHost::MutationResponse{actual,*draft->after,draft->initialization,observation});
                            if(!local() || observation.status()==Session::WorldResponseWriteStatus::Failed)
                                throw std::runtime_error("Owned mutation response capture became stale");
                            host->mutations.insert_or_assign(session.id(),candidate);
                            return response; // Session consumes this exact raw vector through its old FIFO.
                        }
                        // These always-present legacy services use independent''')
replace('''                        std::exception_ptr failure;
                        try {if(host->binding)host->binding->release(*session);}catch(...) {failure=std::current_exception();}''','''                        // Revoke passive per-incarnation custody before any
                        // observer may throw or borrowed movement is removed.
                        if(host->active && host->active->session.lock().get()==session.get())host->active->invalid=true;
                        host->mutations.erase(session->id());
                        std::exception_ptr failure;
                        try {if(host->binding)host->binding->release(*session);}catch(...) {failure=std::current_exception();}''')
inverse=data
for h in reversed(hunks):
    a=base64.b64decode(h['after_b64']);b=base64.b64decode(h['before_b64']);at=h['offset']
    assert inverse[at:at+len(a)]==a
    inverse=inverse[:at]+b+inverse[at+len(a):]
assert inverse==before
for name,b in [('before-Application.cpp',before),('after-Application.cpp',data)]:
    if (OUT/name).exists():raise RuntimeError('immutable source snapshot exists')
    (OUT/name).write_bytes(b)
p.write_bytes(data)
result={'path':'src/core/Application.cpp','before_bytes':len(before),'before_sha256':hashlib.sha256(before).hexdigest(),
    'after_bytes':len(data),'after_sha256':hashlib.sha256(data).hexdigest(),'exact_inverse':True,'hunks':hunks}
(OUT/'main-source-manifest.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps({k:v for k,v in result.items() if k!='hunks'}))
