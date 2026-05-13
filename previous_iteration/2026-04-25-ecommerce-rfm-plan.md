# 电商用户价值分析（RFM + 商品偏好）实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 完成电商用户RFM分群分析 + 商品偏好分析，输出Power BI可视化仪表板

**Architecture:**

- 数据链路：CSV → Python清洗 → MySQL数据仓库 → SQL分析 → Power BI可视化
- 分析核心：8大RFM客群 + 各客群商品品类偏好
- 交付物：清洗脚本、SQL查询文件、Power BI仪表板、运营策略文档

**Tech Stack:** Python (Pandas) / MySQL (Docker) / Power BI Desktop / SQL

---

## 文件结构

```
ecommerce/
├── data/                          # 原始数据
│   ├── users.csv
│   ├── orders.csv
│   ├── order_items.csv
│   └── products.csv
├── cleaned_data/                  # 清洗后数据（输出）
│   └── cleaned_*.csv
├── sql/                           # SQL脚本
│   ├── 01_create_tables.sql        # 建表
│   ├── 02_load_data.sql           # 导入数据
│   ├── 03_rfm_calculation.sql     # RFM计算
│   └── 04_category_preference.sql # 商品偏好分析
├── python/                        # Python脚本
│   └── data_cleaning.py           # 数据清洗脚本
├── powerbi/                       # Power BI文件
│   └── ecommerce_dashboard.pbix
├── docs/
│   ├── superpowers/specs/
│   │   └── 2026-04-25-ecommerce-rfm-design.md
│   └── superpowers/plans/
│       └── 2026-04-25-ecommerce-rfm-plan.md
└── operations/                    # 运营策略文档
    └── rfm_strategy.md
```

---

## 实施阶段

### 阶段一：Python数据清洗

### 阶段二：MySQL数据仓库搭建

### 阶段三：RFM分群计算（SQL）

### 阶段四：商品偏好分析（SQL）

### 阶段五：Power BI可视化

### 阶段六：运营策略文档

---

## Task 1: Python数据清洗脚本

**Files:**

- Create: `python/data_cleaning.py`

**Goal:** 读取原始CSV，清洗数据质量问题，输出可分析的干净数据集

---

- [ ] **Step 1: 创建Python脚本框架**

Create: `python/data_cleaning.py`

```python
"""
电商数据清洗脚本
功能：
1. 读取原始CSV
2. 数据质量检查
3. 清洗异常值
4. 按业务规则过滤
5. 合并输出
"""

import pandas as pd
import os
from datetime import datetime

# 配置路径
DATA_PATH = "data/"
OUTPUT_PATH = "cleaned_data/"
ANALYSIS_DATE = "2025-11-15"  # 分析截止日期

def load_data():
    """加载原始数据"""
    users = pd.read_csv(f"{DATA_PATH}users.csv")
    orders = pd.read_csv(f"{DATA_PATH}orders.csv")
    order_items = pd.read_csv(f"{DATA_PATH}order_items.csv")
    products = pd.read_csv(f"{DATA_PATH}products.csv")
    return users, orders, order_items, products

def check_data_quality(users, orders, order_items, products):
    """数据质量检查"""
    print("=== 数据质量检查 ===")
    print(f"用户数: {len(users)}")
    print(f"订单数: {len(orders)}")
    print(f"订单明细数: {len(order_items)}")
    print(f"商品数: {len(products)}")

    # 检查缺失值
    print("\n=== 缺失值 ===")
    print(orders.isnull().sum())

    # 检查异常订单金额
    print(f"\n订单金额统计:\n{orders['total_amount'].describe()}")

def clean_orders(orders):
    """清洗订单数据"""
    # 1. 过滤已完成订单
    completed = orders[orders['order_status'] == 'completed'].copy()

    # 2. 过滤异常金额（金额<=0）
    completed = completed[completed['total_amount'] > 0]

    # 3. 过滤日期逻辑错误（订单日期早于用户注册日期）
    # 需要关联users表，这里先标记，后续处理

    print(f"清洗后订单数: {len(completed)}")
    return completed

def merge_data(users, orders, order_items, products):
    """合并数据"""
    # 关联订单和明细
    order_detail = orders.merge(order_items, on='order_id', how='left')

    # 关联用户信息
    order_detail = order_detail.merge(users[['user_id', 'gender', 'city', 'signup_date']],
                                       on='user_id', how='left')

    # 关联商品信息
    order_detail = order_detail.merge(products[['product_id', 'category', 'brand', 'price']],
                                        on='product_id', how='left')

    return order_detail

def calculate_recency(df, analysis_date):
    """计算最近下单距分析日天数"""
    df['order_date'] = pd.to_datetime(df['order_date'])
    analysis_dt = pd.to_datetime(analysis_date)
    df['days_since_order'] = (analysis_dt - df['order_date']).dt.days
    return df

def main():
    """主流程"""
    print("开始数据清洗...")

    # 加载
    users, orders, order_items, products = load_data()

    # 检查
    check_data_quality(users, orders, order_items, products)

    # 清洗订单
    orders_cleaned = clean_orders(orders)

    # 合并
    df = merge_data(users, orders_cleaned, order_items, products)

    # 计算R值基础
    df = calculate_recency(df, ANALYSIS_DATE)

    # 输出
    os.makedirs(OUTPUT_PATH, exist_ok=True)
    df.to_csv(f"{OUTPUT_PATH}cleaned_orders.csv", index=False)
    print(f"\n数据已输出到 {OUTPUT_PATH}cleaned_orders.csv")

    # 输出用户粒度汇总（用于RFM）
    user_summary = df.groupby('user_id').agg({
        'order_id': 'count',           # 订单数=F
        'total_amount': 'sum',          # 总金额=M
        'days_since_order': 'min'       # 最近距=R
    }).reset_index()
    user_summary.columns = ['user_id', 'order_count', 'total_amount', 'days_since_order']
    user_summary.to_csv(f"{OUTPUT_PATH}cleaned_user_summary.csv", index=False)
    print(f"用户汇总已输出到 {OUTPUT_PATH}cleaned_user_summary.csv")

if __name__ == "__main__":
    main()
```

