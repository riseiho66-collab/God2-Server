# 台服 PvE 返回後的原有資料續接（來源階段）

狀態：PHASE1／SOURCE_STATIC_ONLY。未編譯、未執行測試、未開啟遊戲或資料庫，未部署；本文件不是 Windows 或原版客戶端驗收。維持 CUSTOM-0161 的明示房間政策，不宣稱恢復原服完整戰鬥／學習規則。

## 實際接線

`OwnedPveApplicationSource::member` 在真正 Session Prepared 時呼叫 Application 安裝的 ReturnHandoff。此時原始 companion 發送者必須已完整 Written（空內容為真正 NoRecords），所有真實 inventory／selection／learning 後繼已接到同一 holder。保留確切 holder、canonical、原始完整 material、初始化、物理 Written 歷史及 actual movement owner／位置，不從戰後相同數值反推前置資格。開戰同時退休物品／金錢銀行視窗；回來必須重新取得 NPC 開倉資格。

有 learning source 時，`prepare_pve_return` 捕獲確切 Entry 或「尚無 Entry」、MaterialEpoch 以及原有 pending／latest／selection／material 指標。Prepared 最後的純 fence 重新比對這些來源；release、stop、同值重新 bootstrap 不能恢復退休 epoch。戰鬥期間的資源與斷線保存由實際房間權限負責；學習服務的退休不阻止保存，但不能取得新的正常世界技能資格。

SOS 等待安全的 admission 邊界時，由 Host 保留有界 Prepared 綁定；此時不呼叫 member supplier、不建 WorldBefore、不發 entry，也不顯示 Fight。真正 admission 保存並成功綁定 Session 後才由 `Sources.entered` 統一顯示 Fight；取消 callback 只清理同一 private binding 的 WorldBefore／Admission。等待中的 Session 不會再由普通行走排另一個自動遇敵或重複 SOS。已解析原工作仍由 Session 原始 hold／同工作恢復機制處理，不把 Prepared 當成已入戰。

返回經房間全員資源／角色／輔助資料／active44／B4 的完整同交易 CAS；原始全部 Return frame 都 Written，確切 context 與該角色 claim 解除成功後，Repository 才發出私有 ReturnContinuation。Session 另以真正最後 Return Written 將原綁定初始化換成新的 private INIT，產生不可用公開數值建造的 OwnedPveReturnSource。這兩項證據缺一不可。GETTER 不是權限；C1C、Queued 或相同 ID 都不能冒充完整 Written。

`RecoveredOwnedCompanions::pve_return_successor` 驗完整既有 deity／learning／inventory／equipment 圖仍 current，保留原批次及學習歷史。原圖不證明當前戰寵 HP；不把歷史 pet bytes 當作新 pet readset。`reanchor_pve_return` 一次消費原 Admission，綁真 Return token、原 INIT → 新 INIT、full owner、battle generation +2 及完整 DB 圖；不 fresh restore、不重播 S30、不修改原 token、不放寬舊 Current。

Application 發布新的 canonical，原 Entry 改綁新 INIT，保留最後學習 publication 為已於開戰前證明的 Written 歷史，清理已完成 pending。後續 C67、學習、銀行／C24 的原有 typed predecessor 接線繼續使用；尚無 Entry 者在下一次真 callback 才走原 bootstrap 與精確 passive supplier window，避免重入服務。新來源之後只檢新 INIT／完整 current learning 圖／實際 GAME 位置，不要求已退休房間仍有 live claim，也不重新查退休敏感的舊 Written Current。

返回 canonical 與每次 SQL 觀察前後，都比對 captured actual movement service 仍為現任 owner、純 `current_world_location` 仍為同一位置（有 learning 時亦等於其 equipment position）。因此 transfer pending、換 binding 或晚期 observer 改位置不會被 private Return lineage 遮蔽。新戰鬥、斷線或來源退休使舊來源失效。

學習 bootstrap 的實際 supplier 使用剛完成的 observer 結果；自該完整 graph／actual-pose 最後 fence 到交付 material，只作 holder／INIT 純讀。移除原先多餘的第二次 SQL current 查詢，避免該查詢的晚期 observer 改位置後只剩 pointer 比對。

返回後合法行走不會把完整 learning 圖永遠卡在舊座標：實際 WholeBag 最外層 wrapper 在 movement 前捕 predecessor／Admission，保留全部真正 joint COMMIT edge 與最後原始回覆 Written，下一 callback 先逐 edge 接到新的完整 inventory／equipment／位置；這是既有 `advance_companion_successors` 的實際宿主流程。沒有 learning／equipment 圖的 deity-only cohort 不假造該圖：每次完整 observer 先捕當前 actual movement pose，在全部 SQL 兩側純比同一快照，仍保原 private INIT 與全 deity readset。歷史入戰位置不冒充現在位置，也不能讓晚期 observer 的變動被下一次檢查默默採納。

## 原版戰寵快取證據

當前原版 EXE SHA-256：`aaf0fae66e89c4547244304ecd8f4c2755746ffa6c9b9dfe68a0ff3fd2b4cd48`。本輪 REA 由 Windows 分工封存至相同證據根的 `native/`，各分析 session 已關閉。

- `5140C0` 的戰鬥 frame 會經 `4E71E0` 同步角色 normal HP／MP；戰寵 helper 亦寫 normal active44 快取。因此不宣稱原版完全沒有 copyback。
- ordinary dispatcher `468AE0` 的 E3 → `4A2B70`、FB → `4858B0` → `4A52A0`，皆覆寫既有 slot42..44；`519370` battle ingress 也可直接處理 E3。未要求先重送 3B。
- 返回 aggregate 只加入該角色全量保存、完全相同 revision／provenance／metadata／opaque stats 的既有 active44 E3 或 FB 全 body。這是最後一致性刷新，與同一 Return cohort 一起取得 Written；不新增 S30、物件、寵物或重新分類。空 active44 維持精確空／不存在來源。
- E3 metadata key 範圍為 `0x3391..0x3778` 或 `0x5DC1..0x6D60`；FB 為十進位 `28001..32599`。名稱／類型不代替真實 definition 與完整實例。

## 新增回歸來源（全部未執行）

`test_session_state.cpp` 寫入真 Session transport + 真 room COMMIT + 真 learning API 的三種情況：尚無 Entry、已有 Entry、Prepared 後 release；不建造私有 token。檢查 full material 不變、false final fence、消費後重用拒絕、runtime room 退休後新正常世界來源仍可用、首次 bootstrap 精確三次 supplier／已有 Entry 不重播、下一次 inventory predecessor 可捕獲、新 battle generation 退休舊 material。另保留多 frame／原始 Tick hold／外 Session 不可借 token，及 WORLD／未綁房間的 InBattle 收到「movement + action9」時整批拒絕，不能先提交 movement。

未以此覆蓋所有原版 UI／Windows 相容性。完整 C67、實際學習扣書、兩代寵物啟用／返回、多人返回及 socket 故障的聯合執行仍須離開 PHASE1 後驗收；既有相應測試來源不等於已執行通過。
