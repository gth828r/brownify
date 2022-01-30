from __future__ import annotations
from abc import ABC, abstractmethod
import argparse
from dataclasses import dataclass
from enum import Enum, auto
import librosa
import numpy as np
import os
from pydub import AudioSegment
import pyparsing as pp
from pytube import YouTube
import shutil
import soundfile as sf
from spleeter.separator import Separator
from tqdm import tqdm
from typing import Callable, Dict, List, Union
import uuid


class NoAudioStreamFoundError(Exception):
    """Error raised when a referenced audio stream does not exist

    NoAudioStreamFoundError should be raised when an audio stream referenced
    by a caller does not exist.
    """


class UnexpectedTokenTypeError(Exception):
    """Error raised when an unexpected token is seen after parsing

    UnexpectedTokenTypeError should be raised when performing post-processing
    steps over input which has already been processed by the grammar. It is
    used to catch issues where the syntax defined by the configuration
    langauge allows for a class of token which is not semantically understood
    by the program. In general, this should not happen unless there is a bug
    caused by a mismatch between the grammar and the current code logic.
    """


class TokenNotInGrammarError(Exception):
    """Error raised when an token is invalid but passed the parser

    TokenNotInGrammarError should be raised when performing post-processing
    steps over input which has already been processed by the grammar. It is
    used to catch issues where the expected syntax of a token in
    post-processing code does not match the expected syntax of the grammar.
    In general, this should not happen unless there is a bug caused by a
    mismatch between the grammar and the current code logic.
    """


class NoPipelineSourceError(Exception):
    """Error raised when a pipeline has a source which does not exist

    NoPipelineSourceError should be raised when a pipeline has been defined
    using a source name that has no backing track available.
    """


@dataclass
class Pipeline:
    """A processing sequence for an audio source

    Pipelines define an audio source name, a series of actions to apply, and
    an audio sink name. They also include a flag noting whether or not the
    track should be saved for merging.

    Args:
        source (str): Name of an audio source
        actions: (List[Callable]): Series of actions to apply to the source
        sink: (str): New name for the processed audio
        save: (bool): Mark a sink to be saved into the final merged file
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
        audio (numpy.ndarray): Array containing the an sequence of audio data;
        the first dimension represents time, and the second dimension (if
        present) represents channels
        num_channels: (int): Number of channels in the audio data
        sample_rate: (int): The rate at which the audio data was sampled
        save: (bool): Mark a track to be saved in the final merged file
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
            Track: A deep copy of the original track
        """
        return Track(
            audio=np.copy(self.audio),
            num_channels=self.num_channels,
            sample_rate=self.sample_rate,
            save=False,
        )


