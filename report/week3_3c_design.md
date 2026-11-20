# Week 3C：Index Strategy Benchmark 開發與審查方案

本輪只開發、測試、唯讀 plan／dry-run；**未執行 CREATE INDEX、DROP INDEX、COMMENT
ON INDEX 或正式效能測量**。既有 advisor_smoke、.env、正式 SQL、Advisor、Runner
均不修改；3A／3B 不重做，Q17～Q20 保持 Advisor 未支援。

## 本次審查的固定產物

- [完整計畫 JSON](../benchmark/results/3c-review-v2/plan.json)：固定統計、策略配置、
  來源查詢、排序決策、環境、所有索引名稱、48-cell 排程與程式檔 hash。
- [完整 DDL 預覽](../benchmark/results/3c-review-v2/planned-ddl.sql)：每個 cell 的 CREATE、
  ownership COMMENT 與受限 DROP 預覽。**不可把此檔當整批 SQL 手動執行**；它是審查清單，
  正式控制器會分 cell 建立、量測、清理並逐次驗證。
- [真實唯讀 dry-run](../benchmark/results/3c-review-v2/dry-run.json)。

本版 run id：`e4b8de6111b3`。
Plan SHA-256：`a8024363ffca87990ef8536653a2641a9264cc7a49ea1ae0990b28bc3310a8cd`。
其他 initial／final 草稿目錄是開發中間產物，本次只審查 **3c-review-v2**。

## 四種策略的生成規則

Baseline：不新增任何索引。現在 tpch 索引清單為空；若正式執行前有外來索引或
環境改變就拒絕執行，不擅自清掉它。Baseline 在三種預算、每一輪都重新測量，作
同 round／budget 的配對參考。

Single-Column：使用人工核對的完整 20 條查詢中 WHERE／JOIN 引用的 17 個欄位，
包括 IN／OR／日期比較等 Advisor 不支援案例中的欄位。只建立普通單欄 B-tree，
不把 SELECT-only 欄位或常數 shippriority 放入候選。

Suboptimal Composite：採每條查詢每表 WHERE 出現順序，再接 ON 欄位，去重後取
最多 3 欄，至少 2 欄，得到 20 個候選。這是 **unoptimized/source-order** 對照，
不刻意反轉成最差順序；名稱不保證實際一定較慢，filter-first 有時可能勝過 Advisor。
相同欄位集合的不同排列只保留最早來源查詢的原序，避免花預算買重複排列。

兩種對照均按「引用全部 key 欄位的查詢數降冪 → 預估 bytes 升冪 → label」排序，
依預算先到先選，跳過超額候選及與已選索引有 ordered-prefix 重疊者。引用次數只是
透明的選取依據，不代表 Planner 一定使用，也不是實際效益。沒有用事後 latency
挑控制組，沒有用 Advisor 的 benefit score 為對照挑選更差索引。

Advisor：原封使用 3B 最終保存的 19 候選／統計／選擇，並以現有實作重算核對。
max_columns=3、max_candidates=40、權重皆 1；100 MiB 保留 exact（12 個可行候選），
500／1024 MiB 保留 marginal-greedy（19 個可行候選），不改演算法與語法範圍。
對照使用全 20 條的欄位，Advisor 只有 16 條可解析，這項差異公開報告而不隱藏。

## 完整索引配置與預估容量

以下 key 順序即實際建議建立順序；具體名稱依 cell 生成，見 plan／DDL。
所有容量為 3B 相同公式的**預估**值，dry-run 沒有實測新索引大小。

