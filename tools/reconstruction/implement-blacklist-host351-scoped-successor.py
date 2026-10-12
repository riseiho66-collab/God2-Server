from pathlib import Path
import hashlib,json
S=Path('C:/Users/risei/Desktop/God2/God2-Server')
D=Path('C:/Users/risei/.codex/artifact-archives/god2-server/20261012/round351-blacklist-live-owner-host-implementation')
assert D.is_dir() and not any(D.iterdir())
p=S/'src/core/Application.cpp'
before=p.read_bytes(); value=before; edits=[]
def replace(old,new):
    global value
    needle=old.encode().replace(b'\r\n',b'\n');new=new.encode()
    normalized=value.replace(b'\r\n',b'\n')
    if normalized.count(needle)!=1:
        a=normalized.index(b'                // Install AFTER the final legacy/common handler selection.')
        b=normalized.index(b'                // CUSTOM-0097',a)
        assert normalized[a:b].count(needle)==1,(needle[:90],normalized[a:b].count(needle))
        start=normalized.index(needle,a,b)
    else:start=normalized.index(needle)
    end=start+len(needle)
    mapping=[];i=0
    while i<len(value):
        mapping.append(i)
        i+=2 if value[i:i+2]==b'\r\n' else 1
    mapping.append(len(value))
    old=value[mapping[start]:mapping[end]]
    assert value.count(old)==1,(old[:90],value.count(old))
    edits.append((old,new));value=value.replace(old,new,1)
replace('            struct BlacklistReplay {\r\n', '''            // CUSTOM-0096: source351 actual committed deltas for idle ready peers.
            // Queued is FIFO submission, never socket Written or client adoption.
            struct BlacklistLivePending {
                std::shared_ptr<const Session::NormalWorldOutputHandle> output;
                std::shared_ptr<const SqliteOwnedBlacklistRepository::Snapshot> before,after;
                std::optional<Session::NormalWorldOutputAttempt> attempt;
                std::vector<std::uint8_t> logical=std::vector<std::uint8_t>(21);
            };
            struct BlacklistReplay {
''')
replace('                std::shared_ptr<const SqliteOwnedBlacklistRepository::Snapshot> snapshot;\r\n            };\r\n            std::map<std::uint64_t,BlacklistReplay> blacklist_replays;', '''                std::shared_ptr<const SqliteOwnedBlacklistRepository::Snapshot> snapshot;
                bool live_disabled=false; // Never revive a stale incarnation by accidental DB equality.
                std::shared_ptr<const Session::NormalWorldOutputHandle> output;
                std::shared_ptr<BlacklistLivePending> live_pending;
            };
            std::map<std::uint64_t,BlacklistReplay> blacklist_replays;
            const auto blacklist_lifetime=std::make_shared<std::atomic_bool>(true);
            const auto retire_blacklist_output=[&](BlacklistReplay& replay) noexcept {
                if(replay.output)replay.output->revoke();
                if(replay.live_pending && replay.live_pending->output)replay.live_pending->output->revoke();
                replay.output.reset();replay.live_pending.reset();
            };
            const auto stop_blacklist_outputs=[&]() noexcept {
                blacklist_lifetime->store(false);
                for(auto& [id,replay]:blacklist_replays)retire_blacklist_output(replay);
            };
            // Called on this actual game owner. Copy all identities before any close.
            const auto settle_blacklist_output=[&](const std::shared_ptr<Session>& peer) {
                const auto at=blacklist_replays.find(peer->id());
                if(at==blacklist_replays.end() || at->second.session.lock()!=peer || !at->second.live_pending)return;
                const auto pending=at->second.live_pending;
                const auto status=pending->attempt?pending->attempt->status():Session::NormalWorldOutputStatus::Failed;
                if(status==Session::NormalWorldOutputStatus::Pending)return;
                const bool accepted=status==Session::NormalWorldOutputStatus::Queued &&
                    at->second.output==pending->output && at->second.snapshot==pending->before &&
                    !at->second.live_disabled && peer->normal_world_output_current_on_game(*pending->output);
                const auto now=blacklist_replays.find(peer->id());
                if(now==blacklist_replays.end() || now->second.session.lock()!=peer || now->second.live_pending!=pending)return;
                if(accepted){now->second.snapshot=pending->after;now->second.live_pending.reset();}
                else {now->second.live_disabled=true;retire_blacklist_output(now->second);peer->close();}
            };''')
