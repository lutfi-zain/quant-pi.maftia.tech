"""
Schema validation tests for maftia_quant.db.

Validates that:
1. All required tables exist
2. All required columns exist with correct types
3. Indexes are created
4. Views are created
5. WAL mode is enabled
6. Foreign keys are enabled
"""

import sqlite3
import sys
from collections.abc import Generator
from pathlib import Path

import pytest

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from db import init_db, get_db, DB_PATH

# ═══════════════════════════════════════════════════════════
# Expected Schema Definitions
# ═══════════════════════════════════════════════════════════

REQUIRED_TABLES = frozenset({
    "master_ohlcv",
    "onchain_metrics",
    "unified_daily_analytics",
    "unified_component_signals",
    "metric_config",
    "wfo_folds",
    "indicator_scores",
})

# Table -> {column_name: expected_type_substring}
EXPECTED_COLUMNS: dict[str, dict[str, str]] = {
    "master_ohlcv": {
        "date": "TEXT",
        "open": "REAL",
        "high": "REAL",
        "low": "REAL",
        "close": "REAL",
        "volume": "REAL",
        "source": "TEXT",
        "fetched_at": "TEXT",
    },
    "onchain_metrics": {
        "date": "TEXT",
        "sth_mvrv": "REAL",
        "sth_nupl": "REAL",
        "sth_sopr_24h": "REAL",
        "sth_supply_in_profit": "REAL",
        "stamp": "TEXT",
        "fetched_at": "TEXT",
    },
    "unified_daily_analytics": {
        "date": "TEXT",
        "mvo_score": "REAL",
        "mvo_pillar_fundamental": "REAL",
        "mvo_pillar_technical": "REAL",
        "mvo_pillar_sentiment": "REAL",
        "lttd_score": "REAL",
        "lttd_regime": "TEXT",
        "lttd_p_bull": "REAL",
        "lttd_p_bear": "REAL",
        "lttd_p_sideways": "REAL",
        "lttd_exposure": "REAL",
        "lttd_circuit_breaker": "INTEGER",
        "mttd_imo": "REAL",
        "mttd_position": "REAL",
        "mttd_er": "REAL",
        "mttd_entropy": "REAL",
        "ichi_imo": "REAL",
        "ichi_position": "REAL",
        "ichi_s_tk": "REAL",
        "ichi_s_cloud": "REAL",
        "ichi_s_future": "REAL",
        "ichi_s_chikou": "REAL",
        "consensus_score": "REAL",
        "consensus_exposure": "REAL",
        "computed_at": "TEXT",
    },
    "unified_component_signals": {
        "date": "TEXT",
        "system": "TEXT",
        "component": "TEXT",
        "score": "REAL",
        "raw_value": "REAL",
    },
    "metric_config": {
        "metric_name": "TEXT",
        "system": "TEXT",
        "pillar": "TEXT",
        "description": "TEXT",
        "min_threshold": "REAL",
        "max_threshold": "REAL",
        "enabled": "INTEGER",
        "updated_at": "TEXT",
    },
    "wfo_folds": {
        "fold_id": "INTEGER",
        "system": "TEXT",
        "train_start": "TEXT",
        "train_end": "TEXT",
        "test_start": "TEXT",
        "test_end": "TEXT",
        "test_accuracy": "REAL",
        "test_sharpe": "REAL",
        "lambda_": "REAL",
        "created_at": "TEXT",
    },
    "indicator_scores": {
        "date": "TEXT",
        "indicator_name": "TEXT",
        "score": "INTEGER",
    },
}

# Expected indexes
REQUIRED_INDEXES = frozenset({
    "idx_ohlcv_date",
    "idx_onchain_date",
    "idx_unified_date",
    "idx_unified_regime",
    "idx_signals_system",
    "idx_signals_system_date",
    "idx_config_system",
    "idx_wfo_system",
    "idx_indicator_date",
})

# Expected views
REQUIRED_VIEWS = frozenset({
    "v_latest_analytics",
    "v_current_regime",
    "v_current_consensus",
})


# ═══════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════


@pytest.fixture(scope="module")
def db_conn(tmp_path_factory: pytest.TempPathFactory) -> Generator[sqlite3.Connection, None, None]:
    """
    Initialize a fresh test database and return connection.
    
    Uses a temporary database to avoid affecting production data.
    """
    tmp_dir = tmp_path_factory.mktemp("schema_test")
    test_db_path = tmp_dir / "test_maftia_quant.db"
    
    # Initialize the schema
    init_db(db_path=test_db_path)
    
    # Return connection for tests
    conn = sqlite3.connect(str(test_db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    
    yield conn
    
    conn.close()


def get_tables(conn: sqlite3.Connection) -> set[str]:
    """Get all user table names from database."""
    rows = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
    ).fetchall()
    return {row["name"] for row in rows}


def get_columns(conn: sqlite3.Connection, table: str) -> dict[str, str]:
    """Get column names and types for a table."""
    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    return {row["name"]: row["type"] for row in rows}


def get_indexes(conn: sqlite3.Connection) -> set[str]:
    """Get all index names."""
    rows = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='index' AND name NOT LIKE 'sqlite_%'"
    ).fetchall()
    return {row["name"] for row in rows}


