# Current player sex: create profile, portrait and weapon restrictions

## 可交給server的結論

當前客戶端兩條create路徑（C2S17及C2S1B）的**raw40-byte送出profile**：

- `profile[33] == 0`：男。
- `profile[33] == 1`：女。
- `profile[38] & 0x0F`由同一值產生；`(profile[29]-1)&1`亦相同。

這次有原始資源名稱與原生按鈕binding建立男／女對照，不再只是binary0／1的中性推測。
69筆明確限制文字都屬TWP（35男、34女）；630筆WPN中沒有這兩種確切限制文字。

建議供owned weapon服務使用的保守predicate如下。輸入必須是已知來源的C2S17／1B
原始profile首40 bytes（目前server持久化即保留這塊），不是07轉換後的另一種40-byte結構。

```python
def qualified_player_sex(profile):
    if len(profile) != 40 or not 1 <= profile[29] <= 8:
        return None
    sex = profile[33]
    if sex not in (0, 1):
        return None
    if ((profile[29] - 1) & 1) != sex or (profile[38] & 15) != sex:
        return None
    return sex  # 0男、1女
```

對source確切含「限男性角色裝備」的owned item，要求sex=0；含「限女性角色裝備」
要求sex=1。未知或不一致profile不能默認某性別；其他沒有此文字的item不可由此推定
不存在其他裝備條件。這是可以實裝的**source-backed服務資格predicate**，不是已恢復原服
完整裝備拒絕演算法或角色資料防偽機制。

本lane只新增工具／報告，未改runtime、DB、client，未操作桌面。

## 男女值來自原始art名稱，而非人物形象猜測

`Data2/Patch/FlowComm.csvZ`解碼line5：

```
0,FlowGui.ROM,"FROM_GUI,",//遊戲介面
```

`404010`的流程介面資源來源為`data3/flow/`。當前`data3/flow/FlowGui.ROMZ`
包含以下原始ACT_DATA（24-byte名稱欄位取首個NUL之前；NUL後殘留bytes不當名稱）：

| action index | action ID | 原始名稱 |
|---:|---:|---|
|95|12550|Flow_CarBoyH|
|96|12560|Flow_CarBoyL|
|97|12570|Flow_CarGirlH|
|98|12580|Flow_CarGirlL|

兩套建立角色UI均使用相同binding：

- `4093F0`表VA`583088`：control0F對應action95／96，control10對應97／98。
- `40C2D0`表VA`583608`：相同control與action index。
- 兩套表中control0B..0E是職業對，0F／10是Boy／Girl；不能把其前四個control序號
  當成性別值。

`4097A0`及`40C680`的event mask01h分支：

- control0F（另有alias2）寫main+152A1=0，main+1529D=`2*(old/2)`。
- control10（另有alias3）寫main+152A1=1，main+1529D=`2*(old/2)+1`。

main+15280是40-byte profile基址，所以分別是byte33與byte29。
工具對兩條handler各測initial byte29=0..7、control0F／10，執行至其原生refresh入口，
確認完整40 bytes只有預期的29／33改变。沒有執行refresh圖形繪製。

## pre-wire與persisted wire不可混淆

兩條原生sender具有相同欄位轉換：

- `40C0B0`→`414CF0`→C2S17。
- `40C160`→`414CC0`→C2S1B。

先複製main+15280的40 bytes，再將byte29及byte31各+1；將byte33低4bits
寫入word38低4bits，其餘位元保留。**byte33本身沒有+1。**
因此wire／DB中的byte29為1..8，male為1/3/5/7、female為2/4/6/8；
但應以來源已證實的byte33與重複欄位一致性判斷，不接受任意奇偶值。

32組測試都執行上述copy／轉換到builder入口，逐byte核對全部40 bytes。
builder queue與登入狀態機不在本輪執行範圍；既有create wire契約另有資格。
現有`RecoveredCharacterCreate`接收17／1B，`SqliteRecoveredCharacterRepository`
完整保存傳入profile；這些檔案本輪只讀。

