import argparse
from brownify.downloaders import YoutubeDownloader
from brownify.parsers import ActionParser
from brownify.splitters import AudioSplitterFactory, AudioSplitterType
from brownify.runners import PipelineProcessor
import os
import shutil
import uuid


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
