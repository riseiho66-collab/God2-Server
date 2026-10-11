# 第184輪：共用原生連線來源與實際聊天收件路徑

本輪新增 `SharedNativeWorldTransports.h/.cpp`，修改既有10個 C++來源，共12個。共用世界的完整角色 Lease 現在可對應實際台服 Session 或陸服 SharedCredentialConnection；登記接在兩版真正的入場完成處，聊天收件路徑則明確選用同一個來源。來源紀錄由175增至176，新增 opcode、階段綁定及完整雙向玩法路徑均為0。全遊戲分母、已完成完整路徑數與百分比仍未知。

連線登記持有同一個 SharedWorldPresence，Token 保存完整 Lease、私有來源身分、單調世代及弱連線。Snapshot 僅在一次查找與發送期間持有強連線。不得用 native actor DWORD 或遮罩後的 ID 當共用64位角色身分；已有 slot 不會自動覆蓋。查找與 current 實際讀取 ready root/population，核對同一私有 Token 與真正連線；台服另保留 phase/battle generation，陸服沒有捏造戰鬥世代。

台服同步入場在真正 entered 成功後登記；非同步入場在真正 scene 完成、撤銷 pending entry 身分後登記。陸服在 incoming held output 及全部 outward queue 成功後登記，之後才處理 gameplay remainder。登記回傳的 Token 在 observer 期間有獨立保留，回呼清理不能令已釋放的入場狀態復活。斷線與失敗先按原 Token 撤銷登記，再清理 visibility/presence；不能依 session ID 刪除後繼世代。Token 保留弱連線，避免 cleanup cycle。

兩版聊天的 Delivery 明確設 `use_common_transport` 才使用登記來源。原收件 Lease、頻道、權限、收件範圍、完整 native header/body、codepage、文字狀態與 sender cipher 仍由真實 WorldOwner 提供。若來源已提供活連線，必須與登記連線的型別及指標一致。實際連線型別選擇原有 TW/CN serializer；不能把同號 opcode 當跨版相同格式。

每次 publication/recipient qualification 保留強 Snapshot，observer 之後使用無 repository／外部回呼的 registry_current 核對同一私有來源世代、弱強連線指標及原生 tuple。新增路徑另在最後核對 sender 的本次 Slot／真實連線／phase；這些 endpoint 不替代完整 common ready、存檔位置與遊戲權限來源。原未選用此來源的路径保持原處理方式。Observer 必須純讀、不 yield、不 pump、不發送或保存借用參數；沒有跨連線原子 fanout 或回滾承諾。

子代理補充台服 C2S6E 觀戰入口的限定原生證據：19 spans／1896 bytes，其中7個新 bounded spans／443 bytes、1個既有 caller 擴展／540 bytes、11個保留 spans／913 bytes，新增完整函式0。首兩 mode1 caller 的查名使用角色 pool namespace，但 lookup 未檢查成功，不能據此認定 raw DWORD 一定指向存在或可觀戰角色。第三 UI 清單及 external menu 的原目標發行與 battle linkage 仍未追完。mode2 的 +12018 是 0x204／0x205 輸入事件 latch，不能當作戰鬥權限；context0 不能當作角色0或 universal exit。原6E、mode2範圍及已查過的 wrapper 保留舊計數，未冒算新封包。

| 盤點 | TW | CN |
|---|---:|---:|
| C2S opcode |156（151 generic＋5 supplemental）|156（完整 phase 尚待釐清）|
| S2C 盤點口徑 |252 length 支援：230 fixed＋22 variable；world 非 default206|280 phase/opcode entries：account6＋world206＋battle68|
| 本輪新增 opcode／phase binding |0／0|0／0|
| 本輪新增完整雙向玩法路徑 |0|0|

TW battle83 actions23／battle86 selectors7，共30個追查前沿項目，不是所有變體。958 endpoint rows／28 source groups 不等於全遊戲路徑分母。TW reviewed scoped42／parser63 的66.7%只適用該範圍，不能作全遊戲完成度。

實際 Main／世界 plan 選用、完整 entry/appearance issuers、文字狀態與 adapted names、權限與全部玩法仍需接入。TW/CN/web共用64位數值、仙幣精確上限99999999999、合格堆疊99、等級不改及原生字體／繁簡轉換要求均保留。

本輪只讀來源、釘定原始檔並保存修改；沒有建置、測試、native/C++/Lua/API/codec 執行、資料庫/SQL 存取或部署。fresh before1313及前輪2384封存成員保留；原始與中間／最終來源 epoch 分開。CN 最初短暫修改的完整中間檔未另存，明列缺失，不重建冒稱原件。未重試第155輪 formatter/capacity/render/glyph chain，也未深入52F330／52F170。帳號、存檔、IME、認證、頭像、客戶端及其他凍結功能保留。目標保持 active，全部來源接通後再集中建置、驗證、修復及發布。
