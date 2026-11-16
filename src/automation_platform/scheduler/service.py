"""Continuous service for processing scheduled automation jobs."""

import logging
import math
from threading import Event


logger = logging.getLogger(__name__)


class SchedulerService:

    def __init__(self, engine, poll_interval: float = 1.0):
        if (
            isinstance(poll_interval, bool)
            or not isinstance(poll_interval, (int, float))
            or not math.isfinite(poll_interval)
            or poll_interval <= 0
        ):
            raise ValueError("Poll interval must be a positive finite number.")

        self.engine = engine
        self.poll_interval = float(poll_interval)

    def run_once(self):
        """Process schedules that are currently due."""
        return self.engine.run_due()

    def run_forever(self, stop_event: Event):
        """Continuously process due schedules until shutdown is requested."""
        logger.info("Scheduler service started.")

        while not stop_event.is_set():
            try:
                self.run_once()
            except Exception:
                logger.exception("Scheduler service encountered an error.")

            stop_event.wait(self.poll_interval)

        logger.info("Scheduler service stopped.")
