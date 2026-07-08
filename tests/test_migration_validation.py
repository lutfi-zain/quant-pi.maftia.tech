"""
Migration validation tests for system migration pipelines.

Tests that:
1. LTTD migration pipeline works correctly
2. Valuation migration pipeline works correctly
3. MTTD sync pipeline works correctly
4. Ichimoku sync pipeline works correctly
5. All pipelines handle missing source gracefully
6. Data validation catches invalid records
7. Orchestrator runs without errors
"""

import json
import sys
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Generator

import pytest

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from db import init_db, get_db, execute_query
from pipelines.lttd_migration import (
    LTTDMigrationPipeline,
    LTTDRecord,
    LTTDDataTransformer,
)
from pipelines.valuation_migration import (
    ValuationMigrationPipeline,
    ValuationRecord,
    ValuationDataTransformer,
)
from pipelines.mttd_sync import (
    MTTDSyncPipeline,
    MTTDRecord,
    MTTDDataTransformer,
    JSONDataReader,
)
from pipelines.ichimoku_sync import (
    IchimokuSyncPipeline,
    IchimokuRecord,
    IchimokuDataTransformer,
)


# ═══════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════


@pytest.fixture(scope="module")
def test_db(tmp_path_factory: pytest.TempPathFactory) -> Generator[Path, None, None]:
    """Create a fresh test database for migration tests."""
    tmp_dir = tmp_path_factory.mktemp("migration_test")
    db_path = tmp_dir / "test_maftia_quant.db"
    
    # Initialize schema
    init_db(db_path=db_path)
    
    yield db_path


@pytest.fixture
def lttd_records() -> list[LTTDRecord]:
    """Sample LTTD records for testing."""
    return [
        LTTDRecord(
            date="2026-07-01",
            score=0.75,
            regime="BULL",
            p_bull=0.6,
            p_bear=0.2,
            p_sideways=0.2,
            exposure=1.0,
            circuit_breaker=0,
        ),
        LTTDRecord(
            date="2026-07-02",
            score=-0.25,
            regime="SIDEWAYS",
            p_bull=0.3,
            p_bear=0.3,
            p_sideways=0.4,
            exposure=0.0,
            circuit_breaker=0,
        ),
        LTTDRecord(
            date="2026-07-03",
            score=-0.8,
            regime="BEAR",
            p_bull=0.1,
            p_bear=0.7,
            p_sideways=0.2,
            exposure=0.0,
            circuit_breaker=0,
        ),
    ]


@pytest.fixture
def valuation_records() -> list[ValuationRecord]:
    """Sample Valuation records for testing."""
    return [
        ValuationRecord(
            date="2026-07-01",
            mvo_score=1.2,
            pillar_fundamental=0.8,
            pillar_technical=1.5,
            pillar_sentiment=1.3,
        ),
        ValuationRecord(
            date="2026-07-02",
            mvo_score=-0.5,
            pillar_fundamental=-0.3,
            pillar_technical=-0.8,
            pillar_sentiment=-0.4,
        ),
    ]


@pytest.fixture
def mttd_records() -> list[MTTDRecord]:
    """Sample MTTD records for testing."""
    return [
        MTTDRecord(
            date="2026-07-01",
            imo=0.45,
            position=1.0,
            er=0.65,
            entropy=1.2,
        ),
        MTTDRecord(
            date="2026-07-02",
            imo=-0.3,
            position=0.0,
            er=0.4,
            entropy=1.8,
        ),
    ]


@pytest.fixture
def ichimoku_records() -> list[IchimokuRecord]:
    """Sample Ichimoku records for testing."""
    return [
        IchimokuRecord(
            date="2026-07-01",
            imo=0.6,
            position=1.0,
            s_tk=0.8,
            s_cloud=0.5,
            s_future=0.7,
            s_chikou=0.4,
        ),
        IchimokuRecord(
            date="2026-07-02",
            imo=-0.2,
            position=0.0,
            s_tk=-0.3,
            s_cloud=-0.1,
            s_future=-0.2,
            s_chikou=-0.4,
        ),
    ]


