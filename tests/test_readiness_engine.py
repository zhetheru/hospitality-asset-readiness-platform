"""
test_readiness_engine.py

Automated tests for the Hospitality Asset Readiness Platform.

Each test begins and ends with a newly seeded fictional SQLite database,
so workflow tests do not leave temporary records in the final demo data.
"""

from __future__ import annotations

import pytest

from data.seed_data import seed_database
from src import database
from src.asset_service import (
    check_in_asset,
    check_out_asset,
    create_operational_issue,
    get_assets,
    get_open_assignments,
    get_operational_issues,
    update_issue_status,
)
from src.readiness_engine import (
    build_readiness_report,
    get_low_uniform_items,
)


@pytest.fixture(autouse=True)
def use_isolated_test_database(tmp_path, monkeypatch) -> None:
    """
    Give every test its own temporary SQLite database.

    This prevents automated tests from changing or locking the dashboard's
    local demonstration database while Streamlit or another program is open.
    """
    test_database_path = tmp_path / "hospitality_assets_test.db"

    # Redirect the application's database utility to a unique temporary file
    # for this one test only.
    monkeypatch.setattr(
        database,
        "DATABASE_PATH",
        test_database_path,
    )

    # Seed the temporary database with the same fictional sample records
    # used by the application.
    seed_database()

    yield


def test_readiness_report_has_expected_portfolio_metrics() -> None:
    """The seeded data should produce a consistent readiness report."""
    report = build_readiness_report()

    metrics = report["portfolio_metrics"]
    department_scores = {
        item["department_name"]: item
        for item in report["department_scores"]
    }

    assert metrics["overall_readiness_score"] == 86.6
    assert metrics["open_issues"] == 5
    assert metrics["maintenance_assets"] == 1
    assert metrics["uniform_shortage_lines"] == 7

    assert len(department_scores) == 6
    assert department_scores["Housekeeping"]["readiness_score"] == 70.0
    assert department_scores["Housekeeping"]["readiness_level"] == "Monitor"
    assert department_scores["Engineering"]["readiness_level"] == "Ready"


def test_low_uniform_items_match_expected_shortage_count() -> None:
    """The seeded inventory should contain seven uniform shortage lines."""
    shortage_items = get_low_uniform_items()

    assert len(shortage_items) == 7

    housekeeping_medium_polo = next(
        item
        for item in shortage_items
        if item["department_name"] == "Housekeeping"
        and item["garment_type"] == "Housekeeping Polo"
        and item["size_label"] == "Medium"
    )

    assert housekeeping_medium_polo["ready_quantity"] == 12
    assert housekeeping_medium_polo["reorder_point"] == 18


def test_asset_checkout_and_checkin_workflow() -> None:
    """An available asset should be checked out, then returned successfully."""
    checkout_result = check_out_asset(
        asset_id="LAP-001",
        employee_id="EMP-010",
        checked_out_by="Test Runner",
        due_back_at="2026-07-02 23:59:00",
        notes="Automated workflow test.",
    )

    assert "checked out" in checkout_result["message"].lower()

    assets_after_checkout = {
        asset["asset_id"]: asset
        for asset in get_assets()
    }

    assert assets_after_checkout["LAP-001"]["status"] == "Checked Out"
    assert assets_after_checkout["LAP-001"]["checked_out_to"] == "Morgan Ellis"

    active_assignments = get_open_assignments()

    assert any(
        assignment["asset_id"] == "LAP-001"
        for assignment in active_assignments
    )

    checkin_result = check_in_asset(
        asset_id="LAP-001",
        received_by="Test Runner",
        condition_status="Excellent",
        notes="Returned after automated workflow test.",
    )

    assert "checked in" in checkin_result["message"].lower()

    assets_after_checkin = {
        asset["asset_id"]: asset
        for asset in get_assets()
    }

    assert assets_after_checkin["LAP-001"]["status"] == "Available"
    assert assets_after_checkin["LAP-001"]["condition_status"] == "Excellent"
    assert assets_after_checkin["LAP-001"]["checked_out_to"] is None

    active_assignments_after_checkin = get_open_assignments()

    assert not any(
        assignment["asset_id"] == "LAP-001"
        for assignment in active_assignments_after_checkin
    )


def test_operational_issue_can_be_created_and_resolved() -> None:
    """A newly created fictional issue should disappear from open issues when resolved."""
    created_issue = create_operational_issue(
        department_id=6,
        issue_title="Automated test workflow issue",
        issue_type="Asset Readiness",
        priority="Low",
        owner_name="Test Runner",
        details="Temporary fictional issue for automated testing.",
    )

    issue_id = created_issue["issue_id"]

    open_issues = get_operational_issues(include_resolved=False)

    assert any(
        issue["issue_id"] == issue_id
        and issue["status"] == "Open"
        for issue in open_issues
    )

    update_result = update_issue_status(
        issue_id=issue_id,
        new_status="Resolved",
        updated_by="Test Runner",
    )

    assert "resolved" in update_result["message"].lower()

    open_issues_after_update = get_operational_issues(
        include_resolved=False
    )

    assert not any(
        issue["issue_id"] == issue_id
        for issue in open_issues_after_update
    )

    all_issues = get_operational_issues(include_resolved=True)

    resolved_issue = next(
        issue
        for issue in all_issues
        if issue["issue_id"] == issue_id
    )

    assert resolved_issue["status"] == "Resolved"
    