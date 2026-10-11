# 第224輪：台服原生場景資源來源

TW先完成全部雙向來源串接，再集中建置／測試／修復；本輪只改來源，目標保持active。

新增 TaiwanNativeNpcSceneGroups.h/.cpp：實際供應的完整decoded原件先自有複製再核對75c3雜湊（4MiB界限），保留全文及NPCList原始451列、CR/CR/LF、行號／offset／列身分。17個area按首次場景出現順序建立251群，重複場景追加資源，空群保留，共1509個原碼。每資源保留原int32 code及原列／欄位置，另依149c的45A91D..45AA3F產生商／餘數低BYTE；低BYTE投影可能有損，不能充當共用實體ID。查詢scene使用WORD完整比較，不將256以上別名成BYTE場景。不合成142B原生記憶體padding。

原生45A8F0對area只有signed>=17檢查，新群寫scene低BYTE及count0；並未證明negativearea／新群70上限／unused尾部clear。原生對非正code停止該列，滿70資源跳過後續寫入，sscanf('%d')允許尾部未消耗。新來源明列較窄的owned安全子集：area0..16、scene0..255、2..7完整ASCII整數欄、正int32 code及70群／70資源界限，reject而不重現越界或靜默丟棄。這些守衛不是聲稱原生本來有完整輸入驗證。五段579B純資料loader/token邊界保守列作已覆蓋證據，不增加全域native覆蓋；兩段195B既有query leaf直接引用223封存。

NativeEnemyDisplayCatalog新增Scene/read_scene(area,scene)：同一CatalogReadScope先完整核對7815列（含24 superseded）、7791可見／96群的既有指紋，再從main表一次取得該場景所有可見列，依ordinal排序，保留完整raw/provenance／generation／source occurrence。拒絕temp影子與main缺schema，既有counts()/lookup行為保持原樣。未載完整catalog回nullopt；完整資格後查不到該場景回帶來源的空Scene。精確source tuple為149c／70a4／75c3／EnyName／0x5a1a0／0x5a0a0。這是場景名稱／資源資料，未生造26B bank、位置、怪物HP、雙攻雙防、技能或掉落。

現有encoded gamedata是ef297／3131095B，與歷史70a4不同。本輪沒有解碼、匯入、恢復歷史原件、查真資料庫或偷偷換基準。NPC factory要求真實供應的完整75c3 decoded內容，其絕對路徑只是該供應原件的來源；historical_encoded_sha256是歷史metadata，不表示encoded檔目前存在。EnyName可使用既有完整資格catalog契約，但本輪沒有聲稱正式DB已載入或新API已啟用。

本輪2新增＋2修改C++檔、1個實際來源增量，累計來源段212→213；新完成全雙向玩法路徑0。TW已觀察156個C2S；world252有效分派（230定長／22變長，另4不支援）、battle110（9專門／101預設），是不同方向／階段的盤點，不能相加當全遊戲總數。65個解析分支中42個已review（64.6%僅解析分支review率）。TW／全遊戲完整路徑分母與完成率仍未知（null）；958端點／28群是當前跨版靜態帳本，也不是遊戲完成分母。

下一步把這些實際完整場景內容接進入場的完整2A資源／狀態issuer，保留尚未解出的B26..27與其後scene呼叫邊界；不得用NPCList或EnyName推猜完整40B封包。一次性admission／lifecycle／scene／reply與Main實際選用，以及PK、邀請、傳送、寵物、每日、同伴、活動、商店、對話與觀戰等全部剩餘TW路徑仍OPEN。保留共用核心、CN／web、數值64位、仙幣99999999999、合資格堆疊99、native字體／文字轉換及凍結功能。

本輪無build／tests／native或VM執行／codec／server／DB／SQL執行／migration／deployment。大型新增完整原件與報告存於本任務外部archive，歷史封存保持原位；來源與證據計量只讀，不充當遊戲驗收。
