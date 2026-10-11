"""Validate original GOD2 SystemMessage data without modifying the client."""
import argparse
import json
from pathlib import Path
from omega_assets import decode_csvz,validate_table

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('source',type=Path)
args=parser.parse_args()
try:
    data=args.source.read_bytes()
    result=validate_table(decode_csvz(data) if data.startswith(b'\x05\x16') else data)
except (ValueError,OSError) as error:
    result={'valid':False,'errors':[str(error)]}
print(json.dumps(result,indent=2))
raise SystemExit(0 if result['valid'] else 1)
