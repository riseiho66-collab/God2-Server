# 第216輪：台服角色清單交接 owner 與獨立世界認證來源

新增2個、修改5個C++來源檔。來源串接段205→206；新增完整雙向玩法路徑0。依使用者最新指示持續台服優先，完整來源串接100%才停止。完整方向／階段／狀態／變體／延後分派分母仍未知，百分比null。未建置、測試、執行原生／codec／runtime、存取DB／SQL或部署。

## 實際接線

Session僅在明確選用native_select的連線，於真正帳號認證完成且account非0、無error、未closing時，一次發布private不可變認證輸入觀察：實際session、account、ProtocolMode與完整raw176／logical173。沒有public setter，不記錄憑證值；不更改既有認證成功／失敗判定、password worker、回覆或legacy模式。觀察配置失敗不改寫登入結果，後續原生交接因缺來源明確拒絕。

SharedTaiwanCharacterListHandoff實作真正game owner bounded map，使用實際host session capacity與獨立單調不重用epoch。紀錄只保存不可變Issued及原L認證輸入，沒有Session／DB／Target.current強引用。Issued新增source_alive弱來源生命觀察；實際源失效、來源快照／roots／帳號／Live失效、失敗未啟用票證會在後續操作清理，亦提供exact ticket retire。正常L連線關閉本身不被當作G交接失效，沒有自創TTL或account-latest替換。

Publish只接受dormant、同一Session真正async_write成功的exact delivery pointer、原L04成功認證觀察、原A6及未選角Authenticated生命週期。重新讀取同一借用reader的完整snapshot tuple／完整共同roots／帳號，並由必需的Live資格化實際issuer epoch、catalog、visibility及生命週期，才登錄票證。Source仍於Publish返回後完成自身Current，最後啟用；Owner不能把dormant提前當權限。

Link必須來自獨立G00成功認證和真正Session private選角輸入。核對session／account／mode／opcode／raw重新解析結果、created完整ID、未選角Authenticated及closing，再比對原生憑證投影。逐一檢查同帳號、符合投影、仍active且來源完整的已發票證，由必需Authority資格化實際目的地、原生variant及選角權限。候選超過一筆明確拒絕，沒有第一筆／最新一筆fallback。

返回Link.current保留exact owner epoch／ticket、G認證及選角private pointer；每次重查所有候選與Authority，涵蓋Link之後票證啟用或新增造成歧義。所有repository／provider呼叫前先複製紀錄，不持map iterator或reference跨回呼；巢狀owner操作會使當次工作失效，即使外部供應者捕捉例外。公開binding在每次呼叫保留本地strong owner，避免供應者釋放facade導致執行中生命消失。Current只弱引用owner，外部不能靠Current延長DB借用來源生命。

StoredSources::ListSources::with_handoff將此實作交給真正create_from_stored_entry，同時要求exact accounts／characters／summary readers、client SHA及host capacity一致。與直接Publish／Link供應者互斥；未選用原生方案的legacy呼叫不變。新CPP由既有CMake src/*.cpp遞迴來源集合收錄。

## 原生依據與未完成界限

子代理保留13段code、1022 bytes／344 instruction sites，新增全域覆蓋與opcode0。547B80完整254 bytes為此子代理首次本地保留，不冒稱全域新覆蓋。實際bounded stringcopy在firstNUL後補零；14C50各複製16並強制末byte NUL。因此從auth logical[1:25]與[25:157]各取最多15個firstNUL前bytes、補零、末byte NUL，才對應1A兩段16 bytes。不能直接memcpy auth前16，不能把角色名字、文字轉換、casefold或opaque tail當憑證權限。

L04／G00原生來源共有saved credential部分，但1D可能改寫172-byte tail；不要求兩者full172相等，也不把parse成功當真實認證。投影只是必要predicate，真正獨立帳號認證、同源epoch與Authority仍不可省略。

實際Live／Authority政策供應者、raw07權威issuer、創角後列表來源與全部token／localbacking變體、full2A／initial scene／5D／Main正式選用仍開放。本輪有界owner實作不等於完整跨連線admission；沒有一次性admission CAS、防重播或parallel-G消耗租約。前後Current不能使wire emission與來源原子，也不能撤回已發bytes。借用reader及real callback仍必須由既有game owner／Application vault drain保證生命。

TW盤點C2S156；world S2C252（fixed230／variable22）；battle S2C110，83 actions23／86 selectors7。CN C2S156；S2C phase rows280（account6／world206／battle68）。這些不是全遊戲完成分母。台服其他13組玩法、全方向／狀態／變體／deferred、numeric64與stack99仍須接通，保留共用資料表、CN／web、存檔、認證、聊天、IME、原生字體與文字轉換。全部來源串接後再全面測試、驗證與修復。
