"""Strict HMD v1.6 navigation inputs; no rendering or gameplay claims."""
import argparse
import json
from pathlib import Path
import subprocess

from .omega_assets import decode_csvz
from .world_scenes import build_scenes
from .world_atlas import digest
from .world_atlas import relative_asset


def parse_hmd(decoded):
    if len(decoded) > 16*1024*1024 or b'\0' in decoded:
        raise ValueError('Invalid HMD text size or embedded NUL')
    lines = [line.strip() for line in decoded.splitlines() if line.strip()]
    at = 0

    def line():
        nonlocal at
        if at >= len(lines):
            raise ValueError('Truncated HMD')
        value = lines[at]
        at += 1
        return value

    def numbers(raw, count=None):
        fields = raw.split()
        if count is not None and len(fields) != count:
            raise ValueError('Invalid HMD numeric record width')
        if any(not field.lstrip(b'+-').isdigit() or field[:2] in (b'++',b'--',b'+-',b'-+') for field in fields):
            raise ValueError('HMD integer must use decimal ASCII digits')
        try:
            result = [int(field) for field in fields]
        except ValueError as error:
            raise ValueError('Invalid HMD integer') from error
        if any(not -32768 <= value <= 32767 for value in result):
            raise ValueError('HMD integer outside supported bounds')
        return result

    def section(name, maximum):
        fields = line().split()
        if len(fields) != 2 or fields[0] != name:
            raise ValueError('Expected HMD section '+name.decode())
        count = numbers(fields[1],1)[0]
        if not 1 <= count <= maximum:
            raise ValueError('HMD section count outside supported bounds')
        return count

    if line() != b'HMD v1.6':
        raise ValueError('Only current HMD v1.6 is qualified')
    roms = [relative_asset(line()) for _ in range(section(b'ROMFILE',512))]
    tiles = []
    for _ in range(section(b'TileModel',512)):
        fields = line().split()
        if len(fields) != 6:
            raise ValueError('Unsupported HMD tile model record')
        tiles.append({'name_bytes':fields[0].hex(),'fields':numbers(b' '.join(fields[1:]),5)})
    models = []
    for _ in range(section(b'ModelDat',512)):
        layers = [numbers(line(),3) for _ in range(3)]
        if any(layer[0] < -1 or layer[0] >= len(tiles) for layer in layers):
            raise ValueError('HMD tile model reference out of bounds')
        navigation_start = at
        frames = numbers(line())
        if not frames or not 1 <= frames[0] <= 10 or len(frames) != 1+2*frames[0]:
            raise ValueError('Unsupported HMD animation frame offsets')
        portals = numbers(line(),8)
        if line() != b'Pass':
            raise ValueError('Expected HMD Pass section')
        grids = []
        for _ in range(frames[0]):
            width,height = numbers(line(),2)
            if not 1 <= width <= 512 or not 1 <= height <= 512:
                raise ValueError('HMD pass grid dimensions out of bounds')
            cells = [value for _ in range(height) for value in numbers(line(),width)]
            if any(not 0 <= value <= 255 for value in cells):
                raise ValueError('HMD pass cell outside byte bounds')
            grids.append({'width':width,'height':height,'cells':cells})
        models.append({'layers':layers,'frame_offsets':frames[1:],
                       'portal_fields':portals,'grids':grids,
                       'navigation_tokens':[t.decode('ascii') for t in b'\n'.join(lines[navigation_start:at]).split()]})
    placements = []
    model_line_start = at
    for index in range(section(b'Model',1024)):
        fields = numbers(line(),6 if index == 0 else 10)
        model,px,py,x,y,frame = fields[:6]
        if not 0 <= model < len(models) or not 0 <= frame < len(models[model]['grids']):
            raise ValueError('HMD placement model/frame out of bounds')
        if index == 0 and frame != 0:
            raise ValueError('Nonzero base frame needs separate qualification')
        placements.append({'model':model,'frame':frame,'pixel_x':px,'pixel_y':py,
                           'x':x,'y':y,'extra_fields':fields[6:]})
    if at != len(lines):
        raise ValueError('Unsupported trailing HMD section')
    # Preserve the exact token stream for the original 37250 placement parser.
    model_tokens = b'\n'.join(lines[model_line_start:]).split()[1:]
    return {'format':'HMD v1.6','roms':roms,'tiles':tiles,'models':models,
            'placements':placements,'model_tokens':[token.decode('ascii') for token in model_tokens]}


