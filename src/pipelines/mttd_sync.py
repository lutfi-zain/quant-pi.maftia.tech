"""
Maftia Quant — MTTD System Sync

Syncs data from MTTD system sources (btc_daily.json, CSV files)
to the unified `maftia_quant.db` schema.

Usage:
    from src.pipelines.mttd_sync import MTTDSyncPipeline
    
    pipeline = MTTDSyncPipeline(data_dir="/path/to/mttd/data")
    result = pipeline.run()
"""

import sys
import json
import csv
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Optional, Any
from dataclasses import dataclass

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from db import execute_many_insert


@dataclass
class MTTDRecord:
    """Represents a single MTTD record from legacy sources."""
    date: str
    imo: float  # Integrated Market Oscillator ∈ [-1, +1]
    position: float  # 0.0 or 1.0
    er: float  # Efficiency Ratio ∈ [0, 1]
    entropy: float  # Shannon Entropy


class JSONDataReader:
    """Reads MTTD data from btc_daily.json files."""
    
    def __init__(self, file_path: str | Path):
        self.file_path = Path(file_path)
    
    def is_available(self) -> bool:
        return self.file_path.exists()
    
    def read(self) -> list[MTTDRecord]:
        """Read records from JSON file."""
        if not self.is_available():
            return []
        
        try:
            with open(self.file_path) as f:
                data = json.load(f)
            
            # Handle different JSON structures
            records = []
            if isinstance(data, list):
                items = data
            elif isinstance(data, dict) and "data" in data:
                items = data["data"]
            else:
                items = [data]
            
            for item in items:
                record = self._parse_item(item)
                if record:
                    records.append(record)
            
            return records
        except (json.JSONDecodeError, IOError) as e:
            print(f"⚠️  Error reading JSON: {e}")
            return []
    
    def _parse_item(self, item: dict[str, Any]) -> Optional[MTTDRecord]:
        """Parse a JSON item into an MTTDRecord."""
        try:
            date_str = item.get("date") or item.get("timestamp", "")
            if not date_str:
                return None
            
            # Normalize date format
            if "T" in str(date_str):
                date_str = str(date_str).split("T")[0]
            
            return MTTDRecord(
                date=str(date_str),
                imo=float(item.get("imo", 0.0) or 0.0),
                position=float(item.get("position", 0.0) or 0.0),
                er=float(item.get("er", 0.0) or 0.0),
                entropy=float(item.get("entropy", 0.0) or 0.0),
            )
        except (ValueError, TypeError):
            return None


class CSVDataReader:
    """Reads MTTD data from CSV files."""
    
    def __init__(self, file_path: str | Path):
        self.file_path = Path(file_path)
    
    def is_available(self) -> bool:
        return self.file_path.exists()
    
    def read(self) -> list[MTTDRecord]:
        """Read records from CSV file."""
        if not self.is_available():
            return []
        
        try:
            records = []
            with open(self.file_path, newline="") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    record = self._parse_row(row)
                    if record:
                        records.append(record)
            return records
        except IOError as e:
            print(f"⚠️  Error reading CSV: {e}")
            return []
    
    def _parse_row(self, row: dict[str, str]) -> Optional[MTTDRecord]:
        """Parse a CSV row into an MTTDRecord."""
        try:
            date_str = row.get("date", "")
            if not date_str:
                return None
            
            return MTTDRecord(
                date=date_str.strip(),
                imo=float(row.get("imo", 0.0) or 0.0),
                position=float(row.get("position", 0.0) or 0.0),
                er=float(row.get("er", 0.0) or 0.0),
                entropy=float(row.get("entropy", 0.0) or 0.0),
            )
        except (ValueError, TypeError):
            return None


