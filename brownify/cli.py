import argparse
import logging
import os
import shutil
import uuid
from typing import Optional

from brownify.downloaders import YoutubeDownloader
from brownify.errors import BrownifyError, InvalidInputError
from brownify.parsers import ActionParser
from brownify.runners import PipelineProcessor
from brownify.splitters import AudioSplitterFactory, AudioSplitterType

_LOG_LEVELS = {"debug", "info", "warning", "error", "critical"}
_DEFAULT_LOG_LEVEL = "warning"


def get_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Make your music brown")

    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument(
        "--youtube-input", help="URL for a youtube video to use as input"
    )
    input_group.add_argument(
        "--local-input", help="Path to a local file to use as input"
    )
    parser.add_argument(
        "output", help="Filename to send output to (will be an mp3)"
    )
    parser.add_argument(
        "--log",
        default=_DEFAULT_LOG_LEVEL,
        choices=_LOG_LEVELS,
        help="Log level to use for output",
    )
    parser.add_argument(
        "--preserve",
        action="store_true",
        help="Allow for intermediate files to be preserved for debugging",
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--recipe", help="Sequence to apply to audio streams")
    group.add_argument("--recipe-file", help="Path to an existing recipe file")

    return parser.parse_args()


def _get_log_level(log_level: str) -> int:
    numeric_log_level = getattr(logging, log_level, None)
    if not isinstance(numeric_log_level, int):
        raise InvalidInputError(f"Invalid log level: {log_level}")
    return numeric_log_level


def _get_program(recipe, recipe_file) -> str:
    if recipe:
        return recipe

    if recipe_file:
        with open(recipe_file, "r") as f:
            # Read in program and ignore newlines
            program = f.read().replace("\n", "")
            return program

    raise InvalidInputError(
        "Either a recipe or a recipe file must be provided"
    )


def _cleanup(downloaded_file, session_id):
    try:
        # Clean the intermediate downloaded file if it exists
        os.remove(downloaded_file)
    except OSError as ose:
        logging.warning(f"Could not remove downloaded file {downloaded_file}")
        logging.debug(ose, exc_info=True)

    try:
        # Spleeter stores its files in a directory named after the original
        # file's base name
        shutil.rmtree(str(session_id))
    except OSError as ose:
        logging.warning(
            "Could not remove intermediate processed files under directory "
            f"{session_id}/"
        )
        logging.debug(ose, exc_info=True)


def main() -> int:
    args = get_args()

    youtube_url: Optional[str] = args.youtube_input
    local_file: Optional[str] = args.local_input
    output_file = args.output
    log_level = args.log.upper()
    preserve = args.preserve
    recipe = args.recipe
    recipe_file = args.recipe_file

    # Put logging setup in its own block so if it fails, we can fail loudly
    try:
        log_level = _get_log_level(log_level)
        logging.basicConfig(level=log_level)
    except InvalidInputError as iie:
        logging.error(iie)
        return 1

    # Create a random ID for tracking this session
    session_id = str(uuid.uuid4())

    # Declare input filename to be set by either the local file
    # or by downloading an audio file from youtube
    input_file: Optional[str] = None

    try:
        # Get the program from user input
        program = _get_program(recipe, recipe_file)

        # Based on the program, instantiate a processing pipeline
        ap = ActionParser()
        pipelines = ap.get_pipelines(program)

        # Grab an audio file based on the provided inputs
        if youtube_url is not None:
            # Create download filename based on session ID
            download_file = f"{session_id}.mp4"
            YoutubeDownloader.get_audio(youtube_url, download_file)
            input_file = download_file
        elif local_file is not None:
            _, local_file_ext = os.path.splitext(local_file)
            input_file = f"{session_id}{local_file_ext}"
            # Create a symlink to the local file for this session
            os.symlink(local_file, input_file)
        else:
            raise InvalidInputError(
                "For audio input, a path to a local file or a youtube URL "
                "must be provided"
            )

        # Split the input audio into different tracks
        splitter = AudioSplitterFactory.get_audio_splitter(
            AudioSplitterType.FIVE_STEM
        )
        splitter.split(input_file)

        # Perform processing pipeline over the audio
        processor = PipelineProcessor(session_id, splitter)
        processor.process(pipelines, output_file)

        return 0

    except BrownifyError as be:
        # All Brownify errors should log their message at the error level and
        # log a stack trace at the debug level
        logging.error(be)
        logging.debug(be, exc_info=True)
        return 1

    finally:
        # Clean up temporary files unless they have been marked for
        # preservation
        if not preserve:
            _cleanup(input_file, session_id)
