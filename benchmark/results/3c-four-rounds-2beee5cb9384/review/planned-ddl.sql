-- REVIEW ONLY. Target: advisor_benchmark. Do not execute this file manually.
-- Plan SHA256: 9eaf530053f64954b2798f826bb71e6559382ad57d48e139a8a17dbe7c6ef47a; real execution requires controller approval.

-- r01b1024s1 baseline 1024 MiB; one atomic build transaction

-- r01b1024s2 single 1024 MiB; one atomic build transaction
CREATE INDEX "g9c_fd1bc32b3b27_r01b1024s2_637db5b0ec" ON "tpch"."orders" USING btree ("o_orderdate");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r01b1024s2_637db5b0ec" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r01b1024s2_637db5b0ec" RESTRICT;
CREATE INDEX "g9c_fd1bc32b3b27_r01b1024s2_9e235190eb" ON "tpch"."orders" USING btree ("o_orderstatus");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r01b1024s2_9e235190eb" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r01b1024s2_9e235190eb" RESTRICT;
CREATE INDEX "g9c_fd1bc32b3b27_r01b1024s2_07a39fda09" ON "tpch"."lineitem" USING btree ("l_shipdate");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r01b1024s2_07a39fda09" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r01b1024s2_07a39fda09" RESTRICT;
CREATE INDEX "g9c_fd1bc32b3b27_r01b1024s2_a828fe6df1" ON "tpch"."orders" USING btree ("o_orderkey");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r01b1024s2_a828fe6df1" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r01b1024s2_a828fe6df1" RESTRICT;
CREATE INDEX "g9c_fd1bc32b3b27_r01b1024s2_b83a3ac03b" ON "tpch"."orders" USING btree ("o_orderpriority");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r01b1024s2_b83a3ac03b" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r01b1024s2_b83a3ac03b" RESTRICT;
CREATE INDEX "g9c_fd1bc32b3b27_r01b1024s2_a2e39e3e09" ON "tpch"."lineitem" USING btree ("l_orderkey");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r01b1024s2_a2e39e3e09" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r01b1024s2_a2e39e3e09" RESTRICT;
CREATE INDEX "g9c_fd1bc32b3b27_r01b1024s2_1b3cca0e6f" ON "tpch"."lineitem" USING btree ("l_shipmode");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r01b1024s2_1b3cca0e6f" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r01b1024s2_1b3cca0e6f" RESTRICT;
CREATE INDEX "g9c_fd1bc32b3b27_r01b1024s2_b9eae9c8d4" ON "tpch"."orders" USING btree ("o_custkey");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r01b1024s2_b9eae9c8d4" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r01b1024s2_b9eae9c8d4" RESTRICT;
CREATE INDEX "g9c_fd1bc32b3b27_r01b1024s2_913f745a9d" ON "tpch"."orders" USING btree ("o_totalprice");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r01b1024s2_913f745a9d" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r01b1024s2_913f745a9d" RESTRICT;
CREATE INDEX "g9c_fd1bc32b3b27_r01b1024s2_0eb51e91a2" ON "tpch"."lineitem" USING btree ("l_returnflag");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r01b1024s2_0eb51e91a2" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r01b1024s2_0eb51e91a2" RESTRICT;
CREATE INDEX "g9c_fd1bc32b3b27_r01b1024s2_57d6470fab" ON "tpch"."orders" USING btree ("o_clerk");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r01b1024s2_57d6470fab" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r01b1024s2_57d6470fab" RESTRICT;

-- r01b1024s3 advisor 1024 MiB; one atomic build transaction
CREATE INDEX "g9c_fd1bc32b3b27_r01b1024s3_d68b2b342a" ON "tpch"."orders" USING btree ("o_orderstatus", "o_orderdate");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r01b1024s3_d68b2b342a" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r01b1024s3_d68b2b342a" RESTRICT;
CREATE INDEX "g9c_fd1bc32b3b27_r01b1024s3_a356299821" ON "tpch"."lineitem" USING btree ("l_orderkey", "l_returnflag");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r01b1024s3_a356299821" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r01b1024s3_a356299821" RESTRICT;
CREATE INDEX "g9c_fd1bc32b3b27_r01b1024s3_4b2ee23d70" ON "tpch"."orders" USING btree ("o_orderkey", "o_orderstatus");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r01b1024s3_4b2ee23d70" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r01b1024s3_4b2ee23d70" RESTRICT;
CREATE INDEX "g9c_fd1bc32b3b27_r01b1024s3_b6351c0547" ON "tpch"."lineitem" USING btree ("l_suppkey", "l_shipdate");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r01b1024s3_b6351c0547" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r01b1024s3_b6351c0547" RESTRICT;
CREATE INDEX "g9c_fd1bc32b3b27_r01b1024s3_d3d040f25b" ON "tpch"."lineitem" USING btree ("l_returnflag", "l_linestatus");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r01b1024s3_d3d040f25b" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r01b1024s3_d3d040f25b" RESTRICT;
CREATE INDEX "g9c_fd1bc32b3b27_r01b1024s3_5007cdd031" ON "tpch"."orders" USING btree ("o_custkey", "o_orderdate");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r01b1024s3_5007cdd031" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r01b1024s3_5007cdd031" RESTRICT;
CREATE INDEX "g9c_fd1bc32b3b27_r01b1024s3_eb17e9a7f0" ON "tpch"."lineitem" USING btree ("l_shipmode", "l_shipdate");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r01b1024s3_eb17e9a7f0" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r01b1024s3_eb17e9a7f0" RESTRICT;
CREATE INDEX "g9c_fd1bc32b3b27_r01b1024s3_5d77d0fe48" ON "tpch"."orders" USING btree ("o_orderpriority", "o_orderstatus");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r01b1024s3_5d77d0fe48" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r01b1024s3_5d77d0fe48" RESTRICT;

-- r01b1024s4 suboptimal 1024 MiB; one atomic build transaction
CREATE INDEX "g9c_fd1bc32b3b27_r01b1024s4_d68b2b342a" ON "tpch"."orders" USING btree ("o_orderstatus", "o_orderdate");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r01b1024s4_d68b2b342a" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r01b1024s4_d68b2b342a" RESTRICT;
CREATE INDEX "g9c_fd1bc32b3b27_r01b1024s4_26d321fc5d" ON "tpch"."orders" USING btree ("o_orderpriority", "o_orderdate");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r01b1024s4_26d321fc5d" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r01b1024s4_26d321fc5d" RESTRICT;
CREATE INDEX "g9c_fd1bc32b3b27_r01b1024s4_eb17e9a7f0" ON "tpch"."lineitem" USING btree ("l_shipmode", "l_shipdate");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r01b1024s4_eb17e9a7f0" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r01b1024s4_eb17e9a7f0" RESTRICT;
CREATE INDEX "g9c_fd1bc32b3b27_r01b1024s4_5007cdd031" ON "tpch"."orders" USING btree ("o_custkey", "o_orderdate");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r01b1024s4_5007cdd031" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r01b1024s4_5007cdd031" RESTRICT;
CREATE INDEX "g9c_fd1bc32b3b27_r01b1024s4_5d77d0fe48" ON "tpch"."orders" USING btree ("o_orderpriority", "o_orderstatus");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r01b1024s4_5d77d0fe48" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r01b1024s4_5d77d0fe48" RESTRICT;
CREATE INDEX "g9c_fd1bc32b3b27_r01b1024s4_4e1a1ae80d" ON "tpch"."lineitem" USING btree ("l_shipdate", "l_orderkey");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r01b1024s4_4e1a1ae80d" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r01b1024s4_4e1a1ae80d" RESTRICT;
CREATE INDEX "g9c_fd1bc32b3b27_r01b1024s4_9914763ac6" ON "tpch"."lineitem" USING btree ("l_shipmode", "l_orderkey");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r01b1024s4_9914763ac6" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r01b1024s4_9914763ac6" RESTRICT;
CREATE INDEX "g9c_fd1bc32b3b27_r01b1024s4_1b28205a0e" ON "tpch"."orders" USING btree ("o_totalprice", "o_orderdate");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r01b1024s4_1b28205a0e" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r01b1024s4_1b28205a0e" RESTRICT;

