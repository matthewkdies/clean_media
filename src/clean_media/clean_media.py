from __future__ import annotations

import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)
logging.basicConfig()
logger.setLevel(logging.INFO)

CONTENT_DIRS: list[Path] = [Path("/volume2/data/media/movies"), Path("/volume2/data/media/tv")]


def rename_forced_subs(content_dir: Path):
    """Renamed any original and forced subtitle files renamed incorrectly by Sonarr and Radarr.

    Args:
        content_dir (Path): The directory to run the renaming on.
    """
    logger.info("Renaming forced subs for content dir: '%s'.", str(content_dir))

    # lets check both en and eng subtitle files for the forced renaming BS
    lang_strs = ["en", "eng"]
    for lang_str in lang_strs:
        # this glob will find all locations where an original and forced subtitle file have been renamed
        for orig_subtitle_file in content_dir.glob(f"**/*.1.{lang_str}.srt"):
            logger.debug("Found '.1.%s.srt` subtitle file: '%s'.", lang_str, str(orig_subtitle_file))
            orig_subtitle_file_str = str(orig_subtitle_file)
            orig_subtitle_file = orig_subtitle_file.rename(orig_subtitle_file_str.replace(f".1.{lang_str}.srt", ".eng.srt"))

            # if a forced subtitle exists, it will have the same path with the `.2.en.srt` suffix
            if (forced_subtitles_file := Path(orig_subtitle_file_str.replace(f".1.{lang_str}.srt", f".2.{lang_str}.srt"))).exists():
                logger.debug("Found `.2.%s.srt` subtitle file: '%s'.", lang_str, str(forced_subtitles_file))
                forced_subtitle_file_str = str(forced_subtitles_file)

                # if the "forced" sub file is the same size or larger than the original, it's a copy -> delete it
                if (forced_size := forced_subtitles_file.stat().st_size) >= (orig_size := orig_subtitle_file.stat().st_size):
                    logger.info("Seeming forced subtitle is larger than original file. Deleting.")
                    forced_subtitles_file.unlink()
                    continue

                elif forced_size > (orig_size * 0.4):
                    logger.warning("'%s' might not be a forced file, it's pretty big. Skipping, check manually.", forced_subtitle_file_str)
                    continue

                # the forced sub file is pretty much certainly forced now, let's rename it
                forced_subtitles_file.rename(forced_subtitle_file_str.replace(f".2.{lang_str}.srt", ".eng.forced.srt"))


def rename_en_to_eng_subs(content_dir: Path) -> None:
    """Finds all instances of a subtitle file ending with `.en.srt` and renames to use `.eng.srt`.

    This is done to match the format that tdarr exports subtitles to, which is the three-letter ISO code.
    Since the new Bazarr settings specify rewriting to the three-letter ISO code and tdarr does as well,
    this function should really only need to be run once.

    Args:
        content_dir (Path): The directory to run the renaming on.
    """
    logger.info("Renaming en subs to eng subs for content dir: '%s'.", str(content_dir))

    # find all instances of `.en.srt` subs -- we want to replace this with `.eng.srt`
    for en_subtitle_file in content_dir.glob("**/*.en.srt"):
        # we've got a file, let's check the `.eng.srt` equivalent
        logger.debug("Found `.en.srt` subtitle file: '%s'.", str(en_subtitle_file))
        en_subtitle_file_str = str(en_subtitle_file)
        eng_subtitle_file_str = en_subtitle_file_str.replace(".en.srt", ".eng.srt")

        # if the `.eng.srt` equivalent exists, let's just delete the old one
        if Path(eng_subtitle_file_str).exists():
            logger.info("Accompanying `.eng.srt` subtitle file exists at: '%s'; deleting `.en.srt` file.", eng_subtitle_file_str)
            en_subtitle_file.unlink()
            continue

        # farts, the `.eng.srt` equivalent doesn't exist -> let's just rename it
        logger.info("Accompanying `.eng.srt` subtitle file does NOT exist. '%s'; renaming file.", eng_subtitle_file_str)
        en_subtitle_file.replace(en_subtitle_file_str.replace(".en.srt", ".eng.srt"))


def delete_nfo_and_txt_files(content_dir: Path) -> None:
    """Deletes all `.nfo` and `.txt` files in a content directory.

    Args:
        content_dir (Path): The directory to run the cleaning on.
    """
    logger.info("Deleting .nfo and .txt files for content dir: '%s'.", str(content_dir))

    for nfo_file in content_dir.glob("**/*.nfo"):
        logger.debug("Deleting '%s'.", str(nfo_file))
        nfo_file.unlink()

    for txt_file in content_dir.glob("**/*.txt"):
        logger.debug("Deleting '%s'.", str(txt_file))
        txt_file.unlink()


def delete_empty_directories(content_dir: Path) -> None:
    """Deletes all empty directories in the content directory.

    Args:
        content_dir (Path): The directory to run the cleaning on.
    """
    logger.info("Deleting empty directories for content dir: '%s'.", str(content_dir))

    # list the files from the bottom up, so we break when we're back to the top
    content_dir_str = str(content_dir)
    for dir_str, _, _ in os.walk(content_dir_str, topdown=False):
        if dir_str == content_dir_str:
            break
        try:
            # try to remove the dir, will fail if not empty
            os.rmdir(dir_str)
            logger.info("Deleted empty directory at '%s'.", dir_str)
        except OSError:
            logger.debug("Not deleting non-empty directory at '%s'.", dir_str)


def main(content_dir: Path) -> None:
    """Runs the media cleaning for a given directory containing content.

    Args:
        content_dir (Path): The directory to run the renaming on.
    """
    logger.info("Cleaning media for content dir: '%s'.", str(content_dir))

    # subtitles
    rename_forced_subs(content_dir)
    rename_en_to_eng_subs(content_dir)

    # removing all `.nfo` and `.txt` files
    delete_nfo_and_txt_files(content_dir)

    # removing all empty directories
    delete_empty_directories(content_dir)


if __name__ == "__main__":
    for content_dir in CONTENT_DIRS:
        main(content_dir)
