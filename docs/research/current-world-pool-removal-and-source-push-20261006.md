# 當前原生 WORLD 物件移除與既有來源推送

原生映像 SHA-256：`149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`。本輪沿 [`S2C 第一跳證據`](../../artifacts/integration/packet-connections-20261006/s2c-unclassified-first-hops-v1.json) 的 WORLD dispatch 切片，核對既有服務端來源。三種低位元組相同的移除封包作用於不同的原生容器，不能共用授權或把同號 C2S 當回覆。

| S2C | 長度／WORLD case | 原生操作 | 服務端狀態 |
|---|---|---|---|
| `73` | 5／`69A28` | `FB4F0` 移除遠端角色，並以轉換後的身分在怪物／跟隨寵物池呼叫 `CC990`，另通知 UI | `RecoveredVisibility` 的同場景離開／轉場來源已有，但由診斷可見性配置控制；正式可見性未啟用 |
| `74` | 5／`6A65D` | 取 `logical+1` DWORD 的低 WORD，以 `W+153B8758` 怪物／跟隨寵物池呼叫 `CC990` | 只有本輪新增的保留原始 bytes codec，無合格動態怪物移除來源 |
| `75` | 5／`6AA93` | 取 `logical+1` WORD，以 `W+1539AED8` NPC／本地標記池呼叫 `CC990` | 只有本輪新增的保留原始 bytes codec，無合格動態 NPC 移除來源；同號 C2S 公會解散無因果關係 |

`RecoveredWorldPoolRemoval.h` 分別表示 `74／75`，只公開低 WORD instance identity；`logical+3..4` 保留為未知原始位元組，改身分時也不覆寫。codec 的 `runtime_emission_enabled=false`。

後續同日修正：上一版此處稱 NPC primary selector 與 `75` instance identity 沒有證據可連接，這說法過於保守。釘定原生 `72` 普通與組合 constructor 均先將 selector 低 WORD 用於 pool 查找，再遮罩存入 record `+0`；`75` 以同一 pool 的 WORD identity 呼叫 `CC990`。因此已存且實際發送的 `72` 可以識別相應的 `75` 目標。這個身分關係不提供 NPC 動態消失時機、權威狀態或 `75` 的兩個未讀位元組，仍不能據此啟用發送。詳見 `current-npc-instance-removal-link-20261006.md`。

另有三個已存在、這輪才補入 S2C 路徑帳本的場景來源推送：`71` 原生怪物顯示、`72` 原生 NPC 顯示、`78` 怪物等級。`recovered_world_display_batches` 只從有場景及來源標記的儲存資料產生 `71／72`，核對 catalog，並為同一怪物 identity 的已存等級發 `78`；`Application` 在合格世界到達時發送。這是特定來源資料的顯示分支，不表示全怪物／NPC 分布、PvE 權威、動態刷新或全部變體完成。

`5E／6F／73` 的遠端角色移動／生成／移除由 `RecoveredVisibility` 和 `Application` 的診斷可見性配置約束；這三個已有來源分支，但正式玩家可見性、身分全域策略與當前客戶端多人驗收仍缺。帳本把它們列為配置限制的來源推送，和 `71／72／78` 分開。

本輪新接的完整遊戲路徑為 0；新增的是 `74／75` 精確格式 codec 與八個既存原生入口的來源狀態分類。沒有 build、測試、客戶端執行、正式服務變更或資料庫寫入。
