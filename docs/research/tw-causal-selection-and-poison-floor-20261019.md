# 選神回覆因果標記與中毒捨去小數（round477）

本輪接通 legacy C67 的真實私有提交、回覆來源及實際寫出觀察，並依
使用者最新答覆補上中毒取整規則。全部仍是 PHASE1 原始碼／靜態作業；
未建置、執行測試、Lua、遊戲、SQL、遷移、啟用或部署。全遊戲完成率
仍為 unknown/null，沒有新增原始戰鬥公式的恢復宣稱。

## 中毒按當前最大 HP 十分之一，捨去小數

使用者於2026-10-19明確指定：當前最大 HP 為123，扣12 HP。因此
CUSTOM-0157 的量值為 `floor(current maximum HP / 10)`。Lua5.4 使用
整數除法；C++ 驗證整數商、十分位餘數可重建全部輸入，並驗證 Lua
明確回傳的 damage_hp 等於商。`PoisonShareResult::damage_hp()` 提供
這個確定的整數扣血量。

餘數只供比例診斷，不會累積到之後的 tick；也不新增最低1 HP。最大
HP 小於10時，按此規則所得量為0。這不是以當前剩餘 HP 計算，也不是
以施放當時保存的最大值計算。既有 Battle 觀察仍核對實際目標、revision
與目前最大 HP，且不修改 HP／revision／RNG。數值維持既有 shared64
精確整數域，沒有新增遊戲上限或浮點截斷。

新增測試來源涵蓋123→12、整數邊界、小於10、超過浮點精確整數範圍、
signed64上界、無效取整，以及真實 Battle／Lua 觀察不改狀態。這些來源
尚未執行。中毒身分取得、觸發週期、到期／清除／堆疊、保存交易及
原生完整回覆仍未串接，不能把量值與取整確定當成中毒系統完成。

## 從真提交保留來源到原有 sender

`LegacyTaiwanOwnedDeitySelectionRegistry` 在真正最外層 callback 開始時，
綁定 private normal INIT、同一 Session、完整64位 owner、CS/IW phase
與精確 battle generation；新一輪 C67 在 SQL 前使舊來源失效。
registry 內部自行呼叫真正 `select_deity_with_source`，保留每個原 C67
一次性 ordinal 的私有 publication。沒有接受外部舊提交的入口。

私有 emission 由這條 producer 路徑建立，保留該次提交預製的完整 S31
frame。move-only `LegacyWorldReply` 只讓真正 producer 建立來源標記；
一般 bytes 仍是一般 bytes。leaf、八處 prefix 拆框副送及 guild53 的
return append 都保留同一 emission occurrence 與精確 frame 位置。
舊 raw leaf 若已配置 causal C67 callback，會在呼叫 SQL producer 前
拒絕該 C67，避免先提交再丟棄標記。

黑名單、隊伍目錄與設定同步三個外層，使用獨立、checked、LIFO 的
callback output-offset 範圍，按實際 `wire.size()` 累加位置。Session
最終依已登記的位置核對完整 child fragment 與 frame 邊界。這不是在
回覆中搜尋相同 bytes，也沒有把狀態式編碼的 wire offset 當 logical
record offset。side sender 與 final return 仍使用原本的送出路徑與順序。

Session 要求每個已建立 emission 精確綁到一次真實 Write；漏掉、重複、
重疊、偏移錯誤或 fragment 被更改都不能產生有效來源。Written 仍要求
真正 callback 被接受、封口及整組完整寫出，不是排入佇列或客戶端 ACK。
Application 在後續實際 callback 觀察並保留合格的私有選神來源。

## 已證明可達的舊流程順序缺口

合法 legacy 設定可啟用 Options 與 guild 路由。輸入
`[C67(A), options notification, C67(B), guild73]` 時，外層可先保存 A 的
回覆，稍後 prefix 將 B 的回覆副送，最後才送 A 的保存回覆。SQL 順序
為 A→B，實際 S31 則為 B→A；guild73 不必成功退會也能走到 prefix。
此精確反例在目前 release JSON 未啟用的外層 flags 下不會發生，但
配置驗證允許它，屬已掛線、可達的 OPEN 問題。

因此，整組實際 Written 不等於可延續選神狀態。Session 保留真實輸出
位置與既有流程，不因這種舊順序新增斷線；registry 的來源採納仍要求
私有 C67 ordinal 與實際位置順序一致，亂序時不給可延續來源。這沒有
修復上述客戶端最終選取狀態，也不能當成全配置的選神流程完成。

完整 restoration／技能書學習的選神延續、同批首次 baseline 的完整
before-source 資格，以及上述順序修復仍需繼續。Shared registry 與 PK
的 lease、presence、private ancestry 判定沒有放寬；legacy token 不會
冒充它們。

## REA 的生命週期與發放來源界線

新增一個 REA session、兩個析構函數分析，session 已關閉。四個選定
CFG 範圍核對69條原始指令；重用的控制流程與歷史 slices 另列，沒有
累加成唯一指令數。分析映像13個原始 PE sections 與現用台服 EXE 相同。

`C` 的 vtable 指到 `51B830→51B850`，已核對路徑只析構三個 UI 成員
與釋放；`51BDD0` 也只是釋放 UI handle。這些不是 header `+2D12/13`
初始化或整物件清零的證明。literal／bulk-size 搜尋的陰性結果只限已記錄
範圍，沒有證明所有 computed aliases 都不存在，也沒有判成 padding。

`87` 的實際接收分派已對回原始 bytes；它仍是收到 S87/38 才更新的
consumer，actor 來源另由 S86/5 接收。它不能反推原始服務端發放規則、
同一世界的實際 actors、施法權限或傷害／治療公式。

外部證據與逐輪 receipts 位於
`C:/Users/risei/.codex/artifact-archives/god2-server/20261019/legacy-causal-reply-round477`。
來源雜湊、回歸來源範圍及未完成項目見同名 JSON。
