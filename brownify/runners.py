from typing import Dict, List

import soundfile as sf
from pydub import AudioSegment
from pydub.exceptions import PydubException
from tqdm import tqdm

from brownify.errors import (
    InvalidInputError,
    MergingError,
    NoPipelineSourceError,
)
from brownify.models import Pipeline, Track
from brownify.splitters import AudioSplitter


class PipelineProcessor:
    """Class for processing a series of Pipeline objects"""

    def __init__(self, target: str, splitter: AudioSplitter):
        self.tracks: Dict[str, Track] = {}
        self.target = target
        self._splitter = splitter
        self._saved_files: List[str] = []
        for channel in tqdm(
            splitter.get_channels(), "Loading split sources for processing..."
        ):
            filename = f"./{target}/{channel}.wav"
            self.tracks[channel] = self._load_track(filename)

    @staticmethod
    def _load_track(filename: str) -> Track:
        audio, sample_rate = sf.read(filename)

        is_stereo = True
        if len(audio.shape) == 1:
            is_stereo = False

        num_channels = 2 if is_stereo else 1

        return Track(
            audio=audio,
            num_channels=num_channels,
            sample_rate=sample_rate,
            save=False,
        )

    @staticmethod
    def _save_track(filename: str, track: Track) -> None:
        sf.write(filename, track.audio, track.sample_rate)

    def _process(self, pipelines: List[Pipeline]) -> None:
        for pipeline in tqdm(pipelines, desc="Brownifying..."):
            if pipeline.source not in self.tracks:
                raise NoPipelineSourceError(
                    f"No track has been loaded with the name {pipeline.source}"
                    f" yet. Is your recipe correct? Pipeline: {pipeline}"
                )

            track = self.tracks[pipeline.source].clone()

            for action in pipeline.actions:
                track = action(track)

            # It is OK to overwrite sources with sinks, so no need to check
            self.tracks[pipeline.sink] = Track(
                audio=track.audio,
                num_channels=track.num_channels,
                sample_rate=track.sample_rate,
                save=pipeline.save,
            )

    def _save(self) -> None:
        for name in tqdm(self.tracks, desc="Preparing to merge tracks..."):
            track = self.tracks[name]
            if track.save:
                filename = f"./{self.target}/{name}.wav"
                self._save_track(filename, track)
                self._saved_files.append(filename)

    def _merge(self, output_file: str) -> None:
        merged_audio = AudioMerger.merge(self._saved_files)
        AudioMerger.save_file(output_file, merged_audio)

    def process(self, pipelines: List[Pipeline], output_file: str) -> None:
        """Process a series of pipelines and output a processed audio file

        Args:
            pipelines: List of pipelines to apply to generate an audio track
            output_file: Path to output the track to
        """
        self._process(pipelines)
        self._save()
        self._merge(output_file)


class AudioMerger:
    @staticmethod
    def merge(files: List[str]) -> AudioSegment:
        """Merge the list of audio sources into an AudioSegment

        Args:
            files: List of track sources to merge

        Raises:
            InvalidInputError: If no files were provided to merge, then this
                is likely the result of a bad input recipe.
            MergingError: If the tracks are unabled to be merged

        Returns:
            The overlaid tracks merged into an AudioSegment
        """
        if len(files) == 0:
            raise InvalidInputError(
                "No files were provided to merge. There is likely an issue "
                "with the input recipe."
            )

        try:
            merged = AudioSegment.from_wav(files[0])

            if len(files) > 1:
                for f in tqdm(files[1:], "Merging tracks..."):
                    audio = AudioSegment.from_wav(f)
                    merged = merged.overlay(audio)

            return merged
        except PydubException:
            raise MergingError(
                f"Unable to combine tracks backed by files: {files}"
            )

    @staticmethod
    def save_file(filename: str, audio: AudioSegment) -> None:
        """Save the merged audio file

        Args:
            filename: Path to use for the merged file
            audio: AudioSegment to save

        Raises:
            MergingError: If unable to save the merged track
        """
        try:
            audio.export(filename, format="mp3")
        except PydubException:
            raise MergingError(
                f"Unable to save merged track to file {filename}"
            )
