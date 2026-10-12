# 第312輪：世界入口的resource條件與遠端更新來源

本輪新增具體的原生查表與consumer證據，將未知來源收斂到實際card row／目標EnyName索引及遠端子物件的呼叫鏈。沒有改動C++、執行遊戲或測試、操作資料庫、遷移或部署；新完整玩法串接為0。

## 2A入口必須取得的真實資料

指定2A nonzero transform path先呼叫45C100；它以lowWORD key與signextended catalog WORD bound作inclusive比較。這個判斷不等於45C000所讀的rowWORD0吻合key。45C000只有吻合分支先填8B local的WORD0／BYTE2／WORD4／WORD6，BYTE3未由此selected分支資格；common join仍複製local到output。未取得原始來源的local不稱為garbage、零值或預設值。

實際caller把outputBYTE2／WORD4／WORD6送進45A0A0，leaf會依area低BYTE、scene低WORD、ordinal低WORD尋找EnyName資源。lookup可回傳0，selected2A caller隨即解參考結果BYTE而無所選範圍內的null guard。因此完整供應者須資格exact card row及實際target resource，不能只接受45C100的AL、共同角色座標或任意表格列。

本輪另唯讀現取ChangeDollCard.csvZ完整encoded bytes，SHA256與歷史4d51b22d51c14bc98b6ec96c16a40384a226e9fa1f90543ea58a36fb4b56ebd2吻合，原始byte copy放God2外。沒有執行decode/codec、讀decoded rows或證明當前native lookup/issuer；decoded0f04 pin仍是歷史reference。ChangeDollCard的增益與資源對應保留原生來源身分；它不是wild怪物的HP、雙攻雙防、五行或技能。沿用20260920／20260926／其他named references，已知helper及重疊範圍不算全域新發現。原311封存中body guard位移的更正仍適用：scratchESP28到guardESP40是body+24，非末DWORD+32。

## 遠端更新與6F保持各自格式

實際S2C36／37的table46B5D4分別到469C6B／469C09，packet+1為各自body。36的low14 identity等於W1539683C時走local5038A0並直接跳tail；只有nonself36及37所選支路CALL4FBC30。它lookup bodyWORD6&3FFF取得remote pool的A=P18+slot268，傳N=A1EC給完整50DF20／50E150，直接写N E／10／12／14 WORD或N22 scalar；沒有直接N34／A220 access。Body9條件寫A265、body8非零條件寫A264，尚有opaque4614A0／Action／resource children。ESI argument2完整DWORD只證selected低BYTEstore，上位與currentlocal來源未知，不當整DWORD bool。

原native-remote REPORT的eachcalls字句已用外部immutable effective correction限定self／nonself，原seal與metrics保持。該修正與確切caller／table／PE／stack／指標證據獨立釘定。136B dispatcher prefix沿用307／310已知範圍不重算；historical290完整466B00只取得entry／467154 CALL相鄰rows資格，不冒稱整歷史package或本輪完整manual callgraph。

S2C36／37與C2S Timer36方向不同。它們的body8／9不是6F body8或opaque DWORD9／17；body0／1條件mask不是完整Afterstate。Actor220相鄰亦不是被整塊讀寫的證明；完整81B6F原始供應者仍未取得。

## 已有服務端接點與真正缺口

Application在explicit world plan內取同一Database的reader／writer，HostPlan要求實際entry_qualify、entered及movement來源。Prepare先經Offer及原生完整frame shape，再由replace_from_issuer按完整expected tuple與same common root／position執行既有CAS。Prepared／BeforeWrite在stage前，BeforeCommit見staged next，完整readback比對。這是當前來源契約，沒有執行SQL或宣稱正式資料庫已存在這些內容。

Offer在COMMIT後不再呼叫provider／reload／retry。後續Native／Current仍可拒絕送出，但不能undo已提交的快照；快照持久化不等於queue release、socket Written、client ACK或world publication。

SceneContent只供應current-world area／scene的NPCList及完整EnyName觀察。Card-derived resource target可能是另一area／scene／ordinal，必須由真正issuer另保留並資格，不能拿world scene catalog代替。Stored raw blob、digest與geometry匹配不供給全部opaque/rules/resources；完整SceneSupply及Current仍是必要來源。現有泛用橋接已存在，本輪不增加同功能wrapper。

source-entry原封存將main call行號誤植為88；實際call在86（88是closing brace），effective-source-correction312.json保留精確更正與原claim雜湊，原封存未改。本輪對main86的run_server(config,seconds)是來源呼叫觀察，不是正式PID/schema/player狀態現讀。沒有啟用尚缺完整source的Main計畫。

## 統計與後續

TW C2S候選聯集156；世界解析74＝部分来源50／控制11／未接通13。S2C supported252＝fixed230／variable22；nondefault206／default46，來源reply48／push11／gated4，未分類117。battle indexed110／specialized9，86 selectors7／cases6，83 actions23／已資格projection2／outside21。TW unhosted chains3／bindings38 unique34。