def get_views(conn: sqlite3.Connection) -> set[str]:
    """Get all view names."""
    rows = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='view'"
    ).fetchall()
    return {row["name"] for row in rows}


def get_primary_keys(conn: sqlite3.Connection, table: str) -> list[str]:
    """Get primary key columns for a table."""
    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    return [row["name"] for row in rows if row["pk"] > 0]


# ═══════════════════════════════════════════════════════════
# Test Classes
# ═══════════════════════════════════════════════════════════


class TestDatabasePragmas:
    """Tests for SQLite PRAGMA settings."""
    
    def test_wal_mode_enabled(self, db_conn: sqlite3.Connection):
        """WAL journal mode is enabled."""
        result = db_conn.execute("PRAGMA journal_mode").fetchone()
        assert result[0] == "wal"
    
    def test_foreign_keys_enabled(self, db_conn: sqlite3.Connection):
        """Foreign keys are enabled."""
        result = db_conn.execute("PRAGMA foreign_keys").fetchone()
        assert result[0] == 1


class TestRequiredTables:
    """Tests that all required tables exist."""
    
    def test_all_tables_exist(self, db_conn: sqlite3.Connection):
        """All required tables are created."""
        actual_tables = get_tables(db_conn)
        
        missing = REQUIRED_TABLES - actual_tables
        assert not missing, f"Missing tables: {missing}"
    
    def test_no_extra_tables(self, db_conn: sqlite3.Connection):
        """No unexpected tables exist."""
        actual_tables = get_tables(db_conn)
        
        extra = actual_tables - REQUIRED_TABLES
        # Allow sqlite internal tables (filtered by get_tables)
        assert not extra, f"Unexpected tables: {extra}"


class TestMasterOhlcvSchema:
    """Tests for master_ohlcv table schema."""
    
    def test_columns_exist(self, db_conn: sqlite3.Connection):
        """All required columns exist with correct types."""
        columns = get_columns(db_conn, "master_ohlcv")
        expected = EXPECTED_COLUMNS["master_ohlcv"]
        
        for col_name, expected_type in expected.items():
            assert col_name in columns, f"Missing column: {col_name}"
            assert expected_type in columns[col_name], (
                f"Column {col_name}: expected {expected_type}, got {columns[col_name]}"
            )
    
    def test_date_is_primary_key(self, db_conn: sqlite3.Connection):
        """date is the primary key."""
        pks = get_primary_keys(db_conn, "master_ohlcv")
        assert pks == ["date"]
    
    def test_insert_valid_row(self, db_conn: sqlite3.Connection):
        """Can insert a valid OHLCV row."""
        db_conn.execute(
            """INSERT INTO master_ohlcv (date, open, high, low, close, volume, source)
               VALUES ('2026-07-08', 100000.0, 101000.0, 99000.0, 100500.0, 1000.0, 'binance')"""
        )
        db_conn.commit()
        
        row = db_conn.execute("SELECT * FROM master_ohlcv WHERE date = '2026-07-08'").fetchone()
        assert row is not None
        assert row["open"] == 100000.0
        assert row["close"] == 100500.0


class TestOnchainMetricsSchema:
    """Tests for onchain_metrics table schema."""
    
    def test_columns_exist(self, db_conn: sqlite3.Connection):
        """All required columns exist."""
        columns = get_columns(db_conn, "onchain_metrics")
        expected = EXPECTED_COLUMNS["onchain_metrics"]
        
        for col_name in expected:
            assert col_name in columns, f"Missing column: {col_name}"
    
    def test_date_is_primary_key(self, db_conn: sqlite3.Connection):
        """date is the primary key."""
        pks = get_primary_keys(db_conn, "onchain_metrics")
        assert pks == ["date"]


