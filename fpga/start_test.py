"""Temporary ETR FPGA diagnostic selection. No startup or filesystem changes.

mpremote connect COM3 run fpga/start_test.py
Or import start_test; start_test.start(project='content_addressed_project_name').
The configured hardware PWM keeps running after this function returns.
"""

PROJECT = "tt_um_emre_vga_selftest"
CLOCK_HZ = 25200000


def start(project=PROJECT, tt=None, manual_mode=None, clock=None):
    if not project.startswith(PROJECT) or not all(c.isalnum() or c == "_" for c in project):
        raise ValueError("Expected a selftest project name")
    if tt is None:
        from ttboard.boot.demoboard_detect import DemoboardDetect
        from ttboard.demoboard import DemoBoard
        DemoboardDetect.probe()
        tt = DemoBoard.get()
    if manual_mode is None:
        from ttboard.mode import RPMode
        manual_mode = RPMode.ASIC_MANUAL_INPUTS
    if clock is None:
        import time as clock
    for name, expected in (("ui_in0", 17), ("ui_in3", 20), ("ui_in4", 21)):
        if getattr(tt.pins, name).gpio_num != expected:
            raise RuntimeError("ETR GPIO mapping required; refusing to touch pins")
    tt.reset_project(True)
    try:
        tt.mode = manual_mode
        getattr(tt.shuttle, project).enable()
        # Loader/config hooks may alter reset or clock; explicitly override both.
        tt.reset_project(True)
        pwm = tt.clock_project_PWM(CLOCK_HZ)
        actual = tt.auto_clocking_freq
        if pwm is None or abs(actual - CLOCK_HZ) > CLOCK_HZ // 200:
            raise RuntimeError("Clock outside +/-0.5%%: %s" % actual)
        clock.sleep_ms(1)
        tt.reset_project(False)
    except Exception:
        tt.reset_project(True)
        raise
    print("VGA SELFTEST selected=%s actual_clock=%s Hz; hardware PWM remains running" %
          (project, actual))
    return actual


if __name__ == "__main__":
    start()
