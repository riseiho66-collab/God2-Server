# 第189輪：台陸原生觀戰關閉請求與精確目標退休

本輪新增2個、修改17個 C++來源檔，共19檔。台服與陸服各自的 A3／CB logical2 關閉請求接入獨立、明確選用的 CloseOwner 與原有有序回覆流程；共用目標來源新增兩階段 UI 退休票據。這是來源與呼叫鏈串接，真正 native window／事件發行者、權威操作、battle membership／rights、完整回覆與Main供應者仍缺，不能宣稱完整觀戰或全遊戲打通。靜態記帳後來源段數180→181；新opcode、phase binding、完整雙向玩法路徑均為0，全遊戲分母與百分比null。

## 原生格式与限制

兩份只讀 view 是 RecoveredSpectatorClose 與 CnSpectatorClose；Request 保存原始 opcode 與 opaque BYTE，logical_size=2，decode只接 A3／CB 和完整原body，沒有encode、固定0、ACK、視窗世代或權限推導。台服149c的完整00478C40 helper128B是第187輪保留證據，不重計為新恢復。陸服582f的獨立完整004A1DA0..004A1E16 helper118B先檢 owner+1C8534 signedWORD非負與視窗record flag20；本地關閉0044E7F0後，mode1送A3、mode2送CB，均經真正00481440發送body1。

陸服prologue PUSH EBP／MOV EBP,ESP／PUSH ECX後的LEA[EBP-1]指向saved incoming ECX最高BYTE。因此這個body是原保存物件指標的一個位元組；不是nonce、epoch、固定0或完全未寫入的資料。004A269B選定caller要求inputflags bit2、selected signedWORD1C8536>=0及selected record flag10；004A26EA caller要求bit1、相同handle非負、0044F070 result非零及signed action36。這些是局部UI前提，不能當服務端目標來源、戰鬥資格或退出確認。

本輪限定6個spans共419B：CN新完整helper118B、4個新限定區173B、TW保留完整helper128B。120 instruction sites、1 data site、41 primary source sites與36 C++ sites不是封包或完整玩法數。完整原件6份、53,995,559B：TW／CN原圖2份50,716,160B、metadata1與primary C3。未擴追formatter、glyph、155停止鏈路或52F330／52F170，沒有執行原生程式。

## 台服完整來源呼叫鏈

RecoveredWorldRecords新增typed Close Request variant及獨立spectator_close開關，decode／parse_frame末尾參數預設false，原本呼叫不會暗開。A3與CB各自只有完整logical2讀入，整批拷貝／形狀檢查先於任何child效果；開啟6E格式本身不開啟close。

SharedTaiwanNativeRecordHandlerSource保留chat／6E／close／remaining的原始順序。close_dispatch非空時才建立close segment；相鄰非chat／6E／close紀錄仍交真正remaining owner，沒有默默跳過未知紀錄。回覆仍為原先完整encrypted frames，累積於批次輸出，不能搶先發送；no_reply須是實際handler明確決定，沒有自創成功ACK。

相同Context的publication factory末尾新增可選CloseOwner，交給原spectator Source。OtherBinding→WorldRecordSource Binding→Plan wrapper→Application install_records→Session RecoveredCharacterHandlers→真正parse_frame傳递獨立close旗標，只有已安裝的明確來源供應可開啟，未改Main預設選用。舊chat、6E及其它parser flag保留。

## 台陸實際CloseOwner

兩版既有spectator Source各保留原WorldOwner的6E current／execute API，增加獨立CloseOwner current／execute及末尾可選create參數。CloseOwner只有配合相同來源的真正publication才可選用；原6E WorldOwner仍mandatory，本輪不新增另一個競爭close-only來源。TW Binding末尾close_dispatch、CN Binding末尾close_ingress未選用時為空。

操作內保留typed variant的實際原始請求。Close snapshot有完整角色、位置、原連線Token与實際UI，但target=nullopt，不用context0或第一項D0 binding假造關閉目標。真正CloseOwner獨立批准native window、opaque欄位、phase／membership／rights與完整回覆；execute僅一次，來源不自動退出戰鬥或清理核心資料。TW重讀真正post phase／battle generation，CN沒有虛構TW計數器。

CN SharedWorldGameplay::Sources新增明確CloseOwner，initialize取得實際child close_ingress，整批split先精確decode logical2再按原pump順序dispatch。6E、Close共用原child的busy／reentry fence、第一次ready保存Token、持久弱receiver與操作強Pending。回覆經既有held logical queue與真正native framing／encryption；approval posted、可能inline false wrapper completion、late true local release及once continuation等前輪行為保留，取消不重試已釋放前綴。Gameplay既有失敗／終端／destructor清理同一child，沒有新的共同presence或後繼Token刪除。

