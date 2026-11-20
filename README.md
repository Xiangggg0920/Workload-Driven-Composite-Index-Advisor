# Workload-Driven Composite Index Advisor

## 1. 專案介紹

這個專題從 SQL 工作負載與 PostgreSQL 統計資料產生複合索引建議，再實際測量不同索引配置的查詢時間、Buffers 和儲存空間。

| 階段 | 完成內容 |
| --- | --- |
| Week 1 | 建立 TPC-H 資料生成、Schema 與 PostgreSQL 匯入流程 |
| Week 2 | 實作 SQL 解析、候選索引、成本估算與預算選擇 |
| Week 3 | 比較 Baseline、Single-column、Suboptimal、Advisor，完成四輪測量與圖表 |

正式實驗使用 TPC-H SF1 的 orders／lineitem 和[二十條 SQL](workload/benchmark20.sql)。GitHub 的 `week2-week3` 分支已附上 **4 策略 × 3 預算 × 4 輪**的成果，48 組皆完成，包含 1,920 次暖機與 4,800 次正式測量。

組員 Clone 後可以直接看 CSV 和圖表來分析、寫報告，**不用先重跑原環境約 2.5 小時的 Benchmark**：

- [分析與圖表](benchmark/results/3c-four-rounds-2beee5cb9384/analysis/)：先看 `aggregates.csv`、`analysis.json` 與 PNG／PDF；逐查詢資料在 `queries.csv`，每次測量在 `attempts.csv`。
- [原始測量與計畫](benchmark/results/3c-four-rounds-2beee5cb9384/run/)：保留時間、Buffers、完整 Query Plan、索引配置與容量。

想自行重現時，再照第 2～5 節執行；只想用既有資料重畫圖，可直接看第 6 節。

## 2. 環境與安裝

以下指令在 Windows PowerShell 的專案根目錄執行。查看既有成果不用安裝套件；離線畫圖需要 Python，自己重測才需要 PostgreSQL 和 `.env`。

- Windows PowerShell 5.1／7、Git、Python **3.11 x64**。
- 本機 PostgreSQL **17**（原實驗為 17.12），服務已啟動。帳號要能建庫並讀取伺服器資訊，範例使用 `postgres`。
- 資料庫使用 **UTF8／libc locale**。目前 SF1 腳本以本機、未開啟 WAL archiving／replication slots 的測試環境為前提。
- 專案與 PostgreSQL 資料所在磁碟各預留 **20 GiB**；後續檢查會要求至少 **10 GiB**。首次安裝套件與 DuckDB TPC-H 擴充套件需要網路。

完整程式與正式成果都在 `week2-week3` 分支：

~~~powershell
$repoUrl = Read-Host '貼上本專案的 GitHub Clone URL'
git clone --branch week2-week3 $repoUrl Workload-Driven-Composite-Index-Advisor
if ($LASTEXITCODE -ne 0) { throw 'Clone 失敗，請停止' }
Set-Location .\Workload-Driven-Composite-Index-Advisor

$ErrorActionPreference = 'Stop'
py -3.11 -m venv .venv
if ($LASTEXITCODE -ne 0) { throw '建立 Python 環境失敗，請停止' }

# 後續指令都用這個函式呼叫專案的 Python
function Invoke-Python {
    & .\.venv\Scripts\python.exe -B @args
    if ($LASTEXITCODE -ne 0) { throw "Python 執行失敗（$LASTEXITCODE）" }
}

Invoke-Python -m pip install -r dataset/requirements.txt
Invoke-Python -m pip install -r analysis/requirements-3c.txt
~~~

要連線資料庫時，再從範本建立 `.env`：

~~~powershell
if (Test-Path .env) { throw '.env 已存在，可沿用或先檢查設定' }
Copy-Item .env.example .env
notepad .env
~~~

填入自己的連線設定並儲存；準備流程維持 `PGDATABASE=advisor_smoke`：

~~~dotenv
PGHOST=localhost
PGPORT=5432
PGUSER=postgres
PGDATABASE=advisor_smoke
PGPASSWORD=你的本機密碼
~~~

程式優先使用既有的 `PG*` 環境變數，其次才是 `.env`。SF1 與四策略實驗使用 `advisor_benchmark`；Advisor 和獨立 Runner 可用 `--dsn` 指定資料庫。

每次重測用一個新目錄存結果，後續指令沿用 `$experimentRoot`：

