# 台服資源選取與場景來源持有者（第175輪）

本輪接續第174輪實際 ROM／HMD／Grid 來源，新增原生檔案選取與具體 game-owned 場景資源持有者，接入既有 movement scene factory。陸服另追帳號目錄 Location 到已選角色摘要的實際原生投影。PHASE1 保持來源實作與靜態逆向，沒有建置、測試、native／C++／Lua／API 執行、DB／SQL 存取、部署或重啟。

使用者已要求「這輪結束停止工作」。第175輪完成來源交接、報告與封存後暫停目標，不啟動第176輪；完整 TW／CN／web 全遊戲目標與所有未完成項目保留，不改成局部完成。

## 台服原生選取

TW 完整 mapped image SHA256 `149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`。`0044D520` 的 ROMFILE 原始 token 經 `0044C6D0` 取得 model object `+0x1C` prefix，再由原生字串函式純 byte 拼接，經 `0044D350`／`0044D2D0` 入 `00429820`。prefix 與原始名稱之間沒有自行新增分隔符，也沒有從 HMD 檔名猜 prefix。

`00429820` 的 ROM binary loader 只在 request 的倒數第四個 byte 是 `.` 時附加 `Z`，先嘗試 candidate。`00402530` 的文字 loader 無條件附加 `Z`。兩者只有 candidate 開啟失敗或非 `05 16` marker 才回到原始 request。選中有效 marker 後的解碼／解析失敗，不構成原始檔 fallback 的資格。

新增 `TaiwanNativeResourceSelection` 具體選取檔案並以 immutable storage 保留完整 Request、原始 reference／prefix、明確 cwd、完整 bank operand、requested／candidate 名稱、candidate probe、完整已開啟 candidate 與選中的 encoded 原始位元組。讀取錯誤或資源大小限制不冒充原生 fopen 失敗。沒有執行這個 C++ 選取器；本輪只實作來源並讀取現存原生證據。

檔名來源目前限定已確認的 ASCII／安全長度域；drive-relative 或缺少 drive 的 rooted 路徑、CP950 高位元 byte 到檔案系統的映射仍開放。這不是把完整遊戲目標縮為 ASCII。原文與 CP950／CP936、繁簡轉換保持原要求。文字原生 loader 的暫存檔及 rt reopen 失敗分支沒有重現；`Candidate0516` 只證明 encoded selection，不能稱原生 FILE／runtime 載入成功。實際初始 cwd、model prefix 與場景 request issuer 仍需接入。

五個新完整 game／library 函式、兩個 CRT 支持範圍、56個精確指令位置與五個完整 literal 保存；三個第173輪 caller 範圍及一個有界 map caller context 另列，不重算。完整 TW image、實際 Wood_B.ROMZ、cityi2.mdlZ 與 decoder 原始來源共四筆；兩份 decoded 衍生資料分開保存。

## 具體場景來源持有者

新增 `TaiwanNativeSceneResourceOwner`。每次 install／replace 需要真實 Session、完整 Lease、已儲存姿態、實際 HMD／每個 ROM／resource／initial scene generations，以及真正 ResourceCurrent 與 Authority。直接解析完整 selected HMD／ROM，驗證所有 ROMFILE ordinal、原文字 byte identity、prefix、cwd 與普通 bank operand，取得既有 `TaiwanNativeMapAsset::RomBound`、model extent／排序／mask／Grid／Resources，再透過 `material_source()`／`factory()` 供給既有 scene factory。

持有者複製所有公有容器，以 private const source／binding／Grid storage 保有完整來源。Current 核對確切 Entry、Session pointer、完整 Lease、同 map、共同世界就緒、沒有 pending entry、精確 Grid identity／generations，以及真正 delegate 前後的 saved position。真正 delegate 仍必須資格化原生 object／window／frame／source 生命週期；private registry 一致或檔案完整不能代替原生 Current，更不能授予移動權限。

來源審閱補齊兩個生命週期問題：每次 scene supply 有獨立、immutable 的 private incarnation；pending 保有確切的一次性 actual Permit identity。舊 scene／舊 permit 不可重新資格化新 supply／新 ticket，也不清除其 successor。被捕捉的 nested reentry 立即讓受影響 Entry terminal 並 detach，下一次 operation 不會重設旗標後使舊來源復活。這些 token 是持有者自己的身分，不稱原生計數器。初版及修補前的完整來源副本均保留。既有 host/controller 與新 supply 的替換協調仍須真正 hosting owner 接入，不能把這些 source 方法稱為已完成正式替換。

