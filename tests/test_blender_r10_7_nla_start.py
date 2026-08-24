from __future__ import annotations

from kodepoia.blender3d.animation_bootstrap import ANIMATION_BOOTSTRAP_SOURCE


def test_r10_7_nla_creation_start_uses_integer_api_contract_and_preserves_exact_frame() -> None:
    source = ANIMATION_BOOTSTRAP_SOURCE
    assert 'nla_start = float(clip["frame_start"])' in source
    assert "nla_creation_start = int(math.floor(nla_start))" in source
    assert 'track.strips.new("kdp_strip_" + str(clip["clip_id"]), nla_creation_start, action)' in source
    assert "strip.frame_start = nla_start" in source
    assert 'track.strips.new("kdp_strip_" + str(clip["clip_id"]), float(clip["frame_start"]), action)' not in source
