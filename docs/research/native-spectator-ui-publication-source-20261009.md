# 第187輪：原生觀戰發送紀錄與同一世界主機串接

本輪新增3個、修改8個 C++來源，累計來源成果178→179。同一世界主機的真正收件連線接入完整供應的 CD／D0、台陸各自 held queue 與本地釋放發送紀錄，再交給台服 typed6E 的資料範圍。真正視窗／事件／世代發行者、目標身分、戰鬥權限、完整回覆及 Main 仍未完成；新增 opcode／phase binding／完整雙向玩法路徑均為0，全遊戲分母與百分比未知。

SharedNativeSpectatorPublication 預先拷貝完整 Event、分割所有 CD65／D07 records，準備不可變 pending／released／failed history，完成容量與原生收件版本核對後才進入真正發送。所有不明欄位保留原位元組，slot1..50 明列為本來源要求供應者使用的輸出範圍，不冒稱原生 consumer 有此拒絕檢查。ui_epoch／previous_revision／revision 是真正供應者必要的外部來源資料，不是從未知原生欄位推導。首次 previous_revision0 的完整 baseline、每次更新、替換或 retire 均仍須真正 WorldOwner 資格。

台服呼叫實際 Session::send_common_world_records_with_publication；陸服呼叫實際 SharedCredentialConnection::send_world_batch_with_publication→CnTransportSession::send_batch_with_publication。兩個真正 queue 的 approval 均以 asio::post 進入 game executor，不猜測 inline approval。BeforeQueue／BeforeRelease／AfterRelease／Observe 讀取真正角色、位置與連線，前後核對同一次觀察；跨非同步階段可接受真正權威批准的位置變化。Published history 只在 true local release completion 後保存，不能視為客戶端已收到或認可。

持久 registry／history／Observation 對 receiver／WorldOwner 採弱引用，pending callbacks 暫時持有強引用；不把主機、來源及權威物件接成永久循環。false completion 使用預備的原始不可變 view，不在此失敗效果後重新配置。retire／remove 只清理 exact private entry／epoch；pending retire後的 true completion 仍保留已釋放前綴，不重新啟用舊視窗，也不清理共用 Lease 或後繼 Token。私有 absence_generation 耗盡時關閉本來源而不 wrap，已釋放前綴及 true completion 的事實保持。

current(Observation) 表示保存的狀態觀察仍準確；Missing／Retired／Unavailable 等負狀態可為準確事實，不能當成 UI 或戰鬥資格。Published／Pending 仍向真正 weak WorldOwner 重新 Observe。台服發送限於既有 held API 支援的 InWorld，但唯讀觀察可在真正 InBattle 連線下成立，避免用世界發送限制阻擋合法模式2戰鬥操作。

SharedWorldHost 新增一次性的實際 publication 安裝入口，要求供應者的 presence／transports 與本主機完全相同。它不自動建立視窗、資料、世代或預設發送者。SharedNativeWorldTransports 的 same_registration 比較保存的私有 Token 物件及目前登記項，不能用相同 Lease、帳號或低位 ID 代替；這項比較沒有提供遊戲權限。

SharedTaiwanNativeSpectatorSource 的 Scope 新增可選 native_ui。未選用為 nullopt；已選用時保留 Missing／Pending／Published／Retired／Unavailable 的實際差別。來源使用原先保存的 Token 觀察同一收件者，核對完整 Lease 與私有登記，並在真正 current observer 前後重新讀取完整角色、位置、階段及 battle generation。合法 execute 後取得新的實際資料範圍，不用舊世界階段鎖死合法轉換。發送歷史不能代替目標身分、入場資格或戰鬥權限。

with_native_chat_spectator_and_publication 從實際 Application Context 取得同一 presence／transports，安裝並取回完全相同的 publication，將它交給觀戰來源，再使用原來的 chat／spectator／remaining 混合順序。聊天來源及其規則沒有額外 publication 參數。此 factory 尚不代表 Main 已選用或功能已啟用。

CnSpectatorTargetsD0 是獨立陸服證據的只讀 logical7／body6 view：slot 為 unsigned BYTE，body1 保留 opaque，body2／4 為 little-endian WORD。FFFF 保持0000FFFF，不補成FFFFFFFF；沒有 encode、原生 slot 上限拒絕或共用64位身分映射。

台服限定原生追查保存7個 spans／414B：3個新限定區108B、1個先前已讀 helper 的擴展完整範圍128B，以及3個保留區178B。完整原件為固定雜湊149c的3174400B mapped image；103 instruction sites、2個 data sites、17個 source sites。新 opcode、phase binding、完整雙向玩法路徑均為0。

world F7→69DD0→78EF0 呼叫77850後把 UI89E3C 設為2；F7 既有 logical1025 長度不重新計作新增。先前觀戰 UI 呼叫區要求模式1，因此模式2重設不能證明模式1視窗的目前世代。第二個選定 caller81B91 位於同一 UI owner 的批次操作區；未追完其整個函式及上游階段，也沒有恢復網路視窗世代。

完整78C40關閉 helper 先核對視窗 handle／flag，再按模式1或2送出 A3／CB 的1B body。PUSH ECX 保存 incoming this 指標，隨後 PUSH ESI；兩處 LEA[ESP+7] 均指向保存 ECX 的最高位元組。此 body 不能当成 nonce、revision、視窗世代、固定0或完全未初始化的位元組。現有184／185／186紀錄保留原樣，本輪明列這項細化。

| 盤點 | TW | CN |
|---|---:|---:|
| C2S opcode |156（151 generic＋5 supplemental）|156，完整 phase 待釐清|
| S2C 盤點口徑 |252 length 支援：230 fixed＋22 variable；world 非 default206|280 phase/opcode entries：account6＋world206＋battle68|
| 本輪新增 opcode／phase binding |0／0|0／0|
| 本輪新增完整雙向玩法路徑 |0|0|

TW battle83 actions23／battle86 selectors7，共30個追查前沿項；958 endpoint rows／28 source groups 不能作全遊戲路徑分母。全遊戲完整封包數、完整雙向路徑數與百分比仍為未知。

仍缺真正的視窗／事件／世代發行者、目標命名空間與共用64位身分映射、戰鬥 membership／rights／execute、完整 native entry／appearance／audience／header／body／codepage／cipher／reply 供應者、Main選用及其餘全遊戲路徑。Web C56 的實際 opaque 用法與 handler／權限／耗費仍未完成。共用64位儲存／線路／物件／飄字、合格堆疊99及正式網頁 WSS／TLS／hosting 仍在完整目標範圍。

未建置、測試、native／C++／Lua／API／codec 執行、DB／SQL存取或部署；未重試155 formatter／capacity／render／glyph chain，也未深入52F330／52F170。保留帳號、存檔、聊天、IME、認證、頭像、客戶端、原生字體與繁簡轉換。目標保持 active，全部來源串接後才集中驗證、修復與發布。

唯讀盤點整個 God2 為42,387,784,516位元組／273090檔，沒有讀取失敗，低於50,000,000,000位元組限制。此為 final accounting 前的目錄 file-length 盤點，不追蹤 symlink／junction，未恢復歷史客戶端或建置樹。fresh before1333、前輪2377封存成員及所有初版／修補前／final來源原件保留，三代理原件、原始與最終報告分開保存。
