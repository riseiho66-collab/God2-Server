# CN 實際配置版本至帳號握手來源（2026-10-08）

本輪 `20261008-cn-config-version-handshake-source`，第一階段靜態恢復與來源串接。前輪 normal-startup 配置輸入已接入，catalog119／97 檔封存保留；屬於具體進度。本輪修改前保存 35 個 context，包含 transport codec、credential stage／verifier、帳號 metadata producer、正式 Application 與存檔來源。

追查尚未命名的帳號 metadata／billing 時，先核對了現有原生帳本：A4 serial、A6 UI version、A8 provider、A9 local group 與 billing byte5 的已知／未知邊界未改動。本輪沒有找到 AA..CB 或 billing byte5 的新增業務語意，不合成它們、不從 incoming04 反射 profile40。具體新增工作是補上已找到的帳號 network version 實際來源。

## 實際輸入及原生轉換

固定 CN EXE SHA256 `582f269535f86e95fcd77946821adf79a30d1bd33f21d566cf48c36fd221b3c8`。前輪四份 actual preferred `.iniZ` 的解碼內容均含 **`$ 296`**，同名 plain `.ini` 則含 `$ 268`。原始／解碼 hash 與精確 snapshot 沿用 118 輪封存，本輪不重新解碼或修改客戶端資源。

0047CBC0 在外層遇到 `$` 時先將 local int 清為 0，0041FA50 以 `%d` 呼叫原生 vsscanf，接著將低 **BYTE** 寫到 config network+650。在已存在至少一組快取的路徑，配置不重新讀取；不得把每個 controller 的配置讀取當成獨立版本來源。

實際選定檔案的 296 取低 BYTE 為 **40**；若錯讀 plain，268 取低 BYTE 會是 **12**。不能將整數 296／268 當成 wire WORD，或把 plain 的 12 冒稱目前 preferred resource 的版本。CnAccountWire 的既有 baseline 40 不變，來源今次改為實際配置的明確供應及相容性核對。

0047FE30 在帳號 waiter 開始取 owner+750 的低 byte，作為 0047E6C0 的 expected-version operand。0047E6C0 遇 logical opcode01 後，從 payload 取 WORD，與 zero-extended expected byte 比較；因此原生帳號 logical01 的完整 bytes 是 `01 28 00`。它不恢復官方權益、認證、成功1D／0A或 key 規則。world callers 的 byte240 和 UI／world-login record version200 是不同來源，不套用這個配置整數。

保存 0047CBC0、0041FA50、0047FE30、0047E6C0 的 metadata envelopes、實際 code／指令與 `%d` 字面區。這些是列明入口的有限證據，不把 metadata size 當成全部 caller／CFG 或所有設定格式的閉合證明。

## 已接入來源程式

`CnClientGroupConfiguration` 現在在相同實際設定 snapshot 中保留 optional signed32 version integer，getter 精確投影至 uint8。解析只在原生外層 `$` 行作用，組內普通行不錯當設定 directive；缺少 `$` 為 unknown／null，不偷偷填 40。無法轉成整數時原生有明確的 initialized-zero 規則，記錄其結果 0；這仍不符合固定 profile40，不能變成默認成功。整數溢位、未資格化 text／chunk／buffer 格式拒絕，保留後續原生分支調查。

`compose_native_login` 要求實際配置的 byte version 精確符合固定 CN native baseline40；將**同一個** shared_ptr<const configuration> 同時保留在 account callback／目錄 Plan 與回傳 Controllers.account_configuration。配置 path、encoded／decoded bytes、選擇輸入、group slots、整數及 byte 來源保持一份不可變物件，不按 Windows 語系／繁簡偏好選版本。

`SharedCredentialServer` 在完整 controllers 指派、開始 accept 前要求這個實際來源及相同版本。新連線透過 SharedCredentialConnection 將同一 snapshot 傳給 CnTransportSession；後者也要求 qualified40，並在成功 challenge 後以該實際 byte 建立帳號 `01 28 00`，沿原有 queue／codec 順序發布，再呼叫 Established。world01 240、native seed／challenge／加密／隊列／backpressure／斷線／cleanup／帳號驗證與入場 authority 不改。

這消除「目錄讀實際設定，但握手只讀獨立固定常數」的來源缺口；不是支援任意修改 `$` 值或新客戶端版本。資料與 baseline 不符時不啟動來源，不改掉 baseline 來讓它通過。沒有將 profile、billing、存檔、等級或64位數值上限改為296／40／12。

## 邊界與計數

source 中新增實際 version operand producer1、既有 account handshake source binding1，同一 immutable config 由 composition／host／connection／transport 傳遞。新 opcode／phase binding／完整 owner chain／完整雙向路徑0，沒有把只有格式／拒絕判定或未啟用來源算成完整玩法。全遊戲總數／完成率仍 unknown/null。

原生 AA..CB、billing byte5 與實際 profile40／billing16／權益／revision／期限／07摘要仍未供應，正式 Application／實際 launch input owner／client profile 部署未配置。全部世界／裝備／場景／ACT／玩法、TW／CN／PC／web／WSS、數值／背包擴充與全路徑分母繼續未完成。原生 unsupported overflow／再載入／64組邊界／特殊text等變體不宣稱關閉。

未建置、測試、執行 native／C++ reader／codec／server／Windows API／client／RNG／DB／遷移／部署。codec、credential stage／verifier、AccountWire baseline、issued profile serializer、正式 Application、存檔、聊天、IME、字體、文字轉換、頭像、等級與客戶端資源保持；全部來源串接後才集中全面測試、修復與發布。
