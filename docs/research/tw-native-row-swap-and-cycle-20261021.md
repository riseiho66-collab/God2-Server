# 台服 action9、動畫邊界與返回資源：2026-10-21

本輪是 PHASE1 靜態研究，沒有建置、測試、遊戲／VM、codec、遊戲 SQL 或部署。
下文的 client consumer 不是原服 producer，也不能證明原服的配對、回合或權限政策。

## 目標與憑據

原檔 `C:/Users/risei/Desktop/God2/God2/God2.exe`，SHA256
`aaf0fae66e89c4547244304ecd8f4c2755746ffa6c9b9dfe68a0ff3fd2b4cd48`。
以既有 REA CLI／Ghidra12.1.2 做新分析，沒有改 MCP 設定或安裝工具。
分析映像只新增 analyst entry CALL seeds；13 個原始 section 逐 byte 不變，
synthetic caller 不算原生 caller，分析映像從未執行。新證據根為：

`C:/Users/risei/.codex/artifact-archives/god2-server/20261021/sos-row-timing-continuation-pass5/native`

| 新 REA 證據檔 | 內容／Evidence ID |
| --- | --- |
| formation-flee-ui-decompile-v9.json | 本輪 v2 的16個函數；歷史檔名沒有更名。`ev_e40b4c42e3d47f87255b12445cad0443631d7769cac3b2c40d6ac855c0ce8992` |
| formation-row-ui-loop-decompile-v3.json |14個 UI／queue／return 函數。`ev_4c9915f8b3340815b1ccf9480caac7cc8d61cf6aa41d4dd5f6b2d1b7122ae5c9` |
| native-queue-pet-decompile-v5.json |16個 queue、group、pet guard 函數。`ev_b5782979f4c3977adc5e0a078f7fe8fe0db32800f713738b3045587d7c8ceeba` |
| native-return-pet-hud-decompile-v6.json |10個返回／pet HUD 函數。`ev_afef4b25a1183f8df99bcab4f03ddad0dbbafa238898db8e062bc1b823487255` |
| native-entry-player-return-decompile-v7.json |4E71E0／4E7640成功，未 seed 的5112C0失敗保留；不能把失敗算成功。`ev_444de2a5f47166001a52339ecec8957258d04918ec70e874dff7fbd8e19656f0` |
| native-pet-cache-input-decompile-v8.json |8個實值 setter 及2個 UI 函數。`ev_f46ee73749d202cbe9fb209073dd575eba74baca195b1dc1f66f825871ef38ba` |
| native-entry-normal-dispatch-decompile-v10.json |加明確 seed 後的5112C0與466B00。`ev_f50d531218b6a6b53cc70b5a59cfe52202bc22a15981757834dcdab53ab30ec2` |
| native-row-ui-enabling-decompile-v11.json |50FDC0／510300／466200。`ev_963a8fd0519944a51a96af58ce7dd45f8d9a908ccc12184a8ca582f71978636b` |
| native-normal-pet-dispatch-decompile-v12.json |4858B0→FB body handler。`ev_a4b74a269628eccf7f2c585a033b5dac6bc88364e8e87a8472a5304d25791040` |
| native-normal-e3-dispatch-decompile-v13.json |468AE0 ordinary dispatcher。`ev_440a2493db5cc8083117956f597cb114013e24a45b56a2850ad8d01da9990219` |

各函數 assembly、incoming references、完整失敗資料、分析映像 provenance 與 close
收據留在同根。v4 工具分析後因重複檔名 EEXIST 未保存結果，因此不以該次結果立論；
v5 改用唯一檔名的持續 session。v5／v10 最後均 close；沒有開著的 REA target。

## action9 原生輸入及成功交換

