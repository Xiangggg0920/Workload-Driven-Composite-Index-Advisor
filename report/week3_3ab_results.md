# Week 3：3A＋3B SF1 執行與預算評估結果

完成範圍僅 3A、3B；**3C 尚未開始，沒有建立／刪除使用者索引**。
3A 依已批准的 [既定計畫](../dataset/sf1_3a_plan.md) 與原 prepare_sf1.py 執行，
3A 全部驗收成功後才開始 3B。原計畫文件保留批准前的歷史狀態，沒有覆蓋它。

## 3A 實際結果

| 項目 | 實測結果 |
| --- | ---: |
| 資料庫 | advisor_benchmark，PostgreSQL 17.12，本機同一 instance |
| orders | 1,500,000 列、9 欄 |
| lineitem | 6,001,215 列、16 欄 |
| orders heap | 226,689,024 bytes |
| lineitem heap | 995,819,520 bytes |
| 最後讀取的完整資料庫大小 | 1,231,050,419 bytes，約 1.147 GiB，包含系統 catalog 等 |
| orders.csv | 173,949,913 bytes |
| lineitem.csv | 772,996,521 bytes |
| 兩個 CSV 合計 | 946,946,434 bytes，約 0.882 GiB |
| 最終 C 槽可用 | 52,418,048,000 bytes，約 48.819 GiB |
| 最終 cluster WAL 目錄 | 1,056,964,608 bytes；這是整個 instance 的 WAL，不是 SF1 table/index 大小 |
| 使用者索引 | 空清單 |

使用 template0 建新庫，UTF8／原 libc locale；只建立現有 tpch.orders、tpch.lineitem，
COPY FROM STDIN 與 ANALYZE。沒有改 .env、角色、服務設定、tablespace 或 WAL 政策。
沒有 DROP／TRUNCATE／破壞性重試。生成與載入各執行一次。

額外的唯讀驗收共 16 項全部通過：

- Schema 欄位、順序、型別、長度／precision／scale、NOT NULL 與 smoke 相同，僅兩表。
- orders.o_orderkey 全部唯一；lineitem 的 (l_orderkey,l_linenumber) 沒有重複。
- 無 lineitem 找不到對應 orders 的孤兒列；數值與旗標範圍檢查無違反。
- 兩表筆數符合 SF1，25 個欄位均有 ANALYZE 統計；沒有使用者索引。
- advisor_smoke 的筆數／Schema／索引與開工前一致；另保存整表依 key 排序後的
  JSON row SHA-256，驗收後及 3B 結束後均一致。該內容指紋首次擷取於本次載入流程中，
  不是過去歷史版本的備份；本次程式寫入連線全都明確指定新庫。
- .env、正式 20 條 SQL、Advisor、Runner、既有 dataset 工具及計畫的內容 hash 不變。

來源：
[生成／載入報告](../benchmark/results/sf1-3a-load.json)、
[完整性驗收](../benchmark/results/sf1-3a-integrity.json)、
[開始狀態](../benchmark/results/sf1-3ab-start-state.json)、
[最終狀態](../benchmark/results/sf1-3ab-final-state.json)。

## 3B 方法與可重現性

以 READ ONLY 交易讀取 SF1 的 pg_class／pg_stats，保存全部 TableStats，之後三個
預算共用**同一份記憶體中的 catalog 快照**。使用原 Advisor 的 candidate generator、
score_candidates、_budget_shortlist、select_indexes；沒有重寫 Parser 或改變推薦邏輯。
每條查詢權重 1、max_columns=3、max_candidates=40、exact_limit=16。

正式 SQL SHA-256：a636adf71a656949cc13ce24c5ef3467778fe6240e47fd4e743c0bb3a8017ba2。
16 條可解析；Q17～Q20 仍整條跳過並警告。Q08／Q13 可解析，但現行 generator
沒有產生純 range 複合候選。預算分數不包含被跳過的 4 條，不能稱為全部 20 條的
實測效能。本輪也沒有在 SF1 執行 EXPLAIN ANALYZE benchmark。

