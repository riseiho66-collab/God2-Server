# Streamer vector badges and natural font proportions

## 2026-10-06 目前狀態：已依使用者要求還原原生字型

取消微軟正黑體／微軟雅黑及自訂自然比例：正式God2.exe的00532918與00538DC6
已回復原生CreateFontIndirectA／CreateFontA，與目前保留的原生God2.unpacked.exe
相同位置位元組一致。僅改12 bytes，其餘客戶端位元組保留；.fontcfg區段保留，
這兩個入口不再呼叫它。主播樣式、IME、繁簡轉換及CN客戶端均未改動。
下列發布/啟用狀態為歷史；CUSTOM-0055目前停用，後續不得自行重套。
恢復前完整EXE、候選與紀錄：`../../artifacts/releases/native-font-restore-20261006`。
本輪未建置、啟動遊戲或執行畫面驗收。下次正常啟動採原生字型呼叫。

Owner authorization: normal-proportion Microsoft JhengHei / Microsoft YaHei,
equally sized vector badges, and repair of the missing own-role overhead badge.
Latest message styles supersede the initial pale outlines:

| DB value | Badge | Message RGB | Weight | New message outline |
| --- | --- | --- | --- | --- |
| 0 | none | native | regular | none |
| 1 | YouTube | FF4040 | 700 | dark gray 404040, 1px |
| 2 | Facebook | 087BF3 | 700 | dark gray 404040, 1px |
| 3 | TikTok | FFC000 | 700 | dark gray 404040, 1px |

Names and bubbles retain the native style. All badges are 16×16 with a 3px
gap, drawn from cached GDI+ vector paths. The native name shadow row reserves
the badge width but does not repaint the badge at a one-pixel offset.
The Facebook message color matches the vector tile's base fill exactly.

## Root cause of the missing own-role icon

The original cosmetic refresh inspected only the remote actor pool at
`world + 0x0ABA32E0` (pointer at `world + 0x15383418`). Native 00500C60
and 00501810 allocate the owned actor in a different pool, `world + 0x039C`,
and store its renderer index at `world + 0x1539AD80`.

Both pools use the same native name renderer. `RefreshNames` now refreshes the
owned index and matching remote actors whenever authoritative metadata arrives.
It preserves DB privilege 0 removal and uses the existing native name-writing
hooks when objects are recreated. No character name is hard-coded in the client.

## Fonts

The client loads the Windows-installed font family; the font files are not
embedded in the executable. CP950 selects Microsoft JhengHei, CP936 Microsoft
YaHei. `lfWidth=0` allows natural glyph width. A positive native height is
converted to negative character height instead of forced cell-height fitting.
Observed native values: width 6 / height 12 → width 0 / height −12.

The font module changes two existing font-creation call sites only. Streamer
message drawing selects a weight-700 instance of the current font, restoring
the previous font afterwards. `GetTextMetricsW` measures the selected font
on nonempty draw calls, including ordinary name draws for comparison.

## Acceptance and release

`private_client_fonts_20260927.py` tests two language processes from one EXE
on a hidden desktop against a cloned DB/private server. It checks initial own
badges before chatting, mutual badges after room return, style 3 updates and
style 0 removal, Chinese chat rings/bubbles, actual font families/proportions,
actual regular/bold GDI weights, and preservation of unrelated saved rows.

Native receipts and screenshots are under
`artifacts/playtests/private-vector-fonts-20260927-08` (latest colors);
`private-vector-fonts-20260927-06` first qualified the owned-pool repair.
Deployment is not implied by source changes or an accepted test. The deployment
receipt, when present, is
`artifacts/releases/streamer-vector-natural-fonts-20260927-02/verification.json`.
The release gate also verifies the frozen server chat route and saves the
previous client image before replacement. Server/DB changes are not needed.
