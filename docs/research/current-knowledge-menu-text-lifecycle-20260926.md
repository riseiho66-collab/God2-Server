# 當前1434知識選單：原文候選、85/86 lifecycle、原生命中驗證

2026-09-26；當前 Taiwan God2.exe SHA256 `6bf75ef8ac1e0f6b2240800ff841d205788bd1b6512149584b5386b10f431e98`。所有地址是 VA。只讀當前 EXE/Data2，沒有正式 DB、共享 codec/Application 修改，沒有開遊戲或碰可見桌面。只新增本報告、獨立研究工具與離線 JSON。

## 結論與可用程度

找到完整涵蓋七個1434選項主題的原生文字，但**沒有找到1434選项→NPCMission頁的原服事件對照表**。以下是逐內容匹配、可供教學閱讀路由選用的候選，不是原服 quest/server 規則。若主線把它們接成閱讀流程，應把原生文字、原生 wire/consumer 與自行指定的 routing 分別記錄；沒有NPC世界ID／任務接受或完成權威。

原生測試新增：當前PE mode1文字讀取/分页，mode4實際4C8920文字格式化與選項可選旗標，再由原生WM_LBUTTONDOWN命中、選單事件與85產生器完成關閉；完整85/86 cleanup 返回。圖形backing為empty fixture、rect為synthetic，沒有替換任何native callee return。這比之前只跑click arithmetic更完整，但仍不是正在運行的真實視窗驗收。

## 選項→教學原文候選

| 1434 wire choice | 原生label | 內容相符的NPCMission key | 来源 | 限制 |
| --- | --- | --- | --- | --- |
| 0 | 我已經知曉箇中奧妙了！我要進行下一階段的修練。 | 8779（候選）；8780較短；3022為另一現存領圖文本 | NPCMission09行781/782；04行24 | 不是普通教學頁。8779/3022包含贈圖/衣承諾，不得無條件display即當完成或實際grant。這三段不是可合併的同一事件 |
| 1 | 滑鼠功能 | 3016 | NPCMission04行18 | 逐內容匹配；無原服選項事件join |
| 2 | 介面概述 | 3017 | NPCMission04行19 | 同上；原文含新手尚無神仙/戰寵的假定，不能因此覆寫實際擁有狀態 |
| 3 | 買賣說明 | 3018購買、3019販賣 | NPCMission04行20/21 | 兩段各說不同主題；若分兩次7A串接是主線routing設計，不是已證明原服轉移 |
| 4 | 交易解惑 | 3020 | NPCMission04行22 | 純教學，不創建交易授權 |
| 5 | 組隊釋疑 | 3021 | NPCMission04行23 | 純教學，不創建組隊授權 |
| 6 | 升級點數配置 | 8786 | NPCMission09行788 | 原文說每次升級4點，但本輪只是呈現文本；沒有恢復升級規則 |

另找到NPCMission03 key2170的多主題長教學，描述的介面與3017有差異（較早式左下三按鈕等）；沒有把兩者拼接或用它覆蓋當前候選。名稱相鄰不能解決版本／條件分支。

所有上述10個候選text均無 `%` 或內嵌NUL，工具會拒絕變更後的格式字串。mode1名字16bytes全零，使用原生NPCMission表；不把NPCNormal、MultiMessage、journal ID混用。各來源hash與精確原文附後。

## Mode1 codec與原生分頁結果

使用既有27-byte logical7A形狀：opcode7A、length27、mode1、contextU8、requestU16、NPCMission keyU16、replyU16、16bytes zero name。header offsets與上一份mode4報告一致，沒有尾端count欄。

工具以loader-equivalent稀疏NPCMission表放入**當前原始CP950 bytes**，實際4C7F10選中指定字串並至4C8234；接著實際4C8780/4FFDF0分頁：

