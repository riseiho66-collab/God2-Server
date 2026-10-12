from pathlib import Path
import hashlib,json,subprocess
S=Path('C:/Users/risei/Desktop/God2/God2-Server');O=Path('C:/Users/risei/.codex/artifact-archives/god2-server/20261013/round352-blacklist-submitted-chain-source-order-review');head='31d79bad16484d0a2021a938cb1a99b58231ba14'
h=lambda b:hashlib.sha256(b).hexdigest();refs=[];files={}
for rel in ['src/core/Application.cpp','src/net/Session.cpp','src/net/Session.h','src/db/SqliteOwnedBlacklistRepository.h','src/db/SqliteOwnedBlacklistRepository.cpp','cmake/Dependencies.cmake']:
 b=subprocess.run(['git','show',head+':'+rel],cwd=S,stdout=subprocess.PIPE,check=True).stdout;files[rel]=b;dest=O/'baseline'/rel;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(b)
 refs.append({'actual_path':str(S/rel),'retained':'baseline/'+rel,'bytes':len(b),'sha256':h(b),'scope':'HISTORICAL_EXACT_GIT_HEAD_SOURCE_ORDER_BASELINE','head':head,'current_byte_equal_at_capture':(S/rel).read_bytes()==b})
for rel in ['asio/version.hpp','asio/post.hpp','asio/strand.hpp','asio/detail/initiate_post.hpp','asio/detail/strand_executor_service.hpp','asio/detail/impl/strand_executor_service.hpp','asio/detail/impl/strand_executor_service.ipp','asio/detail/op_queue.hpp']:
 actual=S/'build/_deps/asio_src-src/asio/include'/rel;b=actual.read_bytes();dest=O/'local-asio-source'/rel;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(b)
 refs.append({'actual_path':str(actual),'retained':'local-asio-source/'+rel,'bytes':len(b),'sha256':h(b),'scope':'LOCAL_DEPENDENCY_SOURCE_ONLY_NOT_RUNTIME_OR_ARCHIVE_ATTESTATION'})
assert b'ASIO_VERSION 103002' in (O/'local-asio-source/asio/version.hpp').read_bytes()
assert b'asio-1-30-2.tar.gz' in files['cmake/Dependencies.cmake']
cuts=[]
for label,rel,first,last in [
 ('single-game-thread-construction','src/core/Application.cpp',628,642),
 ('single-game-run-abort-and-join','src/core/Application.cpp',7713,7730),
 ('outer-directory-original-run','src/core/Application.cpp',7048,7056),
 ('outer-options-original-run','src/core/Application.cpp',7404,7412),
 ('outer-whole-normal-delegate','src/core/Application.cpp',7555,7569),
 ('game-batch-original-callback-and-response-post','src/net/Session.cpp',2044,2168),
 ('private-normal-peer-post-final-enqueue','src/net/Session.cpp',2555,2599),
 ('peer-budget-constants','src/net/Session.cpp',51,53),
 ('record-staging-bound','src/net/Session.cpp',1968,1975),
 ('exact-session-strand-declaration','src/net/Session.cpp',408,413),
 ('exact-session-strand-construction','src/net/Session.cpp',522,527)]:
 b=b''.join(files[rel].splitlines(keepends=True)[first-1:last]);dest=O/'cuts'/f'{label}.source';dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(b)
 cuts.append({'label':label,'source':rel,'first_line':first,'last_line':last,'retained':str(dest.relative_to(O)),'bytes':len(b),'sha256':h(b),'scope':'SELECTED_NONWHOLE_SOURCE_LINES'})
(O/'baseline-source-references.json').write_text(json.dumps(refs,indent=2)+'\n',encoding='utf-8',newline='\n')
(O/'selected-source-cuts.json').write_text(json.dumps(cuts,indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps({'baseline_head':head,'source_references':len(refs),'reference_bytes':sum(r['bytes'] for r in refs),'cuts':len(cuts),'current_tracked_equal':all(r.get('current_byte_equal_at_capture',True) for r in refs),'status':'PRELIMINARY_UNSEALED_SOURCE_ORDER_ONLY'}))
