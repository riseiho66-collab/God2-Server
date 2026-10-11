# 第218輪：台服實際配置表來源與世界連線槽位

新增2個、修改4個C++檔；來源串接段207→208，新增完整雙向玩法路徑0。這輪實作配置來源、Handoff消費與實際Context組裝，屬progress；全遊戲與台服完整路線分母、完成百分比仍未知。依使用者最新指示持續台服優先至實際完整來源串接100%，不在輪末暫停；全部串接後才集中測試。本輪沒有build/test/native/codec/runtime/DB/SQL/deployment執行。

## 接入的來源

新增TaiwanNativeClientGroupConfiguration，限定原生149c1b45…固定來源。TW11BB0以initial_host前8 bytes是否192.168.、TW531C10的實際WORD59DFD8==4且WORD59DFDA==2，選config.ini/config_gb.ini/config2.ini/config2_gb.ini。兩個WORD是實際呼叫端輸入，不推論Windows語系，也不採用CN的constant-false helper或config_2命名。明確供應已解析的絕對client root；沒有模擬未知native path formatter或從process cwd猜路徑。

復用既有TW TaiwanNativeResourceSelection，完整保留Request、candidate/original路徑、probe、branch、encoded原件與已打開的candidate原件。只在Candidate0516分支使用本輪由TW00401D20獨立恢復的有界ring解碼來源；OriginalAfterOpenFailed/Non0516按純文字原件處理，即使原檔前兩bytes恰為05/16，也不能重新探測並解碼。firstcandidate原先漏掉這個branch條件，子代理指出後已在真正final補正；兩個實體epoch分開保存，沒有冒稱候選就是final。

新來源保存完整decoded bytes及不可變ordered groups/slots。TW12740每個group配置0x1804 bytes、count在+40、row stride0x260，最多10 slots、64 groups。無等號的非註解內層列仍消耗一格並保存空name/value；duplicate labels各自保留ordinal；空group/count0保留觀察，使用時拒絕無可用槽位。槽位數不取決於位址有效、廣告05筆數、mask或儲存server ID。

原生rt FILE的CRLF翻譯與parser分開；前置只trim TAB/SPACE，內層blank line結束group，註解;/#跳過，下一個[直接轉外層解析，10列後回外層。$只在外層解析；TW failed %d保留network+650舊值，不能照CN歸零。owned subset拒絕failed/partial/overflow整數、NUL、0x1a、lone CR、超127byte line、無終止LF/未閉合label及過長欄位，保留原始bytes。這些是安全實作限制，並非原生已有防護或完整錯誤分支仿真。CRT非ASCII locale whitespace、64組以後尾端、外層@/^/-含義仍未資格化。

Handoff現在強持shared_ptr<const配置>，create必須提供實際配置與相同固定client來源。Authority只供native group/subgroup及Current，不再能任填configured_subgroups；resolve從不可變配置導出count，目的地前後核對也再次比對同一count。既有完整04/05/06實體偏移重播、raw07 primary key、獨立G private accepted-local endpoint、帳號/roots/snapshot、Live、歧義拒絕與全候選Current保持。configuration值只限定查找域，不創造角色、帳號、native UI WORD高位或權限。

新增ListSources::with_configured_handoff，在真正SharedWorldHostPlan::Context工廠內取相同accounts/characters/native_character_summaries建立owner，保留build/capacity/config/Live/Authority/Target/Qualify強依賴。沒有保留借用Context，沒有替Main選用不完整plan，沒有預設成功或臨時造list。

## 證據及未完成部分

原生子代理保留12段有界code、2061 bytes/668 instruction sites，另7段data/162 bytes；封存62 members+seal，獨立TW wrapper/decoder/parser/selector來源，新增全域coverage/opcode0。另一子代理保留initial27完整依賴、firstcandidate6與真正final6進行靜態來源審閱；全部只是原始檔與雜湊盤點，沒有執行解析器、codec或任何測試。

原生2530確實會解碼到真正暫存wb，再reopen rt，忽略decoder bool；reopen失敗可fallback原檔。owned source對選中壓縮檔錯誤直接拒絕，不重現暫存副作用。原生cache在已載入global count>0時不重讀，現有物件是不可變first-load來源模型；真正startup operands/cache epoch與issuer Live/Authority仍須正式供應。空原檔繼承既有ResourceSelection的拒絕限制，不能宣稱完整支援原生empty-file成功。未解碼或啟用現有Data3檔案，未更新歷史原生基準。

完整raw07/創角後issuer、localbacking/clampedtoken4..7/fallback/較大配置變體、one-time admission CAS/replay/parallel-G、完整2A/initial scene/5D/Main正式選用及其餘玩法仍OPEN。前後Current不等於wire寫出瞬間原子，不可因新增配置來源就稱登入/世界路線100%。

TW盤點C2S156；world S2C252（fixed230/variable22）；battle S2C110，83 actions23/86 selectors7。CN C2S156；S2C phase rows280（account6/world206/battle68）。這些是分階段opcode盤點，不能直接相加當玩法分母或拿來源208段換算完成度。其餘台服13組玩法、numeric64、stack99與完整方向/狀態/變體/deferred分母仍待接通。保留CN/web、共用資料表、帳號存檔、聊天、認證、IME、原生字體、文字轉換及既有凍結功能。