| Budget MiB | Strategy | Complete index configuration | Estimated MiB |
| ---: | --- | --- | ---: |
| 100 | baseline | (none) | 0.000000 |
| 100 | single | `tpch.orders(o_orderdate)`<br>`tpch.orders(o_orderstatus)` | 73.390625 |
| 100 | suboptimal | `tpch.orders(o_orderstatus, o_orderdate)`<br>`tpch.orders(o_custkey, o_orderdate)` | 96.570312 |
| 100 | advisor | `tpch.orders(o_orderkey, o_orderstatus)`<br>`tpch.orders(o_orderstatus, o_orderdate)` | 92.710938 |
| 500 | baseline | (none) | 0.000000 |
| 500 | single | `tpch.orders(o_orderdate)`<br>`tpch.orders(o_orderstatus)`<br>`tpch.lineitem(l_shipdate)`<br>`tpch.orders(o_orderkey)`<br>`tpch.orders(o_orderpriority)`<br>`tpch.orders(o_custkey)`<br>`tpch.orders(o_totalprice)`<br>`tpch.orders(o_clerk)` | 490.585938 |
| 500 | suboptimal | `tpch.orders(o_orderstatus, o_orderdate)`<br>`tpch.orders(o_orderpriority, o_orderdate)`<br>`tpch.lineitem(l_shipmode, l_shipdate)`<br>`tpch.orders(o_custkey, o_orderdate)`<br>`tpch.orders(o_orderpriority, o_orderstatus)` | 471.273438 |
| 500 | advisor | `tpch.orders(o_orderstatus, o_orderdate)`<br>`tpch.lineitem(l_orderkey, l_returnflag)`<br>`tpch.orders(o_orderkey, o_orderstatus)`<br>`tpch.lineitem(l_returnflag, l_linestatus)` | 448.125000 |
| 1024 | baseline | (none) | 0.000000 |
| 1024 | single | `tpch.orders(o_orderdate)`<br>`tpch.orders(o_orderstatus)`<br>`tpch.lineitem(l_shipdate)`<br>`tpch.orders(o_orderkey)`<br>`tpch.orders(o_orderpriority)`<br>`tpch.lineitem(l_orderkey)`<br>`tpch.lineitem(l_shipmode)`<br>`tpch.orders(o_custkey)`<br>`tpch.orders(o_totalprice)`<br>`tpch.lineitem(l_returnflag)`<br>`tpch.orders(o_clerk)` | 1023.703125 |
| 1024 | suboptimal | `tpch.orders(o_orderstatus, o_orderdate)`<br>`tpch.orders(o_orderpriority, o_orderdate)`<br>`tpch.lineitem(l_shipmode, l_shipdate)`<br>`tpch.orders(o_custkey, o_orderdate)`<br>`tpch.orders(o_orderpriority, o_orderstatus)`<br>`tpch.lineitem(l_shipdate, l_orderkey)`<br>`tpch.lineitem(l_shipmode, l_orderkey)`<br>`tpch.orders(o_totalprice, o_orderdate)` | 1012.109375 |
| 1024 | advisor | `tpch.orders(o_orderstatus, o_orderdate)`<br>`tpch.lineitem(l_orderkey, l_returnflag)`<br>`tpch.orders(o_orderkey, o_orderstatus)`<br>`tpch.lineitem(l_suppkey, l_shipdate)`<br>`tpch.lineitem(l_returnflag, l_linestatus)`<br>`tpch.orders(o_custkey, o_orderdate)`<br>`tpch.lineitem(l_shipmode, l_shipdate)`<br>`tpch.orders(o_orderpriority, o_orderstatus)` | 1023.718750 |


## 實際預算的固定處理規則

三個正式預算維持 100／500／1024 MiB，1 MiB=1,048,576 bytes。

1. 先凍結估計配置，正式執行不因實際索引較小而補買新索引。
2. 每個 cell 的所有 CREATE 與 ownership COMMENT 放在同一個非 concurrent 交易。
   每建立一個索引就驗證 catalog 身分，讀取 pg_relation_size 的 main-fork bytes，
   同時保存 pg_total_relation_size 作補充。
3. 新增索引 main-fork 總和一旦超過 cap，拋出錯誤並**整組交易回滾**，標記
   budget_exceeded／不可行，跳過該組 performance measurement。保留已嘗試的實際
   bytes（可能是部分配置，但已足以證明超額），不刪減、不重新挑選、不把失敗當 0 ms。
4. 容量合格才量測；量測後再檢查索引清單與實際總大小。若過程改變則整次停止並清理。
5. summary 明列不可行 cell；有不可行組時標為 complete_with_infeasible_configurations，
   all_configurations_budget_feasible=false，speedup=null，不宣稱所有組通過。

估計值與 PostgreSQL B-tree 實際布局／重複 key 壓縮可能有差距。1024 MiB 的 Single
與 Advisor 估計都很接近上限，實際可行性尚未知。本規則公平套用所有策略，但也表示
比較的是「凍結估計配置＋實際 cap 驗收」，不是每個 cap 下依實測大小重新最佳化。

