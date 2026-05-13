# 项目全面审查报告

## 审查日期：2026-05-07

---

## 项目概要

电商用户价值分析与精细化运营策略 — 基于 RFM + TGI 的端到端用户分群分析 pipeline。代码量约 1,500 行（Python + SQL），配套 6+ 篇文档。

---

## 一、完整性评估

### 优点

- **端到端的分析链路完整**：原始 CSV → 数据清洗 → RFM 分群 → TGI 分析 → 策略 → 可视化 → Power BI，链路清晰
- **Python + SQL 双路径**：核心逻辑在两端各实现一次，互为验证，降低单一实现出错风险
- **文档齐全**：项目背景、数据字典、方法论、结果洞察、技术架构、ROI 基准共 6 篇，且均有实质性内容
- **8 张可视化图表**：覆盖仪表板、清洗漏斗、散点矩阵、营收贡献、TGI 热力图、气泡图、策略矩阵、分组饼图
- **运营输出完整**：10 组差异化策略、三档 ROI 预估、SQL 触达清单、Power BI 仪表板搭建指南
- **输出文件齐全**：清洗后 CSV、Power BI 维度数据均已生成

### 问题

| 严重度 | 问题 | 位置 | 影响 |
|--------|------|------|------|
| **严重** | `order_items` 表未建表但被多条 SQL 引用 | `sql/01_create_tables.sql` — 只建了 `dim_order` 和 `dwd_user_order_detail`，没有建 `order_items` 表；`sql/04_category_tgi.sql` 直接 `FROM order_items` | SQL TGI 管道完全无法运行 |
| **严重** | `order_items.csv` 未被导入 MySQL | `sql/02_load_data.sql` — 没有对应的 `LOAD DATA INFILE` 语句 | MySQL 侧缺少核心事实表 |
| **高** | `events.csv` 和 `reviews.csv` 存在于父级 data 目录但未被项目引用 | — | 可用于用户行为分析的额外数据未利用 |

---

## 二、逻辑一致性评估

### 优点

- **RFM 阈值选择完全由数据驱动**：F 分 2 档有 95% 用户仅购 1 次的数据支撑；R 阈值有多组对比分析；M 用分位数而非固定金额消除极端值影响
- **TGI 方法正确应用**：识别到绝对金额排名无区分度（所有组 TOP1 都是 Electronics），改用 TGI 后发现了差异化偏好
- **7 组 → 10 组拆分有理有据**：3 个原组内部差异用量化指标说明。功效分析显示：最大组流失低潜(539人)可检测 d≥0.17，最小组核心高价值忠诚(16人)仅能检测 d≥1.02（仅大效应量）；活跃复购潜力(23人)可检测 d≥0.84。详见 Python 输出"样本量功效分析"及 docs/04-results.md 功效分析表
- **统计检验**：t 检验（VIP vs 流失低潜消费金额差异）+ ANOVA（各组 R 值）+ Kruskal-Wallis（各组 M 值）+ Tukey HSD 事后检验 + "同群不同期"假说验证。注意：t 检验最初仅覆盖了 VIP vs 流失低潜一组比较，其余 44 对组间比较在修订中通过 Tukey HSD 补齐
- **Python 与 SQL 的分群逻辑一致**（已交叉验证两端的 CASE WHEN 逻辑）
- **流失高潜 vs 活跃复购潜力的 TGI 偏好高度相似**（Books/Sports/Beauty），但统计检验显示两组的 M 值差异显著（t=−3.11, Bonferroni校正p=0.0075, d=−0.76）——"同群不同期"假说不被数据支持，两组更可能是偏好相似但消费能力不同的用户

### 问题

| 严重度 | 问题 | 位置 | 说明 |
|--------|------|------|------|
| **高** | `plot_cleaning_funnel` 数据不准确 | `python/visualization.py:162-203` | `after_amount` 直接使用了 `completed` 的值（仅过滤了状态），金额>0 过滤的丢弃量未计入，漏斗图该步骤始终显示丢弃 0 条 |
| **高** | `cleaned_user_summary.csv` 实际用户数为 1,803（非 README 所称 10,000） | — | 82% 注册用户无有效 completed 订单，文档应明确说明此筛选率 |
| **中** | ROI 策略文档与 `config.py` 的参数不一致 | `operations/strategy.md` vs `python/config.py:73-86` | 邮件基准响应率数值不同：config 用 3%/8%/18%，strategy 文档用 2-5%/8-15%/15-30%，缺乏统一数据源 |
| **低** | `05_operational_list.sql` action 列中文含特殊字符 | `sql/05_operational_list.sql` | 含 `+`、`>`、`/` 等符号，在不同 MySQL 客户端可能出现编码差异 |
| **低** | `data_cleaning.py:32` 日期比较时 NaN 被静默丢弃 | `python/data_cleaning.py#L32` | 用户注册日期缺失时该行被 `>=` 比较自动丢弃，无警告日志 |

---

## 三、企业级就绪度评估

### 总体评分：6.0 / 10

适用于内部数据分析项目/原型，离生产系统有较大距离。

| 维度 | 得分 | 说明 |
|------|------|------|
| 代码模块化 | 8/10 | 良好的职责分离：config/data_loader/cleaner/rfm/viz/main |
| 可复现性 | 7/10 | Docker MySQL 8.4 隔离环境；但依赖版本用 `>=` 未锁定 |
| 错误处理 | 2/10 | 仅 `print` + `sys.exit(1)`，无重试/降级/异常分类 |
| 可观测性 | 1/10 | 全部 `print` 输出，无日志框架、无日志级别、无文件持久化 |
| 可测试性 | 0/10 | 零测试代码，无测试框架配置 |
| 安全性 | 2/10 | MySQL root 密码硬编码 `-p123`；`subprocess.run(shell=True)` 存在命令注入风险 |
| 配置管理 | 3/10 | 配置集中在 `config.py` 但全部硬编码，无 `.env` 支持 |
| 数据治理 | 4/10 | 有数据清洗漏斗和质量记录，但无血缘追踪、数据版本号 |
| CI/CD | 0/10 | 无任何 CI 配置文件 |
| 增量处理 | 0/10 | 仅支持全量批处理，无增量更新逻辑 |

### 关键短板详述

#### 1. 安全性问题

**硬编码密码** (`python/import_to_mysql.py:13`):
```python
MYSQL_CMD = f'docker exec {CONTAINER} mysql -h 127.0.0.1 -u root -p123 ...'
```

**Shell 注入风险** (`python/import_to_mysql.py:20-22`):
```python
result = subprocess.run(cmd, shell=True, ...)
```
当参数来自外部输入时，`shell=True` 允许命令链注入。

#### 2. 可维护性问题

- `requirements.txt` 使用 `>=` 而非 `==`，不同时间安装可能得到不同版本的依赖
- `import_to_mysql.py:140` 中 `result.stdout.strip().replace('\t', ',')` 如果数据中包含逗号将损坏 CSV 输出
- `dim_rfm_segment` 字典表的 seed 数据硬编码在 SQL 文件中，生产环境中数据字典变更需改代码
- 无类型注解，IDE 自动补全和静态检查能力受限

#### 3. 运维问题

- 无日志持久化，排查历史运行问题困难
- 无运行状态通知（成功/失败无告警）
- 分析日期由最新订单日期动态确定，无法复现历史某一天的分析结果

---

## 四、代码质量评审

### 优点
- 职责分离清晰：`config → loader → cleaner → rfm → viz → main`
- Pandas 操作娴熟，groupby/merge/quantile 使用正确
- 分群逻辑通过配置字典驱动（`OPERATION_GROUP_CONFIG`），修改规则只需改配置，体现了数据驱动设计
- 颜色方案统一管理（`SEGMENT_COLORS`），所有图表保持一致的视觉语言
- `main.py` 流程清晰，每个阶段有明确的输出标题

### 具体问题

| 位置 | 问题 | 建议 |
|------|------|------|
| `python/visualization.py:305-364` | `plot_tgi_heatmap` 在函数内部 import 依赖，异常被裸 `except Exception` 吞掉 | 将 import 移到文件顶部，失败时记录日志而非静默跳过 |
| `python/import_to_mysql.py:13` | `--local-infile=1` 重复书写 | 删除重复项 |
| `python/import_to_mysql.py:140` | TSV→CSV 简单字符串替换 | 使用 `csv` 标准库配合 `QUOTE_NONNUMERIC` |
| `python/config.py:12` | `ANALYSIS_DATE = None` 从未被实际使用 | 改为从环境变量/配置文件读取，或删除 |
| `python/visualization.py:376-378` | `np.random.seed(42)` + jitter 可复现但全局影响 | 使用局部 `RandomState` |

---

## 五、数据质量评估

### 清洗链路

| 阶段 | 记录数 | 说明 |
|------|--------|------|
| 原始订单 | 20,000 | orders.csv |
| completed | 4,021 | 过滤 15,979 条 |
| amount > 0 | ~4,021 | 过滤 ~0 条（需核实） |
| 日期正确 | ~2,048 | 过滤 ~1,973 条 |
| 最终用户 | 1,803 | 去重后 |

### 订单状态分布（原始数据）

| 状态 | 数量 | 占比 |
|------|------|------|
| shipped | 4,113 | 20.6% |
| returned | 4,066 | 20.3% |
| completed | 4,021 | 20.1% |
| cancelled | 3,920 | 19.6% |
| processing | 3,880 | 19.4% |

### 关键数据特性

- 82% 注册用户无有效 completed 订单（1,803 / 10,000）
- F 分布极偏：87.5% 用户仅 1 次购买
- M 分布右偏：均值 > 中位数，存在长尾高消费用户
- 品类消费 Pareto 分布：Electronics 占 ~40%

---

## 六、改进方案执行清单

### P0 — 阻断性修复（使项目可运行）
- [x] 创建 `order_items` 建表语句
- [x] 添加 `order_items.csv` 的数据导入语句
- [ ] 在 `dwd_user_order_detail` 中补充 item/product 关联字段（已决定不需要：dw_order_detail 仅存储清洗后订单，item 级数据已在 order_items 表中）

### P1 — 安全性修复
- [x] 移除硬编码 MySQL 密码，改用环境变量 `.env`
- [x] `subprocess.run` 参数化替代 `shell=True`
- [x] 创建 `.env.example` 文件

### P2 — 代码质量
- [x] 部分 Python 函数添加类型注解（config.py, rfm_analysis.py 主要函数已覆盖）
- [x] 用 `logging` 框架替代 `print`
- [x] 修复 `plot_cleaning_funnel` 数据不准确问题（amount 过滤现基于 completed_df 子集）
- [x] 重构 `plot_tgi_heatmap` 的脆弱 import（所有 import 已移至文件顶部）
- [x] 修复 TSV→CSV 转换 bug（使用 csv 标准库 + io.StringIO）
- [x] 锁定 `requirements.txt` 版本（使用 `==` 精确版本）
- [x] `ANALYSIS_DATE` 已接入环境变量（data_loader.py 优先读取，回退到动态确定）

### P3 — 工程化
- [x] 添加 `tests/` 目录与单元测试（2 个测试文件，17 个测试用例）
- [x] 添加 GitHub Actions CI 配置（lint + test + coverage）
- [x] 统一 ROI 参数来源（config.py 与 strategy.md 基准已对齐，range vs point estimate 是设计差异）
- [ ] 添加 `events.csv` 和 `reviews.csv` 可选的扩展分析

### 2026-05-07 新增修复
- [x] Power BI Dashboard Guide 数据源引用错误（引用了不存在的 CSV 和表名）
- [x] Power BI 导出新增 `user_profile.csv`（含 gender/city，用于 Page 2 用户画像）
- [x] Power BI 导出新增 `operational_list.csv`（含 action/priority/response_rate，用于 Page 5 策略看板）
- [x] README.md F分布数据从 "95%+" 修正为 "87.5%"
- [x] README.md TGI 表格修正"唤醒沉睡"行（原 7 组标签）为"唤醒高潜"（当前 10 组标签）

### 2026-05-11 评审问题修复
- [x] SQL `dws_customer_category_pref` 表补齐 `top3_brand` / `top3_brand_tgi` 列（原仅到 TOP2，品类已有 TOP3）
- [x] Power BI 模型 TMDL 同步增加 `top3_brand` / `top3_brand_tgi` 列定义
- [x] 统计检验扩展：增加 Kruskal-Wallis + Tukey HSD 事后检验 + 效应量（Cohen's d, η²）+ "同群不同期"假说验证 + 功效分析
- [x] `requirements.txt` 增加 `statsmodels==0.14.4` 依赖
- [x] strategy.md 乘数来源改注为定性估计（附各乘数的文献依据），增加模型形式说明（含局限性）
- [x] strategy.md 增加预算闭环对照表（¥20,000 完整分解）
- [x] strategy.md 增加 ROI 与行业基准对标表
- [x] 04-results.md 发现 4 统计检验改写为详细方法论（含检验目的和样本量说明）
- [x] comprehensive-review.md 16 人阈值表述修正为含功效分析上下文的准确描述

---

## 七、总结

这是一个**方法论正确、文档充分、分析链路完整的原型级别项目**。作为数据分析工作模板价值很高，但工程化水平不足以直接部署为生产系统。

**核心亮点**：
- 数据驱动的阈值选择，而非拍脑袋
- TGI 方法替代绝对金额排名，解决了品类推荐的"无区分度"问题
- 策略文档的 ROI 三档预估方法严谨，有行业基准支撑
- Python + SQL 双写保证了分析结果的可验证性

**核心短板**：
- SQL 管道因 `order_items` 表缺失而不可运行
- 安全硬伤（硬编码密码、shell 注入）
- 零测试、零 CI、零日志

修复以上问题后，该项目适合作为电商数据分析团队的标准分析模板。
