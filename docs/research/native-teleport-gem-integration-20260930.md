# 16055 傳送珠：原生欄位與有界回城接線 — 2026-09-30

## 新增的確切證據

承接 `native-teleport-next-20260930.md`。本次不是把缺失重述成結論：已執行
當前客戶端相符的 metadata parser、背包使用與快捷producer、剩餘次數tooltip、
完整物品接收consumer，以及指定單一選項的menu/selection/cancel鏈。

Client SHA256 `9be38ef858bc9c63b6f296cae4a8e601ddcfaf614700e725c4bec44065b53336`；
mapped image `149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`。
工具 `tools/strike_lab/current_teleport_gem_20260930.py` 對metadata全部允許code spans，
並對use/charge/menu實際執行的623個instruction地址及3B/41的280個地址，逐byte
與當前PE比較。該offline工具不啟動客戶端或服務；本輪不使用退休語料，不修改正式DB。

| 已執行範圍 | 測例 | 結果與限制 |
| --- | ---: | --- |
| 原生16055使用與快捷request | 30 | slot0/12/29 × charge0/1/10/11/127 × 兩種route |
| 原生producer busy gate | 6 | 非零UI+866E4禁止queue |
| 原生剩餘次數顯示gate/format參數 | 1024 | 全128個高7-bit值 × 全8個其他flag組合 |
| 完整原生3B/41 instance投影 | 16 | 兩slot、四charges、兩opaque flag組合；20bytes及周圍slot保留驗證 |
| CUSTOM單選menu原生資料鏈 | 1 | 6D接收、row enable、selectedID5、99queue、清body、86cancel |
| C++ `RecoveredTeleportGem` | 69129 checks | /W4 /WX；全type、charge、保位更新、20bytes投影 |
| C++ `OwnedTeleportGemOffer` | 104 checks | /W4 /WX；state、owner、CAS snapshot、期限、取消、混合封包、重播 |

原生向量來源與逐筆結果在 `artifacts/research/teleport-gem-20260930/native-normal.json`；
`native-optimized.json` 是同一工具的Python `-O`執行結果。C++收據在同目錄的
`cpp/result.json`、`offer-cpp/result.json`。這些是offline證據，不等於實際menu点击、
服務器TCP、扣次/位置原子提交或重登驗收。整合代理後續各自記錄runtime驗收。

## ItemType與C2S opening

Current gamedata SHA256
`70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731`。
MIS02 item16055的來源line13847、decoded byte offset1374939、原始row SHA256
`ca679d5fafe19b5b7351d136fd7785b1469ffa3b40dfda40181f5768f575fb6d`。
原文名稱「高級傳送珠」，描述可選傳送地點、使用10次後消失。

`459380` 原生ItemType lookup給MIS02 ordinal33/selector24；`459420`解析該行
396byte metadata得到flags+11A=`E1`、flags+11B=`00`，icon group41/actionFFFF。
bit0可使用、bit2非裝備、bit3非target picker；+11B bit0未設，因此原生3B不是堆疊
加數的分支。原文10次是內容證據，沒有證實掉落、授予或新物品初值的server規則。

- 背包 `49A330(slot,4)` 經 `459A60→496350→4132E0`：
  `25 | B7 3E | slot_u8 | opaque_tail_u8`，共5logical bytes。
- 快捷 `496390(slot)→4963C0→459A60→4132E0`：
  `26 | own_actor_u16 | B7 3E | slot_u8 | opaque_tail_u8`，共7logical bytes。
- 兩種producer都不傳charges、不修改instance；連charge0、11、127 fixture都能送。
  因此server必須依owned保存值決定是否使用，不能信任client先擋無次數物品。
- UI+866E4非0會擋producer。普通使用另有視窗gate；它不能取代server的ready、
  pending transfer、battle、owner及slot read-set檢查。
- 這兩條client使用路徑沒有呼叫4F6360或4F6B30。S2C6D由server供給；
  **25/26→6D與context16055是CUSTOM-0057的接線決策，不是假稱原server因果已恢復。**

普通event的tooltip49B820在使用測試中只跳過呈現；metadata查找、條件、producer和
queue均執行原碼。快捷route無此呈現adapter。

## Native instance中的剩餘次數

