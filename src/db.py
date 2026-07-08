"""
Maftia Quant — Database Connection Module

SQLite WAL connection management for maftia_quant.db.
Provides connection pooling and migration support.

Usage:
    from src.db import get_db, init_db
    
    db = get_db()
    rows = db.execute("SELECT * FROM unified_daily_analytics").fetchall()
"""

import sqlite3
import re
from pathlib import Path
from typing import Optional, Any
from contextlib import contextmanager

# Database path
DB_DIR = Path(__file__).parent.parent / "data"
DB_PATH = DB_DIR / "maftia_quant.db"
MIGRATIONS_DIR = Path(__file__).parent.parent / "migrations"

# Allowlisted table names to prevent SQL injection
ALLOWED_TABLES: frozenset[str] = frozenset({
    "master_ohlcv",
    "onchain_metrics",
    "unified_daily_analytics",
    "unified_component_signals",
    "metric_config",
    "wfo_folds",
    "indicator_scores",
})

# Regex pattern for valid column names (alphanumeric + underscore)
COLUMN_PATTERN = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*$")


def ensure_db_dir() -> None:
    """Create data directory if it doesn't exist."""
    DB_DIR.mkdir(parents=True, exist_ok=True)


def get_db(db_path: Optional[Path] = None) -> sqlite3.Connection:
    """
    Get a SQLite connection with WAL mode enabled.
    
    Args:
        db_path: Optional custom database path
        
    Returns:
        sqlite3.Connection with row factory enabled
    """
    path = db_path or DB_PATH
    ensure_db_dir()
    
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    
    # Enable WAL mode for concurrent read/write
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA busy_timeout=5000")
    
    return conn


@contextmanager
def db_transaction(db_path: Optional[Path] = None):
    """
    Context manager for database transactions.
    
    Usage:
        with db_transaction() as conn:
            conn.execute("INSERT INTO ...")
            # Auto-commits on success, rolls back on exception
    """
    conn = get_db(db_path)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def validate_table_name(table: str) -> str:
    """
    Validate table name against allowlist.
    
    Args:
        table: Table name to validate
        
    Returns:
        Validated table name
        
    Raises:
        ValueError: If table name is not in allowlist
    """
    if table not in ALLOWED_TABLES:
        raise ValueError(f"Invalid table name: {table}")
    return table


def validate_column_name(column: str) -> str:
    """
    Validate column name using regex pattern.
    
    Args:
        column: Column name to validate
        
    Returns:
        Validated column name
        
    Raises:
        ValueError: If column name contains invalid characters
    """
    if not COLUMN_PATTERN.match(column):
        raise ValueError(f"Invalid column name: {column}")
    return column


def build_insert_query(table: str, columns: list[str]) -> str:
    """
    Build a parameterized INSERT query with validated identifiers.
    
    Args:
        table: Pre-validated table name
        columns: Pre-validated column names
        
    Returns:
        SQL INSERT query string
    """
    cols = ", ".join(columns)
    placeholders = ", ".join(["?"] * len(columns))
    return f"INSERT OR REPLACE INTO {table} ({cols}) VALUES ({placeholders})"


def init_db(db_path: Optional[Path] = None) -> None:
    """
    Initialize database with schema from migrations.
    
    Args:
        db_path: Optional custom database path
    """
    conn = get_db(db_path)
    
    # Read and execute migration SQL
    migration_file = MIGRATIONS_DIR / "001_create_schema.sql"
    if migration_file.exists():
        try:
            with open(migration_file, "r") as f:
                sql = f.read()
                conn.executescript(sql)
            print(f"✓ Database initialized at {db_path or DB_PATH}")
        except FileNotFoundError:
            print(f"✗ Migration file not found: {migration_file}")
        except sqlite3.Error as e:
            print(f"✗ Database initialization error: {e}")
    else:
        print(f"✗ Migration file not found: {migration_file}")
    
    conn.close()


def execute_query(
    query: str,
    params: Optional[tuple] = None,
    db_path: Optional[Path] = None
) -> list[sqlite3.Row]:
    """
    Execute a SELECT query and return results.
    
    Args:
        query: SQL SELECT query (must use parameterized queries for values)
        params: Optional query parameters
        db_path: Optional custom database path
        
    Returns:
        List of Row objects
    """
    conn = get_db(db_path)
    try:
        if params:
            cursor = conn.execute(query, params)
        else:
            cursor = conn.execute(query)
        return cursor.fetchall()
    finally:
        conn.close()


def execute_insert(
    table: str,
    data: dict[str, Any],
    db_path: Optional[Path] = None
) -> None:
    """
    Insert a row into a table.
    
    Args:
        table: Table name (must be in allowlist)
        data: Dictionary of column -> value
        db_path: Optional custom database path
    """
    # Validate identifiers against allowlist and regex pattern
    validated_table: str = validate_table_name(table)
    validated_columns: list[str] = [validate_column_name(col) for col in data.keys()]
    
    # Build query with validated identifiers (safe: identifiers are pre-validated)
    query: str = build_insert_query(validated_table, validated_columns)
    
    # Execute with parameterized values (safe: values use ? placeholders)
    with db_transaction(db_path) as conn:
        conn.execute(query, tuple(data.values()))


def execute_many_insert(
    table: str,
    rows: list[dict[str, Any]],
    db_path: Optional[Path] = None
) -> None:
    """
    Insert multiple rows into a table.
    
    Args:
        table: Table name (must be in allowlist)
        rows: List of dictionaries (column -> value)
        db_path: Optional custom database path
    """
    if not rows:
        return
    
    # Validate identifiers against allowlist and regex pattern
    validated_table: str = validate_table_name(table)
    validated_columns: list[str] = [validate_column_name(col) for col in rows[0].keys()]
    
    # Build query with validated identifiers (safe: identifiers are pre-validated)
    query: str = build_insert_query(validated_table, validated_columns)
    
    # Execute with parameterized values (safe: values use ? placeholders)
    with db_transaction(db_path) as conn:
        conn.executemany(query, [tuple(row.values()) for row in rows])


if __name__ == "__main__":
    # Initialize database when run directly
    init_db()
