# CityI2 出生區離場 frontier：2026-09-27

## 本輪結果

只讀當前台服資產與釘定重建 image，未重跑126,126→50,124的五種BFS，
未修改runtime／Lua／正式配置，未啟動client或服務。
**新增可授權跨地圖route：0；新增world NPC placement：0。**

新增具體線索是兩條NPC下凡流程、journal31／73、相關當前模板，以及傳送珠
真正的原生item request入口。這些有明確來源；尚無完整NPC身份／世界座標／
到達點join，不能當成已可下凡。已串接的CityI2↔Island03不增加本輪分子。

工具：`tools/strike_lab/current_kunlun_exit_frontier_20260927.py`。
機讀證據：`artifacts/research/kunlun-exit-frontier-20260927/evidence.json`。
收錄267 tiles／267 models／1092 placements中的140筆門、台、碑柱塔、傳送與
attached geometry候選；11筆對話、16筆journal／catalog補充列，以及10筆ROM action
header。每筆保存原始欄、offset、bytes／hash，沒有把geometry位置改名為NPC spawn。

## 出生區中可以追的三條NPC流程

|当前來源 |精確條件／動作文字|原始列SHA256|
|---|---|---|
|NPCMission01.csvZ line936、text934|狗洞下凡；先脫仙衣再交談|`af119099e11fe7b5adbd17d65be83a4d190818d5bcb7a4cc450e12004e1a1bf3`|
|NPCNormal01.csvZ line995、text993|返回崑崙後，跟「縛仙陣外的仙童」交談送回人間|`771fc802e0b98318d21a946abac19f77fb3dfe742d2f56cc4b4152a9d4805fbd`|
|NPCNormal02.csvZ line637、text1635|中央轉生台找元始天尊完成修練|`39a38e48dac056f65e11d15403a3d03e02136ebef6845e1f7054424d565e225a`|
|同檔line638、text1636|天尊回應執意下凡|`53ccbae84cb5d38eecb2d6dbbba7ec878374992695e172deb2a04ac41ff3ddf3`|

三檔source SHA依序為`1ff497204b5cf77cbbccffdf1836d7aeee30e46980ac1e85d8d0a08a0a4bcda7`、
`80750b0041db5284e598237c11ecee8ccfefa0121500919dee99fe098fcc4db0`、
`84a7ea509e4da4fbcb6b971d5c2f149fb944311aa4654f6c6c913267ed4335fa`。
raw rows均strict CP950成功，完整原文與decoded hashes在JSON。

新補到的**journal73「天尊的試煉」**在Mission_data lines459–461，要求恭讀房
134,151學合成、神仙秘室197,124附近選神、練功房185,99獲認可，再回天尊。
這是顯示描述；不補出精確技能等級、神仙鍵、battle模板或完成旗標。

**journal31「仙鶴道僮」** lines122／123把天尊與狗洞兩種下凡都接到楓華鎮
仙鶴道僮119,119。當前Map_City_Coordniate line21082可把楓華鎮名稱join到
area2/scene4。**119,119是尋找NPC的提示，沒有證明為到達點。**
相同來源area4/scene3是line21097；其318,363仍是map資料基準，不是出生点。

gamedata NPCAppearData還有line1822 template3062「二轉狗洞仙童」與line3590
template5388「狗洞仙童改」，以及line308 template760「元始天尊」。
這提供下一輪查模板的鍵；「二轉」需保留適用條件，template key不等於C2S37的
world identity，不能用3062／5388直接綁text934或新增假座標。

## 精確圖像模型與可達分量邊界

50,124來源是placement433（decoded MDL offset63905），model／tile199：
**碑柱塔#C3 → ROM index17 Monolith.ROM → action1018**，同名ACT_DATA
header hash`e7d2102b3deda632dadcac5398da0277da93d446ac3da57a51f51d66dcc36e1f`。
placement原文欄`[199,1080,500,53,121,0,327,351,1,0]`附著`..\Island03.mdt`；
model只開pair2 `[0,6]`，原生49BB0投影得50,124。它**没有轉生台／狗洞／NPC文字join**。
本輪strict CP950訂正其名稱；先前replacement解碼不能作命名權威。