保留既有唯一 common position CAS。BeforePublish 的 Scope 還是 before actor，但 saved position 已是 after；真正 actor publication 成功且保存狀態仍相符後，才保留成功的 after pose／direction。callback partial failure 是 terminal，不回滾已 commit 的 prefix、不再發送或再結算。remove／replace／shutdown 只處理自己的來源生命週期，不釋放共同 Presence／Visibility lease 或誤刪其他 generation。

所有既有 C++、Lua、原生 EXE、帳號存檔與凍結功能不變。真正時序／pending／碰撞／權限／完整原生5D仍由既有 mandatory Authority 供應。新資源持有者沒有製造 native x86 address、固定成功 Current 或猜測 ACK；Main 與正式 issuer 仍未啟用。

## 陸服帳號 Location

CN PE SHA256 `582f269535f86e95fcd77946821adf79a30d1bd33f21d566cf48c36fd221b3c8`。五個新原生函式範圍共272 byte、五個有界關係保存；五個既有 caller／catalog 範圍保留但不重計。

`0047C6C0`／`0047C760` 按 selected group／server，掃描每組十個 node 與每個 node 十個四-byte Location，選第一個非0 routing key。前者讀取同一 Location 的 unsigned BYTE `+0x01`，後者讀取 unsigned WORD `+0x02`；`0047F630`／`0047F650`／`0047F670` 是實際 wrapper。第三個 summary pointer argument 不由這些 getter 讀取。

既有 `00445B40` 的 state `0x1A` 分支呼叫三個 getter，把既有 S2C06 的 BYTE0／BYTE1／WORD2 投影到已選 character row `+0x20`／`+0x21`／WORD `+0x22`，再進 endpoint selection。角色 stride 是 `0x24`；因07 payload 前置兩個 bytes，payload-relative offsets 是 `+0x22`／`+0x23`／WORD `+0x24`。所有位置都以明確 hex 記錄，與 creation state `0x18` 分開。

這是本地選角快取修改，不是原始 server07 producer。Location BYTE1／WORD2 的 map／area／spawn 等玩法語義及官方發送規則仍未知，不造坐標或默認資料。兩個未知 receiver 的 calling slot／phase 也沒有因此解決；14個 contexts／12個 qualified contexts 不變。

## 統計與交接

| 項目 | TW | CN |
|---|---:|---:|
| C2S opcode 索引 | 156（151一般＋5補充） | 156 |
| S2C opcode／phase entries | 252（230定長＋22變長） | 280（帳號6／世界206／戰鬥68） |
| 本輪新增 opcode／phase binding | 0／0 | 0／0 |
| 本輪新增完整雙向遊戲路徑 | 0 | 0 |

本輪新增四個 C++ 來源檔，來源整合紀錄166增為167；這些不是完成封包數。30個既有戰鬥 action／selector frontier entries 保留不重計；958個 endpoint index rows、28個群組也不是完整全遊戲分母。總封包數、已完成完整路徑總數及完成百分比仍未知。

Fresh before1252 SHA256 `d41be7e12f13e1bbf802932483b03a98a20cc06f8601e316d79d7e7991d47cf0`，上一輪2124個封存成員及原始來源完整保留。代理分別保存全部 actual inputs、before／intermediate／current 原始來源、精確 native sites 與缺口；根整合保存原始 CLI 與最終報告再封存。Windows 長路徑造成的一次證據寫入錯誤、原 writer 與只接受 byte-identical partial resume 的原件紀錄保留，不覆寫 before 或偷偷更新基準。

暫停時仍未完成：完整分方向／階段／狀態／變體的全遊戲分母；TW 原生 entry／reservation、完整 peer policy、actual runtime source／cache／object lifecycle、Authority／完整5D／mixed dispatcher／Main；CN 真正 account／rights／summary／world issuer；64位元數值所有 storage／wire／object／display／飄字、stack99所有變動呼叫端；web WSS／TLS／hosting；以及全來源接通後的全面建置、雙版與混合測試、修復及可恢復發布。仙幣99999999999、其他上限另定、等級不改、原生字體與繁簡轉換等原要求全部保留。
