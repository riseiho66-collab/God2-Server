# CN B0完整接收selector布局及實際清除範圍（2026-10-07）

前輪已接條件式三清單94/A4/AE/B0来源，本輪新增`CnDirectoryReceiver.h`，
靜態閉合釘定005118E0這一個B0consumer的全部selector分支：mode0共18，
mode1共3，因此此consumer有21個模式／selector組合。
這是有限consumer的分支盤點，沒有變成全遊戲分母或21條完成路徑。

釘定exe SHA256:
`582f269535f86e95fcd77946821adf79a30d1bd33f21d566cf48c36fd221b3c8`。
新證據為`cn-directory-receiver-matrix-01`，不覆寫catalog33或舊原生／接收／欄位證據。
全程只有靜態primary code/CFG/source盤點，未建置、測試、執行、讀正式DB或部署。

## 一個consumer的完整分支矩陣

以下base皆是相對player或[player+1C85A8]的位址；不是服務端資料表欄位。
record+1開始包含WORD總長；record selector/count/cursor/rows偏移為3/4/5/9，
每列40bytes，byte32作native目標索引。所有此consumer實際複製的分支均用此格式。
初始化欄位表頭是40bytes，索引0會寫到表頭，真正列區域從index1開始。

|selector|owner|列base|翻頁metadata base|非空high-index更新|B0頁數|每次接收先清資料列|初始化列清除bytes|
|---|---|---|---|---|---:|---:|---:|
|11|player|2E228|2E228|max舊值與最後列index|4|0|4000|
|12|player|2F1F0|2F1F0|同上|4|0|4000|
|15|player|3067C|3067C|同上|4|0|2016|
|16|player|36554|36554|同上|4|0|2000|
|17|player|345C4|345C4|同上|4|0|4000|
|18|player|3558C|3558C|同上|4|0|4000|
|19|player|30E74|30E74|同上|4|0|2000|
|1B|player|3166C|3166C|同上|4|0|4000|
|21|player|32634|32634|最後列index替換|2|4000|4000|
|22|player|335FC|335FC|同上|2|4000|4000|
|23|player|36D4C|36D4C|max舊值與最後列index|4|0|2000|
|24|間接owner|469C|469C|同上|4|0|2000|
|27／28|間接owner|B560|B560|最後列index替換|2|0|2000|
|2A／2B|間接owner|BD30|B560|同上|2|0|2000|
|2C／2D|間接owner|C500|B560|同上|2|0|2000|

所有count0分支都把cached high-index清零；不是用max保留舊count。
page由最後列index `(index-1)/25` 計算並限制不小於0，cursor取payload4。
這些是client cache效果，不是server對count、page、cursor或權限的發給規則。

mode1只接19／23／24，其他selector直接return；mode0接上表18種。
1C／1D明確return，其他未列selector亦沒有資料列消費。005118E0入口>=2E return。
因此表不能順便當成「0..2D都支援」，不能替未消費分支製造空清單。

27..2D共用B560的count/page/pages/cursor，其中2A/B和2C/D卻寫不同rowbase；
以單一selector分別儲存翻頁狀態會違反這個原生alias。未恢復對應server分類，
不直接讓六個selector共用一份假rank資料。這是後續共用權威分類的必要依據。

## primary初始化依據及來源範圍

0050EB00直接呼叫釘定_memset0074FC50，三個現有channel的列區域分別為
player+30E9C／player+36D74／[player+1C85A8]+46C4，各清2000bytes；
呼叫點0050EEF9／0050EF0C／0050EF3C。不能僅由頁數4推成100列capacity。
selector1B的清除從base+16起共4024bytes，包含24byte摘要及4000byte列區域；
selector15的2016bytes多出16byte，來源保留完整原生clear值，不改成2000。

`rows_within_initial_clear()`保留所有格式正確的原始rows，但對「限定範圍來源發布」
要求index在1..floor(clear_bytes/40)。目前真正接入SharedDirectory的19／23／24
因此只發布索引1..50、完整落在已追明的初始化資料列區域的原始B0。
這是明列的來源範圍守衛；不是宣稱原生decoder具有相同檢查、不是完整配置容量
證明，也不是把範圍外一律宣布為官方非法。更大範圍的真實變體仍待原生依據。

`CnDirectoryWire::read_page`改用此共用布局reader作結構讀取，保留原有channel
三種及mode1欄位意義。SharedDirectory輸出新增完整列區域條件，必要的
權威qualify_delivery仍負責真實字串終止、角色／洞府身份、資料版本與規則。
新增完整矩陣reader可供其他18分支後續來源串接使用，但沒有因此增加空handler。

## 仍未完成與計數

未恢復所有client allocation/capacity、清單分類、排序／積分／30天規則、server
權限和實際backend；三清單正式分派、完整登入／世界值供應仍待接續。
本輪新增native B0布局形式15（18-原有3），明列這一個consumer的21種mode/selector；
這不增加opcode值、phase/opcode association或partial owner chain。
本輪完整路徑新增0，全遊戲總數／已完成總數／百分比仍unknown/null。
帳號存檔、聊天、IME、認證、頭像、原生字體、客戶端與繁簡轉換保持。