實際 UI `513080 case9 →5127C0→5156E0→518E50(9,actor,0,B+44C)`。
count0 使兩個 target WORD 為0；封包沒有傳交換目的 slot／人寵配對。
logical4 和 DWORD13..16 在此分支沒有初始化，須保留 opaque bits，不能要求常數0。
actor BYTE<=14，sideflag=(A==0且B!=0)，context DWORD9..12=B+3C。
A/B 分別為 B+A9E9C38／3C；5156E0 只有 A0/B非0 才回 B52，其餘回 B51。
共用 cleanup 先消耗 A，否則 B；兩者歸零時設 W34=1，沒有成功送出保證。

S83/9 的52C520→52A8D0把 logical5／7 平面位置存到 source+25A／268，
把 logical WORD9 成功 operand 存到+286，準備 state97。
525B90 state97先開始 pose13，等待 renderer helper41AF90；WORD286非0才交換。
它交換兩 side×14 slot 中指定的兩位置之**全部6層 actor pointer**，同步每層 actor+234，
重取原生座標並排列 presence bits。保留的 self primary／secondary pointer 新位置回寫
呼入的 param2+9/+10；5140C0→529020的實際 param2=B+48，所以這正是 B51／B52。
WORD9為0走失敗動畫再完成，不交換；成功後也不恢復 A/B。

producer chain 513080／5127C0沒有 has-pet、target HP 或 pair查詢。
50FDC0／510300只是顯示對應 controls 與準備 panel，沒有這些檢查。
52A8D0 action9檢查 source object／renderer<1000、target object，沒有要求 target renderer
或 target HP；525B90交換不檢查 HP。2×14×6 tables 預先建構 placeholder object，
不能把 object存在誤認成出戰寵存在。因此「必須兩個活 actor」不是此證據建立的規則。
這仍不授權 dead source 或沒有 server grant 的 source；原服發 grant、UI禁用及配對政策
沒有恢復。CUSTOM-0162可明確以 authority 設定的 pair、活的已授權 source，允許另一端
是保留空格或 dead partner，不憑 incoming mask 猜 slot。

## 真正 queue 邊界，修正上一輪過寬的88推論

519370將1C／38／83..88放入51D4E0 queue。5140C0先以529020推進動畫，然後處理
同一 group 的83。已有 active83時遇到88，會先關 queue gate、**不 pop／執行88**，
改由52AC20啟播該 group。529020完成才重開 gate，之後才執行88及其52D360實值寫入。
若83後 queue已空（即使跟了86/5而後空），5140C0會提前return，不呼52AC20；
不能只發83或83+86/5便假定動畫會開始。

因此先前只看518A90直接 consumer而推定「83+post-HP88必定立即雙扣」的說法過寬。
真正 network queue 的88有上述 deferred boundary；正確 order的83→88可先播傷害，
後套 current資源。直接／eager consumer 或破壞 queue order 仍不在此保證內。
Written是網路 custody，不能代替 renderer完成。

52AC20的 expected／completed是 manager+A7FBC64／68，按 actor state完成計數。
它們與 CWar+A9E9C64／68 的88 DWORD完全不同。529020 expected<=completed 或原生
10秒 timeout可回完成；0B不能證明真動畫完成或每名玩家誠實。

52AC20 assembly `52AC2E MOV CL,AL; INC CL;52AC4F CMP AL,CL; JNC52AE0F`：
group255加1成0，直接略過全部 actor掃描，expected0而回false。明確可用label域是0..254；
在真88邊界完成後可重用label，不能讓 grant_epoch%256 產生255。

## 88 counter、0B與剩餘 control

518A90初次cache64==-1時，把 logical DWORD1 同時寫 cache64／68。後續通常只更新64，
並重置sent0Bflag44=0；6C==1是特殊抑制分支。新查516AE0在83處**清6C=0**，不是設1。
以原13sections的 exact displacement byte掃描只找到初次88直接寫cache68；這是候選掃描，
不能排除 computed alias。普通K0 loop要求64==68、sent44=0、cycleflag48=1。
所以逐回合增加grant_epoch當88counter沒有此普通分支的來源支持。固定完整 per-battle
profile DWORD是明示CUSTOM選擇，仍不是恢復原服counter意義。