初次分析與原 CLI 核對期間，PostgreSQL 的 autoanalyze 刷新了統計。例如 lineitem
reltuples 由 6,000,886 變成 6,001,105；這兩者都是抽樣估計，**實際 count(*) 仍為
6,001,215**。大小與分數微幅變化，三組所選索引沒有改變。
保留初版與診斷報告，未覆蓋。以下以自動維護後的
[sf1-3b-budgets-final.json](../benchmark/results/sf1-3b-budgets-final.json) 為準；
該檔保存 catalog_sha256、完整統計、維護時間、19 個候選與 score vectors。
三種預算也已和當時的原始 Advisor CLI 逐一核對相同 bytes／分數／欄序。
沒有為穩定結果而關閉 autovacuum 或再次 ANALYZE。

## 完整候選索引清單

全部 19 個候選的**預估**大小共 2,418,221,056 bytes＝2,306.1953125 MiB。
下表均非 pg_relation_size(index) 實測。所有 actual_index_bytes 皆為 null。

| ID | 表與欄位順序 | 預估 MiB |
| --- | --- | ---: |
| C01 | lineitem(l_orderkey, l_returnflag) | 200.8828125 |
| C02 | lineitem(l_orderkey, l_shipdate) | 216.3359375 |
| C03 | lineitem(l_orderkey, l_shipmode) | 270.421875 |
| C04 | lineitem(l_returnflag, l_linestatus) | 154.53125 |
| C05 | lineitem(l_shipmode, l_shipdate) | 239.515625 |
| C06 | lineitem(l_suppkey, l_quantity) | 224.0625 |
| C07 | lineitem(l_suppkey, l_shipdate) | 216.3359375 |
| C08 | orders(o_clerk, o_totalprice) | 77.25 |
| C09 | orders(o_custkey, o_orderdate) | 54.078125 |
| C10 | orders(o_orderkey, o_custkey) | 61.8046875 |
| C11 | orders(o_orderkey, o_custkey, o_orderdate) | 69.5234375 |
| C12 | orders(o_orderkey, o_orderpriority) | 77.25 |
| C13 | orders(o_orderkey, o_orderpriority, o_orderdate) | 84.9765625 |
| C14 | orders(o_orderkey, o_orderstatus) | 50.21875 |
| C15 | orders(o_orderkey, o_orderstatus, o_orderdate) | 57.9375 |
| C16 | orders(o_orderpriority, o_orderdate) | 69.5234375 |
| C17 | orders(o_orderpriority, o_orderstatus) | 65.6640625 |
| C18 | orders(o_orderpriority, o_orderstatus, o_orderdate) | 73.390625 |
| C19 | orders(o_orderstatus, o_orderdate) | 42.4921875 |

## 正式三種預算

1 MiB=1,048,576 bytes；1024 MiB=1 GiB。分數是加權 logical-work 啟發式代理值，
不是毫秒、buffer 讀取數或 speedup。

| 預算 MiB | 選中索引（依原演算法輸出順序） | 總預估 bytes | 預估 MiB | 剩餘 MiB | 評分 | 方法 |
| ---: | --- | ---: | ---: | ---: | ---: | --- |
| 100 | C14、C19 | 97,214,464 | 92.7109375 | 7.2890625 | 172,783.9167 | exact，12 個可行候選 |
| 500 | C19、C01、C14、C04 | 469,893,120 | 448.125 | 51.875 | 628,586.5100 | marginal-greedy，19 個可行候選 |
| 1024 | C19、C01、C14、C07、C04、C09、C05、C17 | 1,073,446,912 | 1023.71875 | 0.28125 | 1,045,597.9038 | marginal-greedy，19 個可行候選 |

沒有候選短名單截斷。100 MiB 下所有 lineitem 候選單獨都超預算，只能從 orders
候選中選；在 500／1024 MiB 下，所有 19 個候選都能單獨放入，但不能全部同時放入。

三組**在目前模型／演算法下均有實際約束力**：選擇集合及評分都不同；每組仍有正
邊際分數的未選候選，但沒有一個能放進剩餘空間。這不是對 greedy 全域最優的證明。
100 MiB 的 exact 與其他組的 greedy 也構成比較限制，不能把全部差異都歸因於預算。

