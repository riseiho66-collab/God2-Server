# CN 擬態／特技：選中物件與原生技能來源交接

本輪 `20261008-cn-preborn-selected-subject-source`，PHASE1，目標 ACTIVE／INCOMPLETE。
前輪130的具體window生命週期已封存；本輪修改前保存116檔snapshot，
保留175檔前輪封存與其SHA256，不更新歷史原生基準。

## 本輪釐清的實際指標關係

固定CN PE32 SHA256：
`582f269535f86e95fcd77946821adf79a30d1bd33f21d566cf48c36fd221b3c8`。
讀取file-backed bytes、個別00*.c、entry-rooted局部CFG；不載入或執行client。

`0048CAA0`中`0048D421`將EBX指向同一world+1478084。
傳給004AC850的實際array base是EBP-37C，index10在EBP-354，
`0048D663`保存這個EBX；`0048D670`呼叫004AC850。
Ghidra local_358等標籤與實際EBP偏移有4-byte差，不能直接當instruction boundary。
初次以0048D5E0任意切片的ASM從指令中段開始，本輪另存為unqualified，
不作證據；正式定位使用0048CAA0入口CFG的實際指令位置0048D5E1等。

004AC850中EBX明確是array參數、ESI是入口UI owner；
`004AC8D3/D6`把index10寫入UI+430AC，`004ACF05`也把同一index10
傳入004AF370，mode0分支中的`004AF485`取object+90，
`004AF493/496`傳給004D2D30；後者把實際arg写入同一UI+430A8。
因此在這個來源分支，**UI+430A8=object+90、UI+430AC=object**。
role+D0和object+160、role+D4和object+164、role+CF和object+15F
是同一組實際欄位。前輪只列未確認，這輪才補足入口、傳參及owner證據。

004D4E00以signed BYTE index >=0 且小於實際BYTE count為條件，
把role+D0設為role+D8+index*3EC。換算同一object為object+168+index*3EC。
00492E70對同一object+168清除3EC0 bytes，並分別寫+164 count、+15F index、
+160 pointer；另有無來源分支把pointer放在首entry但count為零。
這個分支不表示已有有效選擇，因此來源reader不替它生成slot0。
本輪只限定這個16-slot native layout，不宣稱全部物件種類或遊戲規則容量。

00534640從object+160取得選中entry，使用其BYTE+1F0的count、
BYTE旗標區+1F1與DWORD指標區+258。100個指標位置結束於entry+3E8前，
後續+3E8/+3E9另有原生page欄位；來源reader拒絕超出可捕獲layout的count，
不截斷或补造缺失資料。WORD0、BYTE+5B、旗標與指標值按原寬度保留；
不能稱為共同ID、可施放技能、費用或server授權。

原生skill bank為role+4474，也就是object+4504。
00492E70的00493555及0048CAA0的另一條0048D49A寫入，都使用
同一actual world+8885F0來源加9D223C。
00533300的A2 consumer按bank+kind*6E04-6A+id*6E定位110-byte record。
本輪保存實際指標／算式來源，但沒有取得完整CN loader／resource／catalog規則，
沒有把既有TW `current-skill-catalog-v1`提升為CN證據，沒有宣稱MP費用或原生技能技能資格。

## 已接入來源

新增`CnPrebornSubjectState`，只讀actual UI+430A8開始的8-byte view及同一object
prefix，要求actual owner／object／source revision與Current；沒有ProcessMemory、
指標解參考、初始化模擬或資料預設。Snapshot擁有選中entry身份、原生技能旗標與
指標副本；空list、無效index、非該slot指標仍保留為unselected。

既有Window來源可附帶這個actual Snapshot作恢復證據；若提供，prepared／issued
observation要求Snapshot當前、來源revision一致及真實selected context。
沒有證據時仍必須由真正common subject／skills／rule來源提供Current及apply，
不要求讀玩家客戶端記憶體，也不生成native UI位址或指標填入快照。
其他未選擇／pre-world變體與全部原生initial時機仍開放。
原有already-issued WorldOwner路徑沒有改成新預設，全部原生phase也沒有因此完成。

SharedPrebornWindowSource將可選Snapshot與window一起退役，在真正common apply callback
保留這段native provenance。真正handler必須從權威common資料及explicit mapping取得common object
及skills，再完成Lua規則、transaction、save、persistent replay及actual native輸出。
不將原生地址、subject WORD或list index當成共同主鍵。

post-commit delivery收到的是retained identity／provenance；
不調用已退役Snapshot.Current去判斷新共同revision。
沒有打開資料庫、建立資料列、補權限或自動啟用Application。

初版來源曾要求native Snapshot作為window前置，會造成對client位址的非必要依賴，
因此已修正為可選恢復證據，actual common資料來源仍必須存在。
原始source／findings／catalog131及CLI報告另存不覆寫；本輪最終來源與修正receipt
保存在source-correction，最新報告綁定endpoint-catalog131-final。

## 增量及缺口

新增實際selected-subject來源reader1，既有window→common operation來源交接補強1，
補足mode0 inline-role／selected pointer／skill bank來源關係。
opcode、phase綁定、partial owner及完整雙向路徑增量均0；全遊戲總數和百分比null。

仍需完整CN skill loader／resource／record身份、實際subject→common映射與skill owner、
initial issuer時機、Lua規則／存檔／重播、Application及其餘輸出變體。
84 caller與全部preborn相對1C／pre-world的時機仍未確認；不推定84→A0。
完整TW／CN／PC／web／WSS、共同帳號世界、所有玩法、64-bit數值、背包99和完整分母
保持目標，之後才全面建置、測試、修復及可恢復發布。

未建置、測試、執行native／C++／API／服務、讀寫DB、遷移或部署。
帳號存檔、認證、聊天、IME、頭像、客戶端、原生字體、繁簡轉換、等級維持。
