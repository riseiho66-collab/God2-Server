# NPC 位置約束反推與面向自由度：2026-09-27

## 能確定的內容

從目前客戶端原始文字、外觀表與地圖表，得到以下唯一同名候選。
它們是 NPC 文字目標座標；原服出生初始位置、漫遊路徑、世界實例與
面向仍須獨立證據，沒有把文字當成完整生成表。

| NPC 原名 | 文字座標 | 外觀表候選 | 原始 Mission_data 行 |
| --- | --- | --- | --- |
| 廚師梁禎 | 108/110 | 2936 | 1488 |
| 李樂 | 113/69 | 2937 | 1492 |
| 阿銀嬸 | 69/72 | 2938 | 1494 |
| 馬老伯 | 68/116 | 2939 | 1496 |

四句各自明寫「果力村的」人物名稱，不是沿用上一句場景。
精確地圖名在當前 catalog 唯一對上 area13/scene12/kind0，資源
`North002/Cityjiu02/Cityjiu02.mdt`。來源與完整原行hex/hash保存於
`artifacts/research/npc-reverse-constraints-20260927/evidence.json`。

## 為何不能由這些資料唯一補出面向

工具 `current_npc_reverse_constraints_20260927.py` 將每個原文座標保持
不變，對八個方向分別執行原生72 selector slice與新NPC scalar slice，
共32個向量。它們都在指定邊界取得同一 x/y、不同方向，沒有從文字或
外觀鍵產生唯一方向的額外判斷。實際讀取是：

* direction = logical[9] >>5
* x = (LE32(logical+17) >>2) &0x7FFF
* y = LE32(logical+17) >>17

這些是明確的合成diagnostic72記錄，不是原服封包。selector測試使用
合成maximum32767；沒有把4043筆來源行數當成稀疏catalog最大鍵。
constructor的EBX世界身分fixture是5A5A，不是外觀表鍵2936～2939。
原生slice停在lookup／scalar寫入之後，不執行完整resource/render、
不連server、不生成NPC。不能據此聲稱任一方向都完成全客戶端驗收。
此證據只說明已查原生欄位本身無法消除八個面向候選。

現用God2.exe與三段原生碼已逐byte核對；source與全EXE hash固定。
normal／`-O`均PASS、JSON逐byte相同，SHA256：
`7e622e8203eee2f5f995ae98620ad474c1ad021965efe1fda1752a7558467fcd`。

```powershell
python -m tools.strike_lab.current_npc_reverse_constraints_20260927 --output artifacts/research/npc-reverse-constraints-20260927/evidence.json
python -O -m tools.strike_lab.current_npc_reverse_constraints_20260927 --output artifacts/research/npc-reverse-constraints-20260927/optimized.json
```

## 外部交叉核對，未覆蓋目前來源

查詢日期2026-09-27。這些是歷史網站／搜尋索引資料，不是当前build
的完整原服封包或出生表。

* [巴哈8591果力村](https://wiki2.gamer.com.tw/wiki.php?n=8591%3A%E6%9E%9C%E5%8A%9B%E6%9D%91)
  搜尋索引的李樂113/69、阿銀嬸69/72與當前文字一致；馬老伯寫69/115，
  與當前來源68/116不同。本輪保留當前值，沒有取平均或挪動NPC。
* [歷史楓華鎮座標帖](https://forum.gamer.com.tw/G2.php?bsn=8395&sn=80)
  自述NPC會移動、座標為附近位置，並註明大陸CB內容。這提醒不能
  把每個攻略觀測點當成固定出生配置；沒有用該帖整批填入服務端。
* [新浪2005地圖索引](https://games.sina.com.cn/z/xjz/2/dtzb/index.shtml)
  可定位葛城NPC圖與崑崙全景頁，但兩個原圖URL取圖超時。
  本輪未讀到圖像，沒有假稱以圖驗證座標／面向。

本輪沒有更新正式runtime、配置、DB、客戶端或存檔。
