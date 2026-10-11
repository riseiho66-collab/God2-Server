# 第231輪：共用物品持有儲存與台服C28原生選取來源

本輪加入實際共用整件物品持有儲存、完整owner population CAS、永久實例／取得憑證去重，以及台服C28(flag1)對真正ready玩家與已持有原生alias的唯讀選取來源。這是CUSTOM-0092內部儲存政策及限定原生來源接點，沒有把舊CUSTOM／6bf／c5d8物品升格，也沒有完成裝備玩法、原生取得規則或item→DA。

## 原生定點與限制

同149c原件保留兩段432B／137個指令位置、12個opaque CALL，新增原生覆蓋0。3B尾段498EA4..498FC2、41尾段499268..4992FA可將完整24B快取row與sign-extended slot送到49B850；它仍是未進入的UI/helper邊界，不能宣稱內部沒有物品→外觀對應。3B依UI866A4的mode0／1跳過不同slot，slot34在mode1不走這個直接CALL；41有效slot尾仍可到4992F0。49FBD0／48E7A0也可存取receiver／global狀態。沒有進入STOP、GUI、render或formatter內部。

既有metadata114／116／118是icon、120是reach；既有DA12B來自完整incoming raw15／2A。這些事實都不能組成完整物品→12B after-appearance來源。C28的完整低WORD key、source低BYTE與flag1也不提供目的格、equip boolean、持有者或全域實例ID。

## 實際共用持有儲存

`OwnedInventorySnapshot`持有完整common character root、嚴格正值revision、來源SHA／record、完整排序的明示位置與全部原生aliases。空格是明示的`nullopt`，未列位置不是空位。位置kind／index是服務端內部名稱，沒有推定原生equipment slot、容量或目的格。

每個物品有獨立server-only正signed64 instance ID與共用definition key、quantity／stackability／revision及不可變取得來源。ID與definition不可由raw20、keyWORD、slot或selector生成。各client／profile alias保存全部原始bytes、native key／slot、來源及同一實例revision；raw20不作共同數量或唯一ID解碼。合格可堆疊量1..99沿用CUSTOM-0089，其餘整件量1；實際definition、stackability、slot資格仍由完整issuer供應，不冒稱原生規則。4096 cells／16 aliases／4096B record是內部資源界線，不是遊戲容量。

`SqliteOwnedInventoryRepository`用同一實際account／character connection與四張共用表。`owned_item_instances`是永久全域registry，instance ID和取得SHA／record各唯一；退役只移除位置，ID／receipt永不自動刪除。新ID只能INSERT，因此不能偷取別人實例、重放同一取得憑證或復活退役實例。跨owner交易與自動merge／split需另外實際多owner交易，目前沒有提供。原生aliases外鍵掛到唯一實際位置，移除位置／角色會連帶移除current aliases，永久registry仍保留。

writer自己持有BEGIN IMMEDIATE，拒借用交易與issuer reader／writer reentry；對完整before population及所有aliases作CAS，不只比revision。原本實例的definition、stackability、取得來源不可變，換位／數量／alias異動須提高instance revision。每個issuer邊界回傳完整next，必須完全相等；不得SQL寫入、交易操作、yield、pump或send。Prepared／BeforeWrite／BeforeCommit前後檢查完整實際root、pending battle、來源、autocommit與total_changes；BeforeCommit比staged next。所有儲存SQL限定main，且拒絕common及新table的TEMP遮蔽。

完整immutable private token在COMMIT前配置，只有成功outer COMMIT才返回，之後沒有issuer、重讀、重試或配置。`observe_committed`是對已存在持有資料的新獨立讀取交易觀察，不是新交易／取得憑證；它與`committed_current`均要求autocommit、完整資料與當前common root。loader自身也用一致讀scope，沒有將數個獨立SELECT當同一觀察。

## 台服C28選取與Application來源

`SharedTaiwanOwnedItemSelectionSource`使用真正Session／ready lease、InWorld、native world ready、common delivery generation、非entry delivery、當前saved position與battle generation。讀取已提交持有資料前後與最後再次檢查；回傳private完整owned Selection，包含原始request、完整持有snapshot、精確cell／instance／alias及連線weak identity。caught重入會poison外層觀察，不接受替身Session。

只有same149c、`tw149c-item20`、exact20B、同raw slot與完整item WORD、alias revision等於實例revision才可被選取。firstWORD只驗client key，沒有推導common ID、definition、quantity或目的格。Request由外部typed caller傳入；這個reader不證明實際封包收取、請求freshness或動作授權，真正C28 dispatcher仍需接入。`current`僅適用mutation前的完整before；真正staged after不能拿舊before比較。C28不會新增物品、猜裝備動作、送成功回覆或代替規則owner。

Database新增optional共用reader／writer；SqliteDatabase lazy accessor在真正game Context建立同一物件，ordinary initialize／migration不裝schema、不匯入或填資料。顯式fresh schema只有原始SOURCE，沒有執行SQL。Context附上同一reader／writer，Application及host Owner驗證／保留實際來源identity；`StoredSources::owned_item_selection`用同一common presence建立選取來源。host opt-in預設false，選取能力限定149c，Main仍未選取。

## 進度與缺口

新增5個C++來源、修改7個C++來源，新增1段部分串接，累計217段。台服C2S156、世界S2C252、戰鬥S2C110維持原方向／階段定義；新增完整雙向遊戲路線0，台服／全遊戲總分母與完成率仍未知。

真正取得／掉落／任務／definition mapping issuer、native C28玩法handler與Lua規則、共用物品變更和完整native presentation快照的**同一outer COMMIT**、完整庫存回覆與item→DA producer仍OPEN。第230輪快照COMMIT仍與這個canonical custody COMMIT分開，不能先後呼叫兩個writer就宣稱原子裝備交易。也未供應self-local DA、完整mixed fanout、完整2A、once-Issued admission或Main／全生命週期drain。

CUSTOM-0092只新增內部儲存政策，不授權CN自訂玩法；共用帳號／角色／道具與各版本alias分開保存。保留CN／web、帳號存檔／聊天／IME／認證／頭像／EXE／原生字體／繁簡轉換／等級、64位數值與stack99要求。本輪沒有建置、測試、native／VM／codec／遊戲執行、SQL／DB操作、遷移或部署。目標active，先續台服完整來源串接再集中測試。