class ActionParser:
    """ActionParser defines and parses the recipe grammar

    ActionParser takes in the user provided recipe for the final audio file
    and converts it into a series of Pipelines for processing. It contains
    the grammar definition and also semantic-level processing for the
    conversion of the recipe into Pipelines.
    """

    def __init__(self):
        self._channel = (
            pp.Keyword("bass")
            | pp.Keyword("drums")
            | pp.Keyword("piano")
            | pp.Keyword("other")
            | pp.Keyword("vocals")
        )
        self._entity = pp.Word(pp.alphanums)
        self._source = self._channel | self._entity
        self._drop = pp.Keyword("drop")
        self._var = self._entity
        self._save = pp.Group(
            pp.Literal("save(") + self._entity + pp.Literal(")")
        )
        self._sink = self._drop | self._save | self._var
        self._action = (
            pp.Keyword("early")
            | pp.Keyword("flat")
            | pp.Keyword("halfflat")
            | pp.Keyword("halfsharp")
            | pp.Keyword("late")
            | pp.Keyword("octavedown")
            | pp.Keyword("octaveup")
            | pp.Keyword("sharp")
        )
        self._connector = pp.Literal("->")
        self._expression = pp.Group(
            self._source
            + self._connector
            + (self._action + self._connector)[0, ...]
            + self._sink
        )
        self._eol = pp.Literal(";")
        self._pipelines = (
            self._expression
            + (self._eol + self._expression)[0, ...]
            + self._eol[0, 1]
        )

        self._fn_map = {
            "early": Brownifier.early,
            "flat": Brownifier.flat,
            "halfflat": Brownifier.half_flat,
            "halfsharp": Brownifier.half_sharp,
            "late": Brownifier.late,
            "octavedown": Brownifier.octave_down,
            "octaveup": Brownifier.octave_up,
            "sharp": Brownifier.sharp,
        }

    @staticmethod
    def _matches_parser_element(token: str, pe: pp.ParserElement) -> bool:
        # FIXME: Is there a better way?
        try:
            pe.parse_string(token)
            return True
        except pp.ParseException:
            return False

    def _is_action(self, token: str) -> bool:
        return self._matches_parser_element(token, self._action)

    def _is_connector(self, token: str) -> bool:
        return self._matches_parser_element(token, self._connector)

    def _is_sink(self, token: str) -> bool:
        return self._matches_parser_element(token, self._sink)

    def _is_save(self, token: str) -> bool:
        return self._matches_parser_element(token, self._save)

    def _is_drop(self, token: str) -> bool:
        return self._matches_parser_element(token, self._drop)

    @staticmethod
    def _split_into_expressions(
        program: pp.ParseResult,
    ) -> List[Union[str, List[str]]]:
        pipeline_specs = []
        for expression in program.asList():
            if expression != ";":
                pipeline_specs.append(expression)

        return pipeline_specs

    def _convert_into_pipeline(
        self, expression: List[Union[str, List[str]]]
    ) -> Union[Pipeline, None]:
        if len(expression) == 0:
            return None

        source = expression[0]
        actions = []
        sink = None
        save = False
        for item in expression[1:]:
            # We need to handle both individual tokens and grouped tokens.
            # An example of a grouped token is a save token, which will
            # take the form ["save(", "NAME", ")"].
            token = None
            if isinstance(item, str):
                token = item
            elif isinstance(item, list):
                token = "".join(item)
            else:
                raise UnexpectedTokenTypeError(
                    f"Encountered unexpected token type: {type(token)}"
                )

            # Parse the input program to construct pipelines
            if self._is_action(token):
                actions.append(self._fn_map[item])
            elif self._is_sink(token):
                if self._is_drop(token):
                    return None
                elif self._is_save(token):
                    # Skip over the part of the lit that says "save(" and ")"
                    # There should only be one element.
                    sink_name_parts = item[1:-1]
                    if len(sink_name_parts) != 1:
                        raise TokenNotInGrammarError(
                            f"Token {token} is not a valid save declaration"
                        )

                    sink = sink_name_parts[0]
                    save = True
                else:
                    sink = token
            elif self._is_connector(token):
                continue
            else:
                raise TokenNotInGrammarError(
                    f"Token {token} is not part of valid grammar"
                )

        return Pipeline(source=source, actions=actions, sink=sink, save=save)

    def get_pipelines(self, program: str) -> List[Pipeline]:
        """Get audio processing pipelines given a recipe

        Args:
            program (str): Recipe defining the steps to perform over the audio

        Returns:
            List[Pipeline]: Sequence of pipelines to be run
        """
        parsed = self._pipelines.parse_string(program)
        pipeline_exprs = self._split_into_expressions(parsed)

        pipelines = []
        for pipeline_expr in pipeline_exprs:
            pipeline = self._convert_into_pipeline(pipeline_expr)
            if pipeline:
                pipelines.append(pipeline)

        return pipelines


