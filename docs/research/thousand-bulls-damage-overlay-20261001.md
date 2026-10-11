# 牛轉仙界踏：傷害跳字遮擋修復

## 原因與範圍

原流程為地面特效 → 原生 viewport 0（角色、傷害字）→ 牛群前景 → viewport 1 UI。
牛群及煙塵因此覆蓋傷害字。此次只調整 CUSTOM-0059／技能 150 當前施放者的
浮動文字 ACT 樹，改為地面 → 角色 → 牛群 → 原生傷害字與底星 → UI。

## 原生依據

* 0051E6E0：war + 38 + (side × 14 + slot) × 6 × 4 為主角色指標。
* 0052B060：傷害文字控制項位於施放者 + 310 + targetIndex × 16。
* 0051DC00：控制項 + 4 為 ACT manager，+ A 為 ACT handle。
* 0051DE40 → 0041F040：數字與底星建立為 + 256 的 child ACT，並非只用 root sprite。
* ACT record 為 manager + 10 + handle × 290；root sprite + E，follow + AC／count + 254，
  child + 256（17 筆）、emitted + 27A（6 筆，有生成旗標時）。
* 00426AB0 依 display + F555C 鏈結，挑選 state 2 且 viewport 相符的 entry；
  00426B30(this=display, viewport, x, y, entry) 為原生單項繪製，ret 16。

在一次 render hook 內收集當前文字的可見 entry，暫設 state 3 讓原生 traversal
略過；牛群完成後恢復 state 2，按原鏈結順序呼叫 00426B30。不重算傷害、
不新增文字、不更改座標／深度／viewport。RAII 在例外時恢復顯示狀態。
僅在技能 150 有效、battle renderer 相符、viewport 0 時啟用。

## 驗證

* bull_damage_overlay_test：112 組實際編譯 render_hook；雙方、1～14 目標、四段。
  確認底星在數字後方、每項只繪製一次、牛群無法覆蓋文字；隱藏項目、UI、其他
  角色及 display 全部欄位保留；中斷復原。舊繪製順序負向測試必須失敗。
* bull_native_pipeline_test：18 情境／36 次施放；新增實際 bull_effect.damage_source
  選取當前施放者與 viewport 限制，原 HP、死亡、四段、音效、全畫面震動檢查通過。
* 28 項原生 ABI、29 項 hook 回歸、18-hook 安裝器、聊天凍結檢查通過。
* Release DLL 編譯成功；僅更新隔離測試包。正式伺服器、帳號存檔、EXE、圖檔未修改。

以上為內部自動化驗證（sprite raster／DirectDraw sink 為隔離測試替代物），
不等同實機畫面驗收。實機視覺待確認。