---

- [ ] **Step 2: 运行脚本验证**

Run: `cd "D:/D30360/Documents/ecommerce" && python python/data_cleaning.py`

Expected output:

```
=== 数据质量检查 ===
用户数: xxx
订单数: xxx
...
清洗后订单数: xxx
数据已输出到 cleaned_data/cleaned_orders.csv
用户汇总已输出到 cleaned_data/cleaned_user_summary.csv
```

---

- [ ] **Step 3: 检查输出文件**

Verify files exist:

- `cleaned_data/cleaned_orders.csv`
- `cleaned_data/cleaned_user_summary.csv`

---

## Task 2: MySQL数据仓库建表

**Files:**

- Create: `sql/01_create_tables.sql`
- Create: `sql/02_load_data.sql`

**Goal:** 创建事实表和维度表，构建星型模型

---

- [ ] **Step 1: 创建建表脚本**

Create: `sql/01_create_tables.sql`

```sql
-- =============================================
-- 电商数据仓库建表脚本
-- 星型模型：dwd_user_orders 事实表 + 维度表
-- =============================================

-- 创建数据库（如果不存在）
CREATE DATABASE IF NOT EXISTS ecommerce_rfm;
USE ecommerce_rfm;

-- ----------------------------
-- 维度表：dim_user（用户维度）
-- ----------------------------
DROP TABLE IF EXISTS dim_user;
CREATE TABLE dim_user (
    user_id VARCHAR(20) PRIMARY KEY,
    user_name VARCHAR(100),
    gender VARCHAR(10),
    city VARCHAR(100),
    signup_date DATE
);

-- ----------------------------
-- 维度表：dim_product（商品维度）
-- ----------------------------
DROP TABLE IF EXISTS dim_product;
CREATE TABLE dim_product (
    product_id VARCHAR(20) PRIMARY KEY,
    product_name VARCHAR(200),
    category VARCHAR(100),
    brand VARCHAR(100),
    price DECIMAL(10,2)
);

-- ----------------------------
-- 维度表：dim_order（订单维度）
-- ----------------------------
DROP TABLE IF EXISTS dim_order;
CREATE TABLE dim_order (
    order_id VARCHAR(20) PRIMARY KEY,
    user_id VARCHAR(20),
    order_date DATETIME,
    order_status VARCHAR(20),
    total_amount DECIMAL(10,2),
    days_since_order INT  -- R值：距分析日天数
);

-- ----------------------------
-- 维度表：dim_rfm_segment（RFM分群维度）
-- ----------------------------
DROP TABLE IF EXISTS dim_rfm_segment;
CREATE TABLE dim_rfm_segment (
    segment_id INT PRIMARY KEY,
    segment_name VARCHAR(50),
    rfm_combo VARCHAR(10),
    description VARCHAR(200)
);

-- 插入8大客群定义
INSERT INTO dim_rfm_segment VALUES
(1, '钻石用户', 'R高F高M高', '频次高金额高最近活跃——核心资产'),
(2, '忠诚用户', 'F高M高', '消费能力强但购买频次低——提升频次'),
(3, '潜力用户', 'R高M低', '最近活跃消费潜力大——提升客单价'),
(4, '唤醒用户', 'R中M高', '消费力强但有流失风险——定向召回'),
(5, '挽回用户', 'R低M高', '消费力强但已沉默——强召回'),
(6, '新用户', 'R高F低M低', '刚注册或首购——培育期'),
(7, '沉睡用户', 'R中F中M中', '中等活跃中等消费——激活'),
(8, '流失用户', 'R低F低M低', '长期无购买消费力低——放弃维护');

-- ----------------------------
-- 事实表：dwd_user_order_detail（用户订单明细事实表）
-- ----------------------------
DROP TABLE IF EXISTS dwd_user_order_detail;
CREATE TABLE dwd_user_order_detail (
    id INT AUTO_INCREMENT PRIMARY KEY,
    order_id VARCHAR(20),
    user_id VARCHAR(20),
    product_id VARCHAR(20),
    order_date DATETIME,
    order_status VARCHAR(20),
    category VARCHAR(100),
    brand VARCHAR(100),
    quantity INT,
    item_price DECIMAL(10,2),
    item_total DECIMAL(10,2),
    total_amount DECIMAL(10,2),
    days_since_order INT,
    INDEX idx_user_id (user_id),
    INDEX idx_order_id (order_id),
    INDEX idx_category (category),
    INDEX idx_order_date (order_date)
);

-- ----------------------------
-- 汇总表：dws_user_rfm（RFM用户汇总表）
-- ----------------------------
DROP TABLE IF EXISTS dws_user_rfm;
CREATE TABLE dws_user_rfm (
    user_id VARCHAR(20) PRIMARY KEY,
    order_count INT,           -- F：历史购买频次
    total_amount DECIMAL(10,2),-- M：历史消费金额
    days_since_order INT,      -- R：最近距分析日天数
    r_score VARCHAR(1),        -- R分档：高/中/低
    f_score VARCHAR(1),         -- F分档：高/中/低
    m_score VARCHAR(1),        -- M分档：高/中/低
    rfm_combo VARCHAR(10),     -- RFM组合
    segment_id INT,            -- 客群ID
    segment_name VARCHAR(50),  -- 客群名称
    gender VARCHAR(10),
    city VARCHAR(100),
    signup_date DATE,
    INDEX idx_segment (segment_id),
    INDEX idx_rfm (r_score, f_score, m_score)
);
```

