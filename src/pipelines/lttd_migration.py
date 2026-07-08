"""
Maftia Quant — LTTD System Migration

Migrates data from the legacy `lttd.db` (LTTD system repository)
to the unified `maftia_quant.db` schema.

Usage:
    from src.pipelines.lttd_migration import LTTDMigrationPipeline
    
    pipeline = LTTDMigrationPipeline(lttd_db_path="/path/to/lttd.db")
    result = pipeline.run()
"""

import sys
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Optional, Any
from dataclasses import dataclass

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from db import get_db, execute_insert, execute_many_insert, execute_query


@dataclass
class LTTDRecord:
    """Represents a single LTTD record from the legacy database."""
    date: str
    score: float
    regime: str  # 'BULL' | 'BEAR' | 'SIDEWAYS'
    p_bull: float
    p_bear: float
    p_sideways: float
    exposure: float  # 0.0 or 1.0
    circuit_breaker: int = 0  # 0 or 1


class LegacyLTTDReader:
    """
    Reads data from the legacy lttd.db database.
    
    Expected legacy schema:
    - lttd_signals: date, score, regime, p_bull, p_bear, p_sideways, exposure
    - Or similar table structure from the LTTD system repository.
    """
    
    def __init__(self, db_path: str | Path):
        """
        Initialize the legacy reader.
        
        Args:
            db_path: Path to the legacy lttd.db
        """
        self.db_path = Path(db_path)
    
    def is_available(self) -> bool:
        """Check if the legacy database exists."""
        return self.db_path.exists()
    
    def read_all(self) -> list[LTTDRecord]:
        """
        Read all LTTD records from legacy database.
        
        Returns:
            List of LTTDRecord objects
            
        Raises:
            FileNotFoundError: If legacy database doesn't exist
        """
        if not self.is_available():
            raise FileNotFoundError(
                f"Legacy LTTD database not found: {self.db_path}"
            )
        
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        
        try:
            # Try common table names from LTTD system
            table_names = ["lttd_signals", "lttd_daily", "signals", "daily_signals"]
            
            for table in table_names:
                try:
                    rows = conn.execute(f"SELECT * FROM {table} ORDER BY date").fetchall()
                    return [self._parse_row(row) for row in rows]
                except sqlite3.OperationalError:  # noqa: E711
                    continue
            
            # If no known table found, try to discover the schema
            tables = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
            
            print(f"⚠️  Could not find standard LTTD table. Available tables: {[t['name'] for t in tables]}")
            return []
            
        finally:
            conn.close()
    
    def _parse_row(self, row: sqlite3.Row) -> LTTDRecord:
        """Parse a database row into an LTTDRecord."""
        # Adapt column names based on actual legacy schema
        # sqlite3.Row supports key access but not .get(), so use try/except
        def safe_float(key: str, default: float) -> float:
            try:
                val = row[key]
                return float(val) if val is not None else default
            except (IndexError, KeyError, TypeError, ValueError):
                return default
        
        def safe_str(key: str, default: str) -> str:
            try:
                val = row[key]
                return str(val) if val is not None else default
            except (IndexError, KeyError, TypeError):
                return default
        
        def safe_int(key: str, default: int) -> int:
            try:
                val = row[key]
                return int(val) if val is not None else default
            except (IndexError, KeyError, TypeError, ValueError):
                return default
        
        return LTTDRecord(
            date=str(row["date"]),
            score=safe_float("score", 0.0),
            regime=safe_str("regime", "SIDEWAYS"),
            p_bull=safe_float("p_bull", 0.33),
            p_bear=safe_float("p_bear", 0.33),
            p_sideways=safe_float("p_sideways", 0.34),
            exposure=safe_float("exposure", 0.0),
            circuit_breaker=safe_int("circuit_breaker", 0),
        )


class LTTDDataTransformer:
    """Transforms LTTD data to unified schema format."""
    
    # Regime normalization map
    REGIME_MAP = {
        "bull": "BULL",
        "bear": "BEAR",
        "sideways": "SIDEWAYS",
        "1": "BULL",
        "-1": "BEAR",
        "0": "SIDEWAYS",
    }
    
    @classmethod
    def normalize_regime(cls, regime: str) -> str:
        """Normalize regime string to standard format."""
        return cls.REGIME_MAP.get(regime.lower().strip(), "SIDEWAYS")
    
    @classmethod
    def normalize_score(cls, score: float) -> float:
        """Normalize LTTD score to [-1.0, +1.0] range."""
        return max(-1.0, min(1.0, score))
    
    @classmethod
    def normalize_probabilities(cls, p_bull: float, p_bear: float, p_sideways: float) -> tuple[float, float, float]:
        """Normalize probabilities to sum to 1.0."""
        total = p_bull + p_bear + p_sideways
        if total == 0:
            return (0.33, 0.33, 0.34)
        return (
            p_bull / total,
            p_bear / total,
            p_sideways / total,
        )
    
    @classmethod
    def transform(cls, record: LTTDRecord) -> dict[str, Any]:
        """
        Transform a legacy LTTD record to unified schema format.
        
        Args:
            record: Legacy LTTD record
            
        Returns:
            Dictionary matching unified_daily_analytics schema
        """
        # Normalize probabilities
        p_bull, p_bear, p_sideways = cls.normalize_probabilities(
            record.p_bull, record.p_bear, record.p_sideways
        )
        
        return {
            "date": record.date,
            "lttd_score": cls.normalize_score(record.score),
            "lttd_regime": cls.normalize_regime(record.regime),
            "lttd_p_bull": p_bull,
            "lttd_p_bear": p_bear,
            "lttd_p_sideways": p_sideways,
            "lttd_exposure": float(record.exposure) if record.exposure is not None else 0.0,
            "lttd_circuit_breaker": int(record.circuit_breaker) if record.circuit_breaker is not None else 0,
        }


