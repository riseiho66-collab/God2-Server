"""Install the owner's language-specific fonts without changing the server."""
import json,shutil,struct,subprocess,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from tools.operations import native_quest_catalog_release as managed
from tools.operations import verify_frozen_chat_20260927 as frozen
ROOT=managed.ROOT
RELEASE=ROOT/'artifacts/releases/streamer-vector-natural-fonts-20260927-02'
MODULE=ROOT.parent/'Launcher-src/launcher-native/build/Release/x86/ClientFonts/candidate.json'
def require(value,message):
    if not value:raise RuntimeError(message)
def main(receipt):
    frozen.main()
    module=json.loads(MODULE.read_text('utf-8'));evidence=json.loads(receipt.read_text('utf-8'))
    require(evidence['accepted'] and evidence['ui']['accepted'],'Native two-language acceptance missing')
    require(evidence['before']['private_client']==module['candidate_sha256'],'Tested client mismatch')
    require(len(evidence['ui'].get('login_head_badges',{}))==2,'Own head badge on initial login not tested')
    require(len(evidence['ui'].get('head_badges_before_chat',{}))==4,'Mutual head badges after scene transition not tested')
    require(len(evidence['ui'].get('head_style_3',{}))==4 and len(evidence['ui'].get('head_style_0',{}))==4,'Privilege update/removal not tested')
    require(all(v[13]>=700 and v[14]<700 for v in evidence['ui']['streamer_diagnostics'].values()),'Actual GDI bold/regular distinction missing')
    require(managed.sha(managed.CLIENT)==module.get('deployment_base_sha256',module['source_sha256']),'Installed client changed')
    require(managed.sha(managed.ACTIVE)==evidence['server_sha256'],'Server changed')
    source=Path(module['candidate']);require(managed.sha(source)==module['candidate_sha256'],'Candidate changed')
    # Do not replace an image while the user's game is running.
    import psutil
    require(not any(p.info['exe'] and Path(p.info['exe'])==managed.CLIENT for p in psutil.process_iter(['exe'])),'Game still running; candidate retained')
    RELEASE.mkdir(exist_ok=False)
    shutil.copy2(managed.CLIENT,RELEASE/'God2.before.exe');shutil.copy2(MODULE,RELEASE/'candidate.json');shutil.copy2(receipt,RELEASE/'native-acceptance.json')
    raw=bytearray(source.read_bytes());needle=bytes.fromhex('68 26 0a 00 00 68 9c 47 5b 00');require(raw.count(needle)==1,'Private port pin');at=raw.index(needle);struct.pack_into('<I',raw,at+1,2592)
    (RELEASE/'God2.candidate.exe').write_bytes(raw)
    try:
        shutil.copy2(RELEASE/'God2.candidate.exe',managed.CLIENT)
        si=subprocess.STARTUPINFO();si.dwFlags|=subprocess.STARTF_USESHOWWINDOW;si.wShowWindow=0
        result=subprocess.run([str(managed.CLIENT.parent/'God2LauncherSupport.exe'),'/verify-client'],cwd=managed.CLIENT.parent,startupinfo=si,creationflags=managed.FLAGS,timeout=15)
        require(result.returncode==0,'Player launcher rejected updated client')
    except BaseException:
        shutil.copy2(RELEASE/'God2.before.exe',managed.CLIENT);raise
    info={'deployed':True,'client_sha256':managed.sha(managed.CLIENT),'server_pid':managed.listener(allow_players=True),'server_unchanged':managed.sha(managed.ACTIVE)==evidence['server_sha256'],'database_modified':False,'fonts':evidence['ui']['native_fonts'],'acceptance':str(receipt),'ordinary_text_bold':False,'privileged_message_bold':True,'launcher_verified':True}
    (RELEASE/'verification.json').write_text(json.dumps(info,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    native=ROOT.parent/'Launcher-src/launcher-native'
    for f in ('src/Support/ClientFonts.cpp','tools/Build-ClientFonts.py'):shutil.copy2(native/f,RELEASE/Path(f).name)
    for f in ('src/Support/StreamerStyle.cpp','src/Support/VectorBadge.h','src/Support/StreamerVectors.h','tools/Build-StreamerStyle.py','tools/Build-StreamerVectors.py'):shutil.copy2(native/f,RELEASE/Path(f).name)
    shutil.copytree(native/'src/Support/StreamerAssets/Vector',RELEASE/'Vector')
    shutil.copy2(native/'build/Release/x86/StreamerStyle/candidate.json',RELEASE/'streamer-candidate.json')
    print(json.dumps(info,ensure_ascii=False))
if __name__=='__main__':main(Path(sys.argv[1]).resolve())