S2C3B帶完整20byte instance。其第一DWORD以LE解讀：

| bits | 本物品用途 |
| --- | --- |
| 0..15 | item ID16055（3EB7） |
| 16..21 | instance type8，原生tooltip jump table導向4BA6F4 |
| 22..24 | 此次不解讀；更新時保留 |
| 25..31 | 剩餘傳送次數，原生只顯示1..10 |

`4B6424..4B6440` 解type並跳表；`4BA6F4..4BA763` 明確比item3EB7、mask
`FE000000`，拒零及大於`14000000`，再 `shr eax,19h` 交給format。ProgramMsg890
（line2916）為「剩餘傳送次數:」，891（line2917）為「次」。工具停在sprintf之前
檢查原生組好的參數，沒有用重寫formula冒充原碼輸出。

`src/protocol/RecoveredTeleportGem.h` 提供 `matches`、`displayed_charges`、
`with_charges`。最後一者只換byte3的bits1..7，保留其bit0及其他19bytes。
0值只代表原生tooltip不顯示次數；耗盡時刪除物品是獨立CUSTOM-0057持久化規則。
勿用 `StoredInventorySlot.count` 取代charges，勿把weapon-only overlay擴充成MIS。

完整回投使用既有 `RecoveredInventoryProjection`：先41清slot，再3B全20bytes，
最後41設絕對count1。原生498DD0/4991E0無stub完整執行，16個投影案例保留opaque
bytes、count旁的reserved bytes和其他slot。這是接收證據，仍沒有建立道具取得權威。

## CUSTOM-0057最小選單與state

`src/handlers/OwnedTeleportGemOffer.h` 是專有header-only transient service。
綁定session/account/character、area2/scene0的完整position/revision、slot完整
`StoredTeleportGemSlot`（含metadata/provenance/revision）和60秒期限。

- `claims`只認領16055的25/26、context16055的selection，以及有pending offer時的86。
- `preflight`准一個操作及ticks；25可帶一次隨後的1F00，其他混合操作整批拒絕。
- `open`要求ready、不在battle/transfer、合法owned count1、type8、charge1..10；
  26還必須target為自己。開menu不寫DB或扣次。
- `select`要求99/context16055/destination5、相同owner、位置/slot完整read-set和期限。
  stale snapshot或失去state資格清掉offer；返回Prepared，尚不算完成。
- repository成功原子commit後才呼叫 `committed(session,token)`；失敗可重試有效offer。
- `cancel`只比86低WORD自身actor。高WORD是client pointer殘值，不是context。
  只清offer，不寫DB。離線由 `forget` 清掉；所有呼叫在既有serial game executor。

Menu使用context3EB7、SystemMessage280（當前SystemMessage line355，選擇地方）、
count_flags81、minutes0、display-level10、單一row `{id5,opaque0,cost0}`。
display-level10讓native顯示numeric zero cost；這不是角色等級或原生免費門檻的斷言。
數字選值、无額外貨幣扣款、只扣既存charge1、單目的地和timeout都須留在CUSTOM0057。
native header會使用其既有SystemMessage517；原生UI字串不建立server費率或等級權威。

驗證輸入及輸出：

```text
S2C menu: 6d b73e 1801 81 00 0a 00 05000000 00000000 00000000 00000000 00000000
C2S select fixture: 99 b73e 05 0e
C2S cancel fixture: 86 0400 7f0e
```

最後的0E與0E7F是fixture UI指標殘值，production decoder不得硬編它們。
原生6D接收exactcopy28bytes、page0/1，4F7090呼叫真50CAA0使row0 enabled=1；
4F7160把row0的ID5保存，不是把index0當目的地；4F72B0送99並清body。
只5077C0/50D010文字呈現被記錄/跳過；接收時使用inactive dialog，沒有冒充實機open。

## 首期位置來源：已驗證楓華入口

目的地label5=楓華，area2/scene4/kind0。CUSTOM首期選既有來源點 `(56,75)`，
不創造落點、不套用atlas座標，也不把它升格為原傳送珠的官方到達位置。

