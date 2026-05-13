"""数据清洗模块单元测试"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'python'))

import pandas as pd
import pytest
from data_cleaning import clean_orders, generate_user_summary


@pytest.fixture
def sample_users() -> pd.DataFrame:
    return pd.DataFrame({
        'user_id': ['U1', 'U2', 'U3'],
        'name': ['Alice', 'Bob', 'Charlie'],
        'email': ['a@x.com', 'b@x.com', 'c@x.com'],
        'gender': ['Female', 'Male', 'Other'],
        'city': ['NY', 'LA', 'SF'],
        'signup_date': ['2024-01-01', '2024-06-01', '2024-12-01'],
    })


@pytest.fixture
def sample_orders() -> pd.DataFrame:
    return pd.DataFrame({
        'order_id': ['O1', 'O2', 'O3', 'O4', 'O5', 'O6'],
        'user_id': ['U1', 'U1', 'U2', 'U3', 'U3', 'U1'],
        'order_date': ['2024-03-01', '2024-07-01', '2024-08-01',
                       '2024-10-01', '2024-11-01', '2023-12-01'],
        'order_status': ['completed', 'completed', 'cancelled',
                         'completed', 'completed', 'completed'],
        'total_amount': [100, 200, 50, 0, 300, 150],
    })


def test_clean_orders_filters_status(sample_orders, sample_users):
    import pandas as pd
    analysis_date = pd.Timestamp('2025-01-01')
    cleaned = clean_orders(sample_orders, sample_users, analysis_date)
    # O3 is cancelled, should be filtered
    assert 'O3' not in cleaned['order_id'].values


def test_clean_orders_filters_zero_amount(sample_orders, sample_users):
    import pandas as pd
    analysis_date = pd.Timestamp('2025-01-01')
    cleaned = clean_orders(sample_orders, sample_users, analysis_date)
    # O4 has amount 0, should be filtered
    assert 'O4' not in cleaned['order_id'].values


def test_clean_orders_filters_date_before_signup(sample_orders, sample_users):
    import pandas as pd
    analysis_date = pd.Timestamp('2025-01-01')
    cleaned = clean_orders(sample_orders, sample_users, analysis_date)
    # O6 date (2023-12-01) < U1 signup_date (2024-01-01), should be filtered
    assert 'O6' not in cleaned['order_id'].values


def test_clean_orders_adds_days_since_order(sample_orders, sample_users):
    import pandas as pd
    analysis_date = pd.Timestamp('2025-01-01')
    cleaned = clean_orders(sample_orders, sample_users, analysis_date)
    assert 'days_since_order' in cleaned.columns
    # O1: 2024-03-01 → 2025-01-01 = 306 days
    o1 = cleaned[cleaned['order_id'] == 'O1'].iloc[0]
    assert o1['days_since_order'] == 306


def test_generate_user_summary(sample_orders, sample_users):
    import pandas as pd
    analysis_date = pd.Timestamp('2025-01-01')
    cleaned = clean_orders(sample_orders, sample_users, analysis_date)
    summary = generate_user_summary(cleaned)
    assert len(summary) > 0
    assert 'order_count' in summary.columns
    assert 'total_amount' in summary.columns
    assert 'days_since_order' in summary.columns
    # U1 should have O1 + O2 = 2 completed orders, total = 300
    u1 = summary[summary['user_id'] == 'U1'].iloc[0]
    assert u1['order_count'] == 2
    assert u1['total_amount'] == 300
