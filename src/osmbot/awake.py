"""Keep the computer awake while the bot works (owner, 2026-10-14).

On 2026-10-14 the office PC went to sleep for half an hour (Windows "Modern Standby", network off) in the middle
of a 2 h training event. On such PCs the system sleeps once the screen turns off, whatever a program asks, so the
bot keeps the screen on too (the owner's choice). Locking the PC still works; closing the lid still sleeps it.
On the Mac (2026-10-17) the same is asked of macOS with ``caffeinate -dims``, tied to the bot's process (``-w``) so
it never outlives it; closing the lid still sleeps the Mac.
"""
from __future__ import annotations

import os
import subprocess
import sys

ES_CONTINUOUS, ES_SYSTEM_REQUIRED, ES_DISPLAY_REQUIRED = 0x80000000, 0x00000001, 0x00000002

_caffeinate: subprocess.Popen | None = None


def keep_awake(on: bool) -> bool:
    """Ask the system not to sleep nor turn the screen off (``on``), or to go back to normal. On Windows it holds
    while the calling thread lives, so the bot's loop calls it at its start and again at its end; on the Mac it
    holds while a ``caffeinate`` runs. True if the system took it."""
    if sys.platform == "darwin":
        return _mac(on)
    if sys.platform != "win32":
        return False
    try:
        import ctypes

        flags = ES_CONTINUOUS | (ES_SYSTEM_REQUIRED | ES_DISPLAY_REQUIRED if on else 0)
        return bool(ctypes.windll.kernel32.SetThreadExecutionState(flags))
    except (AttributeError, OSError):
        return False


def _mac(on: bool) -> bool:
    global _caffeinate
    if _caffeinate is not None and _caffeinate.poll() is None:
        if on:
            return True
        _caffeinate.terminate()
    _caffeinate = None
    if not on:
        return True
    try:  # -d screen, -i idle, -m disk, -s system (on mains power); -w: ends with the bot
        _caffeinate = subprocess.Popen(["caffeinate", "-dims", "-w", str(os.getpid())],
                                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except OSError:
        return False
    return True