-- r01b100s1 baseline 100 MiB; one atomic build transaction

-- r01b100s2 single 100 MiB; one atomic build transaction
CREATE INDEX "g9c_fd1bc32b3b27_r01b100s2_637db5b0ec" ON "tpch"."orders" USING btree ("o_orderdate");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r01b100s2_637db5b0ec" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r01b100s2_637db5b0ec" RESTRICT;
CREATE INDEX "g9c_fd1bc32b3b27_r01b100s2_9e235190eb" ON "tpch"."orders" USING btree ("o_orderstatus");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r01b100s2_9e235190eb" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r01b100s2_9e235190eb" RESTRICT;

-- r01b100s3 advisor 100 MiB; one atomic build transaction
CREATE INDEX "g9c_fd1bc32b3b27_r01b100s3_4b2ee23d70" ON "tpch"."orders" USING btree ("o_orderkey", "o_orderstatus");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r01b100s3_4b2ee23d70" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r01b100s3_4b2ee23d70" RESTRICT;
CREATE INDEX "g9c_fd1bc32b3b27_r01b100s3_d68b2b342a" ON "tpch"."orders" USING btree ("o_orderstatus", "o_orderdate");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r01b100s3_d68b2b342a" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r01b100s3_d68b2b342a" RESTRICT;

-- r01b100s4 suboptimal 100 MiB; one atomic build transaction
CREATE INDEX "g9c_fd1bc32b3b27_r01b100s4_d68b2b342a" ON "tpch"."orders" USING btree ("o_orderstatus", "o_orderdate");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r01b100s4_d68b2b342a" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r01b100s4_d68b2b342a" RESTRICT;
CREATE INDEX "g9c_fd1bc32b3b27_r01b100s4_5007cdd031" ON "tpch"."orders" USING btree ("o_custkey", "o_orderdate");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r01b100s4_5007cdd031" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r01b100s4_5007cdd031" RESTRICT;

-- r01b500s1 baseline 500 MiB; one atomic build transaction

-- r01b500s2 single 500 MiB; one atomic build transaction
CREATE INDEX "g9c_fd1bc32b3b27_r01b500s2_637db5b0ec" ON "tpch"."orders" USING btree ("o_orderdate");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r01b500s2_637db5b0ec" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r01b500s2_637db5b0ec" RESTRICT;
CREATE INDEX "g9c_fd1bc32b3b27_r01b500s2_9e235190eb" ON "tpch"."orders" USING btree ("o_orderstatus");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r01b500s2_9e235190eb" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r01b500s2_9e235190eb" RESTRICT;
CREATE INDEX "g9c_fd1bc32b3b27_r01b500s2_07a39fda09" ON "tpch"."lineitem" USING btree ("l_shipdate");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r01b500s2_07a39fda09" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r01b500s2_07a39fda09" RESTRICT;
CREATE INDEX "g9c_fd1bc32b3b27_r01b500s2_a828fe6df1" ON "tpch"."orders" USING btree ("o_orderkey");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r01b500s2_a828fe6df1" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r01b500s2_a828fe6df1" RESTRICT;
CREATE INDEX "g9c_fd1bc32b3b27_r01b500s2_b83a3ac03b" ON "tpch"."orders" USING btree ("o_orderpriority");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r01b500s2_b83a3ac03b" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r01b500s2_b83a3ac03b" RESTRICT;
CREATE INDEX "g9c_fd1bc32b3b27_r01b500s2_b9eae9c8d4" ON "tpch"."orders" USING btree ("o_custkey");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r01b500s2_b9eae9c8d4" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r01b500s2_b9eae9c8d4" RESTRICT;
CREATE INDEX "g9c_fd1bc32b3b27_r01b500s2_913f745a9d" ON "tpch"."orders" USING btree ("o_totalprice");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r01b500s2_913f745a9d" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r01b500s2_913f745a9d" RESTRICT;
CREATE INDEX "g9c_fd1bc32b3b27_r01b500s2_57d6470fab" ON "tpch"."orders" USING btree ("o_clerk");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r01b500s2_57d6470fab" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r01b500s2_57d6470fab" RESTRICT;

-- r01b500s3 advisor 500 MiB; one atomic build transaction
CREATE INDEX "g9c_fd1bc32b3b27_r01b500s3_d68b2b342a" ON "tpch"."orders" USING btree ("o_orderstatus", "o_orderdate");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r01b500s3_d68b2b342a" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r01b500s3_d68b2b342a" RESTRICT;
CREATE INDEX "g9c_fd1bc32b3b27_r01b500s3_a356299821" ON "tpch"."lineitem" USING btree ("l_orderkey", "l_returnflag");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r01b500s3_a356299821" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r01b500s3_a356299821" RESTRICT;
CREATE INDEX "g9c_fd1bc32b3b27_r01b500s3_4b2ee23d70" ON "tpch"."orders" USING btree ("o_orderkey", "o_orderstatus");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r01b500s3_4b2ee23d70" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r01b500s3_4b2ee23d70" RESTRICT;
CREATE INDEX "g9c_fd1bc32b3b27_r01b500s3_d3d040f25b" ON "tpch"."lineitem" USING btree ("l_returnflag", "l_linestatus");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r01b500s3_d3d040f25b" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r01b500s3_d3d040f25b" RESTRICT;

-- r01b500s4 suboptimal 500 MiB; one atomic build transaction
CREATE INDEX "g9c_fd1bc32b3b27_r01b500s4_d68b2b342a" ON "tpch"."orders" USING btree ("o_orderstatus", "o_orderdate");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r01b500s4_d68b2b342a" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r01b500s4_d68b2b342a" RESTRICT;
CREATE INDEX "g9c_fd1bc32b3b27_r01b500s4_26d321fc5d" ON "tpch"."orders" USING btree ("o_orderpriority", "o_orderdate");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r01b500s4_26d321fc5d" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r01b500s4_26d321fc5d" RESTRICT;
CREATE INDEX "g9c_fd1bc32b3b27_r01b500s4_eb17e9a7f0" ON "tpch"."lineitem" USING btree ("l_shipmode", "l_shipdate");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r01b500s4_eb17e9a7f0" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r01b500s4_eb17e9a7f0" RESTRICT;
CREATE INDEX "g9c_fd1bc32b3b27_r01b500s4_5007cdd031" ON "tpch"."orders" USING btree ("o_custkey", "o_orderdate");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r01b500s4_5007cdd031" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r01b500s4_5007cdd031" RESTRICT;
CREATE INDEX "g9c_fd1bc32b3b27_r01b500s4_5d77d0fe48" ON "tpch"."orders" USING btree ("o_orderpriority", "o_orderstatus");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r01b500s4_5d77d0fe48" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r01b500s4_5d77d0fe48" RESTRICT;

