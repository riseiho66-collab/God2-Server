# 全 NPC 原生位置檢查：2026-09-26

## 本輪實際結論

**尚未完成全 NPC 的原生座標與面向配置。沒有用猜測值補齊，也沒有把任務文字或圖片位置冒充完整原生擺放表。**

目前正式環境原本會生成的两位城鎮嚮導，是 CUSTOM-0020 測試擺放：1606 在 110/69、1607 在 112/70、方向 0。現已啟用 `development.diagnostic_town.native_npc_placements_only=true`，阻止這些測試位置生成，並拒絕其測試互動。已保存的任務、背包、角色與帳號不刪除、不重新初始化；這兩位嚮導的任務暫時不能從 NPC 觸發。

此限制不是「全 NPC 已擺好」。目前沒有可據以設定所有 NPC 完整位置与面向的合格來源。

## 已檢查的當前客戶端來源

`tools/strike_lab/audit_native_npc_placements.py` 的輸出保存在 `artifacts/native-npc-placement-audit-20260926/evidence.json`，含原始行、雜湊、原始位元組及未知欄位。

- NPCAppearData：4,043 筆。身分、名稱、外觀與其他旗標／複合外觀欄位；不是 NPC 座標表。
- NPCList：451 筆。area／scene 的外觀資源預載組；原生 0045A8F0 讀取其 5 個資源碼槽位，不是 x／y／面向。
- MDT／MDL／HMD：429 個資產。地形、模型、室內與入口；僅 cityI1.mdlZ 引用 `npcad.ROM`，這個引用本身不證明是可互動 NPC 的擺放記錄。
- 任務／對話來源中的座標文字提示：851 處。保留文字的完整行，沒有自動將提示綁為 NPC 出現記錄。名稱可能重複、同一行可能有多個目的地；方向缺失。
- client.godZ／client_p.godZ 為檔案 CRC 清單，不能當作 NPC 擺放資料。
- 上述檢查範圍沒有使用已退役的 Classic／XJZ 資料。

## 現用解殼 EXE 的直接證據

直接讀取 **現用 God2.exe 的 PE 映像**，確認下列 NPC 接收路徑與原生映像的位元組完全一致，沒有只依賴舊反編譯文字：

| RVA | SHA256 | 功能 |
| --- | --- | --- |
| CC621..CC690 | e2aac96315e1a4408dc39ad9154f785885a983b5dcf2250bee1d7bc9ecb96982 | 新 NPC 的方向與座標讀取 |
| CC41A..CC447 | 2b43c4598aa96eed157a59d13ebd99578d876f872e40dc241a4aa0972a002ce9 | 已存在 NPC 的座標更新 |
| 6AA63..6AA8E | 8404b51adfba80ca6ec3faed7707bc31e71bd68760ba895efc432992c5ac0d79 | 接收記錄引數傳遞 |

以包含 opcode 的 21 位元組 0x72 記錄計算：

- direction = logical[9] >> 5；這裡只確認原生方向編號，沒有猜測其羅盤方向名稱。
- packed = little-endian DWORD(logical[17..20])。
- x = (packed >> 2) & 0x7FFF。
- y = packed >> 17。

現用 EXE 在 VA 004CC635 從 EDI+8 讀取方向，004CC676 從 EDI+10 讀取座標。EDI 指向服務端記錄 opcode 後的內容，這些位置不是固定 x／y／direction 常數。

因此反編譯可還原如何解讀原服送入的擺放值，不能自行生成原服的全部輸入值。需要原始服務端 spawn／NPC 配置、資料庫或可核對場景的原服 0x72 出現記錄；目前已向使用者請求該來源路徑。

## 實作、驗證與發布

- Config 與 Application 增加原生限制，場景進入時保留已保存任務、聊天、背包及角色可見性回傳路徑，僅停止測試嚮導擺放與互動授權。
- 真實隔離 TCP 測試 2／2 通過：原生限制不洩漏兩個測試出現記錄；其互動不修改已保存狀態；選擇與重啟還原回歸通過。
- 背包 TCP 回歸 3／3 通過。
- 發布备份：`artifacts/releases/native-npc-policy-20260926-01`，保留舊 EXE、配置及 SQLite 線上備份。
- 本機 2592 已重新監聽；更新時無玩家連線。
- 隱藏桌面回歸：`artifacts/playtests/private-native-npc-only-20260926-01` 登入、完整狀態還原及三次戰寵操作通過；輸入桌面未切換。此測試含合成神仙／戰寵實例，原有圖像診斷仍記為未解決，沒有把它宣稱為原生圖像完成。
- 後續檢查將互動拒絕限制到真正的 NPC／任務記錄，防止普通世界 tick 被誤判。新增「兩次真正 NPC 互動恰有兩次拒絕」回歸，2／2 TCP 測試再次通過。最終修正版備份／發布在 `artifacts/releases/native-npc-policy-20260926-02`。
- 本次服務端發布包含上一輪已測試的持有資料路徑與 migration22；正式庫原有 4 個帳號、3 個角色，人物資源／角色快照表原本皆為空。沒有將隔離神仙、戰寵或 NCP catalog 匯入正式庫。
- 發布前后比較所有既有非 migration 表，記錄完全一致；SQLite quick_check=ok；God2.exe 雜湊未變。
- 原生擺放實際完成：**0 筆完整的 area／scene／NPC／x／y／direction 記錄**。不能以 4,043 筆外觀名稱作為擺放完成度。
- 整體可玩完成度仍約 11% 的規劃估計；此輪沒有恢復全 NPC 擺放，不增加該估計。
