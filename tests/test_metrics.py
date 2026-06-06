"""Tests for the metrics and anomaly detection modules."""
import pytest
import pandas as pd
from etl.extract import DemoExtractor
from etl.transform import transform
from analytics.metrics import (
    build_project_metrics, build_stack_metrics,
    build_dashboard_summary,
)
from analytics.anomaly import detect_all_anomalies


@pytest.fixture
def transformed_data():
    extractor = DemoExtractor()
    raw = extractor.extract_all()
    return transform(raw)


def test_build_project_metrics(transformed_data):
    projects = build_project_metrics(transformed_data["project_metrics"])
    assert len(projects) == 18
    # Sorted by margin (worst first)
    assert projects[0].margin <= projects[-1].margin


def test_build_stack_metrics(transformed_data):
    stacks = build_stack_metrics(transformed_data["stack_metrics"])
    assert len(stacks) == 6
    for s in stacks:
        assert s.stack in ["Unity", "UE", "ASP.NET", "Flutter", "Vue.js", "Laravel"]


def test_dashboard_summary(transformed_data):
    summary = build_dashboard_summary(transformed_data)
    assert summary.project_count == 18
    assert summary.developer_count == 30
    assert summary.total_revenue > 0
    assert summary.total_costs > 0


def test_anomaly_detection(transformed_data):
    anomalies = detect_all_anomalies(transformed_data)
    assert isinstance(anomalies, list)
    # Should find at least some anomalies in the demo data
    assert len(anomalies) > 0
    # Sorted by severity
    sev = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    for i in range(len(anomalies) - 1):
        assert sev.get(anomalies[i]["severity"], 3) <= sev.get(anomalies[i + 1]["severity"], 3)


def test_loss_projects_detected(transformed_data):
    """Verify that known loss-making projects are detected."""
    summary = build_dashboard_summary(transformed_data)
    assert summary.loss_projects_count > 0
    red_projects = [p for p in summary.projects if p.status == "red"]
    assert len(red_projects) > 0


def test_import_success_rate(transformed_data):
    """Spec: >= 95% records successfully imported."""
    extractor = DemoExtractor()
    raw = extractor.extract_all()
    for key in ["projects", "developers", "tasks", "financials"]:
        raw_count = len(raw[key])
        transformed_count = len(transformed_data[key])
        rate = transformed_count / raw_count if raw_count > 0 else 0
        assert rate >= 0.95, f"Import rate for {key}: {rate:.2%} < 95%"
