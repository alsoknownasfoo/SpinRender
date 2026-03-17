"""Render settings dataclass with validation."""
from dataclasses import dataclass, asdict


@dataclass
class RenderSettings:
    """Render settings dataclass."""

    board_tilt: float = 0.0
    board_roll: float = 0.0
    spin_tilt: float = 0.0
    spin_heading: float = 0.0
    period: float = 10.0
    direction: str = 'ccw'
    lighting: str = 'studio'
    bg_color: str = '#000000'
    render_mode: str = 'both'
    format: str = 'mp4'
    resolution: str = '1920x1080'
    preset: str = 'custom'
    logging_level: str = 'simple'
    easing: str = 'linear'
    output_auto: bool = True
    output_path: str = ''
    cli_overrides: str = ''

    def __post_init__(self):
        """Validate settings after initialization."""
        if not -90 <= self.board_tilt <= 90:
            raise ValueError(f"board_tilt must be between -90 and 90 degrees, got {self.board_tilt}")
        if not -180 <= self.board_roll <= 180:
            raise ValueError(f"board_roll must be between -180 and 180 degrees, got {self.board_roll}")
        if not -90 <= self.spin_tilt <= 90:
            raise ValueError(f"spin_tilt must be between -90 and 90 degrees, got {self.spin_tilt}")
        if not -180 <= self.spin_heading <= 180:
            raise ValueError(f"spin_heading must be between -180 and 180 degrees, got {self.spin_heading}")
        if self.period <= 0:
            raise ValueError(f"period must be positive, got {self.period}")

    @classmethod
    def from_dict(cls, data: dict):
        """Create RenderSettings from dictionary."""
        return cls(**data)

    def to_dict(self) -> dict:
        """Convert RenderSettings to dictionary."""
        return asdict(self)
