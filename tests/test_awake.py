from osmbot import awake


def test_other_systems_are_not_kept_awake(monkeypatch):
    monkeypatch.setattr(awake.sys, "platform", "linux")
    assert awake.keep_awake(True) is False


def test_on_the_mac_one_caffeinate_tied_to_the_bot_runs_until_it_stops(monkeypatch):
    started = []

    class Process:
        alive = True

        def __init__(self, args, **kwargs):
            started.append(args)

        def poll(self):
            return None if self.alive else 0

        def terminate(self):
            self.alive = False

    monkeypatch.setattr(awake.sys, "platform", "darwin")
    monkeypatch.setattr(awake.subprocess, "Popen", Process)
    monkeypatch.setattr(awake, "_caffeinate", None)
    assert awake.keep_awake(True) and awake.keep_awake(True)
    assert started == [["caffeinate", "-dims", "-w", str(awake.os.getpid())]]  # only one
    process = awake._caffeinate
    assert awake.keep_awake(False) and not process.alive and awake._caffeinate is None


def test_on_windows_the_screen_and_the_system_are_kept_on_and_then_released(monkeypatch):
    calls = []

    class Kernel:
        def SetThreadExecutionState(self, flags):
            calls.append(flags)
            return 1

    class Windll:
        kernel32 = Kernel()

    import ctypes
    monkeypatch.setattr(awake.sys, "platform", "win32")
    monkeypatch.setattr(ctypes, "windll", Windll(), raising=False)
    assert awake.keep_awake(True) and awake.keep_awake(False)
    assert calls == [0x80000003, 0x80000000]
