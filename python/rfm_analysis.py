"""RFM 分析模块：EDA + 分群 + 统计检验 + 功效分析"""
import numpy as np
import pandas as pd
from scipy import stats
from scipy.stats import skew
from config import R_THRESHOLDS, F_THRESHOLD, logger

# statsmodels 用于事后检验和功效分析（可选依赖）
try:
    from statsmodels.stats.multicomp import pairwise_tukeyhsd
    _HAS_STATSMODELS = True
except ImportError:
    pairwise_tukeyhsd = None  # type: ignore
    _HAS_STATSMODELS = False

try:
    from statsmodels.stats.power import TTestIndPower
    _HAS_POWER = True
except ImportError:
    TTestIndPower = None  # type: ignore
    _HAS_POWER = False


# ============================================================
# EDA：分布分析
# ============================================================

def eda_summary(user_summary: pd.DataFrame) -> tuple[pd.Series, pd.Series, pd.Series]:
    """探索性数据分析：R/F/M 分布特征"""
    logger.info("=" * 60)
    logger.info("4. 探索性数据分析 (EDA)")
    logger.info("=" * 60)

    r_col = user_summary['days_since_order']
    f_col = user_summary['order_count']
    m_col = user_summary['total_amount']

    logger.info("%-12s %10s %10s %12s", '指标', 'R(天)', 'F(次)', 'M(元)')
    logger.info("-" * 46)
    stats_data = [
        ('最小值', r_col.min(), f_col.min(), m_col.min()),
        ('P25', r_col.quantile(0.25), f_col.quantile(0.25), m_col.quantile(0.25)),
        ('中位数', r_col.median(), f_col.median(), m_col.median()),
        ('平均值', r_col.mean(), f_col.mean(), m_col.mean()),
        ('P75', r_col.quantile(0.75), f_col.quantile(0.75), m_col.quantile(0.75)),
        ('最大值', r_col.max(), f_col.max(), m_col.max()),
    ]
    for label, r_val, f_val, m_val in stats_data:
        logger.info("%-8s %10.0f %10.0f %12.0f", label, r_val, f_val, m_val)

    # M 分布偏度
    m_skew = float(skew(m_col))
    skew_label = '右偏/长尾' if m_skew > 1 else '近似对称'
    logger.info("M分布偏度: %.2f (%s)", m_skew, skew_label)

    # F 分布集中度
    f1_pct = (f_col == 1).mean() * 100
    logger.info("仅购买1次的用户占比: %.1f%%", f1_pct)
    logger.info("F分2档依据: %.0f%% 用户F=1，若分3档，第2-3档将几乎为空", f1_pct)

    # 阈值探索
    logger.info("R阈值对比 (当前: %s/%s天):", R_THRESHOLDS[0], R_THRESHOLDS[1])
    for low, high in [(30, 90), (60, 120), (60, 180), (90, 180), (90, 365)]:
        low_n = (r_col <= low).sum()
        mid_n = ((r_col > low) & (r_col <= high)).sum()
        high_n = (r_col > high).sum()
        logger.info("  %s/%s天 → 活跃:%s(%s%%)  唤醒:%s(%s%%)  流失:%s(%s%%)",
                    low, high,
                    f"{low_n:>5}", f"{low_n/len(r_col)*100:.0f}",
                    f"{mid_n:>5}", f"{mid_n/len(r_col)*100:.0f}",
                    f"{high_n:>5}", f"{high_n/len(r_col)*100:.0f}")

    return r_col, f_col, m_col


# ============================================================
# RFM 评分
# ============================================================