-- r02b500s1 single 500 MiB; one atomic build transaction
CREATE INDEX "g9c_fd1bc32b3b27_r02b500s1_637db5b0ec" ON "tpch"."orders" USING btree ("o_orderdate");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r02b500s1_637db5b0ec" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r02b500s1_637db5b0ec" RESTRICT;
CREATE INDEX "g9c_fd1bc32b3b27_r02b500s1_9e235190eb" ON "tpch"."orders" USING btree ("o_orderstatus");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r02b500s1_9e235190eb" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r02b500s1_9e235190eb" RESTRICT;
CREATE INDEX "g9c_fd1bc32b3b27_r02b500s1_07a39fda09" ON "tpch"."lineitem" USING btree ("l_shipdate");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r02b500s1_07a39fda09" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r02b500s1_07a39fda09" RESTRICT;
CREATE INDEX "g9c_fd1bc32b3b27_r02b500s1_a828fe6df1" ON "tpch"."orders" USING btree ("o_orderkey");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r02b500s1_a828fe6df1" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r02b500s1_a828fe6df1" RESTRICT;
CREATE INDEX "g9c_fd1bc32b3b27_r02b500s1_b83a3ac03b" ON "tpch"."orders" USING btree ("o_orderpriority");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r02b500s1_b83a3ac03b" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r02b500s1_b83a3ac03b" RESTRICT;
CREATE INDEX "g9c_fd1bc32b3b27_r02b500s1_b9eae9c8d4" ON "tpch"."orders" USING btree ("o_custkey");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r02b500s1_b9eae9c8d4" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r02b500s1_b9eae9c8d4" RESTRICT;
CREATE INDEX "g9c_fd1bc32b3b27_r02b500s1_913f745a9d" ON "tpch"."orders" USING btree ("o_totalprice");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r02b500s1_913f745a9d" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r02b500s1_913f745a9d" RESTRICT;
CREATE INDEX "g9c_fd1bc32b3b27_r02b500s1_57d6470fab" ON "tpch"."orders" USING btree ("o_clerk");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r02b500s1_57d6470fab" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r02b500s1_57d6470fab" RESTRICT;

-- r02b500s2 suboptimal 500 MiB; one atomic build transaction
CREATE INDEX "g9c_fd1bc32b3b27_r02b500s2_d68b2b342a" ON "tpch"."orders" USING btree ("o_orderstatus", "o_orderdate");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r02b500s2_d68b2b342a" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r02b500s2_d68b2b342a" RESTRICT;
CREATE INDEX "g9c_fd1bc32b3b27_r02b500s2_26d321fc5d" ON "tpch"."orders" USING btree ("o_orderpriority", "o_orderdate");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r02b500s2_26d321fc5d" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r02b500s2_26d321fc5d" RESTRICT;
CREATE INDEX "g9c_fd1bc32b3b27_r02b500s2_eb17e9a7f0" ON "tpch"."lineitem" USING btree ("l_shipmode", "l_shipdate");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r02b500s2_eb17e9a7f0" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r02b500s2_eb17e9a7f0" RESTRICT;
CREATE INDEX "g9c_fd1bc32b3b27_r02b500s2_5007cdd031" ON "tpch"."orders" USING btree ("o_custkey", "o_orderdate");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r02b500s2_5007cdd031" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r02b500s2_5007cdd031" RESTRICT;
CREATE INDEX "g9c_fd1bc32b3b27_r02b500s2_5d77d0fe48" ON "tpch"."orders" USING btree ("o_orderpriority", "o_orderstatus");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r02b500s2_5d77d0fe48" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r02b500s2_5d77d0fe48" RESTRICT;

-- r02b500s3 baseline 500 MiB; one atomic build transaction

-- r02b500s4 advisor 500 MiB; one atomic build transaction
CREATE INDEX "g9c_fd1bc32b3b27_r02b500s4_d68b2b342a" ON "tpch"."orders" USING btree ("o_orderstatus", "o_orderdate");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r02b500s4_d68b2b342a" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r02b500s4_d68b2b342a" RESTRICT;
CREATE INDEX "g9c_fd1bc32b3b27_r02b500s4_a356299821" ON "tpch"."lineitem" USING btree ("l_orderkey", "l_returnflag");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r02b500s4_a356299821" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r02b500s4_a356299821" RESTRICT;
CREATE INDEX "g9c_fd1bc32b3b27_r02b500s4_4b2ee23d70" ON "tpch"."orders" USING btree ("o_orderkey", "o_orderstatus");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r02b500s4_4b2ee23d70" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r02b500s4_4b2ee23d70" RESTRICT;
CREATE INDEX "g9c_fd1bc32b3b27_r02b500s4_d3d040f25b" ON "tpch"."lineitem" USING btree ("l_returnflag", "l_linestatus");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r02b500s4_d3d040f25b" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r02b500s4_d3d040f25b" RESTRICT;

-- r02b100s1 single 100 MiB; one atomic build transaction
CREATE INDEX "g9c_fd1bc32b3b27_r02b100s1_637db5b0ec" ON "tpch"."orders" USING btree ("o_orderdate");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r02b100s1_637db5b0ec" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r02b100s1_637db5b0ec" RESTRICT;
CREATE INDEX "g9c_fd1bc32b3b27_r02b100s1_9e235190eb" ON "tpch"."orders" USING btree ("o_orderstatus");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r02b100s1_9e235190eb" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r02b100s1_9e235190eb" RESTRICT;

-- r02b100s2 suboptimal 100 MiB; one atomic build transaction
CREATE INDEX "g9c_fd1bc32b3b27_r02b100s2_d68b2b342a" ON "tpch"."orders" USING btree ("o_orderstatus", "o_orderdate");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r02b100s2_d68b2b342a" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r02b100s2_d68b2b342a" RESTRICT;
CREATE INDEX "g9c_fd1bc32b3b27_r02b100s2_5007cdd031" ON "tpch"."orders" USING btree ("o_custkey", "o_orderdate");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r02b100s2_5007cdd031" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r02b100s2_5007cdd031" RESTRICT;

-- r02b100s3 baseline 100 MiB; one atomic build transaction

-- r02b100s4 advisor 100 MiB; one atomic build transaction
CREATE INDEX "g9c_fd1bc32b3b27_r02b100s4_4b2ee23d70" ON "tpch"."orders" USING btree ("o_orderkey", "o_orderstatus");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r02b100s4_4b2ee23d70" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r02b100s4_4b2ee23d70" RESTRICT;
CREATE INDEX "g9c_fd1bc32b3b27_r02b100s4_d68b2b342a" ON "tpch"."orders" USING btree ("o_orderstatus", "o_orderdate");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r02b100s4_d68b2b342a" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r02b100s4_d68b2b342a" RESTRICT;

