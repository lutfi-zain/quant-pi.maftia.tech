"""
Maftia Quant — Ichimoku System Sync

Syncs data from Ichimoku system sources (yfinance cache, FastAPI)
to the unified `maftia_quant.db` schema.

Usage:
    from src.pipelines.ichimoku_sync import IchimokuSyncPipeline
    
    pipeline = IchimokuSyncPipeline(cache_dir="/path/to/yfinance/cache")
    result = pipeline.run()
"""

import sys
import json
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Optional, Any
from dataclasses import dataclass

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from db import execute_many_insert


@dataclass
class IchimokuRecord:
    """Represents a single Ichimoku record from legacy sources."""
    date: str
    imo: float  # Composite Ichimoku Oscillator ∈ [-1, +1]
    position: float  # 0.0 or 1.0
    s_tk: float  # Tenkan-sen signal
    s_cloud: float  # Cloud signal
    s_future: float  # Future span signal
    s_chikou: float  # Chikou span signal


class YFinanceCacheReader:
    """Reads Ichimoku data from yfinance cache files."""
    
    def __init__(self, cache_dir: str | Path):
        self.cache_dir = Path(cache_dir)
    
    def is_available(self) -> bool:
        return self.cache_dir.exists()
    
    def read(self) -> list[IchimokuRecord]:
        """Read records from yfinance cache."""
        if not self.is_available():
            return []
        
        records: list[IchimokuRecord] = []
        
        # Look for Ichimoku-related cache files
        patterns = ["*ichimoku*.json", "*ichi*.json", "*BTC*cache*.json"]
        
        for pattern in patterns:
            for cache_file in self.cache_dir.glob(pattern):
                file_records = self._read_cache_file(cache_file)
                records.extend(file_records)
        
        return records
    
    def _read_cache_file(self, file_path: Path) -> list[IchimokuRecord]:
        """Read a single cache file."""
        try:
            with open(file_path) as f:
                data = json.load(f)
            
            records = []
            items = data if isinstance(data, list) else [data]
            
            for item in items:
                record = self._parse_item(item)
                if record:
                    records.append(record)
            
            return records
        except (json.JSONDecodeError, IOError):
            return []
    
    def _parse_item(self, item: dict[str, Any]) -> Optional[IchimokuRecord]:
        """Parse a cache item into an IchimokuRecord."""
        try:
            date_str = item.get("date", "")
            if not date_str:
                return None
            
            # Normalize date format
            if "T" in str(date_str):
                date_str = str(date_str).split("T")[0]
            
            return IchimokuRecord(
                date=str(date_str),
                imo=float(item.get("imo", 0.0) or 0.0),
                position=float(item.get("position", 0.0) or 0.0),
                s_tk=float(item.get("s_tk", 0.0) or 0.0),
                s_cloud=float(item.get("s_cloud", 0.0) or 0.0),
                s_future=float(item.get("s_future", 0.0) or 0.0),
                s_chikou=float(item.get("s_chikou", 0.0) or 0.0),
            )
        except (ValueError, TypeError):
            return None


