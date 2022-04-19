from __future__ import annotations
from dataclasses import dataclass
import numpy as np
from typing import Callable, List


@dataclass
class Pipeline:
    """A processing sequence for an audio source

    Pipelines define an audio source name, a series of actions to apply, and
    an audio sink name. They also include a flag noting whether or not the
    track should be saved for merging.

    Args:
        source: Name of an audio source
        actions: Series of actions to apply to the source
        sink: New name for the processed audio
        save: Mark a sink to be saved into the final merged file
    """

    source: str
    actions: List[Callable]
    sink: str
    save: bool


@dataclass
class Track:
    """A container for an audio track

    Track includes the audio details needed for managing an audio track
    throughout the processing stages.

    Args:
        audio: Array containing the an sequence of audio data;
        the first dimension represents time, and the second dimension (if
        present) represents channels
        num_channels: Number of channels in the audio data
        sample_rate: The rate at which the audio data was sampled
        save: Mark a track to be saved in the final merged file
    """

    audio: np.ndarray
    num_channels: int
    sample_rate: int
    save: bool

    def clone(self) -> Track:
        """Clone a track

        Create a deep copy of a track with the save parameter always
        initialized to False

        Returns:
            A deep copy of the original track
        """
        return Track(
            audio=np.copy(self.audio),
            num_channels=self.num_channels,
            sample_rate=self.sample_rate,
            save=False,
        )