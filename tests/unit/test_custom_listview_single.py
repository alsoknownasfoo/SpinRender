#!/usr/bin/env python3
"""
Test that CustomListItem and CustomListView are defined exactly once.
This verifies Phase 2 deduplication is complete.
"""
import sys
from pathlib import Path
import inspect

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from SpinRender.ui import custom_controls


class TestCustomListViewSingleImplementation:
    """Ensure exactly ONE CustomListItem and CustomListView exist."""

    def test_only_one_customlistitem_definition(self):
        """CustomListItem class must be defined exactly once."""
        # Check source code directly
        source_file = inspect.getsourcefile(custom_controls)
        with open(source_file, 'r') as f:
            content = f.read()
        count = content.count('class CustomListItem(wx.Panel):')
        assert count == 1, f"Expected 1 CustomListItem definition, found {count}"

    def test_only_one_customlistview_definition(self):
        """CustomListView class must be defined exactly once."""
        source_file = inspect.getsourcefile(custom_controls)
        with open(source_file, 'r') as f:
            content = f.read()
        count = content.count('class CustomListView(scrolled.ScrolledPanel):')
        assert count == 1, f"Expected 1 CustomListView definition, found {count}"

    def test_duplicate_classes_removed_from_source(self):
        """No duplicate class definitions in source file."""
        source_file = inspect.getsourcefile(custom_controls)
        with open(source_file, 'r') as f:
            content = f.read()

        # Count class definitions
        item_count = content.count('class CustomListItem(wx.Panel):')
        view_count = content.count('class CustomListView(scrolled.ScrolledPanel):')

        assert item_count == 1, f"CustomListItem appears {item_count} times in source (expected 1)"
        assert view_count == 1, f"CustomListView appears {view_count} times in source (expected 1)"
