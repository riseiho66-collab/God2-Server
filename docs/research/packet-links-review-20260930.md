# 本輪原生封包串接獨立審查 — 2026-09-30

## 範圍與候選

審查 C2S24 備用戰寵42↔43、C2SD6 戰寵還原請求拒絕路徑、
C2S20/S2C23 角色次要文字與 migration39。未改聊天、IME、驗證、
啟動器、角色主名稱、客戶端檔案或正式玩家存檔。

最後測試的候選副本：
`artifacts/research/native-pet2-revert-20260930/build/god2-server-packet-links-final.exe`

SHA256：`1c2a6d090c6759eca2786adba690ab7da60e6a821ff87c73005e7df01ad72fc5`。
先複製再啟動隔離進程，避免主線後續編譯覆寫受測 EXE。測試中的
帳號／寵物／道具資料均位於獨立副本；沒有將合成數值提升為原生平衡。

## 發現與處置

1. `Application.cpp` 初次以 `database.recovered_characters()` 的基底介面
   建構 `RecoveredPet2RevertGate`，但 Gate 需要 SQLite 專有的背包與
   未結算戰鬥查詢。主線已改用既有 `supply_repository` 具體參考；
   沒有刪除所有權或戰鬥檢查來通過編譯。
2. `tests/test_recovered_world_records.cpp` 的完整 variant `static_assert`
   與 `reconstruct()` visitor 起初未加入 D6、20，會造成測試編譯失敗。
   已將具體位置與新增兩個 encode 分支的修法交主線。這是測試
   更新缺口；前25個 runtime variant index 並未被改動。
3. 隔離 TCP 測試最初將副本命名 `accounts.db`，不符合既有 town
   diagnostic 保護條件。測試副本已改為 `town-diagnostic-accounts.db`，
   保留原保護條件，沒有放寬正式伺服器驗證。

除上述問題外，本輪靜態審查與下列具體測試未發現新增阻擋缺陷。
測試編譯修正及主線整體 CTest 結果由主線另行記錄，不以本文件代替。

## Application 分流順序

- 先剔除原有 client diagnostic 記錄；剩餘 span 只在同步 callback
  內使用，所指向的 local vector 在 callback 返回前仍有效。
- D6 攔截位於文字、果村、配點、道具與戰鬥 mutation handler 前。
  一個 D6 可伴隨 Tick；第二個 D6 或其他操作會整批記錄為
  `mixed_mutation_batch` 並返回空回應，不呼叫任何 mutation handler。
  D6+20 無論順序均由 D6 拒絕；不會先保存文字。
- 20 路徑同樣只接受一筆 Request 與 Tick。world-ready、既有持有資料
  投影、角色所在場景、非戰鬥、非場景切換均先檢查。NUL 後的
  客戶端堆疊殘留先清零，S2C23 完整 frame 在保存前編碼。
  儲存拒絕不送 S2C23；成功提交後才返回已準備好的 frame。
- 24 仍經 `RecoveredWorldService` 的單一 inventory transaction
  分流，拒絕混合 mutation，world-ready 與非戰鬥條件先於 callback。
  Application 只把42/43組合交新 reserve helper；44與既有28選擇
  契約没有被此 helper 擴張。
- D6與20的新攔截不經原有世界 Tick 的一次性持有快照還原，因此
  初次投影前同包帶 Tick 並不會越過投影 gate。另送正常 Tick 後
  可再操作，已由 TCP 測試確認。

## 所有權、交易及封包邊界

`SqlitePetReserveMove` 在 `BEGIN IMMEDIATE` 中重讀角色所屬三格，
比對來源／目的快照、revision、metadata、generation與provenance，
再檢查未结算戰鬥。兩個 SQL UPDATE 均以舊 revision 作條件。
兩次寫入後驗證全部三格，包含不得改動的44；encode callback前後
各讀回一次，任何例外都由 transaction destructor 回滾。

沒有推測不存在的空格。目的格需有明確保存的 row；空來源或同格
操作不寫入。完整 E3/FB 實例與來源資訊跟隨移動，只改相應 routing
byte與格位revision。先清兩個舊 generation cache，再追加各自完整
metadata/occupancy/stat。雙 FB 的最大邏輯回應216 bytes，小於原生
queue cap2560；E3/FB混合為196 bytes。

D6 decoder只確認4-byte方向契約，保留全部raw operands；資格檢查
另拒絕原生缺石時洩出的20/60索引、超出範圍的pet/option。Gate沒有
任何成功結果，終點是`effect_unqualified`。它不扣石、不生成歷史、
不呼叫28選擇、不回放FB來假裝成功。

角色文字是17-byte C2S20與17-byte S2C23。最多15個原始字節再加NUL；
storage要求16-byte canonical零填充。SQLite owner JOIN與revision CAS
涵蓋存在／不存在的文字row；原始編碼、UTF-8對照與provenance在load
時再次驗證。空文字是可保存的清除值，不會被當成缺row。

## 角色文字重登入及編碼

Session在原有world-ready尾段取得language flag：1選CP936，其他已
接受值0選CP950。保存時使用當次Session語言，未改角色主名稱編碼。
每次新登入的初次持有資料投影從DB讀取已保存文字，使用
`SqliteRoleTextRepository::project`轉為當次Session編碼。

