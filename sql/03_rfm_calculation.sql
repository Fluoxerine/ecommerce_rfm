-- ==============================================
-- RFM 计算（MySQL 8.4 兼容版）
-- 修复：PERCENTILE_CONT → NTILE 窗口函数
-- ==============================================

USE ecommerce_rfm;

-- ==============================================
-- Step 1: 计算 M 阈值（P25/P75）和 VIP 阈值
-- MySQL 8.4 不支持 PERCENTILE_CONT，使用 NTILE + MAX 替代
-- ==============================================
DROP TEMPORARY TABLE IF EXISTS temp_rfm_thresholds;
CREATE TEMPORARY TABLE temp_rfm_thresholds AS
WITH ranked AS (
    SELECT
        total_amount,
        NTILE(4) OVER (ORDER BY total_amount) as quartile
    FROM dws_user_rfm
),
percentiles AS (
    SELECT
        MAX(CASE WHEN quartile = 1 THEN total_amount END) as m_p25,
        MAX(CASE WHEN quartile = 3 THEN total_amount END) as m_p75
    FROM ranked
)
SELECT
    m_p25,
    m_p75,
    m_p75 + 1.5 * (m_p75 - m_p25) as vip_threshold
FROM percentiles;

-- ==============================================
-- Step 2: R 分数（1=活跃, 2=唤醒, 3=流失）
-- ==============================================
UPDATE dws_user_rfm
SET r_score = CASE
    WHEN days_since_order <= 60 THEN 1
    WHEN days_since_order <= 180 THEN 2
    ELSE 3
END;

-- ==============================================
-- Step 3: F 分数（1=一次性, 2=复购）
-- ==============================================
UPDATE dws_user_rfm
SET f_score = CASE
    WHEN order_count >= 2 THEN 2
    ELSE 1
END;

-- ==============================================
-- Step 4: M 分数（1=低, 2=中, 3=高）
-- ==============================================
UPDATE dws_user_rfm r
JOIN temp_rfm_thresholds t
SET m_score = CASE
    WHEN total_amount > t.m_p75 THEN 3
    WHEN total_amount > t.m_p25 THEN 2
    ELSE 1
END;

-- ==============================================
-- Step 5: VIP 标识
-- ==============================================
UPDATE dws_user_rfm r
JOIN temp_rfm_thresholds t
SET is_vip = CASE WHEN total_amount > t.vip_threshold THEN 1 ELSE 0 END;

-- ==============================================
-- Step 6: 保存阈值到表
-- ==============================================
UPDATE dws_user_rfm r
JOIN temp_rfm_thresholds t
SET r.m_p25 = t.m_p25,
    r.m_p75 = t.m_p75,
    r.vip_threshold = t.vip_threshold;

-- ==============================================
-- Step 7: RFM 组合标签
-- ==============================================
UPDATE dws_user_rfm
SET rfm_combined = CASE
    WHEN is_vip = 1 THEN 'VIP'
    ELSE CONCAT(r_score, '-', f_score, '-', m_score)
END;

-- ==============================================
-- Step 8: 19 类基础分群中文标签
-- ==============================================
UPDATE dws_user_rfm
SET segment_19 = CASE
    WHEN is_vip = 1 THEN '至尊VIP'
    WHEN r_score = 1 AND f_score = 1 AND m_score = 1 THEN '活跃-一次性-低价值'
    WHEN r_score = 1 AND f_score = 1 AND m_score = 2 THEN '活跃-一次性-中价值'
    WHEN r_score = 1 AND f_score = 1 AND m_score = 3 THEN '活跃-一次性-高价值'
    WHEN r_score = 1 AND f_score = 2 AND m_score = 1 THEN '活跃-复购-低价值'
    WHEN r_score = 1 AND f_score = 2 AND m_score = 2 THEN '活跃-复购-中价值'
    WHEN r_score = 1 AND f_score = 2 AND m_score = 3 THEN '活跃-复购-高价值'
    WHEN r_score = 2 AND f_score = 1 AND m_score = 1 THEN '唤醒-一次性-低价值'
    WHEN r_score = 2 AND f_score = 1 AND m_score = 2 THEN '唤醒-一次性-中价值'
    WHEN r_score = 2 AND f_score = 1 AND m_score = 3 THEN '唤醒-一次性-高价值'
    WHEN r_score = 2 AND f_score = 2 AND m_score = 1 THEN '唤醒-复购-低价值'
    WHEN r_score = 2 AND f_score = 2 AND m_score = 2 THEN '唤醒-复购-中价值'
    WHEN r_score = 2 AND f_score = 2 AND m_score = 3 THEN '唤醒-复购-高价值'
    WHEN r_score = 3 AND f_score = 1 AND m_score = 1 THEN '流失-一次性-低价值'
    WHEN r_score = 3 AND f_score = 1 AND m_score = 2 THEN '流失-一次性-中价值'
    WHEN r_score = 3 AND f_score = 1 AND m_score = 3 THEN '流失-一次性-高价值'
    WHEN r_score = 3 AND f_score = 2 AND m_score = 1 THEN '流失-复购-低价值'
    WHEN r_score = 3 AND f_score = 2 AND m_score = 2 THEN '流失-复购-中价值'
    WHEN r_score = 3 AND f_score = 2 AND m_score = 3 THEN '流失-复购-高价值'
    ELSE '未知'
END;

-- ==============================================
-- Step 9: 10 大运营组（优于原 7 组）
-- ==============================================
UPDATE dws_user_rfm
SET segment_operation = CASE
    WHEN is_vip = 1 THEN '至尊VIP'
    WHEN r_score = 1 AND f_score = 2 AND m_score = 3 THEN '核心高价值忠诚用户'
    WHEN r_score = 1 AND f_score = 2 AND m_score IN (1, 2) THEN '活跃复购潜力用户'
    WHEN r_score = 1 AND f_score = 1 AND m_score = 3 THEN '高潜新客'
    WHEN r_score = 1 AND f_score = 1 AND m_score IN (1, 2) THEN '普通新客'
    WHEN r_score = 2 AND f_score = 2 AND m_score IN (2, 3) THEN '唤醒高潜'
    WHEN r_score = 2 THEN '唤醒普通'
    WHEN r_score = 3 AND f_score = 2 AND m_score IN (2, 3) THEN '流失高潜用户'
    WHEN r_score = 3 AND f_score = 1 AND m_score = 1 THEN '流失可弃'
    WHEN r_score = 3 THEN '流失低潜'
    ELSE '未知'
END;

-- ==============================================
-- 验证
-- ==============================================
SELECT segment_operation, COUNT(*) as cnt,
       SUM(total_amount) as revenue,
       AVG(total_amount) as avg_revenue
FROM dws_user_rfm
GROUP BY segment_operation
ORDER BY cnt DESC;
