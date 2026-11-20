# Benchmark 20 驗證報告與第三階段準備

先建立 [Coverage Matrix](benchmark20_coverage.md)，再產生 [20 條 SQL](benchmark20.sql)。
這是 TPC-H-derived 自訂索引實驗，不是標準 TPC-H 22-query 測試或 QphH 成績。

## 結果檔與環境

- [Runner 原始結果](../benchmark/results/benchmark20-sf001-baseline.json)：20 條全數成功；
  每條 1 次 warmup、5 次正式測量，共 120 份完整 Plan、100 次正式測量。
- [最終逐條驗證](../benchmark/results/benchmark20-validation-final.json)：expected／actual
  predicates、候選、WHERE／JOIN 命中數、結果 digest、Plan relation／alias／join
  endpoints、環境及資料庫前後快照。
- [修正前證據](../benchmark/results/benchmark20-audit-before-fix.json)：Q08 的比較方向與
  人工規格不符；保留失敗紀錄，沒有替換查詢來通過驗證。

JSON 在上一階段已忽略的 benchmark/results/；本報告與人工規格保存在 workload/。
Workload SHA-256：a636adf71a656949cc13ce24c5ef3467778fe6240e47fd4e743c0bb3a8017ba2。
測量開始：2026-11-20 02:52:18 Asia/Taipei；JSON 為 2026-11-19T18:52:18.743444+00:00。

PostgreSQL 17.12 Windows；orders 15,000／lineitem 60,175；shared_buffers 128MB、
effective_cache_size 4GB、work_mem 4MB。沒有改變 server 設定。
前後筆數、欄位型別及 nullable、heap／total relation 大小、索引定義一致；
tpch 索引清單皆為空。原有 Benchmark Runner 檔案完全未修改。

## 逐條真實結果與 Advisor 核對

O=orders，L=lineitem。本地命中是完整 WHERE 相對整張表，不是 aggregate 輸出列數。
JOIN 命中另列；未篩選 INNER JOIN 共 60,175 列。時間為 5 次正式測量平均，
warmup 不計；Hit/Read 是根 Plan 執行階段計數。

| ID | 本地 WHERE 命中：列（比例） | JOIN 命中 | 輸出列數 | Exec ms | Plan ms | Hit / Read | Advisor |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| Q01 | O: 438（2.9200%） | — | 1 | 1.9812 | 0.1022 | 280 / 0 | 解析＋候選 |
| Q02 | O: 66（0.4400%） | — | 66 | 2.0386 | 0.0812 | 280 / 0 | 解析＋候選 |
| Q03 | O: 471（3.1400%） | — | 1 | 2.5516 | 0.1018 | 280 / 0 | 解析＋候選 |
| Q04 | O: 471（3.1400%） | — | 1 | 2.8680 | 0.1248 | 280 / 0 | 解析＋候選 |
| Q05 | O: 1,468（9.7867%） | — | 1 | 4.5544 | 0.0934 | 280 / 0 | 解析＋候選 |
| Q06 | O: 13（0.0867%） | — | 13 | 2.5042 | 0.0978 | 280 / 0 | 解析＋候選 |
| Q07 | O: 12（0.0800%） | — | 12 | 4.1492 | 0.1106 | 280 / 0 | 解析＋候選 |
| Q08 | O: 902（6.0133%） | — | 1 | 4.8946 | 0.1420 | 280 / 0 | 解析／無複合候選 |
| Q09 | L: 1,225（2.0357%） | — | 3 | 14.2668 | 0.1240 | 1248 / 0 | 解析＋候選 |
| Q10 | L: 30,049（49.9360%） | — | 1 | 17.4116 | 0.1102 | 1248 / 0 | 解析＋候選 |
| Q11 | L: 105（0.1745%） | — | 7 | 10.6128 | 0.1336 | 1248 / 0 | 解析＋候選 |
| Q12 | L: 256（0.4254%） | — | 256 | 10.6868 | 0.0880 | 1248 / 0 | 解析＋候選 |
| Q13 | L: 1,191（1.9792%） | — | 1 | 11.4870 | 0.0984 | 1248 / 0 | 解析／無複合候選 |
| Q14 | O: 438（2.9200%）／L: 14,902（24.7644%） | 699 | 5 | 13.5754 | 0.1680 | 1528 / 0 | 解析＋候選 |
| Q15 | O: 13（0.0867%）／L: 8,491（14.1105%） | 6 | 6 | 14.6768 | 0.2022 | 1528 / 0 | 解析＋候選 |
| Q16 | O: 1,477（9.8467%）／L: 32,260（53.6103%） | 272 | 110 | 15.4634 | 0.1764 | 1528 / 0 | 解析＋候選 |
| Q17 | O: 15,000（100%）／L: 150（0.2493%） | 150 | 5 | 17.1478 | 0.1622 | 1528 / 0 | 未支援，整條跳過 |
| Q18 | L: 1,339（2.2252%） | — | 1 | 16.6986 | 0.1082 | 1248 / 0 | 未支援，整條跳過 |
| Q19 | O: 3,104（20.6933%） | — | 1 | 2.7514 | 0.0868 | 280 / 0 | 未支援，整條跳過 |
| Q20 | O: 438（2.9200%） | — | 1 | 3.2254 | 0.0840 | 280 / 0 | 未支援，整條跳過 |

