"""Run the actual Win32 tick/renderer pipeline in isolation for both sides."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import wave
import array
import math

ROOT = Path(__file__).resolve().parent
PROJECT = ROOT.parents[2]

def main():
    vswhere = Path(os.environ.get('ProgramFiles(x86)', 'C:/Program Files (x86)')) / 'Microsoft Visual Studio/Installer/vswhere.exe'
    install = subprocess.check_output([str(vswhere), '-latest', '-products', '*', '-requires',
        'Microsoft.VisualStudio.Component.VC.Tools.x86.x64', '-property', 'installationPath'], text=True).strip()
    vcvars = Path(install) / 'VC/Auxiliary/Build/vcvars32.bat'
    values = subprocess.check_output(f'cmd.exe /d /s /c ""{vcvars}" >nul && set"', text=True)
    env = dict(line.split('=', 1) for line in values.splitlines() if '=' in line and not line.startswith('='))
    env['VSLANG'] = '1033'
    compiler = shutil.which('cl.exe', path=next(v for k, v in env.items() if k.lower() == 'path'))
    def sha(path):
        return hashlib.sha256(path.read_bytes()).hexdigest()
    with tempfile.TemporaryDirectory(prefix='god2-bull-pipeline-') as temporary:
        subprocess.run([compiler, '/nologo', '/std:c++20', '/EHsc', '/O2', '/W4', '/WX',
            '/DWIN32_LEAN_AND_MEAN', '/DNOMINMAX', str(ROOT / 'bull_native_pipeline_test.cpp'),
            '/Fe:test.exe', 'winmm.lib'], cwd=temporary, env=env, check=True)
        executable = Path(temporary) / 'test.exe'
        result = subprocess.run([str(executable), str(PROJECT / 'artifacts/custom-skills/thousand-bulls/visualpack')],
            cwd=temporary, capture_output=True, text=True, timeout=90)
        if result.returncode:
            raise RuntimeError(result.stderr or result.stdout)
        report = json.loads(result.stdout)
        report['executable_sha256'] = sha(executable)
        with wave.open(str(PROJECT / 'artifacts/custom-skills/thousand-bulls/visualpack/bull-stampede-native-voice.wav'), 'rb') as wav:
            assert wav.getsampwidth() == 2
            original = wav.readframes(wav.getnframes())
            whistle_bytes = int(.8373923 * wav.getframerate()) * wav.getnchannels() * 2
            tail_start = int(1.0 * wav.getframerate()) * wav.getnchannels()
        submitted = (Path(temporary) / 'audio-submitted.pcm').read_bytes()
        assert len(submitted) == len(original) and submitted[:whistle_bytes] == original[:whistle_bytes]
        baseline = array.array('h', original)[tail_start:]
        louder = array.array('h', submitted)[tail_start:]
        ratio = math.sqrt(sum(v*v for v in louder) / sum(v*v for v in baseline))
        assert ratio > 1.7 and max(abs(v) for v in louder) < 32767
        report['audio_tail_gain'] = {'rms_ratio': round(ratio, 3), 'gain_db': round(20*math.log10(ratio), 2),
            'whistle_unchanged': True, 'hard_clipped_samples': sum(abs(v) >= 32767 for v in louder)}
        # Require the same executable-level regression to reject the old bug.
        old = 'if(phase==3&&get<Byte>(cast.source,0x224+i)==9)'
        fixed = 'if(phase==3&&(cast.final_states[i]==9||get<Byte>(cast.source,0x224+i)==9))'
        source = (ROOT / 'bull_native_tick.cpp').read_text(encoding='utf-8')
        if source.count(fixed) != 1:
            raise RuntimeError('Cannot locate the pending-hit repair for negative control')
        mutated = Path(temporary)
        (mutated / 'bull_native_tick.cpp').write_text(source.replace(fixed, old), encoding='utf-8')
        shutil.copyfile(ROOT / 'bull_native_pipeline_test.cpp', mutated / 'negative.cpp')
        subprocess.run([compiler, '/nologo', '/std:c++20', '/EHsc', '/O2', '/W4', '/WX',
            '/DWIN32_LEAN_AND_MEAN', '/DNOMINMAX', '/I' + str(ROOT),
            str(mutated / 'negative.cpp'), '/Fe:negative.exe', 'winmm.lib'],
            cwd=temporary, env=env, check=True)
        negative = subprocess.run([str(mutated / 'negative.exe'),
            str(PROJECT / 'artifacts/custom-skills/thousand-bulls/visualpack')],
            cwd=temporary, capture_output=True, text=True, timeout=90)
        if negative.returncode != 1 or negative.stderr.strip() != 'shared pending count':
            raise RuntimeError('Old pending-hit defect was not detected: ' + negative.stderr)
        report['negative_control'] = {'old_condition_rejected': True,
            'failure': negative.stderr.strip()}
        (mutated / 'bull_native_tick.cpp').write_text(source, encoding='utf-8')
        renderer = (ROOT / 'bull_effect.cpp').read_text(encoding='utf-8')
        controls = [
            ('audio-owner', 'void* ui=battle?read<void*>(battle,0x20):nullptr;',
             'void* ui=battle;', 'battle to UI audio owner chain'),
            ('screen-buffer', 'void* cdx=screen&&screen==cast.screen?read<void*>(screen,0x10):nullptr;',
             'void* cdx=nullptr;(void)screen;', 'final screen shake absent or wrong buffer'),
            ('preview-crop', 'y0=0;y1=h;',
             'y0=unsigned(std::ceil(100.0*h/768.0));y1=std::min<unsigned>(h,unsigned(std::ceil(760.0*h/768.0)));',
             'full canvas composition mismatch')]
        report['presentation_negative_controls'] = []
        for name, fixed, old, expected_error in controls:
            if renderer.count(fixed) != 1:
                raise RuntimeError('Missing regression mutation: ' + name)
            (mutated / 'bull_effect.cpp').write_text(renderer.replace(fixed, old), encoding='utf-8')
            subprocess.run([compiler, '/nologo', '/std:c++20', '/EHsc', '/O2', '/W4', '/WX',
                '/DWIN32_LEAN_AND_MEAN', '/DNOMINMAX', '/I' + str(ROOT),
                str(mutated / 'negative.cpp'), '/Fe:negative.exe', 'winmm.lib'],
                cwd=temporary, env=env, check=True)
            result = subprocess.run([str(mutated / 'negative.exe'),
                str(PROJECT / 'artifacts/custom-skills/thousand-bulls/visualpack')],
                cwd=temporary, capture_output=True, text=True, timeout=90)
            if result.returncode != 1 or result.stderr.strip() != expected_error:
                raise RuntimeError('Missed negative control ' + name + ': ' + result.stderr)
            report['presentation_negative_controls'].append({'name': name, 'rejected': True, 'failure': expected_error})
    if report != {**report, 'status': 'PASS', 'cases': 18, 'casts': 36, 'player_cases': 9, 'enemy_cases': 9}:
        raise RuntimeError('Incomplete pipeline report')
    report['sources'] = {name: sha(ROOT / name) for name in ('bull_native_tick.cpp', 'bull_effect.cpp',
        'bull_frames.h', 'bull_native_pipeline_test.cpp')}
    report['scope'] = 'Actual C++ tick and renderer, actual player/enemy packs, deterministic clock, mocked native APIs and DirectDraw memory surface'
    report['checks'] = ['Both sides: 1/2/14 targets; repeated same caster and shared targets in both orders',
        'Four HP phases, one pending decrement per cast, final lethal state, 8-second owner release',
        'Correct player/enemy ground pack, both layers render, full-screen shift/restoration',
        'Waiting owner cannot change active clock; focus rebind cannot rewind it',
        'Battle+20 -> UI+CFF5C resolves audio owner; 36 non-silent buffers submitted and released; mute and zero volume honored',
        'Final screen+10 backbuffer shakes before presentation and restores afterward; composition surface remains unchanged',
        'Every canvas pixel matches independent composition at all four damage phases for both sides, including restored upper edge']
    report['limitations'] = ['No real client window, audible playback or native GPU driver acceptance']
    output = PROJECT / 'artifacts/custom-skills/thousand-bulls/native-pipeline-20261001.json'
    output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report))

if __name__ == '__main__':
    main()
