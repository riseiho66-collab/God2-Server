# 崑崙七選項對話與原生來源入庫（2026-09-26）

## 完成的層級

1. 當前客戶端MultiMessage三檔原文：2995 introductions、8799 options，合計11794文字列正式入庫。不是2995任務，也不是新增2995 NPC。
2. C++讀取完整表結構與三份來源metadata，精確校驗1434的八列原始CP950 bytes、行號、decoded offset與hash欄位，才產生已驗證28bytes 7A mode4。
3. 新的bounded conversation service綁定session/account/character/request/context，只接受1434選項0..6一次；opaque tail無論0..255均不是授權。手動86只關閉目前綁定會話，不能以其中pointer residue或source word授予任務。
4. 隔離Application路由已用實際隱藏客戶端驗證。正式服只啟用原生來源catalog；diagnostic_knowledge_menu維持false，不能把測試first-tick事件當原服NPC互動。

## 來源與缺口

原生7A/85/86契約、選項資源與完整點擊/分頁/關閉原生鏈，分別見 current-dialogue-mode4-1434-20260926.md、current-knowledge-menu-text-lifecycle-20260926.md。後者已證request word另參與NpcHead lookup，不能把它當任意nonce。隔離測試使用request0/context68/reply0，都是CUSTOM-0043，不宣稱天尊原生NPC ID。

元始天尊位置與面向、完整world NPC instance、37互動到1434、七選項到教學/任務事件仍未有原服authority。新的來源补查见native-npc-source-inventory-followup-20260926.md。未生成任何未證實NPC，未授予或完成任何任務。六個教學主題有原文內容匹配，仍不等於恢復原服事件join；choice0文字中的完成/衣物/地圖獎勵更不能直接執行。

## SQLite與C++

Schema25 native_multi_message_source：

- native_multi_message_sources：3個source_file、壓縮與解碼SHA256、CP950、count/lines/bytes、SOURCE_DISPLAY_ONLY。
- native_multi_messages：2995個key、所屬來源、option_count。
- native_multi_message_rows：11794個intro/option row，ordinal0為intro，保留raw_record/text_bytes、line/offset/hash。ordinal1..N是資源ordinal，不直接冒稱85的zero-based choice。

匯入器先驗完整三檔才寫入；BEGIN IMMEDIATE、全表readback、idempotence，對partial/conflicting catalog拒絕覆寫。C++Reader用deferred只讀transaction，資料不完整或1434改字/改來源即拒絕。正式startup會驗有內容的catalog並記錄NATIVE_MULTI_MESSAGE_SOURCE；資料來源不具NPC/quest權限。

## 實際客戶端與測試

- private-knowledge-menu-20260926-01：first page row2→choice0、原生85、原生關閉；進入4/3，移動成功，owned journal保持。
- private-knowledge-menu-20260926-02：下一頁→上一頁→下一頁均成功且沒有選項封包；第二頁row3→choice6成功，clock週期更新保持。
- private-knowledge-menu-20260926-03：final binary重复第二頁驗收，accepted=true。與正式發佈候選SHA完全相同；無截圖/記憶體寫入/輸入桌面切換，來源DB與客戶端不變。
- Standalone knowledge_conversation：七選項×256 opaque bytes、跨owner/request/context、choice7/8/32767/65535、重放、關閉狀態都檢查。
- Python importer7tests通過；C++來源reader valid与6種corruption拒絕，ro DB bytes不變；config/database測試通過。本輪相關CTest5/5、own-server TCP/restart6/6。
- 原生oracle七個選項均經當前PE WM_LBUTTONDOWN hit-test與完整85/close鏈；實際視窗測到choice0/6與page controls，不宣稱七個均逐一做實際視窗驗收。

## 正式發佈與保留

knowledge-source-20260926-01已正式套用，schema25。verification.json：player_tables_changed=[]，active_config_unchanged=true，client_unchanged=true；native sources3/2995/11794，owned journal仍0，完整playable original quests仍0。原有4帳號/3角色、崑崙出生設定、時鐘60秒及原生位置限制保留。沒有新增NPC生成位置、戰鬥值、獎勵或synthetic journal。

全專案規劃估計維持約11%，不是原生封包完成率。本輪是正式來源入庫、C++來源消費與隔離對話互動驗證；正式天尊NPC與任務流程仍未接通。
