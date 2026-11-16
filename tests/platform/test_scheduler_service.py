import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from automation_platform.scheduler.service import SchedulerService


class FakeEngine:

    def __init__(self, fail_first=False):
        self.calls = 0
        self.fail_first = fail_first

    def run_due(self):
        self.calls += 1

        if self.fail_first and self.calls == 1:
            raise RuntimeError("Temporary scheduler error.")

        return ["processed"]


class FakeStopEvent:

    def __init__(self, stop_after_waits=1):
        self.waits = []
        self.stop_after_waits = stop_after_waits

    def is_set(self):
        return len(self.waits) >= self.stop_after_waits

    def wait(self, timeout):
        self.waits.append(timeout)


class SchedulerServiceTests(unittest.TestCase):

    def test_run_once_processes_due_jobs(self):
        engine = FakeEngine()
        service = SchedulerService(engine)

        result = service.run_once()

        self.assertEqual(result, ["processed"])
        self.assertEqual(engine.calls, 1)

    def test_run_forever_stops_when_requested(self):
        engine = FakeEngine()
        service = SchedulerService(engine, poll_interval=2)
        stop_event = FakeStopEvent()

        service.run_forever(stop_event)

        self.assertEqual(engine.calls, 1)
        self.assertEqual(stop_event.waits, [2.0])

    def test_run_forever_continues_after_error(self):
        engine = FakeEngine(fail_first=True)
        service = SchedulerService(engine)
        stop_event = FakeStopEvent(stop_after_waits=2)

        service.run_forever(stop_event)

        self.assertEqual(engine.calls, 2)
        self.assertEqual(len(stop_event.waits), 2)

    def test_already_stopped_service_does_not_run(self):
        engine = FakeEngine()
        service = SchedulerService(engine)
        stop_event = FakeStopEvent(stop_after_waits=0)

        service.run_forever(stop_event)

        self.assertEqual(engine.calls, 0)

    def test_invalid_poll_intervals_rejected(self):
        for interval in (0, -1, True, float("inf"), float("nan"), "1"):
            with self.subTest(interval=interval):
                with self.assertRaises(ValueError):
                    SchedulerService(FakeEngine(), interval)


if __name__ == "__main__":
    unittest.main()
