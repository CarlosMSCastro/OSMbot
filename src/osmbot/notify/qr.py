"""The QR code of the bot's link (D-110): the matrix of dark squares, with the quiet border the phones need. Pure
(``segno`` is a small pure-Python library with no dependencies); the window paints it."""
from __future__ import annotations

BORDER = 4  # modules of white around the code (the QR standard's quiet zone)


def matrix(text: str, border: int = BORDER) -> list[list[bool]]:
    """Rows of booleans, True = dark, including the border."""
    import segno

    rows = [[bool(cell) for cell in row] for row in segno.make(text, error="m").matrix]
    width = len(rows[0]) + 2 * border
    blank = [False] * width
    return [blank] * border + [[False] * border + row + [False] * border for row in rows] + [blank] * border
