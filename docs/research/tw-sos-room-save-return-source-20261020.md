# 台服 SOS 共用戰鬥、全員保存與逐人返回：來源階段

> 2026-10-21 pass5 更新：本文保留 pass4 歷史結論。action9、返回接續及83／88
> 時序已有後續修正，現況以 [換排與回合源碼](tw-pve-row-swap-cycle-source-20261021.md)、
> [原版佇列 REA](tw-native-row-swap-and-cycle-20261021.md) 與
> [返回接續](tw-pve-return-continuation-source-20261021.md) 為準；
> pass4 直接 consumer 推得的「83 後不能接88」不適用實際延後播放佇列。


2026-10-20，pass4；CUSTOM-0161／0162／0163。這是源碼接線與修改後審查，
不是編譯成功、黑箱通過或原版遊戲驗收。`world.owned_pve_rooms.enabled` 預設
關閉；未更動任何現用設定、帳號、遊戲資料庫或客戶端。完整目標與 Discord
四小時排程仍維持原先暫停狀態。

## 本輪實作

- SOS 使用獨立 PvE 房間與一份權威 Battle checkpoint／RNG；參戰者各自綁定
  實際 Session、完整角色身分、原 WORLD 初始化與戰鬥世代。晚加入只新增
  目前角色／實際出戰寵，不重設怪物、舊玩家 HP、RNG 或已用指令。
- 同一交易保存房間、成員、輸出與返回紀錄，以及全部仍受房間管理的角色
  HP／MP 和實際 slot44 Pet1／Pet2。完整原始寵物資料、版本、來源、角色與
  位置均做 CAS；只改已確認的 HP／MP 位元，不發新寵。空 slot44 與沒有該列
  分別保存。已返回／斷線退休的人保留歷史資料，不再覆蓋其後續遊玩。
- 每筆輸出保留完整記錄邊界；Queued 與完整 socket Written 分開。多人同時
  斷線以同筆保存退休，單人封包失敗不讓該人後續 Pending 阻塞全房。交易
  結束後失去來源時保留真正 durable 結果與 recovery claims，不偽稱 rollback。
- 原生 action6 逃跑與原始 C1C 返回各自檢查本人綁定與 context；一人退出不拆
  其他人的房間。返回保留原 WORLD，補保存 E8 與當時玩家集合，再接上返回
  Written 後的新集合，最後恢復輸入與移動序號。沒有重播 CF／2A／S30。
- 實際普通 Application 加入條件式掛載、移動回覆 Written 後的遇敵入口、
  同場景 SOS 目標、戰鬥標記、scheduler、disconnect 與 NET／GAME drain。
  完整顯式 catalog 缺少就拒絕；未提供預設怪物、原生外觀或自動資料匯入。
  目前刻意拒絕 shared common-world／三分流掛載，不以單世界假裝完成三分流。
- 保存的 B4／E8 前後排用於實際入場位置；主角／副寵占用明確配置的成對座位。
  銀行另接獨立離線容量匯出／核准 manifest 寫入入口，詳見各專題與中文 TXT。

## REA 核對與來源界線

匹配原版 EXE SHA256：
`aaf0fae66e89c4547244304ecd8f4c2755746ffa6c9b9dfe68a0ff3fd2b4cd48`。
本輪靜態原生分析與關閉收據保存在外部 pass4 `formation/`、`capacity/`；
分析器補建的函數入口不算原生呼叫證據。

- `51F410` 寫入兩側各14個座位，排列是5＋4＋3＋2；不是7＋7，也不能加7找
  另一排。`515C90` 的1C身分對應到目前主／副角色欄位；原服配對政策仍未知。
- `518E50` 的 side flag 選主／副角色，不是敵我。主角色旗標優先；兩者都開時
  先處理主角。action6 的部分原始堆疊內容沒有初始化，解析保留原位元，不能
  擅自要求為0。具體 UI 如何選出6的完整路徑未全還原。
