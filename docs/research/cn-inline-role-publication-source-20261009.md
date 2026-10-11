# 第202輪：陸服原生 WORLD24 數值發布來源

本輪新增 `SharedInlineRoleCountersPublication.h/.cpp`，並修改 `SharedWorldGameplay.h/.cpp`。來源串接由191增至192段；新增完整雙向玩法路徑0，全遊戲分母及完成百分比仍未知。依使用者「下一輪結束後停止工作」，第202輪封存完成後暫停目標模式，不開始203輪。

實際增量是：已持有的原生17位元組 WORLD24 → 實際共用世界收件者及原始登記 token → 真正提交後事件的唯讀權威判定 → 原有 held publication queue → 保留實際本機釋放事實。這是來源接線，尚未有正式 Main 選定的具體事件 issuer，不是已完成數值玩法、部署或客戶端驗收。

原生依據沿用第201輪固定雜湊的陸服 EXE：WORLD cell 00492A68 → 004912E8，以 packet+1、mode0 呼叫 00518F70；length cell 00567D34 → 00567B9A 返回17。四個 DWORD 順序為 inline-role +5C/+64/+60/+68。原生封包沒有 actor/subject ID。四值維持未知語義，不標成 HP/MP，不當成 C1F 或 C25 的回覆，不把原生 DWORD 宣稱為已完成64位元數值擴充。

新發布來源只接收完整且已持有的 `CnInlineRoleCounters24` 記錄，不以截斷64位元值、猜測編碼、零資料或成功回覆製造輸出。發布持有真實原連線；第一次實際 ready 發布才取得既有 registry 的私有 token，後续操作固定同一登記世代。實際 WorldOwner 必須確認共用事件、保存、持久重播、提交版本、角色與 inline-role 關係、全部原始數值及順序。單純 record 的值、client pointer 或相同 lease 不提供權限。

BeforeQueue、BeforeRelease、AfterRelease 都保留相同角色、存檔位置及登記 token，且在真正權威觀察前後重新確認。原始 bytes 在觀察前完整複製；事件與提交版本不得為0；記錄數及總 logical bytes 有明確來源預算。局部 last-attempt 僅避免本機立即重複，不代替共用持久事件重播。

準備觀察與實際佇列批准使用獨立 nonreentrant stage。同步完成、取消、晚到完成及 throwing send 保留實際傳回true的本機釋放事實；發布前預先配置兩種 receipt，釋放後不為 receipt 配置記憶體。AfterRelease 不再有效時，保留已釋放 receipt 並標示 post-release current=false。這不表示網路送達或原生客戶端接受。

靜態審阅發現既有 CnTransportSession::complete_send 在 game callback 前套用 accepted && !closing。因此 strand 已釋放、但 callback 前 close/drain 的情況可能回傳false。新來源保留此既有契約，不擅改登入、運輸或其他發布者：只有傳回true是確定的局部釋放；false或沒有receipt代表釋放狀態未知，不能當作「沒有送出」或重送依據。完整 released-then-closed 事實仍缺單獨的來源介面；共用持久事件恢復由真正issuer負責。

SharedWorldGameplay 只在實際1C初始發布內綁定可選來源。compose 要求相同 presence/transport registry，不發啟動資料、不替代 bootstrap、不安裝不存在的權威。來源隨拒絕、terminal、destructor 取消自己的 pending；不釋放共用 token 或寫入 common state。既有 C2S 格式/分派及 roster31/34/35、C1F、C25 維持原樣。

尚缺：具體共用角色數值事件與提交/持久重播 issuer、四個 DWORD 的完整來源語義與跨版 mapping；技能書扣除/學習的權威 mutation、原生初始技能主清單及世界到戰鬥清單來源；完整 TW/CN/web 路徑盤點與64位元/堆疊99擴充。所有路徑打通後才全面建置、測試、修復及發布。

現有盤點：TW/CN C2S 觀察聯集各156；TW 世界 S2C 長度支持252/256、戰鬥分派110；CN S2C 階段條目280（帳號6／世界206／戰鬥68）。TW world parser 審閱42/65，64.6%只代表該範圍審閱。958端點索引、38條未正式host的部分owner鏈、CN93個/TW10個來源phase binding都不能加總成完整遊戲路徑分母。

本輪只做靜態原始碼及來源封存。沒有建置、測試、執行codec/native/server/DB/SQL、遷移、部署或原生驗收；帳號存檔、客戶端、原生字體、繁簡轉換與凍結功能保留。
