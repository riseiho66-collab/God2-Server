# CN 世界 UI 指令與退出返回條件

本輪 `20261008-cn-world-command-return-lineage`，PHASE1。前輪已保存state／EAX／close映射與來源投影，分類progress。保持完整TW／CN／PC／web、共同世界與資料、全部遊戲、64-bit數值、堆疊99和最後集中測試修復發布；不縮減目標。

固定CN EXE `582f269535f86e95fcd77946821adf79a30d1bd33f21d566cf48c36fd221b3c8`。本輪讀primary `004AE370` 與其實際三個相關UI callee，不依void／uint等decompiler型別猜測退出原因，不執行client／API／C++／UI／資料庫。

## 分派、事件及尾端優先序

`0048AA10` 的實際ECX指向world+89B26C，呼叫 `004AE370`。它取得UI事件後，把signed short事件ID與該owner的+1C84D0／+1C84AE／+1C8544等實際WORD綁定比較；本輪不為這些ID填猜測標籤。+1C8654 gate有兩個分支：非零時，ID等於+1C84D0且`004AC4F0`返回非零，才在004AE5CC指定command=-26；零時相同ID也呼叫helper，卻沒有這個command賦值。不能忽略gate而把所有window close都叫0202。

`004AC4F0` primary：event flags的bit1（mask02）非零，或bit5（mask20）非零且signed item=0，則呼叫0044E7F0並返回EAX1；否則EAX0。mask是原生UI事件條件，不是C2S權限／backend退出規則，回傳1也不是存檔或socket成功。

一般tail先呼叫004AF1ED→0050B110、004AF1F4→0050A320、004AF202→00496890、004AF209→0051A720；**之後**004AF20E才讀actual owner+8AC。若值等於1，cmove把暫存command覆寫成-15，否則保留原值，最後mov EAX,EBX／ret4。因此須觀察post-callback值；不能用呼叫前的舊旗標推導command。早期直接signed-WORD return分支不經此tail，這個override只適用到達tail的路徑。

## 確認分支與偽陽性排除

`00527840` 消費byte flags及signed item。flags mask02非零，或mask01為零，或item不等於2時，AL返回0（部分情況會做原生UI清理）。只有mask02=0、mask01非零、item=2的分支，先做UI setter／00527730及條件audio callback，最後005278F5重新比較actual owner+43088：非零→AL1、零→AL2。不能把上方的audio gate+430A8→+449E bit0當成返回值或server權限；return operands在其後觀察。

在004AE370 caller，實際AL1轉command=-2；AL2轉-9；其他保持原command，再經前述tail override。`005280B0` 在item2分支設+43088=1，item3設0，再做UI setters與00527810，但**每個normal return都xor AL,AL**。它的上24-bit EAX不必為0，caller只比较AL。所以004AE62B呼叫該callee之後對AL1／AL2的兩個literal branch，在已恢復的normal callee path不能成立；不能把它们記成真實退出觸發。另一次004AEB09呼叫也只能給這個caller AL0。後續00527840確認事件可能使用新+43088，仍需實際UI來源與生命週期。

|實際command|已保存frame→world→main|此main switch的封包／行為|
|---:|---|---|
|-26|2→2→6|02 02|
|-15|5→5→4|該switch無close，走登入UI分支|
|-9|1→1→2|02 01；main繼續外層流程|
|-2|0→0→1|02 01；main的EBX==1分支結束主流程|

兩個不同native返回原因同樣走control1，因此不能只憑0201推導主程式退出或重新登入。這些是client lifecycle關係；實際server save／pending operation／rule／replay及03兩個payload bytes沒有由此恢复。

`004AC020` 是跳至 `004A9B30` 的5-byte thunk，後者只是對owner+4524C指標free並清0。它的存在不證明server交易／存檔已完成。其他tail/UI helper side effects與resource綁定／labels仍有缺口。

## 來源與計數

既有 `CnPostWorldExitControl` 增加readonly `NativeCommandReturn`，保存raw signed command並接至前輪精確world／main／optional control映射；另增加post-callback tail override projection。它們不進入wire reader或把client state轉為backend authority，不更改原生client、收包格式、現有exit issuer或正式服務。

本輪新增command→return投影1、tail優先序投影1；primary caller／callee條件關係3、normal AL0 callee qualification1、排除2個該callsite的syntactic literal候選。這不等於全遊戲取消兩個封包或其他caller相同值永遠不可能。完整command producer／early signed-WORD returns／UI lifetime／state6来源及全部phase／state／variant分母未封閉。

Opcode、source phase binding、owner chain、完整雙向路徑新增均0；來源片段新增1。Whole-game total／completed／percent=null。無建置、測試、runtime、native/API/C++/codec執行、DB讀寫、遷移或部署。原存檔、帳號、認證、聊天、IME、頭像、字體、繁簡轉換、等級、client二進位及歷史基準保留。
