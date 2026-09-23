-- dim_branch and dim_product: small type 1 dimensions.
--
-- Type 1 means a changed attribute is overwritten and no history is kept. That
-- is right for a branch's display name. It would be wrong for a customer's
-- segment, which is why dim_customer is type 2.
--
-- DuckLake has no sequences and no primary keys, so the load assigns surrogate
-- keys itself: the current maximum plus a row number. Kimball puts key
-- assignment in the ETL anyway; here there is no alternative.

CREATE TABLE IF NOT EXISTS dim_branch (
    branch_sk BIGINT NOT NULL, branch_id VARCHAR NOT NULL, branch_name VARCHAR,
    city VARCHAR, region VARCHAR, etl_batch_id VARCHAR NOT NULL);

MERGE INTO dim_branch d USING stg_branches s ON d.branch_id = s.branch_id
WHEN MATCHED AND (d.branch_name IS DISTINCT FROM s.branch_name
               OR d.city IS DISTINCT FROM s.city OR d.region IS DISTINCT FROM s.region)
    THEN UPDATE SET branch_name = s.branch_name, city = s.city, region = s.region,
                    etl_batch_id = getvariable('batch_id');

INSERT INTO dim_branch
SELECT (SELECT coalesce(max(branch_sk), 0) FROM dim_branch)
           + row_number() OVER (ORDER BY s.branch_id),
       s.branch_id, s.branch_name, s.city, s.region, getvariable('batch_id')
FROM stg_branches s
WHERE NOT EXISTS (SELECT 1 FROM dim_branch d WHERE d.branch_id = s.branch_id);

CREATE TABLE IF NOT EXISTS dim_product (
    product_sk BIGINT NOT NULL, product_code VARCHAR NOT NULL, product_name VARCHAR,
    product_category VARCHAR, etl_batch_id VARCHAR NOT NULL);

MERGE INTO dim_product d USING stg_products s ON d.product_code = s.product_code
WHEN MATCHED AND (d.product_name IS DISTINCT FROM s.product_name
               OR d.product_category IS DISTINCT FROM s.product_category)
    THEN UPDATE SET product_name = s.product_name, product_category = s.product_category,
                    etl_batch_id = getvariable('batch_id');

INSERT INTO dim_product
SELECT (SELECT coalesce(max(product_sk), 0) FROM dim_product)
           + row_number() OVER (ORDER BY s.product_code),
       s.product_code, s.product_name, s.product_category, getvariable('batch_id')
FROM stg_products s
WHERE NOT EXISTS (SELECT 1 FROM dim_product d WHERE d.product_code = s.product_code);
