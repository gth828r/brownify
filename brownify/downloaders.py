import yt_dlp

from brownify.errors import NoAudioStreamFoundError


class YoutubeDownloader:
    """YoutubeDownloader downloads audio to files from Youtube

    YoutubeDownloader is a convenience class for fetching audio files from
    Youtube links.
    """

    @staticmethod
    def get_audio(
        url: str,
        filename: str,
    ) -> None:
        """Method to fetch the audio file

        Args:
            url: URL for the YouTube video to download audio from
            filename: The path to save the fetched aduio file to. This
            must include an extension such as ".mp3" to fetch an audio file
            from youtube.

        Raises:
            NoAudioStreamFoundError: If no audio stream can be found for the
                provided URL given the provided file type and bitrate
        """
        options = {
            "extract_audio": True,
            "format": "bestaudio",
            "outtmpl": f"{filename}",
        }
        with yt_dlp.YoutubeDL(options) as downloader:
            try:
                downloader.download(url)
            except yt_dlp.utils.DownloadError:
                raise NoAudioStreamFoundError(
                    f"No audio stream found at {url}"
                )