診斷用、非正式第四組：把預算放寬至全部候選總大小後，同一 greedy 選出 17 個，
約 2,159.421875 MiB，達到模型的逐維最佳分數上界 1,085,954.7194。
100／500／1024 組分別約為此模型上界的 15.91%／57.88%／96.28%；這些百分比
**不是實測效能提升**。該參考組也不是達到上界的最小容量配置。

結論：SF1 已足以讓 100／500／1024 MiB 的**估計容量**形成不同壓力，建議保留
原正式預算，不需本階段更改標準或升到 SF10。這不表示 SF1 已足夠證明實體 I/O
改善：兩表約 1.14 GiB，可能仍放得進 OS cache，後續需明確快取政策。
若之後要額外觀測飽和區，可另提約 2,200～2,400 MiB 的診斷組；目前未將它列入
正式三組，也沒有為此建立索引或產生更大資料集。

## 測試、檔案與限制

新增：

- [dataset/verify_sf1.py](../dataset/verify_sf1.py)：唯讀的 3A 完整性驗收門檻。
- [analysis/sf1_budget.py](../analysis/sf1_budget.py)：3A 通過才准執行的 3B 模擬與證據輸出。
- [tests/test_verify_sf1.py](../tests/test_verify_sf1.py)、
  [tests/test_sf1_budget.py](../tests/test_sf1_budget.py)：共 7 項新測試。
- 本報告、ignored 的 SF1 CSV 及 benchmark/results/ 下的新 JSON 證據。

既有 prepare_sf1.py／計畫、Advisor、Parser、Runner、正式 SQL、.env 均未改。
沒有 commit／push／切換分支；既有未提交變更保留。

自動測試：共發現 112 項，**102 通過、10 項 opt-in PostgreSQL benchmark 測試略過**。
未為此階段重跑 SF0.01 或 SF1 benchmark。另有真正執行的 3A 16 項驗收、
3B 唯讀 SF1 分析及三次原 CLI 交叉核對，不能和 mock 測試混稱。

3B 可重新唯讀執行，輸出必須使用新檔名：

```powershell
.\.venv\Scripts\python.exe -B -m analysis.sf1_budget --acceptance benchmark/results/sf1-3a-integrity.json --output benchmark/results/sf1-3b-rerun.json
```

**不要重跑 prepare_sf1 --execute**：目標資料庫／CSV 已存在；它會拒絕重用，
不得刪除或清空以繞過。統計可能因自動維護或抽樣改變，重現應使用保存的 catalog
和設定，並確認目前資料庫仍符合驗收報告；既有 acceptance 檔不是永遠有效的保證。

容量模型未校準 PostgreSQL B-tree 實際布局、重複 key 壓縮等；估計可能高估或低估。
本輪 pg_relation_size 取得的是**表 heap** 大小，不是推薦索引大小。3C 才能在
另外授權後建立索引、讀取各 index 的 pg_relation_size，並計算估計誤差。
1024 組只留 294,912 bytes 餘額，不能假設實際建立後一定仍在預算內。

## 3C 開發前仍須確認的規則（尚未執行）

1. 固定四種情境：無索引、單欄基準、預先宣告的非最佳複合索引、Advisor；
   索引完整清單、名稱、欄序與允許建／移除的範圍應先批准，只作用於 benchmark 新庫。
2. 硬預算以新建 index 的 pg_relation_size 總和還是其他 fork／總大小為準；若估計
   組合實際超額，是判定不可行，還是按預先固定的順序刪減／重選。不得事後挑對
   Advisor 有利的規則，也不能默默把實際便宜的額外索引加進來。
3. 候選／統計／權重／搜尋法要凍結。是否保留原 exact≤16／greedy>16，或事先批准
   統一搜尋法的敏感性比較；Q17～Q20 仍列入全 20 條測量，但另列 16 條子集合。
4. SF1 的無索引 baseline、warmup／重複次數、順序交錯、快取政策、逾時／失敗
   計分、背景維護與效能分布報告方式。Shared Read 不直接當作物理磁碟讀取。
5. 每種情境結果完整性與查詢結果一致性、實際容量、Planner 採用／殘餘 Filter、
   索引清理及回復 baseline 的流程；一切需在 3C 授權後才執行。
