# Week 3A：獨立 SF1 環境操作計畫（等待使用者批准）

目前僅完成環境檢查、腳本及安全測試。**尚未產生 SF1、建立 advisor_benchmark、
匯入資料或執行 3B／3C。** Q17～Q20 保留未支援狀態。

## 已檢查的環境

2026-11-20 Asia/Taipei；原始唯讀預檢紀錄：
[sf1-3a-preflight-final.json](../benchmark/results/sf1-3a-preflight-final.json)。

| 項目 | 檢查結果 |
| --- | --- |
| PostgreSQL | 17.12、64-bit Windows，postgresql-x64-17 服務 Running |
| 連線 | 本機 ::1、port 5432；目前 .env／libpq 預設資料庫 advisor_smoke |
| 帳號 | postgres，superuser／CREATEDB；有建庫資格，不需新增角色 |
| 目標資料庫 | advisor_benchmark 尚不存在 |
| 原有 smoke | orders 15,000、lineitem 60,175；tpch 使用者索引為空 |
| 原有資料檔 | 僅 SF0.01；SF1 尚不存在 |
| Python／套件 | Python 3.11.5 x64；duckdb 1.4.3、psycopg 3.2.13、python-dotenv 1.2.1 |
| DuckDB TPC-H | 已快取且 LOAD 成功，dbgen 函式存在；檢查未執行 dbgen／INSTALL |
| 記憶體 | OS 回報 25,446,137,856 bytes，約 23.7 GiB |
| 主要磁碟 | 工作區、PostgreSQL data 與 pg_wal 均在 C；可用約 52.6 GiB |
| 備用磁碟 | E 可用約 1.25 TiB；本計畫不使用 E，不建 tablespace、不搬動資料目錄 |
| WAL | wal_level=replica、archive_mode=off、max_wal_size=1GB、無 replication slot |
| locale | UTF8／libc，Chinese (Traditional)_Taiwan.950；新庫明確沿用 |

初次在沙箱無法讀取資料目錄與 OS 記憶體資訊；經一次**唯讀環境檢查**的工具權限
批准後完成確認。該權限不代表已批准建庫／產生 SF1／匯入。本機資料夾不能直接
讀取不妨礙後續 COPY FROM STDIN：CSV 由 Python 讀取，透過連線送給 PostgreSQL。

獨立資料庫隔離 schema／資料，不是獨立 PostgreSQL instance；CPU、磁碟、WAL、
shared buffers 等仍與 smoke 共用。載入可能影響 smoke 的快取與暫時效能，
但不應修改其資料／schema／索引。

## 預估資料量與容量

只載入現有 schema 的 orders／lineitem，不載入其他六張 TPC-H 表：

| 項目 | 規劃估計 |
| --- | --- |
| orders | 1,500,000 列、9 欄 |
| lineitem | 6,001,215 列、16 欄；生成後必須實際核對 |
| 保留的 CSV | 約 0.9～1.1 GiB |
| PostgreSQL heap／表資料 | 約 1.2～2 GiB，依目前 SF0.01 外推，非實測 |
| DuckDB 資料庫／暫存／spill | 保留約 2～4 GiB 暫存餘裕；既有 dbgen 會先產生所有表，再只匯出兩表 |
| WAL／checkpoint 與其他餘裕 | 規劃約 2～6 GiB，不是硬上限 |
| 3A 峰值規劃 | 保守預留約 8～12 GiB；生成與 PostgreSQL 載入依序進行，實際峰值需監控 |

腳本開始時要求各涉及磁碟至少 20 GiB 可用；產生 CSV 後、建庫前再次要求至少
10 GiB 可用。目前 C 的可用容量符合。這是檢查門檻，不是保證磁碟永遠不會用完。
max_wal_size 是 checkpoint 的軟性目標，不能當成 WAL 使用量的硬上限。
本階段不修改 fsync、wal_level、synchronous_commit、server 設定或服務狀態。
生成／載入耗時尚未實測，不承諾固定分鐘數。