def compute_rfm_scores(user_summary: pd.DataFrame) -> pd.DataFrame:
    """计算 R/F/M 分数和 VIP 标识"""
    r_col = user_summary['days_since_order']
    f_col = user_summary['order_count']
    m_col = user_summary['total_amount']

    # M 阈值
    m_p25 = m_col.quantile(0.25)
    m_p75 = m_col.quantile(0.75)
    iqr = m_p75 - m_p25
    vip_threshold = m_p75 + 1.5 * iqr

    logger.info("M阈值: P25=%.0f元, P75=%.0f元, VIP=%.0f元 (Q3+1.5×IQR)",
                m_p25, m_p75, vip_threshold)

    # R 评分（1=活跃, 2=唤醒, 3=流失）
    r_score = np.where(r_col <= R_THRESHOLDS[0], 1,
                       np.where(r_col <= R_THRESHOLDS[1], 2, 3))
    # F 评分（1=一次性, 2=复购）
    f_score = np.where(f_col >= F_THRESHOLD, 2, 1)
    # M 评分（1=低, 2=中, 3=高）
    m_score = np.where(m_col > m_p75, 3,
                       np.where(m_col > m_p25, 2, 1))
    # VIP（仅 M > 箱线图上边缘）
    is_vip = m_col > vip_threshold

    result = user_summary.copy()
    result['r_score'] = r_score
    result['f_score'] = f_score
    result['m_score'] = m_score
    result['is_vip'] = is_vip.astype(int)
    result['m_p25'] = m_p25
    result['m_p75'] = m_p75
    result['vip_threshold'] = vip_threshold

    # 19 类基础分群标签
    result['rfm_combined'] = [
        'VIP' if v else f'{r}-{f}-{m}'
        for r, f, m, v in zip(r_score, f_score, m_score, is_vip)
    ]
    result['segment_19'] = result['rfm_combined'].map(_segment_19_name)

    # 10 组运营分群
    result['segment_operation'] = result.apply(_assign_10_groups, axis=1)

    return result


def _segment_19_name(rfm: str) -> str:
    """19类基础分群名称映射"""
    mapping: dict[str, str] = {
        'VIP': '至尊VIP',
        '1-1-1': '活跃-一次性-低价值', '1-1-2': '活跃-一次性-中价值', '1-1-3': '活跃-一次性-高价值',
        '1-2-1': '活跃-复购-低价值', '1-2-2': '活跃-复购-中价值', '1-2-3': '活跃-复购-高价值',
        '2-1-1': '唤醒-一次性-低价值', '2-1-2': '唤醒-一次性-中价值', '2-1-3': '唤醒-一次性-高价值',
        '2-2-1': '唤醒-复购-低价值', '2-2-2': '唤醒-复购-中价值', '2-2-3': '唤醒-复购-高价值',
        '3-1-1': '流失-一次性-低价值', '3-1-2': '流失-一次性-中价值', '3-1-3': '流失-一次性-高价值',
        '3-2-1': '流失-复购-低价值', '3-2-2': '流失-复购-中价值', '3-2-3': '流失-复购-高价值',
    }
    return mapping.get(rfm, '未知')


def _assign_10_groups(row: pd.Series) -> str:
    """分配到 10 大运营组"""
    if row['is_vip']:
        return '至尊VIP'
    r, f, m = row['r_score'], row['f_score'], row['m_score']

    if r == 1 and f == 2 and m == 3:
        return '核心高价值忠诚用户'
    if r == 1 and f == 2 and m in (1, 2):
        return '活跃复购潜力用户'
    if r == 1 and f == 1 and m == 3:
        return '高潜新客'
    if r == 1 and f == 1 and m in (1, 2):
        return '普通新客'
    if r == 2 and f == 2 and m in (2, 3):
        return '唤醒高潜'
    if r == 2:
        return '唤醒普通'
    if r == 3 and f == 2 and m in (2, 3):
        return '流失高潜用户'
    if r == 3 and f == 1 and m == 1:
        return '流失可弃'
    return '流失低潜'


# ============================================================
# 分群统计
# ============================================================

def print_segmentation_results(user_summary: pd.DataFrame) -> None:
    """打印 19 类 + 10 运营组分布"""
    total = len(user_summary)

    logger.info("=" * 60)
    logger.info("5. 19类基础分群分布")
    logger.info("=" * 60)
    dist = user_summary['segment_19'].value_counts()
    for seg, cnt in dist.items():
        logger.info("  %-16s: %5s人 (%5.1f%%)", seg, f"{cnt}", cnt/total*100)

    logger.info("=" * 60)
    logger.info("6. 10大运营组分布")
    logger.info("=" * 60)
    dist_op = user_summary['segment_operation'].value_counts()
    for seg, cnt in dist_op.items():
        subset = user_summary[user_summary['segment_operation'] == seg]
        avg_m = subset['total_amount'].mean()
        avg_r = subset['days_since_order'].mean()
        avg_f = subset['order_count'].mean()
        logger.info("  %-14s: %5s人 (%5.1f%%)  均R=%.0f天 均F=%.1f次 均M=%.0f元",
                    seg, f"{cnt}", cnt/total*100, avg_r, avg_f, avg_m)

    logger.info("  总计: %s 人, %s 组", total, len(dist_op))


