# 技术架构

## 数据链路

```
┌─────────────┐       ┌──────────────────┐       ┌─────────────────┐
│  data/*.csv │────▶│ Python (Pandas)   │────▶│ output/*.csv    │
│  原始数据   │       │ 清洗 + EDA + RFM  │      │ 清洗后数据       │
└─────────────┘       └──────────────────┘       └────────┬────────┘
                                                          │
                                                  LOAD DATA INFILE
                                                          │
                                                          ▼
                                                 ┌─────────────────┐
                                                 │ MySQL 8.4       │
                                                 │ (Docker mysql84)│
                                                 │ ecommerce_rfm   │
                                                 └────────┬────────┘
                                                          │
                                                 ┌────────┴────────┐
                                                 ▼                 ▼
                                        ┌──────────────┐  ┌──────────────┐
                                        │ SQL RFM 计算 │  │ SQL TGI 分析 │
                                        │ 03_*.sql     │  │ 04_*.sql     │
                                        └──────┬───────┘  └──────┬───────┘
                                               │                 │
                                               ▼                 ▼
                                     ┌──────────────────────────────────┐
                                     │ dws_customer_category_pref       │
                                     │ 运营触达清单 (05_*.sql)           │
                                     └──────────────┬───────────────────┘
                                                    │
                                                    ▼
                                     ┌──────────────────────────────────┐
                                     │ Power BI Dashboard               │
                                     │ 5 页面: 总览/画像/分群/品类/策略  │
                                     └──────────────────────────────────┘
```

## 环境要求

| 组件             | 版本         | 用途                |
| ---------------- | ------------ | ------------------- |
| Python           | 3.10+        | 数据处理和分析      |
| MySQL            | 8.4 (Docker) | 数据存储和 SQL 分析 |
| Power BI Desktop | 最新版       | 可视化仪表板        |
| Docker           | 最新版       | MySQL 容器管理      |

## Python 模块设计

```
main.py                     # 入口：编排整个分析流程
├── config.py               # 全局配置（路径、阈值、颜色）
├── data_loader.py          # 数据加载 + 分析日期确定
├── data_cleaning.py        # 订单清洗 + 用户汇总
├── rfm_analysis.py         # EDA + RFM评分 + 分群 + 统计检验
└── visualization.py        # 8张图表（RFM仪表板、清洗漏斗、散点、营收贡献、TGI热力图、气泡、策略矩阵、分组概览）
```

## SQL 脚本执行顺序

```
01_create_tables.sql        # 建表（含索引 + order_items 事实表）
02_load_data.sql            # 导入 CSV 到 MySQL（含 order_items.csv）
03_rfm_calculation.sql      # RFM 评分计算
04_category_tgi.sql         # TGI 品类/品牌偏好分析
05_operational_list.sql     # 运营触达清单
```

注意：Python `main.py` 已在本地完成 RFM 计算并输出 CSV，SQL 版本作为备选和 MySQL 侧验证。`order_items` 表是 TGI 分析的必需依赖，`04_category_tgi.sql` 和 `05_operational_list.sql` 都依赖它。

## 设计决策记录

| 决策         | 选择                         | 备选方案                | 选择理由                                         |
| ------------ | ---------------------------- | ----------------------- | ------------------------------------------------ |
| 数据库       | MySQL 8.4 Docker             | 本地 MySQL / PostgreSQL | 环境隔离，版本可控                               |
| M 分位数计算 | Python 端（Pandas quantile） | SQL 端（NTILE）         | Python 端更精确，SQL 端作为 MySQL 侧补充         |
| 可视化       | Matplotlib + Power BI        | Plotly / Seaborn        | Matplotlib 做探索性图表，Power BI 做交互式仪表板 |
| 分群标签     | Python + SQL 双写            | 仅 Python               | 确保 Python 输出 CSV 和 MySQL 查询结果一致       |
