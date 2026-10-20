# 台服 action9、回合時序及返回接續：pass5

2026-10-21。PHASE1／SOURCE_STATIC_ONLY；本輪沒有建置、執行測試、遊戲、VM、codec、遊戲 SQL、schema 安裝、匯入或部署。既有帳號、設定、存檔及原版 EXE 不變。下列是完成的源碼接線及修改後審查範圍，不能當成實際遊玩驗收。

## 本輪接線

- action9 從真正 C35 typed parser、Session 全批預檢、房間角色／操作權，到完整 Actor 換位、live assignment、同交易保存與延後接續。保存的 B4/E8 是入場來源，戰中位置另存；不以位置加7推算，不發不存在的戰寵。允許明確配置的空格或死亡 partner，實際操作者仍須存活且持有該次操作權。
- 依同版本 REA 修正83／88播放佇列。原版會先播放83批次再消費88；只送83而沒有邊界可能不開始播放。完整 profile counter 固定，不拿遞增回合代替；動畫批次單獨用0..254，避開255溢位。0B使用目前主角位置，即使其 side flag 為1；它還會消耗客戶端操作旗標，所以只重發服務端仍有效的同回合權限。
- 每次 publication 保留私有進度邊界，區分全員完整 socket Written、原始0B觀測與真正回合狀態。混合「操作＋0B」、其他玩家已排隊指令、最後玩家／最後AI、終局89、播放中斷線與SOS等待加入均連同檢查。0B沒有批次 nonce，仍是不受信通知，不能叫作原生動畫完成ACK。
- 返回必須有實際保存提交、原始C1C及全部返回框完整 Written；再以房間私有 ReturnContinuation 和 Session 真正新 INIT，接續原來的 companion／learning／inventory／equipment 圖。歷史 Written 不會重標成舊 Current；已release／stop／換owner者不能從相同數值重新取得權限。
- active44 以真正保存的完整 E3／FB 更新既有寵物。既有技能／學習後繼、返回後行走及再次入戰沿實際提交鏈續接。完整 catalog 支援明列的 Pet1／Pet2 替代材料，以種類、完整 metadata、除目前HP／MP外的 stats 及來源唯一比對；不猜測缺少外觀或原始欄位。開戰退休銀行視窗，返回後重新取得正常NPC開倉資格。

## 原件與審查證據

當前台服 EXE SHA-256：`aaf0fae66e89c4547244304ecd8f4c2755746ffa6c9b9dfe68a0ff3fd2b4cd48`。

REA 原始查詢、失敗查詢、analysis-only seeds、原件 section 等同性及 session close 收據位於：
`C:/Users/risei/.codex/artifact-archives/god2-server/20261021/sos-row-timing-continuation-pass5/`。
分析用 PE 沒有執行；額外 CALL seeds 不是原始 caller。詳細結果見：

- [原版換排、佇列及計數器 REA](tw-native-row-swap-and-cycle-20261021.md)
- [房間換排及時序接線](tw-pve-row-swap-cycle-source-20261021.md)
- [返回後資料接續](tw-pve-return-continuation-source-20261021.md)

每項修正均做修改後源碼檢查及分工交叉審查，保存對應 SHA。審查涵蓋呼叫者、來源資格、整批拒絕、狀態、保存／COMMIT不確定性、回覆順序、斷線及退休。回歸案例只新增來源，沒有執行。正式靜態封包報告每輪只允許一次，預留及終端收據也在外部同根；報告統計不是全遊戲完成率。

## 尚未證明的部分

CUSTOM-0161／0162 的配對授權、加入／排程政策及固定 counter 選擇仍明示自訂；客戶端接收器不能還原原服全部服務端規則。原服配對、費用、完整回合排程與counter意義、其他原生模式及原服公式仍有缺口。

完整原生材料仍須明列；本輪沒有自動填角色／怪物／寵物能力，也沒有啟用來源。shared common-world／真正三分流掛載及崩潰恢復執行器仍未完成。原版多人動畫、空格換排、實際換寵與技能操作、返回HUD及故障流程，須在後續獲准的集中建置／測試及原版客戶端階段驗收。不能把這次源碼接線宣稱為已實測或可正式上線。
