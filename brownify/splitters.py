from abc import ABC, abstractmethod
from enum import Enum, auto
from typing import List

from spleeter.separator import Separator

from brownify.errors import InvalidInputError


class AudioSplitter(ABC):
    """Abstract class for an object that splits audio files into sources

    AudioSplitter is the top of the class hierarchy for objects which can
    take in audio files and split them into multiple separated sources
    """

    separator: Separator

    @abstractmethod
    def _init_separator(self) -> None:
        """Initialize the separator

        Each concrete implementation of a separator must implement this method
        to initialize its separator.
        """

    @abstractmethod
    def get_channels(self) -> List[str]:
        """Get the list of named of channels that the splitter will create"""

    def split(self, filename: str) -> None:
        """Split an audio file into multiple sources

        Args:
            filename (str): Path to the file which should be split into
                multiple sources
        """
        self.separator.separate_to_file(filename, ".")


class AudioSplitter5Channel(AudioSplitter):
    """Split a file into bass, drums, piano, vocals, and other tracks

    AudioSplitter5Channel objects can split a single track into separate
    bass, drum, piano, vocals, and other tracks. It is useful when an audio
    source should be split into all of those tracks with the potential of
    a less clean separation than the other splitters with fewer tracks.
    """

    CHANNELS = [
        "bass",
        "drums",
        "other",
        "piano",
        "vocals",
    ]

    def __init__(self):
        self._init_separator()

    def _init_separator(self) -> None:
        self.separator = Separator("spleeter:5stems")

    def get_channels(self) -> List[str]:
        return self.CHANNELS


class AudioSplitter4Channel(AudioSplitter):
    """Split a file into bass, drums, vocals, and other tracks

    AudioSplitter4Channel objects can split a single track into separate
    bass, drum, vocals, and other tracks. It is useful when an audio source
    should be split into all of those tracks with the potential of a less
    clean separation than the other splitters with fewer tracks.
    """

    CHANNELS = [
        "bass",
        "drums",
        "other",
        "vocals",
    ]

    def __init__(self):
        self._init_separator()

    def _init_separator(self) -> None:
        self.separator = Separator("spleeter:4stems")

    def get_channels(self) -> List[str]:
        return self.CHANNELS


class AudioSplitter2Channel(AudioSplitter):
    """Split a file into vocal and other tracks

    AudioSplitter2Channel objects can split a single track into separate
    voice and other tracks. It may provide the cleanest track separation
    if only vocal isolation is desired.
    """

    CHANNELS = [
        "other",
        "vocals",
    ]

    def __init__(self):
        self._init_separator()

    def _init_separator(self) -> None:
        self.separator = Separator("spleeter:2stems")

    def get_channels(self) -> List[str]:
        return self.CHANNELS


class AudioSplitterType(Enum):
    """Enumerate AudioSplitter types for the AudioSplitterFactory"""

    ONLY_VOCALS = auto()
    FOUR_STEM = auto()
    FIVE_STEM = auto()


class AudioSplitterFactory:
    """Factory class for creating AudioSplitter objects"""

    @staticmethod
    def get_audio_splitter(
        audio_splitter_type: AudioSplitterType = AudioSplitterType.FIVE_STEM,
    ) -> AudioSplitter:
        """Method for getting AudioSplitter instances

        Args:
            audio_splitter_type (AudioSplitterType, optional): Type of
            AudioSplitter to create. See the class documentation of each type
            for assistance choosing. Defaults to AudioSplitterType.FIVE_STEM.

        Returns:
            AudioSplitter: A concrete instance of an AudioSplitter
        """
        if audio_splitter_type == AudioSplitterType.ONLY_VOCALS:
            return AudioSplitter2Channel()
        elif audio_splitter_type == AudioSplitterType.FOUR_STEM:
            return AudioSplitter4Channel()
        elif audio_splitter_type == AudioSplitterType.FIVE_STEM:
            return AudioSplitter5Channel()
        else:
            raise InvalidInputError(
                f"Unknown splitter type provided: {audio_splitter_type}"
            )
