# Current Client Manifest Source Check

Read-only check prompted by the unresolved original monster attack/defense
values. This tests whether the current package manifest lists missing data
tables; it does not assign statistics from filenames or CRC values.

Only three files from the current client root were decoded with the existing
bounded CSVZ decoder. No retired archive, historical server, network location,
Save file, account log or configuration body was opened.

| Current root file | SHA256 | Decoded SHA256 |
| --- | --- | --- |
| client.godZ | fc391917f16b2a59fdb95e63d5a004fb05d61f545a3633394a6301e9241de452 | f012b29ffbaade32e4d3c80625a19fe7e2e917270df696db8f92736c2053e7f1 |
| client_p.godZ | 49cbf5f7813053d57961fe621cbf6ea4bef4c8fed6371e6dca79f3d903ec1f92 | de8acdcef8ee61f52f6be9f43ff58566f8819cd47387952a9cc215e1bcd4152f |
| god_crc.txtZ | 11fc8f6e93dbaa3097747f8a3415a0b321379a079b112f02b6ff16ac1b5b0fb1 | 77dc9f26b91d0ce8285217caae84435289d60eaea828619038923b4927e55060 |

All three decode to file-list text, not a monster stat table. No host path
embedded in the text was followed. Current `client.godZ` has 9584 physical
lines, 9117 file records, and a matching declared total at line9580.
`Directory :` entries provide relative paths; each file row was parsed by
the standard CSV reader as filename, decimal size, decimal CRC and date.
Absolute paths and parent traversal were rejected before joining the current
root. The two other lists were inspected as format evidence, not independently
compared file-by-file.

All9117 listed files exist locally. Size comparison found one mismatch:
`Data3/config.iniZ`, listed331 bytes versus current102 bytes. Its body was not
read or changed and it is not proposed as a combat-value source.

The73 listed CSVZ/BIN files under Data, Data2 and Data3 were read and their
raw CRC32 values checked against the list: all73 match. This consists of
72 CSVZ and the one BIN. Other file bodies were not hashed in this check.
There is therefore no manifest-listed missing CSVZ/BIN to nominate as a
new numeric source in this bounded result.

The manifest is not a signed authenticity certificate. It is not proof of
complete semantic analysis, a universal absence of client-side numeric data,
or original server values. Unexamined binary consumers remain unexamined.
No original monster value, formula, database row or runtime rule is promoted.
