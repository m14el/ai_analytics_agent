"""
AI Analytics Agent — Anomaly Detection Module
Statistical methods to identify outliers and suspicious patterns.
"""
import logging
from typing import Dict, List
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def z_score_anomalies(series: pd.Series, threshold: float = 2.0) -> pd.Series:
    if series.std() == 0:
        return pd.Series(False, index=series.index)
    z = (series - series.mean()) / series.std()
    return z.abs() > threshold


def iqr_anomalies(series: pd.Series, factor: float = 1.5) -> pd.Series:
    q1, q3 = series.quantile(0.25), series.quantile(0.75)
    iqr = q3 - q1
    return (series < q1 - factor * iqr) | (series > q3 + factor * iqr)


def detect_project_anomalies(pm: pd.DataFrame) -> List[dict]:
    anomalies = []
    if "margin" in pm.columns and len(pm) > 0:
        mask = z_score_anomalies(pm["margin"], 1.5)
        for _, r in pm[mask].iterrows():
            if r["margin"] < pm["margin"].mean():
                anomalies.append({
                    "type": "project_low_margin", "entity": r["name"],
                    "metric": "margin", "value": round(r["margin"], 2),
                    "mean": round(pm["margin"].mean(), 2),
                    "severity": "high" if r["margin"] < 0 else "medium",
                    "description": f"Проект «{r['name']}»: маржа {r['margin']:.1f}% (средн. {pm['margin'].mean():.1f}%)",
                })
    if "overtime_ratio" in pm.columns:
        mask = z_score_anomalies(pm["overtime_ratio"], 1.5)
        for _, r in pm[mask].iterrows():
            if r["overtime_ratio"] > pm["overtime_ratio"].mean():
                anomalies.append({
                    "type": "project_high_overtime", "entity": r["name"],
                    "metric": "overtime_ratio", "value": round(r["overtime_ratio"], 2),
                    "severity": "high" if r["overtime_ratio"] > 1.5 else "medium",
                    "description": f"Проект «{r['name']}»: перерасход часов {r['overtime_ratio']:.2f}x",
                })
    return anomalies


def detect_task_anomalies(tasks: pd.DataFrame, devs: pd.DataFrame) -> List[dict]:
    anomalies = []
    done = tasks[tasks["actual_hours"] > 0].copy()
    if len(done) > 0:
        done["ratio"] = done["actual_hours"] / done["estimated_hours"].replace(0, 1)
        for _, r in done[done["ratio"] > 2.0].iterrows():
            anomalies.append({
                "type": "task_overtime", "entity": r.get("title", f"#{r['id']}"),
                "metric": "hours_overrun", "value": round(r["ratio"], 2),
                "severity": "high" if r["ratio"] > 3 else "medium",
                "description": f"Задача «{r.get('title','')}»: {r['actual_hours']:.0f}ч vs {r['estimated_hours']:.0f}ч ({r['ratio']:.1f}x)",
            })
    for _, r in tasks[tasks["reopen_count"] >= 3].iterrows():
        anomalies.append({
            "type": "task_high_reopen", "entity": r.get("title", f"#{r['id']}"),
            "metric": "reopen_count", "value": int(r["reopen_count"]),
            "severity": "high" if r["reopen_count"] >= 4 else "medium",
            "description": f"Задача «{r.get('title','')}» переоткрыта {r['reopen_count']} раз",
        })
    return anomalies


def detect_all_anomalies(data: Dict[str, pd.DataFrame]) -> List[dict]:
    logger.info("Running anomaly detection...")
    anomalies = []
    if "project_metrics" in data:
        anomalies.extend(detect_project_anomalies(data["project_metrics"]))
    if "tasks" in data and "developers" in data:
        anomalies.extend(detect_task_anomalies(data["tasks"], data["developers"]))
    sev = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    anomalies.sort(key=lambda x: sev.get(x.get("severity", "low"), 3))
    logger.info(f"  Found {len(anomalies)} anomalies")
    return anomalies