~~~powershell
$experimentRoot = Join-Path 'benchmark/results' ('reproduce-' + [guid]::NewGuid().ToString('N').Substring(0, 12))
New-Item -ItemType Directory -Path $experimentRoot | Out-Null
Write-Host "本次輸出：$experimentRoot"
~~~

`.env`、`.venv/`、`dataset/data/` 和新的實驗輸出由 Git 忽略；已完成的四輪成果則隨專案提供。

## 3. 資料準備

### 3.1 先準備 SF0.01

SF0.01 是目前腳本的測試前置，不是 Proposal 規定。SF1 建庫會參考 smoke 的 Schema 與內容快照，所以新環境先產生並載入這份小資料；已有正確的 smoke 與擴充套件快取時可沿用。

~~~powershell
Invoke-Python dataset/tpch.py generate --scale 0.01 --output dataset/data/sf0.01
Invoke-Python dataset/tpch.py create-db
Invoke-Python dataset/tpch.py load --source dataset/data/sf0.01
~~~

完成後應有 orders **15,000** 筆、lineitem **60,175** 筆，載入時也會 ANALYZE。每份資料只需載入一次，已有資料時不用再執行 `load`。

### 3.2 SF1 預檢與快照

~~~powershell
Invoke-Python -m dataset.prepare_sf1 --output "$experimentRoot/preflight.json"
Get-Content "$experimentRoot/preflight.json" -Raw -Encoding UTF8
~~~

預檢結果為 `ready_for_approval=true`、`blockers=[]` 時，就可以繼續。再用現有函式保存 smoke 內容快照，供匯入後比對：

~~~powershell
$snapshotCode = @'
import json
import sys
from pathlib import Path
from dotenv import load_dotenv
from dataset.prepare_sf1 import ROOT
from dataset.verify_sf1 import smoke_digest

load_dotenv(ROOT / '.env')
with (Path(sys.argv[1]) / 'smoke-before.json').open('x', encoding='utf-8') as stream:
    json.dump({'tables': smoke_digest()}, stream, indent=2)
'@
Invoke-Python -c $snapshotCode $experimentRoot
~~~

### 3.3 建立 SF1 並驗收

接下來產生 SF1、建立獨立的 `advisor_benchmark`，再匯入兩張表並 ANALYZE。腳本會自己產生 `dataset/data/sf1`，前面不用另外生成。

~~~powershell
Invoke-Python -m dataset.prepare_sf1 --execute --confirm-database advisor_benchmark --output "$experimentRoot/load.json"
Invoke-Python -m dataset.verify_sf1 --load-report "$experimentRoot/load.json" --start-state "$experimentRoot/preflight.json" --smoke-before "$experimentRoot/smoke-before.json" --output "$experimentRoot/acceptance.json"
~~~

驗收結果應為 `passed=true`：orders **1,500,000** 筆、lineitem **6,001,215** 筆，Schema、完整性、統計與空間檢查通過，且 smoke 保持不變。

腳本不會覆蓋既有的 SF1 目錄或目標資料庫。若因空間或驗證問題中斷，先檢查輸出與留下的資料，再決定後續操作，避免直接刪庫重試。已有成功的 SF1 與驗收檔時，可以直接沿用。

## 4. 執行 Advisor

~~~powershell
Invoke-Python -m advisor --workload workload/benchmark20.sql --dsn 'dbname=advisor_benchmark' --budget-mb 100 --output "$experimentRoot/advisor-100mib.json"
~~~

這裡的預算單位是 **MiB**，也可改成 500 或 1024。輸出 JSON 包含推薦、估算大小與 `warnings`；Advisor 只列出建議 DDL，不會直接建立索引。換預算時也一起換輸出檔名，避免覆蓋前次推薦。

也可以先用獨立的唯讀 Runner 測量三條 smoke SQL：

~~~powershell
Invoke-Python -m benchmark --workload workload/smoke.sql --dsn 'dbname=advisor_smoke' --warmup 1 --repeats 3 --output "$experimentRoot/smoke.json"
~~~

## 5. 執行 Benchmark

Week 3 分成三個步驟，依 **3A → 3B → 3C** 執行：

- **3A：資料集準備與驗收**，也就是第 3 節的 SF1 建立與完整性檢查。
- **3B：索引預算規劃**，估算索引容量，產生三種預算的配置。
- **3C：正式效能實驗**，比較四種策略，完成測量與第 6 節的分析產圖。

