"""Keep the computer awake while the bot works (owner, 2026-10-14).

On 2026-10-14 the office PC went to sleep for half an hour (Windows "Modern Standby", network off) in the middle
of a 2 h training event. On such PCs the system sleeps once the screen turns off, whatever a program asks, so the
bot keeps the screen on too (the owner's choice). Locking the PC still works; closing the lid still sleeps it.
Only Windows for now: the Mac's ``caffeinate`` is to be done on the Mac (WORKLOG).
"""
from __future__ import annotations

import sys

ES_CONTINUOUS, ES_SYSTEM_REQUIRED, ES_DISPLAY_REQUIRED = 0x80000000, 0x00000001, 0x00000002


def keep_awake(on: bool) -> bool:
    """Ask Windows not to sleep nor turn the screen off (``on``), or to go back to normal. It holds while the
    calling thread lives, so the bot's loop calls it at its start and again at its end. True if Windows took it."""
    if sys.platform != "win32":
        return False
    try:
        import ctypes

        flags = ES_CONTINUOUS | (ES_SYSTEM_REQUIRED | ES_DISPLAY_REQUIRED if on else 0)
        return bool(ctypes.windll.kernel32.SetThreadExecutionState(flags))
    except (AttributeError, OSError):
        return False
