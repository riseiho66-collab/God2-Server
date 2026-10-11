# 角色刪除與完整原生摘要失效的同一交易來源

第152輪 `20261008-cn-native-summary-removal-invalidation-source` 處理151輪已定位的 stale summary header 缺口。新增明確的 `erase_owned_snapshot_with_native_summaries`／`SharedCharacterRemoval::commit_with_native_summaries` 來源入口，把完整 account 原生 delivery snapshot 失效与共用角色刪除放進同一 SQLite transaction。這是來源實作，實際原生 handler／issuer 尚未選用，schema 尚未安裝，沒有執行 SQL 或改存檔。

新 `load_for_account` 必須位於實際 owner transaction 內，按 group／server／client SHA 的 canonical scope 順序讀完整 tuple，沿用既有單 scope reader 的 ordered mapping、common ownership、name mode、optional role 四欄與 origin 檢查。它包含帳號的所有版本／目的地 scopes，不能只挑 CN、可見角色或含被刪 ID 的摘要。就算 header inventory 為空，也實際查 child table 並核對總筆數；孤兒、錯 owner、缺 schema 或不一致不能轉成 empty success。函式沒有隱含 BEGIN、DDL、資料預設或 schema-on-read。

Actual issuer 提供完整 expected inventory 並明確授權 account-wide delivery snapshot invalidation。新 observer 收到 Phase、完整 expected summaries 與完整 original common roots；BeforeCommit 看 staged absence／roots minus selected ID，而非要求舊 raw07 Current。它仍須核對更早操作／權利／規則／可見性／revision，且同步只讀，不 SQL writes、不 yield、事件泵或借用失效 spans。

新 path 檢查同一實際 SqliteRecoveredCharacterRepository、accounts、SQLite pointer、summary owner thread、外部 transaction absence 與 FK enforcement。跨 repository writing lease 從所有 callbacks 前持有至整個 removal transaction 返回，阻止同一 summary writer 重入。原本 legacy public overload 與 frozen TW／CN handler 的選用維持；只有明確新入口帶 actual issuer／完整 expected data 才失效摘要。

交易內先核對完整 selected root、完整帳號 roots 與完整 expected summaries；BeforeErase 回呼前後重讀。Summary child 僅有 character_id FK，不能證明 account ownership，因此拒絕其他 account 的 mapping 指向本次 removed ID，不能借 descendant cleanup 默默修補其他帳號。

在刪 common root／descendants 之前，按 exact account 刪除所有已授權 header，直接 changes 數須等於 expected scopes；FK cascade 結果另由 header／raw child 都 absent 的讀取確認，不能把 changes() 當 cascaded child 數。此時再次檢查完整 original roots、empty inventory 与 foreign-account guard，再走原有 descendants cleanup／完整 selected root CAS。

BeforeCommit 前後要求完整原始 roots 只少 exact removed ID，其他 ID／account／slot／profile／created_at／codepage／style 不變，且全部該 account header／child 仍 absent。所有失敗在同一 transaction rollback。沒有生成替代 raw07、count、level、revision 或空原生回覆。

共用 coordinator 在 saved-state 改變前準備既有 per-character admission invalidation，兩 phase 前後核對 admission plan／prepared & active presence。COMMIT 後同步立即套用已配置的 invalidation，沒有讀取、來源回呼、配置或 yield。這覆蓋同一被刪 common character 的 TW／CN grants；不代表 summary CAS 的一般更新或整個 account 所有 issued world offers 已撤銷。

151輪 stale-header 缺口在**新明確來源 path**獲得解法。舊 native deletion 仍呼叫 legacy entry；實際 issuer／handler 改選、account-wide offer refresh／revocation、原生回覆／replay／disconnect recovery 及 schema qualification／可恢復發布仍 OPEN，不能宣稱正式刪除功能已修復或 playable route 完成。

原生追查新增 GodLevel source qualification：`00423480` 呼叫 `004234F0` parser 後，`004234D5` 明確覆蓋 EAX=1。Column count 存於 resource+C；GodLevel caller 的 read-nonnull 成功條件不能證明兩欄完整、整表載入或94-byte bank copy 安全。Parser379-byte截斷與 bank stride94是不同界線，selector4 bytes／first NUL／42CA20 actual caller仍未知。42C9B0是42C9AF JE的 displacement byte，不能當入口或 caller。新註解保留此資格限制。

Receiver 追查確認 **既有** WORLD68／13-byte／world-connection-1 的 UI context，沒有新增 phase。`004C4060→004C409C→004C4880` 具有 call-free actual ECX／nonnegative handle／nonnull item／literal1 關係，lookup helper 的 ESI 保留及 `004C494A→004C77E0` 同一 owner callback 已資格化。四個 primary CFG 為1345 bytes／375 sites；局部 frontier0 不等於所有 descendants／network owner／全遊戲 graph 完成。Signed record BYTE 与1／30門檻不是 stack99資格。下一 source 是 `004C7816→004C5320`、`004C784E→004C5440` 的 resource／key／output WORD。

三位子代理分工、M2獨立唯讀 review 與所有歷史封存保留。新增 source inventory／invalidation／明確 commit caller 是實際來源進展；packet／phase／完整 owner chain／完整雙向 route 增量均0。完整遊戲分母、已完成路徑總數與百分比仍未知。PHASE1只靜態來源與檔案／hash／CFG／帳本；沒有 build、test、C++／native／Windows API／server／client／Lua／DB／import／migration／deployment。完整 TW／CN／PC／web／WSS、數值64及 qualified stack99 目標繼續。
