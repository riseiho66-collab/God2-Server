"""Pinned death/revival source descriptions, never executable server policy."""
import argparse
import hashlib
import json
from pathlib import Path

from .recover_combat_rules import CLIENT, SKILLS, SOURCE_HASHES, read_pinned
from .recover_companion_growth import raw_lines, SOURCE_HASHES as AUX_HASHES, source_path
from .omega_assets import decode_csvz

IDS = (5518, 5539, 5542, 5543, 5544, 5545, 5546, 6808, 6809, 6810, 6872)


def build_evidence():
    decoded = decode_csvz(read_pinned(CLIENT / SKILLS, SOURCE_HASHES[SKILLS]))
    rows = []
    for row in raw_lines(decoded):
        fields = row['fields_cp950_display']
        if not fields[0].isdigit() or int(fields[0]) not in IDS:
            continue
        # Restrict to item-shaped records, not unrelated numeric tables.
        if len(fields) < 26 or not fields[2].startswith(('Spi', 'Spc')):
            continue
        item = int(fields[0])
        entry = dict(item_id=item, name=fields[4], source=row,
                     authority='description_only', executable=False,
                     description_columns=list(range(7,13)), descriptions=fields[7:13])
        if item in (6808,6809,6810):
            entry['claims'] = dict(scope='revival_skill', mp_cost_text=(66,111,222)[item-6808],
                                   hp_text=('HP1','HP30percent','HPfull')[item-6808],
                                   reach_text=(5,6,7)[item-6808], targets_text='one')
        elif item == 6872:
            entry['claims'] = dict(scope='active_buff', duration_text='60 minutes',
                                   trigger_text='combat_death', hp_text='full')
        elif item == 5539:
            entry['claims'] = dict(scope='item', effect_text='no_experience_loss_on_death_return')
        else:
            entry['claims'] = dict(scope='combat_auto_revival_item',
                                   recipient='combat_pet' if item >= 5544 else 'unspecified_in_description')
        rows.append(entry)
    if sorted(r['item_id'] for r in rows) != sorted(IDS):
        raise ValueError('Missing or duplicate pinned revival records')
    message_path = source_path('message')
    messages = decode_csvz(read_pinned(CLIENT / message_path, AUX_HASHES['message'][0]))
    if hashlib.sha256(messages).hexdigest() != AUX_HASHES['message'][1]:
        raise ValueError('Unqualified decoded message source')
    limits = [row for row in raw_lines(messages)
              if row['fields_cp950_display'][:2] in ([str(i),'1'] for i in (1285,1286,1287))]
    if len(limits) != 3:
        raise ValueError('Missing revival usage-limit messages')
    return dict(source=SKILLS, source_sha256=SOURCE_HASHES[SKILLS],
                decoded_sha256=hashlib.sha256(decoded).hexdigest(), entries=rows,
                usage_limit_messages=dict(source=message_path, source_sha256=AUX_HASHES['message'][0],
                                          records=limits, authority='description_only', numeric_limit=None),
                production_enabled=False, runtime_formula_verified=False,
                unresolved=['dead-target eligibility and target masks', 'HP percentage basis and rounding',
                            'MP debit timing', 'auto-revival priority and item consumption',
                            'ordinary defeat return destination and HP', 'ordinary death experience penalty',
                            'per-battle revival item usage limits and reset rules'])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    evidence = build_evidence()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(evidence, ensure_ascii=True, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(dict(output=str(args.output), records=len(evidence['entries']), production_enabled=False)))


if __name__ == '__main__':
    main()
