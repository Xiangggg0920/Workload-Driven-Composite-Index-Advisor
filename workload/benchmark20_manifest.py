"""Hand-reviewed semantic oracle, independent of Advisor extraction/generation.

Candidate orders describe the CURRENT heuristic under the observed catalog, not
optimal PostgreSQL indexes. Filters are independent cardinality probes, not SQL
substitutions: benchmark20.sql is always measured unchanged by the Runner.
"""


def case(number, filters, predicates, candidates, *, aliases=None, unsupported=None, joins=()):
    return dict(number=number, filters=filters, predicates=predicates,
                candidates=candidates, aliases=aliases or {table: table for table in filters},
                unsupported=unsupported, joins=joins)


def p(table, column, kind, operator):
    return ("tpch", table, column, kind, operator)


def o(column, kind, operator):
    return p("orders", "o_" + column, kind, operator)


def l(column, kind, operator):
    return p("lineitem", "l_" + column, kind, operator)


def oi(*columns):
    return ("orders", tuple("o_" + column for column in columns))


def li(*columns):
    return ("lineitem", tuple("l_" + column for column in columns))


JOIN = (("orders", "o_orderkey", "lineitem", "l_orderkey"),)
JOIN_PREDICATES = [o("orderkey", "join", "="), l("orderkey", "join", "=")]
JOIN_ALIASES = {"o": "orders", "l": "lineitem"}
YEAR95 = "o_orderdate >= DATE '1995-01-01' AND o_orderdate < DATE '1996-01-01'"
YEAR94 = "o_orderdate >= DATE '1994-01-01' AND o_orderdate < DATE '1995-01-01'"
HISTORY = "o_orderdate >= DATE '1994-01-01' AND o_orderdate < DATE '1996-01-01'"
SHIP95 = "l_shipdate >= DATE '1995-01-01' AND l_shipdate < DATE '1996-01-01'"
ORDER_RANGE = [o("orderdate", "range", ">="), o("orderdate", "range", "<")]
SHIP_RANGE = [l("shipdate", "range", ">="), l("shipdate", "range", "<")]

