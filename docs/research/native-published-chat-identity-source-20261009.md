# 原生已發布玩家名字與共用角色身分：第182輪

本輪接續181的完整共用在線姓名觀察，新增兩個、修改六個 C++ 來源檔。實際 CN／TW native chat 的 WorldOwner 可明確供應真正 target→sender visibility Binding；來源把該已發布名字與 matched full64-bit common root／lease核對，並把不可變 Witness 傳入實際 current／delivery 流程。來源紀錄173→174；不是完整私聊、全遊戲玩法或正式掛載完成。新增 opcode／phase binding／完整雙向玩法路徑仍0，分母與百分比未知。

`SharedPublishedChatNameSource` 使用同一 actual identity source、presence、visibility。私人 Binding 必須來自真正 visibility incarnation，source必須等於匹配到的完整 lease；recipient必須是本次真正 sender lease與同一強連線物件，不能只比數字 tuple。原生 actor保持其獨立DWORD數值，不轉成common64 ID。完整角色 root、名字原文、原始target、明確編碼、存檔位置與連線／phase／generation在觀察前後重新核對。Witness持有真正連線、Lookup及同來源 capability；發生重入／失效不發送假成功，也不重播已提交的輸出。

原生名字來源的編碼必須由 actual issuer提供帶revision的 current proof。CN tag0代表原始文字copy，不自動證明CP936；CN tag1成功receiver projection與原文分域，不能當936原名或alias。新 common-published raw分支不以另一個繁簡display converter取代原生projection。TW bit25也不表示CP936／950；原生RawNameState必須保留接收該6F之client當前完整兩個WORD、實際page與issuer revision／Current，不能用sender profile、其他recipient、host ACP或image初始值代替。

台服新原生證據指出，world6F在進入peer store前先比較packed firstDWORD bit25與實際531C10結果。531C10僅在兩個loaded WORD分別為4與2時回1，否則0；相等走469767不改文字。不等走既有52F330／52F170呼叫並可能原地覆寫三個名字欄位。因此181的raw-copy lineage必須限定為consumer當時文字，不能無條件等於最初wire logical29。新增TW readonly query只在真正RawNameState證明無adaptation的分支取名；完整adapted名字／配置／producer與其權限保持OPEN，原生繁簡轉換功能保留。

同一原生ID的新6F會先由4FB460查舊record、呼叫4FC560清理、再4FC1C0重建。名字與角色不能只靠actorID缓存重用。private visibility incarnation/fulllease與原始模型必須一起有效；低12位元只是原生actor namespace，不包含common64 ID或權限。新的Bound Name proof不授予mute／rate／audience／guild／party會員或回覆格式。

CN與TW actual Publication新增可選named_peer只標示真正Owner選擇此已發布共同角色範圍；一旦選擇即強制完整Witness，失敗不能忽略。缺少Binding也不獲得替代名字域的權限：manual／history／不在visibility中的遠端角色／adapted名稱／離線回覆仍須actual原生Owner獨立資格化，不以全域namejoin、NativePromptMarker、TW CUSTOM或猜測ACK替代。TW native body grammar、full5C opaque header／prefix／suffix、實際sender cipher、各native destination、原生權限與收件名單保持既有責任。

本輪也處理visibility current在virtual repository／native text callbacks前後的實際map-entry生命週期：先複製三個外部參數、完整Entry與持有真正transport，再觀察並核對同一私人incarnation／模型／lease，不跨callback保留map iterator或entry pointer。不可變 `ChatActorSnapshot` 保存完整發布模型與真正連線，最末端snapshot-current不呼叫repository或外部Current。Witness保留同一snapshot；CN在最後所有source／recipient觀察後、TW在最後source與peer觀察後及隊列提交前，另用callback-free `registry_current` 核對它。此終點不能取代full current或真實權限。新TW name query與CN原有bubble query分開，原來成功時的bubble／movement／publication行為與凍結CUSTOM保持。

| 保留盤點，本輪未增加 | TW | CN |
|---|---:|---:|
| C2S opcode值 | 156（151通用＋5補充） | 156 |
| S2C紀錄 | 252長度支援值（230fixed＋22variable） | 280phase/opcode entries（account6／world206／battle68） |
| 新opcode／新phase binding | 0／0 | 0／0 |
| 新完整雙向玩法路徑 | 0 | 0 |

TW本輪12spans1522B：新2完整／3bounded共658B，1 expanded known projection127B，另6 retained737B；63 instruction sites、1 data site、125 C++ source sites。這些不是封包數。CN保留3spans166B與3facts，新增native spans／bytes／relations0。181完整原件保持；本輪較精確的FC33F copying boundary不覆寫181 FC340 raw原件。958 endpoint rows／28 groups與30 battle action-selector frontier entries不當全遊戲分母，14 CN receiver contexts／12 qualified及未知兩helpers phase不變。

Fresh before1300 SHA256 `7468461b1c1d42d636de67dd909fb2ac0c666180cd398f4cb9269f37af7640a7`；完整上一輪2318 sealed members已在修改前保存並核對。完整before／source／native originals、當時mutable-source讀取epoch、中間稿、三代理seal及四份raw／final報告分開保存，不重建或偷偷改舊基準。

全部只做靜態來源／PE／指令／檔案證據。未建置、測試、執行native／C++／Lua／codec／Windows API，未讀DB／執行SQL、更新正式服務或部署，也未重試先前停止的155 formatter／capacity／render／glyph研究鏈。actual issuer與raw／adapted receiver state供應、membership／完整header／權限／cipher／loaded sink、entry／Main、其餘全遊戲功能與完整路徑盤點仍待接通。TW／CN／網頁全遊戲、64位元數值、仙幣99999999999、qualified stack99、等級不改、共用表與必要_tw/_cn、原生字體／繁簡轉換、帳號存檔／IME／認證／頭像與凍結功能仍是完整目標，全部來源完成後才集中驗證修復發布。
