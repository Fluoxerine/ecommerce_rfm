#!/usr/bin/env python3
"""
数据清洗与分布分析脚本


使用方法：python python/data_cleaning.py
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
import numpy as np
import os

# 设置中文字体
matplotlib.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'KaiTi', 'YouYuan']
matplotlib.rcParams['axes.unicode_minus'] = False

# ---- 统一的现代图表风格 ----
plt.rcParams['figure.facecolor'] = '#F8F9FA'
plt.rcParams['axes.facecolor'] = '#FFFFFF'
plt.rcParams['axes.spines.top'] = False
plt.rcParams['axes.spines.right'] = False
plt.rcParams['axes.grid'] = True
plt.rcParams['grid.alpha'] = 0.3
plt.rcParams['grid.linestyle'] = '--'
plt.rcParams['font.size'] = 10
plt.rcParams['axes.titlesize'] = 12
plt.rcParams['axes.titleweight'] = 'bold'
plt.rcParams['legend.framealpha'] = 0.9
plt.rcParams['legend.edgecolor'] = 'none'
plt.rcParams['patch.edgecolor'] = 'none'
plt.rcParams['boxplot.boxprops.linewidth'] = 1.5
plt.rcParams['boxplot.medianprops.linewidth'] = 2

# 配置
DATA_DIR = 'D:/D30360/Documents/ecommerce/data'
OUTPUT_DIR = 'D:/D30360/Documents/ecommerce/cleaned_data'
REPORT_DIR = 'D:/D30360/Documents/ecommerce/cleaned_data'
# ANALYSIS_DATE 将在运行时根据订单数据动态确定

# RFM阈值（按RFM划分.md文档规格）
# R: 1-60天(活跃) / 61-180天(唤醒) / 181+天(流失)
R_THRESHOLDS = (60, 180)
# F: 1次(一次性) / 2+次(复购)
F_THRESHOLD = 2
# M阈值将在运行时根据25%/75%分位数确定 + VIP箱线图上边缘
M_THRESHOLD_P25 = None  # 将在分析时确定
M_THRESHOLD_P75 = None  # 将在分析时确定
VIP_THRESHOLD = None    # 箱线图上边缘，将在分析时确定

# 颜色方案
COLORS = {
    'primary': '#2E86AB',      # 蓝色
    'secondary': '#A23B72',    # 紫红色
    'accent': '#F18F01',       # 橙色
    'success': '#C73E1D',      # 深红
    'grid': '#E5E5E5',         # 浅灰
    'text': '#333333',         # 深灰文字
    'bg': '#FFFFFF',           # 白色背景
    'r_high': '#27AE60',       # 绿色-R高
    'r_mid': '#F39C12',        # 黄色-R中
    'r_low': '#E74C3C',        # 红色-R低
    'f_high': '#9B59B6',       # 紫色-F高
    'f_mid': '#3498DB',        # 蓝色-F中
    'f_low': '#95A5A6',        # 灰色-F低
    'm_high': '#1ABC9C',       # 青色-M高
    'm_mid': '#F1C40F',        # 金色-M中
    'm_low': '#E67E22',        # 橙色-M低
    # K-means聚类颜色
    'kmeans_0': '#E74C3C',     # 红色
    'kmeans_1': '#3498DB',     # 蓝色
    'kmeans_2': '#2ECC71',     # 绿色
    'kmeans_3': '#9B59B6',    # 紫色
    'kmeans_4': '#F39C12',     # 橙色
    'kmeans_5': '#1ABC9C',     # 青色
    'kmeans_6': '#E67E22',    # 深橙
    'kmeans_7': '#95A5A6',    # 灰色
    'kmeans_8': '#8B4513',    # 棕色
}


def determine_analysis_date(orders_cleaned):
    """根据订单数据确定分析日期：所有订单中最晚日期的后一天"""
    orders_cleaned['order_date'] = pd.to_datetime(orders_cleaned['order_date'])
    max_order_date = orders_cleaned['order_date'].max()
    analysis_date = max_order_date + pd.Timedelta(days=1)
    print(f"订单最晚日期: {max_order_date.strftime('%Y-%m-%d')}")
    print(f"分析日期（最晚日期+1天）: {analysis_date.strftime('%Y-%m-%d')}")
    return analysis_date


def validate_segmentation(user_summary):
    """核验分层用户累计是否等于所有用户总和"""
    total_users = len(user_summary)

    # 19类基础分群验证
    segment_19_dist = user_summary['segment_19'].value_counts()
    segment_19_sum = segment_19_dist.sum()

    # 7大运营组验证
    segment_op_dist = user_summary['segment_operation'].value_counts()
    segment_op_sum = segment_op_dist.sum()

    print("\n" + "=" * 60)
    print("分层核验")
    print("=" * 60)
    print(f"总用户数: {total_users}")

    print(f"\n【19类基础分群】")
    print(f"累计人数: {segment_19_sum}")
    print(f"核验结果: {'[OK] 通过' if segment_19_sum == total_users else '[FAIL] 失败'}")

    print(f"\n【7大运营组】")
    print(f"累计人数: {segment_op_sum}")
    print(f"核验结果: {'[OK] 通过' if segment_op_sum == total_users else '[FAIL] 失败'}")

    return segment_19_sum == total_users and segment_op_sum == total_users


def load_data():
    """读取原始数据"""
    print("正在读取原始数据...")
    users = pd.read_csv(f'{DATA_DIR}/users.csv')
    orders = pd.read_csv(f'{DATA_DIR}/orders.csv')

    print(f"原始订单数: {len(orders)}")
    print(f"原始用户数: {len(users)}")
    return users, orders


def clean_data(orders, users, analysis_date):
    """清洗数据质量问题"""
    print("\n" + "=" * 60)
    print("数据清洗")
    print("=" * 60)

    orders_cleaned = orders.copy()
    original_count = len(orders_cleaned)

    # 清洗规则1: 只保留 order_status = 'completed' 的订单
    orders_cleaned = orders_cleaned[orders_cleaned['order_status'] == 'completed'].copy()
    print(f"规则1 - 过滤非completed订单后: {len(orders_cleaned)} (过滤 {original_count - len(orders_cleaned)} 条)")

    # 清洗规则2: 过滤 total_amount <= 0 的异常订单
    original_count = len(orders_cleaned)
    orders_cleaned = orders_cleaned[orders_cleaned['total_amount'] > 0].copy()
    print(f"规则2 - 过滤total_amount<=0后: {len(orders_cleaned)} (过滤 {original_count - len(orders_cleaned)} 条)")

    # 清洗规则3: 过滤日期逻辑错误（订单日期早于用户注册日期）
    users_signup = users[['user_id', 'signup_date']].copy()
    users_signup['signup_date'] = pd.to_datetime(users_signup['signup_date'])
    orders_cleaned['order_date'] = pd.to_datetime(orders_cleaned['order_date'])

    orders_cleaned = orders_cleaned.merge(users_signup, on='user_id', how='left')
    original_count = len(orders_cleaned)
    orders_cleaned = orders_cleaned[orders_cleaned['order_date'] >= orders_cleaned['signup_date']].copy()
    print(f"规则3 - 过滤日期逻辑错误后: {len(orders_cleaned)} (过滤 {original_count - len(orders_cleaned)} 条)")

    # 计算 days_since_order（距分析日天数）
    orders_cleaned['days_since_order'] = (analysis_date - orders_cleaned['order_date']).dt.days

    return orders_cleaned


def generate_user_summary(orders_cleaned):
    """生成用户粒度汇总数据（用于RFM计算）"""
    user_summary = orders_cleaned.groupby('user_id').agg(
        order_count=('order_id', 'count'),
        total_amount=('total_amount', 'sum'),
        days_since_order=('days_since_order', 'min')
    ).reset_index()

    return user_summary


def analyze_r_distribution(user_summary):
    """分析R（Recency）分布 - 最近购买距分析日天数"""
    print("\n" + "=" * 60)
    print("R分布分析（最近距分析日天数）")
    print("=" * 60)

    r_col = user_summary['days_since_order']

    # 输出完整分布（用于确定阈值）
    print("\n【原始分布】")
    print(f"最小值: {r_col.min()} 天")
    print(f"最大值: {r_col.max()} 天")
    print(f"平均值: {r_col.mean():.1f} 天")
    print(f"中位数: {r_col.median():.1f} 天")

    # 分段统计
    print("\n【分段统计】")
    bins = [0, 7, 14, 30, 60, 90, 120, 180, 365, float('inf')]
    labels = ['0-7天', '8-14天', '15-30天', '31-60天', '61-90天', '91-120天', '121-180天', '181-365天', '365天+']
    r_binned = pd.cut(r_col, bins=bins, labels=labels, right=False)
    r_dist = r_binned.value_counts().sort_index()
    r_pct = (r_dist / len(r_col) * 100).round(1)

    for label in labels:
        count = r_dist.get(label, 0)
        pct = r_pct.get(label, 0)
        bar = '█' * int(pct / 2)
        print(f"{label:>10}: {count:>5} 人 ({pct:>5.1f}%) {bar}")

    # 常用阈值试探
    print("\n【常用阈值试探】")
    thresholds = [
        (30, 90),
        (30, 120),
        (30, 180),
        (60, 120),
        (60, 180),
    ]
    for low, high in thresholds:
        low_count = (r_col <= low).sum()
        mid_count = ((r_col > low) & (r_col <= high)).sum()
        high_count = (r_col > high).sum()
        print(f"阈值 {low}/{high} 天 → 高:{(r_col<=low).sum():>5}人({(r_col<=low).mean()*100:.1f}%) "
              f"中:{mid_count:>5}人({mid_count/len(r_col)*100:.1f}%) "
              f"低:{high_count:>5}人({high_count/len(r_col)*100:.1f}%)")

    return r_col


def analyze_f_distribution(user_summary):
    """分析F（Frequency）分布 - 购买频次"""
    print("\n" + "=" * 60)
    print("F分布分析（历史购买频次）")
    print("=" * 60)

    f_col = user_summary['order_count']

    print("\n【原始分布】")
    print(f"最小值: {f_col.min()} 次")
    print(f"最大值: {f_col.max()} 次")
    print(f"平均值: {f_col.mean():.2f} 次")
    print(f"中位数: {f_col.median():.1f} 次")

    # 分段统计
    print("\n【分段统计】")
    f_dist = f_col.value_counts().sort_index()
    f_pct = (f_dist / len(f_col) * 100).round(1)

    for freq, count in f_dist.items():
        pct = f_pct[freq]
        bar = '█' * int(pct / 2)
        print(f"{freq:>3}次: {count:>5} 人 ({pct:>5.1f}%) {bar}")

    # 常用阈值试探
    print("\n【常用阈值试探】")
    thresholds = [(1, 2, 3), (1, 3, 5), (2, 3, 5)]
    for low, mid, high in thresholds:
        low_count = (f_col <= low).sum()
        mid_count = ((f_col > low) & (f_col <= mid)).sum()
        high_count = (f_col > mid).sum()
        print(f"阈值 {low}/{mid}/{high} 次 → "
              f"低:{low_count:>5}人({low_count/len(f_col)*100:.1f}%) "
              f"中:{mid_count:>5}人({mid_count/len(f_col)*100:.1f}%) "
              f"高:{high_count:>5}人({high_count/len(f_col)*100:.1f}%)")

    # 累积分布
    print("\n【累积分布】")
    for n in [1, 2, 3, 5, 10]:
        cum_pct = (f_col >= n).mean() * 100
        print(f"购买 {n:>2} 次及以上: {(f_col >= n).sum():>5} 人 ({cum_pct:.1f}%)")

    return f_col


def analyze_m_distribution(user_summary):
    """分析M（Monetary）分布 - 消费金额"""
    print("\n" + "=" * 60)
    print("M分布分析（历史消费金额）")
    print("=" * 60)

    m_col = user_summary['total_amount']

    print("\n【原始分布】")
    print(f"最小值: {m_col.min():.2f} 元")
    print(f"最大值: {m_col.max():.2f} 元")
    print(f"平均值: {m_col.mean():.2f} 元")
    print(f"中位数: {m_col.median():.2f} 元")
    print(f"标准差: {m_col.std():.2f} 元")

    # 分段统计
    print("\n【分段统计】")
    bins = [0, 50, 100, 200, 500, 1000, 2000, 5000, 10000, float('inf')]
    labels = ['0-50', '51-100', '101-200', '201-500', '501-1000', '1001-2000', '2001-5000', '5001-10000', '10000+']
    m_binned = pd.cut(m_col, bins=bins, labels=labels, right=False)
    m_dist = m_binned.value_counts().sort_index()
    m_pct = (m_dist / len(m_col) * 100).round(1)

    for label in labels:
        count = m_dist.get(label, 0)
        pct = m_pct.get(label, 0)
        bar = '█' * int(pct / 2)
        print(f"{label:>10}: {count:>5} 人 ({pct:>5.1f}%) {bar}")

    # 常用阈值试探
    print("\n【常用阈值试探】")
    thresholds = [
        (100, 500),
        (100, 1000),
        (200, 500),
        (200, 1000),
        (500, 2000),
    ]
    for low, high in thresholds:
        low_count = (m_col <= low).sum()
        mid_count = ((m_col > low) & (m_col <= high)).sum()
        high_count = (m_col > high).sum()
        print(f"阈值 {low}/{high} 元 → "
              f"低:{low_count:>5}人({low_count/len(m_col)*100:.1f}%) "
              f"中:{mid_count:>5}人({mid_count/len(m_col)*100:.1f}%) "
              f"高:{high_count:>5}人({high_count/len(m_col)*100:.1f}%)")

    # 分位数
    print("\n【分位数】")
    quantiles = [0.1, 0.2, 0.25, 0.5, 0.75, 0.8, 0.9, 0.95]
    for q in quantiles:
        val = m_col.quantile(q)
        print(f"P{int(q*100):>3}: {val:>8.2f} 元")

    return m_col


def analyze_combinations(user_summary):
    """分析19个RFM组合的实际分布 + VIP
    按RFM划分.md文档规格：R(3档)×F(2档)×M(3档)+1类VIP=19类
    """
    print("\n" + "=" * 60)
    print("19类基础分群分布（按RFM划分.md文档规格）")
    print("=" * 60)

    # 按RFM划分.md文档规格阈值
    r_col = user_summary['days_since_order']
    f_col = user_summary['order_count']
    m_col = user_summary['total_amount']

    # R: 1-60(活跃) / 61-180(唤醒) / 181+(流失)
    r_score = r_col.apply(lambda x: 1 if x <= 60 else (2 if x <= 180 else 3))
    # F: 1次(一次性) / 2+(复购)
    f_score = f_col.apply(lambda x: 2 if x >= 2 else 1)
    # M: 25%/75%分位
    m_p25 = m_col.quantile(0.25)
    m_p75 = m_col.quantile(0.75)
    m_score = m_col.apply(lambda x: 3 if x > m_p75 else (2 if x > m_p25 else 1))
    # VIP: 箱线图上边缘
    q1 = m_col.quantile(0.25)
    q3 = m_col.quantile(0.75)
    iqr = q3 - q1
    vip_threshold = q3 + 1.5 * iqr
    is_vip = m_col > vip_threshold

    # 生成18个RFM组合 + 1类VIP
    combo = r_score.astype(str) + '-' + f_score.astype(str) + '-' + m_score.astype(str)
    combo = combo.where(~is_vip, 'VIP')
    combo_count = combo.value_counts().sort_index()

    print(f"\n【19类基础分群分布】（R×F×M+VIP=19类）")
    print(f"{'组合':>8} {'人数':>6} {'占比':>7} {'平均金额':>10}")
    print("-" * 40)

    # 按R-F-M顺序排序
    def sort_key(x):
        if x == 'VIP':
            return (0, 0, 0)  # VIP排第一
        parts = list(map(int, x.split('-')))
        return (parts[0], parts[1], parts[2])

    for c in sorted(combo_count.index, key=sort_key):
        count = combo_count[c]
        pct = count / len(combo) * 100
        avg_amt = user_summary[combo == c]['total_amount'].mean()
        bar = '█' * int(pct)
        print(f"{c:>8} {count:>6} {pct:>6.1f}% {avg_amt:>10.0f}元 {bar}")

    print(f"\n总计: {len(user_summary)} 人，覆盖 {len(combo_count)} 个组合")

    return combo_count


def rule_based_segmentation(user_summary):
    """基于规则进行RFM分层 - 按RFM划分.md文档规格
    19类基础分群：R(3档) × F(2档) × M(3档) + 1类VIP
    7大运营组
    """
    global VIP_THRESHOLD

    r_col = user_summary['days_since_order']
    f_col = user_summary['order_count']
    m_col = user_summary['total_amount']

    # RFM划分.md 文档规格阈值
    # R: 1-60天(活跃) / 61-180天(唤醒) / 181+天(流失)
    r_thresholds = (60, 180)
    # F: 1次(一次性) / 2+次(复购)
    f_threshold = 2
    # M: 25%/75%分位 + VIP箱线图上边缘
    m_p25 = m_col.quantile(0.25)
    m_p75 = m_col.quantile(0.75)
    # VIP: 箱线图上边缘 = Q3 + 1.5*IQR
    q1 = m_col.quantile(0.25)
    q3 = m_col.quantile(0.75)
    iqr = q3 - q1
    vip_threshold = q3 + 1.5 * iqr

    # 保存全局阈值供其他函数使用
    M_THRESHOLD_P25 = m_p25
    M_THRESHOLD_P75 = m_p75
    VIP_THRESHOLD = vip_threshold

    print(f"\n【规则分层阈值】按RFM划分.md文档规格:")
    print(f"  R: <={r_thresholds[0]}天(活跃), {r_thresholds[0]+1}-{r_thresholds[1]}天(唤醒), >{r_thresholds[1]}天(流失)")
    print(f"  F: 1次(一次性), >={f_threshold}次(复购)")
    print(f"  M: <={m_p25:.2f}元(低, P25), {m_p25:.2f}-{m_p75:.2f}元(中), >{m_p75:.2f}元(高, P75)")
    print(f"  VIP: >{vip_threshold:.2f}元(箱线图上边缘)")

    # R评分（天数少=高分，1=活跃,2=唤醒,3=流失）
    r_score = np.where(r_col <= r_thresholds[0], 1,
                       np.where(r_col <= r_thresholds[1], 2, 3))

    # F评分（次数多=高分，1=一次性,2=复购）
    f_score = np.where(f_col >= f_threshold, 2, 1)

    # M评分（金额多=高分，1=低,2=中,3=高）
    m_score = np.where(m_col > m_p75, 3,
                       np.where(m_col > m_p25, 2, 1))

    # VIP标识（M > 箱线图上边缘）
    is_vip = m_col > vip_threshold

    # 生成组合标签
    rfm_combined = [f'{r}-{f}-{m}' for r, f, m in zip(r_score, f_score, m_score)]
    user_summary = user_summary.copy()
    user_summary['r_score'] = r_score
    user_summary['f_score'] = f_score
    user_summary['m_score'] = m_score
    user_summary['rfm_combined'] = rfm_combined
    user_summary['is_vip'] = is_vip

    # 19类基础分群标签
    def assign_19_segment(row):
        if row['is_vip']:
            return 'VIP'
        r, f, m = row['r_score'], row['f_score'], row['m_score']
        return f'{r}-{f}-{m}'

    user_summary['segment_19'] = user_summary.apply(assign_19_segment, axis=1)

    # 7大运营组
    def assign_operation_group(row):
        if row['is_vip']:
            return '至尊VIP'
        r, f, m = row['r_score'], row['f_score'], row['m_score']

        # 组1: 至尊VIP (已在上方处理)
        # 组2: 核心高价值忠诚用户 R1活跃+F2复购+M3高
        if r == 1 and f == 2 and m == 3:
            return '核心高价值忠诚用户'
        # 组3: 活跃复购潜力用户 R1活跃+F2复购+M1低/M2中
        if r == 1 and f == 2 and m in [1, 2]:
            return '活跃复购潜力用户'
        # 组4: 活跃一次性新客 R1活跃+F1一次性+M1/M2/M3
        if r == 1 and f == 1:
            return '活跃一次性新客'
        # 组5: 唤醒沉睡人群 R2唤醒 全部6类
        if r == 2:
            return '唤醒沉睡人群'
        # 组6: 流失高潜用户 R3流失+F2复购+M2中/M3高
        if r == 3 and f == 2 and m in [2, 3]:
            return '流失高潜用户'
        # 组7: 流失低价值低效用户 R3流失 其他情况
        return '流失低价值低效用户'

    user_summary['segment_operation'] = user_summary.apply(assign_operation_group, axis=1)

    return user_summary


def print_segmentation_results(user_summary):
    """打印分层结果 - 19类基础分群 + 7大运营组"""
    print("\n" + "=" * 60)
    print("RFM 19类基础分群结果")
    print("=" * 60)

    segment_19_dist = user_summary['segment_19'].value_counts()
    total = len(user_summary)

    for seg, count in segment_19_dist.items():
        pct = count / total * 100
        bar = '█' * int(pct / 2)
        print(f"{seg:>8}: {count:>5}人 ({pct:>5.1f}%) {bar}")

    print("\n" + "=" * 60)
    print("7大运营组结果")
    print("=" * 60)

    segment_op_dist = user_summary['segment_operation'].value_counts()
    for seg, count in segment_op_dist.items():
        pct = count / total * 100
        bar = '█' * int(pct / 2)
        print(f"{seg:>12}: {count:>5}人 ({pct:>5.1f}%) {bar}")

    return user_summary


def plot_segmentation_chart(user_summary):
    """绘制分层结果图 - 7大运营组"""
    fig, ax = plt.subplots(figsize=(12, 8))
    fig.patch.set_facecolor('#F8F9FA')
    ax.set_facecolor('#FFFFFF')

    segment_op_dist = user_summary['segment_operation'].value_counts()
    # 按人数降序排列
    segment_op_dist = segment_op_dist.sort_values(ascending=False)

    # 使用7大运营组对应颜色
    seg_colors = ['#F44336', '#FF9800', '#9C27B0', '#2196F3', '#1565C0', '#FFD700', '#E74C3C']
    colors = seg_colors[:len(segment_op_dist)]

    wedges, texts, autotexts = ax.pie(segment_op_dist.values, labels=segment_op_dist.index,
                                       autopct='%1.1f%%', colors=colors,
                                       pctdistance=0.72, labeldistance=1.12,
                                       wedgeprops={'edgecolor': 'white', 'linewidth': 2.5},
                                       textprops={'fontsize': 10, 'fontweight': 'bold'})
    for autotext in autotexts:
        autotext.set_fontsize(10)
        autotext.set_fontweight('bold')
        autotext.set_color('white')

    ax.set_title('RFM 7大运营组分布', fontsize=14, fontweight='bold', pad=15)

    plt.tight_layout()
    plt.savefig(f'{REPORT_DIR}/segmentation_result.png', dpi=150, bbox_inches='tight',
               facecolor='#F8F9FA', edgecolor='none')
    plt.close()
    print(f"已保存: {REPORT_DIR}/segmentation_result.png")


def save_results(orders_cleaned, user_summary):
    """保存清洗后的数据"""
    print("\n" + "=" * 60)
    print("保存结果")
    print("=" * 60)

    # 生成 cleaned_orders.csv
    cleaned_orders = orders_cleaned[['order_id', 'user_id', 'order_date', 'order_status',
                                     'total_amount', 'days_since_order']].copy()
    cleaned_orders.to_csv(f'{OUTPUT_DIR}/cleaned_orders.csv', index=False)
    print(f"已生成: {OUTPUT_DIR}/cleaned_orders.csv ({len(cleaned_orders)} 条)")

    # 生成 cleaned_user_summary.csv（包含分群结果）
    user_summary.to_csv(f'{OUTPUT_DIR}/cleaned_user_summary.csv', index=False)
    print(f"已生成: {OUTPUT_DIR}/cleaned_user_summary.csv ({len(user_summary)} 条)")


def plot_r_distribution(user_summary):
    """绘制R（Recency）分布图 - 按RFM划分.md规格: 60/180天"""
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    fig.patch.set_facecolor('#F8F9FA')

    r_col = user_summary['days_since_order']

    # 左图：分段柱状图
    ax1 = axes[0]
    ax1.set_facecolor('#FFFFFF')
    bins = [0, 60, 180, 700]
    labels = ['≤60天\n(活跃)', '61-180天\n(唤醒)', '>180天\n(流失)']
    colors = [COLORS['r_high'], COLORS['r_mid'], COLORS['r_low']]

    counts, bins, patches = ax1.hist(r_col, bins=bins, edgecolor='white', linewidth=2, rwidth=0.85)
    for patch, color in zip(patches, colors):
        patch.set_facecolor(color)
        patch.set_edgecolor('white')
        patch.set_linewidth(2)

    ax1.set_xlabel('距分析日天数', fontsize=11, color='#333333')
    ax1.set_ylabel('用户数', fontsize=11, color='#333333')
    ax1.set_title('R分段分布 (60/180天阈值)', fontsize=13, fontweight='bold', pad=10)

    for count, x in zip(counts, bins[:-1]):
        ax1.text(x + (bins[1] - bins[0]) / 2, count + 10, f'{int(count)}',
                 ha='center', va='bottom', fontsize=11, fontweight='bold', color='#333333')

    ax1.axvline(x=60, color=COLORS['r_high'], linestyle='--', alpha=0.8, linewidth=2, label='60天')
    ax1.axvline(x=180, color=COLORS['r_mid'], linestyle='--', alpha=0.8, linewidth=2, label='180天')
    ax1.legend(loc='upper right', fontsize=9, framealpha=0.9)
    ax1.grid(axis='y', alpha=0.25, linestyle='--', color='#CCCCCC')
    ax1.spines['top'].set_visible(False)
    ax1.spines['right'].set_visible(False)
    ax1.tick_params(colors='#666666')

    # 右图：累计分布曲线
    ax2 = axes[1]
    ax2.set_facecolor('#FFFFFF')
    sorted_r = np.sort(r_col)
    cumulative = np.arange(1, len(sorted_r) + 1) / len(sorted_r) * 100
    ax2.plot(sorted_r, cumulative, color=COLORS['primary'], linewidth=2.5)
    ax2.fill_between(sorted_r, cumulative, alpha=0.15, color=COLORS['primary'])

    ax2.axvline(x=60, color=COLORS['r_high'], linestyle='--', alpha=0.8, linewidth=1.5, label='60天')
    ax2.axvline(x=180, color=COLORS['r_mid'], linestyle='--', alpha=0.8, linewidth=1.5, label='180天')

    ax2.set_xlabel('距分析日天数', fontsize=11, color='#333333')
    ax2.set_ylabel('累计用户比例 (%)', fontsize=11, color='#333333')
    ax2.set_title('R累计分布曲线', fontsize=13, fontweight='bold', pad=10)
    ax2.legend(loc='lower right', fontsize=9, framealpha=0.9)
    ax2.grid(alpha=0.25, linestyle='--', color='#CCCCCC')
    ax2.set_xlim(0, 700)
    ax2.set_ylim(0, 105)
    ax2.spines['top'].set_visible(False)
    ax2.spines['right'].set_visible(False)
    ax2.tick_params(colors='#666666')

    fig.suptitle('R分布分析 - 最近购买距分析日天数', fontsize=15, fontweight='bold', y=1.02)
    plt.tight_layout()
    plt.savefig(f'{REPORT_DIR}/r_distribution.png', dpi=150, bbox_inches='tight',
               facecolor='#F8F9FA', edgecolor='none')
    plt.close()
    print(f"已保存: {REPORT_DIR}/r_distribution.png")


def plot_f_distribution(user_summary):
    """绘制F（Frequency）分布图 - 按RFM划分.md规格: 1次(一次性)/2+(复购)"""
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    fig.patch.set_facecolor('#F8F9FA')

    f_col = user_summary['order_count']

    # 左图：频次柱状图
    ax1 = axes[0]
    ax1.set_facecolor('#FFFFFF')
    f_dist = f_col.value_counts().sort_index()
    bar_colors = [COLORS['f_low'], COLORS['f_mid'], COLORS['f_high'], COLORS['f_high']]
    bars = ax1.bar(f_dist.index, f_dist.values, color=bar_colors[:len(f_dist)],
                   edgecolor='white', linewidth=2, width=0.7)

    ax1.set_xlabel('购买频次', fontsize=11, color='#333333')
    ax1.set_ylabel('用户数', fontsize=11, color='#333333')
    ax1.set_title('F频次分布 (1次=一次性, 2+=复购)', fontsize=13, fontweight='bold', pad=10)
    ax1.set_xticks([1, 2, 3, 4])

    for bar, count in zip(bars, f_dist.values):
        ax1.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 20,
                 f'{count}\n({count/len(f_col)*100:.1f}%)',
                 ha='center', va='bottom', fontsize=10, fontweight='bold', color='#333333')

    ax1.axvline(x=1.5, color=COLORS['f_mid'], linestyle='--', alpha=0.8, linewidth=2, label='1次/2次分界')
    ax1.legend(loc='upper right', fontsize=9, framealpha=0.9)
    ax1.grid(axis='y', alpha=0.25, linestyle='--', color='#CCCCCC')
    ax1.spines['top'].set_visible(False)
    ax1.spines['right'].set_visible(False)
    ax1.tick_params(colors='#666666')

    # 右图：饼图
    ax2 = axes[1]
    ax2.set_facecolor('#FFFFFF')
    f_bins = ['1次 (一次性)', '2次及以上 (复购)']
    f_counts = [(f_col == 1).sum(), (f_col >= 2).sum()]
    colors_pie = [COLORS['f_low'], COLORS['f_high']]
    explode = (0, 0.05)

    wedges, texts, autotexts = ax2.pie(f_counts, labels=f_bins, colors=colors_pie,
                                        explode=explode, autopct='%1.1f%%',
                                        shadow=False, startangle=90,
                                        textprops={'fontsize': 11, 'fontweight': 'bold'},
                                        wedgeprops={'edgecolor': 'white', 'linewidth': 2})
    for autotext in autotexts:
        autotext.set_fontsize(12)
        autotext.set_fontweight('bold')
        autotext.set_color('white')
    ax2.set_title('F频次占比 (一次性vs复购)', fontsize=13, fontweight='bold', pad=10)

    fig.suptitle('F分布分析 - 历史购买频次', fontsize=15, fontweight='bold', y=1.02)
    plt.tight_layout()
    plt.savefig(f'{REPORT_DIR}/f_distribution.png', dpi=150, bbox_inches='tight',
               facecolor='#F8F9FA', edgecolor='none')
    plt.close()
    print(f"已保存: {REPORT_DIR}/f_distribution.png")


def plot_m_distribution(user_summary):
    """绘制M（Monetary）分布图 - 按RFM划分.md规格: P25/P75分位数"""
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    fig.patch.set_facecolor('#F8F9FA')

    m_col = user_summary['total_amount']

    m_p25 = m_col.quantile(0.25)
    m_p75 = m_col.quantile(0.75)
    vip_threshold = m_p75 + 1.5 * (m_p75 - m_p25)

    # 左图：分段柱状图
    ax1 = axes[0]
    ax1.set_facecolor('#FFFFFF')
    bins = [0, m_p25, m_p75, vip_threshold, m_col.max() + 1]
    colors = [COLORS['m_low'], COLORS['m_mid'], COLORS['m_high'], '#FFD700']

    counts, bins, patches = ax1.hist(m_col, bins=bins, edgecolor='white', linewidth=2, rwidth=0.85)
    for patch, color in zip(patches, colors):
        patch.set_facecolor(color)
        patch.set_edgecolor('white')
        patch.set_linewidth(2)

    ax1.set_xlabel('消费金额 (元)', fontsize=11, color='#333333')
    ax1.set_ylabel('用户数', fontsize=11, color='#333333')
    ax1.set_title(f'M金额分段分布 (P25={m_p25:.0f}, P75={m_p75:.0f})', fontsize=13, fontweight='bold', pad=10)

    for count, x in zip(counts, bins[:-1]):
        ax1.text(x + (bins[1] - bins[0]) / 2, count + 10, f'{int(count)}',
                 ha='center', va='bottom', fontsize=11, fontweight='bold', color='#333333')

    ax1.axvline(x=m_p25, color=COLORS['m_mid'], linestyle='--', alpha=0.8, linewidth=2, label=f'P25={m_p25:.0f}')
    ax1.axvline(x=m_p75, color=COLORS['m_high'], linestyle='--', alpha=0.8, linewidth=2, label=f'P75={m_p75:.0f}')
    ax1.axvline(x=vip_threshold, color='#FFD700', linestyle='-', alpha=0.9, linewidth=2.5, label=f'VIP={vip_threshold:.0f}')
    ax1.legend(loc='upper right', fontsize=9, framealpha=0.9)
    ax1.grid(axis='y', alpha=0.25, linestyle='--', color='#CCCCCC')
    ax1.spines['top'].set_visible(False)
    ax1.spines['right'].set_visible(False)
    ax1.tick_params(colors='#666666')

    # 右图：箱线图
    ax2 = axes[1]
    ax2.set_facecolor('#FFFFFF')
    bp = ax2.boxplot(m_col, vert=True, patch_artist=True,
                     boxprops=dict(facecolor=COLORS['primary'], alpha=0.7, edgecolor='#CCCCCC'),
                     medianprops=dict(color='#E74C3C', linewidth=2.5),
                     whiskerprops=dict(color='#555555', linewidth=1.5),
                     capprops=dict(color='#555555', linewidth=1.5),
                     flierprops=dict(marker='o', markerfacecolor='#888888', markersize=4, alpha=0.5))
    ax2.set_ylabel('消费金额 (元)', fontsize=11, color='#333333')
    ax2.set_title('M金额箱线图', fontsize=13, fontweight='bold', pad=10)
    ax2.grid(axis='y', alpha=0.25, linestyle='--', color='#CCCCCC')
    ax2.set_xticklabels(['全部用户'], fontsize=10)
    ax2.spines['top'].set_visible(False)
    ax2.spines['right'].set_visible(False)
    ax2.tick_params(colors='#666666')

    stats_text = f'最小: {m_col.min():.0f}元\nP25: {m_p25:.0f}元\n'
    stats_text += f'中位数: {m_col.median():.0f}元\nP75: {m_p75:.0f}元\nVIP: {vip_threshold:.0f}元'
    ax2.text(1.18, m_col.median() * 0.5, stats_text, fontsize=9, color='#333333',
             verticalalignment='center', bbox=dict(boxstyle='round,pad=0.4', facecolor='#FFF8DC', alpha=0.8, edgecolor='none'))

    fig.suptitle('M分布分析 - 历史消费金额', fontsize=15, fontweight='bold', y=1.02)
    plt.tight_layout()
    plt.savefig(f'{REPORT_DIR}/m_distribution.png', dpi=150, bbox_inches='tight',
               facecolor='#F8F9FA', edgecolor='none')
    plt.close()
    print(f"已保存: {REPORT_DIR}/m_distribution.png")


def plot_combination_heatmap(user_summary, threshold_r=(60, 180), threshold_f=2, m_p25=None, m_p75=None):
    """绘制19类基础分群热力图 (按RFM划分.md文档规格)
    R(3档)×F(2档)×M(3档)+VIP=19类
    """
    m_col = user_summary['total_amount']
    if m_p25 is None:
        m_p25 = m_col.quantile(0.25)
    if m_p75 is None:
        m_p75 = m_col.quantile(0.75)

    # 计算R/F/M分数
    r_score = user_summary['days_since_order'].apply(
        lambda x: 1 if x <= 60 else (2 if x <= 180 else 3)
    )
    f_score = user_summary['order_count'].apply(
        lambda x: 2 if x >= 2 else 1
    )
    m_score = m_col.apply(lambda x: 3 if x > m_p75 else (2 if x > m_p25 else 1))

    # VIP标识
    q1 = m_col.quantile(0.25)
    q3 = m_col.quantile(0.75)
    iqr = q3 - q1
    vip_threshold = q3 + 1.5 * iqr
    is_vip = m_col > vip_threshold

    # 生成组合
    combo = r_score.astype(str) + '-' + f_score.astype(str) + '-' + m_score.astype(str)
    combo = combo.where(~is_vip, 'VIP')

    # 构建矩阵数据 (R x F x M)，VIP单独统计
    # R=1(活跃),2(唤醒),3(流失) x F=1(一次性),2(复购) x M=1(低),2(中),3(高)
    matrix_data = np.zeros((3, 2, 3))
    for r in [1, 2, 3]:
        for f in [1, 2]:
            for m in [1, 2, 3]:
                pattern = f'{r}-{f}-{m}'
                count = (combo == pattern).sum()
                matrix_data[r-1, f-1, m-1] = count

    vip_count = is_vip.sum()

    # 创建 2x2 子图（3个M层 + 1个VIP）
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.patch.set_facecolor('#F8F9FA')
    fig.suptitle('19类RFM基础分群分布热力图 (R×F×M + VIP)', fontsize=15, fontweight='bold', y=1.02)

    m_labels = [f'M低(≤{m_p25:.0f}元)', f'M中({m_p25:.0f}-{m_p75:.0f}元)', f'M高(>{m_p75:.0f}元)']
    r_labels = ['R1活跃(≤60天)', 'R2唤醒(61-180天)', 'R3流失(>180天)']
    f_labels = ['F1一次性(1次)', 'F2复购(2+次)']

    # 绘制3个M层
    plot_idx = 0
    for m_idx in range(3):
        ax = axes[plot_idx // 2, plot_idx % 2]
        ax.set_facecolor('#FFFFFF')
        plot_idx += 1
        matrix = matrix_data[:, :, m_idx]

        im = ax.imshow(matrix, cmap='YlOrRd', aspect='auto')

        ax.set_xticks([0, 1])
        ax.set_xticklabels(f_labels, fontsize=9)
        ax.set_yticks([0, 1, 2])
        ax.set_yticklabels(r_labels, fontsize=9)
        ax.set_title(f'{m_labels[m_idx]}', fontsize=12, fontweight='bold', pad=8)
        ax.tick_params(colors='#555555')

        for i in range(3):
            for j in range(2):
                count = int(matrix[i, j])
                text_color = 'white' if count > matrix.max() * 0.5 else '#222222'
                ax.text(j, i, str(count), ha='center', va='center',
                       fontsize=13, fontweight='bold', color=text_color)

        cbar = plt.colorbar(im, ax=ax, shrink=0.8, pad=0.02)
        cbar.ax.tick_params(labelsize=8)

    # VIP单独一个图
    ax_vip = axes[1, 1]
    ax_vip.set_facecolor('#FFFFFF')
    ax_vip.text(0.5, 0.5, f'VIP\n(箱线图上边缘>\n{vip_threshold:.0f}元)\n\n{vip_count}人',
                ha='center', va='center', fontsize=14, fontweight='bold', color='#7B5800',
                bbox=dict(boxstyle='round,pad=0.6', facecolor='#FFF3CD', alpha=0.9, edgecolor='#FFD700', linewidth=2))
    ax_vip.set_xlim(0, 1)
    ax_vip.set_ylim(0, 1)
    ax_vip.axis('off')
    ax_vip.set_title('VIP (M>箱线图上边缘)', fontsize=12, fontweight='bold', color='#B8860B', pad=8)

    plt.tight_layout()
    plt.savefig(f'{REPORT_DIR}/rfm_combinations_heatmap.png', dpi=150, bbox_inches='tight',
               facecolor='#F8F9FA', edgecolor='none')
    plt.close()
    print(f"已保存: {REPORT_DIR}/rfm_combinations_heatmap.png")


def plot_segment_summary(user_summary, segment_mapping):
    """绘制客群汇总柱状图"""
    fig, ax = plt.subplots(figsize=(12, 6))
    fig.patch.set_facecolor('#F8F9FA')
    ax.set_facecolor('#FFFFFF')

    segments = list(segment_mapping.keys())
    counts = list(segment_mapping.values())

    sorted_data = sorted(zip(segments, counts), key=lambda x: x[1], reverse=True)
    segments, counts = zip(*sorted_data)

    colors = plt.cm.Spectral(np.linspace(0.2, 0.8, len(segments)))
    bars = ax.barh(segments, counts, color=colors, edgecolor='white', linewidth=2, height=0.6)

    ax.set_xlabel('用户数', fontsize=12, color='#333333')
    ax.set_title('RFM客群分布', fontsize=14, fontweight='bold', pad=10)
    ax.grid(axis='x', alpha=0.25, linestyle='--', color='#CCCCCC')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.tick_params(colors='#666666')

    for bar, count in zip(bars, counts):
        ax.text(bar.get_width() + 5, bar.get_y() + bar.get_height() / 2,
                f'{count} ({count/sum(counts)*100:.1f}%)',
                va='center', fontsize=10, fontweight='bold', color='#333333')

    plt.tight_layout()
    plt.savefig(f'{REPORT_DIR}/segment_summary.png', dpi=150, bbox_inches='tight',
               facecolor='#F8F9FA', edgecolor='none')
    plt.close()
    print(f"已保存: {REPORT_DIR}/segment_summary.png")


def generate_dashboard(user_summary, r_col, f_col, m_col):
    """生成综合仪表板 - 按RFM划分.md规格"""
    fig = plt.figure(figsize=(18, 12))
    fig.patch.set_facecolor('#F8F9FA')
    fig.suptitle('RFM数据分析仪表板', fontsize=18, fontweight='bold', y=0.99)

    m_p25 = m_col.quantile(0.25)
    m_p75 = m_col.quantile(0.75)
    vip_th = m_p75 + 1.5 * (m_p75 - m_p25)

    gs = fig.add_gridspec(3, 4, hspace=0.38, wspace=0.3)

    # 1. R分布
    ax1 = fig.add_subplot(gs[0, :2])
    ax1.set_facecolor('#FFFFFF')
    bins = [0, 60, 180, 700]
    colors = [COLORS['r_high'], COLORS['r_mid'], COLORS['r_low']]
    counts, bins, patches = ax1.hist(r_col, bins=bins, edgecolor='white', linewidth=2, rwidth=0.8)
    for patch, color in zip(patches, colors):
        patch.set_facecolor(color)
        patch.set_edgecolor('white')
    ax1.set_title('R分布 - 最近购买距分析日天数', fontsize=11, fontweight='bold', pad=8)
    ax1.set_xlabel('Days', fontsize=9, color='#555555')
    ax1.set_ylabel('Users', fontsize=9, color='#555555')
    ax1.axvline(x=60, color=COLORS['r_high'], linestyle='--', alpha=0.8, linewidth=1.5)
    ax1.axvline(x=180, color=COLORS['r_mid'], linestyle='--', alpha=0.8, linewidth=1.5)
    for count, x in zip(counts, bins[:-1]):
        ax1.text(x + (bins[1] - bins[0]) / 2, count + 5, f'{int(count)}', ha='center', fontsize=9, fontweight='bold', color='#333333')
    ax1.grid(axis='y', alpha=0.25, linestyle='--', color='#CCCCCC')
    ax1.spines['top'].set_visible(False)
    ax1.spines['right'].set_visible(False)
    ax1.tick_params(colors='#666666', labelsize=8)

    # 2. F分布
    ax2 = fig.add_subplot(gs[0, 2:])
    ax2.set_facecolor('#FFFFFF')
    f_dist = f_col.value_counts().sort_index()
    colors_f = [COLORS['f_low'], COLORS['f_mid'], COLORS['f_high'], COLORS['f_high']]
    bars = ax2.bar(f_dist.index, f_dist.values, color=colors_f[:len(f_dist)],
                   edgecolor='white', linewidth=2, width=0.65)
    ax2.set_title('F分布 - 购买频次', fontsize=11, fontweight='bold', pad=8)
    ax2.set_xlabel('Frequency', fontsize=9, color='#555555')
    ax2.set_ylabel('Users', fontsize=9, color='#555555')
    ax2.set_xticks([1, 2, 3, 4])
    ax2.axvline(x=1.5, color=COLORS['f_mid'], linestyle='--', alpha=0.8, linewidth=1.5)
    for bar, count in zip(bars, f_dist.values):
        ax2.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 15,
                f'{count}\n({count/len(f_col)*100:.1f}%)',
                ha='center', fontsize=8, fontweight='bold', color='#333333')
    ax2.grid(axis='y', alpha=0.25, linestyle='--', color='#CCCCCC')
    ax2.spines['top'].set_visible(False)
    ax2.spines['right'].set_visible(False)
    ax2.tick_params(colors='#666666', labelsize=8)

    # 3. M分布
    ax3 = fig.add_subplot(gs[1, :2])
    ax3.set_facecolor('#FFFFFF')
    bins_m = [0, m_p25, m_p75, vip_th, m_col.max() + 1]
    colors_m = [COLORS['m_low'], COLORS['m_mid'], COLORS['m_high'], '#FFD700']
    counts_m, bins_m, patches_m = ax3.hist(m_col, bins=bins_m, edgecolor='white', linewidth=2, rwidth=0.8)
    for patch, color in zip(patches_m, colors_m):
        patch.set_facecolor(color)
        patch.set_edgecolor('white')
    ax3.set_title(f'M分布 - 消费金额 (P25={m_p25:.0f}, P75={m_p75:.0f}, VIP={vip_th:.0f})', fontsize=11, fontweight='bold', pad=8)
    ax3.set_xlabel('Amount (CNY)', fontsize=9, color='#555555')
    ax3.set_ylabel('Users', fontsize=9, color='#555555')
    ax3.axvline(x=m_p25, color=COLORS['m_mid'], linestyle='--', alpha=0.8, linewidth=1.5)
    ax3.axvline(x=m_p75, color=COLORS['m_high'], linestyle='--', alpha=0.8, linewidth=1.5)
    ax3.axvline(x=vip_th, color='#FFD700', linestyle='-', alpha=0.9, linewidth=2)
    for count, x in zip(counts_m, bins_m[:-1]):
        ax3.text(x + (bins_m[1] - bins_m[0]) / 2, count + 5, f'{int(count)}', ha='center', fontsize=9, fontweight='bold', color='#333333')
    ax3.grid(axis='y', alpha=0.25, linestyle='--', color='#CCCCCC')
    ax3.spines['top'].set_visible(False)
    ax3.spines['right'].set_visible(False)
    ax3.tick_params(colors='#666666', labelsize=8)

    # 4. 关键指标
    ax4 = fig.add_subplot(gs[1, 2:])
    ax4.set_facecolor('#FFFFFF')
    ax4.set_title('Key Metrics', fontsize=11, fontweight='bold', pad=8)
    ax4.axis('off')

    metrics_data = [
        ('Total Users', f'{len(user_summary):,}', 'users'),
        ('Total Orders', f'{user_summary["order_count"].sum():,}', 'orders'),
        ('Total Revenue', f'{user_summary["total_amount"].sum():,.0f}', 'CNY'),
        ('Avg Order Value', f'{user_summary["total_amount"].mean():,.0f}', 'CNY'),
        ('R Median', f'{r_col.median():.0f}', 'days'),
        ('F Median', f'{f_col.median():.0f}', 'times'),
        ('M Median', f'{m_col.median():,.0f}', 'CNY'),
    ]

    y_positions = np.linspace(0.85, 0.15, len(metrics_data))
    for i, (label, value, unit) in enumerate(metrics_data):
        ax4.text(0.05, y_positions[i], f'{label}:', fontsize=10, fontweight='bold', color='#333333',
                 transform=ax4.transAxes)
        ax4.text(0.42, y_positions[i], f'{value}', fontsize=10, color=COLORS['primary'],
                 fontweight='bold', transform=ax4.transAxes)
        ax4.text(0.72, y_positions[i], f' {unit}', fontsize=9, color='#888888',
                 transform=ax4.transAxes)

    # 5. 阈值表格
    ax5 = fig.add_subplot(gs[2, :])
    ax5.set_facecolor('#FFFFFF')
    ax5.axis('off')
    ax5.set_title('Recommended Thresholds', fontsize=11, fontweight='bold', pad=8)

    threshold_data = [
        ['维度', '高', '中', '低'],
        ['R (天)', '<=60 (活跃)', '61-180 (唤醒)', '>180 (流失)'],
        ['F (次)', '>=2 (复购)', '1 (一次性)', '-'],
        ['M (元)', f'>P75 ({m_p75:.0f})', f'P25-P75 ({m_p25:.0f}-{m_p75:.0f})', f'<=P25 ({m_p25:.0f})'],
    ]

    table = ax5.table(
        cellText=threshold_data,
        cellLoc='center',
        loc='center',
        colWidths=[0.18, 0.28, 0.28, 0.26]
    )
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1.2, 2)

    for j in range(4):
        table[(0, j)].set_facecolor(COLORS['primary'])
        table[(0, j)].set_text_props(color='white', fontweight='bold')

    for i in range(1, 4):
        for j in range(4):
            if i % 2 == 0:
                table[(i, j)].set_facecolor('#F0F4F8')
            else:
                table[(i, j)].set_facecolor('#FFFFFF')

    plt.savefig(f'{REPORT_DIR}/rfm_dashboard.png', dpi=150, bbox_inches='tight',
               facecolor='#F8F9FA', edgecolor='none')
    plt.close()
    print(f"已保存: {REPORT_DIR}/rfm_dashboard.png")


def plot_cleaning_summary(orders, orders_cleaned):
    """绘制数据清洗过程图"""
    fig, ax = plt.subplots(figsize=(10, 6))
    fig.patch.set_facecolor('#F8F9FA')
    ax.set_facecolor('#FFFFFF')

    steps = ['原始订单', 'Completed\n订单', '金额>0', '日期\n逻辑正确']
    original = len(orders)
    after_completed = len(orders[orders['order_status'] == 'completed'])
    after_amount = after_completed
    after_date = len(orders_cleaned)

    counts = [original, after_completed, after_amount, after_date]
    colors = ['#E74C3C', '#3498DB', '#2ECC71', '#27AE60']

    bars = ax.bar(steps, counts, color=colors, edgecolor='white', linewidth=2.5, width=0.55)

    ax.set_ylabel('订单数', fontsize=12, color='#333333')
    ax.set_title('数据清洗流程', fontsize=14, fontweight='bold', pad=12)
    ax.grid(axis='y', alpha=0.25, linestyle='--', color='#CCCCCC')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.tick_params(colors='#666666')

    for bar, count in zip(bars, counts):
        pct = count / original * 100 if original > 0 else 0
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + original * 0.015,
                f'{count:,}\n({pct:.1f}%)',
                ha='center', va='bottom', fontsize=11, fontweight='bold', color='#333333')

    ax.set_ylim(0, max(counts) * 1.22)

    plt.tight_layout()
    plt.savefig(f'{REPORT_DIR}/cleaning_summary.png', dpi=150, bbox_inches='tight',
               facecolor='#F8F9FA', edgecolor='none')
    plt.close()
    print(f"已保存: {REPORT_DIR}/cleaning_summary.png")


def main():
    print("=" * 60)
    print("电商RFM分析 - 数据清洗与分布分析")
    print("=" * 60)

    # 1. 加载数据
    users, orders = load_data()

    # 1.5 确定分析日期（基于订单最晚日期的后一天）
    # 先做基本清洗，获取订单日期范围
    orders_temp = orders[orders['order_status'] == 'completed'].copy()
    orders_temp['order_date'] = pd.to_datetime(orders_temp['order_date'])
    ANALYSIS_DATE = determine_analysis_date(orders_temp)
    print(f"分析日期: {ANALYSIS_DATE.strftime('%Y-%m-%d')}")

    # 2. 清洗数据
    orders_cleaned = clean_data(orders, users, ANALYSIS_DATE)

    # 3. 生成用户汇总
    user_summary = generate_user_summary(orders_cleaned)

    # 4. R分布分析
    r_col = analyze_r_distribution(user_summary)

    # 5. F分布分析
    f_col = analyze_f_distribution(user_summary)

    # 6. M分布分析
    m_col = analyze_m_distribution(user_summary)

    # 7. 27组合分布
    combo_count = analyze_combinations(user_summary)

    # 8. 生成可视化图表
    print("\n" + "=" * 60)
    print("生成可视化图表")
    print("=" * 60)

    plot_r_distribution(user_summary)
    plot_f_distribution(user_summary)
    plot_m_distribution(user_summary)
    plot_combination_heatmap(user_summary)
    plot_cleaning_summary(orders, orders_cleaned)

    # 9. 生成综合仪表板
    generate_dashboard(user_summary, r_col, f_col, m_col)

    # 10. 规则分层 RFM 分群
    print("\n" + "=" * 60)
    print("规则分层 RFM 分群")
    print("=" * 60)
    user_summary = rule_based_segmentation(user_summary)

    # 11. 打印分层结果
    print_segmentation_results(user_summary)

    # 12. 绘制分层结果图
    plot_segmentation_chart(user_summary)

    # 13. 核验分层用户累计是否等于总用户数
    validate_segmentation(user_summary)

    # 14. 保存结果
    save_results(orders_cleaned, user_summary)

    print("\n" + "=" * 60)
    print("分析完成")
    print("=" * 60)
    print("\n图表已保存至:", REPORT_DIR)


if __name__ == '__main__':
    main()
