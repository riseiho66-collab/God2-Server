# 金錢、經驗值、傷害與HP數值擴充

使用者2026-10-07明確確認：只要四項數值能突破約21億，整支EXE轉x64
不是前置條件。第一階段繼續靜態恢復與來源串接，不執行客戶端或正式DB。
這是原全遊戲串接目標的增補；不是將全部數值直接改成64就宣稱完成。

最新使用者精確上限：**仙幣99,999,999,999**。使用者已明確回答只有仙幣
使用此值；經驗值、傷害和HP上限另定，不把999億口語換算覆蓋精確數字。
CUSTOM-0088 / ExtendedCoinAmount.h保存非負uint64上限、checked credit/debit、
精確十進位及SQLite signed64表示；超過native DWORD範圍時返回不可表示，
不截低32位。現已接入共用wallet讀取、兩種交易結算、銀行轉帳錢包計算與
公會Lua錢包輸入的來源；資料表可恢復遷移及client擴充仍未完成，
不宣稱目前原生錢包可顯示此值。現有原生正數顯示上限的當前EXE證據
見research/native-xianbi-display-width-20261007.md。
使用者另明確要求傷害/HP增減突破16位元範圍。新增
使用者最終採共用計算與數值域64位元，同步改TW/CN/web封包/物件/飄字，
取代中間提出的32位元方案。ExtendedBattleDeltaAmount.h現在是精確signed64
域與無溢位magnitude，不能表示為legacy native short/DWORD時返回不可表示，
不截位。EXP/傷害/maxHP的實際上限仍未指定，仙幣上限不推廣到其他數值。
實際Battle/Lua/儲存、
TW/CN producer/consumer、動作queue/actor及飄字仍需同步擴充，尚未接通。
目標/side/mask/itemID等無關WORD不能因傷害擴充而一併改寬。
使用者已確認等級不需要改，保留原生欄位與既有升級規則；面板uint8的255
只是已查得顯示容量，不能據此設定全遊戲最高等級或重寫經驗曲線。

## 本輪實際來源

台服God2.exe、God2.unpacked.exe與固定CN God2_opt.exe皆現讀到Machine
0x14c、OptionalHeaderMagic0x10b（x86 PE32）。精確雜湊與大小保留於
artifacts/continuation/numeric64-scope-20261007/client-pe-architecture.json。
解殼不等於具有原始碼，EXE架構與個別整數欄位寬度分開處理。

| 範圍 | 已讀來源與欄位 | 下一個缺口 |
|---|---|---|
| 金錢 | TW RecoveredBank 61/62 amount DWORD；47 absolute bank balance DWORD；交易2B money DWORD。 | 錢包、銀行、交易、公會費用、任務與存檔的實際producer/consumer、signed比較與顯示格式須逐條對齊；這些TW資料不是CN證據。 |
| 經驗值 | CharacterExperience.total與BattleSettlement.total_experience為uint64；settle_battle單次experience仍uint32；SQLite累計來源以INT64_MAX檢查。TW89顯示值在logical5/9/13/53皆DWORD，非累計權威。 | CN89完整consumer、累計/單次/等級門檻/呈現的signedness；舊存檔及Lua交換邊界。 |
| HP | CharacterResources hp/max_hp為uint32；TW24四個DWORD、22 maxHP在17；CN86 scalar5/9及88回合current pairs為DWORD。 | CN pairA/B仍是原生資源欄位，不能冒稱全部敵方HP/MP；需查全讀写與GUI。 |
| 傷害 | TW83/0D目前限定分支amount為signed16；accumulator為DWORD。CUSTOM BattleHit/CombatRuleResult為uint32。 | 此83子型別不能代表所有傷害。其他原生動作/群攻/持續效果與CNconsumer須繼續追，CUSTOM核心不當CN原生規則。 |

TW RecoveredBattleDelta中00528A70/00528AC0的DWORD wrapping ADD、sign floor及
signed cap比較，是已保存的具體限制線索。即使uint32儲存能保留較大bit pattern，
原生consumer仍可能將bit31當負數；不能僅改UI字串或對封包DWORD直接加寬。