515770的auto0B直接取 B51（不是5156E0），count=B45C、targets=B44C、context=B3C。
A0/B1時仍可以 primary actor+sideflag1；bothzero則primary actor+sideflag0。
0B繞過A/B輸入 gate，仍走共用 cleanup並消耗一個尚存的A/B，最後設sent44=1。
每action立即播放時，旁觀 recipient或行動者剩餘pet control也可能被這個0B消耗。
明示CUSTOM可在該人符合來源的進度回報後，僅重發其 server仍擁有的 same-epoch86/5，
不發88、不給新grant、不動damage／RNG。這是恢復既有control，並非0B授權新回合。
無nonce的0B無法證明是哪一次動畫；必須保留 server outbox／stage／owner gates 與限制。

另外，actual pass／target-gone pass若只回86/5，前次sent44已1便可能沒有下一個0B。
它需要獨立的明示CUSTOM progress policy或安全current88邊界；不能把所有grant refresh
都加88，否則形成0B→refresh88→0B迴圈。此項已交作者處理與源碼回歸。

K為B+144C1C，K非0的loop會清K並走wrapped DWORD差值JNS／sentinel分支。
S82兩DWORD→event+28/+2C→5112C0寫B+3C/+40；BYTE(B+41)另成計時值A9E9C70，
context_b低BYTE==FF亦影響A9EA4C8。完整initializer沒有直接寫K，exact displacement
掃描僅找到515A63讀、515A6B清。**不能把K等同context_b，也未證任意context_b是K0**。
固定profile counter使64==68，故K非0分支的wrapped差值也為0、JNS通過並清K；
此策略符合已觀測的兩個counter gate，不需要假認K先為0。這不建立context_b其他
mode／計時分支的可用性，亦不把counter consumer當成原服counter producer。
原服其他mode、K初始化／alias寫入及counter producer政策仍OPEN。

## 返回後角色／戰寵的實值與合法增量刷新

5140C0每frame以目前B51取 primary actor DE8／DEC／DF0／DF4，呼4E71E0參數4=0。
此函數真的寫 U86888角色資料：+5C←currentHP、+64←currentMP、+60←maxHP、+68←maxMP，
不是只更新HUD。B52有效renderer時，4AC550／360／930／740也會再呼實值setter：

- E3家族4A3980／39A0／39C0／39E0：U+A740／742／744／746 WORD。
- FB家族4A6010／6050／6090／60D0：U232EBC物件+94／9C中 current／max HP14bits、MP11bits。

這些setter還有實際panel存在／active44 key等gate，不能推成任何尾frame都已保存。
5118E0清理與所選normal重建鏈沒有恢復原服全部copyback政策；不得聲稱完全沒有同步，
也不能以每frame同步取代server committed資源的fresh return投影。

ordinary dispatcher468AE0 caseE3→4A2B70；caseFB→4858B0→4A52A0。
E3覆寫13DWORD=52B，FB覆寫18DWORD=72B；兩者接受slot42..44，並查非0 key與definition。
E3 key域0x3391..0x3778或0x5DC1..0x6D60；FB域28001..32599；handler不要求先append或先3B。
519370 battle ingress也有E3直接consumer。這支持真C1C返回後在ordinary phase，對**同一
已存在44、同一metadata family／per-instance來源**發完整E3／FB body刷新，不用S30清單。
原始全body、unknown bits、HP／MP寬度及saved pet技能來源仍必須完整保留；key域本身
不是actor／pet／Session授權，不能以模板或低位截斷代替真per-instance source。

## 尚未宣稱完成的項目

這些是可接線的client contract與明示CUSTOM修正依據，沒有原服完整server source、native
執行、實機動畫／多玩家／返回後寵物技能驗收。原服初場配對、K初始化、88counter原始
producer、死亡source的grant政策及無nonce協定的因果限制仍需分別記錄。
