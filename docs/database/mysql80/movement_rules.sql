-- CUSTOM-0150; MySQL 8.0.17+ single-table source counterpart only.
-- No execution, data rows, defaults, migration, backend or activation claim.
-- Require strict SQL mode for importing exact values; never IGNORE/REPLACE
-- or disable CHECK enforcement. All rows share one config_version, validated
-- again by the whole-snapshot repository/cache (no cross-row CHECK fiction).
-- Official syntax/semantics:
-- https://dev.mysql.com/doc/refman/8.0/en/create-table-check-constraints.html
-- https://dev.mysql.com/doc/refman/8.0/en/regexp.html
-- https://dev.mysql.com/doc/refman/8.0/en/charset-binary-collations.html
CREATE TABLE movement_rules (
 profile_key VARCHAR(48) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_bin NOT NULL COMMENT '設定代號：小寫字母開頭，僅 ASCII 小寫字母、數字、底線',
 config_version BIGINT NOT NULL COMMENT '整批設定版本：全表一致，正數，修改時整批遞增',
 step_interval_us INT NOT NULL COMMENT '補充一步額度所需微秒，範圍 1 至 60000000',
 burst_steps TINYINT NOT NULL COMMENT '可累積步數額度上限，範圍 1 至 39',
 initial_credit_steps TINYINT NOT NULL COMMENT '新權限初始步數額度，範圍 1 至額度上限',
 first_sequence TINYINT NOT NULL COMMENT '備援政策第一個預期索引，範圍 0 至 39',
 block_players TINYINT NOT NULL COMMENT '其他人物阻擋目的格：0 關閉，1 開啟',
 forbid_corner_cut TINYINT NOT NULL COMMENT '禁止斜走穿角：0 關閉，1 開啟',
 allow_zero TINYINT NOT NULL COMMENT '允許原地步驟：0 關閉，1 開啟',
 design_id VARCHAR(11) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_bin NOT NULL COMMENT '自訂規則來源識別，固定 CUSTOM-0150',
 PRIMARY KEY (profile_key),
 CONSTRAINT movement_rules_profile_key_check CHECK (
  CHAR_LENGTH(profile_key) BETWEEN 1 AND 48 AND OCTET_LENGTH(profile_key)=CHAR_LENGTH(profile_key)
  AND REGEXP_LIKE(profile_key,'^[a-z]','c') AND NOT REGEXP_LIKE(profile_key,'[^a-z0-9_]','c')) ENFORCED,
 CONSTRAINT movement_rules_config_version_check CHECK (config_version BETWEEN 1 AND 9223372036854775807) ENFORCED,
 CONSTRAINT movement_rules_step_interval_check CHECK (step_interval_us BETWEEN 1 AND 60000000) ENFORCED,
 CONSTRAINT movement_rules_burst_steps_check CHECK (burst_steps BETWEEN 1 AND 39) ENFORCED,
 CONSTRAINT movement_rules_initial_credit_check CHECK (initial_credit_steps BETWEEN 1 AND burst_steps) ENFORCED,
 CONSTRAINT movement_rules_first_sequence_check CHECK (first_sequence BETWEEN 0 AND 39) ENFORCED,
 CONSTRAINT movement_rules_block_players_check CHECK (block_players IN (0,1)) ENFORCED,
 CONSTRAINT movement_rules_forbid_corner_check CHECK (forbid_corner_cut IN (0,1)) ENFORCED,
 CONSTRAINT movement_rules_allow_zero_check CHECK (allow_zero IN (0,1)) ENFORCED,
 CONSTRAINT movement_rules_design_id_check CHECK (design_id='CUSTOM-0150') ENFORCED
) ENGINE=InnoDB CHARACTER SET=utf8mb4 COLLATE=utf8mb4_0900_bin COMMENT='CUSTOM-0150 一般移動備援設定，非原廠公式或角色存檔';
