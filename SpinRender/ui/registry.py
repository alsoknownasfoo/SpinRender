"""
ControlRegistry — tracks all UI controls registered at creation time.

Controls self-register by traversing the parent chain to find the nearest
ancestor with a `_registry` attribute (typically ControlsSidePanel).
"""


class ControlRegistry:
    def __init__(self):
        self._entries = []

    def add(self, control, section=None):
        self._entries.append({
            'control': control,
            'type':    type(control).__name__,
            'id':      getattr(control, 'style_id', None),
            'section': section,
        })

    def filter(self, **kwargs):
        """Return entries matching all given key=value pairs."""
        return [e for e in self._entries if all(e.get(k) == v for k, v in kwargs.items())]

    def controls(self, **kwargs):
        """Return just the control objects matching all given key=value pairs."""
        return [e['control'] for e in self.filter(**kwargs)]

    def __iter__(self):
        return iter(self._entries)

    def __len__(self):
        return len(self._entries)
