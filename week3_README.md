# Week 3 第一階段：PostgreSQL Benchmark Runner

`benchmark/` 是獨立於 Week 2 Advisor 的真實測量工具。它讀取任意數量的
SQL 查詢，逐條執行 `EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON)`，保存原始
測量與完整 Query Plan。沒有建立／刪除索引、資料匯入或資料庫結構修改功能。

## 執行方式

沿用 `dataset/requirements.txt`、專案 `.venv` 與根目錄 `.env`。
`PGHOST`、`PGPORT`、`PGUSER`、`PGPASSWORD`、`PGDATABASE` 的讀取方式與
現有程式相同；既有環境變數優先於 `.env`。亦可傳入 `--dsn`。

在專案根目錄的 PowerShell 執行：

```powershell
.\.venv\Scripts\python.exe -B -m benchmark --workload workload/smoke.sql --warmup 1 --repeats 5 --output benchmark/results/smoke.json
```

正式 20 條 Workload 可直接換檔案，不需要修改程式：

```powershell
.\.venv\Scripts\python.exe -B -m benchmark --workload workload/queries20.sql --warmup 2 --repeats 10 --statement-timeout-ms 120000 --label sf10-baseline --output benchmark/results/sf10-baseline.json
```

`queries20.sql` 是未來正式 Workload 的示意路徑，目前未提供該檔案。

| 參數 | 預設值／意義 |
| --- | --- |
| `--workload` | `workload/smoke.sql`；UTF-8，可含 BOM |
| `--warmup` | 每條查詢 1 次，可設為 0 |
| `--repeats` | 每條查詢 5 次，至少 1 次 |
| `--statement-timeout-ms` | 每次 EXPLAIN 最長 60,000 ms，必須為正數 |
| `--connect-timeout` | 連線等待 5 秒，必須為正數 |
| `--dsn` | 未指定時使用 `.env`／libpq 設定；不會寫入結果 |
| `--label` | 實驗標籤；不會依名稱改變資料庫狀態 |
| `--output` | 選填，同時將 stdout JSON 存成新檔；拒絕覆蓋既有檔案 |

`benchmark/results/` 已由 Git 忽略。Exit code：全部查詢成功為 `0`；空檔案、
SQL 拒絕／錯誤、逾時、連線或輸出失敗為 `2`。即使部分查詢失敗，仍會輸出
JSON 並保留已完成的數據。重跑時請指定新的輸出檔名。

## 資料格式與測量定義

頂層包含 `schema_version`、Workload 路徑及 SHA-256、實驗標籤、UTC 起訖時間、
執行設定、伺服器版本／資料庫／部分 Planner 設定、整體狀態與摘要。
Workload 雜湊以解碼後、移除 UTF-8 BOM 的原始文字重新編碼 UTF-8 計算，保留 CR/LF。

每條 `queries[]` 保留原始 SQL（移除外側空白與分隔分號）、SQL SHA-256、編號、
狀態、`warmup_runs[]`、`measurements[]` 與 `summary`。每次成功執行包含：

- `execution_time_ms`：PostgreSQL 回報的 Execution Time。
- `planning_time_ms`：PostgreSQL 回報的 Planning Time。
- `shared_hit_blocks`、`shared_read_blocks`：**根 Plan 節點**的執行階段累計數；
  不加總子節點，避免重複計算。沒有 buffer 活動時為 0。
- `planning_shared_hit_blocks`、`planning_shared_read_blocks`：規劃階段的計數，
  與執行階段分開保存。
- `query_plan`：完整、未裁剪的 PostgreSQL JSON 陣列，包含所有 Plan 節點及其他欄位。
- `iteration`、`phase`、`status`、UTC 起訖時間。

暖機也保存完整原始數據，但不納入摘要。摘要僅對成功的正式測量計算
mean／median／min／max。失敗記錄包含錯誤類型、SQLSTATE 與主要診斷訊息；
若某條查詢在暖機或測量失敗，停止該條剩餘次數，再繼續下一條。先前成功的
測量會保留；若 warmup 失敗，該條沒有正式測量。查詢不會被靜默跳過。

這些時間是 EXPLAIN ANALYZE 下的伺服器測量，並非一般查詢端到端延遲；
不包含結果傳送至用戶端的耗時。Shared Read Blocks 是 PostgreSQL shared buffers
的讀入計數，可能由作業系統快取滿足，不能直接稱為實體磁碟讀取次數。

## SQL 與唯讀保護

