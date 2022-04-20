from unittest.mock import MagicMock

import pytest

from brownify.downloaders import YoutubeDownloader
from brownify.errors import NoAudioStreamFoundError


class MockYoutubeStream:
    pass


class MockYoutubeStreams:
    pass


class MockYoutube:
    streams: MockYoutubeStreams


@pytest.fixture
def dummy_url():
    return "dummy"


@pytest.fixture
def dummy_outfile():
    return "dummy"


@pytest.fixture
def mock_youtube():
    yt = MockYoutube()
    yt.streams = MockYoutubeStreams()
    return yt


def test_youtube_downloader_get_audio_success(
    dummy_url, mock_youtube, dummy_outfile
):
    ytd = YoutubeDownloader(dummy_url)
    ytd.yt = mock_youtube
    mock_stream = MockYoutubeStream()
    mock_stream.download = MagicMock(return_value=None)
    ytd.yt.streams.filter = MagicMock(return_value=[mock_stream])
    ytd.get_audio(dummy_outfile)


def test_youtube_downloader_get_audio_no_stream_found(
    dummy_url, mock_youtube, dummy_outfile
):
    ytd = YoutubeDownloader(dummy_url)
    ytd.yt = mock_youtube
    ytd.yt.streams.filter = MagicMock(return_value=[])
    with pytest.raises(NoAudioStreamFoundError):
        ytd.get_audio(dummy_outfile)