---

- [ ] **Step 2: 创建数据导入脚本**

Create: `sql/02_load_data.sql`

```sql
-- =============================================
-- 数据导入脚本
-- 将清洗后的CSV数据导入MySQL
-- =============================================

USE ecommerce_rfm;

-- 导入用户维度表
LOAD DATA INFILE 'D:/D30360/Documents/ecommerce/data/users.csv'
INTO TABLE dim_user
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(user_id, user_name, email, gender, city, signup_date);

-- 导入商品维度表
LOAD DATA INFILE 'D:/D30360/Documents/ecommerce/data/products.csv'
INTO TABLE dim_product
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(product_id, product_name, category, brand, price, rating);

-- 导入订单维度表（清洗后的已完成订单）
LOAD DATA INFILE 'D:/D30360/Documents/ecommerce/cleaned_data/cleaned_orders.csv'
INTO TABLE dwd_user_order_detail
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(order_id, user_id, product_id, order_date, order_status, total_amount,
 quantity, item_price, item_total, category, brand, gender, city,
 signup_date, days_since_order);

-- 导入用户汇总表（用于RFM计算）
LOAD DATA INFILE 'D:/D30360/Documents/ecommerce/cleaned_data/cleaned_user_summary.csv'
INTO TABLE dws_user_rfm
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(user_id, order_count, total_amount, days_since_order);

-- 验证导入
SELECT 'dim_user' as table_name, COUNT(*) as row_count FROM dim_user
UNION ALL
SELECT 'dim_product', COUNT(*) FROM dim_product
UNION ALL
SELECT 'dwd_user_order_detail', COUNT(*) FROM dwd_user_order_detail
UNION ALL
SELECT 'dws_user_rfm', COUNT(*) FROM dws_user_rfm;
```

---

- [ ] **Step 3: 执行建表和导入**

Run in MySQL:

```bash
# 连接MySQL
mysql -h 127.0.0.1 -P 3306 -u root -p

# 执行建表
source sql/01_create_tables.sql

# 执行导入
source sql/02_load_data.sql
```

Expected: 4 tables created with data loaded

---

## Task 3: RFM分群计算（SQL）

**Files:**

- Create: `sql/03_rfm_calculation.sql`

