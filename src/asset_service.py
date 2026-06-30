# Read queries and audit helper

"""
asset_service.py

Service functions for the Hospitality Asset Readiness Platform.

This module handles fictional asset inventory, check-out/check-in actions,
uniform inventory, operational issues, and the audit trail.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from src.database import fetch_all, get_connection


VALID_CONDITION_STATUSES = {
    "Excellent",
    "Good",
    "Fair",
    "Needs Repair",
}

VALID_ISSUE_STATUSES = {
    "Open",
    "In Progress",
    "Resolved",
}


def get_current_timestamp() -> str:
    """Return a consistent timestamp for local fictional audit events."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def write_audit_log(
    connection: Any,
    entity_type: str,
    entity_id: str,
    action_type: str,
    actor_name: str,
    details: str,
) -> None:
    """
    Add one event to the fictional audit log.

    This helper is called inside the same database transaction as the
    related business action, such as checking out an asset.
    """
    connection.execute(
        """
        INSERT INTO audit_log (
            entity_type,
            entity_id,
            action_type,
            actor_name,
            event_time,
            details
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            entity_type,
            entity_id,
            action_type,
            actor_name,
            get_current_timestamp(),
            details,
        ),
    )


def get_departments() -> list[dict[str, Any]]:
    """Return all fictional hotel departments."""
    return fetch_all(
        """
        SELECT
            department_id,
            department_name,
            staffing_target
        FROM departments
        ORDER BY department_name
        """
    )


def get_employees(
    department_id: int | None = None,
) -> list[dict[str, Any]]:
    """
    Return active fictional employees.

    When a department is provided, return only active employees assigned
    to that department.
    """
    query = """
        SELECT
            e.employee_id,
            e.employee_name,
            e.job_title,
            e.shift_name,
            e.department_id,
            d.department_name
        FROM employees AS e
        INNER JOIN departments AS d
            ON e.department_id = d.department_id
        WHERE e.active = 1
    """

    parameters: tuple[Any, ...] = ()

    if department_id is not None:
        query += " AND e.department_id = ?"
        parameters = (department_id,)

    query += " ORDER BY e.employee_name"

    return fetch_all(query, parameters)


def get_assets() -> list[dict[str, Any]]:
    """
    Return fictional asset inventory, including any active assignment.
    """
    return fetch_all(
        """
        SELECT
            a.asset_id,
            a.asset_type,
            a.asset_name,
            a.status,
            a.condition_status,
            a.purchase_year,
            a.last_inspection_date,
            a.notes,
            d.department_id,
            d.department_name,
            e.employee_id AS checked_out_employee_id,
            e.employee_name AS checked_out_to,
            aa.checked_out_at,
            aa.due_back_at
        FROM assets AS a
        INNER JOIN departments AS d
            ON a.assigned_department_id = d.department_id
        LEFT JOIN asset_assignments AS aa
            ON a.asset_id = aa.asset_id
            AND aa.checked_in_at IS NULL
        LEFT JOIN employees AS e
            ON aa.employee_id = e.employee_id
        ORDER BY
            d.department_name,
            a.asset_type,
            a.asset_name
        """
    )


def get_open_assignments() -> list[dict[str, Any]]:
    """Return fictional assets that are currently checked out."""
    return fetch_all(
        """
        SELECT
            aa.assignment_id,
            aa.asset_id,
            a.asset_name,
            a.asset_type,
            d.department_name,
            e.employee_id,
            e.employee_name,
            aa.checked_out_at,
            aa.due_back_at,
            aa.checked_out_by,
            aa.notes
        FROM asset_assignments AS aa
        INNER JOIN assets AS a
            ON aa.asset_id = a.asset_id
        INNER JOIN employees AS e
            ON aa.employee_id = e.employee_id
        INNER JOIN departments AS d
            ON a.assigned_department_id = d.department_id
        WHERE aa.checked_in_at IS NULL
        ORDER BY aa.checked_out_at DESC
        """
    )


def get_uniform_inventory() -> list[dict[str, Any]]:
    """Return fictional uniform inventory with shortage calculations."""
    return fetch_all(
        """
        SELECT
            ui.inventory_id,
            d.department_id,
            d.department_name,
            ui.garment_type,
            ui.size_label,
            ui.ready_quantity,
            ui.repair_quantity,
            ui.damaged_quantity,
            ui.reorder_point,
            ui.last_updated,
            CASE
                WHEN ui.ready_quantity < ui.reorder_point
                THEN ui.reorder_point - ui.ready_quantity
                ELSE 0
            END AS shortage_amount
        FROM uniform_inventory AS ui
        INNER JOIN departments AS d
            ON ui.department_id = d.department_id
        ORDER BY
            shortage_amount DESC,
            d.department_name,
            ui.garment_type,
            ui.size_label
        """
    )


def get_operational_issues(
    include_resolved: bool = True,
) -> list[dict[str, Any]]:
    """
    Return fictional operational issues.

    Set include_resolved to False when the dashboard should display only
    issues that still require attention.
    """
    query = """
        SELECT
            oi.issue_id,
            oi.department_id,
            d.department_name,
            oi.issue_title,
            oi.issue_type,
            oi.priority,
            oi.status,
            oi.opened_at,
            oi.owner_name,
            oi.details
        FROM operational_issues AS oi
        INNER JOIN departments AS d
            ON oi.department_id = d.department_id
    """

    if not include_resolved:
        query += " WHERE oi.status != 'Resolved'"

    query += """
        ORDER BY
            CASE oi.priority
                WHEN 'Critical' THEN 1
                WHEN 'High' THEN 2
                WHEN 'Medium' THEN 3
                ELSE 4
            END,
            oi.opened_at DESC
    """

    return fetch_all(query)


def get_audit_events(limit: int = 50) -> list[dict[str, Any]]:
    """Return the most recent fictional operational audit events."""
    return fetch_all(
        """
        SELECT
            audit_id,
            entity_type,
            entity_id,
            action_type,
            actor_name,
            event_time,
            details
        FROM audit_log
        ORDER BY event_time DESC, audit_id DESC
        LIMIT ?
        """,
        (limit,),
    )
    
# Check-out, check-in, and issue-management actions
    
def check_out_asset(
    asset_id: str,
    employee_id: str,
    checked_out_by: str,
    due_back_at: str | None = None,
    notes: str = "",
) -> dict[str, str]:
    """
    Check out an available fictional asset to an active employee.

    The action updates the asset status, creates an assignment record,
    and writes an audit event in one transaction.
    """
    with get_connection() as connection:
        asset = connection.execute(
            """
            SELECT
                asset_id,
                asset_name,
                status
            FROM assets
            WHERE asset_id = ?
            """,
            (asset_id,),
        ).fetchone()

        if asset is None:
            raise ValueError("The selected asset does not exist.")

        if asset["status"] != "Available":
            raise ValueError(
                "Only assets with Available status can be checked out."
            )

        employee = connection.execute(
            """
            SELECT
                employee_id,
                employee_name,
                active
            FROM employees
            WHERE employee_id = ?
            """,
            (employee_id,),
        ).fetchone()

        if employee is None or employee["active"] != 1:
            raise ValueError(
                "The selected employee is not available for assignment."
            )

        existing_assignment = connection.execute(
            """
            SELECT assignment_id
            FROM asset_assignments
            WHERE asset_id = ?
              AND checked_in_at IS NULL
            """,
            (asset_id,),
        ).fetchone()

        if existing_assignment is not None:
            raise ValueError(
                "This asset already has an active assignment."
            )

        checked_out_at = get_current_timestamp()

        connection.execute(
            """
            INSERT INTO asset_assignments (
                asset_id,
                employee_id,
                checked_out_at,
                due_back_at,
                checked_in_at,
                checked_out_by,
                notes
            )
            VALUES (?, ?, ?, ?, NULL, ?, ?)
            """,
            (
                asset_id,
                employee_id,
                checked_out_at,
                due_back_at,
                checked_out_by,
                notes,
            ),
        )

        connection.execute(
            """
            UPDATE assets
            SET status = 'Checked Out'
            WHERE asset_id = ?
            """,
            (asset_id,),
        )

        write_audit_log(
            connection=connection,
            entity_type="Asset",
            entity_id=asset_id,
            action_type="Checked Out",
            actor_name=checked_out_by,
            details=(
                f"Assigned {asset['asset_name']} to "
                f"{employee['employee_name']}."
            ),
        )

    return {
        "message": (
            f"{asset['asset_name']} was checked out to "
            f"{employee['employee_name']}."
        )
    }


def check_in_asset(
    asset_id: str,
    received_by: str,
    condition_status: str,
    notes: str = "",
) -> dict[str, str]:
    """
    Check in a fictional asset and update its recorded condition.

    Assets checked in as Needs Repair are automatically placed into
    Maintenance status instead of Available status.
    """
    if condition_status not in VALID_CONDITION_STATUSES:
        raise ValueError("The selected condition status is not valid.")

    with get_connection() as connection:
        assignment = connection.execute(
            """
            SELECT
                aa.assignment_id,
                aa.notes,
                a.asset_name,
                e.employee_name
            FROM asset_assignments AS aa
            INNER JOIN assets AS a
                ON aa.asset_id = a.asset_id
            INNER JOIN employees AS e
                ON aa.employee_id = e.employee_id
            WHERE aa.asset_id = ?
              AND aa.checked_in_at IS NULL
            """,
            (asset_id,),
        ).fetchone()

        if assignment is None:
            raise ValueError(
                "This asset does not have an active check-out record."
            )

        checked_in_at = get_current_timestamp()

        existing_notes = assignment["notes"] or ""
        combined_notes = existing_notes

        if notes.strip():
            combined_notes = (
                f"{existing_notes} | Check-in note: {notes.strip()}"
                if existing_notes
                else f"Check-in note: {notes.strip()}"
            )

        new_asset_status = (
            "Maintenance"
            if condition_status == "Needs Repair"
            else "Available"
        )

        connection.execute(
            """
            UPDATE asset_assignments
            SET
                checked_in_at = ?,
                notes = ?
            WHERE assignment_id = ?
            """,
            (
                checked_in_at,
                combined_notes,
                assignment["assignment_id"],
            ),
        )

        connection.execute(
            """
            UPDATE assets
            SET
                status = ?,
                condition_status = ?
            WHERE asset_id = ?
            """,
            (
                new_asset_status,
                condition_status,
                asset_id,
            ),
        )

        write_audit_log(
            connection=connection,
            entity_type="Asset",
            entity_id=asset_id,
            action_type="Checked In",
            actor_name=received_by,
            details=(
                f"Checked in {assignment['asset_name']} from "
                f"{assignment['employee_name']}. "
                f"New condition: {condition_status}."
            ),
        )

    return {
        "message": (
            f"{assignment['asset_name']} was checked in and marked "
            f"{condition_status}."
        )
    }


def get_next_issue_id(connection: Any) -> str:
    """Create the next readable fictional operational-issue ID."""
    issue_rows = connection.execute(
        """
        SELECT issue_id
        FROM operational_issues
        """
    ).fetchall()

    existing_numbers = []

    for row in issue_rows:
        try:
            existing_numbers.append(int(row["issue_id"].split("-")[1]))
        except (IndexError, ValueError):
            continue

    next_number = max(existing_numbers, default=0) + 1

    return f"ISS-{next_number:03d}"


def create_operational_issue(
    department_id: int,
    issue_title: str,
    issue_type: str,
    priority: str,
    owner_name: str,
    details: str = "",
) -> dict[str, str]:
    """
    Create a new fictional operational issue and record it in the audit log.
    """
    if priority not in {"Low", "Medium", "High", "Critical"}:
        raise ValueError("The selected issue priority is not valid.")

    if not issue_title.strip():
        raise ValueError("An issue title is required.")

    with get_connection() as connection:
        department = connection.execute(
            """
            SELECT department_name
            FROM departments
            WHERE department_id = ?
            """,
            (department_id,),
        ).fetchone()

        if department is None:
            raise ValueError("The selected department does not exist.")

        issue_id = get_next_issue_id(connection)
        opened_at = get_current_timestamp()

        connection.execute(
            """
            INSERT INTO operational_issues (
                issue_id,
                department_id,
                issue_title,
                issue_type,
                priority,
                status,
                opened_at,
                owner_name,
                details
            )
            VALUES (?, ?, ?, ?, ?, 'Open', ?, ?, ?)
            """,
            (
                issue_id,
                department_id,
                issue_title.strip(),
                issue_type.strip(),
                priority,
                opened_at,
                owner_name.strip(),
                details.strip(),
            ),
        )

        write_audit_log(
            connection=connection,
            entity_type="Issue",
            entity_id=issue_id,
            action_type="Issue Created",
            actor_name=owner_name,
            details=(
                f"Created {priority}-priority issue for "
                f"{department['department_name']}: {issue_title.strip()}."
            ),
        )

    return {
        "issue_id": issue_id,
        "message": f"Created issue {issue_id}.",
    }


def update_issue_status(
    issue_id: str,
    new_status: str,
    updated_by: str,
) -> dict[str, str]:
    """
    Update the status of a fictional operational issue.
    """
    if new_status not in VALID_ISSUE_STATUSES:
        raise ValueError("The selected issue status is not valid.")

    with get_connection() as connection:
        issue = connection.execute(
            """
            SELECT
                issue_id,
                issue_title,
                status
            FROM operational_issues
            WHERE issue_id = ?
            """,
            (issue_id,),
        ).fetchone()

        if issue is None:
            raise ValueError("The selected issue does not exist.")

        connection.execute(
            """
            UPDATE operational_issues
            SET status = ?
            WHERE issue_id = ?
            """,
            (new_status, issue_id),
        )

        write_audit_log(
            connection=connection,
            entity_type="Issue",
            entity_id=issue_id,
            action_type="Issue Status Updated",
            actor_name=updated_by,
            details=(
                f"Updated '{issue['issue_title']}' from "
                f"{issue['status']} to {new_status}."
            ),
        )

    return {
        "message": f"{issue_id} status updated to {new_status}.",
    }    