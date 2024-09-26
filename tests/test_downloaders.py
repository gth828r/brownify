from unittest import mock

import pytest
import yt_dlp

from brownify.downloaders import YoutubeDownloader
from brownify.errors import NoAudioStreamFoundError


@pytest.fixture
def dummy_url():
    return "dummy"


@pytest.fixture
def dummy_outfile():
    return "dummy"


def test_youtube_downloader_get_audio_success(dummy_url, dummy_outfile):
    with mock.patch.object(yt_dlp.YoutubeDL, "download", return_value=None):
        YoutubeDownloader.get_audio(dummy_url, dummy_outfile)


def test_youtube_downloader_get_audio_no_stream_found(
    dummy_url, dummy_outfile
):
    with mock.patch.object(
        yt_dlp.YoutubeDL,
        "download",
        side_effect=yt_dlp.utils.DownloadError("Not found"),
    ):
        with pytest.raises(NoAudioStreamFoundError):
            YoutubeDownloader.get_audio(dummy_url, dummy_outfile)
