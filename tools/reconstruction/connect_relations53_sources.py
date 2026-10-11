"""Integrate common guild/alliance source routes; no tests or deployment."""
import json
import io
from pathlib import Path
from tools.reconstruction.archive_inputs import ArchivedInputs, SERVER

BASE = 'artifacts/research/native-relations-application-candidate84-v01/'
OUT = SERVER / 'artifacts/integration/packet-connections-20261006/relations53-source'

def main():
    archive = ArchivedInputs()
    try:
        delta = json.loads(archive.read(BASE + 'source-delta.json'))
        paths = sorted({row['file'] for row in delta['edits']})
        prepared = {}
        before = {}
        for name in paths:
            target = SERVER / name
            old = target.read_bytes()
            text = io.StringIO(old.decode('utf-8'), newline=None).read()
            for row in delta['edits']:
                if row['file'] == name:
                    if text.count(row['before']) != 1:
                        raise RuntimeError('Source connection anchor changed: ' + name + ' ' + repr(row['before'][:140]))
                    text = text.replace(row['before'], row['after'])
            text = text.replace('private84/', 'relations53/')
            text = text.replace('owned_guild_relations53_private', 'owned_guild_relations53_enabled')
            text = text.replace('private_relations53', 'guild_relations53')
            text = text.replace('configured_guild_relations53_private', 'configured_guild_relations53')
            if name == 'src/core/Config.cpp':
                text = text.replace('"owned_guild_relations53_enabled"', '"owned_guild_relations53"')
                text = text.replace('if(c.owned_guild_relations53_enabled && (!c.owned_guild_succession_enabled||\n           !asio::ip::make_address(c.host).is_loopback()||c.database.parent_path().filename().string().rfind("private-relations84-",0)!=0))',
                                    'if(c.owned_guild_relations53_enabled && !c.owned_guild_succession_enabled)')
                text = text.replace('PRIVATE CUSTOM84 requires loopback, unique private-relations84-* DB and qualified83 flags',
                                    'Guild relations53 requires guild succession52')
            prepared[name] = text.encode('utf-8')
            before[name] = old
        names = list(delta['import_include_retargets']) + [
            'GuildRelations53SelectorDraft.h', 'SharedGuildApplication53Draft.h']
        for name in names:
            target = 'src/relations53/' + name
            if (SERVER / target).exists():
                raise FileExistsError(target)
            text = io.StringIO(archive.read(BASE + 'shadow/src/private84/' + name).decode('utf-8'), newline=None).read()
            text = text.replace('configured_guild_relations53_private', 'configured_guild_relations53')
            prepared[target] = text.encode('utf-8')
            before[target] = None
        # Both normal startup and the existing --migrate entry use the same
        # configured migration selector. No migration is run by this script.
        name = 'src/main.cpp'
        old = (SERVER / name).read_bytes()
        text = io.StringIO(old.decode('utf-8'), newline=None).read()
        text = '#include "relations53/GuildRelations53SelectorDraft.h"\n' + text
        anchor = 'god2::configured_guild_succession_migrations_draft(\n                config.database,{config.owned_guild_membership_enabled,config.owned_guild_announcements_enabled,config.owned_guild_officers_enabled,config.owned_guild_succession_enabled})'
        replacement = 'god2::configured_guild_relations53(\n                config.database,{config.owned_guild_membership_enabled,config.owned_guild_announcements_enabled,config.owned_guild_officers_enabled,config.owned_guild_succession_enabled,config.owned_guild_relations53_enabled})'
        if text.count(anchor) != 1:
            raise RuntimeError('Main migration source anchor changed')
        prepared[name] = text.replace(anchor, replacement).encode('utf-8')
        before[name] = old
        OUT.mkdir(parents=True, exist_ok=False)
        for name, raw in before.items():
            if raw is not None:
                backup = OUT / 'before' / name
                backup.parent.mkdir(parents=True, exist_ok=True)
                backup.write_bytes(raw)
        done = []
        try:
            for name, raw in prepared.items():
                target = SERVER / name
                target.parent.mkdir(parents=True, exist_ok=True)
                if before[name] is None:
                    with target.open('xb') as stream:
                        stream.write(raw)
                else:
                    target.write_bytes(raw)
                done.append(name)
        except BaseException:
            for name in reversed(done):
                target = SERVER / name
                if before[name] is None:
                    if target.read_bytes() == prepared[name]:
                        target.unlink()
                else:
                    target.write_bytes(before[name])
            raise
        registry = SERVER / 'docs/custom-designs.json'
        value = json.loads(registry.read_bytes())
        entries = value if isinstance(value, list) else value['designs']
        if any(row.get('id') == 'CUSTOM-0084' for row in entries):
            raise RuntimeError('CUSTOM0084 already registered; preserve its existing entry')
        entry = json.loads(archive.read(BASE + 'custom84-inactive-registration-draft.json'))
        entry.update({'status': 'SOURCE_CONNECTED_INCOMPLETE', 'activation': False,
                      'formal_registry_changed': True, 'implementation_paths': list(prepared),
                      'verification': 'Deferred by owner 2026-10-06 until all packet routes connect',
                      'replacement_plan': 'Recover missing original permission/consent/fee/time rules; retain native76/95/96 layouts',
                      'remaining': ['known native receiver cache baseline', 'native6F accepted prompt',
                                    'battle generation lifecycle', 'mixed mutation domain sequencing', 'war5/9 rules']})
        entries.append(entry)
        registry.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        result = {'kind': 'FORMAL_COMMON_GUILD_RELATIONS53_SOURCE_CONNECTION',
                  'source_paths': list(prepared), 'source_connected': True,
                  'alliance_gameplay_complete': False, 'tests_run': False, 'compiled': False,
                  'deployed': False, 'database_changed': False, 'activation': False,
                  'open_items': entry['remaining']}
        (OUT / 'connection.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
        print(json.dumps({'connected_source_files': len(prepared), 'new_modules': len(names),
                          'native76_format_connected': True, 'alliance_gameplay_complete': False}))
    finally:
        archive.close()

if __name__ == '__main__':
    main()
