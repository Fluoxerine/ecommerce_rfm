# V1: 初始版本 (2026-04-29)

本目录保存了项目的**第一版实现**，用于展示分析方法的演进过程。

## V1 vs V2 关键变化

| 维度 | V1 (本目录) | V2 (当前版本) |
|------|------------|--------------|
| **分群粒度** | 7 运营组 | 10 运营组 |
| **代码结构** | 单体脚本 `data_cleaning.py` (单文件) | 6 模块拆分 (config → loader → cleaning → analysis → visualization → import) |
| **品类分析** | 绝对金额排名 | TGI 指数 (Target Group Index) |
| **统计检验** | 基础 t检验 | t检验 + ANOVA + Kruskal-Wallis + Tukey HSD + Cohen's d + 功效分析 |
| **数据存储** | 仅 CSV 文件 | MySQL 8.4 (Docker) + 星型模型 |
| **可视化** | Matplotlib 静态图 | Matplotlib + Power BI 6页交互式仪表板 |
| **测试** | 无 | pytest 单元测试 + GitHub CI |

## 7组→10组：为什么拆分？

V1 中 3 个运营组内部差异过大，无法执行统一策略：

- **"唤醒沉睡人群" (6 类)** → 拆为 **唤醒高潜** + **唤醒普通**
- **"活跃一次性新客" (3 类)** → 拆为 **高潜新客** + **普通新客**
- **"流失低价值低效" (4 类)** → 拆为 **流失可弃** + **流失低潜**

详见 [RFM划分.md](RFM划分.md) 查阅原始 7 组映射逻辑。

## 文件说明

| 文件 | 描述 |
|------|------|
| `2026-04-25-ecommerce-rfm-plan.md` | 原始项目计划书 |
| `RFM划分.md` | 7 组运营方案完整文档（19 基础类→7 运营组） |
| `电商 RFM 阈值划分参考.md` | RFM 方法论研究笔记（行业基准/分箱法对比） |
| `data_cleaning_v1.py` | V1 单体清洗脚本（对比 V2 模块化重构） |
| `strategy_v1.md` | V1 运营策略与 ROI 预估 |
| `segmentation_comparison.png` | 分群方法对比可视化 |
| `segmentation_result.png` | V1 分群结果分布 |
| `kmeans_clusters_detail.png` | K-Means 聚类探索（曾评估后被放弃） |
| `rfm_dashboard.png` | V1 基础 RFM 仪表板 |
| `rule_stats.csv` / `kmeans_stats.csv` | 分群统计数据 |