所有 scan relation／alias 均符合設計；Q14～Q17 的 Hash Cond 皆對應
O.o_orderkey=L.l_orderkey。Q01～Q16 逐條比較 schema／table／column／kind／operator
多重集合及完整候選集合（含欄位順序），不是只確認未拋例外。
Q14～Q16 的兩端 join predicate 也獨立核對；Q17 整條被跳過，不能宣稱 Advisor
成功解析其 JOIN，即使 PostgreSQL 可執行。

人工規格 [benchmark20_manifest.py](benchmark20_manifest.py) 獨立於 Advisor。
[validate_benchmark20.py](validate_benchmark20.py) 消費原 Runner 結果，不重寫測量；
另用唯讀 SELECT 計算命中數、結果 digest，檢查 Workload 與每條 SQL 的 SHA-256。

## Bug、未支援與索引適用性的區分

- 已修核心 Bug：Q08 的 `100000 <= o_totalprice` 原本記為欄位 `<=`，正確應為
  `>=`。只在 advisor/parser.py 常數置左分支加入反向映射，測試涵蓋五種比較。
  未修改成本／候選／選擇規則。現行 range 成本不使用方向，因此不能宣稱此修正
  改善成本預測或實測速度。
- 未支援語法：Q17 欄位對欄位 `<`、Q18 IN、Q19 OR、Q20 函式 predicate。
  保留原 SQL，整條警告並跳過，沒有只留下可解析子條件。這不等於不適合索引：
  Q17 的 mode／receiptdate 仍可能利用普通複合索引；IN／OR 也可能走多段或 bitmap。
- 候選生成限制：Q08／Q13 可正確解析，但 generator 最多取一個 range，又要求
  至少兩欄，故沒有複合候選。這不是 Parser Bug，也不是查詢沒有可用索引；
  第三階段仍需對照單欄與 range-leading 複合索引。
- 可能不值得建索引：Q10 命中約 49.94% 明細，SeqScan 可能合理。有候選不代表
  Planner 會採用或 workload 會變快。
- 相關性／冗餘：Q03／Q04 都命中 471 列，因本資料 1994 訂單皆符合 F。
  保留此觀察，不為製造差異換日期。Q10 獨立假設約 1/3×1/2=16.67%，實際 49.94%。
  Q01／Q02 命中 438／66 列，模型卻對相同 status/date 索引給同樣的 250.0833 分，
  因為沒有保存常數，range 選擇率固定為 0.25。
- 等價／非直接 sargable 對照：Q01／Q20 完整結果 digest 一致，均命中 438 列。
  Q20 expression 不直接形成普通日期 B-tree 的 range 條件；expression index 是
  另一方案，本階段沒建立，也不算 Advisor 已有能力。
- 本輪不修未觸發的 self-join alias 遺失等問題；Workload 無 self-join。排序／分組、
  覆蓋掃描、join 演算法、相關性及索引互動仍未完整進入成本模型。

