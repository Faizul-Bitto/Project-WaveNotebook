import threading
import time
from typing import Dict, Set


class ViewTracker:
    """
    Thread-safe in-memory tracker for active product viewers.

    Each viewer is identified by a unique session_id. A view is considered
    active as long as the viewer has "checked in" within the last
    ``expiry_seconds`` window. Stale sessions are cleaned up lazily on every
    access and via a periodic background sweep.
    """

    def __init__(self, expiry_seconds: int = 30):
        self._expiry = expiry_seconds
        self._lock = threading.RLock()
        # product_id -> { session_id: last_seen_timestamp }
        self._sessions: Dict[int, Dict[str, float]] = {}

    def _prune(self, product_id: int, now: float):
        """Remove sessions that haven't checked in within the expiry window."""
        if product_id not in self._sessions:
            return
        active = {
            sid: ts for sid, ts in self._sessions[product_id].items()
            if now - ts < self._expiry
        }
        if active:
            self._sessions[product_id] = active
        else:
            del self._sessions[product_id]

    def register(self, product_id: int, session_id: str) -> int:
        """Register or refresh a viewer session. Returns the current active count."""
        now = time.time()
        with self._lock:
            self._prune(product_id, now)
            if product_id not in self._sessions:
                self._sessions[product_id] = {}
            self._sessions[product_id][session_id] = now
            return len(self._sessions[product_id])

    def get_count(self, product_id: int) -> int:
        """Return the number of currently active viewers for a product."""
        now = time.time()
        with self._lock:
            self._prune(product_id, now)
            return len(self._sessions.get(product_id, {}))

    def unregister(self, product_id: int, session_id: str):
        """Remove a viewer session (called on page unmount / disconnect)."""
        with self._lock:
            if product_id in self._sessions:
                self._sessions[product_id].pop(session_id, None)
                if not self._sessions[product_id]:
                    del self._sessions[product_id]

    def cleanup_all(self):
        """Periodically sweep all products for stale sessions."""
        now = time.time()
        with self._lock:
            for pid in list(self._sessions.keys()):
                self._prune(pid, now)

    def get_active_session_ids(self, product_id: int) -> Set[str]:
        """Return the set of active session IDs for a product (for broadcasting)."""
        now = time.time()
        with self._lock:
            self._prune(product_id, now)
            return set(self._sessions.get(product_id, {}).keys())


view_tracker = ViewTracker()