class LTTDMigrationPipeline:
    """
    Migrates LTTD data from legacy database to unified schema.
    
    Pipeline: Read → Transform → Validate → Store
    """
    
    def __init__(
        self,
        lttd_db_path: str | Path = "lttd.db",
        target_db_path: Optional[str | Path] = None,
    ):
        """
        Initialize the migration pipeline.
        
        Args:
            lttd_db_path: Path to legacy lttd.db
            target_db_path: Optional target database path (default: unified db)
        """
        self.reader = LegacyLTTDReader(lttd_db_path)
        self.target_db_path = target_db_path
        self.transformer = LTTDDataTransformer()
    
    def read(self) -> list[LTTDRecord]:
        """Read data from legacy database."""
        print(f"📖 Reading from legacy LTTD database: {self.reader.db_path}")
        records = self.reader.read_all()
        print(f"   Found {len(records)} records")
        return records
    
    def transform(self, records: list[LTTDRecord]) -> list[dict[str, Any]]:
        """Transform records to unified schema."""
        print("🔄 Transforming to unified schema...")
        transformed = [self.transformer.transform(r) for r in records]
        print(f"   Transformed {len(transformed)} records")
        return transformed
    
    def validate(self, records: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """
        Validate transformed records.
        
        Checks:
        - Date format is YYYY-MM-DD
        - Score is in [-1.0, +1.0]
        - Regime is valid enum value
        - Probabilities sum to ~1.0
        """
        print("🔍 Validating records...")
        valid = []
        invalid_count = 0
        
        for record in records:
            try:
                # Validate date format
                datetime.strptime(record["date"], "%Y-%m-%d")
                
                # Validate score range
                assert -1.0 <= record["lttd_score"] <= 1.0
                
                # Validate regime
                valid_regimes = {"BULL", "BEAR", "SIDEWAYS"}
                assert record["lttd_regime"] in valid_regimes
                
                # Validate probabilities sum to ~1.0
                prob_sum = (
                    record["lttd_p_bull"]
                    + record["lttd_p_bear"]
                    + record["lttd_p_sideways"]
                )
                assert 0.99 <= prob_sum <= 1.01, f"Probabilities sum to {prob_sum}"
                
                # Validate exposure
                valid_exposures = {0.0, 1.0}
                assert record["lttd_exposure"] in valid_exposures
                
                valid.append(record)
            except (ValueError, AssertionError) as e:
                invalid_count += 1
                print(f"   ⚠️  Invalid record {record.get('date')}: {e}")
        
        print(f"   {len(valid)} valid, {invalid_count} invalid")
        return valid
    
    def store(self, records: list[dict[str, Any]]) -> int:
        """
        Store validated records in unified database.
        
        Uses INSERT OR REPLACE to handle re-runs.
        """
        if not records:
            return 0
        
        print("💾 Storing in unified database...")
        target = Path(self.target_db_path) if self.target_db_path else None
        execute_many_insert("unified_daily_analytics", records, target)
        print(f"   Stored {len(records)} records")
        return len(records)
    
    def run(self) -> dict[str, Any]:
        """
        Run the full migration pipeline.
        
        Returns:
            Migration execution summary
        """
        print("═" * 60)
        print("LTTD System Migration")
        print("═" * 60)
        
        # Read
        records = self.read()
        
        if not records:
            print("⚠️  No records to migrate")
            return {"migrated": 0, "skipped": 0, "errors": 0}
        
        # Transform
        transformed = self.transform(records)
        
        # Validate
        valid = self.validate(transformed)
        
        # Store
        stored = self.store(valid)
        
        result = {
            "migrated": stored,
            "skipped": len(records) - len(valid),
            "errors": len(records) - len(valid),
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        print("═" * 60)
        print(f"✅ Migration complete: {result}")
        print("═" * 60)
        
        return result


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Migrate LTTD data to unified schema")
    parser.add_argument(
        "--lttd-db",
        default="lttd.db",
        help="Path to legacy lttd.db (default: lttd.db)",
    )
    args = parser.parse_args()
    
    pipeline = LTTDMigrationPipeline(lttd_db_path=args.lttd_db)
    result = pipeline.run()
