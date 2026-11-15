import logging
import time
from collections import defaultdict
from threading import Lock


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

logger = logging.getLogger("anomaly_detector")


class TTLCache:
    def __init__(self, ttl_seconds: int = 30):
        self.ttl_seconds = ttl_seconds
        self._data = {}
        self._lock = Lock()

    def get(self, key: str):
        with self._lock:
            item = self._data.get(key)
            if item is None:
                return None

            expires_at, value = item

            if time.time() >= expires_at:
                self._data.pop(key, None)
                return None

            return value

    def set(self, key: str, value):
        with self._lock:
            self._data[key] = (
                time.time() + self.ttl_seconds,
                value,
            )

    def clear(self):
        with self._lock:
            self._data.clear()


class Metrics:
    def __init__(self):
        self._lock = Lock()
        self.requests_total = 0
        self.errors_total = 0
        self.total_latency_seconds = 0.0
        self.by_status = defaultdict(int)
        self.by_method = defaultdict(int)

    def record(
        self,
        method: str,
        status_code: int,
        latency_seconds: float,
    ):
        with self._lock:
            self.requests_total += 1
            self.total_latency_seconds += latency_seconds
            self.by_status[str(status_code)] += 1
            self.by_method[method] += 1

            if status_code >= 400:
                self.errors_total += 1

    def snapshot(self):
        with self._lock:
            avg_latency = (
                self.total_latency_seconds / self.requests_total
                if self.requests_total
                else 0.0
            )

            return {
                "requests_total": self.requests_total,
                "errors_total": self.errors_total,
                "average_latency_seconds": round(
                    avg_latency,
                    6,
                ),
                "requests_by_status": dict(self.by_status),
                "requests_by_method": dict(self.by_method),
            }


metrics = Metrics()
dashboard_cache = TTLCache(ttl_seconds=30)
