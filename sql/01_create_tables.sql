-- ==============================================
-- 电商RFM数据仓库 — 建表（含索引、安全开关）
-- ==============================================

-- 安全开关：设为 1 时跳过 DROP（生产环境必须为 1）
SET @safe_mode = 0;

-- ==============================================
-- 1. dim_user — 用户维度表
-- ==============================================
DROP TABLE IF EXISTS dim_user;
CREATE TABLE dim_user (
    user_id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100),
    email VARCHAR(100),
    gender VARCHAR(20),
    city VARCHAR(100),
    signup_date DATE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ==============================================
-- 2. dim_product — 商品维度表
-- ==============================================
DROP TABLE IF EXISTS dim_product;
CREATE TABLE dim_product (
    product_id VARCHAR(50) PRIMARY KEY,
    product_name VARCHAR(200),
    category VARCHAR(100),
    brand VARCHAR(100),
    price DECIMAL(10, 2),
    rating DECIMAL(3, 2),
    INDEX idx_category (category),
    INDEX idx_brand (brand)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ==============================================
-- 3. dim_order — 订单维度表
-- ==============================================
DROP TABLE IF EXISTS dim_order;
CREATE TABLE dim_order (
    order_id VARCHAR(50) PRIMARY KEY,
    user_id VARCHAR(50),
    order_date DATETIME,
    order_status VARCHAR(20),
    total_amount DECIMAL(10, 2),
    INDEX idx_user_id (user_id),
    INDEX idx_order_date (order_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ==============================================
-- 4. dim_order_item — 订单明细事实表
-- ==============================================
DROP TABLE IF EXISTS order_items;
CREATE TABLE order_items (
    order_item_id VARCHAR(50) PRIMARY KEY,
    order_id VARCHAR(50),
    product_id VARCHAR(50),
    user_id VARCHAR(50),
    quantity INT,
    item_price DECIMAL(10, 2),
    item_total DECIMAL(10, 2),
    INDEX idx_order_id (order_id),
    INDEX idx_product_id (product_id),
    INDEX idx_user_id (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ==============================================
-- 5. dim_rfm_segment — RFM分群字典
-- ==============================================
DROP TABLE IF EXISTS dim_rfm_segment;
CREATE TABLE dim_rfm_segment (
    segment_id INT PRIMARY KEY,
    segment_name VARCHAR(50),
    segment_type ENUM('basic_19', 'operation_10') COMMENT '19类基础分群 or 10大运营组',
    r_score INT, f_score INT, m_score INT,
    is_vip TINYINT DEFAULT 0,
    description VARCHAR(200)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 19类基础分群
INSERT INTO dim_rfm_segment VALUES
(1,  '活跃-一次性-低价值', 'basic_19', 1,1,1,0,'R1+F1+M1'),
(2,  '活跃-一次性-中价值', 'basic_19', 1,1,2,0,'R1+F1+M2'),
(3,  '活跃-一次性-高价值', 'basic_19', 1,1,3,0,'R1+F1+M3'),
(4,  '活跃-复购-低价值',  'basic_19', 1,2,1,0,'R1+F2+M1'),
(5,  '活跃-复购-中价值',  'basic_19', 1,2,2,0,'R1+F2+M2'),
(6,  '活跃-复购-高价值',  'basic_19', 1,2,3,0,'R1+F2+M3'),
(7,  '唤醒-一次性-低价值', 'basic_19', 2,1,1,0,'R2+F1+M1'),
(8,  '唤醒-一次性-中价值', 'basic_19', 2,1,2,0,'R2+F1+M2'),
(9,  '唤醒-一次性-高价值', 'basic_19', 2,1,3,0,'R2+F1+M3'),
(10, '唤醒-复购-低价值',  'basic_19', 2,2,1,0,'R2+F2+M1'),
(11, '唤醒-复购-中价值',  'basic_19', 2,2,2,0,'R2+F2+M2'),
(12, '唤醒-复购-高价值',  'basic_19', 2,2,3,0,'R2+F2+M3'),
(13, '流失-一次性-低价值', 'basic_19', 3,1,1,0,'R3+F1+M1'),
(14, '流失-一次性-中价值', 'basic_19', 3,1,2,0,'R3+F1+M2'),
(15, '流失-一次性-高价值', 'basic_19', 3,1,3,0,'R3+F1+M3'),
(16, '流失-复购-低价值',  'basic_19', 3,2,1,0,'R3+F2+M1'),
(17, '流失-复购-中价值',  'basic_19', 3,2,2,0,'R3+F2+M2'),
(18, '流失-复购-高价值',  'basic_19', 3,2,3,0,'R3+F2+M3'),
(19, '至尊VIP',           'basic_19', 0,0,0,1,'M>箱线图上边缘');

-- 10大运营组
INSERT INTO dim_rfm_segment VALUES
(101,'至尊VIP',               'operation_10',0,0,0,1,'M>箱线图上边缘'),
(102,'核心高价值忠诚用户',      'operation_10',1,2,3,0,'R1+F2+M3'),
(103,'活跃复购潜力用户',        'operation_10',1,2,1,0,'R1+F2+M1/M2'),
(104,'高潜新客',              'operation_10',1,1,3,0,'R1+F1+M3（拆分自活跃一次性新客）'),
(105,'普通新客',              'operation_10',1,1,1,0,'R1+F1+M1/M2（拆分自活跃一次性新客）'),
(106,'唤醒高潜',              'operation_10',2,2,2,0,'R2+F2+M2/M3（拆分自唤醒沉睡人群）'),
(107,'唤醒普通',              'operation_10',2,1,0,0,'R2+F1+M任意 + R2+F2+M1'),
(108,'流失高潜用户',           'operation_10',3,2,2,0,'R3+F2+M2/M3'),
(109,'流失可弃',              'operation_10',3,1,1,0,'R3+F1+M1（拆分自流失低价值低效）'),
(110,'流失低潜',              'operation_10',3,0,0,0,'R3中不在以上组的其他用户');

-- ==============================================
-- 6. dwd_user_order_detail — 用户订单明细事实表
-- ==============================================
DROP TABLE IF EXISTS dwd_user_order_detail;
CREATE TABLE dwd_user_order_detail (
    detail_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id VARCHAR(50),
    order_id VARCHAR(50),
    order_date DATETIME,
    order_status VARCHAR(20),
    total_amount DECIMAL(10, 2),
    INDEX idx_user_id (user_id),
    INDEX idx_order_id (order_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ==============================================
-- 7. dws_user_rfm — RFM用户宽表
-- ==============================================
DROP TABLE IF EXISTS dws_user_rfm;
CREATE TABLE dws_user_rfm (
    user_id VARCHAR(50) PRIMARY KEY,
    order_count INT COMMENT '历史购买次数',
    total_amount DECIMAL(12, 2) COMMENT '历史消费总额',
    days_since_order INT COMMENT '最近购买距分析日天数',
    r_score INT COMMENT 'R评分: 1=活跃, 2=唤醒, 3=流失',
    f_score INT COMMENT 'F评分: 1=一次性, 2=复购',
    m_score INT COMMENT 'M评分: 1=低, 2=中, 3=高',
    m_p25 DECIMAL(12, 2) COMMENT 'M阈值: P25分位数',
    m_p75 DECIMAL(12, 2) COMMENT 'M阈值: P75分位数',
    vip_threshold DECIMAL(12, 2) COMMENT 'VIP阈值: 箱线图上边缘',
    is_vip TINYINT DEFAULT 0 COMMENT '是否VIP',
    rfm_combined VARCHAR(10) COMMENT 'R-F-M组合如 1-2-3',
    segment_19 VARCHAR(50) COMMENT '19类基础分群中文标签',
    segment_operation VARCHAR(50) COMMENT '10大运营组名称'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