replace('            Session::DisconnectHandler on_disconnect=[&](std::shared_ptr<Session> session) {\r\n', '''            Session::DisconnectHandler on_disconnect=[&](std::shared_ptr<Session> session) {
                    if(blacklist_lifetime->load()) {
                        const auto at=blacklist_replays.find(session->id());
                        if(at!=blacklist_replays.end() && at->second.session.lock()==session)retire_blacklist_output(at->second);
                    }
''')
replace('            std::unique_ptr<TcpServer> character_server;\r\n', '''            std::unique_ptr<TcpServer> character_server;
            // Retire before character_server and borrowed repository/maps on every unwind.
            struct BlacklistOutputLifetime {
                const decltype(stop_blacklist_outputs)& stop;
                ~BlacklistOutputLifetime(){stop();}
            } blacklist_output_guard{stop_blacklist_outputs};
''')
replace('                    game_handlers.world_ready=[&,ready](Session& session) {\r\n                        ready(session);', '''                    game_handlers.world_ready=[&,ready,lifetime=blacklist_lifetime](Session& session) {
                        if(!lifetime->load())return;
                        if(const auto at=blacklist_replays.find(session.id());at!=blacklist_replays.end() &&
                           at->second.session.lock().get()==&session)retire_blacklist_output(at->second);
                        ready(session);''')
replace('                    game_handlers.world_records=[&,original,dispatch](Session& session,\r\n                            std::span<const RecoveredWorldRecords::Record> records)->std::optional<std::vector<std::uint8_t>> {\r\n                        if(dispatch->reading)', '''                    game_handlers.world_records=[&,original,dispatch,lifetime=blacklist_lifetime](Session& session,
                            std::span<const RecoveredWorldRecords::Record> records)->std::optional<std::vector<std::uint8_t>> {
                        if(!lifetime->load())return {};
                        if(dispatch->reading)''')
replace('                        const auto held=session.shared_from_this();\r\n                        const auto account=session.account_id,character=session.character_id,battle=session.battle_generation();\r\n                        const auto phase=session.state();\r\n                        const auto current=[&] {\r\n                            return !dispatch->reentered', '''                        const auto held=session.shared_from_this();
                        settle_blacklist_output(held);
                        const auto account=session.account_id,character=session.character_id,battle=session.battle_generation();
                        const auto phase=session.state();
                        const auto current=[&] {
                            return lifetime->load() && !dispatch->reentered''')
replace('                        if(!current() && !contains_blacklist)return original(session,records);\r\n', '''                        if(!current() && !contains_blacklist) {
                            if(const auto at=blacklist_replays.find(session.id());at!=blacklist_replays.end() &&
                               at->second.session.lock()==held)retire_blacklist_output(at->second);
                            return original(session,records);
                        }
''')
replace('                                        return now.done==source.done && now.cursor==source.cursor && now.active_phase==source.active_phase && now.snapshot==source.snapshot;\r\n                                    };\r\n                                    const auto reply=owned_blacklist->handle(account,character,*request,source_current);\r\n                                    if(!reply || !source_current())return {};\r\n                                    append_logical(*reply); // Repository already COMMITted; no rollback on delivery failure.', '''                                        return now.done==source.done && now.cursor==source.cursor && now.active_phase==source.active_phase &&
                                            now.snapshot==source.snapshot && now.live_disabled==source.live_disabled &&
                                            now.output==source.output && now.live_pending==source.live_pending;
                                    };
                                    struct PreparedPeer {
                                        std::shared_ptr<Session> session;
                                        BlacklistReplay source;
                                        std::shared_ptr<BlacklistLivePending> delivery;
                                    };
                                    // Own every candidate and preallocate delivery material before this SQL operation.
                                    std::vector<PreparedPeer> peers;peers.reserve(blacklist_replays.size());
                                    for(const auto& [id,replay]:blacklist_replays) {
                                        const auto peer=replay.session.lock();
                                        if(peer && peer!=held && replay.account==account && replay.character==character)
                                            peers.push_back({peer,replay,{}});
                                    }
                                    for(auto& peer:peers) {
                                        settle_blacklist_output(peer.session);
                                        const auto at=blacklist_replays.find(peer.session->id());
                                        if(at==blacklist_replays.end() || at->second.session.lock()!=peer.session)continue;
                                        peer.source=at->second;
                                        if(peer.source.done && peer.source.snapshot && peer.source.snapshot->supported &&
                                           !peer.source.live_disabled && !peer.source.live_pending && peer.source.output &&
                                           peer.session->normal_world_output_current_on_game(*peer.source.output)) {
                                            peer.delivery=std::make_shared<BlacklistLivePending>();
                                            peer.delivery->output=peer.source.output;
                                        }
                                    }
                                    if(!source_current())return {};
                                    const auto change=owned_blacklist->handle_committed(account,character,*request,source_current);
                                    if(!change || !source_current())return {};
                                    append_logical(change->logical()); // Original reply survives no-op; durable COMMIT is never retried.
                                    const auto before=change->before_ptr(),after=change->after_ptr();
                                    // Sender source denotes its submitted reply, never an acknowledgement.
                                    if(*source.snapshot!=*before) {
                                        auto& now=blacklist_replays.at(session.id());now.live_disabled=true;
                                        retire_blacklist_output(now);
                                    } else if(change->changed())blacklist_replays.at(session.id()).snapshot=after;
                                    if(!change->changed()){++i;continue;}
                                    for(auto& peer:peers) {
                                        const auto at=blacklist_replays.find(peer.session->id());
                                        if(at==blacklist_replays.end() || at->second.session.lock()!=peer.session)continue;
                                        const auto now=at->second; // Never carry an iterator through send/close.
                                        const bool same=now.account==account && now.character==character && now.done==peer.source.done &&
                                            now.snapshot==peer.source.snapshot && now.output==peer.source.output &&
                                            now.live_pending==peer.source.live_pending && now.live_disabled==peer.source.live_disabled;
                                        if(!same)continue;
                                        if(now.live_pending) {
                                            // A previous actual delivery is still unsettled; this branch cannot chain losslessly.
                                            at->second.live_disabled=true;retire_blacklist_output(at->second);peer.session->close();continue;
                                        }
                                        if(!peer.delivery || !now.snapshot || *now.snapshot!=*before ||
                                           !peer.session->normal_world_output_current_on_game(*peer.delivery->output)) {
                                            at->second.live_disabled=true;retire_blacklist_output(at->second);continue;
                                        }
                                        const auto delivery=peer.delivery;delivery->before=now.snapshot;delivery->after=after;
                                        std::copy(change->logical().begin(),change->logical().end(),delivery->logical.begin());
                                        delivery->logical.resize(change->logical().size()); // <=21, already allocated before COMMIT.
                                        at->second.live_pending=delivery;
                                        try {delivery->attempt.emplace(peer.session->send_normal_world_records(*delivery->output,std::move(delivery->logical)));}
                                        catch(...) {
                                            const auto failed=blacklist_replays.find(peer.session->id());
                                            if(failed!=blacklist_replays.end() && failed->second.session.lock()==peer.session &&
                                               failed->second.live_pending==delivery) {
                                                failed->second.live_disabled=true;retire_blacklist_output(failed->second);
                                            }
                                            peer.session->close(); // Delivery failure cannot roll back or rerun SQL.
                                        }
                                        settle_blacklist_output(peer.session);
                                    }''')