14 條有候選、2 條解析但無候選、4 條未支援。全體去重後 19 個候選；共用包括
Q01/Q02 的 (status,date)、Q03/Q05 的 (priority,status)。Q11/Q12 有相同 supplier
前綴但不同 range 後綴。Q14～Q16 的 orderkey-leading 候選仍須與 filter-first 實測比較。

## 規模評估

SF0.01 適合功能／語意回歸，不適合作主要容量與實體 I/O 效益證據。

- 兩表 heap 共 12,517,376 bytes，約 11.94 MiB，小於 shared_buffers 128MB。
  本輪 100 次正式測量 Shared Read 全為 0，屬暖快取 baseline；Shared Read 也不能
  直接等同硬碟讀取。
- 19 個候選 heuristic 大小共 24,297,472 bytes，約 23.17 MiB，全部低於 100 MiB。
  因此 100／500／1024 MiB 都不足以形成有效預算壓力。沒有實際建索引，這些不是
  索引大小實測。
- 毫秒級延遲容易受量測開銷、背景負載與快取影響；固定鍵值查詢只命中十幾列，
  未涵蓋多個參數種子與隨機順序，不能概括所有分布。

建議下一步用 SF1 隔離資料庫：orders 約 1,500,000、lineitem 約 6,001,215 列
（TPC-H 3.0.1 §4.2.5.2），保留 SF0.01 回歸。以目前 heap 粗略乘 100 約 1.17 GiB，
候選大小粗略乘 100 約 2.26 GiB。這只是規劃外推，不是速度／儲存實測，須重新
取得統計。SF1 仍可能落在 OS cache；若需冷讀 I/O，再評估 SF10 與可控快取方法。

事前確認磁碟可同時容納 DuckDB 暫存、CSV、PostgreSQL heap、索引、WAL、結果；
另選新資料庫／明確 DSN，再用既有 dataset 工具產生／載入並 ANALYZE。
schema.sql 非冪等，不應重跑至現有 tpch schema。本階段未產生或匯入 SF1、
未修改 .env，也未清快取或重啟服務。

## 重現與第三階段準備

使用新輸出檔，避免覆蓋證據：

```powershell
.\.venv\Scripts\python.exe -B -m benchmark --workload workload/benchmark20.sql --warmup 1 --repeats 5 --label sf001-baseline --output benchmark/results/benchmark20-rerun.json
.\.venv\Scripts\python.exe -B -m workload.validate_benchmark20 --benchmark benchmark/results/benchmark20-rerun.json --output benchmark/results/benchmark20-rerun-audit.json
```

本輪 90/90 測試通過：80 項不需連線、10 項真實 PostgreSQL 測試。真實測試預設跳過：

```powershell
$env:BENCHMARK_TEST_POSTGRES = '1'
.\.venv\Scripts\python.exe -B -m unittest discover -s tests -v
Remove-Item Env:BENCHMARK_TEST_POSTGRES
```

第三階段須先準備：

1. 隔離 SF1 環境、凍結資料／SQL SHA／權重，保存版本、硬體、統計及完整 Planner
   設定。固定 ID 與低 distinct 類別命中數不會都隨 SF 線性放大，須重查分布。
2. 預先宣告 No index、single-column、suboptimal composite、Advisor 四種情境，
   定義完整索引清單與容量規則，另行授權受控建／移除索引。本候選集 19 個通常會
   觸發 >16 的 greedy，不能稱全域最佳；exact sensitivity 範圍也要先說明。
3. 比較 status/date 與 date/status、priority/status/date 的完整／缺欄前綴、
   supplier 兩種 range 後綴、join-key-first 與 filter-first；納入 range-only
   和寬 filter 控制組，不只檢查推薦查詢有無變快。
4. 各情境同樣跑 20 條、相同快取政策與次數，控制或交錯執行順序。主報告保留
   全 20 條，另列 16 條可解析子集合。未支援查詢也可能受其他索引影響，不能
   預設效益為 0 或靜默從分母刪除。
5. 實測 pg_relation_size()／索引清單、Plan 採用、Index Cond／殘餘 filter、
   buffer、sort／hash spill。以實際新增索引大小檢查預算，估計誤差另外報告。
6. IN／OR／欄位比較／expression 支援列為獨立開發與測試，不事後偷偷改寫 Q17～Q20。