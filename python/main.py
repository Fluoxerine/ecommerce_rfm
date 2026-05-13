"""电商 RFM 用户价值分析 — 主入口"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import OUTPUT_DIR, CHART_DIR, logger
from data_loader import load_data, determine_analysis_date
from data_cleaning import clean_orders, generate_user_summary
from rfm_analysis import (
    eda_summary,
    compute_rfm_scores,
    print_segmentation_results,
    validate_segmentation,
    statistical_tests,
    power_analysis,
)
from visualization import (
    plot_rfm_dashboard,
    plot_cleaning_funnel,
    plot_rfm_scatter,
    plot_revenue_contribution,
    plot_tgi_heatmap,
    plot_rfm_bubble,
    plot_strategy_matrix,
    plot_segment_overview,
)


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    CHART_DIR.mkdir(parents=True, exist_ok=True)

    logger.info("=" * 60)
    logger.info("电商用户价值分析 — RFM分群 + 品类TGI偏好")
    logger.info("=" * 60)

    # [1] 数据加载
    users, orders = load_data()

    # [1b] 确定分析日期
    analysis_date = determine_analysis_date(orders)

    # [2] 数据清洗
    orders_cleaned = clean_orders(orders, users, analysis_date)

    # [3] 用户汇总
    user_summary = generate_user_summary(orders_cleaned)

    # [4] EDA
    r_col, f_col, m_col = eda_summary(user_summary)

    # [5-6] RFM 评分 & 分群
    user_summary = compute_rfm_scores(user_summary)

    # [5-6] 分群结果（日志输出 5.19类 + 6.10组）
    print_segmentation_results(user_summary)

    # [7] 统计检验
    statistical_tests(user_summary)

    # [8] 样本量功效分析
    power_analysis(user_summary)

    # 分群核验（与日志编号对齐）
    validate_segmentation(user_summary)

    # [9] 可视化
    logger.info("=" * 60)
    logger.info("9. 生成可视化图表 (8张)")
    logger.info("=" * 60)
    plot_rfm_dashboard(user_summary)
    plot_cleaning_funnel(orders, orders_cleaned)
    plot_rfm_scatter(user_summary)
    plot_revenue_contribution(user_summary)
    plot_tgi_heatmap(user_summary)
    plot_rfm_bubble(user_summary)
    plot_strategy_matrix(user_summary)
    plot_segment_overview(user_summary)

    # [10] 保存结果
    logger.info("=" * 60)
    logger.info("10. 保存清洗结果")
    logger.info("=" * 60)

    out_orders = orders_cleaned[['order_id', 'user_id', 'order_date',
                                  'order_status', 'total_amount', 'days_since_order']]
    out_path = OUTPUT_DIR / 'cleaned_orders.csv'
    out_orders.to_csv(out_path, index=False)
    logger.info("已保存: %s (%s 条)", out_path, f"{len(out_orders):,}")

    summary_path = OUTPUT_DIR / 'cleaned_user_summary.csv'
    user_summary.to_csv(summary_path, index=False)
    logger.info("已保存: %s (%s 条)", summary_path, f"{len(user_summary):,}")

    logger.info("=" * 60)
    logger.info("分析完成")
    logger.info("=" * 60)
    logger.info("图表目录: %s", CHART_DIR)
    logger.info("数据目录: %s", OUTPUT_DIR)
    logger.info("下一步: 将 %s 导入 MySQL", OUTPUT_DIR / 'cleaned_user_summary.csv')
    logger.info("       然后执行 sql/ 目录下的 SQL 脚本进行 TGI 品类分析")


if __name__ == '__main__':
    main()