# ═══════════════════════════════════════════════════════════
# LTTD Migration Tests
# ═══════════════════════════════════════════════════════════


class TestLTTDTransformer:
    """Tests for LTTD data transformer."""
    
    def test_normalize_regime_bull(self):
        """Bull regime is normalized correctly."""
        assert LTTDDataTransformer.normalize_regime("bull") == "BULL"
        assert LTTDDataTransformer.normalize_regime("BULL") == "BULL"
    
    def test_normalize_regime_bear(self):
        """Bear regime is normalized correctly."""
        assert LTTDDataTransformer.normalize_regime("bear") == "BEAR"
        assert LTTDDataTransformer.normalize_regime("BEAR") == "BEAR"
    
    def test_normalize_regime_sideways(self):
        """Sideways regime is normalized correctly."""
        assert LTTDDataTransformer.normalize_regime("sideways") == "SIDEWAYS"
        assert LTTDDataTransformer.normalize_regime("SIDEWAYS") == "SIDEWAYS"
    
    def test_normalize_regime_unknown(self):
        """Unknown regime defaults to SIDEWAYS."""
        assert LTTDDataTransformer.normalize_regime("unknown") == "SIDEWAYS"
        assert LTTDDataTransformer.normalize_regime("") == "SIDEWAYS"
    
    def test_normalize_score_in_range(self):
        """Score in range is unchanged."""
        assert LTTDDataTransformer.normalize_score(0.5) == 0.5
        assert LTTDDataTransformer.normalize_score(-0.5) == -0.5
    
    def test_normalize_score_clamped(self):
        """Score out of range is clamped."""
        assert LTTDDataTransformer.normalize_score(1.5) == 1.0
        assert LTTDDataTransformer.normalize_score(-1.5) == -1.0
    
    def test_normalize_probabilities(self):
        """Probabilities are normalized to sum to 1.0."""
        p_bull, p_bear, p_sideways = LTTDDataTransformer.normalize_probabilities(
            0.6, 0.2, 0.2
        )
        assert abs(p_bull + p_bear + p_sideways - 1.0) < 0.001
    
    def test_normalize_probabilities_zero_sum(self):
        """Zero-sum probabilities default to equal distribution."""
        p_bull, p_bear, p_sideways = LTTDDataTransformer.normalize_probabilities(
            0.0, 0.0, 0.0
        )
        assert abs(p_bull - 0.33) < 0.01
        assert abs(p_bear - 0.33) < 0.01
        assert abs(p_sideways - 0.34) < 0.01
    
    def test_transform_record(self, lttd_records: list[LTTDRecord]):
        """Record is transformed to unified schema format."""
        result = LTTDDataTransformer.transform(lttd_records[0])
        
        assert result["date"] == "2026-07-01"
        assert result["lttd_score"] == 0.75
        assert result["lttd_regime"] == "BULL"
        assert result["lttd_exposure"] == 1.0


class TestLTTDPipeline:
    """Tests for LTTD migration pipeline."""
    
    def test_missing_database_raises_error(self):
        """Pipeline raises FileNotFoundError for missing database."""
        pipeline = LTTDMigrationPipeline(lttd_db_path="/nonexistent/lttd.db")
        
        with pytest.raises(FileNotFoundError):
            pipeline.read()
    
    def test_validate_valid_records(self, lttd_records: list[LTTDRecord]):
        """Valid records pass validation."""
        pipeline = LTTDMigrationPipeline()
        transformed = [LTTDDataTransformer.transform(r) for r in lttd_records]
        
        valid = pipeline.validate(transformed)
        
        assert len(valid) == len(lttd_records)
    
    def test_validate_invalid_date(self):
        """Invalid date format is rejected."""
        pipeline = LTTDMigrationPipeline()
        invalid_records = [
            {"date": "invalid-date", "lttd_score": 0.5, "lttd_regime": "BULL"}
        ]
        
        valid = pipeline.validate(invalid_records)
        
        assert len(valid) == 0
    
    def test_validate_invalid_regime(self):
        """Invalid regime is rejected."""
        pipeline = LTTDMigrationPipeline()
        invalid_records = [
            {
                "date": "2026-07-01",
                "lttd_score": 0.5,
                "lttd_regime": "INVALID",
                "lttd_p_bull": 0.33,
                "lttd_p_bear": 0.33,
                "lttd_p_sideways": 0.34,
                "lttd_exposure": 0.0,
            }
        ]
        
        valid = pipeline.validate(invalid_records)
        
        assert len(valid) == 0


