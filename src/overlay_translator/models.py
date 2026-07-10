from dataclasses import dataclass


@dataclass(frozen=True)
class Rect:
    """A screen region in pixels: top-left (x, y) with width and height."""

    x: int
    y: int
    width: int
    height: int

    @property
    def area(self) -> int:
        return self.width * self.height
