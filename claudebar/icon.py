import math

from PIL import Image, ImageDraw

from .config import THRESHOLD_RED, THRESHOLD_YELLOW
from .enums import Color

_HEIGHT = 20
_GLYPH_SIZE = 20


def format_label(percent, error=False):
    """Formats the status text shown via the tray's native indicator label."""
    if percent is None:
        return "!" if error else "?"
    value = str(min(99, int(percent))) if percent < 100 else "99+"
    return f"{value}%"


def _color_for_percent(percent):
    if percent is None:
        return Color.NEUTRAL
    if percent >= THRESHOLD_RED:
        return Color.RED
    if percent >= THRESHOLD_YELLOW:
        return Color.YELLOW
    return Color.GREEN


def _draw_glyph(draw, cx, cy, radius, color, line_width=2, rays=4):
    """Draws a Claude-inspired spark/asterisk glyph (no logo asset, just primitives)."""
    cap = line_width / 2
    for i in range(rays):
        angle = math.pi * i / rays
        dx, dy = radius * math.cos(angle), radius * math.sin(angle)
        x0, y0 = cx - dx, cy - dy
        x1, y1 = cx + dx, cy + dy
        draw.line([(x0, y0), (x1, y1)], fill=color, width=line_width)
        draw.ellipse([x0 - cap, y0 - cap, x0 + cap, y0 + cap], fill=color)
        draw.ellipse([x1 - cap, y1 - cap, x1 + cap, y1 + cap], fill=color)
    draw.ellipse([cx - cap, cy - cap, cx + cap, cy + cap], fill=color)


def render_app_icon(size=128):
    """Renders the static desktop-entry icon: the glyph alone, at a fixed
    neutral color, with no live status text — used for assets/icon.png."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    _draw_glyph(
        draw,
        cx=size / 2,
        cy=size / 2,
        radius=size / 2 - size * 0.1,
        color=Color.GREEN.value,
        line_width=max(2, round(size * 0.1)),
    )
    return img


def render_icon(percent=None, error=False):
    """Renders a tray icon: a square status glyph colored by threshold.
    The percentage itself is presented separately via the tray's native
    indicator label (see menu.update_icon), since hosts that embed the
    icon into a fixed square slot would otherwise squash a wider bitmap
    and make any text drawn into it illegible."""
    img = Image.new("RGBA", (_GLYPH_SIZE, _HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    glyph_color = (140, 140, 140) if error else _color_for_percent(percent).value
    _draw_glyph(
        draw,
        cx=_GLYPH_SIZE / 2,
        cy=_HEIGHT / 2,
        radius=_GLYPH_SIZE / 2 - 2,
        color=glyph_color,
    )
    return img
