"""Port the existing 52 native admission path to strict 53 storage/source ports.

This is source integration only. No historical tests or client runs are invoked.
"""
import hashlib
import json
from .archive_inputs import SERVER


def main():
    out = SERVER / 'artifacts/integration/packet-connections-20261006/admission53-source'
    out.mkdir(parents=True, exist_ok=False)
    src = (SERVER / 'src/db/EffectiveGuildAdmissionRepositoryDraft.cpp').read_text(encoding='utf-8-sig')
    begin = src.index('EffectiveGuildAdmissionRepositoryDraft::CreationSnapshot ')
    end = src.index('EffectiveGuildAdmissionRepositoryDraft::OfficeChanged ', begin)
    methods = src[begin:end].replace('EffectiveGuildAdmissionRepositoryDraft', 'NeighboringGuild53AdmissionRepositoryDraft').replace('admission52_detail', 'admission53_detail').replace('Created52', 'Created53').replace('create52(', 'create53(')
    methods = methods.replace('creation_snapshot(){', 'creation_snapshot(){require_enabled();')
    methods = methods.replace('const CreationSnapshot& catalog,const Original::Proof& proof){', 'const CreationSnapshot& catalog,const Original::Proof& proof){require_enabled();')
    # WORLD callbacks must not execute SQL or mutate the transaction. Preserve
    # strict53 neighboring ports' authorizer guard around both proof callbacks.
    methods = methods.replace('proof.before_write();', 'ad::immutable_world(db_,proof.before_write);').replace('proof.after_write();', 'ad::immutable_world(db_,proof.after_write);')
    path = SERVER / 'src/relations53/NeighboringGuild53AdmissionRepositoryDraft.cpp'
    original = path.read_bytes()
    (out / 'NeighboringGuild53AdmissionRepositoryDraft.cpp.before').write_bytes(original)
    text = original.decode('utf-8-sig').replace('\r\n', '\n')
    text = text.replace('#include "db/SqliteSupport.h"', '#include "db/SqliteSupport.h"\n#include "db/SqliteTradeRepository.h"')
    final = text.rfind('\n}')
    text = text[:final] + '\n' + methods + text[final:]
    path.write_text(text, encoding='utf-8')
    service = (SERVER / 'src/handlers/EffectiveGuildJoinConversationRuntimeDraft.h').read_text(encoding='utf-8-sig')
    service = service.replace('"db/EffectiveGuildAdmissionRepositoryDraft.h"', '"NeighboringGuild53AdmissionRepositoryDraft.h"').replace('"handlers/OwnedGuildSuccessionServiceDraft.h"', '"Panel53Draft.h"')
    service = service.replace('EffectiveGuildAdmissionRepositoryDraft', 'NeighboringGuild53AdmissionRepositoryDraft').replace('OwnedGuildSuccessionServiceDraft', 'Panel53Draft')
    service = service.replace('EffectiveGuildJoinConversationServiceDraft', 'GuildJoinConversation53Service').replace('EffectiveGuildJoinConversationRuntimeDraft', 'GuildJoinConversation53Runtime')
    service = service.replace('EffectiveGuildMembershipConversationServiceDraft', 'GuildMembershipConversation53Service').replace('EffectiveGuildMembershipConversationRuntimeDraft', 'GuildMembershipConversation53Runtime')
    service = service.replace('Created52', 'Created53').replace('create52(', 'create53(')
    target = SERVER / 'src/relations53/GuildJoinConversation53Runtime.h'
    with target.open('x', encoding='utf-8') as stream:
        stream.write(service)
    (out / 'connection.json').write_text(json.dumps({'format': 'source-integration-only',
        'ancestor': 'src/handlers/EffectiveGuildJoinConversationRuntimeDraft.h',
        'storage': path.relative_to(SERVER).as_posix(), 'service': target.relative_to(SERVER).as_posix(),
        'creation_source_sha256': hashlib.sha256(src[begin:end].encode()).hexdigest(),
        'tests': 'DEFERRED_BY_OWNER', 'deployment': False}, indent=2) + '\n', encoding='utf-8')
    print('Connected strict53 creation storage and native8D/6F conversation source ports.')


if __name__ == '__main__':
    main()
