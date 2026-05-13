# 电商用户价值分析与精细化运营策略

[![Python](https://img.shields.io/badge/Python-3.13+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![MySQL](https://img.shields.io/badge/MySQL-8.4-4479A1?logo=mysql&logoColor=white)](https://www.mysql.com/)
[![Power BI](https://img.shields.io/badge/Power%20BI-Report-F2C811?logo=power-bi&logoColor=black)](https://powerbi.microsoft.com/)
[![Docker](https://img.shields.io/badge/Docker-Container-2496ED?logo=docker&logoColor=white)](https://www.docker.com/)
[![pandas](https://img.shields.io/badge/pandas-Data-150458?logo=pandas&logoColor=white)](https://pandas.pydata.org/)
[![SciPy](https://img.shields.io/badge/SciPy-Stats-8CAAE6?logo=scipy&logoColor=white)](https://scipy.org/)
[![pytest](https://img.shields.io/badge/test-pytest-0A9EDC?logo=pytest&logoColor=white)](https://pytest.org/)
[![License](https://img.shields.io/badge/license-MIT-green)](./LICENSE)

基于 RFM 模型 + TGI 品类偏好分析的端到端用户分群项目。从数据清洗到策略输出，覆盖完整的数据分析链路。

![RFM Dashboard](output/charts/01_rfm_dashboard.png)

## 技能展示

| 领域 | 具体技能 |
|------|---------|
| **数据清洗** | Python (Pandas) — 异常值处理、日期验证、订单状态过滤、数据质量报告 |
| **统计分析** | SciPy — t检验、ANOVA、Kruskal-Wallis、Tukey HSD 事后检验、Cohen's d 效应量 |
| **用户分群** | RFM 模型 — 分位数阈值选择、19 类基础分群 → 10 运营组映射 |
| **品类分析** | TGI (Target Group Index) — 替代绝对金额排名，发掘差异化品类偏好 |
| **数据建模** | MySQL 8.4 — 星型模型设计、DWD/DWS 分层、索引优化 |
| **可视化** | Matplotlib (8 张图表) + Power BI (6 页交互式仪表板) |
| **工程化** | Docker 环境隔离、pytest 单元测试、GitHub CI、python-dotenv 配置管理 |
| **商业洞察** | 运营策略制定、ROI 预估 (8.2:1)、客群触达优先级排序 |

## 业务问题

电商平台面临两个核心挑战：
1. **运营资源分配粗放**：对所有用户无差别推送，高价值用户触达不足，低价值用户过度触达浪费预算
2. **品类策略缺乏差异化**：不清楚不同客群的品类偏好差异，所有用户收到相同的推荐

本项目的目标：将用户划分为可独立运营的客群，输出基于品类偏好的差异化策略，并预估每组的运营 ROI。

## 分析链路

```
原始 CSV → Python 清洗 & EDA → RFM 分群 (19类→10组) → MySQL 入库
    → SQL TGI 品类偏好分析 → 可视化 → 运营策略 + ROI 预估
```

## 项目结构

```
├── README.md
├── requirements.txt                  # 生产依赖（固定版本）
├── requirements-dev.txt              # 开发依赖
├── .env.example                      # 环境变量模板
├── .github/workflows/ci.yml          # CI 配置
├── data/                             # 原始 CSV（模拟电商数据，10,000用户/20,000订单）
├── python/                           # 分析脚本（模块化拆分）
│   ├── config.py                     #   配置常量 + 日志 + 环境变量
│   ├── data_loader.py                #   数据加载
│   ├── data_cleaning.py              #   数据清洗
│   ├── rfm_analysis.py               #   EDA + RFM 评分 + 统计检验
│   ├── visualization.py              #   8张可视化图表
│   ├── import_to_mysql.py            #   MySQL 导入 + Power BI 导出
│   └── main.py                       #   主入口
├── sql/                              # 数据库脚本
│   ├── 01_create_tables.sql          #   建表（含索引 + order_items表）
│   ├── 02_load_data.sql              #   数据导入
│   ├── 03_rfm_calculation.sql        #   RFM 计算（MySQL 8.4 兼容）
│   ├── 04_category_tgi.sql           #   TGI 品类/品牌偏好分析
│   └── 05_operational_list.sql       #   运营触达清单
├── operations/
│   └── strategy.md                   # 10大运营组策略 + ROI 预估
├── docs/                             # 项目文档
│   ├── 01-background.md              #   项目背景与问题定义
│   ├── 02-data-dictionary.md         #   数据字典
│   ├── 03-methodology.md             #   方法论与阈值选择依据
│   ├── 04-results.md                 #   核心发现与洞察
│   ├── 05-architecture.md            #   技术架构
│   ├── 06-roi-benchmarks.md          #   ROI 基准数据来源
│   └── comprehensive-review.md       #   全面审查报告 (2026-05-07)
├── powerbi/
│   ├── rfm.pbip                        # Power BI 项目文件
│   ├── rfm.Report/                     # 报表定义 (PBIR)
│   ├── rfm.SemanticModel/             # 数据模型 (TMDL)
│   └── build_dashboard_guide.md        # Power BI 仪表板搭建指南
├── tests/                            # 单元测试
│   ├── test_rfm_analysis.py
│   └── test_data_cleaning.py
└── output/                           # 输出（gitignored）
    ├── analysis.log                  #   运行日志
    ├── cleaned_orders.csv
    ├── cleaned_user_summary.csv
    └── charts/                       # 8张可视化图表
```

## 技术栈

| 环节 | 工具 |
|------|------|
| 数据处理 | Python 3.13+ + Pandas + NumPy |
| 统计分析 | SciPy（t检验、ANOVA、偏度） |
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

## 核心成果

### 1. 分群结果（10大运营组 vs 原7组）

将原7组中内部差异过大的3组拆分，提升可运营性：
- "唤醒沉睡人群" → 唤醒高潜 + 唤醒普通
- "活跃一次性新客" → 高潜新客 + 普通新客
- "流失低价值低效" → 流失可弃 + 流失低潜

### 2. TGI 品类偏好洞察（替代绝对金额排名）

原分析显示"所有组的 TOP1 品类都是 Electronics"——这在运营上无区分度。

改用 TGI 后发现的差异化偏好：

| 运营组 | TOP1 TGI 品类 | TGI | 运营含义 |
|--------|-------------|-----|---------|
| 至尊VIP | Electronics | 143 | 集中消费电子，回避家居/运动 |
| 核心高价值忠诚用户 | Groceries | 186 | 复购驱动力是日用品和家居 |
| 活跃复购潜力用户 | Books | 228 | 低价高频品类驱动复购 |
| 流失高潜用户 | Books | 153 | 与复购潜力品类偏好重叠，统计检验不支持"同群不同期"假说 |
| 唤醒高潜 | Pet Supplies | 149 | 宠物+日用品偏好，沉睡前的活跃品类 |

### 3. ROI 预估

| 指标 | 数值 |
|------|------|
| 触达用户 | 1,803 人 |
| 有效运营用户 | 1,577 人（排除不触达组） |
| 预估激活 | 122 人 |
| 预估增量收入 | 72,000 元 |
| 运营成本 | 8,730 元 |
| **整体 ROI** | **8.2 : 1** |

详见 [operations/strategy.md](operations/strategy.md)

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
| 7组拆分为10组 | 运营粒度提升 | 原方案中 3 个组内部差异过大，无法执行统一策略 |
| MySQL 8.4 + Docker | 环境隔离 | 可复现的环境，避免本地 MySQL 版本差异 |
| 凭据管理 | .env 文件 | 安全性：密码不进入代码仓库 |

## License

MIT
