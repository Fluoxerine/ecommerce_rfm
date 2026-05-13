"""MySQL 数据导入 + Power BI 数据导出工具

安全说明：所有 MySQL 凭据从 .env 文件或环境变量读取，不硬编码。
"""
import csv
import io
import subprocess
import sys
from pathlib import Path
from config import MYSQL_CONFIG, PROJECT_ROOT

DATA_DIR = PROJECT_ROOT / 'data'
OUTPUT_DIR = PROJECT_ROOT / 'output'
POWERBI_DIR = PROJECT_ROOT / 'powerbi' / 'data'
SQL_DIR = PROJECT_ROOT / 'sql'

CONTAINER = MYSQL_CONFIG['container']
DB = MYSQL_CONFIG['database']


def _mysql_base_args() -> list[str]:
    """构建 mysql 命令行参数列表（安全：无 shell=True）"""
    return [
        'docker', 'exec', '-i', CONTAINER,
        'mysql',
        '-h', MYSQL_CONFIG['host'],
        '-u', MYSQL_CONFIG['user'],
        f"-p{MYSQL_CONFIG['password']}",
        '--default-character-set=utf8mb4',
        '--local-infile=1',
    ]


def _run_docker_cp(local_path: str, container_path: str) -> bool:
    """安全复制文件到容器"""
    result = subprocess.run(
        ['docker', 'cp', str(local_path), f'{CONTAINER}:{container_path}'],
        capture_output=True, text=True, encoding='utf-8', errors='replace',
    )
    return result.returncode == 0


def _run_mysql(description: str, sql_file: Path | None = None,
               query: str | None = None) -> subprocess.CompletedProcess:
    """安全执行 MySQL 命令（参数列表，无 shell）"""
    args = _mysql_base_args()
    args.append(DB)

    if sql_file:
        print(f"  {description}...", end=' ')
        with open(sql_file, 'r', encoding='utf-8') as f:
            result = subprocess.run(args, stdin=f, capture_output=True,
                                    text=True, encoding='utf-8', errors='replace')
    elif query:
        print(f"  {description}...", end=' ')
        result = subprocess.run(args, input=query, capture_output=True,
                                text=True, encoding='utf-8', errors='replace')
    else:
        raise ValueError("Must provide sql_file or query")

    if result.returncode != 0:
        print(f"FAILED\n    {result.stderr.strip()}")
    else:
        print("OK")
    return result


def step1_copy_csv() -> bool:
    """将 CSV 文件复制到容器内 /tmp/"""
    print("\n[1/5] 复制 CSV 到容器...")
    files: list[tuple[Path, str]] = [
        (DATA_DIR / 'users.csv', '/tmp/users.csv'),
        (DATA_DIR / 'products.csv', '/tmp/products.csv'),
        (DATA_DIR / 'orders.csv', '/tmp/orders.csv'),
        (DATA_DIR / 'order_items.csv', '/tmp/order_items.csv'),
        (OUTPUT_DIR / 'cleaned_orders.csv', '/tmp/cleaned_orders.csv'),
        (OUTPUT_DIR / 'cleaned_user_summary.csv', '/tmp/cleaned_user_summary.csv'),
    ]
    for host_path, container_path in files:
        if not host_path.exists():
            print(f"  SKIP: {host_path} 不存在，跳过")
            continue
        if not _run_docker_cp(str(host_path), container_path):
            print(f"  FAILED: {host_path.name} → {container_path}")
            return False
        print(f"  OK: {host_path.name}")
    return True


def step2_create_tables() -> bool:
    """执行建表脚本"""
    print("\n[2/5] 创建表结构...")
    sql_file = SQL_DIR / '01_create_tables.sql'
    result = _run_mysql('01_create_tables.sql', sql_file=sql_file)
    return result.returncode == 0


def step3_load_data() -> bool:
    """执行数据导入脚本"""
    print("\n[3/5] 导入 CSV 数据...")
    sql_file = SQL_DIR / '02_load_data.sql'
    result = _run_mysql('02_load_data.sql', sql_file=sql_file)
    return result.returncode == 0


def step4_rfm_calculation() -> bool:
    """执行 RFM 计算"""
    print("\n[4/5] RFM 计算 (SQL端，作为 Python 端补充)...")
    sql_file = SQL_DIR / '03_rfm_calculation.sql'
    result = _run_mysql('03_rfm_calculation.sql', sql_file=sql_file)
    return result.returncode == 0


