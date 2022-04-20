from unittest import mock

import numpy as np
import pytest
import soundfile as sf

from brownify.actions import Brownifier
from brownify.errors import InvalidInputError, NoPipelineSourceError
from brownify.models import Pipeline
from brownify.runners import AudioMerger, PipelineProcessor
from brownify.splitters import AudioSplitter


class MockSplitter(AudioSplitter):
    def _init_separator(self) -> None:
        """Must implement this abstract method for test"""

    def get_channels(self):
        return ["voice"]


def mock_soundfile_read(filename):
    return np.random.rand(2048) * 1000, 12345


def mock_soundfile_write(filename, audio, sample_rate):
    pass


@pytest.fixture
def dummy_splitter():
    return MockSplitter()


@pytest.fixture
def dummy_target():
    return "dummy"


@pytest.fixture
def dummy_pipeline():
    return Pipeline(
        source="voice", actions=[Brownifier.flat], sink="newvoice", save=True
    )


@pytest.fixture
def missing_source_pipeline():
    return Pipeline(
        source="missing", actions=[Brownifier.flat], sink="newvoice", save=True
    )


def test_pipeline_processor(dummy_target, dummy_splitter, dummy_pipeline):
    with mock.patch.object(sf, "read", new=mock_soundfile_read):
        with mock.patch.object(sf, "write", new=mock_soundfile_write):
            processor = PipelineProcessor(dummy_target, dummy_splitter)
            processor._merge = mock.MagicMock()
            processor.process([dummy_pipeline], "test")


def test_pipeline_processor_missing_source(
    dummy_target, dummy_splitter, missing_source_pipeline
):
    with mock.patch.object(sf, "read", new=mock_soundfile_read):
        with mock.patch.object(sf, "write", new=mock_soundfile_write):
            processor = PipelineProcessor(dummy_target, dummy_splitter)
            processor._merge = mock.MagicMock()
            with pytest.raises(NoPipelineSourceError):
                processor.process([missing_source_pipeline], "test")


def test_audio_merger_merge_no_inputs():
    with pytest.raises(InvalidInputError):
        AudioMerger.merge([])
