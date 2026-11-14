# Workload-Driven Composite Index Advisor

## 已完成的 Dataset

用 DuckDB 的 TPC-H 擴充套件生成了 SF0.01 和 SF10 的 `orders.csv` 與 `lineitem.csv`，並核對各檔案的筆數。CSV 存在本機的 `dataset/data/`，此目錄已排除在 Git 之外。也已加入 PostgreSQL schema 和匯入指令，實際匯入仍待驗證。

### Scale factor 差異

`--scale` 控制生成的資料量。以 SF1 為基準，SF0.01 約是其 1% 的資料量，SF10 約是其 10 倍。`orders` 的列數隨 scale 成比例增加，`lineitem` 的列數會隨每筆訂單的明細數略有變動。

| Scale factor | orders 筆數 | lineitem 筆數 | 兩個 CSV 合計 | 用途 |
| --- | ---: | ---: | ---: | --- |
| 0.01 | 15,000 | 60,175 | 約 9.1 MB | 快速驗證生成與匯入 |
| 1 | 1,500,000 | 約 6,000,000 | 約 1 GB（估計） | 日常開發與查詢測試 |
| 10 | 15,000,000 | 59,986,052 | 約 9.68 GB | 正式索引容量實驗 |

## 安裝 Python 套件

在專案根目錄執行一次。套件會裝在專案的 `.venv` 資料夾，該資料夾已由 Git 忽略。後續指令直接使用 `.venv` 裡的 Python。

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r dataset/requirements.txt
```

## 匯入 SF0.01 到 PostgreSQL

如果專案根目錄已有 `.env`，且 `dataset/data/sf0.01/` 已有 CSV，可直接在專案根目錄執行下列 PowerShell 指令。新環境可從 `.env.example` 複製出 `.env` 並填入連線資料。`.env` 由 Git 忽略。

```powershell
.\.venv\Scripts\python.exe dataset/tpch.py create-db
.\.venv\Scripts\python.exe dataset/tpch.py load --source dataset/data/sf0.01
```

`create-db` 會從 `.env` 讀取連線設定與 `PGDATABASE`（測試環境為 `advisor_smoke`），資料庫已存在時會直接返回。建立資料庫、匯入和重跑查詢都會讀取同一份 `.env`，已設定的環境變數優先。匯入成功後會執行 `ANALYZE`，並顯示 `tpch.orders` 有 15,000 筆、`tpch.lineitem` 有 60,175 筆。

## 執行 SQL 查詢

匯入 SF0.01 後，在專案根目錄執行下列指令。程式會從 `.env` 讀取 PostgreSQL 連線設定，並以唯讀模式執行 `workload/smoke.sql`。

```powershell
.\.venv\Scripts\python.exe workload/run_queries.py
```

也可以將其他唯讀查詢存成 `.sql`，並將路徑傳給同一支程式。例如將查詢存成 `workload/orders.sql` 後執行：

```powershell
.\.venv\Scripts\python.exe workload/run_queries.py workload/orders.sql
```

SQL 檔可以包含多條以分號分隔的 PostgreSQL 查詢。每組結果會列出欄名與所有資料列，以定位字元分隔。建立索引、更新資料及 `psql` 專用的反斜線指令需使用其他執行方式。

## 如何重新生成 Dataset

### 安裝需求

| 項目 | 怎麼安裝 | 用途 |
| --- | --- | --- |
| Python 3.11（64 位元） | 安裝 Windows 版 Python，勾選 `Add python.exe to PATH` | 執行資料生成與匯入腳本。專案已用此版本驗證資料生成 |
| `duckdb==1.4.3` | 由上面的 `pip` 指令安裝到 `.venv` | 生成 TPC-H CSV。Python 套件已包含 DuckDB 引擎 |
| DuckDB `tpch` 擴充套件 | 第一次執行 `generate` 時由腳本自動下載 | 產生 TPC-H 的原始資料 |
| `psycopg[binary]==3.2.13` | 與 DuckDB 一起由上面的 `pip` 指令安裝 | 匯入 CSV 時連線到 PostgreSQL |
| `python-dotenv==1.2.1` | 由上面的 `pip` 指令安裝 | 匯入時讀取專案根目錄的 `.env` |
| PostgreSQL 17.12 | 目前本機已安裝。新環境可安裝同版本來重現實驗 | 儲存資料並執行 advisor 和索引實驗 |

只生成 CSV 時，安裝 Python 並執行上面的套件安裝指令即可。首次安裝套件與下載 `tpch` 擴充套件需要網路。

### Windows PowerShell 指令

在專案根目錄依用途選擇一條指令執行。

```powershell
.\.venv\Scripts\python.exe dataset/tpch.py generate --scale 0.01 --output dataset/data/sf0.01
.\.venv\Scripts\python.exe dataset/tpch.py generate --scale 1 --output dataset/data/sf1
.\.venv\Scripts\python.exe dataset/tpch.py generate --scale 10 --output dataset/data/sf10
```

如需重新生成，將 `--output` 改成尚未存在的目錄。生成 SF10 時請為暫存資料與 CSV 預留數十 GB。