class MTTDDataTransformer:
    """Transforms MTTD data to unified schema format."""
    
    @classmethod
    def normalize_imo(cls, imo: float) -> float:
        """Clamp IMO to [-1.0, +1.0] range."""
        return max(-1.0, min(1.0, imo))
    
    @classmethod
    def normalize_position(cls, position: float) -> float:
        """Normalize position to binary {0.0, 1.0}."""
        return 1.0 if position > 0.5 else 0.0
    
    @classmethod
    def normalize_er(cls, er: float) -> float:
        """Clamp ER to [0.0, 1.0] range."""
        return max(0.0, min(1.0, er))
    
    @classmethod
    def normalize_entropy(cls, entropy: float) -> float:
        """Ensure entropy is non-negative."""
        return max(0.0, entropy)
    
    @classmethod
    def transform(cls, record: MTTDRecord) -> dict[str, Any]:
        """
        Transform a legacy MTTD record to unified schema format.
        
        Args:
            record: Legacy MTTD record
            
        Returns:
            Dictionary matching unified_daily_analytics schema
        """
        return {
            "date": record.date,
            "mttd_imo": cls.normalize_imo(record.imo),
            "mttd_position": cls.normalize_position(record.position),
            "mttd_er": cls.normalize_er(record.er),
            "mttd_entropy": cls.normalize_entropy(record.entropy),
        }


class MTTDSyncPipeline:
    """
    Syncs MTTD data from legacy sources to unified schema.
    
    Pipeline: Read (JSON/CSV) → Transform → Validate → Store
    """
    
    def __init__(
        self,
        data_dir: str | Path = ".",
        target_db_path: Optional[str | Path] = None,
    ):
        """
        Initialize the sync pipeline.
        
        Args:
            data_dir: Directory containing MTTD data files
            target_db_path: Optional target database path (default: unified db)
        """
        self.data_dir = Path(data_dir)
        self.target_db_path = target_db_path
        self.transformer = MTTDDataTransformer()
        
        # Initialize readers
        self.json_reader = JSONDataReader(self.data_dir / "btc_daily.json")
        self.csv_reader = CSVDataReader(self.data_dir / "mttd_daily.csv")
    
    def read(self) -> list[MTTDRecord]:
        """Read data from available sources."""
        records: list[MTTDRecord] = []
        
        # Try JSON first
        if self.json_reader.is_available():
            print(f"📖 Reading from JSON: {self.json_reader.file_path}")
            json_records = self.json_reader.read()
            print(f"   Found {len(json_records)} records from JSON")
            records.extend(json_records)
        
        # Try CSV
        if self.csv_reader.is_available():
            print(f"📖 Reading from CSV: {self.csv_reader.file_path}")
            csv_records = self.csv_reader.read()
            print(f"   Found {len(csv_records)} records from CSV")
            records.extend(csv_records)
        
        if not records:
            print("⚠️  No MTTD data files found")
        
        return records
    
    def transform(self, records: list[MTTDRecord]) -> list[dict[str, Any]]:
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
        - ER is in [0.0, 1.0]
        - Entropy is non-negative
        """
        print("🔍 Validating records...")
        valid = []
        invalid_count = 0
        
        for record in records:
            try:
                # Validate date format
                datetime.strptime(record["date"], "%Y-%m-%d")
                
                # Validate IMO range
                assert -1.0 <= record["mttd_imo"] <= 1.0, (
                    f"IMO {record['mttd_imo']} out of range"
                )
                
                # Validate position is binary
                valid_positions = {0.0, 1.0}
                assert record["mttd_position"] in valid_positions
                
                # Validate ER range
                assert 0.0 <= record["mttd_er"] <= 1.0, (
                    f"ER {record['mttd_er']} out of range"
                )
                
                # Validate entropy is non-negative
                assert record["mttd_entropy"] >= 0.0, (
                    f"Entropy {record['mttd_entropy']} is negative"
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
        print("MTTD System Sync")
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
    
    parser = argparse.ArgumentParser(description="Sync MTTD data to unified schema")
    parser.add_argument(
        "--data-dir",
        default=".",
        help="Directory containing MTTD data files (default: current dir)",
    )
    args = parser.parse_args()
    
    pipeline = MTTDSyncPipeline(data_dir=args.data_dir)
    result = pipeline.run()
