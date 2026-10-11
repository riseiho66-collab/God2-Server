"""Read-only SystemMessage search and minimal recovered CSVZ validation."""
import argparse
import hashlib
import json
from pathlib import Path
import struct

TAG=b'SystemMessage'


def decode_csvz(data, limit=64*1024*1024):
    if len(data)<7 or data[:2]!=b'\x05\x16':
        raise ValueError('Missing 05 16 header')
    size=struct.unpack_from('<I',data,2)[0]
    if size>limit:
        raise ValueError('Declared expansion exceeds analysis bound')
    # Recovered from 0x401D20: space-filled 4096-byte ring, start 0xFEE.
    ring=bytearray(b' '*4096); valid=bytearray([1]*0xfee+[0]*18)
    cursor=0xfee; pos=7; flags=0; out=bytearray()
    while pos<len(data):
        flags >>= 1
        if not flags&0x100:
            flags=data[pos]|0xff00; pos+=1
        if flags&1:
            if pos==len(data): break
            values=[data[pos]]; pos+=1
            for value in values:
                out.append(value); ring[cursor]=value; valid[cursor]=1; cursor=(cursor+1)&4095
        else:
            if pos+2>len(data):
                raise ValueError('Truncated back-reference')
            low,high=data[pos:pos+2]; pos+=2
            offset=low|((high&0xf0)<<4)
            for index in range((high&15)+3):
                address=(offset+index)&4095
                if not valid[address]: raise ValueError('Read from initially unspecified ring tail')
                value=ring[address]; out.append(value)
                ring[cursor]=value; valid[cursor]=1; cursor=(cursor+1)&4095
        if len(out)>size or len(out)>limit: raise ValueError('Expansion exceeds declared length')
    if len(out)!=size: raise ValueError(f'Length mismatch: declared {size}, decoded {len(out)}')
    return bytes(out)


def validate_table(data):
    # The client uses rt/fgets and comma splitting, not quoted CSV semantics.
    text=data.replace(b'\r\n',b'\n')
    lines=text.splitlines(keepends=True)
    original_offsets=[]
    raw_offset=0
    for line in data.splitlines(keepends=True):
        original_offsets.append(raw_offset)
        raw_offset+=len(line)
    sections=[]
    errors=[]
    if not lines: return {'valid':False,'errors':['Empty decoded input'],'sections':[]}
    first=lines[0].rstrip(b'\n').split(b',')
    try:
        header_lines=int(first[2])
        if header_lines<2: errors.append('Header line count below expected two-line minimum')
    except (ValueError,IndexError):
        header_lines=0; errors.append('Missing numeric header field 2')
    offset=0
    for index,line in enumerate(lines):
        fields=line.rstrip(b'\n').split(b',')
        if fields[0]==TAG:
            section={'line':index+1,'text_mode_offset':offset,'raw_decoded_offset':original_offsets[index],
                     'entry_tag':'SystemMessage','errors':[]}
            try:
                count=int(fields[1]); section['declared_records']=count
                if not 1<=count<=32767: raise ValueError('Signed 16-bit count outside positive range')
                rows=lines[index+1:index+1+count]
                if len(rows)!=count: section['errors'].append('Insufficient record lines')
                ids=[]
                for row in rows:
                    columns=row.rstrip(b'\n').split(b',')
                    if len(row)>4095 or any(len(c)>379 for c in columns):
                        section['errors'].append('Line/field exceeds recovered parser buffer bound'); break
                    if len(columns)<2:
                        section['errors'].append('Record lacks id/type'); break
                    row_id=int(columns[0]); int(columns[1]); ids.append(row_id)
                    if not 1<=row_id<=count:
                        section['errors'].append('Record ID outside loader range'); break
                section['record_ids']=ids
                section['max_observed_id']=max(ids,default=0)
                section['unique_ids']=len(set(ids))
            except (ValueError,IndexError) as error:
                section['errors'].append(str(error))
            section['valid']=not section['errors']
            sections.append(section)
        offset+=len(line)
    if not sections: errors.append('No exact SystemMessage section tag')
    encodings={}
    for name in ('cp950','cp936','utf-8'):
        try: text.decode(name); encodings[name]=True
        except UnicodeDecodeError: encodings[name]=False
    return {'valid':not errors and all(s['valid'] for s in sections),'errors':errors,'sections':sections,
        'header_fields_hex':[x.hex() for x in first],'header_line_count':header_lines,
        'encoding_decodable':encodings,'encoding_claim':'Client parser uses byte strings; encoding semantics not proved by decodability',
        'record_layout':'In-memory 16-byte entries: type byte at +0 and string pointers at +4/+8/+12; wire rows are variable length',
        'optional_strings':'Missing columns return empty through 0x451AE0/0x451B60; three string columns need not all be present',
        'scope':'Conservative recovered-contract validation, not execution of the original loader'}


