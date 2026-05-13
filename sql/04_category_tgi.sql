-- ==============================================
-- 品类 & 品牌 TGI 偏好分析
-- TGI = (客群在品类的消费占比) / (全体在该品类的消费占比) × 100
-- TGI > 120: 显著偏好 | 80-120: 正常 | < 80: 显著回避
-- ==============================================

-- ==============================================
-- 1. 各运营组 × 品类 TGI（完整明细）
-- ==============================================
WITH
all_category AS (
    SELECT p.category,
           SUM(oi.item_total) as total_amount,
           SUM(oi.item_total) * 100.0 / SUM(SUM(oi.item_total)) OVER () as amount_pct
    FROM order_items oi JOIN dim_product p ON oi.product_id = p.product_id
    GROUP BY p.category
),
segment_category AS (
    SELECT r.segment_operation, p.category,
           SUM(oi.item_total) as total_amount,
           COUNT(DISTINCT oi.user_id) as user_count
    FROM order_items oi JOIN dim_product p ON oi.product_id = p.product_id
    JOIN dws_user_rfm r ON oi.user_id = r.user_id
    WHERE r.segment_operation IS NOT NULL
    GROUP BY r.segment_operation, p.category
),
segment_total AS (
    SELECT segment_operation, SUM(total_amount) as st FROM segment_category GROUP BY segment_operation
)
SELECT sc.segment_operation, sc.category, sc.total_amount,
       ROUND(sc.total_amount * 100.0 / st.st, 1) as segment_pct,
       ROUND(ac.amount_pct, 1) as overall_pct,
       ROUND((sc.total_amount * 100.0 / st.st) / ac.amount_pct * 100, 0) as TGI,
       sc.user_count,
       CASE
           WHEN (sc.total_amount * 100.0 / st.st) / ac.amount_pct * 100 >= 120 THEN '显著偏好'
           WHEN (sc.total_amount * 100.0 / st.st) / ac.amount_pct * 100 <= 80 THEN '显著回避'
           ELSE '正常'
       END as preference_label
FROM segment_category sc
JOIN segment_total st ON sc.segment_operation = st.segment_operation
JOIN all_category ac ON sc.category = ac.category
ORDER BY sc.segment_operation, TGI DESC;


-- ==============================================
-- 2. 每个运营组 TOP3 偏好品类（按 TGI）
-- ==============================================
WITH
all_category AS (
    SELECT p.category, SUM(oi.item_total) as total_amount,
           SUM(oi.item_total) * 100.0 / SUM(SUM(oi.item_total)) OVER () as amount_pct
    FROM order_items oi JOIN dim_product p ON oi.product_id = p.product_id GROUP BY p.category
),
segment_category AS (
    SELECT r.segment_operation, p.category, SUM(oi.item_total) as total_amount
    FROM order_items oi JOIN dim_product p ON oi.product_id = p.product_id
    JOIN dws_user_rfm r ON oi.user_id = r.user_id
    WHERE r.segment_operation IS NOT NULL GROUP BY r.segment_operation, p.category
),
segment_total AS (
    SELECT segment_operation, SUM(total_amount) as st FROM segment_category GROUP BY segment_operation
),
tgi_ranked AS (
    SELECT sc.segment_operation, sc.category, sc.total_amount,
           ROUND((sc.total_amount * 100.0 / st.st) / ac.amount_pct * 100, 0) as TGI,
           ROW_NUMBER() OVER (PARTITION BY sc.segment_operation ORDER BY
               (sc.total_amount * 100.0 / st.st) / ac.amount_pct * 100 DESC) as rn
    FROM segment_category sc
    JOIN segment_total st ON sc.segment_operation = st.segment_operation
    JOIN all_category ac ON sc.category = ac.category
)
SELECT segment_operation, category, total_amount, TGI, rn as ranking
FROM tgi_ranked WHERE rn <= 3 ORDER BY segment_operation, rn;


