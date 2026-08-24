from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Any


@dataclass(frozen=True, slots=True)
class Timebase:
    fps_num: int
    fps_den: int = 1

    def __post_init__(self) -> None:
        for name, value in (("fps_num", self.fps_num), ("fps_den", self.fps_den)):
            if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                raise ValueError(f"{name} must be a positive integer")
        fps = Fraction(self.fps_num, self.fps_den)
        if fps < 1 or fps > 240:
            raise ValueError("timebase FPS must be in [1,240]")

    @property
    def fps(self) -> Fraction:
        return Fraction(self.fps_num, self.fps_den)

    def seconds_for_frame(self, frame: int) -> Fraction:
        if isinstance(frame, bool) or not isinstance(frame, int) or frame < 0:
            raise ValueError("frame must be a non-negative integer")
        return Fraction(frame * self.fps_den, self.fps_num)

    def frame_for_seconds(self, seconds_num: int, seconds_den: int = 1) -> int:
        if isinstance(seconds_num, bool) or not isinstance(seconds_num, int) or seconds_num < 0:
            raise ValueError("seconds_num must be a non-negative integer")
        if isinstance(seconds_den, bool) or not isinstance(seconds_den, int) or seconds_den <= 0:
            raise ValueError("seconds_den must be a positive integer")
        exact = Fraction(seconds_num, seconds_den) * self.fps
        if exact.denominator != 1:
            raise ValueError("seconds do not land on an exact frame boundary")
        return exact.numerator

    def canonical(self) -> dict[str, int]:
        return {"fps_num": self.fps_num, "fps_den": self.fps_den}


@dataclass(frozen=True, slots=True)
class FrameTime:
    frame: int
    timebase: Timebase

    def __post_init__(self) -> None:
        if isinstance(self.frame, bool) or not isinstance(self.frame, int) or self.frame < 0:
            raise ValueError("frame must be a non-negative integer")
        if not isinstance(self.timebase, Timebase):
            raise TypeError("timebase must be Timebase")

    @property
    def seconds(self) -> Fraction:
        return self.timebase.seconds_for_frame(self.frame)

    def canonical(self) -> dict[str, Any]:
        return {"frame": self.frame, "timebase": self.timebase.canonical()}
