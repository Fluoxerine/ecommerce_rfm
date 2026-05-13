-- ==============================================
-- 运营触达清单 — 将分析结果转化为可执行的 campaign 列表
-- 每个用户分配一个运营动作 + 优先级 + 预估响应率
-- ==============================================

SELECT
    user_id,
    segment_operation,
    order_count,
    total_amount,
    days_since_order,
    -- 运营动作（基于 TGI 分析结果定制）
    CASE segment_operation
        WHEN '至尊VIP' THEN
            'P0-新品电子首发通知+Pulse/Orion品牌日专属折扣+专属客服'
        WHEN '核心高价值忠诚用户' THEN
            'P0-Groceries/Beauty复购券+会员升级+全品类满减'
        WHEN '活跃复购潜力用户' THEN
            'P1-Books/Sports品类优惠券+交叉销售推荐+积分翻倍'
        WHEN '高潜新客' THEN
            'P1-首单复购引导+配套推荐+专属客服跟进'
        WHEN '普通新客' THEN
            'P2-7天复购提醒+品类教育邮件+首单满减券'
        WHEN '唤醒高潜' THEN
            'P1-定向召回+Books/Beauty限时折扣+30天有效'
        WHEN '唤醒普通' THEN
            'P3-常规召回邮件+大促通知+小额优惠券'
        WHEN '流失高潜用户' THEN
            'P2-精准召回+Books/Sports品类强激励+双重触达(邮件+SMS)'
        WHEN '流失可弃' THEN
            'P4-不主动触达，仅大促被动覆盖'
        WHEN '流失低潜' THEN
            'P4-季度触达+大促通知'
    END as action,
    -- 优先级
    CASE segment_operation
        WHEN '至尊VIP' THEN 0
        WHEN '核心高价值忠诚用户' THEN 0
        WHEN '活跃复购潜力用户' THEN 1
        WHEN '高潜新客' THEN 1
        WHEN '唤醒高潜' THEN 1
        WHEN '流失高潜用户' THEN 2
        WHEN '普通新客' THEN 2
        WHEN '唤醒普通' THEN 3
        WHEN '流失低潜' THEN 4
        WHEN '流失可弃' THEN 4
    END as priority,
    -- 预估响应率（基于行业基准，实际需 AB 测试校准）
    CASE segment_operation
        WHEN '至尊VIP' THEN 0.40
        WHEN '核心高价值忠诚用户' THEN 0.35
        WHEN '活跃复购潜力用户' THEN 0.25
        WHEN '高潜新客' THEN 0.20
        WHEN '普通新客' THEN 0.12
        WHEN '唤醒高潜' THEN 0.15
        WHEN '唤醒普通' THEN 0.05
        WHEN '流失高潜用户' THEN 0.10
        WHEN '流失可弃' THEN 0.01
        WHEN '流失低潜' THEN 0.03
    END as estimated_response_rate
FROM dws_user_rfm
ORDER BY priority, total_amount DESC;
