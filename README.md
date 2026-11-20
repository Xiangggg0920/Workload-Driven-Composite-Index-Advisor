# Workload-Driven Composite Index Advisor

## 1. 專案介紹

Group 9 專題：利用 SQL 與 PostgreSQL 統計資料推薦複合 B-tree 索引，比較效能、Buffers 與儲存成本。

流程：SQL → `advisor/` 推薦 → `strategy_benchmark/` 配置與索引管理 → `benchmark/` 真實測量 → `analysis/` 彙整及 Exp 1／2／3 圖表。`dataset/` 負責資料準備，`tests/` 提供測試。

正式實驗採 TPC-H SF1 的 orders／lineitem、[二十條 SQL](workload/benchmark20.sql)，比較 Baseline、Single-column、Suboptimal、Advisor；這是 TPC-H 衍生實驗，不是完整合規的 TPC-H 測試。

**組員可先看既有成果，不必先重跑原環境約 2.5 小時的實驗。** Clone 後即可用瀏覽器、VS Code 或試算表開啟下列檔案，開始分析與撰寫報告，無需先安裝 PostgreSQL 或準備資料：

- [正式四輪成果](benchmark/results/3c-four-rounds-2beee5cb9384/)：4 策略 × 3 預算 × 4 輪，48/48 組成功；2 次暖機、5 次測量，共 1,920／4,800 次成功記錄。
- [分析與圖表](benchmark/results/3c-four-rounds-2beee5cb9384/analysis/)：先看 `analysis.json`、`aggregates.csv` 與四組 PNG／PDF；逐查詢與逐次數據見 `queries.csv`、`attempts.csv`，容量見 `index_capacities.csv`。
- [測量與計畫](benchmark/results/3c-four-rounds-2beee5cb9384/run/)：各單元 JSON 保留完整 Query Plan、時間、Buffers 及索引配置，另有 plan／journal／summary／SQL。發布版省略重複 `.runner.json` 與 `review/plan.json`，不影響離線分析；本機原始檔仍保留。

**只有要自行重現或重新測量，才依第 2～5 節準備環境並執行 3A → 3B → 3C。** 離線重產參考圖表見第 6 節；不要把參考結果與新測量混成同一組。

## 2. 環境與安裝

以下為自行重測的必要條件；只查看既有成果可跳過本節。離線重產圖表只需 Python 與兩份 requirements，不需要 PostgreSQL 服務或 `.env`。

- Windows PowerShell 5.1／7、Git、Python **3.11 x64**。
- 已啟動的本機 PostgreSQL **17**（原實驗為 17.12）。以下使用 `postgres` 帳號；檢查需讀取 `data_directory`、`pg_control_system()`，僅 CREATEDB 權限可能不足。
- smoke 資料庫須為 **UTF8／libc locale**；預檢不接受 ICU、遠端主機、WAL archiving 或 replication slots。
- 專案與 PostgreSQL 資料所在磁碟各至少 **20 GiB** 可用；後續階段要求至少 **10 GiB**。套件與 DuckDB TPC-H 擴充套件首次安裝需要網路。

Clone 包含 Week 3 的版本；本例為 `week2-advisor` 分支，若已合併則改用對應分支。

~~~powershell
$repoUrl = Read-Host '貼上本專案的 GitHub Clone URL'
git clone --branch week2-advisor $repoUrl Workload-Driven-Composite-Index-Advisor
if ($LASTEXITCODE -ne 0) { throw 'Clone 失敗，請停止' }
Set-Location .\Workload-Driven-Composite-Index-Advisor

$ErrorActionPreference = 'Stop'
py -3.11 -m venv .venv
if ($LASTEXITCODE -ne 0) { throw '建立 Python 環境失敗，請停止' }

# 後續 Python 命令失敗時停止，不繼續下一階段
function Invoke-Python {
    & .\.venv\Scripts\python.exe -B @args
    if ($LASTEXITCODE -ne 0) { throw "Python 執行失敗（$LASTEXITCODE），請檢查錯誤" }
}

Invoke-Python -m pip install -r dataset/requirements.txt
Invoke-Python -m pip install -r analysis/requirements-3c.txt
~~~