SF1 標準基數來源：[TPC-H 3.0.1 §4.2.5.2](https://www.tpc.org/tpc_documents_current_versions/pdf/tpc-h_v3.0.1.pdf)。
兩表資料與 schema 沿用本專題設定，仍不是完整、合規的 TPC-H 測試。

## 批准後才執行的流程

1. 重新執行唯讀預檢：確認同一本機 PostgreSQL、可建庫、目標不存在、SF1 目錄
   不存在、容量充足、無需另行審查的 WAL retention，保存 smoke 與保護檔案快照。
2. 重用現有 dataset/tpch.py 的 generate，scale=1，輸出至 dataset/data/sf1。
   不覆蓋任何既有目錄；DuckDB 臨時檔在 dataset/data 的暫存目錄，正常結束會清除。
3. 串流檢查兩份 CSV 的欄數、完整列數與 SHA-256。不是 SF1 或檔案損壞就停止，
   此時還沒有建立 PostgreSQL 資料庫。
4. 再確認 smoke 不變、磁碟空間足夠、advisor_benchmark 仍不存在，才從 postgres
   maintenance database 執行 CREATE DATABASE。使用 template0、UTF8、原有 libc
   locale，owner 為目前 postgres；不複製 advisor_smoke，不新增使用者索引。
5. 以明確 dbname=advisor_benchmark 重用現有 tpch.load：同一交易建立 tpch schema
   與兩表、COPY FROM STDIN、ANALYZE；沿用 schema.sql，不新增 PK／FK／索引。
   DSN 的 dbname 明確覆蓋 PGDATABASE，不修改 .env 或 process PGDATABASE。
6. 以唯讀查詢驗證目標名稱、兩表列數、25 個欄位統計、無 tpch 索引、實際表大小
   與訂單日期範圍；再次核對 smoke 的列數／schema／索引及保護檔案 hash。
7. 保存生成與匯入報告後停止。**不執行 20 條 benchmark、不推薦／建立索引，
   不自行開始 3B 或 3C。**

建庫使用 template0 可避免複製 template1 的本機自訂物件；COPY 與 ANALYZE
沿用 PostgreSQL 建議的載入方式。
[CREATE DATABASE](https://www.postgresql.org/docs/17/sql-createdatabase.html)、
[大量載入](https://www.postgresql.org/docs/17/populate.html)、
[WAL 設定](https://www.postgresql.org/docs/17/runtime-config-wal.html)。

## 已準備、尚未執行的腳本

[prepare_sf1.py](prepare_sf1.py) 預設只有檢查，沒有隱含的建庫／生成／載入：

```powershell
.\.venv\Scripts\python.exe -B -m dataset.prepare_sf1 --output benchmark/results/sf1-preflight-rerun.json
```

**以下必須在本次使用者明確確認後才執行，現在未執行：**

```powershell
.\.venv\Scripts\python.exe -B -m dataset.prepare_sf1 --execute --confirm-database advisor_benchmark --output benchmark/results/sf1-3a-load.json
```

兩個執行旗標是防誤觸機制，不是使用者批准的替代品。來源、資料庫、結果檔已存在
時均拒絕覆蓋／重用；沒有 force、DROP、TRUNCATE、搬移或自動清除失敗資料庫功能。
如需重跑，要先檢查失敗狀態，再提出新計畫，不能直接刪掉已有資料。

失敗處理：

- 生成／CSV 驗證失敗：停止，不建庫；可能保留完成的 CSV 供檢查。
- 建庫失敗／目標競爭出現：停止，不把資料匯入既有資料庫。
- COPY／ANALYZE 失敗：既有 loader 的交易會回滾表與資料；新建的空資料庫仍可能
  保留，因為 CREATE DATABASE 本身不能和 COPY 包在同一交易；不自動刪除。
- 完成驗證失敗：保留報告與目標供審查，不自動修正／重載／切換至 3B。

新測試 [test_prepare_sf1.py](../tests/test_prepare_sf1.py) 的建庫／生成／匯入全部
使用 mock；它們的通過不代表 SF1 已產生或實際載入。本輪亦有真實唯讀預檢，
但沒有執行 SF1 mutation 路徑。

本次請批准的範圍僅為上述 SF1 生成、獨立建庫、schema／COPY／ANALYZE 與驗收；
不包含索引實驗、修正 Q17～Q20、3B／3C 或任何 Git 寫入操作。
