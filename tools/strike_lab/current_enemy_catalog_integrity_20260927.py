"""Private C++ build + full pinned source regression. No process or formal DB use."""
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import sqlite3
import struct
import subprocess
import sys
import tempfile
from contextlib import closing

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from tools.strike_lab.import_native_enemy_display import SOURCE_ROW,pinned_rows,import_catalog

def require(ok,message):
    if not ok:raise ValueError(message)

def main():
    out=ROOT/'artifacts/research/enemy-catalog-integrity-20260927';out.mkdir(parents=True,exist_ok=True)
    rows=pinned_rows(ROOT.parent/'God2');fingerprint=bytearray()
    for row in [SOURCE_ROW,*rows]:
        for value in row:
            data=value if isinstance(value,bytes) else str(value).encode('utf8')
            fingerprint+=struct.pack('<I',len(data))+data
    digest=hashlib.sha256(fingerprint).hexdigest()
    require(digest=='677c274ea71e917914455f5939564fe9080ea584dd3cabbb7d653648a6316e94','Qualified fingerprint changed')
    where=Path(os.environ.get('ProgramFiles(x86)','C:/Program Files (x86)'))/'Microsoft Visual Studio/Installer/vswhere.exe'
    install=subprocess.check_output([str(where),'-latest','-products','*','-requires','Microsoft.VisualStudio.Component.VC.Tools.x86.x64','-property','installationPath'],text=True,timeout=30).strip()
    require(bool(install),'MSVC missing');setup=Path(install)/'VC/Auxiliary/Build/vcvars64.bat'
    settings=subprocess.check_output(f'cmd.exe /d /s /c ""{setup}" >nul && set"',text=True,timeout=30)
    env=dict(line.split('=',1) for line in settings.splitlines() if '=' in line and not line.startswith('='))
    cl=shutil.which('cl.exe',path=next(v for k,v in env.items() if k.lower()=='path'));require(bool(cl),'Compiler missing')
    result={'status':'RUNNING','fingerprint_sha256':digest,'fingerprint_bytes':len(fingerprint),'cases':[],'scope':'Disposable fixtures only; no client launch, production DB/config or shared library build.'}
    def save():(out/'evidence.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
    def run(command,label):
        p=subprocess.run(list(map(str,command)),cwd=out,env=env,text=True,errors='replace',capture_output=True,timeout=90,creationflags=subprocess.CREATE_NO_WINDOW)
        result['cases'].append({'label':label,'command':list(map(str,command)),'exit':p.returncode,'stdout':p.stdout,'stderr':p.stderr});save()
        require(p.returncode==0,label+': '+p.stdout+p.stderr)
    try:
        exe=out/'enemy-catalog-integrity.exe'
        run([cl,'/nologo','/std:c++20','/EHsc','/W4','/WX','/MD','/I'+str(ROOT/'src'),'/I'+str(ROOT/'build/_deps/sqlite_src-src'),
             ROOT/'src/db/NativeEnemyDisplayCatalog.cpp',ROOT/'tests/test_native_enemy_display_catalog_integrity.cpp',
             '/Fe:'+str(exe),'/Fo:'+str(out)+'/', '/link',ROOT/'build-town-visibility/Release/sqlite3.lib','bcrypt.lib'],'compile')
        migration=(ROOT/'src/db/Migration.cpp').read_text('utf8')
        def ddl(table):
            match=re.search(r'CREATE TABLE '+table+r'\s*\(.*?\n\);',migration,re.S)
            require(match is not None,'Missing current schema '+table);return match.group(0)
        with tempfile.TemporaryDirectory(prefix='god2-enemy-integrity-') as directory:
            root=Path(directory);baseline=root/'baseline.sqlite'
            with closing(sqlite3.connect(baseline)) as db:
                db.executescript(ddl('native_data_sources')+ddl('native_enemy_display_catalog'))
                db.executescript("CREATE TABLE schema_migrations(version INTEGER,name TEXT); INSERT INTO schema_migrations VALUES(20,'native_enemy_display_catalog');")
                db.commit()
            run([exe,'empty',baseline],'empty')
            with closing(sqlite3.connect(baseline)) as db:
                require(import_catalog(db,ROOT.parent/'God2')['inserted']==7815,'Full import failed')
            run([exe,'full',baseline],'complete pinned import')
            mutations=[
                ('missing source',"DELETE FROM native_data_sources"),
                ('source only',"DELETE FROM native_enemy_display_catalog"),
                ('missing orphan',"DELETE FROM native_enemy_display_catalog WHERE source_record_index=229"),
                ('missing visible',"DELETE FROM native_enemy_display_catalog WHERE source_record_index=7814"),
                ('rename dataset',"UPDATE native_enemy_display_catalog SET dataset_id='other'"),
                ('visibility',"UPDATE native_enemy_display_catalog SET lookup_visible=1 WHERE source_record_index=229"),
                ('raw bytes',"UPDATE native_enemy_display_catalog SET raw_record=x'312c410a' WHERE source_record_index=10"),
                ('name',"UPDATE native_enemy_display_catalog SET name_bytes=x'41' WHERE source_record_index=10"),
                ('row hash',"UPDATE native_enemy_display_catalog SET record_sha256='"+'0'*64+"' WHERE source_record_index=10"),
                ('source line',"UPDATE native_enemy_display_catalog SET source_line=source_line+1 WHERE source_record_index=10"),
                ('source offset',"UPDATE native_enemy_display_catalog SET source_offset=source_offset+1 WHERE source_record_index=10"),
                ('generation',"UPDATE native_enemy_display_catalog SET area_generation=2 WHERE source_record_index=0"),
                ('area',"UPDATE native_enemy_display_catalog SET area=16 WHERE source_record_index=10"),
                ('scene',"UPDATE native_enemy_display_catalog SET scene=scene+1 WHERE source_record_index=10"),
                ('ordinal',"UPDATE native_enemy_display_catalog SET ordinal=ordinal+1 WHERE source_record_index=10"),
                ('label',"UPDATE native_enemy_display_catalog SET source_label=source_label+1 WHERE source_record_index=10"),
            ]
            for column,value in [('source_path','wrong/file'),('source_sha256','0'*64),('decoded_sha256','0'*64),('native_image_sha256','0'*64),('source_section','Other'),('loader_rva','0x0'),('lookup_rva','0x0')]:
                mutations.append((column,"UPDATE native_data_sources SET "+column+"='"+value+"'"))
            mutations.append(('source row count','UPDATE native_data_sources SET row_count=7814'))
            for index,(label,sql) in enumerate(mutations):
                target=root/f'negative-{index}.sqlite';shutil.copy2(baseline,target)
                with closing(sqlite3.connect(target)) as db:db.execute(sql);db.commit()
                run([exe,'reject',target],label)
            # A self-consistent forged raw+digest pair still differs from the pinned full catalog.
            target=root/'forged.sqlite';shutil.copy2(baseline,target)
            with closing(sqlite3.connect(target)) as db:
                raw=b'1,forged,0,0,0,0\n'
                db.execute('UPDATE native_enemy_display_catalog SET raw_record=?,record_sha256=? WHERE source_record_index=229',(raw,hashlib.sha256(raw).hexdigest()));db.commit()
            run([exe,'reject',target],'forged raw plus matching row digest')
        result['status']='PASS';save();print(json.dumps({'status':'PASS','commands':len(result['cases']),'output':str(out)}))
    except BaseException as error:result['status']='FAIL';result['error']=repr(error);save();raise

if __name__=='__main__':main()
