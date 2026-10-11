# 第186輪：原生觀戰請求來源與混合分派串接

本輪新增3個、修改9個 C++來源，累計來源成果177→178。台服原生 C2S6E 的完整8B body 現在經同一世界主機的已登記連線、typed source、混合 record handlers、WorldRecordSource 與 Application 選用的封包入口串接。真正的目標發行者、戰鬥資格、完整原生回覆及 Main 選用供應者仍未完成；本輪新增 opcode／phase binding／完整雙向玩法路徑均為0，全遊戲分母與百分比未知。

SharedTaiwanNativeSpectatorSource 保留真正 sender Session 強引用、完整 common ready Lease 與私有 registry Token，核對實際 character root、saved position、phase 與 battle generation。每次請求完整拷貝原8B，mode1 raw DWORD 與三個不明位元組不改寫；mode2 的原生輸入 latch 不能當成戰鬥權限。真正 WorldOwner 的 current 與 execute 為必要供應者，execute 每次只呼叫一次。實際回傳 Result 明確指定 post phase／battle generation；來源重新讀取當前 root／position／連線並核對，允許真正權威操作造成合法世界／戰鬥轉換，不用操作前 Snapshot 鎖死合法 post state。失敗使本來源持有的 exact slot 失效，不重做已提交前綴，也不代替 common cleanup。

SharedNativeWorldTransports 新增 callback／repository-free 的 registry_current(Token)，只核對相同私有登記 incarnation、weak endpoint 與原生 Session tuple；完整 current(Token) 及真正 post phase／battle owner 檢查仍不可省略。原有 Snapshot overload 不改，避免把此新 overload 說成額外戰鬥授權。

SharedTaiwanNativeRecordHandlerSource 新 overload 明確接收 chat、spectator 及 remaining 三個實際 binding。它在任何處理器效果之前拷貝整批 records，準備所有 chat／spectator request 及 remaining 最大連續區間，然後依原順序累積真正 encrypted reply。舊 chat＋remaining overload 保留原來的6E處理歸屬。失敗與清理嘗試每個實際 child，即使先前 child 丟出例外也不省略後續清理；沒有新增預設 ACK 或任意成功回覆。

RecordSources::with_native_chat_and_spectator 從同一實際 Application Context 取得 presence／transports，建立上述來源與混合分派。spectator6e 由實際 binding 傳經 WorldRecordSource、plan wrapper，最後只在 Application 真正 install_records 的選用分支送到 Session parser；舊 aggregate 預設 false。此旗標只表示 typed framing 可用，不代表目標、權限或整條玩法已完成。Main 尚未選用完整 native plan。

RecoveredSpectatorTargetsD0 只讀取已證實台服 logical7／body6：unsigned slot、opaque body1、兩個 little-endian WORD。FFFF 保留0000FFFF，不補成FFFFFFFF；沒有 encode、猜測目標映射或原生範圍拒絕。服務端 S2C 發行者與 recipient UI／entry epoch／update／reset lineage 仍待接入。

陸服子代理獨立從固定雜湊的 CN 原圖追查 D0／CD 的 world table、consumer、原生 UI caller 與 C2S6E producer，未以台服同 opcode 推定陸服格式。world D0 寫入兩個 WORD 零擴展的目標陣列，CD 另外更新 flags／metadata／文字，不能把 CD 狀態更新當成目標重新發行。CN C2S6E logical9 與 CN S2C6E logical5 分開；原生 battle table 的 CD／D0／6E 在此限定索引都走 default consume，不代表全遊戲所有 caller 已追完。真正 target namespace、common64身分映射及當前戰鬥資格仍未知。

CN 本輪14個 spans／904B：3個新完整函式426B（CD310B、D069B、C2S6E47B）、3個新限定區339B、8個保留區139B；157 instruction sites、10個 table cells、46個 primary source sites。完整原始輸入12件／50,897,610B：固定 CN PE、完整 metadata 與10份選定 decompiled C 原件。5個 direct E8 位元組候選只限定證實選中的 UI caller，不宣稱全部間接呼叫已追完。精確原件、範圍與計數見本輪 cn-spectator-native-frontier/findings.json。

| 盤點 | TW | CN |
|---|---:|---:|
| C2S opcode |156（151 generic＋5 supplemental）|156，完整 phase 尚待釐清|
| S2C 盤點口徑 |252 length 支援：230 fixed＋22 variable；world 非 default206|280 phase/opcode entries：account6＋world206＋battle68|
| 本輪新增 opcode／phase binding |0／0|0／0|
| 本輪新增完整雙向玩法路徑 |0|0|

TW battle83 actions23／battle86 selectors7，共30個追查前沿項目；958 endpoint rows／28 source groups 均不能作全遊戲路徑分母。仍缺完整 entry／appearance／audience／membership／rights／native header/body／codepage／cipher／reply suppliers、Main 與其餘全遊戲路徑。

已唯讀保存網頁端最新 WEB_SERVER_INTEGRATION.md 原件。其 CN C56 logical7 的 opaque 與 padding 使用0為 browser policy，不作原生初始化、權限或相容性驗收；未修改網頁客戶端，也未另建遊戲核心或資料庫。

大型 CN 原件保存及來源修改後，唯讀統計整個 God2 為42,216,918,928位元組／270,538檔，沒有讀取失敗，低於50,000,000,000位元組限制。此為 final accounting 之前的完整目錄 file-length 盤點，不追蹤 symlink／junction，也未恢復歷史客戶端或建置樹。

本輪 fresh before1325、前輪2286封存成員、完整 before／final source、三子代理原件與 raw／final reports 分別保留。未建置、測試、native／C++／Lua／API／codec 執行、DB／SQL存取或部署；未重試155 formatter／capacity／render／glyph chain，也未深入52F330／52F170。帳號、存檔、聊天、IME、認證、頭像、客戶端、原生字體與繁簡轉換保留。TW／CN／web共用64位數值、仙幣99999999999、合格堆疊99、等級不改與共用資料表要求保持完整範圍。目標保持 active，全部來源串接後才集中驗證、修復及發布。
