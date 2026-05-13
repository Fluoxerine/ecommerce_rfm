# 数据字典

## 数据来源

模拟生成的电商交易数据集，包含 6 个 CSV 文件。本项目主要使用其中 3 个。

## 原始数据表

### users（用户表）— 10,000 条

| 字段 | 类型 | 说明 | 示例 |
|------|------|------|------|
| `user_id` | VARCHAR(50) | 用户唯一标识 | U000001 |
| `name` | VARCHAR(100) | 用户姓名（模拟） | Angel Hill |
| `email` | VARCHAR(100) | 邮箱（模拟） | user@example.net |
| `gender` | VARCHAR(20) | 性别 | Male / Female / Other |
| `city` | VARCHAR(100) | 城市 | New Roberttown |
| `signup_date` | DATE | 注册日期 | 2025-03-13 |

### orders（订单表）— 20,000 条

| 字段 | 类型 | 说明 | 示例 |
|------|------|------|------|
| `order_id` | VARCHAR(50) | 订单唯一标识 | O00000001 |
| `user_id` | VARCHAR(50) | 下单用户 | U009310 |
| `order_date` | DATETIME | 下单时间 | 2025-09-09 14:52:37 |
| `order_status` | VARCHAR(20) | 订单状态 | completed / cancelled / returned / processing |
| `total_amount` | DECIMAL(10,2) | 订单金额（元） | 689.66 |

### order_items（订单明细表）— 43,525 条

| 字段 | 类型 | 说明 | 示例 |
|------|------|------|------|
| `order_item_id` | VARCHAR(50) | 明细唯一标识 | I00000001 |
| `order_id` | VARCHAR(50) | 关联订单 | O00000001 |
| `product_id` | VARCHAR(50) | 关联商品 | P001758 |
| `user_id` | VARCHAR(50) | 下单用户 | U009310 |
| `quantity` | INT | 购买数量 | 2 |
| `item_price` | DECIMAL(10,2) | 商品单价 | 8.07 |
| `item_total` | DECIMAL(10,2) | 明细小计 | 16.14 |

### products（商品表）— 2,000 条

| 字段 | 类型 | 说明 | 示例 |
|------|------|------|------|
| `product_id` | VARCHAR(50) | 商品唯一标识 | P000001 |
| `product_name` | VARCHAR(200) | 商品名称 | - |
| `category` | VARCHAR(100) | 品类 | Electronics / Automotive / Home & Kitchen / ... |
| `brand` | VARCHAR(100) | 品牌 | Willow / Orion / Pulse / ... |
| `price` | DECIMAL(10,2) | 标准价格 | - |
| `rating` | DECIMAL(3,2) | 评分 | 4.5 |

## 核心分析表（MySQL 数仓）

### dws_user_rfm（RFM 用户宽表）

清洗后只有 `completed` + `amount > 0` 的订单参与计算。

| 字段 | 说明 | 来源 |
|------|------|------|
| `user_id` | 用户ID | orders |
| `order_count` | 历史 completed 订单数 | COUNT(order_id) |
| `total_amount` | 历史消费总额 | SUM(total_amount) |
| `days_since_order` | 最近购买距分析日天数 | 分析日期 - MAX(order_date) |
| `r_score` | R评分 1/2/3 | ≤60天/61-180天/>180天 |
| `f_score` | F评分 1/2 | 1次/≥2次 |
| `m_score` | M评分 1/2/3 | ≤P25/P25-P75/>P75 |
| `m_p25` / `m_p75` / `vip_threshold` | M阈值（元） | 运行时计算 |
| `is_vip` | 是否VIP | M > Q3+1.5×IQR |
| `segment_19` | 19类基础分群中文标签 | Python/SQL 计算 |
| `segment_operation` | 10大运营组 | Python/SQL 计算 |

## MySQL 数据仓库表一览

| 表名 | 类型 | 用途 |
|------|------|------|
| `dim_user` | 维度 | 用户信息 |
| `dim_product` | 维度 | 商品信息（品类、品牌） |
| `dim_order` | 维度 | 原始订单 |
| `order_items` | 事实 | 订单明细（关联 order → product → user） |
| `dim_rfm_segment` | 字典 | RFM 分群标签参照 |
| `dwd_user_order_detail` | 明细 | 清洗后的用户订单明细 |
| `dws_user_rfm` | 汇总 | RFM 用户宽表（分析输出） |
| `dws_customer_category_pref` | 汇总 | 品类/品牌偏好汇总（TGI 分析输出，每运营组一行） |

### dws_customer_category_pref 列定义

| 列名 | 类型 | 说明 |
|------|------|------|
| `segment_operation` | VARCHAR(20) | 运营组名称 |
| `total_orders` | INT | 该组历史订单总数 |
| `total_amount` | DECIMAL(12,2) | 该组历史消费总额 |
| `total_quantity` | INT | 该组购买商品总件数 |
| `avg_unit_price` | DECIMAL(10,2) | 该组平均商品单价 |
| `top1_category` / `top1_tgi` | VARCHAR(100) / INT | TOP1 品类及其 TGI |
| `top2_category` / `top2_tgi` | VARCHAR(100) / INT | TOP2 品类及其 TGI |
| `top3_category` / `top3_tgi` | VARCHAR(100) / INT | TOP3 品类及其 TGI |
| `top1_brand` / `top1_brand_tgi` | VARCHAR(100) / INT | TOP1 品牌及其 TGI |
| `top2_brand` / `top2_brand_tgi` | VARCHAR(100) / INT | TOP2 品牌及其 TGI |
| `top3_brand` / `top3_brand_tgi` | VARCHAR(100) / INT | TOP3 品牌及其 TGI（2026-05-11 补齐） |

### 数据质量说明

| 处理 | 影响 |
|------|------|
| 仅保留 `order_status = 'completed'` | 约 80% 的订单为非 completed 状态被过滤 |
| 过滤 `total_amount <= 0` | 过滤金额异常的订单 |
| 过滤 `order_date < signup_date` | 过滤日期逻辑错误的订单 |
| 分析日期 = 最晚订单日期 + 1天 | R 值随新增数据变化，建议固定分析日期 |
| 最终有效用户 | ~1,803 人（约 18% 注册用户有有效 completed 订单） |

> **注意**：本项目使用模拟数据，因此过滤率高于真实电商场景。实际生产中 completed 比例通常为 60-80%。