SQL 切分獨立於 Advisor Parser，保留文字，支援分號分隔、註解、巢狀區塊註解、
引號字串與識別字、`E'...'`、`$$...$$`、`$tag$...$tag$`、最後一條沒有分號。
空白、註解與空陳述式不計入查詢數。未閉合的字串／註解會使整檔在連線前失敗。

允許 SELECT、唯讀 WITH、VALUES、TABLE，包括子查詢、聚合、CASE 等，不受
Week 2 Predicate Parser 的語法子集合限制。實際語法由 PostgreSQL 判斷。
這不是完整 PostgreSQL AST Parser；非引號內的寫入／控制關鍵字會被保守拒絕，
因此少數使用特殊關鍵字作為未加引號識別字的合法查詢也可能被拒絕。

安全層次：

1. 前置檢查拒絕 DML、DDL、SELECT INTO、寫入 CTE 與交易控制等語句。
2. 連線設定 `read_only=True`；**每次**暖機／測量建立新交易，明確執行
   `SET TRANSACTION READ ONLY` 並檢查 `transaction_read_only=on`。
3. 每次交易皆強制 ROLLBACK，即使成功也不提交查詢；錯誤不會污染下一次交易。
4. 使用 binary result 模式強制 extended query protocol，限制每次只能送一條 SQL，
   避免尾端陳述式繞過；不傳入查詢參數，讓原始 SQL 的 `%` 保持不變。
5. 每次設定 `standard_conforming_strings=on`，使伺服器與切分器的字串規則一致；
   設定 statement timeout；停用 prepared-plan 重用以量測各次 Planning Time。

僅使用自己審查過的可信分析查詢，並建議以最小讀取權限的資料庫帳號執行。
PostgreSQL READ ONLY 不是任意程式碼的沙箱，無法隔離自訂函式的外部副作用；
不要把不可信的函式呼叫、會改變 session 的函式或 psql 命令當成 Workload。
Runner 不執行用戶提供的 SET、DDL 或前置初始化腳本。

## 測試

不需要連線的測試及原有 Advisor 測試：

```powershell
.\.venv\Scripts\python.exe -B -m unittest discover -s tests -v
```

真實 PostgreSQL 測試預設跳過。確認 `.env` 指向已載入 SF0.01 的測試環境後，
可在獨立 PowerShell 執行：

```powershell
$env:BENCHMARK_TEST_POSTGRES = '1'
.\.venv\Scripts\python.exe -B -m unittest discover -s tests -p test_benchmark_postgres.py -v
Remove-Item Env:BENCHMARK_TEST_POSTGRES
```

真實測試包含：既有 3 條 smoke、1／4／20 條、空檔案、錯誤 SQL 後繼續、
逾時後繼續、伺服器唯讀保護、單陳述式協定保護，以及兩表筆數與索引清單前後一致。
測試不建立／刪除任何資料庫物件。安全測試使用會被唯讀交易拒絕的
`SELECT ... FOR SHARE`，不提交 DML／DDL。

## 第二階段注意事項

- 目前僅提供測量基礎，尚未執行建立索引、四種索引情境比較、容量預算掃描或 Pareto 曲線。
  第二階段需另外設計受控、明確授權的索引管理流程；本 Runner 可直接重用。
- 正式 20 條查詢仍須編製並先驗證。Runner 能跑較複雜 SQL，不代表 Week 2 Advisor
  也能解析與推薦，兩者成功／跳過數要分別核對。
- 執行順序為逐條查詢先暖機、再重複測量；沒有強制清空 shared buffers／OS cache，
  也沒有隨機交錯各種索引情境。第二階段要控制快取、背景負載與執行順序偏差。
- 每次測量使用新的 READ COMMITTED 交易／snapshot，未固定整個實驗的 snapshot；
  應使用內容穩定的 benchmark 資料庫。
- 應額外保存資料規模、索引定義與實際大小、各情境的完整 Planner 設定與環境資訊，
  再解讀 latency／buffer／storage 的差異。結果中的 label 只是使用者標籤。
- 報告在執行結束時寫入；強制終止程序可能使本次結果來不及保存，尚未提供斷點續跑。

參考：[PostgreSQL EXPLAIN](https://www.postgresql.org/docs/17/sql-explain.html)、
[唯讀交易](https://www.postgresql.org/docs/17/sql-set-transaction.html)、
[psycopg 交易控制](https://www.psycopg.org/psycopg3/docs/basic/transactions.html)。