## 實作順序與完成條件

1. 建立每個欄位從權威計算、交易、儲存、Lua、native wire到client物件/
   顯示的完整路徑，標明位寬、signedness、哨兵及來源版本。已是64位的
   累計經驗沿用，先找窄化及signed分支。
2. 權威非負金額/經驗/資源與傷害擴充到有明確上限的64位計算；中間乘法、
   加減、CAS與持久化全鏈檢查溢位，負號/消耗/恢復語義逐欄保留。SQLite
   signed64可作候選共同儲存界線，實際上限待全鏈資格來源確定。
3. 保留原生格式基準。若僅需突破signed32至unsigned32可行範圍，逐點查
   客戶端signed branch與顯示；需要超過DWORD時，必須同步改TW/CN及網頁
   的物件、producer/consumer、長度與顯示，採明確版本化的自有擴充協定，
   不把擴充稱為原生，不用未知opcode猜成功。舊客戶端不能默默截斷值。
4. 網頁值超過Number安全整數時用BigInt或精確字串/bytes；wire既有DWORD
   仍維持原寬，不因瀏覽器是64位而重新解釋native控制欄位。
5. 全來源串接後集中檢查跨過2^31、2^32與Number精確範圍的儲存/交易/
   戰鬥/收件者呈現；在集中驗證階段實際證明四項不溢位、不丟精度且可
   正常操作後才計完成。凍結聊天、認證、字體與簡繁不受數值擴充影響。

## 錢包來源增量：coin-wallet64-01

- `SqliteTradeRepository::Wallet.amount`、一般交易與完整物品實例交易的
  權威金額提案改為uint64。讀取SQLite整數以uint64承接，再檢查
  CUSTOM-0088精確上限。`ExtendedCoinAmount::exchange`先檢查來源、
  支出及收入，做checked debit/credit；兩個錢包的總和保持守恆。
- 兩個交易plan移除UINT32_MAX截斷；一般交易的錢包SQL另包含原金額、
  revision及既有CUSTOM-0063來源的CAS。完整實例交易保留原來的全物件、
  保存證據及CAS，沒有合併堆疊或改背包格數。
- 銀行61/62的錢包計算及轉帳receipt的wallet_amount讀回改為64位。
  現有銀行500000000限制與原生請求DWORD保持原狀，還未擴充銀行GUI。
- 公會Lua的wallet輸入改为uint64域，確認值在仙幣界線內後以signed64
  integer送入Lua；既有建會50000規則、費用欄位與等級規則不變。
- `RecoveredTrade::wallet`以uint64接收，再檢查當前原生signed32正數顯示
  範圍，不能表示就拋出具名投影錯誤。交易及銀行在SQL前準備全回包，
  投影失敗不得結算、截低位或假成功；三種公會建立conversation在開啟
  之前檢查其後legacy27的金額範圍。這些是相容性拒絕條件，不是大數值
  可玩支援，也不算新增完整封包路線。

現有`install_schema`與migration歷史保留原SQL，未換成另一套自動遷移：
`character_trade_wallets.amount`及`character_bank_receipts.wallet_amount`
仍有DWORD CHECK。因此來源可保留/計算64位值不代表目前資料表能寫入
超過DWORD的金額。需要來源匹配、保留所有舊列及附加欄位/trigger/index、
可恢復且版本化的共同表遷移，不能直接重建或匯入CN獨立DB。

目前數值擴充完整路徑0；沒有改EXE、執行資料庫遷移、改玩法值或原生
封包長度。CN27的consumer證據不代表CN登入/世界錢包已接入；TW/CN的
原生擴充producer/consumer/物件/UI與web精確wire仍是明確缺口。
本輪來源快照與位寬路徑記錄保存在
`artifacts/integration/packet-connections-20261006/coin-wallet64-01`。

架構參考：[Microsoft PE格式](https://learn.microsoft.com/en-us/windows/win32/debug/pe-format)、
[x64 ABI](https://learn.microsoft.com/en-us/cpp/build/x64-software-conventions)、
[JavaScript BigInt](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/BigInt)。
