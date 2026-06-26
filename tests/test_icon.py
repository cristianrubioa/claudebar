from claudebar.icon import format_label, render_icon


def test_format_label_neutral_no_data():
    assert format_label(None, error=False) == "?"


def test_format_label_error():
    assert format_label(None, error=True) == "!"


def test_format_label_percent():
    assert format_label(45, error=False) == "45%"


def test_format_label_caps_at_99():
    assert format_label(99.7, error=False) == "99%"


def test_format_label_over_100():
    assert format_label(100, error=False) == "99+%"


def test_render_icon_is_square():
    img = render_icon(percent=50)
    assert img.width == img.height


def test_render_icon_error_state_is_square():
    img = render_icon(percent=None, error=True)
    assert img.width == img.height
