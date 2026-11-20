-- Group 9 custom TPC-H-derived workload; see benchmark20_coverage.md.
-- Fixed equal query weights. Not the standard TPC-H 22-query benchmark.

-- Q01: annual finalized-order summary; shared status/date index family.
SELECT COUNT(*) AS order_count, SUM(o_totalprice) AS total_price
FROM tpch.orders
WHERE o_orderstatus = 'F'
  AND o_orderdate >= DATE '1995-01-01'
  AND o_orderdate < DATE '1996-01-01';

-- Q02: narrower window, same index family as Q01.
SELECT o_orderkey, o_custkey, o_totalprice
FROM tpch.orders
WHERE o_orderstatus = 'F'
  AND o_orderdate >= DATE '1995-03-01'
  AND o_orderdate < DATE '1995-04-01'
ORDER BY o_orderkey;

-- Q03: two equalities followed by a date range.
SELECT COUNT(*) AS order_count, SUM(o_totalprice) AS total_price
FROM tpch.orders
WHERE o_orderpriority = '1-URGENT'
  AND o_orderstatus = 'F'
  AND o_orderdate >= DATE '1994-01-01'
  AND o_orderdate < DATE '1995-01-01';

-- Q04: omit the middle status column from Q03's priority/status/date family.
SELECT o_orderstatus, COUNT(*) AS order_count, SUM(o_totalprice) AS total_price
FROM tpch.orders
WHERE o_orderpriority = '1-URGENT'
  AND o_orderdate >= DATE '1994-01-01'
  AND o_orderdate < DATE '1995-01-01'
GROUP BY o_orderstatus
ORDER BY o_orderstatus;

-- Q05: equality-only left prefix of Q03's three-column family.
SELECT COUNT(*) AS order_count, AVG(o_totalprice) AS average_price
FROM tpch.orders
WHERE o_orderpriority = '1-URGENT'
  AND o_orderstatus = 'F';

-- Q06: selective customer history and ordering; no LIMIT early termination.
SELECT o_orderkey, o_orderdate, o_totalprice
FROM tpch.orders
WHERE o_custkey = 79
  AND o_orderdate >= DATE '1994-01-01'
  AND o_orderdate < DATE '1996-01-01'
ORDER BY o_orderdate, o_orderkey;

-- Q07: independent clerk/price family, rather than another status/date variant.
SELECT o_orderkey, o_orderdate, o_totalprice
FROM tpch.orders
WHERE o_clerk = 'Clerk#000000890'
  AND o_totalprice >= 150000
ORDER BY o_totalprice DESC, o_orderkey;

-- Q08: pure multi-range; constant-left comparison must normalize direction.
SELECT COUNT(*) AS order_count, SUM(o_totalprice) AS total_price
FROM tpch.orders
WHERE 100000 <= o_totalprice
  AND o_totalprice < 200000
  AND o_orderdate >= DATE '1994-01-01'
  AND o_orderdate < DATE '1995-01-01';

-- Q09: shipping-mode/date family; grouping is deliberately not a filter.
SELECT l_returnflag, COUNT(*) AS line_count,
       SUM(l_extendedprice * (1 - l_discount)) AS revenue
FROM tpch.lineitem
WHERE l_shipmode = 'AIR'
  AND l_shipdate >= DATE '1995-01-01'
  AND l_shipdate < DATE '1996-01-01'
GROUP BY l_returnflag
ORDER BY l_returnflag;

-- Q10: broad, correlated equalities; a sequential scan may be appropriate.
SELECT COUNT(*) AS line_count, SUM(l_quantity) AS quantity
FROM tpch.lineitem
WHERE l_returnflag = 'N'
  AND l_linestatus = 'O';

-- Q11: supplier/date versus supplier/quantity competition with Q12.
SELECT l_shipmode, COUNT(*) AS line_count, SUM(l_extendedprice) AS gross_price
FROM tpch.lineitem
WHERE l_suppkey = 1
  AND l_shipdate >= DATE '1995-01-01'
  AND l_shipdate < DATE '1996-01-01'
GROUP BY l_shipmode
ORDER BY l_shipmode;

-- Q12: shares Q11's leading equality but needs a different range suffix.
SELECT l_orderkey, l_linenumber, l_quantity
FROM tpch.lineitem
WHERE l_suppkey = 1
  AND l_quantity >= 30