## 測量、快取與順序

建議本版使用 warmup=2、repeats=5、rounds=4、seed=20261120、每次查詢 120 秒 timeout。
共有 3 budgets × 4 strategies × 4 rounds＝48 個 cell。若全部可行：

- 每條 SQL 每 cell 保存 2 次暖機與 5 次正式測量；總計 1,920 次暖機、4,800 次正式測量。
- 需建／清理 200 個 cell-specific 索引（重複配置在不同 cell 用不同名稱重建）；
  這是預計操作數，budget_exceeded 或中斷時實際執行數會較少。
- 所有 cell 都執行完整 20 條，另整理 Q01～Q16；不把未支援的 Q17～Q20 移出量測。
- 每次保留原 Runner 的 Execution／Planning Time、Buffers、完整 JSON Plan，
  遞迴擷取 Index Scan／Index Only Scan／Bitmap Index Scan 等的 Index Name、OID、定義。
- Query number 會映射回原 Q01～Q20，另外保留 execution_position／query_order；
  不會因隨機順序把 Q17 誤標成支援查詢。
- full20／advisor16 分別計算 sum of per-query mean execution time；speedup 僅配對
  同 round／budget 的 Baseline。這不是端到端牆鐘時間，任何失敗不以較少查詢數計分。

四策略的 Williams 平衡順序（每個 budget 都相同）：

| round | 執行順序 |
| ---: | --- |
| 1 | Baseline → Single → Advisor → Suboptimal |
| 2 | Single → Suboptimal → Baseline → Advisor |
| 3 | Suboptimal → Advisor → Single → Baseline |
| 4 | Advisor → Baseline → Suboptimal → Single |

三個 budget 的各輪順序也由 seed 固定打散；同 round／budget 四策略使用同一個
打散後的 20-query 順序。各策略在四個位置各出現一次，各有向相鄰配對各出現一次。

快取政策是暖快取，不清 OS cache、不重啟、不安裝 pg_prewarm。每個 cell 建置完成後，
在兩表 SHARE lock 下先完整讀取資料內容 signature 作相同 cache preconditioning，
再用原 Runner 執行等量暖機與測量；記錄 prewarm 時間、maintenance、統計／環境 hash。
這能標準化暖機流程，**不保證所有頁都在 shared buffers，也不是冷讀 I/O 實驗**。

內容 signature 為 count＋兩個 seeded hashtextextended(row_to_json) 的 numeric sum，
同 PostgreSQL 版本可重現；是非惡意資料的機率性檢查，不是密碼學完整性證明。
跨 cell／最後內容與筆數必須一致。SHARE lock 在量測期間阻擋 DML／相關維護；
cleanup 前釋放，以免與 DROP 的表鎖互相阻塞。
表 OID／型別／NOT NULL／collation、heap page／visibility 統計、column stats、Planner
設定、外來索引改變或有其他 active client／maintenance 時停止，要求新計畫審查。
不關閉 autovacuum，不改全域設定；仍需安排 exclusive experiment window，無法隔離
其他資料庫／OS 的 CPU、磁碟背景負載。索引建置與 preconditioning 時間不計入查詢時間。

## 名稱追蹤、安全清理與失敗復原

目標固定為 advisor_benchmark，並核對 database OID、PostgreSQL system_identifier、
server／role；不能改到 advisor_smoke。正式執行先取得同資料庫 advisory session lock，
避免兩個控制器同時執行。鎖等待 5 秒，索引建置單指令最長 15 分鐘。

名稱格式：g9c_<run-id>_<cell-id>_<key-hash>，ASCII 且少於 63 bytes。沒有 IF NOT EXISTS，
遇到任何同名物件拒絕採用／覆蓋。

- CREATE 前先 fsync durable journal 的 pending intent；CREATE 與專屬 COMMENT 同交易。
- COMMIT 後保存 index OID、table OID、完整 definition。若 COMMIT 後來不及寫 OID 就
  中斷，pending intent＋原子 COMMENT＋精確 key／owner 等仍可辨識已建立的自有物件。
- DROP 前取得短暫表 ACCESS EXCLUSIVE lock，**先驗證全部候選再刪任何一個**：journal
  規格、名稱、OID（若已知）、table OID／definition（若已知）、owner、專屬 tag、
  btree／key／valid／ready／非 unique／無 constraint／非 expression／非 partial。
