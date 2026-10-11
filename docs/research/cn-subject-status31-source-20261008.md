# 陸服世界 31：主體狀態發布來源

本輪接續 140 的技能定義匯入来源及既有 113 的 31／68／6D consumer 來源，不重新宣稱那些原生欄位首次恢復。PHASE1 只交付來源；未建置、測試、原生執行、資料庫存取或部署。

## 原生來源與身分邊界

固定 CN PE SHA-256 為 `582f269535f86e95fcd77946821adf79a30d1bd33f21d566cf48c36fd221b3c8`。沿用已封存的 WORLD31 primary dispatch cell `00492A9C`→`0049134C`，實際 callsite `00491356`→`004D58B0`；長度 cell `00567D68`→`00567BBD` 回傳 29。這不建立同 opcode C2S31 的因果配對。

`004D58B0` 的實際 ECX 為 UI owner；`004D58C1` 取 UI+430A8 role，`004D58C7` 取 role+D8 名冊，`004D58CD` 取 BYTE count。`004D58D8` 用 MOVSX CX,BYTE[actual payload]，`004D58E0` 比較 entry+0 WORD；按 3EC stride 取第一個相同值，沒有命中就返回，不建立新 entry。這和 WORLD34／35 的零擴充 subject byte 不同。封包原始 byte、符號擴充後的 native WORD、名冊 ordinal 及 common 主鍵需分開。

命中後，payload1→entry+2 BYTE；payload2／4／6／8／10 的 unsigned WORD 零擴充到 entry+44／48／4C／50／54 DWORD；payload16／18／20／22→entry+38／3A／3C／3E WORD；payload24 的低 15 bits→entry+28 WORD，高 bit→entry+5A BYTE。payload12..15、26..27 沒在這個 prefix 中讀取，仍原樣保留，不称為零或 padding，不猜 HP、攻防、EXP 或費用語義。

`004D59BE／CA` 把真正命中的 entry／ordinal 寫回同一 role+D0／CF。`004D4E00` 的另一個 UI 選擇入口同樣要求 signed index 非負且小於實際 count，再以 role+D8+index*3EC 選中。這些是 native 身分／選擇來源，不是 server 權限。`004D5030` 等 helpers 的全部 UI／資源後續行為仍開放。

## 來源增量

新增 `CnSubjectStatus31` 精確 29B view，保留完整 raw record，提供上述 fields 與 signed-WORD first-match。既有 `CnWorldConsumerSource::OwnedRows31::project_existing_row` 改為使用同一份 view；它原有完整 row、Current、page、flags 及可選研究快照邊界保留。

新增 `SharedSubjectStatusPublication`：真正共用操作 commit 後，由實際 issuer 提供 recipient lease、event ID、新 revision 與原生 31 記錄。readonly／non-yielding qualifier 必須確認真實共用主體／收件者映射、native 第一個名冊命中、所有欄位、規則、存檔、持久重播、次序及新 revision。這些要求没有預設 owner 或任意成功實作。

該 source 在 `SharedWorldGameplay` 真正 1C 初始化內綁定同一 connection／ready presence／lease；綁定不發包。之後實際共用事件才可以經 `send_world_batch_with_publication`，在 BeforeQueue 與 QueueAccepted 兩次 post-commit 觀察通過後釋出。Plan 與 raw record 持有至 transport completion；本機 last-attempt fence 不是持久重播。publisher 不要求客戶端程序記憶體、原生地址或 Snapshot，也不調用已退役的 pre-commit Current。

## 計數与未完成範圍

本輪新增一個條件發布 owner、一個世界 S2C31 來源關聯；opcode 本來已在盤點中，新增 opcode／完整雙向路徑均為 0。實際 common issuer、主體／技能 mapping、Lua 規則、角色存檔／重播及 Application 未配置。不是完成 31 所有上游／状态／同号 C2S 變體。

共用表原則、TW／CN／PC／網頁及 WSS、完整世界與全部玩法、64 位元數值、合格堆疊 99、等級不改、後續集中全面測試與修復發布均保留。只有仙幣上限已定為 99,999,999,999；原生 31 的舊 WORD 欄位不能假装承載較大數值，擴充必須另有版本化 producer／consumer／顯示來源。未修改凍結功能、原生字體、文字轉換、客戶端或歷史基準。全遊戲總量與百分比仍未知。