## 精確UI退休票據

SharedNativeSpectatorTargets的Entry保留發行時的不可變publication觀察。retirement_for_ui(actualUI)以實際來源的私有UI／Token proof取得exact Entry的UiRetirement票據；沒有repo／Current／native API觀察，也沒有context0、原生世代或遊戲權限推導。真正WindowOwner可以在持有實際UI時先保存ticket，完成自己的實際操作後呼叫retire_for_ui(ticket)。

退休比較此來源、原私有Entry identity、完整原Token／Lease及保存的發行lineage，僅標記原Entry retired。即使common lease或publication已釋放，也不能讓舊ticket退休同session、同UIepoch甚至同UI observation後來替換的新Entry。來源沒有tombstone累積，也不修改既有Budgets或create契約。持久UI觀察仍只弱持實際receiver／WorldOwner，不新增Host持有cycle。這項API未自動放到CloseSource作遊戲決策；實際CloseOwner與核心發行者仍必須實作及選入。

capture目前要求Entry原發行UI與供應的UI仍為publication.same，不能用相同epoch代替。如果後續CD／D0更新publication revision，而真正issuer尚未重新issue Target Entry，capture返回null；UI更新與目標重新發行的實際同步仍是必要供應者缺口，沒有擅自放寬私有能力比較或宣稱所有後續view都可捕捉。

## 盤點與接續

網頁客戶端的 C35 陣形、primary skills／F1..F5 item shortcuts、checkpoint v9 與契約四份完整原件已按雜湊保存，並向使用者授權的原網頁任務回覆來源交接 ACK。這些是客戶端的來源交接，不是本服務端獨立原生證據或驗收。实际 src/cn/net、world、battle、protocol 的 h／cpp 搜尋與現讀顯示既有 S86/5 gate 及 scalar projection，尚未找到真正 C2S35 typed request／handler；SharedWorldGameplay 尚未派送35。接續優先追固定582f的真正 producer、logical17 raw view 與實際輸入，再接真正 battle／actor ownership、82 context／86 grant、primary-secondary、targets、formation、learned skill／MP／range、item slot/count、一次結算與完整回覆。C56世界技能、S2C world35與TW CUSTOM PK保持分開，網頁 padding0不能用作權限證據。原讀取 CP950 stdout 失敗所留下的完整 original-00.md 亦保留，四份第二epoch原件與實際來源搜尋範圍另記 web-peer。

| 盤點 | TW | CN |
|---|---:|---:|
| C2S已盤點opcode |156：151 generic＋5 supplemental|156；完整phase未釐清|
| 本輪新增typed parser opcode |2：A3／CB，獨立預設false|2個Close分派值，屬已知opcode|
| S2C盤點口徑 |252支援長度：230 fixed＋22 variable；world非default206|280 phase/opcode entries：account6＋world206＋battle68|
| 本輪新增opcode／phase／完整雙向玩法 |0／0／0|0／0／0|

TW世界parser範圍63→65；既有reviewed分支42不因新typed framing自動增加，局部42／65≈64.6%。A3／CB加入明確未完成玩法分類，既有11個紀錄保持，現13個。958 endpoint rows／28 source groups、battle83 actions23與battle86 selectors7均不是全遊戲分母，完整封包總數與完成度保持未知。

下一步是原生視窗／UI事件與真正權威關閉、發行／目標核心操作、battle membership／rights／execute／完整回覆、其他mode1 DWORD命名空間、entry／appearance／audience／header／body／codepage／cipher供應者、Main正式選用、Web C56 handler／opaque／目標／耗費及其餘全遊戲路徑。完整TW-CN-web與共用64位storage／wire／object／飄字、仙幣上限99999999999、合格stack99、共用表及WSS／TLS／hosting範圍不縮減，等級不改。

只有靜態來源修改、原生有界讀取及file/hash記帳；沒有build、test、native／C++／Lua／API／codec執行、DB／SQL存取、迁移、重啟或部署。帳號、存檔、聊天、IME、認證、頭像、原生字體、繁簡轉換與客戶端／凍結功能保留。fresh before1351與前輪2437封存成員完整保留；各代理before／initial／refinement／current／actual-inputs／context，以及四原始與四最終報告分開保存。本輪整個God2 file-length容量記錄另存policy與continuation，低於50,000,000,000B，不恢復整個歷史客戶端或建置樹。目標保持active，全部來源串接後才集中建置驗證、修復與發布。