| NPCMission key | 原生page_count | threshold/bias |
| --- | --- | --- |
| 3016 | 3 | -1 / -1 |
| 3017 | 3 | -1 / -1 |
| 3018 | 2 | -1 / -1 |
| 3019 | 2 | -1 / -1 |
| 3020 | 2 | -1 / -1 |
| 3021 | 3 | -1 / -1 |
| 3022 | 2 | -1 / -1 |
| 8779 | 5 | -1 / -1 |
| 8780 | 1 | -1 / -1 |
| 8786 | 3 | -1 / -1 |

在最後一頁執行4C8500至cleanup返回，10筆都只排入85，保留7A送來的request2468、reply2、context5B。非最後一頁應透過page controls導航；mode1不使用mode4的threshold例外。

**request欄位不只是自由nonce。** 它存到5B7BFA再由85回傳，但4C81F0也把它傳給4C79C0做NpcHead lookup（resource+121E8 count，+121FA+index*5E的頭像欄）。未定world NPC語義不代表可以任意挑識別字。live候選應沿用已資格的值／確認portrait行為。本oracle不執行portrait載入。

## 85、86、進出頁的精確順序

條件：widget0、open=1/action=0、empty graphics、sourceDWORD DEADBEEF、UI指標10000000、request1234/context9A；menu choice3。下表為真正當前x86完整action/close返回的queue：

| mode | incoming reply | entry | logical bytes |
| --- | --- | --- | --- |
| 1 | 0002 | action | `85341202009aa5` |
| 1 | 0002 | close | `86efbe0010` |
| 1 | 8002 | action | `85341202009aa5` |
| 1 | 8002 | close | `86efbe001085341202009a84` |
| 1 | FFFF | action | `86efbe0010` |
| 1 | FFFF | close | `86efbe0010` |
| 4 | 0002 | action | `85341203009aa5` |
| 4 | 0002 | close | `86efbe0010` |
| 4 | 8002 | action | `85341203009aa585341202009a84` |
| 4 | 8002 | close | `86efbe001085341202009a84` |
| 4 | FFFF | action | `86efbe0010` |
| 4 | FFFF | close | `86efbe0010` |

- 普通reply2：選擇/確認先85，原生設action=1後cleanup不送86；手動關閉open且action=0會送86。
- incoming8002：4C81F0正規化reply2並設5B7BEC=1。mode4 action保留high flag，故送85(choice)後cleanup再送85(reply)。mode1 action先清flag，因此只有一筆85。
- FFFF保持負值且high flag0：確認跳過初始85，開著的頁會送86。
- 86是5bytes，不是17：payload低WORD來自`*[UI+8688C]`，高WORD來自this pointer高16bits。示範`86 ef be 00 10`不是可通用的固定關閉內容。
- 85是7bytes：opcode + requestWORD + reply/choiceWORD + contextBYTE +未初始化stack residue。第一筆尾A5、cleanup追加尾84只是本fixture殘留，不可當協議常數。
- 4C84A0是high-flag flush：只在flag==1排入85(stored request/reply/context)，然後清flag；連續第二次不輸出。當前496750的NPC互動37 producer會在通過time gate後先呼它。本輪單獨執行4C84A0兩次，沒有假設37的時間條件。
- 完整menu choice1→新mode1頁→確認→新menu choice2的隔離鏈已執行。兩次新7A header處理沒有額外排包；新header的request/context覆寫舊值，之後85確實帶新的值。incoming render/portrait邊界之外仍需live驗收。
- 打開新7A會重設stored reply/high flag。不能只靠client保存舊conversation完成事件；server必須獨立維護每次conversation與request/context授權。

## 「17 close」核對

當前world switch入口468B4E直接以opcode索引46B5D4。**0x17（十六進位）與0x11（十進位17）均指向46B517通用尾端**，沒有dialogue close handler。本輪對這兩個opcode直接跑actual dispatcher至尾端，open/action/queue/request/context全部不變。

這只針對當前world dispatcher，沒有聲稱其他階段/方向也相同。如果伺服器送17希望關dialog，本輪沒有原生證據支持；勿以17取代實際85/86 lifecycle。清除狀態需主線以已驗證consumer或真實client動作為依據。

## Live只讀觀測與click路徑

設U為owner/UI物件，L=U+CC9D4：

