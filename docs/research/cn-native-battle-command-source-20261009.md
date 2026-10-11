# 第190輪：陸服原生戰鬥35與實際遊戲輸入來源

新增3個、修改2個C++來源檔，共5檔。獨立CN582f原生C2S35的logical17／body16只讀Request，接入SharedWorldGameplay既有完整批次複製、原順序pump／dispatch，再交明確選用的SharedNativeBattleCommandSource及必要真正WorldOwner。來源有完整角色／位置／原私有Token觀察、單次execute與實際native held logical replies。真正battle／actor／context／grant／rules／settlement／reply供應者及Main仍未完成，不能宣稱戰鬥玩法打通。靜態來源記帳181→182，新opcode／phase binding／完整双向玩法均0，全遊戲分母與百分比未知。

## 獨立原生證據

CN God2_opt.exe SHA582f269535f86e95fcd77946821adf79a30d1bd33f21d566cf48c36fd221b3c8，完整PE47,541,760B。連同metadata與三份primary C，完整原件5份50,819,162B；兩份primary新選定，5471F0完整原件是188輪保留來源，這輪只解讀兩個新的限定caller區，不重計為新完整函式。

機器碼54FFC0..5504B4共1268B，包含完整producer與terminal ret16；primary標頭329B是分段metadata，不能當整個演算法邊界。5504B4是九個DWORD的switch table，36B／9cells，與instruction區分開。三個send sites550277／5502CF／55032C都透過481440傳35、LEA[EBP-14]與body16。另完整54A9A0..54AA9D item caller253B，formation caller45B、primary3 caller30B。總計4spans1596B：兩個新完整區1521B、兩個限定區75B。415 instruction sites、49 primary C sites、25 C++ sites不等於封包或玩法數。

| body offset | logical offset | 寬度 | 來源限定 |
|---|---|---|---|
|0|1|BYTE|實際第二argument低BYTE的actor position，不是共用角色ID|
|1|2|BYTE|實際command kind，部分多筆技能續送帶80 bit|
|2|3|BYTE|先初始化0，實際A970F8／A970FC旗標可改1；不提供服務端授權|
|3|4|BYTE|選定producer沒有直接scalar write；helper／超範圍position的alias尚未追回，不能聲稱所有路徑未写|
|4|5|DWORD|raw target field，不是所有分支都為mask|
|8|9|DWORD|實際owner+3C複製；真正issuer與語義命名空間尚缺|
|12|13|DWORD|分支操作數，沒有共同的zero初始化|

普通分支將position／14決定halfWORD、position%14決定bit；部分skill3／17由55D770 helper供應，此helper仍OPEN。skill-kind2且非WORD+3E=FF5時，target field改存owner+4A4選定BYTE與indexed owner+4A9 BYTE，形成兩個zero-extended WORD；不可用通用mask規則解釋。多目標skill loops會在非最後send設定kind80續送，最後恢復kind；多筆35本身不構成重複／重播證據。

type4 operand是3-owner+A97148；限定caller以owner+46C-10寫A97148，再使用549750實際回傳actor BYTE。type5／12 operand為signed BYTE A9713C高位移24，OR unsigned WORD A9713A，中間8bits為0；type7讀A8CBFC DWORD，type8讀owner+488==0。其他table／default分支可能不寫operand，Request不可補0。完整item caller透過4C9AE0實際inventory getter，從29向requested signed slot尋找正count且WORD+4匹配的項目，再傳type5；getter、現存所有權／耗費與合法item use仍未恢復。

producer的局部flags、actor／count範圍與kind0B例外不是伺服器權限。所有native variant都應由真正Owner按實際条件處理，沒有在parser硬套每個kind都必須相同grant／mask／operand規則。549A70 selected skill、549750 actor selector、55D770 target helper、4C9AE0 inventory reader、owner+3C issuer與481440內部未在本輪擴追。

## 實際來源串接

CnBattleCommand35::Request私有擁有完整17-byte array，decode只要求opcode35及exact length17；raw actor／kind／source／padding／target field／context／operand都保留。raw_target_field命名避免宣稱通用mask。沒有encode、預設0、權限判斷、共同角色ID轉換或成功ACK。TW C35與CUSTOM PK、CN C56世界技能、S2C WORLD35技能資料方向／階段保持分開。

SharedWorldGameplay::Sources末尾新增可選battle_commands與非零budgets。compose要求同一presence的真正world_transports；initialize建立實際child Binding。第一筆真正ready35才lazy保存原私有Token，初始1C尚未ready時不查找或自造registration。未供應Owner時不開35；普通Main未選用。所有known aggregate先完成shape檢查並複製，各35按原pump順序dispatch，不跳過未知紀錄、不自造相同opcode回覆。既有Reservation::gameplay回傳同一Sources，SharedWorldPreparation原本直接傳到compose；沒有另建競爭服務或繞過初始readiness。

child永久receiver為弱引用，每次Pending強持實際connection，先取得強引用再做repository／Current觀察。完整Lease、角色身分、saved position與原私有registry Token在真正Owner.current前後重新讀取；BeforeExecute／AfterExecute／BeforeQueue／BeforeRelease／AfterRelease都獨立資格檢查。Scope不自造battle clock、phase、82 context issuer、86 grant、核心actor incarnation或TW計數器。