def validate_segmentation(user_summary: pd.DataFrame) -> bool:
    """核验：分群用户累计 == 总用户数"""
    total = len(user_summary)
    seg19_sum = user_summary['segment_19'].value_counts().sum()
    seg10_sum = user_summary['segment_operation'].value_counts().sum()
    seg19_ok = seg19_sum == total
    seg10_ok = seg10_sum == total

    logger.info("=" * 60)
    logger.info("分群核验")
    logger.info("=" * 60)
    logger.info("19类分群: [%s] %s == %s", 'OK' if seg19_ok else 'FAIL', total, seg19_sum)
    logger.info("10运营组: [%s] %s == %s", 'OK' if seg10_ok else 'FAIL', total, seg10_sum)

    return seg19_ok and seg10_ok


def _cohens_d(group1: np.ndarray, group2: np.ndarray) -> float:
    """计算两组独立样本的 Cohen's d 效应量"""
    n1, n2 = len(group1), len(group2)
    if n1 < 2 or n2 < 2:
        return float('nan')
    var1, var2 = np.var(group1, ddof=1), np.var(group2, ddof=1)
    pooled_std = np.sqrt(((n1 - 1) * var1 + (n2 - 1) * var2) / (n1 + n2 - 2))
    if pooled_std == 0:
        return 0.0
    return float((np.mean(group1) - np.mean(group2)) / pooled_std)


def statistical_tests(user_summary: pd.DataFrame) -> None:
    """统计检验：t检验 + ANOVA + Kruskal-Wallis + Tukey HSD + 效应量 + 关键对比"""
    logger.info("=" * 60)
    logger.info("7. 统计显著性检验")
    logger.info("=" * 60)

    # ── 1. t检验：VIP vs 流失低潜 消费金额差异 ──
    vip = user_summary[user_summary['segment_operation'] == '至尊VIP']['total_amount']
    low = user_summary[user_summary['segment_operation'] == '流失低潜']['total_amount']
    t_stat, p_value = stats.ttest_ind(vip, low)
    sig = '显著' if p_value < 0.05 else '不显著'
    d = _cohens_d(vip.values, low.values)
    logger.info("1) VIP vs 流失低潜 金额差异: t=%.2f, p=%.4f (%s), Cohen's d=%.2f", t_stat, p_value, sig, d)
    if not np.isnan(d):
        d_label = '大' if abs(d) >= 0.8 else ('中' if abs(d) >= 0.5 else '小')
        logger.info("   效应量解释: |d|=%.2f → %s效应量 (Cohen, 1988: 0.2小/0.5中/0.8大)", abs(d), d_label)

    # ── 2. ANOVA：各组 R 值差异 ──
    seg_names = list(user_summary['segment_operation'].value_counts().index)
    groups_r = {g: user_summary[user_summary['segment_operation'] == g]['days_since_order'].dropna().values
                for g in seg_names}
    group_values_r = [v for v in groups_r.values() if len(v) > 1]
    if len(group_values_r) >= 3:
        f_stat, p_value = stats.f_oneway(*group_values_r)
        sig = '各组R值存在显著差异' if p_value < 0.05 else '差异不显著'
        # eta² 计算
        all_r = np.concatenate(group_values_r)
        grand_mean = np.mean(all_r)
        ss_between = sum(len(g) * (np.mean(g) - grand_mean) ** 2 for g in group_values_r)
        ss_total = sum((x - grand_mean) ** 2 for x in all_r)
        eta_sq = ss_between / ss_total if ss_total > 0 else 0.0
        logger.info("2) 各组R值 ANOVA: F=%.2f, p=%.4f (%s), η²=%.4f", f_stat, p_value, sig, eta_sq)
        eta_label = '大' if eta_sq >= 0.14 else ('中' if eta_sq >= 0.06 else '小')
        logger.info("   效应量解释: η²=%.4f → %s效应量 (Cohen, 1988: 0.01小/0.06中/0.14大)", eta_sq, eta_label)

    # ── 3. Kruskal-Wallis 非参数检验（M分布右偏，ANOVA正态假设不满足） ──
    groups_m = {g: user_summary[user_summary['segment_operation'] == g]['total_amount'].dropna().values
                for g in seg_names}
    group_values_m = [v for v in groups_m.values() if len(v) > 1]
    if len(group_values_m) >= 3:
        h_stat, p_value = stats.kruskal(*group_values_m)
        sig = '各组M值存在显著差异' if p_value < 0.05 else '差异不显著'
        logger.info("3) 各组M值 Kruskal-Wallis: H=%.2f, p=%.4f (%s) [非参数，不要求正态分布]",
                    h_stat, p_value, sig)

    # ── 4. Tukey HSD 事后检验（各组M值） ──
    if _HAS_STATSMODELS:
        m_arr = user_summary['total_amount'].values
        seg_arr = user_summary['segment_operation'].values
        tukey = pairwise_tukeyhsd(m_arr, seg_arr, alpha=0.05)
        summary_df = pd.DataFrame(tukey.summary().data[1:], columns=tukey.summary().data[0])
        sig_pairs = summary_df[summary_df['reject']]
        logger.info("4) Tukey HSD 事后检验（M值）——显著差异组对 (p<0.05): %d/%d",
                    len(sig_pairs), len(summary_df))
        if len(sig_pairs) == 0:
            logger.info("   无显著差异组对")
        else:
            for _, row in sig_pairs.head(15).iterrows():
                logger.info("   %s vs %s: meandiff=%.0f, p=%.4f",
                            row['group1'], row['group2'], float(row['meandiff']), float(row['p-adj']))
            if len(sig_pairs) > 15:
                logger.info("   ... 另有 %d 对省略", len(sig_pairs) - 15)
    else:
        logger.info("4) Tukey HSD: statsmodels 未安装，跳过")

    # ── 5. 关键对比：活跃复购潜力 vs 流失高潜（"同群不同期"假说验证） ──
    active = user_summary[user_summary['segment_operation'] == '活跃复购潜力用户']['total_amount']
    lapsed = user_summary[user_summary['segment_operation'] == '流失高潜用户']['total_amount']
    if len(active) >= 2 and len(lapsed) >= 2:
        t_stat2, p_value2 = stats.ttest_ind(active, lapsed)
        d2 = _cohens_d(active.values, lapsed.values)
        # Bonferroni 校正：3 个计划比较 (VIPvs流失低潜 + 复购潜力vs流失高潜 + 可选的唤醒对比)
        bonferroni_p = min(p_value2 * 3, 1.0)
        sig2 = '显著' if bonferroni_p < 0.05 else '不显著'
        logger.info("5) 活跃复购潜力 vs 流失高潜 M值: t=%.2f, p=%.4f, Bonferroni校正p=%.4f (%s), d=%.2f",
                    t_stat2, p_value2, bonferroni_p, sig2, d2)
        if p_value2 >= 0.05:
            logger.info("   → M值差异不显著，支持'同群不同期'假说（两组消费能力相近）")
        else:
            logger.info("   → M值差异显著，'同群不同期'假说存疑——两组可能不是同一类用户")
    else:
        logger.info("5) 活跃复购潜力 vs 流失高潜: 样本量不足（需每组≥2），跳过")


