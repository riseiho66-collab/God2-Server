from pathlib import Path
import hashlib,json
D=Path(__file__).resolve().parent
p=D/'qualified/553bc0-full-code.tsv';b=p.read_bytes();old=b'va\thex\\mnemonic\toperands\n';new=b'va\thex\tmnemonic\toperands\n';assert b.startswith(old);corrected=new+b[len(old):];rows=corrected.splitlines();assert len(rows)==191 and all(len(r.split(b'\t'))==4 for r in rows);q=D/'qualified/553bc0-full-code-corrected-header.tsv';assert not q.exists();q.write_bytes(corrected);assert p.read_bytes()==b and q.read_bytes()==corrected
v=dict(original=p.as_posix(),original_bytes=len(b),original_sha256=hashlib.sha256(b).hexdigest(),corrected=q.as_posix(),corrected_bytes=len(corrected),corrected_sha256=hashlib.sha256(corrected).hexdigest(),instruction_rows_unchanged=True,rows=190,original_successful_capture_not_rerun=True,nonfatal_SyntaxWarning_retained=True,old_header_hex=old.hex(),new_header_hex=new.hex())
f=D/'additive-TSV-header-correction.json';assert not f.exists();f.write_bytes((json.dumps(v,indent=2)+'\n').encode());print(json.dumps(v))
