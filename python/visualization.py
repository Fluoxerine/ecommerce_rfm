"""可视化模块 — 8张分析图表 + 统一配色"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from config import COLORS, SEGMENT_COLORS, CHART_DIR, DATA_DIR, logger

# ── 中文字体 ──────────────────────────────────────────
matplotlib.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'KaiTi']
matplotlib.rcParams['axes.unicode_minus'] = False

BASE_STYLE = {
    'figure.facecolor': '#F8F9FA',
    'axes.facecolor': '#FFFFFF',
    'axes.spines.top': False,
    'axes.spines.right': False,
    'axes.grid': True,
    'grid.alpha': 0.3,
    'grid.linestyle': '--',
    'font.size': 10,
    'axes.titlesize': 12,
    'axes.titleweight': 'bold',
}
plt.rcParams.update(BASE_STYLE)

# 每组局部随机状态（避免全局种子污染）
_RNG = np.random.RandomState(42)


def _get_segment_color(name: str) -> str:
    """获取运营组对应颜色，未匹配返回灰色"""
    return SEGMENT_COLORS.get(name, '#999999')


def _segment_sort_key(name: str) -> int:
    """10组排序键：VIP → 高价值 → 活跃 → 唤醒 → 流失"""
    order = ['至尊VIP', '核心高价值忠诚用户', '活跃复购潜力用户',
             '高潜新客', '普通新客', '唤醒高潜', '唤醒普通',
             '流失高潜用户', '流失可弃', '流失低潜']
    try:
        return order.index(name)
    except ValueError:
        return 99


# ================================================================
# 图1: RFM 三维分布仪表板
# ================================================================
def plot_rfm_dashboard(user_summary: pd.DataFrame) -> None:
    """合并 R/F/M 分布为一张信息型仪表板"""
    r_col = user_summary['days_since_order']
    f_col = user_summary['order_count']
    m_col = user_summary['total_amount']
    m_p25 = m_col.quantile(0.25)
    m_p75 = m_col.quantile(0.75)
    vip_th = m_p75 + 1.5 * (m_p75 - m_p25)
    total = len(user_summary)

    fig = plt.figure(figsize=(16, 12))
    fig.patch.set_facecolor('#F8F9FA')

    # ---- 左上: R分布 ----
    ax1 = fig.add_subplot(2, 3, 1)
    ax1.set_facecolor('#FFFFFF')
    bins_r = [0, 60, 180, max(r_col.max(), 700)]
    colors_r = [COLORS['r_high'], COLORS['r_mid'], COLORS['r_low']]
    counts_r, _, patches = ax1.hist(r_col, bins=bins_r, edgecolor='white', linewidth=2, rwidth=0.85)
    for p, c in zip(patches, colors_r):
        p.set_facecolor(c)
    for cnt, x in zip(counts_r, bins_r[:-1]):
        pct = cnt / total * 100
        ax1.text(x + (bins_r[1] - bins_r[0]) / 2, cnt + total * 0.01,
                 f'{int(cnt)}\n({pct:.0f}%)', ha='center', fontsize=9, fontweight='bold', color='#333')
    ax1.axvline(x=60, color=COLORS['r_high'], linestyle='--', linewidth=1.5, alpha=0.7)
    ax1.axvline(x=180, color=COLORS['r_mid'], linestyle='--', linewidth=1.5, alpha=0.7)
    ax1.set_title(f'R 分布 (中位={r_col.median():.0f}天)', fontsize=11, fontweight='bold')
    ax1.set_xlabel('距分析日天数')
    ax1.set_ylabel('用户数')
    ax1.legend(['60天', '180天'], fontsize=8, loc='upper right')

    # ---- 中上: R累计曲线 ----
    ax2 = fig.add_subplot(2, 3, 2)
    ax2.set_facecolor('#FFFFFF')
    sorted_r = np.sort(r_col)
    cum = np.arange(1, len(sorted_r) + 1) / len(sorted_r) * 100
    ax2.plot(sorted_r, cum, color=COLORS['primary'], linewidth=2.5)
    ax2.fill_between(sorted_r, cum, alpha=0.12, color=COLORS['primary'])
    ax2.axvline(x=60, color=COLORS['r_high'], linestyle='--', linewidth=1.5, alpha=0.7)
    ax2.axvline(x=180, color=COLORS['r_mid'], linestyle='--', linewidth=1.5, alpha=0.7)
    ax2.set_xlim(0, sorted_r.max() * 1.05)
    ax2.set_ylim(0, 105)
    ax2.set_title('R 累计分布曲线', fontsize=11, fontweight='bold')
    ax2.set_xlabel('天数')
    ax2.set_ylabel('累计占比 (%)')

    # ---- 右上: F分布 ----
    ax3 = fig.add_subplot(2, 3, 3)
    ax3.set_facecolor('#FFFFFF')
    f_dist = f_col.value_counts().sort_index()
    bar_c = [COLORS['f_low'], COLORS['f_mid'], COLORS['f_high'], COLORS['f_high']]
    bars3 = ax3.bar(f_dist.index.astype(str), f_dist.values, color=bar_c[:len(f_dist)],
                     edgecolor='white', linewidth=2, width=0.65)
    for bar, cnt in zip(bars3, f_dist.values):
        ax3.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + total * 0.01,
                 f'{cnt}\n({cnt/total*100:.1f}%)', ha='center', fontsize=9, fontweight='bold', color='#333')
    ax3.set_title(f'F 分布 (1次={f_dist.get(1, 0)/total*100:.0f}%)', fontsize=11, fontweight='bold')
    ax3.set_xlabel('购买次数')
    ax3.set_ylabel('用户数')

    # ---- 左下: M分布 ----
    ax4 = fig.add_subplot(2, 3, 4)
    ax4.set_facecolor('#FFFFFF')
    bins_m = [0, m_p25, m_p75, vip_th, m_col.max() + 1]
    colors_m = [COLORS['m_low'], COLORS['m_mid'], COLORS['m_high'], '#FFD700']
    counts_m, _, patches_m = ax4.hist(m_col, bins=bins_m, edgecolor='white', linewidth=2, rwidth=0.85)
    for p, c in zip(patches_m, colors_m):
        p.set_facecolor(c)
    ax4.axvline(x=m_p25, color=COLORS['m_mid'], linestyle='--', linewidth=1.5, alpha=0.7)
    ax4.axvline(x=m_p75, color=COLORS['m_high'], linestyle='--', linewidth=1.5, alpha=0.7)
    ax4.axvline(x=vip_th, color='#FFD700', linestyle='-', linewidth=2)
    ax4.set_title(f'M分布 P25={m_p25:.0f} P75={m_p75:.0f} VIP={vip_th:.0f}', fontsize=11, fontweight='bold')
    ax4.set_xlabel('消费金额 (元)')
    ax4.set_ylabel('用户数')

    # ---- 中下: 箱线图 ----
    ax5 = fig.add_subplot(2, 3, 5)
    ax5.set_facecolor('#FFFFFF')
    ax5.boxplot(m_col, vert=True, patch_artist=True,
                     boxprops=dict(facecolor=COLORS['primary'], alpha=0.6),
                     medianprops=dict(color='#E74C3C', linewidth=2.5),
                     flierprops=dict(marker='o', markersize=3, alpha=0.4))
    ax5.axhline(y=m_p25, color=COLORS['m_mid'], linestyle='--', linewidth=1, alpha=0.6)
    ax5.axhline(y=m_p75, color=COLORS['m_high'], linestyle='--', linewidth=1, alpha=0.6)
    ax5.axhline(y=vip_th, color='#FFD700', linestyle='-', linewidth=1.5, alpha=0.6)
    ax5.set_ylabel('消费金额 (元)')
    ax5.set_title('M 箱线图')
    ax5.set_xticklabels(['全部用户'])

    # ---- 右下: KPI卡片 ----
    ax6 = fig.add_subplot(2, 3, 6)
    ax6.set_facecolor('#FFFFFF')
    ax6.axis('off')
    kpis = [
        ('总用户', f'{total:,}'),
        ('中位R', f'{r_col.median():.0f}天'),
        ('购买1次占比', f'{((f_col == 1).mean() * 100):.0f}%'),
        ('中位M', f'{m_col.median():.0f}元'),
        ('VIP人数', f'{(m_col > vip_th).sum()}'),
        ('活跃/唤醒/流失',
         f'{((r_col <= 60).mean()*100):.0f}% / '
         f'{(((r_col > 60) & (r_col <= 180)).mean()*100):.0f}% / '
         f'{((r_col > 180).mean()*100):.0f}%'),
    ]
    for i, (label, value) in enumerate(kpis):
        y = 0.85 - i * 0.15
        ax6.text(0.05, y, label, fontsize=11, fontweight='bold', color='#666', transform=ax6.transAxes)
        ax6.text(0.45, y, value, fontsize=13, fontweight='bold', color=COLORS['primary'], transform=ax6.transAxes)
    ax6.set_title('关键指标', fontsize=11, fontweight='bold')

    fig.suptitle('RFM 三维分布仪表板', fontsize=15, fontweight='bold', y=0.98)
    plt.tight_layout(rect=[0, 0, 1, 0.96])
    path = CHART_DIR / '01_rfm_dashboard.png'
    fig.savefig(path, dpi=150, bbox_inches='tight', facecolor='#F8F9FA')
    plt.close(fig)
    logger.info("已保存: %s", path)


# ================================================================
# 图2: 数据清洗漏斗
# ================================================================
def plot_cleaning_funnel(orders: pd.DataFrame, orders_cleaned: pd.DataFrame) -> None:
    """数据清洗漏斗 — 正确标注每步丢弃量"""
    total = len(orders)

    # 步骤1: 过滤 completed
    completed_df = orders[orders['order_status'] == 'completed']
    completed = len(completed_df)
    discarded_status = total - completed

    # 步骤2: 过滤金额 <= 0（在 completed 子集上）
    amount_valid = len(completed_df[completed_df['total_amount'] > 0])
    discarded_amount = completed - amount_valid

    # 步骤3: 日期逻辑校验 = 最终清洗结果
    after_date = len(orders_cleaned)
    discarded_date = amount_valid - after_date

    fig, ax = plt.subplots(figsize=(10, 6))
    fig.patch.set_facecolor('#F8F9FA')
    ax.set_facecolor('#FFFFFF')

    steps = ['原始订单', '保留\nCompleted', '金额 > 0', '日期逻辑\n正确']
    counts = [total, completed, amount_valid, after_date]
    color_list = ['#95A5A6', '#3498DB', '#2ECC71', '#27AE60']

    bars = ax.bar(steps, counts, color=color_list, edgecolor='white', linewidth=2.5, width=0.55)
    for i, (bar, cnt) in enumerate(zip(bars, counts)):
        pct = cnt / total * 100 if total else 0
        previous = counts[i - 1] if i > 0 else cnt
        dropped = previous - cnt if i > 0 else 0
        label = f'{cnt:,}\n({pct:.1f}%)'
        if dropped > 0:
            label += f'\n丢弃 {dropped:,}'
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + total * 0.02,
                label, ha='center', va='bottom', fontsize=10, fontweight='bold', color='#333')

    # 丢弃原因标注
    discards = [
        (discarded_status, '非completed'),
        (discarded_amount, '金额≤0'),
        (discarded_date, '日期异常'),
    ]
    for i, (cnt_val, reason) in enumerate(discards):
        if cnt_val > 0:
            ax.text(i + 1.2, counts[i + 1] / 2, f'{reason}: {cnt_val:,}',
                    fontsize=9, color='#E74C3C', ha='left', va='center', fontweight='bold')

    ax.set_ylabel('订单数')
    ax.set_title('数据清洗漏斗')
    ax.set_ylim(0, max(counts) * 1.25)
    plt.tight_layout()
    path = CHART_DIR / '02_cleaning_funnel.png'
    fig.savefig(path, dpi=150, bbox_inches='tight', facecolor='#F8F9FA')
    plt.close(fig)
    logger.info("已保存: %s", path)


# ================================================================
# 图3: RFM 散点矩阵 — R × M 分群可视化
# ================================================================
def plot_rfm_scatter(user_summary: pd.DataFrame) -> None:
    """RFM散点矩阵：X=Recency(天) Y=Monetary(元) 颜色=运营组"""
    fig, axes = plt.subplots(1, 2, figsize=(18, 7))
    fig.patch.set_facecolor('#F8F9FA')

    segs = sorted(user_summary['segment_operation'].unique(), key=_segment_sort_key)

    for ax_idx, (ax, y_col, y_label) in enumerate([
        (axes[0], 'total_amount', 'M: 历史消费金额 (元)'),
        (axes[1], 'order_count', 'F: 购买次数'),
    ]):
        ax.set_facecolor('#FFFFFF')
        for seg in segs:
            subset = user_summary[user_summary['segment_operation'] == seg]
            alpha_val = 0.6 if len(subset) < 30 else 0.4
            size_val = 25 if len(subset) < 30 else 12
            ax.scatter(subset['days_since_order'], subset[y_col],
                       c=_get_segment_color(seg), label=seg,
                       alpha=alpha_val, s=size_val, edgecolors='none')

        ax.axvline(x=60, color='#666', linestyle='--', alpha=0.4, linewidth=1)
        ax.axvline(x=180, color='#666', linestyle='--', alpha=0.4, linewidth=1)
        ax.set_xlabel('R: 距分析日天数', fontsize=10)
        ax.set_ylabel(y_label, fontsize=10)

    axes[0].set_title('R × M 散点矩阵', fontsize=13, fontweight='bold')
    axes[1].set_title('R × F 散点矩阵', fontsize=13, fontweight='bold')

    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc='center right', fontsize=8, ncol=1,
               framealpha=0.9, bbox_to_anchor=(1.01, 0.5))
    fig.suptitle('RFM 散点矩阵 - 每个点 = 一个用户', fontsize=15, fontweight='bold', y=0.99)
    plt.tight_layout(rect=[0, 0, 0.92, 0.95])
    path = CHART_DIR / '03_rfm_scatter.png'
    fig.savefig(path, dpi=150, bbox_inches='tight', facecolor='#F8F9FA')
    plt.close(fig)
    logger.info("已保存: %s", path)


# ================================================================
# 图4: 营收贡献双层图 — 替代饼图
# ================================================================
def plot_revenue_contribution(user_summary: pd.DataFrame) -> None:
    """双层图：柱=各组人数, 折线=各组累计营收占比, 颜色=运营组"""
    dist = user_summary['segment_operation'].value_counts()
    segs = sorted(dist.index, key=_segment_sort_key)
    counts = [dist[s] for s in segs]
    revenues = [user_summary[user_summary['segment_operation'] == s]['total_amount'].sum() for s in segs]
    total_rev: float = float(sum(revenues))
    cum_pct: np.ndarray = np.cumsum(revenues) / total_rev * 100

    fig, ax1 = plt.subplots(figsize=(14, 7))
    fig.patch.set_facecolor('#F8F9FA')
    ax1.set_facecolor('#FFFFFF')

    colors = [_get_segment_color(s) for s in segs]
    bars = ax1.bar(range(len(segs)), counts, color=colors, edgecolor='white', linewidth=2, width=0.7)
    ax1.set_ylabel('用户数', fontsize=11, color='#333')
    ax1.set_xlabel('运营组', fontsize=11)
    ax1.set_xticks(range(len(segs)))
    ax1.set_xticklabels(segs, rotation=30, ha='right', fontsize=9)

    for bar, cnt, rev in zip(bars, counts, revenues):
        ax1.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + max(counts) * 0.01,
                 f'{cnt}人\n¥{rev/1000:.0f}k', ha='center', fontsize=8, fontweight='bold', color='#333')

    ax2 = ax1.twinx()
    ax2.plot(range(len(segs)), cum_pct, 'o-', color='#E74C3C', linewidth=2.5, markersize=8,
             markerfacecolor='#E74C3C', markeredgecolor='white', markeredgewidth=1.5)
    ax2.set_ylabel('累计营收占比 (%)', fontsize=11, color='#E74C3C')
    ax2.set_ylim(0, 105)
    ax2.tick_params(axis='y', colors='#E74C3C')

    ax2.axhline(y=80, color='#999', linestyle=':', linewidth=1.5, alpha=0.7)
    ax2.text(len(segs) - 0.5, 81, '80%营收线', fontsize=9, color='#999', ha='right')

    ax1.set_title('10大运营组用户数 & 累计营收贡献', fontsize=14, fontweight='bold')
    ax1.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    path = CHART_DIR / '04_revenue_contribution.png'
    fig.savefig(path, dpi=150, bbox_inches='tight', facecolor='#F8F9FA')
    plt.close(fig)
    logger.info("已保存: %s", path)


# ================================================================
# 图5: TGI 品类偏好热力图
# ================================================================
def plot_tgi_heatmap(user_summary: pd.DataFrame) -> None:
    """本地计算 TGI 并生成热力图"""
    try:
        products = pd.read_csv(DATA_DIR / 'products.csv')
        order_items = pd.read_csv(DATA_DIR / 'order_items.csv')
        orders = pd.read_csv(DATA_DIR / 'orders.csv')

        # 仅保留 completed 订单的 order_items
        completed_orders = orders[orders['order_status'] == 'completed']['order_id']
        oi = order_items[order_items['order_id'].isin(completed_orders)].copy()
        oi = oi.merge(products[['product_id', 'category']], on='product_id', how='left')
        oi = oi.merge(user_summary[['user_id', 'segment_operation']], on='user_id', how='inner')

        # 全体品类占比
        all_cat_pct = oi.groupby('category')['item_total'].sum()
        all_cat_pct = all_cat_pct / all_cat_pct.sum()

        # 各组 × 品类 TGI
        segments = sorted(user_summary['segment_operation'].unique(), key=_segment_sort_key)
        categories = sorted(all_cat_pct.index)
        tgi_matrix = np.zeros((len(segments), len(categories)))

        for i, seg in enumerate(segments):
            seg_data = oi[oi['segment_operation'] == seg]
            seg_cat = seg_data.groupby('category')['item_total'].sum()
            seg_cat_pct = seg_cat / seg_cat.sum()
            for j, cat in enumerate(categories):
                if cat in seg_cat_pct and all_cat_pct[cat] > 0:
                    tgi_matrix[i, j] = (seg_cat_pct[cat] / all_cat_pct[cat]) * 100

        fig, ax = plt.subplots(figsize=(14, 8))
        fig.patch.set_facecolor('#F8F9FA')
        ax.set_facecolor('#FFFFFF')

        im = ax.imshow(tgi_matrix, cmap='RdBu_r', aspect='auto', vmin=40, vmax=160)
        ax.set_xticks(range(len(categories)))
        ax.set_xticklabels(categories, rotation=30, ha='right', fontsize=9)
        ax.set_yticks(range(len(segments)))
        ax.set_yticklabels(segments, fontsize=9)

        for i in range(len(segments)):
            for j in range(len(categories)):
                val = tgi_matrix[i, j]
                if val > 0:
                    color = 'white' if abs(val - 100) > 35 else '#333'
                    if val >= 130:
                        marker = '★★★'
                    elif val >= 120:
                        marker = '★★'
                    elif val >= 110:
                        marker = '★'
                    elif val <= 80:
                        marker = '▽'
                    else:
                        marker = ''
                    ax.text(j, i, f'{val:.0f}{marker}', ha='center', va='center', fontsize=8,
                            fontweight='bold', color=color)

        cbar = plt.colorbar(im, ax=ax, shrink=0.8, pad=0.02)
        cbar.set_label('TGI', fontsize=10)
        cbar.ax.axhline(y=100, color='black', linewidth=1.5)

        ax.set_title('TGI 品类偏好热力图 (★★★>130 >★★>120 >★>110)', fontsize=14, fontweight='bold')
        plt.tight_layout()
        path = CHART_DIR / '05_tgi_heatmap.png'
        fig.savefig(path, dpi=150, bbox_inches='tight', facecolor='#F8F9FA')
        plt.close(fig)
        logger.info("已保存: %s", path)
    except FileNotFoundError as e:
        logger.warning("跳过 TGI 热力图（缺少数据文件）: %s", e)
    except Exception as e:
        logger.error("TGI 热力图生成失败: %s", e, exc_info=True)


# ================================================================
# 图6: RFM 气泡图 — R × F × M 三维可视化
# ================================================================
def plot_rfm_bubble(user_summary: pd.DataFrame) -> None:
    """气泡图：X=R Y=F 气泡大小=M 颜色=运营组"""
    fig, ax = plt.subplots(figsize=(14, 8))
    fig.patch.set_facecolor('#F8F9FA')
    ax.set_facecolor('#FFFFFF')

    n = len(user_summary)
    r_jitter = _RNG.uniform(-2, 2, n)
    f_jitter = _RNG.uniform(-0.05, 0.05, n)

    segs = sorted(user_summary['segment_operation'].unique(), key=_segment_sort_key)
    for seg in segs:
        subset = user_summary[user_summary['segment_operation'] == seg]
        idx = subset.index
        sizes = np.sqrt(subset['total_amount']) * 2
        ax.scatter(subset['days_since_order'] + r_jitter[idx],
                   subset['order_count'] + f_jitter[idx],
                   s=sizes, c=_get_segment_color(seg), label=seg,
                   alpha=0.5, edgecolors='white', linewidth=0.5)

    ax.axvline(x=60, color='#666', linestyle='--', alpha=0.4, linewidth=1, label='R=60天')
    ax.axvline(x=180, color='#666', linestyle='--', alpha=0.4, linewidth=1, label='R=180天')
    ax.axhline(y=1.5, color='#666', linestyle='--', alpha=0.4, linewidth=1, label='F=1/2分界')
    ax.set_xlabel('R: 距分析日天数', fontsize=11)
    ax.set_ylabel('F: 购买次数', fontsize=11)
    ax.set_title('RFM 气泡图 (气泡大小 = 消费金额)', fontsize=14, fontweight='bold')
    ax.legend(loc='upper left', fontsize=8, ncol=2, framealpha=0.9)

    plt.tight_layout()
    path = CHART_DIR / '06_rfm_bubble.png'
    fig.savefig(path, dpi=150, bbox_inches='tight', facecolor='#F8F9FA')
    plt.close(fig)
    logger.info("已保存: %s", path)


# ================================================================
# 图7: 策略矩阵 — ROI × 用户数 四象限
# ================================================================
def plot_strategy_matrix(user_summary: pd.DataFrame) -> None:
    """策略矩阵：X=ROI估算 Y=用户数 气泡=营收 颜色=运营组"""
    dist = user_summary['segment_operation'].value_counts()
    segs = sorted(dist.index, key=_segment_sort_key)

    # 为每组估算 ROI
    roi_estimates: dict[str, float] = {}
    for seg in segs:
        subset = user_summary[user_summary['segment_operation'] == seg]
        r_mean = subset['r_score'].mean()
        f_mean = subset['f_score'].mean()
        m_mean = subset['m_score'].mean()
        r_mult = 1.5 if r_mean < 1.5 else (0.6 if r_mean < 2.5 else 0.3)
        f_mult = 1.0 if f_mean >= 1.8 else 0.7
        m_mult = 1.3 if m_mean >= 2.5 else (1.0 if m_mean >= 1.5 else 0.7)
        response = 0.08 * r_mult * f_mult * m_mult
        cost_per = 0.15 + (20 * response)
        n = len(subset)
        if n > 0 and cost_per > 0:
            roi = (n * response * subset['total_amount'].mean() * 0.5) / (n * cost_per)
        else:
            roi = 0.1
        roi_estimates[seg] = max(roi, 0.1)

    fig, ax = plt.subplots(figsize=(14, 8))
    fig.patch.set_facecolor('#F8F9FA')
    ax.set_facecolor('#FFFFFF')

    for seg in segs:
        cnt = dist[seg]
        roi = roi_estimates[seg]
        rev = user_summary[user_summary['segment_operation'] == seg]['total_amount'].sum()
        size = np.sqrt(rev) / 20
        ax.scatter(roi, cnt, s=size * 15, c=_get_segment_color(seg),
                   alpha=0.7, edgecolors='white', linewidth=1.5, label=seg)
        ax.annotate(seg, (roi, cnt), textcoords="offset points", xytext=(8, 4),
                    fontsize=8, fontweight='bold', color='#333')

    ax.axvline(x=1.0, color='#999', linestyle=':', linewidth=1.5)
    ax.axhline(y=user_summary['segment_operation'].value_counts().median(),
               color='#999', linestyle=':', linewidth=1.5)

    ax.set_xlabel('预估 ROI (倍)', fontsize=11)
    ax.set_ylabel('用户数', fontsize=11)
    ax.set_title('运营策略矩阵 (气泡 = 营收贡献)', fontsize=14, fontweight='bold')
    ax.axvline(x=1.0, color='#E74C3C', linestyle='--', linewidth=1.5, alpha=0.5, label='ROI=1 盈亏线')
    ax.legend(fontsize=7, loc='upper right', framealpha=0.8)

    plt.tight_layout()
    path = CHART_DIR / '07_strategy_matrix.png'
    fig.savefig(path, dpi=150, bbox_inches='tight', facecolor='#F8F9FA')
    plt.close(fig)
    logger.info("已保存: %s", path)


# ================================================================
# 图8: 10组统一配色饼图
# ================================================================
def plot_segment_overview(user_summary: pd.DataFrame) -> None:
    """10组饼图 — 统一配色 + 标注小占比组"""
    dist = user_summary['segment_operation'].value_counts()
    segs = sorted(dist.index, key=_segment_sort_key)
    counts_sorted = [dist[s] for s in segs]
    colors_sorted = [_get_segment_color(s) for s in segs]
    total = sum(counts_sorted)

    fig, ax = plt.subplots(figsize=(12, 8))
    fig.patch.set_facecolor('#F8F9FA')
    ax.set_facecolor('#FFFFFF')

    threshold = 0.03 * total
    small_mask = [c < threshold for c in counts_sorted]
    explode = [0.08 if m else 0.02 for m in small_mask]

    wedges, texts, autotexts = ax.pie(counts_sorted, labels=segs, autopct='%1.1f%%',
                                       colors=colors_sorted, explode=explode,
                                       pctdistance=0.75, labeldistance=1.08,
                                       wedgeprops={'edgecolor': 'white', 'linewidth': 2},
                                       textprops={'fontsize': 9})
    for t in autotexts:
        t.set_fontsize(9)
        t.set_fontweight('bold')
    for i, (txt, cnt) in enumerate(zip(texts, counts_sorted)):
        if cnt / total < 0.03:
            txt.set_fontweight('bold')

    ax.set_title('10大运营组分布 (统一配色)', fontsize=14, fontweight='bold', pad=15)
    plt.tight_layout()
    path = CHART_DIR / '08_segment_overview.png'
    fig.savefig(path, dpi=150, bbox_inches='tight', facecolor='#F8F9FA')
    plt.close(fig)
    logger.info("已保存: %s", path)