class YoutubeDownloader:
    """YoutubeDownloader downloads audio to files from Youtube

    YoutubeDownloader is a convenience class for fetching audio files from
    Youtube links.
    """

    def __init__(self, url: str):
        """Create a YoutubeDownloader

        Args:
            url (str): Complete URL to a Youtube video
        """
        self.url = url
        # FIXME: validate
        # What a fool believes: https://www.youtube.com/watch?v=dJe1iUuAW4M
        # Chicago - Saturday: https://www.youtube.com/watch?v=PLiMy4NaSKc

    def __enter__(self):
        self.yt = YouTube(self.url)
        return self

    def __exit__(self, exctype, excval, excbt):
        pass

    def get_audio(
        self, filename: str, file_type: str = "mp4", abr: str = "128kbps"
    ) -> None:
        """Method to fetch the audio file

        Args:
            filename (str): The path to save the fetched aduio file to
            file_type (str, optional): Type of audio stream to fetch from
            Youtube. Defaults to "mp4".
            abr (str, optional): Audio bitrate to look for on Youtube.
            Defaults to "128kbps".

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


class AudioSplitter(ABC):
    """Abstract class for an object that splits audio files into sources

    AudioSplitter is the top of the class hierarchy for objects which can
    take in audio files and split them into multiple separated sources
    """

    separator: Separator

    @abstractmethod
    def _init_separator(self) -> None:
        NotImplementedError

    @abstractmethod
    def get_channels(self) -> List[str]:
        NotImplementedError

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


class Brownifier:
    @staticmethod
    def _is_stereo(track: Track) -> bool:
        return track.num_channels == 2

    @staticmethod
    def _change_pitch_stereo(
        track: Track, n_steps: int, bins_per_octave: int
    ) -> Track:
        track.audio[:, 0] = librosa.effects.pitch_shift(
            track.audio[:, 0],
            track.sample_rate,
            n_steps=n_steps,
            bins_per_octave=bins_per_octave,
        )
        track.audio[:, 1] = librosa.effects.pitch_shift(
            track.audio[:, 1],
            track.sample_rate,
            n_steps=n_steps,
            bins_per_octave=bins_per_octave,
        )
        return track

    @staticmethod
    def _change_pitch_mono(
        track: Track, n_steps: int, bins_per_octave: int
    ) -> Track:
        track.audio = librosa.effects.pitch_shift(
            track.audio,
            track.sample_rate,
            n_steps=n_steps,
            bins_per_octave=bins_per_octave,
        )
        return track

    @staticmethod
    def change_pitch(
        track: Track, n_steps: int, bins_per_octave: int = 12
    ) -> Track:
        """Change the pitch of the track without changing the track speed

        Args:
            track (Track): The track to modify
            n_steps (int): Number of steps to modify by (positive or negative)
            bins_per_octave (int, optional): Number of steps in an octave.
            Defaults to 12.

        Returns:
            Track: The track with the pitch changed
        """
        if Brownifier._is_stereo(track):
            return Brownifier._change_pitch_stereo(
                track, n_steps, bins_per_octave
            )
        else:
            return Brownifier._change_pitch_mono(
                track, n_steps, bins_per_octave
            )

    @staticmethod
    def flat(track: Track) -> Track:
        """Make the track flat by one semitone

        Args:
            track (Track): The track to modify

        Returns:
            Track: The track which is now flat
        """
        return Brownifier.change_pitch(track, n_steps=-1)

    @staticmethod
    def sharp(track: Track) -> Track:
        """Make the track sharp by one semitone

        Args:
            track (Track): The track to modify

        Returns:
            Track: The track which is now sharp
        """
        return Brownifier.change_pitch(track, n_steps=1)

    @staticmethod
    def half_flat(track: Track) -> Track:
        """Make the track flat by one quarter tone

        Args:
            track (Track): The track to modify

        Returns:
            Track: The track which is now half-flat
        """
        return Brownifier.change_pitch(track, n_steps=-1, bins_per_octave=24)

    @staticmethod
    def half_sharp(track: Track) -> Track:
        """Make the track sharp by one quarter tone

        Args:
            track (Track): The track to modify

        Returns:
            Track: The track which is now half-sharp
        """
        return Brownifier.change_pitch(track, n_steps=1, bins_per_octave=24)

    @staticmethod
    def octave_up(track: Track) -> Track:
        """Move the track up by a full octave

        Args:
            track (Track): The track to modify

        Returns:
            Track: The track which is now an octave higher
        """
        return Brownifier.change_pitch(track, n_steps=12)

    @staticmethod
    def octave_down(track: Track) -> Track:
        """Move the track down by a full octave

        Args:
            track (Track): The track to modify

        Returns:
            Track: The track which is now an octave lower
        """
        return Brownifier.change_pitch(track, n_steps=-12)

    @staticmethod
    def time_shift(track: Track, steps: int) -> Track:
        """Shift the track forward or backward in time

        The track is shifted forward or backward in time by rolling the
        values and wrapping where the track ends back to the beginning
        or vice-versa

        Args:
            track (Track): The track to modify
            steps (int): The number of samples to shift by

        Returns:
            Track: The track which has been shifted in time
        """
        # FIXME: the API should be based on time and it should be calculated
        # based on the track's sample rate.
        track.audio = np.roll(track.audio, steps)
        return track

    @staticmethod
    def early(track: Track) -> Track:
        """Shift the track forward in time by about a tenth of a second

        Args:
            track (Track): The track to modify

        Returns:
            Track: The track which is now early
        """
        # FIXME: should be based on sample rate
        return Brownifier.time_shift(track, -1500)

    @staticmethod
    def late(track: Track) -> Track:
        """Shift a track backward in time by about a tenth of a second

        Args:
            track (Track): The track to modify

        Returns:
            Track: The track which is now late
        """
        # FIXME: should be based on sample rate
        track.audio = np.roll(track.audio, 1500)
        return track


class PipelineProcessor:
    """Class for processing a series of Pipeline objects"""

    def __init__(self, target: str, splitter: AudioSplitter):
        self.tracks: Dict[str, Track] = {}
        self.target = target
        self._splitter = splitter
        self._saved_files = []
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
            pipelines (List[Pipeline]): List of pipelines to apply to generate
            an audio track
            output_file (str): Path to output the track to
        """
        self._process(pipelines)
        self._save()
        self._merge(output_file)


