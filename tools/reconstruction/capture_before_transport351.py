"""Readonly custody for the two authorized Session source files only."""
from pathlib import Path
import hashlib,json,subprocess
O=Path(__file__).resolve().parent
R=Path('C:/Users/risei/Desktop/God2/God2-Server')
def main():
    rows=[]
    for name in ['Session.h','Session.cpp']:
        p=R/'src/net'/name;b=p.read_bytes()
        with (O/('before-'+name)).open('xb') as f:f.write(b)
        rows.append(dict(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest(),crlf=b.count(b'\r\n'),lf=b.count(b'\n')))
    v=dict(head=subprocess.run(['git','rev-parse','HEAD'],cwd=R,capture_output=True,check=True).stdout.decode().strip(),files=rows,scope='Only baseline custody; no target/SQL/compiler/runtime/tests or report invocation')
    with (O/'before-manifest.json').open('xb') as f:f.write((json.dumps(v,indent=2)+'\n').encode())
    print(json.dumps(v))
if __name__=='__main__':main()