def step5_export_powerbi() -> None:
    """从 MySQL 导出 Power BI 所需 CSV（安全：避免简单字符串替换）"""
    print("\n[5/5] 导出 Power BI 数据文件...")
    POWERBI_DIR.mkdir(parents=True, exist_ok=True)

    queries: dict[str, str] = {
        'rfm_segments.csv':
            "SELECT user_id, segment_operation, segment_19, order_count, "
            "total_amount, days_since_order, r_score, f_score, m_score, is_vip "
            "FROM dws_user_rfm",

        'user_profile.csv':
            "SELECT u.user_id, u.gender, u.city, r.segment_operation "
            "FROM dim_user u JOIN dws_user_rfm r ON u.user_id = r.user_id",

        'segment_summary.csv':
            "SELECT segment_operation, COUNT(*) as user_count, "
            "SUM(total_amount) as total_revenue, "
            "AVG(total_amount) as avg_revenue, "
            "AVG(order_count) as avg_order_count, "
            "AVG(days_since_order) as avg_recency "
            "FROM dws_user_rfm GROUP BY segment_operation "
            "ORDER BY user_count DESC",

        'segment_category.csv':
            "SELECT sc.segment_operation, sc.category, sc.total_amount, "
            "ROUND(sc.total_amount * 100.0 / st.st, 1) as segment_pct, "
            "ROUND((sc.total_amount * 100.0 / st.st) / ac.amount_pct * 100, 0) as TGI "
            "FROM (SELECT r.segment_operation, p.category, SUM(oi.item_total) as total_amount "
            "      FROM order_items oi JOIN dim_product p ON oi.product_id = p.product_id "
            "      JOIN dws_user_rfm r ON oi.user_id = r.user_id "
            "      WHERE r.segment_operation IS NOT NULL "
            "      GROUP BY r.segment_operation, p.category) sc "
            "JOIN (SELECT segment_operation, SUM(oi.item_total) as st "
            "      FROM order_items oi JOIN dws_user_rfm r ON oi.user_id = r.user_id "
            "      WHERE r.segment_operation IS NOT NULL GROUP BY r.segment_operation) st "
            "      ON sc.segment_operation = st.segment_operation "
            "JOIN (SELECT p.category, SUM(oi.item_total) * 100.0 / SUM(SUM(oi.item_total)) OVER () as amount_pct "
            "      FROM order_items oi JOIN dim_product p ON oi.product_id = p.product_id GROUP BY p.category) ac "
            "      ON sc.category = ac.category "
            "ORDER BY sc.segment_operation, TGI DESC",

        'segment_brand.csv':
            "SELECT sb.segment_operation, sb.brand, sb.total_amount, "
            "ROUND((sb.total_amount * 100.0 / st.st) / ab.amount_pct * 100, 0) as TGI "
            "FROM (SELECT r.segment_operation, p.brand, SUM(oi.item_total) as total_amount "
            "      FROM order_items oi JOIN dim_product p ON oi.product_id = p.product_id "
            "      JOIN dws_user_rfm r ON oi.user_id = r.user_id "
            "      WHERE r.segment_operation IS NOT NULL "
            "      GROUP BY r.segment_operation, p.brand) sb "
            "JOIN (SELECT segment_operation, SUM(oi.item_total) as st "
            "      FROM order_items oi JOIN dws_user_rfm r ON oi.user_id = r.user_id "
            "      WHERE r.segment_operation IS NOT NULL GROUP BY r.segment_operation) st "
            "      ON sb.segment_operation = st.segment_operation "
            "JOIN (SELECT p.brand, SUM(oi.item_total) * 100.0 / SUM(SUM(oi.item_total)) OVER () as amount_pct "
            "      FROM order_items oi JOIN dim_product p ON oi.product_id = p.product_id GROUP BY p.brand) ab "
            "      ON sb.brand = ab.brand "
            "ORDER BY sb.segment_operation, TGI DESC",

        'operational_list.csv':
            "SELECT user_id, segment_operation, order_count, total_amount, "
            "days_since_order, priority, estimated_response_rate, "
            "CASE segment_operation "
            "    WHEN '至尊VIP' THEN 'P0-新品电子首发通知+品牌日专属折扣+专属客服' "
            "    WHEN '核心高价值忠诚用户' THEN 'P0-Groceries/Beauty复购券+会员升级+全品类满减' "
            "    WHEN '活跃复购潜力用户' THEN 'P1-Books/Sports品类优惠券+交叉销售推荐+积分翻倍' "
            "    WHEN '高潜新客' THEN 'P1-首单复购引导+配套推荐+专属客服跟进' "
            "    WHEN '普通新客' THEN 'P2-7天复购提醒+品类教育邮件+首单满减券' "
            "    WHEN '唤醒高潜' THEN 'P1-定向召回+限时折扣+30天有效' "
            "    WHEN '唤醒普通' THEN 'P3-常规召回邮件+大促通知+小额优惠券' "
            "    WHEN '流失高潜用户' THEN 'P2-精准召回+品类强激励+双重触达' "
            "    WHEN '流失可弃' THEN 'P4-不主动触达，仅大促被动覆盖' "
            "    WHEN '流失低潜' THEN 'P4-季度触达+大促通知' "
            "END as action "
            "FROM (SELECT r.user_id, r.segment_operation, r.order_count, "
            "      r.total_amount, r.days_since_order, "
            "      CASE r.segment_operation "
            "          WHEN '至尊VIP' THEN 0 WHEN '核心高价值忠诚用户' THEN 0 "
            "          WHEN '活跃复购潜力用户' THEN 1 WHEN '高潜新客' THEN 1 "
            "          WHEN '唤醒高潜' THEN 1 WHEN '流失高潜用户' THEN 2 "
            "          WHEN '普通新客' THEN 2 WHEN '唤醒普通' THEN 3 "
            "          WHEN '流失低潜' THEN 4 WHEN '流失可弃' THEN 4 "
            "      END as priority, "
            "      CASE r.segment_operation "
            "          WHEN '至尊VIP' THEN 0.40 WHEN '核心高价值忠诚用户' THEN 0.35 "
            "          WHEN '活跃复购潜力用户' THEN 0.25 WHEN '高潜新客' THEN 0.20 "
            "          WHEN '普通新客' THEN 0.12 WHEN '唤醒高潜' THEN 0.15 "
            "          WHEN '唤醒普通' THEN 0.05 WHEN '流失高潜用户' THEN 0.10 "
            "          WHEN '流失可弃' THEN 0.01 WHEN '流失低潜' THEN 0.03 "
            "      END as estimated_response_rate "
            "      FROM dws_user_rfm r) r "
            "ORDER BY priority, total_amount DESC",
    }

    for filename, query in queries.items():
        output_file = POWERBI_DIR / filename
        args = _mysql_base_args()
        args.extend(['--batch', '--raw', DB, '-e', query])

        result = subprocess.run(args, capture_output=True, text=True,
                                encoding='utf-8', errors='replace')
        if result.returncode != 0 or not result.stdout:
            print(f"  {filename}: FAILED - {result.stderr.strip() if result.stderr else 'no output'}")
            continue

        # 安全地解析 TSV 输出并写入标准 CSV
        reader = csv.reader(io.StringIO(result.stdout), delimiter='\t')
        with open(output_file, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            for row in reader:
                writer.writerow(row)

        with open(output_file, 'r', encoding='utf-8') as f:
            line_count = sum(1 for _ in f) - 1
        print(f"  {filename}: {line_count} 行")


def main() -> None:
    print("=" * 60)
    print("MySQL 数据导入 & Power BI 数据导出")
    print("=" * 60)

    # 验证密码已配置
    if not MYSQL_CONFIG['password']:
        print("\n[ERROR] MYSQL_PASSWORD 未设置。请在 .env 文件或环境变量中配置。")
        print("可复制 .env.example → .env 并填写密码。")
        sys.exit(1)

    # 检查容器状态
    result = subprocess.run(
        ['docker', 'ps', '--filter', f'name={CONTAINER}', '--format', '{{.Names}}'],
        capture_output=True, text=True,
    )
    if CONTAINER not in result.stdout:
        print(f"\n[ERROR] 容器 {CONTAINER} 未运行。请先执行: docker start {CONTAINER}")
        sys.exit(1)
    print(f"容器 {CONTAINER} 运行中")

    # 检查 CSV 文件
    required_csv = OUTPUT_DIR / 'cleaned_user_summary.csv'
    if not required_csv.exists():
        print(f"\n[ERROR] 缺少 {required_csv}")
        print("请先运行: python python/main.py")
        sys.exit(1)

    # 执行步骤
    if not step1_copy_csv():
        print("\n[ABORT] CSV 复制失败")
        sys.exit(1)
    if not step2_create_tables():
        print("\n[ABORT] 建表失败")
        sys.exit(1)
    if not step3_load_data():
        print("\n[ABORT] 数据导入失败")
        sys.exit(1)

    step4_rfm_calculation()
    step5_export_powerbi()

    print(f"\n完成！Power BI 数据文件已导出到: {POWERBI_DIR}")
    if POWERBI_DIR.exists():
        exported = sorted(f.name for f in POWERBI_DIR.glob('*.csv'))
        print(f"  可用文件 ({len(exported)} 个):")
        for f in exported:
            print(f"    - {f}")
        print("\nPower BI 用法:")
        print("  - rfm_segments.csv        → Page 1/3 (用户分群明细)")
        print("  - user_profile.csv        → Page 2 (性别/城市画像)")
        print("  - segment_summary.csv     → Page 1 (各组汇总)")
        print("  - segment_category.csv    → Page 4 (品类TGI)")
        print("  - segment_brand.csv       → Page 4 (品牌TGI)")
        print("  - operational_list.csv    → Page 5 (运营触达清单)")


if __name__ == '__main__':
    main()
