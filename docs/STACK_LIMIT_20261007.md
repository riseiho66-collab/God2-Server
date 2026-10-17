# 背包可堆疊物品上限99

使用者2026-10-07指定單格可堆疊數量由原需求30提高到99。此要求不是增加
背包格數；普通背包30格、裝備/武器/傳送石/PET單件身分及不可堆疊規則
保留。金額上限和物品數量是不同欄位。

TW RecoveredInventory的S2C41為logical5，itemWORD1、slot3、raw_count4；
consumer將count當signedbyte，0x80..0xff清除occupancy。99在正數範圍內，
無需因99把該native欄位改成64位，但尚未證明每個UI/producer允許99。
此TW局部資料不代表全部物品流程已支援99。

目前source的30多數是普通背包格數，而不是堆疊上限。SqliteInventoryMove
是CUSTOM-0037整堆交換；OwnedInstanceTrade也是不同完整metadata實例交易，
不能直接改成數量合併。現有BankItems及trade scalar有count<=127 wire範圍
檢查，尚未按本需求接統一99玩法上限。OrangeShop另有選購數量上限30，
不能把這個購買限制冒稱為所有物品堆疊限制或全局替換。

CUSTOM-0089 / OwnedStackQuantity.h新增共用99數量域及checked增減；來源
呼叫者必須先證明物品可堆疊、item/metadata身分及owner/revision。此來源
尚未掛載既有倉庫、交易、拆分、使用/丟棄/獎勵或native UI producer。

接續逐條恢復台服可堆疊分類及原生合併/拆分/輸入流程，在同一權威
transaction內保留總量和兩格metadata/CAS、輸出按版本slot projection。
擴充後99在native byte範圍內仍不表示client本地30 cap已移除。集中驗證
留至全部來源串接完成，舊存檔與凍結功能保留。

本輪未建置、測試、啟動、改EXE、讀寫正式DB或部署；新增完整玩法0。

2026-10-09第208輪：先將CUSTOM-0089接入現有TW CUSTOM-0037 scalar
whole-stack swap。Application的既有InventoryMoveService呼叫保留，service
先驗兩個slot的count0..99再準備原生回覆，SqliteInventoryMove在原本
CAS交易內再次檢查count99、empty occupancy及非零revision。普通背包
30格不改，不新增merge、split、item grant或stackability。讀取與原生
projection127保留；歷史100..127數量不剪截／遷移，新的此類swap拒絕。
倉庫、交易、獎勵、使用、拆分、完整instance及台服UI仍各有未完路徑。
這是實際既有Application來源呼叫的寫入域接入，不是全物品99或TW100%。

2026-10-12第325輪：OwnedStackQuantity的from/increase/decrease收完整uint64
輸入，先比較99/remaining/current再投影BYTE；quantity值域仍0..99。
SqliteOwnedInventoryRepository::valid直接使用此共用域校驗common quantity64，
occupied仍1..99、unstackable仍1。load/validate_change/stage_replace以及既有
兩庫／三庫裝備交易的實際校驗使用相同來源；舊literal uint64比較原已拒絕
大值，沒有聲稱現存存檔曾被截斷。既有scalar move的count:uint8呼叫維持，
未新增increase/decrease玩法caller、merge/split/grant或原生stackability。
SQL schema與wire不改，native30 clamp/台服UI/全玩法99仍未完成。保留0089
歷史欄位并新增唯一325provenance。未build/tests/runtime/native/codec/DBSQL/deploy。
