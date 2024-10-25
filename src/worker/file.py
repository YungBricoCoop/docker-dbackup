import os
from loguru import logger


def delete_file(filepath):
    """
    Deletes a file from the filesystem.

    :param filepath: The path to the file to delete.
    """
    try:
        os.remove(filepath)
        logger.info(f"File deleted: {filepath}")
    except Exception as e:
        logger.error(f"Failed to delete file: {e}")
        raise


def move_file_to_folder(filepath, folder):
    """
    Moves a file to a folder.

    :param filepath: The path to the file to move.
    :param folder: The path to the folder to move the file to.
    """
    try:
        os.replace(filepath, os.path.join(folder, os.path.basename(filepath)))
        logger.info(f"File moved: {filepath} -> {folder}")
    except Exception as e:
        logger.error(f"Failed to move file: {e}")
        raise