| 觀測欄位 | 地址／型別 |
| --- | --- |
| mode/key/choice | U+CCC1C WORD / CCC1E WORD / CCC20 signedSHORT |
| threshold/bias/context | U+CCD32 signedSHORT / CCD34 signedSHORT / CCD36 BYTE |
| open/action | U+AFF00 DWORD / AFF04 DWORD |
| dialogue widget w | U+232DEE signedSHORT |
| page/pageCount | VA5B7BF0 /5B7BF4 signedDWORD |
| highFlag/reply/request | VA5B7BEC DWORD /5B7BF8 WORD /5B7BFA WORD |
| list input-manager pointer | DWORD[L] |
| row hit ID | signedSHORT[L+1C+2*row], row0..49 |
| row enabled | DWORD[L+148+4*row] (nonzero可選) |
| list selected row | signedSHORT[L+224] |

hit entry=`inputManager + hitID*0x18`，hitID0..0xBFF；DWORD欄依序為active,left,top,right,bottom,hit。418950處理WM_MOUSEMOVE/WM_LBUTTONDOWN，以signed座標與**包含邊界**LTRB矩形算hit，418CD0只在active==1回傳hit。不得把active2當啟用。

widget control C=`U+E2170+w*0x2A08+0x8B8+control*100`（最後100為十進位）。signedSHORT[C+8]是hit ID，透過同input manager查rect。先驗w有效及C存在，避免只按猜測固定螢幕座標。

4C85B0 control0=confirm、1=close、2=previous、3=next；flags bit2（數值2）優先走close，flags bit1（數值1）走control action。實際輸入handler的mode4選擇部分呼50D8A0→418CD0後，4C8671把page/row轉成choice，4C8500檢查並送85。flags4也可從selection路徑觸發；本輪click vectors用flags1。

1434原生4C8920直接由資源建立rowEnabled（工具沒有寫假enabled）：page0=[0,0,1,1,1]，page1=[1,1,1,1,0]。七筆WM_LBUTTONDOWN用synthetic rect和hit IDs跑418950後再跑4C85B0，全部85 choice0..6並open=0。graph backing empty，所以這是原生命中/事件驗證，非實際widget像素驗收。

另外實際跑control3、3、2、2：page變成1、1、0、0；每次透過4C8920重建選項，均無85/86且request/context保留。下一頁/上一頁本身不是server event。

## 重現與限制

```powershell
C:/Users/risei/AppData/Local/Programs/Python/Python312/python.exe -O -m tools.strike_lab.current_knowledge_dialogue_lifecycle_20260926 --output artifacts/reports/current-knowledge-dialogue-20260926/native-vectors.json
```

結果PASS，約1.4秒。使用当前PE whole-file pin、current source pins、250000 instructions單slice上限、明確停止地址及強制檢查（不用Python assert）。10教學頁、12close/action情境、7原生命中選項、4page navigation、menu→dialogue→menu鏈、兩次high flush、兩個world no-op已執行。完整rawbytes/line/hash/queue/state在JSON。

No original game function stubbed; tables and rectangles are synthetic fixtures. No full WndProc/event-loop scheduling, live pixels, actual asset-backed widget, network framing/send, NPC世界身分或任務進度／獎勵權威。最終default-off路由及live GUI驗收由主線另記。

## 精確原文與來源

以下行號為解包後實體行，rowSHA不含換行，CP950 strict decode。完整raw_hex亦在JSON。

### NPCMission 3016

NPCMission04.csvZ 行18；CSVZ SHA256 `d173d49216b7b27197aa91ffd82f8ffb753d64a97871b569d8d796ab0f25c99f`；decoded SHA256 `4df96bf6a8742a6abf2c81610c040aab4d8d140ed433c28c24bcd3c77c516284`；row SHA256 `a2c44d8dca8d068369d06caa878643fbf5715c7d1d8e54634f605b5f8a6c6dec`。