同編碼保留原始canonical bytes；跨編碼需完整encode/decode還原同一
Unicode字串，而且不能超過15 bytes。不可表示、替代字、截斷或長度
膨脹失敗時不送錯誤文字、不改保存row，只記錄display unavailable。
這不保證原客戶端在「略過文字回覆」後的畫面觀感，仍需實機驗收。

獨立 review test 實測 Windows CP936的`€`占1 byte，而CP950占2。
1..7字可精確投影；8..15字被拒絕且不截斷。另測未知來源／目標
codepage、兩個SQLite connection的stale CAS、跨owner、writer lock
衝突，以及AFTER UPDATE trigger破壞UTF-8讀回時的完整rollback。
共57 assertions PASS，MSVC `/W4` 編譯無警告。

## 連線及物件生命週期

- 新Gate只持有run_server內既有repositories的參考，沒有額外執行緒、
  全域state或Session裸指標。它在TcpServer建立之前存在。
- `SqliteDatabase::Impl`先宣告connection，後宣告各repository；反向
  解構確保repository先釋放。新role_text repository的constructor
  不查表，因此initialize先於migration39不會提前讀缺表。
- Session的game callback持有`shared_ptr<Session>`與完整record vector；
  request指標只在同步handler執行期間使用。完成後的回應是自己的
  `vector<uint8_t>`，不參照stack或database row記憶體。
- 回傳空vector是「已處理且無wire」，可保留連線；nullopt及例外
  沿用既有Session拒絕／斷線政策。D6明確拒絕時的連線存續已實測。
- Disconnect清理既有`owned_player_and_companions_projected`等Session
  記錄；新文字是owner持久資料，沒有新增需要disconnect清除的cache。
  重登入透過新Session重新取得語言與投影資格。

## migration39正式存檔副本驗證

實讀正式設定：
`artifacts/releases/town-chat-welcome-20260924/server-config.json`。
其DB為：
`artifacts/playtests/persistent-launch-20260923-01/town-diagnostic-accounts.db`。

`tests/research/test_packet_links_migration_review.py`使用SQLite
`mode=ro`與`PRAGMA query_only=ON`，以backup API產生臨時副本。
只對副本執行候選`--migrate-only`，此模式不啟動網路或Lua。
結果1/1 PASS（2.076s）：

- 副本原schema38升到39；原53張表的全部row fingerprints與既有schema
  不變；舊migration1..38的全部欄位逐字不變。
- 新`character_role_text`為空，不替玩家補文字。
- 第二次migration為冪等，沒有改寫歷史。
- `quick_check=ok`，`foreign_key_check`無錯誤。
- 正式來源只以唯讀開啟，仍為schema38。未重啟正式服務。

此測試固定審查「當前schema38升39」；正式升級後不應把它當成日常
CTest gate繼續執行並將預期版本變化誤報成失敗。

新表使用`ON DELETE CASCADE`。既有`erase_owned`也會從FK graph動態
找出帶`character_id`的後代表，因此不需凍結刪角程式新增硬編碼表名。
角色文字代理自己的repository測試覆蓋cascade、單rowrollback與
檔案重開；本review的57 assertions另覆蓋雙connection與讀回破壞。

## WorldRecords 與 variant

新D6及20分別追加為index25、26；原index0..24完整保留。
`src`搜尋未見以這些index執行實際domain分流；`.index()`只用於診斷
log。服務路由使用`holds_alternative`／`get_if`／typed visit。
switch使用原生C2S長度（D6=4，20=17），未借用同opcode的S2C長度。
整個frame先decode完成才會呼叫game handler，截斷新record不能先提交
前面的mutation。舊world-records的compile-time完整variant清單須同步
更新，已列於前述發現。

## 實際TCP結果與尚未覆蓋範圍

最後候選的`test_pet2_revert_server.py`為3/3 PASS（20.797s）。
正常4選項、fragmented frame、Tick同包、缺石raw20/60、錯誤item/
source/slot/option、空pet、初次投影前請求均保持預期拒絕與連線。
D6與24、28、67、21、20、第二個D6兩順序共12個mixed batch無部分
提交；現在逐案比較10張相關表，包含新增角色文字表。截斷D6被斷線
且資料不變。來源合成fixture的SHA256前後一致。

仍未覆蓋或不宣稱的範圍：

- 原客戶端的24拖放、20文字輸入／顯示、D6面板操作與再登入畫面。
  TCP合成peer成功不等於原客戶端UI驗收。
- D6真正還原效果、原始歷史值／選项映射、扣石數量與成功回覆契約。
  這些仍未啟用；不能把可辨識拒絕列為還原玩法完成。
- save/commit已成功後恰逢socket斷線的使用者觀感。DB交易會保留已
  提交資料；沒有推測原生協定不具備的跨重連request-id或exactly-once
  行為。文字相同內容重送可冪等；寵物移動需以重登入保存快照恢復。
- 多個玩家session同時更新同一角色的完整端到端競爭；review測過
  repository兩connection的CAS/lock拒絕，未將其稱為全網路競爭驗收。
- streamer/presence與world clock啟用時可能各自發送既有非本請求回應。
  D6本身不送成功；隔離TCP的「無wire」不是對所有背景通知的全域禁令。
- 強制殺進程、磁碟滿、SQLite底層I/O故障與回應queue耗盡。既有異常
  路徑未在本輪作大範圍故障注入。
- 正式發布、schema39原地升級與全套frozen回歸屬主線發布門檻，本review
  只完成候選、隔離副本及明列測試。
