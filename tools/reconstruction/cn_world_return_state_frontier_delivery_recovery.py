"""Finish a rejected static capture using immutable, byte-equal prior outputs.

Preserves incomplete first-attempt native range/tool; only file-source recovery.
"""
import hashlib
import json
from .cn_wrapper_route_frontier import ROOT
from .cn_world_return_state_frontier_delivery import NAME,main

def recover():
    out=ROOT/'artifacts/integration/packet-connections-20261006'/NAME
    receipt=json.loads((out/'recovery/attempt-01-receipt.json').read_text(encoding='utf-8'))
    if receipt['findings_existed'] or (out/'findings.json').exists():raise RuntimeError('Preserve completed output')
    tool=(out/'recovery/attempt-01-rejected/delivery-tool.py').read_bytes()
    if hashlib.sha256(tool).hexdigest()!=receipt['original_delivery_tool_sha256']:raise RuntimeError('Rejected tool differs')
    retained={}
    for row in receipt['prior_partial_files']:
        data=(out/row['path']).read_bytes()
        if len(data)!=row['bytes'] or hashlib.sha256(data).hexdigest()!=row['sha256']:raise RuntimeError('Rejected capture differs')
        retained[row['path']]=row['sha256']
    # Common delivery consumes identical retained captures. Never reissue or
    # overwrite a first-attempt file; corrected native range has a distinct name.
    main(resume=retained)

if __name__=='__main__':recover()