def power_analysis(user_summary: pd.DataFrame) -> None:
    """样本量功效分析：评估每组在当前人数下可检测的最小效应量"""
    logger.info("=" * 60)
    logger.info("8. 样本量功效分析")
    logger.info("=" * 60)

    if not _HAS_POWER:
        logger.info("statsmodels 未安装，跳过功效分析")
        return

    power_obj = TTestIndPower()
    alpha = 0.05
    target_power = 0.8

    logger.info("α=%.2f, 目标功效=%.1f, 双尾独立样本t检验 (n1=n2=n)", alpha, target_power)
    logger.info("Cohen's d 基准: 0.2=小, 0.5=中, 0.8=大 (Cohen, 1988)")
    logger.info("")
    logger.info("%-16s %7s %14s %14s", "运营组", "样本量", "可检测最小d", "效果")
    logger.info("-" * 54)

    for seg_name in user_summary['segment_operation'].value_counts().index:
        n = user_summary[user_summary['segment_operation'] == seg_name].shape[0]
        if n < 3:
            logger.info("%-16s %7s %14s", seg_name, f"{n}", "N/A (<3)")
            continue
        try:
            min_d = power_obj.solve_power(
                effect_size=None, nobs1=n, alpha=alpha,
                power=target_power, ratio=1.0, alternative='two-sided'
            )
            if min_d >= 0.8:
                level = "仅大效应量"
            elif min_d >= 0.5:
                level = "中+大效应量"
            else:
                level = "小中大均可"
            logger.info("%-16s %7s %14.2f %14s", seg_name, f"{n}", min_d, level)
        except Exception:
            logger.info("%-16s %7s %14s", seg_name, f"{n}", "计算异常")

    logger.info("")
    logger.info("说明: '可检测最小d' 越小越好。d=1.56 表示只能检出 >1.56σ 的差异。")
    logger.info("      核心高价值忠诚(16人)可检出 d≥1.56（仅大效应），VIP(130人)可检出 d≥0.49（中等+大效应）。")
