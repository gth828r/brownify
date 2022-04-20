import numpy as np
import pytest

from brownify.actions import Brownifier
from brownify.models import Track


@pytest.fixture
def dummy_mono_track():
    return Track(
        audio=np.random.rand(2048) * 1000,
        num_channels=1,
        sample_rate=12345,
        save=False,
    )


@pytest.fixture
def dummy_stereo_track():
    return Track(
        audio=np.random.rand(2048, 2) * 1000,
        num_channels=2,
        sample_rate=12345,
        save=False,
    )


# These action functions are hard to test deeply without exposing the
# underlying implementations. As a compromise, just check for equality
# and inequality.


def test_change_pitch_mono_null(dummy_mono_track):
    track = dummy_mono_track.clone()
    track = Brownifier.change_pitch(track, 0)
    assert np.allclose(track.audio, dummy_mono_track.audio)


def test_change_pitch_mono_up(dummy_mono_track):
    track = dummy_mono_track.clone()
    track = Brownifier.change_pitch(track, 1)
    assert not np.allclose(track.audio, dummy_mono_track.audio)


def test_change_pitch_mono_down(dummy_mono_track):
    track = dummy_mono_track.clone()
    track = Brownifier.change_pitch(track, -1)
    assert not np.allclose(track.audio, dummy_mono_track.audio)


def test_change_pitch_stereo_up(dummy_stereo_track):
    track = dummy_stereo_track.clone()
    track = Brownifier.change_pitch(track, 1)
    assert not np.allclose(track.audio, dummy_stereo_track.audio)


def test_change_pitch_stereo_down(dummy_stereo_track):
    track = dummy_stereo_track.clone()
    track = Brownifier.change_pitch(track, -1)
    assert not np.allclose(track.audio, dummy_stereo_track.audio)


def test_sharp(dummy_stereo_track):
    track = dummy_stereo_track.clone()
    track = Brownifier.sharp(track)
    assert not np.all(np.array_equal(track.audio, dummy_stereo_track.audio))


def test_flat(dummy_stereo_track):
    track = dummy_stereo_track.clone()
    track = Brownifier.flat(track)
    assert not np.all(np.array_equal(track.audio, dummy_stereo_track.audio))


def test_half_sharp(dummy_stereo_track):
    track = dummy_stereo_track.clone()
    track = Brownifier.half_sharp(track)
    assert not np.all(np.array_equal(track.audio, dummy_stereo_track.audio))


def test_half_flat(dummy_stereo_track):
    track = dummy_stereo_track.clone()
    track = Brownifier.half_flat(track)
    assert not np.all(np.array_equal(track.audio, dummy_stereo_track.audio))


def test_octave_up(dummy_stereo_track):
    track = dummy_stereo_track.clone()
    track = Brownifier.octave_up(track)
    assert not np.allclose(track.audio, dummy_stereo_track.audio)


def test_octave_down(dummy_stereo_track):
    track = dummy_stereo_track.clone()
    track = Brownifier.octave_down(track)
    assert not np.allclose(track.audio, dummy_stereo_track.audio)


def test_time_shift_mono_forward(dummy_mono_track):
    track = dummy_mono_track.clone()
    track = Brownifier.time_shift(track, 100)
    assert not np.allclose(track.audio, dummy_mono_track.audio)


def test_time_shift_mono_backward(dummy_mono_track):
    track = dummy_mono_track.clone()
    track = Brownifier.time_shift(track, -100)
    assert not np.allclose(track.audio, dummy_mono_track.audio)


def test_time_shift_stereo_forward(dummy_stereo_track):
    track = dummy_stereo_track.clone()
    track = Brownifier.time_shift(track, 100)
    assert not np.allclose(track.audio, dummy_stereo_track.audio)


def test_time_shift_stereo_backward(dummy_stereo_track):
    track = dummy_stereo_track.clone()
    track = Brownifier.time_shift(track, -100)
    assert not np.allclose(track.audio, dummy_stereo_track.audio)


def test_null_time_shift(dummy_stereo_track):
    track = dummy_stereo_track.clone()
    track = Brownifier.time_shift(track, 0)
    assert np.allclose(track.audio, dummy_stereo_track.audio)


def test_early(dummy_stereo_track):
    track = dummy_stereo_track.clone()
    track = Brownifier.early(track)
    assert not np.allclose(track.audio, dummy_stereo_track.audio)


def test_late(dummy_stereo_track):
    track = dummy_stereo_track.clone()
    track = Brownifier.late(track)
    assert not np.allclose(track.audio, dummy_stereo_track.audio)
