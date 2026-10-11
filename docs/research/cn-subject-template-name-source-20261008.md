# 陸服 WORLD30 低 ID 名稱來源

本輪 `20261008-cn-subject-template-name-source` 接續145。
PHASE1靜態來源工作，未建置、測試、原生／C++／API／SQL執行或部署。
原生EXE、資料、歷史紀錄及既有凍結功能保留。

## 原生資料關聯

144已資格化 WORLD30→004D5B20：signed BYTE取絕對值，低ID<100
使用真正resource owner65364呼叫004283A0(ID+AF0)，取返回row+8的名稱；
null使用007EFB9C的SPACE+NUL。ID0與名冊容量滿先返回，沒有名稱lookup。
高ID使用原封包的inline string，不能用這個模板表代替。

004283A0讀unsigned WORD key，key<35000才讀resource+B304C+key*4；
不是NPCAppearData的direct-index name表。00428860將這35000個pointer
清零；00428C80在ItemType描述的區段逐行讀column0正數key，為每個
396B item配置實際row，寫同一pointer表，再呼叫0042CFB0。
0042CFB0通用name分支讀column4到row+8，明確row+2D置NUL，與後續
type-specific switch獨立。GOD沒有專屬primary type tag，不臆造type enum。

當前encoded SHA256為8a72d850a34b14170c4cb0e91da9430559ea7def4e047130c533d666d67b893a；
decoded為16f7bb0f9cdf2965719408204800b329269c810821b96d3d81b5feca168534a3。
只讀既有decoded receipt，不再執行解壓器或native loader。
ItemType第三筆描述2801..2899的GOD區段。實際`GOD,34` header位於
decoded415519／physical line6609，34筆位於415527..416611，key2801..2834。
全部6欄、CRLF、沒有quote／NUL、column4為4..10個CP936 bytes，
沒有觸及37-byte名稱上限。保留原始行、雜湊、offset、line及未解讀欄位。
所有ItemType區段再盤點2801..2899，沒有其他區段覆寫這34個key，
35..99為65個缺列，不能補成NPC名字、預設神仙或能力值。

0042D540也能寫同一pointer表。Current必須由真正source owner維護並在
相關資源或覆寫變更時失效；固定file hash不能證明native runtime已載入
或没有變更。native process memory不是自建服務端的運作前置条件。
本輪只提供釘定來源的projection，缺列SPACE僅適用於該來源／revision
語義仍成立的條件；不能覆蓋其他resource epoch或動態替換。

## 後續 UI helper

004D4B80讀role+D4的實際active prefix，從role+DB（第一row的name+3）
按stride3EC更新tab label，active enable=1；其餘至16的slot用空字串
007EE88C及enable=0，最後以signed BYTE role+CF選取tab。
這是名稱／標籤刷新，不是清零inactive row、生成屬性或分配技能。
004D5030是已於142追查的selected-row panel reader，也不能算初始化公式。
只資格化局部入口CFG；helper內部、例外、全圖與runtime仍未完成。

## 來源接合

新增`CnSubjectTemplateNames`：接收真正revision／Current與釘定encoded／
decoded copied inputs，解析34筆實際GOD行並保留provenance。低非零ID
1..34返回相應名稱，35..99返回有來源條件的SPACE+NUL，0／>=100不走
此lookup。沒有UTF-8改写CP936、名稱正規化、NPC fallback或資料庫匯入。

既有`SharedSubjectRosterPublication`接收可選同一模板supplier；任何實際
非零低ID30必須有current supplier。逐record的optional lookup與原本
definitions、Plan、Framing對齊，在BeforeQueue／QueueAccepted交給
同一真正post-commit owner，並由completion保留。高ID原bytes與名字
邊界保持原先資格化，0／容量／reset／select及全部native wire不變。
名稱證據不是common ID、可召喚權限、怪物雙攻雙防或技能所有權。

真正common roster／inactive row／recipient／identity／字段語義、Lua規則、
存檔、durable replay、committed issuer、supplier Current及Application
尚未配置。本輪新增名稱supplier1、既有publisher名稱handoff1，
新opcode／phase／owner／完整雙向路徑0；全遊戲分母／百分比未知。
完整TW/CN/PC/網頁/WSS、全部玩法、numeric64、堆疊99、集中測試修復
與可恢復發布目標保留，仙幣99999999999、其他上限另定、等級不改。