-- r02b1024s1 single 1024 MiB; one atomic build transaction
CREATE INDEX "g9c_fd1bc32b3b27_r02b1024s1_637db5b0ec" ON "tpch"."orders" USING btree ("o_orderdate");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r02b1024s1_637db5b0ec" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r02b1024s1_637db5b0ec" RESTRICT;
CREATE INDEX "g9c_fd1bc32b3b27_r02b1024s1_9e235190eb" ON "tpch"."orders" USING btree ("o_orderstatus");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r02b1024s1_9e235190eb" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r02b1024s1_9e235190eb" RESTRICT;
CREATE INDEX "g9c_fd1bc32b3b27_r02b1024s1_07a39fda09" ON "tpch"."lineitem" USING btree ("l_shipdate");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r02b1024s1_07a39fda09" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r02b1024s1_07a39fda09" RESTRICT;
CREATE INDEX "g9c_fd1bc32b3b27_r02b1024s1_a828fe6df1" ON "tpch"."orders" USING btree ("o_orderkey");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r02b1024s1_a828fe6df1" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r02b1024s1_a828fe6df1" RESTRICT;
CREATE INDEX "g9c_fd1bc32b3b27_r02b1024s1_b83a3ac03b" ON "tpch"."orders" USING btree ("o_orderpriority");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r02b1024s1_b83a3ac03b" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r02b1024s1_b83a3ac03b" RESTRICT;
CREATE INDEX "g9c_fd1bc32b3b27_r02b1024s1_a2e39e3e09" ON "tpch"."lineitem" USING btree ("l_orderkey");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r02b1024s1_a2e39e3e09" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r02b1024s1_a2e39e3e09" RESTRICT;
CREATE INDEX "g9c_fd1bc32b3b27_r02b1024s1_1b3cca0e6f" ON "tpch"."lineitem" USING btree ("l_shipmode");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r02b1024s1_1b3cca0e6f" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r02b1024s1_1b3cca0e6f" RESTRICT;
CREATE INDEX "g9c_fd1bc32b3b27_r02b1024s1_b9eae9c8d4" ON "tpch"."orders" USING btree ("o_custkey");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r02b1024s1_b9eae9c8d4" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r02b1024s1_b9eae9c8d4" RESTRICT;
CREATE INDEX "g9c_fd1bc32b3b27_r02b1024s1_913f745a9d" ON "tpch"."orders" USING btree ("o_totalprice");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r02b1024s1_913f745a9d" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r02b1024s1_913f745a9d" RESTRICT;
CREATE INDEX "g9c_fd1bc32b3b27_r02b1024s1_0eb51e91a2" ON "tpch"."lineitem" USING btree ("l_returnflag");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r02b1024s1_0eb51e91a2" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r02b1024s1_0eb51e91a2" RESTRICT;
CREATE INDEX "g9c_fd1bc32b3b27_r02b1024s1_57d6470fab" ON "tpch"."orders" USING btree ("o_clerk");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r02b1024s1_57d6470fab" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r02b1024s1_57d6470fab" RESTRICT;

-- r02b1024s2 suboptimal 1024 MiB; one atomic build transaction
CREATE INDEX "g9c_fd1bc32b3b27_r02b1024s2_d68b2b342a" ON "tpch"."orders" USING btree ("o_orderstatus", "o_orderdate");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r02b1024s2_d68b2b342a" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r02b1024s2_d68b2b342a" RESTRICT;
CREATE INDEX "g9c_fd1bc32b3b27_r02b1024s2_26d321fc5d" ON "tpch"."orders" USING btree ("o_orderpriority", "o_orderdate");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r02b1024s2_26d321fc5d" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r02b1024s2_26d321fc5d" RESTRICT;
CREATE INDEX "g9c_fd1bc32b3b27_r02b1024s2_eb17e9a7f0" ON "tpch"."lineitem" USING btree ("l_shipmode", "l_shipdate");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r02b1024s2_eb17e9a7f0" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r02b1024s2_eb17e9a7f0" RESTRICT;
CREATE INDEX "g9c_fd1bc32b3b27_r02b1024s2_5007cdd031" ON "tpch"."orders" USING btree ("o_custkey", "o_orderdate");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r02b1024s2_5007cdd031" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r02b1024s2_5007cdd031" RESTRICT;
CREATE INDEX "g9c_fd1bc32b3b27_r02b1024s2_5d77d0fe48" ON "tpch"."orders" USING btree ("o_orderpriority", "o_orderstatus");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r02b1024s2_5d77d0fe48" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r02b1024s2_5d77d0fe48" RESTRICT;
CREATE INDEX "g9c_fd1bc32b3b27_r02b1024s2_4e1a1ae80d" ON "tpch"."lineitem" USING btree ("l_shipdate", "l_orderkey");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r02b1024s2_4e1a1ae80d" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r02b1024s2_4e1a1ae80d" RESTRICT;
CREATE INDEX "g9c_fd1bc32b3b27_r02b1024s2_9914763ac6" ON "tpch"."lineitem" USING btree ("l_shipmode", "l_orderkey");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r02b1024s2_9914763ac6" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r02b1024s2_9914763ac6" RESTRICT;
CREATE INDEX "g9c_fd1bc32b3b27_r02b1024s2_1b28205a0e" ON "tpch"."orders" USING btree ("o_totalprice", "o_orderdate");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r02b1024s2_1b28205a0e" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r02b1024s2_1b28205a0e" RESTRICT;

-- r02b1024s3 baseline 1024 MiB; one atomic build transaction

-- r02b1024s4 advisor 1024 MiB; one atomic build transaction
CREATE INDEX "g9c_fd1bc32b3b27_r02b1024s4_d68b2b342a" ON "tpch"."orders" USING btree ("o_orderstatus", "o_orderdate");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r02b1024s4_d68b2b342a" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r02b1024s4_d68b2b342a" RESTRICT;
CREATE INDEX "g9c_fd1bc32b3b27_r02b1024s4_a356299821" ON "tpch"."lineitem" USING btree ("l_orderkey", "l_returnflag");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r02b1024s4_a356299821" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r02b1024s4_a356299821" RESTRICT;
CREATE INDEX "g9c_fd1bc32b3b27_r02b1024s4_4b2ee23d70" ON "tpch"."orders" USING btree ("o_orderkey", "o_orderstatus");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r02b1024s4_4b2ee23d70" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r02b1024s4_4b2ee23d70" RESTRICT;
CREATE INDEX "g9c_fd1bc32b3b27_r02b1024s4_b6351c0547" ON "tpch"."lineitem" USING btree ("l_suppkey", "l_shipdate");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r02b1024s4_b6351c0547" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r02b1024s4_b6351c0547" RESTRICT;
CREATE INDEX "g9c_fd1bc32b3b27_r02b1024s4_d3d040f25b" ON "tpch"."lineitem" USING btree ("l_returnflag", "l_linestatus");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r02b1024s4_d3d040f25b" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r02b1024s4_d3d040f25b" RESTRICT;
CREATE INDEX "g9c_fd1bc32b3b27_r02b1024s4_5007cdd031" ON "tpch"."orders" USING btree ("o_custkey", "o_orderdate");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r02b1024s4_5007cdd031" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r02b1024s4_5007cdd031" RESTRICT;
CREATE INDEX "g9c_fd1bc32b3b27_r02b1024s4_eb17e9a7f0" ON "tpch"."lineitem" USING btree ("l_shipmode", "l_shipdate");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r02b1024s4_eb17e9a7f0" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r02b1024s4_eb17e9a7f0" RESTRICT;
CREATE INDEX "g9c_fd1bc32b3b27_r02b1024s4_5d77d0fe48" ON "tpch"."orders" USING btree ("o_orderpriority", "o_orderstatus");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r02b1024s4_5d77d0fe48" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r02b1024s4_5d77d0fe48" RESTRICT;

