# 原生 NPC 位置來源補查：元始天尊

2026-09-26，有界只讀審查。

## 結論

本輪沒有找到能新增完整 NPC 擺放記錄的原服來源。元始天尊仍只有目前台灣客戶端 NPCAppearData 的候選760、1701、1702、4146及外觀2072；沒有足以選定崑崙世界實例、座標與面向的記錄。**新增合格spawn：0。**

已先讀 `native-npc-placement-audit-20260926.md` 和 `kunlun-quests-44-50-npc-chain-20260926.md`。本輪沒有重跑任務／NPC對話文字搜尋；重點是先前資料型態審计以外的候選和擷取來源。沒有修改Application、DB、客戶端或配置，沒有啟動遊戲或操作桌面，沒有打開退役Classic/XJZ資料。

## 實際來源 inventory

| 位置／候選 | 本輪檢查 | 能否提供原服天尊位置 |
| --- | --- | --- |
| `Desktop/God2` 根目錄 | 僅God2、God2-Server、Launcher-src三目錄及兩個探測obj | 沒有新增原服資料根目錄 |
| `God2/God2` 當前客戶端 | 檔名／副檔名清單：未見pcap/pcapng/cap、SQL/SQLite/MDB或spawn命名資料；DB候選僅Thumbs.db；另發現5份crash.dmp | 缺原服生成資料；此為有界檔名盤點，不聲稱識別所有不明格式 |
| `God2/Launcher-src` | NPC候選為ROM／翻譯CSV／玩家版副本；`玩家版登入器-v1.0.0.zip`僅列目錄，45個entries，無SQL/DB/pcap/spawn候選；未見另一份gamedata.csvZ | 登入器與翻譯包不是新台灣原服擺放表 |
| `God2-解殼EXE原始碼重建` | README、inventory、analysis-project、decompiled、preserved-source、reconstructed、verification的用途；排除build/.git/__pycache__後檔名篩查無DB/SQL/pcap/spawn候選 | Ghidra專案／反編譯／後加IME源碼／驗證fixture不是原始伺服器輸入 |
| `God2-Server/artifacts/capture_inbox/native-master-01` | manifest的isolation=`loopback-only`；記憶體範圍00400000..00707000；角色是events/memory_image/raw_trace/unpacked_pe | EXE解殼與分析擷取，非原服世界0x72封包或完整world heap |
| `capture_inbox/host-cdb-20260918-transition` | 同上，manifest明記loopback-only／同一模組範圍 | 同上 |
| `capture_inbox/g03-deep-20260919` | 同上，manifest明記loopback-only／同一模組範圍 | 同上 |
| `capture_requests`、`snapshots`、`golden`、`contracts` | 只檢視目錄及manifest型態；前兩者是既有擷取請求／環境快照，後兩者為握手、登入、選服等契約材料 | 本輪未發現新來源manifest能宣稱原服崑崙NPC會話 |
| `God2/God.log`、`GodAcnt.log` | 檢查時均0 bytes | 無可追會話內容 |

伺服器現有自己產生的playtests、runtime、release、DB備份不因含0x72或NPC字樣而升格原服來源。本輪不掃讀其全部payload；先確認是否有獨立原服來源證明。沒有以既有舊NPC fixture的座標重新認證天尊位置。

## 先前429資產審計之外：CityI2 MBD與MMB

先前位置審計明列MDT／MDL／HMD。此次另外讀取当前 `Data2/map/island03/cityi2` 的MBD明文／壓縮對與MMB頭部，並參照 `current-monster-map-binary-source-20260920.md` 已有MBD讀取器結論。

### cityi2.mbd / cityi2.mbdZ

- 解碼後完全相同，434,536 bytes，magic `MBD v1.2`。
- u32維度12×12，144個檔案offset；123個非零、21個零。
- 非零offset按表序精確為 `592 + k*3528`（k=0..122）。
- `16 + 144*4 + 123*3528 = 434536`，無額外尾部或未列的獨立spawn附表。
- 3528 bytes為21×21×8的區塊格式，與原生MBD block reader（RVA40790）相符。既有證據證明cell WORD+0經3B1B0作tile索引；不能把匹配760/1701等的任意短整數當NPC ID。
- 這是結構與來源比對；沒有新執行CityI2原生reader，亦未宣稱其餘每個cell欄位語義已全部排除NPC關聯。