**Goal:** 计算每个用户的R/F/M值，打标签，归入8大客群

---

- [ ] **Step 1: 创建RFM计算脚本**

Create: `sql/03_rfm_calculation.sql`

```sql
-- =============================================
-- RFM分群计算脚本
-- 分档标准：
--   R：高=0-30天，中=31-120天，低=120天+
--   F：高=3次+，中=2次，低=1次
--   M：高=75分位以上(>976)，中=25-75分位，低=25分位以下(<142)
-- =============================================

USE ecommerce_rfm;

-- ----------------------------
-- Step 1: 计算RFM分位数值
-- ----------------------------
-- 先看金额分位数
SELECT
    PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY total_amount) as p25_amount,
    PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY total_amount) as p75_amount
FROM dws_user_rfm;

-- 结果应为：p25_amount ≈ 142, p75_amount ≈ 976

-- ----------------------------
-- Step 2: 更新R/F/M分档分数
-- ----------------------------
UPDATE dws_user_rfm
SET
    -- R分档：基于天数（越小越好）
    r_score = CASE
        WHEN days_since_order <= 30 THEN '高'
        WHEN days_since_order <= 120 THEN '中'
        ELSE '低'
    END,

    -- F分档：基于订单次数
    f_score = CASE
        WHEN order_count >= 3 THEN '高'
        WHEN order_count = 2 THEN '中'
        ELSE '低'
    END,

    -- M分档：基于金额（基于四分位数）
    m_score = CASE
        WHEN total_amount > 976 THEN '高'       -- 75分位以上
        WHEN total_amount >= 142 THEN '中'        -- 25-75分位
        ELSE '低'                                 -- 25分位以下
    END;

-- ----------------------------
-- Step 3: 生成RFM组合
-- ----------------------------
UPDATE dws_user_rfm
SET rfm_combo = CONCAT(r_score, f_score, m_score);

-- ----------------------------
-- Step 4: 打客群标签
-- ----------------------------
UPDATE dws_user_rfm r
JOIN dim_rfm_segment s ON
    CASE
        -- 钻石用户：R高F高M高
        WHEN r.r_score = '高' AND r.f_score = '高' AND r.m_score = '高'
        THEN s.segment_name = '钻石用户' AND s.rfm_combo = 'R高F高M高'

        -- 忠诚用户：F高M高（RF不是高高）
        WHEN r.f_score = '高' AND r.m_score = '高' AND NOT (r.r_score = '高' AND r.f_score = '高')
        THEN s.segment_name = '忠诚用户'

        -- 潜力用户：R高M低（F不限，但M低）
        WHEN r.r_score = '高' AND r.m_score = '低'
        THEN s.segment_name = '潜力用户'

        -- 唤醒用户：R中M高
        WHEN r.r_score = '中' AND r.m_score = '高'
        THEN s.segment_name = '唤醒用户'

        -- 挽回用户：R低M高
        WHEN r.r_score = '低' AND r.m_score = '高'
        THEN s.segment_name = '挽回用户'

        -- 新用户：R高F低M低
        WHEN r.r_score = '高' AND r.f_score = '低' AND r.m_score = '低'
        THEN s.segment_name = '新用户'

        -- 沉睡用户：R中F中M中
        WHEN r.r_score = '中' AND r.f_score = '中' AND r.m_score = '中'
        THEN s.segment_name = '沉睡用户'

        -- 流失用户：R低F低M低
        WHEN r.r_score = '低' AND r.f_score = '低' AND r.m_score = '低'
        THEN s.segment_name = '流失用户'

        -- 其他情况归入最接近的客群
        ELSE FALSE
    END
WHERE s.segment_id IS NOT NULL;

-- 简化：用CASE WHEN直接更新
UPDATE dws_user_rfm
SET segment_name = CASE
    WHEN r_score = '高' AND f_score = '高' AND m_score = '高' THEN '钻石用户'
    WHEN f_score = '高' AND m_score = '高' AND r_score != '高' THEN '忠诚用户'
    WHEN r_score = '高' AND m_score = '低' THEN '潜力用户'
    WHEN r_score = '中' AND m_score = '高' THEN '唤醒用户'
    WHEN r_score = '低' AND m_score = '高' THEN '挽回用户'
    WHEN r_score = '高' AND f_score = '低' AND m_score = '低' THEN '新用户'
    WHEN r_score = '中' AND f_score = '中' AND m_score = '中' THEN '沉睡用户'
    WHEN r_score = '低' AND f_score = '低' AND m_score = '低' THEN '流失用户'
    -- 兜底：其他情况按M和R判断
    WHEN m_score = '高' AND r_score = '低' THEN '挽回用户'
    WHEN m_score = '高' AND r_score = '中' THEN '唤醒用户'
    WHEN m_score = '中' AND r_score = '中' THEN '沉睡用户'
    ELSE '流失用户'
END;

-- ----------------------------
-- Step 5: 关联用户维度属性
-- ----------------------------
UPDATE dws_user_rfm r
JOIN dim_user u ON r.user_id = u.user_id
SET
    r.gender = u.gender,
    r.city = u.city,
    r.signup_date = u.signup_date;

-- ----------------------------
-- Step 6: 验证结果
-- ----------------------------
SELECT
    segment_name,
    COUNT(*) as user_count,
    SUM(total_amount) as total_revenue,
    AVG(total_amount) as avg_revenue,
    AVG(order_count) as avg_order_count
FROM dws_user_rfm
GROUP BY segment_name
ORDER BY total_revenue DESC;
```

