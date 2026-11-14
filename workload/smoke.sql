-- Count finalized orders placed in 1995.
SELECT COUNT(*) AS finalized_orders
FROM tpch.orders
WHERE o_orderstatus = 'F'
  AND o_orderdate >= DATE '1995-01-01'
  AND o_orderdate < DATE '1996-01-01';

-- Count line items shipped by air in 1995.
SELECT COUNT(*) AS air_lineitems
FROM tpch.lineitem
WHERE l_shipmode = 'AIR'
  AND l_shipdate >= DATE '1995-01-01'
  AND l_shipdate < DATE '1996-01-01';

-- Count returned line items from finalized orders placed in 1995.
SELECT COUNT(*) AS returned_lineitems
FROM tpch.orders AS o
JOIN tpch.lineitem AS l ON l.l_orderkey = o.o_orderkey
WHERE o.o_orderstatus = 'F'
  AND o.o_orderdate >= DATE '1995-01-01'
  AND o.o_orderdate < DATE '1996-01-01'
  AND l.l_returnflag = 'R';