ORDER BY l_orderkey, l_linenumber;

-- Q13: TPC-H Q6 filtering intent with explicit fixed interval endpoints.
SELECT SUM(l_extendedprice * l_discount) AS forecast_revenue
FROM tpch.lineitem
WHERE l_shipdate >= DATE '1994-01-01'
  AND l_shipdate < DATE '1995-01-01'
  AND l_discount >= 0.05
  AND l_discount <= 0.07
  AND l_quantity < 24;

-- Q14: reduced Q10-inspired return revenue; Q01's order filter is reusable.
SELECT o.o_orderpriority, COUNT(*) AS line_count,
       SUM(l.l_extendedprice * (1 - l.l_discount)) AS returned_revenue
FROM tpch.orders AS o
JOIN tpch.lineitem AS l ON o.o_orderkey = l.l_orderkey
WHERE o.o_orderstatus = 'F'
  AND o.o_orderdate >= DATE '1995-01-01'
  AND o.o_orderdate < DATE '1996-01-01'
  AND l.l_returnflag = 'R'
GROUP BY o.o_orderpriority
ORDER BY o.o_orderpriority;

-- Q15: selective outer relation and an equality on the inner relation.
SELECT o.o_orderkey, o.o_orderdate,
       SUM(l.l_extendedprice * (1 - l.l_discount)) AS air_revenue
FROM tpch.orders AS o
JOIN tpch.lineitem AS l ON l.l_orderkey = o.o_orderkey
WHERE o.o_custkey = 79
  AND o.o_orderdate >= DATE '1994-01-01'
  AND o.o_orderdate < DATE '1996-01-01'
  AND l.l_shipmode = 'AIR'
GROUP BY o.o_orderkey, o.o_orderdate
ORDER BY o.o_orderdate, o.o_orderkey;

-- Q16: Q3-inspired shipping cutoff, using priority instead of customer segment.
SELECT o.o_orderkey, o.o_orderdate, o.o_shippriority,
       SUM(l.l_extendedprice * (1 - l.l_discount)) AS pending_revenue
FROM tpch.orders AS o
JOIN tpch.lineitem AS l ON o.o_orderkey = l.l_orderkey
WHERE o.o_orderpriority = '2-HIGH'
  AND o.o_orderdate < DATE '1995-03-15'
  AND l.l_shipdate > DATE '1995-03-15'
GROUP BY o.o_orderkey, o.o_orderdate, o.o_shippriority
ORDER BY pending_revenue DESC, o.o_orderkey;

-- Q17: Q12-inspired late delivery, intentionally retain column comparisons.
SELECT o.o_orderpriority, COUNT(*) AS late_line_count
FROM tpch.orders AS o
JOIN tpch.lineitem AS l ON l.l_orderkey = o.o_orderkey
WHERE l.l_shipmode = 'MAIL'
  AND l.l_shipdate < l.l_commitdate
  AND l.l_commitdate < l.l_receiptdate
  AND l.l_receiptdate >= DATE '1994-01-01'
  AND l.l_receiptdate < DATE '1995-01-01'
GROUP BY o.o_orderpriority
ORDER BY o.o_orderpriority;

-- Q18: multi-point predicate; not rewritten into an equality for the Advisor.
SELECT COUNT(*) AS line_count,
       SUM(l_extendedprice * (1 - l_discount)) AS revenue
FROM tpch.lineitem
WHERE l_shipmode IN ('AIR', 'REG AIR')
  AND l_shipdate >= DATE '1995-01-01'
  AND l_shipdate < DATE '1996-01-01'
  AND l_discount >= 0.05;

-- Q19: boolean alternatives; retain both branches in the formal workload.
SELECT COUNT(*) AS order_count, SUM(o_totalprice) AS total_price
FROM tpch.orders
WHERE (o_orderstatus = 'F' OR o_orderstatus = 'P')
  AND o_orderdate >= DATE '1994-01-01'
  AND o_orderdate < DATE '1996-01-01';

-- Q20: same result as Q01, but the date column is wrapped in an expression.
SELECT COUNT(*) AS order_count, SUM(o_totalprice) AS total_price
FROM tpch.orders
WHERE EXTRACT(YEAR FROM o_orderdate) = 1995
  AND o_orderstatus = 'F';