- `artifacts/world-atlas/island01-all-boundaries-routes-2-0.json` SHA256
  `f88a1a045016f520d2f478f4bb43e6fb747bd05c16146785a2eb47522bd2fe65`。
  `pairs[0].town.arrival=[56,75]`；CityI1 MDL placement offset38284、placement hash
  `e0fa60df522a4dcac50a9d4424f5b5309f094c5d6dfa160bf9fc66699d3b1938`。
  MDL file hash `bb2b72c2cb368ad9e91046783e1c9638ef02318f589cf462f0c45bbfdce04618`。
  點由native49BB0轉換；作為arrival的配對原本就是CUSTOM0036。
- `artifacts/playtests/private-island01-presence-20260927-04/run-result.json` SHA256
  `920da90a753cea01063a4c8a7b68e91dd26de66390da255f6df5a34a9309943e` 的
  `ui.return.source_arrival=[2,4,56,75]`，成功context receipt及coalesced native首步57,75。
  同receipt讀到56,75 native navigation=1，area2/scene4已具有nav/coldrestore支援。
  此receipt是舊6bf客戶端接受既有parent route，不是本輪傳送珠的驗收。

首期只允許area2/scene0→這一楓華入口，沿用已支持的同area scene0→4 transport。
需要既存完整instance；不因feature啟用就grant10、補scalar-only物品或改其他角色保存。
其他四城、任意跨area傳送、取得方式、正式服原始費率與冷卻仍未資格化。

## 歷史玩法資料與CUSTOM平衡範圍