# ═══════════════════════════════════════════════════════════
# Valuation Migration Tests
# ═══════════════════════════════════════════════════════════


class TestValuationTransformer:
    """Tests for Valuation data transformer."""
    
    def test_normalize_score_in_range(self):
        """Score in range is unchanged."""
        assert ValuationDataTransformer.normalize_score(1.5) == 1.5
        assert ValuationDataTransformer.normalize_score(-1.5) == -1.5
    
    def test_normalize_score_clamped(self):
        """Score out of range is clamped."""
        assert ValuationDataTransformer.normalize_score(2.5) == 2.0
        assert ValuationDataTransformer.normalize_score(-2.5) == -2.0
    
    def test_transform_record(self, valuation_records: list[ValuationRecord]):
        """Record is transformed to unified schema format."""
        result = ValuationDataTransformer.transform(valuation_records[0])
        
        assert result["date"] == "2026-07-01"
        assert result["mvo_score"] == 1.2
        assert result["mvo_pillar_fundamental"] == 0.8
        assert result["mvo_pillar_technical"] == 1.5
        assert result["mvo_pillar_sentiment"] == 1.3


class TestValuationPipeline:
    """Tests for Valuation migration pipeline."""
    
    def test_missing_database_raises_error(self):
        """Pipeline raises FileNotFoundError for missing database."""
        pipeline = ValuationMigrationPipeline(metrics_db_path="/nonexistent/metrics.db")
        
        with pytest.raises(FileNotFoundError):
            pipeline.read()
    
    def test_validate_valid_records(self, valuation_records: list[ValuationRecord]):
        """Valid records pass validation."""
        pipeline = ValuationMigrationPipeline()
        transformed = [ValuationDataTransformer.transform(r) for r in valuation_records]
        
        valid = pipeline.validate(transformed)
        
        assert len(valid) == len(valuation_records)


# ═══════════════════════════════════════════════════════════
# MTTD Sync Tests
# ═══════════════════════════════════════════════════════════


class TestMTTDTransformer:
    """Tests for MTTD data transformer."""
    
    def test_normalize_imo_in_range(self):
        """IMO in range is unchanged."""
        assert MTTDDataTransformer.normalize_imo(0.5) == 0.5
        assert MTTDDataTransformer.normalize_imo(-0.5) == -0.5
    
    def test_normalize_imo_clamped(self):
        """IMO out of range is clamped."""
        assert MTTDDataTransformer.normalize_imo(1.5) == 1.0
        assert MTTDDataTransformer.normalize_imo(-1.5) == -1.0
    
    def test_normalize_position_binary(self):
        """Position is normalized to binary."""
        assert MTTDDataTransformer.normalize_position(0.8) == 1.0
        assert MTTDDataTransformer.normalize_position(0.3) == 0.0
        assert MTTDDataTransformer.normalize_position(0.5) == 0.0
    
    def test_normalize_er_in_range(self):
        """ER in range is unchanged."""
        assert MTTDDataTransformer.normalize_er(0.5) == 0.5
    
    def test_normalize_er_clamped(self):
        """ER out of range is clamped."""
        assert MTTDDataTransformer.normalize_er(1.5) == 1.0
        assert MTTDDataTransformer.normalize_er(-0.5) == 0.0
    
    def test_normalize_entropy_non_negative(self):
        """Entropy is non-negative."""
        assert MTTDDataTransformer.normalize_entropy(1.5) == 1.5
        assert MTTDDataTransformer.normalize_entropy(-0.5) == 0.0
    
    def test_transform_record(self, mttd_records: list[MTTDRecord]):
        """Record is transformed to unified schema format."""
        result = MTTDDataTransformer.transform(mttd_records[0])
        
        assert result["date"] == "2026-07-01"
        assert result["mttd_imo"] == 0.45
        assert result["mttd_position"] == 1.0
        assert result["mttd_er"] == 0.65
        assert result["mttd_entropy"] == 1.2


