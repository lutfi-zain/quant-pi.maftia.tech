"""
Unit tests for CausalFreshnessGuard module.
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta

import pytest

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from causal_freshness_guard import (
    CausalFreshnessGuard,
    StaleDataError,
    validate_freshness,
)


class TestStaleDataError:
    """Tests for StaleDataError exception."""
    
    def test_error_message(self):
        """Error message contains series name and timestamps."""
        stamp = datetime(2026, 7, 1)
        expected = datetime(2026, 7, 7)
        error = StaleDataError("test_series", stamp, expected)
        
        assert "test_series" in str(error)
        assert "2026-07-01" in str(error)
        assert "2026-07-07" in str(error)
    
    def test_error_attributes(self):
        """Error has correct attributes."""
        stamp = datetime(2026, 7, 1)
        expected = datetime(2026, 7, 7)
        error = StaleDataError("test_series", stamp, expected)
        
        assert error.series_name == "test_series"
        assert error.stamp == stamp
        assert error.expected == expected


class TestCausalFreshnessGuard:
    """Tests for CausalFreshnessGuard class."""
    
    def test_init_default(self):
        """Default tolerance is 1 day."""
        guard = CausalFreshnessGuard()
        assert guard.tolerance_days == 1
    
    def test_init_custom_tolerance(self):
        """Custom tolerance is stored."""
        guard = CausalFreshnessGuard(tolerance_days=3)
        assert guard.tolerance_days == 3
    
    def test_get_cutoff_time(self):
        """Cutoff time is now minus tolerance."""
        guard = CausalFreshnessGuard(tolerance_days=2)
        now = datetime(2026, 7, 8, 12, 0, 0)
        
        cutoff = guard.get_cutoff_time(now)
        
        assert cutoff == datetime(2026, 7, 6, 12, 0, 0)
    
    def test_parse_stamp_string_iso(self):
        """Parse ISO format string stamp."""
        guard = CausalFreshnessGuard()
        stamp_str = "2026-07-08T12:00:00"
        
        result = guard.parse_stamp(stamp_str)
        
        assert result == datetime(2026, 7, 8, 12, 0, 0)
    
    def test_parse_stamp_string_date(self):
        """Parse date-only string stamp."""
        guard = CausalFreshnessGuard()
        stamp_str = "2026-07-08"
        
        result = guard.parse_stamp(stamp_str)
        
        assert result == datetime(2026, 7, 8, 0, 0, 0)
    
    def test_parse_stamp_datetime(self):
        """Pass through datetime object."""
        guard = CausalFreshnessGuard()
        stamp_dt = datetime(2026, 7, 8, 12, 0, 0)
        
        result = guard.parse_stamp(stamp_dt)
        
        assert result == stamp_dt
    
    def test_parse_stamp_invalid(self):
        """Raise ValueError for invalid stamp."""
        guard = CausalFreshnessGuard()
        
        with pytest.raises(ValueError):
            guard.parse_stamp("invalid-date-format")
    
    def test_parse_stamp_wrong_type(self):
        """Raise ValueError for wrong type."""
        guard = CausalFreshnessGuard()
        
        with pytest.raises(ValueError):
            guard.parse_stamp(12345)
    
    def test_validate_fresh_data(self):
        """Accept fresh data."""
        guard = CausalFreshnessGuard()
        now = datetime(2026, 7, 8, 12, 0, 0)
        data = {
            "stamp": "2026-07-08T10:00:00",
            "value": 1.23
        }
        
        result = guard.validate(data, "test_series", now=now)
        
        assert result == data
    
    def test_validate_stale_data(self):
        """Reject stale data."""
        guard = CausalFreshnessGuard()
        now = datetime(2026, 7, 8, 12, 0, 0)
        data = {
            "stamp": "2026-07-05T10:00:00",  # 3 days ago
            "value": 4.56
        }
        
        with pytest.raises(StaleDataError) as exc_info:
            guard.validate(data, "test_series", now=now)
        
        assert exc_info.value.series_name == "test_series"
    
    def test_validate_missing_stamp(self):
        """Raise KeyError for missing stamp."""
        guard = CausalFreshnessGuard()
        data = {"value": 1.23}
        
        with pytest.raises(KeyError):
            guard.validate(data, "test_series")
    
    def test_validate_custom_stamp_key(self):
        """Use custom stamp key."""
        guard = CausalFreshnessGuard()
        now = datetime(2026, 7, 8, 12, 0, 0)
        data = {
            "timestamp": "2026-07-08T10:00:00",
            "value": 1.23
        }
        
        result = guard.validate(data, "test_series", stamp_key="timestamp", now=now)
        
        assert result == data
    
    def test_validate_batch_all_fresh(self):
        """Accept batch of fresh records."""
        guard = CausalFreshnessGuard()
        now = datetime(2026, 7, 8, 12, 0, 0)
        records = [
            {"stamp": "2026-07-08T10:00:00", "value": 1},
            {"stamp": "2026-07-08T11:00:00", "value": 2},
        ]
        
        result = guard.validate_batch(records, "test_series", now=now)
        
        assert len(result) == 2
    
    def test_validate_batch_one_stale(self):
        """Reject batch if any record is stale."""
        guard = CausalFreshnessGuard()
        now = datetime(2026, 7, 8, 12, 0, 0)
        records = [
            {"stamp": "2026-07-08T10:00:00", "value": 1},
            {"stamp": "2026-07-05T10:00:00", "value": 2},  # Stale
        ]
        
        with pytest.raises(StaleDataError):
            guard.validate_batch(records, "test_series", now=now)


class TestValidateFreshnessConvenience:
    """Tests for validate_freshness convenience function."""
    
    def test_fresh_data_accepted(self):
        """Accept fresh data."""
        now = datetime(2026, 7, 8, 12, 0, 0)
        data = {
            "stamp": "2026-07-08T10:00:00",
            "value": 1.23
        }
        
        # Use the guard directly with now parameter
        guard = CausalFreshnessGuard()
        result = guard.validate(data, "test_series", now=now)
        assert result == data
    
    def test_stale_data_rejected(self):
        """Reject stale data."""
        now = datetime(2026, 7, 8, 12, 0, 0)
        data = {
            "stamp": "2026-07-05T10:00:00",
            "value": 4.56
        }
        
        guard = CausalFreshnessGuard()
        with pytest.raises(StaleDataError):
            guard.validate(data, "test_series", now=now)
