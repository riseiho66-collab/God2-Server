# 目前原生 PET 活動 C2S9E：格式接入與功能邊界

來源為 verified mapped image
`149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`
及既有 `artifacts/integration/packet-connections-20261006/beast-panel-static-contract.json`
的 `D8680`、`D8780`、`D8810` 有界原始指令。該 artifact 早期的
C2S6B 欄位排列表已由後續 V2/V3 修正；本節只採用獨立的9E切片。
本輪沒有客戶端執行、測試、build、SQLite寫入或正式服務部署。

原生 `4132E0` 發送 9E 加6-byte body，logical size7：
`9E | context:u32 raw LE | operation:u8 | selection:u8`。
`D8810` 從面板 `+88654` 複製四個 context bytes；state0 發
operation0，state2 發 operation1，兩者以選取索引加1發送。
`D8780` 發 operation2，選取索引仍為零基；無選取時原始值可為
`FF`。面板 callback `D8680` 透過不同 control 分派到兩個 producer。
這些數字是 client producer 分支；沒有由此證明任務、派遣、召回、
領獎或其他遊戲動詞。不能把顯示中的數量當作獎勵授權。

不同方向的原生 S2C `C5` 長309 bytes，用來建立含完整 context、
state、訊息鍵及原始選項陣列的探索面板快照；`C6` 長7 bytes，
更新 context/state，其中 state4 會關閉面板。它們與9E有面板
狀態關聯，但尚無服務端 action→state/reward 的因果契約。
已存 C5 快照與當前面板選取也沒有原生 replay-resistant 權限。

正式來源的 `RecoveredBeastExploration::Action` 保留所有原始位元組；
`RecoveredWorldRecords` 新增9E解析，`Session` 的獨立
`beast_activity9e` 旗標預設 false。`Application` 不設旗標、
不處理 action；原有 CUSTOM-0085 面板展示/舊context關閉路徑不改。
因此9E是**已知格式和停用中的解析來源，功能未接通**。

仍需恢復：同伴及面板選取的完整 owner/revision readset、各 operation
的真正規則、計時/消耗/獎勵與持久化、Lua規則、C5/C6及其他實際
S2C回覆關係、重登/重試時序。只有這些接入正式 Application 和
SQLite 後，才可把9E特定功能分支列為來源串接完成。
