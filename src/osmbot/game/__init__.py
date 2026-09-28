"""Real contact with the OSM game (login, reading/writing account state).

Everything here talks to the actual game. Only used with the owner's explicit,
per-session OK (CLAUDE.md rule 5). Pure decision logic lives in
``osmbot.theory`` and ``osmbot.training`` instead, and stays testable offline.
"""