必要WorldOwner仍必須供應真正native battle／actor ownership、適用variant的context與grant、primary-secondary、targets／formation、learned skills／MP／range、held item slot/count、semantic duplicate／continuation、一次結算與完整native reply/profile。execute每次已資格請求僅一次；只能傳回明確的完整有序logical records，或handler明確no_reply。缺失／失敗終止，不以空handler或generic success補齊。這輪只有到實際供應者的呼叫來源，未實作這些權威規則，不新增資料庫battle資料或假設數值。

完整logical vector在queue前deep-copy，透過同一Connection.send_world_batch_with_publication與既有CN framing／encryption；approval在game executor，BeforeRelease資格成立才放行。wrapper可能inline false完成，來源在Stage结束後處理；取消後晚到true仍保存locally_released前綴事實，不重試execute、不回滾已釋放的位元組、不再次完成continuation。此本地易失事實不等於持久化、socket delivery或客戶端收到，真正committed／released prefix recovery仍缺。

outer busy重入先invalidate此child；failure／terminal03／destructor沿既有流程release此child。child只清理自身保存Token／Pending，不移除共同presence或後繼連線；成功非terminal batch保留child供下次合法輸入。共同cleanup仍由既有Gameplay／Ready負責，凍結功能未改。

## 盤點、交接與缺口

| 盤點 | TW | CN |
|---|---:|---:|
|已知C2S opcode|156：151 generic＋5 supplemental|156；完整phase待釐清|
|S2C口徑|252長度支援：230 fixed＋22 variable；world非default206|280 phase/opcode entries：account6＋world206＋battle68|
|本輪新增opcode／phase／完整雙向玩法|0／0／0|0／0／0|

TW parser65、reviewed42、18 reviewed／10 pending groups保持；局部42／65=64.6%不是全遊戲完成度。TW battle83 actions23、battle86 selectors7為30個前沿項；CN receiver14 contexts／12 qualified、47DE70／4812B0未知保持。958 endpoint rows／28 groups亦不是全遊戲分母。

第189輪網頁交接四份原件仍是客戶端secondary來源，本輪獨立CN原圖／producer證據與新來源另保存；網頁padding0 policy不是native initialization或權限。新增來源已經具備可供PC／web同一native transport上送的呼叫鏈，但真正Owner／權威battle supplies、全部原生技能／道具／陣形／續送結算及回覆仍OPEN，因此不宣稱完成整合或驗收。網頁契約的泛稱mask應限於已接的普通分支；本輪另回傳特殊2WORD／continuation的來源限定。

本輪另現讀網頁target scopes／manual items v2完整原件121709B、SHA0684c544df41adfc4e46a193fb7629775385d6cf86d281b10c44f27b5de93d7f與更新契約117323B、SHAd2f9847bbe51daf517f2cc184da60bce121d37b4a5a2c06432b90596ee9272e2，舊189原件不改。v2仍是implementation_unverified：skills先進目標階段，包含scope11，真正ACT點擊才出包；scopes13／14／16非群體逐目標帶80續送，群體mask單包。真正War alive／actor metadata供應者、scope17／完整陣形／第二actor／背包ACT／裝備前C28仍待客戶端自身接線。服務端新來源保留所有17bytes、高bit、順序，沒有扣MP／物品或忽略80；source一次execute只對每筆物理請求，尚未實作一個完整semantic command group僅消耗／結算一次的真正原生消費端，不宣稱逐包dispatch已相容。必要權威Owner仍須分辨native continuation、群體與特殊2WORD變體，再決定真正一次操作及回覆；不能用網頁token或相同bytes補造交易身分。

接續從實際battle admission、owner+3C context issuer、S86 grant／actor binding與skill／inventory reader處理權威來源，並補各命令真正操作／回覆。其餘native close/window／target issuer、entry／appearance／audience／native profile與Main、Web C56、全部玩法總表持續保留。完整TW-CN-web共用64位計算／storage／wire／object／飄字、仙幣99999999999、合格stack99、共用資料表（確證不相容才_tw／_cn）、WSS／TLS／hosting仍屬完整目標；等級不改。

本輪僅file／hash／來源修改、原生有界静態讀取；沒有建置、測試、native／C++／Lua／API／codec執行、DB／SQL、迁移、重啟或部署。155停止formatter／capacity／render／glyph鏈路及52F330／52F170未重試。帳號、存檔、聊天、IME、認證、頭像、原生字體、繁簡轉換及客戶端／凍結功能保留。fresh before1358、整個prior189的2537封存成員、各代理before／初版／refinement／current／完整原件與四原始／四最終報告分別保存。547706 short JMP的caller初選終點錯誤保留partial33B／writer01／error，最終30B另存，不冒稱失敗decode完整；root記帳工具的第一次替換斷言失敗在寫檔前停止，另存紀錄，未改baseline。整個God2 file-length容量另記policy與continuation，不還原歷史大型樹。目標保持active，全部來源串接後才集中全面驗證、修復与發布。