def scan(root, output):
    output.mkdir(parents=True,exist_ok=False)
    patterns={'ascii':TAG,'utf16le':TAG.decode().encode('utf-16le'),'utf16be':TAG.decode().encode('utf-16be')}
    files=[]; matches=[]; candidates=[]; errors=[]; total=0; decoded_count=0; skipped_wrappers=[]
    for path in sorted(root.rglob('*')):
        if not path.is_file() or path.is_symlink(): continue
        if not path.resolve().is_relative_to(root.resolve()): continue
        try:
            digest=hashlib.sha256(); hits=[]; offset=0; carry=b''
            with path.open('rb') as stream:
                head=stream.read(7); stream.seek(0)
                while chunk:=stream.read(1024*1024):
                    digest.update(chunk); combined=carry+chunk
                    for kind,pattern in patterns.items():
                        start=0
                        while (start:=combined.find(pattern,start))>=0:
                            position=offset-len(carry)+start
                            if position+len(pattern)>offset:
                                hits.append({'encoding':kind,'offset':position,
                                    'preceding_hex':combined[max(0,start-4):start].hex()})
                            start+=len(pattern)
                    carry=combined[-32:]; offset+=len(chunk)
            record={'path':str(path.relative_to(root)),'size':offset,'sha256':digest.hexdigest()}
            files.append(record); total+=offset
            if hits: matches.append({**record,'hits':hits})
            if head[:2]==b'\x05\x16':
                if path.suffix.lower() not in ('.csvz','.csv'):
                    skipped_wrappers.append(record['path'])
                    continue
                try:
                    decoded=decode_csvz(path.read_bytes()); decoded_count+=1
                    if TAG in decoded:
                        validation=validate_table(decoded)
                        candidates.append({**record,'decoded_size':len(decoded),'decoded_sha256':hashlib.sha256(decoded).hexdigest(),
                                           'wrapper_byte_6':head[6],'validation':validation})
                except ValueError as error:
                    errors.append({'path':record['path'],'decode_error':str(error)})
        except OSError as error: errors.append({'path':str(path),'read_error':str(error)})
    result={'root':str(root.resolve()),'files_scanned':len(files),'bytes_scanned':total,'raw_matches':matches,
        'decoded_0516_files':decoded_count,'decoded_candidates':candidates,'errors':errors,
        'undecoded_non_csv_wrappers':skipped_wrappers,
        'scope':'All readable regular files searched raw, including embedded blobs; recovered 05 16 top-level CSV/CSVZ wrappers decoded. Non-table wrappers and other archive encodings UNKNOWN.',
        'case_policy':'Exact case; client dispatch compares bytes case-sensitively; prefixes retained in raw-match context'}
    for name,value in (('asset-scan-systemmessage.json',result),('asset-scan-manifest.json',files)):
        with (output/name).open('x',encoding='utf-8') as stream: json.dump(value,stream,indent=2)
    print(json.dumps({k:v for k,v in result.items() if k not in ('raw_matches','decoded_candidates','errors','undecoded_non_csv_wrappers')}))
    print(json.dumps({'candidate_paths':[v['path'] for v in candidates],'errors':len(errors)}))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    sub=parser.add_subparsers(dest='command',required=True)
    scan_p=sub.add_parser('scan'); scan_p.add_argument('root',type=Path); scan_p.add_argument('--output',type=Path,required=True)
    valid=sub.add_parser('validate'); valid.add_argument('file',type=Path)
    args=parser.parse_args()
    if args.command=='scan': scan(args.root,args.output)
    else:
        data=args.file.read_bytes(); result=validate_table(decode_csvz(data) if data.startswith(b'\x05\x16') else data)
        print(json.dumps(result,indent=2)); raise SystemExit(0 if result['valid'] else 1)


if __name__=='__main__': main()
