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
