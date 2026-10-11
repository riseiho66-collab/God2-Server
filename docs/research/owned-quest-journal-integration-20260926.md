# 持有角色任務日誌：服務端串接（2026-09-26）

## 本輪實裝

- migration24新增character_quest_journals：15槽60bytes little-endian、revision、origin、provenance、CUSTOM-0041。未搬入舊diagnostic_quest_journal或把其重新標為原生。
- SqliteQuestJournalRepository只接受角色擁有者，非0顯示引用必須符合當前418個定義與2014描述的完整pinned來源。BEGIN IMMEDIATE保存、CAS/readback與例外回滾。讀取以deferred transaction保存一致性，無snapshot不要求來源已匯入，避免破壞既有登入。
- Application在世界首次有效tick將持有快照送入原生DB subtype4全部15槽，包含空槽。之後普通tick不重送／改進度；重新登入按保存值重送。持有正式快照優先於診斷日誌，阻止旧診斷對話覆寫。
- packed highWORD僅是原生描述選擇器，沒有當成完成狀態。快照政策是CUSTOM-0041；不提供自動接任務、授予物品、完成或發獎。

## 驗證

- C++repository在真實當前Mission_data匯入temporary SQLite後通過508檢查，包括越權、CAS、同值revision、完整來源缺失、非法selector、兩連線stale、清空/reopen、trigger中斷及readback回滾。
- CTest七套7/7通過：quest_journal、kunlun_birthplace、database、config、recovered_movement_service、import_native_quests、import_native_quest_sources。
- Own-server TCP五案5/5通過；新增持有journalケース驗證首次world一次投影、移動、服務重啟及重登入重送，不改人物資源、神仙／戰寵快照、持有journal或其revision。沿用的NPC／怪物限制、城鎮與崑崙登入回歸均通過。
- 隱藏God2Lab實際現用客戶端：private-owned-quest-journal-20260926-01 accepted=true。只讀UI+C2104共60bytes核對全部15槽，包含44第一描述、48第五描述、47零highWORD與50第三描述等**合成顯示測試**；走動後仍一致，4/3位置保存為126/128/revision2，client_alive=true。
- 這不是接取／完成上述任務驗收，未向正式玩家授予這些journal項目。桌面未切換、不截圖、不注入或寫客戶端記憶體；來源DB及兩個client EXE雜湊不變。

## 正式發佈

artifacts/releases/owned-quest-journal-20260926-01保存舊EXE、原設定、SQLite線上備份及migration後候選庫。備份／套用使用native_quest_catalog_release.py，更新前檢查無玩家連線及live表內容仍與備份一致，失敗可還原EXE與整個DB schema。

verification.json：player_tables_changed=[]、quick_check=ok、native_source_counts=[418,2014,169,85]、client/config unchanged、active binary matches tested candidate、PID8160 port2592。所有舊帳號／角色／存檔資料保留；正式新journal表0列，沒有合成測試項目。

## 原生內容追查與剩餘項目

native-kunlun-quests-44-50-evidence-20260926.md逐列保存139個原文／hash，kunlun-quests-44-50-npc-chain-20260926.md核對8項来源。確認崑崙地圖鍵5576，龍麟3251不同於龍鱗4427，合成材料3251～3258與4個師傅座標；相同名称的破山劍仍有WPN165／MIS4541區別。來源對話保存不同給圖／給寵流程，不能混串。

4個合成師傅catalog1667～1670可唯一定位名稱／外觀並匹配4/3預載，但仍缺完整世界實例與面向，未亂擺NPC。任務44～50皆仍缺至少一項原生接取／事件／結算／獎勵權威。完整原生可玩任務仍0；本輪完成的是持有journal保存與原生客戶端還原路徑，沒有宣稱全部任務已還原。

整體可玩完成度約11%（規劃估計，非量測封包覆蓋率），保持活動重建目標。
