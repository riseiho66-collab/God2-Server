# 第230輪：台服完整裝備呈現快照、提交憑證與 DA 來源

本輪新增完整原生裝備呈現快照的實際 SQLite 儲存、完整 tuple CAS、outer snapshot COMMIT 後私有憑證、同 Application Context 接點及第229輪真實 DA held-queue 呼叫端。這是版本化 delivery witness，不是共用道具權威、裝備規則或完整裝備交易。正式裝備 handler、物品取得／入庫與 item→完整外觀來源仍未供應。

## 原生範圍

仍使用3174400B、SHA256 `149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763` 的原件。本輪保留7段1021B／285個指令位置，新增覆蓋0；舊6bf動態病例不重跑，也不當目前149c證明。

C28 是 logical5：opcode、item低WORD、source低BYTE、flag低BYTE，沒有目的格、持有者或完整實例；已觀察 caller flag1也含卸裝，不能當 equip boolean。C24只帶兩個低BYTE格號，client panel gate不代表服務端權限。3B logical25帶count、slot、opaqueWORD與完整20B實例；consumer依metadata決定count1或8-bit加法後signed比較30，因此不能當安全絕對數量快照。41的signed count<=0只清count與實例低WORD，保留其餘18B。

兩個consumer直接限定格號0..49，以24B步幅存放完整20B實例到row+4，count在row+0。row+1..3仍未知；3B opaqueWORD沒有證據等於此prefix。新快照保存**全部50×24=1200B原始快取**，再附完整實際DA15，共1215B，不填零、不截尾、不把3B/41封包當完整快照。普通武器slot34的已確認metadata+120是reach，仍不構成item→DA對應。

## 實際儲存與提交

`NativeEquipmentSnapshot` 持有完整common root、當前saved position／revision、獨立native actor handle、client/source SHA、來源紀錄、嚴格正值revision及全部1215B。共用64位character ID與native handle分開，DA完整WORD必須吻合handle，不能截斷ID。資料只屬版本化呈現證據，沿用單一 `character_native_equipment_snapshots` 表按client/profile key保存；沒有複製角色、道具或裝備玩法資料表。

`SqliteNativeEquipmentSnapshotRepository` 必須使用同一個實際SQLite account／character來源。writer拒絕借用交易與caught reentry，自己持有BEGIN IMMEDIATE，對完整expected tuple比對，確認實際common root／saved position及pending battle。必要issuer在Prepared、BeforeWrite、BeforeCommit各返回完整next，必須完全相等；呼叫前後查完整原件、common root、position、交易狀態與SQL total_changes。issuer不得寫SQL、提交交易、yield、pump或發包。BeforeCommit讀staged next，不錯比舊before。

私有 `Committed` 憑證與完整owned snapshot在COMMIT前配置，成功outer snapshot COMMIT後才返回；COMMIT後沒有provider呼叫、重讀、配置或重試。token綁定不可複製writer的private identity，token本身move保持兩份有效。`committed_current`要求autocommit，使用獨立讀取交易重新確認完整快照、實際root／position與pending battle；SAVEPOINT release、另一個writer、staged tuple或來源過期均不能代替。

這個COMMIT只提交呈現快照，**沒有提交canonical item／slot mutation**。完整快照必須由真正取得全部50格與完整外觀afterstate的issuer供應；任意blob或通過格式檢查不會取得物品、規則或權威資格。

## 真正呼叫鏈路

`SqliteDatabase`新增lazy reader／writer accessor，兩者是同一物件，在實際Application game Context建立；普通initialize／migration／login不建schema。顯式fresh schema方法拒絕TEMP影子、要求foreign keys與自有交易，沒有IF NOT EXISTS、匯入、預設資料或自動遷移。本輪沒有呼叫任何SQL。

新的host opt-in預設false。Context附上同一reader／writer，Application驗證實際common sources；host Owner保留並比對新增兩個Context identity。`StoredSources::equipment_publication_factory`在啟動game owner建立後續提交用closure，擷取實際reader／writer、account／character借用來源及strong common host，不保留Context、不在啟動階段寫入。真正後續handler提交後，才將該writer的私有憑證交給closure，建立 `SharedTaiwanNativeEquipmentPublicationSource`；closure拒絕不同thread。

writer的每次load也拒絕TEMP中的accounts、recovered_characters、recovered_positions及battle相關同名物件，因為既有common reader仍使用未限定名稱。完整tuple／issuer邊界與committed_current都重新經過這個檢查，不能讓main witness搭配被TEMP遮蔽的common save。

Source的publish真正呼叫第229輪 `SharedActorVisibility::publish_taiwan_appearance`。每個Prepare／BeforePublish／AfterPublish／queue completion邊界重新讀完整已提交快照，前後確認同一ready lease、實際saved position及獨立actor handle；不能用lease固定入場位置冒充當前位置。快照因移動過期即拒絕，必須由真正issuer重新提供，不偷偷改位置。借用DB的生命週期必須覆蓋game owner drain；既有pending取消、私有Binding與weak IO facade仍沿用229實作。

完整1200B庫存只是來源觀察，不在此發送，也不假裝供出完整最新6F。新snapshot／DA歷史紀錄不代表全快取重建、socket寫完或客戶端驗收。native self-local DA、混合版本完整fanout及真Application全生命週期仍獨立OPEN。

## 進度與下一步

本輪新增5個C++來源檔、修改7個來源檔，新增1段部分來源串接，累計216；新增完整雙向遊戲路線0。台服C2S156、世界S2C252、戰鬥S2C110；完整狀態／變體分母與完成率仍未知。

接下來必須把真正共用owned instance／equipment mutation、完整before/after source revision、實際item→12B appearance、完整庫存回覆及native handler接上，canonical交易成功後才能取得相應呈現資料並發布。本輪快照憑證不能代替該canonical交易。完整2A producer、once-Issued admission、Main與13個世界玩法分支仍OPEN，保留CN／web／共用資料／64位數值／stack99／原生字體與凍結功能。

沒有建置、測試、native／VM／codec／遊戲執行、資料庫讀寫／SQL、遷移或部署。目標active，台服完整串接100%之前持續工作，再集中測試驗證。
