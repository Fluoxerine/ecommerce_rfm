"""项目配置常量"""
import os
import logging
from pathlib import Path
from dotenv import load_dotenv

# 加载 .env 文件（若存在）
load_dotenv(Path(__file__).resolve().parent.parent / '.env')

# ── 项目路径 ──────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / 'data'
OUTPUT_DIR = PROJECT_ROOT / 'output'
CHART_DIR = OUTPUT_DIR / 'charts'

# ── MySQL 连接配置（优先环境变量，回退到默认值仅用于开发） ──
MYSQL_CONFIG = {
    'container': os.getenv('MYSQL_CONTAINER', 'mysql84'),
    'host': os.getenv('MYSQL_HOST', '127.0.0.1'),
    'port': int(os.getenv('MYSQL_PORT', '3306')),
    'user': os.getenv('MYSQL_USER', 'root'),
    'password': os.getenv('MYSQL_PASSWORD', ''),
    'database': os.getenv('MYSQL_DATABASE', 'ecommerce_rfm'),
}

# ── 分析日期 ──────────────────────────────────────────
ANALYSIS_DATE = os.getenv('ANALYSIS_DATE', None)  # 'YYYY-MM-DD' 或 None（动态确定）

# ── RFM 阈值 ──────────────────────────────────────────
R_THRESHOLDS = (60, 180)    # R: ≤60天活跃, 61-180天唤醒, >180天流失
F_THRESHOLD = 2             # F: 1次=一次性, ≥2次=复购
# M 阈值在运行时根据 P25/P75 分位数确定
# VIP 阈值在运行时根据箱线图上边缘确定

# ── 10大运营组分群配置 ───────────────────────────────
OPERATION_GROUP_CONFIG = {
    '至尊VIP':                {'r': None, 'f': None, 'm': None, 'vip': True},
    '核心高价值忠诚用户':       {'r': 1, 'f': 2, 'm': 3, 'vip': False},
    '活跃复购潜力用户':         {'r': 1, 'f': 2, 'm': [1, 2], 'vip': False},
    '高潜新客':               {'r': 1, 'f': 1, 'm': 3, 'vip': False},
    '普通新客':               {'r': 1, 'f': 1, 'm': [1, 2], 'vip': False},
    '唤醒高潜':               {'r': 2, 'f': 2, 'm': [2, 3], 'vip': False},
    '唤醒普通':               {'r': 2, 'f': None, 'm': None, 'vip': False,
                              'note': 'R2唤醒 + 不在唤醒高潜的其他用户（含F2+M1）'},
    '流失高潜用户':            {'r': 3, 'f': 2, 'm': [2, 3], 'vip': False},
    '流失可弃':               {'r': 3, 'f': 1, 'm': 1, 'vip': False},
    '流失低潜':               {'r': 3, 'f': None, 'm': None, 'vip': False,
                             'note': 'R3流失 + 不在以上组的其他用户'},
}

# ── 颜色方案 ──────────────────────────────────────────
COLORS = {
    'primary': '#2E86AB',
    'secondary': '#A23B72',
    'accent': '#F18F01',
    'success': '#C73E1D',
    'grid': '#E5E5E5',
    'text': '#333333',
    'bg': '#FFFFFF',
    'r_high': '#27AE60',
    'r_mid': '#F39C12',
    'r_low': '#E74C3C',
    'f_high': '#9B59B6',
    'f_mid': '#3498DB',
    'f_low': '#95A5A6',
    'm_high': '#1ABC9C',
    'm_mid': '#F1C40F',
    'm_low': '#E67E22',
    'vip': '#FFD700',
}

SEGMENT_COLORS: dict[str, str] = {
    '至尊VIP': '#FFD700',
    '核心高价值忠诚用户': '#1565C0',
    '活跃复购潜力用户': '#2196F3',
    '高潜新客': '#9C27B0',
    '普通新客': '#E91E63',
    '唤醒高潜': '#FF9800',
    '唤醒普通': '#FFC107',
    '流失高潜用户': '#FF5722',
    '流失可弃': '#F44336',
    '流失低潜': '#795548',
}

# ── ROI 预估基准参数 ──────────────────────────────────
# 与 operations/strategy.md 保持一致（以 strategy.md 为权威来源）
ROI_BENCHMARKS = {
    'email_targeted':   {'response': 0.08, 'cost': 0.15},
    'email_personalized': {'response': 0.18, 'cost': 0.50},
    'email_mass':       {'response': 0.03, 'cost': 0.10},
    'sms':              {'response': 0.08, 'cost': 0.08},
    'push':             {'response': 0.05, 'cost': 0.02},
    'vip_call':         {'response': 0.25, 'cost': 25.0},
    # R/F/M 响应率乘数
    'r_multiplier':     {1: 1.5, 2: 0.6, 3: 0.3},
    'f_multiplier':     {1: 0.7, 2: 1.0},
    'm_multiplier':     {1: 0.7, 2: 1.0, 3: 1.3},
}

# ── 日志配置 ──────────────────────────────────────────
LOG_FORMAT = '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
LOG_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

logging.basicConfig(
    level=logging.INFO,
    format=LOG_FORMAT,
    datefmt=LOG_DATE_FORMAT,
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(PROJECT_ROOT / 'output' / 'analysis.log', encoding='utf-8'),
    ],
)

logger = logging.getLogger('rfm_analysis')
