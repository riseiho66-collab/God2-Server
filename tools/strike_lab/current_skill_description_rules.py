"""Source-pinned skill description claims, never executable combat rules."""
import argparse
import hashlib
import json
from pathlib import Path
import re

from .recover_combat_rules import CLIENT, SKILLS, SOURCE_HASHES, read_pinned
from .recover_combat_skills import parse_skills
from .omega_assets import decode_csvz

TERMS = re.compile(r'[%\uff05\u500d]|\u50b7\u5bb3|\u547d\u4e2d|\u66b4\u64ca|\u7206\u64ca|\u6a5f\u7387')


def claim(effect, condition, factor=None, probability=None, ambiguity=None):
    return dict(effect=effect, condition=condition, factor=factor,
                probability=probability, ambiguity=ambiguity)


def annotations(item, column):
    if column == 11 and item in (6890, 6891, 6892, 6893):
        return [claim('double_damage_special_ability_excluded', 'this lifesteal skill')]
    if column == 12 and item in (6604, 6612, 6620, 6628, 6636):
        return [dict(claim('damage_duration', 'this elemental wall'), rounds=5)]
    if column == 12 and item == 6809:
        return [claim('revival_hp_fraction', 'revival skill', factor=0.3,
                      ambiguity='HP basis and rounding not established')]
    if column != 10:
        return []
    if item in (6567, 6663):
        return [claim('damage_multiplier', 'one own martial attack' if item == 6567
                      else 'one own talisman attack', factor=2)]
    if item in (6568, 6569, 6570, 6572, 6573, 6574, 6665, 6666, 6667, 6668, 6669):
        result = [claim('damage_multiplier', 'critical occurs for the described skill family', factor=2)]
        if item == 6570:
            result.append(claim('petrification', 'critical; high chance; current and next two rounds'))
        if item == 6572:
            result.append(claim('critical_chance_increase', 'target defending; very high chance'))
        if item == 6573:
            result.append(claim('speed_decrease', 'critical', ambiguity='decrease 1.5 times is not an unambiguous equation'))
        if item == 6574:
            result.append(claim('mp_decrease_multiplier', 'critical', factor=2))
        return result
    if item == 6571:
        return [claim('physical_and_magic_defense_multiplier', 'axe 1-4; protected target attacked and hit; random proc', factor=2),
                claim('counterattack_critical', 'axe 5; attacked and hit; counterattack', probability=1),
                claim('damage_multiplier', 'critical occurs', factor=2)]
    if item == 6575:
        return [claim('damage_increase', 'bow skill critical; magnitude unspecified'),
                claim('paralysis', 'very high chance; each shot rolled individually')]
    if item == 6871:
        return [claim('recovery_multiplier', 'whole party; summon deity in ordinary scene', factor=5)]
    if item == 6873:
        return [claim('recovery_item_effect_increase', 'using recovery items',
                      ambiguity='effect adds two times; x2 versus x3 not established')]
    if item == 6884:
        return [claim('status_hit_probability', 'status skill enhancement proc AND target not immune', probability=1)]
    if item == 6885:
        return [claim('recovery_multiplier', 'recovery skill critical', factor=2),
                claim('damage_multiplier', 'recovery skill critical against undead', factor=2)]
    if item == 6886:
        return [claim('ability_enhancement_multiplier', 'ability skill critical', factor=2)]
    return []


def build_ledger(client=CLIENT):
    raw = read_pinned(Path(client) / SKILLS, SOURCE_HASHES[SKILLS])
    decoded = decode_csvz(raw)
    parsed = parse_skills(decoded)
    entries = []
    for row in parsed['definitions']:
        for column in range(7, 13):
            text = row['fields'][column]
            if not TERMS.search(text):
                continue
            entries.append(dict(
                item_id=row['item_id'], name=row['name'], source_column=column,
                source_line=row['source_line'], decoded_offset=row['decoded_offset'],
                source_record_sha256=row['source_record_sha256'],
                raw_record_hex=row['raw_record_hex'], source_text=text,
                description_context=row['fields'][7:13],
                authority='description_only', runtime_skill_identity=None,
                executable=False, claims=annotations(row['item_id'], column)))
    return dict(schema_version=1, source=SKILLS, source_sha256=SOURCE_HASHES[SKILLS],
                decoded_sha256=hashlib.sha256(decoded).hexdigest(),
                column_index_base=0, line_index_base=1,
                book_records_scanned=len(parsed['definitions']), entries=entries,
                runtime_verified=False, production_enabled=False,
                unresolved=['book-to-runtime-skill identity', 'base damage equation',
                            'proc probabilities', 'rounding', 'stacking and evaluation order',
                            'runtime agreement with description'])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    ledger = build_ledger()
    payload = json.dumps(ledger, ensure_ascii=True, indent=2) + '\n'
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding='utf-8')
        print(json.dumps(dict(output=str(args.output), entries=len(ledger['entries']),
                              books=ledger['book_records_scanned'], runtime_verified=False)))
    else:
        print(payload, end='')


if __name__ == '__main__':
    main()
