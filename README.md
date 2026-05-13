# 电商用户价值分析与精细化运营策略

> **从数据清洗到运营策略，覆盖完整数据分析链路的端到端项目。** 基于 RFM 模型将 1,803 名用户划分为 10 个可运营客群，结合 TGI 品类偏好分析输出差异化策略，预估 ROI **8.2:1**。

[![Python](https://img.shields.io/badge/Python-3.13+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![MySQL](https://img.shields.io/badge/MySQL-8.4-4479A1?logo=mysql&logoColor=white)](https://www.mysql.com/)
[![Power BI](https://img.shields.io/badge/Power%20BI-Report-F2C811?logo=power-bi&logoColor=black)](https://powerbi.microsoft.com/)
[![Docker](https://img.shields.io/badge/Docker-Container-2496ED?logo=docker&logoColor=white)](https://www.docker.com/)
[![pandas](https://img.shields.io/badge/pandas-Data-150458?logo=pandas&logoColor=white)](https://pandas.pydata.org/)
[![SciPy](https://img.shields.io/badge/SciPy-Stats-8CAAE6?logo=scipy&logoColor=white)](https://scipy.org/)
[![pytest](https://img.shields.io/badge/test-pytest-0A9EDC?logo=pytest&logoColor=white)](https://pytest.org/)
[![License](https://img.shields.io/badge/license-MIT-green)](./LICENSE)

![RFM Dashboard](output/charts/01_rfm_dashboard.png)

## 核心成果速览

| 指标 | 数值 |
|------|------|
| 分析用户 | 10,000 注册用户 → 1,803 有效用户 |
| 客群数量 | 19 基础 RFM 类 → **10 可运营组** |
| 预估增量收入 | **72,000 元** |
| 运营成本 | 8,730 元 |
| **整体 ROI** | **8.2 : 1** |
| Power BI 仪表板 | 6 页交互式报告 |

## 各组运营策略与 ROI

> 完整方法论与敏感性分析见 [operations/strategy.md](operations/strategy.md)

### 总体 ROI 汇总

| 运营组 | 人数 | 触达 | 响应率 | 激活 | 增量收入 | 成本 | ROI | 建议 |
|--------|------|------|--------|------|----------|------|-----|------|
| 至尊VIP | 130 | 130 | 23% | 30 | ¥44,600 | ¥380 | **117:1** | ✅ 全力投入 |
| 核心高价值忠诚用户 | 16 | 16 | 20% | 3 | ¥2,000 | ¥170 | **11.8:1** | ✅ 全力投入 |
| 高潜新客 | 59 | 59 | 18% | 11 | ¥6,700 | ¥710 | **9.4:1** | ✅ 投入 |
| 唤醒高潜 | 75 | 75 | 9% | 7 | ¥3,300 | ¥450 | **7.3:1** | ✅ 投入 |
| 活跃复购潜力用户 | 23 | 23 | 25% | 6 | ¥1,300 | ¥230 | **5.7:1** | ✅ 投入 |
| 流失高潜用户 | 64 | 64 | 8% | 5 | ¥2,000 | ¥580 | **3.4:1** | ✅ 投入 |
| 流失低潜 | 539 | 539 | 2% | 11 | ¥3,200 | ¥1,620 | **2.0:1** | ⚠️ 季度触达 |
| 唤醒普通 | 455 | 455 | 5% | 23 | ¥5,100 | ¥2,510 | **2.0:1** | ⚠️ 控成本 |
| 普通新客 | 216 | 216 | 12% | 26 | ¥3,800 | ¥2,080 | **1.8:1** | ⚠️ AB测试 |
| 流失可弃 | 226 | 0 | — | — | — | — | — | ❌ 放弃 |
| **合计** | **1,803** | **1,577** | — | **122** | **¥72,000** | **¥8,730** | **8.2:1** | — |

### 预算分配：P0+P1 用 29% 预算贡献 83% 收入

```
P0 (VIP+核心忠诚+高潜新客+复购潜力):  ¥1,490 (17%) → 贡献 ¥54,600 收入 (76%)
P1 (唤醒高潜+流失高潜):              ¥1,030 (12%) → 贡献 ¥5,300 收入 (7%)
P2 (普通新客):                       ¥2,080 (24%) → 贡献 ¥3,800 收入 (5%)
P3 (唤醒普通+流失低潜):              ¥4,130 (47%) → 贡献 ¥8,300 收入 (12%)

→ P0+P1 只用 29% 预算，贡献 83% 收入  → 资源聚焦高价值客群
→ P2+P3 用 71% 预算但收入仅占 17%   → 需要 AB 测试优化策略后再规模化
```

### 各组策略概要

| 组别 | 特征 | TGI 偏好 | 策略核心 |
|------|------|----------|---------|
| **至尊VIP** | M>¥1,971, 均M=¥2,975 | Electronics(143) | 电子首发通知 + 品牌日专属折扣 + 专属客服 |
| **核心高价值忠诚** | R<60天, F≥2, M>P75 | Groceries(186), Home(154) | 日用品订阅制 + 会员升级 + 复购券 |
| **活跃复购潜力** | R<60天, F≥2, M<P75 | Books(228), Sports(173) | 品类券 + 交叉销售(运动→运动电子) |
| **高潜新客** | R<60天, F=1, M>P75 | — | 7天专属跟进 + 配套推荐 + VIP升级路径 |
| **普通新客** | R<60天, F=1, M<P75 | — | 复购提醒 + 品类教育邮件 + 首单满减券 |
| **唤醒高潜** | R61-180天, F≥2, M>P25 | Pet Supplies(149) | 定向邮件 + 限时折扣(30天有效) |
| **唤醒普通** | R61-180天, F=1/M低 | — | 最低成本触达(纯邮件/无券) + 大促通知 |
| **流失高潜** | R>180天, F≥2, M>P25 | Books(153), Beauty(150) | 邮件+SMS双触达 + Books/Sports强激励 |
| **流失可弃** | R>180天, F=1, M=¥63 | — | **主动放弃** — ROI < 0.5:1 |
| **流失低潜** | R>180天, 其他 | — | P4季度触达 + 最低成本(仅大促被动覆盖) |

## 技能展示

| 领域 | 具体技能 |
|------|---------|
| **数据清洗** | Python (Pandas) — 异常值处理、日期验证、订单状态过滤、数据质量报告 |
| **统计分析** | SciPy — t检验、ANOVA、Kruskal-Wallis、Tukey HSD 事后检验、Cohen's d 效应量、样本量功效分析 |
| **用户分群** | RFM 模型 — 分位数阈值选择、19 基础类 → 10 运营组映射 |
| **品类分析** | TGI (Target Group Index) — 替代绝对金额排名，发掘差异化品类偏好 |
| **ROI 预估** | 响应率乘数模型 + 三档敏感性分析 + 行业基准对标 |
| **数据建模** | MySQL 8.4 — 星型模型设计、DWD/DWS 分层、索引优化 |
| **可视化** | Matplotlib (8 张图表) + Power BI (6 页交互式仪表板) |
| **工程化** | Docker 环境隔离、pytest 单元测试、GitHub CI、python-dotenv 配置管理 |

## 业务问题

电商平台面临两个核心挑战：

1. **运营资源分配粗放**：对所有用户无差别推送，高价值用户触达不足，低价值用户过度触达浪费预算
2. **品类策略缺乏差异化**：不清楚不同客群的品类偏好差异，所有用户收到相同的推荐

本项目的目标：将用户划分为可独立运营的客群，输出基于品类偏好的差异化策略，并预估运营 ROI。

## 分析链路

```
原始 CSV → Python 清洗 & EDA → RFM 分群 (19类→10组) → MySQL 入库
    → SQL TGI 品类偏好分析 → 可视化 → 运营策略 + ROI 预估
```

## Power BI 仪表板

> 完整 6 页交互式报告，从客群概览到运营落地的全链路可视化。  
> 下载 [rfm.pdf](powerbi/rfm.pdf) 查看完整 PDF 导出。

### 第 1 页：RFM 客群概览

![Page 1](powerbi/rfm_页面_1.png)

KPI 卡片（总用户/总营收/人均消费）+ RFM 三维散点图 + 10 运营组分布。

### 第 2 页：用户画像

![Page 2](powerbi/rfm_页面_2.png)

性别分布、城市矩阵、平均客单价按客群对比——识别高价值用户的人口特征。

### 第 3 页：RFM 客群明细

![Page 3](powerbi/rfm_页面_3.png)

可筛选用户明细表 + R/F/M 分数切片器——支持运营人员按条件检索具体用户。

### 第 4 页：TGI 品类偏好

![Page 4](powerbi/rfm_页面_4.png)

品类 × 客群 TGI 热力图 + 品牌堆叠柱状图——发掘各客群的差异化品类/品牌偏好。

### 第 5 页：VIP 专属分析

![Page 5](powerbi/rfm_页面_5.png)

VIP 客群的 ARPU、品类偏好、城市分布、性别比例——高价值用户深度洞察。

### 第 6 页：运营策略落地

![Page 6](powerbi/rfm_页面_6.png)

10 组触达优先级排序 + 运营清单——从分析到执行，直接落地。

## 核心可视化成果

### 分群结果（10 运营组）

![Segmentation Overview](output/charts/08_segment_overview.png)

### TGI 品类偏好洞察

改用 TGI 后发现的差异化偏好（TGI > 120 表示该组对该品类偏好显著高于平均）：

| 运营组 | TOP1 TGI 品类 | TGI | 运营含义 |
|--------|-------------|-----|---------|
| 至尊VIP | Electronics | 143 | 集中消费电子，回避家居/运动 |
| 核心高价值忠诚用户 | Groceries | 186 | 复购驱动力是日用品和家居 |
| 活跃复购潜力用户 | Books | 228 | 低价高频品类驱动复购 |
| 流失高潜用户 | Books | 153 | 与复购潜力品类偏好重叠，统计检验不支持"同群不同期"假说 |
| 唤醒高潜 | Pet Supplies | 149 | 宠物+日用品偏好，沉睡前的活跃品类 |

![TGI Heatmap](output/charts/05_tgi_heatmap.png)

### RFM 散点分析

![RFM Scatter](output/charts/03_rfm_scatter.png)

### 营收贡献

![Revenue Contribution](output/charts/04_revenue_contribution.png)

### 运营策略矩阵

![Strategy Matrix](output/charts/07_strategy_matrix.png)

## 项目结构

<details>
<summary>点击展开完整目录结构</summary>

```
├── README.md
├── requirements.txt
├── requirements-dev.txt
├── .env.example
├── .github/workflows/ci.yml
├── data/                             # 原始 CSV（模拟数据）
├── python/                           # 分析脚本（模块化）
│   ├── config.py                     #   配置 + 日志 + 环境变量
│   ├── data_loader.py                #   数据加载
│   ├── data_cleaning.py              #   数据清洗
│   ├── rfm_analysis.py               #   EDA + RFM 评分 + 统计检验
│   ├── visualization.py              #   8 张可视化图表
│   ├── import_to_mysql.py            #   MySQL 导入 + Power BI 导出
│   └── main.py                       #   主入口
├── sql/                              # 数据库脚本
│   ├── 01_create_tables.sql          #   建表
│   ├── 02_load_data.sql              #   数据导入
│   ├── 03_rfm_calculation.sql        #   RFM 计算
│   ├── 04_category_tgi.sql           #   TGI 品类偏好分析
│   └── 05_operational_list.sql       #   运营触达清单
├── operations/
│   └── strategy.md                   # 10 运营组策略 + ROI 预估（完整版）
├── docs/                             # 项目文档
│   ├── 01-background.md
│   ├── 02-data-dictionary.md
│   ├── 03-methodology.md
│   ├── 04-results.md
│   ├── 05-architecture.md
│   ├── 06-roi-benchmarks.md
│   └── comprehensive-review.md
├── powerbi/                          # Power BI 项目
│   ├── rfm.pbip
│   ├── rfm.Report/                   # 报表定义 (PBIR)
│   ├── rfm.SemanticModel/            # 数据模型 (TMDL)
│   └── build_dashboard_guide.md
├── previous_iteration/               # V1 历史版本
│   ├── README.md                     #   演进说明
│   ├── RFM划分.md                    #   7 组方案文档
│   ├── data_cleaning_v1.py           #   V1 单体脚本
│   ├── strategy_v1.md                #   V1 运营策略
│   └── ...                           #   V1 图表与数据
├── tests/                            # 单元测试
└── output/                           # 输出
    └── charts/                       # 8 张可视化图表
```

</details>

## 技术栈

| 环节 | 工具 |
|------|------|
| 数据处理 | Python 3.13+ + Pandas + NumPy |
| 统计分析 | SciPy（t检验、ANOVA、Kruskal-Wallis、Tukey HSD、Cohen's d） |
| 可视化 | Matplotlib + Power BI |
| 数据存储 | MySQL 8.4 (Docker) |
| 分析方法 | RFM 模型 + TGI（Target Group Index） |
| 配置管理 | python-dotenv |
| 测试 | pytest + pytest-cov |
| 代码检查 | ruff |

## 快速开始

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 将原始 CSV（users.csv, orders.csv, order_items.csv, products.csv）放入 data/ 目录

# 3. 运行分析（数据清洗 + RFM 分群 + 可视化）
python python/main.py

# 4. 配置 MySQL 连接
cp .env.example .env
# 编辑 .env 填写 MYSQL_PASSWORD

# 5. 导入 MySQL 并导出 Power BI 数据（需要 Docker mysql84 容器运行中）
python python/import_to_mysql.py

# 6. 执行 TGI 品类分析
docker exec -i mysql84 mysql -h 127.0.0.1 -u root -p ecommerce_rfm < sql/04_category_tgi.sql

# 7. 生成运营触达清单
docker exec -i mysql84 mysql -h 127.0.0.1 -u root -p ecommerce_rfm < sql/05_operational_list.sql

# 8. 运行测试
pip install -r requirements-dev.txt
pytest tests/ -v
```

## 数据说明

本项目使用**模拟生成的电商交易数据**。原始数据规模：

| 文件 | 记录数 | 说明 |
|------|--------|------|
| users.csv | 10,000 | 注册用户 |
| orders.csv | 20,000 | 原始订单（completed 约占 20%） |
| order_items.csv | 43,525 | 订单明细 |
| products.csv | 2,000 | 商品 |

清洗后有效用户约 1,803 人（仅保留有 completed 订单的用户）。分析框架完全适用于真实数据——替换数据源即可复用整个 Pipeline。

## 关键设计决策

| 决策 | 选择 | 理由 |
|------|------|------|
| F 分 2 档而非 3 档 | 1次 / 2+次 | 87.5% 用户仅购 1 次，分 3 档后档位几乎为空 |
| M 使用分位数而非固定金额 | P25/P75 | 用户消费能力是相对的，分位数消除极端值影响 |
| TGI 替代绝对金额排名 | TGI > 120 为偏好 | 绝对金额反映的是品类结构，TGI 反映的是客群差异 |
| 7 组拆分为 10 组 | 运营粒度提升 | 原方案中 3 个组内部差异过大，无法执行统一策略 |
| K-Means 弃用 | 选用分位数规则法 | 聚类结果可解释性差，不利于运营团队理解和执行 |
| ROI 三档敏感性 | 乐观/基准/悲观 | 乘数模型参数未经校准，敏感性覆盖不确定性 |
| MySQL 8.4 + Docker | 环境隔离 | 可复现的环境，避免本地 MySQL 版本差异 |
| 凭据管理 | .env 文件 | 密码不进入代码仓库，安全性保障 |

## 项目迭代历程

本项目历经 5 个阶段，从单体脚本演进为完整的分析工程。

### Phase 1: 探索与 V1 实现 (Apr 25–29)

![V1 Segmentation](previous_iteration/segmentation_result.png)

- 研究 RFM 阈值方法论：对比**业务规则法、分位数法、均值比较法、K-Means 聚类法** 4 种方案
- 选择分位数法作为基础，确定 R(60/180天)、F(1/2+次)、M(P25/P75/IQR离群值) 阈值
- 实现 **19 基础 RFM 类 → 7 运营组** 的初版分群
- 单体 Python 脚本完成数据清洗到可视化全流程
- 同步探索 K-Means 聚类效果（后弃用，可运营性不如规则法）

> 详见 [previous_iteration/](previous_iteration/) 查看 V1 完整代码与文档

### Phase 2: 重构与基础设施 (May 7)

- **代码模块化拆分**：单体脚本 → 6 个独立模块 (config / data_loader / data_cleaning / rfm_analysis / visualization / import_to_mysql)
- **MySQL 8.4 数据仓库**：Docker 容器化部署，星型模型设计 (DIM 维度层 + DWD 明细层 + DWS 汇总层)
- **Power BI PBIP 项目**初始化，建立 TMDL 语义模型
- 解决数据库字符集编码问题 (utf8mb4)

### Phase 3: Power BI 仪表板 (May 9)

![Power BI Dashboard](output/charts/08_segment_overview.png)

- 完成 **6 页交互式 Power BI 报告**：
  - RFM 概览 (KPI 卡片 + 散点图)
  - 用户画像 (性别/城市/客单价分布)
  - RFM 客群明细 (可筛选用户列表)
  - TGI 品类偏好 (热力图 + 堆叠柱状图)
  - VIP 专属分析 (ARPU/品类/城市)
  - 运营策略落地页 (触达清单 + 优先级)

### Phase 4: 自我评审与深度优化 (May 11–12)

- **7 组 → 10 组拆分**：对 V1 中内部差异过大的 3 个组进行拆解

| 原 7 组 | 拆分后 10 组 | 拆分原因 |
|---------|-------------|---------|
| 唤醒沉睡人群 (6 类合并) | 唤醒高潜 + 唤醒普通 | 复购与一次性用户运营成本差异 3-5 倍 |
| 活跃一次性新客 (3 类合并) | 高潜新客 + 普通新客 | M 高价值 vs 中低价值需要不同首单策略 |
| 流失低价值低效 (4 类合并) | 流失可弃 + 流失低潜 | 中高 M 流失用户仍有挽回价值 |

- **TGI 替代绝对金额排名**：原分析显示"所有组的 TOP1 品类都是 Electronics"——无运营区分度。改用 TGI 后各群差异化偏好清晰可见

- **统计检验增强**：
  - VIP vs 流失低潜 M 值差异：t=45.54, p<0.001, Cohen's d=4.45 (大效应量)
  - 各组 R 值 ANOVA：F=377.96, p<0.001, η²=0.65 (大效应量)
  - 各组 M 值 Kruskal-Wallis：H=964.58, p<0.001
  - Tukey HSD 事后检验：45 对中 39 对差异显著

- **样本量功效分析**：识别小样本组（如"核心高价值忠诚用户"仅 16 人，仅能检出 d≥1.02 的大效应量），给出数据积累建议

### Phase 5: 工程整理与展示 (May 13)

- 文件夹结构整合，历史版本归档
- 隐私安全检查（密码清洗、敏感文件排除）
- README 优化，GitHub 作品集发布

## License

MIT
