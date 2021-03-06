from pytube import YouTube

from brownify.errors import NoAudioStreamFoundError


class YoutubeDownloader:
    """YoutubeDownloader downloads audio to files from Youtube

    YoutubeDownloader is a convenience class for fetching audio files from
    Youtube links.
    """

    def __init__(self, url: str):
        """Create a YoutubeDownloader

        Args:
            url: Complete URL to a Youtube video
        """
        self.url = url
        # FIXME: validate

    def __enter__(self):
        self.yt = YouTube(
            self.url
        )  # pragma: no cover, this is an external operation
        return self  # pragma: no cover

    def __exit__(self, exctype, excval, excbt):
        pass  # pragma: no cover

    def get_audio(
        self, filename: str, file_type: str = "mp4", abr: str = "128kbps"
    ) -> None:
        """Method to fetch the audio file

        Args:
            filename: The path to save the fetched aduio file to
            file_type: Type of audio stream to fetch from Youtube. Defaults
                to "mp4".
            abr: Audio bitrate to look for on Youtube. Defaults to "128kbps".

        Raises:
            NoAudioStreamFoundError: If no audio stream can be found for the
                provided URL given the provided file type and bitrate
        """
        streams = self.yt.streams.filter(
            only_audio=True, abr=abr, file_extension=file_type
        )
        if len(streams) == 0:
            raise NoAudioStreamFoundError(
                f"No audio stream found at {self.url}"
            )

        streams[0].download(filename=filename)