自行重測者再建立連線設定：

~~~powershell
if (Test-Path .env) { throw '.env 已存在，請檢查，不要覆蓋' }
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

既有 `PG*` 環境變數優先於 `.env`，請排除衝突。SF1 與四策略控制器固定連到 `advisor_benchmark`；Advisor／獨立 Runner 則以下方 `--dsn` 指定。

建立新的實驗輸出目錄，後續沿用 `$experimentRoot`：

~~~powershell
$experimentRoot = Join-Path 'benchmark/results' ('reproduce-' + [guid]::NewGuid().ToString('N').Substring(0, 12))
New-Item -ItemType Directory -Path $experimentRoot | Out-Null
Write-Host "本次輸出：$experimentRoot"
~~~

`.env`、`.venv/`、`dataset/data/` 及新產生的實驗輸出由 Git 忽略。只有核准的上述四輪參考成果已精確納入 Git；不要整批提交其他結果。

## 3. 資料準備

### 3.1 SF0.01：現行程式必要前置

SF0.01 是目前程式的前置測試要求，**並非 Proposal 規定**。SF1 腳本依賴 smoke schema、快照與已快取的 TPC-H 擴充套件，因此先完成：

~~~powershell
Invoke-Python dataset/tpch.py generate --scale 0.01 --output dataset/data/sf0.01
Invoke-Python dataset/tpch.py create-db
Invoke-Python dataset/tpch.py load --source dataset/data/sf0.01
~~~

預期 orders **15,000**、lineitem **60,175** 筆。載入包含 ANALYZE，不建立索引；**已有資料不可再次 load**。若 smoke locale 不符，停止並檢查建庫設定。

### 3.2 SF1 預檢與快照

~~~powershell
Invoke-Python -m dataset.prepare_sf1 --output "$experimentRoot/preflight.json"
Get-Content "$experimentRoot/preflight.json" -Raw -Encoding UTF8
~~~

確認 `ready_for_approval=true`、`blockers=[]`。驗收另需 smoke 內容快照；目前沒有獨立 CLI，以下直接使用既有函式：

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

**預檢通過後才執行。** 第一條命令生成 SF1、建立獨立 `advisor_benchmark`、COPY 並 ANALYZE；不要事先生成 `dataset/data/sf1`。

~~~powershell
Invoke-Python -m dataset.prepare_sf1 --execute --confirm-database advisor_benchmark --output "$experimentRoot/load.json"
Invoke-Python -m dataset.verify_sf1 --load-report "$experimentRoot/load.json" --start-state "$experimentRoot/preflight.json" --smoke-before "$experimentRoot/smoke-before.json" --output "$experimentRoot/acceptance.json"
~~~

只有 `passed=true` 才能繼續：應為 orders **1,500,000**、lineitem **6,001,215** 筆、無索引，Schema／完整性／統計／空間通過且 smoke 不變。

**目標資料庫或 SF1 目錄已存在、空間不足、驗證失敗時停止，不覆蓋、刪庫或自行重試。** 匯入失敗可能留下空資料庫。已有成功 SF1 時保留自己的驗收證據，不重跑匯入；新實驗另建輸出目錄並將後續輸入路徑指向該證據。

## 4. 執行 Advisor

~~~powershell
Invoke-Python -m advisor --workload workload/benchmark20.sql --dsn 'dbname=advisor_benchmark' --budget-mb 100 --output "$experimentRoot/advisor-100mib.json"
~~~

預算單位為 **MiB**，可改為 500／1024。檢查解析／跳過數、warnings、推薦與 `estimated_selected_bytes <= budget_bytes`。Advisor 只輸出建議 DDL，不建立索引。

**選用：** 先用獨立唯讀 Runner 檢查三條 smoke SQL：

~~~powershell
Invoke-Python -m benchmark --workload workload/smoke.sql --dsn 'dbname=advisor_smoke' --warmup 1 --repeats 3 --output "$experimentRoot/smoke.json"
~~~

## 5. 執行 Benchmark

Week 3 依 **3A → 3B → 3C** 執行：

