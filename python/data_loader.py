"""数据加载模块"""
import sys
import pandas as pd
from config import DATA_DIR, ANALYSIS_DATE, logger


def load_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    """读取原始 CSV 数据，含基础错误处理"""
    logger.info("=" * 60)
    logger.info("1. 数据加载")
    logger.info("=" * 60)

    required_files = ['users.csv', 'orders.csv']
    for f in required_files:
        if not (DATA_DIR / f).exists():
            logger.error("缺少数据文件: %s", DATA_DIR / f)
            print(f"[ERROR] 缺少数据文件: {DATA_DIR / f}")
            print(f"请将 {f} 放入 {DATA_DIR} 目录")
            sys.exit(1)

    users = pd.read_csv(DATA_DIR / 'users.csv')
    orders = pd.read_csv(DATA_DIR / 'orders.csv')

    logger.info("用户数据: %s 条", f"{len(users):,}")
    logger.info("订单数据: %s 条", f"{len(orders):,}")

    # 数据质量速报
    status_dist = orders['order_status'].value_counts()
    logger.info("订单状态分布:\n%s", status_dist.to_string())

    return users, orders


def determine_analysis_date(orders: pd.DataFrame) -> pd.Timestamp:
    """确定分析日期：优先使用环境变量 ANALYSIS_DATE，否则取最晚订单日期+1天"""
    if ANALYSIS_DATE:
        analysis_date = pd.Timestamp(ANALYSIS_DATE)
        logger.info("分析日期（环境变量指定）: %s", analysis_date.strftime('%Y-%m-%d'))
        return analysis_date

    completed = orders[orders['order_status'] == 'completed'].copy()
    completed['order_date'] = pd.to_datetime(completed['order_date'])
    max_order_date = completed['order_date'].max()
    analysis_date = max_order_date + pd.Timedelta(days=1)
    logger.info("订单最晚日期: %s", max_order_date.strftime('%Y-%m-%d'))
    logger.info("分析日期（最晚+1天）: %s", analysis_date.strftime('%Y-%m-%d'))
    return analysis_date
