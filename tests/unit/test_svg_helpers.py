#!/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3
"""Unit tests for SVG helper functions."""

import pytest


@pytest.fixture(scope="module")
def helpers():
    """Import helpers after conftest has installed wx mock."""
    import SpinRender.ui.helpers as _helpers
    return _helpers


class TestReplaceSvgFill:
    """Tests for SVG markup fill replacement."""

    def test_replaces_non_none_fill_attributes(self, helpers):
        svg_markup = (
            '<svg fill="none">'
            '<path fill="#333333"/>'
            '<path fill="#abcdef"/>'
            '</svg>'
        )

        result = helpers.replace_svg_fill(svg_markup, "#F5F5F5")

        assert 'fill="none"' in result
        assert result.count('fill="#F5F5F5"') == 2
        assert '#333333' not in result
        assert '#abcdef' not in result


class TestLoadSvgMarkup:
    """Tests for runtime-probed in-memory SVG loading."""

    def test_uses_create_from_bytes_when_available(self, helpers, monkeypatch):
        expected = object()

        class SvgFactory:
            @staticmethod
            def CreateFromBytes(data):
                assert data == b"<svg/>"
                return expected

        monkeypatch.setattr(helpers.wx.svg, "SVGimage", SvgFactory)

        result = helpers.load_svg_markup("<svg/>")

        assert result is expected

    def test_falls_back_to_constructor_when_factory_missing(self, helpers, monkeypatch):
        class SvgCtor:
            def __new__(cls, data):
                assert data == b"<svg/>"
                return "constructed"

        monkeypatch.setattr(helpers.wx.svg, "SVGimage", SvgCtor)

        result = helpers.load_svg_markup("<svg/>")

        assert result == "constructed"

    def test_returns_none_when_all_loaders_fail(self, helpers, monkeypatch):
        """Should return None when no factory and constructor both raise."""

        class BrokenSvg:
            def __new__(cls, data):
                raise RuntimeError("SVG parsing failed")

        monkeypatch.setattr(helpers.wx.svg, "SVGimage", BrokenSvg)

        result = helpers.load_svg_markup("<invalid/>")

        assert result is None