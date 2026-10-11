# 第219輪：台服角色清單實際issuer與共用寫入接線

新增2個、修改6個C++檔，來源串接段208→209，新增完整雙向玩法路徑0。上一輪有實際2新增/4修改，屬progress；本輪持續台服優先至真正完整來源串接100%才停止。台服與全遊戲完整分母、百分比仍未知。只做靜態恢復、來源實作及檔案雜湊盤點，沒有build/test/native/codec/runtime/DB/SQL/deployment執行。

## 實際呼叫鏈

新增SharedTaiwanNativeCharacterOfferSource，讓真正TW完整75-byte logical07、實際visible ordinal對應的common64ID、revision/source origin與mandatory issuer，經既有SqliteNativeCharacterSummarySnapshotRepository::replace_from_issuer落入共用原始交付儲存，再由既有TW native List讀取及傳送。Offer不是實驗candidate，也不從create/profile40推測raw36、補零或把common slot當選角token。

SharedWorldHostPlan::Context新增typed writer能力。Application在已有requires_native_character_summaries明確選用時從同一SqliteDatabase取現有lazy writer，確認它與reader確實同一物件。accessor本身不做SQL/DDL；沒有新資料庫、schema install或migration。HostOwner保持exact writer identity，StoredSources::ListSources可明確提供實際Offer supplier，create_from_stored_entry直接組成OfferSource→List Prepare，並非無caller的孤立wrapper。Main仍未選用未完成plan。

List只在list呼叫的read(...,true)執行Prepare：先保存完整common roots、取得並核對真正Target，再調actual issuer，成功後讀fresh committed tuple。Select、Current、write-completion都不呼叫Prepare，不會暗中寫入。prepare false/throw/來源變動時直接停止這次列表，不退回舊snapshot發包。舊明確read-only供應路徑在未選Offer supplier時保留。

Offer先按原始75/07/count/ordered bindings及common ownership檢查，TW只接受CommonIdentity、不採CN role22/NativePromptMarker。名字只從實際root.name_codepage原名嚴格轉至CP950，再比對原生前NUL字串；不做繁簡顯示轉換、不變更名字、不推論page0是950（page0只允許ASCII無歧義）。所有postNUL、header flags、unused/inactive rows、route、token高位、appearance及resource bytes原樣保存。可見順序由issuer提供，不照common ORDER BY slot重排。row count<=2與token<=3仍是現有transport有界子集，不是原生全容量證明。

Prepare強持實際來源與owned Scope/Target/complete roots/expected/next/issuer。writer使用原有expected-fulltuple CAS、complete roots以及Prepared/BeforeWrite/BeforeCommit observer。每個observer前後檢查parent的Session/Scope/Target/roots與reentry poison，防止供應者捕獲重入例外後仍commit。這個guard不比較old stored snapshot：BeforeCommit處於staged-next，實際writer自行核對該完整next，避免錯拿old Current讓合法staging必敗。

writer commit返回後不再呼叫provider、reload或自動重試；後續List Current仍可能拒絕發布，但不能假稱已回滾durable commit。此接線也不是客戶端收到/處理ACK、選角一次性admission、wire瞬間原子或正式啟用。

## 原生欄位與缺口

原生子代理保留21份完整實際來源及211..215的既有有界證據，4段298 bytes/106 instruction sites；新全域coverage/opcode0。per-row-field-qualification逐欄說明：只對common ownership/實際64ID及原名可做強資格化；W17↔C29等appearance既有關係仍是matching-consumer inference，沒有官方serializer或copy來源證明。W19 token不等於common slot，W32要真實廣告route/resource Current，inactive row及opaque flags不能自動清零。不能把RecoveredCharacterListCandidate升格為原生issuer。

第二子代理保留initial37加later-read unchanged7完整依賴、實體candidate8與真正final8；核對Application→Context→Host→OfferSource→List的實際可達來源。原生peer封存較早的ListSource原件在root修改後成為歷史epoch，保留原seal與全份原件，另以root/account的fresh current來源及epoch-reconciliation明確對照，不偷偷刷新peer或歷史基準。

實際issuer/visibility/ordered metadata/resource/revision policy實例仍待供應；native_select現在回commonID，至world_entry還沒有typed admission ticket。SharedWorldAdmission的32-bit Key/永不重用模型不能把TW低3bit token、常數0或推測TTL塞入冒充原生授權。one-time CAS/replay/parallel-G、postcreate/localbacking/clamp/fallback、完整2A/scene/5D/Main與其餘玩法仍OPEN。此輪不改凍結Session選角/聊天/認證結果，未執行任何來源。

TW C2S盤點156；world S2C252（fixed230/variable22）；battle S2C110，83 actions23/86 selectors7。CN C2S156；S2C phase rows280（account6/world206/battle68）。這是方向/階段opcode盤點；來源段209、parser branch64.6%都不能當全遊戲完成度。保留CN/web、共用資料表、存檔、聊天、IME、認證、原生字體與文字轉換；完整TW方向/狀態/變體/deferred分母、剩餘13組玩法、numeric64/stack99仍待接通。全部來源串接後再全面測試和修復。