CN維持historical C2S156／S2C phase-opcode280／length253，各自scope不相加；unhosted chains35／bindings93 unique71。mixed282／CUSTOM135／groups26／pending10，990個src檔未改。新來源串接分支、opcode及完整雙向路徑均0；全遊戲封包數、完整路徑分母、TW／全遊戲百分比仍null。50／74的67.6%只代表限定解析分支覆蓋。

shared64、仙幣99999999999、stack99、原生level、TW／CN／web、native fonts／繁簡轉換、帳號存檔與其他凍結功能保留。沒有build/compiler/tests/runtime/native/VM/emulator/codec/gameDBSQL/migrate/activate/deploy。前次status-only回合分類no progress；本輪依現讀base／乾淨工作樹／live agents重新採取實際bounded trace。

下一步：補exact transform card row／target EnyName資源來源與完整2A issuer；追已資格的遠端escaped子指標及直接writers，保持未知6F opaque9／17獨立。已知本地option初始化及泛用allocator不再重跑。

## Qualified evidence capsule

19 complete source inputs824429B; manual scope explicitly bounded. Every actual captured nested seal is included; historical source documents do not imply their entire execution snapshots are copied. Native metrics below have explicit named references, not global novelty.

```json
{
  "native-entry": {
    "qualified_spans": 7,
    "bytes": 473,
    "sites": 145,
    "new_selected_spans_vs_reference": 5,
    "new_bytes": 375,
    "new_sites": 115,
    "explicit_overlap_bytes": 98,
    "overlap_sites": 30,
    "data_slices": 1,
    "data_bytes": 16,
    "global_new_coverage_claim": false,
    "raw_seal_sha256": "f881c8deaeb00ebef369c61df7172430704d9ab941a5ff00b38528c31ef54789",
    "canonical_closure_sha256": "237a3f11e860ddfd17d7356283befcaada6bd2a8d8dc0841481442ac747cd451",
    "closure_members": 71,
    "closure_bytes": 6696564,
    "canonical_format": "Whole seal minus own canonical SHA, defaultASCII compact sorted JSON UTF8 no newline"
  },
  "native-remote": {
    "round": 312,
    "qualified_intervals": 6,
    "qualified_bytes": 1772,
    "qualified_instruction_sites": 579,
    "qualified_instruction_bytes": 1772,
    "complete_methods": 4,
    "selected_dispatcher_or_case_intervals": 2,
    "relative_named_reference_overlap_bytes": 136,
    "relative_named_reference_new_bytes": 1636,
    "reference_sets": [
      {
        "file": "inputs/history290/qualified-spans.json",
        "sha256": "06df2f16d8925a69d7b1d4191759a1ee7d06c5d9a8b8d6785cd918fe9d874a0b",
        "intervals": [
          [
            5251600,
            5252280
          ],
          [
            4609592,
            4610246
          ],
          [
            4618336,
            4619459
          ],
          [
            5247424,
            5248525
          ],
          [
            5246048,
            5247418
          ],
          [
            4638368,
            4638465
          ],
          [
            5245984,
            5246036
          ],
          [
            4614912,
            4617876
          ],
          [
            4619632,
            4619666
          ],
          [
            4614416,
            4614419
          ],
          [
            5221488,
            5221657
          ]
        ]
      },
      {
        "file": "inputs/history307/qualified-spans.json",
        "sha256": "9dbf615030690db369c42a68eb160421d9e18c53a0a4e81046e7384b1e57c218",
        "intervals": [
          [
            4623072,
            4623208
          ],
          [
            4632082,
            4632141
          ],
          [
            4610223,
            4610270
          ],
          [
            5313462,
            5313564
          ],
          [
            5314497,
            5314564
          ],
          [
            5331388,
            5331402
          ],
          [
            5331883,
            5331918
          ],
          [
            5331545,
            5331677
          ],
          [
            5320832,
            5320901
          ],
          [
            5323796,
            5323863
          ],
          [
            5319104,
            5320330
          ],
          [
            5344848,
            5346009
          ],
          [
            4741088,
            4741202
          ],
          [
            4723952,
            4724111
          ],
          [
            4879696,
            4879812
          ],
          [
            5207328,
            5207670
          ],
          [
            5207760,
            5207775
          ],
          [
            5537151,
            5537185
          ]
        ]
      },
      {
        "file": "inputs/history308/inputs/tw-current-actor-source-301-native-220/qualified-spans.json",
        "sha256": "0a77daf4bb5829b2d3c9d34f87ec3a758cfa75f79dbf169ab57831a5007fad43",
        "intervals": [
          [
            5221296,
            5221460
          ],
          [
            5223520,
            5223653
          ],
          [
            5227872,
            5228116
          ],
          [
            5228896,
            5228938
          ],
          [
            5300736,
            5300997
          ],
          [
            5299344,
            5299380
          ],
          [
            5244765,
            5244908
          ],
          [
            5243264,
            5243486
          ],
          [
            4626929,
            4626984
          ],
          [
            5226944,
            5227859
          ],
          [
            4609063,
            4609082
          ]
        ]
      },
      {
        "file": "inputs/history308/inputs/tw-pk-phase-owner-gate-305-native-resource/qualified-spans.json",
        "sha256": "f08556d0330991ebc581c3c500d5dcd009e00285467f5d1bba9bf3808183baf7",
        "intervals": [
          [
            5230000,
            5230541
          ],
          [
            5227651,
            5227671
          ],
          [
            5227117,
            5227186
          ],
          [
            5240080,
            5240391
          ],
          [
            5240400,
            5240721
          ],
          [
            5241440,
            5241487
          ],
          [
            5239744,
            5239791
          ],
          [
            5239840,
            5239888
          ],
          [
            5242096,
            5242169
          ]
        ]
      },
      {
        "file": "inputs/history308/inputs/tw-remote-actor-fields-298-native-fields/qualified-spans.json",
        "sha256": "46a2429700cb474b7bf0f8a0c442b0ad7c68f9bb84d8d0dea06c13398fd84735",
        "intervals": [
          [
            4625864,
            4626984
          ],
          [
            5226944,
            5227859
          ],
          [
            5226800,
            5226932
          ],
          [
            5230000,
            5230541
          ],
          [
            5231424,
            5232036
          ],
          [
            5232496,
            5232544
          ],
          [
            5225296,
            5225377
          ],
          [
            5282656,
            5282824
          ],
          [
            5282192,
            5282432
          ]
        ]
      },
      {
        "file": "inputs/history308/qualified-spans.json",
        "sha256": "ac4c33f3ad5e0c666752c2d7e163973c3d5161236a49eafe0fdcd188db3e6c3b",
        "intervals": [
          [
            5232544,
            5232687
          ],
          [
            5224672,
            5224827
          ],
          [
            5228192,
            5228241
          ],
          [
            5228320,
            5228799
          ],
          [
            5299312,
            5299335
          ],
          [
            5299392,
            5299995
          ],
          [
            5302160,
            5302222
          ],
          [
            5301632,
            5301820
          ],
          [
            5301824,
            5302160
          ],
          [
            5301008,
            5301631
          ],
          [
            5241840,
            5241926
          ],
          [
            5241936,
            5242022
          ]
        ]
      }
    ],
    "global_historical_novelty_claim": false,
    "data_bytes": 8,
    "source_branch_increment": 0,
    "opcode_completion_increment": 0,
    "full_route_increment": 0,
    "completion_credit": 0,
    "completion_percentage": null,
    "exploratory_excluded": [
      "nested_following_methods_exploratory",
      "remote_nested_payload_caller_exploratory",
      "actor_subblock_init_exploratory",
      "remote_update_worldcase_exploratory",
      "world_dispatch_entry duplicate subset",
      "world_dispatch_prefix_boundary incomplete finalinstruction"
    ],
    "actual_next_cut": "Inspect actual worldcaller46938F→4FC990 identity setter and true tablecase to distinguish identity replacement from unknown actor220; alternatively follow actual wholeactor resource child with object-base provenance. Lookup4FC960 has no directcall4FC990. Neither path supplies originalserver9/17 without independent evidence.",
    "raw_seal_sha256": "c56068d19fc5a51d2943af2f8633dcdcbc91fa2cd088b917fa3469b25de96324",
    "canonical_closure_sha256": "3a8330cfe9f0eb6bfec245aedab294a4fa91f53dc889419fcdc8c45b6598591b",
    "closure_members": 123,
    "closure_bytes": 7263699,
    "canonical_format": "Whole seal minus own canonical SHA, defaultASCII compact sorted JSON UTF8 no newline"
  },
  "source-entry": {
    "complete_inputs": 19,
    "input_bytes": 824429,
    "new_source_branches": 0,
    "new_fullroutes": 0,
    "source_files_modified": 0,
    "new_opcode_values": 0,
    "reference_full_package": "Only14-member effective correction copied completely; other historical source docs are source files, not their entire historical execution artifacts.",
    "raw_seal_sha256": "f7d3b4a2d3426111258e958b318e882934bb9e727c32816bd6f780cba97fb1db",
    "canonical_closure_sha256": "205230a6a766bbedc60252fb43d53386be8bcfa4fb7256e556187deac4656195",
    "closure_members": 40,
    "closure_bytes": 935214,
    "canonical_format": "Whole seal minus own canonical SHA, defaultASCII compact sorted JSON UTF8 no newline"
  }
}
```
