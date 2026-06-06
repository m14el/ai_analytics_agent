"""Tests for the ETL pipeline."""
import pytest
import pandas as pd
from etl.extract import DemoExtractor
from etl.transform import (
    clean_data, calculate_financial_metrics,
    aggregate_project_metrics, aggregate_stack_metrics,
    aggregate_task_type_metrics, transform,
)


@pytest.fixture
def demo_data():
    extractor = DemoExtractor()
    return extractor.extract_all()


def test_demo_extract(demo_data):
    assert len(demo_data["projects"]) == 18
    assert len(demo_data["developers"]) == 30
    assert len(demo_data["tasks"]) > 50
    assert len(demo_data["financials"]) > 50


def test_clean_data(demo_data):
    cleaned = clean_data(demo_data)
    # No nulls in critical fields
    assert cleaned["tasks"]["actual_hours"].isna().sum() == 0
    assert cleaned["financials"]["revenue"].isna().sum() == 0


def test_financial_metrics(demo_data):
    cleaned = clean_data(demo_data)
    fin = calculate_financial_metrics(cleaned["financials"])
    assert "profit" in fin.columns
    assert "margin" in fin.columns
    # Profit = revenue - costs
    row = fin.iloc[0]
    assert abs(row["profit"] - (row["revenue"] - row["costs"])) < 0.01


def test_project_metrics(demo_data):
    cleaned = clean_data(demo_data)
    fin = calculate_financial_metrics(cleaned["financials"])
    pm = aggregate_project_metrics(fin, cleaned["projects"], cleaned["tasks"], cleaned["developers"])
    assert len(pm) == 18
    assert "profitability_status" in pm.columns
    assert set(pm["profitability_status"].unique()).issubset({"green", "yellow", "red"})


def test_stack_metrics(demo_data):
    cleaned = clean_data(demo_data)
    fin = calculate_financial_metrics(cleaned["financials"])
    pm = aggregate_project_metrics(fin, cleaned["projects"], cleaned["tasks"], cleaned["developers"])
    sm = aggregate_stack_metrics(pm)
    assert len(sm) == 6  # Unity, UE, ASP.NET, Flutter, Vue.js, Laravel


def test_full_transform(demo_data):
    result = transform(demo_data)
    assert "project_metrics" in result
    assert "stack_metrics" in result
    assert "task_type_metrics" in result
    assert "developer_metrics" in result


def test_margin_accuracy(demo_data):
    """Verify margin calculation accuracy (spec: <= 2% deviation)."""
    result = transform(demo_data)
    pm = result["project_metrics"]
    for _, row in pm.iterrows():
        if row["total_revenue"] > 0:
            expected_margin = (row["total_profit"] / row["total_revenue"]) * 100
            assert abs(row["margin"] - expected_margin) < 2.0, (
                f"Margin deviation > 2% for {row['name']}: {row['margin']} vs {expected_margin}"
            )
