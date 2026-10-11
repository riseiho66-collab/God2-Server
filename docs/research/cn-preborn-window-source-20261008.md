# CN 擬態／特技選擇：實際視窗發送與操作狀態來源

本輪 `20261008-cn-preborn-window-source`；PHASE1，目標 ACTIVE／INCOMPLETE。
接續129的81／83條件式來源，不把格式reader或來源接口算成完整玩法。
修改前保存112檔snapshot，保留129的191檔封存及雜湊。

## 原生初始化與目前邊界

固定CN映像SHA256：
`582f269535f86e95fcd77946821adf79a30d1bd33f21d566cf48c36fd221b3c8`。
所有新定位來自此PE32的file-backed bytes及個別反編譯來源，沒有載入或執行EXE。

`004ACF03`明確push0，`004ACF05`push來源array+28，
`004ACF08`把同一UI owner置於ECX，`004ACF0A`呼叫`004AF370`。
`004AF37F`保存入口ECX，`004AF399`把它恢復到ESI，
因此不能把暫時的ESI=owner+7785C誤當成後續owner。
`004AF382`保存BYTE mode於owner+77858；`004AF3C2`設定EDI=owner+1C8490，
接著FFFFFFFF／40 DWORD的rep stosd也把WORD owner+1C8500初始化為-1。
`004AF40C/40E`依mode0進入包含`004AF59A→00533DB0`的分支；
mode非0跳到004AF68C，其正常局部分支沒有這個constructor呼叫。

`00533DB0`保存與恢復同一入口owner。`00533EEC`的00451460正常返回AX
在`00533F04`写入owner+1C8500；constructor尾端`00534295`設owner+8A4=1。
這定位了視窗handle及初始化來源，沒有推定視窗立即顯示、後續A0必然到達，
也沒有窮盡preborn相對1C／pre-world的全部時機。

A0的`00534D1C`先看`*(owner+430A8)+D4`的BYTE，零值直接退出。
同一member在`004D58CD`為list count，entry從+D8開始、stride3EC，
搜尋時把payload的signed BYTE sign-extend後比對entry的WORD0；
`004D59BE/CA`更新同一role的+D0指標與+CF索引。
不能把這個BYTE當作服務端權限bit，也不能把native WORD、signed BYTE或list index
直接當成共同資料庫ID。`004D5B20`的99-byte metadata只涵蓋append前置條件，
不是整個switch；本輪不據此宣称全部subject種類、全域容量或完整回覆流程。

`00534640`還要求signed WORD handle非負，且對應GUI slot flags&10非零；
之後使用owner+430AC及該物件+160指標取得原生資料。
這個指標和role+D0的實際跨函式關係、全部原生技能資源及server資格仍待追查。

`005342B0`確實把owner+430AC所指物件的WORD0作為2-byte body，
在`005342D2`呼叫00481440以opcode84發送，完整logical形狀為3 bytes。
本輪保存個別00*.c直接函式名搜尋與PE可用section範圍的literal pointer搜尋。
沒有定位到caller不等於全域不可達，relative／indirect／computed target仍開放。
**不把84掛入ready-world，不推定84→A0配對，不新增已確認phase。**

## 已改動的實際來源

`SharedPrebornChoices`新增發送視窗入口。實際issuer提供完整有序A0／A1／A2／A3
原生records、同一lease與非零revision，以及擁有資料生命週期的Current觀測。
形狀檢查要求唯一A0及與Scope一致的兩個原生count bytes；不排序、補值或生造封包。
真正的native時機、selected subject、資源容量、可用技能、資格與費用
必須由Current及actual operation提供，count不是服務端許可。

`SharedPrebornWindowSource`實作既有WorldOwner，而非僅新增另一個抽象handler：
prepare只保存實際來源；held world batch在任何視窗bytes釋出前，
再次觀測實際來源，將相同records／revision的scope從prepared轉為issued。
只有issued scope會交給81；83沿用同一scope，先退役本地window，再呼叫一次真正共用
rule／transaction／save／replay callback。該callback仍須實作跨連線／重連的持久化重播處理。
post-commit輸出沿用129的實際revision資格化，不再讀已退役的prepared Current。
輸出失敗放棄同一scope並關閉本連線；不偽裝回復已提交的共同交易。

`SharedWorldGameplay::Sources.preborn_windows`與既有preborn_choices為互斥來源。
真正1C publication的initialize內只綁定同一controller／lease／WindowOwner，沒有發送視窗。
實際Application/source event以保留的preborn_windows呼叫publish，才進入發送入口；
綁定本身、ready lease或constructor都不表示原生觸發條件成立。
原生其他階段仍需自己的完整來源，這個有條件ready-world組合不代替它們。

## 會計與未完成工作

新增具體issued-window owner實作1、held視窗publication入口1、既有gameplay來源綁定1。
同一preborn鏈的生命週期補強，不重複新增partial owner、opcode或已知phase關聯。
完整雙向玩法增量0；全遊戲總量、完成量及百分比仍為null。

真正的native initial issuer／時機／subject映射／技能與原生格式輸出、
共用Lua規則／transaction／save／persistent replay及Application配置仍未完成。
後續繼續正式共同登入世界providers與全部TW／CN／PC／web／WSS玩法，
包含共享資料、社交、物品交易、任務、戰鬥、怪物技能、寵物、公會同盟、
城鎮室內、64-bit數值、背包99及完整路徑分母。

未建置、測試、執行C++／native／API／服務、讀寫DB、遷移或部署。
帳號存檔、認證、聊天、IME、頭像、客戶端、原生字體、繁簡轉換與等級未改。