---

- [ ] **Step 2: 执行RFM计算**

Run: 在MySQL中执行 `sql/03_rfm_calculation.sql`

Expected: 8大客群统计结果

---

## Task 4: 商品偏好分析（SQL）

**Files:**

- Create: `sql/04_category_preference.sql`

**Goal:** 分析各RFM客群的商品品类/品牌偏好

---

- [ ] **Step 1: 创建商品偏好分析脚本**

Create: `sql/04_category_preference.sql`

```sql
-- =============================================
-- 商品偏好分析脚本
-- 分析各RFM客群的品类/品牌偏好
-- =============================================

USE ecommerce_rfm;

-- ----------------------------
-- Query 1: 各客群的品类消费分布
-- ----------------------------
SELECT
    r.segment_name,
    p.category,
    COUNT(*) as order_count,
    SUM(od.quantity) as total_quantity,
    SUM(od.item_total) as total_revenue,
    AVG(od.item_price) as avg_price,
    -- 占该客群总金额的百分比
    ROUND(SUM(od.item_total) * 100.0 /
        SUM(SUM(od.item_total)) OVER (PARTITION BY r.segment_name), 2) as revenue_pct
FROM dwd_user_order_detail od
JOIN dws_user_rfm r ON od.user_id = r.user_id
JOIN dim_product p ON od.product_id = p.product_id
GROUP BY r.segment_name, p.category
ORDER BY r.segment_name, total_revenue DESC;

-- ----------------------------
-- Query 2: 各客群的TOP3品类（按金额）
-- ----------------------------
WITH segment_category AS (
    SELECT
        r.segment_name,
        p.category,
        SUM(od.item_total) as total_revenue,
        RANK() OVER (PARTITION BY r.segment_name ORDER BY SUM(od.item_total) DESC) as rank
    FROM dwd_user_order_detail od
    JOIN dws_user_rfm r ON od.user_id = r.user_id
    JOIN dim_product p ON od.product_id = p.product_id
    GROUP BY r.segment_name, p.category
)
SELECT segment_name, category, total_revenue, rank
FROM segment_category
WHERE rank <= 3
ORDER BY segment_name, rank;

-- ----------------------------
-- Query 3: 各客群的TOP品牌偏好
-- ----------------------------
WITH segment_brand AS (
    SELECT
        r.segment_name,
        p.brand,
        COUNT(*) as order_count,
        SUM(od.item_total) as total_revenue,
        RANK() OVER (PARTITION BY r.segment_name ORDER BY SUM(od.item_total) DESC) as rank
    FROM dwd_user_order_detail od
    JOIN dws_user_rfm r ON od.user_id = r.user_id
    JOIN dim_product p ON od.product_id = p.product_id
    GROUP BY r.segment_name, p.brand
)
SELECT segment_name, brand, order_count, total_revenue, rank
FROM segment_brand
WHERE rank <= 5
ORDER BY segment_name, rank;

-- ----------------------------
-- Query 4: 各客群的件单价分布
-- ----------------------------
SELECT
    segment_name,
    MIN(od.item_price) as min_price,
    MAX(od.item_price) as max_price,
    AVG(od.item_price) as avg_price,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY od.item_price) as median_price,
    PERCENTILE_CONT(0.9) WITHIN GROUP (ORDER BY od.item_price) as p90_price
FROM dwd_user_order_detail od
JOIN dws_user_rfm r ON od.user_id = r.user_id
GROUP BY r.segment_name
ORDER BY avg_price DESC;

-- ----------------------------
-- Query 5: 品类交叉购买矩阵（买了A品类的用户，还会买什么）
-- ----------------------------
WITH purchase_categories AS (
    SELECT DISTINCT od.user_id, p.category
    FROM dwd_user_order_detail od
    JOIN dws_user_rfm r ON od.user_id = r.user_id
    JOIN dim_product p ON od.product_id = p.product_id
),
category_pairs AS (
    SELECT
        a.category as category_a,
        b.category as category_b,
        COUNT(*) as co_occur
    FROM purchase_categories a
    JOIN purchase_categories b ON a.user_id = b.user_id AND a.category < b.category
    GROUP BY a.category, b.category
)
SELECT
    category_a,
    category_b,
    co_occur,
    RANK() OVER (PARTITION BY category_a ORDER BY co_occur DESC) as rank
FROM category_pairs
ORDER BY category_a, co_occur DESC;

-- ----------------------------
-- Query 6: 高价值客群 vs 低价值客群的品类差异
-- ----------------------------
SELECT
    p.category,
    SUM(CASE WHEN r.segment_name IN ('钻石用户','忠诚用户') THEN od.item_total ELSE 0 END) as high_value_revenue,
    SUM(CASE WHEN r.segment_name IN ('流失用户','沉睡用户') THEN od.item_total ELSE 0 END) as low_value_revenue,
    COUNT(DISTINCT CASE WHEN r.segment_name IN ('钻石用户','忠诚用户') THEN r.user_id END) as high_value_users,
    COUNT(DISTINCT CASE WHEN r.segment_name IN ('流失用户','沉睡用户') THEN r.user_id END) as low_value_users
FROM dwd_user_order_detail od
JOIN dws_user_rfm r ON od.user_id = r.user_id
JOIN dim_product p ON od.product_id = p.product_id
GROUP BY p.category
ORDER BY high_value_revenue DESC;

-- ----------------------------
-- Query 7: 输出客群商品偏好汇总表
-- ----------------------------
CREATE TABLE IF NOT EXISTS dws_customer_category_pref AS
SELECT
    r.segment_name,
    p.category,
    SUM(od.item_total) as total_revenue,
    SUM(od.quantity) as total_quantity,
    COUNT(DISTINCT r.user_id) as user_count,
    AVG(od.item_price) as avg_price
FROM dwd_user_order_detail od
JOIN dws_user_rfm r ON od.user_id = r.user_id
JOIN dim_product p ON od.product_id = p.product_id
GROUP BY r.segment_name, p.category;

-- 验证
SELECT * FROM dws_customer_category_pref LIMIT 10;
```

