import argparse
import sys
from brownify.downloaders import YoutubeDownloader
from brownify.errors import BrownifyError, InvalidInputError
from brownify.parsers import ActionParser
from brownify.splitters import AudioSplitterFactory, AudioSplitterType
from brownify.runners import PipelineProcessor
import logging
import os
import shutil
import uuid


_LOG_LEVELS = {"debug", "info", "warning", "error", "critical"}
_DEFAULT_LOG_LEVEL = "warning"


def get_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Make your music brown")
    parser.add_argument("youtube", help="URL for a youtube video")
    parser.add_argument(
        "output", help="Filename to send output to (will be an mp3)"
    )
    parser.add_argument(
        "--log",
        default=_DEFAULT_LOG_LEVEL,
        choices=_LOG_LEVELS,
        help="Log level to use for output",
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--recipe", help="Sequence to apply to audio streams")
    group.add_argument(
        "--recipe-file", help="Path to an existing recipe file"
    )

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

    raise InvalidInputError("Either a recipe or a recipe file must be provided")


def _cleanup(downloaded_file, session_id):
    try:
        # Clean the intermediate downloaded file
        os.remove(downloaded_file)
    except OSError as ose:
        logging.warning(f"Could not remove downloaded file {downloaded_file}")
        logging.debug(ose, exc_info=True)

    try:
        # Spleeter stores its files in a directory named after the original
        # file's base name
        shutil.rmtree(str(session_id))
    except OSError as ose:
        logging.warning(f"Could not remove intermediate processed files under directory {session_id}/")
        logging.debug(ose, exc_info=True)


def main() -> int:
    args = get_args()

    youtube_url = args.youtube
    output_file = args.output
    log_level = args.log.upper()
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

    # Create downloaded filename based on session ID
    downloaded_file = f"{session_id}.mp4"

    try:
        # Get the program from user input
        program = _get_program(recipe, recipe_file)

        # Based on the program, instantiate a processing pipeline
        ap = ActionParser()
        pipelines = ap.get_pipelines(program)

        # Grab an audio file based on the provided inputs
        with YoutubeDownloader(youtube_url) as ytd:
            ytd.get_audio(downloaded_file, file_type="mp4")

        # Split the input audio into different tracks
        splitter = AudioSplitterFactory.get_audio_splitter(
            AudioSplitterType.FIVE_STEM
        )
        splitter.split(downloaded_file)

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
        # Clean up temporary files unless they have been marked for preservation
        _cleanup(downloaded_file, session_id)


if __name__ == "__main__":
    sys.exit(main())
