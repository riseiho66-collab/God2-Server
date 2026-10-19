# 台服 2A 入場下游與 Main 缺口（round480）

本輪直接用現有 REA／Ghidra 靜態分析目前台服 EXE 的入場下游，未執行
遊戲、原生函數、codec、SQL、建置或測試。沒有更動 C++／Lua 或啟用 Main。
新增的是可追溯原生契約證據，不是完整玩法或原始服務端公式的恢復宣稱。

## 當前真正缺口

Main 的 src/main.cpp:90 仍呼叫一般 run_server。帶世界 plan 的入口與
Application／Session 組裝已存在，不能把再增加一個 wrapper 算作接通。
完整 2A SceneSupply／stored Qualify、真正初次場景選擇／次序／Install、
movement 資源與姿態生命週期仍缺實際供應者。兩個初始場景 adapter 仍需
genuine supplier。現有 historical_body 是候選，不能冒充已資格化原生產生器。

Application.cpp:842 的限制是有條件的：world_transfers_enabled 與提供
台服 entry／movement factory 的 world plan 不能並存，真正的 transfer
bridge 尚未提供。本輪沒有繞開此檢查，也沒有改動現用傳送功能。

## REA 原始證據與映像

目前 God2.exe SHA256 為 aaf0fae66e89c4547244304ecd8f4c2755746ffa6c9b9dfe68a0ff3fd2b4cd48。
分析映像只增加分析用呼叫種子；13 個原始 PE section 的位址映射及 bytes
均另行核對。合成 caller 不算原生 caller，分析映像從未執行。
第一次在未標記下游函數的映像查不到 procedure，該失敗保留；後續依實際
callee 加種子才取得 11 個函數，不把第一次失敗稱為函數不存在。

REA batch Evidence：
- ev_8d5e5a8c20f6eeb99ee0818389bd4114296a2375341be2567f5e2dc4f9226b1d
- ev_18cd9a24b58109cdb20982265fababfb48244da86edfe9adddb0e7bfd51b7009
- ev_27d516140251f5d982f196d3caed98afa8a54c912345cac1b42a76801666c84e

## 呼叫參數與快取

4682FC..468310 的原始組語依序 PUSH EBX／ECX／EDI／EDX／EAX，
461AD0 的 RET 0x14 相符，實際五參數依序為 area、scene、NPC group、
enemy descriptor、world object。第五個是 initializer 的 world EBX，
不是另一個未知封包欄位。468160 偽碼只列四參數，不可據此實作。
4616A0／460C60 也會把第二參數當 world context；單參數偽碼不完整。

4619D0 以 WORD area／scene 比對兩槽快取，槽距 0xAD610；命中回傳 1，
未命中輪換並回傳 0。461AD0 只在 cache miss 時走資源預載，最後固定
回傳 1。這不代表每次有磁碟讀取，也不是完整載入成功或場景權威的證明。

45AA70 以 area 低 BYTE 與 scene WORD 找第一個 142-byte NPC 資源群；
scene 與群內 BYTE 比較，所以 scene 大於 255 不會因截成 BYTE 而命中。
45A000 以 area 低 BYTE 及 scene 低 WORD 找 12-byte enemy descriptor。
正常 2A 自己的 area 1..16 條件與這些查詢函數的邊界分開記錄。

## 預載流程及計數

4616A0 讀 enemy descriptor +4 的列數、+8 的資料指標，以 26 bytes
跨列，取每列 byte1 減 1 呼叫 45EEC0。
460C60 先預載一組固定 selector，再按 NPC group +1 的數量掃描兩個
BYTE 的 (kind, ordinal)：
- kind 0..4：45F0E0(kind, ordinal-1)。
- kind 6：45EEC0(ordinal-1)。
- kind 7：45EEC0(ordinal+99)。
- kind 5 與其餘值跳過這些預載分支。

這些是素材預載選擇，不能當 NPC 實例、座標、技能、掉落或生怪條件。
現有 TaiwanNativeNpcSceneGroups 保留原碼及縮成 BYTE 的來源欄位；
本輪沒有把資源群改成 NPC 出現表，也未自行修正 native 的負 index 行為。

