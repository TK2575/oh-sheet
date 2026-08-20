#!/usr/bin/env python3
"""Quick test to verify quantization fix in engrave_local.py"""

from backend.contracts import ScoreNote, PianoScore, ScoreMetadata, ExpressionMap
from backend.services.engrave_local import (
    _quantize_durations_before_build,
    score_to_musicxml,
    EngraveLocalError,
)


def test_quantization_extreme_durations():
    """Test that extreme durations (2048th notes) are quantized to acceptable values."""

    # Create notes with problematic extreme durations
    notes = [
        ScoreNote(
            id="n0",
            pitch=60,
            onset_beat=0.0,
            duration_beat=1.0 / 2048,  # 2048th note - music21 will reject this
            velocity=64,
            voice=1,
        ),
        ScoreNote(
            id="n1",
            pitch=62,
            onset_beat=0.5,
            duration_beat=3.0 / 2048,  # Another extreme duration
            velocity=64,
            voice=1,
        ),
        ScoreNote(
            id="n2",
            pitch=64,
            onset_beat=1.0,
            duration_beat=0.5,  # Normal duration
            velocity=64,
            voice=1,
        ),
    ]

    # Apply quantization
    quantized = _quantize_durations_before_build(notes)

    # Check that extreme durations are quantized to acceptable values
    print(f"Original durations: {[n.duration_beat for n in notes]}")
    print(f"Quantized durations: {[n.duration_beat for n in quantized]}")

    # All durations should be >= 1/64 (0.015625)
    min_duration = 1.0 / 64
    for note in quantized:
        assert note.duration_beat >= min_duration, \
            f"Duration {note.duration_beat} is less than minimum {min_duration}"
        # For extreme durations (< 1/64), should be clamped to exactly 1/64
        if notes[[n.id for n in notes].index(note.id)].duration_beat < min_duration:
            assert note.duration_beat == min_duration, \
                f"Extreme duration {note.id} should be clamped to {min_duration}, got {note.duration_beat}"
        print(f"✓ Note {note.id}: {note.duration_beat} (acceptable)")

    print("\n✓ All durations quantized successfully!")


def test_quantization_in_musicxml_export():
    """Test that quantized notes can be exported to MusicXML without errors."""

    # Create a minimal score with extreme durations
    metadata = ScoreMetadata(
        title="Quantization Test",
        composer="Test",
        key="C:major",
        time_signature=(4, 4),
        tempo_map=[],
        chord_symbols=[],
        arranger=None,
        tempo_marking=None,
        difficulty="beginner",
    )

    # Notes with extreme durations
    right_hand = [
        ScoreNote(
            id="rh0",
            pitch=60,
            onset_beat=0.0,
            duration_beat=1.0 / 2048,  # Extreme
            velocity=64,
            voice=1,
        ),
        ScoreNote(
            id="rh1",
            pitch=64,
            onset_beat=0.5,
            duration_beat=0.5,
            velocity=64,
            voice=1,
        ),
    ]

    left_hand = [
        ScoreNote(
            id="lh0",
            pitch=36,
            onset_beat=0.0,
            duration_beat=1.0 / 1024,  # Another extreme
            velocity=64,
            voice=1,
        ),
    ]

    score = PianoScore(
        metadata=metadata,
        right_hand=right_hand,
        left_hand=left_hand,
    )

    # Try to export to MusicXML
    try:
        xml_bytes, features = score_to_musicxml(score)
        print(f"✓ MusicXML export successful!")
        print(f"  - Generated {len(xml_bytes)} bytes of XML")
        print(f"  - Notes: {features.note_count}")
        print(f"  - Has valid structure: {xml_bytes.startswith(b'<?xml') or b'<score' in xml_bytes}")
    except EngraveLocalError as e:
        print(f"✗ MusicXML export failed: {e}")
        raise


if __name__ == "__main__":
    print("=" * 60)
    print("Testing Quantization Fix")
    print("=" * 60)

    print("\n1. Testing quantization logic...")
    test_quantization_extreme_durations()

    print("\n2. Testing MusicXML export with quantized notes...")
    test_quantization_in_musicxml_export()

    print("\n" + "=" * 60)
    print("✓ All tests passed!")
    print("=" * 60)
