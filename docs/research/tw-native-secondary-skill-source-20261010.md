# 台服次技能清單接既有發送與C35來源，第246輪

本輪修改6個既有C++檔，補上獨立 secondary 清單的資料投影、有序S87發送及C35來源資格。既有 primary 類別／factory名稱保留相容；沒有把primary100項銀行套到secondary，也沒有建立普通戰鬥入口或猜測初始技能。

## 實際來源與資料

same149c原生secondary selector為unsigned BYTE+2D10，銀行數3、stride0x54。每銀行保留10個原WORD、10個nullable完整definition、10個auxBYTE、opaque+46兩BYTE、rawDWORD+48/+4C與signedDWORD count+50；selector旁的rawBYTE+2D11及+2D12兩BYTE也保留。所有active與inactive資料由真issuer明確提供。10是owned安全幾何，原writer未檢查此容量；負count及超過10的輸入仍不在此來源子集。

模型增加optional完整secondary snapshot，缺席時仍維持舊primary-only供應者，但secondary S87／side1請求不能借primary資料或自動補零。nullable pointer由optional完整catalog row取代，不以客戶端地址作權威。所有present的secondary定義（包括inactive tail）在registry before／next／select重讀實際same-Context完整catalog。

S87原WORD bit14分流secondary；kind/id只取low14，bit15為原啟用狀態。真consumer51C6C6..51C7BF按signed count及原順序略過NULL，首個same definition kind/id僅替換舊WORD bit15，並更新同ordinal auxBYTE為0/1。未匹配才append完整incoming WORD、definition、aux與count+1。其餘銀行、尾資料及opaque欄位保留，無primary page／S38 state／獨立aux-search。unsigned selector>=3為原生no-op；缺secondary snapshot仍拒絕。S38只影響原primary，不切換或清除secondary。

## 發送與請求串接

真registry的apply87與publish_updates現在接收secondary route bit14，完整aggregate仍沿第245輪同一held buffer／actual async_write／game before-and-after／exact private previous ticket／pending barrier。沒有另一套猜測sender或成功receipt，也沒有改Session傳輸與既有world路徑。

control A==0且B!=0才取secondary，actor為真BYTE+52／side1；A非0仍走primary BYTE+51／side0。C35本身不能選另一套list或替換controlled actor。既有command source保留raw actor／side與issued選擇／WorldOwner qualification的雙重吻合，去除原先無條件side0硬拒。缺任何真WorldOwner、catalog或完整資格仍不執行action。

原生51B900完整pointer accessor先驗fullsigned ordinal>=0且<count。真正secondary enable leaf為51B760，檢查nonnull row及原WORD bit15，並非auxBYTE；該leaf自身缺負index guard，不能獨立暴露給任意ordinal。實際compound515443..515474先驗W==0／B==1、pointer nonnull，再以同ordinal查enable，之後才進入未展開的UI分支；後續selected DWORD寫入另保留。

C35只攜帶definition kind/id，沒有UI ordinal。secondary的key→ordinal仍明示為受支持的owned first-nonnull-key投影，尚未恢復原生secondary key-search；disabled首重複不重試後面的項目，不能宣稱所有原生重複／UI選擇都已覆蓋。bit15、catalog／存檔技能與socket寫出均不是回合授權。

## 上游缺口與接續

封存的51BD70 reset資料prefix清3×0x54資料、raw48=0/raw4C=1、設定selector rawBYTE，並另存原caller DWORD參數到+2E34。該額外參數及後續GUI calls未接模型，不能當作完整init或授權；本輪也沒有實作reset呼叫或拿它補造實際非空初始清單。

普通battle-entry actor／roster到saved deity row／revision／provenance仍缺真綁定。現有Application的S87 caller只屬CUSTOM診斷技能126／150，pk_rooms尚缺RoomAuthority，均不能移作普通native入口。已學技能的完整saved readset可復用，但不能製造bank flags、inactive tails、aux或control。下一步沿既有111323／111667／11BBEA／11BC01／11BC18／11BC21的roster selector資料關係及11C4F0 reset footprint恢復真正initial來源，接普通producer；並續補grant、MP cost／refund、rules、once durable settlement、完整reply及Main。

## 本輪帳目

6改0新C++，混合TW/CN部分來源230→231；新增完整雙向玩法0、opcode0。TW C2S156、world S2C252（230固定／22變長）、battle索引110保持。它們是不同索引，不能相加當功能分母；231亦不是已完成台服路線數。台服完整方向／階段／狀態／變體分母及完成百分比仍未知。

原生11段743B、224指令位置；新局部exact capture161B，全域新增覆蓋未證、記為0。保留初版7段及後續enable refinement的獨立原件。未build／test／compiler／runtime／native／codec／遊戲DBSQL／migration／deploy；共用/CN/web、凍結功能與所有數值要求保持，goal active，台服優先繼續。

完整before／候選／來源／獨立子代理封存：
C:/Users/risei/.codex/artifact-archives/god2-server/20261010/tw-native-skill-issuer-source-246