replace('                            const auto reply=original(session,records.subspan(begin,i-begin));\r\n', '''                            const bool tick_only=std::all_of(records.begin()+begin,records.begin()+i,[](const auto& r){
                                return std::holds_alternative<RecoveredWorldRecords::Tick>(r);});
                            if(!tick_only) {
                                const auto at=blacklist_replays.find(session.id());
                                if(at!=blacklist_replays.end() && at->second.session.lock()==held) {
                                    const bool pending=bool(at->second.live_pending);
                                    retire_blacklist_output(at->second);
                                    if(pending){at->second.live_disabled=true;session.close();return {};}
                                }
                            }
                            const auto reply=original(session,records.subspan(begin,i-begin));
''')
replace('                                // this is neither socket Written nor client ACK.\r\n                            }\r\n                        }\r\n                        return wire;\r\n                    };\r\n                }\r\n                // CUSTOM-0097', '''                                // this is neither socket Written nor client ACK.
                            }
                            if(tick && current() && replay_current()) {
                                const auto source=blacklist_replays.at(session.id());
                                if(source.done && source.snapshot && source.snapshot->supported && !source.live_disabled &&
                                   !source.live_pending && !source.output) {
                                    const auto initialization=session.normal_world_initialization();
                                    if(initialization)if(auto output=session.capture_normal_world_output(*initialization)) {
                                        const auto owned=std::make_shared<const Session::NormalWorldOutputHandle>(std::move(*output));
                                        if(current() && replay_current() && blacklist_replays.at(session.id()).snapshot==source.snapshot &&
                                           !blacklist_replays.at(session.id()).live_disabled && !blacklist_replays.at(session.id()).output)
                                            blacklist_replays.at(session.id()).output=owned;
                                    }
                                }
                            }
                        }
                        return wire;
                    };
                }
                // CUSTOM-0097''')
replace('                guild_delivery_lifetime->store(false);\r\n                stopping=true;','                guild_delivery_lifetime->store(false);\r\n                stop_blacklist_outputs();\n                stopping=true;')
inverse=value
for old,new in reversed(edits):
    assert inverse.count(new)==1
    inverse=inverse.replace(new,old,1)
assert inverse==before
(D/'Application.before.cpp').write_bytes(before)
(D/'Application.candidate.cpp').write_bytes(value)
(D/'exact-edits-and-inverse.json').write_text(json.dumps({'path':'src/core/Application.cpp','before_bytes':len(before),'before_sha256':hashlib.sha256(before).hexdigest(),'after_bytes':len(value),'after_sha256':hashlib.sha256(value).hexdigest(),'inverse_exact':True,'edits':[{'before':o.decode(),'after':n.decode()} for o,n in edits]},ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
assert p.read_bytes()==before
p.write_bytes(value)
print(json.dumps({'directory':str(D),'bytes':len(value),'sha256':hashlib.sha256(value).hexdigest(),'exact_inverse':True}))
