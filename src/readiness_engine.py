"""
readiness_engine.py

Rule-based readiness scoring for the Hospitality Asset Readiness Platform.

This module translates fictional asset, uniform, and operational-issue data
into department readiness scores and practical recommendations.

The scoring model is intentionally transparent and educational. It is not a
replacement for a hotel's internal policies, safety procedures, or management
decision-making process.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from src.database import fetch_all


# Readiness labels make the score easier to interpret in the future dashboard.
READINESS_LEVELS = [
    (85, "Ready"),
    (70, "Monitor"),
    (50, "At Risk"),
    (0, "Needs Attention"),
]

# Open issues affect readiness differently based on their priority.
ISSUE_PRIORITY_PENALTIES = {
    "Critical": 40,
    "High": 25,
    "Medium": 12,
    "Low": 5,
}


def get_readiness_level(score: float) -> str:
    """
    Convert a numeric readiness score into a plain-language level.
    """
    for minimum_score, level in READINESS_LEVELS:
        if score >= minimum_score:
            return level

    return "Needs Attention"


def clamp_score(score: float) -> float:
    """
    Keep a calculated score within the valid 0 to 100 range.
    """
    return max(0.0, min(100.0, score))


def get_asset_summary() -> list[dict[str, Any]]:
    """
    Summarize fictional assets by assigned department.

    Checked-out assets are still considered operational because they are in use
    by staff. Assets in Maintenance or Retired status are not operational.
    """
    return fetch_all(
        """
        SELECT
            d.department_id,
            d.department_name,
            COUNT(a.asset_id) AS tracked_assets,
            SUM(
                CASE
                    WHEN a.status IN ('Available', 'Checked Out') THEN 1
                    ELSE 0
                END
            ) AS operational_assets,
            SUM(
                CASE
                    WHEN a.status = 'Available' THEN 1
                    ELSE 0
                END
            ) AS available_assets,
            SUM(
                CASE
                    WHEN a.status = 'Checked Out' THEN 1
                    ELSE 0
                END
            ) AS checked_out_assets,
            SUM(
                CASE
                    WHEN a.status = 'Maintenance' THEN 1
                    ELSE 0
                END
            ) AS maintenance_assets,
            SUM(
                CASE
                    WHEN a.condition_status = 'Fair' THEN 1
                    ELSE 0
                END
            ) AS fair_condition_assets,
            SUM(
                CASE
                    WHEN a.condition_status = 'Needs Repair' THEN 1
                    ELSE 0
                END
            ) AS needs_repair_assets
        FROM departments AS d
        LEFT JOIN assets AS a
            ON d.department_id = a.assigned_department_id
        GROUP BY
            d.department_id,
            d.department_name
        ORDER BY d.department_name
        """
    )


def get_uniform_summary() -> list[dict[str, Any]]:
    """
    Summarize fictional uniform readiness by department.

    A uniform line is considered below threshold when its ready-to-issue
    quantity is less than its defined reorder point.
    """
    return fetch_all(
        """
        SELECT
            d.department_id,
            d.department_name,
            COUNT(ui.inventory_id) AS uniform_lines,
            SUM(COALESCE(ui.ready_quantity, 0)) AS ready_quantity,
            SUM(COALESCE(ui.repair_quantity, 0)) AS repair_quantity,
            SUM(COALESCE(ui.damaged_quantity, 0)) AS damaged_quantity,
            SUM(
                CASE
                    WHEN ui.ready_quantity < ui.reorder_point THEN 1
                    ELSE 0
                END
            ) AS below_reorder_lines
        FROM departments AS d
        LEFT JOIN uniform_inventory AS ui
            ON d.department_id = ui.department_id
        GROUP BY
            d.department_id,
            d.department_name
        ORDER BY d.department_name
        """
    )


def get_open_issue_summary() -> list[dict[str, Any]]:
    """
    Return unresolved fictional operational issues grouped by department.
    """
    return fetch_all(
        """
        SELECT
            oi.issue_id,
            oi.department_id,
            d.department_name,
            oi.issue_title,
            oi.issue_type,
            oi.priority,
            oi.status,
            oi.owner_name,
            oi.details
        FROM operational_issues AS oi
        INNER JOIN departments AS d
            ON oi.department_id = d.department_id
        WHERE oi.status != 'Resolved'
        ORDER BY
            oi.department_id,
            CASE oi.priority
                WHEN 'Critical' THEN 1
                WHEN 'High' THEN 2
                WHEN 'Medium' THEN 3
                ELSE 4
            END
        """
    )


def get_low_uniform_items() -> list[dict[str, Any]]:
    """
    Return uniform records that have fallen below their reorder point.
    """
    return fetch_all(
        """
        SELECT
            ui.department_id,
            d.department_name,
            ui.garment_type,
            ui.size_label,
            ui.ready_quantity,
            ui.reorder_point,
            ui.repair_quantity,
            ui.damaged_quantity
        FROM uniform_inventory AS ui
        INNER JOIN departments AS d
            ON ui.department_id = d.department_id
        WHERE ui.ready_quantity < ui.reorder_point
        ORDER BY
            ui.department_id,
            ui.ready_quantity ASC
        """
    )


def calculate_asset_score(asset_summary: dict[str, Any]) -> float:
    """
    Score operational asset readiness from 0 to 100.

    Working assets include both Available and Checked Out items because a
    checked-out asset is still supporting an active staff workflow.
    """
    tracked_assets = int(asset_summary["tracked_assets"] or 0)

    if tracked_assets == 0:
        return 100.0

    operational_assets = int(asset_summary["operational_assets"] or 0)
    fair_assets = int(asset_summary["fair_condition_assets"] or 0)
    repair_assets = int(asset_summary["needs_repair_assets"] or 0)

    operational_ratio = operational_assets / tracked_assets

    # Asset condition applies a smaller penalty than full unavailability.
    condition_penalty = (fair_assets * 2) + (repair_assets * 5)

    score = (operational_ratio * 100) - condition_penalty
    return round(clamp_score(score), 1)


def calculate_uniform_score(uniform_summary: dict[str, Any]) -> float:
    """
    Score uniform readiness from 0 to 100.

    The score considers shortage lines, repair inventory, and damaged items.
    """
    uniform_lines = int(uniform_summary["uniform_lines"] or 0)

    if uniform_lines == 0:
        return 100.0

    below_reorder_lines = int(uniform_summary["below_reorder_lines"] or 0)
    ready_quantity = int(uniform_summary["ready_quantity"] or 0)
    repair_quantity = int(uniform_summary["repair_quantity"] or 0)
    damaged_quantity = int(uniform_summary["damaged_quantity"] or 0)

    total_uniform_items = (
        ready_quantity
        + repair_quantity
        + damaged_quantity
    )

    shortage_ratio = below_reorder_lines / uniform_lines

    repair_and_damage_ratio = (
        (repair_quantity + damaged_quantity) / total_uniform_items
        if total_uniform_items > 0
        else 0
    )

    # Shortages carry the strongest uniform-readiness penalty.
    shortage_penalty = shortage_ratio * 35
    condition_penalty = repair_and_damage_ratio * 20

    score = 100 - shortage_penalty - condition_penalty
    return round(clamp_score(score), 1)


def calculate_issue_score(
    department_issues: list[dict[str, Any]],
) -> float:
    """
    Score unresolved operational issues from 0 to 100.

    Open issues receive their full priority penalty. In-progress issues receive
    a reduced penalty because work has already begun.
    """
    total_penalty = 0.0

    for issue in department_issues:
        priority_penalty = ISSUE_PRIORITY_PENALTIES[issue["priority"]]

        if issue["status"] == "In Progress":
            priority_penalty *= 0.6

        total_penalty += priority_penalty

    return round(clamp_score(100 - total_penalty), 1)


def create_recommendations(
    department_name: str,
    asset_summary: dict[str, Any],
    uniform_summary: dict[str, Any],
    department_issues: list[dict[str, Any]],
    low_uniform_items: list[dict[str, Any]],
) -> list[str]:
    """
    Create transparent, rule-based recommendations for a department.
    """
    recommendations: list[str] = []

    maintenance_assets = int(asset_summary["maintenance_assets"] or 0)
    available_assets = int(asset_summary["available_assets"] or 0)
    tracked_assets = int(asset_summary["tracked_assets"] or 0)
    needs_repair_assets = int(asset_summary["needs_repair_assets"] or 0)

    if maintenance_assets > 0:
        recommendations.append(
            f"Prioritize maintenance for {maintenance_assets} unavailable "
            f"asset(s) assigned to {department_name}."
        )

    if needs_repair_assets > 0:
        recommendations.append(
            f"Review replacement or repair planning for {needs_repair_assets} "
            f"asset(s) marked Needs Repair."
        )

    if tracked_assets > 0 and available_assets / tracked_assets < 0.5:
        recommendations.append(
            "Confirm asset assignments and available backup equipment before "
            "the next shift."
        )

    department_uniform_shortages = [
        item
        for item in low_uniform_items
        if item["department_name"] == department_name
    ]

    for item in department_uniform_shortages:
        recommendations.append(
            f"Replenish {item['garment_type']} in size {item['size_label']}: "
            f"{item['ready_quantity']} ready, reorder point "
            f"{item['reorder_point']}."
        )

    urgent_issues = [
        issue
        for issue in department_issues
        if issue["priority"] in {"Critical", "High"}
        and issue["status"] != "Resolved"
    ]

    for issue in urgent_issues:
        recommendations.append(
            f"Escalate {issue['priority'].lower()}-priority issue: "
            f"{issue['issue_title']}."
        )

    if not recommendations:
        recommendations.append(
            "Maintain current readiness controls and continue routine "
            "inspection, assignment, and inventory review."
        )

    return recommendations


def build_readiness_report() -> dict[str, Any]:
    """
    Build a complete readiness report for every fictional hotel department.

    The final department score uses:
    - 40% asset readiness
    - 30% uniform readiness
    - 30% unresolved operational issue readiness
    """
    asset_summaries = get_asset_summary()
    uniform_summaries = get_uniform_summary()
    open_issues = get_open_issue_summary()
    low_uniform_items = get_low_uniform_items()

    uniform_by_department = {
        item["department_id"]: item
        for item in uniform_summaries
    }

    issues_by_department: dict[int, list[dict[str, Any]]] = defaultdict(list)

    for issue in open_issues:
        issues_by_department[issue["department_id"]].append(issue)

    department_scores: list[dict[str, Any]] = []

    for asset_summary in asset_summaries:
        department_id = asset_summary["department_id"]
        department_name = asset_summary["department_name"]

        uniform_summary = uniform_by_department[department_id]
        department_issues = issues_by_department[department_id]

        asset_score = calculate_asset_score(asset_summary)
        uniform_score = calculate_uniform_score(uniform_summary)
        issue_score = calculate_issue_score(department_issues)

        readiness_score = round(
            (asset_score * 0.40)
            + (uniform_score * 0.30)
            + (issue_score * 0.30),
            1,
        )

        department_scores.append(
            {
                "department_id": department_id,
                "department_name": department_name,
                "readiness_score": readiness_score,
                "readiness_level": get_readiness_level(readiness_score),
                "asset_score": asset_score,
                "uniform_score": uniform_score,
                "issue_score": issue_score,
                "tracked_assets": int(asset_summary["tracked_assets"] or 0),
                "available_assets": int(asset_summary["available_assets"] or 0),
                "maintenance_assets": int(
                    asset_summary["maintenance_assets"] or 0
                ),
                "uniform_shortage_lines": int(
                    uniform_summary["below_reorder_lines"] or 0
                ),
                "open_issues": len(department_issues),
                "recommendations": create_recommendations(
                    department_name=department_name,
                    asset_summary=asset_summary,
                    uniform_summary=uniform_summary,
                    department_issues=department_issues,
                    low_uniform_items=low_uniform_items,
                ),
            }
        )

    department_scores.sort(
        key=lambda item: item["readiness_score"]
    )

    portfolio_score = round(
        sum(item["readiness_score"] for item in department_scores)
        / len(department_scores),
        1,
    )

    portfolio_metrics = {
        "overall_readiness_score": portfolio_score,
        "departments_ready": sum(
            item["readiness_level"] == "Ready"
            for item in department_scores
        ),
        "departments_to_monitor": sum(
            item["readiness_level"] == "Monitor"
            for item in department_scores
        ),
        "departments_at_risk": sum(
            item["readiness_level"] in {"At Risk", "Needs Attention"}
            for item in department_scores
        ),
        "open_issues": len(open_issues),
        "maintenance_assets": sum(
            item["maintenance_assets"]
            for item in department_scores
        ),
        "uniform_shortage_lines": len(low_uniform_items),
    }

    return {
        "department_scores": department_scores,
        "portfolio_metrics": portfolio_metrics,
        "open_issues": open_issues,
        "low_uniform_items": low_uniform_items,
    }