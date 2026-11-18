# Week 2 — Workload-Driven Composite Index Advisor

本階段以 Week 1 的 `dataset/`、`workload/` 為基礎，實作 Python 版複合索引推薦工具。Advisor 從 SQL 工作負載及 PostgreSQL 統計資料產生候選索引，在指定的**預估儲存預算**內選出建議組合，輸出 JSON 和 `CREATE INDEX` DDL；**不會自動建立索引或修改資料庫**。

## 1. 已實作的功能

| 模組 | 功能 |
| --- | --- |
| `advisor/parser.py` | 解析 SQL 的 WHERE 等值／範圍條件、INNER JOIN 等值欄位與別名；無法安全解析的查詢會警告並跳過。 |
| `advisor/statistics.py` | 唯讀查詢 PostgreSQL 的 `pg_class`、`pg_stats`，取得資料表與欄位統計資料。 |
| `advisor/candidates.py` | 依 equality-first、distinctness 等規則產生 B-tree 複合索引候選。 |
| `advisor/cost_model.py` | 估算索引空間與工作負載效益分數（均為啟發式估計）。 |
| `advisor/optimizer.py` | 在預估空間預算下選擇索引組合；可行正效益候選不超過 16 個時完整搜尋，較多時採 greedy。 |
| `advisor/main.py` | 串接推薦流程，輸出 JSON 結果與建議 DDL；先篩選預算可行候選，再套用 `--max-candidates` 短名單限制。 |
| `tests/` | 自動化測試與回歸測試，用來檢查 Parser、候選產生、預算選擇及整合流程。 |

## 2. 在 Windows + VS Code 執行

**前提：** 已依 Week 1 設定 Python `.venv`、PostgreSQL、`.env`，並已將 TPC-H 測試資料匯入 `advisor_smoke`。在專案根目錄開啟 VS Code 的 PowerShell 終端機。

```powershell
# 安裝／確認 Week 1 既有依賴
.\.venv\Scripts\python.exe -m pip install -r dataset/requirements.txt

# 執行自動化測試
.\.venv\Scripts\python.exe -m unittest discover -s tests -v

# 執行 Advisor（100 MiB 預估索引預算）
.\.venv\Scripts\python.exe -m advisor --workload workload/smoke.sql --budget-mb 100 --output advisor-results.json

# 測試較小的預算（1 MiB）
.\.venv\Scripts\python.exe -m advisor --workload workload/smoke.sql --budget-mb 1 --output advisor-results-1mb.json
```

`.env` 須具備 `PGHOST`、`PGPORT`、`PGUSER`、`PGPASSWORD`、`PGDATABASE`；請勿提交 `.env` 或分享密碼。可使用 `python -m advisor --help` 查看其他參數。

**驗證方式：** 檢查 JSON 的 `parsed_queries`、`skipped_queries`、`warnings`，並確認 `estimated_selected_bytes <= budget_bytes`。本機 Windows／PostgreSQL 17.12／TPC-H SF0.01 已驗證：**38/38 項自動化測試通過**；3 條 Smoke SQL 全部解析；100 MiB 預算推薦 4 個索引、估計使用 5,701,632 bytes；1 MiB 預算推薦 2 個索引、估計使用 983,040 bytes。這是功能與整合測試，**不是實際查詢效能測試**。

### 自訂查詢頻率

可新增 `workload/weights.json`（選填）：

```json
{"1": 5, "2": 1, "3": 10}
```

此處的 `1`、`2`、`3` 分別表示 `workload/smoke.sql` 中第 1～3 條 SQL，數值代表頻率權重。

```powershell
.\.venv\Scripts\python.exe -m advisor --workload workload/smoke.sql --weights workload/weights.json --budget-mb 100
```

## 3. 已知限制與尚未實作的功能

- **SQL Parser 並非完整 PostgreSQL Parser：** 目前主要支援 `SELECT`、`INNER JOIN`、純 `AND` 條件（含括號群組）、比較運算子 `=`／`<`／`<=`／`>`／`>=` 及 `DATE` 字面值；不支援 `OR`、`IN`、`BETWEEN`、`EXISTS`、子查詢、CTE、外連接與任意函式比較等。正式 Workload 應先驗證每條 SQL 是否成功解析。
- **候選範圍：** 專注複合索引，不產生單欄位索引候選；欄位選擇性參考 `n_distinct`，範圍條件暫用固定 `0.25` 選擇率假設，尚未根據查詢常數、histogram 或欄位相關性精準估算。
- **估計值不是實測：** `estimated_bytes`、Benefit Score 是啟發式估算，不代表實際磁碟使用量、PostgreSQL Planner 成本、延遲或 Buffer I/O；也不保證推薦索引一定被採用或提升效能。
- **最佳化範圍有限：** 候選數大於 16 時改用 greedy。`--max-candidates` 是進入 Optimizer 的候選短名單上限，**不是最終最多選 K 個索引**；若 `candidate_limit_applied=true`，即使顯示 `exact-within-shortlist`，也不能宣稱對全部候選全域最佳。
- **Workload 來源：** 目前讀取 `.sql` 檔與選填的 `weights.json`，尚未直接整合 `pg_stat_statements` 或 SQL log，也未提供獨立的最終 Top-K 索引數量參數。
- **資料庫統計與實際效能：** 尚需驗證未 `ANALYZE` 或統計異常的資料表情境。推薦 DDL 不會自動執行；Week 3 應透過受控 Benchmark 實際建立／移除索引，使用 `EXPLAIN (ANALYZE, BUFFERS)` 及 `pg_relation_size()` 驗證延遲、I/O 與儲存空間，並在較大 TPC-H 規模及正式 Workload 上比較。

> **給後續開發者：** 修改 `advisor/` 或增加 SQL Workload 後，請重新執行 `python -m unittest discover -s tests -v`，並檢查 Advisor 輸出中的 `warnings`，避免未解析的查詢被誤當作成功推薦。
