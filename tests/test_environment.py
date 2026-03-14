#!/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3
"""
Sample test to verify test infrastructure is working correctly.
"""


def test_pytest_is_working():
    """Basic sanity test to ensure pytest is functional."""
    assert True
    assert 1 + 1 == 2
    assert "hello" == "hello"


def test_wx_is_mocked():
    """Test that wxPython is properly mocked."""
    import wx

    # Create a colour to verify the mock works
    colour = wx.Colour(255, 128, 0)
    assert colour.Red() == 255
    assert colour.Green() == 128
    assert colour.Blue() == 0
    assert colour.Alpha() == 255  # default alpha

    # Test with alpha
    colour_with_alpha = wx.Colour(255, 128, 0, 128)
    assert colour_with_alpha.Alpha() == 128


def test_wx_constants_available():
    """Test that wx constants are accessible."""
    import wx

    # Font weights should be available
    assert wx.FONTWEIGHT_NORMAL == 400
    assert wx.FONTWEIGHT_BOLD == 700
    assert wx.FONTWEIGHT_SEMIBOLD == 600

    # Event types
    assert wx.EVT_PAINT is not None
    assert wx.EVT_SIZE is not None
