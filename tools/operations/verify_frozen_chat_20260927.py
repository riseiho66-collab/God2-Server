"""Reject changes to the owner's frozen native chat contract and dispatch.

Read-only verifier. A new owner-authorized defect repair needs a separately
reviewed baseline and current-client acceptance; this tool cannot refresh it.
"""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
BASELINE=ROOT/'artifacts/releases/streamer-privilege-20260927-01/frozen-chat.json'
START='                            if(session.state()!=SessionState::InBattle &&\n'
END='                            if(config.diagnostic_visibility_battle && pending_visibility_refresh.contains(session.id()) &&\n'

def hashes():
    source=(ROOT/'src/core/Application.cpp').read_text('utf-8')
    end=source.index(END)
    start=source.rfind(START,0,end)
    if start<0:raise RuntimeError('Frozen chat dispatch boundary missing')
    values={'src/core/Application.cpp: native chat dispatch':hashlib.sha256(source[start:end].encode()).hexdigest()}
    for name in ('src/protocol/RecoveredChat.h','src/game/DiagnosticDoorRule.h'):
        values[name]=hashlib.sha256((ROOT/name).read_bytes()).hexdigest()
    return values

def main():
    baseline=json.loads(BASELINE.read_text('utf-8'))
    if not baseline['current_client_accepted']:raise RuntimeError('Frozen baseline has no current-client acceptance')
    actual=hashes()
    if actual!=baseline['source_sha256']:raise RuntimeError('Owner-frozen chat code changed; release rejected')
    print(json.dumps({'accepted':True,'checked':list(actual),'baseline':str(BASELINE)}))

if __name__=='__main__':main()
