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

## 如何生成 Dataset

### 安裝需求

| 項目 | 怎麼安裝 | 用途 |
| --- | --- | --- |
| Python 3.11（64 位元） | 安裝 Windows 版 Python，勾選 `Add python.exe to PATH` | 執行資料生成與匯入腳本。專案已用此版本驗證資料生成 |
| `duckdb==1.4.3` | 用下方的 `pip install -r dataset/requirements.txt` 安裝到專案的 `.venv` | 生成 TPC-H CSV。Python 套件已包含 DuckDB 引擎 |
| DuckDB `tpch` 擴充套件 | 第一次執行 `generate` 時由腳本自動下載 | 產生 TPC-H 的原始資料 |
| `psycopg[binary]==3.2.13` | 與 DuckDB 一起由下方的 `pip` 指令安裝 | 匯入 CSV 時連線到 PostgreSQL |
| PostgreSQL 16 或 17 | 到匯入階段再安裝伺服器，或使用現有的 PostgreSQL 16/17 | 儲存資料並執行 advisor 和索引實驗 |

只生成 CSV 時，安裝 Python 並執行下方的套件安裝指令即可。首次安裝套件與下載 `tpch` 擴充套件需要網路。

### Windows PowerShell 指令

在專案根目錄執行以下指令，先確認 Python 再建立環境。

```powershell
python --version
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r dataset/requirements.txt
```

依用途選擇一條指令執行。

```powershell
.\.venv\Scripts\python.exe dataset/tpch.py generate --scale 0.01 --output dataset/data/sf0.01
.\.venv\Scripts\python.exe dataset/tpch.py generate --scale 1 --output dataset/data/sf1
.\.venv\Scripts\python.exe dataset/tpch.py generate --scale 10 --output dataset/data/sf10
```

如需重新生成，將 `--output` 改成尚未存在的目錄。生成 SF10 時請為暫存資料與 CSV 預留數十 GB。