| 檔案 | SHA256 |
| --- | --- |
| cityi2.mbd（亦為mbdZ解碼後） | `eba7aa7ae1ddc0381c7fe30d452fa251345aa9310386948b5eaf080c37d78e59` |
| cityi2.mbdZ原始壓縮檔 | `e6e12fd3ffe4d87d91205d9d00c02b8960238609c1248ad0e488de4eb8630ce2` |

### cityi2.mmbZ

原始SHA256 `d258ad62e630c671ac82eb559ba5c400d7a314132738bd0857fb6935efcdfe6c`；解碼SHA256 `6235ca38051db7a6084e403cfea14abaaf02e11d86743bc8e6b43adad46824e4`，64,584 bytes。

BMP頭部是252×252、8bpp。它可支持地圖影像來源，沒有結構化world NPC selector／方向／互動授權欄位。未用圖上的符號估計天尊座標或面向。

## 新發現的5份crash minidump

均位於當前God2目錄，MINIDUMP signature有效、flags=0，18個thread，25個MemoryList ranges；沒有Memory64/full-memory stream。逐範圍與thread stack descriptor對照：18範圍皆為執行緒堆疊，其餘7範圍各256 bytes，位址為00533E34及77xxxxxx程式區附近；不存在可重建完整NPC pool的world heap記憶體區。

| 檔名 | UTC產生時間 | 檔案bytes | 所保留memory bytes |
| --- | --- | ---: | ---: |
| God2.1DD4C1698E0B825.crash.dmp | 2026-09-24 11:19:45 | 116758 | 81552 |
| God2.1DD4C169D9EDF0D.crash.dmp | 2026-09-24 11:19:58 | 117038 | 81832 |
| God2.1DD4C16B342A3A4.crash.dmp | 2026-09-24 11:20:29 | 116758 | 81552 |
| God2.1DD4C1A6F2088C8.crash.dmp | 2026-09-24 11:47:13 | 116774 | 81568 |
| God2.1DD4C1A72EA63BB.crash.dmp | 2026-09-24 11:47:19 | 121302 | 86096 |

沒有原服endpoint／場景會話provenance，不能把堆疊上的偶然值當原生生成記錄。本輪只讀header、stream directory及memory/thread descriptors，未掃描玩家堆疊內容。

## 下一個值得追的來源／位置

1. **最高價值且目前沒有的來源：**使用者另持有的原始伺服器NPC配置／世界DB，或原服崑崙進場會話的封包擷取。需要來源路徑與build/time／scene可核对資訊，不能拿目前自己伺服器重送的測試72作證。
2. **若取得原服封包：**在area4、scene3進場鏈後定位21-byte logical S2C72，保留selector primary/secondary、完整opaque bytes、direction=`logical[9]>>5`及packed位置17..20；再關聯實際天尊互動與名稱，不只搜尋ID760/1701/1702/4146。沒有會話解框／加密上下文的單獨0x72 byte不成立。
3. **若取得完整原服會話dump：**需包含world/UI、scene、NPC pool及來源會話證據，沿當前CC380/CC621接收建立路徑還原實例。現有5份小型crash dump和三份module-only unpack capture都不符合。
4. **仍在當前檔案可作的低優先技術追查：**CityI2 MBD cell WORD+2及其餘欄位的完整xrefs／reader語義。已有tile資料結構但未全語義化；沒有直接NPC selector/方向線索，因此不能承諾這條會產出天尊位置。既有CAN/MDL與名稱文字已在之前工作覆蓋，不應再以全文搜尋代替新來源。

上述來源inventory是本輪交付，沒有生成猜測位置或新的實作授權值。審查至此停止。