2026-09-30查閱使用者指定的Bahamut wiki8591及17173。可用的歷史正證據是
[Bahamut「特殊道具相關」](https://wiki2.gamer.com.tw/wiki.php?n=8591%3A%E7%89%B9%E6%AE%8A%E9%81%93%E5%85%B7%E7%9B%B8%E9%97%9C)：
其高級傳送珠條目描述單人使用、可選目的地、十次後消失，並把楓華鎮列在可選位置中。
這與當前MIS02文字及原生1..10次tooltip範圍相容。該頁列出的其他區域和城鎮不構成
本輪server已完成的清單，亦不能證明所有歷史版本的numeric selector相同。

存取限制：直接開頁回403，本次使用搜尋引擎返回的該頁索引內容；來源未與9be版本
綁定，屬歷史社群佐證，不作封包或服務器權威。對17173執行限定網域的「高级传送珠」
及「传送珠」查詢未找到同物品契約；找到的
[17173仙界傳專區](https://xjz.17173.com/senso/senso.htm)介紹傳送神獸而非16055，
因此沒有把神獸規則移植給傳送珠，也不把搜尋未命中說成全站沒有資料。

歷史頁沒有給本物品額外金錢費率、cooldown、封包context或到達座標。CUSTOM-0057
採每次成功提交扣既有一次、無額外貨幣扣款；取消、開menu、stale/owner/state拒絕
不扣次。保留全instance、禁止從scalar補10次及同交易更新位置，是目前有界設計。
楓華(56,75)來自上節已有nav及coldrestore驗證的入口；沒有使用二代坐騎資料的
楓華(104,84)，因其是另一物品family。此實作不宣稱恢復原服費率或全城市傳送。

## 實際UI驗收接線資訊

以下offset全部hex，由9be匹配的4F66A0/50C9F0/418B80確立；後節另列真正客戶端收據。

1. 傳送dialog index=`int16(UI+232E38)`；list=`UI+79108`。
2. row0的hit index=`int16(list+1C)`；inputBase=`uint32(list)`。
   entry=`inputBase+hitIndex*18`，DWORD0必須為1，RECT在entry+4的四個signed32。
   list+148的DWORD必須非0才是可選row。使用此live rectangle中心；不是普通control。
3. 點row後確認`uint32(UI+790E0)==5`，再点dialog control3。
   關閉/取消是control0或4，發86。
4. 靜態預設row0 rect565,273..771,291，confirm control3 rect755,508..779,531；
   視窗可能移動，實機應讀既有live hitrect並使用普通window input，不能據預設盲點。

完成標準仍需獨立TCP和真正客戶端：開menu不扣、取消不扣、選擇只扣一次、最後一次
清slot、position+charge同交易、pending receipt、source scene離開/target presence、
掉線重登恢復，以及重播/stale/mixed/foreign拒絕。以上offline PASS不替代这些驗收。

## 實機驗收準備與失敗收據

`tools/strike_lab/private_teleport_gem_20260930.py` 使用既有owner批准的隔離桌面
runner；原client唯讀，另建只改連線port的副本。只對本工具建立的視窗使用一般
window messages；handle=VM_READ/query，無memory write、native函式注入、截圖或
輸入桌面切換。測試選單以live原生hitrect點擊，native資料與DB並行核對。

fixture取上一輪已通過的 `private-pet-reserve-20260930-03` 存檔複本，保存位置
2/0/474/209；專有test importer `seed_owned_teleport_gem_20260930.cpp` 只接受
`artifacts/playtests/private-teleport-gem-` 路徑，對已存在的char4/slot12 scalar
呼叫 `save_existing` 匯入full20。metadata為明標CUSTOM_TEST_NOT_NATIVE的2次測試
instance，不是取得或grant10規則；importer不建立scalar、不重設已有overlay。

保留所有失敗收據：

- `private-teleport-gem-20260930-01`：舊pet1 fixture保留不合格deity row100，
  strict world restore拒絕，尚未執行gem。改採已qualified的pet-reserve03來源。
- `private-teleport-gem-20260930-02`：81bcf822候選已把full20及count1正確投影到
  原客戶端；但隨後舊diagnostic town bag restore對16055呼叫scalar投影而拋出
  `Unqualified owned bag projection`，導致斷線。此是actual integration缺口，已交
  主線修復generic bag loop，而非把該失敗當成menu沒有原生支持。

兩次收據都確認source檔案未變、更換桌面未發生，且本工具建立的進程已結束。

## 最終候選實機與TCP結果

最終候選 SHA256
`b94ea3dda7bd8c5de8023f2dbaa8be7391d1f72f0b3feac66d2cabca84effc2c`。
主線修正兩個generic bag restore loop，讓已由專有route恢復的16055不再進入scalar
投影。`private-teleport-gem-20260930-03/run-result.json` **accepted=true**，SHA256
`324ae3cc2fb8ab3ec55b3bf202e7b5210b85b754e8e9db092768d5b2ddfc4979`。

原客戶端9be、普通window input實際完成：

1. bag slot12 doubleclick進入已執行原碼驗證的C2S25 producer，服務器開6D；原生
   menu body與28bytes完全相符，row0 enabled。開menu前後charge及position不變。
2. 點control4取消、menu關閉，資料不變。再從背包開啟同menu，點live row中心
   `(668,282)`；原生selected ID確為5，再點confirm `(767,519)`。
3. 99被owned route接受，slot revision1→2、full20由`b73e0804`開頭改為`b73e0802`
   開頭（2次→1次，其他16bytes相同），count維持1；位置revision1→2到2/4/56/75。
4. 原生61 consumer完成kind1/scene0→kind0/scene4換圖，世界座標確為56,75。
   原客戶端回C2S1C `04000000`，server記錄`DIAGNOSTIC_TOWN_SCENE_CONTEXT_ACCEPTED`。
5. 結束該client，再啟動全新client登入；full20、count1及2/4/56/75全部恢復，所有
   保存資料在重登期間不變。除本slot與position外，其他資料表內容及schema均不變。

收據同時確認原client/source DB/source config、候選、private copy不變，桌面一直為
各次唯一God2Lab桌面而非Default；兩個client及該次server/runner全數結束。只檢查
原生資料、enabled/hitrect及回覆，不宣稱pixel/screenshot畫面品質。26快捷路線由
offline oracle及下述TCP覆蓋，本次實機使用的是背包25。

獨立repository lane的最終TCP收據
`artifacts/research/teleport-gem-tcp-20260930/final/result.json` 為同b94候選 **6/6 PASS**。
覆蓋26 self開6D、99與位置/charge提交、86取消、最後一次耗盡和重登，以及本次發現的
town quest restore組態回歸。詳細拒絕與transaction範圍見`teleport-gem-review-20260930.md`。
原生oracle normal/-O輸出完全相等，`optimized-equivalence.json`保留確認。

結論限於 **owned完整16055在area2/scene0，選楓華5，扣既有一次到area2/scene4/56/75**。
仍未建立正式取得/發放、其他城市或跨area權威，沒有補給舊scalar10次，也未測本實機
流程的多人presence可見性。上述結果不能稱全世界傳送、全社交或全封包完成。
