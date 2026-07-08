"""
Maftia Quant — Valuation System Migration

Migrates data from the legacy `metrics.db` (Valuation system repository)
to the unified `maftia_quant.db` schema.

Usage:
    from src.pipelines.valuation_migration import ValuationMigrationPipeline
    
    pipeline = ValuationMigrationPipeline(metrics_db_path="/path/to/metrics.db")
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

from db import get_db, execute_insert, execute_many_insert


@dataclass
class ValuationRecord:
    """Represents a single Valuation record from the legacy database."""
    date: str
    mvo_score: float  # Master Valuation Oscillator ∈ [-2, +2]
    pillar_fundamental: float
    pillar_technical: float
    pillar_sentiment: float


class LegacyValuationReader:
    """
    Reads data from the legacy metrics.db database.
    
    Expected legacy schema:
    - valuation_daily: date, mvo_score, pillar_fundamental, pillar_technical, pillar_sentiment
    - Or similar table structure from the Valuation system repository.
    """
    
    def __init__(self, db_path: str | Path):
        """
        Initialize the legacy reader.
        
        Args:
            db_path: Path to the legacy metrics.db
        """
        self.db_path = Path(db_path)
    
    def is_available(self) -> bool:
        """Check if the legacy database exists."""
        return self.db_path.exists()
    
    def read_all(self) -> list[ValuationRecord]:
        """
        Read all Valuation records from legacy database.
        
        Returns:
            List of ValuationRecord objects
            
        Raises:
            FileNotFoundError: If legacy database doesn't exist
        """
        if not self.is_available():
            raise FileNotFoundError(
                f"Legacy Valuation database not found: {self.db_path}"
            )
        
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        
        try:
            # Try common table names from Valuation system
            table_names = [
                "valuation_daily",
                "mvo_daily",
                "valuation_signals",
                "daily_valuation",
            ]
            
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
            
            print(f"⚠️  Could not find standard Valuation table. Available tables: {[t['name'] for t in tables]}")
            return []
            
        finally:
            conn.close()
    
    def _parse_row(self, row: sqlite3.Row) -> ValuationRecord:
        """Parse a database row into a ValuationRecord."""
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
        
        return ValuationRecord(
            date=safe_str("date", ""),
            mvo_score=safe_float("mvo_score", 0.0),
            pillar_fundamental=safe_float("pillar_fundamental", 0.0),
            pillar_technical=safe_float("pillar_technical", 0.0),
            pillar_sentiment=safe_float("pillar_sentiment", 0.0),
        )


class ValuationDataTransformer:
    """Transforms Valuation data to unified schema format."""
    
    # MVO score is already in [-2, +2] range from the Valuation system
    # No normalization needed for the score itself
    
    @classmethod
    def normalize_score(cls, score: float) -> float:
        """Clamp MVO score to [-2.0, +2.0] range."""
        return max(-2.0, min(2.0, score))
    
    @classmethod
    def transform(cls, record: ValuationRecord) -> dict[str, Any]:
        """
        Transform a legacy Valuation record to unified schema format.
        
        Args:
            record: Legacy Valuation record
            
        Returns:
            Dictionary matching unified_daily_analytics schema
        """
        return {
            "date": record.date,
            "mvo_score": cls.normalize_score(record.mvo_score),
            "mvo_pillar_fundamental": record.pillar_fundamental,
            "mvo_pillar_technical": record.pillar_technical,
            "mvo_pillar_sentiment": record.pillar_sentiment,
        }


class ValuationMigrationPipeline:
    """
    Migrates Valuation data from legacy database to unified schema.
    
    Pipeline: Read → Transform → Validate → Store
    """
    
    def __init__(
        self,
        metrics_db_path: str | Path = "metrics.db",
        target_db_path: Optional[str | Path] = None,
    ):
        """
        Initialize the migration pipeline.
        
        Args:
            metrics_db_path: Path to legacy metrics.db
            target_db_path: Optional target database path (default: unified db)
        """
        self.reader = LegacyValuationReader(metrics_db_path)
        self.target_db_path = target_db_path
        self.transformer = ValuationDataTransformer()
    
    def read(self) -> list[ValuationRecord]:
        """Read data from legacy database."""
        print(f"📖 Reading from legacy Valuation database: {self.reader.db_path}")
        records = self.reader.read_all()
        print(f"   Found {len(records)} records")
        return records
    
    def transform(self, records: list[ValuationRecord]) -> list[dict[str, Any]]:
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
        - MVO score is in [-2.0, +2.0]
        - Pillar scores are numeric
        """
        print("🔍 Validating records...")
        valid = []
        invalid_count = 0
        
        for record in records:
            try:
                # Validate date format
                datetime.strptime(record["date"], "%Y-%m-%d")
                
                # Validate MVO score range
                assert -2.0 <= record["mvo_score"] <= 2.0, (
                    f"MVO score {record['mvo_score']} out of range [-2.0, 2.0]"
                )
                
                # Validate pillar scores are numeric
                numeric_types = (int, float)
                for pillar in ["mvo_pillar_fundamental", "mvo_pillar_technical", "mvo_pillar_sentiment"]:
                    assert isinstance(record[pillar], numeric_types), (
                        f"{pillar} must be numeric, got {type(record[pillar])}"
                    )
                
                valid.append(record)
            except (ValueError, AssertionError) as e:
                invalid_count += 1
                print(f"   ⚠️  Invalid record {record.get('date')}: {e}")
        
        print(f"   {len(valid)} valid, {invalid_count} invalid")
        return valid
    
    def store(self, records: list[dict[str, Any]]) -> int:
        """
        Store validated records in unified database.
        
        Uses INSERT OR REPLACE to handle re-runs and merge with existing data.
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
        print("Valuation System Migration")
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
    
    parser = argparse.ArgumentParser(description="Migrate Valuation data to unified schema")
    parser.add_argument(
        "--metrics-db",
        default="metrics.db",
        help="Path to legacy metrics.db (default: metrics.db)",
    )
    args = parser.parse_args()
    
    pipeline = ValuationMigrationPipeline(metrics_db_path=args.metrics_db)
    result = pipeline.run()
