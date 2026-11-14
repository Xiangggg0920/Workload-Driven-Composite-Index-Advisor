CREATE SCHEMA tpch;

CREATE TABLE tpch.orders (
    o_orderkey       bigint NOT NULL,
    o_custkey        bigint NOT NULL,
    o_orderstatus    char(1) NOT NULL,
    o_totalprice     numeric(15, 2) NOT NULL,
    o_orderdate      date NOT NULL,
    o_orderpriority  char(15) NOT NULL,
    o_clerk          char(15) NOT NULL,
    o_shippriority   integer NOT NULL,
    o_comment        varchar(79) NOT NULL
);

CREATE TABLE tpch.lineitem (
    l_orderkey       bigint NOT NULL,
    l_partkey        bigint NOT NULL,
    l_suppkey        bigint NOT NULL,
    l_linenumber     integer NOT NULL,
    l_quantity       numeric(15, 2) NOT NULL,
    l_extendedprice  numeric(15, 2) NOT NULL,
    l_discount       numeric(15, 2) NOT NULL,
    l_tax            numeric(15, 2) NOT NULL,
    l_returnflag     char(1) NOT NULL,
    l_linestatus     char(1) NOT NULL,
    l_shipdate       date NOT NULL,
    l_commitdate     date NOT NULL,
    l_receiptdate    date NOT NULL,
    l_shipinstruct   char(25) NOT NULL,
    l_shipmode       char(10) NOT NULL,
    l_comment        varchar(44) NOT NULL
);
