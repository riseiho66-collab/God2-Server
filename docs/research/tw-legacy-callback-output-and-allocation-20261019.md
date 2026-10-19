# 舊流程完整輸出與配置來源（round476）

本輪將 legacy C67 的實際 callback 輸出紀錄與輸入等待接到 Application。
這是完整選神來源銜接的必要接點；尚未把 legacy 的私有選神提交接到
完整 restoration、技能書學習或 PK。仍只做 PHASE1 原始碼／靜態分析，
沒有建置、執行測試、遊戲、SQL、遷移、啟用或部署。

## 實際輸出與輸入等待

legacy dispatcher 會在同一次 callback 中先呼叫多次 sender，最後再
回傳剩餘 wire。新的 `Session::WorldCallbackOutput` 保留每一次實際
自身輸出的 occurrence、順序、logical、原 encoder 所產生的 frame
及各自的寫出狀態。三條既有 side sender 與真正的非空 final return
各自保留原 Write；沒有重新合併封包，也沒有以 queued／acceptance
代替原 socket 的完整寫出。

整組來源必須在自身第一筆輸出之前，由實際 callback 的 private normal
INIT 擷取。它綁定同一 Session、完整 account／character、實際
CharacterSelected／InWorld phase 與 INIT 的精確 battle generation。
其中一筆失敗不會抹除較早真正 Written 的歷史，但整組不能取得 Written。
callback 被接受、封口且所有真實成員完成後，整組才是 Written。
被接受且完全沒有輸出的 callback 使用獨立 `NoOutput` 終態；沒有空的
Write、WorldResponseWrite 或選神來源權限。

Application 在 legacy 最外層、任何原 handler／SQL／side-send 之前擷取
並啟用獨立輸入等待。等整組 Written 或真正 NoOutput 才能繼續原始輸入；
既有單筆 WorldResponseWrite 的等待仍保有自己的身分與釋放規則。
raw suffix、已排入 GAME 的工作、關閉與失敗都必須遵守兩種等待。
紀錄至多每個 Session 一份最新 occurrence，受 max_sessions 限制；
disconnect 先依確切 Session 實例移除，再呼叫其他觀察者。

另一個 peer 的 fanout 不會成為本組成員。尚未支援的自身輸出 API
會讓這份新紀錄失效，不能偷偷漏算，但保留原 sender 路徑。這份紀錄
描述實際 transport custody；它本身不證明資料庫提交、技能來源或客戶端 ACK。

## 為何完整選神銜接仍有缺口

同一 callback 的 `[Tick, guild operation, C67]` 可以先透過遞迴的
single-Tick prefix 發送首次 restoration 的 S30／S31／S34／S35，稍後
才真正提交選神。因此不能把同批每筆 S31 都當成該次 C67 回覆。
copied Record adapters 也使原 Request 的記憶體位址無法充當來源。

Session 新增一次性、依原 C67 順序及完整 payload 核對的 private input
claim，支援合法 copied Record。output cursor 只證明成員開始位置，
不能證明同一個 final-return 內某段 bytes 產生於提交之後。完整 registry
還需要從真正 C67 producer 經 leaf return、八處拆框副送，以及 guild53
直接拼入最終 return 的接點，保留私有 emission／frame-range sidecar。
不能在末端以 substring 或相同 bytes 搜尋補造來源。

目前沒有新增 legacy registry，也沒有用這份 composite 冒充 Shared
registry 的 single whole-response token。Shared selection 與 PK 的
presence、lease、private ancestry 判定沒有放寬。

## REA 配置鏈的新增結論

本輪一個 REA session 分析四個函數，已關閉。六個 CFG 範圍核對 126
條原始指令；重用 wrapper 與 parent 範圍另列，不累加成唯一指令數。
分析映像的 13 個原始 PE sections 與現用台服 EXE 逐位元組相同。

- `547985` 的 `6F6EB8` 是配置失敗後的重試／new-handler 旗標，不是
  heap handle。真正 heap handle 是 `6F70D4`。
- `5479B1` 對大小做 16-byte 對齊，在已核對的大物件／threshold
  前提下走到 `HeapAlloc`，傳入 flags `0`，沒有要求 HEAP_ZERO_MEMORY。
- `54F12A` 建立 heap 並存入 `6F70D4`；`54F166` 核對到釋放路徑。
  這些事實沒有提供整個物件或 `C+2D12/+2D13` 預設清零的保證。

未知 header bytes 繼續保留未知。literal-address 搜尋只限制在已記錄的
範圍，未證明全域 computed alias、所有 startup 呼叫或整體生命週期。
本輪沒有新恢復傷害、治療、命中、閃避、暴擊、攻防、五行、抗性或
持續效果 tick 的原始公式。全遊戲百分比仍為 unknown/null。

外部原始證據與逐輪 receipt 位於
`C:/Users/risei/.codex/artifact-archives/god2-server/20261019/legacy-callback-output-round476`。
它們是研究證據，不是執行期依賴。對應雜湊、測試來源範圍及未完成項目
見同名 JSON；測試來源未執行，不代表黑箱驗收通過。