CASES = [
    case(1, {"orders": "o_orderstatus = 'F' AND " + YEAR95},
         [o("orderstatus", "equality", "=")] + ORDER_RANGE,
         [oi("orderstatus", "orderdate")]),
    case(2, {"orders": "o_orderstatus = 'F' AND o_orderdate >= DATE '1995-03-01' AND o_orderdate < DATE '1995-04-01'"},
         [o("orderstatus", "equality", "=")] + ORDER_RANGE,
         [oi("orderstatus", "orderdate")]),
    case(3, {"orders": "o_orderpriority = '1-URGENT' AND o_orderstatus = 'F' AND " + YEAR94},
         [o("orderpriority", "equality", "="), o("orderstatus", "equality", "=")] + ORDER_RANGE,
         [oi("orderpriority", "orderstatus"), oi("orderpriority", "orderstatus", "orderdate")]),
    case(4, {"orders": "o_orderpriority = '1-URGENT' AND " + YEAR94},
         [o("orderpriority", "equality", "=")] + ORDER_RANGE,
         [oi("orderpriority", "orderdate")]),
    case(5, {"orders": "o_orderpriority = '1-URGENT' AND o_orderstatus = 'F'"},
         [o("orderpriority", "equality", "="), o("orderstatus", "equality", "=")],
         [oi("orderpriority", "orderstatus")]),
    case(6, {"orders": "o_custkey = 79 AND " + HISTORY},
         [o("custkey", "equality", "=")] + ORDER_RANGE,
         [oi("custkey", "orderdate")]),
    case(7, {"orders": "o_clerk = 'Clerk#000000890' AND o_totalprice >= 150000"},
         [o("clerk", "equality", "="), o("totalprice", "range", ">=")],
         [oi("clerk", "totalprice")]),
    case(8, {"orders": "100000 <= o_totalprice AND o_totalprice < 200000 AND " + YEAR94},
         [o("totalprice", "range", ">="), o("totalprice", "range", "<")] + ORDER_RANGE, []),
    case(9, {"lineitem": "l_shipmode = 'AIR' AND " + SHIP95},
         [l("shipmode", "equality", "=")] + SHIP_RANGE,
         [li("shipmode", "shipdate")]),
    case(10, {"lineitem": "l_returnflag = 'N' AND l_linestatus = 'O'"},
         [l("returnflag", "equality", "="), l("linestatus", "equality", "=")],
         [li("returnflag", "linestatus")]),
    case(11, {"lineitem": "l_suppkey = 1 AND " + SHIP95},
         [l("suppkey", "equality", "=")] + SHIP_RANGE,
         [li("suppkey", "shipdate")]),
    case(12, {"lineitem": "l_suppkey = 1 AND l_quantity >= 30"},
         [l("suppkey", "equality", "="), l("quantity", "range", ">=")],
         [li("suppkey", "quantity")]),
    case(13, {"lineitem": "l_shipdate >= DATE '1994-01-01' AND l_shipdate < DATE '1995-01-01' AND l_discount >= 0.05 AND l_discount <= 0.07 AND l_quantity < 24"},
         SHIP_RANGE + [l("discount", "range", ">="), l("discount", "range", "<="), l("quantity", "range", "<")], []),
    case(14, {"orders": "o_orderstatus = 'F' AND " + YEAR95, "lineitem": "l_returnflag = 'R'"},
         [o("orderstatus", "equality", "=")] + ORDER_RANGE + [l("returnflag", "equality", "=")] + JOIN_PREDICATES,
         [oi("orderkey", "orderstatus"), oi("orderkey", "orderstatus", "orderdate"), li("orderkey", "returnflag")],
         aliases=JOIN_ALIASES, joins=JOIN),
    case(15, {"orders": "o_custkey = 79 AND " + HISTORY, "lineitem": "l_shipmode = 'AIR'"},
         [o("custkey", "equality", "=")] + ORDER_RANGE + [l("shipmode", "equality", "=")] + JOIN_PREDICATES,
         [oi("orderkey", "custkey"), oi("orderkey", "custkey", "orderdate"), li("orderkey", "shipmode")],
         aliases=JOIN_ALIASES, joins=JOIN),
    case(16, {"orders": "o_orderpriority = '2-HIGH' AND o_orderdate < DATE '1995-03-15'", "lineitem": "l_shipdate > DATE '1995-03-15'"},
         [o("orderpriority", "equality", "="), o("orderdate", "range", "<"), l("shipdate", "range", ">")] + JOIN_PREDICATES,
         [oi("orderkey", "orderpriority"), oi("orderkey", "orderpriority", "orderdate"), li("orderkey", "shipdate")],
         aliases=JOIN_ALIASES, joins=JOIN),
    case(17, {"orders": "TRUE", "lineitem": "l_shipmode = 'MAIL' AND l_shipdate < l_commitdate AND l_commitdate < l_receiptdate AND l_receiptdate >= DATE '1994-01-01' AND l_receiptdate < DATE '1995-01-01'"},
         [l("shipmode", "equality", "="), l("shipdate", "column_range", "<"), l("commitdate", "column_range", "<"),
          l("receiptdate", "range", ">="), l("receiptdate", "range", "<")] + JOIN_PREDICATES, [],
         aliases=JOIN_ALIASES, joins=JOIN, unsupported="column-to-literal comparison or equijoin"),
    case(18, {"lineitem": "l_shipmode IN ('AIR', 'REG AIR') AND " + SHIP95 + " AND l_discount >= 0.05"},
         [l("shipmode", "in", "IN")] + SHIP_RANGE + [l("discount", "range", ">=")], [],
         unsupported="unsupported predicate expression"),
    case(19, {"orders": "(o_orderstatus = 'F' OR o_orderstatus = 'P') AND " + HISTORY},
         [o("orderstatus", "or", "OR")] + ORDER_RANGE, [],
         unsupported="OR predicates are not supported"),
    case(20, {"orders": "EXTRACT(YEAR FROM o_orderdate) = 1995 AND o_orderstatus = 'F'"},
         [o("orderdate", "expression", "="), o("orderstatus", "equality", "=")], [],
         unsupported="column-to-literal comparison or equijoin"),
]
