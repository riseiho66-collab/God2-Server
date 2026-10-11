# 第188輪：共用觀戰目標身分與陸服 typed6E 入口

本輪新增5個、修改8個 C++來源檔，共13檔。共用 SharedNativeSpectatorTargets 將真正已釋放的 D0 操作數連到明確供應的核心 Target 物件；台服既有 typed6E Scope 與陸服既有 SharedWorldGameplay 輸入流程使用這些觀察。這是具體來源串接，尚未完成正式原生視窗發行者、戰鬥操作與回覆供應者，不代表 Main 已選用或客戶端已驗收。完成静態記帳後，來源段數179→180；新增 opcode、phase binding、完整雙向玩法路徑均為0。全遊戲分母與百分比保持未知。

## 共用目標來源

來源要求同一 presence、transports 與 publication 的實際物件。SharedWorldHost 提供一次性的目標來源安裝與取回入口；with_native_chat_spectator_and_publication 的末尾可選參數將 exact supplied source 交给既有台服來源。沒有建立預設 issuer、核心目標、權限、視窗世代或成功回覆，未選用的新參數不改原本呼叫方式。

issue 接收實際已 Published 的 UI 觀察、完整 binding batch、真正 Issuer 與其明確世代。每個 binding 指向事件 revision、完整紀錄零起始 ordinal、D0 第一或第二個 WORD 操作數、真正 Target 與其世代。依完整 CD65／D07 歷史保留每個 slot 最後一筆 D0，再核對供應的定位。FFFF 保留0000FFFF；0和FFFF沒有預設映射。此表是本服務明確發行的 D0 範圍，沒有宣稱已恢復官方全部目標命名空間，也不把 wire WORD 強轉為共用64位角色ID。

全部 binding 的拷貝、配置及資格觀察先完成，再替換私有登記。永久 issuer／Target 是弱引用，每次實際觀察先持有強引用；完整 root、位置、原連線私有 Token、UI 與 endpoint 在每個真正 issuer／Target observer 前後核對。同 context 若指向不同物件、不同弱引用 ownership 或不同 Target 世代，返回 Ambiguous，不任選第一項。原 slot 已被較新 D0 替換、目標消失或世代失效返回 Expired，不悄悄濾掉失效 binding。

Missing／Matched／Ambiguous／Expired／ForeignContext／Unavailable／Retired 都是可觀察的狀態事實。current 表示觀察仍準確，不代表遊戲權限。超過WORD的 context 可以是此 D0 範圍的 ForeignContext，不能據此全域拒絕其他模式1的原生 DWORD 範圍。retire／remove 只處理相同私有 entry，不能刪除後繼連線、共用 presence、原生 transport 或戰鬥狀態。私有 absence fence 耗盡不 wrap。

台服 Scope 使用原保存 Token 與完整 request.context()，不 mask、不窄化；target 的 UI 必須與同次 Scope 的 publication.same 成立。必要實際 WorldOwner 仍獨立決定 native namespace、目前 phase、battle generation、目標與操作權限。真正 execute 維持單次呼叫，合法操作後重新取得实际 Scope。

## 陸服實際輸入與回覆路徑

CnSpectator6E 是獨立陸服證據的只讀 logical9 view：opcode6E，body0 mode，body4..7 完整 DWORD context，body1..3 保留原始未寫入的堆疊位元組。observed_producer_shape 只限定已觀察 caller／producer 形狀：模式1的非負 signed32 context，或模式2的 context0。這個判斷不提供 phase、目標身分或戰鬥資格。S2C6E logical5 是另一方向，沒有據此製造同 opcode ACK。

SharedWorldGameplay::Sources 可明確選入真正 CN WorldOwner、非零 budgets 與同來源 publication／targets。initialize 在原本1C初始化流程建立 child，第一筆真正 ready6E 才取得 actual registry 私有 Token；不在初始 transport 尚未登記時製造 Token。整批輸入先 split 並完整拷貝，新增6E分支按原順序 dispatch 到 SharedNativeSpectatorSource，再由既有 pump 接續原 continuation。

