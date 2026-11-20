# Benchmark 20 Coverage Matrix（先於 SQL 制定的設計）

這是基於 TPC-H 資料與查詢意圖的 Group 9 自訂索引實驗，**不是標準 TPC-H 的
22 條查詢、合規測試或 QphH 成績**。使用現有 orders／lineitem，不補建其他表。
Proposal 第 6～7 頁要求 20 條多欄查詢、延遲／buffer 與容量預算比較；本階段
只完成固定 Workload、語意檢查與無索引 baseline，不執行任何索引 DDL。

設計依據（對研究的應用是本專題的設計判斷，不是論文對這 20 條 SQL 的背書）：

- [TPC-H 3.0.1](https://www.tpc.org/tpc_documents_current_versions/pdf/tpc-h_v3.0.1.pdf)：
  借用 Q3 的待出貨營收、Q6 的日期／折扣／數量區間、Q10 的退貨營收、Q12 的
  運送／承諾／收貨日期意圖。Q14、Q16、Q17 依兩表限制改寫並明列差異；Q13
  保留 Q6 的篩選語意，以明確上下界取代 BETWEEN／日期運算，不因 Advisor 失敗再換 SQL。
- [Chaudhuri & Narasayya, VLDB 1997](https://www.vldb.org/conf/1997/P146.PDF)：
  採用整體 workload 配置評估的觀點，讓查詢共用候選也競爭不同索引需求，不逐條
  挑出「最佳」索引再直接宣稱整體最佳。
- [Valentin et al., ICDE 2000，作者提供的論文](https://www.cs.toronto.edu/~alan/papers/icde00.pdf)：
  借用儲存約束下綜合評估 predicate、join 與排序／分組用途的觀點；目前 Advisor
  沒有 optimizer what-if 能力，不能把它的 heuristic 分數當成該論文的成本估計。
- [PostgreSQL 17 多欄索引](https://www.postgresql.org/docs/17/indexes-multicolumn.html)：
  區分 leading equality、第一個 range、缺少中間欄與只有後綴的效果；缺少左前綴
  **不等於 PostgreSQL 絕對不能用該索引**，第三階段須看實際 Plan 與掃描工作量。

SF0.01 預先觀測：orders 15,000、lineitem 60,175；status 有 3 類、priority 5 類、
shipmode 7 類；customer／clerk 各 1,000 distinct，supplier 100 distinct。
o_shippriority 只有 0，因此只投影／分組，不用它製造虛假的高效益 predicate。
固定顧客 79、clerk 890、supplier 1 均存在；這些例子不能代表所有鍵值分布。
所有查詢初始權重相同，不能依事後 speedup 調權或移除慢／未支援的查詢。

下表的選擇率為**設計預期**，後續以驗證報告中的每表本地 filter count 為準，
不以 aggregate 回傳的一列誤當選擇率。索引欄位是比較假說，並非已驗證的最優順序。
O=orders、L=lineitem；所有 JOIN 都是 O.o_orderkey=L.l_orderkey。

| ID | 資料／Predicate 意圖 | 選擇率目標 | 索引與研究目的 | 預期 Advisor 行為 |
| --- | --- | --- | --- | --- |
| Q01 | O：status F＋1995 年日期窗；計數／金額 | 中 | (status,date) 共用基準；與 Q20 結果等價 | 解析，產生候選 |
| Q02 | O：status F＋1995/03 月窗 | 較窄 | 與 Q01 共用相同索引，暴露常數／區間寬度敏感度 | 解析；模型可能無法區別 Q01/Q02 |
| Q03 | O：priority urgent＋status F＋1994 日期窗 | 較窄 | 三欄 equality/equality/range；比較 (priority,status,date) 與交換前兩欄 | 解析，二／三欄前綴 |
| Q04 | O：priority urgent＋1994 日期窗，沒有 status | 中 | 對 Q03 三欄索引形成中間缺欄；(priority,date) 可能更合適 | 解析，另種候選 |
| Q05 | O：priority urgent＋status F，沒有日期 | 寬 | Q03 索引的完整等值左前綴；與 Q01 只共用 status | 解析，兩等值候選 |
| Q06 | O：固定顧客＋兩年日期窗，依日期排序 | 很窄 | 高 cardinality equality-first；cust/date 與 status/date 競爭空間 | 解析，候選；排序效益未建模 |
| Q07 | O：固定 clerk＋高總價 | 很窄 | 不同鍵值族群、clerk/price 欄序；避免只用日期／狀態 | 解析，候選 |
| Q08 | O：價格雙界＋1994 日期窗；常數置左 | 中 | 兩種 range 誰先；檢驗比較方向正規化；不預設高 distinct range 最好 | 解析，但現行 generator 不產生純 range 複合索引 |
| Q09 | L：AIR＋1995 船期；依 returnflag 分組 | 中 | (shipmode,shipdate) 共用族群與狀態族群的競爭 | 解析，候選；分組效益未建模 |
| Q10 | L：returnflag N＋linestatus O | 很寬 | 相關欄位與低選擇率反例；SeqScan 可能合理 | 解析，候選不等於值得建 |
| Q11 | L：supplier 1＋1995 船期 | 窄 | (suppkey,shipdate)，與 Q12 共用 equality 前綴 | 解析，候選 |
| Q12 | L：supplier 1＋quantity≥30 | 窄 | 相同 supplier、不同 range；對 Q11 是缺少中間欄／不同後綴需求 | 解析，候選 |
| Q13 | L：1994 船期＋折扣 .05～.07＋quantity<24 | 中 | TPC-H Q6 意圖；多 range／聚合；單欄與多欄 range 對照 | 解析，但無純 range 複合候選 |
| Q14 | O–L：F＋1995 訂單＋退貨 R；priority 營收 | 窄 join | Q10 意圖縮成兩表；Q01 本地條件共用；join-key-first 對 filter-first | 解析兩表 WHERE／ON，兩表候選 |
| Q15 | O–L：顧客 79＋兩年訂單＋AIR | 很窄 join | 少量外表結果對參數化內表索引；與 Q14 共用 join-key 前綴 | 解析兩表，兩表候選 |
| Q16 | O–L：high priority＋截日前訂單／截日後船期 | 窄 join | Q3 意圖：移除 customer segment、以 priority 聚焦；group/order 營收，不加 LIMIT | 解析；join 方向／成本仍是代理值 |
| Q17 | O–L：MAIL＋1994 收貨＋ship<commit<receipt | 窄 join | Q12 意圖：單 shipmode，保留欄位對欄位日期關係 | 預期拒絕：非等值 column-to-column 尚未支援 |
| Q18 | L：AIR／REG AIR 的 IN＋船期＋折扣下界 | 中 | 多點 predicate；可能需 bitmap／多段 scan，不強迫單一等值模型 | 預期拒絕：IN 尚未支援 |
| Q19 | O：(F OR P)＋兩年日期窗 | 寬 | Boolean alternatives；不能丟掉 OR 或只分析其中分支 | 預期拒絕：OR 尚未支援 |
| Q20 | O：EXTRACT(year FROM date)=1995＋F | 中 | 與 Q01 等價的非直接 sargable 寫法；普通日期 B-tree 與 expression index 的差異 | 預期拒絕：函式 predicate；不新增 expression index |

全體覆蓋：16 單表／4 JOIN；純等值、純 range、混合、相關性與寬／窄 filter；
高 distinct 鍵、低 distinct 類別、日期／數值 range；共用索引與不同後綴；
三欄完整前綴、缺中間欄、僅共用後綴；COUNT/SUM、投影、GROUP BY、ORDER BY。
保留 4 條語法能力邊界與 2 條已解析但無複合候選的控制組。這些數量是依上述
覆蓋需求形成的結果，不是先設定的配額。

第三階段公平性：主報告固定列出全部 20 條 baseline／各索引情境的測量；另外
明列 16 條 Advisor 可解析子集合的結果。未支援的查詢仍可能受其他查詢的索引
影響，不能直接說效益必為 0，也不能把它們從總 workload 分母靜默移除。
