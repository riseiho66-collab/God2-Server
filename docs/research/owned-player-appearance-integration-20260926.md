# Owned ordinary DA 外觀保存與實際客戶端路徑

2026-09-26。CUSTOM-0047；正式WPN映射、穿裝條件、攻防結算與實際remote
refresh尚未完成，不得將本輪隔離映射提升為原生遊戲規則。

## 原生來源與保存

當前EXE SHA256 `6bf75ef8ac1e0f6b2240800ff841d205788bd1b6512149584b5386b10f431e98`。
`current-2a-da-baseline-20260926.md` 正常／`-O`各266案例驗證2A body
→DA對應：actor低14bits，transform body32..33、scalar5/6 body34/35，
完整component block body12..19。此為原生欄位對應，非WPN映射。

Migration29新增 `character_player_appearance_snapshots`，完整15-byte DA與
8-byte不可變baseline保留owner、revision、origin、provenance、client pin。
沒有row就不產生外觀或物品。repository保留現有交易的savepoint，外層失敗
同時回滾inventory／appearance；不自行commit caller交易。拒錯owner、CAS、
pending battle、opcode／大小／pin／來源損壞。普通分支只接受transform0。

## 實際服務端路徑

- `world.owned_player_appearance.enabled`：從owned snapshot恢復初始2A八個
  components与末四bytes，保留其他world／map／profile bytes；預設false。
- `development.diagnostic_owned_weapon_appearance`：只允許loopback、owned
  weapon与appearance同時開啟，禁止peer／remote actor路徑。僅兩個完整合成
  WPN1/2 instance作為刀01/02映射測試；不是原服item→selector。
- 28既有whole-instance交換後，在同一transaction準備DA after-state，
  preserve其他三component與scalar；卸裝取不可變baseline的weapon pair。
  Inventory清除／完整3B／absolute41與DA同一已提交response。
- 原history2A body6=27會強制騎乘資源而忽略incoming weapon ordinal；
  此診斷案例將body6明確設0，測普通未騎乘分支，重登入同規則。
  正式服與一般owned restoration不套這項fixture覆寫。

## 修復與驗證

Release build已成功。最終候選11/11 CTest：repository、C++ DA codec、
weapon transfer／slots（含跨repo成功與兩種rollback）、Lua、DB、config、
崑崙出生與movement、TCP appearance/restart，以及C++ wire→native consumer。

TCP測試3次server啟動，驗證missing row／otherowner無grant、非零raw scalars、
完整20-byte穿装與DA同時保存、shutdown/restart登入2A還原、卸装baseline、
錯key與mixed／duplicate frame保持state及TCPalive。其他roleaux/resources/
God/pet/owner資料未變。

隱藏驗收01/02失敗紀錄保留：01錯誤比較整個live component6bytes（含未資格化
animation state）；02又錯誤要求handle數字必變且未限定unmounted。這些是
測試資格問題，未把DB成功當作畫面成功。修復後以rawselector0、完整saved
component／scalars、livehandle／variant以及source-backed HeroDoll native
record filename/cache為驗收界線。03又定位到readonly reader漏HeroDoll子表
offset12D78，修復後04通過；01～03均未宣稱功能成功。

最終同候選hidden04 `accepted=true`，SHA256
`d10a222a21c61a867807abec2879ab68883a546d5595c31e95b0a44eed421f72`：
DA更新刀01→刀02→baseline→刀01，revision2／3／4／5；前三component
`01c001600160`保留，weapon pair `0100／0101／3100／0100`；原生cache／
filename對應r02w000(43)、r02w001(44)、r02w300(42)、r02w000(43)。
resource_selector0，HP/MP52/120/26/80不變，崑崙移動126/127及clock通過。
sourceDB/live/privateEXE均未改；desktop input維持Default。全部owned private
process已關閉。這是本人資源與native state資格，不宣稱pixel截圖驗證、
remote視角或神仙保存；fixture沒有God。

## 交付與暫停

本輪僅stage可審查候選版本，正式運行EXE／config／DB保持原狀；測試映射關閉。
`artifacts/releases/owned-player-appearance-20260926-02/manifest.json`：
STAGED_NOT_INSTALLED、migration29、原有tables不變、appearance rows0。
stage01用錯PRAGMA user_version作檢查，已改為權威schema_migrations.max(version)；
失敗的01保留，沒有安裝或變更正式資料。
使用者要求本輪後停止，因此收尾後goal設paused，所有子代理與隔離測試程序停止。
候選與驗收文件保留，未將「停止工作」解讀為完成整個遊戲。
整體約11%為規劃估算，非原生還原或封包覆蓋比例。