```text
3016,在滑鼠按鍵的應用方面，滑鼠左鍵是最常用的功能，主要分為兩種\n　1.移動：對於地面用滑鼠敲擊一下，你就會前往滑鼠敲擊處，即使未來無論你是否可以騎上神獸，這移動的功能都是一樣的。\n　2.交談：對我、其他師傅、甚至天尊或其它的人按滑鼠左鍵敲擊一次，就可以與我們進行交談，無論是進行任務訪查或是買賣東西，均可使用。\n而滑鼠右鍵的功能則是直接取消畫面上出現的介面，不管是道具介面、狀態介面、神仙介面或是對話介面及其它的介面都可以利用滑鼠右鍵關閉。
```

### NPCMission 3017

NPCMission04.csvZ 行19；CSVZ SHA256 `d173d49216b7b27197aa91ffd82f8ffb753d64a97871b569d8d796ab0f25c99f`；decoded SHA256 `4df96bf6a8742a6abf2c81610c040aab4d8d140ed433c28c24bcd3c77c516284`；row SHA256 `a9cc0884ee66f694c454fc1e257e0c2c4ac6db5a8fcaf90fda73d6d4f2d1c41a`。

```text
3017,現在要談的是介面上的使用，在畫面的左下角屬於頻道區，在這裡可以利用切換鈕切換對話頻道，目前提供的頻道包括：一般、組隊、洞府及密語等四個頻道。\n左上方目前你看到的只有你自己的圖像，有個仙字的格子是你現在使用的神仙圖像區，寵字的格子則是裝備好的戰寵圖像區，但由於你初來乍到，所以還沒有神仙和戰寵可以使用，不過當你離開這崑崙仙界時，應該會有神仙及戰寵了。\n正上方有一排熱鍵區可以將功能熱鍵拖曳至該處，即可以利用相對應的Ｆ１～Ｆ１０直接使用該功能，不過熱鍵分為兩類，一種是一般模式，另一種是神仙技能模式，這兩種功能和使用時機不同，只要多操作即可得心應手。\n畫面右上方則是顯示小地圖，你可以在這裡看到附近週遭的地形，如果不想看也可以利用右上角的Ｘ將其關閉。\n最後是右下角的功能區，分別是新手導師、狀態、神仙、道具、功能熱鍵及離開遊戲等幾項功能選單的啟動鈕。
```

### NPCMission 3018

NPCMission04.csvZ 行20；CSVZ SHA256 `d173d49216b7b27197aa91ffd82f8ffb753d64a97871b569d8d796ab0f25c99f`；decoded SHA256 `4df96bf6a8742a6abf2c81610c040aab4d8d140ed433c28c24bcd3c77c516284`；row SHA256 `a62d0946f32f9d2f473a04e4664e9282632393599ac72497ebeae016b372b36b`。

```text
3018,購買：你如果要買東西的話，可以在商店介面中用滑鼠左鍵點選要購買的物品，這時在介面上方會出現價錢，如果你想一次購買複數，可以用滑鼠左鍵點選商店介面上的數字部份（內定為１）進行修改，同時，商店介面會計算出你所購買物品的總額，如果你對於這價錢和數量沒有問題，以滑鼠左鍵按下○即可完成購買的動作。
```

### NPCMission 3019

NPCMission04.csvZ 行21；CSVZ SHA256 `d173d49216b7b27197aa91ffd82f8ffb753d64a97871b569d8d796ab0f25c99f`；decoded SHA256 `4df96bf6a8742a6abf2c81610c040aab4d8d140ed433c28c24bcd3c77c516284`；row SHA256 `a503b6d41e1b194b603a799e84254c3ddd6c4709e6151e6a3abe14490d8b743b`。

```text
3019,販賣：在你叫出商店介面的同時，畫面右方會出現道具介面，你可以用滑鼠左鍵點選道具介面中想要販售的物品，這時這個物品會出現在商店介面的上方，同時會將販售價格顯示在上面，如果這物品你擁有不只一個的話，在你點選時會出現一個輸入框讓你輸入欲販售的數量，如果你對販售價錢沒有問題的話，以滑鼠左鍵按下○即可完成購買的動作。
```

### NPCMission 3020

