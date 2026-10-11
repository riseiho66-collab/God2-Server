# 既有持有角色資源／輔助屬性／任務日誌 S2C 還原推送 — 2026-10-06

本輪只核對正式服務端來源和已釘定的目前原生接收端，沒有新增執行
功能。方向帳本先前未登記四個**條件式來源推送**；v11 補登 2C／DB，
v12 補登 22／24，兩版只更新分類，保留 v10 及原生長度／分派索引
不變。22 原已登記為 C2S21 四維配點的回覆，此處是另一條首次
WORLD 還原來源，同一 opcode 不重複算為新回覆。

| S2C | 既有正式來源 | 原生接收與限定 |
| --- | --- | --- |
| `22` | `RecoveredPlayerSnapshot::load_for_world_entry` 在首次有效 WORLD tick 讀取持有資源與已存角色；有角色快照且 max HP／MP 與資源一致時，Application 先發原始 25-byte role snapshot。 | 原生 `E6B40` 消費 22 的等級、四維、進度等欄位。此推送不同於已登記 C2S21 配點回覆，不證明成長公式或所有 22 變體。 |
| `24` | 同一持有資源快照存在時，`RecoveredRoleVitals::encode` 產生 17-byte HP／MP／最大值記錄並由 Application 發送。 | 原生 `69F4D -> E71E0` 消費 24；此來源是玩家保存值還原，不是怪物屬性、傷害或成長權威。 |
| `2C` | `Application.cpp` 首次有效 WORLD tick 讀取持有角色的 `SqliteRoleAuxiliaryRepository::load`；有保存快照才原樣發出 61-byte logical record。Repository 檢查 owner、client build、origin、design ID、revision 與 raw codec。 | 目前原生 `4E6600` 消費 2C；`RecoveredRoleAuxiliaryProjection` 分別定位四個顯示修正值、五行與角色雙攻雙防。這不是裝備聚合、戰鬥公式或怪物能力來源。 |
| `DB` | 同一首次 WORLD tick 讀取持有角色 `SqliteQuestJournalRepository::load`；有快照才經 `RecoveredQuestSync::encodeJournalLogical` 按槽 0..14 發出十五筆 subtype 4、每筆 13-byte logical record。Repository 驗證 418 個任務定義／2014 筆描述來源及 packed reference。 | 目前原生 `6B44E -> 854F0 -> C9670` 消費 DB4/5；這個來源只支援已存日誌的 DB4 顯示還原，沒有證明 DB5、任務接取、完成或獎勵。 |

四條來源都在首次有效 WORLD tick，且僅在相應持有快照存在時發送；
這個 22 分支不是 C2S21 的同步回覆，DB 不是 D7 的同步回覆，
也不是每位玩家必然會收到的推送。
這輪沒有新的 C2S 功能路徑，沒有 build、測試、客戶端執行、正式
服務部署或任何玩家資料變更。全遊戲完成百分比仍未知。
