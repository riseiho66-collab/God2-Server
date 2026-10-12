# 第317輪：實際入口資源選擇值與原始資料恢復

本輪修改兩個既有C++ headers，新增readonly source projection1；完整玩法branch、opcode與雙向route增量0。316及歷史原件保留。工作仍在PHASE1，不建置或測試。

## 實際世界入口來源

普通zero-transform2A在4684EB呼叫461270：formal1是unsigned B6，控制TEST BP後的四component zero/positive branch；formal2是(LE32(B0)>>16)&0x7f，只在46141B供給463AD0 tail第三arg。後者读signed WORD，當前caller值0..127；它沒有一般negative-index guard。返回AX存WORD，不推fullEAX正規化。B0/B4即時R44 masks同值，但ordinary caller實際讀raw scratch；不宣稱跨opaque children穩定。

RecoveredWorldEntryView::entry_resource_selectors()從完整logical37直接返回logical[7]和logical[3]&0x7f。SharedTaiwanWorldEntered::Scope把同一entry的by-value projection供既有Source使用；cpp實際enter仍先綁session/account/character/handle/position/lease，再傳state->scope給source。沒有另造supplier、cache、欄位或預設值，亦不更改aggregate fields、wire、queue、storage、權限與凍結行為。語義限定普通分支，非零transform/override尚未證；讀raw不授予resource membership、scene admission、load success、fresh component defaults或current after-state。

## 分開兩個資源namespace

463AD0讀WORD count+24F70、pointer+24F74、136B record，使用row+2 cached WORD或filename+8。known4637B0僅126B entryprefix：PUSH58A900的25B NUL literal為\Data2\Patch\DrvDoll.csv；463811存allocation、463817清WORDcount。未展開row loader／ROM／CRT。這個DrvDoll tail不能由Drv.csv的32B bank+121F8／count+121F6替代。

兩selected caller clips163B/48sites全部與named historical reference重疊，new byte/site/method0；complete known461270/463AD0與prefix/literal只作reference，不重計native coverage。partial歷史capture不代表完整原歷史包；完整bytes不等於全callee語義讀取。

## 原始資料的精確恢復

fresh verified=true archive查詢，精確恢復HeroDoll.csvZ.decoded 37189B（SHA256 0ba373ca45d0f4452f1d847fab5f5e194f00501f26a58f082c5352f71fe921c2）與Drv.csvZ.decoded 3899B（SHA256 72cd006c121a865e10b7d1e2c655895da16a5e760bad2c8d473bf5663996f6e0），共41088B，放God2之外。只讀archive index/query_only與普通archive zlib，沒有原csvZ codec、VM、historical differential或game DB SQL。whole pack／mutable index未作全域reaudit。

8個HeroDoll原row与1個Drv原row保留unique key、filename和field5/action值；共享ROM filename不合併source identity。Drv首row真的empty filename/action0，不捏造有效handle。HeroDoll歷史98fresh比較只涵蓋C33 binary0/1、variants0..6、selector0和fresh zero indices；不能當獨立owned2A defaults。DrvDoll第三原明文未恢復，歷史de951...文字pin不是current plaintext資格。Raw CP950 root顯示曾有錯碼，未據此宣稱中文字義解碼。

## 統計與缺口

TW C2S候選156；world74=部分來源50/control11/未接13；S2C252=fixed230/variable22，reply48/push11/gated4/未分類117。Battle indexed110/specialized9；86 selectors7/cases6；83 actions23/projections2/outside21。TW未掛載chains3/bindings38 unique34。CN歷史C2S156/S2C phase280/length253各scope獨立，chains35/bindings93 unique71，本輪CN增量0。Mixed282/CUSTOM135/groups26/pending10不變。50/74=67.6%只計世界解析的部分分支；全遊戲總數／完整分子分母／TW及整體百分比仍未知。

沒有build/compiler/tests/runtime/native/VM/emulator/resourcecodec/gameDBSQL/migrate/activate/deploy；frozen帳號存檔、auth/chat/IME/頭像/原字體/繁簡轉換、TW/CN/web、shared64、coins99999999999、stack99與level保持。新的typed consumer來源不等於完整server issuer。下一步取得DrvDoll當前exact原明文與ordinal grammar，再完成actual owned entry來源及正常worldpublication。

## 固定證據

外部包：`C:\Users\risei\.codex\artifact-archives\god2-server\20261012\tw-native-appearance-selector-and-profile-resource-317`。Workers完整current closures包含實際nested seals，manual範圍見readscope。

```json
{
  "native-entry": {
    "qualified_spans": 2,
    "bytes": 163,
    "sites": 48,
    "new_selected_spans_vs_reference": 0,
    "new_bytes": 0,
    "new_sites": 0,
    "explicit_overlap_bytes": 163,
    "overlap_sites": 48,
    "data_slices": 0,
    "data_bytes": 0,
    "global_new_coverage_claim": false,
    "raw_seal_sha256": "1a2f91368de40a9dad95c4f131e92e1e8fef2a9ad943fce9b2a074b1d3528fe8",
    "canonical_closure_sha256": "daaa6d250ddd2e3fa401501f36e2ec59e4353236a3d255cbe9c936911768ab2d",
    "closure_members": 79,
    "closure_bytes": 7977980
  },
  "profile-resource": {
    "round": 317,
    "restored_exact_original_sources": 2,
    "restored_bytes": 41088,
    "selected_HeroDoll_rows": 8,
    "selected_Drv_rows": 1,
    "readonly_archive_index": true,
    "verified_archive": true,
    "general_archive_zlib_restores": 2,
    "resource_csvz_decode_executed": false,
    "native_methods_increment": 0,
    "source_increment": 0,
    "cpp_increment": 0,
    "branch_increment": 0,
    "opcode_increment": 0,
    "fullroute_increment": 0,
    "game_completion_increment": 0,
    "completion_percentage": null,
    "historical_98_comparisons_rerun": false,
    "historical_9604_projections_rerun": false,
    "input_count": 17,
    "input_bytes": 136418,
    "bounded_field_provenance_facts": [
      "exact original selected resource keys/filenames/field5",
      "Drv source row0/action column2 zero",
      "shared filenames do not merge source identity",
      "fresh preview/selector0 condition is not independently owned2A server rule"
    ],
    "third_resource_restored": false,
    "raw_seal_sha256": "6ac77c201a79e69c770da9c5b8a2e60cce836921d1e7f6e3aa47f4ab29292be3",
    "canonical_closure_sha256": "d1d78f64b4eca7367559b5b2bdf81dafd16ee0bc349c4908735fd045e1a13ffc",
    "closure_members": 43,
    "closure_bytes": 188662
  }
}
```
