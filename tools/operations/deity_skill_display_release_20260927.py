"""Promote qualified learned-state icon checks; no DB or client migration."""
import argparse
from contextlib import closing
import json
import sqlite3
from . import deity_portrait_release_20260927 as shared

base=shared.base
RECEIPT=base.ROOT/'artifacts/playtests/private-deity-skills-20260927-08/run-result.json'

def qualify():
    result=shared.read(RECEIPT);ui=result['ui']
    shared.require(result['accepted'] and result['server_sha256']==base.sha(shared.CANDIDATE),
                   'Same candidate hidden-client acceptance required')
    shared.require(all(result[k] for k in ('source_db_unchanged','live_client_unchanged','private_client_unchanged')),
                   'Fixture/client changed')
    shared.require(base.sha(base.CLIENT)==shared.CLIENT_SHA,'Current client changed')
    shared.require(ui['desktop_before']==ui['desktop_final'],'Input desktop changed')
    skills=ui['deity_native_skills'];pages=ui['deity_native_skill_pages']
    shared.require(skills['owned_rows']==16 and skills['learned_instances']==1600 and
        skills['distinct_definitions']==409 and skills['full_records_match_source'] and
        skills==ui['deity_native_skills_after'],'Capacity/source/state qualification incomplete')
    shared.require(pages['distinct_definitions']==409 and pages['icons_checked']==500 and
        len(pages['pages'])==20 and len(pages['reverse_pages'])==10 and pages['page_controls']==[42,43],
        'Actual bidirectional page qualification incomplete')
    shared.require(ui['skill_icon_audit']['total']==448 and ui['skill_icon_audit']['display_eligible']==409,
        'Full native resource audit missing')
    shared.require('NATIVE_CLIENT_DIAGNOSTIC' not in (RECEIPT.parent/'server.log').read_text('utf8',errors='replace'),
        'Native diagnostic remains')

def stage(release):
    # Reuse the reviewed executable-only deployment: idle-player gate,
    # exact stopped-state save/schema preservation and executable-only rollback.
    original=shared.qualify
    try:
        shared.qualify=qualify
        info=shared.stage(release)
    finally:shared.qualify=original
    database=base.ROOT/info['live_database']
    with closing(sqlite3.connect(database.resolve().as_uri()+'?mode=ro',uri=True)) as db:
        for (blob,) in db.execute('select skills from character_deities'):
            shared.require(len(blob)%4==0,'Malformed stored skills')
            for at in range(0,len(blob),4):
                kind,identity=blob[at+2:at+4]
                available=(kind==0 and 1<=identity<=119 or kind==1 and (1<=identity<=72 or 89<=identity<=129) or
                    kind==2 and (1<=identity<=62 or 69<=identity<=87) or
                    kind==3 and (1<=identity<=83 or 99<=identity<=111))
                shared.require(available,'Existing owned skill lacks native icon; preserve save and investigate')
    info.update(scope='Current-client learned-skill display preflight.409 usable icons/39 unavailable; all448 definitions retained. No learning grants, cast rules or formula claim.',
                client_receipt=str(RECEIPT),
                qualification=str(RECEIPT),owned_capacity=[16,100],definition_catalog=448,display_eligible=409,
                unsafe_icons=39,player_instances_created=0)
    shared.save(release/'manifest.json',info);return info

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode',choices=('stage','apply','verify'));parser.add_argument('--name',required=True)
    args=parser.parse_args()
    shared.require(args.name.startswith('deity-skill-display-') and '/' not in args.name and '\\' not in args.name,
                   'Invalid release name')
    operation={'stage':stage,'apply':shared.apply,'verify':shared.verify}[args.mode]
    print(json.dumps(operation(base.ROOT/'artifacts/releases'/args.name)))
