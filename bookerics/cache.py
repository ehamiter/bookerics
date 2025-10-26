from typing import Optional
import threading


class BookmarkCache:
    """Simple in-memory cache for bookmark counts and frequently accessed data."""

    def __init__(self):
        self._lock = threading.Lock()
        self._total_count: Optional[int] = None
        self._untagged_count: Optional[int] = None

    def get_total_count(self) -> Optional[int]:
        """Get cached total bookmark count."""
        with self._lock:
            return self._total_count

    def set_total_count(self, count: int) -> None:
        """Set cached total bookmark count."""
        with self._lock:
            self._total_count = count

    def get_untagged_count(self) -> Optional[int]:
        """Get cached untagged bookmark count."""
        with self._lock:
            return self._untagged_count

    def set_untagged_count(self, count: int) -> None:
        """Set cached untagged bookmark count."""
        with self._lock:
            self._untagged_count = count

    def invalidate(self) -> None:
        """Invalidate all cached values."""
        with self._lock:
            self._total_count = None
            self._untagged_count = None


cache = BookmarkCache()
