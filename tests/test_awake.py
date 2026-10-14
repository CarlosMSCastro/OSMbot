from osmbot import awake


def test_the_pc_is_kept_awake_only_on_windows(monkeypatch):
    monkeypatch.setattr(awake.sys, "platform", "darwin")
    assert awake.keep_awake(True) is False  # the Mac's caffeinate is still to do


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