-- r03b1024s1 suboptimal 1024 MiB; one atomic build transaction
CREATE INDEX "g9c_fd1bc32b3b27_r03b1024s1_d68b2b342a" ON "tpch"."orders" USING btree ("o_orderstatus", "o_orderdate");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r03b1024s1_d68b2b342a" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r03b1024s1_d68b2b342a" RESTRICT;
CREATE INDEX "g9c_fd1bc32b3b27_r03b1024s1_26d321fc5d" ON "tpch"."orders" USING btree ("o_orderpriority", "o_orderdate");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r03b1024s1_26d321fc5d" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r03b1024s1_26d321fc5d" RESTRICT;
CREATE INDEX "g9c_fd1bc32b3b27_r03b1024s1_eb17e9a7f0" ON "tpch"."lineitem" USING btree ("l_shipmode", "l_shipdate");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r03b1024s1_eb17e9a7f0" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r03b1024s1_eb17e9a7f0" RESTRICT;
CREATE INDEX "g9c_fd1bc32b3b27_r03b1024s1_5007cdd031" ON "tpch"."orders" USING btree ("o_custkey", "o_orderdate");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r03b1024s1_5007cdd031" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r03b1024s1_5007cdd031" RESTRICT;
CREATE INDEX "g9c_fd1bc32b3b27_r03b1024s1_5d77d0fe48" ON "tpch"."orders" USING btree ("o_orderpriority", "o_orderstatus");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r03b1024s1_5d77d0fe48" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r03b1024s1_5d77d0fe48" RESTRICT;
CREATE INDEX "g9c_fd1bc32b3b27_r03b1024s1_4e1a1ae80d" ON "tpch"."lineitem" USING btree ("l_shipdate", "l_orderkey");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r03b1024s1_4e1a1ae80d" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r03b1024s1_4e1a1ae80d" RESTRICT;
CREATE INDEX "g9c_fd1bc32b3b27_r03b1024s1_9914763ac6" ON "tpch"."lineitem" USING btree ("l_shipmode", "l_orderkey");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r03b1024s1_9914763ac6" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r03b1024s1_9914763ac6" RESTRICT;
CREATE INDEX "g9c_fd1bc32b3b27_r03b1024s1_1b28205a0e" ON "tpch"."orders" USING btree ("o_totalprice", "o_orderdate");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r03b1024s1_1b28205a0e" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r03b1024s1_1b28205a0e" RESTRICT;

-- r03b1024s2 advisor 1024 MiB; one atomic build transaction
CREATE INDEX "g9c_fd1bc32b3b27_r03b1024s2_d68b2b342a" ON "tpch"."orders" USING btree ("o_orderstatus", "o_orderdate");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r03b1024s2_d68b2b342a" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r03b1024s2_d68b2b342a" RESTRICT;
CREATE INDEX "g9c_fd1bc32b3b27_r03b1024s2_a356299821" ON "tpch"."lineitem" USING btree ("l_orderkey", "l_returnflag");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r03b1024s2_a356299821" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r03b1024s2_a356299821" RESTRICT;
CREATE INDEX "g9c_fd1bc32b3b27_r03b1024s2_4b2ee23d70" ON "tpch"."orders" USING btree ("o_orderkey", "o_orderstatus");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r03b1024s2_4b2ee23d70" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r03b1024s2_4b2ee23d70" RESTRICT;
CREATE INDEX "g9c_fd1bc32b3b27_r03b1024s2_b6351c0547" ON "tpch"."lineitem" USING btree ("l_suppkey", "l_shipdate");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r03b1024s2_b6351c0547" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r03b1024s2_b6351c0547" RESTRICT;
CREATE INDEX "g9c_fd1bc32b3b27_r03b1024s2_d3d040f25b" ON "tpch"."lineitem" USING btree ("l_returnflag", "l_linestatus");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r03b1024s2_d3d040f25b" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r03b1024s2_d3d040f25b" RESTRICT;
CREATE INDEX "g9c_fd1bc32b3b27_r03b1024s2_5007cdd031" ON "tpch"."orders" USING btree ("o_custkey", "o_orderdate");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r03b1024s2_5007cdd031" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r03b1024s2_5007cdd031" RESTRICT;
CREATE INDEX "g9c_fd1bc32b3b27_r03b1024s2_eb17e9a7f0" ON "tpch"."lineitem" USING btree ("l_shipmode", "l_shipdate");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r03b1024s2_eb17e9a7f0" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r03b1024s2_eb17e9a7f0" RESTRICT;
CREATE INDEX "g9c_fd1bc32b3b27_r03b1024s2_5d77d0fe48" ON "tpch"."orders" USING btree ("o_orderpriority", "o_orderstatus");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r03b1024s2_5d77d0fe48" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r03b1024s2_5d77d0fe48" RESTRICT;

-- r03b1024s3 single 1024 MiB; one atomic build transaction
CREATE INDEX "g9c_fd1bc32b3b27_r03b1024s3_637db5b0ec" ON "tpch"."orders" USING btree ("o_orderdate");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r03b1024s3_637db5b0ec" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r03b1024s3_637db5b0ec" RESTRICT;
CREATE INDEX "g9c_fd1bc32b3b27_r03b1024s3_9e235190eb" ON "tpch"."orders" USING btree ("o_orderstatus");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r03b1024s3_9e235190eb" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r03b1024s3_9e235190eb" RESTRICT;
CREATE INDEX "g9c_fd1bc32b3b27_r03b1024s3_07a39fda09" ON "tpch"."lineitem" USING btree ("l_shipdate");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r03b1024s3_07a39fda09" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r03b1024s3_07a39fda09" RESTRICT;
CREATE INDEX "g9c_fd1bc32b3b27_r03b1024s3_a828fe6df1" ON "tpch"."orders" USING btree ("o_orderkey");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r03b1024s3_a828fe6df1" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r03b1024s3_a828fe6df1" RESTRICT;
CREATE INDEX "g9c_fd1bc32b3b27_r03b1024s3_b83a3ac03b" ON "tpch"."orders" USING btree ("o_orderpriority");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r03b1024s3_b83a3ac03b" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r03b1024s3_b83a3ac03b" RESTRICT;
CREATE INDEX "g9c_fd1bc32b3b27_r03b1024s3_a2e39e3e09" ON "tpch"."lineitem" USING btree ("l_orderkey");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r03b1024s3_a2e39e3e09" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r03b1024s3_a2e39e3e09" RESTRICT;
CREATE INDEX "g9c_fd1bc32b3b27_r03b1024s3_1b3cca0e6f" ON "tpch"."lineitem" USING btree ("l_shipmode");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r03b1024s3_1b3cca0e6f" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r03b1024s3_1b3cca0e6f" RESTRICT;
CREATE INDEX "g9c_fd1bc32b3b27_r03b1024s3_b9eae9c8d4" ON "tpch"."orders" USING btree ("o_custkey");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r03b1024s3_b9eae9c8d4" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r03b1024s3_b9eae9c8d4" RESTRICT;
CREATE INDEX "g9c_fd1bc32b3b27_r03b1024s3_913f745a9d" ON "tpch"."orders" USING btree ("o_totalprice");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r03b1024s3_913f745a9d" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r03b1024s3_913f745a9d" RESTRICT;
CREATE INDEX "g9c_fd1bc32b3b27_r03b1024s3_0eb51e91a2" ON "tpch"."lineitem" USING btree ("l_returnflag");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r03b1024s3_0eb51e91a2" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r03b1024s3_0eb51e91a2" RESTRICT;
CREATE INDEX "g9c_fd1bc32b3b27_r03b1024s3_57d6470fab" ON "tpch"."orders" USING btree ("o_clerk");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r03b1024s3_57d6470fab" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r03b1024s3_57d6470fab" RESTRICT;

