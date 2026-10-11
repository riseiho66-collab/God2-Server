# 傳送珠持久化與提交邊界審查（2026-09-30）

範圍：當前原生客戶端 item16055/type8/full20 的資料契約，以及
CUSTOM-0057 的既有持有物品保存、扣一次使用次數和 Island01 回城。
本 lane 未改正式存檔、正式服務、聊天、驗證、IME、launcher 或客戶端。

## 資料與交易

- Migration40 只新增 `character_teleport_gem_metadata`，不初始化物品或
  次數，不改既有 scalar inventory、角色或位置。新的 overlay 綁定既有
  `(character_id,slot)`，並具有 `ON DELETE CASCADE`。
- `save_existing` 僅接受已持有的16055/count1、目前來源雜湊、完整20bytes、
  type8、charges1..10、正確 scalar revision；已有 overlay 無法重設次數。
- `load_saved` 只列舉完整 overlay。歷史 scalar16055 缺少 metadata 仍維持
  原值，不推算次數，也不阻止其他合格 gem 的初次投影。互動讀取該缺資料格
  則明確拒絕。
- 扣次數與位置的完整 CAS 在同一個 `BEGIN IMMEDIATE` 交易。只有來源
  area2/scene0 可提交到既有落點2/4/56/75，兩個 revision 各加1。
  callback 在 COMMIT 前建好 projection/61，例外、SQL trigger 或讀回不符
  都回滾。單次耗盡清空 scalar 並刪除 overlay 是 CUSTOM-0057 規則。
- 全格移動只接受 gem→明確空格或 gem↔gem，完整 metadata/provenance 隨
  instance 移動。普通物品、武器 overlay、未知/缺格均拒絕，避免遺失 metadata。

## 獨立提交邊界檢查

`tests/companion/test_packet_commit_review.cpp` 使用同一個隔離 SQLite
connection 的真實 MovementService 與 gem repository；54 assertions 通過。

- Movement prepare 不修改 DB 或記憶體位置。
- 位置外部 revision 已改，repository 在 callback 前拒絕，不扣次數。
- gem projection callback 失敗，次數與位置一起回滾。
- 成功後 in-memory commit 只標記新位置與 transfer pending，不再寫第二次 DB。
- 原生目的地 receipt 完成前不能繼續轉移；重登讀回2/4/56/75。
- 同一 prepared plan 不能再次扣次數。
- 角色文字新增、更新與冪等分支的 prepare callback 失敗均回滾；callback 後
  讀回遭破壞也拒絕提交，錯誤 owner / stale revision 不進 callback。

`tests/test_teleport_gem_repository.cpp` 的122 assertions 通過，另涵蓋
擁有權、pending battle、來源雜湊、完整20bytes保留、修訂上限、FK cascade、
兩格移動和 SQL/readback 回滾。

直接編譯與結果：
`artifacts/research/teleport-gem-repository-20260930/unit-result.json`。
上述176 assertions 不是實際客戶端驗收。

## TCP 驗證

測試來源：`tests/research/test_owned_teleport_gem_server.py`。
隔離來源 save 使用 SQLite `mode=ro` backup；每案使用 TemporaryDirectory、
localhost 隨機 port 與獨立 candidate process。測試合成 full20 fixture 明標
`CUSTOM_TEST_NOT_NATIVE`，不代表任何取得物品或原服發放規則。

前四個 case 覆蓋25/26→6D、99→41/3B+61、86取消、6D控制、錯誤 owner/slot、
缺 metadata、首次投影前請求、過期 slot revision、重複/混合包、24整格移動、
位置 SQL 失敗後重試、最後一次耗盡及重啟再登入。

初版固定候選 SHA256：
`81bcf822a26c36076c5fdd51b2b3bbf7f465136048ea5f080dfd0673d1410874`。
4/4 PASS，11.039s；候選副本、完整 log 與 source hashes receipt 位於
`artifacts/research/teleport-gem-tcp-20260930/`（`tcp.log`、`result.json`）。
每案結尾驗證來源 save SHA256 不變，context 關閉所有本測試建立的服務進程。