NPCMission04.csvZ 行22；CSVZ SHA256 `d173d49216b7b27197aa91ffd82f8ffb753d64a97871b569d8d796ab0f25c99f`；decoded SHA256 `4df96bf6a8742a6abf2c81610c040aab4d8d140ed433c28c24bcd3c77c516284`；row SHA256 `6aee6a215a859e35702963d25c7963e7a231a4d6a46d9778298c88821fa4f003`。

```text
3020,在遊戲中，你可以與其它玩家進行道具買賣的交易行為。\n首先，你必須先點選交易鈕，（熱鍵預設為F2），此時游標會變成交易游標，再以此游標去點選你想要交易的對象，便可以進入交易介面。\n在交易介面中，你可以由道具欄中拖曳想要交易的道具，或是輸入要交易的金額，待完成後，雙方按下確定鈕即可完成交易動作。\n不過，這世上有許多人會利用人的善念而在交易過程中進行詐騙，所以，在進行交易時可千萬要小心啊！
```

### NPCMission 3021

NPCMission04.csvZ 行23；CSVZ SHA256 `d173d49216b7b27197aa91ffd82f8ffb753d64a97871b569d8d796ab0f25c99f`；decoded SHA256 `4df96bf6a8742a6abf2c81610c040aab4d8d140ed433c28c24bcd3c77c516284`；row SHA256 `faac9141e7f7743a504c6f1714e048950d0f7465b521d59d9af6683cf99126e9`。

```text
3021,組隊乃是人際關係的重點，下面的解說可要牢牢記住啊。\n首先，點選畫面右下方的「功能熱鍵」會出現一個熱鍵選單，點選動作項目後出現動作類的熱鍵，這選單由左算來第一行的第一個即為組隊鍵（熱鍵預設為F1），第二個即為脫隊鍵（無熱鍵預設，需要自行拖曳）。\n　1.組隊：以滑鼠左鍵點選組隊鍵一下，游標會變成組隊的顯示，此時，以游標去點選玩家即可向對方要求組隊，在此同時，對方畫面中會出現一個對話框，上面會顯示你的資料及要求組隊的訊息，這時對方只要按下○同意組隊後，你們即可成為隊友，在成為隊友後，同一隊裡的人畫面左方會出現隊友的大頭像及簡單資料。\n　2.脫隊：在動作類熱鍵選單中由左算來第一行的第二個即為脫隊鍵，只要你是組隊狀態中按下此鍵即可脫離隊伍，同時畫面左方的隊友名單會消失。
```

### NPCMission 3022

NPCMission04.csvZ 行24；CSVZ SHA256 `d173d49216b7b27197aa91ffd82f8ffb753d64a97871b569d8d796ab0f25c99f`；decoded SHA256 `4df96bf6a8742a6abf2c81610c040aab4d8d140ed433c28c24bcd3c77c516284`；row SHA256 `af6b7157d2282242c18120419525c168f5a5c093598ba9bb766382f4a5c401be`。

```text
3022,有關基礎知識的內容你都懂了是吧！那麼我的工作也算完成了。\n這張是天尊交代我給你的崑崙仙界地圖，地圖的使用法為開啟右下角的『道具』按鈕，用滑鼠左鍵點選地圖兩下即可開啟崑崙仙界地圖，有地圖就比較不容易迷路了。\p你現在可以去做天尊大人交辦的事了！
```

### NPCMission 8779

NPCMission09.csvZ 行781；CSVZ SHA256 `0f00d56b93808a933e6bee811c79d477651b8c6aac002b271a79e002e5dfc812`；decoded SHA256 `96fbea32007a5e8272a57ffc58c865d677485f1771ded22a27bca9982b5dc36f`；row SHA256 `ee1b189acf8109172db45f35582179adf4ad0c02af46bace9527e5853c475c1d`。