---

- [ ] **Step 2: 执行商品偏好分析**

Run: 在MySQL中执行 `sql/04_category_preference.sql`

Expected: 各客群品类偏好数据

---

## Task 5: Power BI可视化

**Files:**

- Create: `powerbi/ecommerce_dashboard.pbix`（手动创建）

**Goal:** 搭建5页交互式仪表板

---

- [ ] **Step 1: Power BI数据连接**

在Power BI Desktop中：

1. Get Data → MySQL Database
2. 连接 `localhost:3306/ecommerce_rfm`
3. 导入以下表：
   - `dws_user_rfm`（RFM分群）
   - `dwd_user_order_detail`（订单明细）
   - `dws_customer_category_pref`（商品偏好）
   - `dim_rfm_segment`（客群字典）

---

- [ ] **Step 2: 创建数据模型关系**

```
dim_rfm_segment (1) ---- (*, segment_id) ---- dws_user_rfm (1) ---- (*, user_id) ---- dwd_user_order_detail
dws_customer_category_pref (N) --被-> dws_user_rfm.segment_name
```

---

- [ ] **Step 3: 创建页面1 - Executive Summary**

| 视觉对象       | 类型       | 字段                            |
| -------------- | ---------- | ------------------------------- |
| 总用户数       | Card       | COUNT(dws_user_rfm[user_id])    |
| 总营收         | Card       | SUM(dws_user_rfm[total_amount]) |
| 平均订单金额   | Card       | AVG(dws_user_rfm[total_amount]) |
| RFM分布        | 饼图       | segment_name, COUNT(user_id)    |
| 各客群金额贡献 | 堆叠柱形图 | segment_name, SUM(total_amount) |

---

- [ ] **Step 4: 创建页面2 - 用户画像**

| 视觉对象           | 类型          | 字段                                 |
| ------------------ | ------------- | ------------------------------------ |
| 各客群用户数       | 柱形图        | segment_name, COUNT(user_id)         |
| 各客群性别分布     | 堆叠柱形图    | segment_name, gender, COUNT(user_id) |
| 各客群城市TOP10    | 表格          | segment_name, city, COUNT(user_id)   |
| 各客群消费金额分布 | 箱线图/柱形图 | segment_name, total_amount           |

