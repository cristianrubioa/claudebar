import math

from PIL import Image, ImageDraw, ImageFont

from .config import THRESHOLD_RED, THRESHOLD_YELLOW
from .enums import Color

_HEIGHT = 20
_GLYPH_SIZE = 20
_GAP = 1
_TEXT_WIDTH = 36
_WIDTH = _GLYPH_SIZE + _GAP + _TEXT_WIDTH
_TEXT_COLOR = (255, 255, 255, 255)
_FONT_SIZE = 13
_FONT_PATHS = (
    "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
)


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


def _load_font(size):
    for path in _FONT_PATHS:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default()


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
    """Renders a tray icon: a status glyph (colored by threshold) next to the
    session percentage (always a fixed standard color), similar to a battery
    indicator's icon+text layout."""
    img = Image.new("RGBA", (_WIDTH, _HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    glyph_color = (140, 140, 140) if error else _color_for_percent(percent).value
    _draw_glyph(
        draw,
        cx=_GLYPH_SIZE / 2,
        cy=_HEIGHT / 2,
        radius=_GLYPH_SIZE / 2 - 2,
        color=glyph_color,
    )

    if percent is None:
        label = "!" if error else "?"
    else:
        value = str(min(99, int(percent))) if percent < 100 else "99+"
        label = f"{value}%"

    font = _load_font(_FONT_SIZE)
    bbox = draw.textbbox((0, 0), label, font=font)
    text_w, text_h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    text_x = _GLYPH_SIZE + _GAP + (_TEXT_WIDTH - text_w) / 2 - bbox[0]
    text_y = (_HEIGHT - text_h) / 2 - bbox[1]
    draw.text((text_x, text_y), label, fill=_TEXT_COLOR, font=font)
    return img