如果資料、Schema、Workload 與 Advisor 設定沒有改變，可沿用有效的 3A／3B 結果，將下方路徑改成自己的驗收與規劃檔。每次重測再產生新的 plan，存到新目錄；專案附帶的 plan 是原實驗紀錄。

### 5.1 模擬、產生 plan、dry-run

這幾個命令只讀取資料庫統計。已有有效的 3B 規劃檔時，略過第一個 Python 命令即可。

~~~powershell
$acceptancePath = Join-Path $experimentRoot 'acceptance.json' # 沿用 3A 時改為既有驗收檔
$budgetPath = Join-Path $experimentRoot 'budgets.json'       # 沿用 3B 時改為既有規劃檔

# 已有有效的 3B 規劃檔時，略過這一行
Invoke-Python -m analysis.sf1_budget --acceptance $acceptancePath --output $budgetPath
Invoke-Python -m strategy_benchmark plan --source-3b $budgetPath --acceptance $acceptancePath --output-dir "$experimentRoot/review" --rounds 4 --warmup 2 --repeats 5 --seed 20261120 --statement-timeout-ms 120000

$planPath = Join-Path $experimentRoot 'review/plan.json'
$runDir = Join-Path $experimentRoot 'run'
Invoke-Python -m strategy_benchmark dry-run --plan $planPath --output "$experimentRoot/dry-run.json"

Get-Content "$experimentRoot/dry-run.json" -Raw -Encoding UTF8
Get-Content "$experimentRoot/review/planned-ddl.sql" -Encoding UTF8
$planDocument = Get-Content $planPath -Raw -Encoding UTF8 | ConvertFrom-Json
$approvedHash = [string]$planDocument.plan_sha256
Write-Host "資料庫：$($planDocument.database.database)；單元：$($planDocument.schedule.Count)"
Write-Host "Plan SHA-256：$approvedHash"
Write-Host "Run 目錄：$runDir"
~~~

dry-run 應顯示 `dry_run_ok`，目標為 `advisor_benchmark`，共 **4 策略 × 3 預算 × 4 輪＝48 組**。可從 DDL 預覽查看索引配置；確認後用 `plan_sha256` 核准執行，這個值與 `Get-FileHash plan.json` 的檔案雜湊不同。

每組執行完整二十條 SQL，各暖機 **2 次、測量 5 次**；預算為 **100／500／1024 MiB**。同預算的四策略使用相同查詢順序與預熱方式，不清 OS cache。實際索引大小用 `pg_relation_size` 計算；超預算時會回滾整組配置並記錄，不自行裁切或補選索引。

### 5.2 正式執行

**這一步會在 `advisor_benchmark` 建立並清理實驗索引。** 建議在沒有其他查詢執行時測量，期間維持資料與設定不變。索引由控制器管理，DDL 預覽不用另外手動執行。

~~~powershell
Invoke-Python -u -m strategy_benchmark run --plan $planPath --run-dir $runDir --approve-plan-sha256 $approvedHash
~~~

想在同一個視窗看進度，可在命令末尾加 `--live-progress`，顯示目前輪次、策略、預算與完成組數。預設關閉；非互動終端或顯示出錯時會改用逐行文字，不影響實驗執行。

執行完成後，正常結果的 `summary.json` 會是 `complete`，共 **1,920 次暖機、4,800 次測量**。若是 `complete_with_infeasible_configurations`，表示部分配置超預算，沒有對應的效能數據。

每次實驗保留整個 `run/`，裡面有計畫、SQL、journal、摘要與原始測量。不同批次或測量設定的結果分開分析。

### 5.3 進度與中斷復原（需要時）

也可以在另一個 PowerShell 的專案根目錄查看已完成組數：

~~~powershell
$runDir = Read-Host '貼上本次 Run 目錄'
.\.venv\Scripts\python.exe -B -m analysis.strategy_progress --run-dir $runDir
~~~

要中斷時，按 **Ctrl+C 一次**，等程式清理並退出後，再於原終端機查看復原預覽。進度用上方工具查看即可，避免執行中開啟 `journal.json` 造成 Windows 檔案鎖。

~~~powershell
Invoke-Python -m strategy_benchmark recover --run-dir $runDir
~~~

若預覽仍列出本次實驗留下的索引，先備份 journal，再執行清理：

