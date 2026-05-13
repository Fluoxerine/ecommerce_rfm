# Power BI Dashboard 搭建指南（MySQL 直连方式）

## 前置条件

1. Docker 容器 `mysql84` 已启动（端口映射 `3307→3306`）
2. Power BI Desktop 已安装
3. 确认数据库可连接：打开终端执行以下命令验证

```bash
docker exec mysql84 mysql -uroot -p123 ecommerce_rfm -e "SELECT COUNT(*) FROM dws_user_rfm;"
```

应返回 `1803`（总用户数）。

---

## 第一步：连接 MySQL 并导入数据

### 1.1 打开 Power BI Desktop，点击「获取数据」

- 启动 Power BI Desktop
- 在欢迎页点击 **获取数据**（或菜单栏：开始 → 获取数据）

### 1.2 选择 MySQL 数据库

- 在弹出窗口左侧选择 **数据库** → 右侧选择 **MySQL 数据库**
- 点击 **连接**

### 1.3 填写连接信息

在弹出的 MySQL 数据库对话框中：

| 字段   | 填写值             |
| ------ | ------------------ |
| 服务器 | `127.0.0.1:3307` |
| 数据库 | `ecommerce_rfm`  |

> **说明**：MySQL 容器内部端口为 3306，映射到宿主机的 3307 端口，所以从本机连接需使用 `127.0.0.1:3307`。

点击 **确定**。

### 1.4 输入数据库凭据

在弹出的凭据窗口中：

| 字段   | 填写值                          |
| ------ | ------------------------------- |
| 用户名 | `root`                        |
| 密码   | 保密(可在"20260507_1\.env"查看) |

点击 **连接**。

### 1.5 选择需要导入的表（6张）

在导航器中**勾选以下表**：

| 表名                           | 用途                     | 关键字段                                                                                           |
| ------------------------------ | ------------------------ | -------------------------------------------------------------------------------------------------- |
| `dws_user_rfm`               | RFM 用户分群宽表（核心） | user_id, segment_operation, order_count, total_amount, days_since_order, r_score, f_score, m_score |
| `dim_user`                   | 用户画像（性别、城市）   | user_id, gender, city                                                                              |
| `dws_customer_category_pref` | 品类/品牌 TGI 偏好汇总   | segment_operation, top1_category, top1_tgi, top1_brand 等                                          |
| `dim_product`                | 商品维度                 | product_id, category, brand, price                                                                 |
| `order_items`                | 订单明细事实表           | order_item_id, order_id, product_id, user_id, item_total                                           |
| `dim_order`                  | 订单主表                 | order_id, user_id, order_date, total_amount                                                        |

> **技巧**：可以全选 6 张表一次性导入，也可以先选 `dws_user_rfm` + `dim_user` 完成前 3 页，后续再追加。

点击 **加载**。

---

## 第二步：建立数据模型（关系）

### 2.1 打开模型视图

- 点击 Power BI 左侧边栏的 **模型** 图标（第三个）
- 你会看到 6 张表的可视化布局

### 2.2 创建表间关系

拖拽字段建立以下关系（或右键 → 管理关系 → 新建）：

```
dws_user_rfm[user_id] ←→ dim_user[user_id]        （多对一，dw方为多）
dws_user_rfm[user_id] ←→ order_items[user_id]      （一对多，dw方为一）
dws_user_rfm[user_id] ←→ dim_order[user_id]        （一对多，dw方为一）
dim_product[product_id] ←→ order_items[product_id]  （一对多，dim方为一）
```

> 如果 Power BI 自动检测到同名字段并创建了关系，请检查是否与上述一致，不一致请手动修正。

### 2.3 按 `segment_operation` 关联偏好表

`dws_customer_category_pref` 与 `dws_user_rfm` 通过 `segment_operation` 字段关联：

```
dws_user_rfm[segment_operation] ←→ dws_customer_category_pref[segment_operation]  （多对一，dw方为多）
```

---

## 第三步：创建度量值（Measures）

在 `dws_user_rfm` 表上右键 → **新建度量值**，依次创建：

```DAX
// 总用户数
Total Users = COUNTROWS(dws_user_rfm)

// 总营收
Total Revenue = SUM(dws_user_rfm[total_amount])

// 平均客单价
Avg Revenue Per User = AVERAGE(dws_user_rfm[total_amount])

// 平均订单数
Avg Order Count = AVERAGE(dws_user_rfm[order_count])

// 平均最近购买天数
Avg Recency = AVERAGE(dws_user_rfm[days_since_order])

// VIP 用户数
VIP Count = CALCULATE(COUNTROWS(dws_user_rfm), dws_user_rfm[segment_operation] = "至尊VIP")
```

---

## 第四步：逐页搭建 Dashboard（共 5 页）

