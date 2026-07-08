"""
Maftia Quant — CausalFreshnessGuard Module

Validates BRK data freshness to prevent stale data ingestion.
Ensures all on-chain metrics are recent before storage.

Usage:
    from src.causal_freshness_guard import CausalFreshnessGuard, StaleDataError
    
    guard = CausalFreshnessGuard()
    validated_data = guard.validate(response, "sth_mvrv")
"""

from datetime import datetime, timedelta
from typing import Any, Optional


class StaleDataError(Exception):
    """Raised when data fails freshness validation."""
    
    def __init__(self, series_name: str, stamp: datetime, expected: datetime):
        self.series_name = series_name
        self.stamp = stamp
        self.expected = expected
        super().__init__(
            f"{series_name} data stale: stamp={stamp}, expected >= {expected}"
        )


class CausalFreshnessGuard:
    """
    Validates that BRK data is fresh before ingestion.
    
    BRK data is derived from confirmed on-chain state.
    The stamp field ≠ datetime.now(). Always check freshness.
    
    Rules:
        - stamp >= yesterday → ACCEPT
        - stamp < yesterday → REJECT (StaleDataError)
    """
    
    def __init__(self, tolerance_days: int = 1):
        """
        Initialize the freshness guard.
        
        Args:
            tolerance_days: Number of days of staleness allowed (default: 1)
        """
        self.tolerance_days = tolerance_days
    
    def get_cutoff_time(self, now: Optional[datetime] = None) -> datetime:
        """
        Calculate the cutoff time for freshness.
        
        Args:
            now: Optional current time (for testing)
            
        Returns:
            Cutoff datetime (now - tolerance_days)
        """
        if now is None:
            now = datetime.utcnow()
        return now - timedelta(days=self.tolerance_days)
    
    def parse_stamp(self, stamp: Any) -> datetime:
        """
        Parse a stamp value into a datetime.
        
        Args:
            stamp: Stamp value (string or datetime)
            
        Returns:
            Parsed datetime
            
        Raises:
            ValueError: If stamp cannot be parsed
        """
        if isinstance(stamp, datetime):
            return stamp
        
        if isinstance(stamp, str):
            # Try common ISO formats
            for fmt in [
                "%Y-%m-%dT%H:%M:%S",
                "%Y-%m-%dT%H:%M:%SZ",
                "%Y-%m-%d %H:%M:%S",
                "%Y-%m-%d",
            ]:
                try:
                    return datetime.strptime(stamp, fmt)
                except ValueError:
                    continue
            raise ValueError(f"Unable to parse stamp: {stamp}")
        
        raise ValueError(f"Invalid stamp type: {type(stamp)}")
    
    def validate(
        self,
        data: dict[str, Any],
        series_name: str,
        stamp_key: str = "stamp",
        now: Optional[datetime] = None
    ) -> dict[str, Any]:
        """
        Validate data freshness and return data if fresh.
        
        Args:
            data: Data dictionary containing stamp
            series_name: Name of the data series (for error messages)
            stamp_key: Key in data dictionary containing the stamp
            now: Optional current time (for testing)
            
        Returns:
            Original data dictionary if fresh
            
        Raises:
            StaleDataError: If data is stale
            KeyError: If stamp_key not found in data
        """
        if stamp_key not in data:
            raise KeyError(f"Stamp key '{stamp_key}' not found in data")
        
        stamp = self.parse_stamp(data[stamp_key])
        cutoff = self.get_cutoff_time(now)
        
        if stamp < cutoff:
            raise StaleDataError(series_name, stamp, cutoff)
        
        return data
    
    def validate_batch(
        self,
        records: list[dict[str, Any]],
        series_name: str,
        stamp_key: str = "stamp",
        now: Optional[datetime] = None
    ) -> list[dict[str, Any]]:
        """
        Validate freshness of a batch of records.
        
        Args:
            records: List of data dictionaries
            series_name: Name of the data series
            stamp_key: Key in data dictionary containing the stamp
            now: Optional current time (for testing)
            
        Returns:
            List of validated records
            
        Raises:
            StaleDataError: If any record is stale
        """
        validated = []
        for i, record in enumerate(records):
            try:
                self.validate(record, f"{series_name}[{i}]", stamp_key, now)
                validated.append(record)
            except StaleDataError as e:
                raise StaleDataError(
                    f"{series_name}[{i}]", e.stamp, e.expected
                )
        return validated


# Convenience function for quick validation
def validate_freshness(
    response: dict[str, Any],
    series_name: str,
    tolerance_days: int = 1
) -> dict[str, Any]:
    """
    Quick freshness validation for a single response.
    
    Args:
        response: Response dictionary containing stamp
        series_name: Name of the data series
        tolerance_days: Number of days of staleness allowed
        
    Returns:
        Validated response dictionary
        
    Raises:
        StaleDataError: If data is stale
    """
    guard = CausalFreshnessGuard(tolerance_days)
    return guard.validate(response, series_name)


if __name__ == "__main__":
    # Example usage
    from datetime import datetime
    
    # Test with fresh data
    fresh_data = {
        "stamp": datetime.utcnow().isoformat(),
        "value": 1.23
    }
    
    try:
        result = validate_freshness(fresh_data, "test_series")
        print(f"✓ Fresh data accepted: {result}")
    except StaleDataError as e:
        print(f"✗ Stale data rejected: {e}")
    
    # Test with stale data
    stale_data = {
        "stamp": (datetime.utcnow() - timedelta(days=5)).isoformat(),
        "value": 4.56
    }
    
    try:
        result = validate_freshness(stale_data, "test_series")
        print(f"✓ Fresh data accepted: {result}")
    except StaleDataError as e:
        print(f"✗ Stale data rejected: {e}")