初次執行的 fixture config 關掉 `spawn_guides`，被既有 door-route startup
gate 正確拒絕；修正隔離 fixture 為 `spawn_guides=true` 後四案通過，沒有
為測試放寬 runtime gate。

### 實際客戶端發現的恢復分支缺口及必要回歸

hidden-client 在初版81bc候選發現：`diagnostic_town.quest_progress=true`、
`owned_supply=false` 時，完整 gem20bytes 已初次投影，隨後舊 town bag
恢復 loop 卻再次呼叫 scalar projection，因 item16055 非普通補品而丟例外、
斷線。前四案關掉 quest progress，沒有涵蓋此組合；原先「未見 App 阻擋缺陷」
的結論範圍不足，不能涵蓋這條恢復路徑。

主線窄修 town bag 與 diagnostic supply 的兩個 scalar 恢復 loop，啟用
owned gem 時跳過16055，保留已由 gem repository 建立的完整 instance 投影。
新增兩案在舊81bc候選皆重現 EOF，log 為 `regression-before.log`。

修正候選 SHA256：
`b94ea3dda7bd8c5de8023f2dbaa8be7391d1f72f0b3feac66d2cabca84effc2c`。
完整六案 **6/6 PASS，13.941s**。固定候選、log 和 source hashes receipt 在
`artifacts/research/teleport-gem-tcp-20260930/final/`（`tcp.log`、`result.json`）。
新增案例確認 full20 只投影一次，後續 scalar 包沒有清空或重投影 gem；
連線保持，25仍可開6D選單，DB 的次數／metadata／位置均不變。

第二案走合法的 `diagnostic_world_resources=true` 外層分支，並以 log
確認執行。resource 內層 `diagnostic_world_supply` 目前與 gem/town 配置
不可同時成立：town DB 的 resource gate 要求 battle-after-quest，而它
要求 rounds1；world-supply 加 battle-transition 則要求 rounds3。因此
沒有放寬 gate 去強行覆蓋不可達配置；該內層 skip 僅完成靜態審查，不能宣稱
TCP 已跑到它。

## 最終 Application 分流審查

- gem claims/preflight 在 targeted-supply 分流之前，因此26/16055不會先被
  普通補品分支吞掉；TCP 的26成功選單已實際驗證。
- 新20和D6分支早於 gem 且完整檢查 mixed batch；20+99兩種排列都無資料變更。
- offer 對 owner、world-ready、已投影、非戰鬥及非 transfer-pending 的限制
  保留。save/位置 CAS 在 repository 中再次核對；拒絕回空 response 保持連線。
- whole-gem24分流在普通背包路線前，僅按已持有 scalar 的 key 分類；完整移動
  成功才清 pending offer。初次投影與斷線清理都有各自的 gem session 集合。
- 全部 wire 編碼、visibility副本與pending節點配置在 DB COMMIT 前完成；之後
  記憶體提交依序列化 executor 不變量。剩餘 post-commit I/O 風險列於下節。

已發現的 legacy scalar restore 缺口由主線修正，新增回歸驗證通過；本輪
owner、CAS、transaction 回滾與 native25/26分流驗證未見其他阻擋缺陷。

## 保留風險與不宣稱範圍

- TCP 合成 peer 不等於原客戶端 UI 點擊、選单顯示與換圖驗收；由主線的
  hidden-client 證據另行驗證。
- 尚無正式玩家取得16055 full20 的發放路徑；不從舊 scalar 自動賦予10次。
- 只開一個來源2/0→2/4的窄路線；其他原生目的地、貨幣費用、冷卻、戰鬥中
  使用和取得規則未在此推測實作。
- SQL/編碼失敗發生在 COMMIT 前可回滾；COMMIT 後 socket 斷線則以持久化
  DB 為準，重登恢復結果，不承諾協定不存在的跨重連 exactly-once receipt。
- `commit_owned_island_return` 的 no-throw invariant 依賴現有序列化遊戲
  executor，若未來改平行處理，須重新驗證 prepare 到 commit 的記憶體生命週期。
- 沒有模擬磁碟滿、SQLite 底層 I/O 損毀、process 在 COMMIT 瞬間被殺、或
  post-commit 發送 queue 記憶體分配失敗。
- 正式部署/schema40 升級尚屬主線決策，本 lane 不執行 apply。
