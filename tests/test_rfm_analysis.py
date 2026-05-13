"""RFM 分析模块单元测试"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'python'))

import pandas as pd
import pytest
from rfm_analysis import (
    _segment_19_name,
    _assign_10_groups,
    compute_rfm_scores,
    validate_segmentation,
)


# ── Fixtures ──────────────────────────────────────────

@pytest.fixture
def sample_user_summary() -> pd.DataFrame:
    """构造典型用户 RFM 数据"""
    return pd.DataFrame({
        'user_id': [f'U{i:06d}' for i in range(100)],
        'order_count': [1]*77 + [2]*15 + [3]*8,
        'total_amount': [50]*25 + [200]*50 + [600]*25,
        'days_since_order': [30]*20 + [100]*30 + [200]*50,
    })


# ── 19类分群标签映射 ─────────────────────────────────

def test_segment_19_vip():
    assert _segment_19_name('VIP') == '至尊VIP'


def test_segment_19_active():
    assert _segment_19_name('1-2-3') == '活跃-复购-高价值'


def test_segment_19_unknown():
    assert _segment_19_name('invalid') == '未知'


# ── 10大运营组分群 ───────────────────────────────────

def test_assign_vip():
    row = pd.Series({'is_vip': True, 'r_score': 3, 'f_score': 1, 'm_score': 3})
    assert _assign_10_groups(row) == '至尊VIP'


def test_assign_core_loyal():
    row = pd.Series({'is_vip': False, 'r_score': 1, 'f_score': 2, 'm_score': 3})
    assert _assign_10_groups(row) == '核心高价值忠诚用户'


def test_assign_wakeup_high_potential():
    row = pd.Series({'is_vip': False, 'r_score': 2, 'f_score': 2, 'm_score': 2})
    assert _assign_10_groups(row) == '唤醒高潜'


def test_assign_churn_disposable():
    row = pd.Series({'is_vip': False, 'r_score': 3, 'f_score': 1, 'm_score': 1})
    assert _assign_10_groups(row) == '流失可弃'


def test_assign_churn_low():
    row = pd.Series({'is_vip': False, 'r_score': 3, 'f_score': 1, 'm_score': 2})
    assert _assign_10_groups(row) == '流失低潜'


# ── RFM 评分全流程 ───────────────────────────────────

def test_compute_rfm_scores_output_columns(sample_user_summary):
    result = compute_rfm_scores(sample_user_summary)
    expected_cols = ['r_score', 'f_score', 'm_score', 'is_vip',
                     'm_p25', 'm_p75', 'vip_threshold',
                     'rfm_combined', 'segment_19', 'segment_operation']
    for col in expected_cols:
        assert col in result.columns, f"Missing column: {col}"


def test_compute_rfm_scores_row_count(sample_user_summary):
    result = compute_rfm_scores(sample_user_summary)
    assert len(result) == len(sample_user_summary)


def test_r_score_range(sample_user_summary):
    result = compute_rfm_scores(sample_user_summary)
    assert result['r_score'].isin([1, 2, 3]).all()


def test_f_score_range(sample_user_summary):
    result = compute_rfm_scores(sample_user_summary)
    assert result['f_score'].isin([1, 2]).all()


def test_m_score_range(sample_user_summary):
    result = compute_rfm_scores(sample_user_summary)
    assert result['m_score'].isin([1, 2, 3]).all()


def test_vip_identification():
    """M > Q3+1.5*IQR 的用户被标记为 VIP"""
    df = pd.DataFrame({
        'user_id': ['U1', 'U2', 'U3', 'U4', 'U5', 'U6', 'U7', 'U8', 'U9', 'U10'],
        'order_count': [1]*10,
        'total_amount': [10, 20, 30, 40, 50, 60, 70, 80, 90, 500],
        'days_since_order': [100]*10,
    })
    result = compute_rfm_scores(df)
    # 只有最后一位应该被标记为 VIP（远高于正常范围）
    assert result.iloc[-1]['is_vip'] == 1


# ── 分群核验 ─────────────────────────────────────────

def test_validate_segmentation_passes(sample_user_summary):
    result = compute_rfm_scores(sample_user_summary)
    assert validate_segmentation(result)


def test_all_users_assigned(sample_user_summary):
    result = compute_rfm_scores(sample_user_summary)
    assert result['segment_operation'].notna().all()


def test_no_empty_segment_19(sample_user_summary):
    result = compute_rfm_scores(sample_user_summary)
    assert (result['segment_19'] != '未知').all()