來源保存真正 CN connection／完整 Lease，永久 receiver 為弱引用，操作 Pending 為強引用。BeforeExecute／AfterExecute／BeforeQueue／BeforeRelease／AfterRelease 各取得真實 root、位置與UI／target觀察，要求 target.ui 與同次 publication 同一 lineage。CN沒有可借用的TW battle counter，沒有製造phase或counter。必要真正 WorldOwner 必須提供CN battle membership、incarnation、操作資格、規則、完整回覆及profile；execute只呼叫一次。

明確有序 logical reply records 經真正 connection.send_world_batch_with_publication，沿原CN framing／encryption發送，不傳入預先加密封包。實際 held transport 的 approval posted 到 game executor；wrapper可能 inline false completion，submitting處理此差異。no_reply 必須是實際 handler 的明確決定，沒有預設成功ACK。late true completion 即使發生在取消後，也保留 monotonic locally_released 事實，但不重開來源、不重跑 execute 或 completion。此事實只是本地釋放，不是持久化或客戶端收到。

既有 Gameplay 的重入失敗、failure、terminal03與destructor清理此次 child。child只釋放自己的保存Token／pending bookkeeping；共用清理由原Gameplay／Ready負責，不能用新child刪除其他連線。成功非terminal batch不釋放child，後續合法請求仍走同一來源。

## 陸服原生追查增量

固定雜湊582f的 God2_opt.exe 及選定原始反編譯／metadata輸入保留完整原件，共19份：PE1、metadata1、保留primary C10、新選定primary C7。18個 spans 共801B，其中14個新增限定區547B、4個保留186區254B；新增完整 native 函式數0。205 instruction sites、7 data sites、18 primary source sites 與37 actual C++ source sites不是完整玩法路徑數。

既有004B2010 producer 經00481440送6E＋8B body。五個直接呼叫候選中，只有004A28DC 的 D0 UI選擇已證明來源為WORD；其餘模式1操作數保持DWORD：0048C009的action17以4→8→0→C順序取第一個非FFFFFFFF DWORD；0048C37F的action17使用selector／owner值，部分分支有未指定local；0050D1A8的action4用signed WORD索引取得紀錄DWORD。這些上游 issuer與目標語義仍未知，不能塞到D0表或窄化。

00547223在owner+A97998==1且[owner+4]+12018非零時傳mode2/context0。00435E60輸入分派的event204設12018=1、12024=0；event205清12018／1201C並設12024=1。12018是客戶端局部輸入 latch，不是服務端戰鬥權限。A97998的issuer與當前phase、間接caller及全部正式目標命名空間仍OPEN。

## 盤點、限制與接續

| 盤點 | TW | CN |
|---|---:|---:|
| C2S opcode |156：151 generic＋5 supplemental|156；完整phase待釐清|
| S2C口徑 |252 length支援：230 fixed＋22 variable；world非default206|280 phase/opcode entries：account6＋world206＋battle68|
| 本輪新增opcode／phase |0／0|0／0|
| 本輪新增完整雙向玩法路徑 |0|0|

TW battle83 actions23、battle86 selectors7為30個前沿項；958 endpoint rows／28 source groups不是全遊戲分母。既有台服世界解析範圍42／63的66.7%也不是全遊戲完成度。正式部署與此次原生客戶端驗收均未進行。

剩餘工作包括真正native視窗／事件／目標發行者、目前核心Target與battle membership／rights／execute／回覆、其他mode1 DWORD範圍、完整entry／appearance／audience／header／body／codepage／cipher供應者、Main正式選用、Web C56真正handler與opaque／目標／耗費及其餘全遊戲路徑。TW-CN-web共用64位計算、storage／wire／object／飄字、仙幣上限99999999999、合格stack99、共用表與WSS／TLS／hosting仍保留完整範圍，等級不改。

本輪只有靜態來源讀取／修改與file/hash記帳；沒有建置、測試、native／C++／Lua／API／codec執行、DB／SQL存取、正式遷移、重啟或部署。沒有重試155已停止formatter／capacity／render／glyph鏈路或深入52F330／52F170。帳號、存檔、聊天、IME、認證、頭像、原生字體、繁簡轉換及客戶端／凍結功能保留。fresh before1341、前輪2428封存成員、各代理before／初版／修補前／final原件與原始／最終報告分開保存。整個God2的檔案長度容量盤點另存於本輪policy與continuation，不恢復整個歷史客戶端或建置樹。
