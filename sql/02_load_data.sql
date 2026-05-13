-- ==============================================
-- 数据导入
--
-- 方式一（推荐）：使用 Python 导入脚本
--   python python/import_to_mysql.py
--
-- 方式二：手动 docker cp + LOAD DATA
--   docker cp data/users.csv mysql84:/tmp/
--   docker cp output/cleaned_user_summary.csv mysql84:/tmp/
--   docker exec mysql84 mysql -h 127.0.0.1 -u root -p --local-infile=1 ecommerce_rfm < 02_load_data.sql
--   注意：需要先 SET GLOBAL local_infile = 1; 并添加 --local-infile=1 标志
-- ==============================================

-- ==============================================
-- 1. 用户维度
--    CSV: user_id, name, email, gender, city, signup_date
--    表:  user_id, name, email, gender, city, signup_date  ✓
-- ==============================================
LOAD DATA LOCAL INFILE '/tmp/users.csv'
INTO TABLE dim_user
FIELDS TERMINATED BY ',' ENCLOSED BY '"'
LINES TERMINATED BY '\n' IGNORE 1 ROWS
(user_id, name, email, gender, city, signup_date);

-- ==============================================
-- 2. 商品维度
--    CSV: product_id, product_name, category, brand, price, rating
--    表:  product_id, product_name, category, brand, price, rating  ✓
-- ==============================================
LOAD DATA LOCAL INFILE '/tmp/products.csv'
INTO TABLE dim_product
FIELDS TERMINATED BY ',' ENCLOSED BY '"'
LINES TERMINATED BY '\n' IGNORE 1 ROWS
(product_id, product_name, category, brand, price, rating);

-- ==============================================
-- 3. 订单维度（原始全量）
--    CSV: order_id, user_id, order_date, order_status, total_amount
--    表:  order_id, user_id, order_date, order_status, total_amount  ✓
-- ==============================================
LOAD DATA LOCAL INFILE '/tmp/orders.csv'
INTO TABLE dim_order
FIELDS TERMINATED BY ',' ENCLOSED BY '"'
LINES TERMINATED BY '\n' IGNORE 1 ROWS
(order_id, user_id, order_date, order_status, total_amount);

-- ==============================================
-- 4. 订单明细（原始全量）
--    CSV: order_item_id, order_id, product_id, user_id, quantity, item_price, item_total
--    表:  order_item_id, order_id, product_id, user_id, quantity, item_price, item_total  ✓
-- ==============================================
LOAD DATA LOCAL INFILE '/tmp/order_items.csv'
INTO TABLE order_items
FIELDS TERMINATED BY ',' ENCLOSED BY '"'
LINES TERMINATED BY '\n' IGNORE 1 ROWS
(order_item_id, order_id, product_id, user_id, quantity, item_price, item_total);

-- ==============================================
-- 5. 订单明细事实表（清洗后）
--    CSV: order_id, user_id, order_date, order_status, total_amount, days_since_order
--    表:  detail_id(AUTO), user_id, order_id, order_date, order_status, total_amount
--    映射: CSV(order_id→表.order_id, user_id→表.user_id, ...)  ✓
--    days_since_order 用 @ 变量接收后丢弃（表无此列，仅 dws_user_rfm 需要）
-- ==============================================
LOAD DATA LOCAL INFILE '/tmp/cleaned_orders.csv'
INTO TABLE dwd_user_order_detail
FIELDS TERMINATED BY ',' ENCLOSED BY '"'
LINES TERMINATED BY '\n' IGNORE 1 ROWS
(order_id, user_id, order_date, order_status, total_amount, @discard);

-- ==============================================
-- 6. RFM 用户宽表（清洗后）
--    CSV: user_id, order_count, total_amount, days_since_order,
--         r_score, f_score, m_score, is_vip,
--         m_p25, m_p75, vip_threshold, rfm_combined, segment_19, segment_operation
--    表:  user_id, order_count, total_amount, days_since_order,
--         r_score, f_score, m_score, m_p25, m_p75, vip_threshold,
--         is_vip, rfm_combined, segment_19, segment_operation
--    注意: CSV 中 is_vip 在 m_score 之后, m_p25 之前;
--          表中 m_p25 在 m_score 之后, is_vip 在 vip_threshold 之后
--    映射需按 CSV 实际列序指定
-- ==============================================
LOAD DATA LOCAL INFILE '/tmp/cleaned_user_summary.csv'
INTO TABLE dws_user_rfm
FIELDS TERMINATED BY ',' ENCLOSED BY '"'
LINES TERMINATED BY '\n' IGNORE 1 ROWS
(user_id, order_count, total_amount, days_since_order,
 r_score, f_score, m_score, is_vip,
 m_p25, m_p75, vip_threshold, rfm_combined, segment_19, segment_operation);