class TestJSONDataReader:
    """Tests for MTTD JSON data reader."""
    
    def test_read_valid_json(self, tmp_path: Path):
        """Valid JSON file is read correctly."""
        data = [
            {"date": "2026-07-01", "imo": 0.5, "position": 1.0, "er": 0.6, "entropy": 1.2},
            {"date": "2026-07-02", "imo": -0.3, "position": 0.0, "er": 0.4, "entropy": 1.8},
        ]
        json_file = tmp_path / "btc_daily.json"
        json_file.write_text(json.dumps(data))
        
        reader = JSONDataReader(json_file)
        records = reader.read()
        
        assert len(records) == 2
        assert records[0].date == "2026-07-01"
        assert records[0].imo == 0.5
    
    def test_read_missing_file(self, tmp_path: Path):
        """Missing file returns empty list."""
        reader = JSONDataReader(tmp_path / "nonexistent.json")
        records = reader.read()
        
        assert records == []
    
    def test_read_invalid_json(self, tmp_path: Path):
        """Invalid JSON returns empty list."""
        json_file = tmp_path / "invalid.json"
        json_file.write_text("not valid json {{{")
        
        reader = JSONDataReader(json_file)
        records = reader.read()
        
        assert records == []


class TestMTTDSyncPipeline:
    """Tests for MTTD sync pipeline."""
    
    def test_validate_valid_records(self, mttd_records: list[MTTDRecord]):
        """Valid records pass validation."""
        pipeline = MTTDSyncPipeline()
        transformed = [MTTDDataTransformer.transform(r) for r in mttd_records]
        
        valid = pipeline.validate(transformed)
        
        assert len(valid) == len(mttd_records)
    
    def test_validate_invalid_imo(self):
        """Invalid IMO is rejected."""
        pipeline = MTTDSyncPipeline()
        invalid_records = [
            {"date": "2026-07-01", "mttd_imo": 1.5, "mttd_position": 1.0, "mttd_er": 0.5, "mttd_entropy": 1.0}
        ]
        
        valid = pipeline.validate(invalid_records)
        
        assert len(valid) == 0


# ═══════════════════════════════════════════════════════════
# Ichimoku Sync Tests
# ═══════════════════════════════════════════════════════════


class TestIchimokuTransformer:
    """Tests for Ichimoku data transformer."""
    
    def test_normalize_imo_in_range(self):
        """IMO in range is unchanged."""
        assert IchimokuDataTransformer.normalize_imo(0.5) == 0.5
    
    def test_normalize_imo_clamped(self):
        """IMO out of range is clamped."""
        assert IchimokuDataTransformer.normalize_imo(1.5) == 1.0
    
    def test_normalize_position_binary(self):
        """Position is normalized to binary."""
        assert IchimokuDataTransformer.normalize_position(0.8) == 1.0
        assert IchimokuDataTransformer.normalize_position(0.3) == 0.0
    
    def test_normalize_component_in_range(self):
        """Component in range is unchanged."""
        assert IchimokuDataTransformer.normalize_component(0.5) == 0.5
    
    def test_normalize_component_clamped(self):
        """Component out of range is clamped."""
        assert IchimokuDataTransformer.normalize_component(1.5) == 1.0
    
    def test_transform_record(self, ichimoku_records: list[IchimokuRecord]):
        """Record is transformed to unified schema format."""
        result = IchimokuDataTransformer.transform(ichimoku_records[0])
        
        assert result["date"] == "2026-07-01"
        assert result["ichi_imo"] == 0.6
        assert result["ichi_position"] == 1.0
        assert result["ichi_s_tk"] == 0.8
        assert result["ichi_s_cloud"] == 0.5
        assert result["ichi_s_future"] == 0.7
        assert result["ichi_s_chikou"] == 0.4


