# C67 暫存回覆的實際順序修正（round479）

本輪只做來源／靜態作業。已在真實 Session callback 串接因果選神回覆的
延後合併；尚未建置、執行測試、原版遊戲或任何 SQL，不宣稱遊戲內已驗收。

## 原因與修正範圍

現行 Application 的合法路徑可讓 [C67(A), C1D選項, C67(B), guild73]
先提交 A、B，卻先副送 B，最後才送外層保存的 A。位移標記只能記錄位置，
不能修復客戶端實際最後看到的選取。放寬 registry 的採納條件也不正確。

現在當帶私有來源的 B 準備副送、且同一 callback 已有較早 A 保留在 final
片段中時，Session 保存 B 的原始 occurrence 及當時 callback output base。
B 經 Created→Deferred，沿真正外層累積的 raw-prefix fence 延後交付。
一般未標記 side-send 保留既有行為；這不是全部輸入記錄的通用輸出排序。

callback 返回後、框驗證及 movement finish 之前，先核對完整原始片段與
框邊界，按登記位置插入 B，不搜尋相同 bytes、不按 opcode 猜來源。
例中的實際 final 為 A→S1B→B；同一位置的多筆插入保持 occurrence 順序，
較晚的原始 final 片段及 movement offsets 同步位移，不拆開已登記整批
movement 回覆。所有保留的私有標記都核對實際 physical order。

來源標記經 Deferred→FinalReserved→Bound；Written 仍由真實 callback
接受、完整封口及所有原始 Write 完成決定，不是排入佇列或客戶端 ACK。
normal options 的 S1B 收據仍對實際最後回覆核查，原送出呼叫的 self-view
退休及 actor-status write 失效動作也保留。既有精確 WorldResponseWrite
若與新回覆不符會拒絕，不私改舊收據來取得資格。

延後空間有既有 callback byte／count 限制。錯誤 fence、片段被改、重複
標記、順序錯誤、receipt 衝突或例外不能取得來源；callback output capture
上的例外會明確拒絕本次 callback。SQL 不重跑，不回滾已提交玩家資料。

## 靜態核對與待驗證

新增 regression source 使用真正 Session、Registry 及私有 SQL producer，
包括不同 key 的兩筆選神、同 fence 三筆、B 延後而 C 留在 final、原 S1B
正常回覆收據、錯誤 fence 及被改片段。只新增測試來源，未執行測試或 SQL。
這些來源模擬實際 appender 邊界，並未執行完整 Application wrapper graph。

目前仍需後續集中編譯與測試，特別是完整 Options／Party／Blacklist／guild
配置、movement 收據及精確 whole-response 的交集。若 whole-response
同時捕捉 splice 前 bytes，現行實作明確拒絕，不能宣稱該交集已完成。

REA 沿用匹配現用台服 EXE 的既有原生證據及 C67/S31 契約；本輪問題是
自有源碼的 sender／buffer 組合，未新執行 REA、遊戲或反推原服公式。
453筆技能、凍結126/150、存檔及台服單一版本範圍保留。
完整 restoration／技能學習延續、2A／Entered／Main、D8／6B／C28、
完整原始公式及全遊戲驗收仍未完成。全遊戲完成率維持 unknown/null。

外部逐輪證據與唯一正式盤點：
C:/Users/risei/.codex/artifact-archives/god2-server/20261019/causal-order-round479。