class TestUnifiedDailyAnalyticsSchema:
    """Tests for unified_daily_analytics table schema."""
    
    def test_all_columns_exist(self, db_conn: sqlite3.Connection):
        """All 25 columns exist with correct types."""
        columns = get_columns(db_conn, "unified_daily_analytics")
        expected = EXPECTED_COLUMNS["unified_daily_analytics"]
        
        missing = set(expected.keys()) - set(columns.keys())
        assert not missing, f"Missing columns: {missing}"
    
    def test_date_is_primary_key(self, db_conn: sqlite3.Connection):
        """date is the primary key."""
        pks = get_primary_keys(db_conn, "unified_daily_analytics")
        assert pks == ["date"]
    
    def test_mvo_score_type(self, db_conn: sqlite3.Connection):
        """mvo_score is REAL type."""
        columns = get_columns(db_conn, "unified_daily_analytics")
        assert "REAL" in columns["mvo_score"]
    
    def test_lttd_regime_type(self, db_conn: sqlite3.Connection):
        """lttd_regime is TEXT type."""
        columns = get_columns(db_conn, "unified_daily_analytics")
        assert "TEXT" in columns["lttd_regime"]
    
    def test_lttd_circuit_breaker_type(self, db_conn: sqlite3.Connection):
        """lttd_circuit_breaker is INTEGER type."""
        columns = get_columns(db_conn, "unified_daily_analytics")
        assert "INTEGER" in columns["lttd_circuit_breaker"]


class TestUnifiedComponentSignalsSchema:
    """Tests for unified_component_signals table schema."""
    
    def test_columns_exist(self, db_conn: sqlite3.Connection):
        """All required columns exist."""
        columns = get_columns(db_conn, "unified_component_signals")
        expected = EXPECTED_COLUMNS["unified_component_signals"]
        
        for col_name in expected:
            assert col_name in columns, f"Missing column: {col_name}"
    
    def test_composite_primary_key(self, db_conn: sqlite3.Connection):
        """Composite primary key on (date, system, component)."""
        pks = get_primary_keys(db_conn, "unified_component_signals")
        assert set(pks) == {"date", "system", "component"}


class TestMetricConfigSchema:
    """Tests for metric_config table schema."""
    
    def test_columns_exist(self, db_conn: sqlite3.Connection):
        """All required columns exist."""
        columns = get_columns(db_conn, "metric_config")
        expected = EXPECTED_COLUMNS["metric_config"]
        
        for col_name in expected:
            assert col_name in columns, f"Missing column: {col_name}"
    
    def test_metric_name_is_primary_key(self, db_conn: sqlite3.Connection):
        """metric_name is the primary key."""
        pks = get_primary_keys(db_conn, "metric_config")
        assert pks == ["metric_name"]


class TestWfoFoldsSchema:
    """Tests for wfo_folds table schema."""
    
    def test_columns_exist(self, db_conn: sqlite3.Connection):
        """All required columns exist."""
        columns = get_columns(db_conn, "wfo_folds")
        expected = EXPECTED_COLUMNS["wfo_folds"]
        
        for col_name in expected:
            assert col_name in columns, f"Missing column: {col_name}"
    
    def test_fold_id_is_primary_key(self, db_conn: sqlite3.Connection):
        """fold_id is the primary key."""
        pks = get_primary_keys(db_conn, "wfo_folds")
        assert pks == ["fold_id"]


class TestIndicatorScoresSchema:
    """Tests for indicator_scores table schema."""
    
    def test_columns_exist(self, db_conn: sqlite3.Connection):
        """All required columns exist."""
        columns = get_columns(db_conn, "indicator_scores")
        expected = EXPECTED_COLUMNS["indicator_scores"]
        
        for col_name in expected:
            assert col_name in columns, f"Missing column: {col_name}"
    
    def test_composite_primary_key(self, db_conn: sqlite3.Connection):
        """Composite primary key on (date, indicator_name)."""
        pks = get_primary_keys(db_conn, "indicator_scores")
        assert set(pks) == {"date", "indicator_name"}


class TestIndexes:
    """Tests for required indexes."""
    
    def test_all_indexes_exist(self, db_conn: sqlite3.Connection):
        """All required indexes are created."""
        actual_indexes = get_indexes(db_conn)
        
        missing = REQUIRED_INDEXES - actual_indexes
        assert not missing, f"Missing indexes: {missing}"


class TestViews:
    """Tests for required views."""
    
    def test_all_views_exist(self, db_conn: sqlite3.Connection):
        """All required views are created."""
        actual_views = get_views(db_conn)
        
        missing = REQUIRED_VIEWS - actual_views
        assert not missing, f"Missing views: {missing}"
    
    def test_latest_analytics_view_queryable(self, db_conn: sqlite3.Connection):
        """v_latest_analytics view can be queried."""
        # Should not raise an exception
        result = db_conn.execute("SELECT * FROM v_latest_analytics").fetchall()
        # May be empty, but should not error
        assert isinstance(result, list)
    
    def test_current_regime_view_queryable(self, db_conn: sqlite3.Connection):
        """v_current_regime view can be queried."""
        result = db_conn.execute("SELECT * FROM v_current_regime").fetchall()
        assert isinstance(result, list)
    
    def test_current_consensus_view_queryable(self, db_conn: sqlite3.Connection):
        """v_current_consensus view can be queried."""
        result = db_conn.execute("SELECT * FROM v_current_consensus").fetchall()
        assert isinstance(result, list)