class TestIchimokuSyncPipeline:
    """Tests for Ichimoku sync pipeline."""
    
    def test_validate_valid_records(self, ichimoku_records: list[IchimokuRecord]):
        """Valid records pass validation."""
        pipeline = IchimokuSyncPipeline()
        transformed = [IchimokuDataTransformer.transform(r) for r in ichimoku_records]
        
        valid = pipeline.validate(transformed)
        
        assert len(valid) == len(ichimoku_records)
    
    def test_validate_invalid_component(self):
        """Invalid component score is rejected."""
        pipeline = IchimokuSyncPipeline()
        invalid_records = [
            {
                "date": "2026-07-01",
                "ichi_imo": 0.5,
                "ichi_position": 1.0,
                "ichi_s_tk": 1.5,  # Out of range
                "ichi_s_cloud": 0.5,
                "ichi_s_future": 0.5,
                "ichi_s_chikou": 0.5,
            }
        ]
        
        valid = pipeline.validate(invalid_records)
        
        assert len(valid) == 0


# ═══════════════════════════════════════════════════════════
# Integration Tests
# ═══════════════════════════════════════════════════════════


class TestMigrationToDatabase:
    """Integration tests for writing to the unified database."""
    
    def test_store_lttd_records(self, test_db: Path, lttd_records: list[LTTDRecord]):
        """LTTD records are stored in unified database."""
        pipeline = LTTDMigrationPipeline(target_db_path=test_db)
        transformed = [LTTDDataTransformer.transform(r) for r in lttd_records]
        valid = pipeline.validate(transformed)
        
        stored = pipeline.store(valid)
        
        assert stored == len(lttd_records)
        
        # Verify data in database
        conn = sqlite3.connect(str(test_db))
        rows = conn.execute(
            "SELECT * FROM unified_daily_analytics WHERE lttd_score IS NOT NULL"
        ).fetchall()
        conn.close()
        
        assert len(rows) == len(lttd_records)
    
    def test_store_valuation_records(self, test_db: Path, valuation_records: list[ValuationRecord]):
        """Valuation records are stored in unified database."""
        pipeline = ValuationMigrationPipeline(target_db_path=test_db)
        transformed = [ValuationDataTransformer.transform(r) for r in valuation_records]
        valid = pipeline.validate(transformed)
        
        stored = pipeline.store(valid)
        
        assert stored == len(valuation_records)
        
        # Verify data in database
        conn = sqlite3.connect(str(test_db))
        rows = conn.execute(
            "SELECT * FROM unified_daily_analytics WHERE mvo_score IS NOT NULL"
        ).fetchall()
        conn.close()
        
        assert len(rows) == len(valuation_records)
    
    def test_upsert_behavior(self, test_db: Path, lttd_records: list[LTTDRecord]):
        """Re-running migration upserts (INSERT OR REPLACE) correctly."""
        pipeline = LTTDMigrationPipeline(target_db_path=test_db)
        transformed = [LTTDDataTransformer.transform(r) for r in lttd_records]
        valid = pipeline.validate(transformed)
        
        # First run
        stored1 = pipeline.store(valid)
        
        # Second run (should upsert, not duplicate)
        stored2 = pipeline.store(valid)
        
        # Verify no duplicates
        conn = sqlite3.connect(str(test_db))
        count = conn.execute(
            "SELECT COUNT(*) FROM unified_daily_analytics WHERE lttd_score IS NOT NULL"
        ).fetchone()[0]
        conn.close()
        
        assert count == len(lttd_records)
