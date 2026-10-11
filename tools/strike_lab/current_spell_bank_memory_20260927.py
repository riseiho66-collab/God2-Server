"""Qualify kind1 learned/selectable identity through real own-server packets.

Hidden desktop; existing login actions and VM_READ only. No injected selection,
cast, damage or original formula claim. Synthetic ownership is CUSTOM-0012.
"""
import hashlib
from pathlib import Path
import struct
import sys
import time

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from tools.strike_lab import current_active_battle_producer_memory_20260927 as active
from tools.strike_lab import current_skill_identity as identity

lab=active.lab
original_find_ui=lab.peer.find_ui


def configure(config):
    active.configure(config)
    config['development']['diagnostic_battle_skill_kind']=1


def capture(handle,ui,output):
    deadline=time.monotonic()+10
    while 'DIAGNOSTIC_VITALS88_SENT_AFTER_TIMER36' not in (output/'server.log').read_text('utf-8',errors='replace'):
        lab.require(time.monotonic()<deadline,'NATURAL_BATTLE_NOT_ENTERED')
        time.sleep(.1)
    exact=lab.exact
    role=struct.unpack('<I',exact(handle,ui+0x86888,4))[0]-0x90
    world=role-0x1539683c
    lab.require(world>0x10000 and ui==world+0xa7f2f6c,'WORLD_ROOT_QUALIFICATION')
    lab.require(exact(handle,role,4)==struct.pack('<I',4),'OWNED_ROLE_IDENTITY')
    source=(lab.fixture.LIVE_CLIENT.parent/identity.SOURCE).read_bytes()
    lab.require(hashlib.sha256(source).hexdigest()==identity.SOURCE_SHA256,'SKILL_SOURCE_IDENTITY')
    published=struct.unpack('<I',exact(handle,role+0x4504,4))[0]
    lab.require(exact(handle,published,len(source)-4)==source[4:],'ROLE_PUBLISHED_SKILL_BODY')
    # The battle owner is a separate allocation. Do not apply battle offsets
    # to the world object merely because both contain large embedded blocks.
    battle=published-0xa924d7c
    owner_role=struct.unpack('<I',exact(handle,battle+0x14,4))[0]
    owner_ui=struct.unpack('<I',exact(handle,battle+0x20,4))[0]
    lab.save(output/'battle-owner.json',{'world':hex(world),'role':hex(role),'ui':hex(ui),
        'published_source':hex(published),'battle':hex(battle),
        'battle_role':hex(owner_role),'battle_ui':hex(owner_ui)})
    lab.require(battle>0x10000 and owner_role==role and owner_ui==ui,'BATTLE_OWNER_RELATION')
    selector=battle+0xa9dc198
    raw=exact(handle,selector,0x3600)
    current=struct.unpack_from('<b',raw,4)[0]
    banks=raw[5]
    lab.save(output/'selector-snapshot.json',{'selector':hex(selector),'ui':hex(ui),
        'world':hex(world),'role':hex(role),'header_hex':raw[:0x20].hex(),
        'current_bank':current,'bank_count':banks,
        'banks':[{'index':i,'count':struct.unpack_from('<I',raw,0x10+i*0x2d0)[0],
                  'state_words_hex':raw[0x14+i*0x2d0:0x24+i*0x2d0].hex(),
                  'definition_pointers_hex':raw[0xdc+i*0x2d0:0xec+i*0x2d0].hex(),
                  'key_pointer':hex(struct.unpack_from('<I',raw,0x2d4+i*0x2d0)[0])}
                 for i in range(16)]})
    lab.require(0<=current<16 and 1<=banks<=16,'PRIMARY_BANK_NOT_READY')
    bank=0x10+current*0x2d0
    count=struct.unpack_from('<I',raw,bank)[0]
    state=struct.unpack_from('<H',raw,bank+4)[0]
    pointer=struct.unpack_from('<I',raw,bank+0xcc)[0]
    lab.require(count==1,'EXPECTED_ONE_SYNTHETIC_SKILL')
    lab.require(state==0x8101,'SPELL_SELECTABLE_IDENTITY_MISMATCH')
    definition=exact(handle,pointer,110)
    expected=identity.decode_definitions(source)[1,1].raw
    lab.require(definition==expected,'FULL_SPELL_DEFINITION_MISMATCH')
    return {'world':hex(world),'battle':hex(battle),'role':hex(role),'ui':hex(ui),'selector':hex(selector),
        'current_bank':current,'bank_count':banks,'entry_count':count,
        'state_word':hex(state),'definition_pointer':hex(pointer),
        'definition_hex':definition.hex(),'definition_sha256':hashlib.sha256(definition).hexdigest(),
        'source_sha256':identity.SOURCE_SHA256,'definition_identity':[1,1],
        'learned_selectable_client_accepted':True,'physical_cast_accepted':False,
        'formula_authority':'CUSTOM_TEST_NOT_NATIVE; no native formula recovered'}


if __name__=='__main__':
    active.require_source()
    lab.fixture.SOURCE_DB=active.SOURCE
    lab.configure_isolated_fixture=configure
    lab.prepare_isolated_clone=active.prepare
    lab.candidate_server=ROOT/'build-town-visibility/Release/god2-server-native-results.exe'
    # RecoveredMovementService::prepare assigns saved scene15 indoor kind2.
    lab.peer.find_ui=lambda handle,actor:original_find_ui(handle,actor,expected_map=(2,15,2))
    lab.capture=capture
    lab.__file__=__file__
    raise SystemExit(lab.main())