-- r03b1024s4 baseline 1024 MiB; one atomic build transaction

-- r03b500s1 suboptimal 500 MiB; one atomic build transaction
CREATE INDEX "g9c_fd1bc32b3b27_r03b500s1_d68b2b342a" ON "tpch"."orders" USING btree ("o_orderstatus", "o_orderdate");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r03b500s1_d68b2b342a" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r03b500s1_d68b2b342a" RESTRICT;
CREATE INDEX "g9c_fd1bc32b3b27_r03b500s1_26d321fc5d" ON "tpch"."orders" USING btree ("o_orderpriority", "o_orderdate");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r03b500s1_26d321fc5d" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r03b500s1_26d321fc5d" RESTRICT;
CREATE INDEX "g9c_fd1bc32b3b27_r03b500s1_eb17e9a7f0" ON "tpch"."lineitem" USING btree ("l_shipmode", "l_shipdate");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r03b500s1_eb17e9a7f0" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r03b500s1_eb17e9a7f0" RESTRICT;
CREATE INDEX "g9c_fd1bc32b3b27_r03b500s1_5007cdd031" ON "tpch"."orders" USING btree ("o_custkey", "o_orderdate");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r03b500s1_5007cdd031" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r03b500s1_5007cdd031" RESTRICT;
CREATE INDEX "g9c_fd1bc32b3b27_r03b500s1_5d77d0fe48" ON "tpch"."orders" USING btree ("o_orderpriority", "o_orderstatus");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r03b500s1_5d77d0fe48" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r03b500s1_5d77d0fe48" RESTRICT;

-- r03b500s2 advisor 500 MiB; one atomic build transaction
CREATE INDEX "g9c_fd1bc32b3b27_r03b500s2_d68b2b342a" ON "tpch"."orders" USING btree ("o_orderstatus", "o_orderdate");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r03b500s2_d68b2b342a" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r03b500s2_d68b2b342a" RESTRICT;
CREATE INDEX "g9c_fd1bc32b3b27_r03b500s2_a356299821" ON "tpch"."lineitem" USING btree ("l_orderkey", "l_returnflag");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r03b500s2_a356299821" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r03b500s2_a356299821" RESTRICT;
CREATE INDEX "g9c_fd1bc32b3b27_r03b500s2_4b2ee23d70" ON "tpch"."orders" USING btree ("o_orderkey", "o_orderstatus");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r03b500s2_4b2ee23d70" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r03b500s2_4b2ee23d70" RESTRICT;
CREATE INDEX "g9c_fd1bc32b3b27_r03b500s2_d3d040f25b" ON "tpch"."lineitem" USING btree ("l_returnflag", "l_linestatus");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r03b500s2_d3d040f25b" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r03b500s2_d3d040f25b" RESTRICT;

-- r03b500s3 single 500 MiB; one atomic build transaction
CREATE INDEX "g9c_fd1bc32b3b27_r03b500s3_637db5b0ec" ON "tpch"."orders" USING btree ("o_orderdate");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r03b500s3_637db5b0ec" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r03b500s3_637db5b0ec" RESTRICT;
CREATE INDEX "g9c_fd1bc32b3b27_r03b500s3_9e235190eb" ON "tpch"."orders" USING btree ("o_orderstatus");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r03b500s3_9e235190eb" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r03b500s3_9e235190eb" RESTRICT;
CREATE INDEX "g9c_fd1bc32b3b27_r03b500s3_07a39fda09" ON "tpch"."lineitem" USING btree ("l_shipdate");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r03b500s3_07a39fda09" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r03b500s3_07a39fda09" RESTRICT;
CREATE INDEX "g9c_fd1bc32b3b27_r03b500s3_a828fe6df1" ON "tpch"."orders" USING btree ("o_orderkey");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r03b500s3_a828fe6df1" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r03b500s3_a828fe6df1" RESTRICT;
CREATE INDEX "g9c_fd1bc32b3b27_r03b500s3_b83a3ac03b" ON "tpch"."orders" USING btree ("o_orderpriority");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r03b500s3_b83a3ac03b" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r03b500s3_b83a3ac03b" RESTRICT;
CREATE INDEX "g9c_fd1bc32b3b27_r03b500s3_b9eae9c8d4" ON "tpch"."orders" USING btree ("o_custkey");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r03b500s3_b9eae9c8d4" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r03b500s3_b9eae9c8d4" RESTRICT;
CREATE INDEX "g9c_fd1bc32b3b27_r03b500s3_913f745a9d" ON "tpch"."orders" USING btree ("o_totalprice");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r03b500s3_913f745a9d" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r03b500s3_913f745a9d" RESTRICT;
CREATE INDEX "g9c_fd1bc32b3b27_r03b500s3_57d6470fab" ON "tpch"."orders" USING btree ("o_clerk");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r03b500s3_57d6470fab" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r03b500s3_57d6470fab" RESTRICT;

-- r03b500s4 baseline 500 MiB; one atomic build transaction

-- r03b100s1 suboptimal 100 MiB; one atomic build transaction
CREATE INDEX "g9c_fd1bc32b3b27_r03b100s1_d68b2b342a" ON "tpch"."orders" USING btree ("o_orderstatus", "o_orderdate");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r03b100s1_d68b2b342a" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r03b100s1_d68b2b342a" RESTRICT;
CREATE INDEX "g9c_fd1bc32b3b27_r03b100s1_5007cdd031" ON "tpch"."orders" USING btree ("o_custkey", "o_orderdate");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r03b100s1_5007cdd031" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r03b100s1_5007cdd031" RESTRICT;

-- r03b100s2 advisor 100 MiB; one atomic build transaction
CREATE INDEX "g9c_fd1bc32b3b27_r03b100s2_4b2ee23d70" ON "tpch"."orders" USING btree ("o_orderkey", "o_orderstatus");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r03b100s2_4b2ee23d70" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r03b100s2_4b2ee23d70" RESTRICT;
CREATE INDEX "g9c_fd1bc32b3b27_r03b100s2_d68b2b342a" ON "tpch"."orders" USING btree ("o_orderstatus", "o_orderdate");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r03b100s2_d68b2b342a" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r03b100s2_d68b2b342a" RESTRICT;

-- r03b100s3 single 100 MiB; one atomic build transaction
CREATE INDEX "g9c_fd1bc32b3b27_r03b100s3_637db5b0ec" ON "tpch"."orders" USING btree ("o_orderdate");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r03b100s3_637db5b0ec" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r03b100s3_637db5b0ec" RESTRICT;
CREATE INDEX "g9c_fd1bc32b3b27_r03b100s3_9e235190eb" ON "tpch"."orders" USING btree ("o_orderstatus");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r03b100s3_9e235190eb" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r03b100s3_9e235190eb" RESTRICT;

-- r03b100s4 baseline 100 MiB; one atomic build transaction

