"""
analytics.py

Dashboard-ready analytics for the Hospitality Asset Readiness Platform.

This module combines fictional asset, uniform, issue, audit, and readiness
data into Pandas DataFrames that can be displayed in Streamlit and exported
as CSV files.
"""

from __future__ import annotations

from typing import Any

import pandas as pd

from src.asset_service import (
    get_assets,
    get_audit_events,
    get_operational_issues,
    get_uniform_inventory,
)
from src.readiness_engine import build_readiness_report


def create_readiness_dataframe(
    department_scores: list[dict[str, Any]],
) -> pd.DataFrame:
    """
    Convert department readiness results into a chart-ready DataFrame.
    """
    readiness_df = pd.DataFrame(department_scores)

    if readiness_df.empty:
        return readiness_df

    return readiness_df[
        [
            "department_id",
            "department_name",
            "readiness_score",
            "readiness_level",
            "asset_score",
            "uniform_score",
            "issue_score",
            "tracked_assets",
            "available_assets",
            "maintenance_assets",
            "uniform_shortage_lines",
            "open_issues",
            "recommendations",
        ]
    ]


def create_asset_status_summary(assets_df: pd.DataFrame) -> pd.DataFrame:
    """
    Count fictional assets by operational status.

    Examples include Available, Checked Out, and Maintenance.
    """
    if assets_df.empty:
        return pd.DataFrame(columns=["status", "asset_count"])

    return (
        assets_df.groupby("status", as_index=False)
        .agg(asset_count=("asset_id", "count"))
        .sort_values("asset_count", ascending=False)
        .reset_index(drop=True)
    )


def create_asset_condition_summary(
    assets_df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Count fictional assets by recorded condition status.
    """
    if assets_df.empty:
        return pd.DataFrame(
            columns=["condition_status", "asset_count"]
        )

    return (
        assets_df.groupby("condition_status", as_index=False)
        .agg(asset_count=("asset_id", "count"))
        .sort_values("asset_count", ascending=False)
        .reset_index(drop=True)
    )


def create_department_asset_summary(
    assets_df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Summarize available and unavailable assets by department.
    """
    if assets_df.empty:
        return pd.DataFrame()

    assets_with_flags = assets_df.copy()

    assets_with_flags["available_count"] = (
        assets_with_flags["status"] == "Available"
    ).astype(int)

    assets_with_flags["maintenance_count"] = (
        assets_with_flags["status"] == "Maintenance"
    ).astype(int)

    assets_with_flags["checked_out_count"] = (
        assets_with_flags["status"] == "Checked Out"
    ).astype(int)

    return (
        assets_with_flags.groupby("department_name", as_index=False)
        .agg(
            tracked_assets=("asset_id", "count"),
            available_assets=("available_count", "sum"),
            checked_out_assets=("checked_out_count", "sum"),
            maintenance_assets=("maintenance_count", "sum"),
        )
        .sort_values(
            by=["maintenance_assets", "available_assets"],
            ascending=[False, False],
        )
        .reset_index(drop=True)
    )


def create_uniform_shortage_summary(
    uniforms_df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Return only uniform inventory lines below their reorder point.
    """
    if uniforms_df.empty:
        return uniforms_df

    shortage_df = uniforms_df.loc[
        uniforms_df["shortage_amount"] > 0
    ].copy()

    return shortage_df.sort_values(
        by=["shortage_amount", "department_name"],
        ascending=[False, True],
    ).reset_index(drop=True)


def create_issue_priority_summary(
    issues_df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Count unresolved issues by priority level.
    """
    if issues_df.empty:
        return pd.DataFrame(columns=["priority", "issue_count"])

    priority_order = {
        "Critical": 1,
        "High": 2,
        "Medium": 3,
        "Low": 4,
    }

    summary_df = (
        issues_df.groupby("priority", as_index=False)
        .agg(issue_count=("issue_id", "count"))
    )

    summary_df["priority_order"] = summary_df["priority"].map(
        priority_order
    )

    return (
        summary_df.sort_values("priority_order")
        .drop(columns="priority_order")
        .reset_index(drop=True)
    )


def create_recommendation_dataframe(
    department_scores: list[dict[str, Any]],
) -> pd.DataFrame:
    """
    Flatten department recommendations into one row per recommendation.
    """
    recommendation_rows: list[dict[str, Any]] = []

    for department in department_scores:
        for recommendation in department["recommendations"]:
            recommendation_rows.append(
                {
                    "department_name": department["department_name"],
                    "readiness_score": department["readiness_score"],
                    "readiness_level": department["readiness_level"],
                    "recommendation": recommendation,
                }
            )

    recommendation_df = pd.DataFrame(recommendation_rows)

    if recommendation_df.empty:
        return recommendation_df

    return recommendation_df.sort_values(
        by=["readiness_score", "department_name"],
        ascending=[True, True],
    ).reset_index(drop=True)


def build_dashboard_data() -> dict[str, Any]:
    """
    Build every table and metric needed by the Streamlit dashboard.

    Returns
    -------
    dict[str, Any]
        Dashboard-ready DataFrames and high-level fictional portfolio metrics.
    """
    readiness_report = build_readiness_report()

    readiness_df = create_readiness_dataframe(
        readiness_report["department_scores"]
    )

    assets_df = pd.DataFrame(get_assets())
    uniforms_df = pd.DataFrame(get_uniform_inventory())
    open_issues_df = pd.DataFrame(
        get_operational_issues(include_resolved=False)
    )
    audit_df = pd.DataFrame(get_audit_events(limit=50))

    return {
        "portfolio_metrics": readiness_report["portfolio_metrics"],
        "readiness_df": readiness_df,
        "assets_df": assets_df,
        "uniforms_df": uniforms_df,
        "open_issues_df": open_issues_df,
        "audit_df": audit_df,
        "asset_status_summary": create_asset_status_summary(assets_df),
        "asset_condition_summary": create_asset_condition_summary(
            assets_df
        ),
        "department_asset_summary": create_department_asset_summary(
            assets_df
        ),
        "uniform_shortage_summary": create_uniform_shortage_summary(
            uniforms_df
        ),
        "issue_priority_summary": create_issue_priority_summary(
            open_issues_df
        ),
        "recommendations_df": create_recommendation_dataframe(
            readiness_report["department_scores"]
        ),
    }