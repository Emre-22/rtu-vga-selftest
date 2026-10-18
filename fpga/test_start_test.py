import importlib.util
from pathlib import Path
import unittest
from types import SimpleNamespace
from unittest.mock import Mock

spec = importlib.util.spec_from_file_location("start_test", Path(__file__).with_name("start_test.py"))
startup = importlib.util.module_from_spec(spec)
spec.loader.exec_module(startup)


class StartupTests(unittest.TestCase):
    def fixture(self):
        events = []
        project = SimpleNamespace(enable=Mock(side_effect=lambda: events.append("enable")))
        tt = SimpleNamespace(pins=SimpleNamespace(**{
            "ui_in%d" % n: SimpleNamespace(gpio_num=g) for n,g in ((0,17),(3,20),(4,21))}),
            shuttle=SimpleNamespace(**{startup.PROJECT: project}),
            reset_project=Mock(side_effect=lambda level: events.append(("reset", level))),
            clock_project_PWM=Mock(side_effect=lambda freq: events.append(("clock", freq)) or object()),
            auto_clocking_freq=25250000)
        clock = SimpleNamespace(sleep_ms=Mock(side_effect=lambda ms: events.append(("sleep", ms))))
        return tt, clock, events

    def test_order_actual_clock_and_manual_inputs(self):
        tt, clock, events = self.fixture()
        actual = startup.start(tt=tt, manual_mode="manual", clock=clock)
        self.assertEqual(actual, 25250000)
        self.assertEqual(tt.mode, "manual")
        self.assertEqual(events, [("reset",True), "enable", ("reset",True),
                                  ("clock",25200000), ("sleep",1), ("reset",False)])

    def test_wrong_mapping_never_touches_pins(self):
        tt, clock, _ = self.fixture()
        tt.pins.ui_in3.gpio_num = 15
        with self.assertRaises(RuntimeError):
            startup.start(tt=tt, manual_mode="manual", clock=clock)
        tt.reset_project.assert_not_called()
        tt.clock_project_PWM.assert_not_called()

    def test_bad_clock_and_loader_failure_hold_reset(self):
        for failure in ("clock", "loader", "pwm"):
            tt, clock, _ = self.fixture()
            if failure == "clock":
                tt.auto_clocking_freq = 25000000
            elif failure == "pwm":
                tt.clock_project_PWM.side_effect = None
                tt.clock_project_PWM.return_value = None
            else:
                getattr(tt.shuttle, startup.PROJECT).enable.side_effect = RuntimeError("load failed")
            with self.assertRaises(RuntimeError):
                startup.start(tt=tt, manual_mode="manual", clock=clock)
            self.assertTrue(tt.reset_project.call_args.args[0])
            self.assertNotIn(False, [c.args[0] for c in tt.reset_project.call_args_list])
            clock.sleep_ms.assert_not_called()

    def test_invalid_project_rejected_without_sdk_or_files(self):
        with self.assertRaises(ValueError):
            startup.start(project="../another-project")


if __name__ == "__main__":
    unittest.main()
