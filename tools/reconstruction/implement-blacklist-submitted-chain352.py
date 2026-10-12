from pathlib import Path
import json,hashlib,subprocess
S=Path('C:/Users/risei/Desktop/God2/God2-Server');A=Path('C:/Users/risei/.codex/artifact-archives/god2-server/20261013');D=A/'round352-blacklist-submitted-chain-host-implementation'
D.mkdir(exist_ok=False);p=S/'src/core/Application.cpp';before=p.read_bytes();value=before;edits=[]
assert hashlib.sha256(before).hexdigest()=='971a77a40c52162403c61e5fcaacb3fe8851ac024c9e0f9970889b1f9f4d3553'
assert before==subprocess.check_output(['git','show','31d79bad16484d0a2021a938cb1a99b58231ba14:src/core/Application.cpp'],cwd=S)
def replace(old,new):
 global value
 old=old.encode();new=new.encode();assert value.count(old)==1,(old[:100],value.count(old));value=value.replace(old,new,1);edits.append(dict(old=old.decode(),new=new.decode()))
replace('''            // CUSTOM-0096: source351 actual committed deltas for idle ready peers.
            // Queued is FIFO submission, never socket Written or client adoption.
            struct BlacklistLivePending {
                std::shared_ptr<const Session::NormalWorldOutputHandle> output;
                std::shared_ptr<const SqliteOwnedBlacklistRepository::Snapshot> before,after;
                std::optional<Session::NormalWorldOutputAttempt> attempt;
                std::vector<std::uint8_t> logical=std::vector<std::uint8_t>(21);
            };''','''            // CUSTOM-0096: source352 ordered submitted endpoints and actual attempt chain.
            // Same game owner posts deltas and original responses to the same peer strand.
            // This is neither native cache adoption nor an original-response Queued receipt.
            constexpr std::size_t blacklist_attempt_limit=256; // Existing Session max_writes transport bound.
            struct BlacklistLivePending {
                const std::shared_ptr<const Session::NormalWorldOutputHandle> output;
                const std::shared_ptr<const BlacklistLivePending> previous;
                const std::size_t depth;
                std::optional<Session::NormalWorldOutputAttempt> attempt;
                std::vector<std::uint8_t> logical=std::vector<std::uint8_t>(21);
                BlacklistLivePending(std::shared_ptr<const Session::NormalWorldOutputHandle> handle,
                        std::shared_ptr<const BlacklistLivePending> prior)
                    :output(std::move(handle)),previous(std::move(prior)),depth(previous?previous->depth+1:1) {}
                // No per-node snapshots or fictitious own-reply nodes: only actual attempts.
            };''')
replace('''            // Called on this actual game owner. Copy all identities before any close.
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
            };''','''            // Pure Current: safe inside the existing SQL source callback. Never settle,
            // mutate a map, close a peer or invoke a game/source observer here.
            const auto blacklist_chain_current=[&](const std::shared_ptr<Session>& peer,const BlacklistReplay& replay) {
                if(!replay.live_pending)return true;
                if(replay.live_disabled || !replay.output || !replay.snapshot || !replay.snapshot->supported ||
                   !peer->normal_world_output_current_on_game(*replay.output))return false;
                std::size_t count=0;
                for(std::shared_ptr<const BlacklistLivePending> node=replay.live_pending;node;node=node->previous) {
                    if(++count>blacklist_attempt_limit || node->output!=replay.output ||
                       node->depth!=replay.live_pending->depth-count+1 || !node->attempt ||
                       node->attempt->status()==Session::NormalWorldOutputStatus::Failed)return false;
                }
                return count==replay.live_pending->depth;
            };
            // Called on this actual game owner. Copy all identities before any close.
            const auto settle_blacklist_output=[&](const std::shared_ptr<Session>& peer) {
                const auto at=blacklist_replays.find(peer->id());
                if(at==blacklist_replays.end() || at->second.session.lock()!=peer || !at->second.live_pending)return;
                const auto source=at->second;const auto pending=source.live_pending;
                bool accepted=blacklist_chain_current(peer,source),queued=accepted;
                if(accepted)for(std::shared_ptr<const BlacklistLivePending> node=pending;node;node=node->previous)
                    queued=queued && node->attempt->status()==Session::NormalWorldOutputStatus::Queued;
                if(accepted)accepted=peer->normal_world_output_current_on_game(*source.output);
                const auto now=blacklist_replays.find(peer->id());
                if(now==blacklist_replays.end() || now->second.session.lock()!=peer || now->second.live_pending!=pending ||
                   now->second.output!=source.output || now->second.snapshot!=source.snapshot)return;
                if(!accepted){now->second.live_disabled=true;retire_blacklist_output(now->second);peer->close();}
                else if(queued)now->second.live_pending.reset(); // Clear attempts only; never rewind the submitted endpoint.
            };''')