-- ==============================================
-- 3. 每个运营组 TOP5 品牌偏好（按 TGI）
-- ==============================================
WITH
all_brand AS (
    SELECT p.brand, SUM(oi.item_total) as total_amount,
           SUM(oi.item_total) * 100.0 / SUM(SUM(oi.item_total)) OVER () as amount_pct
    FROM order_items oi JOIN dim_product p ON oi.product_id = p.product_id GROUP BY p.brand
),
segment_brand AS (
    SELECT r.segment_operation, p.brand, SUM(oi.item_total) as total_amount
    FROM order_items oi JOIN dim_product p ON oi.product_id = p.product_id
    JOIN dws_user_rfm r ON oi.user_id = r.user_id
    WHERE r.segment_operation IS NOT NULL GROUP BY r.segment_operation, p.brand
),
segment_total AS (
    SELECT segment_operation, SUM(total_amount) as st FROM segment_brand GROUP BY segment_operation
),
brand_tgi AS (
    SELECT sb.segment_operation, sb.brand, sb.total_amount,
           ROUND((sb.total_amount * 100.0 / st.st) / ab.amount_pct * 100, 0) as TGI,
           ROW_NUMBER() OVER (PARTITION BY sb.segment_operation ORDER BY
               (sb.total_amount * 100.0 / st.st) / ab.amount_pct * 100 DESC) as rn
    FROM segment_brand sb
    JOIN segment_total st ON sb.segment_operation = st.segment_operation
    JOIN all_brand ab ON sb.brand = ab.brand
)
SELECT segment_operation, brand, total_amount, TGI, rn as ranking
FROM brand_tgi WHERE rn <= 5 ORDER BY segment_operation, rn;


-- ==============================================
-- 4. TGI 热力图（运营组 × 品类）
-- ==============================================
WITH
all_category AS (
    SELECT p.category,
           SUM(oi.item_total) * 100.0 / SUM(SUM(oi.item_total)) OVER () as amount_pct
    FROM order_items oi JOIN dim_product p ON oi.product_id = p.product_id GROUP BY p.category
),
segment_category AS (
    SELECT r.segment_operation, p.category, SUM(oi.item_total) as total_amount
    FROM order_items oi JOIN dim_product p ON oi.product_id = p.product_id
    JOIN dws_user_rfm r ON oi.user_id = r.user_id
    WHERE r.segment_operation IS NOT NULL GROUP BY r.segment_operation, p.category
),
segment_total AS (
    SELECT segment_operation, SUM(total_amount) as st FROM segment_category GROUP BY segment_operation
)
SELECT sc.segment_operation, sc.category,
       ROUND((sc.total_amount * 100.0 / st.st) / ac.amount_pct * 100, 0) as TGI,
       CASE
           WHEN (sc.total_amount * 100.0 / st.st) / ac.amount_pct * 100 >= 130 THEN '★★★'
           WHEN (sc.total_amount * 100.0 / st.st) / ac.amount_pct * 100 >= 120 THEN '★★'
           WHEN (sc.total_amount * 100.0 / st.st) / ac.amount_pct * 100 >= 110 THEN '★'
           WHEN (sc.total_amount * 100.0 / st.st) / ac.amount_pct * 100 <= 70 THEN '▽▽'
           WHEN (sc.total_amount * 100.0 / st.st) / ac.amount_pct * 100 <= 80 THEN '▽'
           ELSE ''
       END as highlight
FROM segment_category sc
JOIN segment_total st ON sc.segment_operation = st.segment_operation
JOIN all_category ac ON sc.category = ac.category
ORDER BY sc.segment_operation, TGI DESC;


-- ==============================================
-- 5. 品类交叉购买矩阵
-- ==============================================
WITH user_categories AS (
    SELECT DISTINCT oi.user_id, p.category
    FROM order_items oi JOIN dim_product p ON oi.product_id = p.product_id
    JOIN dws_user_rfm r ON oi.user_id = r.user_id
    WHERE r.segment_operation IS NOT NULL
),
category_pairs AS (
    SELECT uc1.category as category_a, uc2.category as category_b,
           COUNT(DISTINCT uc1.user_id) as shared_users
    FROM user_categories uc1
    JOIN user_categories uc2 ON uc1.user_id = uc2.user_id AND uc1.category < uc2.category
    GROUP BY uc1.category, uc2.category
)
SELECT category_a, category_b, shared_users,
       shared_users * 100.0 / (SELECT COUNT(DISTINCT user_id) FROM user_categories) as overlap_pct
FROM category_pairs ORDER BY shared_users DESC LIMIT 50;