def navigation_inputs(asset):
    def grid(placement):
        return asset['models'][placement['model']]['grids'][placement['frame']]
    return grid(asset['placements'][0]), [
        {'x':p['x'],'y':p['y'],'grid':grid(p)} for p in asset['placements'][1:]]


def dump_input(base, overlays):
    values = [base['width'],base['height'],*base['cells'],len(overlays)]
    for overlay in overlays:
        grid = overlay['grid']
        values += [overlay['x'],overlay['y'],grid['width'],grid['height'],*grid['cells']]
    return ' '.join(map(str,values))+'\n'


def compile_navigation(client, area, scene, executable):
    root = Path(client).resolve()
    rows = [s for s in build_scenes(root)['scenes'] if (s['area'],s['scene']) == (area,scene)]
    if len(rows) != 1 or not rows[0]['asset_relative'].lower().endswith('.hmd'):
        raise ValueError('Expected one current indoor CAN scene')
    row = rows[0]
    variants = row['asset_variants']
    if not variants or len({v['decoded_sha256'] for v in variants}) != 1:
        raise ValueError('Missing or divergent indoor asset variants')
    source = root/variants[0]['path']
    raw = source.read_bytes()
    decoded = decode_csvz(raw) if source.suffix.lower().endswith('z') else raw
    if digest(raw) != variants[0]['sha256'] or digest(decoded) != variants[0]['decoded_sha256']:
        raise ValueError('Indoor asset changed during import')
    asset = parse_hmd(decoded)
    base,overlays = navigation_inputs(asset)
    result = subprocess.run([str(Path(executable).resolve()),'--dump'],
        input=dump_input(base,overlays),text=True,capture_output=True,timeout=10,check=True)
    fields = result.stdout.split()
    if len(fields) != 2:
        raise ValueError('Invalid C++ grid compiler output')
    side,cells = int(fields[0]),bytes.fromhex(fields[1])
    if not 1 <= side <= 1025 or len(cells) != side*side:
        raise ValueError('Invalid compiled grid dimensions')
    return {'schema':'god2-recovered-indoor-navigation-v1','area':area,'scene':scene,
            'source':{'can':row['source_file'],'can_sha256':row['source_sha256'],
                      'asset':variants[0]['path'],'asset_sha256':digest(raw),
                      'decoded_sha256':digest(decoded)},
            'base':base,'overlays':overlays,'grid':{'side':side,'cells_hex':cells.hex(),
                      'sha256':digest(cells),'nonzero_cells':sum(c!=0 for c in cells)},
            'qualification':'CPP_GENERATED; per-asset original-code comparison is separate',
            'server_loaded':False,'runtime_validated':False}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--client',type=Path,required=True)
    parser.add_argument('--area',type=int,required=True)
    parser.add_argument('--scene',type=int,required=True)
    parser.add_argument('--grid-executable',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args = parser.parse_args(argv)
    output = args.output.resolve()
    if output.is_relative_to(args.client.resolve()):
        parser.error('Navigation output must not modify the original client directory')
    data = compile_navigation(args.client,args.area,args.scene,args.grid_executable)
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(data,indent=2,sort_keys=True)+'\n',encoding='ascii')
    print(json.dumps({'area':args.area,'scene':args.scene,'side':data['grid']['side'],
                      'nonzero_cells':data['grid']['nonzero_cells'],'runtime_validated':False}))


if __name__ == '__main__':
    main()