```text
8779,即然有關基礎知識的內容爾等都懂了！那麼本天尊就先告訴爾等在仙界修練的事項。\p首先，你需要找/c3「合成師傅」/c9學習一些關於合成的基本常識；\n然後再到神仙密室選擇一位最適合的/c3神仙/c9；\n最後跟/c3「拳頭師傅」/c9學習戰鬥訓練，打好這些基本功再回來找本天尊，屆時爾等方可下凡。\p現在，爾等該去/c3崑崙仙界東南方的恭讀房找合成師傅/c9了。\n這張崑崙仙界地圖給你，地圖的使用法為/c3開啟右下角的『道具』按鈕，用滑鼠左鍵點選地圖兩下即可開啟崑崙仙界地圖/c9，有地圖就比較不容易迷路了。\n另外，這件仙衣送你，它能帶給爾等一些戰鬥中的幫助，/c3裝備仙衣的方法是打開道具欄，對仙衣按滑鼠左鍵兩下/c9便可以了，還有，你可以在道具欄中看到一個座騎，/c3對該座騎按滑鼠左鍵兩下便可騎上座騎/c9。\p好了，本天尊言盡於此，爾等下去吧！
```

### NPCMission 8780

NPCMission09.csvZ 行782；CSVZ SHA256 `0f00d56b93808a933e6bee811c79d477651b8c6aac002b271a79e002e5dfc812`；decoded SHA256 `96fbea32007a5e8272a57ffc58c865d677485f1771ded22a27bca9982b5dc36f`；row SHA256 `8bda4fcf466c6eaae7898fcf7aacda2bcf795ebd4dffab98a12a2af1c6a647be`。

```text
8780,有關基礎知識的內容你都懂了是吧！那麼我的工作也算完成了。你現在要做的是去位在/c3崑崙仙界東南方的恭讀房找合成師傅/c9進行修練！
```

### NPCMission 8786

NPCMission09.csvZ 行788；CSVZ SHA256 `0f00d56b93808a933e6bee811c79d477651b8c6aac002b271a79e002e5dfc812`；decoded SHA256 `96fbea32007a5e8272a57ffc58c865d677485f1771ded22a27bca9982b5dc36f`；row SHA256 `cd410539c10d585d64822a75afe99c7dbf102c64ff54a3848e6d809eebafe023`。

```text
8786,升級之後，就會賦予４點能力點數，可供/c3自由分配想要加入的能力/c9。\p可以提升的能力分別為：\n/c3體力/c9：生命力高低的指標，影響抵抗外在打擊的承受力！\n/c3腕力/c9：物理攻擊力大小的指標，腕力越大給予敵人的物理殺傷力也越高！\n/c3智力/c9：影響法力值與法術殺傷力，智力越高法力值也越高！\n/c3速度/c9：影響戰鬥中的迴避率與先制攻擊。
```

## 本輪原生碼範圍hash

| VA start | End exclusive | SHA256 |
| --- | --- | --- |
| 004C8350 | 004C8460 | `110a39785495f5a369fba4d604b8420fc4468c91f85bd87204036f46bf1ef061` |
| 004C84A0 | 004C84D0 | `a2afdcf2a0f45a3ca8c9570876eaef5ce560998d7f1bc43158ccc0464619a15c` |
| 004C85B0 | 004C86D0 | `7230ef9a9d4631c141513523173d6366a9c12a2cd1a42d1614b85cd959e44112` |
| 004C8720 | 004C8780 | `832eea4fab9d6636d33bdaa7448c3e53eed81a0f938dd262c2cde0b9c55b8b2f` |
| 004C8920 | 004C8D60 | `e9f62286ad6d075293b1c0843e54e169cb6a69b1888ff1fae0c1775eec726b55` |
| 00418950 | 00418B80 | `08b55521917d2626e0bd464b1555b4fb2c01394f03900cad6e3d1e5bd836fab8` |
| 0050D8A0 | 0050DB40 | `08210117c21be0994e39bd206d6ad00d6bf8ae05e477bb43781bb2d44756abf5` |
| 00468B4E | 00468B68 | `29a460521cd9647d66d32b2299c115e94eee06aab759c9b090301a2f8ecdbaeb` |
| 004C79C0 | 004C7ED0 | `a4d2469675fabae8c73f75fe0de0aec76e3f88d2ea7794b93eb2e9ddf86e3942` |