---

- [ ] **Step 5: 创建页面3 - RFM分群明细**

| 视觉对象       | 类型   | 字段                                                               |
| -------------- | ------ | ------------------------------------------------------------------ |
| 分群筛选器     | Slicer | segment_name                                                       |
| 用户明细表     | Table  | user_id, segment_name, order_count, total_amount, days_since_order |
| RFM分群占比    | 环形图 | segment_name, COUNT(user_id)                                       |
| 各客群平均金额 | 柱形图 | segment_name, AVG(total_amount)                                    |

---

- [ ] **Step 6: 创建页面4 - 商品偏好分析**

| 视觉对象         | 类型       | 字段                                  |
| ---------------- | ---------- | ------------------------------------- |
| 客群×品类交叉表 | Matrix     | segment_name, category, total_revenue |
| 各客群TOP品类    | 堆叠柱形图 | segment_name, category, total_revenue |
| 各客群件单价分布 | 柱形图     | segment_name, avg_price               |
| TOP品牌偏好      | 表格       | segment_name, brand, total_revenue    |

---

- [ ] **Step 7: 创建页面5 - 运营策略**

运营策略卡片（静态文本+数据联动）：

| 客群     | 核心策略      | 品类推荐           | 预期指标       |
| -------- | ------------- | ------------------ | -------------- |
| 钻石用户 | 维护+专属福利 | 维持现有高客单品类 | 复购率维持90%+ |
| 忠诚用户 | 提升购买频次  | 高频消费品类       | 复购率提升20%  |
| 潜力用户 | 提升客单价    | 高客单潜力品类     | 客单价提升30%  |
| 唤醒用户 | 定向召回      | 召回优惠+偏好品类  | 召回率15%      |
| 挽回用户 | 强召回        | 专属召回+VIP       | 召回率10%      |
| 新用户   | 首单培育      | 新手品类包         | 首单转化50%    |
| 沉睡用户 | 激活          | 促销品类           | 激活率15%      |
| 流失用户 | 低成本维护    | 大促通知           | 成本<20元/人   |

---

## Task 6: 运营策略文档

**Files:**

- Create: `operations/rfm_strategy.md`

**Goal:** 输出8大客群的差异化运营策略文档

---

- [ ] **Step 1: 创建运营策略文档**

Create: `operations/rfm_strategy.md`

