from unittest import mock

import pytest

from brownify.errors import InvalidInputError
from brownify.splitters import (
    AudioSplitter2Channel,
    AudioSplitter4Channel,
    AudioSplitter5Channel,
    AudioSplitterFactory,
    AudioSplitterType,
)


@pytest.fixture
def dummy_filename():
    return "dummy"


class MockSeparator:
    pass


def mock_init_separator(self):
    pass


def test_audio_splitter_factory_2_channel():
    with mock.patch.object(
        AudioSplitter2Channel, "_init_separator", new=mock_init_separator
    ):
        splitter = AudioSplitterFactory.get_audio_splitter(
            AudioSplitterType.ONLY_VOCALS
        )
        assert isinstance(splitter, AudioSplitter2Channel)
        assert len(splitter.get_channels()) == 2


def test_audio_splitter_factory_4_channel():
    with mock.patch.object(
        AudioSplitter4Channel, "_init_separator", new=mock_init_separator
    ):
        splitter = AudioSplitterFactory.get_audio_splitter(
            AudioSplitterType.FOUR_STEM
        )
        assert isinstance(splitter, AudioSplitter4Channel)
        assert len(splitter.get_channels()) == 4


def test_audio_splitter_factory_5_channel():
    with mock.patch.object(
        AudioSplitter5Channel, "_init_separator", new=mock_init_separator
    ):
        splitter = AudioSplitterFactory.get_audio_splitter(
            AudioSplitterType.FIVE_STEM
        )
        assert isinstance(splitter, AudioSplitter5Channel)
        assert len(splitter.get_channels()) == 5


# This is not useful yet, but we can improve this test and spin up similar
# tests if we have more complex exception handling in the implementation.
def test_audio_splitter_split(dummy_filename):
    with mock.patch.object(
        AudioSplitter2Channel, "_init_separator", new=mock_init_separator
    ):
        splitter = AudioSplitter2Channel()
        splitter.separator = MockSeparator()
        splitter.separator.separate_to_file = mock.MagicMock()
        splitter.split(dummy_filename)


def test_audio_splitter_factory_failure():
    with pytest.raises(InvalidInputError):
        AudioSplitterFactory.get_audio_splitter("invalid")
