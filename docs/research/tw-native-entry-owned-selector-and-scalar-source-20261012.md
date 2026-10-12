# 第319輪：角色入場current-selector與owned後態來源

本輪完成有界原生def-use與實際裝備後態來源／交易邊界研究。C++新增／修改0，完整玩法分支、opcode、雙向route新增0；沒有把資料鏈盤點報成新玩法接通。318全部原件保持。上一status-only回報不算goal進度，本輪已現讀clean HEAD及running代理，接續實際來源研究。

## 已定位的裝備後態鏈

C28的OwnedItemSelection按一次輸入選唯一full20 alias與共同instance；明確definition模式讀兩原catalog完整396B。Action.handle是mandatory外部規則owner，adapter不產生next外觀；後續完整State issuer交SqliteOwnedEquipmentTransaction，原writer在同一交易比較兩完整population及共同root/position，成功COMMIT後才返回private Committed。

同Context owned_equipment_publication_factory交既有SharedTaiwanNativeEquipmentPublicationSource。它在每階段核共同完整Committed與實際lease/position，從1215B witness的[1200,1215)抽原DA15並發送既有observer endpoint。此seam已存在，沒有新增泛用supplier。observe_committed只是consistent-read receipt，不能報成原writer曾執行；C24 bag move保留DA tail，revision增加也不產生equip規則。

DA logical7..14是8component bytes，3..4是transform WORD，5/6是raw scalars，1..2 actor WORD不masked。完整入場baseline logical13..20/33..34/35/36及14bit actor讀法保持各自證據；它沒有fresh2A B0/B4/B8或original owner供應。C28 Source只適用InWorld而拒絕common_world_entry_current，不能拿later action授權當fresh-entry來源。

## 為何不能直接回填已存入場body

Actual joint writer的stage只含inventory與equipment。Entry writer replace_from_issuer要求autocommit並自己BEGIN，其Prepared/BeforeWrite/BeforeCommit在交易內；joint committed_current也要求autocommit並自己BEGIN。因此不能從entry Issuer呼叫joint public Current，也不能從joint Issuer呼叫public entry writer。

只串兩次public commit不具同一完整tuple原子性。真正existing-entry＋同actor committed DA後態同步還需要same-connection的完整source/current tuple機制、原producer與不受影響opaque的保留資格；本輪不加guess serializer或wrapper。OwnedTaiwanPkAppearanceSource另保留實際private initialization entry receipt及stored raw witness；任意重寫entry還可能使該exact-current見證失效，不能以有DA便假定safe重新發入場。

## Current-selector原生資料流

Sibling native-entry REPORT與field-source圖保留實際current R44→Petdrv→signed WORD local scalar、選定source binding與callerscope。三selected spans共131B/35sites全部explicit historical overlap，new native bytes/sites/methods均0；三data slices100B只是限定來源資料，不計玩法。完整464910..4651A1 continuity2193B/535sites只有機械映射，未資格整個method/callgraph。

actual468738讀R44，(R44>>18)&FF送46874A CALL464280（owner Main+A7F2E64），返回AX sign-extend後寫R40。完整leaf用signedWORD global58AA5C作上界、formalDWORD index signed比較，owner+4指32B rows，取row+0x16（十進位22）WORD；actual464EC5..464EEB binding提供其table pointer。signed比較不是通用負index拒絕，actual selected caller的BYTE域與generic葉函式保持分開。這是不同Drv銀行／當前狀態派生，不是DrvDoll cache，沒有以rowlabel推所有權。

該getter／constructor早有20260919歷史證據；本輪限定在fresh2A caller與current/prior-state差額，不重新計全球method coverage，也不重跑historical VM/測試。Current R44經opaque children後是否仍等於原B6，不能由早期packed寫入無條件推定。B8..11沒有新原source；無填0。精確位寬、branch範圍、重疊與每個source公式，以封存worker為準。

## 進度與範圍

TW C2S候選156（generic145 direct＋6 wrapper、額外5）；world74＝部分来源50/control11/未接13，50/74＝67.6%只計世界部分解析。S2C252＝fixed230/variable22；nondefault206/default46；reply48/push11/gated4/未分類117。Battle indexed110/specialized9；86 selectors7/cases6；83 actions23/projections2/outside21。TW unhosted chains3/bindings38 unique34。CN historical C2S156/S2C phase280/length253是不同scope，chains35/bindings93 unique71，本輪CN增量0。Mixed282/CUSTOM135/groups26/pending10不變。全遊戲封包數、完整路徑分母、TW及整體百分比仍null。

未連完整world gameplay opcode13仍為35/A9/D6/D8/69/6B/9E/E4/BF/C2/6E/A3/CB，原各phase/variant/rules缺口保留，不因本輪外觀資料鏈而減數。不能把resource供應、parse、拒絕、Current條件或未hosted來源當全遊戲接通。

無build/compiler/tests/runtime/native/VM/emulator/resourcecodec/gameDBSQL/migrate/activate/deploy。SQL只有source文字閱讀，沒有database執行。Native/fonts/帳號存檔/auth/chat/IME/頭像/繁簡轉換、TW/CN/web、shared64、coins99999999999/stack99/原levels保持。Web v111只收到peer metadata，本輪未adopt／ACK／client修改，不使用peer完成估計當server百分比。

## 固定證據

外部包：`C:\Users\risei\.codex\artifact-archives\god2-server\20261012\tw-native-entry-owned-selector-and-scalar-source-319`。各actual nested seals包含在closure；partial歷史reference不代表整個historical package。

```json
{
  "native-entry": {
    "qualified_spans": 3,
    "bytes": 131,
    "sites": 35,
    "new_selected_spans_vs_reference": 0,
    "new_bytes": 0,
    "new_sites": 0,
    "explicit_overlap_bytes": 131,
    "overlap_sites": 35,
    "data_slices": 3,
    "data_bytes": 100,
    "global_new_coverage_claim": false,
    "raw_seal_sha256": "b32fae8415f2995529b844f4ca8b343b026aa0b920cb55c1bdc9fa4ac92196b4",
    "canonical_closure_sha256": "a36b9f56eb02b028b58a1b034774e1b0ed9586969e1b9be60c4789cd83308e94",
    "closure_members": 71,
    "closure_bytes": 7372139
  },
  "owned-field-source": {
    "base": "84d7a90166ae84c2580ee7cf14c7f53e98cbe8eb",
    "bounded_provenance_facts": 9,
    "bounded_slice_inputs": 11,
    "branch_increment": 0,
    "completion_percent": null,
    "cpp_increment": 0,
    "fullroute_increment": 0,
    "gameplay_increment": 0,
    "global_historical_novelty_claim": false,
    "governance_whole_captures": 3,
    "input_bytes": 158920,
    "input_count": 28,
    "native_byte_increment": 0,
    "native_method_increment": 0,
    "new_original_2A_fields": 0,
    "opcode_increment": 0,
    "primary_whole_source_inputs": 14,
    "round": 319,
    "source_increment": 0,
    "raw_seal_sha256": "56a6d433e739c46338cec1ef21cf2b01429c1d66aa3cefe2ab310b51b70439f2",
    "canonical_closure_sha256": "3ec166a44ecb376fe72e29e571b3e4e3ddfadbb80a9ebb6c5ff0bf8728f99780",
    "closure_members": 35,
    "closure_bytes": 207304
  }
}
```