4607D0 僅讀堆疊 WORD，寫入 world+0xA7F2F64 後 RET 4，不改 EDX。
4682D3..4682E9 由 NPC／enemy 群數量相加後左移 3，再用 signed 除 7
序列計算參數；在非負且左移不溢位的範圍可讀成 floor(8*N/7)，最後只
存低 WORD。這不是 B26..27，也未證明此欄是 NPC 實例容量、遊戲上限、
原服計數或戰鬥公式。任意溢位／負值不套用上述數學簡寫。

上述直接流程不把 B26..27 當 scene 高位；仍不能推論該欄全域無用、
padding 或正式 serializer 可任填。保留完整 2A 與原始未知欄位。

## 下一步與驗證界線

461270 的 ordinary appearance／Drv／DrvDoll 已有匹配字節的先前研究，
沿用 tw-native-appearance-selector-and-profile-resource-20261012.md 及
tw-actor-drv-fifth-source-20261015.md，不能當成完全未分析而重算覆蓋。
同輪續追已補上 4606D0 的直接 world 寫入與 45EEC0／45F0E0 的載入／快取
條件，見下節；實際初始場景／資源 owner 仍需接通。原服 2A producer 仍未知，
經授權的自製替代須明列 CUSTOM，不能把本輪 consumer 提升成原服權威。

全部 REA 輸出、失敗、close、映像來源及 source pins：
C:/Users/risei/.codex/artifact-archives/god2-server/20261019/entry-downstream-round480。
本輪完整玩法增加 0；台服／全遊戲分母與完成率維持 unknown/null。

## 同輪續追：預載判定、時間分支及未知 helper

REA Evidence ev_dae376d6aac9aabfdb8d5adbde147d2878cbe77d756ba78122306a7db576232b
再追 4606D0、45EEC0、45F0E0；本輪共取得 11 個函數，不新增原生
服務端規則或完整玩法。原始結果與組語存於 v5，v1 初稿保留在外部證據庫。

45F0E0 先檢查 kind 非負且小於 group count、ordinal index 非負且小於
該組 signed WORD count，再以該組 signed WORD base 加 index 交給
45EEC0。固定資料 58A58C／58A58D 的目前原始 bytes 是 9／1，
故 460C60 的固定呼叫是 45F0E0(9,0)，不是一個 NPC 出現實例。

45EEC0 的列跨度為 0x4C。其 signed WORD cache marker：
- -1：尚未嘗試，才組合 manager prefix 與該列 filename，呼叫既有 429820。
- -2：記錄失敗，後續回傳 false，不自動重試。
- 其餘值：直接依 cache marker 不是 -2 回傳；不能無條件稱每次都有 IO。

新載入時 filename 非空且 429820 回傳非負，才保存目前 signed WORD
resource slot、遞增 slot 並回傳 true；否則保存 0xFFFE 並回傳 false。
loader 的布林值證明其本身的判定，不是遊戲服務端權限、畫面已渲染、
全部原生資源健康或視窗生命週期的保證。外層 4616A0／460C60／461AD0
未把每一筆的失敗傳回，因此不能只靠最外層回傳 1 來資格化完整供應者。

4606D0 讀 world context：若 +A7F2F64 的 signed WORD 小於 1，改為 105；
+A7F2F68 未達該值才遞增。另讀 timeGetTime，時計倒退先更新基準；
超過 500ms 的分支會寫其他 world 欄位並呼叫 41BDC0／41C060、條件式
426AB0，以及 533FC0／432A20；這些 helper 的完整用途及是否泵送事件
本輪未確立。「載入進度用計數」是推論，不把 105 當 NPC 容量或遊戲預設。
native 預載包含已觀察的時間／world 寫入；server 的純 source observer
不得呼叫它來取得資格，仍須維持自己的 immutable source generation
及現有 Current／publish／install 邊界。這輪全為靜態閱讀，未執行該函數。

下一步從已知 preload 結果接續既有 429820 資源選擇證據，建立實際
完整場景與資源 owner，再處理 Main 和 native transfer bridge；
不再把上述三個已分析函數列為尚未分析。