全267tile名稱沒有「狗洞」、「法陣」、「轉生台」字面命中。
tile258「傳送2#M01」→MARK2.ROM/action1001及tile266「傳送#JJPP001」→
Mark.ROM/action1001在CityI2均**沒有placement**。tile261..264有placement，但
附著GR01..04.hmd，正是既有四神仙房；不是新增對外傳送。

借用上輪保存的**reachable conflict targets**，没有重建或搜尋路徑，可精準對到：

- 巨門#BD03／BigDoor.ROM1003、placement513：139,125與139,126；
- 門們#D1L／Door.ROM1001：placement231的167,88、426的185,105／186,105、
  764的185,142／186,142、929的167,159；
- 已有練功房placement420的185,97／186,97、伙房765的185,152／185,153。

這表示上述點曾出現在原生window可走的舊證據中，**不表示全部140geometry都在
出生分量，也不產生新的完整path**。內部門模型13／14／23／24／27／28均空
attachment、target欄-1；不把成對圖像自動接成傳送。

原生資格鏈：完整`00441F90`初始化object+1C／+20=-1；`0043EE20` loader保留
MDL target欄，attachment由`00437540`寫string+34；`00437230`讀該字串。
`00449040`的`0044910D..0044911E`要求string length>0或object+1C>=0，否則
BL=0，後續`00449127..00449129`跳過entry比較。原生slice三組執行全部符合：
空字串/-1拒絕、有字串/-1接受、空字串/0接受。
這是**精確eligibility slice**，不是完整loader／classifier畫面驗收。

## 可直接接到後續own-server lane的封包入口

原生item click入口`004963C0`對owned正數背包slot，item/100為53或55時呼叫
`00496350(item,slot,1)`；後者要求UI+866E4=0，經`004132E0`排入：
`25 + item WORD + slot BYTE + opaque BYTE`。
本輪完整原生caller／lookup／producer／queue返回三次：
5501→`257d150400`、5504→`2580150400`、5571→`25c3150400`，explicit synthetic
slot4/count1；metadata table為空fixture，不假裝授予物品或正式ownership。
另四次直接producer測例證明opaque tail與UI阻擋。**不是C2S6D00開menu**。
56xx及16055不能沿用53/55分支；本輪未資格化其正常click路徑。

既有原生NPC互動入口`00466D75..00466E1B`要求pool identity及角色到NPC的
兩軸距離各≤3、hit37；`00496750`要求合法identity及tick差>1000，再发
`37 + world identity DWORD`。dialogue consumer／producer為既有7A／85／86。
此wire可沿用，仍需先取得狗洞／仙童／天尊的world身份與source position。
6D→99/A9已有display／selection contract，**沒有25或37→6D的原生權威配對**。

### 下一輪實裝需要的最小證據

1. 優先釘住journal31／73與上述NPC模板，找到source world identity、area4/3
   position及text934或1636的真正選項／request join。
2. 提取跨area4→2/4的到達座標、資格／衣服／任務旗標規則及實際61／context
   回執序列；目前Movement `begin_transfer`仍校驗source area等於destination area，
   不能把same-area parent primitive直接當下凡完成。
3. 若只採傳送珠作own-server fallback，25入口已資格化，可開始ownedslot/完整
   readset/CAS/pending設計；目的地、消耗與25→6D pairing仍須清楚列為CUSTOM並
   current-client驗收。不能因道具描述為「最近城鎮」就補出原生算法／到達點。

目前三條NPC文字線及item入口都沒有完整跨區authority；本輪因此只提交研究
receipt與具體下一步，不修改出生點、放寬碰撞或新增production route。