```markdown
# 电商用户RFM分群运营策略

## 1. 项目背景

基于RFM模型（Recency最近距、Frequency频次、Monetary金额）对用户进行价值分群，结合商品偏好分析，制定差异化运营策略。

分析数据范围：2024-01-01 至 2025-11-15
覆盖用户数：3,320人
覆盖订单数：4,021单（已完成）

---

## 2. 分群标准

| 分档 | R（最近距） | F（频次） | M（金额） |
|------|------------|----------|----------|
| 高 | 0-30天 | ≥3次 | >976元 |
| 中 | 31-120天 | 2次 | 142-976元 |
| 低 | 120天+ | 1次 | <142元 |

---

## 3. 8大客群画像及运营策略

### 3.1 钻石用户（高×高×高）

**用户特征：**
- 金额贡献：占比最高
- 购买频次：最高
- 最近活跃：最近30天内

**商品偏好：**
- 偏好品类：[待填充：TOP3品类]
- 品牌偏好：[待填充：TOP3品牌]
- 件单价：[待填充：平均件单价]

**运营策略：**
- 专属VIP服务、优先发货
- 专属福利、生日礼包
- 限量新品优先购
- 避免促销打扰（维护品牌调性）

**预期指标：**
- 复购率目标：维持90%+
- 客单价目标：维持现有水平

---

### 3.2 忠诚用户（F高×M高）

**用户特征：**
- 消费能力强（金额高）
- 购买频次高
- 但最近活跃度下降

**商品偏好：**
- 偏好品类：[待填充]
- 件单价：[待填充]

**运营策略：**
- 定向触达、发送复购提醒
- 积分加倍、专属优惠
- 推荐高频消费品类
- 召回内容突出专属利益

**预期指标：**
- 复购率目标：提升20%
- 召回成本ROI：1:3

---

### 3.3 潜力用户（R高×M低）

**用户特征：**
- 最近活跃
- 消费金额偏低
- 有提升潜力

**商品偏好：**
- 偏好品类：[待填充]
- 当前件单价：[待填充]

**运营策略：**
- 向上销售（upselling）
- 满减活动引导
- 高客单品类推荐
- 搭配套餐优惠

**预期指标：**
- 客单价提升：30%
- 方法：品类升级+满减引导

---

### 3.4 唤醒用户（R中×M高）

**用户特征：**
- 消费能力强
- 有流失风险（31-120天未购买）

**商品偏好：**
- 偏好品类：[待填充]

**运营策略：**
- 定向召回短信/推送
- 专属召回优惠券
- 近期热卖品类推荐
- 强调时效性活动

**预期指标：**
- 召回率目标：15%
- 召回成本ROI：1:3

---

### 3.5 挽回用户（R低×M高）

**用户特征：**
- 消费能力强
- 已沉默（120天+未购买）

**商品偏好：**
- 偏好品类：[待填充]

**运营策略：**
- 强召回策略
- 大额专属优惠券
- VIP专属召回通道
- 重新激活购买兴趣

**预期指标：**
- 召回率目标：10%
- 成本可接受：50元/人以内

---

### 3.6 新用户（R高×F低×M低）

**用户特征：**
- 首购或早期用户
- 培育期

**商品偏好：**
- 品类偏好：[待填充]

**运营策略：**
- 新手首单优惠
- 品类新手包推荐
- 引导关注店铺
- 快速建立购买习惯

**预期指标：**
- 首单转化率：50%+
- 二单转化率：30%+

---

### 3.7 沉睡用户（R中×F中×M中）

**用户特征：**
- 中等活跃
- 中等消费
- 需激活

**商品偏好：**
- 品类偏好：[待填充]

**运营策略：**
- 促销活动触达
- 限时优惠引导
- 激活内容：强调性价比
- 简化购买路径

**预期指标：**
- 激活率目标：15%

---

### 3.8 流失用户（R低×F低×M低）

**用户特征：**
- 长期无购买
- 消费力低

**商品偏好：**
- 品类偏好：[待填充]

**运营策略：**
- 大促通知（成本低）
- 放弃维护或低成本维护
- 如召回，只发大促通知

**预期指标：**
- 维护成本：<20元/人
- ROI要求：不强求

---

## 4. 各客群商品品类推荐

| 客群 | 推荐品类1 | 推荐品类2 | 推荐品类3 |
|------|----------|----------|----------|
| 钻石用户 | [待填充] | [待填充] | [待填充] |
| 忠诚用户 | [待填充] | [待填充] | [待填充] |
| 潜力用户 | [待填充] | [待填充] | [待填充] |
| 唤醒用户 | [待填充] | [待填充] | [待填充] |
| 挽回用户 | [待填充] | [待填充] | [待填充] |
| 新用户 | [待填充] | [待填充] | [待填充] |
| 沉睡用户 | [待填充] | [待填充] | [待填充] |
| 流失用户 | [待填充] | [待填充] | [待填充] |

---

## 5. 效果验证

### 5.1 验证方法

| 方法 | 说明 |
|------|------|
| A/B测试 | 分实验组/对照组，验证策略效果 |
| 假设验证 | 基于数据分布估算预期提升 |
| 行业基准 | 对标电商行业平均指标 |

### 5.2 预期总体效果

- 高价值用户（钻石+忠诚）营收贡献：58%
- 通过精细化运营，整体复购率提升：15-20%
- 挽回/唤醒用户召回率：10-15%

---

## 6. 执行优先级

| 优先级 | 客群 | 原因 |
|--------|------|------|
| P0 | 钻石用户 | 核心资产，重点维护 |
| P1 | 忠诚用户 | 高价值，召回成本低 |
| P1 | 潜力用户 | 提升空间大 |
| P2 | 唤醒用户 | 有流失风险，需尽快触达 |
| P2 | 挽回用户 | 成本较高，但高价值 |
| P3 | 新用户 | 培育期，见效慢 |
| P3 | 沉睡用户 | 激活成本高 |
| P4 | 流失用户 | 低成本维护即可 |
```

**注意：** 文档中 `[待填充]` 部分需要等SQL分析结果出来后填充。

---

## 实施检查清单

- [ ] Task 1: Python数据清洗脚本完成并运行成功
- [ ] Task 2: MySQL建表和数据导入完成
- [ ] Task 3: RFM分群计算完成，8大客群统计验证
- [ ] Task 4: 商品偏好分析完成，数据导出
- [ ] Task 5: Power BI仪表板5页完成
- [ ] Task 6: 运营策略文档填充完成

---

## 执行方式选择

**Plan complete and saved to `docs/superpowers/plans/2026-04-25-ecommerce-rfm-plan.md`**

两个执行选项：

**1. Subagent-Driven (recommended)** — 我dispatch fresh subagent per task，任务间review，快速迭代

**2. Inline Execution** — 在此session中执行，批量处理 + checkpoint review

你选择哪种方式？
