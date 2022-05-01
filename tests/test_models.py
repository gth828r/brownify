import numpy as np
import pytest

from brownify.models import Track


@pytest.fixture
def dummy_track():
    return Track(
        audio=np.array(
            [[254, 123], [55, 72], [11, 0], [55, 24]], dtype=np.float32
        ),
        num_channels=2,
        sample_rate=12345,
        save=True,
    )


def test_clone_track(dummy_track):
    dummy_track_clone = dummy_track.clone()
    # Make sure the audio tracks are identical in value, but that they are
    # not the same object.
    assert np.array_equal(dummy_track_clone.audio, dummy_track.audio)
    assert dummy_track_clone.audio is not dummy_track.audio

    # Make sure the num_channels and sample_rates have same values
    assert dummy_track_clone.num_channels == dummy_track.num_channels
    assert dummy_track_clone.sample_rate == dummy_track.sample_rate

    # Make sure that the cloned track has save set to false by default
    assert not dummy_track_clone.save
