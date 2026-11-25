"""Local SQLite persistence and transactional baseline loading."""
import argparse
import json
import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SEED = ROOT / "data" / "seed"
SCHEMA = Path(__file__).with_name("schema.sql")
SEED_VERSIONS = {
    1: ("foundation", "assurance", "resilience"),
    2: ("risk_rationales",),
    3: ("governance_details",),
}
ASSESSMENT_COLUMNS = {
    "controls": {
        "assessment_basis": "TEXT", "assessed_on": "TEXT", "assessor": "TEXT",
        "assessment_evidence_id": "TEXT REFERENCES evidence(id)",
    },
    "compliance_requirements": {
        "clause_ref": "TEXT", "reference_source": "TEXT", "assessment_evidence_id": "TEXT REFERENCES evidence(id)",
    },
    "maturity_scores": {"assessor": "TEXT", "assessed_on": "TEXT"},
    "ai_evaluations": {"reviewer": "TEXT", "review_notes": "TEXT"},
}


def default_path():
    return Path(os.environ.get("PASS_DB_PATH") or ROOT / "data" / "pass.sqlite3")


@contextmanager
def connect(path=None):
    path = Path(path) if path is not None else default_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path, timeout=10)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    try:
        with connection:
            yield connection
    finally:
        connection.close()


def initialize(path=None):
    with connect(path) as connection:
        connection.executescript(SCHEMA.read_text(encoding="utf-8"))
        connection.execute("BEGIN IMMEDIATE")
        for table, columns in ASSESSMENT_COLUMNS.items():
            existing = {row["name"] for row in connection.execute(f"PRAGMA table_info({table})")}
            for column, definition in columns.items():
                if column not in existing:
                    connection.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")
        connection.execute("PRAGMA defer_foreign_keys = ON")
        applied = {row["version"] for row in connection.execute("SELECT version FROM seed_versions")}
        for version, files in SEED_VERSIONS.items():
            if version in applied:
                continue
            for filename in files:
                tables = json.loads((SEED / f"{filename}.json").read_text(encoding="utf-8"))
                for table, records in tables.items():
                    for record in records:
                        insert(connection, table, record)
            connection.execute("INSERT INTO seed_versions VALUES (?)", (version,))


def query(sql, parameters=(), path=None):
    with connect(path) as connection:
        return [dict(row) for row in connection.execute(sql, parameters)]


def recovery_services():
    return query("""
        SELECT s.*, t.id AS test_id, t.tested_on, t.restore_result, t.actual_rto_minutes, t.actual_rpo_minutes,
               t.reviewer, t.evidence_id
        FROM bcdr_services s LEFT JOIN recovery_tests t ON t.id = (
            SELECT id FROM recovery_tests WHERE asset_id = s.asset_id
            ORDER BY tested_on DESC, rowid DESC LIMIT 1
        )
        ORDER BY s.priority IS NULL, s.priority, s.asset_id
    """)


def insert(connection, table, values):
    # Table and column identifiers come from the local schema, seed or form definitions.
    placeholders = ", ".join("?" for _ in values)
    return connection.execute(
        f"INSERT INTO {table} ({', '.join(values)}) VALUES ({placeholders})", tuple(values.values())
    )


def save(table, values, *, key="id", existing=None, links=(), path=None):
    """Write a record and replace its selected relationships in one transaction."""
    with connect(path) as connection:
        if existing is None:
            cursor = insert(connection, table, values)
            identifier = values.get(key, cursor.lastrowid)
        else:
            identifier = existing
            assignments = ", ".join(f"{column} = ?" for column in values)
            result = connection.execute(
                f"UPDATE {table} SET {assignments} WHERE {key} = ?", (*values.values(), existing)
            )
            if result.rowcount != 1:
                raise ValueError("This record is no longer available.")
        for link_table, parent_column, other_column, selections in links:
            connection.execute(f"DELETE FROM {link_table} WHERE {parent_column} = ?", (identifier,))
            for selected in selections:
                insert(connection, link_table, {parent_column: identifier, other_column: selected})
        return identifier


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Initialize the PASS SQLite database.")
    parser.add_argument("--path", type=Path, default=default_path())
    args = parser.parse_args()
    initialize(args.path)
    print(args.path.resolve())