### 明確不能用來單獨判別的欄位

| offset | 已知用途／限制 |
|---:|---|
|29|職業對與性別組合ID；wire相對UI+1，必須確認結構／來源|
|31|另一個四選一欄位送出+1；本輪不給它性別語義|
|32|預覽component0 variant，不是男女值|
|33|此次證實0男／1女；raw create profile來源限定|
|36|肖像style／color及預覽variant位元，不是男女值|
|38低4bits|從33複製的肖像sex selector；其餘bits是其他肖像欄位|

07 list output的40-byte結構與raw create profile不同，禁止把它直接塞進此predicate。

## S2C2A的對應與模型界線

既有`RecoveredWorldEntry`由profile輸出portrait四bytes：
`[profile36 & E7h, 0, profile38, profile39]`，放在2A **body20..23**（不含opcode）。
`468315..468376`原生片段把該DWORD寫actor+458C。

`4ABE80`的第一個繪製呼叫使用`(portrait[2]&15)+21`作resource bank。
本輪32組均得到男21、女22，並核對actor+458C完整四bytes；在第一個`5068C0`
呼叫入口停止，没有宣稱完整HUD／pixel驗收。

上述是**肖像**欄位。普通世界模型的8-byte HeroDoll components與其binary nibble是
另一塊資料；本輪沒有證明可以由性別任意改寫它。不要用歷史2A模板component
的low nibble反推本角色性別，也不把此結果當WPN→DA mapping。

## 69筆來源適用範圍

工具核對當前gamedata全部630 WPN與629 TWP，只選description columns7..12含
確切「限男性角色裝備」或「限女性角色裝備」的row；每筆保存key、source line、
name、所有description及raw row hex。結果TWP男性35、女性34，沒有雙向矛盾row。

- key19071，source line15548：`限男性角色裝備`。
- key19072，source line15549：`限女性角色裝備`。

普通WPN/TWP的client C2S28 producer並未由此新證據獲得原生性別拒絕邏輯。
既有`49B5E0`測的是神仙裝備7001..7999和神仙性別，不能移用到人物。
此結果建立玩家性別來源與明文item要求的接合條件，服務端仍須owner／slot／instance／
pending-battle等既有條件。沒有從文案推測其他職業、等級、戰鬥或生成公式。

## 驗證與pins

工具：`tools/strike_lab/current_player_sex_contract_20260927.py`。

```
python -X utf8 -B -m tools.strike_lab.current_player_sex_contract_20260927 --output artifacts/research/current-player-sex-contract-20260927/native.json
python -O -X utf8 -B -m tools.strike_lab.current_player_sex_contract_20260927 --output artifacts/research/current-player-sex-contract-20260927/native-optimized.json
```

正常／-O皆exit0：32組原生event、prequeue profile、portrait-copy與HUD入口片段，
另160組不一致profile拒絕檢查。兩份JSON完全一致，SHA256
`d53e314340a9a456b5d8cb2b8e9f105d9d4289e01b842a97777b850b6b8160d5`。
遊戲callee沒有用合成回傳值替代；各slice在明記的實際地址停止，沒有跑完整繪製。

- 當前EXE：`6bf75ef8ac1e0f6b2240800ff841d205788bd1b6512149584b5386b10f431e98`
- FlowComm.csvZ：`27a0660b158d0cfcfe6afd5a01fcae91f98732d0f73efdde953b9d98fbe717e1`
- FlowGui.ROMZ：`2ad797d15aa6daa6562652fb69d39c9e3dbbdc108965c230c199735c8e682503`
- 解碼FlowGui：`8612c3e4953c54d236eaae7c06d78200f0f6787ee05458bc4b004b1706cea215`
- gamedata.csvZ：`70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731`

全部使用當前台灣客戶端供給；未讀退役來源。本lane完成後停止。
