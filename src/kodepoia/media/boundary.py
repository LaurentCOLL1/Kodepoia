from __future__ import annotations

from collections.abc import Iterable, Mapping
from pathlib import Path

from .contracts import MediaRuntimeKind

_ALLOWED_NAMES: dict[MediaRuntimeKind, frozenset[str]] = {
    MediaRuntimeKind.FFPROBE: frozenset({"ffprobe", "ffprobe.exe"}),
    MediaRuntimeKind.FFMPEG: frozenset({"ffmpeg", "ffmpeg.exe"}),
    MediaRuntimeKind.TTS: frozenset({"piper", "piper.exe", "python", "python.exe"}),
    MediaRuntimeKind.GODOT: frozenset({"godot", "godot.exe", "godot4", "godot4.exe"}),
}
_ALLOWED_ENV_KEYS = frozenset({"KODEPOIA_RUN_ID", "TEMP", "TMP"})
_FORBIDDEN_ENV_KEYS = frozenset({"PYTHONPATH", "PYTHONHOME", "LD_PRELOAD", "DYLD_INSERT_LIBRARIES", "FFREPORT", "AV_LOG_FORCE_NOCOLOR"})


class MediaBoundaryError(ValueError):
    pass


def _within(path: Path, root: Path) -> bool:
    return path == root or root in path.parents


class MediaRuntimeBoundary:
    """Finite R11 runtime/path boundary. It validates and compiles fixed argv; it never launches a process."""

    def __init__(self, *, allowed_roots: Iterable[Path], staging_root: Path) -> None:
        roots = tuple(Path(p).resolve(strict=False) for p in allowed_roots)
        if not roots:
            raise ValueError("at least one runtime root is required")
        self.allowed_roots = roots
        self.staging_root = Path(staging_root).resolve(strict=False)

    def validate_executable(self, kind: MediaRuntimeKind, candidate: Path) -> Path:
        try:
            resolved = Path(candidate).resolve(strict=True)
        except OSError as exc:
            raise MediaBoundaryError(f"runtime executable is unavailable: {candidate}") from exc
        if not resolved.is_file():
            raise MediaBoundaryError("runtime executable must be a regular file")
        if resolved.name.lower() not in _ALLOWED_NAMES[kind]:
            raise MediaBoundaryError(f"unexpected executable for {kind.value}: {resolved.name}")
        if not any(_within(resolved, root) for root in self.allowed_roots):
            raise MediaBoundaryError("runtime executable escapes configured roots")
        return resolved

    def validate_input(self, path: Path, *, root: Path, suffixes: frozenset[str]) -> Path:
        root = Path(root).resolve(strict=False)
        try:
            resolved = Path(path).resolve(strict=True)
        except OSError as exc:
            raise MediaBoundaryError("media input is unavailable") from exc
        if not resolved.is_file() or not _within(resolved, root):
            raise MediaBoundaryError("media input escapes governed root")
        if suffixes and resolved.suffix.lower() not in suffixes:
            raise MediaBoundaryError("media input suffix is not allowlisted")
        return resolved

    def validate_output(self, path: Path, *, suffixes: frozenset[str]) -> Path:
        resolved = Path(path).resolve(strict=False)
        if not _within(resolved, self.staging_root):
            raise MediaBoundaryError("media output escapes staging root")
        if suffixes and resolved.suffix.lower() not in suffixes:
            raise MediaBoundaryError("media output suffix is not allowlisted")
        return resolved

    def build_ffprobe_argv(self, executable: Path, input_path: Path, *, input_root: Path) -> tuple[str, ...]:
        exe = self.validate_executable(MediaRuntimeKind.FFPROBE, executable)
        src = self.validate_input(input_path, root=input_root, suffixes=frozenset({".wav", ".ogg", ".mp3", ".flac"}))
        return (str(exe), "-v", "error", "-show_format", "-show_streams", "-of", "json", "--", str(src))

    def build_ffmpeg_pcm_argv(self, executable: Path, input_path: Path, output_path: Path, *, input_root: Path, sample_rate_hz: int, channels: int) -> tuple[str, ...]:
        if sample_rate_hz not in {16000, 22050, 24000, 44100, 48000}:
            raise MediaBoundaryError("sample rate is not allowlisted")
        if channels not in {1, 2}:
            raise MediaBoundaryError("channels must be 1 or 2")
        exe = self.validate_executable(MediaRuntimeKind.FFMPEG, executable)
        src = self.validate_input(input_path, root=input_root, suffixes=frozenset({".wav", ".ogg", ".mp3", ".flac"}))
        dst = self.validate_output(output_path, suffixes=frozenset({".wav"}))
        return (str(exe), "-nostdin", "-hide_banner", "-loglevel", "error", "-y", "-i", str(src), "-vn", "-sn", "-dn", "-ac", str(channels), "-ar", str(sample_rate_hz), "-c:a", "pcm_s16le", str(dst))


def validate_environment_overrides(overrides: Mapping[str, str] | None) -> dict[str, str]:
    if not overrides:
        return {}
    clean: dict[str, str] = {}
    for key, value in overrides.items():
        normalized = str(key).upper()
        if normalized in _FORBIDDEN_ENV_KEYS or normalized not in _ALLOWED_ENV_KEYS:
            raise MediaBoundaryError(f"environment override is not allowlisted: {key}")
        if "\x00" in str(value):
            raise MediaBoundaryError("environment value contains NUL")
        clean[normalized] = str(value)
    return clean