- `518A90 → 52D360` 的88會直接改角色 HP／MP，而83攻擊經 `522FB0／524820 →
  528A70` 延後扣血。普通傷害後直接補88可能重複扣血，本輪已移除。新入場
  與顯式 CUSTOM 進度閘門後的新 Grant 才供應完整88。
- `518BF0` 的89修改 native control 狀態；不要求終局89後再收到新0B才返回。
  原生返回參照既有 `tw-battle-return-source-20261014.md` 的保留地圖路徑。
- 原版銀行 `471310／471610／471E50` 能證實顯示分頁及接收索引，不能證明
  原服如何解鎖、付費或給容量。CUSTOM-0163 要求完整核准清單，不推算容量。

戰鬥指令／AI／遇敵頻率／零獎勵／循環 BYTE 動畫分組及回合排程為顯式自訂
政策。0B 只能是未受信的客戶端進度：伺服器還需檢查實際角色授權已用完與
全房輸出 Written。舊協定沒有回合 nonce，無法由它證明動畫真的完成；BYTE
分組不是 recovered native counter 規則或權限憑據。

## 修改後再次審查

檢查包含入口、原指令批次、權限、全員 CAS、失敗／提交歧義、斷線、逐人
返回、關機順序和同功能其他入口；獨立審查未代替編譯。找到並修正：

1. 某人輸出等待期間，另一人的合法原 GAME 工作可能已排隊：保留原工作，
   不複製 Context 重播；quiet entry 還須核對真正尚未結束的 WORLD 工作。
2. 先抵達的0B不能充作未來進度；排隊的純0B則不能被「沒有 actor grant」
   分支吃掉。普通攻擊與0B同批不算 Written 後的新進度。
3. 一人離房後不得更新其歷史 grant epoch，否則剩餘玩家下一回合的資料鏡像
   不一致。已釋放與新釋放角色的最終實際資料驗證分開處理。
4. 多幀輸出失敗需退休該人的全部 Pending；其他參戰者繼續。SQL 最後讀回與
   COMMIT observer 的資料漂移要保留真實 durable／current 狀態。
5. 移動服務 `resume_after_battle` 與一般 `current_location` 跨資料讀取持有
   iterator；改為完整快照、mutation fence、重新查找及同值 ABA 防護。
6. 返回全幀 Written 才更新 WORLD；新集合補送與 movement／title 回呼後再次
   核對原來源，然後才解除輸入。已返回玩家回呼失敗要明確關閉本人。

新增房間、形成／投影、Session、catalog、容量及移動重入回歸案例的源碼；
依 PHASE1 規定全部未執行。外部 `sos-owned-core-source-manifest-v1.json`、
`formation/pve-core-independent-source-review-v1.json`、capacity、Session 與
linked-source review 收據分別記錄實際雜湊和審查限制。

## 尚待完成，不能宣稱100%

原服遇敵、獎勵、公式、配對與 action9 全房換位／延後完成、原生 counter
時序仍未完整恢復。沒有可憑空補出的完整 native actor／敵人資料。
新程式有持久 recovery claims，但尚無實際崩潰恢復執行器。返回後既有寵物／
學習資料的私有初始化證據更新還需正式 continuation，不能改 token 或重播
S30 冒充；這也是啟用前的必要缺口。完整三分流共同掛載尚未接上。

集中編譯、所有必要回歸、自己的服務端與目前台版客戶端多人實測，以及
後續啟用／發布，均屬後續階段。本輪沒有測試通過數或正式遊戲完成率。

本輪唯一一次正式靜態封包盤點因 ledger 的頂層來源清單漏列新增檔案而失敗；
失敗與終端收據均已保留，沒有重跑。事後已補來源清單，但本輪正式報告仍是
失敗，不能引用舊報告冒充這批源碼通過。下次正式盤點須另起工作輪次。
