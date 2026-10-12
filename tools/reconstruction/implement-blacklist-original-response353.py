from pathlib import Path
import hashlib,json,subprocess
S=Path('C:/Users/risei/Desktop/God2/God2-Server');A=Path('C:/Users/risei/.codex/artifact-archives/god2-server/20261013');D=A/'round353-blacklist-original-response-host-implementation';p=S/'src/core/Application.cpp';before=p.read_bytes();value=before;edits=[]
assert before==subprocess.check_output(['git','show','618eb9cbce52632f984b45f7409407a4e465c234:src/core/Application.cpp'],cwd=S)
def replace(old,new):
 global value
 old=old.encode();new=new.encode();assert value.count(old)==1,(old[:90],value.count(old));value=value.replace(old,new,1);edits.append(dict(old=old.decode(),new=new.decode()))
replace('''            // CUSTOM-0096: source352 ordered submitted endpoints and actual attempt chain.
            // Same game owner posts deltas and original responses to the same peer strand.
            // This is neither native cache adoption nor an original-response Queued receipt.
''','''            // CUSTOM-0096: source353 actual original-response custody plus peer attempt chain.
            // Original response Queued means its validated final wire entered the FIFO.
            // Pending endpoints remain provisional, never native adoption or socket Written.
''')
replace('''                std::shared_ptr<BlacklistLivePending> live_pending;
''','''                std::shared_ptr<BlacklistLivePending> live_pending;
                std::optional<Session::NormalWorldResponseAttempt> own_response;
''')
replace('''                replay.output.reset();replay.live_pending.reset();
''','''                replay.output.reset();replay.live_pending.reset();replay.own_response.reset();
''')
replace('''            // Pure Current: safe inside the existing SQL source callback. Never settle,
''','''            const auto blacklist_pending_source=[](const BlacklistReplay& replay) {
                return bool(replay.live_pending) || (replay.own_response &&
                    replay.own_response->status()==Session::NormalWorldResponseStatus::Pending);
            };
            // Pure Current: safe inside the existing SQL source callback. Never settle,
''')
replace('''                if(!replay.live_pending)return true;
''','''                // An original endpoint must not bypass Failed custody merely because
                // this incarnation has no incoming peer attempt nodes.
                if(replay.own_response && !peer->normal_world_response_current_on_game(*replay.own_response))return false;
                if(!replay.live_pending)return true;
''')
replace('''                if(at==blacklist_replays.end() || at->second.session.lock()!=peer || !at->second.live_pending)return;
''','''                if(at==blacklist_replays.end() || at->second.session.lock()!=peer ||
                   (!at->second.live_pending && !at->second.own_response))return;
''')
replace('''                if(accepted)accepted=peer->normal_world_output_current_on_game(*source.output);
''','''                if(accepted && source.live_pending)accepted=peer->normal_world_output_current_on_game(*source.output);
''')
replace('''                   now->second.output!=source.output || now->second.snapshot!=source.snapshot)return;
''','''                   now->second.output!=source.output || now->second.snapshot!=source.snapshot ||
                   now->second.own_response!=source.own_response)return;
''')
replace('''                                    if(source.live_pending && !blacklist_invocation_current()) {
''','''                                    if(blacklist_pending_source(source) && !blacklist_invocation_current()) {
''')
replace('''                                    if(!blacklist_chain_current(held,source))return {};
                                    const auto source_current=[&] {
''','''                                    if(!blacklist_chain_current(held,source))return {};
                                    std::optional<Session::NormalWorldResponseAttempt> response_attempt;
                                    if(blacklist_invocation_current())
                                        response_attempt=session.capture_normal_world_response(*blacklist_invocation);
                                    if(source.own_response && source.own_response->status()==Session::NormalWorldResponseStatus::Pending &&
                                       (!response_attempt || *source.own_response!=*response_attempt)) {
                                        auto& now=blacklist_replays.at(session.id());now.live_disabled=true;
                                        retire_blacklist_output(now);session.close();return {};
                                    }
                                    const auto response_current=[&] {
                                        return response_attempt && session.normal_world_response_callback_current(*response_attempt);
                                    };
                                    const auto source_current=[&] {
''')
replace('''                                            now.output==source.output && now.live_pending==source.live_pending &&
                                            (!now.live_pending || blacklist_invocation_current()) && blacklist_chain_current(held,now);
''','''                                            now.output==source.output && now.live_pending==source.live_pending &&
                                            now.own_response==source.own_response && (!response_attempt || response_current()) &&
                                            (!blacklist_pending_source(now) || blacklist_invocation_current()) && blacklist_chain_current(held,now);
''')
replace('''                                    append_logical(change->logical()); // Original reply survives no-op; durable COMMIT is never retried.
                                    const auto before=change->before_ptr(),after=change->after_ptr();
                                    // Sender source denotes its submitted reply, never an acknowledgement.
                                    if(!blacklist_invocation_current() || *source.snapshot!=*before) {
                                        auto& now=blacklist_replays.at(session.id());const bool hazard=bool(now.live_pending);
                                        now.live_disabled=true;retire_blacklist_output(now);
                                        if(hazard){session.close();return {};}
                                    } else if(change->changed())blacklist_replays.at(session.id()).snapshot=after;
                                    if(!change->changed() || !blacklist_invocation_current()){++i;continue;}
''','''                                    const auto reply_begin=wire.size();
                                    append_logical(change->logical()); // Original no-op reply; durable COMMIT is never retried.
                                    const auto before=change->before_ptr(),after=change->after_ptr();
                                    const bool qualified=response_current() && blacklist_invocation_current() && *source.snapshot==*before;
                                    if(!qualified) {
                                        auto& now=blacklist_replays.at(session.id());const bool hazard=blacklist_pending_source(source);
                                        now.live_disabled=true;retire_blacklist_output(now);
                                        if(hazard){session.close();return {};}
                                    } else {
                                        // Actual append-owned framed bytes, not a substring claim about later output.
                                        // Session matches this ordered component at final frame boundaries.
                                        session.expect_normal_world_response(*response_attempt,
                                            std::span<const std::uint8_t>(wire).subspan(reply_begin));
                                        if(!response_current())return {};
                                        auto& now=blacklist_replays.at(session.id());now.own_response=*response_attempt;
                                        if(change->changed())now.snapshot=after; // Provisional until actual final FIFO Queued.
                                    }
                                    if(!change->changed() || !qualified){++i;continue;}
''')
replace('''                                            now.live_pending==peer.source.live_pending && now.live_disabled==peer.source.live_disabled;
''','''                                            now.live_pending==peer.source.live_pending && now.live_disabled==peer.source.live_disabled &&
                                            now.own_response==peer.source.own_response;
''')
replace('''                                            const bool hazard=bool(now.live_pending);
''','''                                            const bool hazard=blacklist_pending_source(now);
''')
replace('''                                               posted->second.snapshot!=now.snapshot || posted->second.live_disabled ||
''','''                                               posted->second.snapshot!=now.snapshot || posted->second.own_response!=now.own_response ||
                                               posted->second.live_disabled ||
''')
replace('''                                    const bool pending=bool(at->second.live_pending);
''','''                                    const bool pending=blacklist_pending_source(at->second);
''')
replace('''                                const auto pinned=blacklist_replays.at(session.id()).snapshot;
                                auto observed=owned_blacklist->observe(account,character,[&] {
''','''                                const auto pinned=blacklist_replays.at(session.id()).snapshot;
                                const auto prior_response=blacklist_replays.at(session.id()).own_response;
                                if(!blacklist_chain_current(held,blacklist_replays.at(session.id())))return {};
                                std::optional<Session::NormalWorldResponseAttempt> replay_response;
                                if(blacklist_invocation_current())
                                    replay_response=session.capture_normal_world_response(*blacklist_invocation);
                                if(prior_response && prior_response->status()==Session::NormalWorldResponseStatus::Pending &&
                                   (!replay_response || *prior_response!=*replay_response))return {};
                                const auto replay_response_current=[&] {
                                    return !replay_response || session.normal_world_response_callback_current(*replay_response);
                                };
                                auto observed=owned_blacklist->observe(account,character,[&] {
''')
replace('''                                    return !now.done && now.cursor==cursor && now.active_phase==active_phase && now.snapshot==pinned;
''','''                                    return !now.done && now.cursor==cursor && now.active_phase==active_phase && now.snapshot==pinned &&
                                        now.own_response==prior_response && replay_response_current() && blacklist_chain_current(held,now);
''')
replace('''                                   blacklist_replays.at(session.id()).snapshot!=pinned)return {};
                                append_logical(batch.logical);
                                auto& pending=blacklist_replays.at(session.id());pending.cursor=batch.last_row;pending.snapshot=material;
''','''                                   blacklist_replays.at(session.id()).snapshot!=pinned ||
                                   blacklist_replays.at(session.id()).own_response!=prior_response || !replay_response_current())return {};
                                const auto reply_begin=wire.size();append_logical(batch.logical);
                                if(replay_response && !batch.logical.empty()) {
                                    session.expect_normal_world_response(*replay_response,
                                        std::span<const std::uint8_t>(wire).subspan(reply_begin));
                                    if(!replay_response_current())return {};
                                    blacklist_replays.at(session.id()).own_response=*replay_response;
                                }
                                auto& pending=blacklist_replays.at(session.id());pending.cursor=batch.last_row;pending.snapshot=material;
''')
inverse=value
for e in reversed(edits):
 old=e['old'].encode();new=e['new'].encode();assert inverse.count(new)==1;inverse=inverse.replace(new,old,1)
assert inverse==before
def put(name,b):
 D.mkdir(parents=True,exist_ok=True)
 with (D/name).open('xb') as f:f.write(b)
put('Application.before.cpp',before);put('Application.candidate.cpp',value)
put('exact-edits-and-inverse.json',(json.dumps(dict(path='src/core/Application.cpp',before_bytes=len(before),before_sha256=hashlib.sha256(before).hexdigest(),after_bytes=len(value),after_sha256=hashlib.sha256(value).hexdigest(),inverse_exact=True,edits=edits),indent=2)+'\n').encode())
assert p.read_bytes()==before;p.write_bytes(value)
print(json.dumps(dict(bytes=len(value),sha256=hashlib.sha256(value).hexdigest(),exact_inverse=True)))