~~~powershell
$recoveryPlan = Get-Content "$runDir/plan.json" -Raw -Encoding UTF8 | ConvertFrom-Json
Copy-Item "$runDir/journal.json" (Join-Path $runDir ('journal.before-recovery.' + [guid]::NewGuid().ToString('N') + '.json'))
Invoke-Python -m strategy_benchmark recover --run-dir $runDir --execute --approve-run-id $recoveryPlan.run_id
~~~

復原只處理本次實驗有記錄的索引。若身份或 ownership 檢查失敗，先保留原檔檢查原因。復原不會接續測量，之後重跑仍使用新 plan 與新目錄。

## 6. 分析與產圖

既有圖表和 CSV 都在第 1 節的分析目錄，可以直接開啟。

如果想用既有數據重畫圖，裝好第 2 節的 Python 環境與兩份 requirements 後執行下列命令即可，不需要 PostgreSQL 或 `.env`。結果會存到新目錄：

~~~powershell
$referenceRoot = 'benchmark/results/3c-four-rounds-2beee5cb9384'
$referenceOutput = Join-Path 'benchmark/results' ('reference-analysis-' + [guid]::NewGuid().ToString('N').Substring(0,12))
.\.venv\Scripts\python.exe -B -m analysis.strategy_results --run-dir "$referenceRoot/run" --output-dir $referenceOutput
~~~

分析自己剛完成的實驗，則在原終端機執行：

~~~powershell
Invoke-Python -m analysis.strategy_results --run-dir "$experimentRoot/run" --output-dir "$experimentRoot/analysis"
~~~

分析程式不連線資料庫，輸出目錄使用新名稱。`analysis.json` 記錄資料完整性，正常時 `artifact_issues` 為空；其餘輸出如下：

| 輸出 | 內容 |
| --- | --- |
| `cells.csv`、`queries.csv`、`attempts.csv` | 單元、正式 Q 編號、每次時間／Buffers／使用索引與原始 JSON 檔名 |
| `index_capacities.csv`、`aggregates.csv` | 估算／實測容量與配對彙總；有超預算時另輸出 `infeasible.csv` |
| `exp1_performance`、`exp1_per_query` | 整體效能與逐查詢熱圖 |
| `exp2_buffers`、`exp3_storage_tradeoff` | Buffers 與儲存／效能取捨 |

圖表有 PNG、SVG、PDF 三種格式，分別整理完整二十條（full20）與 Advisor 支援的十六條（advisor16）；熱圖列出全部查詢。完整 Query Plan 留在 `run/` JSON，缺測或超預算也會保留在結果中。

## 7. 測試與限制

一般開發可先跑離線測試，PostgreSQL 測試預設略過：

~~~powershell
Invoke-Python -m unittest discover -s tests -v
~~~

需要測試真實 Runner 時，再將 `.env` 指向已載入 SF0.01 的 smoke 環境，啟用 PostgreSQL 測試。這類測試與正式實驗分開執行：

~~~powershell
$env:BENCHMARK_TEST_POSTGRES = '1'
try {
    Invoke-Python -m unittest discover -s tests -p test_benchmark_postgres.py -v
}
finally {
    Remove-Item Env:BENCHMARK_TEST_POSTGRES -ErrorAction SilentlyContinue
}
~~~

這份實驗有幾個解讀上的限制：

- Advisor 可解析 Q01～Q16，Q08／Q13 沒有複合候選；Q17～Q20 仍由 PostgreSQL 測量，但不參與推薦。容量與效益分數是估算，exact／greedy 的選擇結果不保證實測一定較快。
- 比較的是整體索引配置策略。Single／Suboptimal 使用 manifest 的欄位資訊，Suboptimal 採原始欄位順序，不保證較慢；這不是只改欄位順序的消融實驗。
- Workload 時間是各 SQL 平均 Execution Time 的加總，不含 Planning、建索引與預熱。Shared Read 可能由 OS cache 滿足，不等於實體磁碟讀取；根 Plan 計數也不用再加上子節點。
- 跨輪統計以輪為單位，與同輪、同預算的 Baseline 配對。四輪平衡執行順序，但仍可能有時間漂移，因此儲存取捨圖不能視為全域 Pareto 最佳。

研究目標見 [Proposal](report/Group9.pdf)。這裡使用 TPC-H 衍生資料與自訂 SQL，並非完整合規的 TPC-H Benchmark。
