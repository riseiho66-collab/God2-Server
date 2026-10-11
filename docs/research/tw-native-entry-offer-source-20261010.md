本輪把實際完整台服2A資料供應者接到既有共用資料庫寫入器，再由世界入口
讀取剛取得的完整資料。新增 SharedTaiwanNativeWorldEntryOfferSource：
供應者必須提供完整原生40位元組 frame、共用角色根資料、實際儲存位置、
正遞增 revision、來源雜湊/記錄與真正 issuer。沒有候選 frame、補零、
不透明欄位推測或僅憑座標放行。

實際 Application Context 現在提供與 native_world_entries reader 同一
物件的 writer；沿用現有 accessor 與連線，不安裝 schema、另開資料庫
或更動一般登入。明確選用 entry_offer 的 StoredSources 必須同時具有
原生選角來源。HostPlan 將 Prepare 接到入口取得 NativeSource 之前；
未選用的舊入口保留原行為，Current 純讀不呼叫 Prepare。

Offer 擁有完整 Scope/Selected/資料與回呼，重查同一選角、完整共用根資料、
位置 revision 與 map。寫入沿用 existing expected-fulltuple CAS 與
Prepared/BeforeWrite/BeforeCommit；parent Current 在 issuer 前後核對
選角/根資料/位置/map，不比較舊2A tuple。BeforeCommit 此時資料庫裡是
staged-next，舊 snapshot 可以保留舊 profile/位置作 CAS 見證，next 才必須
等於本次 Scope。交易提交後不再呼叫 provider、重新載入或重試；稍後來源
失效可抑制發送，不能冒稱已回滾持久寫入。

來源閱讀另發現：舊 vault Entry caught-reentry flag 只在入口回傳後檢查，
issuer 位於 Selected Current 兩次呼叫之間時，單靠 active guard 可能
無法在提交前知道巢狀呼叫已被捕捉。本輪增加精確 invalidate_selection
(sessionID)，由 Application 在 Entry 巢狀拒絕時先撤銷該張登錄，再經
HostPlan 傳遞。下一個 parent Current 因登錄已撤而拒絕，能在 COMMIT
前中止；不影響其他 Session 的選角記錄，不把撤銷說成一次性 admission。

新增 C++檔2、修改8；接線段210→211，新增完整雙向遊戲路徑0。沿用8段、
2308位元組原生證據，新增 opcode/覆蓋0。台服 C2S156、世界 S2C252
（230固定、22可變）、戰鬥 S2C110；83動作23、86選擇值7。陸服 C2S156、
分階段 S2C280（登入6、世界206、戰鬥68）維持。不同階段觀察值不當功能
分母，TW與全遊戲百分比仍未知。

完整不透明2A資源/狀態 producer 與真實 issuer policy 仍須供應；此接線
不等於已取得全部原生資料。一次性/跨G/重播/並行入場權限、回傳後 queue/
場景 publication、Main 明確選用、其餘世界/物品/任務/戰鬥與完整方向/
狀態/變體分母仍 OPEN。保持台服優先、共用核心與既定台陸網頁支援。

只做來源修改、靜態來源閱讀與檔案雜湊記帳，未建置、測試、執行原生程式/
codec/runtime/DB/SQL、遷移或部署。保留帳號存檔、聊天/IME/認證/頭像、
原生字體、繁簡轉換、等級與數值擴充方向。目標 active，台服全部實際來源
路徑達100%後才停止。為維持 Desktop/God2 低於50GB，新完整帳本與計畫
原件另存 task-owned 外部封存位置，逐一以絕對路徑/大小/雜湊記錄；沒有
移動、刪除或改寫任何已封存歷史原件，外部原件也不是只存 receipt。