class AudioMerger:
    @staticmethod
    def merge(files: List[str]) -> AudioSegment:
        """Merge the list of audio sources into an AudioSegment

        Args:
            files (List[str]): List of track sources to merge

        Returns:
            AudioSegment: The overlayed tracks merged into an AudioSegment
        """
        merged = None
        for f in tqdm(files, "Merging tracks..."):
            audio = AudioSegment.from_wav(f)
            if merged:
                merged = merged.overlay(audio)
            else:
                merged = audio

        return merged

    @staticmethod
    def save_file(filename: str, audio: AudioSegment) -> None:
        """Save the merged audio file

        Args:
            filename (str): Path to use for the merged file
            audio (AudioSegment): AudioSegment to save
        """
        audio.export(filename, format="mp3")


def get_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Make your music brown")
    parser.add_argument("youtube", help="URL for a youtube video")
    parser.add_argument(
        "output", help="Filename to send output to (will be an mp3)"
    )
    parser.add_argument("--recipe", help="Sequence to apply to audio streams")
    parser.add_argument(
        "--recipe-file", help="Path to an existing recipe file"
    )

    return parser.parse_args()


def main():
    args = get_args()

    youtube_url = args.youtube
    output_file = args.output
    recipe = args.recipe
    recipe_file = args.recipe_file

    program = None
    if recipe:
        program = recipe

    elif recipe_file:
        with open(recipe_file, "r") as f:
            # Read in program and ignore newlines
            program = f.read().replace("\n", "")

    else:
        raise Exception("Must provide either a recipe or a recipe file")

    ap = ActionParser()
    pipelines = ap.get_pipelines(program)

    tmp_name = str(uuid.uuid4())
    downloaded_file = f"{tmp_name}.mp4"

    with YoutubeDownloader(youtube_url) as ytd:
        ytd.get_audio(downloaded_file, file_type="mp4")

    splitter = AudioSplitterFactory.get_audio_splitter(
        AudioSplitterType.FIVE_STEM
    )
    splitter.split(downloaded_file)

    try:
        os.remove(downloaded_file)
    except OSError as ose:
        # FIXME: log here instead
        raise ose

    processor = PipelineProcessor(tmp_name, splitter)
    processor.process(pipelines, output_file)

    try:
        # Spleeter stores its files in a directory named after the original
        # file's base name
        shutil.rmtree(str(tmp_name))
        pass

    except OSError as ose:
        # FIXME: log here instead
        raise ose


if __name__ == "__main__":
    main()
