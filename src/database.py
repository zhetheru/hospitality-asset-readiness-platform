"""
database.py

SQLite database utilities for the Hospitality Asset Readiness Platform.

This module creates and manages the local database used by the project.
All records are fictional and intended only for portfolio demonstration.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any


# src/database.py sits one folder below the project root.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATABASE_PATH = PROJECT_ROOT / "database" / "hospitality_assets.db"


def get_connection() -> sqlite3.Connection:
    """
    Create a connection to the local SQLite database.

    The Row factory allows query results to be accessed by column name,
    which makes later dashboard and service code easier to read.
    """
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row

    # SQLite does not enforce foreign keys unless this setting is enabled
    # for each connection.
    connection.execute("PRAGMA foreign_keys = ON;")

    return connection


def initialize_database() -> None:
    """
    Create the application's database tables when they do not already exist.
    """
    with get_connection() as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS departments (
                department_id INTEGER PRIMARY KEY,
                department_name TEXT NOT NULL UNIQUE,
                staffing_target INTEGER NOT NULL CHECK (staffing_target >= 0)
            );

            CREATE TABLE IF NOT EXISTS employees (
                employee_id TEXT PRIMARY KEY,
                employee_name TEXT NOT NULL,
                department_id INTEGER NOT NULL,
                job_title TEXT NOT NULL,
                shift_name TEXT NOT NULL,
                active INTEGER NOT NULL DEFAULT 1 CHECK (active IN (0, 1)),
                FOREIGN KEY (department_id)
                    REFERENCES departments(department_id)
            );

            CREATE TABLE IF NOT EXISTS assets (
                asset_id TEXT PRIMARY KEY,
                asset_type TEXT NOT NULL,
                asset_name TEXT NOT NULL,
                assigned_department_id INTEGER NOT NULL,
                status TEXT NOT NULL CHECK (
                    status IN ('Available', 'Checked Out', 'Maintenance', 'Retired')
                ),
                condition_status TEXT NOT NULL CHECK (
                    condition_status IN ('Excellent', 'Good', 'Fair', 'Needs Repair')
                ),
                purchase_year INTEGER NOT NULL,
                last_inspection_date TEXT NOT NULL,
                notes TEXT,
                FOREIGN KEY (assigned_department_id)
                    REFERENCES departments(department_id)
            );

            CREATE TABLE IF NOT EXISTS asset_assignments (
                assignment_id INTEGER PRIMARY KEY AUTOINCREMENT,
                asset_id TEXT NOT NULL,
                employee_id TEXT NOT NULL,
                checked_out_at TEXT NOT NULL,
                due_back_at TEXT,
                checked_in_at TEXT,
                checked_out_by TEXT NOT NULL,
                notes TEXT,
                FOREIGN KEY (asset_id)
                    REFERENCES assets(asset_id),
                FOREIGN KEY (employee_id)
                    REFERENCES employees(employee_id)
            );

            CREATE TABLE IF NOT EXISTS uniform_inventory (
                inventory_id INTEGER PRIMARY KEY AUTOINCREMENT,
                department_id INTEGER NOT NULL,
                garment_type TEXT NOT NULL,
                size_label TEXT NOT NULL,
                ready_quantity INTEGER NOT NULL CHECK (ready_quantity >= 0),
                repair_quantity INTEGER NOT NULL CHECK (repair_quantity >= 0),
                damaged_quantity INTEGER NOT NULL CHECK (damaged_quantity >= 0),
                reorder_point INTEGER NOT NULL CHECK (reorder_point >= 0),
                last_updated TEXT NOT NULL,
                FOREIGN KEY (department_id)
                    REFERENCES departments(department_id)
            );

            CREATE TABLE IF NOT EXISTS operational_issues (
                issue_id TEXT PRIMARY KEY,
                department_id INTEGER NOT NULL,
                issue_title TEXT NOT NULL,
                issue_type TEXT NOT NULL,
                priority TEXT NOT NULL CHECK (
                    priority IN ('Low', 'Medium', 'High', 'Critical')
                ),
                status TEXT NOT NULL CHECK (
                    status IN ('Open', 'In Progress', 'Resolved')
                ),
                opened_at TEXT NOT NULL,
                owner_name TEXT NOT NULL,
                details TEXT,
                FOREIGN KEY (department_id)
                    REFERENCES departments(department_id)
            );

            CREATE TABLE IF NOT EXISTS audit_log (
                audit_id INTEGER PRIMARY KEY AUTOINCREMENT,
                entity_type TEXT NOT NULL,
                entity_id TEXT NOT NULL,
                action_type TEXT NOT NULL,
                actor_name TEXT NOT NULL,
                event_time TEXT NOT NULL,
                details TEXT
            );

            CREATE UNIQUE INDEX IF NOT EXISTS idx_active_asset_assignment
            ON asset_assignments(asset_id)
            WHERE checked_in_at IS NULL;
            """
        )


def reset_database() -> None:
    """
    Remove the existing local database and recreate its empty structure.

    This function is used by the seed script so the fictional demonstration
    data can be rebuilt consistently whenever needed.
    """
    if DATABASE_PATH.exists():
        DATABASE_PATH.unlink()

    initialize_database()


def fetch_all(
    query: str,
    parameters: tuple[Any, ...] = (),
) -> list[dict[str, Any]]:
    """
    Run a read query and return the results as normal dictionaries.
    """
    with get_connection() as connection:
        rows = connection.execute(query, parameters).fetchall()

    return [dict(row) for row in rows]


def execute_write(
    query: str,
    parameters: tuple[Any, ...] = (),
) -> int:
    """
    Run an insert, update, or delete query and return the affected row count.
    """
    with get_connection() as connection:
        cursor = connection.execute(query, parameters)
        connection.commit()

    return cursor.rowcount