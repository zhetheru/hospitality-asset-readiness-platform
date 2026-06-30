# Imports, dashboard setup, and Operations Overview'

"""
app.py

Interactive application for the Hospitality Asset Readiness Platform.

This fictional portfolio application demonstrates how a hotel operations team
could monitor asset availability, uniforms, operational issues, audit events,
and department-level readiness through a SQLite-backed workflow.
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any

import pandas as pd
import plotly.express as px
import streamlit as st

from src.analytics import build_dashboard_data
from src.asset_service import (
    check_in_asset,
    check_out_asset,
    create_operational_issue,
    get_departments,
    get_employees,
    get_open_assignments,
    update_issue_status,
)


st.set_page_config(
    page_title="Hospitality Asset Readiness Platform",
    page_icon="🏨",
    layout="wide",
)


@st.cache_data(show_spinner="Loading fictional hospitality operations data...")
def load_dashboard_data() -> dict[str, Any]:
    """
    Load and cache dashboard-ready data from the local SQLite database.
    """
    return build_dashboard_data()


def dataframe_to_csv_bytes(dataframe: pd.DataFrame) -> bytes:
    """Convert a DataFrame into downloadable UTF-8 CSV bytes."""
    return dataframe.to_csv(index=False).encode("utf-8")


def refresh_dashboard_data(message: str) -> None:
    """
    Clear cached dashboard results, preserve a success message, and rerun.

    This is called after a local workflow action changes the SQLite database.
    """
    st.cache_data.clear()
    st.session_state["action_message"] = message
    st.rerun()


def render_page_header() -> None:
    """Display the application title, context, and portfolio limitations."""
    st.title("🏨 Hospitality Asset Readiness Platform")

    st.caption(
        "A fictional SQLite-backed operations platform for tracking hotel "
        "assets, uniforms, readiness risks, operational issues, and audit events."
    )

    st.info(
        "This is an educational portfolio prototype. All employee names, "
        "assets, inventory records, issues, and operational scenarios are "
        "fictional. The app does not use or represent proprietary hotel data."
    )

    with st.expander("How department readiness is calculated"):
        st.markdown(
            """
            Each department receives a transparent readiness score from 0 to 100.

            | Component | Weight | What It Measures |
            |---|---:|---|
            | Asset readiness | 40% | Available, checked-out, maintenance, and condition status |
            | Uniform readiness | 30% | Inventory shortages, repair quantities, and damaged items |
            | Issue readiness | 30% | Open and in-progress issues, weighted by priority |

            **Readiness levels**

            | Level | Score Range |
            |---|---:|
            | Ready | 85–100 |
            | Monitor | 70–84.9 |
            | At Risk | 50–69.9 |
            | Needs Attention | Below 50 |
            """
        )


def render_operations_overview(data: dict[str, Any]) -> None:
    """Display overall readiness, department comparisons, and recommendations."""
    portfolio_metrics = data["portfolio_metrics"]
    readiness_df = data["readiness_df"]
    asset_status_summary = data["asset_status_summary"]
    department_asset_summary = data["department_asset_summary"]
    issue_priority_summary = data["issue_priority_summary"]
    recommendations_df = data["recommendations_df"]

    st.subheader("Operations Overview")
    st.write(
        "This view summarizes fictional hotel readiness across equipment, "
        "uniform inventory, and unresolved operational issues."
    )

    metric_one, metric_two, metric_three, metric_four = st.columns(4)

    metric_one.metric(
        "Overall Readiness",
        f"{portfolio_metrics['overall_readiness_score']:.1f}",
    )
    metric_two.metric(
        "Departments Ready",
        portfolio_metrics["departments_ready"],
    )
    metric_three.metric(
        "Departments to Monitor",
        portfolio_metrics["departments_to_monitor"],
    )
    metric_four.metric(
        "Open Operational Issues",
        portfolio_metrics["open_issues"],
    )

    metric_five, metric_six, metric_seven = st.columns(3)

    metric_five.metric(
        "Tracked Assets",
        len(data["assets_df"]),
    )
    metric_six.metric(
        "Assets in Maintenance",
        portfolio_metrics["maintenance_assets"],
    )
    metric_seven.metric(
        "Uniform Shortage Lines",
        portfolio_metrics["uniform_shortage_lines"],
    )

    left_column, right_column = st.columns(2)

    with left_column:
        st.markdown("### Department Readiness")

        readiness_chart_data = readiness_df.sort_values(
            by="readiness_score",
            ascending=True,
        )

        readiness_chart = px.bar(
            readiness_chart_data,
            x="readiness_score",
            y="department_name",
            color="readiness_level",
            orientation="h",
            text="readiness_score",
            title="Department Readiness Score",
            labels={
                "readiness_score": "Readiness Score",
                "department_name": "Department",
                "readiness_level": "Readiness Level",
            },
            range_x=[0, 100],
        )

        st.plotly_chart(
            readiness_chart,
            width="stretch",
        )

    with right_column:
        st.markdown("### Asset Status Distribution")

        asset_status_chart = px.pie(
            asset_status_summary,
            values="asset_count",
            names="status",
            title="Tracked Assets by Current Status",
        )

        st.plotly_chart(
            asset_status_chart,
            width="stretch",
        )

    lower_left, lower_right = st.columns(2)

    with lower_left:
        st.markdown("### Department Asset Availability")

        department_asset_chart = px.bar(
            department_asset_summary,
            x="department_name",
            y=[
                "available_assets",
                "checked_out_assets",
                "maintenance_assets",
            ],
            barmode="stack",
            title="Asset Status by Department",
            labels={
                "department_name": "Department",
                "value": "Asset Count",
                "variable": "Asset Status",
            },
        )

        st.plotly_chart(
            department_asset_chart,
            width="stretch",
        )

    with lower_right:
        st.markdown("### Open Issue Priority")

        issue_chart = px.bar(
            issue_priority_summary,
            x="priority",
            y="issue_count",
            title="Unresolved Issues by Priority",
            labels={
                "priority": "Priority",
                "issue_count": "Open Issues",
            },
        )

        st.plotly_chart(
            issue_chart,
            width="stretch",
        )

    st.markdown("### Readiness Recommendations")

    if recommendations_df.empty:
        st.success("No readiness recommendations are currently required.")
    else:
        st.dataframe(
            recommendations_df,
            width="stretch",
            hide_index=True,
        )

    with st.expander("View Department Readiness Detail"):
        readable_readiness_df = readiness_df.drop(columns="recommendations")
        st.dataframe(
            readable_readiness_df,
            width="stretch",
            hide_index=True,
        )

    st.download_button(
        label="Download Department Readiness Report",
        data=dataframe_to_csv_bytes(readiness_df),
        file_name="department_readiness_report.csv",
        mime="text/csv",
        width="stretch",
    )
    
    
# Asset Inventory and Uniform Readiness

def render_asset_inventory(data: dict[str, Any]) -> None:
    """
    Display fictional asset inventory and provide check-out/check-in workflows.
    """
    assets_df = data["assets_df"]

    st.subheader("Asset Inventory")
    st.write(
        "Track fictional devices and equipment used by Front Office, "
        "Housekeeping, Engineering, Security, Food & Beverage, and Guest Services."
    )

    filter_one, filter_two, filter_three = st.columns(3)

    with filter_one:
        selected_department = st.selectbox(
            "Filter by department",
            options=["All"] + sorted(assets_df["department_name"].unique()),
            key="asset_department_filter",
        )

    with filter_two:
        selected_status = st.selectbox(
            "Filter by asset status",
            options=["All"] + sorted(assets_df["status"].unique()),
            key="asset_status_filter",
        )

    with filter_three:
        selected_condition = st.selectbox(
            "Filter by condition",
            options=["All"] + sorted(assets_df["condition_status"].unique()),
            key="asset_condition_filter",
        )

    filtered_assets = assets_df.copy()

    if selected_department != "All":
        filtered_assets = filtered_assets.loc[
            filtered_assets["department_name"] == selected_department
        ]

    if selected_status != "All":
        filtered_assets = filtered_assets.loc[
            filtered_assets["status"] == selected_status
        ]

    if selected_condition != "All":
        filtered_assets = filtered_assets.loc[
            filtered_assets["condition_status"] == selected_condition
        ]

    asset_metric_one, asset_metric_two, asset_metric_three = st.columns(3)

    asset_metric_one.metric(
        "Assets Displayed",
        len(filtered_assets),
    )
    asset_metric_two.metric(
        "Available",
        int((filtered_assets["status"] == "Available").sum()),
    )
    asset_metric_three.metric(
        "In Maintenance",
        int((filtered_assets["status"] == "Maintenance").sum()),
    )

    st.dataframe(
        filtered_assets[
            [
                "asset_id",
                "asset_type",
                "asset_name",
                "department_name",
                "status",
                "condition_status",
                "checked_out_to",
                "checked_out_at",
                "due_back_at",
                "last_inspection_date",
                "notes",
            ]
        ],
        width="stretch",
        hide_index=True,
    )

    st.download_button(
        label="Download Filtered Asset Inventory",
        data=dataframe_to_csv_bytes(filtered_assets),
        file_name="filtered_asset_inventory.csv",
        mime="text/csv",
    )

    st.divider()
    st.markdown("### Asset Assignment Workflow")
    st.caption(
        "All workflow actions update only the local fictional SQLite database "
        "and create a corresponding audit event."
    )

    checkout_tab, checkin_tab = st.tabs(
        ["Check Out Asset", "Check In Asset"]
    )

    with checkout_tab:
        available_assets = assets_df.loc[
            assets_df["status"] == "Available"
        ].copy()

        if available_assets.empty:
            st.info("No fictional assets are currently available for check-out.")
        else:
            asset_options = {
                f"{row['asset_id']} — {row['asset_name']}": row
                for _, row in available_assets.iterrows()
            }

            with st.form("check_out_asset_form", border=True):
                selected_asset_label = st.selectbox(
                    "Select available asset",
                    options=list(asset_options.keys()),
                )

                selected_asset = asset_options[selected_asset_label]

                eligible_employees = get_employees(
                    int(selected_asset["department_id"])
                )

                employee_options = {
                    f"{employee['employee_name']} — {employee['job_title']}": employee
                    for employee in eligible_employees
                }

                selected_employee_label = st.selectbox(
                    "Assign to employee",
                    options=list(employee_options.keys()),
                )

                due_date = st.date_input(
                    "Expected return date",
                    value=date.today() + timedelta(days=1),
                )

                checked_out_by = st.text_input(
                    "Checked out by",
                    value="Operations Supervisor",
                )

                checkout_notes = st.text_area(
                    "Assignment notes",
                    placeholder=(
                        "Example: Assigned for morning guest-arrival support."
                    ),
                )

                submit_checkout = st.form_submit_button(
                    "Check Out Selected Asset",
                    width="stretch",
                )

                if submit_checkout:
                    selected_employee = employee_options[
                        selected_employee_label
                    ]

                    due_back_at = f"{due_date.isoformat()} 23:59:00"

                    try:
                        result = check_out_asset(
                            asset_id=str(selected_asset["asset_id"]),
                            employee_id=str(selected_employee["employee_id"]),
                            checked_out_by=checked_out_by.strip()
                            or "Operations Supervisor",
                            due_back_at=due_back_at,
                            notes=checkout_notes,
                        )

                        refresh_dashboard_data(result["message"])

                    except ValueError as error:
                        st.error(str(error))

    with checkin_tab:
        open_assignments = get_open_assignments()

        if not open_assignments:
            st.info("No fictional assets are currently checked out.")
        else:
            assignment_options = {
                (
                    f"{assignment['asset_id']} — "
                    f"{assignment['asset_name']} "
                    f"(assigned to {assignment['employee_name']})"
                ): assignment
                for assignment in open_assignments
            }

            with st.form("check_in_asset_form", border=True):
                selected_assignment_label = st.selectbox(
                    "Select checked-out asset",
                    options=list(assignment_options.keys()),
                )

                selected_assignment = assignment_options[
                    selected_assignment_label
                ]

                condition_status = st.selectbox(
                    "Condition on return",
                    options=[
                        "Excellent",
                        "Good",
                        "Fair",
                        "Needs Repair",
                    ],
                    index=1,
                )

                received_by = st.text_input(
                    "Received by",
                    value="Operations Supervisor",
                )

                checkin_notes = st.text_area(
                    "Check-in notes",
                    placeholder=(
                        "Example: Device returned charged and ready for the "
                        "next shift."
                    ),
                )

                submit_checkin = st.form_submit_button(
                    "Check In Selected Asset",
                    width="stretch",
                )

                if submit_checkin:
                    try:
                        result = check_in_asset(
                            asset_id=str(selected_assignment["asset_id"]),
                            received_by=received_by.strip()
                            or "Operations Supervisor",
                            condition_status=condition_status,
                            notes=checkin_notes,
                        )

                        refresh_dashboard_data(result["message"])

                    except ValueError as error:
                        st.error(str(error))


def render_uniform_readiness(data: dict[str, Any]) -> None:
    """Display fictional uniform inventory and shortage signals."""
    uniforms_df = data["uniforms_df"]
    shortage_df = data["uniform_shortage_summary"]

    st.subheader("Uniform and Supply Readiness")
    st.write(
        "Review ready-to-issue uniforms, repair inventory, damaged items, "
        "and records that have fallen below their reorder point."
    )

    uniform_metric_one, uniform_metric_two, uniform_metric_three = st.columns(3)

    uniform_metric_one.metric(
        "Inventory Lines",
        len(uniforms_df),
    )
    uniform_metric_two.metric(
        "Shortage Lines",
        len(shortage_df),
    )
    uniform_metric_three.metric(
        "Ready-to-Issue Uniforms",
        int(uniforms_df["ready_quantity"].sum()),
    )

    if not shortage_df.empty:
        shortage_chart_data = shortage_df.copy()
        shortage_chart_data["uniform_item"] = (
            shortage_chart_data["department_name"]
            + " — "
            + shortage_chart_data["garment_type"]
            + " ("
            + shortage_chart_data["size_label"]
            + ")"
        )

        shortage_chart = px.bar(
            shortage_chart_data.sort_values(
                by="shortage_amount",
                ascending=True,
            ),
            x="shortage_amount",
            y="uniform_item",
            color="department_name",
            orientation="h",
            title="Uniform Inventory Shortage by Department and Size",
            labels={
                "shortage_amount": "Units Needed to Reach Reorder Point",
                "uniform_item": "Uniform Inventory Line",
                "department_name": "Department",
            },
        )

        st.plotly_chart(
            shortage_chart,
            width="stretch",
        )

        st.markdown("### Inventory Below Reorder Point")

        st.dataframe(
            shortage_df[
                [
                    "department_name",
                    "garment_type",
                    "size_label",
                    "ready_quantity",
                    "reorder_point",
                    "shortage_amount",
                    "repair_quantity",
                    "damaged_quantity",
                ]
            ],
            width="stretch",
            hide_index=True,
        )
    else:
        st.success("All fictional uniform inventory lines meet reorder targets.")

    with st.expander("View Complete Uniform Inventory"):
        st.dataframe(
            uniforms_df,
            width="stretch",
            hide_index=True,
        )

    st.download_button(
        label="Download Uniform Readiness Report",
        data=dataframe_to_csv_bytes(uniforms_df),
        file_name="uniform_readiness_report.csv",
        mime="text/csv",
        width="stretch",
    )
    
# Issues, Audit Trail, and application launcher
    
def render_operational_issues(data: dict[str, Any]) -> None:
    """
    Display fictional operational issues and provide local issue-management actions.
    """
    open_issues_df = data["open_issues_df"]

    st.subheader("Operational Issues")
    st.write(
        "Track fictional asset, uniform, readiness, maintenance, and lifecycle "
        "issues that require operational follow-up."
    )

    issue_metric_one, issue_metric_two, issue_metric_three = st.columns(3)

    issue_metric_one.metric(
        "Open Issues",
        len(open_issues_df),
    )
    issue_metric_two.metric(
        "High Priority",
        int((open_issues_df["priority"] == "High").sum()),
    )
    issue_metric_three.metric(
        "In Progress",
        int((open_issues_df["status"] == "In Progress").sum()),
    )

    st.dataframe(
        open_issues_df[
            [
                "issue_id",
                "department_name",
                "issue_title",
                "issue_type",
                "priority",
                "status",
                "opened_at",
                "owner_name",
                "details",
            ]
        ],
        width="stretch",
        hide_index=True,
    )

    st.download_button(
        label="Download Open Operational Issues",
        data=dataframe_to_csv_bytes(open_issues_df),
        file_name="open_operational_issues.csv",
        mime="text/csv",
    )

    st.divider()
    create_tab, update_tab = st.tabs(
        ["Create Fictional Issue", "Update Issue Status"]
    )

    with create_tab:
        departments = get_departments()

        department_options = {
            department["department_name"]: department
            for department in departments
        }

        with st.form("create_issue_form", border=True):
            selected_department_name = st.selectbox(
                "Department",
                options=list(department_options.keys()),
            )

            issue_title = st.text_input(
                "Issue title",
                placeholder=(
                    "Example: Guest Services tablet charger replacement needed"
                ),
            )

            issue_type = st.selectbox(
                "Issue type",
                options=[
                    "Asset Readiness",
                    "Equipment Availability",
                    "Equipment Maintenance",
                    "Inventory Shortage",
                    "Lifecycle Planning",
                    "Uniform Repair",
                    "Other",
                ],
            )

            priority = st.selectbox(
                "Priority",
                options=["Low", "Medium", "High", "Critical"],
                index=1,
            )

            owner_name = st.text_input(
                "Issue owner",
                value="Operations Supervisor",
            )

            issue_details = st.text_area(
                "Issue details",
                placeholder=(
                    "Describe the fictional operational impact, next step, "
                    "or required follow-up."
                ),
            )

            submit_issue = st.form_submit_button(
                "Create Operational Issue",
                width="stretch",
            )

            if submit_issue:
                selected_department = department_options[
                    selected_department_name
                ]

                try:
                    result = create_operational_issue(
                        department_id=int(selected_department["department_id"]),
                        issue_title=issue_title,
                        issue_type=issue_type,
                        priority=priority,
                        owner_name=owner_name
                        or "Operations Supervisor",
                        details=issue_details,
                    )

                    refresh_dashboard_data(result["message"])

                except ValueError as error:
                    st.error(str(error))

    with update_tab:
        if open_issues_df.empty:
            st.success("No fictional open issues require updates.")
        else:
            issue_options = {
                f"{row['issue_id']} — {row['issue_title']}": row
                for _, row in open_issues_df.iterrows()
            }

            with st.form("update_issue_status_form", border=True):
                selected_issue_label = st.selectbox(
                    "Select issue",
                    options=list(issue_options.keys()),
                )

                selected_issue = issue_options[selected_issue_label]

                new_status = st.selectbox(
                    "New status",
                    options=["Open", "In Progress", "Resolved"],
                    index=[
                        "Open",
                        "In Progress",
                        "Resolved",
                    ].index(str(selected_issue["status"])),
                )

                updated_by = st.text_input(
                    "Updated by",
                    value="Operations Supervisor",
                )

                submit_status_update = st.form_submit_button(
                    "Update Issue Status",
                    width="stretch",
                )

                if submit_status_update:
                    try:
                        result = update_issue_status(
                            issue_id=str(selected_issue["issue_id"]),
                            new_status=new_status,
                            updated_by=updated_by.strip()
                            or "Operations Supervisor",
                        )

                        refresh_dashboard_data(result["message"])

                    except ValueError as error:
                        st.error(str(error))


def render_audit_trail(data: dict[str, Any]) -> None:
    """Display recent local fictional audit events."""
    audit_df = data["audit_df"]

    st.subheader("Audit Trail")
    st.write(
        "The audit trail records fictional check-out, check-in, inventory, "
        "and issue-management actions completed through the local platform."
    )

    if audit_df.empty:
        st.info("No fictional audit events are available yet.")
        return

    st.dataframe(
        audit_df,
        width="stretch",
        hide_index=True,
    )

    st.download_button(
        label="Download Audit Events",
        data=dataframe_to_csv_bytes(audit_df),
        file_name="hospitality_asset_audit_events.csv",
        mime="text/csv",
        width="stretch",
    )


def main() -> None:
    """Run the Hospitality Asset Readiness Platform."""
    render_page_header()

    if "action_message" in st.session_state:
        st.success(st.session_state.pop("action_message"))

    with st.sidebar:
        st.header("Platform Controls")

        st.caption(
            "Refresh the dashboard after reseeding fictional data or after "
            "changing the local database outside this application."
        )

        if st.button(
            "Refresh Dashboard Data",
            width="stretch",
        ):
            st.cache_data.clear()
            st.rerun()

        st.divider()

        st.caption(
            "Portfolio scope: local SQLite database, fictional data, "
            "rule-based readiness scoring, and auditable workflow actions."
        )

    try:
        dashboard_data = load_dashboard_data()
    except Exception as error:
        st.error(
            "The dashboard could not load the fictional hospitality "
            "operations data."
        )
        st.exception(error)
        return

    overview_tab, asset_tab, uniform_tab, issue_tab, audit_tab = st.tabs(
        [
            "Operations Overview",
            "Asset Inventory",
            "Uniform Readiness",
            "Operational Issues",
            "Audit Trail",
        ]
    )

    with overview_tab:
        render_operations_overview(dashboard_data)

    with asset_tab:
        render_asset_inventory(dashboard_data)

    with uniform_tab:
        render_uniform_readiness(dashboard_data)

    with issue_tab:
        render_operational_issues(dashboard_data)

    with audit_tab:
        render_audit_trail(dashboard_data)


if __name__ == "__main__":
    main()    