### Page 1：Executive Summary（经营总览）

**目标**：一眼看清用户规模、营收和 10 大运营组分布。

| 序号 | 图表类型           | 操作步骤                                                                                                                         |
| ---- | ------------------ | -------------------------------------------------------------------------------------------------------------------------------- |
| 1    | KPI 卡片：总用户   | 右侧「可视化」窗格选**卡片** → 拖入度量值 `Total Users` → 格式面板设置标题「总用户数」                                 |
| 2    | KPI 卡片：总营收   | 同上，拖入 `Total Revenue` → 标题「总营收」→ 格式面板中数据标签单位选「无」，值的小数位设为 0                                |
| 3    | KPI 卡片：平均客单 | 同上，拖入 `Avg Revenue Per User` → 标题「客单价」                                                                            |
| 4    | 环形图：运营组分布 | 可视化选**环形图** → 图例拖入 `dws_user_rfm[segment_operation]` → 值拖入 `Total Users` → 格式中打开「详细信息标签」 |
| 5    | 柱状图：各组营收   | 可视化选**簇状柱形图** → X 轴拖入 `dws_user_rfm[segment_operation]` → Y 轴拖入 `Total Revenue` → 排序按 Y 轴降序    |

**颜色设置**：选中每个图表 → 格式面板 → 数据颜色 → 为每个 `segment_operation` 按以下 Hex 值手动设定：

| 运营组             | 颜色 | Hex     |
| ------------------ | ---- | ------- |
| 至尊VIP            | 金色 | #FFD700 |
| 核心高价值忠诚用户 | 深蓝 | #1565C0 |
| 活跃复购潜力用户   | 蓝色 | #2196F3 |
| 高潜新客           | 紫色 | #9C27B0 |
| 普通新客           | 粉红 | #E91E63 |
| 唤醒高潜           | 橙色 | #FF9800 |
| 唤醒普通           | 黄色 | #FFC107 |
| 流失高潜用户       | 深橙 | #FF5722 |
| 流失可弃           | 红色 | #F44336 |
| 流失低潜           | 棕色 | #795548 |

### Page 2：用户画像

**目标**：了解各运营组的性别、城市分布。

| 序号 | 图表类型                   | 操作步骤                                                                                                                                  |
| ---- | -------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------- |
| 1    | 堆叠柱状图：性别 × 运营组 | 可视化选**堆积柱形图** → X 轴拖入 `dws_user_rfm[segment_operation]` → Y 轴拖入 `Total Users` → 图例拖入 `dim_user[gender]` |
| 2    | 表格：城市 TOP 分布        | 可视化选**表** → 列拖入 `dim_user[city]`、`dws_user_rfm[segment_operation]`、`Total Users` → 筛选中设 Top N                 |
| 3    | 柱状图：各组平均订单数     | 可视化选**簇状柱形图** → X 轴 `segment_operation` → Y 轴 `Avg Order Count`                                                    |
| 4    | 卡片：VIP 用户数           | 卡片拖入 `VIP Count`                                                                                                                    |

> **注意**：用户画像数据（gender, city）来自 `dim_user` 表，仅通过直连 MySQL 可用。

### Page 3：RFM 分群明细

**目标**：可检索、筛选每个用户的 RFM 分值。

| 序号 | 图表类型           | 操作步骤                                                                                                                                                                                                                                                                        |
| ---- | ------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1    | 表格：用户明细     | 可视化选**表** → 拖入 `dws_user_rfm[user_id]`、`dws_user_rfm[segment_operation]`、`dws_user_rfm[order_count]`、`dws_user_rfm[total_amount]`、`dws_user_rfm[days_since_order]`、`dws_user_rfm[r_score]`、`dws_user_rfm[f_score]`、`dws_user_rfm[m_score]` |
| 2    | 切片器：运营组筛选 | 可视化选**切片器** → 字段拖入 `dws_user_rfm[segment_operation]` → 格式设为下拉模式                                                                                                                                                                                    |
| 3    | 切片器：活跃度筛选 | 可视化选**切片器** → 字段拖入 `dws_user_rfm[r_score]`                                                                                                                                                                                                                  |

### Page 4：商品偏好（TGI 版）

**目标**：查看各运营组每个品类 / 品牌的 TGI 偏好指数。

#### 4.1 加载完整的 TGI 明细数据

`dws_customer_category_pref` 表只有 TOP3 品类/品牌。要画完整的 TGI 堆叠柱状图，需要加载完整的品类 TGI 明细。

**获取数据 → MySQL 数据库 → 服务器 `127.0.0.1:3307` 数据库 `ecommerce_rfm` → 高级选项 → 粘贴以下 SQL → 加载为 `segment_category_tgi`：**

```sql
WITH
all_category AS (
    SELECT p.category,
           SUM(oi.item_total) * 100.0 / SUM(SUM(oi.item_total)) OVER () AS amount_pct
    FROM order_items oi JOIN dim_product p ON oi.product_id = p.product_id
    GROUP BY p.category
),
segment_category AS (
    SELECT r.segment_operation, p.category, SUM(oi.item_total) AS total_amount
    FROM order_items oi JOIN dim_product p ON oi.product_id = p.product_id
    JOIN dws_user_rfm r ON oi.user_id = r.user_id
    WHERE r.segment_operation IS NOT NULL
    GROUP BY r.segment_operation, p.category
),
segment_total AS (
    SELECT segment_operation, SUM(total_amount) AS st
    FROM segment_category GROUP BY segment_operation
)
SELECT sc.segment_operation, sc.category, sc.total_amount,
       ROUND(sc.total_amount * 100.0 / st.st, 1) AS segment_pct,
       ROUND(ac.amount_pct, 1) AS overall_pct,
       ROUND((sc.total_amount * 100.0 / st.st) / ac.amount_pct * 100, 0) AS TGI
FROM segment_category sc
JOIN segment_total st ON sc.segment_operation = st.segment_operation
JOIN all_category ac ON sc.category = ac.category
ORDER BY sc.segment_operation, TGI DESC
```

同理，加载品牌 TGI 明细为 `segment_brand_tgi`（将 SQL 中的 `category` 替换为 `brand`，`p.category` 替换为 `p.brand`）：

```sql
WITH
all_brand AS (
    SELECT p.brand,
           SUM(oi.item_total) * 100.0 / SUM(SUM(oi.item_total)) OVER () AS amount_pct
    FROM order_items oi JOIN dim_product p ON oi.product_id = p.product_id
    GROUP BY p.brand
),
segment_brand AS (
    SELECT r.segment_operation, p.brand, SUM(oi.item_total) AS total_amount
    FROM order_items oi JOIN dim_product p ON oi.product_id = p.product_id
    JOIN dws_user_rfm r ON oi.user_id = r.user_id
    WHERE r.segment_operation IS NOT NULL
    GROUP BY r.segment_operation, p.brand
),
segment_total AS (
    SELECT segment_operation, SUM(total_amount) AS st
    FROM segment_brand GROUP BY segment_operation
)
SELECT sb.segment_operation, sb.brand, sb.total_amount,
       ROUND(sb.total_amount * 100.0 / st.st, 1) AS segment_pct,
       ROUND(ab.amount_pct, 1) AS overall_pct,
       ROUND((sb.total_amount * 100.0 / st.st) / ab.amount_pct * 100, 0) AS TGI
FROM segment_brand sb
JOIN segment_total st ON sb.segment_operation = st.segment_operation
JOIN all_brand ab ON sb.brand = ab.brand
ORDER BY sb.segment_operation, TGI DESC
```

#### 4.2 创建报表页

| 序号 | 图表类型                       | 操作步骤                                                                                                                                                                                      |
| ---- | ------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1    | 堆叠柱状图：运营组 × 品类 TGI | 可视化选**堆积柱形图** → X 轴 `segment_category_tgi[segment_operation]` → Y 轴 `TGI` → 图例 `category`                                                                         |
| 2    | 矩阵表：品类 TGI 热力图        | 可视化选**矩阵** → 行 `segment_operation` → 列 `category` → 值 `TGI` → 条件格式：红色低 / 绿色高                                                                              |
| 3    | 堆叠柱状图：运营组 × 品牌 TGI | 可视化选**堆积柱形图** → X 轴 `segment_brand_tgi[segment_operation]` → Y 轴 `TGI` → 图例 `brand`                                                                               |
| 4    | 表格：偏好汇总（Top3）         | 可视化选**表** → 拖入 `dws_customer_category_pref[segment_operation]`、`[top1_category]`、`[top1_tgi]`、`[top2_category]`、`[top2_tgi]`、`[top3_category]`、`[top3_tgi]` |

> **TGI 解读**：TGI > 120 = 该组对该品类/品牌显著偏好；TGI < 80 = 显著回避；80~120 = 正常水平。设置条件格式：TGI ≥ 120 绿色高亮，≤ 80 红色高亮。

### Page 5：运营策略看板

**目标**：查看各运营组的触达策略、优先级和 ROI 预估。

**方案 A（推荐）**：在 Power BI 中执行 SQL 视图

回到 **第一步** 的导航器，点击 **高级选项** → 粘贴以下 SQL → 加载为新表 `operational_list`：

```sql
SELECT
    user_id,
    segment_operation,
    order_count,
    total_amount,
    days_since_order,
    CASE segment_operation
        WHEN '至尊VIP' THEN 0
        WHEN '核心高价值忠诚用户' THEN 0
        WHEN '活跃复购潜力用户' THEN 1
        WHEN '高潜新客' THEN 1
        WHEN '唤醒高潜' THEN 1
        WHEN '流失高潜用户' THEN 2
        WHEN '普通新客' THEN 2
        WHEN '唤醒普通' THEN 3
        WHEN '流失低潜' THEN 4
        WHEN '流失可弃' THEN 4
    END AS priority,
    CASE segment_operation
        WHEN '至尊VIP' THEN 0.40
        WHEN '核心高价值忠诚用户' THEN 0.35
        WHEN '活跃复购潜力用户' THEN 0.25
        WHEN '高潜新客' THEN 0.20
        WHEN '普通新客' THEN 0.12
        WHEN '唤醒高潜' THEN 0.15
        WHEN '唤醒普通' THEN 0.05
        WHEN '流失高潜用户' THEN 0.10
        WHEN '流失可弃' THEN 0.01
        WHEN '流失低潜' THEN 0.03
    END AS estimated_response_rate,
    CASE segment_operation
        WHEN '至尊VIP' THEN 'P0-新品电子首发通知+品牌日专属折扣+专属客服'
        WHEN '核心高价值忠诚用户' THEN 'P0-Groceries/Beauty复购券+会员升级+全品类满减'
        WHEN '活跃复购潜力用户' THEN 'P1-Books/Sports品类优惠券+交叉销售推荐+积分翻倍'
        WHEN '高潜新客' THEN 'P1-首单复购引导+配套推荐+专属客服跟进'
        WHEN '普通新客' THEN 'P2-7天复购提醒+品类教育邮件+首单满减券'
        WHEN '唤醒高潜' THEN 'P1-定向召回+限时折扣+30天有效'
        WHEN '唤醒普通' THEN 'P3-常规召回邮件+大促通知+小额优惠券'
        WHEN '流失高潜用户' THEN 'P2-精准召回+品类强激励+双重触达'
        WHEN '流失可弃' THEN 'P4-不主动触达，仅大促被动覆盖'
        WHEN '流失低潜' THEN 'P4-季度触达+大促通知'
    END AS action
FROM dws_user_rfm
ORDER BY priority, total_amount DESC
```

| 序号 | 图表类型           | 操作步骤                                                                                                                                         |
| ---- | ------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------ |
| 1    | 表格：运营策略明细 | 可视化选**表** → 拖入 `operational_list[user_id]`、`[segment_operation]`、`[priority]`、`[estimated_response_rate]`、`[action]` |
| 2    | 切片器：优先级筛选 | 可视化选**切片器** → 字段 `operational_list[priority]`                                                                                  |

---

## 第五步：设置跨页筛选联动

### 5.1 同步切片器

在 Page 3 创建了 `segment_operation` 切片器后：

1. 选中该切片器
2. 菜单栏 → **视图** → **同步切片器**（或右键切片器 → 同步切片器）
3. 在弹出面板中勾选所有页面（Page 1 ~ Page 5）
4. 这样选择一个运营组后，所有页面都会同步筛选

### 5.2 交叉筛选设置

- 选中每个图表 → 格式 → **编辑交互**
- 确保环形图点击某个组时，柱状图和表格联动更新

---

## 第六步：格式美化

1. **主题颜色**：视图 → 主题 → 自定义 → 将 10 组颜色编码配置到主题中
2. **页面背景**：格式面板 → 画布背景 → 浅灰色 #F5F5F5
3. **标题**：每个页面顶部添加文本框作为页面标题（字体大小 24pt，加粗）
4. **对齐**：Ctrl+点击多个图表 → 格式 → 对齐 → 垂直居中 / 均匀分布

---

## 验证清单

- [ ] MySQL 容器 `mysql84` 已运行（`docker ps` 确认）
- [ ] Power BI 成功连接 `127.0.0.1:3307`，导入 6 张基础表
- [ ] Page 4 TGI 数据：加载 `segment_category_tgi` 和 `segment_brand_tgi` 两个 SQL 视图
- [ ] Page 5 策略数据：加载 `operational_list` SQL 视图
- [ ] 模型视图中确认表间关系：dws_user_rfm ↔ dim_user / order_items / dim_order，dim_product ↔ order_items
- [ ] 度量值创建：Total Users, Total Revenue, Avg Revenue Per User, Avg Order Count, Avg Recency, VIP Count
- [ ] KPI 数值验证：总用户 **1,803** / 总营收约 **¥1,205,695**
- [ ] 10 组颜色编码在所有图表中一致（金色 VIP、深蓝核心、红色流失可弃）
- [ ] `segment_operation` 切片器同步到所有 5 页
- [ ] 点击环形图某一组，其他图表联动筛选
- [ ] 5 个页面全部完成，标题清晰
- [ ] 保存文件到 `powerbi/rfm.pbip`
