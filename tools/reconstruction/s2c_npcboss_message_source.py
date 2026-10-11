"""Join S2C 5A/79 NPC label keys to the pinned NPCBossMessage source."""

import hashlib
import json
from pathlib import Path

import capstone

from .archive_inputs import ArchivedInputs, SERVER
from .packet_connection_inventory import BASE, IMAGE, PIN
from tools.strike_lab.omega_assets import decode_csvz


OUT = SERVER / 'artifacts/integration/packet-connections-20261006/s2c-npcboss-message-source-v2.json'
SOURCE = SERVER.parent / 'God2/Data2/Patch/Comm/message.csvZ'
SOURCE_PIN = '5cd34cce66feae96d947cd45e32984765ce625673c0fb19c73cb63d7d9178598'
DECODED_PIN = '370bd6ed9b4892f57190fc7a8dab14061b3e844b0aa9d0171611a9cbab61b5f8'
SLICES = (
    ('resource_section_dispatch_npcboss', 0x562BD, 0x56308),
    ('npcboss_loader_target_fields', 0x57A70, 0x57A8B),
    ('npcboss_world_5a_selector', 0x6AB27, 0x6AB69),
)


def main():
    if OUT.exists():
        raise FileExistsError('Preserve prior NPCBoss source evidence')
    packed = SOURCE.read_bytes()
    if hashlib.sha256(packed).hexdigest() != SOURCE_PIN:
        raise ValueError('Current NPCBoss source file changed')
    plain = decode_csvz(packed)
    if hashlib.sha256(plain).hexdigest() != DECODED_PIN:
        raise ValueError('Decoded NPCBoss source changed')
    lines = plain.splitlines(keepends=True)
    if lines[1].rstrip(b'\r\n') != b'NPCBossMessage,72':
        raise ValueError('NPCBossMessage section changed')
    source_rows = []
    offset = len(lines[0]) + len(lines[1])
    for expected_id, line in enumerate(lines[2:74], 1):
        raw = line.rstrip(b'\r\n')
        key, sep, _ = raw.partition(b',')
        if not sep or int(key) != expected_id:
            raise ValueError('NPCBossMessage source row identity changed')
        source_rows.append({
            'id': expected_id,
            'physical_line': expected_id + 2,
            'decoded_offset': offset,
            'row_sha256': hashlib.sha256(raw).hexdigest(),
            'source_cp950': raw.decode('cp950'),
        })
        offset += len(line)
    reader = ArchivedInputs()
    try:
        image = reader.read(IMAGE)
    finally:
        reader.close()
    if hashlib.sha256(image).hexdigest() != PIN:
        raise ValueError('Pinned native image changed')
    if image[0x18A11C:0x18A12B] != b'NPCBossMessage\0':
        raise ValueError('Native NPCBoss section string changed')
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    slices = []
    for name, start, end in SLICES:
        body = image[start:end]
        instructions = list(md.disasm(body, BASE+start))
        if not instructions or instructions[0].address != BASE+start or \
                instructions[-1].address+instructions[-1].size != BASE+end:
            raise ValueError('Native NPCBoss slice boundary changed: '+name)
        slices.append({
            'name':name,'begin_rva':f'{start:X}',
            'end_rva_exclusive':f'{end:X}',
            'sha256':hashlib.sha256(body).hexdigest(),
            'bytes_hex':body.hex(),
            'instructions':[{'rva':f'{i.address-BASE:X}',
                             'instruction':f'{i.mnemonic} {i.op_str}'}
                            for i in instructions],
        })
    value = {
        'format':'god2-current-native-s2c-npcboss-message-source-v2',
        'native_image':IMAGE,'native_sha256':PIN,
        'source_file':str(Path('God2/Data2/Patch/Comm/message.csvZ')),
        'source_sha256':SOURCE_PIN,'decoded_sha256':DECODED_PIN,
        'section':'NPCBossMessage','declared_count':72,
        'source_backed_ids':[1,72],
        'native_join':'resource section string at 58A11C -> 562BD branch -> 457A70 -> B2C40/B2C44; WORLD 5A reads logical+7 WORD from that table',
        'conditional_79_join':'WORLD 79 uses this same B2C40/B2C44 table only when logical+5 WORD is FFFF',
        'text_path_namespace':'WORLD 59/5B and non-FFFF 79 use distinct NPCNormalMessage B2C3A/B2C3C table',
        'source_rows':source_rows,
        'limits':[
            'Source-backed message IDs and client lookup do not establish which server-owned NPC should receive a label or when.',
            'No C2S causal pairing, original server producer, or emission authorization is proven.',
            'NPCBossMessage is a resource namespace name, not evidence that these records contain monster combat stats.',
        ],
        'slices':slices,
        'tests_builds_client_execution_deployment':False,
    }
    OUT.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'artifact':str(OUT),'source_rows':len(source_rows),'slices':len(slices)}))


if __name__=='__main__':main()
