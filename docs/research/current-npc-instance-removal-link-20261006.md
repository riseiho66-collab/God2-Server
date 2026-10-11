# 原生 S2C72 NPC 建立與 S2C75 移除的身分連結

本輪重讀 SHA-256 `149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763` 的釘定原生映像。逐指令 bytes 與位址保存在 [`npc-instance-removal-link-v1.json`](../../artifacts/integration/packet-connections-20261006/npc-instance-removal-link-v1.json)。這修正上一輪「primary selector 尚不能連到移除 identity」的過度保守敘述；既有報告保留原文，該研究文件另記此修正。

`S2C72` logical21 的 `logical+1..4` 是 selector DWORD。原生 case `6A691` 讀其低 WORD；普通 constructor `CC3B6..CC3BE` 對同一 DWORD 遮罩 `FFFF` 後查 NPC pool，`CC621..CC62F` 再遮罩並存入 pool record `+0`。組合 constructor `CBD7A..CBD93` 及 `CBFFC..CC00C` 做相同的低 WORD 查找／存入。NPC pool 是 `W+1539AED8`。高 WORD 可影響 catalog 外觀選擇，卻不是這個 pool 的查找 identity。

`S2C75` logical5 的 case `6AA93..6AAA0` 取 `logical+1` WORD，對同一 NPC pool 呼叫 `CC990`；`CC990` 隨後用 `CCF80` 的精確 DWORD identity 查找。原生 72 constructor 存入的值已遮罩為低 WORD，所以此移除 key 與同一可見 NPC instance 對應。`S2C74` 使用另一個怪物／跟隨寵物 pool，不能套用 NPC selector；同號 C2S75 公會命令也無關。

服務端 `RecoveredNpcRecord::instanceIdentity()` 現將既有 `primarySelector()` 的低 WORD 用原生 pool 語意明確命名；`SqliteWorldDisplayRepository` 對 72 儲存列的 identity 仍是同一數值，沒有 schema 或既有資料遷移。`RecoveredWorldPoolRemoval` 保留 75 另外兩個原生未讀位元組，並保持 `runtime_emission_enabled=false`。

已存且實際發送的原生 72 可以提供相應 75 的 **目標 identity**，但還缺伺服器權威 NPC 動態消失事件、發送時機、來源追蹤與未讀兩 bytes 的原生 server producer。不能只因離開場景或 catalog 變化猜一筆 75；原生 full reload 已有清池流程。本輪未新接完整功能路徑，也沒有 build、測試、客戶端執行或部署。