replace('''                                    if(source.live_pending) {
                                        // An actual incoming delta has not settled; do not commit a competing sender operation.
                                        auto& now=blacklist_replays.at(session.id());now.live_disabled=true;
                                        retire_blacklist_output(now);session.close();return {};
                                    }
''','''                                    // Earlier admitted peer posts precede this job's original response post.
                                    // Pending may continue only while its entire actual attempt chain is current.
                                    if(!blacklist_chain_current(held,source))return {};
''')
replace('''                                            now.output==source.output && now.live_pending==source.live_pending;
''','''                                            now.output==source.output && now.live_pending==source.live_pending &&
                                            blacklist_chain_current(held,now);
''')
replace('''                                           !peer.source.live_disabled && !peer.source.live_pending && peer.source.output &&
                                           peer.session->normal_world_output_current_on_game(*peer.source.output)) {
                                            peer.delivery=std::make_shared<BlacklistLivePending>();
                                            peer.delivery->output=peer.source.output;
''','''                                           !peer.source.live_disabled && peer.source.output &&
                                           (!peer.source.live_pending || peer.source.live_pending->depth<blacklist_attempt_limit) &&
                                           blacklist_chain_current(peer.session,peer.source) &&
                                           peer.session->normal_world_output_current_on_game(*peer.source.output)) {
                                            peer.delivery=std::make_shared<BlacklistLivePending>(peer.source.output,peer.source.live_pending);
''')
replace('''                                        auto& now=blacklist_replays.at(session.id());now.live_disabled=true;
                                        retire_blacklist_output(now);
                                    } else if(change->changed())blacklist_replays.at(session.id()).snapshot=after;''','''                                        auto& now=blacklist_replays.at(session.id());const bool hazard=bool(now.live_pending);
                                        now.live_disabled=true;retire_blacklist_output(now);
                                        if(hazard){session.close();return {};}
                                    } else if(change->changed())blacklist_replays.at(session.id()).snapshot=after;''')
replace('''                                        if(now.live_pending) {
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
                                        settle_blacklist_output(peer.session);''','''                                        if(!peer.delivery || !now.snapshot || *now.snapshot!=*before ||
                                           !blacklist_chain_current(peer.session,now) ||
                                           !peer.session->normal_world_output_current_on_game(*peer.delivery->output)) {
                                            const bool hazard=bool(now.live_pending);
                                            at->second.live_disabled=true;retire_blacklist_output(at->second);
                                            if(hazard)peer.session->close(); // Actual old chain cannot skip this committed edge.
                                            continue;
                                        }
                                        const auto delivery=peer.delivery;
                                        std::copy(change->logical().begin(),change->logical().end(),delivery->logical.begin());
                                        delivery->logical.resize(change->logical().size()); // <=21, already allocated before COMMIT.
                                        try {
                                            delivery->attempt.emplace(peer.session->send_normal_world_records(*delivery->output,std::move(delivery->logical)));
                                            if(delivery->attempt->status()==Session::NormalWorldOutputStatus::Failed)
                                                throw std::runtime_error("Blacklist ordered submission failed");
                                            const auto posted=blacklist_replays.find(peer.session->id());
                                            if(posted==blacklist_replays.end() || posted->second.session.lock()!=peer.session ||
                                               posted->second.output!=now.output || posted->second.live_pending!=now.live_pending ||
                                               posted->second.snapshot!=now.snapshot || posted->second.live_disabled ||
                                               !peer.session->normal_world_output_current_on_game(*delivery->output))
                                                throw std::runtime_error("Blacklist submitted source retired");
                                            // Actual successful post, immutable core after, newest ordered-submitted endpoint.
                                            // Pending is admitted transport, not FIFO Queued, Written or native adoption.
                                            posted->second.live_pending=delivery;posted->second.snapshot=after;
                                        } catch(...) {
                                            delivery->output->revoke();
                                            const auto failed=blacklist_replays.find(peer.session->id());
                                            if(failed!=blacklist_replays.end() && failed->second.session.lock()==peer.session &&
                                               failed->second.output==now.output) {
                                                failed->second.live_disabled=true;retire_blacklist_output(failed->second);
                                            }
                                            peer.session->close(); // Durable SQL is never rerun or rolled back.
                                        }
                                        settle_blacklist_output(peer.session);''')
inverse=value
for e in reversed(edits):
 old=e['old'].encode();new=e['new'].encode();assert inverse.count(new)==1;inverse=inverse.replace(new,old,1)
assert inverse==before
def put(name,b):
 with (D/name).open('xb') as f:f.write(b)
put('Application.before.cpp',before);put('Application.candidate.cpp',value)
put('exact-edits-and-inverse.json',(json.dumps(dict(path='src/core/Application.cpp',before_bytes=len(before),before_sha256=hashlib.sha256(before).hexdigest(),after_bytes=len(value),after_sha256=hashlib.sha256(value).hexdigest(),inverse_exact=True,edits=edits),indent=2)+'\n').encode())
assert p.read_bytes()==before;p.write_bytes(value)
print(json.dumps(dict(bytes=len(value),sha256=hashlib.sha256(value).hexdigest(),exact_inverse=True)))
