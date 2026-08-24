from __future__ import annotations

import hashlib

from .contracts import AudioCueDefinition, CuePlayback, CueVariant


def select_variant(cue: AudioCueDefinition, *, seed: str, occurrence: int = 0) -> CueVariant:
    if not isinstance(seed, str) or not seed or len(seed) > 256 or any(ord(ch) < 32 for ch in seed):
        raise ValueError("seed must be bounded printable text")
    if isinstance(occurrence, bool) or not isinstance(occurrence, int) or occurrence < 0 or occurrence > 2**31 - 1:
        raise ValueError("occurrence must be a bounded non-negative integer")
    if cue.allow_runtime_nondeterminism:
        raise ValueError("deterministic selector cannot be used for a nondeterministic runtime cue")
    material = f"{cue.digest}\0{seed}\0{occurrence}".encode("utf-8")
    value = int.from_bytes(hashlib.sha256(material).digest()[:8], "big")
    if cue.playback in {CuePlayback.WEIGHTED, CuePlayback.ONE_SHOT, CuePlayback.LOOP}:
        total = sum(item.weight for item in cue.variants)
        target = value % total
        running = 0
        for variant in cue.variants:
            running += variant.weight
            if target < running:
                return variant
    index = value % len(cue.variants)
    return cue.variants[index]


def playlist_order(cue: AudioCueDefinition, *, seed: str) -> tuple[CueVariant, ...]:
    if cue.playback != CuePlayback.PLAYLIST:
        raise ValueError("playlist_order requires playlist playback")
    if cue.allow_runtime_nondeterminism:
        raise ValueError("deterministic playlist cannot be used for nondeterministic runtime cue")
    decorated = []
    for index, variant in enumerate(cue.variants):
        digest = hashlib.sha256(f"{cue.digest}\0{seed}\0{index}".encode("utf-8")).digest()
        decorated.append((digest, variant))
    decorated.sort(key=lambda item: item[0])
    return tuple(item[1] for item in decorated)