-- r04b100s1 advisor 100 MiB; one atomic build transaction
CREATE INDEX "g9c_fd1bc32b3b27_r04b100s1_4b2ee23d70" ON "tpch"."orders" USING btree ("o_orderkey", "o_orderstatus");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r04b100s1_4b2ee23d70" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r04b100s1_4b2ee23d70" RESTRICT;
CREATE INDEX "g9c_fd1bc32b3b27_r04b100s1_d68b2b342a" ON "tpch"."orders" USING btree ("o_orderstatus", "o_orderdate");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r04b100s1_d68b2b342a" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r04b100s1_d68b2b342a" RESTRICT;

-- r04b100s2 baseline 100 MiB; one atomic build transaction

-- r04b100s3 suboptimal 100 MiB; one atomic build transaction
CREATE INDEX "g9c_fd1bc32b3b27_r04b100s3_d68b2b342a" ON "tpch"."orders" USING btree ("o_orderstatus", "o_orderdate");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r04b100s3_d68b2b342a" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r04b100s3_d68b2b342a" RESTRICT;
CREATE INDEX "g9c_fd1bc32b3b27_r04b100s3_5007cdd031" ON "tpch"."orders" USING btree ("o_custkey", "o_orderdate");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r04b100s3_5007cdd031" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r04b100s3_5007cdd031" RESTRICT;

-- r04b100s4 single 100 MiB; one atomic build transaction
CREATE INDEX "g9c_fd1bc32b3b27_r04b100s4_637db5b0ec" ON "tpch"."orders" USING btree ("o_orderdate");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r04b100s4_637db5b0ec" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r04b100s4_637db5b0ec" RESTRICT;
CREATE INDEX "g9c_fd1bc32b3b27_r04b100s4_9e235190eb" ON "tpch"."orders" USING btree ("o_orderstatus");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r04b100s4_9e235190eb" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r04b100s4_9e235190eb" RESTRICT;

-- r04b500s1 advisor 500 MiB; one atomic build transaction
CREATE INDEX "g9c_fd1bc32b3b27_r04b500s1_d68b2b342a" ON "tpch"."orders" USING btree ("o_orderstatus", "o_orderdate");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r04b500s1_d68b2b342a" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r04b500s1_d68b2b342a" RESTRICT;
CREATE INDEX "g9c_fd1bc32b3b27_r04b500s1_a356299821" ON "tpch"."lineitem" USING btree ("l_orderkey", "l_returnflag");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r04b500s1_a356299821" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r04b500s1_a356299821" RESTRICT;
CREATE INDEX "g9c_fd1bc32b3b27_r04b500s1_4b2ee23d70" ON "tpch"."orders" USING btree ("o_orderkey", "o_orderstatus");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r04b500s1_4b2ee23d70" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r04b500s1_4b2ee23d70" RESTRICT;
CREATE INDEX "g9c_fd1bc32b3b27_r04b500s1_d3d040f25b" ON "tpch"."lineitem" USING btree ("l_returnflag", "l_linestatus");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r04b500s1_d3d040f25b" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r04b500s1_d3d040f25b" RESTRICT;

-- r04b500s2 baseline 500 MiB; one atomic build transaction

-- r04b500s3 suboptimal 500 MiB; one atomic build transaction
CREATE INDEX "g9c_fd1bc32b3b27_r04b500s3_d68b2b342a" ON "tpch"."orders" USING btree ("o_orderstatus", "o_orderdate");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r04b500s3_d68b2b342a" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r04b500s3_d68b2b342a" RESTRICT;
CREATE INDEX "g9c_fd1bc32b3b27_r04b500s3_26d321fc5d" ON "tpch"."orders" USING btree ("o_orderpriority", "o_orderdate");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r04b500s3_26d321fc5d" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r04b500s3_26d321fc5d" RESTRICT;
CREATE INDEX "g9c_fd1bc32b3b27_r04b500s3_eb17e9a7f0" ON "tpch"."lineitem" USING btree ("l_shipmode", "l_shipdate");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r04b500s3_eb17e9a7f0" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r04b500s3_eb17e9a7f0" RESTRICT;
CREATE INDEX "g9c_fd1bc32b3b27_r04b500s3_5007cdd031" ON "tpch"."orders" USING btree ("o_custkey", "o_orderdate");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r04b500s3_5007cdd031" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r04b500s3_5007cdd031" RESTRICT;
CREATE INDEX "g9c_fd1bc32b3b27_r04b500s3_5d77d0fe48" ON "tpch"."orders" USING btree ("o_orderpriority", "o_orderstatus");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r04b500s3_5d77d0fe48" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r04b500s3_5d77d0fe48" RESTRICT;

-- r04b500s4 single 500 MiB; one atomic build transaction
CREATE INDEX "g9c_fd1bc32b3b27_r04b500s4_637db5b0ec" ON "tpch"."orders" USING btree ("o_orderdate");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r04b500s4_637db5b0ec" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r04b500s4_637db5b0ec" RESTRICT;
CREATE INDEX "g9c_fd1bc32b3b27_r04b500s4_9e235190eb" ON "tpch"."orders" USING btree ("o_orderstatus");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r04b500s4_9e235190eb" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r04b500s4_9e235190eb" RESTRICT;
CREATE INDEX "g9c_fd1bc32b3b27_r04b500s4_07a39fda09" ON "tpch"."lineitem" USING btree ("l_shipdate");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r04b500s4_07a39fda09" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r04b500s4_07a39fda09" RESTRICT;
CREATE INDEX "g9c_fd1bc32b3b27_r04b500s4_a828fe6df1" ON "tpch"."orders" USING btree ("o_orderkey");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r04b500s4_a828fe6df1" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r04b500s4_a828fe6df1" RESTRICT;
CREATE INDEX "g9c_fd1bc32b3b27_r04b500s4_b83a3ac03b" ON "tpch"."orders" USING btree ("o_orderpriority");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r04b500s4_b83a3ac03b" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r04b500s4_b83a3ac03b" RESTRICT;
CREATE INDEX "g9c_fd1bc32b3b27_r04b500s4_b9eae9c8d4" ON "tpch"."orders" USING btree ("o_custkey");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r04b500s4_b9eae9c8d4" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r04b500s4_b9eae9c8d4" RESTRICT;
CREATE INDEX "g9c_fd1bc32b3b27_r04b500s4_913f745a9d" ON "tpch"."orders" USING btree ("o_totalprice");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r04b500s4_913f745a9d" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r04b500s4_913f745a9d" RESTRICT;
CREATE INDEX "g9c_fd1bc32b3b27_r04b500s4_57d6470fab" ON "tpch"."orders" USING btree ("o_clerk");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r04b500s4_57d6470fab" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r04b500s4_57d6470fab" RESTRICT;

