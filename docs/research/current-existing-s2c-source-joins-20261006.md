# 已有正式來源的 S2C 分支補登：E3／FB、1A、DA

2026-10-06。本輪只核對現有原生長度／WORLD dispatch、codec、Application
與持久來源，並更新方向帳本。沒有新建遊戲效果、執行測試、啟動客戶端、
安裝資料表或部署正式服務。方向分類保存於
`artifacts/integration/packet-connections-20261006/s2c-world-consumer-frontier-v10.json`；
它僅取代 v9 的**分類**，保留較早原生證據和來源實作。

| 分支 | 已有來源與原生接收端 | 嚴格範圍 |
|---|---|---|
| C2S 28 → S2C E3／FB | `Application` 選取 callback 呼叫 `RecoveredOwnedCompanions::select_pet2`；同一持有者的槽 42..44 透過 `SqliteCompanionRepository::transfer_pet2` 更換，回覆 3B／41 與 E3 固定 53 或 FB 固定 73。原生 WORLD case 分別 `6919E`、`691B0`。 | `CUSTOM-0039` 目的槽選擇，只是已持有戰寵的特定來源分支；不涵蓋 C2S 28 的其他道具、全部戰寵取得／成長、所有 E3／FB 變體或原始目的槽政策。 |
| S2C 1A | `Application::send_world_clock` 在 `world_clock_enabled` 且世界準備後發送 logical 4，之後按連線同步；原生 WORLD `6B022→C35F0`。 | `CUSTOM-0042` 時間錨點；非天氣、每日重置或獎勵權威。設定預設關閉，未聲稱正式服務已啟用。 |
| S2C DA | 已持有外觀快照在設定允許的裝備來源中保存並編碼 15 bytes；`RecoveredVisibility` 可向同場已建立的觀察者推送。原生 WORLD `69369`。 | 裝備到外觀的原始映射仍缺；本帳只登錄設定限定的自有快照分支，保留八個 component 與完整 actor WORD，不認定全部 DA 變體完成。 |

上述 E3／FB 是既有來源**特定回覆**，1A 是設定限定的來源推送，
DA 是設定限定的外觀推送。它們此前漏列於路徑帳本，本輪補登，並非
新開發或新驗收。仍需全遊戲變體清單、真實客戶端集中驗收與最終發布。

本輪 C2S 候選 151、WORLD parser 63、限定已審查來源分支 41
（局部 65.1%）、缺口 12、待接群組 10；S2C 支援長度 252、
非預設 206、已登錄來源回覆 opcode 43（+2）、來源推送 4（+1）、
設定限定可見性推送 4（+1）、獨立格式 9、未分類 127（-4）。
全遊戲完整封包總量、完整路徑數與完成率仍未知。
