# 3C 實測結果分析

這些腳本沿用已核准的控制器；不變更 Advisor、Runner、SQL 或 plan。

`run_3c_integration.py` 是本次授權的一次性真實整合測試：使用原 plan 中一個
`orders(o_orderdate)` 索引，讀取實際容量，經日誌 recovery 預覽及執行清理。
輸出目錄必須不存在，避免重寫既有證據。只有這個腳本會建立／刪除索引。

`strategy_results.py` 完全離線讀取正式結果。範例：

```powershell
.\.venv\Scripts\python.exe -B -m analysis.strategy_results --run-dir benchmark/results/strategy-run-e4b8de6111b3 --output-dir benchmark/results/3c-analysis-e4b8de6111b3
```

報表目錄同樣必須是新目錄。產出：

- `analysis.json`：輸入雜湊、完整度、各策略／預算彙總與分析定義。
- `cells.csv`：48 個排程單元，包含缺測或超預算狀態。
- `queries.csv`：每個單元的 20 條 SQL 平均數、支援標記及索引使用情況。
- `attempts.csv`：每一次暖機／正式測量、Execution/Planning Time、Shared/Temp
  Buffers、使用索引，以及完整原始 JSON 所在檔名。
- `index_capacities.csv`：索引名稱、定義、估算 bytes、`pg_relation_size` bytes、
  `pg_total_relation_size` bytes。回滾配置若有容量紀錄，明確標記不是完整配置。
- `aggregates.csv`：以 round 為重複單位的彙總。配對加速比為同 round／budget
  的 Baseline ÷ strategy，再取幾何平均；不是「平均 Baseline ÷ 平均 strategy」。
- `infeasible.csv`：若有不可行配置才產出；不填造效能數字。
- Exp 1、Exp 2、Exp 3 與逐查詢明細圖，均保存 PNG、SVG、PDF。

Workload 時間為每條查詢 5 次 Execution Time 平均值的加總；不含 Planning
Time、建索引或預熱成本。每輪有 20 個查詢平均值；四輪才是四個重複樣本。
完整 Query Plan 保留在正式目錄各 cell 的 `.json` 與未加註的 `.runner.json`。

Exp 1 圖的 whisker 為四輪配對加速比最小值／最大值，並非信賴區間。
Exp 2 使用 Plan 根節點計數，避免重複加總已包含的子節點；shared read 可能由
OS cache 供應，不能當作實體磁碟讀取次數；shared hit 也不是越多一定越好。
Temp Read/Written Blocks 另存 CSV。Exp 3 以實測容量及配對 Baseline 的 Workload
時間節省繪製，只表示已抽樣配置的非支配包絡，沒有全域最優保證。

`final_3c_safety.py` 僅在正式控制器結束後執行唯讀關閉檢查：

```powershell
.\.venv\Scripts\python.exe -B -m analysis.final_3c_safety --run-dir benchmark/results/strategy-run-e4b8de6111b3 --output benchmark/results/3c-analysis-e4b8de6111b3/final-safety.json
```

確認目標身份、無殘留索引、日誌完成、原檔雜湊及 `advisor_smoke` 內容未變。
控制器本身在最終清理後已核對 SF1 兩表完整內容 signature，不重複全表掃描。

繪圖依賴版本記於 `requirements-3c.txt`；PDF 套件只用來核對原 Proposal。