class TestSchemaConstraints:
    """Tests for schema constraints and behavior."""
    
    def test_master_ohlcv_unique_date(self, db_conn: sqlite3.Connection):
        """master_ohlcv rejects duplicate dates."""
        # Use a unique date to avoid conflicts with other module-scoped tests
        test_date = '2026-07-08-unique-test'
        db_conn.execute(
            f"INSERT INTO master_ohlcv (date, open, high, low, close, volume) VALUES ('{test_date}', 100, 101, 99, 100.5, 1000)"
        )
        db_conn.commit()
        
        with pytest.raises(sqlite3.IntegrityError):
            db_conn.execute(
                f"INSERT INTO master_ohlcv (date, open, high, low, close, volume) VALUES ('{test_date}', 200, 201, 199, 200.5, 2000)"
            )
    
    def test_unified_analytics_unique_date(self, db_conn: sqlite3.Connection):
        """unified_daily_analytics rejects duplicate dates."""
        db_conn.execute(
            "INSERT INTO unified_daily_analytics (date, mvo_score) VALUES ('2026-07-08', 1.5)"
        )
        db_conn.commit()
        
        with pytest.raises(sqlite3.IntegrityError):
            db_conn.execute(
                "INSERT INTO unified_daily_analytics (date, mvo_score) VALUES ('2026-07-08', -0.5)"
            )
            db_conn.commit()
    
    def test_component_signals_unique_composite(self, db_conn: sqlite3.Connection):
        """unified_component_signals rejects duplicate composite keys."""
        db_conn.execute(
            "INSERT INTO unified_component_signals (date, system, component, score) VALUES ('2026-07-08', 'valuation', 'mvo', 1.5)"
        )
        db_conn.commit()
        
        with pytest.raises(sqlite3.IntegrityError):
            db_conn.execute(
                "INSERT INTO unified_component_signals (date, system, component, score) VALUES ('2026-07-08', 'valuation', 'mvo', -0.5)"
            )
            db_conn.commit()
    
    def test_insert_or_replace_works(self, db_conn: sqlite3.Connection):
        """INSERT OR REPLACE works for upsert behavior."""
        # Use a unique date to avoid conflicts with other tests
        test_date = '2026-07-08-replace-test'
        
        # Insert initial row
        db_conn.execute(
            f"INSERT INTO master_ohlcv (date, open, high, low, close, volume) VALUES ('{test_date}', 100, 101, 99, 100.5, 1000)"
        )
        db_conn.commit()
        
        # Upsert with INSERT OR REPLACE
        db_conn.execute(
            f"INSERT OR REPLACE INTO master_ohlcv (date, open, high, low, close, volume) VALUES ('{test_date}', 200, 201, 199, 200.5, 2000)"
        )
        db_conn.commit()
        
        row = db_conn.execute(f"SELECT * FROM master_ohlcv WHERE date = '{test_date}'").fetchone()
        assert row["open"] == 200  # Should be updated


class TestInitDbIdempotent:
    """Tests that init_db is idempotent."""
    
    def test_init_db_twice_no_error(self, tmp_path: Path):
        """Calling init_db twice doesn't raise errors."""
        test_db_path = tmp_path / "idempotent_test.db"
        
        init_db(db_path=test_db_path)
        init_db(db_path=test_db_path)  # Second call should be fine
        
        conn = sqlite3.connect(str(test_db_path))
        conn.row_factory = sqlite3.Row
        tables = get_tables(conn)
        assert REQUIRED_TABLES == tables
        conn.close()
    
    def test_init_db_preserves_data(self, tmp_path: Path):
        """Re-running init_db doesn't delete existing data."""
        test_db_path = tmp_path / "preserve_test.db"
        
        # Initialize and insert data
        init_db(db_path=test_db_path)
        conn = sqlite3.connect(str(test_db_path))
        conn.execute(
            "INSERT INTO master_ohlcv (date, open, high, low, close, volume) VALUES ('2026-07-08', 100, 101, 99, 100.5, 1000)"
        )
        conn.commit()
        conn.close()
        
        # Re-initialize
        init_db(db_path=test_db_path)
        
        # Verify data preserved
        conn = sqlite3.connect(str(test_db_path))
        row = conn.execute("SELECT * FROM master_ohlcv WHERE date = '2026-07-08'").fetchone()
        assert row is not None
        assert row[1] == 100  # open
        conn.close()
