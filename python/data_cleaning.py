"""数据清洗模块"""
import pandas as pd
from config import logger


def clean_orders(orders: pd.DataFrame, users: pd.DataFrame,
                 analysis_date: pd.Timestamp) -> pd.DataFrame:
    """清洗订单数据：过滤无效订单 + 计算 Recency"""
    logger.info("=" * 60)
    logger.info("2. 数据清洗")
    logger.info("=" * 60)

    cleaned = orders.copy()
    total_original = len(cleaned)

    # 规则 1：只保留 completed 订单
    discarded_status = cleaned[cleaned['order_status'] != 'completed']
    cleaned = cleaned[cleaned['order_status'] == 'completed'].copy()
    n_status = len(discarded_status)
    logger.info("规则1 - 保留completed订单: %s 条 (过滤 %s 条非completed)",
                f"{len(cleaned):,}", f"{n_status:,}")

    # 规则 2：过滤 total_amount <= 0
    before = len(cleaned)
    cleaned = cleaned[cleaned['total_amount'] > 0].copy()
    n_amount = before - len(cleaned)
    logger.info("规则2 - 过滤金额≤0: %s 条 (过滤 %s 条)",
                f"{len(cleaned):,}", f"{n_amount:,}")

    # 规则 3：订单日期 ≥ 用户注册日期
    users_signup = users[['user_id', 'signup_date']].copy()
    users_signup['signup_date'] = pd.to_datetime(users_signup['signup_date'])
    cleaned['order_date'] = pd.to_datetime(cleaned['order_date'])

    cleaned = cleaned.merge(users_signup, on='user_id', how='left')

    # 检测缺失注册日期的用户
    missing_signup = cleaned['signup_date'].isna().sum()
    if missing_signup > 0:
        logger.warning("规则3 - %s 条订单的 user_id 在 users 表中无匹配，将被过滤", missing_signup)

    date_valid = cleaned['order_date'] >= cleaned['signup_date']
    n_date = (~date_valid).sum()
    cleaned = cleaned[date_valid].copy()
    logger.info("规则3 - 过滤日期逻辑错误: %s 条 (过滤 %s 条)",
                f"{len(cleaned):,}", f"{n_date:,}")

    # 计算 Recency（距分析日天数）
    cleaned['days_since_order'] = (analysis_date - cleaned['order_date']).dt.days

    pct = len(cleaned) / total_original * 100
    logger.info("清洗完成: %s → %s 条 (保留 %.1f%%)",
                f"{total_original:,}", f"{len(cleaned):,}", pct)

    return cleaned


def generate_user_summary(orders_cleaned: pd.DataFrame) -> pd.DataFrame:
    """生成用户粒度汇总表（RFM 输入）"""
    logger.info("=" * 60)
    logger.info("3. 用户粒度汇总")
    logger.info("=" * 60)

    summary = orders_cleaned.groupby('user_id').agg(
        order_count=('order_id', 'count'),
        total_amount=('total_amount', 'sum'),
        days_since_order=('days_since_order', 'min')
    ).reset_index()

    logger.info("用户数: %s", f"{len(summary):,}")
    logger.info("人均订单: %.2f 次", summary['order_count'].mean())
    logger.info("人均消费: %.0f 元", summary['total_amount'].mean())
    logger.info("中位R值: %.0f 天", summary['days_since_order'].median())

    # F 分布速览
    f_dist = summary['order_count'].value_counts().sort_index()
    for k, v in f_dist.items():
        pct = v / len(summary) * 100
        logger.info("  购买 %s 次: %s 人 (%.1f%%)", k, f"{v:>5}", pct)

    return summary
