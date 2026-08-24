from kodepoia.media.audio.qa import AudioQAProfile, evaluate_wav
from kodepoia.media.audio.wav import WavFacts
from kodepoia.media.contracts import MediaState
from kodepoia.media.tts.runtime import _tts_clipping_budget


def _facts(clipped_samples: int) -> WavFacts:
    return WavFacts(
        channels=1,
        sample_rate_hz=22050,
        sample_width_bytes=2,
        frame_count=106496,
        duration_seconds=4.829750566893424,
        pcm_sha256_source_bytes=212992,
        peak=0.999969482421875,
        clipped_samples=clipped_samples,
        silent_fraction=0.12798602764423078,
        first_sample=-3,
        last_sample=10,
    )


def test_tts_profile_accepts_one_isolated_full_scale_sample() -> None:
    facts = _facts(1)
    budget = _tts_clipping_budget(facts.frame_count, facts.channels)
    assert budget == 1
    report = evaluate_wav(
        "a" * 64,
        facts,
        AudioQAProfile(profile_id="tts.local.v2", max_duration_seconds=30.0, max_clipped_samples=budget),
    )
    assert report.state is MediaState.PASS
    assert report.blockers == ()


def test_tts_profile_still_blocks_repeated_full_scale_samples() -> None:
    facts = _facts(2)
    budget = _tts_clipping_budget(facts.frame_count, facts.channels)
    report = evaluate_wav(
        "b" * 64,
        facts,
        AudioQAProfile(profile_id="tts.local.v2", max_duration_seconds=30.0, max_clipped_samples=budget),
    )
    assert report.state is MediaState.BLOCKED
    assert "clipping" in report.blockers


def test_tts_clipping_budget_is_tiny_and_capped() -> None:
    assert _tts_clipping_budget(1, 1) == 1
    assert _tts_clipping_budget(100_000, 1) == 1
    assert _tts_clipping_budget(10_000_000, 2) == 16