- 只發出該 run 記錄中的 DROP INDEX ... RESTRICT，沒有 CASCADE、按 prefix 全刪或刪庫。
  不匹配、遭改名、同名替換、未記錄的標記物件均停止供人工審查，不擅自刪除。
- 正常策略切換即清理本 cell，再確認原始 inventory。例外／Ctrl-C 也嘗試受限清理；
  連線或清理失敗則 journal 標 cleanup_required。原始 Runner 部分數據、錯誤與 journal 保留。
- recover 預設只是唯讀預覽；實際清理還需 --execute 與該 run-id 的批准。
  不自動續跑失敗效能測量，避免混用未知快取狀態；清理後重新審查新計畫／新 run。

普通非 concurrent CREATE／DROP 才能用上述交易回滾；DROP 的表鎖可能阻擋其他操作，
因此需獨占時段與 timeout。[CREATE INDEX](https://www.postgresql.org/docs/17/sql-createindex.html)、
[DROP INDEX](https://www.postgresql.org/docs/17/sql-dropindex.html)。

## Dry-run、測試與限制

真實 dry-run 成功：48 cells、200 個預計 CREATE；前後索引皆空、ddl_executed=false、
workload_executed=false、actual_index_sizes_measured=false。dry-run 連線本身使用唯讀交易，
寫入 API 有獨立拒絕開關，也不取得執行鎖或做全表 prewarm。

新增 23 項自動測試通過；全套 135 項中 **125 通過、10 項 opt-in 資料庫 benchmark 略過**。
涵蓋平衡排程、全 20／16 子集合、策略來源、無重複排列／前綴、plan tamper、
超額回滾、外來索引拒刪、OID／definition 替換、journal crash window、Runner 中斷、
清理失敗及 recover 預覽／復原。所有建／刪索引測試使用 mock／in-memory fake DB；
**這不等於已通過 PostgreSQL 真正 DDL 或正式效能驗證**。

新增原始碼：strategy_benchmark/ 的 plan、database、engine、main 與 package entries；
tests/test_strategy_benchmark.py；本報告及 ignored 的審查產物。既有模組未重寫。
actual-size 超標可能讓正式比較有缺組；若需要「各策略都能在實測 cap 下挑滿」，
那是另一個必須先審查的校準／重選實驗，本版不偷偷加入。

## CLI：本輪只執行前兩種

```powershell
# 重新產生審查資料時必須使用新的 output-dir；本版已產生。
.\.venv\Scripts\python.exe -B -m strategy_benchmark plan --source-3b benchmark/results/sf1-3b-budgets-final.json --acceptance benchmark/results/sf1-3a-integrity.json --output-dir benchmark/results/3c-review-v3 --warmup 2 --repeats 5 --rounds 4 --seed 20261120

# 唯讀 dry-run；新 output 路徑避免覆蓋。
.\.venv\Scripts\python.exe -B -m strategy_benchmark dry-run --plan benchmark/results/3c-review-v2/plan.json --output benchmark/results/3c-review-v2/dry-run-rerun.json
```

以下**未執行，須使用者確認正式實驗方案後才可執行**；執行目錄也必須尚不存在：

```powershell
.\.venv\Scripts\python.exe -B -m strategy_benchmark run --plan benchmark/results/3c-review-v2/plan.json --run-dir benchmark/results/strategy-run-e4b8de6111b3 --approve-plan-sha256 a8024363ffca87990ef8536653a2641a9264cc7a49ea1ae0990b28bc3310a8cd

# 若失敗，先預覽；不會刪索引。
.\.venv\Scripts\python.exe -B -m strategy_benchmark recover --run-dir benchmark/results/strategy-run-e4b8de6111b3

# 確認該次復原後才可執行：只處理符合 journal 的自有索引。
.\.venv\Scripts\python.exe -B -m strategy_benchmark recover --run-dir benchmark/results/strategy-run-e4b8de6111b3 --execute --approve-run-id e4b8de6111b3
```

正式開發／環境／統計若改變，必須重新產生 plan 與取得新 SHA 的確認，不能移除檢查
硬跑舊計畫。本輪停止於開發＋dry-run，等待對配置、strict-infeasible、暖快取與排程的確認。
