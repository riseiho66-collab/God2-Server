# CN清單選擇及真正94產生器（2026-10-07）

將已有primary函式證據0050E5E0／0050E3B0接入來源，而非新增opcode。
新來源`CnDirectorySelection.h`保存43個明確選擇條件、原生返回0與診斷分支、
producer的cursor來源及D1先行條件。既有`CnDirectoryWire::Request`可將限定
94請求的原生來源描述交給真正WorldOwner；沒有增加虛構資料供應器或放行權限。
封存`cn-directory-selection-producer-01`保留catalog34前後來源、原生完整CFG
及前輪證據。客戶端釘定SHA256為
`582f269535f86e95fcd77946821adf79a30d1bd33f21d566cf48c36fd221b3c8`。

## 模式／UI／選擇條件

mode來自真正worldnetwork+4200，UIstate來自player+22CE4；group／secondary
是函式參數，現有控制來源00510E80透過00512700寫入22CDC／22CE0。
这些UI值不在94線路中，服務端不能從selector還原成玩家實際UI或存取許可。

mode1只在UIstate2F有3個明確分支：group1/secondary0→24，1/1→23，
group2→19（mapper忽略secondary）。mode0有40個明確條件：
group0四個；group1/secondary0四個；group1/secondary1九個；group2二十三個。
43是這一mapper的明確條件數；group2的secondary是忽略條件而非逐值枚舉。
這不是全遊戲變體分母、不是43個opcode、不是43條接通路徑。

mode0/UI2F/group0/secondary1確實返回selector00；不能將0一律當失敗。
另一類default也返回0，部分先呼叫診斷0053E3D0；來源分別保留explicit_origin
與diagnostic_line。mode1/group2非2F、mode0/group2未列UIstate都靜默返回0。
0050E3B0呼叫前另判group或secondary為-1直接return；不能因mapper忽略secondary
便假設secondary=-1仍發送。沒有執行此邏輯、沒有新增診斷封包。

0050E5E0舊metadata786bytes會切斷實際控制流程；完整primary包絡
0050E5E0..0050E916（end exclusive）為822bytes，分派表位於E918／E990／E9D0。
本輪接續cn-summary-world-lineage-01已有完整證據，不將相同原生恢復重算新增。
0050E3B0完整primary到0050E542為402bytes，舊metadata153不代表完整函式。

## B0回寫cursor不能套到所有94

0050E3B0模式0 selector11/12/15/16/17/18/1B/21/22，以及兩模式19/23/24，
94 payload4皆讀已追明的對應owner欄位。其欄位恰為對應B0metadata+12。
其他通常讀player+22D0C+selector*3F0，與某些B0的owner游標不同。

模式0 selector25/26只發D1（payload為selector,01），直接return，不發94。
selector27/28先發D1、再發94，但94 payload4沒有賦值，是未指定stack bytes；
不能填成0、不能改成間接owner+B56C的B0游標。
selector2A/2B/2C/2D的94仍讀generic selector cache：2D26C／2D65C／2DA4C／2DE3C；
前輪B0consumer卻寫間接owner+B56C的共享游標。兩者尚無其他alias證據，
所以不能將B0→下一個94游標關係擴張到這四個selector。
原生三個未寫padding及未知DWORD必須保留，沒有製造wire回覆。

前輪完整B0consumer存在15/16等selector，但本mapper沒有對應明確產生條件；
mode0 B0也可接19/23/24，而本mapper只有mode1明確產生這三種。
這是有限producer與consumer不對稱，需追其他producer／UI／延後分派。
空的known_origins不能當成所有來源不存在或服務端禁止該請求。

## 來源與進度限制

Request的known_refresh_origins／refresh_producer是既有三channel的上下文存取；
A4返回無94 producer描述，不能套用refresh映射。WorldOwner仍需真實權威資料、
身份、排序、頁面、資源文字與完整AE/B0 issuance；此輪沒有製造共用rank。
目前不同模式的實際欄位標題及分類、其他receiver、正式world dispatcher、
登入／世界供應器和完整玩法均繼續追查。

新增1份C++來源，修改1份C++及1份catalog工具；新的owner chain、
phase/opcode關聯與完整路徑皆0。全遊戲總数／完成数／百分比unknown/null。
未建置、測試、執行、Lua、資源loader、部署、正式DB讀寫或改客戶端。
保留原生字體、繁簡轉換、認證、存檔、聊天及IME。
