# 第204輪：CN 原生主技能第一筆序號來源

本輪是使用者指定203至207共五輪中的第2輪。目標繼續active，207完成後暫停並停止子代理，不開始208。只做靜態原生恢復與來源串接，未建置、執行原生、測試、操作DB／SQL或部署。

原生004D2B50的93-byte純資料leaf從UI+430A8取得role，再取role+D0選中row。一次讀取row+1F0的BYTE count；按row+258的DWORD指標原始順序比較definition BYTE1／BYTE0零擴展值與兩個完整DWORD參數，回傳第一筆0-based ordinal，沒有符合則-1。沒有flags過濾、去重或上位bit截斷。缺少role或selected pointer也回-1；現有完整bank來源必須已取得真實選中row，沒有把缺失row製造成empty成功。

004DA630的type2實際資料caller保留兩段179B。mode0與mode1使用不同表，kind／id是signed WORD符號擴展為DWORD；mode1還使用selected signed BYTE作表索引。負數或含高位值不能以截BYTE替代成合法技能。首筆匹配之後另送004D3B60 gate；首筆gate失敗不能改找後面的重複項目。沒有進入formatter、GUI、render或該gate內部，本輪不將member lookup當learned／cast權限。

CnWorldPrimarySkillSource新增find_actual_primary_ordinal，對已完整擁有、與釘定資源逐byte相符的選中row／bank來源執行相同first-match資料投影。入口及返回都要求實際Current，重入／Current失效終止；外層null表示資格失敗，合格結果的內層無ordinal表示原生-1。使用完整uint32 kind／id，保持original order／duplicates／flags；ordinal轉uint8由既有完整row指標幾何界線保證，沒有新增遊戲等級或技能數上限。

既有CnPrebornSkillChoiceSource只有在選用actual primary supplier時，才保存每個retained word高／低byte對應的owned ordinal facts，並由既有prepared／issued選擇來源交給共用操作輸入。這是明示的word投影，不聲稱該word來自004DA630的mode table，也不取代native filtered offer、書籍來源、server entitlement或downstream gate。缺supplier仍未知；選用supplier後Current失敗拒絕，不退回geometry／同key目錄來冒充成功。owned facts跨commit保留，沒有事後重用舊Current作權限。

本輪修改4個C++來源檔、新增來源區段1；累計來源區段194，新增完整雙向玩法路徑0。既有帳本歷史、完整203封存與代理原始來源保留，root／catalog204另存全檔SHA與有界原生bytes。未更動帳號存檔、原生EXE、字體、繁簡轉換、native等級或凍結功能，沒有啟用Main實際來源。

| 範圍 | 本輪結束數量 | 說明 |
|---|---:|---|
| TW C2S 已觀察opcode聯集 |156|151 generic＋5 supplemental，不是完整玩法分母|
| CN C2S 已觀察opcode聯集 |156|本輪沒有新增opcode|
| TW WORLD S2C 長度表 |252／256|230固定、22變長、4 unsupported；不是完成路徑|
| TW BATTLE S2C 索引 |110|9 special、101 default；83 action23、86 selector7|
| CN S2C phase entries |280|account6、world206、battle68；phase entry不是全遊戲去重總數|
| CN receiver contexts |14／12已具體限定|47DE70、4812B0仍unknown|
| TW WORLD parser review |42／65＝64.6%|僅這個固定parser範圍的review比例|
| partial owner chains |38|CN35＋TW3，仍非完整route|
| endpoint rows／source groups |958／28|不作可玩百分比分母|
| partial source segments |194|193→194|
| 本輪新增完整雙向route |0|沒有把readonly projection算完整gameplay|
| 全遊戲完整路徑總數／完成百分比 |unknown／null|方向、狀態、變體、deferred總表尚未完整|

下一個精確來源是004D3B60的非GUI ordinal gate，以及原生主清單的正向寫入端。真正common learned actor、owned book custody、扣書、儲存／durable event與原生回覆、WORLD→battle materializer、實際store lifecycle與Main issuer仍待串接；64位數值／99重疊與TW／CN／web整體雙向玩法也仍待接。全部來源打通後才集中全面測試與修復。停止點維持207。
