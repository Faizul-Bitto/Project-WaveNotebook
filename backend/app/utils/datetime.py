from datetime import datetime, timezone


def ensure_timezone_aware(dt):
    """
    Ensure datetime is timezone-aware.
    
    If the datetime is naive (no timezone info), assumes UTC.
    If already timezone-aware, returns as-is.
    """
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt