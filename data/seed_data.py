"""
seed_data.py

Creates a fictional hospitality operations dataset for the
Hospitality Asset Readiness Platform.

The data is intentionally fictional. It does not represent Hilton,
another hotel company, real employees, real inventory, or real operations.
"""

from __future__ import annotations

import sys
from pathlib import Path


# Allow this script to be run directly from the project root:
# .\.venv\Scripts\python.exe data\seed_data.py
PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.database import get_connection, reset_database


def seed_database() -> None:
    """
    Reset the local SQLite database and load fictional demonstration records.
    """
    reset_database()

    departments = [
        (1, "Front Office", 42),
        (2, "Housekeeping", 96),
        (3, "Food & Beverage", 70),
        (4, "Engineering", 18),
        (5, "Security", 14),
        (6, "Guest Services", 20),
    ]

    employees = [
        ("EMP-001", "Maya Carter", 1, "Guest Services Agent", "Morning", 1),
        ("EMP-002", "Jordan Rivera", 1, "Front Desk Supervisor", "Evening", 1),
        ("EMP-003", "Nia Brooks", 2, "Room Attendant", "Morning", 1),
        ("EMP-004", "Samuel Davis", 2, "Housekeeping Floor Supervisor", "Morning", 1),
        ("EMP-005", "Alex Kim", 3, "Banquet Captain", "Evening", 1),
        ("EMP-006", "Priya Shah", 4, "Maintenance Technician", "Day", 1),
        ("EMP-007", "Omar Wilson", 5, "Security Officer", "Night", 1),
        ("EMP-008", "Chloe Martin", 6, "Concierge", "Day", 1),
        ("EMP-009", "Taylor Nguyen", 3, "Restaurant Server", "Evening", 1),
        ("EMP-010", "Morgan Ellis", 4, "Engineering Supervisor", "Day", 1),
        ("EMP-011", "Avery Johnson", 5, "Security Supervisor", "Evening", 1),
        ("EMP-012", "Casey Brown", 6, "Bell Services Attendant", "Day", 1),
    ]

    assets = [
        (
            "TAB-001",
            "Device",
            "Front Desk Tablet 01",
            1,
            "Available",
            "Excellent",
            2025,
            "2026-06-20",
            "Ready for guest arrival support.",
        ),
        (
            "TAB-002",
            "Device",
            "Front Desk Tablet 02",
            1,
            "Checked Out",
            "Good",
            2025,
            "2026-06-20",
            "Assigned to the morning guest services shift.",
        ),
        (
            "TAB-003",
            "Device",
            "Front Desk Tablet 03",
            1,
            "Available",
            "Good",
            2024,
            "2026-06-18",
            "Backup device for high-volume arrival periods.",
        ),
        (
            "RAD-001",
            "Device",
            "Security Radio 01",
            5,
            "Available",
            "Good",
            2024,
            "2026-06-22",
            "Charged and ready for assignment.",
        ),
        (
            "RAD-002",
            "Device",
            "Security Radio 02",
            5,
            "Available",
            "Fair",
            2023,
            "2026-06-22",
            "Battery performance should be monitored.",
        ),
        (
            "RAD-003",
            "Device",
            "Security Radio 03",
            5,
            "Checked Out",
            "Good",
            2025,
            "2026-06-22",
            "Assigned to the night security shift.",
        ),
        (
            "SCN-001",
            "Device",
            "Housekeeping Linen Scanner 01",
            2,
            "Checked Out",
            "Good",
            2025,
            "2026-06-19",
            "Assigned to linen room operations.",
        ),
        (
            "SCN-002",
            "Device",
            "Housekeeping Linen Scanner 02",
            2,
            "Available",
            "Excellent",
            2025,
            "2026-06-19",
            "Available as a backup scanner.",
        ),
        (
            "CART-001",
            "Equipment",
            "Housekeeping Supply Cart 01",
            2,
            "Available",
            "Good",
            2024,
            "2026-06-21",
            "Restocked for the next morning shift.",
        ),
        (
            "CART-002",
            "Equipment",
            "Housekeeping Supply Cart 02",
            2,
            "Maintenance",
            "Needs Repair",
            2022,
            "2026-06-21",
            "Brake repair is required before use.",
        ),
        (
            "KEY-001",
            "Device",
            "Mobile Key Encoder 01",
            1,
            "Available",
            "Excellent",
            2025,
            "2026-06-20",
            "Located at the Front Office workstation.",
        ),
        (
            "KEY-002",
            "Device",
            "Mobile Key Encoder 02",
            1,
            "Available",
            "Good",
            2024,
            "2026-06-20",
            "Backup unit for peak arrival periods.",
        ),
        (
            "LAP-001",
            "Device",
            "Engineering Laptop 01",
            4,
            "Available",
            "Good",
            2024,
            "2026-06-17",
            "Used for maintenance planning and vendor communication.",
        ),
        (
            "LAP-002",
            "Device",
            "Engineering Laptop 02",
            4,
            "Available",
            "Fair",
            2022,
            "2026-06-17",
            "Scheduled for replacement review next quarter.",
        ),
        (
            "PRN-001",
            "Device",
            "Banquet Event Printer 01",
            3,
            "Available",
            "Good",
            2024,
            "2026-06-21",
            "Used for event orders and banquet updates.",
        ),
        (
            "VAC-001",
            "Equipment",
            "Housekeeping Vacuum 01",
            2,
            "Available",
            "Good",
            2024,
            "2026-06-20",
            "Assigned to guest room corridor coverage.",
        ),
        (
            "VAC-002",
            "Equipment",
            "Housekeeping Vacuum 02",
            2,
            "Available",
            "Fair",
            2022,
            "2026-06-20",
            "Filter replacement should be planned.",
        ),
        (
            "LUG-001",
            "Equipment",
            "Bell Services Luggage Cart 01",
            6,
            "Available",
            "Good",
            2023,
            "2026-06-18",
            "Available in the main entrance storage area.",
        ),
    ]

    asset_assignments = [
        (
            "TAB-002",
            "EMP-001",
            "2026-06-30 07:00:00",
            "2026-06-30 15:00:00",
            None,
            "Jordan Rivera",
            "Used for guest arrival support and mobile check-in assistance.",
        ),
        (
            "RAD-003",
            "EMP-007",
            "2026-06-30 22:00:00",
            "2026-07-01 06:00:00",
            None,
            "Avery Johnson",
            "Assigned for night shift patrol communication.",
        ),
        (
            "SCN-001",
            "EMP-003",
            "2026-06-30 07:30:00",
            "2026-06-30 16:00:00",
            None,
            "Samuel Davis",
            "Assigned for linen processing and room turnover support.",
        ),
        (
            "TAB-001",
            "EMP-002",
            "2026-06-29 15:00:00",
            "2026-06-29 23:00:00",
            "2026-06-29 22:45:00",
            "Jordan Rivera",
            "Completed evening shift assignment.",
        ),
    ]

    uniform_inventory = [
        (2, "Housekeeping Polo", "Medium", 12, 5, 2, 18, "2026-06-30"),
        (2, "Housekeeping Polo", "Large", 22, 3, 1, 18, "2026-06-30"),
        (2, "Housekeeping Polo", "Extra Large", 10, 2, 1, 14, "2026-06-30"),
        (2, "Housekeeping Pants", "Medium", 18, 4, 1, 16, "2026-06-30"),
        (2, "Housekeeping Pants", "Large", 20, 3, 1, 16, "2026-06-30"),
        (1, "Front Office Blazer", "Small", 8, 1, 0, 6, "2026-06-30"),
        (1, "Front Office Blazer", "Medium", 6, 2, 1, 8, "2026-06-30"),
        (1, "Front Office Blazer", "Large", 7, 1, 0, 7, "2026-06-30"),
        (1, "Front Office Shirt", "Medium", 14, 1, 0, 12, "2026-06-30"),
        (1, "Front Office Shirt", "Large", 11, 2, 0, 12, "2026-06-30"),
        (3, "Server Shirt", "Medium", 16, 3, 1, 14, "2026-06-30"),
        (3, "Server Shirt", "Large", 13, 2, 1, 14, "2026-06-30"),
        (5, "Security Polo", "Large", 5, 2, 1, 8, "2026-06-30"),
        (6, "Concierge Blazer", "Medium", 4, 1, 0, 6, "2026-06-30"),
        (4, "Engineering Work Jacket", "Large", 9, 1, 1, 7, "2026-06-30"),
    ]

    operational_issues = [
        (
            "ISS-001",
            2,
            "Housekeeping medium polo inventory below reorder point",
            "Inventory Shortage",
            "High",
            "Open",
            "2026-06-30 08:00:00",
            "Samuel Davis",
            "Ready-to-issue quantity is below the defined reorder point.",
        ),
        (
            "ISS-002",
            1,
            "Front Office tablet charging cable replacement",
            "Equipment Availability",
            "Medium",
            "In Progress",
            "2026-06-30 09:15:00",
            "Jordan Rivera",
            "Tablet availability is currently sufficient, but the cable should be replaced.",
        ),
        (
            "ISS-003",
            2,
            "Housekeeping Supply Cart 02 brake repair",
            "Equipment Maintenance",
            "High",
            "Open",
            "2026-06-30 07:45:00",
            "Priya Shah",
            "Cart is unavailable until brake repair is completed.",
        ),
        (
            "ISS-004",
            5,
            "Security radio availability review",
            "Asset Readiness",
            "High",
            "Open",
            "2026-06-30 18:30:00",
            "Avery Johnson",
            "Radio inventory should be reviewed before the next overnight shift.",
        ),
        (
            "ISS-005",
            6,
            "Concierge blazer repair completed",
            "Uniform Repair",
            "Low",
            "Resolved",
            "2026-06-28 10:00:00",
            "Chloe Martin",
            "One blazer was repaired and returned to inventory.",
        ),
        (
            "ISS-006",
            4,
            "Engineering Laptop 02 replacement review",
            "Lifecycle Planning",
            "Medium",
            "In Progress",
            "2026-06-29 13:00:00",
            "Morgan Ellis",
            "Fair-condition device should be evaluated during the next technology refresh cycle.",
        ),
    ]

    audit_events = [
        (
            "Asset",
            "TAB-002",
            "Checked Out",
            "Jordan Rivera",
            "2026-06-30 07:00:00",
            "Assigned Front Desk Tablet 02 to Maya Carter.",
        ),
        (
            "Asset",
            "RAD-003",
            "Checked Out",
            "Avery Johnson",
            "2026-06-30 22:00:00",
            "Assigned Security Radio 03 to Omar Wilson.",
        ),
        (
            "Asset",
            "CART-002",
            "Maintenance Flagged",
            "Priya Shah",
            "2026-06-30 07:45:00",
            "Marked cart unavailable because brake repair is required.",
        ),
        (
            "Uniform Inventory",
            "HK-POLO-M",
            "Reorder Alert",
            "Samuel Davis",
            "2026-06-30 08:00:00",
            "Housekeeping medium polo inventory fell below the reorder point.",
        ),
        (
            "Issue",
            "ISS-003",
            "Issue Created",
            "Priya Shah",
            "2026-06-30 07:45:00",
            "Created maintenance issue for Housekeeping Supply Cart 02.",
        ),
    ]

    with get_connection() as connection:
        connection.executemany(
            """
            INSERT INTO departments (
                department_id,
                department_name,
                staffing_target
            )
            VALUES (?, ?, ?)
            """,
            departments,
        )

        connection.executemany(
            """
            INSERT INTO employees (
                employee_id,
                employee_name,
                department_id,
                job_title,
                shift_name,
                active
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            employees,
        )

        connection.executemany(
            """
            INSERT INTO assets (
                asset_id,
                asset_type,
                asset_name,
                assigned_department_id,
                status,
                condition_status,
                purchase_year,
                last_inspection_date,
                notes
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            assets,
        )

        connection.executemany(
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
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            asset_assignments,
        )

        connection.executemany(
            """
            INSERT INTO uniform_inventory (
                department_id,
                garment_type,
                size_label,
                ready_quantity,
                repair_quantity,
                damaged_quantity,
                reorder_point,
                last_updated
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            uniform_inventory,
        )

        connection.executemany(
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
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            operational_issues,
        )

        connection.executemany(
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
            audit_events,
        )

        connection.commit()


if __name__ == "__main__":
    seed_database()
    print("Fictional hospitality asset database created successfully.")
    print(f"Database location: {PROJECT_ROOT / 'database' / 'hospitality_assets.db'}")