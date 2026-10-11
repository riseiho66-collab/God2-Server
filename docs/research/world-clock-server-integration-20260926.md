# 世界時間封包實装（2026-09-26）

## 原生與自訂邊界

原生證據依 current-world-clock-20260920.md 與 test_current_world_clock.py：S2C logical1A固定4bytes，三個unsigned BYTE無標準時間欄位正規化限制。C35F0記錄WINMM timeGetTime於role source+44AC，6×(3600h+60m+s)於+44B0。原生UI使用DWORD六倍差值、float32縮放及截斷；不是伺服端任意乘法近似。

CUSTOM-0042只定義跨玩家共同UTC epoch-zero錨點：Unix秒取非負mod14400，再分為h/m/s。原生六倍時間形成四小時一個遊戲日；沒有原服曆法、天氣、每日任務或獎勵重置的權威。INT64_MIN/MAX先取餘數，避免epoch乘法溢位。

## 實際服務端路由

Application初次完成owned player/companion/journal恢復後送1A並登記weak session。50ms既有排程使用steady clock每60秒重送當前system clock相位。僅completed native tail及owned restoration已完成的InWorld或保留CharacterSelected連線可以更新；pending scene transfer與InBattle不送。斷線移除追蹤，weak pointer失效亦移除。

第一次測試揭露：native bootstrap故意保留CharacterSelected，單用InWorld使定期更新缺失。已按完成tail及owned恢復的條件修正，沒有改動全域世界狀態。TCP測試亦修正等待方式：先等待定期事件，再使用原本較短的逐frame deadline；不能只調socket timeout而被helper覆寫。

Config預設disabled；enabled要求recovered_world_entry，sync_seconds整數5..300。正式設定60秒，隱藏測試5秒。無DB migration、玩家時間存檔或自動任務授予。

## 驗證與正式套用

- C++ codec89,763項檢查通過；原生BYTE全域與epoch有號邊界。
- compiled C++ CLI11個epoch經原生writer/UI算術消費通過，包括INT64_MIN/MAX與負epoch；CTest world_clock_server_native。
- own-server TCP6/6通過，含首次1A、定期更新、伺服端重啟後新相位及原owned companion/journal保留。
- 隱藏原客戶端 private-world-clock-20260926-02 accepted=true；實際role clock timestamp從495853027更新到495858031，base50160到50190。崑崙4/3移動與15slot owned journal仍通過，客戶端存活。
- 第一輪 private-world-clock-20260926-01失敗保留作診斷證據，不計通過。
- 全程使用God2Lab內部桌面，輸入桌面Default不變；無截圖、無客戶端記憶體寫入。來源DB與正式客戶端雜湊不變。
- world-clock-20260926-01已套用，port2592監聽。候選與實測EXE雜湊一致；verification.json existing_tables_changed=[]、other_config_preserved=true、client_unchanged=true。保留4帳號、3角色、崑崙出生設定及原生位置限制。

驗證範圍是實際原生時間資料consumer及週期更新；未逐像素核對UI時鐘文字，也未恢復原服日曆／時間相關任務規則。整體可玩重建規劃估計仍約11%，不是全封包完成率。

## 本輪下一個原生互動合約

天尊基礎知識MultiMessage1434固定28bytes 7A mode4，七選項、兩頁及C2S85已按compiled-menu.json核對原生consumer/producer。完整NPC位置、事件路由及實際UI尚未接通，不能算已恢復NPC或任務。原生choice7會發出，但這個menu只有0..6有效；服務端須拒絕7。只允許count0/noformat固定分支，不能因transport上限放寬tail。