- **3A：資料集準備與驗收**——第 3 節的 SF1 建立、完整性檢查與驗收。
- **3B：索引預算規劃**——容量估算與 100／500／1024 MiB 預算配置。
- **3C：正式效能實驗**——四策略比較、測量與第 6 節的分析產圖。

有效的 3A／3B 結果可沿用，前提是資料、Schema、Workload 與 Advisor 規劃條件相容，且通過 plan／dry-run 檢查。將下方輸入路徑指向自己的有效檔案；沿用 3B 時略過容量模擬命令。每次 3C 仍須使用新 plan、SHA 與輸出目錄，不覆蓋或混合既有結果。

### 5.1 模擬、產生 plan、dry-run

以下對資料庫只讀；新環境先完成 3B，已有有效 3B 則直接產生新 plan。

~~~powershell
$acceptancePath = Join-Path $experimentRoot 'acceptance.json' # 沿用 3A 時改為既有驗收檔
$budgetPath = Join-Path $experimentRoot 'budgets.json'       # 沿用 3B 時改為既有規劃檔

# 沿用有效 3B 時略過此行，不覆寫規劃檔
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

確認 `dry_run_ok`、目標 `advisor_benchmark`、**4 策略 × 3 預算 × 4 輪＝48 組實驗**，並審閱 DDL。核准值取 `plan_sha256`，不是 `Get-FileHash plan.json` 的整檔 SHA。

固定規則：每單元完整二十條 SQL、各暖機 **2 次／測量 5 次**；預算 **100／500／1024 MiB**。同預算四策略使用相同 SQL 順序與全表預熱，不清 OS cache。實測 `pg_relation_size` 超預算則整組回滾、不測效能、不裁切補選。

### 5.2 正式執行

**此步會在 `advisor_benchmark` 真實建立並清理本次索引。** 保留獨占實驗時段，維持資料、統計及設定不變；不要手動執行 `planned-ddl.sql` 或繞過身份／SHA 檢查。

~~~powershell
Invoke-Python -u -m strategy_benchmark run --plan $planPath --run-dir $runDir --approve-plan-sha256 $approvedHash
~~~

**同視窗進度 UI：** 在此命令末尾加 `--live-progress`，顯示輪次、策略、預算、已處理組數及狀態。省略旗標即關閉（預設）；非互動終端或 UI 出錯時退回逐行文字。進度輸出到 stderr，不增加 PostgreSQL 查詢，也不讀取執行中的 journal；每條 SQL 測量期間不更新畫面。

前景執行直到結束。全部可行且成功時，`summary.json` 為 `complete`，共 **1,920 次暖機／4,800 次測量**。`complete_with_infeasible_configurations` 代表有超預算單元，不能當作全部完成測量。

保留整個 `run/`：plan、SQL、journal、summary、各單元 JSON 與 `.runner.json`；不得混用不同批次或測量設定。

### 5.3 進度與中斷復原（需要時）

在另一個 PowerShell 切到專案根目錄，查一次進度：

~~~powershell
$runDir = Read-Host '貼上本次 Run 目錄'
.\.venv\Scripts\python.exe -B -m analysis.strategy_progress --run-dir $runDir
~~~

執行中不要反覆開啟 `journal.json`，以免 Windows 讀取鎖妨礙保存。停止時按 **Ctrl+C 一次**，等程序清理並退出後，才在原終端機預覽復原：

~~~powershell
Invoke-Python -m strategy_benchmark recover --run-dir $runDir
~~~

確認仍需清理且全屬本次索引，才備份 journal 並執行：

~~~powershell
$recoveryPlan = Get-Content "$runDir/plan.json" -Raw -Encoding UTF8 | ConvertFrom-Json
Copy-Item "$runDir/journal.json" (Join-Path $runDir ('journal.before-recovery.' + [guid]::NewGuid().ToString('N') + '.json'))
Invoke-Python -m strategy_benchmark recover --run-dir $runDir --execute --approve-run-id $recoveryPlan.run_id
~~~

清理核對 ownership tag、owner、定義及 OID，不刪其他索引；若檢查失敗立即停止，保留證據。**復原只清理，不支援斷點續跑**；重跑須使用新 plan／run 目錄。

## 6. 分析與產圖