class FastAPIReader:
    """Reads Ichimoku data from FastAPI endpoint."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip("/")
    
    def is_available(self) -> bool:
        """Check if FastAPI endpoint is reachable."""
        try:
            import urllib.request
            url = f"{self.base_url}/health"
            with urllib.request.urlopen(url, timeout=5) as response:
                return response.status == 200
        except Exception:
            return False
    
    def read(self, from_date: Optional[str] = None) -> list[IchimokuRecord]:
        """Read records from FastAPI endpoint."""
        if not self.is_available():
            return []
        
        try:
            import urllib.request
            import json
            
            url = f"{self.base_url}/api/v1/ichimoku/signals"
            if from_date:
                url += f"?from={from_date}"
            
            with urllib.request.urlopen(url) as response:
                data = json.loads(response.read().decode())
            
            records = []
            items = data.get("data", []) if isinstance(data, dict) else data
            
            for item in items:
                record = self._parse_item(item)
                if record:
                    records.append(record)
            
            return records
        except Exception as e:
            print(f"⚠️  Error reading from FastAPI: {e}")
            return []
    
    def _parse_item(self, item: dict[str, Any]) -> Optional[IchimokuRecord]:
        """Parse an API response item into an IchimokuRecord."""
        try:
            date_str = item.get("date", "")
            if not date_str:
                return None
            
            return IchimokuRecord(
                date=str(date_str).split("T")[0],
                imo=float(item.get("imo", 0.0) or 0.0),
                position=float(item.get("position", 0.0) or 0.0),
                s_tk=float(item.get("s_tk", 0.0) or 0.0),
                s_cloud=float(item.get("s_cloud", 0.0) or 0.0),
                s_future=float(item.get("s_future", 0.0) or 0.0),
                s_chikou=float(item.get("s_chikou", 0.0) or 0.0),
            )
        except (ValueError, TypeError):
            return None


class IchimokuDataTransformer:
    """Transforms Ichimoku data to unified schema format."""
    
    @classmethod
    def normalize_imo(cls, imo: float) -> float:
        """Clamp IMO to [-1.0, +1.0] range."""
        return max(-1.0, min(1.0, imo))
    
    @classmethod
    def normalize_position(cls, position: float) -> float:
        """Normalize position to binary {0.0, 1.0}."""
        return 1.0 if position > 0.5 else 0.0
    
    @classmethod
    def normalize_component(cls, value: float) -> float:
        """Clamp component score to [-1.0, +1.0] range."""
        return max(-1.0, min(1.0, value))
    
    @classmethod
    def transform(cls, record: IchimokuRecord) -> dict[str, Any]:
        """
        Transform a legacy Ichimoku record to unified schema format.
        
        Args:
            record: Legacy Ichimoku record
            
        Returns:
            Dictionary matching unified_daily_analytics schema
        """
        return {
            "date": record.date,
            "ichi_imo": cls.normalize_imo(record.imo),
            "ichi_position": cls.normalize_position(record.position),
            "ichi_s_tk": cls.normalize_component(record.s_tk),
            "ichi_s_cloud": cls.normalize_component(record.s_cloud),
            "ichi_s_future": cls.normalize_component(record.s_future),
            "ichi_s_chikou": cls.normalize_component(record.s_chikou),
        }


class IchimokuSyncPipeline:
    """
    Syncs Ichimoku data from legacy sources to unified schema.
    
    Pipeline: Read (Cache/API) → Transform → Validate → Store
    """
    
    def __init__(
        self,
        cache_dir: str | Path = ".",
        api_url: Optional[str] = None,
        target_db_path: Optional[str | Path] = None,
    ):
        """
        Initialize the sync pipeline.
        
        Args:
            cache_dir: Directory containing yfinance cache files
            api_url: Optional FastAPI endpoint URL
            target_db_path: Optional target database path (default: unified db)
        """
        self.cache_reader = YFinanceCacheReader(cache_dir)
        self.api_reader = FastAPIReader(api_url) if api_url else None
        self.target_db_path = target_db_path
        self.transformer = IchimokuDataTransformer()
    
    def read(self) -> list[IchimokuRecord]:
        """Read data from available sources."""
        records: list[IchimokuRecord] = []
        
        # Try cache first
        if self.cache_reader.is_available():
            print(f"📖 Reading from yfinance cache: {self.cache_reader.cache_dir}")
            cache_records = self.cache_reader.read()
            print(f"   Found {len(cache_records)} records from cache")
            records.extend(cache_records)
        
        # Try FastAPI
        if self.api_reader and self.api_reader.is_available():
            print(f"📖 Reading from FastAPI: {self.api_reader.base_url}")
            api_records = self.api_reader.read()
            print(f"   Found {len(api_records)} records from API")
            records.extend(api_records)
        
        if not records:
            print("⚠️  No Ichimoku data sources found")
        
        return records
    
    def transform(self, records: list[IchimokuRecord]) -> list[dict[str, Any]]:
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
        - IMO is in [-1.0, +1.0]
        - Position is binary {0.0, 1.0}
        - Component scores are in [-1.0, +1.0]
        """
        print("🔍 Validating records...")
        valid = []
        invalid_count = 0
        
        for record in records:
            try:
                # Validate date format
                datetime.strptime(record["date"], "%Y-%m-%d")
                
                # Validate IMO range
                assert -1.0 <= record["ichi_imo"] <= 1.0, (
                    f"IMO {record['ichi_imo']} out of range"
                )
                
                # Validate position is binary
                valid_positions = {0.0, 1.0}
                assert record["ichi_position"] in valid_positions
                
                # Validate component scores
                components = ["ichi_s_tk", "ichi_s_cloud", "ichi_s_future", "ichi_s_chikou"]
                for comp in components:
                    assert -1.0 <= record[comp] <= 1.0, (
                        f"{comp} {record[comp]} out of range"
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
        Run the full sync pipeline.
        
        Returns:
            Sync execution summary
        """
        print("═" * 60)
        print("Ichimoku System Sync")
        print("═" * 60)
        
        # Read
        records = self.read()
        
        if not records:
            print("⚠️  No records to sync")
            return {"synced": 0, "skipped": 0, "errors": 0}
        
        # Transform
        transformed = self.transform(records)
        
        # Validate
        valid = self.validate(transformed)
        
        # Store
        stored = self.store(valid)
        
        result = {
            "synced": stored,
            "skipped": len(records) - len(valid),
            "errors": len(records) - len(valid),
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        print("═" * 60)
        print(f"✅ Sync complete: {result}")
        print("═" * 60)
        
        return result


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Sync Ichimoku data to unified schema")
    parser.add_argument(
        "--cache-dir",
        default=".",
        help="Directory containing yfinance cache files (default: current dir)",
    )
    parser.add_argument(
        "--api-url",
        default=None,
        help="FastAPI endpoint URL (optional)",
    )
    args = parser.parse_args()
    
    pipeline = IchimokuSyncPipeline(
        cache_dir=args.cache_dir,
        api_url=args.api_url,
    )
    result = pipeline.run()