-- ==============================================
-- 汇总表
-- ==============================================
DROP TABLE IF EXISTS dws_customer_category_pref;
CREATE TABLE dws_customer_category_pref AS
WITH
all_category AS (
    SELECT p.category,
           SUM(oi.item_total) * 100.0 / SUM(SUM(oi.item_total)) OVER () as amount_pct
    FROM order_items oi JOIN dim_product p ON oi.product_id = p.product_id GROUP BY p.category
),
all_brand AS (
    SELECT p.brand,
           SUM(oi.item_total) * 100.0 / SUM(SUM(oi.item_total)) OVER () as amount_pct
    FROM order_items oi JOIN dim_product p ON oi.product_id = p.product_id GROUP BY p.brand
),
segment_stats AS (
    SELECT r.segment_operation,
           COUNT(DISTINCT oi.order_id) as total_orders,
           SUM(oi.item_total) as total_amount,
           SUM(oi.quantity) as total_quantity,
           AVG(oi.item_price) as avg_unit_price
    FROM order_items oi JOIN dws_user_rfm r ON oi.user_id = r.user_id
    WHERE r.segment_operation IS NOT NULL GROUP BY r.segment_operation
),
segment_total AS (
    SELECT segment_operation, SUM(oi.item_total) as st
    FROM order_items oi JOIN dws_user_rfm r ON oi.user_id = r.user_id
    WHERE r.segment_operation IS NOT NULL GROUP BY r.segment_operation
),
top_categories_tgi AS (
    SELECT r.segment_operation, p.category,
           SUM(oi.item_total) as category_amount,
           ROUND((SUM(oi.item_total) * 100.0 / MAX(st.st)) / MAX(ac.amount_pct) * 100, 0) as category_tgi,
           ROW_NUMBER() OVER (PARTITION BY r.segment_operation ORDER BY
               (SUM(oi.item_total) * 100.0 / MAX(st.st)) / MAX(ac.amount_pct) * 100 DESC) as cat_rank
    FROM order_items oi JOIN dim_product p ON oi.product_id = p.product_id
    JOIN dws_user_rfm r ON oi.user_id = r.user_id
    JOIN segment_total st ON r.segment_operation = st.segment_operation
    JOIN all_category ac ON p.category = ac.category
    WHERE r.segment_operation IS NOT NULL
    GROUP BY r.segment_operation, p.category
),
top_brands_tgi AS (
    SELECT r.segment_operation, p.brand,
           SUM(oi.item_total) as brand_amount,
           ROUND((SUM(oi.item_total) * 100.0 / MAX(st.st)) / MAX(ab.amount_pct) * 100, 0) as brand_tgi,
           ROW_NUMBER() OVER (PARTITION BY r.segment_operation ORDER BY
               (SUM(oi.item_total) * 100.0 / MAX(st.st)) / MAX(ab.amount_pct) * 100 DESC) as brand_rank
    FROM order_items oi JOIN dim_product p ON oi.product_id = p.product_id
    JOIN dws_user_rfm r ON oi.user_id = r.user_id
    JOIN segment_total st ON r.segment_operation = st.segment_operation
    JOIN all_brand ab ON p.brand = ab.brand
    WHERE r.segment_operation IS NOT NULL
    GROUP BY r.segment_operation, p.brand
)
SELECT s.segment_operation, s.total_orders, s.total_amount,
       s.total_quantity, s.avg_unit_price,
       tc1.category as top1_category, tc1.category_tgi as top1_tgi,
       tc2.category as top2_category, tc2.category_tgi as top2_tgi,
       tc3.category as top3_category, tc3.category_tgi as top3_tgi,
       tb1.brand as top1_brand, tb1.brand_tgi as top1_brand_tgi,
       tb2.brand as top2_brand, tb2.brand_tgi as top2_brand_tgi,
       tb3.brand as top3_brand, tb3.brand_tgi as top3_brand_tgi
FROM segment_stats s
LEFT JOIN top_categories_tgi tc1 ON s.segment_operation = tc1.segment_operation AND tc1.cat_rank = 1
LEFT JOIN top_categories_tgi tc2 ON s.segment_operation = tc2.segment_operation AND tc2.cat_rank = 2
LEFT JOIN top_categories_tgi tc3 ON s.segment_operation = tc3.segment_operation AND tc3.cat_rank = 3
LEFT JOIN top_brands_tgi tb1 ON s.segment_operation = tb1.segment_operation AND tb1.brand_rank = 1
LEFT JOIN top_brands_tgi tb2 ON s.segment_operation = tb2.segment_operation AND tb2.brand_rank = 2
LEFT JOIN top_brands_tgi tb3 ON s.segment_operation = tb3.segment_operation AND tb3.brand_rank = 3
ORDER BY s.total_amount DESC;

SELECT * FROM dws_customer_category_pref;