**直接查看參考成果：** 開啟第 1 節的分析目錄即可，不需要執行命令。

**選用：離線重產參考圖表。** 安裝第 2 節的 Python 環境與兩份 requirements 後執行；不需要 PostgreSQL／`.env`，也不修改參考成果：

~~~powershell
$referenceRoot = 'benchmark/results/3c-four-rounds-2beee5cb9384'
$referenceOutput = Join-Path 'benchmark/results' ('reference-analysis-' + [guid]::NewGuid().ToString('N').Substring(0,12))
.\.venv\Scripts\python.exe -B -m analysis.strategy_results --run-dir "$referenceRoot/run" --output-dir $referenceOutput
~~~

**分析自己的新實驗：** 回到原終端機執行。所有分析只讀取結果、不連線 PostgreSQL，輸出目錄須尚不存在：

~~~powershell
Invoke-Python -m analysis.strategy_results --run-dir "$experimentRoot/run" --output-dir "$experimentRoot/analysis"
~~~

先確認 `analysis.json` 的 `artifact_issues` 為空。輸出包括：

| 輸出 | 內容 |
| --- | --- |
| `cells.csv`、`queries.csv`、`attempts.csv` | 單元、正式 Q 編號、每次時間／Buffers／使用索引與原始 JSON 檔名 |
| `index_capacities.csv`、`aggregates.csv` | 估算／實測容量與配對彙總；有超預算時另輸出 `infeasible.csv` |
| `exp1_performance`、`exp1_per_query` | 整體效能與逐查詢熱圖 |
| `exp2_buffers`、`exp3_storage_tradeoff` | Buffers 與儲存／效能取捨 |

圖表提供 PNG／SVG／PDF；整體比較同時呈現 full20／advisor16，熱圖列全部二十條。完整 Query Plan 留在 `run/` JSON。失敗、缺測及超預算須如實記錄。

## 7. 測試與限制

**選用：** 自動化測試，真實 PostgreSQL 測試預設跳過：

~~~powershell
Invoke-Python -m unittest discover -s tests -v
~~~

需測試真實 Runner 時，確認 `.env` 指向自己的 SF0.01 smoke，且不與正式實驗同時執行：

~~~powershell
$env:BENCHMARK_TEST_POSTGRES = '1'
try {
    Invoke-Python -m unittest discover -s tests -p test_benchmark_postgres.py -v
}
finally {
    Remove-Item Env:BENCHMARK_TEST_POSTGRES -ErrorAction SilentlyContinue
}
~~~

- **推薦限制：** Q01～Q16 可解析，Q08／Q13 無複合候選；Q17～Q20 未支援但仍實際測量。大小／分數是啟發式估計，Optimizer 保留 exact／greedy，非實測效益保證。
- **比較範圍：** Single／Suboptimal 使用 manifest 的 predicate 資訊；Suboptimal 採原始欄位順序，不保證較慢。整體配置比較不能直接證明欄位順序的因果效益。
- **結果解讀：** Workload 時間為各 SQL 平均 Execution Time 加總，不含 Planning／建索引／預熱。Shared Read 不等於實體磁碟讀取；根 Plan 計數不可再加總子節點。
- **輪數與漂移：** 正式採四輪 Williams 順序平衡，跨輪統計以輪為單位，五次查詢測量不等於五輪。各預算只與同輪、同預算的 Baseline 配對；四輪仍不能消除漂移，跨預算及 Pareto 解讀須保留限制。
- **環境與保存：** PostgreSQL 安裝、權限與 locale 需自行準備，不相容時腳本停止。大部分輸出拒絕覆蓋，但 Advisor 會覆蓋同名輸出；請使用新目錄並備份原始結果。
- **歷史 plan：** 參考成果綁定當時程式的 SHA-256；新增進度 UI 後，舊 plan 不適用新版控制器執行。離線分析不受影響，自行重測須建立並核准新 plan。
- **歷史工具：** `benchmark/run_single_round.ps1`、`analysis/run_3c_integration.py`、`analysis/final_3c_safety.py` 綁定舊批次，不用於本指南。研究依據見 [Proposal](report/Group9.pdf)；其他歷史文件不作為目前操作指令。