-- r04b1024s1 advisor 1024 MiB; one atomic build transaction
CREATE INDEX "g9c_fd1bc32b3b27_r04b1024s1_d68b2b342a" ON "tpch"."orders" USING btree ("o_orderstatus", "o_orderdate");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r04b1024s1_d68b2b342a" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r04b1024s1_d68b2b342a" RESTRICT;
CREATE INDEX "g9c_fd1bc32b3b27_r04b1024s1_a356299821" ON "tpch"."lineitem" USING btree ("l_orderkey", "l_returnflag");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r04b1024s1_a356299821" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r04b1024s1_a356299821" RESTRICT;
CREATE INDEX "g9c_fd1bc32b3b27_r04b1024s1_4b2ee23d70" ON "tpch"."orders" USING btree ("o_orderkey", "o_orderstatus");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r04b1024s1_4b2ee23d70" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r04b1024s1_4b2ee23d70" RESTRICT;
CREATE INDEX "g9c_fd1bc32b3b27_r04b1024s1_b6351c0547" ON "tpch"."lineitem" USING btree ("l_suppkey", "l_shipdate");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r04b1024s1_b6351c0547" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r04b1024s1_b6351c0547" RESTRICT;
CREATE INDEX "g9c_fd1bc32b3b27_r04b1024s1_d3d040f25b" ON "tpch"."lineitem" USING btree ("l_returnflag", "l_linestatus");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r04b1024s1_d3d040f25b" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r04b1024s1_d3d040f25b" RESTRICT;
CREATE INDEX "g9c_fd1bc32b3b27_r04b1024s1_5007cdd031" ON "tpch"."orders" USING btree ("o_custkey", "o_orderdate");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r04b1024s1_5007cdd031" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r04b1024s1_5007cdd031" RESTRICT;
CREATE INDEX "g9c_fd1bc32b3b27_r04b1024s1_eb17e9a7f0" ON "tpch"."lineitem" USING btree ("l_shipmode", "l_shipdate");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r04b1024s1_eb17e9a7f0" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r04b1024s1_eb17e9a7f0" RESTRICT;
CREATE INDEX "g9c_fd1bc32b3b27_r04b1024s1_5d77d0fe48" ON "tpch"."orders" USING btree ("o_orderpriority", "o_orderstatus");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r04b1024s1_5d77d0fe48" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r04b1024s1_5d77d0fe48" RESTRICT;

-- r04b1024s2 baseline 1024 MiB; one atomic build transaction

-- r04b1024s3 suboptimal 1024 MiB; one atomic build transaction
CREATE INDEX "g9c_fd1bc32b3b27_r04b1024s3_d68b2b342a" ON "tpch"."orders" USING btree ("o_orderstatus", "o_orderdate");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r04b1024s3_d68b2b342a" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r04b1024s3_d68b2b342a" RESTRICT;
CREATE INDEX "g9c_fd1bc32b3b27_r04b1024s3_26d321fc5d" ON "tpch"."orders" USING btree ("o_orderpriority", "o_orderdate");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r04b1024s3_26d321fc5d" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r04b1024s3_26d321fc5d" RESTRICT;
CREATE INDEX "g9c_fd1bc32b3b27_r04b1024s3_eb17e9a7f0" ON "tpch"."lineitem" USING btree ("l_shipmode", "l_shipdate");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r04b1024s3_eb17e9a7f0" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r04b1024s3_eb17e9a7f0" RESTRICT;
CREATE INDEX "g9c_fd1bc32b3b27_r04b1024s3_5007cdd031" ON "tpch"."orders" USING btree ("o_custkey", "o_orderdate");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r04b1024s3_5007cdd031" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r04b1024s3_5007cdd031" RESTRICT;
CREATE INDEX "g9c_fd1bc32b3b27_r04b1024s3_5d77d0fe48" ON "tpch"."orders" USING btree ("o_orderpriority", "o_orderstatus");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r04b1024s3_5d77d0fe48" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r04b1024s3_5d77d0fe48" RESTRICT;
CREATE INDEX "g9c_fd1bc32b3b27_r04b1024s3_4e1a1ae80d" ON "tpch"."lineitem" USING btree ("l_shipdate", "l_orderkey");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r04b1024s3_4e1a1ae80d" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r04b1024s3_4e1a1ae80d" RESTRICT;
CREATE INDEX "g9c_fd1bc32b3b27_r04b1024s3_9914763ac6" ON "tpch"."lineitem" USING btree ("l_shipmode", "l_orderkey");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r04b1024s3_9914763ac6" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r04b1024s3_9914763ac6" RESTRICT;
CREATE INDEX "g9c_fd1bc32b3b27_r04b1024s3_1b28205a0e" ON "tpch"."orders" USING btree ("o_totalprice", "o_orderdate");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r04b1024s3_1b28205a0e" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r04b1024s3_1b28205a0e" RESTRICT;

-- r04b1024s4 single 1024 MiB; one atomic build transaction
CREATE INDEX "g9c_fd1bc32b3b27_r04b1024s4_637db5b0ec" ON "tpch"."orders" USING btree ("o_orderdate");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r04b1024s4_637db5b0ec" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r04b1024s4_637db5b0ec" RESTRICT;
CREATE INDEX "g9c_fd1bc32b3b27_r04b1024s4_9e235190eb" ON "tpch"."orders" USING btree ("o_orderstatus");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r04b1024s4_9e235190eb" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r04b1024s4_9e235190eb" RESTRICT;
CREATE INDEX "g9c_fd1bc32b3b27_r04b1024s4_07a39fda09" ON "tpch"."lineitem" USING btree ("l_shipdate");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r04b1024s4_07a39fda09" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r04b1024s4_07a39fda09" RESTRICT;
CREATE INDEX "g9c_fd1bc32b3b27_r04b1024s4_a828fe6df1" ON "tpch"."orders" USING btree ("o_orderkey");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r04b1024s4_a828fe6df1" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r04b1024s4_a828fe6df1" RESTRICT;
CREATE INDEX "g9c_fd1bc32b3b27_r04b1024s4_b83a3ac03b" ON "tpch"."orders" USING btree ("o_orderpriority");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r04b1024s4_b83a3ac03b" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r04b1024s4_b83a3ac03b" RESTRICT;
CREATE INDEX "g9c_fd1bc32b3b27_r04b1024s4_a2e39e3e09" ON "tpch"."lineitem" USING btree ("l_orderkey");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r04b1024s4_a2e39e3e09" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r04b1024s4_a2e39e3e09" RESTRICT;
CREATE INDEX "g9c_fd1bc32b3b27_r04b1024s4_1b3cca0e6f" ON "tpch"."lineitem" USING btree ("l_shipmode");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r04b1024s4_1b3cca0e6f" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r04b1024s4_1b3cca0e6f" RESTRICT;
CREATE INDEX "g9c_fd1bc32b3b27_r04b1024s4_b9eae9c8d4" ON "tpch"."orders" USING btree ("o_custkey");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r04b1024s4_b9eae9c8d4" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r04b1024s4_b9eae9c8d4" RESTRICT;
CREATE INDEX "g9c_fd1bc32b3b27_r04b1024s4_913f745a9d" ON "tpch"."orders" USING btree ("o_totalprice");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r04b1024s4_913f745a9d" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r04b1024s4_913f745a9d" RESTRICT;
CREATE INDEX "g9c_fd1bc32b3b27_r04b1024s4_0eb51e91a2" ON "tpch"."lineitem" USING btree ("l_returnflag");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r04b1024s4_0eb51e91a2" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r04b1024s4_0eb51e91a2" RESTRICT;
CREATE INDEX "g9c_fd1bc32b3b27_r04b1024s4_57d6470fab" ON "tpch"."orders" USING btree ("o_clerk");
COMMENT ON INDEX "tpch"."g9c_fd1bc32b3b27_r04b1024s4_57d6470fab" IS 'g9c:v1:fd1bc32b3b27:1b0fb48da5dc4c178aa6138cfe9f5a3c';
-- later cleanup ONLY after catalog identity/ownership verification: DROP INDEX "tpch"."g9c_fd1bc32b3b27_r04b1024s4_57d6470fab" RESTRICT